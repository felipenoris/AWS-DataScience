# General Implementation Plan

Staged plan to build the AWS Data Science environment described in `CLAUDE.md`. This file is the core:
the principles, the stage index and the decision index. Everything else lives in [`docs/plan/`](plan/) and
is read on demand.

## How to use this file

- `CLAUDE.md` holds the **goals and the working rules**; this file holds the **route** to get there.
- Read this file, then only what the task needs. Executing a stage means opening one stage file plus the
  decisions its `Consumes` row lists. `CLAUDE.md` §"What to read, and when" is the full mapping.
- Every entry in the `Claude LOG` section of `CLAUDE.md` references the stage it belongs to
  (e.g. "Stage 3 - Networking, in progress").
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
| A procedure to follow when something is on fire | a file in [`docs/plan/runbooks/`](plan/runbooks/) |
| What happened | [`docs/plan/history.md`](plan/history.md) — never a `docs/log/log-stage-NN-*.md`, which is the user's |
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
   points are the VPN and, later (Stage 13), an experimental web tier. Qualified 2026-08-22 (INT-16,
   measured): the VPN is the only entry to the private network and the AWS control plane; the Unified
   Studio portal's user ingress is reachable off-VPN (`README.md` item 3 carries the full statement). The
   requirement side is explicit in `docs/plan/objectives.md`: the client reaches the organization's cloud
   infrastructure only through the VPN, and once connected, *all* of the client's internet (the portal's
   public names included) runs through the cloud's own egress behind an institutional HTTP/HTTPS proxy
   (D5/D6 revised; Stage 11; D38 owns the topology and closes open question 23). Built by
   [Stage 6c](plan/stages/stage-06c-networking-hub.md) under D38 (2026-09-05): the client is a
   private-network client, its whole internet — the AWS control plane included — crosses the institutional
   proxy, and the WireGuard host drops every tunnel packet that is not bound for an RFC1918 address.
   Monitored by [Stage 11](plan/stages/stage-11-dlp.md), first tested by
   [Stage 13](plan/stages/stage-13-public-web-tier.md). The measured off-VPN gap is a recorded deviation
   from a stated objective — accepted at 6c step 6.6 on 2026-09-07 by the user's choice, fallback (ii),
   revisited at Stage 11 step 3.4 and alarmed by its 5.2.
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
   on: Security Hub at Stage 5, with the first governed data; Macie at Stage 11; GuardDuty at **Stage 15**
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

Full detail, one file each, in [`docs/plan/stages/`](plan/stages/INDEX.md). Open a stage plus the decisions
its **Consumes** row names; that is the whole reading list.

| Stage | What it builds | Status |
|---|---|---|
| [0 — Baseline](plan/stages/stage-00-baseline.md) | Management account by hand, local tooling, the documentation set | **DONE** |
| [1a — Landing zone](plan/stages/stage-01a-landing-zone.md) | Control Tower, the accounts and OUs, root secured, budget — slow and hard to undo | **DONE.** The quota increase for a `Staging` vend was refused; [Stage 6b](plan/stages/stage-06b-development-becomes-staging.md) makes `Staging` by renaming `Development`, so no vend is owed |
| [1b — Identity Center and the alarm](plan/stages/stage-01b-identity-and-controls.md) | The alarm first, then delegation, users and groups, the administrator permission set, SSO profiles, retiring the direct assignments, AZ mapping, Access Analyzer (steps 8.3, 1-6, 5.1, 8.2) | **DONE** (2026-08-12) |
| [1c — Preventive policies](plan/stages/stage-01c-preventive-policies.md) | SCP, RCP, tag and declarative policies, the managed controls (step 7) — the one irreversible-from-inside sitting | **DONE** (2026-08-14) — ten documents, four policy types, battery 93/93 |
| [1d — Audit trail and org-wide enablement](plan/stages/stage-01d-org-wide-enablement.md) | Object Lock, the AWS Config decision, org-wide RAM + the Lake Formation cross-account version, **and the Region ceiling on `Security`** (steps 9-12, independent of each other) | **DONE 2026-08-15 — closes the landing zone.** Object Lock is on at `COMPLIANCE`/90 days, written past `CTS3PV8` as `AWSControlTowerExecution`; the Config recorder is left alone (measured ~USD 0.5/month) and Management is unrecorded; RAM org-wide sharing is on; the Region ceiling is on `Security` |
| [2 — Terraform foundation](plan/stages/stage-02-terraform-foundation.md) | State buckets, the six persona permission sets written from scratch, the policy import, the hygiene checks, D11's `up`/`down`/`status` | **DONE** (2026-08-16) — all nine verifications answered, (iii) from Management (`INV-17`) |
| [3 — Networking](plan/stages/stage-03-networking.md) | One VPC per account that has one, split `foundation/` + `egress/` — **plus the first reusable modules**, moved here from Stage 2 step 7 | **DONE** (2026-08-16) — applied, measured and torn down to USD 0.0000/h; D11 proven twice (`foundation/` byte-identical on the second `up`, every `[E]` id new); the perimeter, both peerings and the flow logs probed |
| [4 — VPN](plan/stages/stage-04-vpn.md) | WireGuard over the Stage 3 network, the only entry point (to the private network and the control plane — the portal qualification of 2026-08-22 is principle 4's) | **DONE 2026-08-18 — closed by the GuardDuty split**: passes 1-3 executed and measured; pass 4 left the stage whole for Stage 15, prepared. Decision 4 (third review) moved the host private key into a `[P]` Secrets Manager secret, with [`docs/plan/runbooks/vpn.md`](plan/runbooks/vpn.md) Part K owning every key event; `sandbox/vpn/` was the tree's first `[D]` slice; the close-out log entry is the user's |
| [5 — Data foundation](plan/stages/stage-05-data-foundation.md) | Lake, Glue, Iceberg, Lake Formation + the three cross-account shares; Security Hub on | **DONE — every pass, 2026-08-18/20**: the governed lake, the governance manager's grants, both cross-account TBAC shares, the consumer side (one `consumer-data` module in two slices — v0.2.0 since the 2026-08-19 revision that withdrew `security-zone`), 4c's persona grants, **4d's behavioural proofs, 4e's `DenyUserCompute` amendment, and pass 6** (Security Hub CSPM org-wide by central configuration on the root, 2026-08-20 — `INV-09` to nine/four). **Two things stay open**: 13.3's triage, which needs a first FSBP report that did not exist when the stage closed, and open question 19, the crawler demander, which no proof can settle. The 2026-08-17 data-governance review added the `zone` tag dimension and classification-scoped LF-TBAC grants (`restricted` by explicit grant only), and withdrew the NFS requirement the same day — no `nfs/` slice (D24 withdrawn) |
| [6a — Unified Studio (executed)](plan/stages/stage-06a-unified-studio.md) | The record of what ran: the domain, both associations, 11 blueprint configurations and 22 grants per member, both project profiles, the create path end to end, `default-v0.1.0`, and the dated readings of passes 4-5 | **CLOSED as a record 2026-09-05** |
| [6b — `Development` becomes `Staging`](plan/stages/stage-06b-development-becomes-staging.md) | One account changes role: the SMUS surface unwound inside `Interactive`, the lake share and the read-write persona revoked, the rename and the OU move, the tree migrated to `staging/` | **DONE 2026-09-06** — every pass in one day; the VPC's CIDR and both `[P]` gateway-endpoint ids survived, `10.40.0.0/16` is free for 6c, and 3.5 closed the same day with the answer that the provisioned product does not follow an out-of-band rename and cannot be made to — a permanent divergence, treated as D32 treats the direct assignment |
| [6c — Networking: the single egress hub](plan/stages/stage-06c-networking-hub.md) | Three VPCs in Production, five peerings, the `awsds.internal` family, WireGuard and Squid as two `[D]` hosts, **zero NAT gateways**, no default route in any spoke — and the client plane moved off the compute plane's resolver. Writes **D38** | **DONE 2026-09-08, pass 8 included** — the second client profile: the split-tunnel profile beside the monitored one, laptop-only, no host change, measured the same night. Passes 0-7: pass 6 closed with 6.5 (two doors by service family, the union trimmed, `sandbox/foundation` unfrozen, `sandbox/vpn/` retired) and 6.6 (INT-16 accepted, revisited at Stage 11); decision due 4 taken as (c): the access log's export waits for Stage 11 step 5.1, the organization trail records any deletion meanwhile |
| [6d — Unified Studio: the remainder](plan/stages/stage-06d-unified-studio-remainder.md) | The deny pair exercised, the house image selectable, a session measured under the proxy, the workflow surface measured, the lifecycle proven, the remote-IDE channel opened | **in progress** — steps 8 and 9 closed 2026-09-08/09 (the Code Editor reaches the gallery through the proxy, the build plane is `open`, `vpc-egress-v0.11.1` generates the bypass list from the endpoints' own `dns_entry`); step 4 measured 2026-09-09/10 and closed as a decision — the portal's notebook operator dies on the D13 boundary and nothing the operator exposes repairs it. Step 2, the house image, is the one that unblocks the rest: step 8's delivery hangs off its 2.4, and 3.1's remaining ecosystems are read in it. 7.3-7.9 wait on decision due 4, the connection method |
| [7 — GitLab, Runners, ECR](plan/stages/stage-07-gitlab-runners-ecr.md) | GitLab CE on EC2, runners, registries, the `awsds.internal` names and TLS from the internal CA — all in `VPC-SharedServices`, all reaching the internet through the proxy | not started — in the action-checklist format, against 6b/6c/6d and the vendor documentation. Seven corrections in its own table, the sharpest three: Let's Encrypt is **on by default** on an HTTPS `external_url` and retries every `reconfigure`; the CA root has a **fourth** surface — GitLab itself; and the pull-through cache's first pull **may need a route this estate does not have**, which makes it D38's first named NAT-contingency candidate. The buildbox retires into the build runner; pass 0 is already applied |
| [8 — CI/CD pipelines](plan/stages/stage-08-cicd-pipelines.md) | The three pipeline types and the promotion gate | not started — no vend to wait for; the engineering apply moves to `sandbox/app/app-etl/` behind a `layers.py` refusal that keeps CI out of Sandbox, and the **D28 workflow lint is authored here** with the four rules 6d supplies |
| [9 — Deployment targets](plan/stages/stage-09-deployment-targets.md) | Staging and Production platforms, Model Registry, the producer path | not started — the announced off-VPC job deny has steps (3.5-3.7): it moves from the six persona sets onto the job-execution **roles** as a permissions boundary, read back with `get-role`, with serverless inference settled as an SCP deny rather than an exception |
| [10 — Orchestration](plan/stages/stage-10-orchestration-promotion.md) | One orchestrator (MWAA Serverless), end-to-end promotion, the model chain | not started — one design in **two accounts**, Staging first; the workers take AWS's documented **private-routing** shape, which makes them **D38's first named exception — one with no internet path at all** |
| [11 — DLP](plan/stages/stage-11-dlp.md) | Macie, the LF data cells filters, the Access Analyzer collection, data-event trails and exfiltration alarms, GuardDuty's paid features — and the threat model, `docs/plan/threat-model.md`. Also the client plane's egress control: the single-egress HTTP/HTTPS proxy of the objectives clarification (D38 owns its topology, closing open question 23) | not started — in the action-checklist format, pre-instrumented by `./aws/dlp.py` |
| [12 — Observability and FinOps](plan/stages/stage-12-observability-finops.md) | Dashboards, alarms, retention, cost attribution against the real bill, backup and recoverability, quota alarms | not started — the NAT panels lose their resource and the proxy's **403 rate** becomes a design signal. Step 2.1 is where D12's budget-notifies-nobody deferral is closed |
| [13 — Public web tier](plan/stages/stage-13-public-web-tier.md) | The public-facing experiment in front of a private backend — **and the only stage with public DNS** (D15 phase 2) | not started — the ALB lands in `VPC-Networking`'s public tier as the **second enumerated listener**, which is what first tests 6c's single-ingress gate; the backend is reached as **IP targets over the peering** |
| [14 — Sandbox vending](plan/stages/stage-14-sandbox-vending.md) | A business unit's `Sandbox` account from one name (D35) | not started — **blocked on the account quota**. Its central question, where the VPN terminates, was **closed without N** by D38: a designated hub. Each vend still owes a CIDR, **two** peering pairs, one child zone and one proxy source block — all generated from 6c's map |
| [15 — GuardDuty org-wide](plan/stages/stage-15-guardduty.md) | Threat detection over the whole organization — delegation to Audit, auto-enable `ALL`, every optional plan switched off (they arrive ON), findings routed to a human for the first time | not started — created 2026-08-18 by splitting Stage 4's pass 4 out whole; nothing blocks it, and it gates Stage 11 step 4 (a month of billing) and Stage 5 step 13.2's ingestion |
| [16 — Sandbox lake](plan/stages/stage-16-sandbox-lake.md) | The fourth Sandbox bucket, `awsds-sandbox-lake` — **permanent** per-SSO-group artifacts, mounted into SMUS projects via the portal's S3 connection, vended to laptops via S3 Access Grants; a compensated shadow lake, its trade argued in the institutional-delta row | **DONE (2026-08-26, created and closed in one day)** — applied (`12 added`, re-plan `No changes`), then measured from every side: the three-layer refusal contrast, the unchanged `s3-read-write` run with the KMS half closed, the connection's both-doors CloudTrail reading, and the finding that the SMUS image **auto-vends** "direct" S3 calls (the in-image direct-refusal test is unrunnable; the laptop is that control's home). Pass 6 measured revocation: the vend door closes between **+1 s and +19 s** of the delete, issued bearers live to their own expiry; `SL-4` hardened by its first live anomaly. The Lake Formation admin-seat finding settled as `consumer-data-v0.5.0` + `DL-13` (OQ 24 keeps the governance half). Log written ([log](log/log-stage-16-sandbox-lake.md)) |

---

## 3. Decisions

**D1-D38, all settled** — **D30 settled as a revert** and keeps its file so the record shows what was
tried. One file each, with its reasoning, consequences and revision trigger:
[`docs/plan/decisions/INDEX.md`](plan/decisions/INDEX.md) — a one-line summary per decision, usually all
that is needed.

The load-bearing few, for orientation: **D11** (pay nothing while idle — three layers), **D13** (Lake
Formation is only real if execution roles hold no S3 on registered prefixes), **D17** (interactive compute
only in Sandbox; **D21 superseded** by its own larger branch, 2026-09-05), **D38** (one egress, an explicit
proxy, and where the client plane resolves), **D22** (the lake is on the ownership axis), **D26** (one
unified domain, a registry and never a runtime), **D16** (the recovery path — **the only one**, since D30
was reverted, which is what makes D29's policy canary load-bearing).

---

## 4. Cross-cutting work (continuous, not a stage)

- [`docs/log/`](log/INDEX.md): every manual step is recorded in that stage's `docs/log/log-stage-NN-*.md`
  — the stage file's own name, prefixed `log-`. **Written cooperatively by the user and Claude, and by
  Claude only when asked**; the rule and its provenance requirement are in
  [`docs/log/INDEX.md`](log/INDEX.md). A new stage gets a new file; its row in that index is Claude's to
  write and keep current — the one file under `docs/log/` Claude maintains.
- `CLAUDE.md` → `Claude LOG`: updated at the end of each stage, referencing the stage number from this
  plan.
- `docs/REFERENCES.md`: every link used as a reference.
- [`docs/NETWORK.md`](NETWORK.md): the network as built — updated in the sitting that changes a
  network-bearing slice or module, and **re-measured** with the `aws/` instruments when a `[P]` fact
  moves. It is the one file that answers *how does an app reach the internet, and what can reach it*
  without opening six slices.
- `README.md`: kept in sync with the real resource structure and repository layout.
- `docs/GENERAL_PLAN.md`: revised whenever a decision changes or a stage is re-scoped.
- The **Well-Architected Machine Learning Lens** is the per-stage checklist: when a stage is built, walk
  its questions for the components the stage touched — it is to this environment what the SRA is to the
  account structure.

---

## 5. Everything else

**`CLAUDE.md` §"What to read, and when" is the only routing table.** It lists every file in this
repository against the question that sends you to it — `docs/plan/objectives.md`,
`docs/plan/architecture.md`, `docs/plan/conventions.md`, `docs/plan/integrations.md`,
`docs/plan/cost-model.md`, `docs/plan/lessons.md`, `docs/plan/open-questions.md`,
`docs/plan/institutional-delta.md`, `docs/plan/history.md`, `docs/plan/runbooks/`, `README.md`,
`docs/GLOSSARY.md`, `docs/PRICING.md`, `docs/log/INDEX.md`.
