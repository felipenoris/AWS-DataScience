#!/usr/bin/env -S uv run --quiet
# check-identifiers.py - no tracked file carries an AWS account id or an e-mail address.
#
#   run:      ./scripts/check-identifiers.py
#   reads:    every file `git ls-files` reports. No AWS session, no side effect.
#   exit:     0 clean | 1 at least one identifier in a tracked file
#
# CLAUDE.md says a stage log carries no account ids, and aws/INDEX.md rule 1 says never to copy an
# id or an address out of a snapshot. Both rules were held by attention alone, and attention had
# missed three log files (Lesson 14). The scope is the whole tracked tree, not docs/ alone: the
# expensive leak is an id reaching a .tf or a .tfvars, copied forward by every consumer.
#
# A hit is redacted, never deleted: an account id becomes the account's name in angle brackets
# (`<Audit Account>`, the AWS `Account.Name` of docs/ORGANIZATION.md), an e-mail inside an ARN becomes
# that user's role (`<control tower admin user>`), and the entry says once that the substitution was
# made. The rest of the pasted evidence stays verbatim: a tidied log is not evidence.

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
