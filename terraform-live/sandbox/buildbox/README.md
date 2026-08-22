# `sandbox/buildbox/` — the build host

**Layer `[E]`.** Created for a build session and destroyed at the end of it. It holds nothing:
the state carries no secret, the volume dies with the instance, and anything worth keeping
leaves as an image in ECR or does not leave at all.

## Why it exists

The images this estate runs on are **`linux/amd64`** — SageMaker instance types are x86 and the
`sagemaker-distribution` base publishes `-cpu`/`-gpu` tags with **no `arm64` variant at all**
(measured 2026-08-21 from the public registry's tag list). The laptop this repository is driven
from is `arm64` and has no docker installed. So [Stage 6 step 5.0](../../../docs/plan/stages/stage-06-unified-studio.md)'s
hand build moves to a machine of the right architecture, inside the perimeter, that exists only
while a build is running. The build code itself is [`images/`](../../../images/README.md).

## The network shape, which is the whole design

**One way in, and it is not a network path** — the shape since 2026-08-21, when the user withdrew the
*"reachable only over the VPN"* requirement rather than let it be delivered in name only.

| | |
|---|---|
| **in** | **Nothing. There is no ingress rule at all.** No public address, a tier with no internet gateway, and a security group with an empty ingress list. The only way to a shell is **Session Manager**, which needs no inbound rule because the agent holds the channel open *outbound* — measured: the host registers `Online` with the group admitting nothing |
| **out** | **Through the WireGuard host**, the single public egress of this design — unchanged, and the requirement that stayed. **Three things in three slices, all three needed** (Lesson 28): the **route** here, the **masquerade rules** in `sandbox/vpn/`, and the WireGuard **security group** in `sandbox/foundation/` admitting them inbound. **No NAT gateway is involved** — `egress/` need never come up, which is 0.170 USD/h not spent |

**Why the ingress rule went, and it is worth one paragraph because it looked like a control.** It admitted
the WireGuard client range on every port, to deliver *"reachable only with the tunnel up"*. Two things were
wrong with it. **It did not gate the shell** — `ssm start-session` goes laptop → the *public* SSM API → the
agent's outbound channel, and the group never sees it, so the claim was false for the one path anybody
uses. **And it was a grant with no consumer**: AL2023 runs `sshd`, so the rule left port 22 *reachable*
from the tunnel on a host with zero authorized keys — one `key_name` away from a second way in that
nothing here asked for. A rule nobody uses is not neutral; it is what a later convenience grows out of.

**What gates the shell is IAM.** For the six persona sets the VPN still does (`DenyControlPlaneOffVpn`
denies `*` on `*` off-VPN); for `InfrastructureAccess` it does not, by **open question 17**, option (a) —
the administrative credential is outside the VPN because it is also the fire escape. **If a port served
during a build ever has to be reached from the laptop:** SSM **port forwarding**
(`AWS-StartPortForwardingSession`), which is still Session Manager and still needs no ingress rule.

**It is the isolated tier, and that is a choice with a co-tenant.** The private tier's default
route belongs to `egress/` under `egress_mode=A`, and two slices writing `0.0.0.0/0` into one
route table is a collision rather than a design. The isolated tier has no default route by
construction — which is the property that leaves room for one, **and** the premise
`sandbox/probes/`'s perimeter probe measures. The two are never up together, and that is
enforced by [`scripts/buildbox.py`](../../../scripts/buildbox.py) rather than asked for in a comment.

## Using it

```bash
./scripts/buildbox.py up
```

```bash
./scripts/buildbox.py sync
```

```bash
./scripts/buildbox.py ssm
```

```bash
./scripts/buildbox.py down
```

`up` refuses to run while a probe instance exists, **starts the WireGuard host if it is
stopped** (a stopped route target is a blackhole, not an error — every symptom then looks like a
broken package mirror), applies the slice, and waits for the host to register with Session
Manager. `sync` puts `images/` at `/opt/awsds/images` — **the one write API in the tooling**
(`ssm:SendCommand`), fenced the way `./aws/vpn.py --on-host` is. `down` destroys the host **and
the route**, so the isolated tier goes back to having no default route.

**In the session you are `ssm-user`**, not `ec2-user`: Session Manager creates that account on
its first connection, so the first boot cannot add it to the `docker` group. Use `sudo docker …`
or `sudo -iu ec2-user`. The banner on login says the same thing.

**`down` does not stop the WireGuard host.** This slice owns one `[E]` unit; the tunnel is `[D]`
and shared with everything else in the account. `make down ENV=sandbox` is what stops it.

## What it deliberately cannot do

**Push an image.** The role carries `AmazonSSMManagedInstanceCore` and no `ecr:` permission at
all. The Production registry grants the two Interactive accounts a **pull** and nothing more
(`terraform-live/production/registry/ecr.tf`: *nothing outside this account publishes*), so a
push from Sandbox is refused at the far end anyway — and granting the near half of a permission
the far half denies would produce a role that reads as if it could publish. The push is step
5.0's own act, from an identity that may; Stage 8's pipeline replaces it.

## What it costs, measured

`t3.xlarge` is **0.1664 USD/h** (`docs/PRICING.md` §8, `us-west-2`) plus ~0.007/h for the 64 GiB
gp3 while it exists. **A week left running is USD 28** against D12's USD 50/month — which is why
every helper the script prints ends in `down`, and why `./scripts/buildbox.py status` exists.

**One thing a bigger instance does not fix:** every byte this host pulls crosses the WireGuard
host, a `t3.nano` by default. If a build is network-bound rather than CPU-bound, the knob is
`sandbox/vpn/instance_type.auto.tfvars` (`docs/plan/runbooks/vpn.md` §S6), not this slice's.
