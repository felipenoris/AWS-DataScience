# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's.
#
# One provider only. The SageMaker image, its version and the two app image configurations all
# exist in hashicorp/aws (measured against the pinned schema, 2026-09-10), so this slice needs no
# awscc block - unlike sandbox/sagemaker/, whose blueprint configuration carries a field the aws
# provider does not have.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
