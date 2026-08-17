# Runbook — The WireGuard keys: loss, revocation, rotation

| | |
|---|---|
| **Scope** | The two kinds of key pair of [`terraform-live/sandbox/vpn/`](../../../terraform-live/sandbox/vpn/README.md) — the host's, and one per enrolled device: where each half lives, and the three procedures: **recovery** (a copy is lost — the `[P]` secret answers), **revocation** (a device), **rotation** (the host pair) |
| **Operator** | The infrastructure user, profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in `Sandbox`) — plus `awsds-infra-identity` for §5's fragment toggles |
| **The one rule** | **Loss is answered by recovery, never by rotation.** A new host key forces an instance replacement and breaks every client config at once — each one pins the server's public key. Rotate for *compromise* (§3), recover for *loss* (§1). The mechanised violation of this rule is Secrets Manager's own rotation feature, which is why it stays off forever (§4, `VP-9`) |
| **Written** | 2026-08-16, from the Stage 4 design review — [Stage 4](../stages/stage-04-vpn.md) decision 4 names where the keys live. **Rewritten the same day at the third design review**: the host key moved into the `[P]` secret `awsds-sandbox-vpn-host-key`, custody by design rather than by side effect — §§0-1 are built around it |

## 0. Where each half lives

| Half | Designed home | Other copies |
|---|---|---|
| Host **private** | **The `[P]` Secrets Manager secret `awsds-sandbox-vpn-host-key`** (Stage 4 step 2.2a) — value written by the user at enrollment (`put-secret-value`, step 4.3), read by the instance role at first boot; its resource policy denies `GetSecretValue` to everything else in the account except `InfrastructureAccess`, and **every read is a CloudTrail management event** | `/etc/wireguard/wg0.conf` on the host's EBS volume, which `[D]` keeps across stop/start. **Not the user data** — it carries the secret's ARN, so `ec2:DescribeInstanceAttribute` yields a pointer; **not the state** — the provider stores a SHA-1 of a script that contains no key; **not the laptop** — the enrollment file is scratch, deleted once the tunnel proves (4.3) |
| Host **public** | `host-public.key` on the laptop, written beside the private half at enrollment (step 4.3) — `644`, not secret, and kept after `host-private.key` is deleted | pinned in every client config's `PublicKey =` line — and recoverable **without touching the secret**: any client config, or `wg show wg0 public-key` over SSM |
| Device **private** | that device, only — it never leaves it (Stage 4 step 4.1) | none, by design |
| Device **public** | `peers.auto.tfvars` — the **tracked** roster, so git history holds every version of it | EC2's stored user data, the host (`wg show`, `/etc/wireguard/peer-names`), and re-derivable on the device from its private half |

Two shapes worth one confirmation each at the first apply: `terraform state pull` shows the
instance's `user_data` as 40 hex characters — the provider's SHA-1 of a script that carries the
ARN and no key — and CloudTrail's event history in the VPN home shows the boot's
`GetSecretValue` as a management event: the audit half of decision 4, exercised rather than
assumed (Lesson 20; Stage 4 verification (viii)).

## 1. Procedure A — recovery: a copy is lost, no compromise suspected

The roster is tracked (a lost working tree comes back with `git clone`) and the key's designed
home is the `[P]` secret, so most losses cost nothing. Find the case, apply its one answer —
none of them is a new key:

1. **The enrollment file on the laptop is gone.** That is the schedule working, not a loss —
   4.3 deletes it once the tunnel proves. Nothing to do.

2. **A new client config needs the host's PUBLIC key.** Take it without touching the secret:
   `host-public.key` on the laptop (§0), the `PublicKey =` line of any existing client config,
   or — tunnel or no tunnel — `wg show wg0 public-key` in an SSM session
   (`aws ssm start-session --target <instance-id> --profile awsds-infra-sandbox-1 --region us-west-2`;
   the laptop side needs the `session-manager-plugin`, which is not in the standard toolset).

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
   step 8.3, read §5 before applying anything.**

## 3. Procedure C — rotate the host pair (the key, or a session that could read it, is compromised)

1. Generate the new pair on the laptop, as at enrollment — **outside the repository**, `umask 077`
   for a `600` file at creation, and `tr -d '\n'` so the stored value is exactly 44 characters
   rather than 45 (measured 2026-08-17; the filename is scratch — any name serves):

   ```bash
   (umask 077 && wg genkey | tr -d '\n' > host-private.key) && wg pubkey < host-private.key | tee host-public.key
   ```

2. Enrol the new value — `file://`, never a pasted literal (§4):

   ```bash
   aws secretsmanager put-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
     --secret-id awsds-sandbox-vpn-host-key --secret-string file://host-private.key
   ```

   The old value stays readable as `AWSPREVIOUS` until the next put — harmless here: rotation
   is for compromise, and the old key is burnt either way.
3. Delete any compromised device entries from the roster (§2) in the same window — one
   replacement, not two. **Read §5 before applying** — after Stage 4 step 8.3 the apply itself
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
   all of them at once, because old configs stop handshaking the moment the new host is up.
   `Endpoint` and `Address` stay as they are. Delete the scratch `host-private.key`.
6. Verify per device: a handshake with the tunnel up; then, if 8.3 has landed, the control-plane
   pair — the same API call denied off-VPN and succeeding on-VPN. The new boot's
   `GetSecretValue` is one more CloudTrail line.

## 4. Never

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
- **Never rebuild the peer map from memory** — read it out of the user data or the host.
  A remembered `host` number that is wrong renumbers someone's tunnel address silently.
- **Never let `wg show all dump` near a log or the chat** — its first line is the interface's
  private key. The host's own sampler uses `latest-handshakes` for exactly this reason.
- **Never put a private key in any tfvars** — the design no longer has a key file at all, and
  `./scripts/check-tfvars-shape.py` still refuses the two regressions it can see: a tracked
  `host-key.auto.tfvars` (the pre-review design coming back) and a `host_private_key` line in
  the roster. A key that was ever pushed is rotated (§3), never merely deleted.

## 5. Timing against Stage 4 step 8.3 — the lockout seam

- **Before** the separate `InfrastructureAccess` diff of 8.3: applies work from anywhere, tunnel up
  or down. §2 and §3 are routine.
- **After** it, every API call the operator makes must exit through the Elastic IP — and §2/§3
  replace the instance (§3's `-replace` included), which drops the tunnel **mid-apply** and strands
  the remaining provider calls off-VPN. The sequence, in order: **(i)** from on-VPN, apply the small
  `identity/sso/` diff that detaches the `DenyControlPlaneOffVpn` fragment from
  `InfrastructureAccess` only — it does not touch the tunnel; **(ii)** run §2/§3; **(iii)** re-attach
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
