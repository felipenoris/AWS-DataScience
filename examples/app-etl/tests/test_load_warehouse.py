"""The warehouse load, run over doubles of awsglue, pyspark, boto3 and the JVM's JDBC: the
statements it prepares, the transaction it commits or rolls back, and the count that fails it."""

from __future__ import annotations

import datetime
import runpy
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "glue" / "load_warehouse.py"
TABLE_PATH = "s3://bucket/app-etl/tables/trades_notional/"
TARGET = "trades.trades_notional"
ROWS = [
    {
        "trade_date": datetime.date(2026, 10, 1),
        "desk": "rates",
        "instrument": "UST10Y",
        "quantity": 120.0,
        "price": 98.5,
        "notional": 11820.0,
    },
    {
        "trade_date": datetime.date(2026, 10, 2),
        "desk": "fx",
        "instrument": "EURUSD",
        "quantity": 500.0,
        "price": 1.08,
        "notional": 540.0,
    },
]


class FakeStatement:
    def __init__(self, sql, log, counted, refuse_insert=False):
        self.sql = sql
        self.log = log
        self.counted = counted
        self.refuse_insert = refuse_insert
        self.values = {}
        self.batches = []

    def setString(self, index, value):
        self.values[index] = value

    def setDouble(self, index, value):
        self.values[index] = value

    def addBatch(self):
        self.batches.append(dict(self.values))

    def executeUpdate(self):
        self.log.append(("update", self.sql, dict(self.values)))
        return 3

    def executeBatch(self):
        if self.refuse_insert:
            raise RuntimeError("insert refused")
        self.log.append(("batch", self.sql, list(self.batches)))
        return [1] * len(self.batches)

    def executeQuery(self):
        self.log.append(("query", self.sql, dict(self.values)))
        counted = self.counted
        return types.SimpleNamespace(
            next=lambda: True,
            getLong=lambda index: counted,
            getString=lambda index: "IAMR:awsds-prod-job-exec",
        )


class FakeConnection:
    def __init__(self, log, counted, refuse_insert=False):
        self.log = log
        self.counted = counted
        self.refuse_insert = refuse_insert

    def setAutoCommit(self, value):
        self.log.append(("autocommit", value))

    def prepareStatement(self, sql):
        return FakeStatement(sql, self.log, self.counted, self.refuse_insert)

    def commit(self):
        self.log.append("commit")

    def rollback(self):
        self.log.append("rollback")

    def close(self):
        self.log.append("close")


def modules(log, counted):
    """awsglue, pyspark and boto3 doubled; the JVM's DriverManager hands out a FakeConnection."""

    def resolved_options(argv, names):
        return {name: argv[argv.index(f"--{name}") + 1] for name in names}

    class Serverless:
        def get_workgroup(self, workgroupName):
            log.append(("get_workgroup", workgroupName))
            return {"workgroup": {"endpoint": {"address": "wg.example", "port": 5439}}}

        def get_credentials(self, workgroupName, dbName, durationSeconds):
            log.append(("get_credentials", workgroupName, dbName, durationSeconds))
            return {"dbUser": "IAMR:awsds-prod-job-exec", "dbPassword": "temporary"}

    properties = {}
    jvm = types.SimpleNamespace(
        java=types.SimpleNamespace(
            lang=types.SimpleNamespace(
                Class=types.SimpleNamespace(forName=lambda name: log.append(("driver", name)))
            ),
            util=types.SimpleNamespace(
                Properties=lambda: types.SimpleNamespace(setProperty=properties.__setitem__)
            ),
            sql=types.SimpleNamespace(
                DriverManager=types.SimpleNamespace(
                    getConnection=lambda url, props: (
                        log.append(("connect", url, dict(properties)))
                        or FakeConnection(log, counted)
                    )
                )
            ),
        )
    )
    frame = types.SimpleNamespace(
        select=lambda *names: frame,
        collect=lambda: [types.SimpleNamespace(asDict=lambda row=row: dict(row)) for row in ROWS],
    )
    session = types.SimpleNamespace(
        read=types.SimpleNamespace(parquet=lambda path: log.append(("read", path)) or frame),
        sparkContext=types.SimpleNamespace(_gateway=types.SimpleNamespace(jvm=jvm)),
    )
    sql = types.ModuleType("pyspark.sql")
    sql.SparkSession = types.SimpleNamespace(
        builder=types.SimpleNamespace(getOrCreate=lambda: session)
    )
    utils = types.ModuleType("awsglue.utils")
    utils.getResolvedOptions = resolved_options
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: Serverless()
    return {
        "awsglue": types.ModuleType("awsglue"),
        "awsglue.utils": utils,
        "pyspark": types.ModuleType("pyspark"),
        "pyspark.sql": sql,
        "boto3": boto3,
    }


def run_script(monkeypatch, counted=2):
    log = []
    for name, module in modules(log, counted).items():
        monkeypatch.setitem(sys.modules, name, module)
    argv = [
        "load_warehouse.py",
        "--TABLE_PATH",
        TABLE_PATH,
        "--WORKGROUP",
        "awsds-prod-warehouse",
        "--DATABASE",
        "governed",
        "--TARGET_TABLE",
        TARGET,
    ]
    monkeypatch.setattr(sys, "argv", argv)
    runpy.run_path(str(SCRIPT), run_name="__main__")
    return log


def test_the_load_deletes_and_inserts_in_one_transaction_then_counts(monkeypatch, capsys):
    log = run_script(monkeypatch)
    assert log[:4] == [
        ("read", TABLE_PATH),
        ("get_workgroup", "awsds-prod-warehouse"),
        ("get_credentials", "awsds-prod-warehouse", "governed", 900),
        ("driver", "com.amazon.redshift.jdbc42.Driver"),
    ]
    assert log[4] == (
        "connect",
        "jdbc:redshift://wg.example:5439/governed",
        {"user": "IAMR:awsds-prod-job-exec", "password": "temporary", "ssl": "true"},
    )
    assert log[5] == ("autocommit", False)
    kind, sql, values = log[6]
    assert kind == "update"
    assert sql == f"DELETE FROM {TARGET} WHERE trade_date IN (CAST(? AS DATE), CAST(? AS DATE))"
    assert values == {1: "2026-10-01", 2: "2026-10-02"}
    kind, sql, batches = log[7]
    assert kind == "batch"
    assert sql.startswith(f"INSERT INTO {TARGET} (trade_date, desk, instrument, quantity, price,")
    assert batches[1] == {1: "2026-10-02", 2: "fx", 3: "EURUSD", 4: 500.0, 5: 1.08, 6: 540.0}
    assert log[8] == "commit"
    assert log[-1] == "close"
    out = capsys.readouterr().out
    assert "3 row(s) deleted, 2 inserted, 2 counted for the load's dates" in out
    assert "temporary" not in out


def test_a_count_other_than_the_rows_fails_the_run(monkeypatch):
    with pytest.raises(RuntimeError, match="3 row\\(s\\) counted for 2 loaded"):
        run_script(monkeypatch, counted=3)


def test_a_refused_insert_rolls_the_delete_back(monkeypatch):
    for name, module in modules([], 2).items():
        monkeypatch.setitem(sys.modules, name, module)
    load = runpy.run_path(str(SCRIPT), run_name="load_warehouse")["load"]
    log = []
    with pytest.raises(RuntimeError, match="insert refused"):
        load(FakeConnection(log, 2, refuse_insert=True), TARGET, ROWS)
    assert log[-1] == "rollback"
    assert "commit" not in log
