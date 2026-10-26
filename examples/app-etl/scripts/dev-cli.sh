#!/usr/bin/env bash
# The CI/CD CLI for the `dev` stage, run in a SageMaker Unified Studio space on the house image as the
# project's role (Stage 8 decision 22). Every argument is the CLI's own:
#
#   scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
#   scripts/dev-cli.sh run --manifest manifest.yaml --targets dev --workflow app-etl
#
# It runs the house environment's CLI by its path: the SageMaker Distribution's aws-smus-cicd-cli 1.0.8
# comes first on a space's PATH and refuses the manifest's `code` field. It answers the CLI's domain
# lookup by name with DOMAIN_ID, the id the manifest reads: the CLI 1.0.9 resolves the domain with
# ListDomains on every deploy with bootstrap actions, the manifest's id notwithstanding, and DataZone
# refuses that call to a project's role. The answer is the same for every caller of the lookup, the id
# the deploy roles' own call returns in the pipeline, which runs the CLI by its name and not this script.
set -eu

if [ -z "${AWSDS_PYTHON_ENV:-}" ]; then
  echo "dev-cli.sh: AWSDS_PYTHON_ENV is not set: run it in a space on the house image (awsds-sandbox-dev-env), which sets it to the environment carrying the CLI 1.0.9" >&2
  exit 2
fi
if [ -z "${DOMAIN_ID:-}" ]; then
  echo "dev-cli.sh: DOMAIN_ID is not set: export the domain's id, the value the manifest reads (sagemaker-application.md §D step 3)" >&2
  exit 2
fi
python="$AWSDS_PYTHON_ENV/bin/python"
if [ ! -x "$python" ]; then
  echo "dev-cli.sh: no interpreter at $python: AWSDS_PYTHON_ENV names no house environment" >&2
  exit 2
fi

# The lookup is replaced before the CLI's modules are imported, so a name bound at import time takes the
# answer too. A CLI without the function exits before any call: the replacement would answer no caller.
program='
import os
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

from smus_cicd.cli import app

sys.argv[0] = "aws-smus-cicd-cli"
app()
'
exec "$python" -c "$program" "$@"
