# Inputs. All of them but the release (release.tf) arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> app/app-etl).

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
    condition     = contains(["staging", "prod"], var.env)
    error_message = "env must be staging or prod: an application slice lives in a deployment target (Stage 8 decision 21)."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["staging", "production"], var.environment_tag)
    error_message = "environment_tag must be staging or production."
  }
}

variable "account_folder" {
  description = "This account's terraform-live/ folder - the state keys of sagemaker/ and data/ are built from it, never re-derived from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "registry" {
  description = "The registry account (REGISTRY_HOME in scripts/tfhygiene/backend.py), keyed by account folder, with the profile its state is read through: on the deploy runner the runner's own (decision 14)."
  type        = map(object({ profile = string, env = string }))
  nullable    = false

  validation {
    condition     = length(var.registry) == 1
    error_message = "One registry account (D14)."
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
  description = "CostCenter tag - the stage that created the resources."
  type        = string
  default     = "stage-08"
}
