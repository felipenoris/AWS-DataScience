# Outputs - what other slices read through terraform_remote_state (never pasted).

output "data_key_arn" {
  description = "The account data CMK - every lake bucket encrypts under it (decision 2, revised 2026-08-19)."
  value       = module.data_key.key_arn
}

output "bucket_names" {
  description = "The five lake buckets by short key (raw, curated, artifacts, logs, dropbox)."
  value       = { for k, m in module.bucket : k => m.bucket_name }
}

output "bucket_arns" {
  description = "The five lake buckets' ARNs, same keys."
  value       = { for k, m in module.bucket : k => m.bucket_arn }
}

output "dropbox_prefix" {
  description = "The drop-box write prefix - dated below it by convention (incoming/<yyyy>/<mm>/<dd>/...)."
  value       = local.dropbox_prefix
}

output "catalog_maintenance_role_arn" {
  description = "awsds-data-catalog-maintenance - the D27 carve-out principal (the SCP names it; DL-4 reads it)."
  value       = module.catalog_maintenance_role.role_arn
}

output "lf_registration_role_arn" {
  description = "The Lake Formation registered-location role - Stage 9 amends its policy for the governed write."
  value       = module.lf_registration_role.role_arn
}

output "database_names" {
  description = "The three catalog databases - what the consumer slices' resource links point at (step 8)."
  value = {
    raw     = aws_glue_catalog_database.raw.name
    curated = aws_glue_catalog_database.curated.name
    dropbox = aws_glue_catalog_database.dropbox.name
  }
}

output "sample_table_name" {
  description = "The stage's working piece - the share and classification pairs query it (deliverables)."
  value       = aws_glue_catalog_table.sample_trades.name
}
