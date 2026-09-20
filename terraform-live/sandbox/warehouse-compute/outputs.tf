# Outputs - what a by-hand step and ./aws/warehouse.py read, never paste.

output "workgroup_name" {
  description = "The workgroup. Same name as the namespace on purpose: Redshift allows it, and one name for one warehouse is what makes a rename fail in a check rather than in Stage 6h."
  value       = aws_redshiftserverless_workgroup.this.workgroup_name
}

output "workgroup_id" {
  description = "The service's own id. Step 1.9 reads it before and after a destroy/re-create, because an id that changes is a fact anything pinning it must not."
  value       = aws_redshiftserverless_workgroup.this.workgroup_id
}

output "endpoint" {
  description = "The workgroup's host and port - the 5439 data path, which resolves to this workgroup's ENIs in this VPC and needs no interface endpoint. THE HOST IS WHAT STEP 1.9 IS ABOUT: Stage 6h's SMUS connection stores it as a field, so a host that does not survive a destroy and re-create under the same name makes every `make down` break every connection (decision 8 is the fallback)."
  value = {
    address = try(aws_redshiftserverless_workgroup.this.endpoint[0].address, null)
    port    = try(aws_redshiftserverless_workgroup.this.endpoint[0].port, null)
  }
}

output "usage_limit_arn" {
  description = "The serverless-compute usage limit with breach_action = deactivate. WH-3 reads that it exists, that the action is not the API's default `log`, and that no looser second limit sits beside it."
  value       = aws_redshiftserverless_usage_limit.compute.arn
}
