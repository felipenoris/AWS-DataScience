# Read by the deploy leg's integration test, which starts a chain and follows its execution, and by
# scripts/deploy-application.py, which writes the parameter each chain reads.

output "state_machine_arns" {
  description = "Each chain's state machine, by key."
  value       = module.orchestration.state_machine_arns
}

output "workflow_names" {
  description = "Each workflow's name in the deployment project, as the CI/CD CLI composes it, by \"<application>/<workflow>\"."
  value       = module.orchestration.workflow_names
}

output "stage_variables_parameters" {
  description = "The SSM parameter each application's stage variables are recorded in, by application."
  value       = module.orchestration.stage_variables_parameters
}

output "chain_role_arns" {
  description = "awsds-<env>-chain-exec and -chain-scheduler."
  value       = module.orchestration.chain_role_arns
}
