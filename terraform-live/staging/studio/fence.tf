# The fence around this account's deployment project role (Stage 19 decision 21 (b), TM-30): the
# buckets and repositories of this account the role never touches. The module denies them in the
# D13 boundary (main.tf). This file is the account's own, as project-roles.tf is: the other files of
# the slice are copies of production/studio/'s (scripts/check-copies.py).
#
# Staging holds the data platform's buckets and its Terraform state, and no registry.
# A bucket created in this account joins the list in the same commit, and ./aws/deploytargets.py
# DT-14 fails on one that is neither listed nor the projects bucket.

variable "fenced_bucket_names" {
  description = "This account's buckets the deployment project's role never touches: every bucket but awsds-staging-smus-projects."
  type        = list(string)
  default = [
    "awsds-staging-derived",
    "awsds-staging-outputs",
    "awsds-staging-tfstate",
  ]
}

# Staging holds no warehouse (D40), so every door to one is on the list.
variable "fenced_services" {
  description = "The services the deployment project's role never calls in this account: the generative ones and Redshift's."
  type        = list(string)
  default     = ["bedrock", "bedrock-agentcore", "q", "codewhisperer", "redshift", "redshift-data", "redshift-serverless", "sqlworkbench"]
}

variable "fenced_repository_names" {
  description = "This account's ECR repositories the deployment project's role never reads."
  type        = list(string)
  default     = []
}
