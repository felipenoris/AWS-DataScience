# production/orchestration/ - Stage 10's [E] slice in Production: terraform-modules/orchestration called
# with VPC-Workloads, this account's keys and roles, and the application's workflows and chains (steps
# 1.1-1.3, 3.1, 3.4-3.7). Applied by the pipeline as awsds-deploy-prod after the Staging leg and the
# gate (step 1.5, INT-14); `make up` refuses it (layers.py refusal 7), and `make down` destroys it, the
# runs' history with it (step 6.3).

data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# Stage 9's job role, awsds-<env>-job-exec (Stage 8 step 2.5, taken 2026-10-22).
data "terraform_remote_state" "sagemaker" {
  count   = var.release == null ? 0 : 1
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/sagemaker/terraform.tfstate"
    region = var.region
  }
}

# Two objects of other slices named by contract: the application ceiling, whose name the deploy role's
# ceiling fixes (Stage 8 step 3.0), and the account data CMK, whose alias docs/GOVERNANCE.md
# (Encryption) fixes. Each lookup fails the plan, naming the object, while it is missing.
data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_iam_policy" "application_boundary" {
  count = var.release == null ? 0 : 1
  arn   = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:policy/awsds-${var.env}-app-boundary"
}

data "aws_kms_alias" "data" {
  count = var.release == null ? 0 : 1
  name  = "alias/awsds-${var.env}-data"
}

locals {
  outputs_bucket = "awsds-${var.env}-outputs"

  # The application's workflows as Stage 10 decision 6's render table places them in this account: the
  # Glue job the application slice declares, the processing jobs' name prefix, and the outputs bucket's
  # prefixes the worker's tasks read and write (summarize reads the processing output, write_result
  # writes the report).
  applications = {
    "app-etl" = {
      application           = "app-etl"
      description           = "app-etl: the Glue transform, the processing job on the application image, the summary and the report (Stage 8 step 2.5, D41)"
      code                  = true
      glue_jobs             = ["awsds-${var.env}-app-etl"]
      processing_job_prefix = "app-etl-"
      reads                 = ["app-etl/work/job/"]
      writes                = ["app-etl/outbox/"]
    }
  }

  workflows = var.release == null ? {} : {
    for k, a in local.applications : k => {
      description = a.description
      definition = {
        bucket     = local.outputs_bucket
        key        = "workflows/${a.application}/${var.release.tag}/workflows/${k}.yaml"
        version_id = var.release.workflows[k].definition_version_id
      }
      code = a.code ? {
        bucket     = local.outputs_bucket
        key        = "workflows/${a.application}/${var.release.tag}/code/${k}.zip"
        version_id = var.release.workflows[k].code_version_id
      } : null
      glue_jobs             = a.glue_jobs
      processing_job_prefix = a.processing_job_prefix
      reads                 = a.reads
      writes                = a.writes
    } if contains(keys(var.release.workflows), k)
  }

  # Decision 13: every production workflow starts from a chain, a chain of one included. The cron is
  # UTC; the schedule's state is the pause lever (step 6.1).
  chains = var.release == null ? {} : {
    "app-etl" = {
      definition_template = file("${path.module}/chains/app-etl.asl.json")
      workflows           = ["app-etl"]
      schedule_expression = "cron(30 6 * * ? *)"
      schedule_timezone   = "UTC"
      schedule_enabled    = true
    }
  }
}

module "orchestration" {
  # By path until orchestration-v0.1.0 exists on origin; Recipe B then pins the tag, the way every
  # caller consumes a module (conventions §6).
  source = "../../../terraform-modules/orchestration"
  count  = var.release == null ? 0 : 1

  env                      = var.env
  vpc_id                   = data.terraform_remote_state.workloads.outputs.vpc_id
  subnet_ids               = [for z in var.zone_ids : data.terraform_remote_state.workloads.outputs.private_subnet_ids[z]]
  application_boundary_arn = data.aws_iam_policy.application_boundary[0].arn
  alerts_topic_arn         = data.terraform_remote_state.foundation.outputs.alerts_topic_arn
  data_key_arn             = data.aws_kms_alias.data[0].target_key_arn
  job_role_arn             = data.terraform_remote_state.sagemaker[0].outputs.job_role_arn
  outputs_bucket           = local.outputs_bucket

  workflows = local.workflows
  chains    = local.chains
  tags      = local.tags
}
