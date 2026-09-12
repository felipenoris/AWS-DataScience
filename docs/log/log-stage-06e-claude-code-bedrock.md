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
