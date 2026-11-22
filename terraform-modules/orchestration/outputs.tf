output "workflow_names" {
  description = "Each workflow's name in the deployment project, as the CLI composes it, by \"<application>/<workflow>\"."
  value       = local.workflow_names
}

output "stage_variables_parameters" {
  description = "The SSM parameter each application's stage variables are recorded in, by application: scripts/deploy-application.py writes it after a deploy, and every chain of the application reads it."
  value       = local.stage_variables_parameters
}

output "log_group_name" {
  description = "The state machines' log group."
  value       = aws_cloudwatch_log_group.chains.name
}

output "state_machine_arns" {
  description = "Each chain's state machine, by key (Stage 10 step 3.5)."
  value       = { for k, m in aws_sfn_state_machine.chain : k => m.arn }
}

output "schedule_names" {
  description = "Each chain's schedule in the group awsds-<env>-chains, by key: its state is the pause lever."
  value       = { for k, s in aws_scheduler_schedule.chain : k => s.name }
}

output "chain_role_arns" {
  description = "awsds-<env>-chain-exec and -chain-scheduler (Stage 10 step 3.4)."
  value = {
    exec      = module.chain_exec_role.role_arn
    scheduler = module.chain_scheduler_role.role_arn
  }
}
