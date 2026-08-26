# What this slice reports - Stage 2 step 5.
#
# NOTHING HERE PRINTS AN ACCOUNT ID (aws/INDEX.md rule 1), which costs one output: the access
# role's ARN carries the account and is therefore NOT reported, even though it is the value the
# portal's S3-connection form asks for. The runbook's §W reads it from the role NAME below plus
# the operator's own `aws sts get-caller-identity`, which is where an account id is allowed to
# be - on a terminal, not in a tracked file.

output "bucket_name" {
  description = "The lake bucket."
  value       = module.lake.bucket_name
}

output "access_role_name" {
  description = "The Access Grants location role, and the access role every S3 connection into this bucket names. A NAME, not an ARN - see the header."
  value       = module.lake_access_role.role_name
}

output "access_grants_location_id" {
  description = "THE VALUE THE RUNBOOK'S §W NEEDS on every wiring: create-access-grant is addressed to it. Reported here so the operator reads it from a plan output rather than re-listing the instance each time."
  value       = aws_s3control_access_grants_location.lake.access_grants_location_id
}

output "tenant_prefixes" {
  description = "The prefix contract, applied: sso-group NAME => the sub-prefix its reserved role holds READWRITE on. The bucket's layout and its grant table are the same table, which is what makes an unexpected top-level prefix a finding (SL-4)."
  value       = { for g in keys(var.tenants) : g => "${g}/*" }
}

output "wired_project_count" {
  description = "How many SMUS projects have a trust statement here - a COUNT, because the list is project role ARNs. Zero until step 4.1; a number larger than the live project count is §R's missing half (SL-4's orphan reading finds the other one)."
  value       = length(var.wired_projects)
}
