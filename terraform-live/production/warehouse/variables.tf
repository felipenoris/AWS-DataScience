# Inputs. region, env, environment_tag and account_folder arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py production warehouse). Everything else below is
# this slice's own, each value a decision of Stage 5b, 6h or 9, copied from sandbox/warehouse/
# (Stage 9 step 9.1: the Sandbox code as built is the specification).

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
    condition     = var.env == "prod"
    error_message = "env must be prod: the governed class of database lives in Production alone (D40, D22), and this slice reads production/workloads/, which no other account folder holds."
  }
}

variable "environment_tag" {
  description = "The Environment tag value - the third vocabulary."
  type        = string
  nullable    = false

  validation {
    condition     = var.environment_tag == "production"
    error_message = "environment_tag must be production."
  }
}

variable "account_folder" {
  description = "The terraform-live/ folder this slice lives in - the first segment of every state key it reads. No .tf file may re-derive it from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

# --------------------------------------------------------------- the class container (5b 2.1)
#
# A Redshift `database` is the class container, one per class per account: `governed` here and
# `sandbox` in Sandbox. A Redshift `schema` is what objectives.md calls a base, and its name is
# thematic, with no necessary relation to any SageMaker project, so a schema name carries no
# authorization information and no check reads a class or a tenant off it.
#
# The value below is not the class container. It is the namespace's first database, which Redshift
# creates at birth (the service default is `dev`); naming it is what makes the REVOKE of 5b 1.6 a
# step somebody can perform. `governed` itself is created in SQL by Stage 9 step 9.3, as 6h 1.1
# created `sandbox`, because a second database is not a namespace attribute.
variable "first_database" {
  description = "The namespace's inert first database. Redshift creates one at birth (default `dev`); naming it is what makes the REVOKE of 5b 1.6 a step somebody can perform. The class container `governed` is created in SQL by Stage 9 step 9.3, not here."
  type        = string
  default     = "warehouse"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{0,63}$", var.first_database))
    error_message = "a Redshift database name is 1-64 lowercase alphanumeric characters starting with a letter (AWS naming constraints, read 2026-09-20)."
  }
}

variable "admin_username" {
  description = "The namespace admin's database user name - a name, never a person (the identity seam). Its password is Redshift-managed in Secrets Manager and appears nowhere in this state. `dbadmin`, the name Sandbox uses: the managed secret is named `redshift!<namespace>-<username>`, and a CreateNamespace that fails after the secret is created leaves the secret behind (EXC-12), so the name is kept identical across the estate and the retry after such a failure moves it."
  type        = string
  default     = "dbadmin"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{0,127}$", var.admin_username))
    error_message = "an admin user name is 1-128 lowercase alphanumeric characters starting with a letter, and no underscore: AWS's naming table says `alphanumeric` and the apply is the only validator (read 2026-09-20)."
  }
}

# ------------------------------------------------------------------- the audit trail (5b 1.2)
variable "log_retention_days" {
  description = "Retention on the three audit log groups: 30 days, Sandbox's value (Stage 9 decision 8). useractivitylog carries SQL text, which in Production carries governed values, so a longer period is a growing store nobody has scoped; Stage 11 step 5.1 decides the export and the real period."
  type        = number
  default     = 30
}

# ------------------------------------------------------------------ the cost ceiling (5b 1.3)
#
# Read by both slices: this one declares the numbers and production/warehouse-compute/ reads them
# from this slice's state. One authored place, two consumers (Lesson 33).
variable "base_capacity" {
  description = "Base RPUs. 4 is the documented floor (D40) and the service default is 128. AWS: once the warehouse scales beyond 4 RPUs it never scales back down to 4 - the ratchet, which no IAM condition key prevents and only the ComputeCapacity alarm sees."
  type        = number
  default     = 4

  validation {
    condition     = var.base_capacity == 4 || (var.base_capacity >= 8 && var.base_capacity % 8 == 0)
    error_message = "base capacity is 4, or a multiple of 8 at or above 8 (AWS, `Compute capacity for Amazon Redshift Serverless`, read 2026-09-20). A value in between is refused by the service, at apply."
  }
}

variable "max_capacity" {
  description = "The ceiling RPUs the service may scale to (5b decision 2: 8, one step up from the floor). AWS honours max capacity and the usage limit whatever the price-performance target says. At 8 the worst hourly rate is 2.88 USD/h."
  type        = number
  default     = 8
}

# 10 RPU-hours, Sandbox's figure, taken for this account by Stage 9 decision 7 (2026-10-22). It is
# 2.5 hours of query time at base capacity, 3.60 USD a month, 7% of the D12 ceiling. Sandbox's
# argument for a low limit holds here: `breach_action = deactivate`, so a breach costs an interruption
# and not money, recovery is immediate on raising the amount (measured at 5b 5.2), and the one
# runaway the estate has seen reached 26.3 RPU-hours in an afternoon (5b log, 2026-09-20). The counter
# belongs to the usage-limit object (measured 2026-09-20), so each `make up` starts it near zero, and
# "monthly" bounds one workgroup's life.
variable "usage_limit_rpu_hours" {
  description = "The hard ceiling, in RPU-hours per period, with breach_action = deactivate (Stage 9 decision 7): 10 RPU-hours = 2.5 hours of query time at 4 RPUs = 3.60 USD/month."
  type        = number
  default     = 10
}

variable "usage_limit_period" {
  description = "The period the limit resets on. `monthly` matches D12's budget window, so a breach and the budget speak about the same month."
  type        = string
  default     = "monthly"

  validation {
    condition     = contains(["daily", "weekly", "monthly"], var.usage_limit_period)
    error_message = "period is daily, weekly or monthly (Redshift Serverless CreateUsageLimit)."
  }
}

# Set and not relied on (Stage 9 step 9.1): in Sandbox a query ran 23,601 s against a 1,800 s
# ceiling, for a reason still open (sandbox/warehouse-compute/main.tf lists the three candidates and
# the test that separates them). The unit is seconds: the service maximum is 86,399 (24 hours).
# 120 s bounds one query at 4 RPU x 120 s = 0.048 USD if the parameter binds at all. What a 2-minute
# ceiling can abort when it does bind: VACUUM on a large table, a first COPY, an aggregation over a
# real table. The governed schema's load job (9.4) is the first demander with a number, and raising
# this is one variable and one apply with a named requester.
variable "max_query_execution_time" {
  description = "The per-query ceiling in seconds, Sandbox's 120. Whether the parameter is enforced at all is not settled (sandbox/warehouse-compute/main.tf); the usage limit and `make down` are what is relied on."
  type        = number
  default     = 120

  validation {
    condition     = var.max_query_execution_time > 0 && var.max_query_execution_time <= 86399
    error_message = "valid range is 1-86399 seconds; 86,399 is the service's own `Timeout for a running query` quota (read 2026-09-20)."
  }
}

variable "storage_alarm_usd" {
  description = "The DataStorage alarm's threshold, in USD/month, converted to MB in data.tf (6h decision 7). The metric is in megabytes with dimension {Namespace}, and storage is 0.024 USD/GB-month, so a threshold in dollars is the thing being defended. 10 USD/month is 417 GB, under one 1 TB schema quota, so the alarm fires before a single schema can fill."
  type        = number
  default     = 10
}

# No `projects` map and no `datazone_domain_id` (Stage 9 steps 9.1 and 9.3): D26 keeps a deployment
# target out of the domain, so no SMUS project is admitted to this warehouse, no `AmazonDataZoneProject`
# tag goes on the namespace or the workgroup, no access role exists, and the only ingress rule names
# the job security group. ./aws/warehouse.py WH-7 reads the absence of the tag here as the pass.

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
  default     = "stage-09"
}
