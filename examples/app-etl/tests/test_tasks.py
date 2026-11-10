"""The worker's tasks, offline: the report over fabricated summaries, the listing over a double of
DataZone, and the evaluation over doubles of SageMaker and S3, since the project installs no boto3
(the worker carries it)."""

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
# The search's asset items in the shape read on 2026-11-10, the account left out: the external
# identifier is the table's ARN with the project's id suffixed to its last segment, and no item
# carries a revision.
ASSETS = [
    {
        "identifier": "asset-product",
        "name": "trades_notional",
        "typeIdentifier": "amazon.datazone.GlueTableAssetType",
        "externalIdentifier": (
            f"arn:aws:glue:us-west-2:ACCOUNT:table/app_etl/trades_notional.{PROJECT}"
        ),
    },
    {
        "identifier": "asset-other",
        "name": "trades_notional",
        "typeIdentifier": "amazon.datazone.GlueTableAssetType",
        "externalIdentifier": (
            f"arn:aws:glue:us-west-2:ACCOUNT:table/glue_db_example/trades_notional.{PROJECT}"
        ),
    },
]


class FakeDataZone:
    """The DataZone calls `publish` makes, over SOURCES and ASSETS, each run ending as the sequence
    says, the first `empty_searches` searches answering nothing, and the listing's latest revision
    read as `listing` says after a change set answering `change_revision`; every call recorded.
    The default is the first publication read on 2026-11-10: the change set answers revision 1,
    which stays CREATING, and revision 2 is ACTIVE."""

    def __init__(
        self,
        sources=SOURCES,
        assets=ASSETS,
        run=("RUNNING", "SUCCESS"),
        listing=(("1", "CREATING"), ("2", "ACTIVE")),
    ):
        self.sources, self.assets = sources, assets
        self.run_statuses, self.listing_states = list(run), list(listing)
        self.change_revision = "1"
        self.empty_searches = 0
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
        if self.empty_searches:
            self.empty_searches -= 1
            return [{"items": []}]
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
        return {"listingId": "listing-1", "listingRevision": self.change_revision}

    def get_listing(self, domainIdentifier, identifier, listingRevision=None):
        self.calls.append(("get_listing", identifier, listingRevision))
        if listingRevision == self.change_revision:
            return {"listingRevision": listingRevision, "status": "CREATING"}
        states = self.listing_states
        revision, status = states.pop(0) if len(states) > 1 else states[0]
        listed = {"assetListing": {"assetId": "asset-product", "assetRevision": "2"}}
        return {"listingRevision": revision, "status": status, "item": listed}


@pytest.fixture
def datazone(monkeypatch):
    fake = FakeDataZone()
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: fake if service == "datazone" else None
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.delenv("DataZoneDomainId", raising=False)
    monkeypatch.delenv("DataZoneProjectId", raising=False)
    monkeypatch.setattr(app_etl_tasks.time, "sleep", lambda seconds: None)
    return fake


def publish(database="app_etl", table="trades_notional", gate="true", **kwargs):
    """`publish` with the identifiers the deploy substitutes, unless a test passes its own."""
    ids = {"domain": DOMAIN, "project": PROJECT, **kwargs}
    return app_etl_tasks.publish(database, table, gate, **ids)


def test_publish_runs_the_source_then_lists_the_assets_latest_revision(datazone, capsys):
    text = publish(ti=None)
    result = json.loads(text)
    assert result == {
        "published": True,
        "domain": DOMAIN,
        "project": PROJECT,
        "data_source": "src-product",
        "source_run": "run-1",
        "asset": "asset-product",
        "listing": "listing-1",
        "listing_revision": "2",
        "asset_revision": "2",
    }
    assert ("start_data_source_run", "src-product") in datazone.calls
    assert ("create_listing_change_set", "asset-product", "ASSET", "PUBLISH") in datazone.calls
    assert ("get_listing", "listing-1", None) in datazone.calls
    printed = capsys.readouterr().out
    assert "source run run-1: SUCCESS" in printed
    assert "listing listing-1 revision 2: ACTIVE, asset revision 2" in printed
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
    assert json.loads(publish(gate="True "))["published"]


def test_publish_reads_the_workers_variable_for_an_identifier_the_deploy_left_empty(
    datazone, monkeypatch
):
    monkeypatch.setenv("DataZoneDomainId", DOMAIN)
    result = json.loads(publish(domain=""))
    assert (result["domain"], result["project"]) == (DOMAIN, PROJECT)


def test_publish_refuses_a_run_with_no_identifier_anywhere(datazone):
    with pytest.raises(RuntimeError, match="no DataZoneProjectId: the deploy substituted none"):
        publish(project=" ")


def test_publish_refuses_a_database_with_no_source_or_two(datazone):
    with pytest.raises(RuntimeError, match=r"0 data source\(s\) over other_db"):
        publish(database="other_db")
    datazone.sources = {"src-a": ["app_etl"], "src-b": ["app_etl"]}
    with pytest.raises(RuntimeError, match=r"2 data source\(s\) over app_etl"):
        publish()


def test_publish_fails_on_a_source_run_that_does_not_succeed(datazone):
    datazone.run_statuses = ["RUNNING", "FAILED"]
    with pytest.raises(RuntimeError, match="source run run-1 ended FAILED: boom"):
        publish()
    assert not any(call[0] == "search" for call in datazone.calls)


def test_publish_fails_when_the_run_outlives_its_timeout(datazone, monkeypatch):
    datazone.run_statuses = ["RUNNING"]
    clock = iter([0, 0, 1000])
    monkeypatch.setattr(app_etl_tasks.time, "monotonic", lambda: next(clock))
    with pytest.raises(RuntimeError, match="still RUNNING after 600 s"):
        publish()


@pytest.mark.parametrize(
    ("external", "expected"),
    [
        (f"arn:aws:glue:us-west-2:ACCOUNT:table/app_etl/trades_notional.{PROJECT}", True),
        ("arn:aws:glue:us-west-2:ACCOUNT:table/app_etl/trades_notional", True),
        ("arn:aws:glue:us-west-2:ACCOUNT:table/app_etl/trades_notional.prj-other", False),
        ("arn:aws:glue:us-west-2:ACCOUNT:table/glue_db_example/trades_notional", False),
        ("arn:aws:glue:us-west-2:ACCOUNT:table/app_etl/trades_notional_v2", False),
        ("", False),
    ],
)
def test_names_table_reads_the_arn_with_or_without_the_projects_suffix(external, expected):
    assert app_etl_tasks.names_table(external, PROJECT, "app_etl", "trades_notional") is expected


def test_publish_asks_the_search_again_until_the_asset_appears(datazone):
    datazone.empty_searches = 2
    assert json.loads(publish())["asset"] == "asset-product"
    assert sum(call[0] == "search" for call in datazone.calls) == 3


def test_publish_refuses_a_table_the_run_did_not_import(datazone, monkeypatch):
    monkeypatch.setattr(app_etl_tasks, "ASSET_TIMEOUT", 0)
    datazone.assets = [ASSETS[1]]
    with pytest.raises(RuntimeError, match=r"0 asset\(s\) for app_etl/trades_notional"):
        publish()


def test_publish_refuses_two_assets_for_the_table_at_once(datazone):
    datazone.assets = [ASSETS[0], {**ASSETS[0], "identifier": "asset-copy"}]
    with pytest.raises(RuntimeError, match=r"2 asset\(s\) for app_etl/trades_notional"):
        publish()
    assert sum(call[0] == "search" for call in datazone.calls) == 1


def test_publish_waits_past_the_previous_publications_revision(datazone):
    datazone.change_revision = "3"
    datazone.listing_states = [("2", "ACTIVE"), ("3", "CREATING"), ("4", "ACTIVE")]
    assert json.loads(publish())["listing_revision"] == "4"
    assert sum(call[0] == "get_listing" for call in datazone.calls) == 3


def test_publish_fails_on_a_listing_that_does_not_activate(datazone):
    datazone.listing_states = [("1", "CREATING"), ("2", "INACTIVE")]
    with pytest.raises(RuntimeError, match="listing listing-1 revision 2 is INACTIVE"):
        publish()


def test_publish_fails_when_no_revision_activates_within_the_timeout(datazone, monkeypatch):
    monkeypatch.setattr(app_etl_tasks, "LISTING_TIMEOUT", 0)
    datazone.listing_states = [("1", "CREATING")]
    message = "not ACTIVE at or past revision 1 after 0 s: its latest is revision 1, CREATING"
    with pytest.raises(RuntimeError, match=message):
        publish()
