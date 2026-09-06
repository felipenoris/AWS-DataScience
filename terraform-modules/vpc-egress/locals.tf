# THE ONE PLACE THIS MODULE BUILDS A NAME (6c step 5.1, v0.6.0). Every `Name` tag and every
# resource name below reads this rather than re-deriving `awsds-<env>`, so a second egress set in
# one account is one input away and there is no site left that could be missed (Lesson 14).
#
# IT IS THE `vpc` MODULE'S LOCAL, WORD FOR WORD, and that is deliberate rather than lazy: the two
# modules name objects in the same account and a reader comparing `awsds-prod-networking-vpc` with
# `awsds-prod-egress` should not have to work out whether the two prefixes are built the same way.
# 0.4a deferred this input to here so one version could carry it beside the NAT removal.
locals {
  name_prefix = var.name_suffix == "" ? "awsds-${var.env}" : "awsds-${var.env}-${var.name_suffix}"
}
