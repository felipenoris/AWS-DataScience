# `terraform-live/` — the deployed tree

One folder per controlled AWS account, each sliced into independently applied units. This is the tree
that describes what actually exists in an account; the reusable code it calls lives in
`terraform-modules/` and is consumed **by git tag, never by branch** — a module that moves under a caller
is a broken caller.

> **The authoritative layout is [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6, and it is not
> repeated here.** That file carries the full annotated tree with every slice and its `[P]`/`[D]`/`[E]`
> layer: two copies of a directory tree drift, and the copy that drifts is always the one somebody reads
> first. **This README explains how the tree is organised and what is in it today.** When the two disagree,
> conventions §6 wins.

> **What the network slices build — the addresses, the routes, both egress paths, the security groups — is
> [`docs/NETWORK.md`](../docs/NETWORK.md), also not repeated here.** This file says how the tree is
> organised; that one says what is on the wire, and `./scripts/check-network-doc.py` fails when a slice
> creating a network object is not named in it.

## What is here today

**Twenty-eight slices across five account folders: eighteen `[P]`, two `[D]`, eight `[E]`** (2026-09-08).
That is a summary, not an authority — `make slices` prints the live table, and a slice that reaches disk
without a row in it fails `make check`.

**Five `bootstrap/` slices**, one slice copied five times (Stage 2 steps 1, 2 and 3, 2026-08-15).
`staging/`'s replaced `development/`'s at Stage 6b steps 4.2-4.7 (2026-09-06) — a rename, not a vend, so
the count never changed. `./scripts/check-bootstrap-parity.py` is what keeps them copies.

`development/` became `staging/` on a new state bucket on 2026-09-06
([Stage 6b](../docs/plan/stages/stage-06b-development-becomes-staging.md), Recipe E), losing
`sagemaker/` and `data/` on the way (destroyed, steps 1.7 and 2.4) and carrying `foundation/`,
`egress/` and `probes/` across (step 4.3). `production/` grew `networking/`, `workloads/` and
`workloads-egress/` the same day, and its existing `foundation/` VPC became **VPC-SharedServices**;
`vpn/` and `proxy/` arrive at 6c pass 4 ([Stage 6c](../docs/plan/stages/stage-06c-networking-hub.md)).

`sandbox/`, `staging/`, `data-governance/`, `production/` and `identity/` each carry the same
`main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `versions.tf` and `.terraform.lock.hcl` — **the state
bucket and the KMS key that encrypts it, and nothing else**. All five have applied and hold their own
state, `production/` with a second key besides.

**Two files may differ**, and each is a file of its own so the rule can be blunt: `backend.tf`, commented
out until a slice has migrated, and `production/bootstrap/pki-key.tf`, D36's second state key (step 3.4).
**`./scripts/check-bootstrap-parity.py` enforces the rest** — byte-identical, `backend.tf` compared with
the comment markers stripped, and any other unshared file a failure. A module would have been the other
answer, and step 2.3 rules it out: modules are consumed **by git tag**, which cannot exist before
`terraform-modules/` does.

**Two files per slice are generated and untracked**, because a `.tf` file may hold neither of the values they
carry — the backend cannot interpolate anything, and the region may not be a literal (step 9.1's check
scans for it). Both are written from `scripts/tfhygiene/backend.py`, one table with two writers, so the
region the backend records and the region the provider uses cannot disagree:

```bash
./scripts/gen-tfvars.py      sandbox bootstrap   # terraform.auto.tfvars: region, env, environment_tag
./scripts/gen-backend-hcl.py sandbox bootstrap   # backend.hcl: bucket, key, region, kms alias
```

**`bootstrap/` is the only slice whose `backend.tf` starts commented out**: it creates the bucket that will
hold its own state, so it applies once with local state and then migrates (step 2.2). Every other slice in
this tree declares its backend from the first `init` and never holds local state at all.

**The rest of `docs/plan/conventions.md` §6's tree is not on disk** — the reading of step 1. Git does not
track empty directories, so a skeleton of ~35 empty slices means ~35 `.gitkeep` files: a second copy of
§6's listing, in a form that drifts silently and that no reader consults. Each slice folder is created by
the stage that first writes a `.tf` file into it, and §6 stays the place the layout is written down.

**`versions.tf` carries the same constraints in every slice**, because Terraform has no repository-wide
pin: the constraint belongs to each root module. The copies are not byte-identical —
`check-bootstrap-parity.py` looks only at `bootstrap/`, so nothing compares them outside those five slices
and five byte-variants exist today. What is enforced is the property that matters, by
[`scripts/check-provider-locks.py`](../scripts/check-provider-locks.py): the `required_version` and the
`hashicorp/aws` constraint must equal `sandbox/foundation`'s, **a second provider block is explicitly
permitted**, and every committed `.terraform.lock.hcl` must carry Stage 2 step 6.3's three platforms.
`sandbox/sagemaker/` and `data-governance/governance/` add that second provider, `awscc`, and each says so
in its own file. The `aws` block is unchanged — what the drift rule is about — and the second one is there
because three resources exist in no other provider at all: the V2 project profile, the blueprint
configuration's `environment_role_permission_boundary` — which is how the D13 boundary reaches roles
**DataZone authors** (INT-15) — and the DataZone policy grant (`awscc_datazone_policy_grant`, both layers
of the create authorization since 2026-08-22). `docs/plan/conventions.md` §6 anticipated that split.

**Stage 3 put a network on disk in the three accounts that have one — `sandbox/`, `staging/` (then named
`development/`) and `production/` — split three ways** (2026-08-16, applied and measured). `foundation/`
is `[P]`: the VPC, its six subnets across three AZs, the gateway endpoints and the private hosted zones,
plus the peerings and zone associations pass 2 adds on a second apply of the same slice. `egress/` is
`[E]` — the interface endpoints (and a NAT gateway, whose code 6c step 5.1 removed), which are this
tree's entire hourly bill. `probes/` is `[E]` as well and is an **instrument rather than infrastructure**:
the hosts the perimeter, both peerings and the flow logs were measured from, kept on disk because a probe
that has to be rewritten is a probe nobody re-runs. **`data-governance/` has no `foundation/` and never
will** (D22 — a registry needs no VPC), which is why `layers.py` carries an explicit comment where its row
would be. What stands right now is the `[P]` half alone: the `[E]` slices are destroyed and the tree bills
**USD 0.0000/h** between sessions, while `foundation/` re-plans `No changes` — that pair is D11's proof.

**Stage 5 put the lake on disk in the one account that has no network — `data-governance/data/`**
(2026-08-18/19, applied in three passes). It is all `[P]`, and nothing in it is ever torn down: the
account data CMK (`alias/awsds-data-data`), the five `awsds-data-*` buckets under it, the Glue databases
and the Iceberg sample table, the `awsds-data-catalog-maintenance` role with its two unscheduled crawlers,
the Lake Formation settings/registrations/LF-Tags, the governance manager's grants, and `shares.tf` — the
cross-account grants that are how a consumer reaches the lake at all - Sandbox alone since 6b step
2.4 destroyed `development/data/`.

**The consumer side is `sandbox/data/` and `development/data/`** (pass 4, 2026-08-19; the second was
**destroyed** at Stage 6b step 2.4, so `sandbox/data/` is the only caller left). They are the tree's first
slices that are **one module applied twice** — `terraform-modules/consumer-data/` — so the design lives
once and each slice says only which account. Each holds the account's own `DataLakeSettings`, its
`alias/awsds-<env>-data` CMK (one data CMK per account, the 2026-08-19 revision that withdrew the
`security-zone` dimension; since 2026-08-26 it is the sandbox lake's key in Sandbox, and the copy in the
account Stage 6b renamed to Staging stands empty under its original `awsds-dev-data` alias — D19 revised:
the derived bucket and the enforced workgroup **left the module at
`consumer-data-v0.6.0`**, the derived zone being the SMUS project path now), the two resource links to the
lake, and the local re-grants without which a held share cannot be used by anybody. All `[P]`.

**Two properties of the lake slice are unlike anything else in the tree, and both are permanent:**

- **it cannot be destroyed.** The `Data` OU SCP denies `s3:DeleteBucket` with no principal carve-out, so a
  `terraform destroy` here stops at the first bucket. Every name in it is permanent, and the amendment
  procedure is the stage file's, not a `-target` away;
- **it applies in two steps, and the plan does not say so.** `aws_lakeformation_data_lake_settings` owns
  values Terraform cannot state an intention about — the two `Create*DefaultPermissions` blocks, which act
  at *creation* time — so the settings land alone under `-target`, are read back, and only then does the
  rest of the slice create a database. That is **Recipe D** in
  [`docs/plan/runbooks/terraform-changes.md`](../docs/plan/runbooks/terraform-changes.md), and it is the
  procedure for **every** account that gains this resource: Sandbox and Development at Stage 5 pass 4,
  Production and Staging at Stage 9.

**Checks stand over this tree — Stage 2 steps 9, 3.5 and 8.1, Stage 4's, `check-identifiers.py`
(2026-08-17) and `check-provider-locks.py` (2026-08-21) — and there is no CI to run them in.** Until
Stage 8 puts them in a pipeline the surfaces are `pre-commit` and the repository's `Makefile`, both
calling the same scripts:

```bash
make check      # offline: region literals, indexed AZs, account-level BPA, wildcard ARNs,
                #          bootstrap parity, slice layers, tracked tfvars shape, the policy index,
                #          account ids and e-mails, provider locks
make check-ou   # needs an SSO session as the infrastructure user on Identity
```

**Every slice folder in this tree must declare its D11 layer** in
[`scripts/tfhygiene/layers.py`](../scripts/tfhygiene/layers.py) — `[P]` persistent, `[D]` dormant, `[E]`
ephemeral (Stage 2 step 8.1, 2026-08-16). The `egress/` slices are `[E]` with a `usd_per_hour` copied from
the measured `docs/PRICING.md` §3 rows, so `make up ENV=…` / `make down ENV=…` act for real and
`make status` reports a burn; the end-of-session reading is `./aws/egress.py` §6. A slice created without
a row fails the sixth check, because `make down` silently skips what it has never heard of — for an
ephemeral slice, a bill nobody is told about. `make slices` prints the table.

**`[D]` is not a slower `[E]`.** The `[D]` rows are the two hub hosts in `VPC-Networking` —
[`production/vpn/`](production/vpn/) (rank 40) and [`production/proxy/`](production/proxy/) (rank 41),
6c pass 4. `sandbox/vpn/`, the tree's first `[D]` slice (Stage 4), was retired at 6c step 6.5 (2026-09-08).
**`make hub-up` / `make hub-down` start and stop the two hub hosts together** and destroy nothing; a
spoke's `make up ENV=…` **refuses** while either is stopped, naming the stopped host, because under D38 a
stopped proxy is the estate's whole internet gone and a stopped tunnel is every persona's control plane
gone. Creating or changing either host is always a deliberate `terraform apply`: an SSM-resolved AMI
re-plans as a *replacement*, and a routine bring-up is no place to rebuild the only way in. `make status`
reads a `[D]` row's **power state from EC2**, not its state file, or a stopped host would report a burn
forever.

**The WireGuard host was also a NAT instance for the isolated tier, from Stage 6 step 5.0 until 6c step
5.8.** `wireguard-v0.4.0`'s `vpc_nat_cidrs` input turned source/destination checking **off** and added
masquerade rules, which is what let an `[E]` `amd64` build host reach the internet with no NAT gateway
anywhere: **the capability was `[D]` and the reach was `[E]`**, since a masquerade rule matches nothing
until a route table sends traffic at it. D38 ended it — there is no default route anywhere in the estate,
and the WireGuard host now lives in `VPC-Networking`, where **a route in another VPC cannot point at its
ENI**. `vpc_nat_cidrs` went with `wireguard-v0.5.0`; the build host is
[`production/buildbox/`](production/buildbox/README.md) and reaches the internet **as a client of the
explicit proxy**, so `egress/` is a hard prerequisite of a build session (its SSM endpoints are the only
door into the host) rather than a slice a build could avoid.

**`buildbox/` is raised by [`scripts/buildbox.py`](../scripts/buildbox.py), not by `make up` — by
convention, not by refusal.** It is `[E]` with a row and no refusal in `layers.py`, so `make status` sees
it, `make down ENV=production` destroys it, **and `make up ENV=production` applies it** with the account's
other three `[E]` slices — `egress/`, `workloads-egress/`, `probes/` — at 0.1664/h for a `t3.xlarge` a
Sandbox session never needs. The script exists for the reverse case: a build needs `egress/` and this slice
and neither of the other two, so it raises this one alone, checks the two prerequisites a rank cannot
express, syncs the context, opens the shell and tears down.
**Its two refusals** read the **`ssmmessages` endpoint** before applying — without it the apply
succeeds and the host is unreachable, which looks exactly like a slow boot — and **start the proxy host**,
because under design B there is no route to fail over to. Both are code in the helper rather than sentences
here (Lesson 5).

**The `[D]` slices are where the layer decides the folder rather than the topic.** The hub's durable
things — **two** Elastic IPs (the WireGuard one **transferred** from Sandbox at
6c step 4.3, so no client `.conf` moved; a new one for the proxy), two security groups, the **host private
key's Secrets Manager container** and the proxy's allow-list parameter — are `[P]` and live in
[`production/networking/hub-anchors.tf`](production/networking/), one slice away from the two `[D]`
instances that consume them. Each is named from outside the slice (the permission sets and Stage 5's
bucket policy pin **the proxy's** address since 6c step 4.12 — every VPN-only condition is keyed on the
address a client's calls *present*, and under D38 that is the proxy's, not the tunnel's; Stage 7's GitLab
rule names the group; every instance the `[D]` slices ever boot reads the key), and **a reference is only
worth writing if what it names outlives the thing using it**: an address that changed would deny every
persona every API call until each client config and the permission-set fragment were edited together.
The **value** in that secret is never Terraform's — it is put there by the user at enrollment and read by
the host at first boot ([`docs/plan/runbooks/vpn.md`](../docs/plan/runbooks/vpn.md) Part K owns every
event that touches it). The Sandbox copies went at 6c step 6.5 (2026-09-08), once the `VPN_HOMES` trim had
removed the last remote-state read of them; `sandbox/foundation/vpn-anchors.tf` is now one `removed {}`
block with `destroy = false`, forgetting the Elastic IP this account no longer owns without releasing it.

Three of the checks exist because nothing else can enforce their rule: **no `.tf` in this tree may declare
`aws_s3_account_public_access_block`** (the SCP that denies the API carves out exactly the principal every
slice applies as, so the apply would *succeed*); **no policy document in `identity/` may carry a
wildcard-account ARN** except the one statement whitelisted by `Sid`; and — since Stage 4 —
**no tracked `*.tfvars` may carry a private key**, which `./scripts/check-tfvars-shape.py` enforces by
**structure** because content is unenforceable here: the WireGuard peers roster is the one deliberately
tracked tfvars, and a WireGuard private key is 44 characters of bare base64 that no scanner can tell from
the public halves that roster commits on purpose (`pre-commit`'s `detect-private-key` reads PEM armor).
So the gate allowlists which tfvars may be tracked and which top-level keys each may assign, and fails a
`host-key.auto.tfvars` by name — a filename that should no longer exist at all, the key having moved to a
`[P]` Secrets Manager secret.

**Set `TF_PLUGIN_CACHE_DIR` before working in this tree**, or every slice downloads its own ~250 MB copy of
the AWS provider — `terraform validate` in the pre-commit hook runs `init` per slice:

```bash
export TF_PLUGIN_CACHE_DIR="$HOME/.terraform.d/plugin-cache"
```

**The by-hand change procedure is [`docs/plan/runbooks/terraform-changes.md`](../docs/plan/runbooks/terraform-changes.md)** —
the recipes, the two-commit tag order a module change requires, and the table of what to do when a hook
blocks the commit. Until Stage 8 there is no CI: that runbook *is* the pipeline.

**[`identity/sso/`](identity/sso/README.md) is the entitlement plane**, written 2026-08-16 (Stage 2
step 5). The **six persona permission sets**, their inline policies, and every **group→account
assignment**; the seventh set, `InfrastructureAccess`, is **imported**, because it is the credential the
apply runs as. Users and groups are not here and never will be — the identity seam. Two rules shape it:
a group is resolved by **display name**, and the assignments are **enumerated** while the policy floor is
discovered (D34). It reads data sources it does not own: `aws_organizations_organization`, for the single
purpose of turning an authored account **name** into the id an assignment requires — the same shape
`attachments.json` uses from the other side — and **two cross-account `terraform_remote_state` data
sources: the VPN home's `foundation/` (Stage 4 step 8.1) and the lake's `data/`** (Stage 5 pass 4c), for
the drop-box and lake-CMK ARNs the persona statements name exactly instead of wildcarding — pass 4c's
third read, the two consumers' `data/` slices, **left 2026-08-26 with the derived zone** (D19 revised).
**So `identity/sso/` applies AFTER those slices, despite ranking above them** —
`scripts/tfhygiene/layers.py`'s `RANKS` comment owns the inversion and says why the rank is not moved.

[`identity/org-policies/`](identity/org-policies/README.md) holds the organization's **preventive policy
documents** — the JSON attached to the organization root and to the OUs in
[Stage 1c step 7](../docs/plan/stages/stage-01c-preventive-policies.md), plus `render.py`, which substitutes this
organization's identifiers into the templates and writes the pasteable copies to untracked `aws/output/`.
Those documents were pasted into the Management console by hand, which is why they live in a file at all:
an import compares a document against itself instead of against a re-typing. **That folder is a slice as
well as a document store** — ten policies and ten attachments, every one of them imported and none
created, deriving the `for_each` keys from the same `attachments.json` that step 9.3's coverage check
reads.

**Stage 6 put the SageMaker Unified Studio surface on disk** (2026-08-21). These three slices read as a
set: one design split by *which account is allowed to hold what*, D26's argument made concrete:

- **`data-governance/governance/` `[P]` — the registry, and nothing else.** The DataZone V2 domain, its
  execution and service roles, the two project profiles, and the two `CREATE_PROJECT_FROM_PROJECT_PROFILE`
  grants on the root domain unit (`grants.tf`, 2026-08-22 — without them the profiles were templates
  nobody could instantiate). **No compute lives here and none ever may**:
  `sagemaker:Create*` is denied in this account by the `Data` OU document, a deny that stays free because
  no blueprint is enabled here, and Stage 6 step 0.4 reads the slice's own plan for any `aws_sagemaker_*`
  resource before every apply.
- **`sandbox/sagemaker/` `[P]` — the runtime's prerequisites**, one module
  (`terraform-modules/sagemaker-prereqs/`). It was applied **twice** until 2026-09-06, in Sandbox and in
  Development, so the two could not drift; **Stage 6b step 1.7 destroyed the Development copy and deleted
  the slice** — that account is becoming the headless `Staging` and provisions no Studio project. The blueprint
  provisioning and manage-access roles, the account's project CMK, the `/awsds/<env>/studio` log group,
  the **D13 permissions boundary** the blueprint imposes on every project role it authors — and, since
  v0.3.x (2026-08-22), the projects bucket `awsds-<env>-smus-projects` (SSE under the project CMK) and the
  11 per-configuration `CREATE_ENVIRONMENT_FROM_BLUEPRINT` grants. **They declare
  no project environment and never will** — DataZone owns those, and a Terraform resource for one would
  fight the blueprint.
- **`production/registry/` `[P]`** — written under Stage 7 step 5 and applied a stage early, because Stage 6
  step 5.0 has nowhere to push the first `dev-env` image otherwise: the `base`/`dev-env` ECR pair,
  CodeArtifact, the slice's own key, and the consumer policies built from the D35 map.
- **`sandbox/dev-env/` `[P]` — the house image, registered** (Stage 6d step 2, 2026-09-10): the SageMaker
  AI image, one immutable version pointing at `awsds-prod-ecr-dev-env:<tag>`, an app image configuration
  per app type, and the role SageMaker assumes to read that repository across the account boundary. It is
  the one slice here whose only real input lives in another account, so it reads
  `production/registry/`'s state rather than carrying an ECR URI. **What it does not hold is the
  attachment**: `CustomImages` is a field of the SageMaker AI domain the `Tooling` blueprint provisions,
  so making the image *selectable* is a hand step — [`docs/plan/runbooks/dev-env.md`](../docs/plan/runbooks/dev-env.md).
  Stage 8 step 1's pipeline takes the slice over (INT-18).

**Two of them apply twice, and the second apply is a different sitting rather than a continuation.** The
SMUS account association is **console-only — there is no public API** — so the blueprint configurations
(in each member's `sagemaker/`) and the project profiles (in `governance/`) cannot exist until the
account association exists (it auto-accepts — org-scoped RAM share, no invitation is ever issued;
measured 2026-08-21). Both halves ride on `SMUS_ASSOCIATED` in `scripts/tfhygiene/backend.py`, a
list whose rows are **measurements, not intentions**.

## What decides where something goes

1. **Which account?** → the top-level folder. The account is the only hard boundary AWS offers
   ([`README.md`](../README.md), "Account segregation"), so it is the first cut.
2. **Which slice?** → the sub-folder. A slice is one Terraform state and one `apply`. The seam between two
   slices is a *reason*, not a size: `identity/` is split into `sso/` and `org-policies/` because the two
   reach their objects through **different delegations**; `production/pki/` is split from `foundation/`
   because foundation is opened to change a CIDR and that edit would otherwise decrypt the root CA; and
   the hub's anchors sit in `production/networking/` rather than in `production/vpn/` or `production/proxy/`
   because they are `[P]` and the hosts are `[D]`. **Question 3 answered differently for two halves of one
   topic is a slice boundary** — the general form of all three.
3. **Which layer?** → `[P]` persistent, `[D]` dormant (stopped, not destroyed), `[E]` ephemeral (destroyed
   between sessions). This is principle 7 — *pay nothing while idle* (D11) — and it is a property of the
   slice, so `make down` can act on whole slices rather than on hand-picked resources.

## The account folders

Names only — **no account id ever enters a tracked file**. The profile column is the one Stage 1b step 5
created; it is also the answer to "who runs `terraform apply` here".

| Folder | Account | OU | Profile that applies it |
|---|---|---|---|
| `identity/` | Identity | `Identity` | `awsds-infra-identity` |
| `sandbox/` | Sandbox Account 1 | `Sandboxes` | `awsds-infra-sandbox-1` — **one such folder per business unit** (D35), N is 1 today |
| `data-governance/` | Data Governance | `Data` | `awsds-infra-data` |
| `staging/` | Staging Account | `Workloads` | `awsds-infra-staging` — **the renamed `Development`, not a vend**: the quota refused that (2026-09-05), so Stage 6b converted the account instead |
| `production/` | Production | `Workloads` | `awsds-infra-prod` — **the only account with more than one VPC** (three since 2026-09-06), which is why `VPC_CIDRS` and `VPC_NAME_SUFFIXES` are keyed by **(account, slice)** rather than by account |

**No folder for Management, Log Archive, Audit or Policy Canary, and each absence is a rule.** Management is
bootstrap-only and never Terraform (principle 1); Log Archive and Audit are Control Tower's, and editing
their contents is landing-zone drift; `Policy Canary` is deliberately empty (D29) — the day something is
created there, the account has stopped being what it is for.

## What does not live in this tree

- **`terraform-modules/`** — the reusable code. `terraform-live/` composes; it does not define. The roster,
  and what each module is for, are [`terraform-modules/README.md`](../terraform-modules/README.md)'s — re-typing
  the count here is how the two drift. Every caller in this tree pins one **by git tag**, and the two-commit
  order that requires is the runbook's.
- **People.** Identity Center **users, groups and memberships** stay in the directory; only **entitlements**
  — permission sets, boundaries, group→account assignments — are Terraform, in `identity/sso/`. The seam and
  its reasoning are in `docs/plan/conventions.md`, "The identity seam".
- **OUs and accounts.** They are created from the console (D34), outside every state. Nothing here declares
  them, so they cannot drift — but a new OU can end up with no policy attached and a new account outside
  every enumerated condition, with `terraform plan` reporting *"No changes"* either way. Hence the rule that
  survives it: **the floor is discovered and the grants are enumerated** — where "discovered", since 1c put
  every must-cover-everything document on the **organization root**, means *inherited* coverage plus a
  `make check` that fails on an OU nobody accounted for, **not** a `for_each` that attaches. See
  [`docs/plan/conventions.md`](../docs/plan/conventions.md), the D34 bullet, for why the distinction is load-bearing.
- **`aws_s3_account_public_access_block`** — never declared in any slice. The account-level setting is made
  by hand in Stage 1c step 7.4 and then denied by the SCP of step 7.5; it reads exactly like something that
  belongs in `foundation/`, which is why the exclusion is written down in three places.
- **The Region restriction.** It is a Control Tower **managed control** (`CT.MULTISERVICE.PV.1`, decision 6),
  not a hand-written document — so it is not in `identity/org-policies/` and not in any slice.

## Pointers

| Question | File |
|---|---|
| The full slice-by-slice tree, with the `[P]`/`[D]`/`[E]` layer of each | [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6 — **the authority** |
| Naming, tags, the IAM rules, the identity seam | [`docs/plan/conventions.md`](../docs/plan/conventions.md) |
| What the policy documents are and what each may not become | [`identity/org-policies/README.md`](identity/org-policies/README.md) |
| **What every policy statement does, and why it exists** — all four types | [`identity/org-policies/POLICIES.md`](identity/org-policies/POLICIES.md) |
| **What governs the lake** — bucket-policy branches, the key policy, tag assignments, LF grants | [`data-governance/data/README.md`](data-governance/data/README.md) — the same one-row-each discipline, for the lake's own controls |
| **What governs the lake's CONSUMER side** — the per-account CMK policy, the account's `DataLakeSettings`, the four re-grants (the derived zone and workgroup left 2026-08-26 — D19 revised) | [`terraform-modules/consumer-data/README.md`](../terraform-modules/consumer-data/README.md) — one README for the module both `data/` slices call, because the design lives once and is applied twice; the persona's identity-side half is `identity/sso/`'s |
| Which stage builds a given slice | [`docs/plan/stages/INDEX.md`](../docs/plan/stages/INDEX.md) |
| What is deployed right now | [`aws/INDEX.md`](../aws/INDEX.md) and [`docs/AWS_STATE.md`](../docs/AWS_STATE.md) |

---

*Plan core: [GENERAL_PLAN.md](../docs/GENERAL_PLAN.md) · Rules: [`docs/plan/conventions.md`](../docs/plan/conventions.md)*
