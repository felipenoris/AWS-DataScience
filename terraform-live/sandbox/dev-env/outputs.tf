# What this slice reports - Stage 2 step 5.
#
# No ARN is printed. Every ARN here carries an account id and aws/INDEX.md rule 1 keeps those out of
# tracked files; the attach step needs none of them, because CustomImages is written in names.

output "image_name" {
  description = "The SageMaker AI image - what the domain's CustomImages names, and what the release pipeline creates versions of."
  value       = aws_sagemaker_image.dev_env.image_name
}

output "app_image_config_names" {
  description = "One configuration per app type - the domain reads them from two different fields of its user settings."
  value = {
    jupyterlab  = aws_sagemaker_app_image_config.jupyterlab.app_image_config_name
    code_editor = aws_sagemaker_app_image_config.code_editor.app_image_config_name
  }
}

output "custom_images" {
  description = "The two CustomImages entries, in the API's own spelling, for the attach in docs/plan/runbooks/dev-env.md. No ImageVersionNumber: the domain offers every version of the image, and a new space pins the one it is created on (Stage 8 decision 7)."
  value = {
    jupyterlab = {
      ImageName          = aws_sagemaker_image.dev_env.image_name
      AppImageConfigName = aws_sagemaker_app_image_config.jupyterlab.app_image_config_name
    }
    code_editor = {
      ImageName          = aws_sagemaker_image.dev_env.image_name
      AppImageConfigName = aws_sagemaker_app_image_config.code_editor.app_image_config_name
    }
  }
}
