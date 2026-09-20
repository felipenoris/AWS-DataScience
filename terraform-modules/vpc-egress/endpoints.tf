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
    # The agent pair, and ONLY the agent pair since 2026-09-12. `bedrock` and `bedrock-runtime`
    # moved into the caller's always-on list, where Stage 6e's assistant needs them every session:
    # an optional group is per apply, and `make up` without the flag destroys what it created, so a
    # permanent consumer cannot live behind one.
    #
    # What is left here is what only the blueprints use. The six enabled AmazonBedrock* blueprints
    # both author Bedrock objects and invoke them, and the two halves are different services:
    # `bedrock` is the control plane that `AmazonBedrockGuardrail` (CreateGuardrail) and
    # `AmazonBedrockEvaluation` (CreateEvaluationJob) call and `bedrock-runtime` is the invocation
    # path - both now always on - while `bedrock-agent` is the control plane for agents, flows and
    # prompts and `bedrock-agent-runtime` invokes them. Excluded and named so nobody adds them by
    # resemblance: bedrock-agentcore*, bedrock-data-automation*, bedrock-mantle.
    #
    # A CALLER THAT DOES NOT CARRY THE PAIR GETS A HALF-WORKING GROUP. This list is the module's
    # and the always-on half is the caller's, which is the seam this restructure introduced: in an
    # account where `bedrock` is not in extra_services, `GROUPS=bedrock` now creates two endpoints
    # that have no control plane to talk to. `sandbox/egress` is the only caller that names any of
    # them today.
    bedrock = ["bedrock-agent", "bedrock-agent-runtime"]

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

    # Stage 5b step 1.10 - the Redshift Serverless warehouse's API door, added 2026-09-20 because
    # the plan did not have one (the user found it by asking, before anything was built). Without
    # it every Redshift API call from a space leaves through the proxy as a public request: the
    # same WRONG DOOR Stage 6e found for `bedrock-runtime`, which the compute plane's
    # `.amazonaws.com` entry admits and the image's NO_PROXY did not cover.
    #
    # ONE TOKEN AND NOT THREE, and each exclusion is a reading. All six `redshift*` services exist
    # in this Region (measured 2026-09-20 from the Region's own catalog):
    #
    #   redshift-serverless        HERE. `GetCredentials` is layer 2 of Stage 6h and the whole
    #                              IAM-credentials path; `GetWorkgroup` and `ListTagsForResource`
    #                              ride with it. This design's API is `redshift-serverless`,
    #                              never `redshift`.
    #   redshift-data              NOT here, and it is the one to reconsider first. A plain JDBC
    #                              connection over 5439 does not touch the Data API at all, so the
    #                              entry is decided by 6h's credential answer rather than added on
    #                              spec. Note that the Data API is how this repository's own
    #                              instruments reach the database from a laptop - but a laptop is
    #                              not in the VPC, so that use needs no endpoint either.
    #   redshift                   NOT here. The PROVISIONED-cluster control plane, which 5b 3.1
    #                              denies organization-wide. AWS's own SMUS access-role sample
    #                              lists `redshift:GetClusterCredentials`/`DescribeClusters` beside
    #                              the serverless pair, so whether the portal calls it anyway is
    #                              read from CloudTrail at 6h 3.5 rather than guessed. An endpoint
    #                              bought on suspicion is 0.010/h for the whole session.
    #   the three *-fips siblings  NOT here, for the reason every other fips sibling is excluded.
    #
    # THE 5439 DATA PATH NEEDS NO ENDPOINT AT ALL. The workgroup's own host resolves to ITS ENIs in
    # the compute VPC (measured 5b 1.9: `10.20.54.29` and `10.20.77.126`, replaced on every
    # re-create), so what admits a space is the warehouse's security group, not PrivateLink.
    #
    # It looks like a DNS collision and it is not. The API's private name is
    # `redshift-serverless.<region>.amazonaws.com`; the workgroup's own host is
    # `<workgroup>.<account>.<region>.redshift-serverless.amazonaws.com`. The region sits BEFORE the
    # service token in one and after it in the other, so they are different subtrees and this
    # endpoint's private DNS does not shadow the workgroup's address.
    redshift = ["redshift-serverless"]
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
  # instead of `*` for that endpoint alone: a second, independent statement of which calls may
  # traverse this door, under the same organization condition.
  #
  # SCOPE ONLY A DOOR WHOSE PURPOSE IS UNAMBIGUOUS, and the Bedrock pair is the worked example.
  # `bedrock-runtime` carries invocation and nothing else for any consumer, so a list of invoke
  # actions on it is a statement about the service rather than about one caller. `bedrock` is the
  # control plane: its API surface is long, it grows, and the six SMUS AmazonBedrock* blueprints
  # call it for things a coding assistant never does. A list written for one of those consumers
  # silently refuses the other, with no denial that names this policy - which is why
  # `sandbox/egress` scopes the runtime endpoint and leaves the control plane open.
  #
  # THE RESOURCE AXIS IS DELIBERATELY NOT NARROWED HERE, and that is the interesting half. Scoping
  # the endpoint to named model ARNs would be a second copy of a list whose first copy is the IAM
  # grant, in a different slice, with nothing comparing them - one intent in two places, which
  # diverges (Lesson 33), and the failure would be an invocation refused at the network layer for a
  # model somebody added to the grant. The action list does not have that problem: it is a property
  # of the service, not of this estate's choices, and it changes when AWS adds an API rather than
  # when a decision is taken here.
  #
  # An endpoint nobody named takes `local.endpoint_policy` itself - the same string rather than a
  # re-encoding of it - so its document stays byte-identical to what every endpoint has carried
  # since step 9, which is what the D11 cycle compares across a `make down` / `make up` (Stage 3's
  # Validation). Emitting `"Action": ["*"]` there would be a policy diff on every unscoped endpoint
  # for a change that means nothing.
  #
  # The two documents are built separately and selected by `lookup`, never merged under a
  # conditional. A conditional has to unify `Action` across its branches - `"*"` on one side, a list
  # on the other - and the mismatch is invisible to `terraform validate`: a statement's type stays
  # dynamic until the keys of `local.service_names` are known, which happens at plan. Validate
  # answered `Success!` on the caller for both versions that shipped it (Lesson 54).
  scoped_policies = {
    for short, actions in var.endpoint_action_scopes :
    short => jsonencode({
      Version = "2012-10-17"
      Statement = [
        for st in jsondecode(local.endpoint_policy).Statement : merge(st, { Action = actions })
      ]
    })
  }

  endpoint_policies = {
    for short, _svc in local.service_names :
    short => lookup(local.scoped_policies, short, local.endpoint_policy)
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
