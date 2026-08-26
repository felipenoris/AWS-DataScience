# The Access Grants location and the standing per-group grants (Stage 16 pass 3), decision 3(a).
#
# WHY THESE ARE IN TERRAFORM AND THE PER-PROJECT GRANTS ARE NOT. The objects here are STANDING:
# one location for the bucket, one grant per tenant group, and both outlive every project. A
# standing object defended only by a register row is a standing object nobody notices the
# deletion of - so these get a plan. The per-project grants are the opposite: they are born
# with an S3 connection and die with the project, and the runbook (§W / §R) owns them by hand.
#
# THE INSTANCE IS NOT HERE, AND THAT IS THE ONE THING TO NOT "FIX". It was created by SageMaker
# Unified Studio on 2026-08-22, the service keeps writing to it, and adopting a service-owned
# object into Terraform would put a plan in a race with its author (Lesson 17). data.tf READS
# it instead, which is enough: the read is what makes the trust's aws:SourceArn a real pin, and
# what makes this file fail by name if the instance is ever deleted.
#
# WHAT A GRANT DOES AND DOES NOT DO. It does not attach a policy to anybody. It says: this
# grantee may ask GetDataAccess for this sub-prefix, and get back a session of the location's
# role, scoped down to that sub-prefix. So the reach of a row below is
# (this grant) AND (the access role's permissions) AND (the key policy) - three documents in
# two slices, which is why no single file in this repository answers "what can this group do".

resource "aws_s3control_access_grants_location" "lake" {
  account_id     = data.aws_caller_identity.current.account_id
  iam_role_arn   = module.lake_access_role.role_arn
  location_scope = "s3://awsds-${var.env}-lake/"

  tags = {
    Name = "awsds-${var.env}-lake"
  }

  # The role must be assumable by the service BEFORE the location is registered - S3 validates
  # the trust at registration, which is the same "the validator is the deploy" shape Stage 6
  # met at every wizard field (Lesson 39). module.lake_access_role is already an implicit
  # dependency through iam_role_arn; the bucket is not, and is named so that a location can
  # never be registered over a scope that does not exist.
  depends_on = [module.lake]
}

# ------------------------------------------------------------------- one grant per tenant
#
# THE GRANTEE IS THE GROUP'S RESERVED ROLE, decision 2(a): the grain the 2026-08-24 vending
# decision already accepted. It is membership-blind WITHIN a group - every human holding
# DataScientistAccess in this account reaches the data-scientists prefix and no other - and the
# group is exactly the unit the requirement names, so per-group separation costs nothing new.
# Per-human attribution would need directory grantees, which need an Identity Center
# association on this SMUS-born instance: open question 13's decision, not this stage's.
#
# READWRITE, not READ + a second row: the requirement is read AND write on the group's own
# folder, and one permission value that says so is one row to revoke.
#
# TWO OF THE THREE ROWS HAVE NO LAPTOP PATH TODAY, and it is not a defect of this file.
# awsds-org-project-storage-vending - the customer-managed policy that lets a persona call
# GetDataAccess at all - is referenced by name from DataScientistAccess only. The other two
# groups reach their prefix from inside a wired project and not from a laptop until
# identity/sso/ extends that reference, which is an act taken when a second group's laptop path
# is actually wanted (step 0.2). The grants are written now anyway: the prefix contract is the
# bucket's layout, and a layout with a hole in it invites somebody to fill the hole differently.

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

    # one() fails on zero and on two - a tenant naming a permission set that is not
    # provisioned in this account is an invented row, and must fail the PLAN rather than
    # create a grant to nothing (step 0.2: the roster is derived, not invented).
    grantee_identifier = one(data.aws_iam_roles.tenant[each.key].arns)
  }

  tags = {
    Name = "awsds-${var.env}-lake-${each.key}"
  }
}
