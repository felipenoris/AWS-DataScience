"""app-ml-train's Python tasks: `evaluate`, after the training job, and `publish`, last.

`evaluate` decodes the train task's XCom, reads the job's final `validation:auc`, writes
`<models><job>/evaluation.json` in SageMaker's model-quality shape for a binary classifier and the
pointer `<models>last-run.json`, which the track task reads, and fails under MIN_AUC. `publish`
makes the run's model the release candidate: it copies the job's archive to
`<models>latest/model.tar.gz` and the evaluation to `<models>latest/evaluation.json`, then writes
`<models>latest/model.json`, the training job, both images by digest, the hyperparameters, the AUC,
the SHA-256 of the bytes it copied and TRAINING_SOURCE. Every check runs before the first write, and
model.json is written after the two copies: a copy cut short leaves an archive model.json does not
describe, which every reader refuses. The archive passes through the worker's memory, which holds a
model of a few megabytes.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from .common import (
    by_digest,
    decode_xcom,
    folder,
    read_bytes,
    sha256_hex,
    threshold,
    write_bytes,
    write_json,
)

APPLICATION = "app-ml"
# The training job's final metric, as XGBoost names it with a validation channel and
# `eval_metric: auc`.
VALIDATION_METRIC = "validation:auc"


def training_job_name(training: str | dict) -> str:
    """The job's name in the train task's XCom, the training operator's `{"Training": ...}`."""
    value = decode_xcom(training, "train")
    try:
        return value["Training"]["TrainingJobName"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError(f"the train task's XCom names no training job: {sorted(value)}") from exc


def completed_job(sagemaker, job: str) -> dict:
    described = sagemaker.describe_training_job(TrainingJobName=job)
    if described["TrainingJobStatus"] != "Completed":
        raise RuntimeError(f"{job} is {described['TrainingJobStatus']}, not Completed")
    return described


def validation_auc(described: dict) -> float:
    metrics = {m["MetricName"]: m["Value"] for m in described.get("FinalMetricDataList", [])}
    if VALIDATION_METRIC not in metrics:
        raise RuntimeError(f"{described['TrainingJobName']} reports no {VALIDATION_METRIC}")
    return float(metrics[VALIDATION_METRIC])


def model_quality(described: dict, auc: float) -> dict:
    """SageMaker's model-quality statistics for a binary classifier, with the job beside them."""
    return {
        "version": 0.0,
        "binary_classification_metrics": {"auc": {"value": auc, "standard_deviation": "NaN"}},
        "awsds": {
            "training_job": described["TrainingJobName"],
            "model_data": described["ModelArtifacts"]["S3ModelArtifacts"],
        },
    }


def evaluation_auc(evaluation: dict) -> float:
    try:
        return float(evaluation["binary_classification_metrics"]["auc"]["value"])
    except (KeyError, TypeError, ValueError) as exc:
        raise RuntimeError("the evaluation carries no binary_classification_metrics.auc") from exc


def evaluate_job(sagemaker, s3, training: str | dict, models: str, min_auc: str) -> dict:
    """The evaluation and the pointer written for the job the XCom names; the pointer."""
    floor = threshold(min_auc)
    job = training_job_name(training)
    described = completed_job(sagemaker, job)
    auc = validation_auc(described)
    evaluation_uri = f"{folder(models)}{job}/evaluation.json"
    write_json(s3, evaluation_uri, model_quality(described, auc))
    run = {
        "training_job": job,
        "model_data": described["ModelArtifacts"]["S3ModelArtifacts"],
        "training_image": described["AlgorithmSpecification"]["TrainingImage"],
        "hyperparameters": dict(described.get("HyperParameters") or {}),
        "auc": auc,
        "evaluation": evaluation_uri,
    }
    write_json(s3, f"{folder(models)}last-run.json", run)
    print(f"{job}: {VALIDATION_METRIC} {auc}, MIN_AUC {floor}, {evaluation_uri}")
    if auc < floor:
        raise RuntimeError(f"{job}: {VALIDATION_METRIC} {auc} is under MIN_AUC {floor}")
    return run


def evaluate(training: str, models: str, min_auc: str, **context) -> str:
    """The task: `evaluate_job` with the worker's clients; the pointer as JSON text, its XCom."""
    import boto3

    run = evaluate_job(boto3.client("sagemaker"), boto3.client("s3"), training, models, min_auc)
    return json.dumps(run, sort_keys=True) + "\n"


def publish_model(
    sagemaker,
    s3,
    training: str | dict,
    models: str,
    serving_image: str,
    training_source: str,
    min_auc: str,
) -> dict:
    """The job's archive and evaluation copied under `<models>latest/`, then model.json beside
    them; model.json's content."""
    floor = threshold(min_auc)
    job = training_job_name(training)
    described = completed_job(sagemaker, job)
    source = str(training_source).strip()
    if not source or source == "none":
        raise RuntimeError(
            "TRAINING_SOURCE is empty or none: deploy the dev stage with scripts/dev-cli.sh"
        )
    training_image = by_digest(
        described["AlgorithmSpecification"]["TrainingImage"], "training image"
    )
    serving = by_digest(serving_image, "serving image")
    evaluation_bytes = read_bytes(s3, f"{folder(models)}{job}/evaluation.json")
    auc = evaluation_auc(json.loads(evaluation_bytes))
    if auc < floor:
        raise RuntimeError(f"{job}: AUC {auc} is under MIN_AUC {floor}, nothing published")
    model_data = described["ModelArtifacts"]["S3ModelArtifacts"]
    archive = read_bytes(s3, model_data)
    latest = f"{folder(models)}latest/"
    write_bytes(s3, f"{latest}model.tar.gz", archive)
    write_bytes(s3, f"{latest}evaluation.json", evaluation_bytes, "application/json")
    model = {
        "application": APPLICATION,
        "training_job": job,
        "model_data": model_data,
        "training_image": training_image,
        "serving_image": serving,
        "hyperparameters": dict(described.get("HyperParameters") or {}),
        "auc": auc,
        "sha256": sha256_hex(archive),
        "size_bytes": len(archive),
        "training_source": source,
        "published": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    write_json(s3, f"{latest}model.json", model)
    print(
        f"published {job}: sha256 {model['sha256']}, {len(archive)} bytes, AUC {auc}, "
        f"training source {source}, {latest}"
    )
    if source == "dirty":
        print("the training source is dirty: the release pipeline's guard refuses this candidate")
    return model


def publish(
    training: str,
    models: str,
    serving_image: str,
    training_source: str,
    min_auc: str,
    **context,
) -> str:
    """The task: `publish_model` with the worker's clients; model.json as JSON text, its XCom."""
    import boto3

    model = publish_model(
        boto3.client("sagemaker"),
        boto3.client("s3"),
        training,
        models,
        serving_image,
        training_source,
        min_auc,
    )
    return json.dumps(model, sort_keys=True) + "\n"
