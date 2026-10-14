#!/usr/bin/env -S uv run --quiet
# check-sg-descriptions.py - every security group and rule description is one EC2 accepts.
#
#   run:      ./scripts/check-sg-descriptions.py            # terraform-live/ + terraform-modules/
#             ./scripts/check-sg-descriptions.py <path>...  # anything else, for testing the check
#   reads:    *.tf only. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one description EC2 refuses | 2 a file the reader cannot parse
#
# EC2 takes a group description and a rule description from one set: letters, digits, the space
# and ._-:/()#,@[]+=&;{}!$*, under 256 characters. `terraform validate` holds an inline ingress or
# egress block and aws_security_group_rule to that set, and holds the group's own description and
# both aws_vpc_security_group_*_rule resources to nothing (hashicorp/aws 6.68.0, measured
# 2026-10-14). EC2 refuses those three at apply, after the resources ahead of them in the plan
# exist: sandbox/warehouse/'s group on an apostrophe (2026-09-20), its 5439 rule on `->`
# (2026-09-21) and sandbox/app/app-etl/'s group on an apostrophe (2026-10-14) each stopped an
# apply part-way.
#
# Read: the `description` of every resource whose type is in DESCRIBED, and of every ingress and
# egress block, inline or dynamic, of a resource whose type is in WITH_RULE_BLOCKS. A description
# is judged when its value is one string:
#
#   ok         a literal EC2 accepts
#   FAIL       a literal, or the literal text of a ${...} template, with a character outside the
#              set or more than 255 characters
#   partial    a ${...} template whose literal text passes; what its sequences produce is not read
#   unchecked  any other value, printed: a reference, a function call, a %{...} directive
#
# Blind spots, so nobody reads more into a green run (Lesson 13):
#
#   - A value that arrives through a variable, a local or a module input is never resolved: the
#     module's side reads unchecked or partial, and the caller's literal is not read.
#   - An `ingress = [...]` argument, the attribute form of the blocks, is printed as unchecked.
#   - .terraform/ is pruned, and .tf.json files are not read.

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

from tfhygiene import hcl
from tfhygiene.scan import collect_files

# The set EC2's InvalidParameterValue message quotes, for a group and a rule description alike.
# One class builds both patterns, so the verdict and the characters it names cannot disagree.
ALLOWED = r"[a-zA-Z0-9. _\-:/()#,@\[\]+=&;{}!$*]"
MAX_LENGTH = 255
CHARACTER_RE = re.compile(ALLOWED)
# Matched with fullmatch: `$` also matches before a trailing newline, and a heredoc ends in one.
DESCRIPTION_RE = re.compile(f"{ALLOWED}{{0,{MAX_LENGTH}}}")
# The class without its brackets and escapes: the set as EC2's message spells it.
SET = ALLOWED[1:-1].replace("\\", "")

# The resources whose own `description` is a group's or a rule's.
DESCRIBED = frozenset(
    {
        "aws_security_group",
        "aws_security_group_rule",
        "aws_vpc_security_group_egress_rule",
        "aws_vpc_security_group_ingress_rule",
    }
)
# The resources whose ingress and egress blocks are rules, each with a description.
WITH_RULE_BLOCKS = frozenset({"aws_default_security_group", "aws_security_group"})
TYPES = DESCRIBED | WITH_RULE_BLOCKS
RULE_BLOCKS = ("ingress", "egress")

OK, PARTIAL, UNCHECKED, FAIL = "ok", "partial", "unchecked", "FAIL"


def visible(text: str) -> str:
    """``text`` with each character that prints as nothing written as its escape: \\n, \\xa0."""
    return "".join(c if c.isprintable() else repr(c)[1:-1] for c in text)


def refused(text: str) -> list[str]:
    """Why EC2 refuses ``text``; empty when it accepts it."""
    if DESCRIPTION_RE.fullmatch(text):
        return []
    why = []
    outside = sorted({c for c in text if not CHARACTER_RE.fullmatch(c)})
    if outside:
        # The code point beside a printable character outside ASCII: an em dash and a hyphen
        # look alike.
        shown = [
            f"{c} (U+{ord(c):04X})" if c.isprintable() and not c.isascii() else visible(c)
            for c in outside
        ]
        why.append("outside the set: " + " ".join(shown))
    if len(text) > MAX_LENGTH:
        why.append(f"{len(text)} characters, over {MAX_LENGTH}")
    return why


def literal_text(parts: list) -> str:
    """The literal text of a template, after the ~ strip markers beside each ${...}."""
    texts, strip_next = [], False
    for kind, text in parts:
        if kind == hcl.LITERAL:
            texts.append(text.lstrip() if strip_next else text)
            strip_next = False
            continue
        if text.startswith("${~") and texts:
            texts[-1] = texts[-1].rstrip()
        strip_next = text.endswith("~}")
    return "".join(texts)


def judge(arg: hcl.Argument) -> tuple[str, str, str]:
    """(verdict, detail, the text a FAIL is about) for a description or a rules argument."""
    if arg.name in RULE_BLOCKS:
        return UNCHECKED, "rules given as an argument: " + " ".join(arg.source.split()), ""
    parts = arg.string_parts()
    if parts is None:
        return UNCHECKED, "not a string: " + " ".join(arg.source.split()), ""
    if any(kind == hcl.DIRECTIVE for kind, _ in parts):
        return UNCHECKED, "a %{...} directive decides its literal text: " + visible(arg.source), ""
    sequences = [text for kind, text in parts if kind == hcl.INTERPOLATION]
    text = literal_text(parts)
    why = refused(text)
    if why and sequences:
        return FAIL, "its literal text: " + "; ".join(why), visible(arg.source)
    if why:
        return FAIL, "; ".join(why), visible(text)
    if sequences:
        detail = f"literal text passes, {len(text)} characters; not read: " + ", ".join(sequences)
        return PARTIAL, detail, ""
    return OK, f"{len(text)} characters", ""


def security_groups(body: list) -> list[list[tuple[str, hcl.Argument]]]:
    """One list per resource whose type is in TYPES, in source order: (where, argument) for each
    of its descriptions, and for an ingress or egress argument that declares rules."""
    found = []
    for block in body:
        if not (isinstance(block, hcl.Block) and block.type == "resource"):
            continue
        if len(block.labels) != 2 or block.labels[0] not in TYPES:
            continue
        address = ".".join(block.labels)
        args = []
        if block.labels[0] in DESCRIBED:
            args.append((address, block.argument("description")))
        if block.labels[0] in WITH_RULE_BLOCKS:
            for rule in block.blocks():
                if rule.type in RULE_BLOCKS:
                    args.append((f"{address} {rule.type}", rule.argument("description")))
                elif rule.type == "dynamic" and rule.labels and rule.labels[0] in RULE_BLOCKS:
                    for content in rule.blocks("content"):
                        where = f"{address} dynamic {rule.labels[0]}"
                        args.append((where, content.argument("description")))
            for item in block.body:
                # `ingress = []` is the attribute form declaring no rule at all.
                if isinstance(item, hcl.Argument) and item.name in RULE_BLOCKS:
                    if [t.text for t in item.value] != ["[", "]"]:
                        args.append((f"{address} {item.name}", item))
        found.append([(where, arg) for where, arg in args if arg is not None])
    return found


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    targets = argv or ["terraform-live", "terraform-modules"]
    files = collect_files(targets, suffixes=(".tf",))

    print(
        f"== security group descriptions in {len(files)} .tf file(s) under: {' '.join(targets)} =="
    )
    print(f"  EC2 accepts {SET} and at most {MAX_LENGTH} characters")
    counts = {OK: 0, PARTIAL: 0, UNCHECKED: 0, FAIL: 0}
    resources, unreadable = 0, []
    for path in files:
        text = path.read_text(encoding="utf-8-sig")
        # A file that names none of the types cannot declare one.
        if not any(t in text for t in TYPES):
            continue
        try:
            body = hcl.parse(text)
        except hcl.HclError as e:
            unreadable.append(f"{path}: {e}")
            continue
        for args in security_groups(body):
            resources += 1
            for where, arg in args:
                verdict, detail, about = judge(arg)
                counts[verdict] += 1
                print(f"  {verdict:<9}  {path}:{arg.line}  {where}  {detail}")
                if about:
                    print(f"             {about}")
    for problem in unreadable:
        print(f"  UNREAD     {problem}")

    print()
    if not resources and not unreadable:
        # Not a pass and not a failure: nothing here declares a security group. Say which it is.
        print("  no security group resource found - nothing to check (this is not a pass)")
        print("OK (vacuous)")
        return 0
    print(
        f"  {sum(counts.values())} description(s) in {resources} resource(s): "
        + ", ".join(f"{n} {verdict}" for verdict, n in counts.items())
    )
    if counts[FAIL]:
        print("  reword inside the set: `to` for an arrow, no apostrophe and no quote")
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
