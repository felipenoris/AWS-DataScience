# Inputs. region, env, environment_tag, account_folder and producers arrive from the generated,
# untracked terraform.auto.tfvars (./scripts/gen-tfvars.py sandbox warehouse). Everything else below
# is this slice's own, and each one carries a decision from Stage 5b, 6h, 19 or 21.

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

variable "producers" {
  description = "The producer account of the products the access roles read in place (Stage 19 pass 5): production, keyed by account folder with its profile and env token, derived from backend.DATA_PRODUCERS in scripts/tfhygiene/backend.py and never authored here. Only providers.tf's aliased provider reads it, to resolve the account id the catalog ARNs carry."
  type        = map(object({ profile = string, env = string }))
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
# guard meant to stop it (max_query_execution_time did not, and make status read 0.0000 USD/h
# throughout), and at 40 it would have let 14.40 USD through first. Whether a breach stops a statement
# already running is unmeasured: that statement read only catalog tables, ran on the leader node, and
# kept running through the two minutes Stage 5b 5.1 held this limit breached (5b log, 2026-10-18).
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

# 120 SINCE 2026-09-20, LOWERED BY THE USER from 1800 in the same sitting the ceiling was tightened.
# THE UNIT IS SECONDS, settled the same day: the service maximum is "86,399 seconds (24 hours)" (which
# is this validation's ceiling), and the serverless query-queues page reads its own QMR examples as
# "more than 60 seconds" and "more than an hour". `statement_timeout` is the millisecond parameter in
# this family and is not in the Serverless config_parameters list, so the two cannot be confused.
#
# 120 s bounds one query at 4 RPU x 120 s = 0.048 USD, against 0.72 at the 1800 it replaces.
#
# WHAT A 2-MINUTE CEILING CAN ABORT, and it is worth knowing before a legitimate job hits it:
#
#   VACUUM   the only way to reclaim space after a DELETE, and at 4 base RPUs it is the plain form
#            with no vacuum boost. On a large table it takes far longer than two minutes, so if this
#            parameter is enforced at all (see warehouse-compute/main.tf - it is not yet settled that
#            it is), space reclamation becomes impossible until the value is raised.
#   COPY     a first load of any size.
#   an aggregation over a real table, as opposed to the empty schema this warehouse holds today.
#
# NONE OF THOSE HAS A DEMANDER YET, which is what makes 120 the right default now: the warehouse holds
# one empty schema, every query so far has been sub-second except the deliberate runaway, and raising
# it is one variable and one apply with a named requester. The failure it guards against has already
# happened once and cost 9.44 USD.
variable "max_query_execution_time" {
  description = "The per-query ceiling in SECONDS. 120 since 2026-09-20 (was 1800), bounding one query at 0.048 USD of compute at 4 RPUs. The service maximum is 86,399 seconds (24h), which is also what a query with no limit gets. Whether the parameter is enforced at all is not settled - see sandbox/warehouse-compute/main.tf."
  type        = number
  default     = 120

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
# One map for every consumer, which is why it is a map and not a list per consumer. Each entry
# expands to:
#
#   layer 1      the tag AmazonDataZoneProject=<projectId> on both the workgroup and the namespace
#                while the map holds one entry; a map of several is admitted by the wide tag
#                (`all_projects_tag_enabled` below). AWS names both objects, and a value that must
#                appear in N places by hand will be missing from one (Lesson 14). The namespace half
#                is written here; the workgroup half is written by sandbox/warehouse-compute/, which
#                reads this map from this slice's state rather than declaring its own copy.
#   layer 2      one IAM policy, on the project's role and on its access role: GetCredentials,
#                GetWorkgroup and ListTagsForResource on this account's workgroups, and the two
#                listings that take no resource.
#   access role  the role the portal's connection assumes (6h 3.1): trusted by the project's role
#                alone, holding layer 2's policy and the portal's own.
#   the door     one ingress rule on the workgroup's security group, 5439/tcp from the project's own
#                security group - not a CIDR, and not the whole private tier.
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
# no ingress rule, no project tag, no access role and no attached policy - which is what makes 6h
# verification (vi) readable at all: the before is a measurement, not an assumption.
# ------------------------------------------------- the domain the admitted project belongs to
#
# Needed by ONE statement: the access role's trust policy pins the session tag
# `aws:RequestTag/AmazonDataZoneDomain`, so a session tagged with another domain's id cannot be
# minted through it. There is no Terraform data source for a DataZone domain, so the value is
# written by hand after the domain exists - the same shape as `sandbox/bedrock/`'s project role list.
variable "datazone_domain_id" {
  description = "The SMUS domain the admitted projects belong to. Read from `datazone list-domains`; only the access role's trust policy uses it."
  type        = string

  # `awsds-studio`, AVAILABLE, read from `datazone list-domains` on 2026-09-21.
  default = "dzd-d8yrvx1ko7im6o"

  validation {
    condition     = can(regex("^dzd-[a-z0-9]+$", var.datazone_domain_id))
    error_message = "a SMUS domain id is `dzd-` followed by lowercase alphanumerics, as `datazone list-domains` prints it."
  }
}

variable "projects" {
  description = "The SMUS projects admitted to this warehouse, keyed by project id. Empty admits nobody. Each value names the two service-minted objects the project is reached by."
  type = map(object({
    role_name           = string
    security_group_name = string
  }))
  # The experimentation project `eighth-experimentation`, admitted 2026-09-21. Both ids in the role
  # name are the service's - `avhvbqn37ty7m8` the project, `5hkjdsy3umpi1c` the environment - and
  # every value here is read from the API rather than the portal's page (Lesson 38):
  # `datazone list-projects` for the key, `iam list-roles` for the role, `describe-security-groups`
  # for the group. The same project holds `sandbox/bedrock/`'s grant, so the role name is one string
  # two slices carry.
  #
  # The group and the workgroup share `vpc-00dca74a35159b11c`, which is what makes the `5439` rule
  # below reachable at all: AWS serves JupyterLab's query path only when the Redshift resource and
  # the project sit in one VPC. The project's Data page needs no such thing.
  default = {
    avhvbqn37ty7m8 = {
      role_name           = "datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c"
      security_group_name = "datazone-avhvbqn37ty7m8-dev"
    }
  }

  validation {
    condition     = alltrue([for id in keys(var.projects) : can(regex("^[a-z0-9]+$", id))])
    error_message = "a project id is the portal's own lowercase alphanumeric id, as it appears in the URL - never a project NAME, which is not what the AmazonDataZoneProject tag is read against."
  }

  # At most one entry while `all_projects_tag_enabled` is false, and the limit is AWS's (read
  # 2026-09-20, AWS "Gaining access to Amazon Redshift resources"). The admin "adds 1 of the
  # following tags": `AmazonDataZoneProject={{projectID}}`, which names one project, or
  # `for-use-with-all-datazone-projects=true`, which names every project in the account. A tag key
  # holds one value, on the workgroup and on the namespace alike, so the project tag is written only
  # while the map holds exactly one entry (main.tf).
  #
  # A second entry therefore needs the wide tag (6h decision 8 (a), taken 2026-11-17). Under it every
  # project role in the account reaches the compute through AWS's SageMakerStudioProjectUserRolePolicy
  # (`ExistingRedshiftCompute`, simulated 2026-10-18), each entry's access role is the per-project
  # gate on the Data page, and the schema GRANT of layer 3 is the only per-project gate on the
  # notebook and Data API doors. Without the wide tag, a second entry would leave both objects with no
  # admission tag and every admitted project's connection would stop with nothing in the plan to say
  # why, which is the failure this validation turns into a plan error.
  validation {
    condition     = var.all_projects_tag_enabled || length(var.projects) <= 1
    error_message = "at most one project while all_projects_tag_enabled is false: `AmazonDataZoneProject` is a single-valued tag key on both the workgroup and the namespace, and AWS admits more than one project only through `for-use-with-all-datazone-projects=true` (6h decision 8 (a)), which all_projects_tag_enabled = true writes."
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

# ------------------------------------------------------------ the wide tag (6h decision 8 (a))
#
# `for-use-with-all-datazone-projects=true`, AWS's tag "to allow all Amazon SageMaker Unified Studio
# projects in this account to access it". True puts it on the namespace here and, through the
# `all_projects_tag` output, on the workgroup at sandbox/warehouse-compute/'s next apply, and lets
# `projects` hold more than one entry. ./aws/warehouse.py WH-7 then expects it on both objects and
# neither tag on the admin secret: the same AWS policy grants GetSecretValue on any secret wearing
# it (`DataConnectionAllProjectResources`, AWS_STATE.md INV-20).
variable "all_projects_tag_enabled" {
  description = "6h decision 8 (a): true writes `for-use-with-all-datazone-projects=true` on the namespace and, through this slice's state, on the workgroup, admitting every SMUS project in the account to the compute, and lets `projects` hold more than one entry. false admits the map's one project by `AmazonDataZoneProject` alone."
  type        = bool
  default     = false
  nullable    = false
}

# ------------------------------------------------- the data transfer role (Stage 21 step 4.5)
variable "data_transfer_role_enabled" {
  description = "Stage 21 decision 3 (b), for one sitting: true creates the data transfer role that data lake access on the federated catalog names (`DataLakeAccessProperties.DataTransferRole`, iam.tf). The update-catalog call that sets it is a command of the sitting. false between sittings."
  type        = bool
  default     = false
  nullable    = false
}

variable "federated_catalog_name" {
  description = "The federated catalog Stage 21 step 4.1 registers this namespace as: the one catalog besides the account's own that the data transfer role reads."
  type        = string
  default     = "stage21_warehouse"
  nullable    = false

  validation {
    condition     = can(regex("^[a-z0-9_-]+$", var.federated_catalog_name))
    error_message = "a catalog name of lowercase letters, digits, `_` and `-`: the data transfer role's Glue resources embed it, and a `*` or a `/` would widen them past one catalog."
  }
}

# ---------------------------------------------- the subscribed products (Stage 19 pass 5)
#
# A product a project subscribes to in the portal and reads in place through the warehouse. DataZone
# fulfils the subscription with a resource link in the subscription target's Glue database in this
# account, and Redshift resolves the link and calls Glue and Lake Formation as the access role, the
# session's IAM principal (runbook redshift-connection.md §G). Each entry adds the identity half of
# that read to the project's access role (iam.tf); Lake Formation's admission is DataZone's grant or
# Stage 19 step 5.1's, never this map.
#
# Written by hand, as `projects` is: the database is the service's, named after the project's
# environment, and the producer's table is the product's asset.
variable "subscribed_products" {
  description = "Per admitted project, keyed by project id: the products it reads in place from the producer account. Each entry names the subscription target's Glue database in this account, which holds DataZone's resource links, and the producer's database and table a link targets. Empty, or a project absent, adds nothing to that project's access role."
  type = map(list(object({
    link_database     = string
    producer_database = string
    producer_table    = string
  })))

  # `eighth-experimentation`'s subscription to Production's `trades_notional` (Stage 19 step 4.12),
  # written before the request exists, from values read 2026-11-19: the subscription target is the
  # project's `DataLake` environment `blerpkhn9nj7o0`, whose database `glue_db_blerpkhn9nj7o0` holds
  # the project's resource links, and the product's asset is `app_etl.trades_notional`, an Iceberg
  # table with no partition keys whose location Lake Formation holds in Lake Formation mode.
  default = {
    avhvbqn37ty7m8 = [{
      link_database     = "glue_db_blerpkhn9nj7o0"
      producer_database = "app_etl"
      producer_table    = "trades_notional"
    }]
  }

  validation {
    condition     = alltrue([for id in keys(var.subscribed_products) : contains(keys(var.projects), id)])
    error_message = "every key of subscribed_products is a key of projects: only `projects` creates an access role, so an entry for a project absent from it grants nothing and reads as a grant that exists. A project leaves both maps in the same edit."
  }

  validation {
    condition = alltrue(flatten([
      for products in values(var.subscribed_products) : [
        for p in products : [
          for name in [p.link_database, p.producer_database, p.producer_table] : can(regex("^[a-z0-9_]+$", name))
        ]
      ]
    ]))
    error_message = "a Glue database or table name of lowercase letters, digits and `_`: the access role's ARNs embed each one, and a `*` or a `/` would widen the read past one database or table."
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
  default     = "stage-05b"
}
