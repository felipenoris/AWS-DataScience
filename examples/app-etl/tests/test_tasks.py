"""The worker's tasks, offline: the report over fabricated summaries and the listing over a double
of DataZone, since the project installs no boto3 (the worker carries it)."""

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
    read as `listing` says, (revision, status) or (revision, status, asset revision), after a change
    set answering `change_revision`; every call recorded. The default is the first publication read
    on 2026-11-10: the change set answers revision 1, which stays CREATING, and revision 2 is
    ACTIVE."""

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
        revision, status, *carried = states.pop(0) if len(states) > 1 else states[0]
        listed = {
            "assetListing": {"assetId": "asset-product", "assetRevision": (carried or ["2"])[0]}
        }
        return {"listingRevision": revision, "status": status, "item": listed}


def install(monkeypatch, fake):
    """`fake` as the boto3 client of `datazone`, the worker's variables unset and no wait slept."""
    boto3 = types.ModuleType("boto3")
    boto3.client = lambda service: fake if service == "datazone" else None
    monkeypatch.setitem(sys.modules, "boto3", boto3)
    monkeypatch.delenv("DataZoneDomainId", raising=False)
    monkeypatch.delenv("DataZoneProjectId", raising=False)
    monkeypatch.setattr(app_etl_tasks.time, "sleep", lambda seconds: None)
    return fake


@pytest.fixture
def datazone(monkeypatch):
    return install(monkeypatch, FakeDataZone())


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


def test_a_republication_takes_neither_the_previous_revision_nor_the_change_sets(datazone):
    """The republication read on 2026-11-10: the change set answered revision 3, which went UPDATING
    and then ACTIVE with the previous asset revision, and revision 4 carried the new one."""
    datazone.change_revision = "3"
    datazone.listing_states = [
        ("2", "ACTIVE", "2"),
        ("3", "UPDATING", "2"),
        ("3", "ACTIVE", "2"),
        ("4", "ACTIVE", "6"),
    ]
    result = json.loads(publish())
    assert (result["listing_revision"], result["asset_revision"]) == ("4", "6")
    assert sum(call[0] == "get_listing" for call in datazone.calls) == 4


def test_a_revision_past_the_change_sets_may_pass_through_updating(datazone):
    datazone.listing_states = [("2", "UPDATING"), ("2", "ACTIVE")]
    assert json.loads(publish())["listing_revision"] == "2"


def test_publish_fails_on_a_listing_that_does_not_activate(datazone):
    datazone.listing_states = [("1", "CREATING"), ("2", "INACTIVE")]
    with pytest.raises(RuntimeError, match="listing listing-1 revision 2 is INACTIVE"):
        publish()


def test_publish_fails_when_no_revision_activates_within_the_timeout(datazone, monkeypatch):
    monkeypatch.setattr(app_etl_tasks, "LISTING_TIMEOUT", 0)
    datazone.listing_states = [("1", "CREATING")]
    message = "not ACTIVE past revision 1 after 0 s: its latest is revision 1, CREATING"
    with pytest.raises(RuntimeError, match=message):
        publish()


# The data product (decision 26): the search answers a project's data products as `dataProductItem`
# with an `id`, as the API's model names them, and the listing of one carries its revision under
# `dataProductListing`.
PRODUCT_NAME, PRODUCT_TEXT = "trades-notional", "Each trade with its notional."
ITEMS = [{"itemType": "ASSET", "identifier": "asset-product"}]


class ServiceError(Exception):
    """A boto3 ClientError's shape: its code under `response`, its message in its text."""

    def __init__(self, code, message):
        super().__init__(f"An error occurred ({code}) when calling the operation: {message}")
        self.response = {"Error": {"Code": code, "Message": message}}


class FakeDataZoneWithProduct(FakeDataZone):
    """FakeDataZone with the data product's calls. `products` holds the project's by id and
    `foreign` other projects', one flagged `unreadable` refused to this role; the search finds the
    project's unless `unindexed`; a create whose name a product holds conflicts, naming it, as
    DataZone's message does; the product's listing reads as `product_listing` says, (revision,
    status, data product revision), after a change set answering `product_change_revision`. The
    default is a first publication shaped like an asset's."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.products, self.foreign = {}, {}
        self.unindexed = False
        self.product_change_revision = "1"
        self.product_listing = [("1", "CREATING", None), ("2", "ACTIVE", "1")]

    def own(self, identifier, items=ITEMS, description=PRODUCT_TEXT, revision="3"):
        self.products[identifier] = {
            "name": PRODUCT_NAME,
            "items": items,
            "description": description,
            "revision": revision,
            "owningProjectId": PROJECT,
        }

    def _pages(self, name, kw):
        if name == "search" and kw["searchScope"] == "DATA_PRODUCT":
            self.calls.append((name, kw))
            assert kw["owningProjectIdentifier"] == PROJECT and kw["searchText"] == PRODUCT_NAME
            found = [
                {"dataProductItem": {"id": identifier, "name": product["name"]}}
                for identifier, product in self.products.items()
            ]
            return [{"items": [] if self.unindexed else found}]
        return super()._pages(name, kw)

    def create_data_product(self, domainIdentifier, owningProjectIdentifier, name, items, **kw):
        self.calls.append(("create_data_product", name, items, kw.get("description")))
        for identifier, product in {**self.products, **self.foreign}.items():
            if product["name"] == name:
                raise ServiceError("ConflictException", f"Conflict with dataProduct {identifier}")
        self.products["dp-new"] = {
            "name": name,
            "items": items,
            "description": kw.get("description"),
            "revision": "1",
            "owningProjectId": owningProjectIdentifier,
        }
        return {"id": "dp-new", "revision": "1"}

    def get_data_product(self, domainIdentifier, identifier):
        self.calls.append(("get_data_product", identifier))
        product = self.products.get(identifier) or self.foreign.get(identifier)
        if product is None:
            raise ServiceError("ResourceNotFoundException", identifier)
        if product.get("unreadable"):
            raise ServiceError(
                "AccessDeniedException", "User is not permitted to perform operation"
            )
        return {"id": identifier, **product}

    def create_data_product_revision(self, domainIdentifier, identifier, name, items, **kw):
        self.calls.append(
            ("create_data_product_revision", identifier, items, kw.get("description"))
        )
        product = self.products[identifier]
        revision = str(int(product["revision"]) + 1)
        product.update(items=items, description=kw.get("description"), revision=revision)
        return {"id": identifier, "revision": revision}

    def create_listing_change_set(self, domainIdentifier, entityIdentifier, entityType, action):
        if entityType != "DATA_PRODUCT":
            return super().create_listing_change_set(
                domainIdentifier, entityIdentifier, entityType, action
            )
        self.calls.append(("create_listing_change_set", entityIdentifier, entityType, action))
        return {"listingId": "listing-dp", "listingRevision": self.product_change_revision}

    def get_listing(self, domainIdentifier, identifier, listingRevision=None):
        if identifier != "listing-dp":
            return super().get_listing(domainIdentifier, identifier, listingRevision)
        self.calls.append(("get_listing", identifier, listingRevision))
        states = self.product_listing
        revision, status, carried = states.pop(0) if len(states) > 1 else states[0]
        listed = {"dataProductListing": {"dataProductId": "dp", "dataProductRevision": carried}}
        return {"listingRevision": revision, "status": status, "item": listed}


@pytest.fixture
def product_zone(monkeypatch):
    return install(monkeypatch, FakeDataZoneWithProduct())


def publish_product(**kwargs):
    """`publish` naming the data product the workflow names, unless a test passes its own."""
    names = {"data_product": PRODUCT_NAME, "data_product_description": PRODUCT_TEXT, **kwargs}
    return publish(**names)


def calls_named(fake, name):
    return [call for call in fake.calls if call[0] == name]


def test_publish_creates_the_data_product_over_the_asset_and_lists_it(product_zone, capsys):
    result = json.loads(publish_product())
    assert {key: value for key, value in result.items() if key.startswith("data_product")} == {
        "data_product": "dp-new",
        "data_product_revision": "1",
        "data_product_change": "created",
        "data_product_listing": "listing-dp",
        "data_product_listing_revision": "2",
        "data_product_listed_revision": "1",
    }
    assert ("create_data_product", PRODUCT_NAME, ITEMS, PRODUCT_TEXT) in product_zone.calls
    changes = calls_named(product_zone, "create_listing_change_set")
    assert changes == [
        ("create_listing_change_set", "asset-product", "ASSET", "PUBLISH"),
        ("create_listing_change_set", "dp-new", "DATA_PRODUCT", "PUBLISH"),
    ]
    printed = capsys.readouterr().out
    assert "data product trades-notional: created dp-new, revision 1" in printed
    assert "listing listing-dp revision 2: ACTIVE, data product revision 1" in printed
    assert printed.endswith(
        "published app_etl.trades_notional: asset asset-product, listing listing-1;"
        " data product dp-new, listing listing-dp\n"
    )


def test_publish_names_no_data_product_unless_the_workflow_does(product_zone):
    result = json.loads(publish())
    assert not any(key.startswith("data_product") for key in result)
    assert not calls_named(product_zone, "create_data_product")
    assert all(
        call[1].get("searchScope") != "DATA_PRODUCT" for call in calls_named(product_zone, "search")
    )


def test_a_blank_description_is_not_sent(product_zone):
    publish_product(data_product_description="  ")
    assert ("create_data_product", PRODUCT_NAME, ITEMS, None) in product_zone.calls


def test_an_unchanged_data_product_is_listed_again_and_not_revised(product_zone):
    product_zone.own("dp-1")
    product_zone.product_change_revision = "5"
    product_zone.product_listing = [("5", "ACTIVE", "3")]
    result = json.loads(publish_product())
    assert (result["data_product"], result["data_product_change"]) == ("dp-1", "unchanged")
    assert result["data_product_listing_revision"] == "5"
    assert not calls_named(product_zone, "create_data_product")
    assert not calls_named(product_zone, "create_data_product_revision")


@pytest.mark.parametrize(
    "held",
    [
        {"items": [{"itemType": "ASSET", "identifier": "asset-older"}]},
        {"description": "An older text."},
        {"items": ITEMS + [{"itemType": "ASSET", "identifier": "asset-other"}]},
    ],
)
def test_a_data_product_whose_item_or_description_changed_is_revised(product_zone, held):
    product_zone.own("dp-1", **held)
    product_zone.product_listing = [("2", "ACTIVE", "4")]
    result = json.loads(publish_product())
    assert (result["data_product_revision"], result["data_product_change"]) == ("4", "revised")
    assert calls_named(product_zone, "create_data_product_revision") == [
        ("create_data_product_revision", "dp-1", ITEMS, PRODUCT_TEXT)
    ]


def test_a_create_conflicting_with_the_projects_own_product_takes_it(product_zone):
    """The search had not indexed the project's product yet: the conflict names it, and it is read
    and left as it is."""
    product_zone.own("dp-1")
    product_zone.unindexed = True
    product_zone.product_listing = [("2", "ACTIVE", "3")]
    result = json.loads(publish_product())
    assert (result["data_product"], result["data_product_change"]) == ("dp-1", "unchanged")
    assert calls_named(product_zone, "create_data_product")
    assert ("get_data_product", "dp-1") in product_zone.calls


def test_a_name_another_project_holds_fails_naming_that_product(product_zone):
    product_zone.foreign["dp-dev"] = {"name": PRODUCT_NAME, "owningProjectId": "prj-dev"}
    message = "data product trades-notional is dp-dev of project prj-dev: a data product's name"
    with pytest.raises(RuntimeError, match=message):
        publish_product()
    assert ("create_listing_change_set", "asset-product", "ASSET", "PUBLISH") in product_zone.calls
    assert all(
        call[2] != "DATA_PRODUCT" for call in calls_named(product_zone, "create_listing_change_set")
    )


def test_a_name_held_by_a_product_the_project_cannot_read_fails_naming_it(product_zone):
    product_zone.foreign["dp-dev"] = {"name": PRODUCT_NAME, "unreadable": True}
    message = r"is dp-dev, which this project cannot read \(AccessDeniedException\)"
    with pytest.raises(RuntimeError, match=message):
        publish_product()


def test_another_refusal_of_the_create_is_raised_as_it_came(product_zone, monkeypatch):
    def refused(**kwargs):
        raise ServiceError("AccessDeniedException", "no identity-based policy allows")

    monkeypatch.setattr(product_zone, "create_data_product", refused)
    with pytest.raises(ServiceError, match="no identity-based policy allows"):
        publish_product()


def test_two_data_products_of_the_name_in_the_project_fail(product_zone):
    product_zone.own("dp-1")
    product_zone.own("dp-2")
    with pytest.raises(RuntimeError, match="2 data products named trades-notional in the project"):
        publish_product()


def test_the_data_products_listing_may_activate_at_the_change_sets_revision(product_zone):
    product_zone.product_listing = [("1", "ACTIVE", "1")]
    assert json.loads(publish_product())["data_product_listing_revision"] == "1"


def test_the_data_products_listing_takes_no_older_revision_and_no_older_product(product_zone):
    product_zone.own("dp-1")
    product_zone.product_change_revision = "5"
    product_zone.product_listing = [
        ("4", "ACTIVE", "3"),
        ("5", "ACTIVE", "2"),
        ("6", "ACTIVE", "3"),
    ]
    result = json.loads(publish_product())
    assert (result["data_product_listing_revision"], result["data_product_listed_revision"]) == (
        "6",
        "3",
    )
    assert (
        len([call for call in product_zone.calls if call[:2] == ("get_listing", "listing-dp")]) == 3
    )


def test_publish_fails_on_a_data_product_listing_that_does_not_activate(product_zone):
    product_zone.product_listing = [("1", "CREATING", None), ("2", "INACTIVE", "1")]
    with pytest.raises(RuntimeError, match="listing listing-dp revision 2 is INACTIVE"):
        publish_product()


def test_publish_fails_when_the_data_products_listing_outlives_the_timeout(
    product_zone, monkeypatch
):
    monkeypatch.setattr(app_etl_tasks, "LISTING_TIMEOUT", 0)
    product_zone.listing_states = [("2", "ACTIVE")]
    product_zone.product_listing = [("1", "CREATING", None)]
    message = (
        "listing listing-dp not ACTIVE with data product revision 1 from revision 1 after 0 s:"
        " its latest is revision 1, CREATING, carrying None"
    )
    with pytest.raises(RuntimeError, match=message):
        publish_product()
