# production/workloads-egress/ - VPC-Workloads' [E] endpoint slice (Stage 6c step 1.3a,
# 2026-09-06).
#
# WRITTEN EMPTY, ON PURPOSE, AND THE REASON IS BOOKKEEPING RATHER THAN NETWORKING. The rank,
# the `SLICES` row and this folder land in one commit (Recipe C), and `make down ENV=production`
# has to know about the slice the FIRST time anything is applied into that VPC - not the first
# time somebody remembers it exists. An [E] slice nobody destroys is a bill, and the way that
# happens is a folder arriving after the teardown target was last read.
#
# egress_mode = "B" FROM BIRTH, WHICH IS THE ONLY SHAPE D38 ALLOWS. Mode A creates a NAT gateway
# and its Elastic IP; the estate has ZERO NAT gateways under D38, because a spoke reaches the
# internet as a CLIENT of the explicit proxy in VPC-Networking rather than through a route.
# `production/egress/` still says "A" and step 5.1 is what changes that - this slice never had
# to pass through the shape it is being converted away from.
#
# NO ENDPOINTS UNTIL STAGE 9/10 NAMES THEM, and `extra_services = []` is that statement rather
# than an omission: Stage 9's SageMaker runtime and Stage 10's MWAA Serverless workers are what
# decide the list, and MWAA's is a documented set (`logs`, `monitoring`, `kms`) that arrives
# with a two-AZ requirement - this estate's single D9 exception. Adding endpoints "because the
# other egress slices have them" would bill 0.010/h each for a VPC nothing runs in yet.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3). Here
# the state read is `workloads`, not `foundation`: this slice's VPC is VPC-Workloads.

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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.6.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.workloads.outputs.vpc_id

  # D38: no NAT gateway anywhere in the estate. See the header.

  # Mode B creates no NAT, so this subnet is never used - the variable is still required by the
  # module, and passing the public tier's first subnet is the honest value rather than a
  # placeholder that would read as a mistake.
  name_suffix = "workloads"

  # THE THREE ARGUMENTS THAT STOOD HERE WENT WITH THE NAT AT `vpc-egress-v0.6.0` (6c step 5.1,
  # 2026-09-06): `egress_mode`, `nat_public_subnet_id` and `private_route_table_ids`. Under D38 the
  # estate has ONE internet exit - an explicit proxy in the hub - and no VPC anywhere carries a
  # default route, so there is no design A to select and no route table for this slice to write to.
  # Nothing here needs replacing: what this slice builds now is endpoints and, where it applies, the
  # DNS Firewall.
  endpoint_subnet_id         = data.terraform_remote_state.workloads.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.workloads.outputs.endpoints_security_group_id

  # THE ONE PLACE `core_services` IS OVERRIDDEN, AND THE MODULE SAYS IT NEVER IS. That variable's
  # description reads "Overridden never - the per-role differences go in extra_services", and it
  # was written when every egress slice served a VPC people work in: the core eight are what a
  # notebook or a runner cannot function without under design B. THIS VPC HAS NO WORKLOAD AT ALL
  # yet, so the core set is not a floor here - it is eight interface endpoints at ~0.010/h each,
  # 0.080/h, for a network nothing runs in. Emptying BOTH lists is what makes 1.3a's "written
  # empty" true rather than aspirational, and it is why this slice's usd_per_hour is 0.0 and
  # honest.
  #
  # STAGE 9/10 DECIDES WHAT COMES BACK, and deciding is the point: MWAA Serverless documents its
  # own set (logs, monitoring, kms) and the SageMaker runtime will name others. Restoring the
  # core eight wholesale would be inheriting a list chosen for a different kind of VPC.
  core_services  = []
  extra_services = []
}
