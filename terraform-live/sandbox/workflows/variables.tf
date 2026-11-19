# Inputs. region, env, environment_tag, deploy_role_name and deploy_runner arrive from the generated,
# untracked terraform.auto.tfvars (./scripts/gen-tfvars.py <account> workflows). project_roles,
# model_applications and datazone_domain_id are this slice's own, edited by hand once per project,
# application or domain.

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
  description = "The SMUS project roles whose workflows run SageMaker or Glue jobs, by role NAME (not ARN). One entry per project; empty is legal and attaches nothing."
  type        = list(string)

  # One entry per project, each read from `iam list-roles`:
  # - eighth-experimentation, created 2026-08-22 (Stage 6a pass 3), where Stage 19 pass 1 ran; read
  #   2026-10-10.
  # - test-experimentation, created 2026-10-15, D41's `test` stage until Stage 19 decision 19 (c)
  #   retired that stage (2026-11-11); read 2026-10-16.
  # - app-etl-dev, created 2026-11-14, the project for app-etl alone and the manifest's `dev` stage
  #   (Stage 19 decision 18 (d), step 1.5); read 2026-11-14.
  # - app-dbt-dev, created 2026-11-19, the project for app-dbt alone and its manifest's `dev` stage
  #   (Stage 20 step 2.0); read 2026-11-19.
  # - app-ml-dev, created 2026-11-19, the project for app-ml alone and its manifest's `dev` stage
  #   (Stage 17 step 9.6); read 2026-11-19.
  # - app-genai-dev, created 2026-11-19, the project for app-genai alone and its manifest's `dev`
  #   stage (Stage 17 step 10.4); read 2026-11-19.
  default = [
    "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c",
    "datazone_usr_role_4gqfau9xuo6e4w_bi356s1sacz0cw",
    "datazone_usr_role_ceweti7jbiu1hs_6kvndq6t2757rk",
    "datazone_usr_role_dnl3l158mbhrio_55hp9teamegf4g",
    "datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk",
    "datazone_usr_role_b8fz4ovppjijv4_c9sdti5d2gaqs0",
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

# The training pair reaches every role in project_roles, and Stage 17's 2.2 reads the tag gap on a
# notebook's training job in eighth-experimentation, which the pair closes. The switch is turned true
# after 2.2's readings (a) and (b), by -var on the plan of that sitting and in the default by the
# sitting's records (Stage 17 step 9.5).
variable "training_pair_enabled" {
  description = "Stage 17 step 9.5: true adds DescribeATrainingJobNoProjectHolds and TagATrainingJobWithTheCallersProject to the policy every listed role carries. false until Stage 17's 2.2 has read (a) and (b)."
  type        = bool
  default     = false
  nullable    = false
}

# An application whose `dev` project trains a model (Stage 17 pass 9): its register task proposes a
# version in its own group, and the bundle role reads the candidate its publish task writes. The group
# and the prefix are the manifest's `dev` MODEL_PACKAGE_GROUP and MODEL_PREFIX.
variable "model_applications" {
  description = "Each application whose dev project trains a model, keyed by application name: the dev project's role, the model package group its register task proposes versions in, and the prefix under the project's shared location its publish task writes the candidate to."
  type = map(object({
    project_role        = string
    model_package_group = string
    model_prefix        = string
  }))

  # app-ml, examples/app-ml/manifest.yaml's `dev` stage, in app-ml-dev (Stage 17 step 9.6).
  default = {
    "app-ml" = {
      project_role        = "datazone_usr_role_5rzplmk81vma34_5ae0dd6m1suvbk"
      model_package_group = "app-ml-dev"
      model_prefix        = "app-ml/models/latest"
    }
  }

  validation {
    condition     = alltrue([for m in values(var.model_applications) : contains(var.project_roles, m.project_role)])
    error_message = "each project_role is an entry of project_roles: the slice reads the role's project id from it."
  }

  validation {
    condition     = alltrue([for app in keys(var.model_applications) : can(regex("^[a-z0-9]+(-[a-z0-9]+)*$", app))])
    error_message = "an application name is lowercase letters and digits joined by single hyphens, as the manifest's applicationName."
  }

  validation {
    condition     = alltrue([for m in values(var.model_applications) : can(regex("^[a-zA-Z0-9](-*[a-zA-Z0-9]){0,62}$", m.model_package_group))])
    error_message = "a model package group name is SageMaker's: letters, digits and hyphens, no `*` or `/`, which would widen the statement past one group."
  }

  validation {
    condition     = alltrue([for m in values(var.model_applications) : can(regex("^[a-z0-9][a-z0-9_-]*(/[a-z0-9][a-z0-9_-]*)*$", m.model_prefix))])
    error_message = "a model prefix is path segments of lowercase letters, digits, `_` and `-`, with no leading or trailing `/` and no `*`, which would widen the bundle role's read past it."
  }
}

# There is no Terraform data source for a DataZone domain, so the id is written by hand after the
# domain exists, as sandbox/warehouse/'s is: the workflows grant and the bundle role name the domain
# by it.
variable "datazone_domain_id" {
  description = "The SMUS domain the projects belong to. Read from `datazone list-domains`; the bundle role's GetDomain names it."
  type        = string

  # `awsds-studio`, AVAILABLE, read from `datazone list-domains` on 2026-09-21.
  default = "dzd-d8yrvx1ko7im6o"

  validation {
    condition     = can(regex("^dzd-[a-z0-9]+$", var.datazone_domain_id))
    error_message = "a SMUS domain id is `dzd-` followed by lowercase alphanumerics, as `datazone list-domains` prints it."
  }
}

# The deploy credential layer's second role in this account (Stage 8 decision 19; the bundle role
# since Stage 19 decision 19 (c)), generated from DEPLOY_ROLES_BY_SLICE in scripts/tfhygiene/backend.py
# (the tfvars of this slice).
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
