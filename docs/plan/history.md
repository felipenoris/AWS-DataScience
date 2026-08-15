# History

How the plan and the environment got here. Two records, deliberately separate:

- **[`docs/log/`](../log/INDEX.md)** — manual actions the user performed in AWS, one file per stage. Written by
  the user, **never** by Claude.
- **this file** — how the plan changed, and what each project step did.

Nothing here changes a future decision; do not read it to execute a stage.

**Why this file is short.** A revision earns a row here only once it changes something that has already
been *provisioned*. Everything up to and including the pre-Stage-1 review predates the first AWS resource
and is therefore a single entry about a document. **Stage 1a started on 2026-08-08**, and from that entry
onwards the file records how the environment changed, not just the plan.

---

## Project history

- **2026-08-07 / 2026-08-08 — Stage 0 (complete), and the plan.** Management account created manually by
  the user through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally. English review
  of `CLAUDE.md`, `README.md` and `docs/REFERENCES.md` — PR #1, merged. The plan was then written and revised
  repeatedly before any AWS resource existed, and finally **split out of two large files** into
  `docs/GENERAL_PLAN.md` (principles, account map, both indexes) and `docs/plan/` (one file per stage, one per
  decision, plus the reference sections). The intermediate revisions are deliberately not recorded: with
  nothing provisioned they describe how the document changed, not how the environment did, and everything
  that survived them is in the plan itself — `docs/plan/decisions/` for the choices and their reasoning,
  `docs/plan/lessons.md` for what would otherwise be relearned, `docs/plan/institutional-delta.md` for the
  lab-versus-institution delta.

  Two things from that period are worth carrying forward, because they are conventions a future reader
  would otherwise have to reverse-engineer:

  - **Identifiers are stable, section numbers are not.** `§4.4 row N` became **`INT-nn`**, because a table
    row renumbers silently when a row is inserted. Every stage file declares the decisions it **consumes**,
    so the reading list for a stage is closed rather than exploratory.
  - **`scripts/check-plan-refs.py` is the guard.** It fails on a broken relative link, an unknown
    `D`/`INT` identifier, a stale `§`/`row` reference, a pointer into `docs/GENERAL_PLAN.md` for content that
    now lives in `docs/plan/`, or either core file growing past 20 KB.

- **2026-08-08 — final pre-Stage-1 review, corrections applied.** The last pass before provisioning
  anything. What it changed is in the plan; what is worth remembering is the *shape* of what it found,
  since the same classes recur:

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
  were actually being created, and it came from execution rather than review. Account Factory's form asks
  for an `SSOUserEmail` that **grants administrative access to the account being vended**; Stage 1a step 4
  named only the account e-mail, so the field had no planned value. `D32` gives it one — the infrastructure
  user, the same on all seven vended accounts — and the consequences reach 1b: the infrastructure user now
  pre-exists (1b step 2 creates four users, not five), `Policy Canary`'s administrator arrives at vend time
  (1b step 3 confirms rather than assigns), and every vended account is left holding a *direct*
  administrator assignment whose removal is deliberately deferred and conditional on a verification.
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

  **A follow-up question the same day found the expensive half.** Asked whether the new user should be
  catalogued and whether its e-mail should be changed, the review turned up its **group memberships** —
  `AWSAccountFactory` and `AWSControlTowerAdmins` — and with them the fact that **the whole Identity Center
  directory was already populated** by the landing zone: Control Tower's groups, its permission sets, one of
  them named `AWSAdministratorAccess`. Stage 1b steps 2 and 3 had been written against an empty directory
  and would have created `AdministratorAccess` four characters from it, where a wrong assignment works
  silently. Both steps were rewritten; `docs/ORGANIZATION.md` gained an "Identities this project did not
  create" section, because an undocumented administrator cannot be told apart from an unauthorised one; and
  `D33` settled the e-mail question as **disable, do not rename** — renaming keeps a standing Management
  administrator alive to fix a mail-routing problem, and Control Tower may re-create the original anyway.

  **A third pass, from the access portal, resized the finding.** Reading the user's actual account list
  showed the reach is not "administrator of Management": `AWSControlTowerAdmins` carries
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

  **A fourth pass, later the same day, withdrew the retirement — `D34`.** Two things arrived together: an
  older AWS account turned out to be attached to the organization, which put the account count against a
  quota of 10 and raised the question of which account could be deferred (answer: `Staging`, whose first
  hard dependency is Stage 8, and which D20 already keeps unpeered from everything); and, following that,
  the observation that **the account list is not static at all** — somebody will eventually want another
  sandbox. That falsified the premise both `D33` and the AFT row in `docs/plan/institutional-delta.md` rested on:
  *"vending is a finite job"*. `D33`'s own second revision trigger had anticipated it, and it fired. `D34`
  keeps `AWS Control Tower Admin` **enabled permanently** as the owner of Control Tower administration —
  OUs, vending, enrolment, landing-zone updates, console only — because the narrow replacement
  (`AWSAccountFactory` through Service Catalog) vends into existing OUs but cannot reach the Control Tower
  console where OUs are created. The cost is stated rather than retired: MFA, Object Lock in **compliance**
  mode and the group-membership alarm stop being cover for a two-week window and become the whole control
  set, and the absence of any approval in front of a vend goes into `docs/plan/institutional-delta.md` as its own
  row. Three side effects: the "vend `Staging` before disabling the only identity that can vend" ordering
  trap disappeared with the retirement; the AFT rejection was re-argued from measured cost instead of
  rarity (Lesson 7, applied to frequency rather than price); and the Terraform question underneath it all —
  *does console vending break state?* — produced the rule now in `docs/plan/conventions.md`: **nothing declares
  the Organization, so nothing drifts, but a console-created OU or account is *invisible* to code written
  as a list, with `plan` reporting "No changes" either way — so the floor is discovered (`for_each` over the
  Organizations data sources) and the grants are enumerated.**

- **2026-08-09 — `D35`, from a question rather than from a failure.** Asked how many of each account would
  exist in five years, the map split in two: everything is **structural** — exactly one, forever — except
  **`Sandbox`, which is one per business unit**. The boundary turned out not to be arbitrary: it is exactly
  `D21`'s graduation boundary, because experimentation is naturally per-unit while engineering is
  institutional. So the chain reads **N Sandboxes → one Development → one Staging → one Production**, and the
  useful consequence is that **the promotion chain is untouched by N** — the multiplication sits entirely
  upstream of the approval gate, which is the cheapest place for it. Automation goes where the multiplication
  is: a new **Stage 14** vends a unit's Sandbox from its name, using rung 2 of `D34`'s ladder. The expensive
  half was not the automation but the **singleton assumptions already written into stages not yet built** —
  one hardcoded Sandbox CIDR, a VPN that lands in "the" Sandbox account, one `data-scientists` group, a domain
  associated with two accounts — each nearly free to loosen while still prose, and each a rebuild afterwards.
  All four were loosened the same day. Per-unit isolation deliberately **ends at the graduation boundary**;
  past it it is Lake Formation's job, and a unit wanting its own Development is the revision trigger.

- **2026-08-09 — the OU tree came back different from the plan, twice, and `D23` was revised to match.**
  Both arrived from execution, and both are adopted rather than undone. **`Identity` could not be vended into
  `Security`** — a *foundational* OU in Control Tower's model, which will not take an account it did not
  create. Stage 1a step 4 had flagged exactly this as a thing to verify and had named exactly this fallback,
  so the plan followed the plan; what the plan had *not* carried is the consequence, and it is the whole
  finding: **`Security`'s policy set was never ours** — it is Control Tower's guardrails, inherited by the OU
  being foundational — so a sibling OU inherits none of it, and 1b step 7 gained an `Identity` tier that
  starts by diffing the controls on the two OUs. An OU created from the console carries no policy set until
  code attaches one (`D34`), and this is that rule meeting a real account. And **`Sandboxes` was created
  nested under `Interactive`** to group the per-unit Sandbox accounts. It carries **no policy set of its
  own** — `Interactive`'s inherits down, which is what keeps `D35`'s "a new Sandbox is governed by being
  placed correctly" true. It also required a third clause in `D23`'s test for when an OU earns its
  existence: not only "two or more accounts need the same policy set", but also "it exists to contain a
  *class* of account" — disposable (`Policy Test`) or multiplied (`Sandboxes`). **The one mechanical cost is
  in Stage 2:** OU nesting depth is now **2**, so an enumeration over the root's children misses every
  Sandbox account — silently, with `plan` reporting "No changes", which is the exact failure mode `D34` was
  written about.

- **2026-08-09 — consistency pass over the whole repository, after D30-D35.** No decision changed and
  nothing provisioned had to change; what it found is the *shape* of what a run of four decisions in two
  days leaves behind, which is worth remembering because it will recur:

  - **A decision's consequences reached the stage bodies but not the stage headers.** D35's forward
    constraints had been written into Stages 1b, 3, 4 and 6, and `D35` was in none of their `Consumes`
    rows — so the one navigation rule this plan has (*a stage is its file plus the decisions it consumes*)
    would have skipped the decision precisely where it changes the work. Added.
  - **An amendment leaves the amended file self-contradictory.** D33 still asserted the retirement D34
    withdrew ("it holds no duty, signs nothing, and has an end date") in the same section that announces
    the withdrawal, and `docs/REFERENCES.md` still annotated a link as the cleanup path for it.
  - **A count is a premise in disguise.** D32's "the same address on all *N* vended accounts" spelled the
    number out, in six files, and was tripping `check-plan-refs.py`'s own account-count rule. The stale part
    was not the arithmetic — it was that a fixed number *is* the frequency premise D34 retired. Made generic
    in D32, D33, Stage 1a, `lessons.md`, `CLAUDE.md` and the decisions index; the script passes again.
  - **D35 reached the prose and not the files that become code**, which is the expensive half: the
    authoritative layout in `docs/plan/conventions.md` still described one `sandbox/` slice, one
    `awsds-infra-sandbox` profile, one `ENV=sandbox`, and two *closed enumerations* — the `<env>` token list
    and the tag policy's allowed values — that would reject a per-unit token as an `AccessDenied` on the
    first apply in a newly vended account. `cost-model.md` had no per-unit term although D35 pointed at it
    by name; `docs/ORGANIZATION.md` and `architecture.md` had no cardinality at all; `integrations.md`
    still associated the domain with two accounts where Stage 6 already said N+1. All loosened, with the
    concrete scheme deliberately left to Stage 14 rather than guessed at now.
  - **The quota arithmetic lived in the wrong file.** That an older account already occupies a slot — so the
    plan's set is eleven against a cap of ten — and that `Staging` is therefore the account to defer were
    recorded in this file and in `CLAUDE.md`, and not in the Stage 1a pre-flight, which is what someone
    executing actually reads. Moved there.

  **The two OU findings it raised were settled the same day** and are the entry above this one; the pass
  itself only surfaced them.

  **It also cut `CLAUDE.md`'s `Current position` section from 4.8 KB to ~2 KB and raised its stated budget
  from ~1 KB to ~2 KB.** Most of what was there had stopped being *state*: paragraphs of D32/D33/D34/D35
  reasoning, duplicated from the decision files, and a note about the plan split that belongs here. The
  budget was raised rather than defended because it had been exceeded roughly fivefold with nothing
  noticing — a number that never fires is not a limit, and the honest one for a landing zone at this account
  count is 2 KB. What replaced the number as the actual rule is a test that can be applied while writing:
  **a bullet in that section that explains *why* is a stale copy of something that lives elsewhere.**

- **2026-08-09 — the infrastructure persona was documented, after a question about whether it conflicted with
  the others.** No decision changed and nothing was re-provisioned; D32 is untouched. The question was asked
  from the access portal — *why is `Infrastructure User` attached to all these accounts, and does it overlap
  another persona?* — and the answer needed three things the repository did not contain.

  **The persona had a two-line section and administrator on every vended account.** `docs/ORGANIZATION.md` gave
  each of the other four a paragraph of reach, denials and reasoning, and gave this one "can assume
  infrastructure change roles". The reason is visible in hindsight: the other four were *argued into
  existence* by successive splits of a `Manager user`, so each split wrote its own justification, while this
  one was never contested and so was never described. It now carries what the others carry — what it is (the
  builder: the identity `terraform apply` runs as), why it is attached to those accounts (D32's `SSOUserEmail`,
  the same value on every vend, so the list is not curated), the difference between **today's direct
  `AWSAdministratorAccess` assignment** and the group path Stage 1b builds, and an access table whose
  Management, Log Archive and Audit rows read *nothing*, with the reason.

  **The answer to the question itself: no functional conflict, total permission overlap.** Each persona
  answers a different question — captured in a new index table at the head of the `SSO Users` section, which
  is the shape of the separation and is now stated once instead of being inferable — and nobody else builds.
  But the builder holds administrator where the others' controls live, so it can `lakeformation:GrantPermissions`
  in Data Governance, `ecr:PutImage` in Production, and rewrite the derived zone's key policy that D31 relies
  on. The separation of duties is real among the four and silent about the fifth, which the document now says
  in the place a reader would otherwise conclude the opposite.

  **One contradiction and one imprecision, both found by following that thread.** Stage 1b step 4 created an
  assignment for the infrastructure user *on the Management account*, against README §3, D33, D34 and
  principle 1 — resolved in the direction the other four take (no assignment; the step now says so
  deliberately and keeps the delegated-administrator constraint it also carried). And the sentence "the
  infrastructure user gains no Management-account reach", repeated in three files as the payoff of keeping
  `AWS Control Tower Admin` standing, is true of *standing assignment* only: that user administers `Identity`,
  and an Identity Center delegated administrator can edit `AWSControlTowerAdmins` membership. All three now
  say **standing**, and name Stage 1b step 8's alarm as what covers the gap. That alarm was already load-bearing
  under D34; it has one more reason now.

  **Lesson 18 was added** — *a policy never constrains the principal that authors it* — with the corollary that
  produced this entry: the persona with the shortest section is usually the one with the widest reach.

  **Two loose ends from the same thread were closed in the same pass, and the second was the larger finding.**
  `docs/plan/conventions.md`'s "nothing gets `AdministratorAccess` or `PowerUserAccess`" now names its one
  exception — the `infrastructure` group — and says to read it narrowly, so any *other* principal holding
  administrator reads as a finding rather than as precedent. And **"human infrastructure changes denied",
  carried in six files as a property of the `Interactive` OU's SCP set, turned out to describe no SCP at
  all.** What holds infrastructure change off the data scientist is `DataScientistAccess` plus its
  permissions boundary — an *identity* policy, which is the thing an SCP is supposed to back up rather than
  the thing an SCP is (Lesson 5, found in its purest form: the sentence had been read as a control for the
  whole planning period). The literal SCP is not written, and the reason is now recorded where it will be
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
  user settled it the other way: **both are skipped by decision**, not deferred. This is an entry here rather
  than a plan edit alone because the budget is already provisioned and four files asserted a control that
  does not exist — `docs/plan/cost-model.md` called the pair "the primary control here, not a convenience",
  1a's deliverables said "the budget and Cost Anomaly Detection are live", and D12 described the alerting as
  part of the ceiling. All four now say what is true: **the budget notifies nobody, so USD 50 is a figure
  read from a console.** What carries the exposure instead is the `[E]` teardown discipline of D11 plus
  whoever opens Cost Explorer — which is exactly the shape Lesson 5 warns about, and is recorded as such
  rather than dressed up. The concrete cost of the gap is in `docs/plan/cost-model.md`: a session that leaves
  `egress/` up burns ~USD 4.08/day, and two forgotten days now surface at the end of the month instead of on
  the day. D12 carries the revision trigger — the first month the bill exceeds the projection, or the first
  forgotten `[E]` resource found by reading the bill. The alerts remain free and take minutes to add.

- **2026-08-09 — Stage 1b is split into 1b, 1c and 1d, along the sessions it already described.** The file
  had reached 98 KB and eleven steps under a single `To execute` heading with no sub-headings, so executing
  step 5 meant reading all of it, and its `Consumes` row named twenty-two decisions with no indication of
  which step wanted which — 114 KB of decision files to perform a step that needs one. The split follows the
  stage's own "Sessions" note rather than inventing a boundary: **1b** keeps steps 1-6 and **8** (step 8's
  alarm is the only control over step 1's blast radius, so the two may not be separated), **1c** is step 7
  alone — the one part that is not freely reversible from inside a governed account, and the one that wants
  the Management console open and the detach command written down before it starts — and **1d** is steps 9,
  10 and 11, which are independent of each other and of 1c. **Step numbers were deliberately not
  renumbered**, so every existing `Stage 1b step 7` reference became `Stage 1c step 7` and nothing else
  moved; the same holds for the verification numerals i-ix and the six decision rows, which are now
  distributed across the three files under the landing zone's numbering rather than restarted. Two index
  defects surfaced while doing it and are fixed: **D28 was consumed by step 7.6 and named nowhere**, and
  **D30 — reverted, but load-bearing in 7.1 and step 3 — was in neither the `Consumes` row nor its own
  "referenced by" line**. This is a documentation change with no provisioned counterpart, and it earns an
  entry only because the stage it reorganises has not started: **[`docs/log/`](../log/INDEX.md) needs a file for
  1c and one for 1d, and only the user writes those.**

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [docs/plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [docs/plan/stages/INDEX.md](stages/INDEX.md)*
