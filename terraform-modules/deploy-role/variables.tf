variable "name" {
  description = "The deploy role's name, from DEPLOY_ROLES in scripts/tfhygiene/backend.py - a contract with ./aws/cicd.py."
  type        = string
  nullable    = false

  validation {
    condition     = startswith(var.name, "awsds-deploy-")
    error_message = "A deploy role is named awsds-deploy-*: the ceiling's DenyChangingTheDeployIdentities protects that pattern, and ./aws/cicd.py reads it."
  }
}

variable "description" {
  description = "What the role applies, and from where."
  type        = string
  nullable    = false
}

variable "env" {
  description = "This account's <env> name token: it names the ceiling, the state bucket, the state key alias and the rule."
  type        = string
  nullable    = false
}

variable "runner_role_arn" {
  description = "The deploy runner's role - the only principal the trust admits (Stage 8 step 4.1). Built by the caller from the runner's name and its home's account id, never pasted."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:[^:]+:iam::[0-9]{12}:role/awsds-[a-z]+-runner-deploy$", var.runner_role_arn))
    error_message = "runner_role_arn must name one role, awsds-<env>-runner-deploy, in one account: never a wildcard and never a path."
  }
}

variable "state_prefixes" {
  description = "The state-key prefixes of the slices this role applies, each ending in '/' (e.g. \"staging/egress/\"). Read, write and delete under each - the lock file sits beside the state."
  type        = list(string)
  nullable    = false

  validation {
    condition     = length(var.state_prefixes) > 0 && alltrue([for p in var.state_prefixes : endswith(p, "/")])
    error_message = "state_prefixes needs at least one prefix, each ending in '/', so a prefix never matches a sibling folder."
  }
}

variable "state_read_keys" {
  description = "Whole state keys the applied slices read through terraform_remote_state and never write (e.g. \"staging/foundation/terraform.tfstate\")."
  type        = list(string)
  default     = []
  nullable    = false
}

variable "inline_policies" {
  description = "The grants particular to this account, name => JSON document, beside the state access every deploy role carries."
  type        = map(string)
  default     = {}
  nullable    = false
}

variable "boundary_denies_json" {
  description = "Deny statements particular to this account, as one policy document merged into the ceiling. Every Sid must differ from the module's own."
  type        = string
  default     = null
}

variable "application_boundary_name" {
  description = "The application ceiling's policy name in a deployment-target account (awsds-<env>-app-boundary). Set, the ceiling denies creating or changing a role that does not carry it, and removing any role's ceiling. Null in an account the deploy role reaches for one named role, Sandbox's."
  type        = string
  default     = null
}

variable "misuse_alarm" {
  description = "Create the misuse rule (Stage 8 step 4.6). True in the deployment-target accounts, which carry an alerts topic (decision 5)."
  type        = bool
  default     = false
  nullable    = false
}

variable "alerts_topic_arn" {
  description = "The account's awsds-<env>-alerts topic, the rule's target. Required when misuse_alarm is true."
  type        = string
  default     = null

  validation {
    condition     = !var.misuse_alarm || var.alerts_topic_arn != null
    error_message = "misuse_alarm needs alerts_topic_arn: a rule with no target is an alarm nobody hears."
  }
}
