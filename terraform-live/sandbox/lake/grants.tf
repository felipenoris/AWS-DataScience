# The Access Grants location and the standing per-group grants (Stage 16 pass 3), decision 3(a).
#
# The objects here are standing - one location for the bucket, one grant per tenant group - and both
# outlive every project, so they get a plan. The per-project grants are born with an S3 connection
# and die with the project; the runbook (§W / §R) owns them by hand.
#
# The instance is not declared here. SageMaker Unified Studio created it on 2026-08-22 and the
# service keeps writing to it, so adopting it would put a plan in a race with its author (Lesson 17).
# data.tf reads it instead: the read is what makes the trust's aws:SourceArn a real pin, and what
# makes this file fail by name if the instance is ever deleted.
#
# A grant attaches no policy to anybody. It says: this grantee may ask GetDataAccess for this
# sub-prefix, and get back a session of the location's role, scoped down to that sub-prefix. The
# reach of a row below is (this grant) AND (the access role's permissions) AND (the key policy) -
# three documents in two slices, so no single file here answers "what can this group do".

resource "aws_s3control_access_grants_location" "lake" {
  account_id     = data.aws_caller_identity.current.account_id
  iam_role_arn   = module.lake_access_role.role_arn
  location_scope = "s3://awsds-${var.env}-lake/"

  tags = {
    Name = "awsds-${var.env}-lake"
  }

  # S3 validates the trust at registration, so the role must be assumable by the service before the
  # location is registered (Lesson 39). module.lake_access_role is already an implicit dependency
  # through iam_role_arn; the bucket is not, and is named so that a location can never be registered
  # over a scope that does not exist.
  depends_on = [module.lake]
}

# ------------------------------------------------------------------- one grant per tenant
#
# The grantee is the group's reserved role, decision 2(a) - the grain the 2026-08-24 vending
# decision accepted. It is membership-blind within a group: every human holding DataScientistAccess
# in this account reaches the data-scientists prefix and no other. Per-human attribution would need
# directory grantees, which need an Identity Center association on this SMUS-born instance: open
# question 13's decision, not this stage's.
#
# READWRITE, not READ plus a second row: the requirement is read and write on the group's own
# folder, and one permission value that says so is one row to revoke.
#
# Two of the three rows have no laptop path today. awsds-org-project-storage-vending - the
# customer-managed policy that lets a persona call GetDataAccess at all - is referenced by name from
# DataScientistAccess only. The other two groups reach their prefix from inside a wired project and
# not from a laptop until identity/sso/ extends that reference (step 0.2). The grants are written now
# because the prefix contract is the bucket's layout.

resource "aws_s3control_access_grant" "tenant" {
  for_each = var.tenants

  account_id                = data.aws_caller_identity.current.account_id
  access_grants_location_id = aws_s3control_access_grants_location.lake.access_grants_location_id
  permission                = "READWRITE"

  access_grants_location_configuration {
    s3_sub_prefix = "${each.key}/*"
  }

  grantee {
    grantee_type = "IAM"

    # one() fails on zero and on two: a tenant naming a permission set that is not provisioned in
    # this account must fail the plan rather than create a grant to nothing (step 0.2 - the roster
    # is derived, not invented).
    grantee_identifier = one(data.aws_iam_roles.tenant[each.key].arns)
  }

  tags = {
    Name = "awsds-${var.env}-lake-${each.key}"
  }
}
