#!/usr/bin/env -S uv run --quiet
# devenv-register.py - Stage 8 step 1.6. Registers a dev-env release in every account that runs the
# house image: it applies each account's dev-env/ slice with the release's image tag, which becomes a
# new SageMaker image version (CreateImageVersion resolves the tag to its digest, and the previous
# version is destroyed), and prints the version the account then holds. The registration job of
# awsds/dev-env's release pipeline runs it on the deploy runner; the same command from the laptop is
# the by-hand path (conventions §6: a rebuild that only works from CI is the same bug as one that only
# works by hand).
#
#   ./scripts/devenv-register.py --tag default-v0.7.0-1a2b3c4d               # the laptop, SSO profiles
#   ./scripts/devenv-register.py --pipeline --tag <tag> --digest sha256:<..> # the deploy runner
#   ./scripts/devenv-register.py --dry-run --tag <tag>                       # print, run nothing
#
#   needs:    on the laptop, an SSO session as the infrastructure user (awsds-infra-sandbox-1, and
#             awsds-infra-prod for the registry's state); on the runner, the deploy profiles of
#             AWS_CONFIG_FILE (production/runners/deploy-runner.tf)
#   writes:   each target's dev-env/ state, a new image version, and the destroy of the previous one
#   exit:     0 registered | 1 a step failed | 2 usage or refusal
#
# The targets are the accounts that run the house image and hold a dev-env deploy role,
# backend.SMUS_MEMBERS with a DEPLOY_ROLES row, so a vended Sandbox unit joins by its rows (D35). The
# pipeline acts as each target's own deploy role, which refusal 8 admits for dev-env/ alone, and reads
# the registry's state through the runner's own profile (decision 14).
#
# No guard, by decision 17: the steward deletes the domain's apps and detaches the image before the
# job runs, and re-attaches and sweeps the spaces after it (runbook dev-env.md §B); this script checks
# and performs none of it. The guards wait in issue #129.

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from tfhygiene import backend, layers

SLICE = "dev-env"
TAG_RE = re.compile(r"^[a-z0-9]+-v[0-9]+\.[0-9]+\.[0-9]+(-[0-9a-f]{8,40})?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def run(cmd: list, profile: str | None, dry: bool, capture: bool = False):
    """One subprocess as `profile`, announced first. Under --dry-run, announced and not run."""
    shown = f"AWS_PROFILE={profile} " if profile else ""
    print(f"  $ {shown}{' '.join(cmd)}", flush=True)
    if dry:
        return None
    env = dict(os.environ)
    if profile:
        env["AWS_PROFILE"] = profile
    return subprocess.run(cmd, env=env, capture_output=capture, text=True, stdin=subprocess.DEVNULL)


def targets() -> list:
    """The accounts that run the house image and hold a dev-env deploy role, in the map's order."""
    return [a for a in backend.SMUS_MEMBERS if a in backend.DEPLOY_ROLES]


def register(account: str, args, scratch: Path) -> bool:
    profile = backend.DEPLOY_ROLES[account] if args.pipeline else backend.profile(account)
    refusal = layers.pipeline_refusal(account, SLICE, profile)
    if refusal:
        print(f"  REFUSED: {refusal}")
        return False
    path = f"terraform-live/{account}/{SLICE}"
    image = f"awsds-{backend.env_token(account)}-dev-env"
    print(f"\n== {account}: {path} as {profile}, image_tag {args.tag}", flush=True)

    gen = ["./scripts/gen-tfvars.py"] + (["--pipeline"] if args.pipeline else []) + [account, SLICE]
    for cmd in (["./scripts/gen-backend-hcl.py", account, SLICE], gen):
        res = run(cmd, None, args.dry_run)
        if res is not None and res.returncode != 0:
            print(f"  FAILED: {cmd[0]} exited {res.returncode}")
            return False

    tf = ["terraform", f"-chdir={path}"]
    plan = scratch / f"{account}-{SLICE}.tfplan"
    steps = [
        tf + ["init", "-backend-config=backend.hcl", "-input=false", "-lockfile=readonly"],
        tf + ["plan", "-input=false", f"-var=image_tag={args.tag}", f"-out={plan}"],
        tf + ["apply", "-input=false", str(plan)],
    ]
    for cmd in steps:
        res = run(cmd, profile, args.dry_run)
        if res is not None and res.returncode != 0:
            print(f"  FAILED: terraform {cmd[2]} exited {res.returncode}")
            return False

    # The version the account now holds, read back for the steward's re-attach (dev-env.md §B steps 4
    # and 5): the number goes into CustomImages, and ContainerImage is the digest SageMaker resolved.
    res = run(tf + ["output", "-raw", "image_version_number"], profile, args.dry_run, capture=True)
    if res is None:
        return True
    if res.returncode != 0:
        print(f"  FAILED: terraform output exited {res.returncode}: {res.stderr.strip()}")
        return False
    version = res.stdout.strip()
    res = run(
        [
            "aws",
            "sagemaker",
            "describe-image-version",
            "--image-name",
            image,
            "--version-number",
            version,
            "--region",
            backend.REGION,
            "--query",
            "[ImageVersionStatus,ContainerImage]",
            "--output",
            "text",
        ],
        profile,
        args.dry_run,
        capture=True,
    )
    if res.returncode != 0:
        print(f"  FAILED: describe-image-version exited {res.returncode}: {res.stderr.strip()}")
        return False
    fields = res.stdout.split()
    status = fields[0] if fields else "?"
    container = fields[1] if len(fields) > 1 else "?"
    print(f"  {image} version {version}: {status}")
    print(f"    ContainerImage {re.sub(r'^[0-9]{12}', '<registry>', container)}")
    if args.digest:
        print(f"    pushed digest  {args.digest}")
    return True


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])
    parser = argparse.ArgumentParser(
        description="Register a dev-env release in every account that runs the house image."
    )
    parser.add_argument("--tag", required=True, help="the image tag, <flavour>-v<semver>[-<sha>]")
    parser.add_argument("--digest", help="the dev-env digest the build pushed, printed beside ours")
    parser.add_argument(
        "--pipeline",
        action="store_true",
        help="act as each target's deploy role and read the registry through the runner's profile",
    )
    parser.add_argument("--only", help="one account folder of the targets")
    parser.add_argument("--dry-run", action="store_true", help="print the commands, run none")
    args = parser.parse_args(argv)

    if not TAG_RE.match(args.tag):
        print(f"not a dev-env tag: {args.tag} - <flavour>-v<semver>[-<sha>]", file=sys.stderr)
        return 2
    if args.digest and not DIGEST_RE.match(args.digest):
        print(f"not a digest: {args.digest}", file=sys.stderr)
        return 2
    selected = targets()
    if args.only:
        if args.only not in selected:
            print(f"not a target: {args.only} - targets: {', '.join(selected)}", file=sys.stderr)
            return 2
        selected = [args.only]

    # The commit this run applies, so a stale checkout shows in the job's log (Stage 8 step 6.1).
    head = subprocess.run(
        ["git", "log", "-1", "--format=%H %cI %s"], capture_output=True, text=True
    ).stdout.strip()
    print(f"infrastructure checkout: {head or 'not a git checkout'}")
    print(f"targets: {', '.join(selected)}")

    failed = 0
    with tempfile.TemporaryDirectory(prefix="devenv-register-") as tmp:
        for account in selected:
            if not register(account, args, Path(tmp)):
                failed += 1
    if failed:
        print(f"\n{failed} target(s) not registered", file=sys.stderr)
        return 1
    print(
        "\nregistered; the steward re-attaches and sweeps the spaces (dev-env.md §B steps 5 and 6)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
