# Version pin. Same constraint as every slice (Stage 2 step 1). The exact build is pinned by each
# caller's .terraform.lock.hcl - a module carries no lock file of its own. The awscc provider left
# with the workflow resource (Stage 19 step 4.11): the CI/CD CLI creates the workflows.

terraform {
  required_version = "~> 1.15"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.60"
    }
  }
}
