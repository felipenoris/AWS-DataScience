# Outputs - what production/warehouse-compute/ reads through terraform_remote_state, never pasted
# (Lesson 3). The compute slice declares no copy of any value below: one authored place, so a
# disagreement is impossible rather than unlikely (Lesson 33).

output "namespace_name" {
  description = "The namespace the workgroup attaches to. Also the stem of the three audit log group paths, which the service derives, so this name is a contract (Stage 9's contracts list)."
  value       = aws_redshiftserverless_namespace.this.namespace_name
}

output "namespace_arn" {
  description = "The namespace ARN."
  value       = aws_redshiftserverless_namespace.this.arn
}

output "security_group_id" {
  description = "The workgroup's security group (step 9.1): ingress 5439/tcp from the job security group alone."
  value       = aws_security_group.warehouse.id
}

output "admin_password_secret_arn" {
  description = "The Redshift-managed admin credential in Secrets Manager. Step 9.3 reads it to run the governed schema's SQL. No password is here: this is the secret's ARN, and WH-5 greps the state to prove the value is not."
  value       = aws_redshiftserverless_namespace.this.admin_password_secret_arn
}

output "namespace_exec_role_arn" {
  description = "The namespace role (step 9.2). It holds no policy; WH-1b reads that back rather than asserting it."
  value       = aws_iam_role.namespace_exec.arn
}

# The cost ceiling's numbers, declared here and consumed by the compute slice. They are on the [P]
# side because they are the decision (5b decision 2, Stage 9 decision 7) and the compute slice is the
# thing that is destroyed and rebuilt: a value living only in an [E] slice is conventions 5.1 rule 2's
# failure.
output "capacity" {
  description = "base_capacity, max_capacity, the usage limit and the per-query ceiling - read by production/warehouse-compute/, which declares none of its own."
  value = {
    base_capacity            = var.base_capacity
    max_capacity             = var.max_capacity
    usage_limit_rpu_hours    = var.usage_limit_rpu_hours
    usage_limit_period       = var.usage_limit_period
    max_query_execution_time = var.max_query_execution_time
  }
}
