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
#                     (t3.nano, D4's shape). The plan reads `~ instance_type` with `1 to
#                     change` on the way down exactly as it did on the way up. Terraform
#                     stops, modifies and starts the instance in one apply.
#
#                     WITHIN ONE FAMILY, which is the whole of what this key can do. The
#                     ARCHITECTURE is not here and never was: it is the module's AMI, moved
#                     from arm64 to x86_64 on 2026-08-20, which is why every value below is
#                     now a t3 where it was a t4g. That move REPLACES the host; this key
#                     never does.
#
#   root_volume_size  ONE WAY - GiB, and UP ONLY. The two warnings below are this key's
#                     whole difference from the one above; read them before assigning.
#
# ---------------------------------------------------------------------------------------
# WARNING 1 - THIS IS NOT REVERSIBLE. EBS GROWS A VOLUME; IT CANNOT SHRINK ONE.
# ---------------------------------------------------------------------------------------
#
# Growing is cheap and in place: the provider issues ModifyVolume and does not even stop the
# instance. GOING BACK IS NOT THE MIRROR OF THAT. Commenting this assignment out does NOT
# return the disk the way commenting out instance_type returns the type - it asks for a
# shrink, and EBS refuses. There is no flag, no force and no apply that undoes it.
#
# The only way down is a HOST REPLACEMENT: a new instance on a new root volume, with
# /etc/wireguard/ rebuilt from the [P] secret and the roster - Part K's rules, not this
# file's. So assign a value you intend to KEEP, and assign it once. The validation in
# variables.tf caps this at 128 GiB for the same reason: past that, an accident is a
# standing bill nobody can hand back.
#
# ---------------------------------------------------------------------------------------
# WARNING 2 - GROWING THE VOLUME DOES NOT GROW THE FILESYSTEM.
# ---------------------------------------------------------------------------------------
#
# ModifyVolume hands the instance a bigger BLOCK DEVICE. The partition and the XFS on top of
# it are untouched until something grows them, and on AL2023 that something is cloud-init's
# growpart, WHICH RUNS AT BOOT. So the apply can succeed, `lsblk` can show the new size, and
# `df -h /` still show the old one - a host billed for space it cannot use.
#
#   IF THE DISK CHANGE RIDES ALONG WITH AN instance_type SWITCH: nothing to do. That apply
#   stops and starts the host, so growpart runs and the filesystem follows by itself.
#
#   IF THE DISK CHANGE GOES OUT ALONE (host left running, which is the normal case when only
#   this key moved): the filesystem does NOT follow. Either reboot the host, or grow it by
#   hand in an SSM session (vpn.md section K0a):
#
#       sudo growpart /dev/nvme0n1 1 && sudo xfs_growfs -d /
#
#   THEN CONFIRM, and read BOTH - they are what can disagree:
#
#       lsblk && df -h /
#
# `./aws/vpn.py` reports the volume in section 2 and VP-1, but that is DescribeVolumes - the
# device half only. The filesystem half is `./aws/vpn.py --on-host`, or the commands above.
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
# WHAT THE ALLOWED VALUES ARE. instance_type: variables.tf's validation admits t3.nano,
# t3.micro and t3.medium, and they are ALL t3 because the wireguard module pins the AL2023
# X86_64 AMI - a Graviton type (t4g.medium, the same 2 vCPU / 4 GiB shape as t3.medium) is not
# an alternative, and the validation rejects it at PLAN time, before a stop has happened.
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


#instance_type    = "t3.nano"
#instance_type    = "t3.medium"
instance_type    = "t3.xlarge"
root_volume_size = 64
