# The account data CMK (Stage 5 pass 4, 2026-08-19). Encryption is per account: this account's
# data buckets encrypt under this account's key (docs/GOVERNANCE.md, "Encryption"). The alias is
# alias/awsds-<env>-data, the same pattern as the lake's alias/awsds-data-data - uniform because
# the rule is uniform, not because a catalog attribute carries it: no AWS mechanism ties a tag
# to a CMK, and the binding is the bucket's default-encryption configuration below.
#
# The derived zone this key was created for is gone (D19 as revised, 2026-08-26, re-homes the
# zone onto the SMUS project path). The key survives on a second consumer: the sandbox lake
# (Stage 16) encrypts under it, admitted through the additional-statements input below. In
# Development the key stands empty, held for the account's next data bucket - the explicit
# no-consumer branch verification (xx) of Stage 6 asks for.
#
# It is a different key from the lake's. The alternative, declined 2026-08-19, was to encrypt
# these buckets with the lake's own key:
#
#   - it puts a cross-account dependency under a local working bucket: every read of a query
#     result here becomes a KMS call into the account nobody signs into;
#   - the lake key's AllowProductionPickupDecryptViaS3 statement grants kms:Decrypt to
#     awsds-prod-job-exec with no bucket scoping - only kms:ViaService=s3 and the role ARN. Put
#     these buckets under that key and Production's job role holds Decrypt over this account's
#     materialised `restricted` results, with the S3 layer as the only thing left standing
#     (D31: a prefix deny-list does not survive forgetting).
#
# The split costs one thing: the key policy below has to be kept in step with the lake's when a
# new principal legitimately reads governed data in this account. That is one file, in one
# module, applied to every consumer (Lesson 14).

# The module address changed from zone_key to data_key (2026-08-19); this block keeps the
# applied key object in place and can be dropped once every caller has applied.
moved {
  from = module.zone_key
  to   = module.data_key
}

module "data_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-data"
  description = "Account data CMK - SSE-KMS for this account's data buckets (today: the sandbox lake in Sandbox; held empty in Development)"

  # The policy is passed, and its shape is the whole of D31. A permission set enumerates; a key
  # policy is default-deny, which is what makes it survive somebody forgetting to update a
  # prefix list. The decision's own words: kms:Decrypt to the project execution roles and
  # DataScientistAccess, and to nobody else.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        # Administration only - the cryptographic actions are absent.
        #
        # The module's default policy (and the lake key's first statement) grants the account
        # root `kms:*`, which is AWS's standard anti-lockout shape and means "the account's IAM
        # policies decide who may use this key". Here that would undo the statement below: any
        # IAM policy in this account could then grant kms:Decrypt, and the read control D31
        # describes would live in whatever policies happen to exist - the state that produced
        # D31 (an approver holding read on materialised `restricted` data because ReadOnlyAccess
        # carries s3:Get* and athena:GetQueryResults).
        #
        # So root keeps every action needed to manage the key - the anti-lockout guarantee AWS
        # warns about is intact, and Terraform can create, tag, re-policy and schedule deletion
        # - and holds no Encrypt, Decrypt, GenerateDataKey* or ReEncrypt*. Delegation to IAM is
        # therefore impossible for the operations that read data.
        #
        # What this does not close (Lesson 18): the administrator can call kms:PutKeyPolicy and
        # rewrite this statement. A policy never constrains the principal that authors it; what
        # it does is make the widening an edit, with a diff and a plan, instead of a side effect
        # of some other grant.
        Sid       = "EnableKeyAdministrationInThisAccount"
        Effect    = "Allow"
        Principal = { AWS = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root" }
        Action = [
          "kms:CancelKeyDeletion",
          "kms:Create*",
          "kms:Delete*",
          "kms:Describe*",
          "kms:Disable*",
          "kms:Enable*",
          "kms:Get*",
          "kms:List*",
          "kms:Put*",
          "kms:Revoke*",
          "kms:ScheduleKeyDeletion",
          "kms:TagResource",
          "kms:UntagResource",
          "kms:Update*",
        ]
        Resource = "*"
      },
      ],
      # No persona statement: AllowDataScientistUseViaS3 granted DataScientistAccess
      # Decrypt/GenerateDataKey via S3 for the derived zone (D31) and left with it on
      # 2026-08-26. The only bucket under this key now is the sandbox lake, which the persona
      # reaches only through vended, prefix-scoped access-role credentials (Stage 16 SS-G); the
      # statement would be a KMS-layer path around that vending door.
      #
      # The extension point arrived with Stage 16 pass 2.2 as a second statement rather than a
      # second element in a Principal list: the new reader is an account-local service role
      # whose ViaService pin and action set are its own, and folding it in would have made one
      # statement mean two things.
      #
      # Structure in the module, values in the slice - the split vpc-egress-v0.3.0 made for the
      # DNS allow-list: every consumer shares the shape of this key policy and none of them
      # shares its extra readers. The default is empty, so a consumer that adds nothing is
      # byte-identical to what it had before the input existed, and its plan after the tag bump
      # reads `No changes`.
      var.additional_data_key_policy_statements,
    )
  })
}
