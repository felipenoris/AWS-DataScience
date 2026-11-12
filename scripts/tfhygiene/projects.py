"""A deployment project's values, read from the project itself (Stage 19 steps 4.6 and 4.9): its id,
and what its Tooling environment provisioned, the subnets, the security group, the key, the role and
the shared prefix. DataZone answers a member of the project, so the caller is the account's deploy
role, an owner of the project, or its infrastructure profile (scripts/deploy-application.py,
scripts/model-chain.py).
"""

from __future__ import annotations

import json
import subprocess

# The deployment project of each target, by the name an application's manifest gives its stage, and
# that stage's name and the prefix of its `${VAR}` names in the manifest.
DEPLOYMENT_PROJECT = {"staging": "deploy-staging", "production": "deploy-production"}
STAGE = {"staging": "staging", "production": "prod"}
STAGE_PREFIX = {"staging": "STAGING", "production": "PROD"}

# What DataZone answers a caller that is no member of the project.
NOT_A_MEMBER = "User is not permitted to perform operation"


class ProjectError(Exception):
    pass


def aws_json(*args: str) -> dict:
    res = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    if res.returncode != 0:
        raise ProjectError(f"aws {' '.join(args[:2])}: {res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def workflow_name(application: str, project: str, workflow: str) -> str:
    """The name the CI/CD CLI gives a workflow it creates (1.0.9, commands/deploy.py): each part
    with every character outside [A-Za-z0-9_] an underscore, joined by underscores."""

    def safe(part: str) -> str:
        return "".join(c if c.isascii() and (c.isalnum() or c == "_") else "_" for c in part)

    return "_".join(safe(part) for part in (application, project, workflow))


def stage_variables_parameter(env: str, application: str) -> str:
    """The SSM parameter a deploy records the stage's variables in and a chain's machine reads
    (terraform-modules/orchestration)."""
    return f"/awsds/{env}/applications/{application}/stage-variables"


def find_project(domain: str, region: str, name: str) -> str:
    """The id of the project named `name`; the listing matches by prefix, the name is compared."""
    token = None
    found = []
    while True:
        args = [
            "datazone",
            "list-projects",
            "--domain-identifier",
            domain,
            "--name",
            name,
            "--region",
            region,
        ]
        if token:
            args += ["--next-token", token]
        page = aws_json(*args)
        found += [p["id"] for p in page.get("items", []) if p.get("name") == name]
        token = page.get("nextToken")
        if not token:
            break
    if len(found) != 1:
        raise ProjectError(f"{len(found)} project(s) named {name} in {domain}, one expected")
    return found[0]


def tooling_resources(domain: str, region: str, project: str) -> dict:
    """The provisioned resources of the project's default Tooling environment, by name."""
    page = aws_json(
        "datazone",
        "list-environments",
        "--domain-identifier",
        domain,
        "--project-identifier",
        project,
        "--region",
        region,
    )
    for item in page.get("items", []):
        environment = aws_json(
            "datazone",
            "get-environment",
            "--domain-identifier",
            domain,
            "--identifier",
            item["id"],
            "--region",
            region,
        )
        resources = {r["name"]: r.get("value") for r in environment.get("provisionedResources", [])}
        if resources.get("isDefaultToolingEnvironment") == "true":
            resources["awsAccountId"] = environment.get("awsAccountId")
            return resources
    raise ProjectError(f"the project {project} holds no default Tooling environment")


def values_from(project_name: str, project_id: str, resources: dict) -> dict:
    """The project's values out of its Tooling environment's resources, each one required."""
    wanted = {
        "account_id": "awsAccountId",
        "role_arn": "userRoleArn",
        "security_group": "securityGroup",
        "key_arn": "kmsKeyArn",
        "subnets": "privateSubnets",
        "shared_uri": "nonGitProjectRepositoryLocation",
    }
    missing = [name for name in wanted.values() if not resources.get(name)]
    if missing:
        raise ProjectError(
            f"the Tooling environment of {project_name} names no {', '.join(sorted(missing))}"
        )
    subnets = [s for s in resources[wanted["subnets"]].split(",") if s]
    if len(subnets) < 2:
        raise ProjectError(f"the Tooling environment of {project_name} names {len(subnets)} subnet")
    values = {key: resources[name] for key, name in wanted.items()}
    values.update(
        project_name=project_name,
        project_id=project_id,
        subnets=subnets,
        shared_uri=resources[wanted["shared_uri"]].rstrip("/") + "/",
    )
    return values


def project_values(account: str, domain: str, region: str) -> dict:
    """The deployment project of `account`: its id and its Tooling environment's values."""
    if account not in DEPLOYMENT_PROJECT:
        raise ProjectError(f"{account}: no deployment project ({', '.join(DEPLOYMENT_PROJECT)})")
    name = DEPLOYMENT_PROJECT[account]
    project_id = find_project(domain, region, name)
    return values_from(name, project_id, tooling_resources(domain, region, project_id))


def is_member(domain: str, region: str, project: str) -> bool:
    """Whether DataZone answers the caller the project's connections, which it answers a member
    alone: the call the CLI's deploy stops at for a non-member (SUP-159)."""
    res = subprocess.run(
        [
            "aws",
            "datazone",
            "list-connections",
            "--domain-identifier",
            domain,
            "--project-identifier",
            project,
            "--region",
            region,
            "--max-results",
            "1",
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return True
    if NOT_A_MEMBER in res.stderr:
        return False
    raise ProjectError(f"aws datazone list-connections: {res.stderr.strip()}")
