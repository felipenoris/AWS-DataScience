# The private DNS this account owns: the `awsds.internal` APEX and the `awsds-pages.internal`
# sibling (Pages keeps its own apex for the cookie-scope reason D36 gives; conventions §6 places
# it here rather than in Stage 7). ~USD 0.50/zone-month each, both in the cost-model floor.
#
# THE FAMILY THIS REPLACED - `prod.internal` and `pages.internal`, Stage 3 step 4.2 - was retired
# at 6c step 2.6 on 2026-09-07; the block below says what moved where.
#
# THE INLINE vpc BLOCK IS THE INITIAL ASSOCIATION ONLY. The four cross-account associations
# of 4.4 (Sandbox and Development, pass 2) are made by aws_route53_zone_association
# resources in the CONSUMING accounts' slices, after an authorization written here - and the
# provider requires ignore_changes on vpc for exactly that mix, or every later plan tries to
# remove what the other account associated.

# THE TWO ZONES THAT STOOD HERE ARE GONE (step 2.6, 2026-09-07). `prod.internal` and
# `pages.internal` were created at Stage 3 step 4.2 and retired once pass 6 had measured their
# successors - step 6.1's DNS pair is that measurement, and it was built to discriminate: it asks
# that `prod.awsds.internal` ANSWER and `sandbox.internal` NOT, from the hub's resolver.
#
# ZONES CANNOT BE RENAMED, so the two families coexisted from pass 2 to pass 6 by construction, and
# every check that compared "the matrix as documented" with "the matrix as deployed" had to tolerate
# that window. It is closed, and `NT-12` is written against the final matrix rather than against a
# dated exception.
#
# WHAT MOVED, so a reader looking for a name knows where it went: the shared names (`gitlab`,
# `proxy`, `vpn`) are in the apex below; the per-environment ones are in the child zones each
# account owns; and the two `[E]` probe records went to the APEX rather than to
# `prod.awsds.internal`, because they are resolved FROM Sandbox and the child zone is deliberately
# not associated there.

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
