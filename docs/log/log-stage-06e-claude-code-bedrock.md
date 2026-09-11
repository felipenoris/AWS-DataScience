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

- **[Claude] The procedure is `claude-code-sagemaker.md` §P**, in both forms the user asked for:
  P1 finds the role name and tells two projects apart by tag, P2 is the Terraform path, P3 the
  `aws iam attach-role-policy` equivalent with the warning that it leaves drift the next plan would
  revert (Lesson 35), P4 verifies and says what a verification here cannot say.
