# Outputs - what a by-hand step and ./aws/warehouse.py read, never paste.

output "workgroup_name" {
  description = "The workgroup. Same name as the namespace on purpose: one name for one warehouse, so a rename fails in a check rather than in a later step."
  value       = aws_redshiftserverless_workgroup.this.workgroup_name
}

output "workgroup_id" {
  description = "The service's own id. It changes across a destroy and re-create under the same name (5b step 1.9), which is why no policy names the workgroup by ARN and 9.4's grant names workgroup/*."
  value       = aws_redshiftserverless_workgroup.this.workgroup_id
}

output "endpoint" {
  description = "The workgroup's host and port - the 5439 data path, which resolves to this workgroup's ENIs in VPC-Workloads and needs no interface endpoint. The deploy runner has no path to it (VPC-SharedServices and VPC-Workloads do not peer); its door is the Data API (step 9.4)."
  value = {
    address = try(aws_redshiftserverless_workgroup.this.endpoint[0].address, null)
    port    = try(aws_redshiftserverless_workgroup.this.endpoint[0].port, null)
  }
}

output "usage_limit_arn" {
  description = "The serverless-compute usage limit with breach_action = deactivate. WH-3 reads that it exists, that the action is not the API's default `log`, and that no looser second limit sits beside it."
  value       = aws_redshiftserverless_usage_limit.compute.arn
}
