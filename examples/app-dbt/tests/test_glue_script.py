"""The Glue script, run over doubles of awsglue and pyspark: what it reads, the Iceberg table it
writes and reads back, and the options it refuses."""

from __future__ import annotations

import runpy
import sys
import types
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "glue" / "load.py"
SOURCE = "s3://bucket/app-dbt/inbox/"
TABLE = "glue_catalog.app_dbt.trades"
OPTIONS = ["--SOURCE_PATH", SOURCE, "--TABLE_DATABASE", "app_dbt", "--TABLE_NAME", "trades"]


class FakeWriter:
    def __init__(self, log):
        self.log = log
        self.format_name = None
        self.save_mode = None

    def format(self, name):
        self.format_name = name
        return self

    def mode(self, name):
        self.save_mode = name
        return self

    def saveAsTable(self, name):
        self.log["table"] = (name, self.format_name, self.save_mode)


class FakeFrame:
    def __init__(self, log, rows):
        self.log = log
        self.rows = rows

    def count(self):
        return self.rows

    @property
    def write(self):
        return FakeWriter(self.log)


class FakeReader:
    def __init__(self, log, rows):
        self.log = log
        self.rows = rows
        self.options = {}

    def option(self, key, value):
        self.options[key] = value
        return self

    def csv(self, path):
        self.log["read"] = (path, self.options)
        return FakeFrame(self.log, self.rows)


class FakeSession:
    def __init__(self, log, rows, read_back):
        self.log = log
        self.read = FakeReader(log, rows)
        self.read_back = read_back

    def table(self, name):
        self.log.setdefault("read_back", []).append(name)
        return FakeFrame(self.log, self.read_back)


def run_script(monkeypatch, log, options=OPTIONS, rows=10, read_back=10):
    """Run the script as Glue would, with awsglue and pyspark doubled."""

    def resolved_options(argv, names):
        return {name: argv[argv.index(f"--{name}") + 1] for name in names}

    session = FakeSession(log, rows, read_back)
    sql = types.ModuleType("pyspark.sql")
    sql.DataFrame = FakeFrame
    sql.SparkSession = types.SimpleNamespace(
        builder=types.SimpleNamespace(getOrCreate=lambda: session)
    )
    utils = types.ModuleType("awsglue.utils")
    utils.getResolvedOptions = resolved_options
    for name, module in {
        "awsglue": types.ModuleType("awsglue"),
        "awsglue.utils": utils,
        "pyspark": types.ModuleType("pyspark"),
        "pyspark.sql": sql,
    }.items():
        monkeypatch.setitem(sys.modules, name, module)
    monkeypatch.setattr(sys, "argv", ["load.py", *options])
    runpy.run_path(str(SCRIPT), run_name="__main__")


def test_the_script_writes_the_iceberg_table_and_reads_it_back(monkeypatch, capsys):
    log = {}
    run_script(monkeypatch, log)
    assert log["read"] == (SOURCE, {"header": True, "inferSchema": True})
    assert log["table"] == (TABLE, "iceberg", "overwrite")
    assert log["read_back"] == [TABLE]
    assert capsys.readouterr().out == (
        f"reading {SOURCE}\nread 10 row(s)\nwrote 10 row(s) to the table {TABLE}\n"
    )


def test_a_table_that_reads_back_short_fails_the_run(monkeypatch):
    with pytest.raises(RuntimeError, match=f"{TABLE} reads 9 row\\(s\\) back, 10 written"):
        run_script(monkeypatch, {}, read_back=9)


@pytest.mark.parametrize(
    ("options", "named"),
    [
        (
            ["--SOURCE_PATH", SOURCE, "--TABLE_DATABASE", "", "--TABLE_NAME", "trades"],
            "--TABLE_DATABASE",
        ),
        (
            ["--SOURCE_PATH", "", "--TABLE_DATABASE", "app_dbt", "--TABLE_NAME", ""],
            "--SOURCE_PATH and --TABLE_NAME",
        ),
    ],
)
def test_an_option_without_a_value_stops_the_run_before_spark(monkeypatch, options, named):
    log = {}
    with pytest.raises(ValueError, match=f"^{named} must have a value; the run gives none$"):
        run_script(monkeypatch, log, options)
    assert log == {}
