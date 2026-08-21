# STAGE 6 STEP 9.1 - the log group, created DELIBERATELY rather than by the service.
#
# WHY THIS IS A RESOURCE AND NOT A SETTING. A service that creates its own log group creates
# it with NO RETENTION - "Never expire" - and nobody is told (Lesson 17 in its cheapest form:
# the bill grows monotonically and the finding is a line item years later). Declaring it here
# fixes two things at once: the NAME (so app and space logs land somewhere a person can find)
# and the retention, at the same 30 days Stage 3 chose for the flow logs. Two different
# subsystems agreeing on a retention is worth more than each being individually optimal.
#
# WHAT STILL HAS TO BE VERIFIED, because a declared group is not a used one (step 9.1's own
# wording): that the per-project SageMaker AI domain's app and space logs actually land HERE
# and not in a default group beside it. That is a reading at pass 3, against a running app -
# and if they land elsewhere, the answer is to point them here, never to widen this.
#
# ENCRYPTION IS THE ACCOUNT DEFAULT, deliberately: Stage 3 made the same call for the flow
# logs, and the argument has not changed - a CMK on a log group costs a key-month and buys
# separation from nobody, since the only readers are principals this account already trusts.

resource "aws_cloudwatch_log_group" "studio" {
  # checkov:skip=CKV_AWS_158:default (AWS-managed) encryption, the same call Stage 3 made for the flow logs - a CMK here costs a key-month and separates this account's logs from nobody
  # checkov:skip=CKV_AWS_338:retention is 30 days, matching Stage 3 decision 3 and the flow logs beside it - two subsystems agreeing beats each being individually optimal
  name              = "/awsds/${var.env}/studio"
  retention_in_days = var.log_retention_days
}
