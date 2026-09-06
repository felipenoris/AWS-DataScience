# Log — Stage 6c — Networking: three VPCs in Production and one egress for the estate

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-06c-networking-hub.md`](../plan/stages/stage-06c-networking-hub.md).*

---

## 2026-09-06 — pass 0 read before it was written, and it contradicted 6b

- **[Claude] Two stages disagreed about `10.40.0.0/16`, and the wrong one had already been copied into
  six files — two of them instruments.** 6b step 4.1 says the freed range is one *"6c step 0 consumes"*;
  6c step 0.2 says it *"is free and stays unallocated"*, and D38's hub is **10.30** (the existing VPC,
  re-labelled), **10.31** and **10.32**, with **10.60** reserved. **The stage that has to BUILD it is the
  correct side** (Lesson 32) — 6b was writing a forward claim about a stage it does not execute.
  - Corrected in `aws/networking.py` (twice — the constant and `NT-3`'s failure text),
    `scripts/tfhygiene/backend.py`, `docs/AWS_STATE.md`, `D20`, `CLAUDE.md`, and 6b's own Status row and
    Deliverables. **The wrong clause is kept and struck at 4.1 rather than deleted**: a sentence copied
    six times is one a reader meets again.
  - **The consequence is that `NT-3`, `NT-5` and `NT-6` stopped having an expiry date.** They measure
    that AWS agrees with the allocation table about a range nobody has claimed, and nothing else in the
    estate measures that at all.
- **[Claude] 0.3 — four ranks, declared before any folder.** `networking` 21, `workloads` 23, `proxy` 41,
  `workloads-egress` 51. **`proxy` at 41 is the load-bearing one**: `up` ascends and `down` descends, so
  it comes up before any `egress` and goes down after — and under D38 there is no NAT anywhere, so a
  spoke with its endpoints up and no proxy has **no internet path at all**.
- **[Claude] 0.2 — one address table, not two, and the deviation was measured rather than preferred.**
  The step asked for a per-VPC table **beside** the per-account `CIDRS`; it **replaces** it. Every reader
  of `CIDRS` was asking a per-VPC question and read per-account only because each account had one VPC —
  and `CIDRS["production"]` has no answer once Production holds three. **The gate is that nothing
  generated changed**, and all three `foundation` slices re-planned `No changes` after the swap.
- **[Claude] 0.7 — the doc gate on the new table.** Rule B's *"no slice on disk"* branch now has two live
  examples where it had none, and `docs/NETWORK.md` already named 10.31 and 10.32 — the address plan
  written down before the code, working.

## 2026-09-06 — 0.4, 0.4a and 0.5

- **[Claude] `vpc-v0.2.0`: a `name_suffix`, because two of the module's names are ACCOUNT-unique.** The
  flow-log log group is a hard create-time conflict; every `Name` tag is what `./aws/networking.py` reads
  to tell objects apart. Security-group *names* are VPC-scoped and would not collide — their tags would.
  Sixteen sites now read one `local.name_prefix`.
  - **The default being harmless is proven, not assumed**: Recipe B step 1's source override planned
    `sandbox/foundation` against the local module before the tag existed — `No changes` — and the
    override was reverted and re-initialised. **The tag was confirmed by asking origin**, not by trusting
    the push.
- **[Claude] 0.4a DEFERRED to 5.1, because the step contradicts itself.** *"Bump in the same sitting"*
  against *"the suffix rides along with the v0.5.0 bump 5.1 makes, so there is one version bump rather
  than two"*. The second wins, and the deferral was checked: `production/egress/` does **not** set
  `dns_firewall`, so none of the firewall-shaped names exists there; what would collide is the NAT pair —
  which **5.1 deletes** — and the endpoint `Name` tags, which cannot arrive before `workloads-egress` is
  applied with endpoints at Stage 9/10. **The window is empty.**
- **[Claude] 0.5 — `VPN_HOMES` gains a slice field, shape only.** Both consumers' `terraform_remote_state`
  keys read `${each.value.slice}` where they hard-coded `foundation`. **The row still points at
  `("sandbox", "foundation")` deliberately** — flipping it now would make `identity/sso` read an empty
  state and `DenyControlPlaneOffVpn` would deny every call from every network. Both consumers re-plan
  `No changes`.

## 2026-09-06 — pass 1: three VPCs, two of them new

- **[Claude] 1.1 applied.** `production/foundation` is **VPC-SharedServices**: `8 to add, 13 to change,
  8 to destroy`, re-plan `No changes`. The two readings that decide it: **`s3_gateway_endpoint_id` is the
  pre-apply value**, and both peerings are still `active` under the **same `pcx-` ids**. The eight
  replacements are the same class 6b step 4.4 measured on Staging.
- **[Claude] 1.2 applied.** `production/networking`, `30 to add, 0 to change, 0 to destroy`, re-plan
  `No changes`. Free at rest — no NAT, no interface endpoint, no Elastic IP. **Its `peers` input was
  dropped from `variables.tf`**: 3.1's matrix is the map it will need, and a declared input nothing
  consumes is what tflint rejects.
  - **"The estate's ONLY IGW route" is the TARGET, not today's reading.** Measured after the apply:
    **four** exist — Production 2, Sandbox 1, Staging 1 — and **pass 5** removes the spokes'.
- **[Claude] 1.3 applied, and it needed a module capability 0.4 did not add.**
  `aws_route.public_internet` was **unconditional**. `vpc-v0.3.1` adds `public_internet_route`; the
  gateway is still created when it is false, so *"is this VPC private?"* is a question about a **route
  table** rather than about which branch of a module ran. **`29 to add` against the hub's 30 — the
  difference is exactly that route.** Read back from AWS: `awsds-prod-workloads-public` returns **0** IGW
  routes, `awsds-prod-networking-public` returns **1**.
  - **A tag was burned.** The `git commit` failed its hooks, the failure was swallowed by a `| grep` on
    the same command line, and `git tag` ran anyway — `vpc-v0.3.0` is on origin pointing at the wrong
    commit. The runbook forbids force-moving a pushed tag, so **v0.3.0 is abandoned** and the release is
    **v0.3.1**. Second time this session that piping into `grep` hid an exit code.
- **[Claude] 1.3a written, and "empty" took an override the module says never happens.**
  `extra_services = []` alone still left the module's **`core_services` default — eight interface
  endpoints, ~0.080/h, for a VPC nothing runs in.** That variable reads *"Overridden never"*, written
  when every egress slice served a VPC people work in. **This slice is the case it did not anticipate**;
  both lists are empty and the plan now reads *"without changing any real infrastructure"*, which is what
  makes `usd_per_hour = 0.0` honest. `egress_mode = "B"` from birth — it never passes through the shape
  5.1 converts away from.
- **[Claude] The instruments absorbed two new VPCs without an edit.** `./aws/networking.py`:
  **`0 check(s) FAILED`**, with `NT-2` and `NT-7` iterating five VPCs and `NT-5` comparing five pairwise.
  `NT-8` never asked Production for *"the single non-default VPC"* — it resolves against the two
  single-VPC accounts — which is the one place that assumption could have broken and did not.

## 2026-09-06 — the rest of the stage reviewed before it runs, and 6d with it

*Claude, at the user's request. No AWS act in this entry.*

- **[Claude] Three checks are corrected BEFORE being written, and all three are the same failure 6b's
  `DT-8` arrived as.** A check written to its final expectation, in a stage that reaches that expectation
  four passes later, is red the whole way — and a check that is red for four passes is a check nobody
  reads on the fifth.
  - **1.5** — *"fails on any IGW route outside that tier, in any account"*. **Three exist today** and they
    are Stage 3's, removed at pass 5. It needs `deploytargets.py`'s `built` shape: an unconverted spoke is
    a **note**, a converted spoke that grows a route back is a **failure**. The signal for "converted" is
    the absence of its NAT gateway.
  - **2.4's `NT-12`** — the zone matrix. 2.6 retires the old zones *"after pass 6 measures the new ones"*,
    so **both families coexist for passes 2-6** and a matrix equality check fails on every surviving old
    association. Either the old family is a dated expected exception, or the check is written at 2.6.
  - **3.7's `NT-11`** — *"every active peering has a route on both sides"* is false **between 3.4 and
    3.5**, in the one place mid-pass where an operator most needs a trustworthy reading. *"Declared but
    not yet routed"* and *"routed to something not in the matrix"* are opposite findings and must not
    share a verdict.
- **[Claude] 3.1 inherits two things from 6b, and one of them is a peering this project worked to keep.**
  The matrix **retires Staging ↔ `VPC-SharedServices`** — Staging keeps only Staging → `VPC-Networking`,
  and INT-09 re-homes onto Sandbox ↔ `VPC-SharedServices`. That is the peering 6b step 4.5 preserved
  through a `for_each` rename with five `moved {}` blocks. **Preserving it was still right**: the
  alternative was destroying it mid-conversion with no replacement, and INT-09 rides on it until this
  step. Those five blocks become **dead** at 3.1 and should be deleted by the commit that restructures
  the file they live in, as `identity/sso/moved.tf` says of itself at 4.9.
- **[Claude] 5.7 owns a question 6b deferred to it.** `dns-allowlist.py`'s Staging row was **retargeted,
  not dropped**, because `staging/egress/main.tf` still declares `dns_firewall = true` — a check whose
  scope shrank while the thing it measures did not is Lesson 31. 5.7's *"it stays in every **compute**
  VPC"* is the sentence that decides it, and Staging carries the SageMaker runtime. **The `.tf` and the
  instrument row move in one commit either way.**
- **[Claude] 4.7 checked for the collision this stage has hit twice — and there is none.** The
  `wireguard` module builds exactly two names, `awsds-<env>-vpn` and `awsds-<env>-vpn-health`; a proxy
  slice builds `awsds-<env>-proxy-*`. Different stems, no collision, no bump. **Measured rather than
  assumed, and written down so the question is not re-opened at the keyboard** — which is what 0.4's
  short list cost an hour earlier.
- **[Claude] Stage 6d needs no correction from these findings, and the reason is structural**: its
  prerequisite row already says *"6c pass 5 — what a Studio app can reach changes there, so any
  measurement below taken earlier would have to be retaken"*, and every one of its steps is a measurement
  rather than a build. Its exposure is the opposite of 6c's: not a check written too early, but a
  reading taken too early. **The one thing to carry into it** is that `production/workloads-egress/` now
  exists with **both** service lists empty — 6d step 4.6's *"carry the network shape forward to Stage
  10"* is about that slice, and the MWAA endpoint set (`logs`, `monitoring`, `kms`) is what fills it.

## 2026-09-06 — pass 2 begins, and step 1.1 turns out to have broken both spokes

- **[Claude] THE FINDING OF THE SITTING, and 1.1's own gate could not have caught it.** Step 1.1 renamed
  Production's VPC `Name` tag from `awsds-prod-vpc` to `awsds-prod-shared-vpc`. **Both spoke slices
  resolve the accepter's VPC BY THAT TAG** — `data "aws_vpc" "production"` in
  `sandbox/foundation/peering.tf` and `staging/foundation/peering.tf` — so from the moment 1.1 applied,
  **neither spoke could apply at all**: `Error: no matching EC2 VPC found`.
  - **The VPC id never changed**, which is exactly why 1.1's gate — *"any id in the replacement list stops
    the step"* — was blind to it. What moved was a **name another account resolves by**, and no id-shaped
    check sees that. This is Lesson 3 from the far side: a fact that moved invalidates the sentence that
    cited it, and the citation lived in a different account.
  - **It also says my deferral of 0.6 was wrong.** 0.6 sits in pass 0 for this reason; I moved it to 3.1
    because the peering *list* belongs with 3.1's matrix. **The list can wait for the matrix; the peer
    LOOKUP cannot wait past the rename that breaks it.** The smallest half of 0.6 — a `name_suffix` field
    on the `peers` map, and a lookup that builds the tag from it — was pulled forward and applied.
  - **How long it was broken, and how it surfaced:** the whole window between 1.1's apply and this fix.
    It surfaced because a *later* apply failed, not because anything checked — and it nearly did not
    surface at all: the first attempt ran `apply … >/dev/null 2>&1`, which swallowed the error and left
    two zones silently uncreated. **Third time this session that redirecting or piping output hid a
    failure**, and the previous two cost a burned git tag.
- **[Claude] 2.1 and 2.3 applied**: `awsds.internal` and `awsds-pages.internal`, both owned by
  `production/foundation/`, `2 to add`, re-plan `No changes`. **Pages keeps its own apex by decision** —
  a `pages.awsds.internal` child would put user-published content under the same registrable parent as
  the platform's names, and a cookie scoped to that parent would be readable by it. That separation is
  the entire reason D36 gave Pages an apex; the rename keeps the project prefix without weakening it.
- **[Claude] 2.2 applied**: `sandbox.awsds.internal`, `staging.awsds.internal` and `prod.awsds.internal`,
  each in the account that owns it, one `to add` each. **All five carry `ignore_changes = [vpc]` from the
  first apply**, which is load-bearing rather than tidy: 2.5 reverses the direction so the *zone owner*
  authorizes and Production associates `VPC-Networking`, and without it every later plan in the owning
  account would try to remove what Production added.
- **[Claude] Read back: eight zones across three accounts** — the five new ones plus `prod.internal`,
  `pages.internal` and `sandbox.internal`, which **2.6 retires after pass 6 measures the new ones**.
  Zones cannot be renamed, so the two families coexist by construction — the window 2.4's `NT-12` was
  corrected in advance to tolerate. Both peerings still `active`.
