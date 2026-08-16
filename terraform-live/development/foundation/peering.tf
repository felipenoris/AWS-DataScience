# development/foundation/peering.tf - the REQUESTER half of Development <-> Production
# (Stage 3 step 6.2, pass 2): D21's path - the `engineering` project's Studio apps clone
# from GitLab over this peering (INT-09). Same shape as sandbox/foundation/peering.tf,
# and the same split for the same ordering reason: accepter, associations and every route
# live in production/foundation/peers.tf, applied third.
#
# The alias below only READS the peer's [P] facts (Lesson 3); it creates nothing, so it
# carries no default_tags. The profile comes from the generated tfvars, never a literal.

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

# The peering request. Acceptance is Production's own act (peers.tf) - Production
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
