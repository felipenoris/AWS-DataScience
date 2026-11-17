"""guardrail/definition.json against botocore's bedrock model at the worker's 1.43.1: the request
`guardrail` sends to create the guardrail and the one it sends to update it, each through a Stubber,
whose client validates the required members, the types and the minimums, and the model's maximums,
enums and patterns walked here, which the client does not check."""

from __future__ import annotations

import re

import botocore
from botocore.stub import Stubber

from app_genai_tasks import guardrail
from conftest import ACCOUNT, NOW, client

DEFINITION = guardrail.load_definition()
NAME = "app-genai-p1"
GID = "gr1abc"
ARN = f"arn:aws:bedrock:us-west-2:{ACCOUNT}:guardrail/{GID}"


def problems(value, shape, path: str = "") -> list[str]:
    """Where `value` breaks the shape's maximums, enums, patterns and members."""
    found = []
    kind = shape.type_name
    metadata = shape.metadata
    if kind == "structure":
        if not isinstance(value, dict):
            return [f"{path}: not a structure"]
        for name in shape.required_members:
            if name not in value:
                found.append(f"{path}.{name}: required")
        for name, item in value.items():
            if name not in shape.members:
                found.append(f"{path}.{name}: no such member")
            else:
                found.extend(problems(item, shape.members[name], f"{path}.{name}"))
    elif kind == "list":
        if not isinstance(value, list):
            return [f"{path}: not a list"]
        if "max" in metadata and len(value) > metadata["max"]:
            found.append(f"{path}: {len(value)} items, over {metadata['max']}")
        if "min" in metadata and len(value) < metadata["min"]:
            found.append(f"{path}: {len(value)} items, under {metadata['min']}")
        for index, item in enumerate(value):
            found.extend(problems(item, shape.member, f"{path}[{index}]"))
    elif kind == "string":
        if not isinstance(value, str):
            return [f"{path}: not a string"]
        if shape.enum and value not in shape.enum:
            found.append(f"{path}: {value!r} not in {shape.enum}")
        if "max" in metadata and len(value) > metadata["max"]:
            found.append(f"{path}: {len(value)} characters, over {metadata['max']}")
        if "min" in metadata and len(value) < metadata["min"]:
            found.append(f"{path}: {len(value)} characters, under {metadata['min']}")
        if "pattern" in metadata and not re.fullmatch(metadata["pattern"], value):
            found.append(f"{path}: {value!r} does not match {metadata['pattern']}")
    elif kind == "boolean" and not isinstance(value, bool):
        found.append(f"{path}: not a boolean")
    return found


def test_the_model_is_the_workers():
    assert botocore.__version__ == "1.43.1"


def test_the_create_request_passes_the_model():
    bedrock = client("bedrock")
    request = {
        "name": NAME,
        "tags": [{"key": guardrail.PROJECT_TAG, "value": "p1"}],
        **DEFINITION,
    }
    shape = bedrock.meta.service_model.operation_model("CreateGuardrail").input_shape
    assert problems(request, shape) == []
    stub = Stubber(bedrock)
    stub.add_response(
        "create_guardrail",
        {"guardrailId": GID, "guardrailArn": ARN, "version": "DRAFT", "createdAt": NOW},
        request,
    )
    with stub:
        assert bedrock.create_guardrail(**request)["version"] == "DRAFT"
    stub.assert_no_pending_responses()


def test_the_update_request_passes_the_model():
    bedrock = client("bedrock")
    request = {"guardrailIdentifier": GID, "name": NAME, **DEFINITION}
    shape = bedrock.meta.service_model.operation_model("UpdateGuardrail").input_shape
    assert problems(request, shape) == []
    stub = Stubber(bedrock)
    stub.add_response(
        "update_guardrail",
        {"guardrailId": GID, "guardrailArn": ARN, "version": "DRAFT", "updatedAt": NOW},
        request,
    )
    with stub:
        assert bedrock.update_guardrail(**request)["version"] == "DRAFT"
    stub.assert_no_pending_responses()


def test_the_walk_finds_what_the_client_does_not_check():
    shape = client("bedrock").meta.service_model.operation_model("CreateGuardrail").input_shape
    broken = {
        "name": "a name with spaces",
        **DEFINITION,
        "blockedInputMessaging": "x" * 501,
    }
    found = problems(broken, shape)
    assert any(item.startswith(".name:") for item in found)
    assert any(item.startswith(".blockedInputMessaging:") for item in found)


def test_the_definition_stays_in_the_region_under_the_aws_owned_key():
    assert "crossRegionConfig" not in DEFINITION
    assert "kmsKeyId" not in DEFINITION
    assert DEFINITION["topicPolicyConfig"]["tierConfig"] == {"tierName": "CLASSIC"}
    assert DEFINITION["contentPolicyConfig"]["tierConfig"] == {"tierName": "CLASSIC"}


def test_the_definition_holds_what_the_check_reads():
    topics = DEFINITION["topicPolicyConfig"]["topicsConfig"]
    assert [topic["type"] for topic in topics] == ["DENY"]
    assert all(topic["inputAction"] == "BLOCK" for topic in topics)
    filters = {item["type"]: item for item in DEFINITION["contentPolicyConfig"]["filtersConfig"]}
    assert filters["PROMPT_ATTACK"]["inputStrength"] != "NONE"
    assert filters["PROMPT_ATTACK"]["outputStrength"] == "NONE"
    entities = {
        item["type"]: item
        for item in DEFINITION["sensitiveInformationPolicyConfig"]["piiEntitiesConfig"]
    }
    for entity in ("EMAIL", "PHONE"):
        assert entities[entity]["inputAction"] == "ANONYMIZE"
        assert entities[entity]["outputAction"] == "ANONYMIZE"


def test_the_hash_is_the_canonical_json():
    reordered = dict(reversed(list(DEFINITION.items())))
    assert guardrail.definition_hash(reordered) == guardrail.definition_hash(DEFINITION)
    changed = {**DEFINITION, "description": DEFINITION["description"] + "."}
    assert guardrail.definition_hash(changed) != guardrail.definition_hash(DEFINITION)
    assert re.fullmatch(r"[0-9a-f]{64}", guardrail.definition_hash(DEFINITION))
