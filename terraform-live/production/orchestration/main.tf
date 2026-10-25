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
  # Glue jobs the application slice declares, the processing and training jobs' name prefixes, and the
  # outputs bucket's prefixes the worker's tasks read and write (summarize reads the processing output,
  # write_result writes the report, evaluate reads the batch input and writes beside the model). The
  # warehouse load's workflow is Production's alone (Stage 9 decision 15): Staging has no warehouse.
  applications = {
    "app-etl" = {
      application           = "app-etl"
      description           = "app-etl: the Glue transform, the processing job on the application image, the summary and the report (Stage 8 step 2.5, D41)"
      code                  = true
      glue_jobs             = ["awsds-${var.env}-app-etl"]
      processing_job_prefix = "app-etl-"
      training_job_prefix   = null
      reads                 = ["app-etl/work/job/"]
      writes                = ["app-etl/outbox/"]
    }
    "app-etl-train" = {
      application           = "app-etl"
      description           = "app-etl-train: XGBoost trained on the sets app-etl wrote, and its evaluation beside the model (Stage 10 step 5.1)"
      code                  = true
      glue_jobs             = []
      processing_job_prefix = null
      training_job_prefix   = "app-etl-train-"
      reads                 = ["app-etl/work/train/"]
      writes                = ["models/app-etl/"]
    }
    "app-etl-warehouse" = {
      application           = "app-etl"
      description           = "app-etl-warehouse: the application's table loaded into the governed warehouse (Stage 9 step 9.4, decision 15)"
      code                  = false
      glue_jobs             = ["awsds-${var.env}-app-etl-load"]
      processing_job_prefix = null
      training_job_prefix   = null
      reads                 = []
      writes                = []
    }
  }

  workflows = var.release == null ? {} : {
    for k, a in local.applications : k => {
      description = a.description
      definition = {
        bucket     = local.outputs_bucket
        key        = "applications/${a.application}/${var.release.tag}/workflows/${k}.yaml"
        version_id = var.release.workflows[k].definition_version_id
      }
      code = a.code ? {
        bucket     = local.outputs_bucket
        key        = "applications/${a.application}/${var.release.tag}/code/${k}.zip"
        version_id = var.release.workflows[k].code_version_id
      } : null
      glue_jobs             = a.glue_jobs
      processing_job_prefix = a.processing_job_prefix
      training_job_prefix   = a.training_job_prefix
      reads                 = a.reads
      writes                = a.writes
    } if contains(keys(var.release.workflows), k)
  }

  # Decision 13: every production workflow starts from a chain, a chain of one included. The cron is
  # UTC; the schedule's state is the pause lever (step 6.1).
  chain_specs = {
    "app-etl" = {
      definition_template = file("${path.module}/chains/app-etl.asl.json")
      workflows           = ["app-etl"]
      schedule_expression = "cron(30 6 * * ? *)"
      schedule_timezone   = "UTC"
      schedule_enabled    = true
    }
    "app-etl-train" = {
      definition_template = file("${path.module}/chains/app-etl-train.asl.json")
      workflows           = ["app-etl-train"]
      schedule_expression = "cron(0 7 * * ? *)"
      schedule_timezone   = "UTC"
      schedule_enabled    = true
    }
    # Paused: the load fails whenever the warehouse compute, [E], is down (Stage 9 decision 15), so its
    # chain is started by hand in a sitting that raises the compute.
    "app-etl-warehouse" = {
      definition_template = file("${path.module}/chains/app-etl-warehouse.asl.json")
      workflows           = ["app-etl-warehouse"]
      schedule_expression = "cron(30 7 * * ? *)"
      schedule_timezone   = "UTC"
      schedule_enabled    = false
    }
  }

  # A chain whose workflows the release carries: a release recorded before a workflow existed creates
  # neither the workflow nor its chain.
  chains = { for k, c in local.chain_specs : k => c if alltrue([for w in c.workflows : contains(keys(local.workflows), w)]) }
}

module "orchestration" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/orchestration?ref=orchestration-v0.2.1"
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
