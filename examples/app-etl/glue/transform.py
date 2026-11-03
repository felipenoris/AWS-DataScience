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
  `batch/batch.csv`, the batch transform's input (Stage 10 steps 5.1 and 5.4);
- with --TABLE_DATABASE and --TABLE_NAME, both or neither, the product: the result as an Iceberg
  table of the project's database, on the Spark catalog PRODUCT_CATALOG the job's --conf declares
  over the account's Glue Data Catalog, read back and counted (Stage 19 decision 2). The Glue table
  is the job's own `CreateTable`, under the database's conditioned CREATE_TABLE; a second run
  replaces the data and keeps the table, its listing and its grants. An empty value is no value,
  since a run the portal starts fills no stage variable.

Where the trades come from: with --SOURCE_TABLE, the governed table on the job's Iceberg catalog,
the columns GOVERNED_COLUMNS name and nothing else, so a governed table that lacks one of them fails
the run naming the column; without it, every CSV under --SOURCE_PATH, the inbox the samples seed.
The Sandbox projects run the inbox path; the application slice of a deployment target gives the job
--SOURCE_TABLE and the catalog.

A governed read is read at one snapshot, the one --SOURCE_SNAPSHOT names or else the table's current
one, and the job writes which beside the CSV: `<stem>.source.json` under --TARGET_PATH's prefix, the
table, the snapshot and whether it was pinned, which the processing job copies into its summary. A
table that reports no current snapshot fails the run. The inbox path leaves no record.

A second run overwrites every output. Glue 6.0 runs it; the test runs it over doubles of awsglue,
pyspark and boto3. What it prints are counts, names and paths, never a value of the data.
"""

from __future__ import annotations

import io
import json
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

OPTIONAL = (
    "SOURCE_TABLE",
    "SOURCE_SNAPSHOT",
    "TABLE_PATH",
    "TRAIN_PATH",
    "TABLE_DATABASE",
    "TABLE_NAME",
)

# The governed read's record, beside the CSV it describes; the processing job reads the same name.
RECORD_SUFFIX = ".source.json"

# The Spark catalog over the account's Glue Data Catalog, which the workflow's --conf declares with
# Iceberg's GlueCatalog; the product table's name is <catalog>.<database>.<table>.
PRODUCT_CATALOG = "glue_catalog"
PRODUCT_OPTIONS = ("TABLE_DATABASE", "TABLE_NAME")


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


def governed_query(table: str, columns: tuple[str, ...], snapshot: int | str | None) -> str:
    """The governed read: the named columns of `table`, at `snapshot` when one is given."""
    query = f"SELECT {', '.join(columns)} FROM {table}"
    if snapshot:
        query += f" VERSION AS OF {int(snapshot)}"
    return query


def missing_columns(available: list[str], wanted: tuple[str, ...]) -> list[str]:
    """The columns of `wanted` that `available` lacks, in `wanted`'s order."""
    return [name for name in wanted if name not in available]


def current_snapshot(spark: SparkSession, table: str) -> int:
    """The snapshot `table` reads at now: the `current-snapshot-id` Iceberg reports to Spark."""
    rows = spark.sql(f"SHOW TBLPROPERTIES {table} ('current-snapshot-id')").collect()
    value = str(rows[0]["value"]) if rows else ""
    if not value.isdigit():
        raise RuntimeError(f"{table} reports no current snapshot to read at: {value!r}")
    return int(value)


def read_source(spark: SparkSession, arguments: dict[str, str]) -> tuple[DataFrame, dict | None]:
    """The trades and the record of their source: the governed table at a snapshot when
    --SOURCE_TABLE names one, the inbox's CSVs and no record otherwise."""
    table = arguments.get("SOURCE_TABLE")
    if not table:
        print(f"reading {arguments['SOURCE_PATH']}")
        trades = (
            spark.read.option("header", True)
            .option("inferSchema", True)
            .csv(arguments["SOURCE_PATH"])
        )
        return trades, None
    missing = missing_columns(spark.table(table).columns, GOVERNED_COLUMNS)
    if missing:
        raise RuntimeError(
            f"{table} lacks {', '.join(missing)}: the application's schema source and the "
            "governed table disagree"
        )
    pinned = arguments.get("SOURCE_SNAPSHOT")
    snapshot = int(pinned) if pinned else current_snapshot(spark, table)
    query = governed_query(table, GOVERNED_COLUMNS, snapshot)
    print(f"reading {query}")
    return spark.sql(query), {"table": table, "snapshot_id": snapshot, "pinned": bool(pinned)}


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


def write_record(target: str, record: dict) -> None:
    """The governed read's record beside `target`, `<stem>.source.json`."""
    bucket, key = split_uri(target)
    stem = key[: -len(".csv")] if key.lower().endswith(".csv") else key
    s3 = boto3.client("s3")
    body = json.dumps(record, sort_keys=True) + "\n"
    s3.put_object(Bucket=bucket, Key=stem + RECORD_SUFFIX, Body=body.encode())
    print(f"wrote s3://{bucket}/{stem}{RECORD_SUFFIX}, snapshot {record['snapshot_id']}")


def write_table(spark: SparkSession, result: DataFrame, path: str, rows: int) -> None:
    """The application's table under `path`, read back: a count other than `rows` fails the run."""
    result.write.mode("overwrite").parquet(path)
    written = spark.read.parquet(path).count()
    if written != rows:
        raise RuntimeError(f"{path} reads {written} row(s) back, {rows} written")
    print(f"wrote {rows} row(s) to the table at {path}")


def product_table(arguments: dict[str, str]) -> str | None:
    """`<catalog>.<database>.<table>` when the run names both options with a value, None when it
    names neither; one without the other stops the run."""
    named = [name for name in PRODUCT_OPTIONS if arguments.get(name)]
    if not named:
        return None
    if len(named) != len(PRODUCT_OPTIONS):
        raise ValueError(f"--TABLE_DATABASE and --TABLE_NAME go together; the run names {named}")
    return f"{PRODUCT_CATALOG}.{arguments['TABLE_DATABASE']}.{arguments['TABLE_NAME']}"


def write_product_table(spark: SparkSession, result: DataFrame, name: str, rows: int) -> None:
    """The product as the Iceberg table `name`, replaced on each run, read back: a count other than
    `rows` fails the run."""
    result.write.format("iceberg").mode("overwrite").saveAsTable(name)
    written = spark.table(name).count()
    if written != rows:
        raise RuntimeError(f"{name} reads {written} row(s) back, {rows} written")
    print(f"wrote {rows} row(s) to the product table {name}")


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
    trades, record = read_source(spark, arguments)
    rows = trades.count()
    print(f"read {rows} row(s)")
    result = trades.transform(transform)
    result.coalesce(1).write.option("header", True).mode("overwrite").csv(
        target[: target.rfind("/") + 1]
    )
    keep_one_file(target)
    print(f"wrote {target}")
    # After keep_one_file, which deletes every other object under the target's prefix.
    if record:
        write_record(target, record)
    if arguments.get("TABLE_PATH"):
        write_table(spark, result, arguments["TABLE_PATH"], rows)
    product = product_table(arguments)
    if product:
        write_product_table(spark, result, product, rows)
    if arguments.get("TRAIN_PATH"):
        write_training_sets(result, arguments["TRAIN_PATH"])


if __name__ == "__main__":
    main()
