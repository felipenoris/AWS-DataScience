"""code/run-dbt.sh over doubles of boto3 and of OpenLineage's wrapper: the refusals, the lineage
configuration it writes for each form of the names, the environment and the arguments the wrapper
gets, the dbt it finds, the exit codes it passes on; and the mode each script is stored with."""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "code" / "run-dbt.sh"
OPTIONS = {
    "--region": "us-west-2",
    "--account": "000000000000",
    "--database": "app_dbt",
    "--workgroup": "workgroup-double",
    "--domain": "dzd-double",
    "--names": "as-built",
}
LOCATION = "s3://bucket-double/catalogs/app_dbt"

# boto3's Glue client as the script calls it: the database's location from DOUBLE_LOCATION, absent
# when the variable is empty, and EntityNotFoundException when it is unset.
BOTO3 = """
import os

from botocore.exceptions import ClientError


class Glue:
    def get_database(self, Name):
        if "DOUBLE_LOCATION" not in os.environ:
            error = {"Error": {"Code": "EntityNotFoundException", "Message": f"{Name} not found"}}
            raise ClientError(error, "GetDatabase")
        database = {"Name": Name}
        if os.environ["DOUBLE_LOCATION"]:
            database["LocationUri"] = os.environ["DOUBLE_LOCATION"]
        return {"Database": database}


def client(service):
    assert service == "glue", service
    return Glue()
"""

# The wrapper: what it was started with, written to DOUBLE_REPORT, and DOUBLE_EXIT as its code.
WRAPPER = """
import json
import os
import shutil
import sys


def main():
    names = [name for name in os.environ if name.startswith(("APP_DBT_", "OPENLINEAGE_", "AWS_"))]
    report = {
        "argv": sys.argv[1:],
        "cwd": os.getcwd(),
        "dbt": shutil.which("dbt"),
        "env": {name: os.environ[name] for name in names + ["DO_NOT_TRACK"] if name in os.environ},
        "config": open(os.environ["OPENLINEAGE_CONFIG"]).read(),
    }
    with open(os.environ["DOUBLE_REPORT"], "w") as handle:
        json.dump(report, handle)
    return int(os.environ.get("DOUBLE_EXIT", "0"))
"""


@pytest.fixture
def doubles(tmp_path):
    """The packages the script imports, and a mktemp that makes its folder under TMPDIR as the
    worker's GNU mktemp does, where macOS's takes the user's temporary folder first."""
    root = tmp_path / "doubles"
    (root / "bin").mkdir(parents=True)
    mktemp = root / "bin" / "mktemp"
    mktemp.write_text(
        f'#!/bin/sh\nexec {shutil.which("mktemp")} -d "${{TMPDIR%/}}/tmp.XXXXXXXXXX"\n'
    )
    mktemp.chmod(0o755)
    (root / "boto3").mkdir(parents=True)
    (root / "boto3" / "__init__.py").write_text(BOTO3)
    (root / "openlineage" / "dbt").mkdir(parents=True)
    (root / "openlineage" / "__init__.py").write_text("")
    (root / "openlineage" / "dbt" / "__init__.py").write_text(WRAPPER)
    return root


def run(tmp_path, doubles, *args, package=ROOT / "src", **env):
    """The script with a bare environment: the doubles and the package on PYTHONPATH, the python
    running the tests and the mktemp double first on PATH."""
    base = {
        "PATH": f"{doubles / 'bin'}:{Path(sys.executable).parent}:/usr/bin:/bin",
        "PYTHONPATH": f"{doubles}:{package}",
        "HOME": str(tmp_path),
        "TMPDIR": str(tmp_path),
        "DOUBLE_REPORT": str(tmp_path / "report.json"),
    }
    return subprocess.run(
        [shutil.which("bash"), str(SCRIPT), *args],
        cwd=tmp_path,
        env={**base, **env},
        capture_output=True,
        text=True,
        timeout=120,
    )


def options(**changes):
    values = {**OPTIONS, **{f"--{key}": value for key, value in changes.items()}}
    return [word for pair in values.items() for word in pair if pair[1] is not None]


def report(tmp_path):
    return json.loads((tmp_path / "report.json").read_text())


@pytest.mark.parametrize(
    ("args", "named"),
    [
        (["--bogus", "x"], "unknown option: --bogus"),
        (["--region"], "--region takes a value"),
        (["--region", "", *options()[2:]], "--region takes a value"),
        (["--region", "--account", "a"], "--region takes a value"),
        (options(domain=None), "--domain is required"),
        (options(names="arn"), "--names is as-built or glue-arn, not arn"),
        ([*options(), "--endpoint", "localhost:1"], "--endpoint is a URL or default"),
        ([*options(), "--attempts", "0"], "--attempts is a number from 1 or default"),
        ([*options(), "--attempts", "two"], "--attempts is a number from 1 or default"),
    ],
)
def test_it_refuses_before_any_call(tmp_path, doubles, args, named):
    done = run(tmp_path, doubles, *args, DOUBLE_LOCATION=LOCATION)
    assert done.returncode == 2
    assert f"run-dbt.sh: {named}" in done.stderr
    assert "usage: run-dbt.sh" in done.stderr
    assert done.stdout == ""


def test_the_names_as_built_post_straight_to_the_domain(tmp_path, doubles):
    done = run(tmp_path, doubles, *options(), DOUBLE_LOCATION=LOCATION)
    assert done.returncode == 0, done.stderr
    seen = report(tmp_path)
    work = Path(seen["cwd"])
    assert seen["argv"] == [
        "build",
        "--project-dir",
        str(work / "project"),
        "--profiles-dir",
        str(work / "project"),
    ]
    assert (work / "project" / "dbt_project.yml").is_file()
    assert seen["dbt"] == str(ROOT / "src" / "app_dbt" / "bin" / "dbt")
    assert yaml.safe_load(seen["config"]) == {
        "transport": {
            "type": "amazon_datazone_api",
            "domainId": "dzd-double",
            "region": "us-west-2",
        }
    }
    assert seen["env"] == {
        "APP_DBT_DATABASE": "app_dbt",
        "APP_DBT_WORKGROUP": "workgroup-double",
        "APP_DBT_DATA_DIR": LOCATION + "/",
        "AWS_DEFAULT_REGION": "us-west-2",
        "OPENLINEAGE_NAMESPACE": "app-dbt",
        "OPENLINEAGE_CONFIG": str(work / "openlineage.yml"),
        "DO_NOT_TRACK": "1",
    }
    assert "run-dbt.sh: peak memory" in done.stdout
    assert "kB, exit code 0" in done.stdout


def test_the_glue_names_wrap_the_transport_in_the_transformer(tmp_path, doubles):
    args = [*options(names="glue-arn"), "--endpoint", "http://127.0.0.1:9", "--attempts", "1"]
    done = run(tmp_path, doubles, *args, DOUBLE_LOCATION=LOCATION + "/")
    assert done.returncode == 0, done.stderr
    seen = report(tmp_path)
    assert yaml.safe_load(seen["config"]) == {
        "transport": {
            "type": "transform",
            "transformer_class": "app_dbt.lineage.GlueTableNames",
            "transformer_properties": {"region": "us-west-2", "account_id": "000000000000"},
            "transport": {
                "type": "amazon_datazone_api",
                "domainId": "dzd-double",
                "region": "us-west-2",
                "endpointOverride": "http://127.0.0.1:9",
            },
        }
    }
    assert seen["env"]["AWS_MAX_ATTEMPTS"] == "1"
    assert seen["env"]["APP_DBT_DATA_DIR"] == LOCATION + "/"


def test_a_dbt_command_after_the_options_replaces_build(tmp_path, doubles):
    args = [*options(), "--", "run", "--select", "notional_by_desk"]
    done = run(tmp_path, doubles, *args, DOUBLE_LOCATION=LOCATION, APP_DBT_NAMESPACE="by-hand")
    assert done.returncode == 0, done.stderr
    seen = report(tmp_path)
    assert seen["argv"][:3] == ["run", "--select", "notional_by_desk"]
    assert seen["env"]["OPENLINEAGE_NAMESPACE"] == "by-hand"


def test_a_console_script_without_its_mode_is_copied_and_marked(tmp_path, doubles):
    package = tmp_path / "extracted"
    shutil.copytree(ROOT / "src" / "app_dbt", package / "app_dbt")
    (package / "app_dbt" / "bin" / "dbt").chmod(0o644)
    done = run(tmp_path, doubles, *options(), package=package, DOUBLE_LOCATION=LOCATION)
    assert done.returncode == 0, done.stderr
    seen = report(tmp_path)
    assert seen["dbt"] == str(Path(seen["cwd"]) / "bin" / "dbt")
    assert (
        f"run-dbt.sh: dbt from {Path(seen['cwd']) / 'bin'}, this script executable" in done.stdout
    )


def test_the_exit_code_is_the_wrapper_s(tmp_path, doubles):
    done = run(tmp_path, doubles, *options(), DOUBLE_LOCATION=LOCATION, DOUBLE_EXIT="1")
    assert done.returncode == 1
    assert "kB, exit code 1" in done.stdout


def test_a_database_glue_does_not_hold_stops_before_dbt(tmp_path, doubles):
    done = run(tmp_path, doubles, *options())
    assert done.returncode == 1
    assert "run-dbt.sh: glue:GetDatabase app_dbt: ClientError:" in done.stderr
    assert not (tmp_path / "report.json").exists()


def test_a_database_without_a_location_exits_3(tmp_path, doubles):
    done = run(tmp_path, doubles, *options(), DOUBLE_LOCATION="")
    assert done.returncode == 3
    assert "the database app_dbt has no location in Glue" in done.stderr
    assert not (tmp_path / "report.json").exists()


@pytest.mark.parametrize(
    "path", ["code/run-dbt.sh", "scripts/dev-cli.sh", "src/app_dbt/bin/dbt"], ids=str
)
def test_each_script_is_stored_executable(path):
    """The bit on disk, and the mode git stores once the file is tracked: package-task copies a
    file's mode into the archive, and a clone takes the mode git stores."""
    assert os.stat(ROOT / path).st_mode & stat.S_IXUSR, f"{path} is not executable on disk"
    git = shutil.which("git")
    if git is None:
        pytest.skip("no git to read the stored mode")
    listed = subprocess.run(
        [git, "ls-files", "--stage", "--", path], cwd=ROOT, capture_output=True, text=True
    )
    if listed.returncode != 0 or not listed.stdout:
        pytest.skip(f"{path} is not tracked")
    assert listed.stdout.split()[0] == "100755", listed.stdout
