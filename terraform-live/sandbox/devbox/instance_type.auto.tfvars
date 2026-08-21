# THE BUILD HOST'S SHAPE - the second tracked tfvars in this repository, and it deliberately
# carries the same NAME and the same two keys as sandbox/vpn/instance_type.auto.tfvars so
# that a reader who knows one knows this one. .gitignore names it as an exception to the
# wholesale *.tfvars ignore and ./scripts/check-tfvars-shape.py allows it exactly these two
# keys. It carries no account id, no address and no key material.
#
# WHAT IS DIFFERENT FROM THE VPN'S COPY, AND IT IS THE ONLY THING WORTH READING TWICE:
#
#   there   the host is [D]. The disk is a STANDING cost that EBS will not shrink, so
#           root_volume_size is a commitment and going back is a host replacement.
#   here    the host is [E]. Volume and instance are created together and destroyed
#           together, so a value that turns out wrong costs one `devbox.py down` and one
#           `devbox.py up`. Assign freely; just do not leave it up.
#
# AND THE DEFAULT MEANS SOMETHING DIFFERENT. In the VPN's file the default is a posture to
# fall back to; here it is a FLOOR - the shape that can actually build the image - so the
# values below and variables.tf's defaults deliberately AGREE. Commenting a line out changes
# nothing, which is the honest outcome when there is no cheaper posture to return to.
#
# THE COST, MEASURED (docs/PRICING.md 8, us-west-2, 2026-08-21) - and it is not small against
# D12's USD 50/month, which is why every helper the script prints ends in `down`:
#
#   t3.large    2 vCPU,  8 GiB   0.0832 USD/h
#   t3.xlarge   4 vCPU, 16 GiB   0.1664 USD/h    <- assigned below
#   t3.2xlarge  8 vCPU, 32 GiB   0.3328 USD/h
#
#   + gp3 at 0.08 USD/GB-month: 64 GiB is ~5.12/month IF it stood, ~0.007/h while it does not
#
# A t3.xlarge left running for a week is USD 28. `./scripts/devbox.py status` is the reading;
# `./scripts/devbox.py down` is the cure. The WireGuard host is the OTHER half of that bill
# while a build runs, and it is a [D] host that `down` deliberately does NOT stop - see the
# script's own note.
#
# ONE THING THIS FILE CANNOT MAKE FASTER, said here because it is where somebody will come
# looking when a build crawls: every byte this host pulls from the internet crosses the
# WireGuard host, which is a t3.nano by default. Sizing THIS host up does not widen that.
# If the build is network-bound rather than CPU-bound, the knob is sandbox/vpn/'s copy of this
# file (docs/plan/runbooks/vpn.md section S6), not this one.
#
# HOW TO APPLY EITHER - the name ends in .auto.tfvars, so Terraform loads it by itself and
# there is no -var-file to forget:
#
#   ./scripts/devbox.py up


instance_type = "t3.xlarge"
#instance_type    = "t3.large"
#instance_type    = "t3.2xlarge"
root_volume_size = 64
