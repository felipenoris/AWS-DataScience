#!/usr/bin/env -S uv run --quiet
# No tracked file carries an AWS account id or an e-mail address.
# Run from anywhere:  ./scripts/check-identifiers.py
#
#   reads:    every file `git ls-files` reports. No AWS session, no side effect.
#   exit:     0 clean | 1 at least one identifier in a tracked file
#
# WHY THIS EXISTS (2026-08-17). `CLAUDE.md` says a stage log carries no account ids and
# `aws/INDEX.md` rule 1 says never to copy an id or an address out of a snapshot into a tracked
# file. Both rules were held by attention alone, and on the day this was written attention had
# already missed three log files: eight ids pasted inside `sts get-caller-identity` output, a
# dozen more inside policy ARNs, and one personal address inside an `UnauthorizedOperation`
# error. Every one of them had a correctly-elided neighbour a few lines away - Lesson 14, a
# condition that must appear in N places by hand will be missing from one of them.
#
# WHAT TO DO WITH A HIT is a redaction, never a deletion: an account id becomes the account's
# NAME in angle brackets (`<Audit Account>`, the AWS `Account.Name` of docs/ORGANIZATION.md),
# an e-mail inside an ARN becomes that user's role (`<control tower admin user>`), and the
# entry says once that the substitution was made. The pasted evidence stays otherwise verbatim
# - suffixes, policy ids, error wording - because a log that has been tidied is not evidence.
#
# THE SCOPE IS THE WHOLE TRACKED TREE and not `docs/` alone. `docs/` is where the misses were,
# but the rule is repository-wide and the expensive leak is a real id reaching a `.tf` or a
# `.tfvars`, where it would be copied forward by every consumer. Narrowing it later is one
# argument to `tracked_files`.

from __future__ import annotations

import os
import sys
from pathlib import Path

from repohygiene.identifiers import ALLOWED, ALLOWED_EMAIL_DOMAINS, findings, tracked_files


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    paths = tracked_files(root)
    hits = list(findings(paths, root))

    print("== account ids and e-mail addresses in tracked files ==")
    print(f"  {len(paths)} tracked files scanned")
    print(f"  allowed by name: {', '.join(ALLOWED)}, and @{', @'.join(ALLOWED_EMAIL_DOMAINS)}")

    for path, line_no, kind, hit in hits:
        print(f"  FAIL  {path}:{line_no}: {kind} `{hit}`")

    if hits:
        print(
            "\n  redact, do not delete: an account id becomes <The Account Name>, an e-mail\n"
            "  inside an ARN becomes <that user's role>, and the entry declares it once."
        )
        print("FAILED")
        return 1

    print("  none")
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
