output "workflow_arns" {
  description = "Each workflow's ARN, by key: its name plus the ten characters the service appends."
  value       = local.workflow_arns
}

output "workflow_versions" {
  description = "Each workflow's current version, by key: every save spends one of fifty (step 1.6)."
  value       = { for k, w in awscc_mwaaserverless_workflow.this : k => w.workflow_version }
}

output "execution_role_arns" {
  description = "Each workflow's execution role, by key (step 1.3)."
  value       = { for k, r in module.execution_role : k => r.role_arn }
}

output "log_group_names" {
  description = "Each workflow's log group, by key, and the chains' log group under \"chains\"."
  value       = merge({ for k, g in aws_cloudwatch_log_group.workflow : k => g.name }, { chains = aws_cloudwatch_log_group.chains.name })
}

output "state_machine_arns" {
  description = "Each chain's state machine, by key (step 3.5)."
  value       = { for k, m in aws_sfn_state_machine.chain : k => m.arn }
}

output "schedule_names" {
  description = "Each chain's schedule in the group awsds-<env>-chains, by key: its state is the pause lever."
  value       = { for k, s in aws_scheduler_schedule.chain : k => s.name }
}

output "chain_role_arns" {
  description = "awsds-<env>-chain-exec, -chain-scheduler and -chain-events (steps 3.4, 3.6): the data key's policy names chain-exec."
  value = {
    exec      = module.chain_exec_role.role_arn
    scheduler = module.chain_starter_role["scheduler"].role_arn
    events    = module.chain_starter_role["events"].role_arn
  }
}

output "workers_security_group_id" {
  description = "awsds-<env>-wf-workers, the security group every workflow's network_configuration names (step 1.2)."
  value       = aws_security_group.workers.id
}
