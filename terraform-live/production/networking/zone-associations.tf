# production/networking/zone-associations.tf - Stage 6c step 2.5, the hub's half of INT-22.
#
# The hub is associated with every zone in the estate, the one asymmetry in the matrix.
# VPC-Networking is where the WireGuard endpoint terminates (step 4.7), so it is the VPC the VPN
# client resolves through, and a client that cannot resolve `gitlab.awsds.internal` or
# `<unit>.sandbox.awsds.internal` has no way to reach a private name at all. Every other VPC is
# associated only with what its own workloads need.
#
# A private zone answers for its whole subtree (Lessons 40-43). Associating a zone here makes it
# authoritative for that name inside this VPC, so a zone associated by mistake shadows the public
# answer for every client on the tunnel. The same mechanism is why this VPC carries no interface
# endpoint with private DNS.
#
# A VPC associated with a matching zone that holds no record gets **NXDOMAIN**, not a public
# answer, so a missing association and a missing name are indistinguishable while debugging.
# INT-22's matrix is therefore written down and read by a check (step 2.4) rather than re-derived
# from these resources.

data "terraform_remote_state" "prod_foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "prod_workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

# These zones are in this account, so no authorization exists or is needed: the
# authorization/association pair is a cross-account protocol, and within one account the VPC owner
# associates directly. The cross-account half of this matrix, the two spoke child zones, is 2.5's
# reversed direction below.
locals {
  hub_zone_ids = {
    apex      = data.terraform_remote_state.prod_foundation.outputs.awsds_internal_zone_id
    pages     = data.terraform_remote_state.prod_foundation.outputs.awsds_pages_internal_zone_id
    prod_apex = data.terraform_remote_state.prod_workloads.outputs.prod_awsds_internal_zone_id
  }
}

resource "aws_route53_zone_association" "hub" {
  for_each = local.hub_zone_ids

  zone_id = each.value
  vpc_id  = module.vpc.vpc_id
}

# ------------------------------------------------- the reversed handshake (step 2.5, INT-22)
#
# This direction is the opposite of every other cross-account association in the estate. Elsewhere
# Production owns the zones and the spokes associate their VPCs into them. The apex family inverts
# one case: each spoke owns its own child zone (`sandbox.awsds.internal`,
# `staging.awsds.internal`) and this VPC, the one the VPN client resolves through, has to be
# associated into it.
#
# AWS's procedure has no console path: the zone owner runs create-vpc-association-authorization,
# one request per VPC, and then the VPC owner runs associate-vpc-with-hosted-zone. Both halves are
# here because an aliased provider lets this slice act as the zone owner for the first half, the
# same shape peers.tf uses for the peering accepters.
#
# AWS recommends deleting the authorization afterwards and this project keeps it in state, the same
# divergence peers.tf records for the peering pair: deleting it does not affect the association,
# but keeping the resource is what makes the destroy order expressible.

provider "aws" {
  alias   = "sandbox"
  region  = var.region
  profile = var.peers["sandbox"].profile
}

provider "aws" {
  alias   = "staging"
  region  = var.region
  profile = var.peers["staging"].profile
}

# The zones are read, never pasted (Lesson 3): a zone id in a tfvars would be a stale copy of
# another account's state, and this data source cannot go stale.
data "aws_route53_zone" "sandbox_child" {
  provider     = aws.sandbox
  name         = "sandbox.awsds.internal"
  private_zone = true
}

data "aws_route53_zone" "staging_child" {
  provider     = aws.staging
  name         = "staging.awsds.internal"
  private_zone = true
}

resource "aws_route53_vpc_association_authorization" "sandbox_child" {
  provider = aws.sandbox

  zone_id = data.aws_route53_zone.sandbox_child.zone_id
  vpc_id  = module.vpc.vpc_id
}

resource "aws_route53_vpc_association_authorization" "staging_child" {
  provider = aws.staging

  zone_id = data.aws_route53_zone.staging_child.zone_id
  vpc_id  = module.vpc.vpc_id
}

# depends_on carries the half the ids do not: the authorization exposes no attribute the
# association consumes, so nothing orders them without saying so.
resource "aws_route53_zone_association" "sandbox_child" {
  zone_id = data.aws_route53_zone.sandbox_child.zone_id
  vpc_id  = module.vpc.vpc_id

  depends_on = [aws_route53_vpc_association_authorization.sandbox_child]
}

resource "aws_route53_zone_association" "staging_child" {
  zone_id = data.aws_route53_zone.staging_child.zone_id
  vpc_id  = module.vpc.vpc_id

  depends_on = [aws_route53_vpc_association_authorization.staging_child]
}
