# What this slice reads and does not own: the [P] states of the slices it watches.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The VPC's id, for its interface-endpoint count, its quota and its DNS Firewall query volume.
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# The warehouse's name, which is the namespace's and the workgroup's: the Redshift metrics carry it
# as their dimension, and the [E] workgroup keeps it across every rebuild.
data "terraform_remote_state" "warehouse" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/warehouse/terraform.tfstate"
    region = var.region
  }
}

# Each quota, read back by its code: its name for the postcondition, its usage metric for the alarm.
data "aws_servicequotas_service_quota" "alarmed" {
  for_each = var.quotas

  service_code = each.value.service_code
  quota_code   = each.value.quota_code

  lifecycle {
    postcondition {
      condition     = strcontains(lower(self.quota_name), each.value.name) && length(self.usage_metric) == 1
      error_message = "${each.value.quota_code} no longer answers as '${each.value.name}' with a usage metric: read the quota in Service Quotas before trusting this alarm (Lesson 38)."
    }
  }
}

locals {
  vpc_id    = data.terraform_remote_state.foundation.outputs.vpc_id
  warehouse = data.terraform_remote_state.warehouse.outputs.namespace_name

  alarm_arn_prefix = "arn:${data.aws_partition.current.partition}:cloudwatch:${var.region}:${data.aws_caller_identity.current.account_id}:alarm:"

  # sandbox/warehouse/alarms.tf's two alarms, by the names that slice gives them.
  warehouse_alarms = ["${local.warehouse}-compute-capacity", "${local.warehouse}-data-storage"]
}
