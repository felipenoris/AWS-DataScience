"""The Glue script, run over doubles of awsglue, pyspark and boto3: what it reads, the column it
adds, the one file it writes and the files it deletes; with its options, the governed read, the
application's table read back and the training sets."""

from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "glue" / "transform.py"
SOURCE = "s3://bucket/app-etl/inbox/"
TARGET = "s3://bucket/app-etl/work/glue/trades.csv"
PART = "app-etl/work/glue/part-00000-0f6a-c000.csv"
TABLE = "s3://bucket/app-etl/tables/trades_notional/"
TRAIN = "s3://bucket/app-etl/work/train/"
GOVERNED = "lake.curated.trades"
ROWS = [
    {"notional": 11820.0, "quantity": 120, "price": 98.5},
    {"notional": 540.0, "quantity": 500, "price": 1.08},
    {"notional": 7980.0, "quantity": 80, "price": 99.75},
    {"notional": 4048.0, "quantity": 40, "price": 101.2},
    {"notional": 1355.0, "quantity": 250, "price": 5.42},
    {"notional": 5895.0, "quantity": 60, "price": 98.25},
]
SCHEMA = ["trade_date", "desk", "instrument", "quantity", "price"]


class FakeColumn:
    """A column expression, kept as text."""

    def __init__(self, text):
        self.text = text

    def __mul__(self, other):
        return FakeColumn(f"({self.text} * {other.text})")


class FakeRow:
    def __init__(self, values):
        self.values = values

    def asDict(self):
        return dict(self.values)


class FakeWriter:
    def __init__(self, log):
        self.log = log
        self.options = {}
        self.save_mode = None

    def option(self, key, value):
        self.options[key] = value
        return self

    def mode(self, name):
        self.save_mode = name
        return self

    def csv(self, path):
        self.log["write"] = (path, self.options, self.save_mode)

    def parquet(self, path):
        self.log["table"] = (path, self.save_mode)


class FakeFrame:
    def __init__(self, log, rows=6):
        self.log = log
        self.rows = rows

    def withColumn(self, name, column):
        self.log.setdefault("columns", {})[name] = column.text
        return self

    def transform(self, function):
        return function(self)

    def coalesce(self, partitions):
        self.log["partitions"] = partitions
        return self

    def count(self):
        return self.rows

    def select(self, *names):
        self.log["selected"] = names
        return self

    def collect(self):
        return [FakeRow(row) for row in ROWS]

    @property
    def write(self):
        return FakeWriter(self.log)


class FakeReader:
    def __init__(self, log, read_back):
        self.log = log
        self.options = {}
        self.read_back = read_back

    def option(self, key, value):
        self.options[key] = value
        return self

    def csv(self, path):
        self.log["read"] = (path, self.options)
        return FakeFrame(self.log)

    def parquet(self, path):
        self.log["read_back"] = path
        return FakeFrame(self.log, rows=self.read_back)


class FakeSession:
    def __init__(self, log, read_back, columns):
        self.log = log
        self.read = FakeReader(log, read_back)
        self.columns = columns

    def table(self, name):
        self.log["described"] = name
        return types.SimpleNamespace(columns=self.columns)

    def sql(self, query):
        self.log["query"] = query
        return FakeFrame(self.log)


class FakeS3:
    """What Spark left under the target's prefix, and the copy, the delete and the puts."""

    def __init__(self, keys):
        self.keys = keys
        self.copied = []
        self.deleted = []
        self.put = {}

    def list_objects_v2(self, Bucket, Prefix):
        return {"Contents": [{"Key": key} for key in self.keys if key.startswith(Prefix)]}

    def copy_object(self, Bucket, Key, CopySource):
        self.copied.append((CopySource["Key"], Key))

    def delete_objects(self, Bucket, Delete):
        self.deleted.append([item["Key"] for item in Delete["Objects"]])

    def put_object(self, Bucket, Key, Body):
        self.put[f"s3://{Bucket}/{Key}"] = Body.decode()


def run_script(monkeypatch, log, keys, options=(), read_back=6, columns=SCHEMA):
    """Run the script as Glue would, with its three libraries doubled; return the S3 double."""
    s3 = FakeS3(keys)

    def resolved_options(argv, names):
        return {name: argv[argv.index(f"--{name}") + 1] for name in names}

    functions = types.ModuleType("pyspark.sql.functions")
    functions.col = lambda name: FakeColumn(f"col({name})")
    functions.round = lambda column, scale: FakeColumn(f"round({column.text}, {scale})")
    session = FakeSession(log, read_back, columns)
    builder = types.SimpleNamespace(getOrCreate=lambda: session)
    sql = types.ModuleType("pyspark.sql")
    sql.DataFrame = FakeFrame
    sql.SparkSession = types.SimpleNamespace(builder=builder)
    sql.functions = functions
    utils = types.ModuleType("awsglue.utils")
    utils.getResolvedOptions = resolved_options
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: s3
    for name, module in {
        "awsglue": types.ModuleType("awsglue"),
        "awsglue.utils": utils,
        "pyspark": types.ModuleType("pyspark"),
        "pyspark.sql": sql,
        "pyspark.sql.functions": functions,
        "boto3": boto3,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    argv = ["transform.py", "--SOURCE_PATH", SOURCE, "--TARGET_PATH", TARGET, *options]
    monkeypatch.setattr(sys, "argv", argv)
    runpy.run_path(str(SCRIPT), run_name="__main__")
    return s3


def test_the_script_reads_transforms_and_writes_one_file(monkeypatch, capsys):
    log = {}
    s3 = run_script(monkeypatch, log, [PART, "app-etl/work/glue/_SUCCESS"])
    assert log["read"] == (SOURCE, {"header": True, "inferSchema": True})
    assert log["columns"] == {"notional": "round((col(quantity) * col(price)), 2)"}
    assert log["partitions"] == 1
    assert log["write"] == ("s3://bucket/app-etl/work/glue/", {"header": True}, "overwrite")
    assert s3.copied == [(PART, "app-etl/work/glue/trades.csv")]
    assert s3.deleted == [[PART, "app-etl/work/glue/_SUCCESS"]]
    assert "table" not in log and not s3.put
    assert capsys.readouterr().out == f"reading {SOURCE}\nread 6 row(s)\nwrote {TARGET}\n"


def test_the_script_refuses_more_than_one_part_file(monkeypatch):
    second = "app-etl/work/glue/part-00001-0f6a-c000.csv"
    with pytest.raises(RuntimeError, match="one part file expected"):
        run_script(monkeypatch, {}, [PART, second])


def test_the_governed_read_names_its_columns_and_its_snapshot(monkeypatch):
    log = {}
    options = ["--SOURCE_TABLE", GOVERNED, "--SOURCE_SNAPSHOT", "123456789"]
    run_script(monkeypatch, log, [PART], options)
    assert "read" not in log
    assert log["described"] == GOVERNED
    assert log["query"] == (
        f"SELECT trade_date, desk, instrument, quantity, price FROM {GOVERNED} "
        "VERSION AS OF 123456789"
    )


def test_a_governed_table_without_a_column_fails_naming_it(monkeypatch):
    columns = ["trade_date", "desk", "quantity", "price"]
    with pytest.raises(RuntimeError, match="lacks instrument: the application's schema source"):
        run_script(monkeypatch, {}, [PART], ["--SOURCE_TABLE", GOVERNED], columns=columns)


def test_the_table_is_written_and_read_back(monkeypatch, capsys):
    log = {}
    run_script(monkeypatch, log, [PART], ["--TABLE_PATH", TABLE])
    assert log["table"] == (TABLE, "overwrite")
    assert log["read_back"] == TABLE
    assert f"wrote 6 row(s) to the table at {TABLE}" in capsys.readouterr().out


def test_a_table_that_reads_back_short_fails_the_run(monkeypatch):
    with pytest.raises(RuntimeError, match="reads 5 row\\(s\\) back, 6 written"):
        run_script(monkeypatch, {}, [PART], ["--TABLE_PATH", TABLE], read_back=5)


def test_the_training_sets_are_xgboost_csv_with_every_fifth_row_held_out(monkeypatch):
    log = {}
    s3 = run_script(monkeypatch, log, [PART], ["--TRAIN_PATH", TRAIN])
    assert log["selected"] == ("notional", "quantity", "price")
    assert sorted(s3.put) == [
        f"{TRAIN}batch/batch.csv",
        f"{TRAIN}train/train.csv",
        f"{TRAIN}validation/validation.csv",
    ]
    assert s3.put[f"{TRAIN}validation/validation.csv"] == "1355.0,250,5.42\n"
    assert s3.put[f"{TRAIN}train/train.csv"].splitlines()[0] == "11820.0,120,98.5"
    assert len(s3.put[f"{TRAIN}train/train.csv"].splitlines()) == 5
    assert s3.put[f"{TRAIN}batch/batch.csv"].splitlines() == [
        f"{row['quantity']},{row['price']}" for row in ROWS
    ]


def test_the_governed_read_without_a_snapshot_reads_the_current_one(monkeypatch):
    log = {}
    run_script(monkeypatch, log, [PART], ["--SOURCE_TABLE", GOVERNED])
    assert log["query"] == f"SELECT trade_date, desk, instrument, quantity, price FROM {GOVERNED}"


def test_a_snapshot_that_is_not_a_number_fails_the_run(monkeypatch):
    with pytest.raises(ValueError):
        run_script(monkeypatch, {}, [PART], ["--SOURCE_TABLE", GOVERNED, "--SOURCE_SNAPSHOT", "x"])
