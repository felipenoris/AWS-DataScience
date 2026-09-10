# ---------------------------------------------------------- Stage 6c pass 2: the child zone
#
# `prod.awsds.internal` - this account's half of the `awsds.internal` family (step 2.2). Private
# zones do not delegate: a VPC does not reach this zone through the apex, it reaches it by being
# associated with this zone as well, and overlapping zones resolve by most-specific match. The
# apex/child split is a naming convention that keeps each account's names in a zone that account
# owns, not a delegation hierarchy.
#
# `ignore_changes` on vpc is load-bearing from the first apply. `VPC-Networking` is associated into
# this zone by Production (step 2.5: the zone owner authorizes, the VPC owner associates). Without
# it, every later plan here would try to remove an association another account made.
resource "aws_route53_zone" "prod_awsds_internal" {
  name    = "prod.awsds.internal"
  comment = "The production runtime's private names, under the estate apex (Stage 6c step 2.2)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}
