#!/usr/bin/env -S uv run --quiet
# check-tf-conventions.py - Stage 2 step 9.1. Three scans over the Terraform trees.
#
#   run:      ./scripts/check-tf-conventions.py            # terraform-live/ + terraform-modules/
#             ./scripts/check-tf-conventions.py <path>...  # anything else, for testing the check
#   reads:    *.tf only. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one violation
#
# The three things it refuses, each a rule nothing else enforces:
#
#   A. A region or AZ literal (docs/plan/architecture.md, region portability): var.region
#      everywhere, AMIs from SSM public parameters. backend.hcl is the one place a literal is allowed
#      (step 2.5) and is not a .tf file.
#   B. An AZ selected by index. AZ names are per-account aliases over the physical zones, so
#      `names[0]` is a different building in two accounts, and a subnet peered across accounts
#      silently pays cross-AZ traffic. Subnets anchor on zone_id, from .tfvars (1b step 6).
#   C. aws_s3_account_public_access_block, anywhere. The account-level setting is hand-managed (1c
#      step 7.4), and the SCP that denies the API carves out `InfrastructureAccess`, the principal
#      every slice applies as, so an apply that touched it would succeed. This script is the rule's
#      only enforcement (step 5.2, terraform-live/README.md).
#
# Blind spots, so nobody reads more into a green run (Lesson 13):
#
#   - Full-line comments are skipped: a comment creates nothing, and forbidding the region's name in
#     an explanation would buy vagueness and no safety. An inline trailing comment on a code line is
#     still read, so prose about the region beside code goes on its own line.
#   - B is a one-line pattern: an index split onto its own line, or hidden behind a local, walks
#     past it.
#   - .terraform/ is pruned: vendored provider and module code is not ours.
#
# Line numbers restart per file, and a pattern that does not compile raises before anything is
# scanned instead of reporting a clean tree (Lesson 13).

from __future__ import annotations

import os
import sys
from pathlib import Path

from tfhygiene.scan import collect_files, scan_code_lines

# The AWS region grammar, plus an optional trailing AZ letter so `us-west-2b` is caught by
# the same pattern that catches `us-west-2`. Anchored on \b at both ends so a bucket name
# like awsds-prod-registry-2 cannot match.
REGION_RE = (
    r"\b(af|ap|ca|cn|eu|il|me|mx|sa|us)-(gov-)?"
    r"(central|north|south|east|west|northeast|northwest|southeast|southwest)"
    r"-[1-9][0-9]?[a-z]?\b"
)

AZ_RE = (
    r"aws_availability_zones\b.*(\[|\belement\s*\(|\bslice\s*\()"
    r"|\belement\s*\(\s*data\.aws_availability_zones"
)

BPA_RE = r"aws_s3_account_public_access_block"


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    targets = argv or ["terraform-live", "terraform-modules"]
    files = collect_files(targets, suffixes=(".tf",))

    fail = 0

    def say(text: str = "") -> None:
        print(text)

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    def report(pattern: str, remedy: str, allow_marker: str | None = None) -> None:
        hits, allowed = [], []
        for path, n, line in scan_code_lines(files, pattern):
            if allow_marker and allow_marker in line:
                allowed.append(f"  allow {path}:{n}: {line.strip()}")
            else:
                hits.append(f"  {path}:{n}: {line}")
        # Allowed lines are PRINTED, never silently skipped - the same discipline as
        # check-iam-wildcards.py: an exception that disappears from the output is an
        # exception nobody re-reads.
        if allowed:
            print("\n".join(allowed))
        if hits:
            print("\n".join(hits))
            bad(remedy)
        elif not allowed:
            say("  none")

    say(f"== scanning {len(files)} .tf file(s) under: {' '.join(targets)} ==")
    if not files:
        # Not a pass and not a failure: there is nothing to judge yet. Say which it is - a
        # checker that prints OK over an empty set is how a broken path becomes a green run.
        say("  no .tf files found - nothing to check (this is not a pass)")
        say("OK (vacuous)")
        return 0

    say()
    say("== A. region and AZ literals ==")
    # The one sanctioned inline exception, a marker with a reason: a code line may carry
    # `# region:aws-pinned <why>` when the literal is AWS's own single-Region pin (a page saying
    # "available only in us-east-1"), which var.region cannot express and D1's portability rule was
    # never about. The line is still printed, as `allow`, so the exception stays visible.
    report(
        REGION_RE,
        "use var.region; the one allowed literal is backend.hcl (step 2.5)",
        allow_marker="region:aws-pinned",
    )

    say()
    say("== B. availability zone selected by index ==")
    report(AZ_RE, "anchor subnets on a zone_id from .tfvars, never on list position (1b step 6)")

    say()
    say("== C. aws_s3_account_public_access_block declared in a slice ==")
    report(
        BPA_RE,
        "the account-level setting is hand-managed (1c step 7.4); the SCP would NOT stop this apply",
    )

    say()
    say("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
