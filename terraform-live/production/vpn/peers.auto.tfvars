# peers.auto.tfvars - THE ROSTER, moved account with the tunnel (Stage 6c step 4.7). PUBLIC
# halves only, and it is the SAME roster the Sandbox slice carried: the point of transferring
# the Elastic IP and copying the host key by hand is that no device's `.conf` changes, and a
# roster that changed here would undo that in the one place nobody would look.
#
# WHY TRACKED, when the wholesale *.tfvars rule ignores everything else: this map is the VPN's
# authorization roster - who may enter the network - and a roster benefits from review and
# history. Adding a device is a reviewable diff; revoking one is a one-line deletion with a date
# on it (D4 accepted exactly that price when it declined Identity Center integration).
#
# WHY THE SHAPE IS ENFORCED: a WireGuard private key is indistinguishable from a public one by
# format (44 chars of base64), so no scanner could catch the paste that matters.
# ./scripts/check-tfvars-shape.py holds this file to STRUCTURE instead - it may assign `peers`,
# with `public_key` and `host` per entry, and nothing else. The SERVER's private key never enters
# a tfvars at all: it lives in the [P] secret `awsds-prod-vpn-host-key`, written by hand at 4.3.
#
# One entry per PERSON PER DEVICE, and `host` is AUTHORED rather than derived from position -
# deleting a revoked device must not renumber anybody else's tunnel address. The full procedure,
# key generation included, is docs/plan/runbooks/vpn.md part K.

# The names are what `wg show` prints and what the handshake log group carries, through
# /etc/wireguard/peer-names - so they are read far more often than they are written.
peers = {
  "mbp"   = { public_key = "P2UV4d1fj5D5PTidGxhGfnLnM69kAhTSRTMwGbRJmGg=", host = 2 } # 2026-08-17, Stage 4 step 4.1
  "raspi" = { public_key = "phfyVANT55vq80AYHcmA8vgyp4xAxKs78JxDRoOKtEE=", host = 3 } # 2026-08-17, Stage 4 step 4.1
}
