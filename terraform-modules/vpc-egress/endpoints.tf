# The interface endpoints (step 8) - the metered heart of egress/: ~USD 0.010/h each, every
# hour the slice is up. The list is core + per-role extras (8.1-8.3), the AZ is ONE (D9,
# 8.5), private DNS is ON (8.5 - without it the SDKs keep resolving the public hostnames and
# the path silently leaves the VPC), and the SG is foundation/'s endpoint group (2.4).
#
# These ids anchor nothing (step 8.6, Lesson 3, INT-05): they are [E], new on every make up.
# The id a policy may name is foundation/'s gateway endpoint; the condition a policy may
# carry is aws:SourceVpc. The outputs repeat this warning so a reader two stages away meets
# it before the mistake.

data "aws_region" "current" {}

data "aws_organizations_organization" "current" {} # DescribeOrganization answers from any member account (measured, Stage 1b)

locals {
  # The optional groups, one map, measured against the Region's own catalog on 2026-09-06 rather
  # than copied from a vendor page: `describe-vpc-endpoint-services` in us-west-2 was the source
  # for every name below (5.2, "measure rather than copy"). It caught `q` - the required list
  # names it, and no such endpoint service exists in this Region.
  #
  # Every `*-fips` sibling is excluded. The catalog carries `bedrock-fips`,
  # `bedrock-runtime-fips`, `elasticmapreduce-fips` and more; none of them is the endpoint the
  # SDKs resolve unless a client is configured for FIPS, and adding one by pattern-match would be
  # a cent an hour for a path nothing takes.
  optional_services = {
    # The six enabled AmazonBedrock* blueprints both author Bedrock objects and invoke them, and
    # the two halves are different services. `bedrock` is the control plane that
    # `AmazonBedrockGuardrail` (CreateGuardrail) and `AmazonBedrockEvaluation`
    # (CreateEvaluationJob) call; `bedrock-agent` is the control plane for agents, flows and
    # prompts; the two `-runtime` names are the invocation path. The stage's own text lists three
    # and omits `bedrock`; this list follows the API split, and 6d measures which of the four are
    # load-bearing. Excluded and named so nobody adds them by resemblance: bedrock-agentcore*,
    # bedrock-data-automation*, bedrock-mantle.
    bedrock = ["bedrock", "bedrock-agent", "bedrock-agent-runtime", "bedrock-runtime"]

    # The same service, a different consumer, and a narrower one (Stage 6e step 4.1). A coding
    # assistant in a space invokes a model and resolves an inference profile; it authors no
    # guardrail, no agent, no flow and no prompt. `bedrock-agent` and `bedrock-agent-runtime` are
    # two endpoints at ~USD 0.010/h each that its calls never reach.
    #
    # It is a SECOND GROUP rather than a narrowing of the one above, because the group above has
    # its own consumer - the six enabled AmazonBedrock* blueprints, whose control-plane calls do
    # reach the agent endpoints. Narrowing it would have taken those away for a reason that has
    # nothing to do with them (Lesson 51: two intents sharing one list stay identical until they
    # must differ, and then a change made for one silently makes it for the other).
    #
    # The two overlap on `bedrock` and `bedrock-runtime`, and naming both groups in one apply is
    # legal: `local.service_names` is a map keyed by the short name, so the overlap collapses to
    # one endpoint rather than colliding.
    "bedrock-llm" = ["bedrock", "bedrock-runtime"]

    # EmrServerless, the enabled blueprint. All seven measured present in the Region.
    # `emr-containers` is EMR-on-EKS - a category 3 blueprint, not here - and `emrwal.prod`
    # belongs to EMR on EC2's write-ahead log.
    emr = [
      "emr-serverless",
      "emr-serverless-services.livy",
      "emr-serverless-services.sessions",
      "emr-serverless.dashboard",
      "emr-dashboard",
      "elasticmapreduce",
      "elasticmapreduce-services",
    ]

    # Reserved and empty, which is a state and not a stub (the user's decision, 2026-09-06).
    # `Workflows` is a category-2 blueprint and Stage 10 builds orchestration, but the estate's
    # decision is MWAA Serverless only, and the catalog splits the two shapes:
    # `airflow-serverless` against the provisioned trio `airflow.api` / `airflow.env` /
    # `airflow.ops`, plus `monitoring`, which is not in core_services. Filling this in now would
    # choose that question by accident. The name is reserved so the day it is answered is one
    # edit, and the empty list means a `GROUPS=mwaa` today creates nothing rather than erroring.
    mwaa = []
  }

  services = distinct(concat(
    var.core_services,
    var.extra_services,
    flatten([for g in var.optional_service_groups : local.optional_services[g]]),
  ))

  # The service name is regional and almost uniform - `com.amazonaws.<region>.<token>` -
  # with one measured exception (verification (i), answered 2026-08-15 from the region's
  # catalog, aws/egress.py 7): SageMaker Studio is `aws.sagemaker.<region>.studio`. The same
  # catalog run measured that every service both lists carry supports an endpoint policy, so
  # the document below is attached unconditionally.
  service_names = {
    for s in local.services :
    s => (
      s == "sagemaker.studio"
      ? "aws.sagemaker.${data.aws_region.current.region}.studio"
      : "com.amazonaws.${data.aws_region.current.region}.${s}"
    )
  }

  # Step 9's document for every interface endpoint, one copy (Lesson 14) - the
  # trusted-networks axis: this network path serves this organization's principals and the
  # AWS services acting as themselves, nobody else. The shapes are the
  # data-perimeter-policy-examples baseline (9.2). The second statement is the carve-out
  # everyone forgets: a service principal (a flow log delivering, a service writing logs)
  # carries no aws:PrincipalOrgID and would be denied by statement 1 alone.
  #
  # aws:ResourceOrgID is absent here, and that is a reading rather than an oversight: through
  # these endpoints pass calls whose resource is AWS-owned and org-less - ECR pulls of public
  # base images, SageMaker JumpStart artifacts - and the resource axis has its own control where
  # it is load-bearing, the S3 gateway policy with its enumerated allow-list (9.3), in
  # foundation/. EG-1 (aws/egress.py) accepts either key by design.
  #
  # NARROWING IT PER ENDPOINT, on the ACTION axis and no other (Stage 6e step 4.4). A caller may
  # name a short service in `endpoint_action_scopes` and the two statements below carry that list
  # instead of `*` for that endpoint alone. What it buys is a second, independent statement of
  # which calls may traverse this door: on the Bedrock pair, an invocation may and
  # `PutAccountDataRetention` or `PutModelInvocationLoggingConfiguration` may not, whatever any
  # identity policy says.
  #
  # THE RESOURCE AXIS IS DELIBERATELY NOT NARROWED HERE, and that is the interesting half. Scoping
  # the endpoint to named model ARNs would be a second copy of a list whose first copy is the IAM
  # grant, in a different slice, with nothing comparing them - one intent in two places, which
  # diverges (Lesson 33), and the failure would be an invocation refused at the network layer for a
  # model somebody added to the grant. The action list does not have that problem: it is a property
  # of the service, not of this estate's choices, and it changes when AWS adds an API rather than
  # when a decision is taken here.
  # `null`, not `["*"]`, for an endpoint nobody named. The difference is not cosmetic: `["*"]`
  # would emit `"Action": ["*"]` where every endpoint has carried `"Action": "*"` since step 9,
  # so a caller adopting this version would see a policy diff on all eighteen endpoints for a
  # change that means nothing. An unscoped endpoint's document must come out BYTE-IDENTICAL, which
  # is also what the D11 cycle checks across a `make down` / `make up` (Stage 3's Validation).
  endpoint_action_scope = {
    for short, _svc in local.service_names :
    short => lookup(var.endpoint_action_scopes, short, null)
  }

  endpoint_policies = {
    for short, _svc in local.service_names :
    short => jsonencode({
      Version = "2012-10-17"
      Statement = [
        for st in jsondecode(local.endpoint_policy).Statement :
        local.endpoint_action_scope[short] == null ? st : merge(st, { Action = local.endpoint_action_scope[short] })
      ]
    })
  }

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
  policy              = local.endpoint_policies[each.key]

  tags = {
    Name = "${local.name_prefix}-${each.key}"
  }
}
