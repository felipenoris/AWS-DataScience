variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

# STAGE 6c step 0.4 (2026-09-06) - the one input that exists because an ACCOUNT can hold more
# than one VPC. Until D38 every account had exactly one, so `awsds-<env>-` was unambiguous and
# two of the names below are ACCOUNT-unique rather than VPC-unique: the flow-log log group is a
# hard create-time conflict, and every `Name` tag is what ./aws/networking.py reads to tell one
# object from another. Security-group NAMES would not have collided - they are scoped to a VPC -
# but their tags would, which is the same failure one layer up.
#
# DEFAULT EMPTY, SO EVERY EXISTING CALLER IS UNTOUCHED. `sandbox/foundation/` and
# `staging/foundation/` pass nothing and keep `awsds-sandbox-*` and `awsds-staging-*`; only
# Production's three VPCs carry a suffix (`shared`, `networking`, `workloads`). A suffix is part
# of a security group's `name`, so ADDING one to a live slice replaces its security groups -
# which is why 6c step 1.1 reads that plan rather than assuming it.
variable "name_suffix" {
  description = "Distinguishes VPCs inside one account: names become awsds-<env>-<suffix>-*. Empty for an account with a single VPC, which is every account but Production."
  type        = string
  default     = ""
  nullable    = false
}

# STAGE 6c step 1.3 (2026-09-06) - and this input exists because that step needs a VPC whose
# public tier reaches nothing. Under D38 exactly ONE VPC in the estate routes to an internet
# gateway; every other one is private BY THE ABSENCE OF THIS ROUTE, not by lacking a gateway.
#
# WHY THE GATEWAY IS STILL CREATED WHEN THIS IS FALSE. A module that varied its resource SET per
# caller would make "is this VPC private?" a question about which code path ran, answerable only
# by reading the module. Keeping the gateway and dropping the route makes it a question about a
# ROUTE TABLE - which `./aws/networking.py` reads, which a console shows, and which is the same
# object the answer is enforced in. An unattached internet gateway is free.
variable "public_internet_route" {
  description = "Whether the public tier carries 0.0.0.0/0 -> igw. False makes the VPC private without removing the gateway, which is how D38's spokes differ from its hub."
  type        = bool
  default     = true
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
