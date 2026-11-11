# This account's deployment project roles. SageMaker Unified Studio mints a role when a project is
# created, `datazone_usr_role_<project>_<environment>`, so the list is written by hand after the
# project exists, as sandbox/workflows/'s is. This file is the account's own: the other files of the
# slice are copies of staging/studio/'s (scripts/check-copies.py).

variable "project_roles" {
  description = "The deployment project's roles, by role NAME (not ARN): each gets the workflows grant and the deny on a person's session. Empty is legal and attaches nothing; the rollback empties it before the project is deleted, so the environment's stack deletes a role that carries only the policies it attached."
  type        = list(string)

  # deploy-production, created 2026-11-11 at 15:30 UTC (Stage 19 step 4.6); read from `iam list-roles`.
  default = ["datazone_usr_role_d7qcazihvr3s7k_59niwej9axztow"]

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}
