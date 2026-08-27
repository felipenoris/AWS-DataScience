# Stage 11 — Data protection and DLP

| | |
|---|---|
| **Status** | not started — **revised 2026-08-17 into the action-checklist format** (executor markers, action-first steps), against the official documentation and the Price List API, and pre-instrumented by `./aws/dlp.py`. Corrections folded in: **internal-access analysis was measured at USD 9.00 per resource-month, charged at setup and then on the first of each month** — so step 2.1's analyzer became an enumerated-ARN, read-then-delete instrument rather than a standing monitor, and its KMS claim was narrowed (**KMS keys are not an internal-access resource type**: the derived CMK is verified by reading its key policy, not by the analyzer); **Macie's auto-enable covers *new* accounts only** — existing accounts are added one by one by the administrator, the inverse of GuardDuty's `ALL` that Stage 4 recorded; the Macie job's **discovery-results repository prompt** is answered as a decision, not at the keyboard (Lesson 16); GuardDuty's two deferred features are named by their **API feature names** (`S3_DATA_EVENTS`, `EBS_MALWARE_PROTECTION`), both prices are measured (USD 0.80/1M events, 0.03/GB), and step 4 is written against the collision `POLICIES.md` documents — with `./aws/vpn.py`'s `VP-8` expectation flipped in the same sitting (that check moved to `./aws/guardduty.py` `GD-3` at the 2026-08-18 split — 4.4 now flips `GD-3`); **the step 5 trails are data-event-only** (the org trail already carries the management copy) with advanced selectors on a monitored-bucket *map*, and the alarms ride **EventBridge rules + the `MatchedEvents` metric** — data events are matched by ordinary `ENABLED` rules once a trail logs them (read 2026-08-17) — never CloudWatch Logs ingestion; **the first member-account trail fires the revision trigger `POLICIES.md` names**, so the CloudTrail-tampering statement is decided here; the presigned-URL correction stands (*use* is detectable as `AuthenticationMethod=QueryString`; *creation* is not detectable); the Athena-inversion alarm became **conditional on Stage 5 decision 4's outcome**; archive **rules** stay forbidden (INV-10) — an accepted external finding is archived individually; and the stale addresses were repointed (open question 6's narrowed answer, Stage 6 step 3.2's recorded residual, Stage 6 step 6's D5 verdict). **Revised again later the same day: the NFS requirement was withdrawn and D24 with it — the EFS residual leaves 2.1.2, 6.1 and the threat-model deliverable** |
| **Prerequisites** | Stages 5, 6, 9 — by named input: Stage 5's classification scheme (its step 2), the LF-Tags, the derived zones (its 9.2) and **decision 4's Athena outcome**; ~~and, since 2026-08-19, Stage 9's producer path having written real rows into `curated`~~ — **lifted 2026-08-20: `sample_trades` holds 12 synthetic rows** (Stage 5's in-account load, user decision; step 2.3's callout carries the shape-and-volume caveat that survives); Stage 6's **D5 verdict** (its step 6), the grain (Stage 5 decision 6 / TIP), and the **remote-access residual its step 3.2 records**; Stage 9's producer path, outputs and results zones. **Stage 15 (GuardDuty base on org-wide — Stage 4 step 10 until the 2026-08-18 split) plus about a month of billing behind it; read its log for the exercised decision-1 path**, which is this stage's step 4 unblock (its step 5 settled that no administration role exists to carve out). Decision D6 is the strategy this stage executes |
| **Consumes** | [D5](../decisions/D05-sagemaker-egress.md), [D6](../decisions/D06-dlp-approach.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D19](../decisions/D19-derived-zone.md), [D22](../decisions/D22-data-governance-account.md), [D27](../decisions/D27-catalog-maintenance.md), [D31](../decisions/D31-approver-read.md) |
| **Proves** | — |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

**Forward constraint from D35:** the Sandbox side multiplies. The monitored-bucket list, the trail in
`sandbox/data/`, its rules and alarms and the Macie member set are all **per business unit** — write every
list as a map keyed by consumer (Stage 5's rule), so unit 2 is a row, not a rewrite.

---

**Objective:** the data-specific detection layer, built on top of a working environment rather than before
it — and the honest ledger of what has no control at all.

**Widened 2026-08-25 (the objectives clarification; D5/D6 revised the same day): this stage also owns the
client plane's egress control.** The requirement now states that a VPN-connected client's *whole* internet
runs through the cloud's single egress behind an institutional **HTTP/HTTPS proxy** — the monitoring half
of DLP's egress-control leg, beside the compute half D5 already covers (two filters: the proxy's, then
SageMaker's stricter list). No step below builds it yet: the topology — where the proxy lives, how
accounts reach it, what happens to the per-account NATs — is **open question 23**, whose answer should
arrive as a decision file before this stage is planned in detail. What the clarification settles today is
scope (the proxy is this stage's deliverable class, not Stage 3's) and the closed circuit it belongs to:
VPN-only access + endpoint DLP on institution laptops + the proxied egress
(`docs/plan/institutional-delta.md`, the device-trust row).

**What is no longer in this stage:** the data perimeter (`docs/plan/architecture.md` §4.2) moved to Stage 1;
the detective services moved to the stage that first gave each one something to observe (principle 9):
Access Analyzer's free external half to 1b step 8.2, **GuardDuty to Stage 15** (Stage 4 step 10 until the
2026-08-18 split), **Security Hub to Stage 5 step 13**. What remains is genuinely data-specific — plus step 2.1, where the analyzer switched on
in 1b is finally *collected on*: a service that emits findings nobody reads is Lesson 5 wearing a dashboard.

## What this stage builds, and in which accounts

| Where | What | Layer |
|---|---|---|
| `data-governance/data/` (amended) | LF data cells filters + the filtered grants; the data-events trail; the `awsds-data-logs` delivery statements; EventBridge rules, SNS topic, alarms | `[P]` |
| `sandbox/data/`, `development/data/`, `production/data/` (amended, one module — every `consumer-data` caller that exists by then) | each consumer account's data-events trail on its derived bucket; the mass-read rule + alarm + SNS | `[P]` |
| Management + Audit, by hand | Macie delegation, members and the discovery job; the internal-access analyzer; GuardDuty's two paid features org-wide | — (no slice, no profile) |
| `identity/org-policies/` (amended — decision 6) | the CloudTrail-tampering statement, through battery phases 1-3 | `[P]` |
| `aws/`, `docs/` | `./aws/dlp.py` (pre-written); the `GD-3` flip in `./aws/guardduty.py` (`VP-8` until the 2026-08-18 split); the `audit-iam-analyser.sh` second-analyzer expectation; the threat model `docs/plan/threat-model.md` | — |

**How steps 4 and 5 divide one problem, so they are not read as duplicates:** GuardDuty S3 Protection is
*managed anomaly* detection — it reads the S3 data-event stream itself, needs no trail, and decides what
"unusual" means; step 5 is *deterministic* detection plus the **forensic record** — named thresholds, named
principals, and log files that survive to be read. Enabling one does not discharge the other.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user/account/permission set stated first |
| **[user]** | console/CloudShell acts in Management and Audit (no profile there, by design), the behavioural proofs run from persona sessions and the laptop, and every log entry |

Hand applies run as the **infrastructure user**: `awsds-infra-data`, `awsds-infra-sandbox-1`,
`awsds-infra-dev` (the trail slices), `awsds-infra-identity` (the org-policies amendment). Every Macie,
analyzer and GuardDuty act is `AWS Control Tower Admin`, console or CloudShell, in **`us-west-2`** — the
Region ceiling does not exempt any of the three (open question 16's closure).

## Step numbers are identifiers, not an order

Four numbers are **stable addresses cited from other files** — `step 1` (the Macie scope) from
`docs/plan/cost-model.md`, D19 and D22; `step 2.1` from `docs/plan/cost-model.md`'s Access Analyzer row;
`step 4` from `docs/plan/cost-model.md`, `POLICIES.md` (the documented collision) and Stage 15 step 3;
`step 5` from Stage 5 steps 1.3, 4.3 and 9.2. They do not change. The sequence to work in is **five
passes**:

| Pass | # | What | Slice · layer | Applied as / by |
|---|---|---|---|---|
| **0** | 2.1 (first half), 3 | the readings: external findings triaged, the Stage 5/6 outcomes collected, the threat-model skeleton | snapshots + paper | Claude reads; **user** runs the Audit snapshot |
| **1** | 2 | the filters: LF column/row/cell restrictions and the filtered grants | `data-governance/data/` `[P]` | `awsds-infra-data` |
| **2** | 5 | the record and the alarms: trails, rules, SNS, thresholds — and decision 6's SCP amendment | the three `data/` slices `[P]`; `identity/org-policies/` | the three infra profiles; `awsds-infra-identity` |
| **3** | 1, 2.1 (second half) | Macie delegated, members added, the job run and mapped; the internal analyzer created, read and retired | by hand in Management + Audit | **user**, `AWS Control Tower Admin` |
| **4** | 4, 6, 3 (close) | GuardDuty's two features against the real bill; the third-party question; the threat model finished | by hand in Audit; `docs/` | **user**; Claude writes |

Pass 2 before pass 3, deliberately: the trail is the forensic record, and Macie's first job plus the
simulated-exfiltration proofs should happen **on the record**. Pass 4 sits last because step 4 is decided
against a real GuardDuty bill — which exists only after **Stage 15** has run and billed for about a month
(its step 3 is what holds the plans off until here; the 2026-08-18 split moved all of this out of Stage 4
step 10) — and step 3's ledger wants every other answer in hand.

---

## To execute

### 1. Amazon Macie — discovery, scoped to where governed data actually sits

**Action:** delegate Macie to Audit, enable it in exactly the accounts that hold governed or derived data,
and run one scoped sensitive-data discovery job whose findings are mapped onto Stage 5's classification
scheme. **Why:** discovery/classification is the first of D6's four problems — knowing *which* sensitive
data exists and where — and D19 says the interesting place is not only the lake: governed data re-surfaces
in the derived zones, which a Data-Governance-only scope would miss. **Explanation:** Macie bills S3 bucket
inventory per bucket-day (USD 0.0033, measured) in every member account, and discovery per GB inspected
(USD 1.00/GB, measured — the line that can dwarf the whole cost model), so membership and job scope are
both enumerated, never "the organization". The first 30 days per account are a free trial (Lesson 6: a
discount, not a measurement window).

- **1.1 — [user] Delegate from Management** — `AWS Control Tower Admin` → CloudShell, **`us-west-2`**:
  `aws macie2 enable-organization-admin-account --admin-account-id <Audit>`. **Delegating IS enabling** —
  the designation turns Macie on in Audit itself (documented), the same coupling as GuardDuty and Security
  Hub.
- **1.2 — [user] Add the members, one by one — auto-enable does not reach them.** In Audit (console →
  Macie → Accounts): **Add member** for **Data Governance, Sandbox Account 1 and Development** — the
  documented behaviour is that auto-enable covers **new** accounts only, and existing ones are added
  explicitly (the inverse of GuardDuty's `ALL`; verification (i)). Use the console flow, which lists the
  organization's accounts — the CLI (`create-member`) requires each account's **e-mail address**, which
  must never be copied out of `secrets/`. Set auto-enable for new accounts **on** (a Stage 14 vend arrives
  covered), **automated sensitive data discovery off** (decision 1). Management, Log Archive, Audit's
  siblings and Staging stay out — nothing governed sits in them. **Production is in the moment
  `awsds-prod-derived` exists** (Stage 9's `consumer-data` call; the pre-declared scope of
  `GOVERNANCE.md` §Derived zone), and `awsds-prod-outputs` joins when decision 3 adds it.
- **1.3 — [user] Run one one-time discovery job from Audit**, every wizard field decided in advance
  (Lesson 16): scope = the lake buckets (`awsds-data-raw`, `awsds-data-curated`, the drop-box) ~~plus the
  derived buckets~~ (**REMOVED 2026-08-26 — D19 revised: no `awsds-<env>-derived` exists; the derived
  zone is the projects bucket, next clause**) **plus `awsds-sandbox-lake`**
  (on decision 3's map since 2026-08-26 — Stage 16's permanent per-group store, the highest-value
  discovery target precisely because nothing in it expires) **plus each
  `awsds-<env>-smus-projects`** (added 2026-08-26 by Stage 6 step 2.4's reading; **since the same
  evening's D19 revision it IS the derived zone**, so this is D19 practice (iv)'s carrier, not an
  extra — see the callout after this step); **sampling
  depth** per decision 1 (the cost lever: GB inspected × USD 1.00); **managed data identifiers** = the
  recommended default set, no custom identifiers; job type **one-time** — re-run deliberately, never
  scheduled. **The wizard's discovery-results repository prompt is decision 2** — answer it from the log,
  not at the keyboard.

> **THE PROJECTS BUCKET JOINED THIS SCOPE ON 2026-08-26, FROM A STAGE 6 READING — AND BY THE SAME
> EVENING IT WAS THE DERIVED ZONE ITSELF** (D19 revised: `awsds-<env>-derived` removed, the SMUS project
> path kept as the one designed destination). The Tooling blueprint gives each project an **enforced**
> Athena workgroup whose output location is `<domain-id>/<project-id>/dev/sys/athena/` **inside this
> bucket**, so query results computed over governed lake data land here. Two properties make it harder
> for discovery than the removed zone was, and both are measured rather than feared:
>
> - **Nothing expires.** Versioning, a 90-day noncurrent expiry, MPU abort — and no rule on current
>   objects. The removed zone shed at 30 days; this one accumulates (open question 25).
> - **Deleting a project does not delete its prefix.** Five project prefixes stood against **one** live
>   project, one orphan carrying a whole `.git` tree and a notebook. So the scan target includes the work
>   of projects that no longer exist and that no console lists — the exact shape this stage cannot
>   discover for itself, which is why it is written down here.
>
> Both are **open question 25** (the expiry, and who reaps an orphan). If it is settled before this stage
> runs, re-read the scope: an expiry short enough would change what a discovery job over this bucket is
> even scanning.
>
> Consequence for **1.3**: the job scope names the bucket, not a prefix — an orphan prefix is invisible to
> any scope written from the live project list. Consequence for **step 5**: it belongs on the
> monitored-bucket map with the derived buckets, and it is the one whose data events will not thin out
> over time.
- **1.4 — [user] Route the findings**: in Macie's settings, turn on publication of **sensitive-data
  findings to Security Hub** (policy findings publish automatically once both services are on), and extend
  Audit's Stage 15 step 4 EventBridge→SNS rule to Macie findings — console-built, like the rule it
  extends.
- **1.5 — [Claude] Map the findings onto the classification scheme** (Stage 5 step 2): every finding
  lands on a level, or the scheme gains one — a finding that fits nowhere is a scheme defect, not a Macie
  defect. The mapping is a threat-model input (step 3).
- **1.6 — [Claude] Close the paperwork in the same sitting**: restate `INV-09` in `docs/AWS_STATE.md`
  (nine trusted-access principals — `macie` delegated to Audit; §C predicts it), re-run
  `./aws/org-trusted-access-services.py`, and run `./aws/dlp.py` (`DP-1`). **[user]** Record 1.1-1.4 in
  the stage log.

### 2. Lake Formation column, row and cell filters — entitlement tightened to the classification

**Action:** narrow the entitlement to the classification's grain — column restrictions through the LF-Tag
grants, row/cell restrictions through data cells filters — **within the classification-scoped grants
Stage 5 already enforces** (its 6.1, 2026-08-17: `restricted`/`personal` travel only on explicit grants),
replacing those explicit grants where the scheme demands finer than a whole column set. **Why:** fine-grained access is D6's second problem, and D13 is what makes any of it real: every
tabular read already goes through an LF-aware engine, so a filter granted here is enforced, not decorative.
**Explanation:** a data cells filter is a named, per-table object (column include/exclude list + a PartiQL
row expression), granted with `SELECT`; filters apply to reads only. Cross-account it follows Stage 9's
two-step: grant the filtered `SELECT` to the consumer **account** (with grant option), local regrant to the
reading principal. **The grain is Stage 5 decision 6's, not this stage's**: if the grain is the project,
the filter lands on project roles and says so; a row filter that silently applies to a role shared by four
people is Lesson 5 with a `WHERE` clause.

- **2.1a — [Claude] Write the filters in `data-governance/data/`** — `aws_lakeformation_data_cells_filter`
  on the tables whose classification requires one (start with the sample `curated` table: one
  column-restriction filter, one row filter), named `awsds-flt-<table>-<what>` — a contract with
  `./aws/dlp.py` (`DP-3`).
> **What pass 4 measured, and it constrains everything in this step (2026-08-19).** The `restricted`
> column does not cross the account line **at all** under the default share: read as its own
> `InfrastructureAccess`, `curated.sample_trades` shows six columns in Data Governance and **five** in
> both consumer accounts — `counterparty` is filtered by the share's `classification ∈ {public,
> internal}` gate, before any persona is involved, because an account may pass on only what it received.
> So a data cells filter written here reaches a consumer only if the `restricted` grant is made in **two
> hops**: an explicit cross-account grant from Data Governance *with grant option*, then a local re-grant
> in the consumer account — and the local half is itself the pair of 2.1b below plus `DESCRIBE` on the
> resource link. A filter granted only on the producer side is invisible in the account that would use it.

- **2.1b — [Claude] Write the filtered grants**, replacing the corresponding explicit `restricted` grants
  in the Stage 5 share map: `aws_lakeformation_permissions` with the `data_cells_filter` block, to the consumer
  accounts with grant option; the consumer-side regrant lands in the same slice pattern Stage 9 2.3 used.
  Column-only restrictions that the LF-Tag ontology already expresses stay on tag-scoped grants — one
  mechanism per dimension, stated in the module comments.
- **2.2 — [Claude⚡] Apply as `awsds-infra-data`, inside `DL-5`'s bracket** (read
  `DataLakeSettings.Parameters` before and after — every `data-governance/data/` apply can silently reset
  INT-11's values).
- **2.3 — [user] Prove the filter pair from a consumer session**: the filtered principal's Athena query
  returns the restricted columns/rows and nothing else; the same table read with pandas against S3 still
  fails (Stage 5's negative, re-run — the filter tightened the entitlement, not the perimeter). Record
  both.

  > **THE ROW HALF NEEDS ROWS, AND THAT IS A DEPENDENCY, NOT A DETAIL (2026-08-19).** Stage 5 applied
  > `curated.sample_trades` **empty** — created through the Glue API's Iceberg path, deliberately with no
  > Athena DDL in that account (its 4.1). A row filter over an empty table returns nothing whether it is
  > working or absent, which is Lesson 13 exactly. **So this proof depends on Stage 9's producer path
  > having written real rows** — the governed cross-account write, which is the only way data enters
  > `curated` by design (D22). The *column* half is unaffected: a column list discriminates all three
  > states on an empty table. If Stage 9's write has not run when this stage does, the row filter is
  > authored and its proof is deferred **in writing**, never quietly recorded as passed.
  >
  > **LIFTED 2026-08-20: the table holds 12 synthetic rows** (Stage 5's log, that date — the user's
  > decision, taken before 4e closed the in-account Athena path; the attempt also surfaced and fixed
  > the registration role's missing write ceiling, Lesson 34). Four distinct `counterparty` values over
  > five instruments and six trade dates, so the row filter has real variety to discriminate on. The
  > caveat that remains: the rows are synthetic and twelve — evidence at production *shape and volume*
  > still arrives only with Stage 9's write, and a filter proof over this table says nothing about
  > distribution-dependent behaviour.

### 2.1. Collect on IAM Access Analyzer — the external findings as input, the internal ones as an instrument

*Numbered 2.1, not 3: `docs/plan/cost-model.md` cites "Stage 11 step 2.1" and "step 4" by name.*

**Action:** triage every external-access finding, then answer "who *inside* the organization can reach the
governed buckets" with a deliberately short-lived internal-access analyzer. **Why:** the org external
analyzer has watched Stages 2-9 create every bucket, role, key, snapshot and file system — an unread
findings list is indistinguishable from an empty one; and an org-scoped external analyzer is **silent by
construction about access inside the organization**, which is exactly the movement this stage exists to
control (D6). The internal findings are the machine check of **D13** — that no execution role holds an S3
path under the catalog — because until now nothing tested a claim about policies this project itself wrote
(Lesson 18). **Explanation:** external stays free and org-wide; internal is **USD 9.00 per monitored
resource per analyzer-month (measured, `docs/PRICING.md`), charged at setup and then on the first of each
month, not prorated** — six resources would exceed the entire D12 ceiling — so the analyzer is an
enumerated-ARN instrument: created, read, recorded, deleted inside one month.

- **2.1.1 — [user] Regenerate the Audit snapshot** — `aws/cloudshell/audit-iam-analyser.sh` in Audit
  CloudShell. **[Claude]** Triage every `ACTIVE` finding: the INV-16 shape (`AWSReservedSSO_*` roles
  trusting the directory's SAML provider) is the expected whole set; anything else is a row in the threat
  model — answered, or explicitly accepted. **An accepted finding is archived individually and recorded;
  an archive *rule* stays forbidden** (INV-10 — a rule suppresses future findings silently).
- **2.1.2 — [Claude] Read the five no-RCP resource types as perimeter, not as commentary** — Lambda, SNS,
  EBS volume snapshots, RDS DB and DB-cluster snapshots, EFS (`docs/plan/architecture.md` §4.2): for the
  data-bearing ones (the snapshots — closed preventively by 1c 7.5's unconditional denies), the external
  finding is not a check on the perimeter, it **is** the perimeter. The threat model says so per row
  rather than inheriting D19's "the perimeter contains it". (EFS used to be the third data-bearing
  member, closed by nothing; the NFS requirement's withdrawal — 2026-08-17, D24 with it — removed the
  filesystem, and the type is back to commentary.)
- **2.1.3 — [user] Create the internal-access analyzer in Audit** — console, **`us-west-2`**, zone of
  trust **Entire organization** (Audit is already the Access Analyzer delegated administrator; **only one
  org-level internal analyzer can exist per organization**). Resources by **exact bucket ARN** (account id
  + ARN pairs; prefixes are not supported): the map of decision 3 — recommended minimum: the two
  registered lake buckets and **every derived zone that exists at run time — since 2026-08-26 that is
  `awsds-<env>-smus-projects`, not `awsds-<env>-derived`** ([D19 revised](../decisions/D19-derived-zone.md):
  the Interactive derived buckets were destroyed, and neither deployment target has a named results home
  until Stage 9 re-decides), plus `awsds-sandbox-lake` if item 3's map keeps it. At USD 9 per
  resource-month the recommended minimum is **five resources, USD 45 for the month** — the same total the
  old sentence quoted, arrived at from a different list. No new principals arrive:
  `AWSServiceRoleForAccessAnalyzer` exists org-wide since 1b (Lesson 17, checked not assumed).
- **2.1.4 — [Claude] Amend the instruments in the same sitting**: `audit-iam-analyser.sh` expects the
  second analyzer (type `ORGANIZATION_INTERNAL_ACCESS`) while it lives; restate **INV-10** in
  `docs/AWS_STATE.md` — and restore both when 2.1.6 deletes it.
- **2.1.5 — [Claude] Read the findings against the two decisions they exist to test**: **D13** — no
  finding may show an execution role, persona set or blueprint-provisioned role reaching a registered
  bucket outside the designed branches; **D19** — the derived buckets' reader list matches the design.
  **Two boundaries, stated so a clean report is not over-read**: the analyzer sees the S3 layer *under*
  the catalog — precisely the bypass D13 closes — and says nothing about LF-Tag entitlements; and **KMS
  keys are not an internal-access resource type**, so D31's "who can decrypt the derived CMK" is verified
  by reading the key policy's enumerated `Decrypt` list (Lesson 22's shape), not by the analyzer.
- **2.1.6 — [user] Delete the analyzer once the findings are recorded** (decision 3; the reading is
  repeatable — recreate it at any later audit for another month's USD 9/resource). **[user]** Record
  create, read and delete in the stage log.
- **2.1.7 — Unused-access findings stay in Stage 12** and are not re-litigated here.

### 3. The egress and endpoint hardening review — the ledger of controls that do not exist

**Action:** re-read the egress surface against the D5 verdict and write the "accepted rather than
controlled" column of the threat model. **Why:** egress control is D6's third problem, and its honest
state is a mix: one strong design, one bypassable design, and two product surfaces with no supported
control at all. A threat model that lists a control nobody implemented is worse than one that says "none".
**Explanation:** readings and writing, no build; the output is `docs/plan/threat-model.md`.

- **3.1 — [Claude] Re-read the surviving egress design** (Stage 6 step 6 closed D5): under **A**, the DNS
  Firewall allowlist is a strong control against accident and a weak one against intent — **raw-IP bypass
  is stated as accepted**, with the blocked-query log as its detection; under **B**, there is no egress
  path to misuse and the row closes.
- **3.2 — [Claude] Record the file-download answer as narrowed by open question 6**: no supported product
  control exists; AWS's official mitigation — a lifecycle configuration disabling the JupyterLab download
  extensions (`aws-samples/sample-disable-sagemaker-jupyterlab-download`) — is a UI control a user with a
  terminal can revert. Classification: **no control; an official, bypassable mitigation; everything else
  is detection** (steps 4-5). Adopting the lifecycle configuration is optional and does not change the
  classification.
- **3.3 — [Claude] Carry the remote-IDE residual Stage 6 step 3.2 recorded** (open question 14):
  `StartSession` is tag-scoped to the user's own spaces — a *scoping* control, not a *transfer* control —
  and remote sessions authenticate with **IAM credentials even in IdC domains, persisting up to 12 h after
  portal logout**. Accepted, with the kill-switch named: the `sagemaker:RemoteAccess` condition key on
  `CreateSpace`/`UpdateSpace`.

### 4. GuardDuty's two paid features — decided against a real bill, unblocked deliberately

**Action:** enable **S3 Protection** (`S3_DATA_EVENTS`) and **Malware Protection for EC2**
(`EBS_MALWARE_PROTECTION`) org-wide, working around this project's own SCP where it blocks Audit's
detector — and answer the ECR enhanced-scanning question Stage 7 decision 2 deferred to this step by name
(4.6). **Why:** the base service has run since Stage 15; these two were switched off there by its
step 3, *by name*, so the decision could be made against a measured bill (`docs/plan/cost-model.md`) — S3 Protection is
the anomaly half of exfiltration detection (D6's fourth problem). **Explanation:** measured us-west-2
prices — **USD 0.80 per 1M S3 data events analyzed** (first tier) and **USD 0.03/GB of EBS scanned**; each
feature carries its own 30-day free trial on first enablement. **The block is known in advance and is this
project's own control working** (`POLICIES.md`): `DenyGuardDutyTampering` denies `guardduty:UpdateDetector`
on the root, so org-wide administration (`UpdateOrganizationConfiguration`, `UpdateMemberDetectors` —
neither denied) succeeds while **Audit's own detector** is the one call that fails. The mistake to avoid is
reading that `AccessDenied` as a broken policy and deleting the statement.

- **4.1 — [user] Read the real bill first**: Cost Explorer, the GuardDuty line since Stage 15 ran — the
  number the decision is made against (Lesson 6); a month of billing is the minimum for the number to
  mean anything, which is why this stage's Prerequisites gate on that stage plus time. Record it.
- **4.2 — [user] Enable org-wide from Audit** — `AWS Control Tower Admin`, GuardDuty console →
  protection plans: auto-enable **`ALL`** for both features (new and existing members, up to 24 h to
  propagate).
- **4.3 — [user] Unblock Audit's own detector by the recorded path** (decision 4): **Stage 15 already met
  this deny in the opposite direction and settled the carve-out question** (its step 5: GuardDuty creates
  only the service-linked role, so there is no administration role to name — its decision 1 chose the
  detach/re-attach procedure and recommended against the carve-out). **Reuse whatever its log records as
  the exercised path**; failing that, detach `awsds-org-scp-baseline`
  from the root, make the change, re-attach, and re-run phases 1-3
  ([`docs/plan/runbooks/scp-battery.md`](../runbooks/scp-battery.md)) — **the re-attach is not done until
  the probes have run**, and the sitting is not closed before the re-attach.
- **4.4 — [Claude] Flip the instruments in the same sitting**: `./aws/guardduty.py` `GD-3` currently
  fails on **any** optional plan reading `ENABLED` (it is driven by the API's own feature list, not a
  constant — the 2026-08-18 split's design; `VP-8` is retired) — after this step the two features of
  decision 4 must read `ENABLED` everywhere, so `GD-3` learns the pair as the sanctioned exception, and
  `./aws/dlp.py` `DP-6` takes over the standing read. Re-run both;
  **[user]** record 4.1-4.3 and the battery outcome in the stage log.
- **4.5 — Malware Protection for *S3* is a different product and a separate decision** (decision 5):
  bucket-level, **USD 0.09/GB + 0.000215 per object above the free tier (measured)**, relevant only to the
  drop-box — the one bucket that ingests files from humans. Recommended off at lab scale; priced here so
  the "no" is a choice.
- **4.6 — Decide ECR enhanced scanning in the same sitting** — Stage 7 decision 2 deferred it *to this
  step by name*: basic scan-on-push (free) carries Stage 8's gate; enhanced is **Inspector** — OS *and*
  language packages, continuous — measured at USD 0.09/image + 0.01 per re-scan, and continuous means a
  re-scan on **every new CVE**, which is the churn to price. If adopted: **[user]** standalone-enable
  Inspector for resource type ECR **in Production only** (the account that owns the registry) — no org
  delegation, no new trusted-access principal. Decision 9 records either answer.

### 5. CloudTrail data events and the exfiltration alarms — the deterministic half, on the record

**Action:** create a data-event-only trail per account that holds monitored buckets, deliver all three to
`awsds-data-logs`, and alarm on the named exfiltration patterns through EventBridge rules. **Why:** D6's
fourth problem needs a *record* (who read what, when — the forensic half no anomaly service provides) and
*deterministic* alarms for the patterns this design can name: mass reads, presigned-URL use, writes by an
unexpected principal, and the Athena path in Data Governance that `POLICIES.md` records as deliberately
uncovered. **Explanation:** the org trail is Control Tower's and is not touched; these are the project's
**first member-account trails**, management events excluded (the org trail already carries that copy — a
second one would bill USD 0.00002/event for nothing). Data events are **USD 0.10 per 100k (measured)**;
reads are logged deliberately — reads *are* the exfiltration signal — and the cost-model's Spark-job
warning is the price of that choice, cents at lab scale. Alarms ride **EventBridge rules on the default
bus** (data events are matched by ordinary `ENABLED` rules once the trail logs them; AWS-service events
are free) with the rule's `MatchedEvents` metric — no CloudWatch Logs ingestion anywhere.

- **5.1 — [Claude] Write the trail module and the slice amendments** — `awsds-<env>-data-events` in
  `data-governance/data/` and every `consumer-data` caller that exists by then (`sandbox/data/`,
  `development/data/`, `production/data/` after Stage 9): **advanced event selectors only** —
  `resources.type = AWS::S3::Object`, `resources.ARN` starts-with the account's monitored buckets (the
  decision 3 map: lake + drop-box in Data Governance; ~~the derived bucket in each consumer account~~
  — removed 2026-08-26, D19 revised;
  **`awsds-sandbox-lake` in Sandbox** since 2026-08-26 — its reads are the exfiltration signal for the
  one store where artifacts persist; **`awsds-<env>-smus-projects` in each Interactive member** since the
  same date — **the derived zone itself since D19's same-evening revision**, and the only monitored
  bucket whose contents never expire, orphaned project prefixes included) —
  **no management-event selector**, reads and writes both, log file validation on. Delivery: all three
  cross-account into **`awsds-data-logs`** under `AWSLogs/<account>/` (decision 7), with the bucket-policy
  statements for `cloudtrail.amazonaws.com` conditioned on `aws:SourceAccount` ∈ the three account ids —
  written in `data-governance/data/` beside the bucket they amend.
- **5.2 — [Claude] Write the rules, the topic and the alarms per account** (`awsds-<env>-security` SNS,
  the Stage 1b pattern; **[user]** subscribes the e-mail):
  - **`awsds-<env>-massread`** — `GetObject` on the monitored buckets; alarm on the rule's
    `MatchedEvents` **Sum** over 5 minutes ≥ decision 8's threshold. The rule needs no target to emit the
    metric.
  - **`awsds-<env>-presigned-use`** — `additionalEventData.AuthenticationMethod = QueryString`: the
    detectable half of the presigned question (signing is a local SigV4 operation and appears nowhere;
    **use** arrives with a distinct authentication method). Target: the SNS topic directly. Pairs with the
    preventive `s3:signatureAge` cap Stage 5 step 1.3 wrote.
  - **`awsds-data-unexpected-writer`** (Data Governance only) — `PutObject` on lake + drop-box where
    `userIdentity`'s role is **anything-but** the three designed writers (the Interactive-OU writer roles,
    `awsds-data-catalog-maintenance`, `awsds-prod-job-exec` — D25's asymmetry, alarmed).
  - **`awsds-data-athena`** (Data Governance only) — on `StartQueryExecution` (a management event: the
    org trail already logs it, so this rule needs no member trail). **Conditional on Stage 5 decision 4's
    outcome:** if the Athena hole was closed by SCP amendment, *any* occurrence — allowed or denied — is
    the signal (read `POLICIES.md` to confirm which); if it stayed open for Athena-based maintenance, the
    rule excludes the maintenance role and alarms on everyone else. The inversion is deliberate: in every
    *other* account Athena is the normal way to read.
- **5.3 — [Claude⚡] Apply the three slices** — `awsds-infra-data`, `awsds-infra-sandbox-1`,
  `awsds-infra-dev`; `DL-5` brackets the Data Governance apply as always. **[user]** Record in the log.
- **5.4 — [Claude] Write the tampering statement the trigger demands** (decision 6): `POLICIES.md` records
  "no CloudTrail statement" with the revision trigger *"the first trail this project creates in a member
  account"* — which is this step. Recommended `Sid` **`DenyCloudTrailKill`** in `awsds-org-scp-baseline`:
  deny `cloudtrail:StopLogging` and `cloudtrail:DeleteTrail`, unconditional (it binds the builder, which
  is what makes it a control — the amendment procedure is the same detach/re-attach as step 4). What it
  deliberately does not cover, recorded as residual in the threat model: `UpdateTrail`/`PutEventSelectors`
  can redirect or narrow a trail and stay allowed — Terraform manages the trail through them, and a policy
  never constrains its author (Lesson 18); the mutation itself is a management event on the org trail.
  **[Claude⚡]** Land it through **battery phases 1-3**, `POLICIES.md` reviewed in the same sitting.
- **5.5 — [user] Fire the alarms once, deliberately — an alarm that has never fired is Lesson 13**: from
  a data-scientist session, a `GetObject` loop over the mass-read threshold; one presigned `GET`
  (generate locally, use it); one drop-box `PutObject` from a persona session (the *writer* statement
  admits it — the rule must stay quiet; then one from an unexpected role if one is obtainable, else record
  Lesson 22). Each alarm fires, the e-mail arrives, and a normal working session stays quiet. Record all
  outcomes, including the quiet ones.

### 6. The third-party question, answered last

**Action:** evaluate whether an agent-based DLP product adds anything, now that the native stack is built
and its gaps are written down. **Why:** D6 deferred this question to exactly this moment — after the
perimeter, the four native controls and the accepted-risk ledger exist, so the evaluation is against named
residuals, not against fear. **Explanation:** a reading, recorded in the threat model.

- **6.1 — [Claude] Walk the threat model's residual column** — the remote-IDE
  channel, design A's raw-IP bypass (if A survived), `UpdateTrail`, the within-persona result visibility
  (Stage 9's stated limit), **and the portal's off-VPN user ingress (INT-16, measured 2026-08-22 — the
  strong form: JupyterLab works with the tunnel down; whether it enters this ledger as a recorded
  acceptance or was closed by fallback (i) is the user's decision, deferred at Stage 6 and read here, not
  re-taken)** — and ask which, if any, an agent would actually close, at what cost, with what
  new principals (Lesson 17). Recommended answer at lab scale: none — record it and the reasoning in
  `docs/plan/threat-model.md` and `docs/plan/institutional-delta.md` (an institution buys the catalog with
  lineage first, D19 practice v).

---

## Deliverables

Each is written so its output differs between working and broken (Lesson 13). **The mechanical half is
`./aws/dlp.py`** ([`aws/INDEX.md`](../../../aws/INDEX.md)): Macie's per-account state and delegation, the
filters and filtered grants, the trails' shape (data-event-only, the monitored map, validation on,
delivering to the logs bucket), the rules and alarms, the GuardDuty features now expected `ENABLED`, and
the tampering `Sid`. The behavioural proofs are the stage's own (Lesson 20):

- **The threat model, `docs/plan/threat-model.md`** — one control (or one named acceptance) per item, and
  a **reachability row per governed resource**: who outside the organization can reach it (the external
  analyzer's answer), who inside can (the internal analyzer's, for the types it covers; a reading, for the
  CMKs and the catalog layer).
- **The alarm pair (5.5):** the simulated exfiltration fires every alarm it should, the e-mail arrives,
  and a normal session stays quiet.
- **The filter pair (2.3):** the filtered principal sees exactly the filtered result; pandas against the
  same table's S3 path still fails.
- **The Macie mapping (1.5):** every finding mapped onto a classification level, or the scheme amended.
- **The collection (2.1):** every external finding answered or individually archived with its reason; the
  internal findings recorded against D13/D19 and the analyzer retired.

## Validation

1. Run `./aws/dlp.py` — all `DP-*` pass; diff two runs across the stage (only timestamps and job/finding
   counts may change).
2. Run `./aws/datalake.py` after every `data-governance/data/` apply — `DL-5` green (the INT-11
   parameters, as always).
3. Re-run `./aws/org-policies.py` and the battery phases after the step 4 and 5.4 amendments — never a
   direct edit; `POLICIES.md` reviewed in the same sittings.
4. Run `./aws/egress.py` §6 at session end — this stage adds nothing metered by the hour, and the reading
   proves it.
5. Read every denial by its wording, never its exit code (standing rule since 1c).

## Cost

Measured (`docs/PRICING.md` §6), us-west-2; everything here is `[P]`-shaped monthly cost, nothing hourly:

| Item | Cost | Note |
|---|---|---|
| Macie bucket inventory | USD 0.0033/bucket-day (~0.10/bucket-month) | ~10-15 buckets across the three members — ~USD 1-1.50/month; 30-day free trial per account |
| Macie discovery job | USD 1.00/GB inspected | the sampling depth (decision 1) is the lever; lab-scale lake ≈ cents per run |
| Internal-access analyzer | **USD 9.00/resource-month, charged at setup** | 4 resources = USD 36 for the one month it lives (2.1.6 retires it) |
| GuardDuty S3 Protection | USD 0.80/1M S3 data events | 30-day free trial; the real driver is job read volume |
| GuardDuty Malware Protection for EC2 | USD 0.03/GB EBS scanned | scans on findings — near zero in quiet months |
| CloudTrail data events | USD 0.10/100k events | reads logged on purpose; a heavy Spark job ≈ tens of thousands of events ≈ cents |
| Alarms (≈6) + SNS e-mail | ~USD 0.60/month | EventBridge rules and AWS-event matching are free |
| Trail S3 storage in `awsds-data-logs` | cents | inside the existing S3 floor row |

## Decisions due while executing

**Blocking questions for the user: none.** Each is decided during the stage and written into
`docs/log/log-stage-11-dlp.md` (Lesson 16). Recommendations stated so the keyboard is not the
decision-maker.

1. **Macie mechanism and sampling depth** (1.2, 1.3) — one-time scoped jobs versus automated discovery.
   Recommended: **one-time jobs on the decision 3 map, automated discovery off** — a standing sampler is a
   standing spend, revisited at Stage 12 against the bill.
2. **The Macie discovery-results repository** (1.3) — the wizard demands an S3 bucket + KMS key for
   long-term results, or results expire in 90 days. Recommended: **skip it at lab scale** — findings
   (the durable part) live in Security Hub and the threat model; record the 90-day acceptance.
3. **The monitored-resource map** (1.3, 2.1.3, 5.1) — which buckets Macie scans, the analyzer monitors
   and the trails select. Recommended: lake (`raw`, `curated`, drop-box) + **every derived zone that
   exists at run time, which since 2026-08-26 means `awsds-<env>-smus-projects`**
   ([D19 revised](../decisions/D19-derived-zone.md): `awsds-<env>-derived` was destroyed and the SMUS
   project path took its place) — the derived zone's Macie and data-event scope is pre-declared
   ([`GOVERNANCE.md`](../../GOVERNANCE.md) §Derived zone, practice (iv) of six), consumed here rather than
   re-decided. **Production's and Staging's join the map the day Stage 9 decides where their results
   land, which is no longer automatic**: neither account has SMUS, so neither inherits the new zone;
   **`awsds-sandbox-lake` is on the map since 2026-08-26** (Stage 16, added in the sitting that created
   that stage, Lesson 34 — the permanent per-group store names this scope as one of its compensations,
   and for 2.1.3's analyzer it is one more enumerated bucket ARN at the same per-resource price);
   **`awsds-prod-outputs` joins when Stage 9's producer path first carries real data** — the one
   genuinely open addition. One map, one variable, consumed by all three (Lesson 14).
4. **The step 4 unblock path** (4.3) — Stage 15 settled the carve-out question (no administration role
   exists; its decision 1 chose detach/re-attach and recommended against the carve-out), so the default
   here is the same procedure. Recommended: **whichever the Stage 15 log answers** — a carve-out written against a
   role that already exists is the one shape this plan trusts (D27).
5. **Malware Protection for S3 on the drop-box** (4.5) — recommended: **off**, priced (USD 0.09/GB +
   0.000215/object); revisit if the drop-box ever ingests files from outside the tunnel.
6. **The CloudTrail-tampering statement** (5.4) — recommended: **`DenyCloudTrailKill`**
   (`StopLogging` + `DeleteTrail`, unconditional) via battery phases 1-3, with the `UpdateTrail` residual
   recorded rather than chased.
7. **Trail delivery** (5.1) — centralized into `awsds-data-logs` versus per-account buckets. Recommended:
   **centralized** — the record lands in the governed account, one lifecycle, no new buckets.
8. **The mass-read threshold** (5.2) — recommended: measure one normal working session's `MatchedEvents`
   first, set the alarm at ~10× that, and revisit at Stage 12; a threshold set blind is either noise or
   silence.
9. **ECR enhanced scanning** (4.6, Stage 7 decision 2's deferral) — recommended: **stay on basic** until a
   Stage 8 gate reading misses a language-package CVE that mattered; if adopted, standalone Inspector in
   Production only, and re-read the re-scan churn against the bill at Stage 12.

## Verifications to answer while executing

Record every answer, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | Does Macie's auto-enable really leave existing accounts unenabled (the documented inverse of GuardDuty's `ALL`), and does the delegation alone enable Audit? | 1.1, 1.2 |
| ii | Does every Macie finding map onto a Stage 5 step 2 classification level — or which level did the scheme gain? | 1.5 |
| iii | Does the filtered grant hold on the SQL path at the Stage 5 decision 6 grain — filtered rows/columns returned, pandas still denied? **The column half answers on an empty table; the row half needs Stage 9's producer path to have written rows** (2.3's callout) | 2.3 |
| iv | Do the internal-access findings confirm D13 (no execution-role path under the catalog) and D19's reader list — and does the reading of the derived CMK's key policy match D31's enumerated list? | 2.1.5 |
| v | Is the step 4 block observed as written — org-wide enablement succeeding, Audit's own `UpdateDetector` denied naming `DenyGuardDutyTampering`? | 4.2, 4.3 |
| vi | After 4.3: do both features read `ENABLED` in every account, and do `GD-3` (flipped — `./aws/guardduty.py`; `VP-8` before the 2026-08-18 split) and `DP-6` agree? | 4.4 |
| vii | Does the mass-read alarm fire on the simulated loop and stay quiet through a normal session — and what did the normal session's `MatchedEvents` baseline measure? | 5.5, decision 8 |
| viii | Does presigned **use** arrive as `AuthenticationMethod=QueryString` and drive its rule — while creation, as predicted, appears nowhere? | 5.5 |
| ix | Do the trails read back data-event-only (`get-event-selectors`: no management events) with validation on, delivering cross-account into `awsds-data-logs`? | 5.3 |
| x | Does the Athena rule match Stage 5 decision 4's outcome — closed hole alarming on any occurrence, open hole alarming on non-maintenance principals only? | 5.2 |

## Risks

- **Two line items can silently dominate the floor**: Macie's per-GB discovery (the sampling depth is the
  only lever — and `sa-east-1` prices it at 2.25×) and the **USD 9.00/resource-month** internal analyzer —
  which is why 2.1.6's delete is a step, not housekeeping.
- **Step 4 and 5.4 both open the root SCP set** — the detach window and the amendment are covered by
  battery phases 1-3, and the sitting is not closed until the re-attach probes have run (the same rule
  `POLICIES.md` states for `Data`'s bucket deny).
- **An EventBridge rule without its trail is an alarm that can never fire** (Lesson 13's shape): the rules
  match only events a trail logs, which is why 5.5 fires every alarm once before the stage closes.
- **Alarm thresholds are a judgement about normal** — set blind they produce noise (ignored within a
  week) or silence (Lesson 5); decision 8 measures first.
- **The deterministic alarms only see the patterns this design named** — the unnamed ones belong to
  GuardDuty's anomaly half (step 4), and the threat model's residual column is the honest boundary between
  the two.
- **`./aws/dlp.py` cannot see Audit** (no profile, by design): Macie's job history, the analyzer and the
  org configuration are verified in the Audit console/CloudShell — section 8 of the report names what it
  is not measuring, so a green run is not over-read.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
