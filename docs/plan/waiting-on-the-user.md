# Waiting on the user

Every item, across stages, that only the user can take: a decision, an act in a console or a portal, a
sign-in as another persona, a request to AWS. Recorded on 2026-10-18 at the user's request, to be taken
later. A row is added when a session stops on one and removed in the sitting that takes it; the stage's
own Decisions-due table keeps the reasoning and the recommendation.

## Items that hold up an apply or a run

| Item | Where | What it holds up |
|---|---|---|
| Which principal the data cells filters bind, and whether the row half is a Lake Formation RLS policy | [Stage 11](stages/stage-11-dlp.md) decision 12, re-read 2026-10-26 under 6f's (b); its inputs arrived 2026-10-27: 6f 11.9 read, and 6f decision 2 keeps `restricted` and `personal` data off the catalog road | pass 1's two lake applies and 2.3's proof; the code is written and creates nothing |
| The three Claude 5.5 model agreements (Sonnet 4.5 is Legacy since 2026-10-08) | [6e](stages/stage-06e-claude-code-bedrock.md) decision 17, PR #108 | PR #108's applies and the image's model pins; the PR conflicts with main in `CLAUDE.md`, `docs/AWS_STATE.md` and `docs/log/INDEX.md` (read 2026-10-18), for its session to resolve when the agreements arrive |

## Decisions

| Item | Where | Why it matters |
|---|---|---|
| `TM-17`: deny `sqs:SendMessage` and Bedrock's cross-account `lambda:InvokeFunction` outside the organization, or accept the channel | Stage 11, [`threat-model.md`](threat-model.md) | the project role's AWS-managed policy reaches other accounts' `airflow-celery-*` queues and `amazon-bedrock*` functions today, and no SCP narrows it |
| Whether Sandbox's `InfrastructureAccess` stays a contributor of both Sandbox projects, added in the portal on 2026-10-15 | 6f, [6h](stages/stage-06h-redshift-connection.md) `EXC-17`, [INT-25](integrations.md) | it opens the projects' connections and assets to the infrastructure user; the instruments now read them from that session |
| The connection's `lineageSync`, daily at 03:43 UTC and failing: off in the portal, or kept | 6h decision 3 | a query on the 1.44 USD/h meter whenever the workgroup is up at that minute |
| The connection's database, `dev`, where a session reads no governed share: select `sandbox` in the Query editor each time, as `redshift-connection.md` §P says since 2026-10-26, or measure a member's `UpdateConnection` of it, a full-replace call (Lesson 60) | 6h, Stage 9 9.7 | a project's first governed read, refused for want of `TEMP` in `dev` (Stage 9 xxiv's positive control) |
| 6g 2.4's Athena read: the persona's from a laptop, or the project role's through 6f step 11's subscription, read from the query editor on 2026-10-26 (11.10), which the portal's query editor runs with no space (Stage 18 7.2) | [6g](stages/stage-06g-access-by-identity.md) 2.4 | as written it is refused, since the project role holds no Lake Formation grant on the lake |
| D12's budget notification and its threshold, a Management console object | 6e decision 6, [Stage 12](stages/stage-12-observability-finops.md) 2.1 | the estate's only spend alarm notifies nobody |
| D12's revision trigger, which fired: the bill read 53.31 USD in August and 74.48 in September from the six profiled accounts, Management, Log Archive and Audit unread, above the 50 USD ceiling | [D12](decisions/D12-budget-ceiling.md), Stage 12 4.2 | the ceiling every cost argument in the plan cites |
| Stage 12's decision due 1, the proxy status-check alarm's action (recommended: `notBreaching`) | Stage 12 | the `[D]` hosts' alarm actions at the next hub session |
| Bedrock invocation logging, due since the threat model exists; decisions 3, 6, 7, 8 and 13 (the warehouse's query record: the empty groups or the S3 Tables feed, measured first) | Stage 11 decision 11 | step 5's trails and alarms |
| Decisions due 2 (its formal close), 3, 4, 6's residual name, 9, 10, 12 and 13 | [6d](stages/stage-06d-unified-studio-remainder.md) | step 10, the Amazon Q door, `EXC-10`'s scope |
| When to spend the Redshift free trial; how a second project is admitted to the warehouse | [5b](stages/stage-05b-redshift-serverless.md) decision 9, 6h decision 8 | 6h step 5's negatives 5.1 and 5.2b; decision 8 (a)'s layer-2 argument is gone, AWS's managed project policy granting `GetCredentials` to every project under the wide tag (PR #187), so (a) now rests on the schema `GRANT` alone for the notebook doors, the access role still gating the Data page |
| The four Anthropic direct-API names on the compute plane: remove them, or accept with a trigger | `TM-04`, 6e | a session can run outside every Bedrock control |
| `EXC-10`'s repair; conformance packs; AWS Backup and its Vault Lock; the layer letters (decision due 3, recommended: keep every letter) | Stage 12 3.1, 5.2, 6.2, 8.x | the rest of Stage 12 |
| GuardDuty's decisions 1-4, the fourth whether the enablement is the console acts or the Organizations policy type of 2026-10-01 (recommended: step 1 as written, steps 2 and 3 by the policy, authored in Audit's GuardDuty console) | [Stage 15](stages/stage-15-guardduty.md) | the whole stage, and Stage 11 step 4 |
| 6e decision 11: carve one probe principal out of `DenyInvokingModelsThatRetain` for one sitting and invoke the Fable profile as it, or accept the vendor's sentence with its date (recommended: the carve-out) | 6e | the only negative control `mode: none` can have; the probe may meet `EXC-08`'s commercial gate before the retention mode |
| 6e decision 13, taken by Claude on 2026-09-12 and never reviewed: only `bedrock-runtime` carries an action scope, not the `bedrock` control-plane endpoint | 6e | `PutModelInvocationLoggingConfiguration` still traverses that door; five weeks of readings show only `ListInferenceProfiles` through it |
| `TM-01`: `-n` on the allow-list planes' `dstdomain` ACL, so a raw address matches no name (never on the deny-list ACL, which it would widen) | Stage 11, [`threat-model.md`](threat-model.md) | the proxy may admit a raw public address whose reverse record names an allowed host (inferred, unexercised); the change replaces the proxy host, so it rides the hub sitting's `production/proxy/` apply |
| Stage 17's decisions 5 (keep or delete at close), 6 (the endpoint's lifetime), 7 (the grants the measurements name), 10 (the Function entry) and 12 (the vector store), each recommended and none taken | [Stage 17](stages/stage-17-sandbox-machine-learning.md) |
| Stage 11's decisions 1 (Macie's mechanism), 2 (its results repository), 5 (Malware Protection on the drop-box) and 9 (ECR enhanced scanning), each recommended; then Macie's acts 1.1 to 1.4 in Management and Audit | [Stage 11](stages/stage-11-dlp.md) |
| At 6f 11.12's rollback: the `dev/` registration the Data OU keeps, accepted as a residue or the deny amended for that sitting (battery phase 4b) | [6f](stages/stage-06f-data-governance.md) step 11.12 | the rollback's last object |

## Acts only the user can perform

| Act | Where |
|---|---|
| Activate the cost allocation tags in Management's Billing console; the analyzer in Audit | Stage 12 4.1, 7.1 |
| Read Cost Explorer for August and September in Management, Log Archive and Audit, the accounts no CLI profile reaches | Stage 12 4.2 |
| The persona's refused job and its implicit-deny attempt | 6d 1.1, 1.2 |
| 6h 5.3 and 5.4's real attempts, for the refusals' wording, with the compute up (the simulator read both as designed on 2026-10-18) | [6h](stages/stage-06h-redshift-connection.md) |
| Step 2's portal acts: a consumer project, a subscription, an approval as the Governance Manager, whose project membership hands that user the project role (Stage 18 6.1) | 6f step 2, 4.3 |
| 0.4's portal half; 6.4, keep or drop `lab` | 6h |
| The domain name | [Stage 13](stages/stage-13-public-web-tier.md) |
| The account quota, D34's rung (recommended: the auto-enrollment rung), and the Account Factory product's reading in Management | [Stage 14](stages/stage-14-sandbox-vending.md) |
| 6d 6.1 (xvii), the `GetEnvironmentCredentials` attempt; an optional new Querybook quota request | [6d](stages/stage-06d-unified-studio-remainder.md), `docs/SMUS.md` |
| Stage 12's 2.4 (provoke one alarm of each class once, after the `[D]` hosts' wiring), 8.4 (the RTO tests for GitLab, the Terraform state and the lake) and 8.5 (rotate the internal CA's root once) | [Stage 12](stages/stage-12-observability-finops.md) |
| Read Production's Redshift free-trial balance in the console before and after a warehouse sitting (5b decision 9), and again the next day: 299.50 of 300.00 on 2026-10-30, Stage 9 xxiv's sitting 0.16 USD in all (299.66 before it, 299.54 38 minutes after), the window open since the namespace's creation on 2026-10-23 and closing 2027-01-21; the next pair at the next warehouse sitting ([`runbooks/promotion.md`](runbooks/promotion.md) §N.8.3) | [Stage 9](stages/stage-09-deployment-targets.md) step 9, 5b |
| The CI/CD CLI remedy and Stage 8 3.3's snapshot pin, both taken 2026-10-26 and written in PR #269 (the upstream report posted by the user the same day as [aws/CICD-for-SageMakerUnifiedStudio#413](https://github.com/aws/CICD-for-SageMakerUnifiedStudio/issues/413)): the template's merge request on `awsds/app-etl` and the next tag, carrying `scripts/dev-cli.sh` beside the manifest, which answers the lookup and calls the house CLI by its path, and the Glue job's record of the `curated.trades` snapshot it read, carried into the summary and the report, its `--SOURCE_SNAPSHOT` pin kept (option A: no change to the leg, the chain or the workflow; the parity of Staging and Production by id waits until it is a requirement). The remedy's third part, the activation hook, shipped in `default-v0.10.0`, Sandbox's version 11 (2026-10-26) | [Stage 10](stages/stage-10-orchestration-promotion.md) 2.1, [Stage 8](stages/stage-08-cicd-pipelines.md) decision 22 and 3.3 |
| Delete Stage 18's two clones under `$HOME/tmp/` | [Stage 18](stages/stage-18-staging-deployment-project.md)'s log, 2026-10-22 |

## Sittings with the environment up

Owed items Claude can take only with metered resources running, grouped by the sitting that raises them
so one start closes as many as it can. Starting a sitting is the user's call: it is metered
([`cost-model.md`](cost-model.md), "Per session", holds the rates), and the tunnel and the portal acts are
the user's hands. Each row names what must be decided or done first. The sittings that close Stages 8,
9 and 10, in order and command by command, are [`runbooks/promotion.md`](runbooks/promotion.md).

| Sitting | Raised by | What it closes | First |
|---|---|---|---|
| Hub | `make hub-up` | [Stage 12](stages/stage-12-observability-finops.md) 2.2's `[D]` half on `production/vpn/` and `production/proxy/` (`EXC-19`). The `production/proxy/` apply replaces the host (`user_data_replace_on_change`), so one apply carries 6g decision 1's replacement, the status-check alarm's action and its missing-data setting, and `TM-01`'s `-n` if it is taken. | Stage 12 decision due 1; `TM-01` |
| GitLab | `make gitlab-up`, after the hub | Stage 12 2.2's alarm action on `production/tooling/`, with the host started. A backup before 2026-11-26, when the newest, of 2026-10-26 22:15 UTC, leaves the bucket; the timer's at 03:00 UTC with the host up or `gitlab-backup create` by hand in an SSM session. Stage 8 decision 29's second reading: the merge request on `awsds/dev-env` carrying the copy's `sts-global-probe`, which prints each refusal and goes on, then the job (decision 29 applied 2026-10-27) | — |
| Sandbox | `make up ENV=sandbox ONLY=egress`, after the hub and GitLab, with `GROUPS=mwaa` for a deploy from a space; Stages 7, 9 and 10's items ran on 2026-10-26 ([`runbooks/promotion.md`](runbooks/promotion.md) §N.3), and the next sitting is §N.7.3 | 6d 5.1, 6.1 (viii), 7.5's monitored half, 7.6 and 7.7; Stage 12 9.1's interface-endpoint reading; Stage 17's 1.4 and 1.6 with `GROUPS=mlflow` (the first tracking call into `ml-demo-mlflow`), then passes 2-5; Stage 17's 0.3, 0.5's interface half and 0.7, and pass 7's 7.4 to 7.4c and 7.6; 6e 6.4's real assistant session with `GROUPS=bedrock-base`, whose token volume sets 6e decision 6's threshold (8.3) | 6f decision 1 before 6g 2.4 |
| Warehouse | `sandbox/warehouse-compute/` up, inside a Sandbox sitting | 5b's `max_query_execution_time` test (a long query over a user table, as a non-superuser and as the admin) and the `enable_large_strings_opt_in` re-plan; 6h's negatives 5.1 and 5.2b; after 2026-11-22, `EXC-13`'s Production half | 6h decision 8 before the negatives; 6h decision 3 if the sitting spans 03:43 UTC |
| Staging | `make up ENV=staging ONLY=egress`, after the hub | Since Stage 8 decision 27 (2026-10-24), every promotion's leg: `make up ENV=staging ONLY=egress` before the tag, `make down ENV=staging` after it | — |
| Promotion | `v0.3.3` (§T, pipeline #71) and the data release `v0.4.2` (§V, pipeline #80, after #74 and #77 stopped in their legs) reached Production; `v0.4.4` (#85) ran decision 27's legs, `v0.4.5` (#87) answered verification ix, and `v0.4.6` (#102, §N.1) closed `EXC-22`, Stage 8 xxiv, Stage 9 xii and Stage 10 xi's CI half | With the next tag: the template's merge request with the deploy script, the snapshot record and the fixed proxy checks; Stage 8 xv (the proxy stopped alone), xxvii's plan half once the Amazon Linux parameter moves; Stage 10 xx's second half (an undeclared Glue job on a branch's tag), both exercises in [`runbooks/promotion.md`](runbooks/promotion.md) §N.8.2 step 12 | the mirror's push; the template's merge request |

## Dates

| Date | What happens |
|---|---|
| 2026-11-01 | Stage 11 2.1.3's internal-access analyzer bills at setup and on each 1st: create it after this date, delete it before 2026-12-01 |
| 2026-11-22 | `EXC-13`'s Production half: the admin secret's first rotation in Production, with or without a workgroup; whether the database took the password is read at the first warehouse sitting after it (Stage 9 9.1, 9.8) |
| 2026-11-13, 2026-11-15, 2026-11-25 and 2026-11-26 | the GitLab backups of 2026-10-13, 2026-10-15, 2026-10-25 (03:01 UTC) and 2026-10-26 (01:53 UTC, 8.2's fresh one, the restored host's baseline, and 22:15 UTC, the GitLab sitting's by hand) expire, 31 days each; with GitLab down past 2026-11-26 no current backup is left |
| 2026-12-19 | Sandbox's Redshift free trial ends (287.51 of 300.00 left on 2026-10-25), and 5b's and 6h's bill halves become readable |
| 2027-01-21 | Production's Redshift free trial ends, 90 days after the namespace's creation (299.50 of 300.00 left on 2026-10-30); Stage 9's warehouse bill becomes readable |
| 2027-09-22 | GitLab's two leaves, `gitlab.awsds.internal` and `*.awsds-pages.internal`, are re-issued by this date: they expire 2027-10-22 06:35:12 UTC, and `production/pki/`'s plan proposes the re-issue from here (`early_renewal_hours` 720; [`runbooks/gitlab.md`](runbooks/gitlab.md) §C) |
