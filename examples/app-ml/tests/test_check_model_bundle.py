"""scripts/check-model-bundle.py over bundles built in a temporary folder: the candidate the
manifest's threshold and the tag's training source accept passes and writes the dotenv, and a
release fails on a model/ folder the bundle read nothing into, an archive whose hash differs, an AUC
under MIN_AUC, a training source that is not the tag's or is dirty, a manifest with two thresholds
and a file that is no zip."""

from __future__ import annotations

import hashlib
import json
import runpy
import zipfile
from pathlib import Path

import pytest
from conftest import ROOT, commit_application, needs_git

SCRIPT = ROOT / "scripts" / "check-model-bundle.py"
ARCHIVE = b"\x1f\x8b a model archive"
DIGEST = hashlib.sha256(ARCHIVE).hexdigest()
JOB = "app-ml-train-20261117T120000"
SOURCE = "c" * 64
MANIFEST = (
    "stages:\n"
    '  dev:\n    environment:\n      MIN_AUC: "0.70"\n'
    "  prod:\n    environment:\n      MIN_AUC: '0.70'\n"
)


@pytest.fixture
def guard(monkeypatch):
    """The script's functions, the tag's training source answered by SOURCE."""
    module = runpy.run_path(str(SCRIPT), run_name="check_model_bundle")
    monkeypatch.setitem(module["main"].__globals__, "training_source", lambda folder: SOURCE)
    return module


def model_json(**changes) -> dict:
    return {
        "application": "app-ml",
        "training_job": JOB,
        "sha256": DIGEST,
        "auc": 0.84,
        "training_source": SOURCE,
        **changes,
    }


def model_folder(model: dict | None = None, auc: float = 0.84, archive: bytes = ARCHIVE) -> dict:
    evaluation = {"binary_classification_metrics": {"auc": {"value": auc}}}
    return {
        "model/model.tar.gz": archive,
        "model/evaluation.json": json.dumps(evaluation),
        "model/model.json": json.dumps(model if model is not None else model_json()),
    }


def run(guard, folder: Path, members: dict, *extra: str, manifest: str = MANIFEST) -> int:
    bundle = folder / "app-ml.zip"
    with zipfile.ZipFile(bundle, "w") as archive:
        archive.writestr("workflows/app-ml-train.yaml", "app-ml-train: {}\n")
        for name, data in members.items():
            archive.writestr(name, data)
    (folder / "manifest.yaml").write_text(manifest)
    return guard["main"]([str(bundle), str(folder / "manifest.yaml"), *extra])


def test_the_candidate_passes_and_writes_the_dotenv(guard, tmp_path, capsys):
    dotenv = tmp_path / "model.env"
    assert run(guard, tmp_path, model_folder(), "--dotenv", str(dotenv)) == 0
    assert dotenv.read_text() == f"MODEL_SHA256={DIGEST}\nMODEL_TRAINING_JOB={JOB}\n"
    out = capsys.readouterr().out
    assert "model/: 3 file(s)" in out
    assert f"sha256: {DIGEST}, {len(ARCHIVE)} bytes" in out
    assert f"training job: {JOB}, AUC 0.84, MIN_AUC 0.7" in out
    assert out.rstrip().endswith("OK")


def test_a_model_folder_the_bundle_read_nothing_into_fails(guard, tmp_path, capsys):
    dotenv = tmp_path / "model.env"
    assert run(guard, tmp_path, {}, "--dotenv", str(dotenv)) == 1
    out = capsys.readouterr().out
    assert "model/: 0 file(s)" in out
    assert (
        "the bundle carries no model/model.tar.gz, model/evaluation.json, model/model.json" in out
    )
    assert out.rstrip().endswith("FAILED")
    assert not dotenv.exists()


@pytest.mark.parametrize(
    ("members", "refusal"),
    [
        (model_folder(archive=b"another archive"), f"and model.json names {DIGEST}"),
        (model_folder(auc=0.65), "the evaluation's AUC 0.65 is under MIN_AUC 0.7"),
        (model_folder(model_json(training_source="d" * 64)), "train again before the tag"),
        (model_folder(model_json(training_source="dirty")), "the training source is dirty"),
        (model_folder(model_json(training_job="")), "model.json names no training job"),
        ({**model_folder(), "model/model.json": "{"}, "is not JSON"),
    ],
)
def test_a_candidate_the_release_cannot_carry_fails(guard, tmp_path, capsys, members, refusal):
    assert run(guard, tmp_path, members) == 1
    assert refusal in capsys.readouterr().out


def test_a_tag_whose_checkout_is_dirty_fails(guard, tmp_path, capsys, monkeypatch):
    monkeypatch.setitem(guard["main"].__globals__, "training_source", lambda folder: "dirty")
    assert run(guard, tmp_path, model_folder()) == 1
    assert f"the candidate's {SOURCE}, the tag's dirty" in capsys.readouterr().out


def test_a_manifest_with_two_thresholds_exits_2(guard, tmp_path, capsys):
    manifest = MANIFEST.replace("'0.70'", "'0.75'")
    assert run(guard, tmp_path, model_folder(), manifest=manifest) == 2
    assert "the manifest gives MIN_AUC 2 value(s), one expected" in capsys.readouterr().err


def test_a_file_that_is_no_zip_exits_2(guard, tmp_path, capsys):
    (tmp_path / "manifest.yaml").write_text(MANIFEST)
    (tmp_path / "app-ml.zip").write_text("not a zip\n")
    arguments = [str(tmp_path / "app-ml.zip"), str(tmp_path / "manifest.yaml")]
    assert guard["main"](arguments) == 2
    assert "check-model-bundle: " in capsys.readouterr().err


def test_the_applications_manifest_gives_one_threshold(guard):
    assert guard["threshold"]((ROOT / "manifest.yaml").read_text()) == 0.70


@needs_git
def test_the_tags_training_source_is_read_from_the_checkout(git_env, tmp_path, capsys):
    """The guard and its helper run as the bundle job runs them, git included: the candidate trained
    from the tag passes, and a change under src/ after the run fails the release."""
    guard = runpy.run_path(str(SCRIPT), run_name="check_model_bundle")
    app = commit_application(tmp_path / "app")
    source = guard["training_source"](app)
    assert len(source) == 64
    members = model_folder(model_json(training_source=source))
    assert run(guard, app, members) == 0
    (app / "src" / "app_ml" / "prepare.py").write_text("FEATURES = ('tenure_months',)\n")
    assert run(guard, app, members) == 1
    assert "the training source is dirty" in capsys.readouterr().out
