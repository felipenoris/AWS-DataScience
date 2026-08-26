#!/usr/bin/env -S uv run --quiet
# check-tf-conventions.py - Stage 2 step 9.1. Three scans over the Terraform trees.
#
#   run:      ./scripts/check-tf-conventions.py            # terraform-live/ + terraform-modules/
#             ./scripts/check-tf-conventions.py <path>...  # anything else, for testing the check
#   reads:    *.tf only. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one violation
#
# THE THREE THINGS IT REFUSES, and each is a rule that has nothing else enforcing it:
#
#   A. A REGION OR AZ LITERAL (docs/plan/architecture.md, region portability). The region is a
#      variable, not an assumption - var.region everywhere, AMIs from SSM public parameters.
#      backend.hcl is the ONE place a literal is allowed (step 2.5) and it is not a .tf file,
#      so this check never sees it. That reconciliation is the whole reason the backend is
#      partial configuration rather than a block.
#
#   B. AN AZ SELECTED BY INDEX. `data.aws_availability_zones.this.names[0]` is portable-looking
#      and wrong: AZ NAMES are per-account aliases over the physical zones, so the same [0]
#      is a different building in two accounts, and a subnet peered across accounts silently
#      pays cross-AZ traffic. Subnets anchor on zone_id, from .tfvars (settled 1b step 6).
#
#   C. aws_s3_account_public_access_block, ANYWHERE. The account-level setting is hand-managed
#      by decision (1c step 7.4), and - the part that makes this scan load-bearing rather than
#      tidy - the SCP that denies the API carves out `InfrastructureAccess`, which is exactly
#      the principal every slice applies as. So an apply that touched it would SUCCEED. This
#      script is the only enforcement the rule has (step 5.2, and terraform-live/README.md).
#
# WHAT IT DELIBERATELY DOES NOT SEE, said out loud so nobody reads more into a green run
# (Lesson 13 - a check has to be honest about its blind side):
#
#   - FULL-LINE COMMENTS ARE SKIPPED. A comment creates nothing, and these files carry their
#     reasoning in prose: a check that forbade naming us-west-2 in an explanation would buy
#     vagueness and no safety. An inline trailing comment on a CODE line is still read, so the
#     way to write about the region beside code is to give the prose its own line.
#   - B is a ONE-LINE pattern. Splitting the index onto its own line, or hiding it behind a
#     local, walks past it. It catches the shape that gets typed, not every shape that exists.
#   - .terraform/ is pruned: it holds vendored provider and module code that is not ours.
#
# The shell version's two scars are structural here rather than remembered: line numbers
# restart per file because the loop is per file, and a pattern that does not compile raises
# before anything is scanned instead of reporting a clean tree (Lesson 13 - the `continue`
# form of the old perl compiled to nothing and reported `none` over a file holding all three
# violations).

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
    # The ONE sanctioned inline exception, and it is a marker with a reason, not a skip:
    # a code line may carry `# region:aws-pinned <why>` when the literal is AWS's OWN
    # single-Region pin (the page says "available only in us-east-1") - a fact var.region
    # cannot express and D1's portability rule was never about. First users: the console's
    # uxc/freetier endpoints and the measured account.us-east-1 host, on the Sandbox DNS
    # allow-list (2026-08-25). The line is still
    # printed, as `allow`, so the exception stays visible on every run.
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
