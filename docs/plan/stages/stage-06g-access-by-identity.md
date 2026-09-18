# Stage 6g — Access to AWS by identity, and the VPN for the private network

| | |
|---|---|
| **Status** | **In progress.** Written 2026-09-17 from the requirement change [`objectives.md`](../objectives.md) records and [D39](../decisions/D39-access-by-identity.md) decides, against two read-only inventories of the repository taken the same day. **Step 0 read the same day**: the six deployed sets match the code, no persona called AWS in the seven days before, and the two reaches 0.1 found that no decision named — the Governance Manager's entitlement writes and CloudWatch Logs contents from any network — were accepted without an alarm by the user. **Both applies ran the same day** (steps 1.3 and 2.3, each re-planning `No changes` and read back from the deployed documents), with steps 3 and 4 in the same sitting. **All three decisions due are taken**, 1 and 2 with their own applies: the proxy wears its instance's own address and `make up`'s hub precondition refuses on the proxy alone. Owed: the behavioural pairs 1.4 and 2.4, which need the Data Scientist User's session |
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

- **0.1 read 2026-09-17, from the deployed sets**: `sso-admin` in Identity, the AWS-managed
  `CloudWatchLogsReadOnlyAccess` (v12) and the customer-managed `awsds-org-project-storage-vending` (v1) in
  Sandbox. The six sets match the code. `InfrastructureAccess` carries `AdministratorAccess` and no inline
  policy, so every reach below already exists, from any network, for that one set.

  | Set | Accounts | Reads | Writes | Credential vending |
  |---|---|---|---|---|
  | `DataScientistAccess` | Sandbox | SageMaker `Search`/`List*`/`Describe*`, Glue metadata, LF-Tag reads, CloudWatch Logs | the drop-box `s3:PutObject` with the lake key through S3, still confined by the bucket until step 2 | `lakeformation:GetDataAccess`; `s3:GetDataAccess` and `s3:ListCallerAccessGrants` on Sandbox's Access Grants instance; `ecr:GetAuthorizationToken` |
  | `DataScientistStagingAccess` | Staging | SageMaker, Glue metadata, CloudWatch Logs | none (`DenyEveryWrite`) | none |
  | `DataScientistProdAccess` | Production | SageMaker, Glue metadata, ECR metadata, Athena discovery, CloudWatch Logs | none (`DenyProductionControlPlane`) | `ecr:GetAuthorizationToken` |
  | `DeploymentManagerAccess` | Sandbox, Staging, Production | SageMaker job and registry status, Glue metadata, ECR scan findings, Step Functions and Scheduler, CloudWatch Logs | none (`DenyControlPlaneInFull`, `DenyDataReadPaths`) | none |
  | `DevEnvStewardAccess` | Production, Sandbox | ECR, SageMaker image registration, build logs | none (`DenyShippingTheArtifactItApproves`, `DenyReadingData`) | none |
  | `GovernanceManagerAccess` | Data Governance | Glue metadata, Lake Formation, DataZone, Macie findings | **Lake Formation grants, revocations and LF-Tag administration; DataZone subscription decisions and project membership** | none (`DenyReadingTheRows`) |

  **Two reaches no decision names.** The Governance Manager's entitlement writes become callable from any
  network: who may read the lake can be changed from a laptop anywhere. And the contents of CloudWatch Logs
  become readable from any network by four sets. Neither exceeds `InfrastructureAccess`'s standing reach,
  and no step in Stages 11 or 12 alarms on a Lake Formation grant or a DataZone subscription decision.
  **Taken the same day by the user: both accepted without an alarm**, named in D39 §3, with the
  organization trail as the record.
  **The vending path does not open the governed lake.** Data Governance's `DataLakeSettings` read
  `AllowExternalDataFiltering: false`, `AllowFullTableExternalDataAccess` unset and no authorized session
  tag value. As the vendor documents those settings, that leaves no Lake Formation credential for a
  governed table to a caller outside an integrated engine; unexercised. Sandbox reads
  `AllowFullTableExternalDataAccess: true`, set by SMUS (Stage 16), which reaches the projects' own tables.
- **0.1 [Claude] List, per persona set, what becomes callable from any network**: every action its allows
  grant, grouped as control plane, data plane and credential vending. The data-plane calls the inventory
  already names are `lakeformation:GetDataAccess`, `s3:GetDataAccess` and `s3:ListCallerAccessGrants`,
  `ecr:GetAuthorizationToken`, Production's Athena discovery, and the drop-box write with its KMS pair.
  Anything the list shows that no decision names is a question before 1.3, not after.
- **0.2 read 2026-09-17.** `./aws/vpn.py` `VP-7` pass: all six sets carry the deny, each testing
  `aws:SourceVpc` as well as the address, and `InfrastructureAccess` does not. `./aws/proxy.py` `PX-5`
  pass: `184.33.8.126` is in the deny on six sets. `./aws/datalake.py` `DL-2` pass on the five lake
  buckets, each carrying `ip+prin+sigage+via+vpce`; the script's persona reads failed for want of a Data
  Scientist session, which `DL-2` does not use. **CloudTrail, 2026-09-10T04:41Z onwards, `us-west-2` and
  `us-east-1` in Sandbox, Staging, Production and Data Governance: about 146,000 management events and
  none by a persona set.** The absence is evidence: the same filter on `sessionIssuer.userName` returns the
  `InfrastructureAccess` sessions, all from a laptop's own uplink or a service and none through either hub
  address. So no refusal of the deny is on record for the window, and 1.4's before half is provoked rather
  than read.
- **0.2 [Claude] Read the before state.** `get-bucket-policy` on the five lake buckets and `./aws/datalake.py`
  `DL-2`; `./aws/vpn.py` `VP-7` and `./aws/proxy.py` `PX-5` green; seven days of the six sets' CloudTrail
  events by `sourceIPAddress`, which should read the proxy's and the WireGuard host's addresses only.
- **0.3 read 2026-09-17** (`git grep` over tracked files, the stage logs excluded). The hub's addresses
  are a policy value in `identity/sso/` and `data-governance/data/` only, both fed by `backend.py`'s
  `VPN_HOMES`, and `production/networking/` outputs them. Every other hit is a comment or a document,
  `sandbox/foundation/` included. No instrument reads them from the repository, and the repository records
  no third party that allow-lists the egress address. So `VPN_HOMES` goes entirely at 2.1, and decision due
  1 finds no consumer outside the documents once steps 1 and 2 have applied.
- **0.3 [Claude] Enumerate every consumer of the hub's addresses as a value**: `VPN_HOMES`, `vpn_homes`,
  `wireguard_eip_public_ip`, `proxy_eip_public_ip`, and the two addresses as literals, across code,
  instruments and documents (Lesson 48). The list decides whether `VPN_HOMES` goes entirely in 2.1, and it
  is decision due 1's input.

### 1. Delete the persona deny — `identity/sso/`

- **1.1-1.3 done 2026-09-17.** The code: the fragment, its six compositions, both address
  preconditions, both locals, the `vpn_home` read, the `vpn_homes` variable and `backend.py`'s emission
  to this slice. Plan `0 to add, 6 to change, 0 to destroy`, each inline policy losing
  `DenyControlPlaneOffVpn` alone (273 bytes; every other statement identical); applied; re-plan
  `No changes`. Read back on the nine provisioned persona roles in Sandbox, Staging, Production and Data
  Governance: no `DenyControlPlaneOffVpn` and no network-origin key on any (`DataScientistAccess` 19 →
  18 statements). 1.4 is owed: it needs the Data Scientist User's session.
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

- **2.1-2.3 done 2026-09-17.** `DenyOutsideTrustedNetworks` lost the `aws:SourceIp` branch
  (`184.33.8.126/32`, `52.89.212.1/32`) and `VPC-Networking`'s gateway endpoint from `aws:SourceVpce`,
  keeping Sandbox's. On the drop-box it denies every action but `s3:PutObject`, beside
  `DenyLetterboxPutOutsideTrustedNetworksToAllButTheWriter`, which names the persona through
  `data_scientist_writer_pattern` rather than `writer_role_patterns`, and
  `DenyPutOutsideTheLetterboxOffTrustedNetworks`, which keeps the exemption on the prefix. `VPN_HOMES`
  left `backend.py` with its renderer. Plan `0 to add, 5 to change, 0 to destroy`, read statement by
  statement against this design; applied; re-plan `No changes`. The five deployed policies read back with
  no `aws:SourceIp` and no hub endpoint, the drop-box at nine statements. 2.4 is owed with 1.4.
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

- **Step 3 done 2026-09-17, each instrument run after its edit.** `VP-7` passes: none of the seven
  sets carries a network-origin key, and its classifier separates all three keys against fabricated
  policies. `proxy.py` reads the proxy's account alone, `PX-1`..`PX-4`. `DL-2` passes on the five
  buckets with no `ip` tag and the drop-box's principal branch naming `s3:PutObject` alone, while
  fabricated `s3:*` and `NotAction` exemptions and an address branch fail. `DT-1` expects `vpce`, `via`
  and `prin` and refuses `ip` on `awsds-prod-outputs`, which reads as a note until Stage 9 builds it.
  `RI-5`, `studio.py`, `NT-9`, `eip-transfer.py`, `aws/INDEX.md` and `AWS-CLI.md` state the channel
  and the addresses without a network requirement. Decision due 3 was taken as recommended: inverted.
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

- **4.1 done 2026-09-17.** `README.md`'s tunnel section and `s3-read-write` line,
  `terraform-live/README.md`, `docs/NETWORK.md`'s client rows and instruments (`check-network-doc.py`
  clean), `docs/AWS_STATE.md` with `INV-19` and §C's rows struck with their dates, `docs/GLOSSARY.md`,
  `docs/SMUS.md`, `docs/REFERENCES.md`, `POLICIES.md`'s serial-console row and `CLAUDE.md`.
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

   **Taken 2026-09-17 as recommended: the instance's own address.** 0.3 found no consumer outside these
   documents. `aws_eip.proxy` and its two outputs left `production/networking/`; `production/proxy/` sets
   `associate_public_ip_address = true` and lost both the association and the `ignore_changes` that the
   `[P]` address needed. The proxy plan read `1 to add, 2 to change, 2 to destroy`: **the host
   replacement was already owed** before this edit, forced by the SSM-resolved `ami` and by a `user_data`
   comment changed in `c70e73e`, and the address change alone would not have replaced it. Applied —
   `i-0d42d0393c39eefdb`, private `10.31.160.140` with `proxy.awsds.internal` re-pointed to it, public
   `35.90.250.102` — then `production/networking/` `0 to add, 0 to change, 1 to destroy` released
   `184.33.8.126`. Both re-plans `No changes`, `52.89.212.1` is the estate's only Elastic IP, and
   `make hub-down` stopped the host again. The hub ran **68.7 hours in the previous 30 days**, so the
   released allocation saves ≈ **USD 3.3/month** and the instance's own address costs ≈ 0.34 at that rate.

   **A replacement is pending from the same sitting.** `user-data.sh.tftpl`'s first-render comment was
   corrected after the apply — it named the Elastic IP association — and the deployed host reads back
   carrying the old text, so the next apply of `production/proxy/`, which `make hub-up` runs, replaces
   the host. It is stateless and rebuilds from this template; only the public address moves with it.
2. **The spoke precondition of `make up`** (6c step 7.2), which refuses while either hub host is stopped. After
   step 1 a Sandbox session needs the proxy, and the WireGuard host only to reach a private name.
   Recommended: keep both hosts in the precondition. `hub-up` starts both anyway, and one rule is easier to
   read than a rule per purpose.

   **Taken 2026-09-17: the proxy alone**, not both hosts. Since D39 nothing a spoke applies, and no session
   it opens, needs the private network, so a stopped tunnel is no longer a reason to refuse an apply;
   `hub-up` still starts both, and `slices.py` reports the tunnel's state beside the proxy's without
   refusing on it. Exercised with both hosts stopped: the refusal named `awsds-prod-proxy` and the tunnel
   row read `(the private network only - no refusal, D39)`. Fabricated states cover the rest — proxy
   running and tunnel stopped proceeds, proxy stopped and tunnel running refuses, both `UNREADABLE`
   waives (Lesson 13's asymmetry, unchanged).
3. **`VP-7`: inverted or retired.** Recommended: inverted. A network condition re-added to a persona set by a
   later change breaks nothing on the tunnel, so no other instrument would notice it.

   **Taken 2026-09-17 as recommended: inverted**, and run after 1.3 (step 3).

## Cost

None from the two applies: they change policy documents only. **Decision 1 removes USD 0.005/h for every
hour the hub is stopped** — ≈ USD 3.3/month at the measured 68.7 hours of uptime per 30 days — and adds
the same rate while the proxy runs, ≈ 0.34/month.

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
