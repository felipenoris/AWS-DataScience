# Log — Stage 6e — Claude Code on Bedrock

*The stage file is [`docs/plan/stages/stage-06e-claude-code-bedrock.md`](../plan/stages/stage-06e-claude-code-bedrock.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

*Identifiers are redacted as [`INDEX.md`](INDEX.md) requires: an account id becomes the account's name
in angle brackets, an e-mail address inside an ARN becomes that user's role. Everything else in a pasted
output stays verbatim. All times UTC.*

---

## 2026-09-11 — the read-only steps: 2.4, 3.1, 7.2, and the instruments that could not answer

*Written by Claude at the user's request, in the sitting that took the readings. Every reading is
Claude's own, read-only, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission set
`InfrastructureAccess`). ARNs are written without their account segment. `aws-cli/2.36.18`.*

### 2.4 — `InfrastructureAccess` can submit the form, on or off the VPN

- `list-attached-role-policies` on `AWSReservedSSO_InfrastructureAccess_*` in Sandbox returns
  **`AdministratorAccess` alone**; `list-role-policies` returns nothing and `Role.PermissionsBoundary`
  is `null`. So `bedrock:PutUseCaseForModelAccess` is covered, and 0.6 was re-read against the ten
  documents in `policies/`: none names a `bedrock:` action.
- **This set does not carry `DenyControlPlaneOffVpn`.** The fragment is attached by
  `aws_ssoadmin_permission_set_inline_policy.persona`, whose `for_each` is the six persona sets;
  `InfrastructureAccess` is the imported seventh and takes only the managed attach. The console
  submission therefore works from any network.

### 3.1 — the project role holds the foundation-model half and none of the profile half

`datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, boundary `awsds-sandbox-project-boundary`, three
AWS-managed policies attached, **no inline document**. Its tags carry
`EnableAmazonBedrockPermissions=true`; **`EnableAmazonBedrockIDEPermissions` is absent**.

Every `Allow` in the three documents was matched against the two ARNs a scoped invocation names:

| Action | `inference-profile/us.anthropic.*` | `foundation-model/anthropic.*` |
|---|---|---|
| `InvokeModel`, `InvokeModelWithResponseStream` | **no statement matches** | `SageMakerStudioBedrockKnowledgeBaseServiceRolePolicy/BedrockModelInvocationPermission`, no principal-tag gate, `Null: {bedrock:InferenceProfileArn: false}` |
| `GetInferenceProfile` | **no statement matches** — every one is scoped to `application-inference-profile/*` | — |
| `ListInferenceProfiles` | **granted nowhere in the three documents** | — |

The two statements that look like they serve do not: `InvokeBRModel` requires the IDE tag the role
does not carry, and `BedrockInvokeModelPermissions` requires `bedrock:InferenceProfileArn` to be
`ArnLike` an **application** inference profile, a different resource type from the system-defined one.

- **The boundary confirms 0.7 by reading**: nine statements, ceiling
  `CeilingIsEverythingTheIdentityPolicyGrants` = `Allow * on *`, and no statement names a `bedrock:`
  action.
- **No probe can run from here.** The role's trust policy admits the DataZone, SageMaker, Bedrock,
  Glue, Athena, Redshift, Lambda and Airflow service principals plus
  `role/awsds-sandbox-smus-provisioning`. `InfrastructureAccess` is not among them, so the call of
  3.4 is step 6's (Lesson 22).
- The grant document drafted from this reading — the three profile ARNs and the three region-less
  foundation-model ARNs for `InvokeModel*`, the profile ARNs for `GetInferenceProfile`, and
  `ListInferenceProfiles` on `*` — returns **zero findings** from
  `accessanalyzer validate-policy --policy-type IDENTITY_POLICY`.

### 7.2 — the account has declared no retention mode, and the per-model reading has no API

```
aws bedrock get-account-data-retention --region us-west-2
{ "mode": "inherit" }
```

No `updatedAt` field: it has never been set. The enum, read from the service model the CLI ships
(`botocore/data/bedrock/2023-04-20/service-2.json`):

| mode | what the API documents |
|---|---|
| `default` | the standard data handling **for the model** applies |
| `none` | zero data retention |
| `provider_data_share` | data may be shared with the model provider |
| `inherit` | **no data retention mode is set at this scope** |

- **`allowed_modes` is not in the Bedrock API.** It is absent from `get-foundation-model`,
  `list-foundation-models` and `get-foundation-model-availability`, and no shape or member matching
  `allowed` exists in any of the eight `bedrock*` service models the CLI ships. 7.2's second reading
  has no control-plane route; it is a vendor-page or console reading.
- 0.3 and 0.5 were re-read the same day and are unchanged: `get-use-case-for-model-access` returns
  `ResourceNotFoundException: You have not filled out the request form.`, and
  `get-model-invocation-logging-configuration` returns nothing.

### 7.5 — the condition key exists, measured with a negative control beside it

`accessanalyzer validate-policy --policy-type SERVICE_CONTROL_POLICY` over a two-statement draft:
the statement conditioned on `bedrock:DataRetentionMode` produced **no finding**, and the statement
beside it conditioned on `bedrock:NoSuchConditionKeyAtAll` produced
`ERROR / INVALID_SERVICE_CONDITION_KEY: The condition key bedrock:NoSuchConditionKeyAtAll does not
exist in the service bedrock.` The instrument fires, so the silence on the real key is a reading.
It establishes that the key is in the service's catalogue, not that `PutAccountDataRetention`
publishes it at request time — that is the battery's, in `Policy Canary`.

### Terraform and CloudFormation coverage, read for the retention mode

- **No Terraform resource and no data source wraps the retention API.** `hashicorp/aws` 6.60.0
  declares nine `aws_bedrock_*` resources and eight data sources; none matches `retention`. The
  binary does carry `bedrock.GetAccountDataRetentionInput` and `PutAccountDataRetentionInput`,
  which is the bundled Go SDK rather than a provider surface.
- **No CloudFormation type either.** `list-types --visibility PUBLIC --filters
  TypeNamePrefix=AWS::Bedrock` returns 29 `AWS::Bedrock::*` types and none is an account setting,
  so `awscc` has nothing to offer (Lesson 8 checked, not assumed).
- **The use-case form, by contrast, is a resource**: `aws_bedrock_use_case_for_model_access`, whose
  whole schema is one required attribute, `form_data (string)`. The API takes `formData` as a
  **blob** on both `Put` and `Get`, so the six fields step 2 specifies would appear in the code and
  in every diff as opaque base64.

### Instruments that returned an answer and were wrong

- **`simulate-principal-policy` cannot evaluate this organization from a member account.** For the
  project role it returned `EvalDecision explicitDeny` with
  `OrganizationsDecisionDetail.AllowedByOrganizations false` on `bedrock:InvokeModel*`, against an
  organization whose ten documents name no `bedrock:` action. The negative control settles it:
  `glue:GetDatabases` — which this role performs in the portal daily — comes back the same way,
  while `sts:GetCallerIdentity` comes back `allowed / true`. The top-level decision inherits the
  false organization verdict, so neither is usable here.
- **`simulate-custom-policy` caps each input policy at 2,000 characters.**
  `Value at 'policyInputList' failed to satisfy constraint: Member must have length less than or
  equal to 2000`. The two SMUS documents are 4,720 and 54,912 bytes compacted, so the identity layer
  cannot be simulated in isolation either. 3.1 above is a reading of the documents.

### What the readings add to step 0

- **All three scoped models are inference-profile only, and all three `us.` profiles route to three
  regions.** 0.1 and 0.2 measured Opus 5; `get-foundation-model` returns
  `inferenceTypesSupported ["INFERENCE_PROFILE"]` for Sonnet 5 and Haiku 4.5 as well, and
  `get-inference-profile` returns `ACTIVE`, `SYSTEM_DEFINED` and the same
  **us-east-1, us-east-2, us-west-2** model list for all three. 7.3's residency exception covers the
  set, not one model.
- **`get-foundation-model-availability` reads permissive while the form has never been submitted**:
  `authorizationStatus AUTHORIZED`, `entitlementAvailability AVAILABLE`, `regionAvailability
  AVAILABLE` for all three, with `agreementAvailability.status NOT_AVAILABLE`. It is not the
  instrument for 2.3; `get-use-case-for-model-access` is.
- **0.4's rates hold against a second source.** `list-foundation-model-agreement-offers` carries a
  rate card per model, independent of the pricing offer file: Opus 5 `5.5 / 27.5 / 0.55 / 6.875`
  and `11` at the 1-hour TTL, Sonnet 5 `2.2 / 11 / 0.22 / 2.75`, Haiku 4.5
  `1.1 / 5.5 / 0.11 / 1.375`, every `global.` figure 10% below its `us.` twin. The two spellings are
  visible here too — Haiku on `USW2_InputTokenCount`, the other two on
  `USW2_input_tokens_standard`. One correction to 8.1: a **batch tier exists on the `us.` profile
  as well** (Opus 5 `2.75 / 13.75`), not only on `global.`, and Haiku 4.5 alone publishes reserved
  TPM dimensions.

## 2026-09-11 — M1: the account declares zero data retention

*The write was the user's, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission set
`InfrastructureAccess`); the reading below is theirs, pasted verbatim. The post-condition beneath it is
Claude's, read-only, and is analysis rather than record.*

- **[user] `put-account-data-retention --mode none`**, `us-west-2`. The account read `inherit` with no
  `updatedAt` before it (entry above). After:

  ```
  {
      "mode": "none",
      "updatedAt": "2026-09-11T22:31:02.565000+00:00"
  }
  ```

- **[Claude] The post-condition, and it is not the mode.** `none` makes a model whose minimum retention
  mode is above it **unavailable in this account** rather than silently retaining, so the reading that
  matters is whether the scoped set survived. All three are unchanged from the morning's reading:

  | model | `authorizationStatus` | `entitlementAvailability` | `regionAvailability` | `agreementAvailability` |
  |---|---|---|---|---|
  | `anthropic.claude-opus-5` | AUTHORIZED | AVAILABLE | AVAILABLE | NOT_AVAILABLE |
  | `anthropic.claude-sonnet-5` | AUTHORIZED | AVAILABLE | AVAILABLE | NOT_AVAILABLE |
  | `anthropic.claude-haiku-4-5-20251001-v1:0` | AUTHORIZED | AVAILABLE | AVAILABLE | NOT_AVAILABLE |

  The mode was re-read independently in the same call set and returned the same `none` and the same
  timestamp. **The setting is not yet frozen**: anyone holding `bedrock:PutAccountDataRetention` can
  set it back until stage step 7.5's deny is attached.

## 2026-09-11 — M2: the model-access form submitted, and what the blob turned out to be

*The submission was the user's, by console, as the infrastructure user on `Sandbox Account 1` with
`InfrastructureAccess`. The `formData` below is theirs, pasted verbatim from
`get-use-case-for-model-access`; the decode and the two readings under it are Claude's.
`companyName` is redacted to the account owner's own name per [`INDEX.md`](INDEX.md).*

- **[user] Submitted from the Bedrock console**, Region `us-west-2`, Model catalog → Claude Opus 5 →
  the use case form.

- **[Claude] Verification (i) closed.** `get-use-case-for-model-access` stops returning
  `ResourceNotFoundException` and returns a `formData` blob. That is the whole verification, and its
  negative control is the same command's refusal in the entry above.

- **[Claude] The blob is double base64 over a flat JSON object**, which is what makes the record
  readable at all — `PutUseCaseForModelAccess` and `GetUseCaseForModelAccess` both declare `formData`
  as an opaque blob, and the CLI prints the outer layer. Decoded, six fields:

  | field | value |
  |---|---|
  | `companyName` | *the account owner's own name* |
  | `companyWebsite` | `https://github.com/felipenoris` |
  | `intendedUsers` | `0` |
  | `industryOption` | `FinancialServices` |
  | `otherIndustryOption` | `` (empty) |
  | `useCases` | `. Data-Science models for Banking` |

- **[Claude] `useCases` carries a leading `". "` and reads narrower than the stage's step 2.2 text.**
  Raised with the user the same day, **who chose to keep it as submitted**: their reading is that the
  separator is an artefact of the console's own form, which is consistent with `otherIndustryOption`
  being empty and the two fields sharing one input. The form is a `Put` and the blob's encoding is now
  known, so a re-submission is cheap if the wording is ever revisited.

- **[Claude] The availability reading did not move on submission.** All three scoped models read
  `AUTHORIZED / AVAILABLE / AVAILABLE` with `agreementAvailability NOT_AVAILABLE` before the form and
  the same after it — identical to the morning's reading and to M1's post-condition. **Three readings
  across two state changes, all identical**: `get-foundation-model-availability` is not an instrument
  for whether this account may invoke, and a later reader meeting `AUTHORIZED` should not take it for
  access.

## 2026-09-11 — every Anthropic model in the Region, and the two the vendor names as retaining

*Claude's readings, read-only, on the user's question "what about the other models". Recorded here
after the fact, in the sitting the user asked for the log to be completed.*

- **[Claude] Thirteen Anthropic models in `us-west-2`, all reading identically with the account at
  `none`.** `AUTHORIZED / AVAILABLE / AVAILABLE`, `agreementAvailability NOT_AVAILABLE` — and that
  includes **`anthropic.claude-fable-5` and `anthropic.claude-fable-5-1`**, the two the vendor's
  abuse-detection page names as retaining every prompt for up to 30 days with human review of
  classifier-flagged traffic.

- **[Claude] So `mode: none` has no visible effect, and the claim that it makes a retaining model
  unavailable is unverified.** Four instruments were tried and none shows a retention mode or its
  consequence: `get-foundation-model`, `list-foundation-models`,
  `get-foundation-model-availability`, and `list-foundation-model-agreement-offers`, whose
  `termDetails` carries pricing, legal and support terms only. **The instrument would not have shown
  the presence either way** (Lesson 62), so this is a non-reading rather than a negative one.

- **[Claude] The catalogue, for scale**: 113 models across 18 providers — Amazon 17, Stability 16,
  Mistral 13, Anthropic 13, Meta 10, OpenAI 8, and twelve more.

- **[Claude] Two consequences written into the stage.** Step **7.2a** was created — invoke
  `us.anthropic.claude-fable-5` as the infrastructure user and read the refusal, the only negative
  control `none` can have, and a **success** would mean it is a label rather than a control
  (decision due 11). And step 7.5's second deny stopped being belt-to-braces: with nothing reading
  the mode's effect, **it is the only half of the pair the battery can prove**, and it now has a
  measured target list rather than a vendor page.

- **[Claude] The form is account-level, shown from the API's own shape.** Neither
  `PutUseCaseForModelAccess` (`POST /use-case-for-model-access`) nor `GetUseCaseForModelAccess`
  (`GET /use-case-for-model-access`) takes a `modelId`, in the path or the body — against
  `GetFoundationModelAvailability`, whose route is `/foundation-model-availability/{modelId}`. So
  one submission covers Sonnet 5 and Haiku 4.5 as well as the Opus 5 selected in the console.

## 2026-09-11/12 — the instrument and the runbook

*Claude's authored changes. Both were asked for by the user; recorded here in the sitting the user
asked for the log to be completed.*

- **[Claude] `aws/bedrock.py`**, read-only, multi-profile, in `aws/INDEX.md`'s shape. It holds the
  three questions the console blurs apart — the account gates, the catalogue, and the resources that
  would be billing — and decodes the use-case form. Checks `BR-1`..`BR-6` are readings;
  **`BR-7` is an instrument control rather than a finding**: it compares the availability reading in
  an account that submitted the form against one that did not. **First run, on a real contrast**:
  `Sandbox` (form, `none`) against `Staging` (no form, `inherit`) — identical. So the call is not
  evidence of access, measured on every run rather than asserted once.

- **[Claude] `BR-8` added after the grant was applied**, in `aws/devenv.py`'s shape: read what
  `terraform-live/sandbox/bedrock/variables.tf` declares, read what IAM reports, and name **which of
  the two divergences** it found — a declared attachment that is gone was removed by something
  (INT-15's open half), and an attachment nothing declares is undone by the next apply (Lesson 35).
  First run: one project role, declared and attached, `agree`.
  **A defect caught in the same sitting**: the first draft built the policy name from an `env_token`
  that was never in the dict, so it silently always read `sandbox`. It now matches
  `awsds-<env>-bedrock-assistant` by shape — `aws/` does not import the env-token table by design.

- **[Claude] `docs/plan/runbooks/claude-code-sagemaker.md`**, the stage's step 9.6 brought forward
  because the two acts it describes were the next thing to happen. **§M** (the retention mode and
  the form) is complete and was executed from it; **§P** is the per-project grant procedure in both
  the Terraform and the `aws` CLI form, added when decision 8 was taken; §I, §U and §V carry what is
  settled, each marked where it describes something unbuilt.

- **[Claude] `CLAUDE.md` re-trimmed to make room for the runbook's routing row**, which the stage
  said that sitting would have to do: 39,713 → 39,900 bytes against a 40,000-byte gate. The cuts are
  explanation whose owning file already carries it — the remote-IDE, 6d, MWAA, VPN, proxy-plane and
  standing-rules bullets — plus one genuine dedup, the two MWAA bullets being one subject.

## 2026-09-11 — step 3's decision: the blueprint grants nothing, so the grant is per project

*Claude's readings and authored changes, at the user's request. No AWS write.*

- **[Claude] The blueprint has no granting lever, measured from the provider schema.**
  `awscc_datazone_environment_blueprint_configuration` carries fourteen attributes and exactly one
  is policy-shaped — `environment_role_permission_boundary`, which is how INT-15 imposes D13 — and
  a boundary only subtracts. The one other IAM-shaped field, `provisioning_configurations`, holds
  `location_registration_role` and an S3 exclusion list: Lake Formation registration, not a grant.
  **The service offers a ceiling for every project role and a floor for none**, so the option this
  stage had recommended — a policy reaching the project roles through `sandbox/sagemaker/` — never
  existed to be chosen or refused.

- **[Claude] Whether a same-account `sts:AssumeRole` needs an identity grant, part-measured.** It
  is the question option (c) would have had to answer. `awsds-sandbox-smus-provisioning` is named
  in the project role's trust policy as a principal allowed to assume it, and its only attached
  policy — `SageMakerStudioProjectProvisioningRolePolicy`, v82 — carries **zero** `sts:` statements
  and zero wildcards, with no inline document. If an identity grant were required, that trust
  statement AWS itself wrote would be inert. **The observation to confirm it was not obtained**:
  the 50 most recent `AssumeRole` events in Sandbox span 19:12 to 20:37 today, and the project was
  created 2026-08-22, so the instrument does not reach the event. The absence is not a reading
  (Lesson 62) and is recorded as such.

- **[user] Decision 8 taken: option (b)** — the policy attached to the project role. Against (c)'s
  advantages (which projects as a list this repository writes, a dedicated principal for cost
  attribution) stood one fact: in (c) the model is invoked by a principal **outside
  `awsds-sandbox-project-boundary`**, and every other interactive call in this account is inside
  it. (c) is recorded as the Stage 14 shape.

- **[Claude] `terraform-live/sandbox/bedrock/` written, unapplied.** Rank **52**, `[P]`, registered
  in `scripts/tfhygiene/layers.py`. One `awsds-<env>-bedrock-assistant` policy — the two invoke
  actions on the three profile ARNs and the three region-less foundation-model ARNs,
  `GetInferenceProfile` on the profiles, `ListInferenceProfiles` on `*` — and one attachment per
  entry in `project_roles`, hand-written after a project exists. The attachment carries a
  **precondition that the role is under the D13 boundary**: a hand-written name matching
  `datazone_usr_role_*` is the one way this could grant Bedrock to a principal outside the ceiling
  the decision was taken to keep. `terraform validate` passes; the lock file was copied from
  `sandbox/dev-env/` per step 6.3 rather than regenerated, which the gate names as the correct move.

- **[Claude] The procedure is `claude-code-sagemaker.md` §P**, added to the runbook in the same
  sitting: P1 finds the role name and tells two projects apart by tag, P2 is the Terraform path, P3
  the `aws iam attach-role-policy` equivalent with the warning that it leaves drift the next plan
  would revert (Lesson 35), P4 verifies and says what a verification here cannot say.

## 2026-09-11 — `sandbox/bedrock/` applied

*The apply was Claude's, authorized by the user in that sitting, as the infrastructure user on
`Sandbox Account 1` with `InfrastructureAccess`. Recipe A. Account ids are redacted.*

- **[user] Authorized the apply.** **[Claude] The one edit it needed first**: `project_roles` was
  `[]`, which would have created a policy attached to nothing. It now carries the experimentation
  project's role, read from `iam list-roles` the same day.

- **[Claude⚡] `terraform apply`, 2 added, 0 changed, 0 destroyed.**

  ```
  aws_iam_policy.bedrock_assistant: Creation complete after 1s
  aws_iam_role_policy_attachment.project["datazone_usr_role_..."]: Creation complete after 0s
  ```

  The plan was read before applying and matched what the runbook's §P2 says to expect for a first
  project: the policy plus exactly one attachment, nothing changed and nothing destroyed. **The
  boundary precondition passed silently**, which is its pass condition — the role carries
  `awsds-sandbox-project-boundary`.

- **[Claude] The policy as applied**, read out of the plan rather than from the source:

  | Sid | Actions | Resources |
  |---|---|---|
  | `InvokeScopedClaudeModelsThroughSystemProfiles` | `InvokeModel`, `InvokeModelWithResponseStream` | the three `us.` profile ARNs **and** the three foundation-model ARNs, the latter with no region segment |
  | `ResolveTheScopedProfiles` | `GetInferenceProfile` | the three profile ARNs |
  | `ListProfilesHasNoResource` | `ListInferenceProfiles` | `*` |

- **[Claude] Verified two ways.** `terraform plan -detailed-exitcode` returns **0** with *"found no
  differences"*; `list-attached-role-policies` on the project role returns **four** policies — the
  blueprint's three and `awsds-sandbox-bedrock-assistant`.

- **What this does not establish.** That the policy is attached is not that the model can be
  invoked: reach is an intersection and this is one term of it. Steps 4 (the private path) and 5
  (the configuration in the image) stand between here and a call, and the call is step 6's.

## 2026-09-11/12 — step 4's code: two module tags, and a premise corrected

*Claude's authored changes and readings. No AWS write; the apply is owed.*

- **[Claude] `vpc-egress-v0.12.0`** — `bedrock-llm = ["bedrock", "bedrock-runtime"]` beside the
  four-endpoint `bedrock` group rather than instead of it (the existing group's consumer, the six
  enabled `AmazonBedrock*` blueprints, does reach the agent endpoints), and
  `endpoint_action_scopes`, which narrows one endpoint's policy on the action axis.

- **[Claude] `vpc-egress-v0.13.0`, and why it is a second tag.** Writing the caller surfaced that
  **`bedrock` and `bedrock-llm` are two configurations of one door**: both contain `bedrock` and
  `bedrock-runtime`, the map key collapses the overlap to one endpoint, and one endpoint carries
  one policy — so the assistant's action list would have applied to the blueprints' control-plane
  calls and refused `CreateGuardrail` with no denial naming the policy. The module now refuses the
  two groups together as a plan error. **A tag is never moved**, so this is a version rather than
  an amendment.

- **[Claude] Step 4.4's premise was wrong, and the stage file now says so.** It read *"the
  interface endpoint's default policy allows every Bedrock action to every principal"*. These
  endpoints have never carried the default: `vpc-egress` has applied the trusted-networks document
  — organization principals and AWS service principals — to every interface endpoint since Stage 3
  step 9. What the new variable adds is a second axis on top of that, not a first control.

- **[Claude] The resource axis is left alone, reversing what 4.4 asked for.** Scoping the endpoint
  to the six model ARNs would put the grant's list in a second slice with nothing comparing them
  (Lesson 33), and the failure would be a network refusal for a model correctly added to the grant.
  The action list is a property of the service rather than of this estate's choices.

- **[Claude] A defect caught before it shipped.** The first draft defaulted an unscoped endpoint's
  `Action` to the list `["*"]` where every endpoint has carried the string `"*"` since step 9. It
  would have shown a policy diff on all eighteen endpoints for a change that means nothing, and
  broken the byte-identical output the D11 cycle checks. Unscoped endpoints now take the statement
  untouched.

- **[Claude] `sandbox/egress/` bumped to `v0.13.0`** and given the action scope. `terraform
  validate` passes and the module resolved from origin at the new tag. **`plan` was not obtained**:
  the `awsds` SSO session token expired at `00:07:30Z` and terraform's refresh returned
  `InvalidGrantException`.

- **[Claude] A reading worth keeping: the CLI and terraform disagreed about whether the session was
  alive.** `aws sts get-caller-identity` answered normally at `00:12Z`, five minutes after the
  token expired, because it used a still-valid cached **role credential**; terraform's SDK tried to
  refresh the **session token** and failed. Neither is wrong — they read different objects, and
  `get-caller-identity` is therefore not a test of whether an apply will authenticate.

## 2026-09-12 — step 4 restructured: the Bedrock pair is always-on, not a group

*Claude's authored changes, at the user's direction. No AWS write; the apply is still owed.*

- **[user] The `bedrock-llm` group is withdrawn**, and the reason is the flag's own semantics: an
  optional group is per apply, `make up` without it destroys what it created, and the assistant
  needs this path in every session a space runs. A permanent consumer cannot live behind a
  per-apply flag.

- **[Claude] `vpc-egress-v0.14.0`.** `bedrock-llm` removed; the optional `bedrock` group narrowed
  to `["bedrock-agent", "bedrock-agent-runtime"]`, what only the blueprints use. **The mutual
  exclusion of `v0.13.0` is gone with it** — the two groups shared two endpoints and could not be
  named together, and with the shared pair moved out there is nothing left to collide. A guard
  against a situation that can no longer arise misleads the next reader.

- **[Claude] `sandbox/egress/` carries the pair in `extra_services`**, always on, and takes the new
  tag. The cost moves from per-apply to permanent-while-up: **Sandbox 18 endpoints → 20, the
  estate's fixed rate 0.390 → 0.410 USD/h.** `CLAUDE.md`, `docs/plan/conventions.md` §6,
  `docs/NETWORK.md` and the `Makefile`'s `GROUPS` help were corrected in the same sitting; the
  2026-09-09 "16 of 18" measurement in `NETWORK.md` stays as measured, with the new count dated
  beside it.

- **[Claude] The restructure moved the action-scope question, and the answer changed with it.**
  While the two endpoints belonged to an assistant-only group, scoping both was safe. As always-on
  infrastructure they are shared with the six SMUS `AmazonBedrock*` blueprints, and a list written
  for one consumer silently refuses the other with no denial naming the policy (Lesson 51). So
  `sandbox/egress/` now scopes **`bedrock-runtime` only**, to `InvokeModel` and
  `InvokeModelWithResponseStream` — that door carries invocation for every consumer, so the list is
  a statement about the service. **`bedrock` keeps `Action = "*"`** under the organization
  condition.

- **[Claude] What that gives up, written rather than left to be discovered.**
  `PutAccountDataRetention` and `PutModelInvocationLoggingConfiguration` are control-plane calls and
  still traverse their endpoint. The first is covered org-wide by step 7.5's SCP, which is the right
  layer for it; the second is Stage 11 step 5.6's and has no control here yet.

- **[Claude] `terraform validate` passes** on the module and on the caller against
  `vpc-egress-v0.14.0`, fetched from origin. **Three tags exist for one step** — `v0.12.0` the
  mechanism, `v0.13.0` a guard, `v0.14.0` the restructure that dissolved it — because a tag is
  never moved and each was pushed before the next question was asked.

## 2026-09-12 — step 5's repository half

*Claude's authored changes, at the user's request while the SSO session was down. No AWS write, and
no build: `default-v0.3.0` is written but not buildable.*

- **[Claude] The managed settings path was read rather than assumed.** The vendor documents the
  system directory per OS, and on **Linux and WSL** it is `/etc/claude-code/managed-settings.json`,
  read at startup and reloaded when the file changes — the mechanism named for *"images you build
  yourself"*. Managed settings are the top tier and `availableModels` is the lock that constrains
  `/model`, `--model` and the `model` key in a user's own file. A wrong path would have been ignored
  in silence, which is why it was fetched.

- **[Claude] It is a side file, not a heredoc, and that was a correction mid-edit.** The first
  version wrote the JSON with a shell heredoc inside the `RUN`. That cannot work here: the
  Dockerfile carries no `# syntax=` directive, so the classic frontend is in use and the line
  continuation eats the newline the heredoc body needs. It is now
  `images/dev-env/claude-code/managed-settings.json`, `COPY`d — reviewable as JSON in a diff, which
  a heredoc inside a `RUN` is not.

- **[Claude] `pre-commit` gains `check-json` over `images/**.json`.** An unparseable
  `managed-settings.json` is **ignored silently**: every key stops applying and the session runs on
  the client's defaults, against `api.anthropic.com`. A trailing comma has to fail in review rather
  than in a space three weeks later. The image re-parses it too, guarded on `command -v python3` the
  way the `visudo` call beside it is.

- **[Claude] `sandbox/dev-env/`'s `image_tag` is `default-v0.3.0`.**

- **[Claude] The build is blocked, and the Dockerfile says why where the value is.** Step 4 made the
  two Bedrock endpoints always-on, so `sandbox/egress`'s generated list is 52 entries against the
  image's literal 50. The two names cannot be added by hand — eight entries in that list are not
  derivable from a service token, which is why it is read from the slice rather than composed — so
  the refresh needs the slice **up**. Until then a Bedrock call from a space reaches the proxy and
  leaves as a public call: it works, with no `aws:SourceVpc` and no `aws:SourceVpce`.

## 2026-09-12 — the close steps that need no session

*Claude's authored changes while the SSO session was down. No AWS call.*

- **[Claude] `docs/AWS_STATE.md` gains two rows (step 9.4).** **`EXC-07`**, 7.3's residency
  exception: all three scoped models are inference-profile only and every `us.` profile routes to
  us-east-1, us-east-2 and us-west-2, so this is the estate's first resource that cannot honour D1.
  The reading is inverted on purpose — a profile that ever showed **one** Region would be the
  finding, because it would mean AWS changed the profile under a pinned model id. **`INV-18`**, the
  account's Bedrock posture: `mode: none` with its timestamp, the form present, invocation logging
  off, the three models `ACTIVE`, and every other account at `inherit`. It names `bedrock.txt`
  `BR-1`..`BR-4` as its instrument and states what is **not** readable — whether `none` is enforced.

- **[Claude] `docs/PRICING.md` (step 9.1) was already correct at planning time**; what this sitting
  added is the cross-check. The agreement rate card is a second, independent publication of the same
  prices and every figure matches, which is worth recording because a disagreement between the two
  would itself be a finding. Two facts the card adds: a batch tier exists on the `us.` profile as
  well as on `global.`, and Haiku 4.5 alone publishes reserved TPM dimensions.

- **[Claude] Step 8.2 restated.** The two endpoints are no longer the cost of naming a flag; since
  step 4's restructure they are the cost of having `sandbox/egress` up at all.

## 2026-09-12 — step 4 applied, the list refreshed, and `default-v0.3.0` built and attached

*Every apply, the build, the push and both domain writes were the user's, as the infrastructure user
on `Sandbox Account 1` with `InfrastructureAccess` (the push as the buildbox's instance role on
`Production`). The diagnosis, the module fix and the authored changes are Claude's. Digests and
sizes below were read back from AWS.*

### 4.2 — the apply, on the second attempt

- **[user] `make up ENV=sandbox AUTO=1` failed** against `vpc-egress-v0.14.0` with twenty
  `Inconsistent conditional result types`, one per endpoint.

- **[Claude] The defect was in the action-scope conditional, pushed under three tags.** The
  `endpoint_policies` local chose between a scoped document and the unscoped one with a conditional
  whose two branches gave `Action` different types — a list for a scoped endpoint, the inherited
  string for every other. HCL unifies a conditional's two result types, and a statement object
  carrying a string where the other carries a list does not unify.

- **[Claude] `terraform validate` had answered `Success!` on the module and on the caller, at
  `v0.12.0`, `v0.13.0` and `v0.14.0`** — the caller fully initialised against the tag that failed.
  The reason it cannot see this is that `local.service_names` is a `for` over
  `distinct(concat(...))` whose keys are unknown until plan, so a statement's type stays dynamic
  through validation. **Lesson 54's instance, recorded there**: a module change is exercised by
  planning a caller against the local path ([`terraform-changes.md`](../plan/runbooks/terraform-changes.md)
  Recipe B step 1), never by validating it. `make check` has no plan step and the commit hooks stop
  at validate, so nothing in this repository could have caught it.

- **[Claude] `vpc-egress-v0.14.1` removes the conditional rather than repairing it.** Two documents
  are built — a `scoped_policies` map keyed by the short service name, and `local.endpoint_policy`
  itself — and `lookup` selects between them. An endpoint nobody scoped now takes **the same
  string**, not a re-encoding of it, so its document cannot drift from what it has carried since
  Stage 6c step 9. Recipe B's two commits, in order; `v0.14.0` joins the abandoned list.

- **[user] The apply: `2 to add, 0 to change, 0 to destroy`.** The two Bedrock endpoints created and
  **no existing endpoint's policy document touched** — which is the measurement that the eighteen
  documents stayed byte-identical, rather than the argument that they should have. Sandbox is now
  20 interface endpoints; the estate's fixed rate is 0.410 USD/h.

### 4.3 — the image's `NO_PROXY` literal refreshed

- **[Claude] Read from the slice, not composed**: `terraform output -raw no_proxy` on
  `sandbox/egress`, **50 → 52 entries**, the two new ones being the Bedrock pair's `dns_entry`
  names. The literal in `images/dev-env/Dockerfile` is **1,514 characters**, sha256
  `fc11caaa3145fdef8615ac59fd4a70207ebbee071edafbcc3271595dbc496ab8`. `sg-proxy.md`'s pasteable
  export block and `dev-env.md`'s dated reading were refreshed in the same sitting.

- **[Claude] A figure repeated across six files was wrong, and is corrected.** The generated
  `NO_PROXY` had been written as *"about 2,300 characters"* since 2026-09-10. Measured: the
  50-entry list is **1,442** characters and the 52-entry one **1,514**. The argument it supports is
  untouched — the app image configuration caps each value at 256 — but the number was never right.
  `docs/SMUS.md`, `docs/REFERENCES.md`, `docs/plan/lessons.md` and three passages of the 6d stage
  file now carry the measured value. **The 6d log keeps what it recorded**; this entry is the
  correction, because a log is a record of what was written on its date.

- **[Claude] `wc -l` miscounted it once**, reporting 51: `terraform output -raw` emits no trailing
  newline. The count that stands was taken by splitting on commas.

### 5.4 — the build, and the two digests

- **[user] Both images built on the buildbox and pushed as `default-v0.3.0`**, verbatim:

  ```
  default-v0.3.0: digest: sha256:97cf219d80fc5539e145733216d280f3ce836e6ccec04214542ccab3ca98bd7a size: 6582
  default-v0.3.0: digest: sha256:bd78c976195fe20c3b15a128766aed2cf15bf6d026d01280ff70128269a0c83a size: 9307
  ```

  The first is `awsds-prod-ecr-base`, the second `awsds-prod-ecr-dev-env`. Read back from the laptop
  with `describe-images`, both agree with the push output.

- **[Claude] The size delta, measured in ECR rather than from `docker images`.** `dev-env`
  **7,256,923,087 → 7,182,175,890 bytes**, −74.7 MB, −1.0% — the Julia precompilation cache removed,
  net of `rust-src` added. `base` moved 14 bytes (3,959,751,940 → 3,959,751,954), upstream drift.
  On the host: `awsds/dev-env` 22.7 → 22.4 GB, `awsds/base` 12.1 GB.

- **[Claude] A verification of Claude's own that read the wrong list, and what it turned out to
  mean.** `docker run … printf "%s" "$NO_PROXY" | sha256sum` on the buildbox returned
  `d8ee66e61600e654…` against the image's `fc11caaa3145fdef…`. The image was not wrong: the host's
  `~/.docker/config.json` carries a `proxies.default` block, and the Docker **client** injects its
  `noProxy` into every container it starts, outranking the image's `ENV`. That value is
  **`production/egress`'s** output — 39 entries, `d8ee66e61600e654…`, an exact match. The manifest
  answers the question the run cannot: `docker image inspect … .Config.Env` returns
  `fc11caaa3145fdef…`. Written up in [`buildbox.md`](../plan/runbooks/buildbox.md), because the
  symptom looks exactly like a broken image.

- **[Claude] `default-v0.3.0` carries four changes against `v0.2.0`**, not the three the stage file
  claimed: the managed settings file, the 52-entry `NO_PROXY`, `rust-src` in the rustup profile, and
  no Julia precompilation cache. `UV_NO_CACHE` landed inside the `v0.2.0` build session itself and
  is not one of them — established from the commits and the 6d log rather than from the stage file.

### The version bump, and the teardown

- **[Claude] The plan read `1 to add, 0 to change, 1 to destroy`** on
  `aws_sagemaker_image_version.dev_env`, `base_image` moving to `default-v0.3.0` with
  `# forces replacement` and `version 2 -> (known after apply)` — exactly what
  [`dev-env.md`](../plan/runbooks/dev-env.md) §B predicts, a SageMaker image version being
  immutable. Saved and applied as a plan file.

- **[user] §B's chain, in order**: no app running, the custom images detached from the domain's
  `DefaultUserSettings`, the apply, the re-attach on the new version number. The detached and
  attached blocks were both generated from the **live** `describe-domain` rather than from a stored
  file (Lesson 61), and the attach entries from `terraform output -json custom_images`, so the
  version number was never typed.

- **[Claude] Read back afterwards.** `describe-image-version` on version **3**: `CREATED`, and its
  `ContainerImage` ends in `@sha256:bd78c976195fe20c3b15a128766aed2cf15bf6d026d01280ff70128269a0c83a`
  — the digest of the push above, which is the whole point of registering against a digest rather
  than a tag. `describe-domain` carries `ImageVersionNumber: 3` on **both** `JupyterLabAppSettings`
  and `CodeEditorAppSettings`. `terraform plan` on the slice: **`No changes`**.

- **[user] The buildbox is down and so is `production/egress`.** Confirmed by reading: the only
  instances left in `Production` are `awsds-prod-vpn` (`t3.nano`) and `awsds-prod-proxy`
  (`t3.micro`), the two hub hosts, and the account's six remaining VPC endpoints are all **Gateway**
  (S3 and DynamoDB, three VPCs), which carry no hourly charge. The 0.130 USD/h has stopped.

- **What this does not establish.** No session has been opened on the new image. That the settings
  file is in the layer is not that Claude Code read it, and that the endpoints exist is not that an
  invocation took them — step 6 is the first call, and §V's CloudTrail `vpcEndpointId` reading is
  where both are settled.

## 2026-09-12 — step 6: the first session, four refusals, and what each one corrected

*The space, the Control Tower change, every agreement and every invocation from the space were the
user's. Claude's are the read-only measurements and three invocations the user authorized in the
sitting, run as the infrastructure user on `Sandbox` with `InfrastructureAccess`. The session ran on
`default-v0.3.0`, image version 3.*

### 6.1 — what the extension showed, and why it could not be debugged from there

- **[user] Opened a new space on version 3, connected remotely, installed *Claude Code for VS Code*.**
  The extension **opened a session with no login screen** — so the provider was Bedrock and nothing
  had to be exported. The picker offered **Default / Sonnet / Opus**, and **Haiku was absent**.

- **[Claude] The absent Haiku is the design, and the picker is not evidence the settings applied.**
  `availableModels` is `["opus","sonnet"]` and the Haiku pin is where background work goes, so a
  reader who sees it missing is seeing the lock. But `Default / Sonnet / Opus` is also the client's
  stock list, so the picker cannot distinguish a loaded managed-settings file from none at all —
  `/status` can.

- **[user] The first prompt hung, then the extension closed the chat and reopened its login screen**,
  and the requested action never ran. **[Claude] That is what the client does when a call fails in a
  way it reads as authentication**, and the refusal text never reaches the UI. Every diagnosis below
  came from CloudTrail and from `aws bedrock-runtime invoke-model` in the space's terminal.

### The first refusal — the organization's Region ceiling

- **[Claude] CloudTrail, twenty-two `InvokeModelWithResponseStream` events, all `AccessDenied`:**

  ```
  User: …/datazone_usr_role_…/SageMaker is not authorized to perform: bedrock:InvokeModel
  on resource: arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-5
  with an explicit deny in a service control policy: …/p-umksvu5a
  ```

  Three things in one reading. The principal is **the granted role**. `vpcEndpointId` is
  `vpce-0171b785473053321` and `sourceIPAddress` `10.20.60.99` — **the call took the private door**,
  so 4.5's property was measured on a denied call. And the resource is in **`us-east-1`** while the
  event's own `awsRegion` is `us-west-2`.

- **[Claude] A cross-Region inference profile is authorized per destination Region**, and in that
  evaluation `aws:RequestedRegion` is the destination. `p-umksvu5a` is `aws-guardrails-fzqpfF`, a
  **Control Tower** document holding `CT.MULTISERVICE.PV.1`, attached to the **`Interactive` OU**
  alone, whose only condition is `aws:RequestedRegion != us-west-2`; no `bedrock:` action appears in
  its 86 `NotAction` entries and its four exempted principals are Control Tower's own. **Nothing in
  this repository authors it** — the ten documents in `org-policies/policies/` carry no Region
  condition at all.

- **[user] The exemption, from `Management` as AWS Control Tower Admin.** Control Tower → Enabled
  controls → `CT.MULTISERVICE.PV.1` → the `Interactive` row → *View configurations* → *Update enabled
  control*. The Region list showed `us-west-2` alone; the next screen showed the policy with
  `{{ExemptedActions}}` and `{{ExemptedPrincipalArns}}` visible as template slots; at the foot of the
  page, *Adding NotActions*. Added over three passes as the diagnosis needed them:

  ```
  bedrock:InvokeModel
  bedrock:InvokeModelWithResponseStream
  bedrock:GetFoundationModelAvailability
  bedrock:GetAccountDataRetention
  bedrock:GetUseCaseForModelAccess
  ```

- **[Claude] Why `NotActions` and not `Exempted principals`.** The two lists are independent inside one
  statement — there is no way to say *this action, for this principal*. A principal exemption removes
  the Region ceiling from that principal **for every action in every Region**, and the project role is
  the interactive-compute principal. The action lever was the narrower by a wide margin. Widening
  `AllowedRegions` was the third option and opens every service in the added Regions.

- **What it gives up, and it is not yet taken back.** Those five actions are now exempt **for every
  principal in the OU, in every Region**, including Regions no profile routes to. Decision 15.

### The second refusal — the model was never enabled

- **[user] The next attempt failed differently**, which is the whole value of it:

  ```
  AccessDeniedException: anthropic.claude-sonnet-5 is not available for this account.
  You can explore other available models on Amazon Bedrock. For additional access options,
  contact AWS Sales at https://aws.amazon.com/contact-us/sales-support/
  ```

- **[Claude] Two hypotheses were tested and both were wrong.** Per-Region entitlement: all three models
  read `AUTHORIZED / AVAILABLE / AVAILABLE` in **all three** Regions. Per-Region form: the use-case
  form is present in all three, same blob. Both eliminated by reading, and the second only after the
  exemption made the other Regions readable at all.

- **[Claude] `list-foundation-model-agreement-offers` carried the answer.** A live offer exists for
  each of the three — `offer-2ykemehpsyf7g`, `offer-f3u6lgbrem3zs`, `offer-fudwqbphlos64` — each with
  a 392-dimension rate card, a `legalTerm` URL and `supportTerm: "No refunds"`. So
  **`agreementAvailability: NOT_AVAILABLE` means no agreement has been created**, not *no agreement is
  needed* — which is how step 3's grant comment and step 0.9 both read it, and how the omission
  survived three separate readings across two state changes.

- **[user] Accepted the agreement for `anthropic.claude-sonnet-5`.** Status went `PENDING` →
  `AVAILABLE` within seconds. **[Claude] It is account-wide, not per Region**: `us-east-1` and
  `us-east-2` read `AVAILABLE` **before** the creating Region left `PENDING`. It is per **model**: the
  other twelve stayed `NOT_AVAILABLE`. Amazon's own models need none — `amazon.nova-lite-v1:0` reads
  `AVAILABLE` with nothing done.

### The third refusal — a commercial gate no instrument exposes

- **[user] With the agreement `AVAILABLE`, the same call returned the same message.** Not propagation:
  it held minutes later.

- **[user] `amazon.nova-lite-v1:0` from the space** was refused at a different layer —
  *"no identity-based policy allows the `bedrock:InvokeModel` action"* — which **confirms 3.1** rather
  than contradicting it: the blueprint's one matching allow is conditioned on an inference-profile ARN
  being present and a bare model id does not satisfy it. It also proves the Claude call was passing
  IAM and the SCP and dying past both.

- **[Claude⚡] Three invocations, authorized by the user in the sitting**, as the infrastructure user:
  `amazon.nova-lite-v1:0` **answered** (1 input / 16 output tokens — the estate's first successful
  Bedrock invocation); `us.anthropic.claude-sonnet-5` returned **the same refusal for
  `AdministratorAccess`**. So the account invokes Bedrock, and this model is refused regardless of
  principal.

- **[user] Accepted the agreement for `anthropic.claude-sonnet-4-5-20250929-v1:0`** — it took minutes
  rather than seconds to leave `PENDING`. **[Claude⚡] `us.anthropic.claude-sonnet-4-5-20250929-v1:0`
  answered `pong`.**

- **The gate follows the shape of the model id.** Dated ids (`…-2025xxxx-v1:0`) invoke; clean ids
  (`claude-sonnet-5`, `claude-opus-5`, `claude-opus-4-6/4-7/4-8`, `claude-sonnet-4-6`, `claude-fable-5`,
  `claude-fable-5-1`) do not. Every readable instrument reports the gated model as available and
  authorized — agreement, authorization, entitlement, Region availability, lifecycle, the form —
  **and the invocation refuses it**. Lesson 13 at account scale; recorded as `EXC-08`.

- **[user] Accepted the agreements for `anthropic.claude-haiku-4-5-20251001-v1:0` and
  `anthropic.claude-opus-4-5-20251101-v1:0`.** **[Claude⚡] Both answered.** All three of the working
  set route to the same `us-east-1, us-east-2, us-west-2`, so `EXC-07`'s routing sentence is unchanged
  by a switch.

### The retention finding, which no refusal surfaced

- **[Claude] `get-account-data-retention` is a per-Region call**, measured by it answering `none` in
  `us-west-2` — the M1 write of 2026-09-11 at 22:31:02Z — and being refused in the other two until the
  exemption, then reading **`inherit` in both**. `inherit` is the same value step 7.2 found here before
  M1 and called *declaring nothing*. **Zero retention is declared in one of the three Regions a prompt
  is processed in.** Whether cross-Region inference obeys the source Region's mode or the
  destination's is in no API and on no vendor page. Decision 16; the repair does not wait on the
  answer and needs `bedrock:PutAccountDataRetention` in the exemption first.

### The session, and both channels read

- **[user] Edited `/etc/claude-code/managed-settings.json` inside the container** — `0444`, so
  `sudo` — pointing all three aliases at Haiku 4.5, the one scoped model this account can invoke.
  Restarted the session. **It answered.** A measurement, not a configuration: it lives in the
  container's writable layer, dies with the app, and diverges from what the image declares
  (Lesson 35's shape).

- **[Claude] CloudTrail, fifteen `InvokeModelWithResponseStream` with no `errorCode`**, each
  `vpcEndpointId: vpce-0171b785473053321`, `sourceIPAddress: 10.20.60.99`, the project role as
  `userIdentity`, `requestParameters.modelId` = `us.anthropic.claude-haiku-4-5-20251001-v1:0`, and
  **`responseElements: null`** — attribution without content, measured rather than asserted. **One
  invocation writes two events**, one carrying `modelId` and a sibling carrying
  `requestParameters: {}`, so counting doubles and filtering on `modelId` halves. Event History lagged
  several minutes on the successes while the denials had appeared promptly.

- **[Claude] `/awsds/prod/proxy` over the same hour: no `bedrock` line and no Anthropic name** — with
  the negative control that makes the absence mean something (Lesson 62). The space's own
  `10.20.60.99` is in that window, tunnelling `idetoolkits-hostedfiles.amazonaws.com` and refused
  `default.exp-tas.com` with `403 TCP_DENIED`. The instrument was watching.

- **What 6.4 did not get.** The session pinned all three aliases to one model, so its accounting
  separates neither the scoped set nor primary from background. Re-run once decision 14 settles.

### What this sitting changed in writing

`claude-code-sagemaker.md` §M gains **M0** (where the models run), **M4** (the agreement) and **M5**
(the Region exemption) and keeps M1-M3's numbers, which other files reference; M1 becomes per Region,
M2 stops claiming to enable a model, and §V opens with the warning that no reading here answers
whether a model is invocable. `AWS_STATE.md` `EXC-07` loses the clause that rested on the unmeasured
premise and `EXC-08` is new; `INV-12` records the `Interactive` divergence. Five entries join
lessons.md's platform-behaviour list. The stage's step 6 carries its verdicts, 0.9 and 7.3 their
corrections, question 9 closes by measurement, and decisions **14**, **15** and **16** open.

## 2026-09-12 — decisions 14, 15 and 16, and the code they land in

*The decisions are the user's, taken in the sitting; the measurements and the authored changes are
Claude's. No AWS write: the grant, the SCP and the image all need an apply that has not run.*

- **[user] Decision 14: the scoped set is the 4.5 generation** — Opus 4.5, Sonnet 4.5, Haiku 4.5, the
  three proven by invocation. **[Claude] Written into all the consumers of that one list**:
  `sandbox/bedrock/`'s `models` map, `images/dev-env/claude-code/managed-settings.json`, the
  Dockerfile's per-key comment, and the runbook's §I block, which is checked byte-identical to the
  file the image ships. The endpoint policy is action-scoped only, so it does not move.

- **[Claude] The switch costs one model's rate and only one, measured rather than assumed.** From
  each model's agreement rate card, `USW2_InputTokenCount` / `USW2_OutputTokenCount` per 1M tokens:
  Opus 4.5 is **5.50 / 27.50**, identical to Opus 5; Haiku 4.5 is **1.10 / 5.50**, unmoved; Sonnet
  goes **2.20 / 11.00 → 3.30 / 16.50**, half as much again. `PRICING.md` now carries both sets — what
  is paid today and what would be paid if the gate opens — rather than replacing one with the other.

- **[Claude] Decision 15's two statements are written and unapplied**, in
  `awsds-org-scp-ou-interactive.json` rather than the root document: the hole was opened on that OU
  and the compensation belongs in the same scope.
  - `DenyBedrockInvocationOutsideTheScopedModels` is a `NotResource` ceiling over the six ARNs. It
    exists because `sandbox/bedrock/` is a **floor** and the blueprint can widen what it allows
    without this repository being asked; a ceiling and a floor are two intents sharing one list
    (Lesson 51), which is worth naming rather than discovering. The profile ARNs carry a wildcard
    account — an account id may not appear in a tracked file, and an inference-profile ARN is always
    the caller's own — and the foundation-model ARNs carry no region, because the profiles route to
    three.
  - `DenyBedrockReadsOutsideTheRoutedRegions` puts back the axis the Control Tower lever cannot
    express. `NotActions` has no resource and no region dimension: it lifts the ceiling for those
    actions everywhere. **The two retention actions are deliberately outside this condition** —
    decision 16 declares the mode in every Region, so a Region condition here would forbid the calls
    that keep it declared. The mode axis guards them instead, in 7.5.
  - Both rows are in `POLICIES.md`; `./scripts/check-index.py` reads clean. The document is 1,827
    bytes against the 5,120 SCP limit.

- **[user] Decision 16: declare `mode: none` in every enabled Region**, not only the routed three.
  **[Claude] The routed list is readable programmatically** — M0's `get-inference-profile`, parsing
  the Region out of each `models[].modelArn` — so the narrow option was available and was refused on
  a race rather than on a limitation: AWS owns the routing and can add a Region under a pinned model
  id, and between that change and the next reading a prompt is processed where nothing is declared.
  **Measured the same day: `get-account-data-retention` answers in all 17 enabled Regions**, reading
  `inherit` in sixteen and `none` in `us-west-2`. The broad option costs 17 one-time calls and turns
  `INV-18` into an invariant that needs no knowledge of the routing.

- **[Claude] The order matters and is written into the decision.** 7.5's mode deny goes **first**: it
  permits `none` and forbids every other value, which is what makes the next step harmless. Then
  `bedrock:PutAccountDataRetention` joins M5's exemption — the write is refused outside `us-west-2`
  without it. Then the sixteen writes. Then the reading in `./aws/bedrock.py`, which enumerates
  Regions rather than carrying a list, because a Region opted into later starts at `inherit`.

## 2026-09-12 — the two applies, and an instrument for the drift neither can see

*Both applies authorized by the user in the sitting and run by Claude, as the infrastructure user:
`sandbox/bedrock/` on `Sandbox` with `InfrastructureAccess`, `identity/org-policies/` on `Identity`.
The two verification invocations are Claude's, under the same authorization.*

- **[Claude⚡] `sandbox/bedrock/` — decision 14's grant half.** `0 to add, 1 to change, 0 to destroy`:
  a **new policy version**, not a replacement, so the attachment never moved and no project lost
  access for a moment. Re-plan `No changes`. The outputs show the six ARNs moving to the 4.5
  generation.

- **[Claude⚡] `identity/org-policies/` — decision 15's two statements.** `0 to add, 1 to change, 0 to
  destroy`, the `Interactive` document alone, **390 → 1,362 bytes** minified; the other nine
  documents untouched. Re-plan `No changes`.

- **[Claude⚡] The deny was exercised, not merely attached** (Lesson 5), with a before/after control
  on the **same principal and the same call**: `amazon.nova-lite-v1:0` answered for
  `InfrastructureAccess` an hour earlier and now returns *"explicit deny in a service control policy:
  …/p-tgda7n58"* — `awsds-org-scp-ou-interactive`. The positive control beside it:
  `us.anthropic.claude-haiku-4-5-20251001-v1:0` still answers. Owed: the full battery run and its
  rows (`scp-battery.md`).

- **[Claude] `aws/bedrock-scope.py` is new**, at the user's request. It reads the **declaration out of
  the SCP** rather than carrying a constant — the models from `DenyBedrockInvocationOutsideTheScoped
  Models`' `NotResource`, the Regions from the other statement's condition — because a script with
  its own copy is one more consumer of a list that already had four. It watches the two facts that
  are AWS's rather than ours: a profile's routing, which can change under a pinned model id with no
  diff here, and whether each model still holds an agreement. First run: **`BS-1`..`BS-5` and `BS-7`
  pass, `BS-6` fails on sixteen Regions at `inherit`** — which is decision 16, reported by an
  instrument instead of by memory.

- **[Claude] A defect in this script, found by its own first run.** `BS-6` read `None` in every
  Region including the one known to be `none`: the response field is **`mode`**, not
  `dataRetentionMode`, and a `--query` naming the second returns `None` — which reads exactly like a
  Region that answered and declared nothing. Fixed and re-run. The runbook's M1 now names the field.

- **[Claude] The order in decision 16 was wrong and is reversed.** M3's deny is
  `StringNotEquals` on `bedrock:DataRetentionMode`, and **a `StringNotEquals` whose key is absent
  from the request evaluates true**. Whether `PutAccountDataRetention` publishes that key at request
  time is unverified — 7.5 says so itself, and `validate-policy` establishing that a key is in the
  service's catalogue is a different claim. Attaching M3 first would therefore risk denying every
  retention write including `--mode none`, stranding the Regions that still need one. The order is
  now: the exemption, the writes, M3 **last**, and a positive control that `--mode none` still
  succeeds afterwards. **7.5's statement was deliberately not written in this sitting** for that
  reason.

## 2026-09-12 — decision 16 executed, 7.5 attached, and `default-v0.4.0` delivered

*One sitting, three acts, each with a measurement in front of it and a reading behind it. Two
findings came out of it that nobody was looking for: a check that had been reporting `pass` about the
wrong models for a day, and a space that carries its own copy of the image version number.*

### Decision 16 — the retention mode, everywhere

- **[Claude] The before-reading, 17 enabled Regions**: `none` in `us-west-2`, **`inherit` in the
  other sixteen**. The *read* answered in all seventeen, which confirmed that the
  `bedrock:GetAccountDataRetention` the user had already added to the Control Tower `NotActions` was
  in force.

- **[user] The negative control, before the console act.** The runbook had *predicted* that the
  Region ceiling refuses the write outside `us-west-2`; that was deduced from the `NotAction` list,
  never exercised. Run by hand, verbatim:

  ```
  aws bedrock put-account-data-retention --mode none --region us-east-1 --profile awsds-infra-sandbox-1

  aws: [ERROR]: An error occurred (AccessDeniedException) when calling the PutAccountDataRetention
  operation: User: … is not authorized to perform: bedrock:PutAccountDataRetention with an explicit
  deny in a service control policy: …/p-umksvu5a
  ```

  The measurement was worth taking for its own sake and for a second reason: had it **succeeded**,
  the console act below would have been unnecessary.

- **[Claude] `p-umksvu5a` is `aws-guardrails-fzqpfF`**, the Control Tower document on the
  `Interactive` OU — **the same id [D37](../plan/decisions/D37-nested-ou-inheritance.md) recorded in
  Stage 1c**, when the `us-east-1` deny inside Sandbox named `Interactive`'s Region policy rather
  than `Sandboxes`' own. An identifier from a year-old reading closed with one taken today.

- **[Claude] The Control Tower document is readable from `Identity`**, and this is new. The
  *control* API answers from `Management` alone, but the SCP the control writes is an Organizations
  document: `organizations describe-policy --policy-id p-umksvu5a --profile awsds-infra-identity`
  returns its content. Before the console act it carried **91** `NotAction` entries — the template's
  86 plus the user's five.

- **[user] `bedrock:PutAccountDataRetention` added as the sixth `NotAction`**, by console, as **AWS
  Control Tower Admin** on **Management**. Region list left at `us-west-2`; exempted principals left
  empty.

- **[Claude] The console act verified by reading the policy, not by re-attempting the call.**
  **91 → 92**, the six `bedrock:` entries present. This matters because the obvious verification is
  not an instrument: a re-attempted call is refused whether the form failed to propagate or something
  else in the chain is missing (Lesson 24).

- **[Claude⚡] The writes: `put-account-data-retention --mode none` in all 17 enabled Regions.**
  17 of 17 accepted. After-reading: **`none` everywhere**, `updatedAt` between 15:31:45Z and
  15:32:02Z. The write is accepted in a Region already at `none` and stamps a fresh `updatedAt`, so
  the loop is safe to re-run and the timestamp is not evidence a Region had drifted.
  `./aws/bedrock-scope.py` `BS-6` green, 7 of 7 checks passing.

- **[Claude] The exemption widened something, and it is written down where it lands.** The five
  earlier `NotActions` are reads. The sixth lets **any principal in the `Interactive` OU** set the
  retention mode in **any Region**, `inherit` included. Until today the Control Tower ceiling confined
  that write to `us-west-2` **as a side effect nobody designed**, and decision 16 traded that
  accidental confinement away. From here 7.5 is the only thing holding the mode.

### A check that was reporting `pass` about the wrong models

- **[Claude] `aws/bedrock.py` carried a fifth copy of the scoped set**, and it still named
  `claude-opus-5` and `claude-sonnet-5` — the generation decision 14 abandoned the day before. Its
  `BR-4` ("every scoped model has an ACTIVE us. profile") read **`pass`**, truthfully, about three
  profiles nobody had scoped: the `us.` profiles for Opus 5 and Sonnet 5 exist and are `ACTIVE`, they
  are simply not invocable in this account. A green check about the wrong subject (Lesson 31's
  neighbour).

- **[Claude] The constant was removed rather than corrected.** The SCP reader moved to
  `aws/awslib/bedrockscope.py` and both `bedrock.py` and `bedrock-scope.py` read it, so the estate is
  back to one declaration. With the document unreadable — standalone in CloudShell — `BR-4` now
  **fails naming why** instead of passing on an empty set.

### Step 7.5 — the mode ceiling and the retaining-model deny

- **[Claude] The mode enum has four values, not the two this plan discussed**: `default`, `none`,
  `provider_data_share`, `inherit`. **`provider_data_share` is the value the requirement is about**,
  and no file here had named it. The condition is unchanged — `StringNotEquals` against `none`
  catches the other three, and naming the one mode to permit cannot go stale where a list of modes to
  forbid would.

- **[Claude] The premise was tested before the root document was touched.** `awsds-org-scp-baseline`
  is attached at the **root**, so it already reaches `Policy Canary`: there is nothing to park, and an
  amendment that turned out to be a blanket deny would have stranded every retention write in the
  organization at once, `--mode none` included. The statement was therefore tested **on its own**, as
  a throwaway document — `canary/awsds-canary-scp-bedrock-retention-mode.json`, the real statement
  verbatim rather than phase 1's inverted shape — created as **`p-ojm4ldiw`** and attached to the
  **`Policy Test` OU**.

- **[Claude⚡/user] Three calls in `Policy Canary`, `us-west-2`.** Claude ran call 0; the user ran the
  attach, calls 1 and 2, and the cleanup, because the classifier declined the policy attachment:

  | # | Call | Result |
  |---|---|---|
  | 0 | `--mode none`, **nothing attached** | succeeded, `updatedAt` 15:56:38Z |
  | 1 | `--mode none`, **document attached** | succeeded, `updatedAt` **16:05:22Z** — a fresh stamp, so a write and not a no-op |
  | 2 | `--mode inherit` | `AccessDeniedException … explicit deny in a service control policy: …/p-ojm4ldiw` |

  **`PutAccountDataRetention` publishes `bedrock:DataRetentionMode` at request time.** Call 0 is what
  makes call 2 attributable; the named policy id is what makes it attributable to *this* document.
  Detached and deleted in the same sitting.

- **[Claude⚡] `identity/org-policies/` applied**: `0 to add, **2 to change**, 0 to destroy`. The
  baseline document updated **in place**, id `p-1fp032g8` unchanged, so the root attachment never
  moved and there was no instant without a baseline — **1,651 → 2,395** minified bytes against the
  5,120 ceiling. The second change is the `Interactive` document's *description*, which still named
  `Development` in an OU it left at 6b and named neither statement decision 15 had added. Re-plan
  `No changes`.

- **[Claude⚡] Re-probed where it lives**, not read back from the document:

  | Probe | Result |
  |---|---|
  | `--mode none` | succeeded, `updatedAt` 16:18:02Z |
  | `--mode inherit` | refused, naming **`p-1fp032g8`** — the baseline, not the deleted throwaway |
  | `invoke-model` on `us.anthropic.claude-fable-5` | refused, same id, **on the inference-profile ARN** |
  | `sts get-caller-identity`, `s3api list-buckets`, `ec2 describe-vpcs` | all three succeed |
  | `invoke-model` on `us.anthropic.claude-haiku-4-5-20251001-v1:0`, from `Sandbox` | **answered** |

  The last row is the one to keep. The failure these statements could cause is not a retaining model
  answering — it is the **scoped set going dark** from a resource list written one character wrong,
  and the canary cannot test it because it holds no agreement.

- **[Claude] Six resource ARNs, not two, and the probe justified it.** The refusal named
  `…:inference-profile/us.anthropic.claude-fable-5` — the **profile** ARN, not a foundation-model one.
  A statement listing only the two model ids would have left open exactly the route an invocation
  takes. Both Fable models have a `us.` **and** a `global.` profile, all four `ACTIVE`.

### `default-v0.4.0` — the pins delivered

- **[Claude] What `v0.3.0` was shipping, measured against the repository.** The image attached to the
  domain pinned `ANTHROPIC_MODEL` and `ANTHROPIC_DEFAULT_OPUS_MODEL` to `us.anthropic.claude-opus-5`
  and `ANTHROPIC_DEFAULT_SONNET_MODEL` to `us.anthropic.claude-sonnet-5`, with `availableModels`
  locked to `["opus","sonnet"]` — **a picker offering exactly the two models that refuse**, with the
  working Haiku not selectable. That is the symptom the user reported on 2026-09-12, now with a cause
  rather than a mystery; and since decision 15's apply those two pins are denied by **two independent
  things**, the commercial gate and this estate's own `NotResource`.

- **[user] `default-v0.4.0` built on the buildbox and pushed**, `dev-env`
  `sha256:ba1b395ea8b035c5a2f770e92c6fcefda5d14fa180479ed25eea0df44f2f2636`,
  **7,182,170,437 bytes against `v0.3.0`'s 7,182,175,890 — 5,453 fewer**. That delta is the sanity
  reading: a four-string edit in a JSON file is kilobytes, and a layer nobody asked for would be
  megabytes.

- **[Claude] `./aws/devenv.py` before the bump**: `DE-1`..`DE-4` pass, 52 entries, sha256
  `fc11caaa3145fdef` on both sides — the proxy list is the same in `v0.4.0`, which is what a pins-only
  release should show.

- **[Claude⚡] The §B chain.** No app was running, so step 1 had nothing to delete. Detached — the
  block generated from the **live read**, all ten keys preserved and only the two `CustomImages`
  arrays emptied, because `update-domain` is full-replace (Lesson 60). Applied for
  `1 to add, 0 to change, 1 to destroy`, `base_image` forcing replacement. **Version 4's
  `ContainerImage` read back against the pushed digest and matched.** Re-attached from the slice's own
  output, so no version number was typed. Domain `InService`, both app types on version 4, re-plan
  `No changes`.

### The finding nobody was looking for: a space carries its own version number

- **[Claude] `remote-editor-claude` pins `…:image-version/awsds-sandbox-dev-env/3`** in its own
  `SpaceSettings.CodeEditorAppSettings.DefaultResourceSpec` — **and version 3 no longer exists**, the
  apply having destroyed it. The domain's `DefaultUserSettings` is what a **new** space reads; an
  **existing** space carries a copy written when it was created, and that copy overrides the domain
  default.

- **[Claude] `dev-env.md` §B did not cover this.** Its only neighbouring sentence is *"A new space. A
  running app keeps the image it started with"*, which is about the **app**, not the space. Every
  version bump from here strands every space that pinned the previous version, and the number of
  spaces only grows.

- **[user] Left unrepaired on purpose** (2026-09-12): *"Não precisa ajustar o space antigo por
  enquanto. Eu vou ver como ele se comporta e criar um space novo para testar a imagem nova."* So the
  behaviour of an app started against a destroyed image version becomes a **measurement this stage
  does not yet have**, and the new space is what exercises `v0.4.0`.

- **[Claude] The other space is unaffected**:
  `default-28f1b390-…` runs AWS's own `sagemaker-distribution-cpu` by **alias `4.3`**, not our image.
  That contrast is the design observation: **an alias survives a version bump, a version ARN does
  not**, and `aws_sagemaker_image_version.dev_env` currently sets `aliases = []`. Whether to give the
  estate's versions aliases is a decision this log records and does not take.

## 2026-09-12 — verification (x) answered, a false negative explained, and `DE-5`

*The evening after `v0.4.0` landed. Two spaces behaved differently on what looked like the same image,
and the question put was whether the build had skipped a step. It had not; the space had been created
on another image. The readings that settled it are now an instrument.*

### The stranded space, and the first session on the image's own pins

- **[user] The space left naming the destroyed version did not start.** Verbatim: *"Sobre o espaço
  que estava com a imagem antiga, ele falhou em iniciar. Editei as configurações do espaço alterando
  para a imagem na versão nova e agora ele subiu corretamente."* This closes the measurement `EXC-09`
  had left open: **an app started against a destroyed image version fails to start**, with no
  fallback to the domain default. The repair was made **in the portal**.

- **[user] A session on the repaired space, reading the pins from the image.** Internet reachable, the
  proxy variables present; the *Claude Code for VS Code* extension installed; a **Sonnet 4.5** prompt
  asking for a Python hello-world project worked. The picker showed *"Default (Opus 4.5), Sonnet 4.5 e
  Opus 4.5. Não vi o Hayku."*

- **[Claude] The picker is the settings file, exactly.** `availableModels: ["opus","sonnet"]` locks it
  to those two, "Default" is `ANTHROPIC_MODEL` (Opus 4.5), and Haiku is pinned through
  `ANTHROPIC_DEFAULT_HAIKU_MODEL` for background work only — not selectable, by design. The pins came
  from the image rather than from the earlier hand edit: `/etc/claude-code/` is in the container's
  filesystem, rebuilt from the image at every app start, where the home directory is what persists.

### A new space with no proxy, and the question of a skipped build step

- **[user] The report and the question.** A new space on the new image *"aparentemente não tem as
  configurações de variáveis de ambiente de proxy, então ele não tem acesso à internet. Ao fazer o
  build da última versão da imagem, eu não executei nenhuma etapa de atualização de variável de
  proxy.. Será que deixei de executar alguma etapa do build da imagem?"*

- **[Claude] Answered from the repository before any AWS reading, the session having expired.** The
  proxy is not a build step: `PROXY_URL` and `NO_PROXY_LIST` are `ARG`s **with default values** and the
  Dockerfile's last `ENV` bakes them on any plain `docker build`. A step exists only when Sandbox's
  endpoint set changes, and `DE-3` had just read the list unchanged. The decisive evidence was the
  other space: **the repaired space ran the same digest and had the variables**, so the difference was
  between the spaces, not in the image. Two hypotheses were put, each with a discriminator — the new
  space on another image (`cat /opt/awsds-proxy.txt`, which only this image writes), or the repaired
  space's variables coming from its persistent home rather than the image (`grep -in proxy
  ~/.bashrc ~/.profile ~/.bash_profile`).

- **[user] The first hypothesis, confirmed by hand.** *"O problema era mesmo a imagem: na criação do
  segundo espaço eu selecionei de forma errada a imagem padrão do SageMaker. Criei um novo space
  selecionando a imagem correta e agora funciona."* The user signed in again as the infrastructure
  user.

### The readings, taken afterwards

- **[Claude] Four spaces, and what each app actually runs** — `describe-app`'s `ResourceSpec`, which
  is the image an app started on, not the space's default:

  | Space | Created (UTC-3) | Image the app ran | `RemoteAccess` |
  |---|---|---|---|
  | `remote-editor-claude` | 01:56 | `awsds-sandbox-dev-env` version 4 | `ENABLED`, 64 GB |
  | `remote-editor-claude-v4` | 17:40, **deleted** | **`sagemaker-distribution-cpu`, alias `4.3`** | — |
  | `remote-editor-claude-v4-2nd` | 18:38 | `awsds-sandbox-dev-env` version 4 | `DISABLED`, 16 GB |
  | `remote-editor-claude-v4-3rd` | 18:52 | `awsds-sandbox-dev-env` version 4 | `ENABLED`, 64 GB |

  **`describe-app` still answered for the deleted app**, which is what made the attribution possible
  after the space was gone. The portal edit of `remote-editor-claude` kept `RemoteAccess`, the 64 GB and
  the project's S3 connection.

- **[Claude] The image's baked `Env`, read from the registry rather than from any space.**
  `batch-get-image` on `default-v0.4.0` gave a manifest naming config blob `sha256:7fd2620c…`;
  `get-download-url-for-layer` and one HTTPS GET returned it, and **its sha256 matched that digest**.
  Its `Env`: `http_proxy`, `https_proxy`, `HTTP_PROXY`, `HTTPS_PROXY` =
  `http://proxy.awsds.internal:3128`; `no_proxy`, `NO_PROXY` = **52 entries, sha256
  `fc11caaa3145fdef`**. The build baked all six. The Sandbox infrastructure role reads Production's
  repository by digest, so the reading needs one profile.

### What was built from it, and what it corrected

- **[Claude] `./aws/devenv.py` gained `DE-5`**, at the user's go-ahead: the latest image version's
  `ContainerImage` digest → its manifest → its config blob, hash-checked, → the six variables, compared
  with the account's list. `DE-3` compares the *recipe*, so an image built from an older checkout
  passes it while the domain serves something else; `DE-5` reads the bytes. First run: **`DE-1`..`DE-5`
  pass**. **Negative control**, through the script's own `fetch()` and `PROXY_NAMES`:
  `default-v0.1.0`, which predates the proxy `ENV`, reads **no proxy variable**; `v0.4.0` reads all
  six. The instrument distinguishes the two outcomes.

- **[Claude] A claim of mine withdrawn: "`update-space` is full-replace like `update-domain`".**
  Written into `dev-env.md` §B step 6 earlier the same day, from inference. It is **not measured**, and
  the portal edit keeping every field settles nothing about the API, since the portal may send the
  whole block itself. The step now says so, and its CLI route is marked written-and-not-run; the recipe
  was already correct under either behaviour, because it transforms the live read.

- **[Claude] The claim that caused the surprise, found in three places.** *"A space cannot name an
  image"* stood in `docs/SMUS.md` (corrected in the previous sitting), in **`dev-env.md` §O** — the
  runbook that drives the bump, adding *"the answer to can we do this per space is no"* — and in a code
  comment in `terraform-live/sandbox/dev-env/main.tf`. All three now say what was measured: a space
  names no image *list*, so the domain decides what the picker offers, and it names **one image and one
  version** in `DefaultResourceSpec`, so the space decides what it runs. The comment on
  `aws_sagemaker_image_version` now states that its destroy strands every space that named it.

- **[Claude] Two more sentences corrected before they were committed.** `dev-env.md` §C7 was first
  written saying the SageMaker Distribution is *what the portal form selects* and that a portal space
  *has `RemoteAccess` off*. Neither was measured: the first is the user's report of picking the default
  image, and the second is one of two spaces' recorded settings. Both now say exactly that.
