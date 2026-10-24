"""The warehouse load: the application's table written into the governed warehouse (Stage 9 9.4).

Production alone runs it, as the Glue job awsds-prod-app-etl-load under awsds-prod-job-exec, the
one task of the workflow awsds-prod-wf-app-etl-warehouse, which its own chain starts (Stage 9
decision 15). Staging has no warehouse, so nothing rehearses it there.

The job reads the table app-etl wrote under --TABLE_PATH, asks Redshift Serverless for temporary
credentials on --DATABASE (GetCredentials, through VPC-Workloads' redshift-serverless endpoint), and
connects to the workgroup --WORKGROUP on its endpoint's port from the job's security group, which
the warehouse's group admits (9.1), with the Amazon Redshift JDBC driver Glue provides to its Spark
jobs. The session is the job role's database user, `IAMR:awsds-prod-job-exec`, which 9.3 created
with the role that writes the schema. In one transaction it deletes the rows of the trade dates it
carries and inserts its own, so a second run of the same table leaves the same rows; then it counts
those dates' rows, and a count other than its rows fails the run.

The table is the deployer's, created by the pipeline's DDL (warehouse/trades.sql); this role writes
it through the default privileges 9.3 gave the deployer's tables. A workgroup that does not exist
fails the run at GetWorkgroup: the compute is raised by hand, and its usage limit refuses queries
once it is breached (9.4). What the job prints are counts and names, never a value of the data.
"""

from __future__ import annotations

import sys

import boto3
from awsglue.utils import getResolvedOptions
from pyspark.sql import SparkSession

COLUMNS = ("trade_date", "desk", "instrument", "quantity", "price", "notional")
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
        sys.argv, ["TABLE_PATH", "WORKGROUP", "DATABASE", "TARGET_TABLE"]
    )
    spark = SparkSession.builder.getOrCreate()
    frame = spark.read.parquet(arguments["TABLE_PATH"]).select(*COLUMNS)
    rows = [row.asDict() for row in frame.collect()]
    if not rows:
        raise RuntimeError(f"no row under {arguments['TABLE_PATH']}: app-etl's run comes first")
    print(f"read {len(rows)} row(s) from {arguments['TABLE_PATH']}")

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
