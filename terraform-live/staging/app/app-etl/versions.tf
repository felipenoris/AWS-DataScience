# Version pin - Stage 2 step 1, the constraint every slice carries. scripts/check-provider-locks.py
# compares required_version and the hashicorp/aws constraint against sandbox/foundation's. The exact
# build is pinned in .terraform.lock.hcl, which carries darwin_arm64, linux_amd64 and linux_arm64
# (step 6.3): the deploy runner applies this slice.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
