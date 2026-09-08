# `production/buildbox/` — the build host

**Layer `[E]`.** Created for a build session and destroyed at the end of it. It holds nothing:
the state carries no secret, the volume dies with the instance, and anything worth keeping
leaves as an image in ECR or does not leave at all.

## Why it exists

The images this estate runs on are **`linux/amd64`** — SageMaker instance types are x86 and the
`sagemaker-distribution` base publishes `-cpu`/`-gpu` tags with **no `arm64` variant at all**
(measured 2026-08-21 from the public registry's tag list). The laptop this repository is driven
from is `arm64` and has no docker installed. So [Stage 6 step 5.0](../../../docs/plan/stages/stage-06a-unified-studio.md)'s
hand build moves to a machine of the right architecture, inside the perimeter, that exists only
while a build is running. The build code itself is [`images/`](../../../images/README.md).

## The network shape, which is the whole design

**One way in, and it is not a network path** — the shape since 2026-08-21, when the user withdrew the
*"reachable only over the VPN"* requirement rather than let it be delivered in name only.

| | |
|---|---|
| **in** | **Nothing. There is no ingress rule at all.** No public address, a tier with no internet gateway, and a security group with an empty ingress list. The only way to a shell is **Session Manager**, which needs no inbound rule because the agent holds the channel open *outbound* — measured: the host registers `Online` with the group admitting nothing |
| **out** | **As a client of the explicit proxy** (D38, 6c step 5.8), and there is **no default route in this tier at all**. Three paths leave this host and reading them apart is what makes a failure diagnosable: the **internet** through `proxy.awsds.internal:3128` over the SharedServices ↔ Networking peering — the `production-foundation` plane, **`open` since 2026-09-08** (D38 §6 amended), so any public name and all of it logged, still under the three global denies; **AWS APIs** through this VPC's interface endpoints, which is why `no_proxy` is *generated* (5.6) and not written; **S3 and DynamoDB** by route, through the `[P]` gateway endpoints — free, and the reason an ECR pull is cheap, since the layers come from S3 |

**It moved here from `sandbox/buildbox/` at [6c step 5.8](../../../docs/plan/stages/stage-06c-networking-hub.md)
(2026-09-06), and the move was forced rather than tidy.** Its only egress was a default route pointing at the
WireGuard host's ENI. D38 removed every default route in the estate and moved that host into another VPC — and
**a route target cannot live in another VPC**, so the old shape was not deprecated, it was unbuildable. This was
a destroy-and-create, not a state migration: the host is `[E]` and holds nothing that survives a session.

**Two consequences worth knowing before the first `up`.** `production/egress/` is now a **hard prerequisite** —
its `ssm`/`ssmmessages`/`ec2messages` endpoints are the *only* door into the host, so a build session pays that
slice's 0.130 USD/h where the old shape paid nothing. And the **tier is the private one**: measured 2026-09-06,
the peering routes to `VPC-Networking` are in the private route tables and **not** in the isolated one, so an
isolated-tier build host could not reach the proxy at all. The isolated tier was the old home only because
design A's default route belonged to `egress/` and two slices cannot write one route table; nothing writes a
default route now, so that reason evaporated with the design.

**And the `sandbox/probes/` exclusion is gone.** `./scripts/buildbox.py` used to refuse to apply while the
perimeter probe existed, because that probe's premise is that the Sandbox *isolated* tier has no default route
and this slice's mechanism was adding one there. It creates no route anywhere now and is not in that account.
The refusal is **deleted rather than retargeted** — a guard that no longer guards anything is the one a later
reader trusts by mistake.

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

`up` **refuses while `production/egress/` is down** — the `ssmmessages` endpoint is read before
the apply, because without it the apply *succeeds*, the host runs, and `start-session` reports it
as not connected, which is indistinguishable from a slow boot for as long as anyone waits
(Lesson 52). It then **starts the proxy host if it is stopped** (there is no route to fail over
to: every package source and every `RUN` step in a build goes through that one host), applies the
slice, and waits for Session Manager. `sync` puts `images/` at `/opt/awsds/images` — **the one
write API in the tooling** (`ssm:SendCommand`), fenced the way `./aws/vpn.py --on-host` is.
`down` destroys the host and **nothing else**; no route was ever created.

**In the session you are `ssm-user`**, not `ec2-user`: Session Manager creates that account on
its first connection, so the first boot cannot add it to the `docker` group. Use `sudo docker …`
or `sudo -iu ec2-user`. The banner on login says the same thing.

**`down` stops neither the proxy nor `egress/`.** This slice owns one `[E]` unit. The proxy is
`[D]` and is the **whole estate's** single egress — stopping it because a build finished would cut
off every other account; `make hub-down` is what stops it. `production/egress/` is `[E]` and keeps
billing until `make down ENV=production`, which is the cost the move added and the one to remember.

## What it deliberately cannot do

**Push an image.** The role carries `AmazonSSMManagedInstanceCore` and no `ecr:` permission at all.
The push is step 5.0's own act, from an identity that may; Stage 8's pipeline replaces it
(D26/D28: the pipeline is the deployer).

**And the move took half of that control away, which is worth stating rather than discovering.**
The old reasoning had two legs: this role names no `ecr:` action, **and** `production/registry/`
grants the Interactive accounts a *pull* and nothing more, so a push from Sandbox was refused **at
the far end** regardless of what the near end said. This host is now **in the registry's own
account**. The far-end refusal does not apply to it, so the absence of an `ecr:` action here is no
longer a belt beside a brace — **it is the whole control**, and one added in a hurry would simply
work. [`runbooks/buildbox.md`](../../../docs/plan/runbooks/buildbox.md) §P's token dance is
unchanged and is now the only thing between a build host and the registry.

## What it costs, measured

`t3.xlarge` is **0.1664 USD/h** (`docs/PRICING.md` §8, `us-west-2`) plus ~0.007/h for the 64 GiB
gp3 while it exists. **A week left running is USD 28** against D12's USD 50/month — which is why
every helper the script prints ends in `down`, and why `./scripts/buildbox.py status` exists.

**A build session is now three bills, not one** (6c step 5.8): this host, plus
`production/egress/` at **0.130 USD/h** — its endpoints are the only door in — plus the proxy's
`t3.micro` at 0.0104, which is `[D]` and shared with the whole estate.

**One thing a bigger instance does not fix:** every byte this host pulls from the internet crosses
the **proxy**, a `t3.micro` — the base image included, whose manifest comes from `public.ecr.aws` and
whose blobs come from the CloudFront distribution its redirect names (measured 2026-09-06). If a build
is network-bound rather than CPU-bound, the knob is that host's instance type, not this slice's. What
does **not** cross it: a private-registry pull's layers, which come from S3 through the `[P]` gateway
endpoint, and the push, which goes to this VPC's `ecr.dkr` interface endpoint — the documented shape,
not yet measured since the move.
