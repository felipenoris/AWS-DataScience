# Open questions

Only things to find out by doing. **All thirty-seven decisions are closed** — a question that
turns into a choice becomes a decision file, not a longer entry here.

---

## 9. Open questions

Everything that was open before execution started is now closed in `plan/decisions/` (D1-D37). What follows is
what is genuinely still unanswered:

1. **Which domain name to register (D15 phase 2).** Still the one input needed from the user, but the
   2026-08-09 revision moved *when*: it now blocks **Stage 13** alone, not Stage 7. Nothing before the
   public web tier registers or publishes anything — internal endpoints are `*.internal` names certified by
   the internal CA. Registration and validation still take time, so it is worth deciding before Stage 13
   starts; it is no longer worth doing early.
2. **D7/D28 - two verifications, not decisions.** The orchestration decision is closed (both built,
   Stage 10; alternative A is MWAA Serverless via `awscc_mwaaserverless_workflow`, verified to exist
   2026-08-08). What is open: (i) whether the awscc resource *applies* cleanly under the CI deploy role
   (INT-14 — fallback chain recorded there); (ii) whether logs-only observability — Serverless has
   no Airflow UI — is livable for a data scientist debugging a failed run, which only the Stage 10
   comparison can answer. Keep application entry points as plain containers so both implementations, and
   the two options that were not built, remain viable.
3. ~~**AZ name-to-ID mapping across accounts**~~ — **measured 2026-08-12 in Stage 1b step 6, and the answer
   did not decide the question the way the question expected.** Every account that has a profile returns
   an identical mapping (`us-west-2a` → `usw2-az2`, `b` → `az1`, `c` → `az3`, `d` → `az4`; the names are
   *not* in ID order). The full table is in
   [`log/log-stage-01b-identity-and-controls.md`](../log/log-stage-01b-identity-and-controls.md), and
   `./aws/AZs.sh` regenerates it into `aws/output/AZs.txt`.
   **Stage 3 anchors subnets on `zone_id` anyway** — this item used to say "if the mappings differ", and
   that conditional was written without knowing that the measurement can only ever speak for the accounts
   that exist. `Staging` is unvended and D35 plus [Stage 14](stages/stage-14-sandbox-vending.md) multiply
   Sandboxes; each new account gets its own mapping at vend time and nothing makes it match. Index-based
   placement would work today and break silently on the first account that disagrees, at USD 0.01/GB each
   way across the two peerings D14 and D21 keep busy — **no error, only a line on the invoice**. Anchoring
   on `zone_id` costs a `.tfvars` entry now and a VPC rebuild later.
   **What stays open is small and named:** re-run `./aws/AZs.sh` after every vend, and treat a disagreement
   as information rather than as a problem — with `zone_id` anchoring it changes nothing, which is the point.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item, and since
   2026-08-08 a **per-account** list rather than one list: Stage 3 step 8)
   and GitLab (the largest idle item).
5. **CodeArtifact ecosystem coverage (`plan/architecture.md` §4.3).** The CodeArtifact documentation lists Cargo among its
   supported formats, so the Rust question is down to confirming it in practice at Stage 6. Julia and R remain genuinely uncovered and keep their `plan/architecture.md` §4.3 fallbacks — they
   are what decides whether egress design B is livable.
6. **Whether SageMaker Studio can block file download** (Stage 6 — the question carries over unchanged to
   the ML-blueprint apps under D26). If not, Stage 11's threat model has to
   record an accepted risk rather than a control.
7. **The cross-account integrations in `plan/integrations.md`.** Each has a stated fallback, so none of them blocks
   a stage, but none of them is known to work either. They are listed there rather than repeated here.
   **INT-15 and 16, added 2026-08-08 by the pre-Stage-1 review, are not integration risks but
   control risks** — whether D13's constraint on execution roles survives blueprint-authored roles (INT-15),
   and whether the VPN restriction reaches the Unified Studio portal at all (INT-16). Each can invalidate an
   objective stated in `CLAUDE.md`, so they are answered at Stages 6 and 4 respectively and their outcome is
   written down either way.
   INT-11's organization halves were **enabled in Stage 1d** (RAM org-wide sharing on 2026-08-14; the LF
   cross-account version already read 4 with `SET_CONTEXT: TRUE`); what remains is Stage 5's — defending
   both values, which nobody set, against the first `aws_lakeformation_data_lake_settings` apply — and
   since D26 the row also carries the domain's account associations (INT-12); its failure mode is silence
   rather than an error. INT-13 (CodeConnections from the unified domain to the self-hosted GitLab in a private subnet)
   is the one with no convenience-preserving fallback: check it while building Stage 7, when GitLab first
   exists.
8. **How much of the S3 console survives the `aws:SourceVpce` condition** (INT-06, Stage 9). This
   decides whether D18's "read named S3 prefixes in Production" is usable through the console at all, or
   whether it is a CLI-over-the-tunnel operation that `README.md` has to say so about. Cheap to answer,
   annoying to discover by symptom.
9. **Whether sampled or synthetic Staging data makes the integration tests meaningful** (D20, Stage 9).
   The decision that Staging never holds a copy of production data is firm — the reasoning is in D20 and
   it is a security argument, not a cost one. What is open is the consequence: a test suite running
   against a sample catches permission, schema and wiring errors and misses everything that only appears
   at production distribution and volume. Answer it by recording, for each production incident this
   environment ever has, whether a Staging run could have caught it. Until there is such a record, this
   is a belief rather than a finding.
10. **How far the Sandbox ordinal propagates.** The token shape is settled — an ordinal integer,
    `awsds-infra-sandbox-1`, `-2`, … (`plan/conventions.md`, 2026-08-11) — and the SSO profile carries it
    today. What is open is which of the other five per-unit tokens D35 names do: the `<env>` token, the
    `Environment` tag value, the `Owner=sso-group-data-scientists` value, the `terraform-live/sandbox/` tree
    and `ENV=sandbox`. **Two of the five are not symmetrical with the profile and are the reason this is a
    question rather than a find-and-replace:**
    - **`Environment=sandbox-1` is an enumerated value inside an SCP-forced tag policy** (1c step 7.8), so
      it must be decided *before* that policy is written. Enumerating `sandbox` alone means the first apply
      in a vended `sandbox-2` is an `AccessDenied` in a new account (Lesson 14); enumerating every ordinal
      up front means editing an org policy at each vend. A prefix-shaped value would dissolve it, and tag
      policies do not do prefixes — which is the constraint, not a preference. It also splits every cost
      report by unit, which may be the point or may be noise.
    - **`sso-group-data-scientists-1` reads worse than the profile does.** A profile names an account and an
      ordinal is a fine name for an account; a *group* exists to say who is in it, and D35 wrote `<bu>`
      there for that reason. This is the one place where the business-unit name may still be the better
      token, and holding both shapes is not a contradiction — the group is on the people axis, the profile
      on the account axis (Lesson 9).
    **The first of those two is closed (user, 2026-08-13): `Environment=sandbox`, one shared value for
    every business unit**, written into 1c step 7.8. Per-unit cost attribution is by *account*, which the
    bill gives for free, and the alternative would have meant editing an organization policy at every vend
    with an `AccessDenied` in a brand-new account as the cost of forgetting. **The group token stays open**,
    as do the `<env>` token, the `terraform-live/` tree and `ENV=sandbox`; decide those with N=2 in hand.
11. **What `AWSOrganizationsFullAccess` reaches from inside a vended account.** Measured 2026-08-11, from
    the first `aws/list-identities.sh` snapshots: **every vended account carries
    `AWSOrganizationsFullAccess` → `AWSControlTowerAdmins`**, a group whose one member is the Control Tower
    admin SSO user — a third live path into every vended account, alongside the two the plan wrote
    (`AWS_STATE.md`, A.1). Nobody chose it; Control Tower created it with the landing zone, which is
    **Lesson 17** in its plainest form. What is open is its reach, not its existence. The managed policy
    grants `organizations:*`, and Organizations refuses most calls made from anywhere but the management
    account and a service's delegated administrator — so the residue is either nothing, or a read over the
    whole organization tree from an account that has no business seeing it. **The policy document cannot
    answer this**: what is left is exactly what the *service* refuses, which only a call finds out. Answer
    it by assuming that permission set in one vended account and running the reads and one harmless write;
    it costs minutes. Two things rode on it, and one is settled: **the deny half closed with 1c step 7.5**
    (`DenyLeaveOrganization` is attached against exactly this path; `POLICIES.md` records it as
    deliberately never probed, since its allowed outcome is the damage). Still open: the reach measurement
    itself, and whether the assignment should be removed at all — landing-zone state, so a decision in
    D32's neighbourhood rather than a cleanup.

### The Unified Studio mechanics, added 2026-08-13

`CLAUDE.md` named six SageMaker Unified Studio features as objectives on 2026-08-13. Reading them against
AWS's documentation produced four findings that are not decisions and are not risks either — they are
things the product does that the plan assumed differently, and each one is answered by a stage that has not
started. **The first one is load-bearing against principle 4.**

12. **The default notebook compute path does not support VPC.** SMUS notebooks run Spark through
    **Amazon Athena for Apache Spark by default**, and AWS documents plainly that Athena for Spark does not
    support VPC; the VPC-capable runtimes are **EMR Serverless, EMR and Glue**, selected per notebook
    through Spark Connect, and the Admin Guide carries a *Network isolation* procedure for **disabling
    Athena Spark** outright. A notebook whose compute is outside the VPC is outside the endpoint policies,
    outside the flow logs and outside the `aws:SourceVpce` conditions the whole data perimeter
    (`plan/architecture.md` §4.2) is built from — so "private by default" would be true of the account and
    false of the thing the data scientist actually runs. **Answer at Stage 6**, by disabling Athena Spark
    and choosing the runtime deliberately; record which, and what it costs, because EMR Serverless and Glue
    are metered differently from a free default. This may deserve a decision file rather than a question.
13. **Notebooks do not support trusted identity propagation, and that reaches a `CLAUDE.md` objective.**
    In an IAM Identity Center domain, notebooks fall back to **compatibility permission mode**, so data
    access resolves through the project/compute role rather than through the signed-in human. The DLP
    requirement *"restrict who can read which database, table, column and row"* is a Lake Formation
    row/column-filter statement about a **user**, and without TIP the unit of grant is the **project**.
    Two honest outcomes and they are very different: either per-user filtering is achievable through a
    different surface (the SQL/query path, which is not the notebook path), or the design's real grain is
    the project and `CLAUDE.md`'s objective is met at that grain with the difference written down.
    **Answer at Stage 5 while granting, and at Stage 6 while running.**
14. **The remote-IDE path is a file-transfer channel to a laptop.** `sagemaker:StartSession` plus the AWS
    Toolkit lets a local VS Code attach to a running space — a `CLAUDE.md` objective, so it is not
    something to deny. It also bypasses whatever a browser IDE could be made to restrict, which makes it
    the concrete version of **item 6** ("whether Studio can block file download") rather than a separate
    question: if the answer to 6 is "yes, in the browser", the remote session is the hole. AWS documents
    tag-based scoping of `StartSession` to a user's own private apps, which is the lever. **Answer at
    Stage 6, and record the residual in Stage 11's threat model either way.** 1c denies the action in
    `Workloads`, `Data` and `Identity` — where nobody should be running a space at all — and deliberately
    not in `Interactive`.
15. **"As many instances as they like" is a cost statement before it is an access statement.** Each
    JupyterLab or Code Editor space is a running instance billed by the hour, and D11 ("pay nothing while
    idle") is a property of the *design*, not of the user's habits. What closes it is idle shutdown plus a
    restricted instance-type list, not a policy — **Stage 6**, priced into `plan/cost-model.md` against the
    USD 50 ceiling. Also confirms rather than changes D7/D28: **SMUS workflows are MWAA**, serverless or
    provisioned, so Stage 10's orchestration comparison and this feature are one surface, not two.

### Raised by Stage 1c step 7.7, 2026-08-13

16. ~~**`Log Archive` and `Audit` have no Region ceiling, and nothing in the plan ever said they should not.**~~
    — **closed 2026-08-14 by Stage 1d step 12 (decision 10): the ceiling was enabled**, together with both
    root-user controls, so every governed account now sits under `us-west-2` and `Sandboxes` is the only OU
    carrying none (D37). **Three things the execution settled that the question could not:** `Security`
    **accepts `enable-control`** despite being Control Tower's foundational OU — the step's one real
    unknown; Control Tower packed the enablements in a **third** shape, a new document for the Region
    control and the pre-existing AWS guardrail for the root ones (11 → 13 statements, Lesson 23 again); and
    the by-hand probe answered in **both** accounts — `us-east-1` denied naming `p-idgyiios`, `us-west-2`
    `DryRunOperation`. What the closure *commits*, and it is the only lasting cost: GuardDuty (Stage 4),
    Security Hub (Stage 5) and Macie (Stage 11) are **not** exempt in the control, so each is `us-west-2`
    or it is denied. The original question, kept because the reasoning is what a future reader needs:

    7.7 enabled `CT.MULTISERVICE.PV.1` on the five OUs its own order named — `Policy Test`, `Workloads`,
    `Data`, `Interactive`, `Identity` — and **`Security` was never on that list**. It is not a regression
    and not drift: the OU was simply outside the step. But the consequence is worth deciding rather than
    inheriting, because those are the two accounts holding the immutable copy of the trail and the
    organization's findings, and they are now the only governed accounts where a resource may be created
    in any Region. **What makes it non-trivial:** `Security` is Control Tower's own foundational OU, its
    guardrail is AWS's rather than this project's, and Control Tower places resources there itself — so
    the exemption list of a Region control needs to be read against *Control Tower's* roles in those
    accounts before enabling anything, which is exactly the reading verification (vii) already
    demonstrates how to do. **Where it belongs:** Stage 1d, which is the stage that touches the log
    archive (Object Lock, step 9). Not a blocker for 7.8 or for anything before it.
    **Given a step of its own on 2026-08-14: [Stage 1d step 12](stages/stage-01d-org-wide-enablement.md),
    decision 10.** What the revision added beyond this paragraph: the two root-user controls belong to the
    same decision, and **the battery can never regress-test whatever lands there** — there is no CLI profile
    in Log Archive or Audit and creating one is refused, so the measurement is by hand in CloudShell plus a
    document read.

### Blocking Stage 1 — closed, condensed to one note (2026-08-15)

The three blocking decisions of the 2026-08-08 pre-Stage-1 review all closed the same day, and their
reasoning lives in the decision files, not here: **D29** (the test-OU question — `Policy Canary`, a
disposable account alone in `Policy Test`, because an *empty* staging OU tests nothing: an SCP is only
evaluated when a principal calls), **D16** (break-glass = the Management account root and nothing else;
its named instrument was replaced by 1d decision 8 with the live alarm plus a state read in the
break-glass test, and the MFA type is deliberately unspecified), and **D31** (no blanket `ReadOnlyAccess`
for the deployment manager — a bespoke `DeploymentManagerAccess` plus the derived-zone CMK, closing a D19
gap). D16's second half round-tripped through **D30** — adopted, then reverted when the recovery role
could not be delivered where its own justification needed it — leaving one lasting consequence: the
policy set lives in code, which is Stage 2 step 5's mandate. *(This section used to restate all three at
length, under item numbers 10-12 that collided with the live items above; the duplicates were retired
2026-08-15 — "item 10" and "items 12-15" now name only the live items.)*

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
