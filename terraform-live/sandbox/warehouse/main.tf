# sandbox/warehouse/ - the DATA half of the Redshift Serverless warehouse (Stage 5b pass 1), layer
# [P]. The compute half is sandbox/warehouse-compute/, layer [E], and the split is not a
# preference:
#
#   REDSHIFT SERVERLESS HAS NO PAUSE. A provisioned cluster can be paused and resumed; a serverless
#   workgroup has create-workgroup and delete-workgroup and nothing in between - no stop, no
#   suspend, no zero-capacity setting. So "powered off" means "does not exist", which is the
#   definition of [E] (conventions 5.1), and it is also the strongest guarantee available: an object
#   that does not exist cannot receive a query, so none of D40's three ways an idle warehouse bills
#   anyway (an open transaction, a connection pool's keep-alive, a cancelled query) has anything to
#   arrive at.
#
#   THE NAMESPACE HOLDS STATE NO PLAN RE-CREATES. The schemas, the database users, the database
#   roles and the GRANTs of Stage 6h are SQL; Terraform never wrote them and no plan can see them.
#   Destroying the namespace would destroy them along with the data, which is conventions 5.1 rule 2
#   - no state lives only inside an [E] resource.
#
# WHAT `make down ENV=sandbox` DOES NOT REMOVE is the Redshift Managed Storage this namespace holds:
# 0.024 USD/GB-month, and 24.58 USD/month for one schema filled to its 1 TB quota, with or without a
# workgroup in the account. Anyone reading D11's "pay nothing while idle" as covering this store
# will be wrong by half the D12 ceiling.

# ------------------------------------------------------------------- the three audit log groups
#
# CREATED BEFORE THE NAMESPACE CAN CREATE THEM, and the order is the whole point. AWS: a log group
# "with the specified name doesn't exist ... Amazon Redshift Serverless creates a new log group
# ... [which] uses the default log-retention period of Never Expire", and "A log group with the
# specified name exists. Redshift exports log data using the existing log group." So owning the
# group first is the documented fix, and the depends_on below is what makes "first" true rather
# than likely.
#
# This estate already carries one never-expiring group as a dated exception (AWS_STATE.md EXC-10,
# the SMUS apps). The whole reason to do this here is not to acquire a second.
resource "aws_cloudwatch_log_group" "audit" {
  # checkov:skip=CKV_AWS_158:a CMK is USD 1/key-month per key and these three groups are an audit feed, not a store - the same judgement Stage 3 recorded for flow logs and Stage 4 for the handshake log
  # checkov:skip=CKV_AWS_338:retention is 30 days by decision (5b decision 4) - useractivitylog carries SQL TEXT and therefore literal data values, so a year of it is a growing store nobody has scoped; Stage 11 step 5.1 decides the export and the real period. The audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  for_each = toset(local.log_types)

  name              = "/aws/redshift/${local.name}/${each.value}"
  retention_in_days = var.log_retention_days
}

# ---------------------------------------------------------------------------------- the namespace
resource "aws_redshiftserverless_namespace" "this" {
  namespace_name = local.name

  # The account data CMK, never the AWS-managed key: docs/GOVERNANCE.md's per-account encryption
  # rule makes "who can read this account's data" one key policy rather than a property of each
  # store.
  kms_key_id = local.data_key_arn

  # THE ADMIN CREDENTIAL IS REDSHIFT'S, NOT OURS. `manage_admin_password` makes Redshift create and
  # rotate a Secrets Manager secret and export its ARN; `admin_user_password` would put a password
  # in this state file and in every plan's output. Stage 6h reads admin_password_secret_arn to run
  # the SQL of its layer 3, and WH-5 greps this state for a password string - a check, not a matter
  # of trust.
  admin_username        = var.admin_username
  manage_admin_password = true

  # THE SECRET TAKES THE SECRETS MANAGER KEY AND NOT THE ACCOUNT DATA CMK, and the first apply is
  # what settled it (2026-09-20). `admin_password_secret_kms_key_id = <the data CMK>` was refused:
  #
  #   ConflictException: Unable to create namespace credential secret: The KMS key used to encrypt
  #   the secret is not accessible
  #
  # The cause is D31, working as designed. AWS: a user who passes AdminPasswordSecretKmsKeyId
  # "require[s] the following permissions in addition" - kms:Decrypt, kms:GenerateDataKey,
  # kms:CreateGrant, kms:RetireGrant - and the data key's policy grants the account root
  # ADMINISTRATION ONLY, deliberately holding back every cryptographic action so that "delegation to
  # IAM is therefore impossible for the operations that read data" (terraform-modules/consumer-data
  # kms.tf). Granting Decrypt and GenerateDataKey on the DATA key so that a CREDENTIAL could be
  # created would widen the read control D31 exists to hold, for a reason that has nothing to do
  # with reading data.
  #
  # And the CMK bought nothing here. AWS: "Optionally, you can specify a customer managed key to
  # encrypt the secret IF YOU NEED TO ACCESS THE SECRET FROM ANOTHER AWS ACCOUNT. You can also use
  # the KMS key that AWS Secrets Manager provides." Nothing reads this secret from another account -
  # D40 puts the other class in its own account with its own namespace and its own admin - so the
  # field is omitted and the secret rides the `aws/secretsmanager` key.
  #
  # docs/GOVERNANCE.md's per-account encryption rule is untouched: it is about DATA, and `kms_key_id`
  # above is the data. A credential is not data under that rule, and saying so here is cheaper than
  # discovering the distinction the next time a store needs a managed secret.

  # The namespace is born with a database whether one is wanted or not - the service default is
  # `dev` - and a database nobody named is a database nobody revoked PUBLIC on. See README.md, "The
  # REVOKE this slice cannot express".
  db_name = var.first_database

  # The Stage 11 feed, switched on at creation rather than added later: a log that starts late has a
  # silent gap, and the gap is exactly the window in which the first connections happen.
  log_exports = local.log_types

  # The role COPY, UNLOAD and the auto-mounted awsdatacatalog database run as. It reaches NOTHING
  # (iam.tf): 5b decision 5, taken so the first grant on the lake is a deliberate act with a named
  # requester.
  iam_roles            = [aws_iam_role.namespace_exec.arn]
  default_iam_role_arn = aws_iam_role.namespace_exec.arn

  # LAYER 1'S NAMESPACE HALF, AND THE TAG ADMITS EXACTLY ONE PROJECT. AWS's documented requirement
  # names both objects - the admin "adds 1 of the following tags to the Amazon Redshift cluster or
  # workgroup AND ITS NAMESPACE" - and the workgroup half is written by
  # sandbox/warehouse-compute/ from this same map, read out of this slice's state. One authored
  # place, two consumers: the two can only disagree through an edit that fails a plan.
  #
  # `AmazonDataZoneProject` is a TAG KEY, so it holds one value, and AWS's second option for more
  # than one project is the wide `for-use-with-all-datazone-projects=true`. variables.tf's
  # `projects` validation is what turns that into a plan error rather than a connection nobody can
  # explain - see its comment, and 6h decision 8.
  tags = { for id in keys(var.projects) : "AmazonDataZoneProject" => id }

  depends_on = [aws_cloudwatch_log_group.audit]
}
