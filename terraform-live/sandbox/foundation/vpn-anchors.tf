# vpn-anchors.tf - WHAT IS LEFT OF STAGE 4's [P] VPN ANCHORS: one `removed` block.
#
# The tunnel moved to Production's VPC-Networking at 6c pass 4 (2026-09-06; D38). The Elastic
# IP was TRANSFERRED between accounts - the address kept its value and arrived under a NEW
# allocation id, imported into production/networking/ at step 4.6 - so the object this slice
# created is no longer this account's, and `destroy = false` is the only honest verb: forget
# it here, never release it (a release would take the tunnel's endpoint away from every
# enrolled device). Until this block landed the slice was FROZEN: the stale entry refreshed to
# nothing and every plan read `1 to add`, a SECOND allocation nobody wanted.
#
# The other two anchors left at 6c step 6.5 (2026-09-07), in the apply that unfroze this slice
# once the VPN_HOMES trim had removed the last remote-state read of it: the security group -
# world-open UDP/51820 guarding no listener since 4.13's first half, and the estate's second
# world-open rule while it stood (VP-3 reads every account since, Lesson 31) - and the
# host-key secret container, whose VALUE was copied by hand into the Production secret at 4.3
# and which keeps Secrets Manager's 30-day recovery window here. `sandbox.internal` went in
# the same apply (zones.tf).
removed {
  from = aws_eip.wireguard

  lifecycle {
    destroy = false
  }
}
