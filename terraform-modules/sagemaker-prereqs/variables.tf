# Inputs. Everything that differs between one member account and the next - and nothing else:
# the design lives here so that Sandbox and Development cannot drift (Lesson 14), and each
# caller says WHICH account, never WHAT.

variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - what every name below is built from. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false
}

variable "region" {
  description = "AWS region. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

# ------------------------------------------------------------------- the network parameters
#
# What the blueprint configuration is POINTED AT (Stage 6 step 1.4). Read from this account's
# own foundation/ state by the caller, never pasted: an id in a .tf file is a copy of another
# slice's state that nothing keeps in step.

variable "vpc_id" {
  description = "The account's VPC - the aws:SourceVpc anchor every project app runs inside under VpcOnly."
  type        = string
  nullable    = false
}

variable "private_subnet_ids" {
  description = "The private subnets, keyed by AZ ZONE ID (never a name, never a list position - Stage 3 step 1.5). Project apps attach ENIs here; the map is flattened for the blueprint's Subnets parameter and its keys become the AZs parameter."
  type        = map(string)
  nullable    = false

  validation {
    condition     = length(var.private_subnet_ids) > 0
    error_message = "at least one private subnet is required - VpcOnly has nowhere to attach otherwise."
  }
}

# ----------------------------------------------------------------------- the lake's surface
#
# THE D13 EXCLUSION IS BUILT FROM THESE. They arrive from the LAKE account's state, through
# the caller's cross-account read - so a bucket renamed on the producer side is a plan diff
# here rather than a deny that quietly stops matching anything.

variable "lake_registered_bucket_arns" {
  description = "The bucket ARNs Lake Formation has REGISTERED (raw and curated today). The boundary denies s3:* on these and on everything under them - D13's whole content: a project role that could read the objects directly would make Lake Formation decorative."
  type        = list(string)
  nullable    = false
}

variable "lake_dropbox_write_arn" {
  description = "The one sanctioned direct write into the lake (D18, docs/GOVERNANCE.md §Drop-box): the dated-prefix object ARN pattern the drop-box bucket policy admits. Mirrors the persona's WriteIngestionDropBox statement - the identity half of a two-sided rule (INT-10)."
  type        = string
  nullable    = false
}

variable "lake_data_key_arn" {
  description = "The lake account's data CMK. The boundary lets a project role use it ONLY through S3 (kms:ViaService), mirroring UseLakeDataKeyViaS3 and the key policy's own condition - each side scoping the other."
  type        = string
  nullable    = false
}

# ------------------------------------------------------------------------ the cost ceiling
variable "allowed_instance_types" {
  description = "Pass-through to terraform-modules/sagemaker-denies, which OWNS the list (Lesson 33 - structure and values are both one copy). null, the default, means \"whatever the shared module says\" - which is what every caller should want: identity/sso/ composes the same fragment for the six persona sets, and a second list here is the divergence the shared module exists to prevent."
  type        = list(string)
  default     = null
}

variable "log_retention_days" {
  description = "Retention on /awsds/<env>/studio (Stage 6 step 9.1). 30 matches Stage 3's flow-log decision - the value is not the interesting part, agreeing with the other subsystem is."
  type        = number
  default     = 30
}

# ------------------------------------------------------------- the second apply (pass 2b)
#
# THE ACCOUNT ASSOCIATION HAS NO PUBLIC API (Stage 6 step 1.3), so the blueprint configuration
# cannot be created in the same apply as the roles it names: a domain has to exist and this
# account has to have ACCEPTED an invitation to it. Both halves ride on one flag, emitted from
# backend.SMUS_ASSOCIATED - a table whose rows are measurements, not intentions.

variable "blueprints_enabled" {
  description = "false until this account's SMUS association is accepted (backend.SMUS_ASSOCIATED). true creates the blueprint configurations - the pass 2b apply."
  type        = bool
  default     = false
}

variable "domain_id" {
  description = "The DataZone V2 domain id, read from data-governance/governance/'s state. null while blueprints_enabled is false."
  type        = string
  default     = null
}

variable "blueprint_names" {
  description = "Decision 5's category 1, by API name (docs/SMUS.md is the reference table; ./aws/studio.py US-3 holds the same list). A category-2 blueprint joins BOTH in the same commit that enables it (Lesson 14)."
  type        = list(string)
  default     = ["Tooling", "DataLake", "EMRServerless", "AmazonBedrockGenerativeAI"]
}
