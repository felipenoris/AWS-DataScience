# production/warehouse-compute/ - the compute half of D40's governed warehouse (Stage 9 step 9),
# layer [E]. Two resources and nothing else: the workgroup and its usage limit.
#
# Why [E] and not [D]: Redshift Serverless has `create-workgroup` and `delete-workgroup` and nothing
# in between, no stop, no suspend, no zero-capacity setting. So "powered off" means "does not exist",
# which is the definition of [E] (conventions 5.1), and an object that does not exist cannot receive a
# query, so none of D40's three ways an idle warehouse bills anyway (an open transaction, a connection
# pool's keep-alive, a cancelled query) has anything to arrive at.
#
# Why the usage limit is in the same slice and the same apply: a workgroup that exists for one plan
# cycle without its ceiling is a workgroup with no ceiling. The two guards are one hard and one soft:
# `make down` removes the compute, and the usage limit bounds it while it exists.
#
# Who raises it: the operator, by hand, before the governed schema's DDL job and `make down` after it
# (step 9.4). `DenyRedshiftCostGuardTamperingExceptInfrastructure` exempts only InfrastructureAccess,
# so awsds-deploy-prod can neither apply nor destroy this slice nor lift a breached limit.
#
# What survives a `make down`: everything in production/warehouse/, the namespace and its data, the
# schemas, the database users, the database roles and every GRANT, the admin secret, the three audit
# log groups, the security group and both alarms. The endpoint host survives a delete and re-create
# under the same name (5b step 1.9's reading in Sandbox), and nothing here stores it as a field: no
# SMUS connection reaches this warehouse (step 9.3).

data "terraform_remote_state" "workloads" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/workloads/terraform.tfstate"
    region = var.region
  }
}

data "terraform_remote_state" "warehouse" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/warehouse/terraform.tfstate"
    region = var.region
  }
}

locals {
  name      = "awsds-${var.env}-warehouse"
  namespace = data.terraform_remote_state.warehouse.outputs.namespace_name
  capacity  = data.terraform_remote_state.warehouse.outputs.capacity

  # The two private subnets of VPC-Workloads, selected by zone id (Stage 9 step 9.1): the subnets
  # the jobs and the MWAA Serverless workers run in, never production/foundation/'s. AWS's
  # considerations page asks for two subnets in two Availability Zones without Enhanced VPC Routing,
  # which is off below; the provider's page says three and its code validates nothing, so the service
  # is the authority and the apply is the reading (Lesson 30). Sandbox applied with two.
  private_subnet_ids = [
    for z in var.zone_ids : data.terraform_remote_state.workloads.outputs.private_subnet_ids[z]
  ]
}

resource "aws_redshiftserverless_workgroup" "this" {
  workgroup_name = local.name
  namespace_name = local.namespace

  base_capacity = local.capacity.base_capacity
  # AWS honours max capacity and the usage limit whatever the price-performance target says. Both are
  # set: this field and the usage limit below.
  max_capacity = local.capacity.max_capacity

  # `subnet_ids` is Optional and Computed, so omitting it plans as unknown and lets the service choose,
  # and the service would choose the default VPC, which no account here has (Lesson 27).
  subnet_ids         = local.private_subnet_ids
  security_group_ids = [data.terraform_remote_state.warehouse.outputs.security_group_id]

  publicly_accessible = false

  # Off, which is what makes two subnets sufficient. Enhanced VPC Routing forces COPY/UNLOAD traffic
  # through the VPC and is the case AWS documents as needing three AZs; nothing here does COPY or
  # UNLOAD, because the namespace role reaches no bucket (step 9.2).
  enhanced_vpc_routing = false

  # AI-driven scaling off, explicitly. The target is enabled by default for every new workgroup, at
  # Balanced (AWS, "Compute capacity for Amazon Redshift Serverless", read 2026-09-20), and AWS does
  # not recommend it at 4 base RPUs; the intent, no scaling on the service's own judgement at the
  # floor, is `enabled = false`, and the default being on is what makes writing it necessary.
  price_performance_target {
    enabled = false
  }

  # require_ssl: the connection is encrypted or it is refused.
  config_parameter {
    parameter_key   = "require_ssl"
    parameter_value = "true"
  }

  # Without this, `useractivitylog` carries no SQL text, the half Stage 11 wants and the half that
  # makes the group a store of governed values as well as a feed (Stage 9 decision 8).
  config_parameter {
    parameter_key   = "enable_user_activity_logging"
    parameter_value = "true"
  }

  # The per-query ceiling, in seconds, set and not relied on (Stage 9 step 9.1). In Sandbox it was
  # 1800 s, read back as 1800, and a `count(*)` over a triple cross join ran 23,601 s at base capacity
  # (2026-09-20, 9.44 USD). Three candidates stand for why it did not bite, and the test that separates
  # them is a long query over a user table as a non-superuser and as the admin, owed in Sandbox with
  # the compute up (5b): (a) a superuser exempt from the query-monitoring rules; (b) the parameter as a
  # standalone config_parameter not enforced at all, a ceiling only existing through
  # `wlm_json_configuration` (Lesson 56); (c) the runaway never entered WLM, a catalog-only statement
  # running on the leader node alone, which also kept running through two minutes of a breached usage
  # limit (5b log, 2026-10-18). It is left set because it costs nothing and under (a) it binds a
  # non-superuser, which the job role's database user is; what is relied on is the usage limit and
  # `make down`.
  config_parameter {
    parameter_key   = "max_query_execution_time"
    parameter_value = tostring(local.capacity.max_query_execution_time)
  }

  # The six parameters the service sets, declared so their values are pinned. Redshift fills its own
  # defaults, so a workgroup created with three parameters reads back with nine. Provider 6.66.0 and
  # later keep only the declared keys in state and ignore the rest (measured 2026-09-20 on 6.64.0, which
  # planned to remove the six on every plan). `enable_large_strings_opt_in`, which the service returns
  # from 2026-10-13, is left undeclared and takes the service's default.
  #
  # auto_mv is off (Stage 9 decision 7): automatic materialized views are compute nobody asked for, a
  # refresh being a query on a 1.44 USD/hour meter, and a governed schema written by one load job gains
  # nothing from views the service decides to build. Sandbox keeps the service's default, on.
  config_parameter {
    parameter_key   = "auto_mv"
    parameter_value = "false"
  }

  config_parameter {
    parameter_key   = "datestyle"
    parameter_value = "ISO, MDY"
  }

  config_parameter {
    parameter_key   = "enable_case_sensitive_identifier"
    parameter_value = "false"
  }

  config_parameter {
    parameter_key   = "query_group"
    parameter_value = "default"
  }

  # `search_path` resolves an unqualified table name in `public`, where PUBLIC holds USAGE and no
  # CREATE once step 9.3's REVOKE has run, so an unqualified CREATE TABLE by a non-superuser fails
  # rather than landing somewhere nobody expects.
  config_parameter {
    parameter_key   = "search_path"
    parameter_value = "$user, public"
  }

  # FIPS off, the default, and what the estate's endpoint lists assume: every `*-fips` sibling is
  # excluded from `vpc-egress`'s service lists.
  config_parameter {
    parameter_key   = "use_fips_ssl"
    parameter_value = "false"
  }

  # No `AmazonDataZoneProject` tag and no wide tag (step 9.3): no SMUS project is admitted to this
  # warehouse, and WH-7 reads the absence as the pass.
  tags = { Name = local.name }

  lifecycle {
    # The two AZs, checked before the apply rather than after the error.
    precondition {
      condition     = length(local.private_subnet_ids) >= 2
      error_message = "a workgroup needs at least two private subnets in two Availability Zones; workloads/ reported ${length(local.private_subnet_ids)}."
    }

    # The floor, asserted where it cannot be edited away by accident. No IAM condition key reaches the
    # base capacity, so the guards are this precondition, the workgroup's own max_capacity, the usage
    # limit and the ComputeCapacity alarm. Past 4 the warehouse never returns to 4 on its own.
    precondition {
      condition     = local.capacity.base_capacity == 4
      error_message = "base_capacity is ${local.capacity.base_capacity} and D40 fixes the warehouse at the documented floor of 4. Raising it is a decision with a cost attached (0.36 USD/RPU-hour) and an irreversible one: Amazon Redshift will not scale back down to 4."
    }
  }
}

# ---------------------------------------------------------------- the hard ceiling the service enforces
#
# `breach_action = deactivate` and not the default: the API's default is `log`, which refuses nothing,
# so a limit whose action was left alone reads as a ceiling and is not one (WH-3 checks exactly that).
#
# The amount is in RPU-hours for `serverless-compute`: 4 RPUs x 1 hour of query time = 4 RPU-hours =
# 1.44 USD. 10 RPU-hours (Stage 9 decision 7) is 2.5 hours of query time a month, 3.60 USD, 7% of the
# D12 ceiling; `deactivate` costs an interruption rather than money and recovery is immediate on
# raising the amount, which only InfrastructureAccess may do (step 9.4). A breached limit leaves the
# workgroup AVAILABLE with leader-node queries answering, so a job reads a refused query, never the
# workgroup's status.
#
# What it does not bound: storage. A schema filled to its 1 TB quota is 24.58 USD/month whether this
# limit has fired or not, and whether a workgroup exists at all; the storage guard is
# production/warehouse/'s DataStorage alarm.
resource "aws_redshiftserverless_usage_limit" "compute" {
  resource_arn  = aws_redshiftserverless_workgroup.this.arn
  usage_type    = "serverless-compute"
  amount        = local.capacity.usage_limit_rpu_hours
  period        = local.capacity.usage_limit_period
  breach_action = "deactivate"
}
