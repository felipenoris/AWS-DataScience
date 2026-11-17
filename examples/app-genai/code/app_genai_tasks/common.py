"""What the tasks share: the files the archive carries beside the package, S3 URIs, the XCom a
template hands a task, and what each guardrail did to a request, read from the Converse trace
without the values it matched."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from urllib.parse import urlparse

PACKAGE = Path(__file__).resolve().parent
# Where a file the archive carries is read: at the archive's root, beside the package, where the
# worker extracts it (/usr/local/airflow/dags); then at the application's root, the repository's
# layout, where the package sits in code/.
ROOTS = (PACKAGE.parent, PACKAGE.parent.parent)

# The policies of a guardrail assessment the record keeps: (the assessment's member, its list, the
# kind recorded, the member naming the item). A custom word has no name of its own, only the text
# it matched, so it is recorded as `custom`.
POLICIES = (
    ("topicPolicy", "topics", "topic", "name"),
    ("contentPolicy", "filters", "filter", "type"),
    ("wordPolicy", "customWords", "word", None),
    ("wordPolicy", "managedWordLists", "word", "type"),
    ("sensitiveInformationPolicy", "piiEntities", "pii", "type"),
    ("sensitiveInformationPolicy", "regexes", "regex", "name"),
    ("contextualGroundingPolicy", "filters", "grounding", "type"),
)


def bundled(relative: str) -> Path:
    """The path of a file the archive carries, such as `prompts/triage.md`."""
    for root in ROOTS:
        path = root / relative
        if path.is_file():
            return path
    raise FileNotFoundError(f"{relative}: neither beside the package nor at the application's root")


def split_uri(uri: str) -> tuple[str, str]:
    """`s3://bucket/key` -> (`bucket`, `key`)."""
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"not an s3:// URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def read_text(s3, uri: str) -> str:
    bucket, key = split_uri(uri)
    return s3.get_object(Bucket=bucket, Key=key)["Body"].read().decode("utf-8")


def write_text(s3, uri: str, text: str, content_type: str) -> None:
    bucket, key = split_uri(uri)
    s3.put_object(Bucket=bucket, Key=key, Body=text.encode("utf-8"), ContentType=content_type)


def read_jsonl(s3, uri: str) -> list[dict]:
    """Each non-empty line of a JSON Lines object, parsed; a line that is no JSON object fails with
    its number, never its text."""
    records = []
    for number, line in enumerate(read_text(s3, uri).splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{uri}: line {number} is not JSON") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{uri}: line {number} is not a JSON object")
        records.append(record)
    return records


def decode(value, what: str) -> dict:
    """The dict a task returned, from the XCom a template hands the next task.

    The worker renders an XCom as the JSON of its value (read 2026-10-24 in Staging), so the JSON
    text a task returns can arrive encoded once more: the value is decoded until a dict appears, and
    the Python literal a template renders a dict as is read too.
    """
    for _ in range(3):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError(f"{what} is neither JSON nor a literal") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{what} is no mapping: {type(value).__name__}")
    return value


def error_code(error: Exception) -> str:
    """The AWS error code of a botocore ClientError, empty for any other exception."""
    return str(getattr(error, "response", {}).get("Error", {}).get("Code", ""))


def actions(assessment: dict) -> list[list[str]]:
    """What one guardrail assessment did, as `[kind, name, action]` triples, in the trace's order.
    The values a policy matched (`match`) and the model's output never enter a triple."""
    found = []
    for member, items, kind, name in POLICIES:
        for item in (assessment.get(member) or {}).get(items) or []:
            label = str(item.get(name, "")) if name else "custom"
            found.append([kind, label, str(item.get("action", "NONE"))])
    return found


def guardrail_key(key: str, assessment: dict) -> str:
    """The guardrail an assessment belongs to: the id its applied details name, else the trace's
    key, an id or an ARN reduced to its id."""
    details = assessment.get("appliedGuardrailDetails") or {}
    if details.get("guardrailId"):
        return str(details["guardrailId"])
    if "guardrail/" in key:
        return key.split("guardrail/", 1)[1].split(":", 1)[0]
    return key


def assessments(trace: dict) -> dict:
    """What each guardrail did to one request, by guardrail id: its origin and version as the
    applied details name them, the input assessment's actions and every output assessment's."""
    found: dict[str, dict] = {}

    def entry(key: str, assessment: dict) -> dict:
        guardrail = guardrail_key(key, assessment)
        item = found.setdefault(guardrail, {"input": [], "output": []})
        details = assessment.get("appliedGuardrailDetails") or {}
        if details.get("guardrailOrigin"):
            item["origin"] = list(details["guardrailOrigin"])
        if details.get("guardrailVersion"):
            item["version"] = str(details["guardrailVersion"])
        return item

    for key, assessment in (trace.get("inputAssessment") or {}).items():
        entry(key, assessment)["input"].extend(actions(assessment))
    for key, outputs in (trace.get("outputAssessments") or {}).items():
        for assessment in outputs or []:
            entry(key, assessment)["output"].extend(actions(assessment))
    return found


def blocked(guardrails: dict) -> bool:
    """Whether any guardrail blocked the request or its answer. A masked entity reads ANONYMIZED,
    and the stop reason reads `guardrail_intervened` for a mask as for a block, so the actions
    decide."""
    return any(
        action == "BLOCKED"
        for item in guardrails.values()
        for side in ("input", "output")
        for _, _, action in item.get(side, [])
    )
