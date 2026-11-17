"""app-ml-score's Python tasks: `resolve`, before the batch transform, and `check`, after it.

`resolve` finds what to serve from model.json under MODEL_PREFIX. Where MODEL_SOURCE is `registry`
(Staging, Production) it is the version of MODEL_PACKAGE_GROUP whose description carries
model.json's hash, served only where its status is Approved and the archive it names has that hash.
Where it is `prefix` (`dev`) it is the archive beside model.json, compared with it. It then creates
the model the transform names, `app-ml-score-<project>`: the version's ModelPackageName, or the
serving image and the archive, with the project role, the project's subnets and security group,
network isolation and the project tag. A model of that name left by a failed run is found with
ListModels and deleted first: a describe of a free name would repeat SUP-267's gap. No value passes
from this task into the transform's request (SUP-277), so the model's name is the workflow's
constant.

`check` decodes the score and resolve tasks' XComs, reads the transform's output, one probability
between 0 and 1 for each line of the batch set, computes their AUC against the holdout's labels by
rank, writes the report and fails under MIN_AUC.
"""

from __future__ import annotations

import json

from .common import (
    PROJECT_TAG,
    auc_by_rank,
    decode_xcom,
    folder,
    read_bytes,
    read_json,
    sha256_hex,
    threshold,
    write_json,
)
from .registry import versions_with_hash

SOURCES = ("registry", "prefix")
APPROVED = "Approved"


def model_request(
    name: str, role: str, subnets: list[str], security_group: str, project: str, container: dict
) -> dict:
    """CreateModel in the project's network with network isolation, as the project role, tagged."""
    request = {
        "ModelName": name,
        "ExecutionRoleArn": role,
        "VpcConfig": {"Subnets": list(subnets), "SecurityGroupIds": [security_group]},
        "EnableNetworkIsolation": True,
        "Tags": [{"Key": PROJECT_TAG, "Value": project}],
    }
    if "ModelPackageName" in container:
        request["Containers"] = [container]
    else:
        request["PrimaryContainer"] = container
    return request


def delete_leftover(sagemaker, name: str) -> bool:
    """The model of that name deleted where ListModels finds one; whether one was."""
    for page in sagemaker.get_paginator("list_models").paginate(NameContains=name):
        for item in page.get("Models", []):
            if item["ModelName"] == name:
                sagemaker.delete_model(ModelName=name)
                print(f"deleted {name}, left by an earlier run")
                return True
    return False


def approved_version(sagemaker, s3, group: str, model: dict, serving_image: str) -> tuple:
    """(version ARN, archive URI) of the one version carrying model.json's hash, Approved, whose
    archive has that hash and whose image is the stage's."""
    digest = model["sha256"]
    found = versions_with_hash(sagemaker, group, digest)
    if len(found) != 1:
        raise RuntimeError(
            f"{len(found)} version(s) of {group} carry sha256 {digest}, one expected"
        )
    version = found[0]["ModelPackageArn"]
    described = sagemaker.describe_model_package(ModelPackageName=version)
    status = described["ModelApprovalStatus"]
    if status != APPROVED:
        raise RuntimeError(f"{version} is {status}: a target serves an Approved version alone")
    containers = described["InferenceSpecification"]["Containers"]
    if len(containers) != 1:
        raise RuntimeError(f"{version} names {len(containers)} container(s), one expected")
    archive_uri = containers[0]["ModelDataUrl"]
    served = sha256_hex(read_bytes(s3, archive_uri))
    if served != digest:
        raise RuntimeError(
            f"{version} names {archive_uri}, whose SHA-256 is {served}, not {digest}"
        )
    if containers[0]["Image"] != serving_image:
        raise RuntimeError(f"{version} names the image {containers[0]['Image']}, not the stage's")
    return version, archive_uri


def resolve_model(
    sagemaker,
    s3,
    *,
    model_prefix: str,
    source: str,
    group: str,
    serving_image: str,
    model_name: str,
    role: str,
    subnets: list[str],
    security_group: str,
    project: str,
) -> dict:
    """The model the transform serves, created; what it serves."""
    if source not in SOURCES:
        raise RuntimeError(f"MODEL_SOURCE {source!r} is not one of {', '.join(SOURCES)}")
    prefix = folder(model_prefix)
    model = read_json(s3, f"{prefix}model.json")
    if model.get("serving_image") != serving_image:
        raise RuntimeError(
            f"model.json names the serving image {model.get('serving_image')}, "
            f"and the stage serves {serving_image}"
        )
    if source == "registry":
        version, archive_uri = approved_version(sagemaker, s3, group, model, serving_image)
        container = {"ModelPackageName": version}
    else:
        version, archive_uri = None, f"{prefix}model.tar.gz"
        digest = sha256_hex(read_bytes(s3, archive_uri))
        if digest != model["sha256"]:
            raise RuntimeError(
                f"the archive under {prefix} has SHA-256 {digest}, and model.json names "
                f"{model['sha256']}"
            )
        container = {"Image": serving_image, "ModelDataUrl": archive_uri}
    delete_leftover(sagemaker, model_name)
    sagemaker.create_model(
        **model_request(model_name, role, subnets, security_group, project, container)
    )
    served = {
        "model_name": model_name,
        "source": source,
        "sha256": model["sha256"],
        "version": version,
        "model_data": archive_uri,
        "training_job": model.get("training_job"),
    }
    print(f"created {model_name} from {version or archive_uri}: sha256 {model['sha256']}")
    return served


def resolve(
    model_prefix: str,
    source: str,
    group: str,
    serving_image: str,
    model_name: str,
    role: str,
    subnet_az1: str,
    subnet_az2: str,
    security_group: str,
    project: str,
    **context,
) -> str:
    """The task: `resolve_model` with the worker's clients; what it serves as JSON text."""
    import boto3

    served = resolve_model(
        boto3.client("sagemaker"),
        boto3.client("s3"),
        model_prefix=model_prefix,
        source=source,
        group=group,
        serving_image=serving_image,
        model_name=model_name,
        role=role,
        subnets=[subnet_az1, subnet_az2],
        security_group=security_group,
        project=project,
    )
    return json.dumps(served, sort_keys=True) + "\n"


def predictions_of(text: str) -> list[float]:
    """The transform's output, one probability between 0 and 1 per line."""
    values = []
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for number, line in enumerate(lines, start=1):
        try:
            value = float(line)
        except ValueError as exc:
            raise RuntimeError(f"prediction {number} is not a number") from exc
        if not 0 <= value <= 1:
            raise RuntimeError(f"prediction {number} is not a probability")
        values.append(value)
    return values


def check_scores(
    s3, *, scored: str, resolved: str, batch: str, labels: str, report: str, min_auc: str
) -> dict:
    """The transform's output against the batch set and its labels, the report written; the
    report."""
    floor = threshold(min_auc)
    transform = decode_xcom(scored, "score").get("Transform") or {}
    job = transform.get("TransformJobName")
    output = (transform.get("TransformOutput") or {}).get("S3OutputPath")
    if not job or not output:
        raise RuntimeError("the score task's XCom names no transform job and output")
    served = decode_xcom(resolved, "resolve")
    rows = sum(1 for line in read_bytes(s3, batch).decode().splitlines() if line.strip())
    expected = [int(value) for value in read_bytes(s3, labels).decode().split()]
    batch_name = batch.rstrip("/").rsplit("/", 1)[-1]
    scores = predictions_of(read_bytes(s3, f"{folder(output)}{batch_name}.out").decode())
    if not rows == len(expected) == len(scores):
        raise RuntimeError(
            f"{len(scores)} prediction(s) for {rows} batch line(s) and {len(expected)} label(s)"
        )
    auc = round(auc_by_rank(scores, expected), 6)
    result = {
        "transform_job": job,
        "sha256": served.get("sha256"),
        "source": served.get("source"),
        "version": served.get("version"),
        "training_job": served.get("training_job"),
        "rows": rows,
        "predictions": len(scores),
        "auc": auc,
        "min_auc": floor,
    }
    write_json(s3, report, result)
    print(f"{job}: {len(scores)} prediction(s) for {rows} line(s), AUC {auc}, MIN_AUC {floor}")
    if auc < floor:
        raise RuntimeError(f"{job}: AUC {auc} is under MIN_AUC {floor}")
    return result


def check(
    scored: str, resolved: str, batch: str, labels: str, report: str, min_auc: str, **context
) -> str:
    """The task: `check_scores` with the worker's client; the report as JSON text."""
    import boto3

    result = check_scores(
        boto3.client("s3"),
        scored=scored,
        resolved=resolved,
        batch=batch,
        labels=labels,
        report=report,
        min_auc=min_auc,
    )
    return json.dumps(result, sort_keys=True) + "\n"
