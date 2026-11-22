"""samples/messages.jsonl: the script's output, its labels the prompt's, its planted messages, and
no identifier the infrastructure repository refuses."""

from __future__ import annotations

import json
import re
from collections import Counter

import make_sample
from app_genai_tasks import check, common

SAMPLE = make_sample.TARGET
MESSAGES = [json.loads(line) for line in SAMPLE.read_text(encoding="utf-8").splitlines()]
# scripts/check-identifiers.py's patterns and allowances, in the infrastructure repository.
ACCOUNT_ID = re.compile(r"(?<![0-9A-Za-z_-])[0-9]{12}(?![0-9A-Za-z_-])")
EMAIL = re.compile(r"[0-9A-Za-z._%+-]+@[0-9A-Za-z.-]+\.[A-Za-z]{2,}")
EMAIL_DOMAINS = ("example.com", "example.org", "example.net")


def test_the_file_is_the_scripts_output():
    assert SAMPLE.read_text(encoding="utf-8") == make_sample.render()
    assert make_sample.main(["--check"]) == 0


def test_forty_messages_numbered_in_order():
    assert [message["id"] for message in MESSAGES] == [f"m{i:02d}" for i in range(1, 41)]


def test_every_label_is_the_prompts_and_each_is_used():
    allowed = check.labels(common.bundled("prompts/triage.md").read_text(encoding="utf-8"))
    assert set(Counter(message["label"] for message in MESSAGES)) == allowed


def test_one_message_of_each_planted_kind():
    planted = Counter(message.get("planted") for message in MESSAGES if message.get("planted"))
    assert planted == {"pii": 1, "denied_topic": 1, "prompt_attack": 1}


def test_the_planted_values_are_in_their_message():
    (message,) = [m for m in MESSAGES if m.get("planted") == "pii"]
    assert set(message["pii"]) == {"EMAIL", "PHONE"}
    for value in message["pii"].values():
        assert value in message["text"]


def test_no_identifier_the_repository_refuses():
    text = SAMPLE.read_text(encoding="utf-8")
    assert ACCOUNT_ID.findall(text) == []
    for address in EMAIL.findall(text):
        assert address.rsplit("@", 1)[1].lower() in EMAIL_DOMAINS


def test_the_seed_decides_the_sample():
    assert make_sample.render(seed=1) != make_sample.render()
    assert make_sample.render(seed=1) == make_sample.render(seed=1)
