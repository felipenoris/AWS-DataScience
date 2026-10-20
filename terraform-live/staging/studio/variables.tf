# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py staging studio).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. `staging` here: the account Stage 18 measures a deployment project in."
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
  description = "This slice's own account folder - the first token of its state key, which no .tf file may re-derive from the env token (the reverse map would be a second copy of ENV_TOKENS, Lesson 14). Used for the same-account foundation/ read."
  type        = string
  nullable    = false
}

variable "lake" {
  description = "The account that owns the governed lake (DATA_LAKE in scripts/tfhygiene/backend.py) - read for the Lake Formation-registered bucket ARNs the D13 boundary excludes, the drop-box prefix it carves back in, and the lake data key."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "domain" {
  description = "The account that owns the SMUS domain (SMUS_DOMAIN in scripts/tfhygiene/backend.py). Read only on the second apply, for the domain id the blueprint configurations name. Same account as `lake` today and a different question - see the backend.py comment."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "blueprints_enabled" {
  description = "false until this account's SMUS association has been accepted and the row added to backend.SMUS_ASSOCIATED (Stage 18 steps 2.1 and 2.3 - the association has no public API). true is the second apply (2.5): decision 1's blueprint configuration and its grant."
  type        = bool
  default     = false
}

variable "blueprint_names" {
  description = "Stage 18 decision 1's base blueprint and, for 7.2's published table, DataLake (decision 5, path A, the user's on 2026-10-20): a deployment project enables no capability a person would use, so the module's default list (Sandbox's twelve) is not this slice's. Tooling with enableSpaces false in the deployment profile creates no SageMaker AI domain (its sageMakerDomainRequired condition is false), so sagemaker:CreateDomain needs no carve-out; DataLake creates a project's Glue database, its Lake Formation permissions and an Athena workgroup, through the provisioning role Staging's Lake Formation admits as an admin. The first apply (blueprints_enabled = false) does not read this list."
  type        = list(string)
  default     = ["Tooling", "DataLake"]
}

# The roles the workflows grant attaches to (workflows.tf) are minted by SageMaker Unified Studio when a
# project is created, `datazone_usr_role_<project>_<environment>`, so the list is written by hand after
# the project exists, as sandbox/workflows/'s is.
variable "project_roles" {
  description = "The SMUS project roles whose workflows create Glue and SageMaker processing jobs, by role NAME (not ARN). Empty is legal and attaches nothing: Stage 18 step 8.1 empties it before the project is deleted."
  type        = list(string)
  # deploy-staging, created 2026-10-19 (Stage 18 pass 3); read with `iam list-roles` 2026-10-19.
  default = ["datazone_usr_role_d1veybt5oak4uo_bujd259b8g9zps"]

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}

variable "allowed_instance_types" {
  description = "The ml.* ceiling (D12). null - the default - is the right answer: the list lives once, in terraform-modules/sagemaker-denies, and the six persona sets in identity/sso/ compose the same fragment. The variable survives so that a business unit which genuinely needs a different ceiling can say so in its tfvars rather than in the shared module (D35: this slice is one unit's, not *the* Sandbox's)."
  type        = list(string)
  default     = null
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
  default     = "stage-18"
}
