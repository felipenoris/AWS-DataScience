# Log — Stage 4 — VPN access

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-04-vpn.md`](../plan/stages/stage-04-vpn.md).*

*Exceptions, named by SUBJECT so the provenance is not guessed later — the same convention
[Stage 3's log](log-stage-03-networking.md) adopted.*

*The six entries below are exceptions: on **2026-08-16** the user authorised Claude, explicitly, to
create this file and write the first two directly, and on **2026-08-17** to write the third, the
fourth, the fifth and the sixth the same way. The first three record no AWS call — one is a repository
change merged with the Stage 3 teardown, one is pass 1 authored and gated but **not applied**, and the
third is a design review propagated through the repository. **The last three are different in kind:
they are the stage's AWS writes**, applied by Claude on the user's explicit authorisation of those
specific steps, and written here by the same authorisation. **Two of them also record steps Claude did
not perform** — step 4.3 and the key generation of 4.1, both run by the user on the devices — and each
says so where it does. The standing rule is unchanged: the next entry is the user's.*

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

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
