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

## 2026-10-18 — pass 1's tags on origin, and its readings from the laptop

*Provenance. The user started a laptop session with a procedure the cloud session wrote, and Claude ran
every command below in it, as the infrastructure user with `InfrastructureAccess` in `Sandbox`
(`awsds-infra-sandbox-1`) and in `Data Governance` (`awsds-infra-data`), with the session down. The relay
the procedure named, `mcp__claude-code-remote__send_message`, did not exist in that session, so each
report went to its chat, and the user then asked the same session to write this entry. No quoted line
carries an account id or an e-mail address.*

- **[Claude] Recipe B's push.** The reads before it matched the procedure:
  `6a84bf3 vpc-egress: the optional group mlflow, the MLflow App's interface endpoint` and
  `41be913 sagemaker-prereqs: MLflowApp joins the blueprint roster`, both ancestors of the branch's head
  `fa20bfe`; origin's newest tags `vpc-egress-v0.17.0` and `sagemaker-prereqs-v0.4.0`; no local tag of
  either name. The two lightweight tags were made at 00:57:12 UTC and pushed, each `* [new tag]`, and
  `git ls-remote --tags origin vpc-egress-v0.18.0 sagemaker-prereqs-v0.5.0` printed:

  ```
  41be9134e459e4b7f8e9c57a30144fa7b6a9540e	refs/tags/sagemaker-prereqs-v0.5.0
  6a84bf346945927b7fef5a377bec172fa239f986	refs/tags/vpc-egress-v0.18.0
  ```

- **[Claude] The readings below ran from a worktree detached at `fa20bfe`**, PR #157's head, which
  `e6dfc6a` merged at 02:33 UTC.
- **[Claude] `./aws/sandbox-ml.py`, its second run** (00:58:21 to 01:01:33 UTC, the report stamped
  `2026-10-18T01:01:31Z`): `wrote aws/output/sandbox-ml.txt (all checks passed)`, exit 0, and section 13
  `None. Every call in this report returned successfully.`
  - **The three quotas no longer read zero.** `ML-7`'s rows for the exercise's types:

    ```
    QUOTA                                                   VALUE  SOURCE   AWS DEFAULT  CODE        LATEST REQUEST
    ml.m5.xlarge for training job usage                     20     applied  0            L-CCE2AFA6  increase to 1 requested 2026-10-17, CASE_OPENED
    ml.m5.large for endpoint usage                          8      applied  0            L-614B09FD  increase to 1 requested 2026-10-17, CASE_OPENED
    ml.m5.large for transform job usage                     8      applied  0            L-236AE59F  increase to 1 requested 2026-10-17, CASE_OPENED
    ml.t3.medium for processing job usage                   10     applied  4            L-0CE343FE  no increase request
    ```

    The first run, at 21:07:55 UTC the day before, read the same four at 0, 0, 0 and 4. Each applied
    value now exceeds the 1 its request asks for while every request reads `CASE_OPENED`, and the
    processing quota, never requested, rose from 4 to 10; what raised them is unread. The four rows pass,
    and the MLflow quotas read as the first run did.
  - **`ML-1` passes on v45** for both project roles; its other rows, `ML-2`..`ML-6` and `ML-8` read as the
    first run did.
  - **`ML-9`'s `DE-5` note is not a reading of this sitting.** It quotes `aws/output/devenv.txt` of
    `2026-10-12T19:49:14Z` (version 6), an earlier session's snapshot left in the worktree, since
    `./aws/devenv.py` was not run; the first run's quote, version 9 of 2026-10-17, stands.
- **[Claude] 1.4, the catalog's reading.** `./scripts/check-gitlab-mirror.py --plan` (01:04:42 to
  01:05:06 UTC) planned `sandbox/egress` at `vpc-egress-v0.18.0` with `-refresh=false` and applied
  nothing. The plan ran, so the Region offers `aws.sagemaker.us-west-2.mlflow`, and the endpoint answers
  for two names the house image's literal lacks:

  ```
    only in the account : .mlflow.sagemaker.us-west-2.app.aws
    only in the account : mlflow.sagemaker.us-west-2.app.aws
  ```

  ```
  fail    GM-4  the literal is the account's list          2 name(s) only in the account, 0 only in the image
  pass    GM-2  the Dockerfile declares one NO_PROXY_LIST  70 entries, sha256 aafa08da98a61f5c
  pass    GM-3  the account's list is readable             72 entries, sha256 6faf2e4761622508, from a plan of terraform-live/sandbox/egress
  ```

  The script exited 2, the fail decision 4 predicts, and wrote the next literal to
  `aws/output/gitlab-mirror-no-proxy.txt`; `GM-1` and `GM-5`..`GM-8` passed.
- **[Claude] 1.2's plans** (Recipe A, steps 3 to 5), kept as `~/tmp/s17-sagemaker.tfplan` and
  `~/tmp/s17-governance.tfplan`. `sandbox/sagemaker`, as `awsds-infra-sandbox-1`:

  ```
    # module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["MLflowApp"] will be created
    # module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["MLflowApp"] will be created
  Plan: 2 to add, 0 to change, 0 to destroy.
  ```

  `data-governance/governance`, as `awsds-infra-data`:

  ```
    # awscc_datazone_project_profile.this["experimentation"] will be updated in-place
  Plan: 0 to add, 1 to change, 0 to destroy.
  ```

  The change adds one element to the profile's `environment_configurations`: `MLflowApp`, `ON_DEMAND`,
  `deployment_order` 11, the Sandbox account in `us-west-2`; the eleven elements already there are
  unchanged. No `.terraform.lock.hcl` changed in either init.
- **[Claude] 1.2, the checklist's step 3: the template** (`docs/SMUS.md`). As `awsds-infra-data`, the
  managed `MLflowApp` blueprint of the domain `awsds-studio` lists one user parameter (key name, optional,
  editable, default present):

  ```
  |  mlflowAppName |  False |  True |  True  |
  ```

  `curl` got HTTP 400 on the template's URL, and `aws s3 cp` as `awsds-infra-sandbox-1` fetched it, 2.6
  KiB of JSON. It declares six parameters, none with `AllowedValues`: `datazoneEnvironmentDomainId`,
  `datazoneEnvironmentProjectId` and `datazoneEnvironmentEnvironmentId` with no default and absent from
  the user parameters (inferred: DataZone fills them), and `datazoneEnvironmentStage` `prod`,
  `datazoneScopeName` `dev` and `mlflowAppName` `mlflow-app`. Its one resource is an
  `AWS::CloudFormation::WaitConditionHandle`, and it declares no `AWS::IAM::Role`. Its outputs import the
  Tooling environment's exports `userRoleArn-<project>-<scope>` and `s3BucketPath-<project>-<scope>`, the
  artifact store being `<that path>/data/ml/mlflow`, and export four values keyed by the environment id.
  So the profile has nothing to declare before the apply, and the stack creates no MLflow App (inferred:
  the app is 1.5's *Create MLflow App*).
- **[Claude] What is owed before the apply**: the checklist's step 4, the console's enable-wizard fields
  for `MLflowApp` in Sandbox, read by the user and cancelled, then the sitting decision 4 orders.

## 2026-10-18 — the `MLflowApp` enable wizard read, and cancelled

*Provenance. The cloud session wrote the route at 18:02 UTC: the infrastructure user with
`InfrastructureAccess` in `Sandbox`, `us-west-2`, the console at `console.aws.amazon.com/datazone`,
**Associated domains**, `awsds-studio`, the **Blueprints** tab, the row "Creates an MLflow App for SageMaker
Unified Studio.", **Enable**, every field noted, out by **Cancel**. The user opened the form at 18:11 UTC, a
session with access to the user's Chrome read it, and the user posted the reading on the project thread at
18:25 UTC. The cloud session compared it with the module and wrote this entry. Nothing was enabled or
applied.*

- **[user] The form**, posted in Portuguese and translated here; every label, value and option is as
  posted. One screen, two sections, the buttons **Cancel** and **Enable blueprint**, and no field marked
  optional:
  - **Permissions and resources → Provisioning role**, a radio. The default, *Create and use a new
    service role*, creates `AmazonSageMakerProvisioning-<domainAccountId>`, trusted entity
    `datazone.amazonaws.com`, managed policy
    `arn:aws:iam::aws:policy/service-role/SageMakerStudioProjectProvisioningRolePolicy`, with a trust
    policy of `sts:AssumeRole` alone under `StringEquals aws:SourceAccount = {{domain_account}}`. *Use an
    existing service role* offers four: `awsds-sandbox-smus-manage-access`,
    `awsds-sandbox-smus-provisioning`, `datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw` and
    `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`.
  - **Authorized domain units (1)**, filled with `awsds-studio` (Root domain), Cascade On and the action
    Remove. **Add** opens "Select domain unit", which lists one unit, `awsds-studio`, already checked,
    and the toggle "Cascade to all child domain units", on.
  - No field for Regions, a manage access role or parameters.
- **[user] Cancel.** `MLflowApp` still reads **Disabled** on `awsds-studio`'s **Blueprints** tab.
- **[Claude] The form against `sagemaker-prereqs-v0.6.0`: the checklist's step 4 closes with no change.**
  The provisioning role `blueprints.tf` names, `awsds-sandbox-smus-provisioning` (`roles.tf`), is one of
  the four offered, and carries the default's managed policy and its `aws:SourceAccount` condition on the
  domain's account; its trust adds `cloudformation.amazonaws.com`. The authorized domain unit is
  `grants.tf`'s `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant on the root unit, with
  `include_child_domain_units = false` against the form's Cascade On: the file justifies it by a domain
  with no subunit, and the form's own list holds only the root, so the two grant the same projects. The
  form has no regional parameter, so nothing joins `blueprints.tf`'s.
- **[Claude] What the configuration sends that the form does not**: the manage-access role and the D13
  boundary, and the `VpcId`, `Subnets` and `AZs` that `blueprints.tf` gives every blueprint, three
  regional parameters the template does not declare (its six, read at 1.2's step 3 from the laptop the
  same day). The environment's deploy at 1.5 is where they meet the template; a refusal there that names
  them points at this configuration, not at the form (inferred).
- **[Claude] What the form adds**: the existing-role list holds both project user roles beside the two
  module roles, so an enable by hand could make a project's own role the provisioning role (inferred: the
  console lists every role that trusts `datazone.amazonaws.com`).
- **[Claude] What is owed before the apply**: 1.1's before, in the portal as the Data Scientist User;
  then the sitting decision 4 orders, the image first.

## 2026-10-18 — the readings with the environment down, and the text they overtook

*Provenance. Claude, in the session "Stage 17: readings and text", a side session of the orchestrating
session, ran every command below from the worktree `stage-17-readings-7be400` at `origin/main` `2074b1b`,
as the infrastructure user with `InfrastructureAccess` in `Sandbox` (`awsds-infra-sandbox-1`), with the
whole environment down. Every call was a read: no plan, no apply, no module tag. The two reports print the
caller's ARN and were not copied; no quoted line carries an account id or an e-mail address.*

- **[Claude] `./aws/devenv.py`** (19:48:48 to 19:48:55 UTC, the report stamped `2026-10-18T19:48:55Z`):
  `wrote aws/output/devenv.txt checks: 5 passed or noted, 1 FAILED`, exit 2, and section 7 `None. Every
  call in this report returned successfully.`

  ```
  fail    DE-2  the account's list is readable                      the state holds neither `no_proxy_all_groups` nor `no_proxy`: the slice is DOWN (an [E] destroy leaves the object and removes the outputs). `make up ENV=sandbox` first - the comparison below is not a divergence, it is an absence
  note    DE-3  the baked list is the account's list                not compared - one of the two sides was not read
  note    DE-6  the last apply's list is inside the account's list  not compared - one of the two outputs was not read
  pass    DE-1  the Dockerfile declares one NO_PROXY_LIST           70 entries, sha256 aafa08da98a61f5c
  pass    DE-4  the proxy URL agrees across the repository          http://proxy.awsds.internal:3128
  pass    DE-5  the registered image carries the account's list     version 9, sha256:b788dbd9c7cf...: 70 names, sha256 aafa08da98a61f5c
  ```
- **[Claude] What `DE-5` compared, read from the script.** `devenv.py` takes the account's list as `DE-5`'s
  reference only when the egress state holds `no_proxy_all_groups`, and the Dockerfile's literal otherwise,
  so the pass above is the image against the Dockerfile, 70 names each. `main` pins `vpc-egress-v0.18.0` on
  `sandbox/egress`, so the first `make up ENV=sandbox` from it writes the 72-entry list (sha256
  `6faf2e4761622508`, read from a plan on 2026-10-18 at 01:05 UTC), and `DE-3` and `DE-5` then fail with 2
  names missing from the image (inferred from the script and that plan; no session has been up since).
  Neither `Makefile` nor `scripts/slices.py` names `devenv`, so `make up` does not refuse on it: the
  failure is a reading, not a gate.
- **[Claude] `./aws/sandbox-ml.py`, third run** (19:49:01 to 19:51:30 UTC, the report stamped
  `2026-10-18T19:51:29Z`): `wrote aws/output/sandbox-ml.txt (all checks passed)`, exit 0, and section 13
  `None. Every call in this report returned successfully.` `ML-7`'s rows for the exercise's types:

  ```
  QUOTA                                                   VALUE  SOURCE   AWS DEFAULT  CODE        LATEST REQUEST
  ml.m5.xlarge for training job usage                     20     applied  0            L-CCE2AFA6  increase to 1 requested 2026-10-17, CASE_OPENED
  ml.m5.large for endpoint usage                          8      applied  0            L-614B09FD  increase to 1 requested 2026-10-17, CASE_OPENED
  ml.m5.large for transform job usage                     8      applied  0            L-236AE59F  increase to 1 requested 2026-10-17, CASE_OPENED
  ml.t3.medium for processing job usage                   10     applied  4            L-0CE343FE  no increase request
  ```

  The values and the requests are those of the second run (2026-10-18 at 01:01 UTC). The request history
  of each quota (`list-requested-service-quota-change-history-by-quota`, read in the same sitting) gives
  `CASE_OPENED`, a desired value of 1.0 and `ACCOUNT` as the level, filed at 21:45:32, 21:45:37 and
  21:45:40 UTC on 2026-10-17 for `L-CCE2AFA6`, `L-614B09FD` and `L-236AE59F`. The first two were last
  updated 13 and 12 seconds after filing; the transform quota's case was last updated at 00:23:33 UTC on
  2026-10-18, the only movement any case shows, and the processing quota has no request. The applied
  values rose between the first run (21:07 UTC on 2026-10-17: the three at zero, the processing quota at
  4) and the second; the fields read do not say what raised them.
- **[Claude] The other sections, as the second run read them.** `ML-1`: both project roles carry
  `EnableSageMakerMLWorkloadsPermissions` `true`, the managed ML policy serves v45, the boundary
  `awsds-sandbox-project-boundary` v2 holds its five statements and the ceiling's seven types, and
  `awsds-sandbox-workflows` grants `AddTags` of `AmazonDataZoneProject` on `processing-job` alone (the gap
  of decision 7); `enableNetworkIsolation` is `true` in both Tooling stacks. `ML-2` to `ML-6`: no MLflow
  App, training job, model package group, endpoint, transform job or pipeline; the only `CreateTrainingJob`
  events in the 90-day lookup are the six refusals of 2026-08-27 and 2026-09-10 by session
  `AmazonMWAAServerless` on `Notebook-task-*` jobs, each `with an explicit deny in a permissions
  boundary`. `ML-7`: no HyperPod cluster or Partner AI app; the MLflow quotas unchanged (3 apps, the
  tracking servers 5, 5 and 1 with at most 10). `ML-8`: both roles carry `EnableAmazonBedrockPermissions`
  `true` and no `EnableAmazonBedrockIDEPermissions`; the four project Bedrock roles carry the boundary and
  their project's tag; no knowledge base, S3 vector bucket, agent, prompt, flow, guardrail or evaluation
  job; the account's one Lambda function is Control Tower's; `amazon.titan-embed-text-v2:0` reads agreement
  `AVAILABLE`, authorization `AUTHORIZED`, entitlement `AVAILABLE`, region `AVAILABLE`; the repository's
  SCP admits `anthropic.claude-haiku-4-5-20251001-v1:0`, `anthropic.claude-opus-4-5-20251101-v1:0` and
  `anthropic.claude-sonnet-4-5-20250929-v1:0` and not the embeddings model, so 7.4a's first sync is still
  expected refused. `ML-9`, with the session down: no interface endpoint and no `awsds-sandbox-egress-allow`
  list; the S3 gateway endpoint's `AllowAwsOwnedServiceBuckets` names `sagemaker-us-west-2` and
  `jumpstart-cache-prod-us-west-2`; the `DE-5` note quotes this sitting's `devenv.py` run, `pass at
  2026-10-18T19:48:55Z: version 9, sha256:b788dbd9c7cf...: 70 names, sha256 aafa08da98a61f5c`, where the
  second run quoted a snapshot of 2026-10-12.
- **[Claude] The coupling between step 1.3 and `TM-21`, read from the files.**
  `terraform-live/sandbox/sagemaker/main.tf` pins `sagemaker-prereqs-v0.6.0` (`0dc159f`, PR #166) and
  passes no `blueprint_names`, so the slice takes the module default, which ends in `MLflowApp` since
  `v0.5.0`. The diff from `v0.5.0` to `v0.6.0` is `data.tf` (a lookup of the organization) and `kms.tf`
  (`aws:PrincipalOrgID` in the `StringEquals` of the project key's `GrantKMSPermissionsForAllProjectRoles`
  and `AllowCreateGrantForProjectRoles`). Any apply of the slice from `main` therefore creates the
  `MLflowApp` configuration and grant and changes the key policy in place; neither goes without the other,
  and both wait on 1.1's before, owed before any apply. No plan of `v0.6.0` has run: the `2 to add` of
  the entry "pass 1's tags on origin, and its readings from the laptop" is `v0.5.0`'s, planned from
  `fa20bfe`, and `2 to add, 1 to change` is an inference. This sitting did not plan the slice; its plan
  belongs to [Stage 11](../plan/stages/stage-11-dlp.md)'s `TM-21`. That stage's log expects, once step 1.3
  has applied first, a plan that changes the key policy alone; with the caller pinned at `v0.6.0`, `main`
  has no apply at `v0.5.0`, so the two are one apply.
- **[Claude] The entry of 2026-10-18 "decision 4 taken" is overtaken on one clause.** It says the image is
  released in the sitting of the group's first apply and that "PR #157's merge goes with it". PR #157 merged
  at 02:33:09 UTC (`e6dfc6a`), before any release, so `main` already pins `vpc-egress-v0.18.0`; the
  entry "pass 1's tags on origin, and its readings from the laptop" records the merge. The stage file's
  decision 4 now says so.
- **[Claude] The text of the stage file this sitting corrected**, each against the file it cites:
  - Status, decision 4 and the risk of the `no_proxy` literal: the merge before any release, and `DE-3`
    and `DE-5` red in any session raised from `main`.
  - The `sandbox/sagemaker` row, 1.2 and 1.3: the caller's `v0.6.0` pin, and the apply that carries
    `TM-21`; `kms.tf` gains no `MLflowApp` statement, where it read "untouched".
  - Steps 7.0a and 7.0b are new: no step carried `AmazonBedrockKnowledgeBase`'s promotion although
    decision 1 is taken, and the roster copies, the template and key-permissions readings and the apply
    are 1.2's and 1.3's shape. 7.2 read "after 1.3" for the knowledge base, which 1.3 does not carry; the
    user's reading of the blueprint's console wizard is owed, as `MLflowApp`'s was. `docs/SMUS.md`'s row
    read "in one change with `MLflowApp`", which PR #157 did not do.
  - "Proves", the menu row, 4.4, decision 8 and the deliverables: [Stage 9](../plan/stages/stage-09-deployment-targets.md)
    took 3.7 as (b) on 2026-10-16, as `DenySageMakerServerlessInference` in the `Workloads` OU document,
    before this stage's reading; 4.4 stays as the Sandbox reading of the boundary and the service.
  - Verification xxi: "three are zero" is the reading of 2026-10-17; the three read 20, 8 and 8 on
    2026-10-18.
  - Decision 11 and 7.4a: the instruments, below.
- **[Claude] Decision 11's amendment reaches three instruments, read from the code and not run.**
  `aws/awslib/bedrockscope.py` builds `pairs[model] = profiles_seen.get(model, "")` for every
  `foundation-model` ARN of `DenyBedrockInvocationOutsideTheScopedModels` (lines 63 to 75), so the
  embeddings model would read as a scoped model with an empty profile. `aws/bedrock-scope.py` then fails
  `BS-2` (`sorted(set(declared.values()))` holds `""`, which is not an active profile) and `BS-7`
  (`grant != declared`, the grant slice's map lacking the model), after calling `get-inference-profile`
  with an empty identifier. `aws/bedrock.py` fails `BR-4` on the same empty profile (line 654).
  `aws/bedrock-usage.py` filters empty profiles (line 306), `scripts/check-gitlab-mirror.py` `GM-8` tests
  the pins against the declared profiles and the grant map, and `aws/sandbox-ml.py` `ML-8` tests
  membership in the dictionary; none of the three fails. An earlier audit of the plan inferred `BS-2` and
  `BS-7` from the same lines; reading them confirms both, and `BR-4` shares the cause.
- **[Claude] What is owed.** [user] 1.1's before in the portal as the Data Scientist User, which needs no
  environment and releases 1.3's apply and `TM-21`'s together; 1.5, 0.3 and 0.7 with a session; the
  console wizard of `AmazonBedrockKnowledgeBase` (7.0a); decision 11. [Claude] The parser change that
  precedes decision 11's amendment, in the sitting of 7.4a. Waiting on the environment: the release of the
  image with the 72-entry literal, 1.4's `mlflow` group, and passes 2 to 7.

## 2026-10-18 — when the Tooling data sources run

*Provenance. Claude, in the side session of the orchestrating session that carries the cross-stage fixes
(worktree `plan-propagation-1018-6f9a01`, at `origin/main` `46abfcf`), with the whole environment down, as
the infrastructure user with `InfrastructureAccess` in `Data Governance` (`awsds-infra-data`). Reads only:
`datazone list-data-sources`, `get-data-source` and `list-data-source-runs`. No quoted line carries an
account id or an e-mail address. Times are UTC.*

- **[Claude] Each project's `Tooling-default-sagemaker-modelpackagegroup-datasource`.**
  `eighth-experimentation`'s, created 2026-08-23 at 17:32 on `cron(32 17 * * ? *)`, started its runs at
  17:38:11 on each of 2026-10-14 to 2026-10-18, the newest `RUNNING` and the four before it `FAILED`.
  `test-experimentation`'s, created 2026-10-15 at 06:06 on `cron(6 6 * * ? *)`, started its runs at 06:16:57
  on 2026-10-16, 2026-10-17 and 2026-10-18, the newest `RUNNING` and the two before it `FAILED`. A run
  starts 6 and 10 minutes after its cron's minute. Step 3.3 and the pass table named 17:32 UTC and "the
  next day" for both sources; they now name the project's own source and both times.
- **[Claude] The live `Workloads` document** (`organizations describe-policy` as `awsds-infra-identity`,
  `InfrastructureAccess` in `Identity`, read-only): `awsds-org-scp-ou-workloads`, 2,499 bytes, nine
  statements, the last `DenySageMakerServerlessInference`, as Stage 9's log of the same day records for
  its apply at 19:54. 7.4a and 4.4 say so. The plan of `sandbox/sagemaker/` on `main`'s pin that step 1.2
  quotes (2 to add, 1 to change, 0 to destroy, not applied) is Stage 11's reading, in its log.

## 2026-10-18 — what raised the three quotas, read in the trail

*Claude, the orchestrating session of 2026-10-18's third round, from the laptop as the infrastructure
user (`awsds-infra-sandbox-1`, `InfrastructureAccess` in `Sandbox Account 1`), read-only, about 22:20 UTC.*

- **[Claude] The requests**: `cloudtrail lookup-events` by `EventName=RequestServiceQuotaIncrease` from
  2026-10-15 returns three calls, 2026-10-17 21:45:32Z, 21:45:37Z and 21:45:40Z, as
  `InfrastructureAccess`, each for `desiredValue` 1.0 (`L-CCE2AFA6`, `L-614B09FD`, `L-236AE59F`), each
  answered `PENDING`. `list-requested-service-quota-change-history` reads all three `CASE_OPENED`.
- **[Claude] The values**: `list-service-quotas` reads `L-CCE2AFA6` 20, `L-236AE59F` 8 and `L-614B09FD` 8,
  as at 19:51 UTC.
- **[Claude] Nothing in the account records the raise**: by `EventSource=servicequotas.amazonaws.com`
  from 2026-10-17 21:00Z to 2026-10-18 21:00Z the only writes are those three requests (the rest are
  `List*` and `Get*` reads), and `support.amazonaws.com` returns no event. AWS applied values above the
  ones asked for, on its side, with the cases still open. Verification xxi says so.

## 2026-10-19 — 1.3's plans on `main`'s pins, 1.1's before, and the applies

*Provenance. Claude, in the session "Stage 17 1.1 and 1.3: MLflow reading and the applies", which the
Stage 18 session started to release that stage's step 2.7, from the worktree `stage-17-readings-7be400`
at `origin/main` `47f5759`, as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`) and in `Data Governance` (`awsds-infra-data`), with the whole environment down. Every AWS call Claude ran was a read or a plan;
the applies are the user's, since the app's auto-mode classifier refuses them to Claude (Stage 18's log,
2026-10-19). No quoted line carries an account id or an e-mail address. Times are UTC.*

- **[Claude] What `main` pins.** `sandbox/sagemaker` takes `sagemaker-prereqs-v0.6.0`, whose default
  roster ends in `MLflowApp`, and the `experimentation` profile's list ends in `MLflowApp`. PR #196
  (Stage 18) is open, so `governance/` carries no `deployment` profile and `SMUS_DEPLOYMENT_MEMBERS` is
  empty. `gen-tfvars.py` wrote `blueprints_enabled = true` for the first slice, and
  `profiles_enabled = true` with `members` holding `sandbox` alone for the second. Neither init changed a
  `.terraform.lock.hcl`.
- **[Claude] `sandbox/sagemaker`, planned at `v0.6.0`** as `awsds-infra-sandbox-1`, 04:51:34 to
  04:52:03, `-input=false`, saved as `~/tmp/s17-sagemaker-1019.tfplan`:

  ```
    # module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["MLflowApp"] will be created
    # module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["MLflowApp"] will be created
    # module.sagemaker_prereqs.module.project_key.aws_kms_key.this will be updated in-place
  Plan: 2 to add, 1 to change, 0 to destroy.
  ```

  The configuration names `awsds-studio`, `us-west-2`, the boundary `awsds-sandbox-project-boundary`,
  `awsds-sandbox-smus-manage-access`, `awsds-sandbox-smus-provisioning` and the regional parameters
  `AZs` (`usw2-az1,usw2-az2`), `Subnets` and `VpcId`; the grant is `CREATE_ENVIRONMENT_FROM_BLUEPRINT`
  to the root domain unit's project contributors, `include_child_domain_units = false`. The key policy
  keeps its nine `Sid`s; `terraform show -json` on the saved plan reads two of them changed,
  `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`, each gaining
  `aws:PrincipalOrgID` in its `StringEquals` and nothing else: [Stage 11](../plan/stages/stage-11-dlp.md)'s
  `TM-21`, the plan its session read on 2026-10-18.
- **[Claude] `data-governance/governance`, planned** as `awsds-infra-data`, 04:52:28 to 04:52:48, saved
  as `~/tmp/s17-governance-1019.tfplan`:

  ```
    # awscc_datazone_project_profile.this["experimentation"] will be updated in-place
  Plan: 0 to add, 1 to change, 0 to destroy.
  ```

  The one changed attribute is `environment_configurations`, eleven elements before and twelve after:
  `MLflowApp`, `ON_DEMAND`, `deployment_order` 11, `us-west-2`, no parameters, the same account as the
  other eleven, which keep their orders 0 to 10 unchanged. No `deployment` profile and no grant is in the
  plan, so the apply carries nothing of Stage 18's 2.6 or 2.7.
- **[user] The portal, opened for Claude.** Before 05:01 the user wrote in this session *"abri uma
  sessão no chrome para você, com a página aberta"*: the user's Chrome held the portal signed in as the
  Data Scientist User. The page's own `list-groups-for-user` request names the DataZone user that
  `get-user-profile` resolves to *Data Scientist User*, so the reading is that persona's.
- **[Claude] 1.1, the before, read 05:01 to 05:04** through Claude in Chrome, in a tab of its own, in
  `eighth-experimentation` (`avhvbqn37ty7m8`). Nothing was submitted or created; the two disabled items
  were hovered, never clicked, and the legacy page's two *Create* buttons were not clicked. The portal
  has two MLflow entries, where the stage names one path, "Compute → AI/ML → MLflow":
  - **AI/ML → MLflow**, the left navigation (`/projects/<project>/experiments`), the legacy experiments
    page. A red notice, still served three days past the date it names:

    ```
    This page will be removed on September 16, 2026
    To view your experiments, go to Compute and open an MLflow Tracking Server or App.
    ```

    Then a banner, *"New! Mlflow 3.0 is now available on SageMaker AI. Accelerate your generative AI
    development with fully managed experiment tracking, observability, and performance evaluation."*,
    with a **Create Tracking Server** button, and the body *"Experiments / Create, analyze, and manage
    MLflow experiments. / No tracking server. / To get started with MLflow experiments, create an MLflow
    Tracking Server."* with a **Create** button. The page offers the tracking server alone.
  - **Compute → MLflow**, a tab of the Compute page (`/projects/<project>/compute?type=mlflow`), beside
    *SQL analytics*, *Data processing*, *HyperPod clusters*, *Spaces* and *Workflow environments*:
    *"MLflow environments (0)"*, *"No MLflow Apps or Tracking Servers found"*, and a **Create** dropdown
    whose two items are greyed out, each with a tooltip:

    ```
    Create MLflow Tracking Server   The MLExperiments blueprint is not enabled for this project. Contact your administrator to enable it.
    Create MLflow App               The MLflowApp blueprint is not enabled for this project. Contact your administrator to enable it.
    ```

  - **The page's requests**: DataZone reads of the project profile, the blueprint configurations, the
    managed blueprints and eleven blueprints by id, and the project's environments; and two `POST`s to
    `api.sagemaker.us-west-2.amazonaws.com`, both `200`, whose bodies were not read (inferred: the two
    MLflow list calls).
  - **Project details** (the project's actions menu): profile `experimentation`, **Update status** *Up
    to date*. The actions menu holds *Project details*, *Copy project link*, *Update project* and
    *Delete project*, and the **Manage** menu *Govern*, *Browse catalog* and *Catalog management*; no
    page lists capabilities, the page 1.5 names (inferred: in this portal a profile change reaches a
    project through *Update project*, not opened).
  - An Amazon Q prompt sat at the page's foot on every page, *"Amazon Q can now list and describe your
    AWS resources. By continuing, you consent to Amazon Q making cross-Region calls to access your
    resources."*, with *Don't allow* and *Continue*; it was left unanswered.
- **[Claude] Verification i's before: the blueprint gates the app.** The portal refuses the create in the
  menu, by a tooltip naming the blueprint, before any SageMaker call, so the project role's
  `SageMakerMlflowServerlessPermission` (`sagemaker:CreateMlflowApp` on `mlflow-app/*` under
  `aws:ResourceTag/AmazonDataZoneProject`, read in v45 the same hour) is never reached; whether it admits
  the create is 1.5's reading. The after is the same tab once `governance/` and `sandbox/sagemaker/`
  are applied, and the project's update status beside it.
- **[user] Both applies**, from the saved plans, in a terminal of the project folder with `-chdir` into
  this worktree, pasted into this session. The paste, with the account ids replaced:

  ```
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/stage-17-readings-7be400/terraform-live/sandbox/sagemaker apply -input=false "$HOME/tmp/s17-sagemaker-1019.tfplan"
  module.sagemaker_prereqs.module.project_key.aws_kms_key.this: Modifying... [id=a81b1ef3-716f-4105-bb42-14184a6e2174]
  module.sagemaker_prereqs.module.project_key.aws_kms_key.this: Modifications complete after 6s [id=a81b1ef3-716f-4105-bb42-14184a6e2174]
  module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["MLflowApp"]: Creating...
  module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["MLflowApp"]: Still creating... [00m10s elapsed]
  module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["MLflowApp"]: Creation complete after 15s [id=dzd-d8yrvx1ko7im6o|agjvpzxbha9fbk]
  module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["MLflowApp"]: Creating...
  module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["MLflowApp"]: Creation complete after 6s [id=dzd-d8yrvx1ko7im6o|00MWjiPOdj|<Sandbox Account 1>:agjvpzxbha9fbk|ENVIRONMENT_BLUEPRINT_CONFIGURATION|CREATE_ENVIRONMENT_FROM_BLUEPRINT]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 2 added, 1 changed, 0 destroyed.

  Outputs:

  manage_access_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-smus-manage-access"
  project_boundary_arn = "arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary"
  project_key_arn = "arn:aws:kms:us-west-2:<Sandbox Account 1>:key/a81b1ef3-716f-4105-bb42-14184a6e2174"
  provisioning_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-smus-provisioning"
  regional_parameters = {
    "AZs" = "usw2-az1,usw2-az2"
    "Subnets" = "subnet-016b5a3a62c739894,subnet-09d3399d6b0fec93a"
    "VpcId" = "vpc-00dca74a35159b11c"
  }
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-data terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/stage-17-readings-7be400/terraform-live/data-governance/governance apply -input=false "$HOME/tmp/s17-governance-1019.tfplan"
  awscc_datazone_project_profile.this["experimentation"]: Modifying... [id=dzd-d8yrvx1ko7im6o|dh60xbal05q64w]
  awscc_datazone_project_profile.this["experimentation"]: Modifications complete after 7s [id=dzd-d8yrvx1ko7im6o|dh60xbal05q64w]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

  Outputs:

  domain_arn = "arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o"
  domain_execution_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-execution"
  domain_id = "dzd-d8yrvx1ko7im6o"
  domain_service_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-service"
  portal_url = "https://dzd-d8yrvx1ko7im6o.sagemaker.us-west-2.on.aws"
  project_profile_creators = {
    "experimentation" = "sso-group-data-scientists"
  }
  project_profile_ids = {
    "experimentation" = "dh60xbal05q64w"
  }
  root_domain_unit_id = "bzq0cbh2gd0f4g"
  ```

- **[Claude] When, from the trails.** Sandbox's reads `PutKeyPolicy` at 05:11:46 and
  `PutEnvironmentBlueprintConfiguration` at 05:11:59, both as `InfrastructureAccess`; Data Governance's
  reads `UpdateProjectProfile` at 05:12:33, the profile's `lastUpdatedAt`. Neither trail's lookup showed a
  `CreatePolicyGrant` event at 05:20.
- **[Claude] Re-planned, both `No changes. Your infrastructure matches the configuration.`**:
  `sandbox/sagemaker` 05:13:11 to 05:13:39, `governance/` 05:13:39 to 05:14:00. The second ran before
  Stage 18's 2.7 apply from a checkout holding PR #196; from this worktree, cut from `main` without it, a
  later plan of `governance/` reads that stage's `deployment` profile and grant as destroys, so none ran.
- **[Claude] Read back.** The project key's policy keeps its nine `Sid`s; the two with `Principal *`,
  `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`, carry
  `aws:PrincipalOrgID`, and the other seven read as before. `list-environment-blueprint-configurations`
  as `awsds-infra-sandbox-1` returns twelve. `experimentation` is `ENABLED` with twelve environment
  configurations, `MLflowApp` `ON_DEMAND` at order 11.
- **[Claude] `./aws/studio.py`**, 05:14:41 to 05:16:00: `wrote aws/output/studio.txt (some calls FAILED -
  see section 10)`, exit 1. Section 10 holds seven `sts get-caller-identity` calls of the persona and
  Control Tower profiles, whose SSO sessions were not signed in. `US-3` passes, *"12 blueprint
  configuration(s) in awsds-infra-sandbox-1 — all inside decision 5's category 1"*, as do `US-4`
  (`experimentation`, one) and `US-8` (six project roles bounded); the rest pass or note. `US-10` notes one
  running app, the Data Scientist User's default JupyterLab space on `ml.t3.medium`, `InService` since
  04:59:27, which the 60-minute idle shutdown stops (`US-7`).
- **[Claude] Verification i's after, read 05:17 to 05:24** through Claude in Chrome, nothing submitted:
  - `eighth-experimentation`, Compute → MLflow: both items of the **Create** dropdown still greyed out,
    *Create MLflow App* with the same tooltip, *"The MLflowApp blueprint is not enabled for this
    project. Contact your administrator to enable it."*; Project details' **Update status** still *Up to
    date*.
  - `test-experimentation`, the same tab on its first load in that browser: the page fetched the profile,
    both blueprint-configuration lists and twelve blueprints by id, `agjvpzxbha9fbk` among them
    (`MLflowApp`, by `get-environment-blueprint`), and the item carries the same tooltip.
  - `test-experimentation`'s Generative AI → AI apps: *"This tool is not available for this project. To
    enable it, activate the "Generative AI Application Development" project profile or its associated
    blueprints using the following documentation."* The six Bedrock blueprints have been in the profile
    since 2026-08-21, before either project.
  - Each project holds two environments: `Tooling`, `ACTIVE`, and a `create-datalake-database-env-*` of
    `DataLake`'s configuration, `CREATE_FAILED` on the manage-access role's
    `lakeformation:CreateLakeFormationOptIn`, [6f](log-stage-06f-data-governance.md)'s refusal of
    2026-09-13, repeated in the second project on 2026-10-15. The portal deploys an `ON_DEMAND`
    environment from the flow that needs it, and the MLflow flow stops at the menu before reaching one.
- **[Claude] What the after says.** 1.3's two objects are live and read back, and neither project's
  portal offers the app. Both projects predate 05:12:33, but the Bedrock tools are refused although
  their blueprints predate both projects, so "a profile change does not reach an existing project" does
  not explain both readings. What the portal wants beyond the configuration and the profile is unread,
  and 1.5's premise, a capabilities page offering the blueprint, does not hold in this portal: 1.5 starts
  by reading what makes the item available.
- **[Claude] [Stage 11](log-stage-11-dlp.md)'s `TM-21` is applied with 1.3.** `TM-21` and `EXC-18` stay
  open until a snapshot in Audit reads the analyzer's finding `RESOLVED`, that stage's condition.
- **[Claude] What is owed.** [user] 1.5, from what makes *Create MLflow App* available; then 1.4's
  sitting, the image first (decision 4). [Claude] 1.7 after 1.5.

## 2026-10-19 — 1.5's reading: what greys out *Create MLflow App*, and what refuses the Bedrock tools

*Provenance. Claude, in the session that took 1.5 after PR #197 merged, from the worktree
`verificar-ambiente-down-e95914` at `origin/main` `b737154`, with the whole environment down. AWS reads
as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`)
and in `Data Governance` (`awsds-infra-data`). The portal was read through Claude in Chrome, in a tab of
its own in the user's session as the Data Scientist User: nothing was created or submitted, the one click
was the left navigation's *AI apps* link, and the *Create* dropdown was never opened, its items being read
from the page's own state. The portal's JavaScript was downloaded from its public CDN and read, never run;
its logic is described below in Claude's words, each bundle named by its content hash. No quoted line
carries an account id or an e-mail address. Times are UTC.*

- **[Claude] The projects** (`get-project`, 05:46): both `ACTIVE` on profile `dh60xbal05q64w`,
  `overallDeploymentStatus` `SUCCESSFUL`, last updated 2026-10-15 at 06:15:45 (`eighth-experimentation`)
  and 06:15:15 (`test-experimentation`). The response carries no profile version; `update-project` takes
  `--project-profile-version`, whose one accepted value is `latest`.
- **[Claude] The profile**, read as `awsds-infra-data`, `awsds-infra-sandbox-1` being refused
  (*"no resource-based policy allows the datazone:GetProjectProfile action"*): `ENABLED`, last updated
  05:12:33, twelve environment configurations, `Tooling` `ON_CREATE` at order 0 and eleven `ON_DEMAND`;
  `MLflowApp` at order 11, configuration `3342d20e-001b-4b95-9053-fbbc04b5c303`, blueprint
  `agjvpzxbha9fbk`. No `AmazonBedrockKnowledgeBase` element.
- **[Claude] The environments**: each project's two, unchanged since 05:24 (`Tooling` `ACTIVE`, the
  `DataLake` one `CREATE_FAILED`).
- **[Claude] The blueprint configurations, per account**: `list-environment-blueprint-configurations`
  returns **12** as `awsds-infra-sandbox-1` (one page, no `nextToken`), `MLflowApp`'s with the same roles,
  boundary and regional parameters as the Bedrock ones, and **0** as `awsds-infra-data` (05:50:37), the
  domain's own account, where `US-3` requires none (D22).
- **[Claude] How the portal deployed the `DataLake` environments**, from Data Governance's trail:
  `CreateEnvironment` at 2026-09-13 01:45:21 and 2026-10-15 06:08:17, each as
  `awsds-data-studio-domain-execution`, with `DataLake`'s `environmentConfigurationId`, its blueprint id,
  the account, the Region and one user parameter, `glueDbName`. The portal acts in DataZone as the domain
  execution role, in the domain's account.
- **[Claude] What the page did on two loads** of `test-experimentation`'s Compute → *MLflow* (05:51:09
  and 05:51:24, Data Governance's trail): two `ListEnvironmentBlueprintConfigurations` as
  `awsds-data-studio-domain-execution`, no error; twelve `GetEnvironmentBlueprint`, one per profile
  configuration; one `GetProjectProfile`.
- **[Claude] The dropdown's state**, from the page's React props at 05:52, the menu closed:

  ```
  create-tracking-server  "Create MLflow Tracking Server"  disabled: true  "The MLExperiments blueprint is not enabled for this project. Contact your administrator to enable it."
  create-mlflow-app       "Create MLflow App"              disabled: true  "The MLflowApp blueprint is not enabled for this project. Contact your administrator to enable it."
  ```

- **[Claude] Why, from the page's query cache**: both blueprint lookups failed, with one message.

  ```
  ["getMLflowAppBPConfig","MLExperiments"]  status: error  "No environment blueprint configurations found"  2026-10-19T05:51:24.047Z
  ["getMLflowAppBPConfig","MLflowApp"]      status: error  "No environment blueprint configurations found"  2026-10-19T05:51:24.716Z
  ```

- **[Claude] The gate, read in the portal's code**
  (`a.b.cdn.console.awsstatic.com/a/v1/WEM6FZF2DHQXD46KL5UJ4ENIRJAVORMDCSYVJVKZIIQ3VJQMLLXA/index.js`,
  6,071,041 bytes). *Create MLflow App* is enabled when a lookup returns an environment configuration
  id. The lookup resolves the name `MLflowApp` to a blueprint id by calling
  `ListEnvironmentBlueprintConfigurations` with the domain id alone, as the domain execution role, and
  reading each listed blueprint's name; an empty list throws the message above. It then takes the
  profile's configuration with that blueprint id. The item is also disabled when that configuration is
  `ON_CREATE`; it carries no owner check, where *Create MLflow Tracking Server* requires the project
  owner. The list the portal reads is the domain account's, which holds none, while the twelve
  configurations are `Sandbox Account 1`'s, so the item stays greyed in every project of this domain
  whatever the profile carries. What would enable it is an `MLflowApp` configuration in Data Governance
  (read from the code, not measured).
- **[Claude] What the create sends**, from the same code: `CreateEnvironment` with the project, the
  blueprint id, the profile's configuration id, the app's name as the environment's name, and one user
  parameter, `mlflowAppName`, the same name. No artifact store, role or key travels with the create; the
  form's artifact-storage field serves `UpdateMlflowApp`.
- **[Claude] *Update project* changes nothing here**: the portal's `GetUpdateEligibility` for
  `test-experimentation`, read from the page's cache at 06:03, answers `{"status": "UPDATE_NOT_AVAILABLE"}`,
  and the lookup reads no project field. A project created after the profile change reads the same
  domain-account list; none was created.
- **[Claude] The Bedrock tools.** `test-experimentation`'s *AI apps* link opened
  `/projects/<project>/bedrock/playground/chat`: *"This tool is not available for this project."* The
  Bedrock module (`…/RLDNULH5G2X4O5BRWMHN7HKFEWSA3P4EGBV33RMSSWWVVU6UT5HQ/assets/module-GY0Cw3hN.js` and
  `App-D6IrICgA.js`) maps the profile's configurations to resource types by managed-blueprint name, and
  opens the whole Generative AI application, the Playground included, only when seven types are all
  present: `ChatApp`, `Evaluation`, `FlowApp`, `Function`, `Guardrail`, `KnowledgeBase` and `Prompt`. The
  map read for `test-experimentation` (05:56:24) holds `Project` (from `Tooling`), `ChatApp`,
  `Guardrail`, `Function`, `Prompt`, `Evaluation` and `FlowApp`. `KnowledgeBase` is missing because
  `AmazonBedrockKnowledgeBase` is category 2 and outside the profile; the refusal follows from the
  profile alone, the domain account's configurations playing no part on that path.
- **[Claude] AWS's pages, read the same morning.** *Update a project* (user guide) says an admin's
  blueprint change reaches a project when its owner runs *Actions → Update project*. The admin guide's
  project-profile pages describe `ON_DEMAND` blueprints as enabled later by project users and name no page
  that does it. The *Generative AI application development* template enables seven Bedrock blueprints,
  `AmazonBedrockKnowledgeBase` among them. `PutEnvironmentBlueprintConfiguration` requires
  `enabledRegions` with a minimum of 0 items, and `ListEnvironmentBlueprintConfigurations` takes no
  account filter. No page says the portal's MLflow entries read the domain account's configurations.
- **[Claude] The three candidates, read.** A project created after the profile change: no, the gate
  reads no project. The owner's *Update project*: no, `UPDATE_NOT_AVAILABLE`. A DataZone path that
  deploys the environment: `CreateEnvironment` with configuration `3342d20e-…` is the request the
  portal's create sends, and the gate it skips is the page's. DataZone authorizes it against the
  `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grant on `Sandbox Account 1`'s configuration, held by the
  projects' contributors. The infrastructure user is a contributor of both projects through a group
  profile whose role is `Sandbox Account 1`'s `InfrastructureAccess`; the Data Scientist User owns both
  through an SSO profile, which no CLI identity reaches.

## 2026-10-19 — 1.5: the app created through `create-environment`

*Provenance. The user ran the create in a terminal of the laptop as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`), and pasted it into this
session; the account id in the paste is replaced by `<Sandbox Account 1>`. The readings after it are
Claude's, read-only, with the same identities as the entry above, and Claude in Chrome reading the
portal's *MLflow* tab in the user's session with nothing clicked. Times are UTC.*

- **[user] The path.** Asked how to go on from the reading above, the user chose *"API, você executa
  (Recomendado)"*: the request the portal's create would send, run by the user, nothing in D22 changed
  and the item left greyed. The options declined were the page's lookup filled in the user's browser,
  an inert `MLflowApp` configuration in Data Governance (an amendment of D22 that fails `US-3` as
  written), and stopping at the reading.
- **[user] The create and the list**, pasted:

  ```
  AWS_PROFILE=awsds-infra-sandbox-1 aws datazone create-environment --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier avhvbqn37ty7m8 --environment-configuration-id 3342d20e-001b-4b95-9053-fbbc04b5c303 --environment-blueprint-identifier agjvpzxbha9fbk --name ml-demo-mlflow --user-parameters name=mlflowAppName,value=ml-demo-mlflow --region us-west-2

  {
      "projectId": "avhvbqn37ty7m8",
      "id": "cu3flqsgefwwls",
      "domainId": "dzd-d8yrvx1ko7im6o",
      "createdBy": "fb9dc808-ab98-4030-bef4-3103631a57a3",
      "createdAt": "2026-10-19T06:39:30.209633+00:00",
      "updatedAt": "2026-10-19T06:39:30.312524+00:00",
      "name": "ml-demo-mlflow",
      "awsAccountId": "<Sandbox Account 1>",
      "awsAccountRegion": "us-west-2",
      "provider": "Amazon SageMaker",
      "status": "CREATING",
      "userParameters": [
          {
              "keyName": "mlflowAppName",
              "description": "The name of MLflow Serverless app",
              "fieldType": "String",
              "defaultValue": "ml-demo-mlflow",
              "isEditable": true,
              "isOptional": false
          }
      ],
      "lastDeployment": {
          "deploymentId": "cucx6zpvyihno0",
          "deploymentType": "CREATE",
          "deploymentStatus": "PENDING_DEPLOYMENT",
          "isDeploymentComplete": false
      },
      "provisioningProperties": {
          "cloudFormation": {
              "templateUrl": "https://env-partner-blueprin-wg7wpbgxcioem11yato9kyjmqipx4usw2b-s3alias.s3-accesspoint.us-west-2.amazonaws.com/v2/DataZone-Amazon-SageMaker-MLflowServerless-prod-20251008.template.json"
          }
      },
      "deploymentProperties": {
          "startTimeoutMinutes": 5,
          "endTimeoutMinutes": 180
      },
      "environmentBlueprintId": "agjvpzxbha9fbk",
      "environmentConfigurationId": "3342d20e-001b-4b95-9053-fbbc04b5c303",
      "environmentConfigurationName": "MLflowApp"
  }
  (END)

  AWS_PROFILE=awsds-infra-sandbox-1 aws datazone list-environments --domain-identifier dzd-d8yrvx1ko7im6o --project-identifier avhvbqn37ty7m8 --region us-west-2 --query "items[].[name,status]" --output table

  ----------------------------------------------------------------------------
  |                             ListEnvironments                             |
  +---------------------------------------------------------+----------------+
  |  create-datalake-database-env-mydatabase-1789263919641  |  CREATE_FAILED |
  |  Tooling                                                |  ACTIVE        |
  |  ml-demo-mlflow                                         |  ACTIVE        |
  +---------------------------------------------------------+----------------+
  ```

  `createdBy` is the DataZone IAM profile of `Sandbox Account 1`'s `InfrastructureAccess` role.
- **[Claude] The trails, in order.** `CreateEnvironment` 06:39:30, in Sandbox's trail as
  `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d` and in Data Governance's with the request as
  sent and the CLI's user agent (`aws-cli/2.37.12`); `CreateStack` 06:39:42 and `DescribeStacks` 06:39:52
  to 06:40:03 as `awsds-sandbox-smus-provisioning`, session
  `AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>`; `CreateMlflowApp` and `AddTags` 06:39:55 in the
  same session, the second adding `AmazonDataZoneBlueprint` `MLflowApp`. `CreateMlflowApp`, from
  Sandbox's trail:

  ```
  "userIdentity": {"type": "AssumedRole", "arn": "arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-smus-provisioning/AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>", "invokedBy": "datazone.amazonaws.com"}
  "sourceIPAddress": "datazone.amazonaws.com", "userAgent": "datazone.amazonaws.com", "vpcEndpointId": null
  "requestParameters": {"name": "ml-demo-mlflow", "artifactStoreUri": "s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/mlflow", "roleArn": "arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c", "tags": [{"key": "AmazonDataZoneEnvironment", "value": "cu3flqsgefwwls"}, {"key": "AmazonDataZoneProject", "value": "avhvbqn37ty7m8"}, {"key": "AmazonDataZoneDomain", "value": "dzd-d8yrvx1ko7im6o"}]}
  "responseElements": {"arn": "arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:mlflow-app/app-IXYTVNFGQRKM"}
  ```

  No `KmsKeyId` travels in the request.
- **[Claude] The environment** (`get-environment`, 06:40:45): `ACTIVE`, updated 06:40:03, deployment
  `cucx6zpvyihno0` `CREATE` `SUCCESSFUL`, five provisioned resources, all *"Amazon DataZone Generated"*:
  `mlflowAppArtifactStoreUri`, `cloudFormationStackId`, `mlflowAppName`, `userRoleArn` (the project
  role) and `mlflowAppArn`.
- **[Claude] The stack** `DataZone-Env-cu3flqsgefwwls`: `CREATE_COMPLETE`, created 06:39:42, parameters
  `datazoneEnvironmentEnvironmentId`, `datazoneEnvironmentProjectId`, `datazoneEnvironmentDomainId`,
  `mlflowAppName`, `datazoneEnvironmentStage` `prod` and `datazoneScopeName` `dev`, four outputs naming
  the app, the stack, the user role and the store, and one resource, `WaitHandle`
  (`AWS::CloudFormation::WaitConditionHandle`, whose presigned URL is not copied here). The app is no
  stack resource: DataZone's deployer creates it beside the stack.
- **[Claude] The app** (`describe-mlflow-app`, 06:41), `Status` `Creating` then:

  ```
  "Arn": "arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:mlflow-app/app-IXYTVNFGQRKM",
  "Name": "ml-demo-mlflow",
  "ArtifactStoreUri": "s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/mlflow",
  "RoleArn": "arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
  "ModelRegistrationMode": "AutoModelRegistrationDisabled",
  "CreationTime": "2026-10-19T03:39:54-03:00",
  "CreatedBy": {"IamIdentity": {"Arn": "arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-smus-provisioning/AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>"}},
  "WeeklyMaintenanceWindowStart": "Sun:14:15"
  ```

  Its tags are `AmazonDataZoneBlueprint` `MLflowApp`, `AmazonDataZoneEnvironment` `cu3flqsgefwwls`,
  `AmazonDataZoneProject` `avhvbqn37ty7m8` and `AmazonDataZoneDomain`. A 30-second poll read `Created`
  at 06:44:27, `LastModifiedTime` `2026-10-19T03:44:15.364000-03:00` (06:44:15 UTC), about four minutes
  twenty seconds after `CreateMlflowApp`. The response carries no `KmsKeyId` and no
  `AccountDefaultStatus`.
- **[Claude] The store's bucket**: `get-bucket-encryption` on `awsds-sandbox-smus-projects` reads
  `aws:kms` under the project key (`alias/awsds-sandbox-project`), `BucketKeyEnabled` `true`, SSE-C
  blocked; the store's prefix held no object at 06:41.
- **[Claude] The portal**, `eighth-experimentation`'s Compute → *MLflow*: at 06:43 *"MLflow environments
  (1)"*, the row `ml-demo-mlflow`, `Creating`, `App`, *October 19, 2026, 03:39 (UTC-03:00)*, with *Open*;
  at 06:46 the same row reads `On`, and both *Create* items are still disabled with the same tooltips,
  the page's two lookups failing again at 06:45:58 and 06:45:59 with *"No environment blueprint
  configurations found"*. The app's row links to `/projects/<project>/compute/mlflow-app/cu3flqsgefwwls`,
  the environment's id.
- **[Claude] 1.7, `./aws/sandbox-ml.py`** (generated 06:47:41, *"all checks passed"*), its `ML-2` rows:

  ```
  NAME            STATUS   VERSION  ARTIFACT STORE                                                                         KEY  ROLE                                             REGISTRATION                   TAG
  ml-demo-mlflow  Created  3.10.1   s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/mlflow  -    datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c  AutoModelRegistrationDisabled  avhvbqn37ty7m8

  note    ML-2  ml-demo-mlflow                                                                   Created; MLflow 3.10.1; role datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c; registration AutoModelRegistrationDisabled; account default -; maintenance Sun:14:15; tag avhvbqn37ty7m8; key none is not the project key (verification iv).
  note    ML-2  CreateMlflowApp ml-demo-mlflow at 2026-10-19T06:39:55Z                           awsds-sandbox-smus-provisioning/AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>, no vpcEndpointId (verification ii).
  ```

  `ML-7` reads the MLflow quotas, among them *"The maximum number of MLflow Apps that can be created. =
  3 (applied)"*, *"Rate of CreateMlflowApp requests = 1 (applied)"* and *"Rate of
  CreatePresignedMlflowAppUrl requests = 5 (applied)"*.
- **[user] *Open***, on the app's row in `eighth-experimentation`'s *MLflow* tab, after 06:48: the
  MLflow UI opened in a new tab of the laptop's browser (the user's answer in this session; the host
  was not recorded).
- **[Claude] The URL's trail**: `CreatePresignedMlflowAppUrl` at 06:54:54 as
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, session
  `28f1b390-0041-7068-8cc7-9ccef94277d1@5hkjdsy3umpi1c` (the Data Scientist User's DataZone id and the
  `Tooling` environment's), the browser's user agent, no `vpcEndpointId`, the app's ARN as the only
  parameter, no error. The portal mints the URL as the project role, from the laptop, on the public
  SageMaker API.

## 2026-10-19 — 7.0's before, and 7.0a's readings: the key page, the template, the console's form

*Provenance. Claude, in a session the Stage 17 1.5 session started for 7.0a and 7.0b, from the worktree
`stage-17-readings-7be400` at `origin/main` `1b95eaa`, as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and in `Data Governance`
(`awsds-infra-data`), with the whole environment down. Every AWS call Claude ran was a read. The console
session was the user's, as the infrastructure user in `Sandbox Account 1`, in a tab the user moved into
Claude in Chrome's group: Claude navigated it by URL and read it, and the user's two clicks were
**Enable** and **Cancel**. The console's JavaScript was downloaded from its public CDN and read, never
run. No quoted line carries an account id or an e-mail address. Times are UTC.*

- **[Claude] 7.0, the before.** `./aws/sandbox-ml.py`, 17:33:33 to 17:36:09 (the report stamped
  17:36:07Z): *"all checks passed"*, exit 0, section 13 *"None."* Its `ML-8` rows, padding
  compressed:

  ```
  note   ML-8  4gqfau9xuo6e4w: Bedrock tags   EnableAmazonBedrockPermissions true, EnableAmazonBedrockIDEPermissions absent (verification xvii).
  note   ML-8  avhvbqn37ty7m8: Bedrock tags   EnableAmazonBedrockPermissions true, EnableAmazonBedrockIDEPermissions absent (verification xvii).
  note   ML-8  knowledge bases   none - not built yet (pass 7, step 7.4a).
  note   ML-8  S3 vector buckets   none
  note   ML-8  agents   none - not built yet (pass 7).
  note   ML-8  prompts   none - not built yet (pass 7).
  note   ML-8  flows   none - not built yet (pass 7).
  note   ML-8  guardrails   none - not built yet (pass 7).
  note   ML-8  evaluation jobs   none - not built yet (pass 7).
  note   ML-8  amazon.titan-embed-text-v2:0 availability   agreement AVAILABLE, authorization AUTHORIZED, entitlement AVAILABLE, region AVAILABLE
  note   ML-8  DenyBedrockInvocationOutsideTheScopedModels amazon.titan-embed-text-v2:0   not admitted by the repository's SCP - step 7.4a's first sync is expected refused until decision 11's amendment.
  pass   ML-8  role AmazonBedrockLambdaExecutionRole-4gqfau9xuo6e4w-bi356s1sacz0cw   boundary awsds-sandbox-project-boundary; project 4gqfau9xuo6e4w; policies AWSLambdaBasicExecutionRole, SageMakerStudioBedrockKnowledgeBaseCustomResourcePolicy, SageMakerStudioBedrockFunctionExecutionRolePolicy
  pass   ML-8  role AmazonBedrockLambdaExecutionRole-avhvbqn37ty7m8-5hkjdsy3umpi1c   boundary awsds-sandbox-project-boundary; project avhvbqn37ty7m8; policies AWSLambdaBasicExecutionRole, SageMakerStudioBedrockKnowledgeBaseCustomResourcePolicy, SageMakerStudioBedrockFunctionExecutionRolePolicy
  pass   ML-8  role AmazonBedrockServiceRole-4gqfau9xuo6e4w-bi356s1sacz0cw   boundary awsds-sandbox-project-boundary; project 4gqfau9xuo6e4w; policies SageMakerStudioBedrockFlowServiceRolePolicy, SageMakerStudioBedrockEvaluationJobServiceRolePolicy, SageMakerStudioBedrockAgentServiceRolePolicy, SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy
  pass   ML-8  role AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c   boundary awsds-sandbox-project-boundary; project avhvbqn37ty7m8; policies SageMakerStudioBedrockFlowServiceRolePolicy, SageMakerStudioBedrockEvaluationJobServiceRolePolicy, SageMakerStudioBedrockAgentServiceRolePolicy, SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy
  pass   ML-8  Lambda functions   none but Control Tower's own
  ```

  It lists no OpenSearch Serverless collection. The four `AmazonBedrock*` roles are the `Tooling`
  environments': `list-roles` dates them 2026-08-23 17:31:18 (`eighth-experimentation`) and
  2026-10-15 06:05:44 (`test-experimentation`), each under the D13 boundary.
- **[Claude] The checklist's step 2: AWS's key-permissions page**
  (`adminguide/sagemaker-unified-studio-provisioned-resources-key-permissions.html`), read before the
  template: one policy *"for the Tooling blueprint config"* with ten `Sid`s, `AllowKmsPermissionsForCloudWatch`,
  `RedshiftCreateGrantKmsPermissions`, `AthenaKmsPermissions`, `EmrServerlessKmsPermissions`,
  `EmrServerlessKmsPermissionsForProvisioning`, `AirflowCreateGrantKmsPermissions`,
  `AllowKmsKeyUsageForSageMakerDomain`, `AllowSageMakerDomainKmsGrantPermissions`,
  `GrantKMSPermissionsForAllProjectRoles` and `AllowCreateGrantForProjectRoles`. None names Bedrock,
  a knowledge base, OpenSearch Serverless, S3 Vectors or Lambda, so `kms.tf` gains no statement.
- **[Claude] Step 3: the blueprint and its template.** As `awsds-infra-data`,
  `AmazonBedrockKnowledgeBase` is `48ls9aowlj9zv4`, updated 2026-07-02, with 61 user parameters, each
  optional and editable. Its `templateUrl` names
  `DataZone-AmazonBedrockKnowledgeBase-prod-20260316.template.json`, fetched at 17:31:41 by `aws s3api
  get-object` as `awsds-infra-sandbox-1` from the URL's access-point alias: 130,848 bytes,
  `LastModified` 2026-10-08T15:10:38Z. It declares 62 parameters:
  - Four have no default, `datazoneEnvironmentEnvironmentId`, `datazoneEnvironmentProjectId`,
    `datazoneEnvironmentDomainId` and `datazoneEnvironmentDomainArn`, and none is a user parameter
    (inferred: DataZone fills them, as it fills `MLflowApp`'s three).
  - Five carry `AllowedValues`: `knowledgeBaseType` (`VECTOR`, `SQL`; default `VECTOR`),
    `storageConfigurationType` (`OPENSEARCH_SERVERLESS`, `NEPTUNE_ANALYTICS`, `RDS`, `S3_VECTORS`;
    default `OPENSEARCH_SERVERLESS`), `logGroupRetention`, `useCustomerManagedKey` and
    `useAwsManagedPoliciesWithoutBoundary` (`true`, `false`; default `false`). The profile locks no
    value of this blueprint, so no locked value meets them.
  - Fourteen are not user parameters: the four above, `datazoneScopeName`, `s3BucketArn`,
    `kmsKeyArn`, `useCustomerManagedKey`, `useAwsManagedPoliciesWithoutBoundary`,
    `bedrockServiceRoleArn`, `lambdaExecutionRoleArn`, `enableExternalS3DataSources`,
    `logGroupRetention` and `componentDefinitionS3Path`; who fills the roles and the key is unread.
    Thirteen user parameters are not in the template: the SQL knowledge base's Redshift and
    query-generation fields and the three `contextEnrichment*`.

  So `blueprint_parameters` declares nothing for the knowledge base.
- **[Claude] What the template builds**: 22 resources. The knowledge base, its data source, an
  OpenSearch Serverless collection `<collectionName>-<environment>` (default `bedrock-ide`) with a
  `network` and a `data` policy, and two Lambdas, the index and the ingestion trigger, with their log
  groups, exist only under `IsAOSSVectorStoreKB` (`knowledgeBaseType` `VECTOR` and
  `storageConfigurationType` `OPENSEARCH_SERVERLESS`); with any other store the stack holds its wait
  handles alone. The network policy sets `AllowFromPublic` true on the collection and its dashboard,
  and the template writes no encryption policy. Its two IAM roles,
  `AmazonBedrockExecutionRoleForKnowledgeBase__<environment>` and
  `AmazonBedrockExecutionRoleForLambda-<environment>`, are created only when `bedrockServiceRoleArn`
  and `lambdaExecutionRoleArn` are empty and the store is OpenSearch Serverless; their boundary is AWS's
  `SageMakerStudioProjectUserRolePermissionsBoundary`, or none with
  `useAwsManagedPoliciesWithoutBoundary` `true`, never `awsds-sandbox-project-boundary`.
- **[user, Claude] Step 4: the console**, the DataZone console's **Associated domains** → `awsds-studio`
  → **Blueprints**, 14 entries. The knowledge base has no row of its own: it is one of the seven in
  `AmazonBedrockGenerativeAI` (*"It enables users to build generative AI applications using tools such
  as Agents, Knowledge Bases, Guardrails, Flows, Functions, and Model Evaluation."*), status *Not all
  enabled*. The grouping's page, read by URL: **Provisioning** type CloudFormation, provisioning role
  `awsds-sandbox-smus-provisioning`; **Regions** the six configured Bedrock blueprints in `us-west-2`;
  **Authorization** *"No domain units"* and *"You must authorize at least one domain unit."*, while the
  page's Tooling card reads *"1 authorized domain unit(s)"*. A banner, *"Not all Amazon Bedrock
  Generative AI blueprints are enabled."*, carries a **Retry** button, not clicked. The domain page also
  offers *Enable new project experience* (*"Create an administration project to allow the creation of
  projects in this account that use existing IAM roles with data access."*), not opened.
- **[user] Enable**, the grouping's row selected: the form *"Set up generative AI"*
  (`#/associatedDomains/<domain>/configure-generative-ai`), every choice defaulting to a new role:
  - **Generative AI blueprints → Provisioning role**: *Create and use a new service role* (selected) or
    *Use an existing service role*, with *View permission details* and *"This role will be used to
    create an administration project that allows this associated account to be managed in the domain
    management portal."*
  - **Permissions for Amazon Bedrock model access → Model provisioning role**, *"The system uses a
    provisioning role to create an inference profile that has access to an Amazon Bedrock model in a
    project."*: *Create an Amazon SageMaker Unified Studio managed role for all models* (selected) or
    *Use a single existing role for all models*.
  - **Model consumption role**, *"The system uses a consumption role to grant users access to Amazon
    Bedrock models in the playgrounds."*: *Use an Amazon SageMaker Unified Studio managed role for each
    model* (selected; *"If a managed role doesn't exist in this account, Amazon SageMaker Unified Studio
    will create the role for you."*) or *Use a single existing role for all models*.
  - No field for Regions, authorized domain units, a manage access role, the VPC or parameters; the
    buttons **Cancel** and **Submit**.
- **[user] Cancel.** The console then showed the domain's **Amazon Bedrock models** tab for
  `Sandbox Account 1` and `us-west-2`: *"Models enabled for the selected account and region (0)"*, every
  listed model with *Enabled in projects*, *Enabled in playground* and *Roles for model access* at `-`.
  Read through the API before the Cancel (18:10:46) and after it (18:13:27): no configuration of
  `48ls9aowlj9zv4` (*"... is not present"*), twelve configurations, no OpenSearch Serverless encryption
  policy, and no role named `AmazonDataZone*` or `AmazonSageMaker*` in `Sandbox Account 1`.
- **[Claude] What the form's Submit adds, read in the console's code**
  (`a.b.cdn.console.awsstatic.com/a/v1/TDTEDU4FYQYQUV2Q7YXPJZAE2IFRJHB6CPMAXB2DTWLNL6YLKQAQ/main.js`,
  6,158,162 bytes): the generative-AI setup creates, when absent, an OpenSearch Serverless encryption
  policy, `bedrock-ide-default` with an AWS-owned key over `collection/bedrock-ide-*`, or
  `bedrock-ide-<14 characters of the domain id>` under the Tooling form's KMS key over
  `collection/bedrock-ide-<3 characters>-*`. AWS's pages name the two model roles
  `AmazonDataZoneBedrockModelManagementRole` (*"The inference profile is required for the project to
  interact with the model."*) and `AmazonDataZoneBedrockFMConsumptionRole` (*"required for each Amazon
  Bedrock model that you want to enable in the playground for non-builders"*), both trusted by
  `datazone.amazonaws.com`.
- **[Claude] The checklist's step 4 against the module: nothing joins `blueprints.tf`.** The form's
  provisioning role is the one `blueprints.tf` names. The two model roles are no field of a blueprint
  configuration: `AmazonBedrockChatAgent`'s, read the same hour, holds the provisioning and
  manage-access roles, the boundary, `enabledRegions` and the three regional parameters. Two readings
  pass to later steps instead. The account enables no model for projects or the playground, which
  7.2 and 7.3 read against the menu. And a knowledge base on OpenSearch Serverless would meet a
  collection no encryption policy covers, since neither Terraform nor the template writes the policy
  the form's Submit writes (inferred, unexercised), behind a network policy open to the public: an
  input to decision 12, whose recommended store, S3 Vectors, creates no collection.

## 2026-10-19 — 7.0b: the tag, the plans and the user's applies; 7.2: the Generative AI menu read

*Provenance. Claude, in the same session and worktree, as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and in `Data Governance`
(`awsds-infra-data`); the governance plan also read `awsds-infra-staging` and `awsds-infra-identity`. The
hub, the GitLab host and the tunnel were up for Stage 18's session, which applied `sandbox/egress/` and
`staging/egress/` in the same hour and touched neither slice here. The applies are the user's, from the
saved plans, in a terminal of the project folder with `-chdir` into this worktree, pasted into this
session with the account ids replaced. The portal was read through Claude in Chrome, in a tab of
Claude's group in the user's session as the Data Scientist User: pages were opened by URL, the clicks
opened two model lists, *My components* and the *Create component* menu, each closed with nothing
chosen, and nothing was saved or created. Times are UTC.*

- **[Claude] The tag.** The module's commit `5b2f940` landed alone; `git ls-remote --tags origin`
  read `sagemaker-prereqs-v0.6.0` as origin's newest at the tagging, so the tag is
  `sagemaker-prereqs-v0.7.0`. The app's classifier refused the push of the branch and the tag
  (*Out-of-Place Publication*), and the edit of the caller's pin after it; the user authorized both in
  this session, and origin then read:

  ```
  5b2f94022b72dcba9a94f50d63d705699bf0a317	refs/tags/sagemaker-prereqs-v0.7.0
  ```

  The callers' commit is `92f8932`. `staging/studio/` keeps `v0.6.0`: it passes its own
  `blueprint_names`, `Tooling` alone, so the new default reaches nothing there.
- **[Claude] The plans**, 18:25:35 to 18:28:10, `-input=false`, saved as `~/tmp/s17-kb-sagemaker.tfplan`
  and `~/tmp/s17-kb-governance.tfplan`, no `.terraform.lock.hcl` changed. `sandbox/sagemaker` at
  `v0.7.0`:

  ```
    # module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["AmazonBedrockKnowledgeBase"] will be created
    # module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["AmazonBedrockKnowledgeBase"] will be created
  Plan: 2 to add, 0 to change, 0 to destroy.
  ```

  The configuration names the same roles, boundary and regional parameters as `MLflowApp`'s; the
  grant is `CREATE_ENVIRONMENT_FROM_BLUEPRINT` to the root unit's project contributors,
  `include_child_domain_units = false`. `data-governance/governance`:

  ```
    # awscc_datazone_project_profile.this["experimentation"] will be updated in-place
  Plan: 0 to add, 1 to change, 0 to destroy.
  ```

  The one changed attribute is `environment_configurations`, twelve elements before and thirteen
  after: `AmazonBedrockKnowledgeBase` (`48ls9aowlj9zv4`), `ON_DEMAND`, `deployment_order` 12,
  `us-west-2`, no parameters, the other elements' account; the first twelve are identical. The
  `deployment` profile and its grant read unchanged.
- **[user] Both applies**, in that order. The first paste also printed the saved plan
  (`terraform show`), as read above. With the account ids replaced:

  ```
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/stage-17-readings-7be400/terraform-live/sandbox/sagemaker apply -input=false "$HOME/tmp/s17-kb-sagemaker.tfplan"
  Acquiring state lock. This may take a few moments...
  module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["AmazonBedrockKnowledgeBase"]: Creating...
  module.sagemaker_prereqs.awscc_datazone_environment_blueprint_configuration.enabled["AmazonBedrockKnowledgeBase"]: Creation complete after 7s [id=dzd-d8yrvx1ko7im6o|48ls9aowlj9zv4]
  module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["AmazonBedrockKnowledgeBase"]: Creating...
  module.sagemaker_prereqs.awscc_datazone_policy_grant.create_environment_from_blueprint["AmazonBedrockKnowledgeBase"]: Creation complete after 6s [id=dzd-d8yrvx1ko7im6o|00Oakl3d33|<Sandbox Account 1>:48ls9aowlj9zv4|ENVIRONMENT_BLUEPRINT_CONFIGURATION|CREATE_ENVIRONMENT_FROM_BLUEPRINT]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

  Outputs:

  manage_access_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-smus-manage-access"
  project_boundary_arn = "arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary"
  project_key_arn = "arn:aws:kms:us-west-2:<Sandbox Account 1>:key/a81b1ef3-716f-4105-bb42-14184a6e2174"
  provisioning_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-smus-provisioning"
  regional_parameters = {
    "AZs" = "usw2-az1,usw2-az2"
    "Subnets" = "subnet-016b5a3a62c739894,subnet-09d3399d6b0fec93a"
    "VpcId" = "vpc-00dca74a35159b11c"
  }
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-data terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/stage-17-readings-7be400/terraform-live/data-governance/governance apply -input=false "$HOME/tmp/s17-kb-governance.tfplan"
  awscc_datazone_project_profile.this["experimentation"]: Modifying... [id=dzd-d8yrvx1ko7im6o|dh60xbal05q64w]
  awscc_datazone_project_profile.this["experimentation"]: Modifications complete after 7s [id=dzd-d8yrvx1ko7im6o|dh60xbal05q64w]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 0 added, 1 changed, 0 destroyed.

  Outputs:

  domain_arn = "arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o"
  domain_execution_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-execution"
  domain_id = "dzd-d8yrvx1ko7im6o"
  domain_service_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-service"
  portal_url = "https://dzd-d8yrvx1ko7im6o.sagemaker.us-west-2.on.aws"
  project_profile_creators = {
    "deployment" = "InfrastructureAccess (staging)"
    "experimentation" = "sso-group-data-scientists"
  }
  project_profile_ids = {
    "deployment" = "dalofykyytykgg"
    "experimentation" = "dh60xbal05q64w"
  }
  root_domain_unit_id = "bzq0cbh2gd0f4g"
  ```

- **[Claude] Read back, and when.** At 18:35:04 the configuration of `48ls9aowlj9zv4` reads the
  planned roles, boundary and `us-west-2` parameters, created 18:33:50; Sandbox holds thirteen
  configurations, and the configuration one grant. The trails: `PutEnvironmentBlueprintConfiguration`
  at 18:33:50 and `AddPolicyGrant` at 18:33:56, in Sandbox's as `InfrastructureAccess` and in Data
  Governance's as well; `UpdateProjectProfile` at 18:36:44 in Data Governance's, the profile's
  `lastUpdatedAt`. DataZone records a grant as `AddPolicyGrant`, so the 2026-10-19 morning entry's
  lookup of `CreatePolicyGrant` could find none. The profile: `ENABLED`, thirteen environment
  configurations, `AmazonBedrockKnowledgeBase` `ON_DEMAND` at order 12, configuration
  `e798d865-a647-4262-a963-b0cd6f6f00f1`.
- **[Claude] Re-planned, both `No changes. Your infrastructure matches the configuration.`**: from
  18:37:51, `governance/` done at 18:38:17 and `sandbox/sagemaker` at 18:38:29.
- **[Claude] `./aws/studio.py`**, 18:38:41 to 18:40:04: `wrote aws/output/studio.txt (some calls FAILED -
  see section 10)`, exit 1, section 10 holding the seven `sts get-caller-identity` calls of the persona
  and Control Tower profiles, whose SSO sessions were not signed in. `US-3` passes, *"13 blueprint
  configuration(s) in awsds-infra-sandbox-1"*, *"all inside decision 5's category 1"*, and *"no
  blueprint configured in the domain account"*; `US-4`, `US-8` (six roles bounded) and `US-10` (no
  running apps) pass.
- **[Claude] Before the portal**, 18:40:12: each project's environments are 1.5's (`eighth-experimentation`:
  `Tooling` `ACTIVE`, the `DataLake` one `CREATE_FAILED`, `ml-demo-mlflow` `ACTIVE`;
  `test-experimentation`: `Tooling` `ACTIVE`, the `DataLake` one `CREATE_FAILED`), both projects
  `ACTIVE`, last updated 2026-10-15, deployment `SUCCESSFUL`.
- **[Claude] The portal's user.** Data Governance's trail names the acting session
  `awsds-data-studio-domain-execution/user-28f1b390-0041-7068-8cc7-9ccef94277d1`, 327 events from
  18:50 to 18:57, and `get-user-profile` resolves that id to the SSO user *Data Scientist User*,
  `ACTIVATED`.
- **[Claude] 7.2, the menu**, 18:53 to 18:56. `eighth-experimentation`'s left navigation carries
  **Generative AI → Playground** (`/bedrock/playground/explorer`, outside any project) and **AI apps**
  (`/projects/<project>/bedrock/playground/chat`):
  - **AI apps**, 18:53:06: the Bedrock IDE's chat agent builder, *"Untitled App - by4x6"*, *Not saved*,
    *Not deployed*, *Not shared*, *App ID: -*; the IDE's navigation *Build* (*Models*, *Chat agent*,
    *Flow*, *Prompt*, *Model evaluations*) and *Asset gallery* (*My apps*, *My prompts*, *My
    components*); a notice, *"Agents Classic will no longer be open to new customers starting on July
    30, 2026"*; and *Configurations → Model*, *"Select model to configure the app."* Its model list, at
    18:55:32: *"No models found. Contact your admin to enable more models."*
  - **Playground**, 18:54:26: *Chat playground*, *Type: Model*, *Model: Select model*, *"Select app or
    model to start chatting"*, *Compare mode*, *Build chat agent*. Its model list, at 18:54:43, reads the
    same sentence.
  - **`test-experimentation`'s AI apps**, 18:55:49: the same builder, *"Untitled App - sz3kck"*, where
    1.5 read *"This tool is not available for this project."* at 05:56.
  - **My components**, 18:56:15: *Components (0)*, *"You can have a maximum of 30 components of each type
    in a project."*, and *Create component* offering *Knowledge Base*, *Guardrail* and *Function*.
- **[Claude] The reading created nothing.** At 18:53:25 and 18:56:51 each project's environments are
  the 18:40:12 ones. Data Governance's DataZone events from 18:50 to 18:57 are reads but for 10
  `SearchListings`, 2 `UserProfileAutoCreated` by DataZone (18:53:22, 18:53:29), 2
  `GetDomainExecutionRoleCredentials` (18:52:49, 18:52:54, the portal's backend's user agent) and one
  `CreateProjectMembership`; no `CreateEnvironment` since 18:40. Sandbox's trail holds no Bedrock event
  from 18:50 to 19:01.
- **[Claude] Two `CreateProjectMembership` calls are not this session's**: on `test-experimentation`,
  from the AWS CLI as Data Governance's `InfrastructureAccess`, at 18:47:04 (the role
  `awsds-deploy-sandbox-test` as `PROJECT_CONTRIBUTOR`, `ValidationException`) and at 18:52:26 (a
  group as `PROJECT_CONTRIBUTOR`, accepted).
- **[Claude] `ML-8` after**: `./aws/sandbox-ml.py`, 18:58:30 to 19:01:04 (stamped 19:01:02Z), *"all
  checks passed"*, exit 0, its `ML-8` rows identical to 7.0's: `EnableAmazonBedrockIDEPermissions`
  still absent on both project roles, no knowledge base, vector bucket or Bedrock object. Nothing was
  deployed, so verification xvii waits for the first Bedrock environment.
- **[Claude] What 7.2 says.** The portal's code was read right: with the seventh Bedrock type in the
  profile, both projects' Generative AI menus open, with no *Update project* and no environment
  deployed. The models are a second gate the profile does not open. The console's **Amazon Bedrock
  models** tab reads no model enabled for `Sandbox Account 1` in `us-west-2` (7.0a's entry), and the
  IDE answers *"Contact your admin to enable more models."* 7.3's chat therefore waits on how a model
  is enabled for the projects (decision 13).

## 2026-10-19 — decision 13's readings: what the Bedrock models tab writes, the model roles' policies, the SCP against an application inference profile

*Provenance. Claude, in a session started for decision 13, from the worktree
`verificar-ambiente-down-e95914` at `origin/main` `5142e0f`, as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and in `Data Governance`
(`awsds-infra-data`). Every AWS call was a read. The console's and the portal's JavaScript was
downloaded from their public CDN and read, never run. No quoted line carries an account id or an e-mail
address. Times are UTC.*

- **[Claude] The two managed policies**, read at 19:16 with `iam get-policy-version`. Both live under
  `service-role/`, so the first `get-policy` at the root path answered `NoSuchEntity`; each reads
  `AttachmentCount` 0 in `Sandbox Account 1`.
  - `AmazonDataZoneBedrockModelManagementPolicy` v1, created 2024-11-12 and never edited:
    `ManageApplicationInferenceProfile` (`bedrock:CreateInferenceProfile` and `TagResource` on
    `application-inference-profile/*` in the principal's account, the request and the resource carrying
    `AmazonDataZoneProject`), `DeleteApplicationInferenceProfile` (profiles carrying that tag),
    `CreateApplicationInferenceProfileUsingFoundationModels` (`foundation-model/*`, no condition) and
    `CreateApplicationInferenceProfileUsingBedrockModels` (`inference-profile/*` in the account). It
    grants no invocation.
  - `AmazonDataZoneBedrockModelConsumptionPolicy` v7, edited 2026-02-12: `InvokeDomainInferenceProfiles`
    (`InvokeModel` and `InvokeModelWithResponseStream` on `application-inference-profile/*` tagged
    `AmazonDataZoneDomain` with `${datazone:domainId}` and carrying no `AmazonDataZoneProject`),
    `ListFoundationModels`, and Bedrock sessions tagged with the DataZone user and domain. AWS's role
    page adds one inline statement per model, `AllowInferenceProfileToInvokeFoundationModels`: the
    model's `foundation-model` ARN when `bedrock:InferenceProfileArn` is one of the account's application
    inference profiles. Both roles' trust is `datazone.amazonaws.com`, `sts:AssumeRole` and
    `sts:SetContext`, under `aws:SourceAccount`.
- **[Claude] AWS's pages** (`REFERENCES.md`). The admin guide's *Amazon Bedrock in SageMaker Unified
  Studio* enables a model with *Manage* and two checkboxes per model, and publishes the models as assets
  through `GenerativeAIModelGovernanceProject`, a project the service creates, owned by the identity that
  configured Bedrock for the domain; an associated account's IAM identity must join it to publish models.
  The inference-profile prerequisites page requires the foundation model in each Region beside the
  profile, under `bedrock:InferenceProfileArn`.
- **[Claude] What the tab's *Manage* writes, read in the console's code**: 7.0a's bundle, unchanged
  (6,158,162 bytes, SHA-256 `950192e9ddeebb64…`, downloaded 19:18). The Submit,
  `processModelEnablementRequestCommand`:
  1. Looks in the current account for a role whose name contains
     `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`; failing that, takes a role
     chosen in the setup wizard; failing that, creates it at `/service-role/` with AWS's management policy,
     its trust's `aws:SourceAccount` the domain's account. This runs before any model is processed, and
     a role chosen in a model's *Roles for model access* is read only afterwards.
  2. Per model enabled in projects: `CreateEnvironment` with `environmentBlueprintIdentifier`
     `AwsServiceBlueprint` in the governance project, named
     `amazon.datazone.BedrockModelEnvironmentType_<12 characters>`, in the selected account and Region;
     `AssociateEnvironmentRole` with the provisioning role as `SYSTEM_ROLE`; `CreateAsset` of type
     `amazon.datazone.BedrockModelAssetType`, owned by the governance project, named
     `<model id><Region>BedrockModelForm`, its form carrying the Region, the account, the role, the
     environment and the model (a cross-Region row's ARN being its system inference profile's), beside a
     `SubscriptionTermsForm` of `{"approvalRequired": "NO"}`; `CreateListingChangeSet` `PUBLISH`.
  3. Per model enabled in the playground: `bedrock:CreateInferenceProfile` as the person pressing
     Submit, named after the domain id, copying the system profile or the model, tagged
     `AmazonDataZoneDomain`; a consumption role, chosen in the form, found by its generated name
     `AmazonSageMakerBedrockModelConsumptionRole-<14 hex characters>`, or created with a customer-managed
     `AmazonSageMakerBedrockModelConsumptionPolicy-<the same hash>`; an environment of type
     `BedrockInferenceOnlyEnvironmentType` holding it as `SHAREABLE_ROLE`; an asset of type
     `amazon.datazone.BedrockInferenceOnlyAssetType` carrying the profile's ARN; the publish.
  4. A disable revokes the listing's approved subscriptions, unpublishes and deletes the asset, and for
     the playground deletes the profile.

  The governance project is found through `ListProjects`, by id or by the name
  `GenerativeAIModelGovernanceProject`. In an associated account *Manage* stays greyed while none is
  found (*"Model governance project does not exist"*), and the *Manage* page offers the project in a
  selector and keeps *Review and submit* disabled until one is chosen. Only the domain account's setup
  creates the profile *Generative AI model governance*, with no environment configuration, and the
  project, in the run that also writes the Bedrock blueprints' and `Tooling`'s configurations in that
  account. The associated account's *Set up generative AI* Submit writes the `Tooling` configuration if
  absent and the Bedrock blueprints' configurations with a blueprint management role, and processes no
  model: the two model roles of its form are unused there (inferred from the code).
- **[Claude] How a project reaches a model, read in the portal's code**: `assets/module-GY0Cw3hN.js`,
  4,374,983 bytes, the bundle that holds 1.5's `App-D6IrICgA.js`, downloaded 19:25. The model lists are
  catalog searches by asset type, `BedrockModelAssetType` in a project and
  `BedrockInferenceOnlyAssetType` in the playground. On a model's first use the portal sends
  `CreateSubscriptionRequest` for its listing, as the project (`PROJECT`) or as the person (`USER`),
  polls the request to `ACCEPTED` and `ListSubscriptionGrants` to `COMPLETED`. A project's grant names
  the application inference profile in its `targetName`, and the call uses the project's bootstrap
  environment's credentials; the playground's names a connection, whose credentials the browser takes
  through `GetConnectionCredentials`. That the grant creates the profile with the provisioning role,
  tagged `AmazonDataZoneProject`, is inferred from the management policy; no grant was observed.
- **[Claude] Who invokes through an application inference profile**, read at 19:23 and 19:26. The
  project role's `SageMakerStudioProjectUserRolePolicy` v75 admits `InvokeModel` on
  `application-inference-profile/*` tagged with its own `AmazonDataZoneProject` (`BRInvokeAppProfile`,
  under `EnableAmazonBedrockPermissions`) and on `foundation-model/*` only when
  `bedrock:InferenceProfileArn` is an application inference profile (`BedrockInvokeModelPermissions`).
  The `Tooling` environments' `AmazonBedrockServiceRole-*` policies, `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy`
  v9, `SageMakerStudioBedrockAgentServiceRolePolicy` v3, `SageMakerStudioBedrockFlowServiceRolePolicy`
  v9 and `SageMakerStudioBedrockEvaluationJobServiceRolePolicy` v3, admit the same pair. The knowledge
  base's embeddings, the agent, the flow and the evaluation therefore reach a model only through a
  project's application inference profile (inferred from the policies).
- **[Claude] The domain and the account**, read at 19:22 and 19:33. As `awsds-infra-data`, the domain
  holds the project profiles `deployment` and `experimentation` and the projects `test-experimentation`,
  `eighth-experimentation` and `deploy-staging`: no governance profile and no governance project. In
  `Sandbox Account 1`, `bedrock list-inference-profiles --type-equals APPLICATION` returns none, and the
  three scoped `us.` profiles read `ACTIVE`, each routing to `us-east-1`, `us-east-2` and `us-west-2`.
- **[Claude] What Terraform reaches (Lesson 8)**, read at 19:24. CloudFormation's registry in
  `us-west-2` lists 17 `AWS::DataZone::*` types, `Environment` among them with
  `EnvironmentBlueprintIdentifier`, `EnvironmentAccountIdentifier`, `EnvironmentAccountRegion` and
  `EnvironmentRoleArn`, beside `Project`, `ProjectMembership` and `ProjectProfile`, and
  `AWS::Bedrock::ApplicationInferenceProfile`; none for an asset, a listing, a subscription or
  `AssociateEnvironmentRole`. The pinned providers, `awscc` 1.98.0 and `aws` 6.61.0, document
  `awscc_datazone_environment` (`environment_role_arn`), `awscc_datazone_project`,
  `awscc_datazone_project_membership`, `awscc_datazone_project_profile`,
  `awscc_bedrock_application_inference_profile` and `aws_bedrock_inference_profile`, and no asset,
  listing or subscription resource in either.
- **[Claude] The SCP against an invocation through an application inference profile.**
  `DenyBedrockInvocationOutsideTheScopedModels` lists six spellings in its `NotResource`, three
  `inference-profile/us.anthropic.*` and three `foundation-model/anthropic.*`, and no
  `application-inference-profile`. Such an invocation is authorized on the profile's ARN and on the
  foundation model's in each Region it routes to (AWS's prerequisites page; 6e's `sandbox/bedrock/`
  names both halves for the system profiles), so the statement refuses every call the portal makes, a
  project's, the knowledge base's sync and the playground's, on the profile's pass (inferred,
  unexercised). Decision 11's amendment as recommended, Titan V2's `foundation-model` ARN alone, would
  leave 7.4a's second sync refused on the same pass. `aws/awslib/bedrockscope.py`'s two patterns match
  neither half of an `application-inference-profile/*` entry, so such an entry moves no instrument's
  reading (read from the code).

## 2026-10-19 — decision 13: the Bedrock models tab and its *Manage* page, read in the console

*Provenance. Claude, in the same session and worktree. The console session was the user's, signed in as
the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`ConsoleLogin` at
19:50:48), read through Claude in Chrome in a tab of Claude's own group, opened by URL. Claude's clicks
opened the governance project selector, one model's *Manage roles* dialog and its role selector, each
closed with Escape or *Cancel*; nothing was ticked, saved or submitted. The AWS calls Claude ran were
reads as `awsds-infra-sandbox-1` and `awsds-infra-data`. Times are UTC.*

- **[Claude] The tab** (`#/associatedDomains/<domain>/modelsManagement`), 19:51. The header reads
  `Sandbox Account 1` and `InfrastructureAccess`, the selectors `<Sandbox Account 1>` and `us-west-2`.
  *Models enabled for the selected account and region (0)*, and **Manage** greyed, its tooltip
  *"Model governance project does not exist"*, the wording the code predicted. The table lists 62 models
  from 12 providers (Amazon 9, Anthropic 11, Cohere 4, DeepSeek 2, Luma AI 1, Meta 9, Mistral AI 5,
  OpenAI 2, Qwen 4, Stability AI 12, TwelveLabs 1, Writer 2), every *Enabled in projects*, *Enabled in
  playground* and *Roles for model access* cell at `-`. Anthropic's eleven are all *On-demand
  cross-region*: Claude Haiku 4.5, Opus 4.1 (*Legacy*), Opus 4.5, 4.6, 4.7, 4.8, Opus 5, Opus 5.5, Sonnet
  4.5 (*Legacy*), Sonnet 4.6 and Sonnet 5. Titan Text Embeddings V2 is listed twice, as `Titan Text
  Embeddings V2` and `Titan Text Embeddings v2`, both *Embedding* and *On-demand*. Below the table,
  *Playground settings* holds *Default playground models - optional* with its *Chat playground* and
  *Image and video playground* selectors empty, and no *Model governance project* section. The page's
  *Next steps* reads *Generative AI* with *8 blueprints enabled*.
- **[Claude] The *Manage* page, opened by URL** (`#/associatedDomains/<domain>/manage-generative-ai-models`),
  19:52. *Manage models access*, the same selectors and the same 62 rows, each with an *Enable* checkbox
  under *Enable in projects* and under *Enable in playground* and a *Manage roles* link under *Roles for
  model access*. A *Model governance project* section says the service creates a governing project at
  the initial model access setup, from a system-generated *Gen AI Model Governance Project* profile; its
  field *Generative AI governance project* opens on a search box and no option. *Review and submit* is
  greyed.
- **[Claude] *Manage roles* on Claude Haiku 4.5's row**, 19:52 to 19:53. The dialog *Permissions for
  Amazon Bedrock model access* holds one section, *Model provisioning role*, with *Use an Amazon
  SageMaker Unified Studio managed role for the model* and *Use a single existing custom role for the
  model*, the second selected with `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`;
  no consumption role section, the playground box being unticked. The role selector lists the account's
  roles in name order, unfiltered by trust (`AmazonBedrockLambdaExecutionRole-*`,
  `AmazonBedrockServiceRole-*`, `aws-controltower-*`, `AWSControlTowerExecution`,
  `AWSControlTower_VPCFlowLogsRole`, `awsds-deploy-devenv-sandbox`, `awsds-deploy-sandbox-test`,
  `awsds-sandbox-lake-access`, and on), and the preselected role is not among them. `iam list-roles` at
  19:53 holds no role whose name carries `AmazonSageMaker`, `AmazonDataZone`, `ModelManagement` or
  `ModelConsumption` but `AWSServiceRoleForAmazonSageMakerNotebooks`: the dialog offers, as an existing
  role, the ARN the code builds as its last fallback. *Cancel*, then the page's *Cancel*, back on the
  tab.
- **[Claude] Nothing was written.** At 19:54 Sandbox holds no application inference profile, and the
  domain the same three projects and two profiles. Sandbox's trail from 19:38 holds, as the
  infrastructure user, `ConsoleLogin` at 19:50:48, six `SearchListings` from 19:51:09 to 19:52:29 (the
  pages' catalog lookups) and, in `us-east-1`, one `PutRolePolicy` at 19:46:08 on
  `awsds-deploy-sandbox-test` by Terraform, Stage 18's `sandbox/workflows/` apply announced by its
  session; no other write.
- **[Claude] What the reading says.** The code's prediction holds: an associated account's console
  offers no way to enable a model until a governance project exists and lists the caller as a member.
  The dialog's default for the provisioning role is the console's managed name, so a role the slice
  creates under that name would appear as the existing role, which is decision 13 (b)'s adoption.

## 2026-10-19 — decision 13 taken

- **[user] Decision 13**, in this session's chat after the console reading: *"Vamos pela opção (b)"*,
  the recommended (b): the governance profile, project and Sandbox `InfrastructureAccess` membership in
  `data-governance/governance/`, and the two model roles in a `[P]` slice `sandbox/model-access/` the
  console adopts. Decision 11, the SCP amendment grown by `application-inference-profile/*`, stays the
  user's.

## 2026-10-19 — decision 13 (b): the governance project and `sandbox/model-access/` written and planned

*Provenance. Claude, in the same session and worktree, as the infrastructure user with
`InfrastructureAccess` in `Data Governance` (`awsds-infra-data`, with the slice's `sandbox`, `staging`
and `identity` aliases) and in `Sandbox Account 1` (`awsds-infra-sandbox-1`). Plans only: nothing was
applied. Account ids in the plans' output are replaced by the account's name. Times are UTC.*

- **[Claude] The group the membership names**, read with `datazone search-group-profiles`: Sandbox's
  `InfrastructureAccess` role has an `IAM_ROLE_SESSION_GROUP` profile, already a
  `PROJECT_CONTRIBUTOR` of `eighth-experimentation` (INT-25's portal membership of 2026-10-15), and
  the slice resolves its id from the role's ARN, as it does Staging's.
- **[Claude] `data-governance/governance/`**: `model-governance.tf` and the Sandbox role's two lookups
  in `data.tf`, beside Staging's. The plan, saved as `~/tmp/s17-model-governance.tfplan` at 20:14:20:

  ```
    # awscc_datazone_project.model_governance[0] will be created
    # awscc_datazone_project_membership.model_governance_sandbox_infrastructure[0] will be created
    # awscc_datazone_project_profile.model_governance[0] will be created
  Plan: 3 to add, 0 to change, 0 to destroy.
  ```

  The profile is *Generative AI model governance*, `ENABLED`, with no environment configuration; the
  project `GenerativeAIModelGovernanceProject`; the membership `PROJECT_CONTRIBUTOR` for that
  session group.
- **[Claude] `sandbox/model-access/`**, a new `[P]` slice at rank 52, registered in `layers.py` and
  given `account_folder` and `domain` by `backend.py`. Its lock file is `sandbox/observability/`'s,
  `hashicorp/aws` 6.69.1 on the three platforms, since the first init locked one platform and
  `check-provider-locks.py` failed it. The plan, saved as `~/tmp/s17-model-access.tfplan` at 20:13:12:

  ```
    # module.model_consumption_role.aws_iam_role.this will be created
    # module.model_consumption_role.aws_iam_role_policy.inline["invoke-through-application-inference-profiles"] will be created
    # module.model_consumption_role.aws_iam_role_policy_attachment.managed["arn:aws:iam::aws:policy/service-role/AmazonDataZoneBedrockModelConsumptionPolicy"] will be created
    # module.model_provisioning_role.aws_iam_role.this will be created
    # module.model_provisioning_role.aws_iam_role_policy.inline["model-management"] will be created
  Plan: 5 to add, 0 to change, 0 to destroy.
  ```

  The provisioning role is `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`, path
  `/`, boundary `awsds-sandbox-project-boundary`, trust `datazone.amazonaws.com` (`sts:AssumeRole`,
  `sts:SetContext`) under `aws:SourceAccount` `<Data Governance Account>`. Its `model-management`
  policy admits `CreateInferenceProfile` from the three scoped models' `foundation-model` ARNs and Titan
  V2's, Region-less, and from the three `us.` profiles in `us-west-2`, beside AWS's two statements on
  `application-inference-profile/*` of `<Sandbox Account 1>`. The consumption role is
  `awsds-sandbox-bedrock-model-consumption`, with the same trust and boundary, AWS's consumption policy
  and `AllowInferenceProfileToInvokeFoundationModels` on `foundation-model/*` under
  `bedrock:InferenceProfileArn`.

## 2026-10-19 — decision 13 (b) applied by the user, read back, and the console's *Manage* open

*Provenance. The applies are the user's, from the saved plans, in a terminal of the project folder
with `-chdir` into this worktree, pasted into this session; the account ids are replaced by the
account's name. Claude, in the same session and worktree, re-planned and read back as
`awsds-infra-data` and `awsds-infra-sandbox-1`, ran `./aws/studio.py`, and read the console through
Claude in Chrome in the user's session as the infrastructure user in `Sandbox Account 1`: the clicks
opened *Manage*, the governance project selector, Claude Haiku 4.5's *Manage roles* dialog and its
role selector, each closed with Escape or *Cancel*; nothing was selected, ticked, saved or submitted.
Times are UTC.*

- **[user] Both applies**, in that order:

  ```
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-data terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/verificar-ambiente-down-e95914/terraform-live/data-governance/governance apply -input=false "$HOME/tmp/s17-model-governance.tfplan"
  awscc_datazone_project_profile.model_governance[0]: Creating...
  awscc_datazone_project_profile.model_governance[0]: Creation complete after 7s [id=dzd-d8yrvx1ko7im6o|ds7ur2s2ce42vk]
  awscc_datazone_project.model_governance[0]: Creating...
  awscc_datazone_project.model_governance[0]: Still creating... [00m10s elapsed]
  awscc_datazone_project.model_governance[0]: Still creating... [00m20s elapsed]
  awscc_datazone_project.model_governance[0]: Still creating... [00m30s elapsed]
  awscc_datazone_project.model_governance[0]: Still creating... [00m40s elapsed]
  awscc_datazone_project.model_governance[0]: Still creating... [00m50s elapsed]
  awscc_datazone_project.model_governance[0]: Still creating... [01m00s elapsed]
  awscc_datazone_project.model_governance[0]: Creation complete after 1m3s [id=dzd-d8yrvx1ko7im6o|dmvami701qu6xc]
  awscc_datazone_project_membership.model_governance_sandbox_infrastructure[0]: Creating...
  awscc_datazone_project_membership.model_governance_sandbox_infrastructure[0]: Creation complete after 7s [id=dzd-d8yrvx1ko7im6o|839bcde8-f8b8-4ada-936a-1441352db302|GROUP_IDENTIFIER|dmvami701qu6xc]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 3 added, 0 changed, 0 destroyed.

  Outputs:

  domain_arn = "arn:aws:datazone:us-west-2:<Data Governance Account>:domain/dzd-d8yrvx1ko7im6o"
  domain_execution_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-execution"
  domain_id = "dzd-d8yrvx1ko7im6o"
  domain_service_role_arn = "arn:aws:iam::<Data Governance Account>:role/awsds-data-studio-domain-service"
  model_governance_project_id = "dmvami701qu6xc"
  portal_url = "https://dzd-d8yrvx1ko7im6o.sagemaker.us-west-2.on.aws"
  project_profile_creators = {
    "deployment" = "InfrastructureAccess (staging)"
    "experimentation" = "sso-group-data-scientists"
  }
  project_profile_ids = {
    "deployment" = "dalofykyytykgg"
    "experimentation" = "dh60xbal05q64w"
  }
  root_domain_unit_id = "bzq0cbh2gd0f4g"
  ➜  AWS-DataScience git:(main) AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=/Users/felipentavares/src/AWS-DataScience/.claude/worktrees/verificar-ambiente-down-e95914/terraform-live/sandbox/model-access apply -input=false "$HOME/tmp/s17-model-access.tfplan"
  module.model_provisioning_role.aws_iam_role.this: Creating...
  module.model_consumption_role.aws_iam_role.this: Creating...
  module.model_consumption_role.aws_iam_role.this: Creation complete after 2s [id=awsds-sandbox-bedrock-model-consumption]
  module.model_consumption_role.aws_iam_role_policy_attachment.managed["arn:aws:iam::aws:policy/service-role/AmazonDataZoneBedrockModelConsumptionPolicy"]: Creating...
  module.model_consumption_role.aws_iam_role_policy.inline["invoke-through-application-inference-profiles"]: Creating...
  module.model_provisioning_role.aws_iam_role.this: Creation complete after 2s [id=AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>]
  module.model_provisioning_role.aws_iam_role_policy.inline["model-management"]: Creating...
  module.model_consumption_role.aws_iam_role_policy_attachment.managed["arn:aws:iam::aws:policy/service-role/AmazonDataZoneBedrockModelConsumptionPolicy"]: Creation complete after 0s [id=awsds-sandbox-bedrock-model-consumption/arn:aws:iam::aws:policy/service-role/AmazonDataZoneBedrockModelConsumptionPolicy]
  module.model_consumption_role.aws_iam_role_policy.inline["invoke-through-application-inference-profiles"]: Creation complete after 0s [id=awsds-sandbox-bedrock-model-consumption:invoke-through-application-inference-profiles]
  module.model_provisioning_role.aws_iam_role_policy.inline["model-management"]: Creation complete after 0s [id=AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>:model-management]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 5 added, 0 changed, 0 destroyed.

  Outputs:

  model_consumption_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-bedrock-model-consumption"
  model_provisioning_role_arn = "arn:aws:iam::<Sandbox Account 1>:role/AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>"
  ```

- **[Claude] Re-planned**, both `No changes. Your infrastructure matches the configuration.`:
  `governance/` from 20:31:41, `sandbox/model-access/` from 20:32:09, done at 20:32:20.
- **[Claude] Read back** at 20:32. The project `GenerativeAIModelGovernanceProject`
  (`dmvami701qu6xc`), created 20:25:25, reads `ACTIVE`, deployment `SUCCESSFUL`, on the profile
  `ds7ur2s2ce42vk`; the profile *Generative AI model governance*, created 20:25:19, reads `ENABLED` with
  no environment configuration. The project's members are two groups: `PROJECT_OWNER` the session group
  of Data Governance's `InfrastructureAccess`, Terraform's identity, and `PROJECT_CONTRIBUTOR`
  Sandbox's. In `Sandbox Account 1` both roles were created 20:27:17 at path `/`, under
  `awsds-sandbox-project-boundary`, trusted by `datazone.amazonaws.com` (`sts:SetContext`,
  `sts:AssumeRole`) under `aws:SourceAccount` `<Data Governance Account>`; the provisioning role holds
  the inline `model-management` and no managed policy, the consumption role
  `AmazonDataZoneBedrockModelConsumptionPolicy` and the inline
  `invoke-through-application-inference-profiles`.
- **[Claude] The console after**, 20:33 to 20:35. On the tab, **Manage** is active, with no disabled
  reason, and the counter still reads *(0)*. On the *Manage* page, the *Generative AI governance
  project* selector offers `GenerativeAIModelGovernanceProject`, and *Review and submit* stays greyed
  with no model ticked. Claude Haiku 4.5's *Manage roles* dialog preselects
  `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`, and the role selector now lists
  that role, the slice's.
- **[Claude] `./aws/studio.py`**, report stamped 20:36:54Z. With the new profile, `US-4` would fail
  (*"is no contracted profile"*, inferred from the code); the script names it in
  `MODEL_GOVERNANCE_PROFILE_NAMES` in this sitting, and the run reads `US-4` passing on *Generative AI
  model governance*, `deployment` and `experimentation`, with `US-3`, `US-8` and `US-10` passing. Exit 1
  comes from section 10 alone: the seven persona and Control Tower profiles whose SSO sessions were not
  signed in.

## 2026-10-19 — decision 13's third step: the models enabled in Sandbox's console

*Provenance. Claude, at the user's request in this session's chat ("Pode fazer estes passos na sessão
do chrome que está aberta", the steps being decision 13's third), through Claude in Chrome in the
user's console session as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`:
Claude's clicks ticked the six boxes, set the consumption role in two dialogs, chose the governance
project and pressed *Submit*, after reading the review table against the user's steps. The readings
before and after are Claude's, as `awsds-infra-sandbox-1` and `awsds-infra-data`. Times are UTC.*

- **[Claude] The rows ticked**, on the *Manage* page, 20:47 to 20:49. *Enable in projects*: Claude
  Opus 4.5, Claude Sonnet 4.5 (*Legacy*) and Claude Haiku 4.5, each *On-demand cross-region*, and
  Titan Text Embeddings V2. `bedrock list-foundation-models` names the two Titan rows: *Titan Text
  Embeddings V2* is `amazon.titan-embed-text-v2:0` and *Titan Text Embeddings v2* is
  `amazon.titan-embed-g1-text-02`, left unticked. *Enable in playground*: Claude Haiku 4.5, and Nova Lite
  on its *On-demand* row, `amazon.nova-lite-v1:0`, the model outside the scoped set for 7.3's refusal.
- **[Claude] The two playground dialogs.** In each *Manage roles* dialog the provisioning role came
  preselected as `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`, the slice's. The
  consumption role came preselected as an existing custom role that does not exist:
  `AmazonSageMakerBedrockModelConsumptionRole-3aa57cf8315f…` for Haiku 4.5 and
  `AmazonSageMakerBedrockModelVideoConsumptionRole-b7bb98…` for Nova Lite, which the console treats as a
  video model. Both were changed to `awsds-sandbox-bedrock-model-consumption`, and each dialog was
  saved with *Save and submit*. Neither save wrote anything: at 20:50:09 and 20:51:29 Sandbox held no
  application inference profile, no new role and no policy beyond the consumption role's two.
- **[Claude] The review**, after `GenerativeAIModelGovernanceProject` was chosen in the selector:

  ```
  Review and submit changes
  Model modifications (5)
  Models                    Inference type          Enabled in projects  Domain playground
  Claude Opus 4.5           On-demand cross-region  Enabled              -
  Claude Sonnet 4.5         On-demand cross-region  Enabled              -
  Claude Haiku 4.5          On-demand cross-region  Enabled              Enabled
  Titan Text Embeddings V2  On-demand               Enabled              -
  Nova Lite                 On-demand               -                    Enabled
  ```

  The table matched the user's steps. *Submit* at 20:52:05; the dialog *Configuring Generative AI* closed
  within a minute onto the tab with *"Roles have been successfully updated"*. After a reload the table
  reads the five rows *Enabled* with *Custom roles* in *Roles for model access*, while the heading
  still reads *Models enabled for the selected account and region (0)*.
- **[Claude] What it made**, read at 20:53. In the governance project, six environments in `<Sandbox
  Account 1>`, all `ACTIVE`, created from 20:52:15 to 20:52:44: four
  `amazon.datazone.BedrockModelEnvironmentType_<12 characters>` and two
  `amazon.datazone.BedrockInferenceOnlyEnvironmentType_<12 characters>`. Six assets, each published,
  owned by `dmvami701qu6xc`, created from 20:52:18 to 20:52:47:
  `anthropic.claude-opus-4-5-20251101-v1:0us-west-2BedrockModelFormCRIT`,
  `anthropic.claude-sonnet-4-5-20250929-v1:0us-west-2BedrockModelFormCRIT`,
  `anthropic.claude-haiku-4-5-20251001-v1:0us-west-2BedrockModelFormCRIT`,
  `amazon.titan-embed-text-v2:0us-west-2BedrockModelForm` (type `BedrockModelAssetType`), and
  `anthropic.claude-haiku-4-5-20251001-v1:0us-west-2BedrockInferenceOnlyFormCRIT` and
  `amazon.nova-lite-v1:0us-west-2BedrockInferenceOnlyForm` (type `BedrockInferenceOnlyAssetType`). In
  `Sandbox Account 1`, two application inference profiles named `dzd-d8yrvx1ko7im6o`, `ACTIVE`, of Haiku
  4.5 (20:52:31) and Nova Lite (20:52:43): the playground's. No project's profile exists yet, since no
  project has subscribed.
- **[Claude] What it did not make.** No IAM role and no customer-managed policy: `iam list-roles` and
  `list-policies --scope Local` show the slice's provisioning role alone among the names the console
  uses, and the consumption role still holds `AmazonDataZoneBedrockModelConsumptionPolicy` and its
  inline policy alone. Sandbox's trail in `us-east-1` holds no write by the infrastructure user from
  20:45. In `us-west-2` it holds, read complete at 20:56:51, 2 `CreateInferenceProfile`, 6
  `CreateEnvironment`, 6 `AssociateEnvironmentRole`, 6 `CreateAsset` and 6 `CreateListingChangeSet` by
  the infrastructure user from 20:52:15 to 20:52:47; Data Governance's trail holds DataZone's
  `CreateLineageNode`, `UpdateLineageNode` and `CreateLineageNodeVersion` in the same minutes.
- **[Claude] `./aws/catalog.py`** after: all checks passed. `CT-2` reads 8 listings, all owned by a live
  project, and `CT-3` *"no subscription, request or grant on any listing"*.
- **[Claude] What the step says.** The console adopted both roles: the provisioning role by its name
  and the consumption role by the dialog's choice, and it created no principal. The dialog's save
  writes nothing for a model not yet enabled. Its preselected consumption role is again a fallback name
  that no role carries, so a save left on it would point the model at a missing role. The playground's
  profiles are the console user's, named after the domain.

## 2026-10-19 — 7.3's first reading: the playground refused by the SCP, before decision 11's amendment

*Provenance. Claude, at the user's request in this session's chat, through Claude in Chrome in the
user's portal session as the Data Scientist User (the account menu reads *Data Scientist User*), in a
tab opened by URL. Claude's clicks opened the model list, chose a model and sent one prompt per model,
`Responda apenas: ok`. The reads around them are Claude's, as `awsds-infra-identity` (the live SCP),
`awsds-infra-sandbox-1` and `awsds-infra-data`. The portal's text is quoted verbatim with the account
ids replaced by the account's name. Times are UTC.*

- **[Claude] The SCP before**, 20:58: `DenyBedrockInvocationOutsideTheScopedModels` in `p-tgda7n58`
  lists the six spellings of the repository's document and no `application-inference-profile`.
- **[Claude] The playground's model list**, 21:12: *Spotlight models*, Nova Lite, then Claude Haiku 4.5
  *Cross-region*, and nothing else: the two the console enabled for the playground, where 7.2 had read
  *"No models found"*.
- **[Claude] Claude Haiku 4.5**, sent at about 21:13:07. The answer, and a red banner *"An error occurred
  in Explorer Chat."* carrying the same text:

  ```
  Something went wrong. User: arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-bedrock-model-consumption/28f1b390-0041-7068-8cc7-9ccef94277d1@cty232yk8f2zyo is not authorized to perform: bedrock:InvokeModelWithResponseStream on resource: arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/cp0gmvjv1h8q with an explicit deny in a service control policy: arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/p-tgda7n58
  ```

- **[Claude] Nova Lite**, sent at 21:13:56:

  ```
  Something went wrong. User: arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-bedrock-model-consumption/28f1b390-0041-7068-8cc7-9ccef94277d1@d747chsyrc379s is not authorized to perform: bedrock:InvokeModelWithResponseStream on resource: arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/csu817ovl4kz with an explicit deny in a service control policy: arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/p-tgda7n58
  ```

- **[Claude] The trail.** Sandbox's holds `ConverseStream` at 21:13:08 as
  `awsds-sandbox-bedrock-model-consumption`, session `28f1b390-0041-7068-8cc7-9ccef94277d1@cty232yk8f2zyo`,
  `AccessDenied`, no `vpcEndpointId` and a browser's user agent; `ListFoundationModels` as the same role
  at 21:12:24 and 21:13:05; and `AssumeRole` of the role by `datazone.amazonaws.com` with that session
  name at 21:12:23 (twice), 21:13:05 and 21:13:07. Nova Lite's `ConverseStream`, delivered by 21:16:05,
  is at 21:13:56, session `…@d747chsyrc379s`, `AccessDenied`, no `vpcEndpointId`, so Nova Lite was sent
  at 21:13:56. Data Governance's holds `CreateSubscriptionRequest` by the domain execution role at
  21:12:18 (twice) and 21:13:51, and `GetConnection` from 21:11:53.
- **[Claude] The subscriptions and grants**, read at 21:15. Three subscriptions, `APPROVED`, each with a
  user as principal: two to Haiku 4.5's playground listing, both at 21:12:18, and one to Nova Lite's at
  21:13:51. Their grants read `COMPLETED`, the asset `GRANTED`, each naming a connection (21:12:19,
  21:13:52).
- **[Claude] What the reading says.** The playground's path works to its last call. The list shows the
  enabled models, and the portal subscribes for the person, with no approval since the listing asks
  for none. DataZone grants the subscription and vends the consumption role to a session named
  `<DataZone user>@<environment>`, and the browser calls Bedrock through the playground's application
  inference profile, past every VPC endpoint. The SCP refuses that call on the profile's pass, attributable
  from its own text, because the statement's `NotResource` names no application inference profile.
  Decision 13's prediction and decision 11's grown amendment rest on this reading. Verification xix is
  answered in part: before the amendment the SCP refuses every playground model, the scoped one
  included, on the profile; the refusal of the model outside the scoped set on its foundation model
  waits for the amendment. The portal subscribed twice to Haiku 4.5's listing in the same second.

## 2026-10-19 — decision 11 taken

- **[user] Decision 11**, in this session's chat after the context was laid out: *"Ok, pode seguir
  conforme sua recomendação. Entendi que é a opção (a)."*, the recommended (a) grown by decision 13's
  reading. `DenyBedrockInvocationOutsideTheScopedModels` admits Titan Text Embeddings V2's
  `foundation-model` ARN and `arn:aws:bedrock:*:*:application-inference-profile/*`, after the commit
  that teaches `aws/awslib/bedrockscope.py` an admitted model, with the battery's rows for both and the
  apply by the user's hand from `Identity`.

## 2026-10-19 — decision 11's amendment written and planned; the battery's before-half

- **[Claude] The parser**, commit `2aa52ec3`: `aws/awslib/bedrockscope.py`'s `scp_declaration()` returns
  the scoped models alone, those with a profile, and the new `scp_admitted()` returns every admitted
  `foundation-model` and whether `application-inference-profile/*` is admitted; `ML-8` and `BS-1` read
  the second. Against the document as applied: 3 scoped, 3 admitted, profiles not admitted. Against the
  amended one: 3 scoped, 4 admitted, profiles admitted.
- **[Claude] The amendment**, uncommitted when planned: `DenyBedrockInvocationOutsideTheScopedModels` in
  `awsds-org-scp-ou-interactive.json` gains `arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0`
  and `arn:aws:bedrock:*:*:application-inference-profile/*` in its `NotResource`; the policy's description
  in `locals.tf` gains a sentence (502 of 512 characters); `POLICIES.md`'s row names both entries and the
  second trigger. `./scripts/check-index.py` clean.
- **[Claude] The plan**, `identity/org-policies` as `awsds-infra-identity`, saved at 21:30:49 UTC as
  `~/tmp/s17-decision-11-scp.tfplan`, not applied:

  ```
  # aws_organizations_policy.this["awsds-org-scp-ou-interactive"] will be updated in-place
                          + "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0",
                          + "arn:aws:bedrock:*:*:application-inference-profile/*",
  Plan: 0 to add, 1 to change, 0 to destroy.
      ~ awsds-org-scp-ou-interactive  = 1362 -> 1483
  ```

  The description changes with it.
- **[Claude] The battery's before-half**, `./aws/probes/scp-battery.py --phase ou`, 21:31:24 to
  21:32:45 UTC, with two new rows: `41 as expected, 1 unexpected, 7 not measured`. The unexpected row is
  Titan's, refused as predicted before the apply:

  ```
  FAIL	ou	sandbox1	allow	DENY-SCP	p-tgda7n58	interactive (inherited): bedrock:InvokeModel on amazon.titan-embed-text-v2:0 (Stage 17 decision 11)
  ok  	ou	sandbox1	allow	ALLOWED	reached-authorization	interactive (inherited): bedrock:InvokeModel through an application inference profile (Stage 17 decision 11)
  ```

  The second row invoked a profile id that does not exist and read `ALLOWED` with the entry absent. The
  same call by hand at 21:33:00 UTC, as `awsds-infra-sandbox-1`, answered:

  ```
  An error occurred (ValidationException) when calling the InvokeModel operation: The provided model identifier is invalid.
  ```

  Bedrock refuses an unknown profile id before it authorizes, so that row reads the same on both sides
  of the amendment. It left `probes.py` before the commit, and the battery holds 48 `ou` rows. 7.3's
  chat after the apply measures the profile's pass.

## 2026-10-19 — decision 11 applied by the user; the readings after, and 7.3's second chat

*Provenance. The apply is the user's, from `Identity` as `awsds-infra-identity`, its output pasted in
this session's chat. Everything after it is Claude's: the reads as `awsds-infra-identity`,
`awsds-infra-sandbox-1` and `awsds-infra-data`, the battery, and the chat through Claude in Chrome in
the user's portal session as the Data Scientist User (the account menu reads *Data Scientist User*), in
a tab opened by URL, one prompt per model, `Responda apenas: ok`, as in the first reading. The portal's
text is quoted verbatim with the account ids replaced by the account's name. Times are UTC.*

- **[user] The apply** of `~/tmp/s17-decision-11-scp.tfplan`:

  ```
  aws_organizations_policy.this["awsds-org-scp-ou-interactive"]: Modifying... [id=p-tgda7n58]
  aws_organizations_policy.this["awsds-org-scp-ou-interactive"]: Modifications complete after 2s [id=p-tgda7n58]
  Releasing state lock. This may take a few moments...

  Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
  ```

  Among the outputs, `"awsds-org-scp-ou-interactive" = 1483`. Identity's trail holds `UpdatePolicy` of
  `p-tgda7n58` at 21:58:46 by `InfrastructureAccess`, with no error.
- **[Claude] The re-plan**, 21:59:36 to 21:59:55: `No changes. Your infrastructure matches the
  configuration.`
- **[Claude] The live statement**: `DenyBedrockInvocationOutsideTheScopedModels` lists the six
  spellings, then `arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0` and
  `arn:aws:bedrock:*:*:application-inference-profile/*`. The description ends *"Stage 17 decision 11 -
  the embeddings model and application inference profiles are admitted beside them."*
- **[Claude] The battery's after-half**, `--phase ou`, 22:00:11 to 22:01:17: `41 as expected, 0
  unexpected, 7 not measured`. Titan's row:

  ```
  ok  	ou	sandbox1	allow	ALLOWED	succeeded	interactive (inherited): bedrock:InvokeModel on amazon.titan-embed-text-v2:0 (Stage 17 decision 11)
  ```

- **[Claude] `./aws/bedrock-scope.py`**: `BS-1` to `BS-7` pass. `BS-1` reads `3 model(s), 3 region(s);
  admitted beside it: amazon.titan-embed-text-v2:0; application inference profiles admitted`.
- **[Claude] `./aws/bedrock.py`**: every check passes or is a note, and `BR-4` reads `3 of 3 in
  awsds-infra-sandbox-1`. Its failed calls are the seven profiles whose SSO sessions were not signed in
  (`awsds-ctadmin`, `awsds-deploy`, `awsds-devenv`, `awsds-governance`, `awsds-scientist`). `BR-7`'s
  note reads `availability DOES distinguish the form`: `agreementAvailability` reads `AVAILABLE` in
  `Sandbox Account 1`, the one account with a form, and `NOT_AVAILABLE` in the five without, for the
  three scoped models. The snapshots of 2026-09-12 and 2026-10-11 on this laptop read the control `not
  runnable`. An availability read is not an invocation, so the amendment does not move it; `BR-7`
  belongs to Stage 6e.
- **[Claude] `./aws/sandbox-ml.py`**, 22:04:06 to 22:06:47: all checks passed. `ML-8` reads Titan's
  availability `agreement AVAILABLE, authorization AUTHORIZED, entitlement AVAILABLE, region AVAILABLE`
  and `admitted by the repository's SCP (decision 11), application inference profiles admitted`.
- **[Claude] Claude Haiku 4.5**, sent at 22:08:48 by the trail: the answer `ok`, and the playground's
  reading `Input: 13`, `Output: 4`, `Latency: 652ms`.
- **[Claude] Nova Lite**, sent at 22:09:15 by the trail. The answer, and a red banner *"An error
  occurred in Explorer Chat."* carrying the same text:

  ```
  Something went wrong. User: arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-bedrock-model-consumption/28f1b390-0041-7068-8cc7-9ccef94277d1@d747chsyrc379s is not authorized to perform: bedrock:InvokeModelWithResponseStream on resource: arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-lite-v1:0 with an explicit deny in a service control policy: arn:aws:organizations::<Management Account>:policy/o-4z1leiit0c/service_control_policy/p-tgda7n58
  ```

- **[Claude] The trail**, Sandbox's. Haiku's `ConverseStream` at 22:08:48 is an `AwsApiCall` as
  `awsds-sandbox-bedrock-model-consumption`, session `…@cty232yk8f2zyo`, with `modelId` the
  playground's profile `cp0gmvjv1h8q`, `inferenceRegion` `us-east-2`, resource
  `foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0`, no error, no `vpcEndpointId`, and host
  `bedrock-runtime.us-west-2.amazonaws.com`; an `AwsServiceEvent` of the same name in the same second
  names the same model. Nova Lite's `ConverseStream` at 22:09:15, session `…@d747chsyrc379s`, is
  `AccessDenied` with the text above, its resource the profile `csu817ovl4kz`, no `vpcEndpointId`.
- **[Claude] The subscriptions**, read at 22:10 in Data Governance with the governance project as
  approver: the same three as the first chat (two to Haiku 4.5's playground listing at 21:12:18, one to
  Nova Lite's at 21:13:51), all `APPROVED`. The second chat subscribed to nothing.
- **[Claude] `./aws/bedrock-usage.py 2026-10-19T21:00Z 2026-10-19T22:20Z`**, Sandbox, `us-west-2`:
  `BU-1` to `BU-4` pass. `cp0gmvjv1h8q` carries 1 invocation, 13 tokens in and 4 out, the Haiku chat;
  Titan 1 invocation and 2 tokens in, the battery's row; each `us.` profile 2 invocations, the
  battery's two halves. `BU-5` notes `cp0gmvjv1h8q` and Titan unpriced: the script prices by model id
  and reads the profile's series under the profile's id.
- **[Claude] What the reading says.** Verification xix is answered. After the amendment the scoped model
  answers through the playground's application inference profile. The model outside the scoped set
  passes the profile's pass and is refused on its foundation model's, by `p-tgda7n58`, attributable
  from its own text. The model ceiling holds on the foundation-model pass, which decision 11 had
  recorded as unmeasured.

## 2026-10-19 — `bedrock-usage.py` rates a call through an application inference profile

*Provenance. Claude, in a session of its own started by the one that took decisions 13 and 11, as the
infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`).
Every AWS call was a read. The script's change is on this session's branch; the fabricated `aws` it
was exercised against lives in the session's scratchpad and is not tracked. Times are UTC.*

- **[Claude] The run before the change**, the same window as decision 11's entry
  (`2026-10-19T21:00Z 2026-10-19T22:20Z`): `BU-1` to `BU-4` pass, and `BU-5` notes `2 unpriced:
  amazon.titan-embed-text-v2:0, cp0gmvjv1h8q`, each with *"not an Anthropic model; docs/PRICING.md
  prices it elsewhere"*. The script priced by model id alone.
- **[Claude] The application inference profiles**, `bedrock list-inference-profiles --type-equals
  APPLICATION` in `us-west-2`: two, both `ACTIVE` and named after the domain id.
  - `cp0gmvjv1h8q`, created 20:52:31: `anthropic.claude-haiku-4-5-20251001-v1:0` in `us-east-1`,
    `us-east-2` and `us-west-2`.
  - `csu817ovl4kz`, created 20:52:43: `amazon.nova-lite-v1:0` in `us-west-2` alone.
- **[Claude] The system-defined profiles.** With no `--type-equals` the call returned 96 profiles, every
  one `SYSTEM_DEFINED`; the API reference names both types and no default.
  `us.anthropic.claude-haiku-4-5-20251001-v1:0` lists the same three model ARNs as `cp0gmvjv1h8q`;
  `global.anthropic.claude-haiku-4-5-20251001-v1:0` lists a model ARN with no Region and the `us-west-2`
  one; `us.amazon.nova-lite-v1:0` lists three Regions where `csu817ovl4kz` lists one. No
  system-defined profile names Titan.
- **[Claude] The trail.** Haiku's `ConverseStream` at 22:08:48 carries `modelId`
  `arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/cp0gmvjv1h8q`; CloudWatch
  carries the same call under `cp0gmvjv1h8q`.
- **[Claude] The change.** A `ModelId` with no dot names no model. The script reads
  `ListInferenceProfiles` once per type and rates such a row as the system-defined profile listing the
  same model ARNs, or as the model when the profile lists `us-west-2` alone. It prints the row as
  `<id> (<model>)`, with a `profile:` line under the table saying which. A profile no longer in the
  account stays unpriced, and the note says so, naming CloudTrail's ARN when the window holds one.
  Titan Text Embeddings V2 is priced from `docs/PRICING.md`'s row, 0.00002 USD per 1K input tokens
  (read 2026-10-12), the one row there naming a model id; a token count that row does not price leaves
  the model unpriced. No profile id is written in the code.
- **[Claude] Exercised against a fabricated `aws`** before the live run: a copy of a `us.` profile, of a
  `global.` profile and of a model in `us-west-2`; a profile gone, with and without CloudTrail's ARN;
  Regions no system-defined profile lists; two models in one profile; Titan with output tokens; and
  `ListInferenceProfiles` refused, which exits 1 with the call in section 7. Each read as intended.
- **[Claude] The re-run**, `./aws/bedrock-usage.py 2026-10-19T21:00Z 2026-10-19T22:20Z`, stamped
  23:05:37, exit 0, *"all checks passed"*:

  ```
  cp0gmvjv1h8q (claude-haiku-4-5)               1            13     4       0           0            0.0000
  profile: cp0gmvjv1h8q (claude-haiku-4-5) - an application inference profile that lists the model ARNs of us.anthropic.claude-haiku-4-5-20251001-v1:0, so it is rated as that profile
  pass    BU-5  every model with tokens has a recorded rate   5 model(s), from docs/PRICING.md, 1 through an application inference profile
  ```

  The row prices at 13 × 1.10 + 4 × 5.50 USD per 1M tokens, 0.0000363 USD, which the report's four
  decimals print as `0.0000`; Titan's 2 tokens price at 0.00000004 USD. `BU-1` to `BU-4` read as before,
  and section 1 reads `ListInferenceProfiles us-west-2, 2 application and 96 system-defined`.
- **[Claude] The month**, `./aws/bedrock-usage.py 2026-10`, stamped 23:06:10, exit 0: `BU-5` passes
  with the same five models, and the per-day table's 2026-10-19 row counts the profile's invocation
  among its 11 (0.0004 USD).
- **[Claude] Outside this change.** `aws/bedrock.py` section 5 passes no type to
  `list-inference-profiles`, so it lists no application profile while its text describes them; the
  default is now in `lessons.md`'s list of platform behaviours. The script belongs to Stage 6e.

## 2026-10-20 — the readings owed with the environment down, and the provisioning role's path

*Provenance. Claude, in a session started by the session that ran 2026-10-20's offline round, from the
worktree `stage-17-log-reads-c5d8e8` at `origin/main` `1a84fc47`, as the infrastructure user with
`InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and in `Data Governance`
(`awsds-infra-data`), with the whole environment down. Every AWS call was a read. The reports print the
caller's ARN and were not copied; no quoted line carries an account id or an e-mail address. Times are
UTC.*

- **[Claude] The provisioning role**, read with `iam get-role` at 22:06, since decision 13's step 2 in
  the stage file placed it at `/service-role/` with a name built from the vended account name.
  `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>` sits at path `/`, created
  2026-10-19 at 20:27:17, under `awsds-sandbox-project-boundary`, its `RoleLastUsed` empty. Compared
  without printing them, the name's suffix and the trust's `aws:SourceAccount` are the account of the
  domain ARN `awsds-infra-data` lists, and not Sandbox's. The slice reads that account from the
  governance state's `domain_arn`, and its `iam-role` module sets no path. The consumption role
  `awsds-sandbox-bedrock-model-consumption` sits at `/` too, last used 2026-10-19 at 22:09:15 in
  `us-west-2`, Nova Lite's refused call.
- **[Claude] `./aws/devenv.py`**, stamped 22:01:30, exit 2, run first so that `ML-9` reads a current
  `DE-5`. `DE-5` fails as it has since PR #172: version 9 (`aafa08da98a61f5c`) against the Dockerfile's
  `6faf2e4761622508`, 2 names the image lacks. `DE-2` fails on `sandbox/egress` being down, as on
  2026-10-18, and `DE-3` and `DE-6` are not compared.
- **[Claude] `./aws/sandbox-ml.py`**, 22:01:30 to 22:04:02, the report stamped 22:04:01, exit 0, *"all
  checks passed"*. Against the run of 2026-10-19 at 22:06:45 (decision 11's entry), section 10 alone
  moved, the session being down where it was up then: no interface endpoint where eighteen read
  `available`, the DNS Firewall list `awsds-sandbox-egress-allow` absent where it held 14 entries, and
  `ML-9`'s endpoint row a note where it was a pass. `ML-1` to `ML-8` read as on 2026-10-19, and
  CloudTrail holds no create after `CreateMlflowApp` at 06:39:55 on 2026-10-19.
- **[Claude] `ML-7`.** The quotas read 20 for training, 8 for endpoints, 8 for transform and 10 for
  processing, all applied, and 3 MLflow Apps. The three increase requests still read `CASE_OPENED`.
  `list-requested-service-quota-change-history` at 22:03:59 gives the last updates read on 2026-10-18:
  21:45:45 and 21:45:49 on 2026-10-17 for `L-CCE2AFA6` and `L-614B09FD`, and 00:23:33 on 2026-10-18 for
  `L-236AE59F`. No case has moved since.
- **[Claude] `ML-2`.** `ml-demo-mlflow` reads `Created`, MLflow `3.10.1`, its store the project's
  `dev/data/ml/mlflow` prefix, its role the project role, `AutoModelRegistrationDisabled`, no account
  default, maintenance `Sun:14:15`, the project's tag and no key, as at 06:47 on 2026-10-19.
- **[Claude] The models' objects**, at 22:04:45. Sandbox holds the two application inference profiles
  of 2026-10-19, the playground's `cp0gmvjv1h8q` and `csu817ovl4kz`. The governance project approves
  the same three subscriptions, each a person's, to the playground listings of Haiku 4.5 and Nova
  Lite. No project has subscribed to a model.

## 2026-10-21 — 7.4a re-planned after decision 11's apply, and the knowledge base's Lambdas, written on 2026-10-20 (PR #212), recorded

*Claude's sitting, no AWS call: the session that opened PR #212 (merged 2026-10-20T21:51:01Z) revised the
stage file and `lessons.md` from this log's entries of 2026-10-19, and read the AWS CLI's SageMaker service
model. It wrote no entry, under the rule of that day; this one is written on 2026-10-21 from the PR's body
and diff, with no AWS call either. Times are UTC.*

- **[Claude] 7.4a plans one sync, expected `COMPLETE`.** The user applied decision 11's amendment on
  2026-10-19 at 21:58:46, before any knowledge base existed (`ML-8` read none at 19:01), so the SCP's
  refusal of Titan was read by the battery's before-half, `DENY-SCP` naming `p-tgda7n58` as
  `InfrastructureAccess` at 21:31, and by no sync. Verification xxii, the pass table, the Cost row and the
  risks describe that sync, and 7.4a keeps the amendment's procedure as a record.
- **[Claude] The knowledge base's Lambdas depend on decision 12.** The blueprint's template creates the
  two functions and their role for an OpenSearch Serverless store alone (7.0a's reading of 2026-10-19),
  while AWS's blueprint page lists them with no condition; the menu table, decision 10 and 7.4a's `ML-8`
  reading carry it.
- **[Claude] The instance-preference risk names both paths**: `ResourceConfig.InstancePreferences` for a
  training job and `ProcessingResources.ClusterConfig.InstancePreferences` for a processing job, read in
  the AWS CLI's SageMaker service model.
- **[Claude] `lessons.md`'s list of platform behaviours** gains three readings of 2026-10-19 from this log:
  `InvokeModel` refuses an unknown application inference profile id before it authorizes; only the domain
  account's setup creates `GenerativeAIModelGovernanceProject`; the Bedrock models tab adopts the
  provisioning role named `AmazonSageMakerBedrockModelManagementRole-<domain account id>`.

## 2026-11-16 — the request, the answer on the menus, and passes 9 and 10 written with no AWS call

*A cloud session's sitting with no AWS credential: no AWS call, no apply and no portal act. Times are
UTC. A sentence quoted from an AWS page was read in the page's Markdown form, through a page-reading
agent, unless the bullet names the HTML form, and a sentence quoted from code is the file's own string.
The repository was read at `main` `c5e1718`. The sitting ran past midnight: the decisions it put on cards
and what it did on 2026-11-17 are the next two entries.*

- **[user] The request**, in a thread of the Claude project at 20:22, after a line on how the task is
  run:

  > Sobre aplicações SMUS promovidas pela ferramenta CI/CD entre ambientes
  > (https://github.com/aws/CICD-for-SageMakerUnifiedStudio), entendi que as aplicações são sempre
  > disparadas por workflow, que é o alvo principal do repositório `awsds-workflows`.
  >
  > Utilizamos também o `awsds-workflows` para auxiliar na criação de aplicações SMUS de exemplo no
  > `AWS-DataScience`.
  >
  > Acredito que também exercitamos algumas aplicações que envolvem modelos de IA, via funcionalidades
  > do Bedrock expostas pela interface do SMUS. Entendi, por exemplo, que existem tasks específicas de
  > treinamento.
  >
  > Considerando o `awsds-workflows` e o `AWS-DataScience`, peço o seguinte:
  >
  > * listar quais foram os pontos exercitados de aplicações SMUS com task envolvendo funcionalidades
  >   do bedrock.
  > * Olhando o SMUS, ele expõe os seguintes itens de menu via interface considerando funcionalidades
  >   do Bedrock: "AI/ML" -> [Models, Training Jobs, MLflow, Inference endpoints, ML pipelines, Feature
  >   Store], "Generative AI" -> [Playgound, AI apps]. Qual funcionalidade cada item de menu desse
  >   cobre? Como estas funcionalidades se encaixam em aplicações SMUS promovidas para outro ambiente?
  >
  > Revise o Stage 17 considerando:
  >
  > * o aprendizado desta sessão
  > * o resultado desta pesquisa
  > * incluir no estágio aplicação de exemplo exercitando as funcionalidades de modelos de AI/ML, de
  >   forma que esta aplicação seja promovida para production via esteira.
  > * escrever runbook explicando funcionalidades e fluxo de desenvolvimento de aplicações considerando
  >   a superfície SMUS de AI/ML

- **[Claude] What the two repositories had exercised**, answered at 20:49 from this repository's stage
  files and logs and from `awsds-workflows` at `196acee`. No task of an application has called Amazon
  Bedrock, in either repository, and a project role of Staging or of Production is denied `bedrock:*`
  since 2026-11-11 (Stage 19 decision 21 (b)). Bedrock ran outside applications: Claude Code in a space
  (6e, 2026-09-12), the Generative AI menu with five models enabled and the playground's chat (this log,
  2026-10-19), and the SCP battery's Bedrock rows. What applications exercised is Amazon SageMaker AI's:
  a processing-job task (6i and `app-etl`), a training-job task and its evaluation (`app-etl-train`, run
  in Staging and in Production), and a registration, a manual approval and a batch transform that jobs of
  the pipeline make (`scripts/model-chain.py`), never a task. `awsds-workflows` holds the lint's `treino`
  and `imagem` rules and no example that trains a model or calls Bedrock. The message dated the training
  task's last run 2026-11-16, at `v0.5.2`, for both targets: that run is Staging's, and Production's
  newest training job is of 2026-10-25, under `v0.4.2` (Stage 19's log, 2026-11-16).
- **[Claude] The menus, answered in the same message.** The six entries the request lists under **AI/ML**
  are Amazon SageMaker AI's, and **Generative AI** alone is Amazon Bedrock's; the task the request calls
  a training task is `SageMakerTrainingOperator`. The message's table, entry by entry, is the stage
  file's "The left navigation's entries, and what a promoted application does with each". Its rule as
  sent: the CI/CD CLI promotes files, workflows and the catalog, and a model, an endpoint, a pipeline, a
  feature group or a Bedrock object is created in each environment by a task or by a job of the pipeline.
  Decision 21 (b) changed that for a trained model's archive the next day. The message also asked the
  user in which portal the menu was read: *Models*, *Training Jobs* and *Feature Store* are entries of
  the guide's chapter for IAM-based domains, and the lab's domain signs its users in through IAM Identity
  Center. No answer came during the sitting, and step 0.9 reads the lab's navigation.
- **[Claude] AWS's SageMaker Unified Studio user guide** (read 20:32 to 20:46):
  - the table of contents (`toc-contents.json`): the section *AI and machine learning* holds *Amazon
    Bedrock in SageMaker Unified Studio* and *Machine learning*, the second in two chapters. *Machine
    learning in Identity Center-based domains*: Discover Jumpstart models, Build models in JupyterLab,
    Train models, Use inference endpoints to deploy models, Pipelines, Model registry, Track experiments
    using MLflow, HyperPod clusters, Partner AI apps. *Machine Learning Workflows in IAM-based domains*:
    Discover Foundation models, Deploy Foundation models, Track experiments using MLflow, Create and
    monitor custom training jobs, Manage Registered Models, Feature Store. The chapter's opening page
    says nothing on which domain type offers which capability;
  - the Identity Center chapter's navigation: *"In the left navigation pane, under AI/ML, choose
    JumpStart models."*, *"… choose Inference endpoints."*, *"… choose ML pipelines."*, *"… choose Model
    registry."*, *"… choose MLflow."*, and *"You can view the training job from the Training jobs
    page."*;
  - the IAM chapter's: *"From the left navigation menu, choose **Models**."*, with the tabs *Foundation
    Models* and *Registered Models*; *"Navigate to **AI/ML** > **Models** and select the **Registered
    Models** tab to view the models."*; *"You can monitor the results of the training job by selecting
    **Training Jobs** on the left panel"*; *"In the left navigation pane, under AI/ML, choose **Feature
    Store**."*;
  - Feature Store: *"The Feature Store interface described on this page is available in Amazon SageMaker
    Unified Studio domains configured with AWS IAM."* and *"You can use Feature Store from a notebook or
    IDE using the SDK in any domain type."*; *"You cannot edit or delete features after the feature group
    is saved."*; *"Data stored in the offline store (Amazon S3) is not automatically deleted."*;
  - MLflow, the Identity Center chapter: *"MLflow Apps are the latest offering with faster startup times
    and cross-account sharing"*; *"Automatically register models from MLflow Model Registry to SageMaker
    AI Model Registry."*; *"Your domain administrator can configure the project profile to automatically
    create an MLflow App during project creation"*. The IAM chapter: *"Note that you can't create a new
    MLflow App in Amazon SageMaker Unified Studio."*;
  - Pipelines: *"You can define the steps using the Amazon SageMaker Unified Studio visual pipeline
    designer, or by creating a pipeline definition JSON schema."*; *"You can also import a pipeline
    definition file from your computer."*; the definition downloads as JSON, with *"Version control"* and
    *"Integration with automation processes"* among the uses the page lists. The page states nothing on a
    schedule, a workflow or another account;
  - Model registry: *"Use the model registry to catalog your models and manage model deployment to
    production."*; *"For each run of the ML pipeline, create a model version that you register in the
    model group you created in the first step."*;
  - the XGBoost recipe's prerequisites: a project *"created with the **All capabilities** project
    profile"* and *"an MLflow tracking server created in your project"*; *"The endpoint runs on a
    dedicated `ml.m5.large` instance and incurs costs as long as it is in service."*;
  - the release notes, entry of October 8, 2026: *"Chat playground, image and video playground, and
    shared apps and prompts can now be found in **Playground**."* and *"Chat agent, flow, prompt, and my
    apps can now be found in **AI apps**."*;
  - Amazon Bedrock in SageMaker Unified Studio: *"you can create two types of generative AI apps: a chat
    agent app and a flow app"*; the model catalog under *"Generative AI"*, *"Playground"*, which
    *"doesn't support Provisioned throughput, custom models or imported models"*; a chat agent app
    deployed by an alias and a version (*"You can create up to 8 aliases for a chat agent app."*); a
    shared app published to the catalog (*"You can't stop sharing a snapshot without deleting the chat
    agent app."*); the evaluation page (*"doesn't support Human-based evaluations"*, and *"the Amazon
    Bedrock API allows users to list all model evaluation jobs in the AWS account that hosts the
    project"*);
  - the export: *"When you export an app, Amazon Bedrock in SageMaker Unified Studio exports a zip file
    with the AWS CloudFormation templates and other files required by your app."*; *"you deploy the
    contents of the zip file into your AWS account (or another AWS account, if you prefer)"*; *"The data
    source files for a knowledge base and the secrets for a function aren't exported, and you have to
    configure them during the deployment."*; the zip is *"amazon-bedrock-ide-app-export-\*.zip"*, and
    *"You can't export an app unless you first save and run the app."*; the deployment is a shell script
    over the AWS CLI and CloudFormation, with a role that carries `provisioning-inline-policy.json`, an
    S3 bucket and, optionally, a KMS key *"tagged with key `EnableBedrock` and a value of `true`"*. The
    overview names the script `deploy-app.sh` and the deployment page `deployApp.sh`;
  - not read: *Create a chat agent app with Amazon Bedrock* (`create-chat-agent-app`) and the guide's
    document history, each a client error in the Markdown form and a page with no body in the HTML form.
    *Pipelines*, *Export your Amazon Bedrock app* and *Reuse and share Amazon Bedrock prompts* were
    rate-limited at the first ask and read at 20:46.
- **[Claude] The SageMaker AI developer guide and its pricing page** (20:47). Feature Store: *"Create
  feature groups that can be configured to include an online or offline store, or both."*; *"Data is
  stored in the offline store in Parquet format for optimized storage and query access."*; *"For batch
  ingestion, you can configure a processing job to batch ingest your data into Feature Store"*; the
  managed policy `AmazonSageMakerFeatureStoreAccess`; and *"After they are created, feature groups are
  mutable and can evolve their schema after creation."*, beside the portal page's sentence that a saved
  feature is never edited or deleted. MLflow: MLflow Apps are available in US West (Oregon); *"All MLflow
  REST APIs are represented as IAM actions under the `sagemaker-mlflow` service prefix."* The pricing
  page: *"Customers pay for MLflow Tracking Servers based on compute and storage costs."*, and no
  sentence on what an MLflow App bills. Not read: `mlflow-app.md`, a client error.
- **[Claude] Agents Classic** (the Bedrock user guide's page on its maintenance mode, read 20:46 and
  whole at 23:46, 18,471 characters): *"Amazon Bedrock Agents (launched November 2023) is now Amazon
  Bedrock Agents Classic and will no longer be open to new customers starting on July 30, 2026."*; *"Only
  CreateAgent and InvokeInlineAgent are restricted for accounts without prior usage."*; *"Accounts
  without prior usage will receive an AccessDeniedException (HTTP 403) when calling CreateAgent or
  InvokeInlineAgent."*; *"If your account has had Bedrock Agents activity in the past 12 months, you are
  allowlisted and unaffected."*; *"There is no exception process."*; *"We recommend that you migrate your
  Amazon Bedrock Agents Classic workloads to Amazon Bedrock AgentCore."*; *"There is no migration
  deadline. Bedrock Agents Classic remains available to existing customers in maintenance mode with no
  planned end-of-life date."*; *"Knowledge Bases continue to work and are not affected by maintenance
  mode."* The page states nothing on Amazon Bedrock Flows or on prompt management. No account of this
  estate has created an agent, so 7.4b's chat agent app is expected to be refused: inferred, not
  measured.
- **[Claude] The MWAA Serverless user guide** (20:32, and the HTML form at 21:03):
  - the operators page lists 25 entries whose name starts with `SageMaker`, `SageMakerNotebookOperator`
    under *Analytics* and 24 under *Machine learning*, the training, processing, transform, tuning,
    AutoML, model, endpoint, endpoint configuration, pipeline, experiment, notebook and
    register-model-version operators and their sensors among them; and 15 that start with `Bedrock`:
    `BedrockInvokeModelOperator`, `BedrockRaGOperator`, `BedrockRetrieveOperator`, the knowledge base,
    data source and ingestion operators, the customization and provisioned-throughput operators, three
    guardrail operators (create, create version, delete) and four sensors. It lists no
    `BedrockBatchInferenceOperator`, no `BedrockCreateEvaluationJobOperator` and no Feature Store or
    MLflow operator, and its one version reference is a link to the Amazon provider's documentation at
    9.38.0;
  - the page on Python and Bash operators differs between its two forms. The Markdown form's table of
    pre-installed packages holds `apache-airflow` 3.0.6, `apache-airflow-providers-amazon` 9.32.0,
    `boto3` and `botocore` 1.43.1, `dag-factory` 1.0.0, `pyyaml` unpinned, `lz4` 4.4.4 and five AWS
    cryptography packages. The HTML form's holds the Amazon provider at 9.38.0,
    `apache-airflow-providers-duckdb` 0.2.1 and `duckdb` 2.0.0, and no cryptography package. Neither
    lists `mlflow`, `sagemaker` or `sagemaker-studio`, and both say a pre-installed package takes
    precedence over the archive's;
  - the document history holds three entries, the latest of August 17, 2026 (*"Python and Bash operator
    support"*).
- **[Claude] The Amazon provider's code** (20:52 and 21:03): `operators/sagemaker.py`,
  `operators/bedrock.py` and `hooks/sagemaker.py`, fetched from the `apache/airflow` repository at the
  tags `providers-amazon/9.32.0` and `providers-amazon/9.38.0`, the two versions the guide's forms name.
  What the transform, model, endpoint, register and pipeline operators call is `SUP-372`; what the
  Bedrock invoke, retrieval and guardrail operators call and log is `SUP-373`. The same file holds three
  AgentCore runtime operators at both tags, which the service's page does not list.
- **[Claude] The CI/CD CLI's documents** (its repository at `main`, fetched 20:25 to 20:33: the README,
  the examples guide, the manifest guide and schema, the pages on connections, bootstrap actions,
  commands and Airflow operators). The README's "Supported AWS Services", under *"Deploy workflows using
  these AWS services through Airflow YAML syntax"*, lists SageMaker Training, SageMaker Pipelines,
  Feature Store, Model Registry and Batch Transform under Machine Learning, and Amazon Bedrock, Bedrock
  Agents, Bedrock Knowledge Bases and Guardrails under Generative AI; its "What Can You Deploy?" marks
  *"Feature Store (future)"* and *"Batch transforms (future)"*. On projects: *"A project can host a
  single application or multiple applications depending on your architecture and CI/CD methodology."* The
  schema comments `storage` as *"Storage content (S3 files, data, models)"*. No document names AgentCore.
- **[Claude] The worker's archive of the MLflow client, measured on a build host** (20:50, this session's
  Linux x86_64 container, `uv` 0.11.32, `awsds-workflows` at `196acee`; step 9.4). A uv project that
  depends on `mlflow-skinny==3.10.1` and `sagemaker-mlflow`, the versions the app `ml-demo-mlflow` and
  1.6 name (unpinned, `mlflow-skinny` resolved to 3.18.0), locked `sagemaker-mlflow` 0.5.0.
  `awsds-workflows package-task <project> <entry module> <archive>` refused an entry module kept inside
  the project folder (*"já está na raiz do .zip"*), and with the module outside it wrote the archive:
  *"15288232 bytes, 55772613 descompactados, para o CPython 3.12 em x86_64-manylinux2014"*, 42
  distributions. Extracted, on CPython 3.12.3 with `boto3==1.43.1` beside it: the first import failed
  with *"ModuleNotFoundError: No module named 'yaml'"*, since the packager leaves out PyYAML as a package
  the worker brings; with PyYAML present, `mlflow` 3.10.1 and `sagemaker_mlflow` 0.5.0 imported,
  `mlflow.set_tracking_uri` took an `mlflow-app` ARN of AWS's example account, and MLflow's request-auth
  registry resolved `arn` to `AuthBoto`. Not measured: the import on a worker, and a tracking call.
- **[Claude] Pass 9 written, and the first card.** The stage file's first pass 9 had every stage train: a
  new application, `app-ml`, on the `app-etl` template and on release F's path. A card went out at
  20:49:42, "Escolher como a aplicação de exemplo de IA/ML entra no Stage 17": "Nova app-ml, GenAI no
  Sandbox" (recommended), "Nova app-ml com task Bedrock", "Estender a app-etl".
- **[user] An application for each path**, in the project's chat at 22:23:43, passed to the thread at
  22:23:50: *"Não sabia desta diferença, achava que todas features que mencionei eram do Bedrock, e não
  conhecia o SageMaker AI. Neste caso, crie apps novos exercitando os dois caminhos: um app para
  exercitar features do SageMaker AI, e outro app para exercitar o caminho Bedrock."* **[Claude]** took
  decisions 14 and 15 from those words, 15 against the recommendation, and withdrew the card at 22:25:33.
- **[Claude] Pass 10's readings** (22:34 to 22:41), for a model call from a project role of a target:
  - the estate, read in the repository: the root's baseline holds the two retention statements for every
    account, the interactive OU alone holds `DenyBedrockInvocationOutsideTheScopedModels` and
    `DenyBedrockReadsOutsideTheRoutedRegions`, and the `Workloads` OU's document holds no Bedrock
    statement; `Workloads` carries Control Tower's stock Region deny without the six `bedrock:`
    exemptions (`INV-12`); Sandbox alone has the retention mode `none`, the use-case form and model
    agreements (`INV-18`); `DenyDataZoneSubscriptionRequests` keeps a deployment project from subscribing
    to a model's listing, SageMaker Unified Studio's own grant of a model to a project;
  - the page on enforcing a guardrail in IAM (HTML form): *"You can enforce the use of a specific
    guardrail for model inference by including the `bedrock:GuardrailIdentifier` condition key in your
    IAM policy."*, for `Converse`, `ConverseStream`, `InvokeModel` and `InvokeModelWithResponseStream`;
    its example for any numbered version of one guardrail compares with `ArnLike` and a `:*` suffix; its
    limits: *"A user should not use the same role with additional permissions to invoke Bedrock APIs like
    `RetrieveAndGenerate`, `InvokeAgent`, and `InvokeInlineAgent` that make `InvokeModel` calls on behalf
    of the user."* and *"A user can bypass applying a guardrail in their prompt by using
    [guardrail input tags]. However, the guardrail is always applied on the response."*;
  - guardrail permissions: `bedrock:ApplyGuardrail` to use one, and the management actions
    `CreateGuardrail`, `CreateGuardrailVersion`, `DeleteGuardrail`, `GetGuardrail`, `ListGuardrails` and
    `UpdateGuardrail`. Cross-Region guardrail inference is a guardrail profile's, `us.guardrail.v1:0`
    routing a guardrail of `us-west-2` to `us-east-1`, `us-east-2` and `us-west-2`;
  - application inference profiles (HTML form): *"To create an application inference profile for one
    Region, specify a foundation model. Usage and costs for requests made to that Region with that model
    will be tracked."*;
  - the model and Region table (`models-region-compatibility`, 81,926 characters: one table for each
    model, one row for each Region, columns In-Region, Geo and Global), its first 39,904 characters word
    for word. In `us-west-2`: Nova Pro Geo alone, Nova 2 Lite Geo and Global, Titan Text Embeddings V2
    In-Region alone. The rows of Nova Lite and Nova Micro came in a summary of the page's tail, which was
    not relied on, and the next entry reads them. The Nova user guide's Regions cell lists no US West
    (Oregon) for Nova Pro, Nova Lite and Nova Micro but through cross-Region inference;
  - not read: the service authorization reference for Amazon Bedrock, a page with no body in the HTML
    form and a client error in the Markdown form.
- **[user] The criterion for decision 22**, at 22:53:09, on the card of 22:50:17 ("Escolha como a
  aplicação Bedrock chama o Bedrock em Staging e Production": "Exceção estreita na cerca", recommended,
  "Projeto de implantação próprio", "Só no Sandbox por enquanto"): *"Para esta decisão, considere o
  caminho natural pretendido pelo SMUS ou recomendação da AWS, considerando o SMUS CICD."*
- **[Claude] The criterion read against the CLI.** The examples guide deploys the notebooks, ETL and
  generative AI examples into one project, `test-marketing`, the generative AI one under a
  *"Project-specific IAM role with Bedrock permissions"* with the model a stage variable, and gives the
  two ML examples a project each. The answer went at 22:59:27: the first option, the narrow exception in
  each target's boundary, with the model and the guardrail's owner still the user's. The card was closed
  at 22:59:29 as answered in the conversation, a note of the user's words and not a tap. The same
  criterion stands for the later cards, and each says where the recommendation without it would differ.

## 2026-11-16 — decisions 23 to 26 and 16 to 21 put on cards, one at a time, to 01:33 on 2026-11-17

*The same sitting, with no AWS call. Times are UTC. A card is the Claude project's decision card: one
question, its options and one recommendation. A card's labels are quoted as the user read them, in the
card's order, and the stage file's decision of the same number holds each option as written and what
follows from the answer. A tap is the user's choice on a card. Each card followed a message with the
decision's context.*

- **[user] The walk asked**, at 23:17:29: *"Pode me passar o contexto de cada decisão, as opções e a
  recomendação, para decidirmos, um de cada vez"*. **[Claude]** named the order at 23:21:23: ten open
  decisions, pass 10's 23 to 26 and then pass 9's 16 to 21. The stage's older open decisions (5, 6, 7, 10
  and 12) stayed out of the round.
- **[Claude] The model's rows, read before decision 23's card** (23:20): the model and Region table
  again, word for word from character 39,904 to the Claude Haiku 5.5 table. In `us-west-2`: Amazon Nova
  Lite In-Region and Geo, Nova Micro Geo alone. Not seen: the rest of the page, the tables of Claude
  Sonnet 4.5, Haiku 4.5 and Opus 4.5 and of every provider after Anthropic among them. The table and the
  Nova guide's Regions cell disagree on Nova Lite in `us-west-2`. This log's entries of 2026-10-19 read
  Nova Lite as *On-demand* on the console's model-access page, where the three Claude models read
  *On-demand cross-region*, and the playground's application inference profile of Nova Lite as
  `us-west-2` alone; the playground's one call of it was refused by the SCP on the model's `us-west-2`
  ARN (`SUP-300`), so no answer from it has been read. Step 10.1 reads which text models answer inside
  `us-west-2`.
- **[Claude] Pass 10's cards, and [user] the answers**, all on 2026-11-16:
  - **23, the model** (card at 23:21:25): "Amazon Nova Lite, dentro de us-west-2" (recommended), "Claude
    Haiku 4.5 pelo perfil us."; the user tapped the first at 23:25:31;
  - **24, who owns the guardrail** (23:30:53): "Terraform de cada conta" (recommended), "Uma task do
    workflow", "Um job da esteira"; the user tapped the second at 23:35:56, against the recommendation.
    The card's line under that option: *"Forma do exemplo genai do SMUS CI/CD: a definição viaja com a
    aplicação. Todo papel de projeto da conta passa a criar guardrails, e a cerca não fixa mais a
    versão."*;
  - **25, a knowledge base** (23:39:17): "Nenhuma base na aplicação", "Incremento depois da 1a release"
    (recommended), "Incremento só no dev", "Já na primeira release"; the user tapped the second at
    23:39:29;
  - **26, what of the Generative AI menu stays in Sandbox** (23:40:08): "Agente, fluxo e avaliação no
    Sandbox" (recommended), "Promover também um fluxo"; never tapped, and withdrawn at 23:54:54 after the
    user's message below;
  - **26, where an agent on AgentCore is exercised** (23:55:06): "Promovido, depois da 1a release"
    (recommended), "Só no Sandbox", "Já na 1a release"; the user tapped the first at 23:55:27.
- **[user] AgentCore in place of Agents Classic**, at 23:42:08, with decision 26's first card open: *"Se
  "agentsclassic" é um serviço que será descontinuado e substituído por "agentcore", revise o plano para
  exercitar o novo serviço."*
- **[Claude] Amazon Bedrock AgentCore, read for that message** (23:46: the developer guide, the two API
  references, the pricing page and the service authorization reference):
  - the service's page: Runtime is *"A secure, serverless runtime environment purpose-built for deploying
    and scaling dynamic AI agents and tools."*, and the harness *"A managed agent loop that lets you
    define and invoke AI agents with a single API call."* The Regions page reads yes for US West (Oregon)
    on the harness, Runtime's microVMs and Instances, Memory, Gateway, Identity, the built-in tools,
    Observability, Policy and Evaluations;
  - Runtime: *"In AgentCore Runtime, each user session runs in a dedicated microVM with isolated CPU,
    memory, and filesystem resources."*; *"Sessions run for up to 8 hours on microVMs, or up to 14 days
    on Instances."*;
  - direct code deployment: *"AgentCore Runtime supports only the **arm64** architecture."*; *"A ZIP
    archive containing Linux **arm64** dependencies needs to be uploaded to S3 as a pre-requisite to
    Create Agent Runtime."*; *"The maximum size for a .zip deployment package for AgentCore Runtime is
    250 MB (zipped) and 750 MB (unzipped)."*; the runtimes are `PYTHON_3_10` to `PYTHON_3_14` and
    `NODE_22`;
  - the network: a runtime's `networkMode` is `PUBLIC` or `VPC`, and in VPC mode it *"does not have
    internet access by default"*. US West (Oregon)'s supported zones are `usw2-az1`, `usw2-az2` and
    `usw2-az3`, and this estate's subnets anchor on the first two. The network interfaces are the
    service-linked role `AWSServiceRoleForBedrockAgentCoreNetwork`'s, and *"the associated ENI may
    persist in your VPC for up to 8 hours before it is automatically removed."* The interface endpoints
    are `bedrock-agentcore`, `bedrock-agentcore-control` and `bedrock-agentcore.gateway`, and they take
    endpoint policies;
  - the execution role is trusted by `bedrock-agentcore.amazonaws.com` under `aws:SourceAccount` and
    `aws:SourceArn`, and the page's policy for direct code deployment holds the logs, X-Ray and metric
    statements and the model invocation. The caller's managed policy, `BedrockAgentCoreFullAccess`,
    *"grants broad permissions including GetWorkloadAccessTokenForUserId, which allows issuing workload
    access tokens using caller-supplied user identifier strings without IdP token verification."* The
    page states neither `iam:PassRole` nor the permission to invoke;
  - the service authorization reference (HTML form, read to about 90,000 characters, its condition-key
    and resource-type tables not received): `CreateAgentRuntime` takes the condition keys
    `bedrock-agentcore:subnets` and `bedrock-agentcore:securityGroups` and depends on `iam:PassRole`. No
    key for the network mode was seen;
  - the pricing page (the first 39,942 of 62,199 characters): *"Runtime microVMs v1 CPU $0.0895 per
    vCPU-hour"*, *"v1 Memory $0.00945 per GB-hour"*, *"Billing is calculated per second, using actual CPU
    and memory consumption, with a 1-second minimum"*. The page states neither the Region of its rates
    nor what a deployed runtime with no invocation bills; the next entry reads the Region's price list;
  - botocore 1.43.1's models, the wheel from PyPI at the version of the worker's `boto3`:
    `bedrock-agentcore`, 54 operations, `InvokeAgentRuntime` and `InvokeHarness` among them, and
    `bedrock-agentcore-control`, 115 operations, where `CreateAgentRuntime` takes a container or a
    `codeConfiguration` (an S3 object, a runtime and an entry point). A harness's Bedrock model
    configuration holds no guardrail member, and `InvokeHarness` lets its caller override the model, the
    system prompt and the tools;
  - SageMaker Unified Studio's administrator guide, the document history in its HTML form, entries of
    October 29, 2026: `SageMakerStudioProjectRoleMachineLearningPolicy` gained *"Amazon Bedrock AgentCore
    permissions, most of which are limited to resources tagged with the user's project"*, and
    `SageMakerStudioProjectUserRolePolicy` the passing of roles to AgentCore and the logs of its
    runtimes. The page's Markdown form stops at June 29, 2026;
  - the estate, read in the repository: `TM-28` is open, no SCP names `bedrock-agentcore`, both targets'
    boundaries hold it among the fenced services, and `vpc-egress`'s catalog excludes its endpoints by
    name.
- **[Claude] The CI/CD CLI's generative AI example** (its repository at `main`, the raw files at 23:48;
  GitHub's tree page refused the fetch). The manifest, `IntegrationTestGenAIWorkflow`, holds one stage,
  `test`, the storage items `agent-code` and `genai-workflows` and the workflow `genai_dev_workflow`: one
  task, a notebook run by `SageMakerNotebookOperator`. The notebook and its helpers call Amazon Bedrock
  Agents (`list_agents`, `get_agent`, `prepare_agent`, `create_agent_alias`,
  `associate_agent_knowledge_base`), `bedrock`'s `list_guardrails` and `create_guardrail`, IAM's
  `create_role` and `put_role_policy`, Lambda's `create_function`, a knowledge base's creation and
  ingestion and OpenSearch Serverless's `create_collection`. The larger helper was read to 39,844 of
  126,207 characters, and `create_agent` appears only in a summary of the rest. The example's test
  asserts an agent whose name holds `test_agent`. No file names AgentCore: AWS's example is built on
  Agents Classic, and a task of it creates the guardrail, the roles and the functions.
- **[Claude] Pass 9's cards, and [user] the answers**, the first card on 2026-11-16 and every other time
  on 2026-11-17:
  - **16, who registers a version** (23:57:01): "Um job da esteira, em Production", "Uma task do
    workflow" (recommended), "O operador pronto do Airflow"; the user tapped the second at 00:10:17. The
    stage file had recommended the pipeline's job, and the card moved the recommendation on the user's
    criterion and on AWS's `ml/training` example;
  - **17, MLflow** (00:12:15): "MLflow App nos três ambientes" (recommended), "MLflow só no dev",
    "Tracking server, como no exemplo"; the user tapped the first at 00:12:22. The message said that
    without the criterion the recommendation would be the second;
  - **18, the inference endpoint** (00:18:36): "Nenhum, fica só no Sandbox", "Incremento nos três
    ambientes" (recommended), "Incremento só no dev", "Sempre ligado, como no exemplo"; the user tapped
    the second at 00:29:03;
  - **19, an ML pipeline** (00:31:15): "Nenhum, fica só no Sandbox", "Incremento nos três ambientes"
    (recommended), "Incremento só no dev"; the user tapped the second at 01:11:27. The message said that
    without the criterion the recommendation would be the first;
  - **20, Feature Store** (01:14:24): "Nenhum, fica só no Sandbox" (recommended), "Incremento nos três
    ambientes", "Incremento só no dev"; the user tapped the first at 01:22:41;
  - **21, what crosses the gate for a model** (01:23:32): "Só o código que treina", "Só o modelo, como no
    exemplo", "Código agora, modelo depois" (recommended). The message said that without the criterion
    the recommendation would be the first. The user answered in words at 01:28:21, the next entry's first
    bullet, and the card was closed at 01:33:34 on the second option, as answered in the conversation: a
    note of the user's words and not a tap.
- **[Claude] AWS's `ml/training` example** (the CI/CD CLI's repository at `main`, the raw files at
  23:55): one task, a notebook run by `SageMakerNotebookOperator`, whose parameters name an MLflow
  tracking server through the connection `mlflow-server`, the instance `ml.m5.large` and the scikit-learn
  container `1.2-1`. The notebook trains with the SageMaker SDK's `SKLearn` estimator, writes the model
  under `ml/output/model-artifacts/` in the project's shared location and copies it to
  `ml/output/model-artifacts/latest/output/model.tar.gz`. The training script registers the model from
  the run itself, through MLflow (`mlflow.sklearn.log_model` with a registered model's name), and the
  example's test asserts a fresh model file and a model package whose status is `Completed`. The manifest
  holds the stages `dev` and `test`, and no `prod`.
- **[Claude] AWS's `ml/deployment` example** (the raw files at 00:13, read again at 00:50). The
  manifest's storage item `model-artifacts` names the connection `default.s3_shared` and includes
  `ml/output/model-artifacts`, so `bundle` reads the trained model from the `dev` project; the stages are
  `dev`, `test` and `prod`, and `test` and `prod` run the workflow. Its one task, a notebook with
  `retries: 1`, reads the model at `ml/bundle/model-artifacts/latest/output/model.tar.gz`, the bundle's
  copy, deletes the endpoints earlier runs left, deploys an endpoint on `ml.m5.large` and calls it. It
  deletes nothing at its end, so an endpoint stands from one run to the next. The reading of 00:13 had
  the task with no retry and the model read from the stage's own `ml/output/`; the reading of 00:50, from
  the saved files, corrected both. Together: AWS's examples train in `dev`, and in `test` under the
  training example's own manifest, and what `test` and `prod` serve is `dev`'s model, carried by the
  bundle. No example trains in `prod`.
- **[Claude] An account-level enforced guardrail, found while decision 24 (b)'s task was written** (the
  SDK's model and AWS's page at 00:04, the page whole again at about 00:25, 24,611 characters). botocore
  1.43.1 and 1.44.4 hold `PutEnforcedGuardrailConfiguration`, `ListEnforcedGuardrailsConfiguration` and
  `DeleteEnforcedGuardrailConfiguration`: a configuration names a guardrail and a numbered version, two
  content controls, each `SELECTIVE` or `COMPREHENSIVE`, and the models it applies to, all of them when
  none is named. The page: *"Account-level enforcement – Designate a particular version of a guardrail
  within an AWS account for all Amazon Bedrock model invocations from that account."*; where a request
  names a guardrail too, *"The net effect is a union of all guardrails, with the most restrictive control
  taking precedence."*; *"Charges apply to each enforced guardrail according to its configured
  safeguards"*; the organization's form is an Organizations policy of the type `BEDROCK_POLICY`. The page
  names no IAM action for the configuration and no agent, knowledge base, flow or AgentCore. Two other
  names tried for the page returned a client error. A new decision, 27, was announced to the user at
  00:12 for the end of the round.
- **[Claude] Read for decisions 18 to 20**:
  - botocore 1.43.1's SageMaker model (00:52): `CreatePipeline` takes a definition or its S3 location and
    requires a role and a client token; `StartPipelineExecution` takes the pipeline's parameters;
    `CreateFeatureGroup` takes an offline store's S3 location, `DisableGlueTableCreation` and a role, and
    the Feature Store runtime's `PutRecord` takes `TargetStores`;
  - the developer guide's page on the offline store (00:58, two fetches that agree): *"When you call
    `PutRecord`, your data is buffered, batched, and written into Amazon S3 within 15 minutes."*;
    *"Feature Store only supports the Parquet file format when writing your data to your offline
    store."*;
  - the provider's `SageMakerStartPipelineOperator`, at both tags: `wait_for_completion` is false by
    default, and the task then returns the execution's ARN without waiting (`SUP-372`);
  - the CLI's README marks *"Feature Store (future)"*, and neither the provider's operators nor the
    service's list holds a Feature Store operator.
- **[Claude] The lint's `manifest` rule, told to the user at 01:25:42 with decision 21's card open**:
  `awsds-workflows` at `196acee` refuses a storage item that names a connection (*"content.storage
  <name>: com connectionName, o bundle lê o projeto, e não a pasta ao lado do manifest"*), so a model
  file read from the `dev` project needs an exception in the rule, and the release records the file's
  hash. The recommendation did not change.
- **[Claude] Written during the round**: each answer went into the stage file's decision as it came. A
  decision's letters follow its card's order, the first label being (a).

## 2026-11-17 — a trained model promoted: Stage 10 decision 22 revised and pass 9 rewritten, with no AWS call

*The same sitting, from 01:28 UTC on, with no AWS call. Times are UTC. The branch was rebased twice at
the user's word, before any pull request existed; nothing was merged.*

- **[user] The trained model is promoted**, at 01:28:21, with decision 21's card open: *"Revisite o
  plano, incluindo a decisão 22 do stage 10, replicando o exemplo da AWS. A decisão 22 do stage 10 foi
  tomada num contexto em que cada ambiente seria completamente isolado, mas hoje sabemos que todos os
  ambientes têm acesso aos dados governados, logo faz sentido treinar o modelo e promover para produção o
  modelo treinado."* **[Claude]** took decision 21 as (b) from those words, against the card's
  recommendation, and Stage 10 decision 22 as revised by them, and closed the card at 01:33:34.
- **[Claude] The premise, read in the repository.** Every consumer account reads the lake's `public` and
  `internal` tables of the `raw` and `curated` layers through one share, and a `restricted` or `personal`
  table reaches a principal by an explicit grant alone (`GOVERNANCE.md`'s grant rules); *"The governed
  lake is the same table in every stage."* (`sagemaker-application.md` §K); Staging tests against the
  lake, read in place (Stage 9 decision 3). A Sandbox project reads a governed table once a subscription
  is fulfilled for it. The premise holds with those limits, and Stage 9 decision 1 stands: the archive
  travels from `dev` upward, and Staging reads nothing of Production's outputs.
- **[Claude] Read for the new shape** (01:43 to 01:56):
  - the CI/CD CLI 1.0.9's released wheel, from PyPI (`commands/bundle.py`, `commands/deploy.py`,
    `helpers/deployment.py`, `helpers/bundle_storage.py`): `bundle` reads a storage item that names a
    connection from the stage's project, as its caller, through the `aws` CLI, and neither `bundle` nor
    `deploy` fails where the item is missing (`SUP-374`);
  - AWS's two ML manifests again, at `main`: `ml/training` gives `dev` no deployment configuration and
    creates its MLflow connection in `test`; `ml/deployment` writes the `model-artifacts` item to
    `ml/bundle/model-artifacts` in `test` and in `prod`, and names no MLflow connection;
  - the XGBoost container's `serve_utils.py`, at `master` of `aws/sagemaker-xgboost-container`:
    `get_loaded_booster` tries `pkl.load` on the model file first and `Booster.load_model` after it, so a
    served archive is unpickled. The copy inside the `3.0-5` image was not read;
  - the developer guide's page on network isolation, read twice: *"When you enable network isolation,
    your training and inference containers can't make any outbound network calls to any service,
    including Amazon S3."*; *"No AWS credentials are made available to the container runtime
    environment."*; *"SageMaker AI still handles all necessary Amazon S3 download and upload operations
    using your SageMaker AI execution role."*;
  - botocore 1.43.1's SageMaker model: a model package created in a group takes no tag (*"In this case,
    you cannot supply a tag argument."*), a container definition carries `ModelDataETag`, and
    `UpdateModelPackage` takes no description, so a version's description is written once.
- **[Claude] Pass 9 rewritten** in the shape of AWS's examples. `app-ml-train` runs in the `dev` project
  alone and ends by publishing its model as the release's candidate; the bundle carries the archive, a
  storage item on the connection `default.s3_shared`; `app-ml-register` and `app-ml-score` run in every
  stage; a target's version is approved by its deploy role, Production's in a job a deployment manager
  runs. The pipeline trains nothing. Added by Claude, and in no example of AWS's: `model.json` beside the
  archive, with the archive's SHA-256, and the mark `TRAINING_SOURCE`, which a guard of the pipeline
  compares with the tag's training code and sample. Decisions 16 to 19, taken while every stage trained,
  each say what 21 (b) leaves of them. Decision 17 (a) was tapped for an MLflow App in the three
  environments, and the plan tracks in `dev` alone, since no target trains: an app in a target is the
  user's to ask.
- **[Claude] The decisions that hold what crosses the gate, amended in place**: Stage 10 decision 22
  carries the user's words and the revision; D17, D20 and D28 each gained an amendment paragraph and a
  line in `decisions/INDEX.md`, and `history.md` an entry. Each says it is planned, with nothing applied.
- **[user] A rebase asked of every running session**, in the project's chat at 02:21:30: *"Avise as
  sessões em andamento para fazer rebase em relação à main"*. **[Claude]** rebased the branch, pushed and
  with no pull request, onto `main` at `bcda72a` (PR #308), with no conflict, and pushed it with a lease
  on its own tip, at 02:25. PR #308's retirement of release T's path was read for decision 28:
  Production's half of `app-etl`'s model chain has not run under release F.
- **[Claude] The plan reported at 02:44:41, and three more cards, with [user] the answers**:
  - **28, `app-etl`'s model chain** (02:44:53): "Aposentar depois da app-ml" (recommended), "Converter
    para o formato novo", "Deixar como está"; the user tapped the first at 02:47:28. Step 9.11, the
    retirement's plan, was written after the answer;
  - **19 again, where the ML pipeline runs** now that no target trains (02:51:15): "Só no projeto dev"
    (recommended), "Nos três ambientes, na pontuação", "Nenhum pipeline na app-ml"; the user tapped the
    first at 02:52:28;
  - **27, an account-level guardrail in each target** (02:52:55): "Um guardrail em cada conta"
    (recommended), "Nenhum", "Um só, pela organização"; the user tapped the first at 02:53:01. The card
    said the recommendation was Claude's own, AWS documenting the enforcement and recommending nothing on
    it.
- **[user] A second rebase**, in the thread at 03:23:35: *"Faça rebase em relação à main."* **[Claude]**
  rebased onto `main` at `97939ba` (PR #309, Stage 20) at 03:25, with one conflict, in
  `docs/plan/history.md`, where both branches had added an entry: both were kept, in date order.
- **[Claude] The plan read against Stage 20 decision 13** (taken 2026-11-16, its pass 4 unapplied), which
  takes `sagemaker:CreateProcessingJob` out of `DenySageMakerJobsWithoutNetworkIsolation` in Sandbox,
  Staging and Production. `app-ml`'s processing jobs keep `EnableNetworkIsolation: true` by their own
  request, a training job and a model stay under the statement, and a risk names the boundary and the
  slices passes 9 and 10 share with that stage's pass 4.
- **[Claude] AgentCore's rates, from AWS's price list** (03:34 to 03:35: the public offer file
  `AmazonBedrockAgentCore` for `us-west-2`, version `20261113204112`, published `2026-11-13T20:41:12Z`,
  922 products, read with no credential). Runtime's consumption-based rows are 0.0895 USD per vCPU-hour
  and 0.00945 USD per GB-hour, the pricing page's figures, and 0.1276 and 0.0169 for the usage types that
  end in `-v2`. The offer holds no row for a runtime that exists with no session. `PRICING.md` holds the
  table.
- **[Claude] `SUP-372` corrected while this log was written** (about 04:00). The entry said
  `SageMakerStartPipelineOperator` polls. In the provider's code at both tags `wait_for_completion` is
  false by default, and the task then returns the execution's ARN without waiting, as the stage file and
  the runbook already said.
- **[Claude] Written**, in one pull request: the stage file (the menu table, steps 0.9 and 6.4, passes 9
  and 10, decisions 14 to 28, their verifications, costs and risks); the runbook
  [`sagemaker-ai-ml.md`](../plan/runbooks/sagemaker-ai-ml.md); Stage 10 decision 22 and that stage's log;
  D17, D20 and D28 with `decisions/INDEX.md` and `history.md`; `AWS_SUPPLEMENT.md` (`SUP-372`, `SUP-373`
  and `SUP-374`); `PRICING.md`; `REFERENCES.md`; `waiting-on-the-user.md`; the stage index, the log
  index, `GENERAL_PLAN.md`'s route and `CLAUDE.md`'s rows. No `TM`, `EXC` or `INT` id was taken: the
  amendment of `INT-25` and the threat-model entry for a model archive that travels from a Sandbox
  project into Production's serving container are step 9.5's, before the first tag. Read and left as it
  is, Stage 19's subject: `sagemaker-application.md` §M says a manifest holds no `catalog` content, and
  `examples/app-etl/manifest.yaml` has held `content.catalog` since that stage's releases. Nothing in AWS
  changed.

## 2026-11-17 — passes 9 and 10 read against the estate, with nothing up

Read by a subagent of the plan's review session as the infrastructure user, read-only, and checked by
that session where marked. Nothing was applied.

- **[Claude, a subagent] Two blockers**: the deploy roles' `state` policies name no `studio` key (Staging:
  `foundation`, `sagemaker`, `data`, `egress`; Production: `workloads`, `foundation`, `sagemaker`, `data`,
  `workloads-egress`; `get-role-policy`), so pass 10's `MODEL_ID` read from `<env>/studio/` stops; and
  `sandbox/workflows/` and `sandbox/bedrock/` read each listed role with `data "aws_iam_role"`, while
  Sandbox holds three `datazone_usr_role_*` roles, all of existing projects, so 9.5 and 10.4 plan after
  the projects are created.
- **[Claude, a subagent] MLflow**: `describe-mlflow-app` on `ml-demo-mlflow` reads version 3.16.0,
  `LastModified` 2026-11-15T13:53Z, `MaintenanceStatus` `MAINTENANCE_COMPLETE`, `ModelRegistrationMode`
  `AutoModelRegistrationDisabled`.
- **[Claude] The registry as `deploy-production`'s project role**, simulated with the role's tags and
  the Region: `UpdateModelPackage` and `DescribeModelPackage` on a version `implicitDeny` without the
  `AmazonDataZoneProject` tag and `allowed` with it, by `SageMakerStudioProjectRoleMachineLearningPolicy`;
  `ListModelPackages`, `ListModelPackageGroups` and `DescribeModelPackageGroup` on the untagged group
  `allowed`. The subagent read the same in Staging, with `CreateModel` `allowed` under the project tag,
  a VPC and isolation, `DescribeTransformJob` on a free name `implicitDeny` and `bedrock:InvokeModel` on
  Nova Lite `explicitDeny` by `awsds-<env>-project-boundary`.
- **[Claude, a subagent] Policy sizes**, `get-policy-version` and `get-role-policy`: the deploy roles'
  inline `apply-application` 1,642 characters in Staging and 1,874 in Production, against 10,240 inline;
  `awsds-<env>-workflows` 1,681 and 1,854 of 6,144; the deploy roles' managed policy 5,060 and 5,045.
- **[Claude, a subagent] Quotas**, identical in the three accounts: `ml.t3.medium` processing 10;
  `ml.m5.large` training 20, transform 8, endpoint 30, processing 8 (Staging's processing value lost to
  a 408). Bedrock: Nova Lite holds cross-Region quotas alone (L-89F8391A 4,000 requests a minute,
  L-7C42E72A 8,000,000 tokens a minute) and no `us-west-2` on-demand one; Titan Text Embeddings V2 holds
  L-26C560CE (6,000); guardrails 100 per account (L-0E5A840C), 20 versions each (L-D471AEAB).
- **[Claude, a subagent] Bedrock**: Nova Lite `ACTIVE`, its availability `AVAILABLE`/`AUTHORIZED` in the
  three accounts; the retention mode `none` in Sandbox and `inherit` in both targets; the use-case form
  filled in Sandbox and `ResourceNotFoundException` in both targets; no guardrail and no enforced
  configuration; no application inference profile in the targets, Sandbox's Nova Lite profile serving
  `us-west-2` alone. Sandbox's `us-west-2` retention reads `updatedAt` 2026-09-12T15:32:02Z, read again
  by the review session, so `INV-18` gains that reading.
- **[Claude, a subagent] The registry and the start**: `awsds-prod-model-app-etl` alone exists, version 1
  `Approved` (2026-10-24), so 9.11's delete meets a version; `production/foundation/deploy-project.tf`
  grants `StartWorkflowRun` on every workflow tagged with the deployment project, so pass 9's start of
  `app-ml-register` needs nothing added.
- **[Claude] Written**: the stage file's tables and steps 9.1, 9.4 to 9.6, 10.2, 10.4 and 10.5 corrected
  with these readings, `sagemaker-ai-ml.md`'s MLflow version, `TM-30`, `INT-07` and `INT-25`. Nothing in
  AWS changed.

## 2026-11-17 — passes 9 and 10 advanced with nothing up: the work handed out, `TM-33`, the order of the sittings

*Claude's hand, in a laptop session on the infrastructure user's SSO session, at the user's request of
13:42 UTC to advance every step that needs neither the environment up nor the user's hands. No AWS write.*

- **[Claude] The work handed out**, 13:52 to 13:55 UTC, to subagents of this session in its worktree, each
  told to edit only its own paths and to run no git command that changes state: 9.2's `examples/app-ml/`,
  10.2's `examples/app-genai/`, the preflights 9.1 and 10.1 (read-only), and 9.5's target-side slices with
  10.4's pre-sitting change for Nova Lite, the last to a subagent in a worktree of its own, which commits
  there and pushes module tags alone. In progress at this entry; each result is a later entry.
- **[Claude] A refusal**, 13:55:03 UTC: the launch of the subagent whose brief held 9.3's and 10.3's lint
  rules with a push and a merge request in `awsds-workflows` was refused, *"Permission for this action was
  denied by the Claude Code auto mode classifier. Reason: [Unsanctioned Communication]."* It was launched
  again at 13:55:25 UTC to work in a clone in the session's scratchpad, committing there and writing the
  merge request's description and a patch series, with no push. Publishing is the user's.
- **[Claude] Written**, 14:05 to 14:09 UTC: `TM-33` in `threat-model.md`, the entry 9.5 asks for before the
  first tag, open until the user accepts it; 9.6 and 10.4 deliver the application to the space as a tar
  built before the sitting, as [Stage 20](../plan/stages/stage-20-dbt-lineage.md) step 2.0 does, so neither
  sitting raises GitLab; `promotion.md` §N.6 items 7, 8 and 10 to 14 placing 9.6, 10.4, 9.7, 10.5, 10.6 and
  9.11, and §N.5's line that 9.11's release of `app-etl` provokes Stage 8 xxvi, `app-etl-train` leaving
  `workflows/`.
- **[Claude] Kept out of this pull request**: `scripts/deploy-application.py`, `scripts/model-chain.py` and
  their hooks for a second application. Every job of `app-etl`'s pipeline clones `awsds/infrastructure` at
  its head (`examples/app-etl/.gitlab-ci.yml`, the `git clone` at line 318), so release G's legs, after the
  mirror's push at `main`, would run what a merge changes there. The change is §N.6 item 10, with nothing up,
  before 9.7's tag.
- **[Claude] 3.3 and `EXC-11`**, 14:22 UTC: from the day's review against SageMaker Unified Studio's standard
  path (6d's log), AWS's page on a SageMaker data source documents the share `EXC-11`'s error names, a RAM
  share of the domain to `sagemaker.amazonaws.com` with `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`,
  never created here. 3.3, `AWS_STATE.md`'s `EXC-11` and the waiting list carry it as the user's decision
  before 3.2 and 9.6.

## 2026-11-17 — 9.3 and 10.3: the lint's rules written in a local branch of `awsds-workflows`, unpublished

*A subagent of the laptop session wrote the rules in a clone of `awsds-workflows` in the session's
scratchpad, with no push and no AWS call; Claude copied the result to the laptop.*

- **[Claude, a subagent] The branch**, done at about 14:39 UTC: `claude/lint-transformacao-modelo-bedrock`,
  cut from `main` at `196acee`, HEAD `052521ea0f574b20e0ac30d3f635c12bc2a0fe0e`, two commits: `a13538a` (the
  code, the tests, the documentation and its references) and `052521e` (that repository's memory and its
  `CLAUDE.md`, whose index PR #24 had left behind).
- **[Claude, a subagent] The rules**: a new option, `--model-item ITEM`, on an application folder alone,
  under which the named storage item passes with `default.s3_shared` and an `include` naming a prefix,
  every other item with a connection still refused, so `app-ml`'s pipeline passes `--model-item model`;
  the rule `transformacao` (`action_if_job_exists` `fail`, the instance type on the list,
  `TransformResources.VolumeKmsKeyId` and `TransformOutput.KmsKeyId`); the rule `modelo` (`VpcConfig`'s
  subnets and security groups, `EnableNetworkIsolation` `true`, on a model's `config` or a transform's
  `Model`); and the rule `operador` refusing by name `SageMakerRegisterModelVersionOperator`,
  `SageMakerEndpointOperator`, `SageMakerEndpointConfigOperator`, `BedrockInvokeModelOperator`,
  `BedrockRaGOperator` and `BedrockRetrieveOperator`, each with its reason. Beyond the request: an item with a
  connection no longer counts as a folder of the tag, so the model's item cannot carry a workflow's code.
- **[Claude, a subagent] The tests**: 38 new cases, of which 31 fail on `196acee`'s code; the whole suite,
  with no `AWS_*` variable, 411 passed, 2 skipped and 7 failed, the 7 being `main`'s own (`prepare-offline`
  does not run on Darwin `arm64`); `ruff check` and `ruff format --check` clean. Copies of `app-etl` shaped
  as `app-ml` will be read `ok` with the option and refused without it, with a second connected item,
  without `VolumeKmsKeyId` and with a `BedrockInvokeModelOperator` task. Nothing was run on a worker, in a
  `bundle` or in a `deploy`.
- **[Claude] Kept**, 14:39 UTC: the branch as a git bundle (`196acee..` the branch), the patch series and
  the pull request's description in `$HOME/tmp/stage17-lint/`, since the scratchpad does not outlive the
  session. The push and the pull request are the user's, or Claude's on the user's word naming them (the
  waiting list); the new applications' pins stay at `196acee` until the merge.

## 2026-11-17 — 9.3 and 10.3: the lint's branch published, `awsds-workflows` pull request #26

*Written by Claude, on the user's word in chat: "Vc está autorizado a abrir um PR para o `awsds-workflows`
no que for necessário."*

- **[Claude] Read before publishing**: the branch's two commits (`a13538a`, `052521e`) against `origin/main`
  at `196acee`, which had not moved: `lint.py`, `cli.py`, their tests, `docs/` and the repository's memory.
  One defect: with no `--model-item`, the list of items bearing the asked name matched every item with no
  `name`, so a lone connection item without `name` took the model item's rules in place of the `manifest`
  refusal. Fixed in `adb5088` with a test, which fails at `052521e` and passes at `196acee` and `adb5088`.
- **[Claude] The checks at `adb5088`**: `uv run pytest -p no:cacheprovider` 412 passed, 2 skipped, 7 failed,
  the seven of `test_prepare_offline.py` and `test_examples.py::test_the_prepared_project_runs_extracted_elsewhere`,
  refused on the laptop (*"esta máquina é Darwin arm64, e a pasta só serve ao job preparada em Linux
  x86_64"*), the same seven as at `196acee`; `ruff check` and `ruff format --check` clean; `awsds-workflows
  --help` and the `pdoc` site exit 0.
- **[Claude] Published**, 15:00 UTC: the clone's HTTPS remote holds no credential helper, and the first push
  answered *"fatal: could not read Username for 'https://github.com': Device not configured"*; `git -c
  credential.helper= -c 'credential.helper=!gh auth git-credential' push -u origin
  claude/lint-transformacao-modelo-bedrock` pushed with the GitHub CLI's login for that command alone, and
  `gh pr create` opened <https://github.com/felipenoris/awsds-workflows/pull/26>, `MERGEABLE`, three checks
  pending. The description is the kept one with the fix and the counts at `adb5088`: 39 new cases, 31 of
  them failing at `196acee`.
- **[Claude] What waits**: the user's merge; then `AWSDS_WORKFLOWS` in `examples/app-ml/.gitlab-ci.yml` and
  `examples/app-genai/.gitlab-ci.yml` moves to the merge commit, and `app-ml`'s lint step gains
  `--model-item model`.

## 2026-11-17 — 9.1, 9.2, 9.4, 9.5, 10.1 and 10.2: the subagents' results, and the model-version denies

*Subagents' hands where marked, then Claude's, in the laptop session of the user's request of 13:42 UTC.
Every AWS call was a read, as the infrastructure user (`InfrastructureAccess`) through
`awsds-infra-sandbox-1`, `awsds-infra-staging` and `awsds-infra-prod`.*

- **[Claude, a subagent] 9.1**, 13:58 to 14:52 UTC.
  - Quotas, 14:13:40Z to 14:13:53Z, the same in the three accounts: `ml.t3.medium for processing job usage
    10.0`, `ml.m5.large for training job usage 20.0`, `ml.m5.large for transform job usage 8.0`,
    `ml.m5.large for endpoint usage 30.0`, against AWS's defaults 4.0, 0.0, 0.0 and 0.0; no request
    `CASE_OPENED` or `PENDING` in any account.
  - Sizes, 14:02:15Z, non-whitespace characters: `awsds-<env>-workflows` 1,681 (Staging), 2,074 (Production,
    since release G's apply of 13:11:54Z) and 986 (Sandbox) of 6,144; `awsds-<env>-deploy-project` 5,060 and
    5,045; the boundaries 3,474, 3,801 and 2,425; the deploy roles' inline policies 2,554 and 2,929 of
    10,240; the `Interactive` SCP 1,483 and the `Workloads` SCP 2,840 of 5,120.
  - Simulations as each target's project role (ML `SageMakerStudioProjectRoleMachineLearningPolicy` v48, UR
    `SageMakerStudioProjectUserRolePolicy` v77), 14:23:29Z and 14:23:54Z: the `AddTags` that comes with
    `CreateModel`, `CreateTransformJob` and `CreateModelPackageGroup` `implicitDeny`; `UpdateModelPackage` to
    `Approved` on a tagged version `allowed` by ML `SageMakerInferencePermissions`; `CreateTransformJob`
    `explicitDeny` from the simulator alone (`SUP-009`, appended). The bundle role holds none of the three
    reads on the stand-in's prefix (`app-etl-dev`'s). The deploy roles before 9.5: `ListModelPackages` on `*`
    `allowed` in Staging (`ListTheModelVersions`) and `implicitDeny` in Production, whose grant names
    `model-package/awsds-prod-model-app-etl/*`; the Service Reference v1.5 gives that action the type
    `model-package`, against `staging/foundation/deploy-role.tf`'s skip reason.
  - The CLI 1.0.9's wheel, SHA-256 `bd7258c0…4903`: verifications xxviii and lxii, read in the code; the
    scans' prefix is `SUP-287`'s.
- **[Claude, a subagent] 10.1**, the same session.
  - 49 on-demand text models, one list in the three accounts, `amazon.nova-lite-v1:0 ON_DEMAND,INFERENCE_PROFILE
    ACTIVE` among them. Nova Lite: *"ValidationException … Agreement not supported for this model"* and
    `AUTHORIZED` in each account; the form held in Sandbox, *"You have not filled out the request form."* in
    Staging and Production, Anthropic's prerequisite alone; the retention mode `none` in Sandbox and
    `inherit` in Staging and Production.
  - Quotas, the same in the three: `L-89F8391A` 4000.0, `L-7C42E72A` 8000000.0, `L-45E0AD92` 5760000000.0,
    `L-0E5A840C` 100.0 and `L-D471AEAB` 20.0, ApplyGuardrail 100 a second; no on-demand quota for Nova Lite.
  - `list-guardrails` `[]` and `list-enforced-guardrails-configuration` `{"guardrailsConfig": []}` in the
    three; three application inference profiles in Sandbox, the portal's, none in the targets.
  - Under today's boundary all 29 Bedrock cases read `explicitDeny` by `DenyServicesNoProjectUsesHere`; AWS's
    policies alone admit the invoke on any profile tagged with the project (UR `BRInvokeAppProfile`) and no
    guardrail action but `ApplyGuardrail`. `InfrastructureAccess` holds the three enforced-configuration calls,
    neither deploy role does.
  - Providers at `staging/studio`'s lock: `aws` 6.69.1 holds `aws_bedrock_guardrail`, its version and
    `aws_bedrock_inference_profile` and no enforced configuration; `awscc` 1.106.0 holds
    `awscc_bedrock_enforced_guardrail_configuration`, CloudFormation's type `PUBLIC` and `LIVE` since
    2026-04-07 and not taggable. 10.5's table row and decision 27's reading follow.
  - `vpc-egress-v0.17.0`'s `bedrock-base` group and its exclusions (`bedrock-mantle` among them); some models
    answer in-Region only through `bedrock-mantle`, Claude Haiku 4.5 among them. `staging/egress` passes no
    `optional_service_groups`, as pass 10's table already provides for.
- **[Claude, a subagent] 9.2 and 9.4**, to 14:57 UTC: `examples/app-ml/`, 35 files; `uv run pytest` *"100
  passed in 3.14s"*; ruff clean; the identifier rule 0 findings. The lint at `196acee` exits 1 on the model
  item alone (*"manifest.yaml: manifest: content.storage model: com connectionName, o bundle lê o projeto, e
  não a pasta ao lado do manifest"*); at `052521e` with `--model-item model`, *"ok: 6 arquivo(s)"*. The
  train archive: 15,910,630 bytes, 58,159,460 unzipped, 42 distributions; the register and score archives
  12,030 bytes each; the host build's import of `mlflow` 3.16.0 and `sagemaker_mlflow` 0.5.0 exits 0, and
  `set_tracking_uri` on an app's ARN resolves `MlflowSageMakerStore`. The house image's lock reads `mlflow`
  3.17.2, not 9.4's 3.16.0 (corrected); `code/uv.lock` resolves boto3 1.43.123, which `package-task` leaves
  out. Its patches to `scripts/model-chain.py`, `deploy-application.py`, `.pre-commit-config.yaml` and
  `aws/cicd.py` are kept in `$HOME/tmp/stage17-proposals/` for `promotion.md` §N.6 item 10.
- **[Claude, a subagent] 10.2**, to 14:55 UTC: `examples/app-genai/`, 32 files; *"95 passed"*; ruff and the
  lint at the template's pin clean (*"ok: 3 arquivo(s)"*); at `052521e`, `lint probes/operator.yaml` refuses
  `BedrockInvokeModelOperator` by name, the probe outside the manifest on purpose. The archive: 8 files,
  15,715 bytes, built twice to the same bytes. The gates' pip-audit step fails on its empty runtime export
  (`set -eu; pinned="$(grep -c == req)"` rc 1), so 10.6 needs a gates tag. botocore 1.43.1's `Stubber` on
  `CreateGuardrail` admitted a 60-character name, a name off the pattern and the enum value `NOT_A_TYPE`,
  and refused a missing required member, so the tests walk the model themselves (`SUP-376`). Its `deploy-application.py`
  proposal is kept beside the others.
- **[Claude, a subagent in a worktree of its own] 9.5**, commit `c1ceff56`: `production/registry` (the
  repository, its lifecycle and its pull policy), `production/sagemaker` and `staging/sagemaker` (the
  groups), both foundations (`ApproveTheModelATaskRegisters`), both `chains/` (two machines, two `DISABLED`
  schedules), both `studio/` (the transform, model and registry statements) and `identity/sso`'s
  `ReadAndPullTheApplicationImages`. Twelve read-only plans, among them *"Plan: 12 to add, 1 to change, 0 to
  destroy."* for each `chains/` and *"3 to add"* for `production/registry`. After: `awsds-staging-workflows`
  3,364, `awsds-prod-workflows` 3,748, the deploy roles' inline `apply-application` 2,031 and 2,257. Its
  findings: `production/registry` applies before `identity/sso`; the project role's `CreateModelPackage` with
  `ModelApprovalStatus=Approved` read `allowed` in both targets; the `UpdateModelPackage` deny named
  `app-ml`'s versions alone; `production/runners` gives the build runner push on the new repository at the
  next `make gitlab-up`; 10.4's `(C)` not written, `probes.py`'s interactive deny row sampling Nova Lite.
- **[Claude] Folded in**, 15:08 to 15:25 UTC: the examples committed (`f444d146`, `c1efca61`) and the branch
  merged (`9dc27110`). `<env>/studio/workflows.tf` gains `DenyRegisteringAVersionNotPending`, a deny of
  `CreateModelPackage` on `model-package/*` under `StringNotEquals` `sagemaker:ModelApprovalStatus`
  `PendingManualApproval`, and `DenyApprovingAModelVersion` names `model-package/*` (Lesson 82). Both
  `studio/` slices planned from the merged tree, 15:14 and 15:15 UTC: *"Plan: 2 to add, 2 to change, 2 to
  destroy."* each, the workflows policy at 3,597 and 3,984 non-whitespace characters. `simulate-custom-policy`
  on the planned policy beside an allow of both actions on `*`, in each target: `CreateModelPackage` on
  `app-ml`'s group `explicitDeny` with `Approved` and with no status, `allowed` with `PendingManualApproval`;
  on another group with `Approved` `explicitDeny`; `UpdateModelPackage` on `app-ml`'s and on `app-etl`'s group
  `explicitDeny`. `staging/foundation`'s skip reason now says which ARN the service evaluates is unread. The
  copies in `$HOME/tmp/stage17-lint/` are superseded by pull request #26.

## 2026-11-17 — 9.3's and 10.3's pins moved, and 9.5 applied with Stage 20's 4.4

*Claude's hand, in the laptop session of the user's request of 13:42 UTC, on the user's message after
both merges: "Fiz o merge do #26 e #313. Pode mover os pints. Autorizo os applies do item 2." Every AWS
call ran as the infrastructure user (`InfrastructureAccess`) through `awsds-infra-identity`,
`awsds-infra-sandbox-1`, `awsds-infra-staging` and `awsds-infra-prod`. Nothing was up: no hub, no GitLab,
no `[E]` slice.*

- **The pins**, to 15:54 UTC. `awsds-workflows` pull request #26 merged at 15:48:39 UTC as
  `37cb5a6`. `app-ml`'s and `app-genai`'s `.gitlab-ci.yml` point `AWSDS_WORKFLOWS` at its archive, and
  `app-ml`'s lint passes `--model-item model`: *"ok: 6 arquivo(s)"*. `app-genai`'s lint reads *"ok: 3
  arquivo(s)"*, and `probes/operator.yaml` is refused by the rule `operador` at `37cb5a6` and passes at
  `196acee`. `app-etl` passes at both commits (*"ok: 9 arquivo(s)"*) and keeps `196acee` until its next
  release. `app-dbt`'s README, its simulation and Stage 20's URL moved to `37cb5a6` too.
- **The plans**, 15:54 to 16:00 UTC, Recipe A from a branch cut at `origin/main` `13581cd0` (pull request
  #313, merged 15:48:49 UTC), `-input=false`, each saved and read statement by statement before its
  apply. The foundations passed the project folder's `secrets/alerts.auto.tfvars`.

  | Slice | Plan | Applied (UTC) | What changed |
  |---|---|---|---|
  | `production/registry` | 3 to add | 16:00:08 | `awsds-prod-ecr-app-ml`, its pull policy (the same principals as `app-etl`'s) and its lifecycle |
  | `identity/sso` | 6 to change | 16:01:26 | the six persona sets (Stage 20 decision 13); `DataScientistProdAccess`'s `ReadAndPullTheApplicationImages` names the new repository |
  | `identity/org-policies` | 1 to change | 16:02:03 | the `Workloads` document (Stage 20's 4.4) |
  | `sandbox/sagemaker` | 1 to change | 16:07:18 | Sandbox's boundary (Stage 20's 4.4) |
  | `staging/studio` | 2 to add, 2 to change, 2 to destroy | 16:08:13 | `awsds-staging-workflows` replaced with its attachment, gaining 9.5's statements; the boundary |
  | `production/studio` | 2 to add, 2 to change, 2 to destroy | 16:09:05 | the same for `awsds-prod-workflows` |
  | `production/sagemaker` | 2 to add | 16:09:56 | the group `app-ml` and its policy `task_registers`: `ApproveAsTheProductionDeployRole` and `ReadTheStatusFromSandbox` |
  | `staging/sagemaker` | 1 to add | 16:10:22 | the group `app-ml` |
  | `staging/foundation` | 1 to change | 16:10:54 | `ApproveTheModelATaskRegisters` |
  | `production/foundation` | 1 to change | 16:11:19 | the same |
  | `staging/chains` | 12 to add, 1 to change | 16:12:03 | `app-ml-register` and `app-ml-score`: machines, schedules, failure rules and targets; the chain role |
  | `production/chains` | 12 to add, 1 to change | 16:12:31 | the same |

  Each apply was followed by a re-plan: *"No changes."* on all twelve. Each `studio/` apply reports *"2
  added, 1 changed, 2 destroyed"*: the plan's second change, the person-session policy, was known only
  after apply because `data.aws_s3_bucket.projects` depends on the module, and its document read
  identical before and after in both targets.
- **The readings after.** The four new schedules read `DISABLED`: `awsds-staging-chain-app-ml-register`
  and `-app-ml-score`, created 16:11:59 UTC, and `awsds-prod-chain-app-ml-register` and `-app-ml-score`,
  created 16:12:28 UTC, at `cron(0 8 * * ? *)` and `cron(30 8 * * ? *)` UTC. `make check` reads *"check:
  OK"* (16:06 UTC). The battery and `DT-11` are Stage 20's log.
- **`TM-30`'s amendment** was owed before the `studio/` applies and was written after them: its clause on
  the project role now names `CreateModelPackage` with any status beside `DescribeModelPackage` and
  `UpdateModelPackage`, each read `allowed` by `SageMakerStudioProjectRoleMachineLearningPolicy` on
  2026-11-17, and the denies `<env>/studio/workflows.tf` applies since 16:08 UTC in Staging and 16:09 UTC
  in Production.
- **Left for the user**: `TM-33`'s acceptance before `app-ml`'s first tag; the projects `app-ml-dev` and
  `app-genai-dev` (9.6 and 10.4's sittings); `production/runners` gives the build runner push on
  `awsds-prod-ecr-app-ml` at the next `make gitlab-up`.

## 2026-11-17 — `TM-33` accepted by the user, on the condition that the path is AWS's

*The user's words, then Claude's readings by subagents fetching public pages, in the laptop session of
the user's request of 13:42 UTC. No AWS call.*

- **[the user]**, after Claude described `TM-33`'s context in chat: *"Desde que este caminho seja o
  sugerido pela AWS, podemos aceitar"*.
- **[Claude] The condition read**, the same day:
  - The CI/CD CLI's `ml/deployment` example, at `main`: its manifest declares `dev`, `test` and `prod`;
    the storage item `model-artifacts` names `default.s3_shared` and includes
    `ml/output/model-artifacts`, which `test` and `prod` write to `ml/bundle/model-artifacts`; `dev`
    holds no deployment configuration. Its `inference.py` loads the model with
    `joblib.load(os.path.join(model_dir, 'model.joblib'))`, and `ml/training`'s script saves it with
    `joblib.dump`.
  - joblib's `load` docstring (`numpy_pickle.py` at `main`): it relies on the pickle module and can
    execute arbitrary Python code. AWS's own example therefore loads, in its `test` and `prod` serving
    container, an archive the `dev` project wrote, which is `TM-33`'s channel. The persistence page of
    joblib's documentation answered 404 at `stable` and `latest`.
  - SageMaker AI's project templates register the models in the Model Registry and hold a manual
    approval step between the staging and production build steps; the registry's page says
    `PendingManualApproval` to `Approved` initiates the CI/CD deployment of the approved version. Neither
    page says in words that one version reaches both stages.
  - Where this plan departs from the examples: `ml/training` also trains in its `test` stage, which
    decision 21 lists as *Not built, and the user's to ask*. What it adds: the bundle's hash, Staging's
    scoring, the approval of the release's hash alone, registration as `PendingManualApproval` only,
    and a network-isolated model.
- **[Claude] Recorded**: `TM-33` accepted, its condition a revision trigger; 9.5's threat-model paragraph
  and the Status row; the waiting list's row; `promotion.md` §N.6 item 2; `CLAUDE.md`'s row; the pages in
  `REFERENCES.md`.

## 2026-11-17 — `EXC-11`'s share and decisions 7, 12, 10, 6 and 5 taken on cards, with no AWS call

*Claude's sitting in a cloud session of the user's Claude project, no AWS call: the review of the plan's
open decisions the user asked for at 22:01 UTC, one card per decision under the user's default of
21:50 UTC (the path AWS suggests), recorded by pull request #317. Times are UTC.*

- **[user] `EXC-11`'s share**, at 22:32, on the card *"Criar o compartilhamento RAM do domínio com o
  SageMaker que a AWS documenta?"*: *"Criar o share (caminho da AWS)"*. **[Claude]** The user's RAM
  write in Data Governance, before 3.2 and 9.6, joins the waiting list.
- **[user] Decision 7**, at 22:33, on the card *"Onde escrever as permissões que as medições do Stage 17
  pedirem?"*: *"Workflows em workflows/, resto em ml/"*, (a).
- **[user] Decision 12**, at 22:34, on the card *"Qual banco de vetores usar na base de conhecimento do
  Stage 17?"*: *"S3 Vectors"*, (a).
- **[user] Decision 10**, at 22:36, on the card *"Criar a entrada Function do portal, uma Lambda, no
  Sandbox?"*: *"Não criar até o controle existir"*, against the card's recommendation: the entry waits
  for Stage 11's deny on `lambda:CreateFunction` without `lambda:VpcIds`.
- **[user] Decision 6**, the endpoint's lifetime. At 22:39, on the first card: *"Pq esse endpoint não pode
  seguir o padrão dos outros (subir no make up e descer no make down)?"* **[Claude]** The create cannot
  ride `make up`: the scientist creates the endpoint in the notebook as the project role, and one created
  by Terraform would bill 0.115 USD an hour in every Sandbox session. The delete can ride `make down`, as
  `scripts/down-studio-apps.py` deletes the Studio apps people create; the card was withdrawn at 22:41
  and put again with that hook recommended. **[user]** At 22:42: *"Como no exemplo da AWS (fica)"*,
  against the recommendation. At 22:48: *"O usuário não consegue subir e descer o endpoint pelo SMUS
  conforme a necessidade?"* **[Claude]** Yes, by the SDK in the notebook (4.1's path) or by the portal's
  *Inference endpoints* page, unread (4.2); deleting is the only stop, and the model and the
  configuration bill nothing. **[user]** At 22:49: *"O próprio usuário pode apagar e refazer conforme a
  necessidade."* **[Claude]** Recorded with the user's words: 4.1's endpoint stays up after its sitting,
  its lifetime the member's, 2.76 USD a day while it stands, outside `make down` and `make status`.
  Owed before 4.1: `examples/sandbox-ml/serve.py endpoint` keeps what it creates instead of deleting it
  in its `finally`, and `aws/sandbox-ml.py`'s `ML-5` prints an endpoint with its price instead of
  failing on it.
- **[user] Decision 5**, at 22:51, on the card *"O que fica e o que é apagado ao fechar o Stage 17?"*:
  *"Manter tudo, endpoint incluso"*, against the card's recommendation: the close deletes nothing.

## 2026-11-18 — decision 6's code: `serve.py endpoint` keeps the endpoint, and `ML-5` prints its price

*Claude's sitting on the laptop with the environment down (`make status` read 0.0000 USD/h at 00:30),
the infrastructure user signed in, read-only AWS calls only, at the user's request of 2026-11-17 to
advance every stage but 11 to 15 with nothing up. Times are UTC.*

- **[Claude]** `examples/sandbox-ml/serve.py endpoint` keeps the model, the endpoint configuration and
  the endpoint after the run: its `finally` calls `keep()` in place of `delete_all()`, which prints each
  object as kept, the endpoint's price (0.115 USD an hour on `ml.m5.large`, 2.76 a day) and the two
  commands its member runs, `delete-endpoint`, and `create-endpoint` from the configuration that stays,
  with the project's tags. A `transform` or `serverless` run deletes what it creates, as before. The
  README's table and its paragraph on the run say the same.
- **[Claude]** `./aws/sandbox-ml.py`'s `ML-5` describes each endpoint and its configuration and notes
  the endpoint with its status, its age, each variant's instance type and count, and its price an hour
  and a day, in place of failing on it (4.6). `aws/INDEX.md`'s row and question follow. `ruff check` and
  `ruff format --check` pass; a synthetic endpoint printed the expected note.
- **[Claude]** The instrument's run at 00:45:51, with nothing up: every check passed, no call failed,
  `ML-5` read no endpoint; `ML-1` notes the managed ML policy at v48 on the three projects against the
  v45 the contract was read at, as before.

## 2026-11-18 — `promotion.md` §N.6 item 10: the deploy scripts taught `app-ml`, `app-genai` and `app-dbt`

*Claude, the orchestrating session and a subagent of it, on the laptop, no AWS call. Times are UTC.*

- **[Claude, a subagent] The 2026-11-17 proposals** in `$HOME/tmp/stage17-proposals/`, read with `git
  apply --check` against `4c441a6e`: `app-ml`'s four patches exit 0; `app-genai`'s
  `deploy-application.proposal.diff` refused on its `+++` path, which named another session's scratchpad,
  and exit 0 with `-p0` once that line named `scripts/deploy-application.py`. The two `deploy-application.py`
  proposals merged by hand with `app-dbt` added.
- **[Claude, a subagent] The change**, commit `bac717e8` on `claude/plano-estagios-execucao-5f64d8-n6-item10`:
  `deploy-application.py` names the applications in `APPLICATIONS` and fills a name only where the target
  stage reads it, `--image-uri` for `${JOB_IMAGE_URI}`, `sagemaker/`'s `training_image_uri`,
  `studio/`'s `<app>_inference_profile_arn`; `model-chain.py`'s `approve` by application and model hash,
  the group from `<account>/sagemaker`'s `model_package_group_arns`, `app-etl`'s `--package-arn` form
  unchanged; `aws/cicd.py`'s `APP_REPOS`, `app-etl`'s and `app-ml`'s repositories; the hook's pattern
  `examples/app-(etl|ml|genai|dbt)/`. `--self-check`: every stage of the four applications `ok`, `app-etl`'s
  two lines byte-identical to `main`'s; `model-chain.py --check` *"ok    the model chain's requests,
  offline"*; `make check` *"check: OK"*. Offline tests against doubles of the aws CLI and the CI/CD CLI,
  kept in the session's scratchpad: `app-etl`'s deploy and follow-up in both targets, every record the
  same as `main`'s script's; thirteen `approve` scenarios; five deliberate breaks of the self-check, each
  refused.
- **[Claude] Read again and published**: `--self-check` and `model-chain.py --check` exit 0 on the branch;
  the runbook's scripts row, the README's line and this stage's two rows of scripts written for the
  change (`b9699ee3`); the branch pushed and
  [pull request #321](https://github.com/felipenoris/AWS-DataScience/pull/321) opened as a draft, to merge
  after #320 and release G's sitting, before `app-dbt`'s mirror push and `app-ml`'s first tag.
- **[Claude] The pins read against the lint's release**, 16:26 UTC, from each application's folder with its
  pipeline's options at `awsds-workflows` `4613ddc`: `app-ml` *"ok: 6 arquivo(s)"*, `app-genai` *"ok: 3
  arquivo(s)"*, `app-etl` *"ok: 9 arquivo(s)"*, and `app-genai`'s `probes/operator.yaml` refused by
  `operador`, exit 1, as at `37cb5a6`. Between `37cb5a6` and `4613ddc` are #27 and #28.
- **[Claude] Left**: `aws/catalog.py`'s `CHAIN_DEV_PROJECTS` once `app-dbt-dev` exists; `app-genai`'s
  legs read `studio/`'s output, which 10.5 declares.

## 2026-11-19 — 9.6 and 10.4: `app-ml-dev` and `app-genai-dev` created, and their `sandbox/workflows/` lines planned

*The user created the projects in the portal. Claude, the orchestrating session, read them as the
infrastructure user through `awsds-infra-sandbox-1` and `awsds-infra-data`, reads only, and wrote and
planned the slice's lines. Times are UTC.*

- **[user] The act**: *"Criei os projetos"*, with Stage 20's `app-dbt-dev` (that log's entry of the same
  night).
- **[Claude] The projects**, read at 00:19 and 00:20: `app-ml-dev` (`5rzplmk81vma34`, created 00:17:46)
  and `app-genai-dev` (`b8fz4ovppjijv4`, 00:18:05), both `ACTIVE` under the `experimentation` profile
  (`dh60xbal05q64w`). Each holds `Tooling` and `SageMakerAIDomain`, both `ACTIVE` by 00:20:41:
  `app-ml-dev`'s `5ae0dd6m1suvbk` and `dpelnav9n8wyds`, `app-genai-dev`'s `c9sdti5d2gaqs0` and
  `5dg9rc3o9t070w`.
- **[Claude] The roles**: `datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk` and
  `datazone_usr_role_b8fz4ovppjijv4_c9sdti5d2gaqs0`, each carrying `awsds-sandbox-project-boundary` by
  `get-role`. `list-roles` read `None` for every role, `app-etl-dev`'s included, omitting the field by
  documented contract.
- **[Claude] The members**: each project's `list-project-memberships` holds the owner and one
  `PROJECT_CONTRIBUTOR`, a user profile of type `IAM` whose ARN is the project's own role, as `app-etl-dev`'s
  holds its role beside the two groups the user added there. The bundle role `awsds-deploy-sandbox-test`
  and Sandbox's `InfrastructureAccess` are members of neither project yet.
- **[Claude] The domains** (`./aws/studio.py`, ending 00:25:24): `US-13` passes on `d-hxxfi3od0xhm`
  (`app-ml-dev`) and `d-q1bianbhckrd` (`app-genai-dev`), each pinning `awsds-sandbox-dev-env` version 11 on
  both app types, and reads *"6 ACTIVE, each holding a SageMakerAIDomain domain"*. Neither project holds a
  `Tooling` domain, so 9.6's §C6 attach takes no step. The script's exit 1 is section 10's persona
  profiles with no SSO token, beside *"0 check(s) FAILED."*
- **[Claude] `sandbox/workflows/`**: both roles joined `project_roles` with `app-dbt-dev`'s (Stage 20 2.0),
  each with its comment line, and the slice was planned from this worktree at 00:29 as
  `awsds-infra-sandbox-1`: *"Plan: 3 to add, 0 to change, 0 to destroy."*, the three attachments of
  `awsds-sandbox-workflows`, the plan saved outside the repository. 9.5's pairs, model statement,
  `CreateModelPackage` and bundle role's read, and 10.4's `sandbox/bedrock/` and `sandbox/model-access/`
  changes are not written.
- **[Claude] Left**: the two contributors in each project, by the user in the portal's member dialog; the
  apply on the user's word; `app-ml-dev`'s MLflow App and model package group; Nova Lite enabled.

## 2026-11-19 — 9.5's `sandbox/workflows/` line applied for `app-ml-dev` and `app-genai-dev`

*Claude, the orchestrating session, on the user's word, as `awsds-infra-sandbox-1`. Times are UTC.*

- **[user] The authorization**: *"Autorizo o apply"*.
- **[Claude] The apply**: the saved plan of 00:29, one apply with Stage 20's `app-dbt-dev` line (that log's
  entry of the same night holds the readings): *"Apply complete! Resources: 3 added, 0 changed, 0
  destroyed."* at 00:49:48, re-planned *"No changes."* at 00:50:15. `app-ml-dev`'s and `app-genai-dev`'s
  roles list `awsds-sandbox-workflows`.
- **[Claude] Left**: 9.5's pairs, model statement, `CreateModelPackage` and bundle role's read; 10.4's
  `sandbox/bedrock/` and `sandbox/model-access/`; the two contributors in each project.

## 2026-11-19 — 9.6 and 10.4: the contributors added to `app-ml-dev` and `app-genai-dev`

*Claude, the orchestrating session, read the members the user added, reads only. Times are UTC.*

- **[user] The act**: *"Editei os três projetos adicionando os contributors solicitados. Pode verificar."*
- **[Claude] The members**, read at 00:54:50: each project lists the owner, its own role, the bundle role's
  group (`06d426f2-…`, `awsds-deploy-sandbox-test`) and Sandbox's `InfrastructureAccess` group
  (`839bcde8-…`), both `PROJECT_CONTRIBUTOR`, as `app-etl-dev` does (Stage 20's log of the same night holds
  the group profiles' readings).
- **[Claude] The workgroups**, by `list-connections` at 00:55:11, refused before the membership:
  `app-ml-dev`'s `workgroup-5rzplmk81vma34-5ae0dd6m1suvbk`, `app-genai-dev`'s
  `workgroup-b8fz4ovppjijv4-c9sdti5d2gaqs0`.
- **[Claude] Left**: `app-ml-dev`'s MLflow App and model package group (9.6); Nova Lite enabled (10.4);
  9.5's pairs and 10.4's `sandbox/bedrock/` and `sandbox/model-access/`.

## 2026-11-19 — 9.5 and 10.4: the rest of `sandbox/workflows/` and the Sandbox Bedrock slices written and planned, nothing applied

*Claude, a session started by the orchestrating session, wrote the code and planned it as the
infrastructure user through `awsds-infra-sandbox-1` and `awsds-infra-identity`: reads, plans and IAM
simulations only. Times are UTC.*

- **[Claude] What the roles hold today**, by `simulate-principal-policy` as each role, whose decision
  includes the organization's policies: `app-ml-dev`'s role is allowed `CreateModel`, `DescribeModel`,
  `DeleteModel` and `ListModels` on its tagged models, `CreateModelPackageGroup` with its tag and a tagged
  version, and refused the describe of a free job name, the tag of a job, of a model and of a group, and a
  version with no tag. `app-genai-dev`'s is allowed the invoke of its project's application profile and of
  Haiku 4.5's system profile, and `ApplyGuardrail` on a guardrail with its project's tag; Nova Lite's
  foundation model reads `explicitDeny` with `AllowedByOrganizations` `false`, the interactive OU's
  `NotResource` (02:01:43); every `guardrail` task's call reads `implicitDeny`. The bundle role is
  refused every read of the model's prefix and of the project key, and `PutObject` reads `explicitDeny`
  from its boundary. Both roles carry
  `EnableAmazonBedrockPermissions`, `EnableSageMakerMLWorkloadsPermissions` and
  `EnableGlueWorkloadsPermissions` `true` (`list-role-tags`, 01:57:33). The job creates' `explicitDeny`
  against a job's ARN with the volume key in the context is the simulator's (`SUP-009`): against `*` the
  same call read `allowed` at 01:31:16.
- **[Claude] `sandbox/workflows/`**: the transform pair, the model's tag and
  `RegisterAPendingVersionForAppMl` in the policy, the training pair behind `training_pair_enabled`
  (`false`), and the map `model_applications` naming `app-ml`'s role, its group `app-ml-dev` and its
  prefix `app-ml/models/latest`; in `deploy-role.tf`, the bundle role's `ListTheTrainedModelsPrefix`,
  `ReadTheTrainedModel` and `DecryptTheTrainedModelThroughS3`, the key read from the alias
  `alias/awsds-sandbox-project`, the same key as the role's `KmsKeyId` tag.
- **[Claude] `sandbox/bedrock/`**: `application.tf`, `awsds-sandbox-bedrock-application` on
  `application_roles` (`app-genai-dev`'s role), the deny behind `application_guardrail_required`, and the
  account's guardrail, its version and the enforced configuration behind `account_guardrail_enabled`, both
  `false`; `awscc` `~> 1.89` in `versions.tf`, its 1.106.0 block copied from `staging/studio`'s lock and
  accepted by `init` unchanged.
- **[Claude] `sandbox/model-access/`**: `amazon.nova-lite-v1:0` in `project_models`.
- **[Claude] `identity/org-policies/`**: the interactive OU's `NotResource` gains
  `arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-lite-v1:0`, the document 1,551 characters
  minified; its description and `POLICIES.md`'s row follow. The battery's deny row now invokes
  `us.amazon.nova-lite-v1:0`, `SYSTEM_DEFINED` and `ACTIVE`, routing to `us-east-1`, `us-west-2` and
  `us-east-2` (`get-inference-profile`, read 2026-11-19), and a new `ou` row invokes the model in
  `us-west-2` as `sandbox1`, expected to answer; `scp-battery.md` follows.
- **[Claude] The plans**, each with the tfvars regenerated and `-input=false`, saved outside the
  repository:

  | Slice | Profile | Time | Plan |
  |---|---|---|---|
  | `sandbox/workflows` | `awsds-infra-sandbox-1` | 01:45:48 | *"Plan: 0 to add, 2 to change, 0 to destroy."*: `awsds-sandbox-workflows` and the bundle role's `project-reads` |
  | `sandbox/workflows`, `-var training_pair_enabled=true`, a preview | `awsds-infra-sandbox-1` | 01:46:03 | the same count, the training pair added |
  | `sandbox/bedrock` | `awsds-infra-sandbox-1` | 01:46:38 | *"Plan: 2 to add, 0 to change, 0 to destroy."*: the policy and its attachment, the assistant's policy unchanged |
  | `sandbox/bedrock`, both variables `true`, a check | `awsds-infra-sandbox-1` | 01:47:17 | 5 to add: the guardrail, its version, the enforced configuration, the policy with the deny, the attachment |
  | `sandbox/model-access` | `awsds-infra-sandbox-1` | 01:46:49 | *"Plan: 0 to add, 1 to change, 0 to destroy."*: `model-management` gains Nova Lite's foundation model |
  | `identity/org-policies` | `awsds-infra-identity` | 01:48:10 | *"Plan: 0 to add, 1 to change, 0 to destroy."*: the interactive OU's document and its description, the description too long (below) |
  | `identity/org-policies`, again | `awsds-infra-identity` | 02:06:00 | *"Plan: 0 to add, 1 to change, 0 to destroy."*, the description at 508 characters |

- **[Claude] The planned documents simulated** (01:49:14 to 01:51:20) by `simulate-custom-policy`, with
  AWS's UR v77 and ML v48 under the live boundaries `awsds-sandbox-project-boundary` v3 and
  `awsds-sandbox-deploy-test-boundary` v2, the organization's policies outside the reading.
  `app-ml-dev`'s role: `DescribeTransformJob` on a free name, `AddTags` on a transform job and on a model,
  and `CreateModelPackage` `PendingManualApproval` with no tag on `model-package/app-ml-dev/new` `allowed`
  by the planned policy; an `Approved` version, a version in another group, `AddTags` on the group and,
  with the switch off, the training pair `implicitDeny`; with the switch on, the training pair `allowed`.
  `eighth-experimentation`'s role: a version in `app-ml-dev` `implicitDeny`. `app-genai-dev`'s role, with
  both variables `false` and `true` alike: `ListGuardrails`, `GetGuardrail`, `CreateGuardrail` with the
  tag, `UpdateGuardrail`, `CreateGuardrailVersion` and `TagResource` of the `awsds:` keys on a tagged
  guardrail `allowed`; the project key put on an untagged guardrail, `UpdateGuardrail` on one,
  `DeleteGuardrail` and `PutEnforcedGuardrailConfiguration` `implicitDeny`; an invoke naming a guardrail
  version `allowed`, Nova Lite's foundation-model pass through the profile included. An invoke naming
  none reads `allowed` with the deny off and `explicitDeny` with it on, through the application profile,
  on the foundation model, through Haiku 4.5's system profile and as a stream. With the deny off, UR v77's
  `ACInvoke` admits the invoke of every system profile and every foundation model on the role's tag. The
  bundle role: `ListBucket` on the prefix, `GetObject` under it and `Decrypt` through S3 `allowed`; the
  whole location, another project's prefix, `inbox/`, a direct `Decrypt` and `PutObject` `implicitDeny`.
- **[Claude] The description refused at commit**: pre-commit's tflint stopped the first commit on
  `aws_organizations_policy_invalid_description`, *"description must be 512 characters or less"*: the
  interactive OU's description, 502 characters before the change, read 608 with Nova Lite's clause, and
  the plan of 01:48 carried it, a value `UpdatePolicy` refuses. Shortened to 508 with every clause kept,
  and re-planned at 02:06.
- **[Claude] The sizes**, minified: the workflows policy 2,451 characters (3,146 with the training pair),
  the bundle role's `project-reads` 1,419, the application policy 1,162 (1,443 with the deny), the
  interactive SCP 1,551.
- **[Claude] Found**: 9.6's group `app-ml-dev` cannot be created with the project's tag from the space,
  `AddTags` on the group reading `implicitDeny` in both readings, and decision 7 (a) puts that statement in
  `sandbox/ml/`, unwritten. 9.6's first training run needs the training pair, so 2.2's (a) and (b) come
  before it in sitting B (`promotion.md` §N.6 item 7). `ACInvoke` reaches every system profile, where
  `sandbox/bedrock/main.tf`'s header records 6e 3.1's reading of 2026-09-11, none; the interactive OU's
  `NotResource` is the model ceiling either way.
- **[Claude] Left**: each apply on the user's word naming it, from `main` after the pull request,
  re-planned first; after the SCP's apply, the battery's `ou` phase and the same principal simulation of
  Nova Lite, expected `AllowedByOrganizations` `true`; Nova Lite enabled on the console's **Amazon
  Bedrock models** tab; the training pair in sitting B after 2.2's (a) and (b); the group's statement.

## 2026-11-19 — 3.3: `EXC-11`'s share written and planned as code, nothing applied

*Claude, a session started by the orchestrating session, which handed it the share at about 02:10. Reads
and a plan as the infrastructure user through `awsds-infra-data`. Times are UTC.*

- **[Claude] AWS's page on a SageMaker data source**, read again: for a unified domain, a RAM share of the
  domain to the service principal `sagemaker.amazonaws.com` under
  `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`, by the console's steps alone, the name
  `DataZone-<domain id>-SageMaker` its example. The page names neither `sources` nor associated accounts.
- **[Claude] The permission**, `ram get-permission` at 02:11: version 3, the default, `ATTACHABLE`, on
  `datazone:Domain`, with twenty DataZone actions, `CreateAsset`, `CreateDataSource`, `StartDataSourceRun`
  and `CreateListingChangeSet` among them. Its `creationTime` and `lastUpdatedTime` read the time of each
  call (`SUP-382`).
- **[Claude] RAM's pages**: `CreateResourceShare`'s `sources` constrains where a service principal's
  requests may come from, against a confused deputy, and RAM's table of shareable resources marks
  `datazone:Domain` as not shareable with a service principal, against AWS's page and the permission.
- **[Claude] Data Governance's shares**, at 02:13: nine `LakeFormation-V4`/`V5` shares and
  `DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY`, none to a service principal. No SCP names a
  `ram:` action. `list-permission-versions` at 02:15:31 read
  `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` versions 9 to 12 `UNATTACHABLE` and 13,
  of 2026-11-16, the default, with the domain's share at version 10; Claude told Stage 19's session, which
  moved the share on the user's word in its chat (Stage 19's log). Read here at 02:23:13: version 13,
  `ASSOCIATED`, updated 02:20:33, and still nine `LakeFormation` shares.
- **[Claude] The `Tooling` sources**, from Data Governance at 02:14: `test-experimentation`'s
  (`c8sn6a0xxc4zv4`, `cron(6 6 * * ? *)`), `eighth-experimentation`'s (`4tb4qnmgi0iej4`, `cron(32 17 * * ?
  *)`) and `app-etl-dev`'s (`apnukh5a1tfonk`, `cron(7 2 * * ? *)`), each `RUNNING` since its run of
  2026-11-18, the two runs before `FAILED` with `VALIDATION_EXCEPTION`, *"Failed to run the data source.
  Please check if RAM share is correctly configured between Amazon SageMaker and Amazon DataZone"*.
  `app-etl-dev`'s tracks `SageMakerModelPackageGroupAssetType` over an empty list, `publishOnImport`
  `false`, through a connection and no environment. `app-dbt-dev`, `app-ml-dev` and `app-genai-dev` hold no
  SageMaker data source.
- **[Claude] The code**: `data-governance/governance/sagemaker-share.tf`,
  `awscc_ram_resource_share.sagemaker`, `DataZone-dzd-d8yrvx1ko7im6o-SageMaker`, the domain's ARN, the
  principal, the permission, `sources` the four accounts of `local.member_account_ids`,
  `allow_external_principals` `false`, the five tags. A hand-made share would be `ManagedBy=console`
  outside Stage 2's table, and the `aws` provider's `aws_ram_resource_share` has no `sources`.
- **[Claude] The plan**, 02:20:19 to 02:20:51 as `awsds-infra-data`, saved outside the repository: *"Plan:
  1 to add, 0 to change, 0 to destroy."*, the share alone.
- **[Claude] Left**: the apply on the user's word naming it, whose wording answers whether RAM shares a
  domain with a service principal and with `allowExternalPrincipals` `false`; then the three sources' next
  runs.

## 2026-11-19 — decision 7 (a): `sandbox/ml/` written and planned with the model package group's statement, nothing applied

*Claude, a session started by the orchestrating session, on the user's answer in its chat, "Write it
before (Recommended)". Reads, a plan and IAM simulations as the infrastructure user through
`awsds-infra-sandbox-1`, and one project read through `awsds-infra-data`. Times are UTC.*

- **[Claude] The roles**, at 02:31: `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` and
  `datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk` carry `AmazonDataZoneProject` `avhvbqn37ty7m8` and
  `5rzplmk81vma34`, scope `dev`, blueprint `Tooling`, and the boundary `awsds-sandbox-project-boundary`;
  `datazone get-project` names the projects `eighth-experimentation` and `app-ml-dev`. The boundary, v3,
  holds no statement on a tag or a model package group.
- **[Claude] The gap**, by principal simulation as both roles, the organization's policies included
  (02:33:12): the tagged `CreateModelPackageGroup` reads `allowed` by
  `SageMakerStudioProjectRoleMachineLearningPolicy` v48's `SageMakerCreatePermissions`, the context
  carrying the caller's tag as `aws:ResourceTag/AmazonDataZoneProject`, and its `AddTags` reads
  `implicitDeny`, in both. The two readings before it were the simulator's: without `aws:RequestedRegion`
  both calls read `explicitDeny` with `AllowedByOrganizations` `false` (02:31:51, `SUP-008`), and without
  the principal tag `EnableSageMakerMLWorkloadsPermissions` the create read `implicitDeny` (02:32:09).
- **[Claude] `sandbox/ml/`**, rank 57, `[P]`: `awsds-sandbox-ml` with
  `TagAModelPackageGroupWithTheCallersProject`, `sagemaker:AddTags` on `model-package-group/*` of the key
  `AmazonDataZoneProject` alone, with the caller's own value, on a group that carries no project tag or
  already the caller's; one attachment per role of `project_roles`, the two above, each checked for the
  boundary; CostCenter `stage-17`; the lock copied from `sandbox/workflows/`'s and accepted by `init`
  unchanged. Registered in `scripts/tfhygiene/layers.py`: `./scripts/slices.py check` read 49 slices
  declared, 49 on disk.
- **[Claude] The plan**, at 02:36:01: *"Plan: 3 to add, 0 to change, 0 to destroy."*, the policy and the
  two attachments, saved outside the repository. The document is 504 characters minified.
- **[Claude] The planned document simulated**, added to each role's live policies by principal
  simulation (`SUP-370`'s refusal of a `file://` document was met first, and a file holding a JSON array
  of one string passed), the organization's policies and the boundary included, `AllowedByOrganizations`
  `true` in every row (02:37:39 to 02:37:54). As each role, its own value reads `allowed` on an untagged
  group and on a group already its own; another project's value, a group carrying another project's tag,
  and the project's key beside a second key (`Team`) read `implicitDeny`.
- **[Claude] Sandbox's model package groups**: none, `list-model-package-groups` at 02:39:54.
- **[Claude] Found**: a create that carries a second tag beside the project's is refused as `AddTags`,
  since the blueprint's tag statement admits no `AmazonDataZone*` key and this one that key alone. 9.6's
  and 3.2's creates carry the project's tag alone.
- **[Claude] Left**: the apply on the user's word naming it, from `main` after pull request #326 and
  re-planned first, before sitting B.

## 2026-11-19 — 9.5, 10.4, 3.3 and decision 7 (a): the slices applied from `main`, the SCP's apply refused to this session

*Claude, a session started by the orchestrating session, after the user merged pull request #326
(02:49:29 UTC, `40c9466c`) and wrote in its chat "Autorizo os applies necessários". Plans and applies as
the infrastructure user through `awsds-infra-sandbox-1`, `awsds-infra-identity` and `awsds-infra-data`.
Times are UTC.*

- **[Claude] The tree**: the worktree on `main` at `40c9466c`. Pull request #327, the other merge since the
  branch's last sync, touched documentation alone.
- **[Claude] The plans re-taken from `main`**, each compared by its planned changes (`terraform show
  -json`) with the branch's saved plan, identical in all six:

  | Slice | Profile | Time | Plan |
  |---|---|---|---|
  | `sandbox/workflows` | `awsds-infra-sandbox-1` | 02:52:26 | *"Plan: 0 to add, 2 to change, 0 to destroy."* |
  | `sandbox/bedrock` | `awsds-infra-sandbox-1` | 02:52:41 | *"Plan: 2 to add, 0 to change, 0 to destroy."* |
  | `sandbox/model-access` | `awsds-infra-sandbox-1` | 02:52:54 | *"Plan: 0 to add, 1 to change, 0 to destroy."* |
  | `sandbox/ml` | `awsds-infra-sandbox-1` | 02:53:10 | *"Plan: 3 to add, 0 to change, 0 to destroy."* |
  | `identity/org-policies` | `awsds-infra-identity` | 02:53:58 | *"Plan: 0 to add, 1 to change, 0 to destroy."* |
  | `data-governance/governance` | `awsds-infra-data` | 02:54:21 | *"Plan: 1 to add, 0 to change, 0 to destroy."* |

- **[Claude] The peers told** at about 02:55: the orchestrating session, Stage 19's, 6h decision 3's and
  Stage 20 8.3's.
- **[Claude] The Sandbox applies**, each from its saved plan, each re-planned *"No changes."* between
  02:57:15 and 02:57:45:

  | Slice | Start | Result |
  |---|---|---|
  | `sandbox/workflows` | 02:55:50 | *"Apply complete! Resources: 0 added, 2 changed, 0 destroyed."*: `awsds-sandbox-workflows` and the bundle role's `project-reads` |
  | `sandbox/bedrock` | 02:56:14 | *"Apply complete! Resources: 2 added, 0 changed, 0 destroyed."*: `awsds-sandbox-bedrock-application` and its attachment to `app-genai-dev`'s role |
  | `sandbox/model-access` | 02:56:37 | *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*: the provisioning role's `model-management` |
  | `sandbox/ml` | 02:56:58 | *"Apply complete! Resources: 3 added, 0 changed, 0 destroyed."*: `awsds-sandbox-ml` and its attachments to `eighth-experimentation`'s and `app-ml-dev`'s roles |

- **[Claude] The SCP's apply refused**: `identity/org-policies` from its saved plan was refused at about
  02:58 by the app's auto-mode classifier before it ran, *"[Protected-Scope IaC Apply]"*, the label
  `CLAUDE.md` records for an SCP apply in a started session on 2026-10-18. Nothing reached Organizations.
- **[Claude] Data Governance's shares before the share's apply** (03:01:51): nine `LakeFormation` shares
  and `DataZone-EXTENDED_ACCESS-dzd-d8yrvx1ko7im6o-ORG-ONLY`, each `ACTIVE`.
- **[Claude] The share's apply**: `data-governance/governance` as `awsds-infra-data` from its saved plan at
  03:02:25, *"awscc_ram_resource_share.sagemaker: Creation complete after 7s"* and *"Apply complete!
  Resources: 1 added, 0 changed, 0 destroyed."*, re-planned *"No changes."* at 03:03:26. Read at 03:03:00:
  - `DataZone-dzd-d8yrvx1ko7im6o-SageMaker`: `ACTIVE`, `allowExternalPrincipals` `false`, feature set
    `STANDARD`, five tags, created 03:02:35;
  - the principal `sagemaker.amazonaws.com`: `ASSOCIATED`, not external;
  - the domain: `ASSOCIATED`;
  - `AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain`, version 3, the default: `ASSOCIATED`;
  - four `SOURCE_ACCOUNT` associations, each `ASSOCIATED`.

  RAM's table of shareable resources says a domain cannot be shared with a service principal (`SUP-383`).
- **[Claude] The `Tooling` sources after it**, at 03:05:32, each source `RUNNING`. Each source's newest run
  read `RUNNING` and had started before the share:
  - `app-etl-dev`'s `apnukh5a1tfonk` at 02:19:45 that day;
  - `test-experimentation`'s `c8sn6a0xxc4zv4` on 2026-11-18 at 06:16:57;
  - `eighth-experimentation`'s `4tb4qnmgi0iej4` on 2026-11-18 at 17:38:11.

  The two runs before each had `FAILED` with `VALIDATION_EXCEPTION`.
- **[Claude] Left**:
  - `identity/org-policies`' apply, on the user's word naming it in this chat or by the user's own run of
    the saved plan `s17-main-identity-org-policies.tfplan`;
  - after it, `./aws/probes/scp-battery.py --phase ou` and Nova Lite's principal simulation, expected
    `AllowedByOrganizations` `true`;
  - the share's reading: whether the runs end and how the next scheduled ones end (verification v);
  - the training pair in sitting B.

## 2026-11-19 — 10.4: the interactive OU's SCP applied by the orchestrating session, the battery's `ou` phase

*Claude, the session that wrote 10.4, recording the orchestrating session's acts from the outputs it sent at
about 04:25 UTC, and reading them back. The orchestrating session ran each step on the user's words in its
own chat, "Autorizo SCP e bateria", which answered a question naming the SCP's apply and the battery's `ou`
phase. As the infrastructure user, permission set `InfrastructureAccess`. Times are UTC.*

- **[orchestrating session] The peers told** at about 04:20.
- **[orchestrating session] The plan**, 04:21:38 to 04:21:53, as `awsds-infra-identity` from its worktree
  at `main`'s `6c3cc62d` and one commit of documentation, the slice identical to `main`'s: *"Plan: 0 to add,
  1 to change, 0 to destroy."*. Its `terraform show -json` resource changes are byte-identical (`cmp`) to
  this session's plan of 02:53:58: `aws_organizations_policy.this["awsds-org-scp-ou-interactive"]`, one
  entry added to `DenyBedrockInvocationOutsideTheScopedModels`' `NotResource`,
  `arn:aws:bedrock:us-west-2::foundation-model/amazon.nova-lite-v1:0`, and the description;
  `DenyBedrockReadsOutsideTheRoutedRegions` unchanged.
- **[orchestrating session] The apply**, 04:22:32 to 04:22:42, from that saved plan:
  *"aws_organizations_policy.this["awsds-org-scp-ou-interactive"]: Modifications complete after 1s
  [id=p-tgda7n58]"* and *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*, re-planned *"No
  changes. Your infrastructure matches the configuration."* at 04:22:51.
- **[orchestrating session] The read-back** at 04:23:16, `organizations describe-policy`: four statements,
  nine entries in the deny's `NotResource`, Nova Lite's among them.
- **[orchestrating session] The battery**, `./aws/probes/scp-battery.py --phase ou`, 04:23:30 to 04:24:52,
  exit 0: *"54 as expected, 0 unexpected, 5 not measured"*, against 53, 0 and 5 on 2026-11-17. As
  `sandbox1`:
  - *"interactive (inherited): bedrock:InvokeModel on amazon.nova-lite-v1:0 in us-west-2 (Stage 17
    decision 23)"*: `ALLOWED`, succeeded, the new row;
  - *"bedrock:InvokeModel outside the scoped set (decision 15)"*, sampling `us.amazon.nova-lite-v1:0`:
    `DENY-SCP` `p-tgda7n58`;
  - Titan V2 and the three Claude 4.5 `us.` profiles: `ALLOWED`, succeeded;
  - `GetUseCaseForModelAccess` in `eu-west-1`: `DENY-SCP` `p-tgda7n58`.

  The five not measured are 2026-11-17's kinds: four Athena rows `DENY-NOT-SCP`, and Identity's
  `ec2:RunInstances` `UNTESTED`, *"no subnet in us-west-2"*. The report is
  `aws/output/scp-battery-20261119T012331.txt` in the orchestrating session's worktree, named and headed in
  local time (01:23:31, 04:23:31 UTC).
- **[orchestrating session] The simulation** at 04:24:17, `iam simulate-principal-policy` as
  `awsds-infra-sandbox-1`: `app-genai-dev`'s role `datazone_usr_role_b8fz4ovppjijv4_c9sdti5d2gaqs0`,
  `bedrock:InvokeModel` on Nova Lite's `us-west-2` foundation model, with `aws:RequestedRegion` `us-west-2`
  and `aws:PrincipalTag/EnableAmazonBedrockPermissions` `true`: `allowed`, `AllowedByOrganizations` `true`,
  `AllowedByPermissionsBoundary` `true`, the matched statement in AWS's `SageMakerStudioProjectUserRolePolicy`.
- **[Claude] The read-back from this session**:
  - `describe-policy` at 04:26:53: `awsds-org-scp-ou-interactive`, four statements, the deny's `NotResource`
    nine entries with Nova Lite's `us-west-2` ARN eighth, the document 1,551 characters, the description 508;
  - the same simulation at 04:26:55: Nova Lite `allowed`, `AllowedByOrganizations` `true`, through
    `SageMakerStudioProjectUserRolePolicy`; the negatives, Nova Pro's `us-west-2` foundation model and the
    system profile `us.amazon.nova-lite-v1:0`, `explicitDeny`, `AllowedByOrganizations` `false`;
  - `identity/org-policies` re-planned from this worktree at 04:27:05, the slice identical to `main`'s:
    *"No changes."*;
  - `./aws/org-policies.py`, 04:29:46 to 04:30:46, exit 0: *"wrote aws/output/org-policies.txt (all checks
    passed)"*.
- **[Claude] Left**: Nova Lite enabled on the console's Amazon Bedrock models tab (10.4), the user's; the
  training pair in sitting B; `EXC-11`'s reading.

## 2026-11-19 — 10.4: Nova Lite enabled in projects on the Bedrock models tab

*The user enabled the model in Sandbox's console, as the infrastructure user with `InfrastructureAccess` in
`Sandbox Account 1`, by the steps Claude gave in the session's chat, and wrote "Concluí a configuração do
Nova Lite pelo console". Claude's readings after it, as `awsds-infra-sandbox-1` and `awsds-infra-data`.
Times are UTC.*

- **[user] The enabling**: *Enable in projects* on Nova Lite's *On-demand* row of the *Manage* page, with
  the governance project in its selector, then *Submit*.
- **[Claude] The trail**: in Sandbox's and in Data Governance's trails in `us-west-2`, one each of
  `CreateEnvironment` at 13:02:38, `AssociateEnvironmentRole` at 13:02:39, `CreateAsset` at 13:02:41 and
  `CreateListingChangeSet` at 13:02:43, and no `CreateInferenceProfile` from 12:55. Sandbox's trail in
  `us-east-1` holds no `CreateRole`, `PutRolePolicy`, `AttachRolePolicy`, `CreatePolicy`,
  `CreatePolicyVersion`, `UpdateAssumeRolePolicy` or `CreateServiceLinkedRole` from 12:55 (read 13:11:43).
- **[Claude] The governance project** `GenerativeAIModelGovernanceProject` (`dmvami701qu6xc`), read at
  13:03:42:
  - a seventh environment, `amazon.datazone.BedrockModelEnvironmentType_3a043e363774` (`4o9mzknvmxhuhc`),
    `ACTIVE`, created at 13:02:38 in `Sandbox Account 1`;
  - a seventh asset, `amazon.nova-lite-v1:0us-west-2BedrockModelForm` (`4kvc963vx6zok0`), of
    `amazon.datazone.BedrockModelAssetType` revision 9, created at 13:02:41, its listing `cp58jn8lqdoknk`
    `ACTIVE`. Its `BedrockModelForm` reads `modelName` *Nova Lite*, `inferenceType` `ON_DEMAND`, input
    modalities text, image and video, `region` `us-west-2`, the environment above, and `managementRoleArn`
    the slice's `AmazonSageMakerBedrockModelManagementRole-<Data Governance Account>`. Its
    `SubscriptionTermsForm` reads `approvalRequired` `NO`.
- **[Claude] Sandbox**: the application inference profiles are the three read before: the playground's two
  of 2026-10-19 (Haiku 4.5 in three Regions, Nova Lite in `us-west-2`) and `eighth-experimentation`'s Opus
  4.5 of 2026-10-30. No project holds a Nova Lite profile before its first use. No role or customer-managed
  policy with *Bedrock* in its name is newer than `awsds-sandbox-bedrock-application` (02:56:22).
- **[Claude] The instruments**:
  - `./aws/catalog.py`, 13:04:30 to 13:07:24, *"all checks passed"*, `CT-2` reading 11 listings, all owned
    by a live project;
  - `./aws/studio.py`, 13:07:24 to 13:10:21, 50 pass, 6 notes and no failure among its checks. It exited 1
    because the persona, deploy and Control Tower profiles had no session (its section 10).
- **[Claude] Left**: `app-genai-dev`'s Nova Lite profile, read with `list-inference-profiles` at the
  project's first use in sitting C (10.4), expected in `us-west-2` alone.

## 2026-11-19 — 3.3 and verification v: `EXC-11`'s first run after the share

*Claude, a session started by the orchestrating session, on its brief of the afternoon, which authorizes
no write. Reads as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-data` (the
domain) and `awsds-infra-sandbox-1` (Sandbox's groups), from 15:01:12 to 15:02:19. Times are UTC.*

- **[Claude] The projects**: ten in the domain. The three created on 2026-11-19, `app-dbt-dev` (00:17:19),
  `app-ml-dev` (00:17:46) and `app-genai-dev` (00:18:05), each hold a `Tooling` and a `SageMakerAIDomain`
  environment, `ACTIVE`, and no data source. `GenerativeAIModelGovernanceProject` holds none either, and
  `governed-lake`, `deploy-staging` and `deploy-production` hold Glue sources alone.
- **[Claude] The `Tooling` sources**: `Tooling-default-sagemaker-modelpackagegroup-datasource` in three
  projects, each tracking `SageMakerModelPackageGroupAssetType` over an empty list:

  | Project | Source | Schedule | Runs | Newest run |
  |---|---|---|---|---|
  | `test-experimentation` | `c8sn6a0xxc4zv4`, `READY` | `cron(6 6 * * ? *)` | 35: 34 `FAILED`, 1 `SUCCESS` | `ajp1ym83139yxc`, from 06:16:57 to 06:17:18, `SUCCESS`, 0 added, updated, unchanged and failed |
  | `app-etl-dev` | `apnukh5a1tfonk`, `RUNNING` | `cron(7 2 * * ? *)` | 5: 4 `FAILED`, 1 `RUNNING` | `3nzznqq176x028`, started 02:19:45, before the share |
  | `eighth-experimentation` | `4tb4qnmgi0iej4`, `RUNNING` | `cron(32 17 * * ? *)` | 87: 86 `FAILED`, 1 `RUNNING` | `6fdkdu6arwynf4`, started 2026-11-18 at 17:38:11 |

- **[Claude] The run before the success**: `bq960tfeokvwcw`, started 2026-11-18 at 06:16:57, was marked
  `FAILED` at 06:16:57 on 2026-11-19 as its successor fired, with the wording of every failed run,
  *"Failed to run the data source. Please check if RAM share is correctly configured between Amazon
  SageMaker and Amazon DataZone"* (`VALIDATION_EXCEPTION`). The successful run lists no activity.
- **[Claude] The start times**: each source starts its run some ten minutes past its schedule's minute,
  06:16:57 for 06:06, 02:19:45 for 02:07 and 17:38:11 for 17:32.
- **[Claude] Sandbox's model package groups**: `list-model-package-groups` returned none, exit 0.
- **[Claude] The verdict so far**: the share removed the failure for the first run started after it,
  which succeeded with nothing to ingest. The two runs started before it still read `RUNNING`. The
  ingestion half of verification v waits on a model package group: 3.2's `ml-demo-xgboost` in
  `eighth-experimentation`, or 9.6's `app-ml-dev` in a project that holds no such source.
- **[Claude] Left**: `eighth-experimentation`'s run of about 17:38 today and `app-etl-dev`'s of about
  02:19 on 2026-11-20, read when the orchestrating session asks.

## 2026-11-19 — sittings B and C as one Sandbox sitting: the pre-flight readings, nothing up

*Claude, the same session, on the same brief. Reads and plans as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` and `awsds-infra-data`, from 15:07 to 15:27, the
plans from the branch at `0d5b573b`. No plan saved, nothing applied, nothing raised. Times are UTC.*

- **[Claude] `./aws/sandbox-ml.py`**, generated 15:07:37: 33 pass, no check failed, *"None. Every call in
  this report returned successfully."* `ML-1` notes the managed ML policy at v48 on every project; `ML-2`
  reads `ml-demo-mlflow` `Created` on MLflow 3.16.0, the version 9.4's archive pins, with
  `AutoModelRegistrationDisabled`.
- **[Claude] `sandbox/workflows/`**: *"No changes."* at 15:08:12; with `-var training_pair_enabled=true` at
  15:08:32, *"Plan: 0 to add, 1 to change, 0 to destroy."*, `aws_iam_policy.workflows` gaining
  `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject`, 9 statements. The
  slice's code is unchanged since its apply's tree, `40c9466c`, so 9.5's measurement stands: 3,146
  characters minified of 6,144.
- **[Claude] `sandbox/bedrock/`**: *"No changes."* at 15:14:55; with both switches `true` at 15:15:08,
  *"Plan: 3 to add, 1 to change, 0 to destroy."*: `aws_bedrock_guardrail.account[0]`,
  `aws_bedrock_guardrail_version.account[0]` and `awscc_bedrock_enforced_guardrail_configuration.account[0]`
  created, `aws_iam_policy.bedrock_application` updated in place.
- **[Claude] SageMaker's quotas**, applied values at 15:11:53, for the types 2.2 and the applications name:

  | Type | Training | Processing | Transform | Endpoint |
  |---|---|---|---|---|
  | `ml.m5.xlarge` | 20 | 8 | 4 | 30 |
  | `ml.m5.large` | 20 | 8 | 8 | 30 |
  | `ml.t3.medium` | | 10 | | |

- **[Claude] Bedrock's quotas for Nova Lite** at 15:10:07, applied equal to the defaults: *"Cross-region
  model inference requests per minute"* 4,000, *"Cross-region model inference tokens per minute"*
  8,000,000, and *"Model invocation max tokens per day"* 5,760,000,000, doubled for cross-region calls. No
  quota names an in-Region on-demand rate for the model, so 10.4's first invoke in `us-west-2` is that
  premise's reading.
- **[Claude] ML v48's MLflow statement**: `SageMakerMlflowServerlessPermission` grants `CreateMlflowApp`,
  `CreatePresignedMlflowAppUrl`, `DeleteMlflowApp`, `DescribeMlflowApp`, `UpdateMlflowApp` and
  `CallMlflowAppApi`.
- **[Claude] The profile of `app-ml-dev` and `app-genai-dev`**: both `experimentation` (`dh60xbal05q64w`),
  `ACTIVE` (15:27). Its `MLflowApp` configuration is `3342d20e-001b-4b95-9053-fbbc04b5c303`, blueprint
  `agjvpzxbha9fbk`, `ON_DEMAND`, with no parameter override (15:16:20), so 1.5's command serves
  `app-ml-dev` with its project id `5rzplmk81vma34`.
- **[Claude] What an MLflow App bills**: Sandbox's `Amazon SageMaker` costs by usage type from 2026-10-19
  to 2026-11-18 (Cost Explorer, 15:12:31) hold Studio's JupyterLab and volume lines, Unified Studio's,
  processing's and `DataAgentCredit`, and no MLflow line, while `ml-demo-mlflow` existed from its creation on 2026-10-19.
- **[Claude] The block**: the section "Sittings B and C as one Sandbox sitting" of the stage file, in the
  order its table gives, about seven hours under `GROUPS=mwaa,mlflow,bedrock-base`.
- **[Claude] Left before the sitting**: `app-ml-dev`'s MLflow App and 0.9's portal reading, the user's; the
  archives of `app-ml` and `app-genai` from `main` on the sitting's eve, Claude's.

## 2026-11-19 — sittings B and C's block: Stage 17's other Sandbox items placed, nothing up

*Claude, the same session, on the orchestrating session's addendum to its brief, which asks which of the
waiting list's Stage 17 Sandbox items ride the same raise. Reads of the repository at `0d5b573b` and of the
module tags, no AWS call. Times are UTC.*

- **[Claude] The items**: the waiting list's Sandbox row names 0.3, 0.5's interface half, 0.7, 7.4 to 7.4c
  and 7.6. The log holds no reading of any of them since 2026-10-18, which left 0.3 and 0.7 owed with a
  session and `ML-9`'s interface half on `make hub-up` and `make up ENV=sandbox`.
- **[Claude] The groups at `vpc-egress-v0.19.0`**, `sandbox/egress`'s pin: `bedrock-base` is `bedrock` and
  `bedrock-runtime`, `bedrock-agent` is `bedrock-agent` and `bedrock-agent-runtime`, `mwaa` is
  `airflow-serverless`. 7.1 raises `bedrock-agent` beside `bedrock-base` for pass 7, and 7.4b's `Retrieve`
  from the space takes `bedrock-agent-runtime`, so pass 7 needs the fourth group.
- **[Claude] The boundary**: `fenced_services` defaults to an empty list at `sagemaker-prereqs-v0.12.0`, and
  `sandbox/sagemaker/` passes none, so `DenyServicesNoProjectUsesHere` is absent and no service pass 7
  calls is fenced.
- **[Claude] The house lock**, `gitlab/awsds/dev-env/dev-env/python/uv.lock`, last changed at `a1c755b5` on
  2026-10-25, the day before `default-v0.10.0`'s build from GitLab's `c8bac16e`, a commit this repository
  does not hold: `boto3` 1.43.92, `mlflow` 3.17.2, `sagemaker` 3.21.0, `sagemaker-mlflow` 0.5.0, `pandas`
  2.3.3, `xgboost-cpu` 3.3.0, Python 3.12. `examples/sandbox-ml/README.md` names `mlflow` 3.16.0 and the
  rest as the lock does.
- **[Claude] Pass 7's inputs**: decisions 5, 10 and 12 taken 2026-11-17, as (everything kept), (a) and (a);
  `docs/plan/runbooks/*.md` holds 20 files and 1,162,979 bytes, against 7.4a's 16 files and 550 KB;
  `examples/sandbox-ml/bedrock/` holds its README alone, so 7.4's twenty-line evaluation dataset is
  unwritten.
- **[Claude] The block**: 0.5's interface half joins the session's opening; 0.3 and 0.7 come next,
  before any run; pass 7 follows 2.2 (c) and precedes 9.6, with `bedrock-agent` in the raise. About 9.6
  hours in all, some 2.50 USD of endpoints and hub. Pass 7 can move to a sitting of its own; 0.7 cannot,
  since the forms precede 2.2's job. No item waits on anything outside the sitting but 7.6's idle bill, which
  Cost Explorer shows after the sitting's day (8.2).

## 2026-11-19 — 7.4's evaluation dataset and 0.3's preparation, nothing up

*Claude, the same session, on the orchestrating session's follow-up, its first two items. AWS's and
MLflow's pages read through page-reading agents, MLflow installed on the laptop in throwaway `uv`
environments, no AWS call. Times are UTC.*

- **[Claude] The IDE's evaluation form**, read on AWS's pages (`docs/REFERENCES.md`): automatic
  evaluations alone, with no human-based form and no judge model; the metrics Toxicity, Accuracy and
  Robustness; the tasks General text generation, Text summarization, Question and answer and Text
  classification; up to 1000 prompts a job. A custom dataset is JSON lines, each line a `prompt`, a
  `referenceResponse` (required for question and answer, and for accuracy and robustness) and an optional
  `category`. The form uploads the file to a bucket the IDE manages or chooses one from S3.
- **[Claude] 7.4 corrected**: its "Haiku 4.5 as the evaluator" named a judge the IDE does not offer, so
  Haiku 4.5 is now the model evaluated. Bedrock's own judge list holds Haiku 4.5 and not Nova Lite v1.
  0.7 gains the form's dataset field: whether *Choose a dataset from S3* reaches `shared/ml-demo/bedrock/`,
  the upload taking the same file where it does not.
- **[Claude] The dataset**: `examples/sandbox-ml/bedrock/evaluation-dataset.jsonl`, twenty prompts of the
  task *Question and answer*, 2,951 bytes, each line the three keys, in five categories: Networking 7,
  AWS 5, Machine learning 4, Tooling 2, Data 2. Each reference is a short fact from this project's own
  vocabulary. `examples/sandbox-ml/evaluation_dataset.py` checks every line and copies the file to
  `shared/ml-demo/bedrock/` from the space; `ruff check` and `ruff format --check` pass.
- **[Claude] 0.3's preparation**: the lock's `mlflow` 3.17.2 depends on `mlflow-skinny` and
  `mlflow-tracing` 3.17.2. The scripts make ten MLflow calls: `set_tracking_uri`, `set_experiment`,
  `start_run`, `log_params`, `log_metric`, `set_tag`, `log_artifact`, `search_runs`, `register_model` and
  `xgboost.log_model`. Their signatures, printed by `inspect.signature` from `mlflow-skinny` 3.16.0 and
  3.17.2 on Python 3.12 at 16:30, are identical; `xgboost.log_model`'s second parameter is
  `artifact_path`, deprecated in both in favour of `name`. GitHub's release pages from 3.16.1 to 3.17.2
  remove or deprecate none of these calls, and v3.16.2 has no page.
- **[Claude] No script changed.** `examples/sandbox-ml/README.md` now names `mlflow` 3.17.2, the lock's
  version since `a1c755b5`, so 0.3 confirms the space's versions against it.

## 2026-11-19 — the combined sitting's block on `promotion.md` §N.9's days 2 and 3, nothing up

*Claude, the same session, on the orchestrating session's message after its commit `f3b87975` (pull request
#334, merged into this branch with `main` at `c11a9829`). No AWS call.*

- **[Claude] The block's days**: §N.9 runs the combined sitting on three days, and Stage 17's rows fill two.
  Day 2 raises `GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent` for sitting B to the end of pass 7, then
  Stage 21's pass 5. Day 3 raises `GROUPS=mwaa,mlflow,bedrock-base` for 6e 6.4's window alone, then 9.6
  and 10.4. Each day ends with `./aws/sandbox-ml.py`, `./aws/catalog.py` and §N.9.6's lowering.
- **[Claude] The section rewritten to match**: the opening paragraph names both days and their groups; the
  table gains a column for the day, a second closing and day 3's raise, 16 rows in all, about 4.9 hours of
  day 2 and 5.3 of day 3; the MLflow App comes before day 3, 0.9's reading before day 2 and the archives on
  day 3's eve. The hourly rates are §N.9.7's, 0.27 and 0.25 USD before the spaces; this section's earlier
  0.26 and 0.24 left out the VPN's address, which `docs/PRICING.md` counts as a floor line.

## 2026-11-19 — verification v: `eighth-experimentation`'s first run after the share

*Claude, the same session, on the orchestrating session's follow-up, its third item, after the user's
"Tente novamente" in that session's chat. Reads as the infrastructure user with `InfrastructureAccess`,
through `awsds-infra-data`, from 18:16:27 to 18:16:48. Times are UTC.*

- **[Claude] The wait**: the Monitor armed at 17:02:28 for 17:50 expired at 17:32 with no event, and the
  turn that would have armed it again ended on an API error (`ENOTFOUND`). The reading was taken at
  18:16, past the orchestrating session's 17:50.
- **[Claude] `eighth-experimentation`'s source** (`4tb4qnmgi0iej4`, `cron(32 17 * * ? *)`): 88 runs, 87
  `FAILED` and 1 `SUCCESS`. The new run `5lkcvfroqbjnyo`, `SCHEDULED`, ran from 17:38:11 to 17:38:19 and
  ended `SUCCESS`, 0 added, updated, unchanged and failed, with no activity. The source reads `READY`, its
  last run `SUCCESS` with 0 assets.
- **[Claude] The run before it**: `6fdkdu6arwynf4`, started 2026-11-18 at 17:38:11, was marked `FAILED` at
  17:38:11 as its successor fired, `VALIDATION_EXCEPTION`, with the wording of every failed run, *"Failed to
  run the data source. Please check if RAM share is correctly configured between Amazon SageMaker and
  Amazon DataZone"*.
- **[Claude] The verdict so far**: both sources that have run since the share succeeded with nothing to
  ingest. Left: `app-etl-dev`'s first run after the share, at about 02:19 on 2026-11-20, read from the
  record in a later session; the ingestion half still waits on a model package group (3.2's or 9.6's).

## 2026-11-20 — verification v: `app-etl-dev`'s first run after the share, and `EXC-11` closed

*Claude, the orchestrating session, with nothing up. Reads as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-data` (account Data Governance), from about 16:00 to 16:05;
`./aws/catalog.py` read through its own profiles. The record's one code change is in `aws/catalog.py`; no
AWS write. Times are UTC.*

- **[Claude] `app-etl-dev`'s `Tooling-default-sagemaker-modelpackagegroup-datasource`** (`apnukh5a1tfonk`,
  `cron(7 2 * * ? *)`): its first run after the share, `3wo565isiosnm8`, `SCHEDULED`, started at 02:19:45
  and ended `SUCCESS` at 02:19:55 on 2026-11-20; `added`, `updated`, `unchanged` and `failed` all 0, no
  activity, `lastRunAssetCount` 0; the source's first success in 6 runs. Its predecessor, started
  2026-11-19 at 02:19:45, was marked `FAILED`, `VALIDATION_EXCEPTION`, at 02:19:45 as it fired, and so were
  the four before it, the oldest started 2026-11-15.
- **[Claude] The other two sources' newest runs**: `test-experimentation`'s second run after the share,
  06:16:57 to 06:17:25, `SUCCESS`; `eighth-experimentation`'s newest is still the one of 2026-11-19 at
  17:38:11, `SUCCESS`, its next due at about 17:38.
- **[Claude] Verification v's failure half answered**: every source of the name ended its first run after
  the share `SUCCESS`, in three projects of Sandbox, an account associated with the domain. The ingestion
  half waits on 3.2's or 9.6's model package group.
- **[Claude] `EXC-11` closed**, as its row said this reading would: the row in `docs/AWS_STATE.md` struck
  and dated, `SUP-383` given the associated account's case, and `aws/catalog.py`'s `FAILING_BY_EXCEPTION`
  emptied, as its comment asks when the exception closes. `./aws/catalog.py` then answered *"all checks
  passed"*, its report written at 16:04:52: `CT-6` a note on the schedules nobody wrote (Lesson 17), the
  three Tooling sources at 34 `FAILED` and 2 `SUCCESS`, 87 and 1, and 5 and 1. A source whose every
  completed run fails now turns `CT-6` red.

## 2026-11-20 — Passes 4 and 5's creates simulated, and `sandbox/ml/`'s endpoint and pipeline statements planned

*Claude, in the session that regrouped the Sandbox days (Stage 8's log, this day), with nothing up. Reads
and plans as the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (account
Sandbox Account 1), from 17:09 to 17:54: `iam:SimulatePrincipalPolicy` as `eighth-experimentation`'s
project role, which evaluates the organization's policies and the role's boundary, and plans from
`origin/main` `30855d92`'s tree and from this branch. No AWS write. Times are UTC.*

- **[Claude] The switches re-planned**, 17:09:27 to 17:10:27, each default *"No changes."*:
  `sandbox/workflows/` with `training_pair_enabled=true` *"Plan: 0 to add, 1 to change, 0 to destroy."*;
  `sandbox/bedrock/` with `application_guardrail_required=true` and `account_guardrail_enabled=true`
  *"Plan: 3 to add, 1 to change, 0 to destroy."*
- **[Claude] The creates of passes 4 and 5**, in three runs, each with the request tag
  `AmazonDataZoneProject` at the project's value. 17:29:40, with nothing else of the project's:
  `CreateModel`, `CreateEndpointConfig`, `CreateEndpoint` and `CreatePipeline` `implicitDeny`,
  `CreateTransformJob` `explicitDeny` by `awsds-sandbox-project-boundary`. 17:30:21, adding the resource tag
  and `aws:PrincipalAccount`: all five `allowed` through `SageMakerStudioProjectRoleMachineLearningPolicy`;
  `CreateTrainingJob` `explicitDeny` by the boundary and `iam:PassRole` of the role to SageMaker
  `implicitDeny`. 17:32:01, adding `sagemaker:InterContainerTrafficEncryption=true`, the `RoleName` principal
  tag and `aws:ResourceAccount`: `CreateTrainingJob` `allowed`, `iam:PassRole` `allowed` through
  `SageMakerStudioProjectUserRolePolicy`, and an endpoint configuration on `ml.g5.xlarge`, 4.5's negative,
  `explicitDeny` by the boundary.
- **[Claude] The tag a create also authorizes**, 17:51:17: `sagemaker:AddTags` of the project tag alone, at
  the caller's value, `allowed` on a model, a transform job and a processing job through
  `awsds-sandbox-workflows` and on a model package group through `awsds-sandbox-ml`; `implicitDeny` on an
  endpoint configuration, an endpoint, a pipeline and a training job. The training job's is
  `sandbox/workflows/`'s pair, applied on `promotion.md` §N.9's day 2; nothing granted the other three, so
  pass 4's endpoint and pass 5's pipeline would have been refused at their create (decision 7).
- **[Claude] `sandbox/ml/` written** on this branch: `TagAnEndpointConfigWithTheCallersProject`,
  `TagAnEndpointWithTheCallersProject` and `TagAPipelineWithTheCallersProject` beside the model package
  group's statement, all four generated by a `dynamic` block from `local.tagged_resources`, so the three
  conditions are written once. The policy's description is unchanged and it updates in place.
- **[Claude] `sandbox/ml/` planned**, 17:52:44 to 17:53:01: *"Plan: 0 to add, 1 to change, 0 to destroy."*,
  `aws_iam_policy.ml` at four statements and 1,858 characters; saved at 17:53:20 to
  `$HOME/tmp/stage17-ml-tags.tfplan`. `terraform fmt` clean.
- **[Claude] The planned document simulated** beside the role's policies, 17:54:04: `AddTags` of the project
  tag at the caller's value `allowed` on the endpoint configuration, the endpoint and the pipeline through
  `PolicyInputList.1`; another project's value on the endpoint, and a second key, `AmazonDataZoneDomain`,
  beside the project's on the pipeline, both `implicitDeny`.
- **[Claude] Where the passes run**: passes 2, 3 and 7 on §N.9's day 2, pass 5 on day 3, pass 4 on §N.10's
  day 1 with its endpoint kept up. `sandbox/ml/` is applied from `main` after the merge, on the user's word
  naming it, before day 3 (§N.6 item 3).

## 2026-11-20 — `sandbox/ml/`'s endpoint and pipeline statements applied

*Claude, in the same session, on the user's "Merge feito, aplique" answering a question that named the apply
of `sandbox/ml/` in Sandbox Account 1 after pull request #343's merge. As the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox Account 1), from this session's
worktree, whose tree equals `origin/main` at `78dc4397`, the merge of 19:38:28 (`git diff` empty). Times
are UTC.*

- **[Claude] Before the write**: #343 read `MERGED`; no other Claude session on the laptop; `make status`,
  read before 6d decision 6's apply at 19:21 (6d's log), had shown 0.0000 USD/h with everything down.
- **[Claude] The plan**, saved as `$HOME/tmp/stage17-ml-tags.tfplan`: *"Plan: 0 to add, 1 to change, 0 to
  destroy."*, `aws_iam_policy.ml` alone. Read with `terraform show -json`: `awsds-sandbox-ml` from one
  statement, `TagAModelPackageGroupWithTheCallersProject`, unchanged, to four, adding
  `TagAPipelineWithTheCallersProject`, `TagAnEndpointConfigWithTheCallersProject` and
  `TagAnEndpointWithTheCallersProject`, each `sagemaker:AddTags` on its type's ARN pattern under the same
  three conditions; no other attribute changing.
- **[Claude⚡] The apply**, 19:40:33 to 19:40:42: *"aws_iam_policy.ml: Modifications complete after 1s"*,
  *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*
- **[Claude] The readings after**: the re-plan *"No changes. Your infrastructure matches the
  configuration."* (`-detailed-exitcode` 0); `get-policy` at `v2`, `AttachmentCount` 2, updated
  19:40:41, its four statements as planned, attached to `eighth-experimentation`'s and `app-ml-dev`'s
  roles.
- **[Claude] The simulation**, as `eighth-experimentation`'s role, `sagemaker:AddTags` with the project tag
  alone. At 19:41:39, with no `aws:RequestedRegion` in the context, every call, the model package group's
  included, read `explicitDeny` with `AllowedByOrganizations` false and no matched statement: `SUP-008`'s
  shape. At 19:42:49, with the context of 17:51:17 (the region, the principal's `AmazonDataZoneProject`,
  `RoleName` and `EnableSageMakerMLWorkloadsPermissions` tags, both accounts): `endpoint-config`,
  `endpoint` and `pipeline` at the caller's value `allowed` through `awsds-sandbox-ml`, as is
  `model-package-group`; the endpoint at `test-experimentation`'s value and the pipeline with a second key,
  `AmazonDataZoneDomain`, both `implicitDeny`; a training job's tag `implicitDeny`, the training pair of
  `sandbox/workflows/` being applied on `promotion.md` §N.9's day 2.
- **[Claude] The records**: decision 7, the deliverables row, the ready list and the `Status` row in the
  stage file; `runbooks/sagemaker-ai-ml.md`'s paragraph on what a notebook creates; `promotion.md` §N.6
  item 3, §N.9.1 and §N.10.1; the waiting list's Sandbox row; Current position.

## 2026-11-20 — Day 2's training pair planned from `main`'s tree

*Claude, in the session that applied 6d decision 6 and Stage 17 decision 7 the same day, on the user's request to prepare every pending sitting before raising anything and to minimise the plan's running time (*"otimize o plano e faça todas as preparações necessárias para que o tempo necessário para executar o plano seja minimizado"*). As the infrastructure user with `InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox
Account 1), from this session's worktree at `main`'s `5dfff219`; nothing applied. Times are UTC.*

- **[Claude] The plan** of `sandbox/workflows/` with `-var training_pair_enabled=true`, saved as
  `$HOME/tmp/stage17-training-pair-preflight.tfplan`: *"Plan: 0 to add, 1 to change, 0 to destroy."*,
  `aws_iam_policy.workflows` alone, its statements from seven to nine with
  `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject`. The default plan reads
  *"No changes."* Day 2 applies the saved file only while the slice's state and `main`'s tree have not
  moved; Terraform refuses it otherwise.
- **[Claude] 2.1's dataset**, `Telco-Customer-Churn.csv` on `raw.githubusercontent.com`, answers 200 to a
  `HEAD` from the laptop.
- **[Claude] 10.4's `DEV_MODEL_ID`**: `aws bedrock list-inference-profiles --type-equals APPLICATION` in
  Sandbox lists three profiles, the domain's Claude Haiku 4.5 and Nova Lite of 2026-10-19 and
  `eighth-experimentation`'s Claude Opus 4.5 of 2026-10-30, none of `app-genai-dev`'s: the project's first
  Nova Lite call, before 10.4's deploy, creates it (`promotion.md` §N.12.4).
- **[Claude] 9.7's gate, dry**: `pip-audit` 2.10.1 over each lock's runtime set (`uv export --frozen --no-dev`), an approximation of
  the gates' job, which `awsds/ci-gates` holds: *"No known vulnerabilities found"* for `app-etl` (one
  package), `app-ml`'s `code` (48) and `app-dbt` (78), at 20:36 UTC. The gate itself runs on the laptop
  the day of each tag, before the tag (Lesson 77).
- **[Claude] 9.9's and 10.9's Sandbox halves**, written by a subagent of this session and read by
  Claude: `./aws/sandbox-ml.py` gained `ML-10` (section 12, `app-ml` in `app-ml-dev`) and `ML-11`
  (section 13, `app-genai` in `app-genai-dev`), its read-only calls `describe-model-package`,
  `describe-model-package-group`, `list-model-packages`, `get-guardrail`, `list-guardrails`,
  `list-enforced-guardrails-configuration`, `list-inference-profiles`, `list-tags-for-resource`,
  `list-objects-v2` and `s3 cp` to the laptop. Its run at 21:04:17 returned every call: `ML-10`
  passes on `models app-ml-score-*`, `none`, and `ML-11` on `ListEnforcedGuardrailsConfiguration`, `empty`;
  nine notes name the objects 9.6 and 10.4 create, among them no application inference profile tagged
  with `app-genai-dev` and `awsds-sandbox-bedrock-application` v1 with no
  `DenyAnInvocationWithNoPublishedGuardrailOfTheAccount`, the state between sittings. `OR-10`, `OR-11`
  and `DT-14` are owed.

## 2026-11-21 — 0.9: the left navigation read in both projects

*Claude's hand in the user's Chrome, on the portal session the user opened for it (*"Abri uma sessão no
chrome no SMUS para você realizar as leituras."*), signed in as the Data Scientist User (read in the account
menu), with the estate down. Links were followed and nothing was created; each project's *Update project*
banner was left alone, and the tab was closed at the end. Times are UTC, from about 17:58 to 18:11.*

- **[Claude] The navigation**, the same in `eighth-experimentation` and `app-etl-dev`, in order: Overview,
  Discover, Data, Files, Repositories, Connections, Resource blueprints (*New*), Compute; Notebooks,
  Workflows; **Data analytics**: Query Editor, Visual ETL, Data processing jobs; **AI/ML**: Models,
  Training jobs, MLflow, Inference endpoints, ML pipelines, Feature Store; **Generative AI**: Playground,
  AI apps; **IDEs**: JupyterLab, Code Spaces; Manage at the foot. *JumpStart models*, *Model registry* and
  *Partner AI apps* are absent.
- **[Claude] The AI/ML entries**, each read in both projects, paths under `/projects/<id>/`:
  - *Models*, `modelhub`: the tabs *Foundation models* (939 models, a model finder by type, featured
    providers) and *My models* (`modelhub/registered`: *"These are your own trained, versioned,
    production-ready models. You can register models using the SageMaker SDK in a notebook."*, filtered by
    *Model group*, *Model* or *Deployable models*), *"No models found"* in both projects.
  - *Training jobs*, `trainingjobs`: *"View and manage SageMaker training jobs created from notebooks."*,
    *"You don't have any training jobs."*; its *Browse models to train* opens *Foundation models*.
  - *MLflow*, `compute?type=mlflow`: Compute's *MLflow* tab, *MLflow environments*, under the banner *"The
    Compute page is migrating to Resource blueprints."*; `eighth-experimentation` lists `ml-demo-mlflow`,
    *On*, *App*, created 2026-10-19 06:39, and `app-etl-dev` *"No MLflow Apps or Tracking Servers found"*.
    The legacy experiments page 1.1 read is no longer what the entry opens.
  - *Inference endpoints*, `endpoints`: *"You don't have any inference endpoints."*, *Create new endpoint*.
  - *ML pipelines*, `pipelines/view`: *Delete*, *Edit*, *Create in visual editor*, *"No pipelines"*.
  - *Feature Store*, `feature-store`: *"You don't have any feature groups."*, *Create feature group*.
- **[Claude] The Generative AI entries**:
  - *Playground*, `/bedrock/playground/explorer`, a domain path with no project in it: *Chat playground*,
    and Amazon Bedrock's panel with *Discover*, *Models*, *Playgrounds* (*Chat*, *Image and video*) and
    *Shared apps and prompts*. `app-etl-dev`'s page preselected Nova Lite; no prompt was sent.
  - *AI apps*, `bedrock/playground/chat`: a new chat agent app, *"Not saved"*, *"Not deployed"*, *"Not
    shared"*, *App ID: -*, under Agents Classic's notice, never saved; the panel's *Build* (*Chat agent*,
    *Flow*, *Prompt*, *Model evaluations*) and *Asset gallery* (*My apps*, *My prompts*, *My components*).
    *My components*, `bedrock/components`, lists *Components (0)* in `app-etl-dev`, typed *Knowledge base*,
    *Guardrail* or *Function*.
  - In `app-etl-dev`, *AI apps* opened from *Playground* rendered *"Whoops, something went wrong."*, the
    console reading *"TypeError: Cannot read properties of undefined (reading 'foundationModel')"* in the
    playground's code at 18:07:05; *Reload page* drew the builder.
- **[Claude] Not opened**: *JupyterLab* (`code`), which opens a space, *Code Spaces* (`code-spaces`) and
  *Manage*.
- **[Claude] The verdicts**: xxvii, neither chapter as written: the menu carries the IAM-based chapter's
  entries, with *My models* where that chapter names *Registered Models*, and neither of the Identity Center
  chapter's *JumpStart models* and *Model registry*. xxxiii's 0.9 half: *Feature Store* shows in an Identity
  Center domain. The paths of "The menu, entry by entry" are corrected in the stage file the same day.
- **[Claude] Day 2's saved plan**: Terraform 1.17.2, on the laptop since this day, refuses
  `$HOME/tmp/stage17-training-pair-preflight.tfplan` (Stage 8's log, `SUP-403`), so day 2 plans the
  training pair again from `main`.

## 2026-11-21 — Day 2's pre-flight with nothing up

*Claude, in a session the user opened to prepare `promotion.md` §N.9's day 2 (*"Faça toda a preparação
necessária para iniciarmos a sessão do dia 2 do §N.9."*). Reads and plans as the infrastructure user with
`InfrastructureAccess`, through `awsds-infra-sandbox-1` (account Sandbox Account 1), `make status` and the
instruments through their own profiles, from this session's worktree at `main`'s `0c78f571`. Nothing applied
and nothing raised; the one other session on the laptop was idle. Times are UTC.*

- **[Claude] `make status`**, 18:45: *"estimated burn: USD 0.0000/h"*, the proxy, VPN and GitLab hosts
  `stopped`, no Studio app, no EMR Serverless application started and no OpenSearch Serverless collection.
- **[Claude] The instruments**, 18:47 to 19:09, each as expected with everything down:
  - `./aws/sandbox-ml.py`: 35 pass, no check failed, no call failed; `ML-2` `ml-demo-mlflow` `Created` on
    MLflow 3.16.0, `ML-7` the four quotas at 20, 30, 8 and 10, `ML-8` Titan V2 `AVAILABLE` and `AUTHORIZED`.
  - `./aws/devenv.py`: `DE-1`, `DE-4` and `DE-5` pass (version 11, 73 names); `DE-2` fails while
    `sandbox/egress/` is down.
  - `./aws/egress.py` on Production, Staging and Sandbox: no metered egress, no call failed.
  - `./aws/catalog.py`: 15 pass and 5 notes, no check failed; `./aws/bedrock-scope.py`: `BS-1` to `BS-7`
    pass; `./aws/remote-ide.py`: `RI-3` and `RI-4` pass.
  - `./aws/studio.py`: 58 pass and 7 notes, no check failed, `US-13` reading version 11 in
    `eighth-experimentation`'s blueprint domain; the persona and deploy profiles did not authenticate, with
    no sign-in on their sessions.
  - `./aws/bedrock-usage.py` from 2026-11-01 to 18:51: 17 invocations and 0.0005 USD computed, the newest
    event at 2026-11-19 04:24:23, so pass 7's and 6e 6.4's baseline has not moved since 2026-11-20. `BU-5`
    notes Nova Lite unpriced: `docs/PRICING.md`'s row names the model, not its id.
- **[Claude] The training pair re-planned.** The file of 2026-11-20 read as *"plan file was created by
  Terraform 1.16.6, but this is 1.17.2; plan files cannot be transferred between different Terraform
  versions"* (`SUP-403`). `sandbox/workflows/` planned *"No changes."* at 18:57:04 (`-detailed-exitcode`
  0); with `-var training_pair_enabled=true`, *"Plan: 0 to add, 1 to change, 0 to destroy."*, saved over the
  old file at 18:57:22. Read with `terraform show -json`: `aws_iam_policy.workflows`'s `policy` alone, from 7
  statements to 9 with `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject`,
  3,146 characters minified, as on 2026-11-20.
- **[Claude] Day 2's raise, dry and planned.** `make up ENV=sandbox
  GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent DRY=1` names `sandbox/egress/` and `sandbox/probes/`, the
  warehouse's compute held by refusal 11. `sandbox/egress/` planned at 18:58 with the four groups as
  `TF_VAR_optional_service_groups`: *"Plan: 33 to add, 0 to change, 0 to destroy."*, 24 interface
  endpoints, the base set's 18 with `airflow-serverless`, `sagemaker.mlflow`, `bedrock`, `bedrock-runtime`,
  `bedrock-agent` and `bedrock-agent-runtime`. Its `no_proxy_all_groups`, 73 names, equals the Dockerfile's
  literal, so `DE-3` reads green after the raise.
- **[Claude] 2.4's model**, `describe-hub-content` on `SageMakerPublicHub`: `xgboost-classification-model`
  2.2.0 `Available`, beside `xgboost-regression-model`. Its document: `DefaultTrainingInstanceType`
  `ml.m5.4xlarge`, outside the boundary's ceiling, with `ml.m5.xlarge` among `SupportedTrainingInstanceTypes`;
  `TrainingEnableNetworkIsolation` and `EncryptInterContainerTraffic` `true`; `DefaultTrainingDatasetUri`
  under `jumpstart-cache-prod-us-west-2/training-datasets/`; `MaxRuntimeInSeconds` 360000.
- **[Claude] Pass 7's service role**, `AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c`, carrying
  `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9 and `SageMakerStudioBedrockEvaluationJobServiceRolePolicy`
  v3 with the flow's and the agent's. Its tags name the project, the domain, the bucket
  `awsds-sandbox-smus-projects` and the bucket's default key. Simulated at 19:03 with those tags,
  `aws:RequestedRegion` and both accounts as context; the boundary and the organization allowed every call:
  - `allowed`: `s3:GetObject` and `s3:ListBucket` on the project's `shared/ml-demo/bedrock/kb/`, `kms:Decrypt`
    of the key through S3, `bedrock:InvokeModel` on an application inference profile tagged with the project
    and on a foundation model through a profile, `s3vectors:PutVectors` on `amazon-bedrock-ide-<project>*`;
  - `implicitDeny`: another project's prefix, Titan V2's foundation model with no profile, the domain's
    Haiku 4.5 profile, which carries no project tag, Haiku 4.5's system profile, another vector bucket name.
- **[Claude] The application inference profiles**: three in Sandbox, the domain's Haiku 4.5 (`cp0gmvjv1h8q`)
  and Nova Lite (`csu817ovl4kz`), tagged with the domain alone, and `eighth-experimentation`'s Opus 4.5
  (`zy55dk32prho`). Pass 7's knowledge base (Titan V2) and its evaluation job, flow and chat agent (Haiku
  4.5) each run as the service role, so each needs a profile of the project's for its model: the IDE's
  first use creates one (decision 13's path), or IAM refuses the call with *no identity-based policy
  allows*.
- **[Claude] The rest**:
  - the runbooks 7.4a indexes: 20 files and 1,210,723 bytes at `0c78f571`;
  - 2.1's dataset and awsds-workflows' `scripts/space_values.py` answer 200 to a `HEAD`;
  - AWS's `sagemaker-xgboost:3.0-5` exists in `us-west-2` (`ecr batch-get-image`, no failure), the URI SDK
    3.21.0's `image_uris.retrieve` prints;
  - `./aws/sandbox-ml.py` prints `MLFLOW_APP_ARN=` under section 3 since this sitting (run at 19:14:50, 35
    pass), the place `examples/sandbox-ml/README.md` names for the value;
  - `$HOME/tmp/stage17-day2-extra_values.json` holds `XGBOOST_IMAGE_URI` and `MLFLOW_APP_ARN` for the
    space's clone, outside git since the ARN carries the account's id.
- **[Claude] Left to the day**: the user's acts of `promotion.md` §N.9.4, and the training pair's apply on
  the user's word naming it.

## 2026-11-21 — Day 2's sitting B: the opening readings, 0.3 and 0.7

*Claude, in the session the orchestrating session started for `promotion.md` §N.9.4's day 2, with the user
at the laptop. Claude's reads as the infrastructure user with `InfrastructureAccess` through
`awsds-infra-sandbox-1` (account Sandbox Account 1) and, for the proxy's log, `awsds-infra-prod` (account
Production); the instruments through their own profiles. The portal was read by Claude through Claude in
Chrome, in the user's Chrome signed in as the Data Scientist User, at the user's choice (*"Você, pelo
Chrome"*); nothing was saved, created or submitted. The space's readings are the user's, pasted, with the
account id written `<Sandbox Account 1>`. Times are UTC.*

- **[Claude] The opening readings** (order 1), with the hub and the day's four groups raised before them;
  the MLflow endpoint `vpce-0c34126a42848e404` was created at 19:47:33:
  - `make status`, 19:55: `production/vpn` and `production/proxy` `UP`, `sandbox/egress` `UP` with 33
    resources and `sandbox/probes` with 4, *"no Studio app billing"*, *"estimated burn: USD 0.2090/h"*.
  - `./aws/egress.py awsds-infra-sandbox-1`: every check passed; `EG-5` *"24 interface endpoint(s) + 0
    NAT(s) = ~USD 0.240/h"*.
  - `./aws/devenv.py`: `DE-1` to `DE-6` pass, the baked list and the account's at 73 names, sha256
    `61f1e1646df12c14`; `DE-5` read the image's bytes at 19:58:18.
  - `./aws/sandbox-ml.py`, 19:58:24 to 20:01:52: 37 pass, none failed. `ML-9`:
    `aws.sagemaker.us-west-2.mlflow` answered by `vpce-0c34126a42848e404`, `available`, private DNS on;
    the S3 gateway's list names `sagemaker-us-west-2` and `jumpstart-cache-prod-us-west-2`;
    `awsds-sandbox-egress-allow` 14 entries. `ML-2` `ml-demo-mlflow` `Created` on MLflow 3.16.0; `ML-7`
    20, 30, 8 and 10; `ML-8` Titan V2 `AVAILABLE` and `AUTHORIZED`, and no knowledge base, vector bucket,
    agent, prompt, flow, guardrail or evaluation job.
  - 1.6's "before", 20:07: `list-metrics` holds no `BytesProcessed` series for `vpce-0c34126a42848e404`.
- **[user] The spaces**, in `eighth-experimentation`'s blueprint domain `eighth-experimentation-ai-domain`
  (`d-m8m0uefej9kb`), read by Claude with `list-spaces` and `list-apps`, both `InService`: `jup`, JupyterLab
  on `ml.t3.medium` with `awsds-sandbox-dev-env` version 11, created 20:07:15, remote access `DISABLED`;
  `code`, Code Editor on `ml.t3.large`, created 20:08:41, remote access `ENABLED`, for 6d's 7.5 and 7.7.
- **[user] 0.3, the space.** The versions in both interpreters, pasted:

  ```text
  == /opt/awsds/venv/bin/python
  python 3.12.14
  sagemaker 3.21.0
  sagemaker-core 2.21.0
  mlflow 3.17.2
  mlflow-skinny 3.17.2
  sagemaker-mlflow 0.5.0
  xgboost absent
  xgboost-cpu 3.3.0
  boto3 1.43.92
  pandas 2.3.3
  == /opt/conda/bin/python
  python 3.12.14
  sagemaker absent
  sagemaker-core 2.21.0
  mlflow 3.15.2
  mlflow-skinny 3.15.2
  sagemaker-mlflow 0.5.0
  xgboost 2.1.4
  xgboost-cpu absent
  boto3 1.43.75
  pandas 2.3.3
  ```

  **[Claude]** The house interpreter holds the lock's versions. Neither `SAGEMAKER_USER_CONFIG_OVERRIDE` nor
  `SAGEMAKER_ADMIN_CONFIG_OVERRIDE` is set (*"no override variable"*), the user configuration
  `~/.config/sagemaker/config.yaml` is `absent`, and the admin configuration is the only `config.yaml` under
  `/etc`, `/opt` and `/home`, pasted:

  ```yaml
  == /etc/xdg/sagemaker/config.yaml
  SchemaVersion: '1.0'
  SageMaker:
    PythonSDK:
      Modules:
        Session:
          DefaultS3Bucket: awsds-sandbox-smus-projects
          DefaultS3ObjectKeyPrefix: shared/
        RemoteFunction:
          IncludeLocalWorkDir: true
          VpcConfig: &id001
            SecurityGroupIds:
            - sg-0fee1c059b82e3562
            Subnets:
            - subnet-016b5a3a62c739894
            - subnet-09d3399d6b0fec93a
        NotebookJob:
          RoleArn: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
          S3RootUri: s3://awsds-sandbox-smus-projects/shared/
          VpcConfig: *id001
        Serve:
          S3ModelDataUri: s3://awsds-sandbox-smus-projects/shared/
    Pipeline:
      RoleArn: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
    Model:
      ExecutionRoleArn: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
      VpcConfig: *id001
    ModelPackage:
      ValidationSpecification:
        ValidationRole: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
    ProcessingJob:
      RoleArn: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
      NetworkConfig:
        VpcConfig: *id001
    TrainingJob:
      RoleArn: arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
      Environment:
        BOTOCORE_EXPERIMENTAL__PLUGINS: S3AccessGrantsPlugin=aws_s3_access_grants_boto3_plugin.s3_access_grants_plugin
      VpcConfig: *id001
    MonitoringSchedule:
      MonitoringScheduleConfig:
        MonitoringJobDefinition:
          NetworkConfig:
            VpcConfig: *id001
    AutoMLJob:
      AutoMLJobConfig:
        SecurityConfig:
          VpcConfig: *id001
    AutoMLJobV2:
      SecurityConfig:
        VpcConfig: *id001
    CompilationJob:
      VpcConfig: *id001
  ```

  **[Claude]** What a `CreateTrainingJob` through the SDK's own classes gets filled in: the project role, the
  project's security group (`datazone-avhvbqn37ty7m8-dev`) and both private subnets, and the S3 Access Grants
  plugin in the container's environment. No key, no tag, no isolation and no inter-container encryption
  anywhere, so 2.2 (a) and (b) stay two readings. The S3 defaults name the bucket's root `shared/`, outside
  the project's `<domain>/<project>/` prefix. `examples/sandbox-ml/` calls boto3's client, which reads none of
  this file. The clone read `b3b900b 2026-11-21T16:51:08-03:00`; `space_values.json` holds `ACCOUNT_ID`,
  `DOMAIN_ID`, `PROJECTS_BUCKET`, `PROJECT_ID`, `PROJECT_KEY_ID`, `PROJECT_ROLE_NAME`, `PROJECT_SG`, `REGION`,
  `SUBNET_AZ1` and `SUBNET_AZ2`; the user replaced the clone's `extra_values.json` with the laptop's. The
  fetch of `space_values.py` is the proxy's line *"2026-11-21T20:19:16+0000 10.20.38.182 CONNECT
  raw.githubusercontent.com:443 200 14336 974 TCP_TUNNEL"*.
- **[Claude] 0.7, the forms**, from 20:15, in `eighth-experimentation`; the account menu read *"Data
  Scientist User"*:
  - **JumpStart has no *Train* form.** AI/ML → *Models*, searched *"xgboost classification"*: one model,
    *"XGBoost Classification"*, Model ID `xgboost-classification-model`, *Tabular Classification ·
    Fine-tune*. Its page offers *Customize* ▾ and *Deploy* ▾, each with *Notebook*, disabled (*"Notebooks
    are currently not supported for cross-region and cross-account project configurations"*), and
    *JupyterLab*, not clicked. The *Sample notebooks* tab previews two:
    - *Deploy*, *"SageMaker Built-In Algorithms: Tabular Classification using XGBoost and Linear
      Learner"*: SDK 3's `ModelTrainer.from_jumpstart_config(JumpStartConfig(model_id=...))` with
      `Compute(instance_type="ml.m5.xlarge")`, JumpStart's dataset under
      `jumpstart-cache-prod-{region}/training-datasets/tabular_multiclass/`, the output under
      `sagemaker_session.default_bucket()`, a first cell `!pip install ipywidgets==7.0.0`, then
      `ModelBuilder.deploy()` and the deletes;
    - *Fine-tune*, *"Training Model with Jumpstart And MLflow In SageMaker Unified Studio"*: SDK 2's
      `sagemaker.jumpstart.estimator.JumpStartEstimator`, which SDK 3.21.0 does not carry, with t5's
      hyperparameters, `instance_type` commented out and an MLflow tracking server placeholder.

    2.4's portal path is a sample notebook run in JupyterLab, not a form to submit once.
  - **Inference endpoints → *Create new endpoint*** opens *Select model*, *"No registered models found. No
    registered models with approved versions found. Models must have at least one approved version to
    appear here."*, with *Create endpoint using JupyterLab* and *Create endpoint using Notebook* disabled;
    no field form and no *Add model*.
  - **Compute → MLflow**: `ml-demo-mlflow`, *On*, *App*. *Create* ▾ greys both items: *Create MLflow App*
    (*"The MLflowApp blueprint is not enabled for this project. Contact your administrator to enable
    it."*) and *Create MLflow Tracking Server* (*"The MLExperiments blueprint is not enabled for this
    project."*). The page carries *"The Compute page is migrating to Resource blueprints"*.
  - **ML pipelines → *Create in visual editor***, a draft never saved. The library: *Run notebook or code*,
    *Run callback*, *Run lambda function*, *Process data*, *Train model*, *Fine tune model*, *Register
    model*, *Create model*, *Deploy model (endpoint)*, *Deploy model (batch inference)*, *Condition*,
    *Fail*. The step forms:

    | Step | Fields | *Advanced → Security* | Isolation, inter-container encryption |
    |---|---|---|---|
    | *Train model* | Model output S3 URI and Algorithm ECR URI (required), Input Mode *FastFile*, metrics, Instance Type default `ml.m5.xlarge`, Count, Additional storage per instance (30 GB shown), hyperparameters, stopping condition 86400 s, checkpoints, caching, retry | IAM Role empty; VPC `vpc-00dca74a35159b11c`, both subnets and `sg-0fee1c059b82e3562` filled; Encryption KMS key empty | no field |
    | *Process data* | Image URI (required), Instance `ml.m5.xlarge`, Count 1, storage 1 GB, stopping 86400 s | as *Train model* | no field |
    | *Create model* | Execution Role, Model S3 URI (required), *Bring your own container*, ECR URI, environment | VPC, subnets, security groups | no field |
    | *Deploy model (endpoint)* | Endpoint Name (required), *Real-time*, default `ml.t2.medium`, Count 1, Maximum count 1 | none, no key | — |
    | *Deploy model (batch inference)* | data input and output (output and capture keys *"No Custom Encryption"*), Instance `ml.m5.xlarge`, configuration, data joins, environment | none, no volume key | — |

    Every step's *Tags* say *"Tag keys will be automatically prefixed with "ProjectUserTag"."*, so no form
    can set `AmazonDataZoneProject`; a *Train model* or *Process data* step submitted from the editor lacks
    isolation and inter-container encryption, which the boundary requires.
  - **Generative AI → *My components***: *"Components (0)"*, *Create component* ▾ offering *Knowledge
    Base*, *Guardrail* and *Function*.
    - *Create function*, cancelled: name, description, an OpenAPI 3.0.0 schema of up to 5 APIs,
      authentication *No authentication* by default (or API keys, bearer token, basic), a server URL; no
      network field and no Lambda field.
    - *Create a new knowledge base*, cancelled: name and description; sources *Local file*, *Web crawler*
      and *Project data sources*. *Local file* takes .docx, .doc, .pdf, .txt, .md, .html, .csv, .xls and
      .xlsx, *"Maximum 10 files, 50MB per file"*, where 7.4a read 50 files on 2026-10-12. *Project data
      sources* lists *Lakehouse (1)*, *Default Lakehouse connection*; *Redshift (1)*,
      `redshift-serverless.redshift`; *S3 (3)*: `default.s3_shared`
      (`s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/`), *S3 (Default)*
      (`…/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/`) and `sandbox-lake.s3`
      (`s3://awsds-sandbox-lake/sso-group-data-scientists/`). *Data storage and processing*, fixed at
      create: the embeddings model *Titan Text Embeddings V2* alone; with it, the embedding type
      *Floating-point vector embeddings* alone, the dimension 256, 512 or 1024 with 256 preselected; the
      vector store preselected as *Vector engine for Amazon OpenSearch Serverless*, beside *Amazon S3
      Vectors - new* and *Amazon Neptune Analytics (GraphRAG) - new*, the last disabled. Chunking
      *Default*, *Fixed size*, *Hierarchical*, *Semantic* and *None*; parsing *Bedrock default parser*
      with *"Access to model required"*. 7.4a picks S3 Vectors and 1024 by hand, since the defaults are
      OpenSearch Serverless and 256.
  - **Build → *Model evaluations* → *Create evaluation***, left at its second step: the model list *Nova
    Lite*, *Claude Haiku 4.5*, *Claude Opus 4.5* and *Claude Sonnet 4.5*, the three Claude models
    *Cross-region*; the task types *General text generation*, *Text summarization*, *Question and answer*
    and *Text classification*. For *Question and answer*, *Accuracy* and *Robustness* take the built-in
    datasets alone (*"Custom datasets are not supported for Q&A task type with robustness or accuracy
    metrics"*: *BoolQ*, *Natural Questions*, *Trivia QA*); *Toxicity* takes *Upload a dataset to S3*
    (*"max. 100 MB per file, 1 file"*, from the browser) or *Choose a dataset from S3*, which opens
    *Select a previously uploaded dataset* and read *"No options"*. The field does not browse
    `shared/ml-demo/bedrock/`: 7.4's dataset reaches the job by the upload.
  - **Build → *Chat agent***, an unsaved *Untitled App*, its model preselected as *Claude Opus 4.5*; the
    list *Nova Lite*, *Claude Haiku 4.5*, *Claude Opus 4.5* and *Claude Sonnet 4.5*, each *"Supports
    Guardrails, Data, Functions"*. The page's banner: *"Agents Classic will no longer be open to new
    customers starting on July 30, 2026"*.

## 2026-11-21 — Day 2's sitting B: 1.6 and 2.1

Written by Claude in the session the orchestrator started. The user ran the commands in the `jup` space and
pasted their output. The lines quoted below are excerpts in the paste's order, each line verbatim except the
account id in S3 Control's host name, written `<Sandbox Account 1>`; left out are the container-credential
fetches from `169.254.170.2` and six of 1.6's nine MLflow requests, all `200`. Claude's readings ran as
`awsds-infra-sandbox-1` (Sandbox Account 1) and, for the proxy's log, `awsds-infra-prod`. Times UTC.

- **[Claude] The apps, restarted.** The blueprint domain's 60-minute idle shutdown deleted `code` at
  21:19:50 and `jup` at 21:23:14 (`DeleteApp` by `AWSServiceRoleForAmazonSageMakerNotebooks`); both spaces
  stayed `InService` with their home volumes, the clone and `extra_values.json` on them. The user started
  both again: `list-apps` read them `Pending` at 23:02:08 under the deleted apps' `CreationTime`. The new
  apps took new addresses, read from their first proxy lines: `jup` 10.20.54.175 (was 10.20.38.182),
  `code` 10.20.26.209 (was 10.20.20.46).
- **[user] 1.6**, the step's script with urllib3's connection log on:

  ```
  start 23:08:13
  urllib3.connectionpool Starting new HTTPS connection (1): mlflow.sagemaker.us-west-2.app.aws:443
  urllib3.connectionpool https://mlflow.sagemaker.us-west-2.app.aws:443 "GET /api/2.0/mlflow/experiments/get-by-name?experiment_name=ml-demo-first-run HTTP/1.1" 404 142
  2026/11/21 23:08:33 INFO mlflow.tracking.fluent: Experiment with name 'ml-demo-first-run' does not exist. Creating a new experiment.
  urllib3.connectionpool https://mlflow.sagemaker.us-west-2.app.aws:443 "POST /api/2.0/mlflow/experiments/create HTTP/1.1" 200 26
  urllib3.connectionpool Starting new HTTPS connection (1): config.mlflow-telemetry.io:443
  urllib3.connectionpool https://mlflow.sagemaker.us-west-2.app.aws:443 "POST /api/2.0/mlflow/runs/create HTTP/1.1" 200 392
  urllib3.connectionpool Starting new HTTPS connection (1): sts.us-west-2.amazonaws.com:443
  urllib3.connectionpool https://sts.us-west-2.amazonaws.com:443 "POST / HTTP/1.1" 200 472
  urllib3.connectionpool https://awsds-sandbox-smus-projects.s3.us-west-2.amazonaws.com:443 "HEAD / HTTP/1.1" 200 0
  urllib3.connectionpool https://<Sandbox Account 1>.s3-control.us-west-2.amazonaws.com:443 "GET /v20180820/accessgrantsinstance/prefix?s3prefix=s3%3A%2F%2Fawsds-sandbox-smus-projects%2Fdzd-d8yrvx1ko7im6o%2Favhvbqn37ty7m8%2Fdev%2Fdata%2Fml%2Fmlflow%2Fworkspaces%2Fdefault%2F1%2Faa66682b1adc4b168ae4f857f1f0e315%2Fartifacts%2Fml-demo-1-6.txt HTTP/1.1" 200 251
  urllib3.connectionpool https://<Sandbox Account 1>.s3-control.us-west-2.amazonaws.com:443 "GET /v20180820/accessgrantsinstance/dataaccess?target=s3%3A%2F%2Fawsds-sandbox-smus-projects%2Fdzd-d8yrvx1ko7im6o%2Favhvbqn37ty7m8%2Fdev%2Fdata%2Fml%2Fmlflow%2Fworkspaces%2Fdefault%2F1%2Faa66682b1adc4b168ae4f857f1f0e315%2Fartifacts%2Fml-demo-1-6.txt&permission=WRITE&privilege=Default HTTP/1.1" 403 449
  urllib3.connectionpool https://awsds-sandbox-smus-projects.s3.us-west-2.amazonaws.com:443 "PUT /dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/mlflow/workspaces/default/1/aa66682b1adc4b168ae4f857f1f0e315/artifacts/ml-demo-1-6.txt HTTP/1.1" 200 0
  run aa66682b1adc4b168ae4f857f1f0e315 experiment 1
  artifact_uri s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/mlflow/workspaces/default/1/aa66682b1adc4b168ae4f857f1f0e315/artifacts
  end 23:08:35
  ```

  and `getent hosts mlflow.sagemaker.us-west-2.app.aws` printed `10.20.36.90     mlflow.sagemaker.us-west-2.app.aws`.
- **[Claude] 1.6's readings.**
  - The door: `vpce-0c34126a42848e404` (CloudWatch's service name `aws.sagemaker.us-west-2.mlflow`) had no
    `BytesProcessed` series at 20:07 or at 23:02; after the run it carried one datapoint, 23:08,
    `BytesProcessed` 9410 and `NewConnections` 1, its per-subnet series on `subnet-016b5a3a62c739894`
    alone. The client opened one connection to the host and sent its nine MLflow requests on it. The
    proxy's log holds no `mlflow` line from 23:05 to 23:10. Verification vi: yes. The name is
    `mlflow.sagemaker.us-west-2.app.aws`, resolved to the endpoint's address; the endpoint carried the
    bytes; nothing failed to resolve, so the DNS Firewall list needs no entry.
  - The artifact: `ml-demo-1-6.txt`, 18 bytes, `LastModified` 23:08:36, `aws:kms` under
    `alias/awsds-sandbox-project`'s key with the bucket key, the bucket's default. The MLflow store's
    objects are verification iv's other half, read with 3.1's model.
  - The S3 Access Grants plugin: before the PUT, `GetAccessGrantsInstanceForPrefix` answered 200 and
    `GetDataAccess` for `WRITE` 403, then the PUT ran under the role's own credentials, the plugin's
    fallback. Both S3 Control calls left through the proxy, one tunnel:
    `2026-11-21T23:08:35+0000 10.20.54.175 CONNECT <Sandbox Account 1>.s3-control.us-west-2.amazonaws.com:443 200 7313 6347 TCP_TUNNEL`.
    The house image's `NO_PROXY` names S3 as `s3.us-west-2.amazonaws.com` and
    `s3.dualstack.us-west-2.amazonaws.com` (`vpc-egress`'s `no-proxy.tf`), which `s3-control` does not end
    in, so `SUP-091`'s direct path through the gateway endpoint is not a space's: from a space the call
    takes `SUP-042`'s path through the proxy. The STS call and the PUT left direct: no proxy line.
  - MLflow's telemetry: `2026-11-21T23:08:33+0000 10.20.54.175 CONNECT config.mlflow-telemetry.io:443 403 3430 89 TCP_DENIED`,
    the connection the client logged with no response. MLflow's source (`mlflow-skinny` 3.18.0 in the
    laptop's uv cache; the house lock pins `mlflow` 3.17.2) reads `CONFIG_URL =
    "https://config.mlflow-telemetry.io"` and turns telemetry off when `MLFLOW_DISABLE_TELEMETRY` is true
    or `DO_NOT_TRACK` equals `true`; `DO_NOT_TRACK=1`, dbt's spelling in Stage 20, does not. The attempt
    shows neither set in the space. The allow-list held.
- **[user] 2.1**, `data.py`:

  ```
  fetched 7043 rows, 970457 bytes, from https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv
  raw: s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/data/raw/telco.csv
  prepared: 7032 rows, 11 dropped for a blank TotalCharges
  train: 4922 rows -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/data/train.csv
  validation: 1054 rows -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/data/validation.csv
  test: 1056 rows -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/data/test.csv
  ```
- **[Claude] 2.1's readings.** One proxy line,
  `2026-11-21T23:08:52+0000 10.20.54.175 CONNECT raw.githubusercontent.com:443 200 979031 1923 TCP_TUNNEL`,
  the CSV's 970,457 bytes and the TLS handshake. Verification xxvi: yes. The four objects read 970457,
  151945, 32496 and 32696 bytes, `LastModified` 23:08:53 to 23:08:54, each `aws:kms` under the project key
  with the bucket key; the rows match the step's 7,043, split 4922/1054/1056 of 7,032. A second S3 Control
  tunnel, `200 9301 12888 TCP_TUNNEL`, closed at 23:08:53, the second the objects were written.
- **[Claude] JupyterLab's telemetry loop, read in the proxy's log.** From `jup`, a pair every 2.5 to 2.6 s,
  each pair the same sizes:
  `CONNECT cognito-identity.us-east-1.amazonaws.com:443 200 8072 2932 TCP_TUNNEL` and
  `CONNECT client-telemetry.us-east-1.amazonaws.com:443 200 5605 3637 TCP_TUNNEL`. 1,529 pairs came from
  10.20.38.182 between 20:17:53 and 21:23:15, the old app's life from its UI's first minutes to its
  idle delete, and the loop started again from 10.20.54.175 at 23:07:53 (49 pairs by 23:09:57). The
  `code` space's addresses carry none, where 6d's log read the pair once per Code Editor start. Both
  names pass the compute plane's `.amazonaws.com` entry. About 6.6 KB leave per pair, 9.2 MB an hour per
  open JupyterLab app, and 19 MB arrive. The loop did not hold the app open: its last pair closed a
  second after the delete. The component that sends it was not identified, and no file of the repository
  then named `client-telemetry` but 6d's and Stage 19's logs (`SUP-450`).

## 2026-11-21 — Day 2's sitting B: 2.2 (a) and (b), and the training pair applied

Written by Claude in the session the orchestrator started. The user ran `train.py` and `env` in the `jup`
space and pasted their output, verbatim below except the account id, written `<Sandbox Account 1>`.
Claude's readings and the apply ran as `awsds-infra-sandbox-1` (Sandbox Account 1), the apply on the user's
words in this session's chat, *"Autorizo o apply do par"*. Times UTC.

- **[user] 2.2 (a) and (b)**:

  ```
  2026/11/21 23:19:34 INFO mlflow.tracking.fluent: Experiment with name 'ml-demo-xgboost' does not exist. Creating a new experiment.
  ml-demo-xgb-untagged-20261121-231933: created
  admitted, contrary to the stage's expectation: stopped
  🏃 View run ml-demo-xgb-untagged-20261121-231933 at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2/runs/b5466f46bf424ac3b1de029f0041ab18
  🧪 View experiment at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2
  ml-demo-xgb-tagged-20261121-231943: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:AddTags on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-tagged-20261121-231943 because no identity-based policy allows the sagemaker:AddTags action
  🏃 View run ml-demo-xgb-tagged-20261121-231943 at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2/runs/0799746e3de245368186293e8332e751
  🧪 View experiment at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2
  ```

  and `env | grep -i -E 'botocore|plugin'` printed
  `BOTOCORE_EXPERIMENTAL__PLUGINS=S3AccessGrantsPlugin=aws_s3_access_grants_boto3_plugin.s3_access_grants_plugin`.
- **[Claude] (a), admitted.** `train.py untagged` deletes `Tags` from its request, yet CloudTrail's
  `CreateTrainingJob` at 23:19:36, from 10.20.54.175 through `vpce-02feedaa4ad58acf4` with the user's
  profile name as source identity, records `requestParameters.tags` with seven keys:
  `sagemaker:user-profile-arn`, `sagemaker:domain-arn`, `sagemaker:space-arn` (`space/d-m8m0uefej9kb/jup`),
  `AmazonDataZoneProject` `avhvbqn37ty7m8`, `AmazonDataZoneScopeName` `dev`, `AmazonDataZoneUser` (the
  user's id) and `AmazonDataZoneDomain` `dzd-d8yrvx1ko7im6o`; `list-tags` on the job reads the same seven.
  No policy on the role allowed `AddTags`, as (b) shows. Who composes the seven is not read: the space's
  only botocore plugin is the S3 Access Grants plugin, which also accounts for 1.6's S3 Control calls; the
  blueprint domain's `TagPropagation` reads `None` (`ExecutionRoleIdentityConfig` `USER_PROFILE_NAME`);
  the four `AmazonDataZone*` keys are four of the nine the space and its user profile carry, without
  `ProjectS3Path`, `AmazonDataZoneStage`, `AmazonDataZoneBlueprint`, `AmazonDataZoneDomainAccount` and
  `AmazonDataZoneDomainRegion`. The job: `Stopped` at 23:19:39, no `TrainingStartTime`, no billable time;
  isolation and inter-container encryption on, `ml.m5.xlarge`, the project key on the volume, two subnets.
  The step's expectation for (a) was wrong for a notebook in a space: there the request that names no tag
  is admitted. `SUP-408`.
- **[Claude] (b), refused as expected.** CloudTrail's event at 23:19:44, `errorCode` `AccessDenied`, the
  message above, the same endpoint and source; `DescribeTrainingJob` of the name reads *"Requested resource
  not found"*: nothing was created. It is `SUP-267`'s exclusion of the `AmazonDataZone*` keys, met by a key
  the caller names.
- **[Claude] What (a) leaves in place.** The training pair stays where decision 7 put it: a workflow's
  operator names the tag, and 2.2 (c) and 2.3's negatives are `train.py tagged`'s variants.
- **[Claude] Order 6, the training pair applied.** At 23:25 the hub's session and the orchestrator were
  told; the other three peers were idle on unrelated work. `sandbox/workflows/` planned from this tree,
  *"No changes."* at 23:24:43. On the user's words, the plan saved at 18:57 (Terraform 1.17.2) applied
  from 23:29:37 to 23:29:49: *"Apply complete! Resources: 0 added, 1 changed, 0 destroyed."*.
  `awsds-sandbox-workflows` reads version `v7` (23:29:46), nine statements, `DescribeATrainingJobNoProjectHolds`
  and `TagATrainingJobWithTheCallersProject` among them. With `-var training_pair_enabled=true`, *"No
  changes."* at 23:30:36. The default is `true` in this branch, planned at 23:31:40, *"No changes."*; a plan
  from `main` removes the pair until the branch merges (Lesson 79).

## 2026-11-21 — Day 2's sitting B: 2.2 (c) and 2.3

Written by Claude in the session the orchestrator started. The user ran `train.py` in the `jup` space and
pasted its output; the lines quoted are verbatim except the account id, written `<Sandbox Account 1>`, and
the MLflow run links, left out. Claude's readings ran as `awsds-infra-sandbox-1` (Sandbox Account 1). Times
UTC.

- **[user] 2.2 (c)**, `train.py tagged --wait` after the training pair's apply:

  ```
  ml-demo-xgb-tagged-20261121-233934: created
  ml-demo-xgb-tagged-20261121-233934: Completed, 89 s billed
  validation:auc: 0.8209
  train:auc: 0.9513
  model: s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/models/ml-demo-xgb-tagged-20261121-233934/output/model.tar.gz
  ```
- **[Claude] 2.2 (c)'s job**: created 23:39:40, trained 23:40:22 to 23:41:51, 89 s billed, against the
  step's five minutes. Network isolation and inter-container encryption on, `ml.m5.xlarge` × 1, a 30 GB
  volume and the output under the project key, the project's two subnets and `sg-0fee1c059b82e3562`,
  `MaxRuntimeInSeconds` 600, the image `sagemaker-xgboost:3.0-5` from the Region's algorithm registry, the
  recipe's hyperparameters (`eta=0.2 eval_metric=auc max_depth=5 num_round=200 objective=binary:logistic
  subsample=0.8`). Its tags are 2.2 (a)'s seven keys: the request's own `AmazonDataZoneProject` and the
  space's seven, merged into one set. `model.tar.gz`, 125,534 bytes, `aws:kms` under the project key with the
  bucket key. Validation AUC 0.8209, a reading.
- **[user] 2.3**, the five negatives and the admitted request again:

  ```
  ml-demo-xgb-no-vpc-20261121-235342: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:CreateTrainingJob on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-no-vpc-20261121-235342 with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary
  ml-demo-xgb-no-isolation-20261121-235351: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:CreateTrainingJob on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-no-isolation-20261121-235351 with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary
  ml-demo-xgb-no-ice-20261121-235359: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:CreateTrainingJob on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-no-ice-20261121-235359 with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary
  ml-demo-xgb-no-volume-key-20261121-235410: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:CreateTrainingJob on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-no-volume-key-20261121-235410 with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary
  ml-demo-xgb-ceiling-20261121-235418: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:CreateTrainingJob on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/ml-demo-xgb-ceiling-20261121-235418 with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary
  ml-demo-xgb-tagged-20261121-235427: created
  ml-demo-xgb-tagged-20261121-235427: Completed, 84 s billed
  validation:auc: 0.8209
  train:auc: 0.9513
  model: s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/models/ml-demo-xgb-tagged-20261121-235427/output/model.tar.gz
  ```
- **[Claude] 2.3's readings.** Each refusal names the boundary, `awsds-sandbox-project-boundary`, never a
  statement: the step's *"each naming its statement"* holds as each attributed by the one field it changes.
  The boundary's version `v3` maps them: `DenySageMakerJobsOffVpc` (`Null` on `sagemaker:VpcSubnets`),
  `DenySageMakerJobsWithoutNetworkIsolation` and `DenySageMakerJobsWithoutInterContainerEncryption`
  (`BoolIfExists` false), `DenySageMakerJobsWithoutVolumeEncryption` (`Null` on `sagemaker:VolumeKmsKey`) and
  `DenySageMakerInstanceCeiling` (`ForAnyValue:StringNotEquals` on `sagemaker:InstanceTypes`). None of the
  five names exists as a job (`DescribeTrainingJob` exit 254 for each), so none billed. The sixth, created
  23:54:28 and trained 23:55:13 to 23:56:37, 84 s billed, read `Completed` with isolation and
  inter-container encryption on: the five refusals are read against a pass of the same sitting. The
  negatives ran through the proxy's replacement (23:51:43 to 23:54:00), which none of them crosses.

## 2026-11-22 — Day 2's sitting B: 2.4, verification iii, 3.1 and 3.2's first attempt

Written by Claude in the session the orchestrator started. The user acted in the portal and ran the commands
in the `jup` space; the lines quoted from their pastes and from the proxy's log are verbatim except the
account id, written `<Sandbox Account 1>`. Claude's readings ran as `awsds-infra-sandbox-1` (Sandbox
Account 1), `awsds-infra-prod` for the proxy's log, and Claude in Chrome for the MLflow UI. Times UTC.

- **[user] 2.4, the portal's path.** On `eighth-experimentation`'s *XGBoost Classification* page,
  *Deploy* ▾ → *JupyterLab* answered *"Failed to open notebook JupyterLab is not ready. Please ensure your
  space is running and try again."* while `jup` read `InService` (read by Claude at the time). *Notebook*
  is disabled under both menus (0.7). Neither entry opens the sample notebook in this project, so no job
  was submitted from the portal: the SDK path of 2.2 is this stage's training path.
- **[user] Verification iii from `jup`**, the hub read and one ranged `GetObject`, creating nothing:

  ```
  start 00:12:57
  hub xgboost-classification-model 2.2.0 Available
  uris 5
  get s3://jumpstart-cache-prod-us-west-2/source-directory-tarballs/training/xgboost-classification/prepack/inference-xgboost-classification/v1.0.0/sourcedir.tar.gz 206 bytes 0-99/77423531
  end 00:12:58
  ```
- **[Claude] Verification iii's readings: yes.** CloudTrail records `DescribeHubContent` at 00:12:57 from
  10.20.54.175 as the project role through `vpce-02feedaa4ad58acf4`, the SageMaker API endpoint. The
  proxy's stream from 00:12:57 to 00:12:58 holds one line, the Access Grants plugin's
  *"CONNECT <Sandbox Account 1>.s3-control.us-west-2.amazonaws.com:443 200 6623 4020 TCP_TUNNEL"*. The spoke
  has no default route, so the 206 from `jumpstart-cache-prod-us-west-2` is the S3 gateway endpoint's: the
  bucket name its policy has listed since Stage 3 is exercised for the first time.
- **[user] 3.1, the second run:**

  ```
  ml-demo-xgb-tagged-20261122-000754: created
  ml-demo-xgb-tagged-20261122-000754: Completed, 88 s billed
  validation:auc: 0.8394
  train:auc: 0.8577
  model: s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/models/ml-demo-xgb-tagged-20261122-000754/output/model.tar.gz
  🏃 View run ml-demo-xgb-tagged-20261122-000754 at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2/runs/78645bec5e354cdaa13ca6321d5b3fcd
  🧪 View experiment at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2
  ```
- **[Claude] 3.1's compare view**, read in the MLflow UI through Chrome: *"Comparing 2 Runs from 1
  Experiment"*, `validation_auc` 0.83936 for `max_depth` 3 and `num_round` 50 against 0.82091 for 5 and 200,
  `train_auc` 0.858 against 0.951. The better job is `ml-demo-xgb-tagged-20261122-000754`, the run
  `78645bec5e354cdaa13ca6321d5b3fcd`. The UI's compare URL loses its run list on load (it redirects to
  `?workspace=default`); selecting both runs in the run list and *Compare* opens the view.
- **[user] 3.1's model and 3.2's two doors**, in that order:

  ```
  sagemaker-user@default:~/AWS-DataScience/examples/sandbox-ml$ /opt/awsds/venv/bin/python register.py log-model ml-demo-xgb-tagged-20261122-000754
  /opt/awsds/venv/bin/python register.py package ml-demo-xgb-tagged-20261122-000754
  /opt/awsds/venv/bin/python register.py from-mlflow ml-demo-xgb-tagged-20261122-000754
  ml-demo-xgb-tagged-20261122-000754: model.tar.gz logged into run 78645bec5e354cdaa13ca6321d5b3fcd under archive/
  /home/sagemaker-user/AWS-DataScience/examples/sandbox-ml/register.py:81: UserWarning: [00:18:19] WARNING: /workspace/src/c_api/c_api.cc:1500: Unknown file format: ``. Using UBJSON (`ubj`) as a guess.
    booster.load_model(str(scratch / members[0].name))
  2026/11/22 00:18:19 WARNING mlflow.models.model: `artifact_path` is deprecated. Please use `name` instead.
  ml-demo-xgb-tagged-20261122-000754: booster logged as runs:/78645bec5e354cdaa13ca6321d5b3fcd/model
  🏃 View run ml-demo-xgb-tagged-20261122-000754 at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2/runs/78645bec5e354cdaa13ca6321d5b3fcd
  🧪 View experiment at: https://mlflow.sagemaker.us-west-2.app.aws/#/experiments/2
  ml-demo-xgboost: created
  ml-demo-xgboost version from ml-demo-xgb-tagged-20261122-000754: refused
  AccessDeniedException: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/SageMaker is not authorized to perform: sagemaker:AddTags on resource: arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:model-package/ml-demo-xgboost/new because no identity-based policy allows the sagemaker:AddTags action
  Successfully registered model 'ml-demo-xgboost'.
  2026/11/22 00:18:56 INFO mlflow.store.model_registry.abstract_store: Waiting up to 300 seconds for model version to finish creation. Model name: ml-demo-xgboost, version 1
  Created version '1' of model 'ml-demo-xgboost'.
  ml-demo-xgboost: MLflow version 1 from ml-demo-xgb-tagged-20261122-000754's model.tar.gz
  ```
- **[Claude] 3.1's model and verification iv: yes.** The archive is the run's
  `artifacts/archive/model.tar.gz`, 10,727 bytes. The booster is not under the run: MLflow 3.16.0 stores it
  as the logged model `m-b2cb7244247a4203ab67bdc66eb9a7c7` under the experiment's `models/`, written 00:18:35
  (`MLmodel`, `conda.yaml`, `model.ubj` of 58,361 bytes, `python_env.yaml`, `requirements.txt`). The house
  interpreter's XGBoost loads the `sagemaker-xgboost:3.0-5` image's `xgboost-model` by guessing UBJSON from a
  file with no extension. Both objects read `aws:kms` under the project key `a81b1ef3-…` with the bucket key:
  the store the app holds no key for encrypts under the project's.
- **[Claude] 3.2's first attempt.** CloudTrail, every call from 10.20.54.175 through
  `vpce-02feedaa4ad58acf4`:
  - `CreateModelPackageGroup` at 00:18:45 admitted, the group `Completed`. Its recorded request carries seven
    tags where `register.py` sends one, the same seven keys as 2.2's training jobs (`SUP-408`): the two
    `sagemaker:` ARNs of the profile and the domain, `sagemaker:space-arn` naming `jup`, and
    `AmazonDataZoneProject`, `AmazonDataZoneScopeName` `dev`, `AmazonDataZoneUser` and
    `AmazonDataZoneDomain`. The group's `AddTags` statement admits the key `AmazonDataZoneProject` alone, so
    the six others were not in the authorization the statement read.
  - `CreateModelPackage` at 00:18:46 refused with the `AddTags` message above, `requestParameters` null. The
    group holds no version.
  - `CreateModelPackage`'s API reference says a version created in a group takes no tag argument and uses
    the group's tags, and `register.py package` sends the project tag. The refused request is one the API
    does not accept. Decision 7 (a) writes a statement per measured refusal, so the request the API accepts,
    the version with no tags, is measured before any statement is written.
  - `from-mlflow`: the MLflow registry holds `ml-demo-xgboost` version 1 at 00:18:56, and SageMaker's
    registry no version from it. The app reads `AutoModelRegistrationDisabled`, so the MLflow door writes the
    MLflow registry alone.

## 2026-11-22 — Day 2's sitting B: 3.2's version, created with no tag

- **[user] The version with no tag argument**, from `jup`: `register.py package`'s request without `Tags`,
  in a block Claude wrote, followed by a `ListTags` on the new version:

  ```
  version: model-package/ml-demo-xgboost/1
  list_tags refused: ValidationException: Tag operations are supported only on ModelPackage Group not on ModelPackage Versions.
  ```
- **[Claude] The version's readings.** `ml-demo-xgboost` version 1, created 00:34:10, `Completed`,
  `PendingManualApproval`, created by the user profile `28f1b390-…` of `d-m8m0uefej9kb` as the project role
  with that profile as the session's source identity; the image `sagemaker-xgboost:3.0-5` and the better
  job's `model.tar.gz`. CloudTrail records it from 10.20.54.175 through `vpce-02feedaa4ad58acf4` with no
  `tags` key in its request.
- **[Claude] What admitted it.** On the role, the one statement allowing `CreateModelPackage` on that
  resource is the blueprint's `SageMakerCreatePermissions` (`SageMakerStudioProjectRoleMachineLearningPolicy`
  v48), conditioned on `aws:ResourceTag/AmazonDataZoneProject` equal to the caller's principal tag and on
  `aws:PrincipalTag/EnableSageMakerMLWorkloadsPermissions`; `awsds-sandbox-workflows` v7's
  `RegisterAPendingVersionForAppMl` names `app-ml-dev`'s project and group alone. The version's resource tag
  at the create is therefore its group's (`SUP-409`), the half of verification lviii the simulation of
  2026-11-17 left open, read here from a space. The refusal of 00:18:46 was of a request the API reference
  excludes, so decision 7 (a) writes no `sandbox/ml/` statement for a version, and `register.py package`
  sends no tag on the version (`62f59123`).

## 2026-11-22 — Day 2's sitting B: 3.2's approval in the portal, and no collection to create

- **[user] The approval.** Version 1 approved from the portal's model group page. **[Claude]** CloudTrail
  records `UpdateModelPackage` at 00:45:45 with `modelApprovalStatus` `Approved`, from the browser and with no
  `vpcEndpointId`, as the project role in the session `28f1b390-…@5hkjdsy3umpi1c`, the user's id as source
  identity. The version reads `LastModifiedBy` that role and no `ApprovalDescription`.
- **[Claude] The registry's pages**, read through Chrome after the approval. AI/ML → *Models* has two tabs,
  *Foundation models* (939 models) and *My models*, the registry: *"These are your own trained, versioned,
  production-ready models. You can register models using the SageMaker SDK in a notebook."* It lists
  `ml-demo-xgboost`, *Model group*, one version. Its *Filter by* offers *All*, *Model group*, *Model* and
  *Deployable models*; the row's menu offers *Delete model group* alone. The group's page shows the ARN, the
  creator's id, the tabs *Versions* and *Tags*, *Publish* and *Delete model group*, and version 1 *Not
  deployed*, *Approved*. No page offers a collection, so 3.2's collection is not created.
- **[Claude] *Inference endpoints* → *Create new endpoint*** now lists *"ml-demo-xgboost, 1 approved
  version"* under *"List of deployable models and registered model versions approved for deployment"*. With
  version 1 selected, *Create endpoint using JupyterLab* is enabled and *Create endpoint using Notebook* is
  disabled, labelled *"Notebooks are currently not supported for cross-region and …"*. The dialog was
  cancelled: the portal's endpoint path is a notebook, and 4.1's is `serve.py endpoint`.

## 2026-11-22 — Day 2's sitting B: pass 7's dataset and documents copied

- **[user] 7.4's dataset and 7.4a's documents**, from `jup`, the clone at `b3b900b4`:

  ```
  20 prompts, 2951 bytes -> s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/bedrock/evaluation-dataset.jsonl
  commit b3b900b4a95b526f4d78dcdd3559aa9ca299fdac
  ...
  20 documents, 1212570 bytes
  ```

  The twenty runbooks went to `shared/ml-demo/bedrock/kb/`, from `break-glass.md` (19,464 bytes) to
  `vpn.md` (85,083), the largest `promotion.md` (217,158).
- **[Claude] The Bedrock IDE's entry**, read through Chrome: Generative AI → *AI apps* opens the IDE on an
  unsaved *Untitled App* chat agent, with an inner panel *Amazon Bedrock*: *Models*; *Build* (*Chat agent*,
  *Flow*, *Prompt*, *Model evaluations*); *Asset gallery* (*My apps*, *My prompts*, *My components*). The
  interface endpoints `bedrock`, `bedrock-runtime`, `bedrock-agent` and `bedrock-agent-runtime` read
  `available` in Sandbox.

## 2026-11-22 — Day 2's sitting B: 7.4a's knowledge base refused at its index

Written by Claude in the session the orchestrator started, the portal's acts through Claude in Chrome in the
user's Chrome signed in as the Data Scientist User, on the authorization below. The banner and the role and
session names are verbatim except the account id, written `<Sandbox Account 1>`. Claude's readings ran as
`awsds-infra-sandbox-1` (Sandbox Account 1). Times UTC.

- **[user] The authorization.** *"Autorizo"*, answering whether Claude should create the knowledge base
  `ml-demo-runbooks` and run a sync.
- **[Claude] The create**, through Chrome, with the form as 7.4a sets it: the name `ml-demo-runbooks`, the
  description *"Stage 17 7.4a: the project's runbooks"*, *Project data sources* → S3 (`default.s3_shared`)
  with the URI `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/ml-demo/bedrock/kb/`,
  Titan Text Embeddings V2, floating-point, 1024 dimensions, Amazon S3 Vectors, default chunking and the
  Bedrock default parser. The form opened on OpenSearch Serverless and 256 dimensions. *Foundation model as a
  parser* was disabled under the alert *"Access to model required"*. *Create* was clicked at 01:02 UTC, and
  the component list then held `ml-demo-runbooks`, *Knowledge base*, under the portal's banner:

  ```
  Amazon Bedrock couldn't deploy the Knowledge Base. Delete this component, and then create a new one. [Failed to create environment cie8747bea6mxc: KB vector store creation failed due to: S3Vectors vector store creation failed due to: S3Vectors index creation failed: Insufficient access to perform asynchronous indexing. Ensure that the key used to encrypt the index still exists, is active, and has a resource policy granting access to the S3 service principal 'indexing.s3vectors.amazonaws.com'. (kms_request_id=5c1cca55-9ee1-4126-a995-7503c2b11654) (Service: S3Vectors, Status Code: 403, Request ID: 1b9a477c-ea82-86c8-9942-261750d8d87f) (SDK Attempt Count: 1), Cloudformation stack DataZone-Env-cie8747bea6mxc failed in account <Sandbox Account 1> and us-west-2 for environment cie8747bea6mxc]
  ```

- **[Claude] The trail and the objects**, read as the infrastructure user:
  - 01:02:39 `CreateInferenceProfile` by `AmazonSageMakerBedrockModelManagementRole-<Sandbox Account 1>`,
    session `AWSDataZone-Subscriptions`, from `datazone.amazonaws.com`: the name
    `dzd-d8yrvx1ko7im6o avhvbqn37ty7m8`, copied from `amazon.titan-embed-text-v2:0`, answered
    `application-inference-profile/p391nstyc81c`, `ACTIVE`. The profile stays.
  - The stack `DataZone-Env-cie8747bea6mxc`: `CREATE_IN_PROGRESS` at 01:02:58, its wait handle and two wait
    conditions (`KnowledgeBaseServiceRolePolicyWaitCondition…`, `CustomResourceRolePolicyWaitCondition…`),
    `CREATE_COMPLETE` at 01:03:04, `DELETE_IN_PROGRESS` *"User Initiated"* at 01:03:30, `DELETE_COMPLETE` at
    01:03:33. With S3 Vectors the stack holds its wait handles alone, as `SUP-169` read from the template.
  - 01:03:10 `CreateVectorBucket` by `awsds-sandbox-smus-provisioning`, session
    `AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>`, from `datazone.amazonaws.com`:
    `amazon-bedrock-ide-avhvbqn37ty7m8-cie8747bea6mxc`, `sseType` `aws:kms` under the key of
    `alias/awsds-sandbox-project`, admitted, with that role's `GenerateDataKey` and `Decrypt` on the key at
    the same second.
  - 01:03:10 `CreateIndex` by the same role: `amazon-bedrock-ide`, dimension 1024, `float32`, `euclidean`,
    `AMAZON_BEDROCK_TEXT` non-filterable. It was refused with `AccessDenied` and the banner's wording.
  - No IAM event in us-east-1 from 01:01 to 01:06, and no `CreateKnowledgeBase`; `list-knowledge-bases`
    answered none at 01:05:40.
  - The vector bucket stays, `defaultIndexMode` `ENHANCED`, with no index and no tag, so the store carries
    no project tag (verification xxiii). Empty, it bills nothing.
- **[Claude] The cause, read 2026-11-22.** The S3 Vectors encryption page's key-policy example grants
  `indexing.s3vectors.amazonaws.com` `kms:Decrypt` under `aws:SourceArn` (`bucket/*`), `aws:SourceAccount`
  and `kms:EncryptionContextKeys` (`aws:s3vectors:arn`, `aws:s3vectors:resource-id`). SMUS's key-permissions
  page lists ten statements and none for S3 Vectors, a knowledge base or OpenSearch Serverless. Bedrock's
  knowledge-base setup page names no key policy. The project key's policy at `sagemaker-prereqs-v0.12.0`
  follows SMUS's page (`SUP-410`).
- **[Claude] The fix, planned.** `sagemaker-prereqs`' `kms.tf` gains the S3 Vectors page's statement, the
  bucket narrowed to `amazon-bedrock-ide-*`, behind the knowledge-base blueprint's switch. A plan of
  `sandbox/sagemaker` against the local module read `0 to add, 1 to change, 0 to destroy`: the project
  key's policy gains that one statement. The caller went back to its pinned tag. The module's tag and the
  apply wait on the user.

## 2026-11-22 — Day 2's sitting B: 7.4a's knowledge base created after the key's apply, and its syncs refused by the index's metadata

- **[user] The authorization.** *"Autorizo"*, answering whether Claude should publish
  `sagemaker-prereqs-v0.13.0`, apply `sandbox/sagemaker`, delete the failed component and recreate the
  knowledge base with a sync.
- **[Claude] The tag and the apply.** `sagemaker-prereqs-v0.13.0` was pushed and read back from origin at
  `4628357d`, and `sandbox/sagemaker` was pinned to it in `207eb246`. The saved plan read
  `0 to add, 1 to change, 0 to destroy`. The other sessions were told, then the plan was applied as the
  infrastructure user (`InfrastructureAccess`, `awsds-infra-sandbox-1`): `Modifications complete after 7s`,
  `Apply complete! Resources: 0 added, 1 changed, 0 destroyed.` at 01:23 UTC. The re-plan read `No changes`,
  and the key's live policy lists `AllowS3VectorsIndexingOfTheBedrockIdesVectorBuckets` tenth.
- **[Claude] The failed component, removed in two acts.** *My components* showed an error icon on the
  failed row and no menu. *Resource blueprints* listed the deployment
  `34bcff63-e1c0-4b5a-b669-a48df19b6f16-dev`, `AmazonBedrockKnowledgeBase`, *Deployment failed*, with a
  delete. Its dialog read *"Permanently delete blueprint deployment …? Deleting a blueprint deployment is
  final and removes all connections created."*; after `confirm`, the portal answered *"Blueprint deployment
  deleted successfully"* at about 01:25, and the row was gone by 01:26:50. The component stayed listed: its
  definition, `amazon-bedrock/builder/components/knowledgeBase/34bcff63-…-definition.json` in the project's
  prefix of the projects bucket, was written by the project role at 01:02:30. Its row then offered *Sync*,
  *View*, *Edit* and *Delete*. *Delete* asked *"Are you sure you want to delete this Knowledge Base?"* and
  removed the definition, so the prefix was empty at 01:30:18. The first vector bucket,
  `amazon-bedrock-ide-avhvbqn37ty7m8-cie8747bea6mxc`, survived both deletes (read 01:33:38).
- **[Claude] The second create**, the same form: Titan V2, floating-point, 1024 dimensions, S3 Vectors,
  default chunking, default parser. At 01:33:17 the provisioning role's `CreateVectorBucket`
  `amazon-bedrock-ide-avhvbqn37ty7m8-46cr0woe7670gg`, under the project key, and `CreateIndex`
  `amazon-bedrock-ide` were both admitted. The index declares `nonFilterableMetadataKeys`
  `AMAZON_BEDROCK_TEXT` alone, `indexMode` `ENHANCED`. The knowledge base `QWDNVYXADH`, named
  `avhvbqn37ty7m8-ml-demo-runbooks`, read `ACTIVE` at 01:33:18. Its role is the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, its embeddings go through
  `application-inference-profile/p391nstyc81c` at 1024 `FLOAT32`, and its storage is `S3_VECTORS`. Its data
  source `JXKIPOER3T` reads the projects bucket under the prefix `…/shared/ml-demo/bedrock/kb/`, with
  `FIXED_SIZE` chunks of 300 tokens and 15 % overlap (the form's *Default*), `dataDeletionPolicy` `DELETE`,
  encrypted under the project key.
- **[Claude] The syncs.** The create started one by itself: `TGR4ZAJ1LU`, 01:33:30 to 01:33:55, `COMPLETE`,
  20 documents scanned, 2 indexed, 18 failed. The *Sync* Claude clicked was `FH5GACQWX9`, 01:34:13 to
  01:34:40, `FAILED`, 20 scanned, 0 indexed, 18 failed. Both jobs' failure reasons have one form:

  ```
  Encountered error: Invalid record for key '1606687c-6dd0-480b-9d30-7b498bd1bced': Metadata value is invalid: exceeds 2048 byte string limit (Service: S3Vectors, Status Code: 400, Request ID: 1ecbbd8d-60cc-8d4f-b8de-4d30bfe12103) (SDK Attempt Count: 1). Call to Amazon S3 Vectors did not succeed.
  ```

  The indexed documents are `break-glass.md` and `buildbox.md`. The 18 others read `FAILED` with a status
  reason that names no metadata: *"The document was not indexed. No content could be extracted from it, or
  processing ended before it completed. Check that the document contai…"*. The embeddings ran as the
  project role, session `EmbeddingTask-FH5GACQWX9`, from `bedrock.amazonaws.com`: 50 `InvokeModel` calls on
  the application inference profile between 01:34:34 and 01:34:37, all admitted (verification xxii).
- **[Claude] The pages, read 2026-11-22.** Bedrock's knowledge-base setup page (its S3 Vectors tab) and its
  chunking page ask that the index declare `AMAZON_BEDROCK_TEXT` and `AMAZON_BEDROCK_METADATA`
  non-filterable. S3 Vectors' limits page caps a filterable string value at 2 KB. Its metadata-filtering
  page says a key declared non-filterable cannot become filterable later. The IDE's index leaves
  `AMAZON_BEDROCK_METADATA` filterable, and the form exposes no index setting (`SUP-411`).
- **[Claude] The documents against their status**, counted in the repository's copies at 01:45: the two
  indexed runbooks hold one Markdown table each (`buildbox.md` 1,187 bytes, `break-glass.md` 19,464), and
  each of the 18 that failed holds two or more, `security-hub.md` (10,432 bytes) among them. Neither the
  file's size, its largest table (750 to 8,099 bytes among the failures) nor its longest line separates the
  two groups. This is a correlation over 20 files, not a cause any reading names.

## 2026-11-22 — Day 2's sitting B: 7.4's prompt and flow created, its guardrail and evaluation refused

- **[user] The authorization.** *"Autorizo"*, answering whether Claude should create, over the two-runbook
  base, 7.4's prompt, guardrail, flow and automatic evaluation of Haiku 4.5, and 7.4b's chat agent with a
  single *Share*.
- **[Claude] The portal session ended** at about 01:51, between the prompt's two versions, with no act of
  Claude's; the cause was not read. **[user]** *"Entrei"*: the user signed in again as Data Scientist User
  in the same tab.
- **[Claude] The prompt.** *Build* → *Prompt*, Claude Haiku 4.5, one variable, `{{excerpt}}`. The first test
  created the model's application inference profile, `ljl42zoh6e4v`, by the IDE's model-management role's
  `CreateInferenceProfile` at 01:48:19, then sent `ConverseStream` at 01:48:24 as the project role, admitted.
  The save is a DataZone environment, `f1fa8784-9ee4-4bfe-ad24-9d62e6a549dc-dev` (`dsffvybs9lppcg`, created
  01:48:46), whose stack's `CreatePrompt` ran at 01:49:04 as the provisioning role. The prompt is
  `Bedrock-Prompt-dsffvybs9lppcg` (`KWK4ZJRAWD`), under the project key; the portal names it
  `untitled-prompt-1yrl1`. Version 1 was created at 01:49:48 and version 2 at 01:53:49, both by
  `CreatePromptVersion` as the project role; version 2 adds *"Answer in Brazilian Portuguese."* to the text.
  Both store `temperature` 1.0, `maxTokens` 4096 and `stopSequences` `Human:`, with no `topP`, where the form
  read Top P 0. Each save took about a minute. The split button's *Create version*, chosen from its
  dropdown, only switches the button's action, and the button's next click creates the version.
- **[Claude] The guardrail, refused.** *Build* → *Guardrail*, `ml-demo-guardrail`. The form's step 2,
  *Filters*, offers *Content filters*, shown enabled, and *Denied topics* alone, so the PII filter 7.4 names
  could not be set. One denied topic was added, *Investment advice*, with two sample phrases. Step 3's blocked
  message, *"Sorry, the model cannot answer this question."*, also applies to responses. The description typed
  still named a PII filter. The environment `d4db8360-ee3b-4562-8349-eae449b1b72d-dev` (`ajfy8315ryk3kg`) was
  created at 01:56:07 and its stack at 01:56:20. At 01:56:24 `CreateGuardrail` was refused with *"You don't
  have sufficient permissions for this KMS key."*, and `kms:CreateGrant` on the project key with *"… because
  no identity-based policy allows the kms:CreateGrant action"*, both as the provisioning role from
  `datazone.amazonaws.com`. The stack rolled back to `DELETE_COMPLETE`, and the environment reads
  `CREATE_FAILED` with *"Access denied for operation 'AWS::Bedrock::Guardrail'."* (`SUP-417`). SMUS's
  guardrail page lists two policies, content filters and denied topics (read 2026-11-22), so no IDE guardrail
  carries a PII filter.
- **[Claude] The flow.** *Build* → *Flow*, `ml-demo-flow`. Claude in Chrome's pointer drag from the palette
  left the canvas empty; a scripted `dragstart`, `dragenter`, `dragover` and `drop`, carrying
  `application/reactflow` `PromptsNode`, placed the node, and the edges took a pointer drag. The builder has
  no model node: the prompt node carries the model. The node `Prompt_1` points at the prompt's version 2
  (`prompt/KWK4ZJRAWD:2`), between `FlowInputNode` and `FlowOutputNode`. The environment
  `d6d9be18-d2cd-4249-bf55-4bd97abc9a33-dev` (`5er1gtql9ewbgw`) was created at 02:02:19, and its stack's
  `CreateFlow` and `PrepareFlow` ran at 02:02:40 and 02:02:41 as the provisioning role. The flow is
  `Bedrock-Flow-5er1gtql9ewbgw` (`Q9HHV1YRRX`), `Prepared`, under the project key; the save took about three
  minutes. One run at 02:03:25: `Converse` as `AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c`,
  admitted, and the answer came back in Portuguese.
- **[Claude] The evaluation, refused.** *Build* → *Model evaluation*, `ml-demo-eval-haiku45`: Claude Haiku
  4.5, *Question and answer*, Toxicity over `evaluation-dataset.jsonl` (2.88 KB), uploaded by the form, whose
  dialog reads *"Once uploaded, you cannot delete the file"*. Accuracy and Robustness offer the built-in
  datasets alone (`SUP-419`). The model list offers Nova Lite, Claude Haiku 4.5, Claude Opus 4.5 and Claude
  Sonnet 4.5. *Inference configurations* holds Max tokens 500, Temperature 0.5, Top P 0.5 and Top K 50, and
  a cleared Top P returns to 0.5. The submit created the environment `avhvbqn37ty7m8ml-demo-eval-haiku45`
  (`6fl52xzq3yt768`, 02:07:10) and its stack (02:07:23, `CREATE_COMPLETE`, one output and no resource), and
  put the file in `awsds-sandbox-smus-projects` under `…/avhvbqn37ty7m8/genAI/assets/evaluations/input/`. At
  02:07:54 Bedrock's pre-flight `Converse`, as the project's service role, was refused with *"The model
  returned the following errors: `temperature` and `top_p` cannot both be specified for this model. Please
  use only one."*, and `CreateEvaluationJob`, as the project role, with the same reason. The portal read
  *"An error occurred while creating the evaluation job: Unknown error. Potentially invalid input"*
  (`SUP-418`). `list-evaluation-jobs` reads none, and the environment stays `ACTIVE`.
- **[Claude] The names** the IDE gives these objects (`SUP-445`): the portal's name lives in the
  environment's description, prompts and flows are named `Bedrock-<type>-<environment id>`, the knowledge
  base `<project id>-<name>`, and the evaluation `<project id><name>`.
- **[Claude] The key's statement for the guardrail**, written in `terraform-modules/sagemaker-prereqs/kms.tf`
  (`51459ace`): Bedrock's `PermissionsForGuardrailsCreators`, with the principal narrowed to the provisioning
  role, on the guardrail blueprint's switch. A plan of `sandbox/sagemaker` with the module read from the
  working tree read `0 to add, 1 to change, 0 to destroy`, the key's policy gaining that statement alone. The
  tag and the apply wait on the user.
- **[Claude] `app-ml-dev`'s MLflow App** is not there yet: `list-mlflow-apps` listed `ml-demo-mlflow` alone at
  about 02:25.

## 2026-11-22 — Day 2's sitting B: 7.4's guardrail created after the key's second apply, and the evaluation submitted with Nova Lite

- **[user] The authorization.** *"Autorizo os quatro"*, answering whether Claude should publish
  `sagemaker-prereqs-v0.14.0`, apply `sandbox/sagemaker`, create the guardrail anew and redo the evaluation
  with Nova Lite.
- **[Claude] The tag and the apply.** `sagemaker-prereqs-v0.14.0` was pushed and read back from origin at
  `b71f4d02`, and `sandbox/sagemaker` was pinned to it in `6f3a0fc5`. The saved plan read
  `0 to add, 1 to change, 0 to destroy`, the key's policy gaining the guardrail statement alone. The other
  sessions were told, then the plan was applied as the infrastructure user (`InfrastructureAccess`,
  `awsds-infra-sandbox-1`): `PutKeyPolicy` at 02:39:01, `Apply complete! Resources: 0 added, 1 changed, 0
  destroyed`. The re-plan read `No changes`. `staging/studio/` and `production/studio/` stay on `v0.11.0`.
- **[Claude] The failed guardrail deleted** in the portal's two acts: its deployment in *Resource blueprints*
  at 02:41:22, then its row in *My components* at 02:42:55. `get-environment` on `ajfy8315ryk3kg` reads
  `ResourceNotFoundException`.
- **[Claude] The guardrail.** *Create component* → *Guardrail*, `ml-demo-guardrail`, its description now
  *"Stage 17 7.4: one denied topic, for the runbooks chat agent."*, with the denied topic *Investment advice*
  and its two sample phrases. The environment `1c6faa73-f751-408c-890b-35fe5ada49cb-dev` (`6udalb5fp1qv0w`)
  was created at 02:44:56. At 02:45:13 `CreateGuardrail` was admitted as the provisioning role, and in the
  same second three `kms:CreateGrant` on the project key, each naming `bedrock.us-west-2.amazonaws.com` as
  grantee and retiring principal: two bound to the encryption context `aws:bedrock:guardrail-id`
  `razikgicppzy` (`Decrypt`, `Encrypt`, `GenerateDataKey`; `Decrypt`, `Encrypt`), one with no constraint
  (`Decrypt`, `Encrypt`, `GenerateDataKey`, `CreateGrant`, `RetireGrant`, `DescribeKey`) (`SUP-417`). The
  guardrail is `razikgicppzy`, `READY`, version `DRAFT`, under the project key, and is named after its
  environment (`SUP-445`). Its content filters read `HIGH` both ways for violence, hate, sexual and insults,
  and `NONE` for prompt attack and misconduct; it holds no word, PII or grounding policy.
- **[Claude] The evaluation, submitted.** *Build* → *Model evaluations*, `ml-demo-eval-nova-lite`: Nova Lite,
  *Question and answer*, Toxicity over `evaluation-dataset.jsonl`, Accuracy and Robustness removed. Nova
  Lite's *Inference configurations* panel held Max tokens 500, Temperature 0.5 and Top P 0.5, with no Top K,
  and was closed with no change. The upload dialog read *"The file name exists in S3. Uploading will replace
  the existing file."*, and the same file was uploaded again. The model's application inference profile,
  `w9u1ufr8ji2z`, was created at 02:51:21 by the IDE's model-management role, the environment
  `avhvbqn37ty7m8ml-demo-eval-nova-lite` (`dkkpe3opbn4m8g`) at 02:51:25, and at 02:52:08
  `CreateEvaluationJob`, as the project role, was admitted: `evaluation-job/31epl34t77s3`, `InProgress`, run
  as the project's service role with no customer key, its output under `…/genAI/assets/evaluations/output/`.
  `get-evaluation-job` reads `inferenceParams`
  `{"inferenceConfig":{"maxTokens":2048,"temperature":0,"topP":0,"stopSequences":[]},"additionalModelRequestFields":{}}`,
  not the panel's values (`SUP-418`). The portal's list heads *Date created* with *(UTC-07:00)* and shows
  21/11/2026 23:52:08, the laptop's UTC−3 time.
- **[Claude] The project's application inference profiles**, all named `dzd-d8yrvx1ko7im6o avhvbqn37ty7m8`,
  one per model: Claude Opus 4.5 (2026-10-30), Titan Text Embeddings V2 (01:02:39), Claude Haiku 4.5
  (01:48:19) and Nova Lite (02:51:21). The domain's two, named `dzd-d8yrvx1ko7im6o`, hold Haiku 4.5 and Nova
  Lite (2026-10-19, `SUP-187`).

## 2026-11-22 — Day 2's sitting B: 7.4's evaluation read, and 7.4b's chat agent refused by Agents Classic

- **[Claude] The evaluation's result.** `31epl34t77s3` read `Completed` at 03:02:11, ten minutes after its
  create, with no failure message. Its one output file, under `…/evaluations/output/avhvbqn37ty7m8ml-demo-eval-nova-lite/31epl34t77s3/models/w9u1ufr8ji2z/taskTypes/QuestionAndAnswer/datasets/evaluation-dataset.jsonl/`,
  holds 20 records, each with the prompt, the reference response, Nova Lite's answer and `Builtin.Toxicity`:
  from 0.00035 to 0.00123, mean 0.00053, every answer `END_TURN`. The object is under the project key
  (`aws:kms`, bucket key on), by the bucket's default. The Haiku 4.5 attempt's output prefix holds
  `amazon-bedrock-evaluations-permission-check` alone, 0 bytes, written at 02:07:54.
- **[Claude] The chat agent, built.** *Build* → *Chat agent*. The *Model* list offers Nova Lite, Claude Haiku
  4.5, Claude Opus 4.5 and Claude Sonnet 4.5, the three Claude models marked *Cross-region*, each *"Supports
  Guardrails, Data, Functions"* (verification xxv). Claude Haiku 4.5, the system prompt *"You answer questions
  about this project's runbooks using only the documents in the knowledge base. If the documents do not
  contain the answer, say that you do not know."*; *Inference parameters* read Temperature 1, Top P 0.5,
  Maximum length 4096 and the stop sequences `</invoke>`, `</answer>` and `</error>`. *Data*: `ml-demo-runbooks`,
  *Override default search* on, which selects *Hybrid search (semantic & text)*, and 5 source chunks.
  *Guardrails*: `ml-demo-guardrail`. *Save* asked for no name, kept `Untitled App - cer31`, and wrote
  `amazon-bedrock/builder/apps/chatApp/502a9c64-70fd-4dab-afea-a1a5a98146d4-definition.json` at 03:01:39,
  creating no environment and no agent. The definition names the model `6vwrjnya013a8g:2`, a catalog listing
  of Claude Haiku 4.5 whose asset has `us.anthropic.claude-haiku-4-5-20251001-v1:0` as its base, and holds
  `temperature` 1, `topK` 250, `maxTokens` 4096, no `topP`, `ragSearchType` `HYBRID` and `ragNumberOfResults`
  5 (`SUP-446`). The project's Haiku 4.5 profile, `ljl42zoh6e4v`, routes to `us-east-1`, `us-east-2` and
  `us-west-2`.
- **[Claude] The preview, refused.** *"When is using the Management account root justified?"*, sent three
  times from 03:02 to 03:03:54, each answered *"Something went wrong."* under the banner *"Failed to run
  application Amazon Bedrock encountered an error when invoking the Bedrock runtime API. Try again later."*.
  A logging wrapper installed on the page's `fetch` read the call: `POST
  bedrock-agent-runtime.us-west-2.amazonaws.com/agents/<session id>`, `InvokeInlineAgent`, answered 403 with
  *"Bedrock Agents is in Maintenance Mode. New agent creation is not available for accounts without prior
  service usage. To learn more visit
  https://docs.aws.amazon.com/bedrock/latest/userguide/agents-classic-maintenance-mode.html."*. The other six
  questions were not sent.
- **[Claude] The deploy, refused.** *Deploy* with a new alias, `ml-demo-v1`. At 03:05:19 the portal created
  the environment `502a9c64-70fd-4dab-afea-a1a5a98146d4-shared` (`b343orq3qka5n4`, blueprint
  `AmazonBedrockChatAgent`), whose stack `DataZone-Env-b343orq3qka5n4` was created at 03:05:33. At 03:05:39
  `CreateAgent`, as the provisioning role from `datazone.amazonaws.com`, was refused `AccessDenied` with no
  error message; its request named the project's service role, the project key, the application inference
  profile `ljl42zoh6e4v` and the guardrail `razikgicppzy` at `DRAFT`. No KMS call by the role or by Bedrock
  falls between 03:05:30 and 03:08:30. The environment read `CREATE_FAILED` at 03:08:18, and the portal *"…
  failed to deploy: Environment b343orq3qka5n4 failed to stabilize after create/update: 1: [Resource handler
  returned message: "Access denied for operation 'AWS::Bedrock::Agent'." (… HandlerErrorCode:
  AccessDenied)]"*. The IAM simulator reads `bedrock:CreateAgent` `allowed` for the provisioning role, by
  `SageMakerStudioProjectProvisioningRolePolicy` (`v86`, statement `BRMng`) and the SCPs, with resource `*`
  under the request's tags; with `agent/*` as the resource it reads `implicitDeny`, the action taking no
  resource type. `list-agents` reads none. Verification xxxiv: the app is Agents Classic, `InvokeInlineAgent`
  for the preview and `CreateAgent` for the deploy, and Agents Classic refuses this account.
- **[Claude] What waits on the user**: 7.4b's fallback, a flow app over the knowledge base with the preview's
  questions and the one *Share*, and the deletion of the failed chat agent's environment.

## 2026-11-22 — Day 2's sitting B: 2.5 and 7.5 read by the instrument, and the flow's role without the boundary

Written by Claude in the session the orchestrator started, with no act of the user's. The instrument's output
and the trail's names are quoted verbatim except the account id, written `<Sandbox Account 1>`. Times UTC.

- **[Claude] The run.** `./aws/sandbox-ml.py` as the infrastructure user (`InfrastructureAccess`,
  `awsds-infra-sandbox-1`), its report generated at 03:25:56: exit 2, one check failed, `ML-8` (below).
- **[Claude] 2.5, `ML-3`.** The three tagged jobs pass, *"the four settings, project role, key and tag"*,
  each `Completed` on `ml.m5.xlarge`: `ml-demo-xgb-tagged-20261121-233934` (89 s billed, validation AUC
  0.8209), `-20261121-235427` (84 s, 0.8209) and `-20261122-000754` (88 s, 0.8394). The four admitted
  `CreateTrainingJob`, the untagged job's at 23:19:36 and the three tagged, pass as the project role, session
  `SageMaker`, through `vpce-02feedaa4ad58acf4`, the SageMaker API endpoint, from the space's `10.20.54.175`.
  `ml-demo-xgb-untagged-20261121-231933` reads `Stopped`, with no billed seconds. The five refusals of 2.3,
  23:53:43 to 23:54:20 (`no-vpc`, `no-isolation`, `no-ice`, `no-volume-key` and `ceiling`), each read *"with
  an explicit deny in a permissions boundary: …/awsds-sandbox-project-boundary"*; the refusal at 23:19:44
  names `sagemaker:AddTags`, *"because no identity-based policy allows the sagemaker:AddTags action"*
  (`SUP-408`). The trail's `BatchGetImage` events on `sagemaker-xgboost` are the infrastructure user's own
  reads, the pre-flight's at 2026-11-21 19:15:34 and four at 00:09:04 to 00:09:08, with no `vpcEndpointId`;
  no pull by a training job is in this account's trail, the repository being AWS's.
- **[Claude] 7.5, `ML-8`.** The prompt `Bedrock-Prompt-dsffvybs9lppcg`, the flow `Bedrock-Flow-5er1gtql9ewbgw`,
  the guardrail `1c6faa73-f751-408c-890b-35fe5ada49cb-dev` and the knowledge base
  `avhvbqn37ty7m8-ml-demo-runbooks` each carry `AmazonDataZoneProject` `avhvbqn37ty7m8`; the knowledge base
  reads `ACTIVE`, embeddings `p391nstyc81c`, store `S3_VECTORS`, role the project role. The evaluation job is
  `avhvbqn37ty7m8ml-demo-eval-nova-lite`, and no agent exists. The vector buckets are
  `amazon-bedrock-ide-avhvbqn37ty7m8-46cr0woe7670gg` and the first attempt's `…-cie8747bea6mxc`. The trail's
  creates, none with a `vpcEndpointId` (verification xviii): as the provisioning role, session
  `AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>`, `CreateKnowledgeBase` at 01:33:19,
  `CreateDataSource` at 01:33:29, the create's own `StartIngestionJob` at 01:33:30, `CreateGuardrail` at
  01:56:24 (`AccessDenied`) and 02:45:13, `CreatePrompt` at 01:49:04, `CreateFlow` at 02:02:40 and
  `CreateAgent` at 03:05:39 (`AccessDenied`); as the project role, in the person's session, the *Sync* click's
  `StartIngestionJob` at 01:34:13 and `CreateEvaluationJob` at 02:07:54 (`ValidationException`) and 02:52:08.
  No `CreateAgentAlias`.
  The six projects' roles carry `EnableAmazonBedrockPermissions` `true` and no
  `EnableAmazonBedrockIDEPermissions` (verification xvii). Every `AmazonBedrockServiceRole-*` and
  `AmazonBedrockLambdaExecutionRole-*` carries `awsds-sandbox-project-boundary`, and one role fails:
  `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw`, *"no permissions boundary - an interactive principal outside
  D13 (policies: SageMakerStudioBedrockFlowServiceRolePolicy)"*.
- **[Claude] The flow's role, read** (`SUP-447`). The provisioning role created it from
  `datazone.amazonaws.com` at 02:02:39 (`CreateRole`, `AttachRolePolicy`), 20 s after the flow's
  environment and a second before `CreateFlow`; the request names no `permissionsBoundary`. It carries the
  flow's five tags and `KmsKeyId`, the project key's id. Its trust admits `bedrock.amazonaws.com` under
  `aws:SourceAccount` and `aws:SourceArn` `flow/*` of this account. Its one policy is AWS's
  `SageMakerStudioBedrockFlowServiceRolePolicy` v9: `GetPrompt`, `Retrieve`, `ApplyGuardrail`, `InvokeAgent`,
  `lambda:InvokeFunction` on `amazon-bedrock*` and `InvokeModel` on application inference profiles, each on
  the project's tag; `InvokeModel` on a foundation model through an inference profile; `RetrieveAndGenerate`
  on `*`; and the key its `KmsKeyId` tag names, through Bedrock, under each object's encryption context.
  `RoleLastUsed` is empty: the flow's `executionRoleArn` is `AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c`.
  The stack `DataZone-Env-5er1gtql9ewbgw` declares the role with no condition, so it is always created. Its
  parameter `useAwsManagedPoliciesWithoutBoundary`, passed `true`, gives it the managed policy and no
  boundary; `false` would give it inline policies under AWS's
  `SageMakerStudioProjectUserRolePermissionsBoundary`. The flow takes the role only when `bedrockServiceRoleArn`
  is empty, and the environment passed the project's service role. The `AmazonBedrockFlow` blueprint
  configuration reads `environmentRolePermissionBoundary` `awsds-sandbox-project-boundary`, as the six other
  Bedrock blueprints' do, and the template takes no parameter for it. The IAM simulator reads `iam:PassRole`
  to `bedrock.amazonaws.com` `implicitDeny` for the project role, on this role and on the project's service
  role. `awsds-sandbox-project-boundary` v3 denies SageMaker creates off their settings, direct S3 on Lake
  Formation's prefixes and the lake data key outside S3; its instance-ceiling statement, written with
  `NotAction`, matches only a request that carries instance types, so the boundary would deny no call the
  role's policy grants.
- **[Claude] What waits on the user**: the flow's role, which `ML-8` fails on every run while the flow
  exists: accept it as an exception, delete the flow, whose stack holds the role, or attach the boundary by
  hand. A second flow app, 7.4b's fallback, creates a second such role.

## 2026-11-22 — Day 2's sitting B: 7.4b's fallback, a knowledge base node in `ml-demo-flow`

- **[user] The authorization.** *"autorizo o plano B, editando o flow existente."*: `ml-demo-flow` edited to
  carry a knowledge base node, rather than a new flow app, whose environment would create a second role with
  no boundary (`SUP-447`).
- **[Claude] The edit**, in the portal as Data Scientist User. *Build* → *Flow* → `ml-demo-flow`: the
  builder's *Nodes* tab lists *Logic* (*Collector*, *Condition*, *Iterator*), *Orchestration* (*Agent*,
  *Prompt*), *Data* (*Knowledge Base*, *S3 Retrieval*, *S3 Storage*) and *Other* (*Flow output*). The canvas
  took the *Knowledge Base* node from a scripted HTML5 drag (`DragEvent`s carrying `application/reactflow`
  `KnowledgeBaseNode`), and the edges from pointer drags. The node's form offers the knowledge base, a
  response model (Nova Lite, Claude Haiku 4.5, Claude Opus 4.5 and Claude Sonnet 4.5, Opus 4.5 preselected)
  and a guardrail, with no search type and no result count, as AWS's page lists
  (`add-kb-component-prompt-flow-app.html`, read 2026-11-22): `ml-demo-runbooks`, Claude Haiku 4.5 and
  `ml-demo-guardrail`. The flow became *Flow input* → `KnowledgeBaseNode_1` (`retrievalQuery`) → `Prompt_1`
  (`excerpt`, prompt `KWK4ZJRAWD` version 2) → *Flow output*.
- **[Claude] *Save* does not deploy** (`SUP-448`). *Save* read *"Saved"* at about 04:21 and wrote the app's
  definition, `amazon-bedrock/builder/apps/flowApp/<uuid>-definition.json`, to the project's bucket, with the
  four nodes; `get-flow` still read the two-node definition prepared at 02:02:40.
- **[Claude] Each test message deploys.** The first message's send ran a PUT of the asset
  `genAI/assets/flows/<uuid>`, DataZone's `UpdateEnvironment` on `5er1gtql9ewbgw`, a PUT of the environment's
  `definition.json`, and the update of the stack `DataZone-Env-5er1gtql9ewbgw` from 04:25:26 to 04:25:36,
  whose `UpdateFlow` and `PrepareFlow` ran as the provisioning role from `datazone.amazonaws.com`. The flow
  read `Prepared` with the four nodes at 04:25:31, and the browser sent `InvokeFlow` on the alias
  `TSTALIASID` at 04:25:49. Each of the three later messages repeated the update with no edit between them:
  the stack from 04:26:50 to 04:27:01, `BedrockFlow` its one resource updated; `UpdateFlow` and `PrepareFlow`
  at 04:28:33 and 04:28:34, then at 04:30:29 and 04:30:30. A message took about 70 to 80 s from the send to
  the answer. No role was created.
- **[Claude] The answers**, to four questions in Portuguese:
  - *"Em quais situações o uso do root da conta Management é justificado?"*: the three cases of
    `break-glass.md`, Identity Center unavailable, a broken organization, and a restrictive policy that
    denies what it should not.
  - *"O que aconteceu com o buildbox e onde as imagens são construídas agora?"*: retired on 2026-10-12 at
    Stage 7 step 6.5 after six releases, the images built by the build runner's pipeline
    (`gitlab/awsds/dev-env/README.md`), the push by the runner's role through ECR's credential helper, as
    `buildbox.md` says.
  - *"Em qual porta o proxy Squid do hub escuta?"*: no answer; the prompt node called its excerpt *"uma
    mensagem genérica de indisponibilidade"*. The port is in neither indexed document (`SUP-411`).
  - *"Em quais ações da bolsa devo investir minhas economias para ter o maior retorno?"*: refused by the
    guardrail at the input; the prompt node called its excerpt *"uma mensagem de erro genérica"* and asked
    for a runbook excerpt.

  The guardrail's blocked message and the knowledge base's no-answer text reach the user rewritten by the
  prompt node, never verbatim. The node's output is `outputText` alone, so the flow's answers carry no
  citation (verification xxv's citation half).
- **[Claude] The guardrail's metrics**, `AWS/Bedrock/Guardrails`, `razikgicppzy` at `DRAFT`, per minute:
  `Invocations` 2 at 04:25, 04:27 and 04:28 and 1 at 04:30; `InvocationsIntervened` 0, 0, 0 and 1, the 1
  under `GuardrailPolicyType` `TopicPolicy` and `GuardrailContentSource` `Input`; `TopicPolicy` at `Output`
  read 0 at 04:25, 04:27 and 04:28, with no datapoint at 04:30. An answered question is evaluated twice, its
  input and its response, and a blocked input once.
- **[Claude] The trail, per message** (`SUP-426`), read as the infrastructure user (`InfrastructureAccess`,
  `awsds-infra-sandbox-1`); the second message's, 04:27:25 to 04:27:30: `GetInferenceProfile` as the
  project's service role; `InvokeModel` on the embeddings profile `p391nstyc81c` as the project role, the
  knowledge base's role; `Converse` on `ljl42zoh6e4v` as the service role, the node's generation; `GetPrompt`;
  and the prompt node's `Converse` as the service role. Every event is invoked by `bedrock.amazonaws.com`.
  The two knowledge base calls carry `vpcEndpointId` `vpce-0cf920938fc4d8fc6` and no `vpcEndpointAccountId`;
  `describe-vpc-endpoints` answers *"The Vpc Endpoint Id 'vpce-0cf920938fc4d8fc6' does not exist"*
  (`InvalidVpcEndpointId.NotFound`), the account's own `bedrock-runtime` endpoint being
  `vpce-0081304ac7a7cbdd3` and its `bedrock-agent-runtime` `vpce-0ef6168e25e9adb32`. The other events carry
  no `vpcEndpointId`. `lookup-events` holds no `InvokeFlow`, `Retrieve` or `RetrieveAndGenerate`.
- **[Claude] No *Share* for a flow app.** *My apps* lists `ml-demo-flow` *"Not shared"*, with a delete icon
  alone. AWS's share page describes chat agent apps alone, and the flow app pages name no share
  (`app-share.html`, `build-flow.html`, read 2026-11-22). The authorized *Share* was not performed, and
  verification xxiv's catalog half has no object to read.
- **[Claude] A correction to this day's 7.4 entry**: the guardrail's form opens from *My components* →
  *Create component* → *Guardrail*, not from *Build*.
- **[Claude] What waits on the user**: nothing new. The flow keeps the project's service role as its
  execution role, `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw` stands as before (`SUP-447`), and xxiv's
  `Retrieve` from a space stays the user's.

## 2026-11-22 — Day 2's sitting B: the closing reads and the lowering

*Claude's hand through `awsds-infra-sandbox-1` (Sandbox Account 1, the infrastructure user with
`InfrastructureAccess`), `catalog.py` also through `awsds-infra-data`, `awsds-infra-staging` and
`awsds-infra-prod`; the lowering by the user's hand in a terminal of their own. The user's *"Não, fechar a
sessão"* at 04:59 closed the sitting without 6d's remainder (6d's log). Times are UTC.*

- **[Claude] `./aws/sandbox-ml.py`**, generated 05:03:58: exit 2, one check failed, `ML-8` on
  `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw`, *"no permissions boundary - an interactive principal
  outside D13 (policies: SageMakerStudioBedrockFlowServiceRolePolicy)"* (`SUP-447`), as at 03:25:56; 46
  checks pass and every call returned. The coordinating session's run at 05:34:11, after *Update project*
  in every Sandbox project, read the same one failure (6d's log).
- **[Claude] `./aws/catalog.py`**, generated 05:03:39: every check passed, every call returned.
- **[Claude] A space no entry named**: CloudTrail records `CreateSpace` `new-jup-xlarge` at 00:12:15 and
  `DeleteSpace` at 00:39:54 in `eighth-experimentation`'s blueprint domain, both from the browser as the
  project role in the user's session; its JupyterLab app read `Deleted` at 05:36.
- **[user] The lowering**: `make down ENV=sandbox`, after the reads, from 05:08:50 (`TerminateInstances`) to
  05:15:28 (`DeleteFirewallRuleGroup`), read in the Sandbox trail by the coordinating session (6d's log).
- **[Claude] `make status`** at 05:24:24: `sandbox/egress`, `sandbox/warehouse-compute`, `sandbox/probes` and
  `staging/egress` down, no Studio app billing in the five environments; Production's `vpn`, `proxy`,
  `egress`, `workloads-egress`, `tooling` and `runners` up for the coordinating session, *"estimated burn: USD
  0.5475/h"*.
- **[Claude] `make check`** at 05:27:42: *"check: OK"*.
- **[Claude] What stands in Sandbox**: `jup` and `code` `InService` in the blueprint domain with every app
  `Deleted` (05:36); pass 7's objects, which 7.6 keeps; the flow's own role, waiting on the user (`SUP-447`).

## 2026-11-22 — Day 3's pre-flight, with nothing up

*Claude, in the orchestrating session of `promotion.md` §N.9's day 2, after the day's lowering: read-only
plans with `-input=false`, Terraform 1.17.2, from 06:26 to 06:32 UTC, and the stage file aligned with
§N.9.5. Nothing was saved or applied.*

- **[Claude] `sandbox/bedrock/`** (`awsds-infra-sandbox-1`), from `86748b34`, whose slice pull request #369
  did not change: *"No changes."*; with `application_guardrail_required=true`, *"Plan: 0 to add, 1 to
  change, 0 to destroy."*, `aws_iam_policy.bedrock_application` (10.4's reading 4); with
  `account_guardrail_enabled=true`, *"Plan: 3 to add, 0 to change, 0 to destroy."*, the guardrail
  `account`, its version and `awscc_bedrock_enforced_guardrail_configuration.account` (reading 6). The stage
  file's 3 to add and 1 to change with both switches is their sum.
- **[Claude] `sandbox/ml/`**: *"No changes."*
- **[Claude] `sandbox/workflows/`**, from the merge of `origin/main` at `82edff32`: *"No changes."*;
  `training_pair_enabled` defaults to `true` since #369, the pair applied on day 2.
- **[Claude] The stage file**: day 3 raises `GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent`, since
  verification xxiv's `Retrieve`, which day 2 left on the user's choice, rides day 3 after 6e 6.4's window
  (`promotion.md` §N.9.5 step 4). Row 12 carries it, and day 3 bills about 0.28 USD an hour before the
  spaces, as day 2 did since the VPN host's return.

## 2026-11-22 — Day 3's prerequisites, with nothing up: `app-ml-dev`'s MLflow App, `app-genai-dev`'s Nova Lite profile and the two tars

*Claude, on the user's request of the session to run every step that needs nothing up, made the portal acts
as the Data Scientist User in the user's own Chrome session, which the user offered for SMUS acts; AWS read
as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and
`Data Governance Account` (`awsds-infra-data`). Times UTC.*

- **[Claude] 9.6, `app-ml-dev`'s MLflow App**, from the project's *Resource blueprints* gallery, *MLflow App*:
  the form asked a name, a description and `mlflowAppName`, whose default reads `serverless-app`, given
  `app-ml-dev-mlflow`. The environment `c7pal0653hk0i8` (`app-ml-mlflow`), created at 08:20:09Z by the Data
  Scientist User, reads `ACTIVE` with the profile's `MLflowApp` configuration
  `3342d20e-001b-4b95-9053-fbbc04b5c303`, so the gallery's deployment uses the profile's configuration.
  `CreateMlflowApp` at 08:20:34Z by `awsds-sandbox-smus-provisioning` in an
  `AmazonDataZoneEnvironmentDeployer-<account>` session, no `vpcEndpointId` (`ML-2`). The app
  `app-ml-dev-mlflow` (`app-KWESNF34TWGW`), created 08:20:33Z, reads `Created`, MLflow 3.16.0, the role
  `datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk`, `AutoModelRegistrationDisabled`, no key, maintenance
  Thu:07:57. Verification lx reads under that mode, as 3.2 read `ml-demo-mlflow`'s: MLflow's registry alone.
- **[Claude] 10.4, `app-genai-dev`'s first use of Nova Lite.** A call in the portal's playground at about
  08:21Z, 7 tokens in and 28 out in 355 ms, went through the domain's profile `csu817ovl4kz`, named
  `dzd-d8yrvx1ko7im6o`, and created no subscription and no profile in the project (`SUP-187`). An unsaved
  *Run* in the Bedrock IDE's prompt builder at about 08:24:50Z did both: `CreateSubscriptionRequest` at
  08:24:51Z in Data Governance's trail as the domain execution role, for `b8fz4ovppjijv4` on the model's
  listing `cp58jn8lqdoknk`, the subscription `5hosg2jcucw8i8` `APPROVED` at creation; `CreateInferenceProfile`
  at 08:24:55Z by `AmazonSageMakerBedrockModelManagementRole-<account>` in an `AWSDataZone-Subscriptions`
  session, invoked by `datazone.amazonaws.com`, named `dzd-d8yrvx1ko7im6o b8fz4ovppjijv4` (`SUP-445`). The
  profile `ciceumyodl7y` lists Nova Lite in `us-west-2` alone and carries `AmazonDataZoneProject`
  `b8fz4ovppjijv4`, `AmazonDataZoneDomain` and `AmazonBedrockManaged` `true`; no environment was created. Its
  ARN is 10.4's `DEV_MODEL_ID`. `./aws/bedrock-usage.py` to 08:30Z reads one invocation of 7 in and 28 out on
  each of the two profiles.
- **[Claude] 9.6 and 10.4, the tars**, built as Stage 20 2.0 built `app-dbt`'s, from `origin/main` at
  `77fc285a` (`git archive` of each application's folder), under `$HOME/tmp/stage17-day3/`:
  - `app-ml.tar`, 16,252,928 bytes, SHA256 `bbb1399bd528d40a01049a2121b7f9c6ee4f2c97f1b10a568a45b8722eaa96f5`:
    `code/app-ml-train.zip` (15,910,638 bytes) by `awsds-workflows package-task code` at the application's
    pin `37cb5a6`, and `code/app-ml-register.zip` and `code/app-ml-score.zip` (12,030 bytes each, one content)
    by `python -m zipfile -c` over `code/app_ml_tasks`, the pipeline's `build-task-code` commands.
  - `app-genai.tar`, 242,176 bytes, SHA256 `c63204d2d7b2d137484aae5ff057d7230b103a823a72d114db62db6d7d440e19`:
    `code/app-genai.zip` (15,715 bytes) by `scripts/build_archive.py`.
  - Each tar holds no AppleDouble member (`COPYFILE_DISABLE=1`, `--no-xattrs --no-acls --no-mac-metadata`,
    `SUP-348`). The train archive holds x86_64 Linux wheels, which the laptop's arm64 interpreter cannot load,
    so its contents were read instead (`testzip` clean, the compiled modules' platform tags), as 2.0 did.
  - `app-ml.env` and `app-genai.env` beside them export what each manifest reads: `DOMAIN_ID`,
    `DOMAIN_REGION`, `DEV_PROJECT_NAME`, and for `app-ml` `MLFLOW_APP_ARN`, `JOB_IMAGE_URI` (the house image
    version 12 by digest), `TRAINING_IMAGE_URI`, `SUBNET_AZ1`, `SUBNET_AZ2`, `DEV_PROJECT_SG` and
    `DEV_PROJECT_KEY_ARN`, for `app-genai` `DEV_MODEL_ID`. The sitting uploads each tar and its file into
    the project's space and sources the file before the deploy.
- **[Claude] The lint** from `main`, each pipeline's options: `app-ml` *"ok: 6 arquivo(s)"* and `app-genai`
  *"ok: 3 arquivo(s)"*, at the pin `37cb5a6` and at `awsds-workflows` `4401f91`, whose rule `operador` each
  application's next tag takes.
- **[Claude] The instruments**: `./aws/sandbox-ml.py` at 08:50Z, `ML-2` reading the new app as above,
  `ML-10` and `ML-11` noting 9.6's and 10.4's objects absent, and `ML-8` failing on the flow's role,
  `AWS_STATE.md`'s expected reading.

## 2026-11-22 — `SUP-447`'s role: the user's decision, an exception

*The user's choice on a question card in the session "Decisões pendentes, uma de cada vez", relayed to this
session with the user's words; Claude read the role as the infrastructure user with `InfrastructureAccess`
in `Sandbox Account 1` (`awsds-infra-sandbox-1`), reads alone. Times UTC.*

- **[user] The decision**, at 13:30, verbatim: *"Aceitar como exceção (Recomendado)"*. The card's other
  options, not taken: *"Apagar o flow e a role"* and *"Pôr o boundary à mão"*. The option as the card
  stated it: an `EXC-nn` row in `docs/AWS_STATE.md` for `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw`, and
  `ML-8` (`aws/sandbox-ml.py`) and `US-8` (`aws/studio.py`) recognising the role's shape rather than its id
  (the name `AmazonBedrockFlowServiceRole-*`, trust in `bedrock.amazonaws.com` alone, AWS's
  `SageMakerStudioBedrockFlowServiceRolePolicy` alone), so the exception covers every later flow app and
  fails again if the shape changes; no AWS write.
- **[Claude] The role read again**, at 13:34: `PermissionsBoundary` null, `RoleLastUsed` empty, created
  02:02:39Z; its trust `sts:AssumeRole` by `bedrock.amazonaws.com` under `aws:SourceAccount` the account's
  own and `aws:SourceArn` `arn:aws:bedrock:us-west-2:<account>:flow/*`; one attached policy,
  `service-role/SageMakerStudioBedrockFlowServiceRolePolicy`, and no inline policy; the only
  `AmazonBedrockFlowServiceRole-*` role in the account.
- **Left**: the `EXC-nn` row and the two checks' change, written on the user's word in this session's chat;
  until then `ML-8` and `US-8` fail on the role, `AWS_STATE.md`'s expected reading.

## 2026-11-22 — 7.6's leftovers: the user's decision to delete the four objects

*The user's choice on a question card in the session "Decisões pendentes, uma de cada vez", relayed to this
session with the user's words; Claude read the objects as the infrastructure user with `InfrastructureAccess`
in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and `Data Governance Account` (`awsds-infra-data`), reads
alone. Times UTC.*

- **[user] The decision**, at 13:34, verbatim: *"Apagar os quatro (Recomendado)"*. The card's other options,
  not taken: *"Apagar só os três listados"* and *"Manter tudo"*. Each deletion waits on the user's word in
  the chat of the session that runs it, and is read back after it (Lesson 86).
- **[Claude] The four objects**, read at 13:37 to 13:40, every one in `eighth-experimentation`
  (`avhvbqn37ty7m8`):
  1. the chat agent's environment `b343orq3qka5n4`, `502a9c64-70fd-4dab-afea-a1a5a98146d4-shared`,
     `CREATE_FAILED` with no provisioned resource, its stack `DataZone-Env-b343orq3qka5n4` `DELETE_COMPLETE`
     since 03:08:08; its definition `…/avhvbqn37ty7m8/amazon-bedrock/builder/apps/chatApp/502a9c64-70fd-4dab-afea-a1a5a98146d4-definition.json`
     in `awsds-sandbox-smus-projects`, 1423 bytes, 03:01:39;
  2. the Haiku 4.5 evaluation's environment `6fl52xzq3yt768`, `avhvbqn37ty7m8ml-demo-eval-haiku45`, `ACTIVE`,
     its stack `CREATE_COMPLETE` with no resource and one output, the project's Bedrock service role
     `AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c`, which the environment lists as its provisioned
     resource `systemRole-AmazonBedrockEvaluationRole-avhvbqn37ty7m8` and did not create; no job of its name
     (`list-evaluation-jobs` lists `avhvbqn37ty7m8ml-demo-eval-nova-lite` alone, `Completed`), and under its
     output prefix the 0-byte `amazon-bedrock-evaluations-permission-check` of 02:07:54 alone;
  3. the vector bucket `amazon-bedrock-ide-avhvbqn37ty7m8-cie8747bea6mxc`, created 01:03:10, no index, its
     stack `DataZone-Env-cie8747bea6mxc` `DELETE_COMPLETE` since 01:03:30; the knowledge base's store is the
     other, `…-46cr0woe7670gg`, created 01:33:17;
  4. a chat app definition no log records, `…/chatApp/043850fa-6a37-44ad-9ade-89e7e3af8fc5-definition.json`,
     1129 bytes, 2026-10-30 06:25:43, with no environment; the project's Claude Opus 4.5 application
     inference profile was created 17 s after it, at 06:26:00, the project's first use of that model.
- **[Claude] What stays**: the Nova Lite evaluation's input `…/genAI/assets/evaluations/input/evaluation-dataset.jsonl`
  (2951 bytes, 02:50:45) and its output, and the project's Bedrock service role the second environment
  names.
- **Left**: the deletions, each on the user's word: the two definitions from the Bedrock IDE's *My apps* by
  the project's owner, and the failed environment from the project's blueprint deployments if the app's
  deletion leaves it; the evaluation's environment from the portal or by `datazone delete-environment`; the
  vector bucket by `s3vectors delete-vector-bucket` alone. The second environment's deletion must leave
  the project's Bedrock service role, which its stack did not create.

## 2026-11-22 — 7.6's deletions by the CLI: the evaluation's environment and the empty vector bucket

*Claude's writes on the user's word in this session's chat, *"autorizo os dois"*, answering a question that
named both deletions; as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`), a contributor of `eighth-experimentation`. The sessions "Guia do Governance
Manager no portal (item 6)", "Decisões pendentes, uma de cada vez" and "Preparação de infraestrutura SSO"
were told before the writes. Times UTC.*

- **[Claude] Before**, 13:40:33: `6fl52xzq3yt768` `ACTIVE`; the vector bucket
  `amazon-bedrock-ide-avhvbqn37ty7m8-cie8747bea6mxc` with `aws:kms` encryption and no index. The project's
  Bedrock service role `AmazonBedrockServiceRole-avhvbqn37ty7m8-5hkjdsy3umpi1c`, the environment's listed
  resource, carries `AmazonDataZoneEnvironment` `5hkjdsy3umpi1c`, the project's `Tooling` environment, and was
  created 2026-08-23 under `awsds-sandbox-project-boundary`.
- **[Claude] The environment**: `datazone delete-environment` on `6fl52xzq3yt768` at 13:40:48, exit 0, the
  record `DELETING` at 13:40:50; its stack `DataZone-Env-6fl52xzq3yt768` `DELETE_COMPLETE` at 13:41:02, and
  `get-environment` answering *"Environment not found"* at 13:41:14. A contributor's call was admitted.
- **[Claude] The vector bucket**: `s3vectors delete-vector-bucket` at 13:41:02, exit 0; `list-vector-buckets`
  at 13:41:03 lists the knowledge base's store `…-46cr0woe7670gg` alone.
- **[Claude] After**: the service role stands, as before; `list-evaluation-jobs` lists
  `avhvbqn37ty7m8ml-demo-eval-nova-lite` `Completed`; the 0-byte
  `…/evaluations/output/avhvbqn37ty7m8ml-demo-eval-haiku45/amazon-bedrock-evaluations-permission-check` of
  02:07:54 stays, the environment's deletion leaving its output prefix.
- **Left of 7.6**: the two chat app definitions, `502a9c64-…` and `043850fa-…`, from the Bedrock IDE's *My
  apps* by the project's owner, and the failed environment `b343orq3qka5n4` from the project's blueprint
  deployments if the app's deletion leaves it, each on the user's word.

## 2026-11-22 — 7.6's deletions in the trails

*Claude, reads alone, as the infrastructure user with `InfrastructureAccess` in `Data Governance Account`
(`awsds-infra-data`) and `Sandbox Account 1` (`awsds-infra-sandbox-1`), at 13:51 UTC after the trails' lag.*

- **[Claude] Sandbox's trail**: `datazone:DeleteEnvironment` on `6fl52xzq3yt768` at 13:40:50Z in the
  infrastructure user's `InfrastructureAccess` session; `cloudformation:DeleteStack` of
  `DataZone-Env-6fl52xzq3yt768` at 13:41:02Z by `awsds-sandbox-smus-provisioning`'s session
  `AmazonDataZoneEnvironmentDeployer-<account>`, invoked by `datazone.amazonaws.com`; `s3vectors:DeleteVectorBucket`
  on `amazon-bedrock-ide-avhvbqn37ty7m8-cie8747bea6mxc` at 13:41:03Z in the infrastructure user's session.
  No error on any of them.
- **[Claude] Data Governance's trail**: the same `DeleteEnvironment` at 13:40:50Z, its caller in another
  account recorded with no ARN.

## 2026-11-22 — `EXC-27`: `SUP-447`'s exception written, and `ML-8` and `US-8` judging the role's shape

*Claude's repository edits on the user's word in this session's chat; the two instruments run as the
infrastructure user with `InfrastructureAccess`, reads alone. Times UTC.*

- **[user] The word**, at 14:51, verbatim: *"SUP-447: escrever o EXC-nn e a mudança no ML-8/US-8 (só no
  repositório)."*
- **[Claude] The record**: `docs/AWS_STATE.md` `EXC-27`, accepted by the user's decision of 13:30 (this log,
  the entry on it), and section C's reading of the role removed. `EXC-27` was free on `origin/main`
  (`6c30f9be`) when it was written.
- **[Claude] The checks**: `aws/awslib/flowrole.py` holds the shape: the name
  `AmazonBedrockFlowServiceRole-*`; every trust statement an `Allow` of `sts:AssumeRole` to
  `bedrock.amazonaws.com` alone, under `aws:SourceAccount` the account's own and an `aws:SourceArn` within
  this account's `flow/*`; `SageMakerStudioBedrockFlowServiceRolePolicy` the only attached policy; no inline
  policy. `aws/sandbox-ml.py` `ML-8` and `aws/studio.py` `US-8` note an unbounded role of that shape with
  `EXC-27`'s text and fail on any other unbounded role, naming what keeps a flow role out of the shape; both
  read `iam:ListRolePolicies` for it now. Run offline on the role's documents, the shape function returned
  no problem, and one or two on each altered copy: another account, no condition, any account's flows, a
  second policy with an inline one, another name, an `AWS` principal.
- **[Claude] The readings**, 15:00:01 to 15:04:01: `./aws/sandbox-ml.py` notes `ML-8` on
  `AmazonBedrockFlowServiceRole-5er1gtql9ewbgw` with `EXC-27`'s text, *"all checks passed"*, exit 0.
  `./aws/studio.py` notes `US-8` on the role in `awsds-infra-sandbox-1` and passes *"all 18
  blueprint-provisioned role(s) bounded, besides 1 under EXC-27 (19 found by tag)"*, with Production,
  Staging and Data Governance three each, *"0 check(s) FAILED"*; its exit 1 is the persona profiles, whose
  sessions held no token (section 10 lists their `sts get-caller-identity` alone).

## 2026-11-22 — 7.6's portal half: the owner's deletions, read

*The user's acts in the portal as `eighth-experimentation`'s owner, the Data Scientist User, as the user's
word in this session's chat placed them; Claude's reads as the infrastructure user with `InfrastructureAccess`
in `Sandbox Account 1` (`awsds-infra-sandbox-1`) and `Data Governance Account` (`awsds-infra-data`). Times
UTC.*

- **[user] The word**, at 14:51, verbatim: *"7.6: as duas deleções que faço pela CLI. As duas definições e o
  registro falho ficam para My apps, no portal, pelo owner."* The two CLI deletions had run at 13:40 and
  13:41 on the user's earlier word (this log, the entry on them), and read again at 14:53:50:
  `get-environment` on `6fl52xzq3yt768` answering *"Environment not found"*, `list-vector-buckets` listing the
  knowledge base's store `…-46cr0woe7670gg` alone.
- **[Claude] The failed environment**: Data Governance's trail holds `datazone:DeleteEnvironment` on
  `b343orq3qka5n4` at 14:59:05Z, no error, as `awsds-data-studio-domain-execution` in the session
  `user-28f1b390-…`, the Data Scientist User's profile; Sandbox's holds `cloudformation:DeleteStack` of
  `DataZone-Env-b343orq3qka5n4` at 14:59:17Z by the provisioning role's session from
  `datazone.amazonaws.com`, on the stack deleted since 03:08:08. The profile's other 380 calls from 14:40:24
  to 15:01:39 are reads. `get-environment` answers *"Environment not found"* at 15:05:29.
- **[Claude] The two definitions**: `head-object` on
  `…/chatApp/502a9c64-70fd-4dab-afea-a1a5a98146d4-definition.json` and
  `…/chatApp/043850fa-6a37-44ad-9ade-89e7e3af8fc5-definition.json` in `awsds-sandbox-smus-projects` answers
  `404` for both at 15:05:30, where the same call read 1423 and 1129 bytes at 13:37 to 13:40; under
  `amazon-bedrock/builder/apps/` the project holds `ml-demo-flow`'s
  `flowApp/d6d9be18-d2cd-4249-bf55-4bd97abc9a33-definition.json` alone. An object's deletion is an S3 data
  event, which the trail's lookup does not return, so the time the definitions went is not read.
- **7.6 done**: the four objects of its list are gone. The Nova Lite evaluation's input and output, the
  project's Bedrock service role, and `ml-demo-flow` with its role (`EXC-27`) stay.

## 2026-11-22 — 7.6's portal half: the user's report, and Sandbox's trail

*The user's words in the orchestrating session's chat, relayed to this session; Claude's reads as the
infrastructure user with `InfrastructureAccess` in `Sandbox Account 1` (`awsds-infra-sandbox-1`), at 15:13.
Times UTC.*

- **[user] The report**, at about 15:00, verbatim: *"Apaguei o deployment do blueprint e os dois apps."* The
  deployment is `502a9c64-…-shared` under *Resource blueprints*, and the apps are *My apps*' rows *"Untitled
  App - cer31"* and *"Untitled App - towev"*, as the orchestrating session named them.
- **[Claude] Sandbox's trail**, read at 15:13 for 14:55 to 15:10, 14 minutes after the portal's call: no
  `DeleteEnvironment` and no event naming `b343orq3qka5n4`. The call is in Data Governance's trail, made
  there as the domain execution role in the owner's session (the entry above), while Claude's own
  `DeleteEnvironment` from Sandbox at 14:53:25 is in both trails (6f's log). The definitions' deletions are S3
  data events, which the lookup does not return.
- **[Claude] The project's environments**, at 15:13: ten, every one `ACTIVE`, none named `…-shared`.

## 2026-11-22 — 10.5's boundary plan and `TM-28`'s unapplied fence

*The overlap reported by the orchestrating session on main at `f37ff75c` and re-read here; Claude's reads
as the infrastructure user with `InfrastructureAccess` in `Staging Account` (`awsds-infra-staging`) and
`Production Account` (`awsds-infra-prod`), at about 17:05, no write. Times UTC.*

- **[Claude] The overlap.** #372 (`77fc285a`) adds `agent-registry` to `fenced_services` in
  `staging/studio/` and `production/studio/`, each planned *"0 to add, 2 to change"* (`SUP-356`), and the
  waiting list holds those applies on the user's word. `sagemaker-prereqs` renders the list as the
  boundary's `DenyServicesNoProjectUsesHere`, in the boundary 10.5 moves to its next version in the same
  slices, its plan read for the Bedrock statements and nothing else (Lesson 69).
- **[Claude] The boundaries**: `awsds-staging-project-boundary` and `awsds-prod-project-boundary` at
  version 4, last updated 2026-11-17 at 16:08:08 and 16:09:01. Neither `DenyServicesNoProjectUsesHere`
  names `agent-registry:*`: Staging's denies `sqlworkbench`, `redshift`, `redshift-serverless`,
  `redshift-data`, `q`, `codewhisperer`, `bedrock` and `bedrock-agentcore`, Production's `sqlworkbench`,
  `redshift-data`, `q`, `codewhisperer`, `bedrock` and `bedrock-agentcore`.
- **[Claude] Recorded**: 10.5's plan reading names `TM-28`'s fence unless that apply ran first, the
  `TM-28` waiting row names 10.5's applies, and `promotion.md` §N.6 item 8 carries the clause.

## 2026-11-22 — Day 3's prerequisites re-read on main at `f37ff75c`: the Sandbox slices and the tars

*The plans are the orchestrating session's, relayed to this session and not re-run here; the tars read by
Claude on the laptop, no AWS call. Times UTC.*

- **[Claude, the orchestrating session] `sandbox/bedrock/` and `sandbox/ml/`**, planned at about 16:55 as
  `awsds-infra-sandbox-1` with `-input=false`, from a worktree whose slices equal `origin/main` at
  `f37ff75c`: each read *"No changes. Your infrastructure matches the configuration."*
- **[Claude] The tars** under `$HOME/tmp/stage17-day3/`, built from `77fc285a`: `git diff --stat 77fc285a
  origin/main -- examples/app-ml examples/app-genai` is empty. Outside the documents, the commits since
  change only #321's `.pre-commit-config.yaml`, `Makefile`, `aws/cicd.py`, `scripts/deploy-application.py`
  and `scripts/model-chain.py`, and every entry of `app-ml.tar`, `app-genai.tar`, `app-ml-source.tar` and
  `app-genai-source.tar` lies under `app-ml/`, `app-genai/`, `examples/app-ml/` or `examples/app-genai/`.
  The tars still match main.

## 2026-11-22 — 3.3: `eighth-experimentation`'s source run after the group, and verification v

*Claude's reads as the infrastructure user with `InfrastructureAccess` in `Data Governance Account`
(`awsds-infra-data`) and `Sandbox Account 1` (`awsds-infra-sandbox-1`), at about 16:55 and from 17:41 to
17:50; no write. Times UTC.*

- **[Claude] Before the run**, at about 16:55: `Tooling-default-sagemaker-modelpackagegroup-datasource`
  (`4tb4qnmgi0iej4`, `cron(32 17 * * ? *)`) `READY`, `ENABLED`, `publishOnImport` `false`, tracking
  `SageMakerModelPackageGroupAssetType` over an empty list; its last run, 2026-11-21 from 17:38:11 to
  17:38:20, `SUCCESS` with 0 assets. Sandbox holds one model package group, `ml-demo-xgboost`, `Completed`
  since 00:18:45. The infrastructure user's `Search` in the project is refused, *"User is not permitted to
  perform operation: Search"*, being no member of it, so the run's activities are the instrument.
- **[Claude] The run** `ahyxtok17bxok0`, `SCHEDULED`, 17:38:11 to 17:38:24: `SUCCESS`, `added` 0,
  `updated` 0, `unchanged` 0, `failed` 0, no error; `list-data-source-run-activities` returns no item. The
  source reads `lastRunAssetCount` 0 and the same empty list.
- **[Claude] `ML-4`**, `./aws/sandbox-ml.py` at 17:47:08, all checks passed: `ml-demo-xgboost` *"tagged
  avhvbqn37ty7m8; 1 version(s): v1 Approved"*, and its `model.tar.gz` *"the model data under the project
  key"*.
- **[Claude] `CT-6`**, `./aws/catalog.py` at 17:50:08, all checks passed: a note listing the source among
  the schedules nobody wrote, *"in eighth-experimentation on cron(32 17 * * ? *) (87 FAILED, 4 SUCCESS)"*.
- **[Claude] Verification v: neither.** The source neither fails on the share nor ingests the group, which
  had existed for 17 hours with the project's tag: it tracks an empty list, and nothing adds to it. 3.3 is
  done.

## 2026-11-22 — Day 3's sitting C: the pre-flight and the raise shared with §N.10's day 1

*Claude, in the session the orchestrating session started for `promotion.md` §N.9.5's day 3, run beside the
session of §N.10's day 1 on one raise. Claude's reads as the infrastructure user with `InfrastructureAccess`
through `awsds-infra-sandbox-1` (account Sandbox Account 1); `make status` through its own profiles. The raise
is the user's. Times UTC.*

- **[Claude] The pre-flight**, 17:28 to 17:41: `make status` at 17:36:20 read nothing up, 0.0000 USD/h. The
  tars under `$HOME/tmp/stage17-day3/` hash as the prerequisites' entry records (`app-ml.tar` `bbb1399b…`,
  `app-genai.tar` `c63204d2…`). `sandbox/bedrock/` planned at about 17:40 from `f37ff75c` with Terraform
  1.17.2 and `-input=false`: *"No changes."* `list-spaces` at 17:38: `code` (Code Editor, remote access
  `ENABLED`) and `jup` (JupyterLab) `InService` in `d-m8m0uefej9kb`, none in `app-ml-dev`'s `d-hxxfi3od0xhm`
  or `app-genai-dev`'s `d-q1bianbhckrd`.
- **[user] The raise**, the hub and `make up ENV=sandbox GROUPS=mwaa,mlflow,bedrock-base,bedrock-agent,redshift`,
  the union of both sittings' groups. The first `make up` stopped at 18:01 on a lock on `sandbox/egress`
  written at 18:01:09 and 18:01:11 with no process holding it; the user released it with `force-unlock`,
  which this session may not run, and ran the union again. The orchestrating session read the slice's
  state rewritten at 18:16:24.
- **[Claude] `make status`**, about 18:22 to 18:26: `production/vpn` and `production/proxy` `UP`,
  `sandbox/egress` `UP` with 34 resources, the warehouse's compute with 2, `sandbox/probes` with 4, `jup`
  billing as JupyterLab on `ml.t3.medium`, GitLab's host stopped; an estimated burn of 1.7094 USD/h.
- **[Claude] 6e 6.4 is not run today**, the user's decision relayed by the orchestrating session at about
  18:30 (the 6e log); 7.5's announcements to §N.10's session stand.

## 2026-11-22 — Day 3's sitting C: 9.6's deploy and the first `app-ml-train` run

*The space's readings are the user's, pasted, from `jup-ml-dev` in `app-ml-dev` (JupyterLab on
`ml.t3.medium`, `awsds-sandbox-dev-env` version 12, created at 18:30:49), with the account id written
`<Sandbox Account 1>`. Claude's reads as the infrastructure user with `InfrastructureAccess` through
`awsds-infra-sandbox-1`, reads alone; the CLI's code read in its cached wheel, 1.0.9, on the laptop. Times
UTC.*

- **[user] The working copy.** `~/app-ml.env` was absent from the space's home at the first `source` and
  was uploaded. The tar carries no `.git`, and `scripts/training-source.py` exits 1 where git cannot read
  the folder, which stops `scripts/dev-cli.sh` under `set -e`; a `git init` and one commit in the
  unpacked folder gave `TRAINING_SOURCE` `46bd65a0ea73f8f3a7b01a55f4c793c8a63d7c104dbbb0caebaa39275d0e2b4d`,
  the value Claude read over `examples/app-ml` on the laptop.
- **[user] The tests and the lint**: `uv sync --locked` on CPython 3.12.14 (`/opt/awsds/venv/bin/python`),
  18 packages; *"100 passed in 2.84s"*; ruff *"All checks passed!"* and *"20 files already formatted"*;
  `awsds-workflows` 0.1.0 at `37cb5a6260c8348cc208988e42090caf42a3a207`, *"ok: 6 arquivo(s)"*. Then
  `create-model-package-group app-ml-dev`, which returned the group's ARN.
- **[user] `bundle`**, at 18:45:20 as the project role: three *"Error getting DataZone project info for
  app-ml-dev: Failed to resolve domain"* lines on `ListDomains` `AccessDenied`; `code` 3 files, `src` 2,
  `samples` 2, `workflows` 3; *"Warning: Connection 'default.s3_shared' not found for storage item
  'model'"*; `./artifacts/app-ml.zip`, 15,592,181 bytes, 10 files, no `model/`; exit 0.
- **[Claude] Why `bundle` reads no connection as the project role**, in the wheel: `commands/bundle.py`
  copies the stage's domain `region`, `name` and `tags` into its configuration and never its `id`, then
  calls `get_datazone_project_info`, whose `_resolve_domain_id` (`helpers/utils.py`) falls through to
  `datazone.resolve_domain_id`, a `ListDomains` call. DataZone refuses that call to a project role, the
  project's information comes back empty, so do its connections, and every item that names a connection
  is skipped with the warning above, whatever its prefix holds. `scripts/dev-cli.sh` answers
  `get_domain_id_by_name`, which `bundle` does not call. The bundle role `awsds-deploy-sandbox-test`
  holds `datazone:ListDomains` (`sandbox/workflows/deploy-role.tf`), so the pipeline's `bundle` job takes
  the other road. `SUP-374` gains the reading.
- **[user] `deploy`**, 18:46:19 to 18:46:57: 12 files under `shared/app-ml/` (`code`, `src`, `inbox`,
  `workflows`), *"No catalog assets configured"*, three workflows created as the project role in the
  Tooling environment's subnets and security group under `alias/awsds-sandbox-project`, the account's key
  for project resources, which `app-genai-dev`'s workflows take too: `app_ml_app_ml_dev_app_ml_train`
  (18:46:32), `…_app_ml_register` (18:46:44) and `…_app_ml_score` (18:46:57), tagged
  `AmazonDataZoneDomain`, `AmazonDataZoneProject`, `CreatedBy`, `Pipeline`, `STAGE` and `Target`;
  *"Deployment completed successfully!"*
- **[user] `run --workflow app-ml-train`** at 18:47:33: the run `8rccuyH59HXJ0RA`, with twelve warnings of
  `ListTagsForResource` refused on other projects' workflows, since the CLI lists every workflow in the
  account.
- **[Claude] The jobs**, read with `describe-processing-job` and `describe-training-job`:
  - `prepare`: `app-ml-prepare-train-20261122T184824`, created 18:48:26, the project role, the house image
    version 12 by digest (`a6f9b5ab…`), one `ml.t3.medium`, the volume and the output under the same key, network isolation and inter-container encryption on, the project's subnets and security group,
    inputs `app-ml/src/` and `app-ml/inbox/churn.csv`, output `app-ml/work/train/`, 1,800 s at most, tagged
    `AmazonDataZoneProject` `5rzplmk81vma34`, `AmazonDataZoneDomain` and `AmazonDataZoneScopeName` `dev`.
    `Completed`, 18:49:11 to 18:56:27.
  - `train`: `app-ml-train-20261122T185913`, created 18:59:16, the project role, `sagemaker-xgboost:3.0-5`
    by tag in `File` mode, one `ml.m5.large` with 10 GB, the volume and the output under the same key,
    isolation and inter-container encryption on, the project's network, output `app-ml/models/`,
    `binary:logistic`, `eval_metric` `auc`, `eta` 0.3, `max_depth` 3, `num_round` 50, the same tags.
    `Completed`, 19:00:01 to 19:02:06, 125 billable seconds; `validation:auc` 0.8289499878883362,
    `train:auc` 0.9929400086402893.
- **[Claude] The run `FAILED`** at 19:05:27: `prepare` 614 s, `train` 226 s, `evaluate` 10 s and `track` 18 s
  `SUCCESS`, `publish` `FAILED` after 12 s. Its log, `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-5rzplmk81vma34/app_ml_app_ml_dev_app_ml_train`,
  at 19:05:22: *"the training image '<AWS registry>.dkr.ecr.us-west-2.amazonaws.com/sagemaker-xgboost:3.0-5'
  names no digest"*, raised by `by_digest` (`code/app_ml_tasks/common.py`) before any write. The prefix
  `app-ml/models/` held the job's `output/model.tar.gz`, its `evaluation.json` and `last-run.json`, and no
  `latest/`.
- **[Claude] The cause is the prerequisites' `app-ml.env`**, which exported `TRAINING_IMAGE_URI` by the tag
  where the README and pass 9 name the image by digest in every stage. The tag has moved:
  `ecr describe-images` on AWS's registry at about 19:11 reads `3.0-5` as `sha256:5a82a2d0f00fa1baa41aba8a95f8145b8214bc65c4c16ce12d723a30e8cc34dd`
  (also `3.0-5-1.0.67.0` and `3.0-5-cpu-py3`, pushed 2026-11-17 19:42:09), and the digest both targets'
  `training-image.tf` pin, `sha256:0b5d9341…3a78`, as `3.0-5-1.0.64.0` alone (pushed 2026-10-11). So the
  job above trained on an image no target serves. The CLI 1.0.9 writes `{env.X}` into the definition as
  `{{ params.X }}` (`helpers/context_resolver.py`) and `run` passes the stage's variables as override
  parameters (`commands/run.py`); the deployed definition holds no image, so the correction needs no
  deploy. The laptop's copy was corrected at 19:12:39 to the pinned digest, and the same `sed` handed to
  the user for the space's.

## 2026-11-22 — Day 3's sitting C: 9.6's second `app-ml-train` run and the refused `CreateModelPackage`

*Claude writes this entry. The space's readings are the user's, pasted, from `jup-ml-dev`. Claude's reads are
as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`, reads alone. Times
UTC.*

- **[user] The second run.** The space's `app-ml.env` was corrected with the same `sed` (`grep` counts one
  line) and sourced. `run --workflow app-ml-train` started the run `hO8zhGFdi8vlso5`, with no deploy.
- **[Claude] The run `SUCCESS`**, 19:18:29 to 19:36:05: `prepare` 610 s, `train` 225 s, `evaluate` 8 s,
  `track` 13 s, `publish` 11 s.
  - `prepare` is `app-ml-prepare-train-20261122T191914`.
  - `train` is `app-ml-train-20261122T193009`, read `InProgress` at 19:30:18 on
    `sagemaker-xgboost@sha256:0b5d9341…3a78`, the targets' pin.
  - `latest/` was written at 19:36:05.
  - `model.json` (962 bytes) names the job and both images by that digest, with `auc`
    0.8289499878883362, `sha256` `852032c55a3047b66de1a2fa6c29e148e10b145cb30fab41d26c83214282d7ab`,
    `size` 9,930, `training_source` `46bd65a0…` and `published` 19:36:04.
  - Claude's SHA-256 of `latest/model.tar.gz` agrees. `evaluation.json` is 378 bytes.
- **[user] `run --workflow app-ml-register`** started the run `ut8uVZghVEV5UIY`, which ended `FAILED`. Its one
  task, `register`, ran 19:39:33 to 19:39:40.
- **[Claude] The refusal**, read in the task's log and in the trail.
  - `CreateModelPackage` at 19:39:35, as the project role, returned *"An error occurred
    (ValidationException) when calling the CreateModelPackage operation: The ETag request value isn't
    permissible."*
  - The request named `ModelDataETag` `b5a42cff73d4153ba6731750a1831ebc`: the copy's ETag without its
    quotes, equal to what `head-object` reads on `app-ml/models/sha256/852032c5…/model.tar.gz`. The task
    had written that copy and `evaluation.json` before the call.
  - `ml-demo-xgboost`'s version 1 was created at 00:34:10 by a request that named no ETag. It holds
    `ModelDataETag` `f8783f02a8dc0bb2867b2e67b030ea30`, the ETag `head-object` reads on its `ModelDataUrl`
    (10,727 bytes).
  - So the service sets the field from the object, and refuses one a caller sends, even the object's own
    (`SUP-462`).
- **[Claude] The correction**, in `examples/app-ml`.
  - `package_request` names no `ModelDataETag`, and the test's expected request no longer carries one.
  - The checks: *"100 passed"*, ruff clean, *"20 files already formatted"*.
  - The same change went to the user as a patch for the space's folder. It was checked on the tree of
    `77fc285a`, which the tar was built from: `registry.py` goes from `441ab566…` to `8d2dedea…`, and
    `test_tasks.py` from `9cd9a80e…` to `a139fabe…`.
  - `TRAINING_SOURCE` covers neither file.

## 2026-11-22 — Day 3's sitting C: 10.4's deploy, readings 1 to 3, and the deny applied

*Claude writes this entry. The space's readings are the user's, pasted, from `jup-app-genai-dev` in
`app-genai-dev` (JupyterLab on `ml.t3.medium`, `awsds-sandbox-dev-env` version 12, created at 18:58:27).
Claude's reads are as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`,
and the apply is Claude's on the user's word. Times UTC.*

- **[user] The profile and the checks.**
  - `DEV_MODEL_ID` was exported from `list-inference-profiles --type-equals APPLICATION`: the project's
    Nova Lite profile, `ciceumyodl7y`.
  - The listing holds eight application profiles: the domain's two, `eighth-experimentation`'s four and
    `app-genai-dev`'s two.
  - The second of `app-genai-dev`'s is an Opus 4.5 profile, `9kuvzfyn59p5`, over `us-east-1`, `us-east-2`
    and `us-west-2`. It was created at 13:12:41 by `AmazonSageMakerBedrockModelManagementRole` in the
    session `AWSDataZone-Subscriptions`, copied from `us.anthropic.claude-opus-4-5-20251101-v1:0`.
  - The checks: `uv sync` on CPython 3.12.14, *"95 passed in 5.45s"*, `make_sample --check` *"40 messages,
    the script's output"*, ruff clean, *"20 files already formatted"*, and the lint at `37cb5a6` *"ok: 3
    arquivo(s)"*.
- **[user] `deploy`**, 19:16:05 to 19:16:29.
  - Four files: `code/app-genai.zip`, `samples/messages.jsonl` and the two workflows.
  - Both workflows were created as the project role: `app_genai_app_genai_dev_app_genai_triage` at
    19:16:17 and `…_probe` at 19:16:28.
  - They run in `subnet-016b5a3a62c739894` and `subnet-09d3399d6b0fec93a` with `sg-04d8984595e5c73ef`,
    under `alias/awsds-sandbox-project`.
- **Reading 1, without the deny.**
  - **[user] `app-genai-triage`**: the run `RV85HhhNwJjJr92`, `SUCCESS` from 19:16:55 to 19:20:08
    (`guardrail` 15 s, `triage` 51 s, `check` 9 s).
  - **[Claude] The guardrail** `app-genai-b8fz4ovppjijv4` (`mn3wavwk9jx7`), created at 19:17:43.
    - Its `DRAFT` and version 1 are `READY`. The version's description is the definition's SHA-256,
      `6b4f6876…`.
    - It is tagged `AmazonDataZoneProject` `b8fz4ovppjijv4`, `awsds:definition-sha256` and
      `awsds:definition-version` `1`.
    - It has no key and no cross-Region profile.
    - The account holds one other guardrail, `razikgicppzy`, created at 02:45:13.
  - **[Claude] The trail, the `guardrail` task's calls**, as the project role in the session
    `AmazonMWAAServerless`, through the `bedrock` endpoint `vpce-0edda39ecbeee2be2` from 10.20.5.45.
    - 19:17:42: `ListGuardrails`.
    - 19:17:43: `CreateGuardrail`, `GetGuardrail` twice, `CreateGuardrailVersion`.
    - 19:17:49: `TagResource`, `GetGuardrail`.
  - **[Claude] The trail, `triage`'s 40 calls**, 19:18:35 to 19:19:15, through the `bedrock-runtime`
    endpoint `vpce-0d325931b42cbb2a4` from 10.20.105.80.
    - Each is recorded as a management event named `Converse`, read-only.
    - Its resource is the profile (`AWS::Bedrock::Model`).
    - Its parameters are the profile's ARN, `maxTokens` 200, and a `guardrailConfig` that names the
      guardrail's unversioned ARN with `guardrailVersion` `"1"` and `trace` `enabled`.
    - Its tokens are in `additionalEventData`.
    - No guarded call was refused. The endpoint's scope holds the two invoke actions alone, so the
      service asked no `bedrock:ApplyGuardrail` of the caller at either layer (verification xxxviii).
  - **[Claude] The report.**
    - 40 messages: 38 answered, 2 blocked, 37 agreeing with the label. Accuracy 0.9737 against 0.8:
      `passed`. Tokens: 12,001 input and 952 output.
    - The planted messages (verification xliii): `m25`'s address and telephone `ANONYMIZED`, and the
      message answered; `m31`'s instruction to ignore the instructions `BLOCKED` by `PROMPT_ATTACK`;
      `m36`'s denied topic `BLOCKED`.
    - A blocked row bills 0 input tokens and stops on `guardrail_intervened`.
    - Each trace names `mn3wavwk9jx7` version 1.
    - The task logs hold counts, URIs, ids and the hash alone.
  - **[user] `app-genai-probe`** with `EXPECT_UNGUARDED` `answered`: the run `kWxQcCXLwIUEWFZ`, `SUCCESS`
    from 19:22:31 to 19:23:23. The outcome was answered, as expected: 6 characters, 8 input and 3 output
    tokens, `end_turn`.
  - **[Claude] The probe's call**: one `Converse` at 19:23:22 through `vpce-0d325931b42cbb2a4` from
    10.20.105.161, with `maxTokens` 10 and no `guardrailConfig`.
- **Reading 2, the guardrail's life.**
  - **[user] `app-genai-triage` over the same definition**: the run `RgOaSj3RuH62Ov1`, `SUCCESS` from
    19:25:30 to 19:28:20 (7, 45 and 6 s).
    - Its log: *"unchanged, version 1, definition sha256 6b4f6876…"*.
    - 40 sent, 2 blocked, 12,001 and 959 tokens, accuracy 0.9737.
  - **[Claude] That run's trail**, read once it had caught up to the run's end: `ListGuardrails`,
    `GetGuardrail`, `ListTagsForResource` and the 40 `Converse`, with no write.
  - **[user] A changed definition.**
    - One filter's strength changed: `MISCONDUCT`'s input from `MEDIUM` to `LOW`. The rewrite also
      reflowed the arrays' whitespace.
    - The archive was rebuilt (8 files, 15,723 bytes) and deployed, 19:31:53 to 19:32:17. Both workflows
      were updated (*"encryption is fixed at creation and left unchanged on update"*).
    - `app-genai-triage`: the run `zxh6p5Uv0hJyrrx`, `SUCCESS` from 19:32:32 to 19:35:23 (8, 50 and 6 s).
      Its log: *"updated, version 2, definition sha256 ed309c78…"*. 12,001 and 964 tokens, accuracy
      0.9737.
  - **[Claude] That run's trail**, worker 10.20.28.252, through `vpce-0edda39ecbeee2be2`.
    - 19:33:10: `ListGuardrails`, `GetGuardrail`, `ListTagsForResource`, `UpdateGuardrail`.
    - 19:33:11: `CreateGuardrailVersion`, `GetGuardrail` on version 2, `TagResource`.
    - The 40 `Converse` name version 2, from 19:33:59 to 19:34:38. The first came 48 s after the publish,
      and none failed (verification xlvii).
  - **[user] The discard**: the definition was restored in the working copy and the archive rebuilt
    (15,715 bytes).
- **Reading 3, the operator.**
  - **[user]** `probes/operator.yaml` was rendered with `awsds-workflows render` and imported in the
    portal's editor as `app-genai-operator-probe`. Its run `H2SHTEFsAarnwLX` ended `SUCCESS`, 19:42:20 to
    19:43:03.
  - **[Claude] The task log.** The task `invoke` (`BedrockInvokeModelOperator`) ran 19:43:00 to 19:43:08.
    It wrote the prompt and the response in full to
    `/aws/mwaa-serverless/dzd-d8yrvx1ko7im6o-b8fz4ovppjijv4/app-genai-operator-probe`.
    - The prompt line: *"Bedrock arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/ciceumyodl7y
      prompt: {'inferenceConfig': {'maxTokens': 10, 'temperature': 0}, 'messages': [{'content': [{'text':
      'Reply with the single word: ready.'}], 'role': 'user'}], …}"*
    - The response line: *"Bedrock model response: {'output': {'message': {'content': [{'text':
      'Ready.'}], …"*
  - **[Claude] The trail** holds one event: `InvokeModel` at 19:43:02.
    - It ran as the project role in the session `AmazonMWAAServerless`, through `vpce-0d325931b42cbb2a4`,
      from 10.20.120.192, the worker's host.
    - Its parameters are the profile's ARN alone, with no guardrail. Tokens: 8 and 3.
    - It is a management, read-only event.
    - Its user agent names `Airflow/3.0.6`, `Caller/BedrockInvokeModelOperator` and
      `exec-env/AWS_ECS_FARGATE`.
  - **Verification xl's first half reads yes**: an `InvokeModel` with no guardrail, and the prompt and the
    response in the task log.
- **Reading 4, the deny.**
  - **[user]** *"Autorizo o apply"*.
  - **[Claude]** §N.10's session was told first, then the other sessions on the laptop.
  - The plan was saved at 19:51:22 from `7fb3724a` with `-var application_guardrail_required=true`: 0 to
    add, 1 to change, 0 to destroy. `awsds-sandbox-bedrock-application` gains
    `DenyAnInvocationWithNoPublishedGuardrailOfTheAccount`.
  - It was applied 19:55:50 to 19:56:01. The policy's default version is `v2`, updated at 19:56:00, and
    holds the statement as planned.
  - A re-plan with the same variable: *"No changes."*

## 2026-11-22 — Day 3's sitting C: 9.6's register after the correction, and the score from the prefix

*Claude writes this entry. The space's readings are the user's, pasted, from `jup-ml-dev` in `app-ml-dev`.
Claude's reads are as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`,
reads alone. Times UTC.*

- **[user] The correction in the space.** The patch applied to the space's folder: `registry.py` and
  `test_tasks.py` read `8d2dedea…` and `a139fabe…`. *"100 passed in 2.27s"*, ruff clean, *"20 files already
  formatted"*, and the task archives rebuilt at 19:57:40.
- **[user] `bundle` after the training run**, 19:57:48 (verification lxii's second reading).
  - `ListDomains` was refused three times, as before the training: *"Error getting DataZone project info
    for app-ml-dev: Failed to resolve domain"*.
  - It printed *"Warning: Connection 'default.s3_shared' not found for storage item 'model'"* and wrote
    `./artifacts/app-ml.zip`, 15,592,095 bytes, 10 files: code 3, src 2, samples 2, workflows 3. The zip
    holds no `model/`, though `app-ml/models/latest/` held the candidate since 19:36:05. The exit was 0.
  - So the project role's `bundle` skips the model item before and after a model exists (`SUP-374`).
- **[user] `deploy`**, about 19:58: 12 files, the three workflows updated (`UpdateWorkflow` at 19:58:57,
  19:59:12 and 19:59:24) with `sg-028f033a218b701b2` and the project key. Each `workflow.create` action
  uploaded the three task archives to `operatorFiles/`, so the deploy wrote nine archives.
- **[user] `run --workflow app-ml-register`**: the run `t5NzIjmLYAtSNGn`, `SUCCESS` from 19:59:35 to
  20:00:19. Its task `register` ran 8 s and logged *"proposed
  arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:model-package/app-ml-dev/1: sha256 852032c5…, trained by
  app-ml-train-20261122T193009, PendingManualApproval"*.
- **[Claude] The version `app-ml-dev/1`**, created at 20:00:18.658.
  - `PendingManualApproval`, `ModelPackageStatus` `Completed`. `CreatedBy` names no user profile.
  - Its container: the serving image by the digest `0b5d9341…`, `ImageDigest` filled by the service,
    `ModelDataUrl` `app-ml/models/sha256/852032c5…/model.tar.gz`, and `IsCheckpoint` `false`, which the
    request did not send.
  - `ModelDataETag` `1792fa2976e38b9a5bec44860076416d`, set by the service: the ETag `head-object` reads on
    the copy the task rewrote at 20:00:19. The copy is SSE-KMS under the project key with the bucket key on.
  - The copy written at 19:39 by the refused run had the ETag `b5a42cff…`, and `latest/` holds the same
    bytes under `fad76c8d…`. So an SSE-KMS object's ETag changes with each PUT of identical bytes, and
    `aws s3 cp` of the copy hashes to `852032c5…` (`SUP-462`).
  - `text/csv` in and out, `ml.m5.large` for transform, the model quality statistics pointing at the copy's
    `evaluation.json` (378 bytes), and the metadata `sha256`, `source_prefix` `app-ml/models/latest/`,
    `training_job`, `training_source` `46bd65a0…` and `validation_auc` 0.8289499878883362.
- **[Claude] The trail of `CreateModelPackage`**, as the project role in the session `AmazonMWAAServerless`,
  through the SageMaker API endpoint `vpce-0dc0f341029459864`: refused at 19:39:35 from 10.20.5.16, admitted
  at 20:00:18 from 10.20.120.228 with a `ListModelPackages` in the same second. At 20:00:19
  `sagemaker.amazonaws.com` itself recorded `CreateArtifact` three times, `CreateAction` twice and
  `AddAssociation` five times: the version's lineage, which the task does not create.
- **[user] `app-ml-register` a second time**: the run `7tWoxPRH5B7MMHJ`, `SUCCESS` from 20:09:11 to
  20:09:55, task 7 s, *"app-ml-dev holds arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:model-package/app-ml-dev/1 for
  sha256 852032c5…: nothing proposed"*. The group holds version 1 alone.
- **[user] `app-ml-score` with `MODEL_SOURCE` `prefix`**: the run `acnc3LIFhHsNGoe`, `SUCCESS` from 20:08:54
  to 20:28:23: `prepare` 613 s (`app-ml-prepare-score-20261122T200942`), `resolve` 7 s, `score` 344 s,
  `check` 10 s, `cleanup` 10 s.
  - `resolve` at 20:20:24: *"created app-ml-score-5rzplmk81vma34 from
    s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/5rzplmk81vma34/shared/app-ml/models/latest/model.tar.gz:
    sha256 852032c5…"*, returning the source `prefix` and no version.
  - **[Claude] `CreateModel` at 20:20:24**, as the project role in the session `AmazonMWAAServerless`,
    through `vpce-0dc0f341029459864` from 10.20.53.111: the image by the digest `0b5d9341…`, the model data
    `latest/model.tar.gz`, the project role as execution role, `vpcConfig` with `sg-028f033a218b701b2` and
    the two project subnets, `enableNetworkIsolation` `true`, and the three project tags.
  - The transform job `app-ml-score-20261122T202107`, created at 20:21:10 from 10.20.96.156, ran 20:24:45
    to 20:26:14 on one `ml.m5.large`: input `app-ml/work/score/batch/`, output
    `app-ml/predictions/20261122/batch.csv.out` (3,902 bytes), output and volume under the project key,
    tagged with the project, the domain and the scope `dev`.
  - `check`: *"app-ml-score-20261122T202107: 200 prediction(s) for 200 line(s), AUC 0.847556, MIN_AUC
    0.7"*.
  - `cleanup`: `DeleteModel` at 20:28:22 from 10.20.106.28, *"Model app-ml-score-5rzplmk81vma34 deleted
    successfully."* `DescribeModel` then read *"Could not find model"*.
- **[Claude] The run in the MLflow App.** `track` of the run `hO8zhGFdi8vlso5` logged *"tracked
  app-ml-train-20261122T193009 as run 3533b6355fd9410f92b0d3f3c3ad3d67 of the experiment app-ml"* with
  `validation_auc` 0.8289499878883362. The app `app-ml-dev-mlflow` keeps its artifacts under the project's
  `dev/data/ml/mlflow` and reads `AutoModelRegistrationDisabled`.

## 2026-11-22 — Day 3's sitting C: 10.4's reading 4, the runs under the deny

*Claude writes this entry. The space's readings are the user's, pasted, from `jup-app-genai-dev`, and the
operator's runs are the user's from the portal's editor. Claude's reads are as the infrastructure user with
`InfrastructureAccess` through `awsds-infra-sandbox-1`, reads alone. Times UTC.*

- **[user] The operator's workflow, run from the portal before the space's commands**: the run
  `PkCuanMhWnJcaL2`, `FAILED` from 20:08:31 to 20:09:19. Its task `invoke` logged at 20:09:14:
  *"AccessDeniedException … User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_b8fz4ovppjijv4_c9sdti5d2gaqs0/AmazonMWAAServerless
  is not authorized to perform: bedrock:InvokeModel on resource:
  arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/ciceumyodl7y with an explicit deny in an
  identity-based policy: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-bedrock-application"*.
- **[user] `app-genai-triage`**: the run `RPNFldOIkDd4tVB`, `SUCCESS` from 20:10:23 to 20:13:25 (`guardrail`
  10 s, `triage` 46 s, `check` 6 s).
  - Its log: *"unchanged, version 2, definition sha256 ed309c78…; GetGuardrail on the version returns the
    hash as its description: True"*. The deployed archive still held the changed definition: reading 2's
    discard had restored the working copy alone, with no deploy.
  - 40 sent under `mn3wavwk9jx7` version 2, 2 blocked, 12,001 and 957 tokens, accuracy 0.9737, no failure.
- **[user] `app-genai-probe`** with the working copy's `EXPECT_UNGUARDED` set to `refused` on the `dev`
  stage's line, read by `grep` beside the two targets' `refused`, and no deploy: the run `OrTNEd36RnUEkxp`,
  `SUCCESS` from 20:10:35 to 20:11:16. Its log: *"the request without a guardrail: refused, refused
  expected"*. The report names `AccessDeniedException` with the explicit deny's wording, on the profile.
  `run` passes the stage's variables at run time, so the deployed workflow read the edited value.
- **[user] The operator's workflow again, after the space's commands**: the run `uDsenQWO6tkBr0a`,
  `FAILED` from 20:10:56 to 20:11:47, its task `invoke` 14 s.
- **[Claude] The trail since 20:05**, 46 Bedrock events, read once it had caught up to the triage's end.
  - The 40 `Converse` of the triage, admitted from 20:12:04, each naming `guardrailVersion` `2`, through
    `vpce-0d325931b42cbb2a4` from 10.20.10.202. The `guardrail` task's `ListGuardrails`, `GetGuardrail` and
    `ListTagsForResource` at 20:11:11 and 20:11:12 from 10.20.26.175.
  - Three refusals, each `AccessDenied` with the explicit deny's wording, as the project role in the
    session `AmazonMWAAServerless`: `InvokeModel` at 20:09:14 from 10.20.14.149 (the first operator run),
    `Converse` at 20:11:15 from 10.20.89.108 (the probe) and `InvokeModel` at 20:11:41 from 10.20.83.169
    (the second operator run).
- **Verification xxxvii reads yes**: a guarded `Converse` through the application profile carries
  `bedrock:GuardrailIdentifier` on every pass the deny reads, so the deny admits the triage's 40 calls.
- **Verification xl's second half reads yes**: the deny refuses `BedrockInvokeModelOperator`'s `InvokeModel`,
  which names no guardrail.

## 2026-11-22 — Day 3's sitting C: the approval, `deploy` without an archive, reading 5's calls and the second guardrail deleted

*Claude writes this entry. The space's readings are the user's, pasted, from `jup-ml-dev` and
`jup-app-genai-dev`, and the approval is the user's from the portal. Claude's reads are as the infrastructure
user with `InfrastructureAccess` through `awsds-infra-sandbox-1`, and the deletion is Claude's on the user's
word. Times UTC.*

- **[user] The approval.** `app-ml-dev/1` was approved from the portal: `UpdateModelPackage` at 20:39:53, as
  `app-ml-dev`'s project role in the portal's session `28f1b390-…@5ae0dd6m1suvbk`, its source identity the
  user's. No approval description. `sagemaker.amazonaws.com` recorded `AddAssociation` and `CreateAction` at
  20:39:54. The version's `ModelDataETag` is unchanged.
- **[user] The registry's path, its literal.** `sed` set `MODEL_SOURCE` to `registry` on the `dev` stage's
  line; `grep` read `registry` on lines 80, 123 and 167, the targets' two being `registry` in the repository.
- **[user] `deploy` without the archive** (verification lxii's last reading), about 20:41: the archive moved
  out of `./artifacts`, then
  `scripts/dev-cli.sh deploy --manifest manifest.yaml --targets dev --skip-validation --no-events`.
  - It read the project (*"✅ ✅ Project 'app-ml-dev' already exists"*), printed *"Updating project
    configuration..."*, found no environment for the target and printed the four storage items, each on
    `default.s3_shared`, with no `model` item.
  - It stopped: *"❌ Error: No bundle file found in ./artifacts directory"*, *"❌ Error: Deployment failed: 1"*,
    `exit=1`. The archive was moved back.
  - **[Claude]** The trail, caught up to 20:52:26, holds no management write from the project role between
    20:40 and the next deploy at 20:51:40.
  - Verification lxii's `deploy` half reads yes: the CLI stops without an archive (`SUP-374`).
- **[user] `deploy` with the archive and `app-ml-score` in the registry's mode**: the three workflows updated at
  20:51:43, 20:51:55 and 20:52:08 (`CreateWorkflow` answered `ConflictException`, then `UpdateWorkflow` and
  `TagResource`; `CreateLogGroup` answered `ResourceAlreadyExistsException`), and `StartWorkflowRun` at
  20:52:13: the run `QCRC1Im4FuKYOMS`, `RUNNING` from 20:52:16.
- **[Claude] Reading 6's plan**, saved at 20:44:09 from `e6a7a488` with `-var application_guardrail_required=true
  -var account_guardrail_enabled=true`: *"Plan: 3 to add, 0 to change, 0 to destroy."* The account's guardrail
  `awsds-sandbox-account-guardrail` with the denied topic `Legal advice`, its version, and
  `awscc_bedrock_enforced_guardrail_configuration` with `included_models` `amazon.nova-lite-v1:0` alone and both
  content controls `COMPREHENSIVE`. Not applied.
- **[Claude] §N.10's day 1 ended** on its side at about 20:50: no further write from that session, and the day's
  lowering is this sitting's. What it keeps for its day 2 is in its own log.
- **[user] Reading 5, the variants**, `variants.py` (SHA-256 `defd1e14…`) from `jup-app-genai-dev`. **[Claude]**
  Its calls in the trail, as the project role in the space's session `SageMaker`, through
  `vpce-0d325931b42cbb2a4`:
  - `0`, the application's guardrail by its ARN with version `2`: admitted at 20:51:09.
  - `a`, the `DRAFT`: refused at 20:51:09, *"… is not authorized to perform: bedrock:InvokeModel on resource:
    arn:aws:bedrock:us-west-2:<Sandbox Account 1>:application-inference-profile/ciceumyodl7y with an explicit deny in an
    identity-based policy: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-bedrock-application"*.
  - `b`, the guardrail by its id `mn3wavwk9jx7` with version `2`: admitted at 20:51:10. The policy matches an
    ARN, so the key carries the versioned ARN when the request names the id.
  - `c`, Nova Lite's system profile `us.amazon.nova-lite-v1:0` with the guardrail: refused at 20:51:10, *"… is
    not authorized to perform: bedrock:InvokeModel on resource:
    arn:aws:bedrock:us-west-2:<Sandbox Account 1>:inference-profile/us.amazon.nova-lite-v1:0 with an explicit deny in a
    service control policy: …p-tgda7n58"*, `awsds-org-scp-ou-interactive`.
  - `d0`, the denied topic inside the guard tag, and `d1`, the same topic outside it: both admitted by the API
    at 20:51:10 and 20:51:11. What the guardrail did with each is in the script's output.
  - The second guardrail, `app-genai-residual-1795380671` (`djlyteclzosd`): `CreateGuardrail` and
    `CreateGuardrailVersion` at 20:51:11 through `vpce-0edda39ecbeee2be2`, with the tag `AmazonDataZoneProject`
    `b8fz4ovppjijv4` and one word filter; its version 1 `READY` at the second poll, 20:51:17.
  - `e`, that guardrail's version 1 named in a `Converse`: admitted at 20:51:17, 8 tokens in and 3 out.
    Decision 24 (b)'s residual reads as the decision says: a guardrail the role published six seconds before
    is admitted.
  - A refused call's event carries `requestParameters` null.
- **[Claude] The second guardrail deleted** on the user's *"Autorizo apagar"*: `delete-guardrail` at 20:54:25,
  exit 0. `get-guardrail` then read *"This guardrail does not exist."*, and the account holds
  `mn3wavwk9jx7` and `razikgicppzy`.

## 2026-11-22 — Day 3's sitting C: reading 5's guardrail decisions and verification lx

*Claude writes this entry. The outputs are the user's, pasted from `jup-app-genai-dev` and `jup-ml-dev`;
Claude's reads are as the infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`.
Times UTC.*

- **[user] Reading 5's outputs** (`variants.py`, SHA-256 `defd1e14…`): what the application's guardrail
  `mn3wavwk9jx7`, version 2, did with each call the deny admitted, from the trace.
  - `0`, *"Reply with the single word: ready."* in a plain text block: `stop=guardrail_intervened`, the
    guardrail's message *"This message was not triaged: the application's guardrail blocked it."*, 0 tokens.
    `PROMPT_ATTACK`, confidence `MEDIUM`, filter strength `HIGH`, `BLOCKED`; 34 of 34 characters guarded.
  - `b`, the guardrail named by its id: the same block and the same trace.
  - `d0`, the denied topic inside the guard tag: blocked by the topic `Investment advice` (`DENY`), 73 of 73
    characters guarded.
  - `d1`, the guard tag holding the `ready` message and the topic outside it: blocked by `PROMPT_ATTACK`
    `MEDIUM` on the tagged text; 34 of 107 characters guarded, so the topic's 73 were not assessed.
  - `e`, the second guardrail, one word filter: `stop=end_turn`, *"Ready."*, 8 tokens in and 3 out.
  - The message the day's probes send reads as a prompt attack to the application's guardrail when the whole
    message is assessed. The triage assesses its guard tag alone: 40 messages, 2 blocked (reading 4).
  - Verification xxxix reads in full. The `DRAFT` is refused by the identity deny and the id is admitted. A
    model outside the profile is refused by the SCP `p-tgda7n58`, the wording shown; the identity deny's part
    is not measured (Lesson 20). A message outside the guard tag is admitted by IAM and not assessed by the
    guardrail.
- **[user] Verification lx** (`lx.py`, SHA-256 `b355b330…`) from `jup-ml-dev`, MLflow's client 3.17.2 against
  the app's 3.16.0:
  - the experiment `app-ml-lx` created (id 2); the run `c058995da0d44cb086359271b2427c61` from 20:53:34; the
    model `models:/m-c30660f6dda246dca5558e9d71f494ad`, its artifacts under the app's store,
    `…/dev/data/ml/mlflow/workspaces/default/2/c058995da0d44cb086359271b2427c61/artifacts`;
  - *"Successfully registered model 'app-ml-lx'."*, *"Created version '1' of model 'app-ml-lx'."*: MLflow's
    registry holds `app-ml-lx` version 1 `READY`;
  - the account's groups read `app-ml-dev` and `ml-demo-xgboost` before the run and at once, 30 s and 90 s
    after it, and the same from the laptop at 21:01 (**[Claude]**);
  - MLflow's `uv export` exported 0 dependencies and fell back to inferring them from the installed packages,
    logging `torch 2.13.0+cpu` as `torch==2.13.0`.
  - Verification lx reads no. With the app's `AutoModelRegistrationDisabled`, a model logged under a
    registered name stays in MLflow's registry and creates no SageMaker group or version, as step 3.2 read in
    `ml-demo-mlflow`. AWS's `ml/training` example asserts the version.
- **[user] Reading 5's portal half**: the chat playground of `app-genai-dev` on Nova Lite, *"Reply with the
  single word: ready."*, answered *"Ready."*. **[Claude]** The trail:
  - `ListFoundationModels` at 20:52:20, 20:52:21 and 20:52:44, and `ConverseStream` at 20:52:48, as
    `awsds-sandbox-bedrock-model-consumption` in sessions `28f1b390-…@cty232yk8f2zyo` and
    `28f1b390-…@d747chsyrc379s`, the second created at 20:52:47;
  - from the browser, with no `vpcEndpointId` and the host header `bedrock-runtime.us-west-2.amazonaws.com`;
  - `modelId` the domain's profile `csu817ovl4kz`, Nova Lite, tagged `AmazonDataZoneDomain` alone and created
    2026-10-19; `maxTokens` 5120; no `guardrailConfig`; 8 tokens in and 3 out on the stream's service event.
  - The deny binds the application's role. The playground calls as the domain's consumption role, which the
    deny does not bind, so the playground answers under it with no guardrail (`SUP-300`). The account's
    guardrail of reading 6, enforced on the model for every caller, is the layer that reaches this path.

## 2026-11-22 — Day 3's sitting C: the registry's score

*Claude writes this entry, from the workflow's logs, the trail and the SageMaker API, as the infrastructure
user with `InfrastructureAccess` through `awsds-infra-sandbox-1`. The run is the user's. Times UTC.*

- **The run `QCRC1Im4FuKYOMS`**, `MODEL_SOURCE` `registry` in the working copy's `dev` stage: `SUCCESS` from
  20:52:16 to 21:11:44. `prepare` took 613 s, `resolve` 13, `score` 339, `check` 9 and `cleanup` 7.
- **`resolve`**, 21:03:58: *"created app-ml-score-5rzplmk81vma34 from
  arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:model-package/app-ml-dev/1: sha256 852032c5…"*.
  - The trail: `CreateModel` at 21:03:58 as the project role in the worker's session `AmazonMWAAServerless`,
    through `vpce-0dc0f341029459864`.
  - The request: `containers` one element, `modelPackageName` the version's ARN alone; `executionRoleArn` the
    project role; the tags `AmazonDataZoneProject`, `AmazonDataZoneDomain` and `AmazonDataZoneScopeName`
    `dev`; `vpcConfig` `sg-028f033a218b701b2` with the two subnets; `enableNetworkIsolation` true.
  - The model read back with the container's `ModelPackageName` and `Mode` `SingleModel`.
  - The version, `Approved`, holds the image by its digest `0b5d9341…`, `ModelDataUrl` under
    `app-ml/models/sha256/852032c5…/`, and `ModelDataETag` `1792fa29…`, the field the service set (`SUP-462`).
- **`score`**: the transform `app-ml-score-20261122T210440`, created at 21:04:42, ran on one `ml.m5.large`
  from 21:08:05 to 21:09:36, its volume under the project's key `a81b1ef3-…`; the output under
  `app-ml/predictions/20261122/`.
- **`check`**: *"app-ml-score-20261122T210440: 200 prediction(s) for 200 line(s), AUC 0.847556, MIN_AUC
  0.7"*, `source` `registry`, the training job `app-ml-train-20261122T193009`. The AUC is the prefix score's,
  the same bytes.
- **`cleanup`**: *"Model app-ml-score-5rzplmk81vma34 deleted successfully."* at 21:11:44; no model created
  since 20:52 remains.
- Verification lix's first half reads yes: a worker creates a model from a version's `ModelPackageName` as
  the project role, under the D13 boundary and the `Workloads` OU, with `VpcConfig` and network isolation.
  Its second half is not measured: the object was unchanged, so a comparison of the version's
  `ModelDataETag` with it reads the same whether it happens or not (Lesson 13). Measuring it needs an object
  whose ETag differs from the version's, which under SSE-KMS any rewrite of the object gives, and which
  leaves `app-ml-dev/1` unusable if the service compares.
- The working copy's `MODEL_SOURCE` returns to `prefix` on the `dev` stage, the user's edit, before the day
  ends.

## 2026-11-22 — Day 3's sitting C: reading 6's first apply, the account's guardrail created and its enforcement refused

*Claude writes this entry; the applies are Claude's, as the infrastructure user with `InfrastructureAccess`
through `awsds-infra-sandbox-1`, on the user's *"Autorizo a leitura 6"* and *"Autorizo os três applies."*,
answering a question that named the three. Times UTC.*

- **21:11:25, the saved plan's apply**: refused before it began, *"No valid credential sources found"*. The
  `awsds` session's token had expired at 21:08:53 and its refresh failed (*"InvalidGrantException"*), while
  `aws sts get-caller-identity` still answered from cached role credentials. The user signed in again at
  about 21:11:47; the orchestrating session relayed it at 21:12. Claude's `./aws/login.py --help`, run to read
  the script's options, started `aws sso login --no-browser`, since the script passes no argument through; it
  was stopped with no approval.
- **21:17:21, the saved plan's apply again**: `aws_bedrock_guardrail.account[0]` created in 2 s
  (`awsds-sandbox-account-guardrail`, `k1w4bpgvtnt4`) and its version in 1 s. The configuration was refused by
  Cloud Control: *"Model validation failed (#/ModelEnforcement: required key [ExcludedModels] not found)"*. The
  plan had shown `excluded_models = []`.
- **21:20:42, a plan with `excluded_models` naming `amazon.titan-embed-text-v2:0`**: `1 to add`. Its apply at
  21:21:10 was refused by Bedrock: *"If modelEnforcement is present, excludedModels can only be nonempty if
  includedModels is ['ALL']."* (`InvalidRequest`). The code change was reverted.
- Through `awscc` 1.106.0 the configuration cannot name Nova Lite alone (`SUP-466`). The account holds the
  guardrail and its version 1, with no configuration (`ListEnforcedGuardrailsConfiguration` empty), and the
  deny stands.

## 2026-11-22 — Day 3's sitting C: reading 6 deferred and both switches back to `false`

*Claude writes this entry; the apply is Claude's, as the infrastructure user with `InfrastructureAccess`
through `awsds-infra-sandbox-1`, the third of *"Autorizo os três applies."*. Times UTC.*

- **About 21:26, the user's decision**: *"Adie a leitura 6"*. Reading 6 rides with 6e 6.4's later sitting,
  and the account guardrail's configuration is redesigned with nothing up (`SUP-466`).
- **21:27:37, the third apply**: a plan saved at 21:27:14 from a tree identical to `origin/main`, both
  switches `false`, *"Plan: 0 to add, 1 to change, 2 to destroy."*. The account guardrail's version and the
  guardrail were destroyed in 1 s each, and `awsds-sandbox-bedrock-application` lost the deny's statement:
  *"Apply complete! Resources: 0 added, 1 changed, 2 destroyed."*. The re-plan reads *"No changes."*
  (exit 0), `ListEnforcedGuardrailsConfiguration` reads none, and the account's guardrails are
  `mn3wavwk9jx7` (`app-genai-dev`'s) and `razikgicppzy`.
- **Left for later**: the probe run once with `EXPECT_UNGUARDED` back on `answered` (line 55 of
  `app-genai-dev`'s working copy), and `MODEL_SOURCE` back on `prefix` (line 80 of `app-ml-dev`'s).

## 2026-11-22 — Day 3's sitting C: the probe without the deny, and the working copies restored

*Claude writes this entry from the output the user pasted at 21:42 and from the run's task log, read as the
infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`. The edits and the run are the
user's, from `jup-app-genai-dev` and `jup-ml-dev`. Times UTC.*

- **`app-genai-dev`'s working copy**: `EXPECT_UNGUARDED` back on `answered` at line 55 of the manifest, the
  `dev` stage; lines 84 and 113 keep `refused`.
- **The probe's run `oIak5MKc0ZlrMj6`**, workflow `probe-anvonKMpvI`: `SUCCESS` from 21:42:11.7 to
  21:42:48.4. The task `unguarded` took 7 s and logged at 21:42:47.5 *"the request without a guardrail:
  answered, answered expected"*: 6 characters, 8 input and 3 output tokens, `end_turn`, `passed` true,
  the model `application-inference-profile/ciceumyodl7y`.
- The CLI printed its `ListTagsForResource` warnings on 15 other workflows, as on every run since Stage 19
  (`sagemaker-application.md` §D).
- Reading 4's after-control reads yes: with the deny's statement removed at 21:27:37, a request naming no
  guardrail answers again. `probe-report.json` holds the run (`ML-11`, 22:56).
- **`app-ml-dev`'s working copy**: `MODEL_SOURCE` back on `prefix` at line 80, the `dev` stage; lines 123 and
  167 keep `registry`.

## 2026-11-22 — Day 3's sitting C: pass 5, the pipeline from the SDK (5.1, 5.2, 5.4)

*Claude writes this entry from the output the user pasted, the SageMaker API and the trail, read as the
infrastructure user with `InfrastructureAccess` through `awsds-infra-sandbox-1`. The `upsert`s and `start`s
are the user's, from `jup` in `eighth-experimentation`; the three fixes are Claude's commits. Times UTC.*

- **The space**: `jup`'s clone at `b3b900b`; `extra_values.json` names the XGBoost tag `3.0-5` and the MLflow
  App. `awsds-workflows values --project avhvbqn37ty7m8` filled `JOB_IMAGE_URI` with the house image by its
  digest in Production's `awsds-prod-ecr-dev-env`, `sha256:a6f9b5ab…`.
- **The first `upsert`**, pasted at 21:56: `prepare.py` uploaded to `shared/ml-demo/pipeline/code/`, then
  `DescribePipeline` of the free name refused at 21:56:03 through `vpce-0dc0f341029459864`, *"no
  identity-based policy allows"*. The blueprint grants it on a pipeline tagged with the caller's project
  alone (`SUP-267`, read again). `fc6bb0e0` makes `upsert` look the name up with `ListPipelines`.
- **The second `upsert`**, pasted at 22:04: `CreatePipeline` refused, *"ValidationException: Unable to parse
  pipeline definition. Model Validation failed: string '…' with length=262 cannot be greater than max=256.0
  defined for ContainerArgument."* The 256-character limit per item is the API's documented one. `93e136ee`
  shortens `Prepare`'s command to 191 characters with a `chown -R` of the output's parent.
- **The third `upsert` and the first `start`**, pasted at 22:12: the pipeline created at 22:12:23, as the
  project role in the space's session `SageMaker` through `vpce-0dc0f341029459864`. Its tags: the script's
  `AmazonDataZoneProject` and the six others of `SUP-408`'s seven, which the space adds.
  - The execution `epycqlyvfigz` started at 22:12:29. `Prepare` failed from 22:12:29.8 to 22:12:30.9:
    *"ClientError: Reserved tag key prefix found for 'AmazonDataZoneProject' in Step: Prepare"*. No
    `CreateProcessingJob` followed. The README's "What the first run decides" had named this reading.
  - `49dde59a` removes `Tags` from the three job steps (`SUP-467`).
- **The fourth `upsert` and the second `start`**, pasted at 22:16: the pipeline updated at 22:15:55, its
  version 2, and the execution `w8qa46pmftoy` started at 22:15:56. `ListPipelineVersions` reads version 1
  with `epycqlyvfigz` and version 2 with `w8qa46pmftoy`: an `UpdatePipeline` with a changed definition adds a
  version. Whether an unchanged one does stays verification lxi's.
  - `Prepare`, 22:15:56.8 to 22:25:59.8: `CreateProcessingJob` at 22:15:57 as the project role in the
    session `sagemaker-pipeline-w8qa46pmftoy-Prepare`, invoked by `pipelines.sagemaker.amazonaws.com`, no
    `vpcEndpointId`. The job `pipelines-w8qa46pmftoy-Prepare-kiB0JNeozt`: isolation and inter-container
    encryption true, `sg-0fee1c059b82e3562` with the two private subnets, `ml.t3.medium`, the volume and the
    output under the project key `a81b1ef3-…`. Its container log at 22:23:57: Python 3.12.14, pandas 2.3.3,
    7032 rows split 4922, 1054 and 1056.
  - The request's eight tags: the pipeline's seven less `AmazonDataZoneUser`, plus
    `sagemaker:pipeline-step-name` and `sagemaker:pipeline-execution-arn`. The job reads the same eight
    (`SUP-467`).
  - `Train`, 22:26:00.7 to 22:28:14.7: `pipelines-w8qa46pmftoy-Train-3Qrj5R3Zrm` completed from 22:26:50.6
    to 22:28:14.3, 84 s billed on `ml.m5.xlarge`, `validation:auc` 0.82091 and `train:auc` 0.95127, the
    four settings, the project key and the same eight tag keys; the image `sagemaker-xgboost:3.0-5`.
  - `CheckAuc`, 22:28:15.1 to 22:28:15.4, outcome `True`.
  - `Register`, 22:28:16.1 to 22:28:18.0: `ml-demo-xgboost/2`, `PendingManualApproval`, created at
    22:28:17.9 with the description *"from the pipeline ml-demo-pipeline"*. The registry held version 1
    alone, `Approved`, so the pipeline's version is the second where 5.2 expects the third.
- Verification xi's pipeline half reads yes: `CreatePipeline` with the project role as `RoleArn` was
  admitted, so the role passes itself to SageMaker for a pipeline, and each step's job runs as that role
  in the session `sagemaker-pipeline-<execution id>-<step name>`. The endpoint half is pass 4's.
- **5.2's portal reading**, from about 22:28, through Claude in Chrome in the Data Scientist User's portal
  session, on the user's *"faça a leitura na sessão no chrome"* (22:27:45). The *ML pipelines* page read
  *"No pipelines"* with *"Results are cached"* until *Refresh* listed `ml-demo-pipeline`. The pipeline's
  page has the tabs *Executions*, *Graph*, *Parameters* and *Information*, and the buttons *Execute*,
  *Visual editor* and a menu. *Executions* lists `execution-1795385756381`, `Succeeded` in 12m 22s, and
  `execution-1795385549186`, `Failed` in 2s: the portal names an execution by its creation time in
  milliseconds, not by its id. The graph: `Prepare` → `Train` → `CheckAuc` → `Register` on true or
  `AucBelowThreshold` on false, the run's four green.
- **A download without the user's yes**, at about 22:31: Claude's click meant for *Visual editor* landed on
  the menu's *Download pipeline definition (JSON)*, which Escape had not closed. Chrome saved
  `execution-1795385756381_definition.json`, 13,316 bytes, to the laptop's Downloads folder. Claude told the
  user at once. The file stays until the user decides.
- Verification xvi reads yes: the downloaded definition equals the live `DescribePipeline` definition, and
  `pipeline.py compare` read the live one equal to `definition.json` with its 12 placeholders filled.
- **5.4**: `ML-6` at 22:56:05 passes `ml-demo-pipeline`: the project role, the four settings, `Succeeded`,
  5 steps as in the committed source.

## 2026-11-22 — Day 3's sitting C: verification xxiv's `Retrieve`, and pass 4 deferred

*The `Retrieve` is the user's, from a notebook in `jup`; Claude writes this entry from the output the user
pasted at 22:19 and from CloudWatch and the trail, read as the infrastructure user with
`InfrastructureAccess` through `awsds-infra-sandbox-1`. Times UTC.*

- **The call**: `Retrieve` on the knowledge base `QWDNVYXADH` (`ACTIVE`, its data source `JXKIPOER3T`
  holding `break-glass.md` and `buildbox.md`), the question *"Who receives the alarm when the root user
  signs in?"*, `numberOfResults` 3. Three results, all from `break-glass.md`, scored 0.507, 0.474 and 0.465.
- **The door**: `bedrock-agent-runtime`'s endpoint `vpce-0915f48c2198cb60b` (private DNS on, in
  `subnet-016b5a3a62c739894` alone). Its PrivateLink counters hold one datapoint since the endpoint's
  creation at 18:14:07, read at 22:23:53: at 22:19, `NewConnections` 1 and `BytesProcessed` 14,870.
  `Retrieve` is a data event, absent from `lookup-events`.
- The query's embedding: `InvokeModel` at 22:18:57 as the project role in the session
  `BKB-Retrieve-QWDNVYXADH-<uuid>`, invoked by `bedrock.amazonaws.com` through the service's own endpoint id
  `vpce-0cf920938fc4d8fc6` (`SUP-426`).
- Verification xxiv's `Retrieve` half reads yes: the project role reaches the knowledge base from a space
  through the `bedrock-agent-runtime` endpoint. Its catalog half has no object (`SUP-446`, `SUP-448`).
- **About 22:25, the user's decision on pass 4**: *"Não, fica para depois"*. §N.10's day 1 had not run it,
  and the orchestrating session had offered it to this sitting after xxiv. The endpoint, the transform and
  the negatives wait for a later sitting.

## 2026-11-22 — Day 3's sitting C: 5.3, the visual editor, and `ML-7`

*The pipeline is Claude's, built, saved and run twice through Claude in Chrome in the Data Scientist User's
portal session, on the user's *"Pode fazer"* at about 22:38, answering whether Claude should build 5.3's
one-step pipeline. Claude reads the SageMaker API and the trail as the infrastructure user with
`InfrastructureAccess` through `awsds-infra-sandbox-1`. Times UTC.*

- **`ML-7` before the editor**: two MLflow Apps at 21:30:38, `app-ml-dev-mlflow` and `ml-demo-mlflow`. The
  same two after the list, executions and graph pages (22:27:53, 22:30:09) and after the editor's first
  entry (22:32:19, 22:32:41, 22:33:02).
- **The editor over `ml-demo-pipeline`**, opened at about 22:32 (`…/pipelines/view/ml-demo-pipeline/edit`):
  the palette holds *Code* (*Run notebook or code*, *Run callback*, *Run lambda function*), *Data
  Preparation* (*Process data*), *Model Development* (*Train model*, *Fine tune model*), *Deployment &
  Inference* (*Register model*, *Create model*, *Deploy model (endpoint)*, *Deploy model (batch
  inference)*) and *Logic* (*Condition*, *Fail*).
  - `Prepare`'s form: inputs, outputs, the image, entry point and arguments, the instance, the stopping
    condition, and under *Advanced settings* *Caching*, *Retry* and *Security*.
  - *Security* shows the project role, `vpc-00dca74a35159b11c`, the two subnets, `sg-0fee1c059b82e3562` and
    the project key, greyed. No field sets network isolation or inter-container encryption.
  - `Train`'s form is the same shape, with the algorithm's image and input mode, metrics, hyperparameters
    and a checkpoint.
- **A new pipeline with one *Train model* step**: the channel `train` (`…/pipeline/w8qa46pmftoy/train`,
  `text/csv`); the output `…/shared/ml-demo/pipeline/editor/model`; `sagemaker-xgboost:3.0-5`, `File`,
  `ml.m5.xlarge`, 30 GB; `objective` `binary:logistic`, `eval_metric` `auc`, `num_round` 20; 600 s.
  *File* → *Save* asked for no name. `CreatePipeline` at 22:45:27 named it `Pipeline-1795387181754`, the
  create page's opening time in milliseconds. The caller was the project role in the person's session, from
  the laptop's browser with no `vpcEndpointId`.
  - The pipeline's tags are the portal's four: `AmazonDataZoneProject`, `AmazonDataZoneDomain`,
    `AmazonDataZoneScopeName` `dev` and `AmazonDataZoneUser`.
  - The definition at 22:46:40 holds the step `Training_1C268` (display name *Train model*) with the role,
    the algorithm, the instance, the stopping condition, the channel, the hyperparameters and the output's
    `KmsKeyId`. It holds no `VpcConfig`, no `VolumeKmsKeyId` and neither isolation flag: *Security*'s
    network fields and its key reach the output alone.
- **The execution `ml-demo-editor-1`, `buk3zbhzkw6s`**, started at 22:46:10. `Training_1C268` failed from
  22:46:11.3 to 22:46:12.5: *"ClientError: Failed to invoke sagemaker:CreateTrainingJob. Error Details: 1
  validation error detected: Value null at 'inputDataConfig.1.member.dataSource.s3DataSource.s3DataType'
  failed to satisfy constraint: Member must not be null"*. The channel's form showed *S3 data type*
  `S3Prefix`, its default, without writing it. `lookup-events` holds no `CreateTrainingJob` for it.
- **The type chosen by hand**: `ManifestFile` and back to `S3Prefix`, then *Save*. `UpdatePipeline` at
  22:48:34 wrote version 2 with `S3DataType` `S3Prefix`.
- **The execution `ml-demo-editor-2`, `rl26r4j8ychr`**, started at 22:49:20. `Training_1C268` failed from
  22:49:20.9 to 22:49:22.7: *"ClientError: Failed to invoke sagemaker:CreateTrainingJob. Error Details: User:
  arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/sagemaker-pipeline-rl26r4j8ychr-Training_1C268
  is not authorized to perform: sagemaker:CreateTrainingJob on resource:
  arn:aws:sagemaker:us-west-2:<Sandbox Account 1>:training-job/pipelines-rl26r4j8ychr-Training-1C268-TomRXvYbLk
  with an explicit deny in a permissions boundary: arn:aws:iam::<Sandbox Account 1>:policy/awsds-sandbox-project-boundary"*.
  - The trail's `CreateTrainingJob` at 22:49:22: `AccessDenied` with the same text, `requestParameters`
    null, invoked by `pipelines.sagemaker.amazonaws.com`.
  - The request lacked `VpcConfig`, the volume key and both flags, so four of the boundary's statements
    match it: `DenySageMakerJobsOffVpc`, `DenySageMakerJobsWithoutVolumeEncryption`,
    `DenySageMakerJobsWithoutNetworkIsolation` and `DenySageMakerJobsWithoutInterContainerEncryption`. The
    wording names the policy, never the statement (Lesson 20).
- Verification xii's 5.3 half: the pipeline-step forms set none of the four settings. They show the
  project's network and key greyed, write the key into the output alone, and offer no field for either flag.
  The portal's pipeline create is admitted, and its training job refused by the boundary.
- **`ML-7` after**: two apps at 22:50:08, and no `CreateMlflowApp` since 22:30. The guide's sentence that
  *"A default MLflow application will be created when you enter the pipeline visual editor."* did not hold
  in this project's domain.
- **`ML-6` at 22:56:05** fails on `Pipeline-1795387181754`: no `VpcConfig`, no isolation, no inter-container
  encryption, no volume key, the latest execution `Failed`, 1 step unlike the committed source. The pipeline
  stands until the user decides on it.

## 2026-11-22 — Day 3's sitting C: the closing reads, and 6d's remainder left

*Claude writes this entry; reads as the infrastructure user with `InfrastructureAccess` through
`awsds-infra-sandbox-1` (account Sandbox Account 1), and no AWS write. Times UTC.*

- **[user] 6d's remainder** did not run: *"Vamos deixar o bloco 6d para outra sessão"* at about 23:22 (6d's
  log). The lowering is §N.10's day 2's, which shares the raise.
- **The spaces**: at 23:22:52 no app stands in `eighth-experimentation`'s, `app-ml-dev`'s or `app-genai-dev`'s
  domain. `jup`'s app was deleted at 23:19:09 by the idle shutdown (`SUP-221`). `jup`, `code`, `jup-ml-dev`
  and `jup-app-genai-dev` stand with no app.
- **The portal**: this session's Claude in Chrome tab group no longer existed at about 23:24. Every other
  portal tab is the user's or §N.10's.
- **`./aws/sandbox-ml.py` at 23:28:43**: 71 passes, one fail and 89 notes, every call returned. The fail is
  `ML-6` on the editor's `Pipeline-1795387181754`, as at 22:56:05; `ML-6` passes `ml-demo-pipeline`.
- **`./aws/catalog.py` at 23:32:28**: 19 checks passed or noted and one failed, `CT-17`, on two grants to
  `awsds-sandbox-warehouse-access-avhvbqn37ty7m8` in Production's `app_etl.trades_notional`, `DESCRIBE` and
  `SELECT`, which §N.10 keeps. None is day 3's. §N.10's day 2 was publishing `eighth-experimentation`'s assets
  through the portal at the time (its 2.3).
- **Standing from day 3**: `ml-demo-pipeline` and its runs, the registry's versions, `sandbox/bedrock/`'s
  switches `false` since 21:27:37, and the editor's pipeline until the user's word.

## 2026-11-22 — Day 3's sitting C: the editor's pipeline kept, `EXC-28`

*Claude's hand, recording the user's answers in chat at about 23:37 UTC; no AWS call.*

- **[user] The editor's pipeline**: *"Pode manter o pipeline do editor"*. `Pipeline-1795387181754` stays in
  `eighth-experimentation` as `SUP-468`'s record, and `ML-6` fails on it while it stands: `AWS_STATE.md`
  `EXC-28`, the id told to §N.10's day 2.
- **[user] The downloaded file** `execution-1795385756381_definition.json`, from 5.2's portal reading at about
  22:31: *"O arquivo em downloads eu msm apago depois"*. It is the user's to delete.

## 2026-11-22 — Day 3's sitting C: the editor's pipeline deleted, `EXC-28` closed

*Claude writes this entry and ran the delete on the user's word in chat, as the infrastructure user with
`InfrastructureAccess` through `awsds-infra-sandbox-1` (account Sandbox Account 1). Times UTC.*

- **[user] The editor's pipeline**, at about 23:45: *"Apague entao o pipeline, pfv"*, reversing the decision
  of about 23:37.
- **Before the delete, at 23:44:50**: `Pipeline-1795387181754` `Active`, created 22:45:27 and last modified
  22:49:22, its role the project role `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`; two executions,
  `ml-demo-editor-1` (22:46:10) and `ml-demo-editor-2` (22:49:20), both `Failed`.
- **The delete**: `aws sagemaker delete-pipeline --pipeline-name Pipeline-1795387181754` exit 0, answering the
  pipeline's ARN. CloudTrail, read at 23:47:55: `DeletePipeline` at 23:46:38 by
  `AWSReservedSSO_InfrastructureAccess_59e5b26af457128d`, no `errorCode`, no `vpcEndpointId`,
  `aws-cli/2.37.12`.
- **After it, at 23:46:38**: `describe-pipeline` answers *"ResourceNotFound … Pipeline '…:pipeline/Pipeline-1795387181754'
  does not exist."*, and `list-pipelines` lists `ml-demo-pipeline` alone.
- **`./aws/sandbox-ml.py` at 23:51:46**: 71 passes, no fail and 89 notes. `ML-6` passes `ml-demo-pipeline`, the
  one pipeline listed. One call failed, `service-quotas list-aws-default-service-quotas --service-code
  sagemaker` with a 408 and no message, so the script exited 1. That call fills the quota table's *AWS
  DEFAULT* column, and the checks read as the re-run's below, two `ML-9` notes in another order.
- **`./aws/sandbox-ml.py` again at 23:58:04**: *"all checks passed"*, 71 passes and 89 notes, every call
  returned, exit 0.
- **Records**: `AWS_STATE.md` `EXC-28` closed; the hand-over note to §N.10's day 2 corrected and day 2 told.
  `SUP-468` stands on this log's readings of 5.3.

## 2026-11-23 — 10.5 written and planned: the boundary's exception, `TM-36` and the targets' slices

*Claude's hand, a subagent of the session coordinating 2026-11-22's batch, on the branch `claude/stage17-10-5`
from `main` at `5fbaaf4f`, brought to `a42e4c9d` (`TM-28`'s applies) before its first commit. Reads and saved
plans as the infrastructure user with `InfrastructureAccess` in `Staging Account` (`awsds-infra-staging`) and
`Production Account` (`awsds-infra-prod`); no AWS write. Terraform 1.17.2. Times UTC.*

- **[Claude] The module**: `sagemaker-prereqs`' input `bedrock_exception`, null by default. Where it is set,
  the ceiling's allow becomes `NotAction` `bedrock:*` and five statements follow: the invoke on the profile and
  its model under `ArnLike` `bedrock:GuardrailIdentifier` `guardrail/*:*`, `ApplyGuardrail` on the account's
  guardrails, the `guardrail` task's seven calls in two statements, and the deny of `CreateGuardrailVersion`,
  `TagResource` and `UpdateGuardrail` on the account's own guardrail. A validation refuses the input beside
  `bedrock` in `fenced_services`.
- **[Claude] The boundary's diff**, read before the tag from each target's plan against the local path, the
  profile's and the guardrail's ARNs replaced by placeholders since both are known only after the apply
  (01:11 and 01:14): the ceiling, `bedrock:*` out of `DenyServicesNoProjectUsesHere` and the five statements,
  nothing else. Staging's boundary goes from 14 statements to 19 and 4,785 characters, Production's from 15 to
  20 and 5,112, of IAM's 6,144. Both prior documents name `agent-registry:*`, so no plan carries `TM-28`'s
  fence.
- **[Claude] The tag**, by Recipe B: the module's commit `ad2a6e0d` at 01:16:54; `git ls-remote --tags origin`
  read `sagemaker-prereqs-v0.14.0` as origin's newest; `sagemaker-prereqs-v0.15.0` tagged and pushed with the
  branch, origin answering `ad2a6e0d` for it.
- **[Claude] The account-level configuration's shape**, decision 27 (a) on every model: no `model_enforcement`,
  since `awscc` 1.106.0 cannot send named models alone (`SUP-466`). Cloud Control's schema, read with
  `describe-type` at 01:31:57, requires `GuardrailIdentifier` and `GuardrailVersion` alone and says a
  configuration without `ModelEnforcement` is enforced on all models; the plans show `model_enforcement`
  `(known after apply)`. No other model call runs in a target: Claude Code and the scoped models are Sandbox's.
- **[Claude] The plans**, each `-input=false` and saved to a plan file:
  - `staging/studio/` at 01:19 and `production/studio/` at 01:20, at `v0.15.0`: *"Plan: 6 to add, 2 to change,
    0 to destroy."* each. The profile `awsds-<env>-app-genai` copied from `amazon.nova-lite-v1:0` and tagged
    with the deployment project; the guardrail `awsds-<env>-account-guardrail` with 10.4 step 6's topic, its
    version and the configuration; the policy `awsds-<env>-app-genai` and its attachment to the project role;
    the boundary; and `person_session`'s document `(known after apply)` (`SUP-356`).
  - `staging/chains/` at 01:21, *"Plan: 12 to add, 1 to change, 0 to destroy."*: for `app-genai-triage` and
    `app-genai-probe` a machine, a schedule `DISABLED`, two failure rules and their targets each, and the chain
    role's statements gaining both workflows' names and `app-genai`'s stage-variables parameter.
    `production/chains/` at 01:22, *"Plan: 6 to add, 1 to change, 0 to destroy."*, `app-genai-triage` alone.
  - `staging/foundation/` at 01:23 and `production/foundation/` at 01:24, with the alerts var-file: *"Plan: 0 to
    add, 1 to change, 0 to destroy."* each, the deploy role's state statement gaining `<env>/studio/`'s key.
  - `staging/egress/` and `production/workloads-egress/`, both down, from 01:25 to 01:26: *"Plan: 18 to add, 0
    to change, 0 to destroy."* with no group, and *"Plan: 20 to add, 0 to change, 0 to destroy."* with
    `TF_VAR_optional_service_groups='["bedrock-base"]'`, `bedrock-runtime`'s policy naming
    `bedrock:ApplyGuardrail` and `bedrock:InvokeModel`, `bedrock`'s the `guardrail` task's seven calls.
- **[Claude] `bedrock:ApplyGuardrail` on the runtime endpoint**: the triage's calls did not need it in Sandbox
  (xxxviii). It stands for the account's enforced guardrail, whose ask of the caller is verification l, as the
  boundary's and the role's statements do.
- **[Claude] Records**: `TM-36` and its channel row, open; `TM-30` amended with its `DT-14` trigger;
  `FENCED_GENERATIVE` in `aws/deploytargets.py` without `bedrock`; `docs/NETWORK.md`; the Makefile's help;
  `SUP-466`'s later reading; `promotion.md` §N.6 item 8 and §N.11.2 step 2; this stage's `TM-28` sentences,
  that apply having run at 00:46 to 00:47.

## 2026-11-23 — `TM-36` accepted by the user

*Claude's hand, in the session coordinating 2026-11-22's batch, on the branch `claude/orchestrator-2026-11-23`.
No AWS call. Times are UTC.*

- **[The user] The acceptance**, at 01:48 in that session's chat: *"Aceito o TM-36"*. It answered a question
  that laid out the channel, decisions 22 (a), 23 (a), 24 (b) and 27 (a), the three bounds (the one model, the
  account's guardrail, the retention mode `none`), what the targets have not measured (`SUP-466`'s every-model
  shape, verification l), and the alternative of putting decisions 22 and 24 again.
- **[Claude] Records**: `TM-36` and its channel row accepted in `threat-model.md`, its waiting bullet narrowed
  to the applies; this stage's `Status` row and step 10.5; `promotion.md` §N.6 item 8; the waiting list's 10.5
  row; CLAUDE.md's Stage 11 and Stage 17 rows. #388 merged at 01:51:14 with its head before this record.

## 2026-11-23 — R2's pre-flight for `app-ml` and `app-genai`, their pins moved to `4401f91`, and 9.11 unwritten

*Claude's hand, a side session of the session coordinating 2026-11-22's batch, on the branch
`claude/prep-pending-sittings-369d94` from `main` at `b89b5a0f`. No AWS call: each job ran on the laptop
over the applications' trees at `b89b5a0f`, copied outside the worktree, on CPython 3.12.13 and uv
0.12.13. Times UTC.*

- **[Claude] The `test` jobs**, at 02:14: `app-ml` `uv sync --locked`, `uv lock --check --project code`,
  ruff clean, 100 passed; `app-genai` ruff clean, 95 passed; the lint with each pipeline's options *"ok: 6
  arquivo(s)"* and *"ok: 3 arquivo(s)"*, at the pin `37cb5a6` and at `4401f91` alike. `app-etl`, 9.11's
  application: 100 passed and 1 skipped (the parametrized case its publish gate admits), the lint *"ok: 9
  arquivo(s)"* at `196acee` and at `4401f91`.
- **[Claude] The pins**: `awsds-workflows`' `main` reads `4401f91` (#29, 2026-11-21) as its head. Between
  `37cb5a6` and it the package changed `lint.py` and `render.py` alone, so `package-task` builds the same
  archive. `examples/app-ml/` and `examples/app-genai/` moved to `4401f91` (`.gitlab-ci.yml`, the README,
  and `probes/operator.yaml`'s comment), the pin `app-dbt` holds since 2026-11-21, so the first tags of 9.7
  and 10.6 carry it (`promotion.md` §N.11.1 step 6). `lint probes/operator.yaml` is refused by `operador`
  with the same line at both commits.
- **[Claude] The `pip-audit` job**, its script read from this repository's `ci-gates/gates.gitlab-ci.yml`
  and run verbatim, at 02:17: `app-ml` with `GATES_UV_PROJECTS=code`, *"48 of 48 pinned package(s)
  audited, 0 blocking vulnerability(ies)"*, exit 0. `app-genai`'s empty case (Lesson 87), with
  `GATES_UV_PROJECTS=.`: the export holds no pin, `grep -c` exits 1 under `set -eu`, and the job ends with
  exit 1 and no line after *"the runtime set its lock pins"*, as on 2026-11-17. The pipeline sets no
  `GATES_UV_PROJECTS`, so R2 runs no `pip-audit` for `app-genai`.
- **[Claude] The `build-task-code` jobs**, at 02:23, as written but on macOS: `code/app-genai.zip` 8 files,
  15,715 bytes, imported on 3.12.13; `code/app-ml-train.zip` 15,910,587 bytes, 58,159,344 unzipped, 42
  distributions, and the register and score zips each importing `app_ml_tasks`. Not run: the worker's
  import of `mlflow` and `sagemaker_mlflow` from the Linux wheels, the laptop having no container runtime.
- **[Claude] `./scripts/deploy-application.py --self-check`**: `app-ml` 12 variables per stage, `app-genai`
  3, every stage `ok`.
- **[Claude] `scan-gate`**: `app-ml`'s extends `.gates-ecr-scan`, `allow_failure: true`, so its `FAILED`
  under `SUP-437` leaves the pipeline going. `app-genai` and `app-dbt` build no image and run no
  `scan-gate`.
- **[Claude] 9.11**: its merge request is unwritten at `b89b5a0f`. `workflows/app-etl-train.yaml`, its
  manifest lines and the jobs `staging-model`, `production-register`, `production-approve` and
  `production-transform` stay in `examples/app-etl/`, and `scripts/model-chain.py` still holds `register`
  and `transform`. `promotion.md` §N.11.2 step 3 says so, and `app-etl`'s pin there reads `4401f91`, as
  §N.11.1 step 6 and §N.12.5 do; it read `4613ddc`.

## 2026-11-23 — 10.5's target commands and the later Sandbox sitting's raise, read with nothing up

*Claude's hand, in the same side session and branch as the entry above, at the user's request in its chat
to review the pending plan; two subagents of this session read 10.5 against the code and the sitting of
2026-11-25 against the stage text, and Claude read each finding's two sides before writing it. No AWS
call.*

- **[Claude] 10.5's retention act**: 10.5 sent the targets to `claude-code-sagemaker.md` §M's M1, written
  for Sandbox alone (decision 2): its loops run on `awsds-infra-sandbox-1` over every enabled Region. In a
  target the Region ceiling exempts `bedrock:PutAccountDataRetention` nowhere but `Interactive` (§M's M5,
  `INV-12`), so a copy of the loop on a target's profile would be refused in each Region the ceiling denies. 10.5 now
  holds the targets' commands, `us-west-2` alone: `get-account-data-retention` before and after,
  `put-account-data-retention --mode none` (`--mode` required, response field `mode`, CLI 2.37.12's help),
  on `awsds-infra-staging` then `awsds-infra-prod`, and `list-enforced-guardrails-configuration` after each
  `<env>/studio/` apply. The pass-10 paragraph that cited M1 says the same.
- **[Claude] The order**: `<env>/chains/` reads only `project_key_arn` from `<env>/studio/`
  (`staging/chains/main.tf` lines 20 and 127, `production/chains/main.tf` 19 and 122), and
  `<env>/foundation/` reads no studio state, naming its key in `state_read_keys` alone. No code orders the
  retention act; M1's reasoning puts it before each `<env>/studio/`, which grants the first invoke, and no
  model call runs before 10.6.
- **[Claude] Reading 6's raise**: 10.4 step 6 runs `app-genai-triage` and `app-genai-probe` from
  `app-genai-dev`'s space, which the `mwaa` group's `airflow-serverless` endpoint serves
  (`vpc-egress/endpoints.tf` line 70), and the 2026-11-25 row of `promotion.md` §N.12.1 raises
  `bedrock-base` alone. §N.6 item 7, §N.12.2 and the passes' group rule now name `bedrock-base,mwaa`. The
  §N.12.1 row and the waiting list's Sandbox row, beside pull request #384's changed lines, followed after
  its merge (`663aee70`).
- **[Claude] Reading 6's change**: `sandbox/bedrock/` passes `included_models = var.enforced_models` and
  `excluded_models = []` (`application.tf`), and `enforced_models`' validation refuses an empty list and
  `ALL` (`variables.tf`). Every shape the `SUP-466` decision offers but none needs that slice changed,
  planned and merged before the sitting; the waiting list's row and §N.12.4 say so.
- **[Claude] The waiting list**: the Stage 17 row lost `app-ml-dev`'s model package group, which holds
  `app-ml-dev/1` since 2026-11-22 (registered 20:00:18, approved 20:39:53, the entries above).

## 2026-11-23 — 9.11's application half written, and R2's first pushes read against the projects, nothing up

*Claude's hand, a side session of the session coordinating 2026-11-22's batch, on the branch
`claude/prep-pending-sittings-369d94`, at the user's request in that session's chat to review the pending
plan again and prepare what needs nothing up; subagents of this session read the stage text against the
logs and the code, and Claude read each finding's two sides before writing it. No AWS call.*

- **[Claude] 9.11's application half**, written by a subagent of this session in the branch's worktree and
  reviewed here, committed as `70cbdf17`: `app-etl-train` leaves `examples/app-etl/workflows/`, the
  manifest (its three `workflow.create` and `code/app-etl-train.zip`) and `build-task-code`'s archive;
  the pipeline loses `staging-model`, `production-register`, `production-approve` and
  `production-transform`, and `staging-test` starts the `app-etl` chain alone; `scripts/model-chain.py`
  keeps `approve` with `app-ml`'s call shape, reads the group from `sagemaker/`'s outputs and refuses one
  that is not `awsds-<env>-model-<application>` by its ARN, and loses `register`, `transform` and
  `--package-arn`; `evaluate` and its seven tests, `TRAINING_IMAGE_URI` in the manifest and
  `LINT_ALGORITHM_REPOSITORIES` in the pipeline go with them; the lint pin moves to `4401f91`; the
  hook's and the Makefile's comments follow.
- **[Claude] The offline readings**, on a copy of the tree: `uv sync --locked`, `ruff check` and
  `ruff format --check` clean; `pytest` *"93 passed, 1 skipped"*, `main`'s 100 less the seven removed
  tests; the lint at `4401f91` with the pipeline's options *"ok: 8 arquivo(s)"*, and on a copy whose
  manifest still names `app-etl-train` two `manifest` refusals; `code/app-etl.zip` 5,895 bytes holding
  `app_etl_tasks.py` alone; `./scripts/model-chain.py --check` and `./scripts/deploy-application.py
  --self-check` `OK`, and the commit's hooks passing. No file of the repository calls `register`,
  `transform` or `--package-arn`.
- **[Claude] Left to the estate half and the records**, 9.11's own order: the Glue job's training sets
  (`--TRAIN_PATH`), which no reader takes after the release, since the release changes nothing else;
  `scripts/tfhygiene/targets.py`, with no caller left; `training-image.tf`'s comment in both targets; and
  the files that walk the model jobs.
- **[Claude] 9.7's and 10.6's first push**: R1 left `awsds/app-ml`, `awsds/app-genai` and `awsds/app-dbt`
  empty (Stage 19's log of 2026-11-22), so a first release has no merge request. `sagemaker-application.md`
  §L step 1 now carries the commands, `main` pushed by a Maintainer from `examples/<app>/`'s archive and
  the tree read against its source (Lesson 86); `gitlab.md`'s template procedure stays for a later change,
  its `git rm -q -r .` exiting 128 on an empty clone. 9.7 and 10.6 say so, 9.7's first commit carrying
  `model.json`'s training job and hash.
- **[Claude] R2's order**, `promotion.md` §N.11.2: both raises name `GROUPS=bedrock-base`; Staging stays up
  through step 3's leg and step 4 lowers it; `pip-audit` runs the day of each tag before it (Lesson 77);
  `sagemaker-application.md` §L step 8 names the four changes a project with no list needs to accept a
  finding, since `gates-v0.6.0`'s `case` maps `awsds/dev-env` alone; step 3 reads lxiv's first half and
  Stage 8 xxvi after each leg (§N.5).
- **[Claude] `SUP-464`**'s path corrected to `terraform-live/*/sagemaker/training-image.tf`, and **`SUP-466`**'s
  reading of 2026-11-23 given its log, the entry on 10.5's writing above.

## 2026-11-23 — 10.5's applies: the retention mode, both `studio/` slices, both `chains/` and both `foundation/`

*Claude's hand, in the session "Applies e infraestrutura SSO", on the branch `claude/applies-infra-sso-dccfb0`
from `main` at `d4a8fb9e`, as the infrastructure user with `InfrastructureAccess` in `Staging Account`
(`awsds-infra-staging`) and `Production Account` (`awsds-infra-prod`). The writes are the two retention calls and
the six applies, each on the user's words in the session's chat. Terraform 1.17.2, `aws` 6.69.1, `awscc`
1.106.0. Times UTC.*

- **[The user] The authorization**, in this session's chat: *"Pode prosseguir com os applies e tudo o que pode
  ser feito conforme planejamento e sem a minha intervenção. Autorizo os applies necessários."*; then, answering
  two questions, *"Sim, execute os dois"* for the retention calls the plan gives the user, and *"Autorizo os
  seis"* for the six applies named, from `main`. After the profile's refusal (below), *"Aplique do branch
  agora"* for both `studio/` slices from the correcting commit.
- **[Claude] The plans**, from `main` at `d4a8fb9e`, 12:50:50 to 12:52:18, each as at 10.5's writing:
  `staging/studio/` and `production/studio/` *"Plan: 6 to add, 2 to change, 0 to destroy."*, `staging/chains/`
  *"12 to add, 1 to change"*, `production/chains/` *"6 to add, 1 to change"*, both `foundation/` with the alerts
  var-file *"0 to add, 1 to change"*. The one Terraform change on `main` since #388 is `sandbox/warehouse/iam.tf`.
- **[Claude] Before**, 12:52:49 to 12:52:51: `get-account-data-retention` `inherit` and
  `list-enforced-guardrails-configuration` `{"guardrailsConfig": []}` in both targets; `awsds-staging-project-boundary`
  and `awsds-prod-project-boundary` at `v5`, 14 and 15 statements.
- **[Claude] Staging's retention**: `put-account-data-retention --mode none` in `us-west-2` answered `"mode":
  "none"`, `updatedAt` 12:53:21.832; read back `none`.
- **[Claude] `staging/studio/`'s first apply**, 12:53:33 to 12:53:52, exit 1: the guardrail
  `awsds-staging-account-guardrail` (`l1gy5nt85y9v`), its version and the enforced configuration `dastwpv6xpqh`
  created; the profile refused: *"ValidationException: 1 validation error detected: Value at 'description' failed
  to satisfy constraint: Member must satisfy regular expression pattern: ([0-9a-zA-Z:.][ _-]?)+"* (`SUP-477`).
  The policy, its attachment, the boundary and `person_session`, which follow the profile, did not run.
- **[Claude] The configuration read back** at 12:56:44: `dastwpv6xpqh`, guardrail `l1gy5nt85y9v` version `1`,
  `selectiveContentGuarding` `COMPREHENSIVE` for `system` and `messages`, `owner` `ACCOUNT`, created
  12:53:49.175, no `modelEnforcement`: the every-model shape's first apply (`SUP-466`).
- **[Claude] The correction**, commit `ca069391`: the description without the apostrophe and the parentheses in
  both `studio/` slices, a comment naming the pattern; every hook passed. Re-planned at 12:56:15 and 12:56:37:
  Staging *"Plan: 3 to add, 2 to change, 0 to destroy."*, Production *"6 to add, 2 to change, 0 to destroy."*.
- **[Claude] `staging/studio/`'s second apply**, from `ca069391`, 14:22:07 to 14:22:24: *"Apply complete!
  Resources: 3 added, 1 changed, 0 destroyed."*, the profile `cejulbydm4lk` and `awsds-staging-app-genai`
  attached to the deployment project's role; `person_session`'s document, `(known after apply)` in the plan
  (`SUP-356`), resolved to the one it held. Re-planned `No changes` at 14:22:59. The boundary at `v6`, 19
  statements, 4,764 characters minified; against `v5`, the ceiling's `Action` `*` became `NotAction`
  `bedrock:*`, `bedrock:*` left `DenyServicesNoProjectUsesHere`, and
  `AllowTheApplicationsModelUnderAPublishedGuardrail`, `AllowApplyingTheAccountsGuardrails`,
  `AllowListingAndCreatingAGuardrail`, `AllowKeepingAGuardrailOfTheAccount` and
  `DenyWritingTheAccountsGuardrail` joined; nothing else changed.
- **[Claude] Production's retention**: `inherit` before, `none` after, `updatedAt` 14:23:15.088.
- **[Claude] `production/studio/`**, from `ca069391`, 14:23:24 to 14:23:48: *"Apply complete! Resources: 6
  added, 1 changed, 0 destroyed."*: the profile `33nugu2skjt9`, the guardrail `awsds-prod-account-guardrail`
  (`aml52z7rpznt`) and its version, the enforced configuration `ah6oaw4xn6k6` (created 14:23:40.829, the fields
  of Staging's), the policy `awsds-prod-app-genai` and its attachment. Re-planned `No changes` at 14:24:20. The
  boundary at `v6`, 20 statements, 5,091 characters, Staging's diff.
- **[Claude] The `chains/` and `foundation/` applies**, from the saved plans of 12:51, the four slices' code
  `main`'s: `staging/chains/` 14:24:47 to 14:25:22, *"12 added, 1 changed, 0 destroyed"*; `production/chains/`
  14:25:23 to 14:25:37, *"6 added, 1 changed, 0 destroyed"*; `staging/foundation/` 14:25:48 to 14:25:59 and
  `production/foundation/` 14:25:59 to 14:26:11, *"0 added, 1 changed, 0 destroyed"* each. Re-planned `No
  changes` from 14:26:27 to 14:27:30, the foundations with the var-file. The schedules
  `awsds-staging-chain-app-genai-probe`, `awsds-staging-chain-app-genai-triage` and
  `awsds-prod-chain-app-genai-triage` read `DISABLED`.
- **[Claude] 10.1's simulation on the applied boundaries**, 14:29:37 to 14:32:34: `simulate-principal-policy`
  as each target's deployment project role, the Region and the project tag in the context (`SUP-008`), 31
  cases a target, 0 unexpected, `AllowedByOrganizations` `true` throughout. `allowed` by
  `awsds-<env>-app-genai`: the invoke on the profile and on the model naming a numbered version of the
  project's guardrail or of the account's; `ApplyGuardrail`; `ListGuardrails`; `CreateGuardrail` with the
  project's tag; `GetGuardrail`, `UpdateGuardrail`, `CreateGuardrailVersion` and the `awsds:` `TagResource` on
  the project's guardrail. `implicitDeny`: the invoke with the `DRAFT`, with no guardrail and on another
  profile, the boundary refusing; `CreateGuardrail` with another project's tag or none and `UpdateGuardrail`
  on an untagged guardrail, the role's policy refusing; `InvokeModelWithResponseStream`, `DeleteGuardrail`,
  `PutEnforcedGuardrailConfiguration`, `InvokeAgent` and `Retrieve`, outside the ceiling. `explicitDeny`, the
  boundary's: `UpdateGuardrail`, `CreateGuardrailVersion` and `TagResource` on the account's guardrail, and
  `TM-30`'s `bedrock-agentcore:StartCodeInterpreterSession`, `bedrock-agentcore:StartBrowserSession`,
  `q:SendMessage` and `codewhisperer:GenerateRecommendations`.
- **[Claude] The instruments**: `./aws/deploytargets.py` on every profile at 14:32:51, *"0 check(s) FAILED"*
  and exit 1 from section 14 alone, the `sts` calls of the five SSO sessions with no token (`awsds-ctadmin`,
  `awsds-deploy`, `awsds-devenv`, `awsds-governance`, `awsds-scientist`); on the five infrastructure profiles,
  14:35:28 to 14:37:42, exit 0 and 45 checks `pass`, `DT-14`'s fenced services
  `agent-registry, bedrock-agentcore, codewhisperer, q, redshift-data, sqlworkbench` in Production and the same
  with `redshift` and `redshift-serverless` in Staging. `./aws/bedrock.py` on the five at 14:39:20, exit 0,
  `BR-2` *"retention mode is none"* in Staging and Production, `BR-7`'s note as on 2026-10-20.
  `./aws/bedrock-scope.py` on each target at 14:45:56 and 14:46:55, exit 2: `BS-6` reads `us-west-2` `none` and
  the other sixteen Regions unreadable, the Region ceiling refusing the read there, and `BS-5` the three scoped
  Anthropic models with no agreement, both a target's expected readings.
- **[Claude] Lesson 79**: both `studio/` slices hold `ca069391`'s description until its pull request merges; a
  plan of either from `main` before then proposes replacing the profile with the description
  `CreateInferenceProfile` refuses.
- **[Claude] Records**: this stage's `Status` row, step 10.5, the table of what a target lacked and verification
  xlix; `SUP-466`'s later reading and `SUP-477`; `AWS_STATE.md` `INV-18`; `threat-model.md`'s `TM-30` and
  `TM-36`; `promotion.md` §N.6 item 8, §N.11.2, §N.12.1 and §N.12.4; `sagemaker-ai-ml.md`'s target list;
  `claude-code-sagemaker.md`'s state line; the waiting list; `CLAUDE.md`'s Stage 17 row and Bedrock bullet.

## 2026-11-23 — `check-bedrock-descriptions.py`, the commit gate for `SUP-477`'s refusal, nothing up

*Claude's hand, in the session "Applies e infraestrutura SSO", on the branch `claude/applies-infra-sso-dccfb0`.
No AWS call: the reads are local files.*

- **[The user] The request**, in this session's chat: *"Sim, adicione."*, answering the offer of a commit gate for
  the profile's description.
- **[Claude] The rule**, read from AWS CLI 2.37.12's model of `bedrock` 2023-04-20: `CreateInferenceProfile`'s
  `InferenceProfileDescription` takes 1 to 200 characters matching `([0-9a-zA-Z:.][ _-]?)+`;
  `CreateGuardrail`, `CreateGuardrailVersion` and `UpdateGuardrail` take `GuardrailDescription`, 1 to 200
  characters and no pattern. All three shapes are `sensitive`.
- **[Claude] The check**: `scripts/check-bedrock-descriptions.py`, one rule per resource type, in the commit gate
  and `make check`, and so in the offline gates. `literal_text` moved from `check-sg-descriptions.py` into
  `scripts/tfhygiene/hcl.py`; the EC2 check's output over the tree is byte-identical before and after.
- **[Claude] The tree**: 494 `.tf` files, 8 descriptions, 8 `ok`, exit 0: each target's profile, guardrail and
  guardrail version, and Sandbox's guardrail and guardrail version.
- **[Claude] The fixtures**, in the session's scratchpad: the description `staging/studio/` planned before
  `ca069391` reads *"FAIL ... outside the set: ' ( )"*; on a profile, a double separator, a separator first, an
  en dash, a comma, an empty string, 201 characters and a template's apostrophe fail too; on a guardrail or a
  version, 201 characters, a template whose literal text alone is 202 characters and an empty string fail. 11
  `FAIL`, exit 1. The corrected description, a trailing separator, a guardrail's apostrophe and a heredoc read
  `ok`, a template `partial`, a reference and a directive `unchecked`, a missing description `absent`, exit 0.
  An unclosed string exits 2, and a tree with no Bedrock resource reads *"OK (vacuous)"*.
- **[Claude] Records**: `SUP-477`'s last sentence; `.pre-commit-config.yaml`, the Makefile's `check` list and
  header; `README.md`, `terraform-live/README.md` and `scripts/tfhygiene/__init__.py`.

## 2026-11-23 — R2's pre-flight for 9.7, 10.6 and 9.11, nothing up

*Claude's hand, R2's session (`promotion.md` §N.11.2); reads only. The shared readings, `make status`, the
deploy script's checks, the mirror and both raises' plans, are in Stage 8's log of the same day. Times UTC.*

- **[Claude] 9.7's gate**: the gates' `pip-audit` step verbatim on `app-ml`'s `code` at 16:01, *"48 of 48
  pinned package(s) audited, 0 blocking vulnerability(ies)"*, exit 0; run again before the tag.
- **[Claude] 10.6's empty case**: the same step on `app-genai` with `GATES_UV_PROJECTS=.` exits 1 at
  `grep -c` on an export that holds no pin; its pipeline sets no `GATES_UV_PROJECTS`, so no `pip-audit` job
  runs and no gates tag comes first.
- **[Claude] `bedrock-base` in both targets**: `staging/egress/` and `production/workloads-egress/` planned
  with the group, *"Plan: 20 to add, 0 to change, 0 to destroy."* each, `bedrock` and `bedrock-runtime` the
  two the group adds.
- **[Claude] 9.11's tree** at `684ec8b1`: `examples/app-etl/` with no `app-etl-train` and no model job, its
  lint pin `4401f91`, `--self-check` reading 8 variables a stage.

## 2026-11-23 — R2: the `test` jobs of `app-ml`, `app-genai` and `app-etl`, offline before the raise

*Claude's hand, R2's session (`promotion.md` §N.11.2), while the user's raise waited for 17:00 UTC. No AWS
call and no Terraform: each `test` job's script items read from its `.gitlab-ci.yml` with the file's
variables and run by `bash -c` on the laptop, on CPython 3.12.13, in a git copy of `examples/<app>/` at
`origin/main` `495ebb1a`. Times UTC.*

- **[Claude] `app-ml`** (9.7), 16:22: `uv sync --locked`, `uv lock --check --project code`, `ruff check`
  and `ruff format --check` clean, `pytest` *"100 passed"*, the lint at `4401f91` with
  `--image-repository`, `--model-item model`, the algorithm repository and the seven instance types *"ok:
  6 arquivo(s)"*.
- **[Claude] `app-genai`** (10.6): clean, *"95 passed"*, the lint *"ok: 3 arquivo(s)"*.
- **[Claude] `app-etl`** (9.11's tree): clean, *"93 passed, 1 skipped"*, as on #390, the lint *"ok: 8
  arquivo(s)"*.

## 2026-11-23 — R2: 9.7, `app-ml`'s first release `v0.1.0`

*Claude's hand, R2's session (`promotion.md` §N.11.2), on the user's words in this session's chat, which name
each act of the list `r2-acts-for-15h.md` in order, among them *"primeiro push do app-ml; tag v0.1.0 do
app-ml; gates do app-ml; chain de score do app-ml; production-approve do app-ml; chain de score de novo"*.
GitLab as its local administrator `felipenoris` in a Chrome tab of Claude's; git through the laptop's
keychain credential; AWS reads as the infrastructure user, `InfrastructureAccess`. Times UTC.*

- **[Claude] Before the push**: `staging/egress` and `production/workloads-egress` up with `bedrock` and
  `bedrock-runtime` and no `sagemaker.mlflow` endpoint in either account (17:06:17).
- **[Claude] The first push** (`sagemaker-application.md` §L step 1): `awsds/app-ml` cloned empty into
  `$HOME/tmp/app-ml`, `examples/app-ml/` at `495ebb1a` extracted, the tree `8b7c14dc` on both sides (Lesson
  86); the message naming `model.json`'s training job `app-ml-train-20261122T193009`, SHA-256
  `852032c55a3047b66de1a2fa6c29e148e10b145cb30fab41d26c83214282d7ab` and AUC 0.8289 against `MIN_AUC` 0.70.
  Pushed onto `main` at 16:59:47 as `a463dd54`. The `main` pipeline #145: `secret_detection` and its gate,
  `pip-audit`, `test` and `pages` green.
- **[Claude] The tag `v0.1.0`** on `a463dd54`, pushed at 17:03:46, after GitLab's three runners read online.
  Pipeline #147: `pip-audit` and `test` green; `build-image` (job 941, on `awsds-prod-runner`, 17:04:15 to
  17:07:47) pushed `awsds-prod-ecr-app-ml:v0.1.0-a463dd54`, digest `sha256:650ad15b…18da`; `scan-gate`
  (job 943, `allow_failure`) *"FAIL: the scan ended FAILED: Number of vulnerabilities for this image exceeds
  the maximum supported with Basic Scanning"*, as `SUP-437` reads every push of a SageMaker Distribution
  image; `build-task-code`, `bundle`, `store-bundle` and `release` green.
- **[Claude] Staging**: `staging-gate` played at 17:09:57, independent of `scan-gate`. `staging-deploy` (job
  949, 17:21:32 to 17:23:30, queued behind `app-dbt`'s `staging-test` on the deploy runner) created
  `app_ml_deploy_staging_app_ml_register` and `app_ml_deploy_staging_app_ml_score` in `deploy-staging`, the
  stage's variables in `/datascience/staging/applications/app-ml/stage-variables`. `staging-test` (job 950)
  started `awsds-staging-chain-app-ml-register`, execution `v0-1-0-950-app-ml-register`, at 17:26:15.
- **[Claude] `staging-test`**: the register chain proposed `awsds-staging-model-app-ml/1`
  `PendingManualApproval`, trained by `app-ml-train-20261122T193009`, validation AUC 0.8289, and the deploy
  role approved it (17:29:30); `awsds-staging-chain-app-ml-score`, execution `v0-1-0-950-app-ml-score`,
  started at 17:29:32 and `SUCCEEDED` at 17:47:56: the processing job `app-ml-prepare-score-20261123T173028`
  (17:30:30 to 17:35:54), the model `app-ml-score-5ido8bej1zoeq8`, the transform job
  `app-ml-score-20261123T173956` (17:39:58 to 17:45:15). The report: `"source": "registry"`, the release's
  SHA-256, `"predictions": 200` over 200 rows, `"auc": 0.847556` against `"min_auc": 0.7`, the version
  `awsds-staging-model-app-ml/1`. The Staging leg reads yes.
- **[Claude] Staging's readings**, as `awsds-infra-staging`, read at about 17:50. Verification lviii: one
  `CreateModelPackage` at 17:27:09 on `awsds-staging-model-app-ml`, `PendingManualApproval`, by the project
  role's `AmazonMWAAServerless` session through `vpce-0c30e0a61f9cb5f09`; one `UpdateModelPackage` at 17:29:29
  on version 1, `Approved`, by `awsds-deploy-staging`; no error. Verification lxii, the target half: the deploy
  wrote `model.tar.gz`, `model.json` and `evaluation.json` under `shared/app-ml/bundle/model/` at 17:22:56,
  and `register` copied the archive and its evaluation under `shared/app-ml/models/sha256/852032c5…d7ab/` at
  17:27:09, each `aws:kms` under `alias/awsds-staging-project` with the bucket key; CloudTrail holds no S3
  data event (`log-debugging.md`), so the principals are read from KMS's `GenerateDataKey` through S3 on
  `awsds-staging-smus-projects` under that key: `awsds-deploy-staging` at 17:22:46, the project role's
  `AmazonMWAAServerless` session at 17:27:08.
- **[Claude] Production**: the orchestrating session verified the leg (the bundle, both Staging executions,
  the approved version, the image) and sent its «verificado»; `production-check` (job 951) green at
  17:48:40, `production-gate` (job 952) played at 18:02:10.

## 2026-11-23 — R2: 10.6, `app-genai`'s first release `v0.1.0`

*Claude's hand, R2's session (`promotion.md` §N.11.2), on the user's words in this session's chat, among them
*"primeiro push do app-genai; tag v0.1.0 do app-genai; gates do app-genai; chain de triage do app-genai"*,
and *"Um ato bloqueado não segura as outras aplicações"*, which moved these acts ahead while `app-dbt`'s and
`app-ml`'s `production-gate` waited on the orchestrating session's «verificado». GitLab as `felipenoris` in
Claude's Chrome tab; git through the keychain credential. Times UTC.*

- **[Claude] The first push** (§L step 1): `awsds/app-genai` cloned empty into `$HOME/tmp/app-genai`,
  `examples/app-genai/` at `495ebb1a` extracted, the tree `1dea9f49` on both sides, `scripts/dev-cli.sh` at
  `100755`; pushed onto `main` at 17:51:38 as `9c9692dc`. The `main` pipeline #149: `secret_detection` and its
  gate, `test` and `pages` green, no `pip-audit` (10.6).
- **[Claude] The tag `v0.1.0`** on `9c9692dc`, pushed at 17:53:07, GitLab's three runners online. Pipeline
  #150: `test`; `build-task-code` (job 977) *"code/app-genai.zip: 8 file(s), 15715 bytes"*; `bundle` (job 978);
  `store-bundle` writing `app-genai/v0.1.0/app-genai.zip`, 18354 bytes, at 17:54:04; `release`.
- **[Claude] Staging**: `staging-gate` played at 17:54:52. `staging-deploy` (job 983, 17:55:27 to 17:57:05):
  *"the bundle of v0.1.0: 4 file(s), no catalog export"*, the workflows `app_genai_deploy_staging_app_genai_triage`
  and `app_genai_deploy_staging_app_genai_probe`, the stage's variables `EXPECT_UNGUARDED`, `MIN_ACCURACY` and
  `MODEL_ID`. `staging-test` (job 984): `awsds-staging-chain-app-genai-probe`, execution
  `v0-1-0-984-app-genai-probe`, 17:57:18 to 18:00:22 `SUCCEEDED`, its report `"outcome": "refused"`,
  `"expected": "refused"`, `"passed": true` on *"… assumed-role/datazone_usr_role_5ido8bej1zoeq8_…/AmazonMWAAServerless
  is not authorized to perform: bedrock:InvokeModel on resource: …"* against the application inference profile
  `cejulbydm4lk`; `awsds-staging-chain-app-genai-triage`, execution `v0-1-0-984-app-genai-triage`, 18:00:25 to
  18:05:32 `SUCCEEDED`, its report `"accuracy": 0.9737` against `"min_accuracy": 0.8`, 37 of 38 let through
  agreeing (`m34` answered `account`, expected `feedback`), 2 of 40 blocked, 12001 input and 948 output tokens,
  the guardrail `app-genai-5ido8bej1zoeq8` (`ryvkg8t7mwb5`) version 1 created by the run, the planted `m25`
  anonymized (`EMAIL`, `PHONE`) and `m31` blocked (`PROMPT_ATTACK`), `"passed": true`. The Staging leg reads yes.
- **[Claude] Production, `app-genai`**: `production-check` (job 985) green; `production-gate` (job 986) waits on
  the orchestrating session's «verificado».

## 2026-11-23 — R2: 9.7's Production leg, the scoring chain held at `resolve`

*Claude's hand, R2's session, continuing the entry above; the chain started on the user's words *"chain de
score do app-ml"*, as `awsds-infra-prod`, `InfrastructureAccess`. Times UTC.*

- **[Claude] `production-deploy`** (job 953, 18:05:39 to 18:09:54): the workflows
  `app_ml_deploy_production_app_ml_register` and `app_ml_deploy_production_app_ml_score` in `deploy-production`;
  the bootstrap ran the register workflow (run `0v1HPNMMpPgSTOG`), whose `register` proposed
  `awsds-prod-model-app-ml/1` `PendingManualApproval` at 18:08:36. The trail: `CreateModelPackage` at 18:08:36
  by the project role's `AmazonMWAAServerless` session through `vpce-02a92c8655cca030c`, no error. The version's
  metadata: the release's SHA-256, `training_job` `app-ml-train-20261122T193009`, `validation_auc` 0.82895,
  `source_prefix` under `shared/app-ml/bundle/model/`. Both schedules `DISABLED`.
- **[Claude] The scoring chain, held** (verification xxxi's first half): `awsds-prod-chain-app-ml-score`,
  execution `r2-v0-1-0-app-ml-score-pending`, started at 18:11:28, `FAILED` at 18:22:32 on
  `WorkflowRunNotSucceeded`. The workflow run `DHnOzz9wEUElZH9`: `prepare` `SUCCESS` (the processing job
  `app-ml-prepare-score-20261123T181218` `Completed`); `resolve` `FAILED` 18:20:25 to 18:20:32 on
  *"RuntimeError: …model-package/awsds-prod-model-app-ml/1 is PendingManualApproval: a target serves an Approved
  version alone"*; `score`, `check` and `cleanup` `UPSTREAM_FAILED`, no transform job. xxxi's first half reads yes.

## 2026-11-23 — R2: 9.11, `app-etl`'s release retiring its model half

*Claude's hand, R2's session, on the user's words in this session's chat *"MR e merge do 9.11 no app-etl; tag
do app-etl; gates do app-etl"*, moved ahead while `app-ml`'s `production-approve` and `app-genai`'s
`production-gate` waited on the orchestrating session's «verificado» (the user's *"Um ato bloqueado não
segura as outras aplicações"*). Times UTC.*

- **[Claude] The merge request** `!18` in `awsds/app-etl`: the branch `retire-model-half` at `c0967c90`, cut from
  `main` `57f2fac0` (release G's), `examples/app-etl/` at `495ebb1a`, the tree `7951fc83` on both sides; six files,
  53 insertions and 388 deletions (`workflows/app-etl-train.yaml` deleted). Pushed at 18:28:28. Its pipeline #151:
  `secret_detection` and its gate, `pip-audit` *"1 of 1 pinned package(s) audited, 0 blocking"*, `test` *"93
  passed, 1 skipped"* and the lint *"ok: 8 arquivo(s)"*. Merged at 18:29:32 by `felipenoris`, the merge commit
  `3d3146bb`, the tree `7951fc83` (Lesson 86).
- **[Claude] The tag `v0.7.0`**, the next after `v0.6.0` read from GitLab's tags at 18:30:17, on `3d3146bb`,
  pushed at 18:30:42, the runners online and the build runner `i-015f85e903a4bfe45` running, `app-ml`'s model
  held in both targets (`promotion.md` §N.11.2 step 3's condition). Pipeline #153.

## 2026-11-23 — R2: 10.6's Production leg, the triage chain failed at `check`

*Claude's hand, R2's session; `production-gate` played on the user's words *"gates do app-genai"* after the
orchestrating session's «verificado», the chain started on *"chain de triage do app-genai"*, as
`awsds-infra-prod`, `InfrastructureAccess`. Times UTC.*

- **[Claude] `production-gate`** (job 986) played at 18:32:51; **`production-deploy`** (job 987, 18:33:39 to
  18:35:11) created the workflow `app_genai_deploy_production_app_genai_triage` in `deploy-production`, `READY`,
  and recorded the stage's variables in `/datascience/prod/applications/app-genai/stage-variables` (version 1,
  18:35:06): `EXPECT_UNGUARDED` `refused`, `MIN_ACCURACY` `0.80`, `MODEL_ID` the application inference profile
  `33nugu2skjt9`. Pipeline #150 green.
- **[Claude] The triage chain**: `awsds-prod-chain-app-genai-triage`, execution `r2-v0-1-0-app-genai-triage`,
  started at 18:37:38, `FAILED` at 18:42:40 on *"app-genai-triage did not succeed"*. The workflow run
  `wk88Ec50c1IWHet` (18:37:41 to 18:41:06): `guardrail` `SUCCESS` (18:38:23 to 18:38:34), `triage` `SUCCESS`
  (18:39:14 to 18:40:14), `check` `FAILED` (18:40:53 to 18:41:05) on *"RuntimeError: 1 failure(s): m19: the
  answer is no JSON object with a label of the list"*. The task's line: *"40 answer(s), 38 let through, 2
  blocked; accuracy 0.9474 against 0.8; 1 failure(s)"*. The report `shared/app-genai/outbox/triage-report.json`:
  36 of 38 agreed, `m34` answered `account` (expected `feedback`), 12001 input and 951 output tokens, the
  planted `m25` anonymized (`EMAIL`, `PHONE`), `m31` blocked (`PROMPT_ATTACK`) and `m36` blocked (the denied
  topic *Investment advice*), no unexpected block, `"passed": false`. `m19`'s answer in
  `work/20261123T184013Z/answers.jsonl` is `{"label": "billing", "summary": "Discount code not applied to order,
  resulting in unexpected extra charge."}]`, a trailing `]` after the object, `stop_reason` `end_turn`, 25
  output tokens. The line of `app-genai` stops here (the user's *"Um job que falhar para a sessão no log
  dele"*); nothing else of it ran.
- **[Claude] Verification xlii, Production** (CloudTrail, 18:37 to 18:42): 40 `Converse`, no error, by
  `datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow` with the session `AmazonMWAAServerless`, through
  `vpce-0cc38cf401b7c102f` (`awsds-prod-workloads-bedrock-runtime`), the model the profile `33nugu2skjt9`, the
  guardrail `8fwsdhtioqe8`. `CreateGuardrail` at 18:38:32 by the same role and session through
  `vpce-07a18f03e17e5c132` (`awsds-prod-workloads-bedrock`), then `GetGuardrail` and `CreateGuardrailVersion`;
  the guardrail `app-genai-d7qcazihvr3s7k`, no customer key, version 1, hash `6b4f6876…cf78`. Each answer names
  the account-enforced guardrail `aml52z7rpznt` version 1 beside the request's. xlii reads yes for Production.

## 2026-11-23 — R2: 9.7's approval and the scoring chain from the registry

*Claude's hand, R2's session; `production-approve` played on the user's words *"production-approve do
app-ml"* after the orchestrating session's «verificado», the chain started on *"chain de score de novo"*, as
`awsds-infra-prod`, `InfrastructureAccess`. Times UTC.*

- **[Claude] `production-approve`** (job 954, 18:32:49 to 18:33:09): *"…model-package/awsds-prod-model-app-ml/1:
  PendingManualApproval, trained by app-ml-train-20261122T193009"*, then *"…/awsds-prod-model-app-ml/1:
  Approved"*. The trail: `UpdateModelPackage` at 18:33:05 by `awsds-deploy-prod`, no `vpcEndpointId`,
  `modelApprovalStatus` `Approved`, *"approved by felipenoris at the promotion pipeline's production leg"*, no
  error. Version 1 alone was approved. lviii's Production half reads: the version proposed by the project
  role's workflow (18:08:36) and approved by the deploy role.
- **[Claude] The scoring chain again**: execution `r2-v0-1-0-app-ml-score-approved`, started at 18:34:22,
  `SUCCEEDED` at 18:53:27. The workflow run `O7sOLeTvjRC2Lgl` (18:34:32 to 18:52:01): `prepare` 18:35:22 to
  18:43:03, `resolve` 18:43:38 to 18:43:47 *"created app-ml-score-d7qcazihvr3s7k from
  …model-package/awsds-prod-model-app-ml/1: sha256 852032c55a3047b66de1a2fa6c29e148e10b145cb30fab41d26c83214282d7ab"*,
  `score` 18:44:29 to 18:50:13, `check` *"app-ml-score-20261123T184437: 200 prediction(s) for 200 line(s), AUC
  0.847556, MIN_AUC 0.7"*, `cleanup` 18:51:51 to 18:52:00, each `SUCCESS`. `shared/app-ml/outbox/score-report.json`:
  `"source": "registry"`, the version `…/awsds-prod-model-app-ml/1`, the SHA-256 Staging named,
  `training_job` `app-ml-train-20261122T193009`, `transform_job` `app-ml-score-20261123T184437`. xxxi's second
  half reads yes, and `app-ml`'s Production leg reads yes.

## 2026-11-23 — R2: 9.11's release `v0.7.0`, the Staging leg

*Claude's hand, R2's session, continuing 9.11's entry; `staging-gate` played on the user's words *"gates do
app-etl"*; reads as `awsds-infra-staging`, `InfrastructureAccess`. Times UTC.*

- **[Claude] Pipeline #153 before the legs**: `pip-audit`, `test`, `build-image`, `build-task-code`, `bundle`,
  `store-bundle` and `release` green from 18:30:45 to 18:35:51, the image `awsds-prod-ecr-app-etl`
  `v0.7.0-3d3146bb` (`sha256:7b12c0fb…e003b`, 3,796,514,985 bytes) pushed at 18:33:42. `scan-gate` (job 1004,
  `allow_failure`) read *"FAIL: the scan ended FAILED: Number of vulnerabilities for this image exceeds the
  maximum supported with Basic Scanning. Please upgrade to Enhanced Scanning to cover all vulnerabilities in
  the image."* at 18:40:09, as `app-ml`'s `scan-gate` (job 943) did at 17:09:59 on its 3,745,677,773-byte
  image (`SUP-437`).
- **[Claude] Staging**: `staging-gate` (job 1008) played at 18:37:30; `staging-check` green at 18:37:57;
  `staging-deploy` (job 1010, 18:38:00 to 18:39:50) *"Successfully created 1 workflow(s)"*,
  `app_etl_deploy_staging_app_etl`, `READY` at 18:39:42, and the stage's variables recorded; `staging-test`
  (job 1011, 18:39:53 to 18:55:31) started `awsds-staging-chain-app-etl`, execution `v0-7-0-1011-app-etl`,
  `SUCCEEDED` at 18:55:24, the run's report 10 rows from `trades.csv` (SHA-256 `a84e2ff3…2dac`) and
  `trades_notional` `ICEBERG` as the catalog answers the deploy role; `staging-catalog` (job 1012) *"staging-deploy's
  import was whole: no second import"*. The pipeline carries no model job: lxiv's first half reads yes in
  Staging.
- **[Claude] What the release left behind**, read at 18:59: `list-workflows` in Staging still holds
  `app_etl_deploy_staging_app_etl_train`, `READY`, modified 2026-11-22 at 04:12:30 by release G's deploy;
  `v0.7.0`'s deploy, whose manifest no longer names it, neither updated nor deleted it (`SUP-484`). Under
  `shared/app-etl/` the deploy wrote `code/app-etl.zip`, `glue/`, `src/` and `workflows/app-etl.yaml` and
  `app-etl-warehouse.yaml` at 18:38 to 18:39, and left `code/app-etl-train.zip` (2026-11-22 04:11:20) and
  `workflows/app-etl-train.yaml` (04:12:29) (`SUP-348`), with the `models/` prefix of the retired training
  and transform jobs. 9.11's estate pull request owes their deletion, an act the user names.

## 2026-11-23 — R2: the user's answers on 9.11's estate and on `app-genai`'s triage

*Claude's hand, R2's session, recording the user's words relayed by the orchestrating session. Times UTC.*

- **[user] 9.11's estate, option (a)**: *"Aceito as três"*, at 18:52 in the orchestrating session's chat,
  answering *"Aceita as três recomendações do R2?"*. Read at 18:38: `awsds-staging-model-app-etl` holds no
  version and `awsds-prod-model-app-etl` one, version 1, `Approved`, created 2026-10-25 at 01:28. Tomorrow's
  estate pull request deletes that version by hand, then its apply removes both groups; the deletion is an act
  the user names in the session that applies, and this answer does not authorize it.
- **[Claude] The failed triage's report kept**: before any new attempt overwrites it,
  `shared/app-genai/outbox/triage-report.json` read at 19:03 (1,608 bytes, written 18:41:01, S3 version
  `lHOzkVjNTYmI3mbJ78GJoE1RxNGgYGbf`, SHA-256 `2b156aa1…2f9c`) and the run's `answers.jsonl` (SHA-256
  `cfe696d1…447a`) copied to the session's scratchpad; their content is in the entry on 10.6's Production leg.
  The orchestrating session reads the cause as `parse_answer`, which admits a code fence and nothing after the
  object; the fix, a parse that stops at the first object's end or structured output in `Converse`, is
  `app-genai`'s follow-up after today. A new attempt waits on the user's word in R2's chat.

## 2026-11-23 — R2: 10.6's triage chain again, `SUCCEEDED`

*Claude's hand, R2's session, on the user's words in this session's chat, *"Autorizo rodar de novo a chain de
triage do app-genai em Production (awsds-prod-chain-app-genai-triage), uma tentativa."*, as `awsds-infra-prod`,
`InfrastructureAccess`. Times UTC.*

- **[Claude] The one attempt**: `awsds-prod-chain-app-genai-triage`, execution `r2-v0-1-0-app-genai-triage-2`,
  input `{}` as the first's, started at 19:04:11, `SUCCEEDED` at 19:09:13; the workflow run `2opd2tNuMU7558T`,
  19:04:16 to 19:07:39, `SUCCESS`. The report: accuracy 0.9737 against 0.8, 37 of 38 let through agreeing (`m34`
  `account`, expected `feedback`), 2 blocked, no failure, 12001 input and 958 output tokens, the guardrail
  `8fwsdhtioqe8` at version 1, its hash unchanged so no version published, the planted `m25` anonymized, `m31`
  and `m36` blocked, `"passed": true`. `m19`'s answer `{"label": "billing", "summary": "Discount code not applied
  to order, resulting in unexpected extra charge."}`, 25 output tokens, `end_turn`: the same message and
  inference configuration answered once with a trailing `]` and once without. The trail: 40 `Converse` through
  `vpce-0cc38cf401b7c102f`, `GetGuardrail`, `ListGuardrails` and `ListTagsForResource` through
  `vpce-07a18f03e17e5c132`, by the project role's `AmazonMWAAServerless` session, no error. `app-genai`'s
  Production leg reads yes; `parse_answer`'s fix stays its follow-up.

## 2026-11-23 — R2: 9.11's release `v0.7.0`, the Production leg

*Claude's hand, R2's session; `production-gate` played on the user's words *"gates do app-etl"* after the
orchestrating session's «verificado» of the Staging leg; reads as `awsds-infra-prod`, `InfrastructureAccess`.
Times UTC.*

- **[Claude] `production-gate`** (job 1014) played at 19:05:25, green at 19:05:31.
- **[Claude] `production-deploy`** (job 1015, 19:05:33 to 19:24:12): *"the bundle of v0.7.0: 10 file(s), a catalog
  export"*, *"Total files deployed: 9"*; the import *"0 created, 1 updated, 3 skipped (extra in target), 0 failed,
  0 published"*, the extras `app-etl`'s data product `trades-notional` and `app-dbt`'s assets `trades` and
  `notional_by_desk`; the workflows `app_etl_deploy_production_app_etl` and `…_warehouse` updated, `READY`. The
  bootstrap's run `gHhoGi4GC8wHu4J` (19:08:00 to 19:22:42): `transform`, `process`, `summarize`, `write_result` and
  `publish` `SUCCESS`; `publish` *"source run 6d5lycntokbfkg: SUCCESS, {"added": 0, "failed": 0, "unchanged": 0,
  "updated": 1}"*, the listing `5hpftif3nnoj2o` at revision 10 `ACTIVE` over the asset `da1fycta6l71n4` at revision
  8, and the data product `anph2bq7uigqa8` *"revision 1, unchanged"*, its listing `dr8t27tte8ezdc` at revision 2
  `ACTIVE`.
- **[Claude] `production-catalog`** (job 1016, 19:24:15 to 19:24:24) *"production-deploy's import was whole: no
  second import"*. `production-warehouse-ddl` (job 1017) left `manual`, unplayed (Stage 8's log, the user's
  answer). Pipeline #153 ends with no model job in either leg: lxiv's first half reads yes in both targets; its
  second and third halves wait on 9.11's estate pull request. The three `awsds-prod-chain-app-etl*` schedules read
  `DISABLED` at 19:15; `app_etl_deploy_production_app_etl_train` stays `READY` and both training files stay under
  `shared/app-etl/` (`SUP-484`).

## 2026-11-23 — 9.11's estate: the reads, the branch's plans and the instruments

*Claude's hand, 9.11's estate session, with nothing up; reads as `awsds-infra-staging` and `awsds-infra-prod`,
`InfrastructureAccess`, from 21:19. Times UTC.*

- **[Claude] The schedules**: `awsds-staging-chains` holds eight, `awsds-prod-chains` seven, each `DISABLED`,
  `awsds-staging-chain-app-etl-train` and `awsds-prod-chain-app-etl-train` among them.
- **[Claude] The workflows**: `app_etl_deploy_staging_app_etl_train` and `app_etl_deploy_production_app_etl_train`
  still listed beside each target's other workflows (`SUP-484`).
- **[Claude] The registry**: Staging lists `awsds-staging-model-app-ml` alone, and `describe-model-package-group`
  on `awsds-staging-model-app-etl` answers *"does not exist"*. R2's "holds no version" was `ListModelPackages`'
  empty list over a group no slice declared (`SUP-485`), so the apply removes one group, Production's.
  Production lists `awsds-prod-model-app-ml` and `awsds-prod-model-app-etl` (created 2026-10-18 at 19:59:03),
  the latter holding version 1, `Approved`, `Completed`, created 2026-10-25 at 01:28:36. Its policy's
  statements: `RegisterAndApproveAsTheProductionDeployRole`, `ReadTheVersionsAsTheStagingDeployRole`,
  `ReadTheStatusFromSandbox`.
- **[Claude] Whether `DeleteModelPackageGroup` refuses a group holding versions** (lxiv's second half), read in
  the documentation, unmeasured: SageMaker's Studio page says *"You can only delete an empty model group"*, the
  API reference names no error for it, and the AWS provider's delete calls `DeleteModelPackageGroup` alone,
  deleting no version first (`docs/REFERENCES.md`). So version 1 is deleted by hand before the apply, as the
  user's option (a) orders; the refusal's wording stays unread unless the user names a delete of the group
  while it holds the version.
- **[Claude] The registry's CloudTrail records**, the 90-day lookup: Staging's `CreateModelPackage` at 17:27:09
  by `app-ml`'s deployment project role, `PendingManualApproval`, and `UpdateModelPackage` at 17:29:29 by
  `awsds-deploy-staging`, `Approved`; Production's `CreateModelPackage` at 18:08:36 by its project role,
  `PendingManualApproval`, approved at 18:33:05 by `awsds-deploy-prod`; and app-etl's retired pair, registered
  2026-10-25 at 01:28:36 and approved at 01:29:10, both by `awsds-deploy-prod`. `requestParameters` carries
  `modelPackageGroupName` and `modelApprovalStatus` on the create, the keys `OR-8` reads.
- **[Claude] The files under `shared/app-etl/`** in each deployment project: Staging holds `code/app-etl-train.zip`
  (7,043 bytes, 2026-11-22 04:11:20), `workflows/app-etl-train.yaml` (2,717 bytes, 04:12:29), `models/` with two
  training outputs (`app-etl-train-20261116T020100`, `-20261122T043108`, each a `model.tar.gz` and an
  `evaluation.json`) and two transform outputs (`batch.csv.out`), and `work/train/` (`batch.csv`, `train.csv`,
  `validation.csv`, written 2026-11-23 18:42:28 by `v0.7.0`'s `transform`, whose Glue script still carries
  `--TRAIN_PATH`). Production holds the same two retired files (7,043 bytes at 04:46:32; 2,702 bytes at
  04:47:40) and `work/train/`'s three files (19:11:10), with no `models/`. The branch removes `--TRAIN_PATH`
  from the application's source; `work/train/` stops growing at `app-etl`'s next release.
- **[Claude] The branch's plans**, each from `claude/stage17-911-estate-04172a` after the merge of `main` at
  `b0d5adfd`, `-input=false`, saved nowhere, `foundation/` with the project folder's `alerts.auto.tfvars`:

  | Slice | Plan | What |
  |---|---|---|
  | `staging/chains` | 0 to add, 1 to change, 6 to destroy | `app-etl-train`'s state machine, schedule, two failure rules and their targets; the chain-exec role's inline policy |
  | `production/chains` | 0 to add, 1 to change, 6 to destroy | the same in Production |
  | `staging/sagemaker` | No changes | a comment |
  | `production/sagemaker` | 0 to add, 0 to change, 2 to destroy | `awsds-prod-model-app-etl` and its policy |
  | `staging/foundation` | 0 to add, 2 to change, 0 to destroy | `PassTheProjectRoleToSageMaker`; `ReadTheApprovedModelVersions`, `ListTheModelVersions`, `FindTheTrainingJobs`, `ReadTheTrainingJobs`, `ServeTheModels`; the output `registry_model_package_group_arn_prefix` |
  | `production/foundation` | 0 to add, 2 to change, 0 to destroy | `PassTheProjectRoleToSageMaker`; `RegisterAndApproveTheModel`, `FindTheTrainingJobs`, `ReadTheTrainingJobs`, `ServeTheModels` |
  | `staging/studio` | 2 to add, 0 to change, 2 to destroy | `awsds-staging-workflows` replaced, its description being ForceNew, and its attachment to the deployment project's role: `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject` leave |
  | `production/studio` | 2 to add, 0 to change, 2 to destroy | the same in Production |

  Between the replaced policy's destroy and its create, the deployment project's role lacks the grant; every
  schedule is `DISABLED` and no workflow runs at an apply with nothing up.

## 2026-11-23 — 9.11's estate: the hand acts

*Claude's hand, 9.11's estate session, on the user's words in its chat, *"Autorizo os três atos"*, answering a
question that listed the three deletions; as `awsds-infra-staging` and `awsds-infra-prod`, `InfrastructureAccess`.
The orchestrating session, `r2-releases` and `n10-stage21-pass5`, running at 21:41, were told first. Times UTC.*

- **[Claude] `awsds-prod-model-app-etl/1` deleted** at 21:41:47 (`delete-model-package`, exit 0). Afterwards
  `list-model-packages` on the group reads `[]` and `describe-model-package` on the version answers *"does not
  exist"*; `describe-model-package-group` reads the group `Completed`, which `production/sagemaker/`'s apply
  removes.
- **[Claude] The retired workflows deleted**: `app_etl_deploy_staging_app_etl_train` (`…-c5HHr2Hhpi`) at
  21:42:08 and `app_etl_deploy_production_app_etl_train` (`…-Diktm0kSnx`) at 21:42:10, `delete-workflow` answering
  each ARN. `list-workflows` then reads seven workflows in Staging and six in Production, none named `*_train`.
- **[Claude] Their files deleted** under each deployment project's `shared/app-etl/`, the bucket versioned, so each
  delete wrote a delete marker over the version read before it: Staging's `code/app-etl-train.zip` (7,043 bytes,
  version `8L8Ve5Hs…`) at 21:42:24 and `workflows/app-etl-train.yaml` (2,717 bytes, `4XVn0vHG…`) at 21:42:28;
  Production's `code/app-etl-train.zip` (7,043 bytes, `o5fyVWsO…`) at 21:42:31 and `workflows/app-etl-train.yaml`
  (2,702 bytes, `lQ5IChPR…`) at 21:42:33.
- **[Claude] Staging's `shared/app-etl/models/` deleted** at 21:42:47 to 21:42:49 (`s3 rm --recursive`, exit 0):
  the six objects read before, two training outputs (`app-etl-train-20261116T020100`, `-20261122T043108`, each
  `evaluation.json` and `output/model.tar.gz`) and two transform outputs (`transform/app-etl-v0-5-2-…`,
  `-v0-6-0-…`, each `batch.csv.out`). The prefix then lists nothing; `shared/app-etl/` holds `code`, `glue`,
  `inbox`, `outbox`, `src`, `tables`, `work` and `workflows`.
- **[Claude] What `DeleteWorkflow` leaves**: each workflow's log group stays,
  `/aws/mwaa-serverless/<domain>-<project>/app_etl_deploy_staging_app_etl_train` with 34,965 bytes and Production's
  with 0, neither with a retention (`EXC-25`). Their deletion is the user's to decide. `work/train/` stays in
  both targets until `app-etl`'s next release, as recommended: each `v0.7.0` run writes it again.

## 2026-11-23 — R2: 9.11's Production leg, the workflows read at 19:14, recorded from R2's transcript

*Claude's hand, the session orchestrating 2026-11-23, at the user's request in its chat to review the day's
logs. No AWS call: the readings are R2's, relayed from its transcript on 2026-11-23. They time the entry *R2:
9.11's release `v0.7.0`, the Production leg* and `SUP-484`. Times UTC.*

- **[Claude] The job**: GitLab's `/pipelines/153/jobs`, read at 19:06:16, *"1015 production-deploy running
  19:05:33"*. Its trace, read at 19:14:39, after the last workflow write:

  ```text
  2026-11-23 19:07:40,920 - smus_cicd.airflow_serverless - INFO - Successfully started workflow run: gHhoGi4GC8wHu4J
  ```

- **[Claude] The workflows**, `aws mwaa-serverless list-workflows` as `awsds-infra-prod`, `InfrastructureAccess`,
  called at 19:14:46 and answered at 19:14:51 while the bootstrap run went on; the second column is `ModifiedAt`:

  ```text
  app_etl_deploy_production_app_etl_train  2026-11-22T04:47:39.836000+00:00  READY  manual_only
  app_etl_deploy_production_app_etl  2026-11-23T19:07:24.926000+00:00  READY  manual_only
  app_etl_deploy_production_app_etl_warehouse  2026-11-23T19:07:39.727000+00:00  READY  manual_only
  ```

- **[Claude] The files**, `aws s3 ls` of `shared/app-etl/` in `awsds-prod-smus-projects` in the same command, its
  local times converted to UTC: `app-etl.zip`, `app-etl.yaml` and `app-etl-warehouse.yaml` at 19:06:24, 19:07:23
  and 19:07:38; `code/app-etl-train.zip` (2026-11-22 04:46:32) and `workflows/app-etl-train.yaml` (04:47:40)
  kept.

## 2026-11-23 — 9.11's estate: the applies from `main`, the re-plans and the instruments

*Claude's hand, the session of 9.11's estate applies, on the branch `claude/nervous-roentgen-9d111c`, as the
infrastructure user with `InfrastructureAccess` in `Staging Account` (`awsds-infra-staging`) and `Production
Account` (`awsds-infra-prod`). The writes are the seven applies, each on the user's words in the session's
chat; the running sessions were told before each. The account id in an error is written `<Production
Account>`. Terraform 1.17.2. Times UTC.*

- **[The user] The authorizations**, in this session's chat: *"Autorizo os três"*, answering a question that
  named `staging/chains`, `staging/studio` and `staging/foundation`; then, one at a time, *"Autorizo
  production/chains"*, *"Autorizo o studio"*, *"Autorizo o foundation"* and *"Autorizo o sagemaker"*, each
  answering a question that named its Production slice. The user signed in again at 22:19 and 22:48 (the
  token's cache written 22:48:22); the cache was written once more at 23:36:36, `expiresAt` 00:36:36 the next
  day, before the authorization of `production/foundation`.
- **[Claude] The plans**, from `main` at `7a3f4e37`, `-input=false`, each saved to
  `~/tmp/s17-911-<account>-<slice>.tfplan`, both `foundation/` with the project folder's `alerts.auto.tfvars`:
  Staging 22:20:48 to 22:22:08, Production 22:22:57 to 22:24:21. Each read as #397's table: both `chains/`
  *"Plan: 0 to add, 1 to change, 6 to destroy."*, `app-etl-train`'s state machine, schedule, `chain_failed`
  and `workflow_failed` rules and their targets, and `app_etl_deploy_<target>_app_etl_train-??????????` out of
  two statements of the chain-exec role's inline policy; both `studio/` *"2 to add, 0 to change, 2 to
  destroy"*, `awsds-<env>-workflows` replaced on its description with its attachment,
  `DescribeATrainingJobNoProjectHolds` and `TagATrainingJobWithTheCallersProject` out; both `foundation/` *"0
  to add, 2 to change, 0 to destroy"*, the statements #397 lists and Staging's output
  `registry_model_package_group_arn_prefix`; `production/sagemaker/` *"0 to add, 0 to change, 2 to destroy"*,
  the group and its policy. #398 merged at 22:21:57 as `99a47744` and #399 at 22:51:04 as `6d297252`; neither
  touched `terraform-live/`, `terraform-modules/`, `scripts/`, `aws/` or `examples/`, so the branch was
  fast-forwarded to each and the saved plans applied as read.
- **[Claude] Before**, 22:24:58: the eight schedules of `awsds-staging-chains` and the seven of
  `awsds-prod-chains` `DISABLED`; `awsds-prod-model-app-etl` `Completed`, `list-model-packages` `[]`. Read again
  at 23:38:07, before its apply: the same, its policy holding `RegisterAndApproveAsTheProductionDeployRole`,
  `ReadTheVersionsAsTheStagingDeployRole` and `ReadTheStatusFromSandbox`.
- **[Claude] Staging's applies**, 22:37:29 to 22:38:45: `staging/chains/` *"Apply complete! Resources: 0
  added, 1 changed, 6 destroyed."*, the state machine's destruction taking 36 s; `staging/studio/` *"2 added, 0
  changed, 2 destroyed"*, the policy destroyed and created again within 22:38:20 to 22:38:33; and
  `staging/foundation/` *"0 added, 2 changed, 0 destroyed"*. Each re-planned `No changes` from `99a47744`,
  22:38:52 to 22:39:49.
- **[Claude] Staging read back** at 22:39:56: seven schedules, each `DISABLED`; `awsds-staging-chain-app-etl` the
  one `app-etl` state machine; no EventBridge rule named `*app-etl-train*`; `awsds-staging-workflows` `v1`,
  created 22:38:30, attached to the deployment project's role alone, nine statements, the training pair gone.
- **[Claude] Production's applies**, each on its own words: `production/chains/` 22:48:20 to 22:49:33, *"0
  added, 1 changed, 6 destroyed"*, the state machine 55 s; `production/studio/` 22:59:22 to 22:59:37, *"2 added,
  0 changed, 2 destroyed"*; `production/foundation/` 23:37:04 to 23:37:17, *"0 added, 2 changed, 0
  destroyed"*; and `production/sagemaker/` 23:38:45 to 23:38:58, *"0 added, 0 changed, 2 destroyed"*, the group's
  policy and then the group, each in a second. Each re-planned `No changes` from `main` right after its apply:
  22:49:56, 23:01:29, 23:37:36 with the var-file, and 23:39:12.
- **[Claude] Production read back**: at 22:49:56, six schedules `DISABLED`, `awsds-prod-chain-app-etl` and
  `-app-etl-warehouse` the `app-etl` state machines, no rule named `*app-etl-train*`; at 23:01:37,
  `awsds-prod-workflows` `v1`, created 22:59:34, attached to `deploy-production`'s role alone, eleven
  statements, the training pair gone; at 23:37:42, `awsds-deploy-prod`'s `apply-application` with five
  statements (`RunTheGovernedWarehouseDdl`, `FollowItsOwnStatements`, `ApproveTheModelATaskRegisters`,
  `DescribeTheEgressEndpoints`, `ReadTheDnsFirewallAssociation`) and `awsds-prod-deploy-project` at `v7` with
  seventeen, `PassTheProjectRoleToSageMaker` gone; at 23:40:11, `list-model-package-groups` listing
  `awsds-prod-model-app-ml` alone and `describe-model-package-group` on the retired group answering
  *"ValidationException … ModelPackageGroup arn:aws:sagemaker:us-west-2:<Production
  Account>:model-package-group/awsds-prod-model-app-etl does not exist."*
- **[Claude] lxiv's third half**: every slice the retirement touched re-plans `No changes` from `main`, the seven
  above and `staging/sagemaker/`, whose change was a comment, initialised and planned from `6d297252` at
  23:39:41 to 23:39:53. lxiv's second half stays unmeasured: the group held no version at its apply.
- **[Claude] The retired workflows' log groups**, read at 23:40:11 as at 21:42: Staging's with 34,965 bytes and
  Production's with 0, neither with a retention. No apply touched them.
- **[Claude] The instruments**, on the five infrastructure profiles. A first run at 23:40:11 passed the five
  as one word, zsh leaving an unquoted variable unsplit (Lesson 84), and each script stopped on *"no profile
  authenticated"*, writing nothing. Run again with the five as separate words: `./aws/orchestration.py`, 23:40:33
  to 23:43:24, exit 2, 125 checks passing, `OR-8` passing in both targets on `app-ml`'s versions and noting
  `awsds-prod-model-app-etl`'s two events as `awsds-deploy-prod` (the newest 2026-10-25 01:29:10), `OR-9` reading
  the remaining chains' schedules `DISABLED`, and 15 `OR-2` failures, each a log group with no retention
  (`EXC-25`), the two retired workflows' groups among them; `./aws/deploytargets.py`, 23:43:24 to 23:45:03, exit
  0, 44 checks passing, `DT-3` reading `awsds-prod-model-app-ml` alone with its two-statement policy, and
  `DT-8`'s note on `app_dbt.trades`. Neither run had a failed call.

## 2026-11-24 — `app-genai`'s `parse_answer` fix for R3, nothing up

*Claude's hand, a sitting with no AWS call, on the branch `claude/vigilant-shtern-ba2579`, the calendar's
2026-11-24 row (`promotion.md` §N.12.1). Times UTC.*

- **[Claude] The fix**, written by 00:23: `check.py`'s `parse_answer` reads the JSON object an answer begins
  with through `json.JSONDecoder.raw_decode`, after an opening code fence if it has one, and stops at its
  closing brace, so the text after it fails no answer. The report gains `text_after_object`, the ids of the
  answers let through that carry text after their object besides a closing fence. The planted values are
  searched for in the whole answer, as before. The prompt, the `Converse` request and the records `triage`
  writes are unchanged.
- **[Claude] Why the parse and not structured output**: the parse is one function of `check`, tested
  offline, and changes nothing the model or the guardrail receives. botocore 1.43.1, the worker's, holds
  `Converse`'s `outputConfig.textFormat` of type `json_schema` (read in the application's lock); which
  models honour it, Nova Lite among them, and what a guarded request's assessment does with it are unread,
  so it would change the request every stage sends and owe a Sandbox loop before R3.
- **[Claude] The tests**: `tests/test_check.py` gains the stray bracket, Production's answer to `m19` of
  2026-11-23 verbatim; the fence; the clean answer; a closing fence followed by text; a second object after
  the first; leading text and an array around the object, which still fail; and a planted telephone number
  after the object, which still fails the run. `uv run pytest` *"108 passed"*, 95 before. The negative
  control, the new tests against `check.py` at `1141d862` at 00:23:45: 12 fail, the stray bracket on *"m01:
  the answer is no JSON object with a label of the list"*, Production's wording for `m19`. `ruff check` and
  `ruff format --check` pass; `awsds-workflows lint .` at `4401f91` with the pipeline's seven instance types
  *"ok: 3 arquivo(s)"*.
- Nothing went to GitLab: `v0.1.1` is R3's tag.

## 2026-11-24 — Pass 6: Claude's halves of 6.1 to 6.4, the APIs read and nothing created

*Claude's hand, as the infrastructure user with `InfrastructureAccess` in `Sandbox Account 1`
(`awsds-infra-sandbox-1`), reads alone: the policy simulator is a read, and nothing was created. No account
id is written. Times UTC.*

- **[Claude] The listings**, 00:25:41: `list-clusters` `{"ClusterSummaries": []}`, `list-partner-apps`
  `{"Summaries": []}` and `list-feature-groups` `{"FeatureGroupSummaries": []}`.
- **[Claude] Feature Store's runtime** (6.4), 00:25:56: `describe-vpc-endpoint-services` lists 598 services in
  `us-west-2`, among them `com.amazonaws.us-west-2.sagemaker.featurestore-runtime` and its `-fips` twin, an
  `Interface` service owned by `amazon` in `us-west-2a` to `us-west-2d`, private DNS
  `featurestore-runtime.sagemaker.us-west-2.amazonaws.com` and `featurestore-runtime.sagemaker.us-west-2.api.aws`,
  endpoint policies supported. No `.tf` file under `terraform-modules/` or `terraform-live/` names
  `featurestore-runtime`. Partner AI apps have a service of their own, `aws.sagemaker.us-west-2.partner-app`,
  private DNS `*.partner-app.us-west-2.sagemaker.aws`, which no slice names either.
- **[Claude] The project roles' policies**: Sandbox's six project roles carry the same three AWS managed
  policies, `SageMakerStudioProjectRoleMachineLearningPolicy` v48, `SageMakerStudioProjectUserRolePolicy` v77
  and `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9, beside each project's `awsds-sandbox-*`
  policies, and no inline policy. No statement names a cluster or a partner-app action. The ML policy's
  `SageMakerFeatureStorePermission` allows `sagemaker:*Feature*` and `sagemaker:*Record` on `*` where
  `aws:ResourceTag/AmazonDataZoneProject` equals `${aws:PrincipalTag/AmazonDataZoneProject}`, and its
  `SageMakerListPermissions` allows `sagemaker:ListFeatureGroups` on the principal tag
  `EnableSageMakerMLWorkloadsPermissions` `true`.
- **[Claude] The simulation**, 00:29:13 to 00:29:37, as `eighth-experimentation`'s project role, the context
  carrying the Region and the role's `AmazonDataZoneProject` and `EnableSageMakerMLWorkloadsPermissions` tags,
  which the simulator does not read from the role (`SUP-008`), each action name checked first against
  SageMaker's Service Reference v1.5. On a feature group tagged with the caller's project,
  `CreateFeatureGroup`, `DescribeFeatureGroup`, `UpdateFeatureGroup`, `DeleteFeatureGroup`,
  `DescribeFeatureMetadata`, `UpdateFeatureMetadata`, `PutRecord`, `GetRecord`, `BatchGetRecord`,
  `BatchWriteRecord` and `DeleteRecord` read `allowed` through the ML policy, Organizations and the boundary
  allowing; on a group tagged with another project, each `implicitDeny`; `AddTags` with `aws:TagKeys`
  `AmazonDataZoneProject` `implicitDeny` (`SUP-267`); `ListFeatureGroups` `allowed`. With the caller's tag in
  the context, `ListClusters`, `ListClusterSchedulerConfigs`, `CreateCluster`, `DescribeCluster`,
  `UpdateCluster`, `DeleteCluster`, `ListClusterNodes`, `BatchAddClusterNodes`, `ListPartnerApps`,
  `CreatePartnerApp`, `DescribePartnerApp`, `UpdatePartnerApp`, `DeletePartnerApp`,
  `CreatePartnerAppPresignedUrl` and `CallPartnerAppApi` each read `implicitDeny`, no statement matched.
  Verification xxxiii's role half reads: every feature-group action, on a group of the caller's project.
- **[Claude] The `PartnerApps` blueprint** (6.2), 00:31:01: `list-environment-blueprints --managed` on
  `awsds-studio` lists it as `5cj3vjg02pcrf4`. Sandbox's 14 blueprint configurations are
  `AmazonBedrockChatAgent`, `AmazonBedrockEvaluation`, `AmazonBedrockFlow`, `AmazonBedrockFunction`,
  `AmazonBedrockGuardrail`, `AmazonBedrockKnowledgeBase`, `AmazonBedrockPrompt`, `DataLake`, `EmrServerless`,
  `MLflowApp`, `S3Bucket`, `S3TableCatalog`, `SageMakerAIDomain` and `Tooling`; none is `PartnerApps`'s.
- **[Claude] `ML-7`** (6.3) gains the feature groups, each project role's grants for the three entries from
  every policy on it, attached and inline, and the runtime's endpoint service; a grant for clusters or partner
  apps fails it. `./aws/sandbox-ml.py`, 00:35:05 to 00:40:28, exit 0, *"all checks passed"*: `ML-7` passing on no
  cluster, no partner app and no feature group, on no HyperPod and no Partner AI apps grant on any of the six
  roles, and on the quotas at 20, 30, 8 and 10; noting the Feature Store grant on the six roles and the
  runtime's service, which no slice declares. The grant helpers read a synthetic `sagemaker:CreateCluster`, a
  `sagemaker:*`, two `NotAction` statements and a `Deny` as expected.
- **[Claude] `make check`**, run with every edit of the branch: *"check: OK"*.
- The user's page halves of 6.1, 6.2 and 6.4 wait on the user's readings.

## 2026-11-24 — Pass 6: the pages of 6.1, 6.2 and 6.4, read in the portal and nothing created

*Claude's hand in the user's Chrome, on the portal session the user opened for it (*"Abri uma sessão no
chrome no SMUS para você realizar esta leitura agora."*), signed in as the Data Scientist User (read in the
account menu), in `eighth-experimentation`, with the estate down; two reads as the infrastructure user
(`awsds-infra-sandbox-1`). Each form and panel was cancelled and nothing was submitted; the project's *Update
project* banner was left alone, and the tab was closed at 01:00:52. No account id or address is written.
Times UTC, from 00:49.*

- **[Claude] 6.1, HyperPod**: Compute's *HyperPod clusters* tab (`compute?type=hyperpod`), under the banner
  0.9 read, *"No connections to display."* *Add compute* opens at its third step, *Enter details*, type
  *SageMaker HyperPod*, and asks a connection name, the cluster's name (*"found in SageMaker Console"*), an
  access role ARN (*"the IAM role ARN that this project needs to assume"*), an account ID (*"the AWS account
  ID the runtime role exists in"*) and the Region. Its first step offers *Create new compute resources*
  (Amazon Redshift Serverless, EMR Serverless) and *Connect to existing compute resources* (SageMaker
  HyperPod alone), its second *All compute types (1)*. The page connects a project to a cluster that exists
  and creates none. Cancelled.
- **[Claude] 6.2, Partner AI apps**: absent, as 0.9 read on 2026-11-21. No entry in the left navigation, the
  *Manage* menu (*Govern*: Domain units, Blueprints; *Catalog management*: Assets, Subscription requests,
  Data sources, Metadata forms, Business glossaries, Custom asset types), the Generative AI group
  (Playground; AI apps, the Bedrock IDE) or Discover's filters (All, Assets, Data products, Files, Models,
  Notebooks, Jobs, Workflows, Feature groups). *Resource blueprints* → *Deploy* offers the *Managed
  blueprints* EMR Serverless, Lakehouse Database, MLflow App and S3 Bucket, the gallery `app-ml-dev`'s owner
  read on 2026-11-21 (`docs/SMUS.md` §Resource blueprints); cancelled. No page shows the four partners.
- **[Claude] 6.4, Feature Store**: AI/ML → Feature Store (`feature-store`), an introduction card (*Feature
  groups*, *Real-time Inference*, *Batch Ingestion*) and *"You don't have any feature groups."*; the empty
  page has no *Feature groups* or *Features* tab. *Create feature group* has three steps, *Feature group
  details*, *Feature definitions* and *Tags - optional*. The first asks a name, a description (*"cannot be
  changed once created"*) and a *Store configuration*: *Online*, *Offline* or *Online and offline*. With
  *Online and offline* chosen in the unsaved form, it pre-fills:
  - online: storage type *Standard*, not editable; the key `alias/awsds-sandbox-project` by its ARN; *Time to
    Live (TTL)* off (*"Once TTL has been enabled for a feature group, it cannot be disabled."*);
  - offline: `s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/dev/data/ml/feature-store`;
    table format *Glue (Default)* or *Iceberg*; the IAM role, the project's own
    `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`; the same key; throughput *On-demand (default)*;
  - the data catalog: *"Create a table to store your offline Feature Store data."* checked, the catalog
    `AwsDataCatalog`, not editable, and the database `new_database`, `glue_db_blerpkhn9nj7o0` or one typed,
    under *"These databases are configured with the Lake Formation permissions required to create the
    offline store table."*; the table name empty.

  Cancelled on its first step. AWS documents the page for IAM-based domains alone, and this Identity Center
  domain shows it and its form.
- **[Claude] The form's values**, read by 00:59:36: the key `alias/awsds-sandbox-project`, customer managed,
  *"SMUS project resources in this account - blueprint-provisioned volumes and artifacts (Stage 6). NOT the
  data CMK."*, the projects bucket's key (`docs/GOVERNANCE.md` §Encryption); both databases in Sandbox's Glue
  Data Catalog, located at the project's `dev/data/catalogs/`, `glue_db_blerpkhn9nj7o0` created 2026-10-26
  21:25:41 and `new_database` 2026-10-28 06:22:40. *Resource blueprints* lists a `DataLake` deployment named
  `create-datalake-database-env-new_database-1793168541728`.
- Pass 6 is read, 6.1 to 6.4. Verification xxxiii's page half: the form writes the offline store as the
  project role, under the project's prefix and key, into a project database; how its Glue table meets Lake
  Formation stays unread while no group exists.

## 2026-11-24 — The readings that create nothing: 9.8's increments, 10.7, 10.11's liii, liv and lvii, and 9.11's loose ends

*Claude's hand, as the infrastructure user with `InfrastructureAccess` in Staging, Production and `Sandbox
Account 1` (`awsds-infra-staging`, `awsds-infra-prod`, `awsds-infra-sandbox-1`), reads alone: quotas, the
Region's endpoint services, roles and policies, the policy simulator with the Region and the project tag in
the context (`SUP-008`), CloudTrail's event history, S3 and MWAA Serverless listings, CloudFormation's
registry, the providers' schemas, and two plans saved outside the repository. Two subagents of this session
read the vendor pages, most in their Markdown form. Nothing was created or applied. No account id is written.
Times UTC.*

- **[Claude] The token**, 01:47:23: the `awsds` session's `expiresAt` read 01:54:48, and the role credentials
  vended at 01:47:34 carried the CLI's reads past it (`SUP-012`). At 02:17:07 it read 02:47:36, ahead of the
  clock, and the two plans below ran under it.
- **[Claude] The endpoint quota** (9.8), 01:51:51: `ml.m5.large for endpoint usage` (`L-614B09FD`) reads 30.0
  in Sandbox, Staging and Production. Neither target has a request open, and Sandbox's one request, for 1.0 on
  2026-10-28 at 01:19, reads `CASE_CLOSED`. No support case is needed.
- **[Claude] The Region's endpoint services**, 01:51:51 and 01:52:16, the same in the three accounts, where
  `us-west-2a` is `usw2-az2` and `us-west-2b` is `usw2-az1`: `sagemaker.runtime` and its `-fips` twin,
  `bedrock-agent`, `bedrock-agentcore-control`, `bedrock-agentcore.gateway` and `s3vectors` in `usw2-az1` to
  `usw2-az4`; `bedrock-agent-runtime` and `bedrock-agentcore` in `usw2-az1` to `usw2-az3`. Each is an
  `Interface` service owned by `amazon` that takes an endpoint policy. Private DNS:
  `runtime.sagemaker.us-west-2.amazonaws.com` and `runtime.sagemaker.us-west-2.api.aws`,
  `bedrock-agent.us-west-2.amazonaws.com`, `bedrock-agent-runtime.us-west-2.amazonaws.com`,
  `bedrock-agentcore.us-west-2.amazonaws.com`, `bedrock-agentcore-control.us-west-2.amazonaws.com`,
  `*.gateway.bedrock-agentcore.us-west-2.amazonaws.com` and `s3vectors.us-west-2.api.aws`. In the code: the
  targets' interface endpoints sit in the subnet of `zone_ids[0]`, `usw2-az1`, a job's `VpcConfig` names the
  subnets of `usw2-az1` and `usw2-az2`, neither target's set names `sagemaker.runtime` (it left on
  2026-10-19, `staging/egress/main.tf`), and `vpc-egress` has no AgentCore group, its comment excluding
  `bedrock-agentcore*` by name.
- **[Claude] The project roles**, 01:52:59 to 01:54:10. Staging's and Production's deployment project roles,
  created 2026-11-11 at 15:26 and 15:30, carry `awsds-<env>-project-boundary` v6, AWS's
  `SageMakerStudioProjectUserRolePolicy` v77, `SageMakerStudioProjectRoleMachineLearningPolicy` v48 and
  `service-role/SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy` v9, and the account's `awsds-<env>-*`
  policies. Their trust names `bedrock.amazonaws.com` and neither `bedrock-agentcore.amazonaws.com` nor
  `agent-registry.amazonaws.com`; Sandbox's six project roles trust both. AWS's statements:
  - `AllowPassRoleOnProjectRoles` lets a role pass itself (`${aws:PrincipalTag/RoleName}`) in its own account
    to a list of services that holds `bedrock-agentcore.amazonaws.com`, `agent-registry.amazonaws.com` and
    `bedrock.amazonaws.com`.
  - `ACProjectResources` (the ML policy) allows `bedrock-agentcore:*AgentRuntime`, `*AgentRuntimeEndpoint`,
    `StopRuntimeSession` and the harness, memory, gateway, workload identity and API key families on `*`
    where `aws:ResourceTag/AmazonDataZoneProject` is the caller's; `ACTagOwnResources` allows `TagResource`
    under the request's and the resource's tag; `CreateSLR` allows seven service-linked roles, AgentCore's
    `RuntimeIdentity`, `Network`, `GatewayNetwork` and `Identity` among them.
  - `DataConnectionLambdaLogs` (the user-role policy) allows `logs:CreateLogGroup`, `CreateLogStream`,
    `PutLogEvents` and `DescribeLogStreams` on `/aws/bedrock-agentcore/runtimes/*`, and `CWPutMetrics`
    `cloudwatch:PutMetricData` in the namespace `bedrock-agentcore`.
  - `BedrockResourceAccessPermissions` names `bedrock:CreateKnowledgeBase` among 47 actions on
    `arn:aws:bedrock:*:*:*`, under `EnableAmazonBedrockPermissions` and the resource's project tag;
    `BedrockNoResourcePermissions` names `ListKnowledgeBases` and `RetrieveAndGenerate` on `*`.
  - Neither `AWSServiceRoleForBedrockAgentCoreNetwork` nor `AWSServiceRoleForBedrockAgentCoreRuntimeIdentity`
    exists in the three accounts (`NoSuchEntity`, 01:52:59 and 02:05:01).
- **[Claude] When Sandbox's project roles came to trust AgentCore**, 01:55:56 and 01:56:05: CloudTrail holds
  eight `UpdateAssumeRolePolicy` events since 2026-10-01, every one by the session
  `AmazonDataZoneEnvironmentDeployer-<Sandbox Account 1>`. The first, 2026-10-11 at 22:05:59 on
  `eighth-experimentation`'s role, writes a trust naming neither `bedrock-agentcore` nor `agent-registry`. The
  seven from 2026-11-14 at 02:07:51 name both: `app-etl-dev`'s, 47 s after its role's creation;
  `test-experimentation`'s at 2026-11-18 19:15:39; `throwaway-6d`'s (`b94v2p77d11oy8`) at 21:45:07;
  `app-dbt-dev`'s, `app-ml-dev`'s and `app-genai-dev`'s at 2026-11-19 00:18:32, 00:18:58 and 00:19:17; and
  `eighth-experimentation`'s again at 2026-11-22 05:21:04. Read again at 02:36:49, after the user's five
  *Update project* of 01:47 to 01:49 (6d's log): no write since 2026-11-22, while the deployer session's 63 IAM
  calls from 01:48:28 to 01:49:53 were `GetRole`, `ListRolePolicies`, `ListAttachedRolePolicies`, `GetPolicy`
  and two `TagRole`, on roles that already held the list. `SUP-168` holds the reading.
- **[Claude] The boundaries and the organization's policies**, 01:56:42 to 01:57:20. Staging's v6 (19
  statements) and Production's v6 (20) allow everything but `bedrock:*` (`CeilingIsEverythingTheIdentityPolicyGrants`,
  a `NotAction`), and of Bedrock the guardrail statements and the one model's invoke alone, so every knowledge
  base action is outside their ceiling; `DenyServicesNoProjectUsesHere` denies `bedrock-agentcore:*` and
  `agent-registry:*`. Sandbox's v3 (9 statements) allows `*`. The five SageMaker statements are the same in
  the three boundaries; `DenySageMakerInstanceCeiling` names `ml.m5.large` among its seven types, and no
  boundary or SCP statement asks a volume key of `CreateEndpointConfig`
  (`DenySageMakerJobsWithoutVolumeEncryption` names the five job creates and `CreateTransformJob`). The
  `Workloads` SCP holds the same five and `DenySageMakerServerlessInference`. No organization policy names
  `s3vectors` or a knowledge base; the one AgentCore statement, `DenyAgentCoreBuiltInTools`, is the
  interactive OU's.
- **[Claude] 9.8's endpoint, simulated**, 01:58:31 to 02:00:56 as each deployment project role and 02:22:08 as
  `app-ml-dev`'s. AWS's SageMaker creates condition on `aws:ResourceTag/AmazonDataZoneProject`, so a create
  is simulated with the request's and the resource's tag.
  - `allowed` in the three accounts by `SageMakerStudioProjectRoleMachineLearningPolicy`:
    `CreateEndpointConfig` on `ml.m5.large`, with the volume key and without; `CreateEndpoint`;
    `DescribeEndpoint`, `DescribeEndpointConfig`, `InvokeEndpoint`, `UpdateEndpoint`, `DeleteEndpoint` and
    `DeleteEndpointConfig` on tagged objects; `ListEndpoints` and `ListEndpointConfigs`; `CreateModel` in a
    VPC with network isolation; `DeleteModel`. `iam:PassRole` of the role to itself for
    `sagemaker.amazonaws.com` `allowed` by `SageMakerStudioProjectUserRolePolicy`.
  - `sagemaker:AddTags` with the project's key on the endpoint configuration and on the endpoint:
    `implicitDeny` in both targets; `allowed` in Sandbox by `awsds-sandbox-ml`'s
    `TagAnEndpointConfigWithTheCallersProject` and `TagAnEndpointWithTheCallersProject`; `implicitDeny` as
    `app-genai-dev`'s role, which no `sandbox/ml/` statement names (`SUP-267`).
  - A describe of a free name: `implicitDeny` for an endpoint, a configuration and a model in the three.
  - The negatives: `ml.g5.xlarge` `explicitDeny`, by the `Workloads` SCP in the targets and by
    `awsds-sandbox-project-boundary` in Sandbox; a serverless configuration (`sagemaker:ServerlessMemorySize`
    2048) `explicitDeny` by the `Workloads` SCP in the targets and `implicitDeny` in Sandbox.
- **[Claude] 9.8's pipeline, simulated**, 01:59:23 as `app-ml-dev`'s role: `CreatePipeline` with the
  project's tags, `AddTags` with the project's key (by `awsds-sandbox-ml`), `UpdatePipeline`,
  `DescribePipeline`, `ListPipelines`, `StartPipelineExecution`, `DescribePipelineExecution`,
  `ListPipelineExecutionSteps`, `DescribePipelineDefinitionForExecution`, `ListPipelineExecutions`,
  `DescribeTrainingJob`, `DeletePipeline` and `iam:PassRole` of the role to itself for
  `sagemaker.amazonaws.com` read `allowed`; `CreatePipeline` with no tag and a describe of a free name
  `implicitDeny`.
- **[Claude] 10.7's knowledge base, simulated**, 01:59:23 to 02:03:33 as the deployment project roles and
  `app-genai-dev`'s.
  - In the targets every knowledge base action, the Titan invoke and `s3vectors:QueryVectors` read
    `implicitDeny`, the boundary's ceiling refusing (`AllowedByPermissionsBoundary` false for the Bedrock
    ones); `iam:PassRole` of the role to itself for `bedrock.amazonaws.com` `allowed`.
  - In Sandbox `GetKnowledgeBase`, `CreateDataSource`, `GetDataSource`, `ListDataSources`,
    `StartIngestionJob`, `GetIngestionJob`, `Retrieve` and `DeleteKnowledgeBase` on a tagged knowledge base,
    `ListKnowledgeBases`, `RetrieveAndGenerate` and the Titan invoke read `allowed` by
    `SageMakerStudioProjectUserRolePolicy`; `Retrieve` on an untagged one `implicitDeny`.
  - `CreateKnowledgeBase` reads `implicitDeny` in the three accounts, on `*` with the request's and the
    resource's tag, and on a knowledge base's ARN with no organization or boundary detail. The Service
    Reference gives it no resource type, and the simulator never applies a statement naming a resource to such
    an action while the service may (`SUP-008`, `SUP-346`): whether AWS's statement on `arn:aws:bedrock:*:*:*`
    admits the create is read from the call.
  - `iam:PassRole` of a role named `awsds-x-app-genai-kb` to `bedrock.amazonaws.com` and
    `s3vectors:QueryVectors` read `implicitDeny` in the three: no statement grants either.
- **[Claude] 10.11's runtime, simulated**, 01:59:23 to 02:03:33.
  - In the targets every runtime action, `CreateAgentRuntimeEndpoint` and `TagResource` read `explicitDeny`
    by the boundary's `DenyServicesNoProjectUsesHere`.
  - In Sandbox `UpdateAgentRuntime`, `GetAgentRuntime`, `InvokeAgentRuntime`, `StopRuntimeSession` and
    `DeleteAgentRuntime` on a tagged runtime and `ListAgentRuntimes` read `allowed` by `ACProjectResources`.
    `CreateAgentRuntime` on `*` reads `allowed` with the request's and the resource's tag and `implicitDeny`
    with the request's tag and the two VPC keys alone, so a create goes through only if the service puts the
    request's tag in `aws:ResourceTag` at create, as SageMaker's creates do; `CreateAgentRuntimeEndpoint`
    and `TagResource` on `*` `allowed`.
  - In the three, `iam:PassRole` of the role to itself for `bedrock-agentcore.amazonaws.com` reads `allowed`,
    of an execution role named `awsds-x-app-genai-agent` `implicitDeny`, and `iam:CreateServiceLinkedRole`
    of the network and runtime-identity roles `allowed` by `CreateSLR`.
- **[Claude] The registry and the providers** (10.7, Lesson 8), 02:05:01 to 02:06:37: CloudFormation's
  `AWS::S3Vectors::VectorBucket`, `AWS::S3Vectors::Index`, `AWS::S3Vectors::VectorBucketPolicy` and
  `AWS::BedrockAgentCore::Runtime` read `PUBLIC`, `LIVE`, `FULLY_MUTABLE`, the index's `DataType`,
  `Dimension`, `DistanceMetric` and `EncryptionConfiguration` among its create-only properties. The studio
  slices' pins, aws 6.69.1 and awscc 1.106.0, hold `aws_s3vectors_vector_bucket`, `aws_s3vectors_index`
  (`encryption_configuration` with `kms_key_arn` and `sse_type`; `metadata_configuration` with
  `non_filterable_metadata_keys`, required), `aws_s3vectors_vector_bucket_policy`,
  `aws_bedrockagent_knowledge_base` with `storage_configuration.s3_vectors_configuration`, and
  `aws_bedrockagentcore_agent_runtime`; awscc holds `awscc_s3vectors_vector_bucket`, `awscc_s3vectors_index`,
  `awscc_s3vectors_vector_bucket_policy` and `awscc_bedrock_knowledge_base`. The S3 gateway endpoint's
  allow-list (`terraform-modules/vpc`, `vpc-v0.4.0` in both targets) names no `acr-code-*` bucket.
- **[Claude, a subagent] AgentCore's pages** (liii, liv, lvii), the report at 02:00:27:
  - The archive: the common-issues page has the role that calls `CreateAgentRuntime` or `UpdateAgentRuntime`
    hold `s3:GetObject` on the object and `kms:Decrypt` on its customer managed key, while the same section's
    *"When this occurs"* line names the execution role, the Python guide's console section asks the execution
    role for S3 access, and the permissions page's direct-deploy example holds no `s3:` or `kms:` statement.
    No page names `s3:GetObjectVersion`, a bucket policy or a forward access session. The service stores the
    code in a service-owned bucket, `acr-code-*-<region>-an` in the example endpoint policy under
    `aws:PrincipalServiceName` `bedrock-agentcore.amazonaws.com`, encrypted with AWS owned keys, and reads it
    at each agent startup; for a runtime created after the rollout that began on 2026-05-05, *"all network
    access, including to Amazon S3, is governed exclusively by your VPC configuration"*, and
    `requireServiceS3Endpoint` is refused on create. A microVM session runs the artifact deployed when it was
    created.
  - The VPC keys: `security-vpc-condition.html`'s `EnforceVPCRuntime` denies `CreateAgentRuntime`,
    `UpdateAgentRuntime`, `CreateCodeInterpreter` and `CreateBrowser` when `bedrock-agentcore:subnets` and
    `bedrock-agentcore:securityGroups` are both null (`Null` `true`, one block). `UpdateAgentRuntime`'s
    `networkConfiguration` is not required, so an update that omits it would meet the deny (the subagent's
    inference). No key names the network mode. The authorization reference's operations table: a
    `CreateAgentRuntime` also authorizes `CreateAgentRuntimeEndpoint`, `PassCapacityProvider`, `TagResource`
    and `iam:PassRole` to `bedrock-agentcore.amazonaws.com`; `UpdateAgentRuntime` `PassCapacityProvider` and
    the pass; `DeleteAgentRuntime` `DeleteAgentRuntimeEndpoint` and `DeleteWorkloadIdentity`;
    `InvokeAgentRuntime` `InvokeAgentRuntimeForUser`.
  - The logs: the service creates `/aws/bedrock-agentcore/runtimes/<agent_id>-<endpoint_name>`, stdout and
    stderr in `[runtime-logs] <UUID>` streams and the ADOT logs in `otel-rt-logs`. No page names who writes
    stdout. The execution role's examples hold `logs:CreateLogGroup` and `DescribeLogStreams` on the prefix,
    `CreateLogStream` and `PutLogEvents` on its streams, `PutResourcePolicy` (*"to allow AWS X-Ray to deliver
    spans to the log group"*), X-Ray's four actions and `cloudwatch:PutMetricData` in `bedrock-agentcore`.
    Traces need CloudWatch Transaction Search, a one-time account setup. VPC mode lists `ecr.dkr`, `ecr.api`,
    the S3 gateway and `logs` as required without internet access.
  - The service-linked roles: `AWSServiceRoleForBedrockAgentCoreNetwork` (`network.bedrock-agentcore.amazonaws.com`,
    `BedrockAgentCoreNetworkServiceRolePolicy` v1), created with a runtime in VPC mode, and
    `AWSServiceRoleForBedrockAgentCoreRuntimeIdentity`, created with any runtime since 2025-10-13; the
    operations table lists neither creation. The supported zones in `us-west-2` are `usw2-az1` to `usw2-az3`.
- **[Claude, a subagent] The knowledge base's, S3 Vectors' and Pipelines' pages** (10.7, li, lxi), the report
  at 02:03:33:
  - The service role (`kb-permissions.html`): trusted by `bedrock.amazonaws.com` under `aws:SourceAccount` and
    `ArnLike` `aws:SourceArn` `knowledge-base/*`; `bedrock:InvokeModel` on the embeddings model; `s3:ListBucket`
    and `s3:GetObject` under `aws:ResourceAccount`, the bucket's key by `kms:Decrypt` under `kms:ViaService`
    S3; `s3vectors:PutVectors`, `GetVectors`, `DeleteVectors`, `QueryVectors` and `GetIndex` on the index.
    No statement for a vector key; S3 Vectors' encryption page requires `kms:Decrypt` for every vector-level
    operation. `CreateDataSource`, `UpdateDataSource` and `StartIngestionJob` pass no role.
  - The create: `indexArn` alone, or `vectorBucketArn` with `indexName`; float32 alone; cosine or euclidean;
    Titan Text Embeddings V2 at 1,024, 512 or 256 dimensions; a store created for the caller is the console's
    alone. The operations table: `CreateKnowledgeBase` has no resource type and authorizes
    `CreateKnowledgeBase`, `TagResource`, `AssociateThirdPartyKnowledgeBase` and `iam:PassRole` to
    `bedrock.amazonaws.com`; `StartIngestionJob` authorizes `AssociateThirdPartyKnowledgeBase` too. No page
    asks the caller for an `s3vectors` action.
  - The providers' history: the aws provider's S3 Vectors resources since 6.24.0, the index's encryption and
    metadata blocks since 6.26.0, a knowledge base's `s3_vectors_configuration` since 6.27.0; awscc's since
    1.62.0, the index's encryption since 1.67.0.
  - Pipelines: the definition's JSON schema admits a parameter (`ArgumentFunction`, `{"Get": "Parameters.X"}`)
    for each item of `VpcConfig.Subnets` and `SecurityGroupIds` or for the whole list, in a processing and in
    a training step; the SDK v2 types each item `Union[str, PipelineVariable]`. An update that changes the
    definition creates a version, one that changes nothing while passing aliases fails, and one that changes
    nothing without aliases is not described.
  - The authorization reference has an operations table in place of its *Dependent actions* column, and
    `list_amazonbedrockagentcore.html`, `list_amazonbedrock.html` and `list_amazons3vectors.html` redirect to
    `list_bedrock-agentcore.html`, `list_bedrock.html` and `list_s3vectors.html`.
- **[Claude] 9.11's loose ends**, 02:06:37 to 02:09:39. By `grep` over `examples/`, `scripts/` and `aws/`,
  nothing writes or lists the outputs bucket's top-level `models/`: `app-ml`'s model lives under its project
  bucket's `shared/app-ml/models/`. `list-objects-v2` at 02:08:48: 13 objects under
  `awsds-staging-outputs/models/app-etl/` and 5 under `awsds-prod-outputs/models/app-etl/`, written
  2026-10-24 and 25 by the retired model chain. Sandbox's workflows at 02:09:22:
  `app_etl_test_experimentation_app_etl_train` is gone, deleted 2026-11-15 at 22:36:48 (Stage 19's log), and
  `app-etl-dev` holds `app_etl_app_etl_dev_app_etl_train`, `READY`, last modified 2026-11-15 22:24:39,
  beside `app_etl_app_etl_dev_app_etl` (22:24:24): `v0.7.0` left it in place.
- **[Claude] The edits and the plans**: D28's amendment and its one line, the decisions index, the approval
  rule's comment in `production/sagemaker/registry.tf`, `sagemaker-application.md` §S's deploy-role grant and
  Stage 19's note on `targets.py`, brought to the retirement; `deploy_prefixes` without `models/` in
  `staging/data/` and `production/data/`, with Production's outputs-bucket descriptions. Planned from the
  branch with `-input=false`, each plan saved outside the repository: `staging/data` 02:18:26 to 02:18:43 and
  `production/data` 02:19:36 to 02:19:55, each *"Plan: 0 to add, 1 to change, 0 to destroy."*,
  `module.outputs_bucket.aws_s3_bucket_policy.this` updated in place, `DenyTheReleaseRoleObjectsOutsideItsPrefixes`
  losing `arn:aws:s3:::awsds-<env>-outputs/models/*` from `NotResource` and
  `DenyTheReleaseRoleListingsOutsideItsPrefixes` `models/*` from `s3:prefix`, and nothing else. Nothing
  applied: both slices carry the change until it is applied from `main` after R3, on the user's word naming
  it (Lessons 69, 79).
- The measured halves stay with the sittings (`promotion.md` §N.12.1): li's reads in `dev`,
  `CreateKnowledgeBase`'s authorization among them, xxxv's operator calls and Stage 9 xvii's cross-zone reach
  in SB2 and R4; liv's `Null` refusal, lvii's writer and door, and lxi's unchanged update in SB3 and R5.
