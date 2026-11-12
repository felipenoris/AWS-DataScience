# Log — index

One file per stage records what was done by hand, in AWS or in a sitting with no AWS call. The user and
Claude write these files cooperatively: Claude records each step of the plan it executes, in the sitting
the step ran, and the user writes whenever they want — their own acts, a correction, a measurement they
hold. A step is not finished while the log is silent about it. Plan narrative goes in
[`docs/plan/history.md`](../plan/history.md), not here.

Claude adds entries; it does not rewrite the ones already there. Not to tidy them, not as a side effect
of another task, and not because an entry looks incomplete: an amendment is a new entry that names what
it amends and why, so the record keeps the order things were learnt in. The user's words are never
edited. Entries up to Stage 4 word their provenance notes as named exceptions to an earlier rule, which
had Claude write only on request.

**Provenance** is mandatory. Every file's header states who wrote it; where one file has entries from
both hands, each entry says which, and so does anything inside an entry that came from the other hand: a
measurement quoted verbatim, an explanation added on request. A reading pasted by the user is data and
stays verbatim; what Claude adds around it is analysis and is marked as such.

Claude maintains this index too. A row changes when its log gains a kind of content the line does not
name, or an entry on another stage's subject.

One log file mirrors one stage file: `docs/log/log-stage-NN-*.md` ↔
[`docs/plan/stages/stage-NN-*.md`](../plan/stages/INDEX.md), the same slug with a `log-` prefix, so no
log file shares a filename with the plan file it mirrors. An entry goes to the log of the stage whose plan
holds the step, whichever session ran it. The `Records` column says in one line what each file holds, and
what it holds on another stage's subject, so no stage requires reading another stage's log. It restates
no entry: a log's headings are its outline.

## Reading a log

From Stage 2 on, every entry opens with a `## ` heading that carries its date and its subject, and some
logs divide an entry with `### ` headings. A log is read by its outline, then from the line of the entry,
never whole: the larger ones pass 250 KB.

```bash
L=docs/log/log-stage-09-deployment-targets.md
grep -n -E '^#{2,3} ' "$L"         # the outline: every entry's date and subject
grep -n '^## 2026-10-23' "$L"      # one day's entries
grep -n -i 'datashare' "$L"        # a subject, an identifier or an error text inside one log
grep -rn 'EXC-13' docs/log/        # which logs record an identifier
```

The logs of Stages 0 to 1d predate that convention; their rows below are their outline.

## The logs

| Stage | Log | Records |
|---|---|---|
| Stage 0 — Baseline | [log-stage-00-baseline.md](log-stage-00-baseline.md) | Management account created by hand; `aws` CLI and `terraform` installed; the pre-existing `SUSPENDED` `Sandbox` account under the root, left alone (`EXC-01`). |
| Stage 1a — Landing zone, accounts and OUs | [log-stage-01a-landing-zone.md](log-stage-01a-landing-zone.md) | Account-quota ticket (15); root MFA; the USD 50 budget; Control Tower enabled in `us-west-2`; every OU and account vend, including the refused `Identity` vend under `Security`; the access portal and the two SSO users; the break-glass chain (`awsds-org-break-glass-alerts`, `awsds-org-root-activity`, `AWS Break Glass Alert`) and its 2026-08-09 test; centralized root access and the `Delete root credentials` check. |
| Stage 1b — Identity, policies, detective controls | [log-stage-01b-identity-and-controls.md](log-stage-01b-identity-and-controls.md) | Closed 2026-08-12. The 8.3 metric filter and alarm; Identity Center delegation (step 1); the five `sso-group-*` groups (2); `InfrastructureAccess` and its assignments (3); the delegated administrator's read boundary (4); the six SSO profiles (5); the `list-identities.sh` snapshot; 5.1's retirement of the Account Factory assignments; the AZ table (6); 8.2's Access Analyzer in Audit (`awsds-org-external-access`), 35 findings, INV-16. |
| Stage 1c — Preventive policies | [log-stage-01c-preventive-policies.md](log-stage-01c-preventive-policies.md) | Closed 2026-08-14. 7.0's readings; 7.2's `enable-policy-type`; 7.4's account BPA; the 7.3 battery; 7.5's root attachments (`awsds-org-scp-baseline`, `awsds-org-scp-perimeter`); 7.6's four `awsds-org-scp-ou-*` documents probed per OU; the 7.5a/7.6a amendments; 7.7's `CT.MULTISERVICE.PV.1` and root-user controls; 7.8's RCP, declarative and tag policies, `readback.py`'s defect, and the RCP lockout of every SSO user, re-probed 93/0/0. |
| Stage 1d — Audit trail, Config scope, org-wide enablement | [log-stage-01d-org-wide-enablement.md](log-stage-01d-org-wide-enablement.md) | Complete. Step 9's Object Lock on the CloudTrail log bucket (2026-08-15: `COMPLIANCE`/90 days, INV-14, the borrowed `AWSControlTowerExecution`); step 12's `Security` OU controls probed from Log Archive and Audit; step 10's Config spend and volume readings, decisions 4 and 8; the 2026-08-14 pre-stage readings (bucket names, `CTS3PV8`, Lake Formation, trusted access); step 11's `ram enable-sharing-with-aws-organization` (INT-11). |
| Stage 2 — Terraform foundation | [log-stage-02-terraform-foundation.md](log-stage-02-terraform-foundation.md) | Closed 2026-08-16. Step 5.0's four delegation readings and the 5.1 document; open question 11 measured; steps 1, 6 and 9 (skeleton, gates, `Makefile`); steps 2 and 3 (five bootstrap applies, `check-bootstrap-parity.py`); 5.1a's narrowing; step 5 (`identity/sso/`) and 5.5 (`identity/org-policies/` adopted); step 8's D11 lifecycle targets; the Validation and the `awsds` reserved-prefix finding; verification (iii), INV-17. |
| Stage 3 — Networking | [log-stage-03-networking.md](log-stage-03-networking.md) | Closed 2026-08-16. The five execute-time decisions; step 0 (Account Factory VPCs removed); pass 1 `foundation/` in three accounts; pass 2's peerings and zone associations; pass 3 `egress/` (`vpc-egress-v0.1.0`, USD 0.480/h); the D11 `make down`/`make up` cycle; the three probe slices (perimeter, peering, INT-09, flow logs); the teardown of 59 resources; the instrument defects (`NT-3`/`NT-4`, `EG-4`, `make status`, the 404/404 pair); 2026-10-17, verification (v) read: one AZ mapping in Sandbox and Production, the hub and GitLab in `usw2-az1`, both Sandbox domains across two AZs. |
| Stage 4 — VPN access | [log-stage-04-vpn.md](log-stage-04-vpn.md) | 2026-08-16/20: step 1.3; pass 1 and the three D11 defects; decision 4 revised (Secrets Manager); 2.3's anchors; 4.3/1.4, the first boot; 4.1/4.2 (`mbp`, `raspi`, `--on-host`); pass 2 (`production/probes`, the MTU finding); pass 3 (`DenyControlPlaneOffVpn` on six sets, `CloudWatchLogsReadOnlyAccess`); the control-plane pair; verification (iii); the lifecycle cycle; the server MTU 1280; the amd64 addendum, `wireguard-v0.3.0`. |
| Stage 5a — Data foundation | [log-stage-05a-data-foundation.md](log-stage-05a-data-foundation.md) | 2026-08-18/20: the INT-11 before-reading; decisions 1-6; pass 1 (the two-step apply); pass 2 (the GM's grants); pass 3 (the shares); the propagation; 4a/4b (`consumer-data`, `DL-6`); 4c (`DataScientistAccess`, `DL-12`); the `security-zone` withdrawal; 4d's proofs, the `DenyControlPlaneOffVpn` S3-path defect and its amendment; the sample rows (`kms:GenerateDataKey`); the wrong-human sign-in; 4e; pass 6 (Security Hub CSPM, `EXC-01`); the FSBP pause of 2026-10-09 (the measured bill, the two policy shapes, `EXC-14`). |
| Stage 5b — Redshift Serverless | [log-stage-05b-redshift-serverless.md](log-stage-05b-redshift-serverless.md) | 2026-09-20 to 2026-10-21: passes 0-3 and their amendments (the free trial, the ceiling refusing, the usage limit at 10 RPU-hours, `max_query_execution_time`); the orphan secret (`EXC-12`); idleness measured; `WH-15` and `WH-6`; `EXC-13`'s first rotation; both alarms on `awsds-sandbox-alerts`. |
| Stage 6a — SageMaker Unified Studio (executed) | [log-stage-06a-unified-studio.md](log-stage-06a-unified-studio.md) | 2026-08-19/30: decisions 1, 3-5 before the stage; step 0 (flat, then rebuilt); the pull-forward audit; passes 0-2a, verification (i); the plan reviews; `images/`, `sandbox/buildbox/`; steps 1.3-1.5, 1.7 (INT-16, `grants.tf`), 5.0 (`default-v0.1.0`); pass 3's first project; the off-VPN reading; the DNS Firewall list, 4.3, the CDN finding (`EXC-05`); S3 Access Grants and the `aws:SourceVpc` swap; OQ 21/22; decision 6 dissolved; the `US-7` repair. |
| Stage 6b — `Development` becomes `Staging` | [log-stage-06b-development-becomes-staging.md](log-stage-06b-development-becomes-staging.md) | 2026-09-05/06: the preparation sitting (pass 0, auto-enrollment ON); passes 1-5 step by step: the SMUS unwind, the persona swap and lake revocation, the rename and OU move, the battery re-composed, the Recipe E migration, the token flip, three `moved {}` sets, the old state bucket destroyed, the document sweep; the Validation list; step 3.5; 6c pass 0 read against 6b. Owed: the provisioned product's parameters, Management-only. |
| Stage 6c — Networking: the single egress hub | [log-stage-06c-networking-hub.md](log-stage-06c-networking-hub.md) | 2026-09-06/08, done: passes 0-3 (three Production VPCs, INT-22, six peerings, `vpc-v0.2.0`/`v0.3.1`); pass 4's cut-over (both hub hosts, the proxy on the perimeter); pass 5 (design B, `NO_PROXY`, DNS Firewall 63→10, the buildbox moved); `EXC-04`/`05`/`06` closed; pass 7 (`hub-up`/`hub-down`, `proxy.py`); 6.1-6.7 (allow-list vs monitored, the IPv6 ULA, the ICMP rate limit); decision due 4 as (c); pass 8's split-tunnel profile. |
| Stage 6d — Unified Studio: what 6a left owed | [log-stage-06d-unified-studio-remainder.md](log-stage-06d-unified-studio-remainder.md) | 2026-09-07 to 2026-10-31: sittings one to twenty (a space under the proxy, `apt` and the Code Editor gallery, the build plane, step 8 and `PX-3`, step 4's workflow, step 2 end to end, the remote IDE, Amazon Q and step 10, the SQL surfaces, SageMaker Distribution 4.5, `default-v0.5.0`); decisions due 5, 6, 8, 11, 13, 14, 15 and 16; SMUS's October releases read against the plan; the `SageMakerAIDomain` pilot and its `VALIDATION_FAILED` environments; RStudio's prerequisites and its close as not taken. Also holds the log-debugging runbook and the Kiro login's cause. |
| Stage 6e — Claude Code on Bedrock | [log-stage-06e-claude-code-bedrock.md](log-stage-06e-claude-code-bedrock.md) | 2026-09-11 to 2026-10-20: the read-only steps; the retention mode (M1) and the use-case form (M2); `aws/bedrock.py`, `aws/bedrock-scope.py` and `aws/bedrock-usage.py`; `sandbox/bedrock/` and the `vpc-egress` tags v0.12.0 to v0.14.1; `default-v0.3.0` and `default-v0.4.0`; the first session and its refusals (`EXC-07`, `EXC-08`, `EXC-09`, `INV-18`); decisions 11 and 13 to 16; the direct API on the compute plane; the battery's rows for 7.5. |
| Stage 6f — Data governance on the SageMaker Catalog | [log-stage-06f-data-governance.md](log-stage-06f-data-governance.md) | 2026-09-12 to 2026-10-27: the portal's first database, table and data product; the stage written (`INT-23`); LF-Tags beside the catalog; `./aws/catalog.py` (`CT-1`..`CT-12`); `EXC-11`; the manage-access role's Glue policy (`sagemaker-prereqs-v0.8.0`) and the `DataLake` environments; decision 1 (b) and step 11 from 11.2 to 11.11: the publishing project, `trades` published, the subscription, its fulfilment and the read; decisions 2 to 6. |
| Stage 6g — Access to AWS by identity, and the VPN for the private network | [log-stage-06g-access-by-identity.md](log-stage-06g-access-by-identity.md) | 2026-09-17: the requirement change and the user's choices; step 0 (0.1, 0.2); 1.3's `identity/sso` and 2.3's `data-governance/data` applied, `VP-7`; decisions due 1 and 2 (`production/proxy/`, `production/networking/`, the Elastic IP released, `make hub-down`, the spoke precondition exercised); 2026-09-18: the behavioural pairs on both profiles (1.4 off the tunnel and through the proxy, 2.4's drop-box puts, the perimeter probe), a write beyond its authorization, two corrections; 2026-10-17: decision 1's host replacement still pending; 2026-10-18: verification ii and the job role's state. |
| Stage 6h — The Redshift connection | [log-stage-06h-redshift-connection.md](log-stage-06h-redshift-connection.md) | 2026-09-20 to 2026-10-21: layer 3 in SQL and layers 1-2 as code; the access role; both database users and the connection (3.2); the first write through each door (`WH-14`, `EXC-15`); decision 8a, the access-role chain; `EXC-16`; the connection's `lineageSync` (`EXC-17`, decision 3); the second project; 5.3 and 5.4 by the simulator; what AWS's managed project policy grants on the warehouse. |
| Stage 6i — Sandbox orchestration | [log-stage-06i-sandbox-orchestration.md](log-stage-06i-sandbox-orchestration.md) | 2026-10-10: pass 0 (0.1-0.4, `./aws/sandbox-orchestration.py`), pass 1 (the project in `shared/`), pass 2's refused save, the import and decision 6's `sandbox/workflows/`; 2026-10-11: pass 2's first processing job and 2.5's `sudo` probe, pass 3 (3.1-3.4), pass 4 (`demo-python-operator`, decision 7, 4.2a's refused CloudTrail Lake store), pass 5 prepared, 5.0's probe, 4.2a's trail `sandbox/endpoint-audit/` with `vpc-v0.4.0` and 4.3, pass 5 (`demo-bash-operator`, verification vii), steps 3.5-3.8 (a project with dependencies); 2026-10-12: pass 6, decisions 3-5, the trail destroyed; 2026-10-16: the Glue job's birth in `dev` and `test` (`GetAGlueJobNoProjectHolds`, its apply and run), the orphan object deleted at 23:05. |
| Stage 7 — GitLab, Runners and ECR | [log-stage-07-gitlab-runners-ecr.md](log-stage-07-gitlab-runners-ecr.md) | 2026-10-12 to 2026-10-27: pass 1's applies and GitLab's first boot (the deadlock, the host replaced); the first sign-in, SAML, the runners, the first pipeline, Pages, `default-v0.6.0`; decisions 2 to 10; the backups and their expiry; the load history of GitLab and of the build runner; 7.2 and INT-13 (issue #268); the instance settings, the usage data turned off; 8.1 to 8.3 (the cycle, the restore rehearsal, the instrument diff); `make gitlab-up`'s order; INT-09 and INT-19 from a space; `PX-3`; the stage's close. Also holds the Sandbox sitting of 2026-10-26 with its downs. |
| Stage 8 — CI/CD pipelines | [log-stage-08-cicd-pipelines.md](log-stage-08-cicd-pipelines.md) | 2026-10-12 to 2026-11-03: passes 0 to 3 (the deploy roles, image and runner; `awsds/ci-gates`, the test runner, `app-etl`'s first run; the image chain and versions 7 to 11); decisions 1 to 29; step 2.5 and the application; pass 4 from its reading to 3.8 by hand; every tag's pipeline from `v0.2.0` to `v0.4.6`, with its failures and fixes; decisions 27 and 28's legs; the deploy image on Terraform 1.16.6; `gates-v0.5.0` and `gates-v0.6.0`; the lock audits and their acceptances; the verifications answered from the trail and the simulator; decision 29 and its battery rows; the hand deletion of old image versions. Also holds Stage 9's and Stage 10's decisions as Stage 8 received them. |
| Stage 9 — Deployment target platforms | [log-stage-09-deployment-targets.md](log-stage-09-deployment-targets.md) | 2026-10-16 to 2026-10-30: pass 1 written and applied (the `Workloads` document, `production/sagemaker/`); the quotas read and requested; passes 2, 3 and 5 and decision 12 (a) applied; 5.1 as a managed policy; 6.3's debug window, and 3.1's on 2026-10-26; decisions 1 to 15; 2.4's proof job and the full-table flag (`TM-26`); the persona proofs (3.4, 5.4, 8.1 to 8.4, 2.5, 2.6); 9.1 to 9.7: the namespace, the governed schema, the DDL and the load, the datashare across three accounts and its Terraform adoption; the warehouse sittings, and xxiv's revoke and re-grant (`WH-16`); the free-trial balances. Also holds `EXC-02`'s cleanup and the first promotion's Production run. |
| Stage 10 — Workflow orchestration and promotion | [log-stage-10-orchestration-promotion.md](log-stage-10-orchestration-promotion.md) | 2026-10-18 to 2026-10-28: pass 0 and 4.3's `DenyProvisionedMwaa`; 5.3's approval rule; the service-linked role in each account; the `orchestration` module and both slices (`orchestration-v0.1.0` to `v0.2.1`); every decision; 6.2's negatives; the Staging leg by hand and the XCom encryption finding; passes 1-2 through pipeline #71 and pass 3 (the training chain, the version registered and approved, the transforms); 6.1's schedules; the verifications read from the trail, the network ACLs and the simulator (`EXC-22`); 3.5's substitution and 1.2's network negative; decision 11's narrowing; 2.1 and xxix from a space (`vpc-egress-v0.19.0`). |
| Stage 11 — Data protection and DLP | [log-stage-11-dlp.md](log-stage-11-dlp.md) | 2026-10-17 to 2026-10-22: the organization analyzer's findings triaged twice (`INV-16`, `TM-21`, `EXC-18`); `TM-21`'s narrowing (`sagemaker-prereqs-v0.6.0`) chosen, applied and read back; pass 0's readings; `DP-8`; pass 1 written and stopped before the apply; decision 12's RLS policies and the mechanisms of `TM-22`..`TM-24`; 5.1's map and 5.2's PKI key alarm. |
| Stage 12 — Observability, governance and FinOps | [log-stage-12-observability-finops.md](log-stage-12-observability-finops.md) | 2026-10-14 to 2026-11-10: step 10's first runs; the `[P]` slices, the quotas and the bill; `sandbox/observability` and its confirmed subscription (`OB-3`, `EXC-19`); 6.1's Config reading; 5.2 against the bill; 8.5, the internal CA root's rotation; the `EC2 - Other` line by usage type; 5.3: GitLab's data volume shrunk to 20 GiB, the restore, the `gitlab.rb` deprecations and the orphan snapshots deleted. |
| Stage 13 — Public-facing web tier | — | *no entries yet* |
| Stage 14 — Per-business-unit Sandbox vending | [log-stage-14-sandbox-vending.md](log-stage-14-sandbox-vending.md) | 2026-10-18, the environment down: `./aws/vending.py`'s first readings of the hand-built unit (nine passes, one note), the negative control on `Staging Account` (four failures), 44 fabricated cases, `ListAccountAssignmentsForPrincipal` answering from the delegated administrator, the unit's billable objects at rest; 2026-10-20: every infrastructure profile's VPCs in `us-west-2` (no default VPC, nothing in `172.31.0.0/16`) and the organization's account states (`EXC-01`'s `Sandbox` reads `SUSPENDED` / `CLOSED`); 2026-10-21, PR #230's sitting of 2026-10-20 recorded, no AWS call: `EXC-01`'s slot and its inferred departure, 2026-10-30 to 2026-11-09, and `VN-1`'s citation. |
| Stage 15 — GuardDuty org-wide | [log-stage-15-guardduty.md](log-stage-15-guardduty.md) | 2026-10-20, the before of step 1, every call a read: `./aws/guardduty.py` (no detector in the five profiled accounts, no delegated administrator; run on the script brought to decision 4, its `GD-3` change exercised on fabricated documents only), trusted access without `guardduty` (`INV-09` holds), the root's four policy types without `GUARDDUTY_POLICY`, no GuardDuty service-linked role; 2026-10-21, PR #227's sitting of 2026-10-20 recorded, no AWS call: the Malware Protection service-linked role and both roles' managed policies (decision 1 (c) unchanged), the `AI_ANALYST` feature no member call or policy names, `GD-3`'s message. |
| Stage 16 — The sandbox lake | [log-stage-16-sandbox-lake.md](log-stage-16-sandbox-lake.md) | 2026-08-26, the whole stage in four sittings: the three applies and the Lake Formation admin-seat finding (`v0.4.0` → `v0.5.0`); the contrast pair and the laptop test; the project wiring (the connection form, the CloudTrail both-doors reading, the notebook readings, the auto-vend plugin); the revoke exercise (`SL-4`'s defect, the ≤19 s vend-door window, the bearer residual). |
| Stage 17 — Machine learning in a Sandbox project | [log-stage-17-sandbox-machine-learning.md](log-stage-17-sandbox-machine-learning.md) | 2026-10-17 to 2026-10-21: pass 0 (`./aws/sandbox-ml.py`, `ML-1`..`ML-9`, the three quotas and their requests); pass 1 (`vpc-egress-v0.18.0`, `MLflowApp`, decision 4, the greyed-out *Create MLflow App* and its cause, `ml-demo-mlflow` by `create-environment`); 7.0a and 7.0b (`sagemaker-prereqs-v0.7.0`); decision 13 (b): the governance project, `sandbox/model-access/` and the five models enabled; decision 11's amendment and the battery's two halves; 7.3's two chats; `bedrock-usage.py` taught application inference profiles. |
| Stage 18 — A deployment-only SageMaker project in Staging | [log-stage-18-staging-deployment-project.md](log-stage-18-staging-deployment-project.md) | 2026-10-17 to 2026-10-22: the stage written; pass 0's readings; passes 1 and 2 (the applies by the user's hand, the association, `EXC-20`, the profile and its grant); the project and what provisioning left; pass 4: the CLI's deploy, the workflows grant, the run `SUCCESS`; pass 5: the second application; 7.1's lineage; 7.2's `DataLake` environment, table, publication, subscription and read; 6.1 and 6.2: a person's membership, `aws:SourceIdentity` and the deny; decisions 4 to 18; pass 8: every object removed, the battery, the spend; the verdict, D41 item 2 kept. |
| Stage 19 — A data product on SMUS's native path | [log-stage-19-smus-native-data-product.md](log-stage-19-smus-native-data-product.md) | 2026-10-28 to 2026-11-12: the stage written from read-only measurements (the catalog across the plan and the estate); decision 6 (b) and every decision to 21; 1.1 in `examples/app-etl/`; pass 1's preparation (the `StartDataSourceRun` grant, decision 10's OpenLineage settings, the form type `classification`) and its window: four runs, `SUP-343`, `SUP-345`, `SUP-346` to `SUP-348`, the readings after it; `TM-29` and `CT-13`; pass 4 with nothing up: the `Workloads` SCP on a candidate and applied, both targets associated, both `studio/` slices, the deployment profiles, `deploy-staging` and `deploy-production`, the grants, decision 21's fence (`sagemaker-prereqs-v0.10.0`, `DT-14`), `TM-30`; release T written; the user's acts of 2026-11-12 read back: the full-table flag off in both targets (`DT-13` passing) and `awsds-deploy-staging` an owner of `deploy-staging`; release F written with nothing up (the chain layer, the template's stages and legs, decisions 22 to 24, each taken as (a)) and its grants in the `studio/`, `foundation/` and `production/warehouse/` slices applied and read back; the lint's pull request opened in `awsds-workflows`. Also holds a GitLab credential printed by a keychain probe (2026-11-08) and what the app's classifier refused on 2026-11-11. |

## How an entry gets written

Claude writes into a `docs/log/log-stage-*` file as part of executing a step, and the user writes
whenever they want. The modes below decide who holds the pen, never what is allowed.

| Mode | When it is the right one |
|---|---|
| **Claude writes the file directly** | The default, for an act Claude ran or observed: a reading, an apply, a write, a measurement. It lands as the step closes, and Claude says in chat what it wrote |
| **Claude drafts, the user pastes** | The entry is about acts Claude did not observe, or the user wants the file to stay in their hand. The draft goes to the chat as one fenced block, so it is pasted untouched |
| **The user writes** | Their own acts and corrections, and any measurement they want kept verbatim. Claude reads what is there and builds on it rather than restating it |

In every mode the entry names its hands (see Provenance above) and follows the rules below. A sitting
with no AWS call — a vendor page read, a pass written, the plan revised — gets an entry too, and its
provenance note says so: the 2026-09-18 entry on step 3.1's documentation half in
[`log-stage-06f-data-governance.md`](log-stage-06f-data-governance.md) is the wording to copy.

- **English and Markdown** in every mode; the chat is in Portuguese and these files are not. In the
  drafting mode, one fenced code block and never chat prose: a ` ```markdown ` fence, or a longer outer
  fence (` ````markdown `) when the draft itself contains one.
- **No identifiers.** An account id becomes the account's AWS `Account.Name` in angle brackets
  (`<Audit Account>`, `<Sandbox Account 1>`, `<Management Account>`); the names are in
  [`docs/ORGANIZATION.md`](../ORGANIZATION.md), and which id is which account is resolved from the
  entry's own surrounding text or from `aws/output/`, never guessed. An e-mail address inside an ARN
  becomes that user's role (`<control tower admin user>`). Nothing else in a pasted output is touched:
  the `AWSReservedSSO_*` suffixes, the policy, organization and root ids, the error wording and the
  encoded authorization failure blobs stay verbatim. The entry declares the substitution once, in its
  provenance note; the tenth entry of [`log-stage-04-vpn.md`](log-stage-04-vpn.md) is the wording to
  copy.
- **Concise:** the command, the outcome, and any finding that survives nowhere else. Leave out what
  `aws/output/` holds (regenerated on demand), what a `docs/plan/` file explains, and the reasoning
  behind a choice. The log carries what happened, in order.

`./scripts/check-identifiers.py` gates the identifier rule: it runs in `make check` and in `pre-commit`
over every tracked file and fails on a standalone twelve-digit number or an e-mail address. It was added
on 2026-08-17 after three log files were found holding twenty-four ids and two addresses (Lesson 14). It
cannot reach git history and cannot decide which account an id belongs to. A hit inside an existing entry
is still an edit to a stage log, so it waits for the user's request; the gate names the line, it does not
authorise the fix.

**Adding a stage log:** the user creates `docs/log/log-<same-filename-as-the-stage-file>` and copies the
two-line header from an existing one; Claude replaces that stage's `—` above with the link and a
one-line `Records` summary: the span of dates, the kinds of content, and anything the file holds on
another stage's subject.

**Not in these files:** break-glass use is recorded here (date, reason, actions), but the procedure is
[`docs/plan/runbooks/break-glass.md`](../plan/runbooks/break-glass.md); why the plan changed is
[`docs/plan/history.md`](../plan/history.md).

---

*Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md) · Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md)*
