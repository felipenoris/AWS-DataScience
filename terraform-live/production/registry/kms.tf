# THE SLICE'S OWN CMK (Stage 7 step 5.4, option-preservation measure 3) - one key for both
# registries, and the reason it is not the account's default key is D14: if the supply chain
# ever moves to a Shared Services account, this slice leaves and takes its key with it. A
# registry encrypted under a key that stays behind is a migration that has to re-encrypt every
# layer.
#
# THE POLICY IS THE HALF THAT MAKES THE CONSUMER LIST A CONTROL. ECR decrypts layers with this
# key on the PULLING side, so an account that may pull and cannot decrypt gets an AccessDenied
# on a path everyone believes is open - and the same is true of CodeArtifact assets. So the
# two grants have to agree, which is Lesson 28 stated as a build instruction rather than as a
# post-mortem.
#
# THREE STATEMENTS, AND THE VIA-SERVICE CONDITION IS WHY THE SECOND ONE IS NARROW: a consumer
# account holds Decrypt only when the call arrives THROUGH ecr or codeartifact in this region.
# Handed a ciphertext blob out of band, the same account can do nothing with it.

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
        Sid       = "AllowConsumerAccountsToDecryptThroughTheRegistries"
        Effect    = "Allow"
        Principal = { AWS = local.consumer_account_arns }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "kms:ViaService" = [
              "ecr.${var.region}.amazonaws.com",
              "codeartifact.${var.region}.amazonaws.com",
            ]
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
