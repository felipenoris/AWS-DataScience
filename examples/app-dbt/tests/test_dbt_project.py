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


def test_the_model_is_an_iceberg_table_dropped_by_athena(manifest):
    model = manifest["nodes"]["model.app_dbt.notional_by_desk"]
    assert model["config"]["materialized"] == "table"
    assert model["config"]["table_type"] == "iceberg"
    assert model["config"]["native_drop"] is True
    assert model["config"]["persist_docs"] == {"relation": True, "columns": True}
    assert model["schema"] == "app_dbt"
    assert model["database"] == "awsdatacatalog"
    assert model["depends_on"]["nodes"] == ["source.app_dbt.app_dbt.trades"]
    assert set(model["columns"]) == {"desk", "notional"}


def test_the_source_is_the_trades_table_of_the_product_database(manifest):
    source = manifest["sources"]["source.app_dbt.app_dbt.trades"]
    assert (source["database"], source["schema"], source["identifier"]) == (
        "awsdatacatalog",
        "app_dbt",
        "trades",
    )
    assert set(source["columns"]) == {"trade_date", "desk", "instrument", "quantity", "price"}


def test_the_desk_column_is_tested_not_null(manifest):
    tests = [node for node in manifest["nodes"].values() if node["resource_type"] == "test"]
    assert [(node["test_metadata"]["name"], node["column_name"]) for node in tests] == [
        ("not_null", "desk")
    ]
    assert tests[0]["depends_on"]["nodes"] == ["model.app_dbt.notional_by_desk"]
