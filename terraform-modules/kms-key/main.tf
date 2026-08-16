# kms-key - a CMK with the two requirements Stage 2 step 7 authored and Stage 3 step 1.1a
# carried over verbatim: rotation on, and a deletion window (no immediate delete).
#
# The default policy delegates to IAM in the caller's account - the bootstrap key's shape
# (Stage 2 step 2.4): the account's IAM policies decide who may use the key, which today
# means InfrastructureAccess. A caller with a narrower answer (D19's derived-zone CMK, D36's
# PKI state key) passes its own document through var.policy.

data "aws_caller_identity" "current" {}

data "aws_partition" "current" {}

resource "aws_kms_key" "this" {
  description = var.description

  enable_key_rotation     = true
  deletion_window_in_days = var.deletion_window_in_days

  policy = var.policy != null ? var.policy : jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableIamPolicyDelegationInThisAccount"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      }
    ]
  })

  tags = {
    Name = var.alias_name
  }
}

resource "aws_kms_alias" "this" {
  name          = "alias/${var.alias_name}"
  target_key_id = aws_kms_key.this.key_id
}
