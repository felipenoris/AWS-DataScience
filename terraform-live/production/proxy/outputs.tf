# Outputs - what a reader needs to diagnose the exit, and nothing a client pins. The address is
# networking/'s [P] output because it is [P]: that split is what makes "a rebuild changes
# nothing" true of the one host every VPN-only condition names after step 4.12.

output "instance_id" {
  description = "The proxy host. First reading of a bad first boot is its cloud-init output through Session Manager; if SSM itself is what failed, `aws ec2 get-console-output --instance-id <this> --latest` needs no endpoint at all."
  value       = aws_instance.this.id
}

output "private_ip" {
  description = "The address the spokes and the tunnel open TCP/3128 to. A peered spoke reaches it across the peering; a tunnel client reaches it un-masqueraded, which is what makes the access log per-device (step 4.7)."
  value       = aws_instance.this.private_ip
}

output "role_arn" {
  description = "The proxy's role - three permissions and no more: Session Manager, one SSM parameter by name, and one log group with no delete."
  value       = module.role.role_arn
}

output "association_id" {
  description = "The State Manager association that re-renders the allow-lists (step 4.10). Its failures are its own report; a SUCCESS that changed nothing it should have is what ./aws/proxy.py exists to catch."
  value       = aws_ssm_association.reconfigure.association_id
}

output "alarm_name" {
  description = "The status-check alarm on the estate's only internet exit."
  value       = aws_cloudwatch_metric_alarm.health.alarm_name
}
