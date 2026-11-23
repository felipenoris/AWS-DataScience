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

# Staging holds no warehouse (D40), so every door to one is on the list. The Agent Registry is a service
# prefix of its own, outside bedrock-agentcore, granted by AWS's ML policy since v48 (TM-28).
# Bedrock is not on the list: the boundary admits the application's model call and the guardrail task's
# calls, and leaves every other Bedrock action outside its ceiling (Stage 17 decision 22 (a), main.tf,
# TM-36). A deny here would win over those allows, and the module refuses the pair.
variable "fenced_services" {
  description = "The services the deployment project's role never calls in this account: the generative ones but Bedrock, the Agent Registry and Redshift's."
  type        = list(string)
  default     = ["bedrock-agentcore", "agent-registry", "q", "codewhisperer", "redshift", "redshift-data", "redshift-serverless", "sqlworkbench"]
}

variable "fenced_repository_names" {
  description = "This account's ECR repositories the deployment project's role never reads."
  type        = list(string)
  default     = []
}
