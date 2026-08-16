variable "name" {
  description = "Role name, awsds-<env>-<component> (conventions §6). Also the Name tag."
  type        = string
  nullable    = false
}

variable "description" {
  description = "What assumes this role and why."
  type        = string
  nullable    = false
}

variable "assume_role_policy" {
  description = "Trust policy JSON - who may assume the role."
  type        = string
  nullable    = false
}

variable "permissions_boundary" {
  description = "Boundary policy ARN. REQUIRED, no default: pass null only when omitting the boundary is a decision (docs/plan/conventions.md, IAM rules) - a service role authored by the infrastructure user is the one legitimate case today."
  type        = string
  nullable    = true

  validation {
    condition     = var.permissions_boundary == null || can(regex("^arn:", var.permissions_boundary))
    error_message = "permissions_boundary must be a policy ARN, or an explicit null."
  }
}

variable "inline_policies" {
  description = "Inline policies, name => JSON document."
  type        = map(string)
  default     = {}
}

variable "managed_policy_arns" {
  description = "Managed policy ARNs to attach. Empty by default - the IAM rules prefer a policy written for the job (D31)."
  type        = list(string)
  default     = []
}
