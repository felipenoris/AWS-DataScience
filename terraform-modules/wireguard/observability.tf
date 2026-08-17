# Step 7 - the one internet-facing host must not fail silently, and "tunnel up, nothing
# routes" must be diagnosable without a shell.
#
# WIREGUARD WRITES NO LOG FILE. Its kernel module logs nothing to disk, so there is nothing to
# tail until the host creates it - which is why the user data installs a systemd timer that
# appends `wg show all latest-handshakes` to a file once a minute, and the agent tails THAT.
# This is a correction of an earlier revision that said "ship WireGuard's log".

resource "aws_cloudwatch_log_group" "handshakes" {
  # checkov:skip=CKV_AWS_158:a CMK is USD 1/key-month for a diagnostic log - the same judgement Stage 3 recorded for flow logs (step 5.1), and the content is a public key and a timestamp
  # checkov:skip=CKV_AWS_338:retention is 30 days by decision - a diagnostic, not an audit trail; the audit trail is CloudTrail, org-wide and Object-Locked since Stage 1d
  name              = "/awsds/${var.env}/vpn"
  retention_in_days = var.log_retention_days
}

# THE ALARM IS ON THE STATUS CHECKS AND NOT ON HANDSHAKE AGE (decision 2). The obvious
# instrument - "no handshake for N minutes" - fires every time the operator simply
# disconnects, which is most of the day: an alarm that is red whenever nobody is working
# teaches its reader to ignore it, and this is the only alarm on the only exposed host.
#
# treat_missing_data = "notBreaching" IS LOAD-BEARING FOR A [D] HOST. EC2 stops publishing
# StatusCheckFailed while an instance is stopped, so the default (`missing`) would put this
# alarm into INSUFFICIENT_DATA after every `make down` - a state change per session, from the
# machinery working exactly as designed.
#
# IT NOTIFIES NOBODY, AND THAT IS STATED RATHER THAN IMPLIED (Lesson 5, an intention is not a
# control). D12 left the budget with no subscriber and this environment's first automatic
# notification is Stage 4 step 10.4's GuardDuty topic, in Audit. Until an SNS topic exists in
# this account, the alarm is read by ./aws/vpn.py VP-6 and by Stage 12's dashboard - so what
# it buys today is a state a script can measure, not a page anybody receives.
resource "aws_cloudwatch_metric_alarm" "health" {
  alarm_name          = "awsds-${var.env}-vpn-health"
  alarm_description   = "WireGuard host status checks (Stage 4 step 7.3). No action: no SNS topic exists in this account yet - see Stage 12."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    InstanceId = aws_instance.this.id
  }
}
