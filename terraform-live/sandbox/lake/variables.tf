# Inputs. The first three arrive from the generated, untracked terraform.auto.tfvars
# (./scripts/gen-tfvars.py <account> lake); the last two are this slice's own tables, and
# both are edited by hand as projects and tenants come and go.

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment TAG value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

# --------------------------------------------------------------------------- the tenants
#
# WHY THIS IS THIS SLICE'S DECISION AND NOT A COPY OF identity/sso/'s TABLE. It looks like one
# - identity/sso/locals.tf already says which groups are assigned to this account - but the two
# answer different questions, and the difference is visible in the very first reading:
# sso-group-infrastructure IS assigned here and gets no prefix, because it is the operator of
# this bucket rather than a tenant of it. "Assigned to the account" is the sso slice's fact;
# "holds artifacts here" is this one's, and a group may be the first without being the second.
#
# WHAT KEEPS IT FROM DRIFTING ANYWAY (Lesson 14 - a value repeated by hand goes stale in one
# of its copies): every row is resolved against the deployed reserved role in data.tf, through
# one(), which fails the PLAN on a permission set that is not provisioned in this account. So
# an invented row cannot be applied, and a row whose permission set is withdrawn fails by name
# on the next plan rather than leaving a prefix with no possible reader.
#
# The roster below is the one measured on 2026-08-26 (Stage 16 step 0.2): three persona groups
# hold an assignment in this account, each one-to-one with a permission set. It is a variable
# rather than a local because D35 vends a Sandbox per business unit and the next unit's tenants
# are its own question, answered in its tfvars.

variable "tenants" {
  description = "The per-prefix roster: sso-group NAME => the permission set whose reserved role in THIS account is the grantee. The group name is the prefix (s3://awsds-<env>-lake/<sso-group>/), so this map is simultaneously the layout of the bucket and the grant table over it."
  type        = map(string)

  default = {
    "sso-group-data-scientists"     = "DataScientistAccess"
    "sso-group-deployment-managers" = "DeploymentManagerAccess"
    "sso-group-dev-env-stewards"    = "DevEnvStewardAccess"
  }

  validation {
    condition     = alltrue([for g in keys(var.tenants) : startswith(g, "sso-group-")])
    error_message = "every tenant key must be an sso-group-* NAME - it becomes a prefix in the bucket."
  }
}

# ------------------------------------------------------------- the wired projects (pass 4)
#
# THE RUNBOOK'S §W WRITES HERE. One entry per SMUS project that has an S3 connection into this
# bucket; the entries become statements in the access role's TRUST, which is the half of §W
# that lives in code (the other half - the Access Grant for the project role - is hand-made,
# because it dies with the project).
#
# WHY THE TRUST NEEDS ENTRIES AT ALL, given that S3 Access Grants assumes this role through its
# own service statement: a runtime assume that carries session tags or a source identity is
# REJECTED by a trust that merely names the principal, so if the connection's vend is a direct
# sts:AssumeRole by the project role - which is what AWS's connection documentation describes,
# read 2026-08-26 - the three actions have to be admitted explicitly. Which of the two paths
# the service actually takes is verification (ii), measured at step 4.2 and not before: this
# map starts EMPTY and the first entry is written by the first wiring.
#
# NEVER A WILDCARD PRINCIPAL. `./aws/sandboxlake.py` SL-2 fails on one, and the enumeration is
# the register: a project that is gone leaves a row here, which is what makes §R's second half
# auditable at all.

variable "wired_projects" {
  description = "SMUS projects with an S3 connection into this bucket: a free-form key => { project_role_arn, project_id }. Empty until step 4.1. Appended by runbooks/sandbox-lake.md §W and REMOVED by §R - an entry outliving its project is the finding, not the record."
  type = map(object({
    project_role_arn = string
    project_id       = string
  }))
  default = {}

  validation {
    condition     = alltrue([for p in values(var.wired_projects) : can(regex("^arn:[a-z-]+:iam::[0-9]{12}:role/datazone_usr_role_", p.project_role_arn))])
    error_message = "project_role_arn must be a datazone_usr_role_* role ARN - the project USER role the portal shows on the project overview page."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
  type        = string
  default     = "AWS-DataScience"
}

variable "owner" {
  description = "Owner tag - an sso-group-* GROUP, never a person (docs/plan/conventions.md)."
  type        = string
  default     = "sso-group-infrastructure"
}

variable "cost_center" {
  description = "CostCenter tag - the stage that created the resource."
  type        = string
  default     = "stage-16"
}
