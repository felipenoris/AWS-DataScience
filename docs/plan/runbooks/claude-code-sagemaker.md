# Runbook — Claude Code on Bedrock, inside a SageMaker space

*The stage that builds this is [`stage-06e-claude-code-bedrock.md`](../stages/stage-06e-claude-code-bedrock.md);
the channel it runs inside is [`remote-ide.md`](remote-ide.md); the image that delivers its configuration
is [`dev-env.md`](dev-env.md).*

**This file is written for two audiences that do not overlap.** The infrastructure engineer configures
this once for everyone and never opens the IDE; the data scientist opens the IDE and never touches an
account. Read your own half.

| Section | Audience | What it holds |
|---|---|---|
| **§M** | infrastructure | enabling the model: the retention mode and the use-case form |
| **§I** | infrastructure | what the infrastructure configures: the endpoints, the grant, the image |
| **§U** | the data scientist | what the user configures, and what a user cannot change |
| **§V** | both | reading it back, one instrument per question |

**State, 2026-09-11.** **§M is done** — M1 at 22:31 UTC, M2 by console the same evening — except M3,
the deny that freezes M1. The readings are in
[`log-stage-06e`](../../log/log-stage-06e-claude-code-bedrock.md). §I is designed and **not built**:
no endpoint, no grant, no image carrying the settings. §U describes a surface no space offers yet.
Every sentence below that describes something unbuilt says so.

---

## §M — Enabling the model

Two acts, in this order, in the account that will invoke. Both are `Sandbox` only, by decision 2:
principle 1 keeps `Management` bootstrap-only, and an org-wide form would open Anthropic models in
five accounts where D17 says no interactive compute runs.

**The identity for both:** the **infrastructure user**
(`felipenoris+infrastructure_user@…`), account **Sandbox**, permission set **InfrastructureAccess** —
the CLI profile `awsds-infra-sandbox-1`, and the same identity picked in the browser for the console
half. That set is `AdministratorAccess` alone and carries **no `DenyControlPlaneOffVpn`**, so neither
act needs the VPN. Check before, not after:

```bash
aws sts get-caller-identity --profile awsds-infra-sandbox-1
```

### M1 — Declare the account's data retention mode

**Why first.** A fresh account reads `mode: inherit`, which the API documents as *no data retention
mode is set at this scope* — so the requirement rests on each model's own default and on nothing this
estate has said. Setting it before the form means the first access ever granted arrives with the
account already declaring zero retention (Lesson 5: an intention is not a control).

**Before-reading.** Expect `inherit`, with no `updatedAt`:

```bash
aws bedrock get-account-data-retention --region us-west-2 --profile awsds-infra-sandbox-1
```

**The call.** One write, reversible by setting the mode back:

```bash
aws bedrock put-account-data-retention --mode none --region us-west-2 --profile awsds-infra-sandbox-1
```

**After-reading.** Expect `none`, now with an `updatedAt`. Re-run the before-reading command.

**What `none` costs, and what no reading here shows.** The vendor's design is that a model whose
minimum retention mode is above `none` becomes **unavailable in this account** rather than quietly
retaining. **Nothing in the control plane shows that happening.** Measured 2026-09-11 with the account
already at `none`: all thirteen Anthropic models in `us-west-2` read
`AUTHORIZED / AVAILABLE / AVAILABLE`, including `claude-fable-5` and `claude-fable-5-1`, the two the
vendor names as retaining every prompt for 30 days with human review; the agreement offer's
`termDetails` carries pricing, legal and support terms and nothing about retention. So the mode's
effect is **presumed to land at the invocation and has not been seen**. The only negative control that
would settle it is invoking a retaining model and reading the refusal — stage step 7.2a, not yet run.

**There is no Terraform for this.** `hashicorp/aws` 6.60.0 declares nine `aws_bedrock_*` resources and
none wraps the retention API; the CloudFormation registry carries 29 `AWS::Bedrock::*` types and none
is an account setting, so `awscc` offers nothing either (measured 2026-09-11). The provider binary
does contain `bedrock.PutAccountDataRetentionInput` — that is the bundled Go SDK, not a provider
surface, and a `strings` grep over it is a false positive. **This joins account-level BPA on the list
of account settings this estate manages by hand**, and what keeps it in place is the SCP of stage step
7.5, not a plan.

### M2 — Submit the model-access form

**What it is.** A declaration on AWS's record, not an approval queue: the vendor states that *access
is granted immediately after submission*. Nobody reviews the answer before the model works, which is
why it is worth writing carefully rather than quickly. Submitted **once per AWS account**.

**Before-reading.** Expect the refusal — it is the negative control for the after-reading:

```bash
aws bedrock get-use-case-for-model-access --region us-west-2 --profile awsds-infra-sandbox-1
# ResourceNotFoundException: You have not filled out the request form.
```

**The console path**, as the vendor documents it:

1. Sign in to the access portal as the infrastructure user and open **Sandbox / InfrastructureAccess**.
2. Open the Amazon Bedrock console and **set the Region to `us-west-2`** before anything else.
3. Open **Model catalog** and select an Anthropic model — Claude Opus 5.
4. Complete the use case form and submit it.

**The answers.** Settled by the user 2026-09-11; write the exclusions as well as the inclusions,
because a use case stated only as what it is admits every reading of what it is not.

| Field | Value |
|---|---|
| `companyName` | the institution's name |
| `companyWebsite` | its site |
| `industryOption` | **Banking / Financial Services** — the catalogue's nearest label; use `otherIndustryOption` only if no banking label exists |
| `intendedUsers` | the institution's data scientists — internal only, no external or public exposure |
| `useCases` | data-science work: a coding assistant inside the institution's own development environment; code comprehension, refactoring, test writing and documentation over internal repositories; exploratory analysis support in notebooks. **No customer-facing application, no automated decisioning, no credit or risk scoring, no content generation for publication** |

**After-reading.** The same command must stop returning `ResourceNotFoundException` and return a
`formData` blob. That is the whole verification. `get-foundation-model-availability` is **not** the
instrument: it reads `authorizationStatus AUTHORIZED` with the form unsubmitted, and it was read
identically before the form, after it, and after the retention mode changed.

**Reading the record back.** `formData` is **double base64 over a flat JSON object** of the six fields,
so what the account declared is recoverable despite the API calling it a blob:

```bash
aws bedrock get-use-case-for-model-access --region us-west-2 --profile awsds-infra-sandbox-1   --query formData --output text | base64 -d | base64 -d
```

Read it back after submitting. The console appears to share one input between `otherIndustryOption` and
`useCases`, so a form submitted with the first empty can leave a `". "` at the head of the second.

**Why not Terraform, and why not org-wide.** `aws_bedrock_use_case_for_model_access` exists, and its
entire schema is one required attribute, `form_data (string)`. The form was submitted by console
(decision 10) on the argument that a blob is unreviewable in a diff — **and the read-back above shows
that argument was wrong**: the encoding is known, so the org-wide form could be authored and checked
field by field. The org-wide shape
(`PutUseCaseForModelAccess` from `Management`, which the vendor says extends to child accounts
automatically) is the right one the day a second account needs a model; the cost of deferring it is
one more form.

### M3 — Freeze the mode

M1 is a setting anyone with the permission can change back. The control that keeps it is a deny on
`bedrock:PutAccountDataRetention` where `bedrock:DataRetentionMode` is not `none`, in
`awsds-org-scp-baseline.json` (decision 4), attached at the root — **which reaches every account and,
like every SCP, does not restrict `Management`**. The condition key was confirmed to exist on
2026-09-11 with `accessanalyzer validate-policy` and a deliberately bogus key beside it as the
control. Attaching it re-runs the battery and adds its rows to `POLICIES.md` in the same sitting
([`scp-battery.md`](scp-battery.md)). **Not done.**

---

## §I — What the infrastructure configures

**None of this is built.** It is the design the stage's steps 3, 4 and 5 carry, recorded here so the
two halves of the configuration are in one place.

- **The private path** (stage step 4). `bedrock-runtime` and `bedrock` as interface endpoints in the
  Sandbox VPC, through a new `bedrock-llm` group in `terraform-modules/vpc-egress`, ~USD 0.010/h each.
  **The endpoints and the `NO_PROXY` bypass list are one change in two places** (Lesson 33): an
  endpoint without the bypass entry sends the call to the proxy and out to the internet, and the call
  still works, which is how it fails silently. The generated list is the slice output; the value a
  process actually reads is the dated literal in `images/dev-env/Dockerfile` (6d decision 8).
- **The grant** (stage step 3). Measured 2026-09-11: the project role's every `InvokeModel*` allow
  lands on `foundation-model/*` and **none on the system inference profile**, and
  `ListInferenceProfiles` is granted nowhere — so a grant is needed. It names the three `us.` profile
  ARNs and the three region-less foundation-model ARNs; **both groups are required**, because
  authorization is evaluated against the profile and against each model it routes to. The
  foundation-model ARN carries no region on purpose: the profile routes to three of them, so a
  region-pinned ARN would authorize a third of the requests and refuse the rest by geography.
- **The endpoint policy** (4.4), narrowed to those actions on those resources, so the endpoint states
  the same intent independently of the identity policy.
- **The configuration** (5.2), in `/etc/claude-code/managed-settings.json`, written by the image.
  Managed settings sit above every other level and nothing a user writes overrides them.
- **The picker** (decision 3): `availableModels` locks `/model` to the scoped set, so nothing outside
  the declared use case and the resource scope is reachable.
- **The background model** (5.3): `ANTHROPIC_DEFAULT_HAIKU_MODEL` is the only key that moves session
  titles off the primary model. Without it a session that sets `ANTHROPIC_MODEL` runs them on
  **Opus 5**, at 27.50 per 1M output tokens, for work a Haiku does.

---

## §U — What the user configures, and what a user cannot change

**No space offers this yet**; the image that carries it is stage step 5.4.

- **Install the extension into the remote session**, not into the portal's Code Editor. A space runs
  two IDE servers with separate extension directories and settings ([`remote-ide.md`](remote-ide.md)
  §E), and an extension installed in the wrong one is invisible to the other.
- **Disable Login Prompt** (`claudeCode.disableLoginPrompt`) is a **VS Code** setting, not a Claude
  Code one, so it is set once per surface: `~/.vscode-server/data/User/settings.json` for the remote
  session and `~/sagemaker-code-editor-server-data/data/User/settings.json` for the Code Editor. A
  configuration that works in one surface and not the other is this file's most common failure.
- **What the institution owns, and an attempt to override is ignored rather than refused** — which
  reads exactly like the setting not working: the provider, the Region, the model pins and the
  picker's contents. Two consequences worth knowing before they surprise someone:
  - `/setup-bedrock` and the login wizard write to `~/.claude/settings.json`, which managed settings
    sit above. The wizard will appear to succeed and change nothing.
  - When a pinned model is older than the client's own default, Claude Code **offers to update the
    pin** and writes the new id to the user settings file on acceptance. Here that write is inert.
    The pin moves when the image moves.
- **Two tools behave differently on Bedrock**: WebSearch is **not available at all**, and `/logout`
  is unavailable because authentication is the container's AWS credentials.
- **Nothing needs to be exported.** In a space the container already carries the project role's
  credentials and the SDK's default chain finds them. The vendor's fifth credential option, an Amazon
  Bedrock API key (`AWS_BEARER_TOKEN_BEDROCK`), is a long-lived credential and principle 2 admits none
  anywhere in this estate — it is refused here, not weighed.

---

## §V — Reading it back

**The whole picture in one command.** [`./aws/bedrock.py`](../../../aws/bedrock.py) photographs what
Bedrock is enabled for in every account that has a profile — the gates, the catalogue, the inference
profiles and anything that would be billing — and writes `aws/output/bedrock.txt`. Run it rather than
re-deriving the calls below; the calls are here because a runbook that only names a script stops
working the day the script does.

```bash
./aws/bedrock.py
```

### Listing what is enabled, by hand

The account gates, one call each:

```bash
aws bedrock get-use-case-for-model-access --region us-west-2 --profile awsds-infra-sandbox-1
```

```bash
aws bedrock get-account-data-retention --region us-west-2 --profile awsds-infra-sandbox-1
```

```bash
aws bedrock get-model-invocation-logging-configuration --region us-west-2 --profile awsds-infra-sandbox-1
```

Every Anthropic model the Region offers, with its lifecycle and whether the bare id is invocable —
`INFERENCE_PROFILE` alone means a request must name a profile:

```bash
aws bedrock list-foundation-models --by-provider Anthropic --region us-west-2 --profile awsds-infra-sandbox-1 --query 'modelSummaries[].[modelId,modelLifecycle.status,join(`,`,inferenceTypesSupported)]' --output table
```

The profiles the account can actually name in a request, and how many models each routes to — the
third column above 1 is a prompt processed outside `us-west-2` some of the time:

```bash
aws bedrock list-inference-profiles --region us-west-2 --profile awsds-infra-sandbox-1 --query "inferenceProfileSummaries[?status=='ACTIVE'].[inferenceProfileId,type,length(models)]" --output table
```

Anything standing up and billing by the hour, which should be empty:

```bash
aws bedrock list-provisioned-model-throughputs --region us-west-2 --profile awsds-infra-sandbox-1 --query 'length(provisionedModelSummaries)'
```

**Do not read `get-foundation-model-availability` as an access check.** It returned
`AUTHORIZED / AVAILABLE / AVAILABLE` for all thirteen Anthropic models before the form, after the form
and after the retention mode changed, and it reads the same in an account that has no form at all —
which is what `BR-7` in the script above measures on every run.

### One instrument per question

All read-only.

| Question | Instrument |
|---|---|
| Is the account's retention mode declared? | `aws bedrock get-account-data-retention --region us-west-2` — `none`, with an `updatedAt` |
| Is that mode *enforced*? | **No read answers this.** Availability and the agreement offer are identical for a retaining model and a scoped one. Only an invocation of a retaining model shows it (stage 7.2a) |
| Which models retain? | Not `allowed_modes` — it is in no Bedrock API. The vendor's abuse-detection page, dated when read; on 2026-09-11 it named the two Fable models, both present and available in `us-west-2` |
| Does the form exist? | `aws bedrock get-use-case-for-model-access --region us-west-2` — anything but `ResourceNotFoundException`. **Not** `get-foundation-model-availability` |
| Did the invocation take the private door? | CloudTrail in Sandbox: `InvokeModelWithResponseStream` is a **management event**, so the organization trail carries it with no data-event charge. The reading is `vpcEndpointId` on the event |
| Did it instead go out through the proxy? | `/awsds/prod/proxy` must hold **no** `bedrock-runtime` line for the same window. Two channels that do not share a failure mode |
| Does the record carry the prompt? | It must not: `requestParameters` carries `modelId`, `responseElements` is `null` — attribution without content |
| Did the session reach any Anthropic host? | `/awsds/prod/proxy` for the session's window. The pass condition is that **no** Anthropic name appears at all |
| Is the session on Bedrock, in the right Region? | `/status` inside the session names the provider and the resolved Region |
| Does the picker offer exactly the scoped set? | `/model` |
| Did a background task bill Haiku? | the `modelId` on the CloudTrail event for a session-title call |
| What does a session cost? | the session's own token accounting, against the rates in the stage's step 8.1 |

**What no instrument here reads**: the per-model `allowed_modes`. It is not in `get-foundation-model`,
`list-foundation-models` or `get-foundation-model-availability`, and no shape matching `allowed` exists
in any `bedrock*` service model the CLI ships (`aws-cli/2.36.18`, 2026-09-11). It is a vendor-page or
console reading, dated when taken — which is why M3's mode deny is the only mechanical guard.

---

*Stage: [`stage-06e-claude-code-bedrock.md`](../stages/stage-06e-claude-code-bedrock.md) ·
Log: [`log-stage-06e`](../../log/log-stage-06e-claude-code-bedrock.md) ·
Plan core: [`GENERAL_PLAN.md`](../../GENERAL_PLAN.md)*
