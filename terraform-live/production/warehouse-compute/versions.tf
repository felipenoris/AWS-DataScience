# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's.
#
# One provider, and the lock file holds hashicorp/aws at 6.68.0, the build sandbox/warehouse-compute/
# locks (Stage 9 step 9.1). Versions before 6.66.0 reject a `config_parameter` key outside their own
# allow-list and keep every key the service returns, so once Redshift returns
# `enable_large_strings_opt_in` (2026-10-13) the workgroup plans a change forever and its update fails
# (hashicorp/terraform-provider-aws#50257). The constraint stays the tree's `~> 6.60`, the one
# scripts/check-provider-locks.py compares.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
