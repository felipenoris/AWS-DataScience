# What this slice reads and does not own.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

# The member accounts a project profile provisions into - resolved live so that no account id
# enters a tracked file (aws/INDEX.md rule 1).
data "aws_caller_identity" "sandbox" {
  provider = aws.sandbox
}

data "aws_caller_identity" "development" {
  provider = aws.development
}

# The blueprint ids, resolved BY NAME on the domain (pass 2c only). Terraform's project-profile
# resource takes ids; the decision, the documentation and ./aws/studio.py all speak names, so
# the lookup happens here rather than opaque identifiers being pasted into a variable.
data "aws_datazone_environment_blueprint" "enabled" {
  for_each = var.profiles_enabled ? toset(local.category_one_blueprints) : toset([])

  domain_id = aws_datazone_domain.this.id
  name      = each.value
  managed   = true
}
