# THE VPN HOST'S SHAPE - the one tfvars in this repository a person edits to change what is
# running, and it is TRACKED on purpose (.gitignore names it as an exception to the wholesale
# *.tfvars ignore; ./scripts/check-tfvars-shape.py allows it exactly the two keys below). It
# carries no account id, no address and no key material: a machine size and a disk size, two
# decisions worth having in git history rather than in somebody's shell.
#
# THE NAME STILL SAYS instance_type AND THE FILE NOW HOLDS TWO KEYS (2026-08-20). Renaming it
# would cost the .gitignore negation, this gate's SIZE constant and every path written about
# it, and would buy what this paragraph buys. The name is provenance, not an index.
#
# THE TWO KEYS DO NOT BEHAVE THE SAME WAY - read this before assuming symmetry:
#
#   instance_type     BOTH DIRECTIONS. Assign it to switch the host up; COMMENT THE
#                     ASSIGNMENT OUT and apply to fall back to variables.tf's default
#                     (t4g.nano, D4's shape). The plan reads `~ instance_type` with `1 to
#                     change` on the way down exactly as it did on the way up. Terraform
#                     stops, modifies and starts the instance in one apply.
#
#   root_volume_size  ONE WAY - GiB, and UP ONLY. EBS grows a volume in place (ModifyVolume,
#                     with the instance left RUNNING), but it CANNOT SHRINK ONE. Commenting
#                     this assignment out therefore does NOT return the disk: it asks for a
#                     shrink that EBS refuses. Going smaller is a host REPLACEMENT, under Part
#                     K's rules, never an apply. And GROWING THE VOLUME IS NOT GROWING THE
#                     FILESYSTEM: the extra GiB reach the OS at BOOT, when cloud-init's
#                     growpart runs - so a disk change that rides along with an instance_type
#                     switch is picked up by the stop/start that switch performs, while a disk
#                     change made ALONE needs a reboot or a hand-run growpart + xfs_growfs
#                     (AL2023's root is xfs). Section S6 has the two readings that prove it.
#
# HOW TO APPLY EITHER OF THEM - and there is no flag in any direction:
#
#   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply
#
# THE NAME ENDS IN .auto.tfvars BECAUSE THAT IS WHAT MAKES TERRAFORM LOAD IT BY ITSELF - the
# apply above is complete as written. Named instance_type.tfvars instead, every plan and apply
# would have to carry the file:
#
#   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn apply -var-file=instance_type.tfvars
#
# (-chdir is an option of `terraform` and goes BEFORE the subcommand; -var-file is an option
# of the subcommand and goes after it.) Forgetting that flag once plans the host back down
# with nothing to warn you.
#
# WHAT THE ALLOWED VALUES ARE. instance_type: variables.tf's validation admits t4g.nano,
# t4g.micro and t4g.medium, and they are ALL t4g because the wireguard module pins the AL2023
# ARM64 AMI - an x86 type (t3.medium, the same 2 vCPU / 4 GiB shape as t4g.medium) is not an
# alternative, and the validation rejects it at PLAN time, before a stop has happened.
# root_volume_size: 8 to 128 GiB - 8 being the AL2023 image's own snapshot size, which is the
# floor EC2 accepts for a root volume, and 128 the ceiling where a fat-fingered 640 is caught
# at plan time rather than on a bill.
#
# WHAT THE DISK COSTS, AND WHAT DOES NOT FOLLOW THIS FILE: EBS is a STANDING cost - it accrues
# while the host is STOPPED, which is the deal a [D] slice makes - at 0.08 USD/GB-mo in
# us-west-2 (docs/PRICING.md 8). 64 GiB is therefore ~5.12 USD/month against the 8 GiB
# default's ~0.64, paid every month whether or not the tunnel is ever brought up. Neither
# `make status` nor docs/PRICING.md 2's WireGuard row follows this file: both stay written
# against the DEFAULTS, deliberately, for the reason section S6 gives.
#
# READ BEFORE SWITCHING EITHER - the pre-flight commands, what the plan must say, what survives
# the stop/start, and how to confirm the filesystem actually grew rather than assuming it did:
# docs/plan/runbooks/vpn.md section S6.

instance_type    = "t4g.medium"
root_volume_size = 64
