# Inputs. Everything but the tag defaults arrives from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py data-governance data) - region and env for
# Stage 2's standing reasons, and the account maps because profile names live in the PROFILES
# table of scripts/tfhygiene/backend.py and may be a literal in no .tf file (Lesson 14).

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. 'data' for this account."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "consumers" {
  description = "Profile, env token and VPC slice per consumer account (INT-03's N+2), derived in scripts/tfhygiene/backend.py - never authored here. Consumed twice: the terraform_remote_state reads of each consumer's VPC slice (the [P] S3 gateway-endpoint id, INT-05's anchor; workloads/ for Production, foundation/ elsewhere), and the aliased providers that resolve each account id for the shares and the drop-box statements."
  type        = map(object({ profile = string, env = string, vpc_slice = string }))
  nullable    = false
}

variable "producers" {
  description = "The account whose job role empties the drop-box (D25, INT-10) - production, resolved to an id by an aliased provider. The role itself (awsds-prod-job-exec) does not exist until Stage 9; the statements name it by ArnLike condition, which S3 does not validate - a nonexistent Principal ARN would reject the whole policy."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

# ------------------------------------------------- Stage 6f step 11, the lake-publishing pilot

variable "lake_publishing_enabled" {
  description = "From backend.LAKE_PUBLISHERS (generated). true seats awsds-data-smus-provisioning and awsds-data-smus-manage-access as Lake Formation administrators beside InfrastructureAccess (publishing.tf), before the publishing project's first environment writes the same list."
  type        = bool
  default     = false
}

variable "lake_publisher_role" {
  description = "The publishing project's role, by NAME, hand-written after its Tooling environment exists (Stage 6f step 11.5), the way sandbox/bedrock/ names project roles. null grants nothing. The role receives DESCRIBE on curated and DESCRIBE and SELECT with the grant option on each table of publishing.tf's list, the terms DataZone sets for publishing a Glue table."
  type        = string
  default     = null

  validation {
    condition     = var.lake_publisher_role == null || can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", var.lake_publisher_role))
    error_message = "the publisher is a SMUS project role, `datazone_usr_role_<project>_<environment>`."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* group, never a person (docs/plan/conventions.md)."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-05"
}
