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
   permitted set is `a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*` and the apply is the only validator.
4. **The connection, in the portal**, by the project member — it cannot be done any other way:
   `datazone list-connections` is refused to the account's administrator by **DataZone's own**
   authorization layer, because that identity is not a project member. *Compute → Data warehouse →
   Add compute → Connect to existing compute resources*, credential type **IAM credentials**. Three
   things the form does that no AWS page describes (measured 2026-09-21):

   - **`Access role ARN` is mandatory**, same account, while `AWS Secret` is optional beside it. Hand
     over `terraform output project_access_role_arns`. AWS's same-account procedure names no access
     role and the field's help calls it *"optional. Required when connecting to resources in a
     different AWS account"* — both wrong against the running form.
   - **The compute dropdown offers the namespace's `dev` database.** The themed schema is in the class
     container (`sandbox`), and a cross-database **write** does not work in Redshift, so the
     connection must name that database — by a database field if the form has one, otherwise through
     the JDBC URL with the `/dev` suffix replaced.
   - **There is no `lineageSync` toggle** on this path, so the scheduled query on the 1.44 USD/hour
     meter cannot be turned on from the portal. It is reachable only through the API.
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

> **`pg_default_acl` is EMPTY on this platform and is not the instrument.** It returns zero rows
> after a successful `ALTER DEFAULT PRIVILEGES`; the privilege is in **`svv_default_privileges`**,
> which carries schema, owner, grantee and privilege. The mirror of the schema-ACL trap in §S, where
> `nspacl` is the authority and the `SVV_` view shows only the RBAC half.

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
| the connection exists, every query fails to authenticate | 2 | `aws iam get-role` on the project role, **per role** (`list-roles` omits `PermissionsBoundary` by documented contract), and whether the D13 boundary admits `redshift-serverless:` at all — a boundary is a ceiling, and a grant it does not admit reaches nothing |
| it connects, the schema is invisible or read-only | 3 | `WH-12`, which needs a database session |
| JupyterLab hangs, the Data page works | the door | the warehouse's security group: group-to-group on `5439`, and the workgroup and the project must share a VPC for the JupyterLab path at all |
| `403` on a `redshift-serverless` API call from inside a space | the endpoint | `make up ENV=sandbox GROUPS=redshift`. Without it the call leaves through the proxy as a public request |
| everything times out and nothing is denied | the compute | **the workgroup may simply not exist.** It is `[E]`: `make down` destroys it, because Redshift Serverless has no pause. `make status` says so |
| the transaction aborts at commit naming a quota | 3 | working as designed. `Transaction N is aborted due to exceeding the disk space quota in schema(s): (Schema: …, Quota: …, Current Disk Usage: …)` |

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
`images/dev-env/python/pyproject.toml`, so it arrives **transitively** — most likely through
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
# Without it there is no door to the API and no fallback: `redshift-serverless` is deliberately
# absent from the proxy's allow-list, so step 3 fails at GetCredentials with a timeout rather than
# with a refusal - which looks like a network fault and is a missing endpoint (Lesson 42).

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
        say("1 dns resolves", "ok", f"{', '.join(private)} - private. These are the WORKGROUP's "
            "own managed VPC endpoint ENIs, which carry the warehouse security group; the "
            "redshift-serverless API endpoint is a different address and is not what this name "
            "resolves to (measured 2026-10-10)")
    else:
        say("1 dns resolves", "FAIL", f"{', '.join(addrs)} - PUBLIC. The private DNS of the "
            "redshift-serverless endpoint is not answering: either the endpoint is absent "
            "(GROUPS=redshift) or its private DNS is off")
except socket.gaierror as exc:
    say("1 dns resolves", "FAIL", f"ENOTFOUND - {exc}. A name that does not resolve inside a "
        "compute VPC is the DNS Firewall or a missing endpoint, never a security group")

# ------------------------------------------------------------------- 2. does the 5439 door open
try:
    with socket.create_connection((host, PORT), timeout=10) as s:
        peer = s.getpeername()[0]
        say("2 port 5439 opens", "ok",
            f"{s.getsockname()[0]} -> {peer}:{PORT}, so the SG rule and the route both exist. The "
            "local address is the space's container NAT, not an ENI")
except OSError as exc:
    say("2 port 5439 opens", "FAIL", f"{type(exc).__name__}: {exc}. A TIMEOUT here is the "
        "security group (the warehouse admits only the project's group on 5439); a REFUSED is a "
        "listener that is not there - check the workgroup is up")

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
        say("2b speaks redshift", "ok", "SSLRequest accepted - TLS required, as the workgroup is set")
    elif reply == b"N":
        say("2b speaks redshift", "warn", "SSLRequest refused - the protocol is there and TLS is off")
    else:
        say("2b speaks redshift", "FAIL", f"answered {reply!r} - whatever is on 5439 is NOT "
            "speaking the Redshift wire protocol, so a driver's BrokenPipe is this and not a session")
except OSError as exc:
    say("2b speaks redshift", "FAIL", f"{type(exc).__name__}: {exc}")

# ------------------------------------------ 3. a session over that door, written and read back
#
# redshift_connector IS importable in the image, transitively - it is absent from
# images/dev-env/python/pyproject.toml and arrives through one of the SageMaker packages (measured
# 2026-10-10). The install below is the fallback and is normally a no-op. A transitive driver is a
# dependency nobody declared: if it is wanted, it belongs in that pyproject by name plus `uv lock`.
try:
    import redshift_connector  # noqa: F401
    say("3a driver present", "ok", "redshift_connector already importable")
except ImportError:
    proc = subprocess.run(
        ["uv", "pip", "install", "--quiet", "--python", sys.executable, "redshift_connector"],
        capture_output=True, text=True,
    )
    if proc.returncode:
        say("3a driver present", "FAIL",
            f"install failed: {(proc.stderr or proc.stdout).strip()[-300:]} - PyPI is on the "
            "proxy allow-list, so a failure here is the proxy variables rather than the index")
        raise SystemExit("no driver, so the 5439 SQL path cannot be measured")
    import redshift_connector  # noqa: F811
    say("3a driver present", "ok", "installed into this space's kernel, not into the image")

try:
    conn = redshift_connector.connect(
        iam=True,
        is_serverless=True,
        serverless_work_group=WORKGROUP,
        database=DATABASE,
        region=REGION,
    )
except Exception as exc:
    say("3b session", "FAIL", f"{type(exc).__name__}: {str(exc)[:400]}")
    raise SystemExit(
        "GetCredentials or the connect failed. Read the wording: an AccessDenied naming "
        "redshift-serverless:GetCredentials is layer 2 on the PROJECT role; a timeout with step 1 "
        "and 2 green is the API endpoint, not the database"
    )

with conn.cursor() as cur:
    # inet_server_addr() returns NULL on Redshift Serverless (measured 2026-10-11), so the address
    # that identifies this door is the SOCKET's peer from step 2, not anything the server reports.
    cur.execute("select current_user, current_database()")
    user, db = cur.fetchone()
    say("3b session", "ok", f"as {user} on {db}")
    say("3b door is the VPC one", "ok" if ipaddress.ip_address(peer).is_private else "FAIL",
        f"peer {peer} - a private address here is what separates this door from the Data page's, "
        "which reaches the warehouse as an AWS service and has no VPC path at all")

    # THE DATABASE USER IS PER PERSON ON THIS DOOR, and that is the finding this script exists for.
    # `IAMR:user-<Identity Center user id>@<project id>` is auto-created at first connect and holds
    # NOTHING. The Data page's door resolves to `IAMR:<the project role's name>` instead, through
    # the access role's RedshiftDbUser tag - so a GRANT made for one door does not serve the other.
    if user.startswith("IAMR:user-"):
        say("3b grantee is per PERSON", "warn",
            "this door mints a user per person, not per project. If 3c fails on permission, that "
            "user holds no role yet - see the runbook on RedshiftDbRoles")

    # LAYER 3 IS READ BEFORE IT IS USED. This came after the write once and the write's permission
    # error arrived as a driver traceback instead of a verdict naming the layer - which is the one
    # thing this script exists to avoid (2026-10-11).
    cur.execute("select role_name from svv_user_grants where user_name = current_user")
    roles = [r[0] for r in cur.fetchall()]
    if roles:
        say("3c the roles this session holds", "ok", str(roles))
    else:
        say("3c the roles this session holds", "FAIL",
            "none. This user holds no database role, so the write below will fail as `permission "
            "denied for schema`. On this door the user is per person and SMUS passes "
            "`RedshiftDbRoles=datazone_env_<environmentId>` as a SESSION tag - if that role does "
            "not exist in the database it is ignored SILENTLY, and if the user already existed "
            "before it did, the mapping does not apply retroactively (runbook section T)")

    # The write, into its OWN table, so the two doors' objects stay distinguishable.
    try:
        cur.execute(f"drop table if exists {SCHEMA}.{TABLE}")
        cur.execute(
            f"create table {SCHEMA}.{TABLE} as "
            f"select 1 as n, 'written over 5439 from jupyterlab' as note, current_user as by_whom"
        )
        conn.commit()
        cur.execute(f"select n, note, by_whom from {SCHEMA}.{TABLE}")
        say("3d write and read", "ok", str(cur.fetchone()))
    except Exception as exc:
        conn.rollback()
        msg = str(getattr(exc, "args", [exc])[0])
        say("3d write and read", "FAIL", f"{msg[:200]} - with 3c empty this is layer 3 and not "
            "the network; with 3c holding a role it is the GRANT's contents")
        raise SystemExit("no write, so 3e has nothing to judge")

    # WH-14's question, asked from inside: is what this session just wrote readable by the role?
    cur.execute(
        "select identity_name, privilege_type from svv_relation_privileges "
        f"where namespace_name = '{SCHEMA}' and relation_name = '{TABLE}'"
    )
    rows = cur.fetchall()
    say("3e readable by the role", "ok" if rows else "FAIL",
        f"{rows} - empty means no default privilege names THIS owner, so a second project holding "
        "the theme role would see none of this table (runbook section T, EXC-15)")

conn.close()

# ------------------- 4. THE SAME DOOR, THROUGH THE ACCESS ROLE, which is the per-project grantee
#
# Redshift grants to DATABASE USERS, never to an IAM role, and which database user a session becomes
# is decided by the caller's `RedshiftDbUser` tag. The space's session carries a per-person one, set
# by SMUS and unchangeable. The ACCESS ROLE carries the per-project one this repository set - and the
# project role may assume it (its trust policy names the project role with the project id as the
# external id; layer 2 grants `sts:AssumeRole` on it).
#
# WHAT MAKES THIS WORK IS THAT NO TAG IS TRANSITIVE. `transitiveTagKeys` is `None` on the space's
# assume (measured 2026-10-11), so the per-person `RedshiftDbUser` does NOT follow into the chained
# session, and the access role's own tag governs there. The database user becomes
# `IAMR:<the project role's name>` - the one that already holds the theme role and is already named by
# the schema's default privilege.
#
# Nothing in AWS changes for this. It is a convention in how a notebook connects.
try:
    sts = boto3.client("sts", region_name=REGION)
    chained = sts.assume_role(
        RoleArn=f"arn:aws:iam::{account}:role/{WORKGROUP}-access-{PROJECT}",
        RoleSessionName="redshift-per-project",
        ExternalId=PROJECT,
    )["Credentials"]
    say("4a assumed the access role", "ok", "the per-project grantee's credentials")
except Exception as exc:
    say("4a assumed the access role", "FAIL", f"{type(exc).__name__}: {str(exc)[:220]} - an "
        "AccessDenied naming sts:AssumeRole is layer 2 on the project role; one naming the trust "
        "policy is the external id, which must equal the project id")
    raise SystemExit("no chained session, so step 4 cannot be measured")

conn2 = redshift_connector.connect(
    iam=True,
    is_serverless=True,
    serverless_work_group=WORKGROUP,
    database=DATABASE,
    region=REGION,
    access_key_id=chained["AccessKeyId"],
    secret_access_key=chained["SecretAccessKey"],
    session_token=chained["SessionToken"],
)
with conn2.cursor() as cur:
    cur.execute("select current_user")
    user2 = cur.fetchone()[0]
    per_project = not user2.startswith("IAMR:user-")
    say("4b the grantee", "ok" if per_project else "FAIL",
        f"{user2} - per PROJECT" if per_project else
        f"{user2} - still per person, so the chained session inherited the tag after all")

    cur.execute("select role_name from svv_user_grants where user_name = current_user")
    roles2 = [r[0] for r in cur.fetchall()]
    say("4c roles", "ok" if roles2 else "FAIL",
        str(roles2) if roles2 else "none - the per-project user holds no role either, so the "
        "chain reached a different user than the Data page's")

    chained_table = f"{TABLE}_via_access"
    try:
        cur.execute(f"drop table if exists {SCHEMA}.{chained_table}")
        cur.execute(
            f"create table {SCHEMA}.{chained_table} as select 1 as n, current_user as by_whom"
        )
        conn2.commit()
    except Exception as exc:
        conn2.rollback()
        say("4d write", "FAIL", f"{str(getattr(exc, 'args', [exc])[0])[:200]}")
        raise SystemExit("no write through the chain, so 4e has nothing to judge")
    say("4d write", "ok", f"{SCHEMA}.{chained_table} created by this session")

    cur.execute(
        "select identity_name, privilege_type from svv_relation_privileges "
        f"where namespace_name = '{SCHEMA}' and relation_name = '{chained_table}'"
    )
    rows = cur.fetchall()
    say("4e the default privilege fires", "ok" if rows else "FAIL",
        f"{rows} - non-empty means the schema's default privilege named THIS owner, so read-across "
        "works without one statement per person")
conn2.close()

print()
print(f"{results.count('ok')} ok, {results.count('warn')} warn, {results.count('FAIL')} FAIL")
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
