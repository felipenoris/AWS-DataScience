# sandbox.internal - one per business unit (Stage 3 step 4.2), associated with its own VPC
# at creation: no cross-account handshake for this zone (4.4's table touches the two
# Production zones, not this one). ~USD 0.50/month, already in the cost-model floor.

resource "aws_route53_zone" "sandbox_internal" {
  name    = "sandbox.internal"
  comment = "Private names of this sandbox unit (Stage 3 step 4.2; .internal per D36/ICANN)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }
}
