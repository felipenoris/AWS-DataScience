# D38 — The single egress hub: where it lives, what reaches it, and where the client plane resolves

**Status:** Decided (2026-09-05, user): a `VPC-Networking` hub inside the `Production` account carries the estate's only internet gateway, an explicit Squid proxy and the WireGuard endpoint; every other VPC has no default route and reaches the internet only by addressing that proxy.

**In one line:** Peering shares an address and never a path, so the "single egress" is an explicit HTTP/HTTPS proxy rather than a shared NAT — and the VPC the VPN client resolves through must hold none of the compute plane's endpoints.

**Related decisions:** [D4](D04-vpn-wireguard.md), [D5](D05-sagemaker-egress.md), [D6](D06-dlp-approach.md), [D9](D09-az-count.md), [D11](D11-lab-lifecycle.md), [D12](D12-budget-ceiling.md), [D14](D14-supply-chain-account.md), [D15](D15-tls-internal.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 6c](../stages/stage-06c-networking-hub.md) (builds it), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 10](../stages/stage-10-orchestration-promotion.md), [Stage 11](../stages/stage-11-dlp.md), [Stage 13](../stages/stage-13-public-web-tier.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

**Closes:** open question 23, in all five of its parts.

---

## Rationale and consequences

### 1. What the mechanism forces

AWS documents that a peered VPC cannot use its neighbour's internet gateway, NAT device or gateway
endpoint, that peering is not transitive, and that a peering route may carry only the peer's CIDR. Four
consequences follow, and none is a preference:

- A **shared NAT gateway does not exist**. What a spoke can reach through a peering is an *address* inside
  the hub — an ENI. So the single egress is an **explicit proxy**, and every client is configured with
  `http_proxy`/`https_proxy`/`no_proxy`.
- A spoke therefore keeps **no default route at all**, D5's design B shape. That closes the two bypasses
  design A could not: a connection to a raw address and a DNS-over-HTTPS query to a public resolver both
  need a route the spoke no longer has.
- Each VPC keeps its **own** S3 and DynamoDB gateway endpoints, and its own interface endpoints. They are
  free (gateway) or per-VPC metered (interface) either way, and centralizing the interface set in the hub
  is ruled out below.
- A sixth limitation from the same page decides §5's other half: **"You cannot connect to or query the
  Amazon DNS server in a peer VPC."** A spoke resolves at its own `.2` and nowhere else, so a private zone
  reaches a spoke only by being **associated with that spoke's VPC**. That is why INT-22's matrix is the
  design rather than a listing, and why a missing association fails as NXDOMAIN rather than as a referral.

**Zero NAT gateways are built.** One would serve only the VPC it sits in, and at USD 0.045/h plus 0.005/h
for its address it is roughly USD 36.50/month standing against a USD 50 ceiling (D12). It stays priced and
unbuilt as the named contingency: if a service needs the internet and cannot be told about a proxy, a NAT
gateway is created **in that service's own VPC**, with a cost row and a removal trigger.

**Amended 2026-09-05, on the documentation:** MWAA Serverless was named here as the first candidate. It is
not one. The MWAA Serverless networking guide documents **two** VPC shapes, and the private one requires the
opposite of a NAT: its subnets *"must not have a route table to a NAT device (gateway or instance), nor an
internet gateway"*, and it is served by interface endpoints for `logs`, `monitoring` and `kms` with a
self-referencing security group. The requirements list that demands two NAT gateways belongs to the
**public-routing** shape on the same page (Lesson 41). Stage 10 builds the private shape.

**Amended again 2026-09-05 (the plan-wide review): the contingency has a candidate, ECR's pull-through
cache.** Amazon ECR documents that the **first** pull through a cache rule *"may require a route to the
internet"*, and its own remedy is a public subnet with an internet gateway and a route from the private tier
— a **route**, which this design removes; an explicit proxy is not one. Unauthenticated upstream pulls are
*"initiated by AWS IP addresses"*, so the requirement is conditional rather than universal.
[Stage 7](../stages/stage-07-gitlab-runners-ecr.md) step 5.2 **measures it**, and ranks two cheaper
fallbacks ahead of a NAT gateway: prime the cache from `VPC-Networking`'s public tier, which has the route;
or drop the cache and bake the two or three public images into `base`. Only a failure of both promotes
`VPC-SharedServices` to this estate's first NAT gateway, with a cost row and a removal trigger. **The
contingency has a named candidate and no instance**, a different state from having neither.

**Amended a third time 2026-09-06, at 6c step 5.9, from a measurement rather than a vendor page.** A third
fallback ranks ahead of the other two, exercised end to end that day on the moved build host: **pull the
public image through the proxy and push it into ECR**, from a host inside the estate. `public.ecr.aws`
serves its token and its manifest through Squid, and the blob download — which **redirects to a CloudFront
distribution**, a name Squid must be told about separately because it matches the hostname the client
*requested* — completed once that distribution was on the build plane. A full
`docker pull public.ecr.aws/docker/library/alpine:3.20` finished, and the layers took the free path:
**S3 through the `[P]` gateway endpoint**, not the proxy.

**Why that outranks priming from the hub's public tier**: it needs no host in `VPC-Networking`, no second
copy of a build environment, and no route. It is the ordinary build path with one name added to one
allow-list. **What it does not do** is make the pull-through *cache* work — that mechanism is AWS fetching
from upstream on the service's own behalf, and no client-side proxy setting reaches it. The ranking is:
(i) pull-and-push through the proxy, **measured working**; (ii) prime the cache from the hub's public tier;
(iii) bake the two or three public images into `base`; and only then a NAT gateway. Stage 7 step 5.2 still
measures whether the cache needs one at all, but the estate no longer *depends* on that answer to obtain a
public image.

### 2. Where the hub lives, and what that costs

The institutional answer is a `Network` account and a `Shared Services` account
(`institutional-delta.md`). The account quota is spent and no slot can be assumed, so both become **VPCs
inside `Production`**, which already holds the supply chain by D14. That is a compromise with a name:

- **A VPC is not an isolation boundary.** The three VPCs share one IAM surface and one blast radius; the
  split catches a routing mistake and never a permission one (Lesson 2).
- The estate's two internet-facing hosts sit in the account that holds the deploy roles and the production
  data path, and GuardDuty is still scheduled at Stage 15 — a widening of exposure recorded here rather
  than absorbed.
- **Revision trigger:** an account slot frees, or the quota is raised → `VPC-Networking` and
  `VPC-SharedServices` migrate to a `shared` platform account. The slices are cut as
  `production/networking/` and `production/foundation/` so that move is a folder migration (Recipe E)
  rather than a rebuild, and `10.60.0.0/16` is reserved for it.

What the split buys back is the largest thing D14 accepted losing: an Interactive account no longer reaches
the runtime VPC, because no peering exists between them.

### 3. Separate hosts for WireGuard and the proxy

The WireGuard host parses untrusted UDP from the internet; the proxy parses untrusted responses from the
internet. They are separate `[D]` instances in the same public tier, with separate security groups and
separate `[P]` Elastic IPs, so a compromise of one is not a compromise of the other. The cost of the second
address is USD 3.65/month.

**The address budget.** Rates are the measured `us-west-2` ones in `PRICING.md`: a public IPv4 address
costs **USD 0.005/h ≈ 3.65/month whether it is in use or idle**, and a NAT gateway costs **0.045/h plus its
own address**, i.e. 0.050/h ≈ **36.50/month** standing.

| | Elastic IPs | NAT gateways |
|---|---|---|
| **Today, in code, with every `egress/` slice up** | **4** — one `[P]` for WireGuard in `sandbox/foundation/`, plus one `[E]` per NAT in `sandbox`, `development` and `production` | **3** — all three `egress/` slices carry `egress_mode = "A"` |
| **Target, after Stage 6c** | **2**, both `[P]`, both in `production/networking/`: the WireGuard host's (**transferred**, not reallocated) and the Squid proxy's (new) | **0** |
| **During the 6c cut-over, at peak** | **3** in Production for one sitting — the proxy's, the transferred one, and Production's own NAT address until pass 5 destroys it. Sandbox goes 1 → 0 | 3 → 0 |
| **Stage 13's public ALB** | **0** — an internet-facing *Application* Load Balancer takes AWS-managed addresses; only a Network Load Balancer can be given Elastic IPs | 0 |
| **Per additional Sandbox (D35)** | **0** — a vended unit peers to the hub and reaches the internet through the same proxy | 0 |

**The estate's steady state is two public addresses and no NAT gateway, and it does not grow with N.**
The default Elastic IP quota is five per Region, which leaves headroom for the cut-over peak and for one
contingency; Stage 12 step 9.1 alarms it. Both addresses are `[P]` **anchors in `networking/`, never in the
`[D]` slice** — a `make down` that released either would invalidate every client `.conf` (the WireGuard one)
or every VPN-only IAM condition (the proxy's).

The **WireGuard host's** Elastic IP is *transferred* from Sandbox rather than reallocated (AWS supports
this within a Region, at no charge, with a seven-day acceptance window; the source account must
**disassociate the address before the recipient accepts**, or the accept fails with
`InvalidTransfer.AddressAssociated`, and the transfer **resets every tag**), so every client keeps its
`Endpoint` line. The **proxy's** address is new, and becomes the anchor of every VPN-only condition.

### 4. The client plane is not special

The VPN client sits inside the private network. Its internet is the private network's internet, so it
crosses the proxy like every other client, and the enforcement lives on the WireGuard host where a user
cannot revert it: tunnel packets are forwarded to RFC1918 destinations only and everything else is dropped.
A laptop with no proxy configured reaches the intranet and nothing else.

Three consequences, easy to get backwards:

- **The anchor moves to the proxy's address.** A laptop's control-plane call exits through Squid, so
  `DenyControlPlaneOffVpn`'s `aws:SourceIp` is the proxy's EIP; `aws:SourceVpc` is `VPC-Networking`; and
  the lake's `aws:SourceVpce` branch gains the hub's S3 gateway endpoint, because S3 from the proxy still
  leaves through it.
- **AWS's own VPC-only policy cannot be copied verbatim here.** The SMUS network-isolation guide's
  `DenyUserAccessFromUnauthorizedVPCs` keys on `StringNotEquals` over `aws:SourceVpc`, which **matches
  whenever the key is absent** — every browser-origin call. Under this design the hub holds no interface
  endpoint, so a portal user's calls carry the proxy's public address and no `aws:SourceVpc` at all, and
  the documented policy would deny the portal outright. INT-16's fallback (i) is therefore authored in
  `policies-shared.tf`'s existing shape: `NotIpAddress` on `aws:SourceIp` **and**
  `StringNotEqualsIfExists` on `aws:SourceVpc`, keeping AWS's `aws:userid` `*:user-*` and
  `aws:ViaAWSService` carve-outs (Stage 6c step 6.6).
- **Per-device attribution is preserved by routing, not by logging.** Inside `VPC-Networking` the proxy's
  subnet carries a route for `10.90.0.0/24` to the WireGuard host's ENI and the host does not masquerade
  traffic bound for the proxy, so the access log records `10.90.0.<device>`. That range appears in no other
  route table, in any account.

### 5. Where the client plane resolves

An interface endpoint with private DNS installs an AWS-managed private zone that is authoritative for the
whole subtree of the service name, and it is visible only from the VPC that owns the endpoint. That is the
mechanism behind Lessons 40-43: a full-tunnel laptop resolving through an Interactive VPC received
**private** addresses for client-plane names, and the SageMaker Unified Studio portal — a public origin —
could only reach them after a browser grant.

The repair is separation, and the hub delivers it as a side effect: the client's `DNS =` points at
`VPC-Networking`'s resolver, and **`VPC-Networking` carries no interface endpoint with private DNS and no
service-name private zone**. Client-plane names then answer publicly while the compute plane keeps its
endpoints. Sandbox may re-add `datazone`, removed on 2026-08-25 for this reason.

This is also why **interface endpoints are never centralized in the hub**, though that is the institutional
pattern: it would put the compute plane's zones back on the client's resolver, and it would make every
spoke's AWS call carry the hub's `aws:SourceVpc`, satisfying the personas' VPN-only condition from any
account. Revisit only when a second business unit makes the endpoint bill dominant (D35).

### 6. What the filters become

`objectives.md` requires two filters: the institutional proxy's, and SageMaker's stricter one on top. Under
an explicit proxy the compute never resolves an internet name — Squid does, in the hub — so a per-VPC DNS
firewall can no longer filter the internet. Both filters therefore live in Squid, as **source-scoped**
allow-lists, one per plane, with a private-destination deny in front of all of them so the proxy cannot
become an L7 bridge between VPCs that peering deliberately keeps apart:

- **The tunnel range is the institutional web filter** (decided 2026-09-05, user). What a person on a
  company laptop may reach is a list on this proxy and nowhere else: no second place enforces a browsing
  decision, and no path from a laptop to the internet avoids it.
- **The Sandbox range is SageMaker's stricter list**, the second filter the objectives name. It is the
  current DNS Firewall allow-list moved verbatim, minus its wildcard and minus the portal families, which
  are the browser's and belong to the tunnel list.

One list per source is what keeps the two filters separate: a name a person may reach is not thereby
reachable from a notebook.

**Amended 2026-09-08 (the user): the build plane is `open`, not an allow-list.** The sentence above says
*"allow-lists, one per plane"*, written from the two planes the objectives name — the client's and
SageMaker's. `production-foundation` is neither. It is `VPC-SharedServices`: the buildbox today, the
GitLab runners from Stage 7 — the tooling that **builds** the restricted environment rather than a surface
the restriction is about. Its control is the **review of the build definition**, which is in git and
promoted as an artifact, not a list of hostnames; and the list it carried was a treadmill whose own comment
called its next revision *"a WHEN rather than an IF"* — `d5l0dvt14r5h8.cloudfront.net`, read out of the
access log after a `docker pull` failed on a redirect nobody could have predicted. A control that must be
widened in a hurry by whoever is blocked, guarding a host whose real control is elsewhere, is not buying
what it costs. So that plane is `open`: **everything permitted, everything logged**, the shape the client
plane has. `proxy_allow_shared` is deleted and `d5l0dvt14r5h8.cloudfront.net` with it.

**What the amendment does not change**, and why "open" here is not "unbounded":

- **The three global denies still sit above this plane** — private destinations (so the proxy cannot become
  an L7 bridge into the estate), unsafe ports, and `CONNECT` to anything but 443.
- **There is still no default route in SharedServices**, and the security group admits that source to 3128
  and nothing else. The proxy is the only door; what changed is which public names fit through it.
- **`sandbox-foundation` stays an allow-list.** This is the first time the source-scoped split earns its
  keep in the *permissive* direction: a name a build host may fetch is not thereby reachable from a
  notebook. That property is why the planes are per-source.

**What it does change, and is easy to miss: a plane is a CIDR, not a host.** `10.30.0.0/16` is the whole
VPC, so anything that lands in SharedServices inherits the open internet, including something put there for
an unrelated reason (Lesson 29). That is the intent for CI/CD tooling and is *not* a general permission: a
host that should not have the open internet does not belong in SharedServices.

**A control moved from the network to code review rather than disappearing.** An image built with
unrestricted egress can bake in anything, and what stops it is the Dockerfile being read before it is
promoted. An institution would likely keep both; the delta is
[`institutional-delta.md`](../institutional-delta.md)'s to record.

The DNS firewall survives in every compute VPC with a different job: an allow-list of AWS and intranet
names plus the blocking rule, which closes the recursive resolver as an exfiltration channel, the classic
residual of a VPC with no NAT. `VPC-Networking` carries none, because the proxy has to resolve.

The proxy terminates CONNECT without decrypting, so it sees the requested hostname (which survives
Encrypted Client Hello, unlike SNI inspection) and the byte counts, never the content. Domain fronting
through an allowed CDN host stays an accepted residual, recorded in Stage 11's threat model.

### 6b. The peerings that are absent

`VPC-SharedServices` is not peered to Staging or to `VPC-Workloads`, though the category name suggests
otherwise. **Deployment is an API act**: the runner assumes a role across the account boundary and calls
SageMaker, CloudFormation and S3, while artifacts travel as ECR images, CodeArtifact packages and S3
objects, each reached through an endpoint in the target's own VPC. Nothing in a deployment target clones a
repository, because the image carries the code (D28); a runtime `git clone` there is a contract violation to
catch, not a path to provide.

Keeping them absent costs one later change, generated from the same peering map as the rest. Building them
costs standing L3 reach from the host that executes repository-supplied build code into both deployment
targets — the blast radius D14 accepted, widened.

**The trigger:** a peering to a deployment target is added when a shared service is consumed **at runtime**
rather than at deploy time. Candidates, none of which exists today: a package mirror or registry proxy on an
instance, a metrics or log collector that is not CloudWatch, an internal secrets or configuration service, a
certificate-status endpoint. The internal CA is not one — D36 issues no CRL and runs no OCSP responder. When
one appears, prefer a regional service or an endpoint to a peering.

### 6c. Where each VPC's endpoints live

An endpoint slice reads exactly one `foundation/` — its VPC id, its subnets, its route tables. Production
has three VPCs, so the `[E]` endpoint layer is **`production/egress/` for `VPC-SharedServices` and
`production/workloads-egress/` for `VPC-Workloads`**, with **none at all** for `VPC-Networking` (§5). Two
consequences, both nearly missed in the first draft:

- **`terraform-modules/vpc-egress` carries account-unique names too**, not just `vpc`: its DNS-firewall
  CloudWatch log group `/awsds/<env>/dns-firewall` collides outright, and its rule group, its two domain
  lists and its query-log config collide by `Name`. It takes the same `name_suffix`, in the same version
  bump that removes the NAT half.
- **There are three NAT gateways to destroy, not two.** `production/egress/` is `egress_mode = "A"` today,
  so `VPC-SharedServices` has one as well. **Measured 2026-09-07: none was destroyed** — every `egress/`
  slice was `[E]` and down when 6c step 5.1 removed the code, so the count was zero all along; the
  sentence above is a prediction kept as the record of what was believed.

### 7. What this does not decide

The proxy's allow-list contents (Stage 6c writes the first version, Stage 11 owns the policy); TLS
interception (rejected today: it would add a fourth trust surface and a CA in every image — D36's trigger);
and whether a second business unit changes the topology (D35's question, answered at Stage 14 with N in
hand).

---

## Revision trigger

- An account slot frees or the quota is raised → move `VPC-Networking` and `VPC-SharedServices` to a
  `shared` platform account (§2).
- A service is found that needs the internet and cannot use a proxy → a NAT gateway **in that service's
  VPC**, priced and dated (§1). **The first candidate is ECR's pull-through cache**, measured at Stage 7
  step 5.2 with two cheaper fallbacks ranked ahead of it.
- The endpoint bill becomes the dominant line at N > 1 Sandboxes → re-open centralization, against §5's
  constraint (§5).
- The proxy's access log stops being sufficient evidence for Stage 11's egress leg → TLS interception is
  re-argued against D36's fourth-surface trigger (§6).

---

*Decisions index: [INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
