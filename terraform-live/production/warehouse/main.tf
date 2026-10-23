# production/warehouse/ - the data half of D40's governed warehouse (Stage 9 step 9), layer [P]. The
# compute half is production/warehouse-compute/, layer [E], and the split is Stage 5b's:
#
#   Redshift Serverless has no pause. A workgroup has create-workgroup and delete-workgroup and
#   nothing in between, so "powered off" means "does not exist", which is the definition of [E]
#   (conventions 5.1), and an object that does not exist cannot receive a query.
#
#   The namespace holds state no plan re-creates: the schemas, the database users, the database roles
#   and the GRANTs of step 9.3 are SQL, which Terraform never wrote. Destroying the namespace would
#   destroy them with the data, which conventions 5.1 rule 2 forbids.
#
# What `make down ENV=production` does not remove is the Redshift Managed Storage this namespace
# holds: 0.024 USD/GB-month, with or without a workgroup in the account.
#
# This is the first governed store outside Data Governance (D22, D40): its schemas reach readers only
# through Lake Formation (step 9.5), it is written by awsds-prod-job-exec alone (9.4, 9.6), and no SMUS
# project is admitted to it (9.3): no project tag, no connection, no access role.

# ------------------------------------------------------------------- the three audit log groups
#
# Created before the namespace can create them, and the order is the point. AWS: a log group
# "with the specified name doesn't exist ... Amazon Redshift Serverless creates a new log group
# ... [which] uses the default log-retention period of Never Expire", and "A log group with the
# specified name exists. Redshift exports log data using the existing log group." Owning the group
# first is the documented fix, and the depends_on below is what makes "first" true. EXC-10 stays at
# one never-expiring group.
#
# Each group is encrypted under the account data CMK (Stage 9 decision 8): useractivitylog carries
# the SQL text of every statement, and in this account that text carries governed values, so the log
# is a store of them. CloudWatch Logs uses the key as its own principal under the key policy's
# CloudWatch statement, which must admit these groups' ARNs; no role holds a grant on the key for them.
resource "aws_cloudwatch_log_group" "audit" {
  # checkov:skip=CKV_AWS_338:retention is 30 days by decision (Stage 9 decision 8, Sandbox's 5b decision 4): useractivitylog carries SQL text and therefore governed values, so a year of it is a growing store nobody has scoped; Stage 11 step 5.1 decides the export and the real period. The audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  for_each = toset(local.log_types)

  name              = "/aws/redshift/${local.name}/${each.value}"
  retention_in_days = var.log_retention_days
  kms_key_id        = local.data_key_arn
}

# ---------------------------------------------------------------------------------- the namespace
resource "aws_redshiftserverless_namespace" "this" {
  namespace_name = local.name

  # The account data CMK, never the AWS-managed key: docs/GOVERNANCE.md's per-account encryption
  # rule makes "who can read this account's data" one key policy rather than a property of each
  # store. The key policy's `AllowRedshiftServerlessViaServiceInThisAccount` is what lets
  # CreateNamespace use it: without that statement the call fails with "the key ... is inaccessible"
  # and leaves an orphan admin secret behind (EXC-12, Sandbox's first apply).
  kms_key_id = local.data_key_arn

  # The admin credential is Redshift's, not ours. `manage_admin_password` makes Redshift create and
  # rotate a Secrets Manager secret and export its ARN; `admin_user_password` would put a password in
  # this state file and in every plan's output. Step 9.3 reads admin_password_secret_arn to run the
  # governed schema's SQL through the Data API, and WH-5 greps this state for a password string.
  admin_username        = var.admin_username
  manage_admin_password = true

  # The secret takes the Secrets Manager key and not the account data CMK (measured 2026-09-20 in
  # Sandbox): `admin_password_secret_kms_key_id = <the data CMK>` was refused with "The KMS key used to
  # encrypt the secret is not accessible", because the data key's policy grants the account root
  # administration only and holds back every cryptographic action (D31). A credential is not data
  # under docs/GOVERNANCE.md's per-account rule, and nothing reads this secret from another account,
  # which is the one case AWS names for a customer managed key on it. The field is omitted and the
  # secret rides the `aws/secretsmanager` key.
  #
  # The rotation runs with no workgroup attached: Sandbox's first scheduled rotation succeeded on
  # 2026-10-20 against AWS's page (EXC-13), and this secret rotates on the same schedule, so EXC-13
  # gains a Production row (step 9.8).

  # The namespace is born with a database whether one is wanted or not; the service default is `dev`,
  # and a database nobody named is a database nobody revoked PUBLIC on (README.md, "The REVOKE this
  # slice cannot express"). `db_name` adds a database beside `dev` rather than replacing it, so the
  # namespace holds `warehouse` and `dev` at birth and `governed` after step 9.3: WH-6 expects those
  # three.
  db_name = var.first_database

  # The Stage 11 feed, switched on at creation: a log that starts late has a silent gap, and the gap
  # is the window in which the first connections happen.
  log_exports = local.log_types

  # The role COPY, UNLOAD and the auto-mounted awsdatacatalog database run as. It holds no policy
  # (iam.tf, step 9.2): a policy here turns awsdatacatalog on over this account's resource links to the
  # lake, with the engine reading as this role rather than as the caller.
  iam_roles            = [aws_iam_role.namespace_exec.arn]
  default_iam_role_arn = aws_iam_role.namespace_exec.arn

  # No `AmazonDataZoneProject` tag (step 9.3): D26 keeps a deployment target out of the domain, and
  # objectives.md makes the absence a requirement. WH-7 reads no project tag on this namespace.

  depends_on = [aws_cloudwatch_log_group.audit]
}
