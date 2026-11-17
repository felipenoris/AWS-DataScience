"""app-ml-register's task: the candidate under MODEL_PREFIX proposed in MODEL_PACKAGE_GROUP.

`register` reads model.json and the archive beside it, and fails where the archive's SHA-256 is not
the one model.json names, or where model.json's serving image is not the stage's. It copies the
archive and the evaluation to `<models>sha256/<hash>/`, a prefix no deploy writes, and calls
CreateModelPackage in MODEL_PACKAGE_GROUP: that copy and the serving image as the inference
specification, with the copy's ETag; the evaluation's copy as the model's quality metrics; the hash
in the version's description, which UpdateModelPackage cannot change; the training job and the
prefix the candidate was read from as its metadata; and the status PendingManualApproval. Where the
group already holds a version whose description carries the hash, it proposes none. It creates no
group and sets no other status (Stage 17 decision 16 (b)): a version's status moves by the
account's deploy role alone.
"""

from __future__ import annotations

import json

from .common import folder, read_bytes, read_json, sha256_hex, write_bytes

APPLICATION = "app-ml"
PENDING = "PendingManualApproval"
# The instance type a version names for a batch transform: the score task's.
INSTANCE_TYPE = "ml.m5.large"


def hash_mark(sha256: str) -> str:
    """How a version's description carries the archive's hash."""
    return f"sha256:{sha256}"


def read_candidate(s3, model_prefix: str, serving_image: str) -> tuple[dict, bytes]:
    """model.json under the prefix and the archive beside it, the archive's hash and the serving
    image checked against model.json and the stage."""
    prefix = folder(model_prefix)
    model = read_json(s3, f"{prefix}model.json")
    missing = [key for key in ("sha256", "training_job", "serving_image") if key not in model]
    if missing:
        raise RuntimeError(f"{prefix}model.json names no {', '.join(missing)}")
    archive = read_bytes(s3, f"{prefix}model.tar.gz")
    digest = sha256_hex(archive)
    if digest != model["sha256"]:
        raise RuntimeError(
            f"the archive under {prefix} has SHA-256 {digest}, "
            f"and model.json names {model['sha256']}"
        )
    if model["serving_image"] != serving_image:
        raise RuntimeError(
            f"model.json names the serving image {model['serving_image']}, "
            f"and the stage serves {serving_image}"
        )
    return model, archive


def versions_with_hash(sagemaker, group: str, sha256: str) -> list[dict]:
    """The versions of the group, any status, whose description carries the hash."""
    mark = hash_mark(sha256)
    found = []
    paginator = sagemaker.get_paginator("list_model_packages")
    for page in paginator.paginate(ModelPackageGroupName=group):
        for summary in page.get("ModelPackageSummaryList", []):
            if mark in (summary.get("ModelPackageDescription") or ""):
                found.append(summary)
    return found


def package_request(
    group: str, model: dict, copy_uri: str, etag: str, evaluation_uri: str, source_prefix: str
) -> dict:
    """CreateModelPackage: the archive's copy served by the serving image, PendingManualApproval."""
    return {
        "ModelPackageGroupName": group,
        "ModelPackageDescription": (
            f"{APPLICATION} {hash_mark(model['sha256'])}, trained by {model['training_job']}"
        ),
        "ModelApprovalStatus": PENDING,
        "InferenceSpecification": {
            "Containers": [
                {"Image": model["serving_image"], "ModelDataUrl": copy_uri, "ModelDataETag": etag}
            ],
            "SupportedContentTypes": ["text/csv"],
            "SupportedResponseMIMETypes": ["text/csv"],
            "SupportedTransformInstanceTypes": [INSTANCE_TYPE],
        },
        "ModelMetrics": {
            "ModelQuality": {
                "Statistics": {"ContentType": "application/json", "S3Uri": evaluation_uri}
            }
        },
        "CustomerMetadataProperties": {
            "sha256": model["sha256"],
            "training_job": model["training_job"],
            "source_prefix": source_prefix,
            "training_source": str(model.get("training_source") or "none"),
            "validation_auc": str(model.get("auc")),
        },
    }


def register_model(
    sagemaker, s3, model_prefix: str, group: str, models: str, serving_image: str
) -> dict:
    """The candidate proposed in the group, or nothing where a version carries its hash; what was
    done."""
    prefix = folder(model_prefix)
    model, archive = read_candidate(s3, prefix, serving_image)
    digest = model["sha256"]
    existing = [v["ModelPackageArn"] for v in versions_with_hash(sagemaker, group, digest)]
    if existing:
        print(f"{group} holds {', '.join(existing)} for sha256 {digest}: nothing proposed")
        return {"registered": False, "sha256": digest, "versions": existing}
    copy = f"{folder(models)}sha256/{digest}/"
    put = write_bytes(s3, f"{copy}model.tar.gz", archive)
    evaluation = read_bytes(s3, f"{prefix}evaluation.json")
    write_bytes(s3, f"{copy}evaluation.json", evaluation, "application/json")
    # The copy's ETag without the quotes S3 returns it in; what the service does with it at
    # CreateModel is unread (Stage 17 verification lix).
    request = package_request(
        group,
        model,
        f"{copy}model.tar.gz",
        put["ETag"].strip('"'),
        f"{copy}evaluation.json",
        prefix,
    )
    version = sagemaker.create_model_package(**request)["ModelPackageArn"]
    print(f"proposed {version}: sha256 {digest}, trained by {model['training_job']}, {PENDING}")
    return {
        "registered": True,
        "sha256": digest,
        "version": version,
        "training_job": model["training_job"],
    }


def register(model_prefix: str, group: str, models: str, serving_image: str, **context) -> str:
    """The task: `register_model` with the worker's clients; what was done as JSON text."""
    import boto3

    result = register_model(
        boto3.client("sagemaker"), boto3.client("s3"), model_prefix, group, models, serving_image
    )
    return json.dumps(result, sort_keys=True) + "\n"
