# The deny fragments every persona set carries - Stage 2 step 5.2 and Stage 4 step 8.2.
#
# WRITTEN ONCE AND REFERENCED SIX TIMES, which is the whole point (Lesson 14: a condition that
# must appear in N places by hand will be missing from one of them). Each set composes them
# through `source_policy_documents`, so a statement added here reaches all six in one diff and
# `terraform plan` shows six changes rather than five.
#
# TWO FRAGMENTS, NOT ONE, AND THE SPLIT IS NOT COSMETIC (Stage 4 decision 1, 8.2). The first is
# UNCONDITIONAL denies of acts nobody should perform - true forever, reviewable on their own
# terms, and nothing outside this file can change what they mean. The second is conditioned on
# an ADDRESS that is read from another account's state and that moves the day a VPN home is
# added or rebuilt. Merging them would put a statement whose truth depends on live
# infrastructure inside a document reviewed as if it were static, and the first plan that
# showed a diff in `shared_denies` would be read as "somebody changed the denies" when it was
# an Elastic IP. Separate documents, separate diffs, separate arguments.
#
# WHY A DENY AND NOT A BOUNDARY. Step 5.2 asks for two of these denies to live in a permissions
# BOUNDARY, and decision 4 (settled 2026-08-16) defers the boundary OBJECT to Stage 3: a
# customer-managed boundary must exist as an aws_iam_policy of the same name and path in EVERY
# account a set is provisioned into, and no governed account has a foundation/ slice yet - so
# the reference would fail provisioning per account, in an account nobody is watching. What is
# deferred is the container, not the content: the denies land here NOW, because the carve-outs
# they defend are attached NOW. A boundary would make them inescapable; an inline deny makes
# them present, which is the whole of what a set can do to itself. Stage 3 adds one
# aws_ssoadmin_permissions_boundary_attachment per set, as a diff, in the stage that can
# actually satisfy it.
#
# WHAT IS DELIBERATELY *NOT* IN THIS FRAGMENT, and the reasoning is Lesson 20 rather than
# tidiness: anything the attached SCP set already denies for these principals. When two
# policies deny the same call only one of them is ever exercised, and a fragment that grew into
# a second copy of the ceiling would drift from it silently while looking like defence in
# depth. `s3:PutAccountPublicAccessBlock` is the concrete case - 1c step 7.5 denies it for
# every principal except InfrastructureAccess, and none of these six is that principal.

data "aws_iam_policy_document" "shared_denies" {

  # ---------------------------------------------------------------------------------------
  # 5.2's first requirement, and it is not about this account's resources at all.
  #
  # 1c's ceiling carves out TWO principals by name, and a carve-out cannot defend itself:
  #
  #   DenyAccountBpaChangeExceptInfrastructure  matches the ARN PATTERN
  #     `...:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*`
  #     (1c decision 7 - the one wildcard-account ARN in the whole design), so anybody who can
  #     mint a role under /aws-reserved/ with that name mints the exemption.
  #   DenyCatalogMaintenanceRunsExceptMaintenanceRole  names one exact role in Data Governance
  #     (D27), so anybody who can rewrite that role's TRUST POLICY hands themselves its
  #     exemption without ever having to BE it. That one needs no verification: it is how IAM
  #     works.
  #
  # Neither is exploitable by the identities that exist today - iam:CreateRole lives with
  # InfrastructureAccess, which is already the exempted one, and the maintenance role does not
  # exist yet. BOTH BECOME EXPLOITABLE THE MOMENT THIS SLICE CREATES A SET THAT IS NEITHER,
  # which is now.
  #
  # WHY THE RESOURCE IS `*` RATHER THAN THE /aws-reserved/ PATH the step names. A permission
  # set is ONE document provisioned into MANY accounts, so a path-scoped ARN would have to
  # leave the ACCOUNT FIELD as a wildcard - the form step 9.2 refuses, for the reason that
  # makes 1c decision 7 an exception rather than a pattern. (The literal is not written out
  # here: 9.2 scans .tf files as text and grants no per-line exception, deliberately, so even
  # a comment naming the shape is a finding. That check is doing its job and this paragraph is
  # what it cost.) The way out is not a narrower ARN but a broader deny: none of these six
  # personas has any business creating an IAM principal ANYWHERE, so the honest statement is
  # the blanket one, and it is strictly stronger than the one that was asked for.
  #
  # THE NEIGHBOURS ARE HERE FOR A REASON, not for completeness. Each listed action is a way to
  # reach the same end - a principal, or a policy on one, that this set did not have.
  # iam:PassRole is NOT among them: it is scoped where it is granted (conventions, IAM rules),
  # and a blanket deny would break the job-submission path Stage 6 has to grant.
  # iam:CreateServiceLinkedRole is not here either - SageMaker creates its own on first use,
  # and denying it breaks Studio without closing anything.
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
  # NO PERSONA READS TERRAFORM STATE. A state file carries every resource ARN, every account
  # id and whatever a resource happened to put in an attribute - it is the one object in this
  # design that describes the whole account. D31 named it explicitly for the deployment
  # manager; it is true of all six.
  #
  # THE BUCKET WILDCARD IS SAFE HERE AND WOULD NOT BE IN AN ALLOW. `awsds-*-tfstate` reaches
  # any bucket of that shape in any account on earth, because S3 names are global - which in a
  # DENY means it also covers the state buckets of accounts vended after this was written
  # (Staging, and every Sandbox unit D35 adds). An ALLOW written this way would be the defect;
  # this is the same wildcard read in the direction that closes rather than opens.
  #
  # ONE PERMISSION IS ENOUGH, MEASURED: reading a state object needs s3:GetObject AND
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
  # NOTHING THESE SIX TOUCH IS EVER MADE PUBLIC, AND THE ACCOUNT-LEVEL BLOCK IS NOT WHAT SAYS
  # SO. Account-level Block Public Access is hand-managed (1c step 7.4) and covers buckets; it
  # says nothing about an ECR repository policy, and a bucket ACL or policy write is the thing
  # a persona set would plausibly be granted by accident later. This statement is about the
  # act, not about today's grants: none of the six is granted any of it right now, so it costs
  # nothing - and it is here so that the day a set acquires a legitimate s3:Put* grant, the
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
  # NO PERSONA STANDS UP COMPUTE, AND NONE OF THEM OPENS A PATH TO THE INTERNET. 1b step 3.4
  # names the failure this closes in its own words - an earlier draft gave DataScientistAccess
  # `PowerUserAccess` "until Stage 6", which would have let it create a public bucket or an
  # internet-facing instance and walk around the whole design for five stages. The public
  # bucket is the statement above; this is the other half.
  #
  # IT IS A FORWARD DENY, LIKE THE ONE ABOVE, and that is the only honest way to describe it:
  # none of the six is granted a single ec2 action today, so nothing here fires. It is written
  # now because Stage 6 grants Studio and Stage 9 grants job submission, and the moment a set
  # acquires a legitimate compute grant is the moment somebody has to remember that the egress
  # half must not ride along with it. D5 owns egress and it owns it in the NETWORK; this says
  # the same thing one layer up, where a persona could otherwise create the network.
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

# ============================================================ THE SECOND FRAGMENT - Stage 4 8.1
#
# THE OTHER HALF OF THE OBJECTIVE. docs/plan/objectives.md says all user access goes through the
# VPN. The tunnel alone delivers the DATA plane - a private network a laptop cannot reach
# without it - and delivers nothing at all about the CONTROL plane, which stays reachable from
# any network on earth with a valid SSO session until this statement lands. Stage 4's own
# framing: role 1 is held by construction, role 2 is held by THIS, and only this.
#
# WHY IT IS `*` ON `*` AND NOT A LIST OF SENSITIVE ACTIONS. A list would be an enumeration of
# what somebody thought of on the day they wrote it, and every service added afterwards arrives
# outside it. The requirement is not "these calls come from the VPN", it is "this person works
# from the VPN"; the honest statement is the total one, and the exceptions are then argued
# ONE BY ONE below rather than implied by an omission.
#
# THE THREE CONDITIONS ARE ANDed, and each one is doing different work:
#
#   NotIpAddress aws:SourceIp   the deny fires when the call did NOT come from a VPN home's
#                               Elastic IP. This only means anything because step 5 routes
#                               `0.0.0.0/0, ::/0` - a SPLIT tunnel would leave every API call
#                               on the laptop's own connection and this statement would then
#                               deny the user everything, tunnel up or not. Step 5 and step 8
#                               stand or fall together, which is why pass 3 runs after pass 2.
#
#   BoolIfExists aws:ViaAWSService = false      the carve-out, and NOT the one people expect.
#                               FORWARD ACCESS SESSIONS PRESERVE THE CALLER'S SOURCE IP - the
#                               deny-by-IP example in AWS's own data-perimeter guidance says so
#                               in a note - so an Athena-to-S3 flow would survive the bare
#                               condition on its own. What this defends is the on-behalf calls
#                               that are NOT FAS, where the service calls with its own network
#                               identity and the caller's IP is simply absent. `IfExists` is
#                               deliberate: a request context missing the key must not be read
#                               as `false` by accident.
#
#   StringNotEqualsIfExists aws:SourceVpc     added 2026-08-20 as aws:SourceVpce and WIDENED TO
#                               THE VPC ON 2026-08-23, when the endpoint-shaped form was
#                               measured one case short. Both halves below; the second is why
#                               the key changed, and locals.tf carries the same argument beside
#                               the values.
#                               THE ORIGINAL HALF CORRECTED A MEASURED
#                               DEFECT rather than extending the design (Lesson 33; stage 5
#                               log, 4d's controls entry). Tunnel traffic SPLITS BY
#                               DESTINATION in the VPN home's public subnet: S3 and DynamoDB
#                               leave through the [P] GATEWAY ENDPOINTS - their prefix-list
#                               routes are more specific than the IGW default - and arrive
#                               carrying the HOST'S PRIVATE ADDRESS plus aws:SourceVpce,
#                               never the Elastic IP. CloudTrail, one session: ListBuckets as
#                               a 10.20.x.x source plus the home's vpce id, the same
#                               minute's Glue call as the EIP. Without this test the
#                               statement explicitly denied every direct S3 call a persona
#                               made from INSIDE the perimeter - the scientist ran the query
#                               and could not fetch the CSV. The values are the VPN HOMES'
#                               endpoints (locals.tf), deliberately not the consumers'.
#                               IfExists holds the polarity: off-VPN traffic carries no such
#                               key, the test passes, the deny still fires.
#                               THE CASE IT MISSED, MEASURED 2026-08-23 WITH A NEGATIVE
#                               CONTROL: while `egress/` is up, every service holding an
#                               INTERFACE endpoint resolves - through the VPC resolver the
#                               client config points at - to a PRIVATE address, so the call
#                               takes that endpoint and presents ITS id. `dig sts...` answered
#                               10.20.12.229 while `dig s3...` answered public addresses (the
#                               gateway does no private DNS), and the persona was explicitly
#                               denied sts:GetCallerIdentity with the tunnel up and `curl
#                               checkip` reading the EIP - two true readings of two paths. An
#                               interface endpoint id CANNOT be listed here: they are [E], new
#                               on every `make up` (Lesson 3). So the key became aws:SourceVpc,
#                               which is [P] and SUBSUMES the gateway ids the branch used to
#                               carry - a request through any endpoint in the VPC presents
#                               both keys, so nothing that passed before stops passing.
#                               What it widens: anything inside the home's own VPC that wears
#                               a persona identity - and a persona role is reachable only
#                               through the IdC sign-in, never by an instance profile.
#                               APPLIED AND PROVEN 2026-08-20, and the proof shape matters to
#                               anyone re-touching this: the document changing is NOT the
#                               evidence. The statement is shared, so it was read back off BOTH
#                               PROVISIONED ROLES, and the behavioural check was the same call
#                               that diagnosed the defect (ListBuckets, explicit -> implicit
#                               deny) beside a CONTRAST PAIR - one action, a granted bucket and
#                               a non-granted one, one session - because "the network refuses
#                               S3" and "this bucket is not granted" are the same reading
#                               otherwise. Downstream consequence worth keeping: while this
#                               statement over-fired, every IMPLICIT deny behind it was
#                               unmeasurable, D13's whole mechanism included.
#
# WHAT THIS FRAGMENT IS NOT COMPOSED INTO, and it is the difference between a bad session and a
# bad month: InfrastructureAccess. Step 8.3 applies it to the six personas ONLY. Getting this
# wrong on a persona costs a data-scientist session; getting it wrong on the credential every
# Terraform apply in the organization runs as costs break-glass (D16). The seventh set gains
# the statement in a separate, deliberate diff, after the recorded control-plane pair - and
# note what the statement pins: a single Elastic IP and, since 2026-08-23, the home's VPC -
# both [P], allocated in foundation/ where `make down` cannot reach them (step 2.1; INT-05).
#
# WHAT IT DOES NOT PROTECT, said here rather than discovered later (8.4, INT-16): the Unified
# Studio portal is entered by an IdC SIGN-IN, not by an IAM call, and this statement does not
# reach that sign-in. MEASURED 2026-08-22 (Stage 6 step 1.7), both directions in ONE sitting:
# off the tunnel a persona session opened the portal and enumerated its project profiles, while
# the console refused logs:DescribeLogGroups "with an explicit deny in an identity-based
# policy" - the wording that names THIS statement and nothing else, because an SCP says
# "service control policy", a boundary says "permissions boundary", and no other deny these
# six documents carry reaches logs: at all. With the tunnel up, both surfaces were clean.
# So: VPN-only APIs and console. Do not write it up as more - which is what the sentence
# standing here while it was unverified already said, and the measurement did not change it.
data "aws_iam_policy_document" "control_plane_vpn" {

  statement {
    sid    = "DenyControlPlaneOffVpn"
    effect = "Deny"

    actions   = ["*"]
    resources = ["*"]

    condition {
      test     = "NotIpAddress"
      variable = "aws:SourceIp"
      values   = local.vpn_egress_cidrs
    }

    condition {
      test     = "StringNotEqualsIfExists"
      variable = "aws:SourceVpc"
      values   = local.vpn_egress_vpc_ids
    }

    condition {
      test     = "BoolIfExists"
      variable = "aws:ViaAWSService"
      values   = ["false"]
    }
  }
}
