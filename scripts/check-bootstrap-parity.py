#!/usr/bin/env -S uv run --quiet
# check-bootstrap-parity.py - Stage 2 step 3.5. The five bootstrap slices are one slice, copied.
#
#   run:      ./scripts/check-bootstrap-parity.py
#   reads:    terraform-live/*/bootstrap/ only. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 at least one divergence
#
# A copy and not a module, by step 2.3: terraform-modules/ is consumed by git tag, a tag cannot exist
# before the module does, and bootstrap is the slice that makes every other slice possible. The
# copy's failure mode is Lesson 14, a setting changed in four slices out of five with nothing
# announcing that the fifth stopped being a copy. Hence this check, and the legitimate differences
# split into files of their own:
#
#   - backend.tf holds the one part that may differ, because a slice that has not migrated yet
#     (step 2.2) must not declare a backend. It is compared with the comment markers removed.
#   - production/bootstrap/pki-key.tf is the one extra file, D36's second key (3.4), allow-listed
#     by name.
#
# Not seen here: the generated files (backend.hcl and terraform.auto.tfvars are per-slice by
# construction and gitignored; gen-backend-hcl.py and gen-tfvars.py keep them honest from one
# table), and whether a slice has applied (./aws/tf-backends.py BK-0 reads AWS).

from __future__ import annotations

import difflib
import os
import re
import sys
from pathlib import Path

LIVE = Path("terraform-live")

# The account folders with a bootstrap slice, in the order docs/plan/conventions.md §6 lists them.
# OPTIONAL holds a slice that is still present while its absence is the expected end state; it is
# empty since Stage 6b step 4.7 destroyed development/bootstrap/. A bootstrap teardown commits its
# end state: a slice with `prevent_destroy` lifted has stopped being a copy and fails this check, and
# a name dropped early fails it the other way.
REQUIRED = ("sandbox", "staging", "data-governance", "production", "identity")
OPTIONAL: tuple[str, ...] = ()

# The slice that is compared against. It is the one that has APPLIED (step 2), so a divergence
# is reported in the direction that matters: what the others would create that this one did not.
REFERENCE = "sandbox"

# Byte-identical in every slice. The lock file is here for the reason step 1 gave it one form:
# it is a function of the version constraint and the platform list alone, so five copies that
# disagree mean one slice is resolving a different provider build.
SHARED = (
    "main.tf",
    "variables.tf",
    "outputs.tf",
    "providers.tf",
    "versions.tf",
    ".terraform.lock.hcl",
)

# Identical only after the comment markers come off - see the header.
UNCOMMENTED = ("backend.tf",)

# The allow-list, by name, one entry per file that is meant to exist in exactly one slice.
ALLOWED_EXTRA = {"production": {"pki-key.tf"}}

# Generated, gitignored, or terraform's own working files. Not ours to compare.
IGNORED = re.compile(r"^(backend\.hcl|.*\.tfvars|terraform\.tfstate.*|\.terraform)$")

COMMENT = re.compile(r"^#[ ]?")


def uncomment(text: str) -> str:
    """Strip one leading '#' and at most one following space from every line."""
    return "\n".join(COMMENT.sub("", line) for line in text.splitlines())


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    fail = 0

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    found = sorted(p.parent.name for p in LIVE.glob("*/bootstrap") if p.is_dir())
    print(f"== bootstrap slices found: {', '.join(found) or '(none)'} ==")

    missing = [a for a in REQUIRED if a not in found]
    unknown = [a for a in found if a not in REQUIRED + OPTIONAL]
    for a in missing:
        bad(f"{a}/bootstrap/ does not exist (step 3.1 creates it)")
    for a in unknown:
        bad(f"{a}/bootstrap/ is not an account folder this project knows (conventions §6)")
    for a in OPTIONAL:
        if a not in found:
            print(f"  note  {a}/bootstrap/ absent - expected, the account is unvended (3.2)")

    ref_dir = LIVE / REFERENCE / "bootstrap"
    if not ref_dir.is_dir():
        bad(f"the reference slice {ref_dir} does not exist - nothing to compare against")
        print("\nFAILED")
        return 1

    others = [a for a in found if a != REFERENCE and a not in unknown]

    for group, transform in ((SHARED, str), (UNCOMMENTED, uncomment)):
        for name in group:
            print(f"\n== {name} ==")
            ref_path = ref_dir / name
            if not ref_path.is_file():
                bad(f"missing in the reference slice: {ref_path}")
                continue
            ref_text = transform(ref_path.read_text(encoding="utf-8"))
            for account in others:
                path = LIVE / account / "bootstrap" / name
                if not path.is_file():
                    bad(f"missing: {path}")
                    continue
                text = transform(path.read_text(encoding="utf-8"))
                if text == ref_text:
                    print(f"  same  {path}")
                    continue
                diff = list(
                    difflib.unified_diff(
                        ref_text.splitlines(),
                        text.splitlines(),
                        fromfile=str(ref_path),
                        tofile=str(path),
                        lineterm="",
                        n=1,
                    )
                )
                for line in diff[:14]:
                    print(f"    {line}")
                if len(diff) > 14:
                    print(f"    ... {len(diff) - 14} more diff line(s)")
                bad(f"{path} has diverged from the reference slice")

    print("\n== files beyond the shared set ==")
    known = set(SHARED) | set(UNCOMMENTED)
    for account in [REFERENCE] + others:
        slice_dir = LIVE / account / "bootstrap"
        allowed = ALLOWED_EXTRA.get(account, set())
        for entry in sorted(p.name for p in slice_dir.iterdir()):
            if entry in known or IGNORED.match(entry):
                continue
            if entry in allowed:
                print(f"  ok    {slice_dir}/{entry} (allow-listed)")
                continue
            bad(f"{slice_dir}/{entry} exists in one slice only and is not allow-listed")
    for account, names in ALLOWED_EXTRA.items():
        for name in names:
            if not (LIVE / account / "bootstrap" / name).is_file():
                bad(f"allow-listed but absent: {LIVE / account / 'bootstrap' / name}")

    print()
    print("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
