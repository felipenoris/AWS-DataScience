# The chain layer (D41 item 5; Stage 10 steps 3.4 to 3.7): the base per account - the schedule
# group, the state machines' log group and the two chain roles - then per chain a Step Functions
# Standard state machine that finds its workflows by name, starts each with the application's stage
# variables and waits for the run, the Scheduler schedule that starts the machine, and the machine's
# failure rule.

# ------------------------------------------------------------------------------- the base (3.4)
resource "aws_scheduler_schedule_group" "chains" {
  name = "awsds-${var.env}-chains"

  tags = {
    Name = "awsds-${var.env}-chains"
  }
}

# Under /aws/vendedlogs/, which keeps every state machine inside one CloudWatch Logs resource
# policy (the 5,120-character limit and the ten-policy quota).
resource "aws_cloudwatch_log_group" "chains" {
  # checkov:skip=CKV_AWS_338:retention is 90 days, D28 item 5's figure; the audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  name              = "/aws/vendedlogs/states/awsds-${var.env}-chains"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.log_key_arn
}

data "aws_iam_policy_document" "chain_exec_trust" {
  statement {
    sid     = "StepFunctionsOfThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

# What a chain's machine calls. The service authorizes a start and a read of a run by IAM and by the
# caller's own use of the workflow's key, with no check of project membership (Stage 18 step 0.4,
# 2026-10-19): GenerateDataKey and Decrypt at the start, one Decrypt per GetWorkflowRun, the
# workflow's ARN as encryption context.
data "aws_iam_policy_document" "chain_exec" {
  # checkov:skip=CKV_AWS_111:ListWorkflows and the log-delivery actions take no resource narrower than "*" (the service's reference and the Step Functions guide's own policy)
  # checkov:skip=CKV_AWS_356:idem
  statement {
    sid       = "FindAWorkflowByItsName"
    effect    = "Allow"
    actions   = ["airflow-serverless:ListWorkflows"]
    resources = ["*"]
  }

  statement {
    sid       = "StartAndReadTheApplicationsWorkflows"
    effect    = "Allow"
    actions   = ["airflow-serverless:GetWorkflowRun", "airflow-serverless:StartWorkflowRun"]
    resources = local.workflow_arn_patterns
  }

  statement {
    sid       = "UseTheProjectKeyForThoseWorkflows"
    effect    = "Allow"
    actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
    resources = [var.project.key_arn]

    condition {
      test     = "StringLike"
      variable = "kms:EncryptionContext:aws:airflow-serverless:workflow-arn"
      values   = local.workflow_arn_patterns
    }
  }

  statement {
    sid       = "ReadTheStageVariablesTheLegRecorded"
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [for app, name in local.stage_variables_parameters : "arn:${local.partition}:ssm:${local.region_account}:parameter${name}"]
  }

  statement {
    sid    = "DeliverTheExecutionLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogDelivery",
      "logs:CreateLogStream",
      "logs:DeleteLogDelivery",
      "logs:DescribeLogGroups",
      "logs:DescribeResourcePolicies",
      "logs:GetLogDelivery",
      "logs:ListLogDeliveries",
      "logs:PutLogEvents",
      "logs:PutResourcePolicy",
      "logs:UpdateLogDelivery",
    ]
    resources = ["*"]
  }
}

module "chain_exec_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-chain-exec"
  description          = "Step Functions' role for the chains of this account (Stage 19 step 4.11): finds, starts and reads the workflows the CI/CD CLI created in ${var.project.name}, reads their stage variables, delivers the execution logs, touches no job and no data"
  permissions_boundary = null
  assume_role_policy   = data.aws_iam_policy_document.chain_exec_trust.json

  inline_policies = {
    "chain" = data.aws_iam_policy_document.chain_exec.json
  }
}

data "aws_iam_policy_document" "chain_scheduler_trust" {
  statement {
    sid     = "TheSchedulerOfThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

data "aws_iam_policy_document" "chain_scheduler" {
  statement {
    sid       = "StartTheChainsOfThisAccount"
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [local.state_machine_arn_pattern]
  }
}

module "chain_scheduler_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name                 = "awsds-${var.env}-chain-scheduler"
  description          = "EventBridge Scheduler's role for the chain schedules of this account (Stage 10 step 3.4): starts the awsds-${var.env}-chain-* machines"
  permissions_boundary = null
  assume_role_policy   = data.aws_iam_policy_document.chain_scheduler_trust.json

  inline_policies = {
    "start" = data.aws_iam_policy_document.chain_scheduler.json
  }
}

# ----------------------------------------------------------------------------- a chain (3.5)
#
# The definition is the slice's definitions/<key>.asl.json (Stage 10 decision 14), rendered with
# the composed name of each workflow of the chain's application and the name of its stage-variables
# parameter. Standard, since Express has no .sync pattern and a five-minute cap.
resource "aws_sfn_state_machine" "chain" {
  # checkov:skip=CKV_AWS_284:no X-Ray: the chain calls SSM once and three MWAA Serverless actions, and the execution history carries every transition
  for_each = var.chains

  name     = "awsds-${var.env}-chain-${each.key}"
  role_arn = module.chain_exec_role.role_arn
  type     = "STANDARD"

  definition = templatestring(each.value.definition_template, {
    env                       = var.env
    partition                 = local.partition
    workflow_name             = { for w in try(var.applications[each.value.application].workflows, []) : w => local.workflow_names["${each.value.application}/${w}"] }
    stage_variables_parameter = try(local.stage_variables_parameters[each.value.application], "")
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.chains.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tags = {
    Name = "awsds-${var.env}-chain-${each.key}"
  }

  lifecycle {
    precondition {
      condition     = contains(keys(var.applications), each.value.application)
      error_message = "chain ${each.key} names an application var.applications does not declare."
    }

    precondition {
      condition     = alltrue([for w in each.value.workflows : contains(try(var.applications[each.value.application].workflows, []), w)])
      error_message = "chain ${each.key} starts a workflow its application does not declare in var.applications."
    }
  }
}

# The pause lever is the schedule's state (Stage 10 step 6.1). The machine receives the scheduled
# time as its input. The Scheduler substitutes a context attribute only where the input carries it
# literally, and jsonencode writes < and > as < and >, so the input is a template with the
# key alone encoded.
resource "aws_scheduler_schedule" "chain" {
  # checkov:skip=CKV_AWS_297:the schedule holds the chain's name and the scheduled-time placeholder and no data; a CMK would put the Scheduler's role on a key's policy to protect neither
  for_each = var.chains

  name                         = "awsds-${var.env}-chain-${each.key}"
  group_name                   = aws_scheduler_schedule_group.chains.name
  description                  = "Starts awsds-${var.env}-chain-${each.key} (Stage 10 step 3.5)"
  schedule_expression          = each.value.schedule_expression
  schedule_expression_timezone = each.value.schedule_timezone
  state                        = each.value.schedule_enabled ? "ENABLED" : "DISABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_sfn_state_machine.chain[each.key].arn
    role_arn = module.chain_scheduler_role.role_arn
    input    = "{\"chain\":${jsonencode(each.key)},\"scheduledTime\":\"<aws.scheduler.scheduled-time>\"}"

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 3
    }
  }
}

# ------------------------------------------------------------------ the chain's failure rule (3.7)
resource "aws_cloudwatch_event_rule" "chain_failed" {
  for_each = var.chains

  name        = "awsds-${var.env}-chain-${each.key}-failed"
  description = "An execution of awsds-${var.env}-chain-${each.key} failed, timed out or was aborted (Stage 10 step 3.7)"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source        = ["aws.states"]
    "detail-type" = ["Step Functions Execution Status Change"]
    detail = {
      status          = ["FAILED", "TIMED_OUT", "ABORTED"]
      stateMachineArn = [aws_sfn_state_machine.chain[each.key].arn]
    }
  })

  tags = {
    Name = "awsds-${var.env}-chain-${each.key}-failed"
  }
}

resource "aws_cloudwatch_event_target" "chain_failed" {
  for_each = var.chains

  rule      = aws_cloudwatch_event_rule.chain_failed[each.key].name
  target_id = "alerts-topic"
  arn       = var.alerts_topic_arn

  input_transformer {
    input_paths = {
      time      = "$.time"
      status    = "$.detail.status"
      machine   = "$.detail.stateMachineArn"
      execution = "$.detail.executionArn"
      event_id  = "$.id"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: a chain's execution ended <status>."
      "When: <time>"
      "State machine: <machine>"
      "Execution: <execution>"
      "Its history names the state that failed: the stage variables, the workflow's name or the run, whose task instances name the task (Stage 10 step 3.2)."
      "EventBridge event id: <event_id>"
    EOT
    )
  }
}
