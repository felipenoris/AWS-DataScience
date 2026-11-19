# The notebook grant for SMUS project roles (Stage 17 decision 7 (a)): the calls a member's notebook
# needs on what it creates and a workflow's operators never create. A workflow's operators' statements
# are sandbox/workflows/'s. The grant holds one statement per refusal measured: the model package
# group's tag. An endpoint configuration, an endpoint, a pipeline or an MLflow App joins it as a
# statement of its own once a refusal is measured on it.
#
# CreateModelPackageGroup with tags is also authorized as sagemaker:AddTags. The blueprint's
# SageMakerCreatePermissions (SageMakerStudioProjectRoleMachineLearningPolicy v48) admits the create
# where the group carries the caller's AmazonDataZoneProject tag, and its SageMakerTagPermissions
# excludes every AmazonDataZone* key, so a project role cannot create the group the create condition
# asks for: the tagged create reads allowed and its AddTags implicitDeny, by simulation as
# eighth-experimentation's and app-ml-dev's roles, the organization's policies included (2026-11-19).
# This statement allows that one tag with the caller's own value, alone, on a group that carries no
# project tag or already the caller's, so a group of another project cannot be claimed. A group created
# untagged by a principal outside SMUS can be claimed by the first listed project role that tags it;
# Sandbox held no model package group on 2026-11-19. A create that carries a second tag beside the
# project's is refused, since the blueprint's tag statement admits no AmazonDataZone* key and this one
# admits that key alone.
#
# The boundary is untouched: awsds-sandbox-project-boundary denies no AddTags.

# The description names the first statement only: it forces a new policy when it changes, and the
# comment above each statement is where the grant is described.
resource "aws_iam_policy" "ml" {
  name        = "awsds-${var.env}-ml"
  description = "Tag a SageMaker model package group with the caller's project, so a notebook can create the group the blueprint's create condition asks for. Stage 17 decision 7 (a); attached to SMUS project roles by this slice."
  policy      = data.aws_iam_policy_document.ml.json
}

data "aws_iam_policy_document" "ml" {
  statement {
    sid       = "TagAModelPackageGroupWithTheCallersProject"
    effect    = "Allow"
    actions   = ["sagemaker:AddTags"]
    resources = [local.model_package_groups]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "StringEqualsIfExists"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }

    condition {
      test     = "ForAllValues:StringEquals"
      variable = "aws:TagKeys"
      values   = ["AmazonDataZoneProject"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "project" {
  for_each = toset(var.project_roles)

  role       = data.aws_iam_role.project[each.value].name
  policy_arn = aws_iam_policy.ml.arn

  lifecycle {
    # A role outside the D13 boundary is not a project role this estate governs, whatever its name.
    precondition {
      condition     = try(data.aws_iam_role.project[each.value].permissions_boundary, "") != "" && endswith(try(data.aws_iam_role.project[each.value].permissions_boundary, ""), ":policy/${local.boundary_name}")
      error_message = "${each.value} does not carry the ${local.boundary_name} permissions boundary. A SMUS project role always does (INT-15); a role that does not is not one."
    }
  }
}
