# `production/warehouse/` — the data half of the governed Redshift warehouse

The compute half is [`../warehouse-compute/`](../warehouse-compute/), layer `[E]`. Why the slice is a
pair, what each half holds and what `make down ENV=production` removes are Stage 5b's; what this
account's copy changes is [`stage-09`](../../../docs/plan/stages/stage-09-deployment-targets.md)
step 9.1; the decision behind the warehouse is
[`D40`](../../../docs/plan/decisions/D40-redshift-warehouse.md); the instrument is
`./aws/warehouse.py`. Written 2026-10-22 from `sandbox/warehouse/` as built, not applied.

## One row per object this slice owns

| Object | What it is, and the rule |
|---|---|
| `aws_redshiftserverless_namespace.this` | the namespace `awsds-prod-warehouse`, under `alias/awsds-prod-data`, with a Redshift-managed admin secret and the three audit log exports on from birth. Its name is a **contract**: the three log-group paths below are derived from it by the service. No `AmazonDataZoneProject` tag: no SMUS project is admitted (step 9.3) |
| `aws_cloudwatch_log_group.audit["userlog"\|"connectionlog"\|"useractivitylog"]` | `/aws/redshift/awsds-prod-warehouse/<type>`, retention **30 days**, encrypted under the account data CMK (Stage 9 decision 8). Created **before** the namespace (`depends_on`): a group the service creates itself arrives `Never Expire` (`EXC-10`). The key policy's CloudWatch statement must name `/aws/redshift/*` before the first apply |
| `aws_iam_role.namespace_exec` | `awsds-prod-warehouse-exec`, trusted by `redshift.amazonaws.com` and `redshift-serverless.amazonaws.com` with the confused-deputy pair. **It holds no policy** (step 9.2): `COPY`, `UNLOAD` and `awsdatacatalog` run as it, the principal D13 is about |
| `aws_security_group.warehouse` | the workgroup's group, in VPC-Workloads. Ingress `5439/tcp` from the job security group only; **no egress rule at all** |
| `aws_vpc_security_group_ingress_rule.jobs_5439` | the one rule, from `awsds-prod-jobs` (`production/sagemaker/`, Stage 9 decision 12 (a)), group to group, never a CIDR |
| `aws_cloudwatch_metric_alarm.compute_capacity` | `ComputeCapacity > 4` on the workgroup. The ratchet is irreversible, so the alarm says *a manual `UpdateWorkgroup` is owed*. Notifies `awsds-prod-alerts` (`production/foundation/`, Stage 8 decision 5) |
| `aws_cloudwatch_metric_alarm.data_storage` | `DataStorage` above the dollar threshold, on the **namespace** dimension, so it keeps working while the compute is destroyed. The only bound on **total** storage. Notifies the same topic |

## What Sandbox's slice has and this one does not

The `projects` map, the per-project layer-2 policies, the access roles and the per-project `5439`
rules: a deployment target is never associated with the domain (D26, `DenyDataZoneEntirely`), so the
governed class has no project tag, no connection and no access role, and `./aws/warehouse.py` `WH-7`
reads the absence of the tag as the pass. The alerts topic is `production/foundation/`'s, where Stage
8 decision 5 created it, not an `observability/` slice's.

## The `REVOKE` this slice cannot express

Redshift creates every new database's `public` schema with `USAGE` and `CREATE` granted to the group
`PUBLIC`, so every database user in the namespace can create objects there until that is revoked.
There is no Terraform resource for a `REVOKE`; it is SQL, run once per database from the admin
credential, through the Data API (step 9.3). For this slice's own first database and the one the
service adds beside it:

```sql
-- database `warehouse`, the namespace's inert first database (Stage 5b step 1.6)
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON DATABASE warehouse FROM PUBLIC;
```

The same statements are owed for `dev` and for the class container `governed`, which step 9.3
creates; 9.3 reads each database's ACL first, since Sandbox's readings disagree on a fresh database.

## The admin secret's rotation while the compute is down

AWS says a rotation attempted with no workgroup attached fails and is not retried. Sandbox's first
scheduled rotation ran on 2026-10-20 with no workgroup and succeeded (`EXC-13`); this secret rotates on
the same 30-day schedule, so `EXC-13` gains a Production row at step 9.8, and whether the database took
the new password is read with the compute up, through the Data API.
