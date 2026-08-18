# sandbox/egress/ - the [E] metered network of a business unit's sandbox (Stage 3 pass 3):
# the NAT under design A, the interface endpoints of step 8's Sandbox list, and step 9's
# org policy on every one of them. THE REPOSITORY'S FIRST [E] SLICE: its lifecycle belongs
# to `make up ENV=sandbox` / `make down ENV=sandbox` (D11), never to a by-hand apply
# (runbook, "What you never do") - a forgotten session costs ~USD 3.84/day and no budget
# alert exists to say so (D12); `./aws/egress.py` 6 is the burn meter that risk gets.
#
# foundation/'s [P] facts arrive through terraform_remote_state - the read its outputs.tf
# announces - never pasted (Lesson 3) and never looked up by tag: a tag lookup answers
# "what matches", remote state answers "what foundation/ BUILT", and for wiring two slices
# of one account the second question is the one being asked.

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

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3), not the outcome - D5's
  # comparison against B (no default route, CodeArtifact as the package path) is Stage 6's.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9); the maps stay keyed by
  # zone id, so this is a selection, not an anchor on list position.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Sandbox row: the three SageMaker endpoints (sagemaker.studio is what lets
  # JupyterLab/Code Editor apps START in a VPC-only domain). elasticfilesystem sat here
  # until 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  extra_services = ["sagemaker.api", "sagemaker.runtime", "sagemaker.studio"]
}
