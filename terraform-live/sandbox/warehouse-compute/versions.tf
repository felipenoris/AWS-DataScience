# Version pin - Stage 2 step 1. The same constraint every slice carries.
#
# Terraform has no repository-wide pin: the constraint belongs to each root module, so these lines
# are repeated per slice (Lesson 14). scripts/check-provider-locks.py compares required_version and
# the hashicorp/aws constraint against sandbox/foundation's.
#
# One provider. `aws_redshiftserverless_namespace` has been in the aws provider since 4.x, and
# nothing here needs a field only awscc offers - unlike sandbox/sagemaker/, whose blueprint
# configuration does.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
