# The one place this module builds a name (6c step 5.1). Every `Name` tag and every resource name
# below reads this rather than re-deriving `awsds-<env>`, so a second egress set in one account is
# one input away and no site is left that could be missed (Lesson 14).
#
# It is the `vpc` module's local, word for word: the two modules name objects in the same account,
# and a reader comparing `awsds-prod-networking-vpc` with `awsds-prod-egress` should not have to
# work out whether the two prefixes are built the same way.
locals {
  name_prefix = var.name_suffix == "" ? "awsds-${var.env}" : "awsds-${var.env}-${var.name_suffix}"
}
