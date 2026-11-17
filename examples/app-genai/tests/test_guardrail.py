"""The `guardrail` task over a Stubber on the bedrock client: its three paths, each by the exact
requests it sends, and its refusals."""

from __future__ import annotations

import json

import pytest
from botocore.stub import Stubber

from app_genai_tasks import guardrail
from conftest import ACCOUNT, NOW, client, operations

PROJECT = "p1"
NAME = "app-genai-p1"
GID = "gr1abc"
ARN = f"arn:aws:bedrock:us-west-2:{ACCOUNT}:guardrail/{GID}"
DEFINITION = guardrail.load_definition()
DIGEST = guardrail.definition_hash(DEFINITION)
WRITES = {"CreateGuardrail", "UpdateGuardrail", "CreateGuardrailVersion", "TagResource"}


def summary(name: str = NAME, status: str = "READY", gid: str = GID) -> dict:
    return {
        "id": gid,
        "arn": f"arn:aws:bedrock:us-west-2:{ACCOUNT}:guardrail/{gid}",
        "status": status,
        "name": name,
        "version": "DRAFT",
        "createdAt": NOW,
        "updatedAt": NOW,
    }


def got(status: str = "READY", version: str = "DRAFT", description: str | None = None) -> dict:
    response = {
        "name": NAME,
        "guardrailId": GID,
        "guardrailArn": ARN,
        "version": version,
        "status": status,
        "createdAt": NOW,
        "updatedAt": NOW,
        "blockedInputMessaging": DEFINITION["blockedInputMessaging"],
        "blockedOutputsMessaging": DEFINITION["blockedOutputsMessaging"],
    }
    if description:
        response["description"] = description
    return response


def tags(digest: str, version: str) -> dict:
    return {
        "tags": [
            {"key": guardrail.PROJECT_TAG, "value": PROJECT},
            {"key": guardrail.HASH_TAG, "value": digest},
            {"key": guardrail.VERSION_TAG, "value": version},
        ]
    }


def stubbed():
    bedrock = client("bedrock")
    return bedrock, Stubber(bedrock), operations(bedrock)


def test_no_guardrail_of_the_name_is_created_and_published():
    bedrock, stub, calls = stubbed()
    stub.add_response(
        "list_guardrails", {"guardrails": [summary("app-genai-other", gid="gr2")]}, {}
    )
    stub.add_response(
        "create_guardrail",
        {"guardrailId": GID, "guardrailArn": ARN, "version": "DRAFT", "createdAt": NOW},
        {"name": NAME, "tags": [{"key": "AmazonDataZoneProject", "value": PROJECT}], **DEFINITION},
    )
    stub.add_response("get_guardrail", got("CREATING"), {"guardrailIdentifier": GID})
    stub.add_response("get_guardrail", got("READY"), {"guardrailIdentifier": GID})
    stub.add_response(
        "create_guardrail_version",
        {"guardrailId": GID, "version": "1"},
        {"guardrailIdentifier": GID, "description": DIGEST},
    )
    stub.add_response(
        "get_guardrail",
        got("READY", "1", DIGEST),
        {"guardrailIdentifier": GID, "guardrailVersion": "1"},
    )
    stub.add_response(
        "tag_resource",
        {},
        {
            "resourceARN": ARN,
            "tags": [
                {"key": "awsds:definition-sha256", "value": DIGEST},
                {"key": "awsds:definition-version", "value": "1"},
            ],
        },
    )
    sleeps = []
    with stub:
        kept = guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION, sleep=sleeps.append)
    stub.assert_no_pending_responses()
    assert [call for call in calls if call in WRITES] == [
        "CreateGuardrail",
        "CreateGuardrailVersion",
        "TagResource",
    ]
    assert kept == {
        "name": NAME,
        "id": GID,
        "arn": ARN,
        "version": "1",
        "sha256": DIGEST,
        "change": "created",
        "version_description_is_hash": True,
    }
    assert sleeps == [guardrail.POLL_SECONDS]


def test_a_version_carrying_the_hash_sends_no_write():
    bedrock, stub, calls = stubbed()
    stub.add_response("list_guardrails", {"guardrails": [summary()]}, {})
    stub.add_response("list_tags_for_resource", tags(DIGEST, "3"), {"resourceARN": ARN})
    stub.add_response(
        "get_guardrail",
        got("READY", "3", DIGEST),
        {"guardrailIdentifier": GID, "guardrailVersion": "3"},
    )
    with stub:
        kept = guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION, sleep=pytest.fail)
    stub.assert_no_pending_responses()
    assert [call for call in calls if call in WRITES] == []
    assert calls == ["ListGuardrails", "ListTagsForResource", "GetGuardrail"]
    assert (kept["change"], kept["version"]) == ("unchanged", "3")


def test_a_changed_definition_is_sent_whole_before_one_version():
    bedrock, stub, calls = stubbed()
    stub.add_response("list_guardrails", {"guardrails": [summary()]}, {})
    stub.add_response("list_tags_for_resource", tags("0" * 64, "3"), {"resourceARN": ARN})
    stub.add_response(
        "update_guardrail",
        {"guardrailId": GID, "guardrailArn": ARN, "version": "DRAFT", "updatedAt": NOW},
        {"guardrailIdentifier": GID, "name": NAME, **DEFINITION},
    )
    stub.add_response("get_guardrail", got("UPDATING"), {"guardrailIdentifier": GID})
    stub.add_response("get_guardrail", got("READY"), {"guardrailIdentifier": GID})
    stub.add_response(
        "create_guardrail_version",
        {"guardrailId": GID, "version": "4"},
        {"guardrailIdentifier": GID, "description": DIGEST},
    )
    stub.add_response(
        "get_guardrail",
        got("READY", "4", DEFINITION["description"]),
        {"guardrailIdentifier": GID, "guardrailVersion": "4"},
    )
    stub.add_response(
        "tag_resource",
        {},
        {
            "resourceARN": ARN,
            "tags": [
                {"key": "awsds:definition-sha256", "value": DIGEST},
                {"key": "awsds:definition-version", "value": "4"},
            ],
        },
    )
    with stub:
        kept = guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION, sleep=lambda _: None)
    stub.assert_no_pending_responses()
    assert [call for call in calls if call in WRITES] == [
        "UpdateGuardrail",
        "CreateGuardrailVersion",
        "TagResource",
    ]
    assert (kept["change"], kept["version"]) == ("updated", "4")
    assert kept["version_description_is_hash"] is False


def test_a_hash_whose_version_is_gone_is_published_again():
    bedrock, stub, calls = stubbed()
    stub.add_response("list_guardrails", {"guardrails": [summary()]}, {})
    stub.add_response("list_tags_for_resource", tags(DIGEST, "3"), {"resourceARN": ARN})
    stub.add_client_error(
        "get_guardrail",
        service_error_code="ResourceNotFoundException",
        http_status_code=404,
        expected_params={"guardrailIdentifier": GID, "guardrailVersion": "3"},
    )
    stub.add_response(
        "update_guardrail",
        {"guardrailId": GID, "guardrailArn": ARN, "version": "DRAFT", "updatedAt": NOW},
        {"guardrailIdentifier": GID, "name": NAME, **DEFINITION},
    )
    stub.add_response("get_guardrail", got("READY"), {"guardrailIdentifier": GID})
    stub.add_response(
        "create_guardrail_version",
        {"guardrailId": GID, "version": "4"},
        {"guardrailIdentifier": GID, "description": DIGEST},
    )
    stub.add_response(
        "get_guardrail", got("READY", "4"), {"guardrailIdentifier": GID, "guardrailVersion": "4"}
    )
    stub.add_response("tag_resource", {}, None)
    with stub:
        kept = guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION, sleep=lambda _: None)
    stub.assert_no_pending_responses()
    assert kept["change"] == "updated"
    assert "UpdateGuardrail" in calls


def test_a_guardrail_mid_change_is_waited_for_before_its_tags_are_read():
    bedrock, stub, _ = stubbed()
    stub.add_response("list_guardrails", {"guardrails": [summary(status="VERSIONING")]}, {})
    stub.add_response("get_guardrail", got("READY"), {"guardrailIdentifier": GID})
    stub.add_response("list_tags_for_resource", tags(DIGEST, "2"), {"resourceARN": ARN})
    stub.add_response(
        "get_guardrail", got("READY", "2"), {"guardrailIdentifier": GID, "guardrailVersion": "2"}
    )
    with stub:
        kept = guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION, sleep=lambda _: None)
    assert kept["change"] == "unchanged"


def test_two_guardrails_of_the_name_fail():
    bedrock, stub, _ = stubbed()
    stub.add_response(
        "list_guardrails", {"guardrails": [summary(gid="gr1"), summary(gid="gr2")]}, {}
    )
    with stub, pytest.raises(RuntimeError, match="2 guardrails named app-genai-p1"):
        guardrail.keep_guardrail(bedrock, PROJECT, DEFINITION)


def test_the_name_is_found_across_pages():
    bedrock, stub, _ = stubbed()
    stub.add_response(
        "list_guardrails", {"guardrails": [summary("other", gid="gr9")], "nextToken": "t2"}, {}
    )
    stub.add_response("list_guardrails", {"guardrails": [summary()]}, {"nextToken": "t2"})
    with stub:
        assert guardrail.find_guardrail(bedrock, NAME)["id"] == GID


def test_a_failed_guardrail_fails_with_its_reasons():
    bedrock, stub, _ = stubbed()
    failed = {**got("FAILED"), "statusReasons": ["the topic definition is too long"]}
    stub.add_response("get_guardrail", failed, {"guardrailIdentifier": GID})
    with stub, pytest.raises(RuntimeError, match="FAILED: the topic definition is too long"):
        guardrail.wait_ready(bedrock, GID, sleep=lambda _: None)


def test_a_guardrail_that_never_reads_ready_fails_at_the_bound():
    bedrock, stub, _ = stubbed()
    for _ in range(3):
        stub.add_response("get_guardrail", got("UPDATING"), {"guardrailIdentifier": GID})
    with stub, pytest.raises(RuntimeError, match="still UPDATING after 10 s"):
        guardrail.wait_ready(bedrock, GID, timeout=10, sleep=lambda _: None)


@pytest.mark.parametrize("project", ["", "  ", "a/b", "x" * 41])
def test_no_name_from_a_project_id_outside_the_alphabet_or_the_length(project):
    with pytest.raises(ValueError, match="no guardrail name"):
        guardrail.guardrail_name(project)


def test_a_definition_carrying_what_the_task_sets_is_refused(tmp_path):
    path = tmp_path / "definition.json"
    path.write_text(json.dumps({**DEFINITION, "name": "x", "tags": []}))
    with pytest.raises(ValueError, match="carries name, tags"):
        guardrail.load_definition(path)


def test_the_task_returns_json_text_and_logs_the_outcome(boto3_clients, capsys):
    bedrock, stub, _ = stubbed()
    boto3_clients["bedrock"] = bedrock
    stub.add_response("list_guardrails", {"guardrails": [summary()]}, {})
    stub.add_response("list_tags_for_resource", tags(DIGEST, "3"), {"resourceARN": ARN})
    stub.add_response(
        "get_guardrail", got("READY", "3"), {"guardrailIdentifier": GID, "guardrailVersion": "3"}
    )
    with stub:
        text = guardrail.ensure_guardrail(project=PROJECT, region="us-west-2")
    assert json.loads(text)["arn"] == ARN
    out = capsys.readouterr().out
    assert f"guardrail {NAME} ({GID}): unchanged, version 3" in out
    assert "returns the hash as its description: False" in out
