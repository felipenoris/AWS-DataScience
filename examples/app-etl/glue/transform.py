"""The Glue job: the Spark transform over the trades, as a Visual ETL custom-code node holds it.

The job reads every CSV under --SOURCE_PATH, with a header and the types Spark infers, applies
`transform` and writes the result as one CSV with a header, the object --TARGET_PATH. Spark names
the file it writes (`part-00000-<uuid>-c000.csv`) and offers no way to choose, so the job writes
into the target's prefix, which the overwrite empties first, then copies the part file to the
target's key and deletes what Spark wrote, with the boto3 the Glue worker carries. A second run
overwrites the one object, so the processing job that reads the prefix finds one file and names
its outputs after it. Glue 6.0 runs it; the test runs it over doubles of awsglue, pyspark and boto3.
"""

from __future__ import annotations

import sys
from urllib.parse import urlparse

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F


def transform(trades: DataFrame) -> DataFrame:
    """Each trade gains its notional, quantity times price, rounded to cents."""
    return trades.withColumn("notional", F.round(F.col("quantity") * F.col("price"), 2))


def split_uri(uri: str) -> tuple[str, str]:
    """`s3://bucket/key` -> (`bucket`, `key`)."""
    parsed = urlparse(uri)
    return parsed.netloc, parsed.path.lstrip("/")


def keep_one_file(target: str) -> None:
    """Copy the part file Spark wrote in `target`'s prefix to `target`; delete what Spark wrote."""
    bucket, key = split_uri(target)
    prefix = key[: key.rfind("/") + 1]
    s3 = boto3.client("s3")
    written = s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get("Contents", [])
    parts = [item["Key"] for item in written if item["Key"].rsplit("/", 1)[-1].startswith("part-")]
    if len(parts) != 1:
        raise RuntimeError(f"one part file expected under s3://{bucket}/{prefix}, found {parts}")
    s3.copy_object(Bucket=bucket, Key=key, CopySource={"Bucket": bucket, "Key": parts[0]})
    leftovers = [{"Key": item["Key"]} for item in written if item["Key"] != key]
    s3.delete_objects(Bucket=bucket, Delete={"Objects": leftovers})


def main() -> None:
    arguments = getResolvedOptions(sys.argv, ["SOURCE_PATH", "TARGET_PATH"])
    target = arguments["TARGET_PATH"]
    spark = SparkSession.builder.getOrCreate()
    trades = (
        spark.read.option("header", True).option("inferSchema", True).csv(arguments["SOURCE_PATH"])
    )
    result = trades.transform(transform)
    result.coalesce(1).write.option("header", True).mode("overwrite").csv(
        target[: target.rfind("/") + 1]
    )
    keep_one_file(target)
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
