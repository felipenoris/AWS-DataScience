# What this slice reports - Stage 2 step 5.
#
# No ARN is printed. Every ARN here carries an account id and aws/INDEX.md rule 1 keeps those out of
# tracked files; the attach step needs none of them, because CustomImages is written in names and a
# version number.

output "image_name" {
  description = "The SageMaker AI image - what the domain's CustomImages names."
  value       = aws_sagemaker_image.dev_env.image_name
}

output "image_version_number" {
  description = "The version the service assigned, 1 upwards. A tag bump replaces the version and this number moves."
  value       = aws_sagemaker_image_version.dev_env.version
}

output "image_tag" {
  description = "The tag registered, so a reader can tell which build a space is running without opening the repository."
  value       = var.image_tag
}

output "app_image_config_names" {
  description = "One configuration per app type - the domain reads them from two different fields of its user settings."
  value = {
    jupyterlab  = aws_sagemaker_app_image_config.jupyterlab.app_image_config_name
    code_editor = aws_sagemaker_app_image_config.code_editor.app_image_config_name
  }
}

output "custom_images" {
  description = "The two CustomImages entries, in the API's own spelling, ready for the attach step in docs/plan/runbooks/dev-env.md. Reported rather than retyped: the version number is the service's and moves under the operator."
  value = {
    jupyterlab = {
      ImageName          = aws_sagemaker_image.dev_env.image_name
      ImageVersionNumber = aws_sagemaker_image_version.dev_env.version
      AppImageConfigName = aws_sagemaker_app_image_config.jupyterlab.app_image_config_name
    }
    code_editor = {
      ImageName          = aws_sagemaker_image.dev_env.image_name
      ImageVersionNumber = aws_sagemaker_image_version.dev_env.version
      AppImageConfigName = aws_sagemaker_app_image_config.code_editor.app_image_config_name
    }
  }
}
