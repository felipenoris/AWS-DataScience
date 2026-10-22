#!/usr/bin/env -S uv run --quiet
# check-copies.py - files kept as one file in several slices, byte for byte.
#
#   run:      ./scripts/check-copies.py
#   reads:    the files COPIES names. No AWS session, no side effect, nothing written.
#   exit:     0 clean | 1 a copy is missing or has diverged
#
# The application ceiling and the deploy role's application and orchestration grants sit in each
# deployment target's foundation/, beside the deploy role whose ceiling names them (Stage 8 steps 3.0
# and 4.1). A copy and not a module because the grants change at their first applies, which read the
# calls they make, and a module would turn each change into a tag (Recipe B). The copy's failure mode
# is Lesson 14: a statement changed in one account and not in the other, with nothing announcing it.
# What one account adds lives outside the copied file, in a document of its own.
#
# The application slice, <env>/app/app-etl/ (Stage 8 steps 3.2 and 3.6), is one slice in both
# targets but for release.tf, which records each account's own promoted release (step 3.7).
#
# check-bootstrap-parity.py holds the same rule for the bootstrap slices, which are copies whole.

from __future__ import annotations

import difflib
import os
import sys
from pathlib import Path

DEPLOY_TARGETS = ("terraform-live/staging/foundation", "terraform-live/production/foundation")
APPLICATION = ("terraform-live/staging/app/app-etl", "terraform-live/production/app/app-etl")

# (file name, the slices holding it). The first slice is the reference a divergence is reported
# against.
COPIES = (
    ("app-boundary.tf", DEPLOY_TARGETS),
    ("apply-application.tf", DEPLOY_TARGETS),
    ("apply-orchestration.tf", DEPLOY_TARGETS),
    *(
        (name, APPLICATION)
        for name in (
            "backend.tf",
            "data.tf",
            "main.tf",
            "outputs.tf",
            "providers.tf",
            "variables.tf",
            "versions.tf",
        )
    ),
)


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    fail = 0

    def bad(text: str) -> None:
        nonlocal fail
        fail = 1
        print(f"  FAIL  {text}")

    for name, slices in COPIES:
        print(f"== {name} ==")
        ref_path = Path(slices[0]) / name
        if not ref_path.is_file():
            bad(f"missing in the reference slice: {ref_path}")
            continue
        ref_text = ref_path.read_text(encoding="utf-8")
        for slice_dir in slices[1:]:
            path = Path(slice_dir) / name
            if not path.is_file():
                bad(f"missing: {path}")
                continue
            text = path.read_text(encoding="utf-8")
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
            bad(f"{path} has diverged from {ref_path}")

    print()
    print("OK" if fail == 0 else "FAILED")
    return fail


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
