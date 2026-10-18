"""What every script of Stage 17's exercise shares: the values, the project's S3 prefix, the
request fields the D13 boundary demands, and how a refusal is printed.

The account-scoped values come from two JSON files beside the scripts, never from the code:
`space_values.json`, which awsds-workflows' `scripts/space_values.py` prints inside the
project's space (untracked: it carries the account id), and `extra_values.json`, the values no
space reading gives, each "<NAME>" until it is filled; an unfilled one never replaces a value
`space_values.json` gave. A value may name another as <NAME>, one level deep, as
awsds-workflows' render resolves them; a script stops while a value it needs is still "<NAME>",
and names it.

The scripts call the SageMaker API through boto3's low-level client, so each negative of the
stage is the admitted request with exactly one field changed (Lesson 20), and a refusal's
errorMessage is printed whole: it is the record, never the exit code.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

HERE = Path(__file__).resolve().parent
VALUE_FILES = ("space_values.json", "extra_values.json")
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]+)>")

# Under the project's shared/: data/, models/, predictions/, pipeline/ and bedrock/.
DEMO_DIR = "ml-demo"
MODEL_GROUP = "ml-demo-xgboost"
EXPERIMENT = "ml-demo-xgboost"
PROJECT_TAG = "AmazonDataZoneProject"


def load_values() -> dict:
    """Both value files merged, each reference to another value resolved."""
    values = {}
    for name in VALUE_FILES:
        path = HERE / name
        if not path.is_file():
            sys.exit(f"{path} is missing: README.md, 'The values', says how to write it.")
        for key, value in json.loads(path.read_text(encoding="utf-8")).items():
            # A model's unfilled "<NAME>" never replaces a value an earlier file gave.
            if value == f"<{key}>" and key in values:
                continue
            values[key] = value
    plain = {k: v for k, v in values.items() if not PLACEHOLDER.search(v)}
    return {
        k: PLACEHOLDER.sub(lambda m: plain.get(m.group(1), m.group(0)), v)
        for k, v in values.items()
    }


def need(values: dict, *names: str) -> None:
    """Stop unless every value named is present and filled."""
    missing = [n for n in names if n not in values or PLACEHOLDER.search(values[n])]
    if missing:
        sys.exit(f"no value for {', '.join(missing)}: fill extra_values.json (README.md).")


def stamp() -> str:
    """A job-name suffix: SageMaker names are unique per account and never reused."""
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def client(values: dict, service: str):
    return boto3.client(service, region_name=values["REGION"])


def demo_prefix(values: dict) -> str:
    """The exercise's key prefix in the project bucket, under the project's shared/."""
    return f"{values['DOMAIN_ID']}/{values['PROJECT_ID']}/shared/{DEMO_DIR}"


def s3_uri(values: dict, *parts: str) -> str:
    return "/".join([f"s3://{values['PROJECTS_BUCKET']}", demo_prefix(values), *parts])


def role_arn(values: dict) -> str:
    """The project role: the jobs run as the role the space runs as."""
    return f"arn:aws:iam::{values['ACCOUNT_ID']}:role/{values['PROJECT_ROLE_NAME']}"


def key_arn(values: dict) -> str:
    return f"arn:aws:kms:{values['REGION']}:{values['ACCOUNT_ID']}:key/{values['PROJECT_KEY_ID']}"


def vpc_config(values: dict) -> dict:
    """The project's subnets and security group, which DenySageMakerJobsOffVpc demands."""
    return {
        "Subnets": [values["SUBNET_AZ1"], values["SUBNET_AZ2"]],
        "SecurityGroupIds": [values["PROJECT_SG"]],
    }


def project_tags(values: dict) -> list:
    """The tag SageMakerCreatePermissions asks of every create."""
    return [{"Key": PROJECT_TAG, "Value": values["PROJECT_ID"]}]


def refusal(err: ClientError) -> str:
    """A refused call as the stage records it: the code and the whole errorMessage."""
    error = err.response.get("Error", {})
    return f"{error.get('Code', '-')}: {error.get('Message', '-')}"


def split_s3_uri(uri: str) -> tuple:
    """s3://bucket/key -> (bucket, key)."""
    bucket, _, key = uri[len("s3://") :].partition("/")
    return bucket, key
