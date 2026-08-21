#!/usr/bin/env -S uv run --quiet
# check-provider-locks.py - the ninth gate, added 2026-08-21 by the Stage 6 plan review.
#
#   run:      ./scripts/check-provider-locks.py
#   reads:    terraform-live/*/*/versions.tf and their .terraform.lock.hcl. No AWS session,
#             no network, nothing written. `.terraform/` is pruned - the copies Terraform
#             caches under there are not the tracked file.
#   exit:     0 clean | 1 at least one violation
#
# WHY THIS EXISTS, AND IT IS A GAP THAT WAS OPEN FOR FOUR MONTHS. Stage 2 step 6.3 requires
# every committed lock file to carry THREE platforms - the laptop is darwin_arm64 and the
# Stage 7-8 runners are Linux, on both architectures (D8 puts GitLab on Graviton), and Stage 8
# step 6.2's GitHub Actions job is linux_amd64. The requirement was held by attention alone,
# and attention had already missed three slices: the Stage 5 `data/` ones each carried a
# single h1: hash until the 2026-08-21 review measured them. The tree's only lock-adjacent
# check before this one was check-bootstrap-parity.py, which covers five slices of twenty-four.
#
# WHAT GOES WRONG WHEN A PLATFORM IS MISSING, stated precisely because the two failure modes
# read nothing alike and only one of them is loud:
#
#   cache-backed init   (TF_PLUGIN_CACHE_DIR, which this repository MANDATES - see
#                       terraform-live/README.md and the pre-commit note) FAILS OUTRIGHT.
#                       Terraform has a directory, not a zip, so it can only compute an h1:
#                       hash, and there is no h1: for that platform to match. The error talks
#                       about checksums and reads like a supply-chain attack.
#   registry-backed init verifies against the 16 zh: hashes the registry signs, then APPENDS
#                       the missing h1: - so the job succeeds and silently rewrites a file
#                       that is committed. In CI that is a dirty worktree, or a `git diff
#                       --exit-code` failure two steps later that names the wrong cause.
#
# WHAT IT CANNOT SEE, AND THE HONESTY MATTERS (Lesson 13). A lock file records the hashes and
# NOT the platform names they belong to. So checks 2 and 3 below compare COUNTS and SETS: they
# can prove that a slice has fewer platforms than the tree's convention, or fewer than a
# sibling locked at the same version, and they can never prove that the three present are the
# three that were asked for. Only re-running the command in the fix message decides that.
#
# WHAT IT DELIBERATELY DOES NOT FAIL ON: the locked VERSION differing between slices. Stage 6
# left the four new slices at aws 6.61.0 against the tree's 6.60.0, both inside `~> 6.60`, and
# recorded the acceptance - a slice initialised today gets today's patch, which is what a lock
# file is for. The census is printed instead, so the split is visible without being a gate.

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from pathlib import Path

LIVE = Path("terraform-live")

# Step 6.3's list, as a constant so the count below and the fix message cannot disagree.
LOCK_PLATFORMS = ("darwin_arm64", "linux_amd64", "linux_arm64")

# The slice whose versions.tf every other slice is compared against. It is an ordinary slice,
# not a special one: what matters is that there is exactly one reference and that it is named.
REFERENCE = ("sandbox", "foundation")

PROVIDER_RE = re.compile(r'^provider "([^"]+)" \{(.*?)^\}', re.S | re.M)
VERSION_RE = re.compile(r'^\s*version\s*=\s*"([^"]+)"', re.M)
H1_RE = re.compile(r'"h1:')
REQUIRED_VERSION_RE = re.compile(r'required_version\s*=\s*"([^"]+)"')
AWS_CONSTRAINT_RE = re.compile(
    r'aws\s*=\s*\{[^}]*?source\s*=\s*"hashicorp/aws"[^}]*?version\s*=\s*"([^"]+)"', re.S
)


def slices() -> list[tuple[str, str, Path]]:
    """(account, name, dir) for every folder under terraform-live with a .tf file in it."""
    out = []
    for path in sorted(LIVE.glob("*/*")):
        if not path.is_dir() or path.name == ".terraform":
            continue
        if not any(path.glob("*.tf")):
            continue
        out.append((path.parent.name, path.name, path))
    return out


def lock_blocks(lock: Path) -> dict[str, tuple[str, int]]:
    """provider source -> (locked version, number of h1: hashes)."""
    text = lock.read_text(encoding="utf-8")
    blocks: dict[str, tuple[str, int]] = {}
    for source, body in PROVIDER_RE.findall(text):
        m = VERSION_RE.search(body)
        blocks[source] = (m.group(1) if m else "?", len(H1_RE.findall(body)))
    return blocks


def h1_set(lock: Path, source: str) -> set[str]:
    text = lock.read_text(encoding="utf-8")
    for src, body in PROVIDER_RE.findall(text):
        if src == source:
            return set(re.findall(r'"(h1:[^"]+)"', body))
    return set()


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    failures: list[str] = []

    def bad(text: str) -> None:
        failures.append(text)
        print(f"  FAIL  {text}")

    rows = slices()
    print(f"== {len(rows)} slice(s) under {LIVE}/ ==")

    # ------------------------------------------------------------------ 1. a lock at all
    locked: list[tuple[str, str, Path, Path]] = []
    for account, name, path in rows:
        lock = path / ".terraform.lock.hcl"
        if not lock.is_file():
            bad(
                f"{account}/{name} has .tf files and no committed .terraform.lock.hcl - "
                "a slice whose provider build is not pinned resolves differently per machine"
            )
            continue
        locked.append((account, name, path, lock))

    # ------------------------------------------------ 2. every provider block has N platforms
    per_group: dict[tuple[str, str], list[tuple[str, str, Path]]] = defaultdict(list)
    census: dict[tuple[str, str], int] = defaultdict(int)
    for account, name, _path, lock in locked:
        for source, (version, h1s) in lock_blocks(lock).items():
            census[(source, version)] += 1
            per_group[(source, version)].append((account, name, lock))
            if h1s < len(LOCK_PLATFORMS):
                bad(
                    f"{account}/{name}: provider {source} carries {h1s} h1: hash(es), "
                    f"fewer than the {len(LOCK_PLATFORMS)} platforms step 6.3 requires. "
                    f"Fix: terraform -chdir={_path} providers lock "
                    + " ".join(f"-platform={p}" for p in LOCK_PLATFORMS)
                    + "  (or copy a sibling's file, which is what step 6.3 actually asks for "
                    "- the lock is a function of the constraint and the platform list, so "
                    "regenerating per slice re-resolves the constraint and can move the version)"
                )

    # ------------------------------- 3. no slice is a strict subset of its version-group's union
    for (source, version), members in sorted(per_group.items()):
        if len(members) < 2:
            continue
        sets = {(a, n): h1_set(lock, source) for a, n, lock in members}
        union: set[str] = set().union(*sets.values())
        for (a, n), got in sorted(sets.items()):
            if got and got < union:
                bad(
                    f"{a}/{n}: provider {source} {version} is missing "
                    f"{len(union - got)} hash(es) that a sibling locked at the same version "
                    "carries - the platforms are not the same set across the tree"
                )

    # -------------------------------------- 4. one required_version and one aws constraint
    ref_dir = LIVE / REFERENCE[0] / REFERENCE[1]
    ref_versions = ref_dir / "versions.tf"
    if not ref_versions.is_file():
        bad(f"the reference slice {REFERENCE[0]}/{REFERENCE[1]} has no versions.tf")
    else:
        ref = ref_versions.read_text(encoding="utf-8")
        ref_req = REQUIRED_VERSION_RE.search(ref)
        ref_aws = AWS_CONSTRAINT_RE.search(ref)
        for account, name, path in rows:
            vf = path / "versions.tf"
            if not vf.is_file():
                bad(f"{account}/{name} has no versions.tf")
                continue
            text = vf.read_text(encoding="utf-8")
            req = REQUIRED_VERSION_RE.search(text)
            aws = AWS_CONSTRAINT_RE.search(text)
            if ref_req and (not req or req.group(1) != ref_req.group(1)):
                bad(
                    f"{account}/{name}: required_version "
                    f"{req.group(1) if req else '(absent)'} differs from "
                    f"{REFERENCE[0]}/{REFERENCE[1]}'s {ref_req.group(1)}"
                )
            if ref_aws and (not aws or aws.group(1) != ref_aws.group(1)):
                bad(
                    f"{account}/{name}: the hashicorp/aws constraint "
                    f"{aws.group(1) if aws else '(absent)'} differs from "
                    f"{REFERENCE[0]}/{REFERENCE[1]}'s {ref_aws.group(1)}"
                )
            # A SECOND PROVIDER IS EXPLICITLY ALLOWED and is not compared: Stage 6's three
            # awscc-declaring slices are the reason this check exists in this shape rather
            # than as a byte-comparison of versions.tf (terraform-live/README.md says which).

    # ------------------------------------------------------- the census, reported not gated
    print("\n== locked versions across the tree (reported, never failed) ==")
    for (source, version), n in sorted(census.items()):
        print(f"  {source} {version}  x{n}")
    print(
        "  a split here is legal: every constraint is a range, and a slice initialised later\n"
        "  gets a later patch. It is printed so the split is visible without being a gate."
    )

    if failures:
        print(f"\n\033[1mprovider locks: {len(failures)} FAILED\033[0m")
        return 1
    print("\n\033[1mprovider locks: OK\033[0m")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
