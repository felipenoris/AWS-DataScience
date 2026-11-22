"""scripts/dev-cli.sh over a double of the CI/CD CLI, run from a checkout built here:
TRAINING_SOURCE computed over the checkout and exported whatever the shell held, `dirty` for a
change under the paths it covers, the domain lookup answered by DOMAIN_ID, the arguments passed
through, the other stages' variables given a placeholder, and the refusals before the CLI runs."""

from __future__ import annotations

import json
import os
import re
import runpy
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from conftest import GIT_ENV, ROOT, commit_application, needs_git

DOMAIN_ID = "dzd-double"
MLFLOW_APP_ARN = "arn:aws:sagemaker:us-west-2:000000000000:mlflow-app/app-double"
SCRIPTS = ("dev-cli.sh", "training-source.py")

DATAZONE = """
def get_domain_id_by_name(domain_name, region):
    raise RuntimeError("User is not permitted to perform operation: ListDomains")


def get_project_user_role_arn(project_name, domain_name, region):
    return get_domain_id_by_name(domain_name, region)
"""

CLI = """
import json
import os
import sys

from smus_cicd.helpers import datazone


def app():
    print(json.dumps({
        "argv": sys.argv,
        "TRAINING_SOURCE": os.environ.get("TRAINING_SOURCE"),
        "stages": {k: v for k, v in os.environ.items() if k.startswith(("STAGING_", "PROD_"))},
        "through the module": datazone.get_domain_id_by_name("awsds-studio", "us-west-2"),
        "inside the module": datazone.get_project_user_role_arn("p", "awsds-studio", "us-west-2"),
    }))
    sys.exit(3)
"""


def double(root: Path) -> Path:
    """The CLI's package under root/lib, and a house environment under root/env whose python is the
    interpreter running the tests."""
    package = root / "lib" / "smus_cicd"
    (package / "helpers").mkdir(parents=True)
    (package / "__init__.py").write_text('__version__ = "1.0.9-double"\n')
    (package / "cli.py").write_text(CLI)
    (package / "helpers" / "__init__.py").write_text("")
    (package / "helpers" / "datazone.py").write_text(DATAZONE)
    python = root / "env" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n')
    python.chmod(0o755)
    return root


@pytest.fixture
def cli(tmp_path) -> Path:
    return double(tmp_path / "double")


@pytest.fixture
def app(git_env, tmp_path) -> Path:
    return commit_application(tmp_path / "app", scripts=SCRIPTS)


def run(app: Path, cli: Path, *args: str, **env: str) -> subprocess.CompletedProcess:
    """The script from the checkout's scripts/, in a bare environment: the double on PYTHONPATH, git
    isolated, and nothing of the caller's house environment, domain or MLflow App."""
    base = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(cli / "lib"),
        **GIT_ENV,
        "GIT_CEILING_DIRECTORIES": str(app.parent),
    }
    return subprocess.run(
        ["bash", str(app / "scripts" / "dev-cli.sh"), *args],
        cwd=app,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=60,
    )


def ready(cli: Path, **env: str) -> dict:
    return {
        "AWSDS_PYTHON_ENV": str(cli / "env"),
        "DOMAIN_ID": DOMAIN_ID,
        "MLFLOW_APP_ARN": MLFLOW_APP_ARN,
        **env,
    }


def expected_source(app: Path) -> str:
    helper = runpy.run_path(str(ROOT / "scripts" / "training-source.py"), run_name="helper")
    return helper["training_source"](app)


@needs_git
def test_training_source_is_the_checkouts_whatever_the_shell_held(app, cli):
    args = ["deploy", "--manifest", "manifest.yaml", "--targets", "dev", "--skip-validation"]
    done = run(app, cli, *args, **ready(cli, TRAINING_SOURCE="none"))
    seen = json.loads(done.stdout)
    source = expected_source(app)
    assert len(source) == 64
    assert seen["TRAINING_SOURCE"] == source
    assert f"dev-cli.sh: TRAINING_SOURCE {source}" in done.stderr
    assert seen["through the module"] == seen["inside the module"] == DOMAIN_ID
    assert seen["argv"] == ["aws-smus-cicd-cli", *args]
    assert done.returncode == 3


@needs_git
def test_a_change_under_the_paths_deploys_dirty(app, cli):
    (app / "samples" / "churn.csv").write_text("tenure_months,churned\n2,1\n")
    done = run(app, cli, "deploy", **ready(cli))
    assert json.loads(done.stdout)["TRAINING_SOURCE"] == "dirty"


@needs_git
def test_the_other_stages_variables_take_a_placeholder(app, cli):
    shutil.copy2(ROOT / "manifest.yaml", app / "manifest.yaml")
    names = set(re.findall(r"\$\{((?:STAGING|PROD)_\w+)\}", (ROOT / "manifest.yaml").read_text()))
    assert names
    done = run(app, cli, "deploy", "--manifest", "manifest.yaml", **ready(cli))
    assert json.loads(done.stdout)["stages"] == dict.fromkeys(names, "unused-by-dev")


@needs_git
def test_the_arguments_pass_through_unchanged(app, cli):
    args = ["run", "--manifest", "manifest.yaml", "--workflow", "app-ml-train", "it's", ""]
    done = run(app, cli, *args, **ready(cli))
    assert json.loads(done.stdout)["argv"] == ["aws-smus-cicd-cli", *args]


@pytest.mark.parametrize(
    ("unset", "named"),
    [
        ("AWSDS_PYTHON_ENV", "AWSDS_PYTHON_ENV is not set"),
        ("DOMAIN_ID", "DOMAIN_ID is not set"),
        ("MLFLOW_APP_ARN", "MLFLOW_APP_ARN is not set"),
    ],
)
@pytest.mark.parametrize("empty", [False, True])
def test_it_refuses_before_the_cli_runs(tmp_path, cli, unset, named, empty):
    loose = tmp_path / "loose"
    (loose / "scripts").mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copy2(ROOT / "scripts" / name, loose / "scripts" / name)
    env = ready(cli)
    if empty:
        env[unset] = ""
    else:
        del env[unset]
    done = run(loose, cli, "deploy", **env)
    assert done.returncode == 2
    assert named in done.stderr
    assert done.stdout == ""


def test_it_refuses_a_folder_without_the_interpreter(tmp_path, cli):
    loose = tmp_path / "loose"
    (loose / "scripts").mkdir(parents=True)
    shutil.copy2(ROOT / "scripts" / "dev-cli.sh", loose / "scripts" / "dev-cli.sh")
    done = run(loose, cli, "deploy", **ready(cli, AWSDS_PYTHON_ENV=str(cli / "lib")))
    assert done.returncode == 2
    assert "no interpreter at" in done.stderr


@needs_git
def test_a_checkout_git_cannot_read_stops_before_the_cli(tmp_path, cli):
    loose = tmp_path / "loose"
    (loose / "scripts").mkdir(parents=True)
    for name in SCRIPTS:
        shutil.copy2(ROOT / "scripts" / name, loose / "scripts" / name)
    done = run(loose, cli, "deploy", **ready(cli))
    assert done.returncode == 1
    assert "training-source: git status in" in done.stderr
    assert done.stdout == ""
