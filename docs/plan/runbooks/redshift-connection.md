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
| 2 | the IAM reach — `GetCredentials`, `GetWorkgroup`, `ListTagsForResource` — in one policy on the project role and on its access role. The project role also carries AWS's `SageMakerStudioProjectUserRolePolicy` v75, which grants it `GetCredentials` and the Data API on a workgroup tagged with its project, the same to every project role under the wide tag, and `GetCredentials` on any workgroup through `sqlworkbench` (simulated 2026-10-18, 6h 5.1 and decision 8) | Terraform, the same map | per **project** on the access role alone | the connection is created and every query fails at authentication; §F says which role to read |
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
2a. **The sharing half, in SQL, and only if the schema is shared.** A table belongs to its creator
   and the theme role carries nothing at table level, so this is what makes a *shared* base readable
   (§T, measured). One statement per admitted project, which is why it sits beside the `GRANT ROLE`
   rather than in a slice:
   ```sql
   ALTER DEFAULT PRIVILEGES FOR USER "<identifier>" IN SCHEMA <theme>
     GRANT SELECT ON TABLES TO ROLE sbx_<theme>_rw;
   ```
3. **Layers 1 and 2, in Terraform.** Add the entry to `sandbox/warehouse/`'s `projects`, then
   `terraform apply` that slice and re-plan `No changes`. One map produces the tag on both objects,
   the IAM policy and its attachment, the **access role** the portal's form demands, and the `5439`
   ingress rule, so they cannot drift apart. `[P]` is never touched by `make up`, so this apply is by
   hand (`runbooks/terraform-changes.md` §2). **EC2 refuses a rule description containing `>`** — the
   permitted set is `a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*`. `validate` does not check this resource;
   `make check` and the commit gate do, through `scripts/check-sg-descriptions.py`.
3a. **Tell the project's notebooks to chain through the access role**, which is what makes the
   schema work from a space (measured 2026-10-10, §V step 4). Redshift grants to database users and
   never to an IAM role, and the space's session carries a **per-person** `RedshiftDbUser` that SMUS
   sets and nobody can change. Assuming the access role first lands the session on the **per-project**
   database user instead — the one the `GRANT ROLE` and the schema's default privilege already name —
   because **no session tag is transitive**, so the per-person value does not follow into the chain.
   A notebook that connects directly still gets a user holding nothing and still fails at the schema,
   so this is a convention with a loud failure rather than a control. In-database attribution becomes
   per project, and CloudTrail still names the person: the chained session carries the space's
   `sourceIdentity`, the data scientist's Identity Center user id, although §J's call passes none (6h
   verification xv, read 2026-10-17).
4. **The connection, in the portal**, by a project member — this repository does not author it.
   DataZone's own authorization layer refused the account's administrator `datazone list-connections`
   three times, and answers it since Sandbox's `InfrastructureAccess` role was made contributor to both
   Sandbox projects on 2026-10-15, as a group profile, so `WH-9` reads the object. *Compute → Data warehouse →
   Add compute → Connect to existing compute resources*, credential type **IAM credentials**. Three
   things the form does that no AWS page describes (measured 2026-09-21):

   - **`Access role ARN` is mandatory**, same account, while `AWS Secret` is optional beside it. Hand
     over `terraform output project_access_role_arns`. AWS's same-account procedure names no access
     role and the field's help calls it *"optional. Required when connecting to resources in a
     different AWS account"* — both wrong against the running form.
   - **The compute dropdown offers the namespace's `dev` database.** The themed schema is in the class
     container (`sandbox`), and a cross-database **write** does not work in Redshift, so the
     connection must name that database — by a database field if the form has one, otherwise through
     the JDBC URL with the `/dev` suffix replaced. Measured 2026-10-10: the Query editor lists every
     database in the namespace (`dev`, `sandbox`, `warehouse`) and the project wrote `lab.hello` from
     it; the connection object names `dev` (read 2026-10-18).
   - **There is no `lineageSync` toggle** on this path, and the connection it wrote has the sync
     **on**: the object read 2026-10-18 has `lineageSync.enabled: true` on a daily cron, and every run
     so far failed without minting a database session (6h decision 3). A run that succeeds is a
     scheduled query on the 1.44 USD/hour meter, and `WH-9` fails on it. Switching it off is an
     `UpdateConnection` by a project member.
5. **Re-run `./aws/warehouse.py --sql`** and add the register row. The database user is
   **`IAMR:<the RedshiftDbUser tag's value>`** — measured 2026-10-10: the tag is honoured and Redshift
   prefixes its value, so with the tag set to the project role's name the user is
   `IAMR:datazone_usr_role_<project>_<env>`. Attribute it rather than assuming: `select trim(u.usename),
   count(*) from sys_query_history q join pg_user u on u.usesysid = q.user_id group by 1`.

**What a correctly wired project sees in the Query editor**, and two of these lines are right rather
than broken:

| Line | Reading |
|---|---|
| `sandbox -> lab -> no data` | the three layers meeting: the schema is visible, and empty until §S's first table |
| `awsdatacatalog -> failed to fetch database` | **correct.** That mount runs as the namespace role, which holds no policy at all (5b decision 5), and `WH-1b` keeps it that way |
| a Glue database refused with *"Insufficient Lake Formation permission(s): Required Describe on \<db\>"* | **correct.** The editor enumerates every Glue database it can see; the lake's layers are not this project's to describe, and granting one is a governance act with a named requester |

**What must stay absent, whatever else is granted:** no `GRANT ALL ON DATABASE`, nothing on a schema
the project's row does not name, no `CREATE` on `public` (`PUBLIC` holds none in any of the three
databases, read 2026-09-21; 6h 1.2 revoked it in `sandbox`), and no
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

**The connection object stays.** It is DataZone's, no apply touches it, and this repository does not
author it (`EXC-17`): removing it is a portal act by a project member. Until then it names an access
role the apply destroyed, which `WH-9` reports.

---

## §T Two projects on one schema

One schema may be shared, and admitting the second is one `GRANT ROLE`. **Sharing the schema shares
nothing in it, and the baseline is worse than it reads** (measured 2026-10-10 on the first table a
project ever wrote): `sbx_<theme>_rw` carries `USAGE, CREATE ON SCHEMA` and **nothing at table
level**, and a table created by project A has a **null `relacl`** — so project B holds `CREATE`, can
write its own tables, and **cannot `SELECT` project A's at all**. Not a reduced privilege: none.

Redshift's answer is `ALTER DEFAULT PRIVILEGES`, and it is set **per creating user**, so a shared
schema owes one statement per admitted project — which is Lesson 14's shape, and `WH-14` is what
notices the one nobody wrote:

```sql
-- every FUTURE table that user creates in the schema
ALTER DEFAULT PRIVILEGES FOR USER "IAMR:<project role name>" IN SCHEMA <theme>
  GRANT SELECT ON TABLES TO ROLE sbx_<theme>_rw;
-- and each table that already exists, one by one
GRANT SELECT ON TABLE <theme>.<table> TO ROLE sbx_<theme>_rw;
```

**`SELECT` and not more, by default.** Letting project B `INSERT` into or `DROP` project A's table is
a sharing semantic nobody has asked for; read-across is what a shared base means. Widening it is
[6h](../stages/stage-06h-redshift-connection.md) decision 8's territory, with the argument written.

> **Neither `pg_default_acl` nor `relacl` is the instrument on this platform.**
> `pg_default_acl` returns zero rows after a successful `ALTER DEFAULT PRIVILEGES` — the privilege is
> in **`svv_default_privileges`** alone. And **`pg_class.relacl` is blind to a grant made to a ROLE**:
> measured 2026-10-10, two tables each carrying `sbx_lab_rw / SELECT` in
> `svv_relation_privileges` read `relacl = (none)`. The legacy PostgreSQL ACL columns hold the legacy
> ACL; Redshift's RBAC lives in the `SVV_` views and nowhere else, so reading both is not two
> independent readings — only one of them can ever see a role.

**Read what the projects actually need before writing any of it.** If *"creates freely"* means
*creates and reads its own*, none of the above is needed. It is also where layer 1's one-project limit
bites: admitting a second project to the **warehouse** needs either the wide tag or a second
workgroup, and that is a decision with a written argument, not a map entry.

---

## §F Where a failure comes from

*The project cannot see the database* is what a missing tag, a missing IAM action and a missing
`GRANT` all look like. Read them apart:

| Symptom | Layer | The reading |
|---|---|---|
| the compute is absent from the project's dropdown | 1 | `./aws/warehouse.py` `WH-7` — the tag on **both** objects against the map |
| the connection exists, every query fails to authenticate | 2 | `aws iam get-role` on the project role, **per role** (`list-roles` omits `PermissionsBoundary` by documented contract), and whether the D13 boundary admits `redshift-serverless:` at all — a boundary is a ceiling, and a grant it does not admit reaches nothing. Which door failed decides whose policy to read: the Data page calls `GetCredentials` as the access role, which holds this repository's policy alone, while a notebook calls it as the project role, which AWS's `SageMakerStudioProjectUserRolePolicy` also admits on a workgroup tagged with its project (simulated 2026-10-18, 6h 5.3), so a notebook refused there has lost the tag as well |
| it connects, the schema is invisible or read-only | 3 | `WH-12`, which needs a database session |
| JupyterLab hangs, the Data page works | the door | the warehouse's security group: group-to-group on `5439`, and the workgroup and the project must share a VPC for the JupyterLab path at all |
| `403` on a `redshift-serverless` API call from inside a space | the endpoint | `make up ENV=sandbox GROUPS=redshift`. Without it the call leaves through the proxy as a public request |
| everything times out and nothing is denied | the compute | **the workgroup may simply not exist.** It is `[E]`: `make down` destroys it, because Redshift Serverless has no pause. `make status` says so |
| the transaction aborts at commit naming a quota | 3 | working as designed. `Transaction N is aborted due to exceeding the disk space quota in schema(s): (Schema: …, Quota: …, Current Disk Usage: …)` |

---

## §J Running SQL from a notebook

**For a data scientist in a space.** `import redshift_connector, boto3` works in a new notebook on the
`Python (awsds dev-env)` kernel with nothing installed: both are declared in
`gitlab/awsds/dev-env/dev-env/python/pyproject.toml`. The driver was already arriving transitively through
`amazon-sagemaker-sql-execution`; it is named there now so a resolution change cannot remove it
silently.

**Two prerequisites, and neither is in the notebook.** The environment must be up with the Redshift
endpoint group — `make up ENV=sandbox GROUPS=redshift` — because without that endpoint `GetCredentials`
leaves through the proxy as a public request: the compute plane admits `.amazonaws.com`, so it is
answered, through the door the group exists to replace (6h 3.5). And the project must be admitted to the
warehouse: `sandbox/warehouse/`'s `projects` map, §P.

### The connection

```python
import boto3
import redshift_connector

WORKGROUP = "awsds-sandbox-warehouse"
DATABASE = "sandbox"  # the class container, NOT the `dev` the dropdown offers
REGION = "us-west-2"
PROJECT = "avhvbqn37ty7m8"  # the project id, from the portal's URL


def connect():
    """A session on the warehouse as the PROJECT's database user."""
    sts = boto3.client("sts", region_name=REGION)
    account = sts.get_caller_identity()["Account"]

    # THE CHAIN IS WHAT MAKES THE GRANTS APPLY (6h decision 8a). Connecting directly lands on a
    # database user named after YOU, created empty, holding nothing: SMUS sets a per-person
    # `RedshiftDbUser` on the space's session and it cannot be changed. The access role carries the
    # per-project one, and no session tag is transitive, so the chained session gets that instead -
    # the user the schema's role and its default privilege are written for.
    creds = sts.assume_role(
        RoleArn=f"arn:aws:iam::{account}:role/{WORKGROUP}-access-{PROJECT}",
        RoleSessionName="notebook",
        ExternalId=PROJECT,
    )["Credentials"]

    return redshift_connector.connect(
        iam=True,
        is_serverless=True,
        serverless_work_group=WORKGROUP,
        database=DATABASE,
        region=REGION,
        access_key_id=creds["AccessKeyId"],
        secret_access_key=creds["SecretAccessKey"],
        session_token=creds["SessionToken"],
    )
```

`select current_user` should answer `IAMR:datazone_usr_role_<project>_<environment>`. If it answers
`IAMR:user-<a long id>@<project>` the chain was skipped, and the next statement fails as
`permission denied for schema`.

### Submitting statements

**The driver does not autocommit.** It opens `begin transaction` before your first statement, so a
`create` or `insert` is lost without `conn.commit()`. Set `conn.autocommit = True` if you prefer
statement-at-a-time.

```python
conn = connect()

with conn.cursor() as cur:
    cur.execute(
        "create table if not exists lab.readings (ts timestamp, sensor varchar(32), v float)"
    )
    cur.execute(
        "insert into lab.readings values (%s, %s, %s)",  # paramstyle is `format`
        ("2026-10-11 12:00:00", "t-1", 21.5),
    )
conn.commit()  # without this the table is not there
```

**Reading back, into pandas:**

```python
with conn.cursor() as cur:
    cur.execute("select sensor, avg(v) as mean_v from lab.readings group by 1 order by 1")
    df = cur.fetch_dataframe()  # pandas is in the image; fetchall() gives tuples instead
df
```

**Always parameterise.** `%s` placeholders with a tuple, never an f-string around a value: the schema
holds whatever a notebook puts in it, and a quoted literal built by string formatting is how a stray
apostrophe becomes a syntax error and how an untrusted value becomes an injected statement.

**Close it, or let the context manager do it:**

```python
with connect() as conn, conn.cursor() as cur:
    cur.execute("select count(*) from lab.readings")
    print(cur.fetchone()[0])
```

### What this costs, because the meter is per query

Every statement runs on compute billed at **0.36 USD per RPU-hour** with **four base RPUs**, so
1.44 USD per query-hour — and there is a **60-second minimum charge per query**. A cell run fifty times
while debugging is fifty minimum charges. An **idle** session costs nothing (`WH-15` measures it), and an
**open transaction** is not idle: AWS bills RPUs until it ends, and the driver opens one at your first
statement, reads included. So end a cell's work with `conn.commit()` or `conn.rollback()`, or close the
connection. On 2026-10-10 `ComputeSeconds` held 4 RPU from 17:57 to 18:56Z while a notebook session was
open and no query longer than ten seconds completed (the 5b log, 2026-10-18).

`max_query_execution_time` is **120 seconds** on this workgroup, and **whether it cuts anything off is
unproven** ([the 5b log](../../log/log-stage-05b-redshift-serverless.md)). The monthly ceiling is
**10 RPU-hours with `breach_action = deactivate`**: when it is reached the workgroup refuses any query
that needs the compute until somebody raises it, while the leader node keeps answering. A statement that
reads only catalog tables (`pg_*`) runs on the leader node, and on 2026-09-20 one ran for six and a half
hours at 1.44 USD/h, past an 1800-second limit and through two minutes of a breached ceiling: end one with
`pg_terminate_backend(<pid>)`. Both values are the user's, set on 2026-09-20 after that runaway.

### Readings that will confuse you otherwise

| Reading | Why |
|---|---|
| `select current_user` comes back **padded with spaces** | it is the `name` type; `trim()` it before comparing |
| `inet_server_addr()` returns **NULL** | not implemented on Redshift Serverless; the server address is the socket's peer |
| `pg_class.relacl` is **empty** on a table a role can read | `relacl` is the legacy ACL and is **blind to role grants**; `svv_relation_privileges` is the only reader |
| `pg_default_acl` is **empty** after `ALTER DEFAULT PRIVILEGES` | the privilege is in `svv_default_privileges` alone |
| `stl_connection_log` is **refused** | to a superuser too; `sys_connection_log` is the readable one, and it has only ever held internal sessions |
| a `drop table` raises `KeyError` first in the traceback | the driver's prepared-statement cache missing, then the real error below it — read the bottom frame |

---

## §V The instruments

```bash
./aws/warehouse.py --sql                 # every WH check, both accounts; --sql adds the database half
./aws/warehouse.py awsds-infra-sandbox-1 # one account
```

**The checks that read an admitted project**, and what each answers when a connection misbehaves:

| Check | What it reads | What its failure means |
|---|---|---|
| `WH-7` | the `AmazonDataZoneProject` tag on the workgroup and the namespace, against the authored map | layer 1. A tag on one object and not the other is a drift, and the compute is missing from the project's dropdown |
| `WH-11` | the slice's policy attached to each admitted project's role, and that the role still carries `awsds-sandbox-project-boundary` | layer 2. The plan-time precondition covers the boundary when the map is edited; this covers the role being recreated afterwards |
| `WH-12` | the themed schemas, the role grants and the **user-role** grants | layer 3, including the orphan an unwiring leaves behind (§U) |
| `WH-14` | every relation in a themed schema, against the roles that can read it through a grant or a default privilege | layer 3's sharing half: a table no role can read, which on a shared schema is one project's data the others cannot see (§T) |
| `WH-9` | each admitted project's Redshift connection: its workgroup, host, access role, database and `lineageSync` | the connection names an access role this repository did not author, or the lineage sync completed a run, a scheduled query on the meter. A `note` while `list-connections` is refused or the sync is on with no run completed (`EXC-17`) |

`WH-11` reads as a `note` where nothing is admitted, because a check that is green for an absence is
green for the wrong reason (Lesson 50).

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

### The JupyterLab door, from inside a space

**Two doors reach this warehouse and they have different prerequisites**, so one of them answering
says nothing about the other. The **Data page** reaches it as an AWS service — `sqlworkbench` calling
Redshift, no network path at all — and the **JupyterLab** door is the space's own ENI opening `5439`
to the workgroup's ENI inside one VPC. The script below is for the second, and it separates three
questions a single *"it worked"* cannot:

1. does the name resolve **privately** — the endpoint, or are we leaving the VPC;
2. does `5439` open — the security group rule and the route;
3. does a session authenticate and write — `GetCredentials` (layer 2) and the `GRANT` (layer 3).

**Its prerequisite is the optional endpoint group** (measured 2026-10-10): `make up ENV=sandbox
GROUPS=redshift`. `redshift-serverless` is deliberately absent from the proxy's allow-list, so
without that endpoint there is no door to the API and no fallback — step 3 fails as a **timeout**,
which reads like a network fault and is a missing endpoint.

**`redshift_connector` is already importable in the image** (measured 2026-10-10). It is not in
`gitlab/awsds/dev-env/dev-env/python/pyproject.toml`, so it arrives **transitively** — most likely through
`sagemaker-studio-dataengineering-sessions` or `aws-glue-sessions`. The script's install step is
therefore a no-op in practice and stays only as the fallback. A transitive driver is a dependency
nobody declared: if it is wanted for good it belongs in that `pyproject.toml` by name, plus
`uv lock`, so that a resolution change cannot remove it silently (Lesson 63's shape).

```python
# Stage 6h step 3.3 - the JupyterLab door to the Sandbox warehouse.
#
# Run this in a SageMaker space, in the project that holds the Redshift connection, on the
# "Python (awsds dev-env)" kernel. Paste it into one cell; it prints a verdict per step.
#
# IT ANSWERS THREE QUESTIONS SEPARATELY, and that is the whole point. The Data page (step 3.4,
# done 2026-10-10) reaches the warehouse as an AWS SERVICE - sqlworkbench calling Redshift - and
# needs no network path at all. This door is different: the space's own ENI opening 5439 to the
# workgroup's ENI inside one VPC. A single "it worked" cannot tell the two apart, and a failure
# that says only "it did not work" names no layer. So:
#
#   1. does the name resolve PRIVATELY            - the endpoint, or we are leaving the VPC
#   2. does 5439 open                             - the security group rule and the route
#   3. does a session authenticate and write      - GetCredentials (layer 2) and the GRANT (layer 3)
#
# PREREQUISITE, measured 2026-10-10: the VPC needs the `redshift-serverless` interface endpoint,
# which is the OPTIONAL endpoint group `redshift`. Raise the environment with it:
#
#     make up ENV=sandbox GROUPS=redshift
#
# Without it GetCredentials leaves through the proxy as a public request and is answered, because
# the compute plane admits `.amazonaws.com`: the house image's six calls of 2026-10-10 took that door
# (6h 3.5). The endpoint keeps the call inside the VPC; the house image's NO_PROXY names it since
# `default-v0.5.0`.

import ipaddress
import socket
import subprocess
import sys

WORKGROUP, DATABASE, SCHEMA = "awsds-sandbox-warehouse", "sandbox", "lab"
TABLE, REGION, PORT = "hello_jupyter", "us-west-2", 5439
PROJECT = "avhvbqn37ty7m8"

results = []


def say(step, verdict, detail):
    results.append(verdict)
    print(f"[{verdict:4}] {step:34} {detail}")


# ---------------------------------------------------------------- 0. who this notebook is
try:
    import boto3

    who = boto3.client("sts", region_name=REGION).get_caller_identity()
    arn = who["Arn"]
    account = who["Account"]
    say("identity", "ok", arn.split("/")[0].split(":")[-1] + " ... " + arn.split("/")[-1][:24])
    if "datazone_usr_role" not in arn:
        say("identity", "warn", "not the project role - a space normally runs as it")
except Exception as exc:
    # THE ONLY FATAL STEP, deliberately. Everything below derives the workgroup host from the
    # account id, so without an identity there is nothing to measure rather than something to
    # report. In a notebook this prints a traceback notice instead of exiting quietly, which is
    # accepted here and nowhere else in this script.
    say("identity", "FAIL", f"{type(exc).__name__}: {exc}")
    raise SystemExit("no identity, so nothing below can be attributed")

# The host is derivable, so this step needs no API call and cannot fail for a permission reason.
host = f"{WORKGROUP}.{account}.{REGION}.redshift-serverless.amazonaws.com"

# ------------------------------------------------- 1. does the name resolve, and to a private IP
try:
    addrs = sorted({ai[4][0] for ai in socket.getaddrinfo(host, PORT, socket.AF_INET)})
    private = [a for a in addrs if ipaddress.ip_address(a).is_private]
    if not addrs:
        say("1 dns resolves", "FAIL", "no A record")
    elif private:
        say(
            "1 dns resolves",
            "ok",
            f"{', '.join(private)} - private. These are the WORKGROUP's "
            "own managed VPC endpoint ENIs, which carry the warehouse security group; the "
            "redshift-serverless API endpoint is a different address and is not what this name "
            "resolves to (measured 2026-10-10)",
        )
    else:
        say(
            "1 dns resolves",
            "FAIL",
            f"{', '.join(addrs)} - PUBLIC. The private DNS of the "
            "redshift-serverless endpoint is not answering: either the endpoint is absent "
            "(GROUPS=redshift) or its private DNS is off",
        )
except socket.gaierror as exc:
    say(
        "1 dns resolves",
        "FAIL",
        f"ENOTFOUND - {exc}. A name that does not resolve inside a "
        "compute VPC is the DNS Firewall or a missing endpoint, never a security group",
    )

# ------------------------------------------------------------------- 2. does the 5439 door open
try:
    with socket.create_connection((host, PORT), timeout=10) as s:
        peer = s.getpeername()[0]
        say(
            "2 port 5439 opens",
            "ok",
            f"{s.getsockname()[0]} -> {peer}:{PORT}, so the SG rule and the route both exist. The "
            "local address is the space's container NAT, not an ENI",
        )
except OSError as exc:
    say(
        "2 port 5439 opens",
        "FAIL",
        f"{type(exc).__name__}: {exc}. A TIMEOUT here is the "
        "security group (the warehouse admits only the project's group on 5439); a REFUSED is a "
        "listener that is not there - check the workgroup is up",
    )

# ------------------------------- 2b. does the thing on 5439 speak the Redshift wire protocol
#
# Eight bytes of PostgreSQL SSLRequest - length 8, code 80877103 - and one byte back: `S` accepts
# TLS, `N` refuses it, and anything else is not this protocol. It separates "the server dropped my
# session" from "whatever accepted the TCP never spoke Redshift", which a driver's BrokenPipe
# cannot (measured open 2026-10-10: the driver connected and broke on the first statement).
try:
    import struct

    with socket.create_connection((host, PORT), timeout=10) as s:
        s.sendall(struct.pack("!ii", 8, 80877103))
        reply = s.recv(1)
    if reply == b"S":
        say(
            "2b speaks redshift",
            "ok",
            "SSLRequest accepted - TLS required, as the workgroup is set",
        )
    elif reply == b"N":
        say(
            "2b speaks redshift",
            "warn",
            "SSLRequest refused - the protocol is there and TLS is off",
        )
    else:
        say(
            "2b speaks redshift",
            "FAIL",
            f"answered {reply!r} - whatever is on 5439 is NOT "
            "speaking the Redshift wire protocol, so a driver's BrokenPipe is this and not a session",
        )
except OSError as exc:
    say("2b speaks redshift", "FAIL", f"{type(exc).__name__}: {exc}")

# ------------------------------------------ 3. a session over that door, written and read back
#
# EVERY STEP BELOW IS GUARDED RATHER THAN FATAL, and the reason is this script's own history: a
# `raise SystemExit` in step 3 once killed step 4, which shares nothing with it and was the
# measurement that mattered. In a notebook `SystemExit` also prints a traceback notice instead of
# exiting, so it is the wrong mechanism twice over. Each step that cannot run says so and the
# summary at the end is the verdict.
#
# redshift_connector is importable in the image: the lock installs it through
# amazon-sagemaker-sql-execution (measured 2026-10-10), and gitlab/awsds/dev-env/dev-env/python/pyproject.toml
# names it since. The install below is the fallback for a kernel without it, normally a no-op.
driver = None
try:
    import redshift_connector as driver

    say("3a driver present", "ok", "redshift_connector already importable")
except ImportError:
    proc = subprocess.run(
        ["uv", "pip", "install", "--quiet", "--python", sys.executable, "redshift_connector"],
        capture_output=True,
        text=True,
    )
    if proc.returncode:
        say(
            "3a driver present",
            "FAIL",
            f"install failed: {(proc.stderr or proc.stdout).strip()[-300:]} - PyPI is on the "
            "proxy allow-list, so a failure here is the proxy variables rather than the index",
        )
    else:
        import redshift_connector as driver

        say("3a driver present", "ok", "installed into this space's kernel, not into the image")


def open_session(creds=None):
    """A database session over 5439. `creds` chains through another role; None is this one."""
    extra = {}
    if creds:
        extra = {
            "access_key_id": creds["AccessKeyId"],
            "secret_access_key": creds["SecretAccessKey"],
            "session_token": creds["SessionToken"],
        }
    return driver.connect(
        iam=True,
        is_serverless=True,
        serverless_work_group=WORKGROUP,
        database=DATABASE,
        region=REGION,
        **extra,
    )


def measure(label, conn, table):
    """Read who this session is, what it holds, then write and read the table back."""
    with conn.cursor() as cur:
        cur.execute("select current_user")
        user = cur.fetchone()[0].strip()
        per_person = user.startswith("IAMR:user-")
        say(f"{label}c the grantee", "ok", f"{user} - per {'PERSON' if per_person else 'PROJECT'}")

        # LAYER 3 IS READ BEFORE IT IS USED. This came after the write once, and the write's
        # permission error arrived as a driver traceback instead of a verdict naming the layer.
        cur.execute("select role_name from svv_user_grants where user_name = current_user")
        roles = [r[0] for r in cur.fetchall()]
        say(
            f"{label}d the roles it holds",
            "ok" if roles else "FAIL",
            str(roles)
            if roles
            else "none, so the write below fails as `permission denied for schema`. A per-person user "
            "is granted nothing by anything: SMUS passes `RedshiftDbRoles` only on the PORTAL's "
            "session, not the space's (runbook section T)",
        )

        try:
            cur.execute(f"drop table if exists {SCHEMA}.{table}")
            cur.execute(
                f"create table {SCHEMA}.{table} as "
                f"select 1 as n, current_user as by_whom, '{label}' as door"
            )
            conn.commit()
            cur.execute(f"select n, by_whom, door from {SCHEMA}.{table}")
            say(f"{label}e write and read", "ok", str(cur.fetchone()))
        except Exception as exc:
            conn.rollback()
            say(
                f"{label}e write and read",
                "FAIL",
                f"{str(getattr(exc, 'args', [exc])[0])[:180]} - with the roles empty this is "
                "layer 3, not the network",
            )
            return

        # WH-14's question, from inside: is what this session just wrote readable by a role?
        cur.execute(
            "select identity_name, privilege_type from svv_relation_privileges "
            f"where namespace_name = '{SCHEMA}' and relation_name = '{table}'"
        )
        rows = cur.fetchall()
        say(
            f"{label}f readable by a role",
            "ok" if rows else "FAIL",
            f"{rows}"
            + (
                " - a role reaches it, so a second project holding the theme role reads "
                "this table: the schema's default privilege named this owner"
                if rows
                else " - EMPTY. No default privilege names this owner, so a second project "
                "holding the theme role would see none of this table (section T)"
            ),
        )


# ---------------------------------------- 3b-3e. as the project role itself: the PER-PERSON user
if driver is None:
    say("3b direct session", "FAIL", "no driver, so the 5439 SQL path cannot be measured")
else:
    try:
        conn = open_session()
    except Exception as exc:
        conn = None
        say(
            "3b direct session",
            "FAIL",
            f"{type(exc).__name__}: {str(exc)[:300]} - an "
            "AccessDenied naming redshift-serverless:GetCredentials is layer 2 on the PROJECT "
            "role; a timeout with steps 1 and 2 green is the API endpoint, not the database",
        )
    if conn:
        say("3b direct session", "ok", f"peer {peer} - the VPC door, not the Data page's")
        measure("3", conn, TABLE)
        conn.close()

# ------------------- 4. THE SAME DOOR, THROUGH THE ACCESS ROLE, which is the per-project grantee
#
# Redshift grants to DATABASE USERS, never to an IAM role, and which database user a session
# becomes is decided by the caller's `RedshiftDbUser` tag. The space's session carries a per-person
# one, set by SMUS and unchangeable. The ACCESS ROLE carries the per-project one this repository
# set, and the project role may assume it: its trust policy names the project role with the project
# id as the external id, and layer 2 grants `sts:AssumeRole` on that ARN.
#
# WHAT MAKES THIS WORK IS THAT NO TAG IS TRANSITIVE. `transitiveTagKeys` is `None` on the space's
# assume (measured 2026-10-10), so the per-person `RedshiftDbUser` does NOT follow into a chained
# session and the access role's own tag governs there. Nothing in AWS changes for this; it is a
# convention in how a notebook connects.
#
# IT SHARES NOTHING WITH STEP 3 and runs even when step 3 failed, which is the whole point.
if driver is None:
    say("4a the chain", "FAIL", "no driver")
else:
    chained = None
    try:
        chained = boto3.client("sts", region_name=REGION).assume_role(
            RoleArn=f"arn:aws:iam::{account}:role/{WORKGROUP}-access-{PROJECT}",
            RoleSessionName="redshift-per-project",
            ExternalId=PROJECT,
        )["Credentials"]
        say("4a assumed the access role", "ok", "the per-project grantee's credentials")
    except Exception as exc:
        say(
            "4a assumed the access role",
            "FAIL",
            f"{type(exc).__name__}: {str(exc)[:220]} - an "
            "AccessDenied naming sts:AssumeRole is layer 2 on the project role; one naming the "
            "trust policy is the external id, which must equal the project id",
        )
    if chained:
        try:
            conn2 = open_session(chained)
        except Exception as exc:
            conn2 = None
            say("4b chained session", "FAIL", f"{type(exc).__name__}: {str(exc)[:300]}")
        if conn2:
            measure("4", conn2, f"{TABLE}_via_access")
            conn2.close()

print()
```

**What each failure means**, which is why the script prints a verdict per step rather than one at the
end: step 1 red is DNS — the DNS Firewall or a missing endpoint, never a security group. Step 2
timing out is the security group; refusing is a listener that is not there, so check the workgroup is
up. Step 3 red with 1 and 2 green separates again: an `AccessDenied` naming
`redshift-serverless:GetCredentials` is layer 2 on the **project role**, and a timeout is the API
endpoint rather than the database.

**`SVV_SCHEMA_QUOTA_STATE` cannot be read**, nor its `STV_` sibling: both are refused to the
namespace admin, who is a superuser (measured 2026-09-20). A schema's quota is authored in §S and
proven by breach, not by a describe.
