# Inputs. region, env and environment_tag arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> ml). project_roles is this slice's own, edited by hand once per
# project.

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
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

# The roles this slice attaches to are minted by SageMaker Unified Studio when a project is created,
# `datazone_usr_role_<project>_<environment>`, so the list is written by hand after the project
# exists, as sandbox/workflows/'s is. A project missing from it is refused, as sagemaker:AddTags, the
# create of a tagged model package group from its notebook.
variable "project_roles" {
  description = "The SMUS project roles whose members create, from a notebook, what this slice's policy lets them tag, by role NAME (not ARN). One entry per project; empty is legal and attaches nothing."
  type        = list(string)

  # One entry per project, each role's AmazonDataZoneProject tag read from `iam list-role-tags` and its
  # project from `datazone get-project` on 2026-11-19:
  # - eighth-experimentation, where Stage 17's passes 0 to 8 run; its step 3.2 creates the group
  #   ml-demo-xgboost.
  # - app-ml-dev, the project for app-ml alone; Stage 17 step 9.6 creates the group app-ml-dev there.
  default = [
    "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
    "datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk",
  ]

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
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
  default     = "stage-17"
}
