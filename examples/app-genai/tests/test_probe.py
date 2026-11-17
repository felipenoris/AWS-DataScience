"""The `unguarded` task over a Stubber on the bedrock-runtime client: a request with no guardrail,
its two outcomes, and the report written before a mismatch fails the task."""

from __future__ import annotations

import json

import pytest
from botocore.stub import Stubber

from app_genai_tasks import probe
from conftest import ACCOUNT, BUCKET, SHARED, FakeS3, client

MODEL = f"arn:aws:bedrock:us-west-2:{ACCOUNT}:application-inference-profile/prof1"
REPORT = f"{SHARED}app-genai/outbox/probe-report.json"
KEY = "domain/project/shared/app-genai/outbox/probe-report.json"
REFUSAL = (
    f"User: arn:aws:sts::{ACCOUNT}:assumed-role/project-role/session is not authorized to perform: "
    "bedrock:InvokeModel with an explicit deny in a permissions boundary"
)


def answered() -> dict:
    return {
        "output": {"message": {"role": "assistant", "content": [{"text": "ready"}]}},
        "stopReason": "end_turn",
        "usage": {"inputTokens": 12, "outputTokens": 2, "totalTokens": 14},
        "metrics": {"latencyMs": 210},
    }


def run(boto3_clients, stub_setup, expect: str):
    runtime = client("bedrock-runtime")
    stub = Stubber(runtime)
    stub_setup(stub)
    s3 = FakeS3()
    boto3_clients.update({"bedrock-runtime": runtime, "s3": s3})
    with stub:
        try:
            return probe.probe_unguarded(model=MODEL, expect=expect, report=REPORT), s3
        finally:
            stub.assert_no_pending_responses()


def test_the_request_names_no_guardrail():
    request = probe.probe_request(MODEL)
    assert "guardrailConfig" not in request
    assert request["messages"] == [{"role": "user", "content": [{"text": probe.PROMPT}]}]


def test_an_answer_reads_answered(boto3_clients):
    def setup(stub):
        stub.add_response("converse", answered(), probe.probe_request(MODEL))

    text, s3 = run(boto3_clients, setup, "answered")
    report = json.loads(text)
    assert report["outcome"] == "answered"
    assert report["passed"] is True
    assert report["answer_chars"] == len("ready")
    assert json.loads(s3.text(KEY)) == report
    assert s3.content_types[(BUCKET, KEY)] == "application/json"


def test_a_refusal_reads_refused_with_its_wording(boto3_clients):
    def setup(stub):
        stub.add_client_error(
            "converse",
            service_error_code="AccessDeniedException",
            service_message=REFUSAL,
            http_status_code=403,
            expected_params=probe.probe_request(MODEL),
        )

    text, _ = run(boto3_clients, setup, "refused")
    report = json.loads(text)
    assert (report["outcome"], report["error"], report["message"]) == (
        "refused",
        "AccessDeniedException",
        REFUSAL,
    )
    assert report["passed"] is True


def test_an_outcome_other_than_expected_fails_after_the_report(boto3_clients):
    runtime = client("bedrock-runtime")
    stub = Stubber(runtime)
    stub.add_response("converse", answered(), probe.probe_request(MODEL))
    s3 = FakeS3()
    boto3_clients.update({"bedrock-runtime": runtime, "s3": s3})
    with stub, pytest.raises(RuntimeError, match="was answered, not refused"):
        probe.probe_unguarded(model=MODEL, expect="refused", report=REPORT)
    assert json.loads(s3.text(KEY))["passed"] is False


def test_another_error_fails_as_it_is(boto3_clients):
    runtime = client("bedrock-runtime")
    stub = Stubber(runtime)
    stub.add_client_error("converse", service_error_code="ValidationException")
    boto3_clients.update({"bedrock-runtime": runtime, "s3": FakeS3()})
    with stub, pytest.raises(Exception, match="ValidationException"):
        probe.probe_unguarded(model=MODEL, expect="refused", report=REPORT)


@pytest.mark.parametrize("expect", ["", "Refused", "blocked"])
def test_an_expectation_outside_the_two_outcomes_is_refused(expect):
    with pytest.raises(ValueError, match="EXPECT_UNGUARDED"):
        probe.probe_unguarded(model=MODEL, expect=expect, report=REPORT)
