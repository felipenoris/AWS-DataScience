# THE BUILD HOST'S SHAPE - the second tracked tfvars in this repository, and it deliberately
# carries the same NAME and the same two keys as production/vpn/instance_type.auto.tfvars so
# that a reader who knows one knows this one. .gitignore names it as an exception to the
# wholesale *.tfvars ignore and ./scripts/check-tfvars-shape.py allows it exactly these two
# keys. It carries no account id, no address and no key material.
#
# WHAT IS DIFFERENT FROM THE VPN'S COPY, AND IT IS THE ONLY THING WORTH READING TWICE:
#
#   there   the host is [D]. The disk is a STANDING cost that EBS will not shrink, so
#           root_volume_size is a commitment and going back is a host replacement.
#   here    the host is [E]. Volume and instance are created together and destroyed
#           together, so a value that turns out wrong costs one `buildbox.py down` and one
#           `buildbox.py up`. Assign freely; just do not leave it up.
#
# AND THE DEFAULT MEANS SOMETHING DIFFERENT. In the VPN's file the default is a posture to
# fall back to; here it is a FLOOR - the shape that can actually build the image - so the
# values below and variables.tf's defaults deliberately AGREE. Commenting a line out changes
# nothing, which is the honest outcome when there is no cheaper posture to return to.
#
# THE COST, MEASURED (docs/PRICING.md 8, us-west-2, 2026-09-11) - and it is not small against
# D12's USD 50/month, which is why every helper the script prints ends in `down`:
#
#   m8i.large    2 vCPU,  8 GiB   0.1058 USD/h
#   m8i.xlarge   4 vCPU, 16 GiB   0.2117 USD/h    <- assigned below
#   m8i.2xlarge  8 vCPU, 32 GiB   0.4234 USD/h
#
#   + gp3 at 0.08 USD/GB-month: 64 GiB is ~5.12/month IF it stood, ~0.007/h while it does not
#
# An m8i.xlarge left running for a week is USD 36. `./scripts/buildbox.py status` is the reading;
# `./scripts/buildbox.py down` is the cure. A build session is THREE bills (6c step 5.8): this
# host, production/egress/ at 0.130 USD/h ([E] - its SSM endpoints are the only door in) and
# the proxy's t3.micro at 0.0104 ([D], the whole estate's egress). `down` ends only the first -
# docs/plan/runbooks/buildbox.md section X.
#
# ONE THING THIS FILE CANNOT MAKE FASTER, said here because it is where somebody will come
# looking when a build crawls: every byte this host pulls from the INTERNET crosses the
# explicit proxy, a t3.micro (production/proxy/'s `instance_type` variable). Sizing THIS host
# up does not widen that. What does not cross it: a private-registry pull's layers (the S3
# gateway endpoint) and the push (the ecr.dkr interface endpoint).
#
# The proxy is not the ceiling, and that is measured rather than argued (the 02:50-03:15 UTC
# build of 2026-09-11, squid's access log against the two hosts' EC2 metrics). The proxy moved
# 3.11 GB in its busiest minute - 414 Mbps, 6.5x its own 64 Mbps baseline - at 2.70% CPU with
# its credit balance never leaving 288. This host sat at 99.98% CPU in two consecutive
# five-minute bins, its own credits never falling and its surplus balance at zero: the build
# ran out of vCPU, not of pipe and not of credit. EBS write peaked at 75.5 MB/s against the
# t3.xlarge's 86.875 baseline, 87% of it.
#
# That is what moved the family from t3 to m8i on 2026-09-11: same 4 vCPU and same 16 GiB, but
# dedicated cores at 3.9 GHz instead of burstable at 2.5, and EBS at 156.25 MB/s and 6000 IOPS
# instead of 86.875 and 4000. The build is expected to shorten by a fifth to a quarter; that
# part is an estimate and the next session's wall clock is what settles it.
#
# HOW TO APPLY EITHER - the name ends in .auto.tfvars, so Terraform loads it by itself and
# there is no -var-file to forget:
#
#   ./scripts/buildbox.py up


instance_type = "m8i.xlarge"
#instance_type    = "m8i.large"
#instance_type    = "m8i.2xlarge"
root_volume_size = 64
