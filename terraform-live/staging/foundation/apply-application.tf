# apply-application.tf - Stage 8 step 4.1's application grant, the deploy role's inline
# apply-application: what <folder>/app/* declares - the application's Glue jobs, the job role it hands to
# a job service - and the application's tables it creates in app_outputs (steps 3.2 and 3.6, Stage 9
# steps 2.5 and 4.1); and the model chain's jobs, which read the training jobs and serve a model by a
# batch transform as the job role (Stage 10 steps 5.2 and 5.4, scripts/model-chain.py). Lake
# Formation's half, CREATE_TABLE on app_outputs and ALTER and DROP on its tables, is in each account's
# data/lakeformation.tf. The leg's read of the account's egress slice before it writes is here too
# (Stage 8 decision 27, scripts/check-egress.py): the two calls below, and the slice's state among the
# role's state_read_keys.
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

  # The application slice's Glue jobs, by name (Stage 10 decision 20 (a)): awsds-<env>-app-etl and the
  # jobs it suffixes, Production's warehouse load among them; a second application names its own.
  statement {
    sid    = "ManageTheApplicationGlueJob"
    effect = "Allow"

    actions = [
      "glue:CreateJob",
      "glue:DeleteJob",
      "glue:GetJob",
      "glue:GetTags",
      "glue:TagResource",
      "glue:UntagResource",
      "glue:UpdateJob",
    ]
    resources = [
      "arn:${local.partition}:glue:${local.region_account}:job/awsds-${var.env}-app-etl",
      "arn:${local.partition}:glue:${local.region_account}:job/awsds-${var.env}-app-etl-*",
    ]
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

  # Stage 8 steps 3.1 and 3.6 (decision 27): the leg reads the account's egress slice before it writes,
  # and raises nothing. DescribeVpcEndpoints takes no resource; the association is read by its id.
  statement {
    sid       = "DescribeTheEgressEndpoints"
    effect    = "Allow"
    actions   = ["ec2:DescribeVpcEndpoints"]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheDnsFirewallAssociation"
    effect    = "Allow"
    actions   = ["route53resolver:GetFirewallRuleGroupAssociation"]
    resources = ["arn:${local.partition}:route53resolver:${local.region_account}:firewall-rule-group-association/*"]
  }

  # Stage 10 step 5.4: the newest completed training job of app-etl-train, the model it made served by a
  # batch transform under the job role, the model deleted after. ListTrainingJobs takes no resource.
  statement {
    sid       = "FindTheTrainingJobs"
    effect    = "Allow"
    actions   = ["sagemaker:ListTrainingJobs"]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheTrainingJobs"
    effect    = "Allow"
    actions   = ["sagemaker:DescribeTrainingJob"]
    resources = ["arn:${local.partition}:sagemaker:${local.region_account}:training-job/app-etl-train-*"]
  }

  statement {
    sid    = "ServeTheModels"
    effect = "Allow"
    actions = [
      "sagemaker:CreateModel",
      "sagemaker:CreateTransformJob",
      "sagemaker:DeleteModel",
      "sagemaker:DescribeModel",
      "sagemaker:DescribeTransformJob",
      "sagemaker:StopTransformJob",
    ]
    resources = [
      "arn:${local.partition}:sagemaker:${local.region_account}:model/app-etl-*",
      "arn:${local.partition}:sagemaker:${local.region_account}:transform-job/app-etl-*",
    ]
  }

  # The evaluation beside a model and a transform's output, read; the outputs bucket's policy holds
  # this role to its prefixes, models/ among them (data/locals.tf).
  statement {
    sid       = "ReadTheModelFiles"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["arn:${local.partition}:s3:::awsds-${var.env}-outputs/models/*"]
  }
}
