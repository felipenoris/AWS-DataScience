"""Stage 17 steps 2.2, 2.3 and 3.1: the XGBoost training job, its variants, and the MLflow run.

One request, built once, and each variant changes exactly one field of it (Lesson 20):

    untagged        no AmazonDataZoneProject tag                      2.2 (a), expected refused
    tagged          the admitted request                              2.2 (b) and (c), 2.3's sixth
    no-vpc          no VpcConfig                                      2.3, DenySageMakerJobsOffVpc
    no-isolation    EnableNetworkIsolation false                      2.3
    no-ice          EnableInterContainerTrafficEncryption false       2.3
    no-volume-key   no ResourceConfig.VolumeKmsKeyId                  2.3
    ceiling         ml.m5.2xlarge for ml.m5.xlarge                    2.3, the instance ceiling

The admitted request is the recipe's but for the image: XGBoost 3.0-5, which XGBOOST_IMAGE_URI
names, for the recipe's 1.7-1 (README.md, "The model format"), ml.m5.xlarge, one instance, 30 GB
under the project key, max_run 600 s, the project's subnets and security group, network
isolation and inter-container encryption on, the output under shared/ml-demo/models/ under the
project key. Step 3.1's second job is the tagged variant with --num-round 50 --max-depth 3. A
negative the boundary admits is stopped at once.

Each attempt opens an MLflow run in the project's MLflow App before the call (step 2.2), logs the
hyperparameters and the variant, and tags the run with the outcome: the job's name, or the
refusal's code and message. With --wait it waits for the job and logs its validation AUC, a
reading and not a gate. It prints the job's name, status and metrics, never a row.

    /opt/awsds/venv/bin/python train.py tagged --wait
"""

from __future__ import annotations

import argparse
import copy
import sys

import mlflow
from botocore.exceptions import ClientError, WaiterError
from common import (
    EXPERIMENT,
    client,
    key_arn,
    load_values,
    need,
    project_tags,
    refusal,
    role_arn,
    s3_uri,
    stamp,
    vpc_config,
)

INSTANCE_TYPE = "ml.m5.xlarge"
CEILING_NEGATIVE = "ml.m5.2xlarge"
VARIANTS = (
    "untagged",
    "tagged",
    "no-vpc",
    "no-isolation",
    "no-ice",
    "no-volume-key",
    "ceiling",
)


def admitted_request(values: dict, name: str, num_round: int, max_depth: int) -> dict:
    """The CreateTrainingJob request that meets the boundary's four settings and the ceiling."""
    channels = []
    for channel in ("train", "validation"):
        channels.append(
            {
                "ChannelName": channel,
                "ContentType": "text/csv",
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": s3_uri(values, "data", f"{channel}.csv"),
                        "S3DataDistributionType": "FullyReplicated",
                    }
                },
            }
        )
    return {
        "TrainingJobName": name,
        "AlgorithmSpecification": {
            "TrainingImage": values["XGBOOST_IMAGE_URI"],
            "TrainingInputMode": "File",
        },
        "RoleArn": role_arn(values),
        "HyperParameters": {
            "objective": "binary:logistic",
            "eval_metric": "auc",
            "num_round": str(num_round),
            "max_depth": str(max_depth),
            "eta": "0.2",
            "subsample": "0.8",
        },
        "InputDataConfig": channels,
        "OutputDataConfig": {
            "S3OutputPath": s3_uri(values, "models") + "/",
            "KmsKeyId": key_arn(values),
        },
        "ResourceConfig": {
            "InstanceType": INSTANCE_TYPE,
            "InstanceCount": 1,
            "VolumeSizeInGB": 30,
            "VolumeKmsKeyId": key_arn(values),
        },
        "StoppingCondition": {"MaxRuntimeInSeconds": 600},
        "VpcConfig": vpc_config(values),
        "EnableNetworkIsolation": True,
        "EnableInterContainerTrafficEncryption": True,
        "Tags": project_tags(values),
    }


def variant_request(admitted: dict, variant: str) -> dict:
    """The admitted request with the one field the variant changes."""
    request = copy.deepcopy(admitted)
    if variant == "untagged":
        del request["Tags"]
    elif variant == "no-vpc":
        del request["VpcConfig"]
    elif variant == "no-isolation":
        request["EnableNetworkIsolation"] = False
    elif variant == "no-ice":
        request["EnableInterContainerTrafficEncryption"] = False
    elif variant == "no-volume-key":
        del request["ResourceConfig"]["VolumeKmsKeyId"]
    elif variant == "ceiling":
        request["ResourceConfig"]["InstanceType"] = CEILING_NEGATIVE
    return request


def wait_for(sagemaker, name: str) -> dict:
    """The job's description once it stops, whatever its outcome."""
    try:
        sagemaker.get_waiter("training_job_completed_or_stopped").wait(
            TrainingJobName=name, WaiterConfig={"Delay": 30, "MaxAttempts": 40}
        )
    except WaiterError as err:
        print(f"the waiter stopped: {err}")
    return sagemaker.describe_training_job(TrainingJobName=name)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="train.py")
    parser.add_argument("variant", choices=VARIANTS)
    parser.add_argument("--wait", action="store_true", help="wait for the job and log its AUC")
    parser.add_argument("--num-round", type=int, default=200)
    parser.add_argument("--max-depth", type=int, default=5)
    args = parser.parse_args(argv)

    values = load_values()
    need(values, "XGBOOST_IMAGE_URI", "MLFLOW_APP_ARN", "PROJECT_KEY_ID")
    sagemaker = client(values, "sagemaker")
    name = f"ml-demo-xgb-{args.variant}-{stamp()}"
    admitted = admitted_request(values, name, args.num_round, args.max_depth)
    request = variant_request(admitted, args.variant)

    mlflow.set_tracking_uri(values["MLFLOW_APP_ARN"])
    mlflow.set_experiment(EXPERIMENT)
    with mlflow.start_run(run_name=name):
        mlflow.log_params(request["HyperParameters"])
        mlflow.log_params(
            {"variant": args.variant, "instance_type": request["ResourceConfig"]["InstanceType"]}
        )
        mlflow.set_tag("training_job_name", name)
        try:
            sagemaker.create_training_job(**request)
        except ClientError as err:
            mlflow.set_tag("outcome", "refused")
            mlflow.set_tag("refusal", refusal(err)[:5000])
            print(f"{name}: refused")
            print(refusal(err))
            return 1
        mlflow.set_tag("outcome", "created")
        print(f"{name}: created")
        if args.variant != "tagged":
            # Every other variant is a negative: admitted, it would train and bill for nothing.
            sagemaker.stop_training_job(TrainingJobName=name)
            print("admitted, contrary to the stage's expectation: stopped")
            return 1
        if not args.wait:
            return 0

        job = wait_for(sagemaker, name)
        status = job["TrainingJobStatus"]
        mlflow.set_tag("status", status)
        print(f"{name}: {status}, {job.get('BillableTimeInSeconds', '-')} s billed")
        if job.get("FailureReason"):
            print(f"failure: {job['FailureReason']}")
        for metric in job.get("FinalMetricDataList", []):
            print(f"{metric['MetricName']}: {metric['Value']:.4f}")
            mlflow.log_metric(metric["MetricName"].replace(":", "_"), metric["Value"])
        print(f"model: {job.get('ModelArtifacts', {}).get('S3ModelArtifacts', '-')}")
        return 0 if status == "Completed" else 1


if __name__ == "__main__":
    sys.exit(main())
