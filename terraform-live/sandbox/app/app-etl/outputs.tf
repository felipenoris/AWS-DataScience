# Outputs. `processing_job_request` is the whole CreateProcessingJob request but its name, which a person
# gives at submission (the stage file's 2.4): the job settings Stage 9 step 3.5 enforces in the deployment
# targets - VpcConfig, network isolation, inter-container encryption, a volume key - and the command a
# processing job opens with, 6i's chown included (decision 8). It is null until release.tf names a
# release.

output "job_role_arn" {
  description = "awsds-<env>-app-etl-job - the role the processing jobs run as."
  value       = module.job_role.role_arn
}

output "job_security_group_id" {
  description = "The jobs' security group: no ingress, HTTPS to S3 and to the interface endpoints."
  value       = aws_security_group.job.id
}

output "image_uri" {
  description = "The release's image, by digest - null until release.tf names one."
  value       = var.release == null ? null : "${data.terraform_remote_state.registry.outputs.ecr_app_etl_repository_url}@${var.release.digest}"
}

output "processing_job_request" {
  description = "The CreateProcessingJob request, for `aws sagemaker create-processing-job --cli-input-json` with --processing-job-name. Null until release.tf names a release."
  value = var.release == null ? null : jsonencode({
    RoleArn = module.job_role.role_arn
    AppSpecification = {
      ImageUri            = "${data.terraform_remote_state.registry.outputs.ecr_app_etl_repository_url}@${var.release.digest}"
      ContainerEntrypoint = ["/bin/bash", "-c"]
      ContainerArguments = [
        "sudo -n chown \"$(id -u)\" /opt/ml/processing/output && exec python -m app_etl --input /opt/app-etl/samples --output /opt/ml/processing/output",
      ]
    }
    ProcessingResources = {
      ClusterConfig = {
        InstanceCount  = 1
        InstanceType   = var.job_instance_type
        VolumeSizeInGB = 10
        VolumeKmsKeyId = data.terraform_remote_state.data.outputs.data_key_arn
      }
    }
    NetworkConfig = {
      EnableNetworkIsolation                = true
      EnableInterContainerTrafficEncryption = true
      VpcConfig = {
        Subnets          = values(data.terraform_remote_state.foundation.outputs.private_subnet_ids)
        SecurityGroupIds = [aws_security_group.job.id]
      }
    }
    ProcessingOutputConfig = {
      KmsKeyId = data.terraform_remote_state.data.outputs.data_key_arn
      Outputs = [
        {
          OutputName = "results"
          S3Output = {
            S3Uri        = "s3://${data.terraform_remote_state.data.outputs.outputs_bucket_name}/app-etl/${var.release.tag}/"
            LocalPath    = "/opt/ml/processing/output"
            S3UploadMode = "EndOfJob"
          }
        }
      ]
    }
    StoppingCondition = { MaxRuntimeInSeconds = 900 }
    Tags = [
      { Key = "Project", Value = var.project },
      { Key = "Environment", Value = var.environment_tag },
      { Key = "Owner", Value = var.owner },
      { Key = "CostCenter", Value = var.cost_center },
    ]
  })
}
