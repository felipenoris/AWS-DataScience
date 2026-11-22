variable "env" {
  description = "The deployment target's <env> name token: every name below carries it."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["staging", "prod"], var.env)
    error_message = "env is staging or prod: a chain runs in the two deployment targets alone (D17); Sandbox's workflows run in its projects and no schedule starts them."
  }
}

variable "project" {
  description = "The account's deployment project (Stage 19 step 4.6): its name, which the CLI writes into each workflow's name, and the ARN of its key, alias/awsds-<env>-project, under which the CLI creates each workflow."
  type = object({
    name    = string
    key_arn = string
  })
  nullable = false

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]*$", var.project.name))
    error_message = "project.name is the DataZone project's name, as the manifest's stage writes it (deploy-staging, deploy-production)."
  }

  validation {
    condition     = can(regex("^arn:[^:]+:kms:[^:]+:[0-9]{12}:key/[0-9a-f-]+$", var.project.key_arn))
    error_message = "project.key_arn is a KMS key ARN: the encryption context of a workflow binds to the key, never to an alias."
  }
}

variable "applications" {
  description = "The applications the CLI deploys into the project, by the manifest's applicationName, each with the workflows a chain may start, as the manifest's content.workflows names them. The CLI creates a workflow as <application>_<project>_<workflow>, every character outside [A-Za-z0-9_] an underscore."
  type = map(object({
    workflows = list(string)
  }))
  nullable = false

  validation {
    condition     = alltrue([for app, a in var.applications : length(a.workflows) > 0 && length(a.workflows) == length(distinct(a.workflows))])
    error_message = "an application names one workflow at least, and each once."
  }

  validation {
    condition     = alltrue(flatten([for app, a in var.applications : [can(regex("^[a-z0-9][a-z0-9-]*$", app)), [for w in a.workflows : can(regex("^[a-z0-9][a-z0-9-]*$", w))]]]))
    error_message = "an application's name and its workflows' names are lower-case letters, digits and hyphens: each is a key of the stage-variables parameter and of a rule's name."
  }
}

variable "alerts_topic_arn" {
  description = "The account's awsds-<env>-alerts topic (Stage 8 decision 5): the failure rules' target."
  type        = string
  nullable    = false
}

variable "log_key_arn" {
  description = "The key of the state machines' log group: the account data CMK (alias/awsds-<env>-data), whose policy admits CloudWatch Logs for the group by name (the data slice's)."
  type        = string
  nullable    = false
}

variable "log_retention_days" {
  description = "Retention of the state machines' log group (D28 item 5)."
  type        = number
  default     = 90
  nullable    = false
}

variable "chains" {
  description = <<-EOT
    One entry per chain (D41 item 5): the state machine, its schedule and its failure rule are
    awsds-<env>-chain-<key>.
      definition_template  the ASL of terraform-live/<env>/chains/definitions/<key>.asl.json (Stage
                           10 decision 14), rendered with env, partition, workflow_name (the
                           composed name of each workflow of the chain's application, by the
                           manifest's name) and stage_variables_parameter
      application          the application whose workflows it starts and whose stage variables it
                           passes to each run
      workflows            the workflows it starts, each one of the application's
      schedule_expression  the Scheduler expression, cron(...) in schedule_timezone
      schedule_enabled     the schedule's state, the pause lever (Stage 10 step 3.5)
  EOT
  type = map(object({
    definition_template = string
    application         = string
    workflows           = list(string)
    schedule_expression = string
    schedule_timezone   = optional(string, "UTC")
    schedule_enabled    = optional(bool, false)
  }))
  default  = {}
  nullable = false

  validation {
    condition     = alltrue([for k, c in var.chains : length(c.workflows) > 0])
    error_message = "a chain starts one workflow at least (Stage 10 decision 13: a chain of one is still a chain)."
  }
}
