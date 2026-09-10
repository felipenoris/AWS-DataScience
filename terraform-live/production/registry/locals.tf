# The consumer set, resolved once.
#
# The ECR repository policies, the CodeArtifact domain policy, the CodeArtifact repository policies
# and the KMS key policy all enumerate the same accounts. They read the list from here rather than
# each building its own (Lesson 14).
#
# The root ARN is the account, not a principal. `arn:<partition>:iam::<id>:root` in a resource
# policy delegates to that account's own IAM: the consumer still has to grant the permission to a
# role there, which is the second half of the intersection (Lesson 28). It is the only form that
# survives the SSO role suffix being minted per account (1c decision 7).

locals {
  consumer_account_ids = [
    data.aws_caller_identity.sandbox.account_id,
    data.aws_caller_identity.staging.account_id,
  ]

  consumer_account_arns = [
    for id in local.consumer_account_ids :
    "arn:${data.aws_partition.current.partition}:iam::${id}:root"
  ]

  registry_key_alias = "awsds-${var.env}-registry"

  # The repository-level read document, written once and attached to both repositories so the two
  # cannot drift. `ReadFromRepository` is the action that serves a package; the Get/List actions
  # beside it are what a package manager calls while resolving a version.
  codeartifact_read_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowConsumerAccountsToReadPackages"
        Effect    = "Allow"
        Principal = { AWS = local.consumer_account_arns }
        Action = [
          "codeartifact:ReadFromRepository",
          "codeartifact:DescribePackageVersion",
          "codeartifact:GetPackageVersionAsset",
          "codeartifact:GetPackageVersionReadme",
          "codeartifact:ListPackages",
          "codeartifact:ListPackageVersions",
          "codeartifact:ListPackageVersionAssets",
          "codeartifact:ListPackageVersionDependencies",
        ]
        Resource = "*"
      },
    ]
  })
}
