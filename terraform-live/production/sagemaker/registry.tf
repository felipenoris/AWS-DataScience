# Stage 9 step 3.2 - the Model Registry: one package group per application or model family, each with
# its resource policy written now rather than improvised in Stage 10 (D28 item 6).
#
# The registry is the promotion boundary: a version is approved here, on the far side of the gate
# from the person who trained it. A task registers every family's versions, as the deployment
# project's role (Stage 17 decision 16 (b)), and a family's policy names two readers and one writer:
#
#   approve           awsds-deploy-prod alone (UpdateModelPackage); no Staging reader, since the model
#                     reaches each account in the release's bundle
#   read the status   the Sandbox readers decision 10 names, matched by aws:PrincipalArn in an account
#                     the D35 map names, so no statement carries arn:aws:iam::*:
#
# The deployment project's role registers by its identity policy (production/studio/workflows.tf).
#
# The Sandbox readers are two principals, because a data scientist reaches AWS as either: the
# persona's reserved role from a laptop or the console, and the project role from a space or a
# workflow. Each needs its own side's allow as well: the persona's ReadSageMakerStatus in identity/sso/,
# and the project role's in the SMUS managed policy (SageMakerCrossAccountPermissions, v44, read on
# AWS's page 2026-10-16: DescribeModelPackage, DescribeModelPackageGroup and ListModelPackages on any
# resource of another account). Step 3.4 measures both.
#
# Inside this account a resource policy constrains nobody an identity policy already admits, and the
# infrastructure user that writes this one is outside every claim it makes (Lesson 18).
#
# A package group costs nothing at rest. When the registry first holds a version, re-read EXC-11
# (./aws/catalog.py CT-6), whose trigger is the Model Registry being used.

locals {
  # Each family by name, with its group's description. SageMaker has no call that updates a group,
  # so a changed description replaces the group.
  model_families = {
    "app-ml" = {
      description = "app-ml's model versions: registered by a task as the deployment project's role, approved by the Production deploy role alone (Stage 17 decision 16 (b))"
    }
  }

  deploy_prod_arn    = data.terraform_remote_state.foundation.outputs.deploy_role_arns[var.account_folder]
  sandbox_account_id = data.aws_caller_identity.sandbox.account_id

  status_reader_patterns = [
    "arn:${local.partition}:iam::${local.sandbox_account_id}:role/aws-reserved/sso.amazonaws.com/*/AWSReservedSSO_DataScientistAccess_*",
    "arn:${local.partition}:iam::${local.sandbox_account_id}:role/datazone_usr_role_*",
  ]

  # The status readers' statement, one per family.
  read_the_status_from_sandbox = {
    for family, group in aws_sagemaker_model_package_group.this : family => {
      Sid       = "ReadTheStatusFromSandbox"
      Effect    = "Allow"
      Principal = { AWS = "arn:${local.partition}:iam::${local.sandbox_account_id}:root" }
      Action = [
        "sagemaker:DescribeModelPackage",
        "sagemaker:DescribeModelPackageGroup",
        "sagemaker:ListModelPackages",
      ]
      Resource = [
        group.arn,
        "arn:${local.partition}:sagemaker:${var.region}:${local.account_id}:model-package/${group.model_package_group_name}/*",
      ]
      Condition = {
        ArnLike = { "aws:PrincipalArn" = local.status_reader_patterns }
      }
    }
  }
}

resource "aws_sagemaker_model_package_group" "this" {
  for_each = local.model_families

  model_package_group_name        = "awsds-${var.env}-model-${each.key}"
  model_package_group_description = each.value.description

  tags = {
    Name = "awsds-${var.env}-model-${each.key}"
  }
}

# A task registers: the deploy role approves alone, and no Staging statement.
resource "aws_sagemaker_model_package_group_policy" "task_registers" {
  for_each = aws_sagemaker_model_package_group.this

  model_package_group_name = each.value.model_package_group_name

  resource_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ApproveAsTheProductionDeployRole"
        Effect    = "Allow"
        Principal = { AWS = local.deploy_prod_arn }
        Action    = ["sagemaker:UpdateModelPackage"]
        Resource  = "arn:${local.partition}:sagemaker:${var.region}:${local.account_id}:model-package/${each.value.model_package_group_name}/*"
      },
      local.read_the_status_from_sandbox[each.key],
    ]
  })
}

# -------------------------------------------------- the approval notification (Stage 10 step 5.3)
#
# Every state change of a model package in this account, to the account's alerts topic (Stage 8
# decision 5): a registration, an approval, a rejection. The pattern names no group, so a package
# registered outside this slice's groups is heard too. SageMaker sends its own events to the
# default bus, which a rule in the ENABLED state receives (OR-4 reads that state), and it may send
# several for one change (AWS's page on SageMaker's EventBridge events), so duplicates are expected.
# The rule's one target is the alerts topic. No chain starts on an approval: app-ml's chain app-ml-score
# serves the approved version from its next run, started by its schedule or by the operator (Stage 17
# step 9.7).
resource "aws_cloudwatch_event_rule" "model_approval" {
  name        = "awsds-${var.env}-model-approval"
  description = "Every SageMaker Model Package State Change in this account (Stage 10 step 5.3, D28 item 6)"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source        = ["aws.sagemaker"]
    "detail-type" = ["SageMaker Model Package State Change"]
  })

  tags = {
    Name       = "awsds-${var.env}-model-approval"
    CostCenter = "stage-10"
  }
}

# The message names the package and its two statuses and leaves the record in the registry. No path
# below is free text the caller chooses (ApprovalDescription is), because EventBridge does not escape
# an extracted value.
resource "aws_cloudwatch_event_target" "model_approval" {
  rule      = aws_cloudwatch_event_rule.model_approval.name
  target_id = "alerts-topic"
  arn       = data.terraform_remote_state.foundation.outputs.alerts_topic_arn

  input_transformer {
    input_paths = {
      time     = "$.time"
      group    = "$.detail.ModelPackageGroupName"
      version  = "$.detail.ModelPackageVersion"
      approval = "$.detail.ModelApprovalStatus"
      status   = "$.detail.ModelPackageStatus"
      package  = "$.detail.ModelPackageArn"
      event_id = "$.id"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: a model package changed state."
      "When: <time>"
      "Group: <group>, version <version>"
      "Approval status: <approval>"
      "Package status: <status>"
      "Package: <package>"
      "Event id: <event_id>"
      "The full record stays in the registry (DescribeModelPackage)."
    EOT
    )
  }
}
