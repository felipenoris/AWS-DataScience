# Runbook — Claude Code on Bedrock, inside a SageMaker space

*The stage that builds this is [`stage-06e-claude-code-bedrock.md`](../stages/stage-06e-claude-code-bedrock.md);
the channel it runs inside is [`remote-ide.md`](remote-ide.md); the image that delivers its configuration
is [`dev-env.md`](dev-env.md).*

**This file is written for two audiences that do not overlap.** The infrastructure engineer configures
this once for everyone and never opens the IDE; the data scientist opens the IDE and never touches an
account. Read your own half.

| Section | Audience | What it holds |
|---|---|---|
| **§M** | infrastructure | enabling the model: where it runs, the retention mode, the form, **the agreement**, and the Region-ceiling exemption |
| **§P** | infrastructure | **granting a project access — once per project, and the one recurring task here** |
| **§I** | infrastructure | what the infrastructure configures: the endpoints, the grant, the image |
| **§U** | the data scientist | what the user configures, and what a user cannot change |
| **§V** | both | reading it back, one instrument per question |

**State, 2026-09-12.** **A session answered from inside a space**, on Haiku 4.5, as the project role,
through the VPC endpoint — which is what every section below was written to produce.

**§M is done**: M0, M2, M4 and M5; M1 in all 17 enabled Regions and M3 attached, both 2026-09-12.
**§I is built**: the grant applied 2026-09-11, the endpoint pair and its policy
2026-09-12, and `default-v0.4.0` carries the settings file as image version 4, attached to the domain
the same day. **§U is exercised** for the first time, on settings edited by hand inside the container
rather than shipped in the image — a measurement, not a configuration.

**Three things are open and none of them is cosmetic.** The scoped models `claude-opus-5` and
`claude-sonnet-5` are **refused by AWS for this account** and the working set is the 4.5 generation
(M4); the retention mode is declared in one Region of three (M1); and M5's exemption has no
compensating deny, so the `Interactive` OU currently has no Region ceiling on Bedrock invocation.

The readings are in [`log-stage-06e`](../../log/log-stage-06e-claude-code-bedrock.md). Every sentence
below that describes something unbuilt or unexercised says so.

---

## §M — Enabling the model

**The order is not the numbering.** M1, M2 and M3 were written when the use-case form was believed to
be the enabling act. 2026-09-12 measured that it is not: what enables a model is the **agreement**
(M4), and a cross-Region profile is refused by the organization's own Region ceiling until M5 is
done. The numbers are kept because other files reference them.

| Order | Act | What it does |
|---|---|---|
| 1 | **M0** | read which Regions the profiles route to. Every act below is per that list |
| 2 | **M1** | declare the retention mode — **in each of those Regions** |
| 3 | **M2** | submit the use-case form — the Anthropic catalogue's prerequisite, not the grant |
| 4 | **M4** | accept each model's agreement — **this is what enables a model** |
| 5 | **M5** | exempt the invocation from the Region ceiling |
| 6 | **M6** | invoke, and read both channels |
| 7 | **M3** | the SCPs that freeze M1 and close the models that retain — **last**, and the order is argued in M1 |

All of it is `Sandbox` only, by decision 2: principle 1 keeps `Management` bootstrap-only, and an
org-wide form would open Anthropic models in five accounts where D17 says no interactive compute
runs. M5 is the exception — it is a Control Tower control and is changed from `Management`.

**The identity:** the **infrastructure user**, account **Sandbox**, permission set
**InfrastructureAccess** — the CLI profile `awsds-infra-sandbox-1`, and the same identity picked in
the browser for the console half. That set is `AdministratorAccess` alone and carries **no
`DenyControlPlaneOffVpn`**, so none of it needs the VPN. M5 is signed in as **AWS Control Tower
Admin** on **Management** instead. Check before, not after:

```bash
aws sts get-caller-identity --profile awsds-infra-sandbox-1
```

### M0 — Where the models run

All three scoped models are invocable **only** through a cross-Region inference profile (step 0.1),
and which Regions that profile routes to is a **reading, not a constant** — AWS owns the routing and
can change it under a pinned model id.

```bash
for P in us.anthropic.claude-opus-5 us.anthropic.claude-sonnet-5 us.anthropic.claude-haiku-4-5-20251001-v1:0; do printf '%-46s ' "$P"; aws bedrock get-inference-profile --region us-west-2 --profile awsds-infra-sandbox-1 --inference-profile-identifier "$P" --query 'models[].modelArn' --output text | tr '\t' '\n' | sed 's|arn:aws:bedrock:||; s|::foundation-model/.*||' | tr '\n' ' '; echo; done
```

**Measured 2026-09-12: `us-east-1`, `us-east-2`, `us-west-2`** — the same three for all three scoped
models and for the 4.5 generation beside them. That list is the input to M1 and the ceiling on M5: an
exemption naming more Regions than this permits calls the profiles never make.

A profile that ever reads **one** Region is the finding, not the relief — it would mean AWS changed
the profile under a pinned model id (`AWS_STATE.md` `EXC-07`).

### M1 — Declare the account's data retention mode

**The mode is per account and per Region.** Measured 2026-09-12: `get-account-data-retention` answers
independently in each Region, and this account read `none` in `us-west-2` and **`inherit` in
`us-east-1` and `us-east-2`** — the two Regions M0 says a prompt is also processed in. A mode
declared in one Region of three covers one third of the routing.

**Why before the form.** A fresh account reads `inherit`, which the API documents as *no data
retention mode is set at this scope* — so the requirement rests on each model's own default and on
nothing this estate has said. Setting it first means the first access ever granted arrives with the
account already declaring zero retention (Lesson 5: an intention is not a control).

**Every enabled Region, not the routed three** (decision 16). The routed list is readable — M0 —
but AWS owns the routing and can add a Region under a pinned model id, and between that change and
the next reading a prompt is processed where nothing is declared. Declaring `none` everywhere
removes the race and makes the invariant checkable without knowing the routing. Measured 2026-09-12:
the API answers in **all 17 enabled Regions**.

**The order, and it is not the obvious one:**

1. **`bedrock:PutAccountDataRetention` joins M5's exemption.** Without it the Region ceiling refuses
   the write outside `us-west-2`, and refuses the read that would show it — which is why M0 comes
   first and why M5's list is not only the two invoke actions. **Done 2026-09-12**, and the refusal
   was measured first rather than assumed: M5 carries the negative control and the reading that
   verifies the console act.
2. **The writes**, every enabled Region. **Done 2026-09-12**, 17 of 17.
3. **M3's mode deny last, not first** — the reverse of what it looks like it should be. M3's
   condition is `StringNotEquals` on `bedrock:DataRetentionMode`, and **a `StringNotEquals` whose key
   is absent from the request evaluates TRUE**. Had `PutAccountDataRetention` not published that key,
   attaching M3 first would have denied every retention write including `--mode none`, stranding the
   Regions that still needed one. **The key is published — measured 2026-09-12, on a throwaway
   document rather than on the root one (M3)** — so this ordering cost nothing and was the right way
   round anyway: it put the risk after the work instead of before it.
4. **Attached 2026-09-12**, and re-probed where it lives rather than read back from the document.
   M3 carries the probes and the *must still succeed* floor.
5. The reading, as a standing check rather than a one-off: `./aws/bedrock-scope.py`'s **`BS-6`**.

**Before-reading**, every enabled Region. Expect `inherit` in all but the ones already done:

```bash
for R in $(aws account list-regions --region-opt-status-contains ENABLED ENABLED_BY_DEFAULT --profile awsds-infra-sandbox-1 --query 'Regions[].RegionName' --output text); do printf '%-16s ' "$R"; aws bedrock get-account-data-retention --region "$R" --profile awsds-infra-sandbox-1 --query mode --output text; done
```

**The call**, once per Region. One write each, reversible by setting the mode back:

```bash
for R in $(aws account list-regions --region-opt-status-contains ENABLED ENABLED_BY_DEFAULT --profile awsds-infra-sandbox-1 --query 'Regions[].RegionName' --output text); do printf '%-16s ' "$R"; aws bedrock put-account-data-retention --mode none --region "$R" --profile awsds-infra-sandbox-1 && echo none; done
```

The response field is **`mode`**, not `dataRetentionMode`: a `--query` naming the second returns
`None` in every Region, which reads exactly like a Region that answered and declared nothing.

**After-reading.** Expect `none` in every Region, each with its own `updatedAt`. Re-run the
before-reading command, or `./aws/bedrock-scope.py` and read `BS-6`. **A Region opted into later
starts at `inherit`**, so this is a standing check and not a one-time act.

Measured 2026-09-12: **17 of 17 `none`**, `updatedAt` between 15:31:45Z and 15:32:02Z, and `BS-6`
green. The write is accepted in a Region already at `none` and stamps a fresh `updatedAt`, so the
loop is safe to re-run and the timestamp is not evidence that a Region had drifted.

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

**What it is, corrected 2026-09-12.** A prerequisite for the Anthropic catalogue and a declaration on
AWS's record — **not the act that enables a model**. With the form present in all three Regions,
`authorizationStatus AUTHORIZED`, `entitlementAvailability AVAILABLE` and `regionAvailability
AVAILABLE`, the invocation was still refused; what was missing was M4. Nobody reviews the answer
before a model works, which is why it is worth writing carefully rather than quickly. Submitted
**once per AWS account**, and it then reads back in every Region.

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
| `intendedUsers` | the institution's data scientists — internal only, no external or public exposure. **A count, and `"0"` is not one**: this account submitted `"0"` and it is the one field worth re-submitting if access to a model is ever refused on review |
| `useCases` | data-science work: a coding assistant inside the institution's own development environment; code comprehension, refactoring, test writing and documentation over internal repositories; exploratory analysis support in notebooks. **No customer-facing application, no automated decisioning, no credit or risk scoring, no content generation for publication** |

**After-reading.** The same command must stop returning `ResourceNotFoundException` and return a
`formData` blob, in every Region M0 named. That is the whole verification of **this act** and says
nothing about any model being invocable. `get-foundation-model-availability` is **not** the
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

### M3 — Freeze the mode, and close the models that retain

M1 is a setting anyone with the permission can change back, and M5's sixth exempted action took away
the Region ceiling that used to confine the write to `us-west-2` by accident. Two statements in
`awsds-org-scp-baseline.json` (decision 4) close both halves. **Applied 2026-09-12**, `0 to add,
2 to change, 0 to destroy` — the document updated in place, its id unchanged, so the root attachment
never moved and there was no instant without a baseline.

The document is attached at the **organization root**, **which reaches every account and, like every
SCP, does not restrict `Management`**. That is accepted here: nobody invokes a model in `Management`,
and decision 2 keeps the model-access form out of it for the same reason.

#### The statements, as they stand in the document

```json
{
  "Sid": "DenyBedrockRetentionModeOtherThanNone",
  "Effect": "Deny",
  "Action": "bedrock:PutAccountDataRetention",
  "Resource": "*",
  "Condition": {
    "StringNotEquals": {
      "bedrock:DataRetentionMode": "none"
    }
  }
}
```

```json
{
  "Sid": "DenyInvokingModelsThatRetain",
  "Effect": "Deny",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "Resource": [
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-fable-5",
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-fable-5-1",
    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-fable-5",
    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-fable-5-1",
    "arn:aws:bedrock:*:*:inference-profile/global.anthropic.claude-fable-5",
    "arn:aws:bedrock:*:*:inference-profile/global.anthropic.claude-fable-5-1"
  ]
}
```

#### What is deliberate in them, and easy to undo by accident

- **No Region condition on the first, and that is the point.** The mode is per account **and** per
  Region (M1), so a deny written for one Region freezes one Region and leaves every other free to be
  set to anything. The same reasoning keeps the two retention actions outside the Region condition of
  the `Interactive` OU document (M5).
- **`StringNotEquals` against `none`, not a list of the modes to forbid.** The enum is `default`,
  `none`, `provider_data_share`, `inherit` — four values, where this plan had discussed two until
  2026-09-12, and **`provider_data_share` is the one the requirement is about**. Naming the three to
  forbid would go stale the day AWS adds a fifth; naming the one to permit cannot.
- **Six resource ARNs in the second, not two.** The two foundation-model ids, plus a `us.` **and** a
  `global.` inference profile for each — all four profiles measured `ACTIVE` on 2026-09-12. A deny
  naming only the model ids leaves the profile routes open, and **the profile ARN is what the
  refusal names**: the probe below was denied on
  `arn:aws:bedrock:us-west-2:<account>:inference-profile/us.anthropic.claude-fable-5`, not on a
  foundation-model ARN.
- **A deny on the models that retain, never an allow-list of the scoped ones.** An allow-list refuses
  the next model this estate adopts, from a document nobody thinks to open. This list goes stale in
  the safe direction: a new retaining model is not on it and is caught by the mode ceiling instead.
- **The two statements are not interchangeable.** Nothing in the control plane reads a retention
  mode's *effect* (§V), so the first is verifiable only in its own terms — that the write is refused.
  The second is verifiable by a call. They cover the same requirement from opposite ends.

#### The condition key is published, and that was measured rather than assumed

A `StringNotEquals` whose key is absent from the request **evaluates TRUE**. If
`PutAccountDataRetention` did not publish `bedrock:DataRetentionMode` at request time, the first
statement would be a blanket deny on the action — including on the `--mode none` M1 needs. Two
readings, and the first is not the second:

| Reading | What it establishes |
|---|---|
| `accessanalyzer validate-policy` accepted the key and rejected a bogus one beside it (2026-09-11) | the key is in the service's **catalogue** |
| the statement parked on the `Policy Test` OU, probed in `Policy Canary` (2026-09-12) | the key is **published at request time** |

#### Doing this in another environment

**Verify the statement before the document that carries it reaches anything.** A root-attached
document already reaches the canary, so there is nothing to park and a mistake lands everywhere at
once ([`scp-battery.md`](scp-battery.md), *Amending a root document*). Put the statement in a
throwaway document instead —
[`canary/awsds-canary-scp-bedrock-retention-mode.json`](../../../terraform-live/identity/org-policies/canary/awsds-canary-scp-bedrock-retention-mode.json)
is the one used here, the real statement verbatim rather than an inverted one — attach it to an OU
holding one disposable account, and run three calls. **Call 0 is what makes the other two
attributable**; without it a refusal is just a refusal.

| # | Call, in the disposable account | Must |
|---|---|---|
| 0 | `put-account-data-retention --mode none`, **nothing attached** | succeed |
| 1 | the same call, **document attached** | succeed, **with a fresh `updatedAt`** — the stamp is what separates a write from a no-op |
| 2 | `put-account-data-retention --mode inherit` | be refused, **naming the throwaway's own policy id** |

Measured 2026-09-12: succeeded at 15:56:38Z, succeeded at 16:05:22Z, refused naming `p-ojm4ldiw`.
Detach and delete in the same sitting — a throwaway left attached governs an OU nobody meant to
govern.

#### After attaching, re-probe where it lives

Amending a root document is the battery's phases 1-3, not phase 4b, because the document reaches the
canary too. Measured 2026-09-12, after the apply:

| Probe | Result |
|---|---|
| `put-account-data-retention --mode none` | succeeded, `updatedAt` 16:18:02Z |
| `put-account-data-retention --mode inherit` | refused, naming **`p-1fp032g8`** — the baseline, not the deleted throwaway |
| `invoke-model` on `us.anthropic.claude-fable-5` | refused, naming `p-1fp032g8`, **on the inference-profile ARN** |
| `sts get-caller-identity`, `s3api list-buckets`, `ec2 describe-vpcs` | all three succeed — the *must still succeed* floor |
| `invoke-model` on `us.anthropic.claude-haiku-4-5-20251001-v1:0`, from `Sandbox` | answered — **the retaining deny does not catch the scoped set**, which the canary cannot test because it holds no agreement |

The last row is the one to keep. The failure this pair of statements could cause is not a model that
answers when it should not; it is the **scoped set going dark** because a resource list was written
one character wrong, in a document nobody opens.

### M4 — Accept each model's agreement

**This is the act that enables a model.** It is what the Bedrock console calls *Enable specific
models*, and until 2026-09-12 this runbook did not name it at all.

**Before-reading.** `NOT_AVAILABLE` means **no agreement has been created**, not *no agreement is
needed*. Reading it the second way is what made the omission invisible:

```bash
aws bedrock get-foundation-model-availability --region us-west-2 --profile awsds-infra-sandbox-1 --model-id anthropic.claude-haiku-4-5-20251001-v1:0 --query 'agreementAvailability.status' --output text
```

**Read the offer before accepting it.** It carries a rate card, a URL to a legal document and a
support term, and accepting it is a legal act:

```bash
aws bedrock list-foundation-model-agreement-offers --region us-west-2 --profile awsds-infra-sandbox-1 --model-id anthropic.claude-haiku-4-5-20251001-v1:0 --query 'offers[0].{offer:offerId,legal:termDetails.legalTerm.url,support:termDetails.supportTerm}'
```

**The call, one model at a time** — deliberately not a loop, because each run accepts a separate
agreement:

```bash
MODEL=anthropic.claude-haiku-4-5-20251001-v1:0
```

```bash
aws bedrock create-foundation-model-agreement --region us-west-2 --profile awsds-infra-sandbox-1 --model-id "$MODEL" --offer-token "$(aws bedrock list-foundation-model-agreement-offers --region us-west-2 --profile awsds-infra-sandbox-1 --model-id "$MODEL" --query 'offers[0].offerToken' --output text)"
```

The model ids this estate has accepted, and the ones it would accept for the scoped set:

| Generation | Model ids | State |
|---|---|---|
| current | `anthropic.claude-opus-5`, `anthropic.claude-sonnet-5` | agreements accepted 2026-09-12; **refused for this account**, see below |
| previous | `anthropic.claude-opus-4-5-20251101-v1:0`, `anthropic.claude-sonnet-4-5-20250929-v1:0` | agreements accepted 2026-09-12; **invocable, and the scoped set since decision 14** |
| either way | `anthropic.claude-haiku-4-5-20251001-v1:0` | agreement accepted 2026-09-12; invocable |

**After-reading.** The status goes `NOT_AVAILABLE` → `PENDING` → `AVAILABLE`. It settled in seconds
for one model and took minutes for another, so poll rather than assume:

```bash
until [ "$(aws bedrock get-foundation-model-availability --region us-west-2 --profile awsds-infra-sandbox-1 --model-id "$MODEL" --query 'agreementAvailability.status' --output text)" = AVAILABLE ]; do sleep 15; done; echo AVAILABLE
```

**Per account and per model, not per Region.** Measured 2026-09-12: an agreement created in
`us-west-2` read `AVAILABLE` in `us-east-1` and `us-east-2` **before** the creating Region left
`PENDING`. Each model needs its own; Amazon's own models need none — `amazon.nova-lite-v1:0` reads
`AVAILABLE` with nothing done.

**The generation gate, and no reading exposes it.** Measured 2026-09-12, with the agreement
`AVAILABLE`, the form present in all three Regions and every availability field green:
`us.anthropic.claude-sonnet-5` was refused for **every principal, `AdministratorAccess` included** —

```
AccessDeniedException: anthropic.claude-sonnet-5 is not available for this account.
You can explore other available models on Amazon Bedrock. For additional access options,
contact AWS Sales at https://aws.amazon.com/contact-us/sales-support/
```

The identical chain on `us.anthropic.claude-sonnet-4-5-20250929-v1:0` answered `pong`, and so did
Haiku 4.5 and Opus 4.5. The split follows the shape of the model id: **dated ids
(`…-2025xxxx-v1:0`) are invocable in this account; clean ids (`claude-sonnet-5`, `claude-opus-5`,
`claude-opus-4-6/4-7/4-8`, `claude-sonnet-4-6`, `claude-fable-5`, `claude-fable-5-1`) are not.** The
gate is commercial, at the account, and **every readable instrument reports the model as available and
authorized while the invocation refuses it** — Lesson 13 at account scale. The message is literal:
the path forward is the sales contact it names, or the previous generation.

### M5 — Exempt the invocation from the Region ceiling

**Why it is needed.** A cross-Region inference profile is authorized **per destination Region**.
Measured 2026-09-12: a call made with `--region us-west-2`, logged with `awsRegion: us-west-2`, was
denied against `arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-sonnet-5` by
`CT.MULTISERVICE.PV.1`, whose only condition is `aws:RequestedRegion != us-west-2`. No `bedrock:`
action appears in that control's 86 `NotAction` entries, and its four exempted principals are Control
Tower's own roles.

**The control is Control Tower's**, and its own SCP says so: *"Do not modify, delete, or detach this
policy … To modify these controls, you must utilize AWS Control Tower."* It is attached to the
**`Interactive` OU** alone and it is parameterized — `AllowedRegions`, `ExemptedActions` and
`ExemptedPrincipalArns` are injection points in the policy template
([`REFERENCES.md`](../../REFERENCES.md), the `ou-region-deny` page).

**The path**, signed in as **AWS Control Tower Admin** on **Management** — the Control Tower API
answers from that account alone, and a member account is told *"you must create a landing zone first"*:

1. **Control Tower → Enabled controls**, open **`CT.MULTISERVICE.PV.1`**.
2. On the row for the **`Interactive`** OU, **View configurations → Update enabled control**.
3. The Region list appears with **`us-west-2`** selected. **Leave it as it is** — see the lever below.
4. The next screen shows the Region deny policy, read-only, with `{{ExemptedActions}}` and
   `{{ExemptedPrincipalArns}}` visible as template slots.
5. At the foot of the page, **Adding NotActions**. Add the actions below, one per line.
6. Leave **Exempted principals** empty.

**The actions added 2026-09-12:**

```
bedrock:InvokeModel
bedrock:InvokeModelWithResponseStream
bedrock:GetFoundationModelAvailability
bedrock:GetAccountDataRetention
bedrock:GetUseCaseForModelAccess
bedrock:PutAccountDataRetention
```

The first two are what an invocation needs. The next three are what lets an operator **see** the other
Regions at all: with only the first two in place, `get-foundation-model-availability` and
`get-account-data-retention` are refused in `us-east-1` and `us-east-2`, so M0 and M1 cannot be
verified there. The sixth is what lets M1 **declare** the mode there, and it was added last, after a
negative control: with the other five in place,
`put-account-data-retention --mode none --region us-east-1` was refused by this control naming
`p-umksvu5a`, so the ceiling's reach over the write is measured rather than deduced from the list.

**The write is the one that widens something.** The five reads tell an operator what is true. The
sixth lets **any principal in the OU** set the retention mode in **any Region**, including back to
`inherit` — the thing this stage exists to prevent. Before this action was exempted the Control Tower
ceiling confined the write to `us-west-2` by accident, and that accidental confinement is what M1
traded away to declare the mode everywhere. **M3 is what replaces it**, on the mode axis rather than
the Region one, and it was attached the same day.

**Verify the console act by reading the policy, not by attempting a call.** The Control Tower *control*
API answers from `Management` alone, but the SCP it writes is an Organizations document, and
`describe-policy` answers for it from `Identity`. The count is the check — the base template carries
86 entries, so the expected total is 86 plus the list above:

```bash
aws organizations describe-policy --policy-id p-umksvu5a --profile awsds-infra-identity --query 'Policy.Content' --output text | python3 -c "import json,sys; na=json.load(sys.stdin)['Statement'][0]['NotAction']; print(len(na)); print([a for a in na if a.startswith('bedrock')])"
```

Measured 2026-09-12: **92**, the six above among them. A console form that is accepted and does not
move that number is a control that did not propagate, and the attempted call cannot tell the two
apart — it is refused either way while something else in the chain is also missing.

**Which lever, and why not the other.** The two lists are independent inside one statement — there is
no way to say *this action, for this principal*. `Exempted principals` removes a principal from the
ceiling **for every action in every Region**; the project role is the interactive-compute principal,
so exempting it would hand the Region ceiling to whatever a scientist runs. `NotActions` removes
those actions **for every principal in the OU**, which is the narrower of the two by a wide margin.
Write the actions explicitly rather than `bedrock:InvokeModel*` — the wildcard would also catch
`InvokeModelWithBidirectionalStream` and whatever AWS adds next, and this list is meant to stay
identical to the grant's and the endpoint policy's.

**Do not widen `AllowedRegions` instead.** That opens every service in the added Regions for the whole
OU; the action lever opens six actions. Both were on the table 2026-09-12 and this is why the action
lever won.

**What is still open, and it is not small.** The exemption is on the action axis, so those five
actions are now permitted **in every Region**, including the ones M0 says the profiles never touch,
and for every principal in the `Interactive` OU. Two compensations, **neither done**:

- **A model scope in the estate's own SCP.** Step 7.5's document gains a deny on
  `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream` for any resource but the scoped
  profiles and their foundation models. This moves the resource ceiling out of IAM — where a
  blueprint's managed policy can widen it without this repository's say — and into the organization.
- **A Region scope for the exemption itself.** The five actions should be denied outside the M0 list
  by the same document, so the door the Control Tower control stopped guarding is closed again for
  every Region a profile does not route to.

**Both are written** (2026-09-12, decision 15), in
[`awsds-org-scp-ou-interactive.json`](../../../terraform-live/identity/org-policies/policies/awsds-org-scp-ou-interactive.json)
rather than in the root document: the hole was opened on this OU and the compensation belongs in the
same scope. The two statements, as they stand in that file — the first two in it are older and
belong to other stages:

```json
{
  "Sid": "DenyBedrockInvocationOutsideTheScopedModels",
  "Effect": "Deny",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream"
  ],
  "NotResource": [
    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-opus-4-5-20251101-v1:0",
    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "arn:aws:bedrock:*:*:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-4-5-20251101-v1:0",
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-4-5-20250929-v1:0",
    "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
  ]
}
```

```json
{
  "Sid": "DenyBedrockReadsOutsideTheRoutedRegions",
  "Effect": "Deny",
  "Action": [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
    "bedrock:GetFoundationModelAvailability",
    "bedrock:GetUseCaseForModelAccess"
  ],
  "Resource": "*",
  "Condition": {
    "StringNotEquals": {
      "aws:RequestedRegion": ["us-east-1", "us-east-2", "us-west-2"]
    }
  }
}
```

**Four things in there are deliberate and easy to undo by accident.**

- **`NotResource`, and all six spellings.** A cross-Region profile is authorized once per destination
  Region: one pass names the profile ARN, the others name a per-Region `foundation-model` ARN. Miss
  one spelling and that pass is denied.
- **A wildcard account on the profile ARNs.** An account id may not appear in a tracked file
  (`aws/INDEX.md` rule 1), and an inference-profile ARN is always the caller's own account, so within
  an account there is nothing else for the wildcard to match.
- **No region on the foundation-model ARNs.** The profiles route to three; a region-pinned ARN would
  deny two thirds of the requests by geography, intermittently.
- **The two retention actions are absent from the second statement's `Action` list.** M1 declares the
  mode in **every** enabled Region, so a Region condition over those calls would forbid the very
  thing that keeps the mode declared. What guards them instead is M3, on the mode axis, everywhere at
  once.

**The list in both statements is the same list M4 and §I carry**, so it has a drift check of its
own: [`./aws/bedrock-scope.py`](../../../aws/bedrock-scope.py) reads the declaration out of this file
and compares it against AWS — `BS-3` when AWS routes somewhere the condition does not name, `BS-7`
when the repository's copies disagree.

Until both statements are **attached**, the honest statement is that the `Interactive` OU has no
Region ceiling on Bedrock invocation.

### M6 — Invoke, and read both channels

The invocation is the only instrument that answers. Run it **from a space**, as the project role, so
that what is measured is the path a session takes:

```bash
aws bedrock-runtime invoke-model --region us-west-2 --model-id us.anthropic.claude-haiku-4-5-20251001-v1:0 --cli-binary-format raw-in-base64-out --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":16,"messages":[{"role":"user","content":"ping"}]}' /tmp/bedrock-out.json && cat /tmp/bedrock-out.json
```

**Read the refusal, never the exit code.** The three that matter, and each names a different act:

| What it says | What is missing |
|---|---|
| `… explicit deny in a service control policy: p-…`, naming a resource in another Region | M5 |
| `… is not available for this account … contact AWS Sales` | M4, or the generation gate M4 describes |
| `… no identity-based policy allows the bedrock:InvokeModel action` | the model is not in `sandbox/bedrock/`'s `models` map — §P |

**Then both channels**, which is what §V's rows are for: CloudTrail for `vpcEndpointId` and the
absence of an `errorCode`, and `/awsds/prod/proxy` for the absence of any `bedrock` or Anthropic name
in the same window — **with a negative control**, since an empty log proves nothing unless the
instrument was seeing the space at all.

---

## §P — Granting a project access

**This is done once per project, and it is the only recurring task in this file.** A SageMaker
Unified Studio project gets its own IAM role, `datazone_usr_role_<project>_<environment>`, minted by
the service when the project is created in the portal. Nothing grants Bedrock to it automatically.

**Why it is per project and not once for the domain.** The blueprint configuration
(`awscc_datazone_environment_blueprint_configuration`) carries fourteen attributes and exactly one
is policy-shaped — `environment_role_permission_boundary`, which is how D13's boundary reaches every
project role — and a boundary only subtracts. The service offers **a ceiling for every project role
and a floor for none**, so there is no lever that would grant Bedrock to a whole domain at once. The
alternative that would have made "which projects" a single list — a role this repository authors,
reached by SDK role chaining — was refused because the invocation would then leave the D13 boundary
(Stage 6e decision 8).

**The order is fixed by what creates what.**

1. The project is created in the portal, by whoever owns it. **Nothing below works before this**:
   the role does not exist and its name is not predictable.
2. The role name is read (P1).
3. The grant is attached (P2 by Terraform, or P3 by the CLI).
4. The attachment is verified (P4).

### P1 — Find the project's role name

```bash
aws iam list-roles --profile awsds-infra-sandbox-1 --query 'Roles[?starts_with(RoleName, `datazone_usr_role_`)].RoleName' --output text
```

More than one line means more than one project, and the name carries no project *title* — only the
two service-minted ids. To tell them apart, read the tags: `AmazonDataZoneProject` is the project id
the portal shows in its URL, and `AmazonDataZoneScopeName` is the environment (`dev`, and others as
a project grows).

```bash
aws iam get-role --role-name datazone_usr_role_<project>_<environment> --profile awsds-infra-sandbox-1 --query 'Role.Tags[?Key==`AmazonDataZoneProject` || Key==`AmazonDataZoneScopeName` || Key==`AmazonDataZoneBlueprint`]' --output table
```

### P2 — Attach it with Terraform, which is how this estate does it

The slice is [`terraform-live/sandbox/bedrock/`](../../../terraform-live/sandbox/bedrock). It owns
one policy, `awsds-<env>-bedrock-assistant`, and one attachment per project.

Add the role name to `project_roles` in
[`variables.tf`](../../../terraform-live/sandbox/bedrock/variables.tf) — the list's `default`, which
is where this slice's hand-edited values live, the same idiom `sandbox/dev-env/` uses for
`image_tag`:

```hcl
variable "project_roles" {
  default = [
    "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
  ]
}
```

Then plan and apply it the way [`terraform-changes.md`](terraform-changes.md) says, as the
infrastructure user on **Sandbox** with **InfrastructureAccess**:

```bash
./scripts/gen-backend-hcl.py sandbox bedrock && ./scripts/gen-tfvars.py sandbox bedrock
```

```bash
terraform -chdir=terraform-live/sandbox/bedrock init -backend-config=backend.hcl -input=false
```

```bash
terraform -chdir=terraform-live/sandbox/bedrock plan -input=false
```

**Read the plan for one thing before applying**: a new project adds exactly one
`aws_iam_role_policy_attachment`. If the policy itself is also being created, this is the first
project; if the policy is being *replaced*, something changed in the model list and every project is
affected.

**Two ways the plan fails, and both are the guard working.** `no IAM role found` names a role that
does not exist — the project was not created, or the name has a typo. A precondition failure naming
`awsds-<env>-project-boundary` means the role exists but is not under D13: it is not a SMUS project
role, whatever its name looks like, and it must not get this grant.

### P3 — The same thing with the AWS CLI

For a project that needs the grant before the next apply window. **It is the same policy**, not a
second copy — the ARN comes from the slice, so the two forms converge rather than diverge:

```bash
aws iam list-policies --scope Local --profile awsds-infra-sandbox-1 --query 'Policies[?PolicyName==`awsds-sandbox-bedrock-assistant`].Arn' --output text
```

```bash
aws iam attach-role-policy --role-name datazone_usr_role_<project>_<environment> --policy-arn arn:aws:iam::<sandbox>:policy/awsds-sandbox-bedrock-assistant --profile awsds-infra-sandbox-1
```

**This is a write, and it leaves drift.** Terraform does not know about it, so the next plan of this
slice shows the attachment as missing and would *remove* it. Add the role to `project_roles` in the
same sitting and re-plan until it reads `No changes` — Lesson 35's shape: the stale path is the one
that still succeeds, quietly, past every guard.

To undo one, by either route: remove the entry and apply, or

```bash
aws iam detach-role-policy --role-name datazone_usr_role_<project>_<environment> --policy-arn arn:aws:iam::<sandbox>:policy/awsds-sandbox-bedrock-assistant --profile awsds-infra-sandbox-1
```

### P4 — Verify, and what a verification here can and cannot say

The attachment reads back:

```bash
aws iam list-attached-role-policies --role-name datazone_usr_role_<project>_<environment> --profile awsds-infra-sandbox-1 --query 'AttachedPolicies[].PolicyName' --output text
```

**That the policy is attached is not that the model can be invoked.** Reach is an intersection
(Lesson 28) and this reads one term. The proof is a call from inside a space on that project, and
§V's CloudTrail row is where it is read.

**Re-plan this slice after any SMUS change to the project.** The role belongs to the service, and a
blueprint reconciliation may detach a policy its control plane does not know about — INT-15's open
half. The symptom is an assistant that stops working with no diff in this repository.

**Or read both sides at once**, which needs no plan and no state lock:

```bash
./aws/bedrock.py
```

Its `BR-8` compares `project_roles` against what IAM reports, and names which fault it found: a
declared attachment that is gone was **removed** by something, and an attachment nothing declares
was **added by hand** and the next apply will undo it.

---

## §I — What the infrastructure configures

**Built 2026-09-12**, the stage's steps 3, 4 and 5. This is the half no user sees and no user can
change; §U is the other half.

| What | Where it is declared | State |
|---|---|---|
| the private path | [`terraform-live/sandbox/egress/`](../../../terraform-live/sandbox/egress), on `vpc-egress-v0.14.1` | applied 2026-09-12, step 4.2 |
| the endpoint policy | `endpoint_action_scopes`, in the same caller | applied with it, step 4.4 |
| the grant | [`terraform-live/sandbox/bedrock/`](../../../terraform-live/sandbox/bedrock), rank 52, `[P]` | applied 2026-09-11, step 3 |
| the client's configuration | [`images/dev-env/claude-code/managed-settings.json`](../../../images/dev-env/claude-code/managed-settings.json) | shipped in `default-v0.4.0`, image version 4, 2026-09-12 — `v0.3.0` shipped the same file pinning `claude-opus-5` and `claude-sonnet-5`, which AWS refuses for this account |

### The private path

`bedrock` and `bedrock-runtime` are interface endpoints in the Sandbox VPC, about USD 0.010/h each.
They sit in the caller's always-on list rather than behind an optional service group: a group is per
apply, and a `make up` without the flag destroys what a flagged one created, so a permanent consumer
cannot live behind one. The module's `bedrock` group is now the agent pair (`bedrock-agent`,
`bedrock-agent-runtime`), which only the blueprints use.

**The endpoints and the `NO_PROXY` bypass list are one change in two places** (Lesson 33). An
endpoint whose name is missing from the bypass list sends the call to the proxy and out to the
internet, and the call still works — with no `aws:SourceVpce` on the far side, which is how the
perimeter is lost silently. The generated list is `terraform output -raw no_proxy` on
`sandbox/egress` (52 entries since 2026-09-12); what a process inside a space reads is the dated
literal in [`images/dev-env/Dockerfile`](../../../images/dev-env/Dockerfile) (6d decision 8), and
[`./aws/devenv.py`](../../../aws/devenv.py) reports the difference between the two.

### The endpoint policy

The caller narrows the runtime door on the action axis and leaves the control plane open:

```hcl
endpoint_action_scopes = {
  "bedrock-runtime" = [
    "bedrock:InvokeModel",
    "bedrock:InvokeModelWithResponseStream",
  ]
}
```

Both statements of the trusted-networks document then carry that list in place of `*`, for that
endpoint alone. Read back from the applied endpoint on 2026-09-12:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOrganizationPrincipals",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": "*",
      "Condition": { "StringEquals": { "aws:PrincipalOrgID": "<org>" } }
    },
    {
      "Sid": "AllowAWSServicePrincipals",
      "Effect": "Allow",
      "Principal": "*",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": "*",
      "Condition": { "Bool": { "aws:PrincipalIsAWSService": "true" } }
    }
  ]
}
```

**Scope a door whose purpose is unambiguous.** `bedrock-runtime` carries invocation and nothing else
for any consumer, so an invoke list on it states a property of the service. `bedrock` is the control
plane: its surface is long, it grows, and the six enabled `AmazonBedrock*` blueprints call it for
things a coding assistant never does — a list written for one of those consumers refuses the other,
with no denial that names this policy. **The resource axis is deliberately not narrowed.** Model
ARNs are the grant's list, and a second copy of it in another slice diverges (Lesson 33), while the
action list changes when AWS adds an API rather than when a decision is taken here.

### The grant

Measured 2026-09-11: the project role's every `InvokeModel*` allow lands on `foundation-model/*`,
**none on the system inference profile**, and `ListInferenceProfiles` is granted nowhere — so a
grant is needed, and §P is how one project gets it.

**Confirmed from a space 2026-09-12, by a refusal.** `bedrock:InvokeModel` on the bare
`amazon.nova-lite-v1:0` — a model id with no profile in the request — came back *"no identity-based
policy allows the bedrock:InvokeModel action"*. The blueprint's one matching allow is conditioned on
an **inference-profile ARN being present**, and a bare model id does not satisfy it; through a profile
it would match the foundation-model half and still nothing on the profile half, which is the half this
slice supplies. Either way the consequence is the same and worth stating plainly: **no model outside
this slice's `models` map is invocable from a space**, so that map is the whole of what a project can
reach.

What the policy says, read back from `awsds-sandbox-bedrock-assistant` v1 on 2026-09-12:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeScopedClaudeModelsThroughSystemProfiles",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-opus-5",
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-sonnet-5",
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-5",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-sonnet-5",
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-haiku-4-5-20251001-v1:0"
      ]
    },
    {
      "Sid": "ResolveTheScopedProfiles",
      "Effect": "Allow",
      "Action": "bedrock:GetInferenceProfile",
      "Resource": [
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-opus-5",
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-sonnet-5",
        "arn:aws:bedrock:us-west-2:<sandbox>:inference-profile/us.anthropic.claude-haiku-4-5-20251001-v1:0"
      ]
    },
    {
      "Sid": "ListProfilesHasNoResource",
      "Effect": "Allow",
      "Action": "bedrock:ListInferenceProfiles",
      "Resource": "*"
    }
  ]
}
```

**Both ARN groups are required for one call**: the request names the profile, and the service
evaluates the profile *and* each foundation model behind it. The foundation-model ARNs carry no
region on purpose — a `us.` profile routes to three of them, so a region-pinned ARN would authorize
a third of the requests and refuse the rest by geography.

### The client's configuration

`/etc/claude-code/managed-settings.json`, written into the image. Managed settings are the top tier
of Claude Code's precedence: no user, project, local or `--settings` value overrides a key set here
(the vendor's table, read 2026-09-11), and on Linux the client reads `/etc/claude-code/` at startup.
It ships in the layer because a space starts with nothing — `/home/sagemaker-user` survives an app
restart and dies with the space, so a configuration that must be present before the first prompt
cannot live in a home directory. Unlike the proxy variables, it is not constrained by the app image
configuration's 256-character cap per environment value: it is a file, not an env entry.

The source is
[`images/dev-env/claude-code/managed-settings.json`](../../../images/dev-env/claude-code/managed-settings.json),
copied by the Dockerfile to that path and `chmod 0444`. It is the whole file:

```json
{
  "env": {
    "CLAUDE_CODE_USE_BEDROCK": "1",
    "AWS_REGION": "us-west-2",
    "ANTHROPIC_MODEL": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "us.anthropic.claude-opus-4-5-20251101-v1:0",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  },
  "availableModels": ["opus", "sonnet"],
  "skipWebFetchPreflight": true
}
```

| Key | What it decides |
|---|---|
| `CLAUDE_CODE_USE_BEDROCK` | the provider. Without it the client calls `api.anthropic.com`, which the compute plane refused 17 times on 2026-09-11 ([`remote-ide.md`](remote-ide.md) §N) |
| `AWS_REGION` | the Region. The client resolves `AWS_REGION` → `AWS_DEFAULT_REGION` → the profile's → `us-east-1`, and the last would be a silent wrong answer |
| `ANTHROPIC_MODEL` | the session's model. It also decides the background model: the vendor states that when a session sets it, background tasks use it too |
| `ANTHROPIC_DEFAULT_OPUS_MODEL`, `ANTHROPIC_DEFAULT_SONNET_MODEL` | what each alias resolves to. Without the pins an alias follows the client's built-in default, which moves with the client version |
| `ANTHROPIC_DEFAULT_HAIKU_MODEL` | the only key that moves background work — session titles and the like — off the primary model. Without it they bill at the primary's rate, 27.50 per 1M output tokens, for work a Haiku does at 5.50 (step 8.1) |
| `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` | the session-quality survey. On Bedrock, metrics, error reports and `/feedback` are already off; the survey is not, and this is what closes it |
| `availableModels` | the picker lock (decision 3). It constrains `/model`, `--model` and the model key in a user's own file, so nothing outside the use-case form's declaration and the grant's resource scope is reachable |
| `skipWebFetchPreflight` | the WebFetch hostname check, which calls `api.anthropic.com` whatever the provider and is not covered by the traffic key above |

**The pins are the 4.5 generation, and not by preference** (decision 14, 2026-09-12):
`claude-opus-5` and `claude-sonnet-5` are refused for this account by AWS while every readable
instrument reports them available (M4's generation gate, `AWS_STATE.md` `EXC-08`). All three below
were proven by invocation the same day. The switch costs one model's rate and only one — Opus 4.5
prices identically to Opus 5 and Haiku did not move, while Sonnet goes 2.20/11.00 → 3.30/16.50
(`PRICING.md`).

**Every model id is an inference profile**, because all three are `INFERENCE_PROFILE` only and the
bare model id is not invocable (step 0.1). These ids, the grant above and 7.5's retention deny are
one list with several consumers: a model added here and nowhere else is a refusal at the first
prompt, and one added to the grant and not here is unreachable from the picker.

`availableModels` names aliases, not ids, and Haiku's absence from it is deliberate. The picker
offers what a person may choose; the Haiku pin is where background work goes, so a user neither
selects it nor needs to — and dropping it from the pins would put session titles back on Opus.

### Changing the configuration

**Editing that file is an image release, not a configuration change.** Nothing re-reads it in place:
a running space holds the layer it started from, and a space's home directory cannot override it.
The chain is [`dev-env.md`](dev-env.md) §B, and its shape is:

1. Edit `images/dev-env/claude-code/managed-settings.json` and commit. `pre-commit`'s `check-json`
   covers `images/**.json` and the Dockerfile re-parses the file during the build, so a trailing
   comma fails in review rather than in a space three weeks later.
2. Build both images on the buildbox ([`buildbox.md`](buildbox.md)) and push under a **new**
   `<flavour>-v<semver>` tag. The ECR repository is immutable-tagged: a rebuild is a new tag, never
   a re-push of an existing one.
3. Bump `image_tag` in
   [`terraform-live/sandbox/dev-env/variables.tf`](../../../terraform-live/sandbox/dev-env/variables.tf)
   and apply. A SageMaker image version is immutable, so `base_image` forces replacement and the
   plan reads `1 to add, 0 to change, 1 to destroy`.
4. The two domain writes around that apply, in §B's order: delete the apps, detach the custom images
   from the domain's `DefaultUserSettings`, apply, re-attach on the new version number, then start a
   new space. The version the apply destroys is the one the domain names, and the service fails the
   re-attach rather than refusing the destroy.

**An unparseable file is ignored silently.** Claude Code neither refuses to start nor warns: every
key above stops applying, the client falls back to its own defaults, and the session goes to
`api.anthropic.com` — which the compute plane refuses. The symptom is an assistant that reaches
nothing, with no message naming this file.

### Reading it back inside a space

```bash
cat /etc/claude-code/managed-settings.json
```

**That the file is there is not that it applied** (Lesson 54). The readings that settle it are in
§V: `/status` for the provider and the resolved Region, `/model` for the picker's contents, and the
CloudTrail row for which `modelId` a call actually used.

---

## §U — What the user configures, and what a user cannot change

**The surface exists since 2026-09-12**, on a space started from image version 3. What is written
here about the client itself is read from the vendor's documentation and from what §I declares;
stage step 6 is the first session, and what it measures lands here.

- **Install the extension into the remote session**, not into the portal's Code Editor. A space runs
  two IDE servers with separate extension directories and settings ([`remote-ide.md`](remote-ide.md)
  §E), and an extension installed in the wrong one is invisible to the other.
- **Disable Login Prompt** (`claudeCode.disableLoginPrompt`) is a **VS Code** setting, not a Claude
  Code one, so it lives in a different file from everything in §I and is set once per surface:
  `~/.vscode-server/data/User/settings.json` for the remote session and
  `~/sagemaker-code-editor-server-data/data/User/settings.json` for the Code Editor. A configuration
  that works in one surface and not the other is this file's most common failure.

  The key merges into whatever that file already holds — it is the editor's own settings file, not a
  Claude Code one, so replacing it drops the user's editor configuration:

  ```json
  {
    "claudeCode.disableLoginPrompt": true
  }
  ```

  This one is the user's, and stays the user's: managed settings do not reach it, because the
  precedence chain §I sits on top of is Claude Code's and this key belongs to VS Code.
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

**Every readable instrument here can report a model as available while the invocation refuses it.**
Measured 2026-09-12 on `claude-sonnet-5`: agreement `AVAILABLE`, `authorizationStatus AUTHORIZED`,
`entitlementAvailability AVAILABLE`, `regionAvailability AVAILABLE`, `modelLifecycle ACTIVE`, the
use-case form present in all three routed Regions — and `AccessDeniedException: not available for
this account` for every principal including `AdministratorAccess`. **The invocation is the only
instrument that answers the question "can this model be used here".** Everything below narrows down
*why* a refusal happened; none of it substitutes for M6.

**The drift nothing else can see.** [`./aws/bedrock-scope.py`](../../../aws/bedrock-scope.py)
compares what this repository **declares** — read out of the SCP, not out of a constant — against
what AWS does: whether a profile still routes only where the condition names (`BS-3`), whether each
scoped model still holds an agreement (`BS-5`), whether every enabled Region declares `none`
(`BS-6`), and whether the SCP, the grant's `models` map and the image's pins still agree (`BS-7`).
Two of those facts are AWS's rather than ours and move without any diff here.

```bash
./aws/bedrock-scope.py
```

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
| Is the account's retention mode declared? | `aws bedrock get-account-data-retention` — `none`, with an `updatedAt`. The response field is **`mode`**; a `--query` naming `dataRetentionMode` returns `None`, which reads exactly like a Region that answered and declared nothing |
| Is the mode *frozen*, or merely set? | `put-account-data-retention --mode inherit` must be **refused naming the baseline's policy id**, and `--mode none` must still succeed beside it. Reading the document back says what is attached, not what evaluates (Lesson 20); the pair is the instrument, and it needs an account it is safe to write in |
| Is that mode *enforced*? | **No read answers this.** Availability and the agreement offer are identical for a retaining model and a scoped one. Only an invocation of a retaining model shows it (stage 7.2a) |
| Which models retain? | Not `allowed_modes` — it is in no Bedrock API. The vendor's abuse-detection page, dated when read; on 2026-09-11 it named the two Fable models, both present and available in `us-west-2` |
| Does the form exist? | `aws bedrock get-use-case-for-model-access --region us-west-2` — anything but `ResourceNotFoundException`. **Not** `get-foundation-model-availability` |
| Which Regions is a prompt processed in? | `get-inference-profile`, `models[].modelArn` — the routing is AWS's and can change under a pinned model id. `us-east-1`, `us-east-2`, `us-west-2` on 2026-09-12 (M0) |
| Is the retention mode declared **where the prompt is processed**? | `get-account-data-retention` **once per enabled Region**, not per routed Region — it answers per Region, and AWS can add a routed Region under a pinned model id. `BS-6` enumerates rather than carrying a list, so a Region opted into later shows up as `inherit` (M1) |
| Did a Control Tower console act propagate? | `organizations describe-policy --policy-id p-umksvu5a` from `awsds-infra-identity`, and count the `NotAction` entries — 86 in the base template, 92 on 2026-09-12. The *control* API answers from `Management` alone, but the SCP it writes is an Organizations document and reads from `Identity`. **Attempting the call is not the instrument**: it is refused whether the form failed to propagate or something else in the chain is missing (M5) |
| Is a model enabled for this account? | `get-foundation-model-availability`, `agreementAvailability.status`. `NOT_AVAILABLE` means **no agreement created**, not *none needed* (M4). It does **not** answer whether the model is invocable — see the warning above |
| Did the invocation take the private door? | CloudTrail in Sandbox: `InvokeModelWithResponseStream` is a **management event**, so the organization trail carries it with no data-event charge. The reading is `vpcEndpointId` on the event. **One invocation writes two events** — one carrying `requestParameters.modelId`, its sibling carrying `requestParameters: {}` — so counting events doubles and filtering on `modelId` halves (measured 2026-09-12, 15 events over one session) |
| Did it instead go out through the proxy? | `/awsds/prod/proxy` must hold **no** `bedrock-runtime` line for the same window. Two channels that do not share a failure mode — and the empty answer is evidence only with a **negative control**, since a log that saw nothing at all reads the same (Lesson 62). The control is the space's own address in that window: on 2026-09-12 `10.20.60.99` appears there tunnelling to `idetoolkits-hostedfiles.amazonaws.com` and being refused `default.exp-tas.com`, with no `bedrock` and no Anthropic name |
| Does the record carry the prompt? | It must not: `requestParameters` carries `modelId`, `responseElements` is `null` — attribution without content |
| Did the session reach any Anthropic host? | `/awsds/prod/proxy` for the session's window. The pass condition is that **no** Anthropic name appears at all |
| Is the session on Bedrock, in the right Region? | `/status` inside the session names the provider and the resolved Region |
| Does the picker offer exactly the scoped set? | `/model` |
| Did a background task bill Haiku? | the `modelId` on the CloudTrail event for a session-title call — and only when the primary model differs from it. The 2026-09-12 session pinned all three aliases to Haiku to work around the generation gate, so primary and background were indistinguishable and this row stayed unanswered |
| What does a session cost? | the session's own token accounting, against the rates in the stage's step 8.1 |

**What no instrument here reads**: the per-model `allowed_modes`. It is not in `get-foundation-model`,
`list-foundation-models` or `get-foundation-model-availability`, and no shape matching `allowed` exists
in any `bedrock*` service model the CLI ships (`aws-cli/2.36.18`, 2026-09-11). It is a vendor-page or
console reading, dated when taken — which is why M3's mode deny is the only mechanical guard.

---

*Stage: [`stage-06e-claude-code-bedrock.md`](../stages/stage-06e-claude-code-bedrock.md) ·
Log: [`log-stage-06e`](../../log/log-stage-06e-claude-code-bedrock.md) ·
Plan core: [`GENERAL_PLAN.md`](../../GENERAL_PLAN.md)*
