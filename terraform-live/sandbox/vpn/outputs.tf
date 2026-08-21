# Outputs - what a reader needs to diagnose the host, and nothing a client config pins.
# The endpoint address and the server's public key are deliberately elsewhere: the first is a
# foundation/ output because it is [P], the second is derived on the laptop from the private
# half the user holds. That split is what makes "a rebuild changes nothing" true (step 9.1).

output "instance_id" {
  description = "The WireGuard host. First reading of a bad first boot is its cloud-init output through Session Manager; if SSM is what failed - verification (iii) - `aws ec2 get-console-output --instance-id <this> --latest` needs no endpoint."
  value       = module.wireguard.instance_id
}

output "private_ip" {
  description = "The address every forwarded packet leaves here wearing (step 1.2) - what makes a flow log in Production readable."
  value       = module.wireguard.private_ip
}

output "log_group_name" {
  description = "The handshake log group (step 7.2)."
  value       = module.wireguard.log_group_name
}

output "instance_role_arn" {
  description = "The host's role, named for the stage that reasons about this principal (Stage 7's GitLab) - a carve-out written against a role that already exists is the shape D27 trusts."
  value       = module.wireguard.instance_role_arn
}

output "primary_network_interface_id" {
  description = "WHAT A ROUTE POINTS AT, read by terraform-live/sandbox/devbox/ through this slice's state (Stage 6). It is the instance's ENI rather than its id because that is what aws_route accepts - and it is read rather than pasted because the instance is [D] and REPLACEABLE: a shape change or a user-data change mints a new interface, and a pasted id would leave a route that blackholes silently instead of a plan that moves."
  value       = module.wireguard.primary_network_interface_id
}
