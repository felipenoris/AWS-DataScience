#!/usr/bin/env -S uv run --quiet
# model-chain.py - Stage 10 steps 5.2 and 5.4: the model app-etl-train trains, registered, approved
# and served by a batch transform, the jobs of the promotion pipeline (examples/app-etl/.gitlab-ci.yml);
# and Stage 17 pass 9: the approval of the version another application's task proposed, found by the
# release's model hash (examples/app-ml/.gitlab-ci.yml).
#
#   run:      ./scripts/model-chain.py register --tag vX.Y.Z [--dotenv <file>] --project
#                 # Production: the newest completed app-etl-train job, PendingManualApproval
#             ./scripts/model-chain.py approve --package-arn <arn> --approver <login>
#                 # app-etl's version, by its ARN
#             ./scripts/model-chain.py approve staging|production --application <app>
#                 --sha256 <hex> --approver <login>
#                 # the one version of the account's group for <app> whose description carries
#                 # the release's model hash, PendingManualApproval or already Approved
#             ./scripts/model-chain.py transform staging --tag vX.Y.Z --project
#                 # Staging's own model, retrained there (Stage 10 decision 22)
#             ./scripts/model-chain.py transform production --tag vX.Y.Z --package-arn <arn> --project
#                 # the approved version, by its package
#             ./scripts/model-chain.py --check
#                 # the requests built from stand-in values, offline: what `make check` runs
#   reads:    the account's sagemaker/ state object and, in Staging, foundation/'s (tfhygiene.targets);
#             the account's deployment project and its Tooling environment (tfhygiene.projects),
#             DOMAIN_ID and DOMAIN_REGION from the environment; the training jobs app-etl-train-*; the
#             evaluation the workflow's evaluate task wrote beside the model; the transform's output;
#             in Staging, Production's newest approved version of the application's registry group,
#             before Staging's own model is served (Stage 9 4.6, INT-07's registry half, verification
#             xii); for an approval by hash, the versions of the group the account's sagemaker/ state
#             names for the application. Nothing with --check.
#   writes:   register, a version of awsds-prod-model-app-etl; approve, the status of the version it
#             names or finds; transform, a model it deletes after and a transform job's output under
#             the models' prefix, transform/<job>/.
#   exit:     0 done | 1 a check failed | 2 usage
#
# Run as the account's deploy role, the deploy runner's profile for it; by hand, the account's
# infrastructure profile. The registration names the evaluation as the version's ModelMetrics and the
# tag, the training job and its validation RMSE in CustomerMetadataProperties (D28 item 6). The
# transform runs the model on the batch input the Glue job wrote, in private subnets with network
# isolation and a customer managed key on its volume and output, the settings the Workloads OU's
# document refuses a request without (Stage 9 3.5); it fails unless every input row comes back as one
# number. The aws CLI is the one dependency, as in the repository's other scripts.
#
# The model lives where the CI/CD CLI's release trains it (Stage 19 step 4.9): the deployment
# project's role writes it under the project's shared prefix, app-etl/models/, with the project key,
# and the transform runs as that role in the project's subnets and security group. --project names
# that layout and is required: the outputs bucket's layout retired with release T's path (Stage 19
# item 31).

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from tfhygiene.projects import ProjectError, project_values
from tfhygiene.states import StateError, state_outputs
from tfhygiene.targets import TargetError, account_values

APP = "app-etl"
TRAINING_PREFIX = f"{APP}-train-"
INSTANCE_TYPE = "ml.m5.large"
POLL_SECONDS = 30
TRANSFORM_BOUND_SECONDS = 2_700


class ChainError(Exception):
    pass


def aws_json(*args: str) -> dict:
    res = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    if res.returncode != 0:
        raise ChainError(f"aws {' '.join(args[:2])}: {res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def aws_with_input(command: list[str], request: dict) -> dict:
    """One aws call whose request is a JSON document, passed through --cli-input-json."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(request, f)
    try:
        return aws_json(*command, "--cli-input-json", f"file://{f.name}")
    finally:
        Path(f.name).unlink()


def read_text(uri: str) -> str:
    res = subprocess.run(
        ["aws", "s3", "cp", uri, "-", "--only-show-errors"], capture_output=True, text=True
    )
    if res.returncode != 0:
        raise ChainError(f"{uri}: {res.stderr.strip() or 'unreadable'}")
    return res.stdout


def run_name(tag: str, now: datetime | None = None) -> str:
    """`app-etl-<tag>-<UTC stamp>`, a model's and a transform job's name, within SageMaker's 63."""
    stamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%dT%H%M%S")
    return f"{APP}-{tag.replace('.', '-')}-{stamp}"


def newest_training_job() -> dict:
    """The newest completed training job of app-etl-train in the account, described."""
    listed = aws_json(
        "sagemaker",
        "list-training-jobs",
        "--name-contains",
        TRAINING_PREFIX,
        "--status-equals",
        "Completed",
        "--sort-by",
        "CreationTime",
        "--sort-order",
        "Descending",
        "--max-results",
        "1",
    ).get("TrainingJobSummaries", [])
    if not listed:
        raise ChainError(f"no completed training job named {TRAINING_PREFIX}* in the account")
    name = listed[0]["TrainingJobName"]
    return aws_json("sagemaker", "describe-training-job", "--training-job-name", name)


def project_layout(values: dict, project: dict) -> dict:
    """Where a CLI-deployed release keeps the model, and what serves it: the deployment project's
    shared prefix, its key, its role and its network."""
    shared = project["shared_uri"]
    return {
        **values,
        "models_uri": f"{shared}{APP}/models/",
        "batch_uri": f"{shared}{APP}/work/train/batch/",
        "key_arn": project["key_arn"],
        "role_arn": project["role_arn"],
        "security_group": project["security_group"],
        "subnets": project["subnets"],
    }


def target_values(account: str, project: bool) -> dict:
    if not project:
        raise ChainError(
            "--project is required: the outputs bucket's layout retired (Stage 19 item 31)"
        )
    values = account_values(account)
    domain, region = os.environ.get("DOMAIN_ID"), os.environ.get("DOMAIN_REGION")
    if not domain or not region:
        raise ChainError("--project reads DOMAIN_ID and DOMAIN_REGION from the environment")
    return project_layout(values, project_values(account, domain, region))


def evaluation_uri(models_uri: str, job: str) -> str:
    return f"{models_uri}{job}/evaluation.json"


def package_request(
    tag: str, group: str, training: dict, evaluation: dict, models_uri: str
) -> dict:
    """CreateModelPackage: the job's image and model, its evaluation, PendingManualApproval."""
    job = training["TrainingJobName"]
    rmse = evaluation["regression_metrics"]["rmse"]["value"]
    return {
        "ModelPackageGroupName": group,
        "ModelPackageDescription": f"{APP} {tag}, trained by {job}",
        "ModelApprovalStatus": "PendingManualApproval",
        "InferenceSpecification": {
            "Containers": [
                {
                    "Image": training["AlgorithmSpecification"]["TrainingImage"],
                    "ModelDataUrl": training["ModelArtifacts"]["S3ModelArtifacts"],
                }
            ],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"],
            "SupportedTransformInstanceTypes": [INSTANCE_TYPE],
        },
        "ModelMetrics": {
            "ModelQuality": {
                "Statistics": {
                    "ContentType": "application/json",
                    "S3Uri": evaluation_uri(models_uri, job),
                }
            }
        },
        "CustomerMetadataProperties": {
            "git_tag": tag,
            "training_job": job,
            "validation_rmse": str(rmse),
        },
    }


def model_request(name: str, values: dict, container: dict) -> dict:
    """CreateModel in the layout's subnets with network isolation, as the layout's role."""
    request = {
        "ModelName": name,
        "ExecutionRoleArn": values["role_arn"],
        "VpcConfig": {"Subnets": values["subnets"], "SecurityGroupIds": [values["security_group"]]},
        "EnableNetworkIsolation": True,
    }
    if "ModelPackageName" in container:
        request["Containers"] = [container]
    else:
        request["PrimaryContainer"] = container
    return request


def transform_request(name: str, values: dict) -> dict:
    """CreateTransformJob over the batch input, the layout's key on its volume and output."""
    return {
        "TransformJobName": name,
        "ModelName": name,
        "TransformInput": {
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": values["batch_uri"],
                }
            },
            "ContentType": "text/csv",
            "SplitType": "Line",
        },
        "TransformOutput": {
            "S3OutputPath": f"{values['models_uri']}transform/{name}/",
            "AssembleWith": "Line",
            "KmsKeyId": values["key_arn"],
        },
        "TransformResources": {
            "InstanceType": INSTANCE_TYPE,
            "InstanceCount": 1,
            "VolumeKmsKeyId": values["key_arn"],
        },
    }


def predictions(text: str, expected: int) -> int:
    """The transform's output: one number per input row, or the check fails."""
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != expected:
        raise ChainError(f"{len(lines)} prediction(s) for {expected} input row(s)")
    for number, line in enumerate(lines, start=1):
        try:
            float(line)
        except ValueError as e:
            raise ChainError(f"prediction {number} is not a number") from e
    return len(lines)


def register(args) -> int:
    values = target_values("production", args.project)
    group_arn = values["model_package_group_arns"].get(APP)
    if not group_arn:
        raise ChainError(f"sagemaker/'s state names no model package group for {APP}")
    group = group_arn.rsplit("/", 1)[-1]
    training = newest_training_job()
    job = training["TrainingJobName"]
    evaluation = json.loads(read_text(evaluation_uri(values["models_uri"], job)))
    request = package_request(args.tag, group, training, evaluation, values["models_uri"])
    arn = aws_with_input(["sagemaker", "create-model-package"], request)["ModelPackageArn"]
    print(f"registered {arn} from {job}, PendingManualApproval")
    if args.dotenv:
        args.dotenv.write_text(f"MODEL_PACKAGE_ARN={arn}\n", encoding="utf-8")
    return 0


def hash_mark(sha256: str) -> str:
    """How a version's description carries its archive's SHA-256: examples/app-ml's register task
    writes `app-ml sha256:<hex>, trained by <job>`."""
    return f"sha256:{sha256}"


def versions_with_hash(summaries: list, sha256: str) -> list:
    """The version summaries whose description carries the hash."""
    mark = hash_mark(sha256)
    return [s for s in summaries if mark in (s.get("ModelPackageDescription") or "")]


def release_version(account: str, application: str, sha256: str) -> str:
    """The ARN of the one version whose description carries the hash, in the account's group for
    the application, which its sagemaker/ state names; any other count fails."""
    groups = state_outputs(account, "sagemaker").get("model_package_group_arns") or {}
    group = groups.get(application)
    if not group:
        raise ChainError(f"{account}/sagemaker names no model package group for {application}")
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
    """app-etl's version by its ARN, or the release's version by its model hash, approved and read
    back Approved; the release's version left as it is once Approved."""
    if args.package_arn:
        arn, where = args.package_arn, "the promotion pipeline's manual job"
    else:
        arn, where = pending_release_version(args), f"the promotion pipeline's {args.account} leg"
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
        f"approved by {args.approver} at {where}",
    )
    status = aws_json("sagemaker", "describe-model-package", "--model-package-name", arn)[
        "ModelApprovalStatus"
    ]
    print(f"{arn}: {status}")
    if status != "Approved":
        raise ChainError(f"the version reads {status} after the update")
    return 0


def wait_for_transform(name: str) -> str:
    """The transform job's final status, polled; stopped past its bound."""
    deadline = time.monotonic() + TRANSFORM_BOUND_SECONDS
    while True:
        time.sleep(POLL_SECONDS)
        job = aws_json("sagemaker", "describe-transform-job", "--transform-job-name", name)
        status = job["TransformJobStatus"]
        print(f"  {datetime.now(timezone.utc).strftime('%H:%M:%S')} {name} {status}")
        if status in ("Completed", "Failed", "Stopped"):
            if status != "Completed":
                print(f"  {job.get('FailureReason', '')}")
            return status
        if time.monotonic() > deadline:
            aws_json("sagemaker", "stop-transform-job", "--transform-job-name", name)
            raise ChainError(f"{name} still {status} after {TRANSFORM_BOUND_SECONDS} s: stopped")


def read_production_registry(values: dict) -> None:
    """Stage 9 4.6, INT-07's registry half: the Staging deploy role reads Production's newest approved
    version of the application's group before Staging serves its own model (Stage 10 decision 22). A
    group with no approved version is reported; a refusal fails the job."""
    prefix = values.get("registry_group_arn_prefix")
    if not prefix:
        raise ChainError("foundation/'s state names no registry group prefix (Stage 9 4.6)")
    group_arn = f"{prefix}{APP}"
    listed = aws_json(
        "sagemaker",
        "list-model-packages",
        "--model-package-group-name",
        group_arn,
        "--model-approval-status",
        "Approved",
        "--sort-by",
        "CreationTime",
        "--sort-order",
        "Descending",
        "--max-results",
        "1",
    ).get("ModelPackageSummaryList", [])
    if not listed:
        print(f"  Production's registry: no approved version in {group_arn}")
        return
    package = aws_json(
        "sagemaker", "describe-model-package", "--model-package-name", listed[0]["ModelPackageArn"]
    )
    metadata = package.get("CustomerMetadataProperties", {})
    print(
        f"  Production's registry: version {package.get('ModelPackageVersion')} of {group_arn} is "
        f"{package['ModelApprovalStatus']}, {metadata.get('git_tag', '?')} trained by "
        f"{metadata.get('training_job', '?')}"
    )


def transform(args) -> int:
    values = target_values(args.account, args.project)
    if args.account == "production":
        if not args.package_arn:
            raise ChainError("transform production serves the approved version: --package-arn")
        package = aws_json(
            "sagemaker", "describe-model-package", "--model-package-name", args.package_arn
        )
        if package["ModelApprovalStatus"] != "Approved":
            raise ChainError(
                f"{args.package_arn} is {package['ModelApprovalStatus']}, not Approved"
            )
        job = package["CustomerMetadataProperties"]["training_job"]
        container = {"ModelPackageName": args.package_arn}
    else:
        read_production_registry(values)
        training = newest_training_job()
        job = training["TrainingJobName"]
        container = {
            "Image": training["AlgorithmSpecification"]["TrainingImage"],
            "ModelDataUrl": training["ModelArtifacts"]["S3ModelArtifacts"],
        }
    evaluation = json.loads(read_text(evaluation_uri(values["models_uri"], job)))
    expected = evaluation["awsds"]["batch_rows"]
    name = run_name(args.tag)
    print(f"== {name}: the model of {job} on {expected} batch row(s)")
    aws_with_input(["sagemaker", "create-model"], model_request(name, values, container))
    try:
        aws_with_input(["sagemaker", "create-transform-job"], transform_request(name, values))
        status = wait_for_transform(name)
        if status != "Completed":
            raise ChainError(f"{name} ended {status}")
        out = transform_request(name, values)["TransformOutput"]["S3OutputPath"] + "batch.csv.out"
        count = predictions(read_text(out), expected)
        print(f"  {count} prediction(s), one per input row, at {out}")
    finally:
        aws_json("sagemaker", "delete-model", "--model-name", name)
        print(f"  deleted the model {name}")
    return 0


def check() -> int:
    """The requests built from stand-in values, and the invariants the Workloads OU's document and
    the registry need, offline."""
    account = {
        "registry_group_arn_prefix": "arn:aws:sagemaker:region:account:model-package-group/awsds-prod-model-",
    }
    project = {
        "shared_uri": "s3://awsds-staging-smus-projects/domain/project/shared/",
        "key_arn": "arn:aws:kms:region:account:key/project-stand-in",
        "role_arn": "arn:aws:iam::account:role/datazone_usr_role_project_environment",
        "security_group": "sg-project-stand-in",
        "subnets": ["subnet-project-1", "subnet-project-2"],
    }
    values = project_layout(account, project)
    shared = project["shared_uri"]
    training = {
        "TrainingJobName": "app-etl-train-20261024T120000",
        "AlgorithmSpecification": {"TrainingImage": "registry.example/sagemaker-xgboost@sha256:1"},
        "ModelArtifacts": {"S3ModelArtifacts": f"{shared}{APP}/models/x/output/model.tar.gz"},
    }
    evaluation = {"regression_metrics": {"rmse": {"value": 1.5}}, "awsds": {"batch_rows": 3}}
    problems = []
    name = run_name("v10.20.30", datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc))
    if len(name) > 63 or not re.fullmatch(r"[a-zA-Z0-9](-*[a-zA-Z0-9])*", name):
        problems.append(f"the run name {name!r} is not a SageMaker name")
    package = package_request(
        "v0.4.0", "awsds-prod-model-app-etl", training, evaluation, values["models_uri"]
    )
    if package["ModelApprovalStatus"] != "PendingManualApproval":
        problems.append("the registration is not PendingManualApproval")
    if not package["ModelMetrics"]["ModelQuality"]["Statistics"]["S3Uri"].endswith(
        "/evaluation.json"
    ):
        problems.append("the version's metrics name no evaluation")
    for container in ({"ModelPackageName": "arn:stand-in"}, {"Image": "i", "ModelDataUrl": "m"}):
        model = model_request(name, values, container)
        if model.get("EnableNetworkIsolation") is not True or not model["VpcConfig"]["Subnets"]:
            problems.append("a model without network isolation or subnets")
    job = transform_request(name, values)
    if not job["TransformResources"].get("VolumeKmsKeyId") or not job["TransformOutput"].get(
        "KmsKeyId"
    ):
        problems.append("a transform without a key on its volume and output")
    if job["TransformResources"]["InstanceType"] != INSTANCE_TYPE:
        problems.append("a transform off the instance type its quota covers")
    served = model_request(name, values, {"Image": "i", "ModelDataUrl": "m"})
    moved = transform_request(name, values)
    if served["ExecutionRoleArn"] != project["role_arn"]:
        problems.append("a project's model not served as the project's role")
    if served["VpcConfig"] != {
        "Subnets": project["subnets"],
        "SecurityGroupIds": [project["security_group"]],
    }:
        problems.append("a project's model off the project's subnets or security group")
    if (
        moved["TransformInput"]["DataSource"]["S3DataSource"]["S3Uri"]
        != f"{shared}{APP}/work/train/batch/"
    ):
        problems.append("a project's transform reads no batch under the shared prefix")
    if not moved["TransformOutput"]["S3OutputPath"].startswith(f"{shared}{APP}/models/transform/"):
        problems.append("a project's transform writes outside the shared prefix's models")
    if {moved["TransformOutput"]["KmsKeyId"], moved["TransformResources"]["VolumeKmsKeyId"]} != {
        project["key_arn"]
    }:
        problems.append("a project's transform off the project key")
    if evaluation_uri(values["models_uri"], "j") != f"{shared}{APP}/models/j/evaluation.json":
        problems.append("a project's evaluation is not beside the model the workflow wrote")
    group_arn = f"{values['registry_group_arn_prefix']}{APP}"
    if not re.fullmatch(
        r"arn:aws:sagemaker:[a-z0-9-]+:[a-z0-9]+:model-package-group/awsds-[a-z]+-model-[a-z0-9-]+",
        group_arn,
    ):
        problems.append(f"the registry group {group_arn!r} is not a group ARN")
    summaries = [
        {"ModelPackageArn": "v1", "ModelPackageDescription": f"app-ml sha256:{'a' * 64}, by j"},
        {"ModelPackageArn": "v2", "ModelPackageDescription": "app-etl v0.4.0, trained by j"},
        {"ModelPackageArn": "v3"},
    ]
    if [s["ModelPackageArn"] for s in versions_with_hash(summaries, "a" * 64)] != ["v1"]:
        problems.append("the release's version is not found by its hash")
    if versions_with_hash(summaries, "b" * 64):
        problems.append("a version found for a hash no description carries")
    try:
        predictions("1.5\n2.5\n", 3)
        problems.append("a short output passed the check")
    except ChainError:
        pass
    for problem in problems:
        print(f"  FAIL  {problem}")
    print(f"  {'ok' if not problems else 'FAILED'}    the model chain's requests, offline")
    print()
    print("OK" if not problems else "FAILED")
    return 1 if problems else 0


def main(argv: list) -> int:
    if argv == ["--check"]:
        return check()
    ap = argparse.ArgumentParser(
        description="Register, approve and serve app-etl's model; approve another application's."
    )
    commands = ap.add_subparsers(dest="command", required=True)
    r = commands.add_parser("register")
    r.add_argument("--tag", required=True)
    r.add_argument("--dotenv", type=Path)
    r.add_argument("--project", action="store_true")
    a = commands.add_parser("approve")
    a.add_argument("account", nargs="?", choices=["staging", "production"])
    a.add_argument("--package-arn")
    a.add_argument("--application")
    a.add_argument("--sha256")
    a.add_argument("--approver", required=True)
    t = commands.add_parser("transform")
    t.add_argument("account", choices=["staging", "production"])
    t.add_argument("--tag", required=True)
    t.add_argument("--package-arn")
    t.add_argument("--project", action="store_true")
    args = ap.parse_args(argv)
    if getattr(args, "tag", None) and not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
    if args.command == "approve":
        by_hash = (args.account, args.application, args.sha256)
        if (args.package_arn and any(by_hash)) or (not args.package_arn and not all(by_hash)):
            ap.error("approve takes --package-arn, or an account with --application and --sha256")
        if args.sha256 and not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
            ap.error("--sha256 is 64 lowercase hex characters")
        if args.application and not re.fullmatch(r"app-[a-z0-9-]+", args.application):
            ap.error("--application is an application's name, app-<name>")
    try:
        return {"register": register, "approve": approve, "transform": transform}[args.command](
            args
        )
    except (ChainError, ProjectError, StateError, TargetError, KeyError) as e:
        print(f"model-chain: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
