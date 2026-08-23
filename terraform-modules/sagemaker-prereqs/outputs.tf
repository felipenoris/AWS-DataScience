output "provisioning_role_arn" {
  description = "What a blueprint configuration provisions through, in this account."
  value       = module.provisioning_role.role_arn
}

output "manage_access_role_arn" {
  description = "What DataZone fulfils a catalog subscription with - the principal verification (xiv) asks about on both sides of the share."
  value       = module.manage_access_role.role_arn
}

output "project_boundary_arn" {
  description = "The D13 boundary (US-8's name contract) - imposed on blueprint-authored roles through the blueprint configuration."
  value       = aws_iam_policy.project_boundary.arn
}

output "project_key_arn" {
  description = "This account's project CMK - NOT its data CMK (kms.tf says why)."
  value       = module.project_key.key_arn
}

output "regional_parameters" {
  description = "The VpcId/Subnets/AZs every blueprint configuration is pointed at - exported so a reader can see the network half of what the second apply will send without opening a plan. Tooling alone adds S3Location and KmsKeyArn on top (blueprints.tf, v0.3.2) - not repeated here."
  value = {
    VpcId   = var.vpc_id
    Subnets = join(",", values(var.private_subnet_ids))
    AZs     = join(",", keys(var.private_subnet_ids))
  }
}

output "deny_sids" {
  description = "The Sids the shared fragment contributed to the boundary - the same list identity/sso/ composes into the six persona sets (Lesson 33)."
  value       = module.denies.sids
}

output "studio_log_group_name" {
  description = "The deliberately-created log group (step 9.1) - what a running-app metric filter is written against."
  value       = aws_cloudwatch_log_group.studio.name
}
