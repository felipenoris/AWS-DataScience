output "repository_name" {
  description = "The repository name - what a docker tag line carries after the registry host."
  value       = aws_ecr_repository.this.name
}

output "repository_url" {
  description = "<account>.dkr.ecr.<region>.amazonaws.com/<name> - the push/pull target, resolved rather than pasted (aws/INDEX.md rule 1)."
  value       = aws_ecr_repository.this.repository_url
}

output "repository_arn" {
  description = "The ARN - what an IAM statement in a consumer account names."
  value       = aws_ecr_repository.this.arn
}
