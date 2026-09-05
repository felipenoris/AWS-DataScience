# Stage 6c — Networking: three VPCs in Production and one egress for the estate

| | |
|---|---|
| **Status** | not started — **created 2026-09-05** with [6b](stage-06b-development-becomes-staging.md), on the user's re-scope. It builds what [open question 23](../open-questions.md) has owed since 2026-08-25 and closes it as **D38**: a `VPC-Networking` hub in Production carrying the estate's only internet gateway, an explicit HTTP/HTTPS proxy, and the VPN endpoint; `VPC-SharedServices` for GitLab, Pages and the runners; `VPC-Workloads` for the production runtime. It also repairs, structurally, the client-plane DNS shadowing of Lessons 40-43 — the VPN client stops resolving through a VPC that holds compute-plane endpoints |
| **Prerequisites** | [Stage 3](stage-03-networking.md) (the `vpc` and `vpc-egress` modules, the peering pattern in `production/foundation/peers.tf`, the `[P]`/`[E]` split), [Stage 4](stage-04-vpn.md) (the WireGuard module and its `[P]` anchors), [6a](stage-06a-unified-studio.md) (the endpoint lists and what a Studio app needs). **6b is not a prerequisite**: the two stages meet at one object, the `Development ↔ Production` peering, which this stage re-cuts whatever the account is called |
| **Consumes** | [D4](../decisions/D04-vpn-wireguard.md), [D5](../decisions/D05-sagemaker-egress.md), [D6](../decisions/D06-dlp-approach.md), [D9](../decisions/D09-az-count.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D35](../decisions/D35-sandbox-cardinality.md), [D36](../decisions/D36-internal-pki.md) |
| **Proves** | [INT-05](../integrations.md) and [INT-06](../integrations.md) re-keyed on the hub; [INT-16](../integrations.md)'s closing choice (fallback (i) on the domain execution role) becomes takeable because this stage owns the address it is keyed on; **INT-21** (new — every account's compute reaching a Production-owned proxy over peering, the estate's first cross-account *network* dependency that is not an IAM crossing) and **INT-22** (new — the `awsds.internal` zone × VPC association matrix) |

*Read with [`docs/plan/conventions.md`](../conventions.md), [`docs/NETWORK.md`](../../NETWORK.md) (the
network as built, re-measured in this stage's own sittings) and
[`docs/plan/runbooks/vpn.md`](../runbooks/vpn.md), whose §S topology this stage rewrites.*

---

**Objective:** one internet egress for the whole cloud, behind one HTTP/HTTPS proxy, with the VPN client
treated as what it is — a client of the private network, which therefore reaches the internet the same way
every other client does. Three VPCs in Production; five peerings; no NAT gateway anywhere; no default route
in any spoke.

## The premise the whole design rests on, stated once

**VPC peering shares an address, never a path.** AWS documents it in one place and it decides five things
below: *"If VPC A has an internet gateway, resources in VPC B can't use the internet gateway in VPC A"*,
the same for *"an NAT device"* and for *"the gateway endpoint to access Amazon S3"*, and
*"VPC peering does not support transitive peering relationships"*. A peering route may only carry the peer
VPC's CIDR, so a `0.0.0.0/0` pointed at a peering blackholes silently.

Therefore:

1. **The single egress reaches a spoke only as an explicit proxy** — an ENI address inside
   `VPC-Networking`'s CIDR that clients are configured to use. There is no transparent path.
2. **No spoke has a default route at all.** That is design B's shape from
   [D5](../decisions/D05-sagemaker-egress.md), and it closes the two bypasses design A could not
   (a raw address, and DNS-over-HTTPS to a public resolver): a subnet with no default route has no door
   the proxy does not see.
3. **A NAT gateway would serve only the VPC it lives in.** Zero are built. One is *priced* below and
   remains the named contingency for a service that needs the internet and cannot be told about a proxy.
4. **Each VPC keeps its own free S3 and DynamoDB gateway endpoints** — they do not cross a peering, and
   they are the `aws:SourceVpce` anchors INT-05 names.
5. **Interface endpoints stay per VPC and are never centralized in the hub.** Centralizing them would put
   compute-plane private zones back on the resolver the VPN client uses (Lesson 43 at a new address) and
   would make every spoke's AWS call carry the hub's `aws:SourceVpc`, satisfying the personas' VPN-only
   condition from any account.

**The client plane is not special.** The VPN client sits inside the private network; its internet is the
private network's internet, so it goes through the proxy like everything else. The enforcement is on the
WireGuard host, where the user cannot revert it: tunnel packets are forwarded to RFC1918 destinations only,
and everything else is dropped. A laptop with no proxy configured reaches the intranet and nothing beyond it.

## What this builds, and in which account

| Object | Where | Layer | Note |
|---|---|---|---|
| `VPC-SharedServices` **10.30.0.0/16** | Production, `foundation/` (the VPC that exists today) | `[P]` | GitLab, Pages, the runners, the build host. No rebuild: the ids, the two peering accepters and the four zone associations survive |
| `VPC-Networking` **10.31.0.0/16** | Production, `networking/` (new) | `[P]` | The only IGW; the public tier is the estate's only internet-facing tier |
| `VPC-Workloads` **10.32.0.0/16** | Production, `workloads/` (new) | `[P]` | The production SageMaker runtime, MWAA Serverless workers, production jobs |
| WireGuard host + its `[P]` anchors | Production, `vpn/` | `[D]` + `[P]` | The Sandbox host's **Elastic IP is transferred**, so no client `.conf` changes its `Endpoint` |
| Squid host + its `[P]` EIP | Production, `proxy/` | `[D]` + `[P]` | The estate's single egress. Its EIP is the new anchor of every VPN-only condition |
| `awsds.internal` + three child zones | Production `foundation/`, and each spoke | `[P]` | With an explicit association matrix (INT-22) |
| Five peerings | requester side per spoke, accepter side in Production | `[P]` | Networking × 4, SharedServices × Sandbox |
| Interface endpoints | every VPC **except** `VPC-Networking` | `[E]` | Single AZ (D9), private DNS on |
| DNS Firewall | every compute VPC | `[E]` | Re-cut to an intranet-and-AWS list. **It no longer filters the compute's internet** — an explicit-proxy client never resolves an internet name, so that filter moved to the proxy's Sandbox ACL. It keeps the names the compute resolves *directly* and closes the recursive resolver as an exfiltration channel |
| **Zero** NAT gateways | — | — | Priced in §Cost as the contingency |

## Ordering, and what it depends on

Passes 0-3 are `[P]` and can be applied in any sitting. Pass 4 is the cut-over and is one sitting with a
blackout window. Pass 5 is the spokes. Pass 6 measures. **Stage 7 waits on passes 1-2** (GitLab needs
`VPC-SharedServices` and the `awsds.internal` zones); **Stage 13's public tier** lands in
`VPC-Networking`'s public tier as its second enumerated listener; **[6d](stage-06d-unified-studio-remainder.md)
waits on pass 5**, because what a Studio app can reach changes here.

**Who does what:** **Claude** writes every slice and module, runs `plan`, the read-only instruments and the
gates, drafts every console step with each field named, and re-measures `docs/NETWORK.md` in the same
sitting as each apply. **The user** runs every `terraform apply`/`destroy`, authorizes the two
address-transfer calls, copies the host-key secret value by hand, edits each device's `.conf`, and writes
the log.

---

## To execute

### 0. Settle the design and prepare the vocabulary — the groundwork that has no AWS side

**Why:** three VPCs in one account break four assumptions in the tooling at once, and `layers.py` refuses
to import a slice kind it has no rank for. None of this is visible in a `plan`, so it comes first.

- **Writing D38 — Claude:** `docs/plan/decisions/D38-single-egress-hub.md`, closing open question 23: the
  hub's account and axis, how traffic reaches it (peering, with the premise above), what the proxy is
  (explicit CONNECT, no TLS interception), what happens to the per-account NATs (destroyed) and DNS
  firewalls (re-purposed), where the client plane resolves, and the revision trigger *"an account slot
  frees → `VPC-Networking` and `VPC-SharedServices` migrate to a `shared` platform account"*. Add the row
  to the decisions INDEX and one bullet to `history.md`.
- **Writing Lesson 44 — Claude:** *"What peering shares is an address, never a path: no route may borrow a
  peer VPC's gateway"* — in `lessons.md`, with its recognition key in `CLAUDE.md`.
- **Extending the address vocabulary — Claude:** `scripts/tfhygiene/backend.py` gains a per-**(account,
  VPC)** CIDR and zone table: `production-shared` 10.30.0.0/16, `production-networking` 10.31.0.0/16,
  `production-workloads` 10.32.0.0/16, `sandbox` 10.20.0.0/16, `staging` 10.50.0.0/16. Delete the
  10.40.0.0/16 reservation (6b keeps the account on 10.50) and leave **10.60.0.0/16 unused**, reserved for
  the `shared` account D38's trigger names. `10.16.0.0/13` stays the Sandbox supernet; `10.90.0.0/24`
  stays the WireGuard client range.
- **Adding the slice ranks — Claude, before any folder exists:** `RANKS` in
  `scripts/tfhygiene/layers.py` gains `networking` (21), `shared-vpc` if the split needs it, `workloads`
  (23) and `proxy` (41) — Recipe C's rule is rank first, folder second, same commit.
- **Bumping the VPC module — Claude:** `terraform-modules/vpc` **v0.2.0** takes a `name_suffix` so three
  VPCs in one account get distinct `Name` tags (`awsds-prod-shared-vpc`, `awsds-prod-networking-vpc`,
  `awsds-prod-workloads-vpc`) and distinct security-group names. Two commits, one tag (the runbook's
  order). Note in the plan review that the **existing** VPC's tags change in place while its security
  groups are replaced.
- **Teaching the peering pattern about three VPCs — Claude:** `production/foundation/peers.tf` finds a
  peer by the single tag `awsds-<env>-vpc`; that lookup becomes per-VPC and the peering map moves into
  `backend.py` so both sides are generated from one list (Lesson 14).
- **Fixing the doc gate — Claude:** `scripts/check-network-doc.py` rule B recomputes subnet tiers from one
  CIDR per account; it now reads the per-VPC table, and `docs/NETWORK.md` §2.1 gains every new
  network-bearing slice.

### 1. Build the three VPCs — the address plan, and the tiers that carry the new rules

**Why:** the hub needs a public tier that is the estate's only internet-facing tier, and the two other VPCs
need to exist before anything can be peered to them. Nothing here costs money at rest.

- **Re-labelling the existing VPC — Claude edits, user applies:** `production/foundation/` keeps VPC
  10.30.0.0/16 and becomes **`VPC-SharedServices`** — the least-churn choice, since GitLab was always
  planned in its private tier, both peering accepters live there and the four zone associations point at
  it. Apply the `name_suffix` and read the plan: tags in place, security groups replaced, VPC and gateway
  endpoint **ids unchanged**.
- **Creating `production/networking/` — Claude writes, user applies:** VPC 10.31.0.0/16 from the same
  module, both AZs by `zone_id` (D9), IGW attached, the public tier carrying the estate's only
  `0.0.0.0/0 → igw` route, S3 and DynamoDB gateway endpoints on every route table, flow logs on.
- **Creating `production/workloads/` — Claude writes, user applies:** VPC 10.32.0.0/16, same shape, **no
  IGW route in any of its route tables** — the module still creates the gateway (free, unused), and the
  absence of the route is what makes the tier private.
- **Enumerating the ingress tier — Claude:** write into `docs/AWS_STATE.md` the invariant *"internet-
  originated traffic terminates only in `VPC-Networking`'s public tier, and every listener there is
  enumerated"* — today the WireGuard host's UDP/51820; Stage 13's public ALB becomes the second row. A
  world-open rule anywhere else is a finding.
- **Writing the no-public-address gate — Claude:** extend `./aws/networking.py` with a check that fails on
  any IGW route, public IP or world-open security-group rule outside that tier, in any account.

### 2. Build the internal DNS — `awsds.internal`, and the association matrix that makes it resolvable

**Why:** private hosted zones do not delegate, overlapping zones resolve by most-specific match, and a VPC
associated with a zone that matches the name but holds no record gets **NXDOMAIN** rather than a public
answer. So the association matrix is the design, not an afterthought — and it must be written down (INT-22)
because nothing derives it.

- **Creating the apex — Claude writes, user applies:** `awsds.internal`, owned by `production/foundation/`
  (the SharedServices slice, since the services named directly under the apex live there). Records:
  `gitlab.awsds.internal`, `pages` is **not** here (next bullet), plus `proxy.awsds.internal` and
  `vpn.awsds.internal` written by pass 4 from the two hosts' private addresses.
- **Creating the three child zones — Claude writes, user applies:** `sandbox.awsds.internal` (owned by
  Sandbox), `staging.awsds.internal` (owned by the renamed account), `prod.awsds.internal` (owned by
  `production/workloads/`).
- **Keeping Pages on its own apex — Claude:** `awsds-pages.internal`, unchanged in intent from D36 — a
  sibling under the shared apex would weaken the cookie-scope separation the two-apex choice exists for.
  Cost: USD 0.50/month.
- **Writing the association matrix — Claude, into `docs/NETWORK.md` §10 and enforced by a new `NT` check:**

  | Zone | Associated with |
  |---|---|
  | `awsds.internal` | all five VPCs |
  | `sandbox.awsds.internal` | Sandbox, `VPC-Networking` |
  | `staging.awsds.internal` | Staging, `VPC-Networking` |
  | `prod.awsds.internal` | `VPC-Workloads`, `VPC-SharedServices`, `VPC-Networking` |
  | `awsds-pages.internal` | `VPC-SharedServices`, `VPC-Networking` |

- **Reversing the authorization direction — Claude writes, user applies:** the spoke-owned child zones
  authorize **Production's `VPC-Networking`** (`create-vpc-association-authorization` on the owner side,
  `associate-vpc-with-hosted-zone` on Production's side) — the opposite of today's choreography, in which
  Production authorizes and the spokes associate. Keep the authorizations in state, as `peers.tf` does.
- **Retiring the old zones — user applies, after pass 6 measures the new ones:** `sandbox.internal`,
  `prod.internal` and `pages.internal` are destroyed with their associations. Zones cannot be renamed, so
  this is create-then-retire and the two families coexist for one sitting.

### 3. Build the five peerings — and generate every route from one map

**Why:** the isolation rule in the user's brief — Interactive and Workloads never talk — is enforced by the
*absence* of a peering, which is the cheapest control in the design. Adding peerings "because they might be
needed" spends it. Deploys are AWS API calls and need no L3 path into a target VPC.

- **Declaring the matrix — Claude, in `backend.py`:**

  | Requester | Accepter | Why |
  |---|---|---|
  | Sandbox | `VPC-Networking` | VPN reach, the proxy |
  | Staging | `VPC-Networking` | the proxy |
  | `VPC-Workloads` | `VPC-Networking` | the proxy |
  | `VPC-SharedServices` | `VPC-Networking` | the proxy, and the VPN's reach to GitLab |
  | Sandbox | `VPC-SharedServices` | `git clone` from a notebook (INT-09 re-homed), the laptop to GitLab and Pages |

  **Not built, and the omission is the control:** Sandbox ↔ Staging, Sandbox ↔ `VPC-Workloads`,
  `VPC-SharedServices` ↔ Staging, `VPC-SharedServices` ↔ `VPC-Workloads`.
- **Writing down why the last two are absent, because the intuition says otherwise — Claude, in this file
  and in D38:** *deployment is an API act.* The runner in `VPC-SharedServices` assumes a role across the
  account boundary and calls SageMaker, CloudFormation and S3; the artifacts travel as ECR images,
  CodeArtifact packages and S3 objects, every one reached through an endpoint in the target's own VPC.
  **Nothing in a deployment target clones a repository** — the image carries the code (D28), so a runtime
  `git clone` there is a contract violation to catch rather than a path to provide. What it costs to keep
  them absent is one later change; what building them costs is standing L3 reach from the host that
  executes repository-supplied build code into both deployment targets, which is exactly the blast radius
  D14 accepted and Lesson 2 warns about.
- **Naming the trigger, so it is recognised rather than rediscovered — Claude:** a peering to a deployment
  target is added when a **shared service is consumed at runtime** rather than at deploy time. The
  candidates, none of which exists today: a package mirror or registry proxy on an instance (as opposed to
  ECR and CodeArtifact, which are endpoints), a metrics or log collector that is not CloudWatch, an
  internal secrets or configuration service, or a certificate-status endpoint. **The internal CA is not
  one** — D36 issues no CRL and runs no OCSP responder, by decision. When one does appear, prefer a
  regional service or an endpoint over a peering; the peering is the last resort, and it is generated from
  the same map as the rest (one edit, both sides).
- **Generating both sides — Claude writes, user applies:** the accepter side stays in Production
  (`foundation/` for SharedServices, `networking/` for the hub), subnet-scoped routes on **both** sides,
  applied accepter-last as the existing pattern does.
- **Routing the tunnel's return path — Claude:** every spoke private route table carries a route to
  `VPC-Networking`'s **public** tier (where both hosts live) as well as its private tier.
- **Keeping `10.90.0.0/24` out of every table but one — Claude:** the WireGuard client range is masqueraded
  today and stays invisible to the spokes. The **one** exception is inside `VPC-Networking`: pass 4 adds
  `10.90.0.0/24 → the WireGuard host's ENI` to the proxy's subnet table, in the same VPC, so Squid logs a
  per-device address. `./aws/networking.py` `NT-4` is re-cut from *"no route to 10.90/24"* to *"no route to
  10.90/24 outside `VPC-Networking`"*.
- **Adding the two-way route check — Claude:** new `NT-11` — every active peering has a route on both
  sides in every affected route table. The reference implementation this project keeps as a comparison has
  exactly this defect (an attachment with no route), which is why the check exists.

### 4. Move the VPN and build the proxy — the cut-over, and the only blackout in the stage

**Why:** the estate's entry point and its exit point both move accounts in one sitting. Two hosts rather
than one: the WireGuard host receives untrusted UDP from the internet, the Squid host parses untrusted
internet responses, and separating them keeps a compromise of either off the other. The Elastic IP transfer
is what keeps every client's `Endpoint` line unchanged.

- **Preparing the anchors — Claude writes, user applies:** `production/networking/` exports the same output
  names the Sandbox slice does (`wireguard_eip_public_ip`, `vpc_id`, `s3_gateway_endpoint_id`,
  `wireguard_security_group_id`, `wireguard_host_key_secret_arn`) — `VPN_HOMES` resolves by name. The
  security group is new (UDP/51820 world-open, and nothing else); the host-key secret is new and **empty**.
- **Copying the host key — user, by hand, never through Terraform or Claude:** `get-secret-value` in
  Sandbox → `put-secret-value` in Production. The key is what keeps every client's public key valid; a new
  key would mean re-issuing every peer.
- **Disassociating the address — user applies:** `sandbox/vpn/`'s `aws_eip_association` is destroyed on its
  own (a plan written first, per the runbook's §8 rule — `make down` stops the host but leaves the address
  associated). `accept-address-transfer` refuses an associated address with
  `InvalidTransfer.AddressAssociated`.
- **Transferring the address — Claude runs, user authorizes each call:**

  ```bash
  aws ec2 enable-address-transfer --allocation-id <the Sandbox allocation> --transfer-account-id <Production>
  aws ec2 accept-address-transfer --address <the address>
  ```

  Same Region, no charge, seven days to accept, tags reset. Read `describe-addresses` in Production
  afterwards: whether the allocation id survives is **not documented**, and the answer decides the next
  bullet.
- **Bringing the address into state — Claude writes, user applies:** an `import {}` block in
  `production/networking/` and a `removed {}` block with `destroy = false` in `sandbox/foundation/`
  (Terraform 1.15.8 supports both), so neither side tries to create or release it.
- **Building the WireGuard host — Claude writes, user applies:** `production/vpn/` `[D]`, in
  `VPC-Networking`'s public tier, from the existing module. Three changes to the module (**v0.5.0**):
  `vpc_nat_cidrs` is **removed** (the isolated-tier NAT job dies with the buildbox's move), the
  `PostUp` chain forwards tunnel packets **only to RFC1918 destinations** and drops the rest, and it stops
  masquerading traffic destined for the proxy's address so Squid sees `10.90.0.x`.
- **Building the proxy — Claude writes, user applies:** `production/proxy/` `[D]`, a second host in the
  same public tier with its **own `[P]` Elastic IP** and a security group admitting **TCP/3128 from the
  spoke and tunnel CIDRs only** — no world-open rule, so the ingress invariant of pass 1 still reads one
  listener. Squid configuration, in this order:

  - `acl to_private dst 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 100.64.0.0/10` +
    `http_access deny to_private`, **before every allow** — without it the proxy is an L7 bridge between
    VPCs that peering deliberately keeps apart. `dst` (not `dstdomain`) also catches a public name that
    resolves to a private address.
  - `SSL_ports 443`, `Safe_ports 80 443`, `http_access deny CONNECT !SSL_ports`.
  - Source-scoped allow-lists, one per plane — **and this is where BOTH of the objectives' two filters
    now live**, because an explicit-proxy client never resolves an internet name and a per-VPC DNS
    firewall therefore cannot see one. The tunnel range `10.90.0.0/24` carries **the institutional web
    filter**: the list of what a person on a company laptop may reach, starting with the SMUS portal,
    console and Identity Center families and the AWS API endpoints the laptop calls. The Sandbox CIDR
    carries **SageMaker's stricter list** — today's DNS Firewall allow-list moved here verbatim, minus its
    wildcard and minus the portal families, which belong to the tunnel. The SharedServices CIDR carries
    the build hosts' package sources; the Workloads CIDR is empty by default. One list per source, so a
    name allowed for a person is not thereby allowed for a notebook.
  - `http_access deny all` last.
- **Keeping the configuration out of the host — Claude:** the allow-lists are `[P]` data (an SSM parameter
  or a Secrets Manager secret rendered at boot), never state that exists only on a `[D]` disk (Lesson 4).
- **Shipping the access log — Claude writes, user applies:** the CloudWatch agent to a `[P]` log group in
  Production, KMS-encrypted, with the proxy's role holding `CreateLogStream`/`PutLogEvents` and no delete;
  an export to Log Archive so the author of the allow-list does not own its record (Lesson 18). Fields:
  time, source, CONNECT host, status, bytes in and out. This is Stage 11's egress evidence.
- **Re-keying the VPN-only conditions — Claude edits, user applies:** with the client's internet crossing
  the proxy, a laptop's control-plane call presents the **proxy's** address. So `VPN_HOMES` yields:
  `aws:SourceIp` = the proxy's EIP, `aws:SourceVpc` = `VPC-Networking`, and `trusted_vpce_ids` gains
  `VPC-Networking`'s S3 gateway endpoint id (S3 from the proxy still leaves through it, so the lake's
  `aws:SourceVpce` branch survives). Apply `identity/sso/` and `data-governance/data/` as
  `InfrastructureAccess`, which is outside the deny by decision — the recovery path (open question 17).
  Read the Sandbox lake's and the projects bucket's policies in the same sitting: any `aws:SourceVpce`
  branch there needs the hub's gateway id too.
- **Destroying the old home — user applies, last:** `sandbox/vpn/` and the VPN anchors in
  `sandbox/foundation/`, once pass 6's readings pass. `VP-2` (no orphan allocation) is the closing check.

### 5. Turn the spokes into design B — no NAT, no default route, and a DNS firewall with a new job

**Why:** with the proxy reachable, the per-account NAT gateways are the last transparent path and the only
metered thing in the egress slices that the design no longer wants. Removing them is also what makes the
proxy's allow-list the single filter it is supposed to be.

- **Destroying both NAT gateways — Claude edits, user applies:** `egress_mode = "B"` in Sandbox and in the
  renamed Staging; the private route tables lose their `0.0.0.0/0` entirely. `vpc-egress` **v0.5.0** drops
  the NAT half rather than keeping dead code.
- **Completing the endpoint sets — Claude edits, user applies:** under B the SMUS network-isolation page's
  required list finally applies, because its premise (no public egress) is true. Sandbox re-adds
  `datazone` — removed on 2026-08-25 only because its private zone shadowed a client-plane name, which
  cannot happen now — and gains `ec2`, `ec2messages`, `secretsmanager`, `ssm`, `ssmmessages` and `q`.
  Measure rather than copy: six of those names have never existed here, and `codewhisperer` is
  `us-east-1`-only.
- **Giving every instance-bearing spoke its SSM path — Claude:** `ssm`, `ssmmessages` and `ec2messages`
  endpoints in Sandbox, `VPC-SharedServices` and `VPC-Workloads`. Session Manager does not work through an
  HTTPS proxy listener, and the shell that reads the proxy's own log must not depend on the proxy
  (Lesson 24). `VPC-Networking`'s two hosts reach SSM through the IGW directly.
- **Re-cutting the DNS Firewall — Claude edits, user applies:** it stays in every **compute** VPC and its
  allow-list shrinks to `*.amazonaws.com`, `*.api.aws`, `.awsds.internal` and the proxy's name; the
  `BLOCK`-NXDOMAIN `*` rule stays. Its job is no longer filtering the internet (an explicit-proxy client
  never resolves an internet name) but closing the recursive resolver as an exfiltration channel. The
  internet allow-list moves verbatim into Squid's Sandbox ACL. `VPC-Networking` carries **no** firewall —
  the proxy has to resolve. `EXC-04`, `EXC-05` and `EXC-06` close with the old list; `DN-1`..`DN-4` are
  re-aimed at the Squid lists, read through SSM the way `vpn.py --on-host` reads the VPN host.
- **Writing the hub invariant into the instruments — Claude:** `VPC-Networking` holds **no** interface
  endpoint with private DNS and **no** service-name private zone; `NT-10` fails if it ever seizes a
  client-plane name.
- **Delivering the proxy variables — Claude:** one generated `NO_PROXY` list, in every seam that carries
  it: `.us-west-2.amazonaws.com` (every service the VPC holds an endpoint for; S3 and DynamoDB ride the
  gateway prefix lists), `169.254.169.254`, `169.254.170.2`, `localhost`, `.awsds.internal`, and the
  RFC1918 ranges. **Never an `ENV HTTP_PROXY` in `images/base`** — every application image inherits from
  it and runs as a Production job behind endpoints, where a wrong `NO_PROXY` would send S3 and STS out
  through the proxy as a public address. Build time is a BuildKit `--build-arg`; runtime in a Studio space
  is a JupyterLab lifecycle configuration attached through the SageMaker AI console (the documented path;
  CLI attach is not supported) or `ContainerEnvironmentVariables` on the app image config, which also
  writes `pip.conf`, `.condarc` and the Julia and R equivalents.
- **Moving the build host — Claude edits, user applies:** `sandbox/buildbox/` moves to
  `VPC-SharedServices` beside the runners, with the docker daemon and the SSM agent proxy-configured. Its
  only egress today is a route to the WireGuard host's ENI, and a route target cannot live in another VPC.
  The `vpc_nat_cidrs` input, the isolated-tier security-group rule and the *must not coexist with
  `probes/`* rule all die in the same commit; `runbooks/buildbox.md` is rewritten in the same sitting.
- **Naming the NAT contingency — Claude, in D38 and in this file:** a NAT gateway is built **only** for a
  named service that needs the internet and cannot be told about a proxy, in **that service's own VPC**,
  with its own cost row and a trigger to remove it. The first candidate is MWAA Serverless, which exposes
  no proxy setting — Stage 10 gives its workers private routing with endpoints instead, and only if that
  measurement fails does the contingency fire.

### 6. Measure the whole thing — the readings that close the stage

**Why:** every claim in this stage is about a path, and a path is measured, never read off a diagram. Three
of these readings also close obligations older than the stage.

- **Measuring the tunnel — user, from a client:** the `.conf` changes **only** its `DNS =` line (to
  `VPC-Networking`'s `.2`); the `Endpoint` is unchanged because the address moved with it. Then
  `runbooks/vpn.md` §C's three checks, plus a fourth: `curl https://1.1.1.1` **times out** and
  `curl -x proxy.awsds.internal:3128 https://checkip.amazonaws.com` prints the **proxy's** EIP.
- **Closing the shadowing — user, from the tunnel:** `dig agent.datazone.us-west-2.api.aws` and
  `dig <domain-id>.studio.us-west-2.sagemaker.aws` return **public** addresses, and the SageMaker Unified
  Studio portal opens with **no** Chrome Local Network Access grant. That is Lesson 43's repair and the
  reading that retires the interim.
- **Proving the isolation — Claude, over SSM:** from a Sandbox probe, `curl -x proxy:3128 https://<a
  Workloads private address>` returns the proxy's **403** while `https://pypi.org` returns 200; the mirror
  from a Workloads probe. Two distinguishable outputs, which is what makes it a verification.
- **Proving the drop rule — user, from the tunnel:** with the laptop's proxy setting removed, no internet
  is reachable and `gitlab.awsds.internal` still is.
- **Re-measuring the vending path — Claude and user:** `s3-read-write` from the laptop, and
  `runbooks/sandbox-lake.md` §T's laptop half, both from the new tunnel, with the CloudTrail
  `sourceIPAddress` and `vpcEndpointId` pair read for each call. This is the proof that the re-keying of
  pass 4 was complete.
- **Taking INT-16's closing choice — user:** fallback (i) (`DenyUserAccessFromUnauthorizedVPCs` on the
  domain execution role, keyed on the proxy's EIP, AWS's `*:user-*` carve-out kept) versus recorded
  acceptance. The address is now stable and owned by this stage, which is what the choice was waiting for.
- **Re-measuring the documents — Claude, same sitting:** `docs/NETWORK.md` rewritten from the readings, not
  from this file; `./scripts/check-network-doc.py` green; `./aws/networking.py` and `./aws/egress.py`
  snapshots regenerated; `docs/AWS_STATE.md`'s §C rows, the VPN row and the DNS rows restated.

### 7. Close the stage — cost, lifecycle and the two operational instruments

**Why:** the hub makes one account's `[D]` host a dependency of every other account's session, and
`make up`/`down` has no concept of that. Left alone, a stopped hub host is a blackhole rather than an error
— the failure mode `buildbox.md` already documents for one tier, now estate-wide.

- **Splitting the hub's lifecycle — Claude:** `make hub-up` / `make hub-down` (or
  `slices.py up --env production --only vpn,proxy`) so a Sandbox session starts the two hosts **without**
  starting GitLab or Production's `[E]` endpoints.
- **Turning the blackhole into an error — Claude:** `make up ENV=<spoke>` reads the hub hosts' state
  through `./aws/vpn.py` and **refuses** with a message when either is stopped.
- **Writing the proxy instrument — Claude:** `./aws/proxy.py`, read-only by default, with an `--on-host`
  flag on the `vpn.py` pattern: the Squid access log tail and a diff of the running allow-list against the
  committed one, both through SSM Run Command.
- **Restating the cost — Claude:** rewrite `docs/plan/cost-model.md`'s hourly table on the zero-NAT basis
  and add the measured rows to `docs/PRICING.md` first (Lesson 6) — Transit Gateway USD 0.05 per
  attachment-hour plus 0.02/GB (the number that records why peering was chosen), Route 53 Resolver endpoint
  USD 0.125/h per ENI (which rules out the forwarding-rule shape of open question 23), the Squid host at
  PRICING §8's `t3.micro` rate, and MWAA Serverless at USD 0.088 per task-hour. Correct
  `architecture.md` §4.3a's proxy figure, which is roughly twice the measured rate, and reconcile PRICING
  with the cost model on peering (charged **cross-AZ** only).

---

## Deliverables

- `production/{networking,workloads}/` and the re-labelled `production/foundation/`, three VPCs, one IGW.
- `production/vpn/` and `production/proxy/`, two `[D]` hosts with two `[P]` Elastic IPs, one of them
  transferred rather than allocated.
- Five peerings with routes on both sides, generated from one map.
- `awsds.internal` + three child zones + `awsds-pages.internal`, with the association matrix in
  `NETWORK.md` and a check that reads it.
- Zero NAT gateways, zero default routes outside `VPC-Networking`, and a DNS firewall in every compute VPC
  with an intranet-only list.
- `D38`, Lesson 44, `INT-21`, `INT-22`, `./aws/proxy.py`, `make hub-up`/`hub-down` and the spoke guard.

## Validation

- `./aws/networking.py`: `NT-3`/`NT-6` re-cut (no route or peering between an Interactive VPC and a
  Workloads or Staging VPC), `NT-4` (no `10.90.0.0/24` route outside the hub), `NT-10` (the hub seizes no
  client-plane name), `NT-11` (every peering routed both ways) — all `pass`.
- `./aws/egress.py`: no NAT gateway in any account; every private route table without a default route.
- `./aws/vpn.py`: `VP-1`..`VP-9` from the new home, `VP-2` with no orphan allocation, `VP-3` still one
  world-open rule in the estate.
- The six readings of pass 6, each with its two distinguishable outcomes.

## Cost

Measured rates, us-west-2 (PRICING §7/§8 after step 7's additions): the design removes two NAT gateways
(**−0.100/h** while a session runs, −0.090/GB) and adds one Elastic IP (**+USD 3.65/month**, the proxy's)
and one to two private hosted zones (**+USD 0.50-1.00/month**). The two `[D]` hosts bill only while running
(`t3.nano` 0.0052/h, `t3.micro` 0.0104/h). Interface endpoints stay 0.010/h each, per VPC, single AZ —
`VPC-Networking` carries none. Peering is free within an AZ and 0.01/GB each way across one, so pinning the
hosts and the endpoint sets to `usw2-az1` keeps the common path free. **A standing NAT gateway would be
0.050/h ≈ USD 36.50/month**, which is why it is a contingency and not a component.

## Risks

- **The address transfer fails or the allocation id changes.** Mitigated by disassociating first, by
  reading `describe-addresses` after the accept, and by the `import`/`removed` pair. If the transfer is
  refused, the fallback is a new allocation and a new `Endpoint` line in every `.conf` — a client-side
  edit, not a redesign.
- **A service that cannot use a proxy is discovered late.** Named as the NAT contingency, per VPC, with
  MWAA Serverless as the known first candidate.
- **The blackout window.** Between the disassociation and the new host coming up, the tunnel, the buildbox,
  the sandbox lake, `s3-read-write` and the portal are unavailable. One sitting, planned, and the
  `[P]` anchors of both accounts exist before it starts.
- **A re-keying that locks every persona out.** The three conditions are applied as
  `InfrastructureAccess`, which carries no VPN-only deny by decision, and the plan for `identity/sso/` is
  read against the generated list before it is applied.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
