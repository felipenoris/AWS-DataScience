variable "env" {
  description = "The deployment target's <env> name token: every name below carries it."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["staging", "prod"], var.env)
    error_message = "env is staging or prod: workflows run in the two deployment targets alone (D17, D41 item 2); Sandbox's run in its projects."
  }
}

variable "vpc_id" {
  description = "The VPC the workers land in: VPC-Workloads in Production, Staging's VPC (Stage 10 step 1.2)."
  type        = string
  nullable    = false
}

variable "subnet_ids" {
  description = "The private subnets, one per AZ, the workers land in. The private-routing shape needs two AZs and no route to a NAT device or an internet gateway (step 1.2)."
  type        = list(string)
  nullable    = false

  validation {
    condition     = length(var.subnet_ids) >= 2
    error_message = "subnet_ids names two subnets in two AZs at least: the private-routing shape's documented minimum (step 1.2)."
  }
}

variable "application_boundary_arn" {
  description = "The application ceiling awsds-<env>-app-boundary (Stage 8 step 3.0). Every role this module creates carries it: the deploy role's ceiling refuses CreateRole and every policy change on a role without it."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:[^:]+:iam::[0-9]{12}:policy/awsds-(staging|prod)-app-boundary$", var.application_boundary_arn))
    error_message = "application_boundary_arn names the policy awsds-<env>-app-boundary, the one DenyRoleChangesOutsideTheApplicationCeiling admits."
  }
}

variable "alerts_topic_arn" {
  description = "The account's awsds-<env>-alerts topic (Stage 8 decision 5): the failure rules' target."
  type        = string
  nullable    = false
}

variable "data_key_arn" {
  description = "The account data CMK's ARN (alias/awsds-<env>-data): the log groups' key, the volume key a SageMaker job carries, and the key of the outputs bucket the roles read and write through S3. Its policy delegates nothing to IAM, so it names this module's roles by aws:PrincipalArn (the data slice's, Stage 9 step 1.1)."
  type        = string
  nullable    = false
}

variable "workflow_encryption" {
  description = "The workflows' EncryptionConfiguration type (Stage 10 decision 2). CUSTOMER_MANAGED_KEY encrypts them with data_key_arn. The type is create-only, so a change replaces every workflow: a new ARN and no run history."
  type        = string
  default     = "CUSTOMER_MANAGED_KEY"
  nullable    = false

  validation {
    condition     = contains(["CUSTOMER_MANAGED_KEY", "AWS_MANAGED_KEY"], var.workflow_encryption)
    error_message = "workflow_encryption is CUSTOMER_MANAGED_KEY or AWS_MANAGED_KEY, the two values AWS::MWAAServerless::Workflow accepts."
  }
}

variable "job_role_arn" {
  description = "Stage 9's awsds-<env>-job-exec (Stage 8 step 2.5, taken 2026-10-22): the role a workflow's SageMaker jobs run as, passed by the execution role to sagemaker.amazonaws.com alone."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:[^:]+:iam::[0-9]{12}:role/awsds-(staging|prod)-job-exec$", var.job_role_arn))
    error_message = "job_role_arn names awsds-<env>-job-exec, Stage 9's [P] job role."
  }
}

variable "outputs_bucket" {
  description = "The account's outputs bucket, awsds-<env>-outputs (Stage 9 step 1.1, Stage 10 decision 17): the definitions home, the result files and the inboxes. Never a lake bucket."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^awsds-(staging|prod)-outputs$", var.outputs_bucket))
    error_message = "outputs_bucket is awsds-<env>-outputs: an execution role reaches no other bucket (D13 one level up, step 1.3)."
  }
}

variable "log_retention_days" {
  description = "Retention of the workflows' and the state machines' log groups (D28 item 5)."
  type        = number
  default     = 90
  nullable    = false
}

variable "workflows" {
  description = <<-EOT
    One entry per workflow, keyed by its short name: the workflow, its execution role and its failure
    rule are awsds-<env>-wf-<key>, its log group /awsds/<env>/wf/<key> (step 1.1).
      definition  the rendered copy the release job wrote (step 2.4), pinned by its S3 VersionId
      code        the worker's code package beside it, pinned the same way, when the workflow has a
                  Python or Bash task (D28 class 2b)
      glue_jobs   the Glue jobs the application slice declares and the workflow starts, by name
      processing_job_prefix / training_job_prefix
                  the job-name prefix of the SageMaker jobs the workflow submits; null when it submits none
      reads, writes, deletes
                  key prefixes of outputs_bucket the role reads, writes and deletes: the processing
                  output a Python task summarizes, the result file and its marker, the inbox markers
                  (D41 item 10; decision 10 for deletes)
  EOT
  type = map(object({
    description = string
    definition = object({
      bucket     = string
      key        = string
      version_id = string
    })
    code = optional(object({
      bucket     = string
      key        = string
      version_id = string
    }))
    glue_jobs             = optional(list(string), [])
    processing_job_prefix = optional(string)
    training_job_prefix   = optional(string)
    reads                 = optional(list(string), [])
    writes                = optional(list(string), [])
    deletes               = optional(list(string), [])
  }))
  nullable = false

  validation {
    condition     = alltrue([for k, w in var.workflows : w.definition.version_id != "" && (w.code == null ? true : w.code.version_id != "")])
    error_message = "every definition and code package is pinned by its S3 VersionId (step 2.4): a workflow saved from an unpinned key runs whatever the key holds at the save."
  }

  validation {
    condition     = alltrue(flatten([for k, w in var.workflows : [for p in concat(w.reads, w.writes, w.deletes) : !startswith(p, "workflows/") && endswith(p, "/")]]))
    error_message = "reads, writes and deletes are prefixes ending in '/' and never under workflows/, which decision 12 keeps for the release job alone."
  }
}

variable "chains" {
  description = <<-EOT
    One entry per chain (D41 item 5): the state machine, its schedule and its failure rule are
    awsds-<env>-chain-<key>.
      definition_template  the ASL of terraform-live/<env>/orchestration/chains/<key>.asl.json
                           (decision 14), rendered with workflow_arn, a map of every workflow's ARN
                           by key
      workflows            the keys of the workflows it starts; every one must be in var.workflows
      schedule_expression  the Scheduler expression, cron(...) in schedule_timezone
      schedule_enabled     the schedule's state, the pause lever (step 3.5)
  EOT
  type = map(object({
    definition_template = string
    workflows           = list(string)
    schedule_expression = string
    schedule_timezone   = optional(string, "UTC")
    schedule_enabled    = optional(bool, true)
  }))
  default  = {}
  nullable = false

  validation {
    condition     = alltrue([for k, c in var.chains : length(c.workflows) > 0])
    error_message = "a chain starts one workflow at least (decision 13: a chain of one is still a chain)."
  }
}

variable "bridges" {
  description = "One entry per inbox bridge (step 3.6, decision 16), keyed by the application whose inbox/<key>/ prefix of outputs_bucket starts the chain it names. The bucket's notification to EventBridge is the data slice's."
  type = map(object({
    chain = string
  }))
  default  = {}
  nullable = false
}

variable "tags" {
  description = "The five mandatory tags (conventions §6). The aws resources take them from the caller's default_tags; awscc_mwaaserverless_workflow takes them here, since awscc reads no default tags."
  type        = map(string)
  nullable    = false

  validation {
    condition     = alltrue([for k in ["Project", "Environment", "ManagedBy", "Owner", "CostCenter"] : contains(keys(var.tags), k)])
    error_message = "tags carries Project, Environment, ManagedBy, Owner and CostCenter (1c's tag policy)."
  }
}
