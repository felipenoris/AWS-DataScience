#!/usr/bin/env -S uv run --quiet
# check-bedrock-descriptions.py - every Bedrock description is one the service's create accepts.
#
#   run:      ./scripts/check-bedrock-descriptions.py            # terraform-live/ + terraform-modules/
#             ./scripts/check-bedrock-descriptions.py <path>...  # anything else, for testing the check
#   reads:    *.tf only. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one description Bedrock refuses | 2 a file the reader cannot parse
#
# Bedrock's service model constrains each description these resources send (AWS CLI 2.37.12's
# model, read 2026-11-23): CreateInferenceProfile takes 1 to 200 characters matching
# ([0-9a-zA-Z:.][ _-]?)+, letters, digits, ':' and '.', each followed by at most one space, '_' or
# '-'; CreateGuardrail and CreateGuardrailVersion take 1 to 200 characters. The AWS provider plans a
# description the pattern refuses, and Bedrock refuses it at apply, after the resources ahead of it
# exist: staging/studio/'s profile on an apostrophe and parentheses (2026-11-23, SUP-477).
#
# Read: the `description` of every resource whose type is in RULES. A description is judged when
# its value is one string:
#
#   ok         a literal the rule accepts
#   FAIL       a literal the rule refuses, or a ${...} template whose literal text alone is over the
#              length or holds a character outside the pattern's set or two separators in a row
#   partial    a ${...} template whose literal text passes; what its sequences produce is not read
#   unchecked  any other value, printed: a reference, a function call, a %{...} directive
#   absent     no description, which the provider does not send
#
# Blind spots, so nobody reads more into a green run (Lesson 13):
#
#   - A value that arrives through a variable, a local or a module input is never resolved.
#   - A template's length is judged on its literal text alone, and a separator beside one of its
#     sequences is not judged.
#   - .terraform/ is pruned, and .tf.json files are not read.

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tfhygiene import hcl
from tfhygiene.scan import collect_files

# CreateInferenceProfile's pattern, built from its two character sets so the verdict and the
# characters a refusal names cannot disagree.
WORD = "0-9a-zA-Z:."
SEPARATORS = " _-"
PROFILE_PATTERN = f"([{WORD}][{SEPARATORS}]?)+"
assert PROFILE_PATTERN == "([0-9a-zA-Z:.][ _-]?)+", PROFILE_PATTERN
CHARACTER_RE = re.compile(f"[{WORD}{SEPARATORS}]")
SEPARATOR_RUN_RE = re.compile(f"[{SEPARATORS}]{{2}}")
MIN_LENGTH = 1


@dataclass(frozen=True)
class Rule:
    operation: str
    max_length: int
    pattern: str | None  # matched whole; None where the model gives the description none


RULES = {
    "aws_bedrock_inference_profile": Rule("CreateInferenceProfile", 200, PROFILE_PATTERN),
    "aws_bedrock_guardrail": Rule("CreateGuardrail", 200, None),
    "aws_bedrock_guardrail_version": Rule("CreateGuardrailVersion", 200, None),
}

OK, PARTIAL, UNCHECKED, ABSENT, FAIL = "ok", "partial", "unchecked", "absent", "FAIL"


def visible(text: str) -> str:
    """``text`` with each character that prints as nothing written as its escape: \\n, \\xa0."""
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in text)


def outside_the_set(text: str) -> list[str]:
    """Why the pattern's character set refuses ``text``; empty when every character is in it."""
    outside = sorted({c for c in text if not CHARACTER_RE.fullmatch(c)})
    if not outside:
        return []
    # The code point beside a printable character outside ASCII: an en dash and a hyphen look alike.
    shown = [
        f"{c} (U+{ord(c):04X})" if c.isprintable() and not c.isascii() else visible(c)
        for c in outside
    ]
    return ["outside the set: " + " ".join(shown)]


def refused(text: str, rule: Rule) -> list[str]:
    """Why Bedrock refuses ``text`` as a literal description; empty when it accepts it."""
    why = []
    if len(text) < MIN_LENGTH:
        why.append("empty")
    if len(text) > rule.max_length:
        why.append(f"{len(text)} characters, over {rule.max_length}")
    if rule.pattern and text and not re.fullmatch(rule.pattern, text):
        reasons = outside_the_set(text)
        if SEPARATOR_RUN_RE.search(text):
            reasons.append("two separators in a row")
        if text[0] in SEPARATORS:
            reasons.append("a separator first")
        # The regular expression decides; the reasons only name what it refused.
        why += reasons or [f"does not match {rule.pattern}"]
    return why


def judge(arg: hcl.Argument, rule: Rule) -> tuple[str, str, str]:
    """(verdict, detail, the text a FAIL is about) for a description argument."""
    parts = arg.string_parts()
    if parts is None:
        return UNCHECKED, "not a string: " + " ".join(arg.source.split()), ""
    if any(kind == hcl.DIRECTIVE for kind, _ in parts):
        return UNCHECKED, "a %{...} directive decides its literal text: " + visible(arg.source), ""
    sequences = [text for kind, text in parts if kind == hcl.INTERPOLATION]
    text = hcl.literal_text(parts)
    if not sequences:
        why = refused(text, rule)
        if why:
            return FAIL, "; ".join(why), visible(text)
        return OK, f"{len(text)} characters", ""
    # A sequence adds characters and removes none, so the literal text's length is a lower bound.
    why = []
    if len(text) > rule.max_length:
        why.append(f"{len(text)} characters, over {rule.max_length}")
    if rule.pattern:
        why += outside_the_set(text)
        if any(SEPARATOR_RUN_RE.search(t) for kind, t in parts if kind == hcl.LITERAL):
            why.append("two separators in a row")
    if why:
        return FAIL, "its literal text: " + "; ".join(why), visible(arg.source)
    detail = f"literal text passes, {len(text)} characters; not read: " + ", ".join(sequences)
    return PARTIAL, detail, ""


def described(body: list) -> list[tuple[str, int, Rule, hcl.Argument | None]]:
    """(address, line, rule, description) for each resource whose type is in RULES, in source
    order; the description is None where the resource sets none."""
    found = []
    for block in body:
        if not (isinstance(block, hcl.Block) and block.type == "resource"):
            continue
        if len(block.labels) != 2 or block.labels[0] not in RULES:
            continue
        rule = RULES[block.labels[0]]
        found.append((".".join(block.labels), block.line, rule, block.argument("description")))
    return found


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    targets = argv or ["terraform-live", "terraform-modules"]
    files = collect_files(targets, suffixes=(".tf",))

    print(f"== Bedrock descriptions in {len(files)} .tf file(s) under: {' '.join(targets)} ==")
    for type_, rule in RULES.items():
        shape = f" matching {rule.pattern}" if rule.pattern else ""
        print(
            f"  {type_}: {rule.operation} takes {MIN_LENGTH} to {rule.max_length} characters{shape}"
        )
    counts = {OK: 0, PARTIAL: 0, UNCHECKED: 0, ABSENT: 0, FAIL: 0}
    unreadable = []
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        # A file that names none of the types cannot declare one.
        if not any(t in text for t in RULES):
            continue
        try:
            body = hcl.parse(text)
        except hcl.HclError as e:
            unreadable.append(f"{path}: {e}")
            continue
        for address, line, rule, arg in described(body):
            if arg is None:
                counts[ABSENT] += 1
                print(f"  {ABSENT:<9}  {path}:{line}  {address}  no description sent")
                continue
            verdict, detail, about = judge(arg, rule)
            counts[verdict] += 1
            print(f"  {verdict:<9}  {path}:{arg.line}  {address}  {detail}")
            if about:
                print(f"             {about}")
    for problem in unreadable:
        print(f"  UNREAD     {problem}")

    print()
    resources = sum(counts.values())
    if not resources and not unreadable:
        # Not a pass and not a failure: nothing here declares a Bedrock resource. Say which it is.
        print(
            "  no Bedrock resource with a description found - nothing to check (this is not a pass)"
        )
        print("OK (vacuous)")
        return 0
    print(
        f"  {resources} resource(s): "
        + ", ".join(f"{n} {verdict}" for verdict, n in counts.items())
    )
    if counts[FAIL]:
        print(
            "  reword: a profile's description takes letters, digits, ':' and '.' with one space,"
            " '_' or '-' between them, no apostrophe, comma or parenthesis; every one 1 to 200"
            " characters"
        )
        print("FAILED")
        return 1
    if unreadable:
        print(
            f"UNREAD - {len(unreadable)} file(s) the reader cannot parse, and nothing in them judged"
        )
        return 2
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
