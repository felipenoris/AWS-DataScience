# ------------------------------------------------------------------ the child private zone
#
# `staging.awsds.internal` - this account's half of the `awsds.internal` family (step 2.2).
# Private zones do not delegate: a VPC reaches this zone by being associated with it, and
# overlapping zones resolve by most-specific match. The apex/child split is a naming convention
# that keeps each account's names in a zone that account owns.
#
# ignore_changes on vpc is load-bearing from the first apply: `VPC-Networking` is associated
# into this zone by Production (step 2.5 - the zone owner authorizes, the VPC owner associates).
# Without it, every later plan here would try to remove an association another account made.
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
