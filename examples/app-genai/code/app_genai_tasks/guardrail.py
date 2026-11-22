"""The `guardrail` task of app-genai-triage: the application's guardrail kept as the archive's
`guardrail/definition.json` defines it (the infrastructure repository's Stage 17 decision 24 (b)).

The guardrail is `app-genai-<project id>`, found by its name in ListGuardrails, which without an
identifier lists the DRAFT of every guardrail of the account. Where there is none, the task creates
it with the definition and the project's tag. Where the guardrail carries the SHA-256 of the
definition in its tag `awsds:definition-sha256`, and the version its tag `awsds:definition-version`
names reads READY, the task writes nothing. Otherwise it sends the whole definition with
UpdateGuardrail, a full replacement of the DRAFT, and waits for READY. A created or updated DRAFT is
then published with CreateGuardrailVersion, the hash as the version's description, and the tags
name the hash and the new version.

The hash is a tag because neither GetGuardrail nor ListGuardrails is documented to return the
description a version was published with: the API reference gives GetGuardrail's `description` as
the guardrail's (read 2026-11-17). The task compares the description GetGuardrail returns for the
published version with the hash and returns the verdict, the reading that settles it.

The task runs as the project role through the `bedrock` endpoint with the boto3 the worker carries.
It returns the guardrail's identifiers, the version and what it changed as JSON text, the XCom
`triage` reads.
"""

from __future__ import annotations

import hashlib
import json
import re
import time

from .common import bundled, error_code

DEFINITION = "guardrail/definition.json"
NAME_PREFIX = "app-genai-"
NAME_PATTERN = re.compile(r"[0-9a-zA-Z_-]{1,50}")
PROJECT_TAG = "AmazonDataZoneProject"
HASH_TAG = "awsds:definition-sha256"
VERSION_TAG = "awsds:definition-version"
# The members of the definition the task sets itself.
TASK_MEMBERS = ("name", "tags", "guardrailIdentifier", "clientRequestToken")
# The statuses a guardrail or a version passes through before READY.
PENDING = ("CREATING", "UPDATING", "VERSIONING")
READY_TIMEOUT = 300
POLL_SECONDS = 5


def load_definition(path=None) -> dict:
    """The definition: the members of a CreateGuardrail request but the name and the tags."""
    definition = json.loads((path or bundled(DEFINITION)).read_text(encoding="utf-8"))
    present = [member for member in TASK_MEMBERS if member in definition]
    if present:
        raise ValueError(f"{DEFINITION} carries {', '.join(present)}, which the task sets")
    return definition


def definition_hash(definition: dict) -> str:
    """The SHA-256 of the definition's canonical JSON: sorted keys, no spaces, UTF-8."""
    text = json.dumps(definition, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def guardrail_name(project: str) -> str:
    """`app-genai-<project id>`, within the 50 characters and the alphabet of a guardrail's name."""
    project = str(project).strip()
    name = NAME_PREFIX + project
    if not project or not NAME_PATTERN.fullmatch(name):
        raise ValueError(f"no guardrail name from the project id {project!r}")
    return name


def find_guardrail(bedrock, name: str) -> dict | None:
    """The summary of the account's guardrail named `name`, None where there is none; two of the
    name fail."""
    found = []
    for page in bedrock.get_paginator("list_guardrails").paginate():
        found.extend(item for item in page.get("guardrails", []) if item["name"] == name)
    if len(found) > 1:
        raise RuntimeError(f"{len(found)} guardrails named {name} in the account, one expected")
    return found[0] if found else None


def wait_ready(
    bedrock,
    guardrail_id: str,
    version: str = "",
    timeout: int = READY_TIMEOUT,
    sleep=time.sleep,
) -> dict:
    """GetGuardrail on the DRAFT, or on `version`, until it reads READY; FAILED, any other status
    and `timeout` seconds fail."""
    request = {"guardrailIdentifier": guardrail_id}
    if version:
        request["guardrailVersion"] = version
    waited = 0
    while True:
        got = bedrock.get_guardrail(**request)
        status = got["status"]
        if status == "READY":
            return got
        which = f"guardrail {guardrail_id} version {version or 'DRAFT'}"
        if status not in PENDING:
            reasons = "; ".join(got.get("statusReasons") or []) or "no reason given"
            raise RuntimeError(f"{which} is {status}: {reasons}")
        if waited >= timeout:
            raise RuntimeError(f"{which} still {status} after {timeout} s")
        sleep(POLL_SECONDS)
        waited += POLL_SECONDS


def published(bedrock, guardrail_id: str, version: str) -> dict | None:
    """GetGuardrail on a numbered version, None where the version is gone or not READY."""
    from botocore.exceptions import ClientError

    try:
        got = bedrock.get_guardrail(guardrailIdentifier=guardrail_id, guardrailVersion=version)
    except ClientError as exc:
        if error_code(exc) == "ResourceNotFoundException":
            return None
        raise
    return got if got["status"] == "READY" else None


def keep_guardrail(
    bedrock,
    project: str,
    definition: dict,
    timeout: int = READY_TIMEOUT,
    sleep=time.sleep,
) -> dict:
    """The application's guardrail as `definition` defines it, created, updated or left as it is,
    with its published version."""
    digest = definition_hash(definition)
    name = guardrail_name(project)
    found = find_guardrail(bedrock, name)
    if found is None:
        created = bedrock.create_guardrail(
            name=name, tags=[{"key": PROJECT_TAG, "value": str(project).strip()}], **definition
        )
        guardrail_id, arn = created["guardrailId"], created["guardrailArn"]
        wait_ready(bedrock, guardrail_id, timeout=timeout, sleep=sleep)
        change = "created"
    else:
        guardrail_id, arn = found["id"], found["arn"]
        if found["status"] != "READY":
            wait_ready(bedrock, guardrail_id, timeout=timeout, sleep=sleep)
        tags = {
            tag["key"]: tag["value"]
            for tag in bedrock.list_tags_for_resource(resourceARN=arn).get("tags", [])
        }
        version = tags.get(VERSION_TAG, "")
        if tags.get(HASH_TAG) == digest and version:
            got = published(bedrock, guardrail_id, version)
            if got is not None:
                return result(name, guardrail_id, arn, version, digest, "unchanged", got)
        bedrock.update_guardrail(guardrailIdentifier=guardrail_id, name=name, **definition)
        wait_ready(bedrock, guardrail_id, timeout=timeout, sleep=sleep)
        change = "updated"
    version = bedrock.create_guardrail_version(
        guardrailIdentifier=guardrail_id, description=digest
    )["version"]
    got = wait_ready(bedrock, guardrail_id, version, timeout=timeout, sleep=sleep)
    bedrock.tag_resource(
        resourceARN=arn,
        tags=[{"key": HASH_TAG, "value": digest}, {"key": VERSION_TAG, "value": version}],
    )
    return result(name, guardrail_id, arn, version, digest, change, got)


def result(
    name: str, guardrail_id: str, arn: str, version: str, digest: str, change: str, got: dict
) -> dict:
    """The task's return: the guardrail, its published version, the definition's hash, what the run
    changed, and whether GetGuardrail on the version returned the hash as its description."""
    return {
        "name": name,
        "id": guardrail_id,
        "arn": arn,
        "version": version,
        "sha256": digest,
        "change": change,
        "version_description_is_hash": got.get("description") == digest,
    }


def ensure_guardrail(project: str, region: str = "", **context) -> str:
    """The task: the guardrail kept, its identifiers and version returned as JSON text."""
    import boto3

    bedrock = boto3.client("bedrock", region_name=region or None)
    kept = keep_guardrail(bedrock, project, load_definition())
    print(
        f"guardrail {kept['name']} ({kept['id']}): {kept['change']}, version {kept['version']}, "
        f"definition sha256 {kept['sha256']}; GetGuardrail on the version returns the hash as its "
        f"description: {kept['version_description_is_hash']}"
    )
    return json.dumps(kept, indent=2, sort_keys=True) + "\n"
