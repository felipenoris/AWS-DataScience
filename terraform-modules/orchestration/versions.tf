# Version pin. Same constraint as every slice (Stage 2 step 1), plus awscc: the MWAA Serverless
# workflow exists in no other provider, and awscc v1.99.0 is the first release whose
# awscc_mwaaserverless_workflow carries `code` (Stage 10 step 0.2). The exact builds are pinned by
# each caller's .terraform.lock.hcl - a module carries no lock file of its own.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }

    awscc = {
      source  = "hashicorp/awscc"
      version = ">= 1.99.0, < 2.0.0"
    }
  }
}
