#!/usr/bin/env -S uv run --quiet
# model-chain.py - Stage 10 steps 5.2 and 5.4: the model app-etl-train trains, registered, approved
# and served by a batch transform, the jobs of the promotion pipeline (examples/app-etl/.gitlab-ci.yml).
#
#   run:      ./scripts/model-chain.py register --tag vX.Y.Z [--dotenv <file>]
#                 # Production: the newest completed app-etl-train job, PendingManualApproval
#             ./scripts/model-chain.py approve --package-arn <arn> --approver <login>
#             ./scripts/model-chain.py transform staging --tag vX.Y.Z
#                 # Staging's own model, retrained there (Stage 10 decision 22)
#             ./scripts/model-chain.py transform production --tag vX.Y.Z --package-arn <arn>
#                 # the approved version, by its package
#             ./scripts/model-chain.py --check
#                 # the requests built from stand-in values, offline: what `make check` runs
#   reads:    the account's data/, sagemaker/ and network slices' state objects (tfhygiene.targets);
#             the training jobs app-etl-train-*; the evaluation the workflow's evaluate task wrote
#             beside the model; the transform's output. Nothing with --check.
#   writes:   register, a version of awsds-prod-model-app-etl; approve, its status; transform, a model
#             it deletes after and a transform job's output under models/app-etl/transform/<job>/.
#   exit:     0 done | 1 a check failed | 2 usage
#
# Run as the account's deploy role, the deploy runner's profile for it; by hand, the account's
# infrastructure profile. The registration names the evaluation as the version's ModelMetrics and the
# tag, the training job and its validation RMSE in CustomerMetadataProperties (D28 item 6). The
# transform runs the model on the batch input the Glue job wrote, under the job role, in the job
# subnets with network isolation and the data key on its volume and output, the settings the Workloads
# OU's document refuses a request without (Stage 9 3.5); it fails unless every input row comes back as
# one number. The aws CLI is the one dependency, as in the repository's other scripts.

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from tfhygiene.states import StateError
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


def evaluation_uri(bucket: str, job: str) -> str:
    return f"s3://{bucket}/models/{APP}/{job}/evaluation.json"


def package_request(tag: str, group: str, training: dict, evaluation: dict, bucket: str) -> dict:
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
                    "S3Uri": evaluation_uri(bucket, job),
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
    """CreateModel in the job subnets with network isolation, as the job role."""
    request = {
        "ModelName": name,
        "ExecutionRoleArn": values["job_role_arn"],
        "VpcConfig": {"Subnets": values["subnets"], "SecurityGroupIds": [values["security_group"]]},
        "EnableNetworkIsolation": True,
    }
    if "ModelPackageName" in container:
        request["Containers"] = [container]
    else:
        request["PrimaryContainer"] = container
    return request


def transform_request(name: str, values: dict) -> dict:
    """CreateTransformJob over the batch input, the data key on its volume and output."""
    bucket = values["bucket"]
    return {
        "TransformJobName": name,
        "ModelName": name,
        "TransformInput": {
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": f"s3://{bucket}/{APP}/work/train/batch/",
                }
            },
            "ContentType": "text/csv",
            "SplitType": "Line",
        },
        "TransformOutput": {
            "S3OutputPath": f"s3://{bucket}/models/{APP}/transform/{name}/",
            "AssembleWith": "Line",
            "KmsKeyId": values["data_key_arn"],
        },
        "TransformResources": {
            "InstanceType": INSTANCE_TYPE,
            "InstanceCount": 1,
            "VolumeKmsKeyId": values["data_key_arn"],
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
    values = account_values("production")
    group_arn = values["model_package_group_arns"].get(APP)
    if not group_arn:
        raise ChainError(f"sagemaker/'s state names no model package group for {APP}")
    group = group_arn.rsplit("/", 1)[-1]
    training = newest_training_job()
    job = training["TrainingJobName"]
    evaluation = json.loads(read_text(evaluation_uri(values["bucket"], job)))
    request = package_request(args.tag, group, training, evaluation, values["bucket"])
    arn = aws_with_input(["sagemaker", "create-model-package"], request)["ModelPackageArn"]
    print(f"registered {arn} from {job}, PendingManualApproval")
    if args.dotenv:
        args.dotenv.write_text(f"MODEL_PACKAGE_ARN={arn}\n", encoding="utf-8")
    return 0


def approve(args) -> int:
    aws_json(
        "sagemaker",
        "update-model-package",
        "--model-package-arn",
        args.package_arn,
        "--model-approval-status",
        "Approved",
        "--approval-description",
        f"approved by {args.approver} at the promotion pipeline's manual job",
    )
    status = aws_json(
        "sagemaker", "describe-model-package", "--model-package-name", args.package_arn
    )["ModelApprovalStatus"]
    print(f"{args.package_arn}: {status}")
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


def transform(args) -> int:
    values = account_values(args.account)
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
        training = newest_training_job()
        job = training["TrainingJobName"]
        container = {
            "Image": training["AlgorithmSpecification"]["TrainingImage"],
            "ModelDataUrl": training["ModelArtifacts"]["S3ModelArtifacts"],
        }
    expected = json.loads(read_text(evaluation_uri(values["bucket"], job)))["awsds"]["batch_rows"]
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
    values = {
        "bucket": "awsds-staging-outputs",
        "data_key_arn": "arn:aws:kms:region:account:key/stand-in",
        "job_role_arn": "arn:aws:iam::account:role/awsds-staging-job-exec",
        "security_group": "sg-stand-in",
        "subnets": ["subnet-stand-in-1", "subnet-stand-in-2"],
    }
    training = {
        "TrainingJobName": "app-etl-train-20261024T120000",
        "AlgorithmSpecification": {"TrainingImage": "registry.example/sagemaker-xgboost@sha256:1"},
        "ModelArtifacts": {
            "S3ModelArtifacts": "s3://awsds-staging-outputs/models/app-etl/x/output/model.tar.gz"
        },
    }
    evaluation = {"regression_metrics": {"rmse": {"value": 1.5}}, "awsds": {"batch_rows": 3}}
    problems = []
    name = run_name("v10.20.30", datetime(2026, 10, 24, 12, 0, 0, tzinfo=timezone.utc))
    if len(name) > 63 or not re.fullmatch(r"[a-zA-Z0-9](-*[a-zA-Z0-9])*", name):
        problems.append(f"the run name {name!r} is not a SageMaker name")
    package = package_request(
        "v0.4.0", "awsds-prod-model-app-etl", training, evaluation, values["bucket"]
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
        problems.append("a transform without the data key on its volume and output")
    if job["TransformResources"]["InstanceType"] != INSTANCE_TYPE:
        problems.append("a transform off the instance type its quota covers")
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
    ap = argparse.ArgumentParser(description="Register, approve and serve app-etl's model.")
    commands = ap.add_subparsers(dest="command", required=True)
    r = commands.add_parser("register")
    r.add_argument("--tag", required=True)
    r.add_argument("--dotenv", type=Path)
    a = commands.add_parser("approve")
    a.add_argument("--package-arn", required=True)
    a.add_argument("--approver", required=True)
    t = commands.add_parser("transform")
    t.add_argument("account", choices=["staging", "production"])
    t.add_argument("--tag", required=True)
    t.add_argument("--package-arn")
    args = ap.parse_args(argv)
    if getattr(args, "tag", None) and not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
    try:
        return {"register": register, "approve": approve, "transform": transform}[args.command](
            args
        )
    except (ChainError, StateError, TargetError, KeyError) as e:
        print(f"model-chain: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
