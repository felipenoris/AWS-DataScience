# deploy-role.tf - awsds-deploy-sandbox-test, the role the pipeline's `bundle` job assumes to make a
# release's bundle with the CI/CD CLI (Stage 19 decision 19 (c); Stage 8 decision 19 created the role
# for the `test` deploy that job replaces, and its name is that decision's). It is this account's
# second deploy role, beside sandbox/foundation/'s awsds-deploy-devenv-sandbox (step 4.2).
#
# `bundle --targets dev` reads the `dev` project the manifest names, its membership, its environments
# and its connections, and, with `content.catalog` enabled, exports the catalog that project owns
# (Stage 19 decision 18 (d)): the reads below. It writes nothing in this account: the bundle's files
# are the tag's own, read beside the manifest, and the role deploys nothing and runs nothing. No action
# below takes a resource type but GetDomain, so DataZone's own membership layer is what confines the
# reads to one project: the role is made a member of the `dev` project in the portal, by hand, and of
# no other (EXC-17).
#
# The ceiling adds, to the module's denies, every role change and every PassRole. No state, since the
# role applies no slice (refusal 8), and no application ceiling.
#
# The trust names the runner's role in the runner's home, built from the runner's name and the home's
# account id, which the alias below resolves (aws/INDEX.md rule 1). production/foundation/ must exist
# first: IAM refuses a trust policy naming a role that does not.

provider "aws" {
  alias   = "deploy_runner"
  region  = var.region
  profile = one([for k, v in var.deploy_runner : v.profile])
}

data "aws_caller_identity" "deploy_runner" {
  provider = aws.deploy_runner
}

locals {
  deploy_runner_role_arn = "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.deploy_runner.account_id}:role/awsds-${one([for k, v in var.deploy_runner : v.env])}-runner-deploy"
}

module "deploy_role_test" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/deploy-role?ref=deploy-role-v0.5.0"

  name            = var.deploy_role_name
  description     = "The bundle of an application's release (Stage 19 decision 19 (c)) - assumed only by the deploy runner's role; reads the dev project and its catalog with the CI/CD CLI, deploys nothing and applies no slice"
  env             = var.env
  boundary_name   = "awsds-${var.env}-deploy-test-boundary"
  runner_role_arn = local.deploy_runner_role_arn
  state_prefixes  = []

  inline_policies = {
    "project-reads" = data.aws_iam_policy_document.bundle_reads.json
  }

  boundary_denies_json = data.aws_iam_policy_document.bundle_ceiling.json
}

# The CLI resolves the domain, the project, its membership, its environments and its connections
# before it writes the bundle. None of these reads takes a resource type but GetDomain, and the domain
# lives in the domain account (SMUS_DOMAIN in scripts/tfhygiene/backend.py), so its ARN names the
# domain by id in any account: an aliased identity of that account would cost this slice a third
# profile at plan for one read.
data "aws_iam_policy_document" "bundle_reads" {
  # checkov:skip=CKV_AWS_356:DataZone's project and catalog reads take no resource type, so only "*" matches them; DataZone confines them by project membership

  statement {
    sid    = "ReadTheProjectItsMembersAndItsConnections"
    effect = "Allow"
    actions = [
      "datazone:GetConnection",
      "datazone:GetEnvironment",
      "datazone:GetGroupProfile",
      "datazone:GetProject",
      "datazone:GetUserProfile",
      "datazone:ListConnections",
      "datazone:ListDomains",
      "datazone:ListEnvironmentBlueprints",
      "datazone:ListEnvironments",
      "datazone:ListProjectMemberships",
      "datazone:ListProjects",
    ]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheDomain"
    effect    = "Allow"
    actions   = ["datazone:GetDomain"]
    resources = ["arn:${data.aws_partition.current.partition}:datazone:${var.region}:*:domain/${var.datazone_domain_id}"]
  }

  # The catalog export (the CLI 1.0.9's helpers/catalog_export.py, read 2026-11-11): Search over the
  # assets, data products, glossaries and terms the project owns, GetAsset and GetDataProduct for
  # each, and SearchTypes for its own form and asset types.
  statement {
    sid    = "ExportTheCatalogTheProjectOwns"
    effect = "Allow"
    actions = [
      "datazone:GetAsset",
      "datazone:GetDataProduct",
      "datazone:Search",
      "datazone:SearchTypes",
    ]
    resources = ["*"]
  }
}

# The denies particular to this role, merged into the module's ceiling: no role created, changed,
# removed or passed. The identity policy above grants reads alone; the ceiling is what an identity
# policy widened later would still meet.
data "aws_iam_policy_document" "bundle_ceiling" {
  statement {
    sid    = "DenyEveryRoleChangeAndEveryPassRole"
    effect = "Deny"
    actions = [
      "iam:AttachRolePolicy",
      "iam:CreateRole",
      "iam:DeleteRole",
      "iam:DeleteRolePermissionsBoundary",
      "iam:DeleteRolePolicy",
      "iam:DetachRolePolicy",
      "iam:PassRole",
      "iam:PutRolePermissionsBoundary",
      "iam:PutRolePolicy",
      "iam:TagRole",
      "iam:UntagRole",
      "iam:UpdateAssumeRolePolicy",
      "iam:UpdateRole",
      "iam:UpdateRoleDescription",
    ]
    resources = ["*"]
  }
}
