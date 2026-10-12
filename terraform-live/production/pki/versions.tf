# Version pin - Stage 2 step 1. The same aws constraint every slice carries, plus the `tls`
# provider, which only this slice uses: the root and the two leaves are its resources (D36).
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's; a second provider is allowed and is
# not compared, which is why the copies are not byte-compared.
#
# The constraint admits a range; the exact build is pinned in the committed .terraform.lock.hcl,
# which carries darwin_arm64, linux_amd64 and linux_arm64 (step 6.3) so the Stage 7-8 runners do
# not fail init with a checksum error that reads like an attack.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }
}
