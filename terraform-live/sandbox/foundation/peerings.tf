# sandbox/foundation/peerings.tf - every peering this account REQUESTS, generated from the
# matrix in scripts/tfhygiene/backend.py (Stage 6c steps 0.6 / 3.1 / 3.4).
#
# CROSS-ACCOUNT, SO IT IS A REQUESTER AND AN ACCEPTER AND TWO APPLIES. `auto_accept` cannot work
# across an account boundary, and that is the boundary doing its job: acceptance is Production's
# own act. This file is the requester half only - the connection sits in `pending-acceptance`
# until `production/networking/` accepts it, and the routes below reference the ACCEPTER's id,
# which is what orders every route after acceptance (AWS requires it).
#
# WHAT THIS BUYS AND WHAT IT DOES NOT. It buys an ADDRESS in VPC-Networking, where the explicit
# proxy runs. It does not buy an internet path: peering shares an address and never a path
# (Lesson 44), so this VPC still reaches the internet only as a CLIENT of that proxy, whose ACL
# decides what it may fetch. That is D38's whole argument, and the reason no NAT gateway exists.
#
# THE ROUTES ARE THE ACCEPTER'S JOB TO MIRROR. A peering with routes on one side only is `active`
# in every console view that shows peerings and dead in every one that shows routes - the defect
# 3.7's NT-11 exists to catch.

# BOTH ROWS NOW, AND THE SECOND ARRIVED BY `moved {}` RATHER THAN BY A REBUILD. Sandbox requests
# two cross-account peerings: VPC-Networking (the proxy, and the VPN's reach) and
# VPC-SharedServices (INT-09 - `git clone` from a notebook). Stage 3 built the second by hand in
# peering.tf; that connection is LIVE, so folding it into the generated shape is an address change
# and nothing else. The block at the foot of this file is what makes it one.
#
# THIS WAS SCOPED TO THE HUB ROW FOR ONE COMMIT, and the reason is worth keeping: selecting on
# `!same_account` alone matched both rows while peering.tf still declared one of them, and `one()`
# raised on the provider profile. That error caught what a wider filter would have BUILT - a
# second Terraform resource for a connection that already existed, in another file, in the same
# state.
locals {
  requested = [for pr in var.peerings : pr if !pr.same_account && pr.role == "requester"]

  # EVERY PEER IN ONE ACCOUNT, ASSERTED RATHER THAN ASSUMED. A provider cannot be iterated, so
  # one alias serves every row - which is only correct while all of them live in one account.
  # `one()` over the DISTINCT profiles is that assertion: the day a spoke peers into a second
  # account, this raises at plan time instead of silently using the wrong credentials.
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

# THE FORWARD ROUTES, AND LEAVING THEM OUT FOR ONE COMMIT WAS THE DEFECT THIS FILE'S OWN HEADER
# NAMES. Between the connection applying and these landing, the peering read `active` in every
# console view that shows peerings and carried nothing - which is precisely what 3.7's NT-11
# exists to catch, arriving as a self-inflicted example.
#
# THE HUB'S PRIVATE AND PUBLIC TIERS, subnet-scoped. Public because the proxy and the WireGuard
# host live there (pass 4); private because that is where anything else in the hub would answer.
# The hub's ISOLATED tier is never a destination - that is what makes it isolated.
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
# THE CONNECTION IS LIVE AND THIS IS AN ADDRESS CHANGE, WHICH IS THE ONLY REASON THESE EXIST.
# Stage 3 declared the INT-09 peering as a singleton in peering.tf; the matrix declares it as one
# row of a for_each. Without these blocks Terraform reads that as a different resource and
# destroys and re-creates it - and a peering re-created is a peering that comes back
# `pending-acceptance`, with every route on both sides pointing at an id that no longer exists.
#
# THEY GO when nothing refers to the old addresses any more - a migration record, not a permanent
# part of the slice, exactly as identity/sso/moved.tf says of itself.

moved {
  from = aws_vpc_peering_connection.to_production
  to   = aws_vpc_peering_connection.to_peer["sandbox-foundation--production-foundation"]
}

moved {
  from = aws_vpc_peering_connection.to_hub["sandbox-foundation--production-networking"]
  to   = aws_vpc_peering_connection.to_peer["sandbox-foundation--production-networking"]
}
