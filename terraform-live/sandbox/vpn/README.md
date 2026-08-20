# `sandbox/vpn/` — the WireGuard host

Stage 4 pass 1. **The repository's first `[D]` slice**: `make down` stops what is here and
destroys nothing, `make up` starts it, and `terraform apply` is always a deliberate act
([layers.py](../../../scripts/tfhygiene/layers.py) refusal 5).

Everything the host consumes is `[P]` in [`../foundation/`](../foundation/) — the public
subnet, the internet gateway, the Elastic IP, the security group and the host-key secret of
[step 2](../../../docs/plan/stages/stage-04-vpn.md), and the S3 gateway endpoint whose
allow-list the first boot exercises. So this slice applies with the network torn down.

## The two inputs this slice cannot generate

Both are **keys**, generated on a laptop and never by Terraform — and since the third design
review (2026-08-16) they live in two different places, **neither of them a git-ignored file**.

**`peers.auto.tfvars` — the roster, TRACKED.** Public halves only: who may enter the network,
one named entry per person per device. A map like this benefits from review and history —
adding a device is a reviewable diff, revoking one is a one-line deletion with a date on it.
It is tracked past the wholesale `*.tfvars` ignore with a one-time `git add -f`, and held to
shape by `./scripts/check-tfvars-shape.py`: a WireGuard private key is indistinguishable from
a public one by format, so the gate checks **structure** — this file may assign `peers`, with
`public_key` and `host` per entry, and nothing else.

```hcl
#   public_key  the DEVICE's public half, generated ON the device (step 4.1). On a laptop:
#               (umask 077 && wg genkey | tr -d '\n' > d-private.key) && wg pubkey < d-private.key > d-public.key
#               - silent, both halves to disk, outside this repository. On a phone, the
#               WireGuard app generates the pair itself. The private half never leaves it.
#   host        the device's address inside peer_cidr: 10.90.0.<host>. The server holds .1.
#               AUTHORED, never derived from position - deleting a revoked device must not
#               renumber anybody else's tunnel address.
peers = {
  "felipe-laptop" = { public_key = "<44-char base64>", host = 2 }
  "felipe-phone"  = { public_key = "<44-char base64>", host = 3 }
}
```

**The host's private key — a `[P]` Secrets Manager secret, not a file here.** Generated once
on the laptop, **outside this repository** (step 4.3), and enrolled into
`awsds-sandbox-vpn-host-key` — the container `../foundation/` owns, its value written by the
user and never by Terraform:

```bash
(umask 077 && wg genkey | tr -d '\n' > host-private.key) && wg pubkey < host-private.key > host-public.key
```

```bash
aws secretsmanager put-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
  --secret-id awsds-sandbox-vpn-host-key --secret-string file://host-private.key
```

**The first command prints nothing** — both halves go to disk and neither reaches the terminal,
so the enrollment leaves no key material in scrollback. Read the public half from the file when
a client config needs it (`cat host-public.key`, step 9.1).

Every other detail of it was measured rather than assumed (2026-08-17). `umask 077` inside the
subshell makes `host-private.key` **`600` at creation** rather than after it, while
`host-public.key` — written outside those parentheses, on purpose — lands `644`: the two halves
get the permissions their names promise. **`tr -d '\n'` is what makes the stored value exactly
44 bytes**; the obvious `wg genkey | tee host-private.key` writes 45, the key plus a newline,
which `file://` stores verbatim (the boot's `$(…)` strips it, so this is unambiguity for later
readers rather than a bug avoided). `host-public.key` **keeps** its newline — 45 bytes, `wg
pubkey`'s own output — which is what lets the verification below be a `diff` rather than a
comparison by eye.

`file://`, never a pasted literal — the key must not enter the shell history. `host-private.key`
is scratch — **keep it until the tunnel proves, then delete it**; the secret is the designed
home. `host-public.key` is not secret and may stay. Both are git-ignored by `*.key`, the net
under the practice of generating them outside the repository at all. The instance fetches the
value at first boot with its own role; the secret's resource policy denies the read to every
other principal in the account except `InfrastructureAccess`.

Verify the round trip **mechanically**, without the private half ever reaching a terminal —
`diff` is silent and exits 0 on a match, so the `echo` firing is the whole result:

```bash
aws secretsmanager get-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 --secret-id awsds-sandbox-vpn-host-key --query SecretString --output text | wg pubkey | diff - host-public.key && echo "MATCH - the enrolled value is the key that was generated"
```

**What it costs and buys, named rather than assumed (decision 4, third review).** It costs
USD 0.40/month for the container, a first boot that retries — loudly, with named `say`-lines —
until the same apply's EIP association gives it a route and until the value is enrolled, and a
rotation that is `put-secret-value` **plus a deliberate `terraform apply -replace`** (the value
sits outside the user data, so a new key alone is invisible to Terraform). It buys: a user
data that carries only the ARN, so `ec2:DescribeInstanceAttribute` yields a pointer; a state
that keeps that same script **in full and in plaintext** — measured at the first apply, where
an earlier line here predicted a SHA-1 — **holding no key, only the ARN and the shell variable
that receives the fetched value**; a CloudTrail management event
for **every** read of the value; and exactly two at-rest copies — the secret (the designed
home) and `wg0.conf` on the host's EBS. The alternative, generating the key on first boot,
still fails the old way: it leaves the key living only inside an instance that the
SSM-resolved AMI and `user_data_replace_on_change` both destroy on schedule, breaking every
client config silently (Lesson 4).

**Losing a copy, revoking a device, rotating the host pair:**
[the VPN runbook, Part K](../../../docs/plan/runbooks/vpn.md). Its one rule — loss is answered
by **recovery** (the `[P]` secret holds the key), never by a new key.

## The one input a person changes to alter what is running

[`instance_type.auto.tfvars`](instance_type.auto.tfvars) — **tracked**, two keys, and the only
tfvars here that is edited rather than generated or enrolled. Its **name is narrower than its
contents** since the disk joined it (2026-08-20): renaming would cost the `.gitignore` negation,
`check-tfvars-shape.py`'s constant and every path written about the file, and buy a name.

- **`instance_type` — both directions.** Assign a type to switch the host up; **comment the
  assignment out** to fall back to [`variables.tf`](variables.tf)'s default, `t4g.nano`. The
  admitted values are all `t4g` — the module pins an **arm64** AMI, so `t3.medium` is not an
  alternative to `t4g.medium` and the validation rejects it at plan time.
- **`root_volume_size` — up only.** GiB of gp3 root disk, `8` by default, `8`–`128` admitted.
  EBS **grows** a volume in place and **cannot shrink** one, so commenting this assignment out does
  not return the disk: down is a host **replacement**, not an apply. Two consequences worth knowing
  before assigning: the extra space reaches the filesystem only at **boot** (`growpart`), and the
  volume **bills while the host is stopped**.

Auto-loaded, so every direction that *is* an apply is a plain `terraform apply` with no flag to
forget.

Read before switching either — the pre-flight commands, what the plan must say (`1 to change` counts
the instance, not the attributes), what survives the stop/start, how to confirm the filesystem
actually grew, and the fact that the cost tables and `make status` stay written against `t4g.nano`
on 8 GiB: [the VPN runbook, §S6](../../../docs/plan/runbooks/vpn.md).

## Applying it

```bash
./scripts/gen-backend-hcl.py sandbox vpn && ./scripts/gen-tfvars.py sandbox vpn
```

Then `init`/`plan`/`apply` as `awsds-infra-sandbox-1`, per
[the by-hand runbook](../../../docs/plan/runbooks/terraform-changes.md). **Enrol the secret's
value first** (the command above) — otherwise the boot's fetch waits politely, saying so once
per 10 s, until you do.

**The first boot is Stage 3's verification (iii) running for real, and both of its failure
modes are hangs rather than errors**: the user data installs its packages from the AL2023
repository in S3 through the *gateway* endpoint — no NAT is in the path, the gateway's
prefix-list route being more specific than the internet gateway's — so an incomplete
allow-list shows up as a host that boots and never finishes; and the key fetch loops until the
EIP association lands and the value exists, each retry naming its cause. Read the cloud-init
output before debugging WireGuard.

---

*Slice tree: [`docs/plan/conventions.md`](../../../docs/plan/conventions.md) §6 ·
Deployed tree: [`terraform-live/README.md`](../../README.md)*
