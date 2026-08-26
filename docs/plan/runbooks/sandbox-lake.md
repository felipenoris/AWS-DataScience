# Runbook — the sandbox lake

| | |
|---|---|
| **Scope** | The fourth Sandbox bucket, `awsds-sandbox-lake` — permanent per-SSO-group artifacts — and every recurring act its life needs: the prefix contract, wiring a SageMaker Unified Studio project to a prefix (the portal's **S3 connection**), the two read/write tests, and revocation when a project dies. The build itself is [Stage 16](../stages/stage-16-sandbox-lake.md)'s, once; this file is what runs *per project*, forever |
| **Operator** | §W and §R: the **infrastructure user** — account **Sandbox**, permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`; every write is authorized per occurrence. §T's in-project half: a **data-scientist persona, in the portal**, no CLI. §T's out-of-project half: a Sandbox SSO user through [`s3-read-write/`](../../../s3-read-write/README.md), profile `awsds-scientist-sandbox`, on the VPN |
| **The two rules** | **This is not the governed lake**: nothing here is catalogued, LF-tagged or granted through Lake Formation — the governed lake's questions belong to [`data-governance/data/README.md`](../../../terraform-live/data-governance/data/README.md), and moving data between the two is a deliberate act (§G), never a mount. **A project's access is a pair of registered objects** — a grant and a trust entry — so it dies with the project or §R is owed; an orphaned grant is `SL-4`'s finding and the orphaned trust half surfaces under `SL-2`, neither of them housekeeping |
| **The picture around it** | Why the bucket exists and what its existence costs: the stage file's own argument. What is *expected* on the instance at any moment: [`docs/AWS_STATE.md`](../../AWS_STATE.md)'s lake-bucket and vending rows. The instrument: `./aws/sandboxlake.py` (`SL-1`–`SL-5`), the first thing to run when anything here surprises |
| **Written** | 2026-08-26, **at Stage 16 planning — every command below is a design read from AWS's documentation (the 2026-08-26 rows of [`docs/REFERENCES.md`](../../REFERENCES.md)) and NONE has been exercised.** Stage 16 passes 4-6 are what turn each section from design into procedure; the markers below fall as the dates arrive (Lesson 37) |

---

## D. What it is — and what it is not

One `[P]` bucket in Sandbox, `awsds-sandbox-lake` (`sandbox/lake/`), SSE-KMS under
`alias/awsds-sandbox-data` (Stage 16 decision 1(a), the recommendation), versioned, TLS-only, BPA on,
**no expiry on current objects** — the one S3
surface in this estate where artifacts are *meant* to outlive both the session and the project. It is not
the governed lake (no catalog object, no LF-Tag — D13's non-registered class), not the derived zone
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

**Never yet exercised — Stage 16 step 4.1/4.2 is this section's first run.**

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

3. **Add the pair to the access-role trust** — append (role ARN, project id) to `sandbox/lake/`'s
   project variable and `terraform apply` (Recipe A); the entry expands to the three documented
   project-side statements (`sts:ExternalId` = the project id, `sts:SetSourceIdentity`,
   `sts:TagSession` — Stage 16 step 2.1). The trust is enumerated by design; a wildcard there is
   `SL-2`'s finding.

4. **Create the connection, in the portal** — observed as the Data area's *Add S3 location*, documented
   as **Connections → Create connection → Amazon S3** (whether they are one form is Stage 16 step 4.2's
   reading): **Name**, URI `s3://awsds-sandbox-lake/<sso-group>/`, Region `us-west-2`, and the access
   role picked from the dropdown (`awsds-sandbox-lake-access`). Any field the form demands beyond those
   four is recorded (Lesson 39).

5. **Register the pair** in `docs/AWS_STATE.md` (the vending discipline: a grant nobody registered reads
   as drift), and re-run `./aws/sandboxlake.py` — the only acceptable ending is `SL-1`–`SL-5` pass.

## T. The two tests — each proving a different claim

**Never yet exercised — Stage 16 steps 4.4 and 5.1 are this section's first runs.**

- **In the project** (proves the *wiring*): from JupyterLab, write a file through the mounted location,
  list, read it back. Then the two refusals that make the pass meaningful: list **above** the prefix,
  and repeat the read from a project holding no grant. Working-and-refusing together is the pass; either
  alone is not (Lesson 13).
- **From the laptop, no project in the path** (proves the *persona* path): on the VPN, as the group's SSO
  user, the `s3-read-write` sequence unchanged — discover (`ListCallerAccessGrants`), vend
  (`GetDataAccess` on `s3://awsds-sandbox-lake/<sso-group>/*`), write, list, read back. The vended
  session's ARN names **the access role** (the project-path vend names the project role — the difference
  is the diagnostic if a vend surprises). The persona's *direct* `aws s3` call on the bucket must still
  refuse — vended-only is the design, and this is its negative control.

## R. Revoke — when a project dies

**Never yet exercised — Stage 16 step 6.1 is this section's first run, against a sacrificial grant.**

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
