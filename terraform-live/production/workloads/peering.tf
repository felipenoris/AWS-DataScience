# production/workloads/peering.tf - Stage 6c step 3.4, the SAME-ACCOUNT half of the matrix.
#
# A PEERING INSIDE ONE ACCOUNT IS ONE RESOURCE, not the requester/accepter pair every other
# peering in this estate needs. `auto_accept` works only when both VPCs belong to the same
# account, and both of these do - so `same_account` in the generated row is what selects the
# shape, and this file simply filters for it.
#
# WHAT THE PEERING IS FOR, AND WHAT IT IS NOT. VPC-Workloads reaches VPC-Networking to use the
# explicit proxy that lives there (pass 4). It does NOT get an internet path by doing so:
# peering shares an ADDRESS and never a PATH (Lesson 44) - the proxy is an application-layer hop
# whose ACL decides what this VPC may fetch, which is the entire argument of D38.
#
# THE ROUTES ARE SUBNET-SCOPED ON BOTH SIDES, not `10.31.0.0/16`. A route table entry is the
# cheapest place to be specific, and a whole-VPC route grants reach to every tier the peer will
# ever add - including its public one, which is the only tier in the estate with an internet
# gateway in front of it.

locals {
  hub_peering = [for pr in var.peerings : pr if pr.same_account && pr.role == "requester"]
}

data "aws_vpc" "peer" {
  for_each = { for pr in local.hub_peering : pr.key => pr }

  filter {
    name   = "tag:Name"
    values = ["awsds-${each.value.peer_env}-${each.value.peer_name_suffix}-vpc"]
  }
}

resource "aws_vpc_peering_connection" "to_peer" {
  for_each = { for pr in local.hub_peering : pr.key => pr }

  vpc_id      = module.vpc.vpc_id
  peer_vpc_id = data.aws_vpc.peer[each.key].id
  auto_accept = true

  tags = {
    Name = "${local.name_prefix}-to-${each.value.peer_name_suffix}"
  }
}

# The peer's PRIVATE and PUBLIC subnets - private because that is where a service would answer,
# public because that is where the proxy and the VPN host live (pass 4). The isolated tier is
# never a destination: that is what makes it isolated.
data "aws_subnets" "peer_reachable" {
  for_each = { for pr in local.hub_peering : pr.key => pr }

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.peer[each.key].id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private", "public"]
  }
}

data "aws_subnet" "peer_reachable" {
  for_each = toset(flatten([for k, v in data.aws_subnets.peer_reachable : v.ids]))

  id = each.key
}

locals {
  # route table x peer subnet - one route each, subnet-scoped.
  forward_routes = {
    for pair in setproduct(
      keys(module.vpc.private_route_table_ids),
      keys(data.aws_subnet.peer_reachable)
    ) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = module.vpc.private_route_table_ids[pair[0]]
      cidr           = data.aws_subnet.peer_reachable[pair[1]].cidr_block
      peering_key    = one(keys(aws_vpc_peering_connection.to_peer))
    }
  }
}

resource "aws_route" "to_peer" {
  for_each = local.forward_routes

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = aws_vpc_peering_connection.to_peer[each.value.peering_key].id
}
