"""A workflow's Bash command as the worker runs it, for the tests and the simulation: the CI/CD
CLI's translation of the manifest's variables at the deploy, then the operator's Jinja rendering at
the run."""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml
from jinja2 import StrictUndefined
from jinja2.sandbox import SandboxedEnvironment

ROOT = Path(__file__).resolve().parents[1]
BASH_OPERATOR = "airflow.providers.standard.operators.bash.BashOperator"

# The CLI 1.0.9 writes each {env.NAME} as {{ params.NAME }}, with no default, and the run fills the
# parameters from the stage's environment_variables (SUP-282); it resolves {proj.*}, {domain.*} and
# {stage.*} at the deploy. The service renders the command under StrictUndefined: a parameter the
# run does not carry fails the DAG's rendering.
VARIABLE = re.compile(r"\{(env|proj|domain|stage)\.([^}]+)\}")

# What the deploy resolves, in the shapes the service gives them.
RESOLVED = {
    "domain.id": "dzd-simulated",
    "domain.region": "us-west-2",
    "proj.id": "simulated-project",
    "proj.iam_role_arn": "arn:aws:iam::000000000000:role/simulated-project-role",
    "proj.connection.default.s3_shared.s3Uri": "s3://simulated-bucket/simulated-project/shared/",
    "proj.connection.project.athena.workgroupName": "workgroup-simulated-project",
    "stage.name": "dev",
}

# The manifest's stages: the application's own Sandbox project, then the deployment projects.
STAGES = ("dev", "staging", "prod")


def manifest() -> dict[str, Any]:
    return yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))


def stage_variables(stage: str = "dev") -> dict[str, Any]:
    return manifest()["stages"][stage]["environment_variables"]


def workflows() -> dict[str, dict[str, Any]]:
    """Each workflow file's document, by the file's name."""
    return {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted((ROOT / "workflows").glob("*.yaml"))
    }


def bash_commands() -> Iterator[tuple[str, str, str]]:
    """The DAG, the task and the command of every Bash task of every workflow."""
    for document in workflows().values():
        for dag, definition in document.items():
            for task, settings in definition["tasks"].items():
                if settings["operator"] == BASH_OPERATOR:
                    yield dag, task, settings["bash_command"]


def env_names(text: str) -> set[str]:
    return {name for kind, name in VARIABLE.findall(text) if kind == "env"}


def translate(text: str, resolved: dict[str, str] = RESOLVED) -> str:
    """The text as the CLI deploys it."""

    def replace(match: re.Match[str]) -> str:
        kind, name = match.groups()
        if kind == "env":
            return "{{ params." + name + " }}"
        return resolved[f"{kind}.{name}"]

    return VARIABLE.sub(replace, text)


def render(text: str, params: dict[str, Any], resolved: dict[str, str] = RESOLVED) -> str:
    """The text as the operator runs it: translated, then rendered with the run's parameters."""
    environment = SandboxedEnvironment(undefined=StrictUndefined, keep_trailing_newline=True)
    return environment.from_string(translate(text, resolved)).render(params=params)
