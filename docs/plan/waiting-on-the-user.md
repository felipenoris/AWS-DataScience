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
| The three Claude 5.5 model agreements (Sonnet 4.5 is Legacy since 2026-10-08) | [6e](stages/stage-06e-claude-code-bedrock.md) decision 17, PR #108 | PR #108's applies and the image's model pins |
| Decision 3: the Production data CMK first, then 1, 2 and 11, and decision 1's contradiction with 4.6 (whether Staging reads Production's outputs) | Stage 9 | pass 2 onward |
| The registry proof, and the escape-hatch window with the deployment manager's approval | Stage 9 3.4, 6.3 | verifications v and xi |
| Decisions 1-7, the account's association, `app-etl`'s first tag with `DEV_PROJECT_KEY_ARN` and `TEST_PROJECT_KEY_ARN` set in GitLab | [Stage 18](stages/stage-18-staging-deployment-project.md) | the deployment-only project, and Stage 10's passes after its verdict |

## Decisions

| Item | Where | Why it matters |
|---|---|---|
| `TM-17`: deny `sqs:SendMessage` and Bedrock's cross-account `lambda:InvokeFunction` outside the organization, or accept the channel | Stage 11, [`threat-model.md`](threat-model.md) | the project role's AWS-managed policy reaches other accounts' `airflow-celery-*` queues and `amazon-bedrock*` functions today, and no SCP narrows it |
| How the lake enters the catalog, recommended (c), and decisions 2-5 | [6f](stages/stage-06f-data-governance.md) decision 1 | step 2's subscriptions, 6g 2.4's Athena read and Stage 11 decision 12 |
| Whether Sandbox's `InfrastructureAccess` stays a contributor of both Sandbox projects, added in the portal on 2026-10-15 | 6f, [6h](stages/stage-06h-redshift-connection.md) `EXC-17` | it opens the projects' connections and assets to the infrastructure user; the instruments now read them from that session |
| The connection's `lineageSync`, daily at 03:43 UTC and failing: off in the portal, or kept | 6h decision 3 | a query on the 1.44 USD/h meter whenever the workgroup is up at that minute |
| 6g 2.4's Athena read: the persona's from a laptop, or the project role's after 6f decision 1 | [6g](stages/stage-06g-access-by-identity.md) 2.4 | as written it is refused, since the project role holds no Lake Formation grant on the lake |
| D12's budget notification and its threshold, a Management console object | 6e decision 6, [Stage 12](stages/stage-12-observability-finops.md) 2.1 | the estate's only spend alarm notifies nobody |
| D12's revision trigger, which fired: the bill read 53.31 USD in August and 74.48 in September from the six profiled accounts, Management, Log Archive and Audit unread, above the 50 USD ceiling | [D12](decisions/D12-budget-ceiling.md), Stage 12 4.2 | the ceiling every cost argument in the plan cites |
| Stage 12's decision due 1, the proxy status-check alarm's action (recommended: `notBreaching`) | Stage 12 | the `[D]` hosts' alarm actions at the next hub session |
| GitLab's product usage data: 4,049 `CONNECT`s to `events.gitlab.net`, 17.3 MB sent from the build plane, 2026-10-12 to 2026-10-16 | Stage 7, Stage 11 | metadata leaving the estate through the open build plane; turning it off is a GitLab setting, applied at a GitLab session |
| Bedrock invocation logging, due since the threat model exists; decisions 3, 6, 7 and 8 | Stage 11 decision 11 | step 5's trails and alarms |
| Decisions 1, 5 and 12 confirmed (taken decisions presuppose them); 2-4, 8, 9 and 11 | Stage 10 | passes 1 and 2 |
| The job role's name for Staging and Production; decision 20's optional `If-None-Match` deny; `awsds/infrastructure` kept as the promotion jobs' next reader or retired | [Stage 8](stages/stage-08-cicd-pipelines.md) 2.5, decision 20 | pass 4's manifest variables and Stage 10 decision 6 |
| Decisions due 2 (its formal close), 3, 4, 6's residual name, 9, 10, 12 and 13 | [6d](stages/stage-06d-unified-studio-remainder.md) | step 10, the Amazon Q door, `EXC-10`'s scope |
| When to spend the Redshift free trial; how a second project is admitted to the warehouse | [5b](stages/stage-05b-redshift-serverless.md) decision 9, 6h decision 8 | 6h step 5's negatives 5.1 and 5.2b |
| The four Anthropic direct-API names on the compute plane: remove them, or accept with a trigger | `TM-04`, 6e | a session can run outside every Bedrock control |
| `EXC-10`'s repair; conformance packs; AWS Backup and its Vault Lock | Stage 12 3.1, 6.2, 8.x | the rest of Stage 12 |
| GuardDuty's decisions 1-3 | [Stage 15](stages/stage-15-guardduty.md) | the whole stage, and Stage 11 step 4 |
| The embeddings model in the Bedrock SCP | Stage 17 decision 11 | pass 7's knowledge base |

## Acts only the user can perform

| Act | Where |
|---|---|
| Confirm the e-mail subscription of `awsds-sandbox-alerts`, created on 2026-10-18 at 20:54Z and reading `PendingConfirmation` | Stage 12 |
| Activate the cost allocation tags in Management's Billing console; the analyzer in Audit | Stage 12 4.1, 7.1 |
| Read Cost Explorer for August and September in Management, Log Archive and Audit, the accounts no CLI profile reaches | Stage 12 4.2 |
| The persona's refused job and its implicit-deny attempt | 6d 1.1, 1.2 |
| The three persona memberships in GitLab; Auto DevOps and the restricted visibility level; the CodeConnections attempt from Data Governance's console | [Stage 7](stages/stage-07-gitlab-runners-ecr.md) 3.5, runbook §I step 6, 7.2 |
| The knowledge-base enable-wizard read in the console | Stage 17 7.0a |
| Step 2's portal acts: a consumer project, a subscription, an approval as the Governance Manager | 6f step 2, 4.3 |
| 0.4's portal half; 6.4, keep or drop `lab` | 6h |
| The domain name | [Stage 13](stages/stage-13-public-web-tier.md) |
| The account quota, and D34's rung | [Stage 14](stages/stage-14-sandbox-vending.md) |

## Dates

| Date | What happens |
|---|---|
| 2026-10-20 01:59:59Z | `EXC-13`: the warehouse admin secret's first rotation fails with the workgroup down and does not retry; restarting it needs the workgroup up |
| 2026-11-01 | Stage 11 2.1.3's internal-access analyzer bills at setup and on each 1st: create it after this date, delete it before 2026-12-01 |
| 2026-11-13 and 2026-11-15 | the two GitLab backups in the bucket expire; with GitLab down past then, no current backup is left, and 8.2 starts with a fresh one |
| 2026-12-19 | the Redshift free trial ends, and 5b's and 6h's bill halves become readable |
