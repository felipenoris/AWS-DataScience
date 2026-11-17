"""The `triage` task of app-genai-triage: each message of the sample sent to the model under the
application's guardrail.

One Converse request per message, as the project role through the `bedrock-runtime` endpoint: the
archive's `prompts/triage.md` as the system prompt, the message as the only content block, a
`guardContent` block, which the guardrail assesses (once a request holds one, the guardrail
evaluates only the `guardContent` blocks, so the instructions are not assessed), `temperature` 0, a
bound on the output tokens, and `guardrailConfig` naming the version the `guardrail` task returned,
with the trace on. The model is MODEL_ID, the application inference profile of the stage.

The task writes `answers.jsonl` under a folder of the run, one line per message: the answer, the
stop reason, the token counts, the latency and what each guardrail did, from the trace without the
values a policy matched and without the model's output, which the trace returns unmasked. It
returns the totals as JSON text, the XCom `check` reads, and prints counts alone: the workflow's log
group never holds a message or an answer.
"""

from __future__ import annotations

import json
import time

from .common import assessments, blocked, bundled, decode, read_jsonl, write_text

PROMPT = "prompts/triage.md"
MAX_TOKENS = 200
TEMPERATURE = 0


def converse_request(model: str, instructions: str, text: str, guardrail: dict) -> dict:
    """The Converse request for one message."""
    return {
        "modelId": model,
        "system": [{"text": instructions}],
        "messages": [{"role": "user", "content": [{"guardContent": {"text": {"text": text}}}]}],
        "inferenceConfig": {"maxTokens": MAX_TOKENS, "temperature": TEMPERATURE},
        "guardrailConfig": {
            "guardrailIdentifier": guardrail["arn"],
            "guardrailVersion": str(guardrail["version"]),
            "trace": "enabled",
        },
    }


def answer_record(message_id: str, response: dict) -> dict:
    """One line of `answers.jsonl`."""
    content = (response.get("output") or {}).get("message", {}).get("content") or []
    usage = response.get("usage") or {}
    guardrails = assessments((response.get("trace") or {}).get("guardrail") or {})
    return {
        "id": message_id,
        "answer": "".join(block.get("text", "") for block in content),
        "stop_reason": response.get("stopReason", ""),
        "input_tokens": int(usage.get("inputTokens", 0)),
        "output_tokens": int(usage.get("outputTokens", 0)),
        "latency_ms": int((response.get("metrics") or {}).get("latencyMs", 0)),
        "guardrails": guardrails,
        "blocked": blocked(guardrails),
    }


def triage(runtime, messages: list[dict], model: str, instructions: str, guardrail: dict) -> list:
    """Every message sent, in the sample's order; a request the service refuses fails the task
    with the message's id and the error, never the message's text."""
    from botocore.exceptions import ClientError

    records = []
    for number, message in enumerate(messages, start=1):
        message_id, text = str(message.get("id") or ""), message.get("text")
        if not message_id or not isinstance(text, str) or not text.strip():
            raise ValueError(f"message {number} of the sample has no id or no text")
        try:
            response = runtime.converse(**converse_request(model, instructions, text, guardrail))
        except ClientError as exc:
            raise RuntimeError(f"Converse refused message {message_id}: {exc}") from exc
        records.append(answer_record(message_id, response))
    return records


def triage_messages(
    guardrail: str, model: str, sample: str, work: str, region: str = "", **context
) -> str:
    """The task: the sample triaged, the answers written under `work`, the totals returned."""
    import boto3
    from botocore.config import Config

    kept = decode(guardrail, "the guardrail task's XCom")
    missing = [key for key in ("id", "arn", "version") if not kept.get(key)]
    if missing:
        raise RuntimeError(f"the guardrail task's XCom names no {', '.join(missing)}")
    if not str(model).strip():
        raise RuntimeError("no model: the stage variable MODEL_ID is empty")
    s3 = boto3.client("s3")
    runtime = boto3.client(
        "bedrock-runtime",
        region_name=region or None,
        config=Config(retries={"mode": "standard", "max_attempts": 6}),
    )
    messages = read_jsonl(s3, sample)
    if not messages:
        raise RuntimeError(f"no message in {sample}")
    instructions = bundled(PROMPT).read_text(encoding="utf-8")
    records = triage(runtime, messages, model, instructions, kept)

    run = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    answers = f"{work.rstrip('/')}/{run}/answers.jsonl"
    text = "".join(json.dumps(record, sort_keys=True) + "\n" for record in records)
    write_text(s3, answers, text, "application/x-ndjson")
    totals = {
        "answers": answers,
        "model": model,
        "guardrail": {key: kept.get(key) for key in ("id", "arn", "name", "version", "sha256")},
        "messages": len(records),
        "blocked": sum(1 for record in records if record["blocked"]),
        "input_tokens": sum(record["input_tokens"] for record in records),
        "output_tokens": sum(record["output_tokens"] for record in records),
    }
    print(
        f"{totals['messages']} message(s) sent under guardrail {kept['id']} version "
        f"{kept['version']}, {totals['blocked']} blocked; {totals['input_tokens']} input and "
        f"{totals['output_tokens']} output token(s); the answers in {answers}"
    )
    return json.dumps(totals, indent=2, sort_keys=True) + "\n"
