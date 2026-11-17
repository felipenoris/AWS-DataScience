#!/usr/bin/env bash
# The CI/CD CLI for the `dev` stage, run in a SageMaker Unified Studio space on the house image as the
# project's role (Stage 8 decision 22). Every argument is the CLI's own; a deploy needs a bundle first,
# since the manifest's `model` item names a connection (SUP-374):
#
#   scripts/dev-cli.sh bundle --manifest manifest.yaml --targets dev
#   scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
#   scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-ml-train
#
# It runs the house environment's CLI by its path, whatever a space's PATH resolves: up to the house
# image's version 10 the SageMaker Distribution's aws-smus-cicd-cli 1.0.8 comes first and refuses the
# manifest's `code` field. It answers the CLI's domain lookup by name with DOMAIN_ID, the id the manifest
# reads: the CLI 1.0.9 resolves the domain with ListDomains on every deploy with bootstrap actions, the
# manifest's id notwithstanding, and DataZone refuses that call to a project's role
# (aws/CICD-for-SageMakerUnifiedStudio issue 413).
#
# The CLI refuses a manifest with an unset `${VAR}`, whatever the target: the names of the `staging` and
# `prod` stages, which the pipeline's legs alone fill, take a placeholder here when the shell has none.
# TRAINING_SOURCE is set on every call, whatever the shell holds, to the value scripts/training-source.py
# computes over this checkout: a deploy writes it as the `dev` stage's variable, the publish task copies
# it into model.json, and the release pipeline's guard compares it with the tag's.
set -eu

if [ -z "${AWSDS_PYTHON_ENV:-}" ]; then
  echo "dev-cli.sh: AWSDS_PYTHON_ENV is not set: run it in a space on the house image (awsds-sandbox-dev-env), which sets it to the environment carrying the CLI 1.0.9" >&2
  exit 2
fi
if [ -z "${DOMAIN_ID:-}" ]; then
  echo "dev-cli.sh: DOMAIN_ID is not set: export the domain's id, the value the manifest reads (sagemaker-application.md §D step 3)" >&2
  exit 2
fi
if [ -z "${MLFLOW_APP_ARN:-}" ]; then
  echo "dev-cli.sh: MLFLOW_APP_ARN is not set: export the ARN of the project's MLflow App, which the track task of app-ml-train logs each run to" >&2
  exit 2
fi
python="$AWSDS_PYTHON_ENV/bin/python"
if [ ! -x "$python" ]; then
  echo "dev-cli.sh: no interpreter at $python: AWSDS_PYTHON_ENV names no house environment" >&2
  exit 2
fi

scripts="$(cd "$(dirname "$0")" && pwd)"
TRAINING_SOURCE="$("$python" "$scripts/training-source.py" "$scripts/..")"
export TRAINING_SOURCE
echo "dev-cli.sh: TRAINING_SOURCE $TRAINING_SOURCE" >&2

# The lookup is replaced before the CLI's modules are imported, so a name bound at import time takes the
# answer too. A CLI without the function exits before any call: the replacement would answer no caller.
program='
import os
import re
import sys

import smus_cicd
import smus_cicd.helpers.datazone as datazone

if not callable(getattr(datazone, "get_domain_id_by_name", None)):
    sys.exit(
        "dev-cli.sh: this CLI has no smus_cicd.helpers.datazone.get_domain_id_by_name to answer;"
        " read its release before running it"
    )
domain_id = os.environ["DOMAIN_ID"]
datazone.get_domain_id_by_name = lambda domain_name, region: domain_id
cli = getattr(smus_cicd, "__version__", "unknown")
print(f"dev-cli.sh: aws-smus-cicd-cli {cli} on {sys.executable}, the domain lookup answered by DOMAIN_ID", file=sys.stderr)

manifest = "manifest.yaml"
for index, argument in enumerate(sys.argv):
    if argument in ("--manifest", "-m") and index + 1 < len(sys.argv):
        manifest = sys.argv[index + 1]
    elif argument.startswith("--manifest="):
        manifest = argument.split("=", 1)[1]
if os.path.isfile(manifest):
    with open(manifest, encoding="utf-8") as handle:
        names = set(re.findall(r"\$\{((?:STAGING|PROD)_[A-Za-z0-9_]+)(?::[^${}]*)?\}", handle.read()))
    given = [name for name in sorted(names) if not os.environ.get(name)]
    for name in given:
        os.environ[name] = "unused-by-dev"
    if given:
        print(f"dev-cli.sh: a placeholder for {len(given)} variable(s) of the other stages: {given[0]} ...", file=sys.stderr)

from smus_cicd.cli import app

sys.argv[0] = "aws-smus-cicd-cli"
app()
'
exec "$python" -c "$program" "$@"
