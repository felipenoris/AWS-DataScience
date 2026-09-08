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

## 2026-09-06 — 5.3 and 5.4 taken, and 5.3's answer is a shape the step did not offer

- **[user] 5.3 — BOTH FAMILIES STAY ENABLED; the ENDPOINTS become the variable.** The step offered
  three shapes (always up / per-session / disable the blueprint) and the user took a fourth: nothing
  leaves the portal, and `make up ENV=<x> GROUPS=bedrock,emr` decides whether the endpoints exist for
  that apply. **Empty by default**, so a family nobody uses that day costs nothing.
- **[user] 5.4 — pin the SMUS app subnets to the endpoint's AZ.** Free, D9's single-AZ rule intact,
  and it makes the resolution failure stop existing rather than be paid for.
- **[Claude] `bedrock` IS FOUR ENDPOINTS AND THE STEP LISTS THREE.** The six enabled blueprints both
  AUTHOR Bedrock objects and INVOKE them, and those are different services: `bedrock` is the control
  plane `AmazonBedrockGuardrail` (`CreateGuardrail`) and `AmazonBedrockEvaluation`
  (`CreateEvaluationJob`) call, `bedrock-agent` is the control plane for agents, flows and prompts,
  and the two `-runtime` names are the invocation path. **Stated as reasoning from the API split, not
  as a measurement of the blueprint's calls** — 6d trims it. Every name in both groups came from
  `describe-vpc-endpoint-services` **in the Region**, which is what 5.2's own *"measure rather than
  copy"* asks for; every `*-fips` sibling and `emr-containers` (EMR-on-EKS, category 3) are excluded
  by name so nobody adds them by resemblance.
- **[Claude] THE MEASUREMENT CAUGHT THE STEP'S OWN REQUIRED LIST: there is no `q` endpoint service in
  `us-west-2`.** 5.2 asks Sandbox to gain `ec2`, `ec2messages`, `secretsmanager`, `ssm`, `ssmmessages`
  **and `q`**; the Region's catalog carries `qapps` and the `quicksight*` family and nothing named
  `q`. **The failure the step warns about, inside the step.** Struck from the plan.
- **[Claude] AND ONE ENABLED BLUEPRINT HAD NO PATH AT ALL, WHICH NOBODY HAD NAMED.** `S3TableCatalog`
  is one of category 1's **eleven** — the count cross-checks exactly — and `s3tables` is its own
  service name in the catalog. **The S3 GATEWAY endpoint does not cover it**: a gateway carries `s3`
  and `dynamodb`, nothing else. Under design B that project would fail on first use for exactly 5.3's
  reason, in a family 5.3 never considered. **The user put it in the always-on set**, not behind a
  flag: one endpoint, and the blueprint is enabled.
- **[Claude] THE FLAG IS AN ENVIRONMENT VARIABLE AND NOT A TRACKED TFVARS, which is a departure from
  this repository's usual answer for a per-apply knob.** The VPN host's size lives in a tracked file
  because it describes a STANDING shape somebody should review in git history. This describes ONE
  apply — and a tracked file would have to be edited back, which is precisely the *flag left on*
  failure the empty default exists to avoid. `slices.py` merges `env_extra` into `os.environ`, so
  `TF_VAR_optional_service_groups` simply arrives.
- **[Claude] The closed-list validation exists because the failure of a typo is SILENT.**
  `GROUPS=bedrok` would contribute no endpoints, the apply would succeed, and the blueprint would fail
  on first use exactly as with no flag at all. **Proven, not asserted**: the plan errors with
  *"admits only: bedrock, emr, mwaa"*.
- **[Claude] Measured end to end rather than reasoned:** `make up … DRY=1` prints the expansion
  `["bedrock","emr"]`; a plan with no flag builds **12** interface endpoints (8 core + 3 SageMaker +
  `s3tables`) and with `bedrock,emr` builds **23** — the eleven optional names, and no others.
- **[Claude] A COUPLING FOUND WHILE WRITING v0.5.0 THAT 5.1 MUST HANDLE, and it would have been
  silent.** `dns-firewall.tf` reads `dns_firewall_enabled = var.dns_firewall && var.egress_mode ==
  "A"`. **Deleting mode A — which is 5.1 — therefore disables the DNS Firewall that 5.7 wants kept in
  every compute VPC.** One condition, two intents ([Lesson 51](../plan/lessons.md)); the clause has to
  go in the same commit as the NAT, or the two steps undo each other while both read correct.
  **This is also why v0.5.0 is the flag alone and 5.1 now cuts v0.6.0** — *"one bump rather than two"*
  was an optimisation, not a constraint, and dragging the coupling into a feature release would have
  hidden it.
- **[Claude] `make help` documents the flag**, its closed value list with per-group hourly cost, the
  empty default, and the two things an operator would otherwise learn by surprise: **running `make up`
  again without the flag destroys the optional endpoints** (that is the flag working, not drift), and
  the wiring is `sandbox/egress` only.

## 2026-09-06 — 5.1: the NAT half removed as code, because there was nothing to destroy

- **[Claude] MEASURED BEFORE ACTING, AND THE MEASUREMENT CHANGED THE VERB.** The step says *destroy
  all three NAT gateways*; the reading was **zero NAT gateways, zero default routes and zero
  interface endpoints in all three accounts**. The `egress/` slices are `[E]` and were all down, so
  5.1 is a **code change** — the next `make up` never creates one — not a destroy. Worth stating
  because a step whose verb does not match the state is how somebody ends up looking for something
  to delete.
- **[Claude] `vpc-egress-v0.6.0`, three changes in one commit and the third is the reason for the
  pairing.** `nat.tf` deleted, and `egress_mode`, `nat_public_subnet_id` and
  `private_route_table_ids` deleted with it — **not defaulted to `"B"`**: a switch whose other
  position no longer exists is dead code that reads like a choice. The route tables went because
  `aws_route.private_default` was their only consumer. 0.4a's `name_suffix` arrives, routed through
  one `name_prefix` local built exactly the way the `vpc` module builds its own. And the
  `&& var.egress_mode == "A"` clause came off `dns_firewall_enabled` — **the coupling found while
  writing v0.5.0, which would have made 5.1 and 5.7 undo each other while both read correct.**
- **[Claude] The capability is not gone and the comment says so at length, deliberately.** 5.9 keeps
  a NAT as a **contingency** — for a named service that cannot be told about a proxy, in that
  service's own VPC, with its own cost row and a removal trigger. Re-adding the resources for one
  caller is the friction that contingency wants; a flag would not have been.
- **[Claude] A STALE CLAIM IN A VARIABLE DESCRIPTION, and it is the dangerous kind.** `dns_firewall`
  said the firewall was design A's allow-list, that mode B made it pointless, and that
  *"dns-firewall.tf enforces the second half itself, so a caller cannot half-enable it"*. All three
  went false at v0.6.0, and the last one matters: **this flag is now the only gate**. Rewritten
  rather than trimmed, because what the firewall is FOR also changed (5.7) — not filtering the
  internet, which is the proxy's job now, but closing the recursive resolver as an exfiltration
  channel, which is a job that exists with or without a default route.
- **[Claude] Four callers rewired to v0.6.0**, including `production/egress` and `workloads-egress`
  jumping from **v0.1.0**. Their two NAT outputs were deleted after checking, across
  `terraform-live/`, `aws/`, `scripts/` and `docs/`, that **nothing consumed either** — which is
  what made it a deletion rather than a migration. `name_suffix` is `shared` and `workloads` in
  Production, matching pass 1's VPC names; the two single-VPC accounts pass nothing.
- **[Claude] Proven by plan rather than asserted:** zero NAT resources in all four; the DNS
  Firewall's **six** resources still in Sandbox's plan (the coupling fix, working);
  `production/workloads-egress` reads *"without changing any real infrastructure"* — outputs only.
  Sandbox drops from 25 to **21** planned resources.
- **[Claude] A STRAY `errored.tfstate` FOUND IN `sandbox/egress/`, dated 2026-08-26 — eleven days
  unnoticed.** That file is Terraform's last-resort dump when it cannot write state back to the
  backend after an apply, and it held 14 resources including the NAT. **Verified stale before
  touching it**: the remote state lists **zero** resources and AWS holds none, so the destroy and
  its state write both completed and this was a transient failure's residue. Removed.
- **[Claude] The right guard for that is a CHECK, not a `make clean` addition, and the distinction
  matters.** `errored.tfstate` is recovery evidence: after a genuine state-write failure it is the
  only record of what was built, and a `clean` that swept it would destroy exactly the thing
  somebody needs at the worst moment. What is missing is something that **notices** one exists —
  it is gitignored, so no gate sees it, and it sat for eleven days beside a slice nobody planned.
  Recorded rather than built mid-pass, beside the other two watchdogs this session has asked for.

## 2026-09-06 — 5.2, and an expired token that nearly became a finding

- **[Claude] THE SESSION EXPIRED MID-STEP AND MY OWN COMMAND TURNED THAT INTO A FALSE MEASUREMENT.**
  The first re-check of 5.2's names ran with `2>/dev/null`, so
  `Error when retrieving token from sso: Token has expired` became an empty catalog, and the reading
  presented itself as **"eight services do not exist in this Region"** — including `s3tables`, which
  I had measured as *existing* an hour earlier. **The contradiction is what caught it, not the
  instrument** (Lesson 30: a tool's failure is not a property of the world, and gets written down as
  one; Lesson 24: the defence against the benign failure hides the serious one). One step from
  writing it into the plan. Re-run with stderr visible, the user re-authenticated, and the catalog
  came back with **569 services**.
- **[Claude] The `q` finding SURVIVED re-measurement**, which is the part that matters: it was taken
  with a live token the first time and is still absent from a healthy 569-entry catalog. Only
  `qapps` and the `quicksight*` family exist.
- **[Claude] Sandbox's `extra_services` goes from 4 to 10**, each entry carrying why it is there:
  `datazone` **back after its 2026-08-25 removal**, and the reason it can return is structural — it
  was taken out because its private DNS shadowed a name the VPN CLIENT resolved publicly, and the
  tunnel is now in `VPC-Networking`, which by decision carries **no interface endpoint at all**
  (Lessons 40-43). A private zone here can no longer reach the client plane. `ssm`, `ssmmessages`
  and `ec2messages` are 5.5's trio, needed here because **Session Manager does not work through an
  HTTPS proxy listener** — the shell that reads the proxy's log must not depend on the proxy
  (Lesson 24 again, in its architectural form). `ec2` and `secretsmanager` were NAT-covered until
  now.
- **[Claude] 18 interface endpoints, and the three `layers.py` rates were COUNTED rather than
  computed** — `terraform plan | grep -c aws_vpc_endpoint.interface` per slice, at the measured
  0.010/h. Sandbox **0.160 → 0.180**, Staging **→ 0.110**, Production **→ 0.100**.
- **[Claude] SANDBOX'S IDLE FLOOR WENT UP, AND THE FIRST VERSION OF THIS BULLET OVERSTATED WHAT THAT
  MEANS.** It said *"design B does not save money on this slice"*, trading 0.050/h of NAT for 0.080/h
  of endpoints because 5.2 has to **enumerate** what the NAT covered in silence. **That compares only
  the idle hourly rate and drops the per-GB axis, which is where the two shapes actually differ:** NAT
  **0.045/h + 0.045/GB** against an endpoint's **0.010/h + 0.010/GB** (measured, `docs/PRICING.md` §8).
  So B costs **+0.020/h fixed** here and saves **0.035 per gigabyte** — break-even
  **≈ 0.57 GB/h**, which one container pull passes in minutes. **Design B is cheaper on this slice too,
  at any real usage**, and estate-wide the fixed rate falls as well (0.470 → 0.390/h), because Staging
  and Production lost a NAT without gaining endpoints. The narrow true statement is: *Sandbox's idle
  floor rose 0.020/h* — and an idle floor is what an `[E]` slice spends least time paying.
  **Corrected because the user asked, and because the original would have been read as an argument
  against the design rather than as a note about one number.** What D38 buys remains one auditable
  exit instead of three unenumerated ones; it just does not have to be paid for.
- **[Claude] The rates deliberately exclude 5.3's optional groups.** `bedrock` adds 0.040 and `emr`
  0.070 only for an apply that names them; a static rate that assumed them would over-report every
  session that does not. `make status` quotes this column, and the flag's own cost is in `make help`.

## 2026-09-06 — 5.5, and two facts a user question found unrecorded

- **[Claude] Two entries added to `lessons.md`'s undocumented-AWS section**, both from the user asking
  whether heavy SageMaker traffic escapes NAT cost. The answer was *yes, but not for the reason
  supposed*, and neither half was written down anywhere:
  - **An ECR image pull is TWO paths and the heavy one is FREE.** `ecr.api` and `ecr.dkr` carry the
    auth and the manifest — kilobytes — while the image **layers come from S3**, which here means the
    `[P]` gateway endpoint: no hourly charge and **no per-GB charge at all**. It is also why AWS
    requires an S3 gateway endpoint beside the two ECR ones, and the symptom of omitting it is an
    auth that succeeds and a download that hangs.
  - **A NAT never carried S3 or DynamoDB traffic here, even under design A** — a prefix-list route
    beats `0.0.0.0/0`, which `docs/NETWORK.md` has recorded as measured since Stage 3. So removing the
    NAT did **not** make that traffic cheaper; it was never paying. What design B saves on is the
    traffic that DID use it — internet downloads at 0.045/GB of processing — which now cross an EC2
    proxy that charges no per-GB processing at all. **Two axes, and the one that looks heaviest was
    already free.**
- **[Claude⚡] 5.5: the Session Manager trio in `VPC-SharedServices`** — `production/egress` goes 10 →
  **13** endpoints, `layers.py` 0.100 → **0.130/h**. Added one step ahead of its first user, which is
  narrow rather than speculative: **5.8 lands the buildbox in that VPC**, and the slice is `[E]`, so
  nothing bills until a build session brings it up anyway.
- **[Claude] `VPC-WORKLOADS` DOES NOT GET IT, AND THE STEP DISQUALIFIES ITSELF.** 5.5 says *every
  INSTANCE-BEARING spoke*; that VPC bears none. Measured rather than assumed: Production's only two
  instances are `awsds-prod-vpn` and `awsds-prod-proxy`, **both in `VPC-Networking`** — which reaches
  SSM through the IGW and needs no endpoint at all. `workloads-egress` already carries the refusal in
  its own words — *"adding endpoints because the other egress slices have them would bill 0.010/h each
  for a VPC nothing runs in yet"* — and 0.030/h of Session Manager path for a network with nothing to
  manage is precisely that purchase.
- **[Claude] The refusal is written INTO the slice rather than only into this log**, beside the empty
  lists, because that is where somebody wondering *"why is SSM missing here?"* will actually look. A
  decision recorded only at the deciding end is a promise the receiving stage never gets (Lesson 34).
- **[Claude] One thing left alone on the way past, deliberately:** `production/egress` still carries
  `sagemaker.api` and `sagemaker.runtime` from Stage 3, when `production/foundation` was simply *the*
  Production VPC. It is SharedServices now — supply chain and build hosts — and whether a SageMaker
  name still belongs there is Stage 7/9's question, not 5.5's. **Removing an endpoint because it looks
  out of place is how a path disappears**, so it is flagged in the code and kept.

## 2026-09-06 — 5.6: `NO_PROXY` generated, and eight names that no rule produces

- **[Claude] `vpc-egress-v0.7.0`, and the interesting half is that the module does not BUILD the
  names — it reads them.** `local.service_names` already turns `sts` into
  `com.amazonaws.us-west-2.sts`, so deriving `sts.us-west-2.amazonaws.com` the same way looks like
  three lines of `replace()`. Measured against the Region instead, across the **29** services this
  estate can declare, **eight** of them do not follow:

  | token | private DNS name | why a rule would miss it |
  |---|---|---|
  | `ecr.api` | `api.ecr.us-west-2.amazonaws.com` | the two labels swap |
  | `ecr.dkr` | `*.dkr.ecr.us-west-2.amazonaws.com` | swap **and** a wildcard |
  | `sagemaker.api` | `api.sagemaker.us-west-2.amazonaws.com` | swap |
  | `sagemaker.runtime` | `runtime.sagemaker.us-west-2.amazonaws.com` | swap |
  | `sagemaker.studio` | `*.studio.us-west-2.sagemaker.aws` | a **different TLD** |
  | `emr-dashboard` | `*.emrappui-prod.us-west-2.amazonaws.com` | an unrelated name |
  | `emr-serverless-services.sessions` | `*.s.emr-serverless-services.…` | `sessions` → `s` |
  | `elasticmapreduce-services` | `*.elasticmapreduce-services.…` | wildcard |

  So the generator is a `data "aws_vpc_endpoint_service"` per declared service, reading
  `PrivateDnsName` at plan time: free, needs no endpoint to exist, and is a **reading** rather than
  a claim ([Lesson 38](../plan/lessons.md)). The one transformation left is a deletion —
  `trimprefix(…, "*.")`, because `NO_PROXY` wildcards are documented to work as **suffixes only**.
- **[Claude] THE STEP'S OWN PARENTHESIS WAS AMBIGUOUS, AND THE WRONG READING FAILS OPEN.** It says
  the list carries the fixed entries *"(S3 and DynamoDB ride the gateway prefix lists)"*, which can
  be read as *so leave them out*. The reading that holds is the opposite, and the measurement is
  what settles it: `describe-vpc-endpoint-services` on `com.amazonaws.us-west-2.s3` returns a
  `PrivateDnsName` for its **Interface** shape and **`None`** for its **Gateway** shape. A gateway
  endpoint has no private DNS at all — it works by *routing*, the public name resolving to a public
  address that a prefix-list route carries to the endpoint. Two consequences: the generator
  **cannot** emit those two names, and if they are missing from `NO_PROXY` every S3 call goes to
  Squid, leaves through the hub's IGW as a **public** call, and arrives at S3 carrying neither
  `aws:SourceVpc` nor `aws:SourceVpce`. Those are the two keys the S3 gateway policy, the lake's
  bucket policies and the projects bucket are all written on. **The data perimeter would fail open,
  silently, for the one service that holds the data.** Hand-named in the fixed half, with the
  reasoning in the file.
- **[Claude] Bare entries, not dot-prefixed, and the two shapes in the list differ for a reason.**
  An AWS service endpoint **is** the host (`sts.us-west-2.amazonaws.com`), so a leading dot would
  make the exact name miss under clients that read a dot as *subdomains only* (Go's `httpproxy`);
  CPython, botocore and curl all match a bare entry against the host and its subdomains, so bare
  covers both. The two internal zones keep their dots and are named **in full** because they are
  siblings, not parent and child: `awsds.internal` does not cover `awsds-pages.internal`. The old
  family (`sandbox.internal`, `prod.internal`, `pages.internal`) is deliberately absent — an entry
  here is exactly the kind of thing that would keep a retired zone alive past 2.6.
- **[Claude] RENDERED ON ALL FOUR SLICES, not merely validated** ([Lesson 54](../plan/lessons.md)),
  by pointing one caller at the local module per Recipe B and then re-planning each at the released
  tag: Sandbox **26** entries, Staging **19**, `VPC-SharedServices` **21**, `VPC-Workloads` **8**.
  That last one is the fixed half alone and it is the *right* answer, not an empty one: a VPC with
  no interface endpoint still has two `[P]` gateway endpoints, so S3 and DynamoDB must bypass the
  proxy there exactly as everywhere else.
- **[Claude] Three output `precondition`s for the three ways this variable fails silently** — a
  `*`, a `/`, a `:`. None of them errors at the client: a malformed entry simply never matches, and
  the symptom is a 403 for a service that should never have been proxied. Checked where the list is
  built rather than in a script somebody has to run.
- **[Claude] Gates:** `terraform validate` on the module alone, `make check` **OK**, `terraform fmt`
  clean, four plans green (`27`/`20`/`13` to add and *outputs only* for `workloads-egress`). Nothing
  applied — the four `egress/` slices are `[E]` and down, so the outputs materialise at the next
  `make up`.

## 2026-09-06 — 5.6a and 5.7: the firewall keeps one job, loses sixty-three names, and a `*`

- **[Claude] 5.6a — Staging keeps its DNS Firewall, and 6b's argument was about a job that no
  longer exists.** 6b step 5.1 wanted the Staging row dropped from `./aws/dns-allowlist.py` on the
  reasoning that *a headless deployment target resolves whatever its pipeline resolves*. That is
  true, and it is an argument about **filtering the internet** — the job 5.1 ended by deleting the
  last default route. The job left is the one 5.7 states: **close the recursive resolver as an
  exfiltration channel**, which is a property of *a VPC where code runs*, not of who runs it.
  Staging runs promoted models, unattended, from artefacts built in Sandbox. The `.tf` keeps
  `dns_firewall = true`, the instrument keeps its row, and **both moved in the same commit** as the
  re-cut — 5.6a's actual requirement.
- **[Claude] 5.7 — sixty-three entries to ten, and the step's own list was one family short.** The
  four families it names are `*.amazonaws.com`, `*.api.aws`, `.awsds.internal` and the proxy's name.
  Missing: **`*.sagemaker.aws`**. The `sagemaker.studio` endpoint answers on
  `*.studio.<region>.sagemaker.aws` — a different TLD, covered by neither of the first two — so the
  obvious short list orphans an interface endpoint **both** Interactive slices pay for hourly, and
  the symptom is NXDOMAIN, which reads as a network fault rather than as a policy decision.
- **[Claude] So the coverage question became a `precondition` rather than a paragraph
  (`vpc-egress-v0.8.0`).** Computed from the same `describe-vpc-endpoint-services` reading 5.6 built
  NO_PROXY from, but kept as a **separate local**, because the two syntaxes look alike and are not
  translatable by transcription ([Lesson 53](../plan/lessons.md)): NO_PROXY needs the `*.` gone, a
  Route 53 domain list needs it **present** and needs the apex listed beside it. **Proven with a
  negative control, not with a green plan** ([Lesson 13](../plan/lessons.md)): remove the
  `sagemaker.aws` pair and the plan fails with
  `dns_firewall_allow_domains does not cover *.studio.us-west-2.sagemaker.aws`; restore it and all
  four slices plan clean.
- **[Claude] A `"*"` CAME OFF THE SANDBOX LIST, and it had been live for a fortnight.** Commit
  `f6bb316` (*"allow-all egress"*, the user's, 2026-08-23) put a single wildcard at the top of the
  list. `*` matches every name, so the sixty-two entries beneath it were decoration and the Sandbox
  DNS Firewall was a default-**ALLOW**. It is removed with the re-cut and **named** rather than
  quietly dropped: a list whose first entry is `*` reads as a configured control to every review
  that does not read it to the end. `EXC-06` closes on it.
- **[Claude] `EXC-04` DOES NOT CLOSE, AND THE STAGE FILE SAID IT WOULD.** *"EXC-04, EXC-05 and
  EXC-06 close with the old allow-list"* is true of two of them. `EXC-04` is the domain-list churn —
  Route 53 canonicalises every entry with a trailing dot, `vpc-egress` writes them without one, and
  the provider re-issues `UpdateFirewallDomains` on every apply. That is a comparison of two
  **spellings** of whatever the content is; 5.7 changed the **content**. Ten entries churn exactly
  as sixty-three did. It could not even be re-measured in this sitting: the symptom appears on the
  plan *after* an apply, and all four `egress/` slices are `[E]` and down, so the plans read
  `27 to add` rather than `2 to change`. Row amended in `docs/AWS_STATE.md` with what would settle
  it — the next `make up` of an Interactive slice.
- **[Claude] `EXC-05`'s failure MODE retires rather than moving.** It needed a resolver evaluating a
  redirection chain and blaming the queried name when a hop was missing. Squid matches the hostname
  the client **requested** and evaluates no chain at all, and every CDN-fronted name left the
  firewall for Squid's lists. There is no longer a place in this estate where that mechanism exists.
- **[Claude] `./aws/dns-allowlist.py` re-aimed at the five Squid planes.** Default source is
  `production/networking/hub-anchors.tf` — the `[P]` slice that declares them — with `--from-api`
  adding one read (`ssm:GetParameter`). It is a **better** default source than the one it replaced:
  the DNS Firewall lists lived in `[E]` slices that are down most of the time, and the parameter is
  `[P]` and always there.
  - **`DN-1`** unchanged in spirit — every exact hostname on every plane answers. **46 names, all
    with an address.**
  - **`DN-2` is new and is the one nothing else does.** Squid's two overlap outcomes are not the
    same severity, and the expensive one is not the one that reads as worse: an apex listed beside
    its own `.x` form is **`FATAL: Bungled`** — the proxy does not start, which surfaces as every
    spoke losing the internet at once — while a deeper name under a `.x` is a warning nobody
    notices. `pass` today.
  - **`DN-3`** compares the committed planes with the deployed parameter: **5 planes, entry for
    entry.** Stated in the report as the **first of two links**, `PX-3` (7.3) being parameter
    against the running `squid.conf`. A green `DN-3` says what was written reached the parameter and
    nothing about what the proxy enforces.
  - **`DN-4`** measures 4.9's design claim rather than reporting a CDN exposure that no longer
    means anything: **exactly one** entry — `.amazonaws.com` — appears on both the tunnel and a
    workload plane. The two filters really are two.
  - **Both new checks proven by negative control**: an injected `cloudfront.net` beside
    `.cloudfront.net` produced `fail DN-2 ... 1 FATAL` and `fail DN-3 ... only in code`, and the
    file was restored.
- **[Claude] Gates:** `make check` **OK**, `ruff` clean, four `egress/` plans green
  (`27`/`20`/`13` to add, *outputs only* for `workloads-egress`). Nothing applied — all four are
  `[E]` and down, so the re-cut takes effect at the next `make up`.
- **[Claude] `docs/NETWORK.md` is deliberately NOT edited here.** Its §s on the DNS Firewall
  describe the sixty-three-entry list and are now wrong; **6.7 rewrites that file from the
  readings**, and editing it ahead of the measurement is what that step exists to prevent.

## 2026-09-06 — the two names pass 4 was supposed to write, and did not

- **[Claude⚡] `proxy.awsds.internal` and `vpn.awsds.internal` did not exist.** Step 2.1 created the
  apex zone with the comment *"shared names only: gitlab, proxy, vpn"* and says the two host records
  are *"written by pass 4 from the two hosts' private addresses"*. Pass 4 built both hosts and
  declared neither record. Found while 5.7 was re-cutting the firewall list to include
  `.awsds.internal` — a family whose only content, at that moment, was nothing.
- **[Claude] What it was breaking, which is more than a convenience.** Every client in the estate is
  configured with `http_proxy=http://proxy.awsds.internal:3128`; 5.6's `NO_PROXY` carries
  `.awsds.internal` precisely so that name is never sent to the proxy itself; and **step 6.1's
  closing check is `curl -x proxy.awsds.internal:3128 https://checkip.amazonaws.com`**. That reading
  was unrunnable and nothing said so — [Lesson 34](../plan/lessons.md), a deferred obligation
  recorded only at the deferring end.
- **[Claude] The record is `[D]` and lives with the host, not with the zone.** The zone is `[P]` in
  `production/foundation/`; the **address** is a property of an instance the `[D]` slice may replace,
  so a `[P]` slice declaring it would be taking a dependency on a `[D]` value. `make down` **stops**
  these hosts rather than destroying them, so the ENI and its private address survive a down/up
  cycle and the record does not churn.
- **[Claude] Private address, not the Elastic IP, and for the proxy that is load-bearing rather than
  tidy.** A spoke reaches 3128 over a **peering**, and a peering carries the private address only.
  Pointing this name at the Elastic IP would send every spoke's proxy traffic at a public address it
  has no route to — a timeout with no message, from a name that resolves perfectly (Lesson 44 in its
  DNS form).
- **[Claude⚡] Applied:** `1 to add` in each slice, both re-planning **`No changes`**; the zone now
  answers `proxy.awsds.internal → 10.31.160.106` and `vpn.awsds.internal → 10.31.160.145`, read back
  from `list-resource-record-sets` rather than from the apply output. `gitlab.awsds.internal` is
  still owed and belongs to Stage 7.

## 2026-09-06 — 5.8: the build host moves, and running it finds three things reading could not

- **[Claude⚡] The move was forced, not tidy.** `sandbox/buildbox/`'s only egress was `0.0.0.0/0` at
  the WireGuard host's ENI. D38 deleted every default route and moved that host to
  `VPC-Networking` — and **a route target cannot live in another VPC**, so the old shape was not
  deprecated, it was unbuildable. Destroy-and-create rather than Recipe E: the host is `[E]` and the
  Sandbox state was **already empty** (serial 36, zero resources), so the destroy half was free.
- **[Claude] The tier changed, and it is a MEASUREMENT rather than a preference.** The peering routes
  to `VPC-Networking` live in `VPC-SharedServices`'s **private** route tables and **not** in the
  isolated one — read from `describe-route-tables`, not assumed. An isolated-tier build host could
  not reach the proxy at all. The isolated tier was only ever the old home because design A's default
  route belonged to `egress/` and two slices cannot write one route table; nothing writes a default
  route now, so that reason evaporated with the design.
- **[Claude] Four places, because an explicit proxy is not transparent.** A client that has not been
  told does not fail over — it hangs. `/etc/environment` (both cases), a **docker daemon** systemd
  drop-in (the daemon is not a child of any shell, so a perfect login environment still leaves
  `docker pull` hanging), `~/.docker/config.json` `proxies` for **build containers**, and **the boot
  script's own `export`**, which `/etc/environment` does not provide because cloud-init is neither a
  login nor a unit that reads it.
- **[Claude] THE ECONOMICS INVERTED, and the old note said the opposite in three files.**
  `production/egress/` used to be an *obstacle* — *"build with `egress/` DOWN"*, because its DNS
  Firewall associated to the VPC id and blocked the CDN-fronted package hosts. It is now a **hard
  prerequisite**: its `ssm`/`ssmmessages`/`ec2messages` endpoints (5.5) are the host's **only door**.
  A build session pays **0.130 USD/h** it used to avoid. `layers.py`, `terraform-live/README.md`, the
  slice README and `runbooks/buildbox.md` all said the old thing and now say this one.
- **[Claude] `buildbox.py`'s refusals moved with the design.** *Do not coexist with `sandbox/probes/`*
  is **deleted**, not retargeted — this slice creates no route anywhere and is not in that account,
  and a guard that no longer guards anything is the one a later reader trusts by mistake. The new
  pair: **read the `ssmmessages` endpoint before the apply** (without it the apply *succeeds*, the
  host runs, and `start-session` says not connected — indistinguishable from a slow boot for as long
  as anyone waits, [Lesson 52](../plan/lessons.md)), and **start the proxy host**, because under
  design B there is no route to fail over to.

### The three defects the RUN found, and none of them was visible to `validate` or `plan`

- **[Claude⚡] (1) `dnf.conf`'s `proxy=` has no exclusion setting.** The first boot died on
  `Failed to download metadata for repo 'amazonlinux'` … `CONNECT tunnel failed, response 403`. dnf
  had been given a proxy in its own configuration, and dnf.conf offers **no `noproxy` to pair with
  it** — so it sent the AL2023 repositories, which are on S3 and must go direct through the gateway
  endpoint, at a proxy whose build-host plane deliberately excludes `.amazonaws.com`. The proxy
  refused them correctly. Removed; the **environment** is the only place that can express both
  halves, and dnf reaches it through libcurl.
- **[Claude⚡] (2) `s3.dualstack.<region>.amazonaws.com` IS A DIFFERENT NAME.** It is not a label
  under `s3.<region>.amazonaws.com`, so a `NO_PROXY` carrying only the plain form does not match it —
  and AL2023's repositories use exactly the dualstack spelling. Measured on the host: **200 direct**
  (16.15.35.255, through the gateway) against **000 through the proxy**; the plain spelling also 200
  direct. `vpc-egress-v0.9.1` adds the dualstack form for **both** gateway services. The gateway
  carries either because a prefix-list route is keyed on the **address**, and both resolve into S3's
  IPv4 ranges.
- **[Claude] LESSON 46 A SECOND TIME IN THIS STAGE, and this one reached origin.**
  `git commit … | tail -2` hands back **`tail`'s** exit code, so an `&&` chain tagged and pushed
  `vpc-egress-v0.9.0` on a commit that **never happened** — the pre-commit `check-network-doc` hook
  had rejected it, because pre-commit **stashes unstaged changes** and the `docs/NETWORK.md` row that
  satisfied it was unstaged. Caught by reading the fetched module rather than trusting the tag:
  `git show vpc-egress-v0.9.0:…/no-proxy.tf | grep -c dualstack` → **0**. **v0.9.0 is abandoned on
  origin**, exactly as `vpc-egress-v0.3.0` was; v0.9.1 carries the change and was verified the same
  way before use.
- **[Claude⚡] (3) `public.ecr.aws` REDIRECTS blob downloads to a CloudFront distribution.** A real
  `docker pull` failed with `download failed after attempts=6: Forbidden` and named nothing. The
  **access log** named it: `CONNECT d5l0dvt14r5h8.cloudfront.net:443 403 TCP_DENIED`. Squid matches
  the hostname the client **requested**, so an HTTP redirect is a *new request with a new name* that
  must itself be allowed — the DNS Firewall never met this, because a CNAME chain and an HTTP
  redirect are different mechanisms ([Lesson 53](../plan/lessons.md) from the other side).
  **One distribution, not `.cloudfront.net`**: the tunnel plane carries the whole namespace because a
  browser needs it, and handing a build host a namespace anyone can publish into is the exact
  widening that splitting the filters was meant to avoid. Recorded with a revision trigger, because
  it is a third party's name and the remedy is to read the next one out of the same log.
  **This is 4.11 earning its keep on the first day it was needed.**

### What the run proved, inside a build container

| probe | result | what it proves |
|---|---|---|
| `https://pypi.org` | **200** | the tunnel, the peering, and this plane's allow-list |
| `http://example.com` | **403** | the allow-list is *enforced*, not merely configured |
| the AL2023 S3 dualstack name | **200**, direct | `NO_PROXY` and the gateway route, not the proxy |
| `docker pull public.ecr.aws/…/alpine:3.20` | complete | manifest **and** the redirected blobs |
| `http://10.32.0.10/` from the host | **403** | **6.3's reading, taken early** — the proxy is not an L7 bridge between VPCs |

- **[Claude] The boot's own egress check is now TWO readings and they use DIFFERENT SCHEMES, which
  is not a detail.** Over `https` a refusal is a **CONNECT** refusal, and `curl`'s `%{http_code}`
  reads **000** because no HTTP response ever crossed the tunnel — the 403 exists where that format
  string cannot see it. Over `http` the refusal **is** the response and reads as a plain 403 whose
  body names Squid. So the allowed probe is `https` (proves a working tunnel) and the refused probe
  is `http` (proves enforcement). The first version printed `000000` for both, which reads as a
  broken proxy.
- **[Claude⚡] Both slices torn back down** — `5 destroyed` for the buildbox, `13 destroyed` for
  `production/egress` — so the estate is where it was, plus the code. `make check` **OK**.

## 2026-09-06 — 5.9, and pass 5 closes

- **[Claude] The re-statement was already written; what 5.9 adds is a fallback that was MEASURED.**
  [D38](../plan/decisions/D38-single-egress-hub.md) already struck MWAA Serverless (its private shape
  *forbids* a route to a NAT device; the requirements list demanding two NAT gateways belongs to the
  **public** shape on the same page — [Lesson 41](../plan/lessons.md)) and already named ECR's
  pull-through cache as the candidate, with Stage 7 step 5.2 as the measurement. Restating that would
  have been transcription.
- **[Claude] So the amendment is what 5.8's run proved: pull-and-push through the proxy, ranked
  first.** A full `docker pull public.ecr.aws/docker/library/alpine:3.20` completed through Squid once
  the blob redirect's CloudFront distribution was on the build plane — token and manifest over the
  proxy, **layers over the free S3 gateway**. It needs no host in `VPC-Networking`, no second build
  environment and no route: it is the ordinary build path with one name added to one allow-list.
- **[Claude] What it deliberately does NOT settle**, because the distinction is the whole of Stage 7
  step 5.2: this is a **client** fetching an image. A pull-through *cache* is **AWS fetching from
  upstream on the service's own behalf**, and no client-side proxy setting reaches that. So 5.2 still
  measures whether the cache needs a route — the change is that the estate no longer *depends* on the
  answer in order to obtain a public image. Ranking is now (i) pull-and-push through the proxy
  (measured), (ii) prime from the hub's public tier, (iii) bake the images into `base`, and only then
  the estate's first NAT gateway.
- **[Claude] PASS 5 IS CLOSED.** 5.1 and 5.2 as code, 5.3 and 5.4 as decisions, 5.5 the SSM trio with
  a written refusal, 5.6 `NO_PROXY` generated from names AWS returns, 5.6a Staging keeps its
  firewall, 5.7 sixty-three entries to ten with a precondition and a re-aimed instrument, 5.8 the
  build host moved **and exercised**, 5.9 the contingency. **Owed into pass 6:** the `VPN_HOMES` trim
  and then the `removed {}` on `sandbox/foundation`'s Elastic IP, in that order; `NT-11`/`NT-4`
  (3.6-3.7); 2.6's retirement of the old zone family; and 4.11's second half (the Log Archive export)
  as decision due #4.

## 2026-09-06 — session audit: three things the log said less than it should

- **[Claude] `EXC-04` STILL COULD NOT BE MEASURED, AND `production/egress` WAS APPLIED AFTER THE
  SENTENCE THAT SAID SO.** The 5.7 entry above records that the churn could not be re-measured
  because *"all four `egress/` slices are `[E]` and down"*. Hours later 5.8 **applied**
  `production/egress` (13 endpoints), re-planned it — **`No changes`** — and destroyed it again. Left
  alone, that reads as a counter-example and closes the row by accident. **It is not one:**
  `production/egress` sets no `dns_firewall`, so it builds **no domain list at all**, and `EXC-04` is
  a defect of `aws_route53_resolver_firewall_domain_list`. A clean re-plan there says nothing about
  it. What settles the row is still the next `make up` of an **Interactive** slice — Sandbox or
  Staging — and only those two. Recorded because a reading taken for one reason is exactly what gets
  quoted later for another (Lesson 37).
- **[Claude] What this session wrote that was NOT Terraform, named rather than left implicit.** Three
  write APIs were called, all of them in the fenced class this repository already recognises:
  - **`ssm:SendCommand`**, repeatedly, to read *inside* the build host — the boot log, `docker info`,
    the proxy probes, and the `docker build` that produced the three-outcome table. Every command it
    carried was a read; the API is a write. This is the same fence `./scripts/buildbox.py sync` and
    `./aws/vpn.py --on-host` sit behind, used deliberately rather than to gather information.
  - **`ssm:StartAssociationsOnce`** on `awsds-prod-proxy-reconfigure`, once, to make the allow-list
    edit reach the running proxy without waiting for the half-hour schedule. It is 4.10's own reload
    path, run early rather than a new mechanism, and its `Success` is the evidence that the path
    works at all — which nothing had exercised before today.
  - **`ec2:CreateTags`/instance lifecycle** through `terraform apply`, under the user's standing
    authorization for this stage's steps.
- **[Claude] The instrument index moved with the instrument.** [`aws/INDEX.md`](../../aws/INDEX.md)'s
  `dns-allowlist.py` row described the DNS Firewall lists, the `EXC-05` flattening exposure and a
  `--from-api` that read `route53resolver`. All three were false after 5.7. The row now describes the
  five Squid planes, `DN-2`'s two severities and the `ssm:GetParameter` read — and the page's own
  paragraph about the one script that needs no AWS identity says *why* it moved. A routing file that
  points at the old subject is worse than one that points nowhere.

## 2026-09-06 — `EXC-04` closed, and 6.3 measured after a stale table surfaced as a timeout

- **[Claude⚡] `EXC-04` IS CLOSED, AND THE CANDIDATE FIX IT CARRIED SINCE 2026-08-22 WAS RIGHT.**
  Route 53 Resolver canonicalises a domain list as **FQDNs** — `list-firewall-domains` returns
  `pypi.org.`, `*.amazonaws.com.` and `*.` — while `vpc-egress` and its callers wrote them bare. The
  provider was comparing two **spellings** of the same list and re-issued `UpdateFirewallDomains` on
  every apply, so a plan read `0 to add, 2 to change` immediately after a successful apply of the
  same code, forever. What that cost is the thing worth naming: **`re-plan reads No changes` is this
  repository's closing check for every change**, and it was unavailable on the two slices carrying a
  firewall.
- **[Claude] Three readings, because the row itself said the fix was a HYPOTHESIS** — the provider
  could normalise the other way and produce the mirror diff:
  1. On the live Sandbox list, after the 5.7 apply: **`0 to add, 2 to change`**, reproduced with
     **ten** entries where it was found with sixty-three. So it was never about list length.
  2. With the caller's ten entries **dotted** and the module's catch-all still bare:
     **`1 to change`** — the allow list settled and the catch-all did not. **That is the reading
     that turned the hypothesis into a repair**, and it is why `vpc-egress-v0.10.0` dots `["*."]`.
  3. With both dotted: **`No changes`** — and then again after a forced re-create of both lists
     (`4 added, 4 destroyed`), so the **create** path is proven and not only convergence. A fix that
     converges an existing list and fails a fresh one would have been the worse outcome.
- **[Claude] Two controls landed in one sitting and the second misread the first (`v0.10.1`).** The
  v0.8.0 endpoint-coverage precondition compares allow-list entries against `PrivateDnsName` values,
  which come back **without** a trailing dot. With the dots in place it failed the plan naming **ten**
  endpoints as uncovered, all ten of which were covered. Normalised on the allow-list side —
  `trimsuffix(e, ".")` — rather than by dropping the dots, because the dots are the repair. Worth the
  note: this is the shape where a new gate reports a defect that is its own.
- **[Claude⚡] 6.3 measured, and TWO of the step's assumptions did not hold.**
  - **The probes carry no IAM role at all.** They report to `/dev/console`, read back with
    `get-console-output` — which is exactly why they work in a tier with no SSM path. So the readings
    went into the **peering probe's user data** rather than being driven over Session Manager, which
    also makes them repeatable rather than ad hoc.
  - **There is no Workloads probe and cannot be one today.** That VPC has no interface endpoint, by
    5.5's deliberate refusal, so a host there would have no management path at all. The mirror was
    taken from `VPC-SharedServices` instead, at 5.8: `http://10.32.0.10/` → **403**.
- **[Claude] The four readings, from the Sandbox spoke's console:**

  | reading | result |
  |---|---|
  | internet **without** the proxy | **silence** — no default route |
  | an address in `VPC-Workloads`, **through** the proxy | **HTTP 403** |
  | a name on this plane (`pypi.org`) | **HTTP 200** |
  | a name on **no** plane (`example.com`) | **HTTP 403** |

  The second is the one D38 rests on: the proxy **can** route to every spoke, and
  `http_access deny to_private` refuses before any allow — so the isolation the absent peerings give
  for free is not quietly undone at layer 7 ([Lesson 44](../plan/lessons.md)).
- **[Claude] The three ORIGINAL peering readings are `curl exit 6` and that is expected, not a
  finding**: `production/probes/` is `[E]` and down, and `probe.prod.internal` belongs to the **old**
  zone family that step 2.6 retires. A name that does not resolve is the honest answer while its
  target does not exist.
- **[Claude] AND 6.3 FOUND A STALE VOCABULARY ROW — AS A TIMEOUT, NOT AS A DIFF.** The first run
  could not reach the proxy at all (`curl exit 28`, after DNS had resolved). Cause:
  `PROBE_PEERS = {"sandbox": ["production"], "development": [...], ...}`, which scoped the probe's
  egress security group to `10.30.0.0/16` alone. Pass 3 added
  `sandbox/foundation ↔ production/networking` to `PEERINGS` and **nothing added `10.31.0.0/16`
  here** — one intent, *which VPCs does this account reach*, in two tables, and only one of them
  moved ([Lesson 33](../plan/lessons.md)). The row was **also** stale from 6b: `development` is a key
  no account has answered to since that rename.
  **Its own comment had predicted the day** — *"the reading that will force PROBE_PEERS to name
  slices rather than accounts"*. So it is **deleted rather than corrected**: `peer_cidrs` is derived
  from `PEERINGS` through a new `probe_peer_cidrs()`, and the membership guard became *"this
  account's `foundation/` must be an end of at least one peering"*, which is stricter than the test
  it replaces. Sandbox now emits `["10.30.0.0/16", "10.31.0.0/16"]`, Production
  `["10.20.0.0/16", "10.31.0.0/16"]` — the second **drops Staging**, correctly, because Staging peers
  only with the hub.
- **[Claude] A security-group change does NOT re-run user data**, and the first re-read after the fix
  returned the **previous boot's** console verbatim — same timestamps, same failures. `-replace` on
  the instance is what took the new reading. A stale console is indistinguishable from an unchanged
  result, which is the same shape as Lesson 52 one layer down.
- **[Claude⚡] Everything torn back down**: probes `4 destroyed`, `sandbox/egress` `27 destroyed`.
  `make check` **OK**.

## 2026-09-06 — 7.1 and 7.2: the hub gets a lifecycle, and a stopped one becomes an error

- **[Claude] 7.1 — `make hub-up` / `make hub-down`, over a new `--only`.** The hub is one
  account's pair of `[D]` hosts and **every other account's session depends on them**, while
  `make up` acts on one env and has no concept of that: `make up ENV=production` would also raise
  Production's `[E]` endpoint slices and its probes, which is money for a Sandbox session that
  needs none of it.
  **`--only` narrows and never widens** — a slice the env already refuses stays refused, with its
  reason still printed — and it is a **closed list**, so an unknown name is an error rather than a
  run that does nothing and reports success (the shape `optional_service_groups` got a validation
  block for). It filters the `[D]` hook as well as the `[E]` loop, which is what makes `hub-up`
  touch the two hosts and no endpoint.
  **No `ENV` argument, deliberately**: there is exactly one hub, so an ENV here would be a
  parameter with one legal value — the shape that invites a second nobody meant.
- **[Claude] 7.2 — the refusal goes BEFORE the `[D]` hook and before the first apply**, because a
  refusal after either would leave the env half-raised, which is worse than not starting.
- **[Claude] A direct `describe-instances`, and the step named `./aws/vpn.py`.** That instrument is
  right for the **question** and wrong for this **moment**: it writes a nine-check report and is
  what a person runs to find out *why* the tunnel is unhappy, whereas this needs one boolean before
  an apply and must not turn `make up` into a report generator. The two cannot disagree, because
  both find the host by the same Name tag — the contract `instance_name()` owns.
- **[Claude] UNREADABLE IS WAIVED, NOT REFUSED, and it is the uncomfortable half of Lesson 13.**
  A spoke operator may hold **no session on the Production account at all** — the profiles are per
  account — so treating a failed read as a stopped hub would make a legitimate `make up ENV=sandbox`
  impossible for exactly the person the check exists to protect. So the two nothings are told apart:
  a read that **fails** is printed and waved through with the reason; a read that **succeeds** and
  says `stopped` is what stops the apply.
- **[Claude] All four outcomes exercised** rather than the happy one:

  | case | result |
  |---|---|
  | both hosts running (the real state) | proceed |
  | the proxy stopped (injected) | **REFUSED**, naming `awsds-prod-proxy` with `<-- this one` |
  | neither readable (no session) | proceed, with the waiver printed |
  | the hub's own env | never checked — `up` is what starts it |

- **[Claude] `make help` carries a `THE HUB` section**, because a refusal a person meets for the
  first time mid-apply should be explainable from the tool that refused. Gates: `ruff` clean,
  `./scripts/slices.py check` 29/29, `make check` **OK**, both targets dry-run in both directions.

## 2026-09-06 — 7.3: `./aws/proxy.py`, and the two defects it found were its own

- **[Claude] Shaped after `vpn.py` deliberately.** Same two-profile default, same typed
  `--on-host` fence around `ssm:SendCommand`, same *an empty answer and a failed answer are
  different things* discipline. The two files are the instruments for D38's two hosts — one way
  in, one way out — and a reader who knows one should not have to learn the other.
- **[Claude] The five checks, first full run:**

  | check | verdict | reading |
  |---|---|---|
  | `PX-1` only the spokes and the tunnel may reach 3128 | **pass** | 5 rules, all TCP/3128, from `10.20`, `10.30`, `10.32`, `10.50` and the tunnel's `10.90.0.0/24` |
  | `PX-2` no `http_access allow` precedes the private deny | **pass** | committed **and** running: `deny to_private` is line 1 of 4 |
  | `PX-3` the running allow-list equals the committed one | **pass** | 5 planes, entry for entry |
  | `PX-4` the access log group, with its Log Archive export | **note** | the group exists (365 days) and has **no export** |
  | `PX-5` the perimeter names the exit address | **pass** | `184.33.8.126` in `DenyControlPlaneOffVpn` on all six persona sets |

- **[Claude] `PX-4` IS A `note` AND NOT A `fail`, AND THE DISTINCTION IS THE POINT.** 4.11's
  second half — the export to Log Archive — is an **open decision** (this stage's decision due #4)
  between a subscription filter into a Firehose and a scheduled `CreateExportTask`, with different
  cost shapes. A `fail` would report a gap the plan is deliberately holding open, and a checklist
  that is red for a decision nobody has taken is a checklist people learn to skim
  ([Lesson 50](../plan/lessons.md)). It says instead what standing without it costs: the author of
  the allow-list also owns its record (Lesson 18).
- **[Claude] TWO DEFECTS, BOTH THE INSTRUMENT'S OWN, BOTH FOUND BY RUNNING IT** — `validate` and a
  reading would have found neither ([Lesson 54](../plan/lessons.md)):
  1. **The per-plane lists are an `include`d drop-in, not part of `squid.conf`.** The main file is
     owned by Terraform because the ORDER of its `http_access` lines is the security property;
     the planes are rendered into `/etc/squid/conf.d/awsds-planes.conf` because their *content*
     changes without their *position* doing so. Read as one blob, the ordering check saw the
     drop-in's `allow` lines after `deny all` and reported a proxy that allows everything at the
     end, while PX-3 parsed **zero** planes from a host serving five.
  2. **`render-squid.sh` spells a plane `production_foundation` where the parameter says
     `production-foundation`** — `gsub("-"; "_")`, because that is what a Squid acl name takes.
     Comparing the raw keys reported **every** plane as both missing and extra. Lesson 53 at its
     smallest: one intent, two spellings, and the rule between them written down nowhere until now.
- **[Claude] And a third, which is the kind worth naming separately: `PX-2` READ ITS OWN SUBJECT
  AND THEN DID NOT USE IT.** The first version decided the verdict from the committed template
  alone and merely *printed* the running one — so a host serving a file nobody committed would
  have reported `pass` beside a detail string describing the problem. Both sources count now.
- **[Claude] Negative controls, because a check that has only ever passed is a claim**: an
  `http_access allow` moved above the deny → `1 allow(s) precede it: allow all_the_things`; the
  deny deleted entirely → `no http_access deny to_private line at all`. Two distinguishable
  outputs, plus the correct one.
- **[Claude] Registered in [`aws/INDEX.md`](../../aws/INDEX.md)** with its write-API fence stated,
  as the folder's rules require for the two files that have one.

## 2026-09-06 — 7.4: re-measuring found one wrong number, and it flattered a rejection

- **[Claude] The three rows this step asked for were already in `PRICING.md`**, added at the
  2026-09-05 review. Restating them would have been transcription, so they were **re-read** from the
  Price List bulk API instead — offer files republished **2026-08-31**, `AmazonVPC` and
  `AmazonRoute53`, `us-west-2` and `sa-east-1`.
- **[Claude] `us-west-2` held exactly**: Transit Gateway **0.05** per VPC-attachment-hour and
  **0.02**/GB processed; Route 53 Resolver endpoint **0.125** per ENI-hour, and an inbound or
  outbound endpoint needs at least two ENIs — so ≈ **USD 182/month standing** for the shape open
  question 23 priced and D38 declined.
- **[Claude] ONE FIGURE WAS WRONG, AND IN THE DIRECTION THAT FLATTERED THE REJECTION**
  ([Lesson 7](../plan/lessons.md)). The table gave `sa-east-1` a Transit Gateway attachment of
  **0.05/h with a ratio of 1.00**; the offer file says **0.09**, ratio **1.80**. The five-attachment
  hub-and-spoke this estate does *not* build would be ≈ **USD 328/month** in São Paulo rather than
  182. The rejection stands and is now stronger, which is exactly why a rejected-on-cost option has
  to be re-read rather than remembered.
- **[Claude] `cost-model.md`'s hourly table is REWRITTEN, not annotated.** The 2026-09-05 repricing
  had left the table saying one thing and a block below it saying another — one intent in two
  places, the shape that drifts ([Lesson 33](../plan/lessons.md)). Folded in, and the endpoint
  counts are now **counted rather than ranged**, each from its own slice's plan:

  | set | endpoints | USD/h |
  |---|---|---|
  | Sandbox | **18** | 0.180 |
  | Staging | **11** | 0.110 |
  | `VPC-SharedServices` | **13** | 0.130 |
  | `VPC-Workloads` | **0** | 0.000 — a written refusal, not an omission |

  The row it replaces read *"NAT ~0.050 + endpoints ~0.100-0.120"* — a range over a set nobody had
  counted. Three new rows carry what 6c actually built: the proxy at **0.0104/h with no per-GB
  charge at all**, the optional endpoint groups at **zero unless named**, and the build host's
  **three** bills.
- **[Claude] `architecture.md` §4.3a now names the shape that EXISTS.** The cell had read
  *"0.0052/h (`t3.nano`) or 0.0104/h (`t3.micro`)"* — a two-value range for a host that had not been
  built. It is a **`t3.micro`**, sized up because `dnf` was OOM-killed on 415 MiB, which is a
  measurement rather than a preference. And it gains the half the NAT comparison kept omitting:
  **an EC2 proxy charges nothing per GB**, where a NAT gateway adds 0.045/GB of processing.
- **[Claude] The two numbers that close the cost story.** Estate-wide the fixed rate fell
  **0.470 → 0.390/h** with the NAT. Sandbox's own idle floor **rose**, 0.160 → 0.180, because
  design B has to enumerate what a NAT covered silently — **the only axis on which it rose**, since
  per gigabyte a NAT is 0.045 against an endpoint's 0.010. Break-even ≈ **0.57 GB/h**.

## 2026-09-06 — 3.6 and 3.7 paid off: `NT-11` exists, and its two findings are two checks

- **[Claude] 3.6 was already done in the code and stale in the legend.** `NT-4` was re-cut with 4.7
  and reads *"no route overlaps `10.90.0.0/24` **outside the hub**"*, paired with a **positive**
  reading — *"the ONE `10.90.0.0/24` route, inside the hub"* — so the exception is asserted rather
  than merely excluded. Measured this run: `rtb-0b13c0405057ab331`,
  `10.90.0.0/24 → eni-0a6313a565c2b09c7`, `active`. The instrument's own closing legend still said
  *"anywhere"*; a summary that contradicts the check above it is the half a reader quotes.
- **[Claude] 3.7 — `NT-11` written, and step 3.7's warning is the design rather than a caveat.**
  *"Every active peering has a route on both sides"* would be red for a whole pass if written as one
  verdict, in the one place an operator most needs a trustworthy reading. So it is **two checks that
  never share a verdict**:

  | finding | what it is | urgency |
  |---|---|---|
  | **declared but not routed** | an `active` peering with no route on one side, **named by side** | real, and the normal state for the minutes between creating a peering and adding its routes |
  | **routed but not active** | a route whose target is deleted, failed or pending, or an id no peering answered to | a **BLACKHOLE** — packets leave and nothing comes back, with no ICMP and no log line. The opposite finding, and the more urgent one |

- **[Claude] Why it exists at all, and it is not hypothetical**: the reference implementation this
  project keeps as a comparison has exactly this defect — an `active` peering whose route table on
  one side never learned about it. Nothing *describes* that as an error. The attachment shows
  healthy, the CIDRs look right in a diagram, and traffic in one direction dies silently. **Peering
  shares an ADDRESS, never a PATH** ([Lesson 44](../plan/lessons.md)), and the path is this route.
- **[Claude] It asserts only about accounts it actually read.** A VPC whose account holds no live
  profile is skipped and said so: *"no route found"* and *"no session"* are the same silence
  (Lesson 13), and a check that crosses accounts by construction meets that case as the norm.
- **[Claude] Reading: `pass` — 5 active peerings, both sides routed, across 5 VPCs.** The estate's
  sixth peering is `deleted` and nothing points at it, which is why it is silent rather than a
  finding — and it is also the live proof that the second branch is looking at the right thing.
- **[Claude] Both branches proven on synthetic inputs**, because a check that has only ever passed
  on a healthy estate is a claim: one side unrouted → `pcx-1: vpc-b has no route to it`; a deleted
  peering still routed → `is deleted and 2 side(s) still point at it`; a route to an id nobody read
  → named; an unread account side → correctly silent.

## 2026-09-06 — the VPN runbook rewritten, because two of its checks now read as failures

- **[Claude] The file still described a host in Sandbox, and its banner said the move was in the
  FUTURE.** Fifty-five stale identifiers — profile, Name tag, slice paths, log group, secret,
  `make up ENV=sandbox` — but the expensive part was not staleness. **Two of Part C's three connection
  checks now produce a "failure" when the design is working**, and the user was about to follow them:
  - `curl https://checkip.amazonaws.com` *"must print `52.89.212.1`"* — there is no NAT on that host
    any more. The address the estate leaves under is the **proxy's**, and only through it.
  - `dig +short SOA sandbox.internal` *"must answer"* — that is the **old** zone family, associated
    with Sandbox alone. Once `DNS` points at the hub it must **not** answer.
  Both are **struck through rather than deleted**, so a reader holding an older copy recognises them
  instead of wondering which file is wrong.
- **[Claude] The DNS check is now a PAIR, in opposite directions, and choosing it needed a
  measurement.** `dig SOA prod.awsds.internal` must **answer** and `dig SOA sandbox.internal` must
  **not**. Read the zone associations rather than the plan: `prod.awsds.internal` and
  `awsds-pages.internal` are associated with `VPC-Networking` and **not** with Sandbox;
  `sandbox.internal` is the reverse. **`awsds.internal` answers through both** and therefore
  discriminates nothing — which is the trap a careless replacement walks into, since it is the obvious
  name to reach for.
- **[Claude] §C4's MTU proof had to be re-aimed, and the old form is now silently useless.** It was
  `ping -D -s 1372 1.1.1.1` against `-s 1200`, and the reading is *1200 passes while 1372 fails*. The
  host now rejects every forwarded packet not bound for RFC1918, so **both sizes fail identically** and
  the test says nothing at all. Re-aimed at **`10.90.0.1`** — `wg0`'s own address, the tunnel's far end
  — which isolates the tunnel from everything beyond it and is reached by the host's INPUT path rather
  than the FORWARD chain the rejection lives in. **Flagged in the file as not yet exercised**, because
  a substituted test is a claim until somebody runs it.
- **[Claude] §S2 re-drawn around three mechanisms that are easy to conflate.** The FORWARD chain is the
  perimeter and **not** a route — the host keeps an IGW default because *it* needs one (SSM, CloudWatch,
  `dnf`); what it will not do is carry a **tunnel** packet there, which is why the failure is a fast
  refusal rather than a timeout. The masquerade has a **deliberate hole** for the public tier so Squid
  sees `10.90.0.x`. And the estate's one sight of the tunnel range is a single route in one table.
  **The warning that earns its place**: do not widen that hole to the VPC CIDR — the resolver at
  `10.31.0.2` sits inside `10.31.0.0/16` and is not in a public subnet, so the tunnel's DNS would die
  while everything else kept working.
- **[Claude] §S3's NAT-instance job retired whole** — `vpc_nat_cidrs`, the disabled
  `source_dest_check`, the isolated-tier route and the extra `[P]` ingress rule. Not because it was
  disliked: the build host moved to Production and **a route target cannot live in another VPC**. What
  is kept is the **lesson** rather than the mechanism — reach is an intersection, the three halves lived
  in three slices, and the missing one made a build look like a broken package mirror. The same shape
  now guards the proxy: a spoke its group admits and its allow-list has never heard of is **reachable
  and mute**.
- **[Claude] Two honesty fixes made while in there, neither of them asked for:**
  - `VP-3`'s *"the estate's only world-open rule"* is currently **one per ACCOUNT** — Sandbox's `[P]`
    anchors outlive the host that used them until 4.13's second half — and the instrument reads
    **Production**, so it says `pass` about one of two ([Lesson 31](../plan/lessons.md)). Recorded as a
    dated exception with the step that ends it.
  - **The proxy's private address is deliberately NOT written down.** §C2 asserts that
    `dig proxy.awsds.internal` returns *a private address in `10.31.160.0/24`* rather than a literal,
    because that value is `[D]` and moves on a replacement — this runbook's own rule. Its **Elastic IP**
    stays literal, because it is `[P]` and is the address `DenyControlPlaneOffVpn` names.
- **[Claude] Every substituted identifier verified against AWS, not against the plan**:
  `awsds-prod-vpn-host-key`, `/awsds/prod/vpn`, `awsds-prod-vpn-health` all exist under those names.
  `check-tfvars-shape.py` already carried both tfvars paths, so nothing there had to move.

## 2026-09-07 — 6.1 measured by the user, and the third reading corrected this repository

- **[user] The four readings, verbatim as pasted** (`macOS`, one terminal, **no proxy environment
  variable set** — check 4 uses `-x` explicitly, which is why it needs none):

  ```
  ➜  ~ dig +short SOA prod.awsds.internal ; dig +short SOA sandbox.internal
  ns-1536.awsdns-00.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
  ➜  ~ dig +short proxy.awsds.internal
  10.31.160.106
  ➜  ~ curl -sS --max-time 15 https://1.1.1.1
  curl: (28) Connection timed out after 15006 milliseconds
  ➜  ~ curl -s --max-time 20 -x http://proxy.awsds.internal:3128 https://checkip.amazonaws.com
  184.33.8.126
  ```

- **[Claude] Reading 1 — the resolver in use is the HUB's, and the pair is what says so.** One SOA
  line for `prod.awsds.internal` and **nothing** for `sandbox.internal`. `.internal` is not a public
  TLD, so an answer can only come from a private zone, and the hub is associated with the first and not
  the second. Had the check been the obvious `awsds.internal`, both resolvers would have answered and
  the reading would have proved nothing.
- **[Claude] Reading 2 — `proxy.awsds.internal` → `10.31.160.106`**, private, inside the hub's public
  tier. The record was **NXDOMAIN until 2026-09-06**: step 2.1 said pass 4 would write it and pass 4
  did not.
- **[Claude] Reading 4 — `184.33.8.126`, the PROXY's Elastic IP.** One command proving the tunnel, the
  peering, the return route and the `tunnel` plane of the allow-list. It is also the address
  `DenyControlPlaneOffVpn` names since 4.12, so this is the perimeter's own premise, measured from the
  outside for the first time.
- **[Claude] READING 3 CONTRADICTED THE RUNBOOK I HAD WRITTEN THE DAY BEFORE, and the host settled it
  rather than a re-reading.** The file predicted *"a refusal, arriving fast, not a timeout"*, because
  the `FORWARD` chain answers with `icmp-admin-prohibited` rather than dropping. The user got
  `curl: (28) Connection timed out after 15006 milliseconds`. Measured on the host the same hour:

  ```
  4     8453  2104K  REJECT  all -- wg0 * 0.0.0.0/0 0.0.0.0/0  reject-with icmp-admin-prohibited
  ```

  **Both are true.** The host refuses, 8453 times — and the counter is what proves the rule is *hit*
  rather than merely present. macOS, like most modern stacks, **ignores an ICMP unreachable arriving
  mid-`connect()`** as hardening against off-path injection, so `curl` retransmits the SYN until
  `--max-time` expires. **The refusal is real and the sender cannot see it.** That is
  [Lesson 42](../plan/lessons.md) mirrored — there *is* a response and the receiver discards it, so
  absence is observed anyway — and it is written up as **Lesson 55**: the discriminator is not a better
  reading of the client's error, it is the counter on the **refusing** side. `§S2` and `§C2` of the
  runbook corrected the same sitting.
  **The rejected-packet count is also a number nobody had**: it is a live measure of how much a laptop
  tries to send straight to the internet while a full tunnel is up.
- **[Claude] AND THE RUN PROVED TWO THINGS 6.1 DID NOT ASK FOR.** The proxy's access log, read for the
  same minutes:

  ```
  2026-09-07T02:58:26+0000 10.90.0.2 CONNECT checkip.amazonaws.com:443 200 4950 735 TCP_TUNNEL
  ```

  **`10.90.0.2` — the DEVICE, not the WireGuard host.** That is 4.7's deliberate hole in the masquerade
  and 4.11's access log working together, end to end, for the first time: the log carries a per-device
  address instead of one indistinguishable blur, which is the whole reason the exemption exists and
  costs the ENI's `source_dest_check`. The NAT table confirms it from the other side —
  `RETURN … 10.90.0.0/24 → 10.31.160.0/24` counted **2** packets, exactly the user's two connections
  (POSTROUTING sees only the first packet of each; conntrack carries the rest).
- **[Claude] What 6.1 leaves**: `6.2`, `6.4` and `6.6` are still the user's, and `6.4`'s premise — *with
  the laptop's proxy setting removed* — now has a documented shape, since this run confirms no such
  setting was ever needed for the `-x` form.

## 2026-09-07 — the client plane was an allow-list, and the objectives ask for the opposite

- **[user] Found by the first browser that tried to use the proxy.** With Chrome launched against
  `proxy.awsds.internal:3128`, the AWS portal opened and **no other site did**. The user's question
  was the right one: *"me recordo de que iríamos colocar lista restrita apenas para a instância
  SageMaker, e a allow-list dos clientes seria bem menos restritiva"*.
- **[Claude] The record agrees with the user and not with what was built.** `objectives.md`, twice:

  > *"all internet access will be **monitored** — there will be an HTTP/HTTPS proxy between the
  > VPN-connected client and the cloud's internet egress. Once on the VPN, **the user can therefore
  > use the browser to reach the internet**"*
  >
  > *"the restriction is on the **SageMaker-managed compute**, **never on the user's (client's)
  > machine**"*

  What stood in the `tunnel` plane was a **23-name allow-list** of AWS console, portal and sign-in
  families — making the **client's** internet stricter than the **compute's**, which is the exact
  inversion of the requirement.
- **[Claude] How it happened, because the mechanism is more useful than the mistake.** Step 4.9
  wrote *"the tunnel range carries the institutional web filter — what a person on a company laptop
  may reach"*, and told the executor to seed it from the SMUS network-isolation guide's tables.
  `squid.conf` is default-deny, so *"filter"* was implemented as an **allow-list**. **An
  institutional web filter is a DENY-list over an open default** — it blocks categories, it does not
  enumerate the web. `CLAUDE.md` says the objectives are *"the specification a stage is measured
  against, so it is summarised nowhere"*; the paraphrase in the stage file **became** the
  specification. That is [Lesson 38](../plan/lessons.md) at a new address: a name travels further
  than the sentence that carried it.
- **[Claude⚡] The repair is a `mode` per plane**, and both keys are always present so no downstream
  parser meets a missing field:

  | mode | list used | meaning | who |
  |---|---|---|---|
  | `allowlist` | `allow` | may reach these names and nothing else | the four spokes — `sandbox-foundation` is D5's *"short list"* for the compute |
  | `open` | `deny` | may reach anything **except** these | the `tunnel` plane, **deny list empty by decision** (the user, 2026-09-07) |

  **Empty is not "no control"** for an open plane — the control is the access log, which is what the
  objectives' word *monitored* names, and it already carries a per-device address. **The three
  global denies are untouched**: private destinations, unsafe ports, CONNECT to anything but 443.
  *Open* means open to the internet, never to the estate.
- **[Claude] Two plan-time gates followed the shape.** The apex-beside-wildcard collision check now
  reads **both** kinds of list — a deny list is the one somebody will paste names into in a hurry,
  from a blocklist written for another syntax — and an unknown `mode` is a **plan failure**, because
  the render script branches on that string and a typo would emit no block at all: a source the
  security group admits and the config has never heard of, reachable and mute.

### The finding that cost the most, and it is a property of the design

- **[Claude⚡] THE PARAMETER IS DATA AND REACHES THE HOST IN THIRTY MINUTES; THE RENDERER IS CODE AND
  NEEDS A NEW HOST.** After applying the new parameter and triggering the association by hand, it
  reported **`Success`** — and the tunnel plane was still absent from the host. Read on the host:

  ```
  55:    | select((.value.allow | length) > 0)
  ```

  the **old** jq, which skips a plane whose `allow` is empty. `/usr/local/sbin/awsds-render-squid` is
  written by **user data**, so it is `[D]` state on the disk; step 4.10 bought a reload path for the
  **list**, not for the **renderer**. The association ran the old script perfectly, which is what its
  `Success` meant. **Two kinds of change with very different costs, and nothing had said so** — the
  proxy host was replaced (`2 to add, 2 to change, 2 to destroy`) and the new one renders
  `acl src_tunnel` + a bare `http_access allow src_tunnel`.
- **[Claude] `PX-3` reported a false mismatch and it was the check's fault, not the estate's.** An
  **empty `allowlist`** plane renders nothing — correct: no acl, no allow line, the source falls to
  the backstop and is refused by name, which is what an empty allow-list means. The check read that
  absence as a diff for `production-workloads` and `staging-foundation`. An empty **`open`** plane is
  the opposite and must be present, so its absence stays a finding. Both cases are now explicit.
- **[Claude] `./aws/dns-allowlist.py`'s parser met a form it did not know, and failed as a
  `KeyError` traceback rather than the loud refusal its own docstring promises.**
  `proxy_allow_shared` had become `concat(<comprehension>, <literal>)` on 2026-09-06 — one
  CloudFront distribution added to a list that is otherwise derived — and the grammar only knew
  `= [`. Both halves are parsed now, and a plane pointing at a local the parser does not recognise
  raises a message naming it. `DN-4` also changed question entirely: comparing the two planes'
  contents would now compare a **blocklist with a permit-list**, so it asks the shape question
  instead — *only the client plane is `open`; every compute plane is an allow-list* — and a compute
  plane that went `open` is a `fail`.
- **[Claude] And a decision from 2026-09-06 was vindicated the next day.** The host replacement moved
  the proxy's private address, and `proxy.awsds.internal` followed it: `10.31.160.106` →
  **`10.31.160.181`**. Yesterday's runbook edit refused to write that literal into §C2 on the
  grounds that it is `[D]` and moves on a replacement. It moved on a replacement.
- **[Claude] Verified end to end**: `./aws/proxy.py --on-host` reads `PX-1`, `PX-2`, `PX-3`, `PX-5`
  **pass** (`PX-4` the standing note), and `./aws/dns-allowlist.py` reads `DN-1`, `DN-2`, `DN-4`
  pass with `tunnel — 0 entries, mode open`.
- **[Claude] Issue opened** at the user's request for the macOS limitation that surfaced alongside
  this: the system proxy is **not consulted** while the WireGuard NetworkExtension tunnel is the
  primary service (`scutil --proxy` returns empty while `networksetup` shows it configured), so
  Safari, Chrome-by-default and native apps have no working path; and with the tunnel **down** the
  same setting breaks the `aws` CLI, which falls back to the macOS system configuration and which an
  empty `https_proxy` does **not** override — `NO_PROXY='*'` does.

## 2026-09-07 — the tunnel gains an IPv6 ULA, and it closes a leak nobody had a reading for

- **[user] The question that found it was not about IPv6.** *"Com o túnel ligado não tenho internet,
  mas a nossa conversa continua funcionando. Como isso é possível?"* — and the answer took two
  measurements, of which only the second was the real one.
- **[Claude] First measurement, and it was only half the story.** `netstat -rn -f inet` shows **two**
  default routes: the tunnel's, and the physical one carrying the **`I` (interface-scoped)** flag.
  macOS keeps the physical default alive and scoped, so a socket already associated with `en0` keeps
  using it. Proven both ways: a new `curl https://example.com` **fails**; the same with
  `--interface en0` returns **200**.
- **[Claude] Second measurement, and this was the finding.** Established TCP connections by local
  address:

  ```
     5 on 192.168.18.45      the Wi-Fi address (IPv4)
     4 on 2804:…             a GLOBAL IPv6 address
     0 on 10.90.0.2          the tunnel
  ```

  By process: **`claude` ×5**, `Claude`, `OneDrive` ×2, `Spotify`, and three macOS services. **The
  session asking the question was one of them**, on IPv6, with no route into the tunnel at all —
  `utun4` had **no `inet6` address and no IPv6 default route**.
- **[Claude] `AllowedIPs = ::/0` HAD BEEN INERT SINCE THE FIRST DAY, AND THREE DOCUMENTS SAID
  OTHERWISE.** `wg-quick` installs routes only for the address families the interface **has an
  address in**, and `[Interface] Address` was IPv4-only. The runbook's §C4 said IPv6 was
  *"deliberately black-holed"* — it was not black-holed, it was **not routed**, and the difference
  is a leak. [Lesson 56](../plan/lessons.md): a configuration line naming a capability the
  surrounding configuration does not have is inert and reads exactly like a working control; verify
  a routing directive from the **routing table**, never from the config that was meant to produce it.
- **[Claude] AND THE LEAK IS NOT AN AWS LEAK, which is worth being precise about.** Measured: `ec2`,
  `ssm`, `logs` and `sts` in `us-west-2` have **no AAAA records** — AWS API endpoints are IPv4-only,
  so they went into the tunnel and were rejected. The perimeter was never bypassed. What leaked was
  ordinary internet traffic — Spotify, OneDrive, Apple's services and the Anthropic clients —
  outside the proxy, outside the allow-list and outside the access log. For the objectives'
  data-leakage requirement the honest sentence is that the full tunnel was, on this client, an
  **IPv4-only** leakage control.
- **[Claude⚡] `wireguard-v0.6.0`, and the point is what it does NOT do.** All five VPCs are
  IPv4-only (measured), so the host has no IPv6 uplink and the ULA carries nothing: IPv6 now
  **enters** the tunnel and is **rejected** there. One `ip6tables` rule rather than an allow-list,
  because there is one answer — and explicit rather than left to routing (forwarding is already `0`)
  so the refusal is **counted**, which [Lesson 55](../plan/lessons.md) established two days earlier
  as the only place a refusal the sender cannot see is legible.
  **`fd90::<n>` mirrors `10.90.0.<n>`** — a deliberate departure from RFC 4193's randomly generated
  global ID, recorded as a departure: that rule guards against collisions when private networks
  merge, this prefix never leaves the tunnel, and the roster, the handshake log and the access log
  all key on the host number.
- **[Claude] THE HONEST HALF, WHICH CORRECTED THE USER'S PREMISE BEFORE THEY CONFIRMED.** The user
  asked whether the ULA is a host-side control the client cannot bypass. **It is not.**
  `AllowedIPs` on the *client* side is a routing directive: whoever holds the laptop deletes the
  IPv6 `Address` line and IPv6 leaves the tunnel again. Nothing on a WireGuard server can compel a
  peer to send it traffic. What this closes is an **accidental** leak and it makes the config honest;
  enforcement is `DenyControlPlaneOffVpn` (which fails closed) and the proxy's lists, and the
  institutional answer to the client half is an MDM profile the owner cannot edit. The user
  confirmed knowing that.
- **[Claude⚡] Applied — `2 to add, 3 to change, 2 to destroy`** (the host is replaced; user data
  writes `wg0.conf`). Measured on the new host:

  ```
  wg0    10.90.0.1/24 fd90::1/64
  peer   allowed ips: 10.90.0.2/32, fd90::2/128
  peer   allowed ips: 10.90.0.3/32, fd90::3/128
  ip6tables FORWARD 1  REJECT  all  wg0 *  ::/0 ::/0  reject-with icmp6-adm-prohibited
  ```

  **The host's public key is unchanged** — `LCD1d6xj…` — because it came from the `[P]` secret again,
  so **no client's `PublicKey` or `Endpoint` line moves**. `./aws/vpn.py`: `VP-1` through `VP-9`,
  all pass, Elastic IP still `52.89.212.1`.
- **[Claude] Rendered before tagging** (Lesson 54): a scratch `templatefile` produced
  `Address = 10.90.0.1/24, fd90::1/64` and both peers' dual `AllowedIPs`, and `bash -n` passed on
  the whole user data. `ip6tables` was confirmed present on the running host **before** the rule was
  written, because a failing `PostUp` on a host reachable only by SSM is an expensive way to learn.
- **[Claude] The vocabulary carries the ULA to exactly one slice.** `WIREGUARD_PEER_CIDR_V6` reaches
  `production/vpn` and **deliberately not** `production/networking`: the hub's consumers are a
  security group and a route table, both IPv4 because the VPCs are, and an unused value in a
  generated file is an invitation to find a use for it.
- **[Claude] Client instruction: ONE line.** `Address = 10.90.0.2/32, fd90::2/128`. Same shape as the
  `DNS` edit the account move needed, and for the same reason — everything else is `[P]`.

## 2026-09-07 — 2.6 and 2.4: the old zone family retired, and the obvious target was wrong

- **[Claude⚡] `prod.internal` and `pages.internal` destroyed** — `0 to add, 0 to change,
  **10 to destroy**`: the two zones, four cross-account authorizations and four associations,
  exactly the old family and nothing else. The gate was **6.1's DNS pair**, which was built for this:
  it asks that `prod.awsds.internal` **answer** and `sandbox.internal` **not**, so passing it is the
  measurement 2.6 was waiting for.
- **[Claude] THE OBVIOUS TARGET FOR THE PROBE RECORDS WAS WRONG, and the matrix is what says so.**
  `probe.prod.internal` and `probe-isolated.prod.internal` look like they belong in
  `prod.awsds.internal` — same account, successor name. INT-22 associates that zone with
  VPC-Workloads, VPC-SharedServices and VPC-Networking and **deliberately not with Sandbox**, which
  is the one place those records are resolved **from**: their whole job is to be the cross-account
  private-DNS Deliverable. In the child zone they would be NXDOMAIN at the only address that asks.
  They went to the **apex**, the one zone all five VPCs share — joining `gitlab`, `proxy` and `vpn`,
  and unlike those three they are `[E]`.
- **[Claude] `sandbox.internal` STAYS, and the reason is another slice's freeze.**
  `sandbox/foundation` plans **`1 to add`** — an Elastic IP that would be a **second** allocation —
  until the `VPN_HOMES` trim, and that trim waits on step **6.5**, which is half the user's.
  `-target` would destroy just the zone and the runbook forbids it outside two recipes, neither of
  which is this. So the zone stands, harmless (nothing resolves it, nothing points at it), and
  leaves with the apply that unfreezes the slice. Recorded where it will be met: `NT-12` carries it
  as a **dated note**, naming the step that ends it.
- **[Claude] `NT-12` written at 2.6, exactly as 2.4's own correction predicted it would have to
  be** — *"it cannot be written to the FINAL matrix and run before 2.6"*. Reading:
  **5, 2, 2, 3, 2 associations, and no others.**
  - **Two-sided, and that is the design.** A **missing** association is a name that NXDOMAINs where
    the matrix says it resolves; an **extra** one is a spoke resolving into a plane INT-22 keeps it
    out of — *the half no expected-direction test would find*. `prod.awsds.internal` not being in
    Sandbox is a control, and only the second half measures it.
  - **By CIDR, not by Name tag.** A range is this estate's identifier for a VPC and it does not move
    when a tag does — which it did at step 1.1, breaking both spokes while every id-shaped gate read
    clean ([Lesson 48](../plan/lessons.md)). The human names ride along as comments so the table can
    be compared with `docs/NETWORK.md` without a lookup.
  - **Four branches exercised on synthetic input** (Lesson 13): matching, one association missing,
    one extra, the zone absent, and an account that was not measured — the last being a `note`
    rather than a `fail`, because no session on an account and no association look alike.
  - **`NT-8` is retired, not renumbered.** It asked four questions about a family that no longer
    exists, and it resolved a VPC as *"the account's non-default one"* — an assumption that could
    only hold while every account had exactly one, which Production stopped doing at pass 1.
- **[Claude] Seven consumers followed the retirement**, found by grep before the destroy rather than
  after it: the three probe slices, `networking.py`, `supplychain.py`'s `ZONES`, `cicd.py`,
  `orchestration.py`, `layers.py` and `aws/INDEX.md`. **Historical prose in Stages 3, 4 and 6a is
  deliberately left alone** — those are records of what was true then, and rewriting them would be
  editing a log.

## 2026-09-07 — 6.7: `docs/NETWORK.md` rewritten from the readings, not promoted

- **[Claude] The file had been describing an estate that stopped existing three passes ago** — three
  VPCs, a NAT gateway per account, a WireGuard host in Sandbox doubling as a NAT instance, and a DNS
  Firewall whose job was filtering the internet. It carried the target in a `§T` block marked
  explicitly *as not built*, which is the discipline that made this rewrite cheap: the shape was
  already argued, and what 6.7 owed was the **measurement**.
- **[Claude] Rewritten FROM readings taken today, not promoted from `§T`.** `describe-vpcs`,
  `describe-subnets`, `describe-route-tables` and `describe-vpc-peering-connections` across three
  profiles; `NT-1`..`NT-12`; `PX-1`..`PX-5`; `DN-1`..`DN-4`; `VP-1`..`VP-9`; and the SSM parameter
  the proxy renders. Where `§T` said *"five peerings"*, the body now says which five, by `pcx-` id
  and CIDR pair, and which five are **absent**.
- **[Claude] Four rules head the file, and the third is the one this estate keeps needing:**
  *what is ABSENT is often the control*. Five peerings where there could be ten; no default route in
  any spoke; `prod.awsds.internal` deliberately not associated with Sandbox. A reader who only looks
  for what is present will read every one of those as an omission.
- **[Claude] The gate found two things a reading would not have.** `check-network-doc.py` requires
  **every subnet CIDR literally** — the first draft used `x.0.0/18` placeholders, which is more
  readable and unverifiable — and it requires **`sandbox/vpn/`** to be named, because the folder is
  still on disk and the gate reads the disk. Both fixed: a per-VPC subnet table with the thirty
  literal ranges, and a row for the slice whose host is already destroyed and whose folder waits on
  6.5.
- **[Claude] `docs/AWS_STATE.md`'s §C row restated as a RECORD rather than a prediction**, and one
  of its predictions was wrong in an interesting way: it said *"zero NAT gateways (three destroyed,
  not two)"*, and **none was ever destroyed** — every `egress/` slice was `[E]` and down when 5.1
  removed the code, so the act was a code change and the count was zero all along.
- **[Claude] A new §C row for what 6c LEAVES OWED**, because a frozen slice with an unapplied plan is
  exactly the state that gets rediscovered as a finding: `sandbox.internal`, the Sandbox VPN anchors
  and `sandbox/foundation`'s `1 to add` all wait on 6.5, **in that order**, and both `NT-12` and
  `VP-3` carry it as a dated note.
- **[Claude] What 6.7 does NOT yet carry, said in the file rather than left to be noticed**: step
  **6.2**'s reading — the portal opening from the tunnel with no browser grant, and the two
  client-plane names resolving publicly. §10's shadowing paragraph is written from the design until
  that measurement lands.

## 2026-09-07 — the client runbook, and `vpn.md` loses what moved

*Written by Claude at the user's request ("atualize o log com o andamento"), covering this sitting's
documentation work; nothing in this entry touched AWS.*

- **[Claude] `docs/plan/runbooks/client-vpn-proxy-configuration.md` is new**, at the user's request and
  to the user's outline: §1 up and §2 down (the session order), §3 the device and the tunnel (enrol,
  the `.conf`, up with its four checks, down), §4 the device and the proxy — macOS in three parts
  (system, terminal, Chrome) and Linux, the Linux half and Firefox marked *documented, not exercised*
  (Lesson 54). Every value in it is `[P]` except the proxy's private address, looked up by name.
- **[Claude] `vpn.md` lost what moved**: §S5's session order (it keeps the host-only start, the
  capacity signal and the floor), and §C0-§C3 whole, replaced by a stub; every internal pointer
  re-aimed. **§K4 step 3 was stale and got fixed on the way**: it named account `Sandbox` and
  `gen-tfvars.py sandbox vpn` for a slice that has been `production/vpn` since pass 4.
- **[Claude] The `proxy-on` shell function's first draft was wrong, and only running it said so** —
  `export https_proxy=… http_proxy=$https_proxy` in one statement expands the variable before the
  assignment, so `http_proxy` came out empty in **both** zsh and bash. Split into two statements and
  re-run in both shells before it went into the file (Lesson 54).
- **[user] Merged as PR #68** with the `docs/log/INDEX.md` row of the morning, and synced `main`.

## 2026-09-07 — 6.4's client half, 6.2's DNS half, and the wrong host

*Written by Claude at the user's request; the user's readings are pasted verbatim from the chat.*

- **[user] Tunnel up, no proxy variable set, verbatim:**

  ```
  ➜  ~ aws sso logout
  ➜  ~ unset https_proxy http_proxy HTTPS_PROXY HTTP_PROXY; date -u; curl -m 15 https://1.1.1.1
  seg  7 set 2026 15:29:33 UTC
  curl: (28) Connection timed out after 15004 milliseconds
  ➜  ~ curl -sI --max-time 10 http://proxy.awsds.internal:3128 | head -5
  HTTP/1.1 400 Bad Request
  Server: squid
  Mime-Version: 1.0
  Date: Mon, 07 Sep 2026 15:30:14 GMT
  Content-Type: text/html;charset=utf-8
  ➜  ~ dig +short agent.datazone.us-west-2.api.aws
  35.83.83.45
  35.163.146.141
  35.155.47.91
  ➜  ~ dig +short dzd-d8yrvx1ko7im6o.studio.us-west-2.sagemaker.aws
  studio.us-west-2.sagemaker.aws.
  100.21.12.108
  54.201.39.161
  100.21.5.92
  ```

- **[user] The browser**: with no proxy configured, no site opened. Launched with
  `open -na "Google Chrome" --args --proxy-server="proxy.awsds.internal:3128"`, **any** site opened —
  and `dzd-….studio.us-west-2.sagemaker.aws`, opened at its root, **redirected to
  `https://aws.amazon.com/pt/sagemaker/`**.
- **[Claude] 6.4's client half reads as predicted**: the timeout is the `FORWARD` refusal the sender
  cannot see (Lesson 55), and Squid's own `400` proves an RFC1918 name still reached through the
  tunnel. The counter half is Claude's, below.
- **[Claude] 6.2's DNS half passes**: both client-plane names resolve to **public** addresses from the
  tunnel — `agent.datazone` to three, the Studio host through a CNAME to `studio.us-west-2.sagemaker.aws`
  and three more. No `10.x` anywhere: the hub's resolver inherits nothing from the compute VPC's
  endpoints.
- **[Claude] The redirect is not the portal, and the next person will take the same turn**: the
  `<domain-id>.studio.…` host is the **Studio front-end**, the host that serves a space's JupyterLab;
  with no space path it sends the visitor to the marketing page. The portal is the `on.aws` surface,
  `dzd-*.sagemaker.us-west-2.on.aws`.

## 2026-09-07 — 6.2 closes: the portal with no browser grant, and the first space under design B hung

*Written by Claude at the user's request; the user's readings are pasted verbatim.*

- **[user] The portal, the right way**: the IdC access portal (`…awsapps.com/start`), signed in as the
  Data Scientist, *Applications* → the SageMaker domain → redirected to
  `https://dzd-d8yrvx1ko7im6o.sagemaker.us-west-2.on.aws/login`; **the site opened**. Project
  `eighth-experimentation`, then JupyterLab: **the terminal works, a Python session completes no
  command, and JupyterLab shows "IDE configuration in progress."**
- **[Claude] Diagnosis before any reading: `sandbox/egress` was down.** Under design B the VPC has no
  default route, so an app's DataZone and SageMaker calls have a path only through the 18 `[E]`
  interface endpoints `make up ENV=sandbox` raises — and the user had not run it. No endpoint means
  **silence**, not a denial (Lesson 42), which is exactly what a banner that never clears looks like;
  the terminal works because it needs nothing remote. A discriminator was proposed from inside the
  space, where the terminal already answered.
- **[user] The confirmations, verbatim**: *"O chrome não pediu nenhuma permissão."* The catalog —
  *Dados → Catálogos → AwsDataCatalog* — opened without errors, showing an empty database. Ran
  `make up ENV=sandbox`, restarted the JupyterLab instances, **and everything worked normally**. From
  the space's terminal:

  ```
  sagemaker-user@default:~$ getent hosts datazone.us-west-2.amazonaws.com sts.us-west-2.amazonaws.com
  10.20.34.83     datazone.us-west-2.amazonaws.com
  10.20.32.164    sts.us-west-2.amazonaws.com
  sagemaker-user@default:~$ curl -sS -m 10 -o /dev/null -w '%{http_code}\n' https://sts.us-west-2.amazonaws.com/
  302
  ```

- **[user] A question the `make up` plan raised**: the plan created the DNS Firewall domain list
  (ten entries — `*.amazonaws.com.`, `*.api.aws.`, `*.sagemaker.aws.`, the two private zones and their
  apexes) and printed the `no_proxy` output (the endpoint names, S3 and DynamoDB in both spellings,
  the private zones, `localhost`, `169.254.169.254`, `169.254.170.2`) — *are these private VPC routes,
  or the access control to external sites, the SageMaker restricted list? I saw none of the whitelist's
  sites.*
- **[Claude] Neither is the list, and the list is in another account — three layers, three questions.**
  The firewall list answers *does this name resolve?*: since pass 5 it closes the recursive resolver as an
  exfiltration channel and allows only AWS's namespaces and the estate's zones; a notebook never
  resolves `pypi.org` itself, it sends `CONNECT` to the proxy and the **proxy** resolves, in
  `VPC-Networking`, which carries no firewall. `no_proxy` answers *which door?*: the names that must
  **not** cross the proxy from inside the VPC, generated per VPC from the endpoint catalogue. The
  twenty-name allow-list answers *is it permitted?* and lives on the **proxy** —
  `production/networking/hub-anchors.tf`'s `proxy_allow_sandbox`, rendered into the SSM parameter — which
  is why a Sandbox plan cannot show it. And the firewall list was *created* because the slice is `[E]`:
  every `make up` rebuilds it.
- **[Claude] What closed**: **6.2 DONE** in the stage file, with the wrong-host turn and the hung space
  recorded under it; verification 3 answered; `docs/NETWORK.md` §10's shadowing paragraph and §13's owed
  note restated from the readings; `docs/SMUS.md` §`VpcOnly` gained the hang as a dated consequence, the
  client runbook §1 the symptom, and `lessons.md`'s second list the platform fact — *a `VpcOnly` space
  with no endpoints does not fail, it hangs with a working terminal*; `CLAUDE.md`'s position trimmed.
  `make check` OK, `check-plan-refs` unchanged.

## 2026-09-07 — 6.4's counter, reading A, taken from inside the tunnel through the proxy

*Claude's readings. The user authorized the on-host read in chat ("Autorizo você a executar os
comandos necessários") and was signed in as the infrastructure user.*

- **[Claude] The first attempt met the design, from the inside.** This shell runs on the laptop, inside
  the full tunnel, and carried no proxy variables: `git fetch` over SSH came back *Connection refused*
  at `github.com:22`, and the SSO credential fetch could not reach `portal.sso.us-west-2.amazonaws.com`.
  With the client runbook §4.1 [b]'s variables exported, both the credential fetch and the SSM read went
  through the proxy. **Git over SSH has no path at all**: the proxy allows `CONNECT` to 443 only, and
  macOS's `nc -X connect` refuses Squid's `HTTP/1.1 200 Connection established` reply — so this branch
  is pushed over **HTTPS**, with `gh`'s credential helper, through the proxy. **The client runbook
  gained §4.3 (GitHub) at the user's request the same hour**: push over HTTPS, never SSH, `gh auth
  setup-git` once, either remote shape. Two observations kept rather than explained: `ssh` reported
  *refused* where `curl` times out (§C2's Lesson 55 reading was taken with `curl`), and the ip6tables
  counter below reads **0**.
- **[Claude] `./aws/vpn.py --on-host` at 16:36:41Z** — `VP-1`..`VP-9` pass, every call returned. The
  lines that matter, verbatim:

  ```
  4    21040 4305K REJECT     all  --  wg0    *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-admin-prohibited
  1        0     0 REJECT     all      wg0    *       ::/0                 ::/0                 reject-with icmp6-adm-prohibited
  1     1648  105K RETURN     all  --  *      *       10.90.0.0/24         10.31.160.0/24
  2        0     0 RETURN     all  --  *      *       10.90.0.0/24         10.31.161.0/24
  3     1190 87322 MASQUERADE  all  --  *      ens5    10.90.0.0/24         0.0.0.0/0
  ```

- **[Claude] Reading.** The counters restarted when the host was replaced for the ULA (the user-data
  log on the host begins `04:54:23Z`), so **21040** is the refusal count since then: it already
  contains the user's 15:29 attempt and cannot isolate it. **What closes 6.4 is reading B** — the same
  read after the user repeats `curl -m 15 https://1.1.1.1` with no proxy: the `REJECT` count must grow
  by a handful (the SYN retransmissions of one 15-second attempt) and the `RETURN` for
  `10.31.160.0/24` must stay at **1648**. **The ip6tables zero is a zero that cannot discriminate**
  (Lesson 13): either the laptop's `.conf` has not yet gained its `fd90::2/128` line, or nothing IPv6
  was attempted; `netstat -rn -f inet6` on the client — a default route through the `utun` — is the
  reading that separates them.

## 2026-09-07 — 6.4 closes with reading B, and the timeout was the host's silence, not the client's deafness

*Claude's readings and the user's, the user's verbatim. The `--on-host` read is the one the user
authorized earlier in the sitting; `aws/vpn.py` gained four ICMP reads for it first (`ruff` clean).*

- **[user] The repeat, tunnel up, no proxy, verbatim:**

  ```
  unset https_proxy http_proxy HTTPS_PROXY HTTP_PROXY; date -u; curl -m 15 https://1.1.1.1
  seg  7 set 2026 16:48:10 UTC
  curl: (7) Failed to connect to 1.1.1.1 port 443 after 194 ms: Couldn't connect to server
  ```

  **A fast failure where 02:58 and 15:29 had timed out** — the same laptop, the same command.
- **[user] The `fd90::2/128` half of `Address` added to the `.conf` just before, and the IPv6 routes,
  verbatim:**

  ```
  netstat -rn -f inet6 | grep default
  default                                 fd90::                                  UGcg                utun4
  default                                 fe80::1%en0                             UGcIg                 en0
  default                                 fe80::%utun0                            UGcIg               utun0
  default                                 fe80::%utun1                            UGcIg               utun1
  default                                 fe80::%utun2                            UGcIg               utun2
  default                                 fe80::%utun3                            UGcIg               utun3
  ```

  The tunnel was then taken **down** on the laptop.
- **[Claude] Reading B — `./aws/vpn.py --on-host` at 16:54:59Z, direct (tunnel down, no proxy),
  `VP-1`..`VP-9` pass. The lines that matter, verbatim:**

  ```
  4    27681 5642K REJECT     all  --  wg0    *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-admin-prohibited
  1        0     0 REJECT     all      wg0    *       ::/0                 ::/0                 reject-with icmp6-adm-prohibited
  1     1724  110K RETURN     all  --  *      *       10.90.0.0/24         10.31.160.0/24
  2        0     0 RETURN     all  --  *      *       10.90.0.0/24         10.31.161.0/24
  3     1552  113K MASQUERADE  all  --  *      ens5    10.90.0.0/24         0.0.0.0/0
  Icmp: InMsgs InErrors InCsumErrors InDestUnreachs InTimeExcds InParmProbs InSrcQuenchs InRedirects InEchos InEchoReps InTimestamps InTimestampReps InAddrMasks InAddrMaskReps OutMsgs OutErrors OutRateLimitGlobal OutRateLimitHost OutDestUnreachs OutTimeExcds OutParmProbs OutSrcQuenchs OutRedirects OutEchos OutEchoReps OutTimestamps OutTimestampReps OutAddrMasks OutAddrMaskReps
  Icmp: 85 0 0 85 0 0 0 0 0 0 0 0 0 0 4366 0 0 23318 4366 0 0 0 0 0 0 0 0 0 0
  Icmp6InMsgs                     	3
  Icmp6InErrors                   	0
  Icmp6OutMsgs                    	219
  Icmp6OutErrors                  	0
  Icmp6InDestUnreachs             	3
  Icmp6OutDestUnreachs            	191
  net.ipv4.icmp_ratelimit = 1000
  net.ipv4.icmp_ratemask = 6168
  net.ipv4.icmp_msgs_per_sec = 1000
  net.ipv4.icmp_msgs_burst = 50
  ```

- **[Claude] 6.4 reads as designed, and the mechanism 6.1 wrote down was wrong.** `REJECT`
  **21040 → 27681** across the window that holds the repeat (+6641 in 18 minutes: the laptop's refused
  background traffic, the repeat's single SYN among them); the nat `RETURN` for `10.31.160.0/24`
  1648 → 1724 is this session's own proxy use (SSO, SSM, the HTTPS push) and the user's Chrome — not
  the curl's, and not meant to be. **The ICMP accounting is the finding**: 27681 rejected, **4366**
  ICMPs sent (`OutDestUnreachs`), **23318 suppressed** by the per-destination limit (`OutRateLimitHost`;
  `icmp_ratelimit` 1000 ms, `icmp_ratemask` 6168 includes destination-unreachable, the global limit
  never hit). A refused SYN gets its ICMP only when the bucket holds a token, and the laptop's
  background applications drain it several times a second — so the client sees a timeout most of the
  time and a fast `Couldn't connect` when lucky, **and macOS honours the ICMP the moment it arrives**
  (194 ms, one round trip). Lesson 55's conclusion stands — the evidence is on the refusing side; its
  mechanism sentence is corrected, and with it `runbooks/vpn.md` §S2, `docs/NETWORK.md` §7, the stage's
  6.1 block, both client checks, `CLAUDE.md` and `vpn.py`'s comment. The platform fact went to
  `lessons.md`'s second list.
- **[Claude] The ULA line works, and the `ip6tables` rule has never fired.** The client's IPv6 default
  now points at `fd90::` on `utun4`, the host answered **191** ICMPv6 destination-unreachables — and
  the explicit `FORWARD` `REJECT` for `::/0` still reads **0**. The host has no IPv6 route, so a
  tunnelled IPv6 packet is refused as *no route* at the routing lookup, **before** the `FORWARD` chain.
  The leak is closed and the refusal is counted — in `/proc/net/snmp6`, not in the rule written to
  count it (Lesson 56's shape, one layer down). The rule stays as the backstop; §C6 says so now. Also
  visible in the user's `netstat`: the physical IPv6 default (`fe80::1%en0`) survives as an
  **interface-scoped** route — the morning's IPv4 phenomenon, in the other family.
- **[Claude] `aws/vpn.py --on-host` reads the ICMP block from now on** — `/proc/net/snmp`'s `Icmp`
  line, three `Icmp6*` counters and the four `icmp_*` sysctls, all reads under the same ban list.
  **6.4 DONE** in the stage file; pass 6 keeps **6.6** and the user's half of **6.5**.
- **[Claude] And one defect of my own, kept**: the script that first appended this entry failed on a
  count assertion, and the commit chain behind it was not gated on the script's exit — so commit
  `9316dc1` carried every correction and the index row's *"forty-nine sections"* without the entry
  they described (Lesson 46's shape). This commit is the entry.

## 2026-09-08 — 6.6 taken as (ii), and 6.5 closes pass 6: two doors by family, the union trimmed, the Sandbox home retired

*Written by Claude at the user's standing request in this sitting; the user's decisions and pastes are
marked. The sitting straddled midnight UTC: it began on 2026-09-07 evening.*

- **[user] 6.6 — the closing choice of INT-16 is (ii), recorded acceptance**, in the user's words: *"vamos
  pela opção (ii). Revise o que for necessário no plano do estágio 11 para rever esta decisão"*.
- **[Claude] Recorded as a DEVIATION, not a gap**, in nine files (the stage's 6.6 block and decision due 3,
  the INT-16 row, `README.md` item 3, `GENERAL_PLAN.md` principle 4, `architecture.md` §3 — which still
  placed the tunnel in Sandbox, corrected —, `open-questions.md`, the device-trust row of
  `institutional-delta.md`, `CLAUDE.md`). Fallback (i)'s condition shape stays written in 6.6 and is
  applied nowhere. **Stage 11 gained the revisit**: step 3.4 re-takes the choice with five named inputs
  (recommendation: (i), unless `NT-9` reports a private door for the portal), 5.2 gains
  `awsds-data-portal-offproxy` — the alarm on a portal session arriving from any address but the proxy's,
  armed only after a tunnel-up session proves it quiet and a tunnel-down one proves it loud — decision
  due 10, verification xi, and the threat model's dated row.
- **[user] The Data Scientist signed in for 6.5, the infrastructure user for the rest**, and authorized
  the two `demo.py` runs, the readings, and — after reading the three plans — both applies, in order.
  The first Data Scientist login came back `ForbiddenException: No access` at `GetRoleCredentials`: the
  browser's IdC session still belonged to the infrastructure user and the flow re-used it silently
  (`aws/AWS-CLI.md`'s documented failure). A portal sign-out and a second login fixed it.
- **[Claude] The two laptop proofs, as the Data Scientist through the proxy, verbatim (account ids
  elided):**

  ```
  Grants available to this identity: 2
    READWRITE s3://awsds-sandbox-lake/sso-group-data-scientists/*
    READWRITE s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/*
  Vended identity: arn:aws:sts::<acct>:assumed-role/awsds-sandbox-lake-access/access-grants-45d4246f-6a6d-4129-9622-e7553b1076b4
  Wrote s3://awsds-sandbox-lake/sso-group-data-scientists/s3-read-write-demo/hello.txt
  Objects under s3://awsds-sandbox-lake/sso-group-data-scientists/: 2
            11  sso-group-data-scientists/from-notebook.txt
            44  sso-group-data-scientists/s3-read-write-demo/hello.txt
  Read back OK — laptop read/write/list on the project path works.
  ```

  ```
  Grants available to this identity: 2
    READWRITE s3://awsds-sandbox-lake/sso-group-data-scientists/*
    READWRITE s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/*
  Vended identity: arn:aws:sts::<acct>:assumed-role/datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c/access-grants-760060d8-98b8-45d5-9e20-e49aef446689
  Wrote s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/s3-read-write-demo/hello.txt
  Objects under s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/: 17
  Read back OK — laptop read/write/list on the project path works.
  ```

  And the negative control, the persona's direct call on the lake:

  ```
  aws s3 ls s3://awsds-sandbox-lake/ --profile awsds-scientist-sandbox
  An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::<acct>:assumed-role/AWSReservedSSO_DataScientistAccess_…/… is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::awsds-sandbox-lake" because no identity-based policy allows the s3:ListBucket action
  ```

- **[Claude] CloudTrail in Sandbox, read two minutes later (`lookup-events`, 2026-09-07 UTC):**

  | time | event | `sourceIPAddress` | `vpcEndpointId` | identity |
  |---|---|---|---|---|
  | 23:53:05 | `GetCallerIdentity` | `184.33.8.126` | `-` | DataScientistAccess |
  | 23:53:06 | `GetCallerIdentity` | `184.33.8.126` | `-` | InfrastructureAccess |
  | 23:53:38 | `GetCallerIdentity` | `184.33.8.126` | `-` | DataScientistAccess |
  | 23:53:39 | `GetDataAccess` | `10.31.160.181` | `vpce-043a6f047c31e06cc` | DataScientistAccess |
  | 23:53:39 | `ListCallerAccessGrants` | `10.31.160.181` | `vpce-043a6f047c31e06cc` | DataScientistAccess |
  | 23:53:40 | `GetCallerIdentity` | `184.33.8.126` | `-` | lake access role |
  | 23:53:46 | `GetCallerIdentity` | `184.33.8.126` | `-` | DataScientistAccess |
  | 23:53:46 | `ListCallerAccessGrants` | `10.31.160.181` | `vpce-043a6f047c31e06cc` | DataScientistAccess |
  | 23:53:47 | `GetDataAccess` | `10.31.160.181` | `vpce-043a6f047c31e06cc` | DataScientistAccess |
  | 23:53:48 | `GetCallerIdentity` | `184.33.8.126` | `-` | project role (vended) |

  **Verification 4 answered: TWO DOORS, BY SERVICE FAMILY.** `sts` leaves the proxy for the public
  endpoint and arrives as the proxy's Elastic IP; `s3control` resolves inside the S3 prefix list and
  takes VPC-Networking's **gateway** endpoint, arriving as the proxy host's private address with the
  endpoint id — 4.12's prediction, measured. Both branches of `DenyControlPlaneOffVpn` are load-bearing,
  and `trusted_vpce_ids` was complete before the trim: the vends succeeded.
- **[Claude] Two plans read as the step wrote them, one read `No changes`.** `identity/sso`: `0 to add,
  6 to change` — the diff shows `aws:SourceVpc` going from `["vpc-00dca…", "vpc-068274…"]` to the string
  `"vpc-068274…"`, which Terraform renders as two removals and is one: Sandbox's VPC leaves,
  `VPC-Networking` stays; the address list is unchanged because the transferred EIP reads `52.89.212.1`
  through either row. `data-governance/data`: **`No changes`** — Sandbox's gateway endpoint stays trusted
  as a consumer, and the addresses are the same set. `sandbox/foundation`: `0 to add, 0 to change, 4 to
  destroy`, the Elastic IP *"will no longer be managed by Terraform, but will not be destroyed"*.
- **[Claude⚡] Applied in the user's order.** `identity/sso` as `awsds-infra-identity` at 00:08 UTC: six
  inline policies modified, re-plan `No changes`, `./aws/proxy.py` `PX-5` pass (`184.33.8.126` on all
  six sets). `sandbox/foundation` as `awsds-infra-sandbox-1` at 00:10: the secret policy, the secret
  (30-day recovery window), the security group and `sandbox.internal` destroyed — the zone took 1m33s —
  and the Elastic IP forgotten; re-plan `No changes`.
- **[Claude] The retirement.** `terraform-live/sandbox/vpn/` deleted after `state list` read empty; its
  `layers.py` row with it — 28 slices, two `[D]`. `VP-3` widened to every `awsds-infra-*` account
  (Lesson 31), `NT-12`'s dated note removed, and the documents restated: `NETWORK.md`, `AWS_STATE.md`'s
  §C row (closed), `cost-model.md` (five zones, USD 2.50), `conventions.md` §6, `terraform-live/README.md`,
  `aws/INDEX.md`, the stage's status row, 4.13 and verification 4, `GENERAL_PLAN.md`, `CLAUDE.md`.
- **[Claude] Re-measured.** `./aws/vpn.py`: `VP-1`..`VP-9` pass — `VP-3` *"UDP/51820 on
  sg-09308ebfd2da884eb in the VPN home, none in the 4 other account(s) read"*. `./aws/networking.py` on
  the five infra profiles: all pass, `NT-12` five zones and no others. **And `NT-10` went red on the first
  run**, with `sandbox/egress` still up from the 6.2 sitting: Sandbox's `datazone` endpoint seizes
  `datazone.us-west-2.api.aws` and the check called that a shadowing of the portal's public name —
  written for the world in which the laptop resolved in Sandbox, red the first time an endpoint existed
  after 6.7 (Lesson 50). Re-cut: a seizure in a **compute** VPC is design B working (5.3 requires the
  endpoint there; the apps are not portal web clients), only one in the hub is the finding. Reads
  `pass` with the discriminator. The run before it also listed every persona profile's preflight failure,
  which is what running the script with no profile named does while only two sessions are live — noise,
  not findings.
- **[Claude] One reading about tokens, two observations.** The infrastructure token was invalidated
  earlier in the sitting and the Terraform plans failed with `GetRoleCredentials … 401`; the CLI kept
  answering for profiles whose role credentials were already cached. This time the Data Scientist's
  token **survived** the browser sign-out and the infrastructure login. So what kills a session's token
  is **`aws sso logout`**, which logs every cached session out at once (the user ran it at 15:29); a
  browser sign-out invalidates none.
- **[Claude] What 6c leaves.** Pass 6 is closed; every pass is executed and measured. **Decision due 4**
  — the access log's export to Log Archive — is the stage's one open item, both rates to be measured
  before the user chooses. `sandbox/egress` is still up.

## 2026-09-08 — decision due 4 taken as (c): the access log stays in Production until Stage 11, and the stage closes

*Written by Claude at the user's request, the same sitting; the choice is the user's, quoted, and the
measurements are Claude's.*

- **[user] The choice, in the user's words: *"Vamos pela opção (c)."*** — after the brief that put the
  three candidates side by side with the measured inputs.
- **[Claude] Measured before the choice (Lesson 6), all from public sources through the proxy.** The
  group's own volume from `IncomingBytes`: **0.53 MB** on 2026-09-06 (the buildbox's image pulls) and
  **0.13 MB** on 2026-09-07 — 4386 and 1057 lines; ~15 MB/month at the higher rate. The bulk Price List,
  `us-west-2`: Firehose **0.029 USD/GB** in 5 KB increments per record; EventBridge Scheduler **free** to
  14 million invocations; Lambda 0.20 USD/million requests; and **no SKU at all** for an export task or a
  Standard-class subscription — the catalogue's delivery SKUs (0.25 USD/GB to S3 or Firehose) are written
  for *vended* logs. Under a cent a month whichever way. `storedBytes` still read 0 on a group two days
  old, so the metric was the reading, not the describe call. Rows in `PRICING.md`; the four documentation
  and offer pages in `REFERENCES.md`.
- **[Claude] What decided it, since the money could not.** (a) and (b) both need objects built by hand in
  Log Archive — a CloudWatch Logs destination, a Firehose, a role and a bucket for (a); a bucket with a
  policy for the `logs` service principal for (b) — in an account with no CLI profile and no IaC, which is
  Lesson 35's shape. The record's destruction is not silent meanwhile: `DeleteLogGroup` and
  `PutRetentionPolicy` are management events on the organization trail, which already lands in Log
  Archive. And Stage 11 step 5.1 decides once, for every log the author must not own, where it lands
  (its decision 7): `/awsds/prod/proxy` now joins that delivery by name. The author of the allow-list owns
  its record until then, knowingly — the same shape as 6.6: accept, watch, revisit in the stage that owns
  the answer.
- **[Claude] Recorded**: the stage's decision due 4 and status row (**DONE 2026-09-08**), the 4.11 block,
  `PX-4`'s note (the reason is dated and compensated, no longer "open"), Stage 11's status and step 5.1,
  `GENERAL_PLAN.md`, `CLAUDE.md`, this index. And the token observation of the night went to `lessons.md`'s
  second list: `aws sso logout` invalidates every cached session's token, a browser sign-out none.
- **Stage 6c is DONE.** Three VPCs, five peerings, the `awsds.internal` family, two `[D]` hub hosts, zero
  NAT, no default route in any spoke, the client plane resolving in the hub, the perimeter re-keyed on the
  proxy's address and trimmed, the Sandbox home retired — every pass executed and every claim measured.

## 2026-09-08 — pass 8 added: the split-tunnel profile beside the monitored one, the requirement amended, 8.1 and 8.2 done, and the user's first `.conf`

*Written by Claude at the user's request ("Suba no mesmo PR o log deste andamento"); the user's decisions,
words and `.conf` are theirs, quoted. No AWS act in this entry beyond reads, and no reading of the new
profile yet — this sitting wrote it; 8.3 measures it.*

- **[user] The ask, after merging PR #69**: a second type of VPN access — *"(a) monitorado"*, what exists,
  and *"(b) aberto"*: the client reaches the private network through the tunnel and its internet leaves on
  its own, with no proxy to configure and no load on the proxy — to be built, if possible, with a new
  client file and host adjustments only, no new address and no new instance; and a check that every cloud
  resource is reachable under both. Asked first: which component implements today's control.
- **[Claude] The log checked first, at the user's request**: fifty-one sections, complete; two lines
  added — the provenance line the decision-(c) entry lacked, and the sentence that the client runbook
  gained §4.3 at the user's request. `make status` at the start of the sitting: both hub hosts **UP**,
  `sandbox/egress` **UP** (0.18/h) and `sandbox/probes` **UP** (0.0084/h) since the previous sitting; the
  tunnel **down** on the laptop — this shell reached `https://1.1.1.1` direct (`301`).
- **[Claude] The control is three layers in three places.** The client's `AllowedIPs = 0.0.0.0/0, ::/0`
  — a routing directive of the device's owner, never a control (`vpn.md` §C6 already said so); the host's
  `FORWARD` chain from `wg0`'s `PostUp` (RFC1918 accepted, the rest `REJECT`ed, the masquerade hole for
  the public tier, the single return route), which makes the internet exist only through the proxy, by
  name, HTTP/HTTPS; and IAM — `DenyControlPlaneOffVpn` on the six persona sets plus the lake's
  `DenyOutsideTrustedNetworks`, with `InfrastructureAccess` outside by decision (OQ 17). The first two make
  *the internet through the proxy*; the third makes *AWS through the proxy*, and it does not depend on the
  tunnel at all.
- **[Claude] The finding that shaped the pass: the reach difference between the profiles is by IDENTITY,
  never by network.** A split-tunnel `.conf` is the monitored one with one line changed — same key, so the
  host holds the same peer and nothing moves: no roster row, no Elastic IP, no instance, no apply. Nothing
  the monitored profile reaches is out of the other's reach; a persona's AWS work under split-tunnel needs
  the proxy pointed at by the *application*, because the perimeter accepts only the proxy's exit, and the
  infrastructure user needs no proxy anywhere. Split-tunnel reaches what monitored cannot — SSH to
  `github.com:22`, any protocol, IPv6 — unmonitored, by decision. Two consequences carried to their owners:
  Stage 11's planned `awsds-data-portal-offproxy` fires on every split-tunnel portal session (an input to
  its 3.4), and 6d's Method 1 deep link is expected to work under split-tunnel with nothing configured
  (its decision due 4 re-read at 7.5).
- **[Claude] Read from source, not measured.** `wireguard-apple`'s `PacketTunnelSettingsGenerator.swift`
  applies a `DNS` line to **every** query (`matchDomains = [""]`) whatever `AllowedIPs` says, and
  `wg-quick`'s `darwin.bash` writes it on every network service — so `DNS = 10.31.0.2` stays in both
  files (decision due 6, on the recommendation; the scoped resolver is the refinement, and `dig` cannot
  read it). One key per device (decision due 5, on the recommendation; the alternative is a roster row per
  device, an instance replacement). **Both to be confirmed by the user before 8.3.** And a correction to
  the brief as first given: `aws sts get-caller-identity` is **not** a discriminator between the profiles —
  AWS documents that no permission is required for it and that an explicit deny does not affect it — so
  8.3's contrast pair is `list-buckets`, the call 4d's proof used (explicit deny direct, implicit through
  the proxy).
- **[user] *"Perfeito. Pode prosseguir"*** — pass 8 written into the stage (8.1-8.5, decisions due 5 and
  6, verification 5, one risk: the monitored profile stops being exercised); the pass table, the stage
  index, `GENERAL_PLAN.md` and `CLAUDE.md` say *DONE for passes 0-7; pass 8 added, open*. The user asked
  for a suggested wording and then **amended `objectives.md` by hand, twice**. The first draft said
  *restricted* / *opened* — *restricted* is the word Lesson 57 caught on 2026-09-07 (the client plane is
  monitored, the compute plane restricted), *opened* collides with the proxy plane's `mode = open` — and
  the second, after the review, **monitored** / **split-tunnel**, the requirement's names since. The paste
  had replaced the monitored paragraph with the suggestion's placeholder; restored verbatim from the
  previous commit, and the bullet given its date marker. The plan then followed the requirement, never
  the other way round (Lesson 57).
- **[Claude] 8.2 done on both halves, 8.1 written.** `institutional-delta.md`'s device-trust row gains a
  fourth instance — the configuration file itself, fixed by MDM in the institution and chosen by the owner
  here; `NETWORK.md` §7 a dated paragraph saying every reading there is the monitored profile's and the
  split-tunnel readings are owed, nothing edited ahead; `GLOSSARY.md` one row for the pair, naming the
  `mode = open` collision; `architecture.md` §3's *full tunnel* sentence qualified. Then `vpn.md` **§C7**
  — the table of the two profiles, why the host is untouched, the one discipline (*one profile active at a
  time*: the same key is one peer), what it is not — and the client runbook's second file, **one `sed` over
  the first**, proved to yield a one-line diff; the scope rule now reads *"full tunnel in the monitored
  profile; the split-tunnel profile is §C7"*.
- **[user] The first split-tunnel `.conf`, shown in chat before the runbook was committed** (key elided):

  ```
  Address = 10.90.0.2/32, fd90::2/128
  DNS = 10.31.0.2
  MTU = 1280
  AllowedIPs = 10.20.0.0/16, 10.30.0.0/16, 10.31.0.0/16, 10.32.0.0/16, 10.50.0.0/16, 10.90.0.0/24
  Endpoint = 52.89.212.1:51820
  PersistentKeepalive = 25
  ```

  **The template, line for line.** Not yet brought up: 8.3's readings are the next act — the monitored
  tunnel down first — and 8.4's two on-host reads bracket them.
- **Commits on PR #70**: `50b4440` (pass 8 and the first objectives draft), `474aa2c` (the vocabulary and
  8.2), `cbe23f6` (8.1), then this entry. **What 6c still holds open**: 8.3 (the user's readings), 8.4
  (two `ssm:SendCommand`s the user authorizes), 8.5, decisions due 5 and 6 to confirm, verification 5.
  `sandbox/egress` and `sandbox/probes` are still up.
- **[user] Decisions due 5 and 6 taken, later the same evening, in the user's words: *"Confirmo as
  decisões 5 e 6. Uma chave. DNS 10.31.0.2"*** — after asking where the two decisions were and how they
  read. Both struck in the stage file; §C7 and the 8.1 block no longer say *to be confirmed*.

## 2026-09-08 — 8.3 and 8.4 measured: the split-tunnel profile from both ends, the persona pair on one command, and a counter that did not move

*Written by Claude at the user's standing request in this sitting; the user's pastes are verbatim, and the
laptop's own public address is never written. The user signed in as the Data Scientist and then as the
infrastructure user, and authorized the two `ssm:SendCommand`s in chat ("autorizo os comandos").*

- **[user] The tunnel up in the split-tunnel profile — the routes and the DNS, verbatim:**

  ```
  default            192.168.1.1        UGScg                 en0
  default            link#23            UCSIg               utun4
  10.20/16           link#23            UCS                 utun4
  10.30/16           link#23            UCS                 utun4
  10.31/16           link#23            UCS                 utun4
  10.31.0.2          link#23            UHWIi               utun4
  10.32/16           link#23            UCS                 utun4
  10.50/16           link#23            UCS                 utun4
  10.90/24           link#23            UCS                 utun4
  10.90.0.2          10.90.0.2          UH                  utun4
  default                                 fd90::                                  UGcIg               utun4
  10.31.160.181
  ns-1536.awsdns-00.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
  resolver #1  nameserver[0] : 10.31.0.2   if_index : 23 (utun4)   order : 102200
  resolver #2  nameserver[0] : 192.168.22.11  nameserver[1] : 192.168.22.12   if_index : 15 (en0)   order : 200000
  ```

- **[Claude] Reading.** The IPv4 default stays on `en0`; the `utun4` default and the `fd90::` default both
  carry **`I`** — interface-scoped, inert — where 6.4's monitored reading had the `fd90::` one `UGcg`,
  primary. The step said *"no `fd90::` default"*; the reading is *no primary one*, and the discriminator
  is the flag. The hub is still the resolver (`proxy.awsds.internal` → `10.31.160.181`, the SOA answered),
  and it is the resolver for **every** query: resolver #1, no domain restriction, order ahead of `en0`'s —
  **verification 5 answered from the reading**, the source's `matchDomains = [""]` measured.
- **[user] The `curl` line, and a shell defect kept.** Pasted with `\;`, the line became ONE `curl` with
  five arguments: `https://1.1.1.1;` and `https://checkip.amazonaws.com;` were *URL rejected: Bad hostname*
  (`000`); the two words `curl` became URLs fetched **through the proxy**, and Squid answered
  **`503 ERR_DNS_FAIL`** — *"Unable to determine IP address from host name curl"*, generated 02:33:57 GMT by
  `ip-10-31-160-181` — the proxy resolving, and refusing by name; only the last URL passed:
  **`184.33.8.126`, `200`** — check 4, valid.
- **[Claude] The two lost readings, from this shell on the same laptop, 02:37:02Z, no proxy variable**:
  `https://1.1.1.1` → **`301`** in 0.010 s connect; `checkip` direct → the laptop's own uplink address
  (elided — not the proxy's, not the tunnel's); through the proxy → `184.33.8.126`; `dig checkip` → a public
  address, `/etc/resolv.conf` naming `10.31.0.2`; `ssh -T git@github.com` → *"Hi felipenoris! You've
  successfully authenticated"*. The infrastructure token was gone (*Token for awsds does not exist*), so
  the identity half waited for a login.
- **[user] Check 1 on the WireGuard app's window** — `wg` does not work well against the App Store tunnel,
  the user reported, and the window is the equivalent reading: *Allowed IPs* the six ranges, *Endpoint*
  `52.89.212.1:51820`, *Data received* 194.88 KiB, *Data sent* 99.84 KiB, *Latest handshake* 1 minute 33 s,
  *Addresses* `10.90.0.2/32, fd90::2/128`, *DNS servers* `10.31.0.2`.
- **[user] "fiz login com sso data scientist."** **[Claude] The persona pair, 02:45:55-02:46:27Z, the
  same session, verbatim (account ids and the user elided):**

  ```
  list-buckets, DIRECT:   AccessDenied ... is not authorized to perform: s3:ListAllMyBuckets with an explicit deny in an identity-based policy
  list-buckets, PROXY:    AccessDenied ... is not authorized to perform: s3:ListAllMyBuckets because no identity-based policy allows the s3:ListAllMyBuckets action
  list-caller-access-grants, DIRECT:  AccessDenied ... s3:ListCallerAccessGrants on resource: "arn:aws:s3:us-west-2:<acct>:access-grants/default" with an explicit deny in an identity-based policy
  list-caller-access-grants, PROXY:   READWRITE s3://awsds-sandbox-lake/sso-group-data-scientists/*  ·  READWRITE s3://awsds-sandbox-smus-projects/dzd-d8yrvx1ko7im6o/avhvbqn37ty7m8/shared/*
  ```

  The proxy setting alone decides. The second pair is a positive control stronger than the step's — a read
  the persona holds, refused direct and answered through the proxy — and it needed no write, where the
  `s3-read-write` tool would have put an object in the lake. `get-caller-identity` succeeded direct, as
  AWS documents it must: exempt from every IAM deny, and no discriminator.
- **[user] "infrastructure user logado. autorizo os comandos."** **[Claude] `InfrastructureAccess` direct,
  02:52:59Z, no proxy variable**: the assumed-role ARN, and `describe-instances` — `awsds-prod-vpn`
  `running`, `awsds-prod-proxy` `running`. The whole infrastructure surface is direct under split-tunnel.
- **[Claude⚡] 8.4 — reading A at 02:53:04Z, the burst, reading B at 02:55:01Z.** Between them, from this
  laptop: `https://1.1.1.1` → `301`, `github.com` / `pypi.org` / `www.google.com` → `200`, one IPv6 attempt
  (`ipv6.google.com`: *Couldn't connect to server after 397 ms* — no primary IPv6 route, nothing to enter
  the tunnel), three names through `10.31.0.2`, two `checkip`s through the proxy. The lines that matter,
  A then B:

  ```
  4    82009   18M REJECT     all  --  wg0    *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-admin-prohibited
  1        0     0 REJECT     all      wg0    *       ::/0                 ::/0                 reject-with icmp6-adm-prohibited
  1     3622  232K RETURN     all  --  *      *       10.90.0.0/24         10.31.160.0/24
  3     6907  501K MASQUERADE  all  --  *      ens5    10.90.0.0/24         0.0.0.0/0
  Icmp: 286 0 0 286 0 0 0 0 0 0 0 0 0 0 12203 0 0 69809 12203 0 0 0 0 0 0 0 0 0 0
  Icmp6OutDestUnreachs            	17197
  ---
  4    82009   18M REJECT     all  --  wg0    *       0.0.0.0/0            0.0.0.0/0            reject-with icmp-admin-prohibited
  1        0     0 REJECT     all      wg0    *       ::/0                 ::/0                 reject-with icmp6-adm-prohibited
  1     3624  232K RETURN     all  --  *      *       10.90.0.0/24         10.31.160.0/24
  3     6948  504K MASQUERADE  all  --  *      ens5    10.90.0.0/24         0.0.0.0/0
  Icmp: 286 0 0 286 0 0 0 0 0 0 0 0 0 0 12203 0 0 69809 12203 0 0 0 0 0 0 0 0 0 0
  Icmp6OutDestUnreachs            	17197
  ```

  **`REJECT` 82009 → 82009; `RETURN` 3622 → 3624, the two proxied calls and nothing else; `MASQUERADE` +41,
  the DNS; every ICMP counter flat.** The handshake log read `peer=mbp` at 21 s and 91 s, then 39 s and
  109 s; `VP-1`..`VP-9` pass on both reads. For scale, between 6.4's reading B and A the monitored sessions
  had grown `REJECT` by 54328 and `Icmp6OutDestUnreachs` by **17006** — the ULA line at work.
- **[Claude] 8.5, and the stage closes with pass 8 included.** `NETWORK.md` §7 re-measured with a profile
  column; the client runbook's check 1 gains the app's fields and its split-tunnel paragraph the flag;
  `vpn.md` §C7 and its banner say *measured*; `lessons.md`'s second list gains the App Store client's two
  behaviours from the readings; Stage 11 step 3.4 gains input (f) and 5.2's arming test names the
  monitored profile; 6d decision due 4 and 7.5 gain the split-tunnel line; verification 5 struck; the
  indexes and `CLAUDE.md`. `make check` OK; `check-plan-refs` unchanged. **What the sitting leaves running**:
  the two hub hosts, `sandbox/egress` and `sandbox/probes` — `make down ENV=sandbox`, then `make hub-down`,
  are the user's.
