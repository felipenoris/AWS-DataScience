# production/workloads-egress/ - VPC-Workloads' [E] endpoint slice (Stage 6c step 1.3a,
# 2026-09-06).
#
# The slice is written empty for bookkeeping rather than networking. The rank, the `SLICES` row and
# this folder land in one commit (Recipe C), so `make down ENV=production` knows about the slice the
# first time anything is applied into that VPC. An [E] slice nobody destroys is a bill, and that is
# what a folder arriving after the teardown target was last read produces.
#
# There is no NAT gateway here, and none anywhere in the estate: under D38 a spoke reaches the
# internet as a client of the explicit proxy in VPC-Networking rather than through a route.
#
# No endpoints until Stage 9/10 names them, and `extra_services = []` is that statement rather than
# an omission: Stage 9's SageMaker runtime and Stage 10's MWAA Serverless workers decide the list,
# and MWAA's is a documented set (`logs`, `monitoring`, `kms`) that arrives with a two-AZ
# requirement - this estate's single D9 exception. Adding endpoints because the other egress slices
# have them would bill 0.010/h each for a VPC nothing runs in yet.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3). Here the
# state read is `workloads`, not `foundation`: this slice's VPC is VPC-Workloads.

data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.11.1"

  env    = var.env
  vpc_id = data.terraform_remote_state.workloads.outputs.vpc_id

  name_suffix = "workloads"

  # No `egress_mode`, `nat_public_subnet_id` or `private_route_table_ids`: under D38 the estate has
  # one internet exit - an explicit proxy in the hub - and no VPC carries a default route, so there
  # is no mode to select and no route table for this slice to write to. What it builds is endpoints
  # and, where it applies, the DNS Firewall.
  endpoint_subnet_id         = data.terraform_remote_state.workloads.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.workloads.outputs.endpoints_security_group_id

  # This is the one place `core_services` is overridden, and the module's own description reads
  # "Overridden never - the per-role differences go in extra_services". That was written when every
  # egress slice served a VPC people work in: the core eight are what a notebook or a runner cannot
  # function without under design B. This VPC has no workload yet, so the core set is not a floor
  # here - it is eight interface endpoints at ~0.010/h each, 0.080/h, for a network nothing runs
  # in. Emptying both lists is what makes 1.3a's "written empty" true, and why this slice's
  # usd_per_hour is 0.0.
  #
  # Stage 9/10 decides what comes back: MWAA Serverless documents its own set (logs, monitoring,
  # kms) and the SageMaker runtime will name others. Restoring the core eight wholesale would
  # inherit a list chosen for a different kind of VPC.
  #
  # Step 5.5 asked for `ssm`/`ssmmessages`/`ec2messages` here and they are absent (2026-09-06). The
  # step's qualifier excludes this VPC: it says every instance-bearing spoke, and VPC-Workloads
  # bears none - measured, Production's only two instances are in VPC-Networking. Adding them would
  # be 0.030/h of Session Manager path for a network with nothing to manage. They arrive with the
  # first workload, from Stage 9/10, beside the rest of that list.
  core_services  = []
  extra_services = []
}
