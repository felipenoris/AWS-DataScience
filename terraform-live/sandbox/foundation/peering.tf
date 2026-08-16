# sandbox/foundation/peering.tf - the REQUESTER half of Sandbox <-> Production (Stage 3
# step 6.1, pass 2). Everything else in the cross-account handshake - the accepter, the
# zone associations of 4.4, every route of 6.3 - lives in production/foundation/peers.tf,
# and the split is ordering, not taste: an association needs its authorization to exist
# first, and a route to a peering needs the peering ACTIVE, so the one place all of that
# can happen in a single ordered apply is the accepting side, after both requesters exist.
# Pass 2 is therefore three applies: sandbox, development, then production.
#
# The alias below only READS the peer's [P] facts (Lesson 3: an id pasted across an
# account boundary invalidates itself; a data source cannot go stale). It creates nothing,
# so it carries no default_tags. The profile comes from the generated tfvars - the same
# PROFILES table every command line uses - never a literal here.

provider "aws" {
  alias   = "production"
  region  = var.region
  profile = var.peers["production"].profile
}

data "aws_caller_identity" "production" {
  provider = aws.production
}

data "aws_vpc" "production" {
  provider = aws.production

  filter {
    name   = "tag:Name"
    values = ["awsds-${var.peers["production"].env}-vpc"]
  }
}

# The peering request. auto_accept cannot work across accounts; acceptance is
# Production's own act (peers.tf), which is the point of the boundary: Production
# accepts two peerings and nothing else (step 6.2).
resource "aws_vpc_peering_connection" "to_production" {
  vpc_id        = module.vpc.vpc_id
  peer_vpc_id   = data.aws_vpc.production.id
  peer_owner_id = data.aws_caller_identity.production.account_id
  auto_accept   = false

  tags = {
    Name = "awsds-${var.env}-to-prod"
    Side = "requester"
  }
}
