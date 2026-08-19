# Runbook — The VPN

| | |
|---|---|
| **Scope** | The whole VPN surface, in three parts. **Part S — the system**: what the pieces are, which slice owns each, how a packet actually travels, what the VPN is *not* (the NAT), and how the host is started and stopped. **Part C — the client**: one enrolled device's side of the tunnel — writing its `.conf`, bringing it up, proving it, taking it down. **Part K — the server**: the shell on the host (§K0a), the two kinds of key pair, and the four procedures — recovery, revocation, host rotation, device rotation (the last also being how a device is *added*) |
| **Operator** | Parts S and K: the **infrastructure user**, profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in `Sandbox`) — plus `awsds-infra-identity` for §K6's fragment toggles. Part C: the **device's owner, on the device** — no AWS profile and no SSO session: nothing in that part calls an AWS API |
| **The two rules** | **Loss is answered by recovery, never by rotation** (Part K): a new host key forces an instance replacement and breaks every client config at once — each one pins the server's public key. Rotate for *compromise* (§K3), recover for *loss* (§K1); the mechanised violation is Secrets Manager's own rotation feature, off forever (§K5, `VP-9`). **Full tunnel, never split** (Part C): `AllowedIPs = 0.0.0.0/0, ::/0`, both families — `DenyControlPlaneOffVpn`'s `aws:SourceIp` can only match traffic that actually exits through the Elastic IP, so a split tunnel is a lockout with the tunnel up |
| **Written** | The keys half 2026-08-16 (Stage 4's third design review; rewritten the same day when the host key moved into the `[P]` secret), the client half 2026-08-17 (the first handshake). **Unified 2026-08-19, at the user's request, replacing `vpn-keys.md` and `vpn-client.md`** — their content is Parts K and C, kept whole; Part S is new, written from the topology readings of Stage 5 pass 4d's first sitting |

---

## Part S — the system: components, topology, and the host's power state

*New 2026-08-19. Everything in this part was measured in the account (route tables, endpoint ids,
bucket-policy conditions read back), not inferred from the code — the two dates below mark the readings.*

### S1. The components, and which slice owns each

The VPN is two slices plus a tracked roster, split exactly along the `[P]`/`[D]` line — what must
survive forever versus what is powered off between sessions (D11):

| Piece | Where · layer | What it is |
|---|---|---|
| The **Elastic IP** allocation | `sandbox/foundation/` · `[P]` | `52.89.212.1` — the one stable address. Every client config pins it (`Endpoint =`), and so does the `DenyControlPlaneOffVpn` fragment and the lake's bucket-policy branch (§S2). It survives every host stop, start and replacement — only its *association* follows the instance |
| The **security group** `awsds-sandbox-vpn` | `sandbox/foundation/` · `[P]` | carries **the estate's only world-open rule**: UDP/51820 (`VP-3`). Anything else world-open anywhere is a finding |
| The **host-key secret** `awsds-sandbox-vpn-host-key` | `sandbox/foundation/` · `[P]` | the container for the host's private key — value written by the user at enrollment, read by the instance at boot, resource-policy deny on every other reader (§K0) |
| The **WireGuard host** | `sandbox/vpn/` · `[D]` | one `t4g.nano` (arm64) in the **public** subnet of `usw2-az1`, tag `Name=awsds-sandbox-vpn` — the tag is the contract everything looks the host up by (§K0a). `wg0` at `10.90.0.1/24`, IMDSv2 required, no port 22, no key pair — the shell is SSM (§K0a) |
| The **handshake log + alarm** | `sandbox/vpn/` · `[D]` | log group `/awsds/sandbox/vpn` (30 days) with per-peer named lines, and the health alarm `awsds-sandbox-vpn-health` |
| The **roster** `peers.auto.tfvars` | the repository (tracked) | every enrolled device's *public* key and `host` number. Public halves only — the shape gate `./scripts/check-tfvars-shape.py` refuses the regressions it can see (§K5) |

`./aws/vpn.py` reads all of it — `VP-1` through `VP-9` — and is the first thing to run when any
question about this system comes up.

### S2. How a packet travels — the topology, measured (2026-08-19)

The host sits in the **public subnet**, and that placement decides everything:

```
laptop 10.90.0.2 ──wg0──▶ host (masquerade: source becomes the host's own address)
                              │
                              ▼ the PUBLIC subnet's route table
          ┌───────────────────┼──────────────────────────────┐
          ▼                   ▼                              ▼
   0.0.0.0/0 → IGW     S3 / DynamoDB prefix lists     10.30.x.x → peering
   (exits as the        → the [P] GATEWAY endpoints    (Production, Stage 3)
    Elastic IP)           of foundation/
```

- **The masquerade is the mechanism**: `iptables -t nat … -j MASQUERADE` in the user data rewrites
  every forwarded packet's source to the host's own address, so tunnel traffic leaves AWS carrying
  the Elastic IP. `source_dest_check` stays **on**, deliberately — with everything masqueraded,
  nothing legitimate is asymmetric, and a broken masquerade rule drops traffic *visibly at the host*
  instead of emitting `10.90.0.x`-sourced packets a peering would discard three hops later
  ([`terraform-modules/wireguard/main.tf`](../../../terraform-modules/wireguard/main.tf)).
- **The path splits by destination, and the lake's perimeter policy mirrors the split exactly.**
  The public subnet's route table carries the two `[P]` **gateway endpoints** (S3, DynamoDB), so S3
  calls from the tunnel arrive at a bucket as **`aws:SourceVpce`** — the endpoint-id branch, the
  INT-05 anchors — while every other API (Athena, Glue, KMS, STS…) exits through the IGW and arrives
  as **`aws:SourceIp` = the Elastic IP**. Read back from the drop-box bucket policy on 2026-08-19:
  its `DenyOutsideTrustedNetworks` condition names exactly that S3 gateway endpoint id and exactly
  that `/32` — the two branches are this route table, restated as policy.
- **One consequence for negative proofs, found the same day**: the same condition carries an
  `aws:PrincipalAccount` branch admitting the lake account's *own* principals from any network — so a
  "denied outside every branch" proof must run as a principal from a **different** account, or it
  proves nothing.

### S3. What the VPN is *not*: the NAT and the interface endpoints

**`sandbox/egress/` is not part of the VPN path, and starting it for a VPN session is pure cost.**
The confusion is natural — both are "how traffic gets out" — and the split is topological:

| | The VPN host (`vpn/`, `[D]`) | The egress slice (`egress/`, `[E]`) |
|---|---|---|
| Serves | devices **outside** AWS, over the tunnel | resources **inside** the private subnets, with no public IP |
| Exit | its own Elastic IP, via the **IGW** of the public subnet | the **NAT gateway** — its route is installed in the *private* route tables only |
| Endpoints | the `[P]` **gateway** endpoints (free, in `foundation/`, always there) | the `[E]` **interface** endpoints (billed hourly, new ids every `make up`) |
| Who needs it | every Stage 5 pass 4d proof — all run from the laptop | Stage 6's notebooks, Stage 7's runners — anything that *lives* in a private subnet |
| At-rest burn | USD 0.0042/h running | USD 0.160/h (NAT + 11 interface endpoints), plus `probes/` if applied |

The two never meet: the host's subnet routes `0.0.0.0/0` to the IGW, the NAT's route exists only in
the private tables. A session that needs only the tunnel starts only the host (§S5).

### S4. Why persona work needs the tunnel at all

Two independent controls, either alone sufficient:

1. **All six persona permission sets carry `DenyControlPlaneOffVpn`** (`VP-7`) — off the tunnel, a
   persona can make no control-plane call at all. `InfrastructureAccess` is deliberately *outside*
   the deny (open question 17): it is the recovery path, and the identity that starts the very host
   the tunnel runs on (§S5's loop).
2. **The lake's bucket policies admit only §S2's two branches** — the Elastic IP and the consumers'
   gateway endpoints (D18, INT-05). Off the tunnel, even a call that IAM would allow dies at the
   resource.

### S5. Start and stop the host

`[D]` means the host is **stopped between sessions and started for one** — never destroyed, never
re-applied by a lifecycle target (refusal 5 in `scripts/tfhygiene/layers.py`). Across stop/start
nothing moves: the Elastic IP stays associated (Stage 4 verification (ii); re-measured 2026-08-19,
`VP-2`), the EBS volume keeps `/etc/wireguard/`, and every client config stays valid. What bills
while stopped is the monthly floor — EIP ~USD 3.65 + secret ~USD 0.40 + 8 GB gp3 — not the hourly
rate.

**Two sanctioned ways up, chosen by what the session needs:**

1. **`make up ENV=sandbox`** — starts the host **and** applies the account's `[E]` slices
   (`egress/` + `probes/`, ~USD 0.173/h all-in). Right when the session needs the private-subnet
   egress; wrong — 41× the burn — when it only needs the tunnel.
2. **The host-only start** — right for a tunnel-only session (Stage 5 pass 4d's case). Two commands,
   as the **infrastructure user** in **Sandbox** (`InfrastructureAccess` — the set that works
   off-VPN, which is what makes this the way back in). The instance id is `[D]` state: it survives
   stop/start but **a roster change replaces the host and the id with it** (§K2/§K4), so it is
   looked up at the moment of use, by the Name-tag contract, and written down nowhere:

   ```bash
   AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 describe-instances --region us-west-2 --filters 'Name=tag:Name,Values=awsds-sandbox-vpn' --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
   ```

   No state filter, on purpose: a `stopped` row is D11 working; **no row at all is a finding** (the
   slice was never applied, or the host is gone). Then, with the id the read printed:

   ```bash
   AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 start-instances --region us-west-2 --instance-ids <INSTANCE_ID>
   ```

   The guarded one-liner, for when the lookup must be programmatic — the guard is the point:
   a `&&`-chain that carries an empty id forward converts "no host" into a confusing downstream
   error (Lesson 25):

   ```bash
   ID=$(AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 describe-instances --region us-west-2 --filters 'Name=tag:Name,Values=awsds-sandbox-vpn' --query 'Reservations[0].Instances[0].InstanceId' --output text); if [ -z "$ID" ] || [ "$ID" = "None" ]; then echo "no VPN host found - a finding, not a retry"; else AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 start-instances --region us-west-2 --instance-ids "$ID"; fi
   ```

   §K0a's other two lookups — `./aws/vpn.py` and `terraform output -raw instance_id` — answer the
   same question with more context around it.

**`InsufficientInstanceCapacity` on start is transient until proven otherwise — retry, change
nothing (measured 2026-08-19).** A stopped instance holds no hardware: every start re-contests
capacity like a fresh launch, and a Graviton nano pinned to one AZ is where the pool runs dry first.
The first-ever start after a `make down` returned exactly this —
`An error occurred (InsufficientInstanceCapacity) … reached max retries: 2` — with the instance left
cleanly `stopped` (nothing to undo), `t4g.nano` confirmed *offered* in the AZ (so not a
configuration problem), and the retry succeeded minutes later. If it persists for ~30 minutes, the
documented fallback is **`t4g.micro` via a deliberate `terraform apply` of the `[D]` slice** — a
known-survivable replacement: the interface key comes from the `[P]` secret and the address from the
`[P]` allocation, so client configs do not move (measured at Stage 4 step 4.2). **Never an AZ
change** — the subnets anchor on `zone_id` in `[P]` `foundation/` — and never a configuration change
on the first transient signal.

**After the start**: `./aws/vpn.py` must read `running` with everything passing; the SSM agent needs
a further minute before a shell works (§K0a's `Online` check); the tunnel itself needs only the
handshake (§C2).

**Down, in this order:**

1. Tunnel down **on each device first** (§C3) — with a full tunnel up, stopping the host strands the
   laptop's default route until `wg-quick down` runs.
2. **`make down ENV=sandbox`** — destroys the `[E]` slices first and stops the host **last**, by
   rank design: the tunnel outlives every API call of the teardown. The direct equivalent, when
   nothing `[E]` is up:

   ```bash
   AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 stop-instances --region us-west-2 --instance-ids <INSTANCE_ID>
   ```

---

## Part C — the client: writing a config, connecting, disconnecting

*Was `vpn-client.md` (written 2026-08-17, from the first handshake — Stage 4 step 5 is the
requirement, step 9.1 the deliverable). The operator is the device's owner, on the device: nothing
in this part calls an AWS API. Bare step numbers in this part are Stage 4's.*

### C0. The values, and where each comes from — five from the design, one from the path

Nothing here is invented, and three of the five are **stable by design** — which is the property
decision 4 bought and step 4.2 proved by rebuilding the host without moving either the address or the
key. **`MTU` is the exception and belongs in a different category**: it is the only line whose correct
value is a property of the network the device happens to be sitting on, so it is derived from nothing in
AWS and is the one line worth re-examining when a working config stops working somewhere new (§C4).

| Line | Value today | Where it comes from |
|---|---|---|
| `PrivateKey` | this device's own | Generated **on the device** and never anywhere else (§K4). Read from its file, never retyped |
| `Address` | `10.90.0.<host>/32` | `cidrhost(peer_cidr, host)` — the device's `host` number in the tracked roster `peers.auto.tfvars`, and `peer_cidr` from the allocation table. `/32`, mirroring the server's `AllowedIPs`: a peer does not reach another peer |
| `DNS` | `10.20.0.2` | `.2` of the VPN home's VPC CIDR (`10.20.0.0/16`) — the VPC resolver, so private hosted zones and interface-endpoint names resolve on the device |
| `PublicKey` | the host's | **`[P]`, in a Secrets Manager secret** — it survives every instance rebuild. Recover it without touching the secret: `host-public.key` on the laptop, this line in any existing config, or `wg show wg0 public-key` on the host |
| `Endpoint` | `52.89.212.1:51820` | The **`[P]` Elastic IP**, allocated in `sandbox/foundation/` a slice away from the host, plus the one port open to the world |
| `MTU` | `1280` | **The path, not the design.** Absent this line `wg-quick` derives it — the MTU of the interface reaching the endpoint, minus 80 — and that derivation is wrong on any path narrower than the local link, phone tethering above all (§C4, measured 2026-08-17). **The server pins the same 1280 since 2026-08-18**, which does *not* make this line optional: the two govern opposite directions, and this one is the only thing bounding what **this device sends** |

**If either of the two key/endpoint lines ever changes without §K3 having been run, that is a
finding, not a reconnection problem.**

### C1. Write the config

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
one nobody diagnoses at 23:00 in an airport (§C4). 1280 is the IPv6 minimum and passes every path
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

### C2. Up, and the three things that prove three different claims

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
This is the one that Stage 4 step 8 depends on: its `aws:SourceIp` matches this address or nothing.

```bash
dig +short SOA sandbox.internal
```

Must answer — **`DNS = 10.20.0.2` is in use**. `sandbox.internal` is the private hosted zone associated
with the VPN home's VPC, so it resolves through the VPC resolver and **NXDOMAIN everywhere else**;
answering is therefore the proof. (Do **not**
pin an `ip-10-20-…compute.internal` name here instead: it encodes the instance's private IP and dies at
every replacement — and a peer change replaces the host.)

### C3. Down

```bash
sudo wg-quick down ~/mbp.conf
```

The config file stays; nothing is revoked, nothing on the server changes. Reconnecting is §C2.

### C4. When it does not work

- **The handshake works, `wg show` counts traffic both ways, DNS answers — and no site loads.** This is
  **MTU**, and it is the failure this runbook exists to stop you from misdiagnosing (measured 2026-08-17,
  on phone tethering, Stage 4 pass 2). **The symptom is graded by packet size**, which is what makes it
  look like something else entirely: the handshake is 148 bytes and succeeds, a DNS query is one small
  UDP exchange and succeeds, and TLS needs a full-MSS certificate chain and times out. WireGuard sets DF
  on its outer packets, so an oversized one is dropped **with no error at either end** — and the natural
  suspicion, a broken NAT on the host, is the expensive wrong turn. **Two answered `dig`s rule the host
  out on their own**: the VPC resolver replies only if the packet was forwarded *and* source-NATed to an
  address inside the VPC, so DNS working means the whole server side is working.
  **The fix is `MTU = 1280` under `[Interface]`** (already in §C1's template — if a config predates it,
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
  over IPv6 would carry an IPv6 source, fail Stage 4 step 8's `NotIpAddress` and read as a lockout *with
  the tunnel up*. Happy Eyeballs falls back to IPv4; a site may pause a moment first.
- **`handshake_age_s` grows without resetting** in the log group `/awsds/sandbox/vpn`. With
  `PersistentKeepalive = 25` the keepalives count as data, so a live tunnel renegotiates about every two
  minutes and the age returns to zero on its own. **An age that only grows means the client stopped
  sending** — the tunnel was taken down (the ordinary case), or the device slept, the network changed,
  or a NAT expired the UDP mapping. The log cannot tell those apart; the device can.
- **`peer=unknown` in that log** is not a client problem at all: it is a peer the roster does not know
  about (§K4).
- **Nothing above settled it, and the suspicion has moved to the server.** That is where this part
  stops by design — the three checks in §C2 exist to rule the device in or out *before* anybody signs in
  to AWS. A shell on the host is an SSM session, opened by the **infrastructure user** and not by the
  device's owner: §K0a, which is also where the `--target` instance id comes
  from. It works with this tunnel down, which is the whole point of it.

### C5. What it costs

**Every byte the device sends anywhere transits the instance** and bills as data transfer out,
~USD 0.09/GB — ordinary browsing included. Connect for lab sessions; this is not an always-on VPN
(Stage 4 step 5.3).

---

## Part K — the server: the shell, the keys, the four procedures

*Was `vpn-keys.md` (written 2026-08-16, from the Stage 4 design review; rewritten the same day at the
third review, when the host key moved into the `[P]` secret `awsds-sandbox-vpn-host-key` — Stage 4
decision 4 names where the keys live). The operator is the infrastructure user,
`awsds-infra-sandbox-1`, plus `awsds-infra-identity` for §K6.*

### K0. Where each half lives

| Half | Designed home | Other copies |
|---|---|---|
| Host **private** | **The `[P]` Secrets Manager secret `awsds-sandbox-vpn-host-key`** (Stage 4 step 2.2a) — value written by the user at enrollment (`put-secret-value`, step 4.3), read by the instance role at first boot; its resource policy denies `GetSecretValue` to everything else in the account except `InfrastructureAccess`, and **every read is a CloudTrail management event** | `/etc/wireguard/wg0.conf` on the host's EBS volume, which `[D]` keeps across stop/start. **Not the user data** — it carries the secret's ARN, so `ec2:DescribeInstanceAttribute` yields a pointer; **not the state** — the state stores the rendered script **in full**, and the script has no key in it: the ARN, and a shell variable that receives the fetched value (measured at the first apply, 2026-08-17 — see the note below); **not the laptop** — the enrollment file is scratch, deleted once the tunnel proves (4.3) |
| Host **public** | `host-public.key` on the laptop, written beside the private half at enrollment (step 4.3) — `644`, not secret, and kept after `host-private.key` is deleted | pinned in every client config's `PublicKey =` line — and recoverable **without touching the secret**: any client config, or `wg show wg0 public-key` over SSM |
| Device **private** | that device, only — it never leaves it (Stage 4 step 4.1) | none, by design |
| Device **public** | `peers.auto.tfvars` — the **tracked** roster, so git history holds every version of it | EC2's stored user data, the host (`wg show`, `/etc/wireguard/peer-names`), and re-derivable on the device from its private half |

Both halves were confirmed at the first apply (2026-08-17, step 1.4) — and **one of them came
back different from what this runbook predicted.** CloudTrail's event history in the VPN home
does show the boot's `GetSecretValue` as a **management** event, principal
`assumed-role/awsds-sandbox-vpn/i-…`, no error: the audit half of decision 4, exercised rather
than assumed (Lesson 20; Stage 4 verification (viii)). But `terraform state pull` shows
`user_data` as **the rendered script in full**, not the 40 hex characters this file used to
promise — provider 6.60.0 stores the plaintext, and the SHA-1 was the pre-5.0 behaviour written
from memory. **The claim that mattered survives the correction and is now the whole of it:
there is no key in that script.** What the state holds is the secret's ARN and the line
`PrivateKey = $HOST_KEY` — a shell variable, expanded on the host at boot, three minutes after
the state was written. Read the mechanism as *the key never crosses Terraform*, never as *the
state is a hash*: the second sentence would also make anything else in a user data look
protected, and nothing is.

### K0a. The shell on the host — an SSM session, and where `--target` comes from

**There is no port 22 anywhere in this design** (Stage 4 step 3), and no bastion and no key pair
either. The AL2023 AMI ships the SSM agent, the instance role carries
`AmazonSSMManagedInstanceCore` and nothing else, and the agent registers itself over its **outbound**
connection — so a shell is opened *through the agent*, never toward it
([`terraform-modules/wireguard/iam.tf`](../../../terraform-modules/wireguard/iam.tf)). Every
`start-session` in this file (§K1's item 2, §K4's stopgap) is this section; so is every "over SSM" in
Part C.

#### The three prerequisites, and the one that is not an AWS grant

| | |
|---|---|
| **The plugin, on the laptop** | `session-manager-plugin` — a **local install**, which is why verification (iii) stayed half-open until Stage 4 step 3's laptop half: the network question was answered days earlier. `brew install --cask session-manager-plugin` (1.2.835.0). Without it the call fails on the laptop with `SessionManagerPlugin is not found`, having reached AWS perfectly well |
| **The identity** | The infrastructure user, profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in `Sandbox`), one `aws sso login --sso-session awsds` behind it. Confirm it *before*, not after a confusing denial: `aws sts get-caller-identity` |
| **A `running` host** | `[D]` means stopped between sessions by design (D11), and a stopped instance is not a target: `TargetNotConnected`. **§S5 is how it is started** — `make up ENV=sandbox` when the session also needs the `[E]` slices, the host-only start when it does not — and note the loop that makes this section matter, [Stage 4](../stages/stage-04-vpn.md) step 8.3: the host that has to be started is the host the tunnel runs on |

**The tunnel does not have to be up, and that is a decision rather than a convenience.**
`InfrastructureAccess` is the one permission set deliberately left *outside* `DenyControlPlaneOffVpn`
(step 8.3, open question 17): the deny would otherwise permit `ec2:StartInstances` only from the
address of the instance that is stopped. This session is therefore the routine way back into a host
whose tunnel is broken — the fire escape, and the institutional shape of that trade is in
[institutional-delta.md](../institutional-delta.md).

#### Finding `--target` — three ways, and why the id is never written down

The instance id is **`[D]` state**. It survives every `make down` / `make up` — those stop and start,
never destroy — but **a peer roster change replaces the host** (§K4), and the replacement carries a new
id. So it is looked up at the moment it is used, and copied into no script, no config and no note; what
*is* stable, and what the tooling pins instead, is the Name tag.

**a. `./aws/vpn.py` — the read-only snapshot. Reach for this one.** No working tree, no Terraform state,
nothing but a session:

```bash
aws sso login --sso-session awsds
```

```bash
./aws/vpn.py awsds-infra-sandbox-1
```

The id is the `INSTANCE` column of section **2. The WireGuard host ([D])** in `aws/output/vpn.txt`, and
the same row answers the third prerequisite in the same glance:

```
INSTANCE              TYPE       STATE     SUBNET        PUBLIC IP     IMDS
i-0…                  t4g.nano   running   subnet-0…     <the EIP>     required
```

That file is untracked and carries account ids: read it, never copy out of it
([`aws/INDEX.md`](../../../aws/INDEX.md) rule 1).

**b. `terraform output` — when the working tree is already open.** The slice publishes the id for
exactly this purpose:

```bash
terraform -chdir=terraform-live/sandbox/vpn output -raw instance_id
```

It reads the **state**, so it needs a slice initialised against its real backend — the
`-backend=false` trap answers with an empty local state rather than with an error
([terraform-changes.md](terraform-changes.md)).

**c. `aws ec2 describe-instances` — the Name-tag contract, direct.** The host is tagged
`awsds-<env>-vpn`, and that tag is a **documented contract** (Stage 4 step 1.1) — it is what
`./aws/vpn.py` itself filters on, rather than any id:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 aws ec2 describe-instances --region us-west-2 --filters 'Name=tag:Name,Values=awsds-*-vpn' 'Name=instance-state-name,Values=running' --query 'Reservations[].Instances[].[InstanceId,State.Name]' --output text
```

**Empty output is two different facts wearing one face**: the host is stopped, or there is no host.
Drop the state filter to tell them apart — a `stopped` row is D11 working, no row at all is a finding.

**Then ask whether the agent is actually connected**, because `running` is necessary and not
sufficient — the agent registers a minute or so after boot, and this is also the one call that fails
usefully when SSM is what is broken:

```bash
AWS_PROFILE=awsds-infra-sandbox-1 aws ssm describe-instance-information --region us-west-2 --query 'InstanceInformationList[].[InstanceId,PingStatus,AgentVersion]' --output text
```

`Online` is the answer. An empty list, or anything else, and `start-session` will return
`TargetNotConnected` however right the id is — at which point the id was never the problem, and
`aws ec2 get-console-output --instance-id <this> --latest` is the read that needs no agent at all.

#### The session

```bash
AWS_PROFILE=awsds-infra-sandbox-1 aws ssm start-session --target i-0… --region us-west-2
```

The shell lands as `ssm-user` with `sudo` available; `exit` or `Ctrl-D` closes it. **`StartSession` is a
CloudTrail event and it names who opened the shell** — this path is audited, which is the other half of
why it replaces port 22 rather than merely standing in for it.

**`wg show wg0`, and never `wg show all dump`.** The dump form prints the interface's **private key** on
its first line. The host's own sampler avoids that form for this reason (Stage 4 step 7), and so does
`./aws/vpn.py --on-host`; in an interactive shell nothing enforces it but the person typing.

The three reads worth knowing, in the order they answer things:

```bash
sudo wg show wg0
```

**Which peers the running interface actually holds** — the roster the kernel is enforcing, read
line by line against the tracked `peers.auto.tfvars`. This is the answer no `describe` call can give
(Stage 4 verification (iii), 2026-08-17), and a peer here that the roster does not have is §K4's `wg set`
stopgap or a hand edit — either way, drift that the handshake log has been calling `peer=unknown`.

```bash
ip -d link show wg0
```

**The server's own MTU** — 8921 on a jumbo-frame VPC when nothing pins it, which is what this read
found; the module has pinned it since `wireguard-v0.2.0`, and the client half is §C4.

```bash
grep -a AWSDS-VPN /var/log/cloud-init-output.log ; cloud-init status
```

**What the boot did** — the first thing to read when the host is up and the tunnel never comes up.

**Against `./aws/vpn.py --on-host`, which runs those same reads: neither is read-only in the API sense.**
`SendCommand` and `StartSession` are both mutating calls and CloudTrail records both. The difference is
what each leaves behind — the flag captures the output into `aws/output/vpn.txt` beside the rest of
Stage 4's evidence, a session leaves the reading in a terminal. Take the session when a person is
asking a question; take the flag when the answer has to be filed.

**And what a session is not: a way to change anything.** Whatever is typed here that alters the host is
state living only inside a `[D]` resource, and it disappears at the next replacement with nobody told
(Lesson 4; Lesson 5 — an intention is not a control). §K4's `wg set` is the one named exception, and it
is named precisely so it stays one.

### K1. Procedure A — recovery: a copy is lost, no compromise suspected

The roster is tracked (a lost working tree comes back with `git clone`) and the key's designed
home is the `[P]` secret, so most losses cost nothing. Find the case, apply its one answer —
none of them is a new key:

1. **The enrollment file on the laptop is gone.** That is the schedule working, not a loss —
   4.3 deletes it once the tunnel proves. Nothing to do.

2. **A new client config needs the host's PUBLIC key.** Take it without touching the secret:
   `host-public.key` on the laptop (§K0), the `PublicKey =` line of any existing client config,
   or — tunnel or no tunnel — `wg show wg0 public-key` in an SSM session (§K0a: the plugin, the
   identity, and where `--target` comes from).

3. **The VALUE itself must be re-read** — rebuilding everything from nothing. Sign in and
   confirm the identity first, then pipe the read straight into `wg pubkey` when the public
   half is all that is wanted, so the private half never lands in a terminal:

   ```bash
   aws sso login --sso-session awsds
   ```

   ```bash
   aws sts get-caller-identity --profile awsds-infra-sandbox-1
   ```

   ```bash
   aws secretsmanager get-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
     --secret-id awsds-sandbox-vpn-host-key --query SecretString --output text | wg pubkey
   ```

   The read is a CloudTrail line naming this session. That is the design working, not an
   incident to explain.

4. **The secret was deleted.** Deletion is scheduled, never immediate —
   `recovery_window_in_days = 30` — so inside the window one call undoes it:

   ```bash
   aws secretsmanager restore-secret --profile awsds-infra-sandbox-1 --region us-west-2 \
     --secret-id awsds-sandbox-vpn-host-key
   ```

   Past the window the value is gone with the name, and this is the **one** loss that forces
   §K3 — which is why deleting this secret is never routine housekeeping.

5. **Everything but the running host is gone** (secret past its window, laptop, repo clone):
   the EBS copy remains. SSM session, `sudo cat /etc/wireguard/wg0.conf`, re-enrol the
   `PrivateKey` value with `put-secret-value` (step 4.3's command, `file://` and all) **before
   anything replaces the instance** — then the designed home is whole again.

### K2. Procedure B — revoke a device (lost, stolen, offboarded)

1. Delete the device's one entry from `peers` in `peers.auto.tfvars` — a tracked file, so the
   revocation is a commit with a date on it. Never renumber the others — `host` is authored per
   peer so a revocation cannot silently invalidate anyone else's config.
2. Plan, and expect **two resources replaced by one cause**: the instance — the peer list rides
   the user data, and `user_data_replace_on_change = true` deliberately makes any peer change
   produce a new host — and its `aws_eip_association`, which follows the instance id. The address
   itself never changes. The replacement host re-fetches the **current** secret value at boot, so
   a §K3 rotation already enrolled but not yet applied lands together with the revocation.
3. Apply. The tunnel drops for the replacement window (minutes). The Elastic IP survives — the
   allocation is `[P]` in `foundation/`, only the association lives here — so the remaining devices
   reconnect **with their configs untouched**.
4. Verify: the handshake log (or `wg show` over SSM) no longer lists the revoked public key;
   `./aws/vpn.py` for the standing checks.
5. **If the device was stolen rather than lost**, WireGuard is the smaller half of the event: the
   same machine likely held SSO sessions — sessions able to read the secret — and this repository.
   Revoke its Identity Center sessions first, and treat §K3 as triggered. **After Stage 4
   step 8.3, read §K6 before applying anything.**

### K3. Procedure C — rotate the host pair (the key, or a session that could read it, is compromised)

1. Generate the new pair on the laptop, as at enrollment — **outside the repository**, `umask 077`
   for a `600` private half at creation, `tr -d '\n'` so the stored value is exactly 44 bytes rather
   than 45, and **no output on screen**: both halves go to disk, so nothing lands in scrollback
   (measured 2026-08-17). Read the new public half from the file at step 5 (`cat host-public.key`):

   ```bash
   (umask 077 && wg genkey | tr -d '\n' > host-private.key) && wg pubkey < host-private.key > host-public.key
   ```

2. Enrol the new value — `file://`, never a pasted literal (§K5):

   ```bash
   aws secretsmanager put-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
     --secret-id awsds-sandbox-vpn-host-key --secret-string file://host-private.key
   ```

   The old value stays readable as `AWSPREVIOUS` until the next put — harmless here: rotation
   is for compromise, and the old key is burnt either way.
3. Delete any compromised device entries from the roster (§K2) in the same window — one
   replacement, not two. **Read §K6 before applying** — after Stage 4 step 8.3 the apply itself
   needs sequencing.
4. **Replace the instance deliberately.** The new value changed nothing Terraform can see — the
   user data carries only the ARN — so the rebuild is explicit:

   ```bash
   terraform apply -replace='module.wireguard.aws_instance.this'
   ```

   (from the slice, as `awsds-infra-sandbox-1`, per
   [terraform-changes.md](terraform-changes.md) Recipe A). The same two-resource replacement as
   §K2 follows — the instance and its association. The Elastic IP does not change, so the
   `DenyControlPlaneOffVpn` fragment in `identity/sso/` needs **no edit** — it pins the address,
   never the key.
5. Update the `PublicKey =` line in **every** device's client config with the new public half —
   read it from `host-public.key` (step 1 put it there and printed nothing) — all of them at once,
   because old configs stop handshaking the moment the new host is up. `Endpoint` and `Address` stay
   as they are. Delete the scratch `host-private.key`; `host-public.key` may stay (§K0).
6. Verify per device: a handshake with the tunnel up; then, if 8.3 has landed, the control-plane
   pair — the same API call denied off-VPN and succeeding on-VPN. The new boot's
   `GetSecretValue` is one more CloudTrail line.

### K4. Procedure D — a device rotates its own key (and how its public half reaches the server)

The mirror of §K3: **one client's half changes and the host's does not.** Reach for it when a device
is reinstalled or reimaged, when its private key is suspected compromised while the host is not, or
when a person simply wants a fresh key. It is also the shape of *adding* a device — steps 1, 2 and 4
are step 4.1 of the stage, with an insertion instead of an edit.

**Two facts decide everything below.** First: the host's public key does not move, so **every other
device's config is untouched**, and the rotating device changes exactly one line of its own —
`Endpoint`, `Address` and the server's `PublicKey =` all stay. Second: **the roster rides the user
data**, so publishing a peer is an instance replacement (§K2's cost, for the same reason) — which is
why anything else pending goes in the same window.

1. **On the device, generate the new pair.** On a laptop, the silent form — outside the repository,
   both halves to disk, nothing in scrollback:

   ```bash
   (umask 077 && wg genkey | tr -d '\n' > laptop-private.key) && wg pubkey < laptop-private.key > laptop-public.key
   ```

   On a phone or tablet, run nothing: the WireGuard app generates the pair inside the device and
   shows the public key on screen. Either way **the private half never leaves the device** — it is
   the one key in this design that has no copy anywhere, by choice.

2. **Publish the public half into the roster** — `peers.auto.tfvars`, the tracked file. Replace that
   entry's `public_key` and **keep its `host` number**: the device keeps its tunnel address, so no
   other config, route or condition anywhere in the estate has anything to notice. Read the value
   with `cat laptop-public.key` (or off the phone's screen) — never retyped.

   ```hcl
   peers = {
     "felipe-laptop" = { public_key = "<the NEW 44-char base64>", host = 2 }
   }
   ```

   `./scripts/check-tfvars-shape.py` holds the file to structure; it cannot tell a private key from a
   public one, and nothing can — that is why the generation stays on the device.

3. **Apply it — this is what "publishing to the server" actually means.** Sign in as the
   **infrastructure user** (`awsds`), account **`Sandbox`**, permission set **`InfrastructureAccess`**
   — profile `awsds-infra-sandbox-1`. **Read §K6 first if step 8.3 has landed.** Then, per
   [terraform-changes.md](terraform-changes.md) Recipe A:

   ```bash
   ./scripts/gen-backend-hcl.py sandbox vpn && ./scripts/gen-tfvars.py sandbox vpn
   ```

   ```bash
   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn init -backend-config=backend.hcl -input=false
   ```

   ```bash
   AWS_PROFILE=awsds-infra-sandbox-1 terraform -chdir=terraform-live/sandbox/vpn plan -out=~/vpn-peer.tfplan
   ```

   **Expect two resources replaced by one cause** — the instance, because the peer list rides its user
   data, and its `aws_eip_association`, which follows the instance id. **The address does not change**
   (the allocation is `[P]`, a slice away). Read the plan, then apply that exact file. The tunnel drops
   for the replacement window — minutes, and **longer if `t4g.nano` capacity is short in the AZ**: the
   first build took 11 minutes across 13 refusals (Stage 4 step 1.4). Budget for that before starting.

4. **On the device, swap one line.** The config's own `PrivateKey =` becomes the new private half —
   from `laptop-private.key`, or regenerated in place by the phone app. Nothing else in the file
   changes. Delete `laptop-private.key` once the tunnel proves, exactly as 4.3 does for the host's.

5. **Verify, and know what "unknown" means.** A handshake from the device with the tunnel up; then
   `wg show wg0` over SSM, or the handshake log group `/awsds/sandbox/vpn`, whose lines carry the
   **device name** because the host renders `/etc/wireguard/peer-names` from the same roster. **A log
   line reading `peer=unknown` is therefore a peer the roster does not know about** — read it as the
   drift alarm it is, not as a cosmetic gap.

#### The stopgap, named as one: `wg set` on the host

There *is* a way to admit a public key in seconds without replacing anything, and it is worth knowing
precisely because it must not be mistaken for step 3. Over SSM (§K0a — the session, and how the
`--target` id is found rather than remembered):

```bash
sudo wg set wg0 peer <NEW_PUBLIC_KEY> allowed-ips 10.90.0.<N>/32 && sudo wg show wg0
```

```bash
sudo wg set wg0 peer <OLD_PUBLIC_KEY> remove
```

**What this changes is the running kernel state and nothing else.** `/etc/wireguard/wg0.conf` is not
touched, so a `wg-quick` restart, a reboot, **or the next `make down` / `make up` cycle** — which stops
and starts this very host — silently drops the peer. The handshake log will call it `peer=unknown` for
as long as it lasts, because `peer-names` does not have it either. Use it to unblock someone mid-session
if you must; **the roster commit and step 3 follow in the same sitting**, or the estate is running a
configuration no file describes (Lesson 5: an intention is not a control; Lesson 4: state living only
inside an `[E]`/`[D]` resource).

### K5. Never

- **Never answer loss with a new key** — the one rule. §K1 costs at most one audited read; an
  unnecessary §K3 costs every device's config in the same minute.
- **Never enable automatic rotation on the secret** — a rotation Lambda would replace the key
  without touching a single client config: the one rule violated by machine, silently, on
  schedule. `./aws/vpn.py` `VP-9` fails the moment `RotationEnabled` reads true.
- **Never pass the key as a `--secret-string` literal** — `file://` keeps it out of the shell
  history; the enrollment file is deleted once the tunnel proves (step 4.3).
- **Never generate the key inside the repository working tree.** `*.key` is git-ignored (the net,
  2026-08-17), but the net is not the practice: pre-commit's `detect-private-key` reads PEM armor
  and a WireGuard key is bare base64, indistinguishable from the public halves this repository
  commits on purpose — so a differently-named file would be caught by nothing.
- **Never hand-edit `/etc/wireguard/wg0.conf` on the host.** It is rendered from the user data,
  so an edit there survives a reboot and dies at the next instance replacement — the worst of the
  two failure modes, because in between it is a running configuration that no file in this
  repository describes and no instrument reads. `wg set` (§K4's stopgap) is the honest version of
  the same impulse: it is obviously temporary, and the handshake log calls its peer `unknown`.
- **Never rebuild the peer map from memory** — read it out of the user data or the host.
  A remembered `host` number that is wrong renumbers someone's tunnel address silently.
- **Never let `wg show all dump` near a log or the chat** — its first line is the interface's
  private key. The host's own sampler uses `latest-handshakes` for exactly this reason.
- **Never put a private key in any tfvars** — the design no longer has a key file at all, and
  `./scripts/check-tfvars-shape.py` still refuses the two regressions it can see: a tracked
  `host-key.auto.tfvars` (the pre-review design coming back) and a `host_private_key` line in
  the roster. A key that was ever pushed is rotated (§K3), never merely deleted.

### K6. Timing against Stage 4 step 8.3 — the lockout seam

- **Before** the separate `InfrastructureAccess` diff of 8.3: applies work from anywhere, tunnel up
  or down. §K2, §K3 and §K4 are routine.
- **After** it, every API call the operator makes must exit through the Elastic IP — and §K2, §K3
  and §K4 all replace the instance (§K3's `-replace` included), which drops the tunnel **mid-apply** and strands
  the remaining provider calls off-VPN. The sequence, in order: **(i)** from on-VPN, apply the small
  `identity/sso/` diff that detaches the `DenyControlPlaneOffVpn` fragment from
  `InfrastructureAccess` only — it does not touch the tunnel; **(ii)** run §K2/§K3/§K4; **(iii)** re-attach
  the fragment. This is the stage's own rollout order, reused: `InfrastructureAccess` is pinned last
  precisely because it is the recovery path. If the order was not followed, the way back is
  [break-glass](break-glass.md) (D16) — rehearsed, per the stage's risks table, before 8.3's
  separate `InfrastructureAccess` diff lands.
- **The single-device corner after 8.3** — the only enrolled device is the one being revoked: you
  are off-VPN by definition and the console-from-the-EIP path needs a device you no longer have, so
  this case reduces to break-glass alone. Enrolling a second device (step 4.1 is per person *per
  device*) is what keeps this corner theoretical.

---

*Stage: [stage-04-vpn.md](../stages/stage-04-vpn.md) · Decision: [D4](../decisions/D04-vpn-wireguard.md) ·
Slice: [`terraform-live/sandbox/vpn/`](../../../terraform-live/sandbox/vpn/README.md) ·
By-hand changes: [terraform-changes.md](terraform-changes.md)*
