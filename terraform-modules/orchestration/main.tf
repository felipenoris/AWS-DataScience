# orchestration - Stage 10's [E] slice body, one design in the two deployment targets (D7 amended,
# D28, D41): the MWAA Serverless workflows with their execution roles, log groups and failure rules
# (steps 1.1-1.3, 3.1), the workers' security group (1.2), and the chain layer above the workflows -
# per account the schedule group, the state machines' log group and the three chain roles, per chain
# a Step Functions state machine, its EventBridge Scheduler schedule and its failure rule, per bridge
# an EventBridge rule on the account's inbox (3.4-3.7). Two callers: staging/orchestration/ and
# production/orchestration/, applied by the pipeline as awsds-deploy-staging and awsds-deploy-prod
# (step 1.5, INT-14).
#
# Every role carries the application ceiling awsds-<env>-app-boundary: the deploy role's own ceiling
# refuses CreateRole, and every policy change on a role, without it (Stage 8 step 3.0). No role here
# holds a lake permission: the execution roles start and observe jobs and reach the outputs bucket's
# result and inbox prefixes, the chain roles start and read workflows (D13 one level up).
#
# The names are contracts ./aws/orchestration.py reads (OR-1 to OR-5, OR-9): awsds-<env>-wf-<key>,
# /awsds/<env>/wf/<key>, awsds-<env>-chain-<key>, awsds-<env>-chains, awsds-<env>-chain-exec,
# -chain-scheduler and -chain-events, awsds-<env>-inbox-<app>.

data "aws_partition" "current" {}

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

locals {
  partition      = data.aws_partition.current.partition
  account_id     = data.aws_caller_identity.current.account_id
  region         = data.aws_region.current.region
  region_account = "${local.region}:${local.account_id}"

  outputs_bucket_arn = "arn:${local.partition}:s3:::${var.outputs_bucket}"

  # A workflow's ARN is its name plus a dash and ten characters the service appends, so a grant on
  # every workflow of this account is a pattern on the name.
  workflow_arn_pattern      = "arn:${local.partition}:airflow-serverless:${local.region_account}:workflow/awsds-${var.env}-wf-*"
  state_machine_arn_pattern = "arn:${local.partition}:states:${local.region_account}:stateMachine:awsds-${var.env}-chain-*"
}

# ------------------------------------------------------------------- the workers' network (1.2)
#
# The private-routing shape: a security group whose inbound rule references itself and whose
# outbound rule admits all traffic. The subnets carry no route to a NAT device or an internet
# gateway, so the outbound rule reaches the VPC's interface endpoints and the S3 gateway endpoint
# and nothing else.
resource "aws_security_group" "workers" {
  # checkov:skip=CKV2_AWS_5:attached by awscc_mwaaserverless_workflow's network_configuration, which checkov does not read as an attachment
  name        = "awsds-${var.env}-wf-workers"
  description = "MWAA Serverless workers in the private-routing shape: inbound from itself, outbound to the VPC (Stage 10 step 1.2)"
  vpc_id      = var.vpc_id

  tags = {
    Name = "awsds-${var.env}-wf-workers"
  }
}

resource "aws_vpc_security_group_ingress_rule" "workers_self" {
  security_group_id            = aws_security_group.workers.id
  description                  = "All traffic between the workers, the documented self-referencing rule"
  ip_protocol                  = "-1"
  referenced_security_group_id = aws_security_group.workers.id
}

resource "aws_vpc_security_group_egress_rule" "workers_all" {
  # checkov:skip=CKV_AWS_382:the documented private-routing shape; with no NAT and no internet gateway route the rule reaches the VPC endpoints alone
  security_group_id = aws_security_group.workers.id
  description       = "All traffic out; the subnets route to no NAT device or internet gateway"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"
}
