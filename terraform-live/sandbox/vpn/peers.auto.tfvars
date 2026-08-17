# peers.auto.tfvars - THE ROSTER, and the one TRACKED tfvars in this repository (Stage 4,
# second design review, 2026-08-16). PUBLIC halves only.
#
# WHY TRACKED, when the wholesale *.tfvars rule ignores everything else: this map is the
# VPN's authorization roster - who may enter the network - and a roster benefits from review
# and history. Adding a device is a reviewable diff; revoking one is a one-line deletion
# with a date on it (D4 accepted exactly that price when it declined Identity Center
# integration). First add needs the -f once - `git add -f terraform-live/sandbox/vpn/peers.auto.tfvars` -
# and a tracked file stays tracked.
#
# WHY THE SHAPE IS ENFORCED: a WireGuard private key is indistinguishable from a public one
# by format (44 chars of base64), so no scanner could catch the paste that matters. The gate
# ./scripts/check-tfvars-shape.py holds this file to STRUCTURE instead - it may assign
# `peers`, with `public_key` and `host` per entry, and nothing else. The server's PRIVATE
# key never enters a tfvars at all: it lives in the [P] Secrets Manager secret
# awsds-sandbox-vpn-host-key (step 4.3; decision 4, third review).
#
# One entry per PERSON PER DEVICE (Stage 4 step 4.1):
#   public_key  the device's public half, generated ON the device (step 4.1). On a laptop, the
#               silent form of 4.3, run outside this repository:
#                 (umask 077 && wg genkey | tr -d '\n' > d-private.key) && wg pubkey < d-private.key > d-public.key
#               On a phone, the WireGuard app generates the pair itself and shows the public
#               half on screen. Either way the private half never leaves the device.
#   host        the device's address inside peer_cidr: 10.90.0.<host>. The server holds .1.
#               AUTHORED, never derived from position - deleting a revoked device must not
#               renumber anybody else's tunnel address.

# The names are what `wg show` prints and what the handshake log group carries, through
# /etc/wireguard/peer-names - so they are read far more often than they are written.
peers = {
  "mbp"   = { public_key = "P2UV4d1fj5D5PTidGxhGfnLnM69kAhTSRTMwGbRJmGg=", host = 2 } # 2026-08-17, step 4.1
  "raspi" = { public_key = "phfyVANT55vq80AYHcmA8vgyp4xAxKs78JxDRoOKtEE=", host = 3 } # 2026-08-17, step 4.1
}
