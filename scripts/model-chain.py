#!/usr/bin/env -S uv run --quiet
# model-chain.py - Stage 17 pass 9: the approval of the version an application's task proposed in
# the account's Model Registry, found by the release's model hash (examples/app-ml/.gitlab-ci.yml).
#
#   run:      ./scripts/model-chain.py approve staging|production --application <app>
#                 --sha256 <hex> --approver <login>
#                 # the one version of the account's group for <app> whose description carries
#                 # the release's model hash, PendingManualApproval or already Approved
#             ./scripts/model-chain.py --check
#                 # the lookup by hash and the group's ARN on stand-in values, offline: what
#                 # `make check` runs
#   reads:    the account's sagemaker/ state object, whose model_package_group_arns names the
#             application's group (tfhygiene.states); the versions of that group. Nothing with
#             --check.
#   writes:   the approval status of the version it finds.
#   exit:     0 done | 1 a check failed | 2 usage
#
# Run as the account's deploy role, the deploy runner's profile for it; by hand, the account's
# infrastructure profile. The aws CLI is the one dependency, as in the repository's other scripts.

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

from tfhygiene.states import StateError, state_outputs

# An application's model package group as sagemaker/'s output model_package_group_arns names it: the
# group awsds-<env>-model-<application> (registry.tf), the name the deploy roles' grants name.
GROUP_ARN = re.compile(
    r"arn:aws:sagemaker:[a-z0-9-]+:[a-z0-9]+:model-package-group/"
    r"awsds-[a-z]+-model-(app-[a-z0-9-]+)"
)


class ChainError(Exception):
    pass


def aws_json(*args: str) -> dict:
    res = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    if res.returncode != 0:
        raise ChainError(f"aws {' '.join(args[:2])}: {res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def hash_mark(sha256: str) -> str:
    """How a version's description carries its archive's SHA-256: examples/app-ml's register task
    writes `app-ml sha256:<hex>, trained by <job>`."""
    return f"sha256:{sha256}"


def versions_with_hash(summaries: list, sha256: str) -> list:
    """The version summaries whose description carries the hash."""
    mark = hash_mark(sha256)
    return [s for s in summaries if mark in (s.get("ModelPackageDescription") or "")]


def application_group(groups: dict, account: str, application: str) -> str:
    """The ARN of the application's group in `groups`, the account's model_package_group_arns; no
    group, or one that is not awsds-<env>-model-<application> by its ARN, fails."""
    group = groups.get(application)
    if not group:
        raise ChainError(f"{account}/sagemaker names no model package group for {application}")
    shape = GROUP_ARN.fullmatch(group)
    if not shape or shape.group(1) != application:
        raise ChainError(
            f"{account}/sagemaker's group for {application} is not the ARN of "
            f"awsds-<env>-model-{application}: {group}"
        )
    return group


def release_version(account: str, application: str, sha256: str) -> str:
    """The ARN of the one version whose description carries the hash, in the account's group for
    the application, which its sagemaker/ state names; any other count fails."""
    groups = state_outputs(account, "sagemaker").get("model_package_group_arns") or {}
    group = application_group(groups, account, application)
    summaries = aws_json(
        "sagemaker", "list-model-packages", "--model-package-group-name", group
    ).get("ModelPackageSummaryList", [])
    found = versions_with_hash(summaries, sha256)
    if len(found) != 1:
        name = group.rsplit("/", 1)[-1]
        raise ChainError(f"{len(found)} version(s) of {name} carry sha256 {sha256}, one expected")
    return found[0]["ModelPackageArn"]


def pending_release_version(args) -> str | None:
    """The release's version, printed with its training job and its metrics: its ARN while it is
    PendingManualApproval, None once Approved; any other status fails."""
    arn = release_version(args.account, args.application, args.sha256)
    described = aws_json("sagemaker", "describe-model-package", "--model-package-name", arn)
    status = described["ModelApprovalStatus"]
    metadata = described.get("CustomerMetadataProperties") or {}
    quality = (described.get("ModelMetrics") or {}).get("ModelQuality") or {}
    metrics = (quality.get("Statistics") or {}).get("S3Uri")
    print(
        f"{arn}: {status}, trained by {metadata.get('training_job')}, validation AUC "
        f"{metadata.get('validation_auc')}, metrics {metrics}"
    )
    if status == "Approved":
        return None
    if status != "PendingManualApproval":
        raise ChainError(f"{arn} is {status}: a release approves a PendingManualApproval version")
    return arn


def approve(args) -> int:
    """The release's version, found by its model hash, approved and read back Approved; left as it
    is once Approved."""
    arn = pending_release_version(args)
    if arn is None:
        return 0
    aws_json(
        "sagemaker",
        "update-model-package",
        "--model-package-arn",
        arn,
        "--model-approval-status",
        "Approved",
        "--approval-description",
        f"approved by {args.approver} at the promotion pipeline's {args.account} leg",
    )
    status = aws_json("sagemaker", "describe-model-package", "--model-package-name", arn)[
        "ModelApprovalStatus"
    ]
    print(f"{arn}: {status}")
    if status != "Approved":
        raise ChainError(f"the version reads {status} after the update")
    return 0


def check() -> int:
    """The lookup by hash and the application's group on stand-in values, offline."""
    problems = []
    summaries = [
        {"ModelPackageArn": "v1", "ModelPackageDescription": f"app-ml sha256:{'a' * 64}, by j"},
        {"ModelPackageArn": "v2", "ModelPackageDescription": "app-ml v0.1.0, trained by j"},
        {"ModelPackageArn": "v3"},
    ]
    if [s["ModelPackageArn"] for s in versions_with_hash(summaries, "a" * 64)] != ["v1"]:
        problems.append("the release's version is not found by its hash")
    if versions_with_hash(summaries, "b" * 64):
        problems.append("a version found for a hash no description carries")
    group = "arn:aws:sagemaker:region:account:model-package-group/awsds-staging-model-app-ml"
    try:
        if application_group({"app-ml": group}, "staging", "app-ml") != group:
            problems.append("the application's group is not the ARN sagemaker/ names")
    except ChainError as e:
        problems.append(f"the application's group refused: {e}")
    refused = {
        "no group": {},
        "a group's name": {"app-ml": "awsds-staging-model-app-ml"},
        "another application's group": {"app-ml": group.replace("app-ml", "app-genai")},
    }
    for label, groups in refused.items():
        try:
            application_group(groups, "staging", "app-ml")
            problems.append(f"{label} passed as the application's group")
        except ChainError:
            pass
    for problem in problems:
        print(f"  FAIL  {problem}")
    print(f"  {'ok' if not problems else 'FAILED'}    the approval's lookup, offline")
    print()
    print("OK" if not problems else "FAILED")
    return 1 if problems else 0


def main(argv: list) -> int:
    if argv == ["--check"]:
        return check()
    ap = argparse.ArgumentParser(
        description="Approve the version of an application's model that a release carries."
    )
    commands = ap.add_subparsers(dest="command", required=True)
    a = commands.add_parser("approve")
    a.add_argument("account", choices=["staging", "production"])
    a.add_argument("--application", required=True)
    a.add_argument("--sha256", required=True)
    a.add_argument("--approver", required=True)
    args = ap.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
        ap.error("--sha256 is 64 lowercase hex characters")
    if not re.fullmatch(r"app-[a-z0-9-]+", args.application):
        ap.error("--application is an application's name, app-<name>")
    try:
        return approve(args)
    except (ChainError, StateError, KeyError) as e:
        print(f"model-chain: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
