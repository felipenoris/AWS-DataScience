"""Stage 17 steps 4.1, 4.3 and 4.4: a registered version served online, offline, and refused.

    endpoint PACKAGE_ARN     4.1: CreateModel from the version's image and ModelDataUrl, with the
                             project's VpcConfig and network isolation; an endpoint configuration
                             on ml.m5.large under the project key; CreateEndpoint. It prints the
                             time to InService, sends validation.csv's features through
                             InvokeEndpoint and recomputes the AUC from the answers, then deletes
                             the endpoint, its configuration and the model, whatever happened
                             (decision 6: no endpoint outlives its sitting)
    transform PACKAGE_ARN [--no-volume-key]
                             4.3: the same model and CreateTransformJob over validation.csv on
                             ml.m5.large, the volume and the output under the project key, the
                             output under shared/ml-demo/predictions/. The label column is
                             filtered out of the input and joined back to the output, so the AUC
                             is recomputed from the transform's own lines. --no-volume-key is the
                             negative, refused by DenySageMakerJobsWithoutVolumeEncryption
    serverless PACKAGE_ARN   4.4, for Stage 9 3.7: (a) CreateModel with no VpcConfig, expected
                             refused by DenySageMakerJobsOffVpc; (b) the model with its VpcConfig
                             named by a serverless endpoint configuration, 1024 MB, expected
                             refused by the service. Anything admitted is deleted in the run

Every object carries the project tag and an ml-demo- name; the model is deleted at the end of
each run. It prints counts, an AUC and every refusal whole, never a row.

    /opt/awsds/venv/bin/python serve.py endpoint <the version's ModelPackageArn>
"""

from __future__ import annotations

import argparse
import io
import sys
import time

import pandas as pd
from botocore.exceptions import ClientError, WaiterError
from common import (
    client,
    key_arn,
    load_values,
    need,
    project_tags,
    refusal,
    role_arn,
    s3_uri,
    split_s3_uri,
    stamp,
    vpc_config,
)
from sklearn.metrics import roc_auc_score

INSTANCE_TYPE = "ml.m5.large"
BATCH_ROWS = 200  # rows per InvokeEndpoint call, far under the 6 MB payload limit
SERVERLESS_MB = 1024


def package_container(sagemaker, package_arn: str) -> dict:
    """The registered version's image and model data, as CreateModel takes them."""
    described = sagemaker.describe_model_package(ModelPackageName=package_arn)
    container = described["InferenceSpecification"]["Containers"][0]
    return {"Image": container["Image"], "ModelDataUrl": container["ModelDataUrl"]}


def model_request(values: dict, name: str, container: dict) -> dict:
    """The CreateModel request the boundary admits: the VpcConfig and network isolation."""
    return {
        "ModelName": name,
        "PrimaryContainer": container,
        "ExecutionRoleArn": role_arn(values),
        "VpcConfig": vpc_config(values),
        "EnableNetworkIsolation": True,
        "Tags": project_tags(values),
    }


def attempt(call, label: str, **request) -> bool:
    """Whether a create was admitted; a refusal is printed whole."""
    try:
        call(**request)
    except ClientError as err:
        print(f"{label}: refused")
        print(refusal(err))
        return False
    print(f"{label}: created")
    return True


def delete_all(sagemaker, created: list) -> None:
    """Delete what a run created, newest first, and print each outcome."""
    calls = {
        "endpoint": lambda name: sagemaker.delete_endpoint(EndpointName=name),
        "endpoint configuration": lambda name: sagemaker.delete_endpoint_config(
            EndpointConfigName=name
        ),
        "model": lambda name: sagemaker.delete_model(ModelName=name),
    }
    for kind, name in reversed(created):
        try:
            calls[kind](name)
        except ClientError as err:
            print(f"{kind} {name}: delete failed, delete it by hand")
            print(refusal(err))
            continue
        print(f"{kind} {name}: deleted")


def validation_table(values: dict) -> pd.DataFrame:
    """validation.csv as data.py wrote it: the label in column 0, no header."""
    bucket, key = split_s3_uri(s3_uri(values, "data", "validation.csv"))
    body = client(values, "s3").get_object(Bucket=bucket, Key=key)["Body"].read()
    return pd.read_csv(io.BytesIO(body), header=None)


def invoke(runtime, endpoint: str, features: pd.DataFrame) -> list:
    """The endpoint's scores for the rows, in order."""
    scores = []
    for start in range(0, len(features), BATCH_ROWS):
        batch = features.iloc[start : start + BATCH_ROWS]
        answer = runtime.invoke_endpoint(
            EndpointName=endpoint,
            ContentType="text/csv",
            Accept="text/csv",
            Body=batch.to_csv(header=False, index=False),
        )
        text = answer["Body"].read().decode("utf-8")
        scores.extend(float(x) for x in text.replace("\n", ",").split(",") if x.strip())
    return scores


def endpoint(values: dict, package_arn: str) -> int:
    sagemaker = client(values, "sagemaker")
    name = f"ml-demo-xgb-{stamp()}"
    container = package_container(sagemaker, package_arn)
    created = []
    try:
        if not attempt(
            sagemaker.create_model, f"model {name}", **model_request(values, name, container)
        ):
            return 1
        created.append(("model", name))
        config = {
            "EndpointConfigName": name,
            "ProductionVariants": [
                {
                    "VariantName": "AllTraffic",
                    "ModelName": name,
                    "InstanceType": INSTANCE_TYPE,
                    "InitialInstanceCount": 1,
                }
            ],
            "KmsKeyId": key_arn(values),
            "Tags": project_tags(values),
        }
        if not attempt(
            sagemaker.create_endpoint_config, f"endpoint configuration {name}", **config
        ):
            return 1
        created.append(("endpoint configuration", name))
        if not attempt(
            sagemaker.create_endpoint,
            f"endpoint {name}",
            EndpointName=name,
            EndpointConfigName=name,
            Tags=project_tags(values),
        ):
            return 1
        created.append(("endpoint", name))

        # The time to InService is a reading of the stage (4.1).
        started = time.monotonic()
        try:
            sagemaker.get_waiter("endpoint_in_service").wait(
                EndpointName=name, WaiterConfig={"Delay": 30, "MaxAttempts": 40}
            )
        except WaiterError as err:
            print(f"the waiter stopped: {err}")
        described = sagemaker.describe_endpoint(EndpointName=name)
        status = described["EndpointStatus"]
        print(f"endpoint {name}: {status} after {time.monotonic() - started:.0f} s")
        if status != "InService":
            print(f"failure: {described.get('FailureReason', '-')}")
            return 1

        table = validation_table(values)
        scores = invoke(client(values, "sagemaker-runtime"), name, table.iloc[:, 1:])
        print(f"{len(scores)} scores for {len(table)} validation rows")
        if len(scores) != len(table):
            return 1
        print(f"AUC recomputed from the endpoint: {roc_auc_score(table[0], scores):.4f}")
        return 0
    finally:
        delete_all(sagemaker, created)


def transform(values: dict, package_arn: str, no_volume_key: bool) -> int:
    sagemaker = client(values, "sagemaker")
    suffix = stamp()
    model, job = f"ml-demo-xgb-{suffix}", f"ml-demo-transform-{suffix}"
    container = package_container(sagemaker, package_arn)
    created = []
    try:
        if not attempt(
            sagemaker.create_model, f"model {model}", **model_request(values, model, container)
        ):
            return 1
        created.append(("model", model))
        output = s3_uri(values, "predictions", job)
        request = {
            "TransformJobName": job,
            "ModelName": model,
            "TransformInput": {
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": s3_uri(values, "data", "validation.csv"),
                    }
                },
                "ContentType": "text/csv",
                "SplitType": "Line",
            },
            "TransformOutput": {
                "S3OutputPath": output + "/",
                "Accept": "text/csv",
                "AssembleWith": "Line",
                "KmsKeyId": key_arn(values),
            },
            "TransformResources": {
                "InstanceType": INSTANCE_TYPE,
                "InstanceCount": 1,
                "VolumeKmsKeyId": key_arn(values),
            },
            # The features go in without the label; each output line is the label and the score.
            "DataProcessing": {
                "InputFilter": "$[1:]",
                "JoinSource": "Input",
                "OutputFilter": "$[0,-1]",
            },
            "Tags": project_tags(values),
        }
        if no_volume_key:
            del request["TransformResources"]["VolumeKmsKeyId"]
        if not attempt(sagemaker.create_transform_job, f"transform job {job}", **request):
            return 1
        if no_volume_key:
            print("the negative was admitted, contrary to the stage's expectation: stopping it")
            sagemaker.stop_transform_job(TransformJobName=job)
            return 1

        try:
            sagemaker.get_waiter("transform_job_completed_or_stopped").wait(
                TransformJobName=job, WaiterConfig={"Delay": 30, "MaxAttempts": 60}
            )
        except WaiterError as err:
            print(f"the waiter stopped: {err}")
        described = sagemaker.describe_transform_job(TransformJobName=job)
        status = described["TransformJobStatus"]
        print(f"transform job {job}: {status}")
        if status != "Completed":
            print(f"failure: {described.get('FailureReason', '-')}")
            return 1

        bucket, key = split_s3_uri(f"{output}/validation.csv.out")
        body = client(values, "s3").get_object(Bucket=bucket, Key=key)["Body"].read()
        lines = pd.read_csv(io.BytesIO(body), header=None)
        print(f"{len(lines)} lines in s3://{bucket}/{key}")
        print(f"AUC recomputed from the transform: {roc_auc_score(lines[0], lines[1]):.4f}")
        return 0
    finally:
        delete_all(sagemaker, created)


def serverless(values: dict, package_arn: str) -> int:
    sagemaker = client(values, "sagemaker")
    container = package_container(sagemaker, package_arn)
    created = []
    try:
        # (a) The one field a serverless endpoint demands be absent, absent.
        name = f"ml-demo-xgb-novpc-{stamp()}"
        request = model_request(values, name, container)
        del request["VpcConfig"]
        print("(a) CreateModel with no VpcConfig")
        if attempt(sagemaker.create_model, f"model {name}", **request):
            created.append(("model", name))
            print("admitted: the stage expected DenySageMakerJobsOffVpc to refuse it")

        # (b) The admitted model, named by a serverless configuration.
        name = f"ml-demo-xgb-sls-{stamp()}"
        print("(b) a model with its VpcConfig, behind a serverless endpoint configuration")
        if not attempt(
            sagemaker.create_model, f"model {name}", **model_request(values, name, container)
        ):
            return 1
        created.append(("model", name))
        config = {
            "EndpointConfigName": name,
            "ProductionVariants": [
                {
                    "VariantName": "AllTraffic",
                    "ModelName": name,
                    "ServerlessConfig": {"MemorySizeInMB": SERVERLESS_MB, "MaxConcurrency": 1},
                }
            ],
            "Tags": project_tags(values),
        }
        if not attempt(
            sagemaker.create_endpoint_config, f"endpoint configuration {name}", **config
        ):
            return 0
        created.append(("endpoint configuration", name))
        if attempt(
            sagemaker.create_endpoint,
            f"endpoint {name}",
            EndpointName=name,
            EndpointConfigName=name,
            Tags=project_tags(values),
        ):
            created.append(("endpoint", name))
            print("admitted: the stage expected the service to refuse a VpcConfig here")
        return 0
    finally:
        delete_all(sagemaker, created)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="serve.py")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("endpoint", "transform", "serverless"):
        cmd = sub.add_parser(command)
        cmd.add_argument("package_arn", help="the registered version's ModelPackageArn")
        if command == "transform":
            cmd.add_argument("--no-volume-key", action="store_true", help="4.3's negative")
    args = parser.parse_args(argv)

    values = load_values()
    need(values, "PROJECT_KEY_ID")
    if args.command == "endpoint":
        return endpoint(values, args.package_arn)
    if args.command == "transform":
        return transform(values, args.package_arn, args.no_volume_key)
    return serverless(values, args.package_arn)


if __name__ == "__main__":
    sys.exit(main())
