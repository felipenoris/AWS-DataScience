# Runbook — The VPN client: writing a config, connecting, disconnecting

| | |
|---|---|
| **Scope** | One enrolled device's side of the tunnel — writing its `.conf`, bringing it up, proving it, taking it down. The **server** side (roster, keys, rotation) is [vpn-keys.md](vpn-keys.md); enrolling a device at all is its §4 |
| **Operator** | The device's owner, on the device. No AWS profile and no SSO session are needed: nothing here calls an AWS API |
| **The one rule** | **Full tunnel, never split.** `AllowedIPs = 0.0.0.0/0, ::/0` — both families. Step 8's `aws:SourceIp` can only match traffic that actually exits through the Elastic IP, so a split tunnel would leave every API call on the laptop's own connection and step 8 would deny the user everything, tunnel up or not. The two stand or fall together |
| **Written** | 2026-08-17, from the first handshake (`mbp`, Stage 4 step 5) — [Stage 4](../stages/stage-04-vpn.md) step 5 is the requirement, step 9.1 the deliverable |

## 0. The five values, and where each comes from

Nothing here is invented, and three of the five are **stable by design** — which is the property
decision 4 bought and step 4.2 proved by rebuilding the host without moving either the address or the
key.

| Line | Value today | Where it comes from |
|---|---|---|
| `PrivateKey` | this device's own | Generated **on the device** and never anywhere else ([vpn-keys.md](vpn-keys.md) §4). Read from its file, never retyped |
| `Address` | `10.90.0.<host>/32` | `cidrhost(peer_cidr, host)` — the device's `host` number in the tracked roster `peers.auto.tfvars`, and `peer_cidr` from the allocation table. `/32`, mirroring the server's `AllowedIPs`: a peer does not reach another peer |
| `DNS` | `10.20.0.2` | `.2` of the VPN home's VPC CIDR (`10.20.0.0/16`) — the VPC resolver, so private hosted zones and interface-endpoint names resolve on the device |
| `PublicKey` | the host's | **`[P]`, in a Secrets Manager secret** — it survives every instance rebuild. Recover it without touching the secret: `host-public.key` on the laptop, this line in any existing config, or `wg show wg0 public-key` on the host |
| `Endpoint` | `52.89.212.1:51820` | The **`[P]` Elastic IP**, allocated in `sandbox/foundation/` a slice away from the host, plus the one port open to the world |

**If either of the last two ever changes without [vpn-keys.md](vpn-keys.md) §3 having been run, that is a
finding, not a reconnection problem.**

## 1. Write the config

**Outside the repository** — `cd ~` first, and it is not housekeeping: this file carries a private key,
and `.gitignore` grew a `*.conf` rule on the day this runbook was written **as the net under this
practice, not as a substitute for it**. Pre-commit's `detect-private-key` reads PEM armor; a WireGuard
key is bare base64, indistinguishable from the public halves this repository commits on purpose, so no
scanner would catch a committed client config. The glob is the only thing that can.

```bash
cd ~ && (umask 077 && cat > mbp.conf <<EOF
[Interface]
PrivateKey = $(cat mbp-private.key)
Address = 10.90.0.2/32
DNS = 10.20.0.2

[Peer]
PublicKey = LCD1d6xjsxRAmOZA/FTo72TToGUkLYqlOryEJwfup28=
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = 52.89.212.1:51820
PersistentKeepalive = 25
EOF
)
```

**The private key is read from its file and never typed**, so it reaches neither the screen nor the
shell history. The `umask 077` sits **inside the subshell** on purpose: the config lands `600` at
creation, and the interactive shell's umask is left alone.

For another device, the only line that changes is `Address` — its own `host` number from the roster.
On a phone or tablet there is no file at all: the WireGuard app holds the private key it generated and
the other four values are typed into its form.

## 2. Up, and the three things that prove three different claims

```bash
sudo wg-quick up ~/mbp.conf
```

```bash
sudo wg show
```

`latest handshake: N seconds ago` and non-zero `transfer` — **the tunnel exists**. On macOS the
interface is a `utun*`, not `wg0`.

```bash
curl -s https://checkip.amazonaws.com
```

Must print **`52.89.212.1`** — **the full tunnel is real**, traffic leaving through the host's NAT.
This is the one that step 8 depends on: its `aws:SourceIp` matches this address or nothing.

```bash
dig +short SOA sandbox.internal
```

Must answer — **`DNS = 10.20.0.2` is in use**. `sandbox.internal` is the private hosted zone associated
with the VPN home's VPC, so it resolves through the VPC resolver and **NXDOMAIN everywhere else**;
answering is therefore the proof, and this is what Stage 5 will need to mount EFS by name. (Do **not**
pin an `ip-10-20-…compute.internal` name here instead: it encodes the instance's private IP and dies at
every replacement — and a peer change replaces the host.)

## 3. Down

```bash
sudo wg-quick down ~/mbp.conf
```

The config file stays; nothing is revoked, nothing on the server changes. Reconnecting is §2.

## 4. When it does not work

- **No handshake ever appears, and there is no error.** The network is dropping **outbound UDP/51820** —
  common on corporate and café Wi-Fi. WireGuard is silent about it by design: it is a UDP protocol that
  never answers unauthenticated packets, so there is nothing to time out visibly. Test from another
  network before suspecting anything in AWS.
- **IPv6 appears broken while connected.** It is: `::/0` routes IPv6 into a tunnel that carries only
  IPv4, so IPv6 is deliberately black-holed. That is the point — on a dual-stack network an AWS call
  over IPv6 would carry an IPv6 source, fail step 8's `NotIpAddress` and read as a lockout *with the
  tunnel up*. Happy Eyeballs falls back to IPv4; a site may pause a moment first.
- **`handshake_age_s` grows without resetting** in the log group `/awsds/sandbox/vpn`. With
  `PersistentKeepalive = 25` the keepalives count as data, so a live tunnel renegotiates about every two
  minutes and the age returns to zero on its own. **An age that only grows means the client stopped
  sending** — the tunnel was taken down (the ordinary case), or the device slept, the network changed,
  or a NAT expired the UDP mapping. The log cannot tell those apart; the device can.
- **`peer=unknown` in that log** is not a client problem at all: it is a peer the roster does not know
  about ([vpn-keys.md](vpn-keys.md) §4).

## 5. What it costs

**Every byte the device sends anywhere transits the instance** and bills as data transfer out,
~USD 0.09/GB — ordinary browsing included. Connect for lab sessions; this is not an always-on VPN
(Stage 4 step 5.3).

---

*Stage: [stage-04-vpn.md](../stages/stage-04-vpn.md) · The server side, and enrolling a device:
[vpn-keys.md](vpn-keys.md) · Slice:
[`terraform-live/sandbox/vpn/`](../../../terraform-live/sandbox/vpn/README.md)*
