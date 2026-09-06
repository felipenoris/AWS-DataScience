# The interface endpoints (step 8) - the metered heart of egress/: ~USD 0.010/h each, every
# hour the slice is up. The list is core + per-role extras (8.1-8.3), the AZ is ONE (D9,
# 8.5), private DNS is ON (8.5 - without it the SDKs keep resolving the public hostnames and
# the path silently leaves the VPC), and the SG is foundation/'s endpoint group (2.4).
#
# THESE IDS ANCHOR NOTHING (step 8.6, Lesson 3, INT-05): they are [E], new on every make up.
# The id a policy may name is foundation/'s gateway endpoint; the condition a policy may
# carry is aws:SourceVpc. The outputs repeat this warning so a reader two stages away meets
# it before the mistake.

data "aws_region" "current" {}

data "aws_organizations_organization" "current" {} # DescribeOrganization answers from any member account (measured, Stage 1b)

locals {
  # THE OPTIONAL GROUPS, ONE MAP, MEASURED AGAINST THE REGION'S OWN CATALOG on 2026-09-06 rather
  # than copied from a vendor page - `describe-vpc-endpoint-services` in us-west-2 was the source
  # for every name below, which is what 5.2's "measure rather than copy" asks for and what caught
  # `q` (the required list names it; **no such endpoint service exists in this Region**).
  #
  # EVERY `*-fips` SIBLING IS EXCLUDED ON PURPOSE. The catalog carries `bedrock-fips`,
  # `bedrock-runtime-fips`, `elasticmapreduce-fips` and more; none of them is the endpoint the
  # SDKs resolve unless a client is configured for FIPS, and adding one by pattern-match would be
  # a cent an hour for a path nothing takes.
  optional_services = {
    # The six enabled AmazonBedrock* blueprints both AUTHOR Bedrock objects and INVOKE them, and
    # the two halves are different services. `bedrock` is the control plane that
    # `AmazonBedrockGuardrail` (CreateGuardrail) and `AmazonBedrockEvaluation` (CreateEvaluationJob)
    # call; `bedrock-agent` is the control plane for agents, flows and prompts; the two `-runtime`
    # names are the invocation path. **The stage's own text lists three and omits `bedrock`** -
    # corrected here from the API split, and 6d measures which of the four are load-bearing.
    # Excluded and named so nobody adds them by resemblance: bedrock-agentcore*,
    # bedrock-data-automation*, bedrock-mantle.
    bedrock = ["bedrock", "bedrock-agent", "bedrock-agent-runtime", "bedrock-runtime"]

    # EmrServerless, the enabled blueprint. All seven measured present in the Region.
    # `emr-containers` is EMR-on-EKS - a CATEGORY 3 blueprint, deliberately not here - and
    # `emrwal.prod` belongs to EMR on EC2's write-ahead log.
    emr = [
      "emr-serverless",
      "emr-serverless-services.livy",
      "emr-serverless-services.sessions",
      "emr-serverless.dashboard",
      "emr-dashboard",
      "elasticmapreduce",
      "elasticmapreduce-services",
    ]

    # RESERVED AND EMPTY, WHICH IS A STATE AND NOT A STUB (user decision, 2026-09-06). `Workflows`
    # is a category-2 blueprint and Stage 10 builds orchestration - but the estate's decision is
    # **MWAA Serverless only**, and the catalog splits the two shapes: `airflow-serverless` against
    # the provisioned trio `airflow.api` / `airflow.env` / `airflow.ops`, plus `monitoring`, which
    # is not in core_services. Filling this in now would be choosing that question by accident.
    # The NAME is reserved so the day it is answered is one edit, and the empty list means a
    # `GROUPS=mwaa` today creates nothing rather than erroring - which is the honest behaviour for
    # a group that exists and has no content yet.
    mwaa = []
  }

  services = distinct(concat(
    var.core_services,
    var.extra_services,
    flatten([for g in var.optional_service_groups : local.optional_services[g]]),
  ))

  # The service NAME is regional and almost uniform - `com.amazonaws.<region>.<token>` -
  # with one measured exception (verification (i), answered 2026-08-15 from the region's
  # catalog, aws/egress.py 7): SageMaker Studio is `aws.sagemaker.<region>.studio`. The same
  # catalog run measured that every service both lists carry supports an endpoint POLICY, so
  # the document below is attached unconditionally.
  service_names = {
    for s in local.services :
    s => (
      s == "sagemaker.studio"
      ? "aws.sagemaker.${data.aws_region.current.region}.studio"
      : "com.amazonaws.${data.aws_region.current.region}.${s}"
    )
  }

  # Step 9's document for EVERY interface endpoint, one copy (Lesson 14) - the
  # trusted-networks axis: this network path serves THIS ORGANIZATION's principals and the
  # AWS services acting as themselves, nobody else. The shapes are the
  # data-perimeter-policy-examples baseline (9.2) - the second statement is the carve-out
  # everyone forgets: a service principal (a flow log delivering, a service writing logs)
  # carries no aws:PrincipalOrgID and would be denied by statement 1 alone.
  #
  # aws:ResourceOrgID is DELIBERATELY ABSENT here, and that is a reading, not an oversight:
  # through these endpoints pass calls whose RESOURCE is AWS-owned and org-less - ECR pulls
  # of public base images, SageMaker JumpStart artifacts - and the resource axis already has
  # its own control where it is load-bearing: the S3 gateway policy with its enumerated
  # allow-list (9.3), in foundation/. EG-1 (aws/egress.py) accepts either key by design.
  endpoint_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowOrganizationPrincipals"
        Effect    = "Allow"
        Principal = "*"
        Action    = "*"
        Resource  = "*"
        Condition = {
          StringEquals = { "aws:PrincipalOrgID" = data.aws_organizations_organization.current.id }
        }
      },
      {
        Sid       = "AllowAWSServicePrincipals"
        Effect    = "Allow"
        Principal = "*"
        Action    = "*"
        Resource  = "*"
        Condition = {
          Bool = { "aws:PrincipalIsAWSService" = "true" }
        }
      },
    ]
  })
}

resource "aws_vpc_endpoint" "interface" {
  for_each = local.service_names

  vpc_id              = var.vpc_id
  service_name        = each.value
  vpc_endpoint_type   = "Interface"
  subnet_ids          = [var.endpoint_subnet_id]
  security_group_ids  = [var.endpoint_security_group_id]
  private_dns_enabled = true
  policy              = local.endpoint_policy

  tags = {
    Name = "awsds-${var.env}-${each.key}"
  }
}
