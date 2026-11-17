"""The Glue job of app-dbt: the trades of the application's inbox as the Iceberg table the dbt
project reads as its source.

The job reads every CSV under --SOURCE_PATH, the inbox the samples seed, and writes the rows as the
Iceberg table --TABLE_NAME of the project's database --TABLE_DATABASE, on the Spark catalog
PRODUCT_CATALOG the job's --conf declares over the account's Glue Data Catalog, then reads the table
back and counts it against the rows read. The Glue table is the job's own `CreateTable`, under the
database's conditioned CREATE_TABLE; a second run replaces the data and keeps the table. Its files
land at the database's location followed by the table's name, whatever warehouse the --conf names.
An empty option stops the run, since a run the portal starts fills no stage variable.

Glue 6.0 runs it; the test runs it over doubles of awsglue and pyspark. What it prints are counts,
names and paths, never a value of the data.
"""

from __future__ import annotations

import sys

from awsglue.utils import getResolvedOptions
from pyspark.sql import DataFrame, SparkSession

# The Spark catalog over the account's Glue Data Catalog, which the workflow's --conf declares with
# Iceberg's GlueCatalog; the table's name is <catalog>.<database>.<table>.
PRODUCT_CATALOG = "glue_catalog"
OPTIONS = ("SOURCE_PATH", "TABLE_DATABASE", "TABLE_NAME")


def table_name(arguments: dict[str, str]) -> str:
    """`<catalog>.<database>.<table>`; an option without a value stops the run, naming it."""
    empty = [f"--{name}" for name in OPTIONS if not arguments.get(name)]
    if empty:
        raise ValueError(f"{' and '.join(empty)} must have a value; the run gives none")
    return f"{PRODUCT_CATALOG}.{arguments['TABLE_DATABASE']}.{arguments['TABLE_NAME']}"


def read_trades(spark: SparkSession, path: str) -> DataFrame:
    """Every CSV under `path`, its header naming the columns."""
    print(f"reading {path}")
    return spark.read.option("header", True).option("inferSchema", True).csv(path)


def write_table(spark: SparkSession, trades: DataFrame, name: str, rows: int) -> None:
    """The trades as the Iceberg table `name`, replaced on each run, read back: a count other than
    `rows` fails the run."""
    trades.write.format("iceberg").mode("overwrite").saveAsTable(name)
    written = spark.table(name).count()
    if written != rows:
        raise RuntimeError(f"{name} reads {written} row(s) back, {rows} written")
    print(f"wrote {rows} row(s) to the table {name}")


def main() -> None:
    arguments = getResolvedOptions(sys.argv, list(OPTIONS))
    name = table_name(arguments)
    spark = SparkSession.builder.getOrCreate()
    trades = read_trades(spark, arguments["SOURCE_PATH"])
    rows = trades.count()
    print(f"read {rows} row(s)")
    write_table(spark, trades, name, rows)


if __name__ == "__main__":
    main()
