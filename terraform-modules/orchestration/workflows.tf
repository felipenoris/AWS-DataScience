# The workflows' failure rules (Stage 10 step 3.1). The workflows are the CLI's, created in the
# deployment project at each deploy; what this module holds of them is the rule that hears a run
# fail, one per workflow of var.applications, whether a chain, the deploy's bootstrap or a person
# started the run.
#
# The service's own events (source aws.airflow-serverless): each detail type carries the "MWAA
# Serverless " prefix, and the detail names the run's workflowArn (the reference page and an example
# event, read 2026-10-22). The ARN ends in a suffix the service generates, so the rule matches the
# ARN up to it. A sensor with soft_fail ends an empty run SUCCESS, which no rule here hears.
resource "aws_cloudwatch_event_rule" "workflow_failed" {
  for_each = local.workflow_arn_prefixes

  name        = "awsds-${var.env}-wf-${replace(each.key, "/", "-")}-failed"
  description = "A run of ${local.workflow_names[each.key]} failed or timed out (Stage 10 step 3.1)"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source        = ["aws.airflow-serverless"]
    "detail-type" = ["MWAA Serverless Workflow Run Failed", "MWAA Serverless Workflow Run Timeout"]
    detail = {
      workflowArn = [{ prefix = each.value }]
    }
  })

  tags = {
    Name = "awsds-${var.env}-wf-${replace(each.key, "/", "-")}-failed"
  }
}

# The message names the run; its record stays in the service. EventBridge does not escape an
# extracted value, so every path is an identifier the service writes, never free text.
resource "aws_cloudwatch_event_target" "workflow_failed" {
  for_each = local.workflow_arn_prefixes

  rule      = aws_cloudwatch_event_rule.workflow_failed[each.key].name
  target_id = "alerts-topic"
  arn       = var.alerts_topic_arn

  input_transformer {
    input_paths = {
      time     = "$.time"
      type     = "$.detail-type"
      workflow = "$.detail.workflowArn"
      run      = "$.detail.workflowRunId"
      status   = "$.detail.status"
      event_id = "$.id"
    }
    input_template = chomp(<<-EOT
      "<aws.events.rule-name>: a workflow run ended <status>."
      "When: <time>"
      "Event: <type>"
      "Workflow: <workflow>"
      "Run: <run>"
      "Diagnose with mwaa-serverless list-task-instances and get-task-instance (Stage 10 step 3.2)."
      "EventBridge event id: <event_id>"
    EOT
    )
  }
}
