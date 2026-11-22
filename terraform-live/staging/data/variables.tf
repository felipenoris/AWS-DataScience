# Inputs. All of them but the stage's settings arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py staging data).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name."
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

variable "account_folder" {
  description = "This account's terraform-live/ folder - the state key of the VPC slice the outputs bucket trusts, never re-derived from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "vpc_slice" {
  description = "The slice holding the VPC the jobs run in, whose [P] S3 gateway endpoint the outputs bucket trusts: foundation/ in Staging (DATA_CONSUMER_VPC_SLICE in scripts/tfhygiene/backend.py)."
  type        = string
  nullable    = false
}

variable "deploy_role_name" {
  description = "The account's deploy role (DEPLOY_ROLES in scripts/tfhygiene/backend.py): the release job's role, which writes the release's tree under applications/ and the inbox from the deploy runner (Stage 10)."
  type        = string
  nullable    = false
}

variable "lake" {
  description = "The account that owns the lake (DATA_LAKE in scripts/tfhygiene/backend.py), keyed by account folder, carrying the profile and the env token its state bucket name is built from."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

# ------------------------------------------------------------------- the stage's settings

variable "scan_limit_bytes" {
  description = "The enforced workgroup's per-query scan cutoff (decision 2, taken 2026-10-22): 10 GB, 10 x 1024^3 bytes, revised against real queries at Stage 12."
  type        = number
  default     = 10737418240
}

variable "results_expiration_days" {
  description = "Days a query result lives under results/ in the derived bucket (decision 11, taken 2026-10-22)."
  type        = number
  default     = 30
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
  description = "CostCenter tag - the stage that created the resources."
  type        = string
  default     = "stage-09"
}
