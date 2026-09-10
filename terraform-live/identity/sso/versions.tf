# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: it belongs to each root module, so the four lines are
# repeated per slice (Lesson 14). scripts/check-bootstrap-parity.py keeps the five bootstrap
# copies from drifting; this slice is not one of them.
#
# The constraint admits a range; the exact build is pinned in the committed
# .terraform.lock.hcl, which carries darwin_arm64, linux_amd64 and linux_arm64 (step 6.3) so
# the Stage 7-8 runners do not fail `init` with a checksum error.
#
# Verifications (ii) and (iv) are phrased "in the pinned provider version", which is why the
# pin is a step of its own: a verification whose subject was never written down cannot be
# repeated.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
