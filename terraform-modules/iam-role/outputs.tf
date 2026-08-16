output "role_arn" {
  description = "The role ARN."
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "The role name."
  value       = aws_iam_role.this.name
}
