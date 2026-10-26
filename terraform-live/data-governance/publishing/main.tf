# data-governance/publishing/ - what a SageMaker Unified Studio project needs in the lake account to
# publish the lake's own tables (Stage 6f decision 1, shape (b), the pilot of 2026-10-26; step 11).
# Layer [P].
#
# The publishing project's `Tooling` environment is provisioned into this account, because a Glue
# data source reads the catalog of its own account and a resource link cannot be subscribed to. Its
# template takes `vpcId`, `subnets` and `availabilityZones` with no default and creates a security
# group in that VPC, and the `DataLake` template imports the bucket path the Tooling stack exports,
# so neither runs without a VPC here (both templates read 2026-10-26). The VPC is the vpc module's
# shape with no internet route and no peering: the Data OU denies every launch, so nothing in it
# ever holds an address but the Tooling stack's security group and Glue connections.
#
# Two applies, the shape sandbox/sagemaker/ has, with no association between them:
#
#   1. terraform apply    the VPC, the flow-log role, the two service roles, the D13 boundary,
#                         the project key, the projects bucket, the log group
#   2. (one edit)         backend.LAKE_PUBLISHERS gains data-governance; tfvars regenerated
#   3. terraform apply    the Tooling configuration and its CREATE_ENVIRONMENT_FROM_BLUEPRINT grant,
#                         after data/ has seated the two service roles (step 11.3)
#
# What this slice cannot remove: the Data OU's DenyLakeDeletionAndDeregistration denies
# s3:DeleteBucket and lakeformation:DeregisterResource to every principal, so the projects bucket
# and the `dev/` registration the Tooling stack writes outlive a rollback (step 11.10).

locals {
  # The vpc module builds its flow-log group from the same prefix (terraform-modules/vpc/main.tf),
  # and the role below is scoped to exactly that group.
  name_prefix = "awsds-${var.env}"

  # The lake's Lake Formation-registered locations (raw and curated), which the D13 boundary
  # denies the project role directly, as in sandbox/sagemaker/main.tf.
  lake_registered_bucket_arns = [
    data.terraform_remote_state.lake.outputs.bucket_arns["raw"],
    data.terraform_remote_state.lake.outputs.bucket_arns["curated"],
  ]

  lake_dropbox_write_arn = format(
    "%s/%s/*",
    data.terraform_remote_state.lake.outputs.bucket_arns["dropbox"],
    data.terraform_remote_state.lake.outputs.dropbox_prefix,
  )
}

# ------------------------------------------------------------------------------- the network

module "flow_log_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "${local.name_prefix}-vpc-flow-logs"
  description = "VPC Flow Logs delivery to CloudWatch Logs (Stage 6f step 11)"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowVpcFlowLogsService"
        Effect    = "Allow"
        Principal = { Service = "vpc-flow-logs.amazonaws.com" }
        Action    = "sts:AssumeRole"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      }
    ]
  })

  inline_policies = {
    "deliver-to-cloudwatch-logs" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid    = "WriteFlowLogStreams"
          Effect = "Allow"
          Action = [
            "logs:CreateLogStream",
            "logs:PutLogEvents",
            "logs:DescribeLogGroups",
            "logs:DescribeLogStreams",
          ]
          Resource = "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:log-group:${local.name_prefix}-vpc-flow-logs:*"
        }
      ]
    })
  }
}

# No route to the internet gateway (D38's spokes), and no peering: the Tooling stack is the VPC's
# only tenant, and it reaches nothing.
module "vpc" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc?ref=vpc-v0.4.0"

  env                   = var.env
  vpc_cidr              = var.vpc_cidr
  zone_ids              = var.zone_ids
  flow_log_role_arn     = module.flow_log_role.role_arn
  public_internet_route = false
}

check "unpeered" {
  assert {
    condition     = length(var.peerings) == 0
    error_message = "a PEERINGS row names data-governance/publishing: the lake account's VPC exists for the Tooling stack's parameters and reaches no other VPC (Stage 6f step 11)."
  }
}

# --------------------------------------------------------------- the blueprint prerequisites

module "sagemaker_prereqs" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-prereqs?ref=sagemaker-prereqs-v0.8.0"

  env    = var.env
  region = var.region

  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids

  lake_registered_bucket_arns = local.lake_registered_bucket_arns
  lake_dropbox_write_arn      = local.lake_dropbox_write_arn
  lake_data_key_arn           = data.terraform_remote_state.lake.outputs.data_key_arn

  # The base alone: publishing needs the project role and its LAKEHOUSE connection, and the
  # subscription target a DataLake environment carries is the consumer's (6f 0.9).
  blueprint_names = ["Tooling"]

  blueprints_enabled        = var.blueprints_enabled
  domain_account_id         = data.aws_caller_identity.current.account_id
  domain_execution_role_arn = var.blueprints_enabled ? data.terraform_remote_state.governance[0].outputs.domain_execution_role_arn : null
  domain_id                 = var.blueprints_enabled ? data.terraform_remote_state.governance[0].outputs.domain_id : null
  root_domain_unit_id       = var.blueprints_enabled ? data.terraform_remote_state.governance[0].outputs.root_domain_unit_id : null
}
