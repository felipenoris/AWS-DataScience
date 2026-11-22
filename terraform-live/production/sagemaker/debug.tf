# Stage 9 step 6 - awsds-prod-debug, the production debugging escape hatch (D17), and the alarm on
# every assumption of it.
#
# The role reads what a job left behind: the outputs bucket, the job log groups and the job
# descriptions. It holds no lake reach of any kind (no lakeformation:GetDataAccess, no catalog read,
# no grant through step 2.3), and no write. Its shape is imposed by the Workloads OU document:
# DenyInteractiveSageMakerSurface refuses CreateSpace, CreateApp, StartSession and
# CreatePresignedDomainUrl with no principal carve-out, so the role is read by API only.
#
# The trust admits the production persona while a window the deployment manager approved is open
# (decision 4): the window is var.debug_window_end, whose default sits in the past, so the role exists
# and nobody can assume it at rest. A session lasts the aws_iam_role default, 3600 s (6.1's hour,
# DT-9's ceiling); the iam-role module takes no max_session_duration.
#
# The builder is outside every claim here (Lesson 18): what watches the role is detective, the
# alarm below and CloudTrail.

locals {
  debug_role_name = "awsds-${var.env}-debug"
  debug_rule_name = "awsds-${var.env}-debug-assume"

  # one() fails the plan unless exactly one role matches (data.tf).
  data_scientist_prod_role_arn = one(data.aws_iam_roles.data_scientist_prod.arns)
}

module "debug_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = local.debug_role_name
  description = "Production debugging escape hatch (Stage 9 step 6, D17): read the job outputs, logs and descriptions while an approved window is open. No lake reach, no write"

  permissions_boundary = null

  # aws:RequestedRegion holds the assumption to this region's STS endpoint. A call to the global
  # endpoint carries us-east-1 in that key and is recorded in us-east-1 (AWS's page on STS endpoints,
  # read 2026-10-16), where the alarm below does not run; refusing it keeps every admitted
  # assumption visible to the alarm.
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "ThePersonaWhileAWindowIsOpen"
        Effect    = "Allow"
        Principal = { AWS = local.data_scientist_prod_role_arn }
        Action    = "sts:AssumeRole"
        Condition = {
          DateLessThan = { "aws:CurrentTime" = var.debug_window_end }
          StringEquals = { "aws:RequestedRegion" = var.region }
        }
      },
    ]
  })

  inline_policies = {
    "debug" = data.aws_iam_policy_document.debug.json
  }
}

data "aws_iam_policy_document" "debug" {
  # checkov:skip=CKV_AWS_356:the SageMaker Describe and List calls, DescribeLogGroups and the Logs Insights query reads take no narrower resource; every one of them is a read

  # ------------------------------------------------------- the outputs bucket (step 1.1)
  statement {
    sid       = "ReadTheOutputs"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${local.outputs_bucket_arn}/*"]
  }

  statement {
    sid       = "ListTheOutputs"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [local.outputs_bucket_arn]
  }

  # The account data CMK decrypts the outputs through S3 alone. The key policy in production/data/
  # names this role for kms:Decrypt only (step 1.1); log events need no key permission from the
  # reader, because CloudWatch Logs decrypts them as itself.
  statement {
    sid       = "DecryptTheOutputsThroughS3"
    effect    = "Allow"
    actions   = ["kms:Decrypt"]
    resources = [local.account_key_arns]

    condition {
      test     = "ForAnyValue:StringEquals"
      variable = "kms:ResourceAliases"
      values   = [local.data_key_alias]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["s3.${var.region}.amazonaws.com"]
    }
  }

  # ------------------------------------------------------------------- the job logs (3.1)
  statement {
    sid    = "ReadTheJobLogs"
    effect = "Allow"
    actions = [
      "logs:DescribeLogStreams",
      "logs:FilterLogEvents",
      "logs:GetLogEvents",
      "logs:StartQuery",
    ]
    resources = flatten([
      for arn in local.job_log_group_arns : [arn, "${arn}:*"]
    ])
  }

  statement {
    sid    = "FindTheGroupsAndReadTheQueries"
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups",
      "logs:GetQueryResults",
      "logs:StopQuery",
    ]
    resources = ["*"]
  }

  # ------------------------------------------------------------------ the job descriptions
  statement {
    sid    = "DescribeTheJobs"
    effect = "Allow"
    actions = [
      "sagemaker:Describe*",
      "sagemaker:List*",
    ]
    resources = ["*"]
  }
}

# The window is the deployment manager's approval, and closing it is the next apply without the flag
# (6.3). This check prints on every plan while it is open.
check "debug_window_closed" {
  assert {
    condition     = timecmp(var.debug_window_end, plantimestamp()) <= 0
    error_message = "The debug window on ${local.debug_role_name} is open until ${var.debug_window_end}: close it in the same sitting with an apply without -var debug_window_end (Stage 9 step 6.3)."
  }
}

# ---------------------------------------------------------------- the assumption alarm (6.2)
#
# Every assumption, to the account's alerts topic (Stage 8 decision 5). EventBridge classes STS
# AssumeRole as a read-only management event, and a rule in the default ENABLED state matches every
# event except those: only the state below makes the rules fire (deploy-role-v0.2.0's misuse rule,
# measured in Staging 2026-10-13). A refused assumption records no roleArn, so the rules see the
# successful ones only; a refused attempt is read from the trail by its errorCode.
#
# A switch in the console records a SwitchRole event from the sign-in service, naming the role in
# additionalEventData.SwitchTo, in place of the STS call [inferred from published examples, not read
# here]. The second rule catches it, and step 6.3 reads which of the two a console switch produces,
# or whether the trust's aws:RequestedRegion refuses it.
resource "aws_cloudwatch_event_rule" "debug_assume" {
  name        = local.debug_rule_name
  description = "Every AssumeRole of ${local.debug_role_name} (Stage 9 step 6.2, D17)"
  state       = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"

  event_pattern = jsonencode({
    source        = ["aws.sts"]
    "detail-type" = ["AWS API Call via CloudTrail"]
    detail = {
      eventSource       = ["sts.amazonaws.com"]
      eventName         = ["AssumeRole"]
      requestParameters = { roleArn = [{ "equals-ignore-case" = module.debug_role.role_arn }] }
    }
  })

  tags = {
    Name = local.debug_rule_name
  }
}

resource "aws_cloudwatch_event_rule" "debug_assume_console" {
  name        = "${local.debug_rule_name}-console"
  description = "Every console switch to ${local.debug_role_name} (Stage 9 step 6.2, D17)"
  state       = "ENABLED_WITH_ALL_CLOUDTRAIL_MANAGEMENT_EVENTS"

  event_pattern = jsonencode({
    source        = ["aws.signin"]
    "detail-type" = ["AWS Console Sign In via CloudTrail"]
    detail = {
      eventSource         = ["signin.amazonaws.com"]
      eventName           = ["SwitchRole"]
      additionalEventData = { SwitchTo = [{ "equals-ignore-case" = module.debug_role.role_arn }] }
    }
  })

  tags = {
    Name = "${local.debug_rule_name}-console"
  }
}

# The messages name the event and leave its record in CloudTrail, the misuse target's format: the
# whole event would carry the new session's access key id into a mailbox, and no path below is free
# text the caller chooses, because EventBridge does not escape an extracted value.
resource "aws_cloudwatch_event_target" "debug_assume" {
  rule      = aws_cloudwatch_event_rule.debug_assume.name
  target_id = "alerts-topic"
  arn       = data.terraform_remote_state.foundation.outputs.alerts_topic_arn

  input_transformer {
    input_paths = {
      time      = "$.detail.eventTime"
      role      = "$.detail.requestParameters.roleArn"
      session   = "$.detail.requestParameters.roleSessionName"
      principal = "$.detail.userIdentity.principalId"
      source    = "$.detail.sourceIPAddress"
      event_id  = "$.detail.eventID"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: the production debug role was assumed."
      "When: <time>"
      "Role: <role>"
      "Caller: <principal>"
      "Session name: <session>"
      "Source address: <source>"
      "CloudTrail event id: <event_id>"
      "The full record stays in CloudTrail; this message carries no credential."
    EOT
    )
  }
}

resource "aws_cloudwatch_event_target" "debug_assume_console" {
  rule      = aws_cloudwatch_event_rule.debug_assume_console.name
  target_id = "alerts-topic"
  arn       = data.terraform_remote_state.foundation.outputs.alerts_topic_arn

  input_transformer {
    input_paths = {
      time      = "$.detail.eventTime"
      role      = "$.detail.additionalEventData.SwitchTo"
      principal = "$.detail.userIdentity.principalId"
      source    = "$.detail.sourceIPAddress"
      event_id  = "$.detail.eventID"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: the production debug role was switched to in the console."
      "When: <time>"
      "Role: <role>"
      "Caller: <principal>"
      "Source address: <source>"
      "CloudTrail event id: <event_id>"
      "The full record stays in CloudTrail; this message carries no credential."
    EOT
    )
  }
}
