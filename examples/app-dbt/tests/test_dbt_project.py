"""The dbt project as dbt reads it: `dbt parse`, run by the package's console script over a copy of
the project, with placeholder values and every network path closed, and the manifest it writes."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PACKAGE = Path(__file__).resolve().parents[1] / "src" / "app_dbt"
CLOSED = "http://127.0.0.1:9"


@pytest.fixture(scope="module")
def manifest(tmp_path_factory):
    """The manifest `dbt parse` writes, the profile's values given by placeholders."""
    root = tmp_path_factory.mktemp("parse")
    project = root / "project"
    shutil.copytree(PACKAGE / "project", project)
    env = {
        "PATH": os.environ["PATH"],
        "HOME": str(root),
        "DO_NOT_TRACK": "1",
        "AWS_DEFAULT_REGION": "us-west-2",
        "APP_DBT_DATABASE": "app_dbt",
        "APP_DBT_WORKGROUP": "workgroup-placeholder",
        "APP_DBT_DATA_DIR": "s3://bucket-placeholder/catalogs/",
        "AWS_ENDPOINT_URL": CLOSED,
        "HTTP_PROXY": CLOSED,
        "HTTPS_PROXY": CLOSED,
        "NO_PROXY": "",
    }
    done = subprocess.run(
        [sys.executable, str(PACKAGE / "bin" / "dbt"), "parse"]
        + ["--project-dir", str(project), "--profiles-dir", str(project)],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    assert done.returncode == 0, done.stdout + done.stderr
    return json.loads((project / "target" / "manifest.json").read_text())


TRADES = {"trade_date", "desk", "instrument", "quantity", "price"}
# Each model and the source it reads: trades, which the workflow's Glue task writes, and
# trades_notional, the resource link of the project's subscription to Production's listing.
MODELS = {
    "notional_by_desk": "source.app_dbt.app_dbt.trades",
    "notional_by_desk_prod": "source.app_dbt.app_dbt.trades_notional",
}


@pytest.mark.parametrize(("name", "source"), MODELS.items())
def test_each_model_is_an_iceberg_table_dropped_by_athena(manifest, name, source):
    model = manifest["nodes"][f"model.app_dbt.{name}"]
    assert model["config"]["materialized"] == "table"
    assert model["config"]["table_type"] == "iceberg"
    assert model["config"]["native_drop"] is True
    assert model["config"]["persist_docs"] == {"relation": True, "columns": True}
    assert model["schema"] == "app_dbt"
    assert model["database"] == "awsdatacatalog"
    assert model["depends_on"]["nodes"] == [source]
    assert set(model["columns"]) == {"desk", "notional"}


def test_the_project_has_the_two_models_alone(manifest):
    models = [node for node in manifest["nodes"].values() if node["resource_type"] == "model"]
    assert sorted(node["name"] for node in models) == sorted(MODELS)


def test_the_sources_are_the_two_tables_of_the_product_database(manifest):
    sources = {
        source["identifier"]: (source["database"], source["schema"], set(source["columns"]))
        for source in manifest["sources"].values()
    }
    assert sources == {
        "trades": ("awsdatacatalog", "app_dbt", TRADES),
        "trades_notional": ("awsdatacatalog", "app_dbt", TRADES | {"notional"}),
    }


def test_each_model_tests_its_desk_column_not_null(manifest):
    tests = sorted(
        (node["test_metadata"]["name"], node["column_name"], node["depends_on"]["nodes"])
        for node in manifest["nodes"].values()
        if node["resource_type"] == "test"
    )
    assert tests == [("not_null", "desk", [f"model.app_dbt.{name}"]) for name in sorted(MODELS)]
