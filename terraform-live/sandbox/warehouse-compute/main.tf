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

  # The per-query ceiling - AND IT DID NOT HOLD (2026-09-20). Set to 1800 s at creation, read back as
  # 1800 by WH-2, and a `count(*)` over a triple cross join ran 23,601 seconds - thirteen times the
  # limit - at base capacity, costing 9.44 USD. The client had stopped polling after 242 s; the Data
  # API does not cancel a statement when its client goes away, and nothing else stopped it either.
  #
  # THE UNIT IS SECONDS, settled from three readings (2026-09-20): the quotas page gives the service
  # maximum as "86,399 seconds (24 hours)", which is also this value's validation ceiling; the
  # serverless query-queues page's own QMR examples read `query_execution_time > 60` as "more than 60
  # seconds" and `> 3600` as "more than an hour"; and the millisecond parameter in this family,
  # `statement_timeout`, is a different one and is not in the Serverless config_parameters list at all.
  # So 1800 is thirty minutes.
  #
  # WHY IT DID NOT BITE IS STILL OPEN, and the first hypothesis lost its support the same day. It was
  # "the superuser queue is exempt from WLM and QMR, and the statement ran as `dbadmin`, which pg_user
  # reports as a superuser". Then AWS's query-queues page turned out to say the opposite: "Query
  # monitoring rules (QMR) apply only at the Redshift Serverless workgroup level, AFFECTING ALL QUERIES
  # RUN IN THIS WORKGROUP UNIFORMLY" - and its example exempts an admin by giving them a QUEUE with no
  # rules, which implies that without queues (this workgroup has none, and enabling them is a permanent
  # change) the workgroup-level rule reaches everyone. Two candidates remain:
  #
  #   (a) the superuser exemption after all - weakened, not excluded: the sentence above describes the
  #       behaviour queues were introduced to improve on, and does not say superusers are included.
  #   (b) `max_query_execution_time` as a standalone config_parameter is simply NOT ENFORCED, and a
  #       per-query ceiling only exists through `wlm_json_configuration`. That is Lesson 56 in its
  #       purest form: a vendor-documented line that reads back with the right value and does nothing.
  #
  # ONE TEST SEPARATES THEM: run a long query as a NON-superuser. Aborting at 1800 s means (a); not
  # aborting means (b). That needs a database credential this estate does not yet issue, so it arrives
  # with Stage 6h's project user.
  #
  # IT IS LEFT SET, and the reason is not optimism. It costs nothing, under (a) it binds a project's
  # database user (which is not a superuser), and removing it would leave nothing at all on this axis.
  # What changed is what is RELIED ON: the guards that did hold are the usage limit (breach_action =
  # deactivate, 10 RPU-hours since 2026-09-20) and `make down`, which is the only one that is not a
  # setting. Read this comment before treating this line as a control.
  config_parameter {
    parameter_key   = "max_query_execution_time"
    parameter_value = tostring(local.capacity.max_query_execution_time)
  }

  # THE SIX THE SERVICE SETS, DECLARED SO THE PLAN IS STABLE. `config_parameter` is a set the
  # provider owns whole: a workgroup created with three parameters reads back with nine, because
  # Redshift fills its own defaults, and the provider then plans to REMOVE the six it was not told
  # about - a perpetual "1 to change" that never converges (found 2026-09-20, on the first re-plan
  # of this slice after the apply, which is why "re-plan No changes" is a step and not a courtesy).
  #
  # Declaring them is the fix and it is also the disclosure: these are the values a query actually
  # runs under, and until now no tracked file said what they were. All six are the service's
  # defaults, read back from `get-workgroup` after the first apply. Two are worth a sentence:
  #
  #   auto_mv      automatic materialized views. ON by default, and it is COMPUTE the estate did
  #                not ask for: Redshift decides on its own to build and refresh materialized
  #                views, and a refresh is a query on a 1.44 USD/hour meter. Left at the default
  #                for now and named here so turning it off is a decision somebody can find.
  #   search_path  `"$user, public"`. It resolves an unqualified table name in `public` - the
  #                schema 5b 1.6 revoked CREATE on - which means an unqualified CREATE TABLE fails
  #                rather than landing somewhere nobody expects. That is the right behaviour, and
  #                it is a consequence of the revoke rather than of this line.
  config_parameter {
    parameter_key   = "auto_mv"
    parameter_value = "true"
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

  config_parameter {
    parameter_key   = "search_path"
    parameter_value = "$user, public"
  }

  # FIPS off, which is the default and is also what the estate's endpoint policy assumes: every
  # `*-fips` sibling is deliberately excluded from `vpc-egress`'s service lists, so a client
  # configured for FIPS would resolve a name no endpoint here serves.
  config_parameter {
    parameter_key   = "use_fips_ssl"
    parameter_value = "false"
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
# time = 4 RPU-hours = 1.44 USD. **10 RPU-hours since 2026-09-20** - 2.5 hours of query time a month,
# 3.60 USD, 7% of the D12 ceiling. It was 40, and it moved because one forgotten statement reached
# 26.3 RPU-hours in an afternoon: sandbox/warehouse/variables.tf carries the argument, and the reason
# a low value is cheap is that `deactivate` costs an interruption rather than money and recovery is
# immediate on raising the amount.
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
