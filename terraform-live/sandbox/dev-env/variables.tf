# Inputs. region, env, environment_tag and the registry map arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> dev-env). No release reaches this slice:
# the versions are the release pipeline's (Stage 8 decision 18, main.tf).

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

# ------------------------------------------------------------------- the registry account
#
# The image lives in Production and is registered here, so this slice reads one state across an
# account boundary: production/registry/'s outputs carry the two repository ARNs the image role's
# statement names. Both would otherwise be
# account-id-bearing literals in a tracked file, which aws/INDEX.md rule 1 forbids (Lesson 3).
#
# The map shape and the profile-from-tfvars idiom are the ones sandbox/sagemaker/ uses for the lake
# and the domain: a profile literal never sits in a .tf file (Lesson 14).

variable "registry" {
  description = "The account holding the ECR repositories: account folder => { profile, env }. One entry - REGISTRY_HOME in scripts/tfhygiene/backend.py."
  type = map(object({
    profile = string
    env     = string
  }))

  validation {
    condition     = length(var.registry) == 1
    error_message = "exactly one registry account - both repositories live in Production (docs/SMUS.md, Custom images)."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* group, never a person (docs/plan/conventions.md). The dev-env stewards own the image; the slice that registers it is the infrastructure group's."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-06d"
}
