# Stage 6c — Networking: three VPCs in Production and one egress for the estate

| | |
|---|---|
| **Status** | **IN PROGRESS — passes 0 and 1 DONE 2026-09-06**, [logged](../../log/log-stage-06c-networking-hub.md). The three Production VPCs exist: `foundation/` re-labelled **VPC-SharedServices**, plus **VPC-Networking** (10.31) and **VPC-Workloads** (10.32), with `workloads-egress/` written and applying nothing. **Two module bumps, and each was forced by a capability its step did not enumerate** — `vpc-v0.2.0`'s `name_suffix` and `vpc-v0.3.1`'s `public_internet_route`; `vpc-v0.3.0` is **abandoned** on origin, tagged onto the wrong commit by a failed-and-swallowed `git commit`. **0.2 replaced `CIDRS` rather than sitting beside it** (no reader wanted a per-account answer); **0.4a is deferred to 5.1** because the step contradicts itself; **0.6 lands with 3.1**. **Three checks are corrected before being written** — 1.5, 2.4's `NT-12` and 3.7's `NT-11` would each be red for passes at a time as specified, which is 6b's `DT-8` recurring. **Created 2026-09-05**; it builds [D38](../decisions/D38-single-egress-hub.md) and repairs the client-plane DNS shadowing of Lessons 40-43 |
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
| Interface endpoints | every VPC **except** `VPC-Networking` | `[E]` | Single AZ (D9), private DNS on. **One `egress/`-shaped slice per VPC**: `sandbox/egress/`, `staging/egress/`, `production/egress/` (SharedServices) and the **new `production/workloads-egress/`** — a second Production VPC needing endpoints needs a second slice, because a slice reads one `foundation/` |
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
| `production/egress/` is the last NAT to destroy after Sandbox's | **There are three**, not two: `terraform-live/production/egress/main.tf` carries `egress_mode = "A"` today, so `VPC-SharedServices` has a NAT gateway and a default route as well | 5.1 |
| Only the `vpc` module has account-unique names | **`vpc-egress` does too**: its DNS-firewall CloudWatch log group `/awsds/<env>/dns-firewall` is account-unique, and its rule group, two domain lists and query-log config all collide by `Name` when two VPCs in one account both run a firewall. It takes the same `name_suffix` in the same version bump | 0.4, 5.1 |
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
- **0.2 — READ 2026-09-06 AND NOT YET WRITTEN, because this step contradicts Stage 6b and it is the one
  that is right.** 6b step 4.1 said 6c *"consumes"* the freed `10.40.0.0/16`; **this step says it "is free
  and stays unallocated"**, and the hub is 10.30 (the existing VPC, re-labelled), 10.31 and 10.32. The
  stage that has to BUILD the thing is the correct side (Lesson 32) — **and 6b's wrong clause had already
  been copied into six files in one day, two of them instruments.** All corrected before any 6c code was
  written; the consequence is that `networking.py`'s `NT-3`/`NT-5`/`NT-6` **stop having an expiry date**,
  because nothing will ever allocate the range they watch.
  - **DONE 2026-09-06, and the table REPLACES `CIDRS` rather than sitting beside it.** This step asked for
    two tables; the deviation was settled by measuring the call sites rather than by preference. **Every
    reader of `CIDRS` was asking a per-VPC question** and read per-account only because each account had
    one VPC: `vpc_cidr` wants the slice's own range, the D22 guard wants *"does this slice have an
    allocation"*, `peer_cidrs` wants a peer VPC's range, and the doc gate iterates the values. **None
    needs an account-level answer**, and `CIDRS["production"]` has none to give once Production holds
    three. Two tables carrying the same numbers with no reader for one of them is Lesson 33 with nothing
    bought. Stage 14's human reader still works: *"the lowest free /16 in the supernet"* is a question
    about the values.
  - **The gate for this step is that NOTHING generated changed**, and it holds: `sandbox/foundation`,
    `production/foundation` and `staging/foundation` all re-plan **`No changes`** after the swap. The
    `peers` map is deliberately still keyed by ACCOUNT — **that seam is 0.6's**, and the comment says so
    where the derivation lives: today every peering joins two accounts with one `foundation/` VPC each, so
    an account key names a VPC unambiguously; the moment Production holds three it stops doing so.
  - **`NETWORK_SLICES` gained the four 6c slices and a subset, `VPC_SLICES`** — the ones that *create* a
    VPC rather than living inside one. `foundation` was the whole answer while every account had one.
- **0.2 — [Claude] Extend the address vocabulary**: `scripts/tfhygiene/backend.py` gains a
  per-**(account, VPC)** table — `production-shared` 10.30.0.0/16, `production-networking` 10.31.0.0/16,
  `production-workloads` 10.32.0.0/16 — beside the per-account `CIDRS` that already carries
  `sandbox` 10.20.0.0/16 and `staging` 10.50.0.0/16 (6b step 4.1 put it there). **`10.40.0.0/16` is free**
  and stays unallocated; `10.60.0.0/16` is reserved for the `shared` account D38's trigger names;
  `10.16.0.0/13` stays the Sandbox supernet and `10.90.0.0/24` the WireGuard client range.
- **0.1 / 0.3 — DONE 2026-09-06.** 0.1 confirmed by reading: `D38`, `Lesson 44`, `INT-21`, `INT-22`,
  Recipe E and Recipe F all stand as written, and Recipe E was **used, not authored**, by 6b the next day.
  0.3 added four ranks — `networking` 21, `workloads` 23, `proxy` 41, `workloads-egress` 51 — each with the
  reason its number is what it is, in the discipline `vpn` and `pki` already sat under. `slices.py check`:
  **24 declared, 24 on disk**.
- **0.3 — [Claude] Add the slice ranks before any folder exists**: `RANKS` in `scripts/tfhygiene/layers.py`
  gains `networking` (21), `workloads` (23), `proxy` (41) and **`workloads-egress` (51)** — the `[E]`
  endpoint slice for the second Production VPC, ranked just above `egress` (50) so both come up after the
  proxy and go down before it. Rank first, folder second, same commit
  (Recipe C). The order is load-bearing: `up` ascends and `down` descends, so `proxy` at 41 comes up before
  any `egress` (50) and goes down after it — which is what makes a spoke's package path exist for the whole
  life of an `[E]` session.
- **0.4 — DONE 2026-09-06, `vpc-v0.2.0` released and the callers bumped.** Sixteen name sites in the
  module now read one `local.name_prefix`; the calling slices mirror it so the flow-log **role** and the
  **log group** keep the single contract their comment already stated. The suffix is generated per
  (account, slice) from a new `VPC_NAME_SUFFIXES` table keyed identically to `VPC_CIDRS` — one is the
  address plan, the other the naming plan, and sharing the key is what stops them drifting on the part
  that matters — and it is **emitted only when non-empty**.
  - **The default being harmless is proven, not assumed.** Recipe B step 1's source override was used:
    `sandbox/foundation` planned against the local module **before** the tag existed and read
    `No changes`; the override was reverted and re-initialised. After the bump, `sandbox/foundation` and
    `staging/foundation` both re-plan `No changes` on the version alone.
  - **The tag was confirmed by asking origin, not by trusting the push** (Recipe B step 5):
    `git ls-remote --tags origin vpc-v0.2.0` returns one line whose hash is the commit tagged.
  - **This step's note about the plan is now a measurement**: `production/foundation` plans
    **`8 to add, 13 to change, 8 to destroy`** — and it is the **same eight** 6b step 4.4 measured on
    Staging, one class: four security groups, the flow-log group, its IAM role, that role's inline policy,
    and the flow log binding them, all replaced because their *names* are inputs. The VPC, all six
    subnets, four route tables and the IGW change **in place**. **The gateway endpoints do not appear in
    the plan at all** — they carry no `Name` tag — so 1.1's *"endpoint ids unchanged"* gate passes by
    construction rather than by luck. **Not applied**: that is step 1.1, and 6c carries no apply
    authorization yet.
- **0.4 — [Claude] Bump `terraform-modules/vpc` to v0.2.0 with a `name_suffix`**, and carry it into the two
  names that are **account-unique, not VPC-unique**: `aws_cloudwatch_log_group.flow_logs`
  (`awsds-<env>-vpc-flow-logs`) and, in the calling slice, the flow-log IAM role of the same name whose
  policy is scoped to exactly that group. Security-group *names* are unique per VPC and would not collide,
  but their `Name` tags would, and `./aws/networking.py` reads tags — so the suffix reaches every `Name` as
  well (`awsds-prod-shared-*`, `awsds-prod-networking-*`, `awsds-prod-workloads-*`). Two commits, one tag
  (the runbook's order). **Note in the plan review that the existing VPC's tags change in place while its
  security groups are replaced.**
- **0.4a — DEFERRED TO 5.1, BECAUSE THIS STEP CONTRADICTS ITSELF** *(read 2026-09-06)*. Its first
  sentence says to bump `vpc-egress` **in the same sitting**; its last says the suffix *"rides along with
  the **v0.5.0** bump 5.1 makes for the NAT removal, so there is one version bump rather than two"*. Doing
  it now produces exactly the two bumps that sentence exists to avoid. **The last sentence wins**, and the
  deferral was checked rather than assumed:
  - **`production/egress/` does not set `dns_firewall`** — measured — so none of the module's
    firewall-shaped account-unique names (`awsds-<env>-egress*`, `/awsds/<env>/dns-firewall`) exists in
    Production today. What *would* collide is the **NAT pair** (`awsds-prod-nat`, gateway and EIP) and the
    interface endpoints' `Name` tags, which `./aws/egress.py` reads.
  - **5.1 removes the NAT outright** (D38: zero NAT gateways), so half that collision is deleted rather
    than renamed, and the other half cannot arrive before `production/workloads-egress/` is applied **with
    endpoints** — Stage 9/10, after 5.1. The window in which a bump is needed and has not happened is
    therefore empty.
- **0.4a — [Claude] Bump `terraform-modules/vpc-egress` in the same sitting, for the same reason**: it
  carries account-unique names too — the DNS-firewall log group **`/awsds/<env>/dns-firewall`** (a hard
  conflict) plus the rule group, its two domain lists and the query-log config, all named
  `awsds-<env>-egress`. Two Production VPCs both running a firewall collide, and `./aws/egress.py` reads
  these by name. The suffix rides along with the **v0.5.0** bump 5.1 makes for the NAT removal, so there is
  one version bump rather than two.
- **0.5 — DONE 2026-09-06, shape only — the VALUE is 4.9's.** Each row is `(account, slice)`, both
  consumers' `vpn_homes` variables carry the third field, and both `terraform_remote_state` keys read
  `${each.value.slice}` where they hard-coded `foundation`. **The row still points at
  `("sandbox", "foundation")` deliberately**: flipping it now would make `identity/sso` read an *empty*
  state, and `DenyControlPlaneOffVpn` would then deny every call from every network — the failure
  `permission-sets.tf`'s precondition already has an error message for. **Gate: `identity/sso` and
  `data-governance/data` both re-plan `No changes`.**
- **0.5 — [Claude] Give `VPN_HOMES` a slice field**: each row is consumed by `identity/sso/` and
  `data-governance/data/` as a `terraform_remote_state` read of that account's **`foundation/`**. The hub's
  Elastic IP, VPC id and gateway-endpoint id live in `production/networking/`, so the row becomes
  `("production", "networking")` and both consumers read the slice the row names. Without this the
  re-keying of 4.9 reads an empty state and `DenyControlPlaneOffVpn` denies every call from every network —
  the failure `permission-sets.tf`'s precondition already has an error message for.
- **0.6 — [Claude] Teach the peering pattern about three VPCs**: `production/foundation/peers.tf` finds a
  peer by the single tag `awsds-<env>-vpc`; that lookup becomes per-VPC and the peering map moves into
  `backend.py`, so both sides of every peering are generated from one list (Lesson 14).
- **0.7 — DONE 2026-09-06.** Rules A and B both read `VPC_CIDRS` per (account, slice). Rule B's
  "no slice on disk" branch now has **two live examples** — `production/networking` and
  `production/workloads`, whose rows are authored before their folders — where before it had none, and
  `docs/NETWORK.md` already names 10.31 and 10.32 in its §T target tables, so rule A passes without a
  documentation edit. That is the address plan having been written down before the code, working. Its second half was the header's stale parenthetical. The gate's own header carried a stale parenthetical —
  *"an account with an allocation and no `foundation/` (Staging today)"* — which described the **unvended**
  Staging, whose 10.40 row had no VPC behind it. 6b renamed `Development` into Staging, so all three
  allocated accounts carry a `foundation/` and that branch now has **no example**; it is kept because
  Stage 14 vends a CIDR row before its slices exist and puts an account back in it. The rule-B rewrite
  waits on 0.2's table.
- **0.7 — [Claude] Fix the documentation gate**: `scripts/check-network-doc.py` rule B recomputes subnet
  tiers from **one** CIDR per account; it now reads the per-VPC table. `docs/NETWORK.md` §2.1 gains every
  new network-bearing slice in the same commit.

### 1. Build the three VPCs — the address plan and the tiers that carry the new rules

**Action:** re-label the existing Production VPC and create two more. **Why:** the hub needs a public tier
that is the estate's only internet-facing tier, and nothing can be peered to a VPC that does not exist.
**Explanation:** nothing here costs money at rest, and the re-label is the least-churn choice — GitLab was
always planned in 10.30's private tier, both peering accepters live there, and the four zone associations
point at it.

- **1.1 — DONE 2026-09-06.** `8 to add, 13 to change, 8 to destroy`, re-plan `No changes`, and the two
  readings that decide it came back right: **`s3_gateway_endpoint_id` is the pre-apply value** and both
  peerings are still `active` under the **same `pcx-` ids**. The VPC tags as `awsds-prod-shared-vpc`.
  The eight replacements are the same class 6b step 4.4 measured on Staging.
- **1.1 — [Claude⚡] Re-label the existing VPC as `VPC-SharedServices`**: apply the `name_suffix` to
  `production/foundation/` and read the plan — tags in place, security groups replaced, **VPC and gateway
  endpoint ids unchanged**. Any id in the replacement list stops the step.
- **1.2 — DONE 2026-09-06.** `30 to add, 0 to change, 0 to destroy`, re-plan `No changes`. Free at rest:
  no NAT, no interface endpoint, no Elastic IP. The slice is `foundation`'s module with
  `name_suffix = "networking"` and **no zones, no peering and no `peers` input** — that last one was
  dropped from its `variables.tf` because 3.1's matrix is the map it will need, and a declared input
  nothing consumes is what tflint rejects.
  - **Its "the estate's ONLY IGW route" is the TARGET, not today's reading.** Measured after the apply:
    **four** IGW routes exist — Production 2, Sandbox 1, Staging 1. The spokes still carry Stage 3's, and
    **pass 5 is what removes them**. Worth stating before step 1.5 writes a check that would otherwise be
    red for four passes — the failure this stage's own pass-5 discipline exists to catch.
- **1.2 — [Claude⚡] Create `production/networking/`**: VPC 10.31.0.0/16 from the same module, both AZs by
  `zone_id` (D9), IGW attached, the public tier carrying the estate's only `0.0.0.0/0 → igw` route, S3 and
  DynamoDB gateway endpoints on every route table, flow logs on.
- **1.3 — DONE 2026-09-06, and it needed a module capability 0.4 did not add.**
  `aws_route.public_internet` was **unconditional**, so every VPC the module builds reached an internet
  gateway. `vpc-v0.3.1` adds `public_internet_route`; the gateway is still created when it is false,
  because that makes *"is this VPC private?"* a question about a **route table** — the object the answer
  is enforced in — rather than about which branch of a module ran.
  - **`29 to add` against the hub's 30, and the difference is exactly the missing route.** Read back from
    AWS rather than from state: `awsds-prod-workloads-public` returns **0** IGW routes,
    `awsds-prod-networking-public` returns **1**.
  - **A tag was burned getting here.** The `git commit` failed its hooks, the failure was swallowed by a
    `| grep` on the same command line, and `git tag` ran anyway — so `vpc-v0.3.0` is on origin pointing at
    the wrong commit. The runbook forbids force-moving a pushed tag, so v0.3.0 is **abandoned** and the
    release is **v0.3.1**. Second time this session that piping a command into `grep` hid its exit code.
- **1.3 — [Claude⚡] Create `production/workloads/`**: VPC 10.32.0.0/16, same shape, **no IGW route in any
  route table**. The module still creates the gateway (free, unused); the absence of the route is what
  makes the tier private. **Two private subnets in two AZs** — Stage 10's MWAA Serverless workers land
  here and AWS's private-routing shape requires it, which is why this one VPC's endpoint set is the
  estate's single D9 exception (Stage 10 decision 3 bounds how far the duplication goes).
- **1.3a — DONE 2026-09-06, and "empty" took an override the module says never happens.**
  `extra_services = []` alone left **eight interface endpoints** — the module's `core_services` default,
  0.010/h each, **0.080/h for a VPC nothing runs in**. That variable's description reads *"Overridden
  never"*, and it was written when every egress slice served a VPC people work in, where the core eight
  are what a notebook cannot function without under design B. **This slice is the case that comment did
  not anticipate**, so it empties both lists — and the plan then reads *"apply this plan to save these
  new output values… without changing any real infrastructure"*, which is what makes `usd_per_hour = 0.0`
  honest rather than aspirational. Stage 9/10 decides what comes back, and deciding is the point:
  restoring the core eight wholesale would inherit a list chosen for a different kind of VPC.
  - `egress_mode = "B"` from birth — this slice never passes through the shape 5.1 converts away from.
- **1.3a — [Claude] Write `production/workloads-egress/` beside it, empty of endpoints until Stage 9/10
  names them**: the `[E]` slice that gives `VPC-Workloads` its interface endpoints and its DNS firewall.
  It exists now rather than later because rank, `SLICES` row and folder land in one commit (Recipe C), and
  because `make down ENV=prod` must know about it the first time something is applied into that VPC.
- **1.4 — [Claude] Enumerate the ingress tier**: write into `docs/AWS_STATE.md` the invariant
  *"internet-originated traffic terminates only in `VPC-Networking`'s public tier, and every listener there
  is enumerated"* — today the WireGuard host's UDP/51820; Stage 13's public ALB becomes the second row. A
  world-open rule anywhere else is a finding.
- **1.5 — CORRECTED BEFORE IT IS WRITTEN (2026-09-06). As specified it is red for four passes.**
  *"Fails on any IGW route … outside that tier, in **any** account"* — measured today, **three** such
  routes exist (Sandbox 1, Staging 1, Production's `foundation/` 1), and they are Stage 3's, removed at
  **pass 5**. A check written now goes red immediately and stays red through 6c, 6d, 7 and 8, which is
  this stage's own pass-5 discipline and 6b's `DT-8` arriving a third time. **It takes a discriminator or
  it waits for 5.1** — `deploytargets.py`'s `built` is the pattern: a spoke that still carries its Stage 3
  NAT and IGW route is *unconverted*, and unconverted is a **note**; a spoke converted at 5.1 that grows
  one back is a **failure**. The cheapest signal for "converted" is the spoke's `egress_mode`, which is
  code, or the absence of its NAT gateway, which is a read.
- **1.5 — [Claude] Write the no-public-address gate**: extend `./aws/networking.py` with a check that fails
  on any IGW route, public IP or world-open security-group rule outside that tier, in **any** account.

### 2. Build the internal DNS — `awsds.internal` and the association matrix

**Action:** create the apex, the three child zones and the second Pages apex, and associate each into the
VPCs that must resolve it. **Why:** private zones do not delegate, overlapping zones resolve by most-
specific match, a VPC cannot query a peer's resolver, and a VPC associated with a matching zone that holds
no record gets **NXDOMAIN** rather than a public answer. **Explanation:** a missing association therefore
produces a failure indistinguishable from a name that does not exist — which is why the matrix is written
down (INT-22) and read by a check, since nothing derives it.

- **2.1 / 2.2 / 2.3 — DONE 2026-09-06.** Five zones: `awsds.internal` and `awsds-pages.internal` in
  `production/foundation/`, `prod.awsds.internal` in `production/workloads/`, `sandbox.awsds.internal` and
  `staging.awsds.internal` in the accounts that own them. **All five carry `ignore_changes = [vpc]` from
  the first apply** — 2.5 reverses the direction, so without it every later plan in an owning account
  would try to remove the association Production made. **Eight zones stand across three accounts**; the
  old three go at 2.6.
- **STEP 1.1 HAD BROKEN BOTH SPOKES, AND THIS PASS IS HOW IT SURFACED.** Renaming Production's VPC `Name`
  tag to `awsds-prod-shared-vpc` broke `data "aws_vpc" "production"` in **both** spokes' `peering.tf`:
  `Error: no matching EC2 VPC found`, on every plan and apply, from 1.1's apply until this fix. **The VPC
  id never changed**, so 1.1's gate — *"any id in the replacement list stops the step"* — could not see
  it. What moved was a **name another account resolves by**. **0.6's smallest half was pulled forward**:
  the `peers` map gains `name_suffix` and the lookup builds the tag from it. **The peering LIST can wait
  for 3.1's matrix; the peer LOOKUP cannot wait past the rename that breaks it**, which is why 0.6 is in
  pass 0 and moving it was the wrong call.
- **2.1 — [Claude⚡] Create the apex** `awsds.internal`, owned by `production/foundation/` (the services
  named directly under it live there). Records: `gitlab.awsds.internal`; `proxy.awsds.internal` and
  `vpn.awsds.internal` are written by pass 4 from the two hosts' **private** addresses.
  **THOSE TWO RECORDS WERE NOT WRITTEN BY PASS 4, AND NOBODY NOTICED UNTIL 5.7 (2026-09-06).** The
  zone was created here, both host slices were built at 4.7/4.8, and neither declared a record — so
  `proxy.awsds.internal` was **NXDOMAIN** while every client instruction, `NO_PROXY`'s
  `.awsds.internal` entry and step **6.1's closing check** all named it. A deferred obligation
  recorded only at the deferring end ([Lesson 34](../lessons.md)). **Repaired and applied**: each
  record is declared in the `[D]` slice that owns the address, `1 to add` each, both re-planning
  `No changes`. `gitlab.awsds.internal` is still owed and belongs to [Stage 7](stage-07-gitlab-runners-ecr.md).
- **2.2 — [Claude⚡] Create the three child zones**: `sandbox.awsds.internal` (owned by Sandbox),
  `staging.awsds.internal` (owned by the renamed account), `prod.awsds.internal` (owned by
  `production/workloads/`).
- **2.3 — [Claude⚡] Keep Pages on its own apex**: `awsds-pages.internal`, unchanged in intent from D36 — a
  sibling under the shared apex would weaken the cookie-scope separation the two-apex choice exists for.
- **2.4 — the same shape, flagged now (2026-09-06): `NT-12` cannot be written to the FINAL matrix and
  run before 2.6.** Step 2.6 retires `sandbox.internal`, `prod.internal` and `pages.internal` *"after pass
  6 measures the new ones"*, so **both zone families coexist for the whole of passes 2-6** and a check
  asserting *"the matrix as documented equals the matrix as deployed"* fails on every surviving old
  association. It needs the old family named as an expected, dated exception that 2.6 removes — the same
  treatment `EXC-nn` rows get — or it is written at 2.6 rather than at 2.4.
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

- **3.1 — 0.6 LANDS HERE, and two consequences of 6b land with it** (recorded 2026-09-06).
  0.6 is the mechanism whose data this step is; doing either alone is half a change, because `CIDRS`'s
  key set is what builds the `peers` map `production/foundation/peers.tf` consumes today.
  - **This matrix RETIRES the Staging ↔ `VPC-SharedServices` peering.** Staging keeps only
    Staging → `VPC-Networking`, and `VPC-SharedServices` ↔ Staging is on the *not built* list. That is the
    peering 6b step 4.5 preserved through a `for_each` rename with five `moved {}` blocks — correctly,
    because the alternative was destroying it mid-conversion with no replacement, and **INT-09 rides on it
    until this step re-homes INT-09 onto Sandbox ↔ `VPC-SharedServices`**.
  - **Those five `moved {}` blocks become dead here.** Their `from` addresses stopped existing when 4.5
    applied; they are a migration record, and this is the commit that should delete them rather than
    carry them into a file it is restructuring. The same is true of `terraform-live/identity/sso/moved.tf`
    at 4.9, which its own header already says.
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
- **3.6 — DONE (the re-cut landed with 4.7; the epilogue caught up 2026-09-06).** `NT-4` reads
  *"no route overlaps `10.90.0.0/24` **outside the hub**"* and pairs it with a positive reading —
  *"the ONE `10.90.0.0/24` route, inside the hub"* — so the exception is **asserted** rather than
  merely excluded. Measured: `rtb-0b13c0405057ab331`, `10.90.0.0/24 → eni-0a6313a565c2b09c7`,
  `active`. The instrument's closing legend still described the old wording and now does not.
  *The original step follows:*
- **3.6 — [Claude] Keep `10.90.0.0/24` out of every table but one**: the WireGuard client range is
  masqueraded today and stays invisible to the spokes. The **one** exception is inside `VPC-Networking`,
  added at 4.7. Re-cut `./aws/networking.py` `NT-4` from *"no route to 10.90/24"* to *"no route to
  10.90/24 outside `VPC-Networking`"*.
- **3.7 — `NT-11` has a window too, and it is inside pass 3 rather than across passes** (2026-09-06).
  *"Every active peering has a route on both sides in every affected route table"* is false between **3.4**
  (the peerings applied) and **3.5** (the tunnel's return path added), and false again for any old peering
  still standing while the new ones come up. Written as specified it goes red mid-pass, in the one place
  an operator most needs a trustworthy reading. Either it runs only at pass 6, or it takes the peering
  matrix as its expectation and reports *"declared but not yet routed"* separately from *"routed to
  something not in the matrix"* — which are opposite findings and must not share a verdict.
- **3.7 — DONE 2026-09-06, AND THE TWO FINDINGS ARE SEPARATE CHECKS, WHICH IS WHAT THE STEP
  ABOVE ASKED FOR.** `NT-11` reads **`pass`: 5 active peerings, both sides routed in every account
  this run could read.** The sixth peering in the estate is `deleted` and nothing points at it,
  which is why it is silent rather than a finding. The split:
  **declared but not routed** — an `active` peering with no route on one side, named by side rather
  than counted, and normal for the minutes between creating a peering and adding its routes;
  **routed but not active** — a route whose target is deleted, failed or pending, which is a
  **blackhole** and the more urgent of the two. A single verdict over both would let the second
  hide behind the first.
  **It asserts only about accounts it actually read**: a VPC whose account holds no live profile is
  skipped, because *"no route found"* and *"no session"* are the same silence — and this check
  crosses accounts by construction, so that case is normal rather than exceptional.
  **Both branches proven on synthetic inputs**, since the estate has neither defect and a check
  that has only ever passed is a claim: one side unrouted → named; a deleted peering still routed →
  named as a blackhole; a route to a peering id nobody read → named; an unread side → silent.
  *The original step follows:*
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
  **APPLIED 2026-09-06 — `6 to add`, and three corrections the writing of it forced.** (i) The
  `wireguard_eip_public_ip` output listed above is **NOT** in this step: the address is transferred rather
  than allocated, so the resource backing that output arrives with 4.6's `import {}`. Declaring it here
  would mean allocating a second address, which is the risk table's *fallback*, not the plan.
  (ii) The proxy's allow-list parameter is `/datascience/<env>/proxy/allowlist` and **cannot** be
  `/awsds/…`: Parameter Store reserves every name beginning with `aws`, a collision
  [`conventions.md`](../conventions.md) has carried since 2026-08-16 and this step did not repeat — the
  apply failed on it. (iii) The tunnel range reaches the slice as a **generated** `wireguard_peer_cidr`
  from a new `VPN_HOST_SLICE` tuple, which is deliberately **not** `VPN_HOMES`: see 4.12.
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
- **4.6a — CHECKED FOR THE COLLISION THIS STAGE HAS HIT TWICE, AND THERE IS NONE (measured 2026-09-06).** *(Numbered `4.7` when written, beside the host build that already had that number — corrected 2026-09-06 at execution. Step numbers are identifiers in this plan, so two steps sharing one is the identifier failing at its only job.)*
  0.4 and 1.3 both found a module asked for a capability its step had not enumerated, and 4.7/4.8 put
  **two hosts in one account** — the exact shape that made `vpc` need a `name_suffix`. So the `wireguard`
  module was grepped rather than assumed: it builds **two** names, `awsds-<env>-vpn` and
  `awsds-<env>-vpn-health`, and a proxy slice builds `awsds-<env>-proxy-*`. **Different modules, different
  stems, no collision** — no bump needed here, and this line exists so the question is not re-opened at
  the keyboard. `vpc-egress` is the module that *does* need the suffix, and that is 0.4a's deferral to 5.1.
- **4.7 — [Claude⚡] Build the WireGuard host — AND RE-HOME `./aws/vpn.py` IN THE SAME SITTING.** The
  instrument hard-codes `VPN_HOME_PROFILE = "awsds-infra-sandbox-1"` (measured 2026-09-06 at 4.1), so from
  the moment a host exists here it reports on the *old* account: a stopped instance and a group about to be
  destroyed, while the live tunnel goes unmeasured and **`VP-3` keeps reading `pass` about Sandbox**
  ([Lesson 31](../lessons.md) exactly — a check inherits the scope of the account it was written in).
  Between 4.1 and 4.13 the estate carries **two** world-open rules, one per account, and that is expected;
  the discriminator is the group *name*, `awsds-<env>-vpn`. Build: `production/vpn/` `[D]`, in `VPC-Networking`'s public tier,
  from the existing module at **v0.5.0** with three changes: `vpc_nat_cidrs` is **removed** (the
  isolated-tier NAT job dies with the buildbox's move, 5.8), the `PostUp` chain forwards tunnel packets
  **only to RFC1918 destinations** and drops the rest, and it stops masquerading traffic bound for the
  proxy so Squid sees `10.90.0.x`. Add `10.90.0.0/24 → the WireGuard host's ENI` to the hub's public-tier
  route table — the single exception 3.6 names, in the same VPC, which is what gives the access log a
  per-device address without any logging change.
- **4.7-4.11 AUTHORED 2026-09-06, NOTHING APPLIED.** `wireguard-v0.5.0` (untagged as yet),
  `terraform-live/production/vpn/` and `terraform-live/production/proxy/` with its `squid.conf` and render
  templates, the `[P]` access log and its key in `networking/`, and both allow-lists filled. Every gate is
  green — `terraform validate`, `tflint` 0, `checkov` 0 failed, `./scripts/slices.py check` 29/29,
  `make check` OK — and both templates were **rendered**, not merely validated, which is what caught three
  defects a reading would not have: `+` in HCL is arithmetic and not concatenation; `%{` is `templatefile`'s
  directive marker and collides with Squid's own `strftime` escape (**and with a comment describing the
  collision**); and the first render script's "revert" deleted the new file while the old one was already
  gone. **What is deliberately NOT authored is 4.11's second half** — the export to Log Archive. The
  mechanism is a real choice (a subscription filter into a Firehose in Log Archive, against a scheduled
  `CreateExportTask` to S3) with different cost shapes, and picking one silently would be an estimate
  standing in for a measurement (Lesson 6). It is a decision due below.
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

- **4.9 — REOPENED AND CORRECTED 2026-09-07: THE CLIENT PLANE WAS THE WRONG SHAPE, AND THIS
  STEP'S OWN PARAPHRASE IS WHAT MADE IT SO.** The user found it on the first browser that tried to
  use the proxy: the AWS console opened and **nothing else on the internet did**.
  `objectives.md` is explicit in two places and they agree — *"all internet access will be
  **MONITORED** … the user can therefore use the browser to reach the internet"* and *"the
  restriction is on the SageMaker-**MANAGED COMPUTE**, never on the user's (client's) machine"*.
  What stood here was a **23-name allow-list** of AWS console, portal and sign-in families, which
  made the **client's** internet stricter than the **compute's**. The step said *"the tunnel range
  carries the institutional web filter — what a person on a company laptop may reach"*, and
  `squid.conf` is default-deny, so *"filter"* was implemented as an **allow-list**. **An
  institutional web filter is a DENY-list over an open default.** `CLAUDE.md` says the objectives
  are *"the specification a stage is measured against, so it is summarised nowhere"* — and the
  summary in this step became the specification, which is exactly what that rule exists to stop.
  **The repair**: every plane now carries a `mode`. `allowlist` (the four spokes, unchanged —
  `sandbox-foundation` is D5's *"short list"* for the compute) and **`open`** (the tunnel), whose
  list is a **deny** list, **empty by decision** — everything permitted, everything logged, filled
  when a written policy exists. The control for that plane is the access log, which is what
  *monitored* names. **The three global denies still apply**: private destinations, unsafe ports,
  CONNECT to anything but 443 — *open* means open to the internet, never to the estate.
  Two plan-time gates followed: the collision check now reads **both** kinds of list, and an
  unknown `mode` is a plan failure rather than a plane that renders nothing.
  *The original step follows:*
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
  - **AND THE STAGING CIDR, which this list omitted until 4.1 was written (2026-09-06).** Staging is a
    peered spoke with a runtime of its own, so it needs a plane like every other. The omission is why the
    parameter's planes are **derived from the peering matrix** rather than transcribed from this
    paragraph: a spoke the security group admits and the allow-list has never heard of is reachable and
    mute, which is the failure that looks like a network fault. Its list starts empty, like Workloads'.
- **4.10 — [Claude] Keep the configuration out of the host, and give it a reload path**: the allow-lists are
  `[P]` data in an SSM parameter rendered at boot, never state that exists only on a `[D]` disk (Lesson 4).
  **The parameter is `/datascience/<env>/proxy/allowlist`** — not `/awsds/…`, which Parameter Store refuses
  outright ([`conventions.md`](../conventions.md)); Standard tier, so free and capped at **4 KB**, and an
  allow-list that outgrows that splits per plane rather than paying for Advanced.
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

**Action:** destroy all three NAT gateways, complete each VPC's endpoint set, and re-purpose the DNS
firewall. **Why:** with the proxy reachable, the per-account NAT gateways are the last transparent path and the only
metered thing in the egress slices the design no longer wants. **Explanation:** removing them is also what
makes the proxy's allow-list the single filter it is supposed to be — and it is what makes the SMUS
network-isolation page's required endpoint list finally apply, because its premise (no public egress)
becomes true.

- **5.1 — DONE 2026-09-06 AS CODE, AND IT WAS NEVER A DESTROY.** Measured first: **zero NAT gateways,
  zero default routes and zero interface endpoints in all three accounts** — the `egress/` slices are
  `[E]` and were all down, so there was nothing to destroy. The act is a code change so that the next
  `make up` never creates one. `vpc-egress-v0.6.0` deletes `nat.tf` and **`egress_mode`,
  `nat_public_subnet_id` and `private_route_table_ids` with it** (nothing else read the route tables),
  carries 0.4a's `name_suffix` through one `name_prefix` local, and **removes the
  `&& var.egress_mode == "A"` clause from `dns_firewall_enabled` in the same commit** — without that,
  this step would have silently disabled the firewall 5.7 keeps. All four callers rewired; the two
  NAT outputs deleted from each after checking nothing anywhere consumed them. **Proven by plan:**
  zero NAT resources in any of the four, and the DNS Firewall's six resources still present in
  Sandbox. `production/workloads-egress` reads *no infrastructure changes* — outputs only.
  *The original step follows:*
- **5.1 — [Claude⚡] Destroy all THREE NAT gateways**: `egress_mode = "B"` in **Sandbox, Staging and
  Production** — `terraform-live/production/egress/main.tf` carries `egress_mode = "A"` today, so
  `VPC-SharedServices` has one as well and "both NAT gateways" undercounted. Every private route table
  loses its `0.0.0.0/0` entirely. `vpc-egress` drops the NAT half (and its `nat_public_subnet_id` input) rather than keeping dead code, and
  carries 0.4a's `name_suffix` in the same version. **THAT VERSION IS NOW v0.6.0, NOT v0.5.0** — v0.5.0
  was spent on 5.3's `optional_service_groups` (2026-09-06), and the *one bump rather than two* line was
  an optimisation rather than a constraint. **AND IT CARRIES A COUPLING THIS STEP MUST HANDLE EXPLICITLY,
  found while writing v0.5.0:** `dns-firewall.tf` reads `dns_firewall_enabled = var.dns_firewall &&
  var.egress_mode == "A"`, so **deleting mode A silently disables the DNS Firewall** that 5.7 wants kept
  in every compute VPC. One condition, two intents ([Lesson 51](../lessons.md)) — the clause goes in the
  same commit as the NAT, or 5.1 and 5.7 undo each other without either plan reading wrong.
- **5.2 — DONE 2026-09-06 (as code; the slice is `[E]` and down, so it takes effect at the next
  `make up`).** Sandbox's `extra_services` goes from 4 to **10** — the three SageMaker names and
  `s3tables`, plus `datazone`, `ssm`, `ssmmessages`, `ec2messages`, `ec2` and `secretsmanager`.
  **18 interface endpoints in total**, counted from the slice's own plan. `q` is struck: the
  Region's catalog (569 services, re-measured with a healthy session) carries `qapps` and
  `quicksight*` and nothing named `q`.
  **The three `layers.py` rates moved with the NAT and were COUNTED, not computed** — Sandbox
  **0.160 → 0.180**, Staging 0.160 → **0.110**, Production 0.150 → **0.100**. Sandbox's *idle floor*
  rises because 5.2 has to enumerate what the NAT covered silently — **and that is the only axis on
  which it rises.** Per gigabyte a NAT is **0.045** against an endpoint's **0.010**, so design B costs
  +0.020/h fixed here and saves 0.035 on every GB: **break-even ≈ 0.57 GB/h**, which one container pull
  passes in minutes. Estate-wide the fixed rate falls too, 0.470 → **0.390/h**. None of the three
  includes 5.3's optional groups, which only exist for an apply that names them.
  *The original step follows:*
- **5.2 — [Claude⚡] Complete the required endpoint set**: Sandbox re-adds **`datazone`** — removed on
  2026-08-25 only because its private zone shadowed a client-plane name, which cannot happen now — and
  gains `ec2`, `ec2messages`, `secretsmanager`, `ssm`, `ssmmessages` and ~~`q`~~. **Measure rather than
  copy** — and the measurement caught this step's own list on 2026-09-06: **there is NO `q` endpoint
  service in `us-west-2`.** The Region's catalog carries `qapps` and the `quicksight*` family and
  nothing named `q`, so that entry is struck. `codewhisperer` is `us-east-1`-only for the same reason
  ([6d](stage-06d-unified-studio-remainder.md) step 3.5 decides it).
  **AND ONE NAME THIS STEP MISSED IS NOW ALWAYS-ON: `s3tables`** (user decision, 2026-09-06).
  `S3TableCatalog` is one of category 1's **eleven** — enabled — and the S3 **gateway** endpoint does
  not cover it: a gateway carries `s3` and `dynamodb`, while `s3tables` is its own service name. Under
  design B a project using that blueprint had no path at all, which is 5.3's failure in a blueprint
  nobody had named. Applied in `sandbox/egress`'s `extra_services`, not behind a flag.
- **5.3 — TAKEN 2026-09-06, AND IT IS NONE OF THE THREE SHAPES THIS STEP OFFERED.** The user kept **both
  families enabled** and made the ENDPOINTS the variable: `vpc-egress` **v0.5.0** takes
  `optional_service_groups`, **empty by default**, threaded by `make up ENV=<x> GROUPS=bedrock,emr`.
  So a family nobody uses that day costs nothing, and nothing is removed from the portal. **The group
  map lives in the module** (three hand-kept copies would diverge on the first addition) with a
  **closed-list validation**, because an unknown group name fails *silently* — it contributes nothing,
  the apply succeeds, and the blueprint fails on first use exactly as with no flag. Wired in
  `sandbox/egress` alone: these are SMUS blueprints and the SMUS surface is in that account only.
  **`bedrock` IS FOUR ENDPOINTS AND NOT THE THREE BELOW** — the six enabled blueprints both AUTHOR
  Bedrock objects and INVOKE them, and `bedrock` (the control plane `CreateGuardrail` and
  `CreateEvaluationJob` call) is a different service from `bedrock-agent`. `mwaa` is **reserved and
  empty**: `Workflows` is category 2 and the estate's decision is *MWAA Serverless only*, while the
  catalog splits `airflow-serverless` from the provisioned trio — filling it in now would settle a
  Stage 10 question by accident. Measured end to end: **12** interface endpoints with no flag, **23**
  with `bedrock,emr`. *The step's original text follows, because the shapes it weighed are why the
  answer is a fourth one:*
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
- **5.4 — TAKEN 2026-09-06: PIN THE SUBNETS**, the free option and the recommended one. The blueprint
  takes a subnet list, so a project's apps are handed only the AZ that holds the endpoints — D9's
  single-AZ rule stays intact and the resolution failure stops existing rather than being paid for.
  Measured at [6d](stage-06d-unified-studio-remainder.md) step 3 either way. *The reading follows:*
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
- **5.5 — DONE 2026-09-06, AND IT COVERS TWO OF THE THREE VPCs THE STEP NAMES.** Sandbox got the trio
  at 5.2; **`VPC-SharedServices` gets it here** (`production/egress` 10 → **13** endpoints,
  0.100 → **0.130/h**), one step ahead of the buildbox 5.8 lands there. **`VPC-Workloads` does NOT,
  and the step's own qualifier is what excludes it:** it says *every INSTANCE-BEARING spoke*, and
  that VPC bears none — measured, Production's only two instances are in `VPC-Networking`, which
  reaches SSM through the IGW and needs no endpoint. `workloads-egress` already refuses endpoints
  *"because the other egress slices have them"* for a network nothing runs in; adding 0.030/h of
  Session Manager path there would have been that exact purchase. **The refusal is written INTO the
  slice**, next to the empty lists, so the next reader meets it where they would look. They arrive
  with the first workload, from Stage 9/10.
- **5.5 — [Claude⚡] Give every instance-bearing spoke its SSM path**: `ssm`, `ssmmessages` and
  `ec2messages` in Sandbox, `VPC-SharedServices` and `VPC-Workloads`. Session Manager does not work through
  an HTTPS proxy listener, and the shell that reads the proxy's own log must not depend on the proxy
  (Lesson 24). `VPC-Networking`'s two hosts reach SSM through the IGW directly.
- **5.6 — DONE 2026-09-06 AS CODE (`vpc-egress-v0.7.0`), AND THE GENERATOR READS THE NAMES RATHER
  THAN BUILDING THEM.** The module already turns a token into `com.amazonaws.<region>.<token>`, and
  building the DNS name the same way is the obvious move and wrong: measured across the **29**
  services this estate can declare, **eight** have a private DNS name no rule derives from the token
  — `ecr.api` → `api.ecr.…`, `ecr.dkr` → `*.dkr.ecr.…`, `sagemaker.api`/`.runtime` reversed the same
  way, `sagemaker.studio` → `*.studio.<region>.sagemaker.aws` (**a different TLD**),
  `emr-dashboard` → `*.emrappui-prod.…` (**an unrelated name**),
  `emr-serverless-services.sessions` → `*.s.…`, and `elasticmapreduce-services` wildcarded. A hand
  list would have been wrong for **ECR**, the busiest path here, and wrong *silently*. So a
  `data "aws_vpc_endpoint_service"` per declared service reads `PrivateDnsName` at plan time — free,
  and needing no endpoint to exist.
  **AND THE STEP'S OWN PARENTHESIS WAS AMBIGUOUS IN THE DANGEROUS DIRECTION.** *"S3 and DynamoDB ride
  the gateway prefix lists"* can be read as *therefore omit them*; the reading that holds is
  **therefore include them**, and it is not a convenience. Measured 2026-09-06:
  `com.amazonaws.<region>.s3` returns a `PrivateDnsName` for its **Interface** shape and **`None` for
  its Gateway shape** — a gateway works by *routing* and never by resolution, so the generator
  **cannot** emit them and they are hand-named in the fixed half. Omitted, every S3 call would go to
  Squid, leave through the hub's IGW as a **public** call, and arrive carrying neither
  `aws:SourceVpc` nor `aws:SourceVpce` — the two keys every bucket policy in this estate is written
  on. The data perimeter would fail **open**, for the one service that holds the data.
  **Rendered, not merely validated** (Lesson 54), on all four slices: Sandbox **26** entries, Staging
  **19**, `VPC-SharedServices` **21**, `VPC-Workloads` **8** — the fixed half alone, which is the
  right answer for a VPC with no interface endpoint and two `[P]` gateways. Three **output
  preconditions** carry the three silent failures: no `*`, no `/`, no `:`. The `images/base` rule is
  recorded in the slices' own `outputs.tf`, where a consumer meets it.
  *The original step follows:*
- **5.6 — [Claude] Generate `NO_PROXY` per VPC, from that VPC's endpoint list**: not a blanket
  `.us-west-2.amazonaws.com`. A blanket suffix tells the client "reach every AWS service directly", and a
  service with no endpoint then has no route at all — a timeout with no message (Lesson 42). Generated from
  the list the `egress/` slice already declares, the same call is a proxy **403 naming the host**, which is
  a finding rather than a hang. The generated list also carries `169.254.169.254`, `169.254.170.2`,
  `localhost`, `127.0.0.1`, `.awsds.internal` and `.awsds-pages.internal` (S3 and DynamoDB ride the gateway
  prefix lists). **It carries no CIDR block and no leading wildcard**: GitLab documents that `NO_PROXY`
  wildcards work only as **suffixes** — not prefixes, not CIDR — so `10.0.0.0/8` in that variable is
  silently ignored by the clients that matter, and an entry must never carry a port, which GitLab
  documents as breaking DNS resolution for repository mirroring. Intranet reach is expressed as name
  suffixes, and any literal address that must bypass the proxy is listed literally.
  **Never an `ENV HTTP_PROXY` in `images/base`** — every application image inherits from it and runs as a
  Production job behind endpoints, where a wrong `NO_PROXY` would send S3 and STS out through the proxy as
  a public address. Build time is a BuildKit `--build-arg`; runtime in a Studio space is
  `ContainerEnvironmentVariables` on the app image configuration, or a JupyterLab lifecycle configuration —
  which for SMUS domains **must be attached in the console**, the CLI path being documented as not
  supported.
- **5.6a — ANSWERED 2026-09-06: STAGING KEEPS ITS FIREWALL, and 6b's argument was about a job that
  no longer exists.** 6b reasoned that *a headless deployment target resolves whatever its pipeline
  resolves* — true, and an argument about **filtering the internet**, which is the job 5.1 ended by
  deleting the last default route. What is left is 5.7's job, *close the recursive resolver as an
  exfiltration channel*, and that channel is a property of **a VPC where code runs**, not of who runs
  it: Staging runs promoted models, unattended, from artefacts built in Sandbox. So the `.tf` keeps
  `dns_firewall = true`, the `dns-allowlist.py` row stays, **and both moved in the same commit** as
  5.7's re-cut — which was this step's actual requirement.
- **5.6a — THIS STEP OWNS A QUESTION 6b DEFERRED TO IT** (2026-09-06). *(Numbered `5.7` when written,
  beside the DNS-Firewall re-cut that already had that number — corrected 2026-09-06, the same defect
  4.7 carried. Step numbers are identifiers in this plan.)* 6b step 5.1 wanted
  `./aws/dns-allowlist.py` to drop the Staging slice, reasoning that a headless deployment target resolves
  whatever its pipeline resolves. **The row was retargeted instead, not dropped**, because
  `terraform-live/staging/egress/main.tf` still declares `dns_firewall = true` with an allow-list — a
  check whose scope shrank while the thing it measures did not is Lesson 31. *"It stays in every **compute**
  VPC"* is the sentence that decides it: **Staging carries the SageMaker runtime, so it is a compute VPC**
  and keeps its firewall — or it does not, and both the `.tf` and the instrument row go together. Whichever
  way, **the two move in the same commit**.
- **5.7 — DONE 2026-09-06, IN BOTH HALVES, AND THE LIST WENT FROM 63 ENTRIES TO 10.** Both compute
  VPCs keep the firewall; `VPC-Networking` never had one and still does not; the four families are
  `*.amazonaws.com`, `*.api.aws`, the two private zones — **and `*.sagemaker.aws`, which the step's
  own list omitted**. That omission would have orphaned a **paid** endpoint: `sagemaker.studio`
  answers on `*.studio.<region>.sagemaker.aws`, a TLD neither of the first two covers, and the symptom
  is NXDOMAIN — indistinguishable from a network fault. **`vpc-egress-v0.8.0` turns it into a
  plan-time failure**: a precondition computed from the same `describe-vpc-endpoint-services` reading
  NO_PROXY uses, kept as a **separate** local because the two syntaxes look alike and are not
  translatable by transcription (Lesson 53) — NO_PROXY needs `*.` gone, a Route 53 domain list needs
  it present **and** the apex beside it. Proven by **negative control**: with the `sagemaker.aws` pair
  removed the plan fails naming `*.studio.us-west-2.sagemaker.aws`; with it, green.
  **AND A `"*"` CAME OFF THE SANDBOX LIST.** Commit `f6bb316` (*"allow-all egress"*, 2026-08-23) had
  put a single wildcard at the top, so the sixty-two entries beneath it were decoration and the
  firewall was a default-**ALLOW** for a fortnight. Named rather than quietly dropped.
  **`EXC-05` and `EXC-06` close; `EXC-04` DOES NOT, and the stage file said it would.** 5.7 changed
  the CONTENT of the lists; `EXC-04`'s mechanism is the provider comparing two **spellings** of
  whatever the content is. Ten entries churn exactly as sixty-three did, and it could not even be
  re-measured — the symptom appears on the plan *after* an apply, and all four `egress/` slices are
  `[E]` and down.
  **`./aws/dns-allowlist.py` re-aimed at the five Squid planes** (`hub-anchors.tf` by default, the
  SSM parameter with `--from-api`). `DN-1` unchanged in spirit — 46 names, all answering. **`DN-2` is
  new and is the valuable one**: Squid's two overlap outcomes are not the same severity, and the
  apex-beside-its-own-`.x` pair is `FATAL: Bungled`, a proxy that does not start. `DN-3` compares
  committed against deployed — **5 planes, entry for entry** — and is explicitly the *first of two
  links*, `PX-3` being the second. `DN-4` measures the design claim: **exactly one** entry
  (`.amazonaws.com`) is on both the tunnel and a workload plane, so the two filters really are two.
  Both new checks proven with a negative control.
  *The original step follows:*
- **5.7 — [Claude] Re-cut the DNS Firewall**: it stays in every **compute** VPC and its allow-list shrinks
  to `*.amazonaws.com`, `*.api.aws`, `.awsds.internal` and the proxy's name; the `BLOCK`-NXDOMAIN `*` rule
  stays. Its job is no longer filtering the internet but closing the recursive resolver as an exfiltration
  channel. `VPC-Networking` carries **none** — the proxy has to resolve. `EXC-04`, `EXC-05` and `EXC-06`
  close with the old list, and **`EXC-05`'s whole failure mode retires with them**: Squid matches the
  *requested* hostname, so a CDN that stops flattening its chain can no longer turn an allowed name into a
  block that blames the wrong entry. Re-aim `./aws/dns-allowlist.py` at the Squid lists — `DN-1`..`DN-4`
  become questions about the proxy's lists, read through SSM the way `vpn.py --on-host` reads the VPN host.
- **5.8 — DONE AND EXERCISED END TO END 2026-09-06, AND THE EXERCISE IS THE POINT.** The slice is
  `production/buildbox/`, in **`VPC-SharedServices`'s PRIVATE tier** — not the isolated one the old
  home used: **measured**, the peering routes to `VPC-Networking` are in the private route tables and
  **not** in the isolated one, so an isolated-tier build host could not reach the proxy at all. The
  Sandbox state was already empty, so the destroy half was free. `vpc_nat_cidrs` was already gone at
  `wireguard-v0.5.0`; the isolated-tier route is deleted; **the `probes/` refusal is deleted rather
  than retargeted**, and `buildbox.py`'s two refusals are now *read the `ssmmessages` endpoint before
  applying* and *start the proxy host*.
  **THE ECONOMICS INVERTED**: `production/egress/` used to be an obstacle (*"build with `egress/`
  down"*) and is now a **hard prerequisite** — its SSM endpoints are the host's only door — so a build
  session pays **0.130 USD/h** it used to avoid.
  **FOUR PLACES, BECAUSE AN EXPLICIT PROXY IS NOT TRANSPARENT**: `/etc/environment`, a docker daemon
  systemd drop-in, `~/.docker/config.json` for build containers, and **the boot script's own exported
  environment**, which `/etc/environment` does not provide.
  **THREE DEFECTS THE RUN FOUND THAT NEITHER `validate` NOR `plan` COULD** (Lesson 54, and the whole
  reason this was applied rather than authored):
  1. **`dnf.conf`'s `proxy=` has no exclusion setting**, so it sent the AL2023 repositories — which
     are on S3 and must go direct — at the proxy. Removed; the environment is the only place that
     expresses both halves.
  2. **`s3.dualstack.<region>.amazonaws.com` is a DIFFERENT NAME**, not a label under
     `s3.<region>.amazonaws.com`, so `NO_PROXY` did not cover it and the first boot died on
     `Failed to download metadata`. `vpc-egress-v0.9.1` adds both gateway services' dualstack forms.
     (**`v0.9.0` is ABANDONED on origin** — Lesson 46 a second time: a piped `git commit` returned
     `tail`'s exit code and the `&&` chain tagged a commit that never happened.)
  3. **`public.ecr.aws` REDIRECTS blob downloads to a CloudFront distribution**, and Squid matches the
     hostname the client *requested* — so a redirect is a new request with a new name that must
     itself be allowed. The name came **out of the access log**, which is what 4.11 is for:
     `docker pull` said only `Forbidden`. **One distribution, not `.cloudfront.net`** — the tunnel
     plane has the namespace and a build host must not.
  **Verified inside a build container**, three outcomes: `pypi.org` **200**, `example.com` **403**,
  the AL2023 S3 dualstack name **200 direct**. Plus a real `docker pull` completing, and — free from
  the same session — `http://10.32.0.10/` returning **403**, which is 6.3's *"the proxy is not an L7
  bridge"* reading taken early. Both slices torn back down afterwards.
  *The original step follows:*
- **5.8 — [Claude⚡] Move the build host**: `sandbox/buildbox/` is destroyed and re-created as
  `production/buildbox/` in `VPC-SharedServices` beside the runners, with the docker daemon and the SSM
  agent proxy-configured. It is `[E]` and holds no state that survives a session (`buildbox.md` §S), so
  this is a destroy-and-create, **not** Recipe E. Its only egress today is a route to the WireGuard host's
  ENI, and a route target cannot live in another VPC. The `vpc_nat_cidrs` input, the isolated-tier
  security-group rule and the *must not coexist with `probes/`* rule all die in the same commit;
  `runbooks/buildbox.md` is rewritten in the same sitting.
- **5.9 — DONE 2026-09-06, AND IT GAINED A FALLBACK THAT IS MEASURED RATHER THAN ARGUED.** The
  re-statement itself was already carried by [D38](../decisions/D38-single-egress-hub.md) — MWAA
  Serverless struck (its private shape *forbids* a NAT route; the requirements list demanding two NAT
  gateways belongs to the public shape, Lesson 41), ECR's pull-through cache named as the candidate,
  Stage 7 step 5.2 as the measurement. What 5.8's run adds is a **third fallback, ranked first**:
  **pull the public image through the proxy and push it into ECR**, exercised end to end that day —
  `docker pull public.ecr.aws/…/alpine:3.20` completed through Squid once the blob redirect's
  CloudFront distribution was on the build plane, with the **layers taking the free S3 gateway path**.
  It needs no host in the hub, no second build environment and no route. It does **not** make the
  pull-through *cache* work — that is AWS fetching upstream on the service's own behalf, which no
  client-side proxy setting reaches — so 5.2 still measures that. But the estate no longer *depends*
  on the answer in order to obtain a public image, which is what "the contingency has a candidate and
  no instance" was worth having.
  *The original step follows:*
- **5.9 — [Claude] Re-state the NAT contingency, with its first candidate removed**: a NAT gateway is built
  **only** for a named service that needs the internet and cannot be told about a proxy, in **that
  service's own VPC**, with its own cost row and a trigger to remove it. **MWAA Serverless is no longer that
  candidate**: AWS documents a private-routing shape whose subnets *"must not have a route table to a NAT
  device… nor an internet gateway"*, with interface endpoints for `logs`, `monitoring` and `kms`, a
  self-referencing security group and two private subnets in two AZs. The requirements list that demands
  two NAT gateways is the **public-routing** shape of the same page (Lesson 41). Stage 10 builds the
  private one. **One candidate is named, and it is not MWAA**: ECR documents that the **first** pull
  through a pull-through cache rule *"may require a route to the internet"*, with a public subnet and an
  IGW route as its own remedy — a route, which this design removes. [Stage 7](stage-07-gitlab-runners-ecr.md)
  step 5.2 **measures** it, and only a failure there promotes `VPC-SharedServices` to an actual NAT
  gateway, with a cost row and a removal trigger. Two cheaper fallbacks are ranked ahead of it in that
  step, and the honest state is: the contingency has a candidate and no instance.

### 6. Measure the whole thing — the readings that close the stage

**Action:** take six readings, each with two distinguishable outcomes. **Why:** every claim in this stage is
about a path, and a path is measured, never read off a diagram. **Explanation:** three of these also close
obligations older than the stage.

- **6.1 — DONE 2026-09-07 BY THE USER, ALL FOUR READINGS, AND ONE OF THEM CORRECTED THIS
  REPOSITORY'S OWN PREDICTION.** The client edited **one line** — `DNS = 10.31.0.2` — and the
  `Endpoint` and `PublicKey` lines did not move, which is the transfer and the hand-copied host key
  paying off in the only place a user would notice. Readings: the DNS **pair** discriminated
  (`prod.awsds.internal` answered, `sandbox.internal` did not); `proxy.awsds.internal` →
  **`10.31.160.106`**, private, in the hub's public tier; no internet without the proxy; and
  `curl -x` → **`184.33.8.126`**, the proxy's address.
  **THE THIRD READING WAS A TIMEOUT WHERE THE RUNBOOK PREDICTED A FAST REFUSAL**, and measuring the
  host settled it rather than a re-reading: `FORWARD` rule 4 had rejected **8453 packets** with
  `icmp-admin-prohibited`, so the host refuses exactly as designed — and macOS **ignores an ICMP
  unreachable arriving mid-`connect()`**, so the sender retransmits until it times out. The refusal is
  real and only legible in the **counter on the refusing side**. [Lesson 55](../lessons.md); runbook
  §S2 and §C2 corrected.
  **AND THE RUN PROVED TWO THINGS 6.1 DID NOT ASK FOR.** The proxy's access log carries
  `10.90.0.2 CONNECT checkip.amazonaws.com:443 200 TCP_TUNNEL` — a **per-device** address, which is
  4.7's no-masquerade exemption and 4.11's log working together, end to end, for the first time. The
  NAT table confirms it from the other side: the `RETURN` rule for `10.31.160.0/24` counted exactly
  the user's two connections.
  *The original step follows:*
- **6.1 — [user] Measure the tunnel from a client**: the `.conf` changes **only** its `DNS =` line (to
  `VPC-Networking`'s `.2`); the `Endpoint` is unchanged because the address moved with it. Then
  `runbooks/vpn.md` §C's three checks, plus a fourth: `curl https://1.1.1.1` **times out**, and
  `curl -x proxy.awsds.internal:3128 https://checkip.amazonaws.com` prints the **proxy's** EIP.
- **6.2 — [user] Close the shadowing**: from the tunnel, `dig agent.datazone.us-west-2.api.aws` and
  `dig <domain-id>.studio.us-west-2.sagemaker.aws` return **public** addresses, and the SMUS portal opens
  with **no** Chrome Local Network Access grant. That is Lesson 43's repair and the reading that retires the
  interim.
- **6.3 — MEASURED 2026-09-06, AND IT IS FOUR READINGS RATHER THAN TWO — but NOT over SSM, and
  not from a Workloads probe.** Two things the step assumed turned out not to hold. **The probes
  carry no IAM role at all** — they report to `/dev/console`, read with `get-console-output`, which
  is why they work in a tier with no SSM path; so the readings were added to the **peering probe's
  user data** rather than driven over Session Manager, which makes them repeatable instead of
  ad hoc. And **there is no Workloads probe and cannot be one today**: that VPC has no interface
  endpoint, by 5.5's deliberate refusal, so a host there would have no management path. The mirror
  is taken from `VPC-SharedServices` instead (the buildbox, at 5.8): `http://10.32.0.10/` → **403**.
  From the Sandbox spoke, on the console:

  | reading | result | what it proves |
  |---|---|---|
  | internet **without** the proxy | silence | **no default route** — design B's core claim, and it is the absence of a thing |
  | an address in `VPC-Workloads`, **through** the proxy | **403** | `http_access deny to_private` fires before every allow: the proxy is **not an L7 bridge** between VPCs that peering deliberately keeps apart |
  | a name on this plane | **200** | the peering, the proxy, and this source CIDR's allow-list |
  | a name on **no** plane | **403** | the allow-list is *enforced*, not merely configured |

  **The refused probes use `http://`**: over `https` a refusal is a CONNECT refusal and `curl`'s
  `%{http_code}` reads **000** — the 403 is where that format string cannot see it.
  **AND IT FOUND A STALE VOCABULARY ROW ON THE WAY, as a TIMEOUT rather than a diff.** The first
  run could not reach the proxy at all: `PROBE_PEERS` still read `{"sandbox": ["production"],
  "development": [...]}` — blind to the peering pass 3 added, and carrying an account name 6b
  retired. Its own comment had predicted *"the reading that will force PROBE_PEERS to name slices
  rather than accounts"*. **Deleted rather than corrected**: `peer_cidrs` is now derived from
  `PEERINGS` via `probe_peer_cidrs()`, so a probe cannot be blind to a peering the matrix has
  (Lesson 33).
  *The original step follows:*
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

- **7.1 — DONE 2026-09-06.** `make hub-up` / `make hub-down`, over
  `./scripts/slices.py up --env production --only vpn,proxy`. `--only` **narrows and never
  widens** — a slice the env already refuses stays refused, with its reason still printed — and it
  is a **closed list**: an unknown name is an error, not a run that quietly does nothing. It
  filters the `[D]` hook as well as the `[E]` loop, which is what makes `hub-up` act on the two
  hosts and **no** endpoint slice. **No `ENV` argument, on purpose**: there is exactly one hub, so
  a parameter with one legal value would be the shape that invites a second nobody meant. Verified
  by dry-run on both directions: `[E] (0)`, both `[D]` hosts named.
  *The original step follows:*
- **7.1 — [Claude] Split the hub's lifecycle**: `make hub-up` / `make hub-down`, over a new
  `./scripts/slices.py up --env production --only vpn,proxy`, so a Sandbox session starts the two hub hosts
  **without** starting GitLab or Production's `[E]` endpoints.
- **7.2 — DONE 2026-09-06, WITH ONE DELIBERATE ASYMMETRY.** A spoke's `make up` reads both hub
  hosts **before** the `[D]` hook and before the first apply — a refusal after either would leave
  the env half-raised — and names the stopped one. **A direct `describe-instances` rather than
  `./aws/vpn.py`**, which the step named: that instrument writes a nine-check report and is what a
  person runs to find out *why* the tunnel is unhappy; this needs one boolean and must not turn
  `make up` into a report generator. The two agree because both find the host by the same Name tag.
  **UNREADABLE is waived, not refused**, and that is the uncomfortable half of Lesson 13: a spoke
  operator may hold no session on Production at all, so a failed read must not make a legitimate
  `make up ENV=sandbox` impossible. A read that **succeeds** and says `stopped` is what stops the
  apply. **All four outcomes exercised** — both running (proceed), proxy stopped (refuse, naming
  it), unreadable (waive with a printed reason), and the hub's own env (never checked, since `up`
  is what starts it).
  *The original step follows:*
- **7.2 — [Claude] Turn the blackhole into an error**: `make up ENV=<spoke>` reads the hub hosts' state
  through `./aws/vpn.py` and **refuses**, naming the stopped host, when either is down.
- **7.3 — DONE 2026-09-06. `./aws/proxy.py`, all five checks, and TWO of them found defects in
  themselves before they found anything in AWS.** Shaped after `vpn.py` deliberately — same
  two-profile default, same typed `--on-host` fence around `ssm:SendCommand`, same "an empty
  answer and a failed answer are different things" discipline — because the two files are the
  instruments for D38's two hosts and a reader who knows one should not have to learn the other.
  **PX-1** `pass`: five rules, all TCP/3128, from the four spoke CIDRs and the tunnel.
  **PX-2** `pass` on **both** sources; the committed template needs no session at all, which
  matters because the answer is most wanted *before* an apply. **PX-3** `pass`: five planes,
  entry for entry. **PX-4** is a **`note`, not a `fail`** — the log group exists with 365 days
  and has no export, and 4.11's second half is an **open decision** (due #4), so a `fail` would
  report a gap the plan is holding open on purpose. **PX-5** `pass`: the proxy's address is in
  `DenyControlPlaneOffVpn` on all six persona sets, `InfrastructureAccess` exempt by decision.
  **The two self-defects, both found by running it** (Lesson 54 again): the per-plane lists are
  an **`include`d drop-in**, not part of `squid.conf`, so reading the two files as one blob made
  the ordering check see `allow` lines after `deny all` and PX-3 see zero planes; and
  `render-squid.sh` spells a plane `production_foundation` where the parameter says
  `production-foundation` (`gsub("-"; "_")`), so the raw keys reported every plane as **both**
  missing and extra. Both are Lesson 53 at its smallest — one intent, two spellings, and a rule
  between them nothing had written down. **PX-2 also decided its verdict from the committed
  template alone while merely printing the running one**, which would have passed a host serving
  a file nobody committed; both sources count now. Negative controls run for PX-2 (an allow moved
  above the deny → `1 allow(s) precede it`; the deny deleted → `no ... line at all`).
  *The original step follows:*
- **7.3 — [Claude] Write the proxy instrument**: `./aws/proxy.py`, read-only by default with an
  `--on-host` flag on the `vpn.py` pattern. Checks: the security group admits only the spoke and tunnel
  CIDRs (`PX-1`); no `http_access allow` precedes the private-destination deny (`PX-2`); the running
  allow-list equals the committed one (`PX-3`, over SSM Run Command); the access log group exists with its
  Log Archive export (`PX-4`); the EIP is the one `identity/sso/` names (`PX-5`).
- **7.4 — DONE 2026-09-06, AND RE-MEASURING FOUND ONE WRONG NUMBER — in the direction that
  flattered a rejection** ([Lesson 7](../lessons.md)). The three rows this step wanted in
  `PRICING.md` were already there from the 2026-09-05 review; re-read against offer files
  republished **2026-08-31**, the `us-west-2` figures held **exactly** (Transit Gateway 0.05 per
  attachment-hour and 0.02/GB, Resolver endpoint **0.125 per ENI-hour**, the same in both regions).
  **`sa-east-1`'s Transit Gateway attachment is 0.09/h, not 0.05** — so the hub-and-spoke this
  estate does *not* build would be ≈ **USD 328/month** there rather than 182. Corrected.
  **`cost-model.md`'s hourly table is REWRITTEN rather than annotated.** The 2026-09-05 repricing
  sat below it as a list of corrections — one intent in two places, which is the shape that drifts
  (Lesson 33) — so the corrections are folded in and the endpoint counts are now **counted, not
  ranged**: Sandbox **18** = 0.180/h, Staging **11** = 0.110, `VPC-SharedServices` **13** = 0.130,
  `VPC-Workloads` **0**. The old `Production egress/` row said *"NAT ~0.050 + endpoints
  ~0.100-0.120"* — a range over a set nobody had counted.
  **`architecture.md` §4.3a's proxy cell now names the shape that EXISTS** — `t3.micro` at
  **0.0104/h**, sized up from `t3.nano` because `dnf` was OOM-killed on 415 MiB — and adds the half
  the comparison kept omitting: **an EC2 proxy charges nothing per GB**, where a NAT gateway adds
  0.045/GB of processing. **Estate-wide the fixed rate fell 0.470 → 0.390/h**; Sandbox's own idle
  floor **rose** 0.160 → 0.180, and that is the only axis on which it rose — break-even against a
  NAT is ≈ **0.57 GB/h**.
  *The original step follows:*
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

**The address and gateway count, which nothing else states in one place** ([D38](../decisions/D38-single-egress-hub.md) §3
carries the full table): this stage takes the estate from **4 Elastic IPs and 3 NAT gateways** (one `[P]`
WireGuard address plus one `[E]` NAT address per `egress/` slice) to **2 Elastic IPs and 0 NAT gateways** —
both addresses `[P]` in `production/networking/`, one of them transferred rather than allocated. Peak during
the cut-over was projected at **3** addresses in Production for one sitting, against a default quota of
five. **Measured 2026-09-06 at 4.2: the peak is 2, and the headroom 4 of 5.** Production held **zero**
Elastic IPs before 4.1 — the projection counted an `[E]` NAT address per `egress/` slice, and those slices
are torn down. The figure that mattered was never the peak but the destination quota, which
`AddressLimitExceeded` enforces at *accept* time; `ET-6` is where it is read.

Measured rates, `us-west-2` (PRICING §7/§8 after 7.4's additions): the design **removes three NAT gateways**
(−0.150/h while a session runs, plus their per-GB processing — 0.045 each plus 0.005 for each one's address) and **adds one Elastic IP** (the proxy's, +0.005/h ≈ 3.65/month) and
one to two private hosted zones, **and one CMK — `alias/awsds-prod-proxy-log`, USD 1.00/key-month
measured (`docs/PRICING.md`), the stage's one line that is neither an address nor a gateway.** It is
the first key in this estate created for a LOG, and the reason is the distinction every other log group
here recorded when it DECLINED one: those are diagnostics, this is the record of what left the estate.
The two `[D]` hosts bill only while running. Interface endpoints stay
per-VPC, single AZ — `VPC-Networking` carries none. Peering is free within an AZ and charged each way
across one, so pinning both hosts and the endpoint sets to `usw2-az1` keeps the common path free. **A
standing NAT gateway is the largest single line the design avoids**, which is why it is a contingency and
not a component. Every figure above is written into `docs/PRICING.md` from a measurement before it is used
in the cost model.

## Decisions due while executing

1. ~~**The optional-endpoint trade for the two enabled blueprint families** (5.3)~~ — **TAKEN 2026-09-06,
   as a fourth shape**: both stay enabled, the ENDPOINTS become a per-apply flag (`GROUPS=bedrock,emr`),
   empty by default. `s3tables` is always-on rather than optional. `make help` documents it.
2. ~~**The `sagemaker.runtime` AZ answer** (5.4)~~ — **TAKEN 2026-09-06: pin the subnets** (free; D9 intact).
3. **INT-16's closing choice** (6.6) — fallback (i) in this estate's condition shape, or recorded
   acceptance.
4. **How the proxy's access log reaches Log Archive** (4.11, opened 2026-09-06 when the rest of 4.11 was
   authored). The requirement is Lesson 18's — the author of the allow-list must not own its record — and
   the group plus its CMK are built; only the *export* is open. Candidates: (a) a CloudWatch Logs
   **subscription filter** into a Kinesis Data Firehose owned by Log Archive, which is continuous and
   carries a per-GB Firehose rate; (b) a scheduled **`CreateExportTask`** to a Log Archive bucket, which is
   cheap and batchy and needs something to schedule it; (c) accept the 365-day in-account retention until
   Stage 11 and record that. **Both rates are measured before the choice, never estimated** (Lesson 6).

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
