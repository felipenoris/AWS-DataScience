"""The worker's task, offline: the report over fabricated summaries, and the listing over a double
of boto3, since the project installs no boto3 (the worker carries it)."""

from __future__ import annotations

import json
import sys
import types

import app_etl_tasks
import pytest

SUMMARIES = {
    "app-etl/work/job/trades.summary.json": {
        "input": "trades.csv",
        "sha256": "ab" * 32,
        "rows": 10,
        "columns": ["trade_date", "desk", "instrument", "quantity", "price", "notional"],
        "numeric": {
            "quantity": {"sum": 1530, "min": 30, "max": 500},
            "price": {"sum": 701.24, "min": 1.08, "max": 101.2},
            "notional": {"sum": 50061.5, "min": 327.0, "max": 11820.0},
        },
    },
    "app-etl/work/job/fees.summary.json": {
        "input": "fees.csv",
        "sha256": "cd" * 32,
        "rows": 2,
        "columns": ["desk", "fee"],
        "numeric": {"fee": {"sum": 3.5, "min": 1.0, "max": 2.5}},
    },
}


class FakeS3:
    """The two calls `summaries` makes, over a bucket holding SUMMARIES and a Parquet beside."""

    def __init__(self):
        self.listed = []
        self.read = []

    def get_paginator(self, name):
        assert name == "list_objects_v2"
        return self

    def paginate(self, Bucket, Prefix):
        self.listed.append((Bucket, Prefix))
        keys = sorted(SUMMARIES) + ["app-etl/work/job/trades.parquet"]
        return [{"Contents": [{"Key": key} for key in keys if key.startswith(Prefix)]}]

    def get_object(self, Bucket, Key):
        self.read.append(Key)
        body = json.dumps(SUMMARIES[Key]).encode()
        return {"Body": types.SimpleNamespace(read=lambda: body)}


@pytest.fixture
def s3(monkeypatch):
    fake = FakeS3()
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: fake
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    return fake


def test_split_uri():
    assert app_etl_tasks.split_uri("s3://bucket/a/b/") == ("bucket", "a/b/")
    with pytest.raises(ValueError, match="not an s3:// URI"):
        app_etl_tasks.split_uri("https://bucket/a/b/")


def test_summaries_reads_only_the_summary_files(s3):
    found = app_etl_tasks.summaries("s3://bucket/app-etl/work/job/")
    assert s3.listed == [("bucket", "app-etl/work/job/")]
    assert s3.read == sorted(SUMMARIES)
    assert [summary["input"] for summary in found] == ["fees.csv", "trades.csv"]


def test_report_orders_the_tables_by_input_and_totals_the_rows():
    found = list(SUMMARIES.values())
    result = app_etl_tasks.report(found)
    assert [table["input"] for table in result["tables"]] == ["fees.csv", "trades.csv"]
    assert result["tables"][1]["sums"] == {"quantity": 1530, "price": 701.24, "notional": 50061.5}
    assert result["tables"][1]["sha256"] == "ab" * 32
    assert result["rows"] == 12


def test_summarize_returns_the_report_as_json_text(s3, capsys):
    text = app_etl_tasks.summarize("s3://bucket/app-etl/work/job/", ti=None)
    assert text.endswith("}\n")
    parsed = json.loads(text)
    assert list(parsed) == ["rows", "tables"]
    assert parsed["rows"] == 12
    assert capsys.readouterr().out == "2 table(s), 12 rows, under s3://bucket/app-etl/work/job/\n"


def test_summarize_refuses_a_prefix_without_summaries(s3):
    with pytest.raises(RuntimeError, match="no .summary.json under"):
        app_etl_tasks.summarize("s3://bucket/app-etl/work/empty/")
