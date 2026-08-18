# Runbook — The VPN client: writing a config, connecting, disconnecting

| | |
|---|---|
| **Scope** | One enrolled device's side of the tunnel — writing its `.conf`, bringing it up, proving it, taking it down. The **server** side (roster, keys, rotation) is [vpn-keys.md](vpn-keys.md); enrolling a device at all is its §4 |
| **Operator** | The device's owner, on the device. No AWS profile and no SSO session are needed: nothing here calls an AWS API |
| **The one rule** | **Full tunnel, never split.** `AllowedIPs = 0.0.0.0/0, ::/0` — both families. Step 8's `aws:SourceIp` can only match traffic that actually exits through the Elastic IP, so a split tunnel would leave every API call on the laptop's own connection and step 8 would deny the user everything, tunnel up or not. The two stand or fall together |
| **Written** | 2026-08-17, from the first handshake (`mbp`, Stage 4 step 5) — [Stage 4](../stages/stage-04-vpn.md) step 5 is the requirement, step 9.1 the deliverable |

## 0. The values, and where each comes from — five from the design, one from the path

Nothing here is invented, and three of the five are **stable by design** — which is the property
decision 4 bought and step 4.2 proved by rebuilding the host without moving either the address or the
key. **`MTU` is the exception and belongs in a different category**: it is the only line whose correct
value is a property of the network the device happens to be sitting on, so it is derived from nothing in
AWS and is the one line worth re-examining when a working config stops working somewhere new (§4).

| Line | Value today | Where it comes from |
|---|---|---|
| `PrivateKey` | this device's own | Generated **on the device** and never anywhere else ([vpn-keys.md](vpn-keys.md) §4). Read from its file, never retyped |
| `Address` | `10.90.0.<host>/32` | `cidrhost(peer_cidr, host)` — the device's `host` number in the tracked roster `peers.auto.tfvars`, and `peer_cidr` from the allocation table. `/32`, mirroring the server's `AllowedIPs`: a peer does not reach another peer |
| `DNS` | `10.20.0.2` | `.2` of the VPN home's VPC CIDR (`10.20.0.0/16`) — the VPC resolver, so private hosted zones and interface-endpoint names resolve on the device |
| `PublicKey` | the host's | **`[P]`, in a Secrets Manager secret** — it survives every instance rebuild. Recover it without touching the secret: `host-public.key` on the laptop, this line in any existing config, or `wg show wg0 public-key` on the host |
| `Endpoint` | `52.89.212.1:51820` | The **`[P]` Elastic IP**, allocated in `sandbox/foundation/` a slice away from the host, plus the one port open to the world |
| `MTU` | `1280` | **The path, not the design.** Absent this line `wg-quick` derives it — the MTU of the interface reaching the endpoint, minus 80 — and that derivation is wrong on any path narrower than the local link, phone tethering above all (§4, measured 2026-08-17). **The server pins the same 1280 since 2026-08-18**, which does *not* make this line optional: the two govern opposite directions, and this one is the only thing bounding what **this device sends** |

**If either of the two key/endpoint lines ever changes without [vpn-keys.md](vpn-keys.md) §3 having been
run, that is a finding, not a reconnection problem.**

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
MTU = 1280

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

**`MTU = 1280` is in the template rather than in a troubleshooting note, and that is deliberate.** The
alternative — "add this line if the tunnel misbehaves" — is an intention, and the failure it prevents is
one nobody diagnoses at 23:00 in an airport (§4). 1280 is the IPv6 minimum and passes every path
encountered so far; it costs a little throughput on a wired network, where the value can be raised once
a real path MTU has been measured rather than guessed.

**Since 2026-08-18 the server pins `MTU = 1280` on its own `wg0` too, and it covers the other
direction — downloads.** The host used to inherit its uplink's MTU, 9001 on an AWS ENA, so it would
inject up to 8921 bytes into a tunnel whose every peer is reached across the internet; it now refuses
anything over 1280, measured from inside the host (`ping -M do -s 1253` returns a local
`message too long, mtu=1280`, and `-s 1252` does not). **What that buys is not speed and not a fixed
bug: it is not depending on ICMP.** An unpinned client on a 1492-byte PPPoE line — measured, and it is
an ordinary home link — emits 1500-byte outer packets and survives only because a router bothers to send
back `frag needed`. Where that ICMP is filtered, which is common, nothing comes back at all. The line
above removes the dependency for what the device sends; the server's removes it for what the device
receives.

For another device, the only line that changes is `Address` — its own `host` number from the roster.
On a phone or tablet there is no file at all: the WireGuard app holds the private key it generated and
the other values are typed into its form — **including MTU**, which the apps expose in the same
interface section.

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
answering is therefore the proof. (Do **not**
pin an `ip-10-20-…compute.internal` name here instead: it encodes the instance's private IP and dies at
every replacement — and a peer change replaces the host.)

## 3. Down

```bash
sudo wg-quick down ~/mbp.conf
```

The config file stays; nothing is revoked, nothing on the server changes. Reconnecting is §2.

## 4. When it does not work

- **The handshake works, `wg show` counts traffic both ways, DNS answers — and no site loads.** This is
  **MTU**, and it is the failure this runbook exists to stop you from misdiagnosing (measured 2026-08-17,
  on phone tethering, Stage 4 pass 2). **The symptom is graded by packet size**, which is what makes it
  look like something else entirely: the handshake is 148 bytes and succeeds, a DNS query is one small
  UDP exchange and succeeds, and TLS needs a full-MSS certificate chain and times out. WireGuard sets DF
  on its outer packets, so an oversized one is dropped **with no error at either end** — and the natural
  suspicion, a broken NAT on the host, is the expensive wrong turn. **Two answered `dig`s rule the host
  out on their own**: the VPC resolver replies only if the packet was forwarded *and* source-NATed to an
  address inside the VPC, so DNS working means the whole server side is working.
  **The fix is `MTU = 1280` under `[Interface]`** (already in §1's template — if a config predates it,
  this is what to add). Take the tunnel down and up: editing the file while the interface is up does not
  change its MTU.
  **Since 2026-08-18 this symptom should have become one-sided** rather than disappearing: the server
  pins 1280 as well, so a config missing the line still receives fine and stalls on what it *sends* —
  large uploads, a `git push`, a form with an attachment. **If a device with no `MTU` line stalls in
  BOTH directions, the server's pin is not doing its job and that is a finding**, not a client problem:
  read `ip link show wg0` on the host (§2a of `./aws/vpn.py --on-host`, or a Session Manager shell) and
  expect `mtu 1280`. To confirm it was MTU rather than assume it, before and after:

  ```bash
  ping -D -s 1372 -c 3 1.1.1.1 ; ping -D -s 1200 -c 3 1.1.1.1
  ```

  `-D` sets don't-fragment; 1372 of payload is 1400 bytes on the wire. **1200 passing while 1372 fails is
  the proof**; both failing means the problem is elsewhere and the next bullet is where to look.
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
- **Nothing above settled it, and the suspicion has moved to the server.** That is where this runbook
  stops by design — the three checks in §2 exist to rule the device in or out *before* anybody signs in
  to AWS. A shell on the host is an SSM session, opened by the **infrastructure user** and not by the
  device's owner: [vpn-keys.md](vpn-keys.md) §0a, which is also where the `--target` instance id comes
  from. It works with this tunnel down, which is the whole point of it.

## 5. What it costs

**Every byte the device sends anywhere transits the instance** and bills as data transfer out,
~USD 0.09/GB — ordinary browsing included. Connect for lab sessions; this is not an always-on VPN
(Stage 4 step 5.3).

---

*Stage: [stage-04-vpn.md](../stages/stage-04-vpn.md) · The server side, enrolling a device, and a
shell on the host: [vpn-keys.md](vpn-keys.md) (§0a) · Slice:
[`terraform-live/sandbox/vpn/`](../../../terraform-live/sandbox/vpn/README.md)*
