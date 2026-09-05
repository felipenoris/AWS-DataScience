# Stage 6c — Networking: three VPCs in Production and one egress for the estate

| | |
|---|---|
| **Status** | not started — **created 2026-09-05** with [6b](stage-06b-development-becomes-staging.md), revised the same day into the action-checklist format and against the AWS documentation (the corrections are listed under "What the documentation changed in this plan"). It builds [D38](../decisions/D38-single-egress-hub.md): a `VPC-Networking` hub in Production carrying the estate's only internet gateway, an explicit HTTP/HTTPS proxy and the VPN endpoint; `VPC-SharedServices` for GitLab, Pages and the runners; `VPC-Workloads` for the production runtime. It also repairs, structurally, the client-plane DNS shadowing of Lessons 40-43 |
| **Prerequisites** | [Stage 3](stage-03-networking.md) (the `vpc` and `vpc-egress` modules, the peering pattern in `production/foundation/peers.tf`, the `[P]`/`[E]` split), [Stage 4](stage-04-vpn.md) (the `wireguard` module and its `[P]` anchors), [6a](stage-06a-unified-studio.md) (the endpoint lists and what a Studio app needs), **[6b](stage-06b-development-becomes-staging.md)** (the account is already `staging`, and step 4.1 there freed `10.40.0.0/16` and re-pointed `CIDRS`) |
| **Consumes** | [D4](../decisions/D04-vpn-wireguard.md), [D5](../decisions/D05-sagemaker-egress.md), [D6](../decisions/D06-dlp-approach.md), [D9](../decisions/D09-az-count.md), [D11](../decisions/D11-lab-lifecycle.md), [D12](../decisions/D12-budget-ceiling.md), [D14](../decisions/D14-supply-chain-account.md), [D15](../decisions/D15-tls-internal.md), [D35](../decisions/D35-sandbox-cardinality.md), [D36](../decisions/D36-internal-pki.md), **[D38](../decisions/D38-single-egress-hub.md)** (written 2026-09-05 — this stage builds it, it does not author it) |
| **Proves** | [INT-05](../integrations.md) and [INT-06](../integrations.md) re-keyed on the hub; [INT-16](../integrations.md)'s closing choice becomes takeable because this stage owns the address it is keyed on; **INT-21** (every account's compute reaching a Production-owned proxy over peering) and **INT-22** (the `awsds.internal` zone × VPC association matrix) |

*Read with [`docs/plan/conventions.md`](../conventions.md) §6 (the target slice tree — the authority when
this file and it disagree), [`docs/NETWORK.md`](../../NETWORK.md) §T (the target topology, re-measured in
this stage's own sittings) and [`docs/plan/runbooks/vpn.md`](../runbooks/vpn.md), whose §S topology this
stage rewrites.*

---

**Objective:** one internet egress for the whole cloud, behind one HTTP/HTTPS proxy, with the VPN client
treated as what it is — a client of the private network, which therefore reaches the internet the same way
every other client does. Three VPCs in Production; five peerings; no NAT gateway anywhere; no default route
in any spoke.

## The premise the whole design rests on, stated once

**VPC peering shares an address, never a path** (Lesson 44). The AWS peering guide's *"Edge to edge routing
through a gateway or private connection"* section says it four times — *"If VPC A has an internet gateway,
resources in VPC B can't use the internet gateway in VPC A"*, the same for *"a NAT device"*, for a VPN or
Direct Connect connection, and for *"a gateway endpoint that provides connectivity to Amazon S3"* — and
adds that *"VPC peering does not support transitive peering relationships"*. Five consequences, none of
them a preference:

1. **The single egress reaches a spoke only as an explicit proxy** — an ENI address inside
   `VPC-Networking` that clients are configured to use. There is no transparent path.
2. **No spoke has a default route at all** — [D5](../decisions/D05-sagemaker-egress.md)'s design B. That is
   what closes the two bypasses design A could not: a raw address and DNS-over-HTTPS to a public resolver
   both need a route the spoke no longer has.
3. **A NAT gateway would serve only the VPC it lives in.** Zero are built; one is priced below as the
   named contingency.
4. **Each VPC keeps its own free S3 and DynamoDB gateway endpoints** — they do not cross a peering, and
   they are the `aws:SourceVpce` anchors INT-05 names.
5. **Interface endpoints stay per VPC and are never centralized in the hub.** Centralizing them would put
   compute-plane private zones back on the resolver the VPN client uses (Lesson 43 at a new address) and
   would make every spoke's AWS call carry the hub's `aws:SourceVpc`, satisfying the personas' VPN-only
   condition from any account.

A sixth limitation from the same page decides pass 2: **"You cannot connect to or query the Amazon DNS
server in a peer VPC."** A spoke resolves at its own `.2` and nowhere else, so every name the spoke must
resolve has to come from a zone **associated with the spoke's own VPC**. The association matrix is the
design, not an afterthought.

**The client plane is not special.** The VPN client sits inside the private network; its internet is the
private network's internet. The enforcement lives on the WireGuard host, where the user cannot revert it:
tunnel packets are forwarded to RFC1918 destinations only, everything else is dropped. A laptop with no
proxy configured reaches the intranet and nothing beyond it.

## What this builds, and in which account

| Object | Slice | Layer | Note |
|---|---|---|---|
| `VPC-SharedServices` **10.30.0.0/16** | `production/foundation/` (exists) | `[P]` | GitLab, Pages, the runners, the build host. **No rebuild**: ids, both peering accepters and the four zone associations survive |
| `VPC-Networking` **10.31.0.0/16** | `production/networking/` (new) | `[P]` | The only IGW; the estate's only internet-facing tier. **Also both hub hosts' `[P]` anchors** — two Elastic IPs, two security groups, the host-key secret, the proxy allow-list parameter |
| `VPC-Workloads` **10.32.0.0/16** | `production/workloads/` (new) | `[P]` | The production SageMaker runtime, MWAA Serverless workers, production jobs |
| WireGuard host | `production/vpn/` (new) | `[D]` | Instance only. Its Elastic IP is **transferred** from Sandbox, so no client `.conf` changes its `Endpoint` |
| Squid host | `production/proxy/` (new) | `[D]` | Instance only. The estate's single egress |
| `awsds.internal` + three child zones + `awsds-pages.internal` | `production/foundation/` and each spoke | `[P]` | With the explicit association matrix (INT-22) |
| Five peerings | requester per spoke, accepter in Production | `[P]` | Networking × 4, SharedServices × Sandbox |
| Interface endpoints | every VPC **except** `VPC-Networking` | `[E]` | Single AZ (D9), private DNS on |
| DNS Firewall | every compute VPC | `[E]` | Re-cut to an intranet-and-AWS list |
| **Zero** NAT gateways | — | — | Priced in §Cost as the contingency |

**Both hosts' `[P]` anchors live in `networking/`, never in the `[D]` slice** — the Stage 4 rule
(`conventions.md` §6): a `make down` that destroyed the `[D]` slice must not release an Elastic IP or the
host key (Lesson 4).

## What the documentation changed in this plan

Read before executing; each is a correction to what the 2026-09-05 draft assumed.

| Was assumed | What the documentation says | Where it lands |
|---|---|---|
| Three VPCs need `name_suffix` for tidy tags | The `vpc` module's **CloudWatch log group** `awsds-<env>-vpc-flow-logs` and the slice's flow-log **IAM role** of the same name are **account-unique** — three VPCs with `env = "prod"` is a hard conflict, not cosmetics | 0.4 |
| `VPN_HOMES` resolves the new home by name | Each row becomes a `terraform_remote_state` read of that account's **`foundation/`** slice; the hub's EIP is in `networking/` | 0.5 |
| MWAA Serverless is the first NAT contingency candidate | AWS documents a **private-routing** MWAA Serverless VPC with *"no route table to a NAT device… nor an internet gateway"*, three interface endpoints (`logs`, `monitoring`, `kms`) and a self-referencing SG. The requirements list that demands a NAT is the **public-routing** shape (Lesson 41 again) | 5.7, and D7/Stage 10 |
| INT-16 fallback (i) is AWS's policy keyed on an address | AWS's `DenyUserAccessFromUnauthorizedVPCs` uses `StringNotEquals` on `aws:SourceVpc`, which **matches when the key is absent** — every browser-origin call. Verbatim, it denies the portal outright | 6.6 |
| The proxy's allow-list is discovered by trial | The SMUS network-isolation guide **enumerates** the portal, IdC and console names that need public internet | 4.7 |
| `NO_PROXY` is `.us-west-2.amazonaws.com` | A blanket suffix sends every endpoint-less AWS service to a route that does not exist — a **timeout** (Lesson 42). Generated per VPC from that VPC's endpoint list, the same call is a proxy **403** | 5.6 |

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply`/`destroy` or any AWS write (the two address-transfer calls included) — run **only after the user authorizes that specific action in chat**, with the SSO user / account / permission set stated first |
| **[user]** | the host-key copy, every device's `.conf`, the tunnel-side measurements, the console acts, git commits and every log entry |
| **[Claude reads, user decides]** / **[Claude and user]** | a measurement Claude takes and a choice only the user can make, in the same sitting — the reading is written down whichever way the choice goes |

## Step numbers are identifiers, not an order

| Pass | What | Sitting | Blocks |
|---|---|---|---|
| **0** | groundwork with no AWS side — module, ranks, vocabulary, gates | any | everything |
| **1** | the three VPCs | any | 2, 3 |
| **2** | `awsds.internal` and the association matrix | any | Stage 7 |
| **3** | the five peerings and every route, from one map | after 1 | 4 |
| **4** | **the cut-over** — the address transfer, both hub hosts, the re-keying | **one sitting, with a blackout** | 5 |
| **5** | the spokes become design B | after 4 | [6d](stage-06d-unified-studio-remainder.md), Stage 7 |
| **6** | the measurements | after 5 | the close |
| **7** | cost, lifecycle, the two operational instruments | after 6 | — |

Passes 0-3 are `[P]` and cost nothing at rest. **Stage 7 waits on passes 1-2**; **Stage 13's public tier**
lands in `VPC-Networking`'s public tier as its second enumerated listener; **6d waits on pass 5**.

---

## To execute

### 0. Prepare the vocabulary and the modules — the groundwork with no AWS side

**Action:** teach the tooling about three VPCs in one account, before any folder exists. **Why:**
`layers.py` refuses a slice kind it has no rank for, `CIDRS` holds one address per account, and two
resources in the `vpc` module are account-unique. **Explanation:** none of this is visible in a `plan`, and
one of the four (0.4) is a hard create-time conflict rather than a naming preference — so it comes first.

- **0.1 — [Claude] Confirm what is already written**, and do not re-author it: `D38`, `Lesson 44`, `INT-21`,
  `INT-22`, Recipe E and Recipe F all landed on 2026-09-05. What this pass adds is code, not prose.
- **0.2 — [Claude] Extend the address vocabulary**: `scripts/tfhygiene/backend.py` gains a
  per-**(account, VPC)** table — `production-shared` 10.30.0.0/16, `production-networking` 10.31.0.0/16,
  `production-workloads` 10.32.0.0/16 — beside the per-account `CIDRS` that already carries
  `sandbox` 10.20.0.0/16 and `staging` 10.50.0.0/16 (6b step 4.1 put it there). **`10.40.0.0/16` is free**
  and stays unallocated; `10.60.0.0/16` is reserved for the `shared` account D38's trigger names;
  `10.16.0.0/13` stays the Sandbox supernet and `10.90.0.0/24` the WireGuard client range.
- **0.3 — [Claude] Add the slice ranks before any folder exists**: `RANKS` in `scripts/tfhygiene/layers.py`
  gains `networking` (21), `workloads` (23) and `proxy` (41). Rank first, folder second, same commit
  (Recipe C). The order is load-bearing: `up` ascends and `down` descends, so `proxy` at 41 comes up before
  any `egress` (50) and goes down after it — which is what makes a spoke's package path exist for the whole
  life of an `[E]` session.
- **0.4 — [Claude] Bump `terraform-modules/vpc` to v0.2.0 with a `name_suffix`**, and carry it into the two
  names that are **account-unique, not VPC-unique**: `aws_cloudwatch_log_group.flow_logs`
  (`awsds-<env>-vpc-flow-logs`) and, in the calling slice, the flow-log IAM role of the same name whose
  policy is scoped to exactly that group. Security-group *names* are unique per VPC and would not collide,
  but their `Name` tags would, and `./aws/networking.py` reads tags — so the suffix reaches every `Name` as
  well (`awsds-prod-shared-*`, `awsds-prod-networking-*`, `awsds-prod-workloads-*`). Two commits, one tag
  (the runbook's order). **Note in the plan review that the existing VPC's tags change in place while its
  security groups are replaced.**
- **0.5 — [Claude] Give `VPN_HOMES` a slice field**: each row is consumed by `identity/sso/` and
  `data-governance/data/` as a `terraform_remote_state` read of that account's **`foundation/`**. The hub's
  Elastic IP, VPC id and gateway-endpoint id live in `production/networking/`, so the row becomes
  `("production", "networking")` and both consumers read the slice the row names. Without this the
  re-keying of 4.9 reads an empty state and `DenyControlPlaneOffVpn` denies every call from every network —
  the failure `permission-sets.tf`'s precondition already has an error message for.
- **0.6 — [Claude] Teach the peering pattern about three VPCs**: `production/foundation/peers.tf` finds a
  peer by the single tag `awsds-<env>-vpc`; that lookup becomes per-VPC and the peering map moves into
  `backend.py`, so both sides of every peering are generated from one list (Lesson 14).
- **0.7 — [Claude] Fix the documentation gate**: `scripts/check-network-doc.py` rule B recomputes subnet
  tiers from **one** CIDR per account; it now reads the per-VPC table. `docs/NETWORK.md` §2.1 gains every
  new network-bearing slice in the same commit.

### 1. Build the three VPCs — the address plan and the tiers that carry the new rules

**Action:** re-label the existing Production VPC and create two more. **Why:** the hub needs a public tier
that is the estate's only internet-facing tier, and nothing can be peered to a VPC that does not exist.
**Explanation:** nothing here costs money at rest, and the re-label is the least-churn choice — GitLab was
always planned in 10.30's private tier, both peering accepters live there, and the four zone associations
point at it.

- **1.1 — [Claude⚡] Re-label the existing VPC as `VPC-SharedServices`**: apply the `name_suffix` to
  `production/foundation/` and read the plan — tags in place, security groups replaced, **VPC and gateway
  endpoint ids unchanged**. Any id in the replacement list stops the step.
- **1.2 — [Claude⚡] Create `production/networking/`**: VPC 10.31.0.0/16 from the same module, both AZs by
  `zone_id` (D9), IGW attached, the public tier carrying the estate's only `0.0.0.0/0 → igw` route, S3 and
  DynamoDB gateway endpoints on every route table, flow logs on.
- **1.3 — [Claude⚡] Create `production/workloads/`**: VPC 10.32.0.0/16, same shape, **no IGW route in any
  route table**. The module still creates the gateway (free, unused); the absence of the route is what
  makes the tier private.
- **1.4 — [Claude] Enumerate the ingress tier**: write into `docs/AWS_STATE.md` the invariant
  *"internet-originated traffic terminates only in `VPC-Networking`'s public tier, and every listener there
  is enumerated"* — today the WireGuard host's UDP/51820; Stage 13's public ALB becomes the second row. A
  world-open rule anywhere else is a finding.
- **1.5 — [Claude] Write the no-public-address gate**: extend `./aws/networking.py` with a check that fails
  on any IGW route, public IP or world-open security-group rule outside that tier, in **any** account.

### 2. Build the internal DNS — `awsds.internal` and the association matrix

**Action:** create the apex, the three child zones and the second Pages apex, and associate each into the
VPCs that must resolve it. **Why:** private zones do not delegate, overlapping zones resolve by most-
specific match, a VPC cannot query a peer's resolver, and a VPC associated with a matching zone that holds
no record gets **NXDOMAIN** rather than a public answer. **Explanation:** a missing association therefore
produces a failure indistinguishable from a name that does not exist — which is why the matrix is written
down (INT-22) and read by a check, since nothing derives it.

- **2.1 — [Claude⚡] Create the apex** `awsds.internal`, owned by `production/foundation/` (the services
  named directly under it live there). Records: `gitlab.awsds.internal`; `proxy.awsds.internal` and
  `vpn.awsds.internal` are written by pass 4 from the two hosts' **private** addresses.
- **2.2 — [Claude⚡] Create the three child zones**: `sandbox.awsds.internal` (owned by Sandbox),
  `staging.awsds.internal` (owned by the renamed account), `prod.awsds.internal` (owned by
  `production/workloads/`).
- **2.3 — [Claude⚡] Keep Pages on its own apex**: `awsds-pages.internal`, unchanged in intent from D36 — a
  sibling under the shared apex would weaken the cookie-scope separation the two-apex choice exists for.
- **2.4 — [Claude] Write the association matrix** into `docs/NETWORK.md` §10, enforced by a new
  `./aws/networking.py` check **`NT-12`** (the matrix as documented equals the matrix as deployed):

  | Zone | Associated with |
  |---|---|
  | `awsds.internal` | all five VPCs |
  | `sandbox.awsds.internal` | Sandbox, `VPC-Networking` |
  | `staging.awsds.internal` | Staging, `VPC-Networking` |
  | `prod.awsds.internal` | `VPC-Workloads`, `VPC-SharedServices`, `VPC-Networking` |
  | `awsds-pages.internal` | `VPC-SharedServices`, `VPC-Networking` |

- **2.5 — [Claude⚡] Reverse the authorization direction**: the spoke-owned child zones authorize
  **Production's `VPC-Networking`**. AWS's procedure is exact and has no console path: the **zone owner**
  runs `create-vpc-association-authorization` (one request **per VPC**), then the **VPC owner** runs
  `associate-vpc-with-hosted-zone`. This is the opposite of today's choreography, where Production
  authorizes and the spokes associate. **AWS recommends deleting the authorization afterwards; this project
  keeps it in Terraform state** (`aws_route53_vpc_association_authorization`, as `peers.tf` keeps the
  peering pair) so the destroy order stays expressible — record the divergence and its reason in
  `NETWORK.md` §10 rather than leaving it to look like an oversight.
- **2.6 — [Claude⚡] Retire the old zones, after pass 6 measures the new ones**: `sandbox.internal`,
  `prod.internal` and `pages.internal` with their associations. Zones cannot be renamed, so this is
  create-then-retire and the two families coexist for one sitting.

### 3. Build the five peerings — and generate every route from one map

**Action:** declare the peering matrix once and generate both sides from it. **Why:** the isolation rule in
the user's brief — Interactive and Workloads never talk — is enforced by the *absence* of a peering, the
cheapest control in the design. **Explanation:** adding peerings "because they might be needed" spends it;
deploys are AWS API calls and need no L3 path into a target VPC.

- **3.1 — [Claude] Declare the matrix** in `backend.py`:

  | Requester | Accepter | Why |
  |---|---|---|
  | Sandbox | `VPC-Networking` | VPN reach, the proxy |
  | Staging | `VPC-Networking` | the proxy |
  | `VPC-Workloads` | `VPC-Networking` | the proxy |
  | `VPC-SharedServices` | `VPC-Networking` | the proxy, and the VPN's reach to GitLab |
  | Sandbox | `VPC-SharedServices` | `git clone` from a notebook (INT-09 re-homed), the laptop to GitLab and Pages |

  **Not built, and the omission is the control:** Sandbox ↔ Staging, Sandbox ↔ `VPC-Workloads`,
  `VPC-SharedServices` ↔ Staging, `VPC-SharedServices` ↔ `VPC-Workloads`.
- **3.2 — [Claude] Record why the last two are absent, because the intuition says otherwise**: *deployment
  is an API act.* The runner in `VPC-SharedServices` assumes a role across the account boundary and calls
  SageMaker, CloudFormation and S3; artifacts travel as ECR images, CodeArtifact packages and S3 objects,
  each reached through an endpoint in the target's own VPC. **Nothing in a deployment target clones a
  repository** — the image carries the code (D28), so a runtime `git clone` there is a contract violation to
  catch rather than a path to provide. Keeping them absent costs one later change; building them costs
  standing L3 reach from the host that executes repository-supplied build code into both deployment
  targets — the blast radius D14 accepted, widened (Lesson 2).
- **3.3 — [Claude] Name the trigger, so it is recognised rather than rediscovered**: a peering to a
  deployment target is added when a **shared service is consumed at runtime** rather than at deploy time.
  Candidates, none of which exists today: a package mirror or registry proxy on an instance (as opposed to
  ECR and CodeArtifact, which are endpoints), a metrics or log collector that is not CloudWatch, an
  internal secrets or configuration service, a certificate-status endpoint. **The internal CA is not one** —
  D36 issues no CRL and runs no OCSP responder, by decision. When one appears, prefer a regional service or
  an endpoint; the peering is the last resort, generated from this same map.
- **3.4 — [Claude⚡] Generate and apply both sides**: the accepter stays in Production (`foundation/` for
  SharedServices, `networking/` for the hub), with subnet-scoped routes on **both** sides, applied
  accepter-last as the existing pattern does.
- **3.5 — [Claude⚡] Route the tunnel's return path**: every spoke private route table carries a route to
  `VPC-Networking`'s **public** tier (where both hosts live) as well as to its private tier.
- **3.6 — [Claude] Keep `10.90.0.0/24` out of every table but one**: the WireGuard client range is
  masqueraded today and stays invisible to the spokes. The **one** exception is inside `VPC-Networking`,
  added at 4.7. Re-cut `./aws/networking.py` `NT-4` from *"no route to 10.90/24"* to *"no route to
  10.90/24 outside `VPC-Networking`"*.
- **3.7 — [Claude] Add the two-way route check**: new **`NT-11`** — every active peering has a route on
  both sides in every affected route table. The reference implementation this project keeps as a comparison
  has exactly this defect (an attachment with no route), which is why the check exists.

### 4. Move the VPN and build the proxy — the cut-over, and the only blackout in the stage

**Action:** transfer the Elastic IP, stand up both hub hosts, and re-key every VPN-only condition onto the
proxy's address. **Why:** the estate's entry point and its exit point both move accounts. **Explanation:**
two hosts rather than one — the WireGuard host receives untrusted UDP from the internet and the Squid host
parses untrusted internet responses, so separating them keeps a compromise of either off the other. The
address transfer is what keeps every client's `Endpoint` line unchanged.

- **4.1 — [Claude⚡] Apply the `[P]` anchors in `production/networking/`**: the same output names the
  Sandbox slice exports (`wireguard_eip_public_ip`, `vpc_id`, `s3_gateway_endpoint_id`,
  `wireguard_security_group_id`, `wireguard_host_key_secret_arn`) plus the proxy's
  (`proxy_eip_public_ip`, `proxy_security_group_id`, `proxy_allowlist_parameter_name`). Both security
  groups are new — WireGuard UDP/51820 world-open and nothing else; the proxy TCP/3128 **from the spoke and
  tunnel CIDRs only** — so pass 1.4's ingress invariant still reads one listener. The host-key secret is
  new and **empty**.
- **4.2 — [Claude] Run the transfer preflight**: new read-only instrument **`./aws/eip-transfer.py`**,
  which answers the four documented refusals *before* either write call — the address must be
  **disassociated** (`InvalidTransfer.AddressAssociated` is raised at accept time, not at enable time), must
  carry **no reverse-DNS record** (`InvalidTransfer.AddressCustomPtrSet`), must not come from a BYOIP,
  IPAM or CoIP pool, and the destination account must be under its Elastic IP quota
  (`AddressLimitExceeded`; the default is five per Region). It prints the two write commands rather than
  running them.
- **4.3 — [user] Copy the host key by hand, never through Terraform or Claude**: `get-secret-value` in
  Sandbox → `put-secret-value` in Production. The key is what keeps every client's public key valid; a new
  key means re-issuing every peer.
- **4.4 — [Claude⚡] Disassociate the address**: destroy `sandbox/vpn/`'s `aws_eip_association` on its own,
  with the plan written first (`runbooks/vpn.md` §8 — `make down` stops the host but leaves the address
  associated).
- **4.5 — [Claude⚡] Transfer the address**, one authorization per call:

  ```bash
  aws ec2 enable-address-transfer --allocation-id <the Sandbox allocation> --transfer-account-id <Production>
  aws ec2 accept-address-transfer --address <the address>
  ```

  Same Region only, no charge, **seven days** to accept, and **AWS notifies nobody** — the two calls are one
  sitting. **Tags are reset by the transfer**, so the address arrives untagged and Terraform re-applies the
  project tag set on the next apply. Read `describe-address-transfers` on both sides (the source can see an
  accepted transfer for 14 days) and `describe-addresses` in Production: **whether the allocation id
  survives is not documented**, and the reading decides the next step's `import` id.
- **4.6 — [Claude⚡] Bring the address into state on both sides**: an `import {}` block in
  `production/networking/` with the allocation id 4.5 measured, and in `sandbox/foundation/` the resource
  block replaced by

  ```hcl
  removed {
    from = aws_eip.wireguard
    lifecycle {
      destroy = false
    }
  }
  ```

  so neither side tries to create or release it (Terraform ≥ 1.7; this project runs 1.15.8).
- **4.7 — [Claude⚡] Build the WireGuard host**: `production/vpn/` `[D]`, in `VPC-Networking`'s public tier,
  from the existing module at **v0.5.0** with three changes: `vpc_nat_cidrs` is **removed** (the
  isolated-tier NAT job dies with the buildbox's move, 5.8), the `PostUp` chain forwards tunnel packets
  **only to RFC1918 destinations** and drops the rest, and it stops masquerading traffic bound for the
  proxy so Squid sees `10.90.0.x`. Add `10.90.0.0/24 → the WireGuard host's ENI` to the hub's public-tier
  route table — the single exception 3.6 names, in the same VPC, which is what gives the access log a
  per-device address without any logging change.
- **4.8 — [Claude⚡] Build the proxy**: `production/proxy/` `[D]`, a second host in the same public tier.
  Squid is in the Amazon Linux 2023 repositories (`dnf install -y squid`) and needs no third-party repo.
  The configuration, **in this order**:

  1. `acl to_private dst 10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 100.64.0.0/10` +
     `http_access deny to_private`, **before every allow** — without it the proxy is an L7 bridge between
     VPCs that peering deliberately keeps apart. `dst` (not `dstdomain`) also catches a public name that
     resolves to a private address.
  2. `acl SSL_ports port 443`, `acl Safe_ports port 80 443`, `http_access deny !Safe_ports`,
     `http_access deny CONNECT !SSL_ports`.
  3. Source-scoped allow-lists, **one per plane** (4.9).
  4. `http_access deny all`, last — so an unlisted name is a fast, named 403 rather than a timeout.

- **4.9 — [Claude] Author the two filters the objectives require, as source-scoped lists**: an
  explicit-proxy client never resolves an internet name, so a per-VPC DNS firewall can no longer see one and
  **both** filters live here.
  - **The tunnel range `10.90.0.0/24` carries the institutional web filter** — what a person on a company
    laptop may reach. Seed it from the SMUS network-isolation guide's own tables rather than by trial: the
    portal's asset and client-API families, the IAM Identity Center sign-in family, and the console
    families it enumerates.
  - **The Sandbox CIDR carries SageMaker's stricter list** — today's DNS Firewall allow-list moved
    verbatim, minus its wildcard and minus the portal families, which belong to the tunnel.
  - **The SharedServices CIDR carries the build hosts' package sources**; the Workloads CIDR is empty by
    default. One list per source is what keeps the two filters two: a name a person may reach is not
    thereby reachable from a notebook.
- **4.10 — [Claude] Keep the configuration out of the host, and give it a reload path**: the allow-lists are
  `[P]` data in an SSM parameter rendered at boot, never state that exists only on a `[D]` disk (Lesson 4).
  A parameter change reaches the running host through an **SSM State Manager association** on a
  `rate(30 minutes)` schedule that re-renders and runs `squid -k reconfigure` — so a list edit needs no
  write API from the laptop, no host replacement, and no 30-second estate-wide outage. `./aws/proxy.py`
  (7.3) diffs running against committed, which is what makes the association's silence readable.
- **4.11 — [Claude⚡] Ship the access log**: the CloudWatch agent to a `[P]` log group in Production,
  KMS-encrypted, with the proxy's role holding `CreateLogStream`/`PutLogEvents` and no delete; an export to
  Log Archive so the author of the allow-list does not own its record (Lesson 18). Fields: time, source,
  CONNECT host, status, bytes in and out. This is Stage 11's egress evidence.
- **4.12 — [Claude⚡] Re-key the VPN-only conditions, as a union first**: a laptop's control-plane call now
  exits through Squid, so `VPN_HOMES` yields `aws:SourceIp` = the **proxy's** EIP, `aws:SourceVpc` =
  `VPC-Networking`, and `trusted_vpce_ids` gains `VPC-Networking`'s S3 gateway endpoint id (S3 from the
  proxy still leaves through that gateway, so the call presents a VPC and a VPCE rather than the proxy's
  public address — both branches of `DenyControlPlaneOffVpn` are load-bearing, and that is why the
  statement already pairs `NotIpAddress` with `StringNotEqualsIfExists`). **Apply the list containing BOTH
  the old WireGuard EIP and the new proxy EIP, measure pass 6, and trim in a second apply** — a single
  cut-over apply is one typo away from locking out all six personas. Apply `identity/sso/` and
  `data-governance/data/` as `InfrastructureAccess`, which carries no VPN-only deny by decision (open
  question 17's recovery path). Read the Sandbox lake's and the projects bucket's policies in the same
  sitting: any `aws:SourceVpce` branch there needs the hub's gateway id too.
- **4.13 — [Claude⚡] Destroy the old home, last**: `sandbox/vpn/` and the VPN anchors in
  `sandbox/foundation/`, once pass 6's readings pass. `VP-2` (no orphan allocation) is the closing check.

### 5. Turn the spokes into design B — no NAT, no default route, and a DNS firewall with a new job

**Action:** destroy both NAT gateways, complete each VPC's endpoint set, and re-purpose the DNS firewall.
**Why:** with the proxy reachable, the per-account NAT gateways are the last transparent path and the only
metered thing in the egress slices the design no longer wants. **Explanation:** removing them is also what
makes the proxy's allow-list the single filter it is supposed to be — and it is what makes the SMUS
network-isolation page's required endpoint list finally apply, because its premise (no public egress)
becomes true.

- **5.1 — [Claude⚡] Destroy both NAT gateways**: `egress_mode = "B"` in Sandbox and Staging; the private
  route tables lose their `0.0.0.0/0` entirely. `vpc-egress` **v0.5.0** drops the NAT half (and its
  `nat_public_subnet_id` input) rather than keeping dead code.
- **5.2 — [Claude⚡] Complete the required endpoint set**: Sandbox re-adds **`datazone`** — removed on
  2026-08-25 only because its private zone shadowed a client-plane name, which cannot happen now — and
  gains `ec2`, `ec2messages`, `secretsmanager`, `ssm`, `ssmmessages` and `q`. **Measure rather than copy**:
  six of those names have never existed here, and `codewhisperer` is `us-east-1`-only, so it is not an
  endpoint this Region can hold at all ([6d](stage-06d-unified-studio-remainder.md) step 3.5 decides it).
- **5.3 — [Claude reads, user decides] Close the gap between the required table and the ENABLED
  blueprints**: the guide's **optional** table is keyed to *"projects that include blueprints using the
  services listed below"*, and this estate enables two of them in category 1 — the six `AmazonBedrock*`
  blueprints (`bedrock-agent`, `bedrock-agent-runtime`, `bedrock-runtime`) and `EmrServerless`
  (`emr-serverless`, `emr-serverless-services.livy`, `emr-serverless-services.sessions`,
  `emr-serverless.dashboard`, `emr-dashboard`, `elasticmapreduce`, `elasticmapreduce-services`). Under
  design A the NAT covered this silently; **with no default route, a project that uses either blueprint has
  no path at all**. That is real money against D12 while those endpoints are up, so it is a decision, not a
  list edit. Three shapes: (a) add them to `egress/`; (b) add them behind a per-session flag, since a
  Bedrock or Spark session is not every session; (c) move the blueprints out of category 1 — the honest
  answer if nobody uses them, because an enabled blueprint whose endpoints are missing is a feature that
  exists in the portal and fails on first use. **Recommended: (c) for `EmrServerless` until a workload asks
  for Spark, (b) for Bedrock.** Whatever is chosen, the enabled-blueprint list and the endpoint list move
  in the same commit, and the check that compares them (`US-3` reads the first, `./aws/egress.py` the
  second, nothing compares them today) is this step's other deliverable.
- **5.4 — [Claude reads, user decides] Settle the `sagemaker.runtime` AZ question, which D9's single-AZ
  rule collides with**: the SageMaker AI guide is explicit that the interface endpoint *"must be activated
  in the Availability Zone of your client… Otherwise, you may see DNS failures"*, and says it of the
  **runtime** endpoint by name. Our metered endpoints live in **one** AZ while a project's apps may land in
  either private subnet, so an app in `usw2-az2` invoking a model endpoint fails as a *resolution* error
  rather than as the cross-AZ cent-per-gigabyte D9 accepted. Three ways out, in order of preference: pin
  the SMUS app subnets to the endpoint's AZ (free — the blueprint takes a subnet list); put **only**
  `sagemaker.runtime` in both AZs; or accept it and let the first `az2` invocation be the measurement.
  **Recommended: pin the subnets**, and measure it at [6d](stage-06d-unified-studio-remainder.md) step 3
  either way.
- **5.5 — [Claude⚡] Give every instance-bearing spoke its SSM path**: `ssm`, `ssmmessages` and
  `ec2messages` in Sandbox, `VPC-SharedServices` and `VPC-Workloads`. Session Manager does not work through
  an HTTPS proxy listener, and the shell that reads the proxy's own log must not depend on the proxy
  (Lesson 24). `VPC-Networking`'s two hosts reach SSM through the IGW directly.
- **5.6 — [Claude] Generate `NO_PROXY` per VPC, from that VPC's endpoint list**: not a blanket
  `.us-west-2.amazonaws.com`. A blanket suffix tells the client "reach every AWS service directly", and a
  service with no endpoint then has no route at all — a timeout with no message (Lesson 42). Generated from
  the list the `egress/` slice already declares, the same call is a proxy **403 naming the host**, which is
  a finding rather than a hang. The generated list also carries `169.254.169.254`, `169.254.170.2`,
  `localhost`, `.awsds.internal` and the RFC1918 ranges (S3 and DynamoDB ride the gateway prefix lists).
  **Never an `ENV HTTP_PROXY` in `images/base`** — every application image inherits from it and runs as a
  Production job behind endpoints, where a wrong `NO_PROXY` would send S3 and STS out through the proxy as
  a public address. Build time is a BuildKit `--build-arg`; runtime in a Studio space is
  `ContainerEnvironmentVariables` on the app image configuration, or a JupyterLab lifecycle configuration —
  which for SMUS domains **must be attached in the console**, the CLI path being documented as not
  supported.
- **5.7 — [Claude] Re-cut the DNS Firewall**: it stays in every **compute** VPC and its allow-list shrinks
  to `*.amazonaws.com`, `*.api.aws`, `.awsds.internal` and the proxy's name; the `BLOCK`-NXDOMAIN `*` rule
  stays. Its job is no longer filtering the internet but closing the recursive resolver as an exfiltration
  channel. `VPC-Networking` carries **none** — the proxy has to resolve. `EXC-04`, `EXC-05` and `EXC-06`
  close with the old list, and **`EXC-05`'s whole failure mode retires with them**: Squid matches the
  *requested* hostname, so a CDN that stops flattening its chain can no longer turn an allowed name into a
  block that blames the wrong entry. Re-aim `./aws/dns-allowlist.py` at the Squid lists — `DN-1`..`DN-4`
  become questions about the proxy's lists, read through SSM the way `vpn.py --on-host` reads the VPN host.
- **5.8 — [Claude⚡] Move the build host**: `sandbox/buildbox/` is destroyed and re-created as
  `production/buildbox/` in `VPC-SharedServices` beside the runners, with the docker daemon and the SSM
  agent proxy-configured. It is `[E]` and holds no state that survives a session (`buildbox.md` §S), so
  this is a destroy-and-create, **not** Recipe E. Its only egress today is a route to the WireGuard host's
  ENI, and a route target cannot live in another VPC. The `vpc_nat_cidrs` input, the isolated-tier
  security-group rule and the *must not coexist with `probes/`* rule all die in the same commit;
  `runbooks/buildbox.md` is rewritten in the same sitting.
- **5.9 — [Claude] Re-state the NAT contingency, with its first candidate removed**: a NAT gateway is built
  **only** for a named service that needs the internet and cannot be told about a proxy, in **that
  service's own VPC**, with its own cost row and a trigger to remove it. **MWAA Serverless is no longer that
  candidate**: AWS documents a private-routing shape whose subnets *"must not have a route table to a NAT
  device… nor an internet gateway"*, with interface endpoints for `logs`, `monitoring` and `kms`, a
  self-referencing security group and two private subnets in two AZs. The requirements list that demands
  two NAT gateways is the **public-routing** shape of the same page (Lesson 41). Stage 10 builds the
  private one; **no candidate for the contingency is named today**, and that is the honest state.

### 6. Measure the whole thing — the readings that close the stage

**Action:** take six readings, each with two distinguishable outcomes. **Why:** every claim in this stage is
about a path, and a path is measured, never read off a diagram. **Explanation:** three of these also close
obligations older than the stage.

- **6.1 — [user] Measure the tunnel from a client**: the `.conf` changes **only** its `DNS =` line (to
  `VPC-Networking`'s `.2`); the `Endpoint` is unchanged because the address moved with it. Then
  `runbooks/vpn.md` §C's three checks, plus a fourth: `curl https://1.1.1.1` **times out**, and
  `curl -x proxy.awsds.internal:3128 https://checkip.amazonaws.com` prints the **proxy's** EIP.
- **6.2 — [user] Close the shadowing**: from the tunnel, `dig agent.datazone.us-west-2.api.aws` and
  `dig <domain-id>.studio.us-west-2.sagemaker.aws` return **public** addresses, and the SMUS portal opens
  with **no** Chrome Local Network Access grant. That is Lesson 43's repair and the reading that retires the
  interim.
- **6.3 — [Claude] Prove the isolation over SSM**: from a Sandbox probe,
  `curl -x proxy:3128 https://<a Workloads private address>` returns the proxy's **403** while
  `https://pypi.org` returns 200; the mirror from a Workloads probe. Two distinguishable outputs, which is
  what makes it a verification.
- **6.4 — [user] Prove the drop rule**: with the laptop's proxy setting removed, no internet is reachable
  and `gitlab.awsds.internal` still is.
- **6.5 — [Claude and user] Re-measure the vending path**: `s3-read-write` from the laptop, and
  `runbooks/sandbox-lake.md` §T's laptop half, both from the new tunnel, with the CloudTrail
  `sourceIPAddress` and `vpcEndpointId` pair read for each call. This is the proof that 4.12's re-keying was
  complete — and the gate for trimming the union.
- **6.6 — [user] Take INT-16's closing choice**: fallback (i) versus recorded acceptance. **If (i):
  do not copy AWS's example verbatim.** Its `StringNotEquals` on `aws:SourceVpc` matches whenever the key is
  **absent**, which is every browser-origin call — under this design the hub holds no interface endpoint, so
  the portal's calls carry the proxy's public address and no `aws:SourceVpc` at all, and the documented
  policy would deny the portal outright. Author it in `policies-shared.tf`'s shape instead: `NotIpAddress`
  on `aws:SourceIp` (the proxy's EIP) **and** `StringNotEqualsIfExists` on `aws:SourceVpc`, keeping AWS's
  `aws:userid` `*:user-*` and `aws:ViaAWSService` carve-outs. The address is now stable and owned by this
  stage, which is what the choice was waiting for.
- **6.7 — [Claude] Re-measure the documents, same sitting**: `docs/NETWORK.md` rewritten **from the
  readings**, not from this file (its §T becomes §0-§14); `./scripts/check-network-doc.py` green;
  `./aws/networking.py` and `./aws/egress.py` snapshots regenerated; `docs/AWS_STATE.md`'s §C rows, the VPN
  row and the DNS rows restated.

### 7. Close the stage — cost, lifecycle, and the two operational instruments

**Action:** split the hub's lifecycle out of `make up`, turn a stopped hub into an error, and restate the
cost from measurements. **Why:** the hub makes one account's `[D]` host a dependency of every other
account's session, and `make up`/`down` has no concept of that. **Explanation:** left alone, a stopped hub
host is a blackhole rather than an error — the failure mode `buildbox.md` documents for one tier, now
estate-wide (INT-21's availability cost).

- **7.1 — [Claude] Split the hub's lifecycle**: `make hub-up` / `make hub-down`, over a new
  `./scripts/slices.py up --env production --only vpn,proxy`, so a Sandbox session starts the two hub hosts
  **without** starting GitLab or Production's `[E]` endpoints.
- **7.2 — [Claude] Turn the blackhole into an error**: `make up ENV=<spoke>` reads the hub hosts' state
  through `./aws/vpn.py` and **refuses**, naming the stopped host, when either is down.
- **7.3 — [Claude] Write the proxy instrument**: `./aws/proxy.py`, read-only by default with an
  `--on-host` flag on the `vpn.py` pattern. Checks: the security group admits only the spoke and tunnel
  CIDRs (`PX-1`); no `http_access allow` precedes the private-destination deny (`PX-2`); the running
  allow-list equals the committed one (`PX-3`, over SSM Run Command); the access log group exists with its
  Log Archive export (`PX-4`); the EIP is the one `identity/sso/` names (`PX-5`).
- **7.4 — [Claude] Restate the cost, measured before written** (Lesson 6): add the rows to
  `docs/PRICING.md` first — Transit Gateway per attachment-hour plus per GB (the number that records why
  peering was chosen), the Route 53 Resolver endpoint per ENI (which ruled out the forwarding-rule shape of
  open question 23), the Squid host's instance rate, and MWAA Serverless per task-hour — then rewrite
  `docs/plan/cost-model.md`'s hourly table on the zero-NAT basis. Correct `architecture.md` §4.3a's proxy
  figure against the measured rate, and reconcile PRICING with the cost model on peering (charged
  **cross-AZ** only).

---

## Deliverables

- `production/{networking,workloads}/` and the re-labelled `production/foundation/` — three VPCs, one IGW.
- `production/vpn/` and `production/proxy/`, two `[D]` instances over `[P]` anchors that live in
  `networking/`, with two Elastic IPs, one of them transferred rather than allocated.
- Five peerings with routes on both sides, generated from one map.
- `awsds.internal` + three child zones + `awsds-pages.internal`, with the association matrix in
  `NETWORK.md` §10 and `NT-12` reading it.
- Zero NAT gateways, zero default routes outside `VPC-Networking`, and a DNS firewall in every compute VPC
  with an intranet-only list.
- `./aws/proxy.py`, `./aws/eip-transfer.py`, `make hub-up`/`hub-down`, and the spoke guard.

## Validation

- `./aws/networking.py`: `NT-3`/`NT-6` re-cut (no route or peering between an Interactive VPC and a
  Workloads or Staging VPC), `NT-4` (no `10.90.0.0/24` route outside the hub), `NT-10` (the hub seizes no
  client-plane name), `NT-11` (every peering routed both ways), `NT-12` (the zone matrix as documented) —
  all `pass`.
- `./aws/egress.py`: no NAT gateway in any account; every private route table without a default route.
- `./aws/proxy.py`: `PX-1`..`PX-5` pass.
- `./aws/vpn.py`: `VP-1`..`VP-9` from the new home, `VP-2` with no orphan allocation, `VP-3` still one
  world-open rule in the estate.
- The six readings of pass 6, each with its two distinguishable outcomes.

## Cost

Measured rates, `us-west-2` (PRICING §7/§8 after 7.4's additions): the design **removes two NAT gateways**
(−0.100/h while a session runs, plus their per-GB processing) and **adds one Elastic IP** (the proxy's) and
one to two private hosted zones. The two `[D]` hosts bill only while running. Interface endpoints stay
per-VPC, single AZ — `VPC-Networking` carries none. Peering is free within an AZ and charged each way
across one, so pinning both hosts and the endpoint sets to `usw2-az1` keeps the common path free. **A
standing NAT gateway is the largest single line the design avoids**, which is why it is a contingency and
not a component. Every figure above is written into `docs/PRICING.md` from a measurement before it is used
in the cost model.

## Decisions due while executing

1. **The optional-endpoint trade for the two enabled blueprint families** (5.3) — (a) always up, (b) per
   session, or (c) disable the blueprint. Recommended (c) for `EmrServerless`, (b) for Bedrock.
2. **The `sagemaker.runtime` AZ answer** (5.4) — pin the subnets, duplicate one endpoint, or accept.
   Recommended: pin.
3. **INT-16's closing choice** (6.6) — fallback (i) in this estate's condition shape, or recorded
   acceptance.

## Verifications to answer while executing

1. Does the allocation id survive the address transfer? (4.5 — not documented; it decides 4.6's import.)
2. Does Session Manager reach both hub hosts through the IGW with no interface endpoint? (5.5.)
3. Does the SMUS portal open with no browser grant once the client resolves in the hub? (6.2 — Lesson 43.)
4. Which door does a laptop's S3 call take after the re-keying — the hub's gateway endpoint, or the proxy's
   public address? (6.5, and it decides whether `trusted_vpce_ids` is complete.)

## Risks

- **The address transfer fails or the allocation id changes.** Mitigated by 4.2's preflight, by
  disassociating first, and by the `import`/`removed` pair. If the transfer is refused outright, the
  fallback is a new allocation and a new `Endpoint` line in every `.conf` — a client-side edit, not a
  redesign.
- **A re-keying that locks every persona out.** Mitigated by 4.12's union-then-trim, by
  `InfrastructureAccess` carrying no VPN-only deny, and by reading the `identity/sso/` plan against the
  generated list before applying it.
- **The blackout window.** Between the disassociation and the new host coming up, the tunnel, the buildbox,
  the sandbox lake, `s3-read-write` and the portal are unavailable. One sitting, planned, with both
  accounts' `[P]` anchors already applied.
- **A service that cannot use a proxy is discovered late.** Named as the per-VPC NAT contingency (5.9),
  with no candidate today.
- **One stopped hub host takes every account's internet with it.** That is INT-21's new availability cost;
  7.1 and 7.2 turn it from a blackhole into a refusal that names the host.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
