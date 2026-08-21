# THE DOMAIN'S OWN ROLES (Stage 6 step 1.2).
#
# TWO, NOT THREE - and the third is named here so its absence reads as a decision. The SMUS
# role family in the live partition (measured 2026-08-21, `iam list-policies --scope AWS`) is:
#
#   SageMakerStudioDomainExecutionRolePolicy   the domain execution role - what the portal and
#                                              the catalog act as inside this account
#   SageMakerStudioDomainServiceRolePolicy     the service role - what DataZone itself uses
#   SageMakerStudioQueryExecutionRolePolicy    an ATHENA FEDERATION role: glue:GetConnection,
#                                              the Athena spill bucket, lambda:InvokeFunction
#                                              for a federated catalog. Nothing in this design
#                                              federates a query, so creating it would be a
#                                              principal nobody chose (Lesson 17). It arrives
#                                              the day a federated connection does.
#
# THE TRUST CONDITION IS THE CONFUSED-DEPUTY PAIR, and aws:SourceAccount is the half that
# matters: without it, a DataZone domain in ANY account could ask the service to assume these
# roles. The ArnLike on aws:SourceArn is deliberately absent from the EXECUTION role's trust:
# the role has to exist BEFORE the domain (aws_datazone_domain takes its ARN as an argument),
# so an ARN naming the domain id would make the two circular. The 0.0 reading of 2026-08-20
# confirms nothing else in the organization interferes: the RCP's
# EnforceOrgIdentitiesOnRoleAssumption carries BoolIfExists aws:PrincipalIsAWSService=false,
# which excludes the service, and the Data OU document names no iam:, datazone: or sts: action.
#
# sts:TagSession IS REQUIRED, not optional: DataZone assumes the execution role with session
# tags carrying the DataZone user id and project - the same tags Stage 6 step 3.2's
# remote-session deny reads on the other side (aws:PrincipalTag/datazone:userId). Omit it and
# the assume fails at sign-in, in a way that reads like an Identity Center problem.

data "aws_iam_policy_document" "domain_execution_trust" {
  statement {
    sid     = "DataZoneAssumesTheDomainExecutionRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "aws_iam_policy_document" "domain_service_trust" {
  statement {
    sid     = "DataZoneAssumesItsOwnServiceRole"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

module "domain_execution_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-studio-domain-execution"
  description          = "The SMUS domain execution role - what the portal and the SageMaker Catalog act as in this account (Stage 6 step 1.2)."
  assume_role_policy   = data.aws_iam_policy_document.domain_execution_trust.json
  permissions_boundary = null

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/SageMakerStudioDomainExecutionRolePolicy",
  ]
}

module "domain_service_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-studio-domain-service"
  description          = "The SMUS domain service role - what DataZone itself uses to operate the domain (Stage 6 step 1.2)."
  assume_role_policy   = data.aws_iam_policy_document.domain_service_trust.json
  permissions_boundary = null

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/SageMakerStudioDomainServiceRolePolicy",
  ]
}
