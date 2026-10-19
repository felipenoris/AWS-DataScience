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
| [4 — VPN](plan/stages/stage-04-vpn.md) | WireGuard over the Stage 3 network, the only entry point to the private network; step 8's control-plane deny is retired by D39 and removed at Stage 6g | **DONE 2026-08-18 — closed by the GuardDuty split**: passes 1-3 executed and measured; pass 4 left the stage whole for Stage 15, prepared. Decision 4 (third review) moved the host private key into a `[P]` Secrets Manager secret, with [`docs/plan/runbooks/vpn.md`](plan/runbooks/vpn.md) Part K owning every key event; `sandbox/vpn/` was the tree's first `[D]` slice; the close-out log entry is the user's |
| [5a — Data foundation](plan/stages/stage-05a-data-foundation.md) | Lake, Glue, Iceberg, Lake Formation + the three cross-account shares; Security Hub on | **DONE — every pass, 2026-08-18/20**: the governed lake, the governance manager's grants, both cross-account TBAC shares, the consumer side (one `consumer-data` module in two slices — v0.2.0 since the 2026-08-19 revision that withdrew `security-zone`), 4c's persona grants, **4d's behavioural proofs, 4e's `DenyUserCompute` amendment, and pass 6** (Security Hub CSPM org-wide by central configuration on the root, 2026-08-20 — `INV-09` to nine/four). **Two things stay open**: 13.3's triage, which needs a first FSBP report that did not exist when the stage closed, and open question 19, the crawler demander, which no proof can settle. The 2026-08-17 data-governance review added the `zone` tag dimension and classification-scoped LF-TBAC grants (`restricted` by explicit grant only), and withdrew the NFS requirement the same day — no `nfs/` slice (D24 withdrawn) |
| [5b — Redshift Serverless](plan/stages/stage-05b-redshift-serverless.md) | The warehouse beside the lake: one namespace and workgroup in `Sandbox` at **4 base RPUs**, its cost ceiling and audit trail in the same apply, and the access model for both classes of database | **passes 0-3 applied 2026-09-20**; owed: the bill's half of verification x after the free trial ends (2026-12-19), with the compute up whether `max_query_execution_time` binds anyone and the `enable_large_strings_opt_in` re-plan, and `EXC-13`'s first rotation, read after 2026-10-20 01:59:59Z. Written 2026-09-19 under **D40**, which admits a warehouse built by hand and keeps the `RedshiftServerless` blueprint disabled; the requirement reached `objectives.md` on 2026-09-20 and settled four readings D40 had made alone, the load-bearing one being that **where the databases live is an implementation matter**, which legalises the two-account split. Priced: **0.36 USD/RPU-hour**, so 4 RPUs is **1.44 USD per query-hour** and **0.00 at rest** — the most expensive object per unit of time in the estate, which is why the usage limit (`breach_action = deactivate`) lands with the workgroup rather than at Stage 12. Two findings shape it: the **ratchet** past 4 RPUs never comes back down, and the provider documentation demands three AZs where the service documents two while validating nothing |
| [6a — Unified Studio (executed)](plan/stages/stage-06a-unified-studio.md) | The record of what ran: the domain, both associations, 11 blueprint configurations and 22 grants per member, both project profiles, the create path end to end, `default-v0.1.0`, and the dated readings of passes 4-5 | **CLOSED as a record 2026-09-05** |
| [6b — `Development` becomes `Staging`](plan/stages/stage-06b-development-becomes-staging.md) | One account changes role: the SMUS surface unwound inside `Interactive`, the lake share and the read-write persona revoked, the rename and the OU move, the tree migrated to `staging/` | **DONE 2026-09-06** — every pass in one day; the VPC's CIDR and both `[P]` gateway-endpoint ids survived, `10.40.0.0/16` is free for 6c, and 3.5 closed the same day with the answer that the provisioned product does not follow an out-of-band rename and cannot be made to — a permanent divergence, treated as D32 treats the direct assignment |
| [6c — Networking: the single egress hub](plan/stages/stage-06c-networking-hub.md) | Three VPCs in Production, five peerings, the `awsds.internal` family, WireGuard and Squid as two `[D]` hosts, **zero NAT gateways**, no default route in any spoke — and the client plane moved off the compute plane's resolver. Writes **D38** | **DONE 2026-09-08, pass 8 included** — the second client profile: the split-tunnel profile beside the monitored one, laptop-only, no host change, measured the same night. Passes 0-7: pass 6 closed with 6.5 (two doors by service family, the union trimmed, `sandbox/foundation` unfrozen, `sandbox/vpn/` retired) and 6.6 (INT-16 accepted, then superseded by D39, which removed the requirement it deviated from); decision due 4 taken as (c): the access log's export waits for Stage 11 step 5.1, the organization trail records any deletion meanwhile |
| [6d — Unified Studio: the remainder](plan/stages/stage-06d-unified-studio-remainder.md) | The deny pair exercised, the house image selectable, a session measured under the proxy, the workflow surface measured, the lifecycle proven, the remote-IDE channel opened | **in progress** — steps 3, 4, 8 and 9 closed (8.8's `staging/egress` tail owed); step 2 closed 2026-09-10, the house image at version 9 (`default-v0.8.0-7c59998c`) since 2026-10-16; step 4 closed 2026-10-18 when the D28 lint refused the portal's four definitions; 5.2 and 5.4 answered by reading. Owed: 1.1/1.2's persona attempts (1.2 reads an implicit deny), 2.4's after half (a reconciliation that writes the domain; the 2026-10-11 one did not), 5.1's threshold, 6.1's (viii), (xvi) and (xvii), 7.5's monitored half, 7.6, 7.7, step 10. Decision due 4 keeps the connection method and the file channel; D39 dissolved its VPN half |
| [6e — Claude Code on Bedrock](plan/stages/stage-06e-claude-code-bedrock.md) | A coding assistant in a Sandbox space answered by Amazon Bedrock inside the estate's perimeter: the model-access form, the inference-profile pins, the endpoint that keeps the call off the proxy, and the data-protection answer written down | **in progress since 2026-09-11** — a session answered from a space on 2026-09-12: Haiku 4.5, the project role, through the `bedrock-runtime` endpoint, the proxy log silent on Bedrock. The scoped set is the 4.5 generation (decision 14; `claude-opus-5` and `claude-sonnet-5` are refused for this account, `EXC-08`), the Region exemption carries its compensating deny (15), and `mode: none` is declared in all 17 enabled Regions (16) and frozen by 7.5. The SCP battery's rows for the new statements ran 2026-10-17, each as expected. Owed: 8.3's budget notification (decision 6), 6.4's token volume, decisions 11 and 13 |
| [6f — Data governance](plan/stages/stage-06f-data-governance.md) | The SageMaker Catalog over the governed lake: subscription and Share measured, the lake's way into the catalog, approvals, AI-generated metadata, and Production publishing through the lake rather than an association | in progress — step 1 done and the read-only readings of 2026-09-18 and 2026-10-18 taken (`./aws/catalog.py`, `CT-7`: the catalog road has not reached the lake); 5.1, 6.1 and 6.2 answered, `EXC-11` counted at two failing `Tooling` sources, decision 5's DataZone half read; no subscription or Share has run, five decisions are open and step 2 is the user's portal acts; `INT-23` is new; decision due 3's last input read 2026-10-18: no IAM condition key reaches business-name generation |
| [6g — Access by identity](plan/stages/stage-06g-access-by-identity.md) | D39 executed: the persona deny deleted from the six permission sets, the lake's laptop branch turned into a principal branch on the drop-box, and the instruments, runbooks and documents that described the previous perimeter | **in progress** — written and applied 2026-09-17: the deny deleted from the six persona sets and the lake's laptop branch turned into a principal branch, both re-planning `No changes` and read back (`INV-19`); `VP-7` inverted, `PX-5` retired. Decisions 1 and 2 taken and applied the same day: the proxy wears its instance's own address (`184.33.8.126` released) and `make up` refuses on the proxy alone. 1.4 and 2.4 measured from the laptop 2026-09-18 — `describe-log-groups` answers, `list-buckets` is now an implicit deny, the drop-box took the persona's `PutObject` by principal on either path. 1.4 is closed on both profiles; owed: 2.4's Athena read from a space, refused as written because the project role holds no Lake Formation grant on the lake, and decision 1's pending replacement of the proxy host, in a hub session; verification ii answered by reading 2026-10-18 |
| [6h — The Redshift connection](plan/stages/stage-06h-redshift-connection.md) | The first sandbox **schema** and the first SMUS compute connection: write for one project on one themed schema, which several projects may share | **in progress** — passes 0-2 done 2026-09-20 to 2026-10-10: the project writes and reads `lab` through both doors, the Data page and JupyterLab over `5439`, each layer read back on its own. *Per database × project* is **three layers in three systems** — a tag on the workgroup **and** its namespace, an IAM policy, a Redshift `GRANT` — and the portal adds a per-project **access role** whose `RedshiftDbUser` tag names the database user. A direct notebook session lands on a per-person user holding nothing, so a notebook chains through the access role (decision 8a). Owed: step 5's negatives (5.1 and 5.2b from `test-experimentation`, a second project since 2026-10-15 in no map), 0.4's portal half, 6.4, and decision 3, re-opened 2026-10-18 by the connection's `lineageSync`, on a daily schedule the form never showed; the audit export carries nothing while a workgroup exists (`EXC-16`); 5.3 and 5.4 simulated as designed on 2026-10-18, the refusals' wording owed, and AWS's managed project policy grants layer 2 through layer 1's tag, an input to decision 8 (PR #187) |
| [6i — Sandbox orchestration](plan/stages/stage-06i-sandbox-orchestration.md) | A MWAA Serverless workflow inside a Sandbox project: a sensor on `shared/`, a Python project's command run in the house image as a SageMaker processing job, the source removed by the workflow; then `PythonOperator` and `BashOperator` on the worker | **DONE 2026-10-12** — every pass, 3b included: the processing workflow runs end to end, a project with vendored dependencies included, with one `[P]` grant slice, `sandbox/workflows/` (decision 6), and a `PythonOperator` with a code archive ran once decision 7 put the service's code-snapshot bucket on the S3 gateway endpoint's list (`vpc-v0.4.0`, measured by a trail, `sandbox/endpoint-audit/`, destroyed at the close). The four workflows are kept (decision 5) and their log groups sit under `EXC-10` (decision 3). Written 2026-10-10. Everything stays in the project (one role, the project key, `shared/`), and the job carries the four settings the D13 boundary demands, so the container has no network and the workflow, not the code, deletes the source. It took Stage 10's Sandbox measurements: verifications (i) and (xv) and the CLI half of step 0.2 |
| [7 — GitLab, Runners, ECR](plan/stages/stage-07-gitlab-runners-ecr.md) | GitLab CE on EC2, runners, registries, the `awsds.internal` names and TLS from the internal CA — all in `VPC-SharedServices`, all reaching the internet through the proxy | **in progress — passes 1-2 closed but for 3.5's three persona memberships, and pass 3 nearly so, 2026-10-12**: the anchors, the SharedServices `egress/` (12 endpoints since decision 9), the internal CA (`production/pki/`), GitLab's `[D]` host with SAML, `registry/` 5.b, the build runner as a protected project runner, the first pipeline (the cache's first pull with no route, BuildKit rootless without privileged mode), Pages, and `default-v0.6.0` built by a pipeline and registered as Sandbox's image version 6; the buildbox retired (6.5); owed: INT-09's clone from a notebook on the house image (no space uses it; versions 7-9 exist), 3.5's memberships, pass 4 (8.1-8.3); step 8.4 is done (`SC-11` reads the deployed `gitlab.rb`, 2026-10-18); the GitLab backups leave the bucket on 2026-11-13 and 2026-11-15. Before: on the build plane, which is `open`; GitLab gets lifecycle targets of its own because `ENV=production` starts and stops the hub, and its configuration travels outside its user data (Lesson 64); the CA-root rebuild is `default-v0.6.0`; CodeArtifact has no consumer (decision 6); the buildbox retires into the build runner; pass 0 is already applied |
| [8 — CI/CD pipelines](plan/stages/stage-08-cicd-pipelines.md) | The three pipeline types and the promotion gate | **in progress since 2026-10-12** — pass 0 read, step 6.2's offline-gates workflow proven, pass 1 applied (three deploy roles, a fourth at 2.5a, the runner's anchors, two alerts topics, the deploy runner), and pass 2 done (the gates in `awsds/ci-gates`, the ECR scan informative by the user's amendment of decision 1, the `app-etl` template and its first release, the test runner, one Sandbox run); the engineering apply moved to `sandbox/app/app-etl/` behind `layers.py` refusals 7 and 8, retired by decision 21 (2026-10-16); the dev-env chain ends at the image version and the domain writes stay the steward's; the scan gate is a delta over the SageMaker Distribution's inherited findings; the **D28 workflow lint is authored here** with 6d's and 6i's rules; `app-etl` becomes a SageMaker application with a manifest, deployed to the `test` project and bundled by the CI/CD CLI (D41, step 2.5); read 2026-10-18 with the environment down: the four deploy roles 0 FAILED, `awsds-deploy-sandbox-test` held to the `test` project by the simulator and never used, no service-issued `UpdateDomain`, the 72-name `NO_PROXY` literal proposed under `gitlab/` for the next release, verification xiv answered at `3c1708e`; 5.6 says clause by clause what the pinned lint enforces and who owns each gap (PR #186): the template's line passes `--image-repository` and the ceiling's seven instance types, GitLab's copy waiting on the user's push; the volume key is Stage 10 2.3's promoted mode, and the `VersionId`, the manifest comparison and the non-processing operators have no rule (Stage 10 2.4, 5.1); `staging/probes/` retired with no state (3.1); verification xxi's simulator half answered; `awsds/infrastructure` has had no reader since decision 18, and whether pass 4's promotion jobs read it or it is retired is decision 2's open question, the user's; 3.0's first half, Staging's pull grant on `app-etl`, applied 2026-10-19 in Stage 18's window |
| [9 — Deployment targets](plan/stages/stage-09-deployment-targets.md) | Staging and Production platforms, Model Registry, the producer path, the governed Redshift warehouse | **pass 1 applied 2026-10-18** — the `Workloads` OU SCP's job settings and serverless deny (the battery after the apply 39/0/7) and `production/sagemaker/` (16 resources); `VPC-Workloads`' endpoints raised by the next Production `make up`; Production's and Staging's SageMaker processing quotas read 0; pass 2 waits on decision 3. The job settings bind the caller of `Create*Job`, so they went to the `Workloads` OU SCP (3.5); the lake trusts `VPC-Workloads`' gateway endpoint; this stage authors the workgroups and results buckets `consumer-data` dropped; step 9 copies the Sandbox warehouse with 5b's and 6h's readings; verification viii answered 2026-10-18, 6b step 2.1's assignment unchanged (PR #188); the battery owes rows for a job naming its types as a preference list, before any SageMaker job runs in `Workloads` (3.5, PR #189) |
| [10 — Orchestration](plan/stages/stage-10-orchestration-promotion.md) | One orchestrator (MWAA Serverless), end-to-end promotion, the model chain | pass 0 read and step 4.3's `DenyProvisionedMwaa` applied 2026-10-18 (the root baseline's thirteenth statement, read `DENY-SCP`); passes 1-2 after Stage 9 with Stage 8's pass 4, and after Stage 18's verdict — one design in **two accounts**, Staging first, on **private routing** with no internet path (D38's first named exception); 6i's measurements remove the endpoint duplication and make the deploy role the saver; Production cannot post lineage under `DenyDataZoneEntirely`; since D41 the workflow is born in the application repository, reaches the `dev` and `test` projects by the CI/CD CLI and Staging and Production by its bundle, and a chain's state machine and schedule start it (design B built as the layer above, not as a replacement); 5.3's `awsds-prod-model-approval` written, planned and applied 2026-10-18 (2 added, `OR-4` passing), xxvii's first clause answered offline, and the pinned lint's gaps owned by 2.3, 2.4 and 5.1 (PR #188); 1.2's `vpc-v0.4.0` on `staging/foundation/` applied 2026-10-19 in Stage 18's window |
| [11 — DLP](plan/stages/stage-11-dlp.md) | Macie, the LF data cells filters, the Access Analyzer collection, data-event trails and exfiltration alarms, GuardDuty's paid features — and the threat model, [`docs/plan/threat-model.md`](plan/threat-model.md). Also the client plane's egress control: the single-egress HTTP/HTTPS proxy of the objectives clarification (D38 owns its topology, closing open question 23) | **in progress since 2026-10-17** — pass 0's readings taken 2026-10-18 (`TM-17`'s identity half: the project role's managed policy admits `sqs:SendMessage` to other accounts' `airflow-celery-*` queues); `TM-21` applied 2026-10-19 with Stage 17's 1.3, its finding's `RESOLVED` unread; pass 1's filters written, creating nothing until decision 12 names the filtered principal; `./aws/dlp.py` gained `DP-8`; in the action-checklist format; `TM-22`..`TM-24` carry the three channels the upstream readings of 2026-10-18 opened, and decision 13 the warehouse's query record |
| [12 — Observability and FinOps](plan/stages/stage-12-observability-finops.md) | Dashboards, alarms, retention, cost attribution against the real bill, backup and recoverability, quota alarms | **in progress since 2026-10-18** — the observability `[P]` slices applied in Production (the hub dashboard with its panels, the proxy's refusal alarm, a quota alarm, `awsds-prod-alerts` admitting CloudWatch) and in Sandbox (the topic `awsds-sandbox-alerts`, its e-mail subscription confirmed by the user on 2026-10-19, a dashboard, five quota alarms); the bill read from the accounts with a profile, **at least USD 53.31 in August and 74.48 in September against D12's 50**, and `cost-model.md` rewritten from it. Owed: the `[D]` hosts' alarm actions at a hub session, decision due 1, and D12's fired revision trigger, the user's |
| [13 — Public web tier](plan/stages/stage-13-public-web-tier.md) | The public-facing experiment in front of a private backend — **and the only stage with public DNS** (D15 phase 2) | not started — the ALB lands in `VPC-Networking`'s public tier as the estate's **second world-open listener**, which is what first tests 6c's single-ingress gate (`vpn.py` `VP-3`, taught the second at 2.4); the backend is reached as **IP targets over the peering** |
| [14 — Sandbox vending](plan/stages/stage-14-sandbox-vending.md) | A business unit's `Sandbox` account from one name (D35) | **the pre-vend half done 2026-10-18** — `./aws/vending.py` (`VN-1`..`VN-6`) read the hand-built unit as nine passes and one note, and a unit is priced at 3.50 USD/month at rest and 0.180/h working; the rest **blocked on the account quota**. Its central question, where the VPN terminates, was **closed without N** by D38: a designated hub. Each vend still owes a CIDR, **two** peering pairs, one child zone and one proxy source block — all generated from 6c's map |
| [15 — GuardDuty org-wide](plan/stages/stage-15-guardduty.md) | Threat detection over the whole organization — delegation to Audit, auto-enable `ALL`, every optional plan switched off (they arrive ON), findings routed to a human through a topic of its own in Audit | not started — created 2026-08-18 by splitting Stage 4's pass 4 out whole; nothing blocks it, and it gates Stage 11 step 4 (a month of billing) and Stage 5a step 13.2's ingestion; decision 4 weighs the Organizations policy type of 2026-10-01 against the console acts (PR #189) |
| [16 — Sandbox lake](plan/stages/stage-16-sandbox-lake.md) | The fourth Sandbox bucket, `awsds-sandbox-lake` — **permanent** per-SSO-group artifacts, mounted into SMUS projects via the portal's S3 connection, vended to laptops via S3 Access Grants; a compensated shadow lake, its trade argued in the institutional-delta row | **DONE (2026-08-26, created and closed in one day)** — applied (`12 added`, re-plan `No changes`), then measured from every side: the three-layer refusal contrast, the unchanged `s3-read-write` run with the KMS half closed, the connection's both-doors CloudTrail reading, and the finding that the SMUS image **auto-vends** "direct" S3 calls (the in-image direct-refusal test is unrunnable; the laptop is that control's home). Pass 6 measured revocation: the vend door closes between **+1 s and +19 s** of the delete, issued bearers live to their own expiry; `SL-4` hardened by its first live anomaly. The Lake Formation admin-seat finding settled as `consumer-data-v0.5.0` + `DL-13` (OQ 24 keeps the governance half). Log written ([log](log/log-stage-16-sandbox-lake.md)) |
| [17 — Sandbox machine learning](plan/stages/stage-17-sandbox-machine-learning.md) | The portal's AI/ML menu exercised once each inside the Sandbox project — an MLflow App, a training job under the D13 boundary, a registry version, a real-time endpoint deleted in the sitting, a batch transform, an ML pipeline — and the Generative AI apps over the scoped models, a chat agent over a knowledge base among them; HyperPod and Partner AI apps read only | pass 0 in progress — `./aws/sandbox-ml.py` and `examples/sandbox-ml/` written 2026-10-17, and the instrument's first run that evening read the training, endpoint and transform quotas of the exercise's types at zero, and its second and third, on 2026-10-18 (the third at 19:51 UTC, the environment down), at 20, 8 and 8 with the increase requests still open; XGBoost `3.0-5` for the recipe's `1.7-1`; pass 1 merged in PR #157 on 2026-10-18 before any release, tagged and planned, not applied, `vpc-egress-v0.18.0`'s `mlflow` group and `sagemaker-prereqs-v0.5.0`'s `MLflowApp`: `main` pins both, so a session raised from it reads `DE-3` and `DE-5` red until the image carrying the next `NO_PROXY` literal ships (decision 4, taken 2026-10-18), and `DE-5` reads red with the environment down too since PR #172 put that literal under `gitlab/`, and `sandbox/sagemaker` pins `sagemaker-prereqs-v0.6.0` since #166, so step 1.3's apply also carried Stage 11's `TM-21`: 1.1 read and 1.3 applied by the user on 2026-10-19, both slices re-planned `No changes`; 1.5 read why the portal still greys out *Create MLflow App* (the entry reads Data Governance's blueprint configurations, which D22 keeps empty), and the user created the app `ml-demo-mlflow` through `create-environment` the same morning, `ML-2` read (1.7); the plan was written 2026-10-12 with no AWS reading. `MLflowApp` and `AmazonBedrockKnowledgeBase` leave category 2 (the second at steps 7.0a and 7.0b), `vpc-egress` gets an `mlflow` endpoint group and the Bedrock SCP admits the embeddings model; `sandbox/ml/` is written only if a training job measures 6i's tag gap. It reads the serverless-inference question Stage 9 3.7 named, which that stage decided on 2026-10-16 as (b), and gives the Model Registry the first version `EXC-11` waits for; decisions 1-3 taken 2026-10-12; pass 2's training job waits on the battery's instance-preference rows, and 1.7 reads whether the app carries the project key (PR #190) |
| [18 — Staging deployment project](plan/stages/stage-18-staging-deployment-project.md) | A deployment-only SageMaker project in Staging, the CI/CD CLI deploying two applications into it from their bundles, read against the perimeter and unwound | pass 0 in progress since 2026-10-18 — 0.2, 0.3 and 0.4's reads taken with the environment down, 2.3's list written with no row, 5.4's quotas read; **written 2026-10-17**, the user's choice to measure D41 item 2's alternative before Stage 10 builds the item; D41 stands until the verdict; its Prerequisites name 4.4's two changes from later passes, Stage 8 3.0's first half and Stage 10 1.2's `vpc-v0.4.0`, neither applied (PR #188); decision 1 gains a custom Tooling blueprint as a third candidate, and 4.3's deploy role holds the DataZone reads the CLI's network fallback needs (PR #190); pass 1 and 2.5's first half applied 2026-10-19 by the user's hand (the classifier refuses these applies to Claude), the carve-out live (`EXC-20`), `staging/studio/`'s prerequisites in place; 2.1 done and read back, 2.3's rows written, 2.5's second half applied by the user, 4.4's two prerequisites applied, 2.6 and 2.7 applied, the `deployment` profile and its grant, and pass 3 done: `deploy-staging` provisioned with no SageMaker AI domain, the two SMUS roles Staging's Lake Formation admins; question i read from the two bases' templates (`ToolingLite` creates a SageMaker AI domain unconditionally, `Tooling` only with `enableSpaces` true), so decision 1 recommends `Tooling` with spaces off |

---

## 3. Decisions

**D1-D41, all settled** — **D30 settled as a revert** and keeps its file so the record shows what was
tried. **D40 (2026-09-19)** admits a Redshift Serverless warehouse built by hand, at 4 base RPUs, and keeps
the `RedshiftServerless` blueprint disabled: what D26 and D12 refused was a warehouse any project member
could provision in one click. **D41 (2026-10-15)** makes the SageMaker application the deployable unit:
the CI/CD CLI deploys it between the Sandbox projects and makes the bundle, the pipeline deploys the
bundle to Staging and Production, and a Step Functions state machine per chain with an EventBridge
Scheduler schedule starts the workflows (D7, D26 and D28 amended in place). One file each, with its reasoning, consequences and revision trigger:
[`docs/plan/decisions/INDEX.md`](plan/decisions/INDEX.md) — a one-line summary per decision, usually all
that is needed.

The load-bearing few, for orientation: **D11** (pay nothing while idle — three layers), **D13** (Lake
Formation is only real if execution roles hold no S3 on registered prefixes), **D17** (interactive compute
only in Sandbox; **D21 superseded** by its own larger branch, 2026-09-05), **D38** (one egress, an explicit
proxy, and where the client plane resolves), **D39** (a person reaches AWS by identity; the VPN reaches
the private network), **D22** (the lake is on the ownership axis), **D26** (one
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
`docs/plan/institutional-delta.md`, `docs/plan/threat-model.md`, `docs/plan/waiting-on-the-user.md`,
`docs/plan/upstream-releases.md`, `docs/plan/history.md`,
`docs/plan/runbooks/`, `README.md`, `docs/GLOSSARY.md`, `docs/PRICING.md`, `docs/log/INDEX.md`.
