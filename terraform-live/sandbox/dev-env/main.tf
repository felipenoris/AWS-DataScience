# The house image, registered for this account (Stage 6d step 2).
#
# Three objects, and the boundary between them is what the rest of the design leans on:
#
#   image          the named thing a domain attaches. Account-scoped, versionless
#   image version  one immutable pointer at one container image in ECR. Numbered by the service,
#                  1 upwards, and force-new here because base_image cannot be updated in place
#   app image      how a space starts that container: the entrypoint, the arguments and the
#   configuration  environment. One per app type, because a JupyterLab space and a Code Editor
#                  space read different fields of the domain's user settings
#
# What is not here is the fourth object, and it is deliberate: the domain's CustomImages. That field
# lives on the SageMaker AI domain the Tooling blueprint provisions for the project, an object this
# repository does not author and must not adopt (Lesson 17 - a service that sets itself up creates
# principals and objects nobody chose, and Terraform would then be racing its author). The attach is
# a hand step and its recipe, its full-replace hazard and its reconciliation reading are
# docs/plan/runbooks/dev-env.md.
#
# The layer is [P]: an image, a version and two configurations are metadata and cost nothing at
# rest. What costs is a space started on them, which is [E] and dies with `make down`.

resource "aws_sagemaker_image" "dev_env" {
  image_name   = "awsds-${var.env}-dev-env"
  display_name = "AWS-DataScience dev-env"
  description  = "The house image: the SageMaker Distribution ancestor plus this project's Python, Julia, R and Rust layer (images/dev-env/Dockerfile)."
  role_arn     = module.image_role.role_arn

  tags = {
    Name = "awsds-${var.env}-dev-env"
  }
}

# The version. `base_image` is force-new: SageMaker image versions are immutable, so a tag bump
# destroys version N and creates version N+1 rather than editing one. That is the intended shape -
# Stage 8 step 1's pipeline takes this slice over and its only input is the approved digest - and it
# is also why the attachment's version number is a decision rather than a detail (the runbook's
# "Attaching the image to the domain").
#
# Version N is named in two places an apply does not reach: the domain's CustomImages, and the
# DefaultResourceSpec of every space created while N was current. A space keeps that copy and it
# overrides the domain default, so after the destroy its app does not start (AWS_STATE.md EXC-09).
# No alias is set, which is what would let a space follow a bump; dev-env.md §B step 6 is the sweep.
resource "aws_sagemaker_image_version" "dev_env" {
  image_name = aws_sagemaker_image.dev_env.image_name
  base_image = local.base_image
}

# ---------------------------------------------------------------- how a space starts it
#
# One configuration per app type: the vendor's instruction is to match the application type to the
# Dockerfile, and the domain reads the two from different fields of its user settings
# (JupyterLabAppSettings and CodeEditorAppSettings). A space names no configuration - CustomImages
# lives on the domain default or a user profile, never on SpaceSettings - though it does name an image
# and a version, in its own DefaultResourceSpec (see the version above).
#
# No file_system_config in either: the defaults are already this image's shape - uid 1000, gid 100,
# and the space's EBS volume mounted at /home/sagemaker-user, a path the platform owns and that
# images/README.md forbids moving.
#
# The environment this configuration cannot carry, measured 2026-09-10 at this slice's first apply.
# 6c step 5.6's six proxy variables were written here as ContainerEnvironmentVariables, which is
# what Stage 6d steps 2.2 and 8.4(c) name as the delivery mechanism, and CreateAppImageConfig
# refused both configurations with a ValidationException: `Member must have length less than or
# equal to 256`. The API reference confirms the shape of the limit - ContainerConfig's map takes at
# most 25 entries, and each key and each value at most 256 characters. The estate's generated
# NO_PROXY is 52 entries and about 1,500 characters, so it does not fit and no rewriting of these
# resources makes it fit.
#
# The four proxy variables are not delivered without it. NO_PROXY is what keeps AWS traffic on the
# VPC endpoints; with a proxy set and no bypass list, every AWS call in a space leaves through the
# hub as a public call carrying neither aws:SourceVpc nor aws:SourceVpce - which the compute plane
# allows (`.amazonaws.com` is on it), so it would succeed and silently lose the perimeter. Half the
# pair is worse than neither.
#
# So these configurations bind an app type to the image and carry no environment. The delivery was
# decided by the user on 2026-09-10 (6d decision 8): the six variables are ENV in
# images/dev-env/Dockerfile, the bypass list a dated literal there with the command that refreshes it
# beside it. What that costs - the image is shaped by one VPC's endpoint list, and a change to it is a
# rebuild, a tag, a version and a re-attach - is docs/plan/runbooks/dev-env.md E, which also carries
# the staleness reading.

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
