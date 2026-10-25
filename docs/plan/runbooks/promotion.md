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

**Where it stands, 2026-10-25**: §0, §P, §T, §W and §V done, and §H but its steps 3 and 4, which §N
carries. `v0.3.3` was the first promotion; the data release `v0.4.2` (after `v0.4.0` and `v0.4.1` stopped
in their legs) reached Production, the model chain ran and was approved, the warehouse was loaded, §W
step 5's datashare was built and read from a Sandbox project, verification ix was answered on `v0.4.5`,
the 06:30 and 07:00 UTC schedules started their chains unattended (6.1), and §R read zero burn in every
account after the downs. What the three stages leave is §N, ordered by the sitting that runs it.

| § | Holds |
|---|---|
| [§0](#0-before-any-sitting-with-the-environment-down) | what runs today, with nothing up: the persona proofs, the quota requests, the flag of decision 13, the deploy roles' grant (§0.5) |
| [§H](#h-the-hub-and-gitlab) | the hub and GitLab: the user's GitLab acts, the legs' merge request; its steps 3 and 4, the next house image and the deploy image, are §N's |
| [§P](#p-production-stage-9s-pass-3-and-stage-10s-05) | Production: the proof job's two runs, Stage 9's producer pair and pickup |
| [§T](#t-the-tag-stage-8s-pass-4-with-stage-10s-passes-1-and-2) | the tag: Stage 8's pass 4 with Stage 10's passes 1 and 2, and Stage 9's 8.5 |
| [§W](#w-the-governed-warehouse-stage-9s-pass-6) | the governed warehouse, Stage 9's pass 6: steps 1 to 4 done, step 5 run within §V |
| [§V](#v-the-data-release-v040) | the data release, the tag `v0.4.2` since `v0.4.0` and `v0.4.1` stopped in their legs: Stage 9's 8.5 and 9.4 to 9.7, Stage 10's pass 3 and 6.1, Stage 8's ix |
| [§N](#n-the-next-release-what-stages-8-9-and-10-leave) | what Stages 8, 9 and 10 leave, by sitting: the steps that need nothing up, the next release through Staging and Production (`EXC-22`, Stage 8 xxiv, Stage 9 xii, the Scheduler's placeholder), the warehouses, a Sandbox space, the deliberate exercises, and what waits on something else |
| [§Q](#q-after-the-quotas-stage-10s-pass-3) | after the quotas: Stage 10's pass 3, now within §V |
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
case id, the answer a person's at AWS. **Read 2026-10-24, 03:47 UTC**: the applied quotas above zero
in both accounts, 20 for `ml.m5.large`'s training and 8 for its transform among them (Stage 9 3.5), the
requests still `CASE_OPENED`; §Q opens, and its steps are §V's.

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
4. **[user] Stage 9 decision 14**, the account that registers the datashare, and 6d decision due 11,
   Sandbox's `lakeformation` endpoint. **Taken 2026-10-24, as recommended**: Data Governance registers and
   grants the datashare; the Sandbox endpoint stays.

### 0.6 The applies v0.4.0 needs, with nothing up

Each a `[P]` slice, planned 2026-10-24 (the logs): **[Claude⚡]** on the user's word, as the
infrastructure user with `InfrastructureAccess`, from a fresh plan (Recipe A), re-planned `No changes`,
the `foundation/` plans with `-var-file=<project folder>/secrets/alerts.auto.tfvars`. Each only adds:
v0.3.0 runs the same on either side of them.

| Slice | Profile | Plan | What it adds |
|---|---|---|---|
| `production/data/` | `awsds-infra-prod` | 0 / 1 / 0 | `models/` among the deploy role's prefixes on `awsds-prod-outputs`; the governed source's four outputs the application slice reads |
| `staging/data/` | `awsds-infra-staging` | 0 / 1 / 0 | the same on `awsds-staging-outputs` |
| `production/sagemaker/` | `awsds-infra-prod` | 0 / 1 / 0 | `ConnectToTheGovernedWarehouse` on the job role; the output `training_image_uri` |
| `staging/sagemaker/` | `awsds-infra-staging` | outputs | the output `training_image_uri` |
| `production/foundation/` | `awsds-infra-prod` | 0 / 1 / 0 | the deploy role's model, transform and registry calls, `models/` read, the load job's name |
| `staging/foundation/` | `awsds-infra-staging` | 0 / 1 / 0 | the same without the registry |

Then `./aws/deploytargets.py` on the five infrastructure profiles, `./scripts/check-copies.py`, and the
policy simulator as each deploy role on `sagemaker:CreateModel`, `CreateTransformJob` and, for
`awsds-deploy-prod`, `CreateModelPackage` and `UpdateModelPackage` on the group's ARN, expected
`allowed`. **Done 2026-10-24, 17:51 to 17:55 UTC** (Stage 9's and Stage 10's logs): each slice applied
from a fresh plan of the counts above and re-planned `No changes`, `deploytargets.py` all checks passed
before and after, the simulator reading every new call `allowed` but `CreateTransformJob` against a job's
ARN, where it drops the volume key (`lessons.md`); the first real transform is `staging-model`'s.

Beside them, the user's two acts that need nothing up: the merge of `awsds-workflows` PR (the branch
`treino-e-repositorio-de-algoritmo`, `d60e1ad`, the rule `treino`); the template pins `d60e1ad`, which
stays reachable through the PR, and the pin moves to the merge's commit in the next template change.
**Done 2026-10-24**: PR #24 squash-merged as `d856982c`, the tree of `d60e1ad`; `v0.4.0` ran on `d60e1ad`,
and MR !9 moved the template's pin to `d856982c`.

## H. The hub and GitLab

`make hub-up`, then `make gitlab-up BUILD=1`, the tunnel, in [`gitlab.md`](gitlab.md) §U's order: the
build runner takes the image builds of steps 3 and 4, and the test runner the merge requests' and
`main`'s pipelines. What this sitting closes besides Stages 8 to 10 is the waiting list's Hub and GitLab
rows.

1. **[user] GitLab's settings for pass 4** (Stage 8 decision 2, `gitlab.md` §M): the mirror
   `awsds/infrastructure` pushed from the project folder at `0236a99d`, the commit v0.3.0's legs were
   prepared and read against (`git push gitlab 0236a99d:refs/heads/main`; §V pushes `main` itself), the job
   token's allowlist of `awsds/infrastructure` admitting `awsds/app-etl` and dropping `awsds/dev-env`,
   `awsds/deployment-managers` a member of `awsds/infrastructure`, and Stage 7 3.5's three persona
   memberships. The promotion legs clone the mirror with the job token and print its commit, so a
   stale push shows in the job's log.
2. **[user] MR !4 merged** on `awsds/app-etl` (the release's notes without backticks), then the legs'
   merge request: a branch of `awsds/app-etl` from `examples/app-etl/` at `0236a99d`, v0.3.0's template
   (`main` since 2026-10-24 carries v0.4.0's, §V),
   by `gitlab.md`'s "The application template" procedure (a fresh clone, the files swapped through
   `git archive`, a branch pushed, the MR), which
   brings `.gitlab-ci.yml`'s `staging-*`, `production-*` jobs and the `--lint` option. The pipeline
   editor validates it before the push; its branch pipeline runs the test stage alone. The legs need no
   CI/CD variable beyond the eleven the project holds (read 2026-10-24): `INFRA_DIR`, `IMAGE_REPO`,
   `AWSDS_WORKFLOWS` and `LINT_INSTANCE_TYPES` are the file's, `BUNDLE_OBJECT`, `BUNDLE_SHA256` and
   `JOB_IMAGE_URI` earlier jobs' dotenv artifacts.
3. **[user] The house image `default-v0.9.0`** with the 72-name `NO_PROXY` literal (Stage 8 1.1, Stage
   17 decision 4), registered as version 10: the merge request on `awsds/dev-env` from the copy under
   `gitlab/awsds/dev-env/`, the steward's tag, the release gate; `./scripts/gitlab-mirror.py` after the
   merge. `DE-5` turns green with it.
4. **[user] The deploy image on Terraform 1.16.6**, the laptop running it since 2026-10-25 and the two pins moved in
   `gitlab/awsds/deploy-image/Dockerfile` (`upstream-releases.md`): the merge request,
   the tag, its digest into `production/runners/variables.tf`, and the slice applied by `make gitlab-up
   BUILD=1`, which keeps the build runner; the flag left out destroys it. Until then the deploy image runs 1.15.8, which every
   slice's `versions.tf` admits and which refuses a state the laptop's 1.16.6 has written: this step comes
   before any laptop apply or `make up` of a slice the pipeline reads or applies (N.1 step 2).
5. **[Claude]** `./aws/cicd.py` after the runners' boot (`CI-1`, `CI-9`), and `GM-1` to `GM-8` on the copies.

**Done 2026-10-24** (Stage 8's log): the environment raised by the user at 18:10 UTC, `cicd.py` 0
failed; steps 1, 2 and 6 by the user, read back at 18:47: the mirror at `0236a99d`, MR !4 merged and the
legs' MR !5 merged, `awsds/app-etl`'s `main` at `5a7d009a` identical to `examples/app-etl/` at
`0236a99d`. Steps 3 and 4 are left: the house image does not hold Stages 8 to 10, and the deploy image is rebuilt
now that the laptop runs Terraform 1.16.6 (since 2026-10-25).
6. **[user] The CI/CD variable `TRAINING_IMAGE_URI`** on `awsds/app-etl`, protected, for v0.4.0's
   `test-deploy`: the value `terraform -chdir=terraform-live/staging/sagemaker output -raw
   training_image_uri` after §0.6, AWS's XGBoost image by digest. v0.3.0 reads no such variable.

## P. Production: Stage 9's pass 3 and Stage 10's 0.5

The proof job needs `workloads-egress/` alone (16 to add, the seven endpoints and the DNS Firewall):
`make up ENV=production` with no `ONLY=` would also start GitLab and raise `egress/` (SharedServices'
twelve endpoints), `warehouse-compute/` (the 4-RPU workgroup), `runners/` (the deploy and test runners,
a build runner destroyed) and `probes/`, so the sitting runs
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
production gate among them, run on the build runner alone), and Sandbox's and Staging's `egress/` up (`make up ENV=sandbox ONLY=egress`, `make up ENV=staging
ONLY=egress`, the infrastructure user's: no pipeline identity raises a shared slice, Stage 8 decision 27). Stage 9's pass 3 (§P) before it, so the
first promotion carries a lake the job role has written (decision 23).

1. **[user] Pass 1's `deploy --targets dev`** from a space on the house image as the project role
   (Stage 10 2.1, Stage 8 decision 22), and the reads 2.1 lists, when the Sandbox sitting is up anyway;
   §N.3 carries it.
2. **[user] The tag** `v0.3.0` on `awsds/app-etl`'s `main`, after the legs merged (**run 2026-10-24,
   pipeline #64**: `test-deploy` passed, then `release` and the legs' clone refused the lab's CA, the
   legs raising nothing; the fix, the CA root the runner mounts, is MR-borne. `v0.3.1` named the legs'
   merge, its pipeline #66 cancelled. **`v0.3.2`, pipeline #68**: `release` passed; `staging-deploy`
   stopped at the workflow's tag-on-create and `staging-down` at the Studio hook, both fixed in this
   repository and the grant applied the same evening; the retried `staging-test` stopped at the clone,
   in the folder its downloaded artifact had created, the template's fix MR-borne. The first promotion's
   tag is **`v0.3.3`**. While the mirror stays at `0236a99d` its `staging-down` stops at the hook, so
   Staging comes down by hand, `make down ENV=staging` as the infrastructure user. Stage 8's and Stage
   10's logs): the pipeline runs
   `test`, `build-image`, `build-task-code`, `test-deploy` (the CLI into the `test` project as
   `awsds-deploy-sandbox-test`), `store-bundle`, `release` (verification xx's `cli` image reading), then
   the legs.
3. **[user] `staging-gate`** (decision 28, once the mirror carries it), then **[pipeline] the Staging
   leg**: `staging-check` (3.1 since decision 27: Staging's `egress/` read as
   `awsds-deploy-staging`, the user having raised it; the legs of 2026-10-24 ran `staging-up`, `make up
   ENV=staging ONLY=egress` as the role, 4.3a's first apply, 16 to add), `staging-deploy` (3.2: the bundle checked,
   the render, 2.3's lint, the tree under `awsds-staging-outputs/applications/app-etl/<tag>/`, the
   application slice's saved plan through 2.3's `lint-plan` and applied, the orchestration slice
   applied, INT-14 in Staging, Stage 10 verification ii),
   `staging-test` (3.3: the chain's machine started and followed, Stage 10 decision 19), and no
   teardown job since decision 27 (3.4 retired): the user's `make down ENV=staging` ends the sitting. What is read at this leg and nowhere before: whether `uv run` resolves the dev group on the
   runner, the deploy role's Cloud Control and Glue calls against their grants, the worker's preparation
   with no `ecr.*` endpoint (Stage 10 verification xvi), `TriggerMode`'s literal, the key's encryption
   context in the saver's and the worker's calls (Stage 10 decision 2), and Staging's `release.auto.tfvars.json`
   kept as the artifact `staging-release.auto.tfvars.json` (the `VersionId`s 3.7 records). **3.8 ran by hand first, on 2026-10-23** (Stage 8's and
   Stage 10's logs): the worker's preparation with no `ecr.*` endpoint, `TriggerMode`'s literal and the key's
   encryption context are read, and two statements gained `kms:GenerateDataKey` for the XCom encryption
   (`orchestration-v0.2.0`); `uv run` on the runner, the deploy role's calls and the artifact remain the leg's.
4. **[user] The gate** (3.5): `production-plan`, its plan passed by `lint-plan`, read beside `staging-test`'s artifacts, then
   `production-gate` by a `deployment-managers` member. Before `production-deploy`: `make up
   ENV=production ONLY=workloads-egress` by the user (§P step 4), since a Production run needs
   `workloads-egress/`; `production-deploy` reads the slice first (decision 27) and fails with that command
   while it is down. The command without `ONLY=` applies `runners/` without `BUILD=1`, and destroys
   the build runner `production-gate` runs on.
5. **[pipeline] `production-deploy`** (3.6, `awsds-deploy-prod`): the service-linked role's creation
   in the deploy role's session on Production's first `CreateWorkflow` (Stage 10 1.5's statement, 1.6's
   record), then `production/orchestration/` with the chain's schedule `ENABLED`; verification vi,
   `CI-8` diffed across the run (INT-08). **Run 2026-10-24, `v0.3.3`'s pipeline #71** (Stage 8's and Stage
   10's logs): Staging's leg `SUCCEEDED` (`v0-3-3-71`, 15 min), `staging-down` stopped at the Studio hook
   and the user's `make down ENV=staging` took Staging down; the gate at 21:31 UTC, and
   `production-deploy` created the job, the workflow and the chain, the service-linked role made in the
   deploy role's session at 21:33:58 UTC.
6. **[user] 3.7**: both `release.tf`s committed with the tag, the digest, the bundle's SHA256 and the
   Staging and Production `VersionId`s from the two legs' artifacts; the mirror pushed again. **`v0.3.3`
   recorded in PR #254 on 2026-10-24**, each `VersionId` read back by `head-object`; the mirror's push
   follows the merge.
7. **[user] 3.8**: the by-hand parity once, the sequence in Stage 8 3.8, as `awsds-infra-staging`. **Run by
   Claude first on 2026-10-23**; the parity reading now belongs to the pipeline's leg.
8. **[user + pipeline] Stage 10 6.1**: the schedule fires at 06:30 UTC with `workloads-egress/` up,
   or the cron is moved into the sitting by a commit and the pipeline applies it; the pause lever
   (`state = DISABLED`) through the slice; 3.2's deliberate break through the slice, the failure rule
   heard, the diagnosis from the APIs; 6.3's sentence in the log before the first `make down
   ENV=production`. **2026-10-24**: Production's first run `SUCCEEDED` by hand (Claude, the user's
   authorization), 6.3's sentence written from Staging's teardown, and `workloads-egress/` left up for the
   schedule's firing at 06:30 UTC on 2026-10-25. The next morning: **[Claude]** the execution the schedule
   started and its run's `RunType` (verification xxiv); §V step 1's third producer run fits there, the
   endpoints still up; then **[user]** `make down ENV=production ONLY=workloads-egress`.
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
   **Read 2026-10-24**: 9.5 carries the command sequence, five steps across Production, Data Governance
   (Stage 9 decision 14) and Sandbox; 9.5a is settled by decision 5 (no switch); the sitting raises both
   warehouses' compute (`make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift`, then
   Sandbox's `warehouse-compute/`) and measures first whether Sandbox reads with Production's workgroup
   gone; 9.6 and 9.7 wait for a table in `trades`, which 9.4's DDL and load job create in a release after
   `v0.3.0`.
   `./aws/warehouse.py awsds-infra-prod --sql` passed on 2026-10-24, and `make down ENV=production` ended the sitting.
   9.5 to 9.7 ran on 2026-10-25 within §V step 8.

## V. The data release: v0.4.0

What v0.3.x leaves, written 2026-10-24 (the stage logs): the Glue job's governed read and the
application's table (Stage 9 8.5), the warehouse's DDL job and its load workflow (9.4, decision 15), the
model chain (Stage 10 pass 3, decisions 21 and 22), and the scheduled end-to-end (6.1). Needs §T, run
2026-10-24 with `v0.3.3` and recorded in PR #254 (3.7); PR #254 merged, and `awsds-workflows`' PR #24,
merged as `d856982c`, the template's pin since MR !9; §0.6
applied, §H step 6, the hub, GitLab and the three runners up, and Sandbox's `egress/` up. Every `make up
ENV=production` here carries `ONLY=`, or the build runner is destroyed.

1. **[user + Claude] The third producer run first** (verification xxviii's last clause): Production's
   full-table flag off in its Lake Formation console, `DT-5` read, the run, the flag on again and `DT-5`
   read, with `workloads-egress/` up (§P steps 4 and 5's commands). A commit with Production's flag off
   says an engine's flag is not needed, and Staging's leg reads through the lake's flag alone; a refusal
   says it is, and **[user]** Staging's flag goes on the same way before step 3 (`DT-5` bracketing it).
   The run adds ten rows to `curated.trades`, which the tests count from, not assume.
   **Done 2026-10-24, 22:14 to 22:29 UTC** (Stage 9's log): the run committed with Production's flag off,
   so Staging's flag stays unset; `curated.trades` at 30 rows, Production's flag on again, `DT-5` passing.
2. **[user] The legs' merge request for v0.4.0** on `awsds/app-etl`, from `examples/app-etl/` at `main`
   (the procedure of §H step 2), merged; the mirror pushed at `main` (`git push gitlab main`), since the
   legs clone the new scripts and slices (`model-chain.py`, the render's classes, the application and
   orchestration slices). The push also carries `c60ad8d6`, so `staging-down` destroys as
   `awsds-deploy-staging` for the first time (Stage 8 verification xii). `awsds/app-etl`'s `main` is the
   v0.3.x template with MR !6's and MR !7's fixes (`ff4caf1c`), both already in `examples/app-etl/`.
   **Done 2026-10-24**: the mirror at `c714c47d`; the branch `data-release`, a patch over `ff4caf1c`
   checked to give `examples/app-etl/`'s tree `495b8953`, merged at 22:25 UTC as `edff65f9`.
3. **[user] The tag `v0.4.0`**. What it reads first: `test` with `--algorithm-repository`; `test-deploy`
   creating both workflows in the `test` project and running `app-etl`, whose Glue job now writes the
   table and the training sets under the project's prefix; then the Staging leg: the render of three
   workflows and the application slice's table and job arguments (`lint-plan` on its plan), the
   orchestration slice's two chains, `staging-test` (the governed read through Staging's share as
   `awsds-staging-job-exec`, the table read back, then Staging's first training job), `staging-model`
   (Staging's first batch transform), `staging-down` (gone once the mirror carries decision 27's
   legs; Staging's `egress/` is the user's, `make up ENV=staging ONLY=egress` before the tag and `make
   down ENV=staging` after the leg).
   **Run 2026-10-24, pipeline #74** (Stage 8's log): `test` passed, and `test-deploy` created both
   workflows and ran `app-etl` to `SUCCESS`, then failed its own read of the run: the job took the last
   *"ARN:"* line of the CLI's log, now app-etl-train's, for app-etl's run (*"Workflow run not found"*).
   The fix, MR !9 (`d1ee24cb`, the template's tree `8974b06d`), reads the ARN of the workflow the run line names and moves the
   `awsds-workflows` pin to `d856982c`; `v0.4.0` is spent. **`v0.4.1`, pipeline #77**: `test-deploy`
   passed, and Staging's leg read `curated.trades` through its share (30 rows), wrote the table and trained
   Staging's first model, then the train chain failed at `evaluate`, whose template indexed the training
   task's XCom and met it as JSON text (Stage 10's log); `staging-down` took Staging to zero as the deploy
   role. The fix, MR !10 (`863f30b1`, the template's tree `e8c12563`), and the data release is
   **`v0.4.2`**, pipeline #80.
4. **[user] The gate**, as §T step 4, after `make up ENV=production ONLY=workloads-egress`. **Done
   2026-10-25 at 00:54 UTC** on `v0.4.2`'s pipeline #80, after Staging's leg passed whole (both chains,
   Staging's first training job and batch transform).
5. **[pipeline] `production-deploy`**: the application slice with the table and the load job, the
   orchestration slice with three workflows and three chains, their schedules at 06:30, 07:00 and 07:30
   UTC. **Done 2026-10-25, 00:54 to 00:57 UTC**: *"2 added, 1 changed"* and *"20 added, 1 changed"*.
6. **[Claude⚡] Production's runs**, as `awsds-infra-prod`, each followed to its end: the app-etl chain,
   then the train chain (`aws stepfunctions start-execution --state-machine-arn
   arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-<chain>`); or the schedules, if
   the sitting spans their minutes. **Done 2026-10-25** (Stage 10's log): the app-etl chain 00:58 to
   01:17 UTC (the governed read, 30 rows), the train chain 01:18 to 01:25 (Production's first model).
7. **[user] The model's registration and approval**: `production-register`, then `production-approve`
   by a `deployment-managers` member, which `production-transform` follows; then Stage 10 5.5 from
   Sandbox as the persona, `DescribeModelPackage` answering and `UpdateModelPackage` refused. **Done
   2026-10-25**: version 1 registered and approved by `awsds-deploy-prod` (01:28, 01:29 UTC), 5.3's rule
   firing, Production's transform from the approved package (30 predictions), 5.5 read by the user.
8. **[user + Claude⚡] The warehouse** (9.4 to 9.7): `make up ENV=production
   ONLY=workloads-egress,warehouse-compute GROUPS=redshift`; `production-warehouse-ddl`; the warehouse
   chain started as in step 6; 9.6's readings (the job's log: the database user and the count;
   verification xxv in `pg_user`); §W step 5's datashare, the table now existing, and 9.7 from a Sandbox
   project with Sandbox's `warehouse-compute/` up. **Done 2026-10-25** (Stage 9's log), after four grants
   the plan had not named: the deploy role's Data API follow-up (`FollowItsOwnStatements`), the job
   group's 5439 egress, and for 9.7 the access role's catalog read and Lake Formation grant and `TEMP` on
   `sandbox` (`redshift-connection.md` §G); 9.7 read 30 rows, and again with Production's workgroup gone.
9. **[user] Verification ix**: a tag `v0.4.3` from a branch whose `GOVERNED_COLUMNS` names a column
   `curated.trades` lacks (`book`), expected to pass `test` and fail `staging-test` at the governed read,
   Production untouched; the branch deleted after, `main` unchanged. The unit tests mock the governed
   table with the list's columns and compare the query it builds (`tests/test_glue_script.py`'s `SCHEMA`
   and expected queries), so the branch moves them with the list, as a developer would; the list alone
   fails `test` first and leaves the leg's gate unmeasured. The patch, read 2026-10-24: ruff clean and
   27 tests passing. **Done 2026-10-25 on `v0.4.5`** (pipeline #87, the branch `ix-governed-drift-2`, on
   decision 27's legs): `staging-test` failed at *"lake.curated.trades lacks book"*, Production untouched;
   `v0.4.3` was cancelled before decision 27's legs, and `v0.4.4`, tagged on `main` without the drift,
   read `staging-check`'s negative and positive. The two branches' delete is the user's.
10. **[user + pipeline] Stage 10 6.1**: the schedules fire with `workloads-egress/` up, or the cron moves
    into the sitting by a commit, the mirror pushed and `production-deploy` retried; the pause lever
    through the slice; 3.2's deliberate break; 6.3's sentence before the first `make down ENV=production`.
    **Done 2026-10-25** with the endpoints up: the app-etl chain at 06:30:17 and the train chain at 07:00:36,
    started by `scheduler.amazonaws.com`, both `SUCCEEDED`, each run `ON_DEMAND`; the warehouse schedule,
    `DISABLED` through the slice at 01:15:54, silent at 07:30. Between sittings a run fails on the absent
    endpoints, so the app-etl and train schedules went `DISABLED` through the slice at 14:39 (the user's
    decision, with `orchestration-v0.2.1`): a sitting that wants the scheduled runs raises `workloads-egress/`
    and turns them on by a commit. 3.2's break waits for the user's decision (§N.0).
11. **[user] 3.7 again**: both `release.tf`s with `v0.4.2`'s tag, digest, SHA256 and `VersionId`s, the
    orchestration slices' three workflows among them; the mirror pushed. **Done 2026-10-25** in PR #255
    (Production's two slices planned `No changes` by hand), the mirror at `79651026`.
12. **[Claude]** §R, `./aws/warehouse.py awsds-infra-prod --sql` and `./aws/orchestration.py` (`OR-9` on
    three chains), then `make down ENV=production ONLY=workloads-egress,warehouse-compute`. **Done
    2026-10-25**: the user's downs of Staging, Sandbox, GitLab, the hub and, after the train chain,
    `workloads-egress/`; at 07:14 `./aws/egress.py` read 0 interface endpoints, 0 NAT and 0.000 USD/h in
    Production, Staging and Sandbox, `make status` 0.0000 USD/h with the application and orchestration slices up, and
    `orchestration.py` passed every Production check, `OR-9` on the three chains. `warehouse.py` ran without
    `--sql`: both workgroups were gone, so its database readings wait for the next warehouse sitting (§N.2);
    `EXC-13`'s database half was read from the day's Data API sessions instead (Stage 9's log).
    Staging's `make down` met Lake Formation's refusal of the application table's delete, fixed by
    `app_outputs`' infrastructure grant (Stage 9's log).

## N. The next release: what Stages 8, 9 and 10 leave

Each stage file's status cell ends with what is left on 2026-10-25; this section orders it by the sitting
that runs it. Written 2026-10-25 with the environment down. N.1 needs the hub, GitLab and the three
runners, then Staging's and Production's endpoints; N.2 the warehouses' compute; N.3 a Sandbox space;
N.4's exercises each wait for the user's word; N.5 waits on something no sitting provides. Every command
runs as the infrastructure user (`InfrastructureAccess`, the `awsds-infra-*` profile of the account it
names) unless it names the Data Scientist User or a pipeline job, and every `make up ENV=production`
carries `ONLY=`, or the build runner is destroyed.

### N.0 The steps that need nothing up

1. **[user] Stage 10 3.2, decided before the tag**: (a) recorded as answered by `v0.4.1`'s unplanted
   failure (verification vi: both failure rules fired, the diagnosis from the APIs alone); (b) recorded
   from `v0.4.5`'s planted drift (pipeline #87), if step 2 reads its rules firing; or (c) a deliberate
   break through a branch's tag, as verification ix's was, after N.1's release: a wrong job argument is
   3.2's own example, and one naming a Glue job the application slice does not declare would also answer
   Stage 10 xx's second half.
2. **[Claude] #87's failure rules**, for (b): the slice went with `make down ENV=staging` at 06:30 UTC,
   and its metrics stayed; `AWS/SNS` `NumberOfNotificationsDelivered` on `TopicName=awsds-staging-alerts`
   is read over the same window beside them:

   ```bash
   for rule in awsds-staging-wf-app-etl-failed awsds-staging-chain-app-etl-failed; do aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name TriggeredRules --dimensions Name=RuleName,Value=$rule --start-time 2026-10-25T05:55:00Z --end-time 2026-10-25T06:15:00Z --period 60 --statistics Sum --profile awsds-infra-staging --region us-west-2; done
   ```

   **Read 2026-10-25** (Stage 10's log): each rule `Sum` 1, at 06:03 and 06:04 UTC, and two notifications
   delivered in the same minutes; (b) has its reading, 3.7's proof with it. **Taken 2026-10-25, (b)**, the
   user's decision as recommended: 3.2 and 3.7 closed on #87's reading; the undeclared-job break stays an N.4
   exercise for Stage 10 xx.

3. **[Claude] Stage 9 xii's call**, written where a Staging deploy session runs, the user choosing where:
   `scripts/model-chain.py transform staging` reading Production's newest approved version before it
   serves Staging's own model, which reaches the runner with the mirror's push (N.1 step 4), or a manual
   job beside `staging-model` in the template, which rides N.1 step 5's merge request. Either runs
   `describe-model-package` and `list-model-packages` on `awsds-prod-model-app-etl` as
   `awsds-deploy-staging`, whose trust names the deploy runner's role alone (Stage 8 4.1). **Written
   2026-10-25** in `scripts/model-chain.py transform staging`: before Staging's own model is served, the
   newest approved version of Production's group is listed and described, an empty group reported and a
   refusal failing the job; the group ARN comes from `staging/foundation/`'s new output
   `registry_model_package_group_arn_prefix`, applied with the alerts var-file on 2026-10-25 (*0 added, 0
   changed*, the output written), and the script reaches the runner with the mirror's push (N.1 step 4).
4. **[Claude] Stage 8 xiv at `awsds-workflows` `d856982c` and Stage 10 xi's offline half**: the 40
   deliberate violations of 2026-10-18 run again against scratch copies of `examples/app-etl/`; the lint
   on a portal-scoped definition, on a container named by anything but an ECR URI and digest and on a
   definition over 50 KB; and `build-task-code`'s import line on a package whose module imports what the
   zip lacks. Each is expected to fail with exit 1. **Done 2026-10-25** (Stage 8's and Stage 10's logs):
   the 40 reproduced at `d856982c` and the rules since refused, 61 refusals, every control passing; xi's
   four offline readings taken, its CI half N.1 step 5's.
5. **[Claude] Stage 9 9.5's Terraform adoption**: import blocks for the share's authorization
   (Production), the consumer association, the registration and the federated database (Data
   Governance), written and planned; an object is adopted only where its plan after the import reads
   `No changes`, 9.5's three mismatches read first. **[Claude⚡]** the applies, on the user's word.
   **Written and planned 2026-10-25** (Stage 9's log): the authorization in
   `production/warehouse/datashare.tf` reads *1 to import* and no change, once `allow_writes` was left
   undeclared; the association and the federated database in `data-governance/data/warehouse-share.tf`
   read *2 to import, 1 to change*, the change the provider's five default tags on the database. The
   registration and the two LF-Tag assignments stay by hand, neither resource importable. **Applied
   2026-10-25**, 17:25 to 17:26 UTC, on the user's authorization: *1 imported* and *2 imported, 1 changed*,
   each re-planned `No changes`, the import blocks removed after (Stage 9's log).
6. **[user] Stage 9 5.4's read deny**, as the Data Scientist User through `awsds-scientist-prod`, the
   script in place since 2026-10-23; expected refused on `s3:GetObject` *"with an explicit deny in a
   resource-based policy"*, `DenyThePersonaReadsOutsideTheNamedPrefixes`. **Done 2026-10-25** (Stage 9's log),
   the wording as expected:

   ```bash
   aws s3api get-object --bucket awsds-prod-outputs --key applications/stage-09-proofs/v0/glue/producer_proof.py /dev/null --profile awsds-scientist-prod --region us-west-2
   ```

7. **[user] Stage 8 xxi's attempt half**, the waiting list's row: a test object written and deleted in
   `awsds-prod-releases` as `awsds-infra-prod`, beside the refusals xxi names.
8. **[Claude] Stage 9 rows i and iii**, filled from 2.2's and 2.4's readings in Stage 9's log. **Done
   2026-10-25.**

### N.1 The release through Staging and Production

`make hub-up`, then `make gitlab-up BUILD=1` and the tunnel ([`gitlab.md`](gitlab.md) §U). Sandbox's
`egress/` stays down until step 6 has read its negative.

1. **[user] Stage 8 1.1, the house image `default-v0.9.0`** (§H step 3), its 72-name literal passing `GM-1`
   to `GM-8` on 2026-10-25 at 07:41 UTC; `DE-5` turns green with it.
2. **[user] The deploy image on Terraform 1.16.6** (§H step 4), the laptop on it since 2026-10-25: **before steps 8
   and 10, and before any laptop apply or `make up` of a slice the pipeline reads or applies** (the application
   and orchestration slices, `staging/egress`, `production/workloads-egress`, and the `data/`, `sagemaker/`,
   `foundation/` and `workloads/` states their `terraform_remote_state` reads), since the image's 1.15.8 refuses
   a state written by 1.16.6.
3. **[Claude] Readings with GitLab up**: `./aws/cicd.py` (`CI-1`, `CI-9`); `awsds/app-etl`'s branch list,
   verification ix's branches deleted on 2026-10-25 by the user's word; and Stage 8 xxvii's plan half, a
   read-only plan of `production/runners/` once the Amazon Linux parameter has moved past the runners'
   image, expected `No changes` (decision 25 (b)):

   ```bash
   aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --query Parameter.Value --output text --profile awsds-infra-prod --region us-west-2
   ```

   ```bash
   ./scripts/gen-backend-hcl.py production runners && ./scripts/gen-tfvars.py production runners && AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/runners init -backend-config=backend.hcl -input=false && TF_VAR_build_runner=true AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/runners plan -input=false
   ```

4. **[user] The mirror pushed at `main`** (`git push gitlab main` from the project folder) once `main`
   carries `orchestration-v0.2.1` and the paused schedules: read at `79651026` on 2026-10-25, the mirror
   holds `production/orchestration/` on `orchestration-v0.2.0` with the app-etl and train schedules
   `ENABLED`, which `production-deploy` would apply over the pause.
5. **[user] The template's merge request on `awsds/app-etl`** (`EXC-22`, Stage 10 xxviii), from
   `examples/app-etl/` at `main` once `workflows/app-etl.yaml` there carries
   `ProcessingOutputConfig.KmsKeyId: "{env.PROJECT_KEY_ARN}"`, by `gitlab.md`'s "The application
   template" procedure. In the same sitting, Stage 10 xi's CI half: a branch carrying N.0 step 4's
   portal-scoped definition, its branch pipeline's `test` expected red, the branch deleted after.
6. **[user] The tag**, `v0.4.6` unless `git ls-remote --tags` on `awsds/app-etl` reads it spent, with
   Sandbox's `egress/` down: Stage 8 xxiv, `test-deploy` expected to fail in seconds before `deploy`
   writes anything, *"FATAL: no sagemaker.api endpoint: is Sandbox's egress up (make up ENV=sandbox
   ONLY=egress)?"*; then `make up ENV=sandbox ONLY=egress` and the job's retry.
7. **[Claude] After `test-deploy`** (**xix, xxiii's second half and Stage 8 iv's re-scan half read 2026-10-25 with nothing up**, on the
   `test` project's workflows of #87 and on `v0.4.5`'s image, the two stages' logs): Stage 10 xix, the domain's lineage events, twice with a delay between
   (Lesson 62); Stage 10 xxiii's second half, the `test` project's workflows' `Code` object (`aws
   mwaa-serverless get-workflow`) against the bundle's `code/<workflow>.zip`; and Stage 8 iv's re-scan
   half, **[Claude⚡]** on the user's word, `aws ecr start-image-scan` on the tag's image in
   `awsds-prod-ecr-app-etl`, scanned on push minutes before, expected refused rather than absorbed:

   ```bash
   aws datazone list-lineage-events --domain-identifier <the CI/CD variable DOMAIN_ID> --profile awsds-infra-sandbox-1 --region us-west-2
   ```

   ```bash
   aws mwaa-serverless get-workflow --workflow-arn <the test project's workflow ARN, test-deploy's log> --profile awsds-infra-sandbox-1 --region us-west-2
   ```

   ```bash
   aws ecr start-image-scan --repository-name awsds-prod-ecr-app-etl --image-id imageTag=<the tag>-<its short sha, build-image's log> --profile awsds-infra-prod --region us-west-2
   ```

8. **[user] `make up ENV=staging ONLY=egress`**, then `staging-gate` (decision 28). **[pipeline]**
   `staging-check`, `staging-deploy`, `staging-test` and `staging-model`, which carries Stage 9 xii's
   call if N.0 step 3 put it there.
9. **[Claude] Staging's readings**: Stage 10 ix's Staging half, `OR-3` in `./aws/orchestration.py` with
   the slice up; `EXC-22`'s Staging half, the processing output under the key of `aws kms describe-key
   --key-id alias/awsds-staging-data` and no longer `aws/s3`; and Stage 9 xii, the call in the job's
   trace and as `DescribeModelPackage` in Production's trail from Staging's account, under
   `awsds-deploy-staging`'s principal id:

   ```bash
   aws s3api head-object --bucket awsds-staging-outputs --key app-etl/work/job/trades.summary.json --query '[LastModified,ServerSideEncryption,SSEKMSKeyId]' --profile awsds-infra-staging --region us-west-2
   ```

10. **[user] `make up ENV=production ONLY=workloads-egress`**, then `production-gate`. **[pipeline]**
    `production-deploy`: the application and orchestration slices on the new tag, the three schedules
    staying `DISABLED` as the slice declares them.
11. **[Claude⚡] Production's app-etl chain**, on the user's word, followed to its end; then `EXC-22`'s
    Production half, the processing output under `alias/awsds-prod-data`'s key, which closes the row with
    step 9's:

    ```bash
    aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl" --profile awsds-infra-prod --region us-west-2
    ```

    ```bash
    aws s3api head-object --bucket awsds-prod-outputs --key app-etl/work/job/trades.summary.json --query '[LastModified,ServerSideEncryption,SSEKMSKeyId]' --profile awsds-infra-prod --region us-west-2
    ```

12. **[user decides] Stage 10 3.5's substitution**: a commit turns the app-etl schedule on
    (`schedule_enabled = true` in `production/orchestration/main.tf`), its cron moved into the sitting
    or kept at 06:30 UTC with `workloads-egress/` up across it, applied by **[Claude⚡]** (Recipe A) or by
    the next `production-deploy` once the mirror carries it. **[Claude]** at the firing, the execution's
    input: a timestamp says the Scheduler substitutes the placeholder, the literal
    `<aws.scheduler.scheduled-time>` says it does not. A commit turns the schedule `DISABLED` again before
    the sitting ends, since between sittings a run fails on the absent endpoints:

    ```bash
    aws stepfunctions list-executions --state-machine-arn "arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl" --max-results 1 --query 'executions[0].executionArn' --output text --profile awsds-infra-prod --region us-west-2
    ```

    ```bash
    aws stepfunctions describe-execution --execution-arn <the execution's ARN> --query input --output text --profile awsds-infra-prod --region us-west-2
    ```

13. **[user] 3.7**: both `release.tf`s with the new tag's values, the mirror pushed after the merge.
14. **Not owed: N.0 step 1 took (b).** Run only as N.4's exercise for Stage 10 xx: the break's branch and its tag, expected to stop in Staging's leg with
    Production untouched; **[Claude]** the failure rules' `TriggeredRules` and the diagnosis from
    `list-task-instances`, `get-task-instance` and the task's log group, read before any `make down
    ENV=staging`; the branch deleted after.
15. **[Claude]** §R, `./aws/orchestration.py` and `./aws/cicd.py`; **[user]** `make down ENV=staging`,
    the first after a release since `app_outputs`' infrastructure grant and so its measurement, then
    `make down ENV=production ONLY=workloads-egress`, `make down ENV=sandbox`, `make gitlab-down` and
    `make hub-down`.

### N.2 The warehouses

Separable from N.1, with the hub up. Each workgroup bills 1.44 USD per query-hour at 4 RPU and nothing
idle, so its `make down` is the guarantee.

1. **[user] The free trial's Production balance**, read in the Redshift console (Stage 9's cost row, 5b
   decision 9), 299.71 of 300.00 on 2026-10-25, the window open since the namespace's creation on 2026-10-23 and
   closing 2027-01-21 (Stage 9's log); then `make up
   ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift`.
2. **[Claude] Stage 9 xviii's last clause**, expected `DISABLED`, then `./aws/warehouse.py
   awsds-infra-prod --sql` (`WH-6`, `WH-12`, `WH-14`):

   ```bash
   aws redshift-serverless get-workgroup --workgroup-name awsds-prod-warehouse --query 'workgroup.pricePerformanceTarget' --profile awsds-infra-prod --region us-west-2
   ```

3. **[user] Stage 9 5.4's Data API negative** (verification vii's third), as the Data Scientist User;
   expected refused naming `DenyMintingARedshiftDatabaseSession`, where the absent workgroup answered
   first on 2026-10-23:

   ```bash
   aws redshift-data execute-statement --workgroup-name awsds-prod-warehouse --database warehouse --sql 'select 1' --profile awsds-scientist-prod --region us-west-2
   ```

4. **[user] `make down ENV=production ONLY=workloads-egress,warehouse-compute`**, then `make up
   ENV=sandbox ONLY=warehouse-compute`.
5. **[user] Stage 9 9.7 again**, from `eighth-experimentation`'s Query editor, the project role's Lake
   Formation grant revoked on 2026-10-25 and Production's workgroup down; 30 rows say the access role's
   grant alone serves the door:

   ```sql
   SELECT current_user, count(*), min(trade_date), max(trade_date) FROM governed_trades.trades.trades_notional;
   ```

6. **[Claude] `./aws/warehouse.py awsds-infra-sandbox-1 --sql`**, the instrument's own `EXC-13` reading
   in Sandbox, whose database half was read from the Data API's password sessions of 2026-10-25 (Stage
   9's log).
7. **[user] `make down ENV=sandbox ONLY=warehouse-compute`**; **[Claude]** §R and `./aws/warehouse.py` on
   both profiles; **[user]** the free trial's balance again, once the sitting's last half-hour interval
   has landed (Stage 9's Validation, `ComputeSeconds`).

### N.3 The proofs from a Sandbox space

`make hub-up`, `make up ENV=sandbox`, a space on the house image (version 10 once N.1 step 1 has run).

1. **[user] Stage 9 3.4's project-role half** (verification v): 3.4's two commands from the space's
   terminal with no `--profile`, so the project role answers: the group read answers, the write is
   refused with the group policy's wording.
2. **[user] Stage 9 8.1's space half**: the project's query editor answering `SELECT count(*) FROM
   curated.trades` and refusing an `INSERT` with Lake Formation's wording. First: 6f decision 1. The
   project role holds no Lake Formation grant on the lake, Sandbox's tag re-grants naming the Data
   Scientist User's set (Stage 9's log, 2026-10-25), so the `SELECT` reads a refusal until it holds one,
   as 6g 2.4's read does.
3. **[user] Stage 10 2.1**, pass 1's `deploy --targets dev` from the space as the project role (Stage 8
   decision 22), and 2.1's reads.
4. **[user] Stage 10 xxix's second half**: the `test` project's app-etl workflow started from the portal
   with no `OverrideParameters`; **[Claude]** the run's state and its first task's log.

### N.4 The deliberate exercises, each the user's decision

Each costs minutes of a sitting and leaves a recorded reading; none holds up another.

| Exercise | Sitting | The act | The reading |
|---|---|---|---|
| Stage 8 xv | N.1 | the proxy host stopped alone, a `.promotion` job retried, the proxy started again | the job's own check failing in about 20 s, *"no answer through the proxy"* |
| Stage 8 xxviii's active half | N.1 | an `AssumeRole` of a deploy role through `sts.amazonaws.com`: a manual job on the deploy runner, or xvi's 15 s trust widening | `us-east-1`'s trail and, for the widened principal, whether the misuse rule fires; a regional assumption beside it reads 4.6's transformed message |
| Stage 9 xxiv | N.2 | `REVOKE USAGE ON DATASHARE trades_lf FROM ACCOUNT '<Data Governance>' VIA DATA CATALOG`, then 9.5's steps 1 to 3 again | the Lake Formation rows the revoke leaves, and whether the register notices; INT-24's door is shut until the rebuild |
| Stage 10 xx's second half | N.1, Staging | a branch's tag whose `GlueJobOperator` names a Glue job the application slice does not declare | the task failing on `CreateJob` rather than creating a job, the two failure rules firing once more |
| Stage 10's network negative (1.2) | N.1, Staging | **[Claude⚡]** a workflow created by hand with no `NetworkConfiguration`, run once and deleted | the worker's address in the CloudTrail record of its first AWS call, beside a configured run's private address |

### N.5 The items that wait on something else

- **A second application**: Stage 10's chain order and xxv (decision 18); the split of
  `staging/orchestration/` per application (Stage 8 decision 27).
- **A `monitoring` endpoint** as the positive control: Stage 10 xvi's metrics clause.
- **S3 data events** (Stage 11): Stage 8 xx's writing identity.
- **A release that removes a file**: Stage 8 xxvi. **A workflow's 50th version**: Stage 8 xxiii.
- **A blueprint reconciliation**: Stage 8 vii's third half, read in Sandbox's trail (`UpdateDomain`,
  `UpdateStack`) at any sitting.
- **A date**: `EXC-13`'s Production half, after the secret's first rotation, due by 2026-11-22.
- **No step provokes them yet**: Stage 8 xxvii's retry (an apply that creates a role and its host
  together); Stage 9 vi's cancel (no table past 10 GB), ix's `VPC-Workloads` branch and off-endpoint
  refusal, xv's deploy- and execution-role halves and xxvii's cancel (no statement past 300 s); Stage 10
  xviii and xxviii's inbox marker (no task writes one).
- **Not written**: Stage 8 3.3's read pinned to an Iceberg snapshot (Stage 9 4.4).
- **Taken 2026-10-25**: Production's full-table flag turned off by the user in the console, bracketed by
  `DT-5` (Stage 9 decision 13; `TM-26`'s Production half closed, the lake's flag sufficing).

## Q. After the quotas: Stage 10's pass 3

The quotas are above zero since 2026-10-24 (§0.2), and pass 3 is the data release's (§V steps 3, 6 and 7).

## R. The readings at the end of every sitting

```bash
./aws/egress.py awsds-infra-prod awsds-infra-staging awsds-infra-sandbox-1
```

Zero burn in every account the sitting raised, no interface endpoint left, no NAT gateway anywhere;
then the stage's own instrument (`cicd.py`, `deploytargets.py`, `orchestration.py`, `datalake.py`,
`warehouse.py` after §W), `make status`, and the log entry of each step, in the sitting it ran.
