# STAGE 6 STEP 3 - what a notebook may create, denied for all six persona sets at once.
#
# WHY THIS IS A MODULE AND NOT A THIRD data "aws_iam_policy_document" IN THIS SLICE. The same
# statements have to reach a SECOND object in a different account: the D13 permissions boundary
# that terraform-modules/sagemaker-prereqs/ imposes on the roles the SMUS blueprint authors in
# Sandbox and Development (Stage 6 step 2.1's "mirror both statements in 2.1's boundary"). Two
# objects, two accounts, two services - and one intent, which is exactly the shape Lesson 33
# describes: one intent enforced in two places diverges, and sharing the VALUES while
# duplicating the STRUCTURE is what makes it look like it cannot. So the structure AND the
# values live in terraform-modules/sagemaker-denies/ and both ends compose it.
#
# THE COST OF THAT CHOICE, NAMED: this slice - the entitlement plane, whose mistakes cost
# people their sign-in - now has a module dependency, which it did not before. It is pinned by
# tag like every other, it creates nothing (the module has no resources at all, only a
# document), and the alternative was a second copy of five statements maintained by hand in the
# one file nobody wants to be wrong.
#
# WHY THE PERSONA SETS NEED IT AT ALL, given that the boundary covers the project roles: the
# two govern different principals. A data scientist signed in to the console can call
# CreateTrainingJob directly, with their own network configuration and their own instance type,
# without any project role being involved. The persona set is what stops that; the boundary is
# what stops the same call made by the role SMUS provisions. Neither covers the other.
#
# WHAT IS NOT HERE: the Athena Spark deny. That is an OU SCP (Stage 6 step 1.6,
# awsds-org-scp-ou-interactive) because it must reach every principal in the member accounts,
# project roles included - and putting a copy here as well would be Lesson 20's cost, not
# defence in depth.

module "sagemaker_denies" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/sagemaker-denies?ref=sagemaker-denies-v0.1.0"

  # allowed_instance_types is deliberately NOT passed: the module owns the list, and the
  # project boundary in the two Interactive accounts omits it for the same reason.
}

# ---------------------------------------------------------------- open question 14, scoped
#
# 3.2 asks for the remote-IDE channel to be SCOPED rather than denied, and this is AWS's own
# documented SMUS shape: a user may attach only to a space that carries THEIR project tag and
# THEIR DataZone user id. Deny-with-conditions rather than allow, because these six sets are
# not where sagemaker:StartSession is granted - the project role is - and a deny is what
# survives someone else granting it.
#
# THE RESIDUAL, RECORDED FOR STAGE 11's THREAT MODEL RATHER THAN SOLVED HERE: a remote session
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
# add ONE entry rather than two - and so a seventh statement lands in all six by editing this
# list (the same argument policies-shared.tf makes for its own pair).
data "aws_iam_policy_document" "stage6_denies" {
  # checkov:skip=CKV_AWS_356:one document, N accounts - no ARN can name the account; see the CKV_AWS_356 note in policies-data-scientists.tf
  source_policy_documents = [
    module.sagemaker_denies.json,
    data.aws_iam_policy_document.sagemaker_remote_ide.json,
  ]
}
