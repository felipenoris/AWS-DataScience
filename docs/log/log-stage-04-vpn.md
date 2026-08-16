# Log — Stage 4 — VPN access

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`docs/plan/stages/stage-04-vpn.md`](../plan/stages/stage-04-vpn.md).*

*Exceptions, named by SUBJECT so the provenance is not guessed later — the same convention
[Stage 3's log](log-stage-03-networking.md) adopted.*

*Both entries below are exceptions: on **2026-08-16** the user authorised Claude, explicitly, to create
this file and write them directly. Neither records an AWS call — one is a repository change merged with
the Stage 3 teardown, the other is pass 1 authored and gated but **not applied** — so what they are an
account of is repository work and readings, not of actions taken in AWS. The standing rule is unchanged:
the next entry is the user's.*

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

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
