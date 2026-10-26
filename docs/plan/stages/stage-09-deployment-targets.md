# Stage 9 — Deployment target platforms, producer path

| | |
|---|---|
| **Status** | **pass 0 read and pass 1 applied on 2026-10-18** ([the log](../../log/log-stage-09-deployment-targets.md)), from a laptop session as the infrastructure user: the `Workloads` OU document's job settings and serverless deny (9 statements, the battery's `ou` phase after the apply 39 as expected, 0 unexpected, 7 not measured, `DT-11` passing) and `production/sagemaker/` (16 resources, re-plan `No changes`); `production/workloads-egress/`'s endpoints and DNS Firewall raised by each Production `make up` since 2026-10-23 (seven endpoints with decision 12 (a), 16 to add). Decisions 4, 9 (a), 10 and 3.7 (b) taken as recommended. Verification viii is answered, its assignment half by `./aws/list-identities.py` and the Identity account's CloudTrail (2026-10-18). 3.5's instance-preference rows ran on 2026-10-22 in Stage 18's 8.7 battery, each as expected. **The processing-job quotas of `ml.m5.large`, `ml.m5.xlarge` and `ml.m5.2xlarge` read 0 in Production and Staging** (2026-10-18, Production's again on 2026-10-20); `ml.t3.medium`, the type `app-etl`'s `process` task names, reads 4 in both, AWS's default (Production's re-read 2026-10-20, no increase requested), and Staging's first SageMaker job ran on it on 2026-10-19, `app-etl-20261019T205205` ([Stage 18](stage-18-staging-deployment-project.md) 4.4), refused by no statement of the `Workloads` document. Production's training quotas read 0 for every type inside the ceiling that has one (2026-10-20, 3.5). Pass 2 waited on decision 3. **Prepared 2026-10-22 with the environment down** (the log): Stage 8's decision of that day makes this stage's `awsds-<env>-job-exec` the job role in Staging and Production, so 4.3's `staging/sagemaker/` stands before Stage 8's pass 4; 4.3a re-cuts `staging/egress/` to `VPC-Workloads`' endpoint set (planned, 16 to add with decision 12 (a)); `production/sagemaker/`'s job role gains `glue:GetConnection`; and `./aws/deploytargets.py` reads each pass from its own objects, 0 failed and 8 notes where the same state read 7 failed, with Staging's job role and the job log groups (`DT-12`) added. Staging's training quotas read 0 like Production's, and no type inside the ceiling has a transform quota above 0 in either account. Every open decision was taken by the user the same day, as recommended, 1 and 3 among them: Staging keeps no mirror and reads the governed lake through a read-only share, and reads nothing of Production's outputs; no decision holds a pass now. **Passes 2, 3 and 5 and decision 12 (a) applied the same day**, 19:35-19:59 UTC, on the user's authorization: `data-governance/data/` (8 added, 5 changed: the read shares to Staging and Production, Production's named write on `curated`, the table `curated.trades` with `classification=internal`, the lake's trusted endpoints), `production/data/` and `staging/data/` by Recipe D (the settings, then 34 and 33 added), the jobs' security group and Glue connection in both `sagemaker/` slices, and `production/workloads/` on `vpc-v0.4.0` for Stage 10; every re-plan reads `No changes`, `./aws/deploytargets.py` and `./aws/datalake.py` 0 failed, and verification xiv is answered. `lakeformation` joined both egress slices at their first `make up` on 2026-10-23 (16 to add each), and `DT-8` reads the read-only share. **The third sitting of 2026-10-22, the environment down**: 5.1 written as the customer-managed policy `awsds-prod-data-scientist` in `production/data/` (planned: 1 to add, 1 to change, the key policy admitting the warehouse's audit groups) and its attachment in `identity/sso/` (1 to add, 1 to change: `DataScientistProdAccess` 7,098 to 8,438 characters), after the inline form rendered 10,550 against the 10,240 ceiling; `lakeformation:GetDataAccess` joins the set, without which 2.3's regrants reach nothing; the two warehouse denies become one shared fragment; `DT-10` reads the managed half. **Both applied the same evening on the user's authorization**, 22:50 to 22:52 UTC, each re-plan `No changes` and `DT-10` passing. Step 9.1's two slices written: `production/warehouse/` plans 9 to add, and `production/warehouse-compute/` is held from `make up ENV=production` (`layers.py` refusal 9) until the namespace it reads is applied. **6.3 done**: the window approved, opened by apply at 23:09 UTC, exercised (three assumptions, each alarmed and mailed; the reads; both negatives refused one layer before the ones the step named), closed by apply at 23:35, and the refusal against the closed trust read in the trail on 2026-10-23. **Prepared 2026-10-23 with the environment down** (the log): 2.4's proof job written, `awsds-prod-producer-proof` in `production/sagemaker/` with its script under `proofs/` and its two modes, the job role gaining `glue:UpdateTable` for an Iceberg commit, the slice planned *1 to add, 1 to change* and **applied the same evening with the script uploaded**, 9.4's grant applied with it, `production/workloads/` read `No changes` (its bump applied 2026-10-22); decision 13 opened and taken by the user the same day as recommended, (a): the full-table-access flag AWS's page names for a Glue write, unset in Production and in the lake, turned on in Production by the user's hand in the console at 19:49 UTC, read back with the parameters intact (`TM-26`); 9.4's Data API grant written on `awsds-deploy-prod` (planned *1 to change*) and `production/workloads-egress/` taking `GROUPS=redshift`; `WH-15` naming each account's `make down`; the persona proofs of 3.4, 5.4, 8.1-8.4 and Stage 10 6.2 written as commands, runnable with nothing up; the quota codes and the request commands in 3.5, no request ever made in either account; the sittings in order in [`runbooks/promotion.md`](../runbooks/promotion.md). **The persona proofs run by the user the same evening** (the log): 5.4 and 8.3 (the override and the two control-plane negatives answered, the Data API negative validating before authorizing with no workgroup, re-run at pass 6), 3.4's persona half (the registry pair, verification v), 8.1's laptop half, 8.4 (three layers, the key, the bucket and the set), 2.5's drop and 2.6's read-back, and 8.2 in the user's console session (INT-06 answered: one page works, open question 8 closed); the space halves wait for the Sandbox sitting. **Staging is the renamed `Development`** ([6b](stage-06b-development-becomes-staging.md)): 10.50.0.0/16 with its `[P]` gateway endpoint, peered with `VPC-Networking` only, no default route, and an `egress/` slice still cut for an Interactive account, which 4.3a re-cuts. **Production's jobs run in `VPC-Workloads`** ([6c](stage-06c-networking-hub.md)), whose endpoint slice holds the jobs' six endpoints once pass 1 is applied (3.3a) and whose gateway endpoint, not `production/foundation/`'s, is their INT-05 anchor (1.4). Three measurements from [6d](stage-06d-unified-studio-remainder.md) and [6i](stage-06i-sandbox-orchestration.md) reshape the runtime: a SageMaker job's settings are enforced on whoever calls `Create*Job`, never on the role the job runs as (3.5, decision 9); a job under network isolation reads no governed data, so the producer and the pickup stay Glue (3.1); and `consumer-data-v0.6.0` supplies neither a workgroup nor a results bucket, so this stage authors both (decision 11, [D19](../decisions/D19-derived-zone.md)'s re-decision). **The Staging data CMK is created here**, as `alias/awsds-staging-data`. Step 9 adds the governed half of the Redshift warehouse ([D40](../decisions/D40-redshift-warehouse.md)), copied from the Sandbox slices [Stage 5b](stage-05b-redshift-serverless.md) built and [6h](stage-06h-redshift-connection.md) measured. **The Production sitting of 2026-10-23** (the log): 2.4's first run refused at the vend with Production's flag alone, decision 13's lake half applied at 22:03 UTC, the second run committed at 22:06 and 2.5's pickup consumed the drop at 22:11, `curated.trades` at twenty rows; Stage 10 0.5 answered; 9.1's namespace applied at 22:07, refusal 9 lifted, the compute planning *2 to add* and waiting on 9.3's theme and quota; `deploytargets.py` and `datalake.py` all checks passed. **9.3 run 2026-10-24** (the log): the compute raised by the user with `GROUPS=redshift`, the nineteen statements `FINISHED` through the Data API as the admin, the schema `trades` at 1 TB with its owner, roles, `IAMR:` users and default privileges, every `PUBLIC` `CREATE` revoked, `warehouse.py --sql` passing, the audit groups carrying the session. **2026-10-24, the environment down** (the log): `deploytargets.py`, `warehouse.py` and `datalake.py` all checks passed, the burn 0.000 USD/h; the `ml.m5.large` pair reads `CASE_OPENED` in both accounts (3.5); 9.5's datashare read on AWS's step pages and written as a command sequence, which opens decision 14 (the account that registers the share and grants it), taken by the user the same night as recommended, Data Governance, and names what 9.6 and 9.7 needed: a table in `trades`, which 9.4's DDL and load job create, written later that day. The same night the user read `curated.trades` as the Data Scientist User through `awsds-prod-athena` (5.4's first query: `SUCCEEDED`, 20 rows, the result under the enforced location despite the request's own) and deleted `EXC-02`'s three objects, the row retired. **2026-10-24, the sixth sitting with the environment down** (the log): the training, transform and processing quotas read above zero in both targets, 20 for `ml.m5.large`'s training and 8 for its transform (3.5), so no step waits on a quota; 9.4 written in the template as v0.4.0's warehouse DDL, a manual job of the Production leg, and its load, a workflow of Production's own that its chain starts (decision 15, the user's, against the recommendation); 8.5's governed read and application table written in the template; `production/data/`, `staging/data/` and `production/sagemaker/` planned *1 to change* each and `staging/sagemaker/` an output, applied the same day on the user's authorization (17:51 to 17:54 UTC, each re-planned `No changes`, `deploytargets.py` all checks passed before and after). **§V, 2026-10-24/25** (the log): xxviii's third run committed with Production's flag off; 8.5's governed read ran in Staging and Production (30 rows); 9.4's DDL job and load ran after two missing grants (the deploy role's Data API follow-up, the job group's 5439 egress), 9.6 and xxv answered; 9.5's datashare built across Production, Data Governance and Sandbox; 9.7 read from `eighth-experimentation` after the access role's catalog read, its Lake Formation grant and `TEMP`, and again with Production's workgroup gone; after the downs `app_outputs`' infrastructure grant was applied in both data slices (Staging's `make down` had been refused the application table's delete), 9.5 step 4's unused grant to the project role revoked, xii's identity half read by the simulator, and `EXC-13`'s Sandbox half read from the day's Data API sessions. **The warehouse sitting of 2026-10-26** (§N.2, the log): Production's balance 299.71 before, unchanged since 2026-10-25; the compute up at 00:43 and xviii closed, `price_performance_target` `DISABLED`; `warehouse.py --sql` green in both accounts, `WH-12` reading the datashare consumer's `ds:trades_lf_acc_DC_<Data Governance>` → `ds:trades_lf`, the platform's pair; 5.4's Data API negative refused by `DenyMintingARedshiftDatabaseSession`, vii three of three; 9.4's DDL job run again from pipeline #102, idempotent, 30 rows counted by `IAMR:awsds-deploy-prod` (xxii); 9.7 read a third time with the project role's grant revoked and Production's workgroup gone; `EXC-13`'s Sandbox half read a second time; xxiv deferred by the user to a sitting of its own, its procedure to be rewritten for the adopted resources; both workgroups destroyed by 01:37 UTC, the Sandbox down meeting the Studio-apps hook against the Query editor's `PendingCheckout` app. **Left, 2026-10-26** ([`promotion.md`](../runbooks/promotion.md) §N): 3.4's project-role half (v) and 8.1's space half, which waits on 6f decision 1, from a Sandbox space on the house image; xii's call, written 2026-10-25 in `scripts/model-chain.py transform staging` on `staging/foundation/`'s new registry output (applied the same day), read at the next Staging leg (4.6); xxiv's producer-side revoke, a sitting of its own with the procedure rewritten (§N.4); ix's `VPC-Workloads` branch and off-endpoint refusal, xv's deploy- and execution-role halves and xxvii's cancel, which no step provokes yet; `EXC-13`'s Production half after its first rotation, due by 2026-11-22; Production's full-table flag turned off by the user on 2026-10-25, `TM-26`'s Production half closed |
| **Prerequisites** | Stage 3: `production/foundation/` and `production/workloads/` with their `[P]` gateway endpoints. Stage 5a: the lake, the LF settings under `DL-5`'s guard, the drop-box statements written against this stage's role name. **Stage 8 pass 1**: step 3's resource policies name `awsds-deploy-prod` and `awsds-deploy-staging`, and a resource policy naming a principal that does not exist fails at put time; the full chain only for pass 5. 6b and 6c: Staging and the three Production VPCs as built. For step 9 alone: [5b](stage-05b-redshift-serverless.md) (the warehouse slices and their readings, its verification (i) answered with two subnets) and [6h](stage-06h-redshift-connection.md) (the database users and grants measured through both doors). Redshift waits on no quota (5b 0.4 read 25 namespaces and 25 workgroups per account); SageMaker does: the processing-job quotas of `ml.m5.large`, `ml.m5.xlarge` and `ml.m5.2xlarge` read 0 in Production and Staging (2026-10-18). [Stage 18](stage-18-staging-deployment-project.md) ran on pass 1's `Workloads` document and its battery (its 0.3 and 0.5) and is done (2026-10-22): D41 item 2 kept, and pass 5 finds Staging at Stage 18's 0.3 reading, with no association, no project, no `staging/studio/` and `SMUS_DEPLOYMENT_MEMBERS` empty (`backend.py`), except `AWSServiceRoleForAmazonMWAAServerless`, Stage 10's, and the project key, `PendingDeletion` until 2026-11-21 |
| **Consumes** | [D13](../decisions/D13-lake-formation-enforcement.md), [D14](../decisions/D14-supply-chain-account.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D18](../decisions/D18-data-scientist-access.md), [D19](../decisions/D19-derived-zone.md), [D20](../decisions/D20-staging-account.md), [D22](../decisions/D22-data-governance-account.md), [D25](../decisions/D25-drop-box-consumer.md), [D28](../decisions/D28-workflow-contract.md), [D31](../decisions/D31-approver-read.md), [D38](../decisions/D38-single-egress-hub.md), [D39](../decisions/D39-access-by-identity.md), [D40](../decisions/D40-redshift-warehouse.md) |
| **Proves** | [INT-03](../integrations.md) **the write share** (the two read shares are Stage 5a's); [INT-05](../integrations.md) (the Production branch, anchored on `VPC-Workloads`, and the persona's principal branch); [INT-06](../integrations.md); [INT-07](../integrations.md) **in part**, the model-registry read half, which absorbed INT-04 at 6b (the image half is Stage 8 step 3.2's); [INT-10](../integrations.md) **the pickup half** (the writer and maintenance halves are Stage 5a's); [INT-24](../integrations.md), a Sandbox project reading a governed Redshift table that lives in Production |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** what Staging and Production need in order to run promoted artifacts, and the governed write
path through which Production becomes the lake's **only** producer (D22). Stage 8 built the promotion
*machinery* (its passes 1-3) against an application that touches no data, and runs the promotion itself,
its pass 4, once this stage's platforms exist (its decision 23); this stage gives it something real to
deploy against, and its end is the first fully meaningful promotion. **Scope (D14):** Production's networking went
to Stage 3 and 6c, the registries to Stage 7, and the deploy credential layer is Stage 8's. What remains here
is the data platform, the SageMaker runtime and the sharing model.

## What this stage builds, and in which accounts

| Where | What | Layer |
|---|---|---|
| `production/sagemaker/` (new) | Model Registry: package groups + **resource policies** (D28 item 6); `awsds-prod-job-exec`; the `awsds-prod-debug` escape hatch + its alarm; the SageMaker job log groups, pre-created with a retention (3.1); 2.4's proof job `awsds-prod-producer-proof` and its script under `proofs/` (applied 2026-10-23, the script uploaded) | `[P]` |
| `data-governance/data/` (amended) | the Production share: LF read **+ governed write**, granted *with grant option* to the Production account (INT-03's last third), and Staging's read share, `DESCRIBE` and `SELECT` by Sandbox's expression (decision 3); the trusted-network list's Production entry read from `production/workloads/` (1.4); the first curated table and its LF-Tags, declared before its first write (2.1) | `[P]` |
| `production/data/` (new) | the `consumer-data` call (account data CMK, LF settings, resource links, re-grants) and, beside it, what `consumer-data-v0.6.0` does not supply: the outputs bucket, the results bucket `awsds-prod-derived` and the enforced workgroup `awsds-prod-athena` (decision 11) | `[P]` |
| `staging/data/`, `staging/sagemaker/` (new) | 1.1-1.3's shape without the write: the `consumer-data` call with the read share's links and read regrants, `awsds-staging-outputs` (Stage 10 decision 17), its results location and workgroup (decision 11), no mirror and no copy (decision 3); the job role `awsds-staging-job-exec` and its six job log groups (4.3), and nothing else. Staging has no SMUS (D17/D28) | `[P]` |
| `production/workloads-egress/` (amended), `staging/egress/` (amended) | the endpoints a job needs where there is no default route (3.3a, 4.3a): the same six in both VPCs, on `vpc-egress` v0.17.0, with the DNS Firewall in both | `[E]` |
| `production/warehouse/` (new, rank 53, step 9; applied 2026-10-23) | **the data half** of D40's governed warehouse: the namespace `awsds-prod-warehouse` under `alias/awsds-prod-data`, its admin secret, its three audit log groups, the namespace role, the security group, the alarms, and the first governed schema, written by `awsds-prod-job-exec` and put under Lake Formation by decision 5's shape | `[P]` |
| `production/warehouse-compute/` (new, rank 54, step 9; refusal 9 lifted with the namespace on 2026-10-23, raised by the user's `make up` on 2026-10-24 and 2026-10-25) | **the compute half**: the workgroup at `base_capacity = 4` in `VPC-Workloads`' private tier and its usage limit, in one apply. `[E]` for Sandbox's reason: Redshift Serverless has no pause, so *powered off* means *does not exist*. RMS storage bills while it is down | `[E]` |
| `production/workloads-egress/` (amended again) | the `redshift` endpoint group (`redshift-serverless`, in the module since `vpc-egress-v0.15.0`) where a job inside the VPC calls the Redshift API. `redshift-data` is not in the group; it is added only if a job inside the VPC uses the Data API | `[E]` |
| `identity/sso/` (amended) and `production/data/` (amended) | `DataScientistProdAccess`'s owed allows as the customer-managed policy `awsds-prod-data-scientist` (the workgroup, the named prefixes, the results, the data key through S3, the debug-role assumption), created by `production/data/` and attached by name in `identity/sso/`, where the set gains `lakeformation:GetDataAccess` and the two Redshift denies `DataScientistAccess` carries, as one shared fragment. Written and applied 2026-10-22. Decision 10 adds no registry read here: both Sandbox readers' own-side allows already exist | `[P]` |
| `identity/org-policies/` (amended) | the job settings in the `Workloads` OU document if decision 9 takes (a), and the serverless-inference deny (3.7), each with its battery rows | `[P]` |
| `scripts/` | `backend.py`/`layers.py` rows: `production/data/`, `production/sagemaker/`, `staging/data/`, `staging/sagemaker/` and `production/warehouse/` are `[P]`, refused by `make up`/`down`; `production/warehouse-compute/` is `[E]`, with `usd_per_hour = 1.44` as its ceiling | — |

**Contracts this stage fixes, each read by `./aws/deploytargets.py` so a rename fails in a check rather
than in a later stage:** the job role **`awsds-prod-job-exec`** (the exact name Stage 5a step 1.4's
reader-deleter statement and drop-box KMS grant carry), the workgroup **`awsds-prod-athena`**, the buckets
**`awsds-prod-outputs`**/**`awsds-prod-derived`** (`results/` is a prefix family in the derived bucket, never
a bucket of its own), the package groups **`awsds-prod-model-<app>`**, the debug role **`awsds-prod-debug`**
with rule **`awsds-prod-debug-assume`** (`DT-9`), Staging's **`awsds-staging-job-exec`**/**`awsds-staging-athena`**,
**`awsds-staging-outputs`** (Stage 10 decision 17) and, if decision 11 takes the recommendation,
**`awsds-staging-derived`**,
and, from step 9, the namespace and workgroup **`awsds-prod-warehouse`**, its role **`awsds-prod-warehouse-exec`**,
the first database `warehouse` (`db_name`) and the class container **`governed`**, with no prefix on anything
([Stage 5b](stage-05b-redshift-serverless.md) 2.1's class convention; `WH-6` reads it, and no project role can
reach this account).

**The outputs other slices read, by state key** (`<account>/<slice>/terraform.tfstate` in
`awsds-<env>-tfstate`, the names Stage 8's application slices list in `state_read_keys` and Stage 10's
render reads): `*/sagemaker/` gives `job_role_arn`, `job_role_name` and `job_log_group_names`, and
Production's also `model_package_group_arns` and `debug_role_arn`; `production/data/` gives the
`consumer-data` module's `data_key_arn`, `data_key_alias` and `resource_link_names`, and
`outputs_bucket_name`/`_arn`, `derived_bucket_name`/`_arn`, `workgroup_name` and
`app_outputs_database`; `staging/data/` gives the same names, Staging having the same shape without the governed write. `*/sagemaker/` also gives
`job_security_group_id` and `glue_connection_name` (decision 12).

```mermaid
flowchart LR
    subgraph DG["Data Governance (D22)"]
        LAKE["curated · Iceberg"]
        BOX["drop-box (D25)"]
    end
    subgraph PRD["Production · jobs in VPC-Workloads"]
        JOB["awsds-prod-job-exec [P]<br/>no S3 on lake prefixes (D13)"]
        REG["Model Registry [P]<br/>groups + resource policies"]
        WG["awsds-prod-athena [P]<br/>enforced · scan limit (decision 11)"]
        OUT["outputs + derived [P]<br/>own CMK (D31)"]
        DBG["awsds-prod-debug [P]<br/>closed by default · alarmed"]
        WH["awsds-prod-warehouse · step 9 · D40<br/>namespace [P] · compute [E] · usage limit<br/>Lake Formation by decision 5<br/>no project tag, no connection"]
    end
    subgraph STG["Staging"]
        MIR["own catalog · read share, no copy<br/>awsds-staging-job-exec only"]
    end
    MIR -.->|"LF read only · decision 3"| LAKE
    JOB ==>|"LF governed write · INT-03"| LAKE
    JOB ==>|"read + delete · INT-10"| BOX
    JOB --> OUT
    JOB ==>|"the only writer of rows · step 9"| WH
    DS["data scientist (D18)"] -->|"Athena, read only"| WG
    DS -.->|"approved window only"| DBG
    SDR["awsds-deploy-staging (St.8)"] -.->|"read approved version<br/>INT-07's registry half"| REG
```

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits (Terraform, scripts) and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user/account/permission set stated first |
| **[user]** | behavioural proofs run from a laptop session, approvals, and the log entries the user writes |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make, in the same sitting |
| **[pipeline]** | Stage 8's chain run in pass 5, which is Stage 8's own pass 4 (its decision 23) — triggered by the user's tag, credentialed by Stage 8 step 4 |

Hand applies run as the **infrastructure user**: `awsds-infra-data` (the grantor half),
`awsds-infra-prod` (the Production slices), `awsds-infra-staging`, `awsds-infra-identity`
(`identity/sso/` and `identity/org-policies/`). The persona proofs of step 8 sign in as the **data-science
user** through the set under test, and from Sandbox also as the project role inside a space where decision
10 makes that the reader: the one stage so far whose evidence is mostly *another* identity's sessions.

## Step numbers are identifiers, not an order

These numbers are **stable addresses cited from other files** — step 3 from Stage 10 step 5 and D28
item 6 (the registry Stage 10 consumes rather than invents); step 2 from Stage 5a step 1.4 and INT-10
(the pickup half); step 5 from `identity/sso/README.md`'s owed table; step 6 from D17 and
`docs/ORGANIZATION.md` (the deployment manager's approval). They do not change. The sequence to work in is
**the passes below**:

| Pass | # | What | Slice · layer | Applied as |
|---|---|---|---|---|
| **0** | 7 | consume Stage 8's credential layer; the preflight readings | readings, no build | — |
| **1** | 3, 6 | the runtime: registry + resource policies, the job role, the escape hatch, the job log groups; the job settings where decision 9 puts them | `production/sagemaker/` `[P]`; `identity/org-policies/` `[P]` | `awsds-infra-prod`; `awsds-infra-identity`, battery first |
| **2** | 2 | the share, grantor side — read + governed write to Production, the trusted list, the first table declared | `data-governance/data/` `[P]` | `awsds-infra-data` |
| **3** | 1, 2 | the consumer slice, then the producer proofs (the write pair, the pickup) | `production/data/` `[P]` | `awsds-infra-prod` |
| **4** | 5, 6, 8 | the persona layer and the boundary sweep | `identity/sso/` `[P]` + sessions | `awsds-infra-identity`; persona sessions |
| **5** | 4, 8 | the Staging platform, then the end-to-end promotion | `staging/data/`, `staging/sagemaker/` `[P]` | `awsds-infra-staging`; the pipeline |
| **6** | 9 | the governed warehouse: the namespace and its guards, the compute, the first governed schema, the Lake Formation shape, and INT-24's cross-account read | `production/warehouse/` `[P]`, `production/warehouse-compute/` `[E]` | `awsds-infra-prod`; then the pipeline for 9.4 |

Pass 1 precedes pass 2 because the grantor's regrant target and Stage 5a's drop-box statements both name
the job role; pass 3 cannot precede pass 2 (a resource link to a share that does not exist resolves
nothing — Stage 5a's rule, repeated for this consumer). **Pass 5 waits on nothing but pass 4 and Stage 8's
chain**; Stage 8 decision 23 (taken 2026-10-16) runs Stage 8's pass 4 once this stage's platforms
exist, together with Stage 10's passes 1 and 2, which makes 8.5 the promotion's first run rather than a
re-run. **Pass 6 is last and
separable**: the warehouse needs the job role (pass 1), the account data CMK with its Redshift statement
(pass 3) and the pipeline (pass 5), and nothing needs it, so it can be deferred past the stage's closing
proof without holding anything up, which is the honest place for the estate's most expensive object per
unit of time.

**One consequence of that order:** Production becomes a Lake Formation account only at **pass 3** (1.3
names its first data lake administrator), so **pass 2's post-grant reading is a RAM reading, not a catalog
one** — the share is *held* before it is *visible*, a pass apart. 2.2's callout carries the discriminator.
Moving 1.3's settings into pass 1 would close the gap and is deliberately not done: it would split one
slice across two applies to buy an earlier confirmation.

---

## To execute

### 1. `production/data/` — the consumer slice, layer `[P]`

**Action:** give Production the data platform D18 and the producer path stand on — output buckets, the
enforced Athena workgroup and its results bucket, and the lake reached through resource links. **Why:**
applications produce locally (logs, intermediates, outputs pending curation) and humans read locally (D18);
the lake itself is never here (D22), so everything in this slice is either *local output* or a *pointer* to
the share. **Explanation:** the `consumer-data` module's second caller, beside `sandbox/data/` (the third,
`development/data/`, was destroyed at 6b). Since `consumer-data-v0.6.0` the module supplies the account data
CMK, the LF settings, the resource links and the re-grants, and nothing else: the derived zone and the
workgroup left it with [D19](../decisions/D19-derived-zone.md)'s revision, which hands their re-decision to
this stage (decision 11). The LF settings in *this* account are written under the discipline `DL-5` imposes
in Data Governance: a `DataLakeSettings` apply replaces the whole structure.

**Applied 2026-10-22** (`terraform-live/production/data/`, its README the index of every added `Sid` and
grant) as `awsds-infra-prod`, by Recipe D: the settings alone (1 added, 19:52Z), read back with the
`InfrastructureAccess` seat alone, both create-default lists `[]`, `CROSS_ACCOUNT_VERSION=4` and
`SET_CONTEXT=TRUE`, so no `IAMAllowedPrincipals` was left to revoke; then the rest, *"Apply complete!
Resources: 34 added, 0 changed, 0 destroyed."* (19:56Z), re-planned `No changes`. The roles the key and bucket policies name are matched by
`aws:PrincipalArn` under the account root, which validates nothing, so the plan stops on no object
another stage creates and survives a role's re-creation under its name.

- **1.1 — [Claude] Write the outputs bucket beside the `consumer-data` call, and the key policy it needs**:
  `awsds-prod-outputs` (application outputs; model artifacts under `models/<app>/`, which step 3 points the
  registry at) from the `s3-bucket` module — versioning, `prevent_destroy`, BPA, SSE-KMS with
  **`alias/awsds-prod-data`**, the account data CMK the call creates (decision 1, D31).
  - **The key policy is enumerated.** The account root keeps administration and holds no cryptographic
    action, so delegation to IAM is impossible and every user of the key is named, through the module's
    `additional_data_key_policy_statements` input, with no module release. The people and roles:
    `awsds-prod-job-exec` writes model artifacts (3.1), `DataScientistProdAccess` writes Athena results as
    the caller (5.1), both needing `kms:GenerateDataKey` and `kms:Decrypt`, conditioned
    `kms:ViaService = s3.<region>.amazonaws.com`; `awsds-prod-debug` reads only. The services, each read
    from the Sandbox apply that needed it: Redshift Serverless
    (`AllowRedshiftServerlessViaServiceInThisAccount`, before pass 6, 9.1); SageMaker's grant on a job's
    volume key, created in the submitting session and invoked by `sagemaker.amazonaws.com` (6i); MWAA
    Serverless, which calls `GenerateDataKey` with the encryption context
    `aws:airflow-serverless:workflow-arn` at a workflow's creation and `Decrypt` at each run (6i), if Stage 10
    decision 2 puts workflows on this key; and CloudWatch Logs (`logs.<region>.amazonaws.com`) for every log
    group encrypted under it. MWAA Serverless calls the key in its caller's session: `CreateGrant`,
    `GenerateDataKey` and `Decrypt` in the one creating a workflow, `GenerateDataKey` and `Decrypt` in the
    one starting a run, and `Decrypt` at each `GetWorkflowRun` (Stage 18 4.2 and 0.4, 2026-10-19), so under
    Stage 10 decision 2 the key names the deploy role and Stage 10's chain role. Which principal makes the
    other services' calls in an account whose key does not delegate to IAM is unread: Sandbox's project key
    delegates, so 6i could not tell. Without the statement,
    the `kms:Decrypt` granted at 5.1 and 6.1 reaches nothing (Lesson 28's intersection, the failure Stage 5a
    pass 4c paid for on the drop-box).
  - **The bucket policy.** The perimeter branches from Stage 5a step 1.3 as Stage 6g leaves them:
    `aws:SourceVpce` = **`production/workloads/`'s** `[P]` gateway endpoint, the VPC the jobs run in, never
    `production/foundation/`'s, which is `VPC-SharedServices` (GitLab, the runners, an `open` proxy plane);
    the `aws:ViaAWSService` carve-out (Athena writes results as the caller); and a principal branch admitting
    `DataScientistProdAccess`'s read of the named prefixes from any network
    ([D39](../decisions/D39-access-by-identity.md), `./aws/deploytargets.py` `DT-1`).
  - **What Stage 10 adds on these objects**, its exact list in [Stage 10](stage-10-orchestration-promotion.md)'s
    file (2026-10-22), the same in `staging/data/`: on `awsds-<env>-outputs`, its decision 12's deny of
    `s3:PutObject` and `s3:DeleteObject` on `applications/*`, where each leg extracts the release bundle's
    tree, to every principal but the release job's deploy role and the account's `InfrastructureAccess`
    role, a principal branch admitting that pair to `applications/*` from outside `VPC-Workloads`'
    endpoint, and the EventBridge notification its decision 16
    reads; on the data key, the deploy role, `awsds-<env>-chain-exec`, the `awsds-<env>-wf-*` roles and
    CloudWatch Logs for `/awsds/<env>/wf/*` and `/aws/vendedlogs/states/awsds-<env>-chains`.
- **1.2 — [Claude] Write the results bucket and the workgroup beside the call** (decision 11): the bucket
  `awsds-prod-derived`, `results/` its prefix family with a 30-day expiry, under the account data CMK, and
  the workgroup `awsds-prod-athena` with `enforce_workgroup_configuration = true` (the console's "override
  client-side settings", documented to replace the client's result location, encryption and
  expected-bucket-owner with the workgroup's), result location `s3://awsds-prod-derived/results/`, SSE-KMS
  with the account data CMK, `bytes_scanned_cutoff_per_query` per decision 2. These are the objects the
  module built for two consumers before 2026-08-26, written here because in a deployment target nothing else
  supplies them: `./aws/deploytargets.py` (`DT-2`), `identity/sso/README.md`'s owed table and Stage 11 all
  still name `awsds-prod-derived`. **One enforced location, not one per principal**: within-persona
  visibility of query results is a stated limit (risk 6).
- **1.3 — [Claude] Write the LF plumbing**: the account's `aws_lakeformation_data_lake_settings`
  (admins = this account's `InfrastructureAccess` role, create-default permissions emptied — Stage 5a
  step 5.2's kill, repeated here — and **`parameters` carried explicitly from a read**, 1.5); **resource
  links** to the shared `raw` and `curated` databases; a local Glue database `app_outputs` for what
  applications write to 1.1. The **regrants** are 2.3's — they need the share first. **2026-10-25**: the
  infrastructure user's `ALTER`, `DROP` and `DESCRIBE` on every table of `app_outputs`
  (`infrastructure_app_outputs_tables`, in both data slices), after Staging's `make down` was refused the
  delete of a table the deploy role created (the log).
  - **The admin seat.** Since `consumer-data-v0.5.0` the module declares the admin list once, at creation,
    with `ignore_changes` on it, and `DL-13` is the only defence. Production has no SMUS, so any second admin
    is a finding: `./aws/datalake.py` gains Production (`awsds-infra-prod` in its consumer profiles) for
    `DL-5` and `DL-13`, which read Sandbox alone today. Its `DL-8` and `DL-9` hold every consumer to no
    `awsds-*` workgroup and no `*-derived` bucket, the removed derived zone staying removed (D19), so the
    same change scopes them to the Interactive consumers, or 1.2's two objects fail them (read 2026-10-22).
  - **The module's re-grant principal.** `data_scientist_role_arn` is required, and Production passes
    `DataScientistProdAccess`'s reserved role: the persona reads through Athena as itself (D18), so its
    `SELECT` re-grants stay, which takes the re-read D19 left to this stage.

  > **This slice applies in two steps, and the plan cannot say why** — measured in Data Governance on
  > 2026-08-18 (Stage 5a pass 1). Both `create_*_default_permissions` blocks are **Computed**: omitting them
  > plans as `after_unknown` and an explicitly empty list is not expressible, so whether omission *clears*
  > them or merely *leaves them alone* is a provider property no plan states — while the difference is
  > permanent, because those defaults act **at creation time**. A resource link and `app_outputs` are both
  > catalog objects created *in this apply*; if the defaults still stand when they are created, they are born
  > deferring to IAM and clearing the settings afterwards does not reach them. **So: apply the settings alone
  > under `-target`, read the account back (`DT-5`, and `DL-6`'s reading applied to this account), revoke
  > `IAMAllowedPrincipals` if it is still there, and only then apply the rest.** Lesson 27; the procedure is
  > **Recipe D** in [`docs/plan/runbooks/terraform-changes.md`](../runbooks/terraform-changes.md). **The same
  > applies to `staging/data/` (4.1)** — to every account that gains this resource, never just the one in
  > front of you.
- **1.4 — [Claude] Write the machinery rows and point the lake at the right VPC**: `backend.py`/`layers.py`
  gain `production/data/` and `production/sagemaker/` (both `[P]`, outside every `make up`/`down` path), and
  `production` joins `DATA_CONSUMERS` so the slice receives its `lake` map; `staging` joins it at 4.1 for
  its read share (decision 3). The list needs no split: it has
  emitted nothing to `identity/sso/` since D19's revision. What the row does change is the lake's
  trusted networks: `data-governance/data/` reads each consumer's `foundation/` for its gateway-endpoint id,
  and Production's `foundation/` is `VPC-SharedServices`. Its entry is read from `production/workloads/`'s
  output instead, the anchor 6c built for exactly this, so the job VPC is admitted and the build plane is
  not; a row read from the wrong slice fails INT-05 with the bucket's own deny and no word about which VPC
  it expected (Lesson 3). The slice reads the endpoint id through `terraform_remote_state`, never a pasted
  id. Re-plan `identity/sso/` and expect `No changes`. **Written 2026-10-22**: `DATA_CONSUMERS` holds
  Sandbox, Staging and Production, and `DATA_CONSUMER_VPC_SLICE` sends the lake's read of Production's
  gateway endpoint to `production/workloads/` (the plan reads `production/workloads/terraform.tfstate`).
- **1.5 — [Claude⚡] Apply as `awsds-infra-prod`, bracketing the LF settings with two readings**:
  `aws lakeformation get-data-lake-settings --profile awsds-infra-prod` before the first apply and again
  after — Production's `Parameters` map is defended nowhere until this slice exists, and this apply is
  exactly the operation that can silently reset it (INT-11's failure mode). **The before-reading is not a
  formality**: on 2026-08-19 both Interactive accounts were found carrying `CROSS_ACCOUNT_VERSION=4` /
  `SET_CONTEXT=TRUE`, set by nobody in this repository, while Staging, after 6b's destroy, read
  `CROSS_ACCOUNT_VERSION=1` with an empty admin list. The values that go into `parameters` are copied **from
  that account's own reading**, never from Data Governance's and never from this file. `DT-5` reads
  every account's parameters since 2026-10-22: `SET_CONTEXT` in all three, `CROSS_ACCOUNT_VERSION` 4 at
  the share's two ends. **Read 2026-10-22 at 04:55Z**: Production holds no administrator, both default
  lists `IAM_ALLOWED_PRINCIPALS` with `ALL` (AWS's defaults, so the two-step is load-bearing here),
  `CROSS_ACCOUNT_VERSION=4` and `SET_CONTEXT=TRUE`. **Done 2026-10-22**: `DT-5` read one
  `IAMAllowedPrincipals` entry in each default list at 19:45Z; the settings alone (19:51-19:52Z) read back
  with the `InfrastructureAccess` seat alone, both lists `[]` and the same parameters (`DT-5` at 19:54Z),
  then the rest (step 1's paragraph).

### 2. The producer path (D22, D25, INT-03, INT-10)

**Action:** grant Production the lake's read **and governed write**, then prove both directions — a
curated table written cross-account through Lake Formation, a direct `PutObject` to the same bucket
denied, and the drop-box pickup that empties the letterbox. **Why:** this is the only path by which
governed data is ever written (D22), and the write grant is INT-03's least-travelled variant — proven
with a job, never assumed. The pickup is the same producer path applied to a file a human dropped
(D25): Data Governance cannot host the job — its OU SCP denies compute — so if it does not run in
Production it runs nowhere. **Explanation:** the grant is the documented two-step. The grantor grants to
the **account** (with grant option); Production's LF admin then **regrants** to the job role locally.
The two-step is what lets Stage 10's per-workflow roles (D28 item 3) receive their own regrants later
without ever touching Data Governance again.

**The local regrant is itself a pair** — measured at pass 4, in two accounts, 2026-08-19. A shared
database reaches a local principal through two permissions that are not interchangeable: `DESCRIBE` on
the **resource link**, which is an ordinary local database object, *and* the permission on the **target**,
addressed through the owner's `catalog_id`. The first is the one that gets forgotten, and its symptom is
the worst kind: the principal sees **no database at all**, holding every permission on the target. Write
both, and read `list-permissions` afterwards rather than the code (pass 4's four rows per account are the
shape).

> **The write ceiling exists since 2026-08-20** (Stage 5a's log entry of that date). The registration role
> `awsds-data-lf-registration` — the session every LF-vended access to the registered locations runs as,
> 2.4's job included — carries `registered-locations-write` (`s3:PutObject`+`s3:DeleteObject` on the two
> registered prefixes, `kms:GenerateDataKey`). **Nothing here needs to touch it**: 2.1's grants and 2.3's
> regrants are the per-principal gate under a ceiling that is already wide enough, and a 2.4 denial naming
> `kms:GenerateDataKey` or `s3:PutObject` for an `AWSLF-…` session would mean the ceiling *regressed*.

- **2.1 — [Claude] Amend `data-governance/data/` with the Production grant and the first table**: LF
  permissions `DESCRIBE, SELECT, INSERT, DELETE, ALTER` on the `curated` database and its tables (**`ALTER`
  is not optional** — an Iceberg commit rewrites table metadata, so a write without it fails at the commit,
  not at the first row), granted to the **Production account** with grant option, from the same authored
  share map Stage 5a built. Read side unchanged: `DESCRIBE`/`SELECT` on `raw` too, if the pickup curates
  from it. Two shapes inherited from Stage 5a pass 3:
  - **every cross-account grant carries the grant option** — the receiving account's own administrator
    can only pass on what it received with the option — so 2.3's regrant is the ordinary second half of
    *any* share here, and what stays particular to Production is the governed **write** in the permission
    list (`docs/GOVERNANCE.md` §Grants);
  - **if these are written as TBAC expressions rather than named resources, the `layer` gate is
    mandatory** (Lesson 29). Stage 5a's decided form was `classification ∈ {public, internal}` alone and
    it matched the **drop-box**, whose entire contract is write-never-read-back. The write grant is more
    dangerous in the same direction. **Recommended here: named-resource on `curated`**, which Stage 5a
    decision 5 reserves for recorded exceptions — a single-database, single-account write is exactly that,
    and it is recorded in the register as one.

  **The table 2.4 writes is declared here, before its first write.** The grant carries no `CREATE_TABLE`, so
  the table and its LF-Tags are declared in `data-governance/data/` (`aws_glue_catalog_table`,
  `aws_lakeformation_resource_lf_tags`) from the versioned schema source (decision 3), with the Governance
  Manager approving the classification ([`docs/GOVERNANCE.md`](../../GOVERNANCE.md), the development cycle
  of a data product). A table without `classification` matches no expression and is invisible to every
  consumer, so the tag is part of the delivery; Staging reads it through its share (decision 3, 4.1). The
  share map gains Staging's read, `DESCRIBE` and `SELECT` with the grant option by the expression
  Sandbox's share uses, and no write. **Applied 2026-10-22** (2.2): the read shares to Staging and
  Production, `production_write_database` and `production_write_tables` (named, with the grant option),
  and `curated.trades` with the columns of `app-etl`'s input and `classification=internal`, the
  classification approved with the apply the user authorized; the five lake bucket policies gained
  Staging's and VPC-Workloads' gateway endpoints, and the settings stayed untouched.
- **2.2 — [Claude⚡] Apply as `awsds-infra-data`, inside `DL-5`'s bracket**: read
  `DataLakeSettings.Parameters` before and after (Stage 5a step 5.4's three-reading discipline — the reset
  it can cause is silent). Then, from Production with a **fresh** session (Lesson 24 — the four-hour CLI
  cache serves stale successes): **Production's RAM holds the new shares**, and **no pending invitation**
  (`DL-7`'s shape; a pending row is INT-11's fallback tax). **Done 2026-10-22, 19:35:58-19:36:25Z**:
  *"Apply complete! Resources: 8 added, 5 changed, 0 destroyed."*, re-planned `No changes`; `DL-5` read
  `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE` at 19:35:09Z and 19:39:12Z, `DL-7` 9 shares out where it
  read 3; Production's RAM holds four `LakeFormation-V4-*` shares and Staging's two, each `ACTIVE`, and
  neither has an invitation pending.

  > **The shared databases will not be visible here, and that is the correct state rather than a failed
  > share** — measured at Stage 5a pass 3, 2026-08-19. A receiving account needs **at least one data lake
  > administrator** before a shared resource appears in its catalog at all — and Production has none until
  > **1.3**, which is pass 3, one pass *after* this one. **The discriminator is therefore the RAM side, not
  > the catalog side** — a share the consumer's RAM does not hold is the real INT-11 failure, an empty
  > catalog before 1.3 is not. `DL-7` reports the two branches separately, and `DT-5`'s twin reading
  > inherits the distinction. The catalog-side confirmation belongs at **2.3**, after 1.3 has made
  > `awsds-infra-prod` an admin.
- **2.3 — [Claude⚡] Regrant locally and finish `production/data/`** (`lakeformation.tf`, applied
  2026-10-22 with pass 3): as `awsds-infra-prod` (an LF admin since 1.3), `aws_lakeformation_permissions` granting the job role `DESCRIBE` on the resource links and
  `SELECT, INSERT, DELETE, ALTER, DESCRIBE` on the shared tables through them. `list-permissions` read
  the same day: 21 grants in Production, 9 of them to `awsds-prod-job-exec`, and none to
  `IAMAllowedPrincipals`; the link `curated` lists `sample_trades` and `trades` to the infrastructure user.
- **2.4 — [user] Prove the write pair (INT-03)**: run a job under `awsds-prod-job-exec` (a Glue job — the
  engine the pickup and Stage 10's workflows use) that writes 2.1's curated Iceberg table through the LF
  share; then, from the same role, a direct `put-object` to the lake bucket — **denied**, because the role
  holds no S3 allow on lake prefixes (D13). Read both wordings; record both. **Decide the job's network
  first**: a Glue job with a network connection runs in `VPC-Workloads` and reaches Glue, Lake Formation,
  STS and S3 through that VPC's endpoints (3.3a) and its gateway endpoint (1.4); one without runs in Glue's
  own network, where neither the endpoints nor the bucket's `aws:SourceVpce` branch are on its path. Either
  way, read the job's Lake Formation events for `vpcEndpointId`: this is the first engine in the estate that
  vends its own Lake Formation credentials, which is the reading Stage 10 step 0.5 waits for (whether the
  `lakeformation` endpoint earns its place). Decision 12 carries the choice, with the job security group's
  owner. **No job exists for this proof (read 2026-10-22)**: the pipeline's `awsds-prod-app-etl` runs the
  release's `glue/transform.py`, which reads the inbox and writes one CSV under `work/glue/`, and the
  template carries no schema (Stage 8 pass 4), so no promotion writes `curated.trades`, and Stage 10
  6.1's curated write is an application's publish task that `app-etl` does not have. The proof therefore
  needs a job of its own before the Production sitting, to write first: a `[P]` Glue 6.0 job
  `awsds-prod-producer-proof` declared in `production/sagemaker/` beside the job role, on
  `awsds-prod-jobs` (decision 12 (a)), running a script the infrastructure user writes under
  `s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/`, the one prefix family the bucket's
  principal branch and the data key admit that principal to from the laptop (Stage 10 decision 12's
  exemption), which inserts the sample rows into `curated.trades` through the resource link with Glue's
  Iceberg catalog under Lake Formation, reads them back, and then attempts the direct `PutObject`; the
  pickup (2.5) is a second script of the same job family, consuming the dated drop-box prefix. Whether
  Lake Formation's full-table-access mode admits a writer holding `INSERT`, `DELETE` and `ALTER` without
  `ALL` is the run's first reading, INT-03's least-travelled variant, and the fallback is INT-03's row.
  The pickup settles part of it: its direct `GetObject` and `DeleteObject` reach the drop-box
  only through `VPC-Workloads`' gateway endpoint (1.4), while the vended reads and writes arrive as the
  registration role, a Data Governance principal the lake's perimeter admits from any network
  (`aws:PrincipalAccount`, read 2026-10-22 in `data-governance/data/buckets.tf`).
- **2.4 — Written 2026-10-23, planned, unapplied** (`terraform-live/production/sagemaker/producer-proof.tf`
  and `proofs/producer_proof.py`; the log). The job runs as the job role on `awsds-prod-jobs`, Glue 6.0,
  two `G.1X` workers, its script at `s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py`,
  one run per `--MODE`: `producer` inserts the ten sample rows of `examples/app-etl/samples/trades.csv`
  into `curated.trades`, reads them back and attempts the direct put, which fails the run if it lands;
  `pickup` is 2.5's. **The write goes through Lake Formation's full-table-access mode**, the one mode
  a Glue Spark job writes a registered table in (AWS's page "Using AWS Glue with AWS Lake Formation
  for Full Table Access", read 2026-10-23): an Iceberg catalog `lake` over the lake account's Glue
  catalog, `glue.lakeformation-enabled` on, the data files read and written with the credentials Lake
  Formation vends, a session of the registration role, so the job's own role touches no lake prefix
  (D13); the catalog's `glue.id` is the lake account, read from the lake state's key ARN. The page
  moved two things: the job role gains `glue:UpdateTable` on the lake's `curated` tables and this
  account's `app_outputs` tables (`CommitTheIcebergWrites`), since an Iceberg commit ends in that
  call and IAM is evaluated beside Lake Formation's `ALTER` (Lesson 28); and it names
  `AllowFullTableExternalDataAccess` as the mode's first step, unset in Production and in the lake on
  2026-10-23, which is decision 13. Two readings the first run takes, each with its fallback: whether
  the mode admits a writer holding `INSERT`, `DELETE` and `ALTER` without `ALL`, which the page says a
  write requires (the fallback is `ALL`, `DROP` with it, on `shares.tf`'s `production_write_tables`
  and `lakeformation.tf`'s `job_curated_write`, planned and applied as `awsds-infra-data` then
  `awsds-infra-prod`); and whether the flag is needed in the engine's account, the lake's, or both.
  Plan as `awsds-infra-prod` at 16:24 UTC: *"Plan: 1 to add, 1 to change, 0 to destroy."*, the job
  and the role's inline policy. **Applied 2026-10-23 at 21:18 UTC** on the user's authorization, from a
  fresh plan of the same counts, *"1 added, 1 changed"*, re-planned `No changes`; the script uploaded at
  21:20, 7,318 bytes under the data key, version `LhV4dvLqaXJCFqSJm.Z0tpmqShZjHM95`, and the job read
  back as declared (the log). **The sequence**, in [`runbooks/promotion.md`](../runbooks/promotion.md)
  §P: decision 13 taken and done; the slice applied; the script uploaded by the infrastructure user,
  the one principal the bucket's branch and the data key admit to `applications/*` from the laptop:

  ```bash
  aws s3 cp terraform-live/production/sagemaker/proofs/producer_proof.py s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py --profile awsds-infra-prod --region us-west-2
  ```

  then `make up ENV=production ONLY=workloads-egress` (the endpoints the job's Glue and Lake Formation
  calls take; without `ONLY=` it applies `runners/` too and destroys the build runner), the run and its
  state:

  ```bash
  aws glue start-job-run --job-name awsds-prod-producer-proof --arguments '{"--MODE":"producer"}' --profile awsds-infra-prod --region us-west-2
  ```

  ```bash
  aws glue get-job-runs --job-name awsds-prod-producer-proof --max-results 3 --query 'JobRuns[].[Id,JobRunState,StartedOn,CompletedOn,ErrorMessage]' --output table --profile awsds-infra-prod --region us-west-2
  ```

  The readings: the script's `[producer-proof` lines in `/aws-glue/jobs/logs-v2`'s stream of the run
  id (the insert's commit or its refusal with the wording, the row count, the direct put's refusal,
  *"no identity-based policy allows the s3:PutObject action"* expected); and in Production's CloudTrail
  the run's Lake Formation events for `vpcEndpointId`, Stage 10 0.5's reading and decision 12 (a)'s:

  ```bash
  aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=lakeformation.amazonaws.com --start-time "$(date -u -v-2H +%Y-%m-%dT%H:%M:%SZ)" --query 'Events[].[EventTime,EventName,Username]' --output table --profile awsds-infra-prod --region us-west-2
  ```

  A refusal names its layer: a Lake Formation wording (*"Insufficient Lake Formation permission(s)"*)
  is the grant's shape or decision 13's flag, an IAM wording naming `glue:UpdateTable` is the role's,
  a timeout at the Glue or Lake Formation API is the endpoint set. **The first run, 2026-10-23 at
  21:43 UTC** (the log): `FAILED` at the first SQL after 56 s, the vend for the lake's `curated/trades`
  with `SELECT` refused *"Insufficient Lake Formation permissions. Verify the data lake settings for
  account"*, Production's flag `true` and the lake's unset at that minute; the four `GetDataAccess`
  carry the `lakeformation` endpoint's id (Stage 10 0.5 answered), and the lake's trail holds none of
  them where 5.4's Athena read of 20:29 UTC left its answered pair in both accounts. Decision 13's
  fallback follows: the lake's resource gains the flag, planned *"0 to add, 1 to change"* at 21:56 UTC;
  applied at 22:03 UTC and run again at 22:04 (the log): **`SUCCEEDED`** in 79 s, the insert committed at 22:06:11, ten rows read back through the share, the direct put refused by the lake's data key (`kms:GenerateDataKey`, *"no resource-based policies allow access"*), one layer before the S3 wording expected here, as 8.4 read for the Staging persona; the eight `GetDataAccess` answered through the `lakeformation` endpoint, four of them shared into the lake's trail. The mode admits the writer without `ALL`; the owner's flag is required; whether the engine's is too, and whether the commit needs `glue:UpdateTable`, are unmeasured, each a run away.
- **2.5 — [user] Prove the pickup (INT-10)**: drop a file into the dated prefix from a Sandbox session
  (Stage 5a's writer half), run the pickup job under the job role — it reads the prefix, curates into a
  governed table through 2.4's write path, and **deletes what it consumed**. Verify the KMS half
  explicitly: an `AccessDenied` on the drop-box key surfaces as an S3 error naming the object, not the
  key (D25's forgotten half — the grant was written in Stage 5a against this stage's role name; this is
  where a typo in that contract fails). The three objects `EXC-02` declared (Stage 5a's and Stage 6g's
  proofs) are not CSV, so this run passed them over, and the infrastructure user removed them on
  2026-10-24, which retired the row; open question 19's third part, whether this
  writer makes `awsds-data-raw` redundant, is answered here.
- **2.5 — The sequence, written 2026-10-23** (`runbooks/promotion.md` §P). The drop, from a laptop as the
  Data Scientist User in Sandbox, the dated key the convention names:

  ```bash
  aws s3 cp examples/app-etl/samples/trades.csv "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" --profile awsds-scientist-sandbox --region us-west-2
  ```

  then 2.6 before the pickup, then the pickup, 2.4's job in its second mode:

  ```bash
  aws glue start-job-run --job-name awsds-prod-producer-proof --arguments '{"--MODE":"pickup"}' --profile awsds-infra-prod --region us-west-2
  ```

  **The drop made 2026-10-23** by the user: `incoming/2026/10/23/trades.csv`, waiting for the pickup
  (the log). The script lists every `.csv` under `incoming/` as the job role (`ListTheDropBox`), fails the run
  when there is none, reads the rows with the role's own credentials under the lake key (the KMS half:
  a refusal there surfaces as an S3 error naming the object), inserts them into `curated.trades`
  through the share, deletes each consumed key and reads it gone (a `404` on `head-object`). `EXC-02`'s
  three `.txt` objects are not CSV and stay: the row retires with a deliberate `InfrastructureAccess`
  cleanup once the pickup has run, as `AWS_STATE.md` has it (done 2026-10-24, the user's hand). **Run 2026-10-23 at 22:09 UTC** (the log):
  `SUCCEEDED` in 97 s; one CSV listed, ten rows read as the role under the lake key (the KMS half, a
  `kms:Decrypt` through S3 in Production's trail), ten rows curated, the table at 20 through the share,
  the key deleted and read gone. The delete is a delete marker over a version the bucket's 90-day
  noncurrent rule expires, and `EXC-02`'s three objects were passed over. The pickup wrote `curated`
  with no `raw` in between, the reading open question 19's third part weighs.
- **2.6 — [user] Confirm the letterbox asymmetry now closes**: the same Sandbox session that wrote the
  file still cannot `GetObject` it back (Stage 5a's deliverable, re-read with the consumer finally
  existing). Read right after 2.5's drop and before the pickup, which empties the letterbox:

  ```bash
  aws s3 cp "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" - --profile awsds-scientist-sandbox --region us-west-2
  ```

  expected refused, the implicit deny Stage 5a pass 4d read. **Run by the user 2026-10-23**: refused
  as a bare `403` on `HeadObject` (the log); the attributed form is the object read, whose error body
  names the layer:

  ```bash
  aws s3api get-object --bucket awsds-data-dropbox --key incoming/2026/10/23/trades.csv /dev/null --profile awsds-scientist-sandbox --region us-west-2
  ```

  **Done 2026-10-23**: *"no identity-based policy allows the s3:GetObject action"*, 4d's implicit deny
  with the consumer now existing (the log).

### 3. `production/sagemaker/` — the runtime half of D17, layer `[P]`

**Action:** the Model Registry and the execution role pipeline-submitted jobs run as — no domain, no user
profiles, no interactive anything. **Why:** the registry is the promotion boundary: a model version is
*approved*, and the approval must sit on the far side of the gate from the person who trained it — which
is why it lives here and not in an Interactive account, and why each package group carries a resource
policy **written now, not improvised in Stage 10** (D28 item 6). A model package group costs nothing at
rest, so this is `[P]`. **Explanation:** cross-account deployment is documented as three resource
policies — the model package group, the ECR repository of the inference image (Stage 8 step 3.0's grant
covers the repositories), and the S3/KMS of the model artifacts (1.1's bucket and CMK). The group policy
is `aws_sagemaker_model_package_group_policy` (`PutModelPackageGroupPolicy`, ≤ 20 480 bytes).

- **3.1 — [Claude] Write the job role `awsds-prod-job-exec`**: trust policy `sagemaker.amazonaws.com`
  and `glue.amazonaws.com` only — never assumable interactively (D27's shape); `ecs-tasks.amazonaws.com`
  joins only if Stage 10 decision 8 keeps an ECS step. Permissions:
  - the Glue catalog read, `lakeformation:GetDataAccess` (the credential-vending call every LF-aware
    engine makes), CloudWatch Logs, read+write on 1.1's and 1.2's buckets, the drop-box read/delete and its
    KMS decrypt (the identity half of Stage 5a's statements — the drop-box is its own bucket, Stage 5a
    decision 3, so it is the named exception), and **no `s3:*` on the four lake buckets** (D13 — 2.4
    proves it); since 2026-10-23, `glue:UpdateTable` on the lake's `curated` tables and this account's
    `app_outputs` tables, the call an Iceberg commit ends in (`CommitTheIcebergWrites`, applied
    2026-10-23; 2.4);
  - what a SageMaker job in a VPC calls as its own role, read from 6i's processing job:
    `ec2:CreateNetworkInterface`, `CreateNetworkInterfacePermission`, `DeleteNetworkInterface` and the
    `Describe*` reads on VPCs, subnets, security groups, network interfaces and DHCP options;
    `ecr:GetAuthorizationToken`, `BatchGetImage` and `GetDownloadUrlForLayer` on the application
    repository, since the job pulls its image as this role through the service and never through the VPC's
    `ecr.*` endpoints; `kms:Decrypt`/`GenerateDataKey` through S3, and no `kms:CreateGrant`. Two errors in
    the job's `SageMaker` session are benign, read on Staging's `app-etl-20261021T235652` (Stage 18,
    2026-10-21): `kms:CreateGrant` on the volume key refused, as in 6i's run of 2026-10-11, and one
    `ecr:BatchGetImage` `InvalidParameterException` beside three that passed; the job completed.
  - a Glue job with a network connection reads the connection as this role before it starts: Glue's
    `GlueJobRunnerSession` called `glue:GetConnection` four times in Staging on 2026-10-19, as the role
    of [Stage 18](stage-18-staging-deployment-project.md) 4.4's job. `ReadTheJobsConnection` grants it on this account's
    connections (applied 2026-10-22).

  **A SageMaker job reads no governed data.** Under the settings 3.5 enforces, the container has no
  network and no AWS credentials, and the platform stages its inputs and outputs with this role, which
  holds no S3 on a lake prefix; Lake Formation vends to Glue, never to a SageMaker input. So the producer
  and the pickup are Glue jobs, and a SageMaker step (training, processing, batch transform) reads what a
  Glue step staged into `awsds-prod-outputs`, which is Stage 10 step 5.1's shape. **The job log groups are
  pre-created**: the first SageMaker job creates `/aws/sagemaker/ProcessingJobs` (and `TrainingJobs`,
  `TransformJobs`) with no retention and no CMK (`EXC-10`, measured at 6i), so this slice declares the ones
  the account will use, with a retention, and Staging's slice does the same (4.3); Glue's job groups the
  same way. In Staging the first job came before the slice: Stage 18 4.4's created
  `/aws/sagemaker/ProcessingJobs` on 2026-10-19 and its pass 8 deleted it on 2026-10-22; 4.3 says what
  the slice owes such a group. **Each group is under the account data key since 2026-10-22**:
  `*/sagemaker/` reads the key's ARN from `*/data/`'s state with a null default,
  so a first build still applies the role before `data/`, and CloudWatch Logs uses the key as its own
  principal under the data key's `AllowCloudWatchLogsForTheJobAndWorkflowGroups`, scoped by each group's
  ARN, with no grant to either role. *"Apply complete! Resources: 0 added, 6 changed, 0 destroyed."* in
  Production (20:51Z) and in Staging (21:00Z), from fresh plans identical to the reviewed ones, `kms_key_id`
  the only attribute that moved, each re-planned `No changes`; the policies name the groups by ARNs built
  from their names, so no role policy moved. AWS's page says the key encrypts what arrives after the
  association, so what a group held before keeps the AWS-owned key until the 30-day retention expires it.
  `DT-12` reads each group's key and passes in both accounts (21:03:22Z); the AWS-owned key, another key
  or a partial apply fails it. The first job shows whether its logs land and the debug role reads them
  with no grant on the key. `iam:PassRole` to
  the role is granted only to Stage 8's deploy roles and Stage 10's execution roles, scoped by
  `iam:PassedToService`.
- **3.2 — [Claude] Write the package groups and their resource policies**: one group per application or
  model family — `awsds-prod-model-app-etl` first (D28 item 6). Policy, three statements: **register and
  approve** (`sagemaker:CreateModelPackage`, `UpdateModelPackage`) for `awsds-deploy-prod` alone, among
  the principals outside this account (inside it a resource policy constrains nobody an identity policy
  admits, so the infrastructure user can approve too, `registry.tf`); **read
  approved** (`DescribeModelPackage`, `ListModelPackages`) for `awsds-deploy-staging`; and **read status**
  for the Sandbox readers decision 10 names. A data scientist reaches AWS from Sandbox as two principals:
  the persona's reserved SSO role (`AWSReservedSSO_DataScientistAccess_*`) from a laptop or the console,
  and the project role (`datazone_usr_role_<project>_<env>`) from inside a space or a workflow, the role
  that already pulls the house image from this account (INT-01). A condition on the reserved-SSO pattern
  alone refuses a notebook's call. The account comes from the D35 map in `backend.py` and the role is
  matched by `aws:PrincipalArn`; the statement carries no `arn:aws:iam::*:`, so
  `./scripts/check-iam-wildcards.py` has nothing to whitelist. When the registry first holds a version,
  re-read nothing for `EXC-11`: its trigger is the Sandbox registry's first version (Stage 17 3.2), and
  this registry is Production's, in an account the domain does not know. Each cross-account reader needs
  its own allow as well (Lesson 28): `awsds-deploy-staging`'s is Stage 8's to write in
  `staging/foundation/`: `sagemaker:DescribeModelPackage` on the packages of Production's
  `awsds-prod-model-*` groups, the two actions the group policy grants it, and `ListModelPackages`, which
  takes no resource.
- **3.3 — [Claude] Write the escape hatch** (step 6's resources — same slice, same apply).
- **3.3a — [Claude] Complete `production/workloads-egress/`.** `VPC-Workloads` is where Production's jobs
  and Stage 10's workers run, and 6c created the slice empty, with `core_services = []`. Bump it from
  `vpc-egress-v0.11.1` to v0.17.0, the tag that carries the optional groups (`redshift`, and the reserved
  `mwaa` Stage 10 fills) and `no_proxy_all_groups`, and name the job-facing set: `sts`, `logs`, `kms`,
  `glue`, `sagemaker.api` and `secretsmanager`, plus `lakeformation` if 2.4's reading shows a job vending
  through it (Stage 3 called it load-bearing in Production), plus Stage 10 step 1.2's worker set. Turn the
  DNS Firewall on, which the module leaves off by default, with a list of AWS namespaces only: the resolver
  channel exists wherever code runs (6c 5.7). **A missing endpoint here never fails as a proxy 403.** This
  plane's proxy list refuses everything by decision, an application image built `FROM base` carries no proxy
  variable, and an isolated job container has no network at all. A worker reaching for a name the firewall
  blocks fails at resolution in about 2 s (`errno 16`, 6i); without the firewall the same reach resolves and
  hangs. **Planned 2026-10-18, read-only, the slice's first plan**: 15 to add, the six endpoints and the
  firewall's nine pieces; the next Production `make up` applies it. Decision 12 (a) adds `lakeformation`
  (2026-10-22): *"Plan: 16 to add"*, seven endpoints at 0.070/h.
- **3.5 — [Claude reads, user decides] Enforce the job settings where `Create*Job` is called (decision
  9).** `terraform-modules/sagemaker-denies/` holds five statements: `DenySageMakerJobsOffVpc` (`VpcConfig`
  present, `CreateModel` included, which is how batch transform is bound), `DenySageMakerInstanceCeiling`
  (seven CPU types), `DenySageMakerJobsWithoutNetworkIsolation`, the inter-container-encryption deny (sent
  even for one instance: the deny is `BoolIfExists`, and 6i had to set it) and the volume-key deny. **They
  bind the caller, never the role the job runs as** (Lesson 66): 6d's refusal named the calling session's
  boundary, and
  6i's accepted job was the caller's. In Sandbox the caller and the job's role are one role, the project
  role, so the D13 boundary covers both. In Staging and Production the callers are Stage 10's workflow
  execution roles, the deploy roles (integration tests, batch transform) and any role a pipeline creates; a
  boundary on `awsds-prod-job-exec` binds none of them. Two shapes:
  - **(a) the `Workloads` OU SCP** carries the five statements, composed from the module's document so there
    is one source (Lesson 33), and binds every principal in Staging and Production whatever creates it. The
    document is 640 bytes minified of the 5,120 an SCP allows. Battery rows first
    ([`scp-battery.md`](../runbooks/scp-battery.md)).
  - **(b) the module as the permissions boundary of every role that submits jobs**, with an `Allow *`
    ceiling beside the denies (a boundary holding only denies allows nothing, `sagemaker-prereqs/boundary.tf`),
    and `iam:PermissionsBoundary` on the deploy roles' `CreateRole`, so a pipeline cannot mint a submitter
    without it.

  **Recommended: (a)**: a condition attached to every submitter by hand will be missing from one
  (Lesson 14). **Applied 2026-10-18** with 3.7's deny, at 19:54Z, as `awsds-infra-identity`; the battery's
  `ou` phase after the apply read each Stage 9 row as expected (the log). **The instance-preference rows
  are written, and ran on 2026-10-22 in Stage 18's 8.7 battery, each as expected** (the upstream readings of 2026-10-18, PR #189): since 2026-09-15 a job may
  name up to five instance types as a list instead of `InstanceType`,
  `ProcessingResources.ClusterConfig.InstancePreferences` for processing and
  `ResourceConfig.InstancePreferences` for training, and whether the service fills
  `sagemaker:InstanceTypes`, the key `DenySageMakerInstanceCeiling` reads, from that list was unread until
  the rows ran: the lists naming an off-ceiling type answered `DENY-SCP` and the list inside the ceiling
  was authorized, so the service fills the key from the list; the
  policy generator's catalogue lists no new key. `probes.py`'s `ou` phase carries the rows in Production:
  for each action a list naming `ml.m5.2xlarge` and a list naming `ml.m5.large` then `ml.m5.2xlarge`, each
  expected `DENY-SCP`, beside a list naming `ml.m5.large`, expected authorized, and for training the same
  request with `ml.m5.2xlarge` as `InstanceType`, the control that attributes the action's replies
  ([`scp-battery.md`](../runbooks/scp-battery.md) phase 4b). An authorized deny row is a hole in the
  ceiling. The key's population is a property of the request, so the answer carries to the D13 boundary
  for [Stage 17](stage-17-sandbox-machine-learning.md) pass 2. **The first job in `Workloads` came before
  the rows**: Stage 18 4.4 ran Staging's first, `app-etl-20261019T205205` on `ml.t3.medium` (2026-10-19),
  naming its type as `InstanceType`, so it did not exercise a list. The rows ran after it, on 2026-10-22,
  before Stage 10's processing step and Stage 17 pass 2's training job. Production's three `ml.m5`
  processing quotas read 0 again on 2026-10-20, so an authorized processing row still answers
  `ResourceLimitExceeded` (the log). Its training quotas read 0 the same day, AWS's defaults with no
  request, for those three types and for every other type inside the ceiling with a training quota
  (`ml.t3.large`, `ml.t3.xlarge`, `ml.c5.xlarge`; `ml.t3.medium` and `ml.c5.large` have none), so
  Stage 10 5.1's training job waits on an increase (the log). **The quota codes, read 2026-10-23** in
  both accounts with `list-service-quotas` (the codes are the service's, the same in every account),
  each at 0 in Staging and in Production, and `list-requested-service-quota-change-history` empty in
  both: no request was ever made.

  | Type | Training | Transform | Processing |
  |---|---|---|---|
  | `ml.m5.large` | `L-611FA074` | `L-236AE59F` | `L-8541302D` |
  | `ml.m5.xlarge` | `L-CCE2AFA6` | `L-7939E4EC` | `L-0307F515` |
  | `ml.c5.xlarge` | `L-E2BB44FE` | `L-09C9B23C` | `L-486519E6` |
  | `ml.t3.large` | `L-B95AAE44` | none | `L-C076FA77` (4) |
  | `ml.t3.xlarge` | `L-823DAB46` | none | `L-DABA7ED5` (2) |
  | `ml.t3.medium` | none | none | `L-0CE343FE` (4) |

  The request is the user's, one call per code and account; the least pass 3 needs is `ml.m5.large`
  for training and for transform in both accounts, the type 5.1's task and 5.4's transform name
  (recommended: 2 of each; the other codes when a workload names the type):

  ```bash
  for q in L-611FA074 L-236AE59F; do aws service-quotas request-service-quota-increase --service-code sagemaker --quota-code "$q" --desired-value 2 --profile awsds-infra-prod --region us-west-2; done
  ```

  ```bash
  for q in L-611FA074 L-236AE59F; do aws service-quotas request-service-quota-increase --service-code sagemaker --quota-code "$q" --desired-value 2 --profile awsds-infra-staging --region us-west-2; done
  ```

  The state of each request is read with `list-requested-service-quota-change-history --service-code
  sagemaker` on the same profile; Stage 17's three requests of 2026-10-17 in Sandbox read `CASE_OPENED`
  for days. **Requested by the user 2026-10-23, 20:00 UTC**: `ml.m5.large` training and transform at 2
  in Production and in Staging, the four reading `PENDING` with no case id at 20:02 UTC (the log); the
  other codes wait for a workload that names the type. **Read 2026-10-24, 01:58 UTC**: the four read
  `CASE_OPENED`, each with a support case id, last updated 2026-10-23 between 20:03 and 21:00 UTC: a
  person at AWS answers them, as Stage 17's Sandbox requests have waited since 2026-10-17. **Read
  2026-10-24, 03:47 UTC**: the requests still `CASE_OPENED`, and the applied quotas above zero in both
  accounts, Sandbox's values: training 20 for `ml.m5.large`, `ml.m5.xlarge`, `ml.c5.xlarge` and
  `ml.m5.2xlarge` and 1 for `ml.t3.large` and `ml.t3.xlarge`; transform 8, 4, 8 and 2 for the first four;
  processing 8, 8, 8 and 4, 10 for `ml.t3.medium` and `ml.t3.large`, 5 for `ml.t3.xlarge` (the log).
  AWS's default for `L-611FA074` still reads 0, so the accounts' own quotas were raised past the
  requests' 2, and Stage 10's pass 3 waits on none.
- **3.6 — [Claude] Read the enforcement back.** `./aws/deploytargets.py` gains **`DT-11`** (`DT-9` is the
  escape hatch): under (a), the five statements present in the `Workloads` OU document and the document
  attached; under (b), every role that can call `Create*Job` in the two accounts carries the boundary, read
  with `get-role`, never `list-roles`, which omits `PermissionsBoundary` by documented contract (the trap
  `US-8` exists for). **Read 2026-10-18**: `DT-11` passes, the document attached and its six job Sids
  present.
- **3.7 — [Claude reads, user decides] Settle serverless inference, which has no VPC configuration at
  all.** An endpoint configuration in serverless mode takes no `VpcConfig`. Two honest shapes: **(a)** a
  named exception with its own row in `docs/AWS_STATE.md` and a trigger to revisit; **(b)** deny
  `sagemaker:CreateEndpointConfig` **without** a `VpcConfig` in the `Workloads` OU SCP, so serverless
  inference does not exist in this estate until somebody argues for it. **Recommended: (b)** — a capability
  nobody has asked for is cheaper to refuse than to fence. Read first whether 3.5's (a) already refuses it:
  `DenySageMakerJobsOffVpc` covers `CreateModel`, so every model in these accounts carries a `VpcConfig`,
  and a serverless endpoint over such a model may be refused by the service itself. If it is, (b) is a
  reading rather than a second statement. **The reading is
  [Stage 17](stage-17-sandbox-machine-learning.md) 4.4's**: a serverless endpoint configuration over a model
  that carries the project's `VpcConfig`, and one over a model created without it, under the Sandbox copy of
  the same boundary; Stage 17 decision 8 records the outcome in this step and leaves the decision here.
  **Taken 2026-10-16: (b), before Stage 17's reading**, as `DenySageMakerServerlessInference`. "Without a
  `VpcConfig`" cannot be written, since `CreateEndpointConfig` carries no VPC field and no VPC condition
  key, so the deny keys on `sagemaker:ServerlessMemorySize` being present (the log).
- **3.4 — [Claude⚡] Apply as `awsds-infra-prod`** (after 3.5-3.7, so the enforcement is in place before any
  role can submit a job). **Applied 2026-10-18 at 19:59Z**: 16 added, re-plan `No changes`, `DT-3`, `DT-4`
  and `DT-9` passing. Then **[user] prove the registry gate**, in two halves. From Sandbox, as the readers decision
  10 picked, the persona from a laptop and the project role from a space: `DescribeModelPackageGroup`
  answers while `CreateModelPackage` and `UpdateModelPackage` are denied, the wording naming the resource
  policy's absence of a grant, not a network condition. The approval under `awsds-deploy-prod` runs where
  that role can be assumed, on the deploy runner, its trust's only principal: a manual job of the
  promotion pipeline that registers and approves a version, at Stage 10's first registration, never a
  trust widened to a person for one sitting (`DenyChangingTheDeployIdentities` exists to keep it fixed).
  **The laptop half, written 2026-10-23**, signed in as the Data Scientist User in Sandbox
  (`awsds-scientist-sandbox`), the group named by its ARN since the account is another; the account id is
  the one the laptop's config carries for `awsds-scientist-prod`. The read answers (**run by the user
  2026-10-23**: the group's record, `Completed`, created by the infrastructure user on 2026-10-18, the
  log):

  ```bash
  aws sagemaker describe-model-package-group --model-package-group-name "arn:aws:sagemaker:us-west-2:<Production>:model-package-group/awsds-prod-model-app-etl" --profile awsds-scientist-sandbox --region us-west-2
  ```

  The write is refused, the wording recorded whichever layer answers first (Lesson 20): the set's own
  policy, which holds no `sagemaker:CreateModelPackage`, or the group's resource policy, which grants the
  persona status reads alone:

  ```bash
  aws sagemaker create-model-package --model-package-group-name "arn:aws:sagemaker:us-west-2:<Production>:model-package-group/awsds-prod-model-app-etl" --model-package-description probe --inference-specification '{"Containers":[{"Image":"<Production>.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-app-etl:v0.2.1"}],"SupportedContentTypes":["text/csv"],"SupportedResponseMIMETypes":["text/csv"]}' --profile awsds-scientist-sandbox --region us-west-2
  ```

  **Run by the user 2026-10-23**: refused *"because no resource-based policy allows the
  sagemaker:CreateModelPackage action"*, the group policy's absence of a grant, no network condition
  (the log); the persona's half of verification v is read. The project-role half runs the same two calls
  from a space, with the Sandbox sitting up.

### 4. The Staging data platform (D20) — layer `[P]`

**Action:** the environment the promotion chain actually deploys against — its own catalog, which each
deploy fills with the application's schemas from the repository, a read-only share of the governed lake,
and the job role. **Why:** code and artifacts are promoted and data is not, and the governed lake is the
one source of truth (decision 3): Staging reads the governed tables through the LF-Tag share Sandbox
holds, scoped by `classification`, writes only to its own catalog, buckets and key, and copies nothing,
so a staging run meets the real schemas under a real permission layer. Decision 3 amends D20, which kept
Staging off the share as the least-defended account with unattended tests and data-scientist read
access; that residual is accepted in `threat-model.md` beside Sandbox's. An earlier stand-in (a `staging`
database inside Production) is gone: it shared an IAM surface with what it de-risked and could never
catch a permission error (Lesson 2). **Explanation:** a reproducible test pins an Iceberg snapshot or
reads by time travel; a test that needs Production's own outputs belongs in Production behind the
approval gate (decision 1).

- **4.0 — [Claude] Read what 6b and Stage 8 already delivered, and build only the gap**: 6b brought the
  bootstrap, `foundation/`, `egress/`, the tree and the SSO assignment; Stage 8 step 4.1 brought
  `awsds-deploy-staging`. The INT-07 image grant, Stage 8 step 3.0's pull grant, was applied by the user
  on 2026-10-19 in [Stage 18](stage-18-staging-deployment-project.md)'s window: `APP_REGISTRY_CONSUMERS`
  reads `sandbox` and `staging` (`backend.py`), and `production/registry/`'s `app-etl` repository policy
  admits Staging's account (that stage's log). 3.0's ceiling half, `awsds-<env>-app-boundary`, stands in
  both `foundation/` slices, applied by Stage 8 (PR #244): read 2026-10-22, version `v1` in both accounts
  and attached to no role. Read 2026-10-18: the AZ mapping is identical in the six profiled accounts, and account-level
  Block Public Access has all four flags in each, Staging's included. **This stage owns two things nobody
  else does** — the account data CMK `alias/awsds-staging-data` (created here, under its own name; 6b
  destroyed the old `dev`-named key rather than renaming it) and the `staging/{data,sagemaker}/` slices
  below. Run
  `./aws/AZs.py` and `./aws/account-bpa.py` once as the standing post-conversion readings.
- **4.1 — [Claude] Write `staging/data/`**, 1.1-1.3's shape without the governed write (decision 3): the
  `consumer-data` call (the account data CMK `alias/awsds-staging-data`, the LF settings, the resource
  links to the read share and the read regrants to the job role, `DESCRIBE` and `SELECT` alone),
  `awsds-staging-outputs`, Stage 10 decision 17's (taken 2026-10-15), 1.1's `s3-bucket` call with
  Production's statements, and a local Glue database for what the application writes, whose tables each
  deploy creates from the repository's schemas; no mirror and no copy of a governed table. Staging joins
  `DATA_CONSUMERS`, so the lake's perimeter admits its `[P]` gateway endpoint, read from
  `staging/foundation/` as Sandbox's is, and 2.1 grants its read. The LF settings follow 1.3's discipline
  (parameters carried, defaults killed), **its two-step apply included**: a resource link born deferring
  to IAM restricts nothing. The before-reading is not Production's: Staging reads no administrator,
  `CROSS_ACCOUNT_VERSION=1`, `SET_CONTEXT=TRUE`, both default lists empty and
  `AllowFullTableExternalDataAccess` false, as Stage 18's pass 8 put them back on 2026-10-22 after its SMUS
  provisioning had seated two administrators and turned that flag on (2026-10-19), re-read at 04:55Z the
  same day with no administrator, both lists empty and the same parameters, and the parameters are copied
  from that reading. With no SMUS in Staging, a second administrator is a finding there as in Production,
  and `./aws/datalake.py` gains Staging for `DL-5` and `DL-13` with 1.3's Production: Stage 18 8.6 read the
  seats by hand. **A resource link to Data Governance is now the design**, and every Staging grant on the
  lake is `DESCRIBE` or `SELECT`: `DT-8`'s isolation check, which fails on a link, is rewritten to read
  that, rewritten on 2026-10-22. **Applied 2026-10-22**: `terraform-live/staging/data/` as
  `awsds-infra-staging`, by Recipe D: the settings alone (1 added, 19:57Z), read back with the
  `InfrastructureAccess` seat alone, both create-default lists `[]` and `CROSS_ACCOUNT_VERSION` moved from
  1 to 4; then the rest, *"Apply complete! Resources: 33 added, 0 changed, 0 destroyed."* (19:59Z),
  re-planned `No changes`. `DT-8` reads the links resolving into Data Governance, and the link `curated`
  lists `sample_trades` and `trades`.
- **4.2 — [Claude] Write the workgroup `awsds-staging-athena` and its results location** (decision 11):
  enforced, scan limit, **for the integration tests and the deployed application, not for people** —
  `DataScientistStagingAccess` carries no Athena at all (Stage 2 wrote it that way: a query writes its result
  somewhere, and this set writes nothing). An enforced workgroup cannot exist without an output location,
  which nothing supplies since `consumer-data-v0.6.0`.
- **4.3 — [Claude] Write `staging/sagemaker/`** with a `backend.py` row of its own: today
  `elif slice_name == "sagemaker"` hands any `sagemaker` slice the blueprint prerequisites' inputs, and
  Staging is not in `DATA_PRODUCERS` (read 2026-10-18 by the Stage 18 session). The slice holds
  `awsds-staging-job-exec`, 3.1's shape and permissions,
  no registry, no domain — the approved model version is read from Production's registry — and the
  SageMaker job log groups pre-created with a retention, as 3.1 does. The job settings bind whoever submits
  the job (3.5), so this role carries nothing of them; under decision 9's (a) the `Workloads` OU SCP covers
  this account with Production's. A job's subnets are Staging's private tier and its security group its
  own. **Applied 2026-10-22** (`terraform-live/staging/sagemaker/`, `READ_ONLY_TARGETS` in `backend.py`, rank
  46): 3.1's trust and permissions without Production's drop-box pickup and with `glue:GetConnection`,
  S3 on `awsds-staging-outputs` and `awsds-staging-derived` and none on a lake bucket, and the
  image pulled from Production's `awsds-prod-ecr-app-etl` cross-account, the repository's grant to this
  account being Stage 8 step 3.0's. Applied as `awsds-infra-staging` at 19:47Z, *"Apply complete! Resources: 14
  added, 0 changed, 0 destroyed."*, decision 12's security group, rules and Glue connection included.
  `iam:PassRole` to the role is the passers' to hold: `awsds-deploy-staging` for the Glue job
  the application slice declares and Stage 10's execution role for the processing job, each scoped by
  `iam:PassedToService`.
  - **A job can create Staging's `/aws/sagemaker/ProcessingJobs` before the slice**: Stage 18 4.4's job
    created it on 2026-10-19 at 20:57:40Z, with no retention and no CMK, and Stage 18's pass 8 deleted it on
    2026-10-22 (that stage's log). A declaration over an existing group fails its apply on
    `ResourceAlreadyExistsException`, so the slice reads `/aws/sagemaker/` and `/aws-glue/` before its
    first plan, as 3.4 did in Production, and imports each group that exists; the apply then sets its
    retention. Read 2026-10-22 at 04:55Z: neither prefix holds a group in Staging, and `DT-12` names any
    group a job creates before the apply. The groups go under `alias/awsds-staging-data` as Production's
    go under its key (3.1).
- **4.3a — [Claude] Re-cut Staging's `[E]` endpoint set in `staging/egress/`.** It was built for an
  Interactive account and migrated whole at 6b: the core eight (`sts`, `logs`, `kms`, `ecr.api`,
  `ecr.dkr`, `athena`, `glue`, `lakeformation`) plus `sagemaker.api`, `sagemaker.runtime` and
  `sagemaker.studio`, with the DNS Firewall on, on `vpc-egress-v0.11.1`. **Written 2026-10-22 as
  `VPC-Workloads`' set** (3.3a), so the Staging leg runs on the network the Production leg runs on (D20):
  `sts`, `logs`, `kms`, `glue`, `sagemaker.api` and `secretsmanager`, `core_services` overridden, on
  v0.17.0, the firewall's list AWS's namespaces alone. This account's own run is the reading: on
  2026-10-19 the worker called `glue`, `sagemaker.api`, `kms` and `logs` through these endpoints, and the
  job's image pull and Glue's job runner called from AWS's own addresses, through none ([Stage 18](stage-18-staging-deployment-project.md)'s
  log, 4.4), so `ecr.*`, `athena`, `lakeformation`, `sagemaker.runtime` and `sagemaker.studio` left. Dropping
  `ecr.*` in both VPCs also lets the Staging leg answer what no run has measured, every worker so far
  having had them present: whether a MWAA Serverless worker needs them, where AWS's private-routing
  minimum names `logs`, `monitoring` and `kms` (Stage 10 1.2). A change joins both slices or carries its
  reason: `lakeformation` on 2.4's reading (decision 12), `athena` when a job inside the VPC queries
  through it, and `monitoring` when Stage 10's verification xvi reads the workers' metrics refused, its
  1.2 keeping the `mwaa` group empty, so the leg's `make up` needs no `GROUPS=`. Planned as `awsds-infra-staging`: *"Plan: 15 to add, 0 to change, 0 to destroy."*, the six
  endpoints and the firewall's nine pieces, the coverage precondition passing, and *"Plan: 16 to add"*
  once decision 12 (a) added `lakeformation`; the next `make up ENV=staging` applies it, at 0.070/h where
  the old set cost 0.110. `staging.awsds.internal` holds no
  record (read 2026-10-22), so its names answering NXDOMAIN in the VPC cost nothing. **No AZ pin**: 6i
  measured MWAA Serverless workers placed in both AZs reaching Sandbox's single-AZ endpoints, and a
  SageMaker job's `VpcConfig` names both subnets. As in 3.3a, this plane has no proxy, so a missing
  endpoint fails at the firewall or as a timeout, never as a 403. **Applied 2026-10-23** by the user's
  `make up ENV=staging ONLY=egress` for Stage 8 3.8's by-hand leg (the log): the seven endpoints `available`
  in `usw2-az1` (`glue`, `kms`, `lakeformation`, `logs`, `sagemaker.api`, `secretsmanager`, `sts`) and the
  firewall group `awsds-staging-egress`, `./aws/egress.py` all checks passed at 0.070 USD/h.
- **4.4 — Withdrawn by decision 3**: Staging holds no seeded or synthetic stand-in for governed data, and
  Stage 8's seed job in `examples/app-etl/` is not written. One exception, Stage 10 decision 20 (d), taken
  by the user on 2026-10-22 for the template: the release job seeds `s3://awsds-<env>-outputs/inbox/app-etl/`
  from the bundle's `samples/`, in Staging and Production alike, since `app-etl` is a template with no
  producer and the samples are its own test input, not a stand-in for governed data; a real application
  names its governed source in its release. In the Staging leg the deploy creates the application's own
  tables from the repository's schemas, after Stage 8's 3.2 and before its 3.3, in 4.1's local database;
  a test then reads them and the governed tables through the share, pinned to an Iceberg snapshot.
- **4.5 — [Claude⚡] Apply both slices as `awsds-infra-staging`**, machinery rows included. **Done
  2026-10-22**: `staging/sagemaker/` first, since Lake Formation refuses a grant to a missing role, then
  `staging/data/` by Recipe D (4.1); `DT-4`, `DT-5`, `DT-8` and `DT-12` pass for Staging (20:01:24Z).
- **4.6 — [Claude⚡] Amend step 3's resource policies with the Staging principals** (as
  `awsds-infra-prod`) where the promotion reads Production's registry: 3.2's policy carries
  `awsds-deploy-staging`'s read since pass 1, and the role's own allow is Stage 8's to write in
  `staging/foundation/`. Staging reads nothing of `awsds-prod-outputs` or its key (decision 1): a model
  reaches Staging as a release artifact, through the registry or the release bucket, or is retrained there
  from the governed data the share gives, its archive carrying its data's classification. The application
  image reaches a Staging job through the job's own role (6i: the pull is made as the job's role, session
  `SageMaker`, through the service), so the repository policy admits the account, which Stage 8 step
  3.0's pull grant does on `app-etl`'s repository since 2026-10-19, and `awsds-staging-job-exec` holds the
  pull actions. Stage 18 4.4's job took that path on 2026-10-19: `awsds-prod-ecr-app-etl` by digest,
  pulled as the project role in the session `SageMaker` (that stage's log). **[user]** Prove INT-07's
  registry half: a `DescribeModelPackage` of an approved version from the Staging role answers. Version
  1 exists since 2026-10-25 (Stage 10 5.2); the simulator read the role's own half the same day
  (verification xii), and the call needs a Staging deploy session, which only the deploy runner opens
  ([`promotion.md`](../runbooks/promotion.md) §N).

### 5. The persona layer (D18) — `identity/sso/` amended

**Action:** deliver the allows `identity/sso/` records as owed by this stage, and read back what was
already built. **Why:** the sets were written narrow in Stage 2 with every object-scoped allow deferred
to the stage that creates the object (guessing an interface is what the slice refuses to do); this stage
creates the objects. **Explanation:** resource ARNs interpolate the account id from the organization
data source the slice already uses — never a literal id (`CLAUDE.md`), never a wildcard account
(conventions §6).

- **5.1 — Written 2026-10-22 as a customer-managed policy, applied the same evening.** Inline, the allows
  below took `DataScientistProdAccess` to 10,550 rendered characters, past the 10,240 the slice's
  precondition allows (planned 2026-10-22 at 22:17 UTC), the case the vending policy set the precedent
  for: they are `awsds-prod-data-scientist`, an `aws_iam_policy` of `production/data/` (`persona.tf`),
  whose every ARN is that slice's own (the workgroup, the two buckets, the data key; the debug role by
  name, as its key policy names it), and `identity/sso/` attaches it to the set by name, the name
  generated from `backend.py`'s `PERSONA_PRODUCTION_POLICY_NAME` into both slices. The read prefixes are
  `PERSONA_READ_PREFIXES`, one list generated into `production/data/` for the bucket's principal branch
  and the policy alike (Lesson 33). What stays inline: `lakeformation:GetDataAccess` with the LF-Tag
  reads, which the set lacked and without which 2.3's regrants reach nothing (Lesson 28), and the two
  Redshift denies, now the fragment `redshift_denies` both data-science sets compose, which left
  `DataScientistAccess`'s rendered document byte-identical. Plans: `production/data/` 1 to add, 1 to
  change (the key policy's CloudWatch statement admitting `/aws/redshift/*`, 9.1's groups);
  `identity/sso/` 1 to add, 1 to change, the set at 8,438; both applied on the user's authorization,
  22:50 to 22:52 UTC, each re-plan `No changes` (the log). `DT-10` reads the attached policy's document
  in Production beside the inline one and passes. The allows, as specified: `athena:StartQueryExecution`,
  `GetQueryExecution`, `GetQueryResults`, `StopQueryExecution` on the `awsds-prod-athena` workgroup ARN
  alone; `s3:GetObject` on the **enumerated** application-output prefixes; the results-bucket
  read/write Athena performs as the caller (`GetBucketLocation`, `ListBucket`, `PutObject`, `GetObject` on
  `awsds-prod-derived`), written here because the statement family Stage 5a pass 4c wrote for it left with
  the derived zone (D19 revised); `kms:Decrypt` and `kms:GenerateDataKey` on the account data CMK (1.1);
  `sts:AssumeRole` on exactly the `awsds-prod-debug` ARN (step 6). The warehouse's read side carries the two
  denies `DataScientistAccess` has and this set lacks: `DenyMintingARedshiftDatabaseSession` (the
  `redshift-data:` family, `GetClusterCredentials*`, `GetCredentials`) and `DenyRedshiftCostGuardAndCompute`.
  The Data API reaches a private workgroup from outside every VPC, so a deny rather than an omission is the
  control. The `DenyProductionControlPlane` families are untouched — they deliberately do not name
  `athena:StartQueryExecution`. **Read the size first**: `DataScientistAccess` stood at 10,217 of 10,240
  rendered bytes before 5b's three Redshift statements, `DataScientistProdAccess` was last read at 4,369,
  and a change to a shared fragment (`sagemaker-denies` among them) lands in every set.
- **5.2 — [Claude] Verify `DataScientistStagingAccess` by reading, not by trusting the intention**
  (Lesson 22): `DenyEveryWrite` present, no Athena statement anywhere, nothing this stage adds. **Its
  assignment already exists** — 6b assigned it in the same sitting that removed `DataScientistAccess` from
  the account. **Read 2026-10-18**: the policy by `DT-10`, the assignment by `./aws/list-identities.py`
  and CloudTrail (verification viii).
- **5.3 — Applied 2026-10-22, in order**: `production/data/` as `awsds-infra-prod` (1 added, 1 changed:
  the policy, and the key's Redshift pattern), then `identity/sso/` as `awsds-infra-identity` (1 added, 1
  changed), since a set that references a policy that does not exist fails to provision in that account;
  `terraform output inline_policy_bytes` reads 8,438 for the set, under the ceiling; Production's
  reserved role carries the policy attached, and `DT-10` passes (the log).
- **5.4 — [user] Prove the workgroup boundary and the negatives**, signed in as the data-science user
  through `DataScientistProdAccess`: a query that asks for a different `OutputLocation` runs and its
  result lands under the enforced location anyway (the documented override — verification (vi)); a query
  over the scan limit is cancelled; `sagemaker:CreateTrainingJob` and `glue:StartJobRun` are denied
  naming the set's own deny; `redshift-data:ExecuteStatement` is denied naming
  `DenyMintingARedshiftDatabaseSession`; and nothing outside the enumerated prefixes answers.
  **The sequence, written 2026-10-23**, runnable with the environment down (D39), as the Data
  Scientist User through `awsds-scientist-prod`. The override: a query asking for a location of its
  own, whose result lands under the enforced one (read 20 on 2026-10-24, the log); the count reads 0 before 2.4's run, 10 after it and
  20 after the pickup:

  ```bash
  aws athena start-query-execution --work-group awsds-prod-athena --query-string 'SELECT count(*) AS n FROM curated.trades' --query-execution-context Database=curated --result-configuration OutputLocation=s3://awsds-prod-outputs/not-enforced/ --profile awsds-scientist-prod --region us-west-2
  ```

  ```bash
  aws athena get-query-execution --query-execution-id <id> --query 'QueryExecution.[Status.State,ResultConfiguration.OutputLocation,Statistics.DataScannedInBytes]' --output text --profile awsds-scientist-prod --region us-west-2
  ```

  expected `SUCCEEDED` with `s3://awsds-prod-derived/results/<id>.csv`, and `get-query-results` the
  count. The scan limit has no table to bite on, since nothing here scans 10 GB; it is read back
  instead, `aws athena get-work-group --work-group awsds-prod-athena --query
  'WorkGroup.Configuration.[EnforceWorkGroupConfiguration,BytesScannedCutoffPerQuery]'`, and the
  cancel waits for a table that size. The negatives, each refused with *"an explicit deny in an
  identity-based policy"*, the set's `DenyProductionControlPlane` for the first two (a control-plane
  action the `Workloads` document does not name, so the set's deny is the one layer that answers) and
  `DenyMintingARedshiftDatabaseSession` for the third:

  ```bash
  aws sagemaker create-model-package-group --model-package-group-name awsds-canary-probe --profile awsds-scientist-prod --region us-west-2
  ```

  ```bash
  aws glue start-job-run --job-name awsds-prod-producer-proof --profile awsds-scientist-prod --region us-west-2
  ```

  ```bash
  aws redshift-data execute-statement --workgroup-name awsds-prod-warehouse --database warehouse --sql 'select 1' --profile awsds-scientist-prod --region us-west-2
  ```

  The prefixes: the named one answers, the bucket's root and a release's tree are refused by the bucket
  policy's `DenyThePersonaListingsOutsideTheNamedPrefixes` and `DenyThePersonaReadsOutsideTheNamedPrefixes`
  (*"an explicit deny in a resource-based policy"*):

  ```bash
  aws s3 ls s3://awsds-prod-outputs/app-etl/outbox/ --profile awsds-scientist-prod --region us-west-2
  ```

  ```bash
  aws s3 ls s3://awsds-prod-outputs/ --profile awsds-scientist-prod --region us-west-2
  ```

  ```bash
  aws s3 cp s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py - --profile awsds-scientist-prod --region us-west-2
  ```

  **Run by the user 2026-10-23** (the log): the override answered, the result under
  `awsds-prod-derived/results/` with the enforced configuration and the 10 GB cutoff read back, the
  count 0; `CreateModelPackageGroup` and `StartJobRun` refused *"with an explicit deny in an
  identity-based policy"*; **`ExecuteStatement` validated before it authorized** (Lesson 21), *"Redshift
  endpoint doesn't exist in this region"* with no workgroup in Production, so that negative was run
  again at pass 6 with the workgroup up: **refused on 2026-10-26** *"with an explicit deny in an
  identity-based policy"* on the workgroup's ARN (the log); `app-etl/outbox/` answered, the root refused by the bucket's
  listing deny, and the release's tree a bare `403` on `HeadObject`, which carries no wording: the
  attributed form is the object read, whose error body names the policy:

  ```bash
  aws s3api get-object --bucket awsds-prod-outputs --key applications/stage-09-proofs/v0/glue/producer_proof.py /dev/null --profile awsds-scientist-prod --region us-west-2
  ```

  Run the same evening: refused on `s3:ListBucket` by the listing deny, since the object does not
  exist yet and S3 reads the listing permission to choose between a 403 and a 404; the read deny is
  exercised by the same command once the script is uploaded (the log).

### 6. The production debugging escape hatch (D17)

**Action:** a time-boxed elevated role in Production — `awsds-prod-debug` — that grants read access to
job inputs and outputs for a bounded window, assumable only while a window the **deployment manager**
approved is open, with an alarm on every assumption. **Why:** "nobody ever needs to look at production
interactively" is not true, and an undesigned need becomes a permanent permission. **Explanation:** its
shape is imposed rather than chosen — `DenyInteractiveSageMakerSurface` (`awsds-org-scp-ou-workloads`)
denies `CreateSpace`, `CreateApp`, `StartSession` and `CreatePresignedDomainUrl` with no principal
carve-out, so this role can only ever be read-by-API; the pressure toward "a notebook in Production,
just this once" has nowhere to go, and the correct response to that failure is to keep the shape, not to
amend the OU document. The builder is outside every claim here (Lesson 18): what watches the role is
detective — the alarm, and CloudTrail.

- **6.1 — [Claude] Write the role**: permissions — `s3:GetObject`/`ListBucket` on 1.1's buckets, logs
  read, `sagemaker:Describe*`/`List*`, `kms:Decrypt` on the 1.1 CMK; **no lake reach of any kind** (no
  `GetDataAccess`, no grant through 2.3). Trust — the `DataScientistProdAccess` reserved-SSO role
  (resolved in-account via `data.aws_iam_roles`, never a pasted suffix) **and**
  `Condition: DateLessThan aws:CurrentTime = var.debug_window_end`, whose default sits in the past: the
  role exists and is unassumable at rest. `max_session_duration` 1 hour.
- **6.2 — [Claude] Write the alarm**: an EventBridge rule `awsds-prod-debug-assume` on the CloudTrail
  `AssumeRole` event for this role — **every** assumption, not just misuse — to the target Stage 8
  decision 5 settled: `awsds-prod-alerts`, one topic per member account (the Stage 1b topic lives in the
  Management account).
  A refused `AssumeRole` records no `roleArn` in CloudTrail, so the rule sees the successful assumptions
  only; a refused attempt is read from the trail by its `errorCode`.
- **6.3 — [user] Operate it as designed, once, to prove it**: the deployment manager approves in
  writing (the log), the window variable is set and applied (`[Claude⚡]` as `awsds-infra-prod`), the
  assumption succeeds and the alarm fires; after the window, the same assumption is denied, and the denial
  is read in CloudTrail rather than expected from the rule; a `CreateSpace` under the role is denied naming
  the Workloads OU policy. Reverting the variable closes the window in the same sitting.
  The persona holds the `sts:AssumeRole` allow since 5.1's apply (2026-10-22), and no persona set denies
  an `sts:` action (read 2026-10-22); the inference that the same-account trust admits the session with no
  identity-side allow is no longer the path this proof takes. **Approved in writing 2026-10-22** by the
  user as the deployment manager (the log), the window to end at 2026-10-23T01:00:00Z, planned as
  `awsds-infra-prod` with `-var debug_window_end=2026-10-23T01:00:00Z`: 0 to add, 1 to change, the trust
  alone, the slice's check warning that the window is open. **The persona's sequence**, from a laptop,
  signed in as the Data Scientist User (`aws sso login --sso-session awsds-scientist --no-browser`, the
  URL answered in a private window, as `aws/AWS-CLI.md` has it), with a profile of the laptop's own
  config that assumes the role through the persona (`role_arn` the debug role's, `source_profile`
  `awsds-scientist-prod`, `region` `us-west-2`, so the call reaches the regional STS endpoint the trust
  pins); the account id is the one that config already carries:

  ```bash
  aws sts get-caller-identity --profile awsds-scientist-prod
  ```

  1. Inside the window, the assumption itself, with a session name the alarm's message will print:

  ```bash
  aws sts assume-role --profile awsds-scientist-prod --region us-west-2 --role-arn "arn:aws:iam::<Production>:role/awsds-prod-debug" --role-session-name debug-window-proof --query 'AssumedRoleUser.Arn' --output text
  ```

  The alerts e-mail from `awsds-prod-alerts` names `awsds-prod-debug-assume`, the time, the role, the
  caller and the session name, and carries no credential.

  2. The reads the role exists for, through the assuming profile: the outputs bucket's listing and the
  six job log groups.

  ```bash
  aws s3 ls s3://awsds-prod-outputs/ --profile awsds-scientist-prod-debug
  ```

  ```bash
  aws logs describe-log-groups --log-group-name-prefix /aws/sagemaker/ --query 'logGroups[].logGroupName' --profile awsds-scientist-prod-debug
  ```

  3. The negatives, read by their wording. **Measured 2026-10-22** (the log): the write is refused by
  the data key, whose `AllowTheDebugRoleToDecryptViaS3` grants `Decrypt` alone, *"not authorized to
  perform: kms:GenerateDataKey … because no resource-based policy allows"*, one layer before the bucket's
  `DenyThePersonaAndTheDebugRoleAnyWrite`, which stays attached and unexercised for this principal; the
  `CreateSpace`, the battery's own probe with a domain that does not exist, is refused by the role's own
  identity policy, *"no identity-based policy allows the sagemaker:CreateSpace action"*, one layer
  before the `Workloads` document's `DenyInteractiveSageMakerSurface`, whose wording appears only to a
  principal whose identity policy allows the action (Lesson 20). Each direction is closed twice, and one
  closure of each pair is the proven one.

  ```bash
  echo probe | aws s3 cp - s3://awsds-prod-outputs/app-etl/outbox/probe.txt --profile awsds-scientist-prod-debug
  ```

  ```bash
  aws sagemaker create-space --domain-id d-0000000000000 --space-name awsds-canary-probe --region us-west-2 --profile awsds-scientist-prod-debug
  ```

  4. After the window, the same `assume-role` of item 1 again, never a call through the profile, whose
  cached credentials outlive the window for up to an hour: the refusal names `sts:AssumeRole` and the
  role, and Claude reads it in Production's trail by `errorCode` as the infrastructure user. Then the
  closing apply without the flag, re-planned `No changes`, `DT-9` reading the window closed.
  **Run 2026-10-22** (the log): the window opened at 23:09:55 UTC and closed by the apply at 23:35:09,
  25 minutes, three assumptions inside it (the direct one, the profile's own at its first read, and a
  third run before the end), each heard by the rule and delivered as one message of the transformer's
  eight lines with no credential; the reads answered; both negatives refused one layer before the ones
  this step named (item 3); the re-plan `No changes` and `DT-9` closed after the apply. **The refused
  assumption against the closed trust, 2026-10-23**: *"not authorized to perform: sts:AssumeRole on
  resource: …role/awsds-prod-debug"*, the trust's own refusal, which STS does not attribute in its
  message; the trail records it at 15:25:28 UTC as `AccessDenied` with `requestParameters` null, by the
  persona's reserved role in `us-west-2`, 15 h 50 min after the close (the log). **Done.**

### 7. Consumed from Stage 8 — readings, not builds

**Action:** read what the credential layer already provides before building anything that overlaps it.
**Why:** the deploy roles are Stage 8 pass 1's, and "the KMS grants for Staging's ECR pulls" do not
exist — ECR decrypts pulls through the grants it holds on the repository key, and the puller needs no
`kms:Decrypt` (Lesson 7). **Explanation:** what Stage 9 *names* from Stage 8: `awsds-deploy-prod` and
`awsds-deploy-staging` in step 3's policies, the misuse alarms as the pattern step 6 copies, the alarm
target its decision 5 settled, and the INT-07 image grant as the model 4.6 follows.

- **7.1 — [Claude] Run `./aws/cicd.py`**: CI-2/CI-3 green (the two roles exist with boundary and
  single-principal trust) before pass 1 writes policies that name them. **Read 2026-10-18: green**, for
  the four deploy roles.
- **7.2 — [Claude] Run `./aws/datalake.py`**: `DL-5` green (the INT-11 parameters intact) before pass 2
  touches the grantor account; the drop-box statement and key grant read back with the 3.1 role name.
  **Read 2026-10-18**: `DL-5` green, and the drop-box policy names `awsds-prod-job-exec` in
  `AllowProductionPickupReadDelete` and `AllowProductionPickupList`. Read again on 2026-10-22 around
  pass 2's apply (19:35:09Z, 19:39:12Z) and after pass 5 (20:03:39Z): `DL-5` green each time, 0 failed.
- **7.3 — [Claude] Record the ECR non-grant**: one line in the log — cross-account pulls need the
  repository policy only, no key grant — so nobody "fixes" the absence later (Lesson 5's inverse: an
  absence that is correct, written down). **Recorded 2026-10-16** (the log).

### 8. Verify the boundary rather than declare it

**Action:** the session matrix — each cell a test with its result recorded, including the ones that
fail. **Why:** the promotion crosses account boundaries this stage just finished wiring, and every cell
is a place where a resource policy can be missing (INT-05/06 are the two most likely to surface as an
`AccessDenied` nobody can diagnose from the error). **Explanation:** run each from the stated session;
read every denial by its wording, never its exit code.

- **8.1 — [user] From Sandbox**, as the persona from a laptop and as the project role from a space wherever
  the two differ: no deployment target's infrastructure can be changed; a lake table reads through the share
  but will not write (the governed write is the job role's alone); a `PutObject` to an out-of-organization
  bucket is denied naming the perimeter (`docs/plan/architecture.md` §4.2 — exercised, not amended; an
  amendment would go through battery phase 4b); the drop-box accepts `PutObject` and refuses the matching
  `GetObject`; the registry answers the reader decision 10 named and nobody else.
  **The laptop half, written 2026-10-23** (`awsds-scientist-sandbox`): the registry pair is 3.4's; the
  drop-box pair is 2.5's drop and 2.6's read-back; the perimeter put is 6g 2.4's probe against a bucket
  outside the organization, refused naming the perimeter document (its log, 2026-09-18); the governed
  write refused on the lake's own bucket, with no S3 allow on a lake prefix in the set:

  ```bash
  echo probe | aws s3 cp - s3://awsds-data-curated/warehouse/trades/probe.txt --profile awsds-scientist-sandbox --region us-west-2
  ```

  and a deployment target's role refused to the Sandbox persona, whose session no Production trust names:

  ```bash
  aws sts assume-role --role-arn "arn:aws:iam::<Production>:role/awsds-prod-debug" --role-session-name probe --profile awsds-scientist-sandbox --region us-west-2
  ```

  The share's read-but-not-write is the space's: the project's query editor answers `SELECT count(*)
  FROM curated.trades` and refuses `INSERT INTO curated.trades VALUES (...)` with Lake Formation's
  wording, with the Sandbox sitting up. **The laptop half run by the user 2026-10-23** (the log): the
  lake put refused by the set's implicit deny, the debug role at the trust, the registry pair 3.4's;
  the perimeter put answered S3's bare `Access Denied` for a bucket another account owns, and the set
  holds no allow on such a bucket, so no laptop persona exercises `DenyS3ObjectWriteOutsideOrganization`
  by its wording: its proof stays 1c's inverted document. The space half reads as the project role, which
  holds no Lake Formation grant on the lake: Sandbox's tag re-grants name the Data Scientist User's set
  (the log, 2026-10-25), so its `SELECT` waits on 6f decision 1, as 6g 2.4's read does.
- **8.2 — [user] From a Production session as the data scientist**: 5.4's proofs, plus INT-06 — how
  much of the S3 **console** works for the persona under 1.1's principal branch, recorded as a fraction
  and written into `README.md` if part of it does not. The console's bucket list is `s3:ListAllMyBuckets`,
  which the set does not hold, so the reading starts at the bucket's own URL: the root listing, then
  `app-etl/outbox/`, each answered or refused. **Read 2026-10-23** in the user's console session (the
  log): the bucket list refused (`s3:ListAllMyBuckets`), the root listing refused (`s3:ListBucket`),
  the listing at `app-etl/outbox/` open with zero objects, every Properties panel and every Permissions
  panel refused, Block Public Access showing the bucket policy's explicit deny. **The fraction: one page
  works**, the object listing under a named prefix reached by URL, with its downloads; `README.md` says
  so, INT-06 is answered and open question 8 closed.
- **8.3 — [user] From the laptop, off the VPN**: a read of the named output prefixes succeeds through
  1.1's principal branch, and the same persona's read outside them fails, its wording naming the policy
  that refuses it (INT-05's laptop half, as D39 shapes it). The three commands of 5.4's last block, run
  on the split-tunnel profile or with the tunnel down: the first answers, the other two are refused by
  the bucket policy's two persona denies. **Run by the user 2026-10-23 with the tunnel down** (5.4's
  block, the log): the named prefix answered, the root refused naming the resource-based policy, the
  read outside a bare `403` until 5.4's `get-object` names its policy.
- **8.4 — [user] From a Staging session as the data scientist** (`DataScientistStagingAccess`, which 6b
  assigned): everything readable, nothing writable — including the buckets the pipeline writes to; the
  wording names `DenyEveryWrite`. No laptop profile reaches that set (read 2026-10-23): the block to add
  to the laptop's config, on the Data Scientist User's session, the account id Staging's:

  ```
  [profile awsds-scientist-staging]
  sso_session    = awsds-scientist
  sso_account_id = <Staging>
  sso_role_name  = DataScientistStagingAccess
  region         = us-west-2
  ```

  Then the reads that answer, and the writes refused with *"an explicit deny in an identity-based
  policy"*, `DenyEveryWrite`'s:

  ```bash
  aws glue get-tables --database-name app_outputs --profile awsds-scientist-staging --region us-west-2
  ```

  ```bash
  echo probe | aws s3 cp - s3://awsds-staging-outputs/probe.txt --profile awsds-scientist-staging --region us-west-2
  ```

  ```bash
  aws glue start-job-run --job-name awsds-staging-app-etl --profile awsds-scientist-staging --region us-west-2
  ```

  **Run by the user 2026-10-23** (the log): the catalog read answered an empty list, the Glue write was
  refused by `DenyEveryWrite`, and **the S3 put was refused by the data key first**, *"kms:GenerateDataKey
  … no resource-based policy allows"*, S3 asking the key before deciding the put, so the set's `s3:Put*`
  deny and the bucket's `DenyThePersonaAnyWrite` stayed unexercised (Lesson 20). A delete takes no key
  and exercises the set's own deny, expected *"an explicit deny in an identity-based policy"*:

  ```bash
  aws s3api delete-object --bucket awsds-staging-outputs --key probe.txt --profile awsds-scientist-staging --region us-west-2
  ```

  **Run 2026-10-23**: refused *"with an explicit deny in a resource-based policy"*, the bucket's
  `DenyThePersonaAnyWrite` named ahead of the set's deny (Lesson 20); the set's deny is proven on Glue,
  the bucket's on S3, the key's on the put, and 8.4 is read: nothing writable, three layers deep.
- **8.5 — [pipeline] The end-to-end**: run Stage 8's promotion against the real catalogs, its first run (Stage 8 pass 4, decision 23) — the
  integration tests now query the governed tables through Staging's share and the application's own
  tables, the artifact lands in Production, and the pandas
  test still fails everywhere it should. It is the stage's closing proof and the first fully meaningful
  promotion. **Written 2026-10-24 in the template's v0.4.0** (the log): the Glue job reads
  `curated.trades` through the share on the application slice's `--SOURCE_TABLE`, writes
  `app_outputs.trades_notional` and reads it back, inside the chain `staging-test` follows, which also
  reads the table as the deploy role; a planted drift in `GOVERNED_COLUMNS`, the unit tests' mocked schema moved with it, fails that leg and passes
  `test` (verification xiii). v0.3.0, the first run, carries none of it. **Run 2026-10-25** (the log; Stage
  8's): `v0.4.2`'s Staging leg read `curated.trades` through Staging's share as `awsds-staging-job-exec`, 30
  rows, wrote and read back the table, and Production's chain read the same 30 rows the next hour; the drift
  on `v0.4.5` passed `test` and stopped at Staging's governed read (Stage 8 ix).

### 9. `production/warehouse/` — the governed class of database (D40)

**Action:** the second half of the warehouse: a Redshift Serverless namespace in `VPC-Workloads`, the
estate's first governed schema, written by `awsds-prod-job-exec`, put under Lake Formation, and the
pipeline's path for deploying what a Production workload writes. **Why:** [Stage 5b](stage-05b-redshift-serverless.md)
built the sandbox class and [6h](stage-06h-redshift-connection.md) connected a project to it. The governed
class waits for this stage because its writer, its CMK and its deploy credential exist here; a namespace in
Sandbox would put governed data in the least-governed account (D22, D17). **Explanation:** the specification
is the Sandbox code as built, `terraform-live/sandbox/warehouse/` and `warehouse-compute/`, whose comments
carry 5b's readings, with the differences 9.1 lists. What is new in this account is the Lake Formation half.

> **This is the first governed store outside Data Governance, and D22 is the line it crosses.** D40 argues
> the trade and names the compensation: the warehouse's schemas reach readers only through Lake Formation
> (9.5), with the same permission layer as the lake's. The Lake Formation grants keep one grantor: Data
> Governance registers the datashare and grants it beside `raw` and `curated` (decision 14, taken
> 2026-10-24), while the `GRANT`s inside `governed` are Production's, in the register's Redshift half, and
> 9.8 tells the register in the same sitting.

- **9.1 — [Claude] Write `production/warehouse/` and `production/warehouse-compute/` from the Sandbox
  slices**, with the same `[P]`/`[E]` split: the namespace holds the data, the users and the `GRANT`s and is
  never destroyed, and the workgroup is `[E]` because Redshift Serverless has no pause. What changes in the
  copy:
  - **Network and key.** The subnets and the VPC come from `production/workloads/`, its two private subnets
    in two AZs (6c), never from `production/foundation/`, which is `VPC-SharedServices` in this account. The
    namespace encrypts under `alias/awsds-prod-data`, read from `production/data/`'s state.
  - **What stays behind.** Everything that exists for SageMaker projects: `projects`, `datazone_domain_id`,
    the project and access-role policies, the per-project `5439` rules and the `AmazonDataZoneProject` tags.
    Their absence is 9.3's control.
  - **The key statement.** The data CMK needs `AllowRedshiftServerlessViaServiceInThisAccount`
    (`kms:ViaService = redshift-serverless.<region>.amazonaws.com`), the statement Sandbox's first apply
    lacked (`sandbox/data/main.tf`). It lands in `production/data/` at pass 3. Without it `CreateNamespace`
    fails with *"the key … is inaccessible"* and leaves an orphan admin secret behind (`EXC-12`), so the retry
    needs a new admin username.
  - **The admin secret.** `manage_admin_password = true`, with no `admin_password_secret_kms_key_id`: the
    data key refuses it. Sandbox's first rotation succeeded on 2026-10-20 with no workgroup, against AWS's
    page ([the 5b log](../../log/log-stage-05b-redshift-serverless.md)), and the database took the
    password, read from the Data API's password sessions of 2026-10-25 (the log); the Production secret
    rotates on the same schedule, so `EXC-13` gains a Production row.
  - **The databases.** `db_name = "warehouse"`, as in Sandbox; `governed` is created in SQL at 9.3. `db_name`
    adds a database beside `dev` rather than replacing it, so the namespace holds three, and `WH-6` expects
    exactly `governed`, `warehouse` and `dev`.
  - **The cost guards.** `base_capacity = 4`, `max_capacity = 8`, `price_performance_target` with
    `enabled = false` (the service turns it on, at Balanced, by default), and the `serverless-compute` usage
    limit with `breach_action = deactivate` in the same apply, its amount decision 7. Three readings bound
    what the limit guards: its counter belongs to the usage-limit object, so each `make up` starts it near
    zero and "monthly" bounds one workgroup's life; `UsageLimitConsumed` rounds up, so a limit of N bites
    between N−1 and N RPU-hours; and a second `deactivate` limit is refused while a looser `log` limit is
    accepted. `max_query_execution_time` is set and not relied on: in Sandbox a query ran 23,601 s against a
    1,800 s ceiling, for a reason still open (`sandbox/warehouse-compute/main.tf`). `auto_mv` is on by
    default, which is compute nobody asked for; decision 7 settles it with the amount.
  - **The provider.** `hashicorp/aws` 6.66.0 or later (Sandbox locks 6.68.0). An earlier provider plans the
    service's undeclared `config_parameter` keys away on every plan, and `enable_large_strings_opt_in`, which
    the service returns from 2026-10-13, stays undeclared.
  - **Logs.** The three groups are pre-created with a retention period, so `EXC-10` stays at one.
    Production's `useractivitylog` carries governed values in its SQL text; its retention, and whether it is
    encrypted under the data key where Sandbox's groups are not, are decision 8.
  - **Alarms.** `ComputeCapacity` and `DataStorage`; `WH-4b` fails without the second. Sandbox's two
    publish to `awsds-sandbox-alerts` since 2026-10-18 (PR #181), so the copies publish to
    `awsds-prod-alerts`, whose policy admits CloudWatch since PR #179 (`CloudWatchAlarmsOfThisAccount`).
    D12's budget still notifies nobody.
  - **Ingress.** `5439/tcp` from the job's security group, group-to-group, never a CIDR: the two subnets also
    hold the MWAA Serverless workers (Stage 10). The deploy runner has no path to `5439`, since
    `VPC-SharedServices` and `VPC-Workloads` do not peer, so its door is the Data API (9.4).
  - **Machinery.** `layers.py` rows for `warehouse` (`[P]`, 53) and `warehouse-compute` (`[E]`, 54), the
    compute row carrying `usd_per_hour = 1.44` as its ceiling, as Sandbox's does.
- **9.1 — Written 2026-10-22, planned, unapplied** (the log): the two slices from Sandbox's, with the
  differences above; `terraform-live/production/warehouse/` plans *"9 to add"* as `awsds-infra-prod` (the
  three audit groups, the two alarms, the role, the namespace, the security group and its one rule), and
  `production/warehouse-compute/`'s plan stops at *"Unable to find remote state"* for the namespace, the
  expected reading. The compute is held from `make up ENV=production` by `layers.py`'s refusal 9
  (`HELD_FROM_UP`), since the slice reads the namespace's state and a Production sitting's `make up` would
  otherwise stop at it after raising the endpoints; the row leaves in the sitting that applies the
  namespace. `production/data/`'s key policy admits `/aws/redshift/*` for the groups (applied with 5.1,
  2026-10-22); `max_query_execution_time` is Sandbox's 120 s; the lock is Sandbox's compute slice's.
  **Written 2026-10-23**: 9.4's Data API grant on `awsds-deploy-prod` (applied the same evening);
  `production/workloads-egress/` taking `GROUPS=redshift` (the variable `optional_service_groups` and its
  wiring, as `sandbox/egress/` has them; the slice's plan unchanged, 16 to add), so the sitting that
  raises the compute runs `make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift`;
  and `WH-15` naming each account's
  `make down` (9.8). Owed at the apply: `EXC-13`'s row, and the refusal-9 row's removal from `layers.py`. **Applied 2026-10-23 at 22:07 UTC** (the log), from a fresh plan of the same nine, re-planned `No changes`: the namespace `awsds-prod-warehouse` `AVAILABLE` with `warehouse` and `dev`, the three audit groups at 30 days, the two alarms `OK`, the role with no policy, the security group; the admin secret is Redshift's, `rate(30 days)`, its first rotation due 2026-11-22 with or without a workgroup (`EXC-13`'s Production sentence); `./aws/warehouse.py awsds-infra-prod` OK, every `--sql` reading a note until a workgroup exists. The refusal-9 row is gone, and `production/warehouse-compute/` plans *2 to add* (the workgroup and the usage limit, 22:10 UTC), raised by the sitting that runs 9.3.
- **9.2 — [Claude] Leave the namespace role `awsds-prod-warehouse-exec` with no policy until 9.5's shape
  names one.** In Sandbox the role holds nothing, which is why the auto-mounted `awsdatacatalog` database
  fails there by design. A Glue or Lake Formation grant here turns `awsdatacatalog` on over Production's
  resource links to the lake, with the engine reading as this role rather than as the caller: a second reader
  of the lake, bounded only by the role's own grants. If the chosen shape needs the role, its Lake Formation
  grants are enumerated in the register, and `WH-1b`, which fails on any attached policy, gets a Production
  rule. In every case the role holds no `s3:*` on a lake prefix (D13), and 9.6 measures it.
- **9.3 — [Claude⚡] Create `governed`, the first governed schema and its grants**, as 6h 1.1-1.5 did for
  `lab`:
  - **Ownership.** `AUTHORIZATION` takes a user, not a role. The owner is a non-login user
    (`PASSWORD DISABLE`), never the deployer's database user, which would give the pipeline owner rights on
    the schema.
  - **Quota.** Set one: a schema defaults to `UNLIMITED`. The range is 2,048–524,288,000 MB, a breach is
    refused at commit after the transaction has overshot, and the value cannot be read back (`WH-13` is a
    permanent note).
  - **`PUBLIC`.** Read each database's ACL (`governed`, `warehouse`, `dev`) and revoke `CREATE` where it
    appears. Sandbox's readings disagree on a fresh database (`=UC/rdsdb` in 6h's log, "not owed" in
    `AWS_STATE.md`), so the reading decides.
  - **Database users.** A role's database user is `IAMR:` plus the session's `RedshiftDbUser` tag, or
    `IAMR:<role name>` for a role without one (6h verification iii). The job role's and the deploy role's
    sessions were never measured, and a user that `GetCredentials` creates holds nothing, so 6h's order
    applies: create both users first, grant through a role, and read `pg_user` after the first real
    connection.
  - **Two creators.** Under 9.4 the deployer's user creates the tables and owns them, and the job role's
    user writes rows into them. Redshift sets default privileges per creating user, with no `FOR ROLE`, no
    wildcard and no tag (6h), so the schema needs `ALTER DEFAULT PRIVILEGES FOR USER "<deployer user>" IN
    SCHEMA <schema> GRANT SELECT, INSERT, DELETE ON TABLES TO ROLE <rw role>`, plus a `GRANT` for each table
    that predates it, and every further creator (a load job's staging tables, Stage 10's per-workflow roles)
    owes its own statement. `svv_default_privileges` is the only reader: `pg_default_acl` is empty on this
    platform and `relacl` cannot see a grant to a role. `WH-14` fails on a table no role can read. Decision 6
    chooses between this and DDL run as the job role, which keeps one creator and gives up 9.4's separation.
  - **The statements, prepared 2026-10-23** for the Data API as the admin (`redshift-connection.md` §S's
    shape, 6h's order), one `execute-statement` each, `--workgroup-name awsds-prod-warehouse
    --secret-arn <the namespace's admin secret>` and the database named per statement. The theme was a
    proposal, `trades`, the data `curated.trades` holds; **confirmed by the user on 2026-10-24 (chat), with the
    quota of 1 TB**, so the statements below run as written at the next Production sitting (`runbooks/promotion.md` §W). **Run 2026-10-24,
    00:27 to 00:29 UTC** (the log): every statement `FINISHED` through the Data API as the admin, the `PUBLIC` readings
    before (`=UC/rdsdb` on `public` in each database, no database ACL) and after (`=U/rdsdb`, the databases'
    ACLs without `PUBLIC`), `pg_user`, `svv_user_grants` and `svv_default_privileges` as written,
    `./aws/warehouse.py awsds-infra-prod --sql` passing; what 9.3 leaves to the roles' first connections is
    verification xxv. The audit groups carry the admin's connection, its statements and the three `create`
    events (9.8's reading), where Sandbox's carry nothing (`EXC-16`).
    First the readings 9.3 asks for, `select nspname, nspacl from pg_namespace where nspname = 'public'`
    in `warehouse`, `dev` and `governed`, then:

    ```sql
    -- in warehouse, then dev, then governed (after its CREATE): PUBLIC loses what every new database grants it
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    REVOKE ALL ON DATABASE warehouse FROM PUBLIC;
    -- the class container (in warehouse)
    CREATE DATABASE governed;
    -- in governed: the owner, a non-login user; the schema, bounded; the two roles; the two database users
    CREATE USER gov_trades_owner PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
    CREATE SCHEMA trades AUTHORIZATION gov_trades_owner QUOTA 1 TB;
    CREATE ROLE gov_trades_rw;
    GRANT USAGE ON SCHEMA trades TO ROLE gov_trades_rw;
    CREATE ROLE gov_trades_ddl;
    GRANT USAGE, CREATE ON SCHEMA trades TO ROLE gov_trades_ddl;
    CREATE USER "IAMR:awsds-prod-job-exec" PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
    CREATE USER "IAMR:awsds-deploy-prod" PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
    GRANT ROLE gov_trades_rw TO "IAMR:awsds-prod-job-exec";
    GRANT ROLE gov_trades_ddl TO "IAMR:awsds-deploy-prod";
    -- what the deployer's user creates, the job role's role may write (per creating user, no FOR ROLE)
    ALTER DEFAULT PRIVILEGES FOR USER "IAMR:awsds-deploy-prod" IN SCHEMA trades GRANT SELECT, INSERT, DELETE ON TABLES TO ROLE gov_trades_rw;
    ```

    The two `IAMR:` names assume a session carrying no `RedshiftDbUser` tag (6h verification iii);
    verification xxv reads `pg_user` after each role's first connection and renames a user that landed
    elsewhere. The quota, 1 TB, is the user's figure for the governed schema (2026-10-24).
  - **Role tags.** These roles are this repository's, so their `tags` can pin `RedshiftDbUser` and
    `RedshiftDbRoles`, the mechanism 6h could not use on a role SMUS owns. Whether a Glue or SageMaker session
    overrides a role tag is unmeasured, and a `RedshiftDbRoles` value naming a missing role is ignored without
    an error.
  - **No project.** No connection and no `AmazonDataZoneProject` tag: D26 keeps deployment targets out of
    the domain (`DenyDataZoneEntirely` on `Workloads`), so 6h's three layers collapse to the `GRANT`, and
    `WH-7` reads no project tag on this namespace and workgroup. `objectives.md` makes the absence a
    requirement: a governed database is read through 9.5's shape and written by 9.4's pipeline, never
    connected to a project.
- **9.4 — [Claude] Write the deploy path: the repository holds the DDL and the load job, the pipeline runs
  the DDL, and `awsds-prod-job-exec` writes the rows**, the principal 2.4 proved the governed S3 write with.
  Which of D28's classes that is: decision 6.
  - **The door.** The Data API, the deploy runner's only path to the workgroup, with IAM authentication
    rather than the admin secret. A pipeline holding the admin secret can grant itself anything, which is the
    register's whole content, and IAM leaves no standing credential (6h decision 2).
  - **The grant.** `redshift-data:ExecuteStatement`, `DescribeStatement`, `GetStatementResult` and
    `CancelStatement`, and `redshift-serverless:GetCredentials`, on `workgroup/*`: the workgroup id changes on
    every re-create. Stage 8 step 4.1 writes them into `awsds-deploy-prod`'s identity policy in
    `production/foundation/`; its ceiling, `Allow *` less the module's denies, needs none of them (read
    2026-10-22), and `iam:PassRole` to the job role stays scoped by `iam:PassedToService` (3.1).
  - **The loop.** Poll `DescribeStatement` with a delay between polls (the API has no waiter, and an unpaced
    poll reads empty), and cancel on timeout or failure. The Data API does not cancel a statement when its
    client stops polling: in Sandbox one abandoned statement ran 6 h 33 min and billed 9.44 USD.
  - **Idempotence.** A `GRANT` is state no plan sees, so every statement is `IF NOT EXISTS` or guarded, and
    verification xxii runs the promotion twice.
  - **The compute is raised by hand.** `DenyRedshiftCostGuardTamperingExceptInfrastructure` exempts only
    `InfrastructureAccess`, so `awsds-deploy-prod` cannot call `UpdateWorkgroup`, `UpdateUsageLimit` or
    `DeleteUsageLimit`: it can neither destroy `production/warehouse-compute/` nor lift a breached limit. The
    operator raises the compute before the DDL job and takes it down after. A breached limit leaves the
    workgroup `AVAILABLE` with leader-node queries answering, so the job reads a refused query, never the
    workgroup's status.
  - **The grant, written 2026-10-23** in `production/foundation/deploy-anchors.tf`,
    `apply_application_in_this_account`'s `RunTheGovernedWarehouseDdl`: the four Data API actions and
    `redshift-serverless:GetCredentials` on `workgroup/*`, inline on `awsds-deploy-prod`'s
    `apply-application`. Planned as `awsds-infra-prod` with the alerts var-file at 16:24 UTC: *"Plan: 0
    to add, 1 to change, 0 to destroy."*; **applied 2026-10-23 at 21:19 UTC** from a fresh plan of the
    same count, on the user's authorization, re-planned `No changes` (the log). **Amended 2026-10-25**
    (the log): `DescribeStatement`, `GetStatementResult` and `CancelStatement` authorize on no resource, so
    under `workgroup/*` they matched nothing and v0.4.2's DDL job was refused following its own statement
    after the table was created; they moved to `FollowItsOwnStatements`, `Resource "*"` with
    `redshift-data:statement-owner-iam-userid` equal to `aws:userid`, applied 01:47 UTC. The load job's
    path needed the job group's egress to the workgroup's group on 5439, which 9.1 had written only as
    the warehouse's ingress: `production/warehouse/`'s `jobs_to_warehouse_5439`, applied 01:59 UTC.
  - **Written 2026-10-24** (the log; decision 15), in the template's next release, v0.4.0, after
    v0.3.0's first promotion: `warehouse/trades.sql`, `CREATE TABLE IF NOT EXISTS
    trades.trades_notional`, run by the Production leg's manual job `production-warehouse-ddl` through
    the Data API as `awsds-deploy-prod`, a read every 5 s and a cancel past 300 s, read back; the load
    `glue/load_warehouse.py`, the Glue job `awsds-prod-app-etl-load` of the application slice, which
    reads the application's table, takes temporary credentials for `governed` through the
    `redshift-serverless` endpoint (`ConnectToTheGovernedWarehouse` on the job role) and writes over
    JDBC on the workgroup's port, delete and insert in one transaction; and the workflow
    `app-etl-warehouse` with its chain at `cron(30 7 * * ? *)`, Production's alone. The driver is the
    one Glue provides to its Spark jobs, `redshift-jdbc42-2.1.0.29` for Glue 5.0 and 5.1 on AWS's page;
    Glue 6.0's is read at the first run. The compute is raised by hand before the DDL job and the
    chain's run, and the chain fails while it is down.
- **9.5 — [Claude⚡] Put the namespace under Lake Formation by decision 5's shape, and read the result
  rather than the plan.** This is what `objectives.md` requires (*"the governance model does not fork"*).
  The two shapes:
  - **(i) A federated catalog**: the namespace registered with the Glue Data Catalog (`aws_glue_catalog` with
    its `federated_catalog` block) and shared by Lake Formation, read by Athena through the Iceberg-engine
    switch below.
  - **(ii) A Lake Formation-managed datashare**: the producer grants `USAGE ON DATASHARE … VIA DATA CATALOG`,
    the data lake administrator registers it (`lakeformation register-resource`) and maps it to a
    **federated database**, and Lake Formation permissions decide the rest. No Iceberg-engine switch.

  > **The Iceberg-engine switch creates a resource this project did not choose** (read 2026-09-20). The
  > federated catalog's *"Access this catalog from Iceberg compatible engines"* is what lets Athena and EMR
  > read the namespace at all, and AWS: *"To enable these query engines to read and write to Amazon Redshift
  > namespaces, AWS Glue creates a **managed Amazon Redshift cluster** with the compute and storage resources
  > required to perform read and write operations without impacting Amazon Redshift data warehouse
  > workloads."* That is a cluster, the always-on shape D12 rules out and `DenyRedshiftProvisionedClusters`
  > refuses at the root; unpriced and unsized; read and write; and encrypted under *"an AWS managed key"*
  > unless a customer managed key is supplied, against `docs/GOVERNANCE.md` §Encryption's per-account CMK
  > rule. It is needed only for the Iceberg engines: *"You don't need to enable data lake access to access the
  > federated catalogs using Amazon Redshift."* Lesson 17 in full.

  > **Two hazards on whichever object is created, both already paid for once.** It carries
  > `create_database_default_permissions`, the `IAMAllowedPrincipals` default that acts at creation time
  > (1.3's callout), and a catalog or federated database born deferring to IAM is a governed schema governed
  > by nothing. So: create it alone, read it back, revoke `IAMAllowedPrincipals` if it is there, and only
  > then create anything inside it (Recipe D, third instance). And the mapping is *namespace → multi-level
  > catalog, database → catalog, schema → database, table → table*: a Redshift "database" is a Glue
  > *catalog* and a Redshift "schema" is a Glue *database*, so a grant written from intuition addresses the
  > wrong level (Lesson 53).

  **Shape (ii) as commands, read on AWS's step pages 2026-10-24** (`docs/REFERENCES.md`), for the
  Lake Formation account, written `<LF>`: Data Governance, by decision 14 (taken 2026-10-24).
  The datashare's ARN is `arn:aws:redshift:us-west-2:<Production>:datashare:<namespace id>/trades_lf`
  and exists only after the first statement:
  1. **[Claude⚡] Production, the compute up, the Data API as the namespace's admin in `governed`**, one
     statement each: `CREATE DATASHARE trades_lf;`, `ALTER DATASHARE trades_lf ADD SCHEMA trades;`,
     `ALTER DATASHARE trades_lf SET INCLUDENEW = TRUE FOR SCHEMA trades;` (later tables join; an existing
     one needs `ADD ALL TABLES IN SCHEMA trades`), `GRANT USAGE ON DATASHARE trades_lf TO ACCOUNT '<LF>'
     VIA DATA CATALOG;`. `SYS_DATASHARE_CHANGE_LOG` records each.
  2. **[Claude⚡] Production, as `awsds-infra-prod`**: `aws redshift authorize-data-share
     --data-share-arn <ARN> --consumer-identifier DataCatalog/<LF>`, expected `AUTHORIZED`.
  3. **[Claude⚡] `<LF>`, its Lake Formation administrator**: `aws redshift describe-data-shares
     --data-share-arn <ARN>`; `aws redshift associate-data-share-consumer --data-share-arn <ARN>
     --consumer-arn arn:aws:glue:us-west-2:<LF>:catalog`, expected `ACTIVE`; `aws lakeformation
     register-resource --resource-arn <ARN>`, no role and no federation flag; `aws glue create-database`
     with `FederatedDatabase` `{"Identifier": <ARN>, "ConnectionName": "aws:redshift"}` and
     `CreateTableDefaultPermissions` `[]`, read back by `list-permissions` for `IAM_ALLOWED_PRINCIPALS`
     before anything else (the second callout above); the LF-Tags on the database, and on its tables once
     one exists; the grant to Sandbox's account, `DESCRIBE` on the database and `SELECT` on its tables,
     by LF-Tag expression or by name. A federated database takes no write or metadata permission.
  4. **[Claude⚡] Sandbox, its Lake Formation administrator**: the RAM invitation if one is pending, then
     `DESCRIBE` and `SELECT` to the project's access role on `<LF>`'s database (a receiving account grants
     only to its own principals and cannot pass the share on). The project role is not the principal the
     door evaluates (9.7): its grant of 2026-10-25 went unused and was revoked the same day.
  5. **[Claude⚡] Sandbox, its workgroup up, the Data API as its admin**: `CREATE DATABASE governed_trades
     FROM ARN 'arn:aws:glue:us-west-2:<LF>:database/governed_trades' WITH DATA CATALOG SCHEMA
     governed_trades;`, a statement of its own (no transaction), then `GRANT USAGE ON DATABASE
     governed_trades` to the project's database user once its first IAM connection has created it; a
     consumer grants on the whole database only.
     9.7 reads it as the project with `SELECT`, the only verb a shared object takes.

  What the pages leave unsaid and the sitting measures before 9.7 relies on it: **whether Sandbox reads
  while Production has no workgroup**, the estate's state between sittings (a paused provisioned producer
  keeps sharing; a Serverless producer with no workgroup is not documented), so a read may cost both
  workgroups at once, 2.88 USD per hour; whether a cross-account LF-Tag grant works on a federated
  database (named grants are the fallback); which principal Lake Formation evaluates for a database user
  the `RedshiftDbUser` tag names, the SMUS access role's mechanism (6h), when the pages show only
  `IAMR:<role>` users; and whether a share with no table registers, since `trades` has none. One page says
  a `CREATE USER` user cannot read a share registered with Lake Formation, while AWS's two blogs create
  `IAMR:` users with `PASSWORD DISABLE` and read: on the consumer side no user is created by hand, the
  first IAM connection creates it. The cost: the consumer pays its compute, the producer its storage. The
  producer's row- and column-level security does not travel; Lake Formation's filters do. Terraform
  covers parts of steps 2 and 3 (`aws_redshift_data_share_authorization`,
  `aws_redshift_data_share_consumer_association`, `aws_lakeformation_resource`, `aws_glue_catalog_database`'s
  `federated_database`), each with an unmeasured mismatch the step pages show: the authorization's read
  keeps the resource only while that identifier is listed, the registration sends `UseServiceLinkedRole`
  unless told not to, and the database cannot send an empty `CreateTableDefaultPermissions`. So the first
  sitting runs the commands, reads each object back, and Terraform adopts what plans `No changes` after an
  import. **9.6 and 9.7 need a table in `trades`**: `trades.trades_notional`, which v0.4.0's DDL job
  creates and its load fills (9.4, written 2026-10-24), after `v0.3.0`'s first promotion; 9.5's share can
  wait for it or be created first, `INCLUDENEW` adding the table. **Built 2026-10-25** (the log), the
  five steps as commands: the datashare in `governed` with the table, authorized to Data Governance's
  catalog; the association, the registration with no role and the federated database there, its only
  permission the creator's (a `Description` refused beside a federation source), tagged `layer=curated` and
  `classification=internal`, which Sandbox's account reached through its existing tag grants with no named
  grant; in Sandbox the consumer database and its `USAGE`. What the pages left open, read: a password user
  is refused (*"not authenticated with IAM credentials"*), the consumer evaluates the session's IAM
  principal, the share's table needs `TEMP` on the session's database, and the share reads with the
  producer's workgroup gone. **The adoption, written and planned 2026-10-25 with the environment down**
  (the log): `production/warehouse/datashare.tf` adopts the authorization and
  `data-governance/data/warehouse-share.tf` the association and the federated database, each through an
  `import` block removed after the apply. The plans read *1 to import* and no change in Production, once
  `allow_writes` was left undeclared (the provider reads it back as unset, and a declared `false` planned
  a replacement), and *2 to import, 1 to change* in Data Governance, the change the provider's five
  default tags on the database. The registration and the two LF-Tag assignments stay by hand:
  `aws_lakeformation_resource` has no importer, `aws_lakeformation_resource_lf_tags` documents none, and
  deregistering is denied by the Data OU SCP. **Applied 2026-10-25 on the user's authorization**, 17:25 to
  17:26 UTC (the log): *1 imported* in Production and *2 imported, 1 changed* in Data Governance, each
  re-planned `No changes`, the import blocks removed after; the registration and the tags stay commands,
  recorded in `AWS_STATE.md`'s two registers.
- **9.5a — [Claude reads, user decides] Settle the collision between the Iceberg-engine switch and
  `DenyRedshiftProvisionedClusters`**, which is live at the root since 5b. If AWS Glue creates its managed
  cluster in this account, the deny is either what breaks the Athena path or what the path breaks, the same
  collision Stage 15 decision 1 has between `DenyGuardDutyTampering` and Audit's own detector. **Read before
  choosing:** whether the cluster is created in the customer account at all, under which principal (a
  service principal is not bound by an organization policy), and whether CloudTrail shows `CreateCluster`.
  The deny's `CreateCluster` half is attached and unprobed (`POLICIES.md`), so verification xxiii is its
  first exercise, and `WH-8` lists only serverless objects, so it cannot see a Glue-managed cluster. Then
  one of: **(a)** carve the Glue service principal out of the deny, which reopens what the estate wanted
  closed; **(b)** take shape (ii), which needs no switch and therefore no cluster; **(c)** leave the switch
  off, which makes the federated catalog readable from Redshift only and leaves a Sandbox project nothing to
  read. **Recommended: (b)**, decision 5. Decision 5 took the datashare on 2026-10-22: no switch, so no
  cluster, and this reading is owed only if the federated catalog comes back.
- **9.6 — [user] Prove the governed pair, the way 2.4 proved the lake's.** Under `awsds-prod-job-exec`: a
  write into the governed schema succeeds; the same role's direct `PutObject` to a lake bucket is still denied;
  and the namespace role reaches no lake prefix. Read every wording. Since 2026-10-24 the write is the
  chain `awsds-prod-chain-app-etl-warehouse`'s run with the compute up, started by its schedule or by
  `aws stepfunctions start-execution` as the infrastructure user, its job's log printing the database
  user and the count; the direct put is 2.4's reading, the role unchanged since; the namespace role holds
  no policy (9.2). **Run 2026-10-25** (the log), after the job group's egress to the workgroup on 5439: the
  load wrote 30 rows as `IAMR:awsds-prod-job-exec` into the table `IAMR:awsds-deploy-prod` created; the
  direct put stays 2.4's refusal; `awsds-prod-warehouse-exec` holds no policy (read 02:41 UTC).
- **9.7 — [user] Prove INT-24: a Sandbox project reads a governed table through the shape 9.5 built.** There
  is no network path and there does not need to be: Sandbox does not peer with `VPC-Workloads`, and the
  absence is a control (`docs/NETWORK.md` §3). Neither shape opens a Redshift connection from the project.
  **The project's Data page against a cross-account connection is excluded by the requirement**
  (`objectives.md`, 2026-09-20): it makes a Redshift `GRANT` the control over governed data, the fork the
  brief forbids, and taking it means revising `objectives.md`. If neither shape works, a governed table
  reaches Sandbox as it does today, through the lake, and the warehouse stays a Production-internal engine.
  What 9.7 also settles: whether a Lake Formation share of a **federated** resource preserves the TBAC
  expressions this estate grants by. Both AWS pages say tags may be used, more than DataZone's Glue path
  offers (it refuses LF-TBAC, Stage 6f 3.2); a share that takes only named resources is a finding, recorded
  in the register as one. On the datashare path, read the revoke too: *"the associated permissions and
  objects in Lake Formation are not automatically deleted"*, so a revoke on one side leaves rows on the other.
  A refusal on this path reads as Lake Formation's (*"Required Describe on <database>"*, 6h's `raw`
  refusal) or as Glue's *"An unknown error occurred"*; attribute it from CloudTrail's `errorMessage`, never
  from `eventName`. A table's *"Required Describe"* says nothing of its existence: `glue get-table` gives it
  for a missing table and an existing one alike to a principal with no grant, where `get-database` answers
  a missing database `EntityNotFoundException` (Stage 18 7.2, 2026-10-22). **Read 2026-10-25** (the log):
  `eighth-experimentation`'s Query editor, as `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, read 30
  rows of `governed_trades.trades.trades_notional`, dated 2026-10-01 to 2026-10-05, and again with
  Production's workgroup destroyed. The door took three grants the pages did not name, all to the session's
  principal, the project's access role: its catalog read (`sandbox/warehouse/`'s
  `ReadTheGovernedShareCatalog`), its Lake Formation grant, and `TEMP` on `sandbox` for the database user
  (`redshift-connection.md` §G). The share preserves the TBAC expressions the estate grants by: the lake's
  tag grant to Sandbox's account reached the federated database. **Read a third time on 2026-10-26** (the
  log): the same query answered the same row with the project role's grant revoked and Production's
  workgroup destroyed, so the access role's grant alone serves the door.
- **9.8 — [Claude] Close the paperwork in the same sitting**: `docs/AWS_STATE.md` (the Lake Formation
  grants on the federated database, Data Governance's by decision 14, `EXC-13`'s Production row, and the database users nobody created:
  `IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>`, a superuser session whenever `InfrastructureAccess`
  reaches the database by IAM, and the service's `rdsdb`), `docs/GOVERNANCE.md` (§Accounts' Production row,
  and the warehouse as a thing Lake Formation governs), `terraform-live/README.md`, `docs/NETWORK.md`
  §2/§2.1/§9 for the security group, and `INT-24`'s row brought to what 9.7 measured. `./aws/warehouse.py`
  already reads Production; it gains `WH-1b`'s Production rule if 9.2 grants the role, a cluster reading if
  9.5a takes (a), and `WH-15` names each account's own `make down` since 2026-10-23. **The audit
  export is not assumed**: Sandbox's carries nothing while a workgroup exists (`EXC-16`), so before the
  Production groups are called an audit trail, read one user connection and one user statement in them,
  logged while the workgroup was up (Lesson 62). **Carried by 2026-10-25**: `docs/NETWORK.md`'s rows and
  `terraform-live/README.md` on 2026-10-24; the Lake Formation and Redshift registers in `AWS_STATE.md`,
  `INT-24`'s measurement and the job group's 5439 rule in `docs/NETWORK.md` on 2026-10-25; the audit
  export read (verification xxvi).

---

## Deliverables

Each is written so its output differs between working and broken (Lesson 13). **The mechanical half is
`./aws/deploytargets.py`** ([`aws/INDEX.md`](../../../aws/INDEX.md)): the buckets, CMK and workgroup
enforcement; the package groups with their policies; the job and debug roles with their trust shapes;
the LF settings in every account that has any (`DT-5` — `DL-5`'s twin); the share, links and regrants with no
pending invitation; Staging's share read-only, every grant `DESCRIBE` or `SELECT`, and no Staging copy of a
governed table; the alarm rule; the persona sets' owed allows read back; the job settings
where decision 9 put them (`DT-11`); the job log groups in both accounts (`DT-12`). The behavioural proofs are the stage's own (Lesson 20):

- **The producer pair (INT-03):** a curated Iceberg table, declared before its first write, written
  cross-account under `awsds-prod-job-exec` — and the same role's direct `PutObject` to the same bucket
  denied.
- **The pickup (INT-10):** the drop-box read, curated, and emptied by the job of what it consumes, `EXC-02`'s objects removed by hand on 2026-10-24;
  the writer still cannot read back what it wrote.
- **The registry gate (INT-07):** approval only under `awsds-deploy-prod` among the principals outside this
  account; the Sandbox reader decision 10 named reads status and nothing else; the Staging deploy role reads an approved version.
- **The workgroup boundary:** a client-requested result location is overridden into the enforced one;
  the scan limit cancels.
- **The job settings:** a `Create*Job` without them is refused from a role that is not the job's own, naming
  the policy decision 9 chose.
- **The escape hatch:** closed at rest, open only inside an approved window, alarmed on every successful
  assumption, and unable to become a notebook (the OU SCP names the denial).
- **The promotion (8.5):** Stage 8's chain against real catalogs, end to end.
- **The governed warehouse (step 9):** a governed schema whose tables the deployer's user creates and the
  job role's user writes, under a default privilege `svv_default_privileges` reads back; the Lake Formation
  object 9.5 created carrying no `IAMAllowedPrincipals`; no project tag anywhere on it; and INT-24 answered
  by measurement rather than by intention.

## Validation

1. Run `./aws/deploytargets.py` — all `DT-*` pass; diff two runs across the stage (only timestamps may
   change).
2. Run `./aws/datalake.py` after every `data-governance/data/` apply — `DL-5` green, and `DL-5`/`DL-13`
   reading Production once 1.3 adds it.
3. Run `./aws/egress.py` §6 at session end — **passes 0-5 add nothing metered, and the reading proves it.
   Pass 6 does**: a Redshift Serverless workgroup bills nothing at rest and **1.44 USD/hour while a query
   runs**, so after step 9 `./aws/warehouse.py`'s burn line is read beside it. `ComputeSeconds` lands per
   half-hour interval, so a reading taken at the session's end under-reports; read it again after the next
   interval.
4. Run `./aws/warehouse.py` after pass 6, with `--sql` for the database half. In Production `WH-1`, `WH-2`,
   `WH-3` and `WH-15` read `note` unless the `[E]` compute is up; `WH-6`, `WH-12` and `WH-14` need the
   database session; `WH-1b` needs its Production rule if 9.2 grants the namespace role a policy; `WH-4b`
   needs the `DataStorage` alarm; `WH-7` reads no project tag; `WH-13` is a permanent note. `WH-15` names
   `make down ENV=sandbox` and assumes interactive use, so a batch load can trip it legitimately until 9.8
   adapts it.
5. Read every denial by its wording, never its exit code (standing rule since 1c).

## Cost

Measured (`docs/PRICING.md`, `docs/plan/cost-model.md`), us-west-2:

| Item | Cost | Layer |
|---|---|---|
| `alias/awsds-prod-data` + the Staging CMK | ~USD 1/key-month | `[P]` |
| Package groups, workgroups, LF grants, links, resource policies | free at rest | `[P]` |
| Outputs/derived storage | cents at lab scale | `[P]` |
| Producer/pickup Glue runs | 0.44 USD/DPU-h, 10-min minimum, on-demand | metered per run |
| Athena queries | 5 USD/TB scanned — the workgroup limit is the guard | metered |
| The endpoints of `production/workloads-egress/` and `staging/egress/` while a session needs them | 0.010/h each, single-AZ: six per VPC, 0.060/h per slice | `[E]` |
| Staging's own account overhead (Config recorder etc.) | ~USD 0.5-1/month at rest, already being paid — the account exists; a build's creates and deletes add Config items: 0.71 of Staging's 1.52 over Stage 18's window (2026-10-17 to 2026-10-21, estimated, Cost Explorer) | — |
| **`production/warehouse-compute/`** (step 9) | **0.00/h at rest · 1.44 USD/h while a query runs** at `base_capacity = 4`, 2.88 at `max_capacity = 8` (0.36/RPU-h, 60-second minimum). The most expensive item in this stage by an order of magnitude: one Sandbox statement nobody cancelled billed 9.4767 USD, 26.32 RPU-hours, 19% of the D12 ceiling in one sitting, absorbed by Sandbox's free trial (USD 300 for 90 days, 287.90 left on 2026-10-17 and 287.51 on 2026-10-25; `docs/PRICING.md`). Production's window is its own and opened with the namespace on 2026-10-23, closing 2027-01-21: 299.71 of 300.00 left on 2026-10-25 after the warehouse sittings of 2026-10-24 and 25, read by the user in the console (5b decision 9); 299.71 before and 299.69 after the sitting of 2026-10-26, 0.02 for a sitting whose `ComputeSeconds` read 79 RPU-seconds (0.0079): the 60-second minimum per query is what the balance shows and the metric does not. Sandbox read 287.51 before and after the same sitting (the log) | `[E]` |
| Redshift Managed Storage for the governed schema | 0.024 USD/GB-month, billed with the workgroup down | `[P]` |
| Its admin secret + three log groups | ~0.40 USD/secret-month + cents | `[P]` |
| **The managed Redshift cluster AWS Glue creates** if 9.5's Iceberg-engine switch is enabled | **unpriced and unsized** — a *cluster*, always-on in shape, which is the item that could break this stage's cost profile on its own. Priced before the switch is enabled, never after (Lesson 6); decision 5's recommendation is the shape that avoids it | — |

## Decisions due while executing

Each is decided during the stage and written into `docs/log/log-stage-09-deployment-targets.md`
(Lesson 16), with a recommendation stated. Decisions 4, 9 and 10 and step 3.7 were taken on 2026-10-16,
1 to 3, 5 to 8, 11 and 12 by the user on 2026-10-22, 13 on 2026-10-23 and 14 on 2026-10-24, each as
recommended, and 15 on 2026-10-24 against the recommendation.

1. **The Production data CMK, and what of Production's outputs Staging reads** (1.1, 4.6) — **the alias
   is not open**: `docs/GOVERNANCE.md` §Encryption settles it (one data CMK per account), which gives
   `alias/awsds-prod-data`. What remains is **dedicated versus reusing `foundation/`'s key**, and the
   contradiction between 4.6, which grants Staging read on `awsds-prod-outputs` and its key for the model
   archives Stage 10 steps 5.1 and 5.4 move, and Stage 10 decision 6, taken by the user on 2026-10-15,
   under which Staging reads nothing of Production's outputs.
   - **Recommended: a dedicated key, and Staging reads nothing of Production's outputs, model archives
     included.** The argument is the user's: in data science code and artifacts are promoted and data is
     not, and the governed lake is the one source of truth. Each environment writes only to its own
     catalog, buckets and key, and only the promoted pipeline in Production writes to the governed lake,
     through the producer path (step 2). A model crosses environments as a release artifact, through the
     registry or the release bucket, or is retrained in Staging from the governed data Staging reads
     through the share (decision 3), and its archive carries its data's classification. Stage 10
     decision 6 then holds as written, and 1.1's bucket and key policies carry no Staging statement; the
     key still names every principal that decrypts, the approvers none (D31).
   - **The options weighed**: (a) Staging reads `awsds-prod-outputs/models/*/model.tar.gz` as
     `awsds-staging-job-exec` and `awsds-deploy-staging`, `s3:GetObject` with no `s3:ListBucket`, the
     pattern rather than `models/*` because a training job copies `/opt/ml/output/data` beside
     `/opt/ml/model` under its `S3OutputPath` (AWS's guide); written in three policies across two
     accounts (1.1's bucket branch and perimeter exemption, the key's `kms:Decrypt` with `kms:ViaService`
     and the bucket's encryption context, each role's own allow, Lesson 28), and rewording Stage 10
     decision 6 for the archives. (b) The archives in a bucket of their own, `awsds-prod-models`, whose
     ARN the key's Staging statement names as its encryption context. (c) The pipeline copies the
     approved archive into Staging's own bucket, so Staging tests a copy and a Production principal
     writes into Staging.
   - **What the key cannot say**: the `s3-bucket` module turns S3 Bucket Keys on unconditionally, and
     with them the encryption context is the bucket's ARN, not the object's (AWS's S3 guide, read
     2026-10-20). No key condition reaches a prefix, so under option (a) the key admits the two roles to the bucket
     through S3 and the bucket policy alone holds them to the archives. D31's recorded zero-cost variant,
     a key condition on the object's ARN, is unavailable on every bucket the module creates, for the same
     reason. Every module tag, `v0.1.0` to `v0.4.0`, sets `bucket_key_enabled = true` with no variable,
     and Production's three module buckets, `awsds-prod-releases` (`v0.4.0`), `awsds-prod-gitlab-objects`
     and `awsds-prod-gitlab-backup` (`v0.3.0`), read `BucketKeyEnabled: true` on 2026-10-20;
     `awsds-prod-outputs` answered `NoSuchBucket`, since 1.1 creates it in pass 3 (the log).
   - **What it changes**: 4.6 keeps the registry read and loses the archive read; Stage 10 5.4's
     batch transform in Staging runs a model built from a release artifact or retrained there, which
     Stage 10's file says; Stage 8's ask for an archive read on `awsds-deploy-staging` drops.

   **Taken by the user 2026-10-22, as recommended**: a dedicated key, and Staging reads nothing of
   Production's outputs, model archives included (the log).
2. **The scan limit** (1.2) — recommended: **10 GB per query** to start, revised against real queries at
   Stage 12 rather than set high and forgotten. **Taken by the user 2026-10-22, as recommended**: 10 GB per query (the log).
3. **Whether Staging keeps a mirror of the lake** (4.1, 4.4). The plan as written gives Staging local
   databases mirroring the lake's, from one versioned schema source with sampled or synthetic content,
   and keeps Staging off the share (D20, the share revoked at 6b 2.3).
   - **Recommended: no mirror.** Staging reads the governed lake read-only through Lake Formation, by the
     LF-Tag share Sandbox already holds, and writes only to its own catalog, buckets and key. The schemas
     the application produces live in its repository, and each deploy creates them in its own
     environment; a reproducible test pins an Iceberg snapshot or reads by time travel. The controls: no
     write grant outside Production on the governed catalog; the read scoped by the `classification`
     LF-Tag, `restricted` excluded or filtered (Stage 11 decision 12); Stage 11's data events audit every
     read from outside Production. The residual, a governed table readable in the account where unattended
     tests run, is accepted in `threat-model.md` beside Sandbox's.
   - **The alternative**: the mirror as written, both catalogs from one versioned schema source in the
     repository (a module input, not a sync script), since a hand-maintained second copy is Lesson 14 as a
     catalog. Who may open a merge request on that source is not decided anywhere (`docs/GOVERNANCE.md`),
     and the Governance Manager approves classification through it.
   - **What it changes**: D20's sentences that keep Staging off the share and its data sampled or
     synthetic are amended, and 6b 2.3's revocation reverses; `DATA_CONSUMERS` gains Staging; 2.1's grant gains Staging's read, `DESCRIBE` and `SELECT` with
     the grant option, by the expression Sandbox's share uses; 4.1 becomes 1.1-1.3's shape without the
     write: the `consumer-data` call (the account CMK, the LF settings by the two-step, the resource
     links, the read regrants to the job role), `awsds-staging-outputs`, the results bucket and workgroup
     (decision 11), and no `awsds-staging-data`; 4.4's seed is withdrawn; `DT-8`'s isolation check
     inverts into one that Staging's grants read and never write. `staging/sagemaker/`'s role is unchanged
     (it reads through `lakeformation:GetDataAccess` and holds S3 on no lake bucket); its comments change.

   **Taken by the user 2026-10-22, as recommended**: no mirror, the read-only share (the log).
4. **The debug window mechanics** (6.1) — recommended: the **`DateLessThan` trust condition from a
   tfvars value defaulting to the past** — approval is a recorded apply, closure is a revert, and no
   standing machinery exists to rot. **Taken 2026-10-16, as recommended**: the default the user's card of
   that day named (the log).
5. **How a Sandbox project reads a governed Redshift table** (9.5, 9.5a, 9.7, INT-24). The brief narrowed
   the field on 2026-09-20 — the controls do not change, so the mechanism is one Lake Formation governs — and
   **two shapes qualify**: a federated catalog read by Athena, or a Lake Formation-managed **datashare**.
   The cross-account connection is excluded by the requirement. **Recommended: the datashare.** The
   federated catalog's Iceberg-engine switch makes AWS Glue create a **managed Amazon Redshift cluster** —
   unpriced, always-on in shape, encrypted by an AWS managed key by default, and a direct collision with
   `DenyRedshiftProvisionedClusters` — while the datashare path needs no such switch. **Take the reading
   first** (9.5a): the recommendation rests on a documentation sentence, and whether that cluster is created
   in this account at all is what decides it. **Taken by the user 2026-10-22, as recommended**: the Lake Formation-managed
   datashare, after 9.5a's reading (the log).
6. **What a governed database is in D28's terms, and who creates its tables** (9.3, 9.4) — recommended: the
   **DDL and the load job in the repository**, carried as ordinary application code (a load job Glue runs
   is D28's class 2c, its script under the release's prefix by Stage 10 decision 12), the pipeline the only
   runner of the DDL, and the deployer's database user the only creator, with `ALTER DEFAULT PRIVILEGES FOR
   USER` granting the job role's rights through a role. A schema outside the repository leaves Staging's
   deploy with nothing to create it from (decision 3). The alternative, DDL run as the job role,
   keeps one creator and gives up the separation. **Taken by the user 2026-10-22, as recommended**: the DDL and the load job in
   the repository, the deployer's database user the only creator (the log).
7. **The governed warehouse's cost guards** (9.1) — the usage limit's amount and `auto_mv`. Recommended:
   **Sandbox's 10 RPU-hours** (the user's figure after the runaway), knowing the counter restarts with each
   workgroup, and **`auto_mv` off**: a governed schema written by one load job gains nothing from views the
   service decides to build and refresh on a 1.44 USD/hour meter. **Taken by the user 2026-10-22, as recommended**: 10 RPU-hours and
   `auto_mv` off (the log).
8. **The governed warehouse's audit logs** (9.1) — retention and encryption. `useractivitylog` carries SQL
   text, so in Production it carries governed values. Recommended: **the Sandbox retention of 30 days and
   the account data CMK** on all three groups, with the CloudWatch Logs statement 1.1 lists, since a log of
   governed values is a store of them. **Taken by the user 2026-10-22, as recommended**: 30 days and the account data CMK (the
   log).
9. **Where the job settings are enforced** (3.5) — recommended: **(a), the `Workloads` OU SCP**, composed
   from `sagemaker-denies`. The alternative is the module as the boundary of every submitting role.
   **Taken 2026-10-16, as recommended**: the default the user's card of that day named (the log).
10. **Who reads model status from Sandbox** (3.2) — the persona from a laptop, the project role from a
    space, or both. Recommended: **both, by `aws:PrincipalArn`**: the person reads status where they work,
    and a notebook comparing its model with the approved one is the project role. Each half also needs an
    allow on its own side: the persona's in `identity/sso/`, the project role's as a policy attached the way
    `sandbox/bedrock/` and `sandbox/workflows/` attach theirs. The project role already reaches this account
    for the house image (INT-01). **Taken 2026-10-16, as recommended**: the default the user's card of
    that day named (the log). Both own-side allows exist already: the persona's `ReadSageMakerStatus` and
    the project role's `SageMakerCrossAccountPermissions` in AWS's managed policy, so 3.4 measures them.
11. **Where each deployment target's query results land** ([D19](../decisions/D19-derived-zone.md)'s
    re-decision, 1.2, 4.2). `consumer-data-v0.6.0` supplies neither the bucket nor the workgroup, and in a
    deployment target no service supplies them either, so ours is the only destination. Recommended: **each
    account's data slice authors both** — `awsds-prod-derived` with `results/` at a 30-day expiry and
    `awsds-prod-athena` in Production; `awsds-staging-derived` and `awsds-staging-athena` in Staging — which
    keeps every name `./aws/deploytargets.py`, `identity/sso/README.md` and Stage 11 already read.
    **Taken by the user 2026-10-22, as recommended** (the log).
12. **The Glue job's network, and who owns the job security group** (2.4, 2.5, 4.3, 9.1; Stage 8's
    application slice, Stage 10 decision 6's render). A Glue job runs in Glue's own network unless it
    names a network connection; a SageMaker job carries a `VpcConfig` because `DenySageMakerJobsOffVpc`
    demands one, so its subnets and security group are set either way. The shapes:
    - **(a)** a Glue network connection in each target's private tier and one job security group per
      account, both `[P]` in `*/sagemaker/` beside the job role, read by the application slice and by
      Stage 10's render;
    - **(b)** the same two objects in the application slice, `[E]`, re-created at each deploy;
    - **(c)** no connection: the Glue job runs in Glue's network, and only the SageMaker job's group exists.

    The readings of 2026-10-22: the pickup's direct `GetObject` and `DeleteObject` reach the drop-box only
    through `VPC-Workloads`' gateway endpoint, which only a job inside the VPC presents (1.4,
    `DenyOutsideTrustedNetworks`), so (c) refuses 2.5; the producer's vended reads and writes are admitted
    from any network, the vended session being the registration role's in Data Governance; and 9.1 admits
    `5439` from the job's security group, group to group, a reference an `[E]` group breaks at every
    teardown, so (b) fails step 9. Under (a), `lakeformation` joins both egress slices before the first
    job (3.3a, 4.3a), Glue's workers reach each other through a self-referencing rule, and
    `job_security_group_id` and `glue_connection_name` join `*/sagemaker/`'s outputs. Whether a job's
    metrics need `monitoring` stays 2.4's reading. **Recommended: (a).** **Taken by the user 2026-10-22, as recommended**: (a) (the log).
    The application slice references the connection and the group from `*/sagemaker/`'s outputs rather
    than declaring them (Stage 10 decision 20 (b)). Written the same day: `awsds-<env>-jobs` and its
    rules and connection in both `sagemaker/` slices (`network.tf`), and `lakeformation` in both egress
    slices.
13. **Whether, and where, `AllowFullTableExternalDataAccess` is turned on for the governed write** (2.4,
    2.5; opened 2026-10-23). AWS's page on full-table access for Glue names it as the mode's first step,
    *"allow third-party query engines to access data without the IAM session tag validation"*, and the
    only mode a Glue Spark job writes a registered table in; on 2026-10-23 the flag reads unset in
    Production (`consumer-data`'s resource declares it nowhere and ignores it) and in the lake
    (`data-governance/data/lakeformation.tf`, this repository's own resource). Which account's setting
    the credential vending reads for a cross-account table, the engine's or the owner's, no page says.
    - **Recommended: (a) Production's flag, by the user's hand in the Lake Formation console**
      (*Administration → Application integration settings → Allow external engines to access data in
      Amazon S3 locations with full table access*), the console's `PutDataLakeSettings` built from the
      structure it read, bracketed by `./aws/deploytargets.py` `DT-5` before and after (the parameters
      and the default lists unchanged); Terraform keeps it through `ignore_changes`. If the first run's
      wording still names the mode, the lake's resource gains `allow_full_table_external_data_access =
      true`, planned and applied as `awsds-infra-data` under `DL-5`'s bracket. SMUS set the same flag
      in Sandbox (2026-08-22) and in Staging (Stage 18, 2026-10-19).
    - **What it costs**: with the flag on, a principal holding full-table Lake Formation permissions in
      that account vends S3 credentials for the whole table directly (`GetTemporaryGlueTableCredentials`),
      outside an integrated engine; in Production `DataScientistProdAccess` holds `GetDataAccess` and
      `SELECT` through the module's re-grants, so the persona could read a governed table's objects
      without `awsds-prod-athena`, its scan limit or its results location. Stage 11 gains the row when
      the flag is taken, beside the Sandbox and Staging readings 6f and Stage 18 left unexercised.
    - **The alternatives**: (b) `consumer-data` taking the flag as an input in a new release, every
      caller re-planned, Sandbox's live `true` and Staging's `false` each declared, a `DataLakeSettings`
      apply in every consumer account; (c) no flag, the governed write made through Athena as the job role, an
      integrated engine, which is a producer of another shape than decision 12's Glue job and leaves
      2.5's pickup, which reads the drop-box as the role, to a second job.

    **Taken by the user 2026-10-23, as recommended: (a)** (the log). The act is the user's, in
    Production's Lake Formation console as the infrastructure user, bracketed by `./aws/deploytargets.py`
    `DT-5` before and after; it needs nothing up, so it runs before the Production sitting. The lake's
    half waits for the first run's wording. **Done 2026-10-23** (the log): the before-reading at 19:29
    UTC, one administrator, both lists empty, `CROSS_ACCOUNT_VERSION=4`, `SET_CONTEXT=TRUE`, the flag
    unset; the console refused the settings page first in `us-east-2`, `CT.MULTISERVICE.PV.1`'s guardrail
    naming itself, and answered in `us-west-2`; the after-reading at 19:49 UTC, the flag `true` and the
    rest as before, `DT-5` passing. `TM-26` carries the residual, `AWS_STATE.md` §C the flag per account. **The lake's half, 2026-10-23** (the log): the first run, with Production's flag alone, was refused at the vend *"Insufficient Lake Formation permissions. Verify the data lake settings for account"*, so `lakeformation.tf` gained `allow_full_table_external_data_access = true`, planned *1 to change* and applied at 22:03 UTC as `awsds-infra-data` under `DL-5`'s bracket (`4` / `TRUE` before and after, the administrator and the empty lists unchanged, the re-plan `No changes`); the second run committed at 22:06. The flag reads `true` in Production, Sandbox and Data Governance and unset in Staging; `TM-26` carries the lake's residual too. **The third run, 2026-10-24** (the log): with Production's flag off and the lake's on, the write committed at 22:26 UTC, so the engine's flag is not needed and Staging's stays unset; Production's was turned on again at 22:29 UTC, as (a) left it. **Turned off for good 2026-10-25** (the log): the user's hand in the console, bracketed by `DT-5` at 17:38:59 and 17:45:00 UTC, the key absent from the settings after and the rest unchanged; the flag reads `true` in Sandbox and Data Governance, unset in Production and Staging, and `TM-26`'s Production half is closed.
14. **The account that registers the datashare, and so grants it** (9.5, 9.7, INT-24), opened 2026-10-24
    from AWS's step pages for shape (ii). Two rules decide it: an LF-Tag created in one account cannot be
    put on a resource shared from another, and an account that receives a Lake Formation share cannot
    pass it on. AWS's own pattern puts a central governance account, which registers and grants, between
    the producer and the consumer.
    - **Recommended: (a) Data Governance.** Production grants the share `VIA DATA CATALOG` to the lake's
      account and authorizes `DataCatalog/<Data Governance>`; the lake's administrator associates it,
      registers it, creates the federated database, tags it with the lake's own `layer`,
      `businessunit` and `classification`, and grants Sandbox; Sandbox's administrator grants the
      project's role. One ontology and one grantor for every governed read, which is what
      `objectives.md`'s "the governance model does not fork" asks.
    - **The alternatives**: (b) Production registers its own share and grants Sandbox, with LF-Tags of
      its own (a second ontology) or named grants only, the producer governing its own rows; (c) Sandbox
      registers it, whose Lake Formation administrators include the SMUS roles (open question 24), the
      least-governed account granting governed rows.
    - **What (a) changes**: the grant register's second grantor is Data Governance on a federated
      database, not Production on `governed` (9.8, D40's compensation sentence); the registration is
      permanent, since `DenyLakeDeletionAndDeregistration` refuses `lakeformation:DeregisterResource` in
      the `Data` OU, so its removal is an SCP amendment, like the lake's own locations. The lake
      administrator's calls (`redshift:AssociateDataShareConsumer`, `redshift:DescribeDataShares`,
      `glue:PassConnection` on `aws:redshift`) are inside `InfrastructureAccess`, and no organization
      policy denies them in the `Data` OU (read 2026-10-24), so no grant is written.

    **Taken by the user 2026-10-24, as recommended: (a) Data Governance** (the log).
15. **Who starts the warehouse load** (9.4), opened 2026-10-24. Staging has no warehouse, so whatever
    starts the load runs in Production alone and nothing rehearses it.
    - **Recommended: (a) a manual job of the Production leg** after `production-deploy`: the DDL, then
      the load's Glue job, then the count, with the compute raised before and taken down after; no
      scheduled run meets a workgroup that is down, which is its state every night.
    - **The alternatives**: (b) a workflow of Production's own with its own chain, under the scheduler,
      failing whenever the compute is down; (c) app-etl's Glue job writing the warehouse too when an
      argument names the table, which only Production's render passes.

    **Taken by the user 2026-10-24: (b)** (the log). The DDL stays the pipeline's manual job (decision
    6); the load is `app-etl-warehouse`'s one task, its chain at `cron(30 7 * * ? *)`, and a run with the
    compute down fails at `GetWorkgroup`, heard by the chain's failure rule.

## Verifications to answer while executing

Record every answer, including the ones that come out fine.

| # | Question | Step |
|---|---|---|
| i | Do the parameter readings bracket every LF-settings apply unchanged — Data Governance (again), Production, Staging (`DT-5`, `DL-5`'s discipline)? **Yes, read 2026-10-22 to 2026-10-24** (the log): `DL-5` read `CROSS_ACCOUNT_VERSION=4` and `SET_CONTEXT=TRUE` before (19:35:09Z) and after (19:39:12Z) pass 2's lake apply; Production's and Staging's settings applies, Recipe D's first step (19:51 and 19:57Z), each read back the `InfrastructureAccess` seat alone, both default lists `[]` and the parameters as the slice writes them (Staging's version moved 1 to 4, the apply's own change), `DT-5` passing after each; decision 13's flag changes, Production's console on 2026-10-23 at 19:49, the lake's apply at 22:03, Production off at 22:23 and on again at 22:29 on 2026-10-24, each bracketed by `DT-5` with the administrator, the lists and the parameters unchanged | 1.5, 2.2, 4.5 |
| ii | Does the write share arrive with a **fresh** session and no pending RAM invitation — INT-11's org path holding for the third consumer? **Answered on the RAM side at 2.2 and on the catalog side at 2.3**, because Production has no data lake administrator in between (2.2's callout) | 2.2, 2.3 |
| iii | Does the write pair hold — the LF write succeeds **and** the direct `PutObject` is denied on the identity side (D13)? **Yes, 2026-10-23 and 2026-10-24** (2.4, the log): the producer run's insert committed through the share (22:06:11 UTC, then 22:26:46 the next day) and the same run's direct put was refused by the lake's data key, one layer before the S3 wording the step expected, *"not authorized to perform: kms:GenerateDataKey on this resource because the resource does not exist in this Region, no resource-based policies allow access, or a resource-based policy explicitly denies access"*; the role's missing `s3:PutObject` stays attached and unexercised (Lesson 20) | 2.4 |
| iv | Does the pickup read, curate and delete — and does the drop-box KMS grant reach the exact 3.1 role name (the Stage 5a contract)? **Yes, run 2026-10-23 at 22:09 UTC** (2.5 and the log): `SUCCEEDED` in 97 s, one CSV listed and its ten rows read as `awsds-prod-job-exec` under the lake key, the drop-box grant reaching the 3.1 role name. | 2.5 |
| v | Is the registry gate real — the Sandbox reader decision 10 named reads status only, and an approval lands only under `awsds-deploy-prod` (INT-07)? **The persona's half, 2026-10-23**: from a laptop as `DataScientistAccess`, `DescribeModelPackageGroup` answered across the account boundary and `CreateModelPackage` was refused *"because no resource-based policy allows"*; the project role's half and the approval half were owed. **The approval half yes, 2026-10-25** (the log): `production-register` and `production-approve` wrote version 1 of `awsds-prod-model-app-etl`, CloudTrail's `CreateModelPackage` and `UpdateModelPackage` both by `awsds-deploy-prod`; the project role's half waits for a space. | 3.4 |
| vi | Does the enforced workgroup override a client-requested result location, and does the scan limit cancel (the documented behaviour, observed)? **The override, yes, 2026-10-23**: a query asking for `s3://awsds-prod-outputs/not-enforced/` landed its result under `s3://awsds-prod-derived/results/`, `SUCCEEDED`, the workgroup reading enforced with a 10,737,418,240-byte cutoff; the cancel waits for a table past 10 GB, which no table here is | 5.4 |
| vii | Are the Production negatives denied naming the **set's** deny — `CreateTrainingJob`, `StartJobRun`, `redshift-data:ExecuteStatement` (D18)? **Three of three, 2026-10-23 and 2026-10-26**: `CreateModelPackageGroup`, in place of `CreateTrainingJob`, which the `Workloads` document's job settings would answer first, and `StartJobRun` each refused *"with an explicit deny in an identity-based policy"*, the set's `DenyProductionControlPlane`; `ExecuteStatement` validated before it authorized with no workgroup in Production (Lesson 21) and, with the workgroup up on 2026-10-26, was refused *"with an explicit deny in an identity-based policy"* on the workgroup's ARN, `DenyMintingARedshiftDatabaseSession` being the set's one statement on the action | 5.4 |
| viii | Does `DataScientistStagingAccess` read back with `DenyEveryWrite` and no Athena, and is its assignment the one 6b made (Lesson 22)? **Answered 2026-10-18, yes to both**: `DT-10` reads `DenyEveryWrite` and no Athena allow; `./aws/list-identities.py` (22:20:57Z) reads the set assigned in `Staging Account` to `sso-group-data-scientists` alone, among the seven assignments 6b's last reading counted, and the Identity account's CloudTrail since 2026-08-20 holds one `CreateAccountAssignment` for the set, at 2026-09-06T04:35:35Z, ten seconds after 6b step 2.1 deleted `DataScientistAccess` and `DevEnvStewardAccess` there, and no delete since | 5.2 |
| ix | Does INT-05 hold from both directions — the `VPC-Workloads` branch for workloads and the principal branch for the persona from any network, with every other principal refused off the endpoint, `VPC-SharedServices` included? **The principal branch, 2026-10-23**: the persona listed `app-etl/outbox/` from a laptop with no tunnel and was refused the bucket's root and a release's tree by the bucket's own denies (8.3); the `VPC-Workloads` branch is 2.4's job, and the refusal of another principal off the endpoint waits for one | 1.4, 8.3 |
| x | What fraction of the S3 console works for the persona under 1.1's principal branch (INT-06, open question 8) — and is `README.md` told? **Answered 2026-10-23**: one page, the object listing under a named prefix reached by URL; the bucket list, the root and every bucket-level tab refuse; `README.md` told, the question closed | 8.2 |
| xi | Is the escape hatch closed at rest, open only in the window, alarmed on every successful assumption — and does a `CreateSpace` under it die on the OU policy? **Three of four answered 2026-10-22**: closed at rest (`DT-9`, the default in the past), open in the window (three assumptions, 23:21 to 23:32 UTC), alarmed on each (the rule's `TriggeredRules` and the topic's messages one per assumption, the e-mails received); the `CreateSpace` died on the role's own identity policy, *"no identity-based policy allows"*, one layer before the OU document, which the battery's infrastructure user is the principal to exercise (Lesson 20). The refusal against the closed trust answered 2026-10-23, *"not authorized to perform: sts:AssumeRole"* on the real ARN, its trail record `AccessDenied` with `requestParameters` null at 15:25:28 UTC | 6.3 |
| xii | Does the Staging role read an approved model version (INT-07's registry half)? **The identity half yes, read 2026-10-25 by the simulator** (the log): `awsds-deploy-staging`'s `DescribeModelPackage` and `ListModelPackages` read `allowed` by its `apply-application`, `UpdateModelPackage` `implicitDeny`; the group policy's `ReadTheVersionsAsTheStagingDeployRole` names that role, which the simulator cannot evaluate as a resource-policy principal, and no call from a Staging deploy session exists yet: the proof is a pipeline job's. | 4.6 |
| xiii | Does the end-to-end promotion pass against the real catalogs — and does a schema drift planted in the application's schema source fail the integration tests, not the deploy? **Yes, 2026-10-25** (Stage 8's log): `v0.4.2` passed every leg against the real catalogs (pipeline #80), and `v0.4.5`'s drift failed `staging-test` at the Glue job, *"lake.curated.trades lacks book"*, with Production untouched (Stage 8 verification ix). | 8.5 |
| xiv | In **each** of the two accounts this stage gives a `DataLakeSettings` (Production, then Staging): do `CreateDatabaseDefaultPermissions` and `CreateTableDefaultPermissions` read `[]` **before** the slice's first catalog object exists, and does no database in that account carry an `IAMAllowedPrincipals` grant afterwards? — the reading the two-step exists to produce, and the only moment it can be taken. **Answered 2026-10-22, yes in both**: Recipe D's first step read both lists `[]` in Production (19:52Z; `DT-5` had read one `IAMAllowedPrincipals` entry in each at 19:45Z) and in Staging (19:57Z, empty since Stage 18's pass 8 put them back), and after the rest no grant in either account names `IAM_ALLOWED_PRINCIPALS` (21 grants in Production, 22 in Staging) | 1.3, 1.5, 4.1 |
| xv | Does a `Create*Job` without the five settings fail when submitted by a role other than the job's own (a deploy role, a workflow execution role), naming the policy decision 9 chose — and does `DT-11` read the enforcement back? **Answered 2026-10-18 for the infrastructure user**: each `Create*Job` row read `DENY-SCP` naming the `Workloads` document, and `DT-11` passes. A deploy role and a workflow execution role are unread until a pipeline submits a job; the simulator cannot separate the five statements for either (read 2026-10-25, Stage 10 xviii: every variant `explicitDeny` by the organization against a job ARN, the infrastructure user's role alike) | 3.5, 3.6 |
| xvi | Which shape did serverless inference take (3.7) — a named exception, the SCP deny, or a refusal 3.5's `CreateModel` deny already produces — and is the choice written into `AWS_STATE.md` either way? **Answered 2026-10-18**: the SCP deny, applied and probed (`DENY-SCP` after, `ALLOWED` before), and `AWS_STATE.md` section C records it | 3.7 |
| xvii | Does a Staging or Production job reach `sagemaker.runtime` from a subnet in the AZ its single-AZ endpoint is not in — the vendor's affinity sentence, measured? **No subject since 4.3a** (2026-10-22): `sagemaker.runtime` is in neither VPC's set and no planned job calls it; the question returns with the first job that invokes an endpoint | 4.3a |
| xviii | Does the governed namespace read back at `base_capacity = 4` with its usage limit, `max_capacity = 8`, `price_performance_target` disabled, the `DataStorage` alarm and **no project tag** — and do its three log groups carry a retention period, so `EXC-10` stays at one? **All, read 2026-10-25 and 2026-10-26** (the log): the workgroup `AVAILABLE` at 01:40:41 at base 4 and max 8 RPU with its usage limit; at 07:15 `./aws/warehouse.py` read no project tag (`WH-7`), both alarms, capacity and storage, `OK` (`WH-4b`), and the three audit groups at 30 days (`WH-4`), so `EXC-10` stays at one; `price_performance_target` read `DISABLED` on the next workgroup, 2026-10-26 at 00:46 UTC, three minutes after its creation (`WH-2` passing) | 9.1 |
| xix | Does the Lake Formation object 9.5 created (a federated catalog or a federated database) carry `IAMAllowedPrincipals` after creation — the Recipe D reading, third instance — and did the two-step prevent it? **No, read 2026-10-25** (the log): `governed_trades`, created at 01:53:16, holds its creator's `ALL` alone and no grant to `IAM_ALLOWED_PRINCIPALS`, its `CreateTableDefaultPermissions` `[]`; Data Governance's default lists have been empty since Stage 5a, so no two-step was needed. | 9.5 |
| xx | Does the governed pair hold: a governed schema write under the job role succeeds, and its direct `PutObject` to a lake bucket is still denied? **The write half yes, 2026-10-25** (the log): the load job `jr_453d7bb9…2870` inserted 30 rows into `trades.trades_notional` as `IAMR:awsds-prod-job-exec`; the direct `PutObject` half is 2.4's refusal, the role unchanged since (9.6): the lake's data key refused it, one layer before the S3 wording. | 9.6 |
| xxi | Which of the two Lake-Formation-governed mechanisms carries INT-24, and does a Lake Formation share of a **federated** resource preserve the TBAC expressions this estate grants by — given that both AWS pages say tags may be used, where DataZone's Glue path refuses them? **Shape (ii), and yes: read 2026-10-25** (9.7, the log): the lake's tag grant reached the federated database in Sandbox, and a project read the governed table through it with no network path; INT-24 holds. | 9.5a, 9.7 |
| xxii | Does the promotion pipeline's second run survive an existing schema — the idempotence a `GRANT` outside every plan forces? **Yes, read 2026-10-25** (the log): `production-warehouse-ddl`'s retry ran `CREATE TABLE IF NOT EXISTS` over the table its first run had created and read back `IAMR:awsds-deploy-prod` and 30 | 9.4 |
| xxiii | Does enabling the Iceberg-engine switch create a **managed Redshift cluster in this account** — under which principal, visible as which CloudTrail call, at what size and under which key — and does `DenyRedshiftProvisionedClusters` refuse it (its `CreateCluster` half's first exercise)? **No subject since decision 5**: shape (ii) was taken, so the Iceberg-engine switch was never enabled and no managed cluster exists to look for. | 9.5, 9.5a |
| xxiv | On the datashare path, does a producer-side revoke leave Lake Formation permissions behind, as documented — and does the register notice? | 9.7 |
| xxv | Which database users do the job role's and the deploy role's sessions land on, read from `pg_user` after the first connection, and does the job role write a row into a table the deployer's user created? **Yes, read 2026-10-25** (the log): the job role's session lands on `IAMR:awsds-prod-job-exec` and the deploy role's on `IAMR:awsds-deploy-prod`, neither a superuser, and the job role wrote 30 rows into `trades.trades_notional`, owned by the deployer's user | 9.3, 9.4 |
| xxvi | Do the Production audit groups hold a user connection and a user statement, logged while the workgroup was up — the presence `EXC-16`'s export makes necessary before the groups are called an audit trail? **Yes, read 2026-10-24 at 00:35** (the log): `connectionlog` holds the admin's Data API session, `useractivitylog` its `CREATE SCHEMA trades …` statement and `userlog` three `create` events. | 9.8 |
| xxvii | Does the Data API job cancel its statement on a timeout, and does `DescribeStatement` read the cancellation? **The read half, 2026-10-25** (the log): the job follows its statement with `DescribeStatement` once the deploy role holds it on its own statements (`FollowItsOwnStatements`); no statement has run past the 300 s bound, so the cancel is unexercised | 9.4 |
| xxviii | Does Lake Formation's full-table-access mode admit the job role's write holding `INSERT`, `DELETE` and `ALTER` without `ALL`, which AWS's page says a write requires; is `AllowFullTableExternalDataAccess` needed in the engine's account, the lake's, or both (decision 13); does the commit need `glue:UpdateTable` on the lake's table (3.1's `CommitTheIcebergWrites`); and does the run's `GetTemporaryGlue*Credentials` carry `vpcEndpointId` (Stage 10 0.5)? **Answered 2026-10-23 and 2026-10-24 but one clause**: the mode admits the writer holding `INSERT`, `DELETE` and `ALTER` without `ALL` (the second run's commit at 22:06 UTC); the owner's flag is required (the first run, with the engine's alone, was refused naming the data lake settings) and the engine's is not (the third run, with Production's flag off, committed on 2026-10-24 at 22:26 UTC); the commit went through with `glue:UpdateTable` on the role, a run without it unmeasured; the vend is logged as `GetDataAccess` and carries `vpcEndpointId`, the `lakeformation` endpoint's | 2.4, decision 13 |

## Risks

- **An instance preference list is held to the instance ceiling** (3.5): `InstancePreferences` names
  up to five types in place of `InstanceType`, and the battery's seven rows read each list as expected on
  2026-10-22 (Stage 18 8.7). The quotas do not keep jobs out of `Workloads`: the
  `ml.t3.medium` processing quota is 4 in Staging and in Production (AWS's default, Production's read
  2026-10-20), and `app-etl-20261019T205205` ran on it in Staging on 2026-10-19 (Stage 18 4.4).
  SageMaker checks the quota of every listed type, so a list naming `ml.m5.2xlarge`, at 0 for processing
  in both accounts and for training in Production, is refused either way; the quotas of the other
  off-ceiling types are unread. Staging's training quotas read 0 like Production's, and no type inside
  the ceiling has a transform quota above 0 in either account, `ml.t3.*` and `ml.c5.large` having none
  (read 2026-10-22; `ml.m5.large`'s training and transform requested at 2 in both on 2026-10-23); the
  applied quotas read above zero in both since 2026-10-24 (3.5), and Stage 10 5.4's batch transforms ran
  on `ml.m5.large` in both on 2026-10-25.
- **The silent LF-settings reset now has three instances, not one** — every account with a
  `DataLakeSettings` resource can zero its own `Parameters` on any apply. `DT-5` extends `DL-5`'s
  reading to all three; run it after every apply, not at stage end. **And that resource carries a
  second, unrelated hazard on the same apply** (measured 2026-08-18, Stage 5a pass 1): the two
  `Create*DefaultPermissions` act at **creation time** and cannot be expressed empty in a plan, so a
  catalog object created in the same apply as the settings can be born deferring to IAM — permanently,
  and invisibly afterwards. One hazard is *overwritten later*, the other *not applied early enough*, and
  both are answered by the same two-step (1.3's callout, Recipe D).
- **"The share did not arrive" and "the account cannot see it yet" look identical from the consumer
  side** — and this stage reads the consumer side twice (2.2, 2.3) across the pass where the difference
  exists. Read RAM first, catalog second, and never treat an empty catalog before 1.3 as evidence about the
  grant.
- **The lake trusts a VPC by its gateway endpoint, and Production has three.** A trusted-network entry read
  from `production/foundation/` admits the build plane and refuses the jobs, and the bucket's deny names
  neither (1.4).
- **The write share is INT-03's least-travelled variant** — an LF-aware cross-account Iceberg write can
  fail in engine-specific ways the read shares never exercised. The fallback is INT-03's row; the proof
  is 2.4, before anything depends on it.
- **A job's settings bind whoever submits it.** Written as a boundary on the job's own role they bind
  nothing, and the failure is silent: the job runs, off the VPC, with a network (3.5).
- **Two contracts are spelled, not enforced**: `awsds-prod-job-exec` (Stage 5a's statements name it) and
  the read share's expression for Staging (2.1). A typo fails closed later, with an error naming a policy rather
  than the typo (Lesson 14); `deploytargets.py` reads both sides.
- **Staging reads governed data** (decision 3): a governed table is readable in the account where
  unattended tests and the data scientists' Staging reads run, the residual `threat-model.md` accepts
  beside Sandbox's. The read is scoped by `classification`, `restricted` excluded or filtered (Stage 11
  decision 12), no grant outside Production writes, and Stage 11's data events audit every read from
  outside Production.
- **Query results are visible within the persona** — one enforced result location means any
  `DataScientistProdAccess` holder can read another's query output. Stated limit at lab scale (D31
  keeps it from the approvers and Staging); per-user isolation would need per-user workgroups, which
  the identity seam forbids as a resource-per-person.
- **The escape hatch is authored by the identity it cannot constrain** (Lesson 18) — the controls above
  it are detective: the alarm on every successful assumption, and a trail its user cannot edit.
- **Step 9 makes this stage's bill unbounded for the first time.** A Redshift Serverless workgroup is
  metered **per hour of query time on a shared meter**, and the ways an idle one bills anyway — an open
  transaction, a connection pool's keep-alive, a cancelled query, and a Data API statement whose client
  stopped polling, which ran 6 h 33 min in Sandbox — apply to a pipeline more readily than to a person,
  since a pipeline's connection is watched by nobody. The usage limit with `breach_action = deactivate` and
  `make down` are the guards; `max_query_execution_time` is not one until its Sandbox failure is explained,
  and the pipeline cannot run `make down` on the compute at all (9.4).
- **`IAMAllowedPrincipals` gets a third place to appear.** The `Create*DefaultPermissions` hazard was a
  `DataLakeSettings` property in Stage 5a and in 1.3/4.1 here; the Lake Formation object 9.5 creates
  carries it too, and one born deferring to IAM is a **governed warehouse governed by nothing** — the same
  failure, one storey up, in the resource least likely to be read for it (9.5).
- **A Redshift "database" is a Glue "catalog" and a Redshift "schema" is a Glue "database".** The federated
  mapping inverts two levels, and a grant written from intuition lands one level off — where it will
  frequently *work* on the easy case and be wrong on the one that matters (Lesson 53).
- **The register holds Production's Redshift `GRANT`s beside the lake's Lake Formation grants**, and Redshift grants have no `list-permissions`: they
  are read from `SVV_*` inside a database session, which means the instrument needs a credential the other
  instruments do not. `WH-12` reports the grants and always passes; `WH-14` is the check that fails, on a
  table no role can read.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
