locals {
  # The one data lake administrator (decision 5): InfrastructureAccess alone. one() fails on
  # zero and on two - both are findings, neither may become an empty admins list.
  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)

  # The five buckets. Names are FOREVER in this account - DenyLakeDeletionAndDeregistration
  # denies s3:DeleteBucket unconditionally (stage callout at 1.2) - so they are built from
  # the env token exactly as docs/GOVERNANCE.md prints them, and from nothing else.
  bucket_keys  = ["raw", "curated", "artifacts", "logs", "dropbox"]
  bucket_names = { for k in local.bucket_keys : k => "awsds-${var.env}-${k}" }
  bucket_arns  = { for k, n in local.bucket_names : k => "arn:${data.aws_partition.current.partition}:s3:::${n}" }

  # INT-05's two allow-list branches, read live from [P] state - never pasted.
  consumer_vpce_ids = [
    for k, s in data.terraform_remote_state.consumer_foundation : s.outputs.s3_gateway_endpoint_id
  ]
  wireguard_eip_cidrs = [
    for k, s in data.terraform_remote_state.vpn_home : "${s.outputs.wireguard_eip_public_ip}/32"
  ]

  # The peer account roots the cross-account statements hang off. A bucket policy VALIDATES
  # its Principal, so a role that does not exist yet (awsds-prod-job-exec, Stage 9's
  # contract) cannot be a Principal - the account root is, and the ArnLike condition narrows
  # it to the one role. The same idiom covers the writers, whose project execution roles
  # (Stage 6) do not exist either.
  sandbox_root     = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.sandbox.account_id}:root"
  development_root = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.development.account_id}:root"
  production_root  = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.production.account_id}:root"

  # D18's writers: the data-scientist persona in each Interactive account. The path is the
  # reserved-SSO one; the suffix is minted per account, so both are patterns. Stage 6's
  # project execution roles join this list when they exist (step 9.3's extension-point rule).
  writer_role_patterns = [
    "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.sandbox.account_id}:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DataScientistAccess_*",
    "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.development.account_id}:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DataScientistAccess_*",
  ]

  # Stage 9 step 3's contract - the exact name deploytargets.py reads from both sides.
  prod_job_exec_pattern = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.production.account_id}:role/awsds-prod-job-exec"

  # The maintenance role's crawler reads the drop-box under this prefix; writers write under
  # it, dated by convention (incoming/<yyyy>/<mm>/<dd>/...) - the POLICY scopes the prefix,
  # the DATE is a convention a policy cannot spell.
  dropbox_prefix = "incoming"
}
