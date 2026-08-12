# `org-policies/` — the organization's preventive documents

**The JSON that is attached to the organization root and to the OUs.** Written by hand in
[Stage 1c](../../../plan/stages/stage-01c-preventive-policies.md) step 7, pasted into the Management
console as `AWS Control Tower Admin`, and **imported into Terraform at Stage 2 step 5.5** — which is the
reason the documents live in a file at all rather than only in the console: an import compares a document
against itself instead of against a re-typing.

This folder is documents only. There is no `.tf` here until Stage 2.

## Layout

| Path | What it is |
|---|---|
| `policies/` | The real documents. One file per policy, named exactly as the policy is named in Organizations |
| `canary/` | **Throwaway** documents, attached to `Policy Test` during the step 7.3 battery and detached in the same sitting. Never attached to anything real |
| `render.sh` | Substitutes this organization's identifiers into the templates and writes the pasteable copies to `aws/output/rendered-policies/` |

## The templates carry placeholders. Paste the *rendered* files

```bash
./terraform-live/identity/org-policies/render.sh
```

`<ORG_ID>`, `<ROOT_ID>`, `<OU_ID_DATA>` and `<ORG_PATH_DATA>` are filled from the Organizations API, and
the result lands in `aws/output/rendered-policies/` — which is untracked, so **no identifier enters a
tracked file** (`aws/INDEX.md` rule 1). `render.sh` also refuses to leave a placeholder unsubstituted,
checks that the JSON parses, and prints each document's size against **5 120 characters** — the RCP limit,
which is the tighter of the two since SCPs went to 10 240 in May 2026, and the right one to check when the
same folder holds both kinds.

Two reasons the ids are not baked in, and either alone would be enough: the organization id has to appear
in four documents and a value typed four times is eventually wrong in one of them, in the silent direction
(Lesson 14); and at Stage 2 the id comes from `data.aws_organizations_organization.this.id`, so a template
is already the right shape while a baked-in literal is an un-baking nobody remembers is pending.

## What is here, and what each document may not become

### `policies/awsds-org-scp-baseline.json` → organization **root**

`organizations:LeaveOrganization`, IAM-user creation, the account-level BPA deny **with its one carve-out**
(decision 7 — the single wildcard-account ARN in this design, whitelisted by name in Stage 2 step 9.2's
check), snapshot and AMI sharing, `ecr-public:*`, GuardDuty tampering, and `datazone:CreateDomain` outside
the `Data` OU.

**It deliberately carries no CloudTrail and no Config statement.** Control Tower's guardrails already deny
the Config recorder on every registered OU, with the `AWSControlTowerExecution` carve-out that keeps the
landing zone able to update itself — measured, not assumed, by `aws/org-policy-baseline.sh` section 4. For
CloudTrail the same measurement found **nothing denied anywhere**, and the user settled it as a deliberate
gap on 2026-08-13: the trail is organization-level and lives in the Management account, which is exempt
from SCPs by AWS's design, so a member-account deny would protect nothing. Written here because "we
checked and chose not to" and "we forgot" are indistinguishable a year later.

### `policies/awsds-org-scp-perimeter.json` → organization **root**

The `aws:ResourceOrgID` write deny, S3 and ECR only, and it is a separate document **because it is the one
most likely to be amended** — Stage 6 and Stage 9 both come back to it, and it is detached and re-attached
on its own rather than inside the document that also holds `iam:CreateUser`.

Three things about its shape that are invisible in review and obvious in the canary:

- **The action lists are enumerated, and an action wildcard is forbidden here** — `plan/conventions.md`
  carries the rule. `StringNotEqualsIfExists` evaluates **true when the key is absent**, so `s3:Put*` would
  reach the account-level `s3:PutAccountPublicAccessBlock` and deny, everywhere and for every principal,
  the call step 7.4 depends on. `ecr:GetAuthorizationToken` is left out for the same reason.
- **The four ECR actions, not `PutImage` alone.** `docker push` is `InitiateLayerUpload` →
  `UploadLayerPart` → `CompleteLayerUpload` → `PutImage`, and **the layers are the data**: denying only the
  manifest write is a completeness control that reads like an exfiltration control. The S3 half needs no
  equivalent — a multipart `UploadPart` is authorized as `s3:PutObject`.
- **`BoolIfExists: aws:PrincipalIsAWSService = false` is load-bearing, not boilerplate.** Without it the
  deny reaches calls AWS services make on your behalf, and service *principals* — unlike service-linked
  roles — are not exempt.

### `canary/awsds-canary-scp-perimeter-inverted.json` → `Policy Test`, temporarily

The perimeter statement with its comparison **inverted**: deny the same writes when `aws:ResourceOrgID`
**equals** this organization. It exists because the obvious test cannot be run — there is no bucket outside
this organization to write to, and `s3:PutObject` is a CloudTrail *data* event that the Control Tower trail
does not record, so the evidence would not exist in either direction (Lesson 13, in the verification rather
than in the control).

Attach it to `Policy Test`, write to a throwaway bucket in `Policy Canary` and run
`ecr initiate-layer-upload` against a throwaway repository there. Both must fail, and the error must name
*an explicit deny in a service control policy*. That proves the key populates, that the `IfExists` pair
evaluates the way it reads, and that the deny reaches an ordinary principal — **per service**, which is why
ECR is probed separately: key population is a property of each service's authorization, not of the policy.
Then detach it, delete the bucket and the repository in the same sitting, and attach the real document —
whose only difference is the direction of one comparison.

**What it does not prove**, so nobody reads more into it: that a write to a genuinely external bucket is
denied. That rests on the real document being the complement of the tested one, which is a one-character
review, and it is the honest limit of a lab with a single organization.

## Discipline

- **Record the returned policy id beside the filename**, in `log/stage-01c-preventive-policies.md`, **as
  each one is attached.** The detach command is the whole recovery path and it needs that id:

  ```bash
  aws organizations detach-policy --policy-id <POLICY_ID> --target-id <OU_OR_ACCOUNT_ID>
  ```

  Reading an id out of a console you have just denied yourself access to is the failure this rule prevents.
- **One policy at a time**: attach, exercise both halves in `Policy Canary`, record, move on.
- **Never add `aws_s3_account_public_access_block` to a slice** — `plan/conventions.md` says why, and the
  decision-7 carve-out makes the temptation worse rather than safer.

---

*Stage: [1c step 7](../../../plan/stages/stage-01c-preventive-policies.md) · Rules:
[`plan/conventions.md`](../../../plan/conventions.md) · What was measured:
[`aws/INDEX.md`](../../../aws/INDEX.md)*
