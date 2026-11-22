# Runbook — the Bedrock IDE in a SageMaker Unified Studio project

| | |
|---|---|
| **Scope** | The objects the Generative AI menu's builder, the Bedrock IDE, makes in a Sandbox project: the prompt, the guardrail, the flow app, the knowledge base, the evaluation and the chat agent app. For each: what it is in AWS, which identity creates it and which runs it, what the project key must allow, how the portal names it, how it is deleted, and what the portal hides; and around them, the doors, the models, the ceilings and the costs. The menu, the models, the playground and the path of a model call to a target are [`sagemaker-ai-ml.md`](sagemaker-ai-ml.md) §G |
| **Operator** | The **data scientist** builds in the portal as a member of the project. The **infrastructure user** (`InfrastructureAccess`, `awsds-infra-sandbox-1`) writes the key's statements in `sagemaker-prereqs`, applies `sandbox/sagemaker/`, and reads the objects and the trail with §V's instruments |
| **The rules** | **The builder's objects stay in Sandbox**: a target has no IDE, and the CI/CD CLI's bundle carries none of them (D17, D41). **Each saved object is a DataZone environment** of the project, which DataZone deploys as a CloudFormation stack. **The portal's banner never names a refusal's cause**: the trail or the browser's network response does (§F). **The project key needs statements** SMUS's key-permissions page does not name (§K) |
| **The picture around it** | [Stage 17](../stages/stage-17-sandbox-machine-learning.md) pass 7, steps 7.2 to 7.6, and its decisions 1, 5, 10, 12 and 26, cited by number. The platform behaviours are `SUP-187`, `SUP-410`, `SUP-411`, `SUP-417`, `SUP-418`, `SUP-419`, `SUP-445`, `SUP-446` and `SUP-447` in [`docs/AWS_SUPPLEMENT.md`](../../AWS_SUPPLEMENT.md). The key is [`terraform-modules/sagemaker-prereqs/kms.tf`](../../../terraform-modules/sagemaker-prereqs/kms.tf), and the prices are [`docs/PRICING.md`](../../PRICING.md), "Knowledge Bases and Guardrails" |
| **Written** | 2026-11-22, from `promotion.md` §N.9's day 2 in `eighth-experimentation`, where each object below was built, refused or both. Each reading is in [the Stage 17 log](../../log/log-stage-17-sandbox-machine-learning.md) under that date, and the AWS pages read are in [`docs/REFERENCES.md`](../../REFERENCES.md) |

| Section | Audience | What it holds |
|---|---|---|
| [§O](#o-the-pieces) | both | the pieces: each object, what it is in AWS, which identity creates it and which runs it, what bills at rest |
| [§I](#i-the-doors-the-models-and-the-ceilings) | the infrastructure user | the doors, the models a project reaches, the ceilings on every call, what a sitting bills |
| [§N](#n-the-names) | both | the names: where the portal's name lives, what each environment and resource is called, the inference profiles |
| [§K](#k-the-project-key) | the infrastructure user | the project key: what the builder puts under it, the statements SMUS's page omits, the grants a guardrail leaves |
| [§B](#b-building-each-object) | the data scientist | building each object: the form, what it sends, what the lab read |
| [§X](#x-deleting-an-object) | both | deleting: the portal's two acts for a failed component, and what survives them |
| [§F](#f-a-refusal-by-its-wording) | both | a refusal by its wording, its cause and the way through |
| [§V](#v-the-instruments) | the infrastructure user | the instruments, one per question |
| [§U](#u-what-is-unmeasured) | both | what is unmeasured, each with the step or verification that closes it |

---

## O. The pieces

**An object is an environment.** Each object the builder saves is a DataZone environment of the project,
made from the project profile's blueprint of its kind: `AmazonBedrockPrompt`, `AmazonBedrockGuardrail`,
`AmazonBedrockFlow`, `AmazonBedrockKnowledgeBase`, `AmazonBedrockEvaluation`, `AmazonBedrockChatAgent` or
`AmazonBedrockFunction`. DataZone deploys it as the stack `DataZone-Env-<environment id>`, whose handler
calls Bedrock as the provisioning role; the trail attributes those calls to `datazone.amazonaws.com`, session
`AmazonDataZoneEnvironmentDeployer-<account>`. The chat agent app is the exception: *Save* writes its
definition and creates nothing until *Deploy*. A flow app's first *Save* creates its environment; a later
*Save* writes the definition alone, and each test message deploys it (`SUP-448`).

| Identity | What it does in the builder |
|---|---|
| The provisioning role, `awsds-sandbox-smus-provisioning` | the stacks' creates: `CreatePrompt`, `CreateGuardrail`, `CreateFlow` and `PrepareFlow`, the knowledge base's vector bucket and index, `CreateAgent`; a flow's `UpdateFlow` and `PrepareFlow` at each test |
| The project role, `datazone_usr_role_<project id>_<suffix>` | the portal's own calls: a prompt's test (`ConverseStream`) and its versions, `CreateEvaluationJob`. It is the knowledge base's role: a sync's embeddings run as it, session `EmbeddingTask-<job id>`, and so does a flow's query embedding (`InvokeModel`), both from `bedrock.amazonaws.com` |
| The service role, `AmazonBedrockServiceRole-<project id>-<suffix>` | a flow's run: a knowledge base node's generation and a prompt node's `Converse`; an evaluation's inference and its pre-flight `Converse`; the chat agent's `CreateAgent` names it as the agent's role |
| The model-management role, `AmazonSageMakerBedrockModelManagementRole-<account>` | the project's application inference profile for a model, at the model's first use (§N) |
| The page itself | the chat agent's preview, `InvokeInlineAgent`, and a flow's test, `InvokeFlow` on the alias `TSTALIASID`, both sent by the browser to `bedrock-agent-runtime.us-west-2.amazonaws.com` |

**The flow's own role.** A flow app's environment also creates `AmazonBedrockFlowServiceRole-<environment id>`,
with AWS's `SageMakerStudioBedrockFlowServiceRolePolicy` and no permissions boundary, and the flow does not
use it: the blueprint configuration's boundary does not reach it, and the stack hands the flow the project's
service role (`SUP-447`). Its trust admits this account's flows alone, and the project role may not pass it.
`ML-8` fails on it while the flow exists, and what becomes of it is the user's (§U).

| Object | What the builder creates | Runs as | In the lab, 2026-11-22 |
|---|---|---|---|
| Prompt | an environment; its stack's `CreatePrompt`; each version by `CreatePromptVersion` as the project role | the project role, for the editor's test | `KWK4ZJRAWD`, two versions, the second asking for Brazilian Portuguese |
| Guardrail | an environment; its stack's `CreateGuardrail`, under the project key | the caller of the model it guards | `razikgicppzy`, `DRAFT`, one denied topic, after `sagemaker-prereqs-v0.14.0` (§K) |
| Flow app | an environment; its stack's `CreateFlow` and `PrepareFlow`, under the project key, then `UpdateFlow` and `PrepareFlow` at each test (`SUP-448`) | the service role; a knowledge base node's embeddings as the knowledge base's role | `Q9HHV1YRRX`, `Prepared`, a knowledge base node over `ml-demo-runbooks` before the prompt node (7.4b's fallback); no *Share* |
| Knowledge base | an environment; an S3 Vectors bucket under the project key and its index; the knowledge base and its data source on a prefix of the projects bucket | the project role | `QWDNVYXADH`, `ACTIVE`, 2 of 20 runbooks indexed (`SUP-411`) |
| Evaluation | an environment whose stack holds one output and no resource; the job, by `CreateEvaluationJob` as the project role | the service role | `31epl34t77s3`, Nova Lite, `Completed`; Haiku 4.5's refused (`SUP-418`) |
| Chat agent app | *Save*: a definition file. *Deploy*: an environment `<uuid>-shared` and its stack's `CreateAgent` | the service role, named in the create | built; its preview and its deploy refused by Agents Classic (`SUP-446`) |
| Function | a Lambda function an agent calls | | not created (decision 10) |

**The definition files.** The builder keeps each component's definition in the project's prefix of the
projects bucket, `amazon-bedrock/builder/components/<kind>/<uuid>-definition.json`, and each app's in
`amazon-bedrock/builder/apps/chatApp/` or `apps/flowApp/<uuid>-definition.json`, all written by the project
role. A row of
*My components* stays while its definition does, after its environment is gone (§X).

**What bills at rest** is the knowledge base's S3 Vectors store, by storage: 0.06 USD per GB-month, cents for
the runbooks. The other objects bill per use (§I), and a flow's own price is not in `docs/PRICING.md` (§U).

## I. The doors, the models and the ceilings

**The doors.** A call from a space reaches Bedrock through the VPC's interface endpoints, two optional
groups of `vpc-egress`: `bedrock-base` (`bedrock`, `bedrock-runtime`) and `bedrock-agent` (`bedrock-agent`,
`bedrock-agent-runtime`), raised with `make up ENV=sandbox GROUPS=…` ([`docs/NETWORK.md`](../../NETWORK.md)).
The house image's `NO_PROXY` carries every group's names, so a call to a group left down times out instead
of leaving through the proxy. The builder needs no door of its own: DataZone's creates and the project role's
`CreateEvaluationJob` and `StartIngestionJob` carry no `vpcEndpointId` (§V, 2026-11-22). A notebook's call
takes one, the `Retrieve` of §U among them.

**The models a project reaches** pass three layers ([`sagemaker-ai-ml.md`](sagemaker-ai-ml.md) §G):

- The account enables a model for the portal: decision 13 (b), the domain's model governance project and
  `sandbox/model-access/`, whose `project_models` admits Claude Opus 4.5, Sonnet 4.5 and Haiku 4.5, copied
  from their `us.` profiles, and Titan Text Embeddings V2 and Nova Lite, on demand.
- The SCP's ceiling, `DenyBedrockInvocationOutsideTheScopedModels`, refuses every other model on whichever
  pass names it ([`POLICIES.md`](../../../terraform-live/identity/org-policies/POLICIES.md)).
- The project's application inference profile for the model (§N), created at its first use.

The builder's lists offered Nova Lite and the three Claude 4.5 models to the chat agent, the evaluation and a
flow's knowledge base node, and Titan V2 to the knowledge base (2026-11-22).

**The retention ceiling.** `DenyInvokingModelsThatRetain` refuses, to every principal, the models the vendor
names as retaining traffic for review, `anthropic.claude-fable-5`, `anthropic.claude-fable-5-1` and
`anthropic.claude-fable-5-2`, and Bedrock's retention mode `none`, hand-managed, is declared in all 17 Regions
(6e 7.5). AWS refuses `claude-opus-5`, `claude-sonnet-5`, `claude-opus-5-5`, `claude-sonnet-5-5` and
`claude-haiku-5-5` to this account (`EXC-08` in [`docs/AWS_STATE.md`](../../AWS_STATE.md)). None of these
models appears in the builder's lists.

**The boundary.** Every project role and every `AmazonBedrock*` role the Tooling environment creates carries
`awsds-sandbox-project-boundary` (D13); the flow's own role is the exception (§O, `SUP-447`).

**What a sitting bills**, from `docs/PRICING.md`: Claude Haiku 4.5 through its `us.` profile at 1.10 USD per
million input tokens and 5.50 per million output; Nova Lite at 0.06 and 0.24; Titan V2's embeddings at 0.02
per million; a guardrail at 0.15 USD per 1,000 text units for each of its content and topic policies; S3
Vectors at 0.06 USD per GB-month stored and 0.20 per GB put. Each optional endpoint group adds to the hub's
hourly rate while it is up. `./aws/bedrock-usage.py` reads a window's tokens and their cost (§V).

## N. The names

**The portal's name lives in the environment's description**, as JSON:
`{"resourceId":"<component uuid>","resourceName":"<the portal's name>","resourceDescription":"<the form's description>"}`.
The portal's URL carries the uuid (`/bedrock/prompts/<uuid>`, `/bedrock/promptFlows/<uuid>`). A reader that
lists Bedrock's objects finds none under the name the portal shows (`SUP-445`).

| Object | The environment | The Bedrock resource |
|---|---|---|
| Prompt | `<uuid>-dev` | `Bedrock-Prompt-<environment id>` |
| Flow app | `<uuid>-dev` | `Bedrock-Flow-<environment id>` |
| Guardrail | `<uuid>-dev` | `<uuid>-dev`, the environment's name |
| Knowledge base | `<uuid>-dev` | `<project id>-<portal name>`; its vector bucket `amazon-bedrock-ide-<project id>-<environment id>`, the index `amazon-bedrock-ide` |
| Evaluation | `<project id><portal name>`, with no separator and no description | the job, under the same name |
| Chat agent app | `<uuid>-shared`, at *Deploy* | the agent, never created here |

**The tags.** The flow and the guardrail carry `AmazonDataZoneProject`, `AmazonDataZoneEnvironment`,
`AmazonDataZoneBlueprint`, `AmazonDataZoneDomain` and `AmazonBedrockManaged`. The first vector bucket carried
no tag (`SUP-410`).

**The application inference profiles.** The project holds one application inference profile per model its
objects used, created by the model-management role at the model's first use and named
`<domain id> <project id>`; the domain's, from the playground, are named `<domain id>` (`SUP-187`,
`SUP-445`). `eighth-experimentation` holds four: Claude Opus 4.5 (2026-10-30), Titan Text Embeddings V2 (at
the knowledge base's create), Claude Haiku 4.5 (at the prompt's first test) and Nova Lite (at the
evaluation's submit, 4 s before its environment). The embeddings, the evaluation's inference and the agent's
create each named one. Haiku 4.5's profile routes to `us-east-1`, `us-east-2` and `us-west-2`.

## K. The project key

**What the builder puts under the project key.** The key the Tooling configuration carries encrypts the
vector bucket (the `KmsKeyArn` of `CreateVectorBucket`; the knowledge-base form takes no key), the guardrail,
the prompt, the flow and the knowledge base's data source. The evaluation job runs with no customer key, and
its output lands under the project key by the bucket's default.

**The statements SMUS's page does not name.** SMUS's key-permissions page lists ten statements, none for S3
Vectors, a knowledge base or a guardrail (read 2026-11-22). A key written to that page refuses every IDE
knowledge base on S3 Vectors and every IDE guardrail. `sagemaker-prereqs` adds both, each on its blueprint's
switch (Lesson 14):

| `Sid` | What it allows | Without it | Since |
|---|---|---|---|
| `AllowS3VectorsIndexingOfTheBedrockIdesVectorBuckets` | `indexing.s3vectors.amazonaws.com` `kms:Decrypt`, for the buckets `amazon-bedrock-ide-*` of this account, under `kms:EncryptionContextKeys` `aws:s3vectors:arn` or `aws:s3vectors:resource-id`: S3 Vectors' documented statement | `CreateIndex` refused, the knowledge base's environment failed (`SUP-410`) | `sagemaker-prereqs-v0.13.0`, applied to `sandbox/sagemaker/` 2026-11-22 at 01:23 UTC |
| `AllowGuardrailCreationByTheProvisioningRole` | Bedrock's `PermissionsForGuardrailsCreators`, `kms:Decrypt`, `kms:GenerateDataKey`, `kms:DescribeKey` and `kms:CreateGrant`, with the principal narrowed to the provisioning role | `CreateGuardrail` refused on the key, the environment `CREATE_FAILED` (`SUP-417`) | `sagemaker-prereqs-v0.14.0`, applied 2026-11-22 at 02:39 UTC |

`sandbox/sagemaker/` pins `v0.14.0`; `staging/studio/` and `production/studio/` stay on `v0.11.0`, where no
IDE runs.

**The grants a guardrail leaves.** At `CreateGuardrail`, Bedrock created three grants on the project key, each
with `bedrock.us-west-2.amazonaws.com` as grantee and retiring principal. Two are bound to the encryption
context `aws:bedrock:guardrail-id`. The third carries no constraint and allows `Decrypt`, `Encrypt`,
`GenerateDataKey`, `CreateGrant`, `RetireGrant` and `DescribeKey` (`SUP-417`): Bedrock holds the whole
project key for as long as it keeps that grant (§U).

## B. Building each object

**The prompt.** *Build* → *Prompt*: a model, the text and its variables (the lab's `{{excerpt}}`). The first
test of a model creates the project's profile for it (§N). *Save* takes about a minute and creates the
environment. The split button's *Create version*, chosen from its dropdown, only switches the button's
action; the button's next click creates the version. The editor drops Top P: a form at Temperature 1 and
Top P 0 stored `temperature` 1.0, `maxTokens` 4096 and `stopSequences` `Human:`, with no `topP` (`SUP-418`).

**The guardrail.** *AI apps* → *Asset gallery* → *My components* → *Create component* → *Guardrail*. The
form offers two policies, *Content filters*, shown only as enabled, and *Denied topics*, as SMUS's guardrail
page lists: no PII, word or grounding filter can be set. The blocked message applies to the input and to the
responses. The lab's guardrail stores its content filters at `HIGH` both ways for violence, hate, sexual and
insults, and `NONE` for prompt attack and misconduct. Its create needs §K's second statement.

**The flow app.** *Build* → *Flow*: a canvas and a palette, whose *Nodes* tab lists *Collector*,
*Condition* and *Iterator*; *Agent* and *Prompt*; *Knowledge Base*, *S3 Retrieval* and *S3 Storage*; and
*Flow output*. The builder has no model node: a prompt node carries the model and points at a prompt
version, `prompt/<id>:<version>`. A *Knowledge Base* node takes the knowledge base, a response model (Opus
4.5 preselected) and a guardrail, with no search type and no result count; it takes `retrievalQuery` and
returns `outputText`, a generated answer with no citation, and the flow stores the project's application
inference profile for the model and the guardrail at `DRAFT`. The lab's flow is `FlowInputNode` →
`KnowledgeBaseNode_1` (`ml-demo-runbooks`, Claude Haiku 4.5, `ml-demo-guardrail`) → `Prompt_1` (the
prompt's version 2) → `FlowOutputNode`. Claude in Chrome's pointer drag from the palette leaves the canvas
empty; a scripted HTML5 drag (`dragstart`, `dragenter`, `dragover` and `drop`, carrying
`application/reactflow`) places a node, and the edges take a pointer drag.

The first *Save* creates the environment and prepares the flow, in about three minutes. A later *Save* reads
*"Saved"* and writes the definition alone; each test message updates the stack, whose `UpdateFlow` and
`PrepareFlow` deploy the saved definition, then invokes the flow, 70 to 80 s from the send to the answer
(`SUP-448`). A flow read with `get-flow` therefore shows the last test, never the last *Save*. A flow app
has no *Share*: *My apps* lists it *"Not shared"*, and AWS's share page describes chat agent apps alone.

Over the two indexed runbooks the lab's flow answered the questions whose answer they hold, and the prompt
node rewrote the other two: a question outside them came back as a request for *"conteúdo real do
runbook"*, and the guardrail's denied topic as a remark that the excerpt held *"uma mensagem de erro
genérica"*. The guardrail's blocked message and the knowledge base's no-answer text reach the user only
through the next node.

**The knowledge base.** *AI apps* → *Asset gallery* → *My components* → *Create component* → *Knowledge
Base*. The form opens on OpenSearch Serverless and 256 dimensions; this estate takes Titan Text Embeddings V2
at 1024 dimensions, floating-point, and Amazon S3 Vectors (decision 12), since a classic OpenSearch
Serverless collection holds an OCU while it exists. *Project data sources* → S3 takes a prefix of the
projects bucket, the lab's `shared/ml-demo/bedrock/kb/`. *Foundation model as a parser* is disabled under
*"Access to model required"*, which leaves the default parser and the default chunking: fixed size, 300
tokens, 15 % overlap. The create starts a sync by itself, and its creates need §K's first statement.

The index the IDE creates leaves `AMAZON_BEDROCK_METADATA` filterable, and the form exposes no index setting.
Over the 20 Markdown runbooks, the sync indexed 2 and failed 18 on S3 Vectors' 2 KB cap on a filterable
string (`SUP-411`). The 2 indexed hold one Markdown table each and the 18 failed two or more, a correlation
and not a cause. A knowledge base the IDE creates on S3 Vectors keeps this index for its life.

**The evaluation.** *Build* → *Model evaluation*: a model, a task, metrics and a dataset. The IDE runs
automatic evaluations alone, with no judge model and no human workers. Under *Question and answer*, a
custom dataset takes Toxicity alone; Accuracy and Robustness keep the built-in BoolQ, Natural Questions and
Trivia QA (`SUP-419`). The form sends `temperature` and `top_p` together, which every Claude model refuses,
so the IDE evaluates Nova Lite and no Claude model; its *Default* sends `maxTokens` 2048, `temperature` 0 and
`topP` 0, values its panel does not show (`SUP-418`). The upload dialog warns *"Once uploaded, you cannot
delete the file"*, and a second upload under the same name replaces the file. The list's *Date created*
column is headed *(UTC-07:00)* and shows the browser's local time. The lab's job completed in ten minutes,
and its one output file holds each prompt, its reference response, the model's answer and the metric's
score: `Builtin.Toxicity` from 0.00035 to 0.00123 over 20 records.

**The chat agent app.** *Build* → *Chat agent*: a model, a system prompt, inference parameters, *Data* (a
knowledge base; *Override default search* selects hybrid search and the number of source chunks),
*Guardrails* and functions. The *Model* list offers Nova Lite and Claude Haiku 4.5, Opus 4.5 and Sonnet 4.5,
the three Claude models marked *Cross-region* (verification xxv). *Save* asks for no name and writes the
definition, which names the model by a catalog listing revision whose asset has the `us.` system profile as
its base, holds `temperature`, `topK` and `maxTokens` with no `topP`, and names the knowledge base and the
guardrail by component uuid (`SUP-446`).

The app is an Agents Classic agent: *Preview* calls `InvokeInlineAgent` and *Deploy* calls `CreateAgent`, and
Agents Classic refuses both to an account with no prior agent use; AWS's page says *"There is no exception
process."* (verification xxxiv). In this account the chat agent app neither previews nor deploys. The
builder's alternative is a flow app with a knowledge base node (above), which chains fixed steps and runs no
agent loop; an agent an application promotes is AgentCore's (decision 26 (a),
[`sagemaker-ai-ml.md`](sagemaker-ai-ml.md) §G).

**The function** is not created: the Lambda it makes runs outside the VPC with a function's default internet,
outside D38's hub (decision 10).

## X. Deleting an object

**A failed component is deleted in two acts.** Its row in *My components* carries an error icon and no menu.
*Resource blueprints* lists its deployment, `<uuid>-dev`, *Deployment failed*, with a delete whose dialog
reads *"Permanently delete blueprint deployment …? Deleting a blueprint deployment is final and removes all
connections created."* and takes `confirm`. The row then offers *Delete*, which removes the definition
file. Both acts ran for the knowledge base (01:25 and 01:30 UTC) and the guardrail (02:41:22 and 02:42:55),
whose environment `get-environment` then read `ResourceNotFoundException`.

**What survives the deletes**, read 2026-11-22:

- The knowledge base's vector bucket: the first attempt's `amazon-bedrock-ide-<project id>-cie8747bea6mxc`
  survived both acts, empty (`SUP-410`).
- The application inference profile a failed create made; the next create reuses it.
- An evaluation's environment after a refused job: `6fl52xzq3yt768` stays `ACTIVE` with no job.
- The chat agent's `-shared` environment after a refused deploy: `b343orq3qka5n4`, `CREATE_FAILED`.
- The evaluation dataset, which the form says cannot be deleted once uploaded, under the projects bucket's
  `…/genAI/assets/evaluations/input/`.
- A shared chat agent's snapshot: AWS's page says it cannot be unshared without deleting the app.

What stays and what goes is decision 5's (7.6); deleting an object is the user's act.

## F. A refusal by its wording

The portal's banner names no cause. The cause is in the trail, read by event name and time, or in the
browser's network response for a call the page sends itself; an `AccessDenied` with no message is separated
from IAM by the simulator (Lesson 24).

| The portal reads | The cause, by its wording | The way through |
|---|---|---|
| *"Amazon Bedrock couldn't deploy the Knowledge Base. Delete this component, and then create a new one. [Failed to create environment …: … S3Vectors index creation failed: Insufficient access to perform asynchronous indexing. …]"* | `CreateIndex` refused: the key grants `indexing.s3vectors.amazonaws.com` nothing (`SUP-410`) | §K's first statement; delete in two acts (§X) and create again |
| A sync `FAILED`, or `COMPLETE` with failures: *"Metadata value is invalid: exceeds 2048 byte string limit"*, and per document *"The document was not indexed. No content could be extracted from it, or processing ended before it completed."* | the index leaves `AMAZON_BEDROCK_METADATA` filterable (`SUP-411`) | none in the form (§U) |
| The guardrail's environment: *"Access denied for operation 'AWS::Bedrock::Guardrail'."* | `CreateGuardrail`: *"You don't have sufficient permissions for this KMS key."*; `kms:CreateGrant`: *"… no identity-based policy allows the kms:CreateGrant action"*, both as the provisioning role (`SUP-417`) | §K's second statement |
| *"An error occurred while creating the evaluation job: Unknown error. Potentially invalid input"* | `Converse` and `CreateEvaluationJob`: *"`temperature` and `top_p` cannot both be specified for this model. Please use only one."* (`SUP-418`) | Nova Lite; no Claude model |
| The preview's *"Something went wrong."* under *"Failed to run application Amazon Bedrock encountered an error when invoking the Bedrock runtime API. Try again later."* | `InvokeInlineAgent`, 403 in the browser's response: *"Bedrock Agents is in Maintenance Mode. New agent creation is not available for accounts without prior service usage."* (`SUP-446`) | none in this account: a flow app (7.4b) or AgentCore (decision 26 (a)) |
| The deploy's *"… failed to stabilize after create/update: … Access denied for operation 'AWS::Bedrock::Agent'."* | `CreateAgent` `AccessDenied`, with no message and no KMS call; the simulator reads it allowed (`SUP-446`) | the same |
| A flow's answer saying its excerpt holds only *"uma mensagem de erro genérica"* | the guardrail blocked the question at the knowledge base node, and the prompt node rewrote the blocked message: `InvocationsIntervened` under `TopicPolicy` and `Input` (§V) | the question, outside the denied topic |
| A flow's answer asking for a runbook's real content, the excerpt holding *"uma mensagem genérica de indisponibilidade"* | the knowledge base found nothing: the answer is in none of the indexed documents (`SUP-411`), and the prompt node rewrote the no-answer text | none until the index takes the documents |
| A flow edited and saved that answers as before | *Save* wrote the definition and deployed nothing (`SUP-448`) | a test message, which deploys it |
| *"Access to model required"* on *Foundation model as a parser* | not read | the default parser |
| *"This tool is not available for this project."*, *"No models found. Contact your admin to enable more models."* | the menu's blueprints or the models' enablement | [`sagemaker-ai-ml.md`](sagemaker-ai-ml.md) §G |
| A model call refused *"with an explicit deny in a service control policy"* | `DenyBedrockInvocationOutsideTheScopedModels` or `DenyInvokingModelsThatRetain` (§I) | a scoped model; [`sagemaker-ai-ml.md`](sagemaker-ai-ml.md) §F holds the dated readings |
| *"… is not available for this account … contact AWS Sales"* | AWS's refusal of `claude-opus-5`, `claude-sonnet-5` and the three 5.5 models, `EXC-08` | none: a Claude 4.5 model |

## V. The instruments

Each runs as the infrastructure user (`InfrastructureAccess`), `AWS_PROFILE=awsds-infra-sandbox-1`, and
reads only.

| Question | Instrument |
|---|---|
| The objects by kind and project tag, the knowledge base's store and sources, the vector buckets, the Bedrock roles' boundary, and the trail's creates with their principal and door | `./aws/sandbox-ml.py`, check `ML-8`, which fails on each flow's own role (`SUP-447`) |
| A shared app's snapshot in the project's catalog | `./aws/catalog.py` |
| The tokens the objects consumed | `./aws/bedrock-usage.py <start>Z <end>Z` |
| The environment behind a portal name | `aws datazone list-environments --domain-identifier <domain id> --project-identifier <project id>`, its description's `resourceName` (§N) |
| A sync's counts and reasons | `aws bedrock-agent list-ingestion-jobs --knowledge-base-id <id> --data-source-id <id>`, then `get-ingestion-job` |
| The index's non-filterable keys | `aws s3vectors get-index --vector-bucket-name <bucket> --index-name amazon-bedrock-ide` |
| What an evaluation sent | `aws bedrock get-evaluation-job --job-identifier <arn>`, its `inferenceParams`, which the trail hides (`SUP-418`) |
| The project's profiles | `aws bedrock list-inference-profiles --type-equals APPLICATION` |
| The grants on the key | `aws kms list-grants --key-id <project key>`, whose `CreationDate` prints in the laptop's time |
| A refused create | `aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=<event>`; for `CreateAgent`, the IAM simulator with resource `*`, since the action takes no resource type |
| A refusal of a call the page sends itself | the browser's network response, `InvokeInlineAgent`'s among them |
| The definition a flow runs | `aws bedrock-agent get-flow --flow-identifier <id>`, which reads the last test's deploy (`SUP-448`); the saved definition is the app's file in the projects bucket |
| Whether the guardrail intervened, on which policy and which side | `aws cloudwatch get-metric-statistics --namespace AWS/Bedrock/Guardrails --metric-name InvocationsIntervened`, with the dimensions `GuardrailArn` and `GuardrailVersion`, or `GuardrailContentSource`, `GuardrailPolicyType` and `Operation=ApplyGuardrail`; `Invocations` counts two per answered question and one per blocked input |
| The door of a flow's model calls | the event's `vpcEndpointId` against `aws ec2 describe-vpc-endpoints`: a knowledge base's calls carry an id the account does not hold (`SUP-449`) |

## U. What is unmeasured

| What | Closed by |
|---|---|
| `Retrieve` on the knowledge base from a space, through `bedrock-agent-runtime` | verification xxiv |
| A shared app's snapshot in the project's catalog, and answers that cite the runbooks' chunks | none in this account: the chat agent app is refused (`SUP-446`), a flow app has no *Share* (`SUP-448`), and a knowledge base node returns no citation |
| A flow's `InvokeFlow` and its knowledge base's `Retrieve` and `RetrieveAndGenerate`: data events, which `lookup-events` never returns | none planned |
| Which metadata key exceeds 2 KB in the 18 failed runbooks | none planned (`SUP-411`) |
| Whether the guardrail's unconstrained grant is retired with the guardrail | the guardrail's deletion, which decision 5 does not plan |
| What becomes of the flow's own role: an exception, the flow's deletion, whose stack holds the role, or a boundary attached by hand | the user's ([`waiting-on-the-user.md`](../waiting-on-the-user.md)) |
| The export's zip | 10.8 |
| A flow's own price | not in `docs/PRICING.md` |
| The S3 Vectors store's idle bill | 7.6 |
