# sandbox/foundation/peerings.tf - every peering this account requests, generated from the matrix in
# scripts/tfhygiene/backend.py (Stage 6c steps 0.6 / 3.1 / 3.4).
#
# A cross-account peering is a requester, an accepter and two applies: `auto_accept` cannot work
# across an account boundary, so acceptance is Production's own act. This file is the requester half.
# The connection sits in `pending-acceptance` until `production/networking/` accepts it, and the
# routes below reference the accepter's id, which is what orders every route after acceptance (AWS
# requires it).
#
# The peering buys an address in VPC-Networking, where the explicit proxy runs. It does not buy an
# internet path: peering shares an address and never a path (Lesson 44), so this VPC reaches the
# internet only as a client of that proxy, whose ACL decides what it may fetch (D38). No NAT gateway
# exists.
#
# The routes are the accepter's job to mirror. A peering with routes on one side only is `active` in
# every console view that shows peerings and dead in every one that shows routes - the defect 3.7's
# NT-11 exists to catch.

# Sandbox requests two cross-account peerings: VPC-Networking (the proxy, and the VPN's reach) and
# VPC-SharedServices (INT-09 - `git clone` from a notebook).
locals {
  requested = [for pr in var.peerings : pr if !pr.same_account && pr.role == "requester"]

  # A provider cannot be iterated, so one alias serves every row, which is correct only while all of
  # them live in one account. `one()` over the distinct profiles asserts that: the day a spoke peers
  # into a second account, this raises at plan time instead of silently using the wrong credentials.
  peer_profile = one(distinct([for pr in local.requested : pr.peer_profile]))
}

provider "aws" {
  alias   = "peer"
  region  = var.region
  profile = local.peer_profile
}

data "aws_vpc" "peer" {
  provider = aws.peer
  for_each = { for pr in local.requested : pr.key => pr }

  filter {
    name = "tag:Name"
    values = [
      each.value.peer_name_suffix == "" ?
      "awsds-${each.value.peer_env}-vpc" :
      "awsds-${each.value.peer_env}-${each.value.peer_name_suffix}-vpc"
    ]
  }
}

data "aws_caller_identity" "peer" {
  provider = aws.peer
}

resource "aws_vpc_peering_connection" "to_peer" {
  for_each = { for pr in local.requested : pr.key => pr }

  vpc_id        = module.vpc.vpc_id
  peer_vpc_id   = data.aws_vpc.peer[each.key].id
  peer_owner_id = data.aws_caller_identity.peer.account_id
  auto_accept   = false

  tags = {
    Name = "awsds-${var.env}-to-${each.value.peer_name_suffix == "" ? each.value.peer_env : each.value.peer_name_suffix}"
    Side = "requester"
  }
}

# The forward routes, scoped to the hub's private and public tiers by subnet. Public because the
# proxy and the WireGuard host live there (pass 4); private because that is where anything else in
# the hub would answer. The hub's isolated tier is never a destination.
locals {
  hub_key = one([for pr in local.requested : pr.key if pr.peer_slice == "networking"])
}

data "aws_subnets" "hub_reachable" {
  provider = aws.peer

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.peer[local.hub_key].id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private", "public"]
  }
}

data "aws_subnet" "hub_reachable" {
  provider = aws.peer
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
  vpc_peering_connection_id = aws_vpc_peering_connection.to_peer[local.hub_key].id
}

# ---------------------------------------------------------------- 6c 3.4: the INT-09 fold
#
# Stage 3 declared the INT-09 peering as a singleton in peering.tf; the matrix declares it as one row
# of a for_each. The connection is live, so this is an address change. Without these blocks Terraform
# reads it as a different resource and destroys and re-creates it - and a re-created peering comes
# back `pending-acceptance`, with every route on both sides pointing at an id that no longer exists.
#
# They go when nothing refers to the old addresses any more: a migration record, not a permanent part
# of the slice, as identity/sso/moved.tf says of itself.

moved {
  from = aws_vpc_peering_connection.to_production
  to   = aws_vpc_peering_connection.to_peer["sandbox-foundation--production-foundation"]
}

moved {
  from = aws_vpc_peering_connection.to_hub["sandbox-foundation--production-networking"]
  to   = aws_vpc_peering_connection.to_peer["sandbox-foundation--production-networking"]
}
