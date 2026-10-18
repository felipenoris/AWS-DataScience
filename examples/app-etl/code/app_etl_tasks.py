"""The worker's task: the run's report, from the summaries the processing job wrote.

`summarize` reads every `<name>.summary.json` under the prefix its ``op_kwargs`` name, the
processing job's output, and returns the run's report as JSON text: the task's XCom, which the
workflow's last task writes to S3. It runs on the MWAA Serverless worker with the boto3 the worker
carries, so the code package is this file alone, zipped. What it prints lands in the workflow's
log group, so it prints counts and names, never a value of the data.
"""

from __future__ import annotations

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
    """The run's report: one entry per table, by input name, and the rows over all of them."""
    tables = []
    for summary in sorted(found, key=itemgetter("input")):
        sums = {name: stats["sum"] for name, stats in summary["numeric"].items()}
        tables.append(
            {
                "input": summary["input"],
                "sha256": summary["sha256"],
                "rows": summary["rows"],
                "sums": sums,
            }
        )
    return {"tables": tables, "rows": sum(table["rows"] for table in tables)}


def summarize(outputs: str, **context) -> str:
    """The report of the summaries under `outputs`, as JSON text: the task's XCom."""
    found = summaries(outputs)
    if not found:
        raise RuntimeError(f"no .summary.json under {outputs}")
    result = report(found)
    print(f"{len(result['tables'])} table(s), {result['rows']} rows, under {outputs}")
    return json.dumps(result, indent=2, sort_keys=True) + "\n"
