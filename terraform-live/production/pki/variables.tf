# Inputs, all generated (./scripts/gen-tfvars.py production pki), none authored here: region and env
# for Stage 2's standing reasons, account_folder because the remote-state key of foundation/ is
# built from the account folder, which no .tf file may re-derive from the env token (Lesson 14).
# The certificate lifetimes are defaults below, with D15 note 5's ceiling as their validation.

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
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
  description = "This slice's terraform-live/ folder name - the first path segment of every state key."
  type        = string
  nullable    = false
}

variable "root_validity_hours" {
  description = "The root CA's lifetime. Ten years: a root rotation is a rebuild of every client surface (D36 section 6, rehearsed at Stage 12), not a scheduled event."
  type        = number
  default     = 87600
}

variable "leaf_validity_hours" {
  description = "Each leaf's lifetime. 9000 hours is 375 days, under D15 note 5's 398-day ceiling, which trust stores apply to publicly trusted roots and which this design does not rely on being exempt from. Terraform re-issues a leaf early_renewal_hours before it expires (main.tf), and the re-issue reaches the host through runbooks/gitlab.md."
  type        = number
  default     = 9000

  validation {
    condition     = var.leaf_validity_hours <= 398 * 24
    error_message = "leaf_validity_hours must not exceed 398 days (9552 hours) - D15 note 5."
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
  default     = "stage-07"
}
