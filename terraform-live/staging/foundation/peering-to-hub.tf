# ------------------------------------------------- Stage 6c step 3.4: the peering to the hub
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

# SCOPED TO THE HUB ROW, AND THE FILTER IS NOT COSMETIC. Sandbox requests TWO cross-account
# peerings - this one to VPC-Networking, and the INT-09 one to VPC-SharedServices that Stage 3
# built and `peering.tf` still owns by hand. Selecting on `!same_account` alone matched both and
# `one()` raised, which is the error catching the thing a wider filter would have BUILT: a second
# Terraform resource for a peering that already exists, in a different file, in the same state.
#
# THE INT-09 ROW STAYS IN peering.tf FOR NOW, and folding it in is a `moved {}` block rather than
# a rewrite - the connection is live and INT-09 rides it. That commit is its own.
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

# THE FORWARD ROUTES, AND LEAVING THEM OUT FOR ONE COMMIT WAS THE DEFECT THIS FILE'S OWN HEADER
# NAMES. Between the connection applying and these landing, the peering read `active` in every
# console view that shows peerings and carried nothing - which is precisely what 3.7's NT-11
# exists to catch, arriving as a self-inflicted example.
#
# THE HUB'S PRIVATE AND PUBLIC TIERS, subnet-scoped. Public because the proxy and the WireGuard
# host live there (pass 4); private because that is where anything else in the hub would answer.
# The hub's ISOLATED tier is never a destination - that is what makes it isolated.
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
