# Waiting on the user

Every item, across stages, that only the user can take: a decision, an act in a console or a portal, a
sign-in as another persona, a request to AWS. Recorded on 2026-10-18 at the user's request, to be taken
later. A row is added when a session stops on one and removed in the sitting that takes it; the stage's
own Decisions-due table keeps the reasoning and the recommendation.

## Items that hold up an apply or a run

| Item | Where | What it holds up |
|---|---|---|
| The portal reading before `MLflowApp` exists, as the data scientist (no environment needed) | [Stage 17](stages/stage-17-sandbox-machine-learning.md) 1.1 | the one apply of `sandbox/sagemaker/` and `data-governance/governance/`, which carries `MLflowApp` and `TM-21`'s narrowing of the Sandbox project key, whose two statements still name `Principal *` with no organization condition. Accepting the loss of verification i releases the apply too |
| Which principal the data cells filters bind | [Stage 11](stages/stage-11-dlp.md) decision 12, with 6f decision 1 | pass 1's two lake applies and 2.3's proof; the code is written and creates nothing |
| SageMaker processing-job quota increases in Production and Staging (`ml.m5.large`, `ml.m5.xlarge`, `ml.m5.2xlarge` read 0 on 2026-10-18) | [Stage 9](stages/stage-09-deployment-targets.md), [Stage 10](stages/stage-10-orchestration-promotion.md) | every SageMaker job in either account, the promotion's processing step included |
| The three Claude 5.5 model agreements (Sonnet 4.5 is Legacy since 2026-10-08) | [6e](stages/stage-06e-claude-code-bedrock.md) decision 17, PR #108 | PR #108's applies and the image's model pins; the PR conflicts with main in `CLAUDE.md`, `docs/AWS_STATE.md` and `docs/log/INDEX.md` (read 2026-10-18), for its session to resolve when the agreements arrive |
| Decision 3, the mirror mechanism, first (pass 2's first table); then 1, the Production data CMK, with its contradiction with 4.6 (whether Staging reads Production's outputs), 2, the scan limit, and 11, where each target's query results land; 5-8 are the governed warehouse's | Stage 9 | pass 2 onward; 5-8 hold pass 6 |
| The registry proof, and the escape-hatch window with the deployment manager's approval | Stage 9 3.4, 6.3 | verifications v and xi |
| Decisions 1-7, the account's association, `app-etl`'s first tag with `DEV_PROJECT_KEY_ARN` and `TEST_PROJECT_KEY_ARN` set in GitLab | [Stage 18](stages/stage-18-staging-deployment-project.md) | the deployment-only project, and Stage 10's passes after its verdict |

## Decisions

| Item | Where | Why it matters |
|---|---|---|
| `TM-17`: deny `sqs:SendMessage` and Bedrock's cross-account `lambda:InvokeFunction` outside the organization, or accept the channel | Stage 11, [`threat-model.md`](threat-model.md) | the project role's AWS-managed policy reaches other accounts' `airflow-celery-*` queues and `amazon-bedrock*` functions today, and no SCP narrows it |
| How the lake enters the catalog, recommended (c), and decisions 2-5 | [6f](stages/stage-06f-data-governance.md) decision 1 | step 2's subscriptions, 6g 2.4's Athena read and Stage 11 decision 12 |
| Whether Sandbox's `InfrastructureAccess` stays a contributor of both Sandbox projects, added in the portal on 2026-10-15 | 6f, [6h](stages/stage-06h-redshift-connection.md) `EXC-17`, [INT-25](integrations.md) | it opens the projects' connections and assets to the infrastructure user; the instruments now read them from that session |
| The connection's `lineageSync`, daily at 03:43 UTC and failing: off in the portal, or kept | 6h decision 3 | a query on the 1.44 USD/h meter whenever the workgroup is up at that minute |
| 6g 2.4's Athena read: the persona's from a laptop, or the project role's after 6f decision 1 | [6g](stages/stage-06g-access-by-identity.md) 2.4 | as written it is refused, since the project role holds no Lake Formation grant on the lake |
| D12's budget notification and its threshold, a Management console object | 6e decision 6, [Stage 12](stages/stage-12-observability-finops.md) 2.1 | the estate's only spend alarm notifies nobody |
| D12's revision trigger, which fired: the bill read 53.31 USD in August and 74.48 in September from the six profiled accounts, Management, Log Archive and Audit unread, above the 50 USD ceiling | [D12](decisions/D12-budget-ceiling.md), Stage 12 4.2 | the ceiling every cost argument in the plan cites |
| Stage 12's decision due 1, the proxy status-check alarm's action (recommended: `notBreaching`) | Stage 12 | the `[D]` hosts' alarm actions at the next hub session |
| GitLab's product usage data: 4,049 `CONNECT`s to `events.gitlab.net`, 17.3 MB sent from the build plane, 2026-10-12 to 2026-10-16 | [Stage 7](stages/stage-07-gitlab-runners-ecr.md), runbook `gitlab.md` §I step 6; the threat model covers Data Governance and Sandbox, so no `TM` row holds it | metadata leaving the estate through the open build plane; turning it off is a GitLab setting, applied at a GitLab session |
| Bedrock invocation logging, due since the threat model exists; decisions 3, 6, 7 and 8 | Stage 11 decision 11 | step 5's trails and alarms |
| Decisions 1, 5 and 12 confirmed (taken decisions presuppose them); 2-4, 8, 9 and 11 | Stage 10 | passes 1 and 2 |
| The job role's name for Staging and Production; decision 20's optional `If-None-Match` deny; `awsds/infrastructure` kept as the promotion jobs' next reader or retired | [Stage 8](stages/stage-08-cicd-pipelines.md) 2.5, decision 20; decision 2 for the mirror | pass 4's manifest variables and Stage 10 decision 6 |
| Decisions due 2 (its formal close), 3, 4, 6's residual name, 9, 10, 12 and 13 | [6d](stages/stage-06d-unified-studio-remainder.md) | step 10, the Amazon Q door, `EXC-10`'s scope |
| When to spend the Redshift free trial; how a second project is admitted to the warehouse | [5b](stages/stage-05b-redshift-serverless.md) decision 9, 6h decision 8 | 6h step 5's negatives 5.1 and 5.2b; decision 8 (a)'s layer-2 argument is gone, AWS's managed project policy granting `GetCredentials` to every project under the wide tag (PR #187) |
| The four Anthropic direct-API names on the compute plane: remove them, or accept with a trigger | `TM-04`, 6e | a session can run outside every Bedrock control |
| `EXC-10`'s repair; conformance packs; AWS Backup and its Vault Lock | Stage 12 3.1, 6.2, 8.x | the rest of Stage 12 |
| GuardDuty's decisions 1-3 | [Stage 15](stages/stage-15-guardduty.md) | the whole stage, and Stage 11 step 4 |
| The embeddings model in the Bedrock SCP | Stage 17 decision 11 | pass 7's knowledge base |
| 6e decision 11: carve one probe principal out of `DenyInvokingModelsThatRetain` for one sitting and invoke the Fable profile as it, or accept the vendor's sentence with its date (recommended: the carve-out) | 6e | the only negative control `mode: none` can have; the probe may meet `EXC-08`'s commercial gate before the retention mode |
| 6e decision 13, taken by Claude on 2026-09-12 and never reviewed: only `bedrock-runtime` carries an action scope, not the `bedrock` control-plane endpoint | 6e | `PutModelInvocationLoggingConfiguration` still traverses that door; five weeks of readings show only `ListInferenceProfiles` through it |
| `TM-01`: `-n` on the allow-list planes' `dstdomain` ACL, so a raw address matches no name (never on the deny-list ACL, which it would widen) | Stage 11, [`threat-model.md`](threat-model.md) | the proxy may admit a raw public address whose reverse record names an allowed host (inferred, unexercised); the change replaces the proxy host, so it rides the hub sitting's `production/proxy/` apply |

## Acts only the user can perform

| Act | Where |
|---|---|
| Confirm the e-mail subscription of `awsds-sandbox-alerts`, created on 2026-10-18 at 20:54Z and reading `PendingConfirmation` | Stage 12 |
| Activate the cost allocation tags in Management's Billing console; the analyzer in Audit | Stage 12 4.1, 7.1 |
| Read Cost Explorer for August and September in Management, Log Archive and Audit, the accounts no CLI profile reaches | Stage 12 4.2 |
| The persona's refused job and its implicit-deny attempt | 6d 1.1, 1.2 |
| The three persona memberships in GitLab; Auto DevOps and the restricted visibility level; the CodeConnections attempt from Data Governance's console | [Stage 7](stages/stage-07-gitlab-runners-ecr.md) 3.5, runbook §I step 6, 7.2 |
| 6h 5.3 and 5.4's real attempts, for the refusals' wording, with the compute up (the simulator read both as designed on 2026-10-18) | [6h](stages/stage-06h-redshift-connection.md) |
| Push `examples/app-etl/.gitlab-ci.yml` and its README to GitLab's `awsds/app-etl` at a GitLab session, so GitLab's pipeline runs the lint with its two options (PR #186) | [Stage 8](stages/stage-08-cicd-pipelines.md) 5.6 |
| Verification xxi's attempt half, an S3 put and delete on the release bucket | Stage 8 |
| The knowledge-base enable-wizard read in the console, before the roster commit that tags `sagemaker-prereqs-v0.7.0` (`docs/SMUS.md`'s order) | Stage 17 7.0a |
| Step 2's portal acts: a consumer project, a subscription, an approval as the Governance Manager | 6f step 2, 4.3 |
| 0.4's portal half; 6.4, keep or drop `lab` | 6h |
| The domain name | [Stage 13](stages/stage-13-public-web-tier.md) |
| The account quota, and D34's rung | [Stage 14](stages/stage-14-sandbox-vending.md) |

## Sittings with the environment up

Owed items Claude can take only with metered resources running, grouped by the sitting that raises them
so one start closes as many as it can. Starting a sitting is the user's call: it is metered
([`cost-model.md`](cost-model.md), "Per session", holds the rates), and the tunnel and the portal acts are
the user's hands. Each row names what must be decided or done first.

| Sitting | Raised by | What it closes | First |
|---|---|---|---|
| Hub | `make hub-up` | [Stage 12](stages/stage-12-observability-finops.md) 2.2's `[D]` half on `production/vpn/` and `production/proxy/` (`EXC-19`). The `production/proxy/` apply replaces the host (`user_data_replace_on_change`), so one apply carries 6g decision 1's replacement, the status-check alarm's action and its missing-data setting, and `TM-01`'s `-n` if it is taken | Stage 12 decision due 1; `TM-01` |
| GitLab | `make gitlab-up`, after the hub | Stage 12 2.2's alarm action on `production/tooling/`, with the host started. The user's acts: Stage 7 3.5's memberships and §I step 6's settings, the usage data among them; pass 4's cycle and restore rehearsal (8.1-8.3) before the backups expire on 2026-11-13; Stage 8 2.5's first `app-etl` tag; the house image `default-v0.9.0` with the 72-name `NO_PROXY` literal, registered as version 10 (Stage 17 decision 4: the image first), which turns `DE-5` green | the usage-data decision |
| Sandbox | `make up ENV=sandbox`, after the hub and the new image | 6d 5.1, 6.1 (viii), 7.5's monitored half, 7.6 and 7.7; Stage 7's INT-09 clone from a notebook on the house image; Stage 12 9.1's interface-endpoint reading; Stage 17's passes 2-5 | Stage 17 1.1 and its `sandbox/sagemaker/` apply before passes 2-5; 6f decision 1 before 6g 2.4 |
| Warehouse | `sandbox/warehouse-compute/` up, inside a Sandbox sitting | 5b's `max_query_execution_time` test (a long query over a user table, as a non-superuser and as the admin) and the `enable_large_strings_opt_in` re-plan; `EXC-13`'s rotation restart, after 2026-10-20 01:59:59Z; 6h's negatives 5.1 and 5.2b | 6h decision 8 before the negatives; 6h decision 3 if the sitting spans 03:43 UTC |
| Staging | `make up ENV=staging`, after the hub | 6d 8.8's `staging/egress` tail | Stage 8 3.1's retirement of `staging/probes/` merged, or the sitting raises it |
| Production | `make up ENV=production`, which leaves the hub alone (refusal 6) | [Stage 9](stages/stage-09-deployment-targets.md)'s `production/workloads-egress/` (15 to add: `VPC-Workloads`' six endpoints and its DNS Firewall) | the processing-job quota requests, before any job runs there |

## Dates

| Date | What happens |
|---|---|
| 2026-10-20 01:59:59Z | `EXC-13`: the warehouse admin secret's first rotation fails with the workgroup down and does not retry; restarting it needs the workgroup up |
| 2026-11-01 | Stage 11 2.1.3's internal-access analyzer bills at setup and on each 1st: create it after this date, delete it before 2026-12-01 |
| 2026-11-13 and 2026-11-15 | the two GitLab backups in the bucket expire; with GitLab down past then, no current backup is left, and 8.2 starts with a fresh one |
| 2026-12-19 | the Redshift free trial ends, and 5b's and 6h's bill halves become readable |
