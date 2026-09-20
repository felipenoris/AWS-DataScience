# Log — Stage 5b — Redshift Serverless: the warehouse beside the lake

*The stage file is [`docs/plan/stages/stage-05b-redshift-serverless.md`](../plan/stages/stage-05b-redshift-serverless.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

*Identifiers are redacted as [`INDEX.md`](INDEX.md) requires: an account id becomes the account's name
in angle brackets, an e-mail address inside an ARN becomes that user's role. Everything else in a pasted
output stays verbatim. All times UTC.*

---

## 2026-09-20 — pass 0 and pass 1: the warehouse exists, and four things the plan did not know

*Written by Claude in the sitting that ran them, at the user's instruction to execute the stage and log
each step. Every reading is Claude's own, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`,
permission set `InfrastructureAccess`). ARNs are written without their account segment.*

### 0.1 — two subnets in two AZs, and the service accepted them

The two sources disagreed and the stage said the apply would settle it. It did: the workgroup was
created with **two** subnets and `enhancedVpcRouting: false`, so **AWS's own considerations page was
right and the Terraform provider's page was wrong** (that page says `subnet_ids` "must contain at least
three subnets spanning three Availability Zones"; its code carries no validator). **Decision 1 does not
arise** — no third AZ, no `vpc` module change, no `check-network-doc.py` arithmetic.

The subnets, read from the EC2 API rather than from prose:

| Subnet | AZ | Zone id | CIDR |
|---|---|---|---|
| `subnet-016b5a3a62c739894` | `us-west-2b` | `usw2-az1` | `10.20.0.0/18` |
| `subnet-09d3399d6b0fec93a` | `us-west-2a` | `usw2-az2` | `10.20.64.0/18` |

### 0.2 — the price is unchanged

`AmazonRedshift/current/us-west-2/index.json`, `publicationDate: 2026-09-11T12:45:05Z` — the same offer
file the stage was written against. SKU `KQ3J5VYQJZ5QMG9Z`, usage type `USW2-Redshift:ServerlessUsage`,
operation `RunServerlessCompute:001`:

```
0.3600000000 USD per RPU-Hr | $0.36 per RPU-Hr for Redshift Serverless compute charges in US West (Oregon)
```

So **4 RPUs = 1.44 USD per query-hour** stands, and `docs/PRICING.md` §5 needs no edit. Two
neighbouring SKUs exist and are not this one — `…-CR-1YR-NU` and `…-CR-1YR-AU`, the reserved-capacity
forms — which is why the reading names the usage type rather than "the serverless SKU".

### 0.3 — no policy in this organization mentions Redshift

`redshift` appears in **none** of the documents under
`terraform-live/identity/org-policies/policies/`. So a workgroup in **Data Governance** is refused by
no control today: what closed that shape was `D22`'s absence of a VPC in that account, which is
architecture rather than control. **Decision 6 stands as recommended** — Data Governance is not
reconsidered, and this reading is the reason.

### 0.4 — the quotas are not a blocking input

`service-quotas list-service-quotas --service-code redshift-serverless`:

| Quota | Value | Adjustable | Code |
|---|---|---|---|
| Serverless Namespaces | 25 | yes | `L-96772D74` |
| Serverless Workgroups | 25 | yes | `L-51089E7F` |
| Redshift Processing Units (RPUs) | 3200 | yes | `L-1854027F` |

**There is no base-capacity quota**; the RPU quota is the aggregate. Stage 9's second namespace lands
in a different account with its own 25, so nothing here waits on a vend. The service's own limits page
adds what the API does not report: **100 databases and 9,900 schemas per namespace**, 200,000 tables,
**idle-session timeout 1 hour** (four hours on a provisioned cluster — a different number for the same
name), **idle-transaction timeout 6 hours**, and **86,399 seconds** as both the maximum and the
no-limit value for a running query.

### 0.3a — the free trial could not be read from the CLI, and its absence from the API is the finding

No Redshift or Billing API reports free-trial eligibility or a credit balance; the page that documents
the trial points at the console. **So verification (xiii) is owed to a console reading and stays open**
— see the pending list at the end of this entry. What the stage predicted about it holds either way:
while a trial is active, *"billing details for free trial usage does not appear in the billing
console"*, so the cost readings of 5.3 and verification (x) must come from `SYS_SERVERLESS_USAGE` and
the credit balance rather than from the bill.

### 1.1–1.7 — the two slices, written and applied

`sandbox/warehouse/` (rank **53**, `[P]`) and `sandbox/warehouse-compute/` (rank **54**, `[E]`), with
`scripts/tfhygiene/layers.py` and `backend.py` rows. `./scripts/slices.py check`: **32 slices declared,
32 on disk**. `checkov`: 48 passed, 0 failed, 7 skipped on the `[P]` slice; 1 passed, 0 failed on the
`[E]` one. `tflint`: clean on both.

One decision was **corrected against a reading** rather than taken as written:

> **Decision 2's letter is impossible and its intent is `price_performance_target { enabled = false }`.**
> The decision said *"the target set to Optimizes for cost, because AWS does not recommend AI-driven
> scaling at 4 base RPUs and the default is Balanced"* — two halves that cannot both be done, because
> *Optimizes for cost* **is** the feature. AWS (*Compute capacity for Amazon Redshift Serverless*, read
> 2026-09-20): the target *"is enabled by default for all new Serverless workgroups and is set to
> **Balanced**"*, its `level` takes *"1, 25, 50, 75, and 100 … LOW_COST, ECONOMICAL, BALANCED,
> RESOURCEFUL, and HIGH_PERFORMANCE"*, and *"We do not recommend using this feature for 4 Base RPU"*.
> So the decision's premise was right — the default is Balanced **and enabled** — and its conclusion
> was not. `max_capacity = 8` stands unchanged.

The values applied, all four of which are this stage's own numbers and not the plan's:

| Value | Applied | Why |
|---|---|---|
| `max_capacity` | **8** | decision 2. Worst hourly rate bounded at 2.88 USD/h |
| usage limit | **40 RPU-hours, `monthly`, `deactivate`** | 10 hours of query time = 14.40 USD/month, 29% of the D12 ceiling, leaving room for the RMS storage this limit does not bound. `monthly` so a breach and D12's budget speak about the same month |
| `max_query_execution_time` | **1800** s | one runaway query bounded at 0.72 USD of compute |
| `DataStorage` alarm | **10 USD/month = 426,667 MB (417 GB)** | 6h decision 7. The metric is in **megabytes** on the `Namespace` dimension, so the threshold is argued in dollars and converted in `data.tf`. 417 GB is well under one 1 TB schema quota, so the alarm fires long before a single schema can fill |

### 1.8 — the readings, after two failed applies

**Three refusals before the namespace existed, and each one is a reading.**

**(a) The security group description cannot contain an apostrophe.**

```
InvalidParameterValue: Invalid security group description. Valid descriptions are strings less than
256 characters from the following set:  a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*
```

No apostrophe in the set. The description said *"…admitted SMUS projects' app ENIs…"*.

**(b) The account data CMK refused the namespace, and the refusal is `D31` working as designed.**

```
ConflictException: Unable to create namespace credential secret: The KMS key used to encrypt the
secret is not accessible
```
then, after the secret's key was dropped,
```
ValidationException: Unable to create namespace. The key 'arn:…:key/4950…' is inaccessible.
```

Probed directly, the wording separates the two layers by itself:

```
An error occurred (AccessDeniedException) when calling the GenerateDataKey operation: User:
…/AWSReservedSSO_InfrastructureAccess_…/<infrastructure user> is not authorized to perform:
kms:GenerateDataKey on resource: arn:…:key/4950… because no resource-based policy allows the
kms:GenerateDataKey action
```

**`no resource-based policy allows`** — so the identity policy does allow it and the **key policy** does
not, which is exactly what `terraform-modules/consumer-data/kms.tf` intends: root holds every
administrative action and **no cryptographic one**, so *"delegation to IAM is therefore impossible for
the operations that read data"*. `kms list-grants` on the key returned `[]` before and the service
creates its own grant afterwards, which is what makes the fix a creation-time door rather than a
standing one.

Two changes followed, and they are not symmetric:

1. **The admin secret gave up the CMK.** AWS: *"Optionally, you can specify a customer managed key to
   encrypt the secret **if you need to access the secret from another AWS account**. You can also use
   the KMS key that AWS Secrets Manager provides."* Nothing reads this secret from another account, so
   `admin_password_secret_kms_key_id` was **removed** and the secret rides `aws/secretsmanager`.
   Granting `kms:Decrypt` and `GenerateDataKey` on the **data** key so that a **credential** could be
   created would have widened the read control D31 exists to hold, for a reason unrelated to reading
   data. `docs/GOVERNANCE.md`'s per-account encryption rule is untouched: it is about data, and
   `kms_key_id` — the namespace's data — still names `alias/awsds-sandbox-data`.
2. **The namespace's own encryption needed a statement, and got the narrowest one that works.**
   `sandbox/data/` now passes a second `additional_data_key_policy_statement`,
   **`AllowRedshiftServerlessViaServiceInThisAccount`**: principal the account root, actions
   `kms:Encrypt`/`Decrypt`/`ReEncrypt*`/`GenerateDataKey*`/`CreateGrant`/`DescribeKey`, condition
   `kms:ViaService = redshift-serverless.us-west-2.amazonaws.com`. The `root` form **delegates to IAM**,
   so both halves must hold — an identity policy that already allows the action *and* a call arriving
   through Redshift Serverless — which keeps D31's line where D31 draws it: `ReadOnlyAccess` carries no
   `kms:Decrypt`, and reading data through this service needs a database session, which 2.3 withholds
   from `DataScientistAccess`. AWS's note on the service is why there is nothing tighter to add:
   Redshift Serverless *"does not support encryption context or confused deputy headers, so access for
   this service is scoped using `kms:ViaService` only"*. `sandbox/data/` re-plans **`No changes`**.

**(c) A failed `CreateNamespace` rolls the namespace back and leaves its secret behind.**

```
ConflictException: Unable to create namespace credential secret: Unable to create secret for the
dbInstance because a secret with a matching name exists
```

`redshift!awsds-sandbox-warehouse-whadmin` — `OwningService: redshift`, `RotationEnabled: true`,
created `2026-09-20T02:53:29-03:00`, and tagged `aws:redshift-serverless:namespaceArn =
…:namespace/bf04abe5-e08b-468b-84c3-166cf8642ad1`, **a namespace id that no longer exists**
(`list-namespaces` returned empty; `get-namespace` returned `ResourceNotFoundException`). So the
service created the namespace, failed on the key, rolled the namespace back, and did not roll back the
secret. The secret's name is derived as `redshift!<namespace>-<username>`, and the namespace name is a
contract (three log-group paths derive from it), so **the admin username moved from `whadmin` to
`dbadmin`** and the apply went through. **The orphan is still there** and is in the pending list below.

**Then the readings, all green.**

`aws_redshiftserverless_namespace` + `aws_redshiftserverless_workgroup`, created
`2026-09-20T06:02:58Z`, both `AVAILABLE`. The workgroup's create took **67 s** wall clock for the whole
apply.

| Check | Read |
|---|---|
| `WH-1` | `baseCapacity: 4`, `maxCapacity: 8`, `publiclyAccessible: false`, `enhancedVpcRouting: false`, the two subnets above, security group `sg-0feeaf8a17c82c5ad` |
| `WH-2` | `require_ssl: true`, `enable_user_activity_logging: true`, `max_query_execution_time: 1800`, and **`pricePerformanceTarget: {"status": "DISABLED"}`** — with **no `level` key at all**, which confirms that `level` has meaning only while the feature is on |
| `WH-3` | one limit: `serverless-compute`, `amount: 40`, `period: monthly`, **`breachAction: deactivate`**, and no second looser one |
| `WH-4` | all three groups at **`retention=30`**, `storedBytes=0`. This estate still has exactly **one** never-expiring group (`EXC-10`) |
| `WH-5` | `manage_admin_password: true`, `adminPasswordSecretArn` set, `adminPasswordSecretKmsKeyId: null`. The state file is 28,131 bytes; `admin_user_password` appears four times **as an attribute name whose value is `null`**, and the strings `"password"` and `adminUserPassword` appear **zero** times |

Two readings the plan did not ask for and that matter later:

- **`get-workgroup` reports `port: null`** while the endpoint reports `5439`. A check that asserts the
  port from `get-workgroup` would read a blank, not a mismatch.
- **`trackName: current`**, the patch track. 5b's "online patching" risk applies to this track.

`endpoint.address` — the value step 1.9 is about, and the field
[6h](../plan/stages/stage-06h-redshift-connection.md)'s connection stores:

```
awsds-sandbox-warehouse.<Sandbox Account 1>.us-west-2.redshift-serverless.amazonaws.com:5439
```

The account segment is redacted per `INDEX.md` rule 1, and the redaction costs nothing here because the
host is **derived, not chosen**: `<workgroup>.<accountId>.<region>.redshift-serverless.amazonaws.com`.
That derivation is also why 1.9's reading is worth taking rather than assuming — a host built from three
values that do not change ought to survive a delete and re-create, and "ought to" is what step 1.9 is
for.

### What pass 1 did not do

- **No `REVOKE` has run.** The database `warehouse` still grants `USAGE` and `CREATE` on `public` to the
  group `PUBLIC`. The statements are in
  [`terraform-live/sandbox/warehouse/README.md`](../../terraform-live/sandbox/warehouse/README.md) and
  running them needs a database session, which is the same blocker as 6h's layer 3.
- **The burn is 0.00.** No query has run, so the claim D40 rests on is untested rather than confirmed;
  pass 3 is what tests it.

### A consequence of the `[P]`/`[E]` split the plan did not have

AWS, on Redshift-managed admin credentials: *"If your serverless namespace doesn't have a workgroup
associated when Amazon Redshift attempts to rotate its attached secret, the rotation will fail and
won't try to rotate it again, even after you attach a workgroup. You must restart the auto-rotation
schedule using the `secretsmanager:RotateSecret` API call"* — and the default schedule is **every 30
days**.

The compute is `[E]`, so *no workgroup* is the normal state between sessions. A scheduled rotation will
almost always land in a window with no workgroup and **stop permanently**. It is a consequence of the
split rather than a defect in it — nothing else in this estate rotates a credential, and the
alternative is keeping a workgroup up so that a secret can rotate, which costs the guarantee the split
exists to give. Recorded in `docs/AWS_STATE.md` as a residual, with the restart call named.
