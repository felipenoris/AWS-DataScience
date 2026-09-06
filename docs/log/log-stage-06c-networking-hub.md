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

## 2026-09-06 — pass 2 finished: the INT-22 matrix, measured rather than asserted

- **[Claude] 2.5 applied in three commits' worth of work, and the matrix reads back EXACTLY as
  documented** — from `route53 get-hosted-zone` in each owning account, not from the code that built it:
  `awsds.internal` **5**, `sandbox.awsds.internal` **2**, `staging.awsds.internal` **2**,
  `prod.awsds.internal` **3**, `awsds-pages.internal` **2**.
- **[Claude] Three shapes of association, and the third is what 2.5 is actually about.**
  - **Same account** — five of them. There is no authorization to make: the pair is a *cross-account*
    protocol, and within one account the VPC owner simply associates. `production/networking/` takes the
    apex, Pages and `prod.awsds.internal`; `production/workloads/` and `production/foundation/` take one
    each.
  - **Cross-account, original direction** — `awsds.internal` into the two spokes. **One line of change**:
    the apex joined `local.zones` in `peers.tf`, and the `setproduct` and two `for_each`es that already
    existed generated two authorizations and two associations. That is what the map shape bought.
  - **Cross-account, REVERSED** — the two child zones into `VPC-Networking`. The spoke **owns** the zone
    now, so the zone owner authorizes and the VPC owner associates: the opposite of every other
    cross-account association in this estate. Both halves sit in `production/networking/` through aliased
    providers — the same trick `peers.tf` uses for the peering accepters — which keeps a two-account
    handshake inside one readable apply. **The authorization is kept in state** although AWS recommends
    deleting it, the same divergence `peers.tf` records, and for the same reason: it is what makes the
    destroy order expressible.
- **[Claude] The `peers` input's scope moved TWICE in one day, and that is written where it lives rather
  than hidden.** At 1.2 it was narrowed to `foundation`, because the hub had no consumer and a declared
  input nothing consumes is what tflint rejects. At 2.5 the hub got one — the reversed authorizations
  need a profile per account to act as each zone owner. 3.1 replaces the *shape* with the peering matrix;
  the need survives.
- **[Claude] 2.4's first half done, second half deferred on purpose.** The matrix is in `docs/NETWORK.md`
  with the measured counts beside the expected ones. **`NT-12` is not written yet**, and the review three
  entries above says why: 2.6 keeps the old zone family alive through pass 6, so an equality check
  written now fails on every surviving old association. It goes at pass 6, where it is true the first
  time it runs.

## 2026-09-06 — pass 3 begins: the matrix declared, and the same-account half of it built

- **[Claude] 3.1 / 0.6 — the peering matrix is one list in `backend.py`, and both sides of every row
  are generated from it.** `PEERINGS` holds five `(requester account, requester slice, accepter account,
  accepter slice)` rows; `peerings_of()` projects it onto a slice **with that slice's role in each**, and
  the generated `peerings` input carries the far end's CIDR, profile, env token and name suffix. Until now
  each half was hand-written in its own file with nothing tying them together — which is what made a
  requester and an accepter able to disagree about which peerings exist (Lesson 14).
  - **`production/foundation` holds both roles**, requester toward the hub and accepter from Sandbox, and
    the projection produces exactly that. It is the case a "one row per slice" shape would have hidden.
  - **The absences are written into the table as prose**, with the trigger for adding one: *a shared
    service consumed at RUNTIME rather than at deploy time*. Deployment is an API act — the runner
    assumes a role across the account boundary and artifacts travel as ECR images, CodeArtifact packages
    and S3 objects, each through an endpoint in the **target's own** VPC. **The internal CA is not a
    trigger**: D36 issues no CRL and runs no OCSP responder, by decision.
  - **The row that left**: `("staging", "foundation", "production", "foundation")`. Stage 3 built it and
    6b preserved it through a `for_each` rename with five `moved {}` blocks. **Preserving it was right** —
    the alternative was destroying it mid-conversion with no replacement, and INT-09 rode on it until
    here. Staging now reaches only the hub, for the proxy.
- **[Claude] 3.4, the same-account half — applied, and `same_account` selects the SHAPE.** A peering
  inside one account is **one resource with `auto_accept`**, not the requester/accepter pair every
  cross-account row needs, and the generated field is what the code branches on rather than a human
  remembering which is which. `production/workloads → networking` and
  `production/foundation → networking`: **9 resources each** (one peering, eight subnet-scoped routes),
  both `active`, named `awsds-prod-workloads-to-networking` and `awsds-prod-shared-to-networking`.
- **[Claude] And the half a peering does not work without: the hub's RETURN routes.** `12 to add` —
  three tables (both private, plus **public**, because the proxy and the VPN host live in that tier) ×
  four requester private subnets. Read back per table: **4, 4, 4, and `isolated` 0**. The isolated table
  gets nothing, which is what makes it isolated.
  - **An attachment with no route is the defect this file exists against**, and the reference
    implementation this project keeps as a comparison has exactly it: a peering `active` that carries no
    traffic because one side's route table was never told. **It looks correct in every console view that
    shows peerings and in none that shows routes** — which is why 3.7's `NT-11` checks both sides rather
    than the connection.
  - **Routes are subnet-scoped on both sides, never `10.31.0.0/16`.** A whole-VPC route grants reach to
    every tier the peer will ever add — including its public one, the only tier in the estate with an
    internet gateway in front of it.

## 2026-09-06 — pass 3, the cross-account half: six peerings, and three self-inflicted findings

- **[Claude] The two spoke requesters and the hub's accepters applied.** Six peerings now stand, all
  `active`: the matrix's five — `networking-from-sandbox`, `networking-from-staging`,
  `workloads-to-networking`, `shared-to-networking`, and `awsds-prod-from-sandbox` (INT-09) — plus
  `awsds-prod-from-staging`, **the one 3.1 retires**. Peering routes read back **14 in Sandbox, 12 in
  Staging, 52 in Production**, and `./aws/networking.py` is clean: `NT-3` over **147** routes, `NT-6`
  over **6** distinct peerings, `NT-5` across five VPCs.
- **[Claude] THREE THINGS WENT WRONG AND EACH ONE TAUGHT SOMETHING THE PLAN DID NOT SAY.**
  - **A backgrounded `terraform plan` with a missing variable waits on stdin forever and HOLDS THE STATE
    LOCK.** I added the `peerings` input and did not regenerate the spokes' tfvars; the plan then prompted
    for the value, in a background task with no terminal, and sat for eleven minutes. The symptom
    everywhere else was `Error acquiring the state lock` on a completely different command. **`-input=false`
    turns that hang into an error**, and every plan and apply in this stage carries it from here.
    Two locks were force-unlocked after confirming no `terraform` process held them.
  - **`one()` raised on Sandbox's peerings, and the error caught what a wider filter would have BUILT.**
    Sandbox requests **two** cross-account peerings — the hub, and the INT-09 one to VPC-SharedServices
    that Stage 3 built and `peering.tf` still owns by hand. Selecting on `!same_account` alone matched
    both; had the expression tolerated two, the slice would have declared **a second Terraform resource
    for a connection that already exists in the same state, in a different file.** The filter is now
    scoped to the hub row, and folding INT-09's in is a `moved {}` block rather than a rewrite — its own
    commit, because the connection is live.
  - **A subnet in another account cannot be read with this account's credentials, and the plan says so in
    AWS's words rather than Terraform's**: `no matching EC2 Subnet found`, which is truthful about the
    account it asked. Providers cannot be iterated, so the cross-account subnet reads are one block per
    peer — the same split `peers.tf` documents, arriving one layer down.
- **[Claude] And one defect I created and then closed in the same sitting**, which is worth recording
  because it is exactly what this pass's own check exists for: the spoke requesters applied **without
  forward routes**, so for one commit each peering read `active` in every console view that shows
  peerings and **carried nothing**. That is the reference implementation's defect, self-inflicted. Eight
  subnet-scoped routes per spoke closed it — to the hub's **private and public** tiers, because the proxy
  and the WireGuard host live in the public one; the hub's **isolated** tier is never a destination.

## 2026-09-06 — the documentation reviewed against what this session cost

*Claude, at the user's request. No AWS act in this entry.*

- **[Claude] Five lessons added (46-50), and every one of them is a habit rather than an insight** —
  which is what makes them worth the file. Four were paid for in this session, in wall-clock time and in
  one abandoned git tag:
  - **46 — a redirected or piped command hands you the PIPE's exit code.** Three instances: a
    `git commit … | grep` swallowed a hook failure and the `git tag` on the same line burned a published
    version; `apply … >/dev/null 2>&1` lost two hosted zones silently; `commit && echo pushed` reported a
    success that had not happened. **The habit: never chain a consequential act onto a filtered command.**
  - **47 — a process waiting on stdin looks exactly like a slow one, and the lock it holds moves the
    symptom somewhere else.** Eleven minutes, diagnosed backwards from `Error acquiring the state lock` in
    an unrelated slice. **`-input=false` is the whole fix** and now sits in the runbook's Recipe A, on
    both `plan` and `apply`.
  - **48 — a name another account resolves by is a cross-account contract, and no id-shaped gate sees it
    move.** Step 1.1's gate was *"any id in the replacement list stops the step"*; every id was unchanged
    and two accounts broke anyway. **The trigger to recognise: a rename of anything selected by tag, name,
    alias or path.**
  - **49 — a comment saying a knob is never turned is a claim about the callers that existed when it was
    written.** `core_services`' *"Overridden never"* was true of every VPC people work in and stopped
    being true when a VPC with no workload arrived. Its premise expired; the comment never changed.
  - **50 — a check written to a stage's FINAL expectation is red for every pass until that stage ends.**
    **Four instances in two days** — `DT-8`, and 6c's `1.5`, `NT-12` and `NT-11`, the last three caught
    *before* being written. Three acceptable exits (a discriminator, writing it at the pass that makes it
    true, or a dated exception) and one that happens by default: ship it red and hope somebody remembers.
- **[Claude] The Terraform runbook gained three things**, each with the date and the incident: `-input=false`
  on Recipe A's plan and apply, the lock-recovery order (**look for a live process before force-unlocking**
  — orphaned and running produce identical text and opposite correct actions), and a guard in Recipe B
  step 3 requiring `git log --oneline -1` between the commit and the tag.
- **[Claude] `CLAUDE.md`'s Current position rewritten** to 6c's real state, under the 8 KB budget: three
  VPCs, five zones with the measured matrix, six peerings, the module tag situation, and the two habits
  (46 and 47) that cost this session time.

## 2026-09-06 — 3.1's retirement, and a structural thing the two matrices were hiding

- **[Claude] The estate now holds EXACTLY the matrix's five peerings**, read from AWS:
  `networking-from-sandbox`, `networking-from-staging`, `workloads-to-networking`,
  `shared-to-networking`, `awsds-prod-from-sandbox`. `awsds-prod-from-staging` is gone —
  `0 to add, 0 to change, 9 to destroy` on the accepter side, `1 to destroy` on the requester's.
- **[Claude] THE ZONE MATRIX AND THE PEERING MATRIX WERE ONE LIST, and this step is where they had to
  part.** `peers.tf`'s `local.peer_vpc_ids` served both: who this VPC peers with, **and** whose VPC
  Production's zones are associated into. That worked while the two answers were the same set — and 3.1
  makes them different, because **Staging keeps the apex association and loses the peering.** It reaches
  the hub for the proxy and has no business in VPC-SharedServices, but it still has to resolve
  `gitlab.awsds.internal` (INT-22).
  - **Left as one list, the retirement would have destroyed Staging's apex association too**, silently,
    inside a plan whose headline was about peerings. The split is `local.zone_vpcs` beside
    `local.peer_vpc_ids`, and the plan then read `9 to destroy` with **no zone resource in it** — which
    is the confirmation.
  - **A DNS association is not a path**, and conflating the two lists is what hid that they could differ.
    A VPC that resolves a name it cannot reach gets an ANSWER and then a timeout — a better failure than
    NXDOMAIN and a worse one than a refusal.
- **[Claude] The five `moved {}` blocks of 6b step 4.5 were deleted in the same commit.** They renamed
  `development` to `staging` in five addresses, they applied, and the state has held the new addresses
  since — a migration record whose `from` can no longer exist anywhere. **Two of the five named addresses
  this commit destroys outright.**
- **[Claude] 3.6 — `NT-4` re-cut, and deliberately BEFORE the change it will have to tolerate.** It read
  *"10.90.0.0/24 in no route table anywhere"*; step 4.7 adds exactly one, inside VPC-Networking's public
  table, and that route is what stops the WireGuard host masquerading traffic bound for the proxy — which
  is what gives the access log a per-device address without any logging change. The check now **passes
  that one and fails every other**, naming the hub in its verdict.
  - **Widening a check before the change is safe; narrowing it afterwards is a rubber stamp** (Lesson 50
    read the other way). A check edited in the same sitting as the change it would have failed on is a
    check nobody trusts again.
  - **The hub is identified by its CIDR, not by a hard-coded id or a tag** — 10.31.0.0/16 is what
    `VPC_CIDRS` allocates to `(production, networking)`, and `NT-5` already fails if any other VPC
    answers to it, so a mis-identification here is a failure there first.

## 2026-09-06 — pass 3 closes: the INT-09 fold, by address change and not by rebuild

- **[Claude] The last hand-written peering joined the matrix, and the plan is the evidence it was an
  ADDRESS change**: **`0 to add, 2 to change, 0 to destroy`** — both connections updated **in place**,
  and the only attribute that moved was a `Name` tag (`awsds-sandbox-to-prod` → `awsds-sandbox-to-shared`,
  which is what the peer is now called). Without the `moved {}` blocks Terraform reads a singleton
  becoming one row of a `for_each` as a **different resource**: destroy and re-create. **A peering
  re-created comes back `pending-acceptance`, with every route on both sides pointing at an id that no
  longer exists** — on the connection INT-09 rides.
- **[Claude] One assertion was added rather than an assumption.** A provider cannot be iterated, so one
  alias serves every requested row — correct only while all peers live in one account.
  `one(distinct([...peer_profile]))` is that assertion written down: the day a spoke peers into a second
  account it raises **at plan time** instead of silently using the wrong credentials. The same expression
  raised for a good reason one commit earlier, which is what put it there.
- **[Claude] Pass 3 is closed. All five peerings come from the matrix; none is hand-written.**
  `production/foundation` re-plans `No changes`, `make check` is OK, `./aws/networking.py` reads
  `0 check(s) FAILED` over 5 VPCs.
  - **One reading nuance worth recording rather than chasing**: `NT-6` says *"6 distinct peering(s)
    read"* while five are active. AWS keeps a deleted peering visible for a while, and the check counts
    what it read. For a check whose question is *"does any peering touch 10.40?"* that is the
    conservative direction — it would rather examine a corpse than miss a live one — so it is left alone.
- **[Claude] And `peers` was SUPERSEDED, not trimmed** — the tflint hook is what surfaced it. That map
  answered *"which VPC-bearing accounts are there, and how do I reach one"*; `peerings` now answers it
  precisely, per row, with the role and the far end resolved. The spokes moved onto `peerings` the moment
  their peering files became generated, so the only consumers left are Production's two slices, whose
  **aliased providers** need a profile per peer account — and providers cannot be iterated. **When that
  constraint is gone, so is this map.** Both spokes re-plan `No changes` after the removal.

## 2026-09-06 — session audit: what the log was missing, and what the plan owed

*Claude, at the user's request: re-read the whole sitting against the record.*

- **[Claude] One event had not reached this file: `account_folder`.** A VPC slice needs the folder its
  state keys are built from **only if it has a sibling in the same account to read**, and until 6c a
  `foundation` never did. The first version emitted it to all five VPC slices; **tflint said
  `declared but not used` in both spokes**, which is the same "declared but not consumed" rule that
  removed `peers` from those slices two commits later, arriving from the other direction. The emission is
  now conditional on the account holding more than one VPC — a condition, not a list, so Stage 14's vend
  needs no edit.
- **[Claude] Five documents lagged the build and were brought up, which is the half of "review the plan"
  that is not about the plan at all:**
  - **`docs/AWS_STATE.md`** said *"Exactly three VPCs exist"*. **Five do.** The row now carries the
    measured IGW-route reading — `networking-public` **1**, `workloads-public` **0** — and states plainly
    that *"the estate's only internet gateway"* is the **target**, because the spokes keep Stage 3's until
    pass 5.
  - **`docs/plan/cost-model.md`** priced **three** private zones. **Eight stand**, five permanently:
    +USD 2.50/month steady, +4.00 during the window step 2.6 closes. **Held back from the Floor range**,
    which that row's own standing instruction requires — recompute the whole range at Stage 12 step 5,
    from the invoice, never one row at a time.
  - **`docs/plan/integrations.md`** — INT-09's re-homing is **done** (and the connection it now rides was
    folded into the matrix without being re-created); INT-21 is **half built** (the peerings exist, the
    proxy does not, and the distinction is Lesson 44's); INT-22 is **built and measured**.
  - **`D36`** — the Pages apex survived the consolidation as a separate registrable parent, and the
    amendment records *why* rather than only *that*.
  - **`terraform-live/README.md`** — Production is now **the only account with more than one VPC**, which
    is the reason two vocabularies became keyed by (account, slice).
- **[Claude] `docs/plan/conventions.md` §6 needed NOTHING**, and that is worth recording as the one place
  the plan was ahead of the code: the 2026-09-05 re-scope authored `networking/`, `workloads/`, `proxy/`
  and `workloads-egress/` into the slice tree before any of them existed. **Every document that had to be
  corrected describes the estate as DEPLOYED; the one that describes it as DESIGNED was already right.**
  That is the split those files are for, working.

## 2026-09-06 — the lessons re-read, and one shape that had no name

- **[Claude] Lesson 51 added: two intents sharing ONE list.** It is **Lesson 33's mirror and the more
  dangerous half.** 33 warns that one intent enforced in two places diverges; this is two intents enforced
  in one place, which never diverges and is wrong differently — **it cannot express a difference the
  design later requires**, so the first change that needs one takes it from both. `peers.tf`'s
  `local.peer_vpc_ids` named who a VPC peers with **and** whose VPC its zones are associated into; those
  were the same set for three stages. **Left conflated, 3.1's retirement would have destroyed a zone
  association nobody was thinking about, inside a plan whose every line was about peerings** — correct
  under review, wrong in effect. The test that finds it in seconds: name each consumer and ask whether a
  row could ever be true for one and false for the other.
- **[Claude] Lesson 3 gained a forward pointer to 48**, because 48 is its quieter half: the resource need
  not move at all — its **name** moving is enough, when another account resolves it by tag rather than by
  id.
- **[Claude] The Terraform runbook gained Recipe E step 5b: `moved {}`.** It recurred **three times**
  across 6b and 6c and the cost varies by three orders of magnitude — a renamed `aws_route` is cheap, a
  renamed **peering accepter deletes the peering**, and a renamed **SSO assignment revokes access**,
  including once the assignment the operator was signed in through. The step carries that table, the gate
  (`0 to add, 0 to destroy` for everything the blocks cover), the one exception worth taking deliberately
  (a key embedding a `[P]` id cannot get a block without pasting that id into a tracked file), and the
  expiry rule.
- **[Claude] Six lessons from one session is unusual and the reason is worth stating**: five of the six
  are **habits about the tools** — the shell, the lock, the tag, the comment, the check's timing — rather
  than facts about AWS. This session's expensive moments were nearly all self-inflicted and cheap to
  prevent, which is exactly the class of thing a lessons file exists to stop repeating.

## 2026-09-06 — pass 4 opens: the hub's `[P]` anchors, and the preflight for an address that may not change

- **[Claude⚡] Step 4.1 applied — `production/networking/hub-anchors.tf`, `6 to add, 0 to change, 0 to
  destroy`** as the infrastructure user on `Production Account` through `InfrastructureAccess`. What now
  exists: the WireGuard security group `awsds-prod-vpn` (UDP/51820 world-open and **nothing else** — no
  `vpc_nat_cidrs` rule, since the isolated-tier NAT job dies with the buildbox at 5.8), the proxy group
  `awsds-prod-proxy` (TCP/3128 from the four spoke ranges plus the tunnel, and no other source), the
  **empty** host-key container `awsds-prod-vpn-host-key` with the same value-read deny the Sandbox one
  carries, the proxy's `[P]` Elastic IP, and the allow-list parameter. `tflint` clean, `checkov`
  **0 failed / 11 skipped**, `make check` OK.
- **[Claude] The apply FAILED the first time, on a naming rule this repository has carried since
  2026-08-16.** `PutParameter` on `/awsds/prod/proxy/allowlist` answered `AccessDeniedException: No
  access to reserved parameter name` — Parameter Store reserves every name beginning with `aws` or `ssm`,
  case-insensitive, and `awsds` begins with `aws`. **`conventions.md` already documents this exact
  collision and already prescribes `/datascience/<env>/…`**; the failure was not consulting it. Five of
  the six resources had already been created, so the correction was a one-resource re-plan.
  **What the fix cost, and why it is written here rather than shrugged off:** nothing but a minute — and
  that is precisely what makes it worth recording. The rule was measured once, written down in the file
  the routing table names for "a naming, layout, Terraform or IAM rule", and then not read at the moment
  it applied. **The mitigation is a comment at the only site in the repository that writes an SSM
  parameter**, so the next one does not rediscover it, plus the constraint named in step 4.10 itself.
- **[Claude] `VPN_HOST_SLICE` added to the vocabulary, and it is Lesson 51 arriving on schedule.** The
  hub needs the tunnel range `10.90.0.0/24` — the proxy's group must admit it, and 4.7's route must send
  it at the WireGuard host — and an address literal may sit in no `.tf` file (Stage 3 decision 1). The
  tidy-looking move was to flip `VPN_HOMES` to `("production", "networking")` and read the range from
  there. **That would have been a total lockout**: `identity/sso/` and `data-governance/data/` turn each
  `VPN_HOMES` row into a `terraform_remote_state` read of the home's Elastic IP, which does not exist in
  the hub until 4.6, so `DenyControlPlaneOffVpn` would have denied every call from every network. The two
  questions — *whose address does the deny pin to* and *which slice builds the tunnel* — were one list
  for three stages because they named the same slice, and **pass 4 is the sitting in which they must
  differ**. They are now two names; `VPN_HOMES` moves at 4.12, on its own schedule.
- **[Claude] Two things the step's own text got wrong, corrected in the plan rather than worked around.**
  4.1 lists `wireguard_eip_public_ip` among the outputs it applies — it cannot: the address is
  *transferred*, so the resource behind that output arrives with 4.6's `import {}`, and declaring it here
  would mean allocating a second address (the risk table's fallback, not the plan). And the step ordering
  carried **two steps numbered 4.7**; in a plan whose own heading says step numbers are identifiers, that
  is the identifier failing at its only job. The collision note is now **4.6a**.
- **[Claude] Step 4.2 written and run: `./aws/eip-transfer.py`, read-only, both accounts.** Registered in
  `aws/INDEX.md`. **Six of seven checks pass; `ET-2` fails because the Sandbox host still holds the
  address — the expected reading before 4.4**, stated in the file's own header so exit 2 is not read as a
  defect (Lesson 50). The four documented refusals are all measured: `PublicIpv4Pool=amazon` (not BYOIP,
  IPAM or CoIP), `PtrRecord` unset, border group `us-west-2`, and **4 of 5 Elastic IP slots free in the
  destination**.
- **[Claude] Why that file exists at all, in one sentence:** two of the four refusals are raised **in the
  destination account at ACCEPT time**, after `enable-address-transfer` has already succeeded — so the
  failure mode is not *the call errored* but *the call succeeded and the wrong thing is now pending in
  another account*, with a **seven-day** clock AWS notifies nobody about.
- **[Claude] Two measurements that correct the stage's own cost paragraph.** Production held **zero**
  Elastic IPs before this apply, so the cut-over peak is **2**, not the projected 3 — the projection
  counted an `[E]` NAT address per `egress/` slice, and those slices are torn down. And the figure that
  actually matters was never the peak but the **destination quota**, which `AddressLimitExceeded`
  enforces at accept time; `ET-6` is where it is read.
- **[Claude] The blackout is smaller than the plan assumes, measured rather than hoped.** The Sandbox VPN
  host has been **stopped since 2026-08-26** with the address still associated — which is exactly what
  `runbooks/vpn.md` §S says `make down` leaves behind. So the tunnel is already down: pass 4 interrupts
  nothing that is currently running, and the "one sitting with a blackout" constraint is about the
  *transfer's* seven-day window, not about a live outage.
- **[Claude] A third plane the allow-list forgot.** Step 4.9 enumerates four sources — tunnel, Sandbox,
  SharedServices, Workloads — and **omits Staging**, a peered spoke with a runtime of its own. The
  parameter therefore derives its planes **from the peering matrix** instead of transcribing that
  paragraph, so a spoke the security group admits can never be one the allow-list has never heard of.
  Every plane starts empty, which is the safe default: Squid's last line is `http_access deny all`, so an
  empty list denies by name rather than by timeout.
- **[user] Step 4.3 is the next act and it is yours alone** — copying the host key from the Sandbox
  container into the Production one. It is the one act in pass 4 that cannot be undone by re-running
  anything: the key is what keeps every client's `PublicKey =` line valid, and a fresh key is a silent
  re-issue of every peer on top of an account move.

## 2026-09-06 — 4.7 through 4.11 authored while the AWS side waits, and what rendering caught

The user was away from the machine and asked what could be advanced. Everything in pass 4 that is
**authoring** was: the module bump, both hub `[D]` slices, the proxy's whole configuration, and the
two filters. **Nothing was applied**, and one plan that is ready was deliberately left unapplied.

- **[Claude] `wireguard-v0.5.0` — the three changes 4.7 names, and a fourth the design forced.**
  `vpc_nat_cidrs` is **gone** rather than renamed (the NAT job dies with the buildbox at 5.8, and
  `sandbox/vpn/` stays pinned at v0.4.0 until 4.13 — a git tag is what makes a removal safe).
  `forward_destinations` restricts the tunnel to the private address space; `no_masquerade_cidrs`
  exempts chosen DESTINATIONS from the masquerade so Squid sees `10.90.0.x`. The fourth: the
  `source_dest_check` trigger had to move from the removed input to the new one — the argument for
  the attribute did not change, only what turns it off.
- **[Claude] THE TIDY VERSION OF THE NO-MASQUERADE RULE WOULD HAVE TAKEN THE TUNNEL'S DNS DOWN, and
  this is the finding of the sitting.** "Do not masquerade traffic staying inside the hub VPC" reads
  better than the rule that shipped and is wrong: the VPC resolver at `.2` is inside the VPC range
  too, and the Amazon DNS server answers requests coming from within the VPC's own addresses — a
  packet arriving with a `10.90.0.x` source is not that. Exempting the VPC CIDR would have left every
  tunnel client unable to resolve anything, with a symptom pointing anywhere but at a masquerade rule.
  **The narrow, correct answer is the PUBLIC SUBNETS**, where the proxy actually is.
- **[Claude] Three defects that only a render could find, and they are the argument for rendering.**
  (i) `+` in HCL is **arithmetic**: `join(...) + "..."` answered `Unsuitable value for left operand: a
  number is required`. (ii) `%{` is `templatefile`'s **directive marker** and collides with Squid's
  `strftime` escape in `logformat` — and then collided a second time with the **comment I wrote to
  explain the first collision**, because a comment is text like any other line. (iii) The render
  script's rollback deleted the new file while the previous one had already been overwritten — "a
  rollback that has nothing to roll back to is not a rollback". A template that has never been run is
  a claim, not an artefact.
- **[Claude] The whole `squid.conf` is written by Terraform, not a drop-in in `conf.d/`.** The ORDER
  of `http_access` rules is the entire security property of that file, and where a distribution's
  stock configuration places its `include` relative to its own `http_access allow localhost` is a fact
  about a package version that nobody here can verify from a laptop ([Lesson 30](../plan/lessons.md)).
  Owning the file makes the order readable, diffable and ours. The same reasoning normalised the ACL
  names: plane keys carry a hyphen, Squid's ACL-name syntax is untestable from here, so `gsub` removes
  the assumption rather than betting on it.
- **[Claude] The DNS-firewall list is TRANSLATED, not copied — the two syntaxes disagree.** Route 53
  DNS Firewall: `example.com` is the apex only, `*.example.com` is subdomains and not the apex. Squid
  `dstdomain`: `example.com` is that exact host, `.example.com` is the domain **and** every subdomain.
  So a DNS-firewall pair collapses to one Squid entry, and transcribing the asterisks would have
  produced entries matching nothing — a refusal indistinguishable from a missing name. **The literal
  `"*"` that opens the old list is dropped**: every entry after it was decoration while it stood, and
  this is the first time the estate's egress is actually enumerated.
- **[Claude] Splitting the filters bought a narrowing that was invisible before.** `.cloudfront.net`
  — every CloudFront distribution in the world — is what the console's asset delivery needs. Under one
  shared DNS-firewall list the notebooks had it too. It is now in the **tunnel** plane only, and the
  code carries a comment saying it was narrowed rather than forgotten.
- **[Claude] The build hosts' list is DERIVED from the notebook list, not retyped** (minus the AWS
  control plane a build host does not call): the day somebody adds a package source for notebooks, a
  build of that image needs it too, and two hand-kept copies would part company on exactly that day
  ([Lesson 33](../plan/lessons.md)). The rendered parameter is **1751 bytes** against Parameter
  Store's 4 KB Standard-tier ceiling, and a plan-time precondition now says so.
- **[Claude] A second precondition catches the failure the merge would swallow.** The planes come from
  the peering matrix; the LISTS are authored by hand against the same keys. Misspell one — `staging`
  for `staging-foundation` — and the lookup silently returns empty: the parameter applies clean, the
  spoke gets nothing, and the symptom reads exactly like a name nobody added.
- **[Claude] The access log is `[P]`, in `networking/`, with a CMK — the first key in this estate
  created for a log.** Every other log group here declined one on the same arithmetic (USD 1/key-month
  against a *debugging* log); this one takes it because it is not a debugging log but the record of
  what left the estate. Retention is **365 days** and 4.11 named none — every other group is 30 days
  because every other group is a diagnostic. Both are now in the stage's cost table and in
  `docs/PRICING.md`.
- **[Claude] The proxy gets a status-check alarm that 4.8 did not ask for.** When the tunnel dies one
  person notices in seconds; when the single exit dies, every automated thing in four accounts loses
  the internet at once with no obvious symptom. `treat_missing_data = "breaching"` so "somebody
  stopped it and forgot" is visible. It has no action wired, which is honest about D12 rather than
  pretending.
- **[Claude] Two guards on one hole, deliberately.** A forward proxy fetches URLs on behalf of others,
  so `169.254.169.254` is denied as a *destination* in `to_private` — a client must not be able to ask
  the proxy for this host's role credentials — **and** IMDSv2 is required on the instance.
- **[Claude] Gates that caught real things rather than nodding.** `tflint` found a variable I declared
  and never used; `check-provider-locks` found two slices with no lock file; `check-network-doc` found
  `production/proxy` unnamed in `NETWORK.md`; the region-literal gate found `us-east-1` needing its
  **inline** `# region:aws-pinned` marker (the paragraph above the line does not count) and the word
  `us-west-2` sitting in a variable description. `check-tfvars-shape.py` needed its `ROSTER` constant
  to become a **list** — both rosters exist at once until 4.13, and a gate naming one file would have
  gone on passing about the old one ([Lesson 31](../plan/lessons.md)).
- **[Claude] ONE PLAN IS READY AND WAS NOT APPLIED, on purpose.** `production/networking/` plans
  `3 to add, 1 to change, 0 to destroy` — the log group, its key and its alias, plus the parameter
  filling with the real allow-lists. Nothing reads that group until the proxy exists, so applying it
  early only starts a bill; and pass 4 is one sitting by the stage's own framing.
- **[Claude] 4.11's second half is NOT authored and is now a decision due (item 4).** The export to
  Log Archive has a real mechanism choice — a subscription filter into a Firehose, against a scheduled
  `CreateExportTask` — with different cost shapes, and picking one silently would be an estimate
  standing in for a measurement ([Lesson 6](../plan/lessons.md)).
- **[Claude] `terraform-live/production/vpn/` IS ON DISK AND NOT IN THE COMMIT, and that is the
  runbook's two-commit tag order rather than an omission.** The `terraform_validate` hook inits from
  **origin**, so a module and its first caller cannot share a commit: `wireguard-v0.5.0` has to be
  tagged and pushed before the slice that names it can pass a hook. The hook said exactly that
  (`invalid ref: "wireguard-v0.5.0"`), which is the guard working. The slice lands in the commit after
  the tag. **The push is blocked in this session** (the auto-mode classifier refused it), so both the
  tag and that commit wait on the user.

## 2026-09-06 — the cut-over: 4.3 through 4.6, and the verification the stage could not predict

- **[user] 4.3 — the host key copied by hand**, Sandbox → Production. **[Claude] Verified by DIGEST and
  never by value**: both secrets hash to `5e9163a6…4174f`, the destination carries one `AWSCURRENT`,
  rotation off. Hashing is what let the check be taken at all — the value stays out of every context
  that did not have to hold it.
- **[Claude⚡] 4.4 — the association destroyed on its own**,
  `-target=module.wireguard.aws_eip_association.this`, `0 to add, 0 to change, 1 to destroy`. Worth
  noting the targeted-destroy recipe does not quite cover this case: it is written for *ordering within
  a full destroy*, and here the intent is to remove ONE resource and keep the rest. The plan directs it
  explicitly, which is what makes it sanctioned. **The preflight went 6/7 → 7/7**: `ET-2` cleared exactly
  as its own header said it would.
- **[Claude] I REPEATED LESSON 46 IN THE SAME SESSION, AND THIS TIME ON A WRITE.** The
  `enable-address-transfer` call was written as `aws … | jq '<malformed>'`. The shell returned **jq's**
  exit code; the AWS call had already run. Then the command that would have told me so —
  `describe-address-transfers` — was refused by the harness twice, including through the instrument, so
  the session could not distinguish *the transfer is pending* from *nothing happened* while a
  **seven-day clock AWS notifies nobody about** was possibly running. **The remedy was not a better
  reading, it was a different CHANNEL** (Lesson 24): a plain `describe-addresses`, which was not refused,
  showed Production holding only the proxy address and settled that the accept had not run.
- **[user] 4.5 — the transfer**, `pending` → `accepted` at 20:30:02Z, offer expiry 2026-09-13.
- **[Claude] VERIFICATION 1 ANSWERED, AND THE ANSWER IS NO: THE ALLOCATION ID DOES NOT SURVIVE.**
  `eipalloc-04397bfae0295333d` became **`eipalloc-07edec7a52dc0820a`**. AWS documents it neither way,
  which is why the stage carried it as a question and why 4.6's `import` id was written from a
  **reading** rather than from the plan's prose (Lesson 38). **An allocation id is a per-account fact
  about an address, not a property of it** — anything that had pinned the old id would now point at
  nothing, which is the standing argument for reading `[P]` ids through remote state. **The tags arrived
  empty**, as predicted; the apply re-applied the whole set.
- **[Claude⚡] 4.6, the PRODUCTION half — `1 to import, 3 to add, 2 to change, 0 to destroy`.**
  `production/networking/` owns the address and exports `wireguard_eip_public_ip = 52.89.212.1` — **the
  same address it was in Sandbox, which is the entire point of transferring rather than allocating**: no
  client `.conf` moved. The apply also brought 4.11's `[P]` access log `/awsds/prod/proxy` with its own
  CMK, and filled the allow-list parameter with 4.9's two lists.
- **[Claude] THE SANDBOX HALF IS NOT DONE, AND IT IS A SEQUENCING KNOT THE PLAN DOES NOT NAME.**
  `sandbox/foundation/` now plans **`1 to add`** — measured, not predicted: the resource is still in its
  state, the allocation it names has left the account, so an apply there would allocate a **new** address
  and start billing. Closing it means `removed {}` plus dropping two outputs, and those outputs have
  three readers: `identity/sso/` and `data-governance/data/` (through `VPN_HOMES`), and **`sandbox/vpn/`,
  which needs `wireguard_eip_allocation_id` to EVALUATE — including on its own `terraform destroy`**. So
  the slice 4.13 is supposed to destroy last would become un-destroyable if the output went first.
- **[Claude] What that knot rules in and out, so the next move is a choice rather than a discovery.**
  The consumers are **not** broken today: the outputs still resolve, and `52.89.212.1` is still the right
  address. Flipping `VPN_HOMES` to `("production", "networking")` keeps the `aws:SourceIp` value
  **identical** and swaps only the VPC id and the S3 gateway-endpoint id onto the hub's — which is where
  the tunnel is about to be, so it is ahead of the traffic rather than behind it. What it cannot be is a
  *union*: a two-row `VPN_HOMES` needs Sandbox to keep exporting, which is the thing being removed.
  **And the fallback 4.13 was waiting on died at 4.5** — the Sandbox host has no address and cannot come
  up; what `[D]` promises instead is that it rebuilds from code and the `[P]` secret if the address is
  ever transferred back.

## 2026-09-06 — 4.12's first half: the union, and a recommendation I had to correct first

- **[Claude] I TOLD THE USER A UNION WAS IMPOSSIBLE. IT WAS NOT, AND THE CORRECTION CHANGED THE
  PLAN OF ACTION** — so it is written down rather than quietly fixed. The reasoning that failed:
  a two-row `VPN_HOMES` seemed to need Sandbox's `wireguard_eip_public_ip`, which is the output
  being removed. **What that missed is that a row yields THREE values, not one.** `vpc_id` and
  `s3_gateway_endpoint_id` are the slice's ordinary outputs and do not move with the address. And
  because the address was **transferred** rather than reallocated, both rows answer the *same*
  `52.89.212.1`. So the union costs nothing on the `aws:SourceIp` axis and is purely additive on
  the other two. The step's own warning — *"a single cut-over apply is one typo away from locking
  out all six personas"* — is why the correction mattered rather than being a detail.
- **[Claude⚡] `identity/sso/` — `0 to add, 6 to change, 0 to destroy`**, applied as
  `InfrastructureAccess`, the set that carries no VPN-only deny (open question 17's recovery
  path). **The plan was enumerated key by key before applying, not skimmed**: across all six
  persona sets the diff touches exactly **one** condition key, and only widens it —
  `aws:SourceVpc` goes from Sandbox's VPC to **[Sandbox's, the hub's]**. Nothing that passed
  before stops passing.
- **[Claude⚡] `data-governance/data/` — `0 to add, 5 to change, 0 to destroy`.** Same shape: the
  hub's S3 gateway endpoint is **added** to `aws:SourceVpce` on five documents, and nothing is
  removed.
- **[Claude] The first plan of the union exposed a latent assumption, and it was worth one line
  of code.** `vpn_egress_cidrs` rendered `52.89.212.1/32` **twice** — the local was written when
  one home meant one address, and `sort()` does not deduplicate. Harmless to IAM and exactly the
  kind of noise a later reader has to stop and explain, so `distinct()` went into all three
  list-building locals (both in `identity/sso/`, one in `data-governance/data/`). After the fix
  `aws:SourceIp` **left the diff entirely** — which is the reading that proves the union is
  additive rather than merely looking additive.
- **[Claude] What this does NOT do, stated so the trim is not forgotten:** the union is
  transitional. **Pass 6 removes the Sandbox row**, and that removal is one act with the
  `removed {}` on `sandbox/foundation`'s Elastic IP — in that order, because the second is what
  the first unblocks. Until then `sandbox/foundation/` plans **`1 to add`** and must not be
  applied.
- **[Claude⚡ REFUSED] The `sandbox/vpn/` destroy was planned and not applied** — `0 to add, 0 to
  change, 8 to destroy`, every resource `[D]` and no `[P]` anchor among them. The harness refused
  the apply as a destructive action. It is no longer on the critical path: the union removed the
  reason it had to go first, so it can wait for 4.13 with the trim. The host cannot come up in the
  meantime — its address is in another account.

## 2026-09-06 — a three-and-a-half-hour phantom, and 4.13's first half

- **[Claude] A `terraform plan` from step 3.4 had been hung since 14:17 — LESSON 47, AGAIN, from
  the session before this one.** The user noticed it, not a gate. The command looped over the two
  spokes running `terraform plan -no-color` **without `-input=false`**, piped into `grep`: the
  Sandbox half finished, the Staging half stopped at an input prompt nobody would ever answer, and
  it sat there for **3h33m**.
- **[Claude] What made it safe to kill was measured, not assumed** — three readings, because
  "it's only a plan" is the kind of reassurance that is right until it is not:
  1. It is a **`plan`**, not an apply: it creates, changes and destroys nothing.
  2. **It held no state lock.** Every `.tflock` object in all three state buckets was listed:
     none. It had blocked during *variable evaluation*, which happens **before** the lock is
     taken. **This is the reading that mattered** — the expensive half of Lesson 47 is never the
     stopped process, it is the lock it holds making the symptom surface in an unrelated slice,
     which is exactly how this stage lost time once already.
  3. Its output would have been **stale**: it planned against the `peering-to-hub.tf` it had just
     written, and pass 3 has since replaced that with the generated `peerings.tf`, applied and live.
  `fd 0` on the process was a unix socket — the harness pipe — which is the direct evidence that
  it was waiting on stdin rather than working.
- **[Claude] The guard this suggests is cheap and not yet written**: nothing in the repository
  looks for a `terraform` process older than an hour, or for a `.tflock` with no live owner. The
  runbook says `-input=false` on every plan and apply; a **check** would have found this in
  minutes instead of hours. Recorded here rather than built mid-pass.
- **[user⚡] 4.13's FIRST HALF — `sandbox/vpn/` destroyed, `8 destroyed`**, matching the plan
  exactly (instance, role, its three policy attachments, instance profile, handshake log group,
  health alarm — every one `[D]`, no `[P]` anchor among them). The harness refused this apply to
  Claude as a destructive action, so the user ran it.
- **[Claude] What that leaves standing in Sandbox, and what it changes:** the `[P]` anchors only —
  the security group `awsds-sandbox-vpn`, now **attached to nothing**, and the host-key secret,
  whose value has been copied to Production. Both go with 4.13's second half. **The estate still
  carries two world-open rules**, but one of them now guards no listener at all.
- **[Claude] Still standing, and still deliberate:** `sandbox/foundation/` plans **`1 to add`** and
  must not be applied. The `removed {}` needs the union's Sandbox row trimmed first, and that is
  pass 6's, after the readings.

## 2026-09-06 — 4.7: the tunnel endpoint is in the hub, and the clients cannot tell

- **[Claude⚡] `production/vpn/` applied — `10 to add, 0 to change, 0 to destroy`.** The eight the
  Sandbox slice had, plus the Elastic IP association and the tunnel return route. `wireguard-v0.5.0`,
  `t3.nano`, `usw2-az1`.
- **[Claude] The plan was read attribute by attribute before applying**, because three of them are
  what the whole design turns on and none of them errors when wrong — it just silently does not
  work: `source_dest_check = false` (keyed off the non-empty `no_masquerade_cidrs`); the return
  route `10.90.0.0/24` → the host's ENI in `rtb-0b13c0405057ab331`; and the rendered `PostUp`, with
  the two `RETURN` exemptions **before** the `MASQUERADE` and the `REJECT` **after** the three
  RFC1918 accepts. The subnet and route table were also cross-checked against
  `production/networking`'s own `vpc_id` output rather than trusted from their names — both resolve
  to `vpc-068274f8215e131a6`, which is the hub.
- **[Claude] THE PROOF THAT THE ACCOUNT MOVE IS INVISIBLE TO EVERY DEVICE, and it is two readings
  and not one.** A client `.conf` pins exactly two things:
  - **the address** — `52.89.212.1`, transferred rather than reallocated, now associated with the
    new host (`VP-2`);
  - **the host's public key** — the interface reports
    `LCD1d6xjsxRAmOZA/FTo72TToGUkLYqlOryEJwfup28=`, **byte for byte the value recorded at Stage 4**
    (`runbooks/vpn.md` line 564, `log-stage-04-vpn.md` line 1640).
  The second follows from 4.3's digest match, but it is measured here independently, from the
  running interface, because *"the private keys hash the same so the public keys must match"* is a
  derivation and this is a reading. **No `.conf` on any device needs an edit.**
- **[Claude] The first boot is legible end to end** (`--on-host`, the deliberate `ssm:SendCommand`
  the folder rule allows): packages at 20:56:52, uplink `ens5`, **the key fetched from Secrets
  Manager at 20:57:35 with `base64 length 44`**, `wg0.conf` written for **2 peers**, `wg-quick`
  started, the sampler active, the CloudWatch agent pointed at `/awsds/prod/vpn`. Both peers are
  present with their names (`mbp`, `raspi`) and read `handshake=never` — correct: nobody has
  connected yet.
- **[Claude] `./aws/vpn.py` RE-HOMED IN THE SAME SITTING**, which is what 4.7's plan text made an
  obligation rather than a tidy-up. `VPN_HOME_PROFILE` now reads `awsds-infra-prod`. **Nothing else
  in the file had to move**, and that is `NAME_TAG_PATTERN` earning its wildcard: `awsds-*-vpn`
  matched the old name and matches the new one. A literal there would have been a second edit
  nobody would have found until a check came back empty (Lesson 31).
- **[Claude] `0 check(s) FAILED` — `VP-1` through `VP-9`, both halves of `VP-7`.** One caveat is
  worth stating rather than reading off the table: **`VP-3` says "exactly one world-open rule" about
  the HOME ACCOUNT, and the estate has two** until 4.13's second half removes Sandbox's. That is the
  blind side this instrument has by construction, named in `AWS_STATE.md` and here.
- **[Claude] VERIFICATION 2, HALF ANSWERED AND UNPROMPTED.** The SSM agent registered `Online` from
  the hub's public tier **with no interface endpoint anywhere in `VPC-Networking`** — Session
  Manager reaches this host through the IGW. The proxy is the other half, at 4.8.

## 2026-09-06 — 4.8: the single egress is up, after four defects the apply found and reading did not

`production/proxy/` applied — 9 resources — and then corrected four times. Every one of the four
was invisible to `terraform validate`, `tflint`, `checkov` and a careful re-read; each needed the
thing to actually run. They are written up individually because three of them are reusable.

- **(i) THE ALLOW-LIST DID NOT PARSE, AND THE REASON IS THE TRANSLATION AGAIN.** The first boot
  logged `the rendered allow-list does not parse - reverting` and the proxy came up with an
  **empty** list — safe, and useless. `squid -k parse` on the rendered file named it exactly:
  ```
  ERROR: '.signin.aws.amazon.com' is a subdomain of 'signin.aws.amazon.com'
  FATAL: Bungled ... line 10
  ```
  **The distinction is fine and it is the whole finding:** a *deeper* name under a wildcard
  (`d35uxhjf90umnp.cloudfront.net` under `.cloudfront.net`) is only a **WARNING** — measured, in
  isolation, before concluding — while **the apex beside its own wildcard is FATAL**. Route 53 DNS
  Firewall *required* both forms to mean what Squid's `.x` means alone, so every pair copied from
  that side carries the defect in. Three collisions existed; a scan of all five planes found them
  all in the tunnel plane, and two were fatal.
- **(ii) A PLAN-TIME GUARD FOR THAT CLASS, because it will come back every time somebody adds a
  domain.** A precondition on the parameter now fails the plan when any plane lists `x` beside
  `.x`, naming the offending pairs. The warning-level overlap is deliberately **not** failed - it
  is redundant rather than wrong, and a gate that refuses both would refuse a list that works.
- **(iii) THE RENDER SCRIPT SWALLOWED THE ERROR IT EXISTED TO REPORT.** `squid -k parse >/dev/null
  2>&1` — so the only evidence was "does not parse", and finding out *why* took a hand-run through
  SSM. Squid names the ACL and the entry; that sentence is exactly what a person needs, and State
  Manager surfaces stderr in the association's own failure report. It is printed now.
- **(iv) THE ASSOCIATION RACED THE BOOT, and the argument that put it there was reasoned rather
  than measured.** `apply_only_at_cron_interval = false` was justified in the code as *"the first
  boot already rendered the list, so an immediate run is a no-op, and a no-op that FAILS says the
  association is misconfigured"*. What actually happens: State Manager fires seconds after
  `RunInstances`, while the user data is ~50 seconds into `dnf install`, and the run dies with
  **exit 127, no such file** — not a diagnostic, a certainty, leaving a `Failed` association as a
  working proxy's first impression. **And the fix exposed a second constraint the API only
  volunteers when you try it**: `ApplyOnlyAtCronInterval is not supported for Rate Schedule
  associations`. So the schedule form is decided by the flag — `cron(0/30 * * * ? *)`, the same
  half-hourly cadence at predictable times — and a `validation` block now says so.
- **(v) `t3.nano` IS NOT TOO SMALL FOR THE PROXY, IT IS MARGINAL — WHICH IS WORSE.** The second
  host's `dnf install squid jq amazon-cloudwatch-agent` was **OOM-killed**, with the kernel naming
  it: `Out of memory: Killed process 1941 (dnf)`, on a host reporting **415 MiB** usable. The
  *first* host had installed the same three packages fine. Steady state is irrelevant here — a
  proxy that relays CONNECT and caches nothing would run on a nano forever; **the BUILD is what
  does not fit**, and a coin-flip boot is the wrong property for the estate's single internet exit.
  Moved to **`t3.micro`** at a measured **0.0104 USD/h** (`docs/PRICING.md` §8 — the rate already
  existed, so no new measurement; Lesson 6). `layers.py` carries the new figure.
- **[Claude] One thing that behaved exactly as designed, and it is worth saying because it is the
  reason (v) was recoverable:** changing `instance_type` is a stop/modify/start, and **user data
  does not re-run on that**. The bigger host still had no Squid. `-replace` on the instance is what
  re-runs a first boot — the same act `runbooks/vpn.md` §S6 documents for the tunnel host.
- **[Claude] FINAL STATE, measured inside the host through SSM:** `squid active`, listening on
  `*:3128`, **three** `http_access allow` lines and all six ACLs rendered
  (`src_/dst_production_foundation`, `src_/dst_sandbox_foundation`, `src_/dst_tunnel`), cloud-init
  `status: done`, **zero** OOM kills, 913 MiB total. All three hub slices re-plan **`No changes`**.
- **[Claude] VERIFICATION 2 IS NOW FULLY ANSWERED.** Both hub hosts registered with Session Manager
  from the public tier **with no interface endpoint anywhere in `VPC-Networking`** — the reach is
  the IGW, which is what D38 predicted and what Lessons 40-43 made worth checking rather than
  assuming.

## 2026-09-06 — the second hung process of the session, and it was mine

- **[user] Two background loops had been spinning since 18:16 and 18:18** — the user noticed, again,
  not a gate. Both were `until` loops I wrote during 4.8 to wait for a cloud-init line on instance
  `i-0b047210cbd810913`; **step 4.8's own `-replace` then terminated that instance**, so they were
  asking a corpse for its console output every 15 and 20 seconds, forever. Confirmed before killing:
  the polled instance reads `terminated`, and the proxy's live host is `i-098d91f80fa424ac2`.
- **[Claude] Lesson 52 written, and it is the SHAPE that is wrong rather than the accident.** An
  `until <success>; do sleep; done` has no branch for *the world changed underneath me*, so every
  failure mode — the object gone, the command erroring, the condition unreachable — collapses into
  "not yet". The `Monitor` tool documents the same trap for event filters (*"if this process crashed
  right now, would my filter emit anything?"*); an `until` loop is that question with the answer
  fixed at no. The fix is a second exit and a subject re-read each round rather than an id pasted at
  the top.
- **[Claude] Two hung processes in one session, with UNRELATED causes, is the argument for the guard
  neither incident had.** The first was blocked on stdin for 3h33m (Lesson 47); this one was polling
  a terminated instance. Nothing in this repository looks for a `terraform` process older than an
  hour, a `.tflock` with no live owner, or a poll outliving its subject — and in both cases the
  detector was a person reading a task list.

## 2026-09-06 — 4.12's second half: the proxy's address on the perimeter, and pass 4 closes

- **[Claude⚡] The proxy's Elastic IP joined `aws:SourceIp` on both perimeters** — `identity/sso/`
  `0 to add, 6 to change` and `data-governance/data/` `0 to add, 5 to change`. Enumerated key by key
  again: **the only change is an addition**, `184.33.8.126/32` beside the tunnel's `52.89.212.1/32`,
  on eleven documents.
- **[Claude] Why the PROXY's address is the one that matters now, and the tunnel's is the one that
  stays for safety.** Under D38 a VPN client is a private-network client: its whole internet crosses
  Squid, so a persona's control-plane call leaves the estate wearing the **proxy's** address and
  never the tunnel endpoint's. The WireGuard address stays because the tunnel host still originates
  traffic of its own — and because pass 4's rule is **union first, trim after the readings**.
- **[Claude] `try(..., null)` rather than a direct read, and it is a shape rather than a guard.** A
  VPN home is not required to hold a proxy: Sandbox exports no such output and is still a home while
  the union stands. A missing output there is legitimate, so `compact()` drops the nulls.
- **[Claude] `./aws/vpn.py`: `0 check(s) FAILED`** from the new home, `VP-1` through `VP-9`, and the
  health alarm has moved `INSUFFICIENT_DATA` → **`OK`** now that the host has reported for long
  enough. `VP-7` reads both halves: all six persona sets carry the deny, `InfrastructureAccess` does
  not (open question 17's recovery path, unchanged by the move).
- **[Claude] WHAT PASS 4 HAS LEFT, and both are deliberately pass 6's:** the **trim** — removing the
  Sandbox row from `VPN_HOMES` — and, one act later and only in that order, the `removed {}` on
  `sandbox/foundation`'s Elastic IP that the trim unblocks. Until then that slice plans **`1 to add`**
  and must not be applied, and the estate carries **two world-open rules**, one of them guarding
  nothing.

## 2026-09-06 — the undocumented-AWS section, swept across every stage log

- **[Claude] Lessons 53 and 54 written** — the DNS-Firewall-to-Squid translation, and *validate / render
  / run are three different verdicts*. Both come from pass 4 and neither was recoverable from the plan.
- **[Claude] A second list added to `lessons.md`: "What AWS does that its documentation does not say".**
  It is a different KIND of thing from the lessons and the file says so — lessons are habits, these are
  platform facts that cost a measurement. **Each entry carries what was measured, when, and where the
  reading lives**, because a behaviour recorded without its evidence is indistinguishable from a belief
  (Lesson 37).
- **[Claude] Then swept every stage log — 0 through 6c, ~16k lines — rather than only this session's.**
  Not read linearly: searched for the SIGNATURES this class of finding leaves behind — an error naming
  the wrong cause, a call that answers differently before and after some other act, a field that writes
  and never reads, a bill starting at a state nobody named. **Seven entries came back from earlier
  stages**, the oldest from Stage 1c: `describe-effective-policy` answering `{}` instead of raising;
  a rename with a **measured absence** of propagation delay; `EnvironmentRolePermissionBoundary` being
  write-only; an associated DataZone domain listing from member accounts under the *owner's* ARN; an
  empty `{"items": []}` that is a **success** signal rather than an absence; the three billing states of
  the `Workflows` blueprint; and `DeleteWorkGroup` counting query **history** as contents with no API to
  clear it.
- **[Claude] Two candidates were EXCLUDED and the file names them**, because an admission rule nobody
  can see applied is not a rule: `iam list-roles` omitting `PermissionsBoundary` is a **documented**
  contract, and ECR's `tagPatternList` wildcards are on the page — what was wrong there was *our* claim,
  not the vendor's. Both belong to the files that own them.
- **[Claude] What the sweep says about this project's own record-keeping, and it is the useful part:**
  every one of the seven was already written down, in the log of the stage that hit it, correctly and
  with its evidence. **What was missing was not the finding but the INDEX** — a reader designing around
  an AWS behaviour had no way to know the estate had already measured it three stages ago, short of
  re-reading 16k lines. That is the gap this section closes, and it is the same gap `POLICIES.md` and the
  lake READMEs close for their own subjects.
