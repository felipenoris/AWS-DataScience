# Outputs - the two instance ids, and only so the console can be read. Everything here is
# [E]; nothing may reference it.

output "perimeter_instance_id" {
  description = "The isolated-tier probe. Read with `aws ec2 get-console-output --instance-id <this> --latest`: no SSM endpoints exist in this account and this tier has no default route, so the serial console is the only path out - which is itself a consequence of the design being measured."
  value       = aws_instance.perimeter.id
}

output "peering_instance_id" {
  description = "The private-tier probe. Same reading path, for consistency rather than necessity: this tier has a NAT, so Session Manager would have been reachable had an instance profile existed - and not creating one keeps both probes free of credentials."
  value       = aws_instance.peering.id
}
