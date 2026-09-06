# THE VPN HOST'S SHAPE - a machine size and a disk size, TRACKED on purpose (.gitignore names it
# as an exception to the wholesale *.tfvars ignore; ./scripts/check-tfvars-shape.py allows it
# exactly the two keys below). No account id, no address, no key material: two decisions worth
# having in git history rather than in somebody's shell.
#
# THE NAME STILL SAYS instance_type AND THE FILE HOLDS TWO KEYS. The name is provenance, not an
# index - renaming it would cost the .gitignore negation, the gate's constant and every path
# written about it, and would buy what this paragraph buys.
#
# THE TWO KEYS DO NOT BEHAVE THE SAME WAY, and that asymmetry is the only thing to read before
# assigning either:
#
#   instance_type     BOTH DIRECTIONS. Assign to switch up; COMMENT THE ASSIGNMENT OUT and apply
#                     to fall back to variables.tf's default (t3.nano, D4's shape). Terraform
#                     stops, modifies and starts the instance in one apply. WITHIN ONE FAMILY:
#                     the ARCHITECTURE is the module's AMI (x86_64 since 2026-08-20), which is
#                     why every admitted value is a t3 and not a t4g. That move REPLACES the
#                     host; this key never does.
#
#   root_volume_size  ONE WAY - GiB, UP ONLY. EBS grows a volume in place and CANNOT SHRINK ONE:
#                     commenting the assignment out asks for a shrink and EBS refuses, with no
#                     flag and no force. The only way down is a host REPLACEMENT. And growing the
#                     volume does NOT grow the filesystem - growpart runs at BOOT, so a change
#                     that goes out alone needs a reboot or a hand-run
#                     `sudo growpart /dev/nvme0n1 1 && sudo xfs_growfs -d /`, confirmed with
#                     `lsblk && df -h /` (both - they are what can disagree).
#
# APPLY EITHER WITH NO FLAG IN ANY DIRECTION - the `.auto.` in the name is what makes Terraform
# load the file by itself:
#
#   AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/vpn apply
#
# THE FULL PROCEDURE - pre-flight readings, what the plan must say, what survives the stop/start,
# how to confirm the filesystem actually grew rather than assuming it did, and the cost
# arithmetic (EBS bills while the host is STOPPED, 0.08 USD/GB-mo): docs/plan/runbooks/vpn.md
# section S6. It is the durable home of this argument; this header is the reminder at the keyboard.

instance_type = "t3.nano"
#instance_type    = "t3.medium"
root_volume_size = 8
