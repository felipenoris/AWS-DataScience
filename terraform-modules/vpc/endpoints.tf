# The S3 and DynamoDB GATEWAY endpoints (Stage 3 step 3) - free, [P], associated with the
# route tables of all three tiers (3.1), and THE ONLY ENDPOINT IDS ANY POLICY MAY EVER NAME
# (3.3, Lesson 3, INT-05): the [E] interface endpoints of egress/ get new IDs on every
# make up and anchor nothing.
#
# THEIR POLICIES LIVE HERE, NOT IN egress/ - a refinement of the step 9 pass, recorded at
# implementation (2026-08-16): the policy is an attribute of the endpoint, the endpoint is
# [P], and Stage 4's WireGuard host installs packages through this endpoint while egress/
# may be down - an allow-list that vanished with make down would leave the gateway on the
# default full-access document exactly when the [D] host can boot. The interface-endpoint
# policies stay [E] with their endpoints, in egress/.

data "aws_organizations_organization" "current" {} # DescribeOrganization answers from any member account (measured, Stage 1b)

data "aws_partition" "current" {}

data "aws_region" "current" {}

locals {
  # Step 9.3's five families as the DOCUMENTED DEFAULT - names from AWS's documentation, not
  # measured (Lesson 23); verification (iii) confirms each at execution. The list is a
  # variable because it is the statement most likely to be trimmed by somebody tidying up
  # (9.5), and its failure mode is a package manager that HANGS, not an AccessDenied.
  default_aws_buckets = [
    "al2023-repos-${data.aws_region.current.region}-*",             # AL2023 repositories - packages AND the mirror list (9.3's correction)
    "amazoncloudwatch-agent-${data.aws_region.current.region}",     # CloudWatch agent (Stage 4 step 7)
    "amazon-ssm-${data.aws_region.current.region}",                 # SSM agent updates (Stage 7; the only way into GitLab)
    "aws-ssm-${data.aws_region.current.region}",                    # SSM document modules - the documented minimum's second half
    "prod-${data.aws_region.current.region}-starport-layer-bucket", # ECR image layers - every docker pull (Stages 6-8)
    "sagemaker-${data.aws_region.current.region}",                  # SageMaker regional bucket (Stage 6)
    "jumpstart-cache-prod-${data.aws_region.current.region}",       # SageMaker JumpStart artifacts (Stage 6)
  ]

  aws_buckets = coalesce(var.s3_endpoint_allowed_bucket_names, local.default_aws_buckets)

  aws_bucket_arns = flatten([
    for b in local.aws_buckets : [
      "arn:${data.aws_partition.current.partition}:s3:::${b}",
      "arn:${data.aws_partition.current.partition}:s3:::${b}/*",
    ]
  ])

  all_route_table_ids = concat(
    [aws_route_table.public.id, aws_route_table.isolated.id],
    [for rt in aws_route_table.private : rt.id],
  )
}

# The single most consequential policy in the stage (step 3.4): an endpoint policy is an
# allow-list, so these two statements are the WHOLE of what this endpoint carries - anything
# else is denied at the endpoint. Statement 1 is the trusted-networks axis (9.1); statement 2
# is the carve-out the data-perimeter examples will not write for you (9.3): AWS's own
# service-owned buckets carry no aws:ResourceOrgID, so without it dnf, the agents, ECR pulls
# and JumpStart all hang. aws:ViaAWSService does not rescue them (9.4) - a dnf process is
# your own credential fetching an object.
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.all_route_table_ids

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowWithinOrganization"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:*"
        Resource  = "*"
        Condition = {
          StringEquals = { "aws:ResourceOrgID" = data.aws_organizations_organization.current.id }
        }
      },
      {
        Sid       = "AllowAwsOwnedServiceBuckets"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject", "s3:ListBucket"]
        Resource  = local.aws_bucket_arns
      },
    ]
  })

  tags = {
    Name = "awsds-${var.env}-s3-gateway"
  }
}

resource "aws_vpc_endpoint" "dynamodb" {
  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.region}.dynamodb"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = local.all_route_table_ids

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowWithinOrganization"
        Effect    = "Allow"
        Principal = "*"
        Action    = "dynamodb:*"
        Resource  = "*"
        Condition = {
          StringEquals = { "aws:ResourceOrgID" = data.aws_organizations_organization.current.id }
        }
      },
    ]
  })

  tags = {
    Name = "awsds-${var.env}-dynamodb-gateway"
  }
}
