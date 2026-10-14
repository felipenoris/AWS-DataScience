# Inputs. The first five arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py sandbox app/app-etl); `release` is the one a person writes, in release.tf.

variable "region" {
  description = "AWS region for this slice. No default: it comes from the generated tfvars."
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
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key."
  type        = string
  nullable    = false
}

variable "registry" {
  description = "The registry account (REGISTRY_HOME in scripts/tfhygiene/backend.py), keyed by account folder, with the profile its state is read through - a profile may be a literal in no .tf file."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "job_instance_type" {
  description = "The processing job's instance: ml.t3.medium, 0.050 USD/h (docs/PRICING.md), 6i's measured shape."
  type        = string
  default     = "ml.t3.medium"
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
  default     = "stage-08"
}
