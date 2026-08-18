# Log — Stage 4 — VPN access

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-04-vpn.md`](../plan/stages/stage-04-vpn.md).*

*Provenance, named by SUBJECT so it is not guessed later — the same convention
[Stage 3's log](log-stage-03-networking.md) adopted. **Read "exception" below as historical**: every
request recorded here was an exception to the rule in force at the time, which barred Claude from these
files outright. Since **2026-08-17** the rule is cooperative and the same requests are ordinary
([`INDEX.md`](INDEX.md)). What does not change either way is the record of whose hand wrote what — the
point of this note, and why it is kept as written rather than restated.*

*The ten entries below: on **2026-08-16** the user authorised Claude, explicitly, to
create this file and write the first two directly, and on **2026-08-17** to write the third through the
eighth the same way. The first three record no AWS call — one is
a repository change merged with the Stage 3 teardown, one is pass 1 authored and gated but **not
applied**, and the third is a design review propagated through the repository. **The fourth, fifth and
sixth are different in kind: they are the stage's AWS writes**, applied by Claude on the user's
explicit authorisation of those specific steps, and written here by the same authorisation. **Two of
them also record steps Claude did not perform** — step 4.3 and the key generation of 4.1, both run by
the user on the devices — and each says so where it does. **The seventh inverts that split and is
labelled accordingly**: its readings are Claude's, but its one AWS write was **executed by the user**,
because the harness refused the apply after the authorisation had been given — the plan Claude read is
the plan the user applied, from a saved file, which is the only reason the two halves can be recorded
as one act. **The eighth is the standing rule finally arriving**: its readings, its commands and its fix
are the user's own, written by the user; Claude was asked, in the text, to explain step 4, and added
that explanation, the flow-log measurement behind it and the entry's finding. The header of that entry
says so, so no line in it is attributed to the wrong hand. **The ninth is the first written under the
cooperative rule rather than as an exception to the old one**, and it inverts the seventh's split
again: it is Claude's repository work and Claude's readings, with **two acts that are the user's** —
`make down ENV=production` and the second device's configuration and connection — recorded because the
user reported them, and marked as reported rather than as observed. **Its closing section and the tenth
entry invert the split once more**: there every command and every output is the user's, run on the
laptop and pasted, and Claude wrote only the analysis around them — with one correction made to the
user's own text and declared where it was made, because what had been pasted was a draft configuration
that was never applied.*

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

## 2026-08-17 — Steps 4.1 and 4.2: two devices enrolled, and the rebuild that proved decision 4

### The key generation, by the user, on each device

Two pairs, generated where their private halves stay: `mbp` and `raspi`. Only the public halves were
handed over, and **the only check possible on them was structural** — 44 characters, decoding to 32
bytes, the shape of a Curve25519 key. Nothing can tell a WireGuard private key from a public one by
format, which is the whole reason the generation never leaves the device and
`./scripts/check-tfvars-shape.py` checks structure rather than content.

**The command was made silent first, at the user's request** — the same form step 4.3 already used,
propagated to the four tracked files that still taught the printing `wg genkey | tee private.key |
wg pubkey`:

```bash
(umask 077 && wg genkey | tr -d '\n' > laptop-private.key) && wg pubkey < laptop-private.key > laptop-public.key
```

Measured with a throwaway pair before it was written anywhere: nothing on stdout, `600`/44 bytes and
`644`/45 bytes. On a phone the honest answer is *no command at all* — the WireGuard app generates the
pair inside the handset, which is stronger than any command can be, and the stage now says so.

### The roster

```hcl
"mbp"   = { public_key = "…", host = 2 }   # 10.90.0.2
"raspi" = { public_key = "…", host = 3 }   # 10.90.0.3
```

`host` authored, never derived from map order — deleting one entry must not renumber the other. The
names are the ones the user chose rather than the README's `person-device` example: they are what
`wg show` prints and what the handshake log carries, so recognisability beat consistency with a sample.

**Two devices rather than one, deliberately** (keys runbook §6): after step 8.3, a single-device estate
whose one device must be revoked leaves break-glass as the only way back. It is also one instance
replacement instead of two.

### The apply

`2 to add, 1 to change, 2 to destroy` — the instance (the peer list rides its user data) and its
`aws_eip_association`, plus the alarm's dimension updated in place. Re-plan `No changes.`, exit 0
**read from Terraform rather than through a pipe** — the correction the previous entry earned. This
time the replacement took about a minute: **no capacity refusals at all**, against 13 on the first
build. The same AZ, four hours apart — worth remembering before treating either number as the AZ's
character.

New host `i-0ecb30e645c1aebce`, private `10.20.160.238`.

### What the rebuild proved, and it is the point of the whole design

The new host's interface key is **byte for byte the previous host's**, and the address is still
`52.89.212.1` — read from `describe-addresses`, naming the new instance, rather than from Terraform.
So an instance was destroyed and recreated and **both values every client config pins — `Endpoint` and
the server's `PublicKey` — did not move**. That is exactly what decision 4 bought when it put the key
in a `[P]` secret and the address in a `[P]` allocation, and it is the **first time it was exercised
rather than argued**. Step 9.1's promise that a rebuild costs clients nothing now rests on a
measurement.

### The rest of the verification

The boot repeated the first one — packages in 35 s through the gateway endpoint, key in 2 s with zero
retries — and then said `(4) writing /etc/wireguard/wg0.conf for 2 peer(s)`. `wg show wg0` lists both
peers at `10.90.0.2/32` and `10.90.0.3/32`: **`/32` each, so a peer cannot reach another peer**.

**One thing was verified that the plan could only promise**: the handshake log is already in CloudWatch,
and it carries names —

```
2026-08-17T05:26:30Z iface=wg0 peer=mbp   handshake=never
2026-08-17T05:26:30Z iface=wg0 peer=raspi handshake=never
```

`handshake=never` is the correct reading with no client configured yet. This closes the residual
verification (i) left for step 7 — the CloudWatch agent's **shipping** path is a different allow-list
entry from its installation — and it confirms from the other side the drift alarm the keys runbook §4
now documents: a line reading `peer=unknown` is a peer the roster does not know about.

`./aws/vpn.py`: **0 FAILED**, VP-1..VP-6 and VP-9 passing, the instance-scoped checks already naming
the new host.

### Also in this sitting: the keys runbook gained procedure D

At the user's request, `docs/plan/runbooks/vpn-keys.md` §4 — a client rotating **its own** key, which
is also how a public half reaches the server at all, and therefore how a device is added. It names the
two facts that decide the procedure (the host key does not move, so no other device is touched; the
roster rides the user data, so publishing is an instance replacement) and carries the commands
end to end.

It also names **the stopgap, as a stopgap**: `wg set wg0 peer <pub> allowed-ips 10.90.0.N/32` over SSM
admits someone in seconds, changes **only the running kernel state**, and is lost to a reboot or to the
next `make down`/`make up` — with `peer=unknown` in the log while it lasts. Hand-editing `wg0.conf`
became a "Never" beside it: that one survives a reboot and dies at the replacement, which is worse,
because in between it is a running configuration no file describes. "Never" and "Timing" renumbered to
§5/§6, every internal reference re-checked against the headings one by one.

### And `./aws/vpn.py` gained the one thing a describe call cannot answer

Also at the user's request: **`--on-host`**, which reads *inside* the running host through SSM Run
Command — the boot's say-lines, `cloud-init status`, `wg show wg0`, the peer-name map, the sampler
timer and the tail of its log. It exists because section 3's checks can prove the host, the address
and the secret exist and **cannot prove that the running `wg0` matches `peers.auto.tfvars`**; that gap
is what the keys runbook §4 calls `peer=unknown`.

**It is a typed flag rather than a default, and that is the whole design decision.** Every command it
carries is a read, but `ssm:SendCommand` is a **write** API — a `Command` resource, a mutating
CloudTrail event, code executed on an instance — and the reason `aws/*` is read-only is that these
scripts must stay safe to fire at anything without thinking. So a bare `./aws/vpn.py` sends nothing and
prints, in the report, what the flag would do and why. `CLAUDE.md` and `aws/INDEX.md` now name this as
the **second** exception to the read-only rule, fenced the same way `aws/probes/` is. Numbered `2a.` —
an appendix to section 2, in the idiom the stage steps already use — rather than renumbering 3 through 9.

**The read-only path was tried first and is recorded as insufficient**: `ec2:GetConsoleOutput` is a pure
read, but it returned **zero bytes** on both Stage 4 hosts for several minutes, and it could never
answer the peer question at all.

**One rule became a gate instead of a comment.** `wg show wg0` is safe; `wg show all dump` prints the
interface's **private key** on its first line, and this output is written verbatim into
`aws/output/vpn.txt`. A comment saying "never use dump" is an intention, not a control (Lesson 5), so
the command list is checked against `dump`, `>`, `rm `, `wg set` and `systemctl start/stop` **before
anything is sent**. And the guard was proven to fire rather than assumed: injecting `wg show all dump`
produced `REFUSING --on-host: 'dump' appears in 'wg show all dump'`, exit 1 (Lesson 13).

Run both ways on the live host: without the flag, exit 0 and the opt-in text; with it, `ssm status:
Success` and the full reading — both peers at `/32`, the name map matching the roster, the timer
`active`, and consecutive minute samples confirming the sampler loop. Three outcomes are kept
distinguishable on purpose — SSM's own `Success`/`Failed`, `(send failed)` (usually an instance not yet
SSM-managed) and `(still running)` (a host that is up and not answering) — because they have different
causes and would read alike if collapsed.

### The first handshake — the tunnel carried traffic

`mbp`'s client configuration was written in the shape step 5 requires: `Address = 10.90.0.2/32` (the
roster's `host = 2` through `cidrhost`), `DNS = 10.20.0.2` (the VPC resolver, `.2` of `10.20.0.0/16`),
`AllowedIPs = 0.0.0.0/0, ::/0` — **full tunnel, both families**, the `::/0` closing the IPv6 bypass that
would otherwise read as a lockout with the tunnel up — `Endpoint = 52.89.212.1:51820` and
`PersistentKeepalive = 25`. It was assembled by a heredoc reading the private key **from its file**, so
that half never crossed the chat, the screen or the shell history; the file lands `600` from a subshell
`umask`, leaving the interactive shell's umask alone.

**The tunnel came up on the first attempt.** The handshake landed at about **12:15:17Z**, and the log
line that had read `handshake=never` since the boot became:

```
2026-08-17T12:19:20Z iface=wg0 peer=mbp   handshake_age_s=243
2026-08-17T12:19:20Z iface=wg0 peer=raspi handshake=never
```

**What that one line closes is the whole observability chain, link by link, and none of it had been
exercised before**: the kernel's peer table → `wg show all latest-handshakes` (never `dump`, which would
print the interface's private key) → the sampler on its one-minute timer →
`/var/log/wireguard-handshakes.log` → the CloudWatch agent → the log group `/awsds/sandbox/vpn` — **with
the device's name rather than base64**, because `/etc/wireguard/peer-names` is rendered from the same
roster. This is the residual verification (i) left for step 7: the agent's *shipping* path is a
different allow-list entry from its installation, and it works.

**One reading was checked against the design before being accepted.** Across the six samples after the
first, `handshake_age_s` grew 243 → 312 → 373 → 443 → 513 → 583 — exactly wall-clock, never resetting.
With `PersistentKeepalive = 25` the keepalives count as data, so a *live* tunnel renegotiates its session
roughly every two minutes and the age would return to zero on its own; an age that only grows means the
client stopped sending. **The user confirmed the tunnel was brought down after the test**, which is that
reading and not a fault. Recorded because the two cases look identical in this log and have completely
different causes: an ageing counter with the tunnel *up* is a client whose packets stopped arriving —
laptop asleep, network changed, or a NAT expiring the UDP mapping.

### Not done

- **`raspi` has no client configuration** — it is enrolled in the roster and reads `handshake=never`,
  which is the correct reading for a device that has never connected.
- **Step 5's other two proofs are not recorded here**: that the laptop's public address becomes
  `52.89.212.1` with the tunnel up, and that a name only the VPC resolver knows resolves through
  `DNS = 10.20.0.2`. The handshake proves the tunnel; **step 8 rests on the first of those two**, since
  its `aws:SourceIp` can only match traffic that actually exits through the Elastic IP.

## 2026-08-17 — Pass 2 opened: step 6.1 answered, and the reachability target back up without its egress

Pass 2 is the sitting that turns the tunnel from *built* into *proven*. This entry covers everything
that precedes the laptop: the audit, which is a reading and not a build, and the target the
Deliverables' pair needs on the other side of the peering. **The readings themselves are not in this
entry** — see "Not done".

### Step 6.1 — the audit, and it is the whole step

`./aws/networking.py`, **0 checks FAILED**. Two rows are the step:

```
pass  NT-4  no route overlaps 10.90.0.0/24    same read as NT-3 (64 routes, 3 accounts)
```

and §9, which must show **exactly one** world-open ingress rule in the entire measured estate. It does:
`awsds-sandbox-vpn` in the Sandbox VPC, UDP/51820. The other five measured accounts — `data`, `dev`,
`identity`, `prod`, `policy-canary` — return empty. This is the shape `VP-3` enforces and the first
sitting in which the estate has anything at all to show.

**Two readings from the same run are not step 6.1 but are preconditions of the pair, and were checked
before anything was applied rather than discovered by a failed curl:**

- `NT-8` confirms `prod.internal` is associated with the **Sandbox** VPC. Without that association
  `probe.prod.internal` is NXDOMAIN over the tunnel and the whole pair is unrunnable.
- The Sandbox **public** tier's route table — the one carrying the internet gateway, where the
  WireGuard host sits — routes `10.30.0.0/18` and `10.30.64.0/18` across the peering: Production's two
  **private** tiers, and **nothing** for the isolated ones (`10.30.128.0/20`, `10.30.144.0/20`). That
  asymmetry is what makes the forbidden address a control rather than a coincidence, and it is in the
  route table, not in a security group.

### The target: `production/probes` re-applied — deliberately without `production/egress`

The stage names `make up ENV=production` for this. It was **read before it was run**, and the reading
changed the act: `make up` has no per-slice filter, so it applies every `[E]` slice in the account, and
the plan for `production/egress` is **14 resources** — a NAT gateway, its EIP, two default routes and
**ten interface endpoints** (athena, glue, kms, lakeformation, logs, sts, ecr×2, sagemaker×2).

**None of them is in this reading's path.** `production/probes` reads exactly one remote state,
`production/foundation`, which is `[P]`; its user data runs `mkdir`, `echo` and
`nohup python3 -m http.server`, with no `dnf` anywhere and python3 already in the AMI. So the slice was
applied alone: **8 resources**, the instance, the second interface and its attachment, the two A
records and the security group with its two ingress rules.

**What the deviation does not cost is the machinery's safety property**, which is why it was acceptable:
`make status` discovers slices from the tree and reads each one's state, and `make down ENV=production`
destroys every `[E]` slice in the account regardless of how it went up. Nothing is orphaned by applying
one slice directly — the guarantee is "nothing is left running", and it still holds.

**Provenance, because this entry's split is unusual.** Recipe A was followed as written — the plan
generated, saved **outside the repository** and read before anything ran — but the two halves had
different operators. The first four commands are Claude's:

```bash
./scripts/gen-tfvars.py production probes
./scripts/gen-backend-hcl.py production probes
AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/probes init -backend-config=backend.hcl -input=false
AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/probes plan -out=<outside the repository>/prod-probes.tfplan -input=false
```

and **the apply was executed by the user**, after the authorisation had already been given, because the
harness refused the command twice:

```bash
AWS_PROFILE=awsds-infra-prod terraform -chdir=terraform-live/production/probes apply -input=false <outside the repository>/prod-probes.tfplan
```

**Applying the saved file rather than re-planning is what keeps this one act rather than two**: what was
read is what ran, which is the property Recipe A exists for and the only reason a split operator is
recordable at all. The same four commands are what `make up` would have issued for this slice — the
deviation is the slice list, not the procedure.

### What the boot settled, and it was the point of leaving `egress` out

Read the way the slice's own outputs prescribe — no `ssm*` interface endpoint exists in Production, so
Session Manager is not available and the console is the reading path:

```bash
aws ec2 get-console-output --profile awsds-infra-prod --region us-west-2 --instance-id <target> --latest --output text --query Output
```

```
ip-10-30-34-118 login: === AWSDS-PROBE-TARGET-BEGIN ===
addr ens5 10.30.34.118/18
listening:
LISTEN 0      5            0.0.0.0:443       0.0.0.0:*
=== AWSDS-PROBE-TARGET-END ===
...
Cloud-init v. 22.2.2 finished at Mon, 17 Aug 2026 13:08:02 +0000. Up 14.87 seconds
```

**Fourteen point eight seconds, in a private tier with no default route at all** — the NAT gateway this
host booted without is one it never wanted. The listener is bound to `0.0.0.0`, which is the design: one
process answering on **both** addresses, so the pair cannot be explained by "nothing was listening
there".

`SSM Agent unable to acquire credentials` follows, and it is expected twice over: this slice creates **no
IAM principal by design** — the perimeter statements under test carry no principal condition, so an
anonymous request is judged by exactly the statement being measured — and no `ssm*` interface endpoint
exists in Production. `get-console-output` is the reading path, as the slice's own outputs say.

### The negative control was checked for being a control

A forbidden address that is silent because nothing is attached to it proves nothing (Lesson 26). Both
interfaces read `in-use` / `attached`, at device index 0 and 1, **carrying the same security group**:

| Address | Subnet | Route from the Sandbox public tier |
|---|---|---|
| `10.30.34.118` | `prod-private-usw2-az1` (10.30.0.0/18) | yes, across the peering |
| `10.30.133.185` | `prod-isolated-usw2-az1` (10.30.128.0/20) | **none exists** |

Same host, same process, same group. The route is the only variable, and the two A records in
`prod.internal` resolve to exactly these two addresses.

### Not done

- **Every behavioural reading of pass 2.** The tunnel-down half, the three step-5 proofs
  (`checkip` → `52.89.212.1`, the `sandbox.internal` SOA, `probe.prod.internal` resolving), the pair
  itself and its second control — the admitted address on a port the group does not admit, which fails
  in a different place from the forbidden address and is why both are read.
- **`raspi` still has no client configuration.** It is enrolled and reads `handshake=never`. The
  argument for closing this *before* 8.3 rather than after is 4.1's own: a one-device estate whose
  device must be revoked leaves break-glass as the only way back, and a device that has never completed
  a handshake is an enrolment, not a proven second way in (Lesson 5).
- **`production/probes` is up and billing** ~USD 0.0042/h until `make down ENV=production` closes the
  sitting.
- **The `make down`/`make up` lifecycle pair** is deliberately not in this sitting: `make up` has no
  `[D]`-only filter either, so exercising the WireGuard host's stop/start drags `sandbox/egress` up with
  it. That is a separate short sitting with its own purpose, and the `aws/output/vpn.txt` "before" copy
  belongs to it (Validation 2's rule, learned by overwriting one in Stage 3).

## 2026-08-17 — Pass 2's readings: the tunnel routes, and the MTU that made it look like it did not

**The readings and the commands below are the user's**, run from the laptop over phone tethering; the
step-4 explanation, the flow-log measurement and the finding were added by Claude at the user's request,
on the same explicit authorisation as the entries above.

### 1. Tunnel DOWN — the negative half, measured first

Run before the tunnel exists, because a silence measured afterwards cannot be told from a silence that
was always there.

```
curl -sS https://checkip.amazonaws.com ; dig +short probe.prod.internal ; curl -sS --max-time 5 http://probe.prod.internal:443/ ; echo "curl rc=$?"
177.26.70.44
curl: (6) Could not resolve host: probe.prod.internal
```

The provider's own address, and **`prod.internal` does not resolve at all**. That is the right failure,
and which failure it is matters: the name dies at **DNS** rather than at the connection, because the zone
is private and reachable only through the VPC resolver. Nothing on this laptop knew it existed.

### 2. Tunnel up

`mbp` brought up on WireGuard. Handshake completed, traffic in both directions.

### 3. The three step-5 proofs — and the first attempt failed in a way worth the entry

```
curl -sS https://checkip.amazonaws.com ; dig +short SOA sandbox.internal ; dig +short probe.prod.internal
curl: (28) SSL connection timeout
ns-1536.awsdns-00.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
10.30.34.118
```

**Both DNS answers came back and every HTTPS request timed out.** The fix was one line in `mbp.conf`,
under `[Interface]`:

```
MTU = 1280
```

after which the same command read as designed:

```
curl -sS https://checkip.amazonaws.com ; dig +short SOA sandbox.internal ; dig +short probe.prod.internal
52.89.212.1
ns-1536.awsdns-00.co.uk. awsdns-hostmaster.amazon.com. 1 7200 900 1209600 86400
10.30.34.118
```

Three claims, one line each:

| Reading | What it proves |
|---|---|
| `52.89.212.1` | **The full tunnel is real** — every packet leaves through the `[P]` Elastic IP. **This is the one step 8 rests on**: its `aws:SourceIp` matches this address or nothing |
| the `sandbox.internal` SOA | `DNS = 10.20.0.2` is in use — a zone that is NXDOMAIN everywhere else answered |
| `10.30.34.118` | the cross-account association of `prod.internal` resolving over the tunnel, which step 4 then depends on |

### The entry's finding: a full tunnel with no MTU works until the path stops being Ethernet

**Nothing in this design set an MTU** — not the module's generated `wg0.conf`, not the client template in
`docs/plan/runbooks/vpn-client.md`. Absent one, `wg-quick` derives it: the MTU of the interface used to
reach the endpoint, minus 80. Phone tethering presents **1500** to the laptop while the cellular path
carries less, so the tunnel came up at **1420** — too large — and WireGuard sets DF on its outer packets,
so the oversized ones are dropped with no error anywhere.

**The failure is graded by packet size, which is why it reads as "the VPN is broken":**

| Traffic | Size | Result |
|---|---|---|
| the handshake | 148 bytes | **succeeded** — `wg show` showed traffic both ways |
| DNS to `10.20.0.2` | one small UDP exchange | **succeeded twice**, the SOA and the A record |
| TLS | a full-MSS certificate chain | **timed out** |

The block above *is* that split, captured before the fix. **The NAT was never involved**, and that is
recorded because the natural first suspicion — a masquerade rule bound to the wrong uplink — would have
sent the next hour into the host over SSM. The two `dig` answers had already ruled it out: the VPC
resolver answers only if the packet was forwarded **and** source-NATed to an address inside the VPC,
which is the whole of 1.2 working.

`MTU = 1280` is the IPv6 minimum and passes any cellular path. It belongs **on the client**, because it
is the client's path that varies — the same laptop needs no such line on a wired network, and the value
can be raised once a real path is measured. It costs a little throughput on a good link; it removes a
failure mode that presents as total.

### 4. The pair, and the two silences that are not the same silence

**What the step is.** The Deliverables' reachability pair, run from the laptop instead of from the
Sandbox probe host Stage 3 used — three requests against **one** target, changing exactly one variable at
a time. The target's design is what makes that possible: one process bound to `0.0.0.0`, **one security
group on both interfaces**, one address in a tier the source routes to and one in a tier it does not. Two
hosts would have left "nothing answered" indistinguishable from "nothing was listening there".

```
curl -sS --max-time 10 http://probe.prod.internal:443/ ; echo "permitido rc=$?" ; curl -sS --max-time 10 http://probe-isolated.prod.internal:443/ ; echo "proibido rc=$?" ; curl -sS --max-time 10 http://probe.prod.internal:8080/ ; echo "porta-bloqueada rc=$?"
awsds-stage03-probe-target
permitido rc=0
curl: (28) Connection timed out after 10003 milliseconds
proibido rc=28
curl: (28) Connection timed out after 10004 milliseconds
porta-bloqueada rc=28
```

**Why each result is the expected one, and all three are:**

1. **Permitted address, admitted port — expect the body.** `awsds-stage03-probe-target` at `rc=0` is
   seven things at once: the tunnel carries traffic, the WireGuard host forwards and SNATs it, the
   Sandbox public tier's peering route reaches Production's private tier, Production routes the answer
   back, the security group admits the port, the listener is up, and the private zone resolved the name.
   This is the deliverable.
2. **Change ONLY the address — expect silence.** `probe-isolated.prod.internal` is the *same host*, the
   *same process* and the *same security group*; the single difference is that its tier
   (`10.30.128.0/20`) has no route in the Sandbox public tier's table. The packet falls through to
   `0.0.0.0/0 → igw` and dies as an unroutable RFC1918 destination **without ever leaving the Sandbox
   account**.
3. **Change ONLY the port — expect silence.** 8080 against the permitted address *does* cross the
   peering and *does* reach the ENI, and is dropped by the security group, which admits 443 alone.

**The honest part, and why this step was measured rather than asserted.** Both silences arrive at the
laptop as `rc=28`. **The exit code cannot tell them apart, and neither can anything else on the client** —
the claim that they die in different places is not observable from where it was made. It was read from
Production's own VPC flow log instead:

| Window | Source | Destination | Port | Action |
|---|---|---|---|---|
| 15:33:04Z | `10.20.160.238` | `10.30.34.118` | 443 | **ACCEPT** |
| 15:32:13Z, 15:32:15Z | `10.20.160.238` | `10.30.34.118` | 8080 | **REJECT** (7 packets — SYN retransmissions) |
| — | — | `10.30.133.185` | — | **no record at all** |

**The REJECT is what makes the absence mean anything.** An instrument that records nothing proves nothing
unless it demonstrably records *something* in the same window — Stage 3's argument, reproduced here from
the laptop rather than from a probe host.

**And the source column proves something nobody asked it to.** Every record reads `10.20.160.238`, the
WireGuard host's own address; **`10.90.0.2` appears nowhere in Production.** That is 1.2's NAT seen from
the far side — VPC peering forwards only packets whose source and destination both sit inside the two
VPCs' ranges — and it is why step 6.1's `NT-4`, no route anywhere for `10.90.0.0/24`, is a property of
the design rather than a gap in it. An earlier ICMP row in the same log (14:54:07Z, 5 packets, REJECT)
says the same thing from a third angle: the group admits one TCP port and nothing else.

### What this closes

- **Step 5 is complete.** All three of its proofs are recorded above, `52.89.212.1` included — so **pass 3
  is unblocked**, which is the only gate step 8 had.
- **The Deliverables' tunnel pair is complete**: NXDOMAIN with the tunnel down (step 1), HTTP 200 with it
  up (step 4), and the negative control travelling with the pair rather than assumed.

### Not done

- **`raspi` still has no client configuration**, and the argument for closing it before 8.3 is unchanged
  (4.1): an enrolled device that has never handshaked is an enrolment, not a proven second way in.
- **The MTU finding reached the runbook in this sitting, and the module deliberately not.**
  `vpn-client.md` gained the line in §1's template — **in the template rather than in a troubleshooting
  note**, because "add this if it misbehaves" is an intention (Lesson 5) — a sixth row in §0 marking it
  as the one value derived from *the path* instead of from the design, and a §4 entry leading with the
  symptom that misleads ("handshake fine, DNS fine, nothing loads"), the reason the two `dig`s exonerate
  the host, and the `ping -D` pair that turns "it was MTU" into a measurement. **Whether the server
  should pin its own `wg0` MTU is a separate question and is left open**: the server's value governs the
  size of what it injects into the tunnel, so it trades against every client's path rather than one, and
  nothing measured here decides it.
- **`production/probes` is still up**, billing ~USD 0.0042/h until `make down ENV=production`.
- **`./aws/vpn.py` has not been re-run** since the readings, and the `aws/output/vpn.txt` "before" copy
  belongs to the deferred lifecycle sitting (Validation 2's rule).

---

## 2026-08-17 — Pass 3 applied: the second device, and the control plane pinned to the tunnel

*Written by Claude at the user's request, in the same sitting, and **amended later in that sitting when
step 8.3 was authorised and applied** — the entry was written while the apply was still pending, and
leaving it saying so would have made it false. **Two acts in it are the user's and are not Claude's to
claim**: `make down ENV=production`, and the `raspi` client configuration and its connection — both
performed on the user's own machines and reported by the user in chat, recorded as **reported rather
than observed**. Everything else is Claude's: the repository work of steps 8.1, 8.2 and 9.1, the
readings, and the one AWS write — `identity/sso`, applied by Claude on the user's explicit
authorisation of that specific act.*

### What the user closed, and what it settles

**`make down ENV=production`.** The reachability target is gone; the pair it existed for is recorded in
the previous entry, negative control included.

**The `raspi` connected, and it is the item the plan named as a precondition rather than as tidiness.**
Step 4.1's argument was never about redundancy for its own sake: after 8.3, a single-device estate whose
one device must be revoked leaves **break-glass as the only way back**, because you are off-VPN by
definition and the console-from-the-EIP path needs the device you no longer have. A second device that
has actually handshaked turns that corner from real into theoretical. The enrolment existed since 4.1 —
the public half has been in the roster all day — and what changed today is that it is now a **proven**
second way in rather than a row in a file.

It also carried the previous entry's finding into its first use: the `raspi`'s config was written from
the runbook template, which has held `MTU = 1280` since that sitting. The value went in **before** the
first connection rather than after a failure, which is what putting it in the template instead of in a
troubleshooting note was for (Lesson 5).

### Steps 8.1, 8.2 and 8.3 — written, planned, read, then applied

The statement, as it renders — extracted from the saved plan rather than from the source, because what
is reviewed has to be what the API receives:

```json
{
  "Sid": "DenyControlPlaneOffVpn",
  "Effect": "Deny",
  "Action": "*",
  "Resource": "*",
  "Condition": {
    "NotIpAddress": { "aws:SourceIp": "52.89.212.1/32" },
    "BoolIfExists": { "aws:ViaAWSService": "false" }
  }
}
```

**`52.89.212.1` is not written anywhere in the repository.** It arrives through the stage's own rule —
a `terraform_remote_state` read of `sandbox/foundation/`'s outputs — and this is the repository's
**first remote-state read that crosses an account boundary**: the apply runs as `awsds-infra-identity`
and the state bucket is in Sandbox. That is the one thing a same-account read does not need and this
one does: a `profile` in the data source's config. Since pass 2's rule is that a profile literal never
sits in a `.tf` file, it arrives from the generated tfvars, through a new `VPN_HOMES` table in
`scripts/tfhygiene/backend.py` and a `vpn_homes` variable — a **map from day one**, because D35 makes
the VPN home a role an account plays and INT-05 already says the EIP is a list. What makes the whole
arrangement workable rather than a second sign-in is that both profiles sit on the `awsds`
`sso-session`, so one login covers the pair.

**The plan: `0 to add, 6 to change, 0 to destroy`** — the six persona inline policies, and nothing else
in the slice. Confirmed by address rather than by count, and confirmed in the negative too: a grep for
the Sid across the whole planned state returns those six and no seventh.

**Applied 2026-08-17** — profile `awsds-infra-identity`, the saved plan file rather than a re-plan, so
what was read is what was applied. `Apply complete! Resources: 0 added, 6 changed, 0 destroyed`, the
slowest set taking 13 s. The slice's own precondition had already compared the caller against the
account this configuration names, so "am I in Identity" was answered by the plan rather than by a
person reading an id.

**Read back from AWS rather than from Terraform**, which is this stage's standing idiom: `./aws/vpn.py`
§5 greps each set's inline policy through the API, and `VP-7` **flipped from `note` to `pass` — all six
carry it**. The seventh row still reads `(no inline policy)`, and the check now says so as its own
note — the expected state until the pair is recorded, rather than an absence nobody is tracking.

**The confirmation re-plan is `No changes` at `-detailed-exitcode 0`** — and the exit code was read
**directly rather than through a pipe**, which is not pedantry here: the fifth entry recorded a
confirmation plan run as `… | tail`, where `$?` was `tail`'s and reported a clean 0 over a plan holding
two destroys.

**What is now true of the estate, stated plainly because it is a change in kind rather than in degree:**
every one of the six persona permission sets denies every AWS API call and every console action that
does not arrive from `52.89.212.1`. That is live in every account each set is provisioned into, for
every member of the four persona groups, from this apply onwards. `InfrastructureAccess` is outside it
by design and is the recovery path.

### The entry's finding: 8.3's "separate, deliberate diff" is a **create**, not an update

The stage file says `InfrastructureAccess` gains the statement in a later diff of its own. Reading the
plan for the negative control turned up why that sentence needs a correction: **`InfrastructureAccess`
has no inline policy at all.** It carries `AWSAdministratorAccess` as a
`aws_ssoadmin_managed_policy_attachment` and nothing else — `./aws/vpn.py` §5 has been printing
`(no inline policy)` for it since the script was written, which is the reading that was there to be had
and was not read as an answer to this question.

So the later diff is not "add a statement to a document"; it is **create the seventh set's first inline
policy, containing exactly one deny**. Same effect, different failure modes, and one of them is worth
naming now: an inline policy that does not exist cannot be *partially* applied, so the act is atomic in
a way an edit would not be — but it is also the first time that set's authorization stops being a
single managed-policy attachment, and every future reader of it has one more place to look.

### Two guards the plan did not ask for, and the reason both are here

`DenyControlPlaneOffVpn` denies `*` on `*` unless `aws:SourceIp` matches a list. **IAM does not validate
that list.** A value that is not a CIDR simply matches nothing — which means the statement's failure
mode, if the address ever reads back wrong, is not an error at plan time and not an error at apply time:
it is a clean apply, a green report, and six personas who cannot make a single AWS call from any network
on earth. Discovered by a person who cannot sign in.

Both guards exist to turn that into a plan-time failure that names the cause:

| Guard | Where | The shape it refuses |
|---|---|---|
| `length(var.vpn_homes) > 0` | `variables.tf` validation | no homes at all → `NotIpAddress` over an empty list → matches every call |
| every address is a `/32` that parses | `permission-sets.tf` precondition | a home whose `foundation/` output came back null or renamed → renders as `/32` |

The second is the one that matters, because it is the shape a *future* change produces: the map has rows
and the state behind one of them did not answer. This is Lesson 13 applied to a control instead of to a
check — a verification that passes identically whether the address is right or absent is not a
verification.

### Verification (vii) is answered, and with room

The 10,240 non-whitespace-byte permission-set quota, which **fails at provisioning rather than in
`plan`** — the reason the slice has carried a size precondition since Stage 2. Measured from the plan's
own output diff:

| Set | Before | After | Δ |
|---|---|---|---|
| `DataScientistStagingAccess` | 3547 | 3851 | +304 |
| `DevEnvStewardAccess` | 3657 | 3961 | +304 |
| `DataScientistProdAccess` | 4065 | 4369 | +304 |
| `GovernanceManagerAccess` | 4233 | 4537 | +304 |
| `DataScientistAccess` | 4349 | 4653 | +304 |
| `DeploymentManagerAccess` | 4563 | **4867** | +304 |

The worst case is 4867 against 10240 — under half. And the conservative half of that comparison is
already built in: the figure is the **rendered** document, which the first apply measured as about a
quarter larger than what Identity Center stores.

### The two readings, and one of them is a shape rather than a check

**`./aws/vpn.py` — 0 FAILED.** `VP-1` through `VP-6` and `VP-9` pass: one `t4g.nano` running,
`52.89.212.1` associated with it, IMDSv2 required, the log group at 30 days, the health alarm `OK`, the
host-key secret carrying its value-read deny with rotation off. `VP-7` and `VP-8` report `note` — the
deny absent from all six sets, no GuardDuty detector anywhere — which is what they are supposed to say
before steps 8 and 10. **The run was copied aside to `aws/output/vpn-before-cycle.txt`** as Validation 2
requires, because the report regenerates in place and Stage 3's validation already overwrote its own
"before" once.

Two calls FAILED, and neither is a finding: `awsds-ctadmin-orgfull-dev` and
`awsds-ctadmin-orgfull-identity` have no SSO token. Those profiles sit on the **`awsds-ctadmin`
session**, which is a different sign-in and is only needed for pass 4.

**`./aws/networking.py` — 0 FAILED**, re-run after the Production teardown. `NT-4` still finds no route
anywhere touching `10.90.0.0/24` (64 routes across three accounts), and §9 still shows **exactly one**
world-open ingress rule in the whole measured estate:

```
sg-0bbb8436fe786b996  awsds-sandbox-vpn  vpc-00dca74a35159b11c   UDP/51820
```

Both are Validation 1, and re-running them here is not ceremony: the previous entry's readings were
taken with `production/probes` up, and a teardown is exactly the kind of change that could have left a
route or a group behind.

### Step 9.1 — delivered as a pointer, and the departure is deliberate

9.1 asks for the client instructions in `README.md`: key generation, the config template, how to verify,
what a rebuild changes. **All of that already exists in full**, in
[`vpn-client.md`](../plan/runbooks/vpn-client.md), which gained its last piece in the previous sitting.
Copying it into `README.md` would be Lesson 14 with two copies of a procedure — and the copy that goes
stale is always the one further from the person following it.

What 9.1 is actually *for* is that the next person looks in `README.md` and finds nothing. So the README
gained a section that carries the two things that are genuinely its own — the **three roles** the tunnel
plays and which of them is unverified (INT-16), and **why an instance rebuild changes no client config**,
which is a claim about the `[P]`/`[D]` split rather than a step — and points at the runbook for the
procedure. The requirement is met; the duplication is not created.

### Gates

`make check: OK`. `pre-commit` on the six changed files: every hook passed, `checkov` and `tflint`
included. `terraform fmt`, `validate` and `plan` clean in `identity/sso`.

### Not done

- **THE CONTROL-PLANE PAIR IS OWED, AND IT IS OWED NOW RATHER THAN EVENTUALLY.** The deny is live; what
  is not yet measured is that it denies the right thing and permits the right thing — the same API call
  refused with the tunnel down and **succeeding with it up**, run **per persona set** rather than once,
  reading the **denial wording** and not the exit code (Validation 3, a standing rule since 1c). Until
  that reading exists, `VP-7`'s `pass` is presence and not sufficiency, which is what the script's own
  §5 header says of itself. Verifications (iv) — the non-FAS on-behalf flows — and (vi) — whether an
  IdC sign-in completes at all with the tunnel down — are answered from the same sitting.
  **→ Three sets of five were measured later the same day; the next entry is that reading.**
- **A practical precondition the plan does not state, found while preparing this**: the pair needs a
  **persona** session, and the four persona users exist in the directory but **none has a CLI profile**
  configured. So the pair runs from the console, or from profiles created for those users first — a
  decision to take before the sitting, not during it. **→ Closed in the section below**, and getting the
  session layout right turned out to be the next entry's first finding.
- **The seventh set's diff is not written.** Deliberately: it is a create rather than an edit, as above,
  and it lands only after the pair is recorded.
- **The lifecycle cycle is still owed** (Validation 2, and the Deliverables' "the lifecycle holds"). The
  "before" copy is now taken, so what remains is the cycle itself — and it has a trap the plan does not
  state: `make down` descends rank and stops `vpn` **last**, so with a full tunnel up, the moment the
  host stops, every remaining AWS call *of that same command* routes into a dead tunnel. Run it with the
  tunnel down. `make up ENV=sandbox` has no `[D]`-only filter and drags `sandbox/egress` along —
  measured at 0.17 USD/h, so a 15-minute cycle is about USD 0.04, which is a fact rather than an
  obstacle.
- **Step 3's laptop half** — the `session-manager-plugin` install, verification (iii)'s residual. It is
  a local install, not a network question.
- **Pass 4 (GuardDuty) is untouched** and independent of all of the above.
- **Whether the server should pin its own `wg0` MTU stays open**, and the `raspi` did not settle it: it
  used the template's 1280 like the laptop, which says nothing about what the *server* injects. What
  would settle it is reading `wg0` and the primary interface **on the host** — `./aws/vpn.py --on-host`,
  which carries `ssm:SendCommand` and is therefore a write API, off by default and run only on explicit
  authorisation.

### Also in this sitting, by the user: the CLI identities the pair cannot run without

Written by the user; **the configuration block below was corrected by Claude against the file as it
actually exists** — what the user pasted was Claude's earlier *draft*, whose session names
(`awsds-ds`, `awsds-dm`, …) were never applied. What is here was read from `~/.aws/config`, with the
start URL and the account ids elided, because this repository keeps neither in a tracked file. Recording
a configuration that does not exist would be worse than recording none: the point of a log is that it
can be trusted against the machine.

- Configured `~/.aws/config` with the other SSO users. Password and MFA configuration was done
  previously for each SSO user.

**One `sso-session` per PERSON, four of them — and that is the rule rather than the count.** The token
cache is keyed by session *name*, so profiles sharing a session share an identity however many people
they were written for; `awsds-scientist` is deliberately shared by two profiles because
`DataScientistAccess` and `DataScientistProdAccess` are held by the same human. The full reasoning, and
what it costs to get wrong, is the next entry's opening finding.

```
[sso-session awsds-scientist]
sso_start_url  = <the same start URL as [sso-session awsds]>
sso_region     = us-west-2
sso_registration_scopes = sso:account:access

[sso-session awsds-deploy]
sso_start_url  = <idem>
sso_region     = us-west-2
sso_registration_scopes = sso:account:access

[sso-session awsds-governance]
sso_start_url  = <idem>
sso_region     = us-west-2
sso_registration_scopes = sso:account:access

[sso-session awsds-devenv]
sso_start_url  = <idem>
sso_region     = us-west-2
sso_registration_scopes = sso:account:access

# Data Scientist User - one login, two permission sets
[profile awsds-scientist-sandbox]
sso_session    = awsds-scientist
sso_account_id = <Sandbox Account 1>
sso_role_name  = DataScientistAccess
region         = us-west-2

[profile awsds-scientist-prod]
sso_session    = awsds-scientist
sso_account_id = <Production Account>
sso_role_name  = DataScientistProdAccess
region         = us-west-2

# Deployment Manager User
[profile awsds-deploy-sandbox]
sso_session    = awsds-deploy
sso_account_id = <Sandbox Account 1>
sso_role_name  = DeploymentManagerAccess
region         = us-west-2

# Governance Manager User
[profile awsds-governance-data]
sso_session    = awsds-governance
sso_account_id = <Data Governance Account>
sso_role_name  = GovernanceManagerAccess
region         = us-west-2

# Dev Env Steward User
[profile awsds-devenv-prod]
sso_session    = awsds-devenv
sso_account_id = <Production Account>
sso_role_name  = DevEnvStewardAccess
region         = us-west-2
```

**The naming generalises what was already there rather than competing with it**, and it is now written
down in [`aws/AWS-CLI.md`](../../aws/AWS-CLI.md) so a seventh row does not have to invent one: the
session names the **person**, the profile is `awsds-<person>-<account>`, and the segment between names
the **role** wherever one person holds several (`-infra-`, `-ctadmin-orgfull-`). The persona rows drop
that segment because person and role coincide — with one exception worth knowing rather than fixing:
`awsds-scientist-sandbox` and `awsds-scientist-prod` carry **different** permission sets, told apart by
the account and not by the name.

## 2026-08-17 — The control-plane pair, all five exercisable sets: the deny measured, and two findings that are not about the VPN

*Provenance. **Every command and every output below was run and pasted by the user**, from the laptop,
and is reproduced verbatim except for two mechanical substitutions, named here and made nowhere else:
**account ids → the account's name**, and **the persona's e-mail inside an ARN → that user's role name**
— this repository keeps neither in a tracked file, and an ARN carries both. Nothing else is edited: the
`AWSReservedSSO_*` suffixes, the resource ARNs and the error wording arrived as they read.
**Claude wrote the analysis around them and nothing else.** One thing in the setup is also the user's
and is not Claude's to claim: the `sso-session` layout is a **correction the user made to a
configuration Claude had drafted wrong** — the entry's first finding.*

### The finding that arrived before any reading did, and it is the user's

The pair needs a **persona** session, and the four persona users held no CLI profile. Claude drafted one
`sso-session` shared by all five persona profiles; **the user rejected it in review, asking whether that
did not mean one persona's token would be handed to another.** It does not hand a credential over — the
portal refuses, because the token's user holds no such assignment — but it refuses **from the portal, at
credential-vending time**, which is a *third* refusal in a reading whose entire purpose is telling two
apart. The CLI caches an SSO token under the **session name**, so profiles sharing a session share an
identity however many people they were written for: switching `AWS_PROFILE` changes what is *requested*
and not *who asks*.

`aws/AWS-CLI.md` already carried the rule — "two sessions, **because they are two different people**" —
and the draft had broken it. Recorded as an addendum to **Lesson 25**, whose first half already names
ambient identity invisible in the place that looks authoritative: there the shell prompt, here the
profile name, and `get-caller-identity` the only instrument in both. The lesson was not opened as a
27th, deliberately: the rule already existed in this repository, and what was new is the second entrance
to it — not duration, but a cache keyed coarser than the switch being operated.

**A second thing the setup taught, and it is why the readings below are sequential:** four
`aws sso login` calls in a row all authorise the **same** person, because the browser stays signed into
the access portal. No CLI flag fixes it — signing out of the portal between personas is part of the
procedure, and each ARN below is the evidence that it worked.

### Reading 1 — Data Scientist User, two permission sets

**Tunnel UP.** The identity first, since it is what says which set answered:

```
$ aws sso login --sso-session awsds-scientist

arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user>

$ AWS_PROFILE=awsds-scientist-sandbox aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

/aws/lambda/aws-controltower-NotificationForwarder      /awsds/sandbox/vpn      awsds-sandbox-vpc-flow-logs

$ AWS_PROFILE=awsds-scientist-prod aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

/aws/lambda/aws-controltower-NotificationForwarder      awsds-prod-vpc-flow-logs
```

**Tunnel DOWN, the same two commands:**

```
$ AWS_PROFILE=awsds-scientist-sandbox aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the DescribeLogGroups operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DataScientistAccess_37932702010107f8/<data scientist user> is not authorized to perform: logs:DescribeLogGroups on resource: arn:aws:logs:us-west-2:<Sandbox Account 1>:log-group::log-stream: with an explicit deny in an identity-based policy

$ AWS_PROFILE=awsds-scientist-prod aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the DescribeLogGroups operation: User: arn:aws:sts::<Production Account>:assumed-role/AWSReservedSSO_DataScientistProdAccess_0a59097411421dd8/<data scientist user> is not authorized to perform: logs:DescribeLogGroups on resource: arn:aws:logs:us-west-2:<Production Account>:log-group::log-stream: with an explicit deny in an identity-based policy
```

### Reading 2 — Deployment Manager User

**Tunnel UP:**

```
$ AWS_PROFILE=awsds-deploy-sandbox aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

/aws/lambda/aws-controltower-NotificationForwarder      /awsds/sandbox/vpn      awsds-sandbox-vpc-flow-logs
```

**Tunnel DOWN:**

```
$ AWS_PROFILE=awsds-deploy-sandbox aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the DescribeLogGroups operation: User: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_DeploymentManagerAccess_848d85a905e0d299/<deployment manager user> is not authorized to perform: logs:DescribeLogGroups on resource: arn:aws:logs:us-west-2:<Sandbox Account 1>:log-group::log-stream: with an explicit deny in an identity-based policy
```

### Reading 3 — Governance Manager User, and the probe had to change

This set holds **no `logs:` action at all**, so the uniform probe does not reach it. The first attempt,
`glue get-databases`, returned **nothing** — a success, since Data Governance has no Glue database yet
(that is Stage 5) — and an empty result is exactly what Validation 3 refuses as the positive half: it is
indistinguishable from a wrong query expression, a wrong profile or a cut pipe (Lesson 13, in the
instrument this time rather than in the check). `lakeformation:GetDataLakeSettings` is in the set's
`AdministerLakeFormation` and returns structure whether or not a lake exists, so it replaced it.

**Tunnel UP:**

```
$ AWS_PROFILE=awsds-governance-data aws lakeformation get-data-lake-settings --query 'DataLakeSettings.Parameters' --output json

{
    "CROSS_ACCOUNT_VERSION": "4",
    "SET_CONTEXT": "TRUE"
}
```

**Tunnel DOWN:**

```
$ AWS_PROFILE=awsds-governance-data aws lakeformation get-data-lake-settings --query 'DataLakeSettings.Parameters' --output json

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the GetDataLakeSettings operation: User: arn:aws:sts::<Data Governance Account>:assumed-role/AWSReservedSSO_GovernanceManagerAccess_ac956c0c7348f956/<governance manager user> is not authorized to perform: lakeformation:GetDataLakeSettings on resource: arn:aws:lakeformation:us-west-2:<Data Governance Account>:catalog:<Data Governance Account> with an explicit deny in an identity-based policy
```

**This is the reading that proves the `Action: "*"` rather than quoting it.** The three before it all used
`logs:DescribeLogGroups`; a deny that was somehow service-specific would have looked identical. Here a
second service refuses under the same Sid, in a third account.

### Reading 4 — Dev Env Steward User

**Tunnel UP:**

```
$ AWS_PROFILE=awsds-devenv-prod aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

/aws/lambda/aws-controltower-NotificationForwarder      awsds-prod-vpc-flow-logs
```

**Tunnel DOWN:**

```
$ AWS_PROFILE=awsds-devenv-prod aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

aws: [ERROR]: An error occurred (AccessDeniedException) when calling the DescribeLogGroups operation: User: arn:aws:sts::<Production Account>:assumed-role/AWSReservedSSO_DevEnvStewardAccess_6f35a9e0c160dfc2/<dev env steward user> is not authorized to perform: logs:DescribeLogGroups on resource: arn:aws:logs:us-west-2:<Production Account>:log-group::log-stream: with an explicit deny in an identity-based policy
```

### Reading 5 — the negative control, and it is what makes the other four mean anything

Same account as reading 2, same action, same laptop, **tunnel still down**. The only variable changed is
the permission set — and it is the one deliberately left outside the fragment. The `aws sso login` is
part of the reading rather than setup: it, too, ran off-VPN.

```
$ aws sso login --sso-session awsds

$ AWS_PROFILE=awsds-infra-sandbox-1 aws logs describe-log-groups --query 'logGroups[].logGroupName' --output text

/aws/lambda/aws-controltower-NotificationForwarder      /awsds/sandbox/vpn      awsds-sandbox-vpc-flow-logs
```

### The probe was chosen so that a refusal would mean something

`logs:DescribeLogGroups` is **granted** to all three sets, so what was measured is an explicit deny
overriding an explicit allow. Had the action not been granted, both halves would have failed and the
reading would have proven nothing — the exact failure Validation 3 exists to catch, and the reason the
*wording* is read rather than the exit code:

| The message ends in | Who refused |
|---|---|
| `with an explicit deny in an identity-based policy` | **`DenyControlPlaneOffVpn`** — what all three returned |
| `because no identity-based policy allows the … action` | nobody: the persona never held the action |
| `with an explicit deny in a service control policy` | an SCP — a different control (Lesson 20) |
| `with an explicit deny in a resource control policy` | the RCP |

`aws sts get-caller-identity` is **not** usable as the probe and was used only to name the answering
role: AWS documents that the call succeeds even when a policy explicitly denies it, because the same
information is returned either way — it would have read identically in both halves (Lesson 13).

### Verification (vi) — the sign-in itself, off-VPN

```
$ aws sso logout
$ aws sso login --sso-session awsds-scientist

Successfully logged into Start URL: <the organization's access portal>
```

**Answered: yes.** The deny governs the *role*; entering Identity Center is an OIDC flow against the
authorization endpoint, not an IAM call the permission set's inline policy evaluates. Expected, and now
read rather than reasoned. **What matters is the chain, and all three links were measured today:**

| Off-VPN | Result |
|---|---|
| sign in to the portal | **works** — this reading |
| `sso:GetRoleCredentials` | **works** — every tunnel-down half printed the ARN |
| use the credential | **denied** — readings 1-4 |

So signing in from anywhere is not an entitlement. What the portal yields off-VPN is
**reconnaissance** — which accounts exist, which roles are held — and nothing actionable. Recorded that
way deliberately, because "you can still log in from any network" reads as a hole until it is paired
with what the login buys.

It is **context for INT-16 and not INT-16**: that row asks whether a permission-set condition gates the
**Unified Studio portal**, which does not exist until Stage 6. What today's reading says about it is
that the general mechanism is not gated — the direction 8.4 already predicted for the third role.

### Verification (iv) — the console with the tunnel up, and three errors that are not the deny

Exercised as the Data Scientist User, tunnel up, over the surfaces this set is actually granted:
CloudWatch **log groups**, **Logs Insights** (a query was run and returned), the **Glue** catalog, and
**Athena** workgroups — the last listing `primary` with no error at all.

**Nothing broke because of `DenyControlPlaneOffVpn`.** Three things broke for three other reasons, and
the entry's point is that all three were attributed **from the wording alone**, without opening a policy:

**(a) The console opened in `us-east-2`:**

```
User: … is not authorized to perform: logs:DescribeLogGroups on resource: arn:aws:logs:us-east-2:… with an explicit deny in a service control policy: arn:aws:organizations::<Management Account>:policy/<org>/service_control_policy/p-umksvu5a
```

The Region ceiling, and **`p-umksvu5a` is a policy this project has already measured**: it is
`Interactive`'s Region document, and [D37](../plan/decisions/D37-nested-ou-inheritance.md) records that a
deny firing inside Sandbox Account 1 names *it* rather than the nested `Sandboxes` OU's own — inheritance
winning, and AWS naming one of two policies (Lesson 20). That finding came from a `CreateKeyPair` probe on
2026-08-13; this is the same measurement arriving through a completely different path five days later.
The operational residue is one line for the client instructions: **the console has to be on `us-west-2`**,
and someone who does not read the wording will file this as a VPN fault.

**(b) `cloudwatch:GetMetricData` — `because no identity-based policy allows`.** Not a deny: the grant
was never there. **Measured across the slice: not one of the six sets holds any `cloudwatch:` action.**
They all hold `logs:` — CloudWatch *Logs* — and nothing in the *metrics* namespace, which the console
presents as one screen and IAM treats as two services. **Deliberately not fixed here**: today it is a
metrics panel failing on a page whose logs render, and no persona has a workload emitting a metric.
Granting against a console symptom rather than against a requirement is the wrong order; Stage 6 revisits
these sets with a real training job in front of them, and that is where "the scientist reads their own
job's metrics" gets written and scoped.

**(c) `logs:GetLogGroupFields` in Logs Insights — the one that is a real defect**, and it is recorded
under its own heading below because it is not a VPN finding at all.

### The finding this verification turned up, and it is a defect in a grant rather than in a control

```
Error: Failed to load discovered fields: Outdated permission. User with accountId: <Sandbox Account 1> is not authorized to perform GetLogGroupFields on resources /aws/lambda/aws-controltower-NotificationForwarder.
```

**Four sets are granted Logs Insights and none of them can use all of it.** `logs:StartQuery` appears in
`DataScientistAccess`, `DataScientistStagingAccess`, `DataScientistProdAccess` and
`DeploymentManagerAccess`; `logs:GetLogGroupFields` appears in **none**. The sharpest form of it is that
the deployment manager's Sid is literally named **`ReadCloudWatchLogsIncludingInsights`** — the name
states the intent and the action list falls short of it. This is Lesson 14 at the smallest scale: an
enumeration written by hand, missing a member.

**Checked against the documentation rather than against the error**, which is the whole method here: AWS
lists the console's required permissions, and comparing that list to the four statements shows **three**
read actions absent, not one — `logs:GetLogGroupFields` (field discovery, the observed failure),
`logs:GetLogRecord` (expanding one event in a result set) and `logs:DescribeQueryDefinitions` (listing
saved queries). Patching only the action that happened to error would have left two behind and brought
everyone back to this same screen. The write counterparts — `PutQueryDefinition`, `DeleteQueryDefinition`
— stay out: this set reads Insights, it does not curate it.

**And the error's FORM is a finding of its own, retroactive and worth more than the fix.** Read it again:
`Outdated permission. User with accountId: … is not authorized to perform GetLogGroupFields` — that is
**not** the canonical IAM message. It carries neither `with an explicit deny in an identity-based policy`
nor `because no identity-based policy allows`. Logs Insights writes its own text. **Had
`GetLogGroupFields` been chosen as the pair's probe, both halves would have been indistinguishable and
the whole reading unreadable.** So a verification that turns on wording must select an action *for
producing the canonical wording*, not merely for being granted — a criterion nobody had written down, and
one that `logs:DescribeLogGroups` satisfied by luck as much as by judgement.

### What the five readings establish, and it is more than the deliverable asked for

**1 · Five independent readings, not one repeated.** Five permission sets across three accounts and two
services, each with its own `AWSReservedSSO_*` suffix — a set becomes an IAM role *per account*, and five
different roles answered. **The account-wide explanation is excluded twice, in two different accounts**:
in Sandbox, `DataScientistAccess` and `DeploymentManagerAccess` are denied while `InfrastructureAccess`
succeeds, same action, same network state; in Production, `DataScientistProdAccess` and
`DevEnvStewardAccess` are both denied. No SCP, RCP or routing artefact separates two permission sets
inside one account.

**2 · The negative control fired, in the same conditions rather than in a different window** (Lesson 26).
An instrument that records nothing proves nothing unless it demonstrably records something alongside it;
here the something is a *permitted* answer, from a principal outside the control, off-VPN, in the
account where the denial had just been measured.

**3 · A credential minted inside the tunnel does not survive leaving it — measured, not assumed.**
Notice that the tunnel-down halves **printed the ARN**: the SSO token stayed valid off-VPN and
`sso:GetRoleCredentials` succeeded, so the CLI held a role credential throughout. The refusal came from
CloudWatch Logs evaluating IAM, because `aws:SourceIp` is evaluated **at the service call and not at
vending time**. That answers a question nobody had put in writing — *can a session be minted on the VPN
and used off it?* — and answers it **no**. It is the mirror of Lesson 24's second trap, where a
four-hour cached credential let probes pass against a policy that had already changed: the same cache
exists here and hides nothing, for a structural reason rather than a lucky one.

**4 · `InfrastructureAccess` outside the deny stopped being an intention.** The stage's Risks section
says step 8 turns "the VPN host is down" into "no persona can call any AWS API", and names the seventh
set staying outside the fragment as what keeps that recoverable without break-glass (D16). Reading 3 is
that claim exercised: the `aws sso login` **completed off-VPN** and the call **succeeded off-VPN**, so
the recovery path is rehearsed before it is needed — Lesson 5, from the side where an intention became a
control. It is also the behavioural half of a negative that had only been checked statically, by
grepping the planned state for a seventh carrier of the Sid.

**5 · The pair is complete for every set that can carry it, and `VP-7`'s `pass` has stopped being
presence alone.** Five of the six are exercised; what remains is not a scheduling gap.

### An unrelated reading that fell out of reading 3, recorded because it was in front of us

The full `get-data-lake-settings` output — taken only to check the response shape — shows Data Governance
with `DataLakeAdmins: []` and both `CreateDatabaseDefaultPermissions` and
`CreateTableDefaultPermissions` granting `ALL` to `IAM_ALLOWED_PRINCIPALS`. Neither
[`AWS_STATE.md`](../AWS_STATE.md) nor INT-11 nor Stage 5 mentioned either. It touches nothing in this
stage and everything in the next, so it is written up where it belongs — INT-11 and `AWS_STATE.md`, in
this same sitting — rather than argued here.

### The fix, applied twice, because the first one was right and still wrong

**First apply (2026-08-17): three actions added to four statements.** `0 to add, 4 to change`,
`logs:GetLogGroupFields` + `logs:GetLogRecord` + `logs:DescribeQueryDefinitions`, identical in each,
nothing removed, `DenyControlPlaneOffVpn` verified intact in all four before and after. The console's
field-discovery error went away.

**And the next call failed:**

```
Error: User: … is not authorized to perform: logs:DescribeFieldIndexes on resource: arn:aws:logs:us-west-2:<Sandbox Account 1>:log-group:/aws/lambda/aws-controltower-NotificationForwarder because no identity-based policy allows the logs:DescribeFieldIndexes action
```

**`logs:DescribeFieldIndexes` is not in the AWS page the fix was derived from.** It is a newer API
(field indexes) that the console already calls and the documented console-permission list does not
mention. **So the method was sound and the source was stale**, and the conclusion is bigger than the
missing action: *enumerating the calls of a console surface is a race that cannot be won.* A console
acquires calls faster than any list documents them, and every miss is a user-visible error and a round
trip. Two enumerations failed in one sitting — the second one derived from the vendor's own
documentation.

**Second apply, by the user's decision: the AWS managed policy `CloudWatchLogsReadOnlyAccess`.**
`4 to add, 4 to change, 0 to destroy` — four attachments created, and each of the four inline policies
losing **exactly one Sid** (`ReadCloudWatchLogs`, or `ReadCloudWatchLogsIncludingInsights` for the
deployment manager) and nothing else. Every deny kept, `DenyControlPlaneOffVpn` still carrying
`52.89.212.1/32` in all four, and the inline documents *shrinking* — 4757→4285, 4473→4001, 3955→3483,
4971→4482 — which is the direction a removed statement should move them. Re-plan `No changes` at
`-detailed-exitcode 0`; `./aws/vpn.py` 0 FAILED with `VP-7` still `pass` on all six.

**Read live before attaching, not from the documentation page**: the policy is on **version 12**, and
v12 added the `observabilityadmin:` namespace — a vocabulary nobody in this project had ever written
down. That version number is itself the argument, from both sides: AWS does maintain it, and AWS does
change it.

**Three things are being accepted, and they are written into `permission-sets.tf` beside the resource
so they are a choice rather than a side effect:**

1. **AWS authors this policy.** A future version reaches these personas with **no diff in this
   repository** — the exact shape [Lesson 11](../plan/lessons.md) warns about, taken deliberately
   because the alternative is a grant that is provably wrong every few months. What bounds it: the
   policy can only ever add *reads*, and it composes **under** every deny already on these sets — the
   shared fragment and `DenyControlPlaneOffVpn` both still apply, a deny always winning.
2. **`logs:StartLiveTail` / `StopLiveTail` arrive with it, and Live Tail is billed per minute.**
   Nothing measures it (D12 declined budget alerts), so this is a cost surface opened without a
   measurement — Lesson 6 acknowledged rather than satisfied.
3. **`cloudwatch:GenerateQuery` and `GenerateQueryResultsSummary` arrive too**, partly undoing the
   decision to defer the `cloudwatch:` namespace. It does **not** include `cloudwatch:GetMetricData`,
   so the console's metrics panel still fails — that one stays deferred to Stage 6 by decision.

`DevEnvStewardAccess` is deliberately outside this: its `ReadBuildPipelineLogs` is narrow on purpose —
the build's own logs, not a console surface — and it never failed. `GovernanceManagerAccess` holds no
`logs:` action at all. **And the reason an AWS-managed policy works where a customer-managed one did
not** (Stage 2 decision 4): the latter must exist as an object in *every* account a set is provisioned
into, which is why the permissions boundary was deferred; an AWS-managed policy exists in all of them
by definition.

### The console confirmed it, and the tunnel-down half of that confirmation is the better finding

Reported by the user, as the Data Scientist User: **with the tunnel up, Logs Insights stopped showing
any error** — `DescribeFieldIndexes` gone with the rest, so the managed policy closed what two
enumerations could not. That is the confirmation a clean plan could not give (presence, not
sufficiency).

**With the tunnel down the errors return, the interface refuses to run a query — and the AWS console
still navigates.** That distinction is worth stating precisely, because it is the one somebody will
later misread as "the deny does not cover the console". It does cover the console's *actions*; it was
never going to prevent the console from *rendering*. `aws:SourceIp` is evaluated on an API call, and
loading a page is not one.

**With it, the layering is now measured end to end, and every layer was read rather than assumed:**

| Off-VPN | Result |
|---|---|
| sign in to the access portal | **works** |
| `sso:GetRoleCredentials` | **works** |
| load and navigate the console | **works** |
| any API call behind those screens | **denied** |

So the answer to "what does a stolen session get you off-VPN" is the same at all three upper layers and
it is the same word: **reconnaissance**. Which accounts exist, which roles are held, which screens
exist — and not one call that returns data or changes anything. Recorded as a property rather than a
gap, and it is exactly the shape 8.4 predicted for the third role.

**Verification (iv) is closed with that.** Exercised as the Data Scientist User, tunnel up: CloudWatch
log groups, Logs Insights (a query ran and returned), the Glue catalog, Athena workgroups (`primary`,
clean). **Nothing broke because of `DenyControlPlaneOffVpn`.** The three things that did break broke for
three other reasons — a Region SCP, a namespace never granted, and an incomplete enumeration — and all
three were attributed **from the wording alone**, which is the whole of what Validation 3 asks for.

### Gates

*Recorded because this entry contains two applies and a change to an instrument, and gate output is the
only part of that which is not somebody's judgement.*

- **`ruff check` and `ruff format --check` on `aws/vpn.py`** — clean. It is the only script this sitting
  changed.
- **`make check`** — `OK`. Seven offline scripts (`check-tf-conventions`, `check-iam-wildcards`,
  `check-bootstrap-parity`, `slices.py check`, `check-tfvars-shape`, `check-index`,
  `check-identifiers`). Worth being explicit about what that does **not** cover: `make check` never
  calls AWS, so it says nothing about either apply — the evidence for those is the re-plan at
  `-detailed-exitcode 0` in the sections above — and `check-identifiers` only guarantees that the
  readings pasted into this file carry no account id or e-mail after the two declared substitutions.
- **`terraform fmt -check -recursive`** on `identity/sso/` — clean.
- **`./aws/vpn.py` re-run after the `VP-7` change** — `0 check(s) FAILED`, `VP-8` still `note`
  (GuardDuty, pass 4). **The line that matters is the new second `VP-7`:**

  ```
  pass  VP-7  DenyControlPlaneOffVpn in the persona sets               all six carry it
  pass  VP-7  DenyControlPlaneOffVpn absent from InfrastructureAccess  by decision (open question 17): the recovery path stays off-VPN
  ```

  Before this sitting that second line read *absent — expected until 8.3*, which is to say the
  instrument was still expecting the opposite of what was decided. **A decision left only in prose is
  measured by nobody**; flipping the check is what makes the seventh set's emptiness an invariant
  rather than a memory.
- **The battery's own banner says `some calls FAILED`, and that is not the verdict** — the checks are
  `0 FAILED`. The failures are seven **profiles with no token**: the two `awsds-ctadmin-*`, which need a
  different sign-in and are only wanted at pass 4, and the five persona profiles — which is exactly the
  set the pair above logged out of, so the banner is a footprint of this entry's own method. Read the
  check table, never the banner.
- **Not run, and deliberately**: `make check-ou` (a session gate about OU coverage, untouched by this
  work) and `make check-docs`, which is red on pre-Stage-2 prose and sits outside the commit gate by
  design — named here so its absence is not read as an oversight.

### Not done
- **`DataScientistStagingAccess` cannot be measured at all, and that is a gap rather than a pass.** It
  carries the deny — `VP-7` confirmed all six — but has **no assignment**, because `Staging` is unvended,
  so there is no account to enter through it. Five sets of six are exercisable; the sixth is an absent
  negative control (Lesson 26's shape) and becomes measurable at the vend, not before.
- ~~The seventh set's diff~~ — **DECLINED, and it is a decision rather than a deferral (option a,
  open question 17, 2026-08-17).** Writing it surfaced the deadlock the stage's Risks row had predicted
  in one line: the VPN host is *stopped* between sessions — the normal `[D]` state — and starting it
  needs `ec2:StartInstances` as the infrastructure user, which the deny would only permit from the
  address of the stopped host itself. The only way back in would be break-glass, for a routine event.
  Three exits were weighed (apply-and-rehearse, a narrow `NotAction` start-the-host hatch, and leaving
  the set off-VPN); **the user chose the third**: every persona is pinned to the tunnel, and the
  administrative credential is deliberately outside it, valued as the recovery path that keeps working
  when the VPN itself is what broke. `./aws/vpn.py` `VP-7` now judges the seventh set in the
  **opposite direction** — a `yes` there is a FAIL naming the deadlock — and what would reopen the
  question (a second operator, GuardDuty's watcher, Stage 14's multiplication of homes) is written in
  the open question, which no current stage waits on. The institutional shape — an admin credential
  that is also the fire escape, two jobs an institution separates — is a new
  `institutional-delta.md` row.
- **`cloudwatch:GetMetricData` is left ungranted by decision**, deferred to Stage 6 with a workload in
  front of it. Recorded so the next person meets a decision rather than a surprise.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
