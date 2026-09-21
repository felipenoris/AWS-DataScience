# Outputs - what sandbox/warehouse-compute/ reads through terraform_remote_state, never pasted
# (Lesson 3). The compute slice declares NO copy of any value below: one authored place, and a
# disagreement is impossible rather than merely unlikely (Lesson 33).

output "namespace_name" {
  description = "The namespace the workgroup attaches to. Also the stem of the three audit log group paths, which the service derives - so this name is a contract, not a label."
  value       = aws_redshiftserverless_namespace.this.namespace_name
}

output "namespace_arn" {
  description = "The namespace ARN."
  value       = aws_redshiftserverless_namespace.this.arn
}

output "security_group_id" {
  description = "The workgroup's security group (step 1.4) - ingress 5439/tcp from admitted projects' app ENIs only."
  value       = aws_security_group.warehouse.id
}

output "admin_password_secret_arn" {
  description = "The Redshift-managed admin credential in Secrets Manager. Stage 6h reads it to run layer 3's SQL. NO PASSWORD IS HERE: this is the secret's ARN, and WH-5 greps the state to prove the value is not."
  value       = aws_redshiftserverless_namespace.this.admin_password_secret_arn
}

output "namespace_exec_role_arn" {
  description = "The namespace role (step 1.5). It holds no policy by decision 5 - 2.4 reads that back rather than asserting it."
  value       = aws_iam_role.namespace_exec.arn
}

# The cost ceiling's numbers, declared here and consumed by the compute slice. They are on the [P]
# side because they are the DECISION (5b decision 2) and the compute slice is the thing that is
# destroyed and rebuilt: a value living only in an [E] slice is conventions 5.1 rule 2's failure.
output "capacity" {
  description = "base_capacity, max_capacity, the usage limit and the per-query ceiling - read by sandbox/warehouse-compute/, which declares none of its own."
  value = {
    base_capacity            = var.base_capacity
    max_capacity             = var.max_capacity
    usage_limit_rpu_hours    = var.usage_limit_rpu_hours
    usage_limit_period       = var.usage_limit_period
    max_query_execution_time = var.max_query_execution_time
  }
}

output "projects" {
  description = "The admitted projects, keyed by project id - layer 1's authored map. The compute slice reads it for the workgroup's half of the tag pair; the namespace's half is written here."
  value       = var.projects
}

# The value a project member types into the portal's "Access role ARN" field, per project. It is an
# output rather than a thing somebody reads off the console because the field is mandatory in the
# form and the run that fills it is the user's, not this repository's (6h 3.2).
output "project_access_role_arns" {
  description = "The access role ARN per admitted project - the portal's mandatory `Access role ARN` field when the credential type is IAM credentials."
  value       = { for id, r in aws_iam_role.project_access : id => r.arn }
}
