# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`. This file is the core:
the principles, the route by subject, the decisions that carry the design, and the map of where new
content goes. Everything else lives in [`docs/plan/`](plan/) and is read on demand.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**; this file holds the **route** to get there.
- Read this file, then only what the task needs. Executing a stage means opening one stage file plus the
  decisions its `Consumes` row lists. `CLAUDE.md` §"What to read, and when" is the full mapping.
- This file carries no status. A stage's state is one line in `CLAUDE.md`'s Current position, the full
  status is the `Status` row in the stage file's header, and what ran is the stage log.
- The plan changes. When a stage is finished or a decision is revisited, the relevant file is updated
  **in place**. [`docs/plan/history.md`](plan/history.md) records only changes made *after* something has
  been provisioned; a plan edit that predates the resource it describes is an earlier draft, and is not
  kept.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered; the
  prerequisites listed inside each stage must hold.

**Where new content goes:**

| New content | Goes to |
|---|---|
| A choice, with reasoning and a revision trigger | a new file in [`docs/plan/decisions/`](plan/decisions/INDEX.md) + one row in its INDEX |
| Steps to build something | the stage file in [`docs/plan/stages/`](plan/stages/INDEX.md) |
| A naming, layout, Terraform or IAM rule | [`docs/plan/conventions.md`](plan/conventions.md) |
| A cross-account thing that must be proven | a new `INT-nn` row in [`docs/plan/integrations.md`](plan/integrations.md) |
| **A network fact** — a VPC, subnet, route, peering, endpoint, security group, egress path or DNS change | the slice that builds it **and** [`docs/NETWORK.md`](NETWORK.md), in the same sitting; `./scripts/check-network-doc.py` is the mechanical half |
| A mistake worth not repeating | [`docs/plan/lessons.md`](plan/lessons.md) + its recognition key in `CLAUDE.md` |
| A behaviour of AWS, Terraform or a tool that its documentation does not state | a `SUP-nnn` entry in [`docs/AWS_SUPPLEMENT.md`](AWS_SUPPLEMENT.md), in the sitting that measures it |
| A reading a snapshot is expected to show, or a known exception to one | an `INV-nn` or `EXC-nn` row in [`docs/AWS_STATE.md`](AWS_STATE.md) |
| A procedure followed in full and in order | a file in [`docs/plan/runbooks/`](plan/runbooks/) |
| A step that was run, a reading, a measurement | the stage's log, `docs/log/log-stage-NN-*.md`, in the sitting that ran it; the rules are [`docs/log/INDEX.md`](log/INDEX.md) |
| What a stage has done and what it owes | the `Status` row in the stage file's header, and the stage's row in `CLAUDE.md`'s Current position |
| A decision or an act that only the user can take | a row in [`docs/plan/waiting-on-the-user.md`](plan/waiting-on-the-user.md) |
| A change to the plan after something was provisioned | [`docs/plan/history.md`](plan/history.md) |
| A price | [`docs/PRICING.md`](PRICING.md), measured; a link used as a reference goes to [`docs/REFERENCES.md`](REFERENCES.md) |
| **A new project requirement**, or a change to one | [`docs/plan/objectives.md`](plan/objectives.md) — the brief in the user's words, and the only copy of it |

This is the **write** map. The **read** map — which file answers which question — is `CLAUDE.md`
§"What to read, and when", and it is kept only there.

---

## Account tree

The accounts, their OUs, the axes and the cardinality rule are in
[`docs/ORGANIZATION.md`](ORGANIZATION.md); the full annotated tree, the two access paths, region
portability, the data perimeter and the two egress designs are in
[`docs/plan/architecture.md`](plan/architecture.md).

---

## 1. Guiding principles

From `CLAUDE.md`; they constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in that stage's file under [`docs/log/`](log/INDEX.md). Terraform does not manage
   the Management account.
2. **No IAM Users, with no exception since 2026-08-08.** Humans authenticate through IAM Identity Center
   (SSO) and assume roles. Machines (GitLab CI) use **EC2 instance profiles**: a VPN-only GitLab cannot
   serve a JWKS that IAM can fetch, so OIDC federation is not available to any runner in this design
   (Stage 7 step 6, Stage 8 step 4). OIDC remains the target the moment a public issuer surface exists,
   and `docs/plan/institutional-delta.md` records it as the institutional answer. No long-lived access keys
   anywhere. The break-glass credential is the Management account root (D16), which is not an IAM user
   and holds no access key, so the principle needs no exception for it.
3. **Everything else is Terraform.** One state per account/environment, no shared state across
   environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier. **The VPN is the only way into the
   private network, and no access to AWS is conditioned on it**
   ([D39](plan/decisions/D39-access-by-identity.md); `docs/plan/objectives.md` carries the requirement):
   a person reaches the AWS console, the AWS APIs and the SageMaker Unified Studio portal from any network
   with an Identity Center session, which the institution grants only on a laptop it monitors. Built by
   [Stage 6c](plan/stages/stage-06c-networking-hub.md) under D38 (2026-09-05): the WireGuard host drops
   every tunnel packet that is not bound for an RFC1918 address, and a client on the monitored profile
   reaches the internet only through the institutional proxy. [Stage 6g](plan/stages/stage-06g-access-by-identity.md)
   removed the two network conditions that bound persona calls to the hub's addresses (2026-09-17), and
   [Stage 11](plan/stages/stage-11-dlp.md) carries the identity premise as a modelled residual, since
   Identity Center's own directory checks no device. First tested by
   [Stage 13](plan/stages/stage-13-public-web-tier.md).
5. **Incremental.** Each stage leaves the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost
   and, where relevant, a cheaper alternative.
7. **Pay nothing while idle** (D11). Between sessions, metered resources are destroyed, stateful ones are
   stopped, and anything free at rest is left alone. `docs/plan/conventions.md` §5.1: every stage says
   which layer its resources belong to, so the rule shapes how each stage is designed, not only how it is
   operated.
8. **The region is a variable, not an assumption** (D1). The lab runs in `us-west-2` and stays there;
   keeping the region out of the code is Terraform hygiene, not migration work.
   `docs/plan/architecture.md` §4.1.
9. **Preventive controls come before detective ones, and the two halves are scheduled by different
   rules.** Detecting an exfiltration that could have been made impossible is the worse outcome, so
   prevention has precedence. **The preventive half is built in the landing zone** (SCPs, RCPs, endpoint
   policies, the data perimeter of `docs/plan/architecture.md` §4.2): it is free, it is structural, and a
   guardrail written after the thing it guards has been used arrives late. **The detective half is
   enabled when there is something to detect**, service by service, each naming the stage that turns it
   on: Security Hub at Stage 5a, with the first governed data; Macie at Stage 11; GuardDuty at **Stage 15**
   — this principle overruled once, with its eyes open. GuardDuty's coupling to the first internet-facing
   resource (Stage 4) was broken by the 2026-08-18 split, and the trade — an exposed host unwatched
   through the build-out, against a free-trial window that opens over a populated estate — is argued in
   `docs/plan/institutional-delta.md`. Detection is metered, it observes rather than prevents, and turned
   on over empty accounts it buys nothing while spending the one free window in which its real cost could
   be measured. **Anything detective that is free follows the preventive rule instead**: IAM Access
   Analyzer's external-access findings, CloudTrail log file validation and S3 Object Lock are all in the
   landing zone. Stage 1b once read the first half alone as licence to enable every detective service at
   once; `docs/plan/institutional-delta.md` records what an institution does instead.
10. **The lab is not the reference architecture.** Most decisions here are bent by a USD 50/month ceiling
    and a single operator. `docs/plan/institutional-delta.md` records, decision by decision, what a large
    institution would do instead, so that what is learned here is the pattern, not the compromise.

---

## 2. Stages

One file per stage in [`docs/plan/stages/`](plan/stages/INDEX.md). The index there lists every stage in
dependency order with what it builds, its state in one word and its prerequisites. Open a stage plus the
decisions its **Consumes** row names; that is the whole reading list.

The route, by subject:

| Subject | Stages |
|---|---|
| The landing zone and the account tree | [0](plan/stages/stage-00-baseline.md) baseline · [1a](plan/stages/stage-01a-landing-zone.md) Control Tower, accounts and OUs · [1b](plan/stages/stage-01b-identity-and-controls.md) Identity Center and the alarm · [1c](plan/stages/stage-01c-preventive-policies.md) preventive policies · [1d](plan/stages/stage-01d-org-wide-enablement.md) audit trail and org-wide enablement · [6b](plan/stages/stage-06b-development-becomes-staging.md) `Development` becomes `Staging` |
| Terraform, the network and access | [2](plan/stages/stage-02-terraform-foundation.md) Terraform foundation · [3](plan/stages/stage-03-networking.md) networking · [4](plan/stages/stage-04-vpn.md) VPN · [6c](plan/stages/stage-06c-networking-hub.md) the single egress hub · [6g](plan/stages/stage-06g-access-by-identity.md) access by identity |
| The data | [5a](plan/stages/stage-05a-data-foundation.md) the governed lake · [5b](plan/stages/stage-05b-redshift-serverless.md) Redshift Serverless · [6f](plan/stages/stage-06f-data-governance.md) the SageMaker Catalog over the lake · [6h](plan/stages/stage-06h-redshift-connection.md) the Redshift connection · [16](plan/stages/stage-16-sandbox-lake.md) the Sandbox lake · [19](plan/stages/stage-19-smus-native-data-product.md) a data product on SMUS's native path |
| The workbench | [6a](plan/stages/stage-06a-unified-studio.md) Unified Studio, as executed · [6d](plan/stages/stage-06d-unified-studio-remainder.md) Unified Studio, the remainder · [6e](plan/stages/stage-06e-claude-code-bedrock.md) Claude Code on Bedrock · [6i](plan/stages/stage-06i-sandbox-orchestration.md) Sandbox orchestration · [17](plan/stages/stage-17-sandbox-machine-learning.md) machine learning in Sandbox |
| The supply chain and the promotion | [7](plan/stages/stage-07-gitlab-runners-ecr.md) GitLab, runners, ECR · [8](plan/stages/stage-08-cicd-pipelines.md) the pipelines · [9](plan/stages/stage-09-deployment-targets.md) the deployment targets · [10](plan/stages/stage-10-orchestration-promotion.md) orchestration and promotion · [18](plan/stages/stage-18-staging-deployment-project.md) a deployment project in Staging |
| Protection and operations | [11](plan/stages/stage-11-dlp.md) data protection · [12](plan/stages/stage-12-observability-finops.md) observability and FinOps · [15](plan/stages/stage-15-guardduty.md) GuardDuty org-wide |
| The public tier and vending | [13](plan/stages/stage-13-public-web-tier.md) the public web tier · [14](plan/stages/stage-14-sandbox-vending.md) Sandbox vending |

---

## 3. Decisions

**D1-D41, all settled** — **D30 settled as a revert** and keeps its file so the record shows what was
tried. One file each, with its reasoning, consequences and revision trigger. The index is
[`docs/plan/decisions/INDEX.md`](plan/decisions/INDEX.md): one line per decision, usually all that is
needed.

The load-bearing few, for orientation: **D11** (pay nothing while idle — three layers), **D13** (Lake
Formation is only real if execution roles hold no S3 on registered prefixes), **D17** (interactive compute
only in Sandbox; **D21 superseded** by its own larger branch, 2026-09-05), **D38** (one egress, an explicit
proxy, and where the client plane resolves), **D39** (a person reaches AWS by identity; the VPN reaches
the private network), **D22** (the lake is on the ownership axis), **D26** (one
unified domain, a registry and never a runtime), **D16** (the recovery path — **the only one**, since D30
was reverted, which is what makes D29's policy canary load-bearing), **D40** (a Redshift Serverless
warehouse built by hand, never by blueprint), **D41** (the SageMaker application is the deployable unit).

---

## 4. Cross-cutting work (continuous, not a stage)

- [`docs/log/`](log/INDEX.md): every manual step is recorded in that stage's `docs/log/log-stage-NN-*.md`
  — the stage file's own name, prefixed `log-`. The user and Claude write it cooperatively: Claude
  records each step of the plan it executes, in the sitting the step ran, and the user writes whenever
  they want. The rule and its provenance requirement are in [`docs/log/INDEX.md`](log/INDEX.md). A new
  stage gets a new file and a row in that index.
- `CLAUDE.md` → `Claude LOG`: the stage's row in Current position is brought to the stage's state in the
  sitting that changes it.
- `docs/REFERENCES.md`: every link used as a reference.
- [`docs/NETWORK.md`](NETWORK.md): the network as built — updated in the sitting that changes a
  network-bearing slice or module, and **re-measured** with the `aws/` instruments when a `[P]` fact
  moves. It is the one file that answers *how does an app reach the internet, and what can reach it*
  without opening six slices.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `docs/GENERAL_PLAN.md`: revised when a principle or a load-bearing decision changes, or a stage is
  added.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 5. Everything else

**`CLAUDE.md` §"What to read, and when" is the only routing table.** It lists every file in this
repository against the question that sends you to it.
