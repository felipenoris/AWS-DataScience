#!/usr/bin/env -S uv run --quiet
# check-tfvars-shape.py - Stage 4, second design review (2026-08-16). One scan over tfvars.
#
#   run:      ./scripts/check-tfvars-shape.py
#   reads:    git ls-files (which tfvars are tracked), the tracked tfvars themselves, and the
#             roster on disk. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one violation
#
# WHY THIS EXISTS. The wholesale `*.tfvars` ignore has ONE deliberate exception: the WireGuard
# peers roster is tracked (`git add -f`), because a map of who may enter the network benefits
# from review and history. The exception's failure mode is exactly one line - the host's
# PRIVATE key landing in the tracked file - and no content scanner can catch it, because a
# WireGuard private key and a public key are INDISTINGUISHABLE by format (44 chars of base64
# ending in '='), and pre-commit's detect-private-key knows only PEM armor. So this gate
# checks STRUCTURE, the thing that can be checked:
#
#   A. Every TRACKED *.tfvars / *.tfvars.json is in the allowlist below and assigns only the
#      top-level keys its row permits. A tracked tfvars nobody allowlisted fails: committing
#      one is a decision, and the table is where the decision is recorded. A tracked
#      host-key.auto.tfvars fails by name - since the third design review (decision 4) that
#      filename should not exist AT ALL, the key lives in Secrets Manager - so tracking one
#      is the pre-review design coming back with its worst failure mode attached.
#   B. The roster file - tracked or not yet - assigns nothing but `peers` at the top level,
#      nothing but `public_key` and `host` inside it, and `host_private_key` nowhere.
#
# WHAT IT DELIBERATELY DOES NOT SEE (Lesson 13 - a check is honest about its blind side):
#
#   - Untracked, git-ignored tfvars: the generated terraform.auto.tfvars. That is the ignore
#     rule's job; this gate exists for the exception to it.
#   - Attributes inside ONE-LINE entries (`"x" = { public_key = "..", host = 2 }`) are not
#     individually inspected - assignments are read at line starts. The top-level rule still
#     holds, and a private key smuggled as a one-line attribute still needs a name this file
#     may not assign to be consumed by Terraform at all.
#   - The brace count is textual: a `{` inside a quoted string would skew the depth. Nothing
#     a tfvars in this repository holds writes braces into strings.

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROSTER = Path("terraform-live/sandbox/vpn/peers.auto.tfvars")

# path -> the top-level keys that tracked tfvars may assign. Growing this table is the
# deliberate act that tracking a new tfvars requires: the .gitignore asks for "an explicit
# `git add -f` and a reason", and the reason lands here, greppable.
TRACKED_SHAPES: dict[str, set[str]] = {
    str(ROSTER): {"peers"},
}

# The attributes an entry of the roster may carry.
ROSTER_NESTED = {"public_key", "host"}

ASSIGN_RE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=")


def assignments(path: Path) -> list[tuple[int, int, str]]:
    """(line, brace depth before the line, identifier) for every bare assignment.

    Full-line comments are skipped, like check-tf-conventions.py: prose may name anything.
    Quoted keys (`"felipe-laptop" = {`) are entry NAMES, not attributes, and do not match.
    """
    out: list[tuple[int, int, str]] = []
    depth = 0
    for n, raw in enumerate(path.read_text().splitlines(), start=1):
        stripped = raw.strip()
        if not stripped.startswith("#"):
            m = ASSIGN_RE.match(raw)
            if m:
                out.append((n, depth, m.group(1)))
            depth += raw.count("{") - raw.count("}")
    return out


def main() -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    fail = 0

    def say(text: str = "") -> None:
        print(text)

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    tracked = subprocess.run(
        ["git", "ls-files", "*.tfvars", "*.tfvars.json"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    say(f"== A. tracked tfvars against the allowlist ({len(tracked)} tracked) ==")
    a_before = fail
    for name in tracked:
        path = Path(name)
        if path.name == "host-key.auto.tfvars":
            bad(
                f"{name}: the host key file is TRACKED - and should not exist at all:"
                " the key lives in the [P] secret awsds-<env>-vpn-host-key since the"
                " third design review (Stage 4 decision 4). Untrack and delete the file,"
                " and rotate the key (docs/plan/runbooks/vpn.md, procedure C): a key"
                " that was ever pushed is rotated, never merely deleted"
            )
            continue
        allowed = TRACKED_SHAPES.get(name)
        if allowed is None:
            bad(
                f"{name}: tracked but not allowlisted in this script - tracking a tfvars"
                " is a decision, and TRACKED_SHAPES is where it is recorded"
            )
            continue
        for n, depth, key in assignments(path):
            if depth == 0 and key not in allowed:
                bad(
                    f"{name}:{n}: assigns `{key}` - this file may assign only:"
                    f" {', '.join(sorted(allowed))}"
                )
    if not tracked:
        say("  none tracked - nothing to judge (the roster arrives with Stage 4 step 4.1)")
    elif fail == a_before:
        say("  ok")

    say()
    say("== B. the roster's shape, tracked or not ==")
    if ROSTER.exists():
        b_before = fail
        for n, depth, key in assignments(ROSTER):
            if key == "host_private_key":
                bad(
                    f"{ROSTER}:{n}: the SERVER'S PRIVATE KEY does not belong here - it"
                    " belongs in the [P] secret awsds-<env>-vpn-host-key, never in any"
                    " tfvars (Stage 4 step 4.3; decision 4, third review). If this file"
                    " ever reached a remote with it, rotate the key"
                    " (docs/plan/runbooks/vpn.md, procedure C)"
                )
            elif depth == 0 and key != "peers":
                bad(
                    f"{ROSTER}:{n}: assigns `{key}` at top level - the roster defines"
                    " `peers` and nothing else"
                )
            elif depth > 0 and key not in ROSTER_NESTED:
                bad(
                    f"{ROSTER}:{n}: entry attribute `{key}` - entries carry only:"
                    f" {', '.join(sorted(ROSTER_NESTED))}"
                )
        if fail == b_before:
            say("  ok")
    else:
        say("  not on disk - nothing to judge (this is not a pass)")

    say()
    say("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main())
