"""app_dbt.lineage.GlueTableNames over the events the simulation recorded (tests/simulation/): the
events the wrapper posted with the names as built, renamed, are the events it posted through the
transformer; any other dataset keeps its names, and an event that is not a run event passes
unchanged."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from openlineage.client import event_v2
from openlineage.client.generated.column_lineage_dataset import (
    ColumnLineageDatasetFacet,
    Fields,
    InputField,
)
from openlineage.client.generated.symlinks_dataset import Identifier, SymlinksDatasetFacet
from openlineage.client.serde import Serde
from openlineage.client.transport.transform import TransformConfig, TransformTransport

from app_dbt.lineage import GlueTableNames

FIXTURES = Path(__file__).resolve().parent / "fixtures"
PROPERTIES = {"region": "us-west-2", "account_id": "000000000000"}
GLUE = "arn:aws:glue:us-west-2:000000000000:table"
ATHENA = "awsathena://athena.us-west-2.amazonaws.com"


def fixture(name: str) -> list[dict[str, Any]]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def field(data: dict[str, Any]) -> InputField:
    return InputField(namespace=data["namespace"], name=data["name"], field=data["field"])


def dataset(kind: type, data: dict[str, Any]) -> Any:
    """A dataset of a recorded event with the facets the transformer reads or must keep."""
    facets: dict[str, Any] = {}
    recorded = data.get("facets") or {}
    if "columnLineage" in recorded:
        lineage = recorded["columnLineage"]
        facets["columnLineage"] = ColumnLineageDatasetFacet(
            fields={
                name: Fields(inputFields=[field(item) for item in column["inputFields"]])
                for name, column in lineage["fields"].items()
            },
            dataset=[field(item) for item in lineage.get("dataset") or []],
        )
    if "symlinks" in recorded:
        facets["symlinks"] = SymlinksDatasetFacet(
            identifiers=[
                Identifier(namespace=item["namespace"], name=item["name"], type=item["type"])
                for item in recorded["symlinks"]["identifiers"]
            ]
        )
    return kind(namespace=data["namespace"], name=data["name"], facets=facets)


def event(data: dict[str, Any]) -> event_v2.RunEvent:
    return event_v2.RunEvent(
        eventType=event_v2.RunState(data["eventType"]),
        eventTime=data["eventTime"],
        run=event_v2.Run(runId=data["run"]["runId"]),
        job=event_v2.Job(namespace=data["job"]["namespace"], name=data["job"]["name"]),
        inputs=[dataset(event_v2.InputDataset, item) for item in data.get("inputs", [])],
        outputs=[dataset(event_v2.OutputDataset, item) for item in data.get("outputs", [])],
        producer=data["producer"],
    )


def names(data: dict[str, Any]) -> tuple[Any, ...]:
    """An event's job, and each dataset's names, column lineage and symlinks."""
    found = []
    for kind in ("inputs", "outputs"):
        for item in data.get(kind) or []:
            facets = item.get("facets") or {}
            lineage = facets.get("columnLineage") or {"fields": {}}
            columns = sorted(
                (column, source["namespace"], source["name"], source["field"])
                for column, value in lineage["fields"].items()
                for source in value["inputFields"]
            )
            links = sorted(
                (link["namespace"], link["name"])
                for link in (facets.get("symlinks") or {}).get("identifiers", [])
            )
            found.append((kind, item["namespace"], item["name"], columns, links))
    return data["eventType"], data["job"]["name"], found


def test_the_fixtures_are_the_six_events_of_a_build_in_both_forms():
    as_built, glue = fixture("events-as-built.json"), fixture("events-glue-arn.json")
    expected = [
        ("START", "dbt-run-app_dbt"),
        ("START", "awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run"),
        ("START", "awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.test"),
        ("COMPLETE", "awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.run"),
        ("COMPLETE", "awsdatacatalog.app_dbt.app_dbt.notional_by_desk.build.test"),
        ("COMPLETE", "dbt-run-app_dbt"),
    ]
    for events in (as_built, glue):
        assert [(item["eventType"], item["job"]["name"]) for item in events] == expected
    datasets = {(d["namespace"], d["name"]) for e in as_built for d in e["inputs"] + e["outputs"]}
    assert datasets == {
        (ATHENA, "awsdatacatalog.app_dbt.trades"),
        (ATHENA, "awsdatacatalog.app_dbt.notional_by_desk"),
    }


def test_the_transformer_gives_each_event_the_names_the_wrapper_posted_through_it():
    transformer = GlueTableNames(PROPERTIES)
    as_built, glue = fixture("events-as-built.json"), fixture("events-glue-arn.json")
    renamed = [names(Serde.to_dict(transformer.transform(event(item)))) for item in as_built]
    assert renamed == [names(item) for item in glue]
    model = renamed[1][2][1]
    assert model[:3] == ("outputs", GLUE, "app_dbt/notional_by_desk")
    assert model[3] == [
        ("desk", GLUE, "app_dbt/trades", "desk"),
        ("notional", GLUE, "app_dbt/trades", "price"),
        ("notional", GLUE, "app_dbt/trades", "quantity"),
    ]
    assert model[4] == [("arn:aws:glue:us-west-2:000000000000", "table/app_dbt/notional_by_desk")]


@pytest.mark.parametrize(
    ("namespace", "name"),
    [
        ("s3://bucket", "app-dbt/inbox"),
        (ATHENA, "app_dbt.trades"),
        (ATHENA, "othercatalog.app_dbt.trades"),
        ("awsathena://athena.eu-west-1.amazonaws.com", "awsdatacatalog.app_dbt.trades"),
    ],
)
def test_any_other_dataset_keeps_its_names(namespace, name):
    before = event_v2.RunEvent(
        eventType=event_v2.RunState.START,
        eventTime="2026-11-17T00:00:00+00:00",
        run=event_v2.Run(runId="01a1e9f0-4da7-7507-a796-cf3ea8e6ad1e"),
        job=event_v2.Job(namespace="app-dbt", name="job"),
        inputs=[event_v2.InputDataset(namespace=namespace, name=name)],
    )
    after = GlueTableNames(PROPERTIES).transform(before)
    assert (after.inputs[0].namespace, after.inputs[0].name) == (namespace, name)


def test_an_event_that_is_not_a_run_event_passes_unchanged():
    job = event_v2.JobEvent(
        eventTime="2026-11-17T00:00:00+00:00",
        job=event_v2.Job(namespace="app-dbt", name="job"),
        inputs=[event_v2.InputDataset(namespace=ATHENA, name="awsdatacatalog.app_dbt.trades")],
    )
    assert GlueTableNames(PROPERTIES).transform(job) is job
    assert job.inputs[0].namespace == ATHENA


@pytest.mark.parametrize(
    ("properties", "missing"),
    [({}, "region and account_id"), ({"region": "us-west-2"}, "account_id")],
)
def test_the_transformer_needs_its_properties(properties, missing):
    with pytest.raises(RuntimeError, match=f"GlueTableNames needs {missing} in transformer"):
        GlueTableNames(properties)


def test_the_transform_transport_loads_the_class_run_dbt_names(tmp_path):
    """The transport run-dbt.sh configures for --names glue-arn, its inner transport a file."""
    written = tmp_path / "events.jsonl"
    config = TransformConfig.from_dict(
        {
            "transformer_class": "app_dbt.lineage.GlueTableNames",
            "transformer_properties": PROPERTIES,
            "transport": {"type": "file", "log_file_path": str(written), "append": True},
        }
    )
    transport = TransformTransport(config)
    for item in fixture("events-as-built.json"):
        transport.emit(event(item))
    emitted = [json.loads(line) for line in written.read_text().splitlines()]
    assert [names(item) for item in emitted] == [names(e) for e in fixture("events-glue-arn.json")]
