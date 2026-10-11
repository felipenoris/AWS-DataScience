# What this slice publishes. Nothing reads it today; the outputs answer the two questions an
# operator asks without reading the plan: what the policy is called, and which projects hold it.

output "policy_arn" {
  description = "The workflows grant."
  value       = aws_iam_policy.workflows.arn
}

output "attached_project_roles" {
  description = "The project roles that hold the grant right now. An empty list is legal."
  value       = sort(var.project_roles)
}
