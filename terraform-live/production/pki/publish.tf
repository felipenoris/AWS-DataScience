# publish.tf - the root and the leaves' CERTIFICATES published from one source (Stage 7 step 2.3,
# INT-19, Lesson 14), and the leaves' KEYS put where only the host can read them (2.4).
#
# Two publication channels, both [P], for two kinds of reader:
#
#   SSM parameters   /datascience/prod/pki/...   the universal reader: the laptop (2.5), the
#                                                runner's user data (6.1), the image build (2.6)
#                                                and the GitLab host's bootstrap all run
#                                                `aws ssm get-parameter`. `/datascience/` because
#                                                Parameter Store reserves every name beginning with
#                                                `aws` (conventions, measured at Stage 2).
#   S3 objects       s3://<objects bucket>/pki/  the copy a host reaches through the free gateway
#                                                endpoint with no `ssm` endpoint up, beside the
#                                                `config/gitlab.rb` tooling/ publishes. The stage
#                                                wrote "an existing Production bucket": the only one
#                                                that existed was the state bucket, so the copies
#                                                sit in the GitLab objects bucket foundation/ created
#                                                at 1.1, outside every GitLab prefix.
#
# A PEM is never pasted anywhere: every consumer reads one of these. ./aws/supplychain.py SC-9 reads
# the root parameter's presence and SC-8 the leaves' expiry.

locals {
  parameter_prefix = "/datascience/${var.env}/pki"

  # The published documents, keyed as the parameter and the object are named.
  published = merge(
    {
      "ca-root" = {
        pem       = tls_self_signed_cert.root.cert_pem
        file_name = "awsds-root.crt"
        what      = "the internal root CA certificate (D36) - the one trust anchor every client surface installs (INT-19)"
      }
    },
    {
      for k, leaf in local.leaves : "leaf-${k}" => {
        pem       = tls_locally_signed_cert.leaf[k].cert_pem
        file_name = "${leaf.file_stem}.crt"
        what      = "the ${leaf.common_name} leaf certificate - the public half; its key is the Secrets Manager secret awsds-${var.env}-tls-${k}"
      }
    },
  )
}

resource "aws_ssm_parameter" "published" {
  # checkov:skip=CKV_AWS_337:a String parameter, not a SecureString - a certificate is the public half of a key pair and is served to every TLS client; its whole value is that a reader with no decrypt permission can install it
  # checkov:skip=CKV2_AWS_34:same reading - SecureString would encrypt a document the server hands to anyone who connects
  for_each = local.published

  name        = "${local.parameter_prefix}/${each.key}-pem"
  description = "${each.value.what} (Stage 7 step 2.3). Read it, never paste it."
  type        = "String"
  tier        = "Standard"
  value       = each.value.pem

  tags = {
    Name = "awsds-${var.env}-pki-${each.key}"
  }
}

resource "aws_s3_object" "published" {
  for_each = local.published

  bucket                 = data.terraform_remote_state.foundation.outputs.gitlab_objects_bucket
  key                    = "pki/${each.value.file_name}"
  content                = each.value.pem
  content_type           = "application/x-pem-file"
  server_side_encryption = "aws:kms"
  kms_key_id             = data.terraform_remote_state.foundation.outputs.gitlab_key_arn

  tags = {
    Name = "awsds-${var.env}-pki-${each.key}"
  }
}

# ---------------------------------------------------------------- the leaf keys (step 2.4)
#
# The private half of each leaf, in a secret the GitLab host's role reads at boot and at every
# refresh. The value is written by Terraform here - it is the tls provider's output and already in
# this state - so this is the one place in the repository where an aws_secretsmanager_secret_version
# exists. The host-key and gitlab-secrets containers hold values Terraform never saw; these hold
# values it minted.
#
# The resource policy denies the read to every principal but the host's role and
# InfrastructureAccess, the shape production/networking/ settled for the host key (6c step 4.1).
# The role name is a contract with tooling/, which names its role awsds-<env>-gitlab.

resource "aws_secretsmanager_secret" "leaf_key" {
  # checkov:skip=CKV2_AWS_57:rotation is the re-issue above, by `terraform apply`, never a Lambda - a key rotated without its certificate is an nginx that refuses to start
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - the containment is the resource policy below, which a CMK would not sharpen
  for_each = local.leaves

  name        = "awsds-${var.env}-tls-${each.key}"
  description = "The private key of the ${each.value.common_name} leaf (Stage 7 step 2.4). Written by production/pki/, read by the GitLab host's role at boot and on refresh; re-issued by `terraform apply` within 30 days of expiry."

  recovery_window_in_days = 30

  tags = {
    Name = "awsds-${var.env}-tls-${each.key}"
  }
}

resource "aws_secretsmanager_secret_version" "leaf_key" {
  for_each = local.leaves

  secret_id     = aws_secretsmanager_secret.leaf_key[each.key].id
  secret_string = tls_private_key.leaf[each.key].private_key_pem
}

resource "aws_secretsmanager_secret_policy" "leaf_key" {
  for_each = local.leaves

  secret_arn = aws_secretsmanager_secret.leaf_key[each.key].arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptHostAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-gitlab",
              "arn:${data.aws_partition.current.partition}:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*",
            ]
          }
        }
      }
    ]
  })
}
