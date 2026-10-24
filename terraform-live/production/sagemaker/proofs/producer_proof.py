"""Stage 9 step 2.4's proof job: the governed write pair and the drop-box pickup, as the job role.

Run by the Glue job awsds-prod-producer-proof (producer-proof.tf), one run per --MODE:

  producer   inserts the application's sample rows into curated.trades through the Production share,
             reads them back, then attempts a direct PutObject to the curated bucket as the job role
             and expects the refusal (INT-03's pair, D13);
  pickup     reads every CSV under the drop-box's dated prefix as the job role, curates the rows into
             the same table through the share, deletes what it consumed and reads each key gone
             (INT-10, D25).

The table is reached as <catalog>.<database>.<table> on the Iceberg catalog the job's --conf
declares over the lake account's Glue catalog, with Lake Formation vending the data credentials
(full-table-access mode); the drop-box and the direct put use the job role's own credentials, which
hold the pickup statements and nothing on a lake prefix. Every wording is printed as the service
gives it: the readings are the log, never the exit code alone (Lesson 13), and a negative that
succeeds fails the run loudly rather than passing as "a write happened".
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone

import boto3
from awsglue.utils import getResolvedOptions
from botocore.exceptions import ClientError
from pyspark.sql import SparkSession
from pyspark.sql.types import DateType, DoubleType, StringType, StructField, StructType

# examples/app-etl/samples/trades.csv, the rows the table was declared for (Stage 9 step 2.1).
SAMPLE_ROWS = [
    ("2026-10-01", "rates", "UST10Y", 120.0, 98.50),
    ("2026-10-01", "fx", "EURUSD", 500.0, 1.08),
    ("2026-10-02", "rates", "UST2Y", 80.0, 99.75),
    ("2026-10-02", "credit", "IG5Y", 40.0, 101.20),
    ("2026-10-03", "fx", "USDBRL", 250.0, 5.42),
    ("2026-10-03", "rates", "UST10Y", 60.0, 98.25),
    ("2026-10-04", "credit", "HY5Y", 30.0, 95.10),
    ("2026-10-04", "fx", "EURUSD", 300.0, 1.09),
    ("2026-10-05", "rates", "UST2Y", 100.0, 99.80),
    ("2026-10-05", "credit", "IG5Y", 50.0, 101.05),
]

TRADES_SCHEMA = StructType(
    [
        StructField("trade_date", DateType(), False),
        StructField("desk", StringType(), False),
        StructField("instrument", StringType(), False),
        StructField("quantity", DoubleType(), False),
        StructField("price", DoubleType(), False),
    ]
)


def say(line: str) -> None:
    print(f"[producer-proof {datetime.now(timezone.utc).strftime('%H:%M:%SZ')}] {line}", flush=True)


def error_text(exc: ClientError) -> str:
    err = exc.response.get("Error", {})
    return f"{err.get('Code', '?')}: {err.get('Message', '?')}"


def table_ref(args: dict[str, str]) -> str:
    return f"{args['LAKE_CATALOG']}.{args['CURATED_DATABASE']}.{args['CURATED_TABLE']}"


def read_back(spark: SparkSession, table: str) -> int:
    """Count the rows through the share and print the newest ten, the reading of either mode."""
    count = spark.sql(f"SELECT count(*) AS n FROM {table}").collect()[0]["n"]
    say(f"{table} holds {count} row(s) through the share")
    for row in spark.sql(f"SELECT * FROM {table} ORDER BY trade_date DESC, desk, instrument LIMIT 10").collect():
        say(f"  {row['trade_date']} {row['desk']:<7} {row['instrument']:<7} {row['quantity']:>8.2f} @ {row['price']:.4f}")
    return int(count)


def producer(spark: SparkSession, args: dict[str, str]) -> None:
    """The governed write, then the direct put that must be refused (INT-03, D13)."""
    table = table_ref(args)
    say(f"producer: inserting {len(SAMPLE_ROWS)} sample rows into {table}")
    values = ", ".join(
        f"(CAST('{d}' AS DATE), '{desk}', '{instrument}', {quantity!r}, {price!r})"
        for d, desk, instrument, quantity, price in SAMPLE_ROWS
    )
    spark.sql(f"INSERT INTO {table} VALUES {values}")
    say("producer: the insert committed")
    read_back(spark, table)

    key = "warehouse/trades/stage-09-producer-proof.txt"
    say(f"producer: direct PutObject to s3://{args['CURATED_BUCKET']}/{key} as the job role, expecting a refusal")
    s3 = boto3.client("s3")
    try:
        s3.put_object(Bucket=args["CURATED_BUCKET"], Key=key, Body=b"stage-09 producer proof\n")
    except ClientError as exc:
        say(f"producer: the direct put was refused: {error_text(exc)}")
        return
    # A put that lands is a hole in D13: say so, take the object back if the role can, and fail.
    say("producer: HOLE - the direct PutObject succeeded; the job role reaches a lake prefix outside Lake Formation")
    try:
        s3.delete_object(Bucket=args["CURATED_BUCKET"], Key=key)
        say("producer: the probe object was deleted")
    except ClientError as exc:
        say(f"producer: the probe object could not be deleted: {error_text(exc)}")
    raise SystemExit("D13 violated: the direct put to the curated bucket succeeded")


def pickup(spark: SparkSession, args: dict[str, str]) -> None:
    """The drop-box curated into the governed table and emptied (INT-10, D25)."""
    bucket, prefix = args["DROPBOX_BUCKET"], args["DROPBOX_PREFIX"].strip("/") + "/"
    s3 = boto3.client("s3")
    keys: list[str] = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket, Prefix=prefix):
        keys.extend(item["Key"] for item in page.get("Contents", []) if item["Key"].lower().endswith(".csv"))
    if not keys:
        # An empty letterbox is not a pickup: a run that reads nothing and succeeds would read as the
        # proof passing (Lesson 13).
        raise SystemExit(f"pickup: nothing to pick up under s3://{bucket}/{prefix}")
    say(f"pickup: {len(keys)} CSV object(s) under s3://{bucket}/{prefix}: {', '.join(keys)}")

    picked = spark.read.csv([f"s3://{bucket}/{k}" for k in keys], header=True, schema=TRADES_SCHEMA)
    rows = picked.count()
    say(f"pickup: {rows} row(s) read as the job role, under the lake data key (the KMS half)")
    picked.createOrReplaceTempView("picked")
    table = table_ref(args)
    spark.sql(f"INSERT INTO {table} SELECT trade_date, desk, instrument, quantity, price FROM picked")
    say(f"pickup: {rows} row(s) curated into {table}")
    read_back(spark, table)

    for key in keys:
        s3.delete_object(Bucket=bucket, Key=key)
        try:
            s3.head_object(Bucket=bucket, Key=key)
        except ClientError as exc:
            say(f"pickup: deleted s3://{bucket}/{key}; a read after the delete answers {error_text(exc)}")
        else:
            raise SystemExit(f"pickup: s3://{bucket}/{key} still answers after its delete")
    say("pickup: the letterbox is empty")


def main() -> None:
    args = getResolvedOptions(
        sys.argv,
        ["MODE", "LAKE_CATALOG", "CURATED_DATABASE", "CURATED_TABLE", "CURATED_BUCKET", "DROPBOX_BUCKET", "DROPBOX_PREFIX"],
    )
    say(f"running as {boto3.client('sts').get_caller_identity()['Arn']}, mode {args['MODE']}")
    spark = SparkSession.builder.getOrCreate()
    if args["MODE"] == "producer":
        producer(spark, args)
    elif args["MODE"] == "pickup":
        pickup(spark, args)
    else:
        raise SystemExit(f"unknown --MODE {args['MODE']!r}: producer or pickup")
    say("done")


if __name__ == "__main__":
    main()
