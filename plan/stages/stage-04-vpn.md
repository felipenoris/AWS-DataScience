# Stage 4 — VPN access

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stage 3. D4 is decided: self-managed WireGuard. |
| **Consumes** | [D4](../decisions/D04-vpn-wireguard.md), [D6](../decisions/D06-dlp-approach.md), [D16](../decisions/D16-break-glass.md), [D26](../decisions/D26-unified-studio.md), [D35](../decisions/D35-sandbox-cardinality.md) |
| **Proves** | [INT-16](../integrations.md) |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

**Forward constraint from D35 — read this before writing "the Sandbox account" anywhere below.** `Sandbox` is
one account **per business unit**, and **the VPN lives on exactly that multiplied side**: the tunnel's landing
account, the client resolver target, the routes and the Sandbox↔Production peering that reaches GitLab all
become per-unit as N grows. (Development is singular, so its own peering is fixed and is not part of the
problem.) **The topology is not decided here and should not be** — a designated hub account, a Transit Gateway
in a shared network account, or per-unit VPN endpoints are all live, and the choice depends on N and on
whether units may reach each other at all ([Stage 14](stage-14-sandbox-vending.md) carries it as its central
open question). What this stage owes Stage 14 is only this: **name the VPN home as a role an account plays,
not as "the Sandbox account"** — one variable, so that changing the topology later is a substitution instead
of a rewrite.

---

**Objective:** the only human path into the private network.

**Prerequisites:** Stage 3. D4 is decided: self-managed WireGuard.

**To execute:**

1. `terraform-modules/wireguard/`: `t4g.nano` (ARM, Amazon Linux 2023) in a public subnet, WireGuard
   installed and configured by user data, IP forwarding and NAT (masquerade) enabled. **NAT is not
   optional** — a correction to the previous version, which mixed a NAT model with a routed one: VPC
   peering does no edge-to-edge routing and only forwards packets whose source and destination sit inside
   the two VPCs' CIDRs, so the WireGuard client range can never cross the peering to Production. Every
   packet the instance forwards must carry its own private IP, which also means security groups admit the
   WireGuard instance's SG (referencing a peer VPC's security group works across a same-region peering),
   never the client CIDR.
   Layer `[D]`: the instance is **stopped** between sessions, not destroyed (~USD 0.65/month of EBS),
   which keeps the host key and the peer configuration stable.
2. Elastic IP allocated in the `[P]` foundation slice and re-associated on start, so the endpoint address
   survives a teardown and client configs never have to be regenerated. ~USD 3.65/month — the price of not
   editing every client config on every rebuild.
3. Security group allowing only UDP/51820 inbound; SSH access only through SSM Session Manager, never
   port 22 from the internet.
4. Peer public keys supplied through a git-ignored `.tfvars` (keys are generated on the client and the
   private key never leaves the laptop). One peer per person and per device.
   **The peer network gets its own CIDR, chosen here and written down: `10.90.0.0/24`.** It has to avoid all
   four VPC ranges (`10.20`, `10.30`, `10.40`, `10.50`) *and* be unlikely to collide with a home or café LAN,
   which is why it is not `10.0.0.0/24` or anything in `192.168.0.0/16`. With NAT on the instance (step 1)
   nothing inside AWS ever sees this range, so its only job is to not collide with the laptop's own network
   — a collision there produces a tunnel that comes up and routes nothing, diagnosed by nobody at 23:00.
   Record it in `plan/architecture.md` §4.1's spirit: a variable with this default, not a literal scattered through the module.
5. **Full tunnel, not split** — a correction to the previous version, forced by step 8: the client routes
   `0.0.0.0/0` through WireGuard, so AWS API and console traffic exits through the instance's Elastic IP
   and the `aws:SourceIp` condition can match it. A split tunnel routing only the two VPC CIDRs would
   leave every API call on the laptop's own connection — and step 8 would then deny the user everything,
   tunnel up or not. The cost of full tunnel is that ordinary browsing also transits the instance and
   bills as EC2 data transfer out (~USD 0.09/GB): connect for lab sessions, not as an always-on VPN.
   Reaching GitLab in Production still works through the Stage 3 peering (NATed by step 1). `DNS` in the
   client config points at the VPC resolver (`.2` of the Sandbox VPC CIDR) so private hosted zones and
   VPC endpoints resolve.
6. No return routes for the WireGuard peer network exist anywhere — with NAT on the instance (step 1) the
   VPCs only ever see the instance's private IP, and across the peering such a route would be dropped
   anyway (edge-to-edge, again). What is actually needed: Production's route back to the **Sandbox VPC
   CIDR** through the peering (already built in Stage 3), and security groups on GitLab, EFS and the
   endpoints that admit the WireGuard instance's SG or IP.
7. CloudWatch agent shipping the WireGuard handshake log; alarm if the instance is unhealthy.
8. **Close the other half of the objective: restrict the AWS control plane to the VPN.** `CLAUDE.md` says
   "all user access to the cloud infrastructure will be performed through a VPN", and a tunnel to the VPC
   only delivers the data plane — the console and the AWS APIs remain reachable from any network in the
   world with a valid SSO session. Add a deny with `NotIpAddress` on the WireGuard Elastic IP **combined
   with `aws:ViaAWSService: false`** to the permission sets in `terraform-live/identity/sso/` — the second
   condition is not optional: services calling on the user's behalf (Athena reaching S3 is this plan's
   first casualty) do not carry the user's source IP, and a bare `aws:SourceIp` deny breaks them.
   **Which API to pin this to changed with D26, and the old answer is still written in several places.**
   The classic Studio path was `sagemaker:CreatePresignedDomainUrl`; there are no classic domains any more,
   so keep the deny on it as a belt-and-braces measure (it costs nothing and the `Workloads` OU SCP denies
   the same action anyway) but understand that it now protects nothing that exists. The surface that
   actually matters is the **Unified Studio portal**, which is reached by signing in to Identity Center and
   opening the domain URL — not by minting a presigned URL with an IAM call. **Whether a permission-set
   `aws:SourceIp` deny covers that sign-in at all is unverified and is INT-16.** Until that row is
   settled, this step delivers VPN-only access to the AWS APIs and the console, and *not* demonstrably to
   the portal — which is the data scientist's primary working surface. Do not write it up as though it
   does. This restriction is what step 5's full tunnel exists for.
   Two cautions, both of which have locked people out before: apply it to the `DataScientistAccess`,
   `DeploymentManagerAccess` and `GovernanceManagerAccess` permission sets first and to `InfrastructureAccess` only once it demonstrably works, and note
   that this pins access to a single Elastic IP — which is precisely why that IP lives in `[P]` (D4).
   Break-glass (D16) is the way out if this goes wrong.
9. Write the client setup instructions in `README.md`, including how to regenerate the config after a
   rebuild.
10. **Enable GuardDuty org-wide, from the Audit account** (delegated in Stage 1b step 8). It lands in this
   stage and not in the landing zone because **this stage builds the first internet-facing resource in the
   project**: an EC2 instance with a public Elastic IP and an open UDP port. Until now there was nothing
   exposed and nothing to detect; from here there is, and the thing GuardDuty is best at is exactly this
   host's failure mode — an instance's role credentials being used from outside AWS, outbound traffic to a
   known-bad destination, crypto-mining patterns.
   It needs no configuration: GuardDuty reads CloudTrail management events, VPC Flow Logs and DNS query
   logs on its own, without you enabling any of them. Route findings to the Audit account and an SNS topic.
   **Leave S3 Protection and Malware Protection off** — they are billed separately and are decided in
   Stage 11 step 4 against a real bill.
   **One thing this step should settle while GuardDuty is being wired, because it is free here and costly
   later:** `awsds-org-scp-baseline` denies `guardduty:UpdateDetector` on the organization root, Audit
   included, so anything that changes **Audit's own detector** is denied — org-wide administration through
   `UpdateOrganizationConfiguration`/`UpdateMemberDetectors` is not. Enabling the base service does not need
   the denied call, so nothing blocks here; Stage 11 step 4 does. **If this stage ends up creating a named
   GuardDuty administration role in Audit, record its exact ARN** — that is the carve-out Stage 11 would
   otherwise have to improvise, and a carve-out written against a role that already exists is the one shape
   this plan trusts (D27).
   **Cost:** free for the first 30 days per account, then driven by log volume (`plan/cost-model.md`).
   Note what that free window is *not*: it starts when the service is enabled, in every account at once, so
   it is a discount on this stage and the next, not a measurement instrument to be spent deliberately.

**Deliverables:** connecting from the laptop gives private access to a test resource in the Sandbox
**and Production** VPCs — the only two the tunnel reaches at the VPC level. The laptop has **no route into
the Development or Staging VPCs, by design**, and that is not a gap: both are used entirely through AWS
API endpoints, which the full tunnel already sends out through the WireGuard Elastic IP (`plan/architecture.md` §3, "How a human
actually reaches each account"). For Development specifically, that means the work is done through the
**Unified Studio portal** (D26) — a public endpoint, reached from the tunnel's IP, and `VpcOnly` does not
change that because it governs how the *app containers* reach the network, not how the browser reaches the
UI. The laptop needs no route into the Development VPC either way.

So the deliverables are:
- the Sandbox and Production test resources are reachable with the tunnel up and unreachable with it down;
- an AWS API call with the tunnel down is denied for the data scientist **and the same call with the tunnel
  up succeeds** — the pair that proves the full-tunnel/`aws:SourceIp` wiring;
- `make down` followed by `make up` restores connectivity without changing the client configuration;
- **and, as a recorded result rather than an assumed one: does the portal itself open with the tunnel down?**
  This is INT-16 and it is answered here, at the first moment it can be. If the portal opens without
  the tunnel, "all user access through a VPN" is not yet true for the surface the data scientist actually
  uses, and the fallback in that row applies. Write down which of the two happened.

An earlier version of this deliverable said "Studio in Development opens with the tunnel up and refuses to
open with it down", via `CreatePresignedDomainUrl`. D26 removed the classic domains that sentence described.

**Known trade-off (D4):** no Identity Center integration — revoking a person's access means removing their
peer and re-applying. Acceptable for a single-operator lab, and the reason AWS Client VPN stays documented
as the alternative.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
