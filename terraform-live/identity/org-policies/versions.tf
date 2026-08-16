# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: it belongs to each root module, so the four lines are
# repeated per slice deliberately (Lesson 14 - and scripts/check-bootstrap-parity.py is what
# keeps the FIVE bootstrap copies from drifting; this slice is outside that check because it
# is not one of them).
#
# THE PIN IS LOAD-BEARING HERE IN A WAY IT IS NOT ELSEWHERE, and two of this stage's
# verifications say so:
#
#   (ii)  `DECLARATIVE_POLICY_EC2` must be a value this provider's `type` validator accepts.
#         It is - measured in the 6.60.0 binary, in the same enum as the two known-good types.
#         `type` is also ForceNew, so a provider that did NOT know the value would not fail
#         politely: it would plan a destroy and a create on a document attached to the root.
#   (iv)  `aws_organizations_organizational_unit_descendant_organizational_units` must exist.
#         It does, and data.tf consumes it to turn an authored OU NAME into an id at any depth.
#
# The constraint admits a range; the exact build is pinned in the committed
# .terraform.lock.hcl, which carries darwin_arm64, linux_amd64 and linux_arm64 (step 6.3) so
# the Stage 7-8 runners do not fail `init` with a checksum error that reads like an attack.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
