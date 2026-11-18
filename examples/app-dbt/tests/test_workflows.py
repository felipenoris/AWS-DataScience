"""The workflows against the manifest and the worker: each Bash task's command translated as the
CI/CD CLI translates it, rendered as the service renders it with every variable of each stage, and
parsed by bash; every variable a workflow reads declared by every stage, since the deploy resolves
every workflow the manifest names; every workflow the manifest names exposed by a file."""

from __future__ import annotations

import re
import shutil
import subprocess

import pytest
import rendering
from jinja2.exceptions import UndefinedError

COMMANDS = list(rendering.bash_commands())
CASES = [(stage, *command) for stage in rendering.STAGES for command in COMMANDS]


def placeholders(stage: str = "dev") -> dict[str, str]:
    """The stage's environment_variables, each ${VAR} given a placeholder."""
    values = {}
    for name, value in rendering.stage_variables(stage).items():
        values[name] = re.sub(r"\$\{(\w+)\}", r"placeholder-\1", str(value))
    return values


@pytest.mark.parametrize(
    ("stage", "dag", "task", "command"), CASES, ids=[f"{c[0]}-{c[2]}" for c in CASES]
)
def test_each_bash_command_renders_with_each_stage_and_parses(stage, dag, task, command):
    rendered = rendering.render(command, placeholders(stage))
    assert "{env." not in rendered and "{proj." not in rendered and "{{" not in rendered
    done = subprocess.run(
        [shutil.which("bash"), "-n", "-c", rendered], capture_output=True, text=True, timeout=30
    )
    assert done.returncode == 0, done.stderr


@pytest.mark.parametrize(("dag", "task", "command"), COMMANDS, ids=[c[1] for c in COMMANDS])
def test_a_parameter_the_run_does_not_carry_fails_the_rendering(dag, task, command):
    parameters = placeholders()
    for name in rendering.env_names(command):
        missing = {key: value for key, value in parameters.items() if key != name}
        with pytest.raises(UndefinedError, match=name):
            rendering.render(command, missing)


def test_the_transform_task_passes_each_option_to_run_dbt_in_single_quotes():
    command = next(text for _, task, text in COMMANDS if task == "transform")
    rendered = rendering.render(command, placeholders())
    assert rendered.startswith("bash /usr/local/airflow/dags/run-dbt.sh --region 'us-west-2' ")
    assert not rendered.rstrip().endswith(".sh")
    for option in ("account", "database", "workgroup", "domain", "names", "endpoint", "attempts"):
        assert re.search(rf" --{option} '[^']+'", rendered), option


@pytest.mark.parametrize("stage", rendering.STAGES)
def test_the_stage_declares_every_variable_a_workflow_reads(stage):
    declared = set(rendering.stage_variables(stage))
    for path in sorted((rendering.ROOT / "workflows").glob("*.yaml")):
        read = rendering.env_names(path.read_text(encoding="utf-8"))
        assert read <= declared, f"{path.name} reads {sorted(read - declared)}, undeclared"


def test_every_workflow_the_manifest_names_is_exposed_by_a_file():
    exposed = {dag for document in rendering.workflows().values() for dag in document}
    named = {item["workflowName"] for item in rendering.manifest()["content"]["workflows"]}
    assert named == exposed


def test_every_task_is_tried_once():
    for document in rendering.workflows().values():
        for definition in document.values():
            for task, settings in definition["tasks"].items():
                assert settings.get("retries") == 0, task
