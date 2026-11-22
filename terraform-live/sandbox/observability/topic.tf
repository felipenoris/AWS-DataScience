# awsds-<env>-alerts in Sandbox (Stage 12 step 2.2). Stage 8 decision 5 gave one to each deployment
# target in its foundation/; Sandbox is not one, and sandbox/warehouse/alarms.tf deferred this
# account's topic to Stage 12, so it lives with the alarms that need it. sandbox/warehouse/'s two
# alarms read it from this slice's output once their slice is applied with the action.

resource "aws_sns_topic" "alerts" {
  # checkov:skip=CKV_AWS_26:CloudWatch cannot publish to a topic under the AWS-managed SNS key, whose policy admits no service, and a key of its own costs 1 USD a month; an alarm notification carries the alarm's name and state
  name = "awsds-${var.env}-alerts"

  tags = {
    Name = "awsds-${var.env}-alerts"
  }
}

resource "aws_sns_topic_policy" "alerts" {
  arn = aws_sns_topic.alerts.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "CloudWatchAlarmsOfThisAccount"
        Effect    = "Allow"
        Principal = { Service = "cloudwatch.amazonaws.com" }
        Action    = "sns:Publish"
        Resource  = aws_sns_topic.alerts.arn
        Condition = {
          ArnLike      = { "aws:SourceArn" = "arn:${data.aws_partition.current.partition}:cloudwatch:${var.region}:${data.aws_caller_identity.current.account_id}:alarm:*" }
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      },
    ]
  })
}

resource "aws_sns_topic_subscription" "alerts_email" {
  count = var.alert_email == null ? 0 : 1

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

check "alerts_reach_someone" {
  assert {
    condition     = var.alert_email != null
    error_message = "awsds-${var.env}-alerts has no subscriber: this account's alarms notify nobody until alert_email is set in an untracked alerts.auto.tfvars (Stage 8 decision 5)."
  }
}
