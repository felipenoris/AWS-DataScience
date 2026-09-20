# `sandbox/warehouse/` — the data half of the Redshift Serverless warehouse

The compute half is [`../warehouse-compute/`](../warehouse-compute/), layer `[E]`. Why the slice is a
pair, what each half holds and what `make down ENV=sandbox` removes are in
[`stage-05b`](../../../docs/plan/stages/stage-05b-redshift-serverless.md); the decision behind the
warehouse is [`D40`](../../../docs/plan/decisions/D40-redshift-warehouse.md); the instrument is
`./aws/warehouse.py`.

## One row per object this slice owns

| Object | What it is, and the rule |
|---|---|
| `aws_redshiftserverless_namespace.this` | the namespace `awsds-sandbox-warehouse`, under the account data CMK, with a Redshift-managed admin secret and the three audit log exports on from birth. Its name is a **contract**: the three log-group paths below are derived from it by the service, so a rename moves them |
| `aws_cloudwatch_log_group.audit["userlog"\|"connectionlog"\|"useractivitylog"]` | `/aws/redshift/awsds-sandbox-warehouse/<type>`, retention **30 days**. Created **before** the namespace (`depends_on`): a group the service creates itself arrives `Never Expire`, and this estate keeps exactly one such group as a dated exception (`AWS_STATE.md` `EXC-10`) |
| `aws_iam_role.namespace_exec` | `awsds-sandbox-warehouse-exec`, trusted by `redshift.amazonaws.com` and `redshift-serverless.amazonaws.com` with the confused-deputy pair. **It holds no policy** (5b decision 5): `COPY`, `UNLOAD` and `awsdatacatalog` run as it, which is exactly the principal D13 is about |
| `aws_security_group.warehouse` | the workgroup's group. Ingress `5439/tcp` from an admitted project's own security group only; **no egress rule at all** |
| `aws_vpc_security_group_ingress_rule.project_5439[<projectId>]` | one per entry in `projects`. Group-to-group, never a CIDR: a CIDR would admit every ENI in two /18s |
| `aws_iam_policy.project_warehouse[<projectId>]` + its attachment | layer 2 of the Redshift connection — `GetCredentials`, `GetWorkgroup`, `ListTagsForResource` scoped to this account's workgroups, plus the two listings that take no resource. The attachment's precondition refuses a role that does not carry the D13 boundary |
| `aws_cloudwatch_metric_alarm.compute_capacity` | `ComputeCapacity > 4` on the workgroup. The ratchet is irreversible, so the alarm says *a manual `UpdateWorkgroup` is owed*, not *this will pass*. Notifies nobody — no SNS topic exists in this account (Stage 12) |
| `aws_cloudwatch_metric_alarm.data_storage` | `DataStorage` above the dollar threshold, on the **namespace** dimension, so it keeps working while the compute is destroyed. It is the only bound on **total** storage: a schema `QUOTA` bounds one schema and nothing bounds the number of schemas |
| `AmazonDataZoneProject` tag | on the namespace here and on the workgroup in the other slice, both from this slice's `projects` map. **One value**: see below |

## Layer 1 admits one project, and the limit is AWS's

AWS (*Gaining access to Amazon Redshift resources*, read 2026-09-20): the admin *"adds 1 of the
following tags to the Amazon Redshift cluster or workgroup and its namespace"* — either
`AmazonDataZoneProject={{projectID}}`, which names **one** project, or
`for-use-with-all-datazone-projects=true`, which names **every** project in the account. There is no
per-project list, because `AmazonDataZoneProject` is a tag key and a key holds one value.

So `projects` is validated to hold at most one entry. Stage 5b 2.2's *"one tag per admitted project"*
is not expressible, and the requirement that one sandbox schema may be **shared** by several projects
meets that wall at the second project, not the first. Layers 2 and 3 are unaffected — one IAM policy
per project role, and a database role per schema granted per project, both genuinely many-to-many.
Admitting a second project is a decision with the wide tag's cost accepted or rejected in writing
([6h](../../../docs/plan/stages/stage-06h-redshift-connection.md) decision 8), never a second map
entry.

## The `REVOKE` this slice cannot express

Redshift creates every new database's `public` schema with `USAGE` and `CREATE` granted to the group
`PUBLIC`, so **every database user in the namespace can create objects there** until that is revoked.
There is no Terraform resource for a `REVOKE`; it is SQL, run once per database from the admin
credential. For this slice's own first database:

```sql
-- database `warehouse`, the namespace's inert first database (Stage 5b step 1.6)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE warehouse FROM PUBLIC;
```

The same statements are owed for the class container `sandbox`, which
[6h](../../../docs/plan/stages/stage-06h-redshift-connection.md) 1.1 creates and 1.2 revokes. Written
here rather than left to memory: an intention is not a control (Lesson 5), and a procedure that
depends on a file it did not create runs only for its author (Lesson 61).

## The admin secret does not rotate while the compute is down

AWS: *"If your serverless namespace doesn't have a workgroup associated when Amazon Redshift attempts
to rotate its attached secret, the rotation will fail and won't try to rotate it again, even after you
attach a workgroup. You must restart the auto-rotation schedule using the
`secretsmanager:RotateSecret` API call"* — and the default schedule is every 30 days.

The `[E]` compute means *no workgroup* is the normal state between sessions, so a scheduled rotation
will almost always land in a window with no workgroup and **stop permanently**. This is a consequence
of the split, not a defect in it, and it is recorded in `AWS_STATE.md` as a residual: nothing else in
this estate rotates a credential either, and the alternative — keeping a 4-RPU workgroup up so that a
secret can rotate — costs the guarantee the split exists to give.
