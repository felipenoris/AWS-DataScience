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
Bucket:     aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx
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

- Login as CT Admin -> Log Archive Account -> AWSAdministratorAccess.

- Inspecting CT CloudTrail S3 logs bucket. No lock configuration, versioning is enabled, lifecycle with 365 days of expiration. Log commands executed on CloudShell:

```
~ $ aws s3api get-object-lock-configuration --bucket "$BUCKET"; aws s3api get-bucket-versioning --bucket "$BUCKET"; aws s3api get-bucket-lifecycle-configuration --bucket "$BUCKET"

aws: [ERROR]: An error occurred (ObjectLockConfigurationNotFoundError) when calling the GetObjectLockConfiguration operation: Object Lock configuration does not exist for this bucket
{
    "Status": "Enabled"
}
{
    "TransitionDefaultMinimumObjectSize": "all_storage_classes_128K",
    "Rules": [
        {
            "Expiration": {
                "Days": 365
            },
            "ID": "RetentionRule",
            "Filter": {
                "Prefix": ""
            },
            "Status": "Enabled",
            "NoncurrentVersionExpiration": {
                "NoncurrentDays": 365
            }
        }
    ]
}
```

- **Before-state only; nothing on the bucket was changed.** Object Lock absent, versioning already
  `Enabled` — which is a precondition rather than a step, since `CTS3PV8` denies `s3:PutBucketVersioning`
  too — and one lifecycle rule, `RetentionRule`, expiring current versions at **365 days** and noncurrent
  versions at **365 days**. **That is the ceiling for decision 3**, and it is the noncurrent half that
  binds: Object Lock protects object *versions*, so a compliance-mode retention at or above 365 days makes
  the landing zone's own expirations start failing. Decision 9 is still open, so nothing was attempted.

- Login as CT Admin -> Management Account -> AWSAdministratorAccess. Management is not recorded. Log of commands executed on CloudShell:

```
~ $ aws configservice describe-configuration-recorders --region us-west-2
{
    "ConfigurationRecorders": []
}
~ $ aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'
0
```

- **Verification (xiii) is answered: the landing zone does not record the management account.**
  `ConfigurationRecorders: []` in `us-west-2`. So `plan/cost-model.md`'s assumption holds and its Config
  row's account count is right as written. `describe-delivery-channels` was not run and does not need to
  be: an empty recorder list already answers the question, and a delivery channel with no recorder records
  nothing. **What this does to decision 8 is make it a real choice rather than a formality** — there is no
  recorder in Management to attach a rule to, so 10.4's "yes" means creating the whole Config plane there
  by hand, in the one account this project keeps out of Terraform.

- `SummaryMap.AccountAccessKeysPresent` reads **`0`** — D16's invariant holds **today**. Recorded as a
  measurement, not as a control: this is the free instrument 10.4 itself calls an intention (Lesson 5),
  and it answers the state question only at the moment somebody runs it.

- Login as CT Admin -> Audit Account -> AWSAdministratorAccess. Log of commands executed on CloudShell:

```
~ $ aws configservice describe-configuration-aggregators --region us-west-2
{
    "ConfigurationAggregators": [
        {
            "ConfigurationAggregatorName": "aws-controltower-ConfigAggregatorForOrganization",
            "ConfigurationAggregatorArn": "arn:aws:config:us-west-2:<Audit Account>:config-aggregator/aws-service-config-aggregator/controltower.amazonaws.com/config-aggregator-bmopj7ig",
            "OrganizationAggregationSource": {
                "RoleArn": "arn:aws:iam::<Audit Account>:role/aws-service-role/config.amazonaws.com/AWSServiceRoleForConfig",
                "AllAwsRegions": true
            },
            "CreationTime": "2026-08-09T01:54:42.782000+00:00",
            "LastUpdatedTime": "2026-08-09T01:54:42.793000+00:00",
            "CreatedBy": "controltower.amazonaws.com"
        }
    ]
}
```

- **10.3's volume half has its instrument, and only that.** The aggregator is Control Tower's own,
  `AllAwsRegions: true`, created with the landing zone on 2026-08-09 — so the per-account item counts are
  readable in one place, from Audit. **The counts themselves are not measured yet**, and neither is the
  spend half from Cost Explorer in Management. Step 10.3 stays open.

- This enables organization-wide resource sharing (Allows sharing resources by specifying an Organization ID or OU ID, instead of listing individual account IDs). Login as CT Admin -> Management Account -> AWSAdministratorAccess. Log of commands executed on CloudShell:

```
~ $ aws ram enable-sharing-with-aws-organization --region us-west-2
{
    "returnValue": true
}

~ $ aws organizations list-aws-service-access-for-organization
{
    "EnabledServicePrincipals": [
        {
            "ServicePrincipal": "access-analyzer.amazonaws.com",
            "DateEnabled": "2026-08-12T03:14:08.900000+00:00"
        },
        {
            "ServicePrincipal": "cloudtrail.amazonaws.com",
            "DateEnabled": "2026-08-09T01:46:52.709000+00:00"
        },
        {
            "ServicePrincipal": "config.amazonaws.com",
            "DateEnabled": "2026-08-09T01:46:53.911000+00:00"
        },
        {
            "ServicePrincipal": "controltower.amazonaws.com",
            "DateEnabled": "2026-08-09T01:46:50.307000+00:00"
        },
        {
            "ServicePrincipal": "iam.amazonaws.com",
            "DateEnabled": "2026-08-09T18:02:35.162000+00:00"
        },
        {
            "ServicePrincipal": "member.org.stacksets.cloudformation.amazonaws.com",
            "DateEnabled": "2026-08-09T01:46:51.502000+00:00"
        },
        {
            "ServicePrincipal": "ram.amazonaws.com",
            "DateEnabled": "2026-08-14T18:47:22.759000+00:00"
        },
        {
            "ServicePrincipal": "sso.amazonaws.com",
            "DateEnabled": "2026-08-01T21:30:39.047000+00:00"
        }
    ]
}

~ $ aws iam get-role --role-name AWSServiceRoleForResourceAccessManager --query 'Role.[RoleName,CreateDate]' --output text
AWSServiceRoleForResourceAccessManager  2026-08-14T18:47:23+00:00
```

- **Step 11 is done.** `enable-sharing-with-aws-organization` returned `true`; the trusted-access list
  went from the **seven** principals of the before-reading to **eight**, with `ram.amazonaws.com` at
  18:47:22Z, and `AWSServiceRoleForResourceAccessManager` was created at 18:47:23Z. **The one-second gap
  is the result worth keeping**: the RAM call made both halves. Enabling trusted access from the
  Organizations side instead would have produced an identical list and no role — the list would read
  correct and organization-wide sharing would still not work, which is INT-11's silent-failure shape
  arriving one stage early.

- **Re-read independently from the laptop** as the infrastructure user (`awsds-infra-identity`): eight
  principals, `ram.amazonaws.com` among them. The after-reading answers from a member account, as the
  before-reading did.

- With 11.1 landed, **step 11 closes whole**: 11.2 stays a reading with its instruction to Stage 5 written
  above, 11.3's two checks are both answered, 11.6 was answered before execution, and 11.4 is Stage 5
  step 7 by construction. INT-11's two organization-level halves are settled; `INV-09` restated to eight.

- **Where 1d stands after this sitting:** step 11 done; steps 9, 10 and 12 open. Decisions 3, 8, 9 and 10 are all still to be taken. Verifications (v) and (xiii) are answered; (iv) and (xiv) are open.

- Login as CT Admin SSO on Management Account, AWSAdministratorAccess. Control Tower -> Control Catalog. Enabled on Security OU:
  - CT.MULTISERVICE.PV.1 on us-west-2 region
  - AWS-GR_RESTRICT_ROOT_USER with Exempt AssumeRoot sessions enabled
  - AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS

- Login as CT Admin SSO on Log Archive Account, AWSAdministratorAccess. Probed `create-key-pair`, denied by SCP on us-east-1, allowed on `us-west-2`. Log of commands executed on CloudShell:

```
~ $ aws ec2 create-key-pair --key-name probe-region --dry-run --region us-east-1

aws: [ERROR]: An error occurred (UnauthorizedOperation) when calling the CreateKeyPair operation: You are not authorized to perform this operation. User: arn:aws:sts::<Log Archive Account>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_b65279a07fc16dfa/felipenoris@gmail.com is not authorized to perform: ec2:CreateKeyPair on resource: arn:aws:ec2:us-east-1:<Log Archive Account>:key-pair/probe-region with an explicit deny in a service control policy: arn:aws:organizations::<MANAGEMENT ACCOUNT>:policy/o-4z1leiit0c/service_control_policy/p-idgyiios. Encoded authorization failure message: OIau77IwNA-RjpafXihrUW41WAUxaBKeALVOZxxGdy7u-JcfuZW95DlcUImc3Szcfs9IIqFOYM2Z0v7obHBXpzuilc2XBGMKH9lT0YXWsxwKU1BEnTXoYeUm2ETiSsvvNDRPi5HO5QWipU9S8biTwVu97C4iZdiUjoscgwFFWZC2X4F68zYENY3NPZ0MgtC_fQiLquKBKm6Hav--_nupIRF-ikk7Zu3DJI9ZmCwmEu-zClu9Xfs3x5iriekEfwh4kSaOpI2c-0LU0KItVhQb6QWZWDI5fEmE9UP4D-lvUckYp5L1yWGhR7IooYGT_IiQo5XbcGyaGzwOLwZYeG4y6wffkqNx2sDlWWoLVi6xkSehdxr-b8WURyY9Qi8l6064yCtISKLPq3Vtz3uOAYvwetmAZ-W3l6KZlUiTV6tp2-CX_hslr_XypZcFlOVvasEEVznCsYAh56UxhYURyVxHmA5AIvuqSY7rwwsBc_uu61XCKwRvIwVQGNdeP_WexnEFyfJ2eddvqeqsSWN778FzMQq5WcYOVQLYsoIgoVanOhwNOvYbLzwjKE_VsaOJyxVoMLmPfCLS7G0qx6JxN735_0pEr0ZRJMqfWeamg3U7jspS7w3OD0jAeP94QW5jRE0bIIHRVYzfxvm3mHAKhVI2Rf8T3mAa_6PhvP3vR07tRZzY9_emmmIS-riGp9sDQfgyuGwd1y2j89NtiWOM1tqx0E8ziO5UpOk47ugvAUWeWTwwOBPSIGlrtr0Bbsmu7CJaNH-SM4nK20fmS9IzUlFbjgCpoPjRNtDAGSc_TPK2k1jjYVXigus4loakCTAELNKKwkuQEDh1h7jRz_ZsGlZaxkVZa4uaXq3nNM9ya60FJ4moQRRtzzV5KXD9c1AiSIKtj3GWChLostz-U53GiINh63c19pZMTjK_6NV_Kj77ymsukbVCb3kpmELSiHgv-OREj8BmEYmiLZZxPJouWJzaGvFUzKZMYQd-LGKoCyxQ0Hm3cGnRcmqB27549P1BLJpu5uRZG3ARrrnBaDihaXOgXcBMBF_RWIx5VfkxQM0crgAoNLSDmdScEVZggFilZgTZKXaON3gZ2B8iXWIMRYb3PBJ0cwVZh9ISr45CgqnRnonOs059OxNGv5lZluPMyA0IMxj5edr7dyiIPcrQOq3zBA9iuaOfMrh-UheZou0rlqvdhEdQ5AQQYLZ-nU1a847_Z518V7NIbBRPjnvIIlw9MsdA3dDDro_9i0qDEM-aNBxxQkQn4UBpqXFxx5_KadskONbspeBL4CXKIVZUBlYJSDR5UYsWePd8tN6YpL44cE24zgxPG-HgIcESrBIGdnY1oxdldWoIjjvYAstKRFLf0NOb8_w02mvfhuBn8GIP39yVBaBFJIL_atCJUYDx9MfNBfG_3IHY5cNQ6-vZvUY_WYAPyamsXbmbiRdZLzKkag6wxbVK1VaSol3tIcFapEGTQE6skdPJCSiEDnMTf2eJmfXMgG7yASyfpx7Gsgxgv8IEBycLKayCT_Db32yizxUBjQoK5zZZizU63C0WlD4gH2nsai6hahzHNMtROjFgXxqMlSIQVy58Rg5VcDoAFjlFTZ4FcoMJoBOE75WiIly1Kh5g8lTeEg7YkqFpRtTJPqMBUsQvFUQd_PniBh0lyvAyf0GRvgcUDlq_J_tXKrpLPxbVdmykd2cqiZ8J4xN0FgCbp7-u-Vp5JG4FdUzorohuznWFk-0R1QlNIDcJ7slGv2sLSKa1ar7CRw
~ $ aws ec2 create-key-pair --key-name probe-region --dry-run --region us-west-2

aws: [ERROR]: An error occurred (DryRunOperation) when calling the CreateKeyPair operation: Request would have succeeded, but DryRun flag is set.
```

- Login as CT Admin SSO on Audit Account, AWSAdministratorAccess. Probed `create-key-pair`, denied by SCP on us-east-1, allowed on `us-west-2`. Log of commands executed on CloudShell:

```
~ $ aws ec2 create-key-pair --key-name probe-region --dry-run --region us-east-1

aws: [ERROR]: An error occurred (UnauthorizedOperation) when calling the CreateKeyPair operation: You are not authorized to perform this operation. User: arn:aws:sts::660820513855:assumed-role/AWSReservedSSO_AWSAdministratorAccess_b987a8e362f41c3e/felipenoris@gmail.com is not authorized to perform: ec2:CreateKeyPair on resource: arn:aws:ec2:us-east-1:660820513855:key-pair/probe-region with an explicit deny in a service control policy: arn:aws:organizations::885931358757:policy/o-4z1leiit0c/service_control_policy/p-idgyiios. Encoded authorization failure message: toYXZzhniD2dKL4eg4qM-o_t_hzQkRg_fl4VPHC3HAEca0fK1RAQWk98dgDDb3IgA0eMY7bE_RUdQqa_4TYLzoDU__aomNIdtaHasobTTstDSYkTMU6LC-__3CSTieufv5WqXJQdZqACT46KWmkd7-Vi2LR3loULcahDTmDqkmIHdhgLHmXhahWzRbJhX4Qsd1yHSb0a9HppsTOlxo3Jp-9CspU-eImxDxRprm1CphCiNanW-7TN-P7rGYAn_D6h-F_cEKZqqK0FsXAEk_jXNrZU5UueVn6rLrnWMmLxuIQGTJrVtk4hp4aQy7aiTSJg8Ohf2qq__Rmy7aMR9L4_06yKGc_eadKofj4C1JtzELysRsQgzjJsfPVvsdPYsFv2hj4YeJkIejml0N_RADpdjBz4sfeSNMxboY3vkwdnGBid5uOe4rL5x-P02Ehe6qKolItfvJuovgW3dIq9epCyK2mjqSX8wwiB_dCD24O5AGU48bP5Yur_jbKbc97H7B1WHoS-gTgXDtGF-fX83QQ3J6ANOpSzouE0WjX9iGG6JCeVU0CNOM-7sAcS4Hf6KKMsPln8l-hLmmRLxqiTpVhVOe1ngixCCKPl7Ar7a2TNYfC6feKnTCVebxNSxnrwWXSkmIHVnBouo3zDu0-TZ-Cdy9bWzY3DxyUx-j9HYKCqjgojgohUKYGoouRRdSHscx8NWuApWdGXoaiNrmdNwvEbYGtJsrfH7BzpK5Wcryeo9w_xxhLLbi3wBoKyRP3-ZquHFZfFxCvTvRuM8MzC_WixOhutVJzZiUQ1KLssNZw_imMpVNreOHZywMnUu-GtnM0WI5eJH-JV989C17PNT_sV_4i5wUNAalT-vvryxXkusvJwc9WOQByq9tNZs2xkkGHMbWCvXD-eC60WrJWewvn-USiI4uhzlIjc3-hj30tqyPS5Ecf5JTTVPW5m57mMMUqsP1wFOoS0YSWkKYu6hqA8pNfdr7ua-iQud7NtzRhXNYPnVwXsJwHTLJxyP9vtU_wWlg_cRllI4X8zK3qnx2pMI8YZm2oPvdQb4oAEQ5reTsYRmaFKoIuhn2zGQZKFD-3_bOVrav62sCZpel9aOtXihsg1C_mOHhJHMUR6crmd9ad7uBDlQwqTGxdYXRUvosuAEDQGizXbNXpf5GSJj9OXFrQ8OQewZYAZOYX__swySq0T7snRklZFbatJ6-QrsY6DmQ9QTxE8SjS-9WShSRg-ru6Ky0WRNrKwNwR3OU7G-DwjQUEdrPvVRo6m4e5dqAkdWm8Fa_iLLsmIfshHMO7eEhlLuNypBnjp8J11OvP2aMqOZ5Xh7gzcrnRvhZeierMaxAL2DQYtyFCEdw2Qs1MgFL4hh8DptsJdFhaoNoKI4waKAQSZ82Rgbtq8ldr4ldmWmbx7ZiflUFceZOfZmKWHy5J6t4ZFkKJf8ybQHeCkfD2kSAtG0hZEb8xLQGckWe-3gVxFK5soggAv4R9wgJZHkOWWG3G4PRsbdL7AEyh-IE0elXeqwWOWHFYoMjbzkUSAKOieuCpgRWh6sIih7rQiiooL0kC3af1ZPiJ19Z9MaTzKEffLScIMLKZzCOpIewVeqWniBtNNibs-zoGYxQLc5S0Hgqk1HtqMAeECBehSPZc_fiwI98Ux4hbGg1kqd2sTlIxizjsGmrh6v6aI7nKbUgwxf_fdd1Y67yukbePlqONx8h_w_GJl5Fu-19dlinlE-k3J7HVeYgRJbBgtH-KcYcRF0r0O9O1Y-g
~ $ aws ec2 create-key-pair --key-name probe-region --dry-run --region us-west-2

aws: [ERROR]: An error occurred (DryRunOperation) when calling the CreateKeyPair operation: Request would have succeeded, but DryRun flag is set.
```

- Login with CT Admin SSO on management. Noticed it doesn't have access to budget features (`You don’t have permission to perform the following operation on the AWS Cost Management console: ce:DescribeReport. `), showing `access denied` on the page. So, I loged in with root account. Billing and Cost Management -> Cost Explorer. I noticed it was already enabled, maybe because my root account is old.

- Login with root account at AWS Console. On Account Name -> Account -> IAM user and role access to Billing -> Edit. Market `Activate IAM Access` -> Update.

- Login with CT Admin SSO on management account, AWSAdminstratorAccess. Billing and Cost Management. I can now see it has access to this page. The Cost Explorer is enabled. As I said before, this account is old, so the Cost Explorer has metrics for many months already.

- Filtering all dates from the current month. Granularity Daily. Filtering Service = Config. Usage Type shows only `USW2-ConfigurationItemRecorded`. Last usage for Config service was yesterday, on Canary Account. It shows a spike in the first day of the series, distributed equally accross all accounts, summing $2.2. Total usage is $2.28. All usage on Audit account is for `USW2-ConfigurationItemRecorded`, summing $0.28.

- Step 12 is done, and decision 10 was yes. All three controls on Security: CT.MULTISERVICE.PV.1
allowing us-west-2, AWS-GR_RESTRICT_ROOT_USER with ExemptAssumeRoot, and
AWS-GR_RESTRICT_ROOT_USER_ACCESS_KEYS without one (D16). The reasoning, so a later reader can tell
a decision from an omission: the ceiling is free today — everything in Log Archive and Audit is already
us-west-2 — and the alternative was leaving the two accounts holding the immutable trail and the
organization's findings as the only governed accounts where a resource may be created in any Region.
The exemption reading taken earlier this day is what made it safe: the four Control Tower roles are
exempt and config:* is exempt entirely, so nothing Control Tower itself runs there is constrained.
What it commits: guardduty, securityhub and macie2 are not in the NotAction list, so
Stages 4, 5 and 11 are us-west-2 or they are denied — which is this design, stated now rather than
discovered then.

- The step's one real unknown is answered: Security accepts enable-control. Being Control Tower's
own foundational OU did not make it a non-target, and a refusal would have turned decision 10 from
"declined" into "impossible" — which is a different sentence in the log.

- Control Tower packed the three enablements in a third shape. CT.MULTISERVICE.PV.1 went into a
new document, aws-guardrails-KAmzSQ (p-idgyiios, one statement, CTMULTISERVICEPV1), while the
two root-user controls went into the pre-existing AWS guardrail aws-guardrails-rFWRFL
(p-2xyaqn66), taking it from 11 statements to 13. So the three measured layouts are now: original
guardrail (Policy Test, Workloads, Interactive), Region document (Identity, Data), and both
at once (Security). Lesson 23 is therefore not "one of two layouts" — it is that the layout cannot be
inferred at all, only read. Log Archive and Audit resolve to 26 statements each, up from 23.

- The half no probe can reach was verified by reading, and it passes. ./aws/org-policies.sh from the
laptop as awsds-infra-identity: CHK-1 — ExemptAssumeRoot present on Security, so
GRRESTRICTROOTUSER ANDs Null: aws:AssumedRoot = true with the root-ARN test; CHK-2 — the access-key
control correctly carries no exemption. Every principal available here is an Identity Center role and
ArnLike …:root never matches one, so the document read is the only instrument (Lesson 22). Section 4's
table now reads yes/yes/yes for Security, and Sandboxes is the only blank row left.

- Verification (xiv), first half: answered in both accounts by the two CloudShell probes above —
us-east-1 denied with "explicit deny in a service control policy" naming p-idgyiios, us-west-2
returning DryRunOperation. Second half provisional: that Control Tower's own operations in those two
accounts are unaffected is answered by the exemption reading, not by a probe, and is re-checked at the
next landing-zone update, account update or re-enrollment — the same shape as (iv) and 1b's (vi).

- And this is now permanently untestable by the battery. ./aws/probes/scp-battery.sh maps probes to
CLI profiles and neither account has one, by design. The probes above were run by hand, once. What stands
behind them is CHK-1/CHK-2 and section 4 of ./aws/org-policies.sh — a regression on the Security
row surfaces there or nowhere. Open question 16 is closed (AWS_STATE.md INV-11 and INV-12 restated).

- Root was used twice, and the reason is a finding rather than a convenience. AWS Control Tower Admin
holds AdministratorAccess, which includes ce:, and Management is exempt from SCPs — yet the Cost
Management console refused it. The cause was IAM user and role access to Billing never having been
activated, which only the root user can change. So the permission model was never the obstacle and no
policy edit would have fixed it. Now that it is activated, every future billing and Cost Explorer
reading is taken as CT Admin, and needing root for one is a signal that this toggle was reverted.

- The break-glass alarm, which those two sign-ins tested for free. awsds-org-root-activity (1a step 5)
fires on any root activity that is not an AWS service event, so both sign-ins should have notified.
All break-glass notifications arrived on both channels.
Recorded because this is an unplanned live test of the whole chain (trail → S3 → Logs → filter → alarm),
distinct from the deliberate test of 2026-08-09, and because a silent alarm here would undermine the
fallback that decision 8 is about to lean on.

- Step 10's spend half is measured, and the shape matters more than the total. Cost Explorer from
Management as CT Admin, current month, daily, Service = Config:

  - One usage type only, USW2-ConfigurationItemRecorded. No rule-evaluation line at all — so 100% of
the Config spend is configuration items, which is exactly what step 10 is about, and the usage-type
split 10.3 asked for has a trivial answer.

  - USD 2.28 month-to-date, of which USD 2.20 is a single-day spike on Aug 09, spread evenly across
the accounts, with Audit's entire share at USD 0.28 and the most recent activity the previous day, in
Policy Canary — which is the SCP battery.

  - Derived, and worth checking against the per-account bars rather than trusting the arithmetic: the
spike divided by the eight recorded accounts (Management is not recorded, (xiii)) is ≈ USD 0.275,
and Audit's total is USD 0.28 — so Audit recorded essentially nothing after the spike day. At
USD 0.003 per item the spike is ≈ 730 items, ≈ 90 per account for an account that was empty.
What that says: Config cost here is event-driven, not time-driven. An idle account bills almost
nothing; the recurring rate at this account count is on the order of USD 0.5/month, well under
PRICING.md's USD 2.50-5.00 band. The spike is the number that generalises to Stages 2-3: an enrollment
or an apply storm is what the recorder charges for, and ~90 items for an empty account is the ratio to
carry into that estimate.

  - Cost Explorer data lags ~24 h, so the last populated day being yesterday is expected and not a signal.

- Where 1d stands after this sitting: steps 11 and 12 done; step 10 half done — the volume half from the
Audit aggregator and decisions 4 and 8 remain; step 9 untouched, with decisions 9 and 3 still to be
taken. Verifications (v), (xiii) and (xiv)'s first half are answered; (iv) is open and (xiv)'s second half
is provisional.

- updated `aws/output/org-policies.txt` using `aws/org-policies.sh`.

- Step 10's volume half, measured from the laptop instead of from the Audit aggregator. 10.3 said to
read the item counts from the aggregator in Audit, on the grounds that going account by account "gives
the same answer for more work, and misses Log Archive and Audit". Half of that is wrong and the other
half is the reason the aggregator is still needed. One loop over the six awsds-infra-* profiles with
aws configservice select-resource-config --expression `"SELECT COUNT(*)"` is a single command, no
sign-in, and it returns more than the aggregator's summary — it groups by resource type per account.
What it cannot reach is Log Archive and Audit, which hold no profile, so the aggregator run keeps
exactly that job and no other.

- Recorded resources, us-west-2, 2026-08-14: Development 82, Sandbox Account 1 80, Production 81,
Data Governance 80, Identity 82, Policy Canary 82.

- This confirms the spend derivation independently. The USD 2.20 spike divided by USD 0.003 gave
≈730 items, ≈90 per account, derived and flagged as such the same day. The inventory says 80-82. Six
accounts at ~81, plus Log Archive and Audit (which hold more — buckets, topics, keys), lands close to
730; the gap is precisely what an inventory cannot show, being resources created and then deleted, which
bill an item each and leave nothing behind.

- The composition is what decides the step, and it is identical type-for-type in Development and Policy
Canary. 18 AWS::IAM::Role, 17 AWS::CodeDeploy::DeploymentConfig, 6 AWS::CloudFormation::Stack,
4 AWS::AppConfig::DeploymentStrategy, 4 AWS::Cassandra::Keyspace, 4 AWS::EC2::RouteTable,
3 AWS::EC2::Subnet, 2 AWS::ECS::CapacityProvider, 1 AWS::Athena::WorkGroup, and ~20 types at one
each. ≈28 of the 82 — a third — are defaults AWS creates by itself and that nobody will ever change:
the CodeDeploy deployment configurations, the AppConfig strategies, the Keyspaces system keyspaces, the
two Fargate capacity providers, the primary Athena workgroup. That is the obvious exclusion list, and
measuring it is what kills it: they are recorded once and never change, so they cost USD 0.08 per
account in total, not per month. Excluding them saves under a dollar across the organization, forever.

- The battery creates nothing, now proven from the other side. Policy Canary's inventory is identical
to Development's, type for type, after 93 probes including three creates. The residual USD 0.08
attributed to it in Cost Explorer did not come from resources that survived.

- The recorder's actual shape, read from Development — allSupported: true,
includeGlobalResourceTypes: true, recordingFrequency: CONTINUOUS, recordingScope: PAID, delivered
through AWSServiceRoleForConfig. 10.3 names only one lever and there are two: besides the
resource-type list there is recordingFrequency: DAILY bills USD 0.012 per item-day against USD 0.003 per change, so the break-even is four changes per resource per day and it would multiply this line rather than divide it.

- Decision 4 is taken: leave the recorder alone, revisit at Stage 12 step 5. The measured recurring
rate is ~USD 0.5/month, below PRICING.md's USD 2.50-5.00 band, and the two sides of the trade are not
comparable: the alternative is a Lambda driven by Control Tower lifecycle events, with a StackSet, a role
per account and re-application on every re-enrollment, to save less than a dollar — and an exclusion list
that is wrong breaks a detective control silently, since both Control Tower's controls and Stage 5's
Security Hub consume Config. The honest limit of the measurement, and its answer: these are empty
accounts, but the shape covers that — the cost is event-driven, not time-driven, and an idle account
bills almost nothing. What will move it is churn, not inventory: AWS::IAM::Role is already the
largest real type at 18 and Stage 2 writes dozens more, and Stage 6's Spark clusters churn EC2 and ENIs.
The revision signal at Stage 12 step 5 is EC2/ENI churn, not the resource count.

- What is left in step 10: the aggregator run in Audit for the two profile-less accounts, and 10.4 —
verification (xiii) and decision 8.

- Login as AWS Control Tower Admin, Audit Account, AWSAdministratorAccess. Executed on CloudShell (replaced account IDs with account name to mark the identitiers on this log):

```
~ $ aws configservice describe-configuration-aggregators --region us-west-2 --query 'ConfigurationAggregators[].ConfigurationAggregatorName' --output text
aws-controltower-ConfigAggregatorForOrganization

~ $ aws configservice select-aggregate-resource-config --region us-west-2 --configuration-aggregator-name aws-controltower-ConfigAggregatorForOrganization --expression "SELECT accountId, COUNT(*) GROUP BY accountId ORDER BY COUNT(*) DESC" --output text
SELECTFIELDS    accountId
SELECTFIELDS    COUNT(*)
RESULTS {"COUNT(*)":86,"accountId":"<Audit Account>"}
RESULTS {"COUNT(*)":82,"accountId":"<Development Account>"}
RESULTS {"COUNT(*)":82,"accountId":"<Policy Canary Account>"}
RESULTS {"COUNT(*)":82,"accountId":"<Identity Account>"}
RESULTS {"COUNT(*)":81,"accountId":"<Production Account>"}
RESULTS {"COUNT(*)":80,"accountId":"<Data Governance Account>"}
RESULTS {"COUNT(*)":80,"accountId":"<Sandbox Account 1>"}
RESULTS {"COUNT(*)":79,"accountId":"<Log Archive Account>"}
```

- Login as AWS Control Tower Admin, Management Account, AWSAdministratorAccess. Executed on CloudShell:

```
~ $ aws configservice describe-configuration-recorders --region us-west-2 && aws configservice describe-delivery-channels --region us-west-2 && aws iam get-account-summary --query 'SummaryMap.AccountAccessKeysPresent'
{
    "ConfigurationRecorders": []
}
{
    "DeliveryChannels": []
}
0
```

- **Decision 8 is taken: no.** `describe-delivery-channels` returning `[]` alongside the recorder is what
  decided it — this was never one resource. A delivery channel needs an S3 bucket, and Control Tower's
  `aws-controltower-config-*` bucket lives in Audit with a policy written for enrolled accounts, which
  Management is not; so D16's `iam-root-access-key-check` meant **a bucket, a bucket policy, a delivery
  channel, a recorder and the rule** — five hand-made resources in the one account kept out of Terraform,
  to answer one boolean. **`AccountAccessKeysPresent` reading `0` is what made declining safe rather than
  merely cheap**: the rule's value over 1a's alarm was state versus event, and the only window the alarm
  cannot see — a key created before it existed — is now permanently excluded, while the alarm itself was
  measured live on both channels earlier the same day.

- **The instrument changed; the invariant did not.** The state read is now **step 4 of `break-glass.md`
  §6**, performed by the tester who is already signed in as Management root. Hanging it on an existing
  procedure is not a control, but it is not an intention either (Lesson 5). **The residual, accepted and
  written rather than argued away:** if the alarm chain breaks silently and a root access key is created
  in that window, nothing reports it until a human looks. **Revision trigger:** Management becoming
  recorded for any other reason — Stage 5's Security Hub central configuration — makes the rule nearly
  free, and it should go on then.

- **The wider gap this decision accepts is not the missing rule, it is the missing history.** Management
  has no configuration record at all, so "what changed here, and what does it look like now" is answerable
  only from CloudTrail, which records calls and not state. Written as a row in
  `plan/institutional-delta.md` rather than left as a consequence nobody named.

- **Step 10 is closed. Stage 1d is down to step 9**, whose before-state was already read: no Object Lock,
  versioning `Enabled`, lifecycle expiring current and noncurrent versions at 365 days.

### Step 9 — S3 Object Lock on the CloudTrail log bucket

- **Preflight.** Login as CT Admin -> Log Archive Account -> AWSAdministratorAccess. The bucket name is
  resolved from the trail rather than pasted from a document, since the trail is the only source that
  cannot be stale. Log of commands executed on CloudShell:

```
~ $ BUCKET=$(aws cloudtrail describe-trails --region us-west-2 --query "trailList[?Name=='aws-controltower-BaselineCloudTrail'].S3BucketName | [0]" --output text) && echo "$BUCKET"
aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx

~ $ aws s3api list-buckets --query "Buckets[?starts_with(Name,'aws-controltower-')].Name" --output text | tr '\t' '\n' | while read -r b; do echo "$b => $(aws s3api get-bucket-logging --bucket "$b" --query 'LoggingEnabled.TargetBucket' --output text)"; done
aws-controltower-cloudtrail-access-logs-<Log Archive Account>-gcs-gsx => None
aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx => aws-controltower-cloudtrail-access-logs-<Log Archive Account>-gcs-gsx
```

- **The check that mattered: the target bucket appears only on the left of the arrow.** Nothing writes S3
  server access logs into it, so enabling Object Lock does not silently stop access logging for a bucket
  beside it. The CloudTrail bucket is a *source* of access logs, and its destination is the access-log
  bucket, which is correctly left untouched.

- **Two corrections to 9.1's names, both found here.** The access-log bucket is
  **`aws-controltower-cloudtrail-access-logs-*`**, not `aws-controltower-access-logs-*`. And **there is no
  `aws-controltower-config-*` bucket in this account** — only two `aws-controltower-*` buckets exist — which
  confirms by inventory what 9.1 argued from policy: the Config bucket is in Audit.

- **A first borrow succeeded before the preflight was finished, and that is what broke the next attempt.**
  Login as CT Admin -> Management Account -> AWSAdministratorAccess. Log of commands executed on CloudShell:

```
$ eval $(aws sts assume-role --role-arn arn:aws:iam::<Log Archive Account>:role/AWSControlTowerExecution --role-session-name stage1d-objectlock --query 'Credentials.[`export AWS_ACCESS_KEY_ID=`,AccessKeyId,`export AWS_SECRET_ACCESS_KEY=`,SecretAccessKey,`export AWS_SESSION_TOKEN=`,SessionToken]' --output text | tr '\t' ' ' | sed 's/= /=/g')

~ $ aws sts get-caller-identity --region us-west-2
{
    "UserId": "AROA4QN6B537DE4I3UXJA:stage1d-objectlock",
    "Account": "<Log Archive Account>",
    "Arn": "arn:aws:sts::<Log Archive Account>:assumed-role/AWSControlTowerExecution/stage1d-objectlock"
}
```

  **Nothing was written from this session and it was never ended.** It stayed exported in the shell, which
  is exactly the leak the next attempt then ran into — so the borrow was proven to work before the run
  that appears to fail on permissions, and the two entries below describe one shell, not two problems.

- **First attempt from Management, which failed and is recorded because the failure is instructive.** Login
  as CT Admin -> Management Account -> AWSAdministratorAccess. Log of commands executed on CloudShell:

```
~ $ LOG_ARCHIVE=$(aws organizations list-accounts --query "Accounts[?Name=='Log Archive'].Id | [0]" --output text) && BUCKET=$(aws cloudtrail describe-trails --region us-west-2 --query "trailList[?Name=='aws-controltower-BaselineCloudTrail'].S3BucketName | [0]" --output text) && echo "$LOG_ARCHIVE / $BUCKET"
aws: [ERROR]: An error occurred (AccessDeniedException) when calling the ListAccounts operation: You don't have permissions to access this resource.

~ $ read -r AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN < <(aws sts assume-role --role-arn "arn:aws:iam::${LOG_ARCHIVE}:role/AWSControlTowerExecution" --role-session-name stage1d-objectlock --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text) && export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN && aws sts get-caller-identity --region us-west-2
aws: [ERROR]: An error occurred (AccessDenied) when calling the AssumeRole operation: User: arn:aws:sts::<Log Archive Account>:assumed-role/AWSControlTowerExecution/stage1d-objectlock is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam:::role/AWSControlTowerExecution
```

- **Neither error was a permissions problem, and both messages named the wrong cause.** The shell still
  carried exported credentials from an earlier borrowed session, so every command ran as
  `AWSControlTowerExecution` in Log Archive Account, not as CT Admin in Management — `ListAccounts` is a
  management-account API and was correctly denied to it. Because the `&&` chain stopped there,
  `LOG_ARCHIVE` stayed **empty** and the next command built `arn:aws:iam:::role/...` with no account,
  producing a second `AccessDenied` that described the role failing to assume itself. **Nothing was written
  and `CTS3PV8` was never reached.**

- **Two operational rules taken from this.** A borrowed-role session leaks into every later command in the
  same shell, so **`unset` of the three credential variables is the pair of "leave the shell when done"**,
  not an optional tidy-up. And a resolution step must **abort on an empty value instead of building an ARN
  from it** — a chain that carries an empty variable forward turns a missing input into an authorization
  error, which is the wrong thing to debug.

- **Recovery and the write.** Login as CT Admin -> Management Account -> AWSAdministratorAccess. Log of
  commands executed on CloudShell:

```
~ $ unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN; aws sts get-caller-identity --region us-west-2
{
    "UserId": "AROA44RM7XIS6JKXK5MYL:<sso-user>",
    "Account": "<Management Account>",
    "Arn": "arn:aws:sts::<Management Account>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_a52d69579a1e4756/<sso-user>"
}

~ $ LOG_ARCHIVE=$(aws organizations list-accounts --query "Accounts[?Name=='Log Archive'].Id | [0]" --output text) && BUCKET=$(aws cloudtrail describe-trails --region us-west-2 --query "trailList[?Name=='aws-controltower-BaselineCloudTrail'].S3BucketName | [0]" --output text) && case "${LOG_ARCHIVE}:${BUCKET}" in ''*|*:''|None*|*:None) echo "ABORT: LOG_ARCHIVE='$LOG_ARCHIVE' BUCKET='$BUCKET'";; *) echo "OK $LOG_ARCHIVE / $BUCKET";; esac
ABORT: LOG_ARCHIVE='None' BUCKET='aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx'

~ $ LOG_ARCHIVE=$(echo "$BUCKET" | grep -oE '[0-9]{12}' | head -1) && echo "derived: $LOG_ARCHIVE" && aws organizations list-accounts --query "Accounts[?Id=='${LOG_ARCHIVE}'].[Name,Id]" --output text
derived: <Log Archive Account>
Log Archive Account     <Log Archive Account>

~ $ read -r AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN < <(aws sts assume-role --role-arn "arn:aws:iam::${LOG_ARCHIVE}:role/AWSControlTowerExecution" --role-session-name stage1d-objectlock --query 'Credentials.[AccessKeyId,SecretAccessKey,SessionToken]' --output text) && export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN && aws sts get-caller-identity --region us-west-2
{
    "UserId": "AROA4QN6B537DE4I3UXJA:stage1d-objectlock",
    "Account": "<Log Archive Account>",
    "Arn": "arn:aws:sts::<Log Archive Account>:assumed-role/AWSControlTowerExecution/stage1d-objectlock"
}

~ $ aws s3api put-object-lock-configuration --region us-west-2 --bucket "$BUCKET" --object-lock-configuration '{"ObjectLockEnabled":"Enabled","Rule":{"DefaultRetention":{"Mode":"COMPLIANCE","Days":90}}}'

~ $ aws s3api get-object-lock-configuration --region us-west-2 --bucket "$BUCKET"
{
    "ObjectLockConfiguration": {
        "ObjectLockEnabled": "Enabled",
        "Rule": {
            "DefaultRetention": {
                "Mode": "COMPLIANCE",
                "Days": 90
            }
        }
    }
}

~ $ unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN; aws sts get-caller-identity --region us-west-2
{
    "UserId": "AROA44RM7XIS6JKXK5MYL:<sso-user>",
    "Account": "<Management Account>",
    "Arn": "arn:aws:sts::<Management Account>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_a52d69579a1e4756/<sso-user>"
}
```

- **Filtering the account by name failed, and the fix is general.** No account is named `Log Archive`; it
  is **`Log Archive Account`**, which `ORGANIZATION.md` had wrong. Rather than correct the string, the id
  was **derived from the trail's own bucket name** — `list-buckets` returns only buckets the calling
  account owns, so the preflight already proved which account that is. Matching on an account name is
  matching on an editable field nobody guaranteed; the trail is the resource the step modifies
  (Lesson 23).

- **Decision 9 is taken: option A — borrow `AWSControlTowerExecution` from Management.** Declining leaves
  open exactly what the step exists to close: `CTS3PV8`'s `NotAction` **permits `s3:DeleteObject` and
  `s3:DeleteObjectVersion` to everyone**, so AWS protects the bucket's configuration and leaves its
  contents deletable on purpose, and D34 made the principal this defends against permanent. A
  project-owned second trail is a full second copy of CloudTrail in S3 to solve by duplication what one
  call solves. **What option A actually costs is precedent, not privilege** — whoever performs it is
  already administrator of that account, and the session adds exactly the set `CTS3PV8` denies. **So this
  is recorded as the only sanctioned by-hand use of `AWSControlTowerExecution`; any future one is a new
  decision.** The asymmetry that settled it: Object Lock cannot be undone, by us or by Control Tower, so
  the usual "a landing-zone update silently reverts a manual change" risk does not apply — an update can
  only fail, not revert.

- **Decision 7 is now exercised rather than only measured.** The `CTS3PV8` exemption is keyed on
  `ArnNotLike …:role/AWSControlTowerExecution` and it matched an assumed-role session, which is the same
  property 1c measured on `aws:PrincipalArn`.

- **Decision 3 is taken: 90 days, compliance mode — and its cost is zero, which the plan did not expect.**
  9.3 treats a long retention as the one cost easy to create by accident. The 9.1 reading removes that
  entirely: the bucket already expires current *and* noncurrent versions at 365 days, so for any retention
  **below** 365 the objects would be kept that long regardless — **Object Lock adds no storage and no
  spend.** The real trade is therefore how much of the trail is undeletable, and the only way to get it
  wrong is to collide with the lifecycle. 90 days gives a quarter of detection window and keeps wide
  clearance.

- **This creates a standing constraint that outlives the stage: the lifecycle rule on this bucket may
  never be shortened below the lock retention.** A future cost pass that cuts the 365 days to 90 or below
  makes the landing zone's own expirations start failing against locked versions, and the retention cannot
  be shortened to fix it. **This binds Stage 12 step 5.**

- **Verification (iv) is provisional by construction.** Whether the adjustment survives a landing-zone
  update, an account update or a re-enrollment is answerable only at the next such event — same shape as
  (xiv) and as 1b's (vi).

- **Step 9 is done, so Stage 1d is done, and with it the landing zone.**

- Login as CT Admin on Log Archive Account.

- **Verification that the default retention reaches new deliveries — which the bucket-level read-back does
  not prove.** Login as CT Admin -> Log Archive Account -> AWSAdministratorAccess. Log of commands executed
  on CloudShell (account ids replaced with names):

```
~ $ aws cloudtrail describe-trails --region us-west-2 --query "trailList[?Name=='aws-controltower-BaselineCloudTrail'].[S3BucketName,S3KeyPrefix,IsOrganizationTrail,IsMultiRegionTrail]" --output text; aws s3 ls "s3://$BUCKET/"
aws-controltower-cloudtrail-logs-<Log Archive Account>-gcs-gsx   <org-id>    True    True
                           PRE <org-id>/

~ $ aws s3 ls --recursive "s3://$BUCKET/" | grep "/CloudTrail/us-west-2/$(date -u +%Y/%m)/" | tail -3
2026-08-15 01:31:48       2457 <org-id>/AWSLogs/<org-id>/<Sandbox Account 1>/CloudTrail/us-west-2/2026/08/15/..._20260815T0130Z_....json.gz
2026-08-15 02:11:29      18588 <org-id>/AWSLogs/<org-id>/<Sandbox Account 1>/CloudTrail/us-west-2/2026/08/15/..._20260815T0210Z_....json.gz
2026-08-15 03:12:01      19678 <org-id>/AWSLogs/<org-id>/<Sandbox Account 1>/CloudTrail/us-west-2/2026/08/15/..._20260815T0310Z_....json.gz

~ $ aws s3api get-object-retention --region us-west-2 --bucket "$BUCKET" --key <the 03:12 key above>
{
    "Retention": {
        "Mode": "COMPLIANCE",
        "RetainUntilDate": "2026-11-13T03:12:00.325000+00:00"
    }
}
```

- **The control is exercised, not just configured.** The object was delivered at 03:12 on 2026-08-15,
  *after* the write, and carries `COMPLIANCE` until 2026-11-13 — 90 days, applied by the bucket default
  rather than by the caller. **Three deliveries the same day prove the lock did not stop delivery**, which
  was the opposite risk. A pre-existing object returns `NoSuchObjectLockConfiguration` and that is correct:
  a default retention binds objects written after it, never retroactively.

- **The trail carries an `S3KeyPrefix`, and it is the organization id**, so the real layout is
  `<org-id>/AWSLogs/<org-id>/<account>/CloudTrail/<region>/<yyyy>/<mm>/<dd>/` — the org id appears
  **twice**. A path built from `AWSLogs/` alone lists empty, which reads like "no deliveries" rather than
  "wrong prefix" (Lesson 13). **Read `S3KeyPrefix` from the trail before constructing any key**; the trail
  is again the only non-stale source, as it was for the bucket name.

- Login as AWS Control Tower Admin -> Management Account -> AWSAdministrator Access. Executed on cloudshell:

```
$ LZ=$(aws controltower list-landing-zones --region us-west-2 --query 'landingZones[0].arn' --output text) && aws controltower get-landing-zone --region us-west-2 --landing-zone-identifier "$LZ" --query 'landingZone.{status:status,drift:driftStatus,version:version,latest:latestAvailableVersion}'
{
    "status": "ACTIVE",
    "drift": {
        "status": "IN_SYNC"
    },
    "version": "4.0",
    "latest": "4.0"
}
```

- **Verification (iv), first half: read, and it is a weaker answer than it looks.** `status: ACTIVE`,
  `driftStatus: IN_SYNC`, `version 4.0` equal to `latestAvailableVersion`, so there is no pending landing-
  zone update either. **What this does not do is predict one.** Control Tower's drift detection watches a
  closed list of things *it* owns — its own `aws-guardrails-*` policies, OU and account placement, the
  `AWSControlTowerExecution` role, the Config recorder, the log bucket's **policy**, the trail's
  configuration — and an arbitrary bucket setting like Object Lock is very likely not among them. So
  `IN_SYNC` is a **weak negative**: it confirms nothing was tripped, not that the baseline and the lock
  agree. **This also explains why Stage 1c's ten attached documents never raised drift**: a customer SCP
  is not Control Tower's, so it is neither claimed nor watched.

- **The second half is unchanged, and decision 9 narrowed what it can find.** It is settled by the next
  landing-zone update, account update or re-enrollment, because an update re-applies the baseline without
  consulting `driftStatus`. Object Lock cannot be removed by Control Tower either, so the failure mode is
  an update **erroring**, not reverting — noisy instead of silent, which is the good side of an
  irreversible control.

- **Stage 1d is complete, and the landing zone with it.** All four steps executed, decisions 3, 4, 8, 9
  and 10 taken, verifications (iv), (v), (xiii) and (xiv) answered — (iv)'s and (xiv)'s second halves
  provisional by construction, each naming the event that settles it.

---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
