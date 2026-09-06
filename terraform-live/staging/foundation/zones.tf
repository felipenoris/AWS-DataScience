# ---------------------------------------------------------- Stage 6c pass 2: the child zone
#
# `staging.awsds.internal` - this account's half of the `awsds.internal` family (step 2.2). PRIVATE ZONES DO
# NOT DELEGATE: a VPC does not reach this zone through the apex, it reaches it by being
# ASSOCIATED with this zone as well, and overlapping zones resolve by most-specific match. So
# the apex/child split here is a naming convention that keeps each account's names in a zone that
# account OWNS - not a delegation hierarchy.
#
# ignore_changes ON vpc, AND IT IS LOAD-BEARING FROM THE FIRST APPLY. `VPC-Networking` is
# associated into this zone by PRODUCTION (step 2.5 reverses the old direction: the zone owner
# authorizes, the VPC owner associates). Without this, every later plan here would try to remove
# an association another account made.
resource "aws_route53_zone" "staging_awsds_internal" {
  name    = "staging.awsds.internal"
  comment = "Staging's private names, under the estate apex (Stage 6c step 2.2)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}
