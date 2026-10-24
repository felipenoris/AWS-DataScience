"""The Glue job: the Spark transform over the trades, as a Visual ETL custom-code node holds it.

The job reads the trades, applies `transform` and writes what the next steps read:

- the result as one CSV with a header, the object --TARGET_PATH, which the processing job reads.
  Spark names the file it writes (`part-00000-<uuid>-c000.csv`) and offers no way to choose, so
  the job writes into the target's prefix, which the overwrite empties first, then copies the part
  file to the target's key and deletes what Spark wrote, with the boto3 the Glue worker carries;
- with --TABLE_PATH, the application's table as Parquet under that prefix, read back and counted
  against the rows read: the table the application slice declares in app_outputs, and the
  integration test of a deployment target (Stage 9 step 8.5);
- with --TRAIN_PATH, the training sets in XGBoost's CSV layout, the label first and no header:
  `train/train.csv`, every fifth row in `validation/validation.csv`, and the features alone in
  `batch/batch.csv`, the batch transform's input (Stage 10 steps 5.1 and 5.4).

Where the trades come from: with --SOURCE_TABLE, the governed table on the job's Iceberg catalog,
pinned to --SOURCE_SNAPSHOT when one is given, the columns GOVERNED_COLUMNS name and nothing else,
so a governed table that lacks one of them fails the run naming the column; without it, every CSV
under --SOURCE_PATH, the inbox the samples seed. The Sandbox projects run the inbox path; the
application slice of a deployment target gives the job --SOURCE_TABLE and the catalog.

A second run overwrites every output. Glue 6.0 runs it; the test runs it over doubles of awsglue,
pyspark and boto3. What it prints are counts, names and paths, never a value of the data.
"""

from __future__ import annotations

import io
import sys
from urllib.parse import urlparse

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

# The application's schema source: the columns it reads from the governed table, in order.
GOVERNED_COLUMNS = ("trade_date", "desk", "instrument", "quantity", "price")

# The training sets: the label XGBoost learns and the features it learns it from.
LABEL = "notional"
FEATURES = ("quantity", "price")
VALIDATION_EVERY = 5

OPTIONAL = ("SOURCE_TABLE", "SOURCE_SNAPSHOT", "TABLE_PATH", "TRAIN_PATH")


def transform(trades: DataFrame) -> DataFrame:
    """Each trade gains its notional, quantity times price, rounded to cents."""
    return trades.withColumn("notional", F.round(F.col("quantity") * F.col("price"), 2))


def split_uri(uri: str) -> tuple[str, str]:
    """`s3://bucket/key` -> (`bucket`, `key`)."""
    parsed = urlparse(uri)
    return parsed.netloc, parsed.path.lstrip("/")


def optional_options(argv: list[str], names: tuple[str, ...]) -> dict[str, str]:
    """The options of `names` that `argv` carries: getResolvedOptions refuses an absent one."""
    present = [name for name in names if f"--{name}" in argv]
    return getResolvedOptions(argv, present) if present else {}


def governed_query(table: str, columns: tuple[str, ...], snapshot: str | None) -> str:
    """The governed read: the named columns of `table`, at `snapshot` when one is given."""
    query = f"SELECT {', '.join(columns)} FROM {table}"
    if snapshot:
        query += f" VERSION AS OF {int(snapshot)}"
    return query


def missing_columns(available: list[str], wanted: tuple[str, ...]) -> list[str]:
    """The columns of `wanted` that `available` lacks, in `wanted`'s order."""
    return [name for name in wanted if name not in available]


def read_source(spark: SparkSession, arguments: dict[str, str]) -> DataFrame:
    """The trades: the governed table when --SOURCE_TABLE names one, the inbox's CSVs otherwise."""
    table = arguments.get("SOURCE_TABLE")
    if not table:
        print(f"reading {arguments['SOURCE_PATH']}")
        return (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .csv(arguments["SOURCE_PATH"])
        )
    missing = missing_columns(spark.table(table).columns, GOVERNED_COLUMNS)
    if missing:
        raise RuntimeError(
            f"{table} lacks {', '.join(missing)}: the application's schema source and the "
            "governed table disagree"
        )
    query = governed_query(table, GOVERNED_COLUMNS, arguments.get("SOURCE_SNAPSHOT"))
    print(f"reading {query}")
    return spark.sql(query)


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


def write_table(spark: SparkSession, result: DataFrame, path: str, rows: int) -> None:
    """The application's table under `path`, read back: a count other than `rows` fails the run."""
    result.write.mode("overwrite").parquet(path)
    written = spark.read.parquet(path).count()
    if written != rows:
        raise RuntimeError(f"{path} reads {written} row(s) back, {rows} written")
    print(f"wrote {rows} row(s) to the table at {path}")


def training_sets(rows: list[dict]) -> dict[str, str]:
    """XGBoost's CSV layout, the label first and no header: the training and validation sets, and
    the batch transform's input, the features alone, by file name."""
    train, validation, batch = io.StringIO(), io.StringIO(), io.StringIO()
    for index, row in enumerate(rows):
        features = ",".join(str(row[name]) for name in FEATURES)
        target = validation if index % VALIDATION_EVERY == VALIDATION_EVERY - 1 else train
        target.write(f"{row[LABEL]},{features}\n")
        batch.write(f"{features}\n")
    return {
        "train/train.csv": train.getvalue(),
        "validation/validation.csv": validation.getvalue(),
        "batch/batch.csv": batch.getvalue(),
    }


def write_training_sets(result: DataFrame, path: str) -> None:
    """The three files of `training_sets` under the prefix `path`."""
    rows = [row.asDict() for row in result.select(LABEL, *FEATURES).collect()]
    bucket, prefix = split_uri(path.rstrip("/") + "/")
    s3 = boto3.client("s3")
    for name, body in training_sets(rows).items():
        s3.put_object(Bucket=bucket, Key=prefix + name, Body=body.encode())
        print(f"wrote s3://{bucket}/{prefix}{name}, {body.count(chr(10))} line(s)")


def main() -> None:
    arguments = getResolvedOptions(sys.argv, ["SOURCE_PATH", "TARGET_PATH"])
    arguments.update(optional_options(sys.argv, OPTIONAL))
    target = arguments["TARGET_PATH"]
    spark = SparkSession.builder.getOrCreate()
    trades = read_source(spark, arguments)
    rows = trades.count()
    print(f"read {rows} row(s)")
    result = trades.transform(transform)
    result.coalesce(1).write.option("header", True).mode("overwrite").csv(
        target[: target.rfind("/") + 1]
    )
    keep_one_file(target)
    print(f"wrote {target}")
    if arguments.get("TABLE_PATH"):
        write_table(spark, result, arguments["TABLE_PATH"], rows)
    if arguments.get("TRAIN_PATH"):
        write_training_sets(result, arguments["TRAIN_PATH"])


if __name__ == "__main__":
    main()
