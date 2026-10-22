# Read by ./aws/orchestration.py by name rather than from this state, and by the Staging leg's
# integration test, which starts the chain and follows its execution (Stage 8 step 3.3).

output "workflow_arns" {
  description = "Each workflow's ARN, by key; empty with no release."
  value       = one(module.orchestration[*].workflow_arns)
}

output "state_machine_arns" {
  description = "Each chain's state machine, by key; empty with no release."
  value       = one(module.orchestration[*].state_machine_arns)
}

output "execution_role_arns" {
  description = "Each workflow's execution role, by key: the data key's policy names them by the pattern awsds-<env>-wf-*."
  value       = one(module.orchestration[*].execution_role_arns)
}

output "chain_role_arns" {
  description = "awsds-<env>-chain-exec, -chain-scheduler and -chain-events."
  value       = one(module.orchestration[*].chain_role_arns)
}
