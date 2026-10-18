# Log — Stage 17 — Machine learning in a Sandbox project

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-17-sandbox-machine-learning.md`](../plan/stages/stage-17-sandbox-machine-learning.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-17 — pass 0 written in a cloud session, nothing run

- **[user] Pass 0 is written from a cloud session.** In a thread of the Claude project, at 19:22 UTC, the
  user answered the card *"Qual passo do AWS-DataScience tocamos agora, em paralelo à medição em
  Staging?"* with *"Stage 17, passo 0"*, whose consequence read *"Escrevo aqui o instrumento
  (sandbox-ml.py) e os exemplos do passo, e você roda as leituras no laptop. Não toca em Staging nem na
  SCP."* The pass is PR #157. The cloud session holds no AWS credential: no `aws` call ran in it, so
  nothing below is a measurement of AWS.
- **[Claude] 0.1, `./aws/sandbox-ml.py`, written and not run.** `ML-1`..`ML-9` as the stage file lists
  them; its contracts and the halves it cannot close are in [`aws/INDEX.md`](../../aws/INDEX.md),
  "`sandbox-ml.py`, written for Stage 17". Its parsing and its verdicts were exercised against a
  fabricated `aws` executable. Its first run on the laptop is 0.1's before, and carries 0.2 (`ML-7`), 0.5
  (`ML-9`) and 0.8 (`ML-1`).
- **[Claude] 0.6, [`examples/sandbox-ml/`](../../examples/sandbox-ml/README.md), written and not run
  against AWS**: a script per step for a terminal of a space, the pipeline definition with every
  account-scoped value a placeholder, and the README with the values, the commands of a sitting and what
  the first run decides. They were written against the house environment's lock
  (`gitlab/awsds/dev-env/dev-env/python/uv.lock`): `boto3` 1.43.92, `mlflow` 3.16.0, `sagemaker-mlflow`
  0.5.0, `sagemaker` 3.21.0, `pandas` 2.3.3, `xgboost-cpu` 3.3.0, Python 3.12. Step 0.3 reads what the
  space holds, and a script that disagrees changes before it runs (Lesson 65).
- **[Claude] The defaults taken where the stage's wording leaves a choice**, each named here because
  nobody was asked:
  - The jobs, the models and the pipeline go through boto3's low-level client and a JSON pipeline
    definition rather than the SageMaker SDK. The lock's SDK is 3.21.0, whose training and pipeline
    classes are not the 2.x `Estimator` and `Pipeline` that AWS's recipe imports, and a request built
    field by field lets each negative change exactly one field (Lesson 20).
  - Step 2.2's image is XGBoost `3.0-5`, not the recipe's `1.7-1`, for the reason the next entry
    measures; the stage file's step 2.2 and its menu table carry the change.
  - `register.py log-model` logs the job's `model.tar.gz` into the job's MLflow run before it loads the
    booster, so verification iv has an object in the artifact store whatever the image.
    `register.py from-mlflow` calls `mlflow.register_model` on the job's `model.tar.gz` by its `s3://`
    URI, as the recipe does.
  - `ML-3` reads the account's 20 most recent training jobs whatever their name, where step 2.5 says
    every `ml-demo-` job, so the job a portal form creates (2.4) is judged too.
  - The knowledge base's documents are copied by `knowledge_base.py` from the space's clone, which prints
    the commit and each document's size for this log (7.4a).
- **[Claude] The model format, measured on the session's build host, not in the lab.** A booster that
  `xgboost` 1.7.6 saved as `xgboost-model`, the name the SageMaker XGBoost container uses, starts with
  the bytes `binf`, and `xgboost-cpu` 3.3.0 refused to load it:

  ```
  The binary format has been deprecated in 1.6 and removed in 3.1, use UBJ or JSON instead. You can
  port the binary model to UBJ and JSON by re-saving it with XGBoost 3.0.
  ```

  The same booster saved by `xgboost` 3.0.5 was UBJSON, and 3.3.0 loaded it with the warning
  ``Unknown file format: ``. Using UBJSON (`ubj`) as a guess.``. So with `1.7-1`, step 3.1's
  `mlflow.xgboost.log_model` cannot run in the house interpreter. The container's own source was not
  read: its repository is outside this session's GitHub scope, and AWS's XGBoost algorithm pages and the
  `us-west-2` registry-paths page did not load from it. `3.0-5` is in the same repository,
  `sagemaker-xgboost`, and the same `us-west-2` registry as `1.7-1` in the image table of `sagemaker-core`
  2.21.0, so `ML-3`'s image check reads both the same way.
- **[Claude] What else ran on that build host**, with fabricated account values:
  - `data.py` fetched the recipe's CSV through the host's proxy, not the lab's: 7,043 rows, 970,457
    bytes. `prepare.py` dropped 11 rows for a blank `TotalCharges` and split the rest 4,922 / 1,054 /
    1,056, byte-identical under `pandas` 2.3.3 and 3.0.6.
  - The recipe's hyperparameters, trained locally with `xgboost-cpu` 3.3.0 over that split, gave a
    validation AUC of 0.8181 at 200 rounds and depth 5 and 0.8415 at 50 rounds and depth 3, both above the
    pipeline's `AucThreshold` of 0.75. A job's AUC is the image's reading, not this one.
  - Every AWS call of the scripts but `register.py log-model`'s went through botocore's `Stubber`, which
    checks each request against the service model, with MLflow replaced by a stand-in; each variant of
    `train.py` differed from the admitted request in one top-level field.
- **[Claude] What the laptop owes next.** On the laptop, as the infrastructure user with
  `InfrastructureAccess` in `Sandbox` (`awsds-infra-sandbox-1`): `./aws/devenv.py`, whose `DE-5` `ML-9`
  reads, then `./aws/sandbox-ml.py`, with the session down or up; its interface-endpoint half of `ML-9`
  reads only after `make hub-up` and `make up ENV=sandbox`. In a space, the user's 0.3; in the portal, the
  user's 0.7.

---

## 2026-10-17 — 0.1's before, run on the laptop: three quotas at zero

*Provenance. The user ran the commands below on the laptop, as the infrastructure user with
`InfrastructureAccess` in `Sandbox` (`awsds-infra-sandbox-1`), from a detached worktree of PR #157's
branch at `bc47f13`, with the session down, and pasted the output into the Claude project's thread at
21:08:53 UTC. Claude read the paste and wrote this entry; no `aws` call ran in the cloud session. No
quoted line carries an account id or an e-mail address, so no identifier substitution was needed.*

- **[user] The block**, and what it printed:

  ```
  aws sts get-caller-identity --profile awsds-infra-sandbox-1
  ./aws/devenv.py
  ./aws/sandbox-ml.py
  ```

  ```
  wrote aws/output/devenv.txt checks: 5 passed or noted, 1 FAILED
  wrote aws/output/sandbox-ml.txt (3 CHECK(S) FAILED - see section 12)
  ```

  The report is stamped `2026-10-17T21:07:55Z`, and its section 13 reads `None. Every call in this report
  returned successfully.`
- **[Claude] `devenv.py`'s failure is the session's state, inferred.** Its report was not pasted. `ML-9`
  quotes its `DE-5` as `pass at 2026-10-17T21:05:30Z: version 9, sha256:b788dbd9c7cf...: 70 names, sha256
  aafa08da98a61f5c`, and with `sandbox/egress` down `DE-2` fails on the slice's absent outputs, as the
  Stage 8 log reads it on 2026-10-16.
- **[Claude] 0.2, `ML-7`: three of the four quotas are zero** (verification xxi):

  ```
  QUOTA                                                   VALUE  SOURCE   CODE
  ml.m5.xlarge for training job usage                     0      applied  L-CCE2AFA6
  ml.m5.large for endpoint usage                          0      applied  L-614B09FD
  ml.m5.large for transform job usage                     0      applied  L-236AE59F
  ml.t3.medium for processing job usage                   4      applied  L-0CE343FE
  ```

  The zeros stop passes 2 to 5: the training job, the version registered from it, the endpoint, the
  transform and the pipeline's training step. Pass 1's MLflow App and pass 7's Bedrock objects use none of
  the three types. The instrument printed no AWS default beside an applied value. The MLflow quotas: `The maximum number of MLflow Apps that can be created.` 3 (`L-F369E3CA`),
  the MLflow App request rates 1, but `CreatePresignedMlflowAppUrl` 5 and `DeleteMlflowApp` 2, and the
  tracking servers Small 5, Medium 5, Large 1, at most 10.
- **[Claude] 0.1, `ML-1`: decision 9 does not arise.** Both project roles,
  `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw` and
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, carry `EnableSageMakerMLWorkloadsPermissions`
  `true`, the key `alias/awsds-sandbox-project`, the bucket `awsds-sandbox-smus-projects` and the
  boundary `awsds-sandbox-project-boundary` v2 with its five statements. The ceiling reads `ml.c5.large,
  ml.c5.xlarge, ml.m5.large, ml.m5.xlarge, ml.t3.large, ml.t3.medium, ml.t3.xlarge`: the exercise's types
  inside, `ml.m5.2xlarge` outside. Both roles hold
  `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`,
  `SageMakerStudioProjectRoleMachineLearningPolicy`, `SageMakerStudioProjectUserRolePolicy` and
  `awsds-sandbox-workflows`; the second adds `awsds-sandbox-bedrock-assistant` and
  `awsds-sandbox-warehouse-project-avhvbqn37ty7m8`.
- **[Claude] The managed ML policy serves v45, and AWS's pages still show v44.**
  `SageMakerCreatePermissions` (14 actions; `aws:PrincipalTag/EnableSageMakerMLWorkloadsPermissions`,
  `aws:ResourceTag/AmazonDataZoneProject`), `SageMakerTagPermissions` (2) and
  `SageMakerMlflowServerlessPermission` (6; `aws:ResourceTag/AmazonDataZoneProject`) read with the action
  counts and condition keys of the reference page's v44, last edited 2026-09-14, which Claude read the
  same evening, and the tag condition is v44's:

  ```
  {"ForAllValues:StringLike": {"aws:TagKeys": ["ProjectUserTag*", "sagemaker*", "sm-jumpstart*", "endpoint-has-jumpstart-model"]}, "ForAllValues:StringNotLike": {"aws:TagKeys": ["AmazonDataZone*", "sagemaker:shared-with:*"]}, "StringEquals": {"aws:ResourceTag/AmazonDataZoneProject": "${aws:PrincipalTag/AmazonDataZoneProject}"}}
  ```

  The admin guide's table of managed-policy updates names no change to this policy after 2026-06-25, so
  what v45 changed is unread; `iam get-policy-version` of v44 and v45 reads it. The `AddTags` gap stands:
  `awsds-sandbox-workflows` grants the project tag on `processing-job` alone, so a training job's create
  meets it (2.2 (b), decision 7).
- **[Claude] 0.8: `enableNetworkIsolation` is `true`** in both Tooling stacks,
  `DataZone-Env-bi356s1sacz0cw` (`CREATE_COMPLETE`) and `DataZone-Env-5hkjdsy3umpi1c`
  (`UPDATE_COMPLETE`).
- **[Claude] `ML-2` to `ML-6`: nothing built.** No MLflow App, training job, model package group,
  endpoint, transform job or pipeline, and no HyperPod cluster or Partner AI app. CloudTrail's 90 days
  hold six `CreateTrainingJob` refusals, two on 2026-08-27 and four on 2026-09-10, by
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` with session `AmazonMWAAServerless`, each on a
  `Notebook-task-*` job `with an explicit deny in a permissions boundary`: the portal notebook tasks of
  6d step 4.
- **[Claude] `ML-8`: the Generative AI menu's before.** The four project Bedrock roles,
  `AmazonBedrockLambdaExecutionRole-<project>-<environment>` and
  `AmazonBedrockServiceRole-<project>-<environment>` for each project, carry the boundary and their
  project's tag. Both project roles carry `EnableAmazonBedrockPermissions` `true` and no
  `EnableAmazonBedrockIDEPermissions`, verification xvii's before. No knowledge base, vector bucket,
  agent, prompt, flow, guardrail or evaluation job exists. `amazon.titan-embed-text-v2:0` reads agreement
  `AVAILABLE`, authorization `AUTHORIZED`, entitlement `AVAILABLE`, region `AVAILABLE`; the repository's
  SCP admits the three 4.5 models only, so 7.4a's first sync is expected refused. The account's one
  Lambda function is Control Tower's `aws-controltower-NotificationForwarder`, with no VPC.
- **[Claude] 0.5, `ML-9`, with the session down.** No interface endpoint and no
  `awsds-sandbox-egress-allow` list; the S3 gateway endpoint's `AllowAwsOwnedServiceBuckets` names
  `sagemaker-us-west-2` and `jumpstart-cache-prod-us-west-2` (verification iii exercises them). The
  interface half waits on `make hub-up` and `make up ENV=sandbox`.
- **[Claude] What is owed.** The user's increase requests for the three quotas; 0.3 in a space and 0.7 in
  the portal, with the session up; v45's change, read with `get-policy-version`.

---

## 2026-10-17 — the three increase requests, and v45's change read

*Provenance. The user ran the block Claude had written in the thread at 21:27 UTC on the laptop, as the
infrastructure user with `InfrastructureAccess` in `Sandbox` (`awsds-infra-sandbox-1`), from the same
worktree at `bc47f13`, and pasted the output at 21:46:05 UTC with "Rodei o pedido de aumento de cotas."
Claude read the paste and wrote this entry; no `aws` call ran in the cloud session. No quoted line
carries an account id or an e-mail address.*

- **[user] The block**, as Claude wrote it:

  ```
  for q in L-CCE2AFA6 L-614B09FD L-236AE59F; do
    d=$(aws service-quotas get-aws-default-service-quota --service-code sagemaker --quota-code $q --query Quota.Value --output text --profile awsds-infra-sandbox-1 --region us-west-2)
    v=$(awk -v d="$d" 'BEGIN { v = 1; if (d + 0 > 1) v = int(d); print v }')
    echo "$q: default $d, pedido $v"
    aws service-quotas request-service-quota-increase --service-code sagemaker --quota-code $q --desired-value $v --profile awsds-infra-sandbox-1 --region us-west-2 --query 'RequestedQuota.[QuotaCode,DesiredValue,Status]' --output text
  done
  for v in v44 v45; do aws iam get-policy-version --policy-arn arn:aws:iam::aws:policy/SageMakerStudioProjectRoleMachineLearningPolicy --version-id $v --query PolicyVersion.Document --output json --profile awsds-infra-sandbox-1 | jq -S . > /tmp/ml-$v.json; done
  diff /tmp/ml-v44.json /tmp/ml-v45.json
  ```

  The loop's own lines, in the order they reached the paste:

  ```
  L-CCE2AFA6: default 0.0, pedido 1
  L-614B09FD: default 0.0, pedido 1
  L-236AE59F: default 0.0, pedido 1
  ```
- **[Claude] The three requests ask for 1 instance each, against an AWS default of 0.** The request
  calls' own lines (code, desired value, status) are absent, and so is any error line, which `aws` writes
  to stderr; so the three calls most likely returned, and their statuses are unread. The absence is
  inferred to be the CLI's pager: AWS CLI v2 sends output bound for a terminal through `less`, with its
  own `FRX` flags only when `LESS` is unset; the paste's prompt is oh-my-zsh's default theme, and
  oh-my-zsh sets `LESS=-R`, under which `less` holds each output until `q` and clears the screen as it
  exits. The
  repository's scripts already set `AWS_PAGER` to empty (`aws/awslib/context.py`); a block handed over by
  hand carries `--no-cli-pager` from now on. `ML-7` now reads the request history, so the next run of
  `./aws/sandbox-ml.py` prints each zero quota's latest request with its status.
- **[user] What `diff` printed** between the two versions, each sorted by key with `jq -S` (which keeps
  every array's order):

  ```
  1141a1142
  >         "s3:GetAccessGrantsInstance",
  1143a1145
  >         "s3:ListAccessGrants",
  1251a1254,1257
  >         "datazone:Get*",
  >         "datazone:CreateListingChangeSet",
  >         "datazone:CreateSubscriptionRequest",
  >         "datazone:RevokeSubscription",
  1258c1264,1266
  <         "datazone:*Compute*"
  ---
  >         "datazone:*Compute*",
  >         "datazone:*Agent*",
  >         "datazone:*DataApp*"
  1291a1300,1315
  >     },
  >     {
  >       "Action": [
  >         "identitystore:DescribeUser",
  >         "identitystore:DescribeGroup",
  >         "sso:DescribeInstance",
  >         "sso:DescribeApplication"
  >       ],
  >       "Condition": {
  >         "Bool": {
  >           "aws:ViaAWSService": "true"
  >         }
  >       },
  >       "Effect": "Allow",
  >       "Resource": "*",
  >       "Sid": "SSOReadOnlyPermissions"
  ```
- **[Claude] Which statements changed**, read against v44 on the managed-policy reference page (re-read
  2026-10-17, still v44, edited 2026-09-14). `diff` printed no context lines, so the attribution rests on
  line positions:
  - **`DataZoneUserPermissions`, certain.** On v44 it is the one statement holding `datazone:*Compute*`,
    the last of its nine actions, on `Resource` `*` with no condition. The line without a trailing comma
    puts that action at v44's line 1258, so the list is lines 1250 to 1258 and the four insertions after
    line 1251 follow its `datazone:CreateAsset*`. v45 adds six actions to it: `datazone:Get*`,
    `datazone:CreateListingChangeSet`, `datazone:CreateSubscriptionRequest`,
    `datazone:RevokeSubscription`, `datazone:*Agent*` and `datazone:*DataApp*`.
  - **`ConsumerS3AGPermission`, inferred.** On v44 the S3 Access Grants actions sit there
    (`s3:GetAccessGrantsInstanceForPrefix`, `s3:GetDataAccess`, `s3:ListCallerAccessGrants`,
    `ram:GetResourceShareInvitations`), and v45 inserts `s3:GetAccessGrantsInstance` and
    `s3:ListAccessGrants` among lines 1141 to 1143. `s3:ListAccessGrants` lists the grants of the
    account's Access Grants instance, not only the caller's.
  - **`SSOReadOnlyPermissions`, new**: four Identity Center reads, admitted only when an AWS service
    makes the call on the role's behalf (`aws:ViaAWSService` `true`).
- **[Claude] What it changes here.** None of the three statements Stage 17 relies on moved:
  `SageMakerCreatePermissions`, `SageMakerTagPermissions` and `SageMakerMlflowServerlessPermission` hold
  what the first run read, so the `AddTags` gap of decision 7 stands and `ML-1`'s known version becomes
  v45. The boundary `awsds-sandbox-project-boundary` v2 denies nothing in `datazone:`, in the Access
  Grants actions or in `identitystore:` and `sso:` (`terraform-modules/sagemaker-prereqs/boundary.tf`),
  and no statement `POLICIES.md` indexes denies them in Sandbox (`DenyDataZoneDomainOutsideDataOu` names
  `CreateDomain` alone), so the IAM half of each new action reaches both project roles:
  code running as a project role (a notebook, a workflow task) may now ask for a subscription, revoke one
  and create a listing change set. DataZone's own authorization is the other half, unread. That is the
  catalog road of [Stage 6f](../plan/stages/stage-06f-data-governance.md), whose decision 5 gains the
  reading as a note.

## 2026-10-17 — pass 1 written in the cloud session, not applied

*Provenance. Claude asked in the thread at 21:27 UTC "quer que eu escreva aqui o passo 1 (MLflow: o
grupo `mlflow` no `vpc-egress` e o blueprint `MLflowApp`), sem aplicar nada?", and the user answered
"Sim." at 21:46:05 UTC. Claude wrote the change in the cloud session, which holds no AWS credential, so
nothing below is a measurement of AWS and nothing was applied.*

- **[Claude] 1.4's module half, `vpc-egress-v0.18.0`** (`6a84bf3`): the group `mlflow`, one service,
  `sagemaker.mlflow`, whose endpoint name `aws.sagemaker.<region>.mlflow` comes from AWS's pages, not
  from the Region's catalog. The `aws.sagemaker.` exception became a list of short names,
  `sagemaker.studio` and `sagemaker.mlflow`, because `sagemaker.api` and `sagemaker.runtime` are
  `com.amazonaws.` names.
  `terraform validate` passed on a scratch copy of the module with the AWS provider 6.68.0 from a local
  mirror (the session's proxy refuses `registry.terraform.io`), and `terraform console` printed
  `aws.sagemaker.us-west-2.mlflow`, `aws.sagemaker.us-west-2.studio` and
  `com.amazonaws.us-west-2.sagemaker.api` for the three short names.
- **[Claude] 1.2's module half, `sagemaker-prereqs-v0.5.0`** (`41be913`): `MLflowApp` last in
  `blueprint_names`. `terraform validate` passed with the AWS provider 6.68.0 and `awscc` 1.98.0, the
  caller's locked version, fetched from `releases.hashicorp.com` with its checksum matched.
- **[Claude] The two tags exist only in the cloud session's clone.** Pushing them was refused twice with
  HTTP 403 by the session's proxy, while the branch push went through, so Recipe B's push and its
  `git ls-remote` check are the laptop's. Until the tags are on origin, the offline gates'
  `terraform_validate` cannot initialise the two callers and the PR's CI reads red.
- **[Claude] The callers' commit**: `sandbox/egress` at `vpc-egress-v0.18.0`, `sandbox/sagemaker` at
  `sagemaker-prereqs-v0.5.0`, `MLflowApp` last in the governance profile's list and in `US-3`'s
  allow-list; the group in `make help`, in `sandbox/egress`'s variable, in `layers.py`'s note, in
  `cost-model.md`, `sg-proxy.md` and `NETWORK.md`; `SMUS.md`'s category 1 at twelve and category 2 at
  three. Three comments that counted category 1 as eleven lost the count.
- **[Claude] Decision 4's recommendation moved from (a) to (b).** (a) rested on "the space exports no
  proxy variable". The house image sets `HTTPS_PROXY` and `NO_PROXY` as `ENV` (6d decision 8,
  `gitlab/awsds/dev-env/dev-env/Dockerfile`), and `sagemaker-mlflow` 0.5.0 sends an app's calls to
  `mlflow.sagemaker.<region>.app.aws`, a family no compute plane admits, so a space whose literal lacks
  the host gets the proxy's 403 whether or not the endpoint exists. The choice is the user's.

## 2026-10-18 — decision 4 taken

- **[user] Decision 4** (00:04 UTC, on the project thread's decision card "Escolher quando sobe o
  grupo mlflow: depois da imagem nova ou já?"): "Imagem antes", the recommended (b). The image
  carrying the next `NO_PROXY` literal is released in the sitting of the `mlflow` group's first apply,
  and PR #157's merge goes with it. Nothing follows yet: the literal comes from the first plan of
  `sandbox/egress` at `vpc-egress-v0.18.0`, which waits on the two tags reaching origin.
