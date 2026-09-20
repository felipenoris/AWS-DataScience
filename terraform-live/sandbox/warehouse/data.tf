# What this slice reads and does not own.

data "aws_caller_identity" "current" {}

# The account data CMK. ONE DATA KEY PER ACCOUNT (docs/GOVERNANCE.md Encryption), and the warehouse
# is a data store in this account, so it takes Sandbox's data key exactly as awsds-sandbox-lake
# does. Read through remote state rather than by alias lookup: an alias resolves to whatever wears
# it, remote state resolves to what data/ built (Lesson 3).
data "terraform_remote_state" "data" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/data/terraform.tfstate"
    region = var.region
  }
}

# The VPC the workgroup's security group lives in. The subnets themselves are read by
# sandbox/warehouse-compute/, which owns the workgroup; this slice needs the VPC id alone.
data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

# Each admitted project's role, read rather than assumed - the same two reasons sandbox/bedrock/
# reads its own:
#
#   - A MISSING PROJECT FAILS AT PLAN with "no IAM role found", naming the role, instead of at
#     apply with a NoSuchEntity from the attachment.
#   - THE BOUNDARY IS CHECKED (iam.tf's precondition). A role that is not under
#     awsds-sandbox-project-boundary is not a project role this estate governs, whatever its name
#     looks like, and granting it GetCredentials would put a database session outside D13.
data "aws_iam_role" "project" {
  for_each = var.projects
  name     = each.value.role_name
}

# Each admitted project's own security group - the group SMUS attaches to the project's app ENIs.
# It is looked up BY NAME because the service created it and named it after the project id; there
# is no state anywhere in this repository that holds its id. A project whose group has been renamed
# or deleted fails at plan, which is the right place: the alternative is a workgroup whose ingress
# rule points at nothing and a JupyterLab connection that times out with no message.
data "aws_security_group" "project" {
  for_each = var.projects

  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  filter {
    name   = "group-name"
    values = [each.value.security_group_name]
  }
}

locals {
  name = "awsds-${var.env}-warehouse"

  data_key_arn  = data.terraform_remote_state.data.outputs.data_key_arn
  boundary_name = "awsds-${var.env}-project-boundary"

  # The three audit log types. The group path is DERIVED FROM THE NAMESPACE NAME by the service -
  # AWS: "/aws/redshift/<namespace>/<log_type>" - so a namespace rename moves three log groups, and
  # that is why the namespace name is a contract Stage 5b fixes rather than a value anybody edits.
  log_types = ["userlog", "connectionlog", "useractivitylog"]

  # 0.024 USD/GB-month (docs/PRICING.md 5, Price List offer file published 2026-09-11) and the
  # DataStorage metric is in MEGABYTES. Both halves of the conversion are here so the threshold can
  # be argued in dollars and the alarm can still be compared against the metric.
  storage_usd_per_gb_month = 0.024
  storage_alarm_mb         = ceil(var.storage_alarm_usd / local.storage_usd_per_gb_month * 1024)
}
