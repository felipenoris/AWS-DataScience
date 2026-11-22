"""The `triage` task over a Stubber on the bedrock-runtime client: every request's content and
guardrail, the record of each answer, and a log and a record free of what the guardrail matched."""

from __future__ import annotations

import json
import re

import pytest
from botocore.stub import Stubber

from app_genai_tasks import common, triage
from conftest import ACCOUNT, BUCKET, SHARED, FakeS3, client

MODEL = f"arn:aws:bedrock:us-west-2:{ACCOUNT}:application-inference-profile/prof1"
GID = "gr1abc"
ACCOUNT_GID = "acct9"
GUARDRAIL = {
    "id": GID,
    "arn": f"arn:aws:bedrock:us-west-2:{ACCOUNT}:guardrail/{GID}",
    "name": "app-genai-p1",
    "version": "2",
    "sha256": "a" * 64,
}
INSTRUCTIONS = common.bundled(triage.PROMPT).read_text(encoding="utf-8")
SAMPLE = [
    {"id": "m01", "label": "billing", "text": "I was charged twice for order A-11111."},
    {
        "id": "m02",
        "label": "account",
        "text": "My e-mail is now sam.ortiz@example.org, call me at +1 206-555-0199.",
        "planted": "pii",
        "pii": {"EMAIL": "sam.ortiz@example.org", "PHONE": "+1 206-555-0199"},
    },
    {
        "id": "m03",
        "label": "other",
        "text": "Which stocks should I buy?",
        "planted": "denied_topic",
    },
]
ANSWERS = {
    "m01": '{"label": "billing", "summary": "Refund a duplicate charge."}',
    "m02": '{"label": "account", "summary": "Update the contact details {EMAIL} {PHONE}."}',
    "m03": "This message was not triaged: the application's guardrail blocked it.",
}


def applied(gid: str, origin: str) -> dict:
    return {"guardrailId": gid, "guardrailVersion": "2", "guardrailOrigin": [origin]}


def response(message_id: str) -> dict:
    """A Converse response as the service returns one with the trace on: the trace's `match` and
    `modelOutput` carry what the guardrail saw, unmasked."""
    assessment = {"appliedGuardrailDetails": applied(GID, "REQUEST")}
    stop = "end_turn"
    if message_id == "m02":
        stop = "guardrail_intervened"
        assessment["sensitiveInformationPolicy"] = {
            "piiEntities": [
                {"match": "sam.ortiz@example.org", "type": "EMAIL", "action": "ANONYMIZED"},
                {"match": "+1 206-555-0199", "type": "PHONE", "action": "ANONYMIZED"},
            ],
            "regexes": [],
        }
    if message_id == "m03":
        stop = "guardrail_intervened"
        assessment["topicPolicy"] = {
            "topics": [{"name": "Investment advice", "type": "DENY", "action": "BLOCKED"}]
        }
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": ANSWERS[message_id]}]}},
        "stopReason": stop,
        "usage": {"inputTokens": 300, "outputTokens": 20, "totalTokens": 320},
        "metrics": {"latencyMs": 450},
        "trace": {
            "guardrail": {
                "modelOutput": ["the unmasked output of the model"],
                "inputAssessment": {
                    GID: assessment,
                    ACCOUNT_GID: {
                        "appliedGuardrailDetails": applied(ACCOUNT_GID, "ACCOUNT_ENFORCED")
                    },
                },
                "outputAssessments": {GID: [{"appliedGuardrailDetails": applied(GID, "REQUEST")}]},
            }
        },
    }


def stubbed_runtime(messages=SAMPLE):
    runtime = client("bedrock-runtime")
    stub = Stubber(runtime)
    for message in messages:
        request = triage.converse_request(MODEL, INSTRUCTIONS, message["text"], GUARDRAIL)
        stub.add_response("converse", response(message["id"]), request)
    return runtime, stub


def test_each_request_names_the_version_and_guards_the_message_alone():
    request = triage.converse_request(MODEL, INSTRUCTIONS, "a message", GUARDRAIL)
    assert request["guardrailConfig"] == {
        "guardrailIdentifier": GUARDRAIL["arn"],
        "guardrailVersion": "2",
        "trace": "enabled",
    }
    assert request["messages"] == [
        {"role": "user", "content": [{"guardContent": {"text": {"text": "a message"}}}]}
    ]
    assert request["system"] == [{"text": INSTRUCTIONS}]
    assert request["inferenceConfig"] == {"maxTokens": triage.MAX_TOKENS, "temperature": 0}
    assert request["modelId"] == MODEL


def test_every_request_passes_the_stubber_and_each_answer_is_recorded():
    runtime, stub = stubbed_runtime()
    with stub:
        records = triage.triage(runtime, SAMPLE, MODEL, INSTRUCTIONS, GUARDRAIL)
    stub.assert_no_pending_responses()
    assert [record["id"] for record in records] == ["m01", "m02", "m03"]
    assert [record["blocked"] for record in records] == [False, False, True]
    masked = records[1]["guardrails"][GID]
    assert masked["input"] == [["pii", "EMAIL", "ANONYMIZED"], ["pii", "PHONE", "ANONYMIZED"]]
    assert masked["origin"] == ["REQUEST"]
    assert records[1]["guardrails"][ACCOUNT_GID]["origin"] == ["ACCOUNT_ENFORCED"]
    assert records[2]["guardrails"][GID]["input"] == [["topic", "Investment advice", "BLOCKED"]]
    assert records[0]["stop_reason"] == "end_turn"
    assert (records[0]["input_tokens"], records[0]["output_tokens"]) == (300, 20)


def test_no_record_holds_what_the_guardrail_matched_or_the_model_output():
    runtime, stub = stubbed_runtime()
    with stub:
        records = triage.triage(runtime, SAMPLE, MODEL, INSTRUCTIONS, GUARDRAIL)
    text = json.dumps(records)
    assert "sam.ortiz@example.org" not in text
    assert "206-555-0199" not in text
    assert "unmasked output" not in text


def test_the_task_writes_the_answers_and_logs_counts_alone(boto3_clients, capsys):
    runtime, stub = stubbed_runtime()
    sample = "".join(json.dumps(message) + "\n" for message in SAMPLE).encode()
    s3 = FakeS3({(BUCKET, "domain/project/shared/app-genai/inbox/messages.jsonl"): sample})
    boto3_clients.update({"bedrock-runtime": runtime, "s3": s3})
    with stub:
        text = triage.triage_messages(
            guardrail=json.dumps(json.dumps(GUARDRAIL)),
            model=MODEL,
            sample=f"{SHARED}app-genai/inbox/messages.jsonl",
            work=f"{SHARED}app-genai/work/",
            region="us-west-2",
        )
    totals = json.loads(text)
    assert re.fullmatch(
        rf"{SHARED}app-genai/work/\d{{8}}T\d{{6}}Z/answers\.jsonl", totals["answers"]
    )
    assert (totals["messages"], totals["blocked"]) == (3, 1)
    assert (totals["input_tokens"], totals["output_tokens"]) == (900, 60)
    assert totals["guardrail"]["version"] == "2"
    key = totals["answers"].removeprefix(f"s3://{BUCKET}/")
    lines = s3.text(key).splitlines()
    assert [json.loads(line)["id"] for line in lines] == ["m01", "m02", "m03"]
    assert s3.content_types[(BUCKET, key)] == "application/x-ndjson"
    out = capsys.readouterr().out
    assert "3 message(s) sent under guardrail gr1abc version 2, 1 blocked" in out
    for message in SAMPLE:
        assert message["text"] not in out
    for answer in ANSWERS.values():
        assert answer not in out
    assert "example.org" not in out


def test_a_refused_request_fails_with_the_id_and_never_the_text():
    runtime = client("bedrock-runtime")
    stub = Stubber(runtime)
    stub.add_client_error(
        "converse",
        service_error_code="AccessDeniedException",
        service_message="not authorized to perform: bedrock:InvokeModel",
        http_status_code=403,
    )
    with stub, pytest.raises(RuntimeError, match="Converse refused message m01") as raised:
        triage.triage(runtime, SAMPLE[:1], MODEL, INSTRUCTIONS, GUARDRAIL)
    assert SAMPLE[0]["text"] not in str(raised.value)


def test_a_message_without_text_fails_by_its_position():
    with pytest.raises(ValueError, match="message 1 of the sample has no id or no text"):
        triage.triage(None, [{"id": "m01", "text": " "}], MODEL, INSTRUCTIONS, GUARDRAIL)


def test_a_guardrail_xcom_without_its_version_fails(boto3_clients):
    without = {key: value for key, value in GUARDRAIL.items() if key != "version"}
    with pytest.raises(RuntimeError, match="names no version"):
        triage.triage_messages(json.dumps(without), MODEL, "s3://b/k", "s3://b/w/")


def test_the_trace_key_reduces_to_the_guardrail_id():
    arn_key = f"arn:aws:bedrock:us-west-2:{ACCOUNT}:guardrail/{GID}:2"
    trace = {"inputAssessment": {arn_key: {"topicPolicy": {"topics": []}}}}
    assert list(common.assessments(trace)) == [GID]
