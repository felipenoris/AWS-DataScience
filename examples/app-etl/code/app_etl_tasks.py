"""The worker's tasks: the run's report, the publication of the product, and the evaluation of a
training job.

`summarize`, a task of app-etl, reads every `<name>.summary.json` under the prefix its
``op_kwargs`` name, the processing job's output, and returns the run's report as JSON text: the
task's XCom, which the workflow's next task writes to S3. `publish`, the last task of app-etl, puts
the product the Glue job wrote into the SageMaker Catalog the way the tool intends (Stage 19
decisions 3 and 14): it runs the project's data source over the product's database, finds the asset
the run imported for the table and publishes its latest revision as a listing, waiting for `ACTIVE`,
since the listing API answers before the listing exists and fails later on its own. It runs as the
project role through the `datazone` endpoint, in the domain and project the worker's environment
names, and returns at once where the stage variable `PUBLISH_LISTING` is not `true`, the stages
whose product is never listed. `evaluate`, a task of app-etl-train, reads the training job's final
metrics and writes them beside its model as SageMaker's model-quality statistics, the file the
pipeline's registration names as the version's `ModelMetrics` (Stage 10 step 5.2), with the rows of
the batch transform's input, which the transform's check counts against.

They run on the MWAA Serverless worker with the boto3 the worker carries, so a workflow's code
package is this file alone, zipped under the workflow's name. What they print lands in the
workflow's log group, so they print counts, names, identifiers and metrics, never a value of the
data.
"""

from __future__ import annotations

import ast
import json
import os
import time
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


# The publication: the worker's variables that name the project (the portal injects them), how long
# a source run and a listing may take before the task fails, and the seconds between two readings.
DOMAIN_VARIABLE = "DataZoneDomainId"
PROJECT_VARIABLE = "DataZoneProjectId"
SOURCE_RUN_TIMEOUT = 600
LISTING_TIMEOUT = 120
POLL_SECONDS = 5


def project_context() -> tuple[str, str]:
    """The domain and the project the worker runs in, from the variables the portal injects."""
    try:
        return os.environ[DOMAIN_VARIABLE], os.environ[PROJECT_VARIABLE]
    except KeyError as exc:
        raise RuntimeError(
            f"the worker carries no {exc.args[0]}: not a project's workflow"
        ) from exc


def find_source(datazone, domain: str, project: str, database: str) -> str:
    """The id of the project's one Glue data source whose filter names `database`."""
    found = []
    paginator = datazone.get_paginator("list_data_sources")
    for page in paginator.paginate(domainIdentifier=domain, projectIdentifier=project, type="GLUE"):
        for item in page.get("items", []):
            source = datazone.get_data_source(
                domainIdentifier=domain, identifier=item["dataSourceId"]
            )
            glue = source.get("configuration", {}).get("glueRunConfiguration", {})
            databases = [f["databaseName"] for f in glue.get("relationalFilterConfigurations", [])]
            if database in databases:
                found.append(item["dataSourceId"])
    if len(found) != 1:
        raise RuntimeError(
            f"{len(found)} data source(s) over {database} in the project, one expected"
        )
    return found[0]


def run_source(datazone, domain: str, source: str, timeout: int = SOURCE_RUN_TIMEOUT) -> str:
    """One run of the source, followed to SUCCESS; any other end, or `timeout` seconds, fails."""
    run = datazone.start_data_source_run(domainIdentifier=domain, dataSourceIdentifier=source)["id"]
    deadline = time.monotonic() + timeout
    while True:
        state = datazone.get_data_source_run(domainIdentifier=domain, identifier=run)
        status = state["status"]
        if status == "SUCCESS":
            counts = state.get("runStatisticsForAssets") or {}
            print(f"source run {run}: SUCCESS, {json.dumps(counts, sort_keys=True)}")
            return run
        if status not in ("REQUESTED", "RUNNING"):
            raise RuntimeError(f"source run {run} ended {status}: {state.get('errorMessage')}")
        if time.monotonic() >= deadline:
            raise RuntimeError(f"source run {run} still {status} after {timeout} s")
        time.sleep(POLL_SECONDS)


def find_asset(datazone, domain: str, project: str, database: str, table: str) -> dict:
    """The project's one inventory asset whose external identifier ends in `database/table`."""
    found = []
    paginator = datazone.get_paginator("search")
    pages = paginator.paginate(
        domainIdentifier=domain,
        searchScope="ASSET",
        owningProjectIdentifier=project,
        searchText=table,
    )
    for page in pages:
        for item in page.get("items", []):
            asset = item.get("assetItem") or {}
            external = asset.get("externalIdentifier") or ""
            if external.split("/")[-2:] == [database, table]:
                found.append(asset)
    if len(found) != 1:
        raise RuntimeError(
            f"{len(found)} asset(s) for {database}/{table} in the project, one expected"
        )
    return found[0]


def publish_asset(datazone, domain: str, asset: str, timeout: int = LISTING_TIMEOUT) -> dict:
    """The asset's latest revision published, and the listing read ACTIVE within `timeout`
    seconds."""
    change = datazone.create_listing_change_set(
        domainIdentifier=domain, entityIdentifier=asset, entityType="ASSET", action="PUBLISH"
    )
    listing, revision = change["listingId"], change["listingRevision"]
    deadline = time.monotonic() + timeout
    while True:
        status = datazone.get_listing(
            domainIdentifier=domain, identifier=listing, listingRevision=revision
        )["status"]
        if status == "ACTIVE":
            print(f"listing {listing} revision {revision}: ACTIVE")
            return {"listing": listing, "listing_revision": revision}
        if status != "CREATING":
            raise RuntimeError(f"listing {listing} revision {revision} is {status}")
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"listing {listing} revision {revision} not ACTIVE after {timeout} s"
            )
        time.sleep(POLL_SECONDS)


def publish(database: str, table: str, publish_listing: str, **context) -> str:
    """The product `database.table` imported and listed in the catalog; its identifiers as JSON
    text, the task's XCom. Nothing when `publish_listing`, the stage variable, is not `true`."""
    if str(publish_listing).strip().lower() != "true":
        print(f"publishing off in this stage (PUBLISH_LISTING={publish_listing!r}); nothing listed")
        return json.dumps({"published": False}) + "\n"
    import boto3

    domain, project = project_context()
    datazone = boto3.client("datazone")
    source = find_source(datazone, domain, project, database)
    run = run_source(datazone, domain, source)
    asset = find_asset(datazone, domain, project, database, table)
    result = {
        "published": True,
        "domain": domain,
        "project": project,
        "data_source": source,
        "source_run": run,
        "asset": asset["identifier"],
        "asset_revision": asset.get("latestRevision") or asset.get("revision"),
        **publish_asset(datazone, domain, asset["identifier"]),
    }
    print(f"published {database}.{table}: asset {result['asset']}, listing {result['listing']}")
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
