# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`.
**This file is the core: principles, the account map, and the two indexes.** Everything else lives in
[`docs/plan/`](plan/) and is read on demand.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**. This file holds the **route** to get there.
- **Read this file, then read only what the task needs.** Executing a stage means opening one stage file
  plus the decisions its `Consumes` row lists — not the whole plan. `CLAUDE.md` §"What to read, and when"
  is the full mapping.
- Every entry in the `Claude LOG` section of `CLAUDE.md` must reference the stage it belongs to
  (e.g. "Stage 3 - Networking, in progress").
- This plan is expected to change. Whenever a stage is finished or a decision is revisited, update the
  relevant file **in place**. [`docs/plan/history.md`](plan/history.md) records only changes made *after*
  something has been provisioned — a plan edit that predates the resource it describes is just an earlier
  draft, and is not kept.
- Stages are ordered by dependency, not by importance. A stage can be split or reordered, but the
  prerequisites listed inside each stage must hold.

**Where new content goes** — the rule that keeps this file small:

| New content | Goes to |
|---|---|
| A choice, with reasoning and a revision trigger | a new file in [`docs/plan/decisions/`](plan/decisions/INDEX.md) + one row in its INDEX |
| Steps to build something | the stage file in [`docs/plan/stages/`](plan/stages/INDEX.md) |
| A naming, layout, Terraform or IAM rule | [`docs/plan/conventions.md`](plan/conventions.md) |
| A cross-account thing that must be proven | a new `INT-nn` row in [`docs/plan/integrations.md`](plan/integrations.md) |
| **A network fact** — a VPC, subnet, route, peering, endpoint, security group, egress path or DNS change | the slice that builds it **and** [`docs/NETWORK.md`](NETWORK.md), in the same sitting — `./scripts/check-network-doc.py` is the mechanical half |
| A mistake worth not repeating | [`docs/plan/lessons.md`](plan/lessons.md) + its recognition key in `CLAUDE.md` |
| A procedure to follow when something is on fire | a file in [`docs/plan/runbooks/`](plan/runbooks/) |
| What happened | [`docs/plan/history.md`](plan/history.md) — never a `docs/log/log-stage-NN-*.md`, which is the user's |
| **A new project requirement**, or a change to one | [`docs/plan/objectives.md`](plan/objectives.md) — the brief in the user's words, and the only copy of it |

This is the **write** map. The **read** map — which file answers which question — is `CLAUDE.md`
§"What to read, and when", and it is kept only there.

---

## The map

| Account | OU | Axis | What it is |
|---|---|---|---|
| Management | (root) | platform | Bootstrap only, console only, never Terraform. Its **root user is the break-glass credential** (D16) |
| Log Archive | Security | platform | Control Tower log sink, S3 Object Lock |
| Audit | Security | platform | Security guardian: GuardDuty, Security Hub, Macie, Access Analyzer |
| Identity | **Identity** | platform | Identity Center **delegated administration** (D10) — as sensitive as Management. Its own OU because Control Tower would not vend it into the foundational `Security` OU (D23, 2026-08-09) |
| Policy Canary | Policy Test | platform | Deliberately empty. The disposable account a candidate SCP is exercised against (D29) |
| Sandbox | Interactive → **Sandboxes** | lifecycle (the chain's origin since 2026-09-05) | **Experimentation** — the unit of work is a notebook, and the **only** account where a human runs code (D17 sharpened). The VPN terminated here until Stage 6c moves it to Production's `VPC-Networking`. One per business unit (D35), grouped in a nested OU that carries no policy set of its own and is not meant to (D37) |
| Data Governance | Data | **ownership** | The governed lake + the Unified Studio domain (D22, D26). No VPC, no user compute, no interactive sign-in |
| Staging | Workloads | lifecycle | Deployment target, written only by the pipeline; sampled or synthetic data (D20). **It is the renamed `Development` account since [Stage 6b](plan/stages/stage-06b-development-becomes-staging.md)** — the quota refused a vend, and the interactive environment it used to be was found unnecessary (D21 superseded by its own larger branch) |
| Production | Workloads | lifecycle | Deployment target **plus** the supply chain (GitLab, runners, ECR, CodeArtifact, Model Registry, orchestration — D14) **plus, since [Stage 6c](plan/stages/stage-06c-networking-hub.md), the network platform**: three VPCs, the estate's only internet gateway, the proxy and the VPN endpoint (D38, a quota-forced compromise with a trigger to move it out) |

Three groups, not one sequence: the **lifecycle** axis (Sandbox → Staging → Production), the **ownership** axis (Data Governance alone), and the **platform**
accounts on neither. *An account off the lifecycle axis is not "a production account"* — Data Governance
and Identity are **high blast radius**, which is a different property.

**And one property that cuts across all three: cardinality (D35).** Every account above is **structural** —
exactly one, forever — **except `Sandbox`, which is one per business unit** (N is 1 today). The chain reads
**N Sandboxes → one Staging → one Production**, so the cardinality boundary is exactly
D21's graduation boundary: experimentation multiplies, the engineering chain that follows it does not — which
is why the promotion chain is untouched by N. That decides where vending is automated: the structural
accounts keep the console flow (D34), the Sandbox gets [Stage 14](plan/stages/stage-14-sandbox-vending.md).
It also means any stage writing "*the* Sandbox account" is writing a singleton assumption that has to be paid
for later.

Full annotated tree, the two access paths, region portability, the data perimeter and the two egress
designs: [`docs/plan/architecture.md`](plan/architecture.md).

---

## 1. Guiding principles

These come from `CLAUDE.md` and constrain every stage:

1. **The Management account is bootstrap-only.** Anything done there is manual, through the console, and
   recorded by the user in that stage's file under [`docs/log/`](log/INDEX.md). Terraform does not manage the
   Management account.
2. **No IAM Users, and since 2026-08-08 with no exception.** Humans authenticate through IAM Identity
   Center (SSO) and assume roles. Machines (GitLab CI) use **EC2 instance profiles**: a VPN-only GitLab
   cannot serve a JWKS that IAM can fetch, so OIDC federation is not available to any runner in this
   design (Stage 7 step 6, Stage 8 step 4). OIDC remains the target the moment a public issuer surface
   exists, and `docs/plan/institutional-delta.md` records it as the institutional answer. No long-lived access
   keys anywhere. This principle used to carry one
   documented exception for break-glass; **D16 settled that credential as the Management account root,
   which is not an IAM user and holds no access key**, so the exception dissolved instead of being
   justified. A rule with no escape hatch is a rule that gets broken under pressure — the escape hatch
   here simply is not an IAM user.
3. **Everything else is Terraform.** One state per account/environment, no shared state across environments.
4. **Private by default.** Data assets and databases never face the public internet. The only public entry
   points are the VPN and, later (Stage 13), an experimental web tier — **qualified 2026-08-22 (INT-16,
   measured): the VPN is the only entry to the private network and the AWS control plane; the Unified
   Studio portal's user ingress was measured reachable off-VPN** (`README.md` item 3 carries the full
   statement; the closing choice — fallback (i) on the domain execution role versus recorded acceptance —
   is the user's, deferred, and presumed nowhere). **Built by [Stage 6c](plan/stages/stage-06c-networking-hub.md) under D38 (2026-09-05): the client is a
   private-network client, so its whole internet — the AWS control plane included — crosses the
   institutional proxy, and the WireGuard host drops every tunnel packet that is not bound for an RFC1918
   address. Re-grounded 2026-08-25: the requirement side is
   explicit in `docs/plan/objectives.md`** — the client reaches the organization's cloud infrastructure
   only through the VPN, and once connected, *all* of the client's internet (the portal's public names
   included) runs through the cloud's own egress behind an institutional HTTP/HTTPS proxy (D5/D6 revised;
   Stage 11; open question 23 owns the topology). The measured off-VPN gap is unchanged; what changed is
   that accepting it would now be recording a deviation from a stated objective.
5. **Incremental.** Each stage must leave the environment in a working, verifiable state.
6. **Cost is a first-class constraint.** This is a personal account. Every stage lists its recurring cost and,
   where relevant, a cheaper alternative.
7. **Pay nothing while idle** (decision D11). Between sessions, metered resources are destroyed, stateful
   ones are stopped, and anything free at rest is simply left alone. See `docs/plan/conventions.md` §5.1 — every stage must say which
   layer its resources belong to, so this shapes how each stage is designed, not just how it is operated.
8. **The region is a variable, not an assumption** (decision D1). The lab runs in `us-west-2` and stays
   there; keeping the region out of the code is plain Terraform hygiene, not migration work. See `docs/plan/architecture.md` §4.1.
9. **Preventive controls come before detective ones — and the two halves are scheduled by different
   rules.** Detecting an exfiltration you could have made impossible is a worse outcome than preventing it,
   so prevention has precedence. **The preventive half is built in the landing zone** (SCPs, RCPs, endpoint
   policies, the data perimeter of `docs/plan/architecture.md` §4.2): it is free, it is structural, and a
   guardrail written after the thing it guards has already been used is a guardrail that arrives late.
   **The detective half is enabled when there is something to detect**, service by service, each naming
   the stage that turns it on — Security Hub at Stage 5, with the first governed data; Macie at Stage 11;
   and GuardDuty at **Stage 15**, which is this principle overruled once, with its eyes open: the coupling
   to the first internet-facing resource (Stage 4) was broken by the 2026-08-18 split, deliberately, and
   the trade — an exposed host unwatched through the build-out, against a free-trial window that opens
   over a populated estate — is argued in `docs/plan/institutional-delta.md`, not silently absorbed. Detection is metered, it observes rather
   than prevents, and turning it on over empty accounts buys nothing while spending the one free window in
   which its real cost could have been measured. **The exception is anything detective that is free**, which
   follows the preventive rule instead: IAM Access Analyzer's external-access findings, CloudTrail log file
   validation and S3 Object Lock are all in the landing zone. *This principle used to say only its first
   half, and Stage 1b read it as licence to enable every detective service at once — see
   `docs/plan/institutional-delta.md` for what an institution does instead.*
10. **The lab is not the reference architecture.** Most decisions here are bent by a USD 50/month ceiling
    and a single operator. `docs/plan/institutional-delta.md` records, decision by decision, what a large institution would do instead —
    so that what is learned here is the pattern, not the compromise.

---

## 2. Stages

Full detail, one file each, in [`docs/plan/stages/`](plan/stages/INDEX.md). Open a stage plus the decisions
its **Consumes** row names; that is the whole reading list.

| Stage | What it builds | Status |
|---|---|---|
| [0 — Baseline](plan/stages/stage-00-baseline.md) | Management account by hand, local tooling, the documentation set | **DONE** |
| [1a — Landing zone](plan/stages/stage-01a-landing-zone.md) | Control Tower, the accounts and OUs, root secured, budget — slow and hard to undo | **DONE.** *(It read "done except the `Staging` vend" until 2026-09-05: the quota increase was refused and [Stage 6b](plan/stages/stage-06b-development-becomes-staging.md) makes `Staging` by renaming `Development`, so there is no vend left to wait for.)* |
| [1b — Identity Center and the alarm](plan/stages/stage-01b-identity-and-controls.md) | The alarm first, then delegation, users and groups, the administrator permission set, SSO profiles, retiring the direct assignments, AZ mapping, Access Analyzer (steps 8.3, 1-6, 5.1, 8.2) | **DONE** (2026-08-12) |
| [1c — Preventive policies](plan/stages/stage-01c-preventive-policies.md) | SCP, RCP, tag and declarative policies, the managed controls (step 7) — the one irreversible-from-inside sitting | **DONE** (2026-08-14) — ten documents, four policy types, battery 93/93 |
| [1d — Audit trail and org-wide enablement](plan/stages/stage-01d-org-wide-enablement.md) | Object Lock, the AWS Config decision, org-wide RAM + the Lake Formation cross-account version, **and the Region ceiling on `Security`** (steps 9-12, independent of each other) | **DONE 2026-08-15 — this closes the landing zone.** Object Lock is on at `COMPLIANCE`/90 days, written past `CTS3PV8` as `AWSControlTowerExecution`; the Config recorder is left alone (measured ~USD 0.5/month) and Management is deliberately unrecorded; RAM org-wide sharing is on; the Region ceiling is on `Security` |
| [2 — Terraform foundation](plan/stages/stage-02-terraform-foundation.md) | State buckets, the six persona permission sets written from scratch, the policy import, the hygiene checks, D11's `up`/`down`/`status` | **DONE** (2026-08-16) — all nine verifications answered, (iii) from Management (`INV-17`) |
| [3 — Networking](plan/stages/stage-03-networking.md) | One VPC per account that has one, split `foundation/` + `egress/` — **plus the first reusable modules**, moved here from Stage 2 step 7 | **DONE** (2026-08-16) — applied, measured and torn down to USD 0.0000/h; D11 proven twice (`foundation/` byte-identical on the second `up`, every `[E]` id new); the perimeter, both peerings and the flow logs probed |
| [4 — VPN](plan/stages/stage-04-vpn.md) | WireGuard over the Stage 3 network, the only entry point (to the private network and the control plane — the portal qualification of 2026-08-22 is principle 4's) | **DONE 2026-08-18 — closed by the GuardDuty split**: passes 1-3 executed and measured; pass 4 left the stage whole for Stage 15, prepared. Decision 4 (third review) moved the host private key into a `[P]` Secrets Manager secret, with [`docs/plan/runbooks/vpn.md`](plan/runbooks/vpn.md) Part K owning every key event; `sandbox/vpn/` is the tree's first `[D]` slice; the close-out log entry is the user's |
| [5 — Data foundation](plan/stages/stage-05-data-foundation.md) | Lake, Glue, Iceberg, Lake Formation + the three cross-account shares; Security Hub on | **DONE — every pass, 2026-08-18/20** — the governed lake, the governance manager's grants, both cross-account TBAC shares, the consumer side (one `consumer-data` module in two slices — v0.2.0 since the 2026-08-19 revision that withdrew `security-zone`), 4c's persona grants, **4d's behavioural proofs, 4e's `DenyUserCompute` amendment, and pass 6** (Security Hub CSPM org-wide by central configuration on the root, 2026-08-20 — `INV-09` to nine/four). **The one thing left is step 13.3's triage**, which needs a first FSBP report that did not exist when the stage closed. Revised **revised 2026-08-17 after the data-governance review** (the `zone` tag dimension; classification-scoped LF-TBAC grants, `restricted` by explicit grant only); **the NFS requirement withdrawn later the same day — no `nfs/` slice (D24 withdrawn)** |
| [6a — Unified Studio (executed)](plan/stages/stage-06a-unified-studio.md) | The record of what ran: the domain, both associations, 11 blueprint configurations and 22 grants per member, both project profiles, the create path end to end, `default-v0.1.0`, and the dated readings of passes 4-5 | **CLOSED as a record 2026-09-05** |
| [6b — `Development` becomes `Staging`](plan/stages/stage-06b-development-becomes-staging.md) | One account changes role: the SMUS surface unwound inside `Interactive`, the lake share and the read-write persona revoked, the rename and the OU move, the tree migrated to `staging/` | not started |
| [6c — Networking: the single egress hub](plan/stages/stage-06c-networking-hub.md) | Three VPCs in Production, five peerings, the `awsds.internal` family, WireGuard and Squid as two `[D]` hosts, **zero NAT gateways**, no default route in any spoke — and the client plane moved off the compute plane's resolver. Writes **D38** | not started |
| [6d — Unified Studio: the remainder](plan/stages/stage-06d-unified-studio-remainder.md) | The deny pair exercised, the house image selectable, a session measured under the proxy, the workflow surface measured, the lifecycle proven | not started |
| [7 — GitLab, Runners, ECR](plan/stages/stage-07-gitlab-runners-ecr.md) | GitLab CE on EC2, runners, registries, internal names and TLS from the internal CA | not started — **pass 0 shrank to `registry/`'s 5.a on 2026-08-21**: the CA came back to pass 1 with its leaves (D36 §3 amended — nothing serves a `.internal` name before this stage), and a new step 2.6 rebuilds the `dev-env` image with the root |
| [8 — CI/CD pipelines](plan/stages/stage-08-cicd-pipelines.md) | The three pipeline types and the promotion gate | not started |
| [9 — Deployment targets](plan/stages/stage-09-deployment-targets.md) | Staging and Production platforms, Model Registry, the producer path | not started |
| [10 — Orchestration](plan/stages/stage-10-orchestration-promotion.md) | Both orchestrators (D7) built and compared, end-to-end promotion | not started |
| [11 — DLP](plan/stages/stage-11-dlp.md) | Macie, the LF data cells filters, the Access Analyzer collection, data-event trails and exfiltration alarms, GuardDuty's paid features — and the threat model, `docs/plan/threat-model.md`. **Since 2026-08-25 also the client plane's egress control**: the single-egress HTTP/HTTPS proxy of the objectives clarification (open question 23 owns its topology) | not started — **revised 2026-08-17** into the action-checklist format, pre-instrumented by `./aws/dlp.py` |
| [12 — Observability and FinOps](plan/stages/stage-12-observability-finops.md) | Dashboards, alarms, cost attribution against the real bill | not started |
| [13 — Public web tier](plan/stages/stage-13-public-web-tier.md) | The public-facing experiment in front of a private backend — **and the only stage with public DNS** (D15 phase 2) | not started |
| [14 — Sandbox vending](plan/stages/stage-14-sandbox-vending.md) | A business unit's `Sandbox` account from one name (D35) | not started |
| [15 — GuardDuty org-wide](plan/stages/stage-15-guardduty.md) | Threat detection over the whole organization — delegation to Audit, auto-enable `ALL`, every optional plan switched off (they arrive ON), findings routed to a human for the first time | not started — created 2026-08-18 by splitting Stage 4's pass 4 out whole; nothing blocks it, and it gates Stage 11 step 4 (a month of billing) and Stage 5 step 13.2's ingestion |
| [16 — Sandbox lake](plan/stages/stage-16-sandbox-lake.md) | The fourth Sandbox bucket, `awsds-sandbox-lake` — **permanent** per-SSO-group artifacts, mounted into SMUS projects via the portal's S3 connection, vended to laptops via S3 Access Grants; a compensated shadow lake, its trade argued in the institutional-delta row | **DONE (2026-08-26, created and closed in one day)** — applied (`12 added`, re-plan `No changes`), then measured from every side: the three-layer refusal contrast, the unchanged `s3-read-write` run with the KMS half closed, the connection's both-doors CloudTrail reading, and the finding that the SMUS image **auto-vends** "direct" S3 calls (the in-image direct-refusal test is unrunnable; the laptop is that control's home). Pass 6 measured revocation: the vend door closes between **+1 s and +19 s** of the delete, issued bearers live to their own expiry; `SL-4` hardened by its first live anomaly. The Lake Formation admin-seat finding settled as `consumer-data-v0.5.0` + `DL-13` (OQ 24 keeps the governance half). Log written ([log](log/log-stage-16-sandbox-lake.md)) |

---

## 3. Decisions

**D1-D37, all settled** — one of them, **D30, settled as a revert** and keeps its file so the record shows
what was tried. One file each, with its reasoning, consequences and revision trigger:
[`docs/plan/decisions/INDEX.md`](plan/decisions/INDEX.md) — a one-line summary per decision, which is usually
all that is needed.

The load-bearing few, for orientation: **D11** (pay nothing while idle — three layers), **D13** (Lake
Formation is only real if execution roles hold no S3 on registered prefixes), **D17** (interactive
compute only in Sandbox; **D21 superseded** by its own larger branch, 2026-09-05), **D38** (one egress,
an explicit proxy, and where the client plane resolves), **D22** (the lake is on the
ownership axis), **D26** (one unified domain, a registry and never a runtime), **D16** (the recovery path
— **the only one**, since D30 was reverted, which is what makes D29's policy canary load-bearing rather
than nice to have).

---

## 4. Cross-cutting work (continuous, not a stage)

- [`docs/log/`](log/INDEX.md): every manual step is recorded in that stage's `docs/log/log-stage-NN-*.md`
  — the stage file's own name, prefixed `log-`, so the two never collide. **Written cooperatively by the
  user and Claude, and by Claude only when asked** (revised 2026-08-17; the rule and its provenance
  requirement are in [`docs/log/INDEX.md`](log/INDEX.md)).
  A new stage gets a new file; its row in [`docs/log/INDEX.md`](log/INDEX.md) is
  Claude's to write and to keep current — that index is the one file under `docs/log/` Claude maintains.
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this plan.
- `docs/REFERENCES.md`: every link used as a reference.
- [`docs/NETWORK.md`](NETWORK.md): the network as built — updated in the sitting that changes a
  network-bearing slice or module, and **re-measured** with the `aws/` instruments when a `[P]` fact
  moves. It is the one file that answers *how does an app reach the internet, and what can reach it*
  without opening six slices, which is what makes a stale copy expensive.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `docs/GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 5. Everything else

**`CLAUDE.md` §"What to read, and when" is the routing table, and it is the only one.** It lists every
file in this repository against the question that sends you to it — `docs/plan/objectives.md`,
`docs/plan/architecture.md`,
`docs/plan/conventions.md`, `docs/plan/integrations.md`, `docs/plan/cost-model.md`, `docs/plan/lessons.md`,
`docs/plan/open-questions.md`, `docs/plan/institutional-delta.md`, `docs/plan/history.md`, `docs/plan/runbooks/`,
`README.md`, `docs/GLOSSARY.md`, `docs/PRICING.md`, `docs/log/INDEX.md`. This section used to repeat two thirds of it,
which is one table too many for something whose whole purpose is to be trusted without checking.
