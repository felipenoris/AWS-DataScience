# production/egress/ - the [E] metered network of Production (Stage 3 pass 3): step 8's Production
# endpoint list, step 9's org policy on every entry. Lifecycle belongs to `make up ENV=production`
# / `make down ENV=production` (D11), never to a by-hand apply (runbook, "What you never do");
# `./aws/egress.py` 6 is the burn meter.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).
#
# Not here yet, each with its trigger (8.7): `states` + `scheduler` under D7(B) when Stage 8 builds
# orchestration; `secretsmanager` with gitlab-secrets.json (Stage 7 step 1). The internal ALB for
# GitLab/Pages joins this slice at Stage 7 (conventions §6).

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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.11.1"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Single-AZ resources land in the first authored zone (D9) - a selection, not an anchor.
  name_suffix = "shared"

  # No `egress_mode`, `nat_public_subnet_id` or `private_route_table_ids`: under D38 the estate has
  # one internet exit - an explicit proxy in the hub - and no VPC carries a default route, so there
  # is no mode to select and no route table for this slice to write to. What it builds is endpoints
  # and, where it applies, the DNS Firewall.
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Production row: sagemaker.api + sagemaker.runtime, no sagemaker.studio (no Studio
  # domain here - endpoints for people belong to the Interactive accounts). lakeformation stays in
  # the core: Production holds the LF read and governed write share (D22), so there it is
  # load-bearing.
  #
  # The Session Manager trio arrives at step 5.5 (2026-09-06). Session Manager does not work
  # through an HTTPS proxy listener, so with no default route in this VPC the shell is these three
  # endpoints or nothing - and the shell that reads the proxy's own access log must not depend on
  # the proxy (Lesson 24).
  #
  # They precede their first user by one step. This VPC held zero instances when they were added
  # (measured 2026-09-06 - Production's only two are in VPC-Networking, and those reach SSM through
  # the IGW); step 5.8 lands the buildbox here and Stage 7 the runners. The slice is `[E]`, so
  # nothing is billed until a `make up`.
  extra_services = [
    # Vestigial from Stage 3, when production/foundation was simply "the" Production VPC. This VPC
    # is SharedServices now - the supply chain and the build hosts - and whether a SageMaker name
    # still belongs is Stage 7/9's question. Left rather than trimmed on the way past: removing an
    # endpoint because it looks out of place is how a path disappears.
    "sagemaker.api",
    "sagemaker.runtime",

    "ssm",
    "ssmmessages",
    "ec2messages",
  ]
}
