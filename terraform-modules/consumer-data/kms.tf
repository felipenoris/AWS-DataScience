# The zone CMK, in THIS account (Stage 5 pass 4, 2026-08-19 - the user's synthesis).
#
# WHY THE NAME CARRIES THE ZONE AND NOT THE WORD "derived". Encryption granularity is the
# `security-zone` dimension's job (Stage 5 decision 2, docs/GOVERNANCE.md) and that rule does
# not stop at the lake's account line: the derived copy of a zn-lab table is still zn-lab data
# - D19 practice (v) says the output of a query over `restricted` data IS `restricted`, and a
# copy that inherits the classification inherits the zone with it. So the alias is
# alias/awsds-<env>-zn-lab, matching alias/awsds-data-zn-lab in the lake, and a second zone is
# a second key HERE TOO, by the same rule rather than by a new decision.
#
# AND IT IS A DIFFERENT KEY FROM THE LAKE'S, DELIBERATELY - same zone, different account. The
# alternative considered and declined (2026-08-19) was to encrypt these buckets with the lake's
# own alias/awsds-data-zn-lab. Three things decided against it, and the second is the one that
# matters:
#
#   - it puts a CROSS-ACCOUNT dependency under a local working bucket: every read of a query
#     result here becomes a KMS call into the account nobody signs into;
#   - the lake key's AllowProductionPickupDecryptViaS3 statement grants kms:Decrypt to
#     awsds-prod-job-exec with NO bucket scoping - only kms:ViaService=s3 and the role ARN. Put
#     these buckets under that key and Production's job role holds Decrypt over this account's
#     materialised `restricted` results, with the S3 layer as the only thing left standing.
#     D31 exists precisely because "a prefix deny-list does not survive forgetting";
#   - an LF-Tag attaches to a database, table or column, and the derived zone has none of the
#     three - so `security-zone` would be governing a bucket no tag can ever be assigned to.
#
# WHAT THE SPLIT COSTS, said here rather than discovered: the key policy below has to be kept
# in step with the lake's when a new principal legitimately reads governed data in this
# account. That is one file, in one module, applied to every consumer - which is the direction
# Lesson 14 asks for.

module "zone_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-zn-lab"
  description = "zn-lab security zone in this account - SSE-KMS for the derived zone (query results, materialised copies, notebook scratch)"

  # THE POLICY IS PASSED, AND ITS SHAPE IS THE WHOLE OF D31. A permission set enumerates; a key
  # policy is default-deny, which is what makes it survive somebody forgetting to update a
  # prefix list. The decision's own words: kms:Decrypt to the project execution roles and
  # DataScientistAccess, and to nobody else.
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
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
      {
        # THE READ CONTROL. SSE-KMS needs GenerateDataKey to write and Decrypt to read, and
        # Athena needs both under the caller's own identity - it writes results through a
        # forward access session carrying the querying principal, so there is no separate
        # service grant to make here.
        #
        # kms:ViaService pins both to S3: the persona cannot use this key to decrypt anything
        # that is not an S3 object, which keeps the key from becoming general-purpose the first
        # time somebody wants to encrypt something else with "the account's key".
        #
        # DELIBERATELY ABSENT AND NAMED SO (Lesson 5): DeploymentManagerAccess and
        # GovernanceManagerAccess - D31 is the decision that an approver does not read the data
        # it approves on. The project execution roles of Stage 6 are absent because they do not
        # exist yet (INT-15); step 9.3 asks for an extension point rather than a redesign, and
        # this statement is it - a second element in the Principal list.
        Sid       = "AllowDataScientistUseViaS3"
        Effect    = "Allow"
        Principal = { AWS = var.data_scientist_role_arn }
        Action    = ["kms:Decrypt", "kms:GenerateDataKey", "kms:DescribeKey"]
        Resource  = "*"
        Condition = {
          StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
        }
      },
    ]
  })
}
