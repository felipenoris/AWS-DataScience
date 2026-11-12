# production/chains/ - the chain layer above deploy-production's workflows (Stage 19 step 4.11,
# decisions 6 (b) and 16 (b)): terraform-modules/orchestration called with this account's deployment
# project and the application the CI/CD CLI deploys into it. [P]: a state machine, a schedule and a
# rule bill nothing at rest, and no pipeline job applies the slice.
#
# It takes the place of production/orchestration/, whose machines, schedules, roles and log group
# carry the same names: that slice is destroyed before this one is applied (runbooks/promotion.md).
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
  # The application's workflows, as its manifest's content.workflows names them. app-etl-warehouse
  # is created by the `prod` stage's bootstrap alone (decision 16 (b)): Staging has no warehouse.
  applications = {
    "app-etl" = {
      workflows = ["app-etl", "app-etl-train", "app-etl-warehouse"]
    }
  }

  # Every production workflow starts from a chain, a chain of one included (Stage 10 decision 13).
  # The cron is UTC; the schedule's state is the pause lever (Stage 10 step 6.1).
  # Paused between sittings: a run needs production/workloads-egress/'s endpoints, [E], so a sitting
  # that wants the scheduled runs raises the endpoints and turns these on by a commit. The load
  # also needs the warehouse compute, [E] (Stage 9 decision 15).
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
    "app-etl-warehouse" = {
      definition_template = file("${path.module}/definitions/app-etl-warehouse.asl.json")
      application         = "app-etl"
      workflows           = ["app-etl-warehouse"]
      schedule_expression = "cron(30 7 * * ? *)"
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
