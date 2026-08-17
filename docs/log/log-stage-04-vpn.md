# Log — Stage 4 — VPN access

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-04-vpn.md`](../plan/stages/stage-04-vpn.md).*

*Exceptions, named by SUBJECT so the provenance is not guessed later — the same convention
[Stage 3's log](log-stage-03-networking.md) adopted.*

*The five entries below are exceptions: on **2026-08-16** the user authorised Claude, explicitly, to
create this file and write the first two directly, and on **2026-08-17** to write the third, the
fourth and the fifth the same way. The first three record no AWS call — one is a repository change
merged with the Stage 3 teardown, one is pass 1 authored and gated but **not applied**, and the third
is a design review propagated through the repository. **The fourth and the fifth are different in
kind: they are the stage's first AWS writes**, applied by Claude on the user's explicit authorisation
of those specific steps, and written here by the same authorisation. **The fifth also records one
step Claude did not perform** — step 4.3, run by the user on the laptop — and says so where it does.
The standing rule is unchanged: the next entry is the user's.*

---

## 2026-08-16 — Step 1.3, two of its three edits (merged alongside the Stage 3 teardown)

**No AWS call in this entry.**

- `"vpn": 40` added to `RANKS` in `scripts/tfhygiene/layers.py`, **between `foundation` (20) and
  `egress` (50)** — correcting the step's earlier "after `egress`", which inverted both consequences it
  claimed.
- `dormant()` in `scripts/slices.py` given its body: stop/start by the Name tag `awsds-<env>-<slice>`,
  **derived from the row rather than written a second time**, never destroying, and printing every
  outcome including the two different nothings ("no instance tagged X" and "already stopped").
- **The `("sandbox", "vpn")` row was added, `./scripts/slices.py check` failed on it exactly as it
  should, and it was withdrawn** to land with the slice. The rank went in early because the order was
  the part got wrong once.

## 2026-08-16 — Pass 1 authored: the `wireguard` module, the `[P]` anchors, and the first `[D]` slice

**No AWS call in this entry either — nothing is applied.** The network is still torn down at
USD 0.0000/h; both applies wait on the keys (4.1, 4.3) and on authorisation.

### What was written

| Where | What |
|---|---|
| `sandbox/foundation/vpn-anchors.tf` | Step 2: the Elastic IP and the WireGuard security group, `[P]`, with step 3.1's rules in the same file — inbound UDP/51820 from the world and nothing else. Three outputs: allocation id, public IP, group id |
| `terraform-modules/wireguard/` | The `t4g.nano` on the SSM-resolved AL2023 arm64 AMI, IMDSv2 required, `source_dest_check` deliberately **on**, `user_data_replace_on_change`, `zone_index`; the role through the `iam-role` module with `permissions_boundary = null`; the log group `/awsds/<env>/vpn` at 30 days; the alarm; the EIP association; the user data as a `templatefile` |
| `terraform-live/sandbox/vpn/` | The slice — one module call — plus a `README.md` carrying the shape of the hand-written `peers.auto.tfvars`, which is the one thing this slice cannot generate |
| `scripts/tfhygiene/backend.py` | `peer_cidr` emitted to `vpn/` alone (step 4.2). It was in the table since Stage 3 and reached no slice until now |
| `scripts/tfhygiene/layers.py` | The withdrawn row, back with the slice: `[D]`, `usd_per_hour = 0.0042` from the measured `t4g.nano` row |

### The entry's finding: the first `[D]` row exposed three defects in the D11 machinery

The targets were written before any `[D]` slice existed, and all three failures are the same shape — the
code did not implement its own documented contract.

1. **`make down` would have destroyed the host.** `is_refused()` recognised `[P]` and nothing else, so a
   `[D]` row joined the very list `down` runs `terraform destroy` over — against D11, against
   conventions 5.1, and against `slices.py`'s own header line ("up: start the `[D]` slices, apply the
   `[E]` ones"). Now **refusal 5**, on the *layer* rather than on a named slice, and it refuses `up` too:
   the SSM-resolved AMI re-plans as a **replacement**, so a routine `make up` is no place to rebuild the
   only way into the network.
2. **The rank was not honoured on the way down.** The `[D]` hook ran before the `[E]` loop on *both*
   actions — stopping the tunnel and only then destroying two slices over the AWS API. That is the
   self-inflicted lockout rank 40 exists to prevent. The hook now sits on the side of the loop its rank
   says: first up, last down. If an `[E]` destroy fails, the host is left **running** on purpose.
3. **`make status` would have reported a burn forever.** It counted resources in the state file, where a
   stopped instance is still present — so the USD 0.0000/h reading Stage 3 closed on could never have
   come back. It now reads the **power state from EC2**, by the same Name tag the hook uses (no
   `terraform init` needed), and prints that a stopped host still bills its EBS volume and its `[P]`
   Elastic IP, monthly rather than hourly.

Verified with `--dry-run`: `down` refuses `vpn` with the reason printed, destroys `probes` then `egress`,
and only then stops the host; `up` is the mirror.

### Decisions taken

| # | Settled as |
|---|---|
| 2 | **The EC2 status-check alarm**, `awsds-<env>-vpn-health`, with `treat_missing_data = "notBreaching"` — a stopped instance publishes no status checks, so the default would raise INSUFFICIENT_DATA after every `make down`. **It notifies nobody**: no SNS topic exists in this account, so what it buys today is a state `VP-6` can measure |
| 4 | **The host key pair is generated on the laptop** and the private half written by the user into `peers.auto.tfvars`. Peers are a **map** keyed by device name with an authored `host` number, so revoking a device cannot renumber anybody else's tunnel address |

### Two things recorded as unverified rather than assumed

- **Decision 4's cost is wider than the decision named.** It accounted for the key transiting Terraform
  state; step 4.3 also puts it in the instance's **user data**, readable by any principal holding
  `ec2:DescribeInstanceAttribute` in this account. Today that is `InfrastructureAccess` alone — but this
  is the account that hosts notebook execution roles from Stage 6. The alternative, a SecureString under
  `/datascience/<env>/…`, is named here so the choice is on the record.
- **The `amazon-cloudwatch-agent-ctl` invocation is not verified.** Every field of the agent's JSON was
  read off the configuration reference and matches; the command-line page did not render on three fetch
  attempts. So step 5 of the user data is **non-fatal** — a log shipper must not be able to break the
  only path into the network — and it prints its own exit status followed by `-a status`. The first boot
  answers it; quote the page here when it does.

### Three smaller findings

- **`wg show all dump` prints the interface's private key on its first line**, so the handshake sampler
  uses `wg show all latest-handshakes` — public keys and timestamps only. The dump form would have
  shipped the server key into a CloudWatch log group.
- **No checkov check fires on a world-open ingress rule on an arbitrary port** — 22, 3389 and 80 are
  checked and 51820 is not. So "exactly one world-open rule in the whole estate" is enforced by
  `./aws/networking.py` §9 and `VP-3` alone; the linter is silent about it in both directions.
- **`CKV2_AWS_5` fired on the `[P]` security group** because the attachment is one slice away — which is
  step 2.2 itself. Skipped with the reason, the same shape the `vpc` module's endpoint SG already carries.

### Gates

`terraform fmt`, `make check`, `tflint` (the module and both slices), `checkov` **0 failed**
(335 / 670 passed), `ruff` — all green. The module alone passes `terraform validate`. The user data was
**rendered for real** through `templatefile()` against sample values and checked with `bash -n`.

### Not done, and why

- **Step 8 (`identity/sso/`) is untouched**: it is pass 3 and runs only after pass 2 has proven the
  tunnel — the deny pins every persona to an address that must demonstrably exist and route first.
- **The `wireguard-v0.1.0` tag is not cut**: a module and its first caller cannot share a commit, so the
  module lands first, the tag goes between, and the slice plus its `layers.py` row follow.

### Repository

WireGuard 1.0.16 installed on the laptop and recorded in `CLAUDE.md`'s tool list. That line took the file
past the 20 KB budget `make check-docs` enforces, so the `Claude LOG` re-trim owed since Stage 3 closed is
now what stands between that target and a green run.

## 2026-08-16 — Third design review: decision 4 revised, the host key moves to Secrets Manager

**No AWS call in this entry.** A chat review on 2026-08-16, propagated through the repository the same
night and committed on 2026-08-17. Nothing is applied; the estate is still the Stage 3 teardown at
USD 0.0000/h.

### What changed, and what did not

The host's private key leaves the tfvars/user-data path for the `[P]` secret
`awsds-<env>-vpn-host-key`. What did **not** change is the reasoning the second review settled: the pair
is still generated on a laptop, never by Terraform and never on the host, because a key generated on
first boot lives only inside an instance that the SSM-resolved AMI and `user_data_replace_on_change`
destroy on schedule (Lesson 4). What changed is **custody**.

| Where | What it holds now |
|---|---|
| `sandbox/foundation/vpn-anchors.tf` | The secret container — **no `aws_secretsmanager_secret_version` anywhere** (Stage 7's `gitlab-secrets.json` idiom, one stage early: the container is Terraform's, the value never is) — plus its resource policy, Sid `DenyValueReadExceptHostAndInfrastructure`: `Deny` on `secretsmanager:GetSecretValue` to every principal except the instance role and `AWSReservedSSO_InfrastructureAccess_*`. A fourth output, the ARN |
| `terraform-modules/wireguard/` | `host_private_key` → `host_key_secret_arn`; `iam.tf` grants `GetSecretValue` on exactly that ARN; the user data gained section (3), a fetch loop |
| `terraform-live/sandbox/vpn/` | The key variable is **gone**; the ARN arrives through `terraform_remote_state`. `host-key.auto.tfvars` no longer exists in the design — the tracked roster and its shape gate stay |
| `./aws/vpn.py` | `VP-9`: the secret exists, carries its deny Sid, and `RotationEnabled` is false |

The consequence, stated as measurables for the first boot to confirm (verification (viii)): the user data
carries a pointer, so `ec2:DescribeInstanceAttribute` yields an ARN; state keeps the provider's SHA-1 of a
script with no key in it; every read of the value is a **CloudTrail management event**; and the at-rest
copies are two — the secret and `wg0.conf` on the `[D]` EBS volume.

### Why the containment is on the object and not in the permission sets

One resource policy reaches every principal this account will ever hold — today's personas and **Stage 6's
notebook execution roles alike** — with no per-set fragment to forget (Lesson 14's good direction). It is
scoped to `GetSecretValue` alone, deliberately: denying `secretsmanager:*` would put the container's own
management behind a deny only its author could lift, an availability trap with no confidentiality gain,
since `GetSecretValue` **is** the secret. Lesson 18 stands and is not dodged — this policy cannot
constrain `InfrastructureAccess`, which authors it, and does not try to: Infrastructure is the enrollment
writer and the recovery reader, carved out by name. The instance-role ARN is a **name contract** with the
module (`awsds-<env>-vpn`), because `foundation/` cannot read a `[D]` slice's outputs.

### The prices, accepted knowingly

- **USD 0.40/month + 0.05/10k reads**, measured (`docs/PRICING.md`).
- **The first boot gains a dependency**: the fetch retries until this same apply's EIP association gives
  the host a route and until the value is enrolled. It is a loop that *names its cause* on every retry —
  a hang with a name, never a timeout into a keyless tunnel — and it is exercised only at instance
  replacement, when an operator is already mid-apply.
- **Rotation costs a step**: the new value is invisible to Terraform, so it is `put-secret-value` **plus**
  a deliberate `apply -replace` plus every client config in the same minute (runbook §3).
- **Automatic rotation is forbidden forever** — a rotation Lambda would replace the key without touching a
  single client config: the keys runbook's one rule, violated by machine, on schedule. `VP-9` fails if
  `RotationEnabled` ever reads true, and `CKV2_AWS_57` is skipped with that reason rather than satisfied.

### What this closes from the previous entry

The 2026-08-16 pass-1 entry recorded that **decision 4's cost was wider than the decision named** — the key
in the user data, in the account that will host Stage 6's execution roles — and named a SecureString under
`/datascience/<env>/…` as the alternative on the record. That reading is what this review answers, and the
SecureString lost on a specific point: a parameter has no resource policy to carry the deny above. An S3
sibling bucket beside the state bucket was weighed too — it reads through the gateway endpoint *before*
the EIP associates, which is its one advantage — and lost on two: its reads are **data events**, which
CloudTrail does not record by default, and containment would have meant extending the state deny's
`awsds-*-tfstate` name pattern, since a differently-named bucket matches nothing.

### Two corrections made while writing it

- **The runbook's premise inverted.** It was built on reconstruction *from the user data*; with the key no
  longer there, §§0-1 are rebuilt around the `[P]` secret, and loss now has five cases rather than one —
  including `restore-secret` inside the 30-day recovery window. The one loss that still forces rotation is
  a secret deleted **past** that window, which is why deleting it is never routine housekeeping.
- **A gate of my own that proved nothing.** The user data was checked with `bash -n` against the
  `terraform console` output while it was still JSON-escaped, so the check passed on text that was not the
  script. Decoded and re-run: syntax clean, `PrivateKey = $HOST_KEY` and the fetch loop intact (Lesson 13
  — a check that passes either way is not a check).

### Gates

`terraform fmt` · `make check` **OK** (the tfvars-shape gate among them) · `tflint` on the module and both
slices · `checkov` **0 failed** (335 / 670 passed) · `ruff` check and format · `terraform validate` on the
module and on `sandbox/foundation/` · the user data **rendered for real** through `templatefile()` and
`bash -n` on the decoded script.

## 2026-08-17 — Step 2.3 applied: the VPN's `[P]` anchors exist

**The stage's first AWS write.** Profile `awsds-infra-sandbox-1` (`InfrastructureAccess` in
`Sandbox Account 1`), [Recipe A](../plan/runbooks/terraform-changes.md) followed end to end: generated
files, `init -reconfigure` (the working copy had been left by a `-backend=false` validate), plan written
to a file **outside the repository**, read in chat, and the apply run against that same file.

`4 to add, 0 to change, 0 to destroy` — purely additive, none of Stage 3's 31 resources touched.
Re-plan **`No changes`** at `-detailed-exitcode 0`.

| What | Reading |
|---|---|
| Elastic IP | allocated, **unassociated** — step 1.4 is what consumes it |
| `awsds-sandbox-vpn` SG | the estate's only world-open rule, UDP/51820 (`VP-3` pass) |
| `awsds-sandbox-vpn-host-key` | container only, **no value** — its deny policy attached and rotation off (`VP-9` pass, the check's first real reading) |

`./aws/vpn.py` and `./aws/networking.py` both **0 FAILED**; `NT-4` still clean on the client range;
`make check` OK. The estate leaves USD 0.0000/h for a **monthly** floor of ~USD 4.05 (EIP 3.65 +
secret 0.40). `make status` still reads 0.0000/h and is right to — these are `[P]`, billed monthly,
which that target's own footer says.

### The entry's finding: `VP-2` said nothing about the state this step creates

Between an allocated Elastic IP and the host that consumes it, `VP-2` fell through both of its branches
and emitted **no line at all** — so an allocation nobody ever attaches, which is the one thing that
check exists to price, would have billed in silence for as long as it lasted. Same shape as the two
instrument defects Stage 3 caught, and found the same way: by running it (Lesson 13). It now emits a
note naming the address and the window in which that reading is legitimate — *expected between 2.3 and
1.4; standing longer than that stretch, it is an orphan allocation rather than a stage in progress*.
`docs/AWS_STATE.md` section C carries the new state with that note as its disposition.

### The plan's second finding, fixed in the same sitting: `CostCenter` said `stage-03`

Read off the plan before the apply: all four resources inherited `CostCenter = stage-03` from the
slice's provider `default_tags`, while being Stage 4's. The convention is **the stage that created the
resource**, and a slice-level default cannot tell two stages apart inside one slice — `foundation/` now
holds resources from both. Fixed with a per-resource override (`local.vpn_anchor_tags`, merged into the
three taggable resources; the secret policy carries no tags), deliberately as the **whole** of the
difference: the other four mandatory tags still arrive from `default_tags`, unrepeated (Lesson 14).

Applied as `0 to add, 3 to change, 0 to destroy` — **in-place, nothing replaced**, which is what made
this cheap to fix after the fact rather than a reason to have blocked the first apply. Read back **from
AWS rather than from Terraform** — `ec2 describe-tags` and `secretsmanager describe-secret` — all three
`stage-04`; re-plan `No changes`.

### Not done, and why

- **Step 4.3 has not run**: the secret is an empty container until the key pair is generated and
  enrolled with `put-secret-value`. It must precede step 1.4, or the first boot's fetch simply waits.
- **Nothing consumes the anchors yet** — `sandbox/vpn/` is authored and gated but not applied.

---

## 2026-08-17 — Steps 4.3 and 1.4: the tunnel endpoint boots, and the plan that followed it wanted to rebuild it

### Step 4.3, by the user, on the laptop — the one step in this entry Claude did not perform

The host key pair was generated outside the repository and the private half enrolled with
`put-secret-value … --secret-string file://host-private.key`; the user reported the round-trip
verification printing **MATCH** — the `get-secret-value | wg pubkey | diff - host-public.key` form,
which keeps both halves off the terminal. What Claude confirmed independently, and only this: the
secret's **metadata** now carries one `AWSCURRENT` version (last changed 04:25Z) with
`RotationEnabled` unset, and CloudTrail carries the user's two verification reads at 04:25:36Z and
04:27:00Z under `AWSReservedSSO_InfrastructureAccess_…`. **The value itself was never read here, and
the generation was never observed** — that is the design, not a gap in the record.

### Step 1.4 — the apply

`terraform apply` on `sandbox/vpn/`, the repository's first `[D]` slice, added **9 resources**. The
instance alone took **11m13s**, and CloudTrail says why: **13 `RunInstances` refused with
`Server.InsufficientInstanceCapacity`** in `usw2-az1`, between 04:30:37Z and 04:37:13Z with growing
backoff, before the 14th succeeded at 04:41:35Z. This is the shortage Stage 3 measured and the reason
the module carries `zone_index` — **which was not needed**: the provider's own retry outlasted it. The
refusal text named `us-west-2a/c/d` as having capacity, so if a future build ever exhausts the retry,
`zone_index = 1` is the one-variable answer rather than a redesign.

Host `i-0bbeb49f0676a2257`, `t4g.nano`, private `10.20.160.63`, the `[P]` address associated one
second after the instance finished creating.

### The boot answered three verifications, and took 40 seconds end to end

- **(i) — YES, and the number is the answer: 35 seconds.** `dnf -y install wireguard-tools
  iptables-nft amazon-cloudwatch-agent` ran between the `(1)` say-lines at 04:41:47Z and 04:42:22Z,
  entirely through `foundation/`'s S3 **gateway** endpoint — no NAT in the path, the prefix-list route
  winning over the internet gateway. **Stage 3's 9.3 allow-list is complete for AL2023 core and the
  CloudWatch agent**, and Stage 3 verification (iii) is answered with it. The failure mode this was
  budgeted against — a hang rather than an error — never appeared.
- **(viii) — the audit half confirmed, the state half wrong, and the retry half still untested.** The
  key fetch took **two seconds and zero retries**: the EIP association completed one second after the
  instance did, and cloud-init only reached section (3) 35 seconds later. So the loud retry loop is
  insurance whose exercise is still owed — it is honest to say it exists, not that it works.
  `(3) key in hand (base64 length 44)` confirms step 4.3's `tr -d '\n'` end to end. CloudTrail shows
  `GetSecretValue` at 04:42:24Z, `managementEvent: true`, principal
  `assumed-role/awsds-sandbox-vpn/i-…`, no error — decision 4's audit claim, exercised rather than
  assumed (Lesson 20).
- **(iii) — the endpoint half.** The SSM agent registered `Online` (v3.3.4624.0) and an
  `AWS-RunShellScript` invocation returned `Success`, over the same `ssmmessages` channel
  `start-session` uses, with no interface endpoint anywhere in the account. What remains is the laptop
  half — the `session-manager-plugin` — which is step 3's, and is an install rather than a network
  question.

`wg0` is up on `10.90.0.1/24` with **zero peers** (4.1 has not run), `wg0.conf` is `0600 root`,
`./aws/vpn.py` reads **0 FAILED** with VP-1..VP-6 and VP-9 passing, and `make status` reads **UP,
1 instance, USD 0.0042/h** — the D11 machinery working on its first real `[D]` row.

### Then the confirmation plan wanted to destroy the host

`terraform plan -detailed-exitcode` came back **2**, with `2 to add, 1 to change, 2 to destroy`:

```
~ associate_public_ip_address = true -> false # forces replacement
```

Nothing had changed. The refresh reads that attribute from the instance's *current* public address,
and the `aws_eip_association` is what gave it one — so the two resources **disagree by construction,
for as long as both exist, and the disagreement is `ForceNew`**. Left alone this is a permanent
replacement loop: every apply rebuilds the tunnel endpoint, and `plan` stops being able to say
"nothing drifted" about anything else in the slice.

Fixed in the module with `lifecycle { ignore_changes = [associate_public_ip_address] }`, **keeping**
the `false` — it is load-bearing at launch, which is the only moment it means anything: no second,
auto-assigned public IPv4 to reason about or to pay for. What is ignored is the read-back alone.
**Measured before it was written**: the fix was applied to the cached copy under
`.terraform/modules/`, the plan re-run (`No changes.`, exit 0), and the cache then restored and proven
byte-identical to `wireguard-v0.1.0`.

### A near-miss worth its own line — Lesson 13, from the other side

The first confirmation plan was run as `terraform plan … | tail -5`, and `$?` reported **the exit code
of `tail`**: a clean `0` over a plan that wanted to replace two resources. A check that returns success
on both outcomes is not a check. Re-run without the pipe, it was exit 2 — and the whole finding above
is what the pipe had swallowed.

### And one documented fact was measured false

This stage, the keys runbook and the slice README all predicted `terraform state pull` would show
`user_data` as **40 hex characters**, the provider's SHA-1. It does not: provider 6.60.0 stores **the
rendered script in full, in plaintext** — the SHA-1 is pre-5.0 behaviour, written from memory. **The
claim that mattered survives the correction and is now the whole of it: there is no key in that
script** — the ARN, and the line `PrivateKey = $HOST_KEY`, a shell variable expanded on the host three
minutes after the state was written. Corrected in `docs/plan/runbooks/vpn-keys.md`,
`docs/plan/stages/stage-04-vpn.md` (two places) and `terraform-live/sandbox/vpn/README.md`, each now
stating the **mechanism** — *the key never crosses Terraform* — rather than the storage, because "the
state is a hash" would make any other user data look protected too.

### Not done, and why

- **Step 4.1 has not run**: the roster is `peers = {}`, so the host has no peers and nothing can
  connect yet. Adding the first one **replaces the instance** by design (the peer list rides the user
  data), which is the runbook §2 path exercised for the first time.
- **The module fix is not yet in effect on the deployed host**: it lands with `wireguard-v0.1.1` and
  the caller's `?ref=` bump. Until that apply, a deliberate `terraform apply` in this slice would
  rebuild the endpoint — `make up`/`make down` do not, they only start and stop.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
