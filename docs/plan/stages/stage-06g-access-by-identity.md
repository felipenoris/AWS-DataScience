# Stage 6g — Access to AWS by identity, and the VPN for the private network

| | |
|---|---|
| **Status** | Not started. Written 2026-09-17 from the requirement change [`objectives.md`](../objectives.md) records and [D39](../decisions/D39-access-by-identity.md) decides, against two read-only inventories of the repository taken the same day. No AWS reading has been taken for it yet |
| **Prerequisites** | **None that block.** The hub up (`make hub-up`) only for the monitored-profile halves of 1.4 and 2.4 |
| **Consumes** | [D6](../decisions/D06-dlp-approach.md), [D13](../decisions/D13-lake-formation-enforcement.md), [D18](../decisions/D18-data-scientist-access.md), [D38](../decisions/D38-single-egress-hub.md), [D39](../decisions/D39-access-by-identity.md) |
| **Proves** | Nothing new crosses an account boundary. Retired: [INT-16](../integrations.md) as a recorded deviation. Changed in shape: [INT-05](../integrations.md)'s laptop half, from an address branch to a principal branch |

*Read with [`docs/plan/runbooks/terraform-changes.md`](../runbooks/terraform-changes.md) (Recipe A, a
change inside a slice) and [`docs/plan/conventions.md`](../conventions.md).*

---

**Objective:** a persona reaches the AWS console, the APIs and the SageMaker Unified Studio portal from any
network with its Identity Center session; the laptop's drop-box write reaches the lake by principal; the
private network stays behind the VPN; and every instrument, runbook and document that described the
previous perimeter says what the estate does after the applies.

## What this stage changes, and in which account

| Account | What changes | Slice | Profile |
|---|---|---|---|
| `Identity` | `DenyControlPlaneOffVpn` leaves the six persona permission sets, provisioned into `Sandbox`, `Staging`, `Production` and `Data Governance` | `identity/sso/` | `awsds-infra-identity` |
| `Data Governance` | `DenyOutsideTrustedNetworks` loses its Elastic IP branch and `VPC-Networking`'s gateway endpoint; the drop-box admits `DataScientistAccess`'s `s3:PutObject` by principal | `data-governance/data/` | `awsds-infra-data` |
| — | `scripts/tfhygiene/backend.py`'s `VPN_HOMES` emission, the instruments, the runbooks and the documents | repository | — |

**Unchanged:** the WireGuard and Squid hosts, every proxy plane, the compute's egress, the SMUS
configuration, the lake's workload doors, and both VPN client profiles.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls, done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write, run only after the user authorizes that action in chat |
| **[user]** | the console, the laptop's terminal and the VPN client, the provoking half of every measurement |

## Step numbers are identifiers, not an order

Step 0 precedes steps 1 and 2. Steps 1 and 2 are independent: before step 1 the persona deny still
confines the drop-box write, and before step 2 the bucket policy still does, so neither order opens more
than D39 decides. Steps 3 and 4 run in the sitting of the apply they describe, never before it: until the
apply, the documents that describe the deny are true (Lesson 37).

---

## To execute

### 0. Read what the removal opens, before anything is removed

**Why:** a deny over `*` hides what the allows beneath it say. Stage 5 pass 4d measured it on 2026-08-20:
`DenyControlPlaneOffVpn` had been masking the drop-box write and D13's refusal until an on-tunnel session
exercised both (Lesson 20's mirror).

- **0.1 [Claude] List, per persona set, what becomes callable from any network**: every action its allows
  grant, grouped as control plane, data plane and credential vending. The data-plane calls the inventory
  already names are `lakeformation:GetDataAccess`, `s3:GetDataAccess` and `s3:ListCallerAccessGrants`,
  `ecr:GetAuthorizationToken`, Production's Athena discovery, and the drop-box write with its KMS pair.
  Anything the list shows that no decision names is a question before 1.3, not after.
- **0.2 [Claude] Read the before state.** `get-bucket-policy` on the five lake buckets and `./aws/datalake.py`
  `DL-2`; `./aws/vpn.py` `VP-7` and `./aws/proxy.py` `PX-5` green; seven days of the six sets' CloudTrail
  events by `sourceIPAddress`, which should read the proxy's and the WireGuard host's addresses only.
- **0.3 [Claude] Enumerate every consumer of the hub's addresses as a value**: `VPN_HOMES`, `vpn_homes`,
  `wireguard_eip_public_ip`, `proxy_eip_public_ip`, and the two addresses as literals, across code,
  instruments and documents (Lesson 48). The list decides whether `VPN_HOMES` goes entirely in 2.1, and it
  is decision due 1's input.

### 1. Delete the persona deny — `identity/sso/`

- **1.1 [Claude] The code, in one commit.** The `control_plane_vpn` document in `policies-shared.tf` and its
  composition into the six sets (`policies-data-scientists.tf`, `policies-approvers.tf`); the two
  preconditions in `permission-sets.tf`; the `vpn_egress_cidrs` and `vpn_egress_vpc_ids` locals; the
  `vpn_home` remote state in `data.tf`; the `vpn_homes` variable; and `backend.py`'s emission of
  `vpn_homes` to this slice. The variable refuses an empty map, so emptying `VPN_HOMES` instead is not an
  option. The comments that argued the deny go with it (`policies-shared.tf`, `permission-sets.tf`'s
  `CloudWatchLogsReadOnlyAccess` sentence, the slice's `README.md`).
- **1.2 [Claude] Plan to a file and read it** (`-input=false`, Lesson 47). Expected: the six inline policies
  updated and nothing else.
- **1.3 [Claude⚡] Apply**, then re-plan `No changes`.
- **1.4 [user provokes, Claude records] The pair, on the same principal.** As `awsds-scientist-sandbox`
  (`DataScientistAccess`, Sandbox), from the split-tunnel profile with no proxy configured, then with the
  tunnel down: `aws logs describe-log-groups`, which the deny refused explicitly before 1.3 (INT-16's
  console contrast) and `CloudWatchLogsReadOnlyAccess` allows, now answers; `aws s3 ls`, refused
  explicitly before 1.3 (`docs/NETWORK.md`'s split-tunnel row), answers or changes to an implicit
  refusal, as 0.1's list of the set's allows predicts. `aws sts get-caller-identity` is no evidence
  either way, since no policy can deny it. The negative control is an action the set's allows
  never grant, still refused, with the wording naming the identity-based policy's implicit deny rather
  than any explicit one (Lesson 24). The private network stays closed with the tunnel down:
  `proxy.awsds.internal` does not resolve. Under the monitored profile, the same calls answer through the
  proxy, and the access log still records the device's `10.90.0.<n>` address.

### 2. Admit the laptop to the lake by principal — `data-governance/data/`

- **2.1 [Claude] The code, in one commit.** `DenyOutsideTrustedNetworks` loses the `aws:SourceIp` branch
  and `vpn_home_vpce_ids` (`trusted_vpce_ids` keeps `consumer_vpce_ids`). On the drop-box, a principal
  branch admits `s3:PutObject` from the principal `AllowInteractiveWriterPutOnly` already names, bound to
  the action and the bucket as well as the principal, so no allow written later inherits it (Lesson 29).
  The persona's every other action and every other principal keep the network condition. Then
  `wireguard_eip_cidrs`, the `vpn_home` data source, the `vpn_homes` variable, `backend.py`'s emission to
  this slice, and `VPN_HOMES` itself if 0.3 found no other reader. `buckets.tf`'s branch comments and the
  slice's `README.md` rows change in the same commit, since that README is reviewed with the `.tf` files.
- **2.2 [Claude] Plan to a file and read it.** Expected: the five bucket policies updated and nothing else.
- **2.3 [Claude⚡] Apply**, then re-plan `No changes`.
- **2.4 [user provokes, Claude records] The contrast.** As `awsds-scientist-sandbox`, from a laptop with no
  proxy: `s3:PutObject` into the drop-box's dated prefix succeeds; `s3:PutObject` into `awsds-data-raw`
  fails, and its wording says whether the bucket policy or the identity refused it. From a Sandbox space,
  an Athena query over `curated` still returns rows (the service door and the gateway endpoint, unchanged).
  The drop-box object cannot be collected before Stage 9's `awsds-prod-job-exec` exists, so it joins
  `EXC-02` by key and date.

### 3. The instruments, in the sitting of each apply

- **3.1 [Claude] `./aws/vpn.py` `VP-7`, inverted into D39's regression guard** (decision due 3): pass when no
  permission set, `InfrastructureAccess` included, carries a statement testing `aws:SourceIp`,
  `aws:SourceVpc` or `aws:SourceVpce`; fail when one appears. The constants, the Identity read and the
  report text that argued the deny change with it. Written and run after 1.3, not before (Lesson 50).
- **3.2 [Claude] `./aws/proxy.py` `PX-5` retired.** After 2.3 no policy names the proxy's address; its
  report section and its Identity read go.
- **3.3 [Claude] `./aws/datalake.py`.** `DL-2` keeps requiring the endpoint, service and signature-age
  branches and gains two assertions: no lake bucket carries an `aws:SourceIp` branch, and the drop-box's
  principal branch names `s3:PutObject` alone. The `ip` report label goes.
- **3.4 [Claude] `./aws/deploytargets.py` `DT-1`**, for the `awsds-prod-outputs` bucket Stage 9 builds:
  endpoint and service branches, a principal branch for `DataScientistProdAccess`'s reads, and no
  `aws:SourceIp` branch.
- **3.5 [Claude] The labels that framed a gap.** `./aws/remote-ide.py` `RI-5` keeps its breakdown of
  `StartSession` sources and drops the VPN-compliance reading; `./aws/studio.py` loses the INT-16 owed
  proof; `./aws/networking.py` `NT-9` rewords its trigger; `aws/INDEX.md` and `aws/AWS-CLI.md` follow.

### 4. The documents that describe the running estate, in the sitting of the applies

- **4.1 [Claude] The estate's descriptions.** `README.md` items 2 and 3 and the `s3-read-write` line;
  `terraform-live/README.md`; `docs/NETWORK.md`'s client rows and its instrument line, with
  `./scripts/check-network-doc.py`; `docs/AWS_STATE.md` §C's rows on the deny and the lake perimeter,
  and a new invariant that no permission set carries a network-origin condition, read by `VP-7`;
  `docs/GLOSSARY.md`'s split-tunnel and `aws:SourceIp` entries; `docs/SMUS.md`'s vending paragraph;
  `docs/REFERENCES.md`'s INT-16 label; `POLICIES.md`'s serial-console row, whose reason becomes the
  private-network boundary; `CLAUDE.md`'s current position.
- **4.2 [Claude] The runbooks.** `vpn.md` (the rules at its top, §S4, §C7, §K0a, §K3, §K6),
  `client-vpn-proxy-configuration.md`, `buildbox.md`, `claude-code-sagemaker.md`, `remote-ide.md`,
  `sandbox-lake.md`.
- **4.3 [Claude] `s3-read-write/`**: its `README.md`, the package docstring and `examples/demo.py`, which
  say the handshake is denied off the VPN.
- **4.4 [Claude] The comments.** `production/networking/` (`outputs.tf`, `hub-anchors.tf`'s Elastic IP
  argument), `production/proxy/` (`main.tf`'s checkov skip reason, `outputs.tf`), `production/vpn/main.tf`,
  `production/buildbox/README.md`, `sandbox/foundation/` (`persona-vending.tf`, `outputs.tf`),
  `data-governance/governance/outputs.tf`; `scripts/tfhygiene/backend.py`, `layers.py`, `slices.py` and
  the `Makefile`. **The security group description in `hub-anchors.tf` stays as it is**: it is still true,
  and changing a description replaces the group. `terraform-modules/wireguard/variables.tf`'s two comments
  change at that module's next tag, not with a tag of their own.

---

## Verifications

| # | Question | Step |
|---|---|---|
| i | Does a persona call from outside the VPN, with no proxy configured, answer after 1.3, and what did the same call's refusal name before it? | 0.2, 1.4 |
| ii | Did the removal open anything 0.1 did not list? | 0.1, 1.4 |
| iii | Does the drop-box take the persona's write from any network while the same persona's write to another lake bucket still fails, and which policy refuses it? | 2.4 |
| iv | Is the lake's read path from a Sandbox space unchanged? | 2.4 |
| v | Does the private network stay closed off the VPN? | 1.4 |
| vi | Does the monitored profile still work end to end, its access log attributing each device? | 1.4 |

## Decisions due

1. **The proxy's public address** (D38 §3). After 2.3 no policy names it, and what binds to it is CloudTrail
   attribution and any third party that allow-lists the estate's egress, of which 0.3 is the list. As a
   `[P]` Elastic IP it bills USD 0.005/h while the hub is stopped; the instance's own public IPv4 is
   released at every stop and bills only while it runs. Recommended: the instance's own address, if 0.3
   finds no consumer outside the documents.
2. **The spoke precondition of `make up`** (6c step 7.2), which refuses while either hub host is stopped. After
   step 1 a Sandbox session needs the proxy, and the WireGuard host only to reach a private name.
   Recommended: keep both hosts in the precondition. `hub-up` starts both anyway, and one rule is easier to
   read than a rule per purpose.
3. **`VP-7`: inverted or retired.** Recommended: inverted. A network condition re-added to a persona set by a
   later change breaks nothing on the tunnel, so no other instrument would notice it.

## Cost

None. Both applies change policy documents only. Decision due 1 would remove USD 0.005/h for every hour the
hub is stopped.

## Risks

- **An allow nobody reviewed becomes reachable from any network.** 0.1 is the defence, taken before 1.3.
- **The instruments degrade quietly.** Left as written, `VP-7` and `PX-5` print misleading notes rather than
  failing, so step 3 runs in the apply's sitting.
- **`VPN_HOMES` feeds two slices.** A generator change that lands before both variables go leaves a value
  for an undeclared variable, so 1.1 and 2.1 each carry their half of the emission.
- **The identity premise is modelled, not enforced** (D39 §4). Identity Center's own directory admits a
  sign-in from any device; Stage 11's threat model carries the residual.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
