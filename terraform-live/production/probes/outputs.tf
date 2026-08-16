# Outputs - for reading the probe, never for anchoring. Everything in this slice is [E] and
# is gone by the end of the sitting; the two addresses below are new on every apply, which is
# exactly why the source slice reaches this host BY NAME and not by any value here.

output "instance_id" {
  description = "The target's instance id - the argument to `aws ec2 get-console-output --latest`, which is the only reading path: no SSM endpoints exist in this account (step 8.7 lists them as not-here-yet), so Session Manager is not available."
  value       = aws_instance.target.id
}

output "permitted_ip" {
  description = "The primary interface, in the private tier the source account routes to. Recorded so the console reading can be matched against what the route tables say - not so anything can reference it."
  value       = aws_instance.target.private_ip
}

output "forbidden_ip" {
  description = "The secondary interface, in the isolated tier the source account holds no route to. Same host, same listener, same security group as the address above - the single difference the negative reading rests on."
  value       = aws_network_interface.isolated.private_ip
}
