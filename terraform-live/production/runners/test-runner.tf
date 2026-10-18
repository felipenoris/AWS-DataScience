# test-runner.tf - the test runner (Stage 8 decision 11), [E] like the other two and raised by the same
# `make gitlab-up`: the runner that serves an unprotected branch. Both the build runner and the deploy
# runner are protected, so without this one a job on a data scientist's branch never schedules.
#
# GitLab's half makes it the test runner: a project runner of awsds/app-etl, linked to awsds/dev-env and
# awsds/ci-gates and locked, NOT protected, tag `awsds-test`, no untagged jobs (runbook K). An
# unprotected runner takes jobs from any ref, so whoever can push a branch can run code here, and the
# host gives that code nothing: the metadata hop limit is 1, so the token's response dies at the docker
# bridge and a job container reads no AWS identity (Lesson 67). The host's own role, which the boot uses,
# holds the Session Manager channel, its registration token and the CA root, and no ECR permission: its
# jobs pull public images through the proxy, the build plane being `open` (D38).

locals {
  test_runner_name = "awsds-${var.env}-runner-test"
}

module "test_runner_role" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/iam-role?ref=iam-role-v0.1.0"

  name        = local.test_runner_name
  description = "GitLab test runner - Session Manager, its token and the CA root; nothing a job can reach (Stage 8 decision 11)"

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
    "boot" = jsonencode({
      Version = "2012-10-17"
      Statement = [
        {
          Sid      = "ReadTheRegistrationToken"
          Effect   = "Allow"
          Action   = "secretsmanager:GetSecretValue"
          Resource = data.terraform_remote_state.foundation.outputs.test_runner_token_secret_arn
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

resource "aws_iam_instance_profile" "test_runner" {
  name = local.test_runner_name
  role = module.test_runner_role.role_name
}

resource "aws_instance" "test_runner" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same session buys nothing - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the private tier, which has no default route
  ami           = data.aws_ssm_parameter.al2023.insecure_value
  instance_type = var.test_runner_instance_type
  ebs_optimized = true

  subnet_id                   = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids      = [data.terraform_remote_state.tooling.outputs.runner_security_group_id]
  iam_instance_profile        = aws_iam_instance_profile.test_runner.name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/test-user-data.sh.tftpl", {
    proxy_url             = local.proxy_url
    no_proxy              = local.no_proxy
    region                = var.region
    gitlab_url            = local.gitlab_url
    gitlab_host           = local.gitlab_host
    ca_root_param         = data.terraform_remote_state.pki.outputs.ca_root_parameter_name
    runner_token_secret   = data.terraform_remote_state.foundation.outputs.test_runner_token_secret_arn
    concurrent_jobs       = 2
    name_tag              = local.test_runner_name
    gitlab_runner_version = var.gitlab_runner_version
  })
  user_data_replace_on_change = true

  # The boot's first read needs the role's inline policy, and the instance profile waits for the
  # role alone.
  depends_on = [module.test_runner_role]

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    # 1, where the other two runners take 2: the boot on the host reads the role, and no job container
    # one hop away obtains a token. This line is the decision; ./aws/cicd.py CI-9 reads it back.
    http_put_response_hop_limit = 1
  }

  root_block_device {
    encrypted             = true
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # The Name tag is a contract: ./aws/cicd.py CI-9 finds the test runner by it, and
  # ./aws/supplychain.py SC-10's `awsds-prod-runner*` counts it among the runners.
  tags = {
    Name = local.test_runner_name
  }

  lifecycle {
    # The AMI is the parameter's value when the host is created (data.tf, Stage 8 decision 25).
    ignore_changes = [ami]
  }
}
