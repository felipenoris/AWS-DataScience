"""The warehouse load: the application's product written into the governed warehouse (Stage 9 9.4).

Production alone runs it, as the Glue job app-etl-load-<project id> the workflow app-etl-warehouse
creates in the deployment project and runs as the project's role (Stage 19 decision 16 (b)); its
own chain starts the workflow (Stage 9 decision 15). Staging has no warehouse, so nothing rehearses
it there.

The job reads the product table app-etl wrote, --TABLE_NAME of --TABLE_DATABASE on the Spark catalog
PRODUCT_CATALOG the job's --conf declares over the account's Glue Data Catalog, asks Redshift
Serverless for temporary credentials on --DATABASE (GetCredentials, through VPC-Workloads'
redshift-serverless endpoint), and connects to the workgroup --WORKGROUP on its endpoint's port from
the project's security group, which the warehouse's group admits, with the Amazon Redshift JDBC
driver Glue provides to its Spark jobs. The session is the project role's database user,
`IAMR:<the role's name>`, which holds the role that writes the schema. In one transaction it deletes
the rows of the trade dates it carries and inserts its own, so a second run of the same table leaves
the same rows; then it counts those dates' rows, and a count other than its rows fails the run.

The warehouse table is the deployer's, created by the pipeline's DDL (warehouse/trades.sql); this
role writes it through the default privileges the deployer's tables carry. A workgroup that does
not exist fails the run at GetWorkgroup: the compute is raised by hand, and its usage limit refuses
queries once it is breached (9.4). What the job prints are counts and names, never a value of the
data.
"""

from __future__ import annotations

import sys

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

COLUMNS = ("trade_date", "desk", "instrument", "quantity", "price", "notional")
# The Spark catalog over the account's Glue Data Catalog, as glue/transform.py names it.
PRODUCT_CATALOG = "glue_catalog"
DRIVER = "com.amazon.redshift.jdbc42.Driver"
CREDENTIAL_SECONDS = 900


def jdbc_url(address: str, port: int, database: str) -> str:
    """The workgroup's JDBC URL for `database`."""
    return f"jdbc:redshift://{address}:{port}/{database}"


def date_list(count: int) -> str:
    """`count` date parameters, for a `trade_date IN (...)`."""
    return ", ".join(["CAST(? AS DATE)"] * count)


def delete_statement(table: str, dates: int) -> str:
    """The rows of `dates` trade dates, removed before their load."""
    return f"DELETE FROM {table} WHERE trade_date IN ({date_list(dates)})"


def insert_statement(table: str) -> str:
    """One row of COLUMNS, the date cast from its ISO text."""
    values = ", ".join(["CAST(? AS DATE)"] + ["?"] * (len(COLUMNS) - 1))
    return f"INSERT INTO {table} ({', '.join(COLUMNS)}) VALUES ({values})"


def count_statement(table: str, dates: int) -> str:
    """The rows of `dates` trade dates after the load, and the session's database user."""
    return f"SELECT count(*), current_user FROM {table} WHERE trade_date IN ({date_list(dates)})"


def load(connection, table: str, rows: list[dict]) -> tuple[int, int, int, str]:
    """Delete and insert in one transaction, then count: (deleted, inserted, counted, user)."""
    dates = sorted({str(row["trade_date"]) for row in rows})
    connection.setAutoCommit(False)
    try:
        delete = connection.prepareStatement(delete_statement(table, len(dates)))
        for index, day in enumerate(dates, start=1):
            delete.setString(index, day)
        deleted = delete.executeUpdate()
        insert = connection.prepareStatement(insert_statement(table))
        for row in rows:
            insert.setString(1, str(row["trade_date"]))
            insert.setString(2, row["desk"])
            insert.setString(3, row["instrument"])
            insert.setDouble(4, float(row["quantity"]))
            insert.setDouble(5, float(row["price"]))
            insert.setDouble(6, float(row["notional"]))
            insert.addBatch()
        inserted = sum(list(insert.executeBatch()))
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    count = connection.prepareStatement(count_statement(table, len(dates)))
    for index, day in enumerate(dates, start=1):
        count.setString(index, day)
    result = count.executeQuery()
    result.next()
    return deleted, inserted, result.getLong(1), result.getString(2)


def main() -> None:
    arguments = getResolvedOptions(
        sys.argv, ["TABLE_DATABASE", "TABLE_NAME", "WORKGROUP", "DATABASE", "TARGET_TABLE"]
    )
    source = f"{PRODUCT_CATALOG}.{arguments['TABLE_DATABASE']}.{arguments['TABLE_NAME']}"
    spark = SparkSession.builder.getOrCreate()
    frame = spark.table(source).select(*COLUMNS)
    rows = [row.asDict() for row in frame.collect()]
    if not rows:
        raise RuntimeError(f"no row in {source}: app-etl's run comes first")
    print(f"read {len(rows)} row(s) from {source}")

    serverless = boto3.client("redshift-serverless")
    endpoint = serverless.get_workgroup(workgroupName=arguments["WORKGROUP"])["workgroup"][
        "endpoint"
    ]
    credentials = serverless.get_credentials(
        workgroupName=arguments["WORKGROUP"],
        dbName=arguments["DATABASE"],
        durationSeconds=CREDENTIAL_SECONDS,
    )
    url = jdbc_url(endpoint["address"], endpoint["port"], arguments["DATABASE"])
    print(f"connecting to {url} as {credentials['dbUser']}")

    jvm = spark.sparkContext._gateway.jvm
    jvm.java.lang.Class.forName(DRIVER)
    properties = jvm.java.util.Properties()
    properties.setProperty("user", credentials["dbUser"])
    properties.setProperty("password", credentials["dbPassword"])
    properties.setProperty("ssl", "true")
    connection = jvm.java.sql.DriverManager.getConnection(url, properties)
    try:
        deleted, inserted, counted, user = load(connection, arguments["TARGET_TABLE"], rows)
    finally:
        connection.close()
    print(
        f"{arguments['TARGET_TABLE']}: {deleted} row(s) deleted, {inserted} inserted, "
        f"{counted} counted for the load's dates, as {user}"
    )
    if counted != len(rows):
        raise RuntimeError(f"{counted} row(s) counted for {len(rows)} loaded")


if __name__ == "__main__":
    main()
