# sandbox/foundation/persona-vending.tf - the object half of the persona's project-storage vending
# permission (user decision of 2026-08-23, strategy 1-A; consumer: `s3-read-write/`).
#
# A data scientist on a laptop reaches their SageMaker Unified Studio project's S3 path by asking S3
# Access Grants for credentials: the service assumes the location's role - which for a
# SMUS-provisioned location is the project role - and hands back a session scoped down to the granted
# prefix. The two actions here are that handshake and nothing else: `ListCallerAccessGrants` discovers
# which prefixes the caller may ask for, `GetDataAccess` performs the vend. Neither opens an object.
# What opens objects is a grant on the SMUS location, created per project, authorized per occurrence
# and revocable without touching this policy, so this document can exist in an account with no
# projects at all and grant nothing.
#
# It is a customer-managed policy rather than two more lines in the permission set because the
# permission set has no room: `DataScientistAccess` renders at 10217 characters against a 10240
# ceiling - 23 free, against the ~251 the statement costs. A permission set becomes an IAM role in
# every account it is provisioned into, where the inline-policy limit is 10240, so raising the
# threshold would move the failure to provisioning time, per account, silently
# (`terraform-live/identity/sso/README.md`, "The size discipline"). A managed policy is a separate
# object whose size does not count against that budget.
#
# It lives in foundation/ rather than sagemaker/ because a permission set that cannot find a policy
# it references fails to provision in that account, and the failure looks like an entitlement outage
# rather than a missing SMUS prerequisite. The object must outlive every slice that can be torn down;
# foundation/ is [P], and sagemaker/ is the slice that would be destroyed if SMUS were rolled back.
#
# The name is not composed here and carries `org`. A permission set references a customer-managed
# policy by name and one reference has to resolve in both member accounts, so an <env> token would
# make the two objects' names differ and the reference could match only one of them. The name is
# generated into this slice's tfvars from `scripts/tfhygiene/backend.py`, the one place it lives
# (Lesson 14), and that file carries the argument for `org`.
#
# The ARN is this account's own instance, read from the caller rather than from the roster.
# `default` is the service's singleton contract - one Access Grants instance per account x Region,
# named by the service. In an account where SMUS has created no instance yet, the policy names a
# resource that does not exist: an IAM policy may do that, and it matches nothing until the account's
# first project creates one.
#
# On-VPN only, by the persona's own pin. The set's `DenyControlPlaneOffVpn` denies `*` off the
# tunnel, and these calls carry none of its keys when the tunnel is down. On the tunnel, the vending
# path needs both of the deny's admitting branches, for two different reasons:
#   - `sts:GetCallerIdentity`, which the library calls to learn the account id s3control requires,
#     takes the VPC's `sts` interface endpoint (private DNS through the client's own resolver) and is
#     admitted by `aws:SourceVpc`. Before that branch existed the whole path was explicitly denied
#     here, with the tunnel up.
#   - `s3control` has no interface endpoint here, and that does not put it on the IGW: it takes the
#     S3 gateway endpoint, because `s3-control.<region>.amazonaws.com` resolves inside the ranges the
#     `pl-s3` prefix-list route captures - the 4d mechanism. So the vending calls were admitted by
#     the old `aws:SourceVpce` list all along, and are admitted by `aws:SourceVpc` now.
# Both bullets are read in CloudTrail from the first full run (2026-08-24T02:28Z): `GetDataAccess`
# carries `sourceIPAddress 10.20.160.87` - the WireGuard host's private address - with
# `vpcEndpointId vpce-0cc3e139c1167ca83`, a gateway id; `GetCallerIdentity` from the same session
# carries the same private address with `vpce-0b3231af86fbedd72`, the STS interface endpoint. Two
# doors, one session, and neither is the Elastic IP. Only `sts` ever needed the `aws:SourceVpc` swap:
# a library that did not call STS would have run on the old policy untouched.
#
# The credentials this vends are bearer for their duration once issued - they keep working off the
# tunnel until they expire. That is the OQ-14 shape (remote-IDE sessions), accepted there and here,
# and it is why the library asks for the shortest duration a task needs.


locals {
  # CostCenter per resource, as vpn-anchors.tf does: the slice's default_tags say stage-03, which is
  # true of what Stage 3 built here and false of this. The other mandatory tags still arrive from
  # default_tags, unrepeated.
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

  # The path is the default `/` and is left unwritten on both sides. A permission set's reference
  # carries a path as well as a name, and the provider defaults it to `/` there too, so leaving both
  # implicit keeps them equal by construction rather than by two literals agreeing (Lesson 14). A
  # path here would have to be mirrored there, and a mismatch is a provisioning failure, not a plan
  # failure.

  lifecycle {
    # The permission set references this object by name. Destroying it - or renaming it, which is a
    # destroy and a create - breaks provisioning of DataScientistAccess in this account until the
    # reference is removed first. The order out is identity/sso before foundation/, the reverse of
    # the order in.
    prevent_destroy = true
  }
}
