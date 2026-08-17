# `terraform-live/` — the deployed tree

**One folder per controlled AWS account, each sliced into independently applied units.** This is the tree
that describes what actually exists in an account; the reusable code it calls lives in
`terraform-modules/` and is consumed **by git tag, never by branch** — a module that moves under a caller
is a broken caller.

> **The authoritative layout is [`docs/plan/conventions.md`](../docs/plan/conventions.md) §6, and it is not repeated
> here.** That file carries the full annotated tree with every slice and its `[P]`/`[D]`/`[E]` layer, on
> purpose: two copies of a directory tree drift, and the copy that drifts is always the one somebody reads
> first. **This README explains how the tree is organised and what is in it today.** When the two disagree,
> conventions §6 wins and this file is the one that was not updated.

## What is here today

**Seventeen slices across five account folders: ten `[P]`, one `[D]`, six `[E]`.** That is a summary, not
an authority — `make slices` prints the live table, and a slice that reaches disk without a row in it fails
`make check`.

**Five `bootstrap/` slices, and they are one slice copied five times — Stage 2 steps 1, 2 and 3, 2026-08-15.**
`sandbox/`, `development/`, `data-governance/`, `production/` and `identity/` each carry the same
`main.tf`, `variables.tf`, `outputs.tf`, `providers.tf`, `versions.tf` and `.terraform.lock.hcl` — **the state
bucket and the KMS key that encrypts it, and nothing else**. **All five have applied and hold their own
state** — `production/` with a second key besides. **No `staging/`**: the account is unvended (step 3.2), and a
folder for an account that does not exist is a folder that fails at `init` with a message about S3.

**Two files are allowed to differ, and both are files of their own so the rule can be blunt:** `backend.tf`,
which is commented out until a slice has migrated, and `production/bootstrap/pki-key.tf`, D36's second state
key (step 3.4). **`./scripts/check-bootstrap-parity.py` enforces the rest** — byte-identical, `backend.tf`
compared with the comment markers stripped, and any other unshared file a failure. A module would have been
the other answer and step 2.3 rules it out: modules are consumed **by git tag**, which cannot exist before
`terraform-modules/` does.

**Two files per slice are GENERATED and untracked**, because a `.tf` file may hold neither of the values they
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

**The rest of `docs/plan/conventions.md` §6's tree is not on disk, and that is the deliberate reading of step 1.**
Git does not track empty directories, so a skeleton of ~35 empty slices means ~35 `.gitkeep` files — a second
copy of §6's listing, in a form that drifts silently and that no reader consults. Each slice folder is created
by the stage that first writes a `.tf` file into it, and **§6 stays the one place the layout is written down**.

**`versions.tf` is byte-identical in every slice**, because Terraform has no repository-wide pin: the
constraint belongs to each root module. The parity check above is what keeps the copies from drifting
(Lesson 14).

**Stage 3 put a network on disk in the three accounts that have one — `sandbox/`, `development/` and
`production/`, split three ways (2026-08-16, applied and measured).** `foundation/` is `[P]`: the VPC, its
six subnets across three AZs, the gateway endpoints and the private hosted zones, plus the peerings and
zone associations pass 2 adds on a second apply of the same slice. `egress/` is `[E]` — the NAT gateway
and the interface endpoints, which are this tree's entire hourly bill. `probes/` is `[E]` as well and is
an **instrument rather than infrastructure**: the hosts the perimeter, both peerings and the flow logs
were measured from, kept on disk because a probe that has to be rewritten is a probe nobody re-runs.
**`data-governance/` has no `foundation/` and never will** (D22 — a registry needs no VPC), which is why
`layers.py` carries an explicit comment where its row would be. What stands right now is the `[P]` half
alone: the `[E]` slices are destroyed and the tree bills **USD 0.0000/h** between sessions, while
`foundation/` re-plans `No changes` — that pair is D11's proof, not an accident of timing.

**Seven checks stand over this tree — Stage 2 steps 9, 3.5 and 8.1, plus Stage 4's — and there is no CI to
run them in.** Until Stage 8 puts them in a pipeline the surfaces are `pre-commit` and the repository's
`Makefile`, both calling the same scripts:

```bash
make check      # offline: region literals, indexed AZs, account-level BPA, wildcard ARNs,
                #          bootstrap parity, slice layers, tracked tfvars shape, the policy index
make check-ou   # needs an SSO session as the infrastructure user on Identity
```

**Every slice folder in this tree must declare its D11 layer** in
[`scripts/tfhygiene/layers.py`](../scripts/tfhygiene/layers.py) — `[P]` persistent, `[D]` dormant, `[E]`
ephemeral (Stage 2 step 8.1, 2026-08-16). **Since Stage 3 pass 3 the `egress/` slices are `[E]` with an
`usd_per_hour` copied from the measured `docs/PRICING.md` §3 rows**, so `make up ENV=…` / `make down ENV=…`
act for real and `make status` reports a burn — the end-of-session reading is `./aws/egress.py` §6. A
slice created without a row fails the sixth check, because `make down` skips what it has never heard of
in silence — and for an ephemeral slice that is a bill nobody is told about. `make slices` prints the table.

**Since Stage 4 pass 1 there is a `[D]` row too — [`sandbox/vpn/`](sandbox/vpn/README.md) — and `[D]` is
not a slower `[E]`.** `make down` **stops** that host and destroys nothing; `make up` starts it; creating
or changing it is always a deliberate `terraform apply`, because an SSM-resolved AMI re-plans as a
*replacement* and a routine `make up` is no place to rebuild the only way into the network. All three are
one refusal in `layers.py` (the fifth), and the rank decides which side of the `[E]` loop the stop/start
lands on: `vpn` at 40 sits below `egress` at 50, so **the tunnel is the first thing up and the last thing
down** — the order that becomes load-bearing once Stage 4 step 8.3 makes every AWS API call exit through
its Elastic IP. `make status` reads a `[D]` row's **power state from EC2**, not its state file, or a
stopped host would report a burn forever.

**That slice is also this tree's clearest instance of the layer deciding the folder, not the topic.** The
VPN's three durable things — the Elastic IP, the host security group and the **host private key's Secrets
Manager container** — are `[P]` and live in [`sandbox/foundation/vpn-anchors.tf`](sandbox/foundation/),
one slice away from the `[D]` instance that consumes them. Each is named from outside Stage 4 (the
permission sets pin the address, Stage 5's bucket and EFS rules and Stage 7's GitLab rule name the group,
and every instance the `[D]` slice ever boots reads the key), and **a reference is only worth writing if
what it names outlives the thing using it**: after step 8.3 an address that changed would deny every
persona every API call until each client config and the permission-set fragment were edited together.
The **value** in that secret is never Terraform's — it is put there by the user at enrollment and read by
the host at first boot ([`docs/plan/runbooks/vpn-keys.md`](../docs/plan/runbooks/vpn-keys.md) owns every
event that touches it).

Three of them exist because nothing else can enforce their rule: **no `.tf` in this tree may declare
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

**And [`identity/sso/`](identity/sso/README.md) — the entitlement plane, written 2026-08-16 (Stage 2 step 5).**
The **six persona permission sets**, their inline policies, and every **group→account assignment**; the
seventh set, `InfrastructureAccess`, is **imported**, because it is the credential the apply runs as. Users
and groups are **not** here and never will be — that is the identity seam. Two rules shape every file in it:
a group is resolved by **display name**, and the assignments are **enumerated** while the policy floor is
discovered (D34). It reads one data source it does not own, `aws_organizations_organization`, for the single
purpose of turning an authored account **name** into the id an assignment requires — the same shape
`attachments.json` uses from the other side.

The one older exception is [`identity/org-policies/`](identity/org-policies/README.md), which holds the organization's
**preventive policy documents** — the JSON attached to the organization root and to the OUs in
[Stage 1c step 7](../docs/plan/stages/stage-01c-preventive-policies.md), plus `render.py`, which substitutes this
organization's identifiers into the templates and writes the pasteable copies to untracked `aws/output/`.
Those documents were pasted into the Management console by hand, which is why they live in a file at all:
an import compares a document against itself instead of against a re-typing. **Since 2026-08-16 that folder
is a slice as well as a document store** — ten policies and ten attachments, every one of them imported and
none created, deriving the `for_each` keys from the same `attachments.json` that step 9.3's coverage check
reads.

## The three questions that decide where something goes

1. **Which account?** → the top-level folder. The account is the only hard boundary AWS offers
   ([`README.md`](../README.md), "Account segregation"), so it is the first cut.
2. **Which slice?** → the sub-folder. A slice is one Terraform state and one `apply`. The seam between two
   slices is a *reason*, not a size: `identity/` is split into `sso/` and `org-policies/` because the two
   reach their objects through **different delegations**; `production/pki/` is split from `foundation/`
   because foundation is opened to change a CIDR and that edit would otherwise decrypt the root CA; and
   the VPN's anchors sit in `sandbox/foundation/` rather than in `sandbox/vpn/` because they are `[P]` and
   the host is `[D]` — **question 3 answered differently for two halves of one topic is a slice boundary**,
   which is the general form of all three.
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
| `development/` | Development | `Interactive` | `awsds-infra-dev` |
| `data-governance/` | Data Governance | `Data` | `awsds-infra-data` |
| `staging/` | Staging | `Workloads` | **none yet — the account is unvended**, held on the account cap |
| `production/` | Production | `Workloads` | `awsds-infra-prod` |

**No folder for Management, Log Archive, Audit or Policy Canary, and each absence is a rule.** Management is
bootstrap-only and never Terraform (principle 1); Log Archive and Audit are Control Tower's, and editing
their contents is landing-zone drift; `Policy Canary` is deliberately empty (D29) — the day something is
created there, the account has stopped being what it is for.

## What deliberately does not live in this tree

- **`terraform-modules/`** — the reusable code. `terraform-live/` composes; it does not define. Six exist
  since Stages 3-4 (`vpc`, `vpc-egress`, `s3-bucket`, `kms-key`, `iam-role`, `wireguard`), and every caller
  in this tree pins one **by git tag** — the two-commit order that requires is the runbook's.
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
| Which stage builds a given slice | [`docs/plan/stages/INDEX.md`](../docs/plan/stages/INDEX.md) |
| What is deployed right now | [`aws/INDEX.md`](../aws/INDEX.md) and [`docs/AWS_STATE.md`](../docs/AWS_STATE.md) |

---

*Plan core: [GENERAL_PLAN.md](../docs/GENERAL_PLAN.md) · Rules: [`docs/plan/conventions.md`](../docs/plan/conventions.md)*
