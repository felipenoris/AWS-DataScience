# History

How the plan and the environment got here. Two records, deliberately separate:

- **[`LOG.md`](../LOG.md)** — manual actions the user performed in AWS. Written by the user, **never** by Claude.
- **this file** — how the plan changed, and what each project step did.

Nothing here changes a future decision; do not read it to execute a stage.

---

## Baseline (state at the time the plan was written: 2026-08-07)

A snapshot, kept for the record. **The current state is `CLAUDE.md` §"Current position"**, which is
the only place that is maintained.

**Repository**

- Documentation only: `CLAUDE.md`, `LOG.md`, `README.md`, `REFERENCES.md`, `GENERAL_PLAN.md`, `LICENSE`.
- `ACCOUNTS_AND_USERS.md` (committed) describes the accounts and SSO users; `secrets/` (git-ignored)
  holds `emails.md` with the e-mail address behind each of them.
- `terraform/` exists but is empty. It must be replaced by `terraform-live/` and `terraform-modules/`
  (the layout defined in `CLAUDE.md`).
- Git remote is GitHub (`felipenoris/AWS-DataScience`). **This infrastructure repository stays on GitHub**;
  GitLab (Stage 7) hosts the *application* repositories and the CI/CD pipelines.

**Local tooling** (verified)

- `aws-cli` 2.36.18, `terraform` 1.15.8, `uv` installed.
- `~/.aws/config` has only a `[default]` profile with invalid credentials. No SSO profile configured yet.

**AWS**

- Management Account created manually through the AWS console. Nothing else exists.

**Planned accounts** (`ACCOUNTS_AND_USERS.md`, e-mails in `secrets/emails.md`): Management, Sandbox
(experimentation), **Development**, **Staging**, Production, **Data Governance**, Log Archive, Audit,
Identity, **Policy Canary** — **ten accounts**. Nine e-mails were registered before the plan was reviewed;
**`Policy Canary`'s is the one still to add to `secrets/emails.md`** (D29, 2026-08-08). Staging arrived on 2026-08-08 with D20; Development
and Data Governance arrived later the same day with D21/D22, closing the two departures from the AWS
references that the first Staging revision had left open. Every earlier statement that six or seven
accounts "are the complete set" is superseded.
**Planned SSO users** (`ACCOUNTS_AND_USERS.md`): infrastructure (admin), **data scientist** (regular —
renamed from "sandbox user", read-write in Sandbox and Development), **deployment manager** (release
approvals) and **governance manager** (data-access approvals) — one persona until 2026-08-08, split then
because the two approvals sit on the two different axes (`plan/architecture.md` §3).

**Region:** `us-west-2` (decision D1, recorded in `CLAUDE.md`).

---

## Plan revision history

Kept deliberately short: this file, not its history, is the source of truth. A revision only earns a row
here once the environment exists — from Stage 1 onwards, when a change to the plan also means a change to
something already provisioned.

| Date | Change |
|---|---|
| 2026-08-07 → 2026-08-08 | **The plan, written and revised ten times before any AWS resource existed.** It arrived at: stages 0-13; decisions D1-D28, all closed — the ninth revision adopted **SageMaker Unified Studio** (D26), the catalog-maintenance exception for Glue Crawlers (D27) and the production workflow contract (D28), and the tenth placed the domain by asking which *axis* it sits on — **`Data Management` was renamed `Data Governance`** and took the domain, no tenth account being needed, and the single `Manager` persona split into **Deployment Manager** and **Governance Manager** so that releasing a job and granting it data are two signatures; the nine-account, four-OU layout; `plan/architecture.md` §4.2 the data perimeter; `plan/architecture.md` §4.3 the two egress designs; `plan/integrations.md` the cross-account integrations — fourteen at that point, sixteen after the review below; `plan/cost-model.md`/`plan/conventions.md` §5.1 the cost model and the `[P]`/`[D]`/`[E]` operating model; `plan/open-questions.md` the open questions; `plan/institutional-delta.md` the lab-versus-institution delta. `GLOSSARY.md` and `PRICING.md` were created along the way, the latter measured from the AWS Price List bulk API rather than estimated. The individual revisions are not recorded here: everything that survived them is in the sections above, and with nothing provisioned they described only how the document changed, not how the environment did. The reasoning that would otherwise be lost is kept in the D-columns of `plan/decisions/` (each decision carries its own rationale and its revision triggers) and in the "Lessons carried forward" list in `CLAUDE.md`. **A final pre-Stage-1 review closed the document out on 2026-08-08** — Stage 1b renumbered, the RAM enablement attributed to the right account with a verification that can fail, OU creation routed through Control Tower, INT-15-16 added as *control* risks, the perimeter's AWS-owned-bucket carve-out written down, Stage 6's dependency on Stages 7-8 resolved with a hand-built first image, and three choices left open as `plan/open-questions.md` items 10-12. It earns no row of its own for the same reason none of the ten revisions do: nothing was provisioned. |

---

## Project history

- **2026-08-07 / 2026-08-08 — Stage 0 (complete), and the plan.** Management account created manually by
  the user through the console; `aws` CLI 2.36, `terraform` 1.15 and `uv` installed locally;
  `~/.aws/config` still has no SSO profile. English review of `CLAUDE.md`, `README.md` and
  `REFERENCES.md` — PR #1, merged. `GENERAL_PLAN.md` was then written and revised ten times before any
  AWS resource existed, arriving at the nine-account / four-OU layout and D1-D28, all closed —
  since extended to ten accounts and five OUs by D29 (see the review entry below) — the ninth
  revision adopting SageMaker Unified Studio (D26), the catalog-maintenance carve-out (D27) and the
  production workflow contract (D28), and the tenth placing the domain on the ownership axis — which
  renamed `Data Management` to **`Data Governance`**, needed no new account, and split the `Manager`
  persona into **Deployment Manager** and **Governance Manager**;
  `GLOSSARY.md` and `PRICING.md` were created along the way. The individual revisions are deliberately
  not recorded: with nothing provisioned they describe how the document changed, not how the environment
  did, and everything that survived them is in `GENERAL_PLAN.md` — `plan/decisions/` for the decisions and their
  rationale, `plan/institutional-delta.md` for the lab-versus-institution delta.

- **2026-08-08 — pre-Stage-1 review of the whole plan, corrections applied.** The last thing done before
  provisioning anything. It found four classes of problem and all but the decisions are fixed: (i) **Stage 1
  ordering and correctness** — SSO profiles used five steps before they were created, `ram` org sharing
  attributed to the wrong account with a verification command that cannot fail, OUs created outside Control
  Tower's registration, the Control Tower wizard's default `Sandbox` OU name colliding with the Sandbox
  *account*; (ii) **two control risks promoted to INT-15 and INT-16** — whether D13 survives roles that
  blueprints now author, and whether the VPN restriction reaches the Unified Studio portal at all; (iii)
  **dependency errors between stages** — Stage 6 needed the `dev-env` image (Stage 8) and GitLab (Stage 7),
  resolved by building the first image **by hand** and deferring the `git clone` deliverable to Stage 7;
  the cross-account private-hosted-zone association that makes "reach GitLab by name" work was missing
  entirely; (iv) **the perimeter denying AWS's own S3 buckets**, which breaks `dnf update` — a stated
  `CLAUDE.md` requirement. Also: the GitLab CE edition limit reaches the *approval gate*, not just SAML
  group sync, so D20's central control needs an edition check before Stage 8 is written.
  **The first of the three remaining choices was then closed as D29** (`plan/open-questions.md` item 10): a tenth account,
  **`Policy Canary`**, alone in a fifth OU, **`Policy Test`**. The reasoning matters more than the outcome
  — the obvious fix (an empty test OU) tests *nothing*, because an SCP is only evaluated when a principal
  makes a call; the OU is worth having only because a disposable account sits inside it, and the test
  principal has to be an **administrator** or the battery measures the identity policy instead of the
  ceiling. Stage 1b step 7 now carries the procedure, in both directions: what must still succeed *and*
  what must now fail. **`plan/open-questions.md` item 11 then closed in two parts.** The break-glass credential is the
  **Management account root** (D16) — which *removes* principle 2's exception rather than documenting one,
  merges Stage 1a steps 1 and 5, and composes with centralized root access management: nine member roots
  disappear, one remains, and it is the break-glass. Its cost is that root cannot be scoped, so every
  compensating control is detective. **MFA type is deliberately unspecified** — a recorded decision, not an
  omission. And the second part went against the recommendation: the **SCP recovery principal was adopted
  (D30)** by the user's choice — `awsds-scp-recovery`, exempt from every custom deny. Built with the
  mitigations that decide whether it is a control or a hole, and it forced the SCPs into code
  (`terraform-live/identity/`), which no earlier version of the plan owned. **`plan/open-questions.md` item 12 then closed as
  D31:** the deployment manager loses blanket `ReadOnlyAccess` for a bespoke `DeploymentManagerAccess`
  (diagnosis, not reading — `athena:*` and `kms:Decrypt` denied explicitly), and the **derived zone gets its
  own KMS CMK** whose key policy is where "who may read materialised `restricted` data" lives. That second
  half closes a D19 gap unrelated to the persona and is the part that outlives it: a permission set
  enumerates, a key policy is default-deny. **All three review decisions are now settled and `plan/open-questions.md` holds only
  things to find out by doing.**

- **2026-08-08 — the plan was split out of two large files, and nothing in it changed.** `GENERAL_PLAN.md`
  (278 KB) and `CLAUDE.md` (32 KB) had to be read in full to do anything, which cost roughly 70k and 8k
  tokens respectively — the second one on *every* session, whatever the task. The content was moved
  verbatim into `plan/`: one file per decision (`D1`-`D31`) behind a one-line-per-decision index, one file
  per stage (with Stage 1 finally split into the `1a`/`1b` files the text already described), and the
  reference sections — architecture, conventions, integrations, cost model, open questions, lessons,
  institutional delta, history — each in its own file. `GENERAL_PLAN.md` became the core: principles, the
  account map, and the two indexes. `CLAUDE.md` kept every working rule and every lesson *title*, and lost
  only its narrative: `Current position` went from 9 KB of restated plan to a status block, and `History`
  moved here. Two identifier changes make the split hold: `§4.4 row N` became **`INT-nn`**, because a table
  row number renumbers silently when a row is inserted, and every stage file now declares the decisions it
  **consumes**, so the reading list for a stage is closed rather than exploratory. `scripts/check-plan-refs.sh`
  fails the build on a broken link, an unknown `D`/`INT` id, or either core file growing past 20 KB.
  **This entry breaks this file's own rule** — nothing was provisioned, so a document change earns no row —
  and it is here anyway because it changes where a future reader has to look for everything else.


---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
