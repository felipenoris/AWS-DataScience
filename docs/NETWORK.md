# NETWORK.md — the network topology, as built

| | |
|---|---|
| **What this is** | One picture of every network this project builds: five VPCs and their address plan, every element that holds an internal address, the route tables, **the estate's single internet egress** and the explicit proxy that is it, the VPN, the DNS layer with its association matrix, and the security groups — and the two questions the picture exists to answer: **how a SageMaker app sees the internet**, and **what can reach a SageMaker app** |
| **What it is not** | A procedure. Connecting a device and the session's up/down order: [`plan/runbooks/client-vpn-proxy-configuration.md`](plan/runbooks/client-vpn-proxy-configuration.md); the VPN host itself, building an image, applying a slice: [`plan/runbooks/vpn.md`](plan/runbooks/vpn.md), [`plan/runbooks/buildbox.md`](plan/runbooks/buildbox.md), [`plan/runbooks/terraform-changes.md`](plan/runbooks/terraform-changes.md). The design argument is [`plan/architecture.md`](plan/architecture.md); the build steps are [`plan/stages/stage-03-networking.md`](plan/stages/stage-03-networking.md) and [`plan/stages/stage-04-vpn.md`](plan/stages/stage-04-vpn.md). **Nor is it the authority on whether a reading is *expected*** — that is [`AWS_STATE.md`](AWS_STATE.md)'s invariants and exceptions, and the slice tree is [`plan/conventions.md`](plan/conventions.md)'s |
| **Kept true, and how** | **Reviewed in the same sitting as any change to a network-bearing slice or module** — the rule is `CLAUDE.md`'s upkeep table, and §2.1 below is the list this file must keep naming. **`./scripts/check-network-doc.py` decides the mechanical half**: every allocated CIDR, every per-tier subnet **recomputed from the `vpc` module's own arithmetic**, and every slice that declares a network object or calls a network module has to appear here. Whether a sentence is still *true* is the reading, which no check makes — and the **measured** date in the row above is what a reader compares against `aws/output/` |
| **Where each fact comes from** | Two kinds, marked throughout. **As code** — read from [`../terraform-modules/vpc/`](../terraform-modules/vpc/main.tf), [`../terraform-modules/vpc-egress/`](../terraform-modules/vpc-egress/endpoints.tf), [`../terraform-modules/wireguard/`](../terraform-modules/wireguard/main.tf), [`../terraform-modules/sagemaker-prereqs/`](../terraform-modules/sagemaker-prereqs/blueprints.tf) and the `foundation/`, `egress/`, `vpn/`, `buildbox/`, `probes/` and `sagemaker/` slices under [`../terraform-live/`](../terraform-live/README.md); the address allocation from [`../scripts/tfhygiene/backend.py`](../scripts/tfhygiene/backend.py). **Measured** — read back from the accounts on **2026-09-07** with `./aws/networking.py`, `./aws/proxy.py`, `./aws/vpn.py`, `./aws/dns-allowlist.py` and direct read-only `describe-*` calls, as the infrastructure user. A measured value that is `[E]` or `[D]` describes **that session**, never the design — §13 says which |
| **Written** | 2026-08-23, Claude, at the user's request. **Rewritten 2026-09-07 at [6c](plan/stages/stage-06c-networking-hub.md) step 6.7, from the readings** — the previous body described a three-VPC estate with a NAT gateway per account, and the `§T` block that had been carrying the target *as unbuilt* is now the body. Stable ids (`D38`, `INT-22`, `NT-12`, `Lesson 44`) are the references; section numbers in other files are not |

---

## 0. Four rules for reading this picture

1. **Every fact is marked `[as code]` or `[measured]`.** A `[measured]` value that describes an `[E]`
   or `[D]` object describes **that session**, never the design: endpoint ids, instance ids and
   private addresses are new on every rebuild, and §13 says which session this one was.
2. **Reach is an intersection.** A route, a security group, a proxy allow-list and an endpoint policy
   are four independent gates, in four different slices, and traffic needs all four (Lesson 28). No
   single file answers *"can X reach Y"*, and neither does this one on its own.
3. **What is ABSENT is often the control.** There are five peerings and there could be ten; there is
   no default route in any spoke; `prod.awsds.internal` is not associated with Sandbox. Each absence
   is deliberate and named where it matters.
4. **A network fact is re-measured, never re-imagined.** This file is rewritten from readings taken
   in one sitting, with the instruments named in §14 — not from the plan that asked for them.

---

## 1. The address plan  `[as code]`

The one table is [`scripts/tfhygiene/backend.py`](../scripts/tfhygiene/backend.py)'s `VPC_CIDRS`,
keyed by **(account, slice)** since Stage 6c — a per-account key stopped being expressible the day
Production got three VPCs.

| VPC | CIDR | Account | What it holds |
|---|---|---|---|
| Sandbox 1 | `10.20.0.0/16` | Sandbox | SMUS project apps, the probes |
| **VPC-SharedServices** | `10.30.0.0/16` | Production | GitLab, Pages, the runners, the build host — *the VPC Stage 3 built, re-labelled at 6c step 1.1* |
| **VPC-Networking** | `10.31.0.0/16` | Production | **the estate's only internet gateway route**; the WireGuard host; the Squid proxy |
| **VPC-Workloads** | `10.32.0.0/16` | Production | the production SageMaker runtime, MWAA Serverless workers — *nothing runs in it yet* |
| Staging | `10.50.0.0/16` | Staging | the runtime target — **the CIDR is inherited, not re-cut**: a VPC CIDR is immutable, and the `[P]` gateway-endpoint ids the lake names survive with it |
| WireGuard peers | `10.90.0.0/24` + `fd90::/64` | — | in **no** route table except VPC-Networking's public tier (`NT-4` asserts both halves) |

`10.40.0.0/16` is **released and stays unallocated** — it was Staging's reservation before 6b renamed
an account instead. `10.60.0.0/16` is reserved for the `shared` platform account D38's trigger names.
`10.16.0.0/13` remains the Sandbox supernet, and the rule for the next unit is *the lowest free `/16`*
in it.

**The tiers, recomputed by the `vpc` module from each VPC's `/16`** `[measured, and they match]` —
every VPC has the same six subnets, two AZs × three tiers, anchored on AZ `zone_id`:

| tier | what makes it that tier |
|---|---|
| **private** | the peering routes and the gateway endpoints — **no default route, in any VPC** |
| **isolated** | the gateway endpoints and **nothing else, ever** |
| **public** | a default route to an internet gateway — and only in VPC-Networking does anything sit in it |

Written out, because the arithmetic is the module's and this table is what `check-network-doc.py`
compares it against — **az1 · az2** in each column:

| VPC | private | isolated | public |
|---|---|---|---|
| **Sandbox** | `10.20.0.0/18` · `10.20.64.0/18` | `10.20.128.0/20` · `10.20.144.0/20` | `10.20.160.0/24` · `10.20.161.0/24` |
| **VPC-SharedServices** | `10.30.0.0/18` · `10.30.64.0/18` | `10.30.128.0/20` · `10.30.144.0/20` | `10.30.160.0/24` · `10.30.161.0/24` |
| **VPC-Networking** | `10.31.0.0/18` · `10.31.64.0/18` | `10.31.128.0/20` · `10.31.144.0/20` | `10.31.160.0/24` · `10.31.161.0/24` |
| **VPC-Workloads** | `10.32.0.0/18` · `10.32.64.0/18` | `10.32.128.0/20` · `10.32.144.0/20` | `10.32.160.0/24` · `10.32.161.0/24` |
| **Staging** | `10.50.0.0/18` · `10.50.64.0/18` | `10.50.128.0/20` · `10.50.144.0/20` | `10.50.160.0/24` · `10.50.161.0/24` |

---

## 2. Every element that holds an internal address  `[measured 2026-09-07]`

| Element | Where | Address | Layer · slice |
|---|---|---|---|
| **WireGuard host** `awsds-prod-vpn` | VPC-Networking · public · az1 | `10.31.160.22` (moves with every replacement) + the `[P]` Elastic IP **`52.89.212.1`**; `wg0` at `10.90.0.1/24` **and `fd90::1/64`** | `[D]` `production/vpn/` |
| **Squid proxy** `awsds-prod-proxy` | VPC-Networking · public · az1 | `10.31.160.181` (moves) + the `[P]` Elastic IP **`184.33.8.126`** | `[D]` `production/proxy/` |
| `vpn.awsds.internal` · `proxy.awsds.internal` | the apex zone | the two **private** addresses above | `[D]`, in each host's own slice |
| **Gateway endpoints** S3 + DynamoDB | all five VPCs — no ENI | none: their **ids** are the INT-05 anchors, the only endpoint ids a policy may name | `[P]` each `foundation/`·`networking/`·`workloads/` |
| **Interface endpoints** | private · **az1 only** (D9) | one ENI each, new on every `make up` | `[E]` the four `egress/` slices |
| **SMUS project app ENIs** | Sandbox · private · both AZs offered | one per running app | created by the blueprint, not by this repository |
| **Probe hosts** | Sandbox/Staging/Production, private + isolated | `[E]`, new every session | `[E]` the three `probes/` slices |
| **Build host** `awsds-prod-buildbox` | **VPC-SharedServices · private** · az1 | `[E]` | `[E]` `production/buildbox/` |

**No NAT gateway appears in this table, in any VPC, and that is [D38](plan/decisions/D38-single-egress-hub.md).**

### 2.1 Which slice puts each of those on the network

*The list `./scripts/check-network-doc.py` requires this file to keep naming.*

| Slice | Layer | What it puts on the network |
|---|---|---|
| `sandbox/foundation/` · `staging/foundation/` | `[P]` | one VPC 3×2, its gateway endpoints, its flow log, the per-account child zone |
| `production/foundation/` | `[P]` | **VPC-SharedServices**, the `awsds.internal` **apex** and `awsds-pages.internal`, the cross-account authorisation for the apex, four peering ends |
| `production/networking/` | `[P]` | **VPC-Networking** — the estate's only IGW route — both hub security groups, both Elastic IPs, the proxy's allow-list parameter and access log, the zone associations that make the hub resolve everything |
| `production/workloads/` | `[P]` | **VPC-Workloads** and `prod.awsds.internal` |
| `production/vpn/` | `[D]` | the WireGuard host, `wg0` (both families), the `10.90.0.0/24` return route, `vpn.awsds.internal` |
| `production/proxy/` | `[D]` | the Squid host, its Elastic IP association, `proxy.awsds.internal`, the reconfigure association |
| `sandbox/egress/` · `staging/egress/` · `production/egress/` · `production/workloads-egress/` | `[E]` | interface endpoints; in the two **compute** VPCs, the DNS Firewall |
| `sandbox/probes/` · `staging/probes/` · `production/probes/` | `[E]` | the throwaway hosts that measure what a `describe` cannot |
| `production/buildbox/` | `[E]` | the build host and its egress-only security group — **and no route at all** |
| `sandbox/sagemaker/` | `[P]` | **no network object of its own** — it hands the blueprint the VPC, the private subnets and their zone ids, which is what makes every project app land where §5 describes |

---

## 3. The estate — five VPCs, five peerings, one way in and one way out  `[measured]`

```
                    the internet
                         │
                         │  ONE internet-gateway route in the whole estate
                         ▼
        ┌──────────── VPC-Networking · 10.31.0.0/16 ─────────────┐
        │  public az1:  WireGuard 10.31.160.22   Squid 10.31.160.181
        │               wg0 10.90.0.1/24, fd90::1/64
        │  the ONLY route for 10.90.0.0/24, in this VPC's public table
        └───┬──────────────┬───────────────┬──────────────┬──────┘
   pcx-039c…│      pcx-0409…│      pcx-037f…│      pcx-0145…│
            ▼               ▼               ▼               ▼
      Sandbox          SharedServices    Workloads       Staging
     10.20.0.0/16      10.30.0.0/16     10.32.0.0/16   10.50.0.0/16
            │
            └── pcx-0001…── SharedServices   (INT-09: a notebook clones GitLab)
```

**Five peerings, and the absent ones are the control.** Sandbox↔Staging, Sandbox↔Workloads,
Staging↔SharedServices, Staging↔Workloads and Workloads↔SharedServices do **not** exist. Nothing has to
enforce that isolation — peering is not transitive, so it is free (Lesson 44).

**`NT-11` asserts both sides of every one** `[measured]`: 5 active peerings, routed in both accounts.
A peering routed on one side only is an `active` attachment whose traffic dies in one direction with
no ICMP and no log line — the defect the reference implementation has.

**The peering routes are in the PRIVATE route tables and not the isolated one**, which is why the
build host is in the private tier and why `production/probes`' isolated host is unreachable from a
spoke by construction.

---

## 4. The route tables are the truth  `[measured]`

| Route table | What is in it | What is NOT |
|---|---|---|
| **VPC-Networking · public** | `0.0.0.0/0` → IGW · the two gateway prefix lists · **`10.90.0.0/24` → the WireGuard ENI** | — |
| **every other public tier** | `0.0.0.0/0` → that VPC's IGW · the gateway prefix lists | nothing reaches those IGWs: no host sits in those tiers |
| **every private tier** | the peer VPCs' ranges via peering · the gateway prefix lists | **no `0.0.0.0/0`, in any account.** This is design B, and it is the whole of it |
| **every isolated tier** | the gateway prefix lists, and nothing else, ever | no peering route, no default |

**The single exception in the estate is the `10.90.0.0/24` line**, and it is safe *because it never
leaves one VPC*: it gives Squid a **per-device** source address instead of one blur. `NT-4` asserts it
positively — *the one `10.90.0.0/24` route, inside the hub* — as well as asserting its absence
everywhere else.

---

## 5. How a SageMaker app sees the internet  `[as code + measured]`

Three paths, and reading them apart is what makes a failure diagnosable:

| destination | path | cost |
|---|---|---|
| **AWS APIs with an endpoint** | this VPC's interface endpoints, private DNS on | 0.010/h each + 0.010/GB |
| **S3 and DynamoDB** | the `[P]` **gateway** endpoints, by prefix-list route | **free**, and this is where an ECR pull's layers come from |
| **the internet** | **as a client of the proxy**, by name, over the peering | the proxy's `t3.micro`; **no per-GB processing charge at all** |

**There is no fourth path.** With no default route, a name the app resolves and then tries to reach
directly has nowhere to go — which is why `NO_PROXY` is **generated per VPC** from that VPC's own
endpoint list (`vpc-egress`'s output) rather than written: a blanket suffix would send a service with
no endpoint into a timeout with no message, where the proxy gives a **403 naming the host**.

**Eight of the twenty-nine service names are not derivable from their token** — `ecr.dkr` answers on
`*.dkr.ecr.<region>.amazonaws.com`, `emr-dashboard` on `*.emrappui-prod.…` — so the list is **read**
from `describe-vpc-endpoint-services` at plan time. And **S3 and DynamoDB are hand-named in it**,
because a *gateway* endpoint has no private DNS at all: omit them and every S3 call goes to Squid,
leaves publicly, and arrives carrying neither `aws:SourceVpc` nor `aws:SourceVpce`.

---

## 6. What can reach a SageMaker app  `[as code]`

**Nothing from the internet, by construction**: no public address, no route from a public tier, no
load balancer. From inside the estate, reach needs a peering **and** a security-group rule **and**,
for anything crossing the proxy, a plane on its allow-list. The absent peerings do most of the work.

**And the proxy is not a way around them.** `http_access deny to_private` is the **first** rule in
`squid.conf`, above every allow, so a client that asks the proxy for a private address gets a
**403** — measured from two different source planes. Without that rule the proxy would be an L7
bridge between VPCs the peering matrix deliberately keeps apart.

---

## 7. The tunnel — what a packet from a laptop can and cannot reach  `[measured 2026-09-07]`

**Two client profiles since 2026-09-08 (`objectives.md`; 6c pass 8), and everything measured in this
section is the monitored one's.** Under the **split-tunnel** profile the `.conf` lists the private ranges
instead of `0.0.0.0/0, ::/0`: the *in* and *the masquerade* rows below hold, *out of the host* is never
exercised (no internet-bound packet enters the tunnel), and *the internet* is the laptop's own uplink —
unmonitored, by decision. The cloud side is identical, so a persona's calls still take the proxy under
either profile. **Its readings are owed to 6c steps 8.3 and 8.4** and land here then; nothing below is
edited ahead of them.

| | |
|---|---|
| **in** | UDP/51820 to `52.89.212.1`, the estate's **one** world-open rule |
| **out of the host** | the `FORWARD` chain accepts **RFC1918 only** and REJECTs the rest with `icmp-admin-prohibited`; a second rule REJECTs **all** forwarded IPv6 — **never reached** (measured 2026-09-07): the host has no IPv6 route, so a tunnelled IPv6 packet is answered *no route* before the chain, `Icmp6OutDestUnreachs` 191 against the rule's 0 |
| **the internet** | only through the proxy, by name, on the `tunnel` plane |
| **the masquerade** | everything except traffic bound for the **public tier** — so Squid's log carries `10.90.0.2`, the **device**, not the host |

**The refusal is real and the sender usually cannot see it.** `curl https://1.1.1.1` from a client
read as a **timeout** twice and as `Couldn't connect … after 194 ms` once (2026-09-07): the host
rejects — 27681 packets by 16:54 UTC — but **rate-limits the ICMP it answers with, per destination**,
and a laptop's refused background traffic starves the bucket: 4366 ICMPs sent, **23318 suppressed**
(`OutRateLimitHost`). When one gets through, macOS honours it at once. The evidence lives in the
counters on the refusing side (Lesson 55): the `REJECT` rule and `/proc/net/snmp`'s `Icmp` line, both
in `./aws/vpn.py --on-host`.

**The client's IPv6 enters the tunnel and is rejected there — since 2026-09-07 and not before.**
`AllowedIPs = ::/0` was **inert** without a matching `Address` line, so every IPv6-capable
application was leaving outside the tunnel, the proxy and the access log. The ULA closes that; it is
**not** a control against the device's owner (Lesson 56, `runbooks/vpn.md` §C6).

---

## 8. Endpoints and their policies — the trusted-networks axis  `[as code]`

Every interface endpoint carries the same document: **this organization's principals, and the AWS
services acting as themselves**. `aws:ResourceOrgID` is deliberately absent — through these endpoints
pass calls whose *resource* is AWS-owned (public base images, JumpStart artifacts) — and the resource
axis has its own control where it is load-bearing: the **S3 gateway policy** with its enumerated
bucket allow-list.

**The endpoint ids are `[E]` and anchor nothing.** The ids a policy may name are the `[P]` **gateway**
endpoints', and the condition a policy may carry is `aws:SourceVpc`.

**Every endpoint a VPC pays for must be resolvable in it** — `vpc-egress-v0.8.0` fails the plan
otherwise, naming the endpoint. The case that forced it: `sagemaker.studio` answers on
`*.studio.<region>.sagemaker.aws`, a TLD neither `*.amazonaws.com` nor `*.api.aws` covers.

---

## 9. Security groups — the second gate  `[measured]`

| group | admits |
|---|---|
| `awsds-prod-vpn` `[P]` | UDP/51820 from `0.0.0.0/0` — **the estate's one world-open rule** |
| `awsds-prod-proxy` `[P]` | TCP/3128 from the four spoke CIDRs **and the tunnel range**, and nothing else |
| `awsds-<env>-endpoints` `[P]` | TCP/443 from that VPC's own range |
| `awsds-prod-buildbox` `[E]` | **nothing** — no ingress rule at all; Session Manager needs none |
| the probe groups `[E]` | no ingress; egress scoped to the peers the **peering matrix** generates |

**The dated exception of 2026-09-07 closed on 2026-09-08 (6c step 6.5)**: `awsds-sandbox-vpn` is
destroyed, the estate holds **one** world-open rule again, and `VP-3` reads **every** account's security
groups to say so (Lesson 31).

---

## 10. DNS — who resolves what  `[measured 2026-09-07]`

**Five private zones, and the association matrix is the design** (INT-22). A private zone answers for
its **whole subtree**, and a VPC resolves a zone only by being associated with it — *"you cannot query
the Amazon DNS server in a peer VPC"*.

| Zone | Associated with | Why |
|---|---|---|
| **`awsds.internal`** (apex) | **all five VPCs** | the shared names — `gitlab`, `proxy`, `vpn` — and the `[E]` probe records |
| `sandbox.awsds.internal` | Sandbox, VPC-Networking | per-account names, plus the client plane |
| `staging.awsds.internal` | Staging, VPC-Networking | as above |
| `prod.awsds.internal` | the three Production VPCs | **deliberately not Sandbox or Staging** |
| `awsds-pages.internal` | VPC-SharedServices, VPC-Networking | Pages keeps a sibling apex for the cookie-scope reason D36 gives |

**`NT-12` reads this table against AWS and is two-sided**: 5, 2, 2, 3, 2 associations **and no
others**. An *extra* association is a spoke resolving into a plane the matrix keeps it out of — the
half no expected-direction test would find.

**The client plane resolves at VPC-Networking's `.2`, which carries no interface endpoint with
private DNS — measured from the tunnel on 2026-09-07 (6c step 6.2).** `agent.datazone.us-west-2.api.aws`
answered three **public** addresses; `<domain-id>.studio.us-west-2.sagemaker.aws` a CNAME to
`studio.us-west-2.sagemaker.aws` and three public ones. In a Chrome pointed at the proxy and nothing
else, the portal, a project, its catalog tab and a JupyterLab space opened **with no Local Network
Access prompt** — the two surfaces that demanded the grant on 2026-08-26. That is the structural
repair: a private zone answers for its whole subtree, so a client resolving through a VPC full of
endpoints inherited every one of their names (Lessons 40-43).

**The DNS Firewall's job changed.** It is in the two **compute** VPCs only, its allow-list is ten
entries — AWS's own namespaces and this estate's private zones — and its purpose is no longer
filtering the internet (the proxy does that) but **closing the recursive resolver as an exfiltration
channel**. `VPC-Networking` carries none: the proxy has to resolve.

**The proxy's filters are the estate's egress policy, and they are two KINDS of list:**

| plane | source | mode | entries |
|---|---|---|---|
| `tunnel` | `10.90.0.0/24` | **`open`** — everything permitted, everything logged | 0 (a *deny* list, empty by decision) |
| `sandbox-foundation` | `10.20.0.0/16` | `allowlist` — SageMaker's | 20 |
| `production-foundation` | `10.30.0.0/16` | `allowlist` — the build hosts' | 20 |
| `production-workloads` · `staging-foundation` | `10.32` · `10.50` | `allowlist` | 0 — **refuse everything**, by decision |

**Empty means opposite things in the two modes**, and that is the sentence to carry away. The
objectives ask for the client's internet to be *monitored* and the **compute's** to be restricted.

---

## 11. Observability — where a packet leaves a trace  `[as code]`

| trace | where | what it answers |
|---|---|---|
| **VPC flow logs** | one per VPC, `[P]` | ACCEPT/REJECT per flow — *did the packet arrive* |
| **the proxy's access log** | `/awsds/prod/proxy`, `[P]`, 365 days, CMK-encrypted | **the requested hostname**, per device on the tunnel plane. This is where an unlisted name gets NAMED: `docker pull` says only `Forbidden` |
| **DNS Firewall query log** | `[E]` with its slice | which name was blocked, and by which rule |
| **the handshake log** | `/awsds/prod/vpn`, `[D]` | which peer, how long since its last handshake |
| **CloudTrail** | org-wide | `sourceIPAddress` and `vpcEndpointId` per API call — how the perimeter sees a call |

**The access log has no export to Log Archive yet** — 6c step 4.11's second half is an open decision,
and `PX-4` reports it as a note rather than a failure. Until it lands, the author of the allow-list
also owns its record (Lesson 18).

---

## 12. What is deliberately not there

- **Any NAT gateway.** Priced and unbuilt; the contingency is a named candidate with no instance, and
  its first fallback — *pull the public image through the proxy and push it into ECR* — was measured
  working on 2026-09-06.
- **A Transit Gateway.** Five attachments ≈ USD 182/month standing before a byte, against peering's
  zero per hour. Re-measured 2026-09-06.
- **A Route 53 Resolver endpoint.** Two ENIs ≈ USD 182/month; the free shape is the association matrix.
- **Any interface endpoint in VPC-Networking.** The invariant that keeps the client plane resolving
  publicly.
- **IPv6 anywhere in a VPC.** All five are IPv4-only, measured — which is why the tunnel's ULA rejects
  rather than forwards.
- **`sandbox/probes/`'s isolated-tier default route**, which the build host used to create. The build
  host moved and the route is gone.

---

## 13. The session this was measured in

**2026-09-07**, as the infrastructure user, with `production/vpn` and `production/proxy` **up** and
**every `[E]` slice down**. So: no interface endpoint exists in any account, no probe host, no build
host. Every `[E]` row above is *what the slice builds*, read from the code; every `[P]` and `[D]` row
is read from AWS.

**The one reading the first draft did not carry landed the same day**: step **6.2**, §10 — the two
client-plane names public from the tunnel, and the portal, a catalog tab and a JupyterLab space
opening with no browser grant. **And a reading nobody planned**: a space started while
`sandbox/egress` was **down** came up with a working terminal and JupyterLab stuck at *"IDE
configuration in progress"* — under design B the app's DataZone and SageMaker calls have **no path
at all**, and the symptom is silence, not an error (Lesson 42). With the endpoints up (`getent` →
`10.20.x`, STS answering `302`) and the space restarted, everything worked — §5's *"there is no
fourth path"*, met from inside an app.

---

## 14. The instruments, and when to run each

| instrument | reads | run it when |
|---|---|---|
| `./aws/networking.py` | VPCs, routes, peerings, zones, endpoints — `NT-1`..`NT-12` | any network change, and before believing this file |
| `./aws/proxy.py` | the proxy host, its `[P]` anchors, the ORDER of its rules, running-vs-committed — `PX-1`..`PX-5` | any allow-list or `squid.conf` change |
| `./aws/dns-allowlist.py` | every name on every proxy plane, re-resolved — `DN-1`..`DN-4` | before adding a name, and when one stops working |
| `./aws/vpn.py` | the tunnel host, the EIP, the world-open rule, the deny — `VP-1`..`VP-9` | any VPN question, `--on-host` for what the interface holds |
| `./aws/egress.py` | the interface endpoints as deployed | while an `egress/` slice is up — it is vacuous otherwise |
| `./scripts/check-network-doc.py` | this file against the code | every commit; it decides the mechanical half only |
