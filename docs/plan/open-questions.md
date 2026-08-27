# Open questions

Only things to find out by doing. **All thirty-seven decisions are closed** — a question that
turns into a choice becomes a decision file, not a longer entry here.

---

## 9. Open questions

Everything that was open before execution started is now closed in `docs/plan/decisions/` (D1-D37). What follows is
what is genuinely still unanswered:

1. **Which domain name to register (D15 phase 2).** Still the one input needed from the user, but the
   2026-08-09 revision moved *when*: it now blocks **Stage 13** alone, not Stage 7. Nothing before the
   public web tier registers or publishes anything — internal endpoints are `*.internal` names certified by
   the internal CA. Registration and validation still take time, so it is worth deciding before Stage 13
   starts; it is no longer worth doing early.
2. **D7/D28 - two verifications, not decisions.** The orchestration decision is closed (both built,
   Stage 10; alternative A is MWAA Serverless via `awscc_mwaaserverless_workflow`, verified to exist
   2026-08-08, re-verified 2026-08-16). What is open: (i) whether the awscc resource *applies* cleanly
   under the CI deploy role (INT-14 — fallback chain recorded there); (ii) whether **no-UI**
   observability is livable for a data scientist debugging a failed run — the 2026-08-16 documentation
   pass corrected "logs only": Serverless has run/task APIs, a console page, per-task log streams and
   (since 2026-06) EventBridge events, but still no Airflow web interface — which only the Stage 10
   comparison (its step 3.3 diagnosis session) can answer. Keep application entry points as plain
   containers so both implementations, and the two options that were not built, remain viable.
3. ~~**AZ name-to-ID mapping across accounts**~~ — **measured 2026-08-12 in Stage 1b step 6, and the answer
   did not decide the question the way the question expected.** Every account that has a profile returns
   an identical mapping (`us-west-2a` → `usw2-az2`, `b` → `az1`, `c` → `az3`, `d` → `az4`; the names are
   *not* in ID order). The full table is in
   [`docs/log/log-stage-01b-identity-and-controls.md`](../log/log-stage-01b-identity-and-controls.md), and
   `./aws/AZs.py` regenerates it into `aws/output/AZs.txt`.
   **Stage 3 anchors subnets on `zone_id` anyway** — this item used to say "if the mappings differ", and
   that conditional was written without knowing that the measurement can only ever speak for the accounts
   that exist. `Staging` is unvended and D35 plus [Stage 14](stages/stage-14-sandbox-vending.md) multiply
   Sandboxes; each new account gets its own mapping at vend time and nothing makes it match. Index-based
   placement would work today and break silently on the first account that disagrees, at USD 0.01/GB each
   way across the two peerings D14 and D21 keep busy — **no error, only a line on the invoice**. Anchoring
   on `zone_id` costs a `.tfvars` entry now and a VPC rebuild later.
   **What stays open is small and named:** re-run `./aws/AZs.py` after every vend, and treat a disagreement
   as information rather than as a problem — with `zone_id` anchoring it changes nothing, which is the point.
4. **Layer assignments.** `[P]`/`[D]`/`[E]` are cost judgements based on estimates. Revisit them at Stage 12
   against the real bill — especially the interface endpoints (the largest hourly item, and since
   2026-08-08 a **per-account** list rather than one list: Stage 3 step 8)
   and GitLab (the largest idle item).
5. **CodeArtifact ecosystem coverage (`docs/plan/architecture.md` §4.3).** The CodeArtifact documentation lists Cargo among its
   supported formats, so the Rust question is down to confirming it in practice at Stage 6. Julia and R remain genuinely uncovered and keep their `docs/plan/architecture.md` §4.3 fallbacks — they
   are what decides whether egress design B is livable.
6. **Whether SageMaker Studio can block file download** (Stage 6 — the question carries over unchanged to
   the blueprint-provisioned apps under D26). If not, Stage 11's threat model has to
   record an accepted risk rather than a control. **Narrowed 2026-08-16 by the documentation pass:** there
   is no product feature, but AWS publishes an official mitigation — a lifecycle configuration disabling
   the JupyterLab download extensions (`aws-samples/sample-disable-sagemaker-jupyterlab-download`). It is a
   UI control a user with a terminal can revert, so the honest classification is unchanged: no supported
   control; an official, bypassable mitigation; everything else is detection.
7. **The cross-account integrations in `docs/plan/integrations.md`.** Each has a stated fallback, so none of them blocks
   a stage, but none of them is known to work either. They are listed there rather than repeated here.
   **INT-15 and 16, added 2026-08-08 by the pre-Stage-1 review, are not integration risks but
   control risks** — whether D13's constraint on execution roles survives blueprint-authored roles (INT-15),
   and whether the VPN restriction reaches the Unified Studio portal at all (INT-16). Each can invalidate an
   objective stated in [`docs/plan/objectives.md`](objectives.md), and **both took their measured answers at
   Stage 6 on 2026-08-22**: INT-15's first real reading is the boundary PRESENT on the provisioned role —
   injected via the configuration's write-only field into the stack template, with the qualification that
   the template's two conditional EMR roles carry none — and INT-16 is answered in the strong form (VPN-only
   APIs and console, NOT a VPN-only portal: off-VPN the whole interactive surface works, JupyterLab
   included). The INT-16 closing choice — fallback (i) versus recorded acceptance — is the user's, deferred.
   INT-11's organization halves were **enabled in Stage 1d** (RAM org-wide sharing on 2026-08-14; the LF
   cross-account version already read 4 with `SET_CONTEXT: TRUE`); its Stage 5 half **closed 2026-08-19
   (pass 3, confirmed per account at pass 4 — see the row)**. The credential-vending half of
   `sts:SetContext` against the RCP is **exercised too (2026-08-19, 4d groups A and B)**: the persona's
   cross-account queries `SUCCEEDED` through the version-4 share from two provisioned roles, so vending
   worked and the RCP left it untouched. The domain's account associations (INT-12)
   **closed at Stage 6 (2026-08-21): the association AUTO-ACCEPTS** — org-scoped RAM share, no invitation,
   no clock — and the feared silent-failure mode never materialised; the measured onboarding choreography
   exercised it end to end. INT-13 (CodeConnections from the unified domain to the self-hosted GitLab in a private subnet)
   is the one with no convenience-preserving fallback: check it while building Stage 7, when GitLab first
   exists.
8. **How much of the S3 console survives the `aws:SourceVpce` condition** (INT-06, Stage 9). This
   decides whether D18's "read named S3 prefixes in Production" is usable through the console at all, or
   whether it is a CLI-over-the-tunnel operation that `README.md` has to say so about. Cheap to answer,
   annoying to discover by symptom.
   **Informed 2026-08-19 by 4d's measurement, not closed**: S3 traffic from a tunneled laptop exits
   through the **VPN home's gateway endpoint** and presents `aws:SourceVpce` = that endpoint id, never
   the Elastic IP (CloudTrail, one session: S3 as the host's private address + the vpce id, Glue as the
   EIP). The console's own S3 API calls ride the same full tunnel (`vpn.md` §C routes `0.0.0.0/0`), so
   INT-06's allow-list must carry the VPN home's endpoint — the same axis rule Lesson 33's second
   finding states for the lake — and the open half narrows to *which* calls the S3 console actually
   makes, from where.
9. **Whether sampled or synthetic Staging data makes the integration tests meaningful** (D20, Stage 9).
   The decision that Staging never holds a copy of production data is firm — the reasoning is in D20 and
   it is a security argument, not a cost one. What is open is the consequence: a test suite running
   against a sample catches permission, schema and wiring errors and misses everything that only appears
   at production distribution and volume. Answer it by recording, for each production incident this
   environment ever has, whether a Staging run could have caught it. Until there is such a record, this
   is a belief rather than a finding.
10. **How far the Sandbox ordinal propagates.** The token shape is settled — an ordinal integer,
    `awsds-infra-sandbox-1`, `-2`, … (`docs/plan/conventions.md`, 2026-08-11) — and the SSO profile carries it
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
    **A sixth token arrived 2026-08-26 (Stage 16): the bucket name `awsds-sandbox-lake`** — bucket names
    are **global**, so a second unit's lake cannot reuse it; unlike `Environment`, no shared-value option
    exists for this one, and the answer becomes an input of Stage 14's `sandbox-unit` module.
11. ~~**What `AWSOrganizationsFullAccess` reaches from inside a vended account.**~~ — **measured
    2026-08-15, in Stage 2 rather than in the 1c step that had been carrying it, and it came back as two
    answers rather than one.** Assumed as `AWS Control Tower Admin` through that permission set, in two
    accounts, with every call and every id identical and exactly one variable: the account.
    - **In a plain vended account (`Development`) it is nearly inert, which is what the question guessed.**
      Two calls answer — `describe-organization`, and the account's own `describe-effective-policy` — and
      `list-roots`, `list-accounts`, `list-organizational-units-for-parent`, `list-policies`,
      `describe-policy`, `list-targets-for-policy`, `list-parents` and `describe-account` all return
      `AccessDenied`. The feared residue — *a read over the whole organization tree from an account that
      has no business seeing it* — **does not exist** there.
    - **In `Identity` it reaches everything**: the accounts, the OU tree, every SCP with its full text,
      and — the half that matters — **policy writes**, proven by a duplicate `AttachPolicy` on
      the root returning `DuplicatePolicyAttachmentException` where `Development` returns `AccessDenied`.
      Not because of the permission set: because **Stage 2 step 5.1's delegation names the account**
      (`arn:aws:iam::<Identity>:root`), so every principal there holding `organizations:*` inherits it.

    **What that does not mean, and it is what decided the disposition:** it grants the Control Tower admin
    **no capability it did not already hold**. That user is `AWSAdministratorAccess` on **Management**,
    where Organizations is native — it could always rewrite every SCP, guardrails included. The Identity
    path is a redundant door, not a new room. **So the finding is not the assignment; it is the
    account-wide principal**, which today reaches two principals and tomorrow reaches whichever this
    account acquires — a persona set from Stage 2 step 5, a pipeline role from Stage 8, or whatever
    Control Tower adds next. Lesson 17, one stage ahead of itself.

    **Decided 2026-08-15, and the two halves went opposite ways.** *The assignment stays*: the gain from
    removing it is ~zero while the same human administers Management, and it is landing-zone state Control
    Tower re-creates — so removal buys a standing verification (the shape 1b's verification (vi) already
    carries) in exchange for tidiness. *The delegation gets narrowed*, which closes the class instead of
    the instance: **[Stage 2 step 5.1a](stages/stage-02-terraform-foundation.md)** adds a `Condition` on
    `aws:PrincipalArn` scoping the two write statements to `…AWSReservedSSO_InfrastructureAccess_*` —
    decision 7's idiom, wildcard account included, for decision 7's reason (the role suffix is minted per
    account; observed as two different suffixes on the day). **What stays genuinely open is only whether
    that works:** this document already lost `NotAction`/`NotResource` to an AWS restriction nobody
    predicted, so whether it accepts a principal condition at all is unverified — and a refusal is a safe
    failure, since nothing changes. It does **not** close the reads either way: those come from the account
    being the Identity Center delegated administrator, not from this delegation.

    **What neither half touches, recorded so it is not mistaken for handled:** one human holding
    `AWSAdministratorAccess` on Management, Log Archive and Audit at once, able to delete the record of its
    own use. That belongs to [`docs/plan/institutional-delta.md`](institutional-delta.md), not to this item.
    The other half that was already settled: **the deny closed with 1c step 7.5** —
    `DenyLeaveOrganization` is attached against exactly this path, and `POLICIES.md` records it as
    deliberately never probed, its allowed outcome being the damage.

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
    (`docs/plan/architecture.md` §4.2) is built from — so "private by default" would be true of the account and
    false of the thing the data scientist actually runs. **Answer at Stage 6**, by disabling Athena Spark
    and choosing the runtime deliberately; record which, and what it costs, because EMR Serverless and Glue
    are metered differently from a free default (EMR Serverless is measured in `docs/PRICING.md` §5 since
    2026-08-16). **Sharpened by the 2026-08-16 documentation pass:** the documented "disable" is three
    controls, and only the SCP on `athena:StartSession`/`UpdateSession` removes Spark *without* removing
    Athena SQL — the Tooling blueprint's Athena flag removes both, and SQL is the D13 path (Stage 6
    step 1.6 owns the choice). **Two riders added 2026-08-20 from pass 4e, which denied
    `athena:StartQueryExecution` elsewhere and probed it — 1.6 carries them in full, this is the pointer.**
    The action *pair* above wants confirming against the machine-readable action list before it ships (the
    installed CLI has no `update-session`), and **Athena's refusal names no policy**, so the probe for
    whatever statement lands here has to be a contrast pair rather than a wording match. Note also that 4e
    does **not** touch this item's surface: it binds `Data` and `Identity`, while the D13 query path runs
    in the consumer accounts, under `Interactive`.
    **Re-examined 2026-08-19 against [Athena Spark's PrivateLink release](../REFERENCES.md) (2026-04-21),
    which looks like it retires this item and does not.** PrivateLink moved the **client → session** path —
    Spark Connect, the Live UI, the History Server, three new interface endpoints — and **not where the
    session runs**: there is no `NetworkConfiguration` anywhere in the Athena Spark API, and the SMUS
    network-isolation page, current after the release, still answers VPC connectivity with *"use Amazon EMR
    or AWS Glue instead"*. The executor stays outside the VPC, so this item stands unchanged.
    **What the re-read did change is the shape of the answer, not the answer**: Stage 6 decision 3 is now
    closed ahead of the stage (the SCP, the boundary carrying no Athena clause, the three optional session
    endpoints deliberately uncreated), so what remains at Stage 6 is *execution and its probes*, plus the
    runtime choice — decision 1, which the same reading **reopened** on an endpoint-count cost the compute
    comparison never saw. **The distinction this item now turns on, and the one a hurried re-reading drops
    first: where a session is reached *from* is not where it *runs*.** The revision trigger is worded
    against exactly that (Stage 6 step 1.6): executors in our subnets, under our security group — never a
    headline saying VPC is supported.
13. **Notebooks do not support trusted identity propagation, and that reaches an `objectives.md` objective.**
    In an IAM Identity Center domain, notebooks fall back to **compatibility permission mode**, so data
    access resolves through the project/compute role rather than through the signed-in human. The DLP
    requirement *"restrict who can read which database, table, column and row"* is a Lake Formation
    row/column-filter statement about a **user**, and without TIP the unit of grant is the **project**.
    Two honest outcomes and they are very different: either per-user filtering is achievable through a
    different surface (the SQL/query path, which is not the notebook path), or the design's real grain is
    the project and [`docs/plan/objectives.md`](objectives.md)'s objective is met at that grain with the difference written down.
    **Answer at Stage 5 while granting, and at Stage 6 while running.**
    **The mechanism now has a name (2026-08-16):** "compatibility permission mode" is not the
    documentation's vocabulary — the real lever is trusted identity propagation, supported since 2025-09
    for Athena, Redshift, Glue and EMR and enabled per project profile through the Tooling parameter
    `enableTrustedIdentityPropagationPermissions`; JupyterLab and Visual ETL still resolve through the
    project role either way. **Its documented cost: remote access does not work with TIP enabled** — so the
    grain decision and the remote-VS-Code objective pull against each other, and Stage 6 decision 2 records
    which yields. **Decision 2 DELIVERED 2026-08-21: TIP locked `"false"`, non-editable, in both project
    profiles — remote access won, as this item's default predicted; the per-user options stay mapped, not
    required.** **The Stage 5 half is answered (2026-08-18, Stage 5 decision 6, the user's): the grain
    target is reframed** — entitlement follows the toolset's practice (grants to roles/projects, assumed
    by people and services), and per-user attribution is an *exploration*, not a requirement; the
    objective is met at the role/project grain, stated in `docs/GOVERNANCE.md` §"The grain". What
    survives: Stage 5 pass 2 maps the per-user options and their costs (verification viii), and the
    Stage 6 half — whether TIP is ever worth its remote-access cost — is now weighed against a *mapped
    option*, not against an objective, with remote access favoured by default. **Sharpened 2026-08-19
    (the decision 1 re-read):** the notebook's Spark Connect page lists TIP *and* FGAC as unsupported for
    **all three engines** (Glue, EMR Serverless, EMR on EC2 — full-table access), so the TIP lever is
    SQL/query-path only; the one documented notebook-side fine-grained route is an EMR-S **compute
    connection** in `project.spark.fineGrained` mode — whether an IdC-domain notebook can actually use it
    is Stage 6 decision 1's second in-stage reading.
    **A second mapped option arrived 2026-08-24, on the S3 surface, while the laptop-vending feature
    chose the persona-role grain:** S3 Access Grants takes grantees of `DIRECTORY_USER`/`DIRECTORY_GROUP`
    (the CLI's own model, not prose), which would make a project-storage grant per-person or per-IdC-group
    and CloudTrail attribution per-human — the TIP *outcome* on the S3 surface without the Tooling
    parameter, which reaches only the SQL/query path and stays locked `"false"`. What is missing is
    measured: the Sandbox instance carries **no Identity Center association** (none of the three
    `IdentityCenter*` fields its API models — a reading, not a silent instrument), so
    `associate-access-grants-identity-center` would have to run first — a new IdC↔Access-Grants crossing
    that deserves its own decision rather than arriving as a side effect. Parked with this item's other
    mapped options; the state is `AWS_STATE.md`'s vending row. **Stage 16 became a consumer of this
    option on 2026-08-26**: its decision 2 recommends the IAM grain for the per-group lake grants and
    defers directory grantees to this item — choosing them there requires the association first,
    measured, never as a side effect.
14. **The remote-IDE path is a file-transfer channel to a laptop.** `sagemaker:StartSession` plus the AWS
    Toolkit lets a local VS Code attach to a running space — an [`objectives.md`](objectives.md) objective, so it is not
    something to deny. It also bypasses whatever a browser IDE could be made to restrict, which makes it
    the concrete version of **item 6** ("whether Studio can block file download") rather than a separate
    question: if the answer to 6 is "yes, in the browser", the remote session is the hole. AWS documents
    tag-based scoping of `StartSession` to a user's own private apps, which is the lever — **the exact SMUS
    policy is documented (read 2026-08-16): `StartSession` on `space/*` conditioned on the
    `AmazonDataZoneProject` and `AmazonDataZoneUser` tags, with `sagemaker:RemoteAccess` on
    `CreateSpace`/`UpdateSpace` as the kill-switch, and one residual worth writing down now: remote
    sessions authenticate with IAM credentials even in IdC domains and persist up to 12 h after portal
    logout.** **Answer at Stage 6 (step 3.2), and record the residual in Stage 11's threat model either
    way.** 1c denies the action in
    `Workloads`, `Data` and `Identity` — where nobody should be running a space at all — and deliberately
    not in `Interactive`.
15. **"As many instances as they like" is a cost statement before it is an access statement.** Each
    JupyterLab or Code Editor space is a running instance billed by the hour, and D11 ("pay nothing while
    idle") is a property of the *design*, not of the user's habits. What closes it is idle shutdown plus a
    restricted instance-type list, not a policy — **Stage 6**, priced into `docs/plan/cost-model.md` against the
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
    `DryRunOperation`. What the closure *commits*, and it is the only lasting cost: GuardDuty (Stage 15 since the
    2026-08-18 split; Stage 4 when this was written), Security Hub (Stage 5) and Macie (Stage 11) are
    **not** exempt in the control, so each is `us-west-2` or it is denied. The original question, kept because the reasoning is what a future reader needs:

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

### Raised by Stage 4 step 8.3, 2026-08-17

17. **`InfrastructureAccess` stays reachable from any network — decided (option a), not deferred, and
    this item exists so the decision stays visible rather than becoming furniture.** Stage 4's
    `DenyControlPlaneOffVpn` pins the six persona sets to the WireGuard Elastic IP and was measured
    doing so (the control-plane pair, log entry ten); the seventh set was to gain it in a separate
    diff. **Writing that diff surfaced a deadlock the stage's Risks row had predicted in one line:**
    the VPN host is *stopped* between sessions — the normal `[D]` state, not a failure — and starting
    it requires `ec2:StartInstances` as `awsds-infra-sandbox-1`, which the deny would only permit from
    the address of the host that is stopped. You cannot start the VPN host without the VPN host, and
    the only way back in is break-glass — for a routine event, which un-makes break-glass. Three exits
    were weighed: (a) leave the seventh set off-VPN; (b) apply and rehearse break-glass as the normal
    recovery, rejected because the deadlock state is *normal*, not exceptional; (c) apply with a
    narrow `NotAction` emergency hatch (`ec2:StartInstances` + `DescribeInstances`), which converts
    the deadlock into an operation at the price of "a stolen infrastructure session can start
    instances off-VPN". **The user chose (a): the objective's "all user access through the VPN" is
    delivered for every persona, and the administrative credential is deliberately outside it, valued
    as the recovery path that keeps working when the VPN itself is what broke.** What would reopen
    this, and none of it is a current stage's prerequisite: a second operator (one person's recovery
    path is another's standing bypass); GuardDuty giving the off-VPN use of that credential a
    watcher, which weakens the "nothing would notice" half of the risk — **Stage 15 since the 2026-08-18
    split (it was Stage 4's pass 4), which defers this reopener with it; Stage 15 step 6 re-reads this
    question the day it closes**; or Stage 14's multiplication
    of VPN homes making option (c)'s hatch list a maintained table rather than two actions. The
    institutional shape of this trade is in
    [`institutional-delta.md`](institutional-delta.md) — the lab's admin credential is
    network-unrestricted because it is also the fire escape, and an institution separates those two
    jobs instead of choosing between them.
    **A third use of the exemption showed up on 2026-08-19/20, unplanned and worth recording, because it
    is an argument nobody made when (a) was chosen.** The exemption is also the **negative control** for
    that deny. When every persona's direct S3 call started failing, the reading that isolated the cause
    was `InfrastructureAccess` succeeding on the same bucket over the same tunnel — exonerating the
    bucket policy, the CMK, the gateway endpoint and the network in one call, and leaving the identity
    statement as the only remaining explanation. A deny applied to *every* set would have had no such
    control inside the estate. That is a genuine benefit of (a), and it is also a warning: it exists
    only because the exempt set is otherwise identical in reach, so **narrowing `InfrastructureAccess`
    later removes a diagnostic instrument as well as a bypass** — say so at the time rather than
    discovering it during the next incident. Separately, the amendment applied that day means this
    statement now pins **two** kinds of thing, an address and a list of endpoint ids: a malformed entry
    in the second list is not a lockout but a **silent regression** to the 4d defect, which is why
    `permission-sets.tf` carries a second `precondition` beside the CIDR one.

### Raised by Stage 5 pass 3, 2026-08-19

    **A FOURTH use, 2026-08-21, and this one was surfaced by the user rather than by an executor.**
    Stage 6 step 5.0's build host (`sandbox/buildbox/`) is reached with `aws ssm start-session`, and the
    user noticed it works **with the tunnel down** and asked whether that was expected. It is, for
    exactly this decision: `start-session` is an API call to a public endpoint, the agent holds its
    channel open outbound, and `InfrastructureAccess` carries no `DenyControlPlaneOffVpn`. What it
    cost was a **false sentence** — the slice had shipped claiming *"reachable only with the tunnel
    up"*, which was true of its network path and false of its shell. The user's resolution was to
    **withdraw the requirement rather than fake it**: the buildbox now has no ingress rule at all and
    SSM is the only way in, with the egress-through-the-VPN-host requirement kept unchanged. **The
    reusable part is the shape, not the host:** an exemption taken for a recovery path keeps arriving
    in places nobody weighed it for, and each arrival is a chance for a design to describe itself
    wrongly. That is what this item is for.
18. **Does `lakeformation:CreateLFTag` in the governance manager's IAM half make it an "LF-Tag creator",
    and therefore able to *grant data* it cannot read?** The larger question this came from is
    **answered** and closed: AWS states that granting data permissions through an LF-Tag expression
    requires the `Grant with LF-Tag expressions` permission, which *"the data lake administrator and the
    LF-Tag creator implicitly receive"* — so a persona holding only `ASSOCIATE` on the tags and
    `DESCRIBE` on the catalog **tags and does not grant**, which is what decision 5 intended and what
    pass 2 built. **The residue is the parenthesis.** The persona's IAM statement
    `AdministerLakeFormation` carries `CreateLFTag`, and no page says whether "LF-Tag creator" means
    *a principal able to create tags* or *the creator of the tag in question* — the tags in this lake
    were created by the infrastructure user, through Terraform. The two readings differ by a real
    power: under the first, the persona can grant `SELECT` on data it is itself denied from reading
    (`DenyReadingTheRows`), which is not obviously wrong for a governance manager but was never decided.
    **Settled by measurement, not by more reading:** a governance-manager session attempting a
    tag-expression grant — **recorded as Stage 6's verification (xii)**, beside **(xiii)**, which is
    pass 2's "can it actually tag" proof and needs the same sign-in. **If the answer is yes**, the decision to
    take is whether the delegation plane is wanted; **if no**, decision 5 needs no revision at all. Do
    not close this from the documentation — the pages that would settle it are the ones already read.

### Raised by Stage 5 pass 4d, 2026-08-19

19. **When do the catalog crawlers run?** Nothing has ever said. `awsds-data-raw` and
    `awsds-data-dropbox` were created at pass 1 deliberately **never-run**, and pass 4d found that the
    omission is not cosmetic: **no principal in this estate can start them.**
    `DenyCatalogMaintenanceRunsExceptMaintenanceRole` admits only `awsds-data-catalog-maintenance` *or a
    service principal*, and that role's trust policy carries one statement,
    `Principal.Service = glue.amazonaws.com` — it is an execution role Glue assumes to *perform* a crawl,
    never an identity a person or another service becomes. **So the only invocation path the design
    permits is Glue's own scheduler, and `Schedule` is `null` on both.**
    **Neither document is at fault, and the question is not "how do we unblock it".** The SCP and the
    trust policy together express something defensible and arguably stronger than intended: catalog
    refreshes happen on a cadence somebody chose, and no human can force one. **And half of this WAS
    chosen (found 2026-08-20, re-reading `maintenance.tf`'s own comment): a standing schedule was
    deliberately rejected on cost** — DPU-hour with a 10-minute billed minimum, cron-always out-costing
    the storage it catalogs — **`DL-3` checks that rejection, and the chosen trigger was "on-demand,
    before a pickup". What 4d measured is that on-demand has NO DEMANDER.** So the untaken decision is
    narrower than a cadence: *who, or what event, demands a run.* **Do not settle this by loosening
    either document** — that trades a real control for the convenience of a manual run.
    **The two crawlers are not the same question, and that is the substance.** `awsds-data-dropbox`
    sits on an **ingestion** path (D18/D25): a person uploads a file and waits for it to appear, so the
    cadence is a latency promise to a user. `awsds-data-raw` catalogues a zone whose producer is
    **Stage 9's governed cross-account write**, so its cadence is about an ETL that does not exist yet
    and may not need a crawler at all once the writer registers its own tables. A single schedule
    applied to both is the answer nobody should reach for first.
    **Three inputs this needs before it can be decided.** (a) **Cost** — the shape is already in
    `maintenance.tf`'s comment (DPU-hour, 10-minute billed minimum) and is what killed the cron; a
    per-demand run pays the same minimum per event, which is the other side of the same argument.
    (b) **Whether Glue's S3 event-driven crawl mode satisfies the SCP** — the crawler subscribes to a
    queue and Glue initiates the run, which *may* present as `aws:PrincipalIsAWSService` and would suit
    the drop-box far better than a fixed interval. **This is verification (iv)'s exact shape**
    (S3 → EventBridge → Glue workflow, landing on the 3.4 service-guard side), already asked by the
    stage — **measure it against the guard rather than assuming it lands on the allow side**; if it
    does not qualify, event-driven ingestion is blocked by the SCP as written and that becomes a
    decision in its own right. (c) Whether Stage 9's writer makes `awsds-data-raw` redundant.
    **The consequence of leaving it open, said plainly**: D25's drop-box stays inert **even after
    `DenyControlPlaneOffVpn` is amended**. The write and the catalogue are independent failures, and
    fixing the first alone produces a bucket that accepts files nothing ever reads.
    **That sentence stopped being a prediction on 2026-08-20**: the amendment applied and the write was
    measured working (`PutObject` succeeds, the three read/list/delete verbs implicit-deny). So the
    drop-box now **accepts files and nothing catalogues them** — this question is the only thing between
    a delivered file and a usable table, and its cost is no longer hypothetical. A second, smaller
    consequence of the same measurement, which belongs to whoever answers this: the writer holds no
    delete and the collector is Stage 9's, so **anything written to the letterbox stays there** until
    that stage lands (`AWS_STATE.md` `EXC-02` declares the one object that already has). An answer that
    starts the crawler does not empty the box; only the pickup does.

    **The addressee, added 2026-08-20 so this is not recorded only at the end that raised it (Lesson 34):
    Stage 6 step 2.1 is the first consumer.** That step is where a blueprint-provisioned notebook role
    would join `writer_role_patterns` and become a drop-box writer — so the demander question is read
    **before** that grant, not after it. Stage 6's Prerequisites row now carries the pointer back.

### Raised while reading the persona sets, 2026-08-19

20. **Does `datazone:Get*` in the governance manager's set reach `GetEnvironmentCredentials` — and does
    credential vending carry the set past its own `DenyReadingTheRows`?** `OwnTheDataZoneDomain`, in
    `terraform-live/identity/sso/policies-approvers.tf`, states its intent in the comment above it —
    *"read as the approval verbs rather than as `datazone:*`"* — and then admits `datazone:Get*`, which
    matches `GetEnvironmentCredentials` lexically. **The statement below it denies the sibling API by
    name**: `DenyReadingTheRows` closes `lakeformation:GetDataAccess` with an argument that applies here
    verbatim — it *"vends temporary credentials for the underlying S3 objects"*, and *"the set
    ADMINISTERS this mechanism; using it is the thing it must not do."* Two credential-vending APIs on
    one axis; one denied by name, the other admitted by a wildcard.
    **What makes it a path rather than an ugly wildcard** is its neighbour in the same statement,
    `datazone:CreateProjectMembership`. Self-add to a project, then ask that project's environment for
    credentials, and the resulting session is a **different principal** — one the permission set's own
    `Deny` does not follow into. Lesson 28 read backwards: a deny attached to an identity says nothing
    about an identity that identity can obtain.
    **THE BLOCKER IN THE NEXT SENTENCE EXPIRED ON 2026-08-21** — the domain exists (`dzd-d8yrvx1ko7im6o`,
    `AVAILABLE`) and **both Interactive accounts are associated**, so *"the domain does not exist, Stage 6
    is not open"* no longer holds and the attempt this question waits on is available as soon as step 2.4
    has a project. **One half is already answered**: the account association's RAM permission contains
    `datazone:GetEnvironmentCredentials` **and** `GetDomainExecutionRoleCredentials`, so the share does
    not stand between a caller and either API — whatever settles this will be an IAM statement, not a
    sharing one. The wider surface that measurement opened is **question 21**.
    **Why this is a question and not a finding.** Nothing has been attempted — and no page
    consulted says what `GetEnvironmentCredentials` requires of its
    caller or *which* role it hands back; the environment user role and the project role may not be the
    same object. The D13 boundary (`awsds-<env>-project-boundary`, step 2.1) may already cap whatever is
    vended, and the OU SCPs reach it regardless. **Lesson 30 is the reason for the restraint**: a page
    that was not found is not a property of the world.
    **Settled by attempting it, in the session (xii) and (xiii) already require** — a governance-manager
    sign-in with the tunnel up, against Stage 6 step 2.4's throwaway project. Three outcomes, costing
    different things: **(a) denied** — record it and close; **(b) it vends, and the boundary caps what the
    vended role reads** — the wildcard is still worth narrowing, because the intent in the comment and the
    reach of the document have drifted, which is the failure the comment was written to prevent;
    **(c) it vends a principal that reads rows** — `Get*` becomes an enumeration in that statement, and
    the same audit is owed to every other wildcard in the approver sets.
    **Where it sits in the map**: the same axis as INT-11's credential-vending half — what a *service* can
    hand a principal that the principal could not ask for directly. Two surfaces now, which is the
    argument for carrying it as an axis rather than as two incidents.

### Raised by Stage 6 step 1.3, 2026-08-21

21. **Nothing in this design writes a `datazone:` policy for the Interactive OU — and since the account
    association there is now a cross-account surface with a 152-action ceiling.** The association shares
    the Data Governance domain into Sandbox and Development under
    `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess`: **152 actions**, a strict superset of
    the resource-type default's 111, including `AddPolicyGrant`/`RemovePolicyGrant`, `CreateProject`,
    `DeleteProject`, `DeleteEnvironmentBlueprintConfiguration` and
    `GetDomainExecutionRoleCredentials` — the last of which hands out credentials for a role that lives
    in the **domain** account.
    **This is a ceiling, not access, and today the intersection is narrow** (Lesson 28). Measured the
    same day: `datazone:` appears in the persona sets **only** in `policies-approvers.tf`, as the
    approval family; `DataScientistAccess` names none. `DenyDataZoneEntirely` covers the **Workloads**
    OU in full, and the **Interactive** OU carries no `datazone:` statement at all — so there the whole
    constraint is member-account IAM, and the only identity holding it is `InfrastructureAccess`.
    **What makes it a question rather than a note is what happens at 1.4/1.5.** Those steps have the
    blueprint author IAM policies for project and environment roles **in the member accounts**
    (INT-15), and the D13 boundary `awsds-<env>-project-boundary` does not narrow `datazone:` at all —
    its ceiling statement is `Allow *` with three lake-shaped denies (S3 on registered prefixes, the
    drop-box write, the lake key). So from the moment blueprints are enabled, what a service-authored
    role may do against the shared domain is bounded by **AWS's managed RAM permission and AWS's own
    policy authorship**, and by nothing this project wrote. Lesson 18 is the reason that is worth
    naming: a policy never constrains the principal that authors it.
    **(a) ANSWERED 2026-08-21 — the ceiling is NOT negotiable.** `datazone:Domain`'s row on RAM's
    shareable-resources page reads **"Can use customer managed permissions: No"**, and RAM agrees:
    `ram list-permissions --resource-type datazone:Domain --permission-type CUSTOMER_MANAGED` returns
    empty. AWS's managed set is the only choice, so the six published permissions are the whole menu and
    the 152-action one is the narrowest that carries the V2 half. *(The same row also says the domain
    **can** be shared with accounts outside its organization — not what was done, and worth knowing.)*
    **So the only remaining lever is (b), an SCP on the Interactive OU** naming the verbs that are
    governance rather than project work — `AddPolicyGrant`, `RemovePolicyGrant`,
    `DeleteEnvironmentBlueprintConfiguration`, `GetDomainExecutionRoleCredentials`.
    **A measured input arrived 2026-08-22 and it halves the menu: `AddPolicyGrant` is now exercised by the
    estate's OWN Terraform from inside the member accounts** — `sagemaker-prereqs` v0.3.0's `grants.tf`
    applies the 11 `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grants per member, and `RemovePolicyGrant` is what
    their destroy calls — so a blanket Interactive-OU deny on those two verbs breaks the estate's own
    applies, the exact product-break outcome this question reserved for
    `DeleteEnvironmentBlueprintConfiguration`. At minimum those two are "recorded ceiling, no blanket
    deny" (or a deny needing a principal condition).
    **(c) AND THE SEQUENCING IN THE SENTENCE THIS REPLACES WAS BACKWARDS.** It said settle *before* 1.4,
    *"after that, service-authored roles exist and the question stops being theoretical"* — which is
    exactly why it must come **after**. The question is whether those four verbs are governance-only or
    whether the blueprint machinery itself uses them, and **that cannot be read until AWS has authored
    the policies**: `DeleteEnvironmentBlueprintConfiguration` in particular is what a `terraform destroy`
    of a `sagemaker/` slice calls, so a deny written blind would break the estate's own teardown.
    Lesson 5 cuts both ways here — an SCP that breaks the product is worse than none — and Lesson 20 says
    a deny nothing exercises reads as coverage.
    **So: measure at 1.5, decide at 1.6 — and the measurement UNBLOCKED 2026-08-22**: the first provisioned
    role exists (`datazone_usr_role_…`, Sandbox 1), so the reading is now performable against a real
    object. Read the policies the blueprint
    authored on the project and environment roles (an extension of the reading `US-8` takes for the
    boundary — and note US-8 itself reads via per-role `get-role` since the same day, because `list-roles`
    omits the field) and check whether any of the four verbs appears. None appearing makes the SCP cheap and
    safe; any appearing turns the deny into a product break, and the answer becomes "recorded ceiling,
    no deny".
    **This does NOT block step 1.4** — corrected the same day it was written. Nothing outside the member
    accounts is reachable today that `InfrastructureAccess` could not already reach directly.
    **Not a reason to delay 1.3, which is done**: nothing reaches the wide half today.
    **Read with question 20, which is the same axis at a different scale** — that one asks whether one
    wildcard in one approver set reaches `GetEnvironmentCredentials`; this one asks what governs the
    surface that API sits on. The measurement below settles the RAM half of 20 in passing: **both**
    `GetEnvironmentCredentials` and `GetDomainExecutionRoleCredentials` are inside the share's
    permission, so the share is not what stands between a caller and either API. Whatever answers 20
    will be an IAM statement, not a sharing one.

    **THE MEASUREMENT IS TAKEN — 2026-08-26, read-only, Sandbox 1, and it removes the blanket deny from
    the menu entirely.** Every policy on every role the Tooling stack provisioned, plus the two service
    roles the `sagemaker/` slice owns: **five roles, eleven AWS-managed documents**, all AWS-authored
    (not one inline policy anywhere — so "AWS's own policy authorship" is the whole of it, exactly as
    this question predicted). Of the four verbs:

    | Verb | In AWS's authorship? | What that means for a deny |
    |---|---|---|
    | `AddPolicyGrant` | **absent** | but already off the menu since 2026-08-22 — **our own** `grants.tf` calls it from inside each member |
    | `RemovePolicyGrant` | **absent** | idem, on `terraform destroy` |
    | `DeleteEnvironmentBlueprintConfiguration` | **absent** | but a `sagemaker/` slice's own destroy calls it as `InfrastructureAccess` — the product break this question reserved for it is **ours**, not AWS's |
    | `GetDomainExecutionRoleCredentials` | **PRESENT** | `SageMakerStudioProjectUserRolePolicy` v74, `Sid` `DataZoneUserPermissions`, on the project user role — scoped to `arn:aws:datazone:*:*:domain/${aws:PrincipalTag/AmazonDataZoneDomain}`. **Every project role holds it**, so a blanket deny breaks every project |

    **So all four are "recorded ceiling, no blanket deny", and outcome (b) of the menu is the answer** —
    but by two different mechanisms, and the distinction is what a future reader needs: three are used by
    **this estate's own Terraform**, and the fourth by **the product**. A deny is still expressible with a
    principal condition (`ArnNotLike` over `AWSReservedSSO_InfrastructureAccess_*` **and**
    `datazone_usr_role_*`), and what it would then reach is nothing: the persona sets carry no `datazone:`
    action at all outside `policies-approvers.tf`, so the deny would be attached and never exercised —
    [Lesson 20](lessons.md) squarely. **The decision is the user's**, and the recommendation on record is
    to write the ceiling down and attach nothing.
    **Two riders the same reading produced, neither of which changes the answer.**
    `SageMakerStudioProjectRoleMachineLearningPolicy` grants `datazone:*Compute*`, `CreateAsset*`,
    `List*` and `Search*` on `Resource: "*"` — unscoped by domain, unlike the user-role policy beside it;
    that is the widest `datazone:` reach in the account and it belongs in the ceiling record. And the
    project role's S3 reach is **principal-tag-shaped**, not path-shaped:
    `arn:aws:s3:::${aws:PrincipalTag/DomainBucketName}/${aws:PrincipalTag/AmazonDataZoneDomain}/${aws:PrincipalTag/AmazonDataZoneProject}/*`
    — which is *why* the bucket name is free (Stage 6's v0.3.2 finding, whose `*/dzd*/<project>/`
    shorthand is the **provisioning** policy's `GetS3GenAI` statement, a different document; the
    conclusion is unaffected and was proven behaviourally anyway).

### Raised while sizing the persona set, 2026-08-23

22. **Nothing in this repository notices when AWS revises a managed policy this design leans on — and
    three of them are load-bearing for the SMUS surface.** Measured 2026-08-23 in Sandbox, on the
    project role `datazone_usr_role_…`: `SageMakerStudioProjectUserRolePolicy` **v74** (AWS's last
    revision 2026-08-11), `SageMakerStudioProjectRoleMachineLearningPolicy` **v42** (2026-08-11),
    `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9 (2026-02-12). Those are the documents
    carrying `DomainS3BucketPermissions` (the project's own path inside `awsds-<env>-smus-projects`,
    reached by principal-tag substitution), `DomainS3BucketKmsPermissions` (the project CMK) and the
    `S3AG*` / `ConsumerS3AGPermission` block (S3 Access Grants) — so what a project role, and any
    credential vended from it, may do is **AWS's text, revised on AWS's schedule**.
    `SageMakerStudioProjectProvisioningRolePolicy` **v81** is a fourth:
    `terraform-modules/sagemaker-prereqs/s3.tf`'s "the bucket NAME is free" argument rests on it.
    **This is Lesson 11 one layer past where that lesson was written.** D26 handed role authorship to a
    blueprint, and the policies the blueprint attaches are not even the blueprint's — they are AWS's,
    and they move. Two claims here are written against a version number **in prose** (`s3.tf:15`, and
    Stage 6's `S3Location` row) and nothing re-reads either.
    **Why it is a question and not a task.** AWS emits **no CloudTrail event** when it revises a managed
    policy — the edit happens outside the account, so there is nothing to react to. The only mechanism
    is *pull*: `iam get-policy` returns `DefaultVersionId` and `UpdateDate`, `get-policy-version` the
    document. So any answer has the same shape — a stored (version, document-hash) pair and an
    instrument that **fails when the pair moves**, not because a revision is wrong but to force somebody
    to read the diff. What is undecided: which policies are in scope (the four above, or every
    AWS-managed policy any principal in the estate carries); where the pair is stored (`docs/AWS_STATE.md`
    is the candidate); whether the check belongs in `./aws/studio.py` beside `US-8` or is its own; and
    what a failure means **procedurally**, given the revision is AWS's and cannot be refused.
    **Raised while implementing the laptop→project-storage vending path** (`s3-read-write/`, 2026-08-23):
    that path's authorization *is* the S3 + KMS + Access Grants statements of the first two policies
    above. It is **not created by that change**, which attaches no AWS-managed policy and removes none.
    **AND IT HAPPENED — three days later, 2026-08-26, caught by hand rather than by an instrument, which
    is the argument for the instrument.** Re-reading the same four documents for question 21:
    `SageMakerStudioProjectProvisioningRolePolicy` is at **v82**, not the v81 this question and
    `s3.tf` name; the other three are unmoved (v74, v42, v9). The diff is **two hunks, both widenings,
    neither reaching the claim that rests on it**: `cloudformation:UntagResource` joins
    `CreateStack`/`TagResource` on `stack/DataZone*`, and the `SMAppDelete` statement becomes `SMApp` —
    gaining `sagemaker:CreateApp` and `AddTags`, with the resource widened from four literal app-type
    ARNs (`codeeditor`, `CodeEditor`, `jupyterlab`, `JupyterLab`) to `arn:aws:sagemaker:*:*:app/*` and
    the `AmazonDataZoneProject` tag condition kept. `GetS3GenAI` is byte-identical, so `s3.tf`'s
    argument stands — **this time**. What the occurrence settles is the question's own premise rather
    than its scope: a revision landed inside four days, the estate learned about it only because a
    human happened to read the document for an unrelated reason, and the prose version number in
    `s3.tf:15` was stale for an unknown part of that window. **Scope, storage and procedure are still
    the user's to decide**; the frequency argument is no longer hypothetical.

### Raised by the 2026-08-25 objectives clarification

23. **How the single-egress + proxy topology lands on an estate built with per-account NATs.** The
    clarification (`objectives.md`; D5/D6 revised the same day) states the target: **one internet egress
    point for the whole cloud, one HTTP/HTTPS proxy**, crossed by the client plane (the VPN laptop's
    whole internet) and by every allowed compute connection alike — two filters, the institutional
    proxy's and SageMaker's stricter one. The lab today has the opposite interim shape: a NAT per
    Interactive account (`egress/`, `[E]`), plus the WireGuard host doubling as NAT for the VPN clients
    and the isolated tier. What is undecided, in rough dependency order: **where the proxy lives**
    (which account owns the egress VPC — a new `Network` platform account, Production, or the VPN home —
    and on which axis, given Lesson 10's registry-vs-runtime question); **how traffic reaches it**
    (Transit Gateway is the institutional answer and its standing cost is against D12 — peering is
    O(n²) but N is small here; `institutional-delta.md`'s Networking row already prices this direction);
    **what the proxy is** (§4.3a's two shapes — the Squid `CONNECT` proxy is the cheap one, and its two
    catches become design inputs: every tool needs `http_proxy`/`https_proxy`, and the proxy must
    resolve outside the DNS Firewall); **what happens to the per-account NATs and DNS firewalls**
    (they become the interim, or survive as the compute's *second* filter — the clarification says two
    filters, so the per-account layer may be exactly where SageMaker's stricter list keeps living); and
    **which stage builds it** — Stage 11's egress-control leg owns the requirement, but the topology
    change touches Stage 3's slices and the VPN runbook. Owner: the user (it is an architecture choice);
    the design pass that answers it should produce a decision file. Until then, `D5`'s two-plane scope
    and the two-filter model are the recorded target and nothing in the tree builds the proxy.

    **Input added 2026-08-26, and it changes this question's standing from optimisation to repair.** The
    interim shape is not merely inelegant, it is **broken by construction for the client plane**: a
    full-tunnel laptop resolving through an Interactive VPC inherits every interface endpoint's private
    zone, so client-plane names answer with **private** addresses, and the SMUS portal — a **public**
    origin — cannot reach them without the browser's Local Network Access grant (Lesson 43; measured
    outage and repair the same day, `NETWORK.md` §5). The `datazone` removal fixed the one instance that
    could be fixed by removing an endpoint; `sagemaker.studio`, `glue`, `lakeformation` and `athena`
    cannot leave, because they are the compute plane's own perimeter. **So "where the client plane
    resolves" is now a required output of this question, alongside where the proxy lives** — and the two
    are related: an egress/inspection VPC that the client plane resolves through must *not* carry the
    compute plane's interface endpoints, or it reproduces this break at the new address. The three
    shapes worth pricing when it is answered: give the client plane its own resolver (no endpoint zones),
    keep the endpoints but add a Route 53 Resolver **FORWARD** rule for the client-plane names (an
    outbound endpoint is 2 ENIs, ~USD 0.25/h — measured against this estate's whole endpoint bill), or
    accept a managed-browser policy as the control (`institutional-delta.md`'s device-trust row).

24. **Should a SageMaker Unified Studio service role be a Lake Formation data lake administrator?**
    Nobody decided that it should be, and in Sandbox two of them are. Found 2026-08-26, while Stage 16
    planned an unrelated key-policy statement: `awsds-sandbox-smus-manage-access` and
    `awsds-sandbox-smus-provisioning` sit in `DataLakeSettings.DataLakeAdmins` beside
    `InfrastructureAccess`, with `allow_full_table_external_data_access = true` beside them. The service
    put them there when the first project in the account was created (2026-08-22) — Lesson 17, a service
    that sets itself up creates principals nobody chose.

    **Two things make this a question rather than a defect to close.** First, an LF data lake
    administrator can grant itself anything in the LOCAL catalog, and this account's local catalog holds
    the resource links to `raw` and `curated` — so the seats reach the governed lake's shared objects
    through a door D13's model never described. Second, they cannot simply be revoked: the Stage 6
    create path was measured END TO END **after** they existed, so removing them is a change to a path
    this estate's whole SMUS surface stands on, and the measurement would have to be redone.

    **What was done instead, 2026-08-26 (the user's decision): ADOPTION.** `consumer-data-v0.4.0` carries
    both as inputs defaulting to empty and null, `sandbox/data/` declares them, and a plan no longer
    proposes to strip them. That stops Terraform fighting the service; it settles nothing about whether
    the seats should exist.

    **What answering it needs:** a reading of what those two roles actually DO with the seat (the trail,
    over a project's lifecycle — provisioning, manage-access, a subscription), and then either a recorded
    acceptance or a narrower mechanism if AWS offers one. **Where it belongs:** Stage 6, whose act created
    them, not Stage 16, which only made a plan that noticed.

    **Amended the same day - the adoption was replaced and the gate exists.** The user asked whether
    v0.4.0 was pulling into Terraform something SMUS manages, and it was, one step removed: adoption froze
    the list, so a seat the service adds later is deleted by the next apply. `consumer-data-v0.5.0`
    declares one create-time admin and `ignore_changes` over the list (the `catalog.tf` Iceberg shape,
    Lesson 23) - measured: three admins live, one declared, plan `No changes`. And the gap that let this
    go unseen is closed: **`./aws/datalake.py` `DL-13`** reads the list per account - FAIL on the required
    `InfrastructureAccess` seat missing (an account with no administrator sees an empty catalog), FAIL on
    any seat that is neither that nor a SMUS service role, **`note`** on the SMUS seats so this question
    stays visible without failing on a state the user chose to leave standing. First run 2026-08-26:
    producer `pass`, Development `pass`, Sandbox `note` naming both seats. **What remains open is only the
    governance half above** - whether the seats should exist - and its instrument is now the trail reading
    this entry already describes.

### Raised by Stage 6 step 2.4's reading, 2026-08-26

25. **What expires in `awsds-<env>-smus-projects`, and who removes the storage of a project that no
    longer exists?** *(Reweighted the same evening it was raised: D19's 2026-08-26 revision made this
    bucket THE derived zone — `awsds-<env>-derived` and its 30-day shedding are removed — so this is no
    longer a side bucket's hygiene question but the derived zone's own expiry, D19 practice (iii)'s only
    open mechanism. The bucket is Terraform's (`sagemaker-prereqs`), so a lifecycle rule is addable
    without touching the tree SMUS manages.)* The reading that answered verification (xviii) found the bucket has **no expiry on
    current objects** (versioning, a 90-day noncurrent rule and MPU abort are all the house module gives
    it) and that **deleting a project leaves its whole prefix behind** — five project prefixes stood
    against one live project, one orphan carrying a complete `.git` tree and a notebook. Neither is a
    defect in anything: no step ever decided this bucket's lifecycle, because until the same reading it
    was believed to be a service's working area rather than a **designed destination for query results
    over governed data** (the project's own enforced Athena workgroup writes into it —
    `GOVERNANCE.md` §Persistence's third family). What has to be decided, and the reason each is not
    obvious:

    - **The expiry itself.** The derived zone's 30 days cannot simply be copied: that number is written
      against *query results*, and this bucket also holds a project's working files and the `shared/`
      folder mounted in JupyterLab — data a person expects to find next week. An expiry short enough to
      bound accumulation and long enough not to eat live work is a different number, and it may have to
      be **per scope** (`dev/sys/athena/` is a result location; `shared/` is not).
    - **Who reaps an orphan.** A prefix whose project is gone is invisible to any rule written from the
      live project list, so an expiry is the only mechanism that reaches it — unless a deletion hook is
      added, which nothing in SMUS offers and D11's `make down` does not cover (it stops apps; it has
      never touched project storage). If the answer is "the expiry alone", say so, because it means an
      orphan survives for exactly that long with no principal accountable for it.
    - **Whether the project workgroup's output location is ours to re-point.** If it is, the result half
      could move into the derived zone and inherit its 30 days, and the question shrinks to the working
      files. It is blueprint-created, so this is verification (vi)'s reconciliation question one resource
      over — a reading, not a preference.

    **Owner:** the user for the numbers, Stage 6 for the proposal (it is that stage's act that created
    the destination). **Instruments:** the S3 reading above, and Stage 11's data-event trail once the
    bucket joins its monitored map — where a real access pattern would say which scopes are actually
    re-read and which only accumulate. **Related:** the `scratch` prefix reasoning in
    [D19](decisions/D19-derived-zone.md), and Stage 16's `awsds-sandbox-lake`, the *other* store this
    estate deliberately lets persist — there the persistence is the point, here it is unexamined.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
