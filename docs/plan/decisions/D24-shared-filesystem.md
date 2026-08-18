# D24 — Where the shared filesystem lives, now that there are two Studio domains

**Status:** **Withdrawn (2026-08-17)** — the user removed the NFS requirement from `docs/plan/objectives.md` in the same sitting. **There is no shared filesystem in this design, in any account, and no stage builds one.** This decision answered *where the required filesystem lives*; with the requirement gone there is nothing left for it to place.

**In one line:** Decided 2026-08-08 (EFS in Sandbox only), withdrawn 2026-08-17 with the requirement itself — no EFS anywhere; file exchange between users, SageMaker and S3 is S3 and git.

**Related decisions:** [D21](D21-development-account.md)

**Referenced by stages:** — (the stages that used to consume it no longer do: [Stage 3](../stages/stage-03-networking.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 11](../stages/stage-11-dlp.md), [Stage 14](../stages/stage-14-sandbox-vending.md))

---

## What survives this decision, and it is the part that matters

**The argument against a Sandbox↔Development file path outlives the filesystem it was made for.** The original decision declined a second EFS and declined a peering, because a convenience path between the two Interactive accounts would weaken the property that graduation is a *rewrite* (D21). That reasoning now holds trivially: with no filesystem at all, the exchange between the Interactive accounts is what it always was on the graduation path — **S3 and git** — and D21 carries it without this file's help.

**What the withdrawal removed beyond the resource itself:** the one *data-bearing* resource type no RCP reaches and no SCP was worth writing for (`docs/plan/architecture.md` §4.2) — the accepted risk D19 named and Stage 11's threat model was to carry — and the three audit gaps `docs/plan/institutional-delta.md` records in its Shared-storage row (POSIX identity untied to SSO, no data-event trail for NFS, `restricted` copies invisible to Macie). A copy that cannot be made needs no control.

## The original decision (2026-08-08), kept for its reasoning

D21 created a second Studio domain, and the NFS requirement ("exchange files between users, the SageMaker environment and S3 buckets") did not automatically follow it. Three options were on the table: a second EFS in Development, a Sandbox↔Development VPC peering carrying NFS, or leaving the filesystem where it was. The choice was the third — EFS in Sandbox only, where the VPN terminates and where the human file-exchange use case actually was, with Development getting neither its own nor a path to it. A second EFS costs cents but doubles a stateful `[P]` resource and creates the question nobody wants to answer at 23:00 — *which* of the two copies of a file is current. A peering would have been the first network path between the two Interactive accounts, built for file convenience rather than for a requirement.

**If a genuine POSIX need ever arrives** (a training job that will not read from S3, a tool that mmaps), that is a *new requirement*, decided on its own terms — not this decision reopening.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
