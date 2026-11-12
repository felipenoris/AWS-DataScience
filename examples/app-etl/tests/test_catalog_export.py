"""scripts/check-catalog-export.py over bundles built in a temporary folder: the declared product
passes, and a release fails on a resource outside the declaration, a required one missing or
doubled, a bundle with no export, and a declaration naming a section the export has none of."""

from __future__ import annotations

import json
import runpy
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check-catalog-export.py"
DECLARED = json.loads((ROOT / "product.json").read_text())
PRODUCT = {
    "metadata": {"sourceProjectId": "project", "sourceDomainId": "dzd-double"},
    "glossaries": [],
    "glossaryTerms": [],
    "formTypes": [{"name": "classification"}],
    "assetTypes": [],
    "assets": [{"name": "trades_notional", "typeIdentifier": "amazon.datazone.GlueTableAssetType"}],
    "dataProducts": [],
}


@pytest.fixture
def guard():
    return runpy.run_path(str(SCRIPT), run_name="check_catalog_export")


def bundle(folder: Path, export: dict | None) -> Path:
    path = folder / "app-etl.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("workflows/app-etl.yaml", "app-etl: {}\n")
        if export is not None:
            archive.writestr("catalog/catalog_export.json", json.dumps(export))
    return path


def run(guard, folder: Path, export: dict | None, declared: dict = DECLARED) -> int:
    declaration = folder / "product.json"
    declaration.write_text(json.dumps(declared))
    return guard["main"]([str(bundle(folder, export)), str(declaration)])


def test_the_declared_product_passes(guard, tmp_path, capsys):
    assert run(guard, tmp_path, PRODUCT) == 0
    out = capsys.readouterr().out
    assert "assets: 1 (trades_notional)" in out
    assert out.rstrip().endswith("OK")


def test_an_allowed_resource_may_be_absent(guard, tmp_path):
    assert run(guard, tmp_path, {**PRODUCT, "formTypes": []}) == 0


@pytest.mark.parametrize(
    ("change", "named"),
    [
        ({"assets": PRODUCT["assets"] + [{"name": "house-price"}]}, "assets: house-price is in"),
        ({"dataProducts": [{"name": "my-data-product"}]}, "dataProducts: my-data-product is in"),
        ({"glossaries": [{"name": "trading"}]}, "glossaries: trading is in"),
        ({"assets": []}, "assets: trades_notional is in the export 0 time(s)"),
        ({"assets": PRODUCT["assets"] * 2}, "assets: trades_notional is in the export 2 time(s)"),
    ],
)
def test_a_release_fails_on_an_export_that_is_not_the_declared_product(
    guard, tmp_path, capsys, change, named
):
    assert run(guard, tmp_path, {**PRODUCT, **change}) == 1
    assert named in capsys.readouterr().out


def test_a_bundle_with_no_export_fails(guard, tmp_path, capsys):
    assert run(guard, tmp_path, None) == 1
    assert "carries no catalog/catalog_export.json" in capsys.readouterr().out


def test_a_declaration_naming_an_unknown_section_fails(guard, tmp_path, capsys):
    declared = {"required": {"assets": ["trades_notional"]}, "allowed": {"forms": ["x"]}}
    assert run(guard, tmp_path, {**PRODUCT, "formTypes": []}, declared) == 1
    assert "names a section the export has none of: forms" in capsys.readouterr().out


def test_a_declaration_that_cannot_be_read_is_a_usage_error(guard, tmp_path):
    assert guard["main"]([str(bundle(tmp_path, PRODUCT)), str(tmp_path / "absent.json")]) == 2
