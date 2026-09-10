# The two roles a blueprint configuration names (Stage 6 step 2.1, the associated-accounts
# documentation).
#
# They are ours rather than the console's. The console's "enable blueprints" flow offers to
# create both, with names carrying the account id or the domain id; letting it would be
# Lesson 17, and would put two roles with real provisioning power outside Terraform in an
# account this repository otherwise owns completely. So they are declared here, named by the
# convention (awsds-<env>-<component>), and the AWS managed policies are attached rather than
# copied: binding to contents is impossible for a policy AWS revises, so the ARN is the contract
# and the revision is AWS's (Lesson 23's case, inverted).
#
# The managed policy ARNs were measured, not remembered (2026-08-21, iam list-policies against
# the live partition). Two plausible names that do not exist:
# SageMakerStudioProjectRoleForManageAccessPolicy, AmazonDataZoneSageMakerProvisioningPolicy.
# The two that do exist are below.
#
# Neither carries a permissions boundary, the IAM convention's one legitimate null
# (terraform-modules/iam-role's own comment, Lesson 18): they are service roles authored by
# the identity that authors boundaries, and a boundary on the provisioning role would cap what
# DataZone can build in this account - a control aimed at the wrong object. The project roles
# get the boundary in boundary.tf, imposed through the blueprint configuration.

data "aws_iam_policy_document" "provisioning_trust" {
  statement {
    sid     = "DataZoneAndCloudFormationProvisionHere"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com", "cloudformation.amazonaws.com"]
    }

    # The confused-deputy guard. aws:SourceAccount on a service-principal trust names the
    # account of the resource the service acts on behalf of - the DataZone domain's account.
    # Naming data.aws_caller_identity.current (the member account) here makes both roles
    # unassumable: the documented trust of AmazonSageMakerProvisioning-<domainAccountId> is
    # SourceAccount = domain_account, the role's name carries the domain account, and
    # CloudTrail in the member account showed no datazone AssumeRole ever (2026-08-22) - a
    # cross-account service denial is invisible in the target account's trail, which is why
    # three deployment failures were attributed before this one (the wizard-field ladder), and
    # the teardown's "Failed to remove EMR EKS IAM roles" is this trust, not those fields. The
    # sample never caught it: single-account, the two values coincide there.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.domain_account_id]
    }
  }
}

data "aws_iam_policy_document" "manage_access_trust" {
  statement {
    sid     = "DataZoneManagesAccessHere"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com"]
    }

    # Same guard as the provisioning trust above.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [var.domain_account_id]
    }
  }
}

module "provisioning_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-smus-provisioning"
  description          = "The role DataZone/CloudFormation provisions SMUS project environments through, in this account (Stage 6 step 2.1)."
  assume_role_policy   = data.aws_iam_policy_document.provisioning_trust.json
  permissions_boundary = null

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/SageMakerStudioProjectProvisioningRolePolicy",
  ]
}

module "manage_access_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-smus-manage-access"
  description          = "The role DataZone fulfils catalog subscriptions with, in this account - it writes the Lake Formation grants a subscription approval becomes (Stage 6 verification (xiv))."
  assume_role_policy   = data.aws_iam_policy_document.manage_access_trust.json
  permissions_boundary = null

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonDataZoneSageMakerManageAccessRolePolicy",
  ]
}

resource "aws_iam_policy" "project_boundary" {
  name        = "awsds-${var.env}-project-boundary"
  description = "D13's permissions boundary for the project roles DataZone authors (Stage 6 step 2.1; name contract ./aws/studio.py US-8)."
  policy      = data.aws_iam_policy_document.project_boundary.json
}
