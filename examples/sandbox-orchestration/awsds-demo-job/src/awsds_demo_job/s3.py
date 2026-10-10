"""`python -m awsds_demo_job.s3 --bucket B --inbox PREFIX --outbox PREFIX`: the worker's mode.

Each object under the inbox prefix becomes a summary under `<outbox>/<UTC stamp>/`, and the
source is deleted only after its summary's write returned. It runs with whatever credentials
it is given: on the MWAA worker, the workflow's execution role, through the S3 gateway
endpoint. boto3 is imported inside `run`, so the processing job's mode never needs it.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone

from . import transform


def _prefix(value: str) -> str:
    return value if value.endswith("/") else value + "/"


def run(bucket: str, inbox: str, outbox: str, client=None) -> int:
    """Process every object under `inbox`; return how many were processed."""
    if client is None:
        import boto3

        client = boto3.client("s3")
    s3 = client
    inbox, outbox = _prefix(inbox), _prefix(outbox)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=inbox):
        keys += [o["Key"] for o in page.get("Contents", []) if not o["Key"].endswith("/")]
    for key in keys:
        name = key.rsplit("/", 1)[-1]
        summary = transform.summarize(name, s3.get_object(Bucket=bucket, Key=key)["Body"].read())
        target = f"{outbox}{stamp}/{transform.result_name(name)}"
        s3.put_object(Bucket=bucket, Key=target, Body=transform.render(summary))
        s3.delete_object(Bucket=bucket, Key=key)
        print(f"{name}: {summary['rows']} rows -> s3://{bucket}/{target}; source deleted")
    print(f"{len(keys)} object(s) processed")
    return len(keys)


def main(argv: list | None = None) -> int:
    parser = argparse.ArgumentParser(prog="awsds_demo_job.s3")
    parser.add_argument("--bucket", required=True)
    parser.add_argument("--inbox", required=True, help="key prefix the files arrive under")
    parser.add_argument("--outbox", required=True, help="key prefix the results go under")
    args = parser.parse_args(argv)
    print(f"python {sys.version.split()[0]} at {sys.executable}")
    # A run starts after the sensor saw a file, so an empty inbox is a failure to show.
    return 0 if run(args.bucket, args.inbox, args.outbox) else 1


if __name__ == "__main__":
    sys.exit(main())
