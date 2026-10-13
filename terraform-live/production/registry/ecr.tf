# The two repositories Stage 6 step 5.0 pushes into (Stage 7 step 5.1, the 5.a half).
#
#   base      every application image is FROM base, so it gets a repository of its own even
#             though nothing pulls it cross-account today - Stage 8 builds both.
#   dev-env   the SMUS custom image (BYOI): the one artifact in this plan that reaches an
#             account without a pipeline, once, at Stage 6 step 5.0, and is replaced by Stage
#             8's pipeline building the same Dockerfile.
#
# 5.b (Stage 7, 2026-10-12) added the pull-through cache rules (cache.tf) and awsds-prod-ecr-app-etl
# below: Stage 7 step 6.4's first pipeline is what pushes into it.
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

# The first application repository (Stage 7 step 5.1, the 5.b half): one per application, the same
# three settings. No cross-account pull principal - decision 7's reading: a deployment target pulls
# an application image through Stage 8's own deploy grant, never through the consumer map, which
# keeps Staging off the dev-env image and the package proxy. The runner pushes in this account by
# its identity policy (6.1).
module "ecr_app_etl" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/ecr-repo?ref=ecr-repo-v0.1.0"

  name                = "awsds-${var.env}-ecr-app-etl"
  kms_key_arn         = module.registry_key.key_arn
  pull_principal_arns = []
}

# The deploy image (Stage 8 steps 3.1 and 4.3): the toolbox the deploy runner's jobs run in, built by the
# GitLab project awsds/deploy-image on the build runner. No cross-account pull principal: only the
# deploy runner in this account pulls it, by its identity policy (production/foundation/'s anchors), and
# by digest.
module "ecr_deploy" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/ecr-repo?ref=ecr-repo-v0.1.0"

  name                = "awsds-${var.env}-ecr-deploy"
  kms_key_arn         = module.registry_key.key_arn
  pull_principal_arns = []
}
