# Inputs - Stage 2 step 2.
#
# THE FIRST TWO HAVE NO DEFAULT, AND THAT IS THE DESIGN. `region` may not be a literal in a
# .tf file (docs/plan/architecture.md, region portability - step 9.1 scans for it), and `env`
# may not be hardcoded either: step 3.3 requires that nothing in this slice is written as
# *the* sandbox, because Stage 14 vends one Sandbox per business unit (D35). Both arrive from
# the generated, untracked terraform.auto.tfvars:
#
#   ./scripts/gen-tfvars.py sandbox bootstrap
#
# The values come from scripts/tfhygiene/backend.py - the same module that builds backend.hcl,
# so the region in the backend and the region the provider uses cannot disagree.
#
# The remaining three ARE defaulted, because they are constants of this repository rather than
# of this account: the project name, the owning group and the stage that paid for the resource.

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name. NOT the Environment tag value, which is spelled differently for three of the six."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md: sandbox, dev, data, staging, prod, org."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary (sandbox|development|data|staging|production|org)."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy, which requires the key."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md). State buckets are the infrastructure group's, whoever created them."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-02"
}

variable "state_noncurrent_version_days" {
  description = "Days a noncurrent state version is kept. A COST choice, not a compliance one (step 2, decision 3): every apply writes a version, and a rule added later does not reach what already accumulated. 90 days is long enough to recover a state file somebody broke and forgot about."
  type        = number
  default     = 90
}
