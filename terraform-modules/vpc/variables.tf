variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "vpc_cidr" {
  description = "The /16 from the allocation table in scripts/tfhygiene/backend.py (Stage 3 decision 1) - arrives through the generated terraform.auto.tfvars, never a literal in a .tf file."
  type        = string
  nullable    = false
}

variable "zone_ids" {
  description = "Exactly two AZ ZONE IDS (usw2-az1, ...) - D9. Subnets anchor on the id, never on a name and never on list position (step 1.5): both peerings carry constant traffic, and cross-AZ bills USD 0.01/GB each way with no error anywhere."
  type        = list(string)
  nullable    = false

  validation {
    condition     = length(var.zone_ids) == 2
    error_message = "Exactly two zone ids (D9: two AZs, no more - cost - and no fewer - subnet diversity requirements arrive at Stage 6)."
  }
}

variable "flow_log_role_arn" {
  description = "Delivery role for the flow log (the iam-role module's first caller, in the slice)."
  type        = string
  nullable    = false
}

variable "flow_log_retention_days" {
  description = "Flow-log retention - Stage 3 decision 3: 30 days, for debugging, not detection."
  type        = number
  default     = 30
}

variable "s3_endpoint_allowed_bucket_names" {
  description = "AWS-owned bucket names (wildcards allowed) the S3 gateway endpoint admits beside the organization - step 9.3's five families. null = the documented default in endpoints.tf; names are documentation, not measurement (Lesson 23), confirmed by verification (iii)."
  type        = list(string)
  default     = null
}
