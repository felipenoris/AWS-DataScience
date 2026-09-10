# production/foundation/peers.tf - pass 2 of Stage 3, the whole cross-account handshake in one
# ordered apply (steps 4.4-4.5 and 6). Production is where it can be one apply: the authorization
# must precede the association, and a route to a peering needs the peering active, so the accepting
# side, applied after both requesters exist, is the one place every arrow points forward.
# "Production accepts two peerings and nothing else" (6.2) is enforced by this file being the only
# accepter and its map having two rows.
#
# The two aliased providers act as the peer account: the association and the forward routes are the
# VPC owner's own API calls (4.4 says "in the VPC owner, behind a provider alias"), executed from
# this slice so the ordering above holds in one apply. They create only untaggable resources
# (routes, zone associations), so the aliases carry no default_tags. Profiles arrive from the
# generated tfvars - the same PROFILES table every command line uses - never a literal here.
#
# The peer's facts are read, never pasted (Lesson 3): VPCs by Name tag, subnets by Tier tag, route
# tables by Name tag. An id copied into a tfvars would be a stale copy of another slice's state; a
# data source cannot go stale. Everything referenced is [P] on both sides, so a make down never
# breaks this file (D11).
#
# A provider cannot vary per for_each instance, so the per-peer data and the association and
# forward-route resources are written once per peer; the single-provider resources (authorizations,
# accepters, return routes) are for_each over the peers map.

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

# ------------------------------------------------------------------ the peers' [P] facts

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

# Sandbox sources, per 6.3's table: the public tier (the WireGuard instance SNATs the laptop there
# - omit it and the tunnel comes up while GitLab stays unreachable) and the private tier (Studio
# apps). Staging contributes only its private tier (INT-09).
data "aws_subnets" "sandbox_public" {
  provider = aws.sandbox

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.sandbox.id]
  }
  filter {
    name   = "tag:Tier"
    values = ["public"]
  }
}

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


data "aws_subnet" "sandbox_public" {
  provider = aws.sandbox
  for_each = toset(data.aws_subnets.sandbox_public.ids)
  id       = each.value
}

data "aws_subnet" "sandbox_private" {
  provider = aws.sandbox
  for_each = toset(data.aws_subnets.sandbox_private.ids)
  id       = each.value
}


# The route tables the forward routes land on - by Name tag, the names the vpc module
# authors. The isolated tier is deliberately absent: it never routes anywhere (2.2).
data "aws_route_table" "sandbox_public" {
  provider = aws.sandbox

  filter {
    name   = "tag:Name"
    values = ["awsds-${var.peers["sandbox"].env}-public"]
  }
}

data "aws_route_tables" "sandbox_private" {
  provider = aws.sandbox

  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.sandbox.id]
  }
  filter {
    name   = "tag:Name"
    values = ["awsds-${var.peers["sandbox"].env}-private-*"]
  }
}


# The pending requests, found by their two VPC ends rather than by pasted ids. The
# status-code values are OR'd: pending-acceptance on the first apply, active on every
# later plan - one filter, idempotent (Lesson 13: the two outcomes stay distinguishable
# because a missing request fails the plan loudly).
data "aws_vpc_peering_connection" "from" {
  for_each = local.peer_vpc_ids

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

# Own private subnets - the forward routes' destinations. Subnet-level on purpose
# (6.3: never the whole peer VPC); GitLab's single subnet is a Stage 7 fact, so both
# private /18s for now, narrowed there if it matters.
data "aws_subnet" "own_private" {
  for_each = module.vpc.private_subnet_ids
  id       = each.value
}

locals {
  # Staging is not in this map, and the absence is the control (6c step 3.1). The matrix in
  # scripts/tfhygiene/backend.py has no `VPC-SharedServices <-> Staging` row: deployment is an API
  # act, and a peering would grant standing L3 reach from the host that executes
  # repository-supplied build code into a deployment target (Lesson 2). Staging reaches the hub for
  # the proxy and nothing else; its apex association survives, in local.zone_vpcs below.
  peer_vpc_ids = {
    sandbox = data.aws_vpc.sandbox.id
  }

  # The zones a peer account associates its VPC with. The setproduct below turns this into one
  # authorization per (zone, peer) and the two association resources for_each the same map.
  # INT-22's matrix asks for the apex in all five VPCs; three are same-account and land in
  # zone-associations.tf, and these are the two that cross an account boundary.
  #
  # `awsds-pages.internal` is not here. Its matrix row is VPC-SharedServices and VPC-Networking
  # only - both in this account - because Pages is reached from the tunnel and from the runners,
  # never from a spoke's compute.
  #
  # What a spoke needs from this account is the apex, where the shared names live (`gitlab`,
  # `proxy`, `vpn`) and where the `[E]` probe records go. The per-environment child zones are
  # associated by their own owners, not from here.
  zones = {
    apex = aws_route53_zone.awsds_internal.zone_id
  }

  # The zone matrix and the peering matrix are two lists, and 6c step 3.1 is where they part:
  # Staging keeps the apex association and loses the peering. It reaches the hub for the proxy and
  # has no business in VPC-SharedServices, but it still has to resolve `gitlab.awsds.internal`
  # (INT-22).
  #
  # A DNS association is not a path. Nothing about a zone association implies reachability: a VPC
  # that resolves a name it cannot reach gets an answer and then a timeout, which is a better
  # failure than NXDOMAIN and a worse one than a refusal.
  zone_vpcs = {
    sandbox = data.aws_vpc.sandbox.id
    staging = data.aws_vpc.staging.id
  }

  # zone x peer - one authorization per pair.
  zone_peer = {
    for pair in setproduct(keys(local.zones), keys(local.zone_vpcs)) :
    "${pair[0]}.${pair[1]}" => {
      zone_id = local.zones[pair[0]]
      vpc_id  = local.zone_vpcs[pair[1]]
    }
  }

  own_private_cidrs = { for k, s in data.aws_subnet.own_private : k => s.cidr_block }

  # The return path (6.3 row 4): every source subnet a peer originates traffic from,
  # keyed peer-tier-subnet so a plan reads as the table does.
  return_sources = merge(
    { for id, s in data.aws_subnet.sandbox_public :
    "sandbox-public-${id}" => { cidr = s.cidr_block, peer = "sandbox" } },
    { for id, s in data.aws_subnet.sandbox_private :
    "sandbox-private-${id}" => { cidr = s.cidr_block, peer = "sandbox" } },
  )

  return_routes = {
    for pair in setproduct(keys(module.vpc.private_route_table_ids), keys(local.return_sources)) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = module.vpc.private_route_table_ids[pair[0]]
      cidr           = local.return_sources[pair[1]].cidr
      peer           = local.return_sources[pair[1]].peer
    }
  }

  sandbox_forward_rts = concat(
    [data.aws_route_table.sandbox_public.id],
    data.aws_route_tables.sandbox_private.ids,
  )

  sandbox_forward = {
    for pair in setproduct(local.sandbox_forward_rts, keys(local.own_private_cidrs)) :
    "${pair[0]}|${pair[1]}" => {
      route_table_id = pair[0]
      cidr           = local.own_private_cidrs[pair[1]]
    }
  }


}

# ------------------------------------------------- 4.4-4.5: the two-sided DNS handshake
#
# The authorization stays in state on purpose (4.5): it persists until deleted, deleting
# it would not affect the association, and a VPC rebuild needs a FRESH one - keeping the
# resource means a rebuild re-runs the handshake by itself.

resource "aws_route53_vpc_association_authorization" "peer" {
  for_each = local.zone_peer

  zone_id = each.value.zone_id
  vpc_id  = each.value.vpc_id
}

# The association is the VPC owner's call, made through its alias. depends_on carries the
# half of the ordering the ids do not: the authorization has no attribute the association
# consumes.
resource "aws_route53_zone_association" "sandbox" {
  provider = aws.sandbox
  for_each = local.zones

  zone_id = each.value
  vpc_id  = data.aws_vpc.sandbox.id

  depends_on = [aws_route53_vpc_association_authorization.peer]
}

resource "aws_route53_zone_association" "staging" {
  provider = aws.staging
  for_each = local.zones

  zone_id = each.value
  vpc_id  = data.aws_vpc.staging.id

  depends_on = [aws_route53_vpc_association_authorization.peer]
}

# --------------------------------------------------------- 6: acceptance, then the routes

resource "aws_vpc_peering_connection_accepter" "peer" {
  for_each = data.aws_vpc_peering_connection.from

  vpc_peering_connection_id = each.value.id
  auto_accept               = true

  tags = {
    Name = "awsds-${var.env}-from-${each.key}"
    Side = "accepter"
  }
}

# Routes reference the accepter's id, not the data source's: that is what orders every route after
# acceptance, which AWS requires for a route to a peering.

resource "aws_route" "return" {
  for_each = local.return_routes

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = aws_vpc_peering_connection_accepter.peer[each.value.peer].id
}

resource "aws_route" "sandbox_forward" {
  provider = aws.sandbox
  for_each = local.sandbox_forward

  route_table_id            = each.value.route_table_id
  destination_cidr_block    = each.value.cidr
  vpc_peering_connection_id = aws_vpc_peering_connection_accepter.peer["sandbox"].id
}


# What is deliberately not here. No route anywhere touching 10.90.0.0/24 (6.5 - peering does no
# edge-to-edge routing; NT-4 fails on any). No security-group rule yet: ingress arrives with the
# workloads (6.4, Stage 7's GitLab SG references the peer SGs or these subnet CIDRs - never
# 0.0.0.0/0, never a whole VPC).
