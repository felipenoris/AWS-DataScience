# Version pin - Stage 2 step 1, the constraint every slice carries, plus awscc for the blueprint
# configuration (sandbox/sagemaker/versions.tf records why). The exact builds are in the committed
# .terraform.lock.hcl, for darwin_arm64, linux_amd64 and linux_arm64 (Stage 2 step 6.3).

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
