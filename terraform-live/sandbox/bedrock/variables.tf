# Inputs. region, env and environment_tag arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> bedrock). project_roles and
# application_roles are this slice's own, edited by hand once per project - see project_roles'
# comment, which is the whole operating cost of this design.

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

  # The experimentation project created 2026-08-22 (Stage 6a pass 3), read from
  # `iam list-roles` on 2026-09-11. Both ids are the service's: `avhvbqn37ty7m8` is the project
  # and `5hkjdsy3umpi1c` the environment, and the pair is what the portal shows in its URL.
  default = [
    "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
  ]

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
# Stage 6e's scoped models, as `model id => us. inference profile id`. THIS IS ONE LIST WITH FOUR
# CONSUMERS (the stage's step 3): this map, the endpoint policy of step 4, the managed-settings
# pins of 5.2, and the retention deny of 7.5 which must not catch any of them. They drift apart
# the moment one is edited alone.
#
# Every entry needs BOTH ARNs the grant builds from it: authorization is evaluated against the
# inference profile AND against each foundation model the profile routes to. A grant naming only
# the foundation model is exactly what the blueprint already gives the role, and 3.1 measured that
# it is not enough.
variable "models" {
  description = "The scoped models: foundation model id => the us. inference profile id it is invoked through. Every one is inference-profile only - the bare model id is not invocable (Stage 6e step 0.1)."
  type        = map(string)

  # The 4.5 generation, and not by preference (Stage 6e decisions 14 and 17). AWS refuses this
  # account the ids without a date: `claude-opus-5` and `claude-sonnet-5` for every principal on
  # 2026-09-12, and Opus, Sonnet and Haiku 5.5 for the infrastructure user on 2026-11-22, each with
  # its agreement `AVAILABLE`, the use-case form present and every availability field green
  # (`AWS_STATE.md` EXC-08). The three below were proven by invocation on 2026-09-12 and route to
  # us-east-1, us-east-2 and us-west-2. Sonnet 4.5 is LEGACY since 2026-10-08 and reaches end of
  # life on 2027-04-08. A change here is this map plus an image release, since the pins also live
  # in gitlab/awsds/dev-env/dev-env/claude-code/managed-settings.json.
  default = {
    "anthropic.claude-opus-4-5-20251101-v1:0"   = "us.anthropic.claude-opus-4-5-20251101-v1:0"
    "anthropic.claude-sonnet-4-5-20250929-v1:0" = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    "anthropic.claude-haiku-4-5-20251001-v1:0"  = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
  }

  validation {
    condition     = length(var.models) > 0
    error_message = "an empty map would build a policy with an empty Resource list, which is a policy that authorizes nothing and reads like one that authorizes everything."
  }
}

# --------------------------------------------------------- an application's dev project (application.tf)
#
# The roles the application policy attaches to, written by hand after the project exists, as
# project_roles are. A role listed here and not in project_roles holds the application's grant and not
# the coding assistant's.
variable "application_roles" {
  description = "The SMUS project roles whose application keeps a guardrail of its own and calls a model under it (Stage 17 step 10.4), by role NAME (not ARN). One entry per application's dev project; empty is legal and attaches nothing."
  type        = list(string)

  # app-genai-dev, created 2026-11-19, the project for app-genai alone and its manifest's `dev` stage
  # (Stage 17 step 10.4); read 2026-11-19.
  default = [
    "datazone_usr_role_b8fz4ovppjijv4_c9sdti5d2gaqs0",
  ]

  validation {
    condition     = alltrue([for r in var.application_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.application_roles) == length(distinct(var.application_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}

variable "application_guardrail_required" {
  description = "Stage 17 step 10.4, step 4: true adds to the application policy a deny of bedrock:InvokeModel and InvokeModelWithResponseStream where the request names no numbered version of a guardrail of this account. false between sittings."
  type        = bool
  default     = false
  nullable    = false
}

variable "account_guardrail_enabled" {
  description = "Stage 17 step 10.4, step 6, decision 27 (a): true creates the account's guardrail, its version and the account-level configuration that enforces it on enforced_models. The configuration is the account's: the peers are told before an apply that turns it on. false between sittings."
  type        = bool
  default     = false
  nullable    = false
}

variable "enforced_models" {
  description = "The models the account-level configuration enforces the account's guardrail on, by model id: Nova Lite alone, so Claude Code's sessions and the scoped Claude models stay outside it (Stage 17 step 10.4, step 6)."
  type        = list(string)
  default     = ["amazon.nova-lite-v1:0"]

  validation {
    condition     = length(var.enforced_models) > 0 && !contains(var.enforced_models, "ALL")
    error_message = "an empty list is refused by the API and ALL enforces the guardrail on every model of the account, Claude Code's included: name each model."
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
