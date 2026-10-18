# Inputs. region, env, environment_tag, deploy_role_name and deploy_runner arrive from the generated,
# untracked terraform.auto.tfvars (./scripts/gen-tfvars.py <account> workflows). project_roles,
# test_project_role and datazone_domain_id are this slice's own, edited by hand once per project or
# domain.

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

variable "env" {
  description = "The <env> name token of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "dev", "data", "staging", "prod", "org"], var.env)
    error_message = "env must be one of the six name tokens in docs/plan/conventions.md."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

# The roles this slice attaches to are minted by SageMaker Unified Studio when a project is created,
# `datazone_usr_role_<project>_<environment>`, so the list is written by hand after the project
# exists, as sandbox/bedrock/'s is. A project missing from it fails at its first processing task,
# with the AccessDeniedException this slice exists to remove.
variable "project_roles" {
  description = "The SMUS project roles whose workflows run SageMaker processing jobs, by role NAME (not ARN). One entry per project; empty is legal and attaches nothing."
  type        = list(string)

  # One entry per project, each read from `iam list-roles`:
  # - eighth-experimentation, created 2026-08-22 (Stage 6a pass 3), D41's `dev` project; read 2026-10-10.
  # - test-experimentation, created 2026-10-15, D41's `test` project, where the CI/CD CLI's deploy of a
  #   release runs its processing task as this role (Stage 8 step 2.5); read 2026-10-16.
  default = [
    "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
    "datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw",
  ]

  validation {
    condition     = alltrue([for r in var.project_roles : can(regex("^datazone_usr_role_[a-z0-9]+_[a-z0-9]+$", r))])
    error_message = "each entry is a SMUS project role name, `datazone_usr_role_<project>_<environment>`."
  }

  validation {
    condition     = length(var.project_roles) == length(distinct(var.project_roles))
    error_message = "a role appears twice. The attachment is keyed by role name, so a duplicate would collide rather than be ignored."
  }
}

# D41's `test` project, which the test deploy role reaches and nobody else's (Stage 8 decision 19):
# written by hand as project_roles is, and read from it.
variable "test_project_role" {
  description = "The project role of D41's `test` project, one of project_roles, by NAME: the role awsds-deploy-sandbox-test passes to the workflow service, and whose project's shared/ prefix, workflows and log groups it reaches."
  type        = string

  # test-experimentation, created 2026-10-15; read 2026-10-16.
  default = "datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw"

  validation {
    condition     = contains(var.project_roles, var.test_project_role)
    error_message = "test_project_role must be one of project_roles: the test project's role holds the workflows grant like every other project's."
  }
}

# There is no Terraform data source for a DataZone domain, so the id is written by hand after the
# domain exists, as sandbox/warehouse/'s is: it names the projects' prefix in the projects bucket and
# the workflows' log groups.
variable "datazone_domain_id" {
  description = "The SMUS domain the projects belong to. Read from `datazone list-domains`; the test deploy role's S3 and log-group scopes use it."
  type        = string

  # `awsds-studio`, AVAILABLE, read from `datazone list-domains` on 2026-09-21.
  default = "dzd-d8yrvx1ko7im6o"

  validation {
    condition     = can(regex("^dzd-[a-z0-9]+$", var.datazone_domain_id))
    error_message = "a SMUS domain id is `dzd-` followed by lowercase alphanumerics, as `datazone list-domains` prints it."
  }
}

# Stage 8 decision 19 - the deploy credential layer's second role in this account, generated from
# DEPLOY_ROLES_BY_SLICE in scripts/tfhygiene/backend.py (the tfvars of this slice).
variable "deploy_role_name" {
  description = "The deploy role this slice builds, awsds-deploy-sandbox-test - a contract with ./aws/cicd.py."
  type        = string
  nullable    = false
}

variable "deploy_runner" {
  description = "The deploy runner's home, keyed by account folder, with the profile the alias in deploy-role.tf resolves its account id from: the trust names awsds-<env>-runner-deploy there."
  type        = map(object({ profile = string, env = string }))
  nullable    = false

  validation {
    condition     = length(var.deploy_runner) == 1
    error_message = "One deploy runner home (D14): the trust names one role in one account."
  }
}

variable "project" {
  description = "Project tag. Fixed by docs/plan/conventions.md and by 1c's tag policy."
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
  default     = "stage-06i"
}
