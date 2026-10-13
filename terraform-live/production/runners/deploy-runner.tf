# deploy-runner.tf - the deploy runner (Stage 8 step 4.3), [E] like the build runner and raised by the
# same `make gitlab-up`, once var.deploy_image_digest pins its job image; until then the slice holds
# the build runner alone. Its role, instance profile and token container are production/foundation/'s
# anchors: a trust policy keeps a role's unique id, so the role outlives this host.
#
# GitLab's half makes it the deploy runner: a protected project runner of awsds/app-etl and
# awsds/dev-env, tag `awsds-deploy`, no untagged jobs (runbook K). This half: its jobs run the deploy
# image by digest and no other image, and every job carries an AWS configuration whose profiles are the
# deploy roles, each assumed with the instance's credentials two hops away (hop limit 2). No credential
# is written down, and nothing is exported into a job's shell (Lesson 25).

locals {
  deploy_runner_name = "awsds-${var.env}-runner-deploy"
  deploy_image       = var.deploy_image_digest == null ? null : "${data.terraform_remote_state.registry.outputs.ecr_deploy_repository_url}@${var.deploy_image_digest}"

  # One profile per deploy role, named after it.
  deploy_aws_config = join("\n", [
    for arn in values(data.terraform_remote_state.foundation.outputs.deploy_role_arns) : join("\n", [
      "[profile ${reverse(split("/", arn))[0]}]",
      "role_arn = ${arn}",
      "credential_source = Ec2InstanceMetadata",
      "region = ${var.region}",
      "sts_regional_endpoints = regional",
      "",
    ])
  ])
}

resource "aws_instance" "deploy_runner" {
  # checkov:skip=CKV_AWS_126:detailed monitoring on a host destroyed the same session buys nothing - CloudWatch spend is Stage 12's subject
  # checkov:skip=CKV_AWS_88:no public address is set here and none is inherited - the subnet is the private tier, which has no default route
  count = var.deploy_image_digest == null ? 0 : 1

  ami           = data.aws_ssm_parameter.al2023.value
  instance_type = var.deploy_runner_instance_type
  ebs_optimized = true

  subnet_id                   = data.terraform_remote_state.foundation.outputs.private_subnet_ids[local.zone]
  vpc_security_group_ids      = [data.terraform_remote_state.tooling.outputs.runner_security_group_id]
  iam_instance_profile        = data.terraform_remote_state.foundation.outputs.deploy_runner_instance_profile_name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/deploy-user-data.sh.tftpl", {
    proxy_url           = local.proxy_url
    no_proxy            = local.no_proxy
    region              = var.region
    gitlab_url          = local.gitlab_url
    gitlab_host         = local.gitlab_host
    ca_root_param       = data.terraform_remote_state.pki.outputs.ca_root_parameter_name
    runner_token_secret = data.terraform_remote_state.foundation.outputs.deploy_runner_token_secret_arn
    concurrent_jobs     = 1
    name_tag            = local.deploy_runner_name
    ecr_registry        = local.ecr_registry
    ecr_helper_version  = var.ecr_credential_helper.version
    ecr_helper_sha256   = var.ecr_credential_helper.sha256
    deploy_image        = local.deploy_image
    aws_config          = local.deploy_aws_config
  })
  user_data_replace_on_change = true

  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
    # 2, not 1: a job container reaches the instance's credentials through the docker bridge, one hop
    # away, and every deploy profile is assumed with them.
    http_put_response_hop_limit = 2
  }

  root_block_device {
    encrypted             = true
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # The Name tag is a contract: ./aws/cicd.py CI-1 finds the deploy runner by it, and
  # ./aws/supplychain.py SC-10's `awsds-prod-runner*` counts it among the runners.
  tags = {
    Name = local.deploy_runner_name
  }
}
