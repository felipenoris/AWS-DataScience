# production/foundation/zone-associations.tf - Stage 6c step 2.5.
#
# VPC-SharedServices resolves `prod.awsds.internal`, which `production/workloads/` owns. GitLab and
# the runners live in this VPC and deploy into the runtime's. A deploy is an API act (3.2), but the
# names a pipeline logs, probes and reports on are the runtime's, and a VPC that cannot resolve
# them reports NXDOMAIN rather than a failure anyone can read.
#
# The apex and the pages zone are not here: this slice owns both, and a zone is associated with its
# owner's VPC by the inline `vpc` block at creation (zones.tf). Associating them again would be a
# second association of the same pair.

data "terraform_remote_state" "prod_workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

resource "aws_route53_zone_association" "prod_apex" {
  zone_id = data.terraform_remote_state.prod_workloads.outputs.prod_awsds_internal_zone_id
  vpc_id  = module.vpc.vpc_id
}
