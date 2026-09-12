# Stage 6e — Claude Code on Bedrock, inside the remote IDE

| | |
|---|---|
| **Status** | **In progress since 2026-09-11**, and its decisions were taken before it started. **Step 2 is done** — the form submitted by console 2026-09-11, verification (i) closed — and so is **7.5a**, the account's retention mode set to `none` at 22:31 UTC with the scoped set still available under it. **Step 3 is done**: `sandbox/bedrock/` (rank 52, `[P]`) applied the same day — one policy and one attachment, re-plan `No changes`, the project role now carrying four policies. Steps 4 and 5 stand between here and a call. Done before those: the read-only steps **2.4**, **3.1** and the half of **7.2** that has an instrument, with 0.3, 0.5 and 0.7 re-read the same day ([`log-stage-06e`](../../log/log-stage-06e-claude-code-bedrock.md)). What they changed is at the steps that own them: **a grant is needed** (3.1 closes the first half of open question 8), the account's retention mode reads **`inherit`** rather than `none` (7.2), the per-model `allowed_modes` has **no API at all** (7.2), and the retention mode has **no Terraform resource and no CloudFormation type** while the use-case form has both (7.5, step 2). Neither IAM simulator can answer this question. Written 2026-09-11 against the vendor documentation and eight read-only measurements taken the same day in `Sandbox` (step 0). The stage exists because [6d](stage-06d-unified-studio-remainder.md) step 7 opened the remote IDE and the user installed the *Claude Code for VS Code* extension in it, whose first act was `api.anthropic.com` — refused by the compute plane, `403 TCP_DENIED` × 17 ([`remote-ide.md`](../runbooks/remote-ide.md) §N). This stage replaces that refused call with a call to Amazon Bedrock inside the estate's own perimeter. **Settled by the user the same day, before execution**: the assistant runs **in the space** (a laptop's VS Code over a remote session is the same answer, measured); the model-access form is submitted in **`Sandbox` alone**; `availableModels` **locks** the picker; the retention denies go in **`awsds-org-scp-baseline.json`**; model invocation logging **stays off and the question moves to [Stage 11](stage-11-dlp.md) step 5.6**, written there rather than only here (Lesson 34). The scoped set is **Opus 5, Sonnet 5 and Haiku 4.5**, with **Haiku pinned for background work** — which caught a defect in this file's first draft: a session that sets `ANTHROPIC_MODEL` runs session titles on the primary model, so the draft would have billed them at the Opus rate (5.3) |
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
  **Re-read 2026-09-11 across the scoped set**: Sonnet 5 and Haiku 4.5 are `INFERENCE_PROFILE` only
  too, and `get-inference-profile` returns `ACTIVE`, `SYSTEM_DEFINED` and the **same three model
  ARNs — us-east-1, us-east-2, us-west-2** — for all three `us.` profiles. 7.3's residency
  qualification is the set's, not Opus 5's.
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
  interactive assistant can use it. Sonnet 5 and Haiku 4.5 were read from the same file on the same day
  and are in step 8.1's table, beside the Sonnet 4.5 rate that decides how much 5.3's pin is worth.
  **Confirmed 2026-09-11 against a second source**: `list-foundation-model-agreement-offers` carries
  a rate card per model, and every figure matches. It also corrects one clause above — a batch tier
  exists on the **`us.` profile as well** (Opus 5 `2.75 / 13.75`), and an interactive assistant can
  use neither.
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
- **0.9 — `get-foundation-model-availability` reads permissive with no form submitted.** All three
  scoped models return `authorizationStatus AUTHORIZED`, `entitlementAvailability AVAILABLE` and
  `regionAvailability AVAILABLE`, with `agreementAvailability.status NOT_AVAILABLE`, while 0.3 holds.
  It is not the instrument for 2.3, and a later reader meeting it should not take it for access.
  **Read three times across two state changes** — before, after the retention mode went to `none`, and
  after the form was submitted — and identical every time.

---

## To execute

### 1. Where the assistant runs — the space

**Action:** pick the machine the `claude` process runs on. **Why:** it decides the principal, the
network path, the perimeter and the blast radius, and every later step reads differently on each side.
**Explanation:** the extension bundles its own copy of the CLI and spawns it; in a Remote-SSH session the
extension installs on the **remote** side, so *"install Claude Code"* means a different thing depending
on which of `remote-ide.md` §E's two surfaces the install happened in.

**Taken 2026-09-11 by the user: the space.** The user also named *VS Code on the laptop, attached to the
space over a remote session* — **that is the same answer, not a second one**, and the estate has already
measured it rather than inferred it. The extension the user installed on 2026-09-11 was installed into
the remote session, and its first outbound call reached `api.anthropic.com` **from the space's own
address**, which is why the proxy refused it (`remote-ide.md` §N). The `claude` process runs where the
workspace is either way. What the laptop keeps is the editor, the keyboard and one setting that has no
remote half (step 5.5).

| | The space | The laptop |
|---|---|---|
| principal | the project role, `datazone_usr_role_<project>_<env>` | the persona, `awsds-scientist-sandbox` |
| credential | ambient, vended by the container | SSO, cached by the profile |
| network | the compute plane, and a VPC endpoint if step 4 builds one | the client plane, `open`, through the proxy |
| what the model can read | the space's filesystem and whatever the project role reaches — the lake included, through Lake Formation | the laptop's checkout |
| what a prompt can contain | governed data | whatever the laptop already holds |

The reason for the choice: the work is there, the perimeter is there, and an assistant running on the
laptop moves the interesting half of the problem outside every control this estate has. **An assistant on
the laptop is a separate question with a separate answer**, and nothing below is written for it.

### 2. Submit the model-access form

**Action:** submit the Bedrock use-case form once, in the account that will invoke.
**Why:** step 0.3 measured that it has never been submitted, and Anthropic models refuse the first
invocation without it. **Explanation:** the vendor calls this *"submit use case details"* and it is not
an approval queue — **access is granted immediately after submission**. Nobody reviews the answer before
the model works; the answer is a declaration on the record, which is why it is worth writing carefully
rather than quickly.

- **2.1 — Where to submit it: `Sandbox` alone** (taken 2026-09-11 by the user). The two shapes are not
  equivalent:
  - **In `Sandbox` alone**, from the Bedrock console's Model catalog, as the infrastructure user. Access
    covers that account and no other.
  - **Once from `Management`**, through `PutUseCaseForModelAccess`, which the vendor documents as
    extending *"to child accounts automatically"*.

  The reason: principle 1 keeps the Management account bootstrap-only, and an org-wide grant would open
  Anthropic models in `Staging`, `Production`, `Data`, `Audit` and `Log Archive` — every account where
  D17 says no interactive compute runs and where nothing has asked for a model. The org-wide form is the
  right shape the day a second account needs one, and the cost of deferring it is one more form.

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

- **2.3 — Read it back. Done 2026-09-11.** `get-use-case-for-model-access` stopped returning
  `ResourceNotFoundException` and returns a `formData` blob — the whole verification, with 0.3 as its
  negative control. **The blob is double base64 over a flat JSON object of the six fields**, so the
  record is readable after all; the submitted `useCases` reads narrower than 2.2's text and the user
  chose to keep it as submitted, reading the leading `". "` as an artefact of the console's own form.
  A re-submission is a `Put` and costs nothing if the wording is revisited.

- **2.4 — `InfrastructureAccess` can submit it, on or off the VPN. Read 2026-09-11.** In Sandbox the
  set carries `AdministratorAccess` and nothing else — no inline document, no permissions boundary —
  so `bedrock:PutUseCaseForModelAccess` is covered, and 0.6 holds against the ten policy documents.
  **It does not carry `DenyControlPlaneOffVpn`**: that fragment's `for_each` is the six persona sets,
  and this is the imported seventh. The console submission therefore works from any network.

- **2.5 — The form is a Terraform resource, and its one field is opaque.**
  `aws_bedrock_use_case_for_model_access` exists in `hashicorp/aws` 6.60.0 with a single required
  attribute, `form_data (string)`; the API takes `formData` as a **blob** on both `Put` and `Get`.
  So the six answers above would reach the code and every diff as base64, and the console keeps them
  legible. **Decision due 10:** submit by console and record the answers in the log (recommended), or
  adopt the resource and lose the reviewable form. The resource is worth knowing about either way —
  it means an org-wide form at the day 2.1 defers to has an authored shape.

### 3. Give the principal the reach, and find out whether it already has it

**Action:** establish that the caller of step 1's choice can invoke the three scoped models, and grant
what is missing. **Why:** the project role is authored by a blueprint (D26), not by this repository, so
*granting* is a different problem from *bounding* — INT-15 solved the second with
`environment_role_permission_boundary` and says nothing about the first. **Explanation:** reach is an
intersection (Lesson 28): the identity policy, the boundary, the SCPs and — here — the endpoint policy of
step 4 all have to agree.

**The scoped model set, settled 2026-09-11 by the user.** Three models, each with a job, all three
`ACTIVE` as `us.` profiles in `Sandbox` and all three **inference-profile only** — none is invocable by
its bare model id:

| Job | Model | `us.` profile |
|---|---|---|
| the primary model | Claude Opus 5 | `us.anthropic.claude-opus-5` |
| the cheaper alternative in the picker | Claude Sonnet 5 | `us.anthropic.claude-sonnet-5` |
| background tasks | Claude Haiku 4.5 | `us.anthropic.claude-haiku-4-5-20251001-v1:0` |

**The set is one list with four consumers** and they drift apart the moment one is edited alone
(Lesson 14): 3.3's resource scope, 4.4's endpoint policy, 5.2's pins and `availableModels`, and 7.5's
deny list, which must not catch any of the three.

- **3.1 — The role holds the foundation-model half and none of the profile half, so a grant is
  needed. Read 2026-09-11**, and it closes the first half of open question 8. The role carries three
  AWS-managed policies, no inline document, the D13 boundary, and the tag
  `EnableAmazonBedrockPermissions=true` — while **`EnableAmazonBedrockIDEPermissions` is absent**.
  Matching every `Allow` against the two ARNs a scoped invocation names:

  | Action | `inference-profile/us.anthropic.*` | `foundation-model/anthropic.*` |
  |---|---|---|
  | `InvokeModel`, `InvokeModelWithResponseStream` | **nothing matches** | `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy/BedrockModelInvocationPermission`, no principal-tag gate, conditioned only on a profile ARN being present |
  | `GetInferenceProfile` | **nothing matches** — every statement is scoped to `application-inference-profile/*` | — |
  | `ListInferenceProfiles` | **granted nowhere** | — |

  The two statements that look like they serve do not: `InvokeBRModel` requires the IDE tag the role
  does not carry, and `BedrockInvokeModelPermissions` requires the profile ARN to be `ArnLike` an
  **application** inference profile, a different resource type from the system-defined one. So the
  `Tooling` template's conditional Bedrock grants are real and land on the wrong resource for a model
  that is invocable only through a system profile (0.1, 0.2).

  **The boundary is not the constraint**: nine statements, ceiling `Allow * on *`, and no `bedrock:`
  action — 0.7 confirmed by reading rather than carried forward.

- **3.1a — Neither IAM simulator can answer this, and one of them answers wrongly.**
  `simulate-principal-policy` from Sandbox returned `explicitDeny` with
  `AllowedByOrganizations false` for `bedrock:InvokeModel*`; the negative control is
  `glue:GetDatabases`, which this role performs in the portal daily and which comes back identically,
  while `sts:GetCallerIdentity` comes back `allowed / true`. **Its organization verdict is unusable
  from a member account, and the top-level decision inherits it** (Lesson 30).
  `simulate-custom-policy` caps each input policy at **2,000 characters** against SMUS documents of
  4,720 and 54,912 bytes, so the identity layer cannot be isolated either. And the role's trust
  policy admits only service principals and `awsds-sandbox-smus-provisioning`, so
  `InfrastructureAccess` cannot produce the principal: **3.1 is a reading, and 3.4's rule stands —
  the proof is step 6's call** (Lesson 22).
- **3.2 — [Claude] The minimum the client needs.** The vendor's policy is four actions plus a
  marketplace pair:

  ```
  bedrock:InvokeModel
  bedrock:InvokeModelWithResponseStream
  bedrock:ListInferenceProfiles
  bedrock:GetInferenceProfile
  ```

  **3.1 measured which of the four the role is missing: all but the `foundation-model` half of the
  two invoke actions.** `ListInferenceProfiles` is what lets the client resolve `opus` to a profile
  that exists in this account instead of guessing; without `GetInferenceProfile` the client recovers by retrying with the
  other request shape, so the cost of omitting it is a round-trip and not a failure. The vendor also
  asks for `aws-marketplace:ViewSubscriptions` and `aws-marketplace:Subscribe` under
  `aws:CalledViaLast = bedrock.amazonaws.com`. **Measure whether they are needed here** before adding
  them: the account reaches these models through the use-case form of step 2, and a `Subscribe` this
  estate never needs is a permission granted for a vendor sentence rather than for a call (Lesson 41).
- **3.3 — [Claude] Scope the resource, not just the action.** `Resource` is the profile ARNs of the three
  scoped models and the foundation-model ARNs they route to, never `*`:

  ```
  arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-opus-5
  arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-sonnet-5
  arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0
  arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-5
  arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-5
  arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0
  ```

  An inference profile is an account resource and the foundation model is not, which is why the second
  group has no account field. Both are needed: authorization is evaluated against the profile *and*
  against each model it routes to. **The foundation-model ARN carries no region** on purpose — the
  profile routes to three of them (0.2), so a region-pinned ARN would authorize a third of the requests
  and refuse the rest, intermittently and by geography.

  **The document drafted from this shape validates clean**: `accessanalyzer validate-policy
  --policy-type IDENTITY_POLICY` returned zero findings over the six ARNs above for `InvokeModel*`,
  the three profile ARNs for `GetInferenceProfile`, and `ListInferenceProfiles` on `*`
  (2026-09-11). Validation is syntax and key names, not reach; the call is still step 6's.
  **Both ARN groups are now built from one map** in `sandbox/bedrock/`'s `models` variable, so the
  two lists cannot disagree about which models are scoped — which is the failure a hand-kept pair
  of lists has (Lesson 51).
- **3.4 — [Claude reads, user decides] Where the grant lives. 3.1 says one is needed.**

  **The blueprint gives a ceiling for every project role and a floor for none.** Measured 2026-09-11
  from the provider schema: `awscc_datazone_environment_blueprint_configuration` carries fourteen
  attributes and exactly one is policy-shaped — `environment_role_permission_boundary`, which is how
  INT-15 imposes D13 — and a boundary only subtracts. `provisioning_configurations` holds Lake
  Formation location registration and nothing else. **So there is no lever that grants to the project
  roles a blueprint creates**, and the shape that would have reached every project in the domain at
  once does not exist to be chosen or refused.

  What is left:

  | | Where the grant lives | Blast radius | What it costs |
  |---|---|---|---|
  | **(a)** | the blueprint's own template | every project | ruled out by 3.1: its grants land on `foundation-model/*` and none on the system profile |
  | **(b)** | a policy attached to the project role, named by Terraform | exactly the roles named | the role is the service's and is created *after* the slice; a new project needs a new attachment (Lesson 14), and the missing one is a refusal mid-session. A blueprint reconciliation may remove it — INT-15's open half |
  | **(c)** | a role **this repository authors**, reached by `awsCredentialExport` in the managed settings; its trust policy names the project roles allowed | exactly what the trust policy lists | an extra moving part in the image, and one thing to measure first: whether a same-account `sts:AssumeRole` needs an identity grant on the project role or the trust policy alone suffices |

  (c) is the only one where *which projects* is a value this repository writes rather than a
  consequence of where the attachment happened to land, and the only one whose grant sits on a
  principal no blueprint reconciles. It also gives cost attribution a dedicated principal, which 8.4
  says CloudTrail's `userIdentity` is otherwise the only instrument for.

  **Taken 2026-09-11 by the user: (b).** One line decided it against (c)'s advantages: in (c) the
  caller is a principal **outside `awsds-sandbox-project-boundary`**, and every other interactive
  call in this account is inside it. Buying "which projects is a list we write" with "the model is
  invoked from outside D13" is the wrong trade while there is one project. **(c) is recorded as the
  shape to adopt at Stage 14**, when per-business-unit vending makes *which projects* stop being
  trivial — and it carries one thing to measure first, which (b) does not have to ask at all:
  whether a same-account `sts:AssumeRole` needs an identity grant on the calling role or the trust
  policy alone suffices.

  **The slice is [`terraform-live/sandbox/bedrock/`](../../../terraform-live/sandbox/bedrock)**,
  rank 52, `[P]`: one `awsds-<env>-bedrock-assistant` policy and one attachment per entry in
  `project_roles`. The role names are hand-written after a project exists, which is Lesson 14's
  cost accepted rather than avoided — and the attachment carries a **precondition that the role is
  under the D13 boundary**, because a hand-written name matching the pattern is the one way this
  could silently grant Bedrock to a principal outside the ceiling the decision was taken to keep.
  The procedure, in both the Terraform and the `aws` CLI form, is
  [`claude-code-sagemaker.md`](../runbooks/claude-code-sagemaker.md) **§P**.

  **Whatever is chosen, the step that proves it is a call, not a `get-role`.**

### 4. Put the call on the private path

**Action:** make `bedrock-runtime.us-west-2.amazonaws.com` resolve to an interface endpoint inside the
Sandbox VPC, and keep it out of the proxy. **Why:** step 0.8 measured that the call works today and
arrives *public*. **Explanation:** the perimeter conditions this estate writes — `aws:SourceVpc` and
`aws:SourceVpce` — are absent on a call that leaves through Squid, so a Bedrock invocation made now is
outside the data perimeter while looking exactly like one that is inside it.

- **4.1 — Done, and the answer is not a group. `vpc-egress-v0.14.0`.** A new optional endpoint group,
  narrower than the one that exists — **withdrawn 2026-09-12 by the user, and the reason is the
  flag's own semantics**: a group is per apply, `make up` without it destroys what it created, and
  the assistant needs this path in every session a space runs. A permanent consumer cannot live
  behind a per-apply flag.

  So `bedrock` and `bedrock-runtime` are in `sandbox/egress`'s **always-on** `extra_services`, and
  the optional `bedrock` group narrows to what only the blueprints use, `bedrock-agent` and
  `bedrock-agent-runtime`. The restructure also dissolves a guard: `bedrock` and `bedrock-llm`
  shared two endpoints and could not be named together (`v0.13.0`), and with the shared pair moved
  out there is nothing left to collide. **One seam it introduces**, named in the module: a caller
  that does not carry the pair gets two agent endpoints with no control plane to talk to.

  **The cost is now permanent while the slice is up**, not per apply: Sandbox moves from 18
  endpoints to 20, and the estate's fixed rate from 0.390 to 0.410 USD/h. It still leaves on
  `make down`. *Superseded text:*
  `terraform-modules/vpc-egress`'s `bedrock` group is four endpoints — `bedrock`, `bedrock-agent`,
  `bedrock-agent-runtime`, `bedrock-runtime` — sized for the portal's blueprints. This stage needs
  **two**: `bedrock-runtime` for the invocation and `bedrock` for the control-plane calls of 3.2. Add
  `bedrock-llm = ["bedrock", "bedrock-runtime"]` beside it rather than narrowing the existing group,
  which has a different consumer, and extend the `optional_service_groups` validation to admit the name.
  **Two tags followed, not one**, by the two-commit order in
  [`terraform-changes.md`](../runbooks/terraform-changes.md): `v0.12.0` carries the group and the
  action scope of 4.4, and `v0.13.0` carries a guard found while writing the caller — **`bedrock`
  and `bedrock-llm` cannot be named together**. They are two configurations of one door rather than
  two doors: both contain `bedrock` and `bedrock-runtime`, the map key collapses the overlap to one
  endpoint, and one endpoint carries one policy, so 4.4's action list would have reached the
  blueprints' control-plane calls and refused `CreateGuardrail` with no denial naming it. A tag is
  never moved, so the fix is a second version rather than an amendment (Lesson 46's rule, applied
  before it cost anything).
- **4.2 — [Claude⚡] Bring it up.** `make up ENV=sandbox` — **no flag**, since 4.1 made the pair
  always-on. Two endpoints at ~USD 0.010/h each on top of the eighteen, `[E]`, and they leave on the
  next `make down` like everything else. **Not done**: the apply is owed.
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
- **4.4 — Done, and this step's premise was wrong.** It said the endpoint's *default* policy allows
  every Bedrock action to every principal. **These endpoints have never carried the default**:
  `vpc-egress` has applied the trusted-networks document to every interface endpoint since Stage 3
  step 9 — organization principals and AWS service principals, nobody else. Read the module before
  writing what a control does (Lesson 30's neighbour).

  What `v0.12.0` adds is `endpoint_action_scopes`, a narrowing of that document **on the action
  axis** for a named endpoint. **4.1's restructure changed what it should be used on.** While the
  two endpoints belonged to an assistant-only group, scoping both was safe; as always-on
  infrastructure they are shared with the six SMUS `AmazonBedrock*` blueprints, and a list written
  for one consumer silently refuses the other with no denial naming the policy (Lesson 51).

  So `sandbox/egress/` scopes **`bedrock-runtime` only**, to the two invoke actions. That door
  carries invocation for every consumer, so the list is a statement about the service rather than
  about one caller, and a future runtime API does not silently acquire it. **`bedrock` keeps
  `Action = "*"`** under the organization condition, like the other nineteen.

  **What that gives up, stated rather than discovered later**: `PutAccountDataRetention` and
  `PutModelInvocationLoggingConfiguration` are control-plane calls and still traverse their
  endpoint. The first is covered org-wide by 7.5's SCP, which is the right layer for it; the second
  is [Stage 11](stage-11-dlp.md) step 5.6's question and has no control here yet.

  **The resource axis is deliberately not narrowed, reversing what this step used to ask for.**
  Scoping the endpoint to the six model ARNs would be a second copy of the grant's list, in another
  slice, with nothing comparing them — one intent in two places, which diverges (Lesson 33) — and
  the failure would be an invocation refused at the network layer for a model somebody had properly
  added to the grant. The action list has no such problem: it is a property of the service, and it
  changes when AWS adds an API rather than when a decision is taken here.

  An action absent from the list gets **no response and no denial naming this policy**, so an
  addition belongs with a measured refusal rather than with a guess.
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
      "ANTHROPIC_DEFAULT_SONNET_MODEL": "us.anthropic.claude-sonnet-5",
      "ANTHROPIC_DEFAULT_HAIKU_MODEL": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
      "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
    },
    "availableModels": ["opus", "sonnet"],
    "skipWebFetchPreflight": true
  }
  ```

  `ANTHROPIC_MODEL` pins the session's model; the three `ANTHROPIC_DEFAULT_*_MODEL` keys pin what each
  alias resolves to, so a later default change in the client does not silently move this estate onto
  another model. **Pinning is not cosmetic**: without it an alias resolves to the client's built-in
  default, which changes with the client version. `availableModels` is the lock, set 2026-09-11 by the
  user: it constrains `/model`, `--model` and the `model` key in a user's own file, so nothing outside
  step 2's declared use case and step 3's resource scope is reachable from the picker. **Verify the
  entries rather than trusting this block** — the list is matched against what the picker offers, and
  `/model` at the first session is the instrument.
- **5.3 — The background model is a pin, and leaving it out was a defect in this plan.** Background work
  — session titles and the like — runs on the small/fast model, and on Bedrock that is **the default
  Sonnet** rather than a Haiku, because Haiku may not be enabled in every account. **But a selected
  primary model overrides that**: the vendor states that when a session sets `ANTHROPIC_MODEL`,
  background tasks use *that* model. So 5.2's block **without** `ANTHROPIC_DEFAULT_HAIKU_MODEL` would
  have run session titles on **Opus 5**, at 27.50 per 1M output tokens, for work a Haiku does.

  **Taken 2026-09-11 by the user: Haiku 4.5.** `ANTHROPIC_DEFAULT_HAIKU_MODEL` is the only key that
  moves background work to a Haiku-class model, and the rates make the size of the mistake it repairs
  visible — Haiku 4.5 is **1.10 / 5.50** against Opus 5's **5.50 / 27.50** and against the Sonnet 4.5
  default's **3.30 / 16.50** (step 8's table). The model is `ACTIVE` as a `us.` profile in `Sandbox` and
  is in step 3.3's scope, **which is the half that fails loudly if it is forgotten**: an unscoped
  background model is a refusal in the middle of a working session rather than a wrong bill.
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
  **WebSearch is not available at all on Bedrock**, so no search host can appear either; `/logout` is
  likewise unavailable, authentication being the container's AWS credentials.
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

- **7.2 — The account has declared nothing, and the per-model reading has no API. Read 2026-09-11.**
  `get-account-data-retention` returns `{"mode": "inherit"}` with no `updatedAt`: it has never been
  set. The enum, from the service model the CLI ships:

  | mode | what the API documents |
  |---|---|
  | `default` | the standard data handling **for the model** applies |
  | `none` | zero data retention |
  | `provider_data_share` | data may be shared with the model provider |
  | `inherit` | **no data retention mode is set at this scope** |

  So the requirement rests today on the per-model default and on nothing this estate has stated —
  Lesson 5's shape exactly, and the reason 7.5 gains a step it did not have.

  **`allowed_modes` is not in the Bedrock API, and neither is the effect of setting the mode.** The
  field is absent from `get-foundation-model`, `list-foundation-models`,
  `get-foundation-model-availability` and `list-foundation-model-agreement-offers` — whose
  `termDetails` carries pricing, legal and support terms and nothing about retention — and no shape
  matching `allowed` exists in any of the eight `bedrock*` service models the CLI ships
  (`aws-cli/2.36.18`). **Measured 2026-09-11 with the account already at `none`: all thirteen Anthropic
  models in `us-west-2` read `AUTHORIZED / AVAILABLE / AVAILABLE`, `claude-fable-5` and
  `claude-fable-5-1` among them** — the two the vendor names as retaining every prompt for 30 days with
  human review. So this step's claim that such a model becomes *unavailable* rather than quietly
  retaining is **unverified, by an instrument that would not have shown it either way** (Lesson 62).
  Where `none` bites is presumed to be the invocation, and nobody here has seen it. **7.2a is the step
  that would.** The
  load-bearing half of this step is a vendor-page or console reading, dated when it is taken — which
  makes 7.1's third statement decay with nothing watching it, and makes the **mode deny of 7.5 the
  only mechanical guard**. A model whose minimum is `aws_review` is then **unavailable** rather than
  quietly retaining, which is the failure mode to want.

- **7.2a — [Claude reads, user decides] A negative control for `mode: none`, which nothing else
  provides.** Invoke a model the vendor names as retaining — `us.anthropic.claude-fable-5` — and read
  the refusal. A refused call costs no tokens, and the two outcomes are both worth having: a refusal
  naming the retention mode proves the account setting is enforced where it matters, and a **success**
  is a finding of the first order, because it would mean `none` is a label on an API and not a control.
  It runs as the infrastructure user, not as the project role: the scoped grant of step 3 names three
  profiles and Fable is not among them, so the probe must not be widened into the grant. **Decision due
  11:** run it, or accept the vendor's sentence and record the acceptance with its date.

- **7.3 — The residency qualification, which no setting removes.** `us.anthropic.claude-opus-5` routes to
  **us-east-1, us-east-2 and us-west-2** (0.2). A prompt is therefore *processed* outside `us-west-2`
  some of the time, inside AWS, over AWS's network. Under ZDR nothing is stored there — the abuse-detection
  page's residency sentence, *"retained inputs and outputs are stored in destination regions"*, is about
  models that retain, and Opus 5 does not. What remains is a transit fact, and it is real: **D1 says the
  region is a variable, and this is the estate's first resource that cannot honour it.** There is no
  narrower option — 0.1 makes the bare model id uninvocable and `global.` routes wider — so the choice is
  `us.`, at a 10% premium (0.4), recorded as a named exception in `docs/AWS_STATE.md` rather than left
  for a later reader to discover.

- **7.4 — Model invocation logging stays off here, and the question moves to Stage 11** (taken
  2026-09-11 by the user). It is off (0.5). Turning it on writes **the full prompt and the full
  completion** to an S3 bucket or a CloudWatch log group **in this account** — inside the private cloud,
  which is what the requirement permits, and durable, which is what the requirement was written against.
  The trade is exact:
  - **on** buys `objectives.md`'s fourth DLP problem, exfiltration detection, on the one channel where a
    model sees governed data. It costs a durable copy of every prompt, which becomes a Macie subject at
    Stage 11 and a retention obligation at Stage 12.
  - **off** keeps 4.6's property — attribution without content — and leaves the assistant channel
    invisible to content inspection.

  The reason is not cost: turning it on creates the exact artefact the requirement is about, and doing
  that before the threat model exists decides the question in the wrong order. **The obligation is
  written into [Stage 11](stage-11-dlp.md) step 5.6 and its decision list, not only here** — a deferral
  recorded at the deferring end is a promise the receiving stage never gets (Lesson 34). That step
  carries what this one would have had to invent: the CMK, the lifecycle, the Macie scope and the
  trail's own retention are already decided there for the buckets beside it.

- **7.5 — [Claude] Turn the default into a control.** 7.2 measured that the account reads `inherit`,
  so this step gained a prerequisite it did not have: **the mode has to be set before it is frozen**,
  and the deny alone leaves the account declaring nothing.
  - **7.5a — [Claude⚡] Set the account's mode to `none`.** `put-account-data-retention --mode none`,
    one call, in `Sandbox`. It is a write, and it is what turns the vendor's default into this
    account's own statement. **It has no Terraform resource and no CloudFormation type** — nine
    `aws_bedrock_*` resources in `hashicorp/aws` 6.60.0 and 29 `AWS::Bedrock::*` registry types,
    none an account setting, so `awscc` offers nothing either (Lesson 8 checked, 2026-09-11). It
    joins account-level BPA on the standing list of settings this estate manages by hand, with the
    SCP below as the thing that keeps it there.
  - **The condition key exists, measured.** `accessanalyzer validate-policy` accepted a statement
    conditioned on `bedrock:DataRetentionMode` and rejected the one beside it conditioned on
    `bedrock:NoSuchConditionKeyAtAll` (`INVALID_SERVICE_CONDITION_KEY`), so the silence on the real
    key is a reading rather than an absence (2026-09-11). It establishes the key is in the service's
    catalogue, not that `PutAccountDataRetention` publishes it at request time — that is the
    battery's, in `Policy Canary`.
  - **Deny any retention mode but `none`.** The write actions publish a `bedrock:DataRetentionMode`
    condition key, so a deny on `bedrock:PutAccountDataRetention` where the mode is not `none` makes it
    impossible for anyone in the organization to opt this estate into retention — including by accident,
    including in an account nobody is watching. A model that then requires `aws_review` becomes
    **unavailable** rather than quietly retaining, which is the failure mode to want.
  - **Deny the models that require retention**, by name, on `bedrock:InvokeModel*`. **Measured
    2026-09-11: the two are `anthropic.claude-fable-5` and `anthropic.claude-fable-5-1`, both present
    in `us-west-2` and both reading available** — so this is written against model ids rather than
    against a vendor page. It stopped being belt to 7.5's braces the moment 7.2 found that nothing
    reads the mode's effect: **a deny is the only half of this pair the battery can prove**. It goes
    stale in the safe direction: a new retaining model is not on the
    list and is caught by the mode deny instead. **It must not catch step 3's three models** — write it
    as a deny on the named retaining models, never as an allow-list of the scoped ones, or the next
    model this estate adopts is refused by a document nobody thought to open.

  **`awsds-org-scp-baseline.json` carries them** (taken 2026-09-11 by the user). It is attached at the
  **root**, so it reaches every account in the organization — **with the exception every SCP has: it does
  not restrict the Management account**, even attached at the root. That is acceptable here and it is not
  nothing: it means the control rests on principle 1 for Management, and the only thing that keeps
  Management out of scope is that nobody invokes a model there. Decision 2 keeps the model-access form
  out of Management for the same reason, and the two reinforce each other.

  Per the standing rule, the battery is re-run and `POLICIES.md` gains its rows in the same sitting
  ([`scp-battery.md`](../runbooks/scp-battery.md)). The battery is also the instrument that answers
  whether the deny bites: an amended ceiling means editing `probes.py`, never reading the document back.

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

- **8.1 — [Claude] The rates of the scoped set, and the arithmetic that matters.** Per 1M tokens,
  `us-west-2`, the `us.` profiles, read 2026-09-11 from `AmazonBedrockFoundationModels`. The fourth row
  is not scoped and is here because it is what a Bedrock session bills for background work when nothing
  pins a Haiku (5.3):

  | Model | Input | Output | Cache read | Cache write, 5 min |
  |---|---|---|---|---|
  | Opus 5 — primary | 5.50 | 27.50 | 0.55 | 6.875 |
  | Sonnet 5 — the picker's alternative | 2.20 | 11.00 | 0.22 | 2.75 |
  | Haiku 4.5 — background | 1.10 | 5.50 | 0.11 | 1.375 |
  | *Sonnet 4.5 — the unpinned background default* | *3.30* | *16.50* | *0.33* | *4.125* |

  Output is five times input and fifty times cache read on every row, so a session's bill is dominated by
  output tokens and by cache misses. **Do not estimate the total here** (Lesson 6, and Lesson 7 — a
  rejected-on-cost option goes stale in the direction that flatters the rejection). Read one real
  session from 6.4, write the number down with its date, and decide against that.

  Two spellings of the usage type coexist in that offer file and a parser over it must handle both:
  the newer models publish `USW2_input_tokens_standard-Units`, the older ones
  `USW2_InputTokenCount-Units`. Haiku 4.5 is on the second spelling and the other three on the first.
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
- **9.6 — The runbook exists**, [`claude-code-sagemaker.md`](../runbooks/claude-code-sagemaker.md),
  written 2026-09-11 at the user's request with **§M complete** — the retention mode and the form, the
  two acts that enable the model — and §I, §U and §V carrying what is settled, each marked where it
  describes something unbuilt. `CLAUDE.md`'s routing row was added in the same sitting, after the
  re-trim it needed. It still owes whatever step 6 finds. **It is written for two audiences that do not overlap**, and
  that is its whole shape: the infrastructure engineer configures this once for everyone and never opens
  the IDE; the data scientist opens the IDE and never touches an account. A runbook that mixes them makes
  each read past the other's half.

  | Section | Audience | What it holds |
  |---|---|---|
  | **§M — Enabling the model** | infrastructure | the use-case form and its answers (step 2), which account submits it and why not Management, `get-use-case-for-model-access` as the before-and-after reading, the scoped model set with its `us.` profile ids, and the fact that access is granted on submission rather than approved |
  | **§I — What the infrastructure configures** | infrastructure | the `bedrock-llm` endpoint group and the `NO_PROXY` that must move with it (step 4), the IAM grant and its resource scope (step 3), the endpoint policy, the managed settings file the image writes (5.2), the image bump that delivers it (5.4), the retention SCP (7.5), and the budget notification (8.3) |
  | **§U — What the user configures** | the data scientist | installing the extension **into the remote session** rather than the portal's Code Editor, *Disable Login Prompt* per surface (5.5), what `/model` should offer and what it means if it offers more, how to confirm the session is on Bedrock (`/status` naming the provider and the resolved region), and the failures with their causes |
  | **§V — Reading it back** | both | one instrument per question, read-only: the CloudTrail event with its `vpcEndpointId`, the proxy log's silence on `bedrock-runtime`, the retention mode, and the token counters |

  **§U says what a user cannot change**, since managed settings sit above every other level: the
  provider, the region, the model pins and the picker's contents are the institution's, and an attempt
  to override one in `~/.claude/settings.json` is ignored rather than refused — which reads like the
  setting not working.

  Its row in `CLAUDE.md`'s routing table was added the day the file was created, after the re-trim it
  needed: the file stood at 39,856 bytes against a 40,000-byte gate and now stands at 39,900, so the
  next sitting that adds to it re-trims again.

---

## Verifications

| | Question | Answered by |
|---|---|---|
| (i) | Does the form exist, and did it change anything? | **Answered 2026-09-11**: it exists (2.3, against 0.3), and it changed nothing any control-plane reading here can see (0.9) |
| (ii) | Can the principal of step 1 invoke **each of the three scoped models**, measured by a call rather than by a policy read? | 6.3, and a background task for the Haiku half |
| (iii) | Does the invocation carry `vpcEndpointId`? | 4.5, 6.3 |
| (iv) | Is the proxy access log silent on `bedrock-runtime` for the same window? | 4.5's negative control |
| (v) | Does a session reach **no** Anthropic host? | 6.2 |
| (vi) | What are the three models' `allowed_modes`, on the day they are read? | 7.2 — **and no AWS API carries the field**, so this one is answered from the vendor page or the console, dated |
| (vii) | Is the account's retention mode `none`, and can anyone change it? | 7.2 read `inherit` on 2026-09-11; 7.5a sets it and 7.5's deny freezes it |
| (viii) | Does the CloudTrail record carry the prompt? | 4.6 — it must not |
| (ix) | What does one session cost? | 6.4, 8.1 |
| (x) | Does the configuration survive a new space? | a second space from `default-v0.3.0`, after 5.4 |
| (xi) | Does `/model` offer exactly the picker set, and `/status` name Bedrock and `us-west-2`? | the first session, against 5.2's `availableModels` |
| (xii) | Does a background task bill Haiku rather than the primary model? | the invocation's `modelId` in CloudTrail for a session-title call (5.3) |

## Decisions

**Taken 2026-09-11 by the user, before execution.** Each is written into the step that owns it; this
table is the index, not the reasoning.

| | Question | Taken |
|---|---|---|
| **8** | Where the IAM grant lives | **on the project role, attached by `sandbox/bedrock/`** (taken 2026-09-11). The blueprint offers no granting lever at all, so a domain-wide floor was never on the table (3.4); the alternative that would have made *which projects* one list puts the caller outside the D13 boundary, and that decided it. Lesson 14's cost is accepted and written into the slice and into the runbook's §P |
| **1** | Where the assistant runs | **the space** — and *VS Code on the laptop over a remote session* is the same answer, measured rather than inferred (step 1) |
| **2** | Where the model-access form is submitted | **`Sandbox` alone**, not org-wide from Management (2.1) |
| **3** | Whether `availableModels` locks the picker to the pinned models | **yes** — an unpinned model is outside step 2's declared use case and outside step 3's resource scope (5.2) |
| **4** | Which policy document carries the retention denies | **`awsds-org-scp-baseline.json`**, attached at the root, which reaches every account but does not restrict Management — the exception every SCP has (7.5) |
| **5** | Model invocation logging on or off | **off here, and the question moves to Stage 11 step 5.6**, written at the receiving end rather than only at this one (7.4) |
| **7** | Which model carries background work | **Haiku 4.5**, pinned. Without the pin a session that sets `ANTHROPIC_MODEL` runs session titles on **Opus 5** — a defect in this plan's first draft, not an optimisation (5.3) |
| — | The scoped model set | **Opus 5, Sonnet 5, Haiku 4.5**, one list with four consumers (step 3) |

## Still open

| | Question | Waits on |
|---|---|---|
| **6** | Whether D12's budget deferral closes here, and at what threshold | the *whether* is decidable now and recommended **yes**; the number waits on 6.4's token volume (8.3) |
| **9** | Whether the `aws-marketplace` pair is needed here | a measured refusal, not the vendor's policy sample (3.2). 0.9 narrows it: the three models read `AUTHORIZED` with `agreementAvailability NOT_AVAILABLE`, so any subscribe would belong to the form's submitter, not to the project role at invocation |
| ~~**10**~~ | ~~Whether the use-case form is submitted by console or adopted as a Terraform resource~~ | **Taken 2026-09-11: console**, and done. The objection that decided it — `form_data` being opaque — turned out to be false: the blob is double base64 over flat JSON, so the org-wide form 2.1 defers to could be authored and reviewed (2.5) |
| **11** | Whether to run 7.2a's Fable probe, the only negative control `mode: none` can have | decidable now; recommended **run it** — a refused call costs nothing and a successful one is a finding of the first order (7.2a) |
| — | Whether the assistant fits the USD 50 ceiling | one real session (6.4, 8.1) |

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
| the background model on Bedrock (5.3) | two sentences that together caught a defect: background work runs on **the default Sonnet** rather than a Haiku, **and a session that sets `ANTHROPIC_MODEL` runs it on that model instead** — so the draft's own config would have billed session titles at the Opus rate. `ANTHROPIC_DEFAULT_HAIKU_MODEL` is the only key that moves it |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` vs the survey | metrics, error reports and `/feedback` are already off on Bedrock; the session-quality survey is **not**, and is the only Anthropic-bound traffic left to close |
| `skipWebFetchPreflight` | the WebFetch hostname check calls `api.anthropic.com` **regardless of provider** and is not covered by the variable above |
| `/etc/claude-code/managed-settings.json` | the configuration has a home that a user cannot override and the image can write — 6d decision 8's shape, with a file made for it |
| `AWS_BEARER_TOKEN_BEDROCK` | a long-lived credential, refused by principle 2 before it is weighed (5.1) |

**Added 2026-09-11, from the readings rather than from a page.** Each corrected something this file
asserted before it was measured.

| Read | What it corrected |
|---|---|
| the project role's three managed policies against the two target ARNs (3.1) | *"this step may be empty"* — it is not. Every `InvokeModel*` allow lands on `foundation-model/*`, none on the system profile, and `ListInferenceProfiles` is granted nowhere |
| `{"mode": "inherit"}` and the enum's own wording (7.2) | the account has **declared nothing**, so 7.5 needs the call that sets `none` before the deny that freezes it |
| no shape matching `allowed` in eight `bedrock*` service models (7.2) | the step's load-bearing reading has **no control-plane route**, which this file gave it |
| nine `aws_bedrock_*` resources and 29 registry types (7.5a) | the retention mode is a hand-managed account setting, and the **use-case form is a Terraform resource** whose single field is an opaque blob (2.5) |
| `glue:GetDatabases` as a negative control (3.1a) | `simulate-principal-policy`'s organization verdict is unusable from a member account, and `simulate-custom-policy` caps a policy at 2,000 characters — neither simulator can answer this |
| `bedrock:DataRetentionMode` accepted, a bogus key rejected (7.5) | the condition key 7.5 rests on exists, measured with the instrument's own negative control |
| `get-inference-profile` on all three (0.2) | the residency exception of 7.3 is the **set's**, not Opus 5's |
| `list-foundation-model-agreement-offers` (0.4) | the rates hold against a second source, and a batch tier exists on the `us.` profile too |

---

*Stage index: [`docs/plan/stages/INDEX.md`](INDEX.md) · Plan core:
[`GENERAL_PLAN.md`](../../GENERAL_PLAN.md) · The channel this runs inside:
[`remote-ide.md`](../runbooks/remote-ide.md)*
