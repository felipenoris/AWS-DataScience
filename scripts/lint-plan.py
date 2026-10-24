#!/usr/bin/env -S uv run --quiet
# lint-plan.py - Stage 10 step 2.3, rule (2c): an application slice's saved plan read before its apply,
# in each promotion leg (Stage 8 steps 3.2, 3.5 and 3.6).
#
#   run:      ./scripts/lint-plan.py <account> <plan.json> --tag vX.Y.Z [--app app-etl]
#   reads:    the JSON `terraform show -json` prints for the saved plan; data/'s state for the outputs
#             bucket, as release-application.py reads it.
#   lint:     `awsds-workflows lint-plan <plan.json> --prefix s3://<bucket>/applications/<app>/<tag>/glue/`,
#             the tool taken from AWSDS_WORKFLOWS (the `uvx --from` source the template's .gitlab-ci.yml
#             pins) or from PATH. It refuses an aws_glue_job the apply leaves whose script, or a file or
#             module its arguments name, lies outside the release's glue/ folder; a module named by its
#             PyPI name; and a script the plan does not know.
#   writes:   nothing.
#   exit:     0 the lint passed | 1 refused, or a check failed | 2 usage
#
# A plan that leaves no aws_glue_job fails after the lint passes: the lint prints ok over zero jobs
# (Lesson 71), and the application slice plans none only when it read no release, whose apply destroys
# any job it holds.

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

from tfhygiene.states import StateError, state_outputs


class PlanError(Exception):
    pass


def glue_jobs(plan: Path) -> list:
    """The address of each aws_glue_job the apply leaves: created, updated or kept."""
    doc = json.loads(plan.read_text(encoding="utf-8"))
    return [
        change.get("address")
        for change in doc.get("resource_changes") or []
        if change.get("mode") == "managed"
        and change.get("type") == "aws_glue_job"
        and isinstance((change.get("change") or {}).get("after"), dict)
    ]


def lint(plan: Path, prefix: str) -> None:
    """awsds-workflows lint-plan on the plan; a refusal is the job's failure."""
    source = os.environ.get("AWSDS_WORKFLOWS", "")
    tool = ["uvx", "--from", source, "awsds-workflows"] if source else ["awsds-workflows"]
    cmd = [*tool, "lint-plan", str(plan), "--prefix", prefix]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"  {' '.join(shlex.quote(c) for c in cmd[len(tool) :])}")
    for line in (res.stdout + res.stderr).splitlines():
        print(f"    {line}")
    if res.returncode != 0:
        raise PlanError(f"{plan.name}: refused by lint-plan (exit {res.returncode})")


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="Lint an application slice's saved plan.")
    ap.add_argument("account", choices=["staging", "production"])
    ap.add_argument("plan", type=Path, help="the JSON of terraform show -json on the saved plan")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--app", default="app-etl")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", args.app):
        ap.error("--app is the application's name, lowercase letters, digits and hyphens")
    try:
        bucket = state_outputs(args.account, "data").get("outputs_bucket_name")
        if not bucket:
            raise PlanError(f"{args.account}/data/'s state has no outputs_bucket_name")
        prefix = f"s3://{bucket}/applications/{args.app}/{args.tag}/glue/"
        print(f"== {args.plan.name} against {prefix}")
        lint(args.plan, prefix)
        if not glue_jobs(args.plan):
            raise PlanError(
                f"{args.plan.name}: no aws_glue_job is left by the apply, so none was read"
            )
        return 0
    except (OSError, PlanError, StateError, ValueError) as e:
        # The lint's lines first: in a job's log, stdout is a pipe and reaches the log at exit.
        sys.stdout.flush()
        print(f"lint-plan: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
