# THE TWO ROLES A BLUEPRINT CONFIGURATION NAMES (Stage 6 step 2.1, the associated-accounts
# documentation).
#
# WHY THEY ARE OURS AND NOT THE CONSOLE'S. The console's "enable blueprints" flow offers to
# create both, with names carrying the account id or the domain id. Letting it would be
# Lesson 17 - a service that "sets itself up" creates principals nobody chose - and it would
# put two roles with real provisioning power outside Terraform in an account this repository
# otherwise owns completely. So they are declared here, named by the convention
# (awsds-<env>-<component>), and the AWS managed policies are attached rather than copied:
# binding to CONTENTS is impossible for a policy AWS revises, so the ARN is the contract and
# the revision is AWS's (the opposite of Lesson 23's case, and for the same reason).
#
# THE MANAGED POLICY ARNs WERE MEASURED, NOT REMEMBERED (2026-08-21, iam list-policies against
# the live partition). The names that read like they should exist and do NOT are worth having
# written down, because each is a plausible guess:
# SageMakerStudioProjectRoleForManageAccessPolicy, AmazonDataZoneSageMakerProvisioningPolicy.
# The two that do exist are below.
#
# NEITHER CARRIES A PERMISSIONS BOUNDARY, and that is the IAM convention's one legitimate null
# (terraform-modules/iam-role's own comment, Lesson 18): they are service roles authored by
# the identity that authors boundaries, and a boundary on the provisioning role would cap what
# DataZone can build in this account - a control aimed at the wrong object. What the project
# roles get is the boundary in boundary.tf, imposed through the blueprint configuration.

data "aws_iam_policy_document" "provisioning_trust" {
  statement {
    sid     = "DataZoneAndCloudFormationProvisionHere"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["datazone.amazonaws.com", "cloudformation.amazonaws.com"]
    }

    # THE CONFUSED-DEPUTY PAIR. Without aws:SourceAccount any DataZone domain in any account
    # could ask the service to assume this role; the ArnLike narrows it to a domain, and the
    # domain id is deliberately a wildcard because this role is created BEFORE the domain
    # exists (pass 1 precedes pass 2) and pinning it would make the two applies circular.
    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
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

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
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
