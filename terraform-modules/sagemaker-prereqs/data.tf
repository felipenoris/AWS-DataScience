# What this module reads and does not own.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The roster guard (pass 2b only). The awscc configuration resource takes the blueprint NAME
# itself (blueprints.tf, measured 2026-08-21), so nothing here needs an id resolved any more;
# the lookup stays because it is the plan-time check that every name in var.blueprint_names
# still exists as a managed blueprint in the shared domain - an AWS-side rename fails the
# plan with a readable "not found" instead of a create-time waiter error (Lesson 38: a name
# read out of prose is a claim, and this data source is what turns the roster's names back
# into a measurement on every plan). blueprints.tf consumes its .name - the same string that
# went in - so the guard is a declared dependency of every configuration rather than a
# dangling declaration tflint would rightly flag.
data "aws_datazone_environment_blueprint" "enabled" {
  for_each = var.blueprints_enabled ? toset(var.blueprint_names) : toset([])

  domain_id = var.domain_id
  name      = each.value
  managed   = true
}
