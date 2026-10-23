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

| § | Holds |
|---|---|
| [§0](#0-before-any-sitting-with-the-environment-down) | what runs today, with nothing up: the persona proofs, the quota requests, the flag of decision 13 |
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
when both accounts read them above zero.

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

## H. The hub and GitLab

`make hub-up`, then `make gitlab-up`, the tunnel, in [`gitlab.md`](gitlab.md) §U's order. What this
sitting closes besides Stages 8 to 10 is the waiting list's Hub and GitLab rows.

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
   editor validates it before the push; its branch pipeline runs the test stage alone.
3. **[user] The house image `default-v0.9.0`** with the 72-name `NO_PROXY` literal (Stage 8 1.1, Stage
   17 decision 4), registered as version 10: the merge request on `awsds/dev-env` from the copy under
   `gitlab/awsds/dev-env/`, the steward's tag, the release gate; `./scripts/gitlab-mirror.py` after the
   merge. `DE-5` turns green with it.
4. **[user] The deploy image on Terraform 1.16.6**, once the laptop runs it (the user's install;
   `upstream-releases.md`): the two pins in `gitlab/awsds/deploy-image/Dockerfile`, the merge request,
   the tag, its digest into `production/runners/` and a `production/runners/` apply. Until then the
   deploy image runs 1.15.8, which every slice's `versions.tf` admits.
5. **[Claude]** `./aws/cicd.py` after the runners' boot (`CI-1`, `CI-9`), and `GM-1` to `GM-8` on the copies.

## P. Production: Stage 9's pass 3 and Stage 10's 0.5

`make up ENV=production` raises `egress/`, `workloads-egress/` (16 to add, the seven endpoints and
the DNS Firewall), `runners/` and `probes/`, leaves the hub alone (refusal 6) and holds
`warehouse-compute/` (refusal 9). The sitting needs the hub up for `make up`'s check and nothing else
of §H.

1. **The flag on in Production** (§0.3, done 2026-10-23), `DT-5` read again at the sitting.
2. **[Claude⚡] `production/sagemaker/` applied** as `awsds-infra-prod` from a fresh plan (Recipe A):
   the proof job added and the job role's `CommitTheIcebergWrites` statement changed, read 2026-10-23
   as *1 to add, 1 to change*.
3. **[Claude⚡] The script uploaded** by the infrastructure user, the one principal the bucket's branch
   and the data key admit to `applications/*` from the laptop, the key the job's `script_location`
   names (`terraform -chdir=terraform-live/production/sagemaker output -raw producer_proof_script`):

   ```bash
   aws s3 cp terraform-live/production/sagemaker/proofs/producer_proof.py s3://awsds-prod-outputs/applications/stage-09-proofs/v0/glue/producer_proof.py --profile awsds-infra-prod --region us-west-2
   ```

4. **[user] `make up ENV=production`**, as the infrastructure user, the hub up.
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
6. **[user] The drop** (Stage 9 2.5's first half), from a laptop as the Data Scientist User in Sandbox:

   ```bash
   aws s3 cp examples/app-etl/samples/trades.csv "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" --profile awsds-scientist-sandbox --region us-west-2
   ```

   and 2.6 at once, before the pickup empties the letterbox, the same session reading back what it wrote:

   ```bash
   aws s3 cp "s3://awsds-data-dropbox/incoming/$(date -u +%Y/%m/%d)/trades.csv" - --profile awsds-scientist-sandbox --region us-west-2
   ```

   expected refused, the implicit deny of Stage 5a pass 4d.
7. **[Claude⚡] The pickup run** (2.5), `--arguments '{"--MODE":"pickup"}'` on the same command, then its
   readings: the keys the job listed, the rows read (the KMS half: a refusal on the lake key surfaces
   as an S3 error naming the object), the rows curated, each key gone after its delete (`404` on the
   `head-object`). `EXC-02`'s three `.txt` objects are not CSV and stay: the row retires with a
   deliberate `InfrastructureAccess` cleanup once the pickup has run, as `AWS_STATE.md` has it.
8. **[Claude]** `./aws/deploytargets.py`, `./aws/datalake.py` (`DL-5` after a run that vended
   through the lake), the table's rows read as the persona through Athena (5.4's first query), and the
   run's events in CloudTrail; `./aws/egress.py` §6 before `make down ENV=production`.

## T. The tag: Stage 8's pass 4 with Stage 10's passes 1 and 2

Needs §H done (the legs on `awsds/app-etl`'s `main`, the mirror pushed, the memberships), the hub,
GitLab and the runners up, and Sandbox's `egress/` up (`make up ENV=sandbox ONLY=egress`, the
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
   application and orchestration slices applied, INT-14 in Staging, Stage 10 verification ii),
   `staging-test` (3.3: the chain's machine started and followed, Stage 10 decision 19), `staging-down`
   (3.4). What is read at this leg and nowhere before: whether `uv run` resolves the dev group on the
   runner, the deploy role's Cloud Control and Glue calls against their grants, the worker's preparation
   with no `ecr.*` endpoint (Stage 10 verification xvi), `TriggerMode`'s literal, the key's encryption
   context in the saver's and the worker's calls (Stage 10 decision 2), and Staging's `release.auto.tfvars.json`
   kept as an artifact (the `VersionId`s 3.7 records).
4. **[user] The gate** (3.5): `production-plan` read beside `staging-test`'s artifacts, then
   `production-gate` by a `deployment-managers` member. Before `production-deploy`: `make up
   ENV=production` by the user (§P's step 4 if the sitting is one), since a Production run needs
   `workloads-egress/`.
5. **[pipeline] `production-deploy`** (3.6, `awsds-deploy-prod`): the service-linked role's creation
   in the deploy role's session on Production's first `CreateWorkflow` (Stage 10 1.5's statement, 1.6's
   record), then `production/orchestration/` with the chain's schedule `ENABLED`; verification vi,
   `CI-8` diffed across the run (INT-08).
6. **[user] 3.7**: both `release.tf`s committed with the tag, the digest, the bundle's SHA256 and the
   Staging and Production `VersionId`s from the two legs' artifacts; the mirror pushed again.
7. **[user] 3.8**: the by-hand parity once, the sequence in Stage 8 3.8, as `awsds-infra-staging`.
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
2. **[Claude⚡] `production/warehouse/` applied** (9 to add) as `awsds-infra-prod`, by hand; the
   refusal-9 row removed from `layers.py` in the same sitting; `EXC-13`'s Production row written.
3. **[user] `make up ENV=production GROUPS=redshift`**: `warehouse-compute/` with the namespace in
   place, and the `redshift-serverless` endpoint in VPC-Workloads for a job that calls the API (9.1).
   The usage limit counts from zero with each workgroup.
4. **[Claude⚡] 9.3's SQL** through the Data API with the admin secret, the statements in the step:
   the `PUBLIC` revokes on the three databases, `governed`, the owner user, the schema with its quota,
   the role, the two database users, the default privileges.
5. **9.5's shape** (decision 5, the datashare) and 9.5a's reading first; 9.6's pair; 9.7's INT-24 from
   a Sandbox project; 9.8's paperwork; `./aws/warehouse.py --sql` and its burn line beside `egress.py`
   §6; `make down ENV=production` before the sitting ends, the only guard that is not a setting.

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
