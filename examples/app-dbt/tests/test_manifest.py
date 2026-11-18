"""The manifest against its three stages and the infrastructure repository's legs: each stage's
project, its variables, the workflows its bootstrap creates or runs and where its storage lands; the
catalog block of a chain application's product; every name a target stage reads one the leg or the
pipeline fills; and product.json naming the two tables the workflow writes."""

from __future__ import annotations

import json
import re

import pytest
import rendering
import yaml

MANIFEST = rendering.manifest()
VARIABLE = re.compile(r"\$\{([^${}:]+)(?::[^${}]*)?\}")
TARGETS = {"staging": "STAGING", "prod": "PROD"}

# What scripts/deploy-application.py of the infrastructure repository fills for a target stage from
# the deployment project's Tooling environment, each under the stage's prefix, and the names the
# pipeline's jobs carry as CI/CD variables of the GitLab project. ATHENA_WORKGROUP is filled from
# the release that carries the infrastructure repository's Stage 20 change to the leg.
LEG_FILLS = (
    "SUBNET_AZ1",
    "SUBNET_AZ2",
    "PROJECT_SG",
    "PROJECT_KEY_ARN",
    "ACCOUNT_ID",
    "ATHENA_WORKGROUP",
)
PIPELINE = {"DOMAIN_ID", "DOMAIN_REGION"}

STORAGE = {
    "code": "app-dbt/code",
    "glue": "app-dbt/glue",
    "samples": "app-dbt/inbox",
    "workflows": "app-dbt/workflows",
}


def names(node) -> set:
    """Every ${NAME} a manifest subtree reads."""
    if isinstance(node, dict):
        return set().union(set(), *(names(value) for value in node.values()))
    if isinstance(node, list):
        return set().union(set(), *(names(value) for value in node))
    if isinstance(node, str):
        return {match.group(1) for match in VARIABLE.finditer(node)}
    return set()


@pytest.mark.parametrize(
    ("stage", "project", "created", "run"),
    [
        ("dev", "${DEV_PROJECT_NAME}", ["app-dbt", "app-dbt-probe"], []),
        ("staging", "deploy-staging", ["app-dbt", "app-dbt-probe"], []),
        ("prod", "deploy-production", ["app-dbt"], ["app-dbt"]),
    ],
)
def test_each_stage_its_project_its_bootstrap_and_its_storage(stage, project, created, run):
    declared = MANIFEST["stages"][stage]
    assert declared["stage"] == stage.upper()
    assert declared["project"] == {"name": project}
    assert declared["domain"] == {"id": "${DOMAIN_ID}", "region": "${DOMAIN_REGION}"}
    actions = declared["bootstrap"]["actions"]
    creates = [a["workflowName"] for a in actions if a["type"] == "workflow.create"]
    runs = [a for a in actions if a["type"] == "workflow.run"]
    assert creates == created
    assert [a["workflowName"] for a in runs] == run
    assert all(a.get("trailLogs") is True for a in runs)
    assert {a["type"] for a in actions} <= {"workflow.create", "workflow.run"}
    if runs:
        assert actions.index(runs[0]) > max(
            i for i, a in enumerate(actions) if a["type"] == "workflow.create"
        )
    storage = declared["deployment_configuration"]["storage"]
    assert {item["name"]: item["targetDirectory"] for item in storage} == STORAGE
    assert {item["connectionName"] for item in storage} == {"default.s3_shared"}
    assert "catalog" not in declared.get("deployment_configuration", {})


@pytest.mark.parametrize(
    ("stage", "expected"),
    [
        (
            "dev",
            {
                "SUBNET_AZ1": "${SUBNET_AZ1}",
                "SUBNET_AZ2": "${SUBNET_AZ2}",
                "ACCOUNT_ID": "${ACCOUNT_ID}",
                "PRODUCT_DATABASE": "app_dbt",
                "ATHENA_WORKGROUP": "${ATHENA_WORKGROUP}",
                "LINEAGE_DOMAIN": "${LINEAGE_DOMAIN}",
                "LINEAGE_NAMES": "${LINEAGE_NAMES}",
                "LINEAGE_ENDPOINT": "${LINEAGE_ENDPOINT}",
                "LINEAGE_ATTEMPTS": "${LINEAGE_ATTEMPTS}",
            },
        ),
        *(
            (
                stage,
                {
                    "SUBNET_AZ1": f"${{{prefix}_SUBNET_AZ1}}",
                    "SUBNET_AZ2": f"${{{prefix}_SUBNET_AZ2}}",
                    "ACCOUNT_ID": f"${{{prefix}_ACCOUNT_ID}}",
                    "PRODUCT_DATABASE": "app_dbt",
                    "ATHENA_WORKGROUP": f"${{{prefix}_ATHENA_WORKGROUP}}",
                    "LINEAGE_DOMAIN": "${DOMAIN_ID}",
                    "LINEAGE_NAMES": "as-built",
                    "LINEAGE_ENDPOINT": "default",
                    "LINEAGE_ATTEMPTS": "default",
                },
            )
            for stage, prefix in TARGETS.items()
        ),
    ],
)
def test_each_stage_variables(stage, expected):
    assert MANIFEST["stages"][stage]["environment_variables"] == expected


@pytest.mark.parametrize(("stage", "prefix"), TARGETS.items())
def test_a_target_reads_only_what_its_leg_and_the_pipeline_fill(stage, prefix):
    fills = PIPELINE | {f"{prefix}_{name}" for name in LEG_FILLS}
    read = names(MANIFEST["stages"][stage])
    assert read <= fills, sorted(read - fills)


@pytest.mark.parametrize("stage", TARGETS)
def test_a_targets_switches_are_literals_in_their_forms(stage):
    variables = MANIFEST["stages"][stage]["environment_variables"]
    assert variables["LINEAGE_NAMES"] in ("as-built", "glue-arn")
    assert variables["LINEAGE_ENDPOINT"] == "default"
    assert variables["LINEAGE_ATTEMPTS"] == "default"


def test_dev_reads_no_name_of_a_target():
    read = names(MANIFEST["stages"]["dev"])
    assert not {name for name in read if name.startswith(("STAGING_", "PROD_"))}


def test_the_catalog_block_imports_the_dev_projects_assets_and_lists_nothing():
    assert MANIFEST["content"]["catalog"] == {
        "enabled": True,
        "connectionName": "project.default_lakehouse",
        "skipPublish": True,
    }


def test_the_storage_items_are_files_or_folders_of_this_tree():
    storage = MANIFEST["content"]["storage"]
    assert [item["name"] for item in storage] == list(STORAGE)
    for item in storage:
        for include in item["include"]:
            assert "*" not in include, include
            assert (rendering.ROOT / include).exists() or include == "code/app-dbt.zip", include


def test_product_json_names_the_two_tables_the_workflow_writes():
    declared = json.loads((rendering.ROOT / "product.json").read_text(encoding="utf-8"))
    assert sorted(declared["required"]["assets"]) == ["notional_by_desk", "trades"]
    load = yaml.safe_load((rendering.ROOT / "workflows" / "app-dbt.yaml").read_text())
    assert load["app-dbt"]["tasks"]["load"]["script_args"]["--TABLE_NAME"] == "trades"
    assert (rendering.ROOT / "src/app_dbt/project/models/notional_by_desk.sql").is_file()
    assert set(declared.get("allowed", {})) <= {"formTypes", "glossaries", "glossaryTerms"}
