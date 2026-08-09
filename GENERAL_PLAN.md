# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`.
**This file is the core: principles, the account map, and the two indexes.** Everything else lives in
[`plan/`](plan/) and is read on demand.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**. This file holds the **route** to get there.
- **Read this file, then read only what the task needs.** Executing a stage means opening one stage file
  plus the decisions its `Consumes` row lists — not the whole plan. `CLAUDE.md` §"What to read, and when"
  is the full mapping.
- Every entry in the `Claude LOG` section of `CLAUDE.md` must reference the stage it belongs to
  (e.g. "Stage 3 - Networking, in progress").
- This plan is expected to change. Whenever a stage is finished or a decision is revisited, update the
  relevant file **in place**. [`plan/history.md`](plan/history.md) records only changes made *after*
  something has been provisioned — a plan edit that predates the resource it describes is just an earlier
  draft, and is not kept.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered, but the
  prerequisites listed inside each stage must hold.

**Where new content goes** — the rule that keeps this file small:

| New content | Goes to |
|---|---|
| A choice, with reasoning and a revision trigger | a new file in [`plan/decisions/`](plan/decisions/INDEX.md) + one row in its INDEX |
| Steps to build something | the stage file in [`plan/stages/`](plan/stages/INDEX.md) |
| A naming, layout, Terraform or IAM rule | [`plan/conventions.md`](plan/conventions.md) |
| A cross-account thing that must be proven | a new `INT-nn` row in [`plan/integrations.md`](plan/integrations.md) |
| A mistake worth not repeating | [`plan/lessons.md`](plan/lessons.md) + its title in `CLAUDE.md` |
| A procedure to follow when something is on fire | a file in [`plan/runbooks/`](plan/runbooks/) |
| What happened | [`plan/history.md`](plan/history.md) — never `LOG.md`, which is the user's |

**Identifiers are stable, section numbers are not.** Reference `D26`, `INT-11`, `Stage 1b step 7`.
The `§` numbers kept inside `plan/` files are historical anchors, not addresses.

---

## The map

| Account | OU | Axis | What it is |
|---|---|---|---|
| Management | (root) | platform | Bootstrap only, console only, never Terraform. Its **root user is the break-glass credential** (D16) |
| Log Archive | Security | platform | Control Tower log sink, S3 Object Lock |
| Audit | Security | platform | Security guardian: GuardDuty, Security Hub, Macie, Access Analyzer |
| Identity | **Identity** | platform | Identity Center **delegated administration** (D10) — as sensitive as Management. Its own OU because Control Tower would not vend it into the foundational `Security` OU (D23, 2026-08-09) |
| Policy Canary | Policy Test | platform | Deliberately empty. The disposable account a candidate SCP is exercised against (D29) |
| Sandbox | Interactive → **Sandboxes** | lifecycle (before the chain) | **Experimentation** — the unit of work is a notebook. VPN terminates here; EFS lives here (D24). One per business unit (D35), grouped in a nested OU that carries no policy set of its own |
| Development | Interactive | lifecycle | **Engineering** — the unit of work is a pipeline. The promotion chain starts here (D21) |
| Data Governance | Data | **ownership** | The governed lake + the Unified Studio domain (D22, D26). No VPC, no user compute, no interactive sign-in |
| Staging | Workloads | lifecycle | Deployment target, written only by the pipeline; sampled or synthetic data (D20) |
| Production | Workloads | lifecycle | Deployment target **plus** the supply chain: GitLab, runners, ECR, CodeArtifact, Model Registry, orchestration (D14) |

Three groups, not one sequence: the **lifecycle** axis (Sandbox before the chain, then
Development → Staging → Production), the **ownership** axis (Data Governance alone), and the **platform**
accounts on neither. *An account off the lifecycle axis is not "a production account"* — Data Governance
and Identity are **high blast radius**, which is a different property.

**And one property that cuts across all three: cardinality (D35).** Every account above is **structural** —
exactly one, forever — **except `Sandbox`, which is one per business unit** (N is 1 today). The chain reads
**N Sandboxes → one Development → one Staging → one Production**, so the cardinality boundary is exactly
D21's graduation boundary: experimentation multiplies, the engineering chain that follows it does not — which
is why the promotion chain is untouched by N. That decides where vending is automated: the structural
accounts keep the console flow (D34), the Sandbox gets [Stage 14](plan/stages/stage-14-sandbox-vending.md).
It also means any stage writing "*the* Sandbox account" is writing a singleton assumption that has to be paid
for later.

Full annotated tree, the two access paths, region portability, the data perimeter and the two egress
designs: [`plan/architecture.md`](plan/architecture.md).

---

## 1. Guiding principles

These come from `CLAUDE.md` and constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in `LOG.md`. Terraform does not manage the Management account.
2. **No IAM Users, and since 2026-08-08 with no exception.** Humans authenticate through IAM Identity
   Center (SSO) and assume roles. Machines (GitLab CI) use **EC2 instance profiles**: a VPN-only GitLab
   cannot serve a JWKS that IAM can fetch, so OIDC federation is not available to any runner in this
   design (Stage 7 step 6, Stage 8 step 4). OIDC remains the target the moment a public issuer surface
   exists, and `plan/institutional-delta.md` records it as the institutional answer. No long-lived access
   keys anywhere. This principle used to carry one
   documented exception for break-glass; **D16 settled that credential as the Management account root,
   which is not an IAM user and holds no access key**, so the exception dissolved instead of being
   justified. A rule with no escape hatch is a rule that gets broken under pressure — the escape hatch
   here simply is not an IAM user.
3. **Everything else is Terraform.** One state per account/environment, no shared state across environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier.
5. **Incremental.** Each stage must leave the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost and,
   where relevant, a cheaper alternative.
7. **Pay nothing while idle** (decision D11). Between sessions, metered resources are destroyed, stateful
   ones are stopped, and anything free at rest is simply left alone. See `plan/conventions.md` §5.1 — every stage must say which
   layer its resources belong to, so this shapes how each stage is designed, not just how it is operated.
8. **The region is a variable, not an assumption** (decision D1). The lab runs in `us-west-2` and stays
   there; keeping the region out of the code is plain Terraform hygiene, not migration work. See `plan/architecture.md` §4.1.
9. **Preventive controls come before detective ones — and the two halves are scheduled by different
   rules.** Detecting an exfiltration you could have made impossible is a worse outcome than preventing it,
   so prevention has precedence. **The preventive half is built in the landing zone** (SCPs, RCPs, endpoint
   policies, the data perimeter of `plan/architecture.md` §4.2): it is free, it is structural, and a
   guardrail written after the thing it guards has already been used is a guardrail that arrives late.
   **The detective half is enabled when there is something to detect**, service by service, each naming
   the stage that turns it on — GuardDuty at Stage 4, with the first internet-facing resource; Security Hub
   at Stage 5, with the first governed data; Macie at Stage 11. Detection is metered, it observes rather
   than prevents, and turning it on over empty accounts buys nothing while spending the one free window in
   which its real cost could have been measured. **The exception is anything detective that is free**, which
   follows the preventive rule instead: IAM Access Analyzer's external-access findings, CloudTrail log file
   validation and S3 Object Lock are all in the landing zone. *This principle used to say only its first
   half, and Stage 1b read it as licence to enable every detective service at once — see
   `plan/institutional-delta.md` for what an institution does instead.*
10. **The lab is not the reference architecture.** Most decisions here are bent by a USD 50/month ceiling
    and a single operator. `plan/institutional-delta.md` records, decision by decision, what a large institution would do instead —
    so that what is learned here is the pattern, not the compromise.

---

## 2. Stages

Full detail, one file each, in [`plan/stages/`](plan/stages/INDEX.md). Open a stage plus the decisions
its **Consumes** row names; that is the whole reading list.

| Stage | What it builds | Status |
|---|---|---|
| [0 — Baseline](plan/stages/stage-00-baseline.md) | Management account by hand, local tooling, the documentation set | **DONE** |
| [1a — Landing zone](plan/stages/stage-01a-landing-zone.md) | Control Tower, the accounts and OUs, root secured, budget — slow and hard to undo | **in progress** |
| [1b — Identity and controls](plan/stages/stage-01b-identity-and-controls.md) | Identity Center, permission sets, SCP/RCP, the free detective controls, org-wide enablement — fast and reversible | not started |
| [2 — Terraform foundation](plan/stages/stage-02-terraform-foundation.md) | State buckets, module skeletons, the SCP import, CI hygiene checks | not started |
| [3 — Networking](plan/stages/stage-03-networking.md) | One VPC per account that has one, split `foundation/` + `egress/` | not started |
| [4 — VPN](plan/stages/stage-04-vpn.md) | WireGuard, the only entry point; peering so the tunnel reaches GitLab; GuardDuty on, with the first exposed resource | not started |
| [5 — Data foundation](plan/stages/stage-05-data-foundation.md) | Lake, Glue, Iceberg, Lake Formation + the three cross-account shares; EFS; Security Hub on | not started |
| [6 — Unified Studio](plan/stages/stage-06-unified-studio.md) | The DataZone V2 domain, project profiles, and the two egress designs compared | not started |
| [7 — GitLab, Runners, ECR](plan/stages/stage-07-gitlab-runners-ecr.md) | GitLab CE on EC2, runners, registries, internal names and TLS from the internal CA | not started |
| [8 — CI/CD pipelines](plan/stages/stage-08-cicd-pipelines.md) | The three pipeline types and the promotion gate | not started |
| [9 — Deployment targets](plan/stages/stage-09-deployment-targets.md) | Staging and Production platforms, Model Registry, the producer path | not started |
| [10 — Orchestration](plan/stages/stage-10-orchestration-promotion.md) | Both orchestrators (D7) built and compared, end-to-end promotion | not started |
| [11 — DLP](plan/stages/stage-11-dlp.md) | Macie, CloudTrail data events, LF column/row filters, GuardDuty's paid add-ons | not started |
| [12 — Observability and FinOps](plan/stages/stage-12-observability-finops.md) | Dashboards, alarms, cost attribution against the real bill | not started |
| [13 — Public web tier](plan/stages/stage-13-public-web-tier.md) | The public-facing experiment in front of a private backend — **and the only stage with public DNS** (D15 phase 2) | not started |
| [14 — Sandbox vending](plan/stages/stage-14-sandbox-vending.md) | A business unit's `Sandbox` account from one name (D35) | not started |

---

## 3. Decisions

**D1-D36, all settled** — one of them, **D30, settled as a revert** and keeps its file so the record shows
what was tried. One file each, with its reasoning, consequences and revision trigger:
[`plan/decisions/INDEX.md`](plan/decisions/INDEX.md) — a one-line summary per decision, which is usually
all that is needed.

The load-bearing few, for orientation: **D11** (pay nothing while idle — three layers), **D13** (Lake
Formation is only real if execution roles hold no S3 on registered prefixes), **D17/D21** (interactive
compute only in the Interactive OU; the chain starts in Development), **D22** (the lake is on the
ownership axis), **D26** (one unified domain, a registry and never a runtime), **D16** (the recovery path
— **the only one**, since D30 was reverted, which is what makes D29's policy canary load-bearing rather
than nice to have).

---

## 4. Cross-cutting work (continuous, not a stage)

- `LOG.md`: the user records every manual step (never edited by Claude).
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this plan.
- `REFERENCES.md`: every link used as a reference.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 5. Everything else

| File | What it holds | Read it when |
|---|---|---|
| [`plan/architecture.md`](plan/architecture.md) | Target architecture, region portability, the data perimeter, the two egress designs, the shape to hold in mind | Designing, or reasoning about where something belongs |
| [`plan/conventions.md`](plan/conventions.md) | Naming, tags, `terraform-live/` layout, Terraform and IAM rules, the `[P]`/`[D]`/`[E]` layers | Any stage from Stage 2 onwards |
| [`plan/integrations.md`](plan/integrations.md) | The `INT-nn` rows: the cross-account things that must be proven, each with a fallback | Building anything that crosses an account boundary |
| [`plan/cost-model.md`](plan/cost-model.md) | The projection and its assumptions (rates live in [`PRICING.md`](PRICING.md)) | Adding a service, or checking the ceiling |
| [`plan/runbooks/break-glass.md`](plan/runbooks/break-glass.md) | When the Management root may be used, the procedure, and the alarm chain that watches it (D16) | An emergency — or when changing anything in that chain |
| [`plan/open-questions.md`](plan/open-questions.md) | Only things to find out by doing | Planning a session |
| [`plan/lessons.md`](plan/lessons.md) | Nineteen mistakes, with the reasoning that makes each recognisable | **Before planning, reviewing or settling a decision** |
| [`plan/institutional-delta.md`](plan/institutional-delta.md) | What a large institution would do instead, decision by decision | Designing — so a lab compromise is not learned as a pattern |
| [`plan/history.md`](plan/history.md) | How the plan and the environment got here | Almost never |
| [`README.md`](README.md) | The argument for the account split, the three AWS reference architectures, and the three distinctions (Development×Experimentation, OU×Account, Data Governance×Production) | Explaining the design to someone, or re-checking why the split is shaped this way |
| [`GLOSSARY.md`](GLOSSARY.md) | Every acronym, the notation, and the IAM condition keys the plan quotes | Reading a stage and hitting an unfamiliar term |
| [`LOG.md`](LOG.md) | Manual AWS actions, written by the user | Never edited by Claude |
