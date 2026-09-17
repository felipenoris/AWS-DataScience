# The deny fragment every persona set carries - Stage 2 step 5.2.
#
# Written once and referenced six times (Lesson 14: a condition that must appear in N places by
# hand will be missing from one of them). Each set composes them through
# `source_policy_documents`, so a statement added here reaches all six in one diff and
# `terraform plan` shows six changes rather than five.
#
# No statement here tests the network a caller calls from: a person reaches AWS by identity
# from any network (D39).
#
# A deny and not a boundary. Step 5.2 asks for two of these denies to live in a permissions
# boundary, and decision 4 (settled 2026-08-16) defers the boundary object to Stage 3: a
# customer-managed boundary must exist as an aws_iam_policy of the same name and path in every
# account a set is provisioned into, and no governed account has a foundation/ slice yet, so
# the reference would fail provisioning per account, in an account nobody is watching. What is
# deferred is the container, not the content: the denies land here because the carve-outs they
# defend are attached. A boundary would make them inescapable; an inline deny makes them
# present, which is the whole of what a set can do to itself. Stage 3 adds one
# aws_ssoadmin_permissions_boundary_attachment per set.
#
# Not in this fragment (Lesson 20): anything the attached SCP set already denies for these
# principals. When two policies deny the same call only one of them is ever exercised, and a
# fragment that grew into a second copy of the ceiling would drift from it silently while
# looking like defence in depth. `s3:PutAccountPublicAccessBlock` is the concrete case - 1c step
# 7.5 denies it for every principal except InfrastructureAccess, and none of these six is that
# principal.

data "aws_iam_policy_document" "shared_denies" {

  # ---------------------------------------------------------------------------------------
  # 5.2's first requirement, and it is not about this account's resources at all.
  #
  # 1c's ceiling carves out two principals by name, and a carve-out cannot defend itself:
  #
  #   DenyAccountBpaChangeExceptInfrastructure  matches the ARN pattern
  #     `...:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*`
  #     (1c decision 7 - the one wildcard-account ARN in the whole design), so anybody who can
  #     mint a role under /aws-reserved/ with that name mints the exemption.
  #   DenyCatalogMaintenanceRunsExceptMaintenanceRole  names one exact role in Data Governance
  #     (D27), so anybody who can rewrite that role's trust policy hands themselves its
  #     exemption without ever having to be it. That is how IAM works and needs no
  #     verification.
  #
  # Neither is exploitable by the identities that exist today - iam:CreateRole lives with
  # InfrastructureAccess, which is already the exempted one, and the maintenance role does not
  # exist yet. Both become exploitable the moment this slice creates a set that is neither.
  #
  # The resource is `*` rather than the /aws-reserved/ path the step names, because a permission
  # set is one document provisioned into many accounts: a path-scoped ARN would have to leave
  # the account field as a wildcard, the form step 9.2 refuses, and 1c decision 7 is an
  # exception rather than a pattern. The literal is not written out here either - 9.2 scans .tf
  # files as text and grants no per-line exception, so even a comment naming the shape is a
  # finding. The way out is a broader deny rather than a narrower ARN: none of these six
  # personas has any business creating an IAM principal anywhere, so the blanket statement is
  # the honest one and it is strictly stronger than the one that was asked for.
  #
  # Each neighbouring action is a way to reach the same end - a principal, or a policy on one,
  # that this set did not have. iam:PassRole is not among them: it is scoped where it is granted
  # (conventions, IAM rules), and a blanket deny would break the job-submission path Stage 6 has
  # to grant. iam:CreateServiceLinkedRole is not here either - SageMaker creates its own on
  # first use, and denying it breaks Studio without closing anything.
  statement {
    sid    = "DenyIamPrincipalMutation"
    effect = "Deny"

    actions = [
      "iam:AddUserToGroup",
      "iam:AttachRolePolicy",
      "iam:AttachUserPolicy",
      "iam:CreateAccessKey",
      "iam:CreatePolicy",
      "iam:CreatePolicyVersion",
      "iam:CreateRole",
      "iam:CreateUser",
      "iam:DeleteRolePermissionsBoundary",
      "iam:DeleteRolePolicy",
      "iam:DeleteUserPermissionsBoundary",
      "iam:DetachRolePolicy",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:PutUserPermissionsBoundary",
      "iam:PutUserPolicy",
      "iam:SetDefaultPolicyVersion",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # No persona reads Terraform state. A state file carries every resource ARN, every account
  # id and whatever a resource happened to put in an attribute - the one object in this design
  # that describes the whole account. D31 named it explicitly for the deployment manager; it is
  # true of all six.
  #
  # The bucket wildcard is safe here and would not be in an allow. `awsds-*-tfstate` reaches
  # any bucket of that shape in any account on earth, because S3 names are global, which in a
  # deny also covers the state buckets of accounts vended after this was written (Staging, and
  # every Sandbox unit D35 adds). An allow written this way would be the defect.
  #
  # One permission is enough, measured: reading a state object needs s3:GetObject and
  # kms:Decrypt, because S3 calls KMS through a forward access session carrying the caller's
  # identity (step 2.7). Denying the S3 half closes the path without this fragment having to
  # know a key ARN it cannot resolve for six different accounts.
  statement {
    sid    = "DenyTerraformStateAccess"
    effect = "Deny"

    actions = ["s3:*"]

    resources = [
      "arn:${data.aws_partition.current.partition}:s3:::awsds-*-tfstate",
      "arn:${data.aws_partition.current.partition}:s3:::awsds-*-tfstate/*",
    ]
  }

  # ---------------------------------------------------------------------------------------
  # Nothing these six touch is ever made public, and the account-level block is not what says
  # so. Account-level Block Public Access is hand-managed (1c step 7.4) and covers buckets; it
  # says nothing about an ECR repository policy, and a bucket ACL or policy write is the thing
  # a persona set would plausibly be granted by accident later. This statement is about the
  # act, not about today's grants: none of the six is granted any of it right now, so it costs
  # nothing, and it is here so that the day a set acquires a legitimate s3:Put* grant, the
  # public half does not come with it.
  statement {
    sid    = "DenyMakingStorageOrImagesPublic"
    effect = "Deny"

    actions = [
      "ecr:DeleteRepositoryPolicy",
      "ecr:PutRegistryPolicy",
      "ecr:SetRepositoryPolicy",
      "s3:DeleteBucketPolicy",
      "s3:PutBucketAcl",
      "s3:PutBucketPolicy",
      "s3:PutBucketPublicAccessBlock",
      "s3:PutObjectAcl",
    ]

    resources = ["*"]
  }

  # ---------------------------------------------------------------------------------------
  # No persona stands up compute, and none of them opens a path to the internet. 1b step 3.4
  # names the failure this closes: an earlier draft gave DataScientistAccess `PowerUserAccess`
  # "until Stage 6", which would have let it create a public bucket or an internet-facing
  # instance and walk around the whole design for five stages. The public bucket is the
  # statement above; this is the other half.
  #
  # It is a forward deny, like the one above: none of the six is granted a single ec2 action
  # today, so nothing here fires. It is written now because Stage 6 grants Studio and Stage 9
  # grants job submission, and the moment a set acquires a legitimate compute grant is the
  # moment somebody has to remember that the egress half must not ride along with it. D5 owns
  # egress in the network; this says the same thing one layer up, where a persona could
  # otherwise create the network.
  statement {
    sid    = "DenyInternetFacingCompute"
    effect = "Deny"

    actions = [
      "ec2:AcceptVpcPeeringConnection",
      "ec2:AllocateAddress",
      "ec2:AssociateAddress",
      "ec2:AttachInternetGateway",
      "ec2:CreateEgressOnlyInternetGateway",
      "ec2:CreateInternetGateway",
      "ec2:CreateNatGateway",
      "ec2:CreateVpcPeeringConnection",
      "ec2:RunInstances",
    ]

    resources = ["*"]
  }
}
