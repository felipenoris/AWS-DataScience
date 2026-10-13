# Version pin - Stage 2 step 1. The same constraint every slice carries (scripts/check-provider-locks.py
# compares it with sandbox/foundation's). One provider: a role, a security group and a remote-state read.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
