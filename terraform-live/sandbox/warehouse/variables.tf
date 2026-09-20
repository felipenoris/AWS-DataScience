# Inputs. region, env, environment_tag and account_folder arrive from the generated, untracked
# terraform.auto.tfvars (./scripts/gen-tfvars.py sandbox warehouse). Everything else below is this
# slice's own, and each one carries a decision from Stage 5b or 6h.

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

variable "account_folder" {
  description = "The terraform-live/ folder this slice lives in - the first segment of every state key it reads. No .tf file may re-derive it from the env token (Lesson 14)."
  type        = string
  nullable    = false
}

# --------------------------------------------------------------- the class container (5b 2.1)
#
# A Redshift `database` is the CLASS CONTAINER, one per class per account: `sandbox` here and
# `governed` in Production. A Redshift `schema` is what objectives.md calls a base, and its name is
# thematic - chosen after the data it holds, with no necessary relation to any SageMaker project -
# so A SCHEMA NAME CARRIES NO AUTHORIZATION INFORMATION AT ALL and no check can read a class or a
# tenant off it (Lesson 29, read backwards: an attribute deliberately carrying no meaning cannot
# become a selector).
#
# The value below is NOT the class container. It is the namespace's FIRST database, which Redshift
# creates whether one is wanted or not - the service default is `dev` - and a database nobody named
# is a database nobody revoked PUBLIC on. `sandbox` itself is created by 6h 1.1, in SQL, because a
# second database is not a namespace attribute.
variable "first_database" {
  description = "The namespace's inert first database. Redshift creates one at birth (default `dev`); naming it is what makes the REVOKE of 5b 1.6 a step somebody can perform. The class container `sandbox` is created in SQL by Stage 6h 1.1, not here."
  type        = string
  default     = "warehouse"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{0,63}$", var.first_database))
    error_message = "a Redshift database name is 1-64 lowercase alphanumeric characters starting with a letter (AWS naming constraints, read 2026-09-20)."
  }
}

variable "admin_username" {
  description = "The namespace admin's database user name - a NAME, never a person (the identity seam: nothing whose count grows with headcount is in Terraform). Its password is Redshift-managed in Secrets Manager and appears nowhere in this state."
  type        = string
  # `dbadmin` and not `whadmin`, and the reason is a residual rather than a preference (2026-09-20).
  # Redshift derives the managed secret's name as `redshift!<namespace>-<username>`, and a
  # CreateNamespace that fails AFTER the secret is created ROLLS THE NAMESPACE BACK AND LEAVES THE
  # SECRET: the first apply here failed on the data key, left
  # `redshift!awsds-sandbox-warehouse-whadmin` behind - service-owned, rotation enabled, tagged with
  # a namespace ARN that no longer exists - and the next attempt failed with `Unable to create secret
  # for the dbInstance because a secret with a matching name exists`. The namespace name is a
  # contract (three log-group paths derive from it), so the username is the segment that moved.
  # AWS_STATE.md carries the orphan as a dated residual.
  default = "dbadmin"

  validation {
    condition     = can(regex("^[a-z][a-z0-9]{0,127}$", var.admin_username))
    error_message = "an admin user name is 1-128 lowercase alphanumeric characters starting with a letter, and no underscore: AWS's naming table says `alphanumeric` and the apply is the only validator (read 2026-09-20)."
  }
}

# ------------------------------------------------------------------- the audit trail (5b 1.2)
variable "log_retention_days" {
  description = "Retention on the three audit log groups. 30 days in Sandbox (5b decision 4): useractivitylog carries SQL TEXT and therefore literal data values, so a longer period is a growing store nobody has scoped - Stage 11 step 5.1 decides the export and the real period together with the proxy's access log."
  type        = number
  default     = 30
}

# ------------------------------------------------------------------ the cost ceiling (5b 1.3)
#
# Read by BOTH slices: this one declares the numbers and sandbox/warehouse-compute/ reads them from
# this slice's state. One authored place, two consumers - Lesson 33's shape, avoided by not giving
# the compute slice its own copy.
variable "base_capacity" {
  description = "Base RPUs. 4 is the documented floor (D40) and the service default is 128. AWS: `Once you scale your data warehouse beyond 4 RPUs, your data warehouse will continue to use more RPUs, and Amazon Redshift won't scale your data warehouse back down to 4 RPUs` - the ratchet, which no IAM condition key can prevent and only the ComputeCapacity alarm can see."
  type        = number
  default     = 4

  validation {
    condition     = var.base_capacity == 4 || (var.base_capacity >= 8 && var.base_capacity % 8 == 0)
    error_message = "base capacity is 4, or a multiple of 8 at or above 8 (AWS, `Compute capacity for Amazon Redshift Serverless`, read 2026-09-20). A value in between is refused by the service, at apply."
  }
}

variable "max_capacity" {
  description = "The ceiling RPUs the service may scale to (5b decision 2: 8, one step up from the floor). AWS: `Max capacity and Max RPU-hours are the controls to limit the maximum RPUs ... Amazon Redshift Serverless always honors and enforces these settings, regardless of the price-performance target setting`. At 8 the worst hourly rate is 2.88 USD/h rather than whatever the service chooses."
  type        = number
  default     = 8
}

# 10 SINCE 2026-09-20, LOWERED BY THE USER AFTER THE FIRST RUNAWAY, and the reason it moved is the
# only kind worth moving a limit for: a measurement. It was 40 - ten hours of query time, 14.40
# USD/month, argued as 29% of the D12 ceiling on the assumption that query time is scarce in a lab.
# Then one forgotten statement ran 6 h 33 min at base capacity and reached **26.3 RPU-hours in an
# afternoon**, two thirds of the way to a ceiling that was supposed to be generous. The limit was the
# only guard that would have stopped it (max_query_execution_time did not, and make status read
# 0.0000 USD/h throughout), and at 40 it would have let 14.40 USD through first.
#
# WHY A LOW LIMIT IS CHEAP HERE: `breach_action = deactivate`, so breaching costs an INTERRUPTION and
# not money, and recovery is immediate on raising the amount - measured at Stage 5b 5.2, no wait for
# the period to roll over. So the cost of setting this too low is one `update-usage-limit` by somebody
# holding InfrastructureAccess, and the cost of setting it too high is the bill above.
#
# 10 RPU-hours is 2.5 hours of query time at base capacity = 3.60 USD/month, 7% of the D12 ceiling.
# Raise it when a real workload has a number, not before.
#
# THE COUNTER IS PER USAGE LIMIT, not per month or per namespace (measured 2026-09-20): the limit
# destroyed at 1.9 reports `UsageLimitConsumed` 0.0 while its successor reports 28.0 over the same
# namespace. So a limit created by the next `make up` starts near zero even though this month has
# already seen 26.3 RPU-hours - which is what makes lowering it now safe rather than a warehouse that
# is born deactivated. If that reading is wrong, the symptom is a workgroup refusing compute at the
# first query, and the remedy is the same one `update-usage-limit` gives.
variable "usage_limit_rpu_hours" {
  description = "The hard ceiling, in RPU-hours per period, with breach_action = deactivate. 10 RPU-hours = 2.5 hours of query time at 4 RPUs = 3.60 USD/month, 7% of the D12 ceiling. Lowered from 40 by the user on 2026-09-20, after a single forgotten query reached 26.3 RPU-hours in one sitting."
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

variable "max_query_execution_time" {
  description = "The per-query ceiling in seconds - the counterpart of the Athena scan limit (Stage 9 1.2 sets that one). 1800 bounds one runaway query at 0.72 USD of compute at 4 RPUs. The service maximum is 86,399 seconds (24h), which is also what a query with no limit gets."
  type        = number
  default     = 1800

  validation {
    condition     = var.max_query_execution_time > 0 && var.max_query_execution_time <= 86399
    error_message = "valid range is 1-86399 seconds; 86,399 is the service's own `Timeout for a running query` quota (read 2026-09-20)."
  }
}

variable "storage_alarm_usd" {
  description = "The DataStorage alarm's threshold, expressed in USD/month and converted to MB here (6h decision 7). The metric is in MEGABYTES with dimension {Namespace}, and storage is 0.024 USD/GB-month - so a threshold in bytes would go stale the day the price moves, while a threshold in dollars is the thing being defended. 10 USD/month is 417 GB, well under one 1 TB schema quota, so the alarm fires long before a single schema can fill."
  type        = number
  default     = 10
}

# ------------------------------------------------- the admitted projects (5b 2.2, 6h 2.1/2.2)
#
# ONE MAP, THREE CONSUMERS, WHICH IS WHY IT IS A MAP AND NOT THREE LISTS. Each entry expands to:
#
#   layer 1  the tag AmazonDataZoneProject=<projectId> on BOTH the workgroup and the namespace -
#            AWS names both objects, and a value that must appear in N places by hand will be
#            missing from one (Lesson 14). The namespace half is written here; the workgroup half
#            is written by sandbox/warehouse-compute/, which READS THIS MAP FROM THIS SLICE'S
#            STATE rather than declaring its own copy.
#   layer 2  one IAM policy attached to the project's role: GetCredentials and the three reads,
#            resource-scoped to this workgroup's ARN.
#   the door one ingress rule on the workgroup's security group, 5439/tcp from the project's own
#            security group - not a CIDR, and not the whole private tier.
#
# Layer 3 - the GRANT on a schema - is NOT here and cannot be: it is SQL in the namespace, and
# removing a project from this map revokes layers 1 and 2 at the next apply and leaves its role
# membership forever (6h 6.1's unwiring half, WH-12's whole reason to exist).
#
# BOTH NAMES IN THE VALUE ARE THE SERVICE'S, not ours: SageMaker Unified Studio mints
# `datazone_usr_role_<project>_<environment>` and `datazone-<project>-<environment>` when a project
# is created in the portal. So this map is written by hand AFTER the project exists, exactly as
# sandbox/bedrock/'s project_roles is, and for the same reason (Stage 6e decision 8).
#
# EMPTY IS LEGAL AND IT IS THE STATE PASS 1 APPLIES IN. A warehouse with no admitted project has
# no ingress rule, no project tag and no attached policy - which is what makes 6h verification (vi)
# readable at all: the before is a measurement, not an assumption.
variable "projects" {
  description = "The SMUS projects admitted to this warehouse, keyed by project id. Empty admits nobody. Each value names the two service-minted objects the project is reached by."
  type = map(object({
    role_name           = string
    security_group_name = string
  }))
  default = {}

  validation {
    condition     = alltrue([for id in keys(var.projects) : can(regex("^[a-z0-9]+$", id))])
    error_message = "a project id is the portal's own lowercase alphanumeric id, as it appears in the URL - never a project NAME, which is not what the AmazonDataZoneProject tag is read against."
  }

  # AT MOST ONE, AND THE LIMIT IS AWS'S RATHER THAN THIS DESIGN'S (read 2026-09-20, AWS "Gaining
  # access to Amazon Redshift resources"). The admin "adds 1 of the following tags": either
  # `AmazonDataZoneProject={{projectID}}`, which names ONE project, or
  # `for-use-with-all-datazone-projects=true`, which names EVERY project in the account. There is
  # no per-project list, because `AmazonDataZoneProject` is a tag KEY and a key holds one value -
  # on the workgroup and on the namespace alike.
  #
  # So Stage 5b 2.2's "one tag per admitted project" is not expressible, and the requirement that
  # one sandbox schema may be SHARED by several projects meets that wall at the second project, not
  # the first. What is NOT affected: layer 2 (one IAM policy per project role, resource-scoped) and
  # layer 3 (a database role per schema, granted per project) are both genuinely per project and
  # many-to-many. Only the compute-admission gate is single-valued.
  #
  # The validation is here rather than in a comment because the failure it prevents is unreadable:
  # a second entry would silently overwrite the first project's tag, the first project's connection
  # would stop working, and nothing in the plan output would say which project lost its access.
  # 6h decision 8 is where the second project is admitted deliberately, with the wide tag's cost
  # accepted or rejected in writing.
  validation {
    condition     = length(var.projects) <= 1
    error_message = "at most one project: `AmazonDataZoneProject` is a single-valued tag key on both the workgroup and the namespace, and AWS's only way to admit more than one is the wide `for-use-with-all-datazone-projects=true`, refused here (5b 2.2). Admitting a second project is 6h decision 8, not a second map entry."
  }

  validation {
    condition = alltrue([
      for id, p in var.projects : can(regex("^datazone_usr_role_${id}_[a-z0-9]+$", p.role_name))
    ])
    error_message = "role_name is `datazone_usr_role_<projectId>_<environmentId>` and its project segment must equal the map key. A mismatch would grant one project's role under another's tag - the two halves of layer 1 and layer 2 pointing at different projects, which is exactly what one map is here to prevent."
  }

  validation {
    condition = alltrue([
      for id, p in var.projects : can(regex("^datazone-${id}-[a-z0-9-]+$", p.security_group_name))
    ])
    error_message = "security_group_name is `datazone-<projectId>-<environmentName>`, the group SMUS creates for the project's app ENIs, and its project segment must equal the map key."
  }
}

# ------------------------------------------------------------------- the wide tag, refused (5b 2.2)
#
# AWS offers `for-use-with-all-datazone-projects=true`, "to allow all Amazon SageMaker Unified
# Studio projects in this account to access it". It appears nowhere in this repository and
# ./aws/warehouse.py WH-7 fails if it appears on either object: it is the same shape as an empty
# deny-list permitting everything, and it turns "per project" into "per account" with one tag.
# There is no variable for it on purpose - a knob whose only safe value is off is better absent.

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
  default     = "stage-05b"
}
