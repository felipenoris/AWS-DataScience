# The consumer set, resolved once.
#
# ONE LIST, FOUR POLICIES. The ECR repository policies, the CodeArtifact domain policy, the
# CodeArtifact repository policies and the KMS key policy all enumerate the same accounts, and
# Lesson 14 is the reason they read it from here rather than each building its own: a
# condition that must appear in N places by hand will be missing from one of them.
#
# THE ROOT ARN IS THE ACCOUNT, NOT A PRINCIPAL. `arn:<partition>:iam::<id>:root` in a resource
# policy means "delegate to that account's own IAM" - the consumer still has to grant the
# permission to a role there, which is the second half of the intersection (Lesson 28). It is
# the only form that survives the SSO role suffix being minted per account (1c decision 7).

locals {
  consumer_account_ids = [
    data.aws_caller_identity.sandbox.account_id,
    data.aws_caller_identity.development.account_id,
  ]

  consumer_account_arns = [
    for id in local.consumer_account_ids :
    "arn:${data.aws_partition.current.partition}:iam::${id}:root"
  ]

  registry_key_alias = "awsds-${var.env}-registry"

  # The repository-level READ document, written once and attached to both repositories -
  # the two are byte-identical by design, and a second copy is how they stop being.
  # `ReadFromRepository` is the one that actually serves a package; the four Get/List
  # actions beside it are what a package manager calls while resolving a version.
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
