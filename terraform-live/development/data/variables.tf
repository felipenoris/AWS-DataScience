# Inputs. All four arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> data) - region and env for Stage 2's standing reasons,
# and the lake map because profile names live in the PROFILES table of
# scripts/tfhygiene/backend.py and may be a literal in no .tf file (Lesson 14).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "lake" {
  description = "The account that OWNS the lake (DATA_LAKE in scripts/tfhygiene/backend.py) - keyed by account folder, carrying the profile and the env token its state bucket name is built from. Consumed twice: an aliased provider that resolves the catalog id live, and a terraform_remote_state read of data-governance/data/ for the shared database names. A map rather than a scalar so it renders through the same emission every other cross-account read in this tree uses."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md)."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-05"
}
