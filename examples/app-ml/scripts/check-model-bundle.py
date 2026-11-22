#!/usr/bin/env python3
"""The guard on a release's model (the pipeline's `bundle` job): what the bundle's model/ folder
holds against the candidate it describes, the manifest's threshold and the tag that releases it.

    python3 scripts/check-model-bundle.py artifacts/app-ml.zip manifest.yaml [--dotenv model.env]

The manifest's `model` item names the `dev` project's app-ml/models/latest/, which `bundle` reads
into the bundle's model/ folder as its caller, and neither `bundle` nor `deploy` fails where the
item read nothing (SUP-374). So a release fails unless the bundle holds model/model.tar.gz,
model/evaluation.json and model/model.json; the archive's SHA-256 is the one model.json names; the
evaluation's AUC is at least MIN_AUC, the one value every stage of the manifest gives it; and
model.json's training source is the tag's, computed by scripts/training-source.py over this
checkout, so a change to the features, the sample or the training request after the last training
run asks for a new run before a tag.

Exit 0 when the model passes, 1 otherwise; 2 on a file it cannot read. It prints the archive's hash,
its size, the training job and the AUC, never a value of the data; with --dotenv it writes
MODEL_SHA256 and MODEL_TRAINING_JOB, which the release's notes and the promotion's jobs read. The
standard library alone: the job runs it on the deploy runner's Python.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import zipfile
from pathlib import Path

ARCHIVE = "model/model.tar.gz"
EVALUATION = "model/evaluation.json"
MODEL = "model/model.json"
MIN_AUC = re.compile(r'^\s+MIN_AUC:\s*["\']?([0-9.]+)["\']?\s*$', re.MULTILINE)
HERE = Path(__file__).resolve().parent


def training_source(folder: Path) -> str:
    """scripts/training-source.py's value for the folder, by the same function dev-cli.sh runs."""
    spec = importlib.util.spec_from_file_location("training_source", HERE / "training-source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.training_source(folder)


def threshold(manifest_text: str) -> float:
    """MIN_AUC, the one value the manifest's stages give it."""
    values = sorted(set(MIN_AUC.findall(manifest_text)))
    if len(values) != 1:
        raise ValueError(f"the manifest gives MIN_AUC {len(values)} value(s), one expected")
    return float(values[0])


def compare(members: dict, floor: float, expected_source: str) -> tuple:
    """(problems, model.json) for the model/ folder's three members, by name."""
    missing = [name for name in (ARCHIVE, EVALUATION, MODEL) if name not in members]
    if missing:
        return [f"the bundle carries no {', '.join(missing)}"], {}
    problems = []
    try:
        model = json.loads(members[MODEL])
        evaluation = json.loads(members[EVALUATION])
    except ValueError as e:
        return [f"model.json or evaluation.json is not JSON: {e}"], {}
    digest = hashlib.sha256(members[ARCHIVE]).hexdigest()
    if model.get("sha256") != digest:
        problems.append(
            f"{ARCHIVE} has SHA-256 {digest}, and model.json names {model.get('sha256')}"
        )
    try:
        auc = float(evaluation["binary_classification_metrics"]["auc"]["value"])
    except (KeyError, TypeError, ValueError):
        problems.append("evaluation.json carries no binary_classification_metrics.auc")
    else:
        if auc < floor:
            problems.append(f"the evaluation's AUC {auc} is under MIN_AUC {floor}")
    source = model.get("training_source")
    if source == "dirty" or expected_source == "dirty":
        problems.append(
            f"the training source is dirty (the candidate's {source}, the tag's {expected_source})"
        )
    elif source != expected_source:
        problems.append(
            f"the candidate was trained from {source}, and the tag's code, sample and training "
            f"request are {expected_source}: train again before the tag"
        )
    if not model.get("training_job"):
        problems.append("model.json names no training job")
    return problems, model


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("bundle", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--dotenv", type=Path)
    args = parser.parse_args(argv)
    try:
        floor = threshold(args.manifest.read_text(encoding="utf-8"))
        expected_source = training_source(args.manifest.resolve().parent)
        with zipfile.ZipFile(args.bundle) as archive:
            names = [
                n for n in archive.namelist() if n.startswith("model/") and not n.endswith("/")
            ]
            members = {name: archive.read(name) for name in names}
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as e:
        print(f"check-model-bundle: {e}", file=sys.stderr)
        return 2
    listed = f" ({', '.join(sorted(members))})" if members else ""
    print(f"  model/: {len(members)} file(s){listed}")
    problems, model = compare(members, floor, expected_source)
    if model:
        print(f"  sha256: {model.get('sha256')}, {len(members.get(ARCHIVE, b''))} bytes")
        print(
            f"  training job: {model.get('training_job')}, AUC {model.get('auc')}, MIN_AUC {floor}"
        )
        print(f"  training source: {model.get('training_source')}, the tag's {expected_source}")
    for problem in problems:
        print(f"FAIL  {problem}")
    if problems:
        print("FAILED")
        return 1
    if args.dotenv:
        args.dotenv.write_text(
            f"MODEL_SHA256={model['sha256']}\nMODEL_TRAINING_JOB={model['training_job']}\n",
            encoding="utf-8",
        )
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
