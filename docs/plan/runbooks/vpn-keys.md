# Runbook — The WireGuard keys: loss, revocation, rotation

| | |
|---|---|
| **Scope** | The two kinds of key pair of [`terraform-live/sandbox/vpn/`](../../../terraform-live/sandbox/vpn/README.md) — the host's, and one per enrolled device: where each half lives, and the four procedures: **recovery** (a copy is lost — the `[P]` secret answers), **revocation** (a device), **rotation of the host pair**, and **rotation of one device's own key** — §4, which is also how a public half reaches the server at all, and therefore how a device is *added*. **§0a is the shell every procedure below reaches for**: an SSM session on the host, and how its `--target` id is found |
| **Operator** | The infrastructure user, profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in `Sandbox`) — plus `awsds-infra-identity` for §6's fragment toggles |
| **The one rule** | **Loss is answered by recovery, never by rotation.** A new host key forces an instance replacement and breaks every client config at once — each one pins the server's public key. Rotate for *compromise* (§3), recover for *loss* (§1). The mechanised violation of this rule is Secrets Manager's own rotation feature, which is why it stays off forever (§5, `VP-9`) |
| **Written** | 2026-08-16, from the Stage 4 design review — [Stage 4](../stages/stage-04-vpn.md) decision 4 names where the keys live. **Rewritten the same day at the third design review**: the host key moved into the `[P]` secret `awsds-sandbox-vpn-host-key`, custody by design rather than by side effect — §§0-1 are built around it |

## 0. Where each half lives

| Half | Designed home | Other copies |
|---|---|---|
| Host **private** | **The `[P]` Secrets Manager secret `awsds-sandbox-vpn-host-key`** (Stage 4 step 2.2a) — value written by the user at enrollment (`put-secret-value`, step 4.3), read by the instance role at first boot; its resource policy denies `GetSecretValue` to everything else in the account except `InfrastructureAccess`, and **every read is a CloudTrail management event** | `/etc/wireguard/wg0.conf` on the host's EBS volume, which `[D]` keeps across stop/start. **Not the user data** — it carries the secret's ARN, so `ec2:DescribeInstanceAttribute` yields a pointer; **not the state** — the state stores the rendered script **in full**, and the script has no key in it: the ARN, and a shell variable that receives the fetched value (measured at the first apply, 2026-08-17 — see §0's note); **not the laptop** — the enrollment file is scratch, deleted once the tunnel proves (4.3) |
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

## 0a. The shell on the host — an SSM session, and where `--target` comes from

**There is no port 22 anywhere in this design** (Stage 4 step 3), and no bastion and no key pair
either. The AL2023 AMI ships the SSM agent, the instance role carries
`AmazonSSMManagedInstanceCore` and nothing else, and the agent registers itself over its **outbound**
connection — so a shell is opened *through the agent*, never toward it
([`terraform-modules/wireguard/iam.tf`](../../../terraform-modules/wireguard/iam.tf)). Every
`start-session` in this file (§1's item 2, §4's stopgap) is this section; so is every "over SSM" in
[vpn-client.md](vpn-client.md).

### The three prerequisites, and the one that is not an AWS grant

| | |
|---|---|
| **The plugin, on the laptop** | `session-manager-plugin` — a **local install**, which is why verification (iii) stayed half-open until Stage 4 step 3's laptop half: the network question was answered days earlier. `brew install --cask session-manager-plugin` (1.2.835.0). Without it the call fails on the laptop with `SessionManagerPlugin is not found`, having reached AWS perfectly well |
| **The identity** | The infrastructure user, profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in `Sandbox`), one `aws sso login --sso-session awsds` behind it. Confirm it *before*, not after a confusing denial: `aws sts get-caller-identity` |
| **A `running` host** | `[D]` means stopped between sessions by design (D11), and a stopped instance is not a target: `TargetNotConnected`. `make up ENV=sandbox` starts it (and applies that account's `[E]` slices with it) — and note the loop that makes this section matter, [Stage 4](../stages/stage-04-vpn.md) step 8.3: the host that has to be started is the host the tunnel runs on |

**The tunnel does not have to be up, and that is a decision rather than a convenience.**
`InfrastructureAccess` is the one permission set deliberately left *outside* `DenyControlPlaneOffVpn`
(step 8.3, open question 17): the deny would otherwise permit `ec2:StartInstances` only from the
address of the instance that is stopped. This session is therefore the routine way back into a host
whose tunnel is broken — the fire escape, and the institutional shape of that trade is in
[institutional-delta.md](../institutional-delta.md).

### Finding `--target` — three ways, and why the id is never written down

The instance id is **`[D]` state**. It survives every `make down` / `make up` — those stop and start,
never destroy — but **a peer roster change replaces the host** (§4), and the replacement carries a new
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

### The session

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
(Stage 4 verification (iii), 2026-08-17), and a peer here that the roster does not have is §4's `wg set`
stopgap or a hand edit — either way, drift that the handshake log has been calling `peer=unknown`.

```bash
ip -d link show wg0
```

**The server's own MTU** — 8921 on a jumbo-frame VPC when nothing pins it, which is what this read
found; the module has pinned it since `wireguard-v0.2.0`, and the client half is
[vpn-client.md](vpn-client.md) §4.

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
(Lesson 4; Lesson 5 — an intention is not a control). §4's `wg set` is the one named exception, and it
is named precisely so it stays one.

## 1. Procedure A — recovery: a copy is lost, no compromise suspected

The roster is tracked (a lost working tree comes back with `git clone`) and the key's designed
home is the `[P]` secret, so most losses cost nothing. Find the case, apply its one answer —
none of them is a new key:

1. **The enrollment file on the laptop is gone.** That is the schedule working, not a loss —
   4.3 deletes it once the tunnel proves. Nothing to do.

2. **A new client config needs the host's PUBLIC key.** Take it without touching the secret:
   `host-public.key` on the laptop (§0), the `PublicKey =` line of any existing client config,
   or — tunnel or no tunnel — `wg show wg0 public-key` in an SSM session (§0a: the plugin, the
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
   §3 — which is why deleting this secret is never routine housekeeping.

5. **Everything but the running host is gone** (secret past its window, laptop, repo clone):
   the EBS copy remains. SSM session, `sudo cat /etc/wireguard/wg0.conf`, re-enrol the
   `PrivateKey` value with `put-secret-value` (step 4.3's command, `file://` and all) **before
   anything replaces the instance** — then the designed home is whole again.

## 2. Procedure B — revoke a device (lost, stolen, offboarded)

1. Delete the device's one entry from `peers` in `peers.auto.tfvars` — a tracked file, so the
   revocation is a commit with a date on it. Never renumber the others — `host` is authored per
   peer so a revocation cannot silently invalidate anyone else's config.
2. Plan, and expect **two resources replaced by one cause**: the instance — the peer list rides
   the user data, and `user_data_replace_on_change = true` deliberately makes any peer change
   produce a new host — and its `aws_eip_association`, which follows the instance id. The address
   itself never changes. The replacement host re-fetches the **current** secret value at boot, so
   a §3 rotation already enrolled but not yet applied lands together with the revocation.
3. Apply. The tunnel drops for the replacement window (minutes). The Elastic IP survives — the
   allocation is `[P]` in `foundation/`, only the association lives here — so the remaining devices
   reconnect **with their configs untouched**.
4. Verify: the handshake log (or `wg show` over SSM) no longer lists the revoked public key;
   `./aws/vpn.py` for the standing checks.
5. **If the device was stolen rather than lost**, WireGuard is the smaller half of the event: the
   same machine likely held SSO sessions — sessions able to read the secret — and this repository.
   Revoke its Identity Center sessions first, and treat §3 as triggered. **After Stage 4
   step 8.3, read §6 before applying anything.**

## 3. Procedure C — rotate the host pair (the key, or a session that could read it, is compromised)

1. Generate the new pair on the laptop, as at enrollment — **outside the repository**, `umask 077`
   for a `600` private half at creation, `tr -d '\n'` so the stored value is exactly 44 bytes rather
   than 45, and **no output on screen**: both halves go to disk, so nothing lands in scrollback
   (measured 2026-08-17). Read the new public half from the file at step 5 (`cat host-public.key`):

   ```bash
   (umask 077 && wg genkey | tr -d '\n' > host-private.key) && wg pubkey < host-private.key > host-public.key
   ```

2. Enrol the new value — `file://`, never a pasted literal (§5):

   ```bash
   aws secretsmanager put-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
     --secret-id awsds-sandbox-vpn-host-key --secret-string file://host-private.key
   ```

   The old value stays readable as `AWSPREVIOUS` until the next put — harmless here: rotation
   is for compromise, and the old key is burnt either way.
3. Delete any compromised device entries from the roster (§2) in the same window — one
   replacement, not two. **Read §6 before applying** — after Stage 4 step 8.3 the apply itself
   needs sequencing.
4. **Replace the instance deliberately.** The new value changed nothing Terraform can see — the
   user data carries only the ARN — so the rebuild is explicit:

   ```bash
   terraform apply -replace='module.wireguard.aws_instance.this'
   ```

   (from the slice, as `awsds-infra-sandbox-1`, per
   [terraform-changes.md](terraform-changes.md) Recipe A). The same two-resource replacement as
   §2 follows — the instance and its association. The Elastic IP does not change, so the
   `DenyControlPlaneOffVpn` fragment in `identity/sso/` needs **no edit** — it pins the address,
   never the key.
5. Update the `PublicKey =` line in **every** device's client config with the new public half —
   read it from `host-public.key` (step 1 put it there and printed nothing) — all of them at once,
   because old configs stop handshaking the moment the new host is up. `Endpoint` and `Address` stay
   as they are. Delete the scratch `host-private.key`; `host-public.key` may stay (§0).
6. Verify per device: a handshake with the tunnel up; then, if 8.3 has landed, the control-plane
   pair — the same API call denied off-VPN and succeeding on-VPN. The new boot's
   `GetSecretValue` is one more CloudTrail line.

## 4. Procedure D — a device rotates its own key (and how its public half reaches the server)

The mirror of §3: **one client's half changes and the host's does not.** Reach for it when a device
is reinstalled or reimaged, when its private key is suspected compromised while the host is not, or
when a person simply wants a fresh key. It is also the shape of *adding* a device — steps 1, 2 and 4
are step 4.1 of the stage, with an insertion instead of an edit.

**Two facts decide everything below.** First: the host's public key does not move, so **every other
device's config is untouched**, and the rotating device changes exactly one line of its own —
`Endpoint`, `Address` and the server's `PublicKey =` all stay. Second: **the roster rides the user
data**, so publishing a peer is an instance replacement (§2's cost, for the same reason) — which is
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
   — profile `awsds-infra-sandbox-1`. **Read §6 first if step 8.3 has landed.** Then, per
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

### The stopgap, named as one: `wg set` on the host

There *is* a way to admit a public key in seconds without replacing anything, and it is worth knowing
precisely because it must not be mistaken for step 3. Over SSM (§0a — the session, and how the
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

## 5. Never

- **Never answer loss with a new key** — the one rule. §1 costs at most one audited read; an
  unnecessary §3 costs every device's config in the same minute.
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
  repository describes and no instrument reads. `wg set` (§4's stopgap) is the honest version of
  the same impulse: it is obviously temporary, and the handshake log calls its peer `unknown`.
- **Never rebuild the peer map from memory** — read it out of the user data or the host.
  A remembered `host` number that is wrong renumbers someone's tunnel address silently.
- **Never let `wg show all dump` near a log or the chat** — its first line is the interface's
  private key. The host's own sampler uses `latest-handshakes` for exactly this reason.
- **Never put a private key in any tfvars** — the design no longer has a key file at all, and
  `./scripts/check-tfvars-shape.py` still refuses the two regressions it can see: a tracked
  `host-key.auto.tfvars` (the pre-review design coming back) and a `host_private_key` line in
  the roster. A key that was ever pushed is rotated (§3), never merely deleted.

## 6. Timing against Stage 4 step 8.3 — the lockout seam

- **Before** the separate `InfrastructureAccess` diff of 8.3: applies work from anywhere, tunnel up
  or down. §2, §3 and §4 are routine.
- **After** it, every API call the operator makes must exit through the Elastic IP — and §2, §3
  and §4 all replace the instance (§3's `-replace` included), which drops the tunnel **mid-apply** and strands
  the remaining provider calls off-VPN. The sequence, in order: **(i)** from on-VPN, apply the small
  `identity/sso/` diff that detaches the `DenyControlPlaneOffVpn` fragment from
  `InfrastructureAccess` only — it does not touch the tunnel; **(ii)** run §2/§3/§4; **(iii)** re-attach
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
