# Inputs. All of them arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> sagemaker).

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

variable "account_folder" {
  description = "This slice's own account FOLDER - the first token of its state key, which no .tf file may re-derive from the env token (the reverse map would be a second copy of ENV_TOKENS, Lesson 14). Used for the same-account foundation/ read."
  type        = string
  nullable    = false
}

variable "lake" {
  description = "The account that OWNS the governed lake (DATA_LAKE in scripts/tfhygiene/backend.py) - read for the Lake Formation-registered bucket ARNs the D13 boundary excludes, the drop-box prefix it carves back in, and the lake data key."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "domain" {
  description = "The account that owns the SMUS domain (SMUS_DOMAIN in scripts/tfhygiene/backend.py). Read only on the SECOND apply, for the domain id the blueprint configurations name. Same account as `lake` today and a different question - see the backend.py comment."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "blueprints_enabled" {
  description = "false until this account's SMUS association has been ACCEPTED and the row added to backend.SMUS_MEMBERS (Stage 6 step 1.3 - the association has no public API). true is the pass 2b apply: the blueprint configurations."
  type        = bool
  default     = false
}

variable "allowed_instance_types" {
  description = "The ml.* ceiling (D12). null - the default - is the right answer: the list lives ONCE, in terraform-modules/sagemaker-denies, and the six persona sets in identity/sso/ compose the same fragment. The variable survives so that a business unit which genuinely needs a different ceiling can say so in ITS tfvars rather than in the shared module (D35: this slice is one unit's, not *the* Sandbox's)."
  type        = list(string)
  default     = null
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
  default     = "stage-06"
}
