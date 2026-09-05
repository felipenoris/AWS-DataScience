# D38 — The single egress hub: where it lives, what reaches it, and where the client plane resolves

**Status:** Decided (2026-09-05, user): **a `VPC-Networking` hub inside the `Production` account carries the estate's only internet gateway, an explicit Squid proxy and the WireGuard endpoint; every other VPC has no default route and reaches the internet only by addressing that proxy**

**In one line:** Peering shares an address and never a path, so the "single egress" is an explicit HTTP/HTTPS proxy rather than a shared NAT — and the VPC the VPN client resolves through must hold none of the compute plane's endpoints.

**Related decisions:** [D4](D04-vpn-wireguard.md), [D5](D05-sagemaker-egress.md), [D6](D06-dlp-approach.md), [D9](D09-az-count.md), [D11](D11-lab-lifecycle.md), [D12](D12-budget-ceiling.md), [D14](D14-supply-chain-account.md), [D15](D15-tls-internal.md), [D35](D35-sandbox-cardinality.md)

**Referenced by stages:** [Stage 6c](../stages/stage-06c-networking-hub.md) (builds it), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 10](../stages/stage-10-orchestration-promotion.md), [Stage 11](../stages/stage-11-dlp.md), [Stage 13](../stages/stage-13-public-web-tier.md), [Stage 14](../stages/stage-14-sandbox-vending.md)

**Closes:** open question 23, in all five of its parts.

---

## Rationale and consequences

### 1. What the mechanism forces, before anything is chosen

AWS documents that a peered VPC cannot use its neighbour's internet gateway, NAT device or gateway
endpoint, that peering is not transitive, and that a peering route may carry only the peer's CIDR. Three
consequences follow and none of them is a preference:

- A **shared NAT gateway does not exist**. What a spoke can reach through a peering is an *address* inside
  the hub — an ENI. So the single egress is an **explicit proxy**, and every client is configured with
  `http_proxy`/`https_proxy`/`no_proxy`.
- A spoke therefore keeps **no default route at all**, which is D5's design B shape. This is what closes
  the two bypasses design A could not: a connection to a raw address and a DNS-over-HTTPS query to a public
  resolver both need a route the spoke no longer has.
- Each VPC keeps its **own** S3 and DynamoDB gateway endpoints, and its own interface endpoints. They are
  free (gateway) or per-VPC metered (interface) either way, and centralizing the interface set in the hub
  is ruled out below.

**Zero NAT gateways are built.** One would serve only the VPC it sits in, and at USD 0.045/h plus 0.005/h
for its address it is roughly USD 36.50/month standing against a USD 50 ceiling (D12). It stays priced and
unbuilt as the named contingency: if a service needs the internet and cannot be told about a proxy, a NAT
gateway is created **in that service's own VPC**, with a cost row and a removal trigger. The first
candidate is MWAA Serverless, whose workers expose no proxy setting — Stage 10 gives them private routing
with interface endpoints first.

### 2. Where the hub lives, and what that costs

The institutional answer is a `Network` account and a `Shared Services` account
(`institutional-delta.md`). The account quota is spent and no slot can be assumed, so both become **VPCs
inside `Production`**, which already holds the supply chain by D14. That is a compromise with a name:

- **A VPC is not an isolation boundary.** The three VPCs share one IAM surface and one blast radius; the
  split catches a routing mistake and never a permission one (Lesson 2).
- The estate's two internet-facing hosts now sit in the account that holds the deploy roles and the
  production data path, and GuardDuty is still scheduled at Stage 15 — a widening of exposure recorded
  here rather than absorbed.
- **Revision trigger:** an account slot frees, or the quota is raised → `VPC-Networking` and
  `VPC-SharedServices` migrate to a `shared` platform account. The slices are cut as
  `production/networking/` and `production/foundation/` precisely so that move is a folder migration
  (Recipe E) rather than a rebuild, and `10.60.0.0/16` is reserved for it.

What the split buys back immediately is the largest thing D14 accepted losing: an Interactive account no
longer reaches the runtime VPC, because no peering exists between them.

### 3. Two hosts, not one

The WireGuard host parses untrusted UDP from the internet; the proxy parses untrusted responses from the
internet. They are separate `[D]` instances in the same public tier, with separate security groups and
separate `[P]` Elastic IPs, so a compromise of one is not a compromise of the other. The cost of the second
address is USD 3.65/month.

The **WireGuard host's** Elastic IP is *transferred* from Sandbox rather than reallocated (AWS supports
this within a Region, at no charge, with a seven-day acceptance window and the address disassociated at
accept time), so every client keeps its `Endpoint` line. The **proxy's** address is new, and it becomes the
anchor of every VPN-only condition.

### 4. The client plane is not special

The VPN client sits inside the private network. Its internet is the private network's internet, so it
crosses the proxy like every other client, and the enforcement lives on the WireGuard host where a user
cannot revert it: tunnel packets are forwarded to RFC1918 destinations only and everything else is dropped.
A laptop with no proxy configured reaches the intranet and nothing else.

Two consequences worth stating because they are easy to get backwards:

- **The anchor moves to the proxy's address.** A laptop's control-plane call exits through Squid, so
  `DenyControlPlaneOffVpn`'s `aws:SourceIp` is the proxy's EIP; `aws:SourceVpc` is `VPC-Networking`; and
  the lake's `aws:SourceVpce` branch gains the hub's S3 gateway endpoint, because S3 from the proxy still
  leaves through it.
- **Per-device attribution is preserved by routing, not by logging.** Inside `VPC-Networking` the proxy's
  subnet carries a route for `10.90.0.0/24` to the WireGuard host's ENI and the host does not masquerade
  traffic bound for the proxy, so the access log records `10.90.0.<device>`. That range appears in no other
  route table, in any account.

### 5. Where the client plane resolves — the structural repair

An interface endpoint with private DNS installs an AWS-managed private zone that is authoritative for the
whole subtree of the service name, and it is visible only from the VPC that owns the endpoint. That is the
mechanism behind Lessons 40-43: a full-tunnel laptop resolving through an Interactive VPC received
**private** addresses for client-plane names, and the SageMaker Unified Studio portal — a public origin —
could only reach them after a browser grant.

The repair is separation, and the hub delivers it as a side effect: the client's `DNS =` points at
`VPC-Networking`'s resolver, and **`VPC-Networking` carries no interface endpoint with private DNS and no
service-name private zone**. Client-plane names then answer publicly while the compute plane keeps its
endpoints. Sandbox may re-add `datazone`, removed on 2026-08-25 for exactly this reason.

This is also why **interface endpoints are never centralized in the hub**, though that is the institutional
pattern: it would put the compute plane's zones back on the client's resolver, and it would make every
spoke's AWS call carry the hub's `aws:SourceVpc`, satisfying the personas' VPN-only condition from any
account. Revisit only when a second business unit makes the endpoint bill dominant (D35).

### 6. What the two filters become

`objectives.md` requires two filters: the institutional proxy's, and SageMaker's stricter one on top. Under
an explicit proxy the compute never resolves an internet name — Squid does, in the hub — so a per-VPC DNS
firewall can no longer filter the internet. Both filters therefore live in Squid, as **source-scoped**
allow-lists: one list per plane (the tunnel range, Sandbox, SharedServices, Workloads), with a
private-destination deny in front of all of them so the proxy cannot become an L7 bridge between VPCs that
peering deliberately keeps apart.

The DNS firewall survives in every compute VPC with a different job: an allow-list of AWS and intranet
names plus the blocking rule, which closes the recursive resolver as an exfiltration channel — the classic
residual of a VPC with no NAT. `VPC-Networking` carries none, because the proxy has to resolve.

The proxy terminates CONNECT without decrypting, so it sees the requested hostname (which survives
Encrypted Client Hello, unlike SNI inspection) and the byte counts, and never the content. Domain fronting
through an allowed CDN host stays an accepted residual, recorded in Stage 11's threat model.

### 7. What this does not decide

The proxy's allow-list contents (Stage 6c writes the first version, Stage 11 owns the policy), TLS
interception (rejected today: it would add a fourth trust surface and a CA in every image — D36's trigger),
and whether a second business unit changes the topology (D35's question, answered at Stage 14 with N in
hand).

---

## Revision trigger

- An account slot frees or the quota is raised → move `VPC-Networking` and `VPC-SharedServices` to a
  `shared` platform account (§2).
- A service is found that needs the internet and cannot use a proxy → a NAT gateway **in that service's
  VPC**, priced and dated (§1).
- The endpoint bill becomes the dominant line at N > 1 Sandboxes → re-open centralization, against §5's
  constraint (§5).
- The proxy's access log stops being sufficient evidence for Stage 11's egress leg → TLS interception is
  re-argued against D36's fourth-surface trigger (§6).

---

*Decisions index: [INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
