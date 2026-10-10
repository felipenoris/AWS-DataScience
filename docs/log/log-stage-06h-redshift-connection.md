# Log — Stage 6h — The Redshift connection in SageMaker Unified Studio

*The stage file is [`docs/plan/stages/stage-06h-redshift-connection.md`](../plan/stages/stage-06h-redshift-connection.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

*Identifiers are redacted as [`INDEX.md`](INDEX.md) requires: an account id becomes the account's name
in angle brackets, an e-mail address inside an ARN becomes that user's role. Everything else in a pasted
output stays verbatim. All times UTC.*

---

## 2026-09-20 — layer 3 exists, layers 1 and 2 are code with nobody in them, and the portal half is owed

*Written by Claude in the sitting that ran it, at the user's instruction to execute the stage and log
each step. Every reading is Claude's own, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`,
permission set `InfrastructureAccess`). The stage's pass 2 and most of step 5 are the user's, in the
portal and from a space, and are not done.*

### 0.1 — the project's identifiers

One project exists in Sandbox, created 2026-08-22 at [Stage 6a](../plan/stages/stage-06a-unified-studio.md)
pass 3. Its two service-minted names, read from the API:

| What | Value |
|---|---|
| project role | `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` |
| the project's own security group | `datazone-avhvbqn37ty7m8-dev` (`sg-0fee1c059b82e3562`) |
| project id | `avhvbqn37ty7m8` — the first segment of both names |

`sandbox/warehouse/`'s `projects` map takes exactly these two names per entry and **validates that the
project segment of each equals the map key**, because a mismatch would put one project's role under
another's tag — the two halves of layer 1 and layer 2 pointing at different projects, which is the
whole failure one map exists to prevent.

### The finding that changes the stage: layer 1 admits ONE project

AWS, *Gaining access to Amazon Redshift resources*, read 2026-09-20: the admin **"adds 1 of the
following tags to the Amazon Redshift cluster or workgroup and its namespace"** — either
`AmazonDataZoneProject={{projectID}}`, *"to allow only a specific … project to access it"*, or
`for-use-with-all-datazone-projects=true`, *"to allow all Amazon SageMaker Unified Studio projects in
this account to access it"*.

**There is no per-project list, because `AmazonDataZoneProject` is a tag key and a key holds one
value** — on the workgroup and on the namespace alike. So this stage's own step 2.1, *"one tag per
admitted project"*, is not expressible, and the requirement that **one sandbox schema may be shared by
several projects** meets that wall at the second project rather than the first.

**What is not affected**: layer 2 is one IAM policy per project role, and layer 3 is a database role
per schema granted per project. Both are genuinely per project and many-to-many. **Only the
compute-admission gate is single-valued.**

`sandbox/warehouse/`'s `projects` variable therefore refuses a second entry, at plan time, with the
reason in the error message. The alternative it prevents is unreadable: a second entry would silently
overwrite the first project's tag, the first project's connection would stop working, and nothing in
the plan output would say which project lost its access. **A new decision is owed** — 6h decision 8,
below.

### 0.2 — the project role and the D13 boundary

`get-role` per role, never `list-roles` (which omits `PermissionsBoundary` by documented contract).
`datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` carries `awsds-sandbox-project-boundary`, so INT-15
holds. **Whether that boundary admits `redshift-serverless:` at all is not yet measured** — the
attachment's own precondition checks that the boundary is *present*, which is a different question
from whether it *admits* the action, and the answer arrives when a query is attempted from the project
(the stage's pass 2). If it has to be amended, `terraform-modules/sagemaker-prereqs/boundary.tf` is the
single source and the amendment is a module version bump under Recipe B.

### 0.3 — the credential type, and the reason the decision is not taken here

The stage's callout was confirmed against the page: AWS's **same-account** procedure names only one
credential path — *"The admin then must send you a username and password for a database user that has
access to the compute resources."* The `RedshiftDbUser={{Username}}` tag and the IAM-credentials path
appear **only under the cross-account heading**, on an **access role** a same-account connection does
not have. The two pages do not meet.

**One half of the question did get an answer, and it was not on the page.** `pg_user` on this namespace
already carries **`IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>`**, with **`usesuper = true`** —
an IAM-derived database user nobody created. So the spelling for a role-derived user in this account is
**`IAMR:<role name>`**, which is what 1.4's `CREATE USER` will use for the project role, and the fact
that the admin role's derived user is a **superuser** is worth carrying on its own: an
`InfrastructureAccess` session that reaches the database by IAM is a superuser session, and what bounds
it is the SSO policy rather than anything inside Redshift.

**The decision stays open** because it is the portal that answers it: which of the three types the form
actually offers for a same-account compute is a reading nobody here can take without a portal session.
Both preparations are in place either way — layer 2 grants `GetCredentials`, and a purpose-made secret
is one object to create if the form insists on a password.

### 0.4 — unread

Whether anything at the domain level stops a project member creating a connection of their own. It
needs the portal, and [6f](../plan/stages/stage-06f-data-governance.md) step 1's answer for
`ADD_TO_PROJECT_MEMBER_POOL` (open to every user) is the reason the question matters: if any member may
add a compute connection, layer 1's tag is the only thing between a member and this warehouse.

### 1.1-1.5 — layer 3, in SQL, and two shapes the plan had wrong

**The Data API is the session, and it needs no network path.** Measured from a laptop outside every
VPC: `redshift-data execute-statement` with `--workgroup-name` and the namespace's admin secret runs
SQL on this warehouse with nothing but an IAM identity. So every step below ran without a space, a
connection or a VPN, and that is also why `identity/sso` now denies the whole `redshift-data:` family
to `DataScientistAccess` ([5b](../plan/stages/stage-05b-redshift-serverless.md) 2.3).

| Step | Statement | Result |
|---|---|---|
| 1.1 | `CREATE DATABASE sandbox` | the class container |
| 1.2 | `REVOKE CREATE ON SCHEMA public FROM PUBLIC` + `REVOKE ALL ON DATABASE sandbox FROM PUBLIC` | `public`'s ACL went `=UC/rdsdb` → `=U/rdsdb` |
| 1.3 | `CREATE USER sbx_lab_owner PASSWORD DISABLE NOCREATEDB NOCREATEUSER`, then `CREATE SCHEMA lab AUTHORIZATION sbx_lab_owner QUOTA 1 TB` | the first themed schema |
| 1.5 | `CREATE ROLE sbx_lab_rw` + `GRANT USAGE, CREATE ON SCHEMA lab TO ROLE sbx_lab_rw` | the access role, holding nobody |

**`AUTHORIZATION` takes a USER, not a role.** The first attempt was
`CREATE SCHEMA lab AUTHORIZATION sbx_lab_owner QUOTA 1 TB` with `sbx_lab_owner` created as a **role**,
and Redshift answered `ERROR: user "sbx_lab_owner" does not exist`. Redshift roles cannot own a schema.
So the owner is a **non-login database user** created for the purpose — still not a person and not a
project — and the grants stay on a role, which is what keeps the relation many-to-many. The stage's
1.3 said *"a non-login role this stage creates for the purpose"*; the word was wrong and the intent was
right.

**A schema quota has a floor, and neither bound is on the QUOTA page.**
`ERROR: Schema quota must be between 2048 and 524288000 MB` — so **2 GB minimum, 500 TB maximum**, and
a quota below 2 GB cannot be written at all.

**The name `lab` is this stage's exercise schema, not a business theme.** The requirement is that a
schema is named after the data it will hold; nothing holds data yet, so naming a theme would be
inventing a business fact. The first real theme is the user's to name, and
[`runbooks/redshift-connection.md`](../plan/runbooks/redshift-connection.md) §S is the procedure.

**1.6 — the register rows are in [`docs/AWS_STATE.md`](../AWS_STATE.md)**, in the Redshift grant
register that until today had none. Two rows for `lab`, plus the two database users nobody created.

### The quota refuses at commit, and this is its first exercise anywhere in this estate

Part of 5.2a, done without the project because it needed only a throwaway schema. `quotatest` at the
**2 GB floor**, filled with incompressible rows (1 KB of concatenated `md5(random())` per row,
`ENCODE RAW`, doubled repeatedly):

```
ERROR: Transaction 6250 is aborted due to exceeding the disk space quota in schema(s):
(Schema: quotatest, Quota: 2048, Current Disk Usage: 2458).
Free up disk space or request increased quota for the schema(s).
```

**Three readings in that one message.** The refusal is **at commit**, as documented. The usage
**exceeded the quota inside the transaction before the abort** — 2458 against 2048 — so the quota is
not a hard write barrier, it is a commit-time check. And **1,024,000 rows of 1 KB read as 2458 MB**, so
a quota bounds **disk blocks, not logical bytes**: a 1 TB quota holds rather less than a terabyte of
source data.

An earlier attempt with compressible content (`repeat('x',1000)`) reached **4.2 million rows without
breaching anything** — Redshift's compression defeated it entirely. Worth recording because it is the
shape of a quota test that reports success and proves nothing.

The throwaway schema was dropped. **What is still owed on 5.2a is the half that needs the project**:
that `ALTER SCHEMA … QUOTA` fails for a non-superuser. It is documented as superuser-only and was not
attempted, because the only non-superuser database user here is the schema owner and no credential for
it exists.

### 2.1-2.3 — the gate layers are code, and admit nobody

`sandbox/warehouse/` carries the `projects` map, and it is **empty**. That is deliberate and it is what
makes the stage's verification (vi) answerable at all: the *before* is a measurement rather than an
assumption. With the map empty, `./aws/warehouse.py` reads —

- no `AmazonDataZoneProject` tag on the workgroup or the namespace, and no
  `for-use-with-all-datazone-projects` on either;
- no IAM policy attached to the project role;
- **no ingress rule at all** on the warehouse's security group, so nothing in the VPC can open a
  connection on `5439`.

**Filling it in is one edit and one apply**, and the procedure is
[`runbooks/redshift-connection.md`](../plan/runbooks/redshift-connection.md) §P. It was **not** done in
this sitting, for one reason: step 3.2's connection is the user's act in the portal, and wiring the
gates without it would leave the estate with a project admitted to a warehouse it cannot reach, which
is the state hardest to read later.

### What this stage still owes, and to whom

| Step | What | Why it is not done |
|---|---|---|
| 2.1-2.3 | the project in the map, applied | ordered after the portal decision, so the before/after stays readable |
| 3.1, 3.2 | the connection, and every field the portal asks for | **the portal**, and decision 1 wants the portal path measured once |
| 3.3, 3.4 | the first write from JupyterLab, and the same query from the Data page | **a space**, and the two doors are read apart on purpose |
| 3.5, 3.6 | CloudTrail attribution, and the audit groups for that session | after 3.3; the audit half also waits on the export question 5b 6.1 left open |
| 5.1 | a project outside the map cannot use the compute | needs a second project |
| 5.2, 5.2a, 5.2b | the schema negatives, the quota from inside the project, two projects on one schema | need the project's own session |
| 5.3 | the project cannot administer the warehouse | the policy grants none of it, but that is an omission and not a measurement |
| 5.4 | the persona cannot mint a database session | needs the `awsds-scientist` SSO session |
| 6.4 | keep or drop `lab` | the user's, and it has no hourly meter |
| 6.2 | `WH-9`, `WH-10`, `WH-11` in `./aws/warehouse.py` | **nothing to read until a connection exists.** `WH-7` already compares the tag pair against the authored map on both objects, which is `WH-10`'s substance; `WH-11`'s — the project role's policy and its D13 boundary — is enforced at plan time by the attachment's own precondition in `sandbox/warehouse/iam.tf`, and the runtime form is worth adding when there is a project to read it for. `WH-12` is written and green. Writing checks now that can only report *"no project admitted"* would add three rows that say what `WH-7` already says |

### Decisions

| # | State |
|---|---|
| 1 | **open** — portal or Terraform for the connection. The recommendation stands: the portal first, then the Terraform shape written against the object it produced |
| 2 | **open, and better informed** — the credential type. IAM credentials remain the recommendation, the same-account procedure still names only a username and password, and the `IAMR:<role>` spelling is now measured rather than assumed |
| 3 | **taken: `lineageSync` off.** It is a scheduled query on the estate's most expensive meter and nothing has asked for the lineage nodes |
| 4 | **taken: it stands.** The persona gets the read side and no credential path, and 5b 2.3 applied exactly that — plus the Data API family, which the stage had not thought to deny |
| 5, 6, 7 | answered by the brief, as the stage file records. 7's compensating control is applied: the `DataStorage` alarm, threshold argued in USD |
| **8 — new** | **How a second project is admitted.** Layer 1's tag is single-valued (above), so the options are: **(a)** the wide `for-use-with-all-datazone-projects=true`, accepting that the compute gate becomes per-account and leaning on layers 2 and 3, which are per project and resource-scoped; **(b)** a second workgroup per project on the same namespace — but the **namespace** tag is single-valued too, so this probably does not work and would need measuring first; **(c)** one project per warehouse, which multiplies the `[E]` object rather than the data. **Recommended: (a), with the argument written down** — a project whose role lacks `GetCredentials` still cannot connect, so the wide tag widens a gate that has two narrower gates behind it. It is not taken now because no second project exists, and taking it early would be deciding the shape before the requirement has a shape |

---

## 2026-09-21 — the project is admitted: layers 1, 2, 3 and the door are all applied, and the portal is the only half left

*Written by Claude in the sitting that ran it. The user was in the portal, had raised the sandbox, and
asked whether the absent Redshift connection was expected — it was, and the answer names which layer's
absence produces that exact symptom. Every reading and every apply is Claude's own, from
`awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission set `InfrastructureAccess`).*

### The question that started the sitting, and the layer it points at

The user opened project `eighth-experimentation` and saw no Redshift connection. The runbook's own table
([§O](../plan/runbooks/redshift-connection.md)) predicts that symptom for one layer and not the others:
**layer 1 absent = "the compute does not appear in the project's dropdown at all"**. Layer 2 absent would
have let the connection be created and failed every query at authentication; layer 3 absent would have
shown the cluster with an invisible schema. So the reading was not ambiguous, and the pending half was
Claude's rather than the user's.

### 0.1 re-read — the identifiers have not moved

| What | Value |
|---|---|
| domain | `dzd-d8yrvx1ko7im6o` (`awsds-studio`, `AVAILABLE`) |
| project | `avhvbqn37ty7m8`, `eighth-experimentation`, `ACTIVE` |
| project role | `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` |
| the project's security group | `datazone-avhvbqn37ty7m8-dev` (`sg-0fee1c059b82e3562`) |
| its VPC | `vpc-00dca74a35159b11c` |

**The workgroup's two subnets are in that same VPC** (`subnet-016b5a3a62c739894` in `us-west-2b`,
`subnet-09d3399d6b0fec93a` in `us-west-2a`), which is the precondition AWS names for JupyterLab's query
path. The Data page needs no such thing, and step 3.3/3.4 read the two doors apart for that reason.

### Two ceilings read before granting anything, because a grant above a ceiling is inert

Lesson 28's intersection, and Lesson 56's inert line. Layer 2 grants `GetCredentials` to a role that
carries the D13 permissions boundary, so the grant means nothing unless the boundary permits it:

- **the boundary** `awsds-sandbox-project-boundary` (v2) — nine statements, `Allow *` at
  `CeilingIsEverythingTheIdentityPolicyGrants`, and the eight Denies are SageMaker job shapes, direct S3
  on Lake-Formation-registered prefixes, and the lake data key off `kms:ViaService`. **Nothing names
  `redshift-serverless:` or `redshift-data:`**, so the boundary does not narrow layer 2.
- **the SCP** — `awsds-org-scp-baseline` carries exactly two Redshift statements,
  `DenyRedshiftProvisionedClusters` and `DenyRedshiftCostGuardTamperingExceptInfrastructure`. Neither
  touches `GetCredentials` or the Data API family.

### 1.4, 1.5 — the project's database user exists, and holds one role

Order (a) of the stage's chicken-and-egg: create the user, then grant, then let the connection use it.
Through the Data API, on database `sandbox`:

```sql
CREATE USER "IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c" PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
GRANT ROLE sbx_lab_rw TO "IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c";
```

Both `FINISHED`, 340 ms and 195 ms. Read back:

| `pg_user` | super | createdb |
|---|---|---|
| `IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>` | true | true |
| `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` | **false** | **false** |
| `dbadmin` | true | true |
| `rdsdb` | true | true |
| `sbx_lab_owner` | false | false |

`svv_user_grants` holds one row: that user, `sbx_lab_rw`, **`admin_option = false`** — so the project
cannot re-grant the role to anyone.

**`IAMR:<role>` is still a prediction, not a measurement.** It is the spelling the documented family uses
and the one this warehouse already carries for the SSO role, but whether a same-account serverless
`GetCredentials` resolves to it is what 3.2 answers. If it is wrong, the symptom is a second,
auto-created user appearing beside this one at the first connection, and the correction is one
`DROP USER` — which is why order (a) was taken.

### What `PUBLIC` already holds, read rather than assumed

The stage carried an owed `REVOKE` on `public` in each database (`db_name` adds a database, it does not
replace `dev`). Read on all three: `nspacl` is `rdsdb=UCDA/rdsdb | =U/rdsdb`, so **`PUBLIC` has `USAGE`
and not `CREATE`** in `sandbox`, `warehouse` and `dev` alike. Nothing owed. `lab` carries no legacy ACL
entry at all — its grants are RBAC, on `sbx_lab_rw`, which is `CREATE` + `USAGE` and nothing else.

### 2.1, 2.2, 2.3 — the map, applied, and a description EC2 refuses

One entry in `sandbox/warehouse/`'s `projects`, and the plan was exactly the four objects the design
promises from one map: `3 to add, 1 to change, 0 to destroy`.

| Object | Layer |
|---|---|
| `aws_redshiftserverless_namespace.this` (update) | 1, the namespace half |
| `aws_iam_policy.project_warehouse["avhvbqn37ty7m8"]` + its attachment | 2 |
| `aws_vpc_security_group_ingress_rule.project_5439["avhvbqn37ty7m8"]` | the door |

**The apply half-failed on the rule's description, and the wording is the finding:**

```
Error: creating VPC Security Group Rule
operation error EC2: AuthorizeSecurityGroupIngress, StatusCode: 400,
InvalidParameterValue: Invalid rule description. Valid descriptions are
strings less than 256 characters from the following set:  a-zA-Z0-9. _-:/()#,@[]+=&;{}!$*
```

The description read `... app ENIs -> Redshift 5439 ...`. **`>` is not in that set** — `=` is, `+` is,
`$` is, the arrow is not. This is the same trap as [5b](log-stage-05b-redshift-serverless.md)'s security
group *description*, which was refused for an apostrophe, and both times the apply was the only
validator: `terraform validate`, `fmt` and `tflint` all pass. Reworded to `app ENIs to Redshift 5439`,
re-applied, and the slice re-plans **`No changes`**.

The workgroup's half of layer 1 is written by `sandbox/warehouse-compute/` from this slice's state:
`0 to add, 1 to change, 0 to destroy`, the tag only, and it too re-plans `No changes`. Both objects read
back `AmazonDataZoneProject=avhvbqn37ty7m8`, and `for-use-with-all-datazone-projects` is **absent on
both**.

**The layer 2 policy, as applied** — two statements, and the workgroup id is a wildcard because the id
does not survive a destroy/re-create while the ARN carries it:

| Sid | Actions | Resource |
|---|---|---|
| `MintADatabaseSessionOnThisAccountsWarehouse` | `GetCredentials`, `GetWorkgroup`, `ListTagsForResource` | `…:workgroup/*` |
| `ListingWorkgroupsHasNoResource` | `ListWorkgroups`, `ListNamespaces` | `*` |

**The `redshift-data:` family is deliberately absent**, per 2.2's "only if 0.3's answer needs it". So the
JDBC path over 5439 is open and the Data API path is not granted to the project. Whether the portal's
Data page needs it is unmeasured, and 3.4's refusal — if it comes — is the measurement that decides it.
Starting narrow is what makes that refusal informative.

### 6.2 — `WH-11` is written, because there is now a project to read it for

The previous entry deferred `WH-11` on the grounds that a check reporting *"no project admitted"* says
nothing `WH-7` does not. That changed with the apply, so `./aws/warehouse.py` gained it: per admitted
project, the role exists, the slice's policy is attached to it, **and the role still carries
`awsds-sandbox-project-boundary`**. The plan-time precondition in `iam.tf` covers the boundary at author
time; this covers it afterwards, when somebody recreates the role. With no project admitted it is a
`note` that says nothing is verified, and outside Sandbox a `note` that D26 admits no project at all.

**`WH-7` failed first, and the defect was the instrument's.** It read `authored none, live
['avhvbqn37ty7m8']` against a map that was plainly there. Two faults in the parser, both Lesson 30 — a
tool's failure reported as a property of the world:

1. it required the map key to be **quoted**, and an identifier-shaped HCL key is written bare;
2. its regex ended the `default` block on a `}` at column zero, so the body ran on through the
   variable's `validation` blocks — and it read an entry called **`roject`**, out of the middle of
   `AmazonDataZoneProject` in an error message.

Both replaced by matching the map's braces. Tested against four inputs — the real file, an empty
`default = {}` (which must still parse, as `{}`, so the check keeps comparing instead of going quiet),
a quoted key, and a missing file.

### The instrument after the sitting

`./aws/warehouse.py awsds-infra-sandbox-1 --sql`, exit 0, **13 pass and 1 note**:

| Check | Reading |
|---|---|
| `WH-7` | `['avhvbqn37ty7m8']`, on both objects |
| `WH-11` | the warehouse policy is attached and the role is still under `awsds-sandbox-project-boundary` |
| `WH-12` | 1 themed schema, 1 role grant, **1 user-role grant** — the first time this is not zero |
| `WH-15` | idle: 9 RPU-seconds in the interval ending 2026-09-21T00:00:00-03:00 |
| `WH-13` | the permanent note: `svv_schema_quota_state` is refused to a superuser |

### What this stage still owes, and to whom

| Step | What | Why it is not done |
|---|---|---|
| 3.1, 3.2 | the connection, and every field the portal asks for | **the portal**, by a project member. Decision 1 wants the portal path measured once, and decision 2's `IAMR:` spelling is confirmed or refuted here |
| 3.3, 3.4 | the first write from JupyterLab, then the same query from the Data page | **a space.** 3.4 is also the measurement that decides whether the `redshift-data:` family joins layer 2 |
| 3.5, 3.6 | CloudTrail attribution, and the audit groups for that session | after 3.3; the audit half still waits on the export question 5b 6.1 left open |
| 5.1 | a project outside the map cannot use the compute | needs a second project |
| 5.2, 5.2a, 5.2b | the schema negatives, the quota from inside the project, two projects on one schema | need the project's own session |
| 5.3 | the project cannot administer the warehouse | the policy grants none of it, and an omission is not a measurement |
| 5.4 | the persona cannot mint a database session | needs the `awsds-scientist` SSO session |
| 6.2 | `WH-9`, `WH-10` | `WH-9` reads a connection that does not exist yet; `WH-10`'s substance is `WH-7` |
| 6.4 | keep or drop `lab` | the user's, and it has no hourly meter |
| — | `max_query_execution_time` binding a non-superuser | the project's database user now exists, so this is testable for the first time — from the project's session, not this one |

### Decisions

| # | State |
|---|---|
| 1, 2 | **open**, unchanged: both are answered by the portal act in 3.2 |
| 3, 4 | taken, as the previous entry records |
| 5, 6, 7 | answered by the brief |
| 8 | **open, and not yet forced.** One project is admitted and the single-valued tag has cost nothing yet. It bites at the second project |

---

## 2026-09-21 — the portal demands an access role on a same-account connection, which AWS's own procedure says it does not

*Written by Claude at the end of the sitting. The three portal readings are the **user's**, from the
data-scientist persona in the project, and are quoted as they were reported. Every documentation reading
and the Terraform are Claude's. **Nothing in this entry is applied**: the access role is authored and
`terraform validate` passes, and no plan has run against it — the SSO session expired twice during the
sitting and the apply is owed.*

### What the user found at the form

Three readings, in the order they arrived:

| Reading | Consequence |
|---|---|
| the **Redshift compute** dropdown offered `awsds-sandbox-warehouse…/dev` | **layer 1 works** — the tag put the compute in the project's dropdown. But the database offered is `dev`, and `lab` is in `sandbox` |
| no `lineageSync` option anywhere in the form | decision 3 costs nothing on this path: the portal cannot turn it on |
| **`Access role ARN` is required; `AWS Secret` is marked optional** | the form refuses to submit without a role AWS's same-account procedure never mentions |

### The contradiction, stated from both sides

AWS's *"Gaining access to Amazon Redshift resources"* splits into two procedures. **Same account** is
three steps: the member sends the project id, the admin adds `AmazonDataZoneProject={{projectID}}` to the
workgroup and its namespace, and *"The admin then must send you a username and password for a database
user that has access to the compute resources."* The access role, its trust policy and the
`RedshiftDbUser` tag appear only under **a different account**. The form's own help repeats it: *"Access
role ARN is optional. Required when connecting to resources in a different AWS account."*

The form then refuses to submit without it, same account, same VPC. So the implemented form and the
documented procedure disagree and the form is what has to be satisfied — Lesson 41's shape, with the
polarity reversed: a vendor **"optional"** that the implementation makes mandatory.

### Why this is the better outcome, and it removes decision 2's fallback

`aws datazone create-connection`'s model settles what "IAM credentials" is.
**`redshiftProperties.credentials` is a tagged union with exactly two variants — `secretArn` and
`usernamePassword`.** There is no IAM variant. So the portal's third option is not a credential type at
all: it is `awsLocation.accessRole` plus the `RedshiftDbUser` tag, which is how a connection reaches a
database with **no standing credential anywhere**.

That is what decision 2 wanted and had no mechanism for. Since the secret is optional and the role is
not, the purpose-made Secrets Manager secret decision 2 held in reserve is **not needed**, and no
password enters the estate.

### Three ceilings read, none of which blocks it

- **the D13 boundary** on the project role — nine statements, `Allow *` at the ceiling, eight Denies over
  SageMaker job shapes, direct S3 on LF-registered prefixes and the lake key. Nothing names `sts:`,
  `redshift-serverless:` or `redshift-data:`.
- **the RCP** — `EnforceOrgIdentitiesOnRoleAssumption` denies `sts:AssumeRole` only where
  `aws:PrincipalOrgID` is not this organization's. The project role is inside it.
- **the tag policy** — constrains `environment`, `project`, `managedby`, `owner`, `costcenter`.
  `RedshiftDbUser` is unconstrained.

### The API is closed to the infrastructure identity

`datazone list-connections` as `awsds-infra-sandbox-1`:

```
An error occurred (AccessDeniedException) when calling the ListConnections operation:
User is not permitted to perform operation: ListConnections
```

That is **DataZone's own authorization layer, not IAM** — the infrastructure identity is not a project
member. `create-connection` was not attempted: the call was **refused by this session's own tooling
guard**, so whether `CreateConnection` lands in the same place is **inferred and not measured**, and the
inference is recorded as one. The consequence stands either way: the connection is created by a project
member in the portal, which is where decision 1 put it.

### The access role, as authored

One per admitted project, from the same `projects` map, so layer 1, layer 2, the door and this cannot
drift apart.

| Piece | Content |
|---|---|
| trust policy | AWS's three statements whole: `sts:AssumeRole` with `sts:ExternalId` = the project id, `sts:SetSourceIdentity` matching `${aws:PrincipalTag/datazone:userId}`, `sts:TagSession` with **both** `AmazonDataZoneProject` and `AmazonDataZoneDomain` pinned |
| permissions | the **same** layer 2 policy document, two holders: the project role for a direct IAM session from JupyterLab, the access role for the portal's connection |
| plus | `tag:GetResources`, `tag:GetTagKeys` — AWS names them for "signing in using IAM credentials", where the user comes from a tag, so the signing identity must read its own tags |
| tag | `RedshiftDbUser = datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` |

`sts:AssumeRole` on that one role was added to layer 2's policy. AWS publishes the access role's trust
policy and never mentions granting the project role anything, which implies a managed policy already
carries it — a claim about an AWS document's contents, and AWS edits those (Lesson 49). A grant that
works because somebody else's document happens to include it is a grant with no owner.

**The tag's value is chosen to delete a guess.** No page read on 2026-09-21 says whether
`RedshiftDbUser` is used verbatim or prefixed the way an IAM-derived user is spelled. With the project
role's name as the value, the two candidate spellings collapse onto the pair layer 3 needed anyway —
`datazone_usr_role_<project>_<env>` and `IAMR:datazone_usr_role_<project>_<env>`, the second of which
already exists and already holds `sbx_lab_rw`. Creating the first as well means the first connection
cannot land on a user with no privileges; which one the service picked is then a readable fact in
`pg_user` and the other is one `DROP USER`.

**`RedshiftDbRoles` is deliberately absent.** It would map a database role at first sign-in and save the
`GRANT`, but AWS: *"In a case where you pass a role name that doesn't exist in the database, it's
ignored"* — a typo would produce a session with no privileges and nothing anywhere saying why. Layer 3
stays in SQL, where `WH-12` reads it back.

### A comment whose reason was wrong

`iam.tf` recorded `sqlworkbench:*` as refused because *"check-iam-wildcards.py rejects it"*. The script's
matcher is `arn:aws:iam::\*:` and its default target is `terraform-live/identity` — it neither scans this
slice nor judges an action. The refusal stands as an unmeasured wildcard; the reason is corrected, and
the corrected comment says that if 3.5's CloudTrail reading shows the portal needs it, it goes on the
**access role** rather than on the project role.

### Owed at the next sitting, in order

1. **Apply** `sandbox/warehouse/` — the access role, its two policies, the two attachments, and layer 2's
   new `sts:AssumeRole` statement. No plan has run.
2. **Create the second database user**, `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` (unprefixed),
   and grant it `sbx_lab_rw`.
3. **Hand the user `terraform output project_access_role_arns`** for the form's mandatory field.
4. **The connection, by the user**, with the **database set to `sandbox` and not `dev`** — by a separate
   database field if the form has one, otherwise through the JDBC URL with the `/dev` suffix replaced.
   Cross-database reads work in Redshift; a cross-database **write** does not, and 3.3 writes a table.
5. Then `pg_user`, `WH-12`, and 3.5's CloudTrail reading — which also decides `sqlworkbench:` and whether
   anything called the provisioned-cluster APIs.

### Decisions

| # | State |
|---|---|
| 1 | **answered in substance: the portal.** Not by preference — the API refuses the infrastructure identity, so a project member in the portal is the only path that exists today. The Terraform shape for the second connection is now writable against a measured object rather than against the API reference |
| 2 | **answered: IAM credentials, and the fallback is withdrawn.** The union has no IAM variant, so "IAM credentials" *is* the access role plus `RedshiftDbUser`; and because the secret is optional, no standing credential is needed. The purpose-made secret stays unbuilt |
| 3 | **taken, and now free**: the portal offers no `lineageSync` toggle on this path |
| 4 | taken, as the previous entries record |
| 5, 6, 7 | answered by the brief |
| 8 | open, and not yet forced |

---

## 2026-10-09 — the access role is applied, and the database half waits on the hub

*Written by Claude in the sitting that ran it. The apply is Claude's, from `awsds-infra-sandbox-1`
(account `Sandbox Account 1`, permission set `InfrastructureAccess`). Eighteen days passed since the
previous entry and the estate was found entirely down.*

### State found

`make status`: **burn 0.0000 USD/h**, every `[E]` slice at zero resources, both hub hosts `stopped`, and
**no workgroup**. `iam list-roles` carried only `awsds-sandbox-warehouse-exec`, so the access role
authored on 2026-09-21 had never been applied — which is what that entry said and what this one
confirms rather than assumes.

### The apply

`sandbox/warehouse/` is `[P]`, so it needs no compute and no hub. Plan: **4 to add, 1 to change, 0 to
destroy**, and the change is layer 2's policy gaining its `sts:AssumeRole` statement.

| Object | Action |
|---|---|
| `aws_iam_role.project_access["avhvbqn37ty7m8"]` | create |
| `aws_iam_policy.project_access_tags["avhvbqn37ty7m8"]` | create |
| `aws_iam_role_policy_attachment.project_access_warehouse[…]` | create |
| `aws_iam_role_policy_attachment.project_access_tags[…]` | create |
| `aws_iam_policy.project_warehouse["avhvbqn37ty7m8"]` | update |

Re-plan: **`No changes`**, exit 0. Read back: the role carries `RedshiftDbUser =
datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` and both policies are attached. The value a project
member needs is now an output:

```
project_access_role_arns = {
  "avhvbqn37ty7m8" = "arn:aws:iam::<Sandbox Account 1>:role/awsds-sandbox-warehouse-access-avhvbqn37ty7m8"
}
```

### Why the database half did not run, and it is a rule rather than a problem

Step 2 of the previous entry's list — the unprefixed database user — needs a **workgroup**: the Data API
serves SQL through the workgroup, and the namespace alone serves none. Raising
`sandbox/warehouse-compute` was refused:

```
awsds-prod-vpn         stopped i-…
awsds-prod-proxy       stopped i-…  <-- this one
```

**A spoke `up` refuses while a hub host is stopped** (D38, 6c step 7.2), and the refusal named the proxy.
The Data API itself needs neither the hub nor the proxy nor `sandbox/egress` — it reaches a private
workgroup from outside every VPC — so the guard is the estate's rule and not a technical dependency
here. It was **not worked around**: `slices.py` is the sanctioned path and a by-hand
`terraform apply` on that slice would have bypassed a guard somebody put there on purpose.

### Owed, and the order has collapsed into one sitting

Everything left needs the environment up, and the user's portal act needs it too, so the database user
belongs in the same sitting rather than ahead of it:

1. `make hub-up`, then `make up ENV=sandbox` — or `--only warehouse-compute` once the hub is up, which is
   enough for the database half alone.
2. **[Claude]** `CREATE USER "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c" PASSWORD DISABLE
   NOCREATEDB NOCREATEUSER` and `GRANT ROLE sbx_lab_rw` to it — the unprefixed spelling, so that
   whichever form `RedshiftDbUser` resolves to lands on a granted user.
3. **[user]** the connection, credential type **IAM credentials**, the access role ARN above, and the
   database set to **`sandbox`** rather than the dropdown's `dev`.
4. **[Claude]** `pg_user` for which spelling appeared, a `DROP USER` for the other, `WH-12`, and 3.5's
   CloudTrail reading.

---

## 2026-10-10 — both candidate database users exist and both hold the role; the form is unblocked

*Written by Claude in the sitting that ran it. The user raised the sandbox; the two statements and every
reading are Claude's, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission set
`InfrastructureAccess`).*

### State found

`make status ENV=sandbox`: `egress` **27 resources**, `warehouse-compute` **2**, `probes` **4**. The
workgroup reads `AVAILABLE` at base 4 / max 8. The namespace is `[P]`, so `lab`, `sbx_lab_owner`,
`sbx_lab_rw` and the prefixed database user all survived the eighteen-day down period unchanged.

### The second spelling

```sql
CREATE USER "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c" PASSWORD DISABLE NOCREATEDB NOCREATEUSER;
GRANT ROLE sbx_lab_rw TO "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c";
```

`FINISHED` at 12,503 ms and 4,575 ms — the first statement is the session's cold start, not the work.

| `pg_user` | super | createdb | `sbx_lab_rw` |
|---|---|---|---|
| `IAMR:AWSReservedSSO_InfrastructureAccess_<suffix>` | true | true | — |
| `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` | false | false | yes, `admin_option = false` |
| `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` | false | false | yes, `admin_option = false` |
| `dbadmin` | true | true | — |
| `rdsdb` | true | true | — |
| `sbx_lab_owner` | false | false | — |

**Both candidate spellings now hold the role**, which is the whole point: the access role's
`RedshiftDbUser` tag carries the project role's name, no page says whether the platform uses that value
verbatim or prefixes it `IAMR:`, and the project's first connection therefore cannot land on a user with
no privileges. One of the two is scaffolding and is removed once `pg_user` says which.

### The instrument

`./aws/warehouse.py awsds-infra-sandbox-1 --sql`, exit 0, **13 pass and 1 note**:

| Check | Reading |
|---|---|
| `WH-11` | the warehouse policy is attached and the role is still under `awsds-sandbox-project-boundary` |
| `WH-12` | 1 themed schema, 1 role grant, **2 user-role grants** |
| `WH-15` | idle: 0 RPU-seconds in the interval ending 2026-10-10T00:00:00-03:00 |
| `WH-7` | `['avhvbqn37ty7m8']`, on both objects |
| `WH-13` | the permanent note |

Every layer Claude owns is applied and read back. What remains is the portal act and what it measures.

---

## 2026-10-10 — the connection exists, and CloudTrail names every caller: three refusals, and the access role is the database identity

*Written by Claude in the sitting that ran it. The connection was created by the **user**, in the portal,
as the data-scientist persona; the quoted portal error is theirs. Every CloudTrail reading, the policy
change and its apply are Claude's, from `awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission
set `InfrastructureAccess`).*

### 3.2 — the connection, and the first attempt's error was an ARN

The user's first two attempts failed with:

```
Unable to assume AccessRole. User: arn:aws:sts::<Sandbox Account 1>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/<session>
is not authorized to perform: sts:AssumeRole on resource:
arn:aws:iam::<Sandbox Account 1>:role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c
```

The resource is the **project role itself** — the role trying to assume itself, because the field held the
wrong ARN. With `awsds-sandbox-warehouse-access-avhvbqn37ty7m8` the form accepted, and the compute
registered as **`redshift-serverless.redshift`**, reading **`Available`**.

> **A refused `sts:AssumeRole` records no `roleArn`.** Both denials are in the trail at 03:41:43Z and
> 03:43:15Z with `requestParameters.roleArn` **absent** and no `externalId`, while the two successes
> carry the target in full. So the trail says *denied* and not *denied for what*: the only evidence of
> which role was requested is the portal's own error text. Worth knowing before attributing a refusal
> from the trail alone.

### `Available` is the object's health, not a database session

`pg_user` after the connection was created and read `Available`: **the same six users, unchanged**. No
third spelling appeared, so **creating the connection mints no database session** — which means the
`RedshiftDbUser` question is still open and the `DROP USER` still owed. A database user is created when
credentials are *used*, not when they are minted.

### 3.5 — the attribution, from the account's own trail

Three hours, by event source, after the connection existed:

| Call | Result | Caller |
|---|---|---|
| `sts:AssumeRole` → the access role | ok ×2 | the **project role** |
| `sts:AssumeRole` → (target not logged) | **AccessDenied** ×2 | the project role — the wrong-ARN attempts |
| `redshift-serverless:ListWorkgroups` | ok ×1 | the **project role** |
| `redshift-serverless:GetWorkgroup` | ok ×3 | the **access role** |
| `redshift-serverless:GetCredentials` | ok ×2 | the **access role** |
| `redshift-serverless:GetNamespace` | **AccessDenied** ×1 | the access role |
| `sqlworkbench:GetResources` | **AccessDenied** ×6 | the access role |
| `sqlworkbench:ExecuteQuery` | **AccessDenied** ×1 | the access role |

**The database identity is the ACCESS ROLE, not the project role.** `GetCredentials` is called by
`awsds-sandbox-warehouse-access-avhvbqn37ty7m8`, so the session that reaches the database is the assumed
role's — which is why the `RedshiftDbUser` tag sits on that role and why layer 2 had to be attached to
both. The project role's own calls are the dropdown (`ListWorkgroups`) and the assume. This is the
answer 6h 1.4 and 6d step 7 both pointed at: *whose identity reaches the database* is neither the person
nor the project role.

**No provisioned-cluster API was called.** `redshift.amazonaws.com` in the whole window carries one
event, `DescribeIntegrations` by a Config session — no `DescribeClusters`, no `GetClusterCredentials`,
no `GetClusterCredentialsWithIAM`. So [5b](log-stage-05b-redshift-serverless.md) 1.10's third endpoint is
**not needed** for this path, and `DenyRedshiftProvisionedClusters` was never approached.

**Three statements of layer 2 are attached and unexercised**: `ListTagsForResource` (the portal checks
the admission tag somewhere this account's trail does not show), `ListNamespaces`, and the whole of the
old tag-reads policy. Lesson 20's shape, recorded rather than removed.

### The managed policy for the query editor does not cover what SMUS calls

`AmazonRedshiftQueryEditorV2NoSharing` **v9**, read 2026-10-10: 72 actions, 66 of them `sqlworkbench:`,
and **both `GetResources` and `ExecuteQuery` are absent**. So attaching AWS's own managed policy for this
surface would not have lifted the refusal — and that is why AWS's SMUS sample asks for `sqlworkbench:*`
instead. The sibling product calls actions outside the published policy for the product they belong to.

### The fix, authored from the trail rather than from the sample

`awsds-sandbox-warehouse-access-tags-<project>` is replaced by
`awsds-sandbox-warehouse-access-portal-<project>` — 2 added, 2 destroyed, nothing else touched, re-plan
`No changes`, `./aws/warehouse.py --sql` **13 pass / 1 note**. It carries:

- `redshift-serverless:GetNamespace`, scoped to `namespace/*` for the same reason the workgroup's id is a
  wildcard;
- the two measured `sqlworkbench` actions **plus the unconditional non-resource set** of that managed
  policy — the surface a session needs to exist;
- the tag reads, now with the managed policy's own condition `aws:CalledViaLast =
  sqlworkbench.amazonaws.com`, so they cannot become a general tag-enumeration grant.

**The owner-scoped half is withheld deliberately.** Saved queries, notebooks and charts carry a
`sqlworkbench-resource-owner` tag, and `sqlworkbench:*` would let one project's session read and delete
another principal's account-wide — worse again at the second project's access role (decision 8).
Narrowing the measured two further is owed once 3.3 and 3.4 have exercised the whole path.

**`checkov` refused the commit, and the finding was judged rather than waved through.**
`CKV_AWS_356` (`*` as a resource for restrictable actions) and `CKV_AWS_111` (write access without
constraints) both fired on the new document. The judgement: these `sqlworkbench` actions are **not
resource-scopable** — AWS's own managed policy puts them in a statement it names
`NonResourceLevelPermissions` with `Resource: *` — and `tag:GetResources` is an account-wide API that the
same policy also grants on `*`. The constraint that does exist is the **trust policy**: only this
project's role can assume the role, with the project id as the external id. The resource-scopable half,
the owner-tagged saved queries and notebooks, is the half deliberately withheld. Suppressed with both
reasons inside the block, per `runbooks/terraform-changes.md`; the slice scans **77 passed, 0 failed, 9
skipped**.

> **An absence from `lookup-events` shortly after the fact is not evidence.** A lookup by
> `EventName=GetResources` returned **no events**; a lookup by
> `EventSource=sqlworkbench.amazonaws.com` two minutes later returned **six of them**, same window.
> Whether that is indexing lag or an index that does not carry them, the reading is the same, and it is
> Lesson 62: the instrument has to be shown to report a presence before its silence means anything. The
> provisioned-cluster conclusion above rests on the **source** sweep for that reason, not on the name
> sweep that ran first.

### Owed

1. **[user]** a query through the connection — the Data page, or JupyterLab. The policy refusals are
   lifted; what this produces is the database user.
2. **[Claude]** `pg_user` for which spelling the platform resolved `RedshiftDbUser` to, `DROP USER` for
   the other, and the trail again for any further refusal.
3. **[user]** 3.3 proper: write a table into `lab` and read it back — and the connection's database must
   be `sandbox`, since a cross-database write does not work.
4. **[Claude]** 3.6, the two audit log groups for this session, searching `AUDITMARKER20260920`.

---

## 2026-10-10 — amendment: the previous entry read event names as actions, and the policy it authored granted nothing

*Written by Claude, same day, correcting the entry above rather than editing it. The Query editor
reading is the **user's** (*"Failed to fetch catalog", "Failed to fetch database"*); the trail readings,
the correction and its apply are Claude's.*

### What the previous entry got wrong

It recorded the refused actions as `sqlworkbench:GetResources` and `sqlworkbench:ExecuteQuery`, read from
CloudTrail's `eventName`, and granted exactly those. **Those are event names, not IAM actions.** The
denial **message** on the same events names the action being authorized:

```
User: arn:aws:sts::<Sandbox Account 1>:assumed-role/awsds-sandbox-warehouse-access-avhvbqn37ty7m8/<session>
is not authorized to perform: sqlworkbench:CreateConnection
because no identity-based policy allows the sqlworkbench:CreateConnection action
```

One event authorizes a differently-named action, and two different events authorized the same one. So
the policy applied at 03:49:40Z granted two actions nobody checks, and the next refusal was **identical
to the first** — which is the part worth carrying: the symptom does not say the grant missed.

**It also followed that the claim about the managed policy was wrong.** The previous entry said
`AmazonRedshiftQueryEditorV2NoSharing` v9 does not cover what SMUS calls, because `GetResources` and
`ExecuteQuery` are absent from it. They are absent because they are not actions. That policy **does**
carry both real ones — `DriverExecute` unconditionally and `CreateConnection` under
`aws:RequestTag/sqlworkbench-resource-owner` — so attaching it was a live option all along. It is still
not attached, for different and smaller reasons: it also brings `redshift:DescribeClusters` for a cluster
this design does not have, plus a secret-creation grant, and AWS edits a managed policy under its
holders (Lesson 49).

### Split by the apply, which is what separated signal from echo

The policy was created at **03:49:40Z**. Grouping the refusals around it:

| Window | Action refused |
|---|---|
| before 03:49:40Z | `sqlworkbench:DriverExecute` ×7 |
| after 03:49:40Z | `sqlworkbench:CreateConnection` ×12 |

So the first apply **did** work — for `DriverExecute`, which it happened to grant from the managed
policy's unconditional list. `CreateConnection` was the only one outstanding. Without the split, twelve
fresh refusals of a just-granted-looking action read as "the grant does not take".

### What the Query editor needs, from the messages rather than the event names

| Event | The action, or the layer | Principal |
|---|---|---|
| `GetResources` | `sqlworkbench:CreateConnection` ×12 | access role |
| `GetResources` | `sqlworkbench:DriverExecute` ×7, lifted | access role |
| `GetCatalogs` | `glue:GetCatalogs` ×7 — message is `An unknown error occurred`, so the action comes from the event name by necessity | access role |
| `GetNamespace` | `redshift-serverless:GetNamespace` ×1, lifted | access role |
| `GetDatabase` | **Lake Formation, not IAM**: *"Insufficient Lake Formation permission(s): Required Describe on raw"* ×8 | **project role** |

**The `raw` refusal is the perimeter working and stays refused.** The Query editor enumerates every Glue
database it can see and meets the lake's raw layer, where this project holds no `DESCRIBE`. Granting it
is a governance act under `GOVERNANCE.md`'s grant rules, with a named requester, not a fix for a
connection — and *"Failed to fetch database"* is the correct outcome for a project that may not describe
that database.

### Applied

`awsds-sandbox-warehouse-access-portal-avhvbqn37ty7m8` → **v2**, `0 added, 1 changed, 0 destroyed`,
re-plan `No changes`. It now carries `sqlworkbench:CreateConnection`, `sqlworkbench:DriverExecute`,
`glue:GetCatalogs` scoped to this account's catalog and its children, and the fifteen other
unconditional query-editor actions.

`CreateConnection` is **unconditional for now**, and the narrowing is one trail read rather than another
cycle: the managed policy guards it with `aws:RequestTag/sqlworkbench-resource-owner = ${aws:userid}`,
and whether the portal sends that tag is readable from the first **successful** call's
`requestParameters`.

### Owed

1. **[user]** open the Query editor again. `glue:GetCatalogs` and `sqlworkbench:CreateConnection` are
   live; the `raw` line will stay refused and should be read as correct.
2. **[Claude]** the trail for the next refusal, **from `errorMessage` this time**; whether the owner tag
   is sent on the successful `CreateConnection`; and `pg_user`, which is still unchanged and still owes
   the `RedshiftDbUser` answer and one `DROP USER`.

---

## 2026-10-10 — the Query editor answers, `RedshiftDbUser` resolves with an `IAMR:` prefix, and no user query reaches the audit log

*Written by Claude in the sitting that ran it. The Query editor listing is the **user's**, quoted as
reported; every trail and database reading, the `DROP USER` and the apply are Claude's, from
`awsds-infra-sandbox-1` (account `Sandbox Account 1`, permission set `InfrastructureAccess`).*

### What the project sees

The user, with the connection open in the Query editor:

```
awsdatacatalog  -> failed to fetch database
dev      -> public -> no data
sandbox  -> lab    -> no data
sandbox  -> public -> no data
warehouse -> public -> no data
```

**`sandbox → lab` is the three layers meeting.** The schema is visible to the project, which requires
`USAGE` on it, which arrives only through `sbx_lab_rw`. *"no data"* is correct: the schema holds no
tables, and writing one is 3.3.

**`awsdatacatalog -> failed to fetch database` is the designed state, not a gap.** That database is the
service's auto-mount of the Glue catalog, and it runs as the namespace role — which
[5b](log-stage-05b-redshift-serverless.md) decision 5 gave **no policy at all**. A warehouse that could
read a lake prefix directly would be a second producer into the governed lake, outside Lake Formation.
`WH-1b` is the check that keeps it that way.

### 1.4 answered: the tag is honoured, and Redshift prefixes it

`sys_query_history`, joined to `pg_user`, after the editor's first catalog walk:

| Database user | Queries | Last |
|---|---|---|
| `IAMR:datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c` | **142** | 2026-10-10 04:47:06 |
| `dbadmin` | 59 | 04:47:11 — Claude, through the Data API |

**`RedshiftDbUser` decides the database user and its value arrives prefixed `IAMR:`.** The
discriminator is clean: had the tag been ignored, the user would have been
`IAMR:awsds-sandbox-warehouse-access-avhvbqn37ty7m8`, the access role's own name, and it is not. So the
runbook's `IAMR:<role-name>` is measured rather than predicted — for a *tag value*, not for the calling
role.

The unprefixed spelling, created as insurance against the opposite answer, is **gone**: `DROP USER`
after confirming it owned no relation (`pg_class` 0) and had run no query (`sys_query_history` 0).
`WH-12` reads **1 user-role grant** again, and `./aws/warehouse.py --sql` is **13 pass / 1 note**.

### The two refusals that remain, and neither is a gap to close

| Event | What it is | Verdict |
|---|---|---|
| `GetResources` → `glue:GetDatabases`, access role ×1 | the editor enumerating Glue databases | **not granted, deliberately.** The only thing it reaches is the `awsdatacatalog` path decision 5 leaves unreachable |
| `GetDatabase` → *"Insufficient Lake Formation permission(s): Required Describe on raw"*, project role ×2 | Lake Formation, not IAM | **the perimeter working.** The project holds no `DESCRIBE` on the lake's raw layer; granting it is a governance act with a named requester |
| `GetResources` → *"Unknown resource type EXTERNAL_DATABASE"*, project role ×1 | not an authorization failure | the editor asking for the external-database type, which is the `awsdatacatalog` mount again |

### `CreateConnection` cannot be tightened the way the managed policy tightens it

The promise in the previous entry was that the owner-tag narrowing would cost one trail read rather than
another cycle. It cost the read, and the answer is **no**. A successful call's request, in full:

```json
{ "sqlworkbenchSource": "SUS",
  "connection": { "id": "arn:aws:sqlworkbench:us-west-2:<Sandbox Account 1>:connection/axsiuoykrswosw",
                  "databaseType": "REDSHIFT", "connectableResourceType": "WORKGROUP" },
  "type": "EXTERNAL_DATABASE", "maxItems": 50 }
```

**No `sqlworkbench-resource-owner` tag anywhere in it.** So
`AmazonRedshiftQueryEditorV2NoSharing`'s `CreateConnection`, guarded by
`aws:RequestTag/sqlworkbench-resource-owner = ${aws:userid}`, would not have been satisfied on this
path — and attaching that managed policy would have lifted `DriverExecute` and **left
`CreateConnection` refused**. The first entry's conclusion was therefore right in outcome and wrong in
its reason; the measured reason is this condition, not an absent action. The grant stays unconditional
and the containment is the trust policy: only this project's role may assume this role, with the project
id as the external id.

### 3.6 — no user query has ever reached the audit log, and the instrument is working

| Group | Last event | Age at reading |
|---|---|---|
| `connectionlog` | 2026-10-10T03:09:06Z | 99 min — and the workgroup was created 03:06:42Z, so this is its own startup |
| `useractivitylog` | 2026-09-21T05:43:33Z | 19 days |
| `userlog` | 2026-09-21T03:03:40Z | 19 days |

The configuration is not the explanation: the namespace exports **all three**
(`connectionlog useractivitylog userlog`) and the live workgroup reads
`enable_user_activity_logging true`.

**The absence passes Lesson 62's bar, which is why it is written down as a finding.** The instrument
demonstrably reports presences — `useractivitylog`'s last events are `user=rdsdb` health checks,
`SET QUERY_GROUP TO 'health'` and `SELECT 1` — and the marker left on 2026-09-20,
`AUDITMARKER20260920`, **is not in the group**, although the group holds events from *after* it. Today's
**142 queries** are likewise absent 40 minutes on. So twice, by two different paths — the Data API and
the portal's Query editor — a user query has produced nothing in `useractivitylog` while internal
`rdsdb` traffic arrives.

**Stage 11 must not rest its DLP feed on this group.** What remains possible is an export lag measured
in hours or days rather than minutes; the discriminator is a re-read, and it is owed. What is already
excluded is "the queries are there and nobody looked".

### Owed

1. **[user]** 3.3: write a table into `lab` from the Query editor and read it back. `lab` is visible and
   empty; this is the first write and the test `sbx_lab_rw`'s `CREATE` exists for.
2. **[user]** 3.4 from a space's JupyterLab, which is the `5439` door rather than this one — needs
   `make up ENV=sandbox GROUPS=redshift`.
3. **[Claude]** a later re-read of the three audit groups, for the lag question above.
4. **[Claude]** `WH-9`, now that a connection object exists to read.

---

## 2026-10-10 — amendment: the audit-log finding was half as strong as the previous entry claimed

*Written by Claude, same day, after a background `filter-log-events` over the whole
`connectionlog` group returned. The previous entry was written from the group's **latest event
timestamp**; this one is written from its **contents**, and one of its two claims does not survive.*

### What the full group says

155 connection records, and the two facts that matter:

- **Every one is `user=rdsdb`.** Not one user connection, by any path, in the group's whole retention
  window — not the portal's, not the Data API's.
- **The internal heartbeat fires about every 2h25m**, every day, through today: `9 Oct` at 00:59,
  03:24, 05:49, 08:14; `10 Oct` at 00:14, 02:39, and a `disconnecting session` at 03:09:06.

### The claim that does not survive

The previous entry argued that today's 142 queries being absent was evidence, because *"the group does
receive events"*. **The group's last write was 03:09:06Z and our activity was 04:17 and 04:47** — the
next heartbeat was not due until about 05:04. So the group had written nothing since before our queries,
and **a lag of tens of minutes fits every observation**. The reasoning was "it received today, so it
would have received ours", and the cadence makes that false.

`useractivitylog`'s 19-day silence has a similar reading available:
`enable_user_activity_logging` is a **workgroup** config parameter, and the `[E]` workgroup did not
exist for most of that window.

### What remains firm, and it is enough to act on

**The marker is the evidence.** `AUDITMARKER20260920`, run through the Data API on 2026-09-20, is
**absent** from `useractivitylog` — and that group holds events from **2026-09-21**, after it. No lag
explains a missing event when later events arrived. Together with 155 connection records that are
entirely `rdsdb`, the standing conclusion is unchanged: **Stage 11 must not rest its DLP feed on these
groups**, and the re-read is owed.

### The reading to carry

An absence needs a presence **of the same kind** before it is evidence. "The group received events" is
not the same statement as "the group received a user event", and the first was allowed to stand for the
second for one entry. Lesson 62 applied to its own write-up.

### One reading for free

`connectionlog` carries an `rdsdb` heartbeat on days the `[E]` workgroup did not exist — 3 through 9
October, with the estate found entirely down on the 9th. The **namespace** generates internal activity
with no workgroup at all, which is the same shape as RMS storage billing with no workgroup: `[P]` keeps
living, and a log group is not evidence that anybody's compute is up.
