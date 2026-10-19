# Inputs. region, env, environment_tag, account_folder and domain arrive from the generated,
# untracked terraform.auto.tfvars (./scripts/gen-tfvars.py <account> model-access). project_models
# is this slice's own.

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

variable "account_folder" {
  description = "This slice's own account folder - the first token of the state key of the same-account sagemaker/ read, which no .tf file may re-derive from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

variable "domain" {
  description = "The account that owns the SMUS domain (SMUS_DOMAIN in scripts/tfhygiene/backend.py) - read for the domain ARN, whose account the provisioning role's name and both trust policies carry."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

# ------------------------------------------------------------------------- the profiled models
#
# The models a project may get an application inference profile of, as `foundation model id => the
# us. inference profile id it is copied from`, or "" for a model invoked on demand in one Region.
# The three Claude models are Stage 6e's scoped set, sandbox/bedrock/'s `models`, which lists four
# consumers of that one set: this map is a fifth, and the first to add a model to it. Titan Text
# Embeddings V2 is the knowledge base's embeddings model (Stage 17 decisions 1 and 11). The two
# lists differ on purpose (Lesson 51), and a change of the scoped set edits both.
#
# The provisioning role may create a profile of these models and of no other. Which of them a
# project reaches is the console's Manage; whether a call through a profile is admitted is the SCP
# DenyBedrockInvocationOutsideTheScopedModels, on the foundation model's pass.
variable "project_models" {
  description = "Foundation model id => the us. inference profile id a project's application inference profile is copied from, or \"\" for an on-demand model. The provisioning role may profile these alone."
  type        = map(string)

  default = {
    "anthropic.claude-opus-4-5-20251101-v1:0"   = "us.anthropic.claude-opus-4-5-20251101-v1:0"
    "anthropic.claude-sonnet-4-5-20250929-v1:0" = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    "anthropic.claude-haiku-4-5-20251001-v1:0"  = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    "amazon.titan-embed-text-v2:0"              = ""
  }

  validation {
    condition     = length(var.project_models) > 0
    error_message = "an empty map would build a CreateInferenceProfile statement with an empty Resource list."
  }

  validation {
    condition     = alltrue([for m, p in var.project_models : p == "" || p == "us.${m}"])
    error_message = "a model's profile is its us. system inference profile, `us.<model id>`, or \"\" for an on-demand model."
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
