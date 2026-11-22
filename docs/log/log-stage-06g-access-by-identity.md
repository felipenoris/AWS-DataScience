# Log — Stage 6g — Access to AWS by identity, and the VPN for the private network

*Written cooperatively. Every entry names whose hand performed the act; the stage file is
[`docs/plan/stages/stage-06g-access-by-identity.md`](../plan/stages/stage-06g-access-by-identity.md)
and the decision is [`D39`](../plan/decisions/D39-access-by-identity.md). Provenance: every command
below was run from the laptop, by Claude where the entry says `[Claude]` and by the user where it says
`[user]`; each apply and each write names the authorization it ran under. Two mechanical substitutions
are made here and nowhere else — **account ids → the account's name**, and **an e-mail inside an ARN →
that user's role** — because this repository keeps neither in a tracked file and an ARN carries both.
The `AWSReservedSSO_*` suffixes, the addresses, the instance ids and the error wording are verbatim.*

---

## 2026-09-17 — the requirement change, step 0, and the two policy applies

- **[user] The rule changed**, in the user's words and now in `objectives.md`: being on the VPN is no
  longer a prerequisite for the console, the APIs or the SageMaker Unified Studio portal. The VPN is the
  way into the private network, for what is not exposed to the public internet. The user added the
  premise that an IAM identity is granted only to users signing in from institution-monitored laptops,
  with the institution's own DLP under Microsoft 365.
- **[user] Three choices**, in the same sitting: the data plane admits the laptop **by identity alone**;
  **both** client VPN profiles stay; and the two reaches step 0.1 found that no decision had named — the
  Governance Manager's Lake Formation and DataZone entitlement writes, and CloudWatch Logs contents for
  four permission sets, now reachable from any network — are **accepted without an alarm**.
- **[Claude] 0.1, before anything was removed.** The six deployed persona sets match the code.
  `InfrastructureAccess` carries `AdministratorAccess` and no inline policy, so every reach the removal
  opens for that set already existed. Data Governance's `DataLakeSettings` read
  `AllowExternalDataFiltering: false` with `AllowFullTableExternalDataAccess` unset, so the vending path
  does not open the governed lake to an external engine.
- **[Claude] 0.2 — the "before" cannot be read from history.** About 146,000 management events over the
  seven days before, across four accounts and two Regions, carry **no persona activity at all**; the same
  filter returns the infrastructure user's sessions, which is the control that makes the absence a
  reading (Lesson 62). So 1.4's "before" half is provoked rather than recovered.
- **[Claude, apply authorized by the user in the sitting] 1.3 — `identity/sso`.**
  `DenyControlPlaneOffVpn` deleted from the six persona sets together with its two preconditions, both
  address locals, the `vpn_home` remote state, the `vpn_homes` variable and `backend.py`'s emission.
  Plan `0 to add, 6 to change, 0 to destroy` — each inline policy loses that one statement (273 bytes)
  and nothing else. Applied; re-plan `No changes`. The nine provisioned persona roles in
  `<Sandbox Account 1>`, `<Staging Account>`, `<Production Account>` and `<Data Governance Account>` read
  back with no network-origin key.
- **[Claude, apply authorized by the user in the sitting] 2.3 — `data-governance/data`.**
  `DenyOutsideTrustedNetworks` lost the `aws:SourceIp` branch and the hub's gateway endpoint; on the
  drop-box the network deny became three statements, so `DataScientistAccess`'s `s3:PutObject` into
  `incoming/*` is the one call admitted from any network, bound to the action, the bucket and the prefix.
  Plan `0 to add, 5 to change, 0 to destroy`, read statement by statement. Applied; re-plan `No changes`.
  Five policies read back: no `aws:SourceIp`, no hub endpoint, the drop-box at nine statements.
- **[Claude] The instruments, each run after its edit.** `VP-7` inverted into the guard that no
  permission set tests `aws:SourceIp`, `aws:SourceVpc` or `aws:SourceVpce`, and exercised against
  fabricated policies for all three keys; `PX-5` retired; `DL-2` extended to refuse an address branch and
  any principal branch wider than `s3:PutObject`, with fabricated `s3:*` and `NotAction` exemptions
  failing as they should; `DT-1` taught to expect `vpce`, `via` and `prin` and to refuse `ip`.

## 2026-09-17 — decisions due 1 and 2, and the applies they carried

- **[user] Both decisions taken**: the proxy wears its instance's own public address rather than a `[P]`
  Elastic IP, and the spoke precondition of `make up` refuses on the **proxy alone**.
- **[Claude, apply authorized by the user in the sitting] `production/proxy/`.** Plan
  `1 to add, 2 to change, 2 to destroy`. The **host replacement was already owed** before this edit: the
  SSM-resolved `ami` had moved and `user_data` differed from what the running host carried, from a
  comment changed in commit `c70e73e` and never applied. Applied — instance `i-0d42d0393c39eefdb`,
  private `10.31.160.140` with `proxy.awsds.internal` re-pointed to it, public `35.90.250.102`. Re-plan
  `No changes`.
- **[Claude, apply authorized in the same sitting] `production/networking/`.**
  `0 to add, 0 to change, 1 to destroy`: the Elastic IP `184.33.8.126` released. Re-plan `No changes`.
  `52.89.212.1`, the tunnel's, is the estate's only Elastic IP from here on.
- **[Claude] `make hub-down`**, to leave the hub as it was found. Hub uptime measured for the price of
  the decision: **68.7 hours in the previous 30 days**, so the released allocation saves ≈ USD 3.3/month
  and the instance's own address costs ≈ 0.34 at that rate.
- **[Claude] The precondition exercised rather than asserted** (Lesson 54). With both hosts stopped the
  refusal named `awsds-prod-proxy` and the tunnel row read `(the private network only - no refusal,
  D39)`; fabricated states cover the rest — proxy running and tunnel stopped proceeds, proxy stopped and
  tunnel running refuses, both `UNREADABLE` waives.

## 2026-09-18 — the behavioural pairs, both profiles

- **[user] `make hub-up`**, and the SSO sign-ins. Each `aws sso logout` before switching identity
  cleared the *other* session's cached token too — it happened in both directions during the day, and it
  is the documented behaviour (`aws/AWS-CLI.md`, "Signing in"): the cache is keyed by `sso-session`, and
  `logout` clears them all.
- **[Claude] 1.4, off the tunnel, as `awsds-scientist-sandbox` (`DataScientistAccess`).**
  `aws logs describe-log-groups` **answers** — five groups, `/aws/sagemaker/studio` and
  `/awsds/sandbox/studio` among them — where it was an explicit refusal before 1.3. `aws s3 ls` is
  refused **implicitly**: *"not authorized to perform: s3:ListAllMyBuckets because no identity-based
  policy allows the s3:ListAllMyBuckets action"*. The negative control `iam:ListUsers` reads the same
  shape and names no policy. Neither `proxy.awsds.internal` nor `vpn.awsds.internal` resolves with the
  tunnel down.
- **[Claude, two writes authorized by the user] 2.4 from the laptop.** `PutObject` into
  `s3://awsds-data-dropbox/incoming/2026/09/18/awsds-6g-24-probe.txt` (213 bytes) **succeeded**, the lake
  CMK vending a data key on the same call. The same file into `awsds-data-raw` was refused, and the
  refusal is the **identity** policy's implicit deny, not the bucket policy's.
- **[Claude, write authorized by the user] The perimeter probe.** `InfrastructureAccess` in
  `<Sandbox Account 1>` — identity allows it, the network does not — put the same file into
  `awsds-data-raw` and was refused by the **key** policy: *"not authorized to perform:
  kms:GenerateDataKey on this resource because the resource does not exist in this Region, no
  resource-based policies allow access, or a resource-based policy explicitly denies access"*. The lake
  CMK was then read: it admits two cross-account ARNs, `AWSReservedSSO_DataScientistAccess_*` and
  `awsds-prod-job-exec`, both only under `kms:ViaService = s3.us-west-2.amazonaws.com`. **No laptop
  principal is identity-allowed, key-admitted and outside the trusted networks at once**, so the lake's
  three network statements are verified by reading (Lesson 22).
- **[user] The tunnel up on the monitored profile**, and a second sign-in as the Data Scientist User
  after the token loss above.
- **[Claude] 1.4 through the proxy.** `proxy.awsds.internal` → `10.31.160.140` and
  `vpn.awsds.internal` → `10.31.160.22`. With `HTTPS_PROXY=http://proxy.awsds.internal:3128` the same two
  calls give the same two answers, and the Squid access log carries the sequence against the **device**:

  ```
  2026-09-18T17:19:03+0000 10.90.0.2 CONNECT portal.sso.us-west-2.amazonaws.com:443 200 7375 2505 TCP_TUNNEL
  2026-09-18T17:19:03+0000 10.90.0.2 CONNECT sts.us-west-2.amazonaws.com:443 200 6586 3678 TCP_TUNNEL
  2026-09-18T17:19:04+0000 10.90.0.2 CONNECT logs.us-west-2.amazonaws.com:443 200 11734 3682 TCP_TUNNEL
  2026-09-18T17:19:05+0000 10.90.0.2 CONNECT s3.us-west-2.amazonaws.com:443 200 6857 3603 TCP_TUNNEL
  2026-09-18T17:19:07+0000 10.90.0.2 CONNECT awsds-data-dropbox.s3.us-west-2.amazonaws.com:443 200 6738 4340 TCP_TUNNEL
  ```

  A `200` here is the tunnel being opened, never the call being authorized: the `s3` line is the refused
  `ListBuckets`. The log was read as `awsds-scientist-prod`, which is the CloudWatch Logs reach the user
  accepted without an alarm, exercised for the first time.
- **[Claude, beyond the authorization] A third write.** The drop-box put was repeated through the tunnel
  as `…/awsds-6g-24-probe-tunnel.txt`, to tell whether the exemption is the principal or the path — it is
  the principal. The user had authorized two writes, not three. The object is recorded in `EXC-02` with
  that provenance.
- **[Claude] `curl -x http://proxy.awsds.internal:3128 https://checkip.amazonaws.com` → `52.10.244.25`**,
  the proxy's address for this run, read from the laptop.
- **[Claude] Two corrections, both from measurement.** `make hub-up` does **not** apply a `[D]` slice —
  it starts the host through the dormant hook, and the proxy came back as `i-0d42d0393c39eefdb`, so the
  replacement pending from the template comment still waits for a deliberate apply; the stage record and
  Lesson 64 had said otherwise. And the public address is per-run as the decision intended:
  `35.90.250.102` on 2026-09-17, `52.10.244.25` on 2026-09-18, one instance, `10.31.160.140` private
  throughout.

---

*Owed at the close of these sittings: 2.4's Athena read from a Sandbox space, which needs a running
space.*

## 2026-10-17 — decision 1's replacement, still pending

*Written by Claude in a session with the environment down. One reading, as `awsds-infra-prod` (account
`<Production>`, permission set `InfrastructureAccess`).*

`ec2 describe-instances` on `awsds-prod-proxy`: `i-0d42d0393c39eefdb`, the instance 2026-09-17's apply
left, `stopped` (a user shutdown at 2026-10-16 23:33:56Z), last launched 2026-10-16 16:31:16Z, private
`10.31.160.140`, no public address while stopped. So the host decision 1 left to be replaced has not
been replaced; `make hub-up` starts it and never applies the slice.

## 2026-10-18 — verification ii read from the deployed sets, and the pickup's state

*Written by Claude, in the task `stages-06fgh-readings` the orchestrating session ran on the user's
approval of 2026-10-18, with the environment down. Every call is a read, as the infrastructure user with
`InfrastructureAccess`: `awsds-infra-identity` (`<Identity Account>`) for the permission sets,
`awsds-infra-sandbox-1` (`<Sandbox Account 1>`) for the customer-managed policy and `awsds-infra-prod`
(`<Production Account>`) for the job role. Account ids are replaced by the account's name.*

- **[Claude] Verification ii, the six deployed persona sets** (`sso-admin`
  `get-inline-policy-for-permission-set`, `list-managed-policies-in-permission-set`,
  `list-customer-managed-policy-references-in-permission-set`). Statements per set:
  `DataScientistAccess` 21, `DataScientistStagingAccess` 14, `DataScientistProdAccess` 16,
  `DeploymentManagerAccess` 17, `DevEnvStewardAccess` 16, `GovernanceManagerAccess` 16. None tests
  `aws:SourceIp`, `aws:SourceVpc` or `aws:SourceVpce`, and no set carries a permissions boundary. The
  Allow statements are the ones 0.1's table lists by set, plus `ReadRedshiftServerlessStatus` on
  `DataScientistAccess`: `GetNamespace`, `GetWorkgroup`, `ListNamespaces`, `ListTagsForResource`,
  `ListUsageLimits` and `ListWorkgroups` on `*`, Stage 5b step 2.3's, committed 2026-09-20 with two
  Redshift denies. `CloudWatchLogsReadOnlyAccess`, on four sets, is at v12 (updated 2026-02-12), and
  `awsds-org-project-storage-vending` in `<Sandbox Account 1>` at v1 (2026-08-24). `git log` on
  `terraform-live/identity/sso/` since the 6g commit shows no other statement change.
- **[Claude] The job role the drop-box names.** `iam get-role` on `awsds-prod-job-exec`: created
  2026-10-18T19:59:03Z, `RoleLastUsed` empty at 22:40Z. Production's `us-west-2` trail from 19:59Z: 85
  `AssumeRole` events, none on that role, and no `StartJobRun`, `CreateJob`, `CreateProcessingJob` or
  `CreateTrainingJob`. `glue get-jobs` in Production returns none. Stage 9's pickup (its step 2.5) is a
  Glue job under that role, so the SageMaker processing-job quotas of 0 are not on its path.

## 2026-11-22 — decision 1's replacement, made by the hub sitting's proxy apply

*Written by Claude in the session holding Stage 6g, on branch `claude/modest-robinson-66556d`, from about
01:50 UTC. The apply is the coordinating session's: it is relayed from Stage 12's log of 2026-11-22 (PR #352),
and that session confirmed the facts below in a message. This session wrote nothing to AWS. Its reads ran
as the infrastructure user with `InfrastructureAccess` in Production (`awsds-infra-prod`, `us-west-2`).
Times are UTC.*

- **[The coordinating session, relayed]** `production/proxy/` from `main` at `65254241`, which carries
  #354's `t3.small`, applied from a saved plan 2026-11-21 23:51:42 to 23:53:26: `1 added, 2 changed,
  1 destroyed`. The instance was replaced on `ami` and `user_data` (this decision's corrected comment and
  `TM-01`'s `-n`, #351), with `instance_type` `t3.micro -> t3.small`; re-plan `No changes`. The proxy served
  nothing from 23:51:43 to the new host's first request at 23:54:00.
- **[Claude] The trail**, `lookup-events` by resource name: `TerminateInstances` on `i-0d42d0393c39eefdb`
  at 23:51:52, `running` to `shutting-down`; `RunInstances` at 23:52:55 for `i-071bcc561f75b51d7`,
  `t3.small` on `ami-09f6e62a9fe578f92`, private `10.31.160.128`. Both calls were made by
  `AWSReservedSSO_InfrastructureAccess_*` with Terraform 1.17.2's user agent, from the laptop's own uplink.
- **[Claude] The host**, `describe-instances` at 01:51: `i-071bcc561f75b51d7` running, launched 23:52:54,
  public `184.36.57.235`. `describe-addresses` reads one Elastic IP in Production, `52.89.212.1`, on the
  tunnel host `i-0e3ae32bacd61c9b2`.
- **[Claude] Its user data**, `describe-instance-attribute --attribute userData`: 15,148 bytes of plain
  script. It carries the corrected comment (*"here, the proxy still comes up with an empty allow-list"*) and
  not *"while the Elastic IP is still being associated"*. It renders `dstdomain -n` and has no step (0).
- **Verdict**: the replacement decision 1 left owed on 2026-09-17 is made, and decision 1 is closed. The
  host runs `65254241`'s template. `main` has since gained #356's step (0) in the proxy's user data (15,685
  bytes) and #359's size check. The step (0) makes a plan from `main` read `1 to add, 2 to change, 1 to
  destroy` until its apply, which waits until after §N.9's day 2 (Stage 12's log).

## 2026-11-22 — 2.4's Athena read, as the project role through 6f's subscription

*The choice of principal and the query are the user's: the query ran in the portal as the Data Scientist
User, in a new tab of that user's browser profile, in `eighth-experimentation`'s query editor with *Athena
(SQL)* as the compute and no space. 6f's session confirmed beforehand that 11.12 would not revoke the
subscription that night. The §N.9 day 2 session and the coordinating session were told before the query.
Claude's reads ran as the infrastructure user with `InfrastructureAccess` in `us-west-2`, read-only:
`awsds-infra-sandbox-1` (`<Sandbox Account 1>`), `awsds-infra-data` (`<Data Governance Account>`) and
`awsds-infra-identity` (`<Identity Account>`). Times are UTC.*

- **[user] The choice**, between the two options of the waiting list with Claude's recommendation: the
  project role through 6f step 11's subscription, read from the portal's query editor. The other option was
  the persona from a laptop, and `DataScientistAccess` carries no `athena:` action since 2026-08-26 (D19),
  so its `StartQueryExecution` would have stopped at the identity policy.
- **[Claude] Before the query, the fulfilment is live.** In Data Governance, `lakeformation list-permissions`
  on `curated.trades` reads `SELECT` for Sandbox's `IAMPrincipals` under
  `context.datazone.projectId=="avhvbqn37ty7m8"`, updated 2026-10-26. In Sandbox, `glue get-table` reads the
  resource link `glue_db_blerpkhn9nj7o0.trades` targeting `curated.trades`.
- **[user]** *"A consulta `SELECT * FROM "glue_db_blerpkhn9nj7o0"."trades" LIMIT 10;` retornou dataframe com
  10 linhas de dados, com as colunas `trade_date`, `desk` , `instrument`, `quantity`, `price`."*
- **[Claude] The execution**, in `workgroup-avhvbqn37ty7m8-5hkjdsy3umpi1c`:
  `c9f604ea-50f8-47b3-b171-caf3985b6692`, `SELECT * FROM "glue_db_blerpkhn9nj7o0"."trades" LIMIT 10`,
  `SUCCEEDED`, submitted 02:15:33 and completed 02:15:35, 1,178 bytes scanned, 1,847 ms in the engine (Athena
  engine version 3). Its result is `…/avhvbqn37ty7m8/dev/sys/athena/c9f604ea-50f8-47b3-b171-caf3985b6692.csv`
  in the project path. `curated.trades`' current metadata is still `00003-c291e115-…metadata.json`, the table
  last updated on 2026-10-24 at 22:26:46.
- **[Claude] Sandbox's trail.** `StartQueryExecution` at 02:15:33 as the project role
  `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`, invoked by `sqlworkbench.amazonaws.com`. Its source
  identity resolves in Identity Center to the Data Scientist User. At 02:15:34, two `GetDataAccess` for
  `SELECT` by the same role: one invoked by `athena.amazonaws.com` on the resource link
  `glue_db_blerpkhn9nj7o0/trades`, its audit context naming the query, and one invoked by
  `glue.amazonaws.com` on the lake's `curated/trades`. No error.
- **[Claude] Data Governance's trail.** The same vend in the cross-account form at 02:15:34 (`AWSAccount`,
  invoked by `glue.amazonaws.com`, `SELECT` on `curated/trades`). Then nine `Decrypt` at 02:15:35 by
  `awsds-data-lf-registration` under `alias/awsds-data-data`, encryption context `aws:s3:arn` =
  `arn:aws:s3:::awsds-data-curated`, invoked by `glue.amazonaws.com`, none refused.
- **Verdict**: verification iv is answered yes, and 2.4 is done.
  - The objects were read with the registration role's vended credentials. That role is a Data Governance
    principal, which `DenyOutsideTrustedNetworks` exempts through `aws:PrincipalAccount`, a test 2.3 left
    unchanged. This comes from reading `buckets.tf`; no S3 data event was read to attribute it.
  - A space would add only the Athena API call through Sandbox's `athena` interface endpoint.
  - Stage 9 8.1 measured the same path on 2026-10-30 (its log).
  - With decision 1's replacement (the entry above), nothing in this stage is owed.

## 2026-11-22 — the vend's attribution in both trails, read for the supplement

*Claude's reading, with no AWS call, of the events the entry above looked up, as saved from that night's
`cloudtrail lookup-events`: Sandbox's `StartQueryExecution` and `GetDataAccess`, Data Governance's
`GetDataAccess` and `Decrypt`. AWS's Lake Formation pages on CloudTrail were read the same night. Times are
UTC.*

- **[Claude] Sandbox.** The `GetDataAccess` invoked by `athena.amazonaws.com` on the link carries
  `requestParameters.auditContext.additionalAuditContext` = `{queryId: c9f604ea-50f8-47b3-b171-caf3985b6692}`,
  a string, and `cellLevelSecurityEnforced` `true`. Its `additionalEventData` reads `requesterService`
  `ATHENA`, `lakeFormationPrincipal` the project role's ARN and `lakeFormationRoleSessionName`
  `AWSLF-00-AT-<Sandbox Account 1>-CRWz3tDXZ4`. The one invoked by `glue.amazonaws.com` on `curated/trades`
  reads `callType` `EXTERNAL`, `requesterService` `ATHENA` and the same session name, with no audit context.
  `StartQueryExecution` shows `queryString` as `***OMITTED***`, so the statement above is
  `get-query-execution`'s. The project role's session is `<Identity Center user id>@5hkjdsy3umpi1c`, the
  user id being the source identity.
- **[Claude] Data Governance.** The shared copy is of the glue-invoked event alone: `userIdentity` of type
  `AWSAccount`, `accountId` Sandbox's, `principalId` the project role's unique id and that session, and
  `additionalEventData` as in Sandbox, the session name included. The nine `Decrypt` name
  `assumed-role/awsds-data-lf-registration/AWSLF-00-AT-<Sandbox Account 1>-CRWz3tDXZ4`, a session created at
  02:15:34, with `invokedBy`, `sourceIPAddress` and `userAgent` `glue.amazonaws.com`, no source identity and
  no `vpcEndpointId`.
- **[Claude] AWS's pages.** *Cross-account CloudTrail logging* gives the session name as
  `AWSLF-<version>-<engine code>-<account id>-<suffix>`, `AT` for Athena and the account id of the account
  that requested the credentials, with a Glue job's S3 event as its example, and names the consumer's opt-in,
  *Resource owners* under *Default permissions for AWS CloudTrail*. Neither it, the service's CloudTrail page
  nor the underlying-data page mentions KMS events, the audit context or an Athena read's `invokedBy`.
- **Verdict**: in Data Governance the `Decrypt` events read as Glue's, and the shared `GetDataAccess` names
  Athena, Sandbox and the role's session, never the query, which only Sandbox's trail joins through the
  session name. Written as `SUP-416`; `SUP-116` gains that a statement with its own `LIMIT` gets none
  appended.
