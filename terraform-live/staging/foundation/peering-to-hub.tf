# ------------------------------------------------ the peering to the hub (Stage 6c step 3.4)
#
# Cross-account, so it is a requester, an accepter and two applies: `auto_accept` cannot work
# across an account boundary, and acceptance is Production's own act. This file is the requester
# half only - the connection sits in `pending-acceptance` until `production/networking/` accepts
# it, and the routes below reference the accepter's id, which AWS requires before any route.
#
# What it buys is an address in VPC-Networking, where the explicit proxy runs. It does not buy an
# internet path: peering shares an address and never a path (Lesson 44), so this VPC reaches the
# internet only as a client of that proxy, whose ACL decides what it may fetch (D38).
#
# The accepter mirrors the routes. A peering with routes on one side only reads `active` in every
# console view that shows peerings and dead in every one that shows routes - the defect NT-11
# (step 3.7) exists to catch.

# Scoped to the hub row. The filter names the peer slice because one account can request more
# than one cross-account peering - Sandbox requests this one to VPC-Networking and the INT-09 one
# to VPC-SharedServices, which `peering.tf` owns there by hand. On `!same_account` alone both
# match and `one()` raises, instead of a second Terraform resource for a peering that already
# exists in another file in the same state.
locals {
  hub_peerings = [
    for pr in var.peerings : pr
    if !pr.same_account && pr.role == "requester" && pr.peer_slice == "networking"
  ]
}

provider "aws" {
  alias   = "hub"
  region  = var.region
  profile = one([for pr in local.hub_peerings : pr.peer_profile])
}

data "aws_vpc" "hub" {
  provider = aws.hub

  filter {
    name   = "tag:Name"
    values = ["awsds-${one([for pr in local.hub_peerings : pr.peer_env])}-${one([for pr in local.hub_peerings : pr.peer_name_suffix])}-vpc"]
  }
}

resource "aws_vpc_peering_connection" "to_hub" {
  for_each = { for pr in local.hub_peerings : pr.key => pr }

  vpc_id        = module.vpc.vpc_id
  peer_vpc_id   = data.aws_vpc.hub.id
  peer_owner_id = data.aws_vpc.hub.owner_id

  tags = {
    Name = "${local.name_prefix}-to-${each.value.peer_name_suffix}"
  }
}

# The forward routes, scoped to the hub's private and public subnets. Public because the proxy
# and the WireGuard host live there (pass 4); private because that is where anything else in the
# hub would answer. The hub's isolated tier is never a destination.
data "aws_subnets" "hub_reachable" {
  provider = aws.hub

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.hub.id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private", "public"]
  }
}

data "aws_subnet" "hub_reachable" {
  provider = aws.hub
  for_each = toset(data.aws_subnets.hub_reachable.ids)

  id = each.key
}

locals {
  hub_forward_routes = {
    for pair in setproduct(
      keys(module.vpc.private_route_table_ids),
      keys(data.aws_subnet.hub_reachable)
    ) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = module.vpc.private_route_table_ids[pair[0]]
      cidr           = data.aws_subnet.hub_reachable[pair[1]].cidr_block
    }
  }
}

resource "aws_route" "to_hub" {
  for_each = local.hub_forward_routes

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = one(values(aws_vpc_peering_connection.to_hub)).id
}
