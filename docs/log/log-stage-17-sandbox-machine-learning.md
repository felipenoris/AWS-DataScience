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
