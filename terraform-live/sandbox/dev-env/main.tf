# The house image, registered for this account (Stage 6d step 2).
#
# Three objects, and the boundary between them is what the rest of the design leans on:
#
#   image          the named thing a domain attaches. Account-scoped, versionless. This slice's
#   image version  one immutable pointer at one container image in ECR, numbered by the service from 1
#                  upwards. The release pipeline's since Stage 8 decision 18
#   app image      how a space starts that container: the entrypoint, the arguments and the
#   configuration  environment. One per app type, because a JupyterLab space and a Code Editor
#                  space read different fields of the domain's user settings. This slice's
#
# What is not here is deliberate. The image versions are the release pipeline's (below). The domain's
# CustomImages lives on the SageMaker AI domain the Tooling blueprint provisions for the project, an
# object this repository does not author and must not adopt (Lesson 17 - a service that sets itself up
# creates principals and objects nobody chose, and Terraform would then be racing its author). The
# attach is a hand step and its recipe, its full-replace hazard and its reconciliation reading are
# docs/plan/runbooks/dev-env.md.
#
# The layer is [P]: an image, its versions and two configurations are metadata and cost nothing at
# rest. What costs is a space started on them, which is [E] and dies with `make down`.

resource "aws_sagemaker_image" "dev_env" {
  image_name   = "awsds-${var.env}-dev-env"
  display_name = "AWS-DataScience dev-env"
  description  = "The house image: the SageMaker Distribution ancestor plus this project's Python, Julia, R and Rust layer (dev-env/Dockerfile of the GitLab project awsds/dev-env)."
  role_arn     = module.image_role.role_arn

  tags = {
    Name = "awsds-${var.env}-dev-env"
  }
}

# The versions are not this slice's (Stage 8 decision 18). A version is a release artifact: awsds/dev-env's
# register job creates one per approved release with `create-image-version`, by digest and with the
# release's semver as an alias, and its retire job deletes every version past the newest 10 that no space
# names. The domain attaches this image with no version number, so the portal offers every version and a
# new space pins the one it is created on (decision 7, dev-env.md §B).
#
# Version 7, the last one Terraform created, leaves the state and stays in the account.
removed {
  from = aws_sagemaker_image_version.dev_env

  lifecycle {
    destroy = false
  }
}

# ---------------------------------------------------------------- how a space starts it
#
# One configuration per app type: the vendor's instruction is to match the application type to the
# Dockerfile, and the domain reads the two from different fields of its user settings
# (JupyterLabAppSettings and CodeEditorAppSettings). A space names no configuration - CustomImages
# lives on the domain default or a user profile, never on SpaceSettings - though it does name an image
# and a version, in its own DefaultResourceSpec, written when the space is created (dev-env.md §B).
#
# No file_system_config in either: the defaults are already this image's shape - uid 1000, gid 100,
# and the space's EBS volume mounted at /home/sagemaker-user, a path the platform owns and that
# gitlab/awsds/dev-env/README.md forbids moving.
#
# The environment this configuration cannot carry, measured 2026-09-10 at this slice's first apply.
# 6c step 5.6's six proxy variables were written here as ContainerEnvironmentVariables, which is
# what Stage 6d steps 2.2 and 8.4(c) name as the delivery mechanism, and CreateAppImageConfig
# refused both configurations with a ValidationException: `Member must have length less than or
# equal to 256`. The API reference confirms the shape of the limit - ContainerConfig's map takes at
# most 25 entries, and each key and each value at most 256 characters. The image's NO_PROXY is 70
# entries and 2,295 characters (2026-10-10), so it does not fit and no rewriting of these resources
# makes it fit.
#
# The four proxy variables are not delivered without it. NO_PROXY is what keeps AWS traffic on the
# VPC endpoints; with a proxy set and no bypass list, every AWS call in a space leaves through the
# hub as a public call carrying neither aws:SourceVpc nor aws:SourceVpce - which the compute plane
# allows (`.amazonaws.com` is on it), so it would succeed and silently lose the perimeter. Half the
# pair is worse than neither.
#
# So these configurations bind an app type to the image and carry no environment. The delivery was
# decided by the user on 2026-09-10 (6d decision 8): the six variables are ENV in
# gitlab/awsds/dev-env/dev-env/Dockerfile, the bypass list a dated literal there with the command
# that refreshes it beside it. What that costs - the image is shaped by one VPC's endpoint list, and
# a change to it is a rebuild, a tag and a version - is docs/plan/runbooks/dev-env.md
# E, which also carries the staleness reading.

resource "aws_sagemaker_app_image_config" "jupyterlab" {
  app_image_config_name = "awsds-${var.env}-dev-env-jupyterlab"

  jupyter_lab_image_config {}

  tags = {
    Name = "awsds-${var.env}-dev-env-jupyterlab"
  }
}

resource "aws_sagemaker_app_image_config" "code_editor" {
  app_image_config_name = "awsds-${var.env}-dev-env-codeeditor"

  code_editor_app_image_config {}

  tags = {
    Name = "awsds-${var.env}-dev-env-codeeditor"
  }
}
