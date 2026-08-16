output "key_arn" {
  description = "The key ARN - what encryption configurations reference."
  value       = aws_kms_key.this.arn
}

output "key_id" {
  description = "The key id."
  value       = aws_kms_key.this.key_id
}

output "alias_name" {
  description = "The full alias, alias/ prefix included."
  value       = aws_kms_alias.this.name
}
