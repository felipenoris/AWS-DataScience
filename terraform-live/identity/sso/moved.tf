# identity/sso/moved.tf - Stage 6b step 4.6, 2026-09-06.
#
# WHY THIS FILE EXISTS. `local.assignments` is keyed `<persona>@<account folder>` and that key IS
# the resource address of an aws_ssoadmin_account_assignment. Stage 6b renames the account folder
# `development` to `staging`, so two keys move - and Terraform reads a moved key as a different
# resource: it would DESTROY each assignment and CREATE it again. For an SSO assignment that is
# not merely churn. Deleting one revokes access for everyone in the group while the create half
# runs, and the two halves are separate API calls against a service that provisions
# asynchronously - so the window is real and its length is not ours to choose.
#
# WITH THESE BLOCKS THE PLAN READS `0 to add, 0 to change, 0 to destroy`, which is the gate: the
# rename is a bookkeeping change in state and nothing at all in IAM Identity Center.
#
# THE FIRST KEY CHANGES ON BOTH SIDES OF THE @, and that is not a typo. Step 2.1 had already
# swapped the permission set from DataScientistAccess to DataScientistStagingAccess while leaving
# the key alone on purpose; 4.6 is where the persona half of the name catches up with the set it
# has been pointing at since that step.
#
# THIS FILE GOES when nothing in this repository refers to the old folder name any more - it is
# a migration record, not a permanent part of the slice, and a moved block whose `from` address
# can no longer exist anywhere is dead weight that reads like history.

# THE THIRD BLOCK WAS FOUND BY THE PLAN, NOT BY READING, AND IT IS THE MOST IMPORTANT ONE.
# Step 4.6 names two assignment keys. It does not mention `aws_ssoadmin_account_assignment`
# .infrastructure, which for_eaches over `local.accounts` - the SAME map whose `development` key
# the step also renames. Without this block the plan read `1 to add, 0 to change, 1 to destroy`:
# InfrastructureAccess REVOKED on the account and re-granted, which is the assignment the
# operator running the apply is signed in through. A plan is what surfaced it; a step-by-step
# reading of the step would not have.
moved {
  from = aws_ssoadmin_account_assignment.infrastructure["development"]
  to   = aws_ssoadmin_account_assignment.infrastructure["staging"]
}

moved {
  from = aws_ssoadmin_account_assignment.persona["data-scientist@development"]
  to   = aws_ssoadmin_account_assignment.persona["data-scientist-staging@staging"]
}

moved {
  from = aws_ssoadmin_account_assignment.persona["deployment-manager@development"]
  to   = aws_ssoadmin_account_assignment.persona["deployment-manager@staging"]
}
