# Outputs - what the helper script and a person diagnosing a build need, and nothing else.

output "instance_id" {
  description = "The build host. ./scripts/buildbox.py finds it by Name tag rather than through this output - a script that needs terraform state to open a shell cannot help you when terraform is what is broken - so this is for a person: `aws ssm start-session --target <this>`, or `aws ec2 get-console-output --instance-id <this> --latest` when SSM itself is what failed."
  value       = aws_instance.buildbox.id
}

output "private_ip" {
  description = "The address to reach it on FROM THE TUNNEL - the only place it is reachable from. Also what a flow log in this account shows for the build's traffic on its way to the WireGuard host."
  value       = aws_instance.buildbox.private_ip
}

output "instance_role_arn" {
  description = "The host's role. Named because its ABSENCES are the interesting part: Session Manager and nothing else - no ecr:, so this host builds images and publishes none (main.tf carries the reasoning)."
  value       = module.role.role_arn
}
