# Step 7 - the one internet-facing host must not fail silently, and "tunnel up, nothing
# routes" must be diagnosable without a shell.
#
# WireGuard writes no log file. Its kernel module logs nothing to disk, so there is nothing to
# tail until the host creates it: the user data installs a systemd timer that appends
# `wg show all latest-handshakes` to a file once a minute, and the agent tails that file.

resource "aws_cloudwatch_log_group" "handshakes" {
  # checkov:skip=CKV_AWS_158:a CMK is USD 1/key-month for a diagnostic log - the same judgement Stage 3 recorded for flow logs (step 5.1), and the content is a public key and a timestamp
  # checkov:skip=CKV_AWS_338:retention is 30 days by decision - a diagnostic, not an audit trail; the audit trail is CloudTrail, org-wide and Object-Locked since Stage 1d
  name              = "/awsds/${var.env}/vpn"
  retention_in_days = var.log_retention_days
}

# The alarm is on the status checks rather than on handshake age (decision 2). The obvious
# instrument - "no handshake for N minutes" - fires every time the operator simply
# disconnects, which is most of the day: an alarm that is red whenever nobody is working
# teaches its reader to ignore it, and this is the only alarm on the only exposed host.
#
# treat_missing_data = "notBreaching" is load-bearing for a [D] host. EC2 stops publishing
# StatusCheckFailed while an instance is stopped, so the default (`missing`) would put this
# alarm into INSUFFICIENT_DATA after every `make down` - a state change per session, from the
# machinery working exactly as designed.
#
# It notifies var.alarm_actions, the caller's alerts topic (Stage 12 step 2.2). With the default,
# an empty list, it notifies nobody (Lesson 5) and is read by ./aws/vpn.py VP-6 and Stage 12's
# dashboard alone.
resource "aws_cloudwatch_metric_alarm" "health" {
  alarm_name          = "awsds-${var.env}-vpn-health"
  alarm_description   = "WireGuard host status checks while running (Stage 4 step 7.3, Stage 12 step 2.2); a stopped host reads OK. docs/plan/runbooks/vpn.md: section S5 to start and stop the host, section K0a for a shell on it, section C4 when the tunnel does not work."
  namespace           = "AWS/EC2"
  metric_name         = "StatusCheckFailed"
  statistic           = "Maximum"
  period              = 300
  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = var.alarm_actions

  dimensions = {
    InstanceId = aws_instance.this.id
  }
}
