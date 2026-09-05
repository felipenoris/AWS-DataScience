# Runbook — the sandbox lake

> **Re-measured, not re-designed, at [Stage 6c](../stages/stage-06c-networking-hub.md) — 2026-09-05.**
> The bucket, the grants, the access role and every procedure below are unchanged. What moves is the
> *address* the laptop presents: after the hub is built, `s3control:GetDataAccess` leaves through the
> Squid proxy and the S3 calls through `VPC-Networking`'s gateway endpoint, so §T's laptop half and
> `s3-read-write` are re-run in that stage's pass 6 as the proof that the VPN-only conditions were
> re-keyed completely.

| | |
|---|---|
| **Scope** | The fourth Sandbox bucket, `awsds-sandbox-lake` — permanent per-SSO-group artifacts — and every recurring act its life needs: the prefix contract, wiring a SageMaker Unified Studio project to a prefix (the portal's **S3 connection**), the two read/write tests, and revocation when a project dies. The build itself is [Stage 16](../stages/stage-16-sandbox-lake.md)'s, once; this file is what runs *per project*, forever |
| **Operator** | §W and §R: the **infrastructure user** — account **Sandbox**, permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`; every write is authorized per occurrence. §T's in-project half: a **data-scientist persona, in the portal**, no CLI. §T's out-of-project half: a Sandbox SSO user through [`s3-read-write/`](../../../s3-read-write/README.md), profile `awsds-scientist-sandbox`, on the VPN. §P: the tenant's own code — a wired project's notebook, or the laptop as the group's SSO user on the VPN |
| **The two rules** | **This is not the governed lake**: nothing here is catalogued, LF-tagged or granted through Lake Formation — the governed lake's questions belong to [`data-governance/data/README.md`](../../../terraform-live/data-governance/data/README.md), and moving data between the two is a deliberate act (§G), never a mount. **A project's access is a pair of registered objects** — a grant and a trust entry — so it dies with the project or §R is owed; an orphaned grant is `SL-4`'s finding and the orphaned trust half surfaces under `SL-2`, neither of them housekeeping |
| **The picture around it** | Why the bucket exists and what its existence costs: the stage file's own argument. What is *expected* on the instance at any moment: [`docs/AWS_STATE.md`](../../AWS_STATE.md)'s lake-bucket and vending rows. The instrument: `./aws/sandboxlake.py` (`SL-1`–`SL-5`), the first thing to run when anything here surprises |
| **Written** | 2026-08-26, at Stage 16 planning, as designs read from AWS's documentation (the 2026-08-26 rows of [`docs/REFERENCES.md`](../../REFERENCES.md)) — and **exercised the same day**: §W (steps 4.1-4.2), §T's both halves (4.4 and 5.1, with the in-image amendment the exercise forced), §R's **grant half** (6.1, sacrificial; the **trust half** waits a real project's death), §P added after the readings at the user's request. Each section's own marker carries its date and its limits (Lesson 37) |

---

## D. What it is — and what it is not

One `[P]` bucket in Sandbox, `awsds-sandbox-lake` (`sandbox/lake/`), SSE-KMS under
`alias/awsds-sandbox-data` (Stage 16 decision 1(a), the recommendation), versioned, TLS-only, BPA on,
**no expiry on current objects** — the one S3
surface in this estate where artifacts are *meant* to outlive both the session and the project. It is not
the governed lake (no catalog object, no LF-Tag — D13's non-registered class), not the derived zone — which since D19's 2026-08-26 revision is the SMUS project path —
(nothing expires), and not the project path (nothing here is keyed by a project id). Access is **only** by
vended, prefix-scoped, expiring credentials from the account's S3 Access Grants instance — no persona and
no project role carries a standing identity statement on this bucket, which is what makes the entitlement
an enumerable register.

## G. The prefix contract

One prefix per SSO group: `s3://awsds-sandbox-lake/<sso-group>/`, read-write for that group's members and
nobody else. The roster is **derived** — a group gets a prefix when it holds a persona assignment in this
account (three by today's assignments: `sso-group-data-scientists`, `sso-group-deployment-managers`,
`sso-group-dev-env-stewards` — confirmed at Stage 16 step 0.2, never from this sentence; only the first
set carries the vending policy, so the other two groups' laptop path is inert until `identity/sso`
extends it) — and each prefix is opened by exactly one standing grant
(`<sso-group>/*`, `READWRITE`, grantee = the reserved role of that group's permission set; Stage 16
decision 2). Two norms ride the contract, stated here because nothing enforces them: **the classification
of a source follows its copies in** — the output of a query over `restricted` data is `restricted` here as
anywhere — and **what matures leaves by the promotion chain** (git for code; the governed ingestion path
for data bound for the lake), because this bucket is a workshop, not an archive of record and never a
serving path.

## W. Wire a project — as projects appear

**First exercised 2026-08-26 (Stage 16 steps 4.1-4.2): steps 1-5 all ran, the connection worked first try with the four fields, and CloudTrail showed the trust's direct-assume door (ExternalId + session tags) AND the vend door both in use.** §R's grant half followed the same day (6.1); its trust half waits a real project's death.

A project's access is three acts: a grant, a trust entry, a connection. The first two are the
infrastructure user's; the third is done in the portal, by a project member or the operator with them.

1. **Read the project's user role ARN and its project id** — both on the project's **overview page**
   (the documented location; the id is the trust's `sts:ExternalId`). The user has also observed the
   ARN (`datazone_usr_role_<project>_<env>`) displayed in the connection form. The CLI fallback for the
   role:

   ```bash
   aws iam list-roles --path-prefix / --query 'Roles[?starts_with(RoleName, `datazone_usr_role`)].[RoleName,Arn]' --output table --profile awsds-infra-sandbox-1
   ```

2. **Cut the grant** — prefix = the group's folder, grantee = the project role. The location id is the
   bucket-wide location Stage 16 pass 3 registered (`list-access-grants-locations` shows it):

   ```bash
   aws s3control create-access-grant --account-id "$(aws sts get-caller-identity --query Account --output text --profile awsds-infra-sandbox-1)" --access-grants-location-id <location-id> --access-grants-location-configuration 'S3SubPrefix=<sso-group>/*' --grantee 'GranteeType=IAM,GranteeIdentifier=<the project user role ARN>' --permission READWRITE --profile awsds-infra-sandbox-1
   ```

3. **Add the pair to the access-role trust** — append (role **NAME**, project id) to
   `var.wired_projects` in `sandbox/lake/variables.tf` and `terraform apply` (Recipe A); the entry
   expands to the three documented project-side statements (`sts:ExternalId` = the project id,
   `sts:SetSourceIdentity`, `sts:TagSession` — Stage 16 step 2.1). **The NAME, never the ARN** — the
   table lives in a tracked file and the ARN carries the account id (`aws/INDEX.md` rule 1); the slice
   builds the ARN itself, and a second validation holds name and project id consistent. The trust is
   enumerated by design; a wildcard there is `SL-2`'s finding.

4. **Create the connection, in the portal**: **Name**, URI `s3://awsds-sandbox-lake/<sso-group>/`,
   Region `us-west-2`, and the access role picked from the dropdown (`awsds-sandbox-lake-access`).
   **Measured 2026-08-26 (first run): those four fields are the whole form** — nothing extra was
   demanded, and creation raised no `S3AG*`/`iam:PassRole` complaint, so the access role's deliberate
   omission of the location-management statements stands measured. A future field beyond these four is
   recorded (Lesson 39).

5. **Register the pair** in `docs/AWS_STATE.md` (the vending discipline: a grant nobody registered reads
   as drift), and re-run `./aws/sandboxlake.py` — the only acceptable ending is `SL-1`–`SL-5` pass.

## T. The two tests — each proving a different claim

**First exercised 2026-08-26 (Stage 16 steps 4.4 and 5.1) — with one amendment the exercise itself
forced, below.**

- **In the project** (proves the *wiring*): from JupyterLab, write a file through the mounted location,
  list, read it back. Then the refusal that makes the pass meaningful: a vend for a scope the project
  holds no grant over (another group's prefix, or anything above the wired one) must come back
  `AccessDenied` **in the grant register's wording** — *"You do not have … permissions to the requested
  S3 Prefix"*. Working-and-refusing together is the pass; either alone is not (Lesson 13).
  **What this test can NOT include, measured 2026-08-26: a "direct un-vended" refusal.** The SMUS
  JupyterLab image ships **`aws_s3_access_grants_boto3_plugin`**, which intercepts every boto3 S3 call
  and vends underneath it (caching the credentials, so most calls show no fresh `GetDataAccess` in the
  trail) — a plain `list_objects_v2`/`get_object` from the notebook **succeeds by design**, and reading
  that 200 as a hole is Lesson 30's mistake. The direct-refusal control lives in the laptop half alone.
  The third refusal the first draft named — the same read from a *second* project holding no grant —
  stays unexercised until a second project exists.
- **From the laptop, no project in the path** (proves the *persona* path): on the VPN, as the group's SSO
  user, the `s3-read-write` sequence unchanged — discover (`ListCallerAccessGrants`), vend
  (`GetDataAccess` on `s3://awsds-sandbox-lake/<sso-group>/*`), write, list, read back. The vended
  session's ARN names **the access role** (the project-path vend names the project role — the difference
  is the diagnostic if a vend surprises). The persona's *direct* `aws s3` call on the bucket must still
  refuse — vended-only is the design, this is its negative control, and **the laptop is the only place
  it is runnable**: no plugin sits in that path.

## P. Python — list, read, write

*For the tenant's own code — a notebook cell or a laptop script. Added 2026-08-26 at the user's
request, after the stage's readings; every claim below carries the measurement it rides on.*

**Two contexts, opposite rules, both measured 2026-08-26.** Inside a SMUS JupyterLab, the image ships
`aws_s3_access_grants_boto3_plugin`, which calls `GetDataAccess` underneath every plain boto3 S3 call —
so plain code is the whole answer and an explicit vend is unnecessary. On the laptop no plugin exists:
the explicit vend is the **only** door, because a direct call is refused (§T's negative control). Both
paths end in the same place — a session of `awsds-sandbox-lake-access`, scoped down to the grant's
prefix, expiring.

### In a SMUS notebook — plain boto3; the plugin vends underneath

Works where the project is wired (§W): the plugin rides the **project role's** grant.

```python
import boto3

BUCKET = "awsds-sandbox-lake"
PREFIX = "sso-group-data-scientists/"  # your group's folder (§G), trailing slash included

s3 = boto3.client("s3")

# write
s3.put_object(Bucket=BUCKET, Key=PREFIX + "demo/hello.txt", Body=b"hello")

# list (paginate - list_objects_v2 pages at 1000 keys)
for page in s3.get_paginator("list_objects_v2").paginate(Bucket=BUCKET, Prefix=PREFIX):
    for obj in page.get("Contents", []):
        print(obj["Key"], obj["Size"])

# read
body = s3.get_object(Bucket=BUCKET, Key=PREFIX + "demo/hello.txt")["Body"].read()
```

Asking outside the granted prefix raises `AccessDenied` **in the grant register's wording** — *"You do
not have READWRITE permissions to the requested S3 Prefix"* — not a policy's; that is the vend being
refused, relayed. The plugin caches credentials, so most calls show no fresh `GetDataAccess` in the
trail (step 4.4's reading).

### On the laptop — the explicit vend is the only door

Preconditions: **VPN up**, signed in as the group's SSO user — for `sso-group-data-scientists`, profile
`awsds-scientist-sandbox` (account **Sandbox**, permission set **`DataScientistAccess`** — today the
only set carrying the vending policy, §G).

```python
import boto3

BUCKET = "awsds-sandbox-lake"
GROUP = "sso-group-data-scientists"  # your group (§G)

sess = boto3.Session(profile_name="awsds-scientist-sandbox")
acct = sess.client("sts").get_caller_identity()["Account"]

c = sess.client("s3control").get_data_access(
    AccountId=acct,
    Target=f"s3://{BUCKET}/{GROUP}/*",
    Permission="READWRITE",  # or READ - request only what the task needs
    Privilege="Default",
)["Credentials"]  # dies at c["Expiration"] (~1 h default); nothing renews it - re-vend

lake = boto3.Session(
    aws_access_key_id=c["AccessKeyId"],
    aws_secret_access_key=c["SecretAccessKey"],
    aws_session_token=c["SessionToken"],
).client("s3")

lake.put_object(Bucket=BUCKET, Key=f"{GROUP}/demo/hello.txt", Body=b"hello")
print(lake.list_objects_v2(Bucket=BUCKET, Prefix=f"{GROUP}/")["KeyCount"])
print(lake.get_object(Bucket=BUCKET, Key=f"{GROUP}/demo/hello.txt")["Body"].read())
```

Four facts to code against, each measured at Stage 16:

- **The vend is not optional here.** The persona session's direct S3 call on this bucket is refused —
  *"no identity-based policy allows"* (2.3) — and that refusal is the design, not a misconfiguration.
- **The session is the access role**, `awsds-sandbox-lake-access/access-grants-…`, scoped to the
  grant: a call outside the prefix fails *"no session policy allows"* (2.3, reading 8).
- **Expiry is the only end.** Credentials die at `c["Expiration"]` and at nothing else — 6.1 measured
  them surviving even the grant's revocation until that instant — so long jobs re-vend; nothing
  refreshes a bearer.
- **The maintained form of this flow is [`s3-read-write/`](../../../s3-read-write/README.md)**
  (discover → vend → demo). If you discover with `ListCallerAccessGrants` instead of naming the
  target, match `grant_scope` — never take `grants[0]`: with two grants discoverable, the lake lists
  first and the positional default silently switches buckets (verification (ix)).

## R. Revoke — when a project dies

**The grant half was first exercised 2026-08-26 (Stage 16 step 6.1), against a sacrificial grant — the
trust half stays unexercised until a real project dies** (the sacrificial grantee had no trust entry to
remove). Three timings from that run, measured, not believed: **the vend door does not close with the
delete** — a re-vend still answered at **+1 s** (minting a fresh 900 s bearer *after* the deletion) and
refused at **+19 s**, so the propagation window is under twenty seconds and more than one; and
**already-vended credentials survive revocation entirely** — forty seconds after the delete they
listed, read and **deleted** an object, dying only at their own expiry. The residual horizon is
therefore `delete + propagation + duration`, not the credentials outstanding at the delete.
One shape note: a sacrificial grant for this exercise must use a grantee holding **no standing grant**
(the run used the operator's own reserved role) — with a tenant grantee, the standing `<group>/*` grant
answers every post-delete re-vend and the refusal is unmeasurable.

The reverse of §W, in the same order it can be read — and **both halves, always**: a grant deleted with
its trust entry left behind is a half-executed §R no check reads (`SL-2` sees a live role's entry as
legitimate). Delete the grant:

```bash
aws s3control delete-access-grant --account-id "$(aws sts get-caller-identity --query Account --output text --profile awsds-infra-sandbox-1)" --access-grant-id <grant-id> --profile awsds-infra-sandbox-1
```

Then remove the pair from the trust variable and apply, and delete the `AWS_STATE.md` row. The
connection inside a deleted project dies with the project; a connection in a *living* project
whose grant was cut keeps its form and loses its reach — already-vended credentials keep working for
their remaining duration (the bearer residual, open question 14's shape; Stage 16 verification (viii)
measures the window). **The orphan reading is `SL-4`**: a grant whose `datazone_usr_role_*` grantee no
longer exists in IAM is a dead project that skipped this section — run it then, not a new design.

---

*Stage: [stage-16-sandbox-lake.md](../stages/stage-16-sandbox-lake.md) · Expected state:
[docs/AWS_STATE.md](../../AWS_STATE.md) · The governed lake: [data-governance/data/README.md](../../../terraform-live/data-governance/data/README.md)*
