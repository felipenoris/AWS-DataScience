# production/networking/peerings.tf - Stage 6c step 3.4, the hub's side of the matrix.
#
# The hub accepts every peering in the estate but one: four rows of the matrix end here, and the
# fifth (Sandbox to VPC-SharedServices) is the one INT-09 rides. The peerings themselves are
# created by their requesters - within this account by a single resource with auto_accept, across
# an account by the requester/accepter pair. What this file adds is the return routes.
#
# An attachment with no route is the defect it exists against, and the reference implementation
# kept for comparison has exactly it: a peering in `active` state carrying no traffic, because one
# side's route table was never told. It looks correct in every console view that shows peerings and
# in none that shows routes, so 3.7's NT-11 checks both sides rather than the connection.
#
# The routes are subnet-scoped and written into every tier that originates traffic. The private
# tables are where a workload answers from; the public table is here because the proxy and the VPN
# host live in that tier (pass 4) and their replies have to find the way back. The isolated table
# gets nothing.

locals {
  # The rows this slice accepts and that live in the same account. The cross-account rows need a
  # requester to exist first and land in their own commit.
  local_accepted = [for pr in var.peerings : pr if pr.role == "accepter" && pr.same_account]
}

data "aws_vpc" "requester" {
  for_each = { for pr in local.local_accepted : pr.key => pr }

  filter {
    name   = "tag:Name"
    values = ["awsds-${each.value.peer_env}-${each.value.peer_name_suffix}-vpc"]
  }
}

# The peering is read, never re-declared: its requester owns it, and a second resource for the same
# connection is two Terraform states claiming one object. status-code admits `pending-acceptance`
# and `provisioning` beside `active`, so the lookup is idempotent across a first apply, and a
# missing peering fails the plan loudly instead of resolving to nothing (Lesson 13).
data "aws_vpc_peering_connection" "accepted" {
  for_each = { for pr in local.local_accepted : pr.key => pr }

  filter {
    name   = "requester-vpc-info.vpc-id"
    values = [data.aws_vpc.requester[each.key].id]
  }
  filter {
    name   = "accepter-vpc-info.vpc-id"
    values = [module.vpc.vpc_id]
  }
  filter {
    name   = "status-code"
    values = ["pending-acceptance", "provisioning", "active"]
  }
}

data "aws_subnets" "requester_private" {
  for_each = { for pr in local.local_accepted : pr.key => pr }

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.requester[each.key].id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

data "aws_subnet" "requester_private" {
  for_each = toset(flatten([for k, v in data.aws_subnets.requester_private : v.ids]))

  id = each.key
}

locals {
  # Every table that originates traffic toward a peer: both private tables and the public one.
  return_tables = merge(
    module.vpc.private_route_table_ids,
    { public = module.vpc.public_route_table_id },
  )

  # Which peering each requester subnet belongs to - the join the route needs and the subnet
  # itself cannot carry.
  subnet_peering = merge([
    for k, v in data.aws_subnets.requester_private : { for id in v.ids : id => k }
  ]...)

  return_routes = {
    for pair in setproduct(keys(local.return_tables), keys(data.aws_subnet.requester_private)) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = local.return_tables[pair[0]]
      cidr           = data.aws_subnet.requester_private[pair[1]].cidr_block
      peering_key    = local.subnet_peering[pair[1]]
    }
  }
}

resource "aws_route" "return" {
  for_each = local.return_routes

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = data.aws_vpc_peering_connection.accepted[each.value.peering_key].id
}

# ------------------------------------------------- the cross-account accepters (step 3.4)
#
# A provider cannot be iterated, so these are written once per peer instead of for_each'd over the
# matrix like everything above. `peers.tf` carries the same constraint and the same shape, and this
# file joins Stage 14's edit list by construction.
#
# Acceptance is Production's own act: a spoke can request reach into the hub and cannot grant
# itself any. The requester half sits in the spoke's own slice and leaves the connection
# `pending-acceptance` until this applies.
#
# The return routes reference the accepter's id rather than the data source's, which orders every
# route after acceptance, as AWS requires for a route to a peering.

data "aws_vpc" "sandbox" {
  provider = aws.sandbox

  filter {
    name   = "tag:Name"
    values = ["awsds-${var.peers["sandbox"].env}-vpc"]
  }
}

data "aws_vpc" "staging" {
  provider = aws.staging

  filter {
    name   = "tag:Name"
    values = ["awsds-${var.peers["staging"].env}-vpc"]
  }
}

locals {
  cross_requester_vpcs = {
    sandbox = data.aws_vpc.sandbox.id
    staging = data.aws_vpc.staging.id
  }
}

data "aws_vpc_peering_connection" "from_spoke" {
  for_each = local.cross_requester_vpcs

  filter {
    name   = "requester-vpc-info.vpc-id"
    values = [each.value]
  }
  filter {
    name   = "accepter-vpc-info.vpc-id"
    values = [module.vpc.vpc_id]
  }
  filter {
    name   = "status-code"
    values = ["pending-acceptance", "provisioning", "active"]
  }
}

resource "aws_vpc_peering_connection_accepter" "from_spoke" {
  for_each = data.aws_vpc_peering_connection.from_spoke

  vpc_peering_connection_id = each.value.id
  auto_accept               = true

  tags = {
    Name = "${local.name_prefix}-from-${each.key}"
    Side = "accepter"
  }
}

# The spokes' private subnets are the only destinations: a spoke originates from its private tier,
# and nothing in the hub ever initiates toward a spoke's public or isolated one.
data "aws_subnets" "sandbox_private" {
  provider = aws.sandbox

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.sandbox.id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

data "aws_subnets" "staging_private" {
  provider = aws.staging

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.staging.id]
  }
  filter {
    name   = "tag:Tier"
    values = ["private"]
  }
}

# One block per peer, because a subnet in another account cannot be read with this account's
# credentials: a single for_each over both id sets with the default provider plans as `no matching
# EC2 Subnet found`. Providers cannot be iterated, so this is the split `peers.tf` documents,
# arriving one layer down.
data "aws_subnet" "sandbox_private" {
  provider = aws.sandbox
  for_each = toset(data.aws_subnets.sandbox_private.ids)

  id = each.key
}

data "aws_subnet" "staging_private" {
  provider = aws.staging
  for_each = toset(data.aws_subnets.staging_private.ids)

  id = each.key
}

locals {
  spoke_private_cidrs = merge(
    { for id, sn in data.aws_subnet.sandbox_private : id => sn.cidr_block },
    { for id, sn in data.aws_subnet.staging_private : id => sn.cidr_block },
  )
}

locals {
  spoke_subnet_owner = merge(
    { for id in data.aws_subnets.sandbox_private.ids : id => "sandbox" },
    { for id in data.aws_subnets.staging_private.ids : id => "staging" },
  )

  spoke_return_routes = {
    for pair in setproduct(keys(local.return_tables), keys(local.spoke_subnet_owner)) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = local.return_tables[pair[0]]
      cidr           = local.spoke_private_cidrs[pair[1]]
      peer           = local.spoke_subnet_owner[pair[1]]
    }
  }
}

resource "aws_route" "spoke_return" {
  for_each = local.spoke_return_routes

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = aws_vpc_peering_connection_accepter.from_spoke[each.value.peer].id
}
