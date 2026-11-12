# orchestration - the chain layer above a deployment project's workflows (D41 item 5; Stage 19 step
# 4.11, decisions 6 (b) and 16 (b)). The SMUS CI/CD CLI creates the workflows in the account's
# deployment project, each named <application>_<project>_<workflow> and run as the project's role.
# This module creates what starts them on a schedule: per account the schedule group, the state
# machines' log group and two roles; per chain a Step Functions state machine, its EventBridge
# Scheduler schedule and its failure rule; per workflow a failure rule on the service's own events.
# Two callers: staging/chains/ and production/chains/, applied by the infrastructure user.
#
# A machine finds its workflow by name at each execution (ListWorkflows), since the ARN carries a
# suffix the service generates and a workflow deleted and created again takes a new one. It passes
# the run the application's stage variables: the CLI writes each `{env.VAR}` of a workflow into the
# deployed definition as an Airflow parameter and fills it only on a run it starts itself, so a run
# another caller starts names every one as OverrideParameters or fails before its first task. The
# deploy leg records them in an SSM parameter after each deploy, and the machine reads it.
#
# No role here touches data, and none is a workflow's execution role. The roles carry no application
# ceiling: awsds-<env>-app-boundary caps what the pipeline creates (Stage 8 step 3.0), and the
# pipeline creates nothing here.
#
# The names are contracts: awsds-<env>-chain-<key>, awsds-<env>-chains, awsds-<env>-chain-exec and
# -chain-scheduler, awsds-<env>-wf-<workflow>-failed, and the parameter
# /awsds/<env>/applications/<application>/stage-variables, which scripts/deploy-application.py writes.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  partition      = data.aws_partition.current.partition
  account_id     = data.aws_caller_identity.current.account_id
  region         = data.aws_region.current.region
  region_account = "${local.region}:${local.account_id}"

  # The CLI's own rule (commands/deploy.py, 1.0.9): each part with every character outside
  # [A-Za-z0-9_] replaced by an underscore, joined by underscores.
  workflow_names = {
    for pair in flatten([
      for app, a in var.applications : [for w in a.workflows : { application = app, workflow = w }]
    ]) :
    "${pair.application}/${pair.workflow}" => join("_", [
      replace(pair.application, "/[^A-Za-z0-9_]/", "_"),
      replace(var.project.name, "/[^A-Za-z0-9_]/", "_"),
      replace(pair.workflow, "/[^A-Za-z0-9_]/", "_"),
    ])
  }

  # A workflow's ARN is its name, a dash and the ten characters the service appends.
  workflow_arn_prefixes = { for k, n in local.workflow_names : k => "arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/${n}-" }
  workflow_arn_patterns = [for k, p in local.workflow_arn_prefixes : "${p}??????????"]

  stage_variables_parameters = { for app, a in var.applications : app => "/awsds/${var.env}/applications/${app}/stage-variables" }

  state_machine_arn_pattern = "arn:${local.partition}:states:${local.region_account}:stateMachine:awsds-${var.env}-chain-*"
}
