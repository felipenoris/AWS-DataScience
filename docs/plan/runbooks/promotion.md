# The first promotion — the sittings that close Stages 8, 9 and 10, in order

The owed steps of [Stage 8](../stages/stage-08-cicd-pipelines.md) (pass 4), [Stage 9](../stages/stage-09-deployment-targets.md)
(passes 3, 4 and 6, 8.5) and [Stage 10](../stages/stage-10-orchestration-promotion.md) (passes 1 to 4)
share one chain: each needs something another raised, and every one of them is written. This runbook
puts them in the order they can run, one section per sitting, with the command each step is and the
reading each step leaves. [`waiting-on-the-user.md`](../waiting-on-the-user.md)'s "Sittings with the
environment up" says what each sitting closes; the stage files hold each step's reasoning and its
record. What a step reads is recorded in that stage's log, in the sitting it ran.

Written 2026-10-23 with the environment down. Every `[Claude⚡]` apply waits for the user's word in
chat, with the identity stated first (`CLAUDE.md`); every `[user]` act is theirs.

**Where it stands, 2026-10-24**: §0 and §P done but the items §0.5 lists; §W's steps 1 to 4 done (the
namespace, 9.3's schema); left, in order: §0.5's item 4 (the two decisions; items 1 to 3 done), §H (the hub and GitLab), §T (the tag), §W
step 5 (the datashare, after Stage 9 decision 14), §Q (after the quotas, which read `CASE_OPENED`).

| § | Holds |
|---|---|
| [§0](#0-before-any-sitting-with-the-environment-down) | what runs today, with nothing up: the persona proofs, the quota requests, the flag of decision 13, the deploy roles' grant (§0.5) |
| [§H](#h-the-hub-and-gitlab) | the hub and GitLab: the user's GitLab acts, the legs' merge request, the next house image |
| [§P](#p-production-stage-9s-pass-3-and-stage-10s-05) | Production: the proof job's two runs, Stage 9's producer pair and pickup |
| [§T](#t-the-tag-stage-8s-pass-4-with-stage-10s-passes-1-and-2) | the tag: Stage 8's pass 4 with Stage 10's passes 1 and 2, and Stage 9's 8.5 |
| [§W](#w-the-governed-warehouse-stage-9s-pass-6) | the governed warehouse, Stage 9's pass 6, separable and last |
| [§Q](#q-after-the-quotas-stage-10s-pass-3) | after the quotas: Stage 10's pass 3 |
| [§R](#r-the-readings-at-the-end-of-every-sitting) | the readings at the end of every sitting |

## 0. Before any sitting, with the environment down

Nothing below needs the hub: a person reaches AWS by identity (D39), and every object these steps read
is `[P]`.

### 0.1 The persona proofs the user can run now

Each signs in as one persona (`aws/AWS-CLI.md`, "Signing in"; `aws sso login --sso-session <session>
--no-browser`, the URL answered in a private window) and reads every refusal by its wording. The
commands and the expected wording are in the steps:

| Proof | Persona, profile | Step |
|---|---|---|
| the workgroup boundary and the Production negatives | Data Scientist User, `awsds-scientist-prod` | Stage 9 [5.4](../stages/stage-09-deployment-targets.md) |
| the registry gate's Sandbox half, from a laptop | Data Scientist User, `awsds-scientist-sandbox` | Stage 9 3.4 |
| the Sandbox session's reach: the perimeter, the drop-box pair, the registry | Data Scientist User, `awsds-scientist-sandbox` | Stage 9 8.1 |
| the S3 console under the principal branch | Data Scientist User, the console | Stage 9 8.2 |
| the laptop off the VPN: the named prefixes and nothing else | Data Scientist User, `awsds-scientist-prod` | Stage 9 8.3 |
| Staging: everything readable, nothing writable | Data Scientist User, a profile for `DataScientistStagingAccess` (8.4 gives the block) | Stage 9 8.4 |
| the orchestration negatives from Production | Data Scientist User, `awsds-scientist-prod` | Stage 10 [6.2](../stages/stage-10-orchestration-promotion.md) |

A proof that touches a Sandbox space (8.1's project-role half, 3.4's) waits for the Sandbox sitting.
**Run 2026-10-23**, every row but the space halves, the readings in Stage 9's and Stage 10's logs: the
override and the control-plane negatives, the registry gate's persona half, the drop and its read-back,
Staging's three layers, the console's one working page; 5.4's Data API negative waits for a workgroup
(pass 6), and 6.2's provisioned deny is the battery's to exercise, a persona's implicit deny answering
first.

### 0.2 The quota requests

Every type inside the ceiling reads 0 for training and transform in Staging and Production, with no
request ever made in either account (read 2026-10-23: `list-requested-service-quota-change-history`
empty in both). Stage 10's pass 3 waits on them; the commands, with each quota's code, are in Stage 9
[3.5](../stages/stage-09-deployment-targets.md). The user runs them; a request takes hours to days.
**Requested 2026-10-23**: `ml.m5.large` training and transform at 2 in both accounts, `PENDING`; §Q opens
when both accounts read them above zero. **Read 2026-10-24**: the four `CASE_OPENED`, each with a support
case id, the answer a person's at AWS.

### 0.3 The one act the Production sitting needs first

Stage 9 decision 13, taken 2026-10-23 as (a): `AllowFullTableExternalDataAccess` turned on in Production's
Lake Formation settings before the proof job runs, by the user's hand in the console. AWS's page on
full-table access names it as the first step of the only mode a Glue Spark job writes a registered
table in, and both Production and the lake read it unset on 2026-10-23; the reasoning and the cost in
the threat model are in the stage file. The act needs nothing up:

1. **[Claude]** the before-reading, `./aws/deploytargets.py awsds-infra-prod` (`DT-5`) and
   `aws lakeformation get-data-lake-settings --profile awsds-infra-prod`, the admins, the two default
   lists, the parameters and the flag, kept for the after-reading.
2. **[user]** signed in to the console as the infrastructure user (`InfrastructureAccess`, the account's
   Lake Formation administrator), in Production: *Lake Formation → Administration → Application
   integration settings → Allow external engines to access data in Amazon S3 locations with full table
   access*, saved.
3. **[Claude]** the after-reading, the same two commands: the flag `true`, and the admin, the default
   lists and the parameters as before. A moved parameter is INT-11's failure and is put back by the
   same page before anything else runs. Then Stage 11's threat-model row, and `AWS_STATE.md`'s word on
   the flag per account.

**Done 2026-10-23, 19:29 to 19:49 UTC**: the flag reads `true` in Production, the rest unchanged, `DT-5`
passing (Stage 9's log; `TM-26`). The console refused the page first in `us-east-2`, the Region ceiling:
the Lake Formation console is opened in `us-west-2`.

The lake's half, its own `lakeformation.tf`, waits for the first run's wording (§P step 5).

### 0.4 The applies that need nothing up

Each is a `[P]` slice or an S3 write the infrastructure user makes from the laptop, with the tunnel
down; each shortens the Production sitting by one apply. `[Claude⚡]` on the user's word, as
`awsds-infra-prod`, each from a fresh plan (Recipe A) and re-planned `No changes`:

1. `production/sagemaker/`, 2.4's proof job and the job role's `CommitTheIcebergWrites` (*1 to add,
   1 to change*), then the script's upload (§P step 3), the one write the user's hand or Claude's makes
   under `applications/stage-09-proofs/`. **Done 2026-10-23, 21:18 and 21:20 UTC** (Stage 9's log).
2. `production/workloads/` on `vpc-v0.4.0`, the S3 gateway endpoint's policy admitting the workers'
   code bucket (Stage 10 1.2). **Applied 2026-10-22** with Stage 9's passes; a fresh plan read
   `No changes` on 2026-10-23.
3. `production/foundation/`, 9.4's `RunTheGovernedWarehouseDdl` on the deploy role (*1 to change*, with
   the alerts var-file), pass 6's, harmless before it. **Done 2026-10-23, 21:19 UTC.**
4. `production/warehouse/`, the namespace and its guards (*9 to add*), pass 6's start: it bills the
   admin secret from its creation and opens `EXC-13`'s Production row, so it waits for the user to want
   pass 6 begun; the compute stays held either way.

What stays with the environment: the runs, the legs, the warehouse's compute and SQL.

### 0.5 What runs before the next sitting, read 2026-10-24

1. **[Claude⚡] The deploy roles' orchestration grant**, before §T: 3.8's calls replayed through the
   policy simulator as both deploy roles found `states:ValidateStateMachineDefinition` granted to neither,
   and the provider calls it while it plans a state machine, so both legs would stop at the orchestration
   apply (Stage 10 1.5). As the infrastructure user, Recipe A, each with the alerts var-file:
   `staging/foundation/` as `awsds-infra-staging` and `production/foundation/` as `awsds-infra-prod`, each
   *0 to add, 1 to change*, the policy `awsds-<env>-deploy-orchestration-resources`; then the simulator,
   `states:ValidateStateMachineDefinition` on `*` read `allowed` for `awsds-deploy-staging` and
   `awsds-deploy-prod`, and `./scripts/check-copies.py`. **Done 2026-10-24, 02:52 and 02:53 UTC**, each
   re-planned `No changes`, the simulator reading both actions `allowed` for both roles.
2. **[user] The persona's read of the twenty rows** (Stage 9 5.4's first query, the count 20 after the
   pickup), as the Data Scientist User through `awsds-scientist-prod`; Athena and the `[P]` workgroup need
   nothing up (D39). The commands are 5.4's. **Done 2026-10-24**: `SUCCEEDED`, `n` 20, the result at
   `s3://awsds-prod-derived/results/<id>.csv` and not at the request's `not-enforced/` (Stage 9's log).
3. **[Claude⚡] `EXC-02`'s cleanup**, on the user's word, as `awsds-infra-data`: the three `.txt` objects
   the row names deleted from `awsds-data-dropbox`, a delete marker each under the 90-day noncurrent
   rule, and the row retired in `AWS_STATE.md`. **2026-10-24**: Claude Code's auto-mode classifier
   refused Claude's delete, so the user runs it from the project folder as the infrastructure user, and
   Claude reads the bucket back and retires the row (**done 2026-10-24**, the delete markers at 03:12 UTC,
   the row closed):

   ```bash
   for k in incoming/2026/08/20/probe-4d-sandbox.txt incoming/2026/09/18/awsds-6g-24-probe.txt incoming/2026/09/18/awsds-6g-24-probe-tunnel.txt; do aws s3api delete-object --bucket awsds-data-dropbox --key "$k" --profile awsds-infra-data --region us-west-2; done
   ```
4. **[user] Stage 9 decision 14**, the account that registers the datashare (recommended: Data
   Governance), before §W step 5; and 6d decision due 11, Sandbox's `lakeformation` endpoint (recommended:
   keep it, Stage 10 0.5).

## H. The hub and GitLab

`make hub-up`, then `make gitlab-up BUILD=1`, the tunnel, in [`gitlab.md`](gitlab.md) §U's order: the
build runner takes the image builds of steps 3 and 4 and the pipelines on `main`. What this sitting
closes besides Stages 8 to 10 is the waiting list's Hub and GitLab rows.

1. **[user] GitLab's settings for pass 4** (Stage 8 decision 2, `gitlab.md` §M): `main` pushed to
   `awsds/infrastructure` from the project folder at `origin/main` (`git push gitlab main`), the job
   token's allowlist of `awsds/infrastructure` admitting `awsds/app-etl` and dropping `awsds/dev-env`,
   `awsds/deployment-managers` a member of `awsds/infrastructure`, and Stage 7 3.5's three persona
   memberships. The promotion legs clone the mirror with the job token and print its commit, so a
   stale push shows in the job's log.
2. **[user] MR !4 merged** on `awsds/app-etl` (the release's notes without backticks), then the legs'
   merge request: a branch of `awsds/app-etl` from `examples/app-etl/` at this repository's `main`,
   by `gitlab.md`'s "The application template" procedure (clone, `rsync`, commit, push, MR), which
   brings `.gitlab-ci.yml`'s `staging-*`, `production-*` jobs and the `--lint` option. The pipeline
   editor validates it before the push; its branch pipeline runs the test stage alone. The legs need no
   CI/CD variable beyond the eleven the project holds (read 2026-10-24): `INFRA_DIR`, `IMAGE_REPO`,
   `AWSDS_WORKFLOWS` and `LINT_INSTANCE_TYPES` are the file's, `BUNDLE_OBJECT`, `BUNDLE_SHA256` and
   `JOB_IMAGE_URI` earlier jobs' dotenv artifacts.
3. **[user] The house image `default-v0.9.0`** with the 72-name `NO_PROXY` literal (Stage 8 1.1, Stage
   17 decision 4), registered as version 10: the merge request on `awsds/dev-env` from the copy under
   `gitlab/awsds/dev-env/`, the steward's tag, the release gate; `./scripts/gitlab-mirror.py` after the
   merge. `DE-5` turns green with it.
4. **[user] The deploy image on Terraform 1.16.6**, once the laptop runs it (the user's install;
   `upstream-releases.md`): the two pins in `gitlab/awsds/deploy-image/Dockerfile`, the merge request,
   the tag, its digest into `production/runners/` and a `production/runners/` apply, `make gitlab-up
   BUILD=1` again so the build runner stays. Until then the deploy image runs 1.15.8, which every
   slice's `versions.tf` admits.
5. **[Claude]** `./aws/cicd.py` after the runners' boot (`CI-1`, `CI-9`), and `GM-1` to `GM-8` on the copies.

## P. Production: Stage 9's pass 3 and Stage 10's 0.5

The proof job needs `workloads-egress/` alone (16 to add, the seven endpoints and the DNS Firewall):
`make up ENV=production` with no `ONLY=` would also raise `egress/` (SharedServices' twelve endpoints),
`runners/` (three hosts that register with a GitLab that is down) and `probes/`, so the sitting runs
`make up ENV=production ONLY=workloads-egress`. Every `make up` checks the hub, so `make hub-up` comes
first; VPC-Workloads has no proxy path, so the hub serves the check alone, and with the hub down the
slice is applied by hand instead (Recipe A, as `awsds-infra-prod`), the check guarding proxy clients
that this VPC has none of. `make down ENV=production ONLY=workloads-egress` ends it. Nothing else of §H
is needed.

1. **The flag on in Production** (§0.3, done 2026-10-23), `DT-5` read again at the sitting.
2. **`production/sagemaker/` applied** (done 2026-10-23, 21:18 UTC: *1 added, 1 changed*, re-plan
   `No changes`).
3. **The script uploaded** (done 2026-10-23, 21:20 UTC, version `LhV4dvLqaXJCFqSJm.Z0tpmqShZjHM95`); a
   changed script is uploaded again with the same command, the key the job's `script_location` names:

   ```bash
   aws s3 cp terraform-live/production/sagemaker/proofs/producer_proof.py s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py --profile awsds-infra-prod --region us-west-2
   ```

4. **[user] `make up ENV=production ONLY=workloads-egress`**, as the infrastructure user, the hub up
   (or the slice by hand with the hub down, above).
5. **[Claude⚡] The producer run** (Stage 9 2.4), then its readings:

   ```bash
   aws glue start-job-run --job-name awsds-prod-producer-proof --arguments '{"--MODE":"producer"}' --profile awsds-infra-prod --region us-west-2
   ```

   ```bash
   aws glue get-job-runs --job-name awsds-prod-producer-proof --max-results 3 --query 'JobRuns[].[Id,JobRunState,StartedOn,CompletedOn,ErrorMessage]' --output table --profile awsds-infra-prod --region us-west-2
   ```

   The log is `/aws-glue/jobs/logs-v2`'s stream of the run id (`--enable-continuous-cloudwatch-log`), every
   line of the script's prefixed `[producer-proof`. The readings, each recorded in Stage 9's log: the
   insert's commit or its refusal with the wording (the first run answers whether full-table access
   admits a writer without `ALL`, and whether the flag of §0.3 was needed); the row count read back;
   the direct put's refusal, *"no identity-based policy allows the s3:PutObject action"* expected; and,
   in Production's CloudTrail, the run's Lake Formation events, `GetDataAccess` and the
   `GetTemporaryGlue*Credentials` pair, read for `vpcEndpointId` (Stage 10 0.5, decision 12 (a)'s
   `lakeformation` endpoint):

   ```bash
   aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventSource,AttributeValue=lakeformation.amazonaws.com --start-time "$(date -u -v-2H +%Y-%m-%dT%H:%M:%SZ)" --query 'Events[].[EventTime,EventName,Username]' --output table --profile awsds-infra-prod --region us-west-2
   ```

   A refusal names its layer: Lake Formation's wording (*"Insufficient Lake Formation permission(s)"*,
   which permission) is the grant's shape, decision 13's fallback or 2.1's `ALL`; an IAM wording naming
   `glue:UpdateTable` is the role's; a timeout at the Glue or Lake Formation API is the endpoint set.
   **The first run (2026-10-23, 21:43 UTC) was refused at the vend naming the data lake settings**,
   Production's flag on and the lake's unset, so decision 13's fallback runs before the second run:
   5a. **[Claude⚡] The lake's flag**: `data-governance/data/lakeformation.tf` carries
   `allow_full_table_external_data_access = true`; `./aws/datalake.py awsds-infra-data` before (`DL-5`
   4/TRUE), a fresh plan as `awsds-infra-data` (*1 to change*, the flag `false -> true` alone), the apply
   on the user's authorization, the same script and `get-data-lake-settings` after, then step 5 again.
   With both flags on, a commit answers verification xxviii's first two halves and leaves the third
   half (whether the engine's flag is also needed) unmeasured; the measurement is the user's hand in
   Production's console, the flag off, a third run, the flag on again, bracketed by `DT-5`.
   **Done 2026-10-23**: the flag applied at 22:03 UTC, the second run `SUCCEEDED` at 22:06 (Stage 9's log).
6. **The drop is in place** (Stage 9 2.5's first half, done 2026-10-23): `incoming/2026/10/23/trades.csv`,
   and 2.6 read the same evening, the writer's read-back refused by the set's implicit deny. A second
   drop before the pickup is optional, the same command on the day's prefix as the Data Scientist User
   in Sandbox:

   ```bash
   aws s3 cp examples/app-etl/samples/trades.csv "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" --profile awsds-scientist-sandbox --region us-west-2
   ```
7. **[Claude⚡] The pickup run** (2.5), `--arguments '{"--MODE":"pickup"}'` on the same command, then its
   readings: the keys the job listed, the rows read (the KMS half: a refusal on the lake key surfaces
   as an S3 error naming the object), the rows curated, each key gone after its delete (`404` on the
   `head-object`). `EXC-02`'s three `.txt` objects are not CSV and stay: the row retires with a
   deliberate `InfrastructureAccess` cleanup once the pickup has run, as `AWS_STATE.md` has it.
   **Done 2026-10-23, 22:11 UTC** (Stage 9's log): one CSV, ten rows read and curated, the key deleted, a
   delete marker over a version the bucket expires at 90 days.
8. **[Claude]** `./aws/deploytargets.py`, `./aws/datalake.py` (`DL-5` after a run that vended
   through the lake), the table's rows read as the persona through Athena (5.4's first query), and the
   run's events in CloudTrail; `./aws/egress.py` §6 before `make down ENV=production`.
   **Taken 2026-10-23, 22:14 to 22:16**: `deploytargets.py` and `datalake.py` all checks passed, `EG-5`
   ~0.070 USD/h with the seven endpoints up, `make status` 0.0856 USD/h; the persona's Athena read of the
   twenty rows and `make down` were left to the user.

## T. The tag: Stage 8's pass 4 with Stage 10's passes 1 and 2

Needs §H done (the legs on `awsds/app-etl`'s `main`, the mirror pushed, the memberships), the hub,
GitLab and the three runners up (`make gitlab-up BUILD=1`: the tag pipeline's untagged jobs, the
production gate among them, run on the build runner alone), and Sandbox's `egress/` up (`make up ENV=sandbox ONLY=egress`, the
infrastructure user's, since no pipeline identity raises it). Stage 9's pass 3 (§P) before it, so the
first promotion carries a lake the job role has written (decision 23).

1. **[user] Pass 1's `deploy --targets dev`** from a space on the house image as the project role
   (Stage 10 2.1, Stage 8 decision 22), and the reads 2.1 lists, when the Sandbox sitting is up anyway.
2. **[user] The tag** `v0.3.0` on `awsds/app-etl`'s `main`, after the legs merged: the pipeline runs
   `test`, `build-image`, `build-task-code`, `test-deploy` (the CLI into the `test` project as
   `awsds-deploy-sandbox-test`), `store-bundle`, `release` (verification xx's `cli` image reading), then
   the legs.
3. **[pipeline] The Staging leg**: `staging-up` (3.1, `make up ENV=staging ONLY=egress` as
   `awsds-deploy-staging`, 4.3a's first apply, 16 to add), `staging-deploy` (3.2: the bundle checked,
   the render, 2.3's lint, the tree under `awsds-staging-outputs/applications/app-etl/<tag>/`, the
   application slice's saved plan through 2.3's `lint-plan` and applied, the orchestration slice
   applied, INT-14 in Staging, Stage 10 verification ii),
   `staging-test` (3.3: the chain's machine started and followed, Stage 10 decision 19), `staging-down`
   (3.4). What is read at this leg and nowhere before: whether `uv run` resolves the dev group on the
   runner, the deploy role's Cloud Control and Glue calls against their grants, the worker's preparation
   with no `ecr.*` endpoint (Stage 10 verification xvi), `TriggerMode`'s literal, the key's encryption
   context in the saver's and the worker's calls (Stage 10 decision 2), and Staging's `release.auto.tfvars.json`
   kept as an artifact (the `VersionId`s 3.7 records). **3.8 ran by hand first, on 2026-10-23** (Stage 8's and
   Stage 10's logs): the worker's preparation with no `ecr.*` endpoint, `TriggerMode`'s literal and the key's
   encryption context are read, and two statements gained `kms:GenerateDataKey` for the XCom encryption
   (`orchestration-v0.2.0`); `uv run` on the runner, the deploy role's calls and the artifact remain the leg's.
4. **[user] The gate** (3.5): `production-plan`, its plan passed by `lint-plan`, read beside `staging-test`'s artifacts, then
   `production-gate` by a `deployment-managers` member. Before `production-deploy`: `make up
   ENV=production` by the user (§P's step 4 if the sitting is one), since a Production run needs
   `workloads-egress/`.
5. **[pipeline] `production-deploy`** (3.6, `awsds-deploy-prod`): the service-linked role's creation
   in the deploy role's session on Production's first `CreateWorkflow` (Stage 10 1.5's statement, 1.6's
   record), then `production/orchestration/` with the chain's schedule `ENABLED`; verification vi,
   `CI-8` diffed across the run (INT-08).
6. **[user] 3.7**: both `release.tf`s committed with the tag, the digest, the bundle's SHA256 and the
   Staging and Production `VersionId`s from the two legs' artifacts; the mirror pushed again.
7. **[user] 3.8**: the by-hand parity once, the sequence in Stage 8 3.8, as `awsds-infra-staging`. **Run by
   Claude first on 2026-10-23**; the parity reading now belongs to the pipeline's leg.
8. **[user + pipeline] Stage 10 6.1**: the schedule fires at 06:30 UTC with `workloads-egress/` up,
   or the cron is moved into the sitting by a commit and the pipeline applies it; the pause lever
   (`state = DISABLED`) through the slice; 3.2's deliberate break through the slice, the failure rule
   heard, the diagnosis from the APIs; 6.3's sentence in the log before the first `make down
   ENV=production`.
9. **[Claude]** `./aws/orchestration.py` (`OR-9` on the layer), `./aws/cicd.py`, `./aws/egress.py` §6
   after `make down` in every account the sitting raised: zero burn, no NAT gateway.

## W. The governed warehouse: Stage 9's pass 6

Separable and last; nothing needs it. In a Production sitting with the hub up.

1. **[Claude⚡] `production/foundation/` applied** with 9.4's `RunTheGovernedWarehouseDdl` on the deploy
   role, planned 2026-10-23 (the alerts var-file on the command line, or the subscription is destroyed).
   **Done 2026-10-23, 21:19 UTC.**
2. **[Claude⚡] `production/warehouse/` applied** (9 to add) as `awsds-infra-prod`, by hand; the
   refusal-9 row removed from `layers.py` in the same sitting; `EXC-13`'s Production row written.
   **Done 2026-10-23, 22:07 UTC**, the re-plan `No changes`; `warehouse-compute/` plans *2 to add* (22:10).
3. **[user] `make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift`** (run by the user on
   2026-10-24, the workgroup `AVAILABLE` at 00:23 UTC):
   `warehouse-compute/` with the namespace in place, and the `redshift-serverless` endpoint in
   VPC-Workloads for a job that calls the API (9.1). The usage limit counts from zero with each
   workgroup.
4. **[Claude⚡] 9.3's SQL** through the Data API with the admin secret, the statements in the step (the theme
   `trades` and the quota 1 TB confirmed by the user on 2026-10-24):
   the `PUBLIC` revokes on the three databases, `governed`, the owner user, the schema with its quota,
   the role, the two database users, the default privileges. **Done 2026-10-24, 00:27 to 00:29 UTC** (Stage 9's log).
5. **9.5's shape** (decision 5, the datashare) and 9.5a's reading first; 9.6's pair; 9.7's INT-24 from
   a Sandbox project; 9.8's paperwork; `./aws/warehouse.py --sql` and its burn line beside `egress.py`
   §6; `make down ENV=production` before the sitting ends, the only guard that is not a setting.
   **9.5 and 9.5a are a sitting of their own**: the datashare's two sides, the producer's SQL in Production and
   the lake's registration and federated database, then the Sandbox mount for 9.7; 9.6 and 9.7 are the user's.
   **Read 2026-10-24**: 9.5 carries the command sequence, five steps across Production, the account Stage 9
   decision 14 names and Sandbox; 9.5a is settled by decision 5 (no switch); the sitting raises both
   warehouses' compute (`make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift`, then
   Sandbox's `warehouse-compute/`) and measures first whether Sandbox reads with Production's workgroup
   gone; 9.6 and 9.7 wait for a table in `trades`, which 9.4's DDL and load job create in a release after
   `v0.3.0`.
   `./aws/warehouse.py awsds-infra-prod --sql` passed on 2026-10-24, and `make down ENV=production` ended the sitting.

## Q. After the quotas: Stage 10's pass 3

When the training and transform quotas of `ml.m5.large` are above zero in both accounts (§0.2): 5.1's
training task as a second workflow of the manifest with a chain of its own, 5.2's registration and
approval jobs, 5.4's batch transform in Staging then Production, 5.5's far-side proof — a release of
`app-etl` that runs §T's chain again.

## R. The readings at the end of every sitting

```bash
./aws/egress.py awsds-infra-prod awsds-infra-staging awsds-infra-sandbox-1
```

Zero burn in every account the sitting raised, no interface endpoint left, no NAT gateway anywhere;
then the stage's own instrument (`cicd.py`, `deploytargets.py`, `orchestration.py`, `datalake.py`,
`warehouse.py` after §W), `make status`, and the log entry of each step, in the sitting it ran.
