# production/egress/ - the [E] metered network of Production (Stage 3 pass 3): the NAT
# (10.3: Staging and Production keep one for the minutes a promotion or a build runs), step
# 8's Production endpoint list, step 9's org policy on every entry. Lifecycle belongs to
# `make up ENV=production` / `make down ENV=production` (D11), never to a by-hand apply
# (runbook, "What you never do"); `./aws/egress.py` 6 is the burn meter.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).
#
# NOT HERE YET, each with its trigger (8.7): `states` + `scheduler` under D7(B) when Stage 8
# builds orchestration; `ssm`+`ssmmessages`+`ec2messages` the first time the GitLab host is
# needed outside a build window; `secretsmanager` with gitlab-secrets.json (Stage 7 step 1).
# The internal ALB for GitLab/Pages joins this slice at Stage 7 (conventions §6).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.1.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Step 10.3: Production is NOT governed by D5 - the NAT stays whatever Stage 6 decides
  # for the Interactive accounts. Still mode A, but for its own reason.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9) - a selection, not an anchor.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Production row: sagemaker.api + sagemaker.runtime, no sagemaker.studio
  # (no Studio domain here - endpoints for people belong to the Interactive accounts).
  # lakeformation stays IN the core deliberately: Production holds the LF read AND governed
  # write share (D22), so there it is load-bearing, not speculative.
  extra_services = ["sagemaker.api", "sagemaker.runtime"]
}
