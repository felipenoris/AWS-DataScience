# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's.
#
# Two providers. The aws provider carries the IAM grants and the account's guardrail; awscc carries
# the account-level enforced guardrail configuration, which the aws provider does not (Stage 17
# verification xlix, read 2026-11-17 at awscc 1.106.0).

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.89"
    }
  }
}
