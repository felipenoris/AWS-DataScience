"""The transformer OpenLineage's transform transport runs on each event before the post: every
Athena dataset renamed to the form AWS's lineage page turns into the Glue table's ARN.

The wrapper names a dataset of the athena adapter `<catalog>.<database>.<table>` under the namespace
`awsathena://athena.<region>.amazonaws.com`, the Glue table beside it as a symlink. `GlueTableNames`
rewrites each such dataset of an event, the inputs, the outputs and every input field of a
`columnLineage` facet, to the namespace `arn:aws:glue:<region>:<account>:table` and the name
`<database>/<table>`. The symlinks and every other facet stay as built. A dataset under another
namespace, or in a catalog other than the account's Glue Data Catalog, keeps its name.

run-dbt.sh names the class in openlineage.yml when its --names is glue-arn:

    transport:
      type: transform
      transformer_class: app_dbt.lineage.GlueTableNames
      transformer_properties:
        region: us-west-2
        account_id: "<account id>"
      transport:
        type: amazon_datazone_api
        domainId: <domain id>
        region: us-west-2

The transport hands the transformer a copy of the event, so the renaming changes nothing the wrapper
keeps.
"""

from __future__ import annotations

from typing import Any

from openlineage.client import event_v2
from openlineage.client.transport.transform import EventTransformer

# The catalog dbt-athena names in front of a table of the account's Glue Data Catalog.
GLUE_CATALOG = "awsdatacatalog"
PROPERTIES = ("region", "account_id")


def athena_namespace(region: str) -> str:
    """The namespace the wrapper gives a dataset of the athena adapter."""
    return f"awsathena://athena.{region}.amazonaws.com"


def glue_namespace(region: str, account_id: str) -> str:
    """The namespace of a Glue table; with `/<database>/<table>` after it, the table's ARN."""
    return f"arn:aws:glue:{region}:{account_id}:table"


class GlueTableNames(EventTransformer):
    """Each Athena dataset of a run event under the Glue table's name."""

    def __init__(self, properties: dict[str, Any]) -> None:
        missing = [name for name in PROPERTIES if not properties.get(name)]
        if missing:
            raise RuntimeError(
                f"{type(self).__name__} needs {' and '.join(missing)} in transformer_properties"
            )
        super().__init__(properties=properties)
        region, account_id = (str(properties[name]) for name in PROPERTIES)
        self.athena = athena_namespace(region)
        self.glue = glue_namespace(region, account_id)

    def rename(self, namespace: str, name: str) -> tuple[str, str]:
        """The Glue form of an Athena dataset's namespace and name; any other pair unchanged."""
        parts = name.split(".")
        if namespace != self.athena or len(parts) != 3 or parts[0] != GLUE_CATALOG:
            return namespace, name
        return self.glue, f"{parts[1]}/{parts[2]}"

    def transform(self, event: Any) -> Any:
        """The event with its datasets and their column lineage renamed; an event that is not a run
        event, which DataZone does not take, unchanged."""
        if not isinstance(event, event_v2.RunEvent):
            return event
        for dataset in [*(event.inputs or []), *(event.outputs or [])]:
            dataset.namespace, dataset.name = self.rename(dataset.namespace, dataset.name)
            lineage = (dataset.facets or {}).get("columnLineage")
            if lineage is None:
                continue
            fields = [field for column in lineage.fields.values() for field in column.inputFields]
            for field in [*fields, *(lineage.dataset or [])]:
                field.namespace, field.name = self.rename(field.namespace, field.name)
        return event
