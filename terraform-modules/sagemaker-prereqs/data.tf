# What this module reads and does not own.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The blueprint ids, resolved BY NAME from the shared domain (pass 2b only). Terraform's
# blueprint-configuration resource takes an id; the decision, the documentation and
# ./aws/studio.py all speak names, so the lookup happens here rather than a set of opaque
# identifiers being pasted into a variable (Lesson 23: bind to contents, never to an id).
data "aws_datazone_environment_blueprint" "enabled" {
  for_each = var.blueprints_enabled ? toset(var.blueprint_names) : toset([])

  domain_id = var.domain_id
  name      = each.value
  managed   = true
}
