# D13 — How Lake Formation is actually enforced

**Status:** Decided (2026-08-07): **execution roles get no direct S3 access to registered locations**

**In one line:** Execution roles get NO direct S3 access to Lake Formation-registered prefixes, or every filter is decoration.

**Related decisions:** —

**Referenced by stages:** [Stage 5](../stages/stage-05-data-foundation.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Lake Formation only constrains engines that ask it. A role holding `s3:GetObject` on a registered bucket can read the raw Parquet from a notebook and every column and row filter becomes decoration. So the fine-grained access control objective in [`docs/plan/objectives.md`](../objectives.md) is only real if the SageMaker execution role's S3 permissions **exclude** the Lake Formation-registered prefixes, and tabular access goes exclusively through an LF-aware engine: Athena, Glue interactive sessions, or EMR with runtime roles. Non-registered prefixes (scratch, artifacts, model outputs) keep ordinary IAM access. Lake Formation's **hybrid access mode** is the documented migration path if a workload turns out to need both, and is a deliberate exception rather than the default. This is decided in Stage 5, before Stage 6 can bake the bypass into the execution role.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
