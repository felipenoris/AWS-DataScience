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
#   public_key  the DEVICE's public half: `wg genkey | tee private.key | wg pubkey`,
#               run on the device (step 4.1). The private half never leaves it.
#   host        the device's address inside peer_cidr: 10.90.0.<host>. The server holds .1.
#               AUTHORED, never derived from position - deleting a revoked device must not
#               renumber anybody else's tunnel address.
peers = {
  "felipe-laptop" = { public_key = "<44-char base64>", host = 2 }
  "felipe-phone"  = { public_key = "<44-char base64>", host = 3 }
}
```

**The host's private key — a `[P]` Secrets Manager secret, not a file here.** Generated once
on the laptop (step 4.3) and enrolled into `awsds-sandbox-vpn-host-key` — the container
`../foundation/` owns, its value written by the user and never by Terraform:

```bash
wg genkey | tee host-private.key | wg pubkey
```

```bash
aws secretsmanager put-secret-value --profile awsds-infra-sandbox-1 --region us-west-2 \
  --secret-id awsds-sandbox-vpn-host-key --secret-string file://host-private.key
```

`file://`, never a pasted literal — the key must not enter the shell history. The **public**
half (the second line of the first command) goes into every client config (step 9.1); the
local `host-private.key` is scratch — delete it once the tunnel proves. The instance fetches
the value at first boot with its own role; the secret's resource policy denies the read to
every other principal in the account except `InfrastructureAccess`.

**What it costs and buys, named rather than assumed (decision 4, third review).** It costs
USD 0.40/month for the container, a first boot that retries — loudly, with named `say`-lines —
until the same apply's EIP association gives it a route and until the value is enrolled, and a
rotation that is `put-secret-value` **plus a deliberate `terraform apply -replace`** (the value
sits outside the user data, so a new key alone is invisible to Terraform). It buys: a user
data that carries only the ARN, so `ec2:DescribeInstanceAttribute` yields a pointer; a state
that keeps the provider's SHA-1 of a script with no key in it; a CloudTrail management event
for **every** read of the value; and exactly two at-rest copies — the secret (the designed
home) and `wg0.conf` on the host's EBS. The alternative, generating the key on first boot,
still fails the old way: it leaves the key living only inside an instance that the
SSM-resolved AMI and `user_data_replace_on_change` both destroy on schedule, breaking every
client config silently (Lesson 4).

**Losing a copy, revoking a device, rotating the host pair:**
[the keys runbook](../../../docs/plan/runbooks/vpn-keys.md). Its one rule — loss is answered
by **recovery** (the `[P]` secret holds the key), never by a new key.

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
