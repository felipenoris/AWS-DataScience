# THE PROJECTS BUCKET (v0.3.2, 2026-08-22) - the wizard's "Amazon S3 bucket for projects",
# which the API-enabled configuration never had.
#
# THE THIRD RUNG OF THE SAME LADDER, and the pattern is now named: every field the console's
# Enable-Tooling wizard fills and PutEnvironmentBlueprintConfiguration does not REQUIRE is
# validated at environment DEPLOYMENT - and at TEARDOWN - not at Put. After the policy grants
# (v0.3.0) and the manage-access role (v0.3.1), the next project died with "Invalid S3 path
# provided null", and the stuck first project could not be deleted for the same reason. This
# bucket, wired into Tooling's regional parameters (blueprints.tf), is what "null" was.
#
# WHAT LANDS HERE: project artifacts and the portal's per-project shared storage, under the
# path the service owns - <bucket>/<domain-id>/<project-id>/<scope>/ (docs/SMUS.md §S3; the
# managed provisioning policy reaches content by that PATH SHAPE, `*/dzd*/<project>/...`, so
# the bucket NAME is free and follows the house convention rather than the wizard's
# amazon-sagemaker-* one - measured 2026-08-22 against SageMakerStudioProjectProvisioningRolePolicy v81).
#
# WHY THE HOUSE MODULE AND NOT THE SAMPLE'S SHAPE: aws-samples' SMUS-IaC bucket is versioning
# + BPA + SSE-KMS + TLS-only-policy + Retain; terraform-modules/s3-bucket is exactly that set
# with prevent_destroy instead of Retain, so the sample is evidence the shape suffices, not a
# second design. No expiration rule (the module default): project artifacts are not
# disposable, and the derived zone's D19 argument for expiry does not apply to them.
#
# THE KEY IS THE PROJECT CMK, and this is its first consumer (kms.tf's revision trigger,
# fired): the bucket's SSE and Tooling's KmsKeyArn parameter hand the blueprint-provisioned
# surface - artifacts here, volumes there - to the key that was cut for it at pass 1.
module "projects_bucket" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = "awsds-${var.env}-smus-projects"
  kms_key_arn = module.project_key.key_arn
}
