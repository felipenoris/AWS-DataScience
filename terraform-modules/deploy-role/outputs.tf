output "role_arn" {
  description = "The deploy role's ARN - what the runner role's AssumeRole statement lists."
  value       = module.role.role_arn
}

output "role_name" {
  description = "The deploy role's name."
  value       = module.role.role_name
}

output "boundary_arn" {
  description = "The ceiling the role carries: awsds-<env>-deploy-boundary, or the name the caller gave a second role's."
  value       = aws_iam_policy.boundary.arn
}

output "misuse_rule_arn" {
  description = "The misuse rule's ARN, or null where the account carries no alarm."
  value       = one(aws_cloudwatch_event_rule.misuse[*].arn)
}
