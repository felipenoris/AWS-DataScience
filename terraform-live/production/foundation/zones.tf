# prod.internal and pages.internal - Production owns both (Stage 3 step 4.2; pages here
# rather than in Stage 7 because conventions §6 places it in production/foundation/).
# ~USD 0.50/zone-month, both already in the cost-model floor.
#
# THE INLINE vpc BLOCK IS THE INITIAL ASSOCIATION ONLY. The four cross-account associations
# of 4.4 (Sandbox and Development, pass 2) are made by aws_route53_zone_association
# resources in the CONSUMING accounts' slices, after an authorization written here - and the
# provider requires ignore_changes on vpc for exactly that mix, or every later plan tries to
# remove what the other account associated.

resource "aws_route53_zone" "prod_internal" {
  name    = "prod.internal"
  comment = "Production private names - gitlab and friends (Stage 3 step 4.2, Stage 7)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}

resource "aws_route53_zone" "pages_internal" {
  name    = "pages.internal"
  comment = "GitLab Pages private names (Stage 3 step 4.2, Stage 7 step 4)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}
