# The NAT gateway - design A only (step 7), and the largest single hourly item after the
# endpoint set: USD 0.045/h + 0.045/GB processed, plus 0.005/h for its public IPv4
# (docs/PRICING.md 3, measured). Everything in this file is conditional on egress_mode
# (step 7.2): under design B none of it exists and the private tier has NO default route.
#
# THE ROUTES LIVE HERE, NOT IN foundation/ - they name the NAT's [E] id, so a route left in
# a [P] slice would blackhole the private tier the moment make down removes the NAT it
# points at (Lesson 4's shape: [P] state referencing an [E] resource). Destroyed with the
# NAT, rebuilt with it, and foundation/ never changes across the cycle - the Validation's
# byte-identical reading depends on exactly this split.

resource "aws_eip" "nat" {
  # checkov:skip=CKV2_AWS_19:the address is attached to the NAT GATEWAY below, not to an EC2 instance - the association the check looks for does not exist for this resource pairing
  count = var.egress_mode == "A" ? 1 : 0

  domain = "vpc"

  tags = {
    Name = "awsds-${var.env}-nat"
  }
}

resource "aws_nat_gateway" "this" {
  count = var.egress_mode == "A" ? 1 : 0

  subnet_id     = var.nat_public_subnet_id
  allocation_id = aws_eip.nat[0].id

  tags = {
    Name = "awsds-${var.env}-nat"
  }
}

# One NAT, every private route table (step 7.1): both zones' tables point at the single
# gateway, so one AZ's private tier reaches the internet cross-AZ - accepted at lab scale,
# and the one-per-AZ switch is documented on nat_public_subnet_id.
#
# A NAT DOES NOT BYPASS THE S3 GATEWAY ENDPOINT'S POLICY (9.3's correction): the endpoint
# puts the S3 prefix list in these same tables and the more specific route wins, so
# in-region S3 traffic is judged by foundation/'s allow-list, this 0.0.0.0/0 notwithstanding.
resource "aws_route" "private_default" {
  for_each = var.egress_mode == "A" ? var.private_route_table_ids : {}

  route_table_id         = each.value
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this[0].id
}
