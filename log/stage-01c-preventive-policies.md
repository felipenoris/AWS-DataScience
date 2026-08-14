# Log — Stage 1c — Preventive policies: SCP, RCP, tag and declarative

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`plan/stages/stage-01c-preventive-policies.md`](../plan/stages/stage-01c-preventive-policies.md).*

*One exception, recorded so the provenance is not guessed later: **the 7.0 entries below were drafted by
Claude on 2026-08-13 at the user's explicit request**, from the two snapshots the same session produced.
Everything after them is the user's, as usual.*

---

- Started sitting A with step 7.0, the preflight. Nothing has been attached and nothing has been
  changed in AWS as of this entry — everything below is measurement.

- 7.0 was run from the laptop as the **infrastructure user**, profile `awsds-infra-identity`, through
  two read-only scripts written for this step. Both write to `aws/output/`, which is untracked:

```
./aws/org-policy-baseline.sh      # 7.0 steps 1, 2, 3 and 5
./aws/account-bpa.sh              # 7.0 step 4
```

- **7.0 step 1 — the organization's coordinates.** `FeatureSet` reads `ALL`, so RCPs are possible.
  Root is `r-zhj6`, organization is `o-4z1leiit0c`. The root's policy types:
  **`SERVICE_CONTROL_POLICY` `ENABLED` and nothing else** — as `AWS_STATE.md` section C expected.
  Step 7.2 still has to enable the other three.

- The OU tree, ids as measured. Depth is 2 (`Sandboxes` nested under `Interactive`), which is INV-03.
  Every ARN is `arn:aws:organizations::<MGMT_ACCOUNT_ID>:ou/o-4z1leiit0c/<ou-id>`; the literal ARNs are
  in section 2 of the snapshot.

  | OU | Id | Parent |
  |---|---|---|
  | Policy Test | `ou-zhj6-ebwso7wp` | root |
  | Workloads | `ou-zhj6-hisvfbzq` | root |
  | Identity | `ou-zhj6-hrcu9hog` | root |
  | Security | `ou-zhj6-u9qe0l0h` | root |
  | Interactive | `ou-zhj6-vn5q14hi` | root |
  | Data | `ou-zhj6-z3drywoq` | root |
  | Sandboxes | `ou-zhj6-mojnh3rs` | Interactive |

- The `Data` OU path that 7.5's `datazone:CreateDomain` carve-out is written from, with the trailing
  slash: `o-4z1leiit0c/r-zhj6/ou-zhj6-z3drywoq/`.

- **7.0 step 2 — what Control Tower already attaches.** `FullAWSAccess` (`p-FullAWSAccess`) is on the
  root and on every OU. One `aws-guardrails-*` policy per OU:

  | OU | Policy | Id |
  |---|---|---|
  | Policy Test | `aws-guardrails-vldGRP` | `p-kve97k0o` |
  | Workloads | `aws-guardrails-QWkHhe` | `p-xss3mf3w` |
  | Identity | `aws-guardrails-coSzJr` | `p-5wfd3ory` |
  | Security | `aws-guardrails-rFWRFL` | `p-2xyaqn66` |
  | Interactive | `aws-guardrails-lBxFwY` | `p-o32xhs2d` |
  | Data | `aws-guardrails-IErlqi` | `p-5weyyc6d` |
  | **Sandboxes** | **none** | — |

  No RCP, tag policy or declarative policy is attached anywhere — the listing returns
  `(policy type not enabled)`, which is the same fact as step 1 read from the other side.

- **Verification (iii), answered by reading the documents rather than by assuming.** Three findings, and
  two of them contradict what the stage file assumed:

  - **Config is already denied** on every OU that has a guardrail — `GRCONFIGENABLED` covers
    `config:DeleteConfigurationRecorder`, `PutConfigurationRecorder`, `StopConfigurationRecorder`,
    the delivery channel and the retention configuration, carved out for
    `arn:*:iam::*:role/AWSControlTowerExecution`. **7.5 must not write a second one.**
  - **CloudTrail is denied nowhere.** No `cloudtrail:` action appears in any of the six documents. The
    stage file assumed Control Tower covered it; it does not.
  - Also already covered, and therefore not to be duplicated: tampering with `aws-controltower-*` and
    `*AWSControlTower*` IAM roles and with `stacksets-exec-*`; `logs:DeleteLogGroup` and
    `logs:PutRetentionPolicy` on `*aws-controltower*` log groups; the Control Tower SNS topics,
    EventBridge rules, Lambda functions and S3 buckets. **GuardDuty is not covered**, which is why its
    four denies stay in `awsds-org-scp-baseline.json`.

- **`Identity` carries the standard Control Tower guardrail** — the same 8 statements as Workloads,
  Data, Interactive and Policy Test — so it is registered, contrary to what the plan assumed about an OU
  created outside Control Tower's own flow. `Security` is the only different one: 11 statements, the
  extra three (`CTSNSPV1`, `CTS3PV7`, `CTS3PV8`) being about the log-archive, access-logs and
  cloudtrail buckets and the centralized-logging SNS topic. **This is the `Security` vs `Identity` diff
  that 7.6 asks for, and it means nothing for an account that holds neither bucket** — so no elective
  control is owed to `Identity` on that basis.

- **`Sandboxes` is the only OU with no guardrail policy**, and `Sandbox Account 1` is inside it. Either
  the nested OU is not registered with Control Tower, or Control Tower relies on inheritance from
  `Interactive`. This is verification (xi) and it decides whether 7.7 can enable `CT.MULTISERVICE.PV.1`
  there. **Open until the Management run of 7.0 step 3.**

- **7.0 step 3 could not be answered from the laptop.** `controltower list-enabled-controls` failed on
  all seven OUs under `awsds-infra-identity` with:

```
An error occurred (ResourceNotFoundException) when calling the ListEnabledControls operation:
AWS Control Tower cannot complete the operation, because you must create a landing zone first.
```

  That is the answer a **member account** gets, not evidence about the landing zone — the API only
  answers in Management. Pending: run `bash org-policy-baseline.sh -` in CloudShell on Management as
  `AWS Control Tower Admin`.

- **Verification (x), answered: yes.** Every Organizations *policy* read — `ListPoliciesForTarget`,
  `DescribePolicy`, `DescribeOrganization`, `ListRoots`, `ListOrganizationalUnitsForParent` — answered
  from the Identity account. So 7.0 is a script, except for its Control Tower section. This extends the
  read boundary of Stage 1b step 4 once more.

- **7.0 step 5 — the quota is not published.** `service-quotas list-service-quotas --service-code
  organizations --region us-east-1` returns only account-related quotas (`Maximum number of accounts`,
  the billing-transfer ones), all with value `0.0`, and **nothing about policies per node or document
  size**. So the budget is the documented number and not a measured one. Counted against the
  conservative 5-per-node reading: the root will carry `FullAWSAccess` + baseline + perimeter +
  require-tags = **4**; each OU will carry `FullAWSAccess` + its guardrail + its tier + the Region
  control = **4**. It fits either way.

- **7.0 step 4 — account-level Block Public Access, before changing anything.** All six accounts with a
  profile — `awsds-infra-data`, `-dev`, `-identity`, `-prod`, `-sandbox-1` and `awsds-policy-canary` —
  return `NoSuchPublicAccessBlockConfiguration`, i.e. **NOT SET**. So 7.4 step 1 has real work in every
  one of them; nothing is a no-op. Management, Log Archive and Audit have no profile and are still to be
  read from CloudShell.

- **Decision recorded while executing: `awsds-org-scp-baseline.json` carries no CloudTrail deny.**
  Control Tower denies nothing about CloudTrail (above), and the deny was still not written: the trail
  is organization-level and lives in the Management account, which is exempt from SCPs by AWS's design,
  so a member-account deny would protect nothing. Recorded as a measured, deliberate gap rather than as
  an oversight.

- **The 7.5 documents were written before anything was attached**, as templates with placeholders, in
  `terraform-live/identity/org-policies/`:

  | File | Attaches to | Rendered size (minified) |
  |---|---|---|
  | `policies/awsds-org-scp-baseline.json` | organization root | 1279 characters |
  | `policies/awsds-org-scp-perimeter.json` | organization root | 716 characters |
  | `canary/awsds-canary-scp-perimeter-inverted.json` | `Policy Test`, throwaway | 724 characters |

  `./terraform-live/identity/org-policies/render.sh` substitutes the organization, root and `Data` OU
  ids and writes the pasteable copies into `aws/output/rendered-policies/`. **The console paste comes
  from there, not from the templates.** No policy has been created yet, so there is no policy id to
  record in this entry.

- One rule was added to `plan/conventions.md` while writing the perimeter document, because it decides
  its shape: in a deny conditioned on a resource key, the action list must be enumerated —
  `StringNotEqualsIfExists` evaluates *true* when the key is absent, so `s3:Put*` would reach the
  account-level `s3:PutAccountPublicAccessBlock` and deny, in every account and for every principal, the
  exact call 7.4 depends on. `ecr:GetAuthorizationToken` is left out of the ECR half for the same reason.

- **Still open in sitting A:** BPA in the six accounts, BPA in Management / Log Archive / Audit, the
  three `enable-policy-type` calls of 7.2, the 7.3 battery, and only then the two root attachments.

- **7.4 step 1 — account-level S3 Block Public Access, six of the nine accounts.** Set from the laptop
  as the **infrastructure user**, one `s3control put-public-access-block` per account with all four
  flags `true`: `awsds-infra-sandbox-1`, `-dev`, `-prod`, `-data` and `-identity` through
  `InfrastructureAccess`, and `awsds-policy-canary` through its direct `AWSAdministratorAccess`
  assignment (D32). There is no cross-account API for this setting — every call is made from *inside*
  the account it configures, which is the reason 7.4 states a list rather than an organization-wide
  action.

- `./aws/account-bpa.sh` re-run immediately afterwards: **6 of 6 measured accounts read `ALL FOUR
  true`**, where the same script had read `NOT SET` in all six a few hours earlier.
  `aws/output/account-bpa.txt` is the evidence. **Management, Log Archive and Audit are still unread
  and unset** — they hold no profile on this laptop — so 7.5 stays blocked.

- **The same thing is doable entirely from the console**, recorded because that is the screen a future
  reader will be looking at: *Console → Amazon S3 → Account and organization settings → Block Public
  Access settings for this account → Edit → Block all public access*. It writes the same account-level
  setting, one account at a time, and it is the path to use in Management, Log Archive and Audit if
  CloudShell is inconvenient there.

- Login as CT Admin on Management account, AWSAdministratorAccess.

- On Console, I can see that page AWS Organizations -> Policies says that these are not enabled: Resource Control Policies, Tag Policies, EC2 Policies.

- Executed on CloudShell:

```
aws organizations enable-policy-type --root-id r-zhj6 --policy-type RESOURCE_CONTROL_POLICY
aws organizations enable-policy-type --root-id r-zhj6 --policy-type TAG_POLICY
aws organizations enable-policy-type --root-id r-zhj6 --policy-type DECLARATIVE_POLICY_EC2
```

- Checked that policies are ENABLED, on the same CloudShell session:

```
$ aws organizations list-roots --query 'Roots[0].PolicyTypes' --output table
----------------------------------------
|               ListRoots              |
+----------+---------------------------+
|  Status  |           Type            |
+----------+---------------------------+
|  ENABLED |  DECLARATIVE_POLICY_EC2   |
|  ENABLED |  RESOURCE_CONTROL_POLICY  |
|  ENABLED |  SERVICE_CONTROL_POLICY   |
|  ENABLED |  TAG_POLICY               |
+----------+---------------------------+
```

- uploaded `org-policy-baseline.sh` script using Actions → Upload file. Executed on CloudShell. The result is at `aws/output/org-policy-baseline.txt`.

- Executed the following on accounts Management, Log and Audit, using CT Admin:

```
aws s3control put-public-access-block --account-id "$(aws sts get-caller-identity --query Account --output text)" --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
```

- Checked on each one that Block Public access on S3 was enabled (Amazon S3 -> Account and organization settings).


- Enabling RCP made AWS attach `RCPFullAWSAccess` to every node by itself, the way `FullAWSAccess` mirrors
  the SCP type. Nothing here attached it.

- **7.0 step 3 — controls per OU, which only Management answers.** `Workloads`, `Data`, `Interactive`,
  `Identity` and `Policy Test`: the same 9 `AWS-GR_*`, all `SUCCEEDED`. `Security`: those 9 plus
  `CT.S3.PV.7`, `CT.S3.PV.8`, `CT.SNS.PV.1` — the control half of its three extra SCP statements, so
  **7.6's `Security`/`Identity` diff is answered on both halves**. `Security` names them as
  `controlcatalog:::control/<opaque>`, every other OU as `controltower:…/AWS-GR_*`; `controlcatalog
  get-control` resolves either, `Aliases[0]` being the `AWS-GR_*` name.

- **`Sandboxes` returned an empty list, not an error** — no controls, no guardrail SCP. The plan's
  discriminator is that an unregistered target *errors*, but no call in the report failed (section 7:
  "None"), so it was never exercised in the failing direction. **Verification (xi) stays open; 7.7's
  `enable-control` settles it.**

- **The account quota reads 10, not the requested 15.** A member account reads 0.0, so only this
  Management run is evidence. The `Staging` vend stays held.

- **7.3 phase 0 — baseline in `Policy Canary`, nothing attached.** As `awsds-policy-canary`
  (`AWSAdministratorAccess`). Must-succeed half: `sts:GetCallerIdentity`, `s3 ls`
  (`s3:ListAllMyBuckets`, empty), `ec2:DescribeVpcs` `us-west-2`, `iam:ListRoles` (18),
  `budgets:DescribeBudgets` `us-east-1` (none) — all permitted. The last two answer in `us-east-1` and
  are the pre-state for 7.7's Region control.

- Throwaway resources created, to be deleted in phase 3: bucket `awsds-canary-throwaway-1786569935`
  and ECR repository `awsds-canary-throwaway`. Both writes baselined and **passing**: `s3:PutObject`
  (confirmed with `head-object` — `aws s3 cp` exits 0 with empty output, which is not evidence) and
  `ecr:InitiateLayerUpload` (`uploadId 1fceb2bf-…`, no bytes uploaded).

- Executing Stage 1c, step 7, sitting A, 7.3, phase 1. Login on console using CT Admin on Management account. AWS Organizations -> Policies -> Service control policies. Create policy:
  - policy name: `awsds-canary-scp-perimeter-inverted`
  - Description: THROWAWAY - Stage 1c step 7.3 battery. Detach and delete in the same sitting.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvertedDenyS3ObjectWriteInsideOrganization",
      "Effect": "Deny",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:PutObjectTagging",
        "s3:PutObjectVersionAcl",
        "s3:PutObjectVersionTagging",
        "s3:PutObjectRetention",
        "s3:PutObjectLegalHold"
      ],
      "Resource": "*",
      "Condition": {
        "StringEqualsIfExists": {
          "aws:ResourceOrgID": "o-4z1leiit0c"
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    },
    {
      "Sid": "InvertedDenyEcrPushInsideOrganization",
      "Effect": "Deny",
      "Action": [
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*",
      "Condition": {
        "StringEqualsIfExists": {
          "aws:ResourceOrgID": "o-4z1leiit0c"
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    }
  ]
}
```

- I can see a new policy listed with name `awsds-canary-scp-perimeter-inverted`, with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-539eaz19`.

- On the policy, clicked attach, selected org Policy Test (ou-zhj6-ebwso7wp). The console new lists that policy attached to Policy Test OU.

- **7.3 phase 1 — the inverted perimeter, `p-539eaz19` on `ou-zhj6-ebwso7wp` (`Policy Test`).**
  First run of both probes returned an **expired SSO session**, not a deny — discarded, re-logged in
  and re-run. Reading the error *wording* rather than the exit code is what caught it.

- Both probes then failed as required, and the message names the policy:

```
s3:PutObject             AccessDenied ... explicit deny in a service control policy: ... p-539eaz19
ecr:InitiateLayerUpload  AccessDeniedException ... explicit deny in a service control policy: ... p-539eaz19
```

  Same bucket, same repository, same principal as phase 0, so the only variable was the policy. Proves
  the `IfExists` pair evaluates as written, that the deny reaches an ordinary principal, and — the half
  S3 could not answer — that **`aws:ResourceOrgID` populates on an ECR request**. It does not prove a
  write to a genuinely external bucket is denied; that rests on the production document being the
  complement, `StringNotEqualsIfExists` where this one has `StringEqualsIfExists`.

- Login as CT Admin on Management Account. Detached `awsds-canary-scp-perimeter-inverted` from `Policy Test` OU an deleted the policy.

- Starting 7.3 phase 2. Login as CT Admin on Management Account. AWS Organizations -> Policies -> Service control policies. Create policy:
  - policy name: `awsds-org-scp-baseline`
  - Description: Stage 1c step 7.5 - organization baseline: LeaveOrganization, IAM users, account BPA (carve-out), snapshot and AMI sharing, ecr-public, GuardDuty, datazone outside Data OU.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyLeaveOrganization",
      "Effect": "Deny",
      "Action": "organizations:LeaveOrganization",
      "Resource": "*"
    },
    {
      "Sid": "DenyIamUserCreation",
      "Effect": "Deny",
      "Action": [
        "iam:CreateUser",
        "iam:CreateAccessKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyAccountBpaChangeExceptInfrastructure",
      "Effect": "Deny",
      "Action": "s3:PutAccountPublicAccessBlock",
      "Resource": "*",
      "Condition": {
        "ArnNotLike": {
          "aws:PrincipalArn": "arn:aws:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*"
        }
      }
    },
    {
      "Sid": "DenySnapshotAndImageSharing",
      "Effect": "Deny",
      "Action": [
        "ec2:ModifySnapshotAttribute",
        "ec2:ModifyImageAttribute",
        "rds:ModifyDBSnapshotAttribute",
        "rds:ModifyDBClusterSnapshotAttribute"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyEcrPublicEntirely",
      "Effect": "Deny",
      "Action": "ecr-public:*",
      "Resource": "*"
    },
    {
      "Sid": "DenyGuardDutyTampering",
      "Effect": "Deny",
      "Action": [
        "guardduty:DeleteDetector",
        "guardduty:UpdateDetector",
        "guardduty:DeleteMembers",
        "guardduty:DisassociateFromMasterAccount"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDataZoneDomainOutsideDataOu",
      "Effect": "Deny",
      "Action": "datazone:CreateDomain",
      "Resource": "*",
      "Condition": {
        "ForAllValues:StringNotLike": {
          "aws:PrincipalOrgPaths": "o-4z1leiit0c/r-zhj6/ou-zhj6-z3drywoq/"
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    }
  ]
}
```

- Policy `awsds-org-scp-baseline` created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-1fp032g8`. Attached to root account `r-zhj6`.

- **7.3 phase 2 — `awsds-org-scp-baseline` (`p-1fp032g8`) attached to the root `r-zhj6`.** Probes as
  `awsds-policy-canary`. Five denied, each naming `p-1fp032g8`: `iam:CreateUser`,
  `ec2:ModifyImageAttribute`, `ecr-public:DescribeRegistries`, `guardduty:DeleteDetector`, and
  `s3control:PutAccountPublicAccessBlock` from a principal outside the carve-out.

- **Decision 7 holds — the probe this phase was for.** The same `put-public-access-block` as
  `awsds-infra-dev` (`InfrastructureAccess`) **succeeded** with the policy attached, so
  `aws:PrincipalArn` names the right form: the `role/aws-reserved/sso.amazonaws.com/...` ARN, not the
  `assumed-role` one `get-caller-identity` prints. Had it failed, every future account would be
  permanently without account-level BPA and no principal could set it.

- Must-still-succeed half re-run under the new ceiling: the five phase-0 reads plus both in-org writes,
  all still permitted.

- **Two probes measured nothing, both because the service validates input before authorizing.**
  - `ec2:ModifySnapshotAttribute`: any invented snapshot id returns `InvalidSnapshotID.Malformed`,
    `--dry-run` included, so it never reaches the SCP. Left untested — the statement carries **no
    condition** and `ec2:ModifyImageAttribute`, denied above, is the **same statement**, so the only
    untested thing is one action string, verified by reading the rendered document.
  - `datazone:CreateDomain`: returns `Cross-account pass role is not allowed`. **The same error comes
    back from `awsds-infra-data`, the account the carve-out exempts** — an authorization difference
    would have made the two differ, so the probe measures nothing in either direction. Moved to
    **Stage 6 step 0**, before the domain is created, because `ForAllValues:` over a key that does not
    populate evaluates *true*: the untested failure is the deny applying to everyone, `Data` included.


- Login CT Admin on Management Account. AWS Organizations -> Policies -> Service control policies. Create policy:
  - policy name: `awsds-org-scp-perimeter`
  - Description: Stage 1c step 7.5 - trusted resources: deny S3 object writes and ECR layer/image pushes to resources outside this organization.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyS3ObjectWriteOutsideOrganization",
      "Effect": "Deny",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl",
        "s3:PutObjectTagging",
        "s3:PutObjectVersionAcl",
        "s3:PutObjectVersionTagging",
        "s3:PutObjectRetention",
        "s3:PutObjectLegalHold"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEqualsIfExists": {
          "aws:ResourceOrgID": "o-4z1leiit0c"
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    },
    {
      "Sid": "DenyEcrPushOutsideOrganization",
      "Effect": "Deny",
      "Action": [
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": "*",
      "Condition": {
        "StringNotEqualsIfExists": {
          "aws:ResourceOrgID": "o-4z1leiit0c"
        },
        "BoolIfExists": {
          "aws:PrincipalIsAWSService": "false"
        }
      }
    }
  ]
}
```

- Policy awsds-org-scp-perimeter created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-4vs49ztw`. Policy was attached to root account `r-zhj6`.

- - **7.3 phase 3 / 7.5 complete — `awsds-org-scp-perimeter` (`p-4vs49ztw`) attached to the root.** The
  root now carries `FullAWSAccess`, `p-1fp032g8` and `p-4vs49ztw`. The direction phase 1 could not test:
  both in-org writes **still succeed** — `s3:PutObject` (7 bytes confirmed) and
  `ecr:InitiateLayerUpload`. The statement does not over-reach, which was the expensive failure: it
  would have broken `docker push` to our own registry and every Stage 2 module writing to our own
  buckets.

- Must-still-succeed re-run with **both** documents attached: the five reads from the canary, plus
  `ec2:DescribeVpcs` and `s3 ls` from `awsds-infra-dev` — added outside the runbook, because a policy
  verified only in an empty account is verified against nothing.

- **Cleanup, same sitting.** Deleted `probe.txt`, `probe3.txt`, `probe4.txt`, `probe5.txt`, the bucket
  `awsds-canary-throwaway-1786569935` and the repository `awsds-canary-throwaway`. `Policy Canary` reads
  back empty: no buckets, no ECR repositories, 0 IAM users. `Policy Test` carries only `FullAWSAccess`
  and `aws-guardrails-vldGRP`.

- **Sitting A is closed: 7.0, 7.2, 7.3, 7.4 step 1 and 7.5 are done.** Sitting B is 7.6 (per-OU sets),
  7.7 (managed controls, which settles verification (xi) on `Sandboxes`) and 7.8 (RCP, tag, declarative).

- **7.6 — the four per-OU documents written; nothing created, nothing attached.**
  `terraform-live/identity/org-policies/policies/awsds-org-scp-ou-{workloads,data,interactive,identity}.json`.
  `render.sh` gained one placeholder, `<ACCOUNT_ID_DATA>`, resolved by
  `organizations list-accounts-for-parent` over the `Data` OU — exactly one active account, or it stops.

- Rendered (read-only), pasteable copies in `aws/output/rendered-policies/`:

```
./terraform-live/identity/org-policies/render.sh
```

```
awsds-org-scp-ou-workloads.json
awsds-org-scp-ou-data.json
awsds-org-scp-ou-interactive.json
awsds-org-scp-ou-identity.json
```

- **Verification (viii) answered by reading AWS's machine-readable action list**, one JSON per service at
  `https://servicereference.us-east-1.amazonaws.com/v1/<service>/<service>.json`. `sagemaker:CreateSpace`,
  `CreateApp` and `StartSession` all exist today — `StartSession` is the local-IDE-to-space connection —
  and a Unified Studio domain is created through `datazone:CreateDomain`, with no `sagemaker:Create*` in
  that path. So the `Data` OU keeps its `sagemaker:Create*` wildcard and **no carve-out was widened**;
  `Workloads` stays enumerated, because `CreateModel`/`CreateEndpoint`/`CreateTrainingJob` are its job.

- Attach targets read from `awsds-infra-identity` (read-only), recorded here because 7.6 needs them:
  `Workloads ou-zhj6-hisvfbzq`, `Data ou-zhj6-z3drywoq`, `Interactive ou-zhj6-vn5q14hi`,
  `Identity ou-zhj6-hrcu9hog`, `Policy Test ou-zhj6-ebwso7wp`. `Sandboxes ou-zhj6-mojnh3rs` gets
  **nothing**: it inherits `Interactive`'s set.

- The `Data` document's crawler carve-out names `awsds-data-catalog-maintenance`, which does not exist
  until Stage 5 — its **positive half is untested**, not passed.

- Documentation written in the same sitting: `terraform-live/README.md` and
  `terraform-live/identity/org-policies/SCPs.md` (both new), the battery runbook's **phase 4** (the four
  documents, parked on `Policy Test`, then re-probed from each OU's own account), and the role-name
  contract in Stage 5.

- Login in Console as AWS Control Tower Admin, management account, ps AWSAdministratorAccess. AWS Organizations -> Policies -> Service control policies. Create policy:
  - policy name: `awsds-org-scp-ou-workloads`
  - Description: Stage 1c step 7.6 - Workloads OU: no interactive SageMaker surface, no DataZone.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInteractiveSageMakerSurface",
      "Effect": "Deny",
      "Action": [
        "sagemaker:CreateDomain",
        "sagemaker:CreateUserProfile",
        "sagemaker:CreatePresignedDomainUrl",
        "sagemaker:CreateSpace",
        "sagemaker:CreateApp",
        "sagemaker:StartSession",
        "sagemaker:CreateNotebookInstance",
        "sagemaker:CreatePresignedNotebookInstanceUrl"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyDataZoneEntirely",
      "Effect": "Deny",
      "Action": "datazone:*",
      "Resource": "*"
    }
  ]
}
```

- policy `awsds-org-scp-ou-workloads` created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-83t232f4`. Policy attached to `Policy Test` OU.

- Create policy:
  - policy name: `awsds-org-scp-ou-interactive`
  - Description: Stage 1c step 7.6 - Interactive OU (Development + the nested Sandboxes): deny the classic SageMaker notebook instance and its presigned URL. SMUS notebooks are spaces and apps and are unaffected.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyClassicNotebookInstances",
      "Effect": "Deny",
      "Action": [
        "sagemaker:CreateNotebookInstance",
        "sagemaker:CreatePresignedNotebookInstanceUrl"
      ],
      "Resource": "*"
    }
  ]
}
```

- Policy `awsds-org-scp-ou-interactive` created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-tgda7n58`. Policy attached to `Policy Test` OU.


- Create policy:
  - policy name: `awsds-org-scp-ou-identity`
  - Description: 
  - Used this JSON:

```JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUserCompute",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "sagemaker:Create*",
        "sagemaker:StartSession",
        "glue:CreateDevEndpoint",
        "glue:CreateJob",
        "glue:StartJobRun",
        "glue:CreateSession",
        "glue:RunStatement",
        "glue:CreateMLTransform",
        "glue:StartNotebook",
        "lambda:CreateFunction",
        "ecs:RegisterTaskDefinition",
        "ecs:RunTask",
        "ecs:CreateService"
      ],
      "Resource": "*"
    }
  ]
}
```

- Policy `awsds-org-scp-ou-identity` created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-mmfc17ac`. Policy attached to `Policy Test` OU.

- Create policy:
  - policy name: `awsds-org-scp-ou-data`
  - Description: Stage 1c step 7.6 - Data OU: deny user compute; crawler and column-statistics runs allowed only for awsds-data-catalog-maintenance (D27); deny bucket deletion and Lake Formation deregistration.
  - Used this JSON:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyUserCompute",
      "Effect": "Deny",
      "Action": [
        "ec2:RunInstances",
        "sagemaker:Create*",
        "sagemaker:StartSession",
        "glue:CreateDevEndpoint",
        "glue:CreateJob",
        "glue:StartJobRun",
        "glue:CreateSession",
        "glue:RunStatement",
        "glue:CreateMLTransform",
        "glue:StartNotebook",
        "lambda:CreateFunction",
        "ecs:RegisterTaskDefinition",
        "ecs:RunTask",
        "ecs:CreateService"
      ],
      "Resource": "*"
    },
    {
      "Sid": "DenyCatalogMaintenanceRunsExceptMaintenanceRole",
      "Effect": "Deny",
      "Action": [
        "glue:StartCrawler",
        "glue:StartCrawlerSchedule",
        "glue:StartColumnStatisticsTaskRun",
        "glue:StartColumnStatisticsTaskRunSchedule"
      ],
      "Resource": "*",
      "Condition": {
        "ArnNotEquals": {
          "aws:PrincipalArn": "arn:aws:iam::782981553460:role/awsds-data-catalog-maintenance"
        }
      }
    },
    {
      "Sid": "DenyLakeDeletionAndDeregistration",
      "Effect": "Deny",
      "Action": [
        "s3:DeleteBucket",
        "lakeformation:DeregisterResource"
      ],
      "Resource": "*"
    }
  ]
}
```

- policy `awsds-org-scp-ou-data` created with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-gl01bcdm`. Attached to `Policy Test` OU.

- **7.6 — the four policies created (CT Admin @ Management, console) and all four attached to
  `Policy Test` at once**, deliberately, for the battery's phase 4. None has moved to its target OU yet:

| Policy | Id | Target during the battery |
|---|---|---|
| `awsds-org-scp-ou-workloads` | `p-83t232f4` | `Policy Test` `ou-zhj6-ebwso7wp` |
| `awsds-org-scp-ou-data` | `p-gl01bcdm` | idem |
| `awsds-org-scp-ou-identity` | `p-mmfc17ac` | idem |
| `awsds-org-scp-ou-interactive` | `p-tgda7n58` | idem |

- The SSO token expired between the rendering and the battery — again. Re-login before the probes
  (`aws sso login --sso-session awsds`); without it every probe comes back with an error that reads
  like a deny.

- **The floor, before any deny probe** (`awsds-policy-canary`): `sts:GetCallerIdentity`, `s3 ls` (empty,
  no error), `ec2:DescribeVpcs`, `iam:ListRoles`, `budgets:DescribeBudgets`, `ce:GetCostAndUsage` — all
  pass. Two read controls named by no document, `sagemaker:ListDomains` and `glue:GetDatabases`, are still
  allowed: the denies are not a blanket.

- **Deny probes — all denied, and the CLI error names the policy id:**

| Probe | Outcome | Policy |
|---|---|---|
| `datazone:ListDomains` | denied | `p-83t232f4` |
| `sagemaker:CreateSpace` | denied | `p-mmfc17ac` (`Create*`) |
| `sagemaker:StartSession` | denied | `p-mmfc17ac` |
| `sagemaker:CreateNotebookInstance` | denied | `p-83t232f4` |
| `sagemaker:CreatePresignedNotebookInstanceUrl` | denied | `p-mmfc17ac` (`Create*`) |
| `ec2:RunInstances --dry-run` | denied (`UnauthorizedOperation`) | `p-mmfc17ac` |
| `glue:StartJobRun` | denied | `p-gl01bcdm` |
| `glue:StartCrawler` | denied | `p-gl01bcdm` |
| `lakeformation:DeregisterResource` | denied | `p-gl01bcdm` |
| `s3:DeleteBucket` | **untested** — `NoSuchBucket`, before authorization | — |

- **The API error carries the policy id** — `... with an explicit deny in a service control policy:
  arn:aws:organizations::.../service_control_policy/p-xxxxxxxx` — no CloudTrail and no lag. That is what
  makes it survivable to park four candidates on one target. **The limit:** when more than one attached
  policy denies the same call, AWS names **one** of them, so `p-tgda7n58` (interactive) decided no probe
  at all: it is **attached and unexercised**. It isolates itself in `Interactive`, where nothing else
  denies `CreateNotebookInstance`.

- **`ec2:RunInstances` only reaches authorization with a real AMI and a real subnet.** An invented AMI
  returns `InvalidAMIID.Malformed`; a well-formed but non-existent one `InvalidAMIID.NotFound`; omitting
  the subnet `VPCIdNotSpecified` — all three before authorizing. With real ids the `--dry-run` still
  creates nothing:

```
aws ssm get-parameter --name /aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64 --region us-west-2 --profile awsds-policy-canary --query Parameter.Value --output text
aws ec2 describe-subnets --region us-west-2 --profile awsds-policy-canary --query 'Subnets[0].SubnetId' --output text
aws ec2 run-instances --dry-run --image-id <AMI> --instance-type t3.micro --subnet-id <SUBNET> --region us-west-2 --profile awsds-policy-canary
```

- **`s3:DeleteBucket` stays untested**, on sitting A's argument: its sibling in the same `Sid`
  (`lakeformation:DeregisterResource`) was denied, so the statement evaluates; what is unverified is the
  spelling of one action. Testing it for real would need a bucket that could not be deleted while the
  policy stayed attached.

- **`glue:StartCrawler` denied is the negative half of D27's carve-out** — the canary is not
  `awsds-data-catalog-maintenance`, and the `ArnNotEquals` condition evaluated. The positive half remains
  **untested until Stage 5**, when the role exists.

- **Nothing was created in `Policy Canary`:** every probe used a non-existent id or `--dry-run`. The
  account is still empty.

- Login as CT Admin on management account, AWS Console. Detached all 4 policies (data, identity, interactive, workload) from Policy Test OU. Attached each one to the final OU.
    - awsds-org-scp-ou-data -> Data OU
    - awsds-org-scp-ou-identity -> Identity OU
    - awsds-org-scp-ou-interactive -> Interactive OU
    - awsds-org-scp-ou-workloads -> Workloads OU

- **7.6 — the four documents moved to their target OUs and re-probed there.** Each OU now shows
  `FullAWSAccess` + its Control Tower guardrail + exactly one of ours; `Policy Test` is back to its
  baseline and `Sandboxes` still carries no policy of its own:

| OU | Target id | Policy |
|---|---|---|
| `Workloads` | `ou-zhj6-hisvfbzq` | `awsds-org-scp-ou-workloads` `p-83t232f4` |
| `Data` | `ou-zhj6-z3drywoq` | `awsds-org-scp-ou-data` `p-gl01bcdm` |
| `Interactive` | `ou-zhj6-vn5q14hi` | `awsds-org-scp-ou-interactive` `p-tgda7n58` |
| `Identity` | `ou-zhj6-hrcu9hog` | `awsds-org-scp-ou-identity` `p-mmfc17ac` |

- **Isolation probes, each from that OU's own account** (the canary cannot reach these OUs):

| Account / OU | Probe | Outcome |
|---|---|---|
| `awsds-infra-prod` / `Workloads` | `datazone:ListDomains`, `sagemaker:CreateSpace`, `CreateNotebookInstance` | denied, all by `p-83t232f4` |
| `awsds-infra-dev`, `awsds-infra-sandbox-1` / `Interactive` | `sagemaker:CreateNotebookInstance` | denied by `p-tgda7n58` |
| same | `sagemaker:CreateSpace`, `datazone:ListDomains` | **allowed** |
| `awsds-infra-data` / `Data` | `glue:StartJobRun`, `StartCrawler`, `sagemaker:CreateSpace`, `lakeformation:DeregisterResource`, `ec2:RunInstances --dry-run` | denied, all by `p-gl01bcdm` |
| same | `datazone:ListDomains`, `glue:GetDatabases`, `s3 ls`, `ec2:DescribeVpcs` | allowed |
| `awsds-infra-identity` / `Identity` | `glue:StartJobRun`, `sagemaker:CreateSpace`, `ec2:RunInstances --dry-run` | denied by `p-mmfc17ac` |
| same | `glue:StartCrawler`, `lakeformation:DeregisterResource` | **allowed** (`EntityNotFoundException`) |

- **The `Interactive` document was only proven after the move.** Parked on `Policy Test` alongside the
  other three it decided no probe at all — its two actions are also denied by the `Workloads` document and
  matched by `Identity`'s `sagemaker:Create*`, and AWS names one policy per denial. In `Interactive`,
  nothing else denies `CreateNotebookInstance` and one call settled it. Written up as **Lesson 20**.

- **Decision 1 costs no feature, and it is now measured rather than argued:** in Development and in
  Sandbox Account 1, `sagemaker:CreateSpace` and `datazone:ListDomains` still work while the classic
  notebook instance is denied.

- **`Sandboxes` is governed by inheritance** — the same deny fires in `awsds-infra-sandbox-1`, with no
  policy attached to that OU. This is the **SCP half** of verification (xi); whether the OU can carry an
  *enabled Control Tower control* is a different question and stays open for 7.7.

- **The Data/Identity cross-check is the strongest single result of the sitting:** `glue:StartCrawler` and
  `lakeformation:DeregisterResource` are denied in Data Governance and **allowed** in Identity. Those two
  statements exist only in the `Data` document, so nothing is leaking from the root set and the two
  documents differ exactly where they were written to differ.

- Still **untested**, unchanged by the move: `s3:DeleteBucket` (S3 answers `NoSuchBucket` before
  authorizing; its `Sid` is proven through `lakeformation:DeregisterResource`) and the **positive** half of
  the D27 carve-out, which needs Stage 5's `awsds-data-catalog-maintenance` role.

- Nothing was created in any account: every probe used a non-existent id or `--dry-run`.

- **7.5a and 7.6a uploaded and exercised.** All three documents read back from Organizations before any
  probe: `awsds-org-scp-baseline` `p-1fp032g8` at **8 statements** (`DenyImageAndSnapshotExport` added,
  `DenyGuardDutyTampering` at 9 actions), `awsds-org-scp-ou-data` `p-gl01bcdm` and
  `awsds-org-scp-ou-identity` `p-mmfc17ac` at **18 actions** in `DenyUserCompute`, with the
  `BoolIfExists: aws:PrincipalIsAWSService=false` guard live in the `Data` carve-out. Rendered sizes:
  baseline 1651, data 1028, identity 494 — the other three documents were byte-identical to what was
  already attached and were not re-uploaded.

- **Phase 4b, in each OU's own account** (the canary cannot reach these OUs):

| Probe | `awsds-infra-data` | `awsds-infra-identity` |
|---|---|---|
| `ec2:RequestSpotInstances`, real AMI + real subnet, `--dry-run` | denied by `p-gl01bcdm` | denied by `p-mmfc17ac` |
| `ec2:CreateFleet`, `--dry-run` | denied by `p-gl01bcdm` | denied by `p-mmfc17ac` |
| `ec2:StartInstances`, `--dry-run` | **untested** — `Malformed` at 17 chars, `NotFound` at 8 | **untested** |
| `glue:StartCrawler` | denied by `p-gl01bcdm` | **allowed** (`EntityNotFoundException`) |
| floor: `sts`, `s3 ls`, `describe-vpcs`, `glue get-databases` | all OK | all OK |

  The crawler row is the regression that mattered: the new service guard did **not** invert the carve-out —
  a human principal still lands on the deny side in Data — and the Data/Identity asymmetry still holds.

- **Phases 1-3 on `awsds-policy-canary`, for the root document. Seven probes, seven denies, every one
  naming `p-1fp032g8`:** `guardduty:DisassociateFromAdministratorAccount` (the spelling that was open
  before this amendment), `guardduty:UpdateDetector`, `guardduty:StopMonitoringMembers`,
  `ec2:ExportImage`, `ec2:CreateInstanceExportTask`, `ec2:CreateStoreImageTask` and `rds:StartExportTask`.
  Floor intact (`sts`, `s3 ls`, `describe-vpcs`).

- **GuardDuty authorizes before validating the detector id**, so all three of its probes measured with an
  invented id — which is what made the amendment provable while the service is still off everywhere.

- **Two predictions in the runbook were wrong, both in the same direction, and the correction is the
  finding worth keeping.** `ec2:CreateFleet` was expected to be untestable for want of a launch template
  and was denied anyway — `--dry-run` authorizes before resolving the template — so the door this
  amendment was written for is proven directly rather than by inference. And the EC2/RDS block was expected
  to come back mostly *untested*: **the validation-before-authorization wall is per *action*, not per
  service.** `ExportImage` and `CreateInstanceExportTask` authorized against a malformed AMI id;
  `CreateStoreImageTask` rejected the same shape and only reached authorization with a real public AMI;
  `StartInstances` never reached it. Written up as **Lesson 21**: a first-try validation error is a reason
  to retry with an id that exists, not a result.

- Nothing was created anywhere: spot requests, fleets, store-image tasks and both flavours of export task
  all read zero afterwards.

- Login as CT Admin -> Management Account. AWS Control Tower -> Controls -> Control Catalog. Searched for `CT.MULTISERVICE.PV.1` (Deny access to AWS based on the requested AWS Region for an organizational unit). Selected -> Enable -> Policy Test  -> Regions to allow access = `us-west-2`. Generated a policy named `aws-guardrails-njKkvb` with ARN `arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-q3y11w1n` attached to `Policy Test` OU.

- **Probes after enabling `CT.MULTISERVICE.PV.1` on `Policy Test`** (`./aws/probes/scp-battery.sh --phase region`):
  `us-east-1` denied naming `p-q3y11w1n`, `us-west-2` still `DryRunOperation`, and the four global floors
  (`iam:ListRoles`, `budgets:DescribeBudgets`, `ce:GetCostAndUsage`, `organizations:DescribeOrganization`)
  intact. **Exactly one row flipped**, which is what distinguishes the intended control from the loose
  construction that adds `us-east-1` to the allowed list.
  The first version of that probe was wrong and the control exposed it: it resolved its AMI through
  `ssm:GetParameter` **in the region being denied**, so the resolution itself was denied and the probe
  degraded to `UNTESTED` at the moment it finally had something to measure. Replaced with
  `ec2:CreateKeyPair --dry-run`, which authorizes with nothing but a name.

- **Verification (vii), read from the attached document rather than the console's `Artifacts` tab** —
  the control lands as an ordinary SCP, so `describe-policy` answers it and the answer is repeatable per OU.
  **86 `NotAction` entries, no `ExemptedActions` of ours**, condition `aws:RequestedRegion = ["us-west-2"]`
  plus the four Control Tower roles the plan predicted. Every global prefix this project calls is present,
  `route53domains` and the three S3 account-level actions included. **It falsified a prediction of this
  stage: `ecr-public:*` is exempt**, so the Region control never denied it and `DenyEcrPublicEntirely` is
  the only thing that does. `ssm:GetParameter`, `cloudshell:*` and `servicequotas:*` are **not** exempt.

- Login as CT Admin -> Management Account. AWS Control Tower -> Controls -> Control Catalog. Enabled control `CT.MULTISERVICE.PV.1` with allow region `us-west-2` for OUs: Interactive, Workloads, Data, Identity, Sandboxes.

- Also, enabled `AWS-GR_RESTRICT_ROOT_USER` (ARN `arn:aws:controlcatalog:::control/5kvme4m5d2b4d7if2fs5yg2ui`) and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` (ARN `arn:aws:controlcatalog:::control/8ui9y3oace2513xarz8aqojl7`) for `Policy Test` OU.

- **After enabling on the five remaining OUs, the battery ran whole: 61 as expected, 0 unexpected,
  0 untested.** `us-east-1` denied and `us-west-2` working in Data Governance (`p-pk85fvr1`), Identity
  (`p-fw2pctqw`), Development (`p-umksvu5a`), Sandbox Account 1 (`p-umksvu5a`), Production (`p-i0ney7mx`)
  and Policy Canary (`p-q3y11w1n`), with `iam:ListRoles` alive in every one.

- **Verification (xi) is closed in both halves.** `Sandboxes` accepted `enable-control` and now carries
  `aws-guardrails-yvYgxw` (`p-h7lc62d0`) — the first policy that OU has ever held — so it **is** a
  registered target. But the deny measured in Sandbox Account 1 names `p-umksvu5a`, `Interactive`'s policy:
  two policies deny the call and AWS names one, and the inherited one won. **Attribution answered coverage
  and said nothing about registration**; the OU's attached-policy list is what answered it.

- **Every OU now carries two `aws-guardrails-*` documents** — its original guardrail plus one holding
  `CT.MULTISERVICE.PV.1` — **except `Sandboxes`, which carries one**. `Policy Test` is different in kind:
  its two root-user controls were folded into its **existing** guardrail document rather than a new one, so
  Control Tower packs per enablement and counting policies is not counting controls.

- **OPEN, and the one thing 7.7 leaves owed: `AWS-GR_RESTRICT_ROOT_USER` was enabled on `Policy Test`
  without `ExemptAssumeRoot`.** Read from `aws-guardrails-vldGRP` (`p-kve97k0o`): `GRRESTRICTROOTUSER` is
  `Deny *` on `ArnLike aws:PrincipalArn = arn:*:iam::*:root` with no second condition, and the string
  `aws:AssumedRoot` appears in no policy in this organization. So `sts:AssumeRoot` into the canary — 1a
  step 6's member-account recovery — is denied.
  **No probe can measure this**: every principal available here is an Identity Center role and
  `ArnLike …:root` never matches one, so the document read is the only instrument. Blast radius is one
  throwaway account, and Management stays SCP-exempt (D16). **Fix: disable, re-enable with the parameter,
  re-read the document, and only then take the control to the other five OUs.**

- Edited - Also, enabled `AWS-GR_RESTRICT_ROOT_USER` (ARN `arn:aws:controlcatalog:::control/5kvme4m5d2b4d7if2fs5yg2ui`), setting `ExemptAssumeRoot` option.

- **Read back after the fix, from Identity** (`organizations describe-policy p-kve97k0o`):
  `GRRESTRICTROOTUSER` now ANDs `"Null": {"aws:AssumedRoot": "true"}` with the root-ARN test, so the deny
  reaches every root principal *except* a privileged session. **The policy id did not change** — Control
  Tower edited the document in place rather than issuing a new one. Org-wide, `aws:AssumedRoot` appears in
  **exactly one** policy and the two root-user statements exist **only** there: the controls are still
  `Policy Test`-only.
  `GRRESTRICTROOTUSERACCESSKEYS` carries no exemption and should not — the parameter does not exist on that
  control, and a root access key minted inside a privileged session is precisely what D16 forbids.
  No battery run: nothing the probes measure changed, and this statement is invisible to them in both
  directions.

- Disabled `CT.MULTISERVICE.PV.1` for `Sandboxes` OU. This OU is under `Interactive` with the same control.

- Enabled `AWS-GR_RESTRICT_ROOT_USER` (ARN `arn:aws:controlcatalog:::control/5kvme4m5d2b4d7if2fs5yg2ui`), setting `ExemptAssumeRoot` option, and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` (ARN `arn:aws:controlcatalog:::control/8ui9y3oace2513xarz8aqojl7`) on Interactive, Workloads, Data and Identity OUs.

- Login as CT Admin -> Management Account. Enabled `AWS-GR_RESTRICT_ROOT_USER` (with `ExemptAssumeRoot`)
  and `AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS` on `Workloads`, `Data`, `Interactive` and `Identity`.
  Disabled `CT.MULTISERVICE.PV.1` on `Sandboxes`.

- **Read back per OU from Identity — `aws:AssumedRoot` is present in every document that carries
  `GRRESTRICTROOTUSER`**, which is the whole test, on all five OUs that hold these controls
  (`Policy Test`, `Workloads`, `Data`, `Interactive`, `Identity`). The parameter was not missed anywhere.

- **Control Tower's packing is inconsistent across OUs, and this is the finding that outlives the step.**
  The two root statements were folded into the **original guardrail** on `Policy Test` (`p-kve97k0o`),
  `Workloads` (`p-xss3mf3w`) and `Interactive` (`p-o32xhs2d`), but into the **`CT.MULTISERVICE.PV.1`
  document** on `Identity` (`p-fw2pctqw`) and `Data` (`p-pk85fvr1`) — the same two ids this log records as
  "the Region policy" for those OUs. The battery's results stand, but **a document's id no longer says what
  is inside it**. Read the `Sid` list; never infer from what the document was created for.

- **`Sandboxes` is back to `FullAWSAccess` and nothing else**, and `p-h7lc62d0` no longer exists in the
  organization — disabling the control deleted the document. **The rule this settles (user, 2026-08-13):
  nothing is attached or enabled on `Sandboxes` unless it is a configuration that *differs* from
  `Interactive`'s.** Verification (xi) had already answered both halves, so this is a knowing decline, not
  a limitation: the OU is a registered target and would take an enablement. What it costs is Control
  Tower's reporting — an enablement is per OU and is not inherited, only the statements are — so
  `Sandboxes` reads as zero controls while its accounts are fully governed.

- **`Security` carries neither the Region control nor the root ones**, having never been a target of 7.7.
  So `Log Archive` and `Audit` are the two accounts with no Region ceiling. Recorded, not acted on: that
  OU is Control Tower's own and Stage 1d is where it gets touched.

- This closes 7.7.

### After 7.7 — the review pass, 2026-08-13

- **Reviewed the section against plan, rules, decisions and lessons.** What came out of it that is not a
  restatement of something already written: **Lesson 22** — a control whose principal the harness cannot
  produce is verified by *reading*, and the `ExemptAssumeRoot` omission proved it by surviving a 61/61
  battery; **Lesson 23** — Control Tower packs per enablement and inconsistently, so bind to the `Sid`;
  **D37** — nothing on `Sandboxes` unless it differs from `Interactive`; and **open question 16** —
  `Log Archive` and `Audit` have no Region ceiling, addressed to Stage 1d.

- **`./aws/org-policies.sh` written**, the post-attachment counterpart to `org-policy-baseline.sh`'s
  preflight: condensed by `Sid`, inheritance resolved per account, and it runs the checks no probe can
  reach — **exits 2 when one fails**. First run: 20 checks, 0 failures. Two bugs found by running it, both
  worth recording because they produce *plausible* output rather than an error: a variable set inside a
  command substitution never returns to the parent, and BSD `paste -sd ', '` reads the string as a rotating
  list of delimiters.

### 7.8 — the documents, none of them attached yet

- **Decision 5 settled by measurement, and the measurement inverted this plan's own premise.** From the
  machine-readable service reference: **`s3:CreateBucket` does map `aws:RequestTag`/`aws:TagKeys`** (1 of 11
  S3 actions), so the 2026-08-09 reasoning that excluded S3 is stale — but the deciding question is now
  whether the Terraform provider sends the tags *on the create call*, and that is answered at Stage 2 for
  free. `rds:CreateDBInstance` maps it and is **inert** — no RDS here. **`ec2:RunInstances` could not be
  measured this way at all: 0 of EC2's 793 actions map the key while EC2 declares it at the service level**
  — a gap in the instrument, not a fact about EC2, recorded beside the link in `REFERENCES.md`. Scope is
  therefore `ec2:RunInstances` alone, to be settled by probe after attachment.

- **Four documents written and rendered**, all minified well inside the tighter 5 120 limit:
  `awsds-org-rcp-perimeter.json` (RCP, 1150), `awsds-org-scp-tag-enforcement.json` (SCP, 518),
  `awsds-org-tag-policy.json` (tag policy, 430), `awsds-org-declarative-ec2.json` (declarative EC2, 640).

- **`SCPs.md` now indexes all four policy types** and `check-index.sh` is type-aware — `Sid`s for SCP/RCP,
  tag keys for a tag policy, `ec2_attributes` names for a declarative one, with an unrecognised document
  stopping the run rather than being skipped. Ten documents, `clean`.

- Three choices made while writing, recorded because a later reader will otherwise assume the opposite:
  **the tag policy enforces nothing** (no `enforced_for` — it reports); **`http_tokens_enforced` is
  deliberately not set**, so IMDSv2 is the account default and not yet a ceiling, to be turned on once
  Stage 4 and Stage 7 have launched successfully; and **`serial_console_access: disabled` is beyond what
  7.8 listed**, added because the serial console reaches an instance without traversing any network.

---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
