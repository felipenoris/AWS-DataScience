# What this slice reads and does not own. Every value is read from a sibling's state, never pasted
# (Lesson 3), and every state key is built from the account folder (Lesson 14).

data "aws_caller_identity" "current" {}

# The account data CMK, alias/awsds-prod-data. One data key per account (docs/GOVERNANCE.md
# Encryption), and the warehouse is a data store in this account, so the namespace and the three
# audit log groups take Production's data key (Stage 9 decision 8). Its policy admits the namespace
# through `AllowRedshiftServerlessViaServiceInThisAccount`, the statement Sandbox's first apply
# lacked (EXC-12), and CloudWatch Logs through `AllowCloudWatchLogsForTheJobAndWorkflowGroups`, whose
# group patterns must name `/aws/redshift/` before the groups are created.
data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/data/terraform.tfstate"
    region = var.region
  }
}

# VPC-Workloads, where the jobs run and the workgroup lands (Stage 9 step 9.1), never
# production/foundation/, which is VPC-SharedServices. This slice needs the VPC id alone, for the
# security group; the subnets are read by production/warehouse-compute/, which owns the workgroup.
data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

# awsds-prod-alerts, both alarms' action, created by production/foundation/ (Stage 8 decision 5),
# whose policy admits CloudWatch (`CloudWatchAlarmsOfThisAccount`, PR #179).
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# The job security group awsds-prod-jobs (Stage 9 decision 12 (a)), the one client the warehouse
# admits on 5439: every pipeline-submitted Glue and SageMaker job carries it, the governed schema's
# load job included (step 9.4). Read from production/sagemaker/'s state, which owns the group.
data "terraform_remote_state" "sagemaker" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/sagemaker/terraform.tfstate"
    region = var.region
  }
}

locals {
  name = "awsds-${var.env}-warehouse"

  data_key_arn          = data.terraform_remote_state.data.outputs.data_key_arn
  vpc_id                = data.terraform_remote_state.workloads.outputs.vpc_id
  alerts_topic_arn      = data.terraform_remote_state.foundation.outputs.alerts_topic_arn
  job_security_group_id = data.terraform_remote_state.sagemaker.outputs.job_security_group_id

  # The three audit log types. The group path is derived from the namespace name by the service
  # (AWS: "/aws/redshift/<namespace>/<log_type>"), so a namespace rename moves three log groups, and
  # that is why the namespace name is a contract Stage 9 fixes rather than a value anybody edits.
  log_types = ["userlog", "connectionlog", "useractivitylog"]

  # 0.024 USD/GB-month (docs/PRICING.md 5, Price List offer file published 2026-09-11) and the
  # DataStorage metric is in megabytes. Both halves of the conversion are here so the threshold can
  # be argued in dollars and the alarm can still be compared against the metric.
  storage_usd_per_gb_month = 0.024
  storage_alarm_mb         = ceil(var.storage_alarm_usd / local.storage_usd_per_gb_month * 1024)
}
