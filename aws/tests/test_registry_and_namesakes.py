"""OR-8 and DT-8 read against each application's shape, the empty cases included (Lesson 87).

OR-8 is orchestration.py's registry_verdicts(): each target's Create/UpdateModelPackage events against
Stage 17 decision 16 (b). DT-8's table half is deploytargets.py's split_namesakes() and
namesake_verdicts(): Staging's local tables named like a lake table. Both scripts are loaded from
their files; neither main() runs.
"""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

import pytest

AWS = Path(__file__).resolve().parents[1]
REPO = AWS.parent


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"awsds_{name}", AWS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


orch = load("orchestration")
dt = load("deploytargets")

PROJECT_ROLE = "arn:aws:sts::000000000000:assumed-role/datazone_usr_role_abc_def/SageMaker"
DEPLOY_PROD = "arn:aws:sts::000000000000:assumed-role/awsds-deploy-prod/gitlab-42"
DEPLOY_STAGING = "arn:aws:sts::000000000000:assumed-role/awsds-deploy-staging/gitlab-41"
APP_ML = "awsds-prod-model-app-ml"


def event(caller: str, when: str = "2026-11-23T18:30:00Z", error: str = "", **params) -> dict:
    ev = {"userIdentity": {"arn": caller}, "eventTime": when, "requestParameters": params}
    if error:
        ev["errorCode"] = error
    return ev


def propose(caller: str = PROJECT_ROLE, group: str = APP_ML, status: str = "PendingManualApproval"):
    return (
        "CreateModelPackage",
        event(caller, modelPackageGroupName=group, modelApprovalStatus=status),
    )


def approve(caller: str = DEPLOY_PROD, group: str = APP_ML):
    arn = f"arn:aws:sagemaker:us-west-2:000000000000:model-package/{group}/1"
    return (
        "UpdateModelPackage",
        event(caller, modelPackageArn=arn, modelApprovalStatus="Approved"),
    )


def verbs(lines: list) -> list:
    return [verb for verb, _subject, _detail in lines]


# ---------------------------------------------------------------------------------------- OR-8


def test_or8_no_event_is_a_note_never_a_pass():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [], [])
    assert verbs(lines) == ["note"]
    assert "an absence, not a pass" in lines[0][2]


def test_or8_app_ml_in_production_passes():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [propose(), approve()], [])
    assert lines == [
        (
            "ok",
            "prod: registry writes",
            "1 version(s) proposed PendingManualApproval by a project role, 1 approval(s) "
            "awsds-deploy-prod's",
        )
    ]


def test_or8_app_ml_in_staging_is_approved_by_the_staging_deploy_role():
    events = [propose(group="awsds-staging-model-app-ml"), approve(DEPLOY_STAGING)]
    assert verbs(orch.registry_verdicts("staging", "awsds-deploy-staging", events, [])) == ["ok"]


def test_or8_production_deploy_role_approving_in_staging_fails():
    lines = orch.registry_verdicts("staging", "awsds-deploy-staging", [approve(DEPLOY_PROD)], [])
    assert verbs(lines) == ["fail"]
    assert "the approval is awsds-deploy-staging's" in lines[0][2]


def test_or8_a_project_role_approving_fails():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [approve(PROJECT_ROLE)], [])
    assert verbs(lines) == ["fail"]


def test_or8_the_deploy_role_registering_in_app_ml_fails():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [propose(DEPLOY_PROD)], [])
    assert verbs(lines) == ["fail"]
    assert "a version is a project role's proposal" in lines[0][2]


def test_or8_a_version_proposed_approved_fails():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [propose(status="Approved")], [])
    assert verbs(lines) == ["fail"]
    assert "a version is proposed PendingManualApproval" in lines[0][2]


def test_or8_the_group_may_be_named_by_its_arn():
    arn = f"arn:aws:sagemaker:us-west-2:000000000000:model-package-group/{APP_ML}"
    assert verbs(orch.registry_verdicts("prod", "awsds-deploy-prod", [propose(group=arn)], [])) == [
        "ok"
    ]


def test_or8_the_retired_shape_alone_is_a_note_and_an_absence():
    retired = propose(DEPLOY_PROD, group="awsds-prod-model-app-etl", status="Approved")
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [retired], [])
    assert verbs(lines) == ["note", "note"]
    assert "app-etl's model half" in lines[0][2]
    assert "an absence, not a pass" in lines[1][2]


def test_or8_the_retired_approval_counts_with_the_retired_shape():
    retired = [
        propose(DEPLOY_PROD, group="awsds-prod-model-app-etl", status="PendingManualApproval"),
        approve(group="awsds-prod-model-app-etl"),
    ]
    lines = orch.registry_verdicts(
        "prod", "awsds-deploy-prod", [*retired, propose(), approve()], []
    )
    assert verbs(lines) == ["note", "ok"]
    assert lines[0][2].startswith("2 event(s) on awsds-prod-model-app-etl")
    assert "1 version(s) proposed" in lines[1][2] and "1 approval(s)" in lines[1][2]


def test_or8_the_retired_shape_beside_app_ml_notes_and_passes():
    retired = propose(DEPLOY_PROD, group="awsds-prod-model-app-etl", status="Approved")
    events = [retired, propose(), approve()]
    assert verbs(orch.registry_verdicts("prod", "awsds-deploy-prod", events, [])) == ["note", "ok"]


def test_or8_the_retired_shape_is_production_deploy_roles_alone():
    staging_registrar = propose(DEPLOY_STAGING, group="awsds-prod-model-app-etl")
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [staging_registrar], [])
    assert verbs(lines) == ["fail"]


def test_or8_a_refused_call_wrote_nothing_and_is_a_note():
    refused = ("UpdateModelPackage", event(PROJECT_ROLE, error="AccessDenied"))
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [refused, propose()], [])
    assert verbs(lines) == ["note", "ok"]
    assert "UpdateModelPackage AccessDenied" in lines[0][2]


def test_or8_an_unread_page_is_a_note():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [propose()], ["UpdateModelPackage"])
    assert verbs(lines) == ["note"]
    assert "not read to the last page" in lines[0][2]


def test_or8_a_bad_write_fails_even_when_a_page_is_unread():
    lines = orch.registry_verdicts(
        "prod", "awsds-deploy-prod", [approve(PROJECT_ROLE)], ["CreateModelPackage"]
    )
    assert verbs(lines) == ["fail"]


def test_or8_an_event_without_parameters_or_caller_fails():
    lines = orch.registry_verdicts("prod", "awsds-deploy-prod", [("CreateModelPackage", {})], [])
    assert verbs(lines) == ["fail"]


def test_or8_reads_one_approver_per_target():
    assert orch.REGISTRY_APPROVERS == {env: f"awsds-deploy-{env}" for env, _p in orch.ORCH_ENVS}


# ---------------------------------------------------------------------------------------- DT-8


def product_databases(env: str) -> tuple:
    text = (REPO / "terraform-live" / env / "foundation" / "deploy-project.tf").read_text()
    match = re.search(r"deployment_product_databases\s*=\s*\[([^\]]*)\]", text)
    assert match, f"{env}/foundation/deploy-project.tf declares no deployment_product_databases"
    return tuple(re.findall(r'"([^"]+)"', match.group(1)))


def test_dt8_product_databases_mirror_the_deploy_project():
    assert dt.STAGING_PRODUCT_DBS == product_databases("staging")


LAKE = {"trades", "trades_raw"}


def test_dt8_app_dbt_trades_is_its_own_namesake():
    copies, own = dt.split_namesakes({"app_dbt": ["trades", "trades_enriched"]}, LAKE)
    assert copies == [] and own == [("app_dbt", "trades")]


def test_dt8_a_namesake_outside_a_product_database_is_a_copy():
    tables = {"scratch": ["trades"], "app_etl": ["trades_notional"]}
    assert dt.split_namesakes(tables, LAKE) == ([("scratch", "trades")], [])


@pytest.mark.parametrize(
    "tables, lake",
    [({}, LAKE), ({"app_etl": []}, LAKE), ({"app_etl": ["trades"]}, set())],
)
def test_dt8_empty_sides_split_into_nothing(tables, lake):
    assert dt.split_namesakes(tables, lake) == ([], [])


def test_dt8_nothing_named_like_the_lake_passes():
    assert verbs(dt.namesake_verdicts([], [], [])) == ["ok"]


def test_dt8_an_unread_catalog_is_a_note_never_a_pass():
    lines = dt.namesake_verdicts(["the lake's tables (Data Governance not measured)"], [], [])
    assert verbs(lines) == ["note"]
    assert "an absence, not a pass" in lines[0][2]


def test_dt8_a_copy_fails_even_when_a_catalog_is_unread():
    lines = dt.namesake_verdicts(["Staging's app_dbt (read failed)"], [("scratch", "trades")], [])
    assert verbs(lines) == ["fail", "note"]


def test_dt8_an_own_namesake_is_noted_beside_the_pass():
    lines = dt.namesake_verdicts([], [], [("app_dbt", "trades")])
    assert verbs(lines) == ["ok", "note"]
    assert lines[1][1] == "staging table app_dbt.trades"
