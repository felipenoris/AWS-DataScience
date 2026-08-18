# development/egress/ - the [E] metered network of Development (Stage 3 pass 3): the NAT
# under design A, step 8's Development endpoint list, step 9's org policy on every entry.
# Lifecycle belongs to `make up ENV=development` / `make down ENV=development` (D11), never
# to a by-hand apply (runbook, "What you never do"); `./aws/egress.py` 6 is the burn meter.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).

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

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3) - D5's comparison is Stage 6's.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9) - a selection, not an anchor.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Development row: the three SageMaker endpoints - the same list as Sandbox
  # since 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  extra_services = ["sagemaker.api", "sagemaker.runtime", "sagemaker.studio"]
}
