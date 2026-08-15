#!/usr/bin/env -S uv run --quiet
# Generate a slice's backend.hcl - Stage 2 step 2.5.
#
#   ./scripts/gen-backend-hcl.py <account-folder> <slice>
#   ./scripts/gen-backend-hcl.py production pki
#
# WHY THIS FILE IS GENERATED AND NOT WRITTEN. A `backend` block cannot interpolate anything -
# no var, no local - so the bucket, the key and the REGION have to be literals somewhere.
# docs/plan/architecture.md forbids region literals in .tf files, and step 9's check scans for
# them. Partial backend configuration is the reconciliation: `backend "s3" {}` stays in
# providers.tf and the literals live in a per-slice backend.hcl, which is not a .tf file and
# is gitignored. The content itself is scripts/tfhygiene/backend.py, the ONLY place that
# knows how to build one - step 8's Makefile calls this script rather than growing a second
# copy (Lesson 14: two mechanisms for one file is a defect waiting).
#
# It writes a file. It makes no AWS call, and it does not create the bucket it names - that
# is the bootstrap slice's job, and until that slice has applied, `terraform init` against
# the output of this script fails with NoSuchBucket. That order is step 2.2's
# chicken-and-egg, not a fault here.

from __future__ import annotations

import os
import sys
from pathlib import Path

from tfhygiene import backend


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    if len(argv) != 2:
        print("usage: gen-backend-hcl.py <account-folder> <slice>", file=sys.stderr)
        return 2
    account, slice_name = argv

    try:
        values = backend.backend_values(account, slice_name)
    except backend.UnknownAccountFolder:
        print(f"unknown account folder: {account}", file=sys.stderr)
        return 2

    slice_dir = Path("terraform-live") / account / slice_name
    if not slice_dir.is_dir():
        print(f"no such slice: {slice_dir}", file=sys.stderr)
        return 2

    (slice_dir / "backend.hcl").write_text(backend.render(account, slice_name), encoding="utf-8")

    print(f"wrote {slice_dir}/backend.hcl")
    print(f"  bucket {values['bucket']}   key {values['key']}   kms {values['kms_key_id']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
