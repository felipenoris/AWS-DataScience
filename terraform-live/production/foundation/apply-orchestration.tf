# apply-orchestration.tf - Stage 8 step 4.1's orchestration grant: what this account's deploy role
# calls when the pipeline applies <folder>/orchestration/, and the release job's copy into the
# definitions home and its seed of the inbox (Stage 10 steps 1.5 and 2.4, decision 20 (d)). Stage 10
# step 1.5 holds the enumeration; these two documents are its code.
#
# Two customer-managed policies the infrastructure user attaches, not an inline document: a role's
# inline documents share 10,240 characters and a managed policy holds 6,144, and the grant measured
# 7,836 in Staging's plan on 2026-10-22, where the role's inline documents would have totalled 12,483.
# The split follows the content: the resources the slice creates, and the roles, data and logs they
# use.
#
# The deploy role's ceiling admits iam:CreateRole and the role-policy writes only on a role carrying
# awsds-<env>-app-boundary (app-boundary.tf); every other role action is scoped here by name. The
# statements one account adds are apply_orchestration_in_this_account's: deploy-role.tf's in Staging,
# deploy-anchors.tf's in Production.
#
# The same file in staging/foundation/ and production/foundation/, byte for byte
# (./scripts/check-copies.py).

locals {
  orchestration_policies = {
    resources = {
      description = "Stage 8 step 4.1 - the deploy role's apply of the orchestration slice: the workflows, the state machines, schedules and rules, and the workers' security group (Stage 10 step 1.5)"
      document    = data.aws_iam_policy_document.orchestration_resources.json
    }
    access = {
      description = "Stage 8 step 4.1 - the deploy role's apply of the orchestration slice and the release job's copy: the application roles and their PassRole, the release's tree and the inbox, the data key and the log groups (Stage 10 step 1.5)"
      document    = data.aws_iam_policy_document.orchestration_access.json
    }
  }
}

# IAM has no call that changes a managed policy's description: a change plans its replacement.
resource "aws_iam_policy" "orchestration" {
  for_each = local.orchestration_policies

  name        = "awsds-${var.env}-deploy-orchestration-${each.key}"
  description = each.value.description
  policy      = each.value.document

  tags = merge(local.deploy_anchor_tags, {
    Name = "awsds-${var.env}-deploy-orchestration-${each.key}"
  })
}

resource "aws_iam_role_policy_attachment" "orchestration" {
  for_each = aws_iam_policy.orchestration

  role       = module.deploy_role.role_name
  policy_arn = each.value.arn
}

# ----------------------------------------------------------- the resources the slice creates
data "aws_iam_policy_document" "orchestration_resources" {
  # checkov:skip=CKV_AWS_111:Cloud Control, CreateWorkflow, ListWorkflows, ValidateStateMachineDefinition and the Describe calls take no resource narrower than "*"; every other write names this account's resources by name or by pattern
  # checkov:skip=CKV_AWS_356:idem
  source_policy_documents = [data.aws_iam_policy_document.apply_orchestration_in_this_account.json]

  # Cloud Control's IAM actions carry the cloudformation: prefix and take no resource (its security
  # page).
  statement {
    sid    = "CloudControl"
    effect = "Allow"
    actions = [
      "cloudformation:CreateResource",
      "cloudformation:DeleteResource",
      "cloudformation:GetResource",
      "cloudformation:GetResourceRequestStatus",
      "cloudformation:ListResources",
      "cloudformation:UpdateResource",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "CreateAndListWorkflows"
    effect    = "Allow"
    actions   = ["airflow-serverless:CreateWorkflow", "airflow-serverless:ListWorkflows"]
    resources = ["*"]
  }

  statement {
    sid    = "ManageTheWorkflows"
    effect = "Allow"
    actions = [
      "airflow-serverless:DeleteWorkflow",
      "airflow-serverless:GetWorkflow",
      "airflow-serverless:ListTagsForResource",
      "airflow-serverless:ListWorkflowVersions",
      "airflow-serverless:TagResource",
      "airflow-serverless:UntagResource",
      "airflow-serverless:UpdateWorkflow",
    ]
    resources = ["arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/awsds-${var.env}-wf-*"]
  }

  statement {
    sid    = "TheStateMachines"
    effect = "Allow"
    actions = [
      "states:CreateStateMachine",
      "states:DeleteStateMachine",
      "states:DescribeStateMachine",
      "states:ListStateMachineVersions",
      "states:ListTagsForResource",
      "states:TagResource",
      "states:UntagResource",
      "states:UpdateStateMachine",
    ]
    resources = ["arn:${local.partition}:states:${local.region_account}:stateMachine:awsds-${var.env}-chain-*"]
  }

  # The aws provider validates a new or changed definition while it plans a state machine, at the apply
  # too, and fails on any error from the call (stateMachineDefinitionValidate, v6.70.0). The action
  # takes no resource. Read in Staging's trail of Stage 8 3.8 (2026-10-23), the simulator refusing it
  # to both deploy roles on 2026-10-24.
  statement {
    sid       = "ValidateTheChainDefinitions"
    effect    = "Allow"
    actions   = ["states:ValidateStateMachineDefinition"]
    resources = ["*"]
  }

  statement {
    sid    = "TheSchedules"
    effect = "Allow"
    actions = [
      "scheduler:CreateSchedule",
      "scheduler:CreateScheduleGroup",
      "scheduler:DeleteSchedule",
      "scheduler:DeleteScheduleGroup",
      "scheduler:GetSchedule",
      "scheduler:GetScheduleGroup",
      "scheduler:ListTagsForResource",
      "scheduler:TagResource",
      "scheduler:UntagResource",
      "scheduler:UpdateSchedule",
    ]
    resources = [
      "arn:${local.partition}:scheduler:${local.region_account}:schedule-group/awsds-${var.env}-chains",
      "arn:${local.partition}:scheduler:${local.region_account}:schedule/awsds-${var.env}-chains/*",
    ]
  }

  statement {
    sid    = "TheRules"
    effect = "Allow"
    actions = [
      "events:DeleteRule",
      "events:DescribeRule",
      "events:DisableRule",
      "events:EnableRule",
      "events:ListTagsForResource",
      "events:ListTargetsByRule",
      "events:PutRule",
      "events:PutTargets",
      "events:RemoveTargets",
      "events:TagResource",
      "events:UntagResource",
    ]
    resources = [
      "arn:${local.partition}:events:${local.region_account}:rule/awsds-${var.env}-wf-*",
      "arn:${local.partition}:events:${local.region_account}:rule/awsds-${var.env}-chain-*",
      "arn:${local.partition}:events:${local.region_account}:rule/awsds-${var.env}-inbox-*",
    ]
  }

  # The workers' group, awsds-<env>-wf-workers: created with its Name tag, then changed only through
  # it. A rule created with tags is also a security-group-rule resource of the same calls.
  statement {
    sid       = "CreateTheWorkersGroup"
    effect    = "Allow"
    actions   = ["ec2:CreateSecurityGroup"]
    resources = ["arn:${local.partition}:ec2:${local.region_account}:security-group/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/Name"
      values   = ["awsds-${var.env}-wf-workers"]
    }
  }

  statement {
    sid       = "CreateTheWorkersGroupInAVpc"
    effect    = "Allow"
    actions   = ["ec2:CreateSecurityGroup"]
    resources = ["arn:${local.partition}:ec2:${local.region_account}:vpc/*"]
  }

  statement {
    sid    = "ChangeTheWorkersGroup"
    effect = "Allow"
    actions = [
      "ec2:AuthorizeSecurityGroupEgress",
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:DeleteSecurityGroup",
      "ec2:RevokeSecurityGroupEgress",
      "ec2:RevokeSecurityGroupIngress",
    ]
    resources = ["arn:${local.partition}:ec2:${local.region_account}:security-group/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Name"
      values   = ["awsds-${var.env}-wf-workers"]
    }
  }

  statement {
    sid       = "TheWorkersGroupsRules"
    effect    = "Allow"
    actions   = ["ec2:AuthorizeSecurityGroupEgress", "ec2:AuthorizeSecurityGroupIngress"]
    resources = ["arn:${local.partition}:ec2:${local.region_account}:security-group-rule/*"]
  }

  statement {
    sid     = "TagAtCreation"
    effect  = "Allow"
    actions = ["ec2:CreateTags"]
    resources = [
      "arn:${local.partition}:ec2:${local.region_account}:security-group/*",
      "arn:${local.partition}:ec2:${local.region_account}:security-group-rule/*",
    ]

    condition {
      test     = "StringEquals"
      variable = "ec2:CreateAction"
      values   = ["AuthorizeSecurityGroupEgress", "AuthorizeSecurityGroupIngress", "CreateSecurityGroup"]
    }
  }

  statement {
    sid    = "DescribeTheNetwork"
    effect = "Allow"
    actions = [
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeSecurityGroupRules",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeSubnets",
      "ec2:DescribeVpcs",
    ]
    resources = ["*"]
  }
}

# ------------------------------------------------- the roles, data and logs those resources use
data "aws_iam_policy_document" "orchestration_access" {
  # checkov:skip=CKV_AWS_111:the log-delivery calls and kms:ListAliases take no resource narrower than "*"; every other write names this account's resources by name or by pattern
  # checkov:skip=CKV_AWS_356:idem
  # checkov:skip=CKV_AWS_109:logs:PutResourcePolicy, the vended log delivery's, takes no resource; the role actions are scoped by name to awsds-<env>-wf-* and awsds-<env>-chain-*
  # checkov:skip=CKV_AWS_110:idem - and the deploy role's ceiling holds CreateRole and the role-policy writes to roles carrying the application ceiling
  statement {
    sid     = "CreateTheApplicationRoles"
    effect  = "Allow"
    actions = ["iam:CreateRole", "iam:DeleteRolePolicy", "iam:PutRolePolicy"]
    resources = [
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-wf-*",
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-chain-*",
    ]

    condition {
      test     = "StringEquals"
      variable = "iam:PermissionsBoundary"
      values   = [local.application_boundary_arn]
    }
  }

  statement {
    sid    = "ManageTheApplicationRoles"
    effect = "Allow"
    actions = [
      "iam:DeleteRole",
      "iam:GetRole",
      "iam:GetRolePolicy",
      "iam:ListAttachedRolePolicies",
      "iam:ListInstanceProfilesForRole",
      "iam:ListRolePolicies",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRoleDescription",
    ]
    resources = [
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-wf-*",
      "arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-chain-*",
    ]
  }

  statement {
    sid       = "ReadTheApplicationCeiling"
    effect    = "Allow"
    actions   = ["iam:GetPolicy", "iam:GetPolicyVersion"]
    resources = [local.application_boundary_arn]
  }

  statement {
    sid       = "PassTheExecutionRolesToTheWorkflowService"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-wf-*"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["airflow-serverless.amazonaws.com"]
    }
  }

  statement {
    sid       = "PassTheChainRoleToStepFunctions"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-chain-exec"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["states.amazonaws.com"]
    }
  }

  statement {
    sid       = "PassTheSchedulerRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-chain-scheduler"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["scheduler.amazonaws.com"]
    }
  }

  statement {
    sid       = "PassTheBridgeRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-chain-events"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["events.amazonaws.com"]
    }
  }

  # The saver's read of a pinned definition and code package, the release job's copy (Stage 10 step
  # 2.4) and its seed of the inbox (decision 20 (d)). The outputs bucket's policy holds this role to
  # these two prefixes (Stage 9 steps 1.1 and 4.1).
  statement {
    sid     = "WriteTheReleaseTreeAndTheInbox"
    effect  = "Allow"
    actions = ["s3:GetObject", "s3:GetObjectVersion", "s3:PutObject"]
    resources = [
      "arn:${local.partition}:s3:::awsds-${var.env}-outputs/applications/*",
      "arn:${local.partition}:s3:::awsds-${var.env}-outputs/inbox/*",
    ]
  }

  statement {
    sid       = "ListTheReleasePrefixes"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:${local.partition}:s3:::awsds-${var.env}-outputs"]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"
      values   = ["applications/*", "inbox/*"]
    }
  }

  # The data key by its alias, which exists before this slice can know the key's ARN.
  statement {
    sid       = "UseTheDataKeyThroughS3"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = ["arn:${local.partition}:kms:${local.region_account}:key/*"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-data"]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }

  # Stage 10 decision 2: the workflow is encrypted with the data key, and the service makes its calls
  # in the saver's session (Stage 18 step 4.2), the read handler's Decrypt included. Each statement
  # here has its twin among the key policy's AllowTheReleaseRoles* statements (Stage 9 step 1.1).
  statement {
    sid       = "UseTheDataKeyForTheWorkflows"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = ["arn:${local.partition}:kms:${local.region_account}:key/*"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-data"]
    }

    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:airflow-serverless:workflow-arn"
      values   = ["arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/awsds-${var.env}-wf-*"]
    }
  }

  statement {
    sid       = "GrantTheDataKeyToTheServices"
    effect    = "Allow"
    actions   = ["kms:CreateGrant"]
    resources = ["arn:${local.partition}:kms:${local.region_account}:key/*"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-data"]
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }

  statement {
    sid       = "DescribeTheDataKey"
    effect    = "Allow"
    actions   = ["kms:DescribeKey"]
    resources = ["arn:${local.partition}:kms:${local.region_account}:key/*"]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = ["alias/awsds-${var.env}-data"]
    }
  }

  statement {
    sid       = "FindTheDataKey"
    effect    = "Allow"
    actions   = ["kms:ListAliases"]
    resources = ["*"]
  }

  statement {
    sid    = "TheLogGroups"
    effect = "Allow"
    actions = [
      "logs:AssociateKmsKey",
      "logs:CreateLogGroup",
      "logs:DeleteLogGroup",
      "logs:DeleteRetentionPolicy",
      "logs:DisassociateKmsKey",
      "logs:ListTagsForResource",
      "logs:ListTagsLogGroup",
      "logs:PutRetentionPolicy",
      "logs:TagLogGroup",
      "logs:TagResource",
      "logs:UntagLogGroup",
      "logs:UntagResource",
    ]
    resources = [
      "arn:${local.partition}:logs:${local.region_account}:log-group:/awsds/${var.env}/wf/*",
      "arn:${local.partition}:logs:${local.region_account}:log-group:/aws/vendedlogs/states/awsds-${var.env}-chains",
      "arn:${local.partition}:logs:${local.region_account}:log-group:/aws/vendedlogs/states/awsds-${var.env}-chains:*",
    ]
  }

  statement {
    sid    = "DescribeAndDeliverTheLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:DeleteLogDelivery",
      "logs:DescribeLogGroups",
      "logs:DescribeResourcePolicies",
      "logs:GetLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
    ]
    resources = ["*"]
  }
}
