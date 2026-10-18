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
