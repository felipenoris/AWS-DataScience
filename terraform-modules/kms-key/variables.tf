variable "alias_name" {
  description = "Alias WITHOUT the alias/ prefix, awsds-<env>-<component> (conventions §6). Also the Name tag."
  type        = string
  nullable    = false
}

variable "description" {
  description = "What the key encrypts - shown in every console listing, so say the component, not 'a key'."
  type        = string
  nullable    = false
}

variable "deletion_window_in_days" {
  description = "Days between scheduling deletion and the key ceasing to exist - the undo window."
  type        = number
  default     = 30
}

variable "policy" {
  description = "Key policy JSON. null = delegate to the account's IAM (the bootstrap-key shape). A key whose reads are themselves a control (D19, D31) passes its own document."
  type        = string
  default     = null
}
