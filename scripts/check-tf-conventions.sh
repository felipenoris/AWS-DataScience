#!/usr/bin/env bash
#
# check-tf-conventions.sh - Stage 2 step 9.1. Three greps over the Terraform trees.
#
#   run:      ./scripts/check-tf-conventions.sh            # terraform-live/ + terraform-modules/
#             ./scripts/check-tf-conventions.sh <path>...  # anything else, for testing the check
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
#      by decision (1c step 7.4), and - the part that makes this grep load-bearing rather than
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

set -uo pipefail
cd "$(dirname "$0")/.." || exit 1

TARGETS=("$@")
[ ${#TARGETS[@]} -eq 0 ] && TARGETS=(terraform-live terraform-modules)

fail=0
say()  { printf '%s\n' "$*"; }
bad()  { fail=1; printf '  FAIL  %s\n' "$*"; }

# Collect the .tf files once. -prune on .terraform/ rather than a grep -v, so a vendored
# module whose path merely CONTAINS the string is not excluded by accident.
FILES=()
while IFS= read -r f; do FILES+=("$f"); done < <(
  for t in "${TARGETS[@]}"; do
    [ -e "$t" ] || continue
    find "$t" -type d -name '.terraform' -prune -o -type f -name '*.tf' -print
  done | sort
)

say "== scanning ${#FILES[@]} .tf file(s) under: ${TARGETS[*]} =="
if [ ${#FILES[@]} -eq 0 ]; then
  # Not a pass and not a failure: there is nothing to judge yet. Say which it is - a checker
  # that prints OK over an empty set is how a broken path becomes a green run.
  say "  no .tf files found - nothing to check (this is not a pass)"
  say "OK (vacuous)"
  exit 0
fi

# One perl invocation per rule, over the same list. $ARGV:$. gives file:line, and the
# comment test is the only place the comment policy above is implemented.
#
# TWO THINGS IN THIS FUNCTION ARE SCARS, both from the same afternoon:
#
#   - `close ARGV if eof` is not decoration. Without it $. counts CUMULATIVELY across the file
#     list, so the first violation in the sixth file is reported at line 162 of a three-line
#     file. A line number that is confidently wrong sends the reader to a line somewhere else.
#     It is written as a trailing statement rather than a `continue` block because -n wraps the
#     program in the loop body, where a continue block will not parse - and because an earlier
#     `next` would jump straight over it.
#   - THE EXIT STATUS IS CHECKED BY THE CALLER. A perl that fails to compile prints its error
#     on stderr, produces no matches, and is indistinguishable from a clean tree - which is a
#     checker that returns the same answer on success and on failure (Lesson 13). Measured
#     here, not imagined: the `continue` form above compiled to nothing and reported `none`
#     over a file holding all three violations.
scan() {
  perl -ne 'print "  $ARGV:$.: $_" if !m{^\s*(#|//)} && /'"$1"'/; close ARGV if eof;' "${FILES[@]}"
}

# Wraps scan so that a scanner which did not run is a FAILURE and not a clean section.
report() {   # $1 = regex, $2 = the remedy printed when it matches
  local hits rc
  hits=$(scan "$1"); rc=$?
  if [ "$rc" -ne 0 ]; then
    bad "the scanner itself failed (perl exit $rc) - this section checked NOTHING"
    return
  fi
  if [ -n "$hits" ]; then printf '%s\n' "$hits"; bad "$2"; else say "  none"; fi
}

say
say "== A. region and AZ literals =="
# The AWS region grammar, plus an optional trailing AZ letter so `us-west-2b` is caught by
# the same pattern that catches `us-west-2`. Anchored on \b at both ends so a bucket name
# like awsds-prod-registry-2 cannot match.
REGION_RE='\b(af|ap|ca|cn|eu|il|me|mx|sa|us)-(gov-)?(central|north|south|east|west|northeast|northwest|southeast|southwest)-[1-9][0-9]?[a-z]?\b'
report "$REGION_RE" "use var.region; the one allowed literal is backend.hcl (step 2.5)"

say
say "== B. availability zone selected by index =="
AZ_RE='aws_availability_zones\b.*(\[|\belement\s*\(|\bslice\s*\()|\belement\s*\(\s*data\.aws_availability_zones'
report "$AZ_RE" "anchor subnets on a zone_id from .tfvars, never on list position (1b step 6)"

say
say "== C. aws_s3_account_public_access_block declared in a slice =="
report 'aws_s3_account_public_access_block' "the account-level setting is hand-managed (1c step 7.4); the SCP would NOT stop this apply"

say
[ "$fail" -eq 0 ] && say "OK" || say "FAILED"
exit "$fail"
