# The fence around this account's deployment project role (Stage 19 decision 21 (b), TM-30): the
# buckets and repositories of this account the role never touches. The module denies them in the
# D13 boundary (main.tf). This file is the account's own, as project-roles.tf is: the other files of
# the slice are copies of staging/studio/'s (scripts/check-copies.py).
#
# Production is the hub: it holds GitLab's buckets, the release bundles, the Terraform state and the
# deploy image beside the data platform's buckets.
# A bucket created in this account joins the list in the same commit, and ./aws/deploytargets.py
# DT-14 fails on one that is neither listed nor the projects bucket.

variable "fenced_bucket_names" {
  description = "This account's buckets the deployment project's role never touches: every bucket but awsds-prod-smus-projects."
  type        = list(string)
  default = [
    "awsds-prod-derived",
    "awsds-prod-gitlab-backup",
    "awsds-prod-gitlab-objects",
    "awsds-prod-outputs",
    "awsds-prod-releases",
    "awsds-prod-tfstate",
  ]
}

variable "fenced_repository_names" {
  description = "This account's ECR repositories the deployment project's role never reads."
  type        = list(string)
  default     = ["awsds-prod-ecr-deploy"]
}

# The warehouse workflow's job opens its session on the governed workgroup with
# redshift-serverless:GetCredentials, over JDBC (decision 16 (b), warehouse.tf), so that service is
# not on the list: the Data API and the query editor, the other doors to a database session, are.
variable "fenced_services" {
  description = "The services the deployment project's role never calls in this account: the generative ones, and the warehouse's doors but the one the load takes."
  type        = list(string)
  default     = ["bedrock", "bedrock-agentcore", "q", "codewhisperer", "redshift-data", "sqlworkbench"]
}
