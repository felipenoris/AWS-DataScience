# D24 — Where the shared filesystem lives, now that there are two Studio domains

**Status:** Decided (2026-08-08): **EFS in Sandbox only; there is no shared filesystem in Development and no network path to Sandbox's**

**In one line:** EFS in Sandbox only; Development gets neither its own nor a path to it — the exchange is S3 and git.

**Related decisions:** [D21](D21-development-account.md)

**Referenced by stages:** [Stage 5](../stages/stage-05-data-foundation.md), [Stage 6](../stages/stage-06-unified-studio.md)

---

## Rationale and consequences

D21 created a second Studio domain, and the NFS requirement in `CLAUDE.md` ("exchange files between users, the SageMaker environment and S3 buckets") did not automatically follow it. Three options were on the table: a second EFS in Development, a Sandbox↔Development VPC peering carrying NFS, or leaving the filesystem where it is. **The choice is the third**, and the reason it is a decision rather than an omission is that the alternatives each buy something real and are being declined on purpose. A second EFS costs cents but doubles a stateful `[P]` resource and creates the question nobody wants to answer at 23:00 — *which* of the two copies of a file is current. A peering would be the first network path between the two Interactive accounts, built for file convenience rather than for a requirement, and it would weaken the property that graduation is a *rewrite* (D21) by making it possible to simply drag files across. **What this means in practice:** the NFS requirement is served in Sandbox, which is where the VPN terminates and where the human file-exchange use case actually is. The exchange between Sandbox and Development is **S3 and git**, which is the same path the graduation itself takes — the rewrite passes through a repository either way. **Revision trigger:** the first time a Development workflow genuinely needs a POSIX filesystem (a training job that will not read from S3, a tool that mmaps), build the second EFS in `development/nfs/` from the Stage 5 module rather than reaching for the peering. Recorded in `plan/institutional-delta.md` as a lab-scale compromise: an institution gives every interactive account its own home and scratch filesystem and does not ask people to think about which account their files are in.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
