"""Stage 17 steps 3.1 and 3.2: the model tracked in MLflow and registered, through both doors.

    log-model JOB        3.1: download the job's model.tar.gz and log it as an artifact of the
                         run train.py opened for that job, under archive/, which verification iv
                         reads in the artifact store; then load the booster and log it with
                         mlflow.xgboost.log_model, where this interpreter's xgboost reads the
                         image's format, or print xgboost's refusal as the reading
    package JOB          3.2: the group ml-demo-xgboost (created with the project tag if absent)
                         and a version from the job: the job's own image, its ModelDataUrl,
                         PendingManualApproval. The user approves it from the portal's page
    from-mlflow JOB      3.2: a second version through the registry's MLflow integration, as
                         AWS's recipe registers one: mlflow.register_model on the job's
                         model.tar.gz, into the registered model ml-demo-xgboost

The image's format decides the booster half (README.md, "The model format"): XGBoost 1.7-1
writes the binary format XGBoost 3.1 removed, and the house interpreter's xgboost is 3.3.0 in the
image's lock. It prints the names, versions and ARNs, never the model.

    /opt/awsds/venv/bin/python register.py package ml-demo-xgb-tagged-20261020-140000
"""

from __future__ import annotations

import argparse
import sys
import tarfile
import tempfile
from pathlib import Path

import mlflow
import mlflow.xgboost
import xgboost
from botocore.exceptions import ClientError
from common import (
    EXPERIMENT,
    MODEL_GROUP,
    client,
    load_values,
    need,
    project_tags,
    refusal,
    split_s3_uri,
)
from xgboost.core import XGBoostError

# SageMaker's XGBoost 1.3-1 and later save the booster under this name, in the format of the
# XGBoost version the image carries.
MODEL_FILE = "xgboost-model"
SERVING_TYPE = "ml.m5.large"


def model_data(sagemaker, job: str) -> tuple:
    """(image, model.tar.gz URI) of a completed training job."""
    described = sagemaker.describe_training_job(TrainingJobName=job)
    if described["TrainingJobStatus"] != "Completed":
        sys.exit(f"{job} is {described['TrainingJobStatus']}: only a completed job has a model.")
    image = described["AlgorithmSpecification"]["TrainingImage"]
    return image, described["ModelArtifacts"]["S3ModelArtifacts"]


def run_of(job: str) -> str:
    """The MLflow run train.py opened for the job."""
    runs = mlflow.search_runs(
        experiment_names=[EXPERIMENT], filter_string=f"tags.training_job_name = '{job}'"
    )
    if len(runs) != 1:
        sys.exit(f"{len(runs)} runs carry training_job_name {job} in {EXPERIMENT}; expected one.")
    return runs.iloc[0]["run_id"]


def log_booster(scratch: Path, archive: Path) -> bool:
    """Log the archive's booster as the run's model; False, with xgboost's words, if refused."""
    with tarfile.open(archive) as tar:
        members = [m for m in tar.getmembers() if Path(m.name).name == MODEL_FILE]
        if not members:
            print(f"no {MODEL_FILE} in model.tar.gz: {', '.join(tar.getnames())}")
            return False
        tar.extract(members[0], path=scratch, filter="data")
    booster = xgboost.Booster()
    try:
        booster.load_model(str(scratch / members[0].name))
    except XGBoostError as err:
        print(f"xgboost {xgboost.__version__} refused {MODEL_FILE}:")
        print(str(err).split("Stack trace:")[0].strip())
        return False
    mlflow.xgboost.log_model(booster, "model")
    return True


def log_model(values: dict, job: str) -> int:
    sagemaker, s3 = client(values, "sagemaker"), client(values, "s3")
    _image, uri = model_data(sagemaker, job)
    run_id = run_of(job)

    with tempfile.TemporaryDirectory() as scratch:
        archive = Path(scratch) / "model.tar.gz"
        bucket, key = split_s3_uri(uri)
        s3.download_file(bucket, key, str(archive))
        with mlflow.start_run(run_id=run_id):
            mlflow.log_artifact(str(archive), "archive")
            print(f"{job}: model.tar.gz logged into run {run_id} under archive/")
            if log_booster(Path(scratch), archive):
                print(f"{job}: booster logged as runs:/{run_id}/model")
    return 0


def ensure_group(sagemaker, values: dict) -> bool:
    """Whether the group exists after the call; a refused create is printed."""
    try:
        sagemaker.describe_model_package_group(ModelPackageGroupName=MODEL_GROUP)
        return True
    except ClientError as err:
        if "does not exist" not in refusal(err):
            raise
    try:
        sagemaker.create_model_package_group(
            ModelPackageGroupName=MODEL_GROUP,
            ModelPackageGroupDescription="Stage 17: the XGBoost churn model of the exercise",
            Tags=project_tags(values),
        )
    except ClientError as err:
        print(f"{MODEL_GROUP}: refused")
        print(refusal(err))
        return False
    print(f"{MODEL_GROUP}: created")
    return True


def package(values: dict, job: str) -> int:
    sagemaker = client(values, "sagemaker")
    image, uri = model_data(sagemaker, job)
    if not ensure_group(sagemaker, values):
        return 1
    try:
        created = sagemaker.create_model_package(
            ModelPackageGroupName=MODEL_GROUP,
            ModelPackageDescription=f"from the training job {job}",
            InferenceSpecification={
                "Containers": [{"Image": image, "ModelDataUrl": uri}],
                "SupportedContentTypes": ["text/csv"],
                "SupportedResponseMIMETypes": ["text/csv"],
                "SupportedRealtimeInferenceInstanceTypes": [SERVING_TYPE],
                "SupportedTransformInstanceTypes": [SERVING_TYPE],
            },
            ModelApprovalStatus="PendingManualApproval",
            Tags=project_tags(values),
        )
    except ClientError as err:
        print(f"{MODEL_GROUP} version from {job}: refused")
        print(refusal(err))
        return 1
    print(f"{MODEL_GROUP} version from {job}: {created['ModelPackageArn']}")
    return 0


def from_mlflow(values: dict, job: str) -> int:
    _image, uri = model_data(client(values, "sagemaker"), job)
    version = mlflow.register_model(model_uri=uri, name=MODEL_GROUP)
    print(f"{MODEL_GROUP}: MLflow version {version.version} from {job}'s model.tar.gz")
    return 0


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="register.py")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("log-model", "package", "from-mlflow"):
        sub.add_parser(command).add_argument("job", help="a completed training job's name")
    args = parser.parse_args(argv)

    values = load_values()
    if args.command == "package":
        return package(values, args.job)
    need(values, "MLFLOW_APP_ARN")
    mlflow.set_tracking_uri(values["MLFLOW_APP_ARN"])
    if args.command == "log-model":
        return log_model(values, args.job)
    return from_mlflow(values, args.job)


if __name__ == "__main__":
    sys.exit(main())
