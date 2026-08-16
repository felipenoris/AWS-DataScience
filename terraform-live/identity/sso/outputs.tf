# What this slice reports - Stage 2 step 5.
#
# NOTHING HERE PRINTS AN ACCOUNT ID, A GROUP GUID OR AN E-MAIL ADDRESS, and that is a rule
# rather than an accident: an output is echoed to the terminal on every apply and pasted into
# logs and chat windows afterwards (aws/INDEX.md rule 1). The slice HOLDS all three - the
# organization roster is in its state - and reports none of them. Where a count would do, it is
# a count.
#
# A permission set ARN is not in that class: `arn:aws:sso:::permissionSet/ssoins-…/ps-…` names
# the Identity Center instance and the set, and carries no account.

output "permission_set_arns" {
  description = "The six written persona sets, by local key. The imported administrator set is reported separately below so the two halves stay distinguishable in the apply output."
  value       = local.permission_set_arns
}

output "infrastructure_permission_set_arn" {
  description = "The imported InfrastructureAccess set (Stage 1b step 3). Reported on its own because it is the credential this apply runs as."
  value       = aws_ssoadmin_permission_set.infrastructure.arn
}

output "inline_policy_bytes" {
  description = <<-EOT
    The rendered size of each written set's inline policy, against the ceiling in
    var.inline_policy_max_bytes.

    IT IS AN OUTPUT RATHER THAN A COMMENT BECAUSE THE NUMBER MOVES. Three of these sets are
    long enumerated denies (1b step 3.5) and every stage from 5 onwards adds grants to them;
    the precondition on each inline policy is what FAILS, and this is what lets somebody see
    the margin shrinking before it does. Step 5.2's "count before writing", made repeatable.
  EOT
  value       = { for k, v in local.inline_policies : k => length(v) }
}

output "assignment_count" {
  description = "How many group->account assignments this slice manages, written half and imported half apart. A count rather than a list: the list is account ids. Measured on the first plan, 2026-08-16: 10 persona rows and 5 infrastructure rows. Both grow at the Staging vend - the persona side by two (DataScientistStagingAccess and DeploymentManagerAccess), the infrastructure side by one."
  value = {
    persona        = length(aws_ssoadmin_account_assignment.persona)
    infrastructure = length(aws_ssoadmin_account_assignment.infrastructure)
  }
}
