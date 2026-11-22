# What this slice reads and does not own: the [P] states of the slices it watches. Never a [D]
# slice's state (Lesson 4): the three host alarms are named by the convention their slices write
# them under, so a stopped or replaced host changes nothing here.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# VPC-SharedServices' id, for its interface-endpoint count, and awsds-prod-alerts, every alarm's
# target (Stage 8 decision 5).
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# The proxy's access log group, which the two metric filters read.
data "terraform_remote_state" "networking" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/networking/terraform.tfstate"
    region = var.region
  }
}

# VPC-Workloads' id, for its interface-endpoint count and its DNS Firewall query volume.
data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

locals {
  alerts_topic_arn = data.terraform_remote_state.foundation.outputs.alerts_topic_arn
  proxy_log_group  = data.terraform_remote_state.networking.outputs.proxy_access_log_group_name
  shared_vpc_id    = data.terraform_remote_state.foundation.outputs.vpc_id
  workloads_vpc_id = data.terraform_remote_state.workloads.outputs.vpc_id

  alarm_arn_prefix = "arn:${data.aws_partition.current.partition}:cloudwatch:${var.region}:${data.aws_caller_identity.current.account_id}:alarm:"

  # The [D] hosts' alarms, by the names their slices give them: production/vpn/ through the
  # wireguard module (observability.tf), production/proxy/main.tf and production/tooling/main.tf.
  host_alarms = {
    vpn    = "awsds-${var.env}-vpn-health"
    proxy  = "awsds-${var.env}-proxy-status-check"
    gitlab = "awsds-${var.env}-gitlab-status-check"
  }

  # The WireGuard handshake log, written by the same module under this name.
  vpn_log_group = "/awsds/${var.env}/vpn"

  # The namespace of the proxy log's metric filters - the project's own, never an AWS/ one.
  proxy_metric_namespace = "AWSDS/Proxy"
}
