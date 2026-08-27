# D19 — The derived zone — what Lake Formation does *not* do (extends D13)

**Status:** Decided (2026-08-07); **revised 2026-08-26 by the user — the zone is RE-HOMED onto the SMUS project path** (`awsds-<env>-smus-projects`, per-project folders, managed by the service). The principle stands: **the copy is not prevented; the destination is managed and the perimeter contains it** — what moved is which destination, and whose hand manages it

**In one line:** The derived copy is not prevented; the destination is managed and the perimeter contains it. Since 2026-08-26 the destination is the SMUS project path, its CMK is the project CMK, and `awsds-<env>-derived` is removed.

**Related decisions:** [D5](D05-sagemaker-egress.md), [D6](D06-dlp-approach.md), [D13](D13-lake-formation-enforcement.md), [D18](D18-data-scientist-access.md), [D24](D24-shared-filesystem.md), [D31](D31-approver-read.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 5](../stages/stage-05-data-foundation.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Running a `SELECT` against the lake and storing the result is what a data science environment is *for*. Any principal that can read tabular data can materialise it outside the governed prefixes, and no configuration changes that. This is not a hole introduced by D18 — it has been true of the Sandbox since Stage 5, and of every SageMaker installation ever built. What it actually means is worth stating plainly: **Lake Formation's column and row filters are an entitlement mechanism, not a containment mechanism.** They decide what a principal may see at the moment of read; they say nothing about where the bytes go next. D13 makes the entitlement real; this decision covers everything after it. The practice: (i) **the output location is not the user's choice** — the Athena workgroup sets `EnforceWorkGroupConfiguration = true`, so a client cannot override the result location, and `s3:PutObject` on execution roles and permission sets is scoped to enumerated prefixes, never `*`; (ii) derived prefixes are **per principal** (`…/derived/${aws:userid}/`), so one person's copy is not a way around another person's grants; (iii) they carry a **lifecycle expiry**, so the shadow lake does not become permanent by accident; (iv) they sit **inside Macie's scan scope and carry CloudTrail data events** (Stage 11), because this is where sensitive data actually accumulates; (v) classification **inherits** — the output of a query over `restricted` data is `restricted` — stated as policy, because nothing enforces it automatically at this scale (`docs/plan/institutional-delta.md`: this is exactly where a catalog with lineage earns its price). **And the containment itself comes from somewhere else entirely:** the copy is tolerable because the data perimeter (`docs/plan/architecture.md` §4.2) stops it leaving the organization and D5 stops it leaving the network. Preventing the copy was never the control. The perimeter is. **Revised 2026-08-08 (D31): a sixth practice, and it is the only one on this list that is default-deny.** The five above answer *where the copy lands*, *how long it lives* and *who is told about it*; none of them answers **who may read it**, which was left to whatever IAM policies happened to exist — and that turned out to be how a release approver acquired read access to materialised `restricted` data without anyone deciding it. So the derived zone gets **its own KMS CMK**, separate from the account's general-purpose key, and the key policy carries the answer: `kms:Decrypt` to the project execution roles and `DataScientistAccess`, and to nobody else. It survives forgetfulness in a way a prefix deny-list does not — a new derived prefix under the same key is covered without anyone updating anything.

**Revised 2026-08-12 (D6) — the containment sentence was true of this decision's own object and was stated
more broadly than that.** "The perimeter stops it leaving the organization" holds exactly where the derived
copy lands: **S3 under a KMS CMK**, and RCPs cover both. It does *not* hold as a general claim about derived
data, because **the perimeter is scoped by resource type**, and five of the types IAM Access Analyzer reports
on have no RCP behind them at all (`docs/plan/architecture.md` §4.2). Two of those reach this decision:

- **EBS and RDS snapshots — the route that bypasses everything this decision leans on.** Derived bytes read
  onto a Studio space's volume leave the organization through `ec2:CreateSnapshot` followed by
  `ec2:ModifySnapshotAttribute`: two API calls, **no network path**, so neither the perimeter's
  `aws:ResourceOrgID` write deny nor D5's egress design is anywhere in that route. **It is closed
  preventively instead**, by an unconditional deny in the organization-root SCP set — **Stage 1c step 7.5**.
  RCPs are limited to a service list and SCPs are not, which is the whole reason the fix lands on the
  identity side rather than beside the rest of the perimeter.
- **EFS (D24) — retired 2026-08-17.** This bullet used to record the one route nothing closed: no RCP
  covers `elasticfilesystem`, no SCP was worth writing, and the residual was carried by Access Analyzer's
  external-access findings as an accepted risk (Lesson 5). The NFS requirement was then withdrawn from
  `objectives.md` and D24 with it — no filesystem exists, and the accepted risk went with the resource.

**Revised 2026-08-19 (Stage 5 pass 4, the sitting that built it) — two corrections of shape, neither of
which moves the decision.** Practice (vi)'s key is `alias/awsds-<env>-zn-lab`, **not** `-derived`: the
user amended `security-zone`'s scope so that encryption granularity is that dimension's job in every
account rather than only inside the lake — a query result over a `zn-lab` table is still `zn-lab` data,
which is practice (v) applied to the key. **One CMK per (zone × account)**; sharing the *lake's* key
across the account line was declined on a measurement, `AllowProductionPickupDecryptViaS3` carrying no
bucket scoping. The applied key policy also delegates *administration* to the account root while
withholding every cryptographic action, so no IAM policy in the account can grant `Decrypt` behind this
decision — which is what "the key policy is the answer" has to mean to be true.

And **`scratch` is a prefix in the same bucket, not a bucket of its own.** Three files credited this
decision for a "scratch + derived-zone *buckets*" pairing it never contained; the origin is D13's
*"non-registered prefixes (scratch, artifacts, model outputs)"*. The applied shape is one bucket with
three prefix families — `results/` (the workgroup's enforced output, per-persona because an enforced
workgroup has exactly one), `derived/${aws:userid}/` (practice ii), `scratch/`.

**Also revised 2026-08-19 (pass 4c, following Stage 5 decision 6) — practice (ii) is per principal on
WRITE only.** The applied persona statements grant `s3:PutObject` under `derived/${aws:userid}/` but
`s3:GetObject` across `derived/*`, at decision 6's persona grain — so (ii) contains who may *create or
overwrite* a copy, not who may read one: another holder of `DataScientistAccess` can read a materialised
copy. What keeps other personas out is practice (vi), the zone CMK (D31), which is what that practice was
added for. The per-user `s3:GetObject` variant was mapped (`docs/GOVERNANCE.md` §"The grain") and
declined with the grain decision.

**Revised once more 2026-08-19, later the same day — the `security-zone` dimension is withdrawn (the
user's revision) and practice (vi)'s key is `alias/awsds-<env>-data`.** The zone framing two blocks up is
kept as history: the (zone × account) form rested on the premise that the CMK was associated with an
LF-Tag, and no AWS mechanism makes that association — the tag-to-key link was only a naming convention.
The rule's carrier is now the account: **one data CMK per account**, assigned to buckets by Terraform
(`GOVERNANCE.md` §Encryption). Nothing this decision leans on moves: the key is still dedicated (not the
account's `tfstate` key), still deliberately not the lake's (the measured
`AllowProductionPickupDecryptViaS3` reason stands verbatim), and its policy still delegates
administration to root while withholding every cryptographic action.

**The decision itself does not move.** Preventing the copy is still impossible, the destination is still
managed, and the six practices above all stand. What is corrected is a claim about *who does the
containing*: for the derived zone in S3 it is the perimeter, exactly as written; for the routes derived
bytes can be moved *onto*, it is one named SCP and — where none exists — an accepted risk with a name.

---

## Revised 2026-08-26 — the zone re-homed onto the SMUS project path (the user's decision)

**What was measured, the same day, before the choice** (Stage 6 step 2.4's reading): the Tooling
blueprint gives every project an **enforced** Athena workgroup writing into
`awsds-<env>-smus-projects` under `<domain-id>/<project-id>/dev/sys/athena/`, and a `shared/` scope
mounted as the working folder in JupyterLab. That is, per project, the results-and-scratch shape this
decision had built per account — **two designed destinations for the same class of data**, which is
exactly the "second, undesigned copy zone" the enforced-location argument exists to prevent, except
both were designed. One had to go, and the user chose to keep the service's: **the SMUS project path IS
the derived zone**, organised by project folder, managed by SMUS.

**What is removed** (consumer-data `v0.6.0` + the same-day `identity/sso/` edit): the
`awsds-<env>-derived` bucket in both Interactive accounts, the enforced `awsds-<env>-athena`
workgroup, and the persona's whole direct query path — `DataScientistAccess` carries **no `athena:`
action at all** now; a data scientist queries through a SMUS project, as the project role, into the
project path. The account data CMK (`alias/awsds-<env>-data`) **survives with a different consumer**:
the sandbox lake encrypts under it (Stage 16), so the key stays and only the persona's statement
leaves its policy — in Development it stands empty, held for the account's next data bucket, the
explicit no-consumer branch dated rather than drifting. Stage 5 step 9.3's extension point (the
data-key `Decrypt` second principal for project roles) **dies unconsumed** — a project role never
needed the data key, because its results never land under it.

**The six practices, re-read against the new home:**

- **(i) enforced output location** — HOLDS, per project now: the project workgroup carries
  `EnforceWorkGroupConfiguration = true` (measured 2026-08-26), and the write scoping is the managed
  provisioning policy's path shape plus S3 Access Grants, both project-grained.
- **(ii) per-principal prefixes** — WITHDRAWN. The project path has **no person grain** (measured:
  `shared/` is project-wide); the containment grain moves from the person to the **project**, which is
  Stage 5 decision 6's grain applied one level up. Attribution of who wrote a copy moves to Stage 11's
  CloudTrail data events, which carry the principal per object write.
- **(iii) lifecycle expiry** — **OPEN, and currently ABSENT**: the projects bucket has no rule on
  current objects, and a deleted project keeps its prefix (both measured 2026-08-26). **Open question
  25 is now this decision's expiry question** — the bucket is Terraform's (`sagemaker-prereqs`), so a
  lifecycle rule is addable without touching anything SMUS manages; the number is the user's.
- **(iv) Macie + data events** — MOVED with the zone: Stage 11's scope and trail map now name
  `awsds-<env>-smus-projects` (and no longer the removed buckets); `./aws/dlp.py` `DP-4` re-aimed.
- **(v) classification inheritance** — UNCHANGED: a policy statement either way, enforced by nobody.
- **(vi) the CMK read control (D31)** — RE-HOMED onto the **project CMK** (`alias/awsds-<env>-project`),
  whose policy names the service principals, the domain execution role and the project roles — not the
  persona, not the approver. The approver-side half of D31 survives untouched: `DeploymentManagerAccess`
  still carries its explicit `kms:Decrypt` deny.

**What this deliberately gives up, so it is chosen rather than discovered**: the persona-direct lake
query (the Stage 5 pandas-pair surface — future share proofs run inside a project); the per-person
write attribution at the prefix grain; and the 30-day shedding, until OQ 25 lands. **What it buys**:
one destination instead of two, no contract between our prefix families and the service's tree, and a
zone whose management cost is the service's.

**Production is not covered by this revision.** It has no SMUS (D28), so where Stage 9's job results
land is that stage's to re-decide at its revision — the module no longer provides a derived zone, and
`aws/deploytargets.py` carries the dated note.

**The persona's LF re-grants stay** (the lake-consumption machinery — settings, resource links,
re-grants — is what SMUS subscriptions ride and what catalog visibility needs); whether the persona's
own `SELECT` re-grants retire now that no persona engine exists is re-read at Stage 9/14, not decided
here.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
