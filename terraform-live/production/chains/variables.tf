# Inputs. All of them but the deployment project's name arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py production chains).

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
  description = "This account's terraform-live/ folder - the state keys of foundation/ and studio/ are built from it, never re-derived from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "deployment_project_name" {
  description = "This account's deployment project, by the name an application's manifest gives its stage (Stage 19 step 4.6): the CI/CD CLI writes it into each workflow's name."
  type        = string
  default     = "deploy-production"
  nullable    = false
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
  default     = "stage-19"
}
