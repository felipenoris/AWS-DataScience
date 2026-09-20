# sandbox/warehouse-compute/ - the COMPUTE half of the Redshift Serverless warehouse (Stage 5b pass
# 1), layer [E]. Two resources and nothing else: the workgroup and its usage limit.
#
# WHY [E] AND NOT [D]. Redshift Serverless has `create-workgroup` and `delete-workgroup` and nothing
# in between - no stop, no suspend, no zero-capacity setting. A provisioned cluster can be paused; a
# serverless workgroup cannot. So "powered off" means "does not exist", which is the definition of
# [E] (conventions 5.1), and it is also the strongest guarantee available: an object that does not
# exist cannot receive a query, so none of D40's three ways an idle warehouse bills anyway - an open
# transaction (up to 6 hours before the idle-transaction timeout ends it, 8.64 USD at 4 RPUs), a
# connection pool's `SELECT 1`, a cancelled query that billed for the time it ran - has anything to
# arrive at.
#
# WHY THE USAGE LIMIT IS IN THE SAME SLICE AND THE SAME APPLY. A workgroup that exists for even one
# plan cycle without its ceiling is a workgroup with no ceiling, and that window is exactly when a
# mistake is most likely. The two guards are one hard and one soft: `make down` removes the compute,
# and the usage limit bounds it while it exists.
#
# WHAT SURVIVES A `make down`. Everything in sandbox/warehouse/: the namespace and its data, the
# schemas, the database users, the database roles and every GRANT, the admin secret, the three audit
# log groups, the security group and both alarms. Step 1.9 reads that back rather than trusting it,
# and it also reads THE ENDPOINT HOST, because 6h's SMUS connection stores that address as a field:
# if the host does not survive a delete and re-create under the same name, every `make down`
# silently breaks every connection and 5b decision 8 is the fallback.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
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
  projects  = data.terraform_remote_state.warehouse.outputs.projects

  # THE TWO PRIVATE SUBNETS, SELECTED BY ZONE ID. AWS's own considerations page: "Two subnets
  # (without EVR) - You must have at least two subnets, and they must span across two Availability
  # Zones"; three only WITH Enhanced VPC Routing, which is off below. The Terraform provider's own
  # documentation page says three, and its code has no validator at all - `subnet_ids` is a plain
  # optional/computed TypeSet - so the service is the only authority and the apply is the reading
  # (Lesson 30: a tool's failure is not a property of the world).
  private_subnet_ids = [
    for z in var.zone_ids : data.terraform_remote_state.foundation.outputs.private_subnet_ids[z]
  ]
}

resource "aws_redshiftserverless_workgroup" "this" {
  workgroup_name = local.name
  namespace_name = local.namespace

  base_capacity = local.capacity.base_capacity
  # AWS: "Max capacity and Max RPU-hours ... are the controls to limit the maximum RPUs that Amazon
  # Redshift Serverless allows the data warehouse to scale ... Amazon Redshift Serverless ALWAYS
  # HONORS AND ENFORCES THESE SETTINGS, REGARDLESS OF THE PRICE-PERFORMANCE TARGET SETTING." Both
  # are set here: this field and the usage limit below.
  max_capacity = local.capacity.max_capacity

  # `subnet_ids` is Optional AND Computed, so omitting it plans as unknown and lets the service
  # choose - and the service would choose the default VPC, which no account here has. Always set it
  # (Lesson 27: a plan is silent about the values the provider owns).
  subnet_ids         = local.private_subnet_ids
  security_group_ids = [data.terraform_remote_state.warehouse.outputs.security_group_id]

  publicly_accessible = false

  # Off, which is what makes two subnets sufficient (see locals above). Enhanced VPC Routing forces
  # COPY/UNLOAD traffic through the VPC and is the case AWS documents as needing three AZs; nothing
  # here does COPY or UNLOAD at all, because the namespace role reaches no bucket (5b decision 5).
  enhanced_vpc_routing = false

  # AI-DRIVEN SCALING OFF, EXPLICITLY, AND THIS CORRECTS 5b DECISION 2'S LETTER. That decision said
  # "the target set to Optimizes for cost, because AWS does not recommend AI-driven scaling at 4
  # base RPUs" - two halves that cannot both be done, because "Optimizes for cost" IS the feature.
  # The reading (AWS, "Compute capacity for Amazon Redshift Serverless", 2026-09-20): the target "is
  # enabled by default for all new Serverless workgroups and is set to Balanced", its `level` takes
  # 1, 25, 50, 75 or 100 (LOW_COST, ECONOMICAL, BALANCED, RESOURCEFUL, HIGH_PERFORMANCE), and "We do
  # not recommend using this feature for 4 Base RPU". So the decision's INTENT - do not let the
  # service scale on its own judgement at the capacity floor - is `enabled = false`, and the default
  # being ENABLED is what makes writing it explicitly necessary rather than tidy.
  price_performance_target {
    enabled = false
  }

  # require_ssl: the connection is encrypted or it is refused. There is no other value worth having
  # on a store holding project data.
  config_parameter {
    parameter_key   = "require_ssl"
    parameter_value = "true"
  }

  # Without this, `useractivitylog` carries no SQL text - which is the half Stage 11 wants and the
  # half that makes the group a DLP exposure as well as a DLP feed (5b step 4's residual).
  config_parameter {
    parameter_key   = "enable_user_activity_logging"
    parameter_value = "true"
  }

  # The per-query ceiling, the counterpart of the Athena scan limit. The service's own maximum is
  # 86,399 seconds, which is also what a query with no limit gets - so leaving this unset is a
  # 24-hour runaway at 1.44 USD/h.
  config_parameter {
    parameter_key   = "max_query_execution_time"
    parameter_value = tostring(local.capacity.max_query_execution_time)
  }

  # LAYER 1'S WORKGROUP HALF, from sandbox/warehouse/'s map rather than from a copy here. AWS's
  # requirement names both objects - the tag goes on "the Amazon Redshift cluster or workgroup AND
  # ITS NAMESPACE" - and the namespace's half is written by that slice. Reading the map instead of
  # declaring it is what makes the two unable to disagree (Lesson 14).
  tags = merge(
    { Name = local.name },
    { for id in keys(local.projects) : "AmazonDataZoneProject" => id },
  )

  lifecycle {
    # The two AZs, checked before the apply rather than after the error. If the service ever refuses
    # two, this is 5b decision 1 and the fallback is a third AZ's subnet trio - free, but a change to
    # the vpc module, to docs/NETWORK.md's address table and to check-network-doc.py's arithmetic.
    precondition {
      condition     = length(local.private_subnet_ids) >= 2
      error_message = "a workgroup needs at least two private subnets in two Availability Zones; foundation/ reported ${length(local.private_subnet_ids)}."
    }

    # The floor, asserted where it cannot be edited away by accident. A base capacity above 4 is not
    # PREVENTABLE by any IAM condition key - none exists - so the guards are this precondition, the
    # workgroup's own max_capacity, the usage limit and the ComputeCapacity alarm. The ratchet is why
    # it matters: past 4 the warehouse never returns to 4 on its own.
    precondition {
      condition     = local.capacity.base_capacity == 4
      error_message = "base_capacity is ${local.capacity.base_capacity} and D40 fixes the warehouse at the documented floor of 4. Raising it is a decision with a cost attached (0.36 USD/RPU-hour) and an irreversible one: Amazon Redshift will not scale back down to 4."
    }
  }
}

# ---------------------------------------------------------------- the hard ceiling the service enforces
#
# `breach_action = deactivate` and NOT the default. The API's default is `log`, which refuses nothing
# - a limit whose action was left alone reads as a ceiling and is not one (WH-3 is the check for
# exactly that). The other two actions are `emit-metric` and `log`.
#
# The amount is in RPU-HOURS for `serverless-compute`, so the arithmetic is: 4 RPUs x 1 hour of query
# time = 4 RPU-hours = 1.44 USD. The default of 40 RPU-hours is 10 hours of query time a month,
# 14.40 USD, 29% of the D12 ceiling - leaving room for the RMS storage this limit does not bound and
# `make down` does not remove.
#
# WHAT IT DOES NOT BOUND, said here because the name suggests otherwise: storage. A schema filled to
# its 1 TB quota is 24.58 USD/month whether this limit has fired or not, and whether a workgroup
# exists at all. The storage guard is sandbox/warehouse/'s DataStorage alarm.
resource "aws_redshiftserverless_usage_limit" "compute" {
  resource_arn  = aws_redshiftserverless_workgroup.this.arn
  usage_type    = "serverless-compute"
  amount        = local.capacity.usage_limit_rpu_hours
  period        = local.capacity.usage_limit_period
  breach_action = "deactivate"
}
