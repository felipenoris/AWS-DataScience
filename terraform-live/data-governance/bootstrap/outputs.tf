# Outputs - Stage 2 step 2.
#
# NO SLICE READS THESE THROUGH terraform_remote_state, and none should: the backend literals
# come from scripts/tfhygiene/backend.py (step 2.5), which is the one place that knows how to
# build them. These exist so the apply ENDS by printing what it created - the values the log
# entry records and the values `./aws/tf-backends.py` is then checked against.

output "state_bucket" {
  description = "The state bucket this account's slices use as their backend."
  value       = aws_s3_bucket.tfstate.bucket
}

output "state_bucket_arn" {
  description = "ARN of the state bucket."
  value       = aws_s3_bucket.tfstate.arn
}

output "state_kms_key_arn" {
  description = "ARN of the key the state is encrypted under."
  value       = aws_kms_key.tfstate.arn
}

output "state_kms_alias" {
  description = "The alias backend.hcl names - a backend must refer to the key by something stable, and a key id is not it."
  value       = aws_kms_alias.tfstate.name
}
