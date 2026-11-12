# staging/chains/ - the chain layer above deploy-staging's workflows (Stage 19 step 4.11, decision
# 6 (b)): terraform-modules/orchestration called with this account's deployment project and the
# application the CI/CD CLI deploys into it, the same module and the same statements as
# Production's (D20). [P]: a state machine, a schedule and a rule bill nothing at rest, and no
# pipeline job applies the slice.
#
# It takes the place of staging/orchestration/, whose machines, schedules, roles and log group
# carry the same names: that slice is down before this one is applied (runbooks/promotion.md).
#
# A machine starts a workflow the CLI created, so a chain fails with WorkflowNotDeployed until the
# application's first deploy into the project, and reads the parameter that deploy's leg wrote.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "studio" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/studio/terraform.tfstate"
    region = var.region
  }
}

# The account data CMK, whose alias docs/GOVERNANCE.md (Encryption) fixes: the state machines' log
# group is one of the groups its policy admits CloudWatch Logs for.
data "aws_kms_alias" "data" {
  name = "alias/awsds-${var.env}-data"
}

locals {
  # The application's workflows, as its manifest's content.workflows names them and the `staging`
  # stage's bootstrap creates them. The warehouse load is Production's alone: Staging has no
  # warehouse.
  applications = {
    "app-etl" = {
      workflows = ["app-etl", "app-etl-train"]
    }
  }

  # The schedules are DISABLED here (Stage 10 decision 19): the Staging leg starts each chain's
  # machine itself and follows the execution. Production's fire unattended in a sitting that turns
  # them on.
  chains = {
    "app-etl" = {
      definition_template = file("${path.module}/definitions/app-etl.asl.json")
      application         = "app-etl"
      workflows           = ["app-etl"]
      schedule_expression = "cron(30 6 * * ? *)"
      schedule_enabled    = false
    }
    "app-etl-train" = {
      definition_template = file("${path.module}/definitions/app-etl-train.asl.json")
      application         = "app-etl"
      workflows           = ["app-etl-train"]
      schedule_expression = "cron(0 7 * * ? *)"
      schedule_enabled    = false
    }
  }
}

module "orchestration" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/orchestration?ref=orchestration-v0.3.0"

  env = var.env

  project = {
    name    = var.deployment_project_name
    key_arn = data.terraform_remote_state.studio.outputs.project_key_arn
  }

  applications     = local.applications
  alerts_topic_arn = data.terraform_remote_state.foundation.outputs.alerts_topic_arn
  log_key_arn      = data.aws_kms_alias.data.target_key_arn
  chains           = local.chains
}
