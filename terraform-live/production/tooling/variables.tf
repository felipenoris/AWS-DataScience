# Inputs, from three sources, and the split is the point:
#
#   generated   terraform.auto.tfvars (./scripts/gen-tfvars.py production tooling): region, env, tag,
#               zone_ids, account_folder, interactive_private_cidrs - the allocation table's values,
#               never literals here.
#   defaults    below: the host's shape, the two volume sizes, the proxy bypass list (a dated
#               literal, step 1.3), the names.
#   typed once  saml.auto.tfvars, gitignored: the identity provider's SSO URL and certificate, read
#               off the Identity Center console at step 3.1 and never committed.

variable "region" {
  description = "AWS region for this slice. No default: see the note above."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary. Not cosmetic: awsds-org-scp-tag-enforcement denies ec2:RunInstances outright when Environment or Project is absent."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "zone_ids" {
  description = "The two AZ zone ids subnets anchor on (Stage 3 step 1.5, D9). Which one this host lands in is zone_index below."
  type        = list(string)
  nullable    = false
}

variable "zone_index" {
  description = "Which authored zone the host lands in. 0 is usw2-az1, where every endpoint set and both hub hosts sit (D9), so peering traffic stays in one AZ. The data volume is created in the same zone; changing this after the first apply replaces both."
  type        = number
  default     = 0
}

variable "account_folder" {
  description = "This slice's terraform-live/ folder name - the first path segment of every state key the remote-state reads are built from."
  type        = string
  nullable    = false
}

variable "interactive_private_cidrs" {
  description = "The private tiers of the Interactive accounts' VPCs, where a SMUS project's app ENIs land - the Sandbox sources 1.2's HTTPS rule admits (INT-09). Generated from the allocation table by scripts/tfhygiene/backend.py, never authored here."
  type        = list(string)
  nullable    = false
}

# ------------------------------------------------------------------- the proxy bypass list (1.3)
#
# A dated literal, copied from production/egress's `no_proxy_all_groups` output (vpc-egress-v0.17.0,
# read at plan time on 2026-10-12), the shape 6d decision 8 gave the house image. This slice cannot
# read that output: it is [D] and applied by hand, while egress/ is [E] and a destroyed slice's
# outputs fail the plan by name. ./aws/supplychain.py SC-11 compares the literal with the output
# and fails when they differ in either direction.
#
# Suffixes and literal addresses only, and never a port: GitLab documents a port in this variable
# as breaking DNS resolution for repository mirroring, and NO_PROXY matchers ignore CIDR notation.
# On this `open` plane a missing name fails open - the call leaves by the proxy to the public
# endpoint, the wrong door, with no error - which is why the list is every name this VPC could
# declare and not the ones its last apply built.
variable "no_proxy" {
  description = "The NO_PROXY value every GitLab component carries: this VPC's endpoint names in every spelling, S3 and DynamoDB in both spellings, the link-local pair, localhost, and the two internal zones as suffixes. Empty means main.tf's dated copy of production/egress's no_proxy_all_groups."
  type        = string
  nullable    = false

  # Empty by default: the value is then main.tf's dated literal with the region filled in. Set it
  # only to override that literal for one apply.
  default = ""

  validation {
    condition     = !strcontains(var.no_proxy, "*") && !strcontains(var.no_proxy, "/") && !strcontains(var.no_proxy, ":")
    error_message = "no_proxy carries a wildcard, a CIDR or a port - none of them matches anything in a NO_PROXY matcher, and a port breaks GitLab's repository mirroring (1.3)."
  }
}

# ------------------------------------------------------------------------------ the host's shape

variable "instance_type" {
  description = "GitLab's size. t4g.large (2 vCPU, 8 GiB) is the realistic minimum for Omnibus with Pages (D8), at a measured 0.0672 USD/h (docs/PRICING.md 8). Every admitted value is Graviton, because data.tf pins the arm64 AMI and an AMI is specific to its architecture."
  type        = string
  default     = "t4g.large"

  validation {
    condition     = contains(["t4g.large", "t4g.xlarge"], var.instance_type)
    error_message = "instance_type must be t4g.large or t4g.xlarge - arm64, matching the AMI data.tf pins."
  }
}

variable "root_volume_size" {
  description = "The root volume, in GiB: the OS and /opt/gitlab (about 3 GiB of Omnibus). 12 is comfortable; GitLab's data is on the separate data volume."
  type        = number
  default     = 12

  validation {
    condition     = var.root_volume_size >= 10 && var.root_volume_size <= 32
    error_message = "root_volume_size must be between 10 and 32 GiB - the data lives on the data volume."
  }
}

variable "data_volume_size" {
  description = "The data volume mounted at /var/opt/gitlab, in GiB - repositories, the database, local Pages deployments; object storage is S3. 50 is the stage's figure (D8: ~USD 4/month at 0.08 USD/GiB-month while stopped, the largest idle item). A [D] volume is a standing cost EBS will not shrink, so the value is a commitment."
  type        = number
  default     = 50

  validation {
    condition     = var.data_volume_size >= 20 && var.data_volume_size <= 200
    error_message = "data_volume_size must be between 20 and 200 GiB."
  }
}

variable "snapshot_retain_count" {
  description = "How many daily DLM snapshots of the data volume are kept. Seven: a week of restore points beside the 30 days of application backups in the backup bucket."
  type        = number
  default     = 7
}

# ------------------------------------------------------------------------------- SAML (step 3.2)
#
# Both empty until step 3.1 has created the Identity Center application: the rendered gitlab.rb
# then carries no SAML block, and GitLab offers the local sign-in alone. Typed into the gitignored
# saml.auto.tfvars once the IdP metadata exists, never committed - the certificate is public, the
# SSO URL carries the Identity Center instance id.
variable "saml_idp_sso_target_url" {
  description = "Identity Center's SAML sign-on URL for the GitLab application (step 3.1's metadata). Empty disables the SAML block."
  type        = string
  default     = ""
}

variable "saml_idp_cert_pem" {
  description = "Identity Center's SAML signing certificate, PEM, from the same metadata. Empty disables the SAML block; both SAML inputs are set together or not at all."
  type        = string
  default     = ""

  validation {
    condition     = (var.saml_idp_cert_pem == "") == (var.saml_idp_sso_target_url == "")
    error_message = "saml_idp_cert_pem and saml_idp_sso_target_url are set together or left empty together - a SAML block with one half is a sign-in loop."
  }
}

# --------------------------------------------------------------------------------- the five tags

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy - and required at RunInstances by awsds-org-scp-tag-enforcement."
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
  default     = "stage-07"
}
