# The private DNS this account owns: the `awsds.internal` APEX and the `awsds-pages.internal`
# sibling (Pages keeps its own apex for the cookie-scope reason D36 gives; conventions §6 places
# it here rather than in Stage 7). ~USD 0.50/zone-month each, both in the cost-model floor.
#
# The inline `vpc` block is the initial association only. The cross-account associations of 4.4
# (Sandbox and Staging, pass 2 - Staging kept its apex association when 6c step 3.1 retired its
# peering) are made by aws_route53_zone_association resources in the consuming accounts' slices,
# after an authorization written here, and the provider requires
# ignore_changes on vpc for exactly that mix or every later plan tries to remove what the other
# account associated.

# `prod.internal` and `pages.internal` were created at Stage 3 step 4.2 and retired at 6c step 2.6
# (2026-09-07). Where their names went: the shared ones (`gitlab`, `proxy`, `vpn`) are in the apex
# below; the per-environment ones are in the child zones each account owns; and the two `[E]` probe
# records went to the apex rather than to `prod.awsds.internal`, because they are resolved from
# Sandbox and the child zone is deliberately not associated there. `NT-12` is written against the
# final matrix rather than against a dated exception.

# ---------------------------------------------------------------- Stage 6c pass 2: the apex
#
# A private hosted zone answers for its whole subtree, and the estate has five VPCs and one client
# plane that must resolve across all of them. Three sibling apexes (`prod.internal`,
# `sandbox.internal`, `pages.internal`) means three association matrices to keep in step, and a VPC
# associated with a zone that holds no matching record gets NXDOMAIN rather than a public answer,
# so a missing association and a missing name are indistinguishable to whoever is debugging. One
# apex with child zones makes the shared names (`gitlab`, `proxy`, `vpn`) live in exactly one
# place, and leaves per-environment names in a zone their own account owns.
#
# Private zones do not delegate, so `sandbox.awsds.internal` is not reached through this zone: a
# VPC resolves it because it is associated with that zone too, and overlapping zones resolve by
# most-specific match. The apex holding the shared names and the children holding the per-account
# ones is a naming convention, not a delegation hierarchy. INT-22's matrix is what makes it work,
# which is why 2.4 writes the matrix down and a check reads it.
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

# Pages keeps its own apex - the one place this design does not consolidate (D36). A
# `pages.awsds.internal` child would put user-published content under the same registrable parent
# as the platform's own names, and a cookie scoped to the parent would be readable by it.
# `awsds-pages.internal` keeps the project prefix without weakening that separation.
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
