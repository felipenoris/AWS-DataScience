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


def test_the_report_carries_a_governed_source_and_no_other():
    source = {"table": "lake.curated.trades", "snapshot_id": 5512, "pinned": False}
    found = [{**SUMMARIES["app-etl/work/job/trades.summary.json"], "source": source}]
    found.append(SUMMARIES["app-etl/work/job/fees.summary.json"])
    tables = app_etl_tasks.report(found)["tables"]
    assert "source" not in tables[0]
    assert tables[1]["source"] == source


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


TRAINING = {
    "TrainingJobName": "app-etl-train-20261024T120000",
    "TrainingJobStatus": "Completed",
    "ModelArtifacts": {
        "S3ModelArtifacts": (
            "s3://bucket/models/app-etl/app-etl-train-20261024T120000/output/model.tar.gz"
        )
    },
    "FinalMetricDataList": [
        {"MetricName": "train:rmse", "Value": 12.5},
        {"MetricName": "validation:rmse", "Value": 40.25},
    ],
}


class FakeClients:
    """The SageMaker and S3 calls `evaluate` makes, over TRAINING and a batch of three rows."""

    def __init__(self, training):
        self.training = training
        self.put = {}

    def describe_training_job(self, TrainingJobName):
        assert TrainingJobName == self.training["TrainingJobName"]
        return self.training

    def get_object(self, Bucket, Key):
        assert (Bucket, Key) == ("bucket", "app-etl/work/train/batch/batch.csv")
        body = b"120,98.5\n500,1.08\n80,99.75\n"
        return {"Body": types.SimpleNamespace(read=lambda: body)}

    def put_object(self, Bucket, Key, Body):
        self.put[f"s3://{Bucket}/{Key}"] = json.loads(Body)


def run_evaluate(monkeypatch, training):
    clients = FakeClients(training)
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: clients
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    result = app_etl_tasks.evaluate(
        json.dumps({"Training": training}),
        batch="s3://bucket/app-etl/work/train/batch/batch.csv",
        models="s3://bucket/models/app-etl/",
    )
    return clients, json.loads(result)


def test_evaluate_writes_the_model_quality_beside_the_model(monkeypatch, capsys):
    clients, result = run_evaluate(monkeypatch, TRAINING)
    key = "s3://bucket/models/app-etl/app-etl-train-20261024T120000/evaluation.json"
    assert clients.put[key] == result
    assert result["regression_metrics"]["rmse"] == {"value": 40.25, "standard_deviation": "NaN"}
    assert result["awsds"]["batch_rows"] == 3
    assert result["awsds"]["model_data"].endswith("/output/model.tar.gz")
    assert "validation:rmse 40.25, 3 batch row(s)" in capsys.readouterr().out


def test_evaluate_refuses_a_job_that_did_not_complete(monkeypatch):
    with pytest.raises(RuntimeError, match="is Failed, not Completed"):
        run_evaluate(monkeypatch, {**TRAINING, "TrainingJobStatus": "Failed"})


def test_evaluate_refuses_a_job_without_the_validation_metric(monkeypatch):
    training = {**TRAINING, "FinalMetricDataList": [{"MetricName": "train:rmse", "Value": 1.0}]}
    with pytest.raises(RuntimeError, match="reports no validation:rmse"):
        run_evaluate(monkeypatch, training)


def test_the_job_name_is_read_from_the_xcom_as_the_worker_renders_it():
    rendered = json.dumps({"Training": TRAINING})
    assert app_etl_tasks.training_job_name(rendered) == "app-etl-train-20261024T120000"


def test_the_job_name_is_read_from_twice_encoded_text_a_dict_and_a_literal():
    name = "app-etl-train-20261024T120000"
    assert app_etl_tasks.training_job_name(json.dumps(json.dumps({"Training": TRAINING}))) == name
    assert app_etl_tasks.training_job_name({"Training": TRAINING}) == name
    assert app_etl_tasks.training_job_name(repr({"Training": TRAINING})) == name


def test_an_xcom_without_the_job_fails_naming_its_keys():
    with pytest.raises(RuntimeError, match=r"names no training job: \['Processing'\]"):
        app_etl_tasks.training_job_name(json.dumps({"Processing": {}}))


def test_an_xcom_that_is_not_json_fails():
    with pytest.raises(RuntimeError, match="neither JSON nor a literal"):
        app_etl_tasks.training_job_name("app-etl-train-20261024T120000 (")


DOMAIN, PROJECT = "dzd-example", "prj-example"
SOURCES = {
    "src-product": ["app_etl"],
    "src-default": ["glue_db_example"],
}
ASSETS = [
    {
        "identifier": "asset-product",
        "externalIdentifier": "app_etl/trades_notional",
        "latestRevision": "3",
    },
    {"identifier": "asset-other", "externalIdentifier": "glue_db_example/trades_notional"},
]


class FakeDataZone:
    """The DataZone calls `publish` makes, over SOURCES and ASSETS, each run and listing ending as
    the sequences say; every call recorded."""

    def __init__(
        self,
        sources=SOURCES,
        assets=ASSETS,
        run=("RUNNING", "SUCCESS"),
        listing=("CREATING", "ACTIVE"),
    ):
        self.sources, self.assets = sources, assets
        self.run_statuses, self.listing_statuses = list(run), list(listing)
        self.calls = []

    def get_paginator(self, name):
        return types.SimpleNamespace(paginate=lambda **kw: self._pages(name, kw))

    def _pages(self, name, kw):
        self.calls.append((name, kw))
        if name == "list_data_sources":
            assert kw == {"domainIdentifier": DOMAIN, "projectIdentifier": PROJECT, "type": "GLUE"}
            return [{"items": [{"dataSourceId": source} for source in self.sources]}]
        assert name == "search" and kw["searchScope"] == "ASSET"
        assert kw["owningProjectIdentifier"] == PROJECT and kw["searchText"] == "trades_notional"
        return [{"items": [{"assetItem": asset} for asset in self.assets]}]

    def get_data_source(self, domainIdentifier, identifier):
        filters = [{"databaseName": name} for name in self.sources[identifier]]
        return {
            "configuration": {"glueRunConfiguration": {"relationalFilterConfigurations": filters}}
        }

    def start_data_source_run(self, domainIdentifier, dataSourceIdentifier):
        self.calls.append(("start_data_source_run", dataSourceIdentifier))
        return {"id": "run-1"}

    def get_data_source_run(self, domainIdentifier, identifier):
        status = self.run_statuses.pop(0) if len(self.run_statuses) > 1 else self.run_statuses[0]
        return {"status": status, "runStatisticsForAssets": {"added": 1}, "errorMessage": "boom"}

    def create_listing_change_set(self, domainIdentifier, entityIdentifier, entityType, action):
        self.calls.append(("create_listing_change_set", entityIdentifier, entityType, action))
        return {"listingId": "listing-1", "listingRevision": "2", "status": "CREATING"}

    def get_listing(self, domainIdentifier, identifier, listingRevision):
        status = (
            self.listing_statuses.pop(0)
            if len(self.listing_statuses) > 1
            else self.listing_statuses[0]
        )
        return {"status": status}


@pytest.fixture
def datazone(monkeypatch):
    fake = FakeDataZone()
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: fake if service == "datazone" else None
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.setenv("DataZoneDomainId", DOMAIN)
    monkeypatch.setenv("DataZoneProjectId", PROJECT)
    monkeypatch.setattr(app_etl_tasks.time, "sleep", lambda seconds: None)
    return fake


def test_publish_runs_the_source_then_lists_the_assets_latest_revision(datazone, capsys):
    text = app_etl_tasks.publish("app_etl", "trades_notional", "true", ti=None)
    result = json.loads(text)
    assert result == {
        "published": True,
        "domain": DOMAIN,
        "project": PROJECT,
        "data_source": "src-product",
        "source_run": "run-1",
        "asset": "asset-product",
        "asset_revision": "3",
        "listing": "listing-1",
        "listing_revision": "2",
    }
    assert ("start_data_source_run", "src-product") in datazone.calls
    assert ("create_listing_change_set", "asset-product", "ASSET", "PUBLISH") in datazone.calls
    printed = capsys.readouterr().out
    assert "source run run-1: SUCCESS" in printed
    assert "listing listing-1 revision 2: ACTIVE" in printed
    assert printed.endswith(
        "published app_etl.trades_notional: asset asset-product, listing listing-1\n"
    )


@pytest.mark.parametrize("value", ["false", "", "True "])
def test_publish_does_nothing_where_the_stage_lists_no_product(value, capsys):
    if value.strip().lower() == "true":
        pytest.skip("the gate admits it")
    text = app_etl_tasks.publish("app_etl", "trades_notional", value)
    assert json.loads(text) == {"published": False}
    assert "nothing listed" in capsys.readouterr().out


def test_publish_admits_the_gate_whatever_its_case_and_spaces(datazone):
    assert json.loads(app_etl_tasks.publish("app_etl", "trades_notional", "True "))["published"]


def test_publish_refuses_a_worker_outside_a_project(datazone, monkeypatch):
    monkeypatch.delenv("DataZoneProjectId")
    with pytest.raises(RuntimeError, match="carries no DataZoneProjectId"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")


def test_publish_refuses_a_database_with_no_source_or_two(datazone):
    with pytest.raises(RuntimeError, match=r"0 data source\(s\) over other_db"):
        app_etl_tasks.publish("other_db", "trades_notional", "true")
    datazone.sources = {"src-a": ["app_etl"], "src-b": ["app_etl"]}
    with pytest.raises(RuntimeError, match=r"2 data source\(s\) over app_etl"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")


def test_publish_fails_on_a_source_run_that_does_not_succeed(datazone):
    datazone.run_statuses = ["RUNNING", "FAILED"]
    with pytest.raises(RuntimeError, match="source run run-1 ended FAILED: boom"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")
    assert not any(call[0] == "search" for call in datazone.calls)


def test_publish_fails_when_the_run_outlives_its_timeout(datazone, monkeypatch):
    datazone.run_statuses = ["RUNNING"]
    clock = iter([0, 0, 1000])
    monkeypatch.setattr(app_etl_tasks.time, "monotonic", lambda: next(clock))
    with pytest.raises(RuntimeError, match="still RUNNING after 600 s"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")


def test_publish_refuses_a_table_the_run_did_not_import(datazone):
    datazone.assets = [ASSETS[1]]
    with pytest.raises(RuntimeError, match=r"0 asset\(s\) for app_etl/trades_notional"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")


def test_publish_fails_on_a_listing_that_does_not_activate(datazone):
    datazone.listing_statuses = ["CREATING", "INACTIVE"]
    with pytest.raises(RuntimeError, match="listing listing-1 revision 2 is INACTIVE"):
        app_etl_tasks.publish("app_etl", "trades_notional", "true")
