# Inputs. region, env and environment_tag arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py <account> lake). tenants and wired_projects are this
# slice's own tables, edited by hand as projects and tenants come and go.

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
# This roster is not a copy of identity/sso/locals.tf. That table says which groups are assigned to
# this account; this one says which groups hold artifacts here. sso-group-infrastructure is assigned
# here and gets no prefix, because it is the operator of this bucket rather than a tenant of it.
#
# Every row is resolved against the deployed reserved role in data.tf, through one(), which fails the
# plan on a permission set that is not provisioned in this account (Lesson 14). An invented row
# cannot be applied, and a row whose permission set is withdrawn fails by name on the next plan
# rather than leaving a prefix with no possible reader.
#
# The roster below was measured on 2026-08-26 (Stage 16 step 0.2): three persona groups hold an
# assignment in this account, each one-to-one with a permission set. It is a variable rather than a
# local because D35 vends a Sandbox per business unit and the next unit's tenants are answered in
# its tfvars.

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
# The runbook's §W writes here: one entry per SMUS project that has an S3 connection into this
# bucket. The entries become statements in the access role's trust, the half of §W that lives in
# code; the other half, the Access Grant for the project role, is hand-made because it dies with the
# project.
#
# The trust needs entries even though S3 Access Grants assumes this role through its own service
# statement. A runtime assume that carries session tags or a source identity is rejected by a trust
# that merely names the principal, so if the connection's vend is a direct sts:AssumeRole by the
# project role - what AWS's connection documentation describes, read 2026-08-26 - the three actions
# have to be admitted explicitly. Which of the two paths the service takes is verification (ii),
# measured at step 4.2.
#
# Never a wildcard principal: `./aws/sandboxlake.py` SL-2 fails on one. The enumeration is the
# register, so a project that is gone leaves a row here and §R's second half stays auditable.

variable "wired_projects" {
  description = "SMUS projects with an S3 connection into this bucket: a free-form key => { project_role_name, project_id }. Empty until step 4.1. Appended by runbooks/sandbox-lake.md W and REMOVED by R - an entry outliving its project is the finding, not the record. The role arrives as a NAME, never an ARN: the ARN carries the account id, this table lives in a TRACKED file, and aws/INDEX.md rule 1 forbids the copy - iam.tf builds the ARN from the account this slice already reads."
  type = map(object({
    project_role_name = string
    project_id        = string
  }))

  default = {
    # Stage 16 step 4.1, wired 2026-08-26: the Stage 6 test project, the same one the 2026-08-24
    # s3-read-write work vended (its SMUS-born location is the other register entry). The name
    # embeds the project id; the validation below holds the pair consistent.
    "avhvbqn37ty7m8" = {
      project_role_name = "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"
      project_id        = "avhvbqn37ty7m8"
    }
  }

  validation {
    condition     = alltrue([for p in values(var.wired_projects) : startswith(p.project_role_name, "datazone_usr_role_")])
    error_message = "project_role_name must be a datazone_usr_role_* role NAME (not an ARN) - the project USER role the portal shows on the project overview page."
  }

  validation {
    condition     = alltrue([for p in values(var.wired_projects) : strcontains(p.project_role_name, p.project_id)])
    error_message = "the role name must embed the project id (datazone_usr_role_<project>_<suffix>) - a mismatched pair is a copy error from the portal page."
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
