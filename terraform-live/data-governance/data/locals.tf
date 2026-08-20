locals {
  # The one data lake administrator (decision 5): InfrastructureAccess alone. one() fails on
  # zero and on two - both are findings, neither may become an empty admins list.
  infrastructure_access_role_arn = one(data.aws_iam_roles.infrastructure_access.arns)

  # The governance manager (step 6, pass 2) - resolved the same way and for the same reason,
  # and NOT an admin by decision 5: it holds the specific grants in governance.tf instead.
  # one() failing here means the set is not provisioned in this account, which would make
  # every grant below aim at nothing - a loud failure rather than a silent no-op.
  governance_manager_role_arn = one(data.aws_iam_roles.governance_manager.arns)

  # The three catalog databases, as the grant targets of step 6. Built from the resources so
  # a fourth database cannot be added without deciding whether the governance manager sees
  # it - the alternative, a literal list, is the same set written twice (Lesson 14).
  governed_databases = {
    raw     = aws_glue_catalog_database.raw.name
    curated = aws_glue_catalog_database.curated.name
    dropbox = aws_glue_catalog_database.dropbox.name
  }

  # The consumer accounts of step 7's shares. Production is absent BY DESIGN, not by omission:
  # its share carries the governed write and arrives with Stage 9, which has a job role to
  # receive it. The ids come from the aliased providers, so no account id enters a tracked
  # file, and an account that cannot be read fails by name here.
  consumer_accounts = {
    sandbox     = data.aws_caller_identity.sandbox.account_id
    development = data.aws_caller_identity.development.account_id
  }

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

  # THE VPN HOMES' OWN S3 ENDPOINTS, ON THE AXIS THAT CARRIES THEM (2026-08-20; Lesson 33's
  # second finding, stage 5 log's controls entry). Every tunnel call - whichever account's
  # persona makes it - exits through the HOME's gateway endpoint, so its id belongs in the
  # trusted list because the home is the tunnel's exit, NOT because the home happens to
  # consume the lake. Today the two lists intersect (the single home is also a consumer) and
  # the rendered policy is UNCHANGED by this line; the day a second home appears, or the host
  # moves to a non-consumer account, this is what keeps the perimeter's S3 branch honest
  # instead of correct by coincidence (Lessons 10, 29).
  vpn_home_vpce_ids = [
    for k, s in data.terraform_remote_state.vpn_home : s.outputs.s3_gateway_endpoint_id
  ]
  trusted_vpce_ids = sort(distinct(concat(local.consumer_vpce_ids, local.vpn_home_vpce_ids)))

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
