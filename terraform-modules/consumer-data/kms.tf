# The account data CMK (Stage 5 pass 4, 2026-08-19; revised the same day - the security-zone
# dimension withdrawn, encryption is per ACCOUNT. RE-SCOPED 2026-08-26: the derived zone it was
# created for is REMOVED - D19 as revised, the zone re-homed onto the SMUS project path - and
# the key SURVIVES because it picked up a second consumer before the first one died: the
# sandbox lake (Stage 16) encrypts under it, admitted through the additional-statements input
# below. In Development the key stands EMPTY, held for the account's next data bucket - the
# explicit no-consumer branch verification (xx) of Stage 6 asks for, dated here.)
#
# ONE DATA CMK PER ACCOUNT (docs/GOVERNANCE.md "Encryption"): this account's data buckets
# encrypt under this account's key. The alias is alias/awsds-<env>-data, the same pattern as
# the lake's alias/awsds-data-data - uniform because the rule is uniform, not because a
# catalog attribute carries it: no AWS mechanism ties a tag to a CMK, and the binding is the
# bucket's default-encryption configuration below.
#
# AND IT IS A DIFFERENT KEY FROM THE LAKE'S, DELIBERATELY. The alternative considered and
# declined (2026-08-19) was to encrypt these buckets with the lake's own key. Two things
# decided against it, and the second is the one that matters:
#
#   - it puts a CROSS-ACCOUNT dependency under a local working bucket: every read of a query
#     result here becomes a KMS call into the account nobody signs into;
#   - the lake key's AllowProductionPickupDecryptViaS3 statement grants kms:Decrypt to
#     awsds-prod-job-exec with NO bucket scoping - only kms:ViaService=s3 and the role ARN. Put
#     these buckets under that key and Production's job role holds Decrypt over this account's
#     materialised `restricted` results, with the S3 layer as the only thing left standing.
#     D31 exists precisely because "a prefix deny-list does not survive forgetting".
#
# WHAT THE SPLIT COSTS, said here rather than discovered: the key policy below has to be kept
# in step with the lake's when a new principal legitimately reads governed data in this
# account. That is one file, in one module, applied to every consumer - which is the direction
# Lesson 14 asks for.

# The module address moved with the 2026-08-19 revision (zone_key -> data_key); the block
# keeps the applied key object in place and can be dropped once every caller has applied.
moved {
  from = module.zone_key
  to   = module.data_key
}

module "data_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-data"
  description = "Account data CMK - SSE-KMS for this account's data buckets (today: the sandbox lake in Sandbox; held empty in Development)"

  # THE POLICY IS PASSED, AND ITS SHAPE IS THE WHOLE OF D31. A permission set enumerates; a key
  # policy is default-deny, which is what makes it survive somebody forgetting to update a
  # prefix list. The decision's own words: kms:Decrypt to the project execution roles and
  # DataScientistAccess, and to nobody else.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        # ADMINISTRATION ONLY - THE CRYPTOGRAPHIC ACTIONS ARE DELIBERATELY ABSENT, and this is
        # the difference between D31 being a control and being a comment.
        #
        # The module's DEFAULT policy (and the lake key's first statement) grants the account
        # root `kms:*`, which is AWS's standard anti-lockout shape and means "the account's IAM
        # policies decide who may use this key". Here that would undo the statement below: any
        # IAM policy in this account could then grant kms:Decrypt, and the read control D31
        # describes would live in whatever policies happen to exist - exactly the state that
        # produced D31 (an approver holding read on materialised `restricted` data because
        # ReadOnlyAccess carries s3:Get* and athena:GetQueryResults).
        #
        # So root keeps every action needed to MANAGE the key - the anti-lockout guarantee AWS
        # warns about is intact, and Terraform can create, tag, re-policy and schedule deletion
        # - and holds no Encrypt, Decrypt, GenerateDataKey* or ReEncrypt*. Delegation to IAM is
        # therefore impossible for the operations that read data.
        #
        # WHAT THIS DOES NOT CLOSE, stated rather than implied (Lesson 18): the administrator
        # can call kms:PutKeyPolicy and rewrite this statement. A policy never constrains the
        # principal that authors it; what it does is make the widening an EDIT, with a diff and
        # a plan, instead of a side effect of some other grant.
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
      # THE PERSONA STATEMENT (AllowDataScientistUseViaS3) LEFT THIS POLICY ON 2026-08-26, and
      # its absence is now the control rather than the leftover. It granted the persona
      # Decrypt/GenerateDataKey via S3 because the derived zone encrypted here and the persona
      # read it (D31). With the zone re-homed onto the SMUS project path (D19 revision), the
      # only bucket left under this key is the sandbox lake - which the persona reaches ONLY
      # through vended, prefix-scoped access-role credentials (Stage 16 SS-G). Keeping the
      # statement would have granted the persona a KMS-layer path around that vending door.
      # THE EXTENSION POINT THE STATEMENT ABOVE ASKED FOR, delivered on 2026-08-26 by the first
      # caller that needed it (Stage 16 pass 2.2). Its comment predicted the shape - "a second
      # element in the Principal list" - and the shape that actually arrived is a second
      # STATEMENT, because the new reader is not the persona: it is an account-local service
      # role whose ViaService pin and whose action set are its own, and folding it into the
      # persona's Principal list would have made one statement mean two things.
      #
      # STRUCTURE IN THE MODULE, VALUES IN THE SLICE - the split vpc-egress-v0.3.0 made for the
      # DNS allow-list, for the same reason: every consumer shares the shape of this key policy
      # and none of them shares its extra readers. The default is EMPTY, so a consumer that adds
      # nothing is byte-identical to what it had before the input existed, and its plan after
      # the tag bump reads `No changes` - which is the proof the default protected it, not a
      # hope about it.
      var.additional_data_key_policy_statements,
    )
  })
}
