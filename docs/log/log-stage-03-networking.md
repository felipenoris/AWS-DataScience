# Log — Stage 3 — Networking

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-03-networking.md`](../plan/stages/stage-03-networking.md).*

---

*Five exceptions, recorded so the provenance is not guessed later. **On 2026-08-16 the user authorised
Claude, once and explicitly, to create this file and write the entry below** — a decision sitting held
with the user in that same session, with no AWS call in it. **A second explicit authorisation, later the
same day, covers the wording revision of the step 0 entry and its merged 0.4 subsection**, marked inline.
**A third, later still, covers the pass-1 entry, a fourth the pass-2 entry, and a fifth the pass-3 entry**
— in all three the user authorised the applies in chat and then asked for the progress to be written into
this file directly, so those entries are Claude's account of commands the user authorised. **The pass-3
one differs in one way worth naming: the user ran every command personally**, so it is Claude's account of
commands it drafted and read the output of, not of commands it ran. Everything else is the user's, as
usual, and the rule is unchanged.*

---

## 2026-08-16 — the five execute-time decisions, settled before the stage

**No AWS call in this entry, and nothing in this stage has been executed.** The sitting settled the five
choices the stage lists under "Decisions due while executing", so that none of them is taken at the
keyboard (Lesson 16). Two of them were brought forward because their consequences leave the stage: step 0
has an ordering against the `Staging` vend, and step 9.3's list is a prerequisite of Stage 4.

| # | Step | Settled as |
|---|---|---|
| 1 | 1.2, 1.3 | Supernet `10.16.0.0/13`, unit 1 at `10.20.0.0/16`. The allocation — CIDR and `zone_ids` — lives in `scripts/tfhygiene/backend.py` and reaches each slice through the generated `terraform.auto.tfvars`. **No new file**: that module is already the one place a slice's generated files are built from (Stage 2 step 2.6). Entries are authored, never computed; the rule is the lowest free `/16`; the duplicate check is born with N=2 |
| 3 | 5.1 | CloudWatch Logs, **30 days**. Not a cost choice — between 7 and 30 days the difference is cents. S3 delivery was the real alternative and was declined: it halves the delivery price and costs Logs Insights, on a log whose stated purpose is debugging |
| 4 | 10.1 | **`egress_mode = A`**. The USD 0.030/h decides nothing; what decides it is that B has no default route and its package path is not built until Stages 6-7. The switch stays per account and D5's comparison is unaffected |
| 5 | 9.3 | **Five families**, written now as the module variable's documented default: AL2023 repositories, CloudWatch agent, SSM agent, **ECR layer storage** and SageMaker |
| 6 | step 0 | **Delete all six Account Factory VPCs, and turn creation off in Account Factory.** The Management half before the `Staging` vend; the deletions by hand, per account, whenever. Closes with 0.4 |

- **The sitting's one finding, and it outranks the decision that produced it: a NAT does not bypass an
  endpoint policy.** A gateway endpoint puts a route to the S3 prefix list in the route table and the more
  specific route wins, so in-region S3 traffic goes through it and is judged by its policy whether or not a
  `0.0.0.0/0` route exists. Design A carries only what is *not* in-region S3. **So the allow-list of 9.3 is
  load-bearing from [Stage 4](../plan/stages/stage-04-vpn.md), not from Stage 6** — the first EC2 instance
  in the project is the WireGuard host, and it installs WireGuard from `dnf` in its user data. The stage's
  own 9.5 had said the endpoint is the only route "under design B", which is true and reads as though A had
  a second one.

- **One entry the step was missing, found while enumerating: ECR pulls its image layers from an S3 bucket.**
  `ecr.api`/`ecr.dkr` (8.2) authorise the pull; the layers come from `prod-<region>-starport-layer-bucket`,
  which is AWS-owned and therefore denied by the `aws:ResourceOrgID` condition like any other. It fails
  *after* a successful login and the error points at S3, not at ECR.

- **What the list is not: measured.** The five families' bucket names are taken from AWS's documentation,
  not read from an account, so each is confirmed at execution by verification (iii) — Lesson 23. And AL2023
  resolves its mirror list from a public HTTPS endpoint before fetching from S3: under A that leaves through
  the NAT, under B no entry in the list can rescue it, which makes it a design-B input due at Stage 6.

- **Repository, same sitting, no AWS call:** each decision written into the step that owns it (0.2, 1.3,
  5.1, 9.3, 10.1) with the "Decisions due while executing" section left as the index; 9.5's misleading
  sentence corrected; the stage's Status row now records that the five were settled before execution;
  `CLAUDE.md`'s Current position brought current. `make check` green, `make check-docs` still red on the
  same pre-Stage-2 prose, 1056 links resolve.

- **Open, and the next action:** step 0 — the Account Factory network configuration on Management, as
  `AWS Control Tower Admin` through `AWSAdministratorAccess`, which must land **before** the `Staging` vend.
  The six VPC deletions run per account as the **infrastructure user** through `InfrastructureAccess`
  (`awsds-infra-*`), and 0.4 closes the loop: re-run `./aws/networking.py` and update `docs/AWS_STATE.md`
  §C in the same sitting.

## 2026-08-16 — two statements of the previous entry corrected against the documentation

**No AWS write in this sitting** — a plan revision plus read-only snapshots. The Stage 3 roteiro was
revised into the action-checklist format, and the official documentation corrected two statements the
entry above records:

- **The Account Factory VPCs are not removed by a per-account hand-deletion.** The Control Tower
  walkthrough names the supported cleanup: **delete each account's stack instance from the
  `AWSControlTowerBP-VPC-ACCOUNT-FACTORY-V1` StackSet on Management** — so both halves of step 0 are one
  Management sitting as `AWS Control Tower Admin`, and verification (vi) now asks what the removal
  leaves behind. The decision itself — remove all of them, creation off before the `Staging` vend — is
  unchanged.
- **AL2023 does not fetch its mirror list from a generic public endpoint.** The default `mirrorlist=`
  URL points into the regional repository bucket itself (`al2023-repos-<region>-de612dc2`), and AWS's
  no-internet guidance is exactly the 9.3 gateway-endpoint policy — the package path works under both
  egress designs, and the "design-B input due at Stage 6" above is withdrawn. Verification (iii) still
  confirms the behaviour, plus that the AMI's repo files use the mirrorlist, not `cdn.amazonlinux.com`.

Also answered by documentation: verification (vii) — a Route 53 association authorization persists
until deleted, and deleting it does not affect the association.

## 2026-08-16 — Step 0: the Account Factory VPCs removed (0.2), creation turned off (0.3)

This step deletes the Account Factory VPCs — by deleting their CloudFormation **stack instances** from
the StackSet on Management, the removal path the Control Tower documentation names (0.2) — and turns VPC
creation **off** in Account Factory's network configuration (0.3), so every future vend arrives without
one.

- Login at AWS Console using `AWS Control Tower Admin` -> Management Account -> `AWSAdministratorAccess`.
  CloudFormation → StackSets → `AWSControlTowerBP-VPC-ACCOUNT-FACTORY-V1` → Actions → Delete stacks from
  StackSet.

  - "Accounts" section: left the default setting `Deploy stacks in accounts`. I took the account numbers
    from the StackSet's `Stack instances` tab:

    - Production Account
    - Development Account
    - Data Governance Account
    - Policy Canary Account
    - Identity Account
    - Sandbox Account 1

  - Section "Specify regions": set to `us-west-2`.

  - Section "Deployment options": `Retain stacks` is **not** marked, and the rest was left with default
    settings:
    - maximum concurrent accounts set to 1
    - failure tolerance set to 0
    - region concurrency set to sequential
    - concurrency mode set to "Strict failure tolerance"

- Moving to AWS Control Tower -> Account Factory. Network configuration section -> Edit.
  - `Internet-accessible subnet` is not marked.
  - `Maximum number of private subnets` set to 0.
  - Regions for VPC creation: unmarked `US West (Oregon)`; all the others were already unmarked by
    default.

### 0.4 — the loop closed *(merged by Claude, authorised by the user in this sitting)*

- Preflight, before the console sitting (read-only): zero ENIs in every Account Factory VPC and one
  `CREATE_COMPLETE` stack per account, so no dependency could block the delete — and the template read
  showed the stack **owns** the flow-log log group and carries no `DeletionPolicy: Retain` anywhere.
- Re-ran `./aws/networking.py` and `./aws/egress.py` (0.1's before-photo was taken earlier the same day):
  **no VPC in any measured account**, no interface endpoint, burn zero — every `NT-1`/`EG-1` note is
  gone, and the only notes left are the step 4 zones that do not exist yet.
- **Verification (vi) answered: nothing survives the stack-instance deletion.** Every stack reads
  `DELETE_COMPLETE` from its own account, `Policy Canary` included, and the flow-log **log groups are
  gone too** — consistent with the template reading above.
- `docs/AWS_STATE.md` §C rewritten in the same sitting. What remains open of step 0 is only the
  configuration half's proof: **verified at the `Staging` vend**, the first account that arrives after
  the change — run `./aws/networking.py` at that vend.

## 2026-08-16 — Steps 1-5 (pass 1): `foundation/` applied in Sandbox, Development and Production

*Written by Claude under the user's explicit authorisation, and the applies themselves were authorised in
chat the same sitting ("autorizo o apply. pode rodar todos"). Signed in as the **infrastructure user**
through **`InfrastructureAccess`** — profiles `awsds-infra-sandbox-1`, `awsds-infra-dev`,
`awsds-infra-prod`.*

### The git order, which the tooling forces

Branch `claude/stage-03-pass-1`, **two commits with the tags between them**:

1. the four modules, the address allocation in `scripts/tfhygiene/backend.py`, docs;
2. the tags `vpc-v0.1.0`, `iam-role-v0.1.0`, `kms-key-v0.1.0`, `s3-bucket-v0.1.0`, pushed with the branch;
3. the three `foundation/` slices and their `layers.py` rows.

The order is not a preference. `terraform_validate` runs `terraform init` on each slice, which resolves
`…/AWS-DataScience.git//terraform-modules/<name>?ref=<tag>` **from origin** — a first attempt staging
everything as one commit failed there with `invalid ref`, and no local tag would have helped. **A module
consumed by tag cannot be committed in the same commit as its first caller**, and 1.1a's "[user] Tag the
modules" is therefore a step *between* two commits, not after both.

### The applies

- **Generated** `backend.hcl` + `terraform.auto.tfvars` per slice (`gen-backend-hcl.py`, `gen-tfvars.py` —
  the allocation reaching the slices exactly as decision 1 specified); `terraform init` connected each
  backend on the first attempt, so the wrong-account guard was never exercised in anger.
- **Plans, read in chat before any apply, all three only-create:** Sandbox **31**, Development **30**,
  Production **32** — the difference is only the zones (Development has none, Production has two).
  Resource-by-resource the three plans are otherwise identical, which is what the single module promised.
  Spot-checked in the plan text: CIDRs `10.20`/`10.50`/`10.30`, the authored subnet cut (`/18` private,
  `/20` isolated, `/24` public, two AZs each), **no foreign CIDR in any plan**, both S3 endpoint policy
  statements, flow logs `ALL`/600s/**30 days**, and the `Environment` tag per account.
- **`Apply complete`** in all three: 31, 30 and 32 added, **0 changed, 0 destroyed**. A re-plan of each
  slice afterwards reads **`No changes`**.

### The post-apply reading, and the instrument it corrected

- `./aws/networking.py`: **NT-2, NT-3, NT-4, NT-5 and NT-7 pass**; the S3 and DynamoDB gateway endpoints
  (the INT-05 `[P]` anchors) are live in the three VPCs and present in all four route tables of each;
  `sandbox.internal`, `prod.internal` and `pages.internal` exist.
- **The four `NT-8` rows are red, and that is pass 2's work**, not a fault: the cross-account zone
  associations of 4.4 have not been made. `docs/AWS_STATE.md` §C now says so, so a later reading does not
  re-discover it as a finding.
- **NT-3 and NT-4 were wrong, and the applies exposed it.** Both flagged the public tier's mandatory
  `0.0.0.0/0 → igw` route as an "overlap" with the Staging and WireGuard ranges — arithmetically true,
  operationally meaningless: an internet exit cannot deliver into an RFC1918 range. Left alone, the two
  checks would have been permanently red from the first VPC onwards, which is a check nobody reads.
  `aws/networking.py` now excludes **exactly** that shape (`0.0.0.0/0` to an `igw-`/`nat-` target); a route
  naming a guarded range itself is still flagged, whatever its target.

### Repository

`docs/plan/stages/stage-03-networking.md` Status and a `RAN` note on the `foundation/` section;
`docs/AWS_STATE.md` §C rewritten from "no VPC anywhere" to the three project VPCs and their contents;
`CLAUDE.md` Current position re-trimmed to fit its 20 KB budget. `make check` green.

**Next: pass 2** — the four cross-account zone associations (4.4-4.5) and the two peerings into Production
(6). Both sides now exist, which is what they were waiting for.

## 2026-08-16 — Steps 4.4-4.5 and 6 (pass 2): the zone associations and the two peerings

*Written by Claude under the user's explicit authorisation; the applies were authorised in chat the same
sitting ("autorizo. pode aplicar na sequência proposta"), each plan read before the apply it belongs to.
Signed in as the **infrastructure user** through **`InfrastructureAccess`**.*

### The shape, and why it is three applies rather than five

Pass 2's constraints are all ordering: an association needs its authorization to already exist, a route to
a peering needs the peering **ACTIVE**, and acceptance is the peer account's own act. Spread across three
accounts that would be a sequence of alternating small applies. Instead the requesters are kept minimal —
`peering.tf` in Sandbox and in Development, one `aws_vpc_peering_connection` each (**+1**, **+1**) — and
everything else lives in `production/foundation/peers.tf`, applied third as **one ordered apply** (**+32**):

- the **4 authorizations** (`for_each` over zone × peer),
- the **4 associations**, executed *as* the VPC owners through provider aliases — which is what 4.4 means
  by "in the VPC owner, behind a provider alias", and what lets the ordering hold inside one apply,
- the **2 accepters**,
- **22 routes**: 12 return routes on Production's two private tables, 6 forward for Sandbox (its **public**
  table included — the WireGuard instance SNATs the laptop there, and without that route the tunnel comes
  up while GitLab stays unreachable) and 4 forward for Development.

Every route references the **accepter's** id rather than the data source's: that is what orders the routes
after acceptance, which AWS requires.

### Two rules the file keeps

- **The peers' facts are read, never pasted** (Lesson 3): VPCs by `Name` tag, subnets by `Tier`, route
  tables by `Name`. An id copied into a tfvars would be a stale copy of another slice's state; a data
  source cannot go stale. Everything referenced is `[P]` on both sides, so no `make down` can break it.
- **The profiles are derived, not authored** (Lesson 14): a generated `peers` map, built in
  `scripts/tfhygiene/backend.py` from the same `PROFILES` and `CIDRS` tables every command line already
  uses. No new vocabulary, and a network slice in an account with no allocation still fails loudly (D22).

Destinations are subnet-level, never a whole VPC (6.3); nothing anywhere routes `10.90.0.0/24` (6.5); and
there is no peering to Staging (6.6, D20).

### Verification

- Production's apply reads **`32 added, 0 changed, 0 destroyed`** — **verification (iv) answered: the
  second apply of `production/foundation/` is additive**. A re-plan of all three slices reads `No changes`.
- `./aws/networking.py`: **0 checks FAILED**. `NT-6` reads the two peerings and confirms neither touches
  the Staging range; `NT-8` is green on all five rows. From here **any red NT row is a finding**, which
  `docs/AWS_STATE.md` §C now says.
- **Verification (vii)'s residual, read-only:** `list-vpc-association-authorizations` on both zones shows
  exactly the four rows Terraform holds — two VPCs per zone, nothing else.
- **Verification (v) half-answered:** the AZ *name* mappings differ between accounts (that is why D9
  anchors on `zone_id`), but every VPC pins the same pair, so a same-AZ path exists at both ends of both
  peerings. Whether traffic *stays* same-AZ is a placement question that lands with GitLab's subnet
  (Stage 7), where the client route can be narrowed further.

### Repository

`peering.tf` ×2, `peers.tf`, the `peers` variable in three `variables.tf` (and a copy-paste header naming
the wrong slice, fixed in two of them); the stage's Status, its pass-2 `RAN` note and verifications (iv),
(v), (vii); `docs/AWS_STATE.md` §C; `CLAUDE.md`. **And a runbook the project did not have:**
[`docs/plan/runbooks/terraform-changes.md`](../plan/runbooks/terraform-changes.md) — how to make a
Terraform change by hand while there is no CI, including the two-commit tag order that pass 1 learned the
hard way, and a symptom table for a blocked commit.

**Stage 3 now needs only pass 3** — `egress/` `[E]`: the NAT behind the D5 switch, the interface endpoints
and their policies. It is the repository's first `[E]` slice, so it is also the first `make up` / `make
down` that is not a no-op.


## 2026-08-16 — Steps 7-10 (pass 3): `egress/`, and the first `make up` that is not a no-op

*Written by Claude under the user's explicit authorisation. **The user ran every command in this entry
personally** — Claude drafted them, read the plans and the instrument output, and this is its account of
that. Signed in as the **infrastructure user** through **`InfrastructureAccess`**.*

### What was built

One module, `terraform-modules/vpc-egress`, tagged `vpc-egress-v0.1.0` and called once per VPC-bearing
account. Applied through **`make up ENV=<account>`** — the D11 machinery Stage 2 wrote before there was
anything for it to act on, exercised for the first time:

| Account | Resources | Interface endpoints | USD/h |
|---|---|---|---|
| Sandbox | 16 | 12 — core 8 + three SageMaker + `elasticfilesystem` | 0.170 |
| Development | 15 | 11 — no `elasticfilesystem` (D24) | 0.160 |
| Production | 14 | 10 — no `sagemaker.studio`, no domain there | 0.150 |

Each also carries a NAT (design A, decision 4), its Elastic IP, and the private tier's `0.0.0.0/0` in both
AZs. Endpoints are single-AZ (`usw2-az1`, D9) with private DNS on, and every one carries step 9's document:
`aws:PrincipalOrgID` plus the `aws:PrincipalIsAWSService` carve-out, without which a service principal —
which carries no org id — is denied by the first statement alone.

### Two placements that are the point of the pass

- **The private tier's default route lives in `egress/`, not in `foundation/`.** It names the NAT's `[E]`
  id, so a route left in the `[P]` slice would blackhole the private subnets the moment `make down`
  removed what it points at. This is Lesson 4's shape — state in a `[P]` slice referencing an `[E]`
  resource — and it is why every `foundation/` re-plan still reads **`No changes`** after the applies:
  routes into a `[P]` route table are owned by the ephemeral side, so the two lifecycles do not touch.
- **`aws:ResourceOrgID` is deliberately absent from the interface-endpoint document.** Through these
  endpoints pass calls whose *resource* is AWS-owned and org-less — ECR base layers, JumpStart artifacts.
  The resource axis is controlled where it is load-bearing instead: the S3 gateway policy's enumerated
  allow-list (9.3), which lives in `foundation/` precisely so it survives a `make down`.

### Verification

- `./aws/egress.py`: **all checks passed** — EG-1 on 39 endpoints (33 interface, plus both gateway
  endpoints in each account), EG-2 and EG-3 on all 33, EG-4 on the three S3 gateway policies.
- `./aws/networking.py`: **0 FAILED**. The six new `0.0.0.0/0` routes are the first exercise of the
  `nat-` half of pass 1's `internet_exit_default()` exclusion; without it NT-3 and NT-4 would have gone
  red on a route the design requires.
- `make status`: `UP 16 / 15 / 14`, **USD 0.4800/h** — the sum of the `layers.py` rows, which are copied
  from the measured `docs/PRICING.md` §3 rates.
- **Verification (i) re-confirmed in the applied resource**, not only in the region catalog:
  `aws.sagemaker.us-west-2.studio` exists and is `available` in Sandbox and Development.

### Two instruments were wrong, and the applies are what exposed them

Both had the shape Lesson 13 names — a check whose output is the same whether the thing holds or not.

- **`EG-4` had no pattern for the ECR layer-storage family.** The live policy carries
  `prod-<region>-starport-layer-bucket`; the check could not see it, so it reported `pass` without reading
  it and would have kept reporting `pass` the day somebody deleted the entry. That is the family 9.3 calls
  the entry the step was missing, and it fails *after* a successful ECR login, pointing at S3 rather than
  at ECR. A pattern was added; the class now appears in the check's output.
- **`make status` counted a child module as one resource**, and counted data sources as deployed —
  reporting `2 resource(s)` for a slice holding 16. The burn was right, because it comes from the
  `layers.py` table rather than from that count, but the line that says what is *running* understated it
  by an order of magnitude. The count is now recursive and managed-only.

### Repository, and one note on provenance

`terraform-modules/vpc-egress/` (tagged `vpc-egress-v0.1.0`), three `terraform-live/*/egress/` slices, the
first three `[E]` rows in `scripts/tfhygiene/layers.py` with the first `usd_per_hour`, and `backend.py`
scoped so `vpc_cidr`/`peers` reach `foundation/` alone while `egress/` gets `zone_ids` + `account_folder`.
Plus a `.gitignore` rule of its own: **a module carries no lock file of its own**, which four modules had
acquired in pass 1 as a side effect of being validated by hand — one `h1:` hash each, the platform of
whoever ran `init` last, against the three the slices carry deliberately.

**The two instrument corrections above were committed by a parallel session** working in the same tree
(`ed3f65c`, "stage 8 review"), which staged them along with its own work. Nothing was lost and everything
is pushed, but `git log` on `aws/egress.py` and `scripts/slices.py` attributes those fixes to a Stage 8
review. Recorded here because the history cannot be corrected without rewriting a published commit.

**What is left of Stage 3 is not an apply**: the Validation's `make down` / `make up` cycle — the pair that
shows which id INT-05 may name, the `foundation/` ones byte-identical and the interface-endpoint ones all
new — and the two throwaway probes, one of which answers verification (iii). Verification (ii) is Stage 6's
by nature. **The lab is metered from this entry onward**: `make down` is what ends the session, and
`./aws/egress.py` §6 is the only instrument that will ever mention it (D12).


---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
