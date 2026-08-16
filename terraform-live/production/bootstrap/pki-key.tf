# The SECOND state key, and the only file that is not shared by all five bootstrap slices -
# Stage 2 step 3.4, D36.
#
# WHY PRODUCTION HAS TWO KEYS. D36 puts the internal CA's ROOT PRIVATE KEY in a Terraform state
# file (terraform-live/production/pki/, Stage 7). If every Production slice shared one bucket
# under one key, then "who can read Production state" and "who can mint a certificate for any
# internal name" would be the same permission - the exact merge D36 exists to prevent. One
# bucket, two keys, two answerable questions.
#
# WHY IT IS CREATED HERE AND NOT BY THE pki/ SLICE. A backend is configured at `init`, before
# the slice has ever applied, so a key that pki/ creates does not exist at the moment its own
# backend needs it. That is step 2.2's chicken-and-egg in a second place, and it is cheaper to
# see it here than at `terraform init`. bootstrap/ creates it; pki/ only names it, through
# scripts/tfhygiene/backend.py, which already returns alias/awsds-prod-tfstate-pki for that
# one slice.
#
# WHAT MAKES THIS A CONTROL RATHER THAN A FOLDER, said plainly because the key alone is not
# one: the key policy below is the same IAM delegation as the account state key, so today
# InfrastructureAccess reaches both. The separation buys two things that a shared key cannot
# offer at any price - a kms:Decrypt ALARM that is meaningful (D36; an alarm on a key that also
# encrypts the state somebody reads to change a subnet is pure noise), and a single condition
# key to scope later, when Stage 7 knows who the CA operator is. Lesson 5 applies until then:
# this is a seam, not yet a wall.
#
# THE FILE EXISTS SEPARATELY so that main.tf stays byte-identical across the five bootstrap
# slices (step 3.5). It is the one entry in the parity check's allow-list.

resource "aws_kms_key" "tfstate_pki" {
  description = "Terraform state encryption - ${var.env} PKI slice only (D36)"

  enable_key_rotation     = true
  deletion_window_in_days = 30

  policy = jsonencode({
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
    Name = "awsds-${var.env}-tfstate-pki"
  }

  # A file copied into another account's bootstrap slice would silently create a second key
  # there, under a name that reads like Production's. Fail the plan instead.
  lifecycle {
    precondition {
      condition     = var.env == "prod"
      error_message = "pki-key.tf belongs to production/bootstrap/ only (step 3.4, D36)."
    }
  }
}

resource "aws_kms_alias" "tfstate_pki" {
  name          = "alias/awsds-${var.env}-tfstate-pki"
  target_key_id = aws_kms_key.tfstate_pki.key_id
}

output "state_kms_key_pki_arn" {
  description = "ARN of the key that encrypts production/pki/'s state, and nothing else. D36's kms:Decrypt alarm hangs on this key."
  value       = aws_kms_key.tfstate_pki.arn
}

output "state_kms_alias_pki" {
  description = "The alias production/pki/backend.hcl names."
  value       = aws_kms_alias.tfstate_pki.name
}
