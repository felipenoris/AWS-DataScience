# THE VPN HOST'S SIZE - the one tfvars in this repository a person edits to change what is
# running, and it is TRACKED on purpose (.gitignore names it as an exception to the wholesale
# *.tfvars ignore; ./scripts/check-tfvars-shape.py allows it exactly one key). It carries no
# account id, no address and no key material: one instance type, which is a decision worth
# having in git history rather than in somebody's shell.
#
# HOW TO USE IT - both directions, and no flag either way:
#
#   BIGGER: uncomment the line below (or edit its value), then `terraform apply` on this slice.
#   BACK TO THE DEFAULT: COMMENT THE LINE OUT AGAIN and `terraform apply` on this slice. With
#   nothing assigned here, variables.tf's default takes over - t4g.nano, D4's shape - and the
#   plan reads `~ instance_type` with `1 to change`, exactly as it did on the way up.
#
# THE NAME ENDS IN .auto.tfvars BECAUSE THAT IS WHAT MAKES TERRAFORM LOAD IT BY ITSELF - the
# apply above is complete as written:
#
#   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply
#
# Named instance_type.tfvars instead, every plan and apply would have to carry the file:
#
#   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply -var-file=instance_type.tfvars
#
# (-chdir is an option of `terraform` and goes BEFORE the subcommand; -var-file is an option
# of the subcommand and goes after it.) Forgetting that flag once plans the host back down
# with nothing to warn you.
#
# WHAT THE ALLOWED VALUES ARE, AND WHY THEY ARE ALL t4g: variables.tf's validation admits
# t4g.nano, t4g.micro and t4g.medium. The wireguard module pins the AL2023 ARM64 AMI, so an
# x86 type (t3.medium - the same 2 vCPU / 4 GiB shape as t4g.medium) is not an alternative;
# the validation rejects it at PLAN time, before a stop has happened.
#
# READ BEFORE SWITCHING - the two pre-flight commands, what the plan must say, what survives
# the stop/start, and the one thing that does NOT follow this file (the cost tables and
# `make status` stay written against t4g.nano): docs/plan/runbooks/vpn.md section S6.

instance_type = "t4g.medium"
