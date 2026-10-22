# The chain layer (D41 item 5; steps 3.4 to 3.7): the base per account - the schedule group, the
# state machines' log group and the three chain roles - then per chain a Step Functions Standard
# state machine that starts its workflows in order and waits for each run, the Scheduler schedule
# that starts the machine, and the machine's failure rule; per bridge an EventBridge rule that starts
# a chain on a write under inbox/<app>/. No chain role touches data, and none is a workflow's
# execution role.

locals {
  workflow_arns = { for k, w in awscc_mwaaserverless_workflow.this : k => w.workflow_arn }
}

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
  kms_key_id        = var.data_key_arn
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

# What a chain's machine calls: the start and the read of a run, the key the service decrypts the
# workflow with in the caller's session at both (Stage 18 step 0.4, 2026-10-19: one Decrypt per
# GetWorkflowRun, the workflow's ARN as encryption context), and the log delivery.
data "aws_iam_policy_document" "chain_exec" {
  # checkov:skip=CKV_AWS_111:the log-delivery actions take no resource narrower than "*" (the Step Functions guide's own policy)
  # checkov:skip=CKV_AWS_356:idem
  statement {
    sid       = "StartAndReadTheWorkflowsOfThisAccount"
    effect    = "Allow"
    actions   = ["airflow-serverless:GetWorkflowRun", "airflow-serverless:StartWorkflowRun"]
    resources = [local.workflow_arn_pattern]
  }

  dynamic "statement" {
    for_each = var.workflow_encryption == "CUSTOMER_MANAGED_KEY" ? [1] : []

    content {
      sid       = "UseTheWorkflowKey"
      effect    = "Allow"
      actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
      resources = [var.data_key_arn]

      condition {
        test     = "StringLike"
        variable = "kms:EncryptionContext:aws:airflow-serverless:workflow-arn"
        values   = [local.workflow_arn_pattern]
      }
    }
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
  description          = "Step Functions' role for the chains of this account (Stage 10 step 3.4): starts and reads the awsds-${var.env}-wf-* workflows, delivers the execution logs, touches no job and no data"
  permissions_boundary = var.application_boundary_arn
  assume_role_policy   = data.aws_iam_policy_document.chain_exec_trust.json

  inline_policies = {
    "chain" = data.aws_iam_policy_document.chain_exec.json
  }
}

# Two starters with one grant and two trusts: CloudTrail tells a scheduled start from a start on an
# inbox write by the role that made it (step 3.6).
data "aws_iam_policy_document" "chain_starter_trust" {
  for_each = {
    scheduler = "scheduler.amazonaws.com"
    events    = "events.amazonaws.com"
  }

  statement {
    sid     = "TheServiceOfThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = [each.value]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

data "aws_iam_policy_document" "chain_starter" {
  statement {
    sid       = "StartTheChainsOfThisAccount"
    effect    = "Allow"
    actions   = ["states:StartExecution"]
    resources = [local.state_machine_arn_pattern]
  }
}

module "chain_starter_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"
  for_each = {
    scheduler = "EventBridge Scheduler's role for the chain schedules of this account (Stage 10 step 3.4): starts the awsds-${var.env}-chain-* machines"
    events    = "EventBridge's role for the inbox bridges of this account (Stage 10 step 3.6): starts the awsds-${var.env}-chain-* machines"
  }

  name                 = "awsds-${var.env}-chain-${each.key}"
  description          = each.value
  permissions_boundary = var.application_boundary_arn
  assume_role_policy   = data.aws_iam_policy_document.chain_starter_trust[each.key].json

  inline_policies = {
    "start" = data.aws_iam_policy_document.chain_starter.json
  }
}

# ----------------------------------------------------------------------------- a chain (3.5)
#
# The definition is the slice's chains/<key>.asl.json (decision 14), rendered with every workflow's
# ARN by key. Standard, since Express has no .sync pattern and a five-minute cap.
resource "aws_sfn_state_machine" "chain" {
  # checkov:skip=CKV_AWS_284:no X-Ray: the chain calls two MWAA Serverless actions and the execution history carries every transition
  for_each = var.chains

  name     = "awsds-${var.env}-chain-${each.key}"
  role_arn = module.chain_exec_role.role_arn
  type     = "STANDARD"

  definition = templatestring(each.value.definition_template, {
    env          = var.env
    partition    = local.partition
    workflow_arn = local.workflow_arns
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
      condition     = alltrue([for w in each.value.workflows : contains(keys(var.workflows), w)])
      error_message = "chain ${each.key} starts a workflow var.workflows does not declare."
    }
  }
}

# The pause lever is the schedule's state (step 6.1). The machine receives the scheduled time as its
# input; a chain forwards it to a run as an OverrideParameters entry only where its workflow reads one.
resource "aws_scheduler_schedule" "chain" {
  # checkov:skip=CKV_AWS_297:the schedule holds the chain's name and the scheduled-time placeholder and no data; a CMK would put the Scheduler's role and the deploy role on the data key's policy to protect neither
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
    role_arn = module.chain_starter_role["scheduler"].role_arn
    input    = jsonencode({ chain = each.key, scheduledTime = "<aws.scheduler.scheduled-time>" })

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
      "Its history names the workflow whose run failed; the workflow's task instances name the task (Stage 10 step 3.2)."
      "EventBridge event id: <event_id>"
    EOT
    )
  }
}

# ---------------------------------------------------------------------------- a bridge (3.6)
#
# An object created under inbox/<app>/ of the outputs bucket starts the chain the bridge names. The
# bucket's notification to EventBridge is the data slice's. Two objects start two executions.
resource "aws_cloudwatch_event_rule" "inbox" {
  for_each = var.bridges

  name        = "awsds-${var.env}-inbox-${each.key}"
  description = "An object created under inbox/${each.key}/ of ${var.outputs_bucket} starts awsds-${var.env}-chain-${each.value.chain} (Stage 10 step 3.6)"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source        = ["aws.s3"]
    "detail-type" = ["Object Created"]
    detail = {
      bucket = { name = [var.outputs_bucket] }
      object = { key = [{ prefix = "inbox/${each.key}/" }] }
    }
  })

  tags = {
    Name = "awsds-${var.env}-inbox-${each.key}"
  }

  lifecycle {
    precondition {
      condition     = contains(keys(var.chains), each.value.chain)
      error_message = "bridge ${each.key} names a chain var.chains does not declare."
    }
  }
}

resource "aws_cloudwatch_event_target" "inbox" {
  for_each = var.bridges

  rule      = aws_cloudwatch_event_rule.inbox[each.key].name
  target_id = "chain"
  arn       = aws_sfn_state_machine.chain[each.value.chain].arn
  role_arn  = module.chain_starter_role["events"].role_arn
}
