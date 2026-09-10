# Stage 6 step 3 - what a notebook may create, denied for all six persona sets at once.
#
# A module rather than a third data "aws_iam_policy_document" in this slice, because the same
# statements have to reach a second object in a different account: the D13 permissions boundary
# that terraform-modules/sagemaker-prereqs/ imposes on the roles the SMUS blueprint authors in
# Sandbox (Stage 6 step 2.1's "mirror both statements in 2.1's boundary"; the second Interactive
# account left at Stage 6b step 1.2). Two objects, two services, one intent (Lesson 33), so the
# structure and the values both live in terraform-modules/sagemaker-denies/ and both ends
# compose it.
#
# The cost: this slice - the entitlement plane, whose mistakes cost people their sign-in - has a
# module dependency it did not have before. It is pinned by tag like every other, and it creates
# nothing, the module having no resources at all, only a document.
#
# The persona sets need it even though the boundary covers the project roles, because the two
# govern different principals. A data scientist signed in to the console can call
# CreateTrainingJob directly, with their own network configuration and their own instance type,
# without any project role being involved. The persona set is what stops that; the boundary is
# what stops the same call made by the role SMUS provisions. Neither covers the other.
#
# Not here: the Athena Spark deny. That is an OU SCP (Stage 6 step 1.6,
# awsds-org-scp-ou-interactive) because it must reach every principal in the member accounts,
# project roles included; a copy here as well would be Lesson 20's cost, not defence in depth.

module "sagemaker_denies" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-denies?ref=sagemaker-denies-v0.2.0"

  # allowed_instance_types is not passed: the module owns the list, and the project boundary in
  # Sandbox - the one Interactive account with a sagemaker/ slice - omits it for the same reason.
}

# ---------------------------------------------------------------- open question 14, scoped
#
# 3.2 asks for the remote-IDE channel to be scoped rather than denied, and this is AWS's own
# documented SMUS shape: a user may attach only to a space that carries their project tag and
# their DataZone user id. Deny-with-conditions rather than allow, because these six sets are
# not where sagemaker:StartSession is granted - the project role is - and a deny is what
# survives someone else granting it.
#
# The residual, recorded for Stage 11's threat model rather than solved here: a remote session
# authenticates with IAM credentials even in an IdC domain, and persists up to 12 h after
# portal logout. The kill switch, if it is ever needed, is the sagemaker:RemoteAccess condition
# key on CreateSpace/UpdateSpace - one statement, not a redesign.
data "aws_iam_policy_document" "sagemaker_remote_ide" {

  statement {
    sid    = "DenyRemoteSessionOnSomeoneElsesSpace"
    effect = "Deny"

    actions   = ["sagemaker:StartSession"]
    resources = ["*"]

    condition {
      test     = "StringNotEquals"
      variable = "aws:ResourceTag/AmazonDataZoneProject"
      values   = ["$${aws:PrincipalTag/AmazonDataZoneProject}"]
    }
  }

  statement {
    sid    = "DenyRemoteSessionAsSomeoneElse"
    effect = "Deny"

    actions   = ["sagemaker:StartSession"]
    resources = ["*"]

    condition {
      test     = "StringNotEquals"
      variable = "aws:ResourceTag/AmazonDataZoneUser"
      values   = ["$${aws:PrincipalTag/datazone:userId}"]
    }
  }
}

# The two fragments this stage contributes, composed once so the six persona documents each
# add one entry rather than two, and so a seventh statement lands in all six by editing this
# list (the same argument policies-shared.tf makes for its own pair).
data "aws_iam_policy_document" "stage6_denies" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    module.sagemaker_denies.json,
    data.aws_iam_policy_document.sagemaker_remote_ide.json,
  ]
}
