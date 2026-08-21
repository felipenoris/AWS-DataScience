# Runbook — the devbox

The `amd64` build host of [Stage 6 step 5.0](../stages/stage-06-unified-studio.md), in the Sandbox
account. Slice: [`terraform-live/sandbox/devbox/`](../../../terraform-live/sandbox/devbox/README.md).
Layer **`[E]`** — created for a build session, destroyed at the end of it.

## D. What it is

One EC2 instance (`t3.xlarge`, 64 GiB gp3, both selectable in the tracked
`instance_type.auto.tfvars` beside the slice), with docker and git installed at first boot, plus the
one route that gives it a way out. It holds nothing worth keeping: the volume dies with the
instance, the state carries no secret, and anything that must survive leaves as an image in ECR.

## M. Why it exists

**The images this estate runs on are `linux/amd64` and the laptop is `arm64`.** SageMaker instance
types are x86 and `sagemaker-distribution` publishes `-cpu`/`-gpu` tags with **no `arm64` variant at
all** (measured 2026-08-21 from the public registry's tag list); the laptop also has no docker. So
[`images/`](../../../images/README.md) — `base` and `dev-env` — is built here rather than there, on a
machine of the right architecture, inside the perimeter, that exists only while a build runs.

It is a **builder, not a workstation**. It cannot push: its role carries Session Manager and no
`ecr:` permission at all, because the Production registry grants the Interactive accounts a *pull*
and nothing more. The push is step 5.0's own act, from an identity that may.

## C. The components, and how they connect

| Piece | Where | What it does |
|---|---|---|
| the instance | isolated tier, no public IP | the build host itself |
| its security group | the slice, `[E]` | **egress only — no ingress rule at all.** Session Manager needs none |
| **the route** | `0.0.0.0/0` in the **isolated** route table, `[E]` | sends this tier's default at the WireGuard host's **ENI** |
| `vpc_nat_cidrs` | `sandbox/vpn/`, module `wireguard-v0.4.0`, `[D]` | makes that host a **NAT instance** for this tier: source/dest check off, MASQUERADE + FORWARD in `wg0`'s `PostUp` |
| the WireGuard **security group** | `sandbox/foundation/vpn-anchors.tf`, `[P]` | admits the isolated tier's ranges **inbound**. Without it the other three do their jobs and the packet is dropped on arrival |

**Those last three are one path in three slices, and that is what made the gap easy to miss.** Reach is
an **intersection** (Lesson 28): the first apply had the route and the masquerade and no security-group
rule, so the host booted, installed its packages through the S3 gateway endpoint, and then timed out on
`ssm.<region>.amazonaws.com`. Nothing in any single file was wrong.

**In: nothing.** There is no ingress rule at all — the *"reachable only over the VPN"* requirement was
**withdrawn by the user on 2026-08-21** rather than delivered in name only: the rule that used to be here
did not gate the shell (`ssm start-session` reaches the agent's *outbound* channel and no security group
sees it) and it left port 22 reachable on a host with no authorized keys. **What gates the shell is IAM** —
for the six persona sets the VPN still does; for `InfrastructureAccess` it does not, by open question 17,
option (a). A port served during a build is reached with SSM **port forwarding**, not with an ingress rule.

**Out:** through the WireGuard host, the single public egress of this design. **No NAT gateway is
involved**, so `egress/` need never be up for a build — 0.170 USD/h not spent.

**Three couplings worth holding in mind:**

- **Three lifetimes, one path.** The security group is `[P]` (a private range, admitting a tier that is
  empty between sessions), the masquerade rules are `[D]` with the host, and only the **route** is `[E]`.
  So the reach is the one thing that comes and goes.
- **The capability is `[D]`, the reach is `[E]`.** A masquerade rule matches nothing until a route
  table sends traffic at it. Turning `vpc_nat_cidrs` on is one standing attribute; everything
  metered comes and goes with the session. (`vpn.md` §S carries the rest, including why the rules
  ride `PostUp` rather than the user data.)
- **A stopped WireGuard host makes the route a blackhole**, not an error — every symptom then looks
  like a broken package mirror. `up` starts it; `down` does **not** stop it (it is `[D]` and shared).
- **It must not coexist with `sandbox/probes/`.** That slice's perimeter probe measures the isolated
  tier's *absence* of a default route; this one adds one. `devbox.py` refuses rather than warns.

## U. Up

```bash
./scripts/devbox.py up && ./scripts/devbox.py sync && ./scripts/devbox.py ssm
```

`up` refuses if a probe instance exists, starts the WireGuard host if it is stopped, applies the
slice, and waits for Session Manager. `sync` puts `images/` at `/opt/awsds/images` — the one write
API in the tooling (`ssm:SendCommand`), fenced the way `./aws/vpn.py --on-host` is. `ssm` opens the
shell.

**In the session you are `ssm-user`, not `ec2-user`** — Session Manager creates that account on its
first connection, so the first boot cannot add it to the `docker` group. Use `sudo docker …` or
`sudo -iu ec2-user`. Then:

```bash
cd /opt/awsds/images && sudo docker build -t awsds/base:local base && sudo docker build -t awsds/dev-env:local dev-env
```

**If it never registers with SSM**, the route is failing nine times out of ten. Read the first boot
without SSM: `aws ec2 get-console-output --instance-id <id> --latest`, and `/var/log/awsds-devbox-boot.log`
once you are in — its egress check prints the public address the host leaves under, which must be the
WireGuard Elastic IP.

## X. Down

```bash
./scripts/devbox.py down
```

Destroys the host **and the route**, so the isolated tier goes back to having no default route. It
deliberately leaves the WireGuard host running — `make down ENV=sandbox` is what stops that.

**`./scripts/devbox.py status` is the reading**, and the reason to take it: `t3.xlarge` is
**0.1664 USD/h** (`PRICING.md` §8) — a week left up is USD 28 against D12's USD 50/month.

## Setting up github conectivity

```
ssh-keygen -t ed25519 -C "<EMAIL>"
eval "$(ssh-agent -s)"
cat ~/.ssh/id_ed25519.pub
```

- go to <https://github.com/settings/keys> and add new ssh key. paste pulic key.

- Clone with git protocol:

```
git clone git@github.com:felipenoris/AWS-DataScience
```
