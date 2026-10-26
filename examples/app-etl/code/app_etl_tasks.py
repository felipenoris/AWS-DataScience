"""The worker's tasks: the run's report, and the evaluation of a training job.

`summarize`, a task of app-etl, reads every `<name>.summary.json` under the prefix its
``op_kwargs`` name, the processing job's output, and returns the run's report as JSON text: the
task's XCom, which the workflow's last task writes to S3. `evaluate`, a task of app-etl-train, reads
the training job's final metrics and writes them beside its model as SageMaker's model-quality
statistics, the file the pipeline's registration names as the version's `ModelMetrics` (Stage 10
step 5.2), with the rows of the batch transform's input, which the transform's check counts against.

They run on the MWAA Serverless worker with the boto3 the worker carries, so a workflow's code
package is this file alone, zipped under the workflow's name. What they print lands in the
workflow's log group, so they print counts, names and metrics, never a value of the data.
"""

from __future__ import annotations

import ast
import json
from operator import itemgetter
from urllib.parse import urlparse


def split_uri(uri: str) -> tuple[str, str]:
    """`s3://bucket/prefix/` -> (`bucket`, `prefix/`)."""
    parsed = urlparse(uri)
    if parsed.scheme != "s3" or not parsed.netloc:
        raise ValueError(f"not an s3:// URI: {uri}")
    return parsed.netloc, parsed.path.lstrip("/")


def summaries(outputs: str) -> list[dict]:
    """Every `.summary.json` under the prefix `outputs`, parsed, in key order."""
    import boto3

    bucket, prefix = split_uri(outputs)
    s3 = boto3.client("s3")
    found = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        for item in page.get("Contents", []):
            if item["Key"].endswith(".summary.json"):
                body = s3.get_object(Bucket=bucket, Key=item["Key"])["Body"].read()
                found.append(json.loads(body))
    return found


def report(found: list[dict]) -> dict:
    """The run's report: one entry per table, by input name, with the governed table and snapshot
    it was read from when its summary names them, and the rows over all of them."""
    tables = []
    for summary in sorted(found, key=itemgetter("input")):
        sums = {name: stats["sum"] for name, stats in summary["numeric"].items()}
        entry = {
            "input": summary["input"],
            "sha256": summary["sha256"],
            "rows": summary["rows"],
            "sums": sums,
        }
        if "source" in summary:
            entry["source"] = summary["source"]
        tables.append(entry)
    return {"tables": tables, "rows": sum(table["rows"] for table in tables)}


def summarize(outputs: str, **context) -> str:
    """The report of the summaries under `outputs`, as JSON text: the task's XCom."""
    found = summaries(outputs)
    if not found:
        raise RuntimeError(f"no .summary.json under {outputs}")
    result = report(found)
    print(f"{len(result['tables'])} table(s), {result['rows']} rows, under {outputs}")
    return json.dumps(result, indent=2, sort_keys=True) + "\n"


# The training job's final metric the evaluation reports, as XGBoost names it with a validation
# channel and `eval_metric: rmse`.
VALIDATION_METRIC = "validation:rmse"


def model_quality(training: dict) -> dict:
    """SageMaker's model-quality statistics for a regression, from a training job's description."""
    metrics = {m["MetricName"]: m["Value"] for m in training.get("FinalMetricDataList", [])}
    if VALIDATION_METRIC not in metrics:
        raise RuntimeError(f"{training['TrainingJobName']} reports no {VALIDATION_METRIC}")
    return {
        "version": 0.0,
        "regression_metrics": {
            "rmse": {"value": metrics[VALIDATION_METRIC], "standard_deviation": "NaN"}
        },
    }


def training_job_name(training: str | dict) -> str:
    """The job's name in the train task's XCom, which reaches a template as JSON text.

    The worker renders an XCom as the JSON of its value (read 2026-10-24 in Staging: indexing the
    training operator's XCom failed on a string), so the text is decoded until the operator's dict
    appears; a dict, and the Python literal a template renders one as, are read too.
    """
    value = training
    for _ in range(3):
        if not isinstance(value, str):
            break
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            try:
                value = ast.literal_eval(value)
            except (ValueError, SyntaxError) as exc:
                raise RuntimeError("the train task's XCom is neither JSON nor a literal") from exc
    try:
        return value["Training"]["TrainingJobName"]
    except (KeyError, TypeError) as exc:
        shape = sorted(value) if isinstance(value, dict) else type(value).__name__
        raise RuntimeError(f"the train task's XCom names no training job: {shape}") from exc


def evaluate(training: str, batch: str, models: str, **context) -> str:
    """The evaluation of the job the train task's XCom names, written to
    `<models><job>/evaluation.json`; its JSON."""
    import boto3

    training_job = training_job_name(training)
    training = boto3.client("sagemaker").describe_training_job(TrainingJobName=training_job)
    if training["TrainingJobStatus"] != "Completed":
        raise RuntimeError(f"{training_job} is {training['TrainingJobStatus']}, not Completed")
    s3 = boto3.client("s3")
    batch_bucket, batch_key = split_uri(batch)
    body = s3.get_object(Bucket=batch_bucket, Key=batch_key)["Body"].read()
    rows = body.decode().count("\n")
    evaluation = model_quality(training)
    evaluation["awsds"] = {
        "training_job": training_job,
        "model_data": training["ModelArtifacts"]["S3ModelArtifacts"],
        "batch_rows": rows,
    }
    bucket, prefix = split_uri(models)
    key = f"{prefix}{training_job}/evaluation.json"
    s3.put_object(Bucket=bucket, Key=key, Body=json.dumps(evaluation, indent=2).encode())
    rmse = evaluation["regression_metrics"]["rmse"]["value"]
    print(f"{training_job}: {VALIDATION_METRIC} {rmse}, {rows} batch row(s), s3://{bucket}/{key}")
    return json.dumps(evaluation, sort_keys=True) + "\n"
