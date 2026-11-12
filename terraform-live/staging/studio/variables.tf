# Inputs. All but project_roles (project-roles.tf) and the fence's lists (fence.tf) arrive from the
# generated, untracked terraform.auto.tfvars (./scripts/gen-tfvars.py <account> studio).

variable "region" {
  description = "AWS region for this slice. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
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
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["sandbox", "development", "data", "staging", "production", "org"], var.environment_tag)
    error_message = "environment_tag must be one of the six tag values in docs/plan/conventions.md."
  }
}

variable "account_folder" {
  description = "This slice's own account folder - the first token of its state key, which no .tf file may re-derive from the env token (Lesson 14). Used for the same-account VPC read."
  type        = string
  nullable    = false
}

variable "vpc_slice" {
  description = "The slice of this account that holds the VPC a project's environments provision into (DATA_CONSUMER_VPC_SLICE in scripts/tfhygiene/backend.py): foundation in Staging, workloads in Production, whose foundation/ is VPC-SharedServices."
  type        = string
  nullable    = false
}

variable "lake" {
  description = "The account that owns the governed lake (DATA_LAKE in scripts/tfhygiene/backend.py) - read for the Lake Formation-registered bucket ARNs the D13 boundary excludes, the drop-box prefix it carves back in, and the lake data key."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "domain" {
  description = "The account that owns the SMUS domain (SMUS_DOMAIN in scripts/tfhygiene/backend.py). Read once the blueprints are enabled, for the domain id the blueprint configurations name."
  type        = map(object({ profile = string, env = string }))
  nullable    = false
}

variable "blueprints_enabled" {
  description = "true once this account's row is in backend.SMUS_ASSOCIATED: the blueprint configurations, their grants and the workflows grant. false plans the prerequisites alone, which make no datazone: call."
  type        = bool
  default     = false
}

variable "blueprint_names" {
  description = "The blueprints a deployment project uses, never the module's default list (Sandbox's): Tooling, which with enableSpaces false in the deployment profile creates no SageMaker AI domain, and DataLake, which creates a project's Glue database, its Lake Formation permissions, its data source and an Athena workgroup."
  type        = list(string)
  default     = ["Tooling", "DataLake"]
}

variable "allowed_instance_types" {
  description = "The ml.* ceiling (D12). null - the default - takes terraform-modules/sagemaker-denies' list, the one the Workloads SCP and the persona sets compose."
  type        = list(string)
  default     = null
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
  default     = "stage-19"
}
