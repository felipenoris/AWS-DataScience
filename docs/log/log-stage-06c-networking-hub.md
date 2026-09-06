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
