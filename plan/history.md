# History

How the plan and the environment got here. Two records, deliberately separate:

- **[`LOG.md`](../LOG.md)** — manual actions the user performed in AWS. Written by the user, **never** by Claude.
- **this file** — how the plan changed, and what each project step did.

Nothing here changes a future decision; do not read it to execute a stage.

**Why this file is short.** A revision earns a row here only once it changes something that has already
been *provisioned*. Nothing has been provisioned yet — the whole plan predates the first AWS resource — so
everything below is a single entry about a document. The moment Stage 1a runs, this file starts growing
for real, and the entries above that line stay as short as they are now.

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

---

*Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md) · Decisions: [plan/decisions/INDEX.md](decisions/INDEX.md) · Stages: [plan/stages/INDEX.md](stages/INDEX.md)*
