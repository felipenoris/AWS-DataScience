# Stage 5 — Data foundation

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 3. |
| **Consumes** | [D6](../decisions/D06-dlp-approach.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D22](../decisions/D22-data-governance-account.md), [D24](../decisions/D24-shared-filesystem.md), [D25](../decisions/D25-drop-box-consumer.md), [D26](../decisions/D26-unified-studio.md), [D27](../decisions/D27-catalog-maintenance.md), [D31](../decisions/D31-approver-read.md) |
| **Proves** | [INT-03](../integrations.md), [INT-05](../integrations.md), [INT-10](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** where data lives and how it is catalogued.

**Prerequisites:** Stage 3.

**Scope change (D22):** the governed lake — buckets, catalog, Lake Formation, classification — is built in
the **Data Governance account** (`terraform-live/data-governance/data/`), not in Sandbox. What the
environment accounts get in this stage is their *consumer* side: LF resource links, an Athena workgroup,
the scratch and derived-zone buckets (D19), and — Sandbox only — the NFS layer. The lake is written once;
the consumer slice is applied twice (Sandbox and Development), which is how the sharing shape gets proven
before Stage 9 repeats it for Production.

**To execute:**

*`data-governance/data/` — layer `[P]`; the KMS CMKs it uses live in the same account:*

1. KMS CMKs per data domain; S3 buckets `raw`, `curated`, `artifacts`, `logs` with
   versioning, encryption, **S3 Bucket Keys** (`plan/cost-model.md`), lifecycle rules, `prevent_destroy`, and a bucket policy
   that denies access not coming through the VPC endpoint (`aws:SourceVpce`) — the resource-side half of
   the trusted-networks axis in `plan/architecture.md` §4.2, complementing the endpoint policies from Stage 3.
   > **Every bucket created in this account is undeletable while the `Data` OU SCP is attached, and that
   > includes the ones created by mistake.** `DenyLakeDeletionAndDeregistration` denies `s3:DeleteBucket`
   > unconditionally — no principal carve-out, `InfrastructureAccess` included, which is the property that
   > makes it a control rather than a convention. It was written for the lake buckets and it reaches all of
   > them, so a `terraform destroy` of *anything* here stops at the first bucket, with an `AccessDenied`
   > naming the OU policy. **The amendment procedure, when a bucket genuinely has to go:** detach
   > `awsds-org-scp-ou-data` from the `Data` OU, delete, re-attach, and re-run phase 4 of
   > [`plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md) — the re-attach is not done until the
   > probes have run again, because a policy detached "for a minute" is how a ceiling goes missing for a
   > month. Two consequences to plan around rather than discover: name buckets as if they were permanent,
   > because here they are; and **this is why 1c left the `s3:DeleteBucket` half untested** — exercising it
   > means creating a bucket that then cannot be deleted. **The deny must
   carry the `aws:ViaAWSService` carve-out**, or it blocks Athena and Lake Formation vended access — the
   exact path D13 forces all tabular reads through; a bare `aws:SourceVpce` deny makes step 6 unusable.
   Take the policy shape from `data-perimeter-policy-examples` (`plan/architecture.md` §4.2). While in the bucket policy, add a
   `s3:signatureAge` cap: it bounds the lifetime of any presigned URL, the preventive counterpart of the
   detection Stage 11 sets up.
   **Write the `aws:SourceVpce` condition as a list from the start, not as a single ID** (INT-05) —
   and in this account the caller is *never* local (D22): every legitimate reader sits in Sandbox,
   Development or Production, or behind the WireGuard Elastic IP. The list is therefore a per-consumer
   variable from day one: `aws:SourceVpce ∈ [sandbox, development, production endpoints]` **or**
   `aws:SourceIp = <WireGuard EIP>`. Getting this wrong produces an `AccessDenied` with no usable
   diagnostic, in every environment at once.
   **There is a third legitimate caller and it satisfies neither branch: this account's own
   catalog-maintenance role (D27).** A Glue Crawler over the raw zone or the drop-box runs in the Glue
   service with no VPC attachment, so it presents no `aws:SourceVpce` and no WireGuard source IP — a
   condition written for "every reader is a remote consumer" denies the one reader that is local. The same
   applies to Iceberg table optimizers and column-statistics runs. Add a third branch keyed on the
   principal rather than on the network: `aws:PrincipalArn` equal to the maintenance role (or
   `aws:PrincipalAccount` equal to this account, which is looser and easier to get right). This is the
   collision D27 created after this step was first written, and it is the reason `AccessDenied` on a
   crawler is a network-policy bug rather than an IAM one — a distinction nobody makes at first, because
   the error text points at neither.
   No `athena-results` bucket is created here: Stage 5 step 8 gives every consuming account its own results
   bucket, local to it and behind its own enforced workgroup configuration (D19). A results bucket in this
   account would be a place for query output to accumulate *inside* the governed account, owned by nobody,
   and outside the per-principal prefix scheme the derived zone is built on.
   **And the endpoint IDs in that list must be the S3 *gateway* endpoints from each consumer's
   `foundation/` slice, never the interface endpoints from `egress/`.** This is the sharp edge D22
   created and it is worth spelling out, because the failure is total and the symptom is mute. Interface
   endpoints live in `egress/`, layer `[E]`: `make down` destroys them and `make up` recreates them with
   **new IDs**. A `[P]` bucket policy pinned to those IDs is stale after the first teardown — and since
   D22 the policy lives in a *different account* from the endpoints, so the `terraform apply` that
   recreates them cannot fix it either. The S3 gateway endpoint is the right anchor on both counts: S3
   traffic goes through it anyway, it is free, and it sits in `foundation/` (`[P]`), so its ID outlives
   every session. `aws:SourceVpc` — the VPC ID, also `[P]` — is the equally valid alternative and is the
   one to prefer if a service ever needs the condition without having a gateway endpoint. Record the
   chosen anchor in the module's variable description, so the next person does not "fix" it by pasting in
   an interface endpoint ID that works until Friday.
   Also here: the **ingestion drop-box** prefix (D18) — `s3:PutObject` granted by bucket policy to the
   Interactive-OU roles, dated prefix, no read, no list, no delete. **Its bucket policy has two asymmetric
   statements, not one** (D25, INT-10): the writer statement above, and a reader statement granting
   the **Production job execution role** `GetObject`, `ListBucket` on the dated prefixes and
   `DeleteObject`, because a letterbox nobody empties fills up. The Production role also needs a grant on
   the drop-box KMS key — that is the half that is forgotten until the `AccessDenied` arrives, and the
   error text will point at S3, not at KMS. The pickup job itself is built in Stage 9 step 2, on the
   producer path; nothing runs in this account (D25 tightens the `Data` OU SCP so that stays true).
   **Make that three statements, not two (D27).** The drop-box crawler has to read what the writer wrote
   in order to infer its schema, so the maintenance role needs `GetObject`/`ListBucket` on the same dated
   prefixes — and, again, a grant on the drop-box KMS key. Three principals, three statements, and the
   asymmetry is the design: the data scientist writes and cannot read back; the maintenance role reads and
   cannot delete; the Production job role reads and deletes. Nobody holds two of those three, which is what
   keeps the drop-box from becoming the general-purpose exchange bucket D18 refuses to build.
2. **Define the data classification scheme before defining LF-Tags.** LF-Tags are the mechanism; the
   classification is the decision — which levels exist (e.g. public / internal / restricted / personal),
   who owns the assignment, and what each level permits. Writing the tags first produces a taxonomy shaped
   by whatever the first table happened to contain, and Stage 11's Macie findings then have nothing to map
   onto. This is the smallest piece of real data governance in the plan and it costs nothing but thought.
3. Glue Data Catalog databases (`raw`, `curated`). **Glue Crawlers where schema arrives from outside,
   and only there (D27):** one over the raw zone, one over the ingestion drop-box — in this account,
   under the named catalog-maintenance exception to the `Data` OU SCP, startable only by the maintenance
   role.
   > **The role's name is fixed, and it is a contract rather than a preference: `awsds-data-catalog-maintenance`.**
   > The `Data` OU SCP attached in [Stage 1c step 7.6](stage-01c-preventive-policies.md) denies
   > `glue:StartCrawler`, `StartCrawlerSchedule` and the column-statistics runs to every principal
   > *except* that exact ARN in this account. Create the role under any other name and the crawlers never
   > run — a fail-closed failure that surfaces at the first crawl with an `AccessDenied` naming the OU
   > policy, not the role. **This is also where the carve-out's positive half is finally exercised**
   > ([`plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md), phase 4): 1c could only prove that a
   > principal outside the carve-out is denied, because the role did not exist yet. Start a crawler as the
   > role before anything is wired to trigger it.
   > **The carve-out names a principal, so it can only exempt principals it can spell.** Amended
   > 2026-08-13 to carry `BoolIfExists: aws:PrincipalIsAWSService=false` alongside the ARN test, matching
   > the two conditioned statements at the root: a run *initiated by Glue itself* presents no principal
   > ARN the carve-out could match, and without the guard it would land on the deny side of a test it was
   > never meant to take. Nothing measured this — the schedule that would provoke it is the one this step
   > refuses to create — and that is exactly why it is written rather than left to be discovered.
   > **And the role itself has to be protected, or the carve-out is a formality.** An SCP exemption keyed on
   > a principal ARN belongs to whoever can *become* that principal, and editing a trust policy is a way of
   > becoming it: anyone holding `iam:UpdateAssumeRolePolicy` on `awsds-data-catalog-maintenance` can add
   > themselves to it and inherit the exemption without ever appearing in the SCP. Deny that action on this
   > role — in the boundaries of every set that is not `InfrastructureAccess` (Stage 2), and in a resource
   > policy here if this account ever gains a second administrator. The same reasoning applies to
   > `iam:PassRole` for anything that could run *as* the role.

   Event-driven (EventBridge on drop-box object creation) or run before a D25 pickup, never on a
   standing schedule: a crawler run bills per DPU-hour with a 10-minute minimum, so cron-always would
   out-cost the storage it catalogs. **No crawler ever points at an Iceberg table** — Iceberg is
   catalog-native, and a crawler would at best duplicate what the catalog already knows.

   **Lake Formation blueprints are unusable in this account, and that is by construction:** a blueprint
   workflow creates and runs Glue jobs, which `DenyUserCompute` denies. If an ingestion path ever wants
   one, it runs from an environment account and writes across the boundary — the same shape D25 already
   uses for the drop-box pickup. Reading this as "the SCP is in the way" is the error to avoid: the SCP is
   the statement that nothing runs here, and a blueprint is compute.
4. Iceberg tables on S3. **Table maintenance gets an owner on day one**: scheduled `OPTIMIZE`
   (compaction) and `VACUUM` (snapshot expiry) through Athena, or Glue's automatic compaction — an
   Iceberg table nobody compacts degrades quietly and pays storage for every dead snapshot. **Amazon S3
   Tables** — managed Iceberg with automatic maintenance and Lake Formation integration — is the
   AWS-native alternative, deliberately not used here: D13's registered/unregistered prefix split leans
   on general-purpose buckets. Recorded in `plan/institutional-delta.md`.

   **The Athena branch is why `athena:StartQueryExecution` is not in `DenyUserCompute`, and that absence
   has a cost worth naming here rather than in an audit:** a principal in this account can read any table
   the catalog exposes and write the result to S3, and the perimeter document only stops that write when
   the destination is outside the organization. The `Data` OU SCP therefore makes "nothing *runs* here"
   true and leaves "nothing *reads everything* here" to detection, which is
   [Stage 11](stage-11-dlp.md)'s; it is recorded in
   [`SCPs.md`](../../terraform-live/identity/org-policies/SCPs.md) as a stated non-coverage. **If
   maintenance ends up on Glue's automatic compaction instead, this hole can be closed** by adding
   `athena:StartQueryExecution` to the statement — decide it here, when the maintenance path is chosen,
   rather than leaving the wider version by default.
5. Enable Lake Formation as the permission model for the catalog; register the S3 locations; apply the
   LF-Tags from step 2.
6. **Implement D13 — make Lake Formation enforceable — which D22 makes structural.** In the old layout
   this required carefully *excluding* the registered prefixes from roles that lived next to them; now the
   environment accounts do not even contain the lake buckets. The SageMaker execution roles and the
   `DataScientistAccess` permission set hold **no S3 permission of any kind on Data Governance buckets**
   (except the drop-box `PutObject`) — tabular access goes through Athena, Glue interactive sessions or
   EMR runtime roles, which ask Lake Formation across the account boundary. This is the step that decides
   whether the fine-grained access control objective in `CLAUDE.md` is a control or a decoration.
   Record any exception through Lake Formation **hybrid access mode** rather than by quietly widening a
   role.
   **What that objective's *grain* is has been open since 2026-08-13, and it is decided here rather than
   assumed.** `CLAUDE.md` asks to "restrict who can read which database, table, column and row" — a
   statement about a **person** — while Unified Studio **notebooks do not support trusted identity
   propagation**: in an Identity Center domain they fall back to *compatibility permission mode*, so the
   principal Lake Formation actually sees is the project/compute role, not the human. Grant accordingly and
   say which it is: either per-user filtering exists on the SQL path and not on the notebook path — a
   two-grain design that has to be stated, not discovered — or the grain is the **project**, and the
   objective is met at that grain with the difference written down (`plan/open-questions.md` item 13). A
   row filter that silently applies to a role shared by four people is Lesson 5 with a `WHERE` clause.
7. **The cross-account shares (D22, INT-03 and 11).** **Prerequisite, and it is not optional:**
   Stage 1d step 11 must have enabled `ram:EnableSharingWithAwsOrganization` and raised the Lake Formation
   cross-account version to 3 or above. Without them the grant appears to succeed on this side and the
   resource never appears on the consumer side — which is the least diagnosable failure in the whole plan,
   because nothing errors.

   **This stage is also the thing most likely to undo it, which is why the check is run twice.**
   `aws_lakeformation_data_lake_settings` replaces the whole `DataLakeSettings` structure rather than
   patching it — the same trap 1d step 11.2 describes for the CLI. **The resource that declares this
   account's data lake administrators must carry `parameters = { CROSS_ACCOUNT_VERSION = "3" }`**, or the
   first `terraform apply` here resets the version 1d set by hand and INT-11 breaks in silence, days before
   anyone tries a share. So: run `aws lakeformation get-data-lake-settings --profile awsds-infra-data
   --query 'DataLakeSettings.Parameters'` **after** the apply as well as before it, and record both.

   Then grant the catalog read share to the Sandbox and
   Development accounts through Lake Formation/RAM, create the resource links on the consumer side, and
   prove each one with the pandas test *before* Stage 6 builds anything on top. (The Production share,
   including the governed write, waits for Stage 9 — no consumer exists for it yet.)

   **The catalog gains a second storey in Stage 6 (D26):** SageMaker Catalog — the DataZone layer of the
   unified domain — sits on top of this Glue/LF substrate. Publishing an asset and approving a
   subscription happen in the portal, and for managed assets the *fulfilment* of an approval is a Lake
   Formation grant that DataZone writes. Nothing in this stage is replaced by that: the LF-Tags, the
   registrations and the cross-account shares built here are what the portal's approvals resolve to —
   which is why this stage still comes first. **Whose approvals:** the **governance manager**'s. That
   persona also owns the classification scheme from step 2 and the LF-Tag assignments — deliberately the
   same person, because a taxonomy owned by someone who does not answer for the grants is decoration.

*`sandbox/data/` and `development/data/` — the consumer side, layer `[P]`, same module for both:*

8. Per account: the **Athena workgroup** — result bucket local to the account, per-query scan limit, and
   **`EnforceWorkGroupConfiguration = true`** (the setting the console calls "override client-side
   settings"; without it the result location is whatever the client asks for, which makes step 9 a
   suggestion rather than a boundary, D19); LF **resource links** to the shared databases; and the
   scratch buckets.
9. **Build the derived zone deliberately (D19), in each Interactive account.** D13 makes the *entitlement*
   real; it does nothing about what happens after the read, and what happens after the read is that people
   store results — which is the job, not an abuse of it. So the local prefixes get designed rather than
   left over: `…/derived/${aws:userid}/` per principal, so one person's materialised result is not a way
   around another person's grants; a lifecycle expiry (30 days is a reasonable start) so the shadow lake
   does not silently become permanent; `s3:PutObject` scoped to exactly these prefixes on both the
   execution role and the permission sets, never `*`; and the prefixes recorded here as **in scope for
   Macie and for CloudTrail data events** in Stage 11, because this is where sensitive data will actually
   accumulate — *outside* the account Macie primarily watches, which is exactly why the scope has to be
   written down. State the classification rule alongside them: the output of a query over `restricted`
   data is `restricted`. Nothing enforces that automatically at this scale — it is policy, and `plan/institutional-delta.md` records
   that a catalog with lineage is what enforces it in an institution.
   **And the sixth practice, added by D31, which is the only default-deny one on the list: the derived zone
   gets its own KMS CMK.** Separate from the account's general-purpose key — that separation is the whole
   mechanism, because a key shared with scratch buckets, state and logs cannot express "who may read
   derived data" without breaking everything else that uses it. The key policy grants `kms:Decrypt` to the
   project execution roles and to `DataScientistAccess`, and to nobody else; the `DeploymentManagerAccess`
   set of D31 is deliberately absent from it, as is any future broad read persona. The five practices above
   answer *where the copy lands*, *how long it lives* and *who is told about it*; this one answers **who may
   read it**, and it answers it in the one place that keeps answering after everyone has forgotten the
   question — a new derived prefix under the same key is covered with no list to update.
   **Cost:** one CMK per Interactive account, ~USD 1 each (`plan/cost-model.md`). **The zero-cost variant if that ever
   matters:** S3 sets the KMS encryption context to the object ARN, so the account's existing key can carry
   a `kms:EncryptionContext:aws:s3:arn` condition scoped to the derived prefix instead of a second key —
   subtler, more fragile, and recorded here as the fallback rather than the default.

*`sandbox/nfs/` — layer `[P]`: mount targets are free, and EFS storage with a
lifecycle policy to Infrequent Access is ~USD 0.016/GB-month — cents at lab scale. **Sandbox only, and
that is now a decision rather than an accident (D24):** the file-exchange requirement in `CLAUDE.md` is
about people, the VPN terminates in Sandbox, and Development deliberately gets neither its own EFS nor a
path to this one — the exchange between the two Interactive accounts is S3 and git, the same path
graduation itself takes. Build `development/nfs/` from this module only when a Development workload
genuinely needs POSIX semantics:*

10. EFS filesystem + mount targets in the private subnets, access points per group; this is the NFS layer
   shared between users and SageMaker. Enable the lifecycle policy (transition to IA after 30 days).
   S3 ↔ EFS movement is an explicit copy in code when a dataset needs to cross — no standing
   synchronisation machinery (DataSync would cost per GB moved, and there is no teardown left to protect
   against).
11. **Access from the user's own machine**, which `CLAUDE.md` asks for ("exchange files between users, the
   SageMaker environment and S3"): NFSv4 over the WireGuard tunnel, TCP/2049 allowed from the VPN peer
   CIDR, using the EFS mount helper with TLS. Two caveats to state rather than discover: throughput over a
   VPN is poor enough that this is for exchanging files, not for working off; and **EFS has no mapping
   between POSIX UIDs and SSO identities**, so "who wrote this file" is not auditable. EFS Access Points
   pin a UID/GID per group, which bounds the problem to the group level — good enough for a lab, and named
   in `plan/institutional-delta.md` as a real gap for an institution.
12. **S3 is the source of truth for data; the filesystem itself now persists.** An earlier version had the
    EFS `[E]` with a sync-to-S3 step inside `make down` — and correctly called that sync the single most
    likely way to lose real work in this design. Persistence removes the failure mode outright, for cents;
    `make down` does not touch the filesystem at all.

*Not part of the data foundation, but this is the stage it belongs to:*

13. **Enable Security Hub org-wide, from the Audit account** (delegated in Stage 1b step 8, moved out of
    the landing zone by principle 9 as amended). This stage is the trigger because Security Hub's value is
    its *standards* — automated checks of your resources against the AWS Foundational Security Best
    Practices and CIS benchmarks — and before this stage there were barely any resources to check.
    Turning it on here means its first report is about a lake, a catalog and a set of buckets that will
    still exist next month, rather than about scaffolding.
    Enable the AWS Foundational Security Best Practices standard, ingest the GuardDuty findings already
    flowing from Stage 4 step 10, and **triage the first report deliberately**: a benchmark run against a
    freshly built environment produces its largest finding count ever, and the useful act is deciding which
    controls to disable as not-applicable rather than carrying a permanently red dashboard. A dashboard
    nobody believes is worth less than no dashboard.
    **Cost:** per check and per finding ingested above the free tier (`plan/cost-model.md`). Note the
    compounding this stage now inherits and the landing zone no longer pays: Security Hub's checks run as
    **AWS Config rules**, so they add rule evaluations on top of the configuration items Control Tower
    already records.

**Deliverables:** a sample Iceberg table written in Data Governance and queried through Athena **from both
Sandbox and Development**, with access granted through the Lake Formation share rather than raw IAM
policies; **a demonstration that the same table cannot be read by pointing pandas at its S3 path from
either account** — which is the only convincing evidence that D13 holds, now with the account boundary
underneath it; **a demonstration that Athena still works with the bucket policy attached** — the evidence
that the `aws:ViaAWSService` carve-out is wired correctly; **a query whose result the client tries to
write outside the derived prefix, and fails to** — the evidence that D19's enforced workgroup
configuration holds; and a `make down`/`make up` cycle that provably leaves EFS content untouched.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
