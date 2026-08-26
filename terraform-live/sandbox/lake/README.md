# sandbox/lake — the sandbox lake, layer `[P]`

The [Stage 16](../../../docs/plan/stages/stage-16-sandbox-lake.md) slice; the operating procedures are
[`runbooks/sandbox-lake.md`](../../../docs/plan/runbooks/sandbox-lake.md), and
`./aws/sandboxlake.py` (`SL-1`–`SL-5`) is what reads the result back. Applied as `awsds-infra-sandbox-1`
— SSO user the **infrastructure user**, account **Sandbox**, permission set **`InfrastructureAccess`**.

**WRITTEN 2026-08-26, NOT YET APPLIED.** Every row below describes what the code *declares*. The
baseline reading of the same day says the bucket, the role, the location and the grants do not exist
(`SL-1`–`SL-4` all `note`), and no sentence here may move into the perfect tense before an apply
([Lesson 37](../../../docs/plan/lessons.md)).

## What this bucket is, and what it is not

Permanent, per-SSO-group artifact storage in the experimentation account: the class D13 leaves
ungoverned (`scratch`) made **durable**, so a project can mature across weeks and across projects
instead of dying with either. The alternatives it replaces are the derived zone (expires by design —
30 days) and the SMUS project bucket (dies with its project, and shares nothing between projects).

It is **not** the governed lake. No Lake Formation registration, no LF-Tag, no resource link, no share.
D13's denies over `awsds-data-raw` and `awsds-data-curated` are untouched and this bucket appears in
none of them (measured 2026-08-26). A copy of governed data landing here is **Stage 11's finding to
make**, not a hole this slice can close ([Lesson 1](../../../docs/plan/lessons.md)) — which is why the
stage buys the permanence with five named compensations rather than with a control.

## The first apply is three acts over two slices

Not a preference: **KMS validates the principals in a key policy**, so the statement admitting the
access role cannot be written before the role exists.

| # | Slice | What |
|---|---|---|
| 1 | `sandbox/data/` | already applied — it owns `alias/awsds-sandbox-data`, the CMK this bucket names |
| 2 | `sandbox/lake/` | **this slice** — the bucket, the access role, the Access Grants location, the per-group grants |
| 3 | `sandbox/data/` | **again** — the one key-policy statement admitting the access role (`consumer-data-v0.3.0`) |

`scripts/tfhygiene/layers.py`'s `lake` rank comment carries the same order; the rank itself cannot
express it, because both slices are `[P]` and no `up`/`down` target ever acts on them.

## A permission here is the intersection of three documents in two slices

Nothing in this file, on its own, lets any object in `awsds-sandbox-lake` be read. A vended read needs
**all three**, and two of them are elsewhere:

| Document | Where | What it decides |
|---|---|---|
| the Access **Grant** | `grants.tf` (here) | who may *ask* for a session, and over which sub-prefix |
| the access role's **identity policy** | `iam.tf` (here) | what that session may do at all — one bucket, one key |
| the **key policy** | `sandbox/data/`, via `consumer-data` `v0.3.0` | whether S3 may decrypt for it |

This is [Lesson 28](../../../docs/plan/lessons.md) in one slice: **no single file in this repository
answers "what can this group do"**, and step 2.3's negative control exists to record the middle state
where two of the three are in place and nothing works yet.

## `main.tf` — the bucket

| Property | Value, and why |
|---|---|
| name | `awsds-<env>-lake` (conventions §6). Global, so it is a **D35 singleton** — the next business unit's bucket is a different name, and that is [open question 10](../../../docs/plan/open-questions.md)'s sixth token |
| key | `alias/awsds-<env>-data` — decision 1(a): `GOVERNANCE.md` §Encryption holds unamended, every data bucket encrypts under the data CMK of the account it lives in |
| **no `expiration_days`** | **the one bucket in this tree with no current-object expiry, deliberately.** The module's variable argues the other way — it exists so "the shadow lake does not silently become permanent" — and permanence is this bucket's whole requirement. The trade is priced in the stage file's five compensations and in [`institutional-delta.md`](../../../docs/plan/institutional-delta.md) |
| noncurrent versions | 90 days, multipart abort 7 days — the module's unconditional hygiene. Neither removes an object anybody expects to find again |
| **no `additional_policy_statements`** | the emptiness **is** the access model. Nothing reaches this bucket by naming it in a bucket policy; the only principal with a statement over its objects is the access role, and the only way to become it is a vended session. `SL-5` measures the identity side of the same claim |

Inherited unconditionally from the house module: versioning, SSE-KMS with bucket keys, all four
public-access-block flags, `DenyInsecureTransport`, `prevent_destroy`.

## `iam.tf` — `awsds-<env>-lake-access`

**One role doing two jobs, which is the point**: the Access Grants **location** role (the identity S3
vends when it answers `GetDataAccess`) and the SMUS connection's **access role** (the ARN typed into the
portal form). One principal to name in the key policy, one session identity in every CloudTrail row.

### The trust

| `Sid` | Who, and under what condition |
|---|---|
| `AccessGrantsServiceVending` | `access-grants.s3.amazonaws.com` — `sts:AssumeRole` + `sts:SetSourceIdentity`, pinned by `aws:SourceAccount` **and** `aws:SourceArn` = this account's Access Grants **instance** ARN. The instance is **SMUS-born (2026-08-22) and stays service-owned** ([Lesson 17](../../../docs/plan/lessons.md)); its ARN is *built*, not read, because `hashicorp/aws` v6.61.0 has **no data source** for it — measured, `terraform validate` names the absence |
| `SmusProjectAssume<key>` | **per wired project**, from `var.wired_projects` — the project user role, `sts:AssumeRole` under `sts:ExternalId` = the project id |
| `SmusProjectSourceIdentity<key>` | idem — `sts:SetSourceIdentity` matched to the caller's own `datazone:userId` principal tag |
| `SmusProjectTagSession<key>` | idem — `sts:TagSession` with `aws:RequestTag/AmazonDataZoneProject` pinned to the project id |

**The three project statements are three statements because they are three actions**: a trust admitting
`sts:AssumeRole` alone **rejects** an assume that also sets tags or a source identity.

**They are documentation-derived and unmeasured** until step 4.2 answers verification (ii) — AWS's
connection documentation, read 2026-08-26. `var.wired_projects` starts **empty**, so nothing unmeasured
is applied today; the first entry is written by the first wiring (§W). **Never a wildcard principal** —
`SL-2` fails on one, and the enumeration *is* the register that makes §R's second half auditable.

**Deliberately absent:** `sts:SetContext` — the directory-grantee path, which decision 2 declined so
that the Identity Center association stays [open question 13](../../../docs/plan/open-questions.md)'s own
decision. **Deliberately looser than the prose:** `AmazonDataZoneDomain` is not pinned; the principal is
already one project's role and the project id is already pinned, so pinning the domain would buy nothing
with a cross-account remote-state read. Revision trigger: a second domain in this estate.

### The permissions

| `Sid` | What |
|---|---|
| `ReadWriteLakeObjects` | `GetObject`, `GetObjectVersion`, `PutObject`, `DeleteObject`, `AbortMultipartUpload`, `ListMultipartUploadParts` on `<bucket>/*`. `DeleteObject` is in because a permanent store people use needs correction; **versioning is what makes that safe** |
| `ListTheLake` | `ListBucket`, `ListBucketMultipartUploads`, `GetBucketLocation` on the bucket |
| `UseTheAccountDataKeyViaS3` | `Decrypt`, `GenerateDataKey`, `DescribeKey` on the account data CMK, `kms:ViaService = s3.<region>` — **the identity half only**; the key policy is the other half and lives in `sandbox/data/` |

**Deliberately not carried, as a recorded deviation from AWS's documented "option 1" location role:** the
`S3AG*` location/grant-management statements and the `iam:PassRole` to the Access Grants service. They
exist so a connection can register its *own* location; here the location is pre-registered. **Verification
(ii) is the gate** — if creating a connection demands them, they join as a measured amendment with a date.

**`permissions_boundary = null`, and it is a decision** (the module makes the argument required so it has
to be one): the identity policy is already one bucket and one key, and every vended session is narrowed
again by the grant's scope-down. A boundary would be a third copy of the same narrowing, and
[Lesson 20](../../../docs/plan/lessons.md) turns redundancy into a cost. **Revision trigger:** the first
statement added to this role naming anything other than this bucket or this account's data key.

## `grants.tf` — the location and the standing grants

| Resource | What it declares |
|---|---|
| `aws_s3control_access_grants_location.lake` | scope `s3://awsds-<env>-lake/`, vending role = the access role. Its `access_grants_location_id` is an **output** — the value the runbook's §W needs on every wiring |
| `aws_s3control_access_grant.tenant["<sso-group>"]` | one per `var.tenants` row: sub-prefix `<sso-group>/*`, permission `READWRITE`, grantee = **that group's reserved SSO role in this account**, resolved by pattern through `one()` |

**A grant attaches no policy to anybody.** It says: this grantee may ask `GetDataAccess` for this
sub-prefix and get back a session of the *location's* role, scoped down to it.

**The instance is neither declared nor adopted** — see the trust row above. Terraform owns the location
and the standing grants because both **outlive every project**; the **per-project** grants are hand-made
under §W and revoked under §R, because they die with their project.

## The tenants, and why the roster is not a copy

`var.tenants` maps an `sso-group-*` **name** to the permission set whose reserved role is its grantee.
The group name **is** the prefix, so this one map is simultaneously the bucket's layout and the grant
table over it — which is what makes an unexpected top-level prefix a finding (`SL-4`).

Measured 2026-08-26 (step 0.2), against the deployed assignments and this account's reserved roles:

| `sso-group-*` | Permission set | Laptop path today |
|---|---|---|
| `sso-group-data-scientists` | `DataScientistAccess` | **yes** — the only set referencing `awsds-org-project-storage-vending` |
| `sso-group-deployment-managers` | `DeploymentManagerAccess` | **no** — inert until `identity/sso/` extends that by-name reference |
| `sso-group-dev-env-stewards` | `DevEnvStewardAccess` | **no** — same |

`sso-group-infrastructure` **is** assigned to this account and gets **no prefix**: it is the operator of
this bucket, not a tenant of it. That is why the table is this slice's decision rather than a copy of
`identity/sso/`'s — the two answer different questions. What keeps it from drifting anyway is `one()`:
a row naming a permission set not provisioned here **fails the plan**, so an invented tenant cannot be
applied and a withdrawn one fails by name on the next plan.

The two inert rows are written now anyway: the prefix contract is the bucket's layout, and a layout with
a hole in it invites somebody to fill the hole differently.

## What this slice does **not** hold

- **the Access Grants instance** — SMUS-born, service-owned, read-but-never-declared
- **per-project grants and their S3 connections** — the runbook's, because they die with projects
- **the key-policy statement** — `sandbox/data/`'s, because that slice owns the key
- **`awsds-org-project-storage-vending`** — `*/foundation/`'s, referenced by name from the persona set;
  it is what lets a laptop call `GetDataAccess` at all, and it is not this stage's to widen
