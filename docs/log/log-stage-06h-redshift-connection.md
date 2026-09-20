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
