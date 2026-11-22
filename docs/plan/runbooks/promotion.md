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

**Where it stands, 2026-11-20**: §0, §H, §P, §T, §W and §V done; of §N, N.0 to N.3 ran 2026-10-25/26,
release T's sitting (N.8.2, `v0.4.7`, pipeline #117) on 2026-11-15 and release F's (N.8.4, `v0.5.2`,
pipeline #129) on 2026-11-16, its step 10, Stage 19 item 31, applied on 2026-11-17. What is left is §N.6's
order: five Sandbox days (N.9's three and N.10's two) and two release sittings (N.11), R1 carrying release
G (N.8.5, `v0.6.0`) and N.8.3, R2 the first releases of `app-ml`, `app-genai` and, unless R1 took it,
`app-dbt`; the steps that need nothing up run first.

| § | Holds |
|---|---|
| [§0](#0-before-any-sitting-with-the-environment-down) | what runs today, with nothing up: the persona proofs, the quota requests, the flag of decision 13, the deploy roles' grant (§0.5) |
| [§H](#h-the-hub-and-gitlab) | the hub and GitLab: the user's GitLab acts, the legs' merge request; its steps 3 and 4, the next house image and the deploy image, are §N's |
| [§P](#p-production-stage-9s-pass-3-and-stage-10s-05) | Production: the proof job's two runs, Stage 9's producer pair and pickup |
| [§T](#t-the-tag-stage-8s-pass-4-with-stage-10s-passes-1-and-2) | the tag: Stage 8's pass 4 with Stage 10's passes 1 and 2, and Stage 9's 8.5 |
| [§W](#w-the-governed-warehouse-stage-9s-pass-6) | the governed warehouse, Stage 9's pass 6: steps 1 to 4 done, step 5 run within §V |
| [§V](#v-the-data-release-v040) | the data release, the tag `v0.4.2` since `v0.4.0` and `v0.4.1` stopped in their legs: Stage 9's 8.5 and 9.4 to 9.7, Stage 10's pass 3 and 6.1, Stage 8's ix |
| [§N](#n-the-next-release-what-stages-8-9-and-10-leave) | what Stages 8, 9 and 10 leave, by sitting: the steps that need nothing up, the next release through Staging and Production (`EXC-22`, Stage 8 xxiv, Stage 9 xii, the Scheduler's placeholder), the warehouses, a Sandbox space, the deliberate exercises (xxiv on the adopted datashare in N.4a), what waits on something else, N.6, the order of what is left on 2026-11-20, N.9 and N.10, the Sandbox days, and N.11, the release sittings |
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
ARN, where it drops the volume key (`SUP-009`); the first real transform is `staging-model`'s.

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
3. **[user] The house image `default-v0.9.1`** with the 72-name `NO_PROXY` literal (Stage 8 1.1, Stage
   17 decision 4), registered as version 10. `default-v0.9.0` was spent 2026-10-25 at `pip-audit`, pipelines
   #89 to #91 on the lock of 2026-10-16, so first `gates-v0.5.0` with the 42 acceptances
   ([`gitlab.md`](gitlab.md) §G), then the merge request on `awsds/dev-env` from the copy under
   `gitlab/awsds/dev-env/` (the lock, the `include:` `ref`), the steward's tag, the release gate;
   `./scripts/gitlab-mirror.py` after the merge. `DE-5` turns green with it. **Done 2026-10-25**: pipeline
   #96, version 10 with alias `0.9.1`, `DE-5` passing at 22:11 UTC.
4. **[user] The deploy image on Terraform 1.16.6**, the laptop running it since 2026-10-25 and the two pins moved in
   `gitlab/awsds/deploy-image/Dockerfile` (`upstream-releases.md`): the merge request,
   the tag, its digest into `production/runners/variables.tf`, and the slice applied by `make gitlab-up
   BUILD=1`, which keeps the build runner; the flag left out destroys it. **Done 2026-10-25** as `v0.3.0`
   (N.1 step 2), the deploy runner replaced at 20:40:08 UTC; before it the image ran 1.15.8, which refuses a
   state 1.16.6 has written.
5. **[Claude]** `./aws/cicd.py` after the runners' boot (`CI-1`, `CI-9`), and `GM-1` to `GM-8` on the copies.

**Done 2026-10-24** (Stage 8's log): the environment raised by the user at 18:10 UTC, `cicd.py` 0
failed; steps 1, 2 and 6 by the user, read back at 18:47: the mirror at `0236a99d`, MR !4 merged and the
legs' MR !5 merged, `awsds/app-etl`'s `main` at `5a7d009a` identical to `examples/app-etl/` at
`0236a99d`. Steps 3 and 4 ran on 2026-10-25 as N.1 steps 1 and 2: version 10 by pipeline #96, the deploy
image `v0.3.0` on Terraform 1.16.6.
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
that runs it. Written 2026-10-25 with the environment down. N.1 (run 2026-10-25/26 on `v0.4.6`) needs the hub, GitLab and the three
runners, then Staging's and Production's endpoints; N.2 (run 2026-10-26) the warehouses' compute; N.3 a Sandbox space;
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
   changed*, the output written), and the script reaches the runner with the mirror's push (N.1 step 4). **Read 2026-10-25** at
   `v0.4.6`'s `staging-model` (pipeline #102): version 1 read `Approved` from Staging's deploy session, and
   Production's trail holds the `DescribeModelPackage` at 23:46:03 UTC under `awsds-deploy-staging`'s role
   id (Stage 9 xii).
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
   `awsds-prod-releases` as `awsds-infra-prod`, beside the refusals xxi names. **Done 2026-10-25** (Stage 8's log).
8. **[Claude] Stage 9 rows i and iii**, filled from 2.2's and 2.4's readings in Stage 9's log. **Done
   2026-10-25.**

### N.1 The release through Staging and Production

`make hub-up`, then `make gitlab-up BUILD=1` and the tunnel ([`gitlab.md`](gitlab.md) §U). Sandbox's
`egress/` stays down until step 6 has read its negative.

1. **[user] Stage 8 1.1, the house image `default-v0.9.1`** (§H step 3), its 72-name literal passing `GM-1`
   to `GM-8` on 2026-10-25 at 07:41 UTC, after `gates-v0.5.0`; `default-v0.9.0` was spent at `pip-audit` the
   same day. **Done 2026-10-25**: pipeline #96 registered version 10, `DE-5` passing.
2. **[user] The deploy image on Terraform 1.16.6** (§H step 4; **built 2026-10-25 as `v0.3.0`**, its digest
   pinned in `production/runners/variables.tf`, the runner's replacement by `make gitlab-up BUILD=1` once the
   pin is on `main`), the laptop on it since 2026-10-25: **before steps 8
   and 10, and before any laptop apply or `make up` of a slice the pipeline reads or applies** (the application
   and orchestration slices, `staging/egress`, `production/workloads-egress`, and the `data/`, `sagemaker/`,
   `foundation/` and `workloads/` states their `terraform_remote_state` reads), since the image's 1.15.8 refuses
   a state written by 1.16.6. **Done 2026-10-25**: the deploy runner replaced at 20:40:08 UTC by the user's
   `make gitlab-up BUILD=1` on the pinned digest (Stage 8's log). No pipeline job runs Terraform since
   release F: a leg reads its role's `state_read_keys` as JSON (`terraform-changes.md` §1).
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
   `ENABLED`, which `production-deploy` would apply over the pause. **Done 2026-10-25**: the mirror at
   `2d3160f1`, `origin`'s `main`, read at 22:45 UTC.
5. **[user] The template's merge request on `awsds/app-etl`** (`EXC-22`, Stage 10 xxviii), from
   `examples/app-etl/` at `main` once `workflows/app-etl.yaml` there carries
   `ProcessingOutputConfig.KmsKeyId: "{env.PROJECT_KEY_ARN}"`, by `gitlab.md`'s "The application
   template" procedure. In the same sitting, Stage 10 xi's CI half: a branch carrying N.0 step 4's
   portal-scoped definition, its branch pipeline's `test` expected red, the branch deleted after. **Done
   2026-10-25**: the merge request merged as `8d50f685` (pipelines #99 and #100 green); xi's branch
   `xi-portal-scoped`, pipeline #101's `test` red on the lint's `projeto` rule (Stage 10's log).
6. **[user] The tag**, `v0.4.6` unless `git ls-remote --tags` on `awsds/app-etl` reads it spent, with
   Sandbox's `egress/` down: Stage 8 xxiv, `test-deploy` expected to fail in seconds before `deploy`
   writes anything, *"FATAL: no sagemaker.api endpoint: is Sandbox's egress up (make up ENV=sandbox
   ONLY=egress)?"*; then `make up ENV=sandbox ONLY=egress` and the job's retry. **Done 2026-10-25**: `v0.4.6`'s pipeline
   #102; `test-deploy` failed at 22:51:36, 10 s after its start and before any write, with that wording
   (Stage 8 xxiv), Sandbox's `egress/` raised by the user and the job retried to `SUCCESS`.
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
   call if N.0 step 3 put it there. **Done 2026-10-25**: `staging-check` read the seven endpoints, both
   Staging chains `SUCCEEDED` (15 and 9 min), `staging-model` read Production's approved version 1.
9. **[Claude] Staging's readings** (**done 2026-10-25**: `OR-1` to `OR-9` passing with the slices up,
   `EXC-22`'s Staging half closed at 23:37 UTC, xii's call in Production's trail at 23:46:03): Stage 10 ix's Staging half, `OR-3` in `./aws/orchestration.py` with
   the slice up; `EXC-22`'s Staging half, the processing output under the key of `aws kms describe-key
   --key-id alias/awsds-staging-data` and no longer `aws/s3`; and Stage 9 xii, the call in the job's
   trace and as `DescribeModelPackage` in Production's trail from Staging's account, under
   `awsds-deploy-staging`'s principal id:

   ```bash
   aws s3api head-object --bucket awsds-staging-outputs --key app-etl/work/job/trades.summary.json --query '[LastModified,ServerSideEncryption,SSEKMSKeyId]' --profile awsds-infra-staging --region us-west-2
   ```

10. **[user] `make up ENV=production ONLY=workloads-egress`**, then `production-gate`. **[pipeline]**
    `production-deploy`: the application and orchestration slices on the new tag, the three schedules
    staying `DISABLED` as the slice declares them. **Done 2026-10-26**: the guard's negative at
    `production-gate` with the slice down (00:02:57 UTC), `production-deploy` on the retry at 00:09:05,
    *"0 to add, 2 to change"* on the application slice.
11. **[Claude⚡] Production's app-etl chain**, on the user's word, followed to its end; then `EXC-22`'s
    Production half, the processing output under `alias/awsds-prod-data`'s key, which closes the row with
    step 9's (**done 2026-10-26**: the chain `SUCCEEDED` at 00:25:52 UTC, `trades.summary.json` under the
    data key at 00:27:20, the row closed):

    ```bash
    aws stepfunctions start-execution --state-machine-arn "arn:aws:states:us-west-2:<Production>:stateMachine:awsds-prod-chain-app-etl" --profile awsds-infra-prod --region us-west-2
    ```

    ```bash
    aws s3api head-object --bucket awsds-prod-outputs --key app-etl/work/job/trades.summary.json --query '[LastModified,ServerSideEncryption,SSEKMSKeyId]' --profile awsds-infra-prod --region us-west-2
    ```

12. **[user decides] Stage 10 3.5's substitution** (**done 2026-10-26**: the user's decision in chat, the
    schedule on by a commit and an apply at 00:30 UTC with `cron(42 0 26 10 ? 2026)`, the firing's
    execution input `"scheduledTime":"2026-10-26T00:42:00Z"`, the schedule `DISABLED` again at 00:43:55;
    Stage 10's log): a commit turns the app-etl schedule on
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

13. **[user] 3.7**: the four `release.tf`s with the new tag's values, the two application slices' (the tag,
    the image digest, the bundle's SHA256) and the two orchestration slices' (the tag and each workflow's
    definition and code VersionIds, the legs' `*-release.auto.tfvars.json` artifacts), the mirror pushed
    after the merge. An orchestration slice applied by hand on a stale default rolls its workflows back
    to the recorded release (read 2026-10-26 at step 12: a plan of 4 changes until the default moved).
    **Written 2026-10-26** in PR #261, every slice planning `No changes`.
14. **Not owed: N.0 step 1 took (b).** Run only as N.4's exercise for Stage 10 xx: the break's branch and its tag, expected to stop in Staging's leg with
    Production untouched; **[Claude]** the failure rules' `TriggeredRules` and the diagnosis from
    `list-task-instances`, `get-task-instance` and the task's log group, read before any `make down
    ENV=staging`; the branch deleted after.
15. **[Claude]** §R, `./aws/orchestration.py` and `./aws/cicd.py`; **[user]** `make down ENV=staging`,
    the first after a release since `app_outputs`' infrastructure grant and so its measurement, then
    `make down ENV=production ONLY=workloads-egress`, `make down ENV=sandbox`, `make gitlab-down` and
    `make hub-down`. **Done 2026-10-26**: §R with 45 and 9 checks passing; Staging's `make down` clean at
    01:24 UTC, Sandbox's at 02:00, `make hub-down` at 02:44, 0 endpoints in Production, Staging and Sandbox (Stage 8's log).

### N.2 The warehouses

Separable from N.1, with the hub up. Each workgroup bills 1.44 USD per query-hour at 4 RPU and nothing
idle, so its `make down` is the guarantee. **Run 2026-10-26** (Stage 9's log): every step below but xxiv's
exercise, which the user deferred to a sitting of its own on N.4a's procedure; both computes down by 01:37
UTC, Production's balance 299.69.

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
5. **[user] Stage 9 9.7 again**, from `eighth-experimentation`'s Query editor with the database `sandbox`
   selected (the connection opens on `dev`, where the read is refused for want of `TEMP`), the project
   role's Lake Formation grant revoked on 2026-10-25 and Production's workgroup down; 30 rows say the access
   role's grant alone serves the door:

   ```sql
   SELECT current_user, count(*), min(trade_date), max(trade_date) FROM governed_trades.trades.trades_notional;
   ```

6. **[Claude] `./aws/warehouse.py awsds-infra-sandbox-1 --sql`**, the instrument's own `EXC-13` reading
   in Sandbox, whose database half was read from the Data API's password sessions of 2026-10-25 (Stage
   9's log).
7. **[user] `make down ENV=sandbox ONLY=warehouse-compute`**; **[Claude]** §R and `./aws/warehouse.py` on
   both profiles; **[user]** the free trial's balance again, once the sitting's last half-hour interval
   has closed (Stage 9's Validation, `ComputeSeconds`), and the next day. The reading at about 01:50 on
   2026-10-26 missed 0.03 that the next reading showed.

### N.3 The Sandbox sitting: the proofs from a space and INT-09's clone

What this sitting closes: Stage 7's INT-09 clone and push (verification xi) with INT-19's notebook
surface (x), Stage 9 3.4's project-role half (v), Stage 10 2.1 (the first `deploy --targets dev` from a
space) and xxix's second half (a portal run with no overrides). Stage 9 8.1's space half waits on 6f
decision 1 (step 9). The raises and the downs are the infrastructure user's (`felipenoris+infrastructure_user@…`,
`InfrastructureAccess`, the profiles `awsds-infra-prod` and `awsds-infra-sandbox-1`), from the project
folder; the portal, the space and GitLab are the Data Scientist User's, signed in through Identity Center
in one private window, since a sign-in answered in a browser holding another user's portal session ends
that session; every reading is Claude's, as the infrastructure user. While up, at `cost-model.md`'s rates:
the hub about 0.026 USD/h, GitLab and SharedServices' twelve endpoints 0.187, Sandbox's eighteen endpoints
0.180 and the space on `ml.t3.medium` 0.050, about 0.44 USD/h, plus the runs (cents) and AWS Config's
cycle charge (0.36 to 0.87 per Sandbox `[E]` cycle, 0.21 to 0.38 per GitLab cycle).

**Read 2026-10-26 with nothing up** (the stage logs):

- Both Sandbox projects are the Data Scientist User's (`PROJECT_OWNER`): `eighth-experimentation`, the
  manifest's `dev` (domain `d-p6gthxc82ckg`), and `test-experimentation`, its `test` (`d-lfgbdrjncmsu`).
  Each project's role is a contributor and carries `awsds-sandbox-workflows`, and each Tooling environment
  carries its `kmsKeyArn`, its two Glue network connections and its security group.
- `eighth-experimentation`'s space, `default-28f1…` (the persona's, private, `ml.t3.medium`), reads
  `awsds-sandbox-dev-env` version 10 as its default image since 2026-10-25 22:55 UTC; the `test`
  project's space runs AWS's SageMaker Distribution 4.5. No app runs in either domain.
- The `dev` project holds no `app-etl` workflow, so step 7 creates two; the `test` project holds
  `app_etl_test_experimentation_app_etl` and its `_train` twin, last updated by `v0.4.6`'s `test-deploy`.
- `ReadTheStatusFromSandbox` on `awsds-prod-model-app-etl` admits `datazone_usr_role_*` of Sandbox.
- Both VPCs' flow logs are on (`awsds-prod-shared-vpc-flow-logs`, `awsds-sandbox-vpc-flow-logs`), default
  format, 600 s aggregation; GitLab's host answers at `10.30.6.245` since 2026-11-10 (`10.30.39.111`
  before; a rebuild moves it, and `terraform output private_ip` in `production/tooling/` reads it), and
  Sandbox is `10.20.0.0/16`.
- The CI/CD CLI 1.0.9, read in its code: it refuses a manifest with any `${VAR}` unset or empty, the
  `test` stage's included (`find_missing_env_vars`), and writes each `{env.VAR}` as `{{ params.VAR }}`
  with no default, so a deploy embeds no value and only a run the CLI starts fills one.

1. **[user] The raises**, in this order:

   ```bash
   make hub-up
   ```

   ```bash
   make gitlab-up RUNNERS=0
   ```

   then the tunnel ([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md) §3.4), then:

   ```bash
   make up ENV=sandbox ONLY=egress GROUPS=mwaa
   ```

   `ONLY=egress` because a plain `make up ENV=sandbox` also raises `probes/`, which this sitting does not
   use; `GROUPS=mwaa` for step 7's MWAA Serverless endpoint (`vpc-egress-v0.19.0`), and no
   other group, since no step calls Bedrock or MLflow. **[Claude]** the other sessions
   on the laptop told before the first raise; after the last, `./aws/egress.py awsds-infra-prod
   awsds-infra-sandbox-1` (SharedServices' twelve endpoints, Sandbox's eighteen), `./aws/devenv.py`
   (`DE-3` and `DE-5` with the session up) and `make status`. **Run 2026-10-26** (Stage 7's log): the hub
   and GitLab started at 04:25 to 04:27 UTC, Sandbox's egress raised without the group (added at step 7),
   30 endpoints and 0.300 USD/h, `DE-1` to `DE-6` passing; the tunnel read *Disconnected* on this laptop
   until the user connected `mbp-split-tunnel` at 04:40.

2. **[user] The persona's token in GitLab**: in the private window, through the tunnel,
   `https://gitlab.awsds.internal` → *Sign in with SAML* as the Data Scientist User; *Edit profile →
   Access tokens → Add new token*: the name `int-09`, the expiry tomorrow, the scopes `read_repository`
   and `write_repository`. GitLab shows the token once; it is typed at step 5's prompt and nowhere else,
   never into chat or a file. The same pages give the username the clone asks for, and `awsds/app-etl`
   lists the persona as Developer through `awsds/data-scientists` (Stage 8 2.1).

3. **[user] The space**: in the same private window, the portal, `eighth-experimentation` → *Compute →
   Spaces*: the JupyterLab space's image `awsds-sandbox-dev-env` version 10 (alias `0.9.1`) on
   `ml.t3.medium`, confirmed in its settings before *Start*; then *Open* and a terminal (*File → New →
   Terminal*). The space bills from its start.

4. **[user] INT-19's notebook surface** (Stage 7 x): the image's own trust, read as the release smoke test
   reads it (`gitlab/awsds/dev-env/smoke/Dockerfile`), in the terminal:

   ```bash
   G=https://gitlab.awsds.internal
   curl -sS -o /dev/null -w '%{http_code} ssl_verify=%{ssl_verify_result}\n' "$G/users/sign_in"
   GIT_TERMINAL_PROMPT=0 git ls-remote "$G/awsds/app-etl.git"
   for py in /opt/conda/bin/python "$AWSDS_PYTHON_ENV/bin/python"; do "$py" -c "import sys, urllib.request, requests; u = sys.argv[1]; print(sys.executable, urllib.request.urlopen(u, timeout=20).status, requests.get(u, timeout=20).status_code)" "$G/users/sign_in"; done
   ```

   and in a notebook cell on the house kernel (`$AWSDS_PYTHON_ENV`, `/opt/awsds/venv`), the surface the verification
   names:

   ```python
   import requests; requests.get("https://gitlab.awsds.internal/users/sign_in", timeout=20).status_code
   ```

   Expected: `200 ssl_verify=0`; the `ls-remote` stopped at the authentication wall, never at a
   certificate; `200 200` from both Pythons and `200` from the cell. **Read 2026-10-26**: as expected, the
   wall reading *"HTTP Basic: Access denied"* after an AWS credential helper's error (step 5). A certificate error is INT-19's
   failure, the image's trust; a timeout is the network's (the peering, GitLab's group on 443, `NO_PROXY`).
   **Read 2026-10-26** (Stage 7 x): `200 ssl_verify=0`, the wall, `200 200` twice, the cell `200`.

5. **[user] INT-09's clone and push** (Stage 7 xi), the token at git's password prompt, kept in memory
   for an hour by git's cache helper and never on disk. The space's git configuration names an AWS
   credential helper for every host (`--ignore-host-check`, the CodeCommit helper's option; read
   2026-10-26): it errors, a credential GitLab refuses reaches the server, and git never prompts. The
   empty `credential.helper=` resets that list before the cache helper joins it:

   ```bash
   cd ~ && git -c credential.helper= -c credential.helper='cache --timeout=3600' clone https://gitlab.awsds.internal/awsds/app-etl.git
   ```

   ```bash
   cd ~/app-etl && git -c credential.helper= -c credential.helper='cache --timeout=3600' push -o ci.skip origin HEAD:refs/heads/int-09-probe
   ```

   ```bash
   git -c credential.helper= -c credential.helper='cache --timeout=3600' push origin --delete int-09-probe
   ```

   The push creates a branch on `main`'s commit, no new object, and `ci.skip` keeps GitLab from queueing
   a pipeline that no runner would take with `RUNNERS=0`. **[Claude]** the path, about 15 minutes after
   the clone (the logs aggregate over 600 s, and an early empty answer is no answer, Lesson 62). **Done
   2026-10-26** (Stage 7 xi): the clone at 05:04 UTC, the branch pushed and deleted, the flows from
   `10.20.56.248` accepted and the proxy log silent on GitLab. The reading's shape: accepted
   flows from a `10.20.x` address to GitLab's address on 443 (`10.30.39.111` that day) in SharedServices'
   log, the space's own address and no proxy between, since `NO_PROXY` names `.awsds.internal`:

   ```bash
   aws logs filter-log-events --log-group-name awsds-prod-shared-vpc-flow-logs --start-time <the clone's minute, epoch ms> --filter-pattern '[version, account, eni, srcaddr="10.20.*", dstaddr="<GitLab's address>", srcport, dstport="443", protocol, packets, bytes, start, end, action, status]' --profile awsds-infra-prod --region us-west-2
   ```

6. **[user] Stage 9 3.4's project-role half** (v), in the terminal with no `--profile`, so the project
   role answers. Production's account id is typed, never written into a file; on the laptop,
   `aws configure get sso_account_id --profile awsds-infra-prod` prints it:

   ```bash
   export PROD=<Production's account id>
   GROUP="arn:aws:sagemaker:us-west-2:${PROD}:model-package-group/awsds-prod-model-app-etl"
   aws sagemaker describe-model-package-group --model-package-group-name "$GROUP" --region us-west-2
   ```

   ```bash
   aws sagemaker create-model-package --model-package-group-name "$GROUP" --model-package-description probe --inference-specification "{\"Containers\":[{\"Image\":\"${PROD}.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-app-etl:v0.2.1\"}],\"SupportedContentTypes\":[\"text/csv\"],\"SupportedResponseMIMETypes\":[\"text/csv\"]}" --region us-west-2
   ```

   Expected: the read answers (the group `Completed`), and the write is refused, the wording recorded
   whichever layer answers first (Lesson 20); the persona's laptop half read *"because no resource-based
   policy allows the sagemaker:CreateModelPackage action"* on 2026-10-23. **[Claude]** both calls in
   Production's trail under `datazone_usr_role_avhvbqn37ty7m8_…`, the read with no error and the write's
   `errorMessage`. **Done 2026-10-26** (Stage 9 v): `DescribeModelPackageGroup` at 05:09:37 UTC in both
   trails, `CreateModelPackage` refused at 05:09:45 with the persona's wording, in Sandbox's trail alone, both
   through Sandbox's `sagemaker.api` endpoint.

7. **[user] Stage 10 2.1**, the first `deploy --targets dev` from a space, as the project role, in
   `~/app-etl` (step 5's clone, at `main`). The values the manifest reads ([`sagemaker-application.md`](sagemaker-application.md)
   §M): the project's own from its Tooling environment by the package's in-space script
   ([`serverless-workflows.md`](serverless-workflows.md) §T), the image from the release `v0.4.6`
   records (`production/app/app-etl/release.tf`), and placeholders for the four names neither the `dev`
   deploy nor `app-etl`'s run reads:

   ```bash
   git clone --depth 1 https://github.com/felipenoris/awsds-workflows /tmp/awsds-workflows
   /opt/conda/bin/python /tmp/awsds-workflows/scripts/space_values.py > /tmp/space_values.json
   eval "$(/opt/conda/bin/python -c 'import json; v = json.load(open("/tmp/space_values.json")); k = "arn:aws:kms:%s:%s:key/%s" % (v["REGION"], v["ACCOUNT_ID"], v["PROJECT_KEY_ID"]); print("\n".join("export %s=%s" % p for p in (("DOMAIN_ID", v["DOMAIN_ID"]), ("DOMAIN_REGION", v["REGION"]), ("SUBNET_AZ1", v["SUBNET_AZ1"]), ("SUBNET_AZ2", v["SUBNET_AZ2"]), ("DEV_PROJECT_SG", v["PROJECT_SG"]), ("DEV_PROJECT_KEY_ARN", k))))')"
   export DEV_PROJECT_NAME=eighth-experimentation TEST_PROJECT_NAME=test-experimentation
   export TEST_PROJECT_SG=unused-by-dev TEST_PROJECT_KEY_ARN=unused-by-dev TRAINING_IMAGE_URI=unused-by-app-etl
   export JOB_IMAGE_URI="${PROD}.dkr.ecr.us-west-2.amazonaws.com/awsds-prod-ecr-app-etl@sha256:ba8d41bf08bebee084b38e7df9b8efa28e6fcccaf9865e0591fdec7d0462f98d"
   ```

   The MWAA Serverless API's only name, `airflow-serverless.<region>.api.aws`, is refused by the compute
   plane's proxy, so the session needs the `mwaa` group's endpoint (step 1) and the name in its
   `NO_PROXY` until the house image carries it (`getent hosts` answers a `10.20.x` address):

   ```bash
   export NO_PROXY="$NO_PROXY,airflow-serverless.us-west-2.api.aws" no_proxy="$no_proxy,airflow-serverless.us-west-2.api.aws"
   ```

   Then the worker's packages, as `build-task-code` builds them, the deploy, and one run of `app-etl` (the
   train workflow trains on `ml.m5.large` and is not 2.1's). The CLI is the house image's, by its path:
   the SageMaker Distribution's own, 1.0.8, comes first on `PATH` and refuses the manifest's `code` field.
   The CLI 1.0.9 looks the domain up by name with `ListDomains`, which DataZone refuses to a project's role,
   so each command answers that lookup with the manifest's domain id, as the deploy role's `ListDomains`
   answers in the pipeline:

   ```bash
   for w in app-etl app-etl-train; do python3 -m zipfile -c "code/$w.zip" code/app_etl_tasks.py; done
   ```

   ```bash
   "$AWSDS_PYTHON_ENV/bin/python" -c 'import os, sys, smus_cicd.helpers.datazone as dz; dz.get_domain_id_by_name = lambda name, region: os.environ["DOMAIN_ID"]; from smus_cicd.cli import app; sys.argv[0] = "aws-smus-cicd-cli"; app()' deploy --manifest manifest.yaml --targets dev --skip-validation --no-events
   ```

   ```bash
   "$AWSDS_PYTHON_ENV/bin/python" -c 'import os, sys, smus_cicd.helpers.datazone as dz; dz.get_domain_id_by_name = lambda name, region: os.environ["DOMAIN_ID"]; from smus_cicd.cli import app; sys.argv[0] = "aws-smus-cicd-cli"; app()' run --manifest manifest.yaml --targets dev --workflow app-etl
   ```

   The deploy creates both workflows at their first of 50 versions; a line saying the network or the
   key was omitted would be the non-member's quiet failure (`sagemaker-application.md` §D), not expected
   for the project's own role. `run` prints the run id and returns. **[Claude]** 2.1's reads: both
   workflows `READY` under the project key, each definition object identical to the resolved
   `shared/app-etl/workflows/*.yaml`, the six tags, the `Code` object under `shared/operatorFiles/`
   against its zip, and the two log groups under `/aws/mwaa-serverless/`, with no retention; then the run
   to its end (`get-workflow-run`, `list-task-instances`): the Glue job `app-etl-avhvbqn37ty7m8` over the
   inbox the deploy synced, the processing job on the release's image, the report under
   `shared/app-etl/outbox/`. The run costs cents: two G.1X workers for minutes, about 15 minutes of
   `ml.t3.medium`, worker tasks at 0.088 USD per task-hour. **Done 2026-10-26** (Stage 10's log): the three
   findings above met in that order, the endpoint applied at 05:41:56 UTC; the deploy created both workflows
   at 05:54, and from 05:55:41 the run reached `SUCCESS` at 06:07:19 UTC (11 min 34 s), its four tasks `SUCCESS`: the Glue job `app-etl-avhvbqn37ty7m8` over the synced inbox (66 s, two G.1X workers), the processing job `app-etl-20261026T055826` on the release's image by digest (`ml.t3.medium`, network-isolated, 5 min 21 s), and the report under `shared/app-etl/outbox/` (10 rows, `notional` 49,850.5), both outputs under the project key.

8. **[user] Stage 10 xxix's second half**: in the portal, `test-experimentation`'s *Workflows* page,
   `app_etl_test_experimentation_app_etl` → *Run*, with no parameter, and nothing saved (a save replaces
   the CLI's definition whole, Lesson 60). **[Claude]** the run as the infrastructure user:
   `list-workflow-runs` (its `RunType`), `get-workflow-run`, `list-task-instances` and the first task's log
   in the workflow's `/aws/mwaa-serverless/` group. `transform` names `{{ params.SUBNET_AZ1 }}` in its
   connections, so the run is expected to stop there, at Airflow's template or at Glue's connection, with
   the wording the verification records; the processing task's image is a parameter too. A worker minute.
   **Done 2026-10-26**: run at 05:32:19 UTC, failed at 05:34:25 at the DAG's template, *"'dict object' has no
   attribute 'SUBNET_AZ1'"*, no task instance.

9. **[user] Stage 9 8.1's space half, only once 6f step 11's subscription is approved** (decision 1, taken
   2026-10-26 as (b), the pilot in PR #270): the project's query editor answering `SELECT count(*) FROM
   curated.trades` and refusing an `INSERT` with Lake Formation's wording. The project role holds no Lake
   Formation grant on the lake, Sandbox's tag re-grants naming the Data Scientist User's set (Stage 9's log,
   2026-10-25), so before the subscription the `SELECT` reads a refusal, as 6g 2.4's read does, and the step
   stays owed. **Done 2026-10-30 from the portal instead** (N.8.1 step 3, Stage 9's log): 30 rows read through
   the subscription, the `INSERT` refused by Lake Formation at the vend.

10. **The downs**: **[user]** the token revoked (*Access tokens → Revoke*) and `git credential-cache exit`
    in the terminal; every portal tab closed first, since an open project page starts the space's app
    again and an app the portal is starting refuses the hook's delete (Stage 9's log of 2026-10-26); then:

    ```bash
    make down ENV=sandbox
    ```

    which deletes the Studio apps before it destroys `egress/` (the space and its volume stay), then
    `make gitlab-down`, the tunnel down, `make hub-down`. **[Claude]** §R on the three profiles,
    `make status`, and each step's entry in its stage's log: Stage 7's for x and xi, Stage 9's for 3.4,
    Stage 10's for 2.1 and xxix. **Done 2026-10-26** (Stage 7's log): GitLab stopped at 06:11:15 UTC; the
    hook deleted the three apps at 06:10, and the open portal tabs started both projects' apps again at
    06:13; the first `make hub-down` left no `StopInstances` in the trail. With every tab closed the user
    ran both downs again: the proxy and the WireGuard host stopped at 06:20:48 to 06:20:51, the hook's
    `DeleteApp` refused eight times on the app still `PendingCheckout` until 06:25:04, both apps deleted at
    06:26:10 and 06:26:12; §R read no endpoint, no NAT and 0.000 USD/h in Production, Staging and Sandbox at 06:30, and
    `make status` 0.0000 USD/h.

### N.4 The deliberate exercises, each the user's decision

Each costs minutes of a sitting and leaves a recorded reading; none holds up another.

| Exercise | Sitting | The act | The reading |
|---|---|---|---|
| Stage 8 xv | N.8.2 step 12b, on `v0.4.7` or later | the proxy host stopped alone, `staging-check` retried, the proxy started again and the job retried | the job's own check failing in about 20 s, *"no answer through the proxy"*, which the template's check gives only since the fix of 2026-10-28 (12b) |
| Stage 8 xxviii's active half | N.1 | an `AssumeRole` of a deploy role through `sts.amazonaws.com`: a manual job on the deploy runner, or xvi's 15 s trust widening | `us-east-1`'s trail and, for the widened principal, whether the misuse rule fires; a regional assumption beside it reads 4.6's transformed message |
| Stage 9 xxiv | a warehouse sitting (N.2's raises, both computes) | N.4a: the revoke by SQL, the two adopted slices' plans read, the re-grant by SQL and their applies. **Done 2026-10-26** (Stage 9's log) | the Lake Formation rows the revoke leaves, whether the register notices, and what each adopted resource's plan reads; INT-24's door shut until the re-grant |
| Stage 10 xx's second half | N.8.2 step 12a, Staging | a branch's tag whose `GlueJobOperator` names a Glue job the application slice does not declare | the task failing on its `GetJob`, which the workflow's role is refused, before any `CreateJob`, no job created, the two failure rules firing once more |
| Stage 10's network negative (1.2) | N.1, Staging | **[Claude⚡]** a workflow created by hand with no `NetworkConfiguration`, run once and deleted. **Done 2026-10-26** (Stage 10's log) | the worker's address in the CloudTrail record of its first AWS call, beside a configured run's private address: `10.1.11.134` through `airflow-serverless.amazonaws.com` against `10.50.x` through `vpce-…` |

### N.4a Stage 9 xxiv on the adopted datashare: the producer-side revoke

**Run 2026-10-26** (Stage 9's log). The steps below are the measured procedure, for a second run or for a
revoke that happens by accident. The authorization (`production/warehouse/datashare.tf`), the association and
the federated database (`data-governance/data/warehouse-share.tf`) are Terraform's since 2026-10-25, so a
re-grant by command would leave both states drifted (Lesson 35). The registration and the two LF-Tag
assignments stay by hand (`AWS_STATE.md`'s registers). The question (Stage 9 xxiv): does a producer-side
revoke leave the Lake Formation rows behind, as AWS's page says (*"the associated permissions and objects in
Lake Formation are not automatically deleted"*), and does the register notice. It does leave them, and only
`WH-16`, written after the run, notices. `<ARN>` is the datashare's,
`arn:aws:redshift:us-west-2:<Production>:datashare:<namespace id>/trades_lf`. Each `[Claude⚡]` act is on the
user's word. The sitting is a warehouse sitting with the hub up, since a spoke's `make up` refuses while the
proxy is stopped and the downs need no hub: `make up ENV=production ONLY=workloads-egress,warehouse-compute
GROUPS=redshift` and `make up ENV=sandbox ONLY=warehouse-compute`, at 1.44 USD per query-hour per workgroup.
`data-governance/data/` is planned from a tree that carries every change applied to the slice (Lesson 79):
on 2026-10-26 `main` lacked the 6f pilot's applied seats and grants, and its plan reverted them.

1. **The before-reading**, kept for the diff:
   - **[user]** the free trial's Production balance in the Redshift console;
   - **[Claude]** as `awsds-infra-prod`: `aws redshift describe-data-shares --data-share-arn <ARN>`, the
     consumer `DataCatalog/<Data Governance>` `AUTHORIZED` and the lake's catalog ARN `ACTIVE`; through the
     Data API as the namespace's admin in `governed` (9.3's door), `SELECT * FROM svv_datashare_consumers;`;
     `./aws/warehouse.py awsds-infra-prod --sql`, `WH-16` passing and `WH-12` counting the `ds:` pair;
   - **[Claude]** as `awsds-infra-data`: the same `describe-data-shares`; `aws lakeformation describe-resource
     --resource-arn <ARN>` for the registration, which `list-resources` does not list; `aws glue get-database
     --name governed_trades` and `get-tables --database-name governed_trades`, the table
     `trades.trades_notional`; `aws lakeformation list-permissions` on the database and on that table, every
     `NextToken` followed; `get-resource-lf-tags` on both; `./aws/datalake.py awsds-infra-data`;
   - **[Claude]** as `awsds-infra-sandbox-1`: `list-permissions` on Data Governance's database and table, the
     access role's grants;
   - **[Claude]** the two slices planning `No changes`, `production/warehouse/` as `awsds-infra-prod` and
     `data-governance/data/` as `awsds-infra-data` (Recipe A, read-only);
   - **[user] the positive control**: 9.7's query from `eighth-experimentation`'s Query editor with the
     database **`sandbox`** selected, 30 rows. The project's connection opens the editor on `dev`, where the
     read is refused for want of `TEMP` (`redshift-connection.md` §G). The refusal after step 2 means
     something only beside this read.
2. **[Claude⚡] The revoke**, one statement through the Data API as the admin in `governed`: `REVOKE USAGE
   ON DATASHARE trades_lf FROM ACCOUNT '<Data Governance>' VIA DATA CATALOG;`, then `SELECT * FROM
   sys_datashare_change_log ORDER BY record_time DESC LIMIT 5;` for the revoke's row and
   `svv_datashare_consumers` for the consumer's absence.
3. **The readings after the revoke**:
   - **[Claude]** step 1's commands again. Measured 2026-10-26: `describe-data-shares` answers
     `InvalidDataShareFault` in both accounts; the federated table reads *"No glue catalog datashare is
     found"* and its LF-Tags *"Entity Not Found"*; the registration, the database, its grants and LF-Tag, and
     Sandbox's grants stay; `WH-16` fails and every other check passes;
   - **[user]** the same 9.7 query, `sandbox` selected. It is refused by Glue with that wording, which shuts
     INT-24's door.
4. **[Claude] The plans after the revoke**, read and never applied:
   - `production/warehouse/` reads *1 to add*, the authorization gone from the read;
   - `data-governance/data/` fails with *"Iteration over null value"* at `warehouse-share.tf`. The data
     source lists null when the account sees no share, so no plan of the lake's slice runs until step 5's two
     applies.
5. **[Claude⚡] The re-grant**, three acts in this order, each on the user's word:
   1. By SQL as the admin, `GRANT USAGE ON DATASHARE trades_lf TO ACCOUNT '<Data Governance>' VIA DATA
      CATALOG;`. The consumer comes back `PENDING_AUTHORIZATION`, and Data Governance does not see the share
      yet.
   2. `production/warehouse/`'s plan, *1 to add*, the authorization; its apply, then `No changes`. The
      consumer reads `AUTHORIZED`, and the share is `AVAILABLE` to Data Governance.
   3. `data-governance/data/`'s plan, *1 to add*, the association. Any line on another resource of the slice
      stops the step. Then its apply, and `No changes`. If the plan instead replaces the federated database,
      the new object owes Recipe D's read-back for `IAM_ALLOWED_PRINCIPALS`, the two LF-Tags by hand (9.5
      step 3) and `AWS_STATE.md`'s two registers. On 2026-10-26 the database survived and owed nothing.

   No `authorize-data-share` or `associate-data-share-consumer` by command: the states would drift.
6. **The restored read**:
   - **[user]** 9.7 again, `sandbox` selected, 30 rows; the first read after the re-grant took 26 s. Sandbox's
     consumer database `governed_trades` is re-created from the ARN only if its mapping broke (9.5 step 5);
   - **[Claude]** step 1's readings, `WH-16` passing, then `data-governance/data/README.md`'s rows read
     against what survived, and the log entry.
7. **The downs**:
   - **[user]** `make down ENV=production ONLY=workloads-egress,warehouse-compute`, and, with the Query editor
     closed, `make down ENV=sandbox ONLY=warehouse-compute`;
   - **[Claude]** §R;
   - **[user]** the free trial's balance, read after the last half-hour interval has closed and again the
     next day. A reading twenty minutes after the end of 2026-10-26's early sitting missed 0.03 that the next
     reading showed.

### N.5 The items that wait on something else

- **A second application**: Stage 10's chain order and xxv (decision 18). `<env>/chains/` takes it as an
  entry of its `applications` and `chains` maps; the split of `staging/orchestration/` per application
  (Stage 8 decision 27) retired with that slice (Stage 19 item 31). The first in the targets is Stage 17's
  `app-ml` (9.7), then `app-genai` (10.6); Stage 20's `app-dbt` follows under its decision 9 (b), taken
  2026-11-17: its pass 8 releases it through both targets. The three are written in `examples/` since 2026-11-17 and none is deployed. Neither of
  Stage 17's consumes another application's marker as written, so xxv stays open on them.
- **A `monitoring` endpoint** as the positive control: Stage 10 xvi's metrics clause.
- **S3 data events** (Stage 11): Stage 8 xx's writing identity.
- **A release that removes a file**: Stage 8 xxvi, which Stage 17 9.11's release of `app-etl` provokes in
  both deployment projects, `app-etl-train` leaving `workflows/`. **A workflow's 50th version**: Stage 8 xxiii, read
  2026-10-26 at 12 for the `test` project's `app-etl` and 6 for its `_train` twin. No release deploys
  to that project since Stage 19 decision 19 (c), so its count stands; the question passes to the `dev`
  project's workflows, a version per deploy from a space, and from release F to each deployment
  project's, a version per release.
- **A blueprint reconciliation**: Stage 8 vii's third half, read in Sandbox's trail (`UpdateDomain`,
  `UpdateStack`) at any sitting; read again 2026-10-26 with nothing up, none since 2026-10-11.
- **A date**: `EXC-13`'s Production half, after the secret's first rotation, due by 2026-11-22, read at the
  first warehouse sitting after it (the waiting list's Dates).
- **No step provokes them yet**: Stage 8 xxvii's retry (an apply that creates a role and its host
  together); Stage 9 vi's cancel (no table past 10 GB), ix's `VPC-Workloads` branch and off-endpoint
  refusal, xv's deploy- and execution-role halves and xxvii's cancel (no statement past 300 s); Stage 10
  xviii and xxviii's inbox marker (no task writes one).

### N.6 The order of what is left, read 2026-11-20

Read on 2026-11-18 against the stage files and their logs, with nothing up, after Stage 20's 8.4 applies
and the day's log review, whose pull requests are #320 (the records), #321 (the scripts taught a second
application), #322 (6d 2.7's step 3) and #323 (the warehouse switches); read again on 2026-11-20 with
nothing up, when the user asked for the most steps with the least environment in each sitting. Each
sitting starts on the user's word, since it is metered, and raises only what its blocks call: what needs
nothing up runs before it, a sitting that needs no GitLab raises none, and an application reaches a
Sandbox space as a tar built on the laptop (Stage 20 step 2.0), never through GitLab. The steps are
grouped by what they raise. Every Sandbox step that needs no GitLab is on one of five Sandbox days, N.9's
three and N.10's two, which also hold the passes no sitting held: Stage 17's 2.3 to 5, Stage 20's pass 5
and Stage 21's pass 5. Every step that needs GitLab is on one of two release sittings, N.11's R1 and R2,
where release G, N.8.3 and each application's first release had a sitting of their own. The order is the
dependencies', and N.12 holds its calendar; the waiting list's "Sittings with the environment up" says what each
closes, and its Dates bound items 4, 5, 9 and 10.

1. **With nothing up, done 2026-11-17.** Release G's step 3, `production/studio/`, applied at 13:11 UTC on
   the user's word naming it, from the plan saved at 05:06 UTC from `main` at `80e996f5` (2 added, 2
   destroyed), and re-planned `No changes` (N.8.5 step 3); under a blanket authorization the app's
   classifier had refused it the same day (*Production Deploy*). The five slices item 31 applied re-plan
   `No changes` from the same tree, so the Lesson 79 window is closed, and Stage 19's step 8 read the same
   day (xvii, xxv). The day's pull request writes Stage 17's 9.1 to 9.4 and 10.1 to 10.3 (the preflights,
   `examples/app-ml/` and `examples/app-genai/`; the lint's rules are
   [`awsds-workflows` pull request #26](https://github.com/felipenoris/awsds-workflows/pull/26)), 9.5's
   target slices with `TM-33`, and Stage 20's pass 1 (`examples/app-dbt/` and [`catalog.md`](catalog.md))
   and its 4.1 to 4.3 (the modules' tags, the callers' pins, the battery's rows); its plans came from
   worktrees and are taken again from `main` (Lesson 79).
2. **With nothing up, the user's acts**, each a waiting-list row. Done 2026-11-17: that pull request
   (#313) and `awsds-workflows` pull request #26 merged at 15:48 UTC, the new applications' pins moved to
   the merge, `37cb5a6`; and each apply by name, from `main` at `13581cd0`, from 16:00 to 16:12 UTC:
   `production/registry` first, since `identity/sso` names its repository, then Stage 20 4.4's five slices
   with the battery's Phase 4b (53 as expected), then the rest of 9.5's target slices, both `studio/`
   slices taking the two changes in one apply (Lesson 69), each re-planned `No changes`; and `TM-33`
   accepted, on the condition that the path is AWS's, read the same day. The decisions a sitting reads
   were taken on 2026-11-17 on the open-decisions review's cards (pull request #317): Stage 19 decisions
   28 and 15, Stage 20 decisions 9 and 11, 6h decisions 3 and 8, and 6d decision 16 (a), under which a
   project created before 6d's step 2.7 applies the profile takes that step's path for living projects.
   6d 2.7's steps 2 to 5 were done on 2026-11-18 (step 4's *Update project* retiring no `Tooling` domain,
   `SUP-380`; step 5's `throwaway-6d` read, *Workflows* opening on the blueprint's domain alone, then
   deleted). The three application projects were created on 2026-11-19 and their `sandbox/workflows/`
   lines applied the same night on the user's word (`3 added`, re-planned `No changes`), and the user added
   their contributors, the bundle role and Sandbox's `InfrastructureAccess` (9.6, 10.4, Stage 20 2.0).
   Stage 20 2.0's archive and tar were built on 2026-11-19 from `main` at `103b4acc`, pull request #320's
   merge, and checked, which closes 2.0 before sitting A (item 4). Stage 20 8.3's `DataLake` environments
   `deploy-staging-app-dbt` and `deploy-production-app-dbt` were created on 2026-11-19 at 02:23 and 02:27
   UTC on the user's word, both `ACTIVE` with the database `app_dbt` and its source, and `staging/studio/`'s
   `product_databases` line applied at 02:27 from 8.3's branch, re-planned `No changes` (8.4).
   The rest of the Sandbox slices that read `app-ml-dev`'s and `app-genai-dev`'s roles (9.5's pairs but the
   training pair, `sandbox/bedrock/`, `sandbox/ml/`), `EXC-11`'s share and the interactive OU's SCP admitting
   Nova Lite were applied on 2026-11-19 from `main` after pull request #326, the SCP by the orchestrating
   session with the battery's `ou` phase (54 as expected). Nova Lite was enabled in projects the same day
   (10.4). Left: the training pair in sitting B (item 7). Stage 20's decisions 14 to
   17 were taken on 2026-11-18 and their changes written, `app-dbt` pinned to `awsds-workflows` `4613ddc`.
   Stage 20 8.4's applies of the four `[P]` slices its pass 8 wrote ran on 2026-11-18, closing their
   Lesson 69 window. 6d 2.7's acts need nothing metered; its step 3's code was written and planned on
   2026-11-18 on [pull request #322](https://github.com/felipenoris/AWS-DataScience/pull/322) (`1 to change`), applied on the user's word at 18:45 UTC the same day, after step 2's acts;
   *Workflows* opened after it, and the user merged it at 19:13 UTC.
3. **With nothing up, now**, each a waiting-list row:
   - [Claude⚡] 6d decision 6's apply of `production/networking/` ran at 19:21 UTC on 2026-11-20 from a
     tree equal to `30855d92`'s, on the user's word: the portal's name in the proxy's allow-list parameter,
     *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, version 12, the re-plan `No changes`.
     The name reaches Squid at the association's first run with the proxy up, and only day 1's `PX-3` on
     the host proves the render (`SUP-071`).
   - [Claude⚡] Stage 17 decision 7's statements for endpoint configurations, endpoints and pipelines in
     `sandbox/ml/` ran at 19:40 UTC on 2026-11-20 from `main` at `78dc4397`, on the user's word, *"Apply
     complete! Resources: 0 added, 1 changed, 0 destroyed."*, the re-plan `No changes`: N.9's day 3 (pass
     5's pipeline) and N.10's day 1 (pass 4's endpoint) wait on nothing of it.
   - [user] Stage 19 4.12's membership: the Governance Manager added to `deploy-production` by the
     project's owner with the designation `subscription-approver`, then xxvi's portal half. Neither needs
     release G; the request and the approval do (item 6).
   - [user] Stage 20 2.1 before N.9's day 1; Stage 17 0.9 before day 2 and `app-ml-dev`'s MLflow App
     before day 3; 6d 1.1 and 1.2, and 7.6's second identity in a browser profile of its own; N.10.1's
     acts; 6g 2.4, read from the query editor with no space on 2026-11-22 (6g's log).
4. **N.9's day 1** (N.9.3), `make hub-up` and `make up ENV=sandbox GROUPS=mwaa`, no GitLab: 6d's block
   and Stage 20's sitting A, passes 2 and 3 and 4.5, after Stage 20 2.1 and before 2026-12-18, when dbt
   Core 1.11's critical support ends.
5. **R1** (N.11.1), after the admin secret's first rotation in Production, scheduled 2026-11-22 01:59:59
   UTC, and before 2026-12-17, when the newest GitLab backup leaves the bucket: release G (N.8.5 steps 4
   and 5), N.8.3's reading of the rotation on a Production raise of its own after the leg, a backup, the
   local user's password, 6d 2.7's step 7, the three application projects in GitLab, and pull request
   #321 merged after Production's leg. `app-dbt`'s first release joins it once N.9's day 1 has run and
   Stage 20's 8.5 and 8.6 are done; otherwise R2 carries it.
6. **With nothing up, once R1's Production leg has run**, in R1's own wait (N.11.1 step 5): Stage 19 4.12's request by `eighth-experimentation` and Stage 20 5.0's
   by `app-dbt-dev`, both on the listing release G creates, each approved by the Governance Manager and
   its fulfilment read on both sides; Stage 20 5.1's model, its archive and its tar. Both subscriptions
   stay until N.10's day 2 ends, since both of its days read through them.
7. **N.9's days 2 and 3** (N.9.4, N.9.5), no GitLab: Stage 17's sitting B with 2.3 to 3.2 and pass 7 on
   day 2, `GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent`; 6e 6.4's window, Stage 17's sitting C and its
   pass 5 on day 3, `GROUPS=mwaa,mlflow,bedrock-base`. They depend on no other sitting, so they run before
   R1 or after it.
8. **With nothing up, after N.9's day 3**: Stage 17 10.5, the exception and the application's names in
   the targets, once 10.4 read a first answer from Nova Lite through Sandbox's in-Region profile; its
   threat-model entry accepted before its applies, the account's guardrail configuration applied by
   `<env>/studio/`, and the retention mode the user's act in each target.
9. **N.10's two days** (N.10.3, N.10.4), no GitLab, before 2026-12-19 so the trial absorbs the
   warehouse: 5b, 6h, Stage 19's pass 5, Stage 17's pass 4 and Stage 20's pass 5 on its day 1,
   `GROUPS=redshift,mwaa`; Stage 21's passes 2 to 5, Stage 19's 5.4 and 6h's 6.4 on its day 2,
   `GROUPS=redshift`, the subscriptions revoked at its end. Its day 1 follows item 6, whose subscriptions
   it reads, and N.9's day 2, whose registered version pass 4 serves.
10. **R2** (N.11.2), after items 7 to 9 and #321's merge: `app-dbt`'s first release unless R1 carried it,
    before 2026-12-18 or with the archive moved to dbt 1.12; `app-ml`'s (Stage 17 9.7) and `app-genai`'s
    (10.6), whose pipeline runs no `pip-audit` and so waits on no gates tag; then `app-etl`'s release
    retiring its model half (9.11).
11. **With nothing up, after R2**: 9.11's estate pull request, planned from a `main` that holds it
    (Lesson 79).
12. **The stages' close**: after item 5, Stages 8, 9 and 10 hold only what N.5 lists, and each can close
    as Stage 4 did, what waits moved to the trigger or the stage that provides its subject. The user's
    decision, read then.
13. **What waits on something else** (N.5): a second application in a chain that consumes another's
    marker, a `monitoring` endpoint, Stage 11's S3 data events, a release that removes a file (item 10),
    a workflow's 50th version, a blueprint reconciliation, and the halves no step provokes.

### N.7 The sittings prepared 2026-10-26

Written with nothing up, after N.3. N.1, N.2 and N.4a carry the release's and the warehouse's commands;
these are the sittings N.6 adds.

#### N.7.1 The GitLab sitting: the house image `default-v0.10.0`

What it closes: Stage 8 1.1's 73-name literal, so `DE-5` passes again and a deploy from a space needs no
session export (Stage 10 2.1); with it, Stage 8 decision 1's zlib pair in `gates-v0.6.0`, the mirror at
`main` before the next tag, Stage 8 xxviii's active half by a job on the deploy runner, Stage 7 Validation
2's `PX-3`, and a GitLab backup before the oldest leaves the bucket on 2026-11-13. While up, at
`cost-model.md`'s rates: the hub about 0.026 USD/h, GitLab and SharedServices' twelve endpoints 0.187, the
build runner 0.2117, the test and deploy runners 0.0376 and their root volumes 0.0136, about 0.48 USD/h.

1. **[Claude] The day of the tag, before it** (Lesson 77): the lock's audit on the laptop
   ([`gitlab/awsds/dev-env/README.md`](../../../gitlab/awsds/dev-env/README.md), *Before a build*) and the
   copy against the estate:

   ```bash
   ./scripts/check-gitlab-mirror.py --plan
   ```

   **Read 2026-10-26** (Stage 8's log): 454 pins audited, 57 findings accepted by id or alias, none
   blocking, `nltk` 3.10.3's `PYSEC-2026-3740` a warning with no fixed version; `GM-1` to `GM-8` passing,
   73 names, `61f1e1646df12c14` on both sides. A reading of another day is taken again.
2. **[user] The raises**: `make hub-up`, `make gitlab-up BUILD=1`, the tunnel ([`gitlab.md`](gitlab.md) §U).
3. **[user] The gates' tag `gates-v0.6.0`** (Stage 8 decision 1's zlib pair, option A, taken 2026-10-26): a
   merge request on `awsds/ci-gates` carrying the copy's `baselines.gitlab-ci.yml`, which names
   `CVE-2026-85091` on `zlib` and `zlib1g` in the SageMaker Distribution's list, the commit message saying
   who accepted the pair and why; the merge, the tag `gates-v0.6.0` once `git ls-remote --tags` reads it
   free, and its commit read back ([`gitlab.md`](gitlab.md) §G). That commit replaces the `include:` `ref` of
   the copy's `gitlab/awsds/dev-env/.gitlab-ci.yml`, the tag in the comment beside it, so step 4's merge
   request moves the image's pin with it. The application template's pin moves with its own next merge
   request.
4. **[user] The merge request on `awsds/dev-env`** from the copy under `gitlab/awsds/dev-env/`: the
   Dockerfile's `NO_PROXY_LIST` at 73 names, and the CI/CD CLI by its name through the base
   environment's activation hook (Stage 8 decision 22, taken 2026-10-26), by `gitlab.md` §M's procedure;
   the branch pipeline runs the recipe
   checks and the gates, and the steward merges. `./scripts/gitlab-mirror.py` then copies the merge back.
   An order set by the image's `ENV PATH` is not the hook's equivalent: every start script of the
   SageMaker Distribution runs `micromamba activate base`, which puts `/opt/conda/bin` first, so such an
   order reaches no space's server or terminal, and the smoke's `RUN`, which activates nothing, passes
   on it (Stage 8 decision 22). The hook prepends `/opt/awsds/bin`, the house CLI's entry point alone,
   after each activation, and the smoke reads the name after `micromamba activate base`.
5. **[user] The tag** `default-v0.10.0` on the merge, a minor since the recipe changes, once `git
   ls-remote --tags` on `awsds/dev-env` reads it free: the release pipeline builds `base` and `dev-env` on
   the build runner, runs the smoke and the scans, waits on the release gate, the user's manual job, and
   `register` creates Sandbox's version 11, alias `0.10.0`.
6. **[Claude] The readings**: `./aws/devenv.py` (`DE-5` passing against version 11, `DE-1` 73 entries), the
   version's `ContainerImage` the pushed digest, the smoke's `cicd-cli.txt` reading
   `/opt/awsds/bin/aws-smus-cicd-cli` under `/opt/awsds/venv/bin/` and the house environment's version,
   and the README's release row with both digests and sizes, in the copy.
7. **[user] The mirror** pushed at `main` from the project folder, read at the commit `origin/main` holds:

   ```bash
   git push gitlab main
   ```

8. **[user] Stage 8 xxviii's active half** (option B, taken 2026-10-26), with no trust widening: the job
   `sts-global-probe` arrives with step 4's merge request. On `awsds/dev-env`, *Build → Pipelines → Run
   pipeline* on `main` with the variable `STS_GLOBAL_PROBE` set to `1`, then *Run* on the manual job: the
   deploy runner assumes both deploy roles as its own role through `sts.us-west-2.amazonaws.com` and
   through `sts.amazonaws.com`, and prints each session's ARN. **[Claude]** the trails, read after their
   delay (Lesson 62), the session name `xxviii-<pipeline id>`:

   ```bash
   for p in awsds-infra-prod awsds-infra-staging; do for r in us-west-2 us-east-1; do echo "== $p $r"; aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole --start-time <the job's minute> --profile "$p" --region "$r" --query 'Events[?contains(CloudTrailEvent, `xxviii-`)].EventTime' --output text; done; done
   ```

   Expected: each global call's records in `us-east-1` alone and each regional call's in `us-west-2`; the
   misuse rules exempt the runner's role, so none fires. A record in `us-east-1` reaches no `us-west-2`
   rule, whoever its caller, which is xxviii's question; whether a trust pinning `aws:RequestedRegion`
   refuses the call stays unread, the deploy roles' trust pinning nothing.
9. **[user] A GitLab backup** by hand in a Session Manager shell ([`gitlab.md`](gitlab.md) §B), read in the
   bucket after. **[Claude⚡]** `PX-3`, deliberately, since the flag's SSM Run Command is a write API:

   ```bash
   ./aws/proxy.py --on-host
   ```

10. **The downs**: `make gitlab-down`, the tunnel, `make hub-down`; **[Claude]** §R and each step's entry in
   Stage 7's and Stage 8's logs.

**Run 2026-10-26** (Stage 7's and Stage 8's logs), 21:16 to 22:31 UTC, beside N.4a's warehouse sitting,
which shared the hub: the lock's audit (0 blocking) and `GM-1` to `GM-8` the day of the tag;
`awsds/ci-gates` !1 merged and tagged `gates-v0.6.0` (`d0b895c8`); `awsds/dev-env` !12 merged as
`c8bac16e`; the tag's pipeline #109 registered `default-v0.10.0-c8bac16e` as version 11, alias `0.10.0`,
22 min 39 s from the tag, its smoke reading the CLI by its name as the house's 1.0.9 after `micromamba
activate base` and `./aws/devenv.py` reading `DE-5` passing at 73 names; the mirror at `94ed050d`;
`sts-global-probe` (pipeline #110) put each global call's records in `us-east-1` alone, past 4.6's
rules (Stage 8 decision 29); `PX-3` passing; the backup `1793052899_2026_10_26_19.4.2`. Two readings
are new: the smoke runs after both pushes in `build-images`, so a red smoke spends the release tag and
both ECR tags; and GitLab's agent registered 7 min 21 s after the start, its first call timed out at
the `ssm` endpoint's address ([`gitlab.md`](gitlab.md) §U step 5).

#### N.7.2 The debug window: Stage 9 3.1's debug-role read

Needs nothing up: the window is an apply on `production/sagemaker/`'s trust, the read a CloudWatch Logs call.
Step 6.3's sequence, run on 2026-10-22, with one read added. The infrastructure user's read of a job stream
on 2026-10-26 answered with no key grant through `logs` (Stage 9's log), so the debug role's read is
expected to answer the same way, its refused `Decrypt` in the trail beside the service's own.

1. **[user] The approval** in writing in this chat, as the deployment manager, with the window's end (an
   hour from the apply is enough for one assumption and the read).
2. **[Claude⚡]** the plan as `awsds-infra-prod`, from an initialised slice folder ([`terraform-changes.md`](terraform-changes.md)
   Recipe A), expected *0 to add, 1 to change*, the trust's `DateLessThan` alone and the slice's check
   warning that the window is open; the apply on the user's word:

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/sagemaker plan -input=false -var debug_window_end=<the approved end> -out="$HOME/tmp/debug-window.tfplan"
   ```

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/sagemaker apply -input=false "$HOME/tmp/debug-window.tfplan"
   ```

3. **[user] The persona's session** as the Data Scientist User (`aws sso login --sso-session
   awsds-scientist --no-browser`, the URL answered in a private window), the assumption of 6.3's item 1,
   then the read through the assuming profile, a job stream named by `describe-log-streams`:

   ```bash
   aws logs describe-log-streams --log-group-name /aws/sagemaker/ProcessingJobs --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text --profile awsds-scientist-prod-debug --region us-west-2
   ```

   ```bash
   aws logs get-log-events --log-group-name /aws/sagemaker/ProcessingJobs --log-stream-name '<the stream>' --limit 5 --start-from-head --profile awsds-scientist-prod-debug --region us-west-2
   ```

   Expected: the events; a refusal is recorded with its wording, and its layer read in the trail.
4. **[Claude]** the trail: the assumption, the read, and the `Decrypt` pair, the debug role's refused one
   `invokedBy logs.amazonaws.com` and the service's through `fas.s3.amazonaws.com`. The alarm's mail is
   the user's to read.
5. **[Claude⚡] The closing apply** without the variable, re-planned `No changes`, and `./aws/deploytargets.py
   awsds-infra-prod` reading `DT-9` closed, in the same sitting.

**Run 2026-10-26** (Stage 9's log): the approval in chat; the window applied at 15:09:55 UTC until 16:10, the
plan *0 to add, 1 to change*; the persona's assumption `debug-window-logs` and its read answered, the stream's
first lines returned through the debug role; the trail held both assumptions, the read and the `Decrypt`
pair, and the alarm fired once per assumption with a notification delivered each time; the closing apply at
15:25:44 UTC, `DT-9` closed and the re-plan `No changes`.

#### N.7.3 The second Sandbox sitting

Since 2026-10-27 it runs inside the release sitting, N.8.2 step 13, whose raises it shares; Stage 9 8.1's half
ran from the portal's query editor on 2026-10-30 (N.8.1 step 3). N.3's raises and downs, without GitLab when no
clone is owed. What it closes, with `default-v0.10.0` registered as version 11 on 2026-10-26: the `dev` deploy
from a space on it by [`sagemaker-application.md`](sagemaker-application.md) §D,
`scripts/dev-cli.sh` for steps 6 and 7, with no `NO_PROXY` export, `getent hosts
airflow-serverless.us-west-2.api.aws` answering a `10.20.x` address and the proxy log silent on the name.
The clone carries the script once the template's merge request with it has merged on `awsds/app-etl`
([`gitlab.md`](gitlab.md) "The application template"), which needs GitLab up. The space's terminal
reads `type -a aws-smus-cicd-cli` with `/opt/awsds/bin/aws-smus-cicd-cli` first and
`aws-smus-cicd-cli --version` 1.0.9, the activation hook's reading the smoke cannot take, since a build
starts no space. The space's image is set to `awsds-sandbox-dev-env` version 11 (alias `0.10.0`) in its settings
before *Start*, as N.3 step 3 does for version 10: an image's environment is read when its app starts.

#### N.7.4 Stage 10 decision 11's narrowing: the applies and the Deployment Manager's read

Needs nothing up: three policy writes and an API read. Option A, taken by the user on 2026-10-26:
`kms:ViaService` `airflow-serverless.<region>.amazonaws.com` on the Deployment Manager's decrypt, in the
permission set (`identity/sso/`'s `DecryptWhatTheWorkflowServiceEncrypts`) and in both data keys
(`AllowTheDeploymentManagerToReadWorkflowRuns`). The value is the key's convention and unmeasured: the read
after the applies is the measurement, and a refusal reverts all three.

1. **[Claude] The plans**, read 2026-10-26 (Stage 10's log): `identity/sso/` as `awsds-infra-identity`,
   `production/data/` as `awsds-infra-prod` and `staging/data/` as `awsds-infra-staging`, each *0 to add,
   1 to change*, the condition alone, the set's inline policy from 8,223 to 8,333 characters. Fresh plans
   at the applies.
2. **[Claude⚡] The applies**, on the user's authorization in chat and the other sessions told first: the
   two data slices, then `identity/sso/`, each re-planned `No changes`.
3. **[user] The Deployment Manager's read** in Production. The laptop holds no Production profile on the
   `awsds-deploy` session, so one is added first, its account id read from the infrastructure user's
   profile and written into no file of the repository:

   ```bash
   aws configure set sso_session awsds-deploy --profile awsds-deploy-prod
   aws configure set sso_account_id "$(aws configure get sso_account_id --profile awsds-infra-prod)" --profile awsds-deploy-prod
   aws configure set sso_role_name DeploymentManagerAccess --profile awsds-deploy-prod
   aws configure set region us-west-2 --profile awsds-deploy-prod
   ```

   Then the sign-in as the Deployment Manager User, the URL answered in a private window, and a run of the
   `app-etl` workflow read:

   ```bash
   aws sso login --sso-session awsds-deploy --no-browser
   ```

   ```bash
   W=$(aws mwaa-serverless list-workflows --profile awsds-deploy-prod --region us-west-2 --query "Workflows[?Name=='awsds-prod-wf-app-etl'].WorkflowArn | [0]" --output text)
   R=$(aws mwaa-serverless list-workflow-runs --workflow-arn "$W" --profile awsds-deploy-prod --region us-west-2 --max-results 1 --no-paginate --query 'WorkflowRuns[0].RunId' --output text)
   aws mwaa-serverless get-workflow-run --workflow-arn "$W" --run-id "$R" --profile awsds-deploy-prod --region us-west-2 --query 'RunDetail.RunState' --output text
   ```

   Expected: the run's state, `SUCCESS` for the runs of 2026-10-25, as the infrastructure user read it on
   2026-10-26. A refusal naming `kms:Decrypt` is the value's verdict: the three slices return to the commit
   before the narrowing, by the same plans and applies.
4. **[Claude]** the trail: the `Decrypt` paired with the `GetWorkflowRun`, `invokedBy
   airflow-serverless.amazonaws.com`, under the workflow-ARN context, with no error. Staging holds no
   workflow between legs, so its half is read at its next leg's run, by the same commands with a Staging
   profile.

**Applied 2026-10-26** (Stage 10's log): the user's authorization in chat; fresh plans as step 1's; the
applies from 16:15:08 to 16:19:47 UTC, each re-planned `No changes`, the condition read back in both key
policies and in the set's role policy in Production and Staging. **Step 3 read the same day**: the
Deployment Manager's `GetWorkflowRun` answered `SUCCESS`, so the value holds and nothing reverts; step 4
read the same evening, the service's `Decrypt` in the Deployment Manager's session at 20:01:18 UTC with no
error. Staging's half is owed, at its next leg.

### N.8 The sittings prepared 2026-10-27

Written with nothing up, after the readings of 2026-10-27 (the stage logs): every instrument passing but
`DE-2`, the known absence with `sandbox/egress` down, and 0.000 USD/h in Production, Staging and Sandbox;
the Amazon Linux parameter at the runners' image; no blueprint reconciliation since 2026-10-11; the four
`ml.m5.large` quota cases `CASE_OPENED`; five GitLab backups, the newest 2026-10-26 22:15 UTC; Production's
admin secret's first rotation scheduled 2026-11-22 01:59:59 UTC. Every command runs as the infrastructure
user (`InfrastructureAccess`, the `awsds-infra-*` profile of the account it names) unless it names another
identity.

#### N.8.1 The steps with nothing up

1. **[Claude⚡] Stage 8 decision 29's apply**, on the user's authorization in chat, the other sessions on
   the laptop told first. The saved plan of 2026-10-27 reads *0 to add, 1 to change*, `p-1fp032g8` in place,
   its content and description; a plan older than another apply to the slice is made again (Recipe A):

   ```bash
   AWS_PROFILE=awsds-infra-identity terraform -chdir=terraform-live/identity/org-policies apply -input=false "$HOME/tmp/decision29-org-policies.tfplan"
   ```

   Then the re-plan, expected `No changes`, and the document read back, its last statement
   `DenyDeployRoleAssumptionOutsideTheRegion` and 14 in all:

   ```bash
   AWS_PROFILE=awsds-infra-identity terraform -chdir=terraform-live/identity/org-policies plan -input=false
   ```

   ```bash
   aws organizations describe-policy --policy-id p-1fp032g8 --query Policy.Content --output text --profile awsds-infra-identity | jq -r '.Statement[-1].Sid, (.Statement | length)'
   ```

   The slice is applied from this change's branch, so another tree plans it after the merge (Lesson 79).
   **Done 2026-10-27** (Stage 8's log): the apply 02:58:10 to 02:58:22 UTC, *"0 added, 1 changed, 0
   destroyed"*, the re-plan `No changes`, 14 statements read back.
2. **[Claude] The battery's `root` phase**, deliberately ([`scp-battery.md`](scp-battery.md), the decision 29
   amendment):

   ```bash
   ./aws/probes/scp-battery.py --phase root
   ```

   **Run 2026-10-27 at 02:59 UTC** (Stage 8's log): 26 as expected and 1 unexpected, the global row on a role
   that exists nowhere reading STS's plain refusal, as before the apply and in 20 tries to 03:09, while the
   IAM simulator read the call `explicitDeny`. The refusal of a role that does not exist hides the deny, so
   the two rows left `probes.py` and the phase holds its 25, each read as expected in that run; the
   statement's measurement is N.8.2 step 5's job ([`scp-battery.md`](scp-battery.md)).
   **[user] Optional, with nothing up**: whether STS shows the deny behind the refusal of a role that exists
   but does not trust the caller, which would let a battery row measure it. The session's classifier refused
   this attempt to Claude on 2026-10-27. Both calls are refused, the trust naming the runner alone; the
   global one names the service control policy if STS shows it:

   ```bash
   P=$(aws sts get-caller-identity --profile awsds-infra-prod --query Account --output text)
   aws sts assume-role --role-arn "arn:aws:iam::${P}:role/awsds-deploy-prod" --role-session-name scp-probe --endpoint-url https://sts.amazonaws.com --region us-east-1 --profile awsds-infra-prod
   aws sts assume-role --role-arn "arn:aws:iam::${P}:role/awsds-deploy-prod" --role-session-name scp-probe --endpoint-url https://sts.us-west-2.amazonaws.com --region us-west-2 --profile awsds-infra-prod
   ```

   **Run by the user 2026-10-30** (Stage 8's log): both refused, STS's text naming no policy on either endpoint.
   The global refusal carries an authorization id, whose details (`aws iam-toolbox
   get-request-authorization-details --region us-east-1`) name `DenyDeployRoleAssumptionOutsideTheRegion` in
   `p-1fp032g8` as the matched deny, `EXPLICIT_DENY`; the regional refusal carries none. The battery's `root` phase
   reads such an id since ([`scp-battery.md`](scp-battery.md)): its run at 06:24 UTC, 25 as expected and 1 not
   measured, met a refusal of the same call with none.

3. **[user] Stage 9 8.1's read-but-not-write**, as the Data Scientist User in a private window: the portal,
   `eighth-experimentation`'s query editor with *Athena (SQL)* as the compute, which 6f 11.10 ran with no
   space and Sandbox's `egress/` down. The subscription's resource link `glue_db_blerpkhn9nj7o0.trades`
   points at the lake's `curated.trades`:

   ```sql
   SELECT count(*) FROM "glue_db_blerpkhn9nj7o0"."trades";
   ```

   ```sql
   INSERT INTO "glue_db_blerpkhn9nj7o0"."trades" VALUES (DATE '2026-10-27', 'probe-8-1', 'probe', 0.0, 0.0);
   ```

   The row matches the table's five columns (`trade_date`, `desk`, `instrument`, `quantity`, `price`), so
   the statement reaches authorization instead of stopping at its shape (Lesson 21). Expected: the count
   answers, and the insert is refused, its wording recorded whichever layer answers first (Lesson 20),
   Lake Formation's expected, since the project role holds `SELECT` alone through the subscription's grant.
   A row that lands names itself (`desk = 'probe-8-1'`) and is the producer's to delete. **[Claude]** both
   executions and the trails: Sandbox's `StartQueryExecution` as the project role with the user's source
   identity, the read's `GetDataAccess` in both accounts, and the write's refusal with its `errorCode`:

   ```bash
   aws athena list-query-executions --work-group workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c --max-items 5 --profile awsds-infra-sandbox-1 --region us-west-2
   ```

   ```bash
   aws athena batch-get-query-execution --query-execution-ids <the two ids> --query 'QueryExecutions[].[QueryExecutionId,Status.State,Status.StateChangeReason]' --output text --profile awsds-infra-sandbox-1 --region us-west-2
   ```

   **Run 2026-10-30** (Stage 9's log): the count 30; the insert refused at the vend, Lake Formation's
   `GetDataAccess` for `INSERT` and then `DELETE` answering *"Principal does not have any privilege on
   specified resource"* in Sandbox and Data Governance; no commit and no manifest.

4. **[user] Production's free-trial balance** in the Redshift console, the day after xxiv's sitting: 299.54
   of 300.00 on 2026-10-26 at about 22:45 UTC. **Read 2026-10-30** (Stage 9's log): *"$299.50 out of
   $300.00"*, 0.04 USD after 2026-10-26's reading with no workgroup in between, so xxiv's sitting cost 0.16
   USD in all.

#### N.8.2 The release sitting: `v0.4.7`, the Sandbox half and the exercises

What it closes: the template's next release through both legs, with Stage 8 3.3's snapshot record read in
Staging and Production and the deploy script in GitLab; Stage 10 decision 11's Staging half; Stage 8
xxviii's second reading, after decision 29's apply; N.7.3's `dev` deploy from a space on version 11 with no
export; a GitLab backup; and, each on the user's word, Stage 8 xv, Stage 10 xx's second half and Stage 8
xxvii's plan half. While everything is up, at [`cost-model.md`](../cost-model.md)'s rates: the hub about
0.026 USD/h, GitLab and SharedServices' twelve endpoints 0.187, the build runner 0.2117, the test and deploy
runners 0.0376 and their volumes 0.0136, Sandbox's nineteen endpoints with the `mwaa` group 0.19, Staging's
eight 0.08, Production's `workloads-egress/` eight 0.08 (each gained `datazone` at Stage 19 step 4.4) and
the space 0.050, about 0.88 USD/h, plus the runs (cents) and AWS Config's cycle charges.

**This release is release T** ([Stage 19](../stages/stage-19-smus-native-data-product.md) decision 19 (c),
§The estate against decisions 17 to 20): the manifest holds the stage `dev` alone and the job `bundle`
stands where `test-deploy` stood, so the pipeline deploys nothing and runs nothing in Sandbox, and the
release's first run is Staging's leg. The legs are today's. Sandbox's `egress/` is raised for step 13's
space alone: a sitting without step 13 leaves Sandbox down.

0. **Release T's preparation, with nothing up**, each once:
   - **[user] The project for app-etl alone**, created from `experimentation` in the portal as the data
     scientist (Stage 19 1.5; its database created 2026-11-14, the Sandbox sitting's step 12). **[Claude]** reads its id, its
     role's name and its `Tooling` environment. **Done 2026-11-14**: `app-etl-dev`, `ceweti7jbiu1hs`, its
     role `datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk`, its `Tooling` environment `ACTIVE`.
   - **[user] The bundle role's membership**: `awsds-deploy-sandbox-test`'s group added to that project as
     a contributor, as an owner of the project (the infrastructure user once seated, or the data
     scientist in the portal; **done 2026-11-14** in the portal, whose dialog lists the group by the
     role's name), and removed from `test-experimentation`, where it was a
     `PROJECT_CONTRIBUTOR` from Stage 8 2.5 to 2026-11-14, the day the user removed it in the portal. The group is the role's
     `IAM_ROLE_SESSION_GROUP` profile, `06d426f2-84d6-38ae-a991-6806981d9520`: such a profile has no
     name, so `search-group-profiles` lists it by id alone and `get-group-profile` names its role:

     ```bash
     aws datazone get-group-profile --domain-identifier dzd-d8yrvx1ko7im6o --group-identifier 06d426f2-84d6-38ae-a991-6806981d9520 --profile awsds-infra-data --region us-west-2 --query rolePrincipalArn --output text
     ```

     Both membership writes are an owner's, made in the portal as the data scientist, on the
     project's members page, where the group shows under the role's name. The infrastructure
     role is a `PROJECT_CONTRIBUTOR` of the Sandbox projects, and DataZone refused it
     `delete-project-membership` on `test-experimentation` on 2026-11-14: *"User is not permitted
     to perform operation: DeleteProjectMembership DesignationPolicy does not allow access."*

   - **[Claude]** `sandbox/workflows/variables.tf`'s `project_roles` gains the project's role, then the
     plan, expected the role narrowed (0 to add, 3 to change, 2 to destroy on 2026-11-11) and one
     attachment added; **[user]** applies as the infrastructure user, account **Sandbox Account 1**,
     permission set `InfrastructureAccess` (`awsds-infra-sandbox-1`). After it GitLab's `main`, which
     still runs `test-deploy`, cannot deploy: no tag is pushed before step 4's merge. **Applied
     2026-11-14**, 1 added, 3 changed, 2 destroyed, from the plan saved that day:

     ```bash
     AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/workflows apply -input=false "$HOME/tmp/stage19-t-sandbox-workflows.tfplan"
     ```

   - **[user] GitLab's CI/CD variables** on `awsds/app-etl`, in step 4's sitting: `DEV_PROJECT_NAME` the
     project's name; `TEST_PROJECT_NAME`, `TEST_PROJECT_SG`, `TEST_PROJECT_KEY_ARN` and
     `TEST_PROJECT_S3_URI` removed. `SUBNET_AZ1`, `SUBNET_AZ2`, `DEV_PROJECT_SG`, `DEV_PROJECT_KEY_ARN` and
     `TRAINING_IMAGE_URI` are read by no job since this release and may stay or go.

1. **[Claude] The day of the tag, before the raises** (Lesson 77): the template's gates on the laptop,
   `pip-audit` over its runtime set as the gate runs it (`pyarrow` 25.0.1 and no finding on 2026-10-27), its
   tests, ruff and the lint at `d856982c` (45 passed and *"ok: 9 arquivo(s)"* on 2026-10-27),
   `./scripts/check-gitlab-ci.py`; and the Amazon Linux parameter (N.1 step 3), `ami-0829b74b2a8c619b7` on
   2026-10-27.
   **Read 2026-11-15** on release T's tree, `36bcf916:examples/app-etl` extracted outside the repository:
   `uv sync --locked`, ruff check and format clean, 72 passed and 1 skipped, the lint at `d856982c` with
   the job's options *"ok: 9 arquivo(s)"*, and `pip-audit` 2.10.1 over the one pinned package, `pyarrow`
   25.0.1, with no finding. `main`'s `./scripts/check-gitlab-ci.py` read `36bcf916`'s tree and `main`'s,
   *"OK"* on both. A tag on another day runs them again. The Amazon Linux parameter read
   `ami-0dac6cd09676c9fb1`, version 201, modified 2026-11-12 at 19:49 UTC: the runners `make gitlab-up`
   creates boot on a release no runner has booted on, and a boot it breaks is read in the boot log (Stage 8
   decision 25 (b)).
2. **[user] The raises**, after this change's merge: `make hub-up`, `make gitlab-up BUILD=1`, the tunnel, and,
   for step 13's space alone, Sandbox's endpoints with the MWAA Serverless group, which no job of the
   pipeline reads since release T:

   ```bash
   make up ENV=sandbox ONLY=egress GROUPS=mwaa
   ```

   **[Claude]** the other sessions told before the first raise; `./aws/cicd.py`, `./aws/egress.py
   awsds-infra-prod awsds-infra-sandbox-1` and `make status`; Stage 8 xxvii's plan half (N.1 step 3) if the
   parameter moves after the runners' creation: runners created on the current image plan `No changes`
   with or without `ignore_changes`.
3. **[user] The local user's password rotated** before the first push, in GitLab's *Edit profile →
   Password*: a keychain probe printed it into a session's transcript on 2026-11-08 (Stage 19's log). The
   keychain's entry for `gitlab.awsds.internal` goes with it, and the next push asks for the new one:

   ```bash
   printf 'protocol=https\nhost=gitlab.awsds.internal\n\n' | git credential-osxkeychain erase
   ```

   **[user] The mirror at `main`**, from the project folder; **[Claude]** read at `origin/main`'s commit:

   ```bash
   git push gitlab main
   ```

4. **[user] The template's merge request on `awsds/app-etl`**, from `examples/app-etl/` at commit
   `36bcf916`, release T's tree: `main` holds release F's since 2026-11-12 (§N.8.4), so the folder is
   taken from that commit, `git archive 36bcf916 examples/app-etl | tar -x -C <a scratch folder>`
   ([`gitlab.md`](gitlab.md) "The application template", steps 1 to 4, a branch named for the change):
   `scripts/dev-cli.sh` and its test (Stage 8 decision 22), the Glue job's snapshot record (3.3, option A:
   `glue/transform.py`, `src/app_etl/pipeline.py`, `code/app_etl_tasks.py` and their tests), the README,
   the gates' `include:` at `gates-v0.6.0` (`d0b895c8`), whose gates file is `gates-v0.4.0`'s and whose
   baseline adds decision 1's zlib pair to the scan that informs, the two proxy checks of
   `.gitlab-ci.yml` fixed for Stage 8 xv (step 12b), Stage 19 1.1's product table and publishing task
   (pass 1's mirror), and release T: the manifest with the stage `dev` alone and `PUBLISH_LISTING`
   false, and `.gitlab-ci.yml`'s job `bundle` in place of `test-deploy`. **[Claude]** beforehand, GitLab's `main`
   against the archive. **Read 2026-11-15, offline**: the clone `$HOME/tmp/app-etl` is on `main` at
   `8d50f68`, its tree `2d3160f1:examples/app-etl`'s (`5a5970a2…`), so the merge request is `git diff
   2d3160f1 36bcf916 -- examples/app-etl`: 12 files, 1,040 insertions and 214 deletions,
   `scripts/dev-cli.sh` and `tests/test_dev_cli.py` new. From the project folder, the clone brought to
   GitLab's `main` first, whose commit **[Claude]** reads against `8d50f68`:

   ```bash
   git -C "$HOME/tmp/app-etl" switch main && git -C "$HOME/tmp/app-etl" pull && git -C "$HOME/tmp/app-etl" switch -c release-t
   ```

   ```bash
   git -C "$HOME/tmp/app-etl" rm -q -r .
   ```

   ```bash
   git archive --format=tar -o "$HOME/tmp/app-etl-release-t.tar" 36bcf916:examples/app-etl
   ```

   ```bash
   tar -x -f "$HOME/tmp/app-etl-release-t.tar" -C "$HOME/tmp/app-etl" && git -C "$HOME/tmp/app-etl" add -A && git -C "$HOME/tmp/app-etl" diff --cached --stat
   ```

   The stat lists the 12 files; then the commit and the push:

   ```bash
   git -C "$HOME/tmp/app-etl" commit -m "Release T: the stage dev alone and the bundle job in place of test-deploy (Stage 19 decision 19 (c)); the deploy script, the snapshot record, the proxy checks, the product table and the publishing task" && git -C "$HOME/tmp/app-etl" push -u origin release-t
   ```

   The branch pipeline's `test`, `secret_detection` and `pip-audit` green before the merge. Then the
   CI/CD variables of step 0, before step 6's tag: `DEV_PROJECT_NAME` `app-etl-dev`, the four
   `TEST_PROJECT_*` removed.
5. **[user] `awsds/dev-env`'s merge request** from the copy under `gitlab/awsds/dev-env/` ([`gitlab.md`](gitlab.md)
   §M): `sts-global-probe` prints each call's answer or refusal and goes on, so decision 29's refusal of the
   first global call does not stop it before Staging's role; `./scripts/gitlab-mirror.py awsds/dev-env`
   copies the merge back. **Read 2026-11-15, offline**: the copy differs from GitLab's `main` at `6eff905`
   (`gitlab/mirror.json`) in `.gitlab-ci.yml` alone, 5 insertions and 3 deletions (PR #273), and the clone
   `$HOME/tmp/dev-env-v0.10.0` holds `6eff905`'s file on its branch `the-releases-v0.10.0`. From the project
   folder:

   ```bash
   git -C "$HOME/tmp/dev-env-v0.10.0" switch main && git -C "$HOME/tmp/dev-env-v0.10.0" pull && git -C "$HOME/tmp/dev-env-v0.10.0" switch -c sts-global-probe-goes-on
   ```

   ```bash
   cp gitlab/awsds/dev-env/.gitlab-ci.yml "$HOME/tmp/dev-env-v0.10.0/.gitlab-ci.yml" && git -C "$HOME/tmp/dev-env-v0.10.0" diff --stat
   ```

   The stat reads `1 file changed, 5 insertions(+), 3 deletions(-)`; then:

   ```bash
   git -C "$HOME/tmp/dev-env-v0.10.0" commit -am "sts-global-probe prints each call's answer or refusal and goes on (Stage 8 decision 29)" && git -C "$HOME/tmp/dev-env-v0.10.0" push -u origin sts-global-probe-goes-on
   ```

   The branch pipeline's `pip-audit` is expected red. The lock of `default-v0.10.0`, audited on 2026-11-15
   as the gate does with the lock's `x86_64` and `linux` markers removed (the laptop matches neither),
   reads 454 of 454 packages, 76 findings accepted and 29 blocking with a fixed version, in `langgraph`,
   `langgraph-sdk`, `msgpack`, `nltk`, `oauthlib`, `opentelemetry-api`, `pillow`, `pyasn1`, `soupsieve` and
   `tornado`. The job changes no image, so the merge is the user's call on that pipeline; a merge GitLab
   refuses for it leaves this step to the house image's next release, whose merge request moves the lock.
   Then, once N.8.1 step 1 has applied, *Build → Pipelines → Run pipeline* on `main`
   with `STS_GLOBAL_PROBE` set to `1`, and *Run* on the manual job. **[Claude]** the job's log and, after the
   trail's delay (Lesson 62), N.7.1 step 8's command: each global call refused, recorded in the caller's
   account in `us-east-1` with its `errorCode`, and each regional call answered in `us-west-2`
   (verification xxviii's second reading). A refused call's record carries no `requestParameters`, so that
   command's session-name filter misses it: the job's minute is read by `errorCode`. **Run 2026-11-15**,
   pipeline #118 (Stage 8's log). The deploy roles trust the runner, so a global refusal can only be
   `DenyDeployRoleAssumptionOutsideTheRegion`'s: the statement's one measurement, which the battery could not
   take (N.8.1 step 2); its wording says whether STS names the policy.
6. **[user] The tag** `v0.4.7` on the template's merge, once `git ls-remote --tags` on `awsds/app-etl` reads it
   free. **[pipeline]** `test`, `pip-audit`, `build-image`, `scan-gate`, `build-task-code`, `bundle`,
   `store-bundle`, `release`. **[Claude]** after `bundle`, its log: the caller `awsds-deploy-sandbox-test`,
   the 11 files, no *"Failed to get project connections"* and no *"Pattern not found"*; and in Sandbox's
   trail no write by that role over the job's minutes. The `test` project's workflows are no longer
   touched: Stage 8 xxiii's count stands at 12 and 6.
7. **[user] `make up ENV=staging ONLY=egress`**, then `staging-gate`. **[pipeline]** `staging-check`,
   `staging-deploy`, `staging-test`, `staging-model`.
8. **[Claude] Staging's readings**, with the slices up: `./aws/orchestration.py` (`OR-1` to `OR-9`); Stage 8
   3.3's record, the first `SHOW TBLPROPERTIES` against the job's Lake Formation catalog, read in the Glue
   run's output log (*"reading … VERSION AS OF <id>"*, *"wrote …/trades.source.json, snapshot <id>"*) and in
   the object, expected the table, an integer `snapshot_id` and `pinned` false, the same object as the
   summary's `source`:

   ```bash
   aws s3 cp s3://awsds-staging-outputs/app-etl/work/glue/trades.source.json - --profile awsds-infra-staging --region us-west-2
   ```

   ```bash
   aws s3 cp s3://awsds-staging-outputs/app-etl/work/job/trades.summary.json - --profile awsds-infra-staging --region us-west-2 | jq .source
   ```

   A refusal of `SHOW TBLPROPERTIES` fails the run naming the table, at `staging-test`, before the gate.
9. **[user] Stage 10 decision 11's Staging half**, with Staging's workflows up: the Deployment Manager's read
   of a run, N.7.4 step 3 with a Staging profile, added once, its account id read from the infrastructure
   user's profile and written into no file of the repository:

   ```bash
   aws configure set sso_session awsds-deploy --profile awsds-deploy-staging
   aws configure set sso_account_id "$(aws configure get sso_account_id --profile awsds-infra-staging)" --profile awsds-deploy-staging
   aws configure set sso_role_name DeploymentManagerAccess --profile awsds-deploy-staging
   aws configure set region us-west-2 --profile awsds-deploy-staging
   ```

   Then `aws sso login --sso-session awsds-deploy --no-browser`, answered in a private window as the
   Deployment Manager User, with no `aws sso logout` before or after: the logout removes every cached token,
   the infrastructure user's included (`SUP-015`), and the two `sso-session`s' tokens coexist. Then:

   ```bash
   W=$(aws mwaa-serverless list-workflows --profile awsds-deploy-staging --region us-west-2 --query "Workflows[?Name=='awsds-staging-wf-app-etl'].WorkflowArn | [0]" --output text)
   R=$(aws mwaa-serverless list-workflow-runs --workflow-arn "$W" --profile awsds-deploy-staging --region us-west-2 --max-results 1 --no-paginate --query 'WorkflowRuns[0].RunId' --output text)
   aws mwaa-serverless get-workflow-run --workflow-arn "$W" --run-id "$R" --profile awsds-deploy-staging --region us-west-2 --query 'RunDetail.RunState' --output text
   ```

   Expected `SUCCESS`. **[Claude]** Staging's trail: the `Decrypt` paired with the `GetWorkflowRun`, `invokedBy
   airflow-serverless.amazonaws.com`, in the Deployment Manager's session, with no error.
10. **[user] `make up ENV=production ONLY=workloads-egress`**, then `production-gate`. **[pipeline]**
    `production-deploy`, the three schedules staying `DISABLED`.
11. **[Claude⚡] Production's app-etl chain**, on the user's word (N.1 step 11's command), followed to its end;
    3.3's record in Production, step 8's two reads on `awsds-prod-outputs` with `awsds-infra-prod`. The two
    legs' snapshot ids are equal unless the producer wrote between them: a parity observed, not enforced
    (option A).
12. **The exercises**, each on the user's word (N.4's table), after step 11 and before the downs, with no
    other job running: 12a, then 12b, which retries a job of 12a's pipeline. Both were prepared with
    nothing up on 2026-10-27 and 2026-10-28 (Stage 8's and Stage 10's logs).

    **12a. Stage 10 xx's second half: a Glue job no application slice declares.** Nothing between the
    branch and the run compares a task's `job_name` with the job the application slice declares. The
    lint's `glue` rule at `d856982c` reads a `GlueJobOperator`'s script and `--extra-*` files against the
    allowed prefixes and, in the promoted mode, refuses the creation keys, never the name;
    `scripts/render-workflow.py` turns `app-etl-<suffix>-{proj.id}` into `awsds-<env>-app-etl-<suffix>`;
    `scripts/lint-plan.py` reads the slice's own job; the orchestration slice grants the workflow's role
    `glue_jobs`, `awsds-<env>-app-etl` alone. The policy simulator on Production's `awsds-prod-wf-app-etl`,
    the module Staging's role comes from, read 2026-10-27: `glue:GetJob` `allowed` on
    `job/awsds-prod-app-etl` and `implicitDeny` on `job/awsds-prod-app-etl-undeclared`, `glue:CreateJob`
    `implicitDeny` on both. The operator reads the job before it creates one and counts only
    `EntityNotFoundException` as absent (provider 9.32.0; the lab's run of 2026-10-16 stopped at `GetJob`
    with `AccessDenied` and no `CreateJob`), so the task is expected to stop at `GetJob` and never call
    `CreateJob`.

    1. **[user] The branch and its tag**, in step 4's clone, from `awsds/app-etl`'s `main` after step 4's
       merge, one line changed. Read offline on 2026-10-27 and again on 2026-10-28, on a copy of
       `examples/app-etl/` with that line:
       ruff, 45 tests passed, the lint *"ok: 9 arquivo(s)"* with the job's options, the render for Staging
       naming `awsds-staging-app-etl-undeclared` with no creation key, and each of the three rendered
       copies *"ok: 1 arquivo(s)"* in the promoted mode:

       ```bash
       git -C "$HOME/tmp/app-etl" switch main && git -C "$HOME/tmp/app-etl" pull && git -C "$HOME/tmp/app-etl" switch -c xx-undeclared-glue-job
       ```

       ```bash
       sed -i '' 's/job_name: app-etl-{proj.id}/job_name: app-etl-undeclared-{proj.id}/' "$HOME/tmp/app-etl/workflows/app-etl.yaml"
       ```

       ```bash
       git -C "$HOME/tmp/app-etl" commit -am "Stage 10 xx: the Glue task names a job no application slice declares, a deliberate break" && git -C "$HOME/tmp/app-etl" push -u origin xx-undeclared-glue-job
       ```

       The branch pipeline's `test` green, then the tag on the branch's commit once `git ls-remote` reads
       `v0.4.8` free, or the next free patch:

       ```bash
       git -C "$HOME/tmp/app-etl" ls-remote --tags origin 'v0.4.*'
       ```

       ```bash
       git -C "$HOME/tmp/app-etl" tag v0.4.8 && git -C "$HOME/tmp/app-etl" push origin v0.4.8
       ```

    2. **[pipeline]** `test` to `release`, as in step 6. `bundle` is expected green: since release T
       nothing of the tag is deployed in Sandbox, so the exercise leaves no residue there, and the
       undeclared name first meets a run in Staging.
    3. **[user]** `staging-gate`. **[pipeline]** `staging-check`; `staging-deploy`, the promoted lint `ok`
       on each copy and `lint-plan` *"ok: 1 job(s) do Glue: aws_glue_job.this[0]"*, both applies;
       `staging-test` expected to fail with *"FATAL: the chain app-etl ended FAILED"*; `staging-model` and
       every Production job skipped.
    4. **[Claude] The diagnosis from the APIs**, before any `make down ENV=staging`, which destroys both
       `[E]` slices and the failure rules with them. The execution is the one `staging-test`'s log names:

       ```bash
       aws stepfunctions describe-execution --execution-arn <the execution> --query '[status,error,cause]' --output text --profile awsds-infra-staging --region us-west-2
       ```

       ```bash
       W=$(aws mwaa-serverless list-workflows --profile awsds-infra-staging --region us-west-2 --query "Workflows[?Name=='awsds-staging-wf-app-etl'].WorkflowArn | [0]" --output text)
       R=$(aws mwaa-serverless list-workflow-runs --workflow-arn "$W" --profile awsds-infra-staging --region us-west-2 --max-results 1 --no-paginate --query 'WorkflowRuns[0].RunId' --output text)
       aws mwaa-serverless list-task-instances --workflow-arn "$W" --run-id "$R" --profile awsds-infra-staging --region us-west-2
       ```

       ```bash
       aws mwaa-serverless get-task-instance --workflow-arn "$W" --run-id "$R" --task-instance-id <transform's id> --profile awsds-infra-staging --region us-west-2
       ```

       Expected: `transform` `FAILED` in seconds, its stream in `/awsds/staging/wf/app-etl` holding the
       operator's *"Checking if job already exists: awsds-staging-app-etl-undeclared"* and an
       `AccessDeniedException` on `GetJob`, and no *"Creating job"*. Then the trail, after its delay
       (Lesson 62); the refused `GetJob` is the positive control of the `CreateJob` lookup's zero:

       ```bash
       aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=GetJob --start-time <staging-test's start> --profile awsds-infra-staging --region us-west-2 --query 'Events[].CloudTrailEvent' --output json | jq -r '.[] | fromjson | [.eventTime, .userIdentity.arn, (.errorCode // "-"), (.errorMessage // .requestParameters.jobName)] | @tsv'
       ```

       ```bash
       aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=CreateJob --start-time <staging-test's start> --profile awsds-infra-staging --region us-west-2 --query 'length(Events)'
       ```

       Expected: the workflow role's `GetJob` on the undeclared name refused, and 0. The failure rules and
       the topic over the run's window, as N.0 step 2 read them:

       ```bash
       for rule in awsds-staging-wf-app-etl-failed awsds-staging-chain-app-etl-failed; do aws cloudwatch get-metric-statistics --namespace AWS/Events --metric-name TriggeredRules --dimensions Name=RuleName,Value=$rule --start-time <staging-test's start> --end-time <its end plus 10 minutes> --period 60 --statistics Sum --profile awsds-infra-staging --region us-west-2; done
       ```

       ```bash
       aws cloudwatch get-metric-statistics --namespace AWS/SNS --metric-name NumberOfNotificationsDelivered --dimensions Name=TopicName,Value=awsds-staging-alerts --start-time <staging-test's start> --end-time <its end plus 10 minutes> --period 60 --statistics Sum --profile awsds-infra-staging --region us-west-2
       ```

       Expected each rule `Sum` 1 and two notifications delivered. Production is untouched when its job
       still reads `v0.4.7`'s prefix and the undeclared name does not exist there (read 2026-10-28:
       `v0.4.6`'s prefix and *"Job not found"*):

       ```bash
       aws glue get-job --job-name awsds-prod-app-etl --query 'Job.Command.ScriptLocation' --output text --profile awsds-infra-prod --region us-west-2
       ```

       ```bash
       aws glue get-job --job-name awsds-prod-app-etl-undeclared --profile awsds-infra-prod --region us-west-2
       ```

    5. **After the readings**: **[user]** the branch deleted in GitLab; **[Claude⚡]** on the user's word, the
       Sandbox residue, its name read first:

       ```bash
       aws glue get-jobs --query "Jobs[?starts_with(Name, 'app-etl-undeclared-')].Name" --output text --profile awsds-infra-sandbox-1 --region us-west-2
       ```

       ```bash
       aws glue delete-job --job-name <the name> --profile awsds-infra-sandbox-1 --region us-west-2
       ```

       The tag `v0.4.8` stays spent. Step 14 records `v0.4.7`'s values, never the `*-release.auto.tfvars.json`
       of `v0.4.8`'s pipeline. **[Claude]** `terraform-modules/orchestration/workflows.tf`'s comment on
       `RunTheApplicationsGlueJobs` says an undeclared name reaches `CreateJob`; it is brought to the
       reading in the module's next tag.

    **12b. Stage 8 xv: the proxy stopped alone.** Through `v0.4.6` the template's check could not see a
    stopped proxy (read 2026-10-27 and 2026-10-28, Stage 8's log). The `.promotion` check read
    `sts.us-west-2.amazonaws.com`, a name the deploy runner's `NO_PROXY` carries since VPC-SharedServices'
    `egress/` holds an `sts` endpoint (the `vpc-egress` core): the runner's regional `AssumeRole` calls of
    2026-10-26 21:51:42 and 21:51:46 UTC came from `10.30.20.81` through `vpce-0bf41975f9312dbc0`, its
    global ones of 21:51:43 and 21:51:47 from the proxy's `44.244.33.52`. Under the job's `set -eu`, a
    failed `code="$(curl …)"` also ends the script with curl's own status before the `if`: on the laptop,
    against a proxy that does not answer, the old check exited 28 after 20 s with nothing printed, and with
    the STS name in `NO_PROXY` it read `302` in 1 s and passed. A `.promotion` job of `v0.4.6` would pass
    the check and fail at its first call through the proxy, `uv run`'s download from PyPI, since the deploy
    image holds no project environment and the runner mounts no uv cache. The fix rides step 4's merge
    request: both checks read the SageMaker API, which VPC-SharedServices holds no endpoint for (Stage 7
    decision 9), with `|| true` inside the substitution; against a proxy that does not answer, the fixed
    check printed the FATAL line and exited 1 after 20 s (2026-10-28).

    The laptop is on the split-tunnel profile: under the monitored one a stopped proxy leaves it no path to
    AWS ([`vpn.md`](vpn.md) §C7), and step 3's start could not reach EC2. While the proxy is stopped no
    runner and no space reaches the internet; GitLab answers through the tunnel, `.awsds.internal`
    bypassing the proxy.

    1. **[user] The stop**, the proxy host alone, from the project folder as the infrastructure user
       (`awsds-infra-prod`, account Production, `InfrastructureAccess`); **[Claude]** the host read
       `stopped`:

       ```bash
       ./scripts/slices.py down --env production --only proxy
       ```

       ```bash
       aws ec2 describe-instances --filters Name=tag:Name,Values=awsds-prod-proxy --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text --profile awsds-infra-prod --region us-west-2
       ```

    2. **[user] The negative**: *Retry* on `staging-check` in 12a's pipeline, already failed, or in
       `v0.4.7`'s when 12a is not run, which the positive turns green again. The job reads Staging's
       `egress/` and nothing else, and every `.promotion` job runs the same check first. Expected about
       20 s after the job starts, before the clone: *"FATAL: no answer through the proxy: is the hub up
       (make hub-up)?"*, exit 1.
    3. **[user] The start**; **[Claude]** the host read `running`, by step 1's command:

       ```bash
       ./scripts/slices.py up --env production --only proxy
       ```

    4. **[user] The positive**, a minute after `running`: *Retry* on the same job, expected *"the proxy
       answers (<code>)"*, the clone's commit and the job green. **[Claude]** both runs' times and lines,
       from the job logs.
13. **The Sandbox half** (N.7.3), Sandbox's `egress/` up since step 2. Stage 19's Sandbox sitting created
    `app-etl-dev`'s database `app_etl` on 2026-11-14 (its step 12) and ran this deploy from a tar with
    `v0.4.6`'s image (its step 13): the workflows `app_etl_app_etl_dev_app_etl` and
    `app_etl_app_etl_dev_app_etl_train`, the run `huQUoGZvttPwAMs` `SUCCESS` in 893 s, and the table
    `app_etl.trades_notional` created. This step redeploys them from the clone with `v0.4.7`'s image, and
    the run writes the table that run created.
    - **[user]** the persona's GitLab token (N.3 step 2); the space, a JupyterLab space of the `dev`
      project, the one for app-etl alone since Stage 19 decision 18 (d), whose domain takes the house
      image first ([`dev-env.md`](dev-env.md) §C6; attached 2026-11-14, Stage 19 item 33), set to `awsds-sandbox-dev-env`
      version 11 (alias `0.10.0`) on `ml.t3.medium` in its settings before *Start*, then a terminal;
    - **[user]** the activation hook's reading, which no build can take, and the endpoint's name:

      ```bash
      type -a aws-smus-cicd-cli; aws-smus-cicd-cli --version; getent hosts airflow-serverless.us-west-2.api.aws; printenv NO_PROXY | tr , '\n' | grep -c .
      ```

      expected `/opt/awsds/bin/aws-smus-cicd-cli` first, 1.0.9, a `10.20.x` address and 73;
    - **[user]** the clone (N.3 step 5's command), then [`sagemaker-application.md`](sagemaker-application.md)
      §D steps 3, 5, 6 and 7 with `scripts/dev-cli.sh` and no `NO_PROXY` export, `JOB_IMAGE_URI` the image
      `v0.4.7`'s `build-image` pushed, by digest;
    - **[Claude]** 2.1's reads (N.3 step 7) and the run to its end, and the proxy's log silent on the name
      over the deploy's minutes:

      ```bash
      aws logs filter-log-events --log-group-name /awsds/prod/proxy --start-time <the deploy's minute, epoch ms> --filter-pattern airflow-serverless --profile awsds-infra-prod --region us-west-2
      ```

14. **[Claude] 3.7**: the four `release.tf`s with `v0.4.7`'s values (the two application slices' tag, image
    digest and bundle SHA256; the two orchestration slices' tag and each workflow's definition and code
    `VersionId`s, from the legs' `*-release.auto.tfvars.json` artifacts), each slice planning `No changes`,
    in a change the user merges; the mirror pushed after the merge.
15. **[user] A GitLab backup** by hand in a Session Manager shell ([`gitlab.md`](gitlab.md) §B), or the timer's
    at 03:00 UTC with the host up; **[Claude]** read in the bucket.
16. **The downs**: **[user]** the token revoked and `git credential-cache exit` in the terminal, every portal
    tab closed, then `make down ENV=sandbox` if step 13 raised it, `make down ENV=staging`, `make down
    ENV=production ONLY=workloads-egress`, `make gitlab-down`, the tunnel down, `make hub-down`; **[Claude]**
    §R on the three profiles, `./aws/cicd.py`, `./aws/orchestration.py`, `make status`, and each step's
    entry in its stage's log.
17. **[Claude⚡] The application removed from `test-experimentation`**, on the user's word, once the
    pipeline has reached Production: the two workflows the `test` deploys created, the Glue job
    `app-etl-4gqfau9xuo6e4w` and the objects under the project's `shared/app-etl/`, each read before its
    delete; their log groups stay under `EXC-10`'s rule. With nothing up, as the infrastructure user in
    **Sandbox Account 1**:

    ```bash
    aws mwaa-serverless list-workflows --profile awsds-infra-sandbox-1 --region us-west-2 --query "Workflows[?contains(Name,'test_experimentation')].[Name,WorkflowArn]" --output text
    ```

#### N.8.3 The warehouse and backup readings, carried by R1

What it closes: `EXC-13`'s Production half, whether the database took the password the admin secret's first
rotation wrote; the free trial's pair of readings around a warehouse sitting; and a GitLab backup before
the newest, of 2026-10-26 22:15 UTC, leaves the bucket on 2026-11-26. A release sitting inside the window
carries the backup, and the Sandbox warehouse's owed items (the waiting list's Warehouse row) can ride the
same hub start, each after its decision. **Read 2026-11-17**: the newest backup is the timer's of
2026-11-16 03:01 UTC, taken during release F's sitting, expiring 2026-12-17 (the bucket's rule expires a
current version after 30 days), so step 4's backup moves to any GitLab sitting before that date; the
secret's `NextRotationDate` read 2026-11-22 01:59:59 UTC on 2026-11-16, never rotated. R1 (N.11.1)
carries every step below on its own raises, after the rotation and before 2026-12-17: steps 2 and 3 on a
Production raise after release G's leg, step 4's backup with GitLab already up.

1. **[Claude] The rotation**, with nothing up, expected `LastRotatedDate` on 2026-11-22:

   ```bash
   aws secretsmanager describe-secret --secret-id 'redshift!awsds-prod-warehouse-dbadmin' --query '[LastRotatedDate,NextRotationDate]' --output text --profile awsds-infra-prod --region us-west-2
   ```

2. **[user]** the free trial's Production balance; `make hub-up`; then:

   ```bash
   make up ENV=production ONLY=workloads-egress,warehouse-compute GROUPS=redshift
   ```

3. **[Claude]** `./aws/warehouse.py awsds-infra-prod --sql`: its database half signs in as `dbadmin` through
   the secret, so a session answering means the database took the rotated password, as Sandbox's did
   (2026-10-25); a refusal of the password is `EXC-13`'s finding.
4. **[user]** `make down ENV=production ONLY=workloads-egress,warehouse-compute`; `make gitlab-up RUNNERS=0`, a
   backup by hand ([`gitlab.md`](gitlab.md) §B), `make gitlab-down`; the tunnel down and `make hub-down`.
   **[Claude]** the backup in the bucket and §R. **[user]** the balance after the last half-hour interval
   has closed and again the next day. In R1, N.11.1's steps 3, 5 and 8 replace this step: the backup is
   taken with GitLab up for the tag, step 5 brings `warehouse-compute` down alone, and
   `production/workloads-egress/` stays up for `app-dbt`'s leg.

#### N.8.4 Release F: the CI/CD CLI's legs (Stage 19 steps 4.9 to 4.11)

What it closes: the pipeline's legs deploying `app-etl` with the CI/CD CLI into `deploy-staging`
and `deploy-production`, the chains starting the workflows the CLI creates, and the Terraform path's
retirement. What is written and why is the stage file's
[§Release F as written](../stages/stage-19-smus-native-data-product.md); this section is its order
with the commands. Every apply is the infrastructure user's (`InfrastructureAccess`), on the
user's word naming it, from a checkout that holds PR #291, with `NO_PROXY='*'`, `-input=false` and
`TF_PLUGIN_CACHE_DIR` set ([`terraform-changes.md`](terraform-changes.md) §1). A plan saved on
2026-11-12 is re-made if its slice was applied since.

**With nothing up**, before or after release T (they change nothing its legs use). Steps 1 to 3
were applied on 2026-11-12, 03:40 to 03:42 UTC, on the user's word; a saved plan applies once, so
their commands are the record of what ran:

1. **Both `studio/` slices**, accounts **Staging Account** and **Production**: the fence's warehouse
   half, the person-session deny's growth, Staging's `DESCRIBE` for the integration test,
   Production's `awsds-prod-warehouse-load`. 2 to add, 2 to change in each. **Applied 2026-11-12**,
   2 added and 2 changed in each.

   ```bash
   AWS_PROFILE=awsds-infra-staging terraform -chdir=terraform-live/staging/studio apply -input=false "$HOME/tmp/stage19-f-staging-studio.tfplan"
   ```

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/studio apply -input=false "$HOME/tmp/stage19-f-production-studio.tfplan"
   ```

2. **Both `foundation/` slices**: the deploy role's three statements. 1 to change in each; a re-plan
   takes `-var-file=<project folder>/secrets/alerts.auto.tfvars`. **Applied 2026-11-12**, 1 changed
   in each.

   ```bash
   AWS_PROFILE=awsds-infra-staging terraform -chdir=terraform-live/staging/foundation apply -input=false "$HOME/tmp/stage19-f-staging-foundation.tfplan"
   ```

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/foundation apply -input=false "$HOME/tmp/stage19-f-production-foundation.tfplan"
   ```

3. **`production/warehouse/`**: 5439 from `deploy-production`'s security group. 1 to add. **Applied
   2026-11-12**, the rule `sgr-021fb49c3c05b5697`.

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/warehouse apply -input=false "$HOME/tmp/stage19-f-production-warehouse.tfplan"
   ```

   **[Claude] reads** after the three: each re-plan `No changes`, `./aws/deploytargets.py`, and each
   project role simulated on `redshift-data:ExecuteStatement`, `sqlworkbench:CreateConnection` and
   `redshift-serverless:GetCredentials`, with a person's session beside the worker's. **Read
   2026-11-12**, 03:44 to 03:52 UTC: the five re-plans `No changes`; the instrument's 42 rows
   `pass`, `DT-13` and `DT-14` among them; Production's role `allowed` on `GetCredentials` as a worker
   and `explicitDeny` as a person, `explicitDeny` on the other two either way; Staging's role
   `explicitDeny` on the three (Stage 19's log).
4. **The lint**: the pull request in `awsds-workflows` from the patch of 2026-11-12, the user's
   merge, and `AWSDS_WORKFLOWS` in `examples/app-etl/.gitlab-ci.yml` moved to that commit. **Done
   2026-11-12**: [PR #25](https://github.com/felipenoris/awsds-workflows/pull/25) merged as `196acee` and the pin moved; the lint taken from the pin answers `ok: 9 arquivo(s)` on the template.

**After release T's sitting and the Sandbox sitting** (§N.8.2; the stage file's items 16 to 20 and
its 1.5): `product.json` brought to what the `dev` project for app-etl alone owns, the stage file's §The
Sandbox sitting, in order, step 17: expected `trades-notional` in `dataProducts` beside the asset, and no
form type, since the export carries those the project owns (item 22). **Done 2026-11-15**, before release
T's sitting: the export carries the asset and the data product with no form type, and `product.json`
requires both.

**The promotion sitting**, the hub and GitLab up and `make up ENV=staging`:

5. **`staging/chains/`**, account **Staging Account**. Staging's `orchestration/` and
   `app/app-etl/` are down since its last `make down`; a plan that reads anything to destroy there
   stops the step. 18 to add. **Re-planned 2026-11-15** at 19:32 UTC with 2026-11-12's actions, that plan
   kept as `stage19-chains-staging-1112.tfplan`; both slices read empty by `state list` the same day.

   ```bash
   AWS_PROFILE=awsds-infra-staging terraform -chdir=terraform-live/staging/chains apply -input=false "$HOME/tmp/stage19-chains-staging.tfplan"
   ```

6. **[user] The mirror and the template's merge request** from `examples/app-etl/` at `main`, then
   the tag. `bundle` fails a bundle whose catalog is not `product.json`'s; `staging-gate` is the
   user's; `staging-check` reads the egress and the project; `staging-deploy` runs the CLI;
   `staging-test` starts both chains and reads the report and the table; `staging-model` serves the
   model as the project's role. **[Claude] reads** the stage file's xxix to xxxi from the jobs' logs
   and Staging's trail. **Ran 2026-11-15 as `v0.5.0`** (pipeline #123): `staging-deploy` failed on the
   data product, a target's first import (`SUP-369`), after creating the two workflows in
   `deploy-staging`. Decision 25 (b) adds `staging-catalog` and `production-catalog`, and the next tag is
   `v0.5.1`, in this order:
   1. **Both `foundation/` slices**, accounts **Staging Account** and **Production**: the deploy role's
      `StartTheProjectsSourceBeforeTheSecondImport`, 1 to change in each, planned 2026-11-15; a re-plan
      takes `-var-file=<project folder>/secrets/alerts.auto.tfvars`. **Applied 2026-11-16**, 00:00 to
      00:01 UTC, 1 changed in each, both re-plans `No changes`.

      ```bash
      AWS_PROFILE=awsds-infra-staging terraform -chdir=terraform-live/staging/foundation apply -input=false "$HOME/tmp/stage19-d25-staging-foundation.tfplan"
      ```

      ```bash
      AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/foundation apply -input=false "$HOME/tmp/stage19-d25-production-foundation.tfplan"
      ```

   2. **[user] This repository's pull request merged and the mirror pushed**: the legs clone
      `awsds/infrastructure` at its default branch, so `deploy-application.py --catalog-follow-up`
      reaches them through the mirror alone.
   3. **[user] The template's merge request** from `examples/app-etl/` at the merged `main`, then the
      tag `v0.5.1`. `staging-deploy` admits the first import and writes `STAGING_CATALOG_PENDING=true`;
      `staging-test` runs both chains, the first writing the product table; `staging-catalog` starts
      `deploy-staging`'s source, waits for `trades_notional` in the project and deploys again, failing
      on any failed item. `v0.5.0`'s two workflows are updated in place.

   **Ran 2026-11-16 as `v0.5.1`** (pipeline #126): `staging-deploy` failed on the stage-variables
   parameter's name (`SUP-067`), moved to `/datascience/<env>/…` and retried green; in `staging-test` the
   `app-etl` chain passed and `app-etl-train` failed on `DescribeTrainingJob` (`SUP-267`). A retry of
   `staging-test` reuses the pipeline's execution names, which Step Functions refuses once an execution
   has ended, so the next tag is `v0.5.2`:
   4. **Both `studio/` slices**, accounts **Staging Account** and **Production**: the workflows grant's
      training pair; the description changes, so the policy and its attachment are replaced, 2 to add
      and 2 to destroy in each, planned 2026-11-16. **Applied 2026-11-16**, 01:20 to 01:21 UTC, both
      re-plans `No changes`.

      ```bash
      AWS_PROFILE=awsds-infra-staging terraform -chdir=terraform-live/staging/studio apply -input=false "$HOME/tmp/stage19-training-staging-studio.tfplan"
      ```

      ```bash
      AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/studio apply -input=false "$HOME/tmp/stage19-training-production-studio.tfplan"
      ```

   5. **[user] This repository's pull request merged and the mirror pushed.**
   6. **[user] The template's merge request** from `examples/app-etl/` at the merged `main`, where
      `staging-test` names its executions `$CI_COMMIT_TAG-$CI_JOB_ID-<chain>`, then the tag `v0.5.2`. The
      jobs run as in sub-step 3; `staging-deploy` writes `STAGING_CATALOG_PENDING=true` only if the import
      still fails on the data product alone.
7. **`production-check` fails once**, on the membership: the call creates `awsds-deploy-prod`'s
   group profile, whose id **[Claude] reads** from the domain's account (`datazone
   search-group-profiles --group-type IAM_ROLE_SESSION_GROUP` as `awsds-infra-data`, the profile whose
   `rolePrincipalArn` is the role). No profile names the role on 2026-11-15. **[user]**, account
   **Production**:

   ```bash
   NO_PROXY='*' aws datazone create-project-membership --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier d7qcazihvr3s7k --designation PROJECT_OWNER --member groupIdentifier=<the group's id> --profile awsds-infra-prod --region us-west-2
   ```

   Then the job again, `production-gate`, and, with `make up ENV=production ONLY=workloads-egress`,
   `production-deploy`: the bootstrap creates the three workflows and runs `app-etl` to its end
   (xxviii), and the product is listed. The deploy admits the first import, and `production-catalog`
   deploys again after the project's source: the bootstrap runs `app-etl` a second time, whose
   `publish` lists the asset's revision with `dev`'s description, README and classification.
8. **Production's cut-over, once that deploy is green.** The chain layer's names are the same in the
   old slice and the new, so the old goes first; the CLI's workflows are untouched by it. As
   `awsds-infra-prod`: a destroy plan of `production/orchestration/` (41 read on 2026-11-12) and of
   `production/app/app-etl/` (3), each read and applied; then `production/chains/` re-planned (24)
   and applied. **[Claude] reads** a chain started by hand against xxix.
9. **A warehouse sitting** (`make up ENV=production ONLY=workloads-egress,warehouse-compute
   GROUPS=redshift`): as the admin, in `governed`, `GRANT ROLE gov_trades_rw TO
   "IAMR:user-project@<project id>";`, the user the project role's `RedshiftDbUser` tag names for the
   Glue job's session (`SUP-205`), preceded by `CREATE USER "IAMR:user-project@<project id>" PASSWORD
   DISABLE NOCREATEDB NOCREATEUSER;` when the job has never connected; `production-warehouse-ddl`; the
   chain `app-etl-warehouse` started by hand and read against xxxii; `make down` after. `production-warehouse-ddl` is a manual job of the tag's
   pipeline on the deploy runner, so this step runs in the promotion sitting, GitLab up, after step 8;
   from 2026-11-22 the same raise carries N.8.3's `EXC-13` reading. **Ran 2026-11-16** in release F's
   sitting: xxxii read yes on the chain's second run, the first refused at the schema before the grant
   reached the job's user.
10. **The retirement**, a pull request after both targets ran release F: the stage file's item 31.
    **Done 2026-11-17**: PR #308's five saved plans applied from its branch, the pull request merged at
    02:13 UTC.

#### N.8.5 Release G: the data product in Production (Stage 19 decision 26 (b))

What it closes: Production's `publish` task owning the product's data product, the domain's one
`trades-notional`, created over Production's asset and listed. What is written and why is the stage
file's [§Release G as written](../stages/stage-19-smus-native-data-product.md). It runs after N.8.4's
step 8, in R1 (N.11.1), with the hub and GitLab up with the build runner for its tag (`make gitlab-up
BUILD=1`: a tag pipeline's untagged jobs run on the build runner alone, [`gitlab.md`](gitlab.md) §U), and
each act below names its identity.

1. **[user] `app-etl-dev`'s data product deleted**, `trades-notional` (`5070mjwdvjwp3k`), which was
   never published: in the portal as the project's owner (the project's data products, *Delete*), or
   as Sandbox's `InfrastructureAccess`, a contributor of the project, whose delete DataZone admits
   (measured 2026-11-16). The SSO user is the infrastructure user, account
   **Sandbox Account 1**, permission set `InfrastructureAccess` through `awsds-infra-sandbox-1`:

   ```bash
   NO_PROXY='*' aws datazone delete-data-product --domain-identifier dzd-d8yrvx1ko7im6o --identifier 5070mjwdvjwp3k --profile awsds-infra-sandbox-1 --region us-west-2
   ```

   **[Claude] reads** the name free: `get-data-product` on the id answers `ResourceNotFoundException`,
   and `search --search-scope DATA_PRODUCT --owning-project-identifier ceweti7jbiu1hs` names no item
   (`Search` refuses that scope without a project, `SUP-371`). The tag's `bundle` job then exports the
   asset alone, which `product.json` requires. **Done 2026-11-16**, 06:03 UTC, through the CLI.
2. **[user] This repository's pull request merged and the mirror pushed.** The leg's
   `deploy-application.py` reads a first import on the asset's conflict from then on, release F's
   logs read as before. **PR #307 merged 2026-11-16** as `c5e1718e`; the mirror waits for GitLab.
3. **`production/studio/` re-planned and applied**, by Claude on the user's word naming it, from a
   checkout of the merged `main` (Lesson 79): account **Production**, the infrastructure user,
   `InfrastructureAccess` through `awsds-infra-prod`. No run of Production's workflows may be in
   progress: the description's change replaces `awsds-prod-workflows` and its attachment, so for
   seconds the project role holds no workflows grant. Planned 2026-11-16: 2 to add, 2 to destroy;
   `staging/studio/` re-plans `No changes`.

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/studio plan -input=false -out="$HOME/tmp/stage19-g-production-studio.tfplan"
   ```

   ```bash
   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/studio apply -input=false "$HOME/tmp/stage19-g-production-studio.tfplan"
   ```

   **[Claude] reads** the role's policy at its new version: seven statements, the last
   `CreateTheProductsDataProductInTheProjectsDomain`, and the slice re-planning `No changes`.
   **Re-planned 2026-11-16** at 06:33 UTC from `c5e1718e`'s tree into the file above: *"Plan: 2 to add,
   0 to change, 2 to destroy"*, the new statement among the policy's; `staging/studio/` `No changes`. The
   saved plan goes stale with any apply of the slice before it. **Applied 2026-11-17**, 13:11:44 to
   13:11:57 UTC, from the plan re-saved at 05:06 UTC from `main` at `80e996f5`
   (`$HOME/tmp/review-production-studio.tfplan`), with no Production run in progress: *"Apply complete!
   Resources: 2 added, 0 changed, 2 destroyed."* The re-plan at 13:12:44 UTC reads *"No changes"*, and the
   policy is at `v1`, seven statements, the last `CreateTheProductsDataProductInTheProjectsDomain`. The IAM
   simulator answers nothing on the new pair, as on `StartDataSourceRun` (`SUP-008`): step 5's trail is the
   measurement.
4. **[user] The template's merge request** from `examples/app-etl/` at the merged `main`, then the tag
   `v0.6.0`. `staging/egress/` raised before the tag and destroyed after the Staging leg (Stage 8
   decision 27); `production/workloads-egress/` raised before `production-gate`. Each slice also creates
   its `athena` endpoint, Stage 20 decision 15 (a)'s line, once that line is on `main` (Lesson 69): 18 to
   add in each plan of 2026-11-18, where 17 was. Both targets hold their assets since `v0.5.2`, so each
   import revises the asset by name and admits nothing, and `staging-catalog` and `production-catalog`
   end at once. **The merge request read 2026-11-16**:
   GitLab's `main` holds `ced09fe4:examples/app-etl` (`07348ffa`, the tag `v0.5.2`), so it carries
   `git diff ced09fe4 c5e1718e -- examples/app-etl`, eight files: `.gitlab-ci.yml`'s and
   `manifest.yaml`'s comments, `README.md`, `code/app_etl_tasks.py`, `product.json` requiring the asset
   alone, both test files and the two arguments in `workflows/app-etl.yaml`; the tree `3b43b395…`, 28
   blobs.
5. **[Claude] reads** Production's leg: the bootstrap run's `publish` creating `trades-notional` in
   `deploy-production`, its one item Production's asset `da1fycta6l71n4`, the data product's listing
   `ACTIVE` at its revision (the task's XCom), and the trail's `CreateDataProduct` and
   `CreateListingChangeSet` as the project role with no error, which settles the resource DataZone
   authorizes them against. From Sandbox, the listing found by a search of the catalog; 4.12's
   subscription requests it. `production-register`, `-approve` and `-transform` stay `manual`: the
   newest training job in Production is release T's (the stage file, §The sittings that follow).

### N.9 The combined Sandbox sitting, prepared 2026-11-19

Written with nothing up on 2026-11-19, when the user asked for the sitting that closes the most steps with
the least environment. It holds N.6 items 4 and 7: 6d's Sandbox items and Stage 20's sitting A on day 1,
Stage 17's sittings B and C with its passes 2, 3 and 5 on days 2 and 3, and 6e 6.4. It raises the hub and
`sandbox/egress` alone: no GitLab, since an application reaches a space as a tar built on the laptop; no
Staging or Production egress; and no warehouse, which N.10 raises. `make status` read 0.0000 USD/h at 14:49 UTC that day. The
pre-flight ran the same afternoon with nothing up, each block's by the session holding its stage, the
readings in its stage log: Stage 20's (pull request #335), Stage 17's (#336) and 6d's (#337). Each stage
file holds its block step by step; this section holds the days, the raises and the lowerings. Every command
runs as the infrastructure user (`InfrastructureAccess`) unless it names another identity, and each write
is Claude's on the user's word naming it, the other sessions on the laptop told first.

The blocks add up to about twenty-one and a half hours, so the sitting runs on three days. Each day raises the groups its
blocks call and ends at zero burn: a night of fourteen hours with the hub and `sandbox/egress` up costs
about 3 USD, against 0.36 to 0.87 USD for the next day's Config cycle.

#### N.9.1 What comes before the sitting

- **[user] The merges** of this section's pull request and of #335, #336 and #337, so every apply runs
  from `main` (Lesson 79). Done 2026-11-19.
- **[user] With nothing up:**
  - Stage 20 2.1: the database `app_dbt` in `app-dbt-dev` and the editor's probe. The database's source
    then runs daily at the minute of its creation, which the sitting's runs keep clear of.
  - Stage 17 0.9's portal reading, before day 2; `app-ml-dev`'s MLflow App by 1.5's path, before day 3. An
    MLflow App bills nothing at rest.
  - 6d 7.6's second identity, `eighth-experimentation`'s contributor, signed in from a browser profile of
    its own; and the window for 6d 7.5's monitored profile, which moves the laptop's network for every
    session.
  - The laptop's client for 6d 7.5 to 7.7 and `proxy-on` in `~/.zshrc` (N.12.4), neither on the laptop on
    2026-11-20.
- **6d decision 6's apply** of `production/networking/` ran on 2026-11-20 with nothing up (N.6 item 3); day 1
  reads its effect.
- **`sandbox/ml/`'s statements** for endpoint configurations, endpoints and pipelines (Stage 17 decision 7)
  ran from `main` on 2026-11-20 with nothing up (N.6 item 3).
- **[Claude] With nothing up:** the archives of `app-ml` and `app-genai` from `main` on day 3's eve. Done
  2026-11-19: Stage 20 4.5's workflow and its second tar (pull request #335); Stage 17 7.4's evaluation
  dataset, and `examples/sandbox-ml`'s scripts read against the house image's lock (#336).

#### N.9.2 The days

| Day | Raise | Blocks | Hours |
|---|---|---|---|
| 1 | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa` | 6d decision 6's render and reading; Stage 20's sitting A; 6d 4.7, 7.6, 7.5's monitored half, 7.7 and 6.1 (viii)'s Code Editor half. Ran 2026-11-21 to 7.6; the rest rides day 2's end (N.9.3) | about 6.5 |
| 2 | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent` | Stage 17's sitting B with 2.3 to 3.2, and pass 7; then 6d's remainder of day 1. Ran 2026-11-21 to 22 without 6d's remainder (N.9.4) | about 8 |
| 3 | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base` | 6e 6.4's window; Stage 17's sitting C and pass 5 | about 8 |

A group lasts one apply, so each day's raise names every group its blocks call, and no other. The tunnel is
the user's ([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md)). A day ends where the
sitting can stop, and no block depends on a later day's.

#### N.9.3 Day 1: 6d and Stage 20

The blocks are [6d](../stages/stage-06d-unified-studio-remainder.md)'s "The combined Sandbox sitting: 6d's
items in order" and [Stage 20](../stages/stage-20-dbt-lineage.md)'s "Sitting A in order".

1. [Claude] The other sessions told, `make status`; [user] `make hub-up`.
2. 6d decision 6's apply of `production/networking/` ran with nothing up on 2026-11-20 (N.9.1); [Claude],
   right after `make hub-up`, the day re-plans it, `No changes`. The name reaches Squid at the association's next :00 or :30 with the host running, or at once by
   [Claude⚡] `start-associations-once`; only the count `PX-3` reads on the host proves a render
   (`SUP-071`).
3. [user] `make up ENV=sandbox GROUPS=mwaa` as soon as the hub reads up, beside step 2, which waits on no
   Sandbox slice; [Claude] `make status` after it.
4. [user] The spaces, created at once and each stopped when its steps end: 6d's JupyterLab on `ml.t3.medium` and remote-access
   Code Editor on `ml.t3.large` in `eighth-experimentation`, the contributor's remote-access space and one
   in `test-experimentation`; Stage 20's JupyterLab in `app-dbt-dev`.
5. [Claude] Decision 6's reading: `200 TCP_TUNNEL` on the portal's name from the new app, and no `403`
   after the render.
6. Stage 20's sitting A, once step 7's three runs are launched, its steps between the raise and the downs: 2.2 to 2.5, 3.1 on a split graph
   alone, 3.3, 2.6 if there is room, 3.4 and 4.5. About 3.5 hours, 35 minutes more with 3.1 and 2.6. Pass 3 gives 3.1's
   verdict, which 8.5 owes.
7. 6d 4.7, about an hour, most of it beside step 6: a background run, a schedule and a *Notebook
   Operator* workflow in `eighth-experimentation`, launched before step 6, their trail read in one batch;
   then, after step 6, the `PUBLIC_INTERNET_ONLY` negative from the space, with no deny in Sandbox before
   it: decision 17 (a) as it stands, the user's choice of 2026-11-19. The project role holds
   `datazone:StartNotebookRun` (N.12.3), so a refusal is DataZone's.
8. 6d 7.6 on the split-tunnel profile, about 20 minutes; then 7.5's monitored half in the window the
   orchestrating session announces, about 20 minutes, every shell on `proxy-on`.
9. 6d 7.7 after the portal's logout, read at 5 and 30 minutes, with [Claude] 6.1 (viii)'s Code Editor half
   from the flow log during the wait: about 35 minutes. It comes last because the logout ends every portal
   tab.
10. 6d's step 12: 4.7's schedule deleted, the spaces stopped, the portal tabs closed; then the lowering
    (N.9.6).

**Day 1 ran on 2026-11-21 to step 8**: Stage 20's sitting A whole, and 6d to 7.6. The user deleted the spaces
and lowered the estate before step 9. Step 8's 7.5 half, steps 9 and 10 are 6d's *The remainder after day 1*,
about 75 minutes on the base endpoint set, planned for the end of day 2, the user's choice of 2026-11-21, and
left unrun there (N.9.4). 7.7's sign-out ends every portal tab, so it comes after the sitting's last portal
work. The deep link is its one method (`SUP-398`), with Chrome relaunched on the proxy flag under the
monitored profile and the copy's portal tab watched (`SUP-399`).

#### N.9.4 Day 2: Stage 17's sitting B, its passes 2 and 3, pass 7, and 6d's remainder

The block is [Stage 17](../stages/stage-17-sandbox-machine-learning.md)'s "Sittings B and C as one
Sandbox sitting", its day 2 rows.

1. [Claude] The other sessions told; [user] `make hub-up`, then
   `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent`; [Claude] `make status`.
   `bedrock-agent` is pass 7's alone.
2. Stage 17's sitting B and pass 7: the opening with 1.4's and 0.5's readings and the spaces, 0.3 and 0.7, 1.6,
   2.1, 2.2 (a) and (b), [Claude⚡] the training pair's apply in `sandbox/workflows/`, 2.2 (c), 2.3's
   negatives, 2.4's JumpStart form, 3.1's second run and 3.2's registry, then pass 7. About 6.2 hours. The
   training pair's default flips to `true` in that day's pull request, or the next plan from `main`
   removes it (Lesson 79). 3.3 is read with nothing up after `eighth-experimentation`'s next source run,
   about 17:38 UTC.
3. 6d's remainder of day 1 (N.9.3), the user's choice of 2026-11-21: steps 1 to 4 of 6d's *The remainder
   after day 1*, about 75 minutes that call no group, Stage 17's space stopped when pass 7 ends; 7.7's
   sign-out comes after the day's last portal step.
4. Stage 17's closing reads, `./aws/sandbox-ml.py` and `./aws/catalog.py`, 2.5's `ML-3` among them; the
   spaces stopped and the portal tabs closed, 6d's step 12 with them; then the lowering (N.9.6).

**Prepared 2026-11-21 with nothing up** (Stage 17's log): `make status` at 0.0000 USD/h and every instrument
as expected; the training pair planned again from `main` at `0c78f571` with Terraform 1.17.2 and saved as
`$HOME/tmp/stage17-training-pair-preflight.tfplan`, `0 to add, 1 to change`, which applies while the slice's
state and `main`'s tree have not moved; `sandbox/egress/` planned with the four groups, 33 to add and 24
endpoints; and `$HOME/tmp/stage17-day2-extra_values.json`, the two values the space's clone needs. Readings
that shape the day:
- 3.2 comes about 3.7 hours into the day, so a start before about 13:30 UTC creates the group before
  `eighth-experimentation`'s source run of about 17:38; a later start leaves 3.3 to the next day's run.
- 2.4's JumpStart model defaults to `ml.m5.4xlarge`, which the ceiling refuses; `ml.m5.xlarge` is the
  submission that reads what the form fills.
- Pass 7's knowledge base, evaluation job, flow and chat agent run as the project's Bedrock service role,
  which invokes a model only through an application inference profile tagged with the project; the IDE's
  first use creates one, and `eighth-experimentation` holds Opus 4.5's alone.
- Each project's *Update project* banner, seen at 0.9's reading on 2026-11-21, stays unpressed: the press
  re-deploys the project's `Tooling` environment (`SUP-380`) and is 6d 2.4's after half, which Claude reads
  before and after.

**Day 2 ran on 2026-11-21 to 22** (Stage 17's and 6d's logs): steps 1, 2 and 4, pass 7 with 7.4b's fallback, a
knowledge base node in the existing flow on the user's word, after Agents Classic refused the chat agent
(`SUP-446`); the closing reads at 05:03 UTC and Sandbox's lowering from 05:08 to 05:15. Step 3 did not run,
the user's choice at 04:59 UTC, and 6d's remainder waits for a later Sandbox sitting on the base endpoint set
(6d's `Status`). 3.2 created the group at 00:18 UTC, so 3.3 reads `eighth-experimentation`'s source run of
about 17:38 UTC on 2026-11-22. The owner's *Update project* presses, 6d 2.4's after half, ran from 05:14 UTC,
read by the coordinating session.

#### N.9.5 Day 3: 6e 6.4, Stage 17's sitting C and its pass 5

The blocks are [6e](../stages/stage-06e-claude-code-bedrock.md) 6.4 and Stage 17's day 3 rows: sitting C,
9.6 and 10.4, then pass 5.

1. [Claude] The other sessions told; [user] `make hub-up`, then
   `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base`; [Claude] `make status`.
2. 6e 6.4's window, about an hour: one Claude Code session in a space on the default model, a task of
   real length over several turns, and no other Bedrock call in the account. 9.6's workflow (step 3),
   which calls none, starts just before the window and trains through it.
   Claude marks its start and end in UTC as the user reports them and reads `./aws/bedrock-usage.py` after
   the channels' publication lag. The token volume goes to Stage 12 decision due 2's ceiling, where 6e
   decision 6, taken 2026-11-17, leaves it.
3. Stage 17's sitting C: 9.6, `app-ml` trained, registered and scored in `app-ml-dev` (verification
   lx); then 10.4's deploy and its readings 1 to 6, each `sandbox/bedrock/` apply [Claude⚡], both switches
   back to `false` at the end; then pass 5 in `eighth-experimentation`'s space, the pipeline authored from
   the SDK, run and read back, and the editor's forms (5.1 to 5.4). About 6.2 hours.
4. Stage 17's closing reads, `./aws/sandbox-ml.py` and `./aws/catalog.py`; the spaces stopped and the portal
   tabs closed; then the lowering (N.9.6).

#### N.9.6 The lowering, each day

Every portal tab is closed first (`sagemaker-application.md` §D), then:

```bash
make down ENV=sandbox
make hub-down
make status
```

§R's readings follow. `make status` reads every account's Studio apps, so an app an open page restarted
after the down's hook shows there.

#### N.9.7 The sitting's cost

At [`cost-model.md`](../cost-model.md)'s "Per session" rates:
- the hub's two hosts and two addresses, 0.026 USD/h to 2026-11-21 23:23 UTC, 0.062 from 23:23, when the VPN
  host relaunched as a `t3.medium` (0.0416), 0.0724 from 23:53, when the proxy relaunched as a `t3.small`
  (0.0208), and 0.036 since 2026-11-22 01:16, when the VPN host returned to a `t3.nano` (0.0052) (launch
  times read 2026-11-22); and Sandbox's 18 endpoints, 0.180 USD/h, each day;
- the groups' endpoints at 0.010 USD/h each: day 1's one, day 2's six and day 3's four;
- each space's app, 0.050 USD/h on `ml.t3.medium` and 0.100 on `ml.t3.large`, 6d's remote-access spaces;
- a Config cycle of Sandbox's `[E]` slices each day, 0.36 to 0.87 USD whatever its length.

Before the spaces, day 1 bills about 0.22 USD/h, day 2 0.27, 0.31 after the rebuilds and 0.28 since the VPN
host's return, and day 3 0.26, some 1.4, 2.4 and 2.2 USD of hub and endpoints; with the spaces and the Config
cycle, 2 to 4 USD a day and 9 to 11 USD for the sitting. The models' tokens, the jobs and the embeddings are
billed apart, and 6e 6.4's session is the largest of them; Stage 17's training jobs are about five minutes of
`ml.m5.xlarge` each, at 0.23 USD/h.

#### N.9.8 What follows the sitting

N.6 items 5 to 11, in their order: R1 (N.11.1) after 2026-11-22, the subscriptions with nothing up, Stage
17 10.5 after day 3, N.10's two days before 2026-12-19, and R2 (N.11.2). Days 2 and 3 depend on none of
them, so R1 may come between day 1 and day 2.

### N.10 The Sandbox warehouse sitting, prepared 2026-11-19

Written with nothing up on 2026-11-19, the pre-flight of N.6 item 9 (pull request #339). It joins 5b's
test and re-plan, 6h's owed negatives and readings, Stage 19's pass 5 and Stage 21's passes 2 to 5, with
Stage 17's pass 4 and Stage 20's pass 5, which call no warehouse. Each day raises the hub and one `make up
ENV=sandbox GROUPS=redshift`, which brings `sandbox/egress/` with the `redshift` group, the warehouse's
compute and `sandbox/probes/`, and day 1 adds `mwaa` for Stage 20's run: no GitLab, no Staging or
Production egress. It shares no hub start with N.9, whose days already run six to seven hours. `make status` read 0.0000 USD/h
at 21:46 UTC that day. Each stage file holds its block step by step under "The Sandbox warehouse sitting",
and its stage log the readings; this section holds the days, the raises and the lowerings. Every command
runs as the infrastructure user (`InfrastructureAccess`) unless it names another identity, and each write
is Claude's on the user's word naming it, the other sessions on the laptop told first.

The blocks add up to about fifteen hours, so the sitting runs on two days. Each `make up` creates a new
usage limit, so each day starts at zero of its 10 RPU-hours.

#### N.10.1 What comes before the sitting

- **[user] The merges** of pull request #339 and of this section's, so every apply runs from `main`
  (Lesson 79). Done 2026-11-20.
- **[Claude⚡] `sandbox/warehouse/` applied from `main`**, with nothing up, on the user's word naming it:
  Stage 19 5.2's door, the access role's catalog read and `lakeformation:GetDataAccess`, which the user
  chose on 2026-11-19 (*"Sim, escreva"*, in the pre-flight's session) and pull request #339 writes,
  planned `0 to add, 1 to change, 0 to destroy`. The role held neither piece: simulated that day,
  `glue:GetTable` read `implicitDeny` on Sandbox's and Production's `trades_notional` and `allowed` on the
  lake's table, the control. Done 2026-11-20, 15:57:30 to 15:57:40 UTC, on the user's *"autorizo o apply no
  warehouse"*, re-planned `No changes`.
- **R1 and the subscriptions** (N.6 items 5 and 6): [user] Stage 19's pass 5 and Stage 20's read the
  product through `eighth-experimentation`'s and `app-dbt-dev`'s subscriptions, requested and approved in
  R1 after Production's leg (N.11.1 step 5); [Claude] Stage 20 5.1's model, archive and tar once 5.0's
  fulfilment names the resource link, before day 1.
- **N.9's day 2**: Stage 17's pass 4 serves the version 3.2 registered.
- **`sandbox/ml/`'s endpoint statements** (Stage 17 decision 7) ran from `main` on 2026-11-20 with nothing
  up (N.6 item 3): pass 4 creates an endpoint configuration and an endpoint.
- **[user] With nothing up:**
  - 6h decision 8 (a)'s window, taken 2026-11-22 as standing: pull request #363, merged 2026-11-22 at
    03:24 UTC, which also gives 5.2b's network door (N.12.4).
  - Sandbox's free-trial balance, before the sitting, after each day and the next day.
- **[user] The identities**: `eighth-experimentation`'s contributor in a browser profile of its own (6h
  0.4); the Data Scientist User signed in (6h 5.4).

#### N.10.2 The days

| Day | Raise | Blocks | Hours |
|---|---|---|---|
| 1 | `make hub-up`, `make up ENV=sandbox GROUPS=redshift,mwaa` | 5b; 6h to 0.4's portal half; Stage 19's pass 5 to 5.3; Stage 17's pass 4; Stage 20's pass 5 | about 7.5 |
| 2 | `make hub-up`, `make up ENV=sandbox GROUPS=redshift` | Stage 21's passes 2 to 5 and their closing reads; Stage 19's 5.4 with Stage 21's rollback; the subscriptions revoked | about 7.5 |

A breach of the usage limit deactivates the compute until its amount is raised; Stage 17's and Stage 20's
blocks call no warehouse, so they run on through one. The amount is the user's value: on a breach the
warehouse's remaining steps wait for the user's word on a raise for the day, a write, or move to day 2.

#### N.10.3 Day 1: 5b, 6h, Stage 19, Stage 17's pass 4 and Stage 20's pass 5

The blocks are the sections titled "The Sandbox warehouse sitting" in
[5b](../stages/stage-05b-redshift-serverless.md), [6h](../stages/stage-06h-redshift-connection.md) and
[Stage 19](../stages/stage-19-smus-native-data-product.md), then
[Stage 17](../stages/stage-17-sandbox-machine-learning.md)'s pass 4 and
[Stage 20](../stages/stage-20-dbt-lineage.md)'s pass 5.

1. [Claude] The other sessions told, `make status`; [user] `make hub-up`, `make up ENV=sandbox
   GROUPS=redshift,mwaa`; [Claude] `make status`.
2. [user] The spaces, each stopped when its steps end: a JupyterLab on `ml.t3.medium` in
   `eighth-experimentation` (6h 5.3, Stage 19's pass 5, Stage 17's pass 4), one in `test-experimentation`
   (6h 5.2b) and one in `app-dbt-dev` (Stage 20's pass 5).
3. [Claude] 5b's steps 1 and 2: `./aws/warehouse.py awsds-infra-sandbox-1 --sql`, then the re-plan of
   `warehouse-compute/`. A change in that plan stops every apply to the slice for the day, the wide tag's
   included. About 15 minutes.
4. [user; Claude] 6h's step 1, the editor's first session on `sandbox`, then 5b's step 3, the
   `max_query_execution_time` test. About 40 minutes.
5. 6h's steps 2 to 10: 5.2, 5.2a's owed half, 5.3, 5.4, 5.1's before half; [Claude⚡] the standing apply,
   `sandbox/warehouse/` then `warehouse-compute/`; 5.2b; 5.1's after half from `app-dbt-dev`'s space; 0.4's
   portal half. About 2 hours 10 minutes.
6. Stage 19's pass 5, steps 1 to 6: the session, `USAGE ON DATABASE awsdatacatalog`, 5.2's read with
   DataZone's grant alone (xiii), 5.1's Lake Formation half only on its refusal, the copy and the view, and
   5.3's source, which is Stage 21's 2.2. About 1 hour 25 minutes.
7. Stage 17's pass 4, 4.1 to 4.6: the endpoint from the SDK, which stays up after the sitting (decision
   6), the portal's form, the batch transform, the serverless and GPU negatives. About 2 hours. Simulated
   on 2026-11-20 as `eighth-experimentation`'s project role: `CreateModel`, `CreateEndpointConfig`,
   `CreateEndpoint`, `CreateTransformJob` and `CreatePipeline` `allowed` with the project's tag on the
   resource, and the GPU's endpoint configuration `explicitDeny` by the project boundary.
8. Stage 20's pass 5, 5.2 and 5.3: the model over the subscribed table deployed and run from
   `app-dbt-dev`'s space by 2.2's and 2.3's commands, its read and its graph read, then the listing's
   *Lineage* tab as a member of another project. About 45 minutes.
9. [user] Every space stopped and every portal tab closed, then the lowering (N.10.5). 5.1's grants, the
   copy and both subscriptions stay for day 2, whose 2.1 reads the copy and 3.3 the read in place.

#### N.10.4 Day 2: Stage 21

The blocks are [Stage 21](../stages/stage-21-redshift-s3-data-products.md)'s "The Sandbox warehouse sitting:
passes 2 to 4 in order" and its §5.

1. [Claude] The other sessions told; [user] `make hub-up`, `make up ENV=sandbox GROUPS=redshift`; the
   spaces in both projects.
2. Stage 21's block, steps 1 to 7: pass 2 from 2.1, the consumer's workgroup by 1.5's applies in 2.4's order
   and its removal by 2.9's, pass 3, pass 4 with 4.5's transfer role and then its key statement in
   `sandbox/data/` applied (decision 4 (b)) and 4.8 at once, then the
   closing reads (`list-workgroups`, `describe-clusters`, `WH-8`). About 4 hours 30 minutes. Then Stage
   21's pass 5: the prefix published from the `eighth-experimentation` space, the product requested from a
   `test-experimentation` notebook, approved, read and revoked, about two hours with the revocation's
   five-minute wait.
3. [user] Stage 19's 5.4 with Stage 21's rollback item 5: 5.1's grants revoked, then the view and the
   tables that item names dropped, `lab` kept (6h 6.4, taken 2026-11-22); then the subscriptions of N.6 item 6
   revoked, Stage 19 4.12's (by its 2.5) and Stage 20 5.0's, each read on both sides. Then the lowering
   (N.10.5).

#### N.10.5 The lowering, each day

Every portal tab is closed first (`sagemaker-application.md` §D), then:

```bash
make down ENV=sandbox
make hub-down
make status
```

§R's readings follow. `make status` reads no Redshift workgroup, so day 2's closing reads stand for the
consumer's workgroup and the managed compute, which no slice holds.

#### N.10.6 The sitting's cost

At [`cost-model.md`](../cost-model.md)'s "Per session" rates:
- the hub's two hosts and two addresses, 0.036 USD/h (N.9.7), Sandbox's 18 endpoints, 0.180, the
  `redshift` group's one, 0.010, and `sandbox/probes/`, 0.008: about 0.23 USD/h each day before the spaces,
  0.24 on day 1 with the `mwaa` group's endpoint;
- each space's app, 0.050 USD/h on `ml.t3.medium`, three of them on day 1;
- Stage 17 4.1's endpoint, hosting `ml.m5.large` at 0.115 USD/h from its creation until the member deletes
  it (decision 6), 2.76 USD a day, which neither `make status` nor `make down` reaches;
- a Config cycle of Sandbox's `[E]` slices each day, 0.36 to 0.87 USD;
- the warehouse: 1.44 USD per query-hour at 4 RPUs and 2.88 at 8, nothing idle, each day capped at 10
  RPU-hours, 3.60 USD; 6h's full day of 2026-10-10 burned 2.44 USD;
- Stage 21's consumer workgroup at the same rate with its 4 RPUs locked, and its decision 3 (b)'s managed
  compute, whose base capacity is unread: at 128 RPUs a query's 60-second minimum costs 0.77 USD. Neither is
  under the usage limit.

With the warehouse's queries running, a day bills about 1.7 USD/h. The days come to about 4.5 and 5 USD,
some 9.5 USD for the sitting, between 6.5 and 13, the managed compute the widest term and 4.1's endpoint
apart. The trial absorbs the
warehouse's share to 2026-12-19; whether it covers the two other compute objects is a reading.

#### N.10.7 What follows the sitting

1. **R2** (N.11.2), after Stage 17 10.5 and #321's merge in R1 (N.6 items 8 and 10).
2. The bill halves after 2026-12-19: 5b's verification x and 6h's xii; Stage 19's close (its sitting 12);
   Stage 21's close.

### N.11 The release sittings, read 2026-11-20

Written with nothing up on 2026-11-20 (N.6). Every owed step that needs GitLab is on one of two sittings,
each raising the hub, GitLab with the build runner and the targets' egress once for every tag it carries:
a tag pipeline's untagged jobs run on the build runner alone, so each is `make gitlab-up BUILD=1`
([`gitlab.md`](gitlab.md) §U), and `BUILD=1` lasts one apply. Each stage file holds its steps; this section
holds the order, the raises and the lowerings. Every command runs as the infrastructure user
(`InfrastructureAccess`) unless it names another identity, and each write is Claude's on the user's word
naming it, the other sessions on the laptop told first.

#### N.11.1 R1: release G, the rotation's reading and the GitLab chores

After 2026-11-22 01:59:59 UTC, the admin secret's first scheduled rotation in Production, and before
2026-12-17, when the newest GitLab backup leaves the bucket. It needs no Sandbox day before it, and
`app-dbt`'s release joins it only after N.9's day 1.

1. [Claude] With nothing up: N.8.3 step 1, `LastRotatedDate` on 2026-11-22; the other sessions told;
   `make status`. [user] Production's free-trial balance.
2. [user] `make hub-up`, `make gitlab-up BUILD=1`, the tunnel ([`gitlab.md`](gitlab.md) §U); the local
   user's password rotated before the first push (N.8.2 step 3).
3. [user] With GitLab up, in any order: a backup by hand ([`gitlab.md`](gitlab.md) §B), which [Claude] reads
   in the bucket; 6d 2.7's step 7, `release/versions.py`'s header by a merge request on `awsds/dev-env`, then
   the mirror (`gitlab/README.md`, *Changing a recipe*); `awsds/app-ml`, `awsds/app-genai` and
   `awsds/app-dbt` created by [`sagemaker-application.md`](sagemaker-application.md) §L's steps 1 to 6,
   with `awsds/infrastructure`'s job-token allowlist admitting each (Stage 20 8.7).
4. [user] Release G, N.8.5 step 4: the mirror at `main`, the template's merge request of eight files,
   `make up ENV=staging ONLY=egress`, the tag `v0.6.0`; `make up ENV=production ONLY=workloads-egress`
   before `production-gate`, then the gate. [Claude] N.8.5 step 5's readings of Production's leg.
5. [user] After Production's leg, `make up ENV=production ONLY=workloads-egress,warehouse-compute
   GROUPS=redshift`, so no run of the leg meets a warehouse; [Claude] N.8.3 step 3,
   `./aws/warehouse.py awsds-infra-prod --sql`, whose database half signs in as `dbadmin` through the
   rotated secret: `EXC-13`'s Production half. Then [user] `make down ENV=production
   ONLY=warehouse-compute`. In the same wait, N.6 item 6, which needs nothing up: [user] Stage 19 4.12's
   request from `eighth-experimentation` and Stage 20 5.0's from `app-dbt-dev` on the listing the leg
   created, each approved by the Governance Manager once 4.12's membership is in; [Claude] each
   fulfilment read on both sides, then Stage 20 5.1's model, archive and tar over the link 5.0 writes.
   When step 7 runs, 5.0's request waits for its `bundle` job: `app-dbt-dev`'s source imports the link
   as an asset (`SUP-197`), which the bundle would carry and its guard refuse (Stage 20 8.6).
6. [user] [Pull request #321](https://github.com/felipenoris/AWS-DataScience/pull/321) merged, its branch
   having taken `origin/main` by merge (it read `CONFLICTING` on 2026-11-20), so release G's leg ran the
   script it was read with; the mirror pushed at the merge, since the legs clone the scripts from it. The
   pull request teaches `scripts/deploy-application.py`, `scripts/model-chain.py` and their hooks `app-ml`,
   `app-genai` and `app-dbt` (Stage 20 8.1): `--self-check` printed every stage of every application `ok`,
   `app-etl`'s lines as on `main`. The pins read against the lint's release on 2026-11-18, `app-etl`
   (`196acee`), `app-ml` and `app-genai` (`37cb5a6`), each pass at `4613ddc` with their pipelines'
   options, so each moves to it at the application's next tag, `app-etl`'s after release G. Its successor
   `4401f91` ([pull request #29](https://github.com/felipenoris/awsds-workflows/pull/29), merged
   2026-11-21) adds the rule `operador`'s refusal of the native notebook operator (Stage 8 5.6, `TM-34`), and
   no application's lint has run at it yet.
7. When N.9's day 1 read Stage 20's passes 2 and 3, 8.5's verdict is written and 8.6's bundle rehearsed:
   `app-dbt`'s first push and branch pipeline (8.7), then its tag `v0.1.0` by 8.8, `staging/egress/` kept
   up from step 4 to the last Staging leg and `production/workloads-egress/` still up. Otherwise R2
   carries it.
8. [user] `make down ENV=staging` after the last Staging leg, release G's `staging-catalog` when step 7
   does not run; `make down ENV=production ONLY=workloads-egress`; `make gitlab-down`; the tunnel down;
   `make hub-down`. [Claude] `make status`
   and §R; [user] Production's free-trial balance after the last half-hour interval has closed, and again
   the next day.

#### N.11.2 R2: the first releases of `app-ml`, `app-genai` and `app-dbt`, and `app-etl`'s model half

After N.9's day 3 (9.6's candidate published, 10.4's readings), Stage 17 10.5's applies and #321's merge;
before 2026-12-18 when it carries `app-dbt`, or with that archive moved to dbt 1.12.

1. [Claude] The other sessions told, `make status`. [user] `make hub-up`, `make gitlab-up BUILD=1`, the
   tunnel.
2. [user] Each application's first push and branch pipeline, its merge request and its tag, in this order:
   `app-dbt`'s `v0.1.0` (Stage 20 8.7 and 8.8) unless R1 carried it; `app-ml`'s (Stage 17 9.7), whose bundle
   carries the candidate `app-ml-dev` last published; `app-genai`'s (10.6), whose `.gitlab-ci.yml` sets no
   `GATES_UV_PROJECTS`, so its pipeline runs no `pip-audit` and no gates tag comes first. `make up
   ENV=staging ONLY=egress` before the first tag and `make down ENV=staging` after the last Staging leg;
   `make up ENV=production ONLY=workloads-egress` before the first `production-gate`. Each raise names
   `GROUPS=bedrock-base` for `app-genai`'s legs, Staging's once Stage 17 10.5 gives `staging/egress/` the
   `optional_service_groups` variable, absent there and present in `production/workloads-egress/` on
   2026-11-20. [Claude] the
   readings per target after each leg (Stage 17's, and Stage 20's 8.9).
3. [user] `app-etl`'s release retiring its model half (Stage 17 9.11), last, once `app-ml`'s release holds
   the model in both targets; `app-etl`'s lint pin moves to `4613ddc` with it.
4. [user] `make down ENV=production ONLY=workloads-egress`; `make gitlab-down`; the tunnel down;
   `make hub-down`. [Claude] `make status`, §R, and 9.11's estate pull request, planned from a `main` that
   holds the release (N.6 item 11).

#### N.11.3 The sittings' cost

At the rates of [`gitlab.md`](gitlab.md) §U and [`cost-model.md`](../cost-model.md)'s "Per session": the hub,
0.036 USD/h (N.9.7); GitLab's session, 0.1961 USD/h, and its three runners with `BUILD=1`, 0.2493; Staging's
and Production's egress, 0.080 USD/h each while raised; a Config cycle of GitLab's `[E]` slices, 0.21 to 0.38
USD per sitting. A sitting of six to eight hours bills about 0.48 USD/h before the targets' egress, some 4 to
6 USD in all. R1 adds N.8.3's warehouse queries, at 1.44 USD per query-hour and nothing idle, against
Production's trial. The two replace the sittings of release G, of N.8.3 and of each application's first
release, each of which raised the same hub, GitLab and egress.

### N.12 The calendar and the overlaps inside each day, read 2026-11-20

Written with nothing up on 2026-11-20, when the user asked for the plan that takes the least time to run.
N.6's order stands; this section dates it, moves N.6 item 6 into R1's wait, and puts each day's waits
beside other work. What N.12.3 lists was read or built that day, so no sitting spends time on it.

#### N.12.1 The calendar

The earliest dates, each sitting on the day after the one it waits on. A sitting may slip; the dates that
bound it stay N.6's.

| Date | Sitting | Raise | Waits on |
|---|---|---|---|
| 2026-11-21 | N.9's day 1, run to 6d 7.6 | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa` | the user's acts of N.12.4 |
| 2026-11-22, after 01:59:59 UTC | R1 (N.11.1), N.6 item 6 inside it | `make hub-up`, `make gitlab-up BUILD=1`, Staging's and Production's egress, Production's warehouse compute after the leg | the rotation; N.9's day 1, for `app-dbt`'s release |
| 2026-11-23 | N.9's day 2, 6d's remainder at its end | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent` | Stage 17 0.9 |
| 2026-11-24 | N.9's day 3, then Stage 17 10.5 with nothing up (N.6 item 8) | `make hub-up`, `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base` | `app-ml-dev`'s MLflow App |
| 2026-11-25 | N.10's day 1 | `make hub-up`, `make up ENV=sandbox GROUPS=redshift,mwaa` | R1's subscriptions and Stage 20 5.1's tar; day 2's registered version; 6h decision 8 (a)'s merge, done 2026-11-22 (N.12.4) |
| 2026-11-26 | N.10's day 2 | `make hub-up`, `make up ENV=sandbox GROUPS=redshift` | day 1 |
| 2026-11-27 | R2 (N.11.2) | `make hub-up`, `make gitlab-up BUILD=1`, Staging's and Production's egress | 10.5's applies; #321 merged in R1 |

Then 9.11's estate pull request with nothing up (N.6 item 11). The seven metered days sit inside N.6's
dates: R1 before 2026-12-17, `app-dbt`'s release before 2026-12-18, N.10 before 2026-12-19.

Two pairs can share a day, the user's choice, since each keeps the user on two surfaces at once:
- R1 with N.9's day 2: R1's acts sit between its pipelines' legs, an hour or more each, and day 2's portal
  steps fill them; the hub starts once.
- R2 with N.10's day 2, the same shape: R2 waits on no result of N.10 (N.11.2 names its prerequisites).

With both, the plan runs in five metered days, 2026-11-21 to 2026-11-25. The cost barely moves: each raise
bills by the hour whichever day it runs, and each Sandbox day carries its own Config cycle either way.

#### N.12.2 The overlaps inside each day

Every day runs two tracks, the user's hands in the portal and Claude's at the terminal, joined only where a
step names the other's result. A trail or a log is read once per block, after its lag
([`log-debugging.md`](log-debugging.md)), never after each act. A run, a job or a pipeline that takes
minutes starts before the step that does not need it.

- **N.9's day 1** (N.9.3): `make up ENV=sandbox GROUPS=mwaa` runs right after `make hub-up`, beside
  Claude's re-plan and `start-associations-once`, since the render waits on no Sandbox slice; the spaces are
  created at once; 4.7's three runs are launched before Stage 20's sitting A, and Claude reads their trail
  in one batch while the user works in `app-dbt-dev`, the negative following when the user returns to
  `eighth-experimentation`; 7.7's thirty minutes hold Claude's 6.1 (viii) reading and the day's records.
  About an hour less than N.9.2's 6.5 hours, 4.7's hour being mostly compute starts and the trail's lag.
- **N.9's day 2** (N.9.4): the training pair's plan is read already (N.12.3); each training job, about five
  minutes, runs while the next notebook cell is written; 3.3 is read with nothing up after the source run
  of about 17:38 UTC, so the day does not wait for it.
- **N.9's day 3** (N.9.5): 9.6's workflow, which calls no Bedrock, starts before 6e 6.4's window and trains
  through it, since the window excludes other Bedrock calls alone; 10.4's and pass 5's calls follow the
  window's end.
- **N.10's day 1** (N.10.3): pass 4's endpoint, minutes to create, starts before Stage 20's pass 5. The
  usage limit's amount is the user's value ([`redshift-connection.md`](redshift-connection.md)): on a
  breach the warehouse's remaining steps wait for the user's word on a raise for the day, a write, or move
  to day 2, while Stage 17's and Stage 20's blocks run on.
- **N.10's day 2** (N.10.4): Stage 21 pass 5's five-minute revocation wait holds the closing reads.
- **R1 and R2**: a release's legs run an hour or more each. R1's GitLab chores (N.11.1 step 3) fill the
  first leg's wait, and N.6 item 6, which needs nothing up, fills the time after Production's leg (N.11.1
  step 5).

#### N.12.3 What was read and built with nothing up on 2026-11-20

Each reading is in the log of the stage that owns it.

- **The instruments**, every check as expected with everything down: `studio`, `remote-ide`, `warehouse`,
  `catalog`, `cicd`, `deploytargets`, `orchestration`, `devenv`, `egress`, `vpn`, `datalake`,
  `sandbox-orchestration`, `sandbox-ml`, `bedrock-usage` and `bedrock-scope`. `OR-2`'s five fails are
  `EXC-25`'s; `DE-2` fails while `sandbox/egress/` is down; the persona profiles' calls fail with no sign-in
  on their session.
- **The commands**: the 134 distinct `aws <service> <command>` this runbook and the stage files of 5b, 6d,
  6e, 6h, 17, 19, 20 and 21 name exist in the laptop's `aws-cli/2.37.12`; a made-up command, the negative
  control, read *"Found invalid choice"*.
- **N.9's day 1**: 4.7's negative runs as written. Simulated with no resource named,
  `eighth-experimentation`'s project role holds `datazone:StartNotebookRun`, `ListNotebooks`,
  `GetNotebook` and `CreateNotebook` through `SageMakerStudioProjectRoleMachineLearningPolicy`'s
  `datazone:*Notebook*`, the boundary and the organization allowing, and the Data Scientist's permission
  set holds none, so a refusal of the negative is DataZone's, never IAM's. With the domain's ARN named the
  same calls read `implicitDeny` naming no statement, `SUP-008`'s reading of an action with no resource
  type. The laptop's client: VS Code 1.146.0 in `/Applications`, its executable `Code`, with no Remote -
  SSH, no AWS Toolkit, no pinned 1.119.1 and no `proxy-on` in `~/.zshrc` (N.12.4); 6d's step 9 reads the
  executable's name from the bundle.
- **N.9's day 2**: the training pair's plan from `main`'s tree at `5dfff219`, `-var
  training_pair_enabled=true`: *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.workflows`
  gaining `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject` alone; the
  default plan `No changes`. Saved as `$HOME/tmp/stage17-training-pair-preflight.tfplan`, it applies on day
  2 only while the slice's state and `main`'s tree have not moved; Terraform refuses it otherwise, and the
  day plans again. The evaluation dataset's URL answers 200. Terraform 1.17.2, on the laptop since
  2026-11-21, refuses the file 1.16.6 wrote (`SUP-403`); the pair was planned again with 1.17.2 and saved
  on 2026-11-21 (N.9.4).
- **N.9's day 3**: 6e 6.4's baseline, `./aws/bedrock-usage.py` from 2026-11-01 to 20:16 UTC: 0.0005 USD
  computed over one to four invocations per model. Sandbox's application inference profiles are three,
  the domain's Haiku 4.5 and Nova Lite of 2026-10-19 and `eighth-experimentation`'s Opus 4.5 of
  2026-10-30, none of `app-genai-dev`'s (N.12.4). `./aws/sandbox-ml.py` gained `ML-10` and `ML-11`,
  Stage 17's 9.9 and 10.9 halves, so day 3 reads 9.6's and 10.4's objects with it: at 21:04 UTC every
  call returned, two passes and nine notes for what 9.6 and 10.4 create.
- **R1**: `./scripts/deploy-application.py staging --check` and `production --check`, each project's
  values read and the infrastructure user a member; `./scripts/check-gitlab-mirror.py --plan`, `GM-1` to
  `GM-8` passing, the house image's literal equal to the account's 73 names. Pull request #321's branch took
  `origin/main` at `5dfff219` by merge (`00113780`), its one conflict in
  [`sagemaker-application.md`](sagemaker-application.md) §S's table; `--self-check` printed every stage of
  the four applications `ok`, `app-etl`'s nine variables per stage as on `main`, and `make check` passed. R1's
  step 6 syncs it again with whatever `main` gained since.
- **R1 and R2's gates**: `pip-audit` 2.10.1 over each lock's runtime set (`uv export --frozen --no-dev`), an approximation of
  the gates' job, which `awsds/ci-gates` holds: *"No known vulnerabilities found"* for `app-etl` (one
  package), `app-ml`'s `code` (48) and `app-dbt` (78), at 20:36 UTC. The gate itself runs on the laptop
  the day of each tag, before the tag (Lesson 77).
- **N.10's day 1**: 6h 5.2b's door, read in `sandbox/warehouse/`'s code (N.12.4). `app-dbt-dev` holds
  the `Tooling` and `SageMakerAIDomain` environments alone, so Stage 20 2.1's *Create database* makes its
  first `DataLake` environment, which carries the subscription target 5.0's link lands in (`SUP-184`).

#### N.12.4 The user's acts before each day

The waiting list holds each as a row. In the calendar's order:

- **Before N.9's day 1**:
  - Stage 20 2.1, done 2026-11-21, its source's minute 02:43 UTC, which the sitting's runs keep clear of;
  - the client for 6d 7.5 to 7.7 ([`remote-ide.md`](remote-ide.md) §W): Remote - SSH and AWS Toolkit in a VS
    Code whose settings carry `remote.downloadExtensionsLocally` and `remote.SSH.localServerDownload`. The
    pinned 1.119.1 is a choice, not a prerequisite, and the current client serves 7.5's reading, which is the
    session's source address and its `CONNECT`s;
  - `proxy-on` and `proxy-off` in `~/.zshrc`
    ([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md) §4.1 [b]), which 7.5's window
    runs in every shell;
  - 7.6's contributor in a browser profile of its own, and the monitored profile's tunnel in the WireGuard
    app ([`vpn.md`](vpn.md) §C7).

  All taken by day 1, read 2026-11-21: Remote - SSH 0.128.0 and AWS Toolkit 4.20.0 with both settings,
  `proxy-on` in `~/.zshrc`, the tunnels `mbp` and `mbp-split-tunnel` in the WireGuard app.
- **Before 6d's remainder** (N.9.3): nothing new. Chrome's proxy flag is typed in the window itself
  ([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md) §4.1 [c]).
- **Before R1**: Production's free-trial balance, read 2026-11-21 at 299.18 of 300.00 (Stage 9's log);
  Stage 19 4.12's membership, which R1's approval needs, done 2026-11-21 (Stage 19's log).
- **Before N.9's day 2**: Stage 17 0.9, read 2026-11-21 (Stage 17's log).
- **Before N.9's day 3**: `app-ml-dev`'s MLflow App; and, before 10.4's deploy, `app-genai-dev`'s first
  call to Nova Lite, which creates the project's application inference profile whose ARN 10.4's
  `DEV_MODEL_ID` names (`examples/app-genai/README.md`). Which portal act counts as that first use, the
  playground's or a notebook's, is read on the day.
- **After N.9's day 3**: Stage 17 10.5's threat-model acceptance and each target's retention mode.
- **Before N.10's day 1**: N.10.1's acts, and 6h decision 8 (a)'s merge, done 2026-11-22. `sandbox/warehouse/`'s security group
  admits port 5439 from the spaces of the projects in `projects` alone, `eighth-experimentation` today, so
  `test-experimentation`'s notebook reaches no workgroup whatever its grant, and 5.2b as written reads the
  network's timeout, not the schema's verbs (Lesson 42). The wide tag admits every project at the IAM layer
  and lets `projects` take a second entry: `test-experimentation` in `projects` within the wide tag's
  applies of 6h's steps 5 and 9 gives it the door, with its access-role policies, at no extra apply.
  The user took decision 8 (a)'s window as standing on 2026-11-22 (pull request #363):
  `test-experimentation` joins `projects` at 6h's step 7, which gives it the rule, and the tag stays.

## Q. After the quotas: Stage 10's pass 3

The quotas are above zero since 2026-10-24 (§0.2), and pass 3 is the data release's (§V steps 3, 6 and 7).

## R. The readings at the end of every sitting

```bash
./aws/egress.py awsds-infra-prod awsds-infra-staging awsds-infra-sandbox-1
```

Zero burn in every account the sitting raised, no interface endpoint left, no NAT gateway anywhere;
then the stage's own instrument (`cicd.py`, `deploytargets.py`, `orchestration.py`, `datalake.py`,
`warehouse.py` after §W), `make status`, and the log entry of each step, in the sitting it ran.
`make status` also lists each EMR Serverless application started and each OpenSearch Serverless
collection, which a portal deployment leaves and `make down` never deletes. After a
Sandbox sitting, no Studio app in any of Sandbox's domains, nine across its six projects on 2026-11-20,
since an open portal page starts one again after the down's hook (N.3 step 10). The loop reads the domains
rather than naming them:

```bash
for d in $(aws sagemaker list-domains --query 'Domains[].DomainId' --output text --profile awsds-infra-sandbox-1 --region us-west-2); do aws sagemaker list-apps --domain-id-equals "$d" --query 'Apps[?Status!=`Deleted`].[SpaceName,AppType,Status]' --output text --profile awsds-infra-sandbox-1 --region us-west-2; done
```
