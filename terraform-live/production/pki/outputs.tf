# Outputs - the certificates and the names of what publishes them. Never the root's private key
# (D36 section 2), and never a leaf's: tooling/ reads a leaf key's secret ARN and grants its role
# the read; the value stays between Secrets Manager and the host.

output "ca_certificate_pem" {
  description = "The root CA certificate - the trust anchor every client surface installs (INT-19). Prefer the parameter below for anything automated."
  value       = tls_self_signed_cert.root.cert_pem
}

output "ca_root_parameter_name" {
  description = "The SSM parameter holding the root certificate - INT-19's one source (step 2.3); the runner's user data and the image build read it."
  value       = aws_ssm_parameter.published["ca-root"].name
}

output "leaf_parameter_names" {
  description = "The SSM parameters holding each leaf's certificate, by leaf (gitlab, pages). ./aws/supplychain.py SC-8 reads the expiry from these."
  value       = { for k in keys(local.leaves) : k => aws_ssm_parameter.published["leaf-${k}"].name }
}

output "leaf_certificate_pems" {
  description = "Each leaf's certificate, by leaf - what tooling/'s bootstrap installs as /etc/gitlab/ssl/<host>.crt."
  value       = { for k, c in tls_locally_signed_cert.leaf : k => c.cert_pem }
}

output "leaf_key_secret_arns" {
  description = "Each leaf's private key, as the Secrets Manager secret the GitLab host's role reads (step 2.4). ARNs only."
  value       = { for k, s in aws_secretsmanager_secret.leaf_key : k => s.arn }
}

output "leaf_validity_end_times" {
  description = "Each leaf's notAfter, as the tls provider reports it - the date the re-issue is owed by."
  value       = { for k, c in tls_locally_signed_cert.leaf : k => c.validity_end_time }
}

output "published_object_keys" {
  description = "The S3 keys of the published certificates in the GitLab objects bucket, by document."
  value       = { for k, o in aws_s3_object.published : k => o.key }
}

output "parameter_arns" {
  description = "Every published parameter's ARN - what the host and runner roles' ssm:GetParameter statements name."
  value       = { for k, p in aws_ssm_parameter.published : k => p.arn }
}
