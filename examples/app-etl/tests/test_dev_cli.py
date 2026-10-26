"""scripts/dev-cli.sh over a double of the CI/CD CLI: the domain lookup answered by DOMAIN_ID for
both kinds of caller, the arguments passed through unchanged, the CLI's exit code kept, and the
refusals when the house environment, the domain's id or the lookup is missing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "dev-cli.sh"
DOMAIN_ID = "dzd-double"

# The lookup refuses as DataZone refuses ListDomains to a project's role. 1.0.9 calls it through
# the module (project_manager.py) and from inside it (get_project_user_role_arn), so the double's
# app makes both calls and prints what each returned and the argv it ran with.
DATAZONE = """
def get_domain_id_by_name(domain_name, region):
    raise RuntimeError("User is not permitted to perform operation: ListDomains")


def get_project_user_role_arn(project_name, domain_name, region):
    return get_domain_id_by_name(domain_name, region)
"""

CLI = """
import json
import sys

from smus_cicd.helpers import datazone


def app():
    print(json.dumps({
        "argv": sys.argv,
        "through the module": datazone.get_domain_id_by_name("awsds-studio", "us-west-2"),
        "inside the module": datazone.get_project_user_role_arn("p", "awsds-studio", "us-west-2"),
    }))
    sys.exit(3)
"""


def double(root: Path, datazone: str = DATAZONE) -> Path:
    """The CLI's package under root/lib, and a house environment under root/env whose python is the
    interpreter running the tests."""
    package = root / "lib" / "smus_cicd"
    (package / "helpers").mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "1.0.9-double"\n')
    (package / "cli.py").write_text(CLI)
    (package / "helpers" / "__init__.py").write_text("")
    (package / "helpers" / "datazone.py").write_text(datazone)
    python = root / "env" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    python.chmod(0o755)
    return root


def run(root: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    """The script with a bare environment: the double on PYTHONPATH and nothing of the caller's
    AWSDS_PYTHON_ENV or DOMAIN_ID."""
    base = {"PATH": os.environ["PATH"], "PYTHONPATH": str(root / "lib")}
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=root,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=60,
    )


@pytest.fixture
def root(tmp_path):
    return double(tmp_path)


def test_the_lookup_is_answered_by_domain_id_for_both_callers(root):
    args = ["deploy", "--manifest", "manifest.yaml", "--targets", "dev", "--skip-validation"]
    done = run(root, *args, "--no-events", AWSDS_PYTHON_ENV=str(root / "env"), DOMAIN_ID=DOMAIN_ID)
    seen = json.loads(done.stdout)
    assert seen["through the module"] == DOMAIN_ID
    assert seen["inside the module"] == DOMAIN_ID
    assert seen["argv"] == ["aws-smus-cicd-cli", *args, "--no-events"]
    assert "aws-smus-cicd-cli 1.0.9-double on" in done.stderr
    assert done.returncode == 3


def test_the_arguments_pass_through_unchanged(root):
    args = ["run", "--manifest", "manifest.yaml", "--workflow", "a name with spaces", "it's", ""]
    done = run(root, *args, AWSDS_PYTHON_ENV=str(root / "env"), DOMAIN_ID=DOMAIN_ID)
    assert json.loads(done.stdout)["argv"] == ["aws-smus-cicd-cli", *args]


@pytest.mark.parametrize(
    ("env", "named"),
    [
        ({"DOMAIN_ID": DOMAIN_ID}, "AWSDS_PYTHON_ENV is not set"),
        ({"AWSDS_PYTHON_ENV": "", "DOMAIN_ID": DOMAIN_ID}, "AWSDS_PYTHON_ENV is not set"),
        ({"AWSDS_PYTHON_ENV": "env"}, "DOMAIN_ID is not set"),
        ({"AWSDS_PYTHON_ENV": "env", "DOMAIN_ID": ""}, "DOMAIN_ID is not set"),
        ({"AWSDS_PYTHON_ENV": "lib", "DOMAIN_ID": DOMAIN_ID}, "no interpreter at"),
    ],
)
def test_it_refuses_before_the_cli_runs(root, env, named):
    env = {k: str(root / v) if k == "AWSDS_PYTHON_ENV" and v else v for k, v in env.items()}
    done = run(root, "deploy", "--targets", "dev", **env)
    assert done.returncode == 2
    assert named in done.stderr
    assert done.stdout == ""


def test_it_refuses_a_cli_without_the_lookup(tmp_path):
    root = double(
        tmp_path, datazone="def resolve_domain_id(domain_name, region):\n    return None\n"
    )
    done = run(root, "deploy", AWSDS_PYTHON_ENV=str(root / "env"), DOMAIN_ID=DOMAIN_ID)
    assert done.returncode == 1
    assert "no smus_cicd.helpers.datazone.get_domain_id_by_name" in done.stderr
    assert done.stdout == ""
