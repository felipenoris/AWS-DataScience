# History

How the plan and the environment got here. Two records, deliberately separate:

- **[`LOG.md`](../LOG.md)** — manual actions the user performed in AWS. Written by the user, **never** by Claude.
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
  of `CLAUDE.md`, `README.md` and `REFERENCES.md` — PR #1, merged. The plan was then written and revised
  repeatedly before any AWS resource existed, and finally **split out of two large files** into
  `GENERAL_PLAN.md` (principles, account map, both indexes) and `plan/` (one file per stage, one per
  decision, plus the reference sections). The intermediate revisions are deliberately not recorded: with
  nothing provisioned they describe how the document changed, not how the environment did, and everything
  that survived them is in the plan itself — `plan/decisions/` for the choices and their reasoning,
  `plan/lessons.md` for what would otherwise be relearned, `plan/institutional-delta.md` for the
  lab-versus-institution delta.

  Two things from that period are worth carrying forward, because they are conventions a future reader
  would otherwise have to reverse-engineer:

  - **Identifiers are stable, section numbers are not.** `§4.4 row N` became **`INT-nn`**, because a table
    row renumbers silently when a row is inserted. Every stage file declares the decisions it **consumes**,
    so the reading list for a stage is closed rather than exploratory.
  - **`scripts/check-plan-refs.sh` is the guard.** It fails on a broken relative link, an unknown
    `D`/`INT` identifier, a stale `§`/`row` reference, a pointer into `GENERAL_PLAN.md` for content that
    now lives in `plan/`, or either core file growing past 20 KB.

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
  not go stale, the monthly floor recomputed from the measured rates in `PRICING.md`, Stage 1b's internal
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
  silently. Both steps were rewritten; `ACCOUNTS_AND_USERS.md` gained an "Identities this project did not
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
  `ACCOUNTS_AND_USERS.md` now records that Control Tower's *empty* groups are pre-wired ceilings, one
  membership edit away from an organization-wide grant.

  **A fourth pass, later the same day, withdrew the retirement — `D34`.** Two things arrived together: an
  older AWS account turned out to be attached to the organization, which put the account count against a
  quota of 10 and raised the question of which account could be deferred (answer: `Staging`, whose first
  hard dependency is Stage 8, and which D20 already keeps unpeered from everything); and, following that,
  the observation that **the account list is not static at all** — somebody will eventually want another
  sandbox. That falsified the premise both `D33` and the AFT row in `plan/institutional-delta.md` rested on:
  *"vending is a finite job"*. `D33`'s own second revision trigger had anticipated it, and it fired. `D34`
  keeps `AWS Control Tower Admin` **enabled permanently** as the owner of Control Tower administration —
  OUs, vending, enrolment, landing-zone updates, console only — because the narrow replacement
  (`AWSAccountFactory` through Service Catalog) vends into existing OUs but cannot reach the Control Tower
  console where OUs are created. The cost is stated rather than retired: MFA, Object Lock in **compliance**
  mode and the group-membership alarm stop being cover for a two-week window and become the whole control
  set, and the absence of any approval in front of a vend goes into `plan/institutional-delta.md` as its own
  row. Three side effects: the "vend `Staging` before disabling the only identity that can vend" ordering
  trap disappeared with the retirement; the AFT rejection was re-argued from measured cost instead of
  rarity (Lesson 7, applied to frequency rather than price); and the Terraform question underneath it all —
  *does console vending break state?* — produced the rule now in `plan/conventions.md`: **nothing declares
  the Organization, so nothing drifts, but a console-created OU or account is *invisible* to code written
  as a list, with `plan` reporting "No changes" either way — so the floor is discovered (`for_each` over the
  Organizations data sources) and the grants are enumerated.**

- **2026-08-09 — consistency pass over the whole repository, after D30-D35.** No decision changed and
  nothing provisioned had to change; what it found is the *shape* of what a run of four decisions in two
  days leaves behind, which is worth remembering because it will recur:

  - **A decision's consequences reached the stage bodies but not the stage headers.** D35's forward
    constraints had been written into Stages 1b, 3, 4 and 6, and `D35` was in none of their `Consumes`
    rows — so the one navigation rule this plan has (*a stage is its file plus the decisions it consumes*)
    would have skipped the decision precisely where it changes the work. Added.
  - **An amendment leaves the amended file self-contradictory.** D33 still asserted the retirement D34
    withdrew ("it holds no duty, signs nothing, and has an end date") in the same section that announces
    the withdrawal, and `REFERENCES.md` still annotated a link as the cleanup path for it.
  - **A count is a premise in disguise.** D32's "the same address on all *N* vended accounts" spelled the
    number out, in six files, and was tripping `check-plan-refs.sh`'s own account-count rule. The stale part
    was not the arithmetic — it was that a fixed number *is* the frequency premise D34 retired. Made generic
    in D32, D33, Stage 1a, `lessons.md`, `CLAUDE.md` and the decisions index; the script passes again.
  - **D35 reached the prose and not the files that become code**, which is the expensive half: the
    authoritative layout in `plan/conventions.md` still described one `sandbox/` slice, one
    `awsds-infra-sandbox` profile, one `ENV=sandbox`, and two *closed enumerations* — the `<env>` token list
    and the tag policy's allowed values — that would reject a per-unit token as an `AccessDenied` on the
    first apply in a newly vended account. `cost-model.md` had no per-unit term although D35 pointed at it
    by name; `ACCOUNTS_AND_USERS.md` and `architecture.md` had no cardinality at all; `integrations.md`
    still associated the domain with two accounts where Stage 6 already said N+1. All loosened, with the
    concrete scheme deliberately left to Stage 14 rather than guessed at now.
  - **The quota arithmetic lived in the wrong file.** That an older account already occupies a slot — so the
    plan's set is eleven against a cap of ten — and that `Staging` is therefore the account to defer were
    recorded in this file and in `CLAUDE.md`, and not in the Stage 1a pre-flight, which is what someone
    executing actually reads. Moved there.

  **One item was found and deliberately not fixed**, because it is a decision rather than a correction: the
  organization now contains an OU named `Sandboxes`, nested under `Interactive` (`LOG.md`, 2026-08-09), and
  no plan document knows about it — not D23, not D35, not the account tables. It also makes the
  organization's OU nesting depth **2**, which is exactly the parameter Stage 2's `for_each`-over-the-data-sources
  rule (D34) depends on and currently lists as "to verify".

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
