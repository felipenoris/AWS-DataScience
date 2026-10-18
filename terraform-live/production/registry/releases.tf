# releases.tf - the release store (Stage 8 decision 20, D41): awsds-<env>-releases, where a tag's
# pipeline puts the bundle the `test` project ran, under <application>/<tag>/, and where a promotion
# leg reads it (Stage 10). It is this slice's because the bundle is a supply-chain artifact beside the
# images (D14), encrypted under the same key.
#
# The build runner's role writes it (production/runners/), the deploy runner's role reads it
# (production/foundation/), and nobody deletes: the bucket policy denies every delete, and the two
# configuration writes that amount to one, to all but InfrastructureAccess, so a release's bytes
# outlive any job, under the versioning the module turns on. GitLab's package registry was the
# alternative, refused because any Developer of a project can delete a package there.

locals {
  releases_bucket_name = "awsds-${var.env}-releases"
  releases_bucket_arn  = "arn:${data.aws_partition.current.partition}:s3:::${local.releases_bucket_name}"

  infrastructure_access_arn_pattern = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*"
}

module "releases_bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.4.0"

  bucket_name = local.releases_bucket_name
  kms_key_arn = module.registry_key.key_arn

  # The bucket's own ARN is built from its name: the module's policy cannot read the module's output.
  additional_policy_statements = [
    {
      Sid       = "DenyDeletesExceptInfrastructure"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action = [
        "s3:DeleteBucket",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutBucketVersioning",
        "s3:PutLifecycleConfiguration",
      ]
      Resource = [local.releases_bucket_arn, "${local.releases_bucket_arn}/*"]
      Condition = {
        StringNotLike = { "aws:PrincipalArn" = local.infrastructure_access_arn_pattern }
      }
    },
  ]

  tags = {
    CostCenter = "stage-08"
  }
}
