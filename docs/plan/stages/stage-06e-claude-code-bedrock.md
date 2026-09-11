# Stage 6e — Claude Code on Bedrock, inside the remote IDE

| | |
|---|---|
| **Status** | **Not started.** Written 2026-09-11 against the vendor documentation and eight read-only measurements taken the same day in `Sandbox` (step 0). The stage exists because [6d](stage-06d-unified-studio-remainder.md) step 7 opened the remote IDE and the user installed the *Claude Code for VS Code* extension in it, whose first act was `api.anthropic.com` — refused by the compute plane, `403 TCP_DENIED` × 17 ([`remote-ide.md`](../runbooks/remote-ide.md) §N). This stage replaces that refused call with a call to Amazon Bedrock inside the estate's own perimeter |
| **Prerequisites** | [6d](stage-06d-unified-studio-remainder.md) step 2 (the house image is selectable; `default-v0.2.0` carries the proxy environment) and step 7 (the remote session works, and [`remote-ide.md`](../runbooks/remote-ide.md) says how). [6c](stage-06c-networking-hub.md) pass 5 for the proxy and the generated `NO_PROXY`. Nothing here waits on a vend |
| **Consumes** | [D1](../decisions/D01-region.md) (the region is a variable — step 7.3 records the exception this stage buys), [D11](../decisions/D11-lab-lifecycle.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D17](../decisions/D17-interactive-vs-runtime.md), [D26](../decisions/D26-unified-studio.md), [D38](../decisions/D38-single-egress-hub.md). Principle 2 rules out one of the vendor's five credential options before the stage starts (step 5.1) |
| **Proves** | The first **Bedrock invocation** in this estate. `docs/PRICING.md` §5 has carried the Claude token rates as a named gap since 2026-08-21 — *"price the specific model against the inference profile before leaning on it"* — and step 0.4 closes it. `docs/SMUS.md`'s six `AmazonBedrock*` blueprints stay unexercised: this is a different consumer of the same service |

*Read with [`remote-ide.md`](../runbooks/remote-ide.md) (the channel this runs inside),
[`dev-env.md`](../runbooks/dev-env.md) (the image that delivers the configuration) and
[`docs/NETWORK.md`](../../NETWORK.md) (what a space reaches).*

---

**Objective:** a data scientist working in a Sandbox space asks a coding assistant a question about the
code in front of them, the model answers, and **no byte of the question leaves AWS, is written to durable
storage anywhere, or becomes readable by anyone outside the institution**. The last clause is the
requirement; the rest is plumbing.

The objective this serves is `objectives.md`'s *"use of IA models built in SageMaker Unified Studio"*,
read narrowly. That bullet names the portal's own Bedrock surface, which this stage does not touch. What
it does is open the **Bedrock plane** — the account's first invocation, its first model-access form, its
first inference-profile pin and its first token bill — so that when the portal's blueprints are
exercised they arrive at a perimeter that already exists.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — run only after the user authorizes that specific action in chat |
| **[user]** | the console, the space's terminal, the VS Code window — the parts no AWS API performs |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make, in the same sitting |

## Step numbers are identifiers, not an order

Step 2 (the form) gates every invocation and can be done first, alone, in five minutes. Steps 3, 4 and 7
are independent of each other and all three precede step 6, which is the only step that sends a prompt.
Step 5 is a repository edit that can be written before any of them and delivered by step 5.4's image
build. Step 8 is the close.

---

## 0. What is already measured

Read 2026-09-11 by Claude, all read-only, from `awsds-infra-sandbox-1` (account **Sandbox**, permission
set **InfrastructureAccess**). These are the stage's starting facts; nothing below re-derives them.

- **0.1 — Opus 5 is in the catalogue in `us-west-2`, and it is inference-profile only.**
  `get-foundation-model --model-identifier anthropic.claude-opus-5` returns `modelLifecycle.status
  ACTIVE`, `startOfLifeTime 2026-07-23`, `inputModalities [TEXT, IMAGE]`, `responseStreamingSupported
  true` and `inferenceTypesSupported ["INFERENCE_PROFILE"]`. The bare model id is therefore **not
  invocable**: a request must name a profile.
- **0.2 — Two profiles exist and both are `ACTIVE` in this account.** `us.anthropic.claude-opus-5` —
  *"Routes requests to Anthropic Claude Opus 5 in us-east-1, us-east-2 and us-west-2"*, three model ARNs
  — and `global.anthropic.claude-opus-5`. Neither is single-region, and no single-region option exists
  for this model. Step 7.3 is where that becomes a written exception rather than an omission.
- **0.3 — The model-access form has never been submitted here.**
  `get-use-case-for-model-access` → `ResourceNotFoundException: You have not filled out the request form.
  Fill out the form before getting access.` That is step 2's before-reading.
- **0.4 — The token rates, measured.** `docs/PRICING.md` §5 read the wrong offer file: the modern Claude
  models are not in `AmazonBedrock`, they are in **`AmazonBedrockFoundationModels`**, one `servicename`
  per model (`Claude Opus 5 (Amazon Bedrock Edition)`). From
  `AmazonBedrockFoundationModels/current/us-west-2/index.json`, published `2026-09-11T12:44:10Z`, per
  **1M tokens**:

  | Dimension | `us.` (standard) | `global.` (standard) |
  |---|---|---|
  | Input | 5.50 | 5.00 |
  | Output | 27.50 | 25.00 |
  | Cache read | 0.55 | 0.50 |
  | Cache write, 5-minute TTL | 6.875 | 6.25 |
  | Cache write, 1-hour TTL | 11.00 | 10.00 |

  The narrower routing costs **10%**. A batch tier exists on the `global.` profile (2.50 / 12.50) and no
  interactive assistant can use it.
- **0.5 — Model invocation logging is off.** `get-model-invocation-logging-configuration` returns
  nothing, which is the documented shape of *no configuration*. Step 7.4 decides whether it stays off.
- **0.6 — No policy in this organization denies Bedrock.** `POLICIES.md` carries no `bedrock:` action in
  any of the ten documents; `DenyUserCompute` reaches the `Data` and `Identity` OUs and names SageMaker,
  Glue, EC2, Athena, Lambda and ECS, never Bedrock. The `Interactive` OU permits the call today.
- **0.7 — The D13 boundary permits it too.** `awsds-sandbox-project-boundary`'s ceiling is
  `Allow * on *`; its denies are `s3:*` on the Lake Formation-registered prefixes, `kms:*` on the lake
  data key except via S3, and the `sagemaker-denies` module's statements. Nothing there reaches
  `bedrock:`. A boundary grants nothing, so step 3 is still a real question.
- **0.8 — `bedrock-runtime.us-west-2.amazonaws.com` is already reachable from a space, by the wrong
  door.** The compute plane's allow-list opens with `.amazonaws.com`, so the name is permitted through
  Squid; the image's `NO_PROXY` literal (50 entries, `images/dev-env/Dockerfile`) carries no Bedrock
  name, and the proxy sits in `VPC-Networking` where no Sandbox endpoint answers. A call made today
  would therefore succeed as a **public** call carrying neither `aws:SourceVpc` nor `aws:SourceVpce` —
  the same shape 6d found on `aws-language-servers.us-east-1.amazonaws.com`. Step 4 is about that and
  nothing else.

---

## To execute

### 1. Decide where the assistant runs

**Action:** pick the machine the `claude` process runs on. **Why:** it decides the principal, the
network path, the perimeter and the blast radius, and every later step reads differently on each side.
**Explanation:** the extension bundles its own copy of the CLI and spawns it; in a Remote-SSH session the
extension installs on the **remote** side, so *"install Claude Code"* means a different thing depending
on which of `remote-ide.md` §E's two surfaces the install happened in.

| | The space | The laptop |
|---|---|---|
| principal | the project role, `datazone_usr_role_<project>_<env>` | the persona, `awsds-scientist-sandbox` |
| credential | ambient, vended by the container | SSO, cached by the profile |
| network | the compute plane, and a VPC endpoint if step 4 builds one | the client plane, `open`, through the proxy |
| what the model can read | the space's filesystem and whatever the project role reaches — the lake included, through Lake Formation | the laptop's checkout |
| what a prompt can contain | governed data | whatever the laptop already holds |

**Decision due 1, and the recommendation is the space.** The work is there, the perimeter is there, and
an assistant on the laptop moves the interesting half of the problem outside every control this estate
has. The laptop is a separate question with a separate answer; nothing below is written for it.

### 2. Submit the model-access form

**Action:** submit the Bedrock use-case form once, in the account that will invoke.
**Why:** step 0.3 measured that it has never been submitted, and Anthropic models refuse the first
invocation without it. **Explanation:** the vendor calls this *"submit use case details"* and it is not
an approval queue — **access is granted immediately after submission**. Nobody reviews the answer before
the model works; the answer is a declaration on the record, which is why it is worth writing carefully
rather than quickly.

- **2.1 — [Claude reads, user decides] Where to submit it.** The two shapes are not equivalent:
  - **In `Sandbox` alone**, from the Bedrock console's Model catalog, as the infrastructure user. Access
    covers that account and no other.
  - **Once from `Management`**, through `PutUseCaseForModelAccess`, which the vendor documents as
    extending *"to child accounts automatically"*.

  **Recommended: `Sandbox` alone.** Principle 1 keeps the Management account bootstrap-only, and an
  org-wide grant would open Anthropic models in `Staging`, `Production`, `Data`, `Audit` and
  `Log Archive` — every account where D17 says no interactive compute runs and where nothing has asked
  for a model. The org-wide form is the right shape the day a second account needs one, and the cost of
  deferring it is one more form.

- **2.2 — [user] The answers.** The API reference gives the form's fields; the console renders the same
  six. The values, settled by the user 2026-09-11:

  | Field | Value |
  |---|---|
  | `companyName` | the institution's name |
  | `companyWebsite` | its site |
  | `industryOption` | **Banking / Financial Services** — pick the catalogue's nearest label, and use `otherIndustryOption` only if no banking label exists |
  | `intendedUsers` | the institution's data scientists — internal only, no external or public exposure |
  | `useCases` | data-science work: a coding assistant inside the institution's own development environment; code comprehension, refactoring, test writing and documentation over internal repositories; exploratory analysis support in notebooks. **No customer-facing application, no automated decisioning, no credit or risk scoring, no content generation for publication** |

  Write the exclusions as well as the inclusions. A use case stated only as what it is admits every
  reading of what it is not, and this form is the one place the institution's intent is on AWS's record.

- **2.3 — [Claude] Read it back.** `get-use-case-for-model-access` must stop returning
  `ResourceNotFoundException`. That is the whole verification, and it is the negative control for 0.3.

- **2.4 — [Claude] Whether `InfrastructureAccess` can submit it.** The call needs
  `bedrock:PutUseCaseForModelAccess`; the console path needs the same permission behind it. Read the
  permission set before the user opens the console, so a refusal is expected rather than discovered.

### 3. Give the principal the reach, and find out whether it already has it

**Action:** establish that the caller of step 1's choice can invoke Opus 5, and grant what is missing.
**Why:** the project role is authored by a blueprint (D26), not by this repository, so *granting* is a
different problem from *bounding* — INT-15 solved the second with `environment_role_permission_boundary`
and says nothing about the first. **Explanation:** reach is an intersection (Lesson 28): the identity
policy, the boundary, the SCPs and — here — the endpoint policy of step 4 all have to agree.

- **3.1 — [Claude] Measure what the project role already grants.** `Sandbox` enables eleven blueprint
  configurations including six `AmazonBedrock*` ones, and `docs/SMUS.md` records that the `Tooling`
  template carries **conditional Bedrock roles**. So the role may already hold `bedrock:InvokeModel*`
  and this step may be empty. Read the role's attached and inline policies rather than assuming either
  way; `list-attached-role-policies` plus `get-role-policy` per inline document.
- **3.2 — [Claude] The minimum the client needs.** The vendor's policy is four actions plus a
  marketplace pair:

  ```
  bedrock:InvokeModel
  bedrock:InvokeModelWithResponseStream
  bedrock:ListInferenceProfiles
  bedrock:GetInferenceProfile
  ```

  `ListInferenceProfiles` is what lets the client resolve `opus` to a profile that exists in this
  account instead of guessing; without `GetInferenceProfile` the client recovers by retrying with the
  other request shape, so the cost of omitting it is a round-trip and not a failure. The vendor also
  asks for `aws-marketplace:ViewSubscriptions` and `aws-marketplace:Subscribe` under
  `aws:CalledViaLast = bedrock.amazonaws.com`. **Measure whether they are needed here** before adding
  them: the account reaches these models through the use-case form of step 2, and a `Subscribe` this
  estate never needs is a permission granted for a vendor sentence rather than for a call (Lesson 41).
- **3.3 — [Claude] Scope the resource, not just the action.** `Resource` is the two profile ARNs and the
  foundation-model ARNs they route to, never `*`:

  ```
  arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-opus-5
  arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-5
  ```

  An inference profile is an account resource and the foundation model is not, which is why the second
  ARN has no account field. Both are needed: authorization is evaluated against the profile *and*
  against each model it routes to.
- **3.4 — [Claude reads, user decides] Where the grant lives, if 3.1 says one is needed.** The candidates,
  worst last: the blueprint's own template if it already does it (3.1's answer); a policy attached to
  the project role by hand, which a blueprint reconciliation may remove (INT-15's open half); a policy
  attached through `sandbox/sagemaker/`'s prerequisite slice, the mechanism 6a judged least likely to be
  overwritten. **Whatever is chosen, the step that proves it is a call, not a `get-role`.**

### 4. Put the call on the private path

**Action:** make `bedrock-runtime.us-west-2.amazonaws.com` resolve to an interface endpoint inside the
Sandbox VPC, and keep it out of the proxy. **Why:** step 0.8 measured that the call works today and
arrives *public*. **Explanation:** the perimeter conditions this estate writes — `aws:SourceVpc` and
`aws:SourceVpce` — are absent on a call that leaves through Squid, so a Bedrock invocation made now is
outside the data perimeter while looking exactly like one that is inside it.

- **4.1 — [Claude] A new optional endpoint group, narrower than the one that exists.**
  `terraform-modules/vpc-egress`'s `bedrock` group is four endpoints — `bedrock`, `bedrock-agent`,
  `bedrock-agent-runtime`, `bedrock-runtime` — sized for the portal's blueprints. This stage needs
  **two**: `bedrock-runtime` for the invocation and `bedrock` for the control-plane calls of 3.2. Add
  `bedrock-llm = ["bedrock", "bedrock-runtime"]` beside it rather than narrowing the existing group,
  which has a different consumer, and extend the `optional_service_groups` validation to admit the name.
  A new module tag follows (`vpc-egress-v0.12.0`), by the two-commit order in
  [`terraform-changes.md`](../runbooks/terraform-changes.md).
- **4.2 — [Claude⚡] Bring it up.** `make up ENV=sandbox GROUPS=bedrock-llm`. Two endpoints at
  ~USD 0.010/h each, `[E]`, and they leave on the next `make down` like everything else.
- **4.3 — [Claude] The bypass list moves with it.** `NO_PROXY` is generated from each endpoint's own
  `dns_entry` (`vpc-egress-v0.11.1`), so the two names join the list the moment the endpoints exist —
  in the **slice output**. The image carries a dated literal instead (6d decision 8), which is where the
  value actually reaches a process, so the list in `images/dev-env/Dockerfile` is 50 entries and knows
  nothing about Bedrock. Two deliveries, and they are not the same act:
  - in the session at hand, `export NO_PROXY="$(terraform output -raw no_proxy)"` per
    [`sg-proxy.md`](../runbooks/sg-proxy.md);
  - durably, a rebuild with the new `--build-arg NO_PROXY_LIST`, which is step 5.4.

  **The endpoints and the bypass list are one change in two places** (Lesson 33): an endpoint without
  the bypass entry sends the call to the proxy and out to the internet, and the call still works, which
  is how this fails silently.
- **4.4 — [Claude] An endpoint policy, because the default is full access.** The interface endpoint's
  default policy allows every Bedrock action to every principal. Narrow it to 3.2's actions on 3.3's
  resources, so the endpoint is a second, independent statement of the same intent rather than a hole
  under it.
- **4.5 — [Claude] Prove the door.** CloudTrail records `InvokeModelWithResponseStream` as a
  **management event**, so the organization trail already carries it with no data-event charge and no
  configuration. The reading is the `vpcEndpointId` field on the event, and the negative control is the
  proxy access log: `/awsds/prod/proxy` must contain **no** `bedrock-runtime` line for the same window.
  Two channels that do not share a failure mode, which is the test 6d used for `NO_PROXY` and the reason
  to use it again.
- **4.6 — [Claude] What the CloudTrail record does not contain.** `requestParameters` carries `modelId`
  and `responseElements` is `null`. So the estate gets **attribution without content**: who invoked,
  when, from which address and endpoint, against which model — and not one token of the prompt. That is
  the property step 7.4 is about to trade away if it turns invocation logging on.

### 5. Configure the extension, and put the configuration where it survives

**Action:** write the Bedrock settings into the image, not into a space. **Why:** `/home/sagemaker-user`
survives an app restart and dies with the space; a new space starts with nothing.
**Explanation:** this is 6d decision 8's shape again — a value that must be present before anything runs
belongs in the image — and Claude Code has a file made for it.

- **5.1 — [Claude] The credential, decided by principle 2.** The vendor offers five ways to authenticate:
  `aws configure`, static access keys, an SSO profile, `aws login`, and an **Amazon Bedrock API key**
  (`AWS_BEARER_TOKEN_BEDROCK`). The API key is a long-lived credential, and principle 2 admits none
  anywhere in this estate — **it is refused here, not weighed**. In a space, none of the five is needed:
  the container already carries the project role's credentials and the SDK's default chain finds them.
- **5.2 — [Claude] The institution's file, `/etc/claude-code/managed-settings.json`.** Managed settings
  sit above every other level and nothing a user writes overrides them. The image writes it:

  ```json
  {
    "env": {
      "CLAUDE_CODE_USE_BEDROCK": "1",
      "AWS_REGION": "us-west-2",
      "ANTHROPIC_MODEL": "us.anthropic.claude-opus-5",
      "ANTHROPIC_DEFAULT_OPUS_MODEL": "us.anthropic.claude-opus-5",
      "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
    },
    "skipWebFetchPreflight": true
  }
  ```

  `ANTHROPIC_MODEL` pins the session's model; `ANTHROPIC_DEFAULT_OPUS_MODEL` pins what the `opus` alias
  resolves to, so a later default change in the client does not silently move this estate onto another
  model. **Pinning is not cosmetic**: without it the alias resolves to the client's built-in default,
  which changes with the client version. `availableModels` is the key that stops a user picking
  something else from `/model`, and whether to set it is decision due 3.
- **5.3 — The small/fast model is a second pin, and it defaults to Sonnet.** Background work — session
  titles and the like — runs on the small/fast model, and on Bedrock that is the **default Sonnet**
  model rather than a Haiku, because Haiku may not be enabled in an account. Two consequences: a model
  this estate never named will be invoked unless something says otherwise, and `ANTHROPIC_DEFAULT_HAIKU_MODEL`
  is what names it. Whichever is chosen, step 2's form and step 3's resource scope must cover **both**
  models, or the first background task is a refusal in the middle of a working session.
- **5.4 — [Claude] The image build, `default-v0.3.0`.** It carries three changes: the new
  `NO_PROXY_LIST` of 4.3, the managed settings file of 5.2, and `rust-src` in the rustup profile, which
  6d already owed. The bump's order is [`dev-env.md`](../runbooks/dev-env.md) §B — apps gone first, a
  detach is `[]` — and the registered version freezes to a digest, not a tag.
- **5.5 — [user] The one setting the image cannot carry.** *Disable Login Prompt*
  (`claudeCode.disableLoginPrompt`) is a **VS Code** setting, not a Claude Code one, and
  `remote-ide.md` §E says the two IDE servers in a space keep **separate settings files**. So it is set
  once per surface: `~/.vscode-server/data/User/settings.json` for the remote session and
  `~/sagemaker-code-editor-server-data/data/User/settings.json` for the portal's Code Editor. A
  configuration that works in one surface and not the other is this file's most common failure, and it
  has bitten the estate once already (6d 8.4).

### 6. The first session, and what it is allowed to touch

**Action:** open the extension in a remote session and ask it one question about real code.
**Why:** every step above is a claim until a token is spent. **Explanation:** this is the step that
produces the readings steps 7 and 8 need, so it is run deliberately and read afterwards, not repeated
until it works.

- **6.1 — [user] Ask one question**, in a repository that holds no governed data, on a space started
  from `default-v0.3.0`.
- **6.2 — [Claude] Read the egress by host.** `/awsds/prod/proxy` for the session's window. **The pass
  condition is that no Anthropic name appears at all** — not `api.anthropic.com`, not
  `downloads.claude.ai`, not `statsig` or either Datadog intake. On Bedrock the vendor documents metrics,
  error reports and `/feedback` as **off by default**, and step 5.2's
  `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` closes the session-quality survey, which is on by default
  even there. A line on any of those names is a finding about the configuration, not about the network.
- **6.3 — [Claude] Read the invocation.** CloudTrail in `Sandbox`: `eventName
  InvokeModelWithResponseStream`, `eventSource bedrock.amazonaws.com`, the project role as
  `userIdentity`, `requestParameters.modelId` naming the profile, and `vpcEndpointId` present. That last
  field is 4.5's whole point.
- **6.4 — [Claude] Read the token volume.** From the first session's own accounting, and it is the one
  number step 8 cannot get any other way.

### 7. Does this meet the data-protection requirement

**Action:** answer the question the stage was asked, in writing, with each clause attached to its
evidence; then turn the two clauses that are defaults into controls.
**Why:** *"nothing that transits the model may be persisted outside the private cloud, nor be readable by
anyone outside the institution"* is a requirement, and a requirement satisfied by a vendor default is
satisfied by something nobody in this estate controls (Lesson 5). **Explanation:** the answer is
**yes, with three qualifications and two controls owed**, and the qualifications are the useful part.

- **7.1 — What the vendor states, and where.** The statements that carry the answer are not
  interchangeable:
  - **Bedrock's default is zero data retention and zero operator access.** *"Amazon Bedrock uses a zero
    operator access (ZOA) data security model. This means no operators of the service can access model
    input or output. Also, Amazon Bedrock uses a zero data retention (ZDR) data security model. This
    means that by default, Amazon Bedrock does not store model inputs or outputs."*
  - **The model provider receives nothing.** Each provider's models run in a Bedrock-owned deployment
    account: *"Because the model providers don't have access to those accounts, they don't have access
    to Amazon Bedrock logs or to customer prompts and completions."* The retention page adds that content
    sharing with model providers *"is not supported today"*, and that the legacy `provider_data_share`
    mode grants a permission that is not exercised.
  - **The default has named exceptions, and they are per model.** For **Claude Fable 5 and Fable 5.1**,
    *"all traffic will be retained for up to 30 days for automated offline abuse detection"*, with
    classifier-flagged traffic subject to human review by AWS. Several OpenAI models retain
    classifier-flagged traffic. **Opus 5 is on neither list**, and the retention page's own example names
    Claude Opus 4.8 as a model whose `allowed_modes` includes `none`, so *"data is not retained whatever
    mode you set"*.

  **The third statement is the one that decays.** It is a list on a vendor page, it grew when Fable 5
  shipped, and a model added to it tomorrow would change this estate's answer without changing anything
  in this repository. 7.2 is the instrument that reads it rather than trusting it.

- **7.2 — [Claude] Measure the retention mode, per account and per model.** Two readings, and the second
  is the load-bearing one:

  ```
  # the account's effective mode
  aws bedrock get-account-data-retention --region us-west-2 --profile awsds-infra-sandbox-1
  # the model's own allowed_modes - `none` present means ZDR applies whatever the account is set to
  ```

  A model whose `allowed_modes` contains `none` is retention-free by construction. A model whose minimum
  is `aws_review` retains for up to 30 days **and is simply unavailable** below that mode, so the failure
  is visible rather than silent. **Record the reading with its date.** If `get-account-data-retention` is
  absent from the installed CLI, the control-plane route is `GET /data-retention` and the reading is
  still owed.

- **7.3 — The residency qualification, which no setting removes.** `us.anthropic.claude-opus-5` routes to
  **us-east-1, us-east-2 and us-west-2** (0.2). A prompt is therefore *processed* outside `us-west-2`
  some of the time, inside AWS, over AWS's network. Under ZDR nothing is stored there — the abuse-detection
  page's residency sentence, *"retained inputs and outputs are stored in destination regions"*, is about
  models that retain, and Opus 5 does not. What remains is a transit fact, and it is real: **D1 says the
  region is a variable, and this is the estate's first resource that cannot honour it.** There is no
  narrower option — 0.1 makes the bare model id uninvocable and `global.` routes wider — so the choice is
  `us.`, at a 10% premium (0.4), recorded as a named exception in `docs/AWS_STATE.md` rather than left
  for a later reader to discover.

- **7.4 — [Claude reads, user decides] Model invocation logging, which is the requirement's mirror.**
  It is off (0.5). Turning it on writes **the full prompt and the full completion** to an S3 bucket or a
  CloudWatch log group **in this account** — inside the private cloud, which is what the requirement
  permits, and durable, which is what the requirement was written against. The trade is exact:
  - **on** buys `objectives.md`'s fourth DLP problem, exfiltration detection, on the one channel where a
    model sees governed data. It costs a durable copy of every prompt, which becomes a Macie subject at
    Stage 11 and a retention obligation at Stage 12.
  - **off** keeps 4.6's property — attribution without content — and leaves the assistant channel
    invisible to content inspection.

  **Recommended: off in Sandbox now, revisited at [Stage 11](stage-11-dlp.md) step 3.** The reason is not
  cost: it is that turning it on creates the exact artefact the requirement is about, and doing that
  before the threat model exists decides the question in the wrong order. If it is turned on later, it
  goes to S3 with the account's CMK and a lifecycle, never to CloudWatch with a default retention.

- **7.5 — [Claude] Turn the default into a control.** Two SCP statements, of which the mode deny is the
  load-bearing one:
  - **Deny any retention mode but `none`.** The write actions publish a `bedrock:DataRetentionMode`
    condition key, so a deny on `bedrock:PutAccountDataRetention` where the mode is not `none` makes it
    impossible for anyone in the organization to opt this estate into retention — including by accident,
    including in an account nobody is watching. A model that then requires `aws_review` becomes
    **unavailable** rather than quietly retaining, which is the failure mode to want.
  - **Deny the models that require retention**, by name, on `bedrock:InvokeModel*`. This is the
    belt to 7.5's braces and it goes stale in the safe direction: a new retaining model is not on the
    list and is caught by the mode deny instead.

  **Decision due 4** is which document carries them — `awsds-org-scp-baseline.json`, which reaches every
  account, or `awsds-org-scp-ou-interactive.json`, which reaches only where invocation happens.
  **Recommended: baseline.** The statement's value is that it holds where nobody is looking.
  Per the standing rule, the battery is re-run and `POLICIES.md` gains its rows in the same sitting
  ([`scp-battery.md`](../runbooks/scp-battery.md)).

- **7.6 — The residuals, stated rather than closed.** None of these is a defect in the design; each
  is a place where the requirement's boundary is the operator rather than the perimeter.
  - **The transcript is a local plaintext copy.** Claude Code writes session transcripts to
    `~/.claude/projects/` on the machine it runs on, for 30 days by default (`cleanupPeriodDays`). In a
    space that is the EBS volume — inside the estate, encrypted — and it is still a copy of whatever the
    model was shown, in a place no Lake Formation grant governs (Lesson 1).
  - **The remote session is a file channel the plane cannot see.** `remote-ide.md` §N already records it:
    a file crosses in either direction inside the data channel, no name reaches Squid, no query reaches
    the DNS Firewall. A transcript is a file. This stage adds a reason to care about a channel Stage 11
    already owns.
  - **ZDR is about persistence, not about reading.** The model is handed whatever the operator and the
    project role can reach, and in a Sandbox space that includes the governed lake. Bedrock guarantees
    the content is not stored outside and not readable by anyone outside; it guarantees nothing about
    what the operator chose to put in the prompt. **That is the control the institution exercises through
    people and policy**, and it belongs in Stage 11's threat model with its own accepted-risk row.

### 8. Cost, and the ceiling this estate actually has

**Action:** measure a session, then decide whether the assistant fits.
**Why:** the rates are measured (0.4) and the volume is not, and the volume is the number that decides.
**Explanation:** this is the first thing in the estate that bills **per use with no ceiling** — an idle
space costs its instance, an idle endpoint costs 0.010/h, and an idle assistant costs nothing while a
busy one has no upper bound at all. `make down` does not reach it.

- **8.1 — [Claude] The arithmetic that matters, from 6.4's reading.** Output at **27.50/1M** is five times
  input and fifty times cache read; a session's bill is dominated by output tokens and by cache misses.
  Do not estimate it here (Lesson 6, and Lesson 7 — a rejected-on-cost option goes stale in the direction
  that flatters the rejection). Read one real session, write the number down with its date, and decide
  against that.
- **8.2 — The endpoint cost is separate and known.** Two interface endpoints at ~USD 0.010/h each add
  **~0.020/h** to the Sandbox `[E]` set while `sandbox/egress` is up, moving the estate's fixed rate
  from 0.390/h to 0.410/h. They go away with `make down`.
- **8.3 — [Claude reads, user decides] The alarm, and the deferral it collides with.** D12 left the
  USD 50 budget notifying **nobody**, and that deferral was taken when nothing in the estate could spend
  quickly. This can. **Decision due 5:** either close D12's deferral here — a budget notification with a
  real subscriber — or accept a manual daily read for the first week and name the date it is revisited.
  Recommended: close it. A per-use service with no ceiling and no notification is the shape of the
  invoice nobody sees coming.
- **8.4 — [Claude] Attribute the spend.** Invocation logging is off, so `identity.arn` grouping is not
  available; the attribution instruments that remain are CloudTrail's `userIdentity` per event and
  Cost Explorer by usage type. Per-request metadata tagging exists and needs a caller that sets it,
  which this client does not.

### 9. Close

- **9.1 — [Claude] `docs/PRICING.md`.** Correct §5: the offer code for modern Claude models is
  **`AmazonBedrockFoundationModels`**, and the existing table's two Claude rows are legacy in-region SKUs
  that no current model uses. Add 0.4's table, dated.
- **9.2 — [Claude] `docs/NETWORK.md`.** Two endpoints, the new `bedrock-llm` group, the `NO_PROXY` count,
  and the fact that the Bedrock name is on the compute plane's allow-list *and* on the bypass list —
  which is not a contradiction but is the kind of sentence a later reader has to be told once.
  `./scripts/check-network-doc.py` is the mechanical half.
- **9.3 — [Claude] `POLICIES.md`**, one row per new `Sid`, in the sitting that attaches them (7.5).
- **9.4 — [Claude] `docs/AWS_STATE.md`**, the residency exception of 7.3 and the retention reading of 7.2,
  both dated, so a later snapshot that shows a three-region profile is recognised as expected.
- **9.5 — [Claude] `docs/REFERENCES.md`**, the vendor pages this stage was written from.
- **9.6 — [Claude] A runbook**, `docs/plan/runbooks/bedrock-assistant.md`, if and only if step 6 produced
  something a second operator would get wrong. If it did not, this file is enough.

---

## Verifications

| | Question | Answered by |
|---|---|---|
| (i) | Does the form exist, and did it change anything? | 2.3, against 0.3 |
| (ii) | Can the principal of step 1 invoke Opus 5, measured by a call rather than by a policy read? | 6.3 |
| (iii) | Does the invocation carry `vpcEndpointId`? | 4.5, 6.3 |
| (iv) | Is the proxy access log silent on `bedrock-runtime` for the same window? | 4.5's negative control |
| (v) | Does a session reach **no** Anthropic host? | 6.2 |
| (vi) | What is Opus 5's `allowed_modes`, on the day it is read? | 7.2 |
| (vii) | Is the account's retention mode `none`, and can anyone change it? | 7.2 and 7.5 |
| (viii) | Does the CloudTrail record carry the prompt? | 4.6 — it must not |
| (ix) | What does one session cost? | 6.4, 8.1 |
| (x) | Does the configuration survive a new space? | a second space from `default-v0.3.0`, after 5.4 |

## Decisions due

| | Question | Recommendation |
|---|---|---|
| **1** | Where the assistant runs | the space (step 1) |
| **2** | Where the model-access form is submitted | `Sandbox` alone, not org-wide from Management (2.1) |
| **3** | Whether `availableModels` locks the picker to the pinned models | yes — an unpinned model is a model outside step 2's declared use case and outside step 3's resource scope |
| **4** | Which policy document carries the retention denies | `awsds-org-scp-baseline.json` (7.5) |
| **5** | Model invocation logging on or off | off now, revisited at Stage 11 step 3 (7.4) |
| **6** | Whether D12's budget deferral closes here | yes (8.3) |

## What the documentation changed

Each row corrected something a plan written from familiarity would have got wrong.

| Read | What it corrected |
|---|---|
| `inferenceTypesSupported ["INFERENCE_PROFILE"]` (0.1) | there is no on-demand Opus 5; a request naming `anthropic.claude-opus-5` fails |
| the profile's three model ARNs (0.2) | the estate's first resource that cannot be pinned to `us-west-2` |
| `AmazonBedrockFoundationModels` (0.4) | `docs/PRICING.md` §5 had read the wrong offer file since 2026-08-21, which is why its Claude rows are legacy SKUs |
| *"Access is granted immediately after submission"* | the form is a declaration, not an approval queue — nothing waits on AWS |
| the abuse-detection page's model list | ZDR is Bedrock's default and the exceptions are **per model**, so the answer to the requirement is a measurement (7.2), not a property of the service |
| `InvokeModel*` logged as a **management event** | attribution arrives for free on the existing organization trail, with no data-event charge and no prompt content |
| the small/fast model defaults to **Sonnet** on Bedrock (5.3) | a model this estate never named gets invoked unless something names it — and it must be inside step 2's form and step 3's scope |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` vs the survey | metrics, error reports and `/feedback` are already off on Bedrock; the session-quality survey is **not**, and is the only Anthropic-bound traffic left to close |
| `skipWebFetchPreflight` | the WebFetch hostname check calls `api.anthropic.com` **regardless of provider** and is not covered by the variable above |
| `/etc/claude-code/managed-settings.json` | the configuration has a home that a user cannot override and the image can write — 6d decision 8's shape, with a file made for it |
| `AWS_BEARER_TOKEN_BEDROCK` | a long-lived credential, refused by principle 2 before it is weighed (5.1) |

---

*Stage index: [`docs/plan/stages/INDEX.md`](INDEX.md) · Plan core:
[`GENERAL_PLAN.md`](../../GENERAL_PLAN.md) · The channel this runs inside:
[`remote-ide.md`](../runbooks/remote-ide.md)*
