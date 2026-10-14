# gitlab-anchors.tf - GitLab's [P] anchors (Stage 7 step 1.1), in foundation/ and not in tooling/:
# an anchor must survive the destruction of the slice it serves. Step 8.2's rehearsal destroys
# tooling/ on purpose, and every session destroys runners/, so a bucket or a secret container
# declared in either would go with it and take the only copy of something.
#
# What is here, and what each one keeps:
#
#   awsds-prod-gitlab-objects   GitLab's object storage - artifacts, LFS, uploads and the rest,
#                               one bucket with a prefix per object type (the consolidated form
#                               GitLab documents for the Linux package). Also `config/gitlab.rb`,
#                               the rendered configuration tooling/ publishes and the host fetches
#                               (1.3, decision 8), and `pki/`, the certificates production/pki/
#                               publishes (2.3). Nothing in it expires.
#   awsds-prod-gitlab-backup    `gitlab-backup create`'s upload target. Versioned, and every
#                               current object expires after 30 days: a backup is a copy of state
#                               that is still on the host, and the DLM snapshots of the data volume
#                               (tooling/) are the second copy.
#   awsds-prod-gitlab-secrets   the container for /etc/gitlab/gitlab-secrets.json. GitLab excludes
#                               that file from its own backups, and a backup restored without it
#                               cannot decrypt the database - so the first boot either restores it
#                               from here or pushes the generated one here (1.5). No value resource:
#                               the value never crosses Terraform.
#   awsds-prod-runner-token     the container for the runner's authentication token (`glrt-...`),
#                               minted in GitLab's UI once the instance exists (6.1) and read by
#                               every [E] runner at boot. No value resource, for the same reason.
#   awsds-prod-runner-test-token  the same for the test runner, the unprotected runner whose jobs
#                               hold no AWS identity (Stage 8 decision 11).
#   alias/awsds-prod-gitlab     the CMK under both buckets and the data volume. Its own key rather
#                               than the registry's, for D14's option-preservation reason: if the
#                               supply chain ever moves to a Shared Services account, GitLab leaves
#                               with its buckets and its key, and the registry with its own.
#
# The secrets carry a resource policy denying GetSecretValue to every principal but the one role
# that consumes each and InfrastructureAccess - the shape production/networking/'s host-key
# container settled (6c step 4.1). The role names are a contract with tooling/ and runners/, whose
# iam-role modules name them `awsds-<env>-gitlab`, `awsds-<env>-runner` and `awsds-<env>-runner-test`:
# a [P] slice cannot read a [D] or [E] slice's outputs, so the name is the seam.
#
# CostCenter: the two module-built buckets and the key take this slice's default_tags
# (`stage-03`), since neither module version pinned here takes a tag map (`s3-bucket-v0.4.0` does);
# the secrets, declared here, say `stage-07`.

locals {
  gitlab_anchor_tags = {
    CostCenter = "stage-07"
  }

  infrastructure_access_arn_pattern = "arn:${data.aws_partition.current.partition}:iam::*:role/aws-reserved/sso.amazonaws.com/*AWSReservedSSO_InfrastructureAccess_*"
}

module "gitlab_key" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/kms-key?ref=kms-key-v0.1.0"

  alias_name  = "awsds-${var.env}-gitlab"
  description = "GitLab's object storage, backups and data volume (Stage 7 step 1.1, D8, D14)"
}

module "gitlab_objects" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = "awsds-${var.env}-gitlab-objects"
  kms_key_arn = module.gitlab_key.key_arn
}

module "gitlab_backup" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/s3-bucket?ref=s3-bucket-v0.3.0"

  bucket_name = "awsds-${var.env}-gitlab-backup"
  kms_key_arn = module.gitlab_key.key_arn

  # A backup is disposable by design: the data is on the host's volume and in its daily snapshot.
  # 30 days of daily backups is what a restore has to choose from; a superseded version lives a
  # week, since `gitlab-backup` never overwrites a key.
  expiration_days                    = 30
  noncurrent_version_expiration_days = 7
}

# ------------------------------------------------------------- the two secret containers

resource "aws_secretsmanager_secret" "gitlab_secrets" {
  # checkov:skip=CKV2_AWS_57:no rotation - the value is GitLab's own secrets file, generated once by `gitlab-ctl reconfigure`; rotating it would orphan every encrypted column in the database
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - it delegates to IAM exactly as the host-key container does, and the containment is the resource policy below
  name        = "awsds-${var.env}-gitlab-secrets"
  description = "/etc/gitlab/gitlab-secrets.json - pushed by the GitLab host's first boot and read by every later first boot (Stage 7 step 1.5). Never written by Terraform. Excluded from GitLab's own backups by design, so losing it loses every backup at once."

  recovery_window_in_days = 30

  tags = merge(local.gitlab_anchor_tags, {
    Name = "awsds-${var.env}-gitlab-secrets"
  })
}

resource "aws_secretsmanager_secret_policy" "gitlab_secrets" {
  secret_arn = aws_secretsmanager_secret.gitlab_secrets.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptHostAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-gitlab",
              local.infrastructure_access_arn_pattern,
            ]
          }
        }
      }
    ]
  })
}

resource "aws_secretsmanager_secret" "runner_token" {
  # checkov:skip=CKV2_AWS_57:no rotation - the token is minted in GitLab's UI (Stage 7 step 6.1) and replaced there, never by a Lambda that GitLab does not know about
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - the containment is the resource policy below
  name        = "awsds-${var.env}-runner-token"
  description = "The build runner's authentication token (glrt-...), copied in by the user once the runner exists in GitLab (Stage 7 step 6.1) and read by every [E] runner at boot. Never written by Terraform."

  recovery_window_in_days = 30

  tags = merge(local.gitlab_anchor_tags, {
    Name = "awsds-${var.env}-runner-token"
  })
}

resource "aws_secretsmanager_secret_policy" "runner_token" {
  secret_arn = aws_secretsmanager_secret.runner_token.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptRunnerAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-runner",
              local.infrastructure_access_arn_pattern,
            ]
          }
        }
      }
    ]
  })
}

# The test runner's token (Stage 8 decision 11). Its role lives with its host in runners/, as the build
# runner's does: no trust policy names it, so nothing keeps its unique id.
resource "aws_secretsmanager_secret" "test_runner_token" {
  # checkov:skip=CKV2_AWS_57:no rotation - the token is minted in GitLab's UI (Stage 8 decision 11) and replaced there, never by a Lambda that GitLab does not know about
  # checkov:skip=CKV_AWS_149:the aws/secretsmanager managed key, deliberately - the containment is the resource policy below
  name        = "awsds-${var.env}-runner-test-token"
  description = "The test runner's authentication token (glrt-...), copied in by the user once the runner exists in GitLab (Stage 8 decision 11) and read by every [E] test runner at boot. Never written by Terraform."

  recovery_window_in_days = 30

  tags = {
    Name       = "awsds-${var.env}-runner-test-token"
    CostCenter = "stage-08"
  }
}

resource "aws_secretsmanager_secret_policy" "test_runner_token" {
  secret_arn = aws_secretsmanager_secret.test_runner_token.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyValueReadExceptTestRunnerAndInfrastructure"
        Effect    = "Deny"
        Principal = "*"
        Action    = "secretsmanager:GetSecretValue"
        Resource  = "*"
        Condition = {
          StringNotLike = {
            "aws:PrincipalArn" = [
              "arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:role/awsds-${var.env}-runner-test",
              local.infrastructure_access_arn_pattern,
            ]
          }
        }
      }
    ]
  })
}
