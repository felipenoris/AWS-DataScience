# The two repositories Stage 6 step 5.0 pushes into (Stage 7 step 5.1, the 5.a half).
#
#   base      every application image is FROM base, so it gets a repository of its own even
#             though nothing pulls it cross-account today - Stage 8 builds both.
#   dev-env   the SMUS custom image (BYOI): the one artifact in this plan that reaches an
#             account without a pipeline, once, at Stage 6 step 5.0, and is replaced by Stage
#             8's pipeline building the same Dockerfile.
#
# 5.b adds what is not here: the pull-through cache rules (registry-scoped, and priming one needs
# Production's NAT up) and awsds-prod-ecr-app-etl. No application image exists before Stage 8, so
# that repository would have nothing pushing to it for two stages.
#
# Both carry the consumer pull policy. `base` carries it although design B's rebuild loop is `FROM
# base` on a runner in Production today: the moment a project builds its own image, the missing
# grant would read as a network fault. It is one list (locals.tf).

module "ecr_base" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/ecr-repo?ref=ecr-repo-v0.1.0"

  name                = "awsds-${var.env}-ecr-base"
  kms_key_arn         = module.registry_key.key_arn
  pull_principal_arns = local.consumer_account_arns
}

module "ecr_dev_env" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/ecr-repo?ref=ecr-repo-v0.1.0"

  name                = "awsds-${var.env}-ecr-dev-env"
  kms_key_arn         = module.registry_key.key_arn
  pull_principal_arns = local.consumer_account_arns
}
