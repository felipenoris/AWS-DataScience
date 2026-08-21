# Inputs. The module is deliberately small: a repository, its three non-negotiable settings,
# a lifecycle policy and ONE resource policy whose whole content is "which accounts may pull".

variable "name" {
  description = "Repository name, awsds-<env>-ecr-<image> (docs/plan/conventions.md 6). The image name is the last token because that is what a `docker pull` line reads."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^awsds-[a-z0-9]+-ecr-[a-z0-9-]+$", var.name))
    error_message = "name must be awsds-<env>-ecr-<image>."
  }
}

variable "kms_key_arn" {
  description = "The CMK the repository encrypts layers with - the slice's OWN key (Stage 7 step 5.4, option-preservation measure 3), never the account default. A consumer that may pull must also hold kms:Decrypt on it, which is the key policy's job and not this module's."
  type        = string
  nullable    = false
}

variable "pull_principal_arns" {
  description = "Account root ARNs allowed to PULL - the D35 consumer map, resolved to ARNs by the caller. Empty means no cross-account pull, which is a legitimate state for a repository whose only reader is the account itself. Never a wildcard: a registry that any account may read is the exfiltration path this design spends a whole stage closing."
  type        = list(string)
  nullable    = false
  default     = []
}

variable "untagged_expiry_days" {
  description = "Days an untagged image survives. Untagged means superseded-by-digest or a failed push: nothing references it, and every one of them is stored bytes on the bill."
  type        = number
  default     = 14
}

variable "tagged_image_count" {
  description = "How many tagged images to keep, newest first. The approved-digest chain (Stage 8) pins by digest, so an expired tag is only a convenience lost - but the count is what keeps a weekly rebuild from growing without bound."
  type        = number
  default     = 30
}
