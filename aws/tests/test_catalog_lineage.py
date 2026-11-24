"""CT-21 to CT-24 read against the shapes measured on 2026-11-24, the empty cases included (Lesson 87).

catalog.py's lineage rows (Stage 20 step 6.1) and its comparison of a deployment project's assets with
their dev project's (Stage 20 verification xxi). The script is loaded from its file; main() never runs.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

AWS = Path(__file__).resolve().parents[1]


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"awsds_{name}", AWS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cat = load("catalog")

# Account ids built at run time: the identifier gate refuses a twelve-digit literal.
SANDBOX, STAGING, PROD = "1" * 12, "2" * 12, "3" * 12
WHERE = {SANDBOX: "consumer", STAGING: "staging", PROD: "production"}


def table_arn(account: str, table: str, database: str = "app_dbt") -> str:
    return f"arn:aws:glue:us-west-2:{account}:table/{database}/{table}"


def event(status: str = "SUCCESS", namespace: str = "app-dbt-prod", eid: str = "e1") -> dict:
    job = {"name": "dbt-run-app_dbt", "namespace": namespace}
    return {
        "id": eid,
        "processingStatus": status,
        "eventSummary": {"openLineageRunEventSummary": {"job": job}},
    }


# ---------------------------------------------------------------------------------------- helpers


def test_a_glue_table_arn_is_labelled_by_its_account():
    assert cat.glue_table_label(table_arn(STAGING, "trades"), WHERE) == "staging:app_dbt.trades"


def test_an_account_not_read_is_elsewhere():
    assert cat.glue_table_label(table_arn("4" * 12, "trades"), WHERE) == "elsewhere:app_dbt.trades"


def test_anything_but_a_glue_table_arn_has_no_label():
    for source in ("", "s3://bucket/dzd/project/shared/app-etl/tables/t", "awsdatacatalog.a.b"):
        assert cat.glue_table_label(source, WHERE) == ""


def test_an_asset_externalidentifier_loses_its_project_suffix():
    external = table_arn(PROD, "notional_by_desk") + ".d7qcazihvr3s7k"
    assert (
        cat.asset_table_label(external, "d7qcazihvr3s7k", WHERE)
        == "production:app_dbt.notional_by_desk"
    )


def test_an_empty_externalidentifier_has_no_label():
    assert cat.asset_table_label("", "d7qcazihvr3s7k", WHERE) == ""


def run_node(name: str) -> dict:
    return {"typeName": cat.JOB_RUN_NODE_TYPE, "name": name}


def listing_node(name: str, listing: str) -> dict:
    source = cat.LISTING_NODE_PREFIX + listing
    return {"typeName": cat.DATASET_NODE_TYPE, "name": name, "sourceIdentifier": source}


ASSET_NODE = {
    "typeName": cat.DATASET_NODE_TYPE,
    "name": "trades",
    "sourceIdentifier": cat.ASSET_NODE_PREFIX + "da1fycta6l71n4",
}


def test_a_run_node_names_its_job_without_the_run():
    run = run_node("app-dbt-prod.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run/01a2")
    assert cat.feeder(run) == (
        "job",
        "app-dbt-prod.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run",
    )


def test_a_run_node_name_loses_its_account():
    run = run_node(f"redshift://w.{SANDBOX}.x:5439.q/7#1")
    assert cat.feeder(run) == ("job", "redshift://w.ACCOUNT.x:5439.q")


def test_a_listing_node_feeds_a_subscriptions_table():
    # test-experimentation's trades link hangs from the lake listing's node (measured 2026-11-24).
    node = listing_node("trades", "b3bagfgnvev3tc")
    assert cat.feeder(node) == ("listing", "trades (b3bagfgnvev3tc)")


def test_any_other_dataset_node_is_a_plain_node():
    assert cat.feeder(ASSET_NODE) == ("node", "trades")


def test_a_version_with_no_upstream_has_no_feeder():
    assert cat.feeders([]) == ("", "")
    assert cat.fed_by_label("", "") == "no run"


def test_two_listings_feed_one_table_as_one_listing_reading():
    nodes = [listing_node("trades", "bx8v3rafykv3ww"), listing_node("trades", "b3bagfgnvev3tc")]
    kind, names = cat.feeders(nodes)
    assert kind == "listing" and names == "trades (b3bagfgnvev3tc), trades (bx8v3rafykv3ww)"
    assert cat.fed_by_label(kind, names).startswith("listing trades (b3bag")


def test_a_run_among_the_feeders_makes_the_version_a_jobs():
    nodes = [listing_node("trades", "b3bagfgnvev3tc"), run_node("job.x/run1")]
    assert cat.feeders(nodes)[0] == "job"


def test_a_listing_beside_a_plain_node_is_a_plain_reading():
    nodes = [listing_node("trades", "b3bagfgnvev3tc"), ASSET_NODE]
    assert cat.feeders(nodes)[0] == "node"


# ---------------------------------------------------------------------------------------- CT-21


def test_ct21_an_unread_listing_is_a_note_never_a_pass():
    result, detail = cat.event_verdict([], "2026-11-17T00:00:00Z", read=False)
    assert result == "note" and "an absence, not a pass" in detail


def test_ct21_an_empty_window_is_a_note_never_a_pass():
    result, detail = cat.event_verdict([], "2026-11-17T00:00:00Z", read=True)
    assert result == "note" and detail.startswith("no event since 2026-11-17T00:00:00Z")


def test_ct21_every_event_success_passes_with_its_namespaces():
    events = [event(), event(namespace="default", eid="e2"), event(namespace="default", eid="e3")]
    result, detail = cat.event_verdict(events, "2026-11-17T00:00:00Z", read=True)
    assert result == "pass"
    assert "3 event(s)" in detail and "app-dbt-prod 1, default 2" in detail


def test_ct21_a_redshift_namespace_loses_its_account():
    events = [event(namespace=f"redshift://w.{SANDBOX}.us-west-2:5439")]
    _, detail = cat.event_verdict(events, "2026-11-17T00:00:00Z", read=True)
    assert SANDBOX not in detail and "ACCOUNT" in detail


def test_ct21_a_failed_event_fails_and_is_named():
    events = [event(), event("FAILED", eid="bad1")]
    result, detail = cat.event_verdict(events, "2026-11-17T00:00:00Z", read=True)
    assert result == "fail" and "bad1" in detail and "1 of 2" in detail


def test_ct21_an_event_in_flight_is_a_note():
    events = [event(), event("PROCESSING", eid="e2"), event("REQUESTED", eid="e3")]
    result, detail = cat.event_verdict(events, "2026-11-17T00:00:00Z", read=True)
    assert result == "note" and "1 PROCESSING" in detail and "1 REQUESTED" in detail


def test_ct21_a_failed_event_beside_one_in_flight_fails():
    events = [event("FAILED", eid="bad1"), event("PROCESSING", eid="e2")]
    assert cat.event_verdict(events, "2026-11-17T00:00:00Z", read=True)[0] == "fail"


# ---------------------------------------------------------------------------------------- CT-22

DBT_PROD = "app-dbt-prod.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run"
DBT_DEV = "app-dbt-dev.awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run"
PROD_TABLE = "production:app_dbt.notional_by_desk"


def asset(project="deploy-production", own=PROD_TABLE, named=None, upstream=(), read=True):
    named = own if named is None else named
    deployment = project in cat.DEPLOYMENT_PROJECTS
    return cat.AssetLineage(project, deployment, "notional_by_desk", own, named, upstream, read)


def test_ct22_no_asset_and_no_gap_is_a_note_never_a_pass():
    result, detail = cat.lineage_verdict([], [])
    assert result == "note" and "an absence, not a pass" in detail


def test_ct22_an_unread_inventory_is_a_note_in_one_clean_sentence():
    result, detail = cat.lineage_verdict([], ["deploy-staging"])
    assert result == "note"
    assert detail == (
        "not read: the inventory of deploy-staging; "
        "0 from their own table's job run, 0 from a subscription's listing"
    )


def test_ct22_its_own_node_written_by_a_run_passes():
    row = asset(upstream=((PROD_TABLE, "job", DBT_PROD),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "pass"
    assert detail == (
        "1 asset(s) in 1 project(s), each hanging from its own table's node: "
        "1 from their own table's job run, 0 from a subscription's listing"
    )


def test_ct22_a_subscriptions_table_fed_by_its_listing_passes():
    # test-experimentation's trades: its link's node hangs from the lake listing's node.
    own = "consumer:glue_db_4zojr4rr6bmnww.trades"
    fed = ("listing", "trades (b3bagfgnvev3tc), trades (bx8v3rafykv3ww)")
    row = asset("test-experimentation", own, upstream=((own, *fed),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "pass" and detail.endswith(
        "0 from their own table's job run, 1 from a subscription's listing"
    )


def test_ct22_its_own_node_fed_by_a_plain_node_is_a_note():
    own = "consumer:app_dbt.t"
    row = asset("app-dbt-dev", own, upstream=((own, "node", "trades"),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "note" and "fed by trades's node" in detail


def test_ct22_a_deployment_asset_whose_own_node_no_run_wrote_fails():
    row = asset(upstream=((PROD_TABLE, "", ""),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "fail" and "SUP-097" in detail


def test_ct22_a_sandbox_asset_whose_own_node_no_run_wrote_is_a_note():
    own = "consumer:app_dbt.t"
    row = asset("app-dbt-dev", own, upstream=((own, "", ""),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "note" and "no job run wrote" in detail


def test_ct22_the_import_window_shape_of_2026_11_24_is_a_note():
    # Staging's notional_by_desk at the import's revision: forms and node both Sandbox's.
    row = asset(
        "deploy-staging",
        own="staging:app_dbt.notional_by_desk",
        named="consumer:app_dbt.notional_by_desk",
        upstream=(("consumer:app_dbt.notional_by_desk", "job", DBT_DEV),),
    )
    result, detail = cat.lineage_verdict([row], [])
    assert result == "note"
    assert "SUP-483" in detail and "SUP-454" in detail and DBT_DEV in detail


def test_ct22_another_accounts_node_with_its_own_forms_is_a_note_without_the_window():
    row = asset(upstream=(("consumer:app_dbt.notional_by_desk", "job", DBT_DEV),))
    result, detail = cat.lineage_verdict([row], [])
    assert result == "note" and "SUP-483" in detail and "SUP-454" not in detail


def test_ct22_a_deployment_asset_on_no_node_with_its_own_forms_fails():
    result, detail = cat.lineage_verdict([asset()], [])
    assert result == "fail" and "hangs from no dataset node" in detail


def test_ct22_a_deployment_asset_on_no_node_in_the_import_window_is_a_note():
    row = asset(named="consumer:app_dbt.notional_by_desk")
    assert cat.lineage_verdict([row], [])[0] == "note"


def test_ct22_a_sandbox_asset_on_no_node_is_a_note():
    row = asset("eighth-experimentation", "consumer:lab.t")
    assert cat.lineage_verdict([row], [])[0] == "note"


def test_ct22_an_unread_node_is_a_note():
    row = asset(read=False)
    result, detail = cat.lineage_verdict([row], [])
    assert result == "note" and "its lineage not read" in detail


def test_ct22_a_failure_reports_the_notes_beside_it():
    own = "consumer:app_dbt.t"
    rows = [asset(), asset("app-dbt-dev", own, upstream=((own, "", ""),))]
    result, detail = cat.lineage_verdict(rows, [])
    assert result == "fail" and "SUP-097" in detail and "no job run wrote" in detail


# ---------------------------------------------------------------------------------------- CT-23


def test_ct23_no_node_and_nothing_unread_is_a_note_never_a_pass():
    result, detail = cat.orphan_verdict([], set(), [])
    assert result == "note" and "an absence, not a pass" in detail


def test_ct23_every_node_carried_passes():
    nodes = [("6w7hp2vvi8kscw", "consumer:app_dbt.notional_by_desk")]
    assert cat.orphan_verdict(nodes, {"6w7hp2vvi8kscw"}, [])[0] == "pass"


def test_ct23_the_targets_own_nodes_left_behind_are_a_note():
    nodes = [
        ("6w7hp2vvi8kscw", "consumer:app_dbt.notional_by_desk"),
        ("dc5kf0jitjz91s", "production:app_dbt.notional_by_desk"),
        ("4epfbzmhyf6p74", "staging:app_dbt.notional_by_desk"),
    ]
    result, detail = cat.orphan_verdict(nodes, {"6w7hp2vvi8kscw"}, [])
    assert result == "note"
    assert detail.startswith("2 of 3 Glue table node(s)")
    assert detail.index("production:") < detail.index("staging:")


def test_ct23_a_node_the_trail_created_twice_counts_once():
    nodes = [("n1", "consumer:a.t"), ("n1", "consumer:a.t")]
    assert cat.orphan_verdict(nodes, set(), [])[1].startswith("1 of 1")


def test_ct23_an_unread_side_is_a_note_that_still_names_the_orphans():
    result, detail = cat.orphan_verdict([("n1", "consumer:a.t")], set(), ["the registry's trail"])
    assert result == "note" and "not read: the registry's trail" in detail and "n1" in detail


# ---------------------------------------------------------------------------------------- CT-24

README = "# notional_by_desk\n\nThe notional each desk traded."
DEV = cat.Curation(
    "The notional each desk traded.", README, "internal", "consumer:app_dbt.notional_by_desk"
)
OWN = "production:app_dbt.notional_by_desk"


def pair(mine, dev=DEV, dev_project="app-dbt-dev"):
    return ("deploy-production", "notional_by_desk", OWN, mine, dev_project, dev)


def test_ct24_no_deployment_asset_and_no_gap_is_a_note_never_a_pass():
    result, detail = cat.curation_verdict([], [])
    assert result == "note" and "an absence, not a pass" in detail


def test_ct24_an_unread_inventory_is_a_note_in_one_clean_sentence():
    result, detail = cat.curation_verdict([], ["app-dbt-dev"])
    assert (
        result == "note"
        and detail == "not read: the inventory of app-dbt-dev; 0 as their dev asset"
    )


def test_ct24_the_curation_carried_and_its_own_table_named_passes():
    mine = DEV._replace(named=OWN)
    result, detail = cat.curation_verdict([pair(mine)], [])
    assert result == "pass" and detail.startswith("1 asset(s)")


def test_ct24_the_import_window_shape_of_2026_11_24_is_a_note():
    # The import's revision: the curation equal, the forms naming Sandbox's table.
    result, detail = cat.curation_verdict([pair(DEV)], [])
    assert result == "note" and "SUP-454" in detail and "differ" not in detail


def test_ct24_a_readme_edited_in_dev_after_the_release_is_a_note():
    mine = DEV._replace(readme=README + "\nMore.", named=OWN)
    result, detail = cat.curation_verdict([pair(mine)], [])
    assert result == "note" and "its README differ from app-dbt-dev's" in detail


def test_ct24_a_missing_classification_differs():
    mine = DEV._replace(classification=None, named=OWN)
    assert "classification" in cat.curation_verdict([pair(mine)], [])[1]


def test_ct24_an_asset_no_dev_project_holds_is_a_note():
    mine = DEV._replace(named=OWN)
    result, detail = cat.curation_verdict([pair(mine, dev=None, dev_project="")], [])
    assert result == "note" and "no chain application's dev project" in detail
