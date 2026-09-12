# `production/buildbox/` — the build host

**Layer `[E]`.** Created for a build session and destroyed at the end of it. It holds nothing:
the state carries no secret, the volume dies with the instance, and anything worth keeping
leaves as an image in ECR.

## Why it exists

The images this estate runs on are **`linux/amd64`** — SageMaker instance types are x86 and the
`sagemaker-distribution` base publishes `-cpu`/`-gpu` tags with no `arm64` variant at all
(measured 2026-08-21 from the public registry's tag list). The laptop this repository is driven
from is `arm64` and has no docker installed. [Stage 6 step 5.0](../../../docs/plan/stages/stage-06a-unified-studio.md)'s
hand build therefore runs on a machine of the right architecture, inside the perimeter, that
exists only while a build is running. The build code itself is [`images/`](../../../images/README.md).

## The network shape

There is one way in, and it is not a network path. The user withdrew the *"reachable only over the
VPN"* requirement on 2026-08-21 rather than let it be delivered in name only.

| | |
|---|---|
| **in** | Nothing. There is no ingress rule at all. No public address, a tier with no internet gateway, and a security group with an empty ingress list. The only way to a shell is **Session Manager**, which needs no inbound rule because the agent holds the channel open *outbound* — measured: the host registers `Online` with the group admitting nothing |
| **out** | As a client of the explicit proxy (D38, 6c step 5.8), with no default route in this tier. Three paths leave this host and reading them apart is what makes a failure diagnosable: the **internet** through `proxy.awsds.internal:3128` over the SharedServices ↔ Networking peering — the `production-foundation` plane, **`open` since 2026-09-08** (D38 §6 amended), so any public name and all of it logged, still under the three global denies; **AWS APIs** through this VPC's interface endpoints, which is why `no_proxy` is *generated* (5.6) and not written; **S3 and DynamoDB** by route, through the `[P]` gateway endpoints — free, and the reason an ECR pull is cheap, since the layers come from S3 |

The host moved here from `sandbox/buildbox/` at [6c step 5.8](../../../docs/plan/stages/stage-06c-networking-hub.md)
(2026-09-06). Its only egress was a default route pointing at the WireGuard host's ENI; D38 removed every
default route in the estate and moved that host into another VPC, and **a route target cannot live in another
VPC**. The move was a destroy-and-create, not a state migration: the host is `[E]` and holds nothing that
survives a session.

Two consequences before the first `up`. `production/egress/` is a **hard prerequisite** — its
`ssm`/`ssmmessages`/`ec2messages` endpoints are the only door into the host, so a build session pays that
slice's 0.130 USD/h where the old shape paid nothing. And the tier is the **private** one: measured
2026-09-06, the peering routes to `VPC-Networking` are in the private route tables and **not** in the
isolated one, so an isolated-tier build host could not reach the proxy at all.

`./scripts/buildbox.py` no longer refuses to apply while `sandbox/probes/` exists. That refusal guarded the
Sandbox *isolated* tier's no-default-route premise, which this slice's mechanism used to break; it creates no
route anywhere now and is not in that account.

The ingress rule that stood here admitted the WireGuard client range on every port, to deliver *"reachable
only with the tunnel up"*. **It did not gate the shell** — `ssm start-session` goes laptop → the *public* SSM
API → the agent's outbound channel, which the group never sees. And it was a grant with no consumer: AL2023
runs `sshd`, so the rule left port 22 *reachable* from the tunnel on a host with zero authorized keys, one
`key_name` away from a second way in.

**What gates the shell is IAM.** For the six persona sets the VPN still does (`DenyControlPlaneOffVpn`
denies `*` on `*` off-VPN); for `InfrastructureAccess` it does not, by **open question 17**, option (a) —
the administrative credential is outside the VPN because it is also the fire escape. A port served during a
build is reached from the laptop with SSM **port forwarding** (`AWS-StartPortForwardingSession`), which is
still Session Manager and still needs no ingress rule.

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
(Lesson 52). It then starts the proxy host if it is stopped (there is no route to fail over to:
every package source and every `RUN` step in a build goes through that one host), applies the
slice, and waits for Session Manager. `sync` puts `images/` at `/opt/awsds/images` — the one
write API in the tooling (`ssm:SendCommand`), fenced the way `./aws/vpn.py --on-host` is.
`down` destroys the host and nothing else; no route was ever created.

**In the session you are `ssm-user`**, not `ec2-user`: Session Manager creates that account on
its first connection, so the first boot cannot add it to the `docker` group. Use `sudo docker …`
or `sudo -iu ec2-user`. The banner on login says the same thing.

**`down` stops neither the proxy nor `egress/`.** This slice owns one `[E]` unit. The proxy is
`[D]` and is the whole estate's single egress, so stopping it because a build finished would cut
off every other account; `make hub-down` is what stops it. `production/egress/` is `[E]` and keeps
billing until `make down ENV=production`.

## What it cannot do

**Push an image.** The role carries `AmazonSSMManagedInstanceCore` and no `ecr:` permission at all.
The push is step 5.0's own act, from an identity that may; Stage 8's pipeline replaces it
(D26/D28: the pipeline is the deployer).

Since the move, that absence is the whole control. `production/registry/` grants the Interactive
accounts a *pull* and nothing more, so a push from Sandbox was refused **at the far end**; this
host is now in the registry's own account, the far-end refusal does not apply to it, and an `ecr:`
action added here would simply work. [`runbooks/buildbox.md`](../../../docs/plan/runbooks/buildbox.md)
§P's token dance is now the only thing between a build host and the registry.

## What it costs

`m8i.xlarge` is **0.2117 USD/h** (`docs/PRICING.md` §8, `us-west-2`) plus ~0.007/h for the 64 GiB
gp3 while it exists. **A week left running is USD 36** against D12's USD 50/month, which is why
every helper the script prints ends in `down`, and why `./scripts/buildbox.py status` exists.

A build session is three bills (6c step 5.8): this host, plus `production/egress/` at
**0.130 USD/h** — its endpoints are the only door in — plus the proxy's `t3.micro` at 0.0104,
which is `[D]` and shared with the whole estate.

**A bigger instance does not fix the network.** Every byte this host pulls from the internet crosses
the proxy, a `t3.micro` — the base image included, whose manifest comes from `public.ecr.aws` and
whose blobs come from the CloudFront distribution its redirect names (measured 2026-09-06). What
does **not** cross it: a private-registry pull's layers, which come from S3 through the `[P]` gateway
endpoint, and the push, which goes to this VPC's `ecr.dkr` interface endpoint — the documented shape,
not yet measured since the move.

**The build is CPU-bound, and that is measured.** On the 02:50-03:15 UTC build of 2026-09-11 the proxy
moved 3.11 GB in its busiest minute — 414 Mbps, 6.5x its own 64 Mbps baseline — at 2.70% CPU with its
credit balance never leaving 288, while this host sat at 99.98% CPU in two consecutive five-minute bins
with its own credits never falling and its surplus balance at zero. EBS write peaked at 75.5 MB/s
against the `t3.xlarge`'s 86.875 baseline. Sizing the proxy up would widen a pipe nothing was waiting
on; the family moved to `m8i` instead, and the knob that matters is this slice's.
