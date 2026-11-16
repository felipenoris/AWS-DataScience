# This account's deployment project roles. SageMaker Unified Studio mints a role when a project is
# created, `datazone_usr_role_<project>_<environment>`, so the list is written by hand after the
# project exists, as sandbox/workflows/'s is. This file and fence.tf are the account's own: the other
# files of the slice are copies of production/studio/'s (scripts/check-copies.py).

variable "project_roles" {
  description = "The deployment project's roles, by role NAME (not ARN): each gets the workflows grant and the deny on a person's session. Empty is legal and attaches nothing; the rollback empties it before the project is deleted, so the environment's stack deletes a role that carries only the policies it attached."
  type        = list(string)

  # deploy-staging, created 2026-11-11 at 15:26 UTC (Stage 19 step 4.6); read from `iam list-roles`.
  default = ["datazone_usr_role_5ido8bej1zoeq8_d6nu5aphq1e974"]

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}

# Whether the workflows grant lets the project role start a data source of the domain (workflows.tf),
# the publishing task's step before it lists the asset (Stage 19 decisions 3 and 17).
variable "publishing_starts_the_source" {
  description = "Whether the project role may start a data source of the domain: true in the one stage whose PUBLISH_LISTING is true."
  type        = bool

  # Staging lists nothing: its PUBLISH_LISTING is false, so its task starts no source.
  default = false
}

# Whether the workflows grant lets the project role create and revise a data product of the domain
# (workflows.tf), the publishing task's step after it lists the asset (Stage 19 decision 26).
variable "publishing_creates_the_data_product" {
  description = "Whether the project role may create and revise a data product of the domain: true in the one stage whose PUBLISH_LISTING is true."
  type        = bool

  # Staging lists nothing, so its task creates no data product.
  default = false
}
