# The Glue manage-access policy on this account's manage-access role, for Stage 18's window (step
# 7.2). DataLake's environment calls lakeformation:CreateLakeFormationOptIn as that role, which
# AmazonDataZoneSageMakerManageAccessRolePolicy, the one policy sagemaker-prereqs attaches, does not
# grant; AmazonDataZoneGlueManageAccessRolePolicy does, with the Lake Formation grants a subscription to
# a Glue table becomes. Without it the environment failed "because no identity-based policy allows the
# lakeformation:CreateLakeFormationOptIn action" (2026-10-20, c2ej62w956q2a8), as Sandbox's DataLake
# environments have since 2026-09-13. The role module attaches its policies one by one, so this
# attachment beside them is not undone by its next apply. Stage 18 step 8.6 destroys it with the slice.
#
# sagemaker-prereqs-v0.8.0 attaches the same policy inside the module. A bump of this slice past v0.6.0
# deletes this file in the same change, with a `moved` block to the module's attachment: two resources
# would hold one IAM attachment, and destroying either would detach it.

resource "aws_iam_role_policy_attachment" "manage_access_glue" {
  role = element(split("/", module.sagemaker_prereqs.manage_access_role_arn), 1)
  # Under the service-role/ path, unlike the SageMaker policy beside it.
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonDataZoneGlueManageAccessRolePolicy"
}
