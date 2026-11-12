#!/usr/bin/env -S uv run --quiet
# deploy-application.py - Stage 19 step 4.9: a release's bundle deployed into a target's deployment
# project by the SMUS CI/CD CLI, the deploy job of each promotion leg.
#
#   run:      ./scripts/deploy-application.py <account> --manifest <manifest.yaml> --bundle <app>.zip
#                 --sha256 <hex> --tag vX.Y.Z --image-uri <uri> [--log <file>] [--dotenv <file>]
#             ./scripts/deploy-application.py <account> --check     # the project, its values and the
#                                                                   # caller's membership; no deploy
#             ./scripts/deploy-application.py --self-check          # examples/app-etl's manifest
#                                                                   # against this script, offline:
#                                                                   # what `make check` runs
#   reads:    DOMAIN_ID and DOMAIN_REGION from the environment, the names the template's pipeline
#             defines; the bundle, already downloaded by the runner's own role (Stage 8 decision 20);
#             the deployment project and its Tooling environment, from DataZone; sagemaker/'s state
#             for the training image. Nothing with --self-check.
#   writes:   what the CLI's `deploy` writes: the bundle's files under the project's shared prefix,
#             the bundle's catalog into the project, the stage's workflows, and the run its bootstrap
#             starts; then the SSM parameter /awsds/<env>/applications/<app>/stage-variables, the
#             stage's variables as the deploy filled them. With --dotenv, the project's id and shared
#             prefix for the leg's later jobs.
#   exit:     0 deployed and read back | 1 a check failed | 2 usage
#
# Run as the account's deploy role, an owner of the project (by hand, its infrastructure profile).
# The order is the step's: the bundle's SHA256 against the value the tag pipeline passed down,
# before a file of it is read; the project's values and the caller's membership, before anything is
# written; the bundle extracted beside the tag's manifest, since the CLI 1.0.9 copies a storage item
# from the manifest's folder and reads the catalog from the archive (SUP-286); every `${VAR}` of the
# manifest exported, the target stage's from the project and the other stages' as a placeholder,
# since the CLI refuses a manifest with one unset whatever the target (SUP-282).
#
# The CLI's exit status is not the whole verdict, so the log is read too: the workflows' network
# named from the Tooling environment (without the line they run in the service's own, SUP-285); the
# catalog import's `Failed:` count at zero, since the import fails only when every item fails
# (SUP-357); and each workflow the stage's bootstrap creates found by its name.
#
# The stage's variables are recorded last. The CLI writes each `{env.VAR}` of a workflow into the
# deployed definition as a parameter and fills it on a run it starts; a chain's machine fills it from
# this record (terraform-modules/orchestration), so the record is what the last deploy ran with.

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import yaml
from tfhygiene import backend
from tfhygiene.projects import (
    DEPLOYMENT_PROJECT,
    STAGE,
    STAGE_PREFIX,
    ProjectError,
    aws_json,
    is_member,
    project_values,
    stage_variables_parameter,
    workflow_name,
)
from tfhygiene.states import StateError, state_outputs

REPO = Path(__file__).resolve().parents[1]
CLI = "aws-smus-cicd-cli"
CATALOG_EXPORT = "catalog/catalog_export.json"

# The CLI's own pattern for a manifest variable (helpers/utils.py, 1.0.9): ${NAME} or ${NAME:default}.
MANIFEST_VARIABLE = re.compile(r"\$\{([^${}:]+)(?::([^${}]*))?\}")
WORKFLOW_VARIABLE = re.compile(r"\{env\.([A-Za-z0-9_]+)\}")

# The log lines the verdict reads.
NETWORK_LINE = "Tooling VPC config"
IMPORT_HEADER = "Catalog import completed"
IMPORT_FAILED = re.compile(r"^\s*Failed:\s*(\d+)\s*$", re.MULTILINE)

PLACEHOLDER = "unused-by-this-stage"


class DeployError(Exception):
    pass


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unpack(bundle: Path, into: Path) -> list:
    """The bundle's files, refusing a member that would land outside `into`."""
    names = []
    with zipfile.ZipFile(bundle) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            target = (into / info.filename).resolve()
            if into.resolve() not in target.parents:
                raise DeployError(f"{info.filename}: outside the bundle's tree")
            names.append(info.filename)
        z.extractall(into)
    return sorted(names)


def variables_in(node) -> set:
    """Every ${NAME} a manifest subtree names, a name with a default included."""
    if isinstance(node, dict):
        return set().union(*[variables_in(v) for v in node.values()]) if node else set()
    if isinstance(node, list):
        return set().union(*[variables_in(v) for v in node]) if node else set()
    if isinstance(node, str):
        return {m.group(1) for m in MANIFEST_VARIABLE.finditer(node)}
    return set()


def substitute(value: str, env: dict) -> str:
    """A manifest value as the CLI resolves it: each ${NAME} from `env`, or its default."""

    def resolve(match: re.Match) -> str:
        name, default = match.group(1), match.group(2)
        if env.get(name):
            return env[name]
        if default is not None:
            return default
        raise DeployError(f"${{{name}}}: unset, and the manifest gives it no default")

    return MANIFEST_VARIABLE.sub(resolve, value)


def stage_exports(account: str, project: dict, image_uri: str, training_image_uri: str) -> dict:
    """The `${VAR}` names this script fills for the account's stage, from the project itself."""
    prefix = STAGE_PREFIX[account]
    return {
        f"{prefix}_SUBNET_AZ1": project["subnets"][0],
        f"{prefix}_SUBNET_AZ2": project["subnets"][1],
        f"{prefix}_PROJECT_SG": project["security_group"],
        f"{prefix}_PROJECT_KEY_ARN": project["key_arn"],
        f"{prefix}_ACCOUNT_ID": project["account_id"],
        "JOB_IMAGE_URI": image_uri,
        "TRAINING_IMAGE_URI": training_image_uri,
    }


def deploy_environment(manifest: dict, stage: str, exports: dict, base: dict) -> dict:
    """The environment the CLI runs in: `base`, the stage's exports over it, and a placeholder for
    every name another stage alone reads. A name the target stage reads and nothing fills fails."""
    env = dict(base)
    env.update(exports)
    stages = manifest.get("stages") or {}
    if stage not in stages:
        raise DeployError(f"the manifest has no stage {stage}: {', '.join(stages)}")
    needed = variables_in(stages[stage])
    unset = sorted(name for name in needed if not env.get(name))
    if unset:
        raise DeployError(
            f"the stage {stage} reads {', '.join(unset)}, which neither the environment nor the "
            "project fills"
        )
    for name in sorted(variables_in(manifest) - needed):
        if not env.get(name):
            env[name] = PLACEHOLDER
    return env


def stage_variables(manifest: dict, stage: str, env: dict) -> dict:
    """The stage's environment_variables as the deploy filled them, every value a string."""
    declared = (manifest["stages"][stage].get("environment_variables")) or {}
    return {name: substitute(str(value), env) for name, value in declared.items()}


def created_workflows(manifest: dict, stage: str) -> list:
    """The workflows the stage's bootstrap creates, by the manifest's name; an action that names
    none creates every workflow of content.workflows."""
    actions = ((manifest["stages"][stage].get("bootstrap")) or {}).get("actions") or []
    every = [w["workflowName"] for w in (manifest.get("content") or {}).get("workflows") or []]
    names = []
    for action in actions:
        if action.get("type") != "workflow.create":
            continue
        for name in [action["workflowName"]] if action.get("workflowName") else every:
            if name not in names:
                names.append(name)
    return names


def read_log(log: str, carries_catalog: bool) -> list:
    """What the deploy's log says beyond the exit status: the problems, none when it reads clean."""
    problems = []
    if NETWORK_LINE not in log:
        problems.append(
            f'no "{NETWORK_LINE}" line: the workflows carry no network from the Tooling environment'
        )
    if carries_catalog:
        if IMPORT_HEADER not in log:
            problems.append("the bundle carries a catalog and the log reports no import of it")
        else:
            counts = IMPORT_FAILED.findall(log[log.index(IMPORT_HEADER) :])
            if not counts:
                problems.append("the catalog import's summary carries no Failed: count")
            elif int(counts[0]) != 0:
                problems.append(f"the catalog import failed {counts[0]} item(s)")
    return problems


def list_workflows(region: str) -> dict:
    """Every workflow of the account, name to (ARN, status)."""
    found, token = {}, None
    while True:
        args = ["mwaa-serverless", "list-workflows", "--region", region, "--max-results", "100"]
        if token:
            args += ["--next-token", token]
        page = aws_json(*args)
        for w in page.get("Workflows", []):
            found[w.get("Name")] = (w["WorkflowArn"], w.get("WorkflowStatus"))
        token = page.get("NextToken")
        if not token:
            return found


def record_stage_variables(env_token: str, app: str, region: str, variables: dict) -> str:
    """The stage's variables written to their parameter and read back."""
    name = stage_variables_parameter(env_token, app)
    value = json.dumps(variables, sort_keys=True)
    aws_json(
        "ssm",
        "put-parameter",
        "--name",
        name,
        "--type",
        "String",
        "--overwrite",
        "--value",
        value,
        "--region",
        region,
    )
    back = aws_json("ssm", "get-parameter", "--name", name, "--region", region)
    if json.loads(back["Parameter"]["Value"]) != variables:
        raise DeployError(f"{name} reads back differently from what was written")
    return name


def domain_from_environment() -> tuple:
    domain, region = os.environ.get("DOMAIN_ID"), os.environ.get("DOMAIN_REGION")
    if not domain or not region:
        raise DeployError(
            "DOMAIN_ID and DOMAIN_REGION are read from the environment, and one is unset"
        )
    if region != backend.REGION:
        raise DeployError(f"DOMAIN_REGION is {region}; this estate deploys in {backend.REGION}")
    return domain, region


def describe(account: str, project: dict, member: bool) -> None:
    print(f"== the deployment project of {account}")
    print(
        f"   {project['project_name']} ({project['project_id']}), role {project['role_arn'].rsplit('/', 1)[-1]}"
    )
    print(f"   subnets {', '.join(project['subnets'])}, security group {project['security_group']}")
    print(f"   key {project['key_arn'].rsplit('/', 1)[-1]}, shared prefix {project['shared_uri']}")
    print(f"   the caller is {'a member' if member else 'NOT a member'} of the project")


def membership_error(account: str, project: dict) -> DeployError:
    return DeployError(
        f"the caller is no member of {project['project_name']}: DataZone refuses it the project's "
        "connections, where the CLI's deploy stops. Its group profile exists since this call; an "
        "owner of the project adds it as PROJECT_OWNER by group id (datazone "
        "create-project-membership, as the account's infrastructure profile), the id read from the "
        "domain's account (search-group-profiles, the profile whose rolePrincipalArn is the role)"
    )


def check(account: str) -> int:
    domain, region = domain_from_environment()
    project = project_values(account, domain, region)
    member = is_member(domain, region, project["project_id"])
    describe(account, project, member)
    if not member:
        raise membership_error(account, project)
    return 0


def deploy(args: argparse.Namespace) -> int:
    if sha256_hex(args.bundle) != args.sha256:
        raise DeployError(f"{args.bundle}: its SHA256 is not the one the release recorded")
    domain, region = domain_from_environment()
    manifest_text = args.manifest.read_text(encoding="utf-8")
    manifest = yaml.safe_load(manifest_text)
    app = manifest["applicationName"]
    stage = STAGE[args.account]
    env_token = backend.ENV_TOKENS[args.account]

    project = project_values(args.account, domain, region)
    member = is_member(domain, region, project["project_id"])
    describe(args.account, project, member)
    if not member:
        raise membership_error(args.account, project)
    if manifest["stages"].get(stage, {}).get("project", {}).get("name") != project["project_name"]:
        raise DeployError(
            f"the manifest's stage {stage} names another project than {project['project_name']}"
        )

    training_image_uri = state_outputs(args.account, "sagemaker").get("training_image_uri")
    if not training_image_uri:
        raise DeployError(f"{args.account}/sagemaker outputs no training_image_uri")
    exports = stage_exports(args.account, project, args.image_uri, training_image_uri)
    env = deploy_environment(manifest, stage, exports, dict(os.environ))
    variables = stage_variables(manifest, stage, env)
    expected = [
        workflow_name(app, project["project_name"], w) for w in created_workflows(manifest, stage)
    ]

    cli = shutil.which(CLI)
    if not cli:
        raise DeployError(f"{CLI} is not on PATH: the deploy image carries it")
    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp)
        names = unpack(args.bundle, tree)
        (tree / "manifest.yaml").write_text(manifest_text, encoding="utf-8")
        carries_catalog = CATALOG_EXPORT in names
        catalog = "a catalog export" if carries_catalog else "no catalog export"
        print(f"== the bundle of {args.tag}: {len(names)} file(s), {catalog}")
        command = [
            cli,
            "deploy",
            "--manifest",
            "manifest.yaml",
            "--targets",
            stage,
            "--bundle-archive-path",
            str(args.bundle.resolve()),
            "--skip-validation",
            "--no-events",
        ]
        print(f"== {' '.join(command[1:])}", flush=True)
        res = subprocess.run(command, cwd=tree, env=env, capture_output=True, text=True)
    log = res.stdout + res.stderr
    if args.log:
        args.log.write_text(log, encoding="utf-8")
    sys.stdout.write(log)
    sys.stdout.flush()
    if res.returncode != 0:
        raise DeployError(f"the CLI's deploy exited {res.returncode}")
    problems = read_log(log, carries_catalog)

    deployed = list_workflows(region)
    for name in expected:
        if name not in deployed:
            problems.append(f"no workflow named {name} after the deploy")
        elif deployed[name][1] not in (None, "READY"):
            problems.append(f"the workflow {name} is {deployed[name][1]}")
    if problems:
        raise DeployError("; ".join(problems))
    print(f"== the workflows: {', '.join(expected)}")

    parameter = record_stage_variables(env_token, app, region, variables)
    print(f"== the stage's variables recorded in {parameter}: {', '.join(sorted(variables))}")
    if args.dotenv:
        prefix = STAGE_PREFIX[args.account]
        args.dotenv.write_text(
            f"{prefix}_PROJECT_ID={project['project_id']}\n{prefix}_SHARED_URI={project['shared_uri']}\n",
            encoding="utf-8",
        )
    return 0


def self_check() -> int:
    """examples/app-etl's manifest against this script, with a stand-in project: every name a target
    stage reads is one this script or the pipeline fills, every `{env.VAR}` of a workflow is a
    variable of every stage, and the log's readings hold on sample text."""
    app_dir = REPO / "examples" / "app-etl"
    manifest = yaml.safe_load((app_dir / "manifest.yaml").read_text(encoding="utf-8"))
    app = manifest["applicationName"]
    project = {
        "account_id": "account",
        "subnets": ["subnet-stand-in-1", "subnet-stand-in-2"],
        "security_group": "sg-stand-in",
        "key_arn": "arn:aws:kms:region:account:key/stand-in",
    }
    pipeline = {"DOMAIN_ID": "dzd-standin", "DOMAIN_REGION": backend.REGION}
    workflow_variables = set()
    for path in sorted((app_dir / "workflows").glob("*.yaml")):
        workflow_variables |= set(WORKFLOW_VARIABLE.findall(path.read_text(encoding="utf-8")))
    fail = 0
    for account, stage in STAGE.items():
        exports = stage_exports(account, project, "registry.example/app@sha256:" + "0" * 64, "x")
        try:
            env = deploy_environment(manifest, stage, exports, pipeline)
            variables = stage_variables(manifest, stage, env)
        except DeployError as e:
            print(f"  FAIL  {stage}: {e}")
            fail = 1
            continue
        problems = []
        if manifest["stages"][stage]["project"]["name"] != DEPLOYMENT_PROJECT[account]:
            problems.append(f"its project is not {DEPLOYMENT_PROJECT[account]}")
        missing = sorted(workflow_variables - set(variables))
        if missing:
            problems.append(f"no stage variable for {', '.join(missing)}")
        placeholders = sorted(k for k, v in variables.items() if v == PLACEHOLDER)
        if placeholders:
            problems.append(f"{', '.join(placeholders)} left to a placeholder")
        if len(json.dumps(variables).encode()) > 4096:
            problems.append("its variables exceed a standard SSM parameter's 4,096 bytes")
        created = created_workflows(manifest, stage)
        if not created:
            problems.append("its bootstrap creates no workflow")
        for problem in problems:
            print(f"  FAIL  {stage}: {problem}")
        if problems:
            fail = 1
        else:
            names = ", ".join(workflow_name(app, DEPLOYMENT_PROJECT[account], w) for w in created)
            print(f"  ok    {stage}: {len(variables)} variable(s); {names}")
    samples = [
        (
            "a clean log",
            f"x {NETWORK_LINE} y\n{IMPORT_HEADER}:\n   Created: 1\n   Failed: 0\n",
            True,
            0,
        ),
        ("a failed import", f"{NETWORK_LINE}\n{IMPORT_HEADER}:\n   Failed: 2\n", True, 1),
        ("no import of a catalog the bundle carries", f"{NETWORK_LINE}\n", True, 1),
        ("no network line", f"{IMPORT_HEADER}:\n   Failed: 0\n", True, 1),
        ("no catalog in the bundle", f"{NETWORK_LINE}\n", False, 0),
    ]
    for label, log, carries, expected in samples:
        got = len(read_log(log, carries))
        if got != expected:
            print(f"  FAIL  the log's reading of {label}: {got} problem(s), {expected} expected")
            fail = 1
    if (
        workflow_name("app-etl", "deploy-staging", "app-etl-train")
        != "app_etl_deploy_staging_app_etl_train"
    ):
        print("  FAIL  the workflow's composed name")
        fail = 1
    print()
    print("OK" if fail == 0 else "FAILED")
    return fail


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="Deploy a release's bundle into a target's project.")
    ap.add_argument("account", nargs="?", choices=sorted(DEPLOYMENT_PROJECT))
    ap.add_argument("--manifest", type=Path)
    ap.add_argument("--bundle", type=Path)
    ap.add_argument("--sha256")
    ap.add_argument("--tag")
    ap.add_argument("--image-uri")
    ap.add_argument("--log", type=Path)
    ap.add_argument("--dotenv", type=Path)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--self-check", action="store_true")
    args = ap.parse_args(argv)

    if args.self_check:
        return self_check()
    if not args.account:
        ap.error("<account> is required without --self-check")
    try:
        if args.check:
            return check(args.account)
        if not (args.manifest and args.bundle and args.sha256 and args.tag and args.image_uri):
            ap.error("--manifest, --bundle, --sha256, --tag and --image-uri are required to deploy")
        if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
            ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
        if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
            ap.error("--sha256 is 64 lowercase hex characters")
        return deploy(args)
    except (
        OSError,
        DeployError,
        ProjectError,
        StateError,
        zipfile.BadZipFile,
        yaml.YAMLError,
    ) as e:
        print(f"deploy-application: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
