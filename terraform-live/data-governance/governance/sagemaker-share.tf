# The domain shared through RAM with SageMaker's service principal (Stage 17 3.3, EXC-11). A SageMaker
# data source calls DataZone as sagemaker.amazonaws.com, and each run of the source a Tooling
# environment creates fails with "Please check if RAM share is correctly configured between Amazon
# SageMaker and Amazon DataZone" while no such share exists. AWS's page on a SageMaker data source
# names the share: the domain, the principal and the managed permission below.
#
# The permission, version 3 and the default on 2026-11-19, gives the principal twenty DataZone actions
# on the domain, CreateAsset, CreateDataSource, StartDataSourceRun and CreateListingChangeSet among
# them. RAM's table of shareable resources marks a DataZone domain as not shareable with a service
# principal (read 2026-11-19), against that page and that permission: the create is the measurement.
#
# sources limits the principal to requests from the domain's own accounts, RAM's confused-deputy
# constraint, which AWS's console steps leave unset; the aws provider's aws_ram_resource_share has no
# sources argument, so the share is awscc's. A share with a service principal admits no other
# principal, so allow_external_principals reaches nothing here and states the organization's rule.
resource "awscc_ram_resource_share" "sagemaker" {
  name                      = "DataZone-${aws_datazone_domain.this.id}-SageMaker"
  allow_external_principals = false
  resource_arns             = [aws_datazone_domain.this.arn]
  principals                = ["sagemaker.amazonaws.com"]
  permission_arns           = ["arn:${data.aws_partition.current.partition}:ram::aws:permission/AWSRAMSageMakerServicePrincipalPermissionAmazonDataZoneDomain"]
  sources                   = sort(values(local.member_account_ids))

  # awscc carries no default_tags.
  tags = [
    { key = "Project", value = var.project },
    { key = "Environment", value = var.environment_tag },
    { key = "ManagedBy", value = "terraform" },
    { key = "Owner", value = var.owner },
    { key = "CostCenter", value = "stage-17" },
  ]
}
