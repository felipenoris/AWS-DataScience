# Version pin. Same constraint as every slice (Stage 2 step 1); the exact build is pinned by
# each CALLER's .terraform.lock.hcl - a module carries no lock file of its own.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
