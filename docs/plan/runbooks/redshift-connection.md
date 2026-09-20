# Runbook — the Redshift warehouse: schemas, projects, and the connection

*The stage files are [`stage-05b`](../stages/stage-05b-redshift-serverless.md) (the warehouse) and
[`stage-06h`](../stages/stage-06h-redshift-connection.md) (the connection). The decision is
[`D40`](../decisions/D40-redshift-warehouse.md). The instrument is `./aws/warehouse.py`.
Shaped after [`sandbox-lake.md`](sandbox-lake.md), which is the same kind of recurring procedure for
the S3 connection.*

| | |
|---|---|
| **Who runs this** | the infrastructure user (`felipenoris+infrastructure_user@…`), profile `awsds-infra-sandbox-1`, account `Sandbox Account 1`, permission set `InfrastructureAccess`. The SQL halves need the namespace admin secret, which only that identity can read |
| **What it does not cover** | the governed class. A governed database gets **no project connection**: it is read through the federated catalog Lake Formation governs ([Stage 9](../stages/stage-09-deployment-targets.md) 9.5) and written by a pipeline. Reusing anything below there would put a Redshift `GRANT` beside a Lake Formation grant over governed data |

---

## §O The pieces, and which system each lives in

| # | Layer | Lives in | Grain | What its absence looks like |
|---|---|---|---|---|
| 1 | the tag `AmazonDataZoneProject=<projectId>` on the workgroup **and** the namespace | Terraform, `sandbox/warehouse/`'s `projects` map | per **workgroup** | the compute does not appear in the project's dropdown at all |
| 2 | the project role's IAM policy — `GetCredentials`, `GetWorkgroup`, `ListTagsForResource` | Terraform, the same map | per **project role** | the connection is created and every query fails at authentication |
| 3 | a database role per schema, granted to each admitted project's database user | **SQL**, nowhere else | per **schema × project** | the project connects, sees the cluster, and the schema is invisible or read-only |
| — | the door on `5439/tcp` | Terraform, the warehouse's security group | per **project's security group** | JupyterLab hangs; the Data page still works |

**Layer 3 is the requirement's grain and it is the one no plan can see.** Layers 1, 2 and the door
are code and diff; a `GRANT` is state in the namespace that Terraform never wrote. That asymmetry
is the whole of §U below.

**Layer 1 admits exactly one project, and the limit is AWS's.** The admin *"adds 1 of the following
tags"*: `AmazonDataZoneProject={{projectID}}`, which names one project, or
`for-use-with-all-datazone-projects=true`, which names every project in the account. There is no
per-project list, because it is a tag key. `sandbox/warehouse/`'s `projects` variable refuses a
second entry for that reason — a second one would silently overwrite the first project's tag and the
first project's connection would stop working with nothing in the plan to say which project lost it.

---

## §S Adding a schema

A schema is what `objectives.md` calls a base. Its name is **thematic** — chosen after the data it
will hold, with no relation to any project — so a schema name is not an authorization fact, and the
schema × project relation exists only in the `projects` map and in the `GRANT ROLE` statements.

Run every statement in the **`sandbox` database**, from the namespace admin secret (§V has the one
command that gets a session). `<theme>` is the new schema's name.

```sql
-- the owner. A non-login USER and not a role: CREATE SCHEMA ... AUTHORIZATION takes a user, and
-- Redshift answers `user "<name>" does not exist` if given a role (measured 2026-09-20). It is not
-- a person and not a project's user - ownership is singular and a schema may be shared.
CREATE USER sbx_<theme>_owner PASSWORD DISABLE NOCREATEDB NOCREATEUSER;

-- the schema, bounded. QUOTA is what makes "creates freely" bounded, a superuser sets it and no
-- project can raise it, and Redshift checks it AT COMMIT. The valid range is 2048 MB to
-- 524288000 MB (measured; neither bound is on the QUOTA page), and the DEFAULT IS UNLIMITED - a
-- schema created in a hurry is an unbounded one on a store nothing expires.
CREATE SCHEMA <theme> AUTHORIZATION sbx_<theme>_owner QUOTA 1 TB;

-- the access role. The grants live here rather than on the owner, which is what makes the
-- relation many-to-many: admitting or removing a project is then one statement against one object.
CREATE ROLE sbx_<theme>_rw;
GRANT USAGE, CREATE ON SCHEMA <theme> TO ROLE sbx_<theme>_rw;
```

Then add the row to `docs/AWS_STATE.md`'s Redshift grant register, and re-run
`./aws/warehouse.py --sql`.

**What `QUOTA` bounds is disk blocks, not logical bytes.** 1,024,000 incompressible 1 KB rows read
as **2458 MB** (measured 2026-09-20), so a 1 TB quota holds rather less than a terabyte of source
data.

**`DELETE` frees nothing until `VACUUM`; `DROP` frees at once.** The caveat — *"disk space is freed up
only when `VACUUM` runs"* — is about **rows** removed from a table that still exists, and at 4 base RPUs
vacuum boost is unavailable so it is the plain `VACUUM`. Dropping the **object** is different:
`DROP SCHEMA … CASCADE` over a 1.5 GB table took the namespace's `DataStorage` from 1,596 MB to 129 MB
in the next datapoint, with no `VACUUM` (measured 2026-09-20). Do not raise the `[E]` compute to reclaim
space after a `DROP` — check `DataStorage`'s **latest** datapoint first, and not a `Maximum` over a
window, which reports the peak.

---

## §P Wiring a project

**In this order.** Layer 3 first: a `GRANT` to a database user that does not exist yet fails loudly,
and a project that can connect before it has been granted anything produces *"the project can
connect but sees nothing"* as the expected state for a while — which is the ambiguity worth avoiding.

1. **Read the project's identifiers from the API, never from the portal's page.** An identifier read
   out of prose is a claim (Lesson 38), and it goes into four places:
   ```bash
   aws datazone list-projects --domain-identifier <domain> --profile awsds-infra-sandbox-1
   aws iam list-roles --profile awsds-infra-sandbox-1 \
     --query 'Roles[?starts_with(RoleName, `datazone_usr_role_`)].RoleName'
   aws ec2 describe-security-groups --profile awsds-infra-sandbox-1 \
     --filters 'Name=group-name,Values=datazone-*' --query 'SecurityGroups[].GroupName'
   ```
2. **Layer 3, in SQL.** `<identifier>` is the project's database user, and **its spelling is a
   reading rather than a guess**: an IAM-derived user is `IAMR:<role-name>` for a role, and this
   warehouse already carries one — `IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>`, which
   appeared without anybody creating it. Confirm with `select usename from pg_user`.
   ```sql
   CREATE USER "<identifier>" PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
   GRANT ROLE sbx_<theme>_rw TO "<identifier>";
   ```
   Take this order rather than letting the first connection auto-create the user. If the identifier
   turns out wrong the symptom is a second, auto-created user appearing beside the hand-made one —
   a clean diff in `pg_user`, and the correction is one `DROP USER`.
3. **Layers 1 and 2, in Terraform.** Add the entry to `sandbox/warehouse/`'s `projects`, then
   `terraform apply` that slice and re-plan `No changes`. One map produces the tag on both objects,
   the IAM policy and its attachment, and the `5439` ingress rule, so they cannot drift apart.
4. **The connection, in the portal**, by the project member: *Compute → Data warehouse → Add compute
   → Connect to existing compute resources*. Leave **`lineageSync` off** — it is a scheduled query on
   a 1.44 USD/hour meter.
5. **Re-run `./aws/warehouse.py --sql`** and add the register row.

**What must stay absent, whatever else is granted:** no `GRANT ALL ON DATABASE`, nothing on a schema
the project's row does not name, no `CREATE` on `public` (revoked at 5b 1.6), and no
`secretsmanager:GetSecretValue` on the admin secret — a project role that can read the admin
credential has the admin's rights and layer 3 stops meaning anything.

---

## §U Unwiring a project — the half that gets forgotten

**Removing the project from the map removes layers 1 and 2 at the next apply, and leaves layer 3
forever.** Terraform never wrote the `GRANT`, so no plan can see it, and on a **shared** schema the
revoke is the only thing that distinguishes a project that left from one that never came.

```sql
REVOKE ROLE sbx_<theme>_rw FROM "<identifier>";
-- and only if the project is leaving the warehouse entirely:
DROP USER "<identifier>";
```

`WH-12` is what finds a role membership nothing declares; this section is what prevents it.

---

## §T Two projects on one schema

One schema may be shared, and admitting the second is one `GRANT ROLE`. **What sharing does not
give away is ownership**: a table belongs to the user that created it, so project B holding the
schema's role can `SELECT` and `INSERT` in the schema but is not automatically able to `ALTER` or
`DROP` project A's tables. Redshift's answer is `ALTER DEFAULT PRIVILEGES`, which is set **per
granting user**, so a shared schema needs one statement per contributing project — per pair.

**Read what the projects actually need before writing any of it.** If *"creates freely"* means
*creates and reads its own*, nothing more is needed. It is also where layer 1's one-project limit
bites: admitting a second project to the **warehouse** needs either the wide tag or a second
workgroup, and that is a decision with a written argument, not a map entry.

---

## §F Where a failure comes from

*The project cannot see the database* is what a missing tag, a missing IAM action and a missing
`GRANT` all look like. Read them apart:

| Symptom | Layer | The reading |
|---|---|---|
| the compute is absent from the project's dropdown | 1 | `./aws/warehouse.py` `WH-7` — the tag on **both** objects against the map |
| the connection exists, every query fails to authenticate | 2 | `aws iam get-role` on the project role, **per role** (`list-roles` omits `PermissionsBoundary` by documented contract), and whether the D13 boundary admits `redshift-serverless:` at all — a boundary is a ceiling, and a grant it does not admit reaches nothing |
| it connects, the schema is invisible or read-only | 3 | `WH-12`, which needs a database session |
| JupyterLab hangs, the Data page works | the door | the warehouse's security group: group-to-group on `5439`, and the workgroup and the project must share a VPC for the JupyterLab path at all |
| `403` on a `redshift-serverless` API call from inside a space | the endpoint | `make up ENV=sandbox GROUPS=redshift`. Without it the call leaves through the proxy as a public request |
| everything times out and nothing is denied | the compute | **the workgroup may simply not exist.** It is `[E]`: `make down` destroys it, because Redshift Serverless has no pause. `make status` says so |
| the transaction aborts at commit naming a quota | 3 | working as designed. `Transaction N is aborted due to exceeding the disk space quota in schema(s): (Schema: …, Quota: …, Current Disk Usage: …)` |

---

## §V The instruments

```bash
./aws/warehouse.py --sql                 # WH-1..WH-12, both accounts; --sql adds the database half
./aws/warehouse.py awsds-infra-sandbox-1 # one account
```

**A session for the SQL above**, from a laptop, with no network path into the VPC — the Data API
reaches the database with an IAM identity and the admin secret alone:

```bash
aws redshift-data execute-statement --workgroup-name awsds-sandbox-warehouse \
  --database sandbox --secret-arn "$(aws redshift-serverless get-namespace \
  --namespace-name awsds-sandbox-warehouse --query namespace.adminPasswordSecretArn --output text)" \
  --sql 'select current_user'
```

then `aws redshift-data describe-statement --id <Id>` and `get-statement-result --id <Id>`. **There
is no waiter**: the API is asynchronous and a poll without a delay reports an empty result for a
warehouse that is answering perfectly.

**That convenience is also a control question.** `redshift-data:ExecuteStatement` needs no VPC, no
security group and no connection, which is why `identity/sso` denies the whole family — and
`redshift-serverless:GetCredentials` with it — to `DataScientistAccess`: a persona holding it has a
query path from anywhere.

**`SVV_SCHEMA_QUOTA_STATE` cannot be read**, nor its `STV_` sibling: both are refused to the
namespace admin, who is a superuser (measured 2026-09-20). A schema's quota is authored in §S and
proven by breach, not by a describe.
