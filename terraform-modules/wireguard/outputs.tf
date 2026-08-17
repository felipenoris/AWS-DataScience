# Outputs. NOTHING HERE IS AN ADDRESS OR A KEY a client config needs: the endpoint address is
# the caller's [P] Elastic IP output and the server's public key is derived at enrollment from
# the private half that lives in the caller's [P] secret (step 4.3). Both by design - this
# module's contents are [D] and may be replaced, so anything a client pins must come from
# somewhere that cannot be.

output "instance_id" {
  description = "The WireGuard host. Read cloud-init output through Session Manager (step 3); if SSM itself is what failed - verification (iii) - `aws ec2 get-console-output --instance-id <this> --latest` needs no endpoint at all."
  value       = aws_instance.this.id
}

output "private_ip" {
  description = "The address every forwarded packet leaves here wearing (step 1.2). A peer VPC admits the SECURITY GROUP rather than this address - it moves with a rebuild - but the value makes a flow log readable."
  value       = aws_instance.this.private_ip
}

output "log_group_name" {
  description = "The handshake log group (step 7.2)."
  value       = aws_cloudwatch_log_group.handshakes.name
}

output "alarm_name" {
  description = "The health alarm (step 7.3). ./aws/vpn.py VP-6 fails if no awsds-*vpn* alarm exists once the host does."
  value       = aws_cloudwatch_metric_alarm.health.alarm_name
}

output "instance_role_arn" {
  description = "The host's role - named here because a carve-out written against a role that already exists is the one shape this plan trusts (D27), and Stage 5's EFS and Stage 7's GitLab both reason about this principal."
  value       = module.role.role_arn
}
