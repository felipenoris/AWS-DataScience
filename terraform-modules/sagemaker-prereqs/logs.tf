# Stage 6 step 9.1 - the log group, created here rather than by the service.
#
# A service that creates its own log group creates it with no retention - "Never expire" - and
# nobody is told (Lesson 17 in its cheapest form: the bill grows monotonically and the finding
# is a line item years later). Declaring it here fixes the name (so app and space logs land
# somewhere a person can find) and the retention, at the same 30 days Stage 3 chose for the flow
# logs. Two different subsystems agreeing on a retention is worth more than each being
# individually optimal.
#
# Still to verify, because a declared group is not a used one (step 9.1): that the per-project
# SageMaker AI domain's app and space logs land here and not in a default group beside it. That
# is a reading at pass 3, against a running app; if they land elsewhere, the answer is to point
# them here, never to widen this.
#
# Encryption is the account default, the same call Stage 3 made for the flow logs: a CMK on a
# log group costs a key-month and buys separation from nobody, since the only readers are
# principals this account already trusts.

resource "aws_cloudwatch_log_group" "studio" {
  # checkov:skip=CKV_AWS_158:default (AWS-managed) encryption, the same call Stage 3 made for the flow logs - a CMK here costs a key-month and separates this account's logs from nobody
  # checkov:skip=CKV_AWS_338:retention is 30 days, matching Stage 3 decision 3 and the flow logs beside it - two subsystems agreeing beats each being individually optimal
  name              = "/awsds/${var.env}/studio"
  retention_in_days = var.log_retention_days
}
