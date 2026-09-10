#!/usr/bin/env -S uv run --quiet
# gen-backend-hcl.py - Stage 2 step 2.5. Writes one slice's backend.hcl.
#
#   ./scripts/gen-backend-hcl.py <account-folder> <slice>
#   ./scripts/gen-backend-hcl.py production pki
#
# A `backend` block interpolates nothing, no var and no local, so the bucket, the key and the region
# have to be literals somewhere. docs/plan/architecture.md forbids a region literal in a .tf file and
# step 9's check scans for one. Partial backend configuration reconciles the two: `backend "s3" {}`
# stays in providers.tf and the literals live in a per-slice backend.hcl, which is not a .tf file and
# is gitignored. scripts/tfhygiene/backend.py is the only place that knows how to build one, and
# step 8's Makefile calls this script rather than growing a second copy (Lesson 14).
#
# It writes a file, makes no AWS call, and does not create the bucket it names: that is the bootstrap
# slice's job, and until that slice has applied, `terraform init` against this output fails with
# NoSuchBucket (step 2.2).

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
