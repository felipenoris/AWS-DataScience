# The workflows (steps 1.1, 1.3 and 3.1): per entry of var.workflows, the execution role, the named
# log group, the workflow and its failure rule, all named awsds-<env>-wf-<key>.

locals {
  workflow_names = { for k, w in var.workflows : k => "awsds-${var.env}-wf-${k}" }

  workflow_log_groups = { for k, w in var.workflows : k => "/awsds/${var.env}/wf/${k}" }

  # Built from the name rather than read from the resource, so the plan shows each role's policy whole.
  workflow_log_group_arns = { for k, g in local.workflow_log_groups : k => "arn:${local.partition}:logs:${local.region_account}:log-group:${g}" }

  # A workflow that submits a SageMaker job passes the job role and grants SageMaker the volume key.
  submits_jobs = { for k, w in var.workflows : k => w.processing_job_prefix != null || w.training_job_prefix != null }

  # The prefixes a workflow's tasks read: its own reads, and what it writes, since an S3 operator
  # checks a key before it writes one.
  read_prefixes = { for k, w in var.workflows : k => distinct(concat(w.reads, w.writes, w.deletes)) }
}

# ------------------------------------------------------------------- the execution role (1.3)
#
# Trusted by the workflow service of this account alone. AWS's sample trust omits aws:SourceAccount;
# if CreateWorkflow refuses the role naming its trust, the condition is dropped and the refusal
# recorded (step 1.3).
data "aws_iam_policy_document" "workflow_trust" {
  statement {
    sid     = "TheWorkflowServiceOfThisAccount"
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["airflow-serverless.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [local.account_id]
    }
  }
}

# What the workflow's tasks call as this role: the worker runs every Python, Bash and S3 operator task
# with its credentials, and the Glue and SageMaker operators make their calls with them. It starts and
# observes jobs and reaches the outputs bucket's own prefixes; the jobs' data access is the job role's.
data "aws_iam_policy_document" "workflow" {
  # checkov:skip=CKV_AWS_111:every write names this account's resources by name or by prefix; kms:CreateGrant is held to SageMaker's grants for an AWS resource by its conditions
  # checkov:skip=CKV_AWS_356:no statement takes "*": the job ARNs are prefixes because each run names its job
  for_each = var.workflows

  statement {
    sid       = "WriteItsLogGroup"
    effect    = "Allow"
    actions   = ["logs:CreateLogStream", "logs:PutLogEvents"]
    resources = [local.workflow_log_group_arns[each.key], "${local.workflow_log_group_arns[each.key]}:*"]
  }

  # GlueJobOperator reads the job before it starts it and counts only EntityNotFoundException as
  # absent; on an absent job it calls CreateJob, which this role does not hold, so a name the
  # application slice did not declare fails closed (step 1.3, D41 item 9).
  dynamic "statement" {
    for_each = length(each.value.glue_jobs) > 0 ? [1] : []

    content {
      sid    = "RunTheApplicationsGlueJobs"
      effect = "Allow"
      actions = [
        "glue:BatchStopJobRun",
        "glue:GetJob",
        "glue:GetJobRun",
        "glue:GetJobRuns",
        "glue:StartJobRun",
      ]
      resources = [for j in each.value.glue_jobs : "arn:${local.partition}:glue:${local.region_account}:job/${j}"]
    }
  }

  # SageMakerProcessingOperator describes the name it proposes before the create and counts only a
  # ValidationException as absent; a create with tags is also authorized as AddTags (6i).
  dynamic "statement" {
    for_each = each.value.processing_job_prefix == null ? [] : [1]

    content {
      sid    = "SubmitItsProcessingJobs"
      effect = "Allow"
      actions = [
        "sagemaker:AddTags",
        "sagemaker:CreateProcessingJob",
        "sagemaker:DescribeProcessingJob",
        "sagemaker:StopProcessingJob",
      ]
      resources = ["arn:${local.partition}:sagemaker:${local.region_account}:processing-job/${each.value.processing_job_prefix}*"]
    }
  }

  # SageMakerTrainingOperator describes the configured name before the create and reads the
  # training log group while print_log is true, the default (step 1.3, provider 9.32.0).
  dynamic "statement" {
    for_each = each.value.training_job_prefix == null ? [] : [1]

    content {
      sid    = "SubmitItsTrainingJobs"
      effect = "Allow"
      actions = [
        "sagemaker:AddTags",
        "sagemaker:CreateTrainingJob",
        "sagemaker:DescribeTrainingJob",
        "sagemaker:StopTrainingJob",
      ]
      resources = ["arn:${local.partition}:sagemaker:${local.region_account}:training-job/${each.value.training_job_prefix}*"]
    }
  }

  dynamic "statement" {
    for_each = each.value.training_job_prefix == null ? [] : [1]

    content {
      sid       = "ReadTheTrainingLogs"
      effect    = "Allow"
      actions   = ["logs:DescribeLogStreams", "logs:GetLogEvents"]
      resources = ["arn:${local.partition}:logs:${local.region_account}:log-group:/aws/sagemaker/TrainingJobs:*"]
    }
  }

  # The training hook heads each S3DataSource channel's bucket before the create, and HeadBucket is
  # s3:ListBucket with no prefix, which no prefix condition can admit.
  dynamic "statement" {
    for_each = each.value.training_job_prefix == null ? [] : [1]

    content {
      sid       = "HeadTheOutputsBucket"
      effect    = "Allow"
      actions   = ["s3:ListBucket"]
      resources = [local.outputs_bucket_arn]

      condition {
        test     = "Null"
        variable = "s3:prefix"
        values   = ["true"]
      }
    }
  }

  dynamic "statement" {
    for_each = local.submits_jobs[each.key] ? [1] : []

    content {
      sid       = "PassTheJobRoleToSageMaker"
      effect    = "Allow"
      actions   = ["iam:PassRole"]
      resources = [var.job_role_arn]

      condition {
        test     = "StringEquals"
        variable = "iam:PassedToService"
        values   = ["sagemaker.amazonaws.com"]
      }
    }
  }

  # A job's VolumeKmsKeyId is the data key, and SageMaker creates its grant in the submitting
  # session (6i), which is this role's.
  dynamic "statement" {
    for_each = local.submits_jobs[each.key] ? [1] : []

    content {
      sid       = "GrantSageMakerTheVolumeKey"
      effect    = "Allow"
      actions   = ["kms:CreateGrant"]
      resources = [var.data_key_arn]

      condition {
        test     = "StringEquals"
        variable = "kms:ViaService"
        values   = ["sagemaker.${local.region}.amazonaws.com"]
      }

      condition {
        test     = "Bool"
        variable = "kms:GrantIsForAWSResource"
        values   = ["true"]
      }
    }
  }

  dynamic "statement" {
    for_each = length(local.read_prefixes[each.key]) > 0 ? [1] : []

    content {
      sid       = "ReadItsPrefixes"
      effect    = "Allow"
      actions   = ["s3:GetObject"]
      resources = [for p in local.read_prefixes[each.key] : "${local.outputs_bucket_arn}/${p}*"]
    }
  }

  dynamic "statement" {
    for_each = length(local.read_prefixes[each.key]) > 0 ? [1] : []

    content {
      sid       = "ListItsPrefixes"
      effect    = "Allow"
      actions   = ["s3:ListBucket"]
      resources = [local.outputs_bucket_arn]

      condition {
        test     = "StringLike"
        variable = "s3:prefix"
        values   = [for p in local.read_prefixes[each.key] : "${p}*"]
      }
    }
  }

  dynamic "statement" {
    for_each = length(each.value.writes) > 0 ? [1] : []

    content {
      sid       = "WriteItsResultAndMarkers"
      effect    = "Allow"
      actions   = ["s3:PutObject"]
      resources = [for p in each.value.writes : "${local.outputs_bucket_arn}/${p}*"]
    }
  }

  # Decision 10: a file-triggered workflow empties its own inbox.
  dynamic "statement" {
    for_each = length(each.value.deletes) > 0 ? [1] : []

    content {
      sid       = "EmptyItsInbox"
      effect    = "Allow"
      actions   = ["s3:DeleteObject"]
      resources = [for p in each.value.deletes : "${local.outputs_bucket_arn}/${p}*"]
    }
  }

  # The worker's session decrypts directly through the kms endpoint (Stage 18 step 4.4, on a key the
  # log did not name), so the role decrypts what is encrypted for its own workflow and nothing else:
  # the ten ? are the suffix the service appends, so app-etl's role cannot read app-etl-check's.
  dynamic "statement" {
    for_each = var.workflow_encryption == "CUSTOMER_MANAGED_KEY" ? [1] : []

    content {
      sid       = "DecryptItsWorkflow"
      effect    = "Allow"
      actions   = ["kms:Decrypt"]
      resources = [var.data_key_arn]

      condition {
        test     = "StringLike"
        variable = "kms:EncryptionContext:aws:airflow-serverless:workflow-arn"
        values   = ["arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/${local.workflow_names[each.key]}-??????????"]
      }
    }
  }

  # The outputs bucket is encrypted with the data key, which delegates nothing to IAM: the key policy
  # names awsds-<env>-wf-* as well (the data slice's, Stage 9 step 1.1).
  dynamic "statement" {
    for_each = length(local.read_prefixes[each.key]) > 0 ? [1] : []

    content {
      sid       = "UseTheDataKeyThroughS3"
      effect    = "Allow"
      actions   = ["kms:Decrypt", "kms:GenerateDataKey"]
      resources = [var.data_key_arn]

      condition {
        test     = "StringEquals"
        variable = "kms:ViaService"
        values   = ["s3.${local.region}.amazonaws.com"]
      }
    }
  }
}

module "execution_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source   = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"
  for_each = var.workflows

  name                 = local.workflow_names[each.key]
  description          = "The execution role of the workflow ${local.workflow_names[each.key]} (Stage 10 step 1.3): starts and observes its jobs, reaches its prefixes of ${var.outputs_bucket}, holds no lake permission"
  permissions_boundary = var.application_boundary_arn
  assume_role_policy   = data.aws_iam_policy_document.workflow_trust.json

  inline_policies = {
    "orchestrate" = data.aws_iam_policy_document.workflow[each.key].json
  }
}

# ------------------------------------------------------------------------ the log group (1.1)
#
# Named, so the service never creates /aws/mwaa-serverless/<id>/, which nobody expires (D28 item 5).
resource "aws_cloudwatch_log_group" "workflow" {
  # checkov:skip=CKV_AWS_338:retention is 90 days, D28 item 5's figure; the audit trail of record is CloudTrail, org-wide and Object-Locked since Stage 1d
  for_each = var.workflows

  name              = local.workflow_log_groups[each.key]
  retention_in_days = var.log_retention_days
  kms_key_id        = var.data_key_arn
}

# --------------------------------------------------------------------------- the workflow (1.1)
#
# An update replaces every attribute it is not given (Lesson 60), so every attribute the service
# accepts is declared. The definition and the code package are pinned by S3 VersionId: the service
# reads both at save time, in the saver's session (the deploy role's, step 1.5). A workflow a chain
# starts carries no schedule of its own (decision 13) and the TriggerMode the service writes when
# none is given. Name and EncryptionConfiguration are create-only: a change to either is a new ARN
# and loses the run history.
resource "awscc_mwaaserverless_workflow" "this" {
  for_each = var.workflows

  name        = local.workflow_names[each.key]
  description = each.value.description
  role_arn    = module.execution_role[each.key].role_arn

  definition_s3_location = {
    bucket     = each.value.definition.bucket
    object_key = each.value.definition.key
    version_id = each.value.definition.version_id
  }

  code = each.value.code == null ? null : {
    s3_location = {
      bucket     = each.value.code.bucket
      object_key = each.value.code.key
      version_id = each.value.code.version_id
    }
  }

  logging_configuration = {
    log_group_name = aws_cloudwatch_log_group.workflow[each.key].name
  }

  network_configuration = {
    subnet_ids         = var.subnet_ids
    security_group_ids = [aws_security_group.workers.id]
  }

  encryption_configuration = var.workflow_encryption == "CUSTOMER_MANAGED_KEY" ? {
    type       = "CUSTOMER_MANAGED_KEY"
    kms_key_id = var.data_key_arn
    } : {
    type       = "AWS_MANAGED_KEY"
    kms_key_id = null
  }

  trigger_mode = "manual_only"

  tags = merge(var.tags, { Name = local.workflow_names[each.key] })
}

# ---------------------------------------------------------------------- the failure rule (3.1)
#
# The service's own events (source aws.airflow-serverless): each detail type carries the "MWAA
# Serverless " prefix, and the detail names the run's workflowArn (the reference page and an example
# event, read 2026-10-22). A sensor with soft_fail ends an empty run SUCCESS, which no rule here hears.
resource "aws_cloudwatch_event_rule" "workflow_failed" {
  for_each = var.workflows

  name        = "${local.workflow_names[each.key]}-failed"
  description = "A run of ${local.workflow_names[each.key]} failed or timed out (Stage 10 step 3.1)"
  state       = "ENABLED"

  event_pattern = jsonencode({
    source        = ["aws.airflow-serverless"]
    "detail-type" = ["MWAA Serverless Workflow Run Failed", "MWAA Serverless Workflow Run Timeout"]
    detail = {
      workflowArn = [awscc_mwaaserverless_workflow.this[each.key].workflow_arn]
    }
  })

  tags = {
    Name = "${local.workflow_names[each.key]}-failed"
  }
}

# The message names the run; its record stays in the service. EventBridge does not escape an
# extracted value, so every path is an identifier the service writes, never free text.
resource "aws_cloudwatch_event_target" "workflow_failed" {
  for_each = var.workflows

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
