# Inputs. region, env and environment_tag arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> bedrock). project_roles is this slice's
# own, edited by hand once per project - see its comment, which is the whole operating cost of
# this design.

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

# ------------------------------------------------------------------------ one entry per project
#
# THE ROLES THIS SLICE ATTACHES TO ARE NOT CREATED HERE, and cannot be: SageMaker Unified Studio
# mints `datazone_usr_role_<project>_<environment>` when a project is created in the portal, and
# both ids in that name are the service's. So the list below is written by hand AFTER the project
# exists, and Stage 6e decision 8 took that cost deliberately over the alternative (a role this
# repository authors, reached by role chaining, whose trust policy would have listed the projects).
# The boundary decided it: attaching here keeps the invocation on the project role, under
# awsds-sandbox-project-boundary, where every other interactive call in this account already is.
#
# THE COST IS LESSON 14, AND IT IS PAID PER PROJECT. A project whose role is missing from this list
# gets no Bedrock access, and the failure is loud rather than silent: the assistant refuses at the
# first prompt. The Haiku half is the one worth naming - background work runs on it (Stage 6e 5.3),
# so a role in the list but a model out of `models` below fails in the MIDDLE of a working session
# instead of at its start.
#
# runbooks/claude-code-sagemaker.md section P is the procedure, in both forms: this slice, and the
# aws CLI equivalent for a project that needs the grant before the next apply window.
variable "project_roles" {
  description = "The SMUS project roles that may invoke the scoped models, by role NAME (not ARN). One entry per project; empty is legal and attaches nothing."
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`. A role of any other shape is not a project role, and this slice grants Bedrock to project roles only."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}

# ------------------------------------------------------------------------------ the scoped set
#
# Stage 6e's three models, as `model id => us. inference profile id`. THIS IS ONE LIST WITH FOUR
# CONSUMERS (the stage's step 3): this map, the endpoint policy of step 4, the managed-settings
# pins of 5.2, and the retention deny of 7.5 which must not catch any of them. They drift apart
# the moment one is edited alone.
#
# Every entry needs BOTH ARNs the grant builds from it: authorization is evaluated against the
# inference profile AND against each foundation model the profile routes to. A grant naming only
# the foundation model is exactly what the blueprint already gives the role, and 3.1 measured that
# it is not enough.
variable "models" {
  description = "The scoped models: foundation model id => the us. inference profile id it is invoked through. All three are inference-profile only - the bare model id is not invocable (Stage 6e step 0.1)."
  type        = map(string)

  default = {
    "anthropic.claude-opus-5"                  = "us.anthropic.claude-opus-5"
    "anthropic.claude-sonnet-5"                = "us.anthropic.claude-sonnet-5"
    "anthropic.claude-haiku-4-5-20251001-v1:0" = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
  }

  validation {
    condition     = length(var.models) > 0
    error_message = "an empty map would build a policy with an empty Resource list, which is a policy that authorizes nothing and reads like one that authorizes everything."
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
  default     = "stage-06e"
}
