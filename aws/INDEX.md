# `aws/` — index

Read-only scripts that photograph what is deployed in AWS, and the text snapshots they produce. Nothing
here creates, changes or deletes a resource, and nothing here is infrastructure code; that is
`terraform-live/` from Stage 2 on.

[`docs/GENERAL_PLAN.md`](../docs/GENERAL_PLAN.md) and `docs/plan/` say what *should* be there, the
[`docs/log/`](../docs/log/INDEX.md) files say what was *done by hand*, and these snapshots say what AWS
*reports right now*. The three disagreeing is itself information.

[`probes/`](probes/README.md) is the exception to the read-only sentence, fenced rather than hidden. The
SCP battery attempts the calls a policy forbids, the only way to measure a preventive control, so it
reaches authorization and leaves `AccessDenied` events in CloudTrail. It creates nothing: every probe is
read-only, carries `--dry-run`, or names a prerequisite that does not exist, and the seven that would act
if a deny were missing are refused by the driver anywhere but `Policy Canary`. The scripts on this page are
run to gather information; the battery is run deliberately. Its reports land in `output/` beside these
snapshots.

`./aws/vpn.py --on-host` is the second exception, a flag that is off by default. It reads inside the
WireGuard host through SSM Run Command (the boot log, `wg show wg0`, the peer-name map, the sampler timer,
`lsblk` and `df -h /`), the only way to learn which peers the running interface holds and whether the
filesystem followed the volume after a `root_volume_size` change; no `describe` call answers either. Every
command it carries is a read, but `ssm:SendCommand` is a write API (a Command resource, a mutating
CloudTrail event, code executed on an instance), so the flag is typed rather than assumed. The script names
the read-only path tried first: `ec2:GetConsoleOutput` returned zero bytes on both Stage 4 hosts for
minutes, and could never answer the peer question. Without the flag `vpn.py` is read-only like every other
script here; `--on-host` is run deliberately.

[`dns-allowlist.py`](dns-allowlist.py) needs no AWS identity. Every other file on this page photographs
AWS; that one photographs the public DNS the proxy's allow-lists depend on, reading this repository's own
`.tf` and asking a resolver. Its AWS mode (`--from-api`, the deployed lists) is not the default, because
`egress/` is `[E]` and down most of the time, and the check matters before the slice is brought up. Its
two identity columns below therefore read *none*.

## The scripts

| Script | SSO user signed in | Profile it runs as | Writes | Captures |
|---|---|---|---|---|
| [`list-identities.py`](list-identities.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity` (Identity account, IAM Identity Center delegated administrator, D10) | `output/list-identities.txt` | The Organization: the organization id (the value `aws:PrincipalOrgID` and `aws:ResourceOrgID` are compared against), the management account id, the root and its enabled policy types, the OU tree, every account. The directory: Identity Store instance, groups, users, group memberships. The entitlements: permission sets with what each grants, and every assignment triple. |
| [`AZs.py`](AZs.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user), also behind `awsds-policy-canary`, the same user through a different permission set (D32) | every `awsds-*` profile in `~/.aws/config`, or the ones named as arguments (multi-profile, see below) | `output/AZs.txt` | The availability-zone name → zone ID mapping each account reports, one listing per account, the mappings side by side, and whether they agree. |
| [`org-trusted-access-services.py`](org-trusted-access-services.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; another profile as its argument, or `-` for no profile at all, inside CloudShell on Management | `output/org-trusted-access-services.txt` | Which AWS services hold trusted access across the organization, which account is each one's delegated administrator, the `access-analyzer` registration on its own, and whether the `account.amazonaws.com` switch that lets Management rename a member account is on (Stage 6b step 0.5a). |
| [`cloudshell/audit-iam-analyser.sh`](cloudshell/audit-iam-analyser.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33), no laptop path | no profile: CloudShell on the Audit account as `AWS Control Tower Admin`. Takes a profile as its argument if one ever exists there | `output/cloudshell/audit-iam-analyser.txt` | The IAM Access Analyzer analyzers of that account and Region: type (the zone of trust), status, tags, archive rules, findings, and a check that there is exactly one, `ORGANIZATION`, `ACTIVE`. |
| [`org-policy-baseline.py`](org-policy-baseline.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user), whether it suffices being section 7's answer; [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback, which section 5 needs | `awsds-infra-identity` by default; another profile, or `-` for CloudShell on Management as `AWS Control Tower Admin`, the fallback if the policy reads are denied | `output/org-policy-baseline.txt` | The policy ceiling that already exists: organization id and feature set, the root and its enabled policy types, every node with its id, ARN and full path, the policies attached per node per type, the documents of the ones found, the Control Tower controls enabled per node, and the policy quota. Stage 1c step 7.0 steps 1, 2, 3 and 5 in one pass. |
| [`org-policies.py`](org-policies.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; another profile, or `-` for CloudShell on Management | `output/org-policies.txt` | What governs each node now, by `Sid`, with no document bodies: the attachments per node condensed to statement names, what governs each account once inheritance is resolved, the read-only checks no probe can reach, and a per-OU ceiling table. Exits 2 when a check fails, so it can gate a change. Section 1 lists the ids of all four policy types, the argument [Stage 2](../docs/plan/stages/stage-02-terraform-foundation.md) step 5.5 takes; the [1c log](../docs/log/log-stage-01c-preventive-policies.md) carries their attachment dates |
| [`account-bpa.py`](account-bpa.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs in Management, Log Archive and Audit | every `awsds-*` profile, the ones named as arguments, or `-` inside CloudShell for the three accounts without a profile (multi-profile) | `output/account-bpa.txt` | The account-level S3 Block Public Access configuration of each account, the four flags side by side, and which accounts nothing is measuring. Read before 7.4, after 7.4 and before 7.5, and at every vend. |
| [`bedrock.py`](bedrock.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | every `awsds-*` profile in `~/.aws/config`, or the ones named as arguments (multi-profile) | `output/bedrock.txt` | What Amazon Bedrock is enabled for, per account, in three layers the console blurs: the **account gates** (the use-case form, the data retention mode, model invocation logging), the **catalogue** (providers, the scoped model set with its lifecycle and inference types, the inference profiles the account holds and how many models each routes to), and the **resources that would be billing** (provisioned throughput, custom, imported and marketplace models, guardrails). It decodes the use-case form, which is a blob on both sides of the API and double base64 over flat JSON inside. `BR-7` is an instrument control rather than a finding: it compares the availability reading in an account that submitted the form against one that did not, and reports whether the call distinguishes them. |
| [`declarative-ec2.py`](declarative-ec2.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for the `-` runs | every `awsds-*` profile, the ones named, or `-` inside CloudShell (multi-profile) | `output/declarative-ec2.txt` | The four EC2 settings `awsds-org-declarative-ec2` declares, read back per account against the document. A declarative policy is enforced in the service's control plane, so the battery can only show that a change is refused; this shows what the setting is. Also the one instrument that answers whether a root-attached declarative policy reaches Management, which AWS documentation leaves undecided. |
| [`org-delegation.py`](org-delegation.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) on the `-` fallback | `awsds-infra-identity` by default; another profile, or `-` for CloudShell on Management | `output/org-delegation.txt` | INT-20: can the Identity account manage the organization's policies, and which of them. The organization resource policy in three distinguishable states (present, absent, the read itself denied), decomposed into nine checks: the principal, the read and write halves, the two actions that must be absent, and the three that fail silently, whether the `Resource` list reaches the root, nested OUs and the policy-type ARNs at all (`DEL-9`: a target-only list denies every write and reads like "all refused"). Plus the documents a write would have to reach, split by target class. Exits 2 when a check fails. |
| [`import-ids.py`](import-ids.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | `awsds-infra-identity`, which reaches both planes: Identity Center delegated administrator (D10) and Organizations reads (1c verification (x)) | `output/import-ids.txt` | The import manifest for Stage 2 step 5: the exact strings `terraform import` takes, in the four formats, for every policy, every attachment, the `InfrastructureAccess` set and its assignments; the resolved values of the three template placeholders; and, in section 4, what must not be imported, with the reason. |
| [`tf-backends.py`](tf-backends.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | every `awsds-*` profile, the ones named, or `-` (multi-profile) | `output/tf-backends.txt` | The Terraform state buckets and their keys, side by side: existence, versioning, SSE-KMS and the key's alias, the four BPA flags, the TLS-only statement, the noncurrent-version lifecycle, Object Lock, plus every bucket in each account, so one under an unexpected name is visible. Section 4 decides Stage 2 step 3.4's two keys in Production. Exits 2 when a check fails. |
| [`s3-persistence.py`](s3-persistence.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); the default profile list is this user's own reach, narrower than `awsds-*`, because the four persona sessions belong to different people and each demands its own login | every `awsds-infra-*` profile plus `awsds-policy-canary`, the ones named, or `-` inside CloudShell; multi-profile because a bucket holding governed data in the wrong account is the finding | `output/s3-persistence.txt` | The whole S3 estate and every setting that describes a bucket. `tf-backends.py`, `datalake.py` and `account-bpa.py` each judge one contract and start from the buckets they expect; this file starts from the estate and judges every bucket against the invariants that hold for all of them: in `us-west-2`, public access blocked, encrypted under a named key, ACLs disabled, no wildcard principal, no website, no wildcard CORS. Per bucket: Region, age, origin, versioning and MFA delete, SSE and the key's alias, the four BPA flags, object ownership, the bucket policy one row per statement (`POLICIES.md`'s discipline applied to a resource policy: Sid, effect, principal, action count, condition keys, and whether the statement is `OPEN`), lifecycle, Object Lock, replication with its destinations printed and never judged, access logging, event notifications, tags, and the CloudWatch daily size and object metrics. Plus the four surfaces `list-buckets` does not show: directory buckets, S3 Tables (`S3TableCatalog` is an enabled blueprint, so a project can make one with no Terraform), access points with their own policy and BPA, and multi-region access points. Checks `SP-0`–`SP-9`; exits 2 when a check fails. `none` and `DENIED` never share a cell: a refused per-resource read is a reading of the permission ceiling (section 11's second table), never an error |
| [`networking.py`](networking.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | every `awsds-*` profile, the ones named, or `-` inside CloudShell; multi-profile because a CIDR overlap, a peering and a cross-account zone association are facts between accounts | `output/networking.txt` | The `[P]` networking half per account, side by side: [Stage 3](../docs/plan/stages/stage-03-networking.md)'s preflight and its standing regression. VPCs with default and Account Factory vend artifacts flagged (every vended account carries one, `docs/AWS_STATE.md` §C), the two DNS attributes of step 4.1, subnets with their zone IDs (step 1.5), route tables and routes, IGWs, the gateway endpoint IDs that are the INT-05 anchor (the only endpoint IDs a policy may name, Lesson 3), peerings from both sides (INT-09), the three private zones with associations and pending authorizations (the 4.5 trap), flow logs with retention, NACLs and SGs. Checks `NT-1`–`NT-8` mechanise validation 2 (no route into `10.40.0.0/16`, local routes excluded), step 6.5 (`10.90.0.0/24` nowhere), step 1.2 (no overlap), 4.1, 4.4 and 5. `NT-9` pins the regional endpoint-service catalog against the SMUS portal's browser surfaces: the 2026-08-24 absence (no private door for the portal, which therefore needs public egress under every endpoint set) is held as a family baseline, so AWS shipping one turns up as a red check. `NT-10` reads the deployed interface endpoints' `DnsEntries`, the public names each door seizes in the VPC resolver, and fails when one seizes or shadows a portal name the same page requires over the public internet (the 2026-08-24 breakage, as a check). Exits 2 when a check fails. The `[P]`-stability deliverable is a diff of two runs, either side of a `make down`/`make up` |
| [`egress.py`](egress.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: step 8's endpoint list is per account role, so the set is only readable with the columns side by side | `output/egress.txt` | The `[E]` networking half, plus the burn meter. Interface endpoints (subnet count per D9, private DNS per 8.5), NAT gateways, elastic addresses, every endpoint policy read against step 9 (the org condition, 9.1, and the AWS-owned-bucket allow, 9.3; presence, never completeness, the no-NAT `dnf` probe being the stage's), the service × account matrix read against step 8's lists (not encoded here, Lesson 14), the hourly burn right now (the instrument the forgotten-egress risk gets, D12 having skipped the alerts; zero everywhere is D11 working), and the region's endpoint service-name catalog, which answers stage verification (i) and the `VpcEndpointPolicySupported` flag before anything is paid for. Checks `EG-1`–`EG-4`; exits 2 when a check fails |
| [`dns-allowlist.py`](dns-allowlist.py) | none in the default mode (no session, no profile, no AWS call); [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) on Production for `--from-api` | none by default: it reads `terraform-live/production/networking/hub-anchors.tf`, the `[P]` slice that declares the proxy's five source-scoped planes. `--from-api` adds one read, `ssm:GetParameter` on `/datascience/prod/proxy/allowlist` | `output/dns-allowlist.txt` | The estate's egress policy, which since Stage 6c step 5.7 is Squid's allow-lists rather than the DNS Firewall's: one list per source, so what a person on the tunnel may reach differs from what a notebook may. Per exact hostname: the chain, whether it answers, the terminal address and, with `--whois`, who owns it, the party each entry extends trust to. A leading-dot entry (`.x`) is coverage and is never queried; `*.internal` names are listed and skipped. `DN-1`: every name still answers. `DN-2`: no apex is listed beside its own `.x`, which is `FATAL: Bungled`, a proxy that does not start and every spoke losing the internet at once; nothing else checks it. `DN-3`: the committed planes equal the deployed parameter, the first of two links (`PX-3` in `proxy.py` compares that parameter with the running `squid.conf`). `DN-4`: no plane is `open` except the ones a decision names (`OPEN_BY_DECISION`). Exits 2 when a check fails. What it cannot see: it is not the proxy's resolver. Under an explicit proxy a spoke client resolves nothing and Squid does, so a clean run is a screen and the proof is a request through the proxy |
| [`proxy.py`](proxy.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) on Production and Identity; the two halves of `PX-5` sit in two accounts, and one login (the `awsds` sso-session) covers both | `ec2:DescribeInstances`, `DescribeAddresses`, `DescribeSecurityGroups`, `ssm:GetParameter`, `logs:DescribeLogGroups`, `DescribeSubscriptionFilters`, `sso-admin:*` reads. `--on-host` adds `ssm:SendCommand`, a write API carrying only reads, fenced as `vpn.py`'s is | `output/proxy.txt` | The instrument for D38's single internet exit, shaped after `vpn.py` (one way in, one way out). `PX-1`: only the spokes and the tunnel may reach 3128. `PX-2`: no `http_access allow` precedes the private-destination deny; the order is the security property, since one allow above it makes the proxy an L7 bridge between VPCs peering keeps apart. The check reads the committed template with no session and the running file with `--on-host`, both counting toward the verdict. `PX-3`: the running allow-list equals the committed one, the second of two links (`DN-3` in `dns-allowlist.py` is the first, and needs no write API). `PX-4`: the access log group; a missing Log Archive export is a `note`, not a `fail`, because 4.11's second half is an open decision. `PX-5`: the perimeter names the address the estate leaves under. Exits 2 when a check fails. What it cannot see: whether a request succeeds. Every check reads configuration; the behavioural proof is 6c step 6.3's four probe readings |
| [`vpn.py`](vpn.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | two profiles by default, the VPN home and Identity (the step 8 deny lives in Identity, the Elastic IP it names in the VPN home); the ones named, or `-` | `output/vpn.txt` | [Stage 4](../docs/plan/stages/stage-04-vpn.md)'s evidence. The WireGuard host (`[D]`: type, root volume size and type, state, IMDSv2; the disk needs a second call, `DescribeVolumes`, because `DescribeInstances` names the volume and not its capacity; both halves of the shape are slice parameters, so `VP-1` reports them and passes), the `[P]` Elastic IP (printed as `WG_EIP=`, the value step 8 and Stage 5's bucket policy name), the one world-open SG rule (UDP/51820 and nothing else, never port 22), the handshake log and alarm, and which permission sets carry `DenyControlPlaneOffVpn` (read through the Identity Center delegated admin; the six persona sets move together, `InfrastructureAccess` reported as the separate 8.3 decision). Checks `VP-1`–`VP-9` less `VP-8`, retired when the GuardDuty reading moved to `guardduty.py` and not renumbered, so the Stage 4 log's readings stay unambiguous. Exits 2 when a check fails |
| [`eip-transfer.py`](eip-transfer.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | two fixed profiles, `argv` ignored: the source (`awsds-infra-sandbox-1`) and the destination (`awsds-infra-prod`). Two of the four refusals are invisible from the source account, and the one that matters most fires in the destination at accept time | `output/eip-transfer.txt` | [Stage 6c](../docs/plan/stages/stage-06c-networking-hub.md) step 4.2's preflight: can the WireGuard Elastic IP move from Sandbox to Production without every client `.conf` changing? The source address field by field (allocation, association, pool, `PtrRecord`, border group), the destination's Elastic IP headroom against quota `L-0263D0A3`, and transfers already in flight on both sides. Checks `ET-1`–`ET-7` are the four documented refusals plus the seam: `InvalidTransfer.AddressAssociated` and `AddressLimitExceeded` are raised at accept time, not at enable time, so an unready transfer is discovered with a seven-day clock running and AWS notifying nobody. It prints the two write commands with the ids resolved and runs neither; 4.5's calls are authorized one at a time in chat. Exits 2 when a check fails, and exit 2 before step 4.4 is the expected reading: `ET-2` is false while the Sandbox host still holds the address |
| [`guardduty.py`](guardduty.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | every `awsds-*` profile, the ones named, or `-`; multi-profile because coverage is org-wide, and one account silently uncovered is the finding | `output/guardduty.txt` | [Stage 15](../docs/plan/stages/stage-15-guardduty.md)'s evidence. The detector per account with its status, every protection-plan feature read from the API (all arrive `ENABLED` except Runtime Monitoring, step 0, so any `ENABLED` after step 3 is drift or an unfinished switch-off), and the delegated-administrator registration visible from Identity. Section 3 names what it cannot see: the org configuration in Audit and Management's own detector (no profiles, D33/D34). Checks `GD-1`–`GD-3`; exits 2 when a check fails |
| [`datalake.py`](datalake.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: the lake and its policy live in Data Governance, every legitimate reader in a consumer account (D22), and a pending RAM invitation is visible only from the consumer | `output/datalake.txt` | [Stage 5](../docs/plan/stages/stage-05-data-foundation.md)'s evidence, producer and consumers side by side. The lake buckets with their policy branches (vpce/ip/via/sigage/prin; presence, never sufficiency), KMS aliases, the Glue catalog with resource links flagged, crawlers (never scheduled, never at an Iceberg target), the `awsds-data-catalog-maintenance` role and its trust, the Lake Formation `Parameters` reading that defends INT-11 (`DL-5`, the check to read after any apply in `data-governance/data/`), RAM shares and pending invitations, the absence of any consumer `awsds-*` workgroup or `*-derived` bucket (both removed 2026-08-26, D19 revised; `DL-8`/`DL-9` are absence checks), the absence of any EFS beyond a Studio domain's own tagged home (the NFS requirement was withdrawn 2026-08-17; conventions §5.1 rule 2 expects the domain's), Security Hub per account, and the persona's identity half of the drop-box write, read off the provisioned role in each consumer (`DL-12`; `DL-2` measures the resource half, and a cross-account permission is the AND of the two). Checks `DL-1`–`DL-12`; exits 2 when a check fails |
| [`studio.py`](studio.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: D26's claim that the domain is a registry, not a runtime, is only readable with Data Governance and the Interactive accounts side by side, and a SageMaker domain in the wrong column is the finding | `output/studio.txt` | [Stage 6](../docs/plan/stages/stage-06a-unified-studio.md)'s evidence, registry and runtimes side by side. DataZone domains visible in every account with the owner read from the ARN (one owned, V2, in Data Governance; one owned anywhere else is INT-12's fallback by accident; a shared-in row is step 1.3 working, the false `FAIL` of 2026-08-21), blueprint configurations read per member account (one in the domain account is a `US-3` `FAIL`, D22), profiles and projects (no Redshift), the blueprint-provisioned SageMaker AI domain per Interactive account (`VpcOnly`, idle shutdown), the D13 permissions boundary on the project roles (INT-15's presence half; survival is a diff of two runs), the step 3 deny Sids in the persona sets, registered images (INT-17's mechanical half), and running apps (the burn). Checks `US-1`–`US-10`; exits 2 when a check fails |
| [`rename-check.py`](rename-check.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | four profiles, the reading being the comparison between them: Organizations from Identity, the SMUS and RAM surfaces from the member itself, the lake's grants from the producer | `output/rename-check.txt` | [Stage 6b](../docs/plan/stages/stage-06b-development-becomes-staging.md)'s instrument: is the account that used to be `Development` a Workload target yet, and is anything stranded? Three readings: before (every check `note`s), after (every check passes) and mixed, which is a finding rather than a phase. `RC-3`: an account already in `Workloads` that still holds blueprint configurations cannot delete them from inside itself, because the OU denies `datazone:*`. Read it before each step of 6b and after the last one. |
| [`sandboxlake.py`](sandboxlake.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | one profile, `awsds-infra-sandbox-1`: every object Stage 16 builds (the bucket, the access role, the Access Grants instance and its grants) lives in the Sandbox account | `output/sandboxlake.txt` | [Stage 16](../docs/plan/stages/stage-16-sandbox-lake.md)'s evidence: the sandbox lake and its register. The bucket's shape (versioning, SSE-KMS under `alias/awsds-sandbox-data`, BPA, the TLS statement, no expiry on current objects), the access role's enumerated trust (a wildcard is the finding), the Access Grants location against that role, every grant on the bucket classified by shape (standing per-group, per-project, or a `FAIL` to attribute: `SL-4`; an orphaned `datazone_usr_role_*` grantee is a dead project that skipped [`runbooks/sandbox-lake.md`](../docs/plan/runbooks/sandbox-lake.md) §R; whether a well-shaped grant was authorized is a human diff against `AWS_STATE.md`, which this script does not read), and the persona's inline and attached documents read for the absence of any direct allow on the bucket (vended-only, `SL-5`; a wildcard that merely covers it is a note, never a silent pass). Checks `SL-1`–`SL-5`; exits 2 when a check fails |
| [`devenv.py`](devenv.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user) | one profile, the account folder's own (`awsds-infra-sandbox-1` by default; the argument picks another) | `output/devenv.txt` | The dev-env image's proxy contract against the account that generates it. Since [6d decision 8](../docs/plan/stages/stage-06d-unified-studio-remainder.md) the house image carries `NO_PROXY` as a literal in [`images/dev-env/Dockerfile`](../images/dev-env/Dockerfile), and the list is generated by `<account>/egress`: the copy is dated the moment it is written and a change on the generating side leaves an image that still works. `DE-1`: the Dockerfile declares one `ARG NO_PROXY_LIST`, on one line, with no whitespace inside an entry. `DE-2`: the account's list reads from the egress slice's state object (`s3:GetObject` + `kms:Decrypt`, no terraform binary and no initialised directory) - an **empty** `no_proxy` output is the session being down, reported as that and not as a divergence. `DE-3`: the two lists are equal, and the two directions are different faults - a name in the account and not in the image leaves through the proxy and **succeeds**, without `aws:SourceVpce`; a name in the image and not in the account **times out** against an absent endpoint (Lesson 42). `DE-4`: the proxy URL agrees with the repository's other copy. Exits 2 when a check fails. What it cannot see: the image a space is **running**, which may be older than the Dockerfile - section 3 prints the digest to compare with `/opt/awsds-proxy.txt` inside the space |
| [`supplychain.py`](supplychain.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: D14 puts the registries in Production and every consumer in an Interactive account, so the consumer map (Lesson 14) is read from both sides, the policies from Production and a cross-account read from each consumer | `output/supplychain.txt` | [Stage 7](../docs/plan/stages/stage-07-gitlab-runners-ecr.md)'s evidence, producer and consumers side by side. The GitLab host (`[D]`, stopped between sessions) and the runner (`[E]`, absent between sessions), the `[P]` anchors a restore depends on (buckets, the `gitlab-secrets` container, metadata only and never the value), the TLS surface (imported ACM leaves with their days of runway, since ACM does not renew imports; the one-source CA root parameter; the two zones' records), ECR repositories with tag immutability and the scanning configuration, the pull-through cache rules against their immutability trap, the CodeArtifact domain, repositories and policy, and a real cross-account read from each Interactive account (INT-01/INT-02's mechanical half). Checks `SC-1`–`SC-10`; exits 2 when a check fails |
| [`cicd.py`](cicd.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: the deploy runner lives in Production and its roles in Staging and the Interactive accounts (INT-08, INT-18), and D17's identical-runtime claim is read with the Interactive accounts side by side | `output/cicd.txt` | [Stage 8](../docs/plan/stages/stage-08-cicd-pipelines.md)'s evidence, the credential layer from every side. The deploy runner (`[E]`, absent between sessions; IMDSv2, the instance profile), its role's enumerated `AssumeRole` reach, the four deploy roles with permissions boundary and single-principal trust, the `*deploy-misuse*` alarm rules, the app-repository grant plus a real cross-account read from Staging (INT-07's mechanical half), the registered dev-env versions side by side (D17's parity), and who assumed a deploy role (CloudTrail's 90-day lookup, the record INT-08 exists for). Checks `CI-1`–`CI-8`; exits 2 when a check fails. INT-17's reconciliation-survival half is a diff of two runs |
| [`deploytargets.py`](deploytargets.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: the lake and the drop-box live in Data Governance, the only principal allowed to write them in Production (D22, D25), Staging's value is what it does not reach (D20), and the persona allows live in Identity | `output/deploytargets.txt` | [Stage 9](../docs/plan/stages/stage-09-deployment-targets.md)'s evidence, producer and targets side by side. The Production data platform (buckets, CMK, the enforced workgroup), the job role with D13's absence read from its own policies, the package groups with their resource policies (D28 item 6), the LF settings in every account that has any (`DT-5`, `DL-5`'s discipline extended), the write share with links and pending invitations (INT-03), the drop-box contract from both sides (INT-10's role-name contract), the Staging mirror plus the absence that is a control (no link to Data Governance, D20), the escape hatch (windowed trust, closed at rest, alarmed on every assumption), and the two persona sets' owed allows read through the delegated admin. Checks `DT-1`–`DT-10`; exits 2 when a check fails |
| [`orchestration.py`](orchestration.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: the workflow is authored in Development (D21) and runs in Production (D17), and the provisioned-MWAA burn is measured in every account, since the OnDemand Workflows blueprint would create a fee-bearing environment in a member account | `output/orchestration.txt` | [Stage 10](../docs/plan/stages/stage-10-orchestration-promotion.md)'s evidence, both orchestrators side by side. The MWAA Serverless workflows (status, `TriggerMode`, the cron in the YAML, the version count against the 50-version quota) and the Scheduler → Step Functions pair (`STANDARD` or it fails), the per-workflow roles (boundary, service trust, no lake reach with D13 one level up, and `NetworkConfiguration` present, the non-VPC bypass reading), the named log groups with retention (D28 item 5; an auto-created `/aws/mwaa-serverless/` group fails), the failure rules and `awsds-prod-model-approval`, recent runs (the `SCHEDULED` evidence), no provisioned MWAA environment anywhere (the burn), the definitions home, and the registry's register/approve callers (INT-04 read back as behaviour). Checks `OR-1`–`OR-8`; exits 2 when a check fails |
| [`dlp.py`](dlp.py) | [Infrastructure](../docs/ORGANIZATION.md#infrastructure-user); [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33) for `-` runs | the same multi-profile shape: the lake and drop-box live in Data Governance, the derived zone (D19; the SMUS project path since 2026-08-26) in the Interactive accounts, and the GuardDuty feature state is org-wide, where one account silently uncovered is the finding | `output/dlp.txt` | [Stage 11](../docs/plan/stages/stage-11-dlp.md)'s evidence, per account, side by side. Macie's per-account state and its delegation, the LF data cells filters under their name contract, the data-event trails (data-only, validated, scoped by `resources.ARN`, delivering into `awsds-data-logs`), the EventBridge rules, alarms and SNS topics of the exfiltration patterns, the two GuardDuty paid features (`DISABLED` before step 4, `ENABLED` everywhere after; the partial state fails in both directions), and the `DenyCloudTrailKill` Sid owed the moment the first member trail exists. Checks `DP-1`–`DP-7`; exits 2 when a check fails. Audit is outside every profile: the job history, the internal analyzer and the org configuration are read in its console or CloudShell (`audit-iam-analyser.sh` covers the analyzer half) |
| [`cloudshell/management-landing-zone-drift.sh`](cloudshell/management-landing-zone-drift.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33), no laptop path | no profile: CloudShell on Management. Takes a profile if one ever exists there | `output/cloudshell/management-landing-zone-drift.txt` | Stage 2 verification (iii): whether the Organizations resource policy of step 5.1 shows up as landing-zone drift. The `driftStatus` flag, the manifest that says what the flag compares, the operation history (an update that ran after the delegation and succeeded is the only positive evidence available without writing), and whether the document is still there and still narrowed to two statements. Sections 2-4 are suppressed outside Management and the run exits 2: from a member account both landing-zone calls succeed and return empty, so an unguarded report would state "the landing zone has never run". Section 5 answers from Identity too, because the delegation grants it. It also answers Stage 6b step 0.5b: section 2's `remediationTypes` is the account auto-enrollment switch, and the report says what each state costs. |
| [`cloudshell/management-quotas.sh`](cloudshell/management-quotas.sh) | [`AWS Control Tower Admin`](../docs/ORGANIZATION.md#aws-control-tower-admin-d33), no laptop path | no profile: CloudShell on Management. Takes a profile if one ever exists there | `output/cloudshell/management-quotas.txt` | Whether the account-cap increase has landed, the number the `Staging` vend is held on: the applied value (not the default), how much of it is spent, and any pending request. Refuses to interpret the number outside Management, where the same quota reads `0.0`. |

A profile is an *(account, permission set)* pair; the user is whoever holds the assignment for that pair
([`docs/ORGANIZATION.md`](../docs/ORGANIZATION.md), "Assignments"). Every `awsds-*` profile resolves to the
**infrastructure user**: the five `awsds-infra-*` through `sso-group-infrastructure` →
`InfrastructureAccess`, and `awsds-policy-canary` through the permanent Account Factory direct assignment
of Control Tower's `AWSAdministratorAccess` (D32). Everything runnable from this laptop is one person and
one login. Everything run with `-` is `AWS Control Tower Admin` in CloudShell: `-` exists for Management,
Log Archive and Audit, the three accounts where no persona holds an assignment by design and that standing
identity (D33, D34) is the only way in.

`org-policy-baseline.py` and `org-policies.py` walk the same tree at opposite ends of one change. The
baseline is a preflight, run before writing policy (step 7.0): it prints whole documents, the quota and the
organization's metadata, and answers what already exists that must not be duplicated. `org-policies.py` is
a check, run after every attachment and at every vend: it prints no document bodies, binds to `Sid` because
a managed document's id says nothing about its contents (Lesson 23), resolves inheritance down to each
account, and exits 2 on the statements the SCP battery cannot reach (Lesson 22). Use the first when writing
a policy and the second when verifying one.

All but the `cloudshell/` scripts are Python on the uv project at the repository root, sharing the
[`awslib`](awslib/__init__.py) package beside them. The shebang is `#!/usr/bin/env -S uv run --quiet`: uv
resolves `pyproject.toml`, pins the interpreter to `.python-version` and provides the packages, so nothing
is installed or activated beyond uv. Run any of them from anywhere; each locates the repository root
itself:

```bash
./aws/list-identities.py
```

```bash
./aws/AZs.py
```

```bash
./aws/org-trusted-access-services.py
```

```bash
./aws/org-policy-baseline.py
```

```bash
./aws/account-bpa.py
```

```bash
./aws/bedrock.py
```

```bash
./aws/org-policies.py
```

```bash
./aws/declarative-ec2.py
```

```bash
./aws/org-delegation.py
```

```bash
./aws/import-ids.py
```

```bash
./aws/tf-backends.py
```

```bash
./aws/networking.py
```

```bash
./aws/egress.py
```

```bash
./aws/vpn.py
```

```bash
./aws/eip-transfer.py
```

```bash
./aws/guardduty.py
```

```bash
./aws/datalake.py
```

```bash
./aws/studio.py
```

```bash
./aws/sandboxlake.py
```

```bash
./aws/devenv.py
```

```bash
./aws/supplychain.py
```

```bash
./aws/cicd.py
```

```bash
./aws/deploytargets.py
```

```bash
./aws/orchestration.py
```

```bash
./aws/dlp.py
```

`cloudshell/` holds the scripts with no laptop path. `management-quotas.sh` and
`management-landing-zone-drift.sh` answer only from Management, `audit-iam-analyser.sh` only from Audit,
the two accounts that hold no CLI profile by design (D33/D34). They run inside CloudShell, signed in as
`AWS Control Tower Admin` through `AWSAdministratorAccess`. CloudShell has no uv, so they are standalone
shell: no `awslib`, no environment, one self-contained file each. Upload the file (Actions → Upload file)
and run it where it lands:

```bash
bash management-quotas.sh
```

```bash
bash audit-iam-analyser.sh
```

```bash
bash management-landing-zone-drift.sh
```

In a clone they are [`cloudshell/management-quotas.sh`](cloudshell/management-quotas.sh),
[`cloudshell/audit-iam-analyser.sh`](cloudshell/audit-iam-analyser.sh) and
[`cloudshell/management-landing-zone-drift.sh`](cloudshell/management-landing-zone-drift.sh); their
reports land in `aws/output/cloudshell/`. All three refuse to interpret a result from the wrong account:
the calls do not error there, they answer with something meaningless that looks like an answer.

A Python script run in CloudShell needs the whole `aws/` folder: the `-` modes of `account-bpa.py`,
`declarative-ec2.py`, `networking.py`, `egress.py` and the `org-*` scripts import `awslib`, so the system
`python3` runs them as long as the folder is present (clone the repository, or upload it zipped and
unzip). A single `.py` file alone does not work.

They need a live SSO session. If the run stops with `cannot authenticate`:

```bash
aws sso login --sso-session awsds
```

One login covers every script here, whatever profile each declares. The login authenticates against the
access portal, the `awsds` sso-session, and the cached token is keyed by the session name, not by profile
or account: the profiles these scripts run as (`awsds-infra-*`, `awsds-policy-canary`) declare
`sso_session = awsds`. The persona and ctadmin profile families sit on sessions of their own (the roster is
[`AWS-CLI.md`](AWS-CLI.md), "Signing in") and show up as preflight-failed rows in a multi-profile run until
their session is logged in. The profile matters one step later, when a call trades the token for temporary
credentials of its account's role (`sso_account_id` + `sso_role_name`).
`aws sso login --profile awsds-infra-identity` reaches the same session and is equivalent.
[`login.py`](login.py) wraps that command and nothing else.

## `aws/output/` — the snapshots

Untracked (`.gitignore`), and regenerated, never edited. Deleting the folder loses nothing.

The rules, in the order they matter:

1. **Never copy an account id or an email address out of these files into a tracked file** — the rule the
   `secrets` folder carries ([`CLAUDE.md`](../CLAUDE.md)). A snapshot may be read freely and what it says
   may be used freely; the identifiers stay here.
2. **A snapshot is evidence, not intent.** It records what AWS answered at one instant. Why a resource
   exists belongs in [`docs/plan/decisions/`](../docs/plan/decisions/INDEX.md), what was typed to create it
   belongs in [`docs/log/`](../docs/log/INDEX.md), and neither is derivable from a listing.
3. **Check the timestamp in the header before trusting a line.** If the file predates the work being
   reasoned about, re-run the script.

Before reporting anything in a snapshot as a finding, read [`docs/AWS_STATE.md`](../docs/AWS_STATE.md): it
holds what a snapshot is expected to show (`INV-nn`), the differences already accounted for (`EXC-nn` —
the suspended `Sandbox` account at the root is not ours), and what a later stage will change anyway.
Without it, a real finding stops being distinguishable from the ones already known.

## Finding an answer in `output/list-identities.txt`

The file is sectioned and each block prints the command that produced it. Jump to the section, don't read
the file end to end.

| Question | Section |
|---|---|
| What is the **organization id**, the value `aws:PrincipalOrgID` and `aws:ResourceOrgID` take? | 2.1 — `ORG_ID`; the same value, with the enabled policy types beside it, is section 1 of `org-policy-baseline.txt` |
| What is the management account id? | 2.1 — `MGMT_ID` |
| Which policy types can be attached at all (SCP, RCP, tag, declarative)? | 2.2 — the root's `PolicyTypes`, `ENABLED` or not |
| What does the OU tree look like, and how deep is it? | 2.3 — the indented tree first, then one pair of tables per parent |
| Which OU is an account in? | 2.3 — the account appears under its parent |
| Which accounts exist, and are they `ACTIVE`? | 2.4 |
| What is the Identity Store id, and is there exactly one? | 3.1 and 3.2 — 3.2 is a hard check; the report stops there if it fails |
| Which `sso-group-*` groups exist? | 3.3 |
| Which SSO users exist? | 3.4 |
| Who is in a group? | 3.5 — one table per group |
| Which permission sets exist, and how long is a session? | 4.1 and 4.2 |
| What does a permission set actually grant — managed policies, boundary, inline policy, tags? | 4.3 |
| Who can reach which account, through which permission set? | 5.1 (full triples) and 5.2 (same rows, grouped by account) |
| Did something not answer? | 6 — every failed call, with its error |

Section 6 makes an empty block readable: a listing that returns nothing and a listing that was denied look
identical otherwise (Lesson 13, [`docs/plan/lessons.md`](../docs/plan/lessons.md)). Section 6 empty means
every `(none)` in the file is a real none.

## Finding an answer in `output/AZs.txt`

| Question | Section |
|---|---|
| Which zone ID is `us-west-2a` **in this account**? | 2 — one listing per account, or 3 for all of them at once |
| Do the accounts name the same physical datacenter the same way? | 4 — the verdict, with the differing rows printed if they do not |
| Which accounts were actually measured? | 1 — a `(failed)` row is a profile that did not authenticate |
| Is a zone something other than a plain, available AZ? | 2 — `ZoneType`, `State` and `OptInStatus` are in the per-account listing |

The file can mislead in two ways, both stated inside it. An account with **no profile** on this laptop
does not appear at all — `Staging` today, and every Sandbox until Stage 14 gives it one — so the file
is silent about it rather than reassuring. A **single** measured profile agrees with itself, and the check
reports that as *"nothing was compared"* rather than as a pass (Lesson 13).

What was decided from this measurement is [`docs/plan/architecture.md`](../docs/plan/architecture.md) §4.1
and [`docs/plan/open-questions.md`](../docs/plan/open-questions.md) item 3, not this file (rule 2).

## Finding an answer in `output/org-trusted-access-services.txt`

| Question | Section |
|---|---|
| Which services may act across every account in this organization? | 1 |
| Can Management rename a **member** account — is `account.amazonaws.com` trusted access on? | 1 — the derived line under the table, added for Stage 6b step 0.5a |
| Is the Audit account registered as the Access Analyzer delegated administrator? | 2 — the one row Stage 1b step 8.2 creates |
| Who administers GuardDuty / Security Hub / RAM / Config / Identity Center org-wide? | 3 — one row per enabled principal |
| Did something not answer? | 4 |

Section 3 is where the two registrations stop looking alike. *Trusted access* says a **service** may read
the organization and create its own service-linked roles inside member accounts; *delegated administration*
says an **account** operates that service for the whole organization. The first is the prerequisite for the
second, so a service can appear in section 1 with no row worth reading in section 3, which means it is
administered from Management — the default, not a gap. A third case,
`(no delegated administration for this service)`, is the API rejecting the question; Control Tower is one.

Section 1 is an inventory nobody in this project wrote: most of it is what Control Tower switched on when
the landing zone was installed, and a service there that no stage accounts for is a finding (Lesson 17).
The expected content is `INV-09` in [`docs/AWS_STATE.md`](../docs/AWS_STATE.md).

Both calls answer from the Identity account, measured on this script's first run, 2026-08-12, extending the
read boundary of Stage 1b step 4: a delegated administrator for *any* service may make these Organizations
reads, so the management account is needed to *change* this state and not to read it. If a run is denied,
section 4 says so and the fallback is in the script header.

## Finding an answer in `output/cloudshell/audit-iam-analyser.txt`

| Question | Section |
|---|---|
| Was this run in the account it was meant to be run in? | 1 — read it **first**; every other section is about whatever account answered |
| Which analyzers exist here, and since when? | 2 |
| Is the **zone of trust** the organization, or just this account? | 2 and 5 — the `type` column |
| Is anything suppressing findings? | 3 — archive rules; none is expected |
| What has been found, and in which account? | 4 — `resourceOwnerAccount` names the account the exposed resource is in |
| Did something not answer? | 6 |

This script and `cloudshell/management-quotas.sh` do not run from a profile. The organization analyzer
lives in **Audit** (Stage 1b step 8.2) and no project persona holds an assignment there, which
[`docs/ORGANIZATION.md`](../docs/ORGANIZATION.md) records as permanent; the only identity reaching Audit is
`AWS Control Tower Admin`, which D33/D34 keep in the console. So the run is CloudShell inside Audit, and
section 1 resolves the **account name** through Organizations rather than trusting the operator to be where
they think they are — the check the console wizard did not have on 2026-08-12, when it named the zone of
trust and never the account the analyzer was being created in (Lesson 16).

The file can mislead in two ways, both answered inside it. An empty findings table is not evidence: access
*inside* the organization is not external to an organization zone of trust, and the estate is nearly empty
until Stages 2-3, so section 4 prints a **count** rather than leaving an absent table to be read as a pass.
An `ACCOUNT`-type analyzer sitting in Audit stays `ACTIVE`, reports on one near-empty account and raises
nothing, so the `type` is a checked field and not a column (Lesson 13).

## Finding an answer in `output/org-policy-baseline.txt`

| Question | Section |
|---|---|
| What is the organization id, and is `FeatureSet` `ALL` (which RCPs require)? | 1 — `ORG_ID`, printed as a named variable because it is the value `aws:ResourceOrgID` and `aws:PrincipalOrgID` are compared against, and what `render.py` puts in place of `<ORG_ID>` |
| Which policy types may be attached at all? | 1.2 — the same reading as `list-identities.txt` 2.2, kept here so this file stands alone |
| What is an OU's **id**, its **ARN** (which `enable-control` takes), or its **full path** (which `aws:PrincipalOrgPaths` takes)? | 2 |
| What is already attached to this node, and is it AWS's or ours? | 3 — one block per node, one line per policy type |
| What is **already denied** — what should Stage 1c *not* write again? | 4 — the policy documents themselves, and the carve-outs inside them |
| Is this OU registered with Control Tower, and which controls does it already have? | 5 — **an error means unregistered**, an empty list means registered with nothing elective |
| How many policies still fit on this node, and how large may each be? | 6 |
| Did something not answer? | 7 — and *which* calls failed is the answer to Stage 1c verification (x) |

Sections 4 and 6 change what gets written, and both are read *before* the first `create-policy`. Control
Tower's mandatory controls already deny changes to CloudTrail and to the Config recorder on every
registered OU, with the service-role carve-outs that keep the landing zone able to update itself, so a
hand-written duplicate costs SCP budget and adds a second place to get those carve-outs wrong. That is
Stage 1c verification (iii).

In section 5 an error is the answer: `controltower list-enabled-controls` rejects an unregistered target
instead of returning an empty list, so the empty result and the failure mean different things and the
report keeps them apart.

## Finding an answer in `output/account-bpa.txt`

| Question | Section |
|---|---|
| Does this account have account-level S3 Block Public Access, and are all four flags set? | 3 — the verdict table; 2 for the raw answer |
| Which accounts is nobody measuring? | 4 — **read it before reading section 3 as a pass** |
| Which identity produced each row? | 1 — a `(failed)` row is a profile that did not authenticate, never a compliant one |
| How is it set, and in which order relative to the SCP? | 5 — the command, and the interlock that must not be reversed |

`NoSuchPublicAccessBlockConfiguration` is the "not set" answer, not a failure, and it is what to expect
before Stage 1c step 7.4: it is reported as `NOT SET` in sections 2 and 3 and kept out of the failure
section. **A missing account is not a passing account.** Management, Log Archive and Audit hold no project
persona, so they are read from CloudShell (`./aws/account-bpa.py -`) and recorded by hand; `Staging` and
every Sandbox beyond the first have no profile yet, and `EXC-01` is not ours. An account in neither
section 3 nor section 4 is the hole this snapshot exists to expose.

## Finding an answer in `output/org-delegation.txt`

| Question | Section |
|---|---|
| Has the Organizations **policy** delegation been created at all (Stage 2 step 5.1)? | 2 — and it has **three** states, not two |
| Is "no delegation" being confused with "the read was denied"? | 2 — they are separate states on purpose; only the first is the expected pre-5.1 answer |
| Can the delegated administrator reach a **root-attached** document? | 3 — `DEL-6`, the check that decides how much of Stage 2 exists |
| Does it reach the **nested** OU, or only a named one? | 3 — `DEL-7`; AWS excludes child OUs when a single OU is named, and this tree is depth 2 |
| Which policy types does it admit, and does it wrongly grant `Enable`/`DisablePolicyType`? | 3 — `DEL-8` and `DEL-5` |
| Is the type condition on an operator that **denies every write** — one without `IfExists`? | 3 — `DEL-8`, which reads the operator and not only the values |
| Which documents would a write have to reach, and how many are on the root? | 5 |

Section 4 is the main finding. Organizations *reads* already answer from the Identity account with **no**
policy delegation, measured in Stage 1b step 4 and 1c verification (x), so nothing that merely reads is
evidence here and a script built on `describe-policy` would return OK before *and* after step 5.1
(Lesson 13). This file decides **scope, by reading the document** (Lesson 22). The decisive test is a
*write*, named in Stage 2 step 5.0, and it is a human act on Management.

## Finding an answer in `output/import-ids.txt`

| Question | Section |
|---|---|
| What string does `terraform import` take for this object? | 5 — split by slice: 5a documents, 5b attachments, 5c the permission set, 5d the assignments |
| What are `<ORG_ID>`, `<ORG_PATH_DATA>` and `<ACCOUNT_ID_DATA>` right now? | 1 — and how Terraform is meant to derive each |
| Which policies exist, of which type, and where is each attached? | 2 |
| Which permission sets exist, and which one does Stage 2 actually import? | 3 — only `InfrastructureAccess` is marked `yes`, and that is the design |
| What must **not** be imported? | 4 — Control Tower's policies and sets, and the Account Factory direct assignments, each with the reason |

The address is a suggestion; the id is the measurement. Only the configuration knows whether a resource
is `.baseline` or `.this["awsds-org-scp-baseline"]`, and **an import into a `for_each` resource with the
wrong key does not error** — it leaves an orphan in state and a create in the plan. Import one, run
`plan`, then the rest. A manifest with a failed call in it is incomplete, not wrong, and section 6 says
so: importing from a short list leaves objects unmanaged with an empty plan, which looks like success.

## Finding an answer in `output/tf-backends.txt`

| Question | Section |
|---|---|
| Does this account have a Terraform state bucket, and is it versioned, SSE-KMS, closed, TLS-only, lifecycled? | 2 — the side-by-side table; 3 for the verdict |
| Is there already a bucket under the name the bootstrap slice is about to claim? | 2 — the per-account listing of **every** bucket, below the table |
| Does **Production** carry the second key of Stage 2 step 3.4? | 4 — the alias list; Production is the one account that should show two |
| Which accounts is nobody measuring, and which of those is correct? | 5 — **read it before reading section 3 as a pass** |
| Which identity produced each row? | 1 — a `(failed)` row is a profile that did not authenticate, never a compliant one |

"No state bucket" is the expected answer until Stage 2 steps 2 and 3 have run, so it is reported as a
`note` rather than a failure; it becomes a **regression** once that account has been bootstrapped. Bucket
names are **discovered** by matching `tfstate`, not composed from a convention: the `<env>` token for the
Identity account is not settled in any plan file, and a hardcoded guess would report a correctly-named
bucket as missing.

## Finding an answer in `output/s3-persistence.txt`

| Question | Section |
|---|---|
| What buckets exist at all, in every account this identity reaches? | 2 — nothing is filtered, and the `ORIGIN` column separates `awsds-` from what a console or a landing zone made. The `other` rows are gathered again below the table: **read those first** |
| Is anything encrypted under a key nobody can name? | 3 — `KEY` names an **alias**; `(no alias)` is a bucket whose key no later report can refer to. The account's whole alias list is printed below it |
| Can anything outside the organization reach a bucket? | 4 — five independent doors in one table (BPA, object ownership, the policy, a website, CORS), then **every bucket policy one row per statement**. `OPEN` counts `Allow` + wildcard principal + **no** condition tying the caller to an org, an account, a VPC endpoint or an address |
| What leaves this bucket without touching the network? | 5 — **replication and event notifications**: no VPC endpoint policy, no DNS allow-list and no SCP on a reader is anywhere near either. Destinations are printed in full and **judged by nobody**, because whether one is inside the organization is not derivable from a bucket ARN |
| How much is actually in there? | 6 — CloudWatch's **daily** metric, free and lagging: a bucket filled this morning still reads `-` |
| Is there storage that is not a bucket? | 7 — directory buckets, **S3 Table buckets**, access points (their **own** policy and BPA, so a bucket reading 4/4 in section 4 can still be reachable through one) and multi-region access points. None of them appears in section 2 |
| Which accounts is nobody measuring, and which of those is correct? | 10 — **read it before reading section 9 as a pass** |
| A cell says `DENIED` — is the script broken? | 11's **second** table. No: a refused per-resource read is a permission ceiling being measured, sets no exit code, and is kept apart from section 11's first table, which is the calls that should always work |

This file owns no stage contract. A state bucket without a noncurrent-version lifecycle is
`tf-backends.py`'s `BK-5`; the lake's policy branches are `datalake.py`'s; the **account**-level Block
Public Access flag is `account-bpa.py`'s, reported here in section 7 and checked nowhere. Encoding a step
list in two files is Lesson 14, so where a reading here disagrees with one of those three, **that** file is
the owner.

Two readings it cannot give, both named in section 10. `Log Archive` holds no CLI profile, so the
CloudTrail bucket — and `INV-14`'s Object Lock on it — is **not** measured here and must not be read out
of section 5. Section 4 is the **resource** half of every grant only: reach is the intersection of the
bucket policy, the caller's identity policy, the SCP above it and, for the lake, Lake Formation
(Lesson 28), so nothing here proves anyone *can* read a bucket — only who the bucket itself lets in.

## Finding an answer in `output/networking.txt`

| Question | Section |
|---|---|
| Which VPCs exist here, and which of them did **nobody in this project create**? | 2 — the DEFAULT column, plus `NT-1` in 12: every vended account carries an **Account Factory VPC** (`docs/AWS_STATE.md` §C), which is not the default VPC and not ours |
| Are both DNS attributes on (step 4.1)? | 2; checked as `NT-2` |
| Which **zone ID** is each subnet in — is a peering about to be cross-AZ? | 3, read next to `AZs.txt` |
| Does any route table reach into Staging's range (validation 2), or carry the WireGuard client range (step 6.5)? | 4, decided by `NT-3`/`NT-4` — `NT-3` excludes `local` routes on purpose, so a future Staging VPC does not fail against its own local route |
| What may Stage 5's bucket policies anchor on (INT-05)? | 5 — the gateway endpoint IDs, and only those; the interface endpoints of `egress.txt` are `[E]` and may anchor nothing (Lesson 3) |
| Are the two peerings there — and only the two? | 6, with both sides printed; `NT-6` holds the D20 half |
| Did the step 4.4 zone handshake complete, and is an authorization still pending (the 4.5 trap)? | 7, decided by `NT-8` |
| Is a flow log missing, or retaining forever? | 8; `NT-7` |
| Did somebody add a NACL rule (2.3), or open an SG to the world? | 9 — the SG listing is informational: from Stage 4 on, exactly one world-open rule is expected (UDP 51820) |
| Is the `[P]` half byte-stable across `make down`/`make up`? | the whole file **except section 11**: run, copy aside, cycle, run, `diff` with 11 cut out (the header carries the `awk`) — only the timestamp may change. Section 11 is `[E]` and moves by design; section 10 is regional and does not move with `egress/` at all |
| Does any private door exist for the SMUS portal's browser surfaces? | 10 — the regional endpoint-service catalog filtered to the SMUS families, each row read against the VPC configuration it fits; `NT-9` holds the 2026-08-24 absence as a baseline, so a door appearing is a red check pointing at the client plane's egress design (OQ 23 / Stage 11), never a silent widening |
| Which doors did this estate open, and what DNS names did they seize? | 11 — one row per `aws_vpc_endpoint` of `vpc-egress/endpoints.tf`, with a `DnsEntries` column: an unlisted subdomain of a seized name is NXDOMAIN for every VPC-resolver client, the tunnelled laptop included. `NT-10` tests it against the portal's public-required names; empty is the expected reading while `egress/` is down, and the check says vacuous rather than passing |
| Which accounts is nobody measuring? | 13 — **Staging above all**, whose "peering list is empty" deliverable is unrunnable until the vend |

## Finding an answer in `output/egress.txt`

| Question | Section |
|---|---|
| Which interface endpoints are up, in how many AZs (D9), with private DNS (8.5)? | 2; `EG-2`/`EG-3` |
| Is a NAT running, and which elastic addresses exist? | 3 |
| Does every endpoint policy name the organization (9.1), and does the S3 gateway policy carry the AWS-owned-bucket allow (9.3)? | 4; `EG-1`/`EG-4` — **presence, never sufficiency**: only the stage's no-NAT `dnf` probe shows the allow-list is complete. Account Factory endpoints are notes, not step 9 failures |
| Does each account's endpoint set match step 8's per-role list? | 5 — the matrix, read against the stage file rather than a copy here |
| What is the burn right now — did I forget `make down`? | 6 — the D12 instrument. Zero everywhere is D11 working, not an absent reading |
| What is the Studio endpoint's real service name (verification (i)), does CodeArtifact exist here (8.4), and which services can carry a policy at all? | 7 |
| Which accounts is nobody measuring? | 9 — Staging's list (8.3) is unmeasurable until the vend |

`networking.py` and `egress.py` split one stage the way the stage itself does, and the split is a cadence.
`foundation/` is `[P]` and never destroyed, so `networking.py` is run at each vend, after each Stage 3
pass, and on **both sides of a lifecycle cycle** — the diff of two runs is the stability deliverable.
`egress/` is `[E]` and dies with the session, so `egress.py` is run at the session's two ends: after
`make up` (is the set right) and after `make down` (is anything still burning, the question D12's declined
budget alerts left unasked). Both are **control-plane readings**: the stage's behavioural proofs — `dnf`
through the endpoint, `NXDOMAIN` from Staging, the probe reaching GitLab's port — belong to the stage's
throwaway probe instances, and no describe call substitutes for them (Lesson 20).

Both are readings of [`docs/NETWORK.md`](../docs/NETWORK.md), the network as built: the address plan, every
element holding an internal address, the routes, both egress paths, the VPN, DNS and its firewall, the
security groups. Read it when the question is *what is this supposed to look like*; run these two when the
question is *what does AWS report today*. A `[P]` fact that moves is re-measured here and then written
there.

## Finding an answer in `output/vpn.txt`

| Question | Section |
|---|---|
| Is the WireGuard host there, what type, and is it running or stopped ([D])? | 2 — `stopped` between sessions is D11 working, not an outage |
| What is the **Elastic IP**, the value step 8's deny and Stage 5's bucket policy name? | 3 — printed as `WG_EIP=`; also whether it is associated with the host |
| Is anything world-open besides the home's UDP/51820 — in **any** account, port 22 included? | 3, decided by `VP-3` (every `awsds-infra-*` account since 6c 6.5) |
| Is the handshake log shipping, and does the health alarm exist (step 7)? | 4 |
| Which permission sets carry **`DenyControlPlaneOffVpn`** — did the 8.2 rollout reach all six, and has the deliberate 8.3 diff been applied to `InfrastructureAccess`? | 5, decided by `VP-7` — a partial rollout fails (Lesson 14) |

`vpn.txt` ends at section 7 and reads nothing GuardDuty; those questions are in `output/guardduty.txt`.

## Finding an answer in `output/guardduty.txt`

| Question | Section |
|---|---|
| Is the delegated administrator registered, and is it Audit? | 2, decided by `GD-1` — the registration line is printed below the table |
| Is GuardDuty enabled in every measured account? | 2, decided by `GD-2` — up to 24 h of auto-enable propagation is the one excused window |
| Is every optional protection plan off — S3/Malware Protection included? | 2, decided by `GD-3`; red between Stage 15 steps 1 and 3 is the stage in progress, the same red a week later is drift |
| Which accounts is nobody measuring? | 3 — GuardDuty's org configuration in Audit above all, then Management's own detector |

## Finding an answer in `output/datalake.txt`

| Question | Section |
|---|---|
| Do the lake buckets exist with versioning, SSE-KMS and Bucket Keys? | 2, decided by `DL-1` |
| Does each bucket policy carry the three step 1.3 branches and the two guards? | 2 — the `BRANCHES` column; `DL-2` (presence, never sufficiency) |
| Did an apply reset `CROSS_ACCOUNT_VERSION`/`SET_CONTEXT` — the silent INT-11 failure? | 6 and 7, decided by **`DL-5`**, per account — read it after *every* apply that touches a `DataLakeSettings`, in whichever account that is. Both consumers were measured carrying `4/TRUE` of their own, so the hazard is symmetric and the values written into `parameters` come from *that* account's reading |
| Are the IAM-fallback defaults still granting `IAMAllowedPrincipals` (step 5.2)? | 6 and 7, decided by `DL-6` **per account**. In Data Governance the check is guarded on databases existing; in a consumer it is not, because the defaults act at *creation* time and the first local object is the resource link, so the reading is only actionable *before* it |
| Does the maintenance role exist under its exact contracted name, trusting only Glue? | 5, decided by `DL-4` |
| Is a crawler scheduled, or pointed at an Iceberg table — both forbidden (D27)? | 4, decided by `DL-3` |
| Did the shares arrive as resource links, with **no pending RAM invitation**? | 7 and 4, decided by `DL-7` — a `PENDING` row is INT-11's fallback tax. Section 7's tables are read together: a share this side owns that no consumer *holds* is the silent failure; a share both sides show with an empty consumer catalog is normal, because AWS needs a **data lake administrator in the consumer account** before a shared resource is visible there — the admin count is the third table, and a zero explains the emptiness by itself |
| Is the consumer workgroup actually enforcing its result location and scan limit (D19)? | 8, decided by `DL-8` |
| Is the removed derived zone staying removed, and is the VPN home still EFS-free beyond a Studio domain's own home? | 9 and 10, decided by `DL-9`/`DL-10`, both absence checks |
| Is Security Hub on everywhere, with FSBP? | 11, decided by `DL-11` |
| Does the persona hold the **identity** half of the drop-box write, or only the bucket policy? | 12, decided by `DL-12`. It reads the **provisioned role** in each consumer, not the permission set: a set lives in Identity and *becomes* a role in every account it reaches. `DL-2` is the other half, and neither answers alone |
| Which accounts is nobody measuring? | 13 — Staging is absent by design (D20), Production joins at Stage 9 |

## Finding an answer in `output/studio.txt`

| Question | Section |
|---|---|
| Does the unified domain exist — exactly one, V2, **in Data Governance**? | 2, decided by `US-1` |
| Is a domain **owned** by any account but Data Governance — INT-12's fallback by accident, or the 1c root deny not holding? (a shared-in row is step 1.3 working — the owner is read from the ARN, never from who is asking) | 2, decided by `US-2` |
| Is anything **SageMaker-shaped** running in Data Governance — the registry/runtime split (step 0's second preflight)? | 4, decided by `US-2` |
| Which blueprints are configured — is any **Redshift-backed**, and is any **outside decision 5's category 1**? | 3, decided by `US-3`, read per account and split in sign: **zero** configurations in the domain account is the pass (one there is the finding, D22 puts no compute there), while in each member account two questions apply with two different messages: the Redshift family (`RedshiftServerless`, and `LakehouseCatalog` — RMS-backed, decision 4) reopens D26/D12, and anything else off the allow-list amends Stage 6 decision 5. The categories are [`docs/SMUS.md`](../docs/SMUS.md) |
| Do the `experimentation` and `engineering` project profiles exist? | 3, decided by `US-4` |
| Is every Interactive SageMaker AI domain **VpcOnly**, with idle shutdown ENABLED? | 4, decided by `US-5`/`US-7` |
| Does any deployment target carry a domain (D28)? | 4, decided by `US-6` |
| Do the blueprint-provisioned project roles carry the **D13 boundary** (INT-15's presence half)? | 6, decided by `US-8` — survival is a `diff` of two runs either side of a reconciliation |
| Do all six persona sets carry the step 3 deny Sids together? | 7, decided by `US-9` |
| Is an app still running — did `make down` leave a burn? | 5, `US-10` — the same reading `scripts/down-studio-apps.py` makes per env |
| What image registrations exist (INT-17's mechanical half)? | 5 |
| Which accounts is nobody measuring? | 9 — Staging until the vend; every Sandbox beyond unit 1 until Stage 14 |

## Finding an answer in `output/sandboxlake.txt`

| Question | Section |
|---|---|
| Does the lake bucket exist with the Stage 16 shape — and is nothing expiring current objects? | 2, decided by `SL-1` |
| Does the access role's trust admit only the Access Grants service plus enumerated project roles? | 3, decided by `SL-2` |
| Is the bucket registered as an Access Grants location, vending the access role? | 4, decided by `SL-3` |
| Does every grant on the bucket classify by shape, and is any grantee a dead project's role (runbook §R owed)? The authorized-or-not half is a human diff against `AWS_STATE.md` | 4 (the classified table), decided by `SL-4` |
| Does the persona still hold NO direct allow on the bucket (vended-only), inline and attached documents both? | 5 (the roster) and 6, decided by `SL-5` — wildcard coverage surfaces as a note |
| Which project roles exist right now (the orphan reading's roster)? | 5 |

## Finding an answer in `output/supplychain.txt`

| Question | Section |
|---|---|
| Is the GitLab host there, what type, and is it running or stopped ([D])? | 2 — `stopped` between sessions is D11 working, not an outage |
| Is a runner still up — did `make down` leave a burn? | 2, `SC-10` — absent between sessions is the design |
| Did port 22 or any world-open rule reach the host's SGs? | 2, decided by `SC-2` |
| Do the `[P]` anchors exist — the versioned backup bucket, the `gitlab-secrets` container? | 3, decided by `SC-3` — **metadata only; this file never reads a secret value** |
| How many days of runway does an imported leaf have (ACM does not renew imports)? | 4, decided by `SC-8` |
| Is the CA root published at its one source (INT-19, Lesson 14)? | 4, decided by `SC-9` |
| Do `gitlab.awsds.internal` and `*.awsds-pages.internal` resolve to records at all? | 4 |
| Are the two required repositories tag-**immutable** — the Stage 8 premise? | 5, decided by `SC-4` |
| Is a pull-through cache repository immutable (the documented trap)? | 5, decided by `SC-5` |
| Is scanning BASIC (decision 2's free path) or ENHANCED (the Stage 11 upgrade)? | 5 — reported, not judged |
| Does CodeArtifact hold the domain, `pypi` + `crates`, and a domain policy? | 6, decided by `SC-6` |
| Does the cross-account read answer from every consumer, or did the D35 map miss one? | 7, decided by `SC-7` — a deny after the registry exists fails |
| Which accounts is nobody measuring? | 9 — Staging is deliberately **not** in the consumer map (INT-07 is the pipeline's path) |

## Finding an answer in `output/cicd.txt`

| Question | Section |
|---|---|
| Is a deploy runner up — did `make down` leave a burn? | 2 — absent between sessions is the design; IMDSv2 and the instance profile are checked by `CI-1` |
| May the runner's role assume anything beyond the enumerated `awsds-deploy-*` list? | 2, decided by `CI-4` — a `*`, a wildcard account or a foreign ARN fails |
| Do the four deploy roles exist, each with a **permissions boundary**? | 3, decided by `CI-2` — Staging's row appears only after the vend |
| Does every trust policy admit **only the deploy runner**, only `sts:AssumeRole`? | 3, decided by `CI-3` (INT-08/INT-18's contract) |
| Are the `*deploy-misuse*` alarm rules present and ENABLED (step 4.6)? | 4, decided by `CI-7` |
| Can Staging pull the application image — is the 3.0 grant in place (INT-07)? | 5, decided by `CI-5` — policy from Production, a real read from Staging |
| Is the same dev-env base image registered in every Interactive account (D17)? | 6, decided by `CI-6` — one lagging row is a 1.6 registration that failed quietly |
| Who assumed a deploy role, and was it ever not the runner (INT-08)? | 7, decided by `CI-8` — the after-the-fact twin of 4.6's alarm |
| Did a registration survive a blueprint reconciliation (INT-17)? | a **diff of two runs** — one run cannot answer it |
| Which accounts is nobody measuring? | 9 — Staging until the vend; every Sandbox beyond unit 1 until Stage 14 |

## Finding an answer in `output/deploytargets.txt`

| Question | Section |
|---|---|
| Do the two buckets carry the perimeter branches, and do results expire? | 2, decided by `DT-1` |
| Is the workgroup actually enforcing its result location and scan limit (D19)? | 2, decided by `DT-2` |
| Does every `awsds-prod-model-*` group carry its resource policy (D28 item 6)? | 3, decided by `DT-3` |
| Does the job role reach a lake bucket through plain S3 — D13's absence, read from its own policies? | 3, decided by `DT-4` |
| Did an apply reset the LF `Parameters` anywhere — the silent INT-11 failure, in any account? | 4, decided by **`DT-5`** — read it after *every* `DataLakeSettings` apply |
| Did the write share arrive, with **no pending RAM invitation** (INT-03, INT-11's tax)? | 5, decided by `DT-6` |
| Do the drop-box statement **and** its key name exactly `awsds-prod-job-exec` (the Stage 5 contract, INT-10)? | 6, decided by `DT-7` |
| Is Staging linked to Data Governance — the absence that is the control (D20)? | 7, decided by `DT-8` |
| Does the Staging mirror agree with the lake's catalog, table by table? | 7, decided by `DT-8` |
| Is the escape hatch closed at rest, capped at 1 h, alarmed on **every** assumption? | 8, decided by `DT-9` |
| Did the persona sets gain their owed allows — and the Staging set **nothing** (Lesson 22)? | 9, decided by `DT-10` |
| Which accounts is nobody measuring? | 11 — Staging until the vend; Development appears only as a principal in the group policies |

## Finding an answer in `output/orchestration.txt`

| Question | Section |
|---|---|
| Are both implementations whole — A `READY`, B a `STANDARD` machine **with** its schedule? | 2-3, decided by `OR-1` — a machine without a schedule, or the reverse, fails |
| What is each workflow's schedule and pause state — the cron from the YAML, `TriggerMode`, B's `state`? | 2-3 — the pause lever verification (v) toggles |
| Does every workflow/machine log to a **named** group with retention — and did an auto-created `/aws/mwaa-serverless/` group appear? | 5, decided by `OR-2` (D28 item 5) |
| Do the per-workflow roles carry a boundary, service-only trust, **no lake reach** — and is A's `NetworkConfiguration` set (the non-VPC bypass)? | 4, decided by `OR-3` |
| Are the `*-failed` rules and `awsds-prod-model-approval` present and ENABLED? | 6, decided by `OR-4` |
| Did a `SCHEDULED` run fire — the unattended evidence of verification (v)? | 7 — reported; the proof is the stage's own |
| Is a provisioned MWAA environment burning anywhere (0.29 USD/h each)? | 8, decided by `OR-6` — step 4's fallback is same-sitting `[E]` |
| Did the service-linked role appear at the first `CreateWorkflow` (Lesson 17, steps 0.3/1.5)? | 9 — reported both ways, absent is the pre-stage baseline |
| Are the definitions under `s3://awsds-prod-outputs/workflows/` (decision 1)? | 9, decided by `OR-5` |
| How many workflow versions exist against the 50-version quota (risk 4)? | 2, decided by `OR-7` |
| Was every registry write `awsds-deploy-prod` (INT-04, Stage 9 3.2 read as behaviour)? | 10, decided by `OR-8` |
| Which accounts is nobody measuring? | 13 — Staging until the vend; the Studio surface is console-recorded |

## `sandboxlake.py`, written for Stage 16

`sandboxlake.py` was written 2026-08-26, at the stage's creation. Until the stage runs, the bucket and role
rows read `note`; the Access Grants sections read whatever the SMUS-born instance already holds, the
baseline its pass 0 records. Its contracts: the bucket name (`awsds-sandbox-lake`), the access role
(`awsds-sandbox-lake-access`), the key alias (`alias/awsds-sandbox-data`, decision 1's recommendation, so a
different key fails rather than passing silently) and the two grantee classes (`AWSReservedSSO_*`,
`datazone_usr_role_*`). Two of its checks are halves: `SL-1`'s policy reading is presence, never
sufficiency, and the behavioural proofs — the in-project read/write through the S3 connection, the
`s3-read-write` vend, the two refusals — are the stage's own (Lesson 20).

## `orchestration.py`, written for Stage 10

`orchestration.py` was written 2026-08-16, from the
[Stage 10](../docs/plan/stages/stage-10-orchestration-promotion.md) roteiro, before the stage runs. Until
it runs, every absent resource reads as a `note`; a *partial* build fails loudly. Its contracts: the
`awsds-prod-wf-` name fragment (workflows, machines, schedules, roles, failure rules), the two log prefixes
(`/awsds/prod/wf/` for A, `/aws/vendedlogs/states/awsds-prod-wf-` for B — the documented vended-logs
prefix, load-bearing against the ten-resource-policy quota), the definitions home
(`awsds-prod-outputs/workflows/`) and the approval rule (`awsds-prod-model-approval`). Three of its checks
are halves: `OR-1` shows the resources exist, while whether the `awscc` apply *lands under the deploy
role's boundary* (INT-14) is pass 2's pipeline run; section 7 shows run rows, while the *unattended*
`SCHEDULED` proof is the stage's own; and `OR-8` reads the registry record after the fact, the preventive
half being Stage 9 3.2's policy, which `deploytargets.py` `DT-3` owns.

## `deploytargets.py`, written for Stage 9

`deploytargets.py` was written 2026-08-16, from the
[Stage 9](../docs/plan/stages/stage-09-deployment-targets.md) roteiro, before the stage runs. Until it
runs, every absent resource reads as a `note`; a *partial* build fails loudly. Its contracts: the job role
(**`awsds-prod-job-exec`**, the same name Stage 5's drop-box statement and key grant carry), the workgroups
(`awsds-prod-athena`, `awsds-staging-athena`), the buckets (`awsds-prod-outputs`,
`awsds-prod-athena-results`), the package-group prefix (`awsds-prod-model-`), and the debug pair
(`awsds-prod-debug`, rule `*debug-assume*`). Two of its checks are halves: `DT-6` shows the write share was
*granted*, while whether an LF-aware cross-account Iceberg write *lands* is step 2.4's job run (INT-03's
least-travelled variant); and `DT-4` reads D13's absence from the role's policies, while the behavioural
converse (the direct `PutObject` dying) is the same step's pair.

## `cicd.py`, written for Stage 8

`cicd.py` was written 2026-08-16, from the [Stage 8](../docs/plan/stages/stage-08-cicd-pipelines.md)
roteiro, before the stage runs. Until it runs, every absent resource reads as a `note`; a *partial* build
fails loudly. Its contracts: the deploy runner name (`awsds-prod-runner-deploy`, instance and role), the
four deploy-role names (`awsds-deploy-staging`, `awsds-deploy-prod`, `awsds-deploy-devenv-sandbox`,
`awsds-deploy-devenv-dev`), the alarm-rule fragment (`deploy-misuse`), the application repository
(`awsds-prod-ecr-app-etl`). Its first run measured a clean pre-stage state — nothing
deploy-credential-shaped anywhere, every reading a `note`, zero failures — the baseline the pass-1 apply
will be diffed against. Two of its checks are halves: `CI-5`'s behavioural proof is a real promotion's pull
(3.2), and `CI-6` reads parity, not whether the registration *survives reconciliation*, which is a diff of
two runs (INT-17).

## `supplychain.py`, written for Stage 7

`supplychain.py` was written 2026-08-16, from the
[Stage 7](../docs/plan/stages/stage-07-gitlab-runners-ecr.md) roteiro, before the stage runs. Until it
runs, every absent resource reads as a `note`; a *partial* build fails loudly. Its contracts: the two Name
tags (`awsds-prod-gitlab`, `awsds-prod-runner*`), the two required repositories (`awsds-prod-ecr-base`,
`awsds-prod-ecr-dev-env`), the CodeArtifact domain (`awsds-prod-packages`, repos `pypi`/`crates`), the
secret container (`awsds-prod-gitlab-secrets`) and the CA root parameter
(`/datascience/prod/pki/ca-root-pem`). Its first run measured a clean pre-stage state: nothing
supply-chain-shaped existed in Production, every reading a `note`, zero failures — the baseline the
pass-0 apply was diffed against. That apply happened on 2026-08-21 (Stage 6 pass 0, Stage 7 step 5.a):
both ECR repositories and the CodeArtifact domain with its two repositories now exist, so `SC-4` and
`SC-6` read `pass` while the two GitLab rows and the CA-root row still read `note` — Stage 7's remaining
half, not a regression. `SC-7` is one-sided: it exercises the consumer map with a **real cross-account
read** from each Interactive profile, because a policy listing in Production cannot show a missing
consumer (Lesson 13).

## `eip-transfer.py`, written for Stage 6c step 4.2

`eip-transfer.py` was written 2026-09-06, at
[Stage 6c](../docs/plan/stages/stage-06c-networking-hub.md) step 4.2, the only script here written for one
act rather than for a stage's standing evidence. An Elastic IP transfer has four documented refusals, and
**two of them are raised in the destination account at accept time**, after `enable-address-transfer` has
already succeeded and a **seven-day** clock is running that AWS notifies nobody about. The failure mode is
a call that succeeded with the wrong thing now pending in another account, which no single-account
`describe-addresses` can predict and no error message will volunteer. Its first run, before step 4.4, read
six of seven passing with `ET-2` red because the Sandbox host still held the address: the expected reading,
stated in its own header, and which row is red separates *not yet* from *never* (Lesson 50). It survives
the stage as the instrument for any later address move; an Elastic IP is `[P]` because it outlives the
accounts it sits in.

## `vpn.py` and `datalake.py`, written for Stages 4 and 5

Both were written 2026-08-16, from the [Stage 4](../docs/plan/stages/stage-04-vpn.md) and
[Stage 5](../docs/plan/stages/stage-05-data-foundation.md) roteiros, before either stage runs. Until each
stage runs, every absent resource reads as a `note` ("expected before Stage N step M"), so today's clean
state passes and a *partial* build fails loudly. Their first run measured what `DL-5` exists to defend:
Data Governance answers `CROSS_ACCOUNT_VERSION=4, SET_CONTEXT=TRUE` with no admins declared — the INT-11
state Stage 5 step 5.4 must carry through its first apply — and confirmed the `IAMAllowedPrincipals`
create-defaults are still in place, which step 5.2 removes. Each script names its contracts (the
`awsds-*-vpn` Name tag, the `DenyControlPlaneOffVpn` Sid, the `awsds-data-catalog-maintenance` role name)
so a rename fails in a check rather than in a stage.

## `studio.py`, written for Stage 6

`studio.py` was written 2026-08-16, from the [Stage 6](../docs/plan/stages/stage-06a-unified-studio.md)
roteiro, before the stage runs. Until it runs, every absent resource reads as a `note`; a *partial* build
fails loudly. Its contracts: the two project-profile names (`experimentation`, `engineering`), the two
step 3 Sids (`DenySageMakerJobsOffVpc`, `DenySageMakerInstanceCeiling`) and the `project-boundary` name
fragment. Two of its checks are halves: `US-8` reads the boundary's *presence*, never whether it survives a
blueprint reconciliation (INT-15's behavioural half is a diff of two runs), and `US-2`'s registry reading
cannot exercise the SCP carve-out (step 0's probe is a write, and it is the user's). Its first run measured
two things: Data Governance holds nothing SageMaker-shaped (`US-2` pass, step 0.4's premise), and
`datazone:ListDomains` from Production is denied naming the Workloads document — D28's headless ceiling
holding, which the script reads as a pass, not a failed call.

## The scripts written for Stage 2

`org-delegation.py`, `import-ids.py`, `tf-backends.py` and `cloudshell/management-quotas.sh` were written
2026-08-15. [Stage 2](../docs/plan/stages/stage-02-terraform-foundation.md) is the first stage that has to
**feed an AWS-generated identifier back into a command** rather than read it. A snapshot tolerates a stale
line because a human reads it and notices; an import id is pasted into a state file, and a wrong one
produces an orphan and a create rather than an error. So each of the three Python scripts names what it is
*not* authoritative about: `import-ids.py` owns the id and not the Terraform address, `org-delegation.py`
owns the delegation's scope and not whether a write will land, `tf-backends.py` owns what is there and not
what should be.

`org-policies.py` §1 listed ids for `SERVICE_CONTROL_POLICY` only and reduced the RCP to a presence check,
so three of the ten attached documents had no id in any snapshot and existed only in the 1c log. All four
types now carry theirs.

## `networking.py` and `egress.py`, written for Stage 3

Both were written 2026-08-15, from the [Stage 3](../docs/plan/stages/stage-03-networking.md) roteiro before
the stage starts, because the stage's own validations are the kind of reading that otherwise gets done
once, in one console tab, per account. Their first run measured something no plan file had: every vended
account carries an **Account Factory VPC** with an S3 gateway endpoint on the default full-access policy,
recorded in [`docs/AWS_STATE.md`](../docs/AWS_STATE.md) §C and decided in Stage 3. Both scripts report
those artifacts as `note` rows tied to that decision, so today's known state reads clean and a *new*
deviation still fails loudly.

## Adding a script here

Keep the shape, so that one file explains all of them:

- **Read-only.** A script that changes something does not belong in `aws/`.
- **Build on [`awslib`](awslib/__init__.py)**, the package beside the scripts: `context` (repo root, output
  dir, the CloudShell fallback), `awscli` (the CLI as a subprocess, with `run`'s capture/tolerate
  semantics), `report` (sections, `column -t` tables, the failed-calls log), `profiles` (discovery and the
  preflight). The scripts shell out to the `aws` CLI rather than using an SDK: the report prints the exact
  command above each block, and the battery reads the CLI's error wording. `awslib` must stay
  standard-library-only and must import nothing from outside `aws/`, or the CloudShell fallback dies.
  [`cloudshell/`](cloudshell/management-quotas.sh) is the exception: its scripts run where neither uv nor
  the repository may exist, so they stay standalone shell — one self-contained file each, no `awslib`,
  uploadable alone.
- **One profile per script**, named at the top, with the reason that profile can see what it sees, and
  **name the SSO user behind it in the table above**: a profile is an *(account, permission set)* pair and
  the user is a second fact. `AZs.py`, `account-bpa.py` and `declarative-ec2.py` are the exceptions,
  because in all three the subject is a *per-account* fact whose meaning is the comparison **between**
  accounts — an AZ name→ID mapping is only interesting next to another account's, and a setting that is
  right in five accounts and unset in the sixth is the sixth account's hole. All three print the caller ARN
  of every profile in section 1. Multi-profile is for a script whose subject is the difference between
  accounts.
- **Output to `aws/output/<script-name>.txt`**, one file per script (`awslib.context` creates the folder).
- **Print the command above its output** (`Report.show`) so any line can be re-derived by hand, and prefer
  `--output table` over post-processing.
- **Print reused identifiers as `NAME=value` lines** (`MGMT_ID`, `ROOT_ID`, `IDS`, `INST`) where they are
  resolved, so a reader can re-run any later command by hand.
- **Log every failed call into a final section** rather than letting it read as an empty result.
- **Number the sections** and list them in the header, then add the row to the table above and to the
  question table.

---

*Project root: [`README.md`](../README.md) · CLI recipes run by hand: [`aws/AWS-CLI.md`](AWS-CLI.md) ·
What was done by hand: [`docs/log/INDEX.md`](../docs/log/INDEX.md)*
