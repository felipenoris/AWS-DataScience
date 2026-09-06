# production/workloads/zone-associations.tf - Stage 6c step 2.5.
#
# VPC-Workloads resolves TWO zones and the second one is its own: `prod.awsds.internal` is
# associated at creation (zones.tf), and the estate apex is associated here so the runtime can
# reach `gitlab.awsds.internal` and `proxy.awsds.internal` by name. It is NOT associated with
# `sandbox.` or `staging.` - a deployment target has no business resolving another environment's
# private names, and INT-22's matrix says so by omission rather than by a rule.
#
# SAME ACCOUNT, SO THE VPC OWNER SIMPLY ASSOCIATES: the authorization/association pair is a
# cross-account protocol and there is nothing to authorize here.

data "terraform_remote_state" "prod_foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

resource "aws_route53_zone_association" "apex" {
  zone_id = data.terraform_remote_state.prod_foundation.outputs.awsds_internal_zone_id
  vpc_id  = module.vpc.vpc_id
}
