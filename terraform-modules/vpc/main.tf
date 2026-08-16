# vpc - one VPC, three tiers x two AZs (Stage 3 steps 1-2, 4.1, 5), the same in every
# VPC-bearing account; only the CIDR and the endpoint lists differ (view 2). Free at rest,
# layer [P]: everything in this module survives every make down.
#
# THE ADDRESS CUT IS AUTHORED HERE AND IS [P] - changing it later is a VPC rebuild (risks):
#   private  a /18 per AZ  = cidrsubnet(cidr, 2, 0..1)   .0.0/18, .64.0/18
#   isolated a /20 per AZ  = cidrsubnet(cidr, 4, 8..9)   .128.0/20, .144.0/20
#   public   a /24 per AZ  = cidrsubnet(cidr, 8, 160..161) .160.0/24, .161.0/24
# The rest of the /16 stays free. Private is the big tier (Studio apps, runners, GitLab);
# isolated is created empty on purpose (step 1.4) - subnets are free, re-cutting is not.

locals {
  private_cidrs  = [for i in range(2) : cidrsubnet(var.vpc_cidr, 2, i)]
  isolated_cidrs = [for i in range(2) : cidrsubnet(var.vpc_cidr, 4, 8 + i)]
  public_cidrs   = [for i in range(2) : cidrsubnet(var.vpc_cidr, 8, 160 + i)]
}

# Both DNS attributes ON (step 4.1): aws_vpc defaults hostnames to false, and endpoint
# private DNS plus everything in step 4 silently resolves nothing without both.
resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "awsds-${var.env}-vpc"
  }
}

# The DEFAULT security group, emptied: nothing may use it, so it holds no rules - anything
# that appears in it later was placed by hand and is a finding.
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "awsds-${var.env}-default-do-not-use"
  }
}

# ------------------------------------------------------------------------------ subnets
# Anchored on availability_zone_id - the ZONE id names the datacenter; the AZ NAME is a
# per-account label (step 1.5, ./aws/AZs.py).

resource "aws_subnet" "public" {
  for_each = { for i, z in var.zone_ids : z => i }

  vpc_id                  = aws_vpc.this.id
  cidr_block              = local.public_cidrs[each.value]
  availability_zone_id    = each.key
  map_public_ip_on_launch = false # a public IP is a per-resource decision (the WireGuard EIP is [P] and explicit)

  tags = {
    Name = "awsds-${var.env}-public-${each.key}"
    Tier = "public"
  }
}

resource "aws_subnet" "private" {
  for_each = { for i, z in var.zone_ids : z => i }

  vpc_id               = aws_vpc.this.id
  cidr_block           = local.private_cidrs[each.value]
  availability_zone_id = each.key

  tags = {
    Name = "awsds-${var.env}-private-${each.key}"
    Tier = "private"
  }
}

resource "aws_subnet" "isolated" {
  for_each = { for i, z in var.zone_ids : z => i }

  vpc_id               = aws_vpc.this.id
  cidr_block           = local.isolated_cidrs[each.value]
  availability_zone_id = each.key

  tags = {
    Name = "awsds-${var.env}-isolated-${each.key}"
    Tier = "isolated"
  }
}

# --------------------------------------------------------------- IGW and route tables
# One IGW (step 2.1); the public tier routes to it. The private tier's default route exists
# ONLY under design A and is inserted by egress/ (steps 2.2, 7, 10) - never here. The
# isolated tier never gets one: that is what makes it isolated (step 2.2).

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "awsds-${var.env}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "awsds-${var.env}-public"
  }
}

resource "aws_route" "public_internet" {
  route_table_id         = aws_route_table.public.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this.id
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

# Private route tables are PER AZ, so the documented one-NAT-per-AZ switch (step 7.1) is a
# route change, not a re-plumbing.
resource "aws_route_table" "private" {
  for_each = aws_subnet.private

  vpc_id = aws_vpc.this.id

  tags = {
    Name = "awsds-${var.env}-private-${each.key}"
  }
}

resource "aws_route_table_association" "private" {
  for_each = aws_subnet.private

  subnet_id      = each.value.id
  route_table_id = aws_route_table.private[each.key].id
}

resource "aws_route_table" "isolated" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "awsds-${var.env}-isolated"
  }
}

resource "aws_route_table_association" "isolated" {
  for_each = aws_subnet.isolated

  subnet_id      = each.value.id
  route_table_id = aws_route_table.isolated.id
}

# NACLs stay at the default allow, by decision (step 2.3): the control lives in security
# groups, and a stateless deny is the fastest way to break a path nobody can then debug.
# No aws_network_acl resource here, deliberately.

# ------------------------------------------------------------- baseline security groups
# Referencing each other by ID rather than by CIDR where possible (step 2.4). The tier
# groups ship with egress only; ingress arrives with the workloads later stages put there.

resource "aws_security_group" "endpoints" {
  # checkov:skip=CKV2_AWS_5:consumed by egress/'s interface endpoints - a different slice by design (steps 2.4, 8.5)
  name        = "awsds-${var.env}-endpoints"
  description = "Interface VPC endpoints - TCP/443 from this VPC (step 2.4). Under design B an endpoint whose SG does not admit 443 is not a slow path, it is no path."
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from this VPC"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "awsds-${var.env}-endpoints"
  }
}

resource "aws_security_group" "tier" {
  # checkov:skip=CKV_AWS_382:baseline egress-all is the tier default; the perimeter is the endpoint policies and SCP/RCP axes, not per-SG egress (step 2.4)
  # checkov:skip=CKV2_AWS_5:baseline groups exist for the workloads LATER stages attach (step 2.4) - unattached today by construction
  for_each = toset(["public", "private", "isolated"])

  name        = "awsds-${var.env}-${each.key}-tier"
  description = "Baseline for the ${each.key} tier - no ingress; workloads add their own rules (step 2.4)"
  vpc_id      = aws_vpc.this.id

  egress {
    description = "All egress - constrained by routes and endpoint policies, not here"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "awsds-${var.env}-${each.key}-tier"
  }
}

# ------------------------------------------------------------------------- flow logs
# One per VPC, CloudWatch Logs, 30 days (step 5, decision 3) - for debugging, not detection
# (GuardDuty reads flow logs on its own). No CMK on the log group: a key is ~USD 1/key-month
# per account (docs/PRICING.md) for a debugging log, and the stage's cost table carries no
# such line - default encryption, deliberately.

resource "aws_cloudwatch_log_group" "flow_logs" {
  # checkov:skip=CKV_AWS_158:a CMK here is USD 1/key-month per account for a debugging log - unbudgeted, declined (step 5.1)
  # checkov:skip=CKV_AWS_338:retention is 30 days by decision 3 - a debugging log, not an audit trail
  name              = "awsds-${var.env}-vpc-flow-logs"
  retention_in_days = var.flow_log_retention_days
}

resource "aws_flow_log" "this" {
  vpc_id                   = aws_vpc.this.id
  traffic_type             = "ALL"
  log_destination_type     = "cloud-watch-logs"
  log_destination          = aws_cloudwatch_log_group.flow_logs.arn
  iam_role_arn             = var.flow_log_role_arn
  max_aggregation_interval = 600

  tags = {
    Name = "awsds-${var.env}-vpc"
  }
}
