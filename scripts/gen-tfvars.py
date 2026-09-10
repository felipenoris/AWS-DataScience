#!/usr/bin/env -S uv run --quiet
# gen-tfvars.py - Stage 2 step 2. Writes one slice's terraform.auto.tfvars.
#
#   ./scripts/gen-tfvars.py <account-folder> <slice>
#   ./scripts/gen-tfvars.py sandbox bootstrap
#
# Two of a slice's inputs may not be literals in a .tf file: the region (region portability, scanned
# by step 9.1's check) and the <env> name token, because step 3.3 forbids writing this slice as *the*
# sandbox when D35 vends one per business unit. Both arrive as variables, from a file terraform
# auto-loads, gitignored (`*.tfvars`) and written from scripts/tfhygiene/backend.py, the same table
# gen-backend-hcl.py reads. One vocabulary for both generated files, so the region in the backend and
# the region the provider uses cannot disagree (Lesson 14).
#
# It writes a file. It makes no AWS call and creates nothing.
#
# A network slice also gets vpc_cidr and zone_ids, from the allocation table in the same module
# (Stage 3 decision 1). bootstrap/ does not: it has no subnet, and an unused zone list would send the
# next reader looking for the resource that consumes it. The emission is scoped by
# backend.NETWORK_SLICES.

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
