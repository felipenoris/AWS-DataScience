# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py production registry).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name."
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

variable "consumers" {
  description = "The accounts that PULL images and READ packages (REGISTRY_CONSUMERS in scripts/tfhygiene/backend.py, D35's forward constraint). Keyed by account folder, carrying the profile an aliased provider resolves the account id from - a profile may be a literal in no .tf file (Lesson 14). It is NOT the lake's consumer list: that answers a different question and Stage 9 adds Production to it while this one must never carry the account that owns the registry."
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
  description = "CostCenter tag - the stage that created the resource (see providers.tf)."
  type        = string
  default     = "stage-06"
}
