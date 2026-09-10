# vpn-anchors.tf - what is left of Stage 4's [P] VPN anchors: a `removed` block for the Elastic IP.
#
# The tunnel moved to Production's VPC-Networking at 6c pass 4 (2026-09-06; D38). The Elastic IP was
# transferred between accounts - the address kept its value and arrived under a new allocation id,
# imported into production/networking/ at step 4.6 - so the object this slice created is no longer
# this account's. `destroy = false` forgets it here and never releases it; a release would take the
# tunnel's endpoint away from every enrolled device.
#
# The other anchors left at 6c step 6.5, once the VPN_HOMES trim had removed the last remote-state
# read of them: the security group - world-open UDP/51820 guarding no listener since 4.13's first
# half, and the estate's second world-open rule while it stood (VP-3 reads every account since,
# Lesson 31) - and the host-key secret container, whose value was copied by hand into the Production
# secret at 4.3 and which keeps Secrets Manager's 30-day recovery window here. `sandbox.internal`
# went in the same apply (zones.tf).
removed {
  from = aws_eip.wireguard

  lifecycle {
    destroy = false
  }
}
