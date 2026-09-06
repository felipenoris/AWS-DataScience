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

# ---------------------------------------------------------------- Stage 6c pass 2: the apex
#
# WHY AN APEX AT ALL, WHEN prod.internal AND sandbox.internal ALREADY WORK. A private hosted zone
# answers for its WHOLE SUBTREE, and the estate now has five VPCs and one client plane that must
# resolve across all of them. Three sibling apexes (`prod.internal`, `sandbox.internal`,
# `pages.internal`) means three association matrices to keep in step, and a VPC associated with a
# zone that holds no matching record gets **NXDOMAIN** rather than a public answer - so a missing
# association and a missing name are indistinguishable to whoever is debugging. One apex with
# child zones makes the shared names (`gitlab`, `proxy`, `vpn`) live in exactly one place, and
# leaves per-environment names in a zone their own account owns.
#
# PRIVATE ZONES DO NOT DELEGATE, so `sandbox.awsds.internal` is not reached THROUGH this zone: a
# VPC resolves it because it is associated with THAT zone too, and overlapping zones resolve by
# most-specific match. The apex holding the shared names and the children holding the per-account
# ones is therefore a naming convention, not a delegation hierarchy - and INT-22's matrix is what
# makes it work, which is why 2.4 writes the matrix down and a check reads it.
#
# THE OLD FAMILY IS STILL HERE, AND FOR SEVERAL PASSES. `prod.internal` and `pages.internal` above
# are retired at step 2.6, AFTER pass 6 measures the new ones - zones cannot be renamed, so the
# two families coexist by construction. Anything comparing "the matrix as documented" against "the
# matrix as deployed" has to tolerate that window (2.4's NT-12, corrected before it was written).

resource "aws_route53_zone" "awsds_internal" {
  name    = "awsds.internal"
  comment = "The estate apex - shared names only: gitlab, proxy, vpn (Stage 6c step 2.1, D38)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}

# PAGES KEEPS ITS OWN APEX, and it is the one place this design does NOT consolidate (D36,
# unchanged in intent). A `pages.awsds.internal` child would put user-published content under the
# same registrable parent as the platform's own names, and a cookie scoped to the parent would be
# readable by it. The separation is the whole reason Pages was given an apex in the first place;
# renaming it to `awsds-pages.internal` keeps the project prefix without weakening that.
resource "aws_route53_zone" "awsds_pages_internal" {
  name    = "awsds-pages.internal"
  comment = "GitLab Pages private names - a SEPARATE registrable parent, by decision (D36, 6c 2.3)"

  vpc {
    vpc_id = module.vpc.vpc_id
  }

  lifecycle {
    ignore_changes = [vpc]
  }
}
