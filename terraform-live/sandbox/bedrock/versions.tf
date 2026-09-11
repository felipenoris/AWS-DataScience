# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's.
#
# One provider. Everything here is IAM, which the aws provider has covered since before this
# project - unlike sandbox/sagemaker/, whose blueprint configuration carries a field only awscc
# offers.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
