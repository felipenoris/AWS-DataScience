# THE SLICE'S OWN CMK (Stage 7 step 5.4, option-preservation measure 3) - one key for both
# registries, and the reason it is not the account's default key is D14: if the supply chain
# ever moves to a Shared Services account, this slice leaves and takes its key with it. A
# registry encrypted under a key that stays behind is a migration that has to re-encrypt every
# layer.
#
# THE CONSUMER GRANT IS CODEARTIFACT'S ONLY, AND THAT IS A CORRECTION (2026-08-21, the Stage 6
# plan review). This statement named `ecr` beside `codeartifact` on the reasoning that a puller
# must be able to decrypt what it pulls - Lesson 28's shape, and wrong here. **ECR creates two
# grants on this key FOR ITSELF at repository creation and makes the Decrypt call on the
# caller's behalf**, so a pulling principal, cross-account included, needs the repository policy
# and no KMS grant at all (docs/REFERENCES.md, "ECR encryption at rest - who decrypts a pull" -
# the same page that deleted half of Stage 9's old step 7). The KMS permissions ECR documents
# belong to whoever CREATES or DELETES a repository, which is this account.
#
# CODEARTIFACT IS DIFFERENT AND KEEPS THE GRANT: its assets are encrypted under the domain key
# and a cross-account read decrypts them as the reader, so there the two grants genuinely have
# to agree - an account that may read and cannot decrypt gets an AccessDenied on a path
# everybody believes is open.
#
# WHAT IS NOT MEASURED, said plainly rather than left to look settled: `SC-7`'s cross-account
# ECR read is `describe-images`, which decrypts no layer, so it proves the repository policy and
# says nothing about the key either way. **Stage 6 step 5.1's first real cross-account PULL is
# the measurement** - and if it fails on KMS, the AWS page above is wrong and the fix is one
# service name on the line below.
#
# THREE STATEMENTS, AND THE VIA-SERVICE CONDITION IS WHY THE SECOND ONE IS NARROW: a consumer
# account holds Decrypt only when the call arrives THROUGH codeartifact in this region. Handed
# a ciphertext blob out of band, the same account can do nothing with it.

module "registry_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = local.registry_key_alias
  description = "ECR image layers and CodeArtifact assets for the supply chain (D14, Stage 7 step 5)."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "EnableIamPolicyDelegationInThisAccount"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action    = "kms:*"
        Resource  = "*"
      },
      {
        Sid       = "AllowConsumerAccountsToDecryptThroughCodeArtifact"
        Effect    = "Allow"
        Principal = { AWS = local.consumer_account_arns }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = ["codeartifact.${var.region}.amazonaws.com"]
          }
        }
      },
      {
        Sid       = "AllowTheRegistryServicesToUseTheKeyOnOurBehalf"
        Effect    = "Allow"
        Principal = { Service = ["ecr.amazonaws.com", "codeartifact.amazonaws.com"] }
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*",
          "kms:DescribeKey",
          "kms:CreateGrant",
        ]
        Resource = "*"
        Condition = {
          StringEquals = { "aws:SourceAccount" = data.aws_caller_identity.current.account_id }
        }
      },
    ]
  })
}
