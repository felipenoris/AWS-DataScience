# Version pin - Stage 2 step 1, the constraint every slice carries, plus awscc: the MWAA Serverless
# workflow exists in no other provider, and awscc v1.99.0 is the first release whose
# awscc_mwaaserverless_workflow carries `code` (Stage 10 step 0.2). scripts/check-provider-locks.py
# compares required_version and the hashicorp/aws constraint against sandbox/foundation's; the
# second provider is not compared. The exact builds are pinned in .terraform.lock.hcl, which carries
# darwin_arm64, linux_amd64 and linux_arm64 (step 6.3): the deploy runner applies this slice.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }

    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.99"
    }
  }
}
