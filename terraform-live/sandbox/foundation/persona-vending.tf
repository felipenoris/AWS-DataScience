# sandbox/foundation/persona-vending.tf - the OBJECT half of the persona's project-storage
# vending permission (user decision of 2026-08-23, strategy 1-A; consumer: `s3-read-write/`).
#
# WHAT IT AUTHORIZES, AND WHAT IT DELIBERATELY DOES NOT. A data scientist on a laptop reaches
# their SageMaker Unified Studio project's S3 path by asking S3 Access Grants for credentials:
# the service assumes the LOCATION's role - which for a SMUS-provisioned location IS the project
# role - and hands back a session scoped down to the granted prefix. These two actions are that
# handshake and nothing else: `ListCallerAccessGrants` discovers which prefixes the caller may
# ask for, `GetDataAccess` performs the vend. NEITHER OPENS AN OBJECT. What opens objects is a
# GRANT on the SMUS location, created per project and authorized per occurrence, revocable
# without touching this policy - so this document can exist in an account with no projects at
# all and grant nothing, which is exactly the state Development is in today.
#
# WHY THIS IS A CUSTOMER-MANAGED POLICY RATHER THAN TWO MORE LINES IN THE PERMISSION SET. It was
# written inline first, and the slice's own size precondition refused it: `DataScientistAccess`
# renders at 10217 characters against a 10240 ceiling - 23 free, against the ~251 the statement
# costs. That ceiling is not a house preference. A permission set BECOMES AN IAM ROLE in every
# account it is provisioned into, where the inline-policy limit is 10240, so raising the
# threshold would only move the failure to provisioning time, per account, silently
# (`terraform-live/identity/sso/README.md`, "The size discipline": the answer is a
# customer-managed policy, not a larger threshold). A managed policy is a separate object whose
# size does not count against that budget - which is also why Stages 6 and 7, which still owe
# grants to this same set, now have somewhere to put them.
#
# WHY foundation/ AND NOT sagemaker/, WHICH IS WHERE THE SUBJECT MATTER LIVES. Because a
# permission set that cannot find a policy it references FAILS TO PROVISION in that account, and
# the failure looks like an entitlement outage rather than a missing SMUS prerequisite. So the
# object must outlive every slice that can be torn down; foundation/ is [P] and sagemaker/,
# whatever its layer today, is the slice that would be destroyed if SMUS were rolled back.
#
# THE NAME IS NOT COMPOSED HERE, AND IT CARRIES `org` ON PURPOSE. A permission set references a
# customer-managed policy BY NAME, and one reference has to resolve in BOTH member accounts - so
# an <env> token would make the two objects' names differ and the reference could match only one
# of them. The name is generated into this slice's tfvars from `scripts/tfhygiene/backend.py`,
# the one place it lives (Lesson 14), and that file carries the argument for `org`.
#
# THE ARN IS THIS ACCOUNT'S OWN, WHICH IS THE HALF THE INLINE VERSION COULD NOT HAVE. One
# document served N accounts there, so the instance had to be named for a specific account and
# the statement was Sandbox-only by construction. Here each account's copy names its own
# instance, read from the caller rather than from the roster - and `default` is the service's
# singleton contract (one Access Grants instance per account x Region, and the service names it),
# not a convention of ours. In Development that instance does not exist yet: an IAM policy may
# name a resource that does not exist, and it simply matches nothing until SMUS creates one with
# that account's first project.
#
# ON-VPN ONLY, BY THE PERSONA'S OWN PIN - AND THE FIRST RUN (2026-08-23) SPLIT THE QUESTION IN
# TWO RATHER THAN ANSWERING IT ONCE. The set's `DenyControlPlaneOffVpn` denies `*` off the
# tunnel, and these calls carry none of its keys when the tunnel is down, so that half is
# invariant. On the tunnel, the vending path needs BOTH of the deny's admitting branches, for
# two different reasons, and the run proved the first by failing on it:
#   - `sts:GetCallerIdentity`, which the library calls to learn the account id s3control
#     requires, takes the VPC's `sts` INTERFACE endpoint (private DNS through the client's own
#     resolver) and is admitted by `aws:SourceVpc`. Before that branch existed the whole path
#     was explicitly denied here - the defect this estate found the hard way, with the tunnel up.
#   - `s3control` has NO endpoint in this VPC (`vpc-egress`'s core + extra lists), so
#     `ListCallerAccessGrants` and `GetDataAccess` resolve publicly, leave by the IGW and are
#     admitted by `aws:SourceIp` - the Elastic IP.
# The second bullet is DERIVED FROM THE ENDPOINT LISTS, not yet read: the confirming event is
# `GetDataAccess` in CloudTrail, which should carry `sourceIPAddress = the Elastic IP` and NO
# `vpcEndpointId`, while `GetCallerIdentity` carries a private address and one. Replace this
# with that reading when it is taken (Lesson 33: the split is measured, never assumed) - and
# note the prediction is falsifiable in a useful direction, since an `s3control` endpoint
# appearing in `extra_services` later would move the call to the other branch silently.
#
# AND THE CREDENTIALS THIS VENDS ARE BEARER FOR THEIR DURATION once issued - they keep working
# off the tunnel until they expire. That is the OQ-14 shape (remote-IDE sessions), accepted there
# and accepted here for the same reason, and it is why the library asks for the shortest duration
# a task needs.


locals {
  # CostCenter per resource, as vpn-anchors.tf does and for the same reason: the slice's
  # default_tags say stage-03, which is true of what Stage 3 built here and false of this. The
  # other four mandatory tags still arrive from default_tags, unrepeated.
  persona_vending_tags = {
    CostCenter = "stage-06"
  }
}

data "aws_iam_policy_document" "persona_vending" {
  statement {
    sid    = "VendProjectStorageCredentials"
    effect = "Allow"

    actions = [
      "s3:GetDataAccess",
      "s3:ListCallerAccessGrants",
    ]

    resources = [
      "arn:${data.aws_partition.current.partition}:s3:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:access-grants/default",
    ]
  }
}

resource "aws_iam_policy" "persona_vending" {
  name        = var.persona_vending_policy_name
  description = "S3 Access Grants vending handshake for the data-scientist persona - referenced by name from DataScientistAccess (terraform-live/identity/sso). Opens no object: a per-project grant does."
  policy      = data.aws_iam_policy_document.persona_vending.json

  tags = merge(local.persona_vending_tags, {
    Name = var.persona_vending_policy_name
  })

  # THE PATH IS THE DEFAULT `/` AND IS LEFT UNWRITTEN ON BOTH SIDES. A permission set's reference
  # carries a path as well as a name, and the provider defaults it to `/` there too - so leaving
  # both implicit keeps them equal by construction instead of by two literals agreeing
  # (Lesson 14). A path here would have to be mirrored there, and a mismatch is a provisioning
  # failure, not a plan failure.

  lifecycle {
    # The permission set REFERENCES this object by name. Destroying it - or renaming it, which is
    # a destroy and a create - breaks provisioning of DataScientistAccess in this account until
    # the reference is removed first. The order out is therefore identity/sso before foundation/,
    # the reverse of the order in.
    prevent_destroy = true
  }
}
