#!/usr/bin/env -S uv run --quiet
"""Stage 6i's placeholders, filled with the live values of the Sandbox project.

    ./examples/sandbox-orchestration/render.py --values
    ./examples/sandbox-orchestration/render.py examples/sandbox-orchestration/devenv-job/demo-devenv-job.probe.yaml
    ./examples/sandbox-orchestration/render.py --profile awsds-infra-sandbox-1 README.md

The repository holds every account-scoped value as a `<PLACEHOLDER>` (Stage 6i decision 1),
and the portal needs the real ones. This script reads them with read-only calls, as the
profile given (the infrastructure user's InfrastructureAccess in Sandbox by default), and
prints the rendered file to stdout. Nothing it prints is written to the repository.

Every value is read, never assumed: the project from its role's tags, the security group the
Tooling blueprint created for the project, the private subnets by name, and the house image's
digest from the image version registered in Sandbox.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROLE_PREFIX = "datazone_usr_role_"
HOUSE_IMAGE = "awsds-sandbox-dev-env"
PRIVATE_SUBNETS = "awsds-sandbox-private-*"
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]+)>")


def aws(profile: str, region: str | None, *args: str):
    cmd = ["aws", "--profile", profile] + (["--region", region] if region else []) + list(args)
    proc = subprocess.run(cmd + ["--output", "json"], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.exit(f"aws {' '.join(args[:2])} failed: {proc.stderr.strip()}")
    return json.loads(proc.stdout or "null")


def read_values(profile: str, project: str | None) -> dict:
    proc = subprocess.run(
        ["aws", "--profile", profile, "configure", "get", "region"], capture_output=True, text=True
    )
    region = proc.stdout.strip()
    if not region:
        sys.exit(f"the profile {profile} names no region")
    account = aws(profile, region, "sts", "get-caller-identity")["Account"]

    roles = aws(
        profile,
        region,
        "iam",
        "list-roles",
        "--query",
        f"Roles[?starts_with(RoleName, '{PROJECT_ROLE_PREFIX}')].RoleName",
    )
    found = {}
    for name in roles or []:
        tags = aws(profile, region, "iam", "get-role", "--role-name", name)["Role"].get("Tags", [])
        found[name] = {t["Key"]: t["Value"] for t in tags}
    if project:
        found = {n: t for n, t in found.items() if t.get("AmazonDataZoneProject") == project}
    if len(found) != 1:
        sys.exit(
            f"{len(found)} project roles match - name the project with --project "
            f"({', '.join(t.get('AmazonDataZoneProject', '?') for t in found.values()) or 'none read'})"
        )
    role, tags = next(iter(found.items()))
    project_id = tags["AmazonDataZoneProject"]
    vpc = tags["VpcId"]

    group_name = f"datazone-{project_id}-{tags.get('AmazonDataZoneScopeName', 'dev')}"
    groups = aws(
        profile,
        region,
        "ec2",
        "describe-security-groups",
        "--filters",
        f"Name=vpc-id,Values={vpc}",
        f"Name=group-name,Values={group_name}",
    )["SecurityGroups"]
    if len(groups) != 1:
        sys.exit(f"{len(groups)} security groups named {group_name} in {vpc}")

    subnets = aws(
        profile,
        region,
        "ec2",
        "describe-subnets",
        "--filters",
        f"Name=vpc-id,Values={vpc}",
        f"Name=tag:Name,Values={PRIVATE_SUBNETS}",
    )["Subnets"]
    subnets.sort(key=lambda s: s["AvailabilityZoneId"])
    if len(subnets) < 2:
        sys.exit(f"{len(subnets)} private subnets in {vpc} - the private shape needs two AZs")

    image = aws(profile, region, "sagemaker", "describe-image-version", "--image-name", HOUSE_IMAGE)
    container = image["ContainerImage"]
    if "@" not in container:
        sys.exit(f"the registered image is not pinned by digest: {container}")

    return {
        "REGION": region,
        "SANDBOX_ACCOUNT_ID": account,
        "REGISTRY_ACCOUNT_ID": container.split(".", 1)[0],
        "PROJECT_ROLE_NAME": role,
        "PROJECT_KEY_ID": tags["KmsKeyId"],
        "PROJECTS_BUCKET": tags["DomainBucketName"],
        "DOMAIN_ID": tags["AmazonDataZoneDomain"],
        "PROJECT_ID": project_id,
        "PROJECT_SG": groups[0]["GroupId"],
        "SUBNET_AZ1": subnets[0]["SubnetId"],
        "SUBNET_AZ2": subnets[1]["SubnetId"],
        "IMAGE_DIGEST": container.split("@", 1)[1],
        "DEMO_PREFIX": f"{tags['AmazonDataZoneDomain']}/{project_id}/shared/orchestration-demo",
    }


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="render.py", description=__doc__.split("\n")[0])
    parser.add_argument("file", nargs="?", type=Path, help="a file holding <PLACEHOLDER>s")
    parser.add_argument("--values", action="store_true", help="print the values, not a file")
    parser.add_argument("--profile", default="awsds-infra-sandbox-1")
    parser.add_argument("--project", help="the project id, when the account holds more than one")
    args = parser.parse_args(argv)
    if not args.values and args.file is None:
        parser.error("name a file, or pass --values")

    values = read_values(args.profile, args.project)
    if args.values:
        width = max(len(k) for k in values)
        for key, value in values.items():
            print(f"<{key}>".ljust(width + 3), value)
        return 0

    text = args.file.read_text()
    unknown = sorted({m.group(1) for m in PLACEHOLDER.finditer(text)} - set(values))
    if unknown:
        sys.exit(f"no value read for: {', '.join(unknown)}")
    sys.stdout.write(PLACEHOLDER.sub(lambda m: values[m.group(1)], text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
