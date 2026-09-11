# What this slice publishes.
#
# Nothing here is read by another slice today. The outputs exist so the state answers the two
# questions an operator asks without reading the plan: what the policy is called, and which
# projects currently hold it.

output "policy_arn" {
  description = "The Bedrock grant. Named in the runbook's aws CLI equivalent, so the two forms attach the same policy rather than two copies of one."
  value       = aws_iam_policy.bedrock_assistant.arn
}

output "attached_project_roles" {
  description = "The project roles that hold the grant right now. An empty list is legal: a fresh account has no project yet."
  value       = sort(var.project_roles)
}

output "scoped_model_arns" {
  description = "The resources the grant names, both groups. The endpoint policy of Stage 6e step 4 is written against the same two lists (one list, four consumers)."
  value = {
    inference_profiles = sort(local.profile_arns)
    foundation_models  = sort(local.foundation_model_arns)
  }
}
