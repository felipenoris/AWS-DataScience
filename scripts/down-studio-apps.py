#!/usr/bin/env -S uv run --quiet
# down-studio-apps.py - Stage 2 step 8.6. The teardown hook that is empty until Stage 6.
#
#   ./scripts/down-studio-apps.py <env>     called by `make down` before anything is destroyed
#   exit: 0 nothing to delete | 1 there IS something and this hook is still a stub | 2 usage
#
# WHY IT EXISTS BEFORE THE THING IT DELETES. docs/plan/conventions.md 6 requires `make down` to
# delete running Studio apps through sagemaker:ListApps / DeleteApp against the
# blueprint-provisioned domain, DISCOVERING the domain id rather than having it pasted in - a
# Studio app is metered by the hour and is created from the console by a person, so it is the
# one [E]-shaped thing Terraform does not own and `terraform destroy` cannot reach. Step 8.6
# asks for the hook now and empty: a hook added later is a hook that was missing from the first
# teardown that needed it.
#
# WHAT MAKES THIS MORE THAN A STUB, and it is the only line worth arguing about. An empty hook
# that exits 0 forever reports the same thing whether Stage 6 has run or not (Lesson 13), and
# the day a domain exists the silence would read as "no apps running". So it DETECTS ITS OWN
# OBSOLESCENCE: no domain -> exit 0 and say so; a domain -> exit 1 with the sentence naming who
# owes the body. It cannot delete anything, and it is not meant to be able to.
#
# READ-ONLY. sagemaker:ListDomains and nothing else, through the account's own SSO profile
# (AWS_PROFILE per command - Lesson 25). It creates nothing and deletes nothing today.

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tfhygiene import backend


def main(argv: list) -> int:
    os.chdir(Path(__file__).resolve().parents[1])

    if len(argv) != 1:
        print("usage: down-studio-apps.py <env>", file=sys.stderr)
        return 2
    env = argv[0]
    try:
        profile = backend.profile(env)
    except backend.UnknownAccountFolder:
        print(f"unknown account folder: {env}", file=sys.stderr)
        return 2

    proc = subprocess.run(
        [
            "aws",
            "sagemaker",
            "list-domains",
            "--region",
            backend.REGION,
            "--profile",
            profile,
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        # NOT a pass. A hook that cannot look must not report an empty result, or `make down`
        # would treat an expired token as "no apps are running" (Lesson 13, and Lesson 24 -
        # the defence against the benign failure is what hides the serious one).
        print(f"    could not list domains in {env} ({profile}) - this is NOT evidence that")
        print("    no app is running. Log in first:  aws sso login --sso-session awsds")
        print(f"    {proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else ''}")
        return 1

    domains = json.loads(proc.stdout or "{}").get("Domains", [])
    if not domains:
        print(f"    no SageMaker domain in {env} - nothing to delete (Stage 6 creates the first)")
        return 0

    print(f"    {len(domains)} SageMaker domain(s) exist in {env} and THIS HOOK IS STILL A STUB.")
    print("    Stage 6 owes it a body: list the apps of each domain and delete them before")
    print("    `make down` destroys anything - see Stage 2 step 8.6 and conventions 6.")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
