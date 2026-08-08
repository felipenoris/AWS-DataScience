# D27 — Catalog-maintenance compute in the Data OU: crawlers and optimizers

**Status:** Decided (2026-08-08): **Glue Crawlers for the raw zone and the ingestion drop-box run in Data Governance, under a named catalog-maintenance exception to the Data OU SCP; no crawler ever points at an Iceberg table**

**In one line:** Crawlers and table optimizers may run in Data Governance under a named catalog-maintenance exception; never on Iceberg tables.

**Related decisions:** [D25](D25-drop-box-consumer.md)

**Referenced by stages:** [Stage 1a](../stages/stage-01a-landing-zone.md), [Stage 5](../stages/stage-05-data-foundation.md)

---

## Rationale and consequences

The 2026-08-08 revision asks for crawlers on the data-lake buckets; D25 had just tightened the Data OU SCP to deny all Glue compute. The collision is resolved by distinguishing **user compute** (ETL jobs, dev endpoints, notebooks, interactive sessions — still denied, no exception) from **the catalog's own maintenance** (crawlers, Iceberg compaction/table optimizers, column statistics — allowed, startable only by the lake's maintenance role, which is not assumable interactively). The exception must be *named*, not smuggled: a crawler samples object contents to infer schema, so it does read data — the honest statement is "no compute here **except** the bounded set that produces catalog metadata, under one role, alarmed". **Scope:** crawlers only where schema arrives from outside — the raw zone and the drop-box, where files land whose shape nobody declared. **Never on Iceberg tables**: Iceberg is catalog-native; a crawler would at best duplicate what the catalog already knows and at worst fight the table's own metadata. **Trigger:** EventBridge on drop-box object creation, or on demand before a pickup run (D25) — never a standing schedule; a crawler run bills per DPU-hour with a 10-minute minimum, so cron-always would out-cost the storage it catalogs. **SCP mechanics:** the deny list from D25 stays; add a condition carve-out for `glue:StartCrawler`/`CreateCrawler` and the table-optimizer/statistics actions when the principal is the maintenance role.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
