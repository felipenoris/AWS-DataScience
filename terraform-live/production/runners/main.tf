# production/runners/ - the build runner (Stage 7 step 6, decision 5), layer [E]: one m8i.xlarge in
# VPC-SharedServices' private tier, created by `make gitlab-up` and destroyed by `make gitlab-down`.
#
# It is the buildbox's successor (6.5): the same amd64 shape, in the same VPC, behind the same
# proxy, pushing with its own instance profile where the buildbox pushed with a token the operator
# carried in. The buildbox's role held no ecr: permission and that absence was its whole control;
# this role pushes by itself, so the control moves to who can run a job on it (GitLab's protected
# refs and project locks) and to the immutable tags.
#
# What it may do, and no more (6.1): push to the three image repositories, pull any image in this
# registry including through the pull-through cache prefixes, read its own registration token and
# the published CA root, and open the Session Manager channel. No deploy permission: the deploy
# runner and its roles are Stage 8's, kept apart so this role never accumulates them.
#
# How it authenticates to AWS: the instance profile is the machine credential (principle 2). A
# VPN-only GitLab cannot serve a JWKS that IAM can fetch, so OIDC federation is structurally
# unavailable here. How it authenticates to GitLab: an authentication token (`glrt-...`) minted in
# GitLab's UI and read at boot from foundation/'s secret container - never a tfvars, never a
# user-data literal. Each session's new instance registers as a new runner manager under the same
# token.
#
# How a job pushes: the role's credentials reach a job container through the metadata service (hop
# limit 2, below), and ECR's credential helper turns them into the registry login. The boot installs
# the helper at a pinned digest and the runner mounts it read-only into every job, because the build
# image, `moby/buildkit:rootless`, runs as UID 1000 and cannot install a client of its own. Every job
# also carries `ECR_REGISTRY`. The helper adds no reach: any job on this host can already read the
# role's credentials, which is why the runner is a protected project runner (runbook K).
#
# Every layer of the runner is a proxy client (6.2), because none of them inherits it: the boot
# script, the runner service, the docker daemon, the job containers and the build itself. The
# bypass list is egress/'s generated `no_proxy` (data.tf), never written by hand.

locals {
  zone        = var.zone_ids[var.zone_index]
  gitlab_url  = data.terraform_remote_state.tooling.outputs.gitlab_url
  gitlab_host = trimprefix(local.gitlab_url, "https://")
  proxy_url   = "http://proxy.awsds.internal:3128"
  no_proxy    = data.terraform_remote_state.egress.outputs.no_proxy

  cache_prefixes = data.terraform_remote_state.registry.outputs.pull_through_cache_prefixes
  cache_repo_arns = [
    for p in local.cache_prefixes :
    "arn:${data.aws_partition.current.partition}:ecr:${var.region}:${data.aws_caller_identity.current.account_id}:repository/${p}/*"
  ]

  ecr_registry = "${data.aws_caller_identity.current.account_id}.dkr.ecr.${var.region}.amazonaws.com"

  user_data = templatefile("${path.module}/user-data.sh.tftpl", {
    proxy_url             = local.proxy_url
    no_proxy              = local.no_proxy
    region                = var.region
    gitlab_url            = local.gitlab_url
    gitlab_host           = local.gitlab_host
    ca_root_param         = data.terraform_remote_state.pki.outputs.ca_root_parameter_name
    runner_token_secret   = data.terraform_remote_state.foundation.outputs.runner_token_secret_arn
    concurrent_jobs       = var.concurrent_jobs
    name_tag              = "awsds-${var.env}-runner"
    ecr_registry          = local.ecr_registry
    ecr_helper_version    = var.ecr_credential_helper.version
    ecr_helper_sha256     = var.ecr_credential_helper.sha256
    gitlab_runner_version = var.gitlab_runner_version
  })
}

# ------------------------------------------------------------------------------- the role (6.1)
module "role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = "awsds-${var.env}-runner"
  description = "GitLab build runner - Session Manager, push to the image repositories, pull through the cache, its token and the CA root; no deploy permission (Stage 7 step 6.1)"

  permissions_boundary = null

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowEc2Service"
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  managed_policy_arns = [
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ]

  inline_policies = {
    "registry" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        # Registry-scoped by AWS's design: the token is minted for the whole registry and the
        # action takes no resource (conventions 6, the perimeter document's reasoning).
        {
          Sid      = "MintTheRegistryToken"
          Effect   = "Allow"
          Action   = "ecr:GetAuthorizationToken"
          Resource = "*"
        },
        # Push and pull on every image repository this estate builds, the deploy image's among them.
        # `DescribeImageScanFindings` is what Stage 8's gate reads after a push.
        {
          Sid    = "PushAndPullTheImageRepositories"
          Effect = "Allow"
          Action = [
            "ecr:BatchCheckLayerAvailability",
            "ecr:InitiateLayerUpload",
            "ecr:UploadLayerPart",
            "ecr:CompleteLayerUpload",
            "ecr:PutImage",
            "ecr:BatchGetImage",
            "ecr:GetDownloadUrlForLayer",
            "ecr:DescribeImages",
            "ecr:DescribeRepositories",
            "ecr:ListImages",
            "ecr:DescribeImageScanFindings",
          ]
          Resource = values(data.terraform_remote_state.registry.outputs.ecr_repository_arns)
        },
        # The pull-through cache (5.2): a first pull imports the upstream image and creates the
        # repository under the prefix, so the puller needs both actions besides the pull itself.
        {
          Sid    = "PullThroughTheCache"
          Effect = "Allow"
          Action = [
            "ecr:BatchImportUpstreamImage",
            "ecr:CreateRepository",
            "ecr:BatchCheckLayerAvailability",
            "ecr:BatchGetImage",
            "ecr:GetDownloadUrlForLayer",
            "ecr:DescribeImages",
            "ecr:DescribeRepositories",
          ]
          Resource = local.cache_repo_arns
        },
      ]
    })

    # The release store (Stage 8 decision 20): the tag's store-bundle job puts the bundle `test` ran
    # under <application>/<tag>/ and deletes nothing, which the bucket's policy refuses anyway. The
    # data key comes from the registry key through S3.
    "releases" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "PutABundle"
          Effect   = "Allow"
          Action   = ["s3:PutObject", "s3:AbortMultipartUpload"]
          Resource = "${data.terraform_remote_state.registry.outputs.releases_bucket_arn}/*"
        },
        {
          Sid      = "EncryptItUnderTheRegistryKey"
          Effect   = "Allow"
          Action   = ["kms:GenerateDataKey", "kms:Decrypt"]
          Resource = data.terraform_remote_state.registry.outputs.registry_key_arn
          Condition = {
            StringEquals = { "kms:ViaService" = "s3.${var.region}.amazonaws.com" }
          }
        },
      ]
    })

    "boot" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ReadTheRegistrationToken"
          Effect   = "Allow"
          Action   = "secretsmanager:GetSecretValue"
          Resource = data.terraform_remote_state.foundation.outputs.runner_token_secret_arn
        },
        {
          Sid      = "ReadTheCaRoot"
          Effect   = "Allow"
          Action   = "ssm:GetParameter"
          Resource = data.terraform_remote_state.pki.outputs.parameter_arns["ca-root"]
        },
      ]
    })
  }
}

resource "aws_iam_instance_profile" "this" {
  name = "awsds-${var.env}-runner"
  role = module.role.role_name
}

# -------------------------------------------------------------------------- the host itself
resource "aws_instance" "runner" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same session buys nothing - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the private tier, which has no default route
  ami           = data.aws_ssm_parameter.al2023.insecure_value
  instance_type = var.instance_type
  ebs_optimized = true

  subnet_id                   = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids      = [data.terraform_remote_state.tooling.outputs.runner_security_group_id]
  iam_instance_profile        = aws_iam_instance_profile.this.name
  associate_public_ip_address = false

  user_data = local.user_data
  # The user data is the whole installation and runs at first boot only, so a change to it must
  # produce a new host rather than an attribute nobody applied. Cheap here: the slice is [E].
  user_data_replace_on_change = true

  # The boot's first read needs the role's inline policies, and the instance profile waits for the
  # role alone.
  depends_on = [module.role]

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    # 2, not 1: a job container reaches the instance role's credentials through the docker bridge,
    # one hop away, and a build that pushes to ECR from inside its container needs them. The
    # account default (the declarative policy) is 2 for the same reason.
    http_put_response_hop_limit = 2
  }

  root_block_device {
    encrypted             = true
    volume_size           = var.root_volume_size
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # The Name tag is a contract: ./aws/supplychain.py SC-10 finds the runner by `awsds-prod-runner*`,
  # and `./aws/egress.py` 6 is where a forgotten one shows up as this stage's likeliest leak.
  tags = {
    Name = "awsds-${var.env}-runner"
  }

  lifecycle {
    # The AMI is the parameter's value when the host is created (data.tf, Stage 8 decision 25).
    ignore_changes = [ami]
  }
}
