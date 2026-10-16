"""The Glue script, run over doubles of awsglue, pyspark and boto3: what it reads, the column it
adds, the one file it writes and the files it deletes."""

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


class FakeColumn:
    """A column expression, kept as text."""

    def __init__(self, text):
        self.text = text

    def __mul__(self, other):
        return FakeColumn(f"({self.text} * {other.text})")


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


class FakeFrame:
    def __init__(self, log):
        self.log = log

    def withColumn(self, name, column):
        self.log.setdefault("columns", {})[name] = column.text
        return self

    def transform(self, function):
        return function(self)

    def coalesce(self, partitions):
        self.log["partitions"] = partitions
        return self

    @property
    def write(self):
        return FakeWriter(self.log)


class FakeReader:
    def __init__(self, log):
        self.log = log
        self.options = {}

    def option(self, key, value):
        self.options[key] = value
        return self

    def csv(self, path):
        self.log["read"] = (path, self.options)
        return FakeFrame(self.log)


class FakeS3:
    """What Spark left under the target's prefix, and the copy and the delete the script asks."""

    def __init__(self, keys):
        self.keys = keys
        self.copied = []
        self.deleted = []

    def list_objects_v2(self, Bucket, Prefix):
        return {"Contents": [{"Key": key} for key in self.keys if key.startswith(Prefix)]}

    def copy_object(self, Bucket, Key, CopySource):
        self.copied.append((CopySource["Key"], Key))

    def delete_objects(self, Bucket, Delete):
        self.deleted.append([item["Key"] for item in Delete["Objects"]])


def run_script(monkeypatch, log, keys):
    """Run the script as Glue would, with its three libraries doubled; return the S3 double."""
    s3 = FakeS3(keys)

    def resolved_options(argv, names):
        return {name: argv[argv.index(f"--{name}") + 1] for name in names}

    functions = types.ModuleType("pyspark.sql.functions")
    functions.col = lambda name: FakeColumn(f"col({name})")
    functions.round = lambda column, scale: FakeColumn(f"round({column.text}, {scale})")
    session = types.SimpleNamespace(read=FakeReader(log))
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
    argv = ["transform.py", "--SOURCE_PATH", SOURCE, "--TARGET_PATH", TARGET]
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
    assert capsys.readouterr().out == f"wrote {TARGET}\n"


def test_the_script_refuses_more_than_one_part_file(monkeypatch):
    second = "app-etl/work/glue/part-00001-0f6a-c000.csv"
    with pytest.raises(RuntimeError, match="one part file expected"):
        run_script(monkeypatch, {}, [PART, second])
