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
