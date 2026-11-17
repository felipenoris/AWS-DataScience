"""The manifest and the workflows against the package: each callable a workflow names exists and
takes the arguments the task passes; each stage creates the workflows and holds the variables
Stage 17's step 10.2 gives it; the operator's probe stays outside every storage item."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
import yaml

import app_genai_tasks
import build_archive

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = yaml.safe_load((ROOT / "manifest.yaml").read_text(encoding="utf-8"))
WORKFLOWS = {
    path.stem: yaml.safe_load(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "workflows").glob("*.yaml"))
}
TASKS = [
    (workflow, name, task)
    for workflow, document in WORKFLOWS.items()
    for name, task in document[workflow]["tasks"].items()
]


@pytest.mark.parametrize(("workflow", "name", "task"), TASKS)
def test_each_task_names_a_callable_of_the_package_with_its_arguments(workflow, name, task):
    module, _, function = task["python_callable"].rpartition(".")
    assert module == "app_genai_tasks"
    assert function in app_genai_tasks.__all__
    parameters = inspect.signature(getattr(app_genai_tasks, function)).parameters
    required = {
        key
        for key, parameter in parameters.items()
        if parameter.default is inspect.Parameter.empty
        and parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    }
    assert required <= set(task["op_kwargs"]) <= set(parameters)
    assert task["retries"] == 0


def test_the_workflows_are_the_manifests():
    named = [item["workflowName"] for item in MANIFEST["content"]["workflows"]]
    assert named == ["app-genai-triage", "app-genai-probe"]
    assert set(WORKFLOWS) == set(named)
    for item in MANIFEST["content"]["workflows"]:
        assert item["code"] == "code/app-genai.zip"
    assert build_archive.ROOT / item["code"] == ROOT / "code" / "app-genai.zip"


def test_no_catalog_and_three_storage_items():
    content = MANIFEST["content"]
    assert "catalog" not in content
    assert [item["name"] for item in content["storage"]] == ["code", "samples", "workflows"]


@pytest.mark.parametrize(
    ("stage", "project", "model", "expect", "created"),
    [
        ("dev", "${DEV_PROJECT_NAME}", "${DEV_MODEL_ID}", "answered", ["triage", "probe"]),
        ("staging", "deploy-staging", "${STAGING_MODEL_ID}", "refused", ["triage", "probe"]),
        ("prod", "deploy-production", "${PROD_MODEL_ID}", "refused", ["triage"]),
    ],
)
def test_each_stage(stage, project, model, expect, created):
    declared = MANIFEST["stages"][stage]
    assert declared["project"]["name"] == project
    assert declared["environment_variables"] == {
        "MODEL_ID": model,
        "MIN_ACCURACY": "0.80",
        "EXPECT_UNGUARDED": expect,
    }
    actions = declared["bootstrap"]["actions"]
    assert {action["type"] for action in actions} == {"workflow.create"}
    assert [action["workflowName"] for action in actions] == [f"app-genai-{w}" for w in created]
    targets = {
        item["name"]: item["targetDirectory"]
        for item in declared["deployment_configuration"]["storage"]
    }
    assert targets == {
        "code": "app-genai/code",
        "samples": "app-genai/inbox",
        "workflows": "app-genai/workflows",
    }


def test_the_operator_probe_is_outside_every_storage_item():
    includes = [pattern for item in MANIFEST["content"]["storage"] for pattern in item["include"]]
    assert all(not pattern.startswith("probes") for pattern in includes)
    probe = yaml.safe_load((ROOT / "probes" / "operator.yaml").read_text(encoding="utf-8"))
    (task,) = probe["app-genai-operator-probe"]["tasks"].values()
    assert task["operator"].endswith(".BedrockInvokeModelOperator")
