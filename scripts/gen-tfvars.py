#!/usr/bin/env -S uv run --quiet
# Generate a slice's terraform.auto.tfvars - Stage 2 step 2.
#
#   ./scripts/gen-tfvars.py <account-folder> <slice>
#   ./scripts/gen-tfvars.py sandbox bootstrap
#
# WHY THIS FILE IS GENERATED AND NOT WRITTEN, which is gen-backend-hcl.py's argument one step
# out. Two of a slice's inputs may not be literals in a .tf file: the REGION (region
# portability - step 9.1's check scans for it) and the <env> NAME TOKEN, because step 3.3
# forbids writing this slice as *the* sandbox when D35 vends one per business unit. So both
# arrive as variables, from a file that is auto-loaded by terraform, gitignored (`*.tfvars`)
# and written from scripts/tfhygiene/backend.py - the SAME table gen-backend-hcl.py reads. One
# vocabulary, two generated files: the region in the backend and the region the provider uses
# cannot disagree, which they could the moment somebody typed the second one (Lesson 14).
#
# It writes a file. It makes no AWS call and creates nothing.
#
# WHAT IT DOES NOT CARRY, on purpose: zone_ids. The AZ anchors are per-environment and belong
# to a network slice's own tfvars (1b step 6, ./aws/AZs.py) - bootstrap has no subnet, and a
# generator that emitted an unused zone list would make the next reader look for the resource
# that consumes it.

from __future__ import annotations

import os
import sys
from pathlib import Path

from tfhygiene import backend


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    if len(argv) != 2:
        print("usage: gen-tfvars.py <account-folder> <slice>", file=sys.stderr)
        return 2
    account, slice_name = argv

    try:
        values = backend.tfvars_values(account, slice_name)
    except backend.UnknownAccountFolder:
        print(f"unknown account folder: {account}", file=sys.stderr)
        return 2

    slice_dir = Path("terraform-live") / account / slice_name
    if not slice_dir.is_dir():
        print(f"no such slice: {slice_dir}", file=sys.stderr)
        return 2

    (slice_dir / "terraform.auto.tfvars").write_text(
        backend.render_tfvars(account, slice_name), encoding="utf-8"
    )

    print(f"wrote {slice_dir}/terraform.auto.tfvars")
    print(
        f"  region {values['region']}   env {values['env']}"
        f"   environment_tag {values['environment_tag']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
