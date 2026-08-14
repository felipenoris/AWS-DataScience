# Log — Stage 1d — Audit trail, Config scope, org-wide enablement

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`plan/stages/stage-01d-org-wide-enablement.md`](../plan/stages/stage-01d-org-wide-enablement.md).*

*One exception, recorded so the provenance is not guessed later: **the entries of 2026-08-14 below were
drafted by Claude at the user's explicit request**, from readings Claude took on the laptop in that same
session. Everything after them is the user's, as usual.*

---

## 2026-08-14 — readings only, before the stage starts

**Nothing has been created, attached or changed in AWS as of this entry.** Every line below is a
measurement, taken from the laptop as the **infrastructure user** through the profiles of Stage 1b step 5.
They exist because Stage 1c closed the same day and three of this stage's steps were written against a
world that had changed — the revision they produced is in the stage file, not here.

- **The CloudTrail bucket is not the name this project had been carrying, and the trail's validation is
  already on.** From `awsds-infra-identity`, `cloudtrail describe-trails` in `us-west-2`:

```
Name:       aws-controltower-BaselineCloudTrail
Bucket:     aws-controltower-cloudtrail-logs-859928915710-gcs-gsx
IsOrganizationTrail: true      LogFileValidationEnabled: true      HomeRegion: us-west-2
```

  So **step 9.4 is answered before the stage starts** — verify, do not enable — and it is answered from a
  *member* account, which extends 1b step 4's read boundary once more: the organization trail's
  configuration is readable without Management. The bucket prefix the stage file used until today,
  `aws-controltower-logs-`, matches **nothing** here; a `list-buckets` filtered on it returns `None`, which
  reads like a failed Object Lock rather than a wrong prefix.

- **Step 9 is denied to every principal but one, and the deny is AWS's own.** `describe-policy` on
  `p-2xyaqn66` (`aws-guardrails-rFWRFL`, the Control Tower guardrail on the `Security` OU, 11 statements):

  - **`CTS3PV8`** — `Effect: Deny`, `Resource` = `aws-controltower-access-logs-*`,
    `aws-controltower-cloudtrail-*`, `aws-controltower-logs-*`, with a **`NotAction`** list and
    `ArnNotLike aws:PrincipalARN = arn:*:iam::*:role/AWSControlTowerExecution`.
  - **`CTS3PV7`** — the same shape over `aws-controltower-config-*`, which is the Audit account's bucket.
  - The `NotAction` list, identical in both: `s3:DeleteObject`, `s3:DeleteObjectTagging`,
    `s3:DeleteObjectVersion`, `s3:DeleteObjectVersionTagging`, `s3:Get*`, `s3:List*`, `s3:PutBucketTagging`,
    `s3:PutObject`, `s3:PutObjectAcl`, `s3:PutObjectLegalHold`, `s3:PutObjectRetention`,
    `s3:PutObjectTagging`, `s3:PutObjectVersionAcl`, `s3:PutObjectVersionTagging`, `s3:RestoreObject`.

  **`s3:PutBucketObjectLockConfiguration` and `s3:PutBucketVersioning` are not in that list**, so
  `AWS Control Tower Admin` — administrator of the Log Archive account — cannot enable Object Lock on the
  trail's bucket. The **one** exempt principal is `AWSControlTowerExecution`. Two consequences, and the
  second is why the step survives the first: this cannot be fixed by widening a permission, because the
  identity that would grant it is the identity the deny is written against; and **the same `NotAction`
  permits `s3:DeleteObject` and `s3:DeleteObjectVersion` to everyone**, so AWS protects the bucket's
  *configuration* and deliberately leaves its *contents* deletable — which is exactly the exposure step 9
  exists to close. Recorded as **decision 9**, to be taken while executing.

- **Step 11.2 has nothing to set.** `lakeformation get-data-lake-settings` in Data Governance
  (`awsds-infra-data`, `us-west-2`), an account with no lake, no registered location and no administrator:

```
Parameters:      { "CROSS_ACCOUNT_VERSION": "4", "SET_CONTEXT": "TRUE" }
DataLakeAdmins:  []      ReadOnlyAdmins: []      TrustedResourceOwners: []
CreateDatabaseDefaultPermissions / CreateTableDefaultPermissions: IAM_ALLOWED_PRINCIPALS = ALL
```

  **Verification (v) is answered without acting**: the cross-account version is above 3 in an account with
  no lake, because that is the account default. So no `put-data-lake-settings` is made — the
  replaces-the-whole-structure hazard is avoided by not making the call — and what the step owes Stage 5
  grew instead: its `aws_lakeformation_data_lake_settings` must carry
  `parameters = { CROSS_ACCOUNT_VERSION = "4", SET_CONTEXT = "TRUE" }` alongside its `admins`, **both keys**,
  re-read immediately before writing. A value nobody set is a value nobody defends, and INT-11 fails
  silently on both sides.

- **Step 11.1 has real work.** `organizations list-aws-service-access-for-organization`, from *Identity*:
  the seven principals of `INV-09` — `access-analyzer`, `cloudtrail`, `config`, `controltower`, `iam`,
  `member.org.stacksets.cloudformation`, `sso` — and **`ram.amazonaws.com` is absent**. The after-reading is
  therefore one name appearing in a list that goes from seven to eight.

- **The exemption reading step 12 asks for, taken early and from the document.** `describe-policy` on
  `p-fw2pctqw` (the `CT.MULTISERVICE.PV.1` document as Control Tower packed it on `Identity` — it also
  carries `GRRESTRICTROOTUSER` and `GRRESTRICTROOTUSERACCESSKEYS`, which is Lesson 23 in one line). The
  `CTMULTISERVICEPV1` statement: **86 `NotAction` entries across 68 service prefixes**, condition
  `StringNotEquals aws:RequestedRegion = us-west-2` **AND** `ArnNotLike aws:PrincipalARN` over **four**
  Control Tower roles — `AWSControlTowerExecution`, `aws-controltower-ConfigRecorderRole`,
  `aws-controltower-ForwardSnsNotificationRole`, `AWSControlTower_VPCFlowLogsRole`.

  Read against what actually runs in Log Archive and Audit, which is what open question 16 asked for:
  **`config:*`, `access-analyzer:*`, `iam:*`, `kms:*` and `organizations:*` are exempt entirely**, so the
  Config aggregator and `awsds-org-external-access` are untouched in any region; of `cloudtrail:` only
  `LookupEvents` is exempt, so creating a second trail elsewhere would be denied — which is the intent; and
  of `s3:` only the account-level and multi-region-access-point actions are exempt, so a bucket created in
  another region would be denied — also the intent. **`guardduty`, `securityhub` and `macie2` are not
  exempt**, so enabling the control is a commitment that Stages 4, 5 and 11 stay in `us-west-2` — which they
  are in this design. The two Control Tower roles that matter in these two accounts,
  `ConfigRecorderRole` and `ForwardSnsNotificationRole`, are both exempt.

- **Operational, and it shapes the whole stage:** there is **no CLI profile for Log Archive, Audit or
  Management** on this laptop, and there is not meant to be — the infrastructure user has no assignment in
  any of them. Every remaining reading of this stage is taken in **CloudShell as `AWS Control Tower Admin`**
  through `AWSAdministratorAccess`, and `./aws/probes/scp-battery.sh` can never reach those accounts.
