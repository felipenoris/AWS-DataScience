# Stage 10 step 5.1 - the image app-etl-train trains with and its batch transform serves: AWS's built-in
# XGBoost (decision 21), by digest. The registry is AWS's own for the Region, its address taken from the
# provider's table of SageMaker's prebuilt images, so no account id is written here. AWS republishes a
# tag in place: the digest pins what the lint reads and the model package records, and a new one is a
# reading of the tag (`aws ecr describe-images --registry-id <the registry> --repository-name
# sagemaker-xgboost --image-ids imageTag=<tag>`) and a commit. The render writes the output into a
# promoted workflow's TrainingImage (scripts/render-workflow.py), and the template's lint admits the
# repository beside the application's own (LINT_ALGORITHM_REPOSITORIES).
#
# The same file in staging/sagemaker/ and production/sagemaker/, byte for byte (./scripts/check-copies.py).

variable "training_image" {
  description = "AWS's XGBoost algorithm image app-etl-train trains with (Stage 10 decision 21): the tag the provider's lookup takes, and the digest read for it, 3.0-5's on 2026-10-24 (pushed 2026-10-11)."
  type = object({
    tag    = string
    digest = string
  })
  default = {
    tag    = "3.0-5"
    digest = "sha256:0b5d9341baa09ab2432fc9efbc329425e69325ba33562b1e2a015fd6f16e3a78"
  }

  validation {
    condition     = can(regex("^sha256:[0-9a-f]{64}$", var.training_image.digest))
    error_message = "training_image.digest is the image's sha256 digest, read for its tag."
  }
}

data "aws_sagemaker_prebuilt_ecr_image" "xgboost" {
  repository_name = "sagemaker-xgboost"
  image_tag       = var.training_image.tag
}

output "training_image_uri" {
  description = "The XGBoost image by digest, the TrainingImage of a promoted app-etl-train and the model package's container."
  value       = "${split(":", data.aws_sagemaker_prebuilt_ecr_image.xgboost.registry_path)[0]}@${var.training_image.digest}"
}
