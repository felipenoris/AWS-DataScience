# apply-application.tf - Stage 8 step 4.1's application grant, the deploy role's inline
# apply-application: what <folder>/app/* hands to a job service and the application's tables it
# creates in app_outputs (step 3.2, Stage 9 steps 2.5 and 4.1). Lake Formation's half, CREATE_TABLE on
# app_outputs and ALTER and DROP on its tables, is in each account's data/lakeformation.tf.
#
# The statements one account adds are apply_application_in_this_account's: deploy-role.tf's in
# Staging, deploy-anchors.tf's in Production.
#
# The same file in staging/foundation/ and production/foundation/, byte for byte
# (./scripts/check-copies.py).
data "aws_iam_policy_document" "apply_application" {
  source_policy_documents = [data.aws_iam_policy_document.apply_application_in_this_account.json]

  statement {
    sid       = "PassTheJobRole"
    effect    = "Allow"
    actions   = ["iam:PassRole"]
    resources = ["arn:${local.partition}:iam::${local.account_id}:role/awsds-${var.env}-job-exec"]

    condition {
      test     = "StringEquals"
      variable = "iam:PassedToService"
      values   = ["glue.amazonaws.com", "sagemaker.amazonaws.com"]
    }
  }

  statement {
    sid    = "ManageTheApplicationTables"
    effect = "Allow"
    actions = [
      "glue:CreateTable",
      "glue:DeleteTable",
      "glue:GetDatabase",
      "glue:GetTable",
      "glue:GetTables",
      "glue:UpdateTable",
    ]
    resources = [
      "arn:${local.partition}:glue:${local.region_account}:catalog",
      "arn:${local.partition}:glue:${local.region_account}:database/app_outputs",
      "arn:${local.partition}:glue:${local.region_account}:table/app_outputs/*",
    ]
  }
}
