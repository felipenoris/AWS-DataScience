"""The `unguarded` task of app-genai-probe: one Converse request that names no guardrail.

The request carries a fixed prompt, a bound on the output tokens and no `guardrailConfig`. Its
outcome is `answered` when the model answers and `refused` when the service refuses the call with
AccessDeniedException; any other error fails the task as it is. The report, `probe-report.json`,
holds the outcome, the stage variable EXPECT_UNGUARDED, and what came back: the answer's length,
its stop reason and its tokens, or the refusal's code and wording. The task passes when the outcome
equals EXPECT_UNGUARDED, so a run that succeeds in Staging is the reading that the boundary refuses
an invocation without the guardrail; the report is written before a mismatch fails the task.
"""

from __future__ import annotations

import json

from .common import error_code, write_text

PROMPT = "Reply with the single word: ready."
MAX_TOKENS = 10
OUTCOMES = ("answered", "refused")


def probe_request(model: str) -> dict:
    """The request: the fixed prompt, and no guardrail."""
    return {
        "modelId": model,
        "messages": [{"role": "user", "content": [{"text": PROMPT}]}],
        "inferenceConfig": {"maxTokens": MAX_TOKENS, "temperature": 0},
    }


def probe(runtime, model: str) -> dict:
    """What came back for the request."""
    from botocore.exceptions import ClientError

    try:
        response = runtime.converse(**probe_request(model))
    except ClientError as exc:
        if error_code(exc) != "AccessDeniedException":
            raise
        return {
            "outcome": "refused",
            "error": error_code(exc),
            "message": str(exc.response.get("Error", {}).get("Message", "")),
        }
    content = (response.get("output") or {}).get("message", {}).get("content") or []
    usage = response.get("usage") or {}
    return {
        "outcome": "answered",
        "answer_chars": len("".join(block.get("text", "") for block in content)),
        "stop_reason": response.get("stopReason", ""),
        "input_tokens": int(usage.get("inputTokens", 0)),
        "output_tokens": int(usage.get("outputTokens", 0)),
    }


def probe_unguarded(model: str, expect: str, report: str, region: str = "", **context) -> str:
    """The task: the request sent, the report written, the run failed where the outcome is not the
    one the stage expects."""
    import boto3

    expect = str(expect).strip()
    if expect not in OUTCOMES:
        raise ValueError(f"EXPECT_UNGUARDED {expect!r} is neither {' nor '.join(OUTCOMES)}")
    if not str(model).strip():
        raise RuntimeError("no model: the stage variable MODEL_ID is empty")
    runtime = boto3.client("bedrock-runtime", region_name=region or None)
    reading = probe(runtime, model)
    result = {"model": model, "expected": expect, **reading, "passed": reading["outcome"] == expect}
    text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    write_text(boto3.client("s3"), report, text, "application/json")
    print(f"the request without a guardrail: {reading['outcome']}, {expect} expected")
    if not result["passed"]:
        raise RuntimeError(
            f"the request without a guardrail was {reading['outcome']}, not {expect}"
        )
    return text
