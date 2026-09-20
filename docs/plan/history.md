# History

How the plan and the environment got here. Two separate records:

- **[`docs/log/`](../log/INDEX.md)** — manual actions performed in AWS, one file per stage. Written
  cooperatively by the user and Claude, and by Claude only when asked ([`docs/log/INDEX.md`](../log/INDEX.md)).
- **this file** — how the plan changed, and what each project step did.

Nothing here changes a future decision; do not read it to execute a stage.

A revision earns a row here only once it changes something already *provisioned*. Everything up to and
including the pre-Stage-1 review predates the first AWS resource and is a single entry about a document.
**Stage 1a started on 2026-08-08**, and from that entry onwards the file records how the environment
changed, not just the plan.

---

## Project history

- **2026-08-07 / 2026-08-08 — Stage 0 (complete), and the plan.** Management account created manually by
  the user through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally. English review
  of `CLAUDE.md`, `README.md` and `docs/REFERENCES.md` — PR #1, merged. The plan was written and revised
  repeatedly before any AWS resource existed, then split out of two large files into
  `docs/GENERAL_PLAN.md` (principles, account map, both indexes) and `docs/plan/` (one file per stage, one per
  decision, plus the reference sections). The intermediate revisions are not recorded: with nothing
  provisioned they describe how the document changed, and everything that survived them is in the plan
  itself — `docs/plan/decisions/` for the choices and their reasoning, `docs/plan/lessons.md` for what
  would otherwise be relearned, `docs/plan/institutional-delta.md` for the lab-versus-institution delta.

  Two conventions from that period:

  - **Identifiers are stable, section numbers are not.** `§4.4 row N` became **`INT-nn`**, because a table
    row renumbers silently when a row is inserted. Every stage file declares the decisions it **consumes**,
    so the reading list for a stage is closed rather than exploratory.
  - **`scripts/check-plan-refs.py` is the guard.** It fails on a broken relative link, an unknown
    `D`/`INT` identifier, a stale `§`/`row` reference, a pointer into `docs/GENERAL_PLAN.md` for content that
    now lives in `docs/plan/`, or either core file growing past its size budget (20 KB then; raised to
    40 KB on 2026-08-19, when meeting the original ceiling would have cost `CLAUDE.md` either its routing
    table or its lesson keys; `CLAUDE.md`'s raised again to 50 KB on 2026-09-18, the ceilings becoming
    one per core file).

- **2026-08-08 — final pre-Stage-1 review, corrections applied.** The last pass before provisioning
  anything. What it changed is in the plan; the classes it found recur:

  - **Ordering and correctness inside Stage 1** — SSO profiles used before they were created, an
    organization-wide setting attributed to the wrong account, OUs created outside Control Tower's
    registration, and a verification command that returns empty on both success and failure.
  - **Two stated controls that may not exist** — `INT-15` (does D13 survive execution roles that a
    blueprint now authors?) and `INT-16` (does the VPN restriction reach the Unified Studio portal at
    all?). Each can invalidate an objective stated in `CLAUDE.md`, and each is answered by doing.
  - **Dependency errors between stages** — Stage 6 needed artifacts from Stages 7 and 8; resolved by
    building the first image by hand and deferring one deliverable.
  - **A perimeter that denies AWS's own S3 buckets**, which breaks `dnf update` — a stated requirement.
  - **Three choices left open, then closed** as `D29` (the `Policy Canary` account and the `Policy Test`
    OU), `D16` + `D30` (break-glass is the Management root; the SCP recovery role adopted *against* the
    recommendation and **reverted the same day**, once a review found it could not be delivered to the
    account whose repair path justified it) and `D31` (the deployment manager loses blanket
    `ReadOnlyAccess`; the derived zone gets its own CMK).

  Consistency corrections from a second review on the same date — account counts made generic so they do
  not go stale, the monthly floor recomputed from the measured rates in `docs/PRICING.md`, Stage 1b's internal
  step references repaired, and an account-quota pre-flight added to Stage 1a — are in the files
  themselves and change no decision.

- **2026-08-08 — Stage 1a in flight: `D32` added, mid-vend.** The first revision made while AWS resources
  were being created, from execution rather than review. Account Factory's form asks
  for an `SSOUserEmail` that **grants administrative access to the account being vended**; Stage 1a step 4
  named only the account e-mail, so the field had no planned value. `D32` gives it one — the infrastructure
  user, the same on all seven vended accounts — and the consequences reach 1b: the infrastructure user now
  pre-exists (1b step 2 creates four users, not five), `Policy Canary`'s administrator arrives at vend time
  (1b step 3 confirms rather than assigns), and every vended account is left holding a *direct*
  administrator assignment whose removal is deferred and conditional on a verification.
  Generalised as **Lesson 16**. Nothing already provisioned had to change: Control Tower creates Log
  Archive and Audit without asking this question.

- **2026-08-09 — `D33` added, also mid-vend, and also from execution.** Two findings in the same session,
  both about *who* performs a manual step rather than what it does. The landing zone had created an Identity
  Center user, `AWS Control Tower Admin`, holding Management-account administrator under the **root
  account's e-mail** — no wizard field asked for it, and it surfaced only as an unexpected invitation
  e-mail. And the root user, which had executed every step so far, could not open Account Factory at all:
  documented behaviour (Service Catalog portfolio access; root is not a principal that can hold it), so
  Stage 1a step 4 named an action nobody had an identity for. `D33` settles both — vending runs from the
  access portal as that user, which is treated as a bootstrap credential with MFA and is disabled in 1b once
  the infrastructure user's group path is proven — and leaves one edge open on purpose: who administers
  Control Tower after 1a. Generalised as **Lesson 17**. Nothing already vended had to change; the
  `Development` account was created correctly under `D32`.

  A follow-up question the same day found the expensive half. Asked whether the new user should be
  catalogued and whether its e-mail should be changed, the review turned up its **group memberships** —
  `AWSAccountFactory` and `AWSControlTowerAdmins` — and with them the fact that **the whole Identity Center
  directory was already populated** by the landing zone: Control Tower's groups, its permission sets, one of
  them named `AWSAdministratorAccess`. Stage 1b steps 2 and 3 had been written against an empty directory
  and would have created `AdministratorAccess` four characters from it, where a wrong assignment works
  silently. Both steps were rewritten; `docs/ORGANIZATION.md` gained an "Identities this project did not
  create" section, because an undocumented administrator cannot be told apart from an unauthorised one; and
  `D33` settled the e-mail question as **disable, do not rename** — renaming keeps a standing Management
  administrator alive to fix a mail-routing problem, and Control Tower may re-create the original anyway.

  A third pass, from the access portal, resized the finding. Reading the user's account list showed the
  reach is not "administrator of Management": `AWSControlTowerAdmins` carries
  `AWSAdministratorAccess` on **Management, Log Archive and Audit**, plus `AWSOrganizationsFullAccess` on
  every member account — all of it group-derived, no direct assignments. So the bootstrap administrator can
  delete the organization CloudTrail record of its own use, including the trail `D16`'s break-glass alarm
  reads, and the group is atomic so the reach cannot be trimmed while Stage 1a still runs on it. `D33` was
  corrected: MFA becomes mandatory rather than advisable, the window is closed on schedule, and the narrow
  replacement is `AWSAccountFactory` alone — which vends through the **Service Catalog** console, the
  Control Tower console being documented as reachable only by `AWSControlTowerAdmins` members. Two knock-on
  edits: 1b step 7's "deny leaving the organization" stopped being hygiene, because
  `AWSOrganizationsFullAccess` gives a member account a real `organizations:LeaveOrganization` path; and
  `docs/ORGANIZATION.md` now records that Control Tower's *empty* groups are pre-wired ceilings, one
  membership edit away from an organization-wide grant.

  A fourth pass the same day withdrew the retirement (`D34`). Two things arrived together: an
  older AWS account turned out to be attached to the organization, which put the account count against a
  quota of 10 and raised the question of which account could be deferred (answer: `Staging`, whose first
  hard dependency is Stage 8, and which D20 already keeps unpeered from everything); and, following that,
  the observation that **the account list is not static** — somebody will eventually want another
  sandbox. That falsified the premise both `D33` and the AFT row in `docs/plan/institutional-delta.md` rested on:
  *"vending is a finite job"*. `D33`'s own second revision trigger had anticipated it, and it fired. `D34`
  keeps `AWS Control Tower Admin` **enabled permanently** as the owner of Control Tower administration —
  OUs, vending, enrolment, landing-zone updates, console only — because the narrow replacement
  (`AWSAccountFactory` through Service Catalog) vends into existing OUs but cannot reach the Control Tower
  console where OUs are created. The cost: MFA, Object Lock in **compliance** mode and the group-membership
  alarm stop being cover for a two-week window and become the whole control set, and the absence of any
  approval in front of a vend goes into `docs/plan/institutional-delta.md` as its own row. Three side
  effects: the "vend `Staging` before disabling the only identity that can vend" ordering trap disappeared
  with the retirement; the AFT rejection was re-argued from measured cost instead of rarity (Lesson 7,
  applied to frequency rather than price); and the Terraform question underneath it — *does console vending
  break state?* — produced the rule now in `docs/plan/conventions.md`: nothing declares the Organization,
  so nothing drifts, but a console-created OU or account is *invisible* to code written as a list, with
  `plan` reporting "No changes" either way, so the floor is discovered (`for_each` over the Organizations
  data sources) and the grants are enumerated.

- **2026-08-09 — `D35`, from a question rather than from a failure.** Asked how many of each account would
  exist in five years, the map split in two: everything is **structural** — exactly one, forever — except
  **`Sandbox`, which is one per business unit**. That boundary is `D21`'s graduation boundary, because
  experimentation is per-unit while engineering is institutional. The chain reads **N Sandboxes → one
  Development → one Staging → one Production**, so **the promotion chain is untouched by N**: the
  multiplication sits upstream of the approval gate, the cheapest place for it. Automation goes where the
  multiplication is: a new **Stage 14** vends a unit's Sandbox from its name, using rung 2 of `D34`'s
  ladder. The expensive half was the **singleton assumptions already written into stages not yet built** —
  one hardcoded Sandbox CIDR, a VPN that lands in "the" Sandbox account, one `data-scientists` group, a domain
  associated with two accounts — each nearly free to loosen while still prose, and each a rebuild afterwards.
  All four were loosened the same day. Per-unit isolation **ends at the graduation boundary**; past it it
  is Lake Formation's job, and a unit wanting its own Development is the revision trigger.

- **2026-08-09 — the OU tree came back different from the plan, twice, and `D23` was revised to match.**
  Both arrived from execution, and both are adopted rather than undone. **`Identity` could not be vended into
  `Security`** — a *foundational* OU in Control Tower's model, which will not take an account it did not
  create. Stage 1a step 4 had flagged this as a thing to verify and had named this fallback, so the plan
  followed the plan. The consequence it had not carried: **`Security`'s policy set was never ours** — it is
  Control Tower's guardrails, inherited by the OU being foundational — so a sibling OU inherits none of it,
  and 1b step 7 gained an `Identity` tier that
  starts by diffing the controls on the two OUs. An OU created from the console carries no policy set until
  code attaches one (`D34`), and this is that rule meeting a real account. And **`Sandboxes` was created
  nested under `Interactive`** to group the per-unit Sandbox accounts. It carries **no policy set of its
  own** — `Interactive`'s inherits down, which is what keeps `D35`'s "a new Sandbox is governed by being
  placed correctly" true. It also required a third clause in `D23`'s test for when an OU earns its
  existence: not only "two or more accounts need the same policy set", but also "it exists to contain a
  *class* of account" — disposable (`Policy Test`) or multiplied (`Sandboxes`). The mechanical cost is in
  Stage 2: OU nesting depth is now **2**, so an enumeration over the root's children misses every
  Sandbox account — silently, with `plan` reporting "No changes", the exact failure mode `D34` was
  written about.

- **2026-08-09 — consistency pass over the whole repository, after D30-D35.** No decision changed and
  nothing provisioned had to change. What a run of four decisions in two days leaves behind:

  - A decision's consequences reached the stage bodies but not the stage headers. D35's forward
    constraints had been written into Stages 1b, 3, 4 and 6, and `D35` was in none of their `Consumes`
    rows — so the one navigation rule this plan has (*a stage is its file plus the decisions it consumes*)
    would have skipped the decision where it changes the work. Added.
  - An amendment leaves the amended file self-contradictory. D33 still asserted the retirement D34
    withdrew ("it holds no duty, signs nothing, and has an end date") in the same section that announces
    the withdrawal, and `docs/REFERENCES.md` still annotated a link as the cleanup path for it.
  - A count is a premise in disguise. D32's "the same address on all *N* vended accounts" spelled the
    number out, in six files, and was tripping `check-plan-refs.py`'s own account-count rule. The stale
    part was the fixed number, which *is* the frequency premise D34 retired. Made generic in D32, D33,
    Stage 1a, `lessons.md`, `CLAUDE.md` and the decisions index; the script passes again.
  - D35 reached the prose and not the files that become code, the expensive half: the authoritative layout
    in `docs/plan/conventions.md` still described one `sandbox/` slice, one `awsds-infra-sandbox` profile,
    one `ENV=sandbox`, and two *closed enumerations* — the `<env>` token list and the tag policy's allowed
    values — that would reject a per-unit token as an `AccessDenied` on the first apply in a newly vended
    account. `cost-model.md` had no per-unit term although D35 pointed at it by name;
    `docs/ORGANIZATION.md` and `architecture.md` had no cardinality at all; `integrations.md` still
    associated the domain with two accounts where Stage 6 already said N+1. All loosened, with the
    concrete scheme left to Stage 14.
  - The quota arithmetic lived in the wrong file. That an older account already occupies a slot — so the
    plan's set is eleven against a cap of ten — and that `Staging` is therefore the account to defer were
    recorded in this file and in `CLAUDE.md`, and not in the Stage 1a pre-flight, which is what someone
    executing reads. Moved there.

  The two OU findings it raised were settled the same day and are the entry above; the pass only surfaced
  them.

  It also cut `CLAUDE.md`'s `Current position` section from 4.8 KB to ~2 KB and raised its stated budget
  from ~1 KB to ~2 KB. Most of what was there had stopped being *state*: paragraphs of D32/D33/D34/D35
  reasoning duplicated from the decision files, and a note about the plan split that belongs here. The
  budget was raised rather than defended because it had been exceeded roughly fivefold with nothing
  noticing; a number that never fires is not a limit, and 2 KB is the honest one for a landing zone at this
  account count. The rule that replaced it: **a bullet in that section that explains *why* is a stale copy
  of something that lives elsewhere**.

- **2026-08-09 — the infrastructure persona was documented, after a question about whether it conflicted with
  the others.** No decision changed and nothing was re-provisioned; D32 is untouched. The question was asked
  from the access portal — *why is `Infrastructure User` attached to all these accounts, and does it overlap
  another persona?* — and the answer needed three things the repository did not contain.

  The persona had a two-line section and administrator on every vended account. `docs/ORGANIZATION.md` gave
  each of the other four a paragraph of reach, denials and reasoning, and gave this one "can assume
  infrastructure change roles". The other four were *argued into existence* by successive splits of a
  `Manager user`, so each split wrote its own justification, while this one was never contested and so was
  never described. It now carries what the others carry — what it is (the builder: the identity
  `terraform apply` runs as), why it is attached to those accounts (D32's `SSOUserEmail`, the same value on
  every vend, so the list is not curated), the difference between **today's direct `AWSAdministratorAccess`
  assignment** and the group path Stage 1b builds, and an access table whose Management, Log Archive and
  Audit rows read *nothing*, with the reason.

  The answer: no functional conflict, total permission overlap. Each persona answers a different question —
  captured in a new index table at the head of the `SSO Users` section — and nobody else builds. But the
  builder holds administrator where the others' controls live, so it can `lakeformation:GrantPermissions`
  in Data Governance, `ecr:PutImage` in Production, and rewrite the derived zone's key policy that D31
  relies on. The separation of duties is real among the four and silent about the fifth, which the document
  now says in the place a reader would otherwise conclude the opposite.

  One contradiction and one imprecision, both found by following that thread. Stage 1b step 4 created an
  assignment for the infrastructure user *on the Management account*, against README §3, D33, D34 and
  principle 1 — resolved in the direction the other four take (no assignment; the step now says so
  deliberately and keeps the delegated-administrator constraint it also carried). And the sentence "the
  infrastructure user gains no Management-account reach", repeated in three files as the payoff of keeping
  `AWS Control Tower Admin` standing, is true of *standing assignment* only: that user administers `Identity`,
  and an Identity Center delegated administrator can edit `AWSControlTowerAdmins` membership. All three now
  say **standing**, and name Stage 1b step 8's alarm as what covers the gap. That alarm was already load-bearing
  under D34; it has one more reason now.

  Lesson 18 was added — *a policy never constrains the principal that authors it* — with the corollary that
  produced this entry: the persona with the shortest section is usually the one with the widest reach.

  Two loose ends from the same thread were closed in the same pass; the second was the larger finding.
  `docs/plan/conventions.md`'s "nothing gets `AdministratorAccess` or `PowerUserAccess`" now names its one
  exception — the `infrastructure` group — and says to read it narrowly, so any *other* principal holding
  administrator reads as a finding rather than as precedent. And "human infrastructure changes denied",
  carried in six files as a property of the `Interactive` OU's SCP set, turned out to describe no SCP at
  all. What holds infrastructure change off the data scientist is `DataScientistAccess` plus its
  permissions boundary — an *identity* policy, the thing an SCP is supposed to back up rather than the
  thing an SCP is (Lesson 5: the sentence had been read as a control for the whole planning period). The
  literal SCP is not written, and the reason is now recorded where it will be
  needed: it would have to exempt the identity that *builds* every VPC, bucket, role and key in those
  accounts, which is the standing builder exemption D30 proposed and had reverted — with a second exemption
  behind it for the DataZone provisioning roles D26's blueprints create, principals that do not exist until
  Stage 6. So `Interactive` is stated as carrying **no set of its own**: interactive compute is allowed there
  because, unlike `Workloads` and `Data`, nothing denies it. Stage 1b step 7 now carries the choice of
  whether to give it one, with the single candidate that would need no exemption named and **not** adopted —
  `sagemaker:CreateNotebookInstance` and `CreatePresignedNotebookInstanceUrl`, the ungoverned interactive
  surface that bypasses both the VPC-only app configuration and the `dev-env` gate. Adopting it is a decision
  for whoever attaches policy against the `Policy Canary` battery, not one to inherit as prose. One knock-on:
  "attach at `Interactive` so `Sandboxes` inherits" is currently an instruction about nothing — a newly
  vended Sandbox is governed on arrival by the organization-root set, whatever the nesting.

- **2026-08-09 — the budget's alerts and Cost Anomaly Detection are skipped, and the USD 50 ceiling stops
  being enforced by anything automatic.** 1a step 2 built the budget and left its 50/80/100% thresholds and
  Cost Anomaly Detection undone; the plan carried them as pending work for Stage 1b to close in passing. The
  user settled it the other way: **both are skipped by decision**, not deferred. It is an entry here
  because the budget is already provisioned and four files asserted a control that does not exist —
  `docs/plan/cost-model.md` called the pair "the primary control here, not a convenience", 1a's
  deliverables said "the budget and Cost Anomaly Detection are live", and D12 described the alerting as
  part of the ceiling. All four now say what is true: **the budget notifies nobody**, so USD 50 is a figure
  read from a console. What carries the exposure instead is the `[E]` teardown discipline of D11 plus
  whoever opens Cost Explorer (Lesson 5). The concrete cost is in `docs/plan/cost-model.md`: a session that
  leaves `egress/` up burns ~USD 4.08/day, and two forgotten days now surface at the end of the month
  instead of on the day. D12 carries the revision trigger — the first month the bill exceeds the projection, or the first
  forgotten `[E]` resource found by reading the bill. The alerts remain free and take minutes to add.

- **2026-08-09 — Stage 1b is split into 1b, 1c and 1d, along the sessions it already described.** The file
  had reached 98 KB and eleven steps under a single `To execute` heading with no sub-headings, so executing
  step 5 meant reading all of it, and its `Consumes` row named twenty-two decisions with no indication of
  which step wanted which — 114 KB of decision files to perform a step that needs one. The split follows the
  stage's own "Sessions" note rather than inventing a boundary: **1b** keeps steps 1-6 and **8** (step 8's
  alarm is the only control over step 1's blast radius, so the two may not be separated), **1c** is step 7
  alone — the one part that is not freely reversible from inside a governed account, and the one that wants
  the Management console open and the detach command written down before it starts — and **1d** is steps 9,
  10 and 11, which are independent of each other and of 1c. Step numbers were not renumbered, so every
  existing `Stage 1b step 7` reference became `Stage 1c step 7` and nothing else moved; the same holds for
  the verification numerals i-ix and the six decision rows, which are now distributed across the three
  files under the landing zone's numbering rather than restarted. Two index defects surfaced while doing it
  and are fixed: **D28 was consumed by step 7.6 and named nowhere**, and **D30** — reverted, but
  load-bearing in 7.1 and step 3 — was in neither the `Consumes` row nor its own "referenced by" line. A
  documentation change with no provisioned counterpart; it earns an entry because the stage it reorganises
  has not started: [`docs/log/`](../log/INDEX.md) needs a file for 1c and one for 1d, and only the user
  writes those.

- **2026-08-16 — Stage 2 step 7 leaves Stage 2 and becomes Stage 3 step 1.1a.** The three modules
  (`s3-bucket`, `iam-role`, `kms-key`) were moved to the *end* of Stage 2 on 2026-08-15, on the finding that
  nothing in the stage consumes one — `bootstrap/` is forbidden a module (step 2.3) and both identity slices
  declare their resources directly. The argument was applied one step short of its conclusion: it does
  not expire when the stage does, and at the end of Stage 2 there is still no caller. The first is Stage 3's
  `foundation/`, which already writes a module of its own (`vpc/`), so the move costs that stage structure
  rather than a new sitting. It also un-blocks an input Stage 2 cannot settle: modules are consumed **by git
  tag** in a **monorepo**, and the host is GitHub today and GitLab from Stage 7 (D8) — choosing the tag
  scheme with no caller in hand is choosing it twice. This entry exists because the re-scope came after
  the stage had provisioned (the state buckets, both identity slices), the class of change this file keeps.

  The re-scope was found by measuring the disk against the stage file. `CLAUDE.md` and `docs/log/INDEX.md`
  both said Stage 2 had nothing left but its status header; `terraform-modules/` held one `README.md`, the
  `Makefile` said in its own header that `up`/`down`/`status` were not written yet (step 8), and no `[E]`
  slice had ever existed, so the Validation had never run. A stage is closed against its own file, never
  against a summary of it.

- **2026-08-17 — the NFS requirement is withdrawn from `objectives.md`, and D24 with it.** A user edit to
  the requirements brief, followed through the plan in the same sitting: Stage 5a pass 5 (steps 10-12) and
  Stage 6 step 7 tombstoned with their numbers retired, `DL-10` inverted into an absence reading, and the
  no-RCP EFS residual — the accepted risk D19 named and Stage 11's threat model was to carry — retired with
  the filesystem itself. This entry exists because one provisioned thing changed shape: the Sandbox
  `egress/` slice, applied and torn down at Stage 3, drops `elasticfilesystem` — the slice as built carried
  12 interface endpoints, the next `make up` builds 11 (0.160/h in `scripts/tfhygiene/layers.py`), so the
  Stage 3 record and the tree now disagree by one endpoint, deliberately and with both sides dated.
  Everything else the withdrawal touched was still prose.

- **2026-08-18 — GuardDuty leaves Stage 4 for a new Stage 15, and Stage 4 closes with the split.** The
  user's direction, hours after pass 4 had been prepared against the current documentation — so the move
  carried a *prepared* step, findings and all: the protection plans arrive ON (all but Runtime
  Monitoring), the switch-off on Audit's own detector collides with `DenyGuardDutyTampering` (now
  Stage 15's decision 1), auto-enable `ALL` never reaches Management, and the `Security` OU's measured
  SNS statements forbid reusing Control Tower's topics. This entry exists because the re-scope came
  after the stage had provisioned (the host, the anchors, the six-set deny — passes 1-3 measured and
  done), and because it is the plan's first deliberate
  overrule of one of its own principles: principle 9 had coupled GuardDuty to the first internet-facing
  resource, and the split breaks that coupling with the trade argued in a new `institutional-delta.md`
  row (an exposed host unwatched through the build-out, against a free-trial window that opens over a
  populated estate). The mechanics of the move: step 10 and its sub-steps became Stage 15 steps 0-6 one
  for one; decisions 3 and 5 and verifications (v) and (ix) travelled with their numbers retired into
  tombstones; `VP-8` left `./aws/vpn.py` for a new `./aws/guardduty.py` (`GD-1`–`GD-3`) with the id
  retired rather than renumbered, and `vpn.py`'s default narrowed to the two profiles its remaining
  subject needs; Stage 11 step 4 now gates on Stage 15 plus a month of billing, and Stage 5a step 13.2's
  Security Hub ingestion is recorded as empty until Stage 15 runs.

- **2026-08-19 — the `security-zone` LF-Tag dimension is withdrawn, one day after it was created: one
  data CMK per account.** The user's revision, taken after working through the mechanics in
  conversation: the dimension had been decided on the premise that a CMK was associated with an LF-Tag,
  and no AWS mechanism makes that association — a tag attaches to catalog objects and gates TBAC
  expressions (none of which ever used `security-zone`); a key is assigned per bucket by Terraform; the
  tag-to-key link was only the shared `zn-lab` spelling in the aliases. This entry exists because
  provisioned things changed: the LF-Tag key and its `ASSOCIATE` grant destroyed, the three database
  assignments narrowed, and the three data CMKs renamed in place (`alias/awsds-<env>-data` — the same
  key objects under new aliases, no re-encryption, the count untouched). What replaced the dimension:
  every data bucket encrypts under its own account's
  data key (`GOVERNANCE.md` §Encryption); D31's dedicated-key read control and the
  measured refusal to share the lake's key across the account line
  (`AllowProductionPickupDecryptViaS3`, unscoped) both survive unchanged, because neither ever rested
  on the tag. `consumer-data` went to v0.2.0 with the rename; `UseLakeZoneKeyViaS3` became
  `UseLakeDataKeyViaS3` in `DataScientistAccess` and `DL-12` reads the new name; Stage 9's future
  Production key is `alias/awsds-prod-data`.

- **2026-08-19 — D21's revision trigger fired and is recorded, not answered.** The trigger was "the
  discriminating data test asked with real grants in place"; Stage 5a passes 3-4c put those grants in
  place, identical for both consumers. The file now records that the test is askable, that today it
  still names nothing, and that the answer waits for pass 4d's first behavioural persona
  queries — nothing was changed about the account or the chain.

- **2026-08-25 — D5 and D6 re-scoped by the user's clarification: two egress planes, one proxy.**
  `objectives.md` gained the requirement in the user's words (client internet through the cloud's
  egress once on the VPN; an institutional HTTP/HTTPS proxy; a single egress point for the whole
  cloud; the compute-vs-client scope of the SageMaker restriction; Microsoft 365 endpoint DLP on the
  institution laptops that alone can hold a VPN peer). Consequences propagated the same sitting:
  D5 now governs the **SageMaker-managed compute only** — (A) a short whitelist versus (B) an empty
  one, both ultimately behind the proxy (two filters); D6's egress-control leg covers both planes;
  `architecture.md` §4.3's 2026-08-24 "hard limit of (B)" was re-scoped (the portal's public-internet
  need is the client plane's — the limit was real, the plane was wrong), and §4.3a's "a requirement
  nothing in objectives.md states" is false as of this date — an HTTP/HTTPS proxy is the stated
  target (its shape and topology are open question 23's, its build Stage 11's). Provisioned things this
  touches: the two Interactive `egress/` slices (their NATs become the recorded *interim* of the
  single-egress target; nothing was applied), and the Sandbox DNS allow-list gained the portal/console
  public-name families in the same sitting (the user's `*` kept first, so removing it
  becomes an experiment instead of a breakage — `EXC-06`'s exit path).

- **2026-08-25 — `datazone` left both Interactive `extra_services` (issue #39).**
  It joined at Stage 6 step 4.2 on 2026-08-21, on a misread of the
  network-isolation page's required table (scoped by that page's own no-public-egress premise, never by
  `VpcOnly` — Lesson 41), and was provisioned on the applies of 2026-08-21/24. What it cost was measured
  on 2026-08-24: its private zone is authoritative for the whole `datazone.<region>.api.aws` subtree, so
  `agent.datazone.<region>.api.aws` — a name the portal's browser needs, per the same page's
  public-internet table — was NXDOMAIN for every client of the VPC resolver, the full-tunnel laptop
  included, and the portal broke *on* the VPN. The removal is **code-only**: `egress/` was down when it
  landed, so nothing was destroyed and the prediction — the app's DataZone calls moving from the endpoint
  to the NAT, `agent.datazone…` resolving again — is tested at the next `make up`, not asserted here.
  Counts and rates moved with it: **12 → 11** interface endpoints per Interactive account, **0.170 →
  0.160/h**, a forgotten day back to **USD 3.84** (`egress.py`'s two copies of that figure had diverged
  again and were converged in the same commit). The general rule now recorded in both slices: no
  endpoint whose private zone shadows a name the *client* plane requires may live in the VPC the client
  resolves through — which is why design B, where this endpoint must come back because there is no NAT,
  has to move the portal off that resolver instead of dropping the endpoint.

- **2026-09-05 — the plan was re-scoped on three inputs from the user, and Stage 6 was split into four.**
  The inputs: AWS refused the account-quota increase, so no account can be vended; the SageMaker
  experience showed no need for a *second* interactive environment; and the client-plane DNS break of
  2026-08-26 showed the network was too thin to carry the estate. What changed. **Stage 6 became 6a
  (the record of what ran), 6b (the rename), 6c (the network) and 6d (the remainder)**, and the stage log
  moved to `log-stage-06a-unified-studio.md` with its index rows. **`Development` becomes `Staging`**: a
  Workload account with the SageMaker runtime only, which is [D21](decisions/D21-development-account.md)'s
  own larger branch of 2026-08-13 taken on experience rather than on the quota — the chain is now
  `Sandbox → Staging → Production` and the user edited `objectives.md` in the same sitting.
  **[D38](decisions/D38-single-egress-hub.md) was written**, closing open question 23: three VPCs in
  Production, an explicit Squid proxy as the estate's single egress, **zero NAT gateways**, no default
  route in any spoke, the WireGuard host re-homed with its Elastic IP *transferred*, and the VPN client
  moved onto a resolver that carries no compute-plane endpoint — which is the structural repair Lessons
  40-43 named and `NETWORK.md` §5 had been carrying as a browser grant. **[D7](decisions/D07-orchestration.md)
  became MWAA Serverless only** (measured USD 0.088 per task-hour against USD 0.29/h for the smallest
  provisioned environment); design B stays as INT-14's terminal fallback and the provisioned rung leaves
  the plan, with an `airflow:CreateEnvironment` deny replacing the prose. **The SageMaker Unified Studio
  CI/CD CLI was read rather than assumed**: it deploys only into existing SMUS *projects*, so it is an
  exporter on the Sandbox side and the pipeline stays the deployer (D26/D28 amended) — the alternative
  would have meant associating deployment targets and carving `datazone:*` out of the `Workloads` SCP.
  **Lesson 44 was written** from the design's central correction: peering shares an address, never a path,
  which is why "one NAT gateway behind the proxy" does not exist and why the isolation rule between
  Interactive and Workloads is enforced for free. Amended in place, each with a dated line: D4, D5, D6,
  D9, D11, D12, D14, D15, D17, D18, D19, D20, D22, D23, D26, D35, D36; D21 superseded; INT-04 closed into
  INT-07, INT-09 re-homed, INT-21 and INT-22 added; open question 23 closed and 24-26 narrowed; Stage 14
  marked blocked on the quota, and Stage 15 deliberately **not** pulled forward (offered and declined).
  **Provisioned things this touches:** nothing yet — every act above is plan and code. What it *schedules*
  against provisioned state is in `AWS_STATE.md` §C: the account's rename and OU move, the destruction of
  both NAT gateways and of `development/{sagemaker,data,egress}/`, the Elastic IP transfer, and the
  re-keying of every VPN-only condition onto the proxy's address.

- **2026-09-05 (same day, second sitting) — the three new stage files were reviewed for consistency,
  ordering and feasibility, rewritten in the action-checklist format, and corrected against the AWS
  documentation.** The format is Stage 4's and Stage 16's: an **Action / Why / Explanation** header per
  step, numbered sub-steps that open with the action, and a `[Claude]` / `[Claude⚡]` / `[user]` marker on
  each. **Ordering:** 6b runs **before** 6c, so 6c writes the peering map and the `awsds-<env>-vpc` peer
  lookup once, against the final name. Six corrections came from reading the vendor pages rather than the
  drafts. (i) Three VPCs in one account is a **hard
  conflict**, not a tagging preference: the `vpc` module's flow-log **log group** and the slice's flow-log
  **IAM role** are account-unique. (ii) `VPN_HOMES` rows resolve `foundation/`, and the hub's Elastic IP
  lives in `networking/` — the row needs a slice field or the re-keying reads an empty state and denies
  every persona. (iii) **MWAA Serverless is not D38's NAT contingency candidate**: AWS documents a
  private-routing shape whose subnets *"must not have a route table to a NAT device … nor an internet
  gateway"*, so the requirements list demanding two NAT gateways belongs to the public shape on the same
  page — **Lesson 41's second instance**, and D7, D38 §1 and Stage 10 were amended. (iv) INT-16's fallback
  (i) **cannot** copy AWS's `DenyUserAccessFromUnauthorizedVPCs`: its `StringNotEquals` on `aws:SourceVpc`
  matches when the key is **absent**, which is every browser-origin call, so it is authored in
  `policies-shared.tf`'s `NotIpAddress` + `StringNotEqualsIfExists` shape. (v) The proxy allow-list is
  **seeded from the network-isolation guide's own portal, IdC and console tables** instead of by trial, and
  the guide's **optional** endpoint table was transcribed in full into `REFERENCES.md` because design B
  turns it into a costed decision. (vi) `NO_PROXY` is generated **per VPC from that VPC's endpoint list**,
  so an endpoint-less AWS service fails as a proxy **403** rather than as a timeout (Lesson 42). Three
  smaller ones: `CIDRS["staging"]` is re-pointed to 10.50.0.0/16 **in 6b, before** the token flip, or the
  folder rename proposes a VPC replacement; the SSO assignment keys are renamed behind `moved {}` blocks
  after the account is; and the allow-list reaches the running proxy through an **SSM State Manager
  association** rather than a host replacement or a new write API. **Two instruments were added to the
  plan**: `./aws/eip-transfer.py` (a read-only preflight for the four documented transfer refusals, which
  prints the two write commands) and `./aws/proxy.py` `PX-1`..`PX-5`; `./aws/dns-allowlist.py` is re-aimed
  at the Squid lists, and `EXC-05`'s redirection-chain failure mode retires with them, because Squid matches
  the requested hostname rather than the resolution chain. **Provisioned things this touches:** none — the
  whole sitting is plan, prose and decisions.

- **2026-09-05 (same day, third sitting) — the review was carried past 6d: Stages 7-15 were checked for
  consistency, ordering and feasibility against the new network, corrected against the vendor
  documentation, and rewritten where they were still in an older format.** The trigger was that every stage
  from 7 on carried a `RE-SCOPED` **Status row** while its **body** still described the old estate — and in
  one case the two contradicted each other outright. **The worst of it was Stage 10**, whose Status row said
  "MWAA Serverless only, design B is not built" while the body still built design B, carried an
  `orchestrator = both` switch, and ran a comparison pass to decide something D7 had already decided. It is
  now one design in **two** accounts (Staging gets its own slice, because a serverless workflow bills nothing
  at rest), applied **Staging first**, with step 4 turned from *the provisioned fallback* into **the fallback
  ladder that records why the provisioned rung left** — replaced by a `DenyProvisionedMwaa` SCP and an `OR-6`
  that flipped from a teardown check to an **absence** check. **Stage 7 was rewritten whole** and carries a
  "What the documentation changed in this plan" table of seven rows, three of which are the same shape and
  became **Lesson 45**: GitLab Omnibus turns **Let's Encrypt on by default** whenever `external_url` is HTTPS
  and retries it on every `reconfigure`; ECR's pull-through cache documents that the **first** pull *"may
  require a route to the internet"* with a public subnet as its own remedy; and MWAA Serverless's workers
  have no internet path at all. The other four: the CA root has a **fourth** surface — GitLab itself, through
  `/etc/gitlab/trusted-certs/` (INT-19 amended); Omnibus takes the proxy **per component** and `no_proxy`
  must carry no port; **`NO_PROXY` wildcards work only as suffixes — no CIDR**, which corrected 6c step 5.6's
  generated list; and a wildcard Pages domain needs **no secondary IP**, with access control in the Free
  tier. **Three corrections landed back in 6c**, all found by reading the code rather than the drafts: there
  are **three** NAT gateways to destroy, not two (`production/egress/` is `egress_mode = "A"`);
  **`vpc-egress` needs the same `name_suffix` as `vpc`**, because its DNS-firewall log group is
  account-unique; and **`VPC-Workloads` had no `[E]` endpoint slice at all** — an endpoint slice reads
  exactly one `foundation/`, so `production/workloads-egress/` was added with its rank. **Stage 9 gained the
  steps its own Status row had announced and never written**: 3.5-3.7 move the off-VPC job deny from the six
  persona sets onto the job-execution **roles** as a permissions boundary, read back with `get-role` because
  `list-roles` omits it, and settle serverless inference — which takes no `VpcConfig` at all — as an SCP deny
  rather than an exception. **Stage 8** lost its vend gate, moved the engineering apply to
  `sandbox/app/app-etl/` behind a `layers.py` refusal that keeps CI out of Sandbox, and became the one
  author of the D28 workflow lint. **Stages 12 and 13 were rewritten from numbered prose into the
  action-checklist format** — 12 because its dashboards still had NAT panels and its budget alarm still
  deferred D12, 13 because the ALB is now the **second enumerated listener** in the estate's only ingress
  tier, which is what first tests 6c's gate. **Stage 14's central question was closed without N**: where the
  VPN terminates is D38's designated hub, one of the three shapes that stage was holding. **D38 gained a
  named NAT-contingency candidate** (the pull-through cache, measured at Stage 7 step 5.2 with two cheaper
  fallbacks ranked ahead of it) and a §6c on where each VPC's endpoints live. **Provisioned things this
  touches:** none — the whole sitting is plan, prose and decisions.

- **2026-09-06 — Stage 6b run end to end in one day, the first stage that removed an
  account.** `Development Account` became `Staging Account` in the `Workloads` OU; its eleven blueprint
  configurations, their eleven grants, the `engineering` project profile, the domain association, the Lake
  Formation share, both re-grants, the project-storage vending policy, `development/sagemaker/`,
  `development/data/` and finally `awsds-dev-tfstate` itself were all removed, and
  `terraform-live/development/` migrated to `staging/` on a new bucket. The account cap forced the question
  and experience answered it: a second interactive environment was a place to stand that nobody stood in,
  so the chain lost a link rather than gaining an account (`Sandbox → Staging → Production`). What was
  preserved: the VPC keeps `10.50.0.0/16` because a CIDR is immutable, both `[P]` gateway-endpoint ids
  survived a folder rename, a state migration and a token flip, and the Production peering kept its `pcx-`
  id through a `for_each` key rename that would otherwise have destroyed it. Three times a step's rule was
  right and its list was short — 4.4's replacements, 4.5's `for_each` keys, 4.6's third assignment — and every
  one was caught by saving the plan to a file and reading it. **Provisioned things this touches:** one
  state bucket and KMS key created, one destroyed; one VPC's security groups, flow log and its IAM role
  replaced; four Production routes re-created; eight state objects moved.

- **2026-09-08 — D38 amended: the build plane stopped being an allow-list.** The user, reading
  `hub-anchors.tf` after the day's proxy measurements, asked why a build host is restricted at all. It is
  not the thing `objectives.md` restricts — that is the SageMaker-managed compute — and the buildbox stands
  in for the CI/CD pipeline whose control is the reviewed Dockerfile, not a hostname list. The list it
  carried was also a treadmill whose own comment called its next revision *"a WHEN rather than an IF"*.
  So `production-foundation` became `open` (everything permitted, everything logged, the three global
  denies untouched), `proxy_allow_shared` and its one CloudFront name were deleted, the plane's mode became
  a property of **which of two maps** it is in rather than a hard-coded string, and `DN-4` was rewritten
  from *"only the client plane is open"* to *"no plane is open except the ones a decision names"*, carrying
  each exception's reason into its pass line. D38 §6 amended in place. The same sitting added `open-vsx.org`
  to the Sandbox plane after a Code Editor space failed to update AWS's own extensions.

- **2026-09-17 — The VPN stopped being a condition of reaching AWS (D39; Stage 6g planned).** The user
  changed the requirement in `objectives.md`: the VPN is a prerequisite only for reaching resources on the
  private network, being on it is not required for SageMaker Unified Studio or the AWS console, and an IAM
  identity is granted only to users who sign in from institution-monitored laptops carrying Microsoft 365
  DLP. Two read-only inventories of the repository found the previous rule enforced by exactly two
  statements, `DenyControlPlaneOffVpn` on the six persona sets and the laptop branch of the lake's
  `DenyOutsideTrustedNetworks`, and carried as a recorded deviation by INT-16, 6c step 6.6 and Stage 11
  steps 3.4 and 5.2. The user chose identity alone for the data plane (the deny deleted rather than
  narrowed, the laptop's drop-box write admitted by principal) and kept both VPN client profiles. D39
  records it and amends D5, D6, D15, D18, D20 and D38; Stage 6g carries the two applies, the instruments
  and the documents that describe the running estate; Stage 11 writes the identity premise as a modelled
  residual in place of the INT-16 re-take; 6d decision due 4 loses its VPN half; open question 17 is
  closed. **Provisioned things this touches:** six inline policies in Identity and five bucket policies in Data Governance, applied the same day (Stage 6g steps 1.3 and 2.3), each re-planning `No changes` and read back from the deployed documents.
- **2026-09-19 — A Redshift Serverless warehouse enters the plan, and Stage 5 becomes Stage 5a.** The user
  asked for a warehouse with two classes of database — governed, written by a Production workload; sandbox,
  written by SageMaker project roles with access granted per database × project. Nothing in the repository
  admitted one: `docs/GOVERNANCE.md` said *"No warehouse is built here"*, `docs/SMUS.md` carried
  `RedshiftServerless` as a **Never** on the strength of D26 and D12, and `docs/PRICING.md` §5 rejected the
  cost family without a measured rate. **Reading the exclusion's own words is what decided how much of it had
  to go**: D12's argument was the RPU bill and D26's was that a *blueprint* puts the object one click from a
  project member, sized by the service. The second argument survives a hand-built warehouse untouched, so
  **[D40](decisions/D40-redshift-warehouse.md) admits one warehouse per account and keeps both Redshift
  blueprints disabled** — reached by a SageMaker **connection to an existing compute resource**, the shape
  Stage 16 used for the sandbox lake. The rate was measured the same day from the Price List bulk API
  (**0.36 USD/RPU-hour**, offer file published 2026-09-11), which makes 4 base RPUs **1.44 USD per query-hour
  and 0.00 at rest** — the estate's most expensive object per unit of time, and the reason the usage limit
  with `breach_action = deactivate` is applied in the same act as the workgroup rather than deferred to
  Stage 12. Three new stage files: **5b** the warehouse and the access model, **6h** the first `sbx_*`
  database and the first connection, and **Stage 9 step 9** the governed class with its federated-catalog
  registration. `INT-24` is new. Four documentation findings shaped the design rather than decorating it: the
  **ratchet** past 4 RPUs never comes back down; the **provider page demands three AZs where the service
  documents two** and the provider validates neither, so the estate's two-AZ plumbing is settled only by an
  apply; **a namespace is not a boundary between its databases** (the cross-database page carries both
  "read-only" and "writable with permissions"), which is why the two classes are in two accounts; and Redshift
  creates its audit log groups at **`Never Expire`** unless they exist first. **Stage 5 was renamed to
  Stage 5a** in the same sitting, file and log file both, with 94 files re-pointed — a bare "Stage 5" would
  have become ambiguous the moment 5b existed. The log's entries were not rewritten (one link target was
  repointed so the reference gate stays green); one entry still names `stage-05-data-foundation.md` in prose,
  and this row is the explanation for it. **Provisioned things this touches: none.** Nothing was applied, and
  `objectives.md` does not yet carry the requirement — that is Stage 5b step 0.0, the user's hand, and the
  stage's one unconditional blocking input. **Corrected the same day, before the branch was merged:** the
  first draft of 5b 0.0 said that file *"says nothing about a warehouse today"*, and it does — *"Use AWS Glue
  Data Catalog with data stored on S3 buckets, using ICEBERG format, as Data Warehouse."* So 0.0 is a
  **revision** of an existing sentence rather than a new bullet, and the fork it hides is whether Redshift is
  a second engine beside the Iceberg lake (what D40 assumes) or a replacement for it (which would re-open
  D13, D22 and the producer path). 0.0 now carries that fork as a table.

- **2026-09-20 — the requirement reaches `objectives.md`, and Claude wrote it.** At the user's request, and
  that is the departure worth recording: [Stage 16](stages/stage-16-sandbox-lake.md) step 0.1 had the *user*
  write the sandbox-lake requirement, and the rule behind it is that a paraphrase written by the implementer
  becomes the specification (Lesson 57). Here the user asked Claude to draft the revision and then answered the
  questions the draft left open, in the same sitting. The user's own sentences from the chat — the two classes
  of database, their writers, the per database × project grain, the minimum capacity — are transcribed; the
  framing sentences around them are Claude's, and those are the ones to re-read if the plan ever drifts from
  the intent. **What the revision settled**, each of which
  [D40](decisions/D40-redshift-warehouse.md) had previously assumed on its own: Redshift is a **second
  possible engine** and the Glue/Iceberg lake stays the warehouse of record, so D13, D22 and the producer path
  extend rather than re-open; a query engine is a choice **per workload, not per estate**, with Athena the
  default, which restates D40's own revision trigger as a requirement; **the governance model does not fork**,
  which makes Stage 9 9.5's federated-catalog registration a requirement rather than a compensation Claude
  chose; and it is **one Redshift environment from a data scientist's point of view, with where its databases
  physically live an implementation matter** — the clause that makes D40's two-account split admissible rather
  than a deviation to be argued. **Then the read side, answered the same day:** *the controls stay the same, it
  is just one more execution environment.* That closed `INT-24` down from three candidate mechanisms to **one**
  — a Lake Formation cross-account share of the federated catalog, read by Athena — and **excluded** Redshift
  data sharing and a cross-account connection by requirement rather than by preference, each being a second
  control path over governed data. It also fixed that a **`gov_*` database gets no project connection**:
  Stage 6h's three layers are a sandbox-class mechanism, and `WH-7` reading *no project tag* on the Production
  namespace is the mechanical half of a rule that now has a sentence behind it. Stage 9's decision due 5 is
  struck; what survives of it is verification (xxi), whether a Lake Formation share of a *federated* catalog
  preserves the TBAC expressions this estate grants by. **Provisioned things this touches: none.**

  **Corrected hours later, on the user's question *why are those two excluded*.** One of the two exclusions was
  wrong and checking it found a defect in the recommendation. **Lake Formation-managed datashares exist**: AWS
  documents that *"you can centrally define and enforce database, table, column, and row-level access
  permissions of Amazon Redshift datashares"* and that *"you can also use tags in Lake Formation to configure
  permissions"*, same-account and cross-account, with the datashare mapped to a **federated database** and only
  *"users with access to both Redshift and Lake Formation"* reaching it. So data sharing is **not** inherently a
  second control path, and `INT-24` carries **two** Lake-Formation-governed shapes rather than one. Only the
  cross-account Data-page connection stays excluded, and it now rests on two independent grounds — the fork, and
  `sqlworkbench:*` on `*`, which `check-iam-wildcards.py` refuses. **The worse finding is about the shape that
  had been recommended**: enabling a federated catalog's *"Access this catalog from Iceberg compatible engines"*
  switch makes **AWS Glue create a managed Amazon Redshift cluster** *"with the compute and storage resources
  required to perform read and write operations"* — a cluster rather than a serverless workgroup, unpriced, read
  **and** write, encrypted by an AWS managed key unless a CMK with extra key policies is supplied, and a direct
  collision with Stage 5b step 3.1's own `DenyRedshiftProvisionedClusters`. Lesson 17's shape. Stage 9 gains
  **9.5a** to settle the collision with a reading, its decision due 5 is restored rather than struck, the
  datashare becomes the recommendation, `docs/PRICING.md` names the cluster as unpriced on purpose, and Stage 5b
  3.1 carries the collision beside the deny so it is not attached in ignorance of what it refuses (Lesson 34).
  **`objectives.md` needed no change**: the requirement was right and the derivation from it was too narrow.

- **2026-09-20 — the sandbox class bypasses the catalog, and `CREATE SCHEMA` turns "freely" into something
  bounded.** The user's third clarification of the day: for a sandbox database the catalog and Lake Formation
  are not in the path, access is granted **directly to the project role** by whatever is simplest, and a project
  member *"creates tables freely inside that project's own schema"*. That confirmed the asymmetry D40 had
  already chosen — `sbx_*` outside Lake Formation, like `awsds-sandbox-lake` — and **changed the shape of
  layer 3** in [Stage 6h](stages/stage-06h-redshift-connection.md). It had been a grant list with
  `ALTER DEFAULT PRIVILEGES` to keep later tables in step; it is now
  `CREATE SCHEMA <name> AUTHORIZATION "<the project's database user>" QUOTA <n> GB` — **ownership rather than a
  list of verbs**, one schema per project, which is the *"simplest to configure"* the requirement asks for and
  needs no bookkeeping as the project works. **A datashare is not the mechanism** and it was named as such: the
  project, the workgroup and the database are in one account and one namespace, so a datashare would add a
  producer/consumer chain to reach something already local; it enters only if a sandbox database ever has to be
  read from another namespace, which nothing asks for. **What the reading added that nobody had:** the schema
  `QUOTA` is what bounds a free hand — a superuser alone may set or change it, Redshift *"checks each
  transaction for quota violations before committing"*, and **the default is `UNLIMITED`**, so a schema created
  without one is unbounded on a store nothing expires. `WH-13` fails on exactly that, `WH-14` reports the
  violations, and 5.2a exercises the refusal — the one control here that bounds a free hand and has never been
  exercised anywhere in this estate. Two smaller facts landed with it: `DELETE` frees no disk until `VACUUM`
  runs, which at 4 base RPUs is the plain command because vacuum boost needs 8, closing a loop with Stage 5b's
  own capacity reading; and a schema name *"can't be `PUBLIC`"*. **Provisioned things this touches: none.**

- **2026-09-20 — a schema is a base, a base can be shared, and two decisions the plan had guessed were answered
  against it.** The user's fourth clarification of the day re-mapped the model rather than adding to it. *"In
  Redshift, a schema is a database"* in the sense the brief uses the word — so the Redshift `database` is only a
  **class container** (`sandbox`, `governed`, one per account, **no name prefixes**), and every grain is **per
  schema × project**. The plan now uses Redshift's own two words and states the mapping once, rather than
  letting one word mean two things (Lesson 32). *"One sandbox schema can be shared with more than one SageMaker
  project"*, which **breaks the ownership shape written hours earlier**: ownership is singular and the relation
  is many-to-many, so layer 3 became a **Redshift database role per schema** (`sbx_<theme>_rw`) granted to each
  admitted project — admitting or removing one is a single `GRANT`/`REVOKE ROLE` against a single object — with
  the schema owned by a non-login role so no project is privileged over the others sharing it. **Sharing brings
  back the cost ownership had removed:** a table belongs to the user that created it, so whether a second project
  may alter or drop the first's tables is unread and `ALTER DEFAULT PRIVILEGES` may be owed **per contributing
  project**; [6h](stages/stage-06h-redshift-connection.md) step 5.2b is the reading, and until it is taken
  *"creates freely"* is specified only as *creates and reads its own*. **The schema's name is thematic** —
  *"chosen when the schema is created, after the theme of the data it will hold"*, with *"no necessary relation
  to any SageMaker project"* — which answered 6h decision 6 against **both** shapes it had offered, and has a
  consequence worth keeping: a schema name carries **no authorization information**, so the schema × project
  relation exists only in `sandbox/warehouse/`'s map and in the `GRANT ROLE` statements, `WH-6` can no longer
  classify anything by name (it reads instead that each account holds one class database and that every schema
  appears in the map), and a schema whose theme has outlived its projects looks exactly like one in use.
  **The quota is 1 TB**, answering decision 7 — and the arithmetic went into `docs/PRICING.md` and this file's
  §5 rather than being left flattering: a filled schema is **24.58 USD a month, 49% of the D12 ceiling**, nothing
  bounds the number of schemas, and 32 at 1 TB reach the 32 TB a 4-RPU workgroup supports, at roughly 786 USD a
  month. So the quota bounds a runaway and not the bill, and what bounds the bill is a new compensating control:
  an alarm on the namespace's `DataStorage` metric. **Provisioned things this touches: none.**

- **2026-09-20 — the compute gets an off switch, and two gaps the user found by asking.** Three questions closed
  the day's design work, and each found something the plan had either assumed or missed. **Can the compute be
  turned off?** The plan had the whole warehouse `[P]` on the strength of *a workgroup serving no query bills no
  compute* — true, and conditional, since D40's own three ways an idle warehouse bills anyway are all real.
  **Redshift Serverless has no pause**: `create-workgroup` and `delete-workgroup` and nothing in between, no
  stop, no suspend, no zero-capacity setting. So the slice became a **pair** — `warehouse/` `[P]` for the
  namespace (the data, the schemas, the database users, the roles and the `GRANT`s, state no plan re-creates,
  §5.1 rule 2) and `warehouse-compute/` `[E]` at rank 54 for the workgroup and its usage limit and nothing else.
  *Powered off* therefore means *does not exist*, the strongest guarantee available, and `make down` is it. What
  `make down` does **not** stop is RMS: a schema filled to its 1 TB quota is 24.58 USD a month with no workgroup
  in the account, which went into `docs/PRICING.md` and the cost model beside the GitLab-volume trade it
  resembles. **The split rests on one unmeasured property** — that the endpoint host survives a delete and
  re-create under the same name, since [6h](stages/stage-06h-redshift-connection.md)'s SMUS connection stores it
  as a field — so 5b gained step **1.9** to read it before anything depends on it, and decision 8 as the
  fallback. This estate has been bitten by the same shape before: the Elastic IP whose *allocation id* did not
  survive a transfer while its address did. **Second gap: the endpoints**, which the user asked about and which
  were foreseen nowhere. `terraform-modules/vpc-egress` admits exactly `bedrock`, `emr` and `mwaa`, enforced by a
  precondition, so a fourth group is a **module change** under Recipe B. The list needed correcting too: the
  load-bearing endpoint is **`redshift-serverless`**, because `GetCredentials` is a serverless call and not a
  `redshift` one; `redshift-data` is needed only if the Data API is the query path; `redshift` probably not, which
  is a CloudTrail reading at 6h 3.5; and the **5439 data path needs no endpoint at all**, the workgroup's ENIs
  being in the VPC, which makes it the security group's job. Written down beside it: the API's private name and
  the workgroup's own host are **different subtrees**, so private DNS does not shadow the workgroup — close
  enough to a collision to deserve the sentence rather than the assumption. **Third: the free trial.** USD 300
  over 90 days, **per account**, eligible only if the account has not used Redshift Serverless yet — so the two
  namespaces carry two independent windows opened four stages apart, which makes building the governed one late
  an accidental win. Its trap is the one that matters: *"billing details for free trial usage does not appear in
  the billing console"*, so every cost verification in 5b would read **0.00 whether the design is right or
  wrong** (Lesson 13). During the trial the instruments are `SYS_SERVERLESS_USAGE` and the console credit
  balance, and the trial's status is recorded beside every cost figure. When the 90 days start is **not defined**
  on AWS's page, so 0.3a reads the credit balance across the first apply rather than paraphrasing *sign-up*.
  `CLAUDE.md`'s Redshift entry went over the 50 KB file budget in the same sitting and was re-trimmed to state
  only, as its own rule requires. **Provisioned things this touches: none.**

**2026-09-20 — Stage 5b executed, and nine of its sentences turned out to be wrong.** The Sandbox warehouse
exists: two slices, the two SCP statements, the persona's reach, the first schema and the ceiling proven to
refuse. What is worth recording as *plan history* rather than as a log entry is how much of the stage the
execution corrected, because the pattern is the one Lesson 54 names — `validate`, `render` and `run` are three
verdicts, and this stage had only ever been *written*.

Decision 2's letter was **impossible**: it asked for the price-performance target set to *Optimizes for cost*
"because AWS does not recommend AI-driven scaling at 4 base RPUs", and *Optimizes for cost* **is** the feature.
Step 2.2's *"one tag per admitted project"* is **not expressible**: `AmazonDataZoneProject` is a tag key, so
layer 1 admits one project and the sharing requirement meets that wall at the second. Step 1.3's schema owner
as *"a non-login role"* is **not a thing Redshift has** — `AUTHORIZATION` takes a user. `WH-13`'s instrument,
`SVV_SCHEMA_QUOTA_STATE`, is **refused to a superuser**, so that check can only ever be a note. And 1.1's
`admin_password_secret_kms_key_id` was **refused by this estate's own D31**, which gives the account root no
cryptographic action on the data key — the plan had assumed one key served both the data and the credential.

None of those were catchable by reading. Two things that were: the stage's own *"re-plan `No changes`"* step
found a perpetual diff the first time it was actually run (six `config_parameter` defaults the service fills),
and the negative control the battery runbook asks for is what made both new denies attributable rather than
assumed. **The cost of learning all of it was 0.0405 USD.**

What the execution added to the plan rather than correcting: a runbook
([`redshift-connection.md`](runbooks/redshift-connection.md)), an instrument (`aws/warehouse.py`), two dated
exceptions (`EXC-12` the orphan secret, `EXC-13` the rotation the `[P]`/`[E]` split stops), nine entries in
`lessons.md`'s platform list, and one new decision — **6h decision 8**, how a second project is admitted,
which did not exist before the tag turned out to be single-valued. **Provisioned things this touches:** the
Sandbox namespace and workgroup, one key-policy statement, two SCP statements, one permission-set document,
one module tag.

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
