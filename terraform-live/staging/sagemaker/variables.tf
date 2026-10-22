# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py staging sagemaker).

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

variable "registry" {
  description = "The account holding the ECR repositories: account folder => { profile, env }. One entry - REGISTRY_HOME in scripts/tfhygiene/backend.py."
  type = map(object({
    profile = string
    env     = string
  }))

  validation {
    condition     = length(var.registry) == 1
    error_message = "exactly one registry account - the application repositories live in Production (D14)."
  }
}

# ------------------------------------------------------------------- the job log groups (4.3)
variable "log_retention_days" {
  description = "Retention on the job log groups this slice pre-creates. 30 days, the figure Production's job groups carry (production/sagemaker/)."
  type        = number
  default     = 30
}

variable "account_folder" {
  description = "This account's terraform-live/ folder - the state key of the VPC slice the job network reads, never re-derived from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (D9). The first entry is where the Glue connection's subnet is selected - a selection among authored zones, made in one place."
  type        = list(string)
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
  default     = "stage-09"
}
