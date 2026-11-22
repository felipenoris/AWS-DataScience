# Stage 9 steps 4.1 and 4.2 - the outputs bucket (Stage 10 decision 17) and the results bucket, under
# the account data CMK, the shape of production/data/buckets.tf.
#
#   awsds-<env>-outputs   application outputs: the release's tree under applications/<app>/<tag>/
#                         (Stage 10 decision 1), the inbox under inbox/<app>/, each application's
#                         work/ and outbox/ under <app>/
#   awsds-<env>-derived   query results, results/ expiring after var.results_expiration_days
#                         (decision 11); its policy is the module's alone, since Athena writes it as the
#                         caller through the service and the persona reads it through Athena
#
# The outputs bucket's perimeter: a request made through no gateway endpoint of this VPC, by no service
# and by no named principal is denied (INT-05). The named principals reach it from any network (D39)
# and each is held to its share by a statement of its own: the persona reads everything and writes
# nothing (8.4); the release job's role writes applications/ and inbox/; InfrastructureAccess
# administers the bucket.

module "outputs_bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.4.0"

  bucket_name = local.outputs_bucket_name
  kms_key_arn = module.consumer_data.data_key_arn

  additional_policy_statements = [
    {
      Sid       = "DenyOutsideTheJobNetwork"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = "s3:*"
      Resource  = [local.outputs_bucket_arn, "${local.outputs_bucket_arn}/*"]
      Condition = {
        StringNotEquals = { "aws:SourceVpce" = data.terraform_remote_state.vpc.outputs.s3_gateway_endpoint_id }
        BoolIfExists = {
          "aws:ViaAWSService"         = "false"
          "aws:PrincipalIsAWSService" = "false"
        }
        ArnNotLike = {
          "aws:PrincipalArn" = [
            local.infrastructure_access_role_arn,
            local.data_scientist_role_arn,
            local.deploy_role_arn,
          ]
        }
      }
    },
    {
      Sid       = "DenyThePersonaAnyWrite"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      NotAction = ["s3:GetObject", "s3:GetObjectVersion", "s3:ListBucket", "s3:GetBucketLocation"]
      Resource  = [local.outputs_bucket_arn, "${local.outputs_bucket_arn}/*"]
      Condition = {
        ArnLike = { "aws:PrincipalArn" = local.data_scientist_role_arn }
      }
    },
    {
      Sid       = "DenyTheReleaseRoleAnythingButItsObjects"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      NotAction = ["s3:PutObject", "s3:GetObject", "s3:GetObjectVersion", "s3:ListBucket", "s3:GetBucketLocation"]
      Resource  = [local.outputs_bucket_arn, "${local.outputs_bucket_arn}/*"]
      Condition = {
        ArnLike = { "aws:PrincipalArn" = local.deploy_role_arn }
      }
    },
    {
      Sid         = "DenyTheReleaseRoleObjectsOutsideItsPrefixes"
      Effect      = "Deny"
      Principal   = { AWS = "*" }
      Action      = ["s3:PutObject", "s3:GetObject", "s3:GetObjectVersion"]
      NotResource = [for p in local.deploy_prefixes : "${local.outputs_bucket_arn}/${p}*"]
      Condition = {
        ArnLike = { "aws:PrincipalArn" = local.deploy_role_arn }
      }
    },
    {
      Sid       = "DenyTheReleaseRoleListingsOutsideItsPrefixes"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = "s3:ListBucket"
      Resource  = local.outputs_bucket_arn
      Condition = {
        ArnLike       = { "aws:PrincipalArn" = local.deploy_role_arn }
        StringNotLike = { "s3:prefix" = [for p in local.deploy_prefixes : "${p}*"] }
      }
    },
    # Stage 10 decision 12: what a release wrote under applications/ is changed only by the next release,
    # so no job and no workflow rewrites the code it runs.
    {
      Sid       = "DenyWritesToApplicationsButTheReleaseRoles"
      Effect    = "Deny"
      Principal = { AWS = "*" }
      Action    = ["s3:PutObject", "s3:DeleteObject"]
      Resource  = "${local.outputs_bucket_arn}/applications/*"
      Condition = {
        ArnNotLike = { "aws:PrincipalArn" = [local.deploy_role_arn, local.infrastructure_access_role_arn] }
      }
    },
  ]
}

# Stage 10 decision 16's bridge: an Object Created under inbox/<app>/ starts the consuming chain, and S3
# sends its events to the account's default bus only through this switch.
resource "aws_s3_bucket_notification" "outputs_to_eventbridge" {
  bucket      = module.outputs_bucket.bucket_name
  eventbridge = true
}

module "derived_bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.4.0"

  bucket_name     = local.derived_bucket_name
  kms_key_arn     = module.consumer_data.data_key_arn
  expiration_days = var.results_expiration_days
}
