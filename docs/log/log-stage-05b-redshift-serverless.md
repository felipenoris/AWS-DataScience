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

---

## 2026-09-20 — 1.9, 1.10, pass 2, pass 3: the split holds, and the ceiling refuses

*Written by Claude in the same sitting, continuing the entry above. Same identity throughout unless a
step names another: `awsds-infra-sandbox-1`, and `awsds-infra-identity` for the two policy slices.*

### 1.9 — the endpoint host survives; the workgroup id does not

Destroy, then re-create, under the same name. **This is the reading the `[E]` layer rests on.**

| Read | Before | After |
|---|---|---|
| `endpoint.address` | `awsds-sandbox-warehouse.<Sandbox Account 1>.us-west-2.redshift-serverless.amazonaws.com` | **identical** |
| `endpoint.port` | `5439` | `5439` |
| `workgroupId` | `75b926c8-a206-4566-a397-84e398f2f4ee` | **`4b0577a2-6f30-4d9c-b069-b6bd1b6ab010`** |
| the usage limit's id | `cf7ced6a-…` | **`a5b0a714-…`** |
| the workgroup's VPC endpoint | `vpce-0c740e3be5ff53369` | **`vpce-0f8ecc79b20bbfd2e`** |
| its two ENIs | `10.20.22.101` / `us-west-2b`, `10.20.109.138` / `us-west-2a` | **`10.20.54.29` / `us-west-2b`, `10.20.77.126` / `us-west-2a`** |
| the namespace, the admin secret, the three log groups, the security group | present | **all present** |

**So decision 8 does not arise and the compute stays `[E]`.** The host is derived from the name, the
account and the Region, and a re-create under the same name restores it — which is what
[6h](../plan/stages/stage-06h-redshift-connection.md)'s connection needs.

**The id half is the finding, and it changes code.** A workgroup's ARN carries the service-minted
UUID, not the name, so **any policy naming this workgroup's ARN exactly would stop matching after the
first `make down`** — silently, presenting as a project whose queries stopped authenticating with no
diff anywhere. Two things were written against that reading: layer 2's IAM policy scopes to
`workgroup/*` in this account and Region, and `DenyRedshiftCostGuardTamperingExceptInfrastructure`
uses `Resource: "*"`. Both now say so in a comment.

**Timings**, which §5.1 rule 6 asks for: destroy **28 s** total (the workgroup itself 9 s), re-create
**114 s**. Comfortable for a session boundary rather than merely correct.

**One transient the plan did not predict.** Immediately after the destroy the old VPC endpoint was
gone but **its two ENIs survived in `available` state**, still referencing the `[P]` security group and
holding two private addresses, owned by an AWS service account. They were gone by the time the
re-create finished, under two minutes later. So it is a garbage-collection lag rather than a leak —
recorded because a `terraform destroy` of `sandbox/warehouse/` inside that window would fail on a
security group still in use, and the symptom would be unexplainable.

### 1.10 — the endpoint family, and the three tokens that are not in it

`terraform-modules/vpc-egress` gains a fourth optional group, **`redshift = ["redshift-serverless"]`**,
tagged **`vpc-egress-v0.15.0`** (confirmed on origin by `git ls-remote --tags`, whose hash matches
`git rev-parse`). `sandbox/egress/` moved to it; the other three callers stay on `v0.11.1`, where they
already were.

**All six `redshift*` endpoint services exist in `us-west-2`**, measured from the Region's own catalog
rather than assumed: `redshift`, `redshift-data`, `redshift-serverless` and a `-fips` sibling for each.
Only `redshift-serverless` is in the group; `redshift-data` waits on
[6h](../plan/stages/stage-06h-redshift-connection.md)'s credential answer and `redshift` on 6h 3.5's
CloudTrail reading. **Not exercised**: no space has been started with `GROUPS=redshift`, so
verification (xv) is open.

### Pass 2 — the access model

**2.3 applied** to `identity/sso`, `data_scientist` inline document 7,265 → 8,640 bytes, re-plan
`No changes`. One allow of six `redshift-serverless:` reads, and two denies:

- **`DenyMintingARedshiftDatabaseSession`** — `GetCredentials`, the three `redshift-data:` statement
  actions, and `redshift:GetClusterCredentials`/`GetClusterCredentialsWithIAM`. **The Data API is in
  it because of a measurement, not a guess**: it reaches the database from a laptop outside every VPC
  with nothing but an IAM identity and the admin secret (below), so a persona holding
  `ExecuteStatement` has a query path from anywhere and no security group sees it.
- **`DenyRedshiftCostGuardAndCompute`** — the nine create/update/delete calls on namespaces,
  workgroups and usage limits.

**Written as denies rather than left to omission**, for the reason the Lake Formation deny beside them
gives: these actions sit in services this set is granted real reads on, so an omission is one AWS
managed policy away from being undone. **Not exercised**: the persona's session is not open in this
sitting, so 6h 5.4 is owed.

**2.4 read rather than asserted, and all three came out as designed:**

- `awsds-sandbox-warehouse-exec` has **no attached policy, no inline policy and no permissions
  boundary**.
- **`awsdatacatalog` lists nothing** — zero rows from `svv_all_schemas` and `svv_all_tables` for that
  database, which is the correct state for a role Lake Formation has granted nothing.
- The documented read-only direction has a stronger form than the page says: **you cannot connect to
  `awsdatacatalog` at all.** `FATAL: Cannot connect to shared database "awsdatacatalog" created from
  Data Catalog ARN. Connect to a database in your cluster … and use cross-database query notation`.

### Pass 3 — the ceiling refuses, and the workgroup does not say so

**5.1, and the shape of the test had to change twice.**

First, a throwaway limit beside the real one is **impossible**:
`ValidationException: Only one DISABLE usage limit allowed per feature`. So the test lowered the real
limit instead. Second, and this is `WH-3`'s whole premise: **a second limit with `breach_action = log`
IS allowed** — created at 9,999 RPU-hours daily, `WH-3` failed on it naming *"2 limits - the loosest
one wins"*, and it was deleted. So the service prevents a second *ceiling* and permits a second
*looser* limit, which is exactly the hole the check exists for.

Then the real limit went to **1 RPU-hour** and a triple cross join over `pg_attribute` (46,391 rows,
so ~10¹⁴ output rows) was left to run. **The breach fired.** What it looks like, at each layer:

| Where | What it says |
|---|---|
| the client | **`ERROR: Query reached usage limit`** — six words, no policy, no limit id, no amount |
| `get-workgroup` | **`status: AVAILABLE`.** Nothing in the workgroup's own record shows it. An instrument that checked `status` would report a healthy warehouse that cannot run a query |
| `UsageLimitConsumed` | **`1.0`** against an amount of 1 |
| `UsageLimitAvailable` | **`38.0` and `40.0`** — stale, still reported against the amount before the change |
| `ComputeSeconds` (the day's total) | **405 RPU-seconds = 0.1125 RPU-hours**. The two numbers do not reconcile: the consumed metric appears to round **up** to whole RPU-hours, which means a limit of N is breached somewhere between N−1 and N real RPU-hours. Recorded as an open reading rather than explained |

**What the breach refuses is the compute, not the endpoint**, and the boundary is sharp:

| Statement | Result |
|---|---|
| `select 1` | **FINISHED** |
| `select count(*) from pg_attribute` | **FINISHED** |
| `select count(*) from svv_all_schemas` | **FINISHED** |
| `CREATE TABLE lab.probe_after_breach (x int)` | **FAILED — `Query reached usage limit`** |

Every statement that finished is answerable on the leader node. So a client can still connect and
query the catalogue on a deactivated warehouse, and **a health check of the shape "connect and
`select 1`" passes while no real query can run** — Lesson 13's shape, on the control this stage
called load-bearing.

**5.2 — recovery is immediate, and the documentation does not say so.** Raising the amount back to
**40** made `CREATE TABLE` succeed on the next attempt: **no wait for the period to roll over**, which
is the question verification (vi) asked and no vendor page answers. AWS's own guidance for a breached
quota is *"increase your workgroup usage quota"*, and that is what works. The independent fallback
never had to be used: 1.9 had already proven that destroying and re-creating the compute restores the
same endpoint host.

`./aws/warehouse.py --sql` after the restore: **11 pass, 1 note**, and the compute slice re-plans
`No changes`.

**5.3 — the measured cost of everything in this sitting: 405 RPU-seconds = 0.0405 USD** at
0.36/RPU-hour, against the 1.44 USD/query-hour prediction, which it is consistent with (405 s of
4-RPU time is 101 s of wall clock). **The free trial's status is unknown** (0.3a), so this figure comes
from `ComputeSeconds` and not from the bill either way.

### A perpetual diff the plan did not have, found by re-planning

**The service fills in six `config_parameter` defaults the code did not declare, and the provider
plans to remove them on every plan** — `auto_mv`, `datestyle`, `enable_case_sensitive_identifier`,
`query_group`, `search_path`, `use_fips_ssl`. `config_parameter` is a set the provider owns whole, so a
workgroup created with three parameters reads back with nine and the plan is `1 to change` forever.
All six are now declared at their read-back values and the slice plans clean.

**Two of them are worth knowing about rather than merely declaring.** `auto_mv` is **on** by default:
Redshift decides on its own to build and refresh materialized views, and a refresh is a query on a
1.44 USD/hour meter — compute the estate did not ask for, left at the default and named in the code so
turning it off is a decision somebody can find. `search_path` is `"$user, public"`, and `public` is the
schema 1.6 revoked `CREATE` on, so an unqualified `CREATE TABLE` fails rather than landing somewhere
nobody expects.

### 6.1 — the audit groups carry content, and whose is unresolved

All three groups exist; **`userlog` is empty and that is the correct state** (no user was created
through a session, and the ones that were came from SQL run as the admin). The other two carry
**1,176 events between 06:03:54Z and 06:15:50Z**, and every one of them is `user=rdsdb`, the service's
internal user — connection open/close and internal `xpx` operations.

**Not one `dbadmin` session appears, and neither does any of this sitting's SQL text**, including a
query written specifically to be searched for (`AUDITMARKER20260920`). **This is not yet evidence that
the Data API is unlogged**: the group's `lastIngestionTime` is **06:15:52Z** and nothing has been
ingested in the 53 minutes since, while queries ran throughout — so the export is either batched on
an interval nobody here has measured or has stalled. The instrument works (1,176 events prove it), but
it has not been given the chance to show the presence, which is exactly the condition Lesson 62 puts
on reading an absence. **Owed: a re-read of both groups in a later sitting**, and until then 6h 3.6 is
unanswered and Stage 11 should not assume the Data API path is in the feed.

### What pass 3 leaves owed

- **verification (xv)**, the endpoint door from inside a space, needs a space started with
  `GROUPS=redshift`.
- **6h 5.4**, the persona's `GetCredentials` refusal, needs the `awsds-scientist` session.
- **verification (xiii)**, the free trial, needs the Redshift console.

---

## 2026-09-20 — an amendment to 6.1, and the closing readings

*Written by Claude in the same sitting. This entry amends 6.1 above rather than editing it: the earlier
reading was taken 53 minutes after the last ingestion and this one at 73, which is the only thing that
changed.*

### 6.1 amended — the audit export stopped, and 73 minutes of queries did not restart it

At **07:29:48Z**, `lastIngestionTime` on both `connectionlog` and `useractivitylog` reads
**06:16:21Z**. Between those two times this sitting ran the quota breach, a 30-minute cross join, the
usage-limit breach, the recovery and roughly sixty statements. `logExports` still lists all three
types.

So the sharper statement is: **the export ingested a twelve-minute burst around the namespace's
creation — 1,176 events, every one the service's internal `rdsdb` user — and has ingested nothing
since, through 73 minutes of continuous query activity.** What that rules out is the pleasant reading,
that the groups are merely empty or that the feed has never worked. What it does not settle is whether
the Data API path is **never** exported or exported on an interval longer than 73 minutes, and the
06:03–06:16 burst cannot decide it either, because that window contains only `rdsdb` events too.

**Either answer is a finding [Stage 11](../plan/stages/stage-11-dlp.md) has to act on**, and they need
different repairs: if the path is not covered, the DLP feed has a hole exactly where this estate's own
instruments query, and CloudTrail's `redshift-data` events are the only record; if it lags by hours,
the feed is real but useless for anything time-bounded. **Owed: one re-read in a later sitting**, with
the marker query `AUDITMARKER20260920` as the search term — it is already in the namespace's history
and nothing removes it.

### The closing readings of the sitting

| Check | Result |
|---|---|
| `make check` | **OK** |
| `./aws/warehouse.py --sql` | **11 pass, 1 note** (`WH-13`, unreadable on this platform) |
| `./aws/datalake.py` | **zero failed checks**; `DL-5` and `DL-6` green in both accounts, so the key-policy statement this stage added to `sandbox/data/` disturbed nothing in the lake. Its exit code is 1 for the seven persona profiles whose SSO sessions are not open, which is the expected state of a session held as the infrastructure user alone |
| `make status ENV=sandbox` | `warehouse-compute` **UP, 2 resources, 0.0000 USD/h** — the mechanical form of the claim the split exists to make. `egress` and `probes` are **down**, which is why verification (xv) is still open: no space has been started with `GROUPS=redshift` |
| `terraform plan` on `sandbox/warehouse`, `sandbox/warehouse-compute`, `sandbox/data`, `identity/sso`, `identity/org-policies` | **`No changes`** on all five |

**The compute was left UP deliberately.** [6h](../plan/stages/stage-06h-redshift-connection.md)'s
remaining work is a portal session and a space, and both need the workgroup to exist. `make down
ENV=sandbox` is what ends the session, and it costs nothing to defer: the warehouse bills **0.00 per
hour** while no query runs, which is the whole reason the usage limit rather than the layer is the
guard while it is up.

---

## 2026-09-20 — an amendment to 5.3: the cost figure was ten times too small

*Written by Claude in the same sitting, at the end of it. It amends 5.3 above and the entry before this
one rather than editing either, per [`INDEX.md`](INDEX.md): the order things were learnt in is the
point.*

**5.3 said `405 RPU-seconds = 0.0405 USD`. The settled figure is `4,743 RPU-seconds = 1.3175 RPU-hours
= 0.4743 USD`** — twenty minutes of wall-clock query time at 4 RPUs, for everything this sitting did.

The reason is the metric, not the arithmetic. `ComputeSeconds` is *"accumulated compute-unit seconds
used in the last 30 minutes"* and it publishes **per half-hour interval**, so the 30-minute cross join
that caused the usage-limit breach had not been published when 5.3 was read. Its interval, when it
arrived, carried **3,842 of the 4,743** — nearly the whole bill in one datapoint:

| Interval (local) | RPU-seconds |
|---|---|
| 03:00 | 85 |
| 03:30 | 93 |
| **04:00** | **3,842** |
| 04:30 | 723 |

**So a Redshift cost figure read immediately after an expensive query is an under-reading**, and here
it was one by a factor of ten. It was written into `docs/PRICING.md`, `docs/plan/cost-model.md`,
`CLAUDE.md`, this stage's verification (vii) and `docs/log/INDEX.md` before the correction, and all
five now carry 0.4743 with the reason beside it. The lesson is not about Redshift: **a metric whose own
description names a window has not answered until that window has closed**, and the instrument's own
burn line (`./aws/warehouse.py`) has the same property.

It also strengthens one reading and leaves another alone. **The usage limit is evaluated in whole
RPU-hours**: `UsageLimitConsumed` said `1.0` against an amount of 1 and fired, while the real usage
settled at 1.3175 — consistent, where against 0.1125 it had looked like aggressive rounding. And the
prediction held: 1.44 USD per query-hour × 0.3294 hours of 4-RPU time is 0.4743.
