# Log — index

One file per stage records what was done in AWS by hand. The user and Claude write these files
cooperatively; Claude writes only when the user asks, in that sitting. Plan narrative goes in
[`docs/plan/history.md`](../plan/history.md), not here.

Claude never edits a stage log on its own initiative: not to tidy it, not to correct it, not as a side
effect of another task, and not because an entry looks incomplete. An unrequested edit to the record of
what happened is the one change nobody would think to review. Entries up to Stage 4 word their
provenance notes as named exceptions to an earlier, stricter rule.

**Provenance** is mandatory. Every file's header states who wrote it; where one file has entries from
both hands, each entry says which, and so does anything inside an entry that came from the other hand: a
measurement quoted verbatim, an explanation added on request. A reading pasted by the user is data and
stays verbatim; what Claude adds around it is analysis and is marked as such.

Claude maintains this index without asking. After reading a stage log, Claude brings that stage's
`Records` cell to what the file holds.

One log file mirrors one stage file: `docs/log/log-stage-NN-*.md` ↔
[`docs/plan/stages/stage-NN-*.md`](../plan/stages/INDEX.md), the same slug with a `log-` prefix, so no
log file shares a filename with the plan file it mirrors. The `Records` column says what each file holds,
so no stage requires reading another stage's log.

| Stage | Log | Records |
|---|---|---|
| Stage 0 — Baseline | [log-stage-00-baseline.md](log-stage-00-baseline.md) | Management account created by hand; `aws` CLI and `terraform` installed; the pre-existing `SUSPENDED` `Sandbox` account under the root, left alone (`EXC-01`). |
| Stage 1a — Landing zone, accounts and OUs | [log-stage-01a-landing-zone.md](log-stage-01a-landing-zone.md) | Account-quota ticket (15); root MFA; the USD 50 budget; Control Tower enabled in `us-west-2`; every OU and account vend, including the refused `Identity` vend under `Security`; the access portal and the two SSO users; the break-glass chain (`awsds-org-break-glass-alerts`, `awsds-org-root-activity`, `AWS Break Glass Alert`) and its 2026-08-09 test; centralized root access and the `Delete root credentials` check. |
| Stage 1b — Identity, policies, detective controls | [log-stage-01b-identity-and-controls.md](log-stage-01b-identity-and-controls.md) | Closed 2026-08-12. The 8.3 metric filter and alarm; Identity Center delegation (step 1); the five `sso-group-*` groups (2); `InfrastructureAccess` and its assignments (3); the delegated administrator's read boundary (4); the six SSO profiles (5); the `list-identities.sh` snapshot; 5.1's retirement of the Account Factory assignments; the AZ table (6); 8.2's Access Analyzer in Audit (`awsds-org-external-access`), 35 findings, INV-16. |
| Stage 1c — Preventive policies | [log-stage-01c-preventive-policies.md](log-stage-01c-preventive-policies.md) | Closed 2026-08-14. 7.0's readings; 7.2's `enable-policy-type`; 7.4's account BPA; the 7.3 battery; 7.5's root attachments (`awsds-org-scp-baseline`, `awsds-org-scp-perimeter`); 7.6's four `awsds-org-scp-ou-*` documents probed per OU; the 7.5a/7.6a amendments; 7.7's `CT.MULTISERVICE.PV.1` and root-user controls; 7.8's RCP, declarative and tag policies, `readback.py`'s defect, and the RCP lockout of every SSO user, re-probed 93/0/0. |
| Stage 1d — Audit trail, Config scope, org-wide enablement | [log-stage-01d-org-wide-enablement.md](log-stage-01d-org-wide-enablement.md) | Complete. Step 9's Object Lock on the CloudTrail log bucket (2026-08-15: `COMPLIANCE`/90 days, INV-14, the borrowed `AWSControlTowerExecution`); step 12's `Security` OU controls probed from Log Archive and Audit; step 10's Config spend and volume readings, decisions 4 and 8; the 2026-08-14 pre-stage readings (bucket names, `CTS3PV8`, Lake Formation, trusted access); step 11's `ram enable-sharing-with-aws-organization` (INT-11). |
| Stage 2 — Terraform foundation | [log-stage-02-terraform-foundation.md](log-stage-02-terraform-foundation.md) | Closed 2026-08-16. Step 5.0's four delegation readings and the 5.1 document; open question 11 measured; steps 1, 6 and 9 (skeleton, gates, `Makefile`); steps 2 and 3 (five bootstrap applies, `check-bootstrap-parity.py`); 5.1a's narrowing; step 5 (`identity/sso/`) and 5.5 (`identity/org-policies/` adopted); step 8's D11 lifecycle targets; the Validation and the `awsds` reserved-prefix finding; verification (iii), INV-17. |
| Stage 3 — Networking | [log-stage-03-networking.md](log-stage-03-networking.md) | Closed 2026-08-16. The five execute-time decisions; step 0 (Account Factory VPCs removed); pass 1 `foundation/` in three accounts; pass 2's peerings and zone associations; pass 3 `egress/` (`vpc-egress-v0.1.0`, USD 0.480/h); the D11 `make down`/`make up` cycle; the three probe slices (perimeter, peering, INT-09, flow logs); the teardown of 59 resources; the instrument defects (`NT-3`/`NT-4`, `EG-4`, `make status`, the 404/404 pair). |
| Stage 4 — VPN access | [log-stage-04-vpn.md](log-stage-04-vpn.md) | 2026-08-16/20: step 1.3; pass 1 and the three D11 defects; decision 4 revised (Secrets Manager); 2.3's anchors; 4.3/1.4, the first boot; 4.1/4.2 (`mbp`, `raspi`, `--on-host`); pass 2 (`production/probes`, the MTU finding); pass 3 (`DenyControlPlaneOffVpn` on six sets, `CloudWatchLogsReadOnlyAccess`); the control-plane pair; verification (iii); the lifecycle cycle; the server MTU 1280; the amd64 addendum, `wireguard-v0.3.0`. |
| Stage 5 — Data foundation | [log-stage-05-data-foundation.md](log-stage-05-data-foundation.md) | 2026-08-18/20: the INT-11 before-reading; decisions 1-6; pass 1 (the two-step apply); pass 2 (the GM's grants); pass 3 (the shares); the propagation; 4a/4b (`consumer-data`, `DL-6`); 4c (`DataScientistAccess`, `DL-12`); the `security-zone` withdrawal; 4d's proofs, the `DenyControlPlaneOffVpn` S3-path defect and its amendment; the sample rows (`kms:GenerateDataKey`); the wrong-human sign-in; 4e; pass 6 (Security Hub CSPM, `EXC-01`). |
| Stage 6a — SageMaker Unified Studio (executed) | [log-stage-06a-unified-studio.md](log-stage-06a-unified-studio.md) | 2026-08-19/30: decisions 1, 3-5 before the stage; step 0 (flat, then rebuilt); the pull-forward audit; passes 0-2a, verification (i); the plan reviews; `images/`, `sandbox/buildbox/`; steps 1.3-1.5, 1.7 (INT-16, `grants.tf`), 5.0 (`default-v0.1.0`); pass 3's first project; the off-VPN reading; the DNS Firewall list, 4.3, the CDN finding (`EXC-05`); S3 Access Grants and the `aws:SourceVpc` swap; OQ 21/22; decision 6 dissolved; the `US-7` repair. |
| Stage 6b — `Development` becomes `Staging` | [log-stage-06b-development-becomes-staging.md](log-stage-06b-development-becomes-staging.md) | 2026-09-05/06: the preparation sitting (pass 0, auto-enrollment ON); passes 1-5 step by step: the SMUS unwind, the persona swap and lake revocation, the rename and OU move, the battery re-composed, the Recipe E migration, the token flip, three `moved {}` sets, the old state bucket destroyed, the document sweep; the Validation list; step 3.5; 6c pass 0 read against 6b. Owed: the provisioned product's parameters, Management-only. |
| Stage 6c — Networking: the single egress hub | [log-stage-06c-networking-hub.md](log-stage-06c-networking-hub.md) | 2026-09-06/08, done: passes 0-3 (three Production VPCs, INT-22, six peerings, `vpc-v0.2.0`/`v0.3.1`); pass 4's cut-over (both hub hosts, the proxy on the perimeter); pass 5 (design B, `NO_PROXY`, DNS Firewall 63→10, the buildbox moved); `EXC-04`/`05`/`06` closed; pass 7 (`hub-up`/`hub-down`, `proxy.py`); 6.1-6.7 (allow-list vs monitored, the IPv6 ULA, the ICMP rate limit); decision due 4 as (c); pass 8's split-tunnel profile. |
| Stage 6d — Unified Studio: what 6a left owed | [log-stage-06d-unified-studio-remainder.md](log-stage-06d-unified-studio-remainder.md) | 2026-09-07/10, in progress: 3.6, 7.2, 7.1, the space-path ceiling lifted (`sagemaker-denies-v0.2.0`); the first session under the proxy (3.1-3.3); `sudo`/`apt` and the Code Editor gallery; the DNS Firewall attribution; D38 §6's `open` build plane; step 9's `default-v0.1.1` build; step 8 closed (`github.com` removed); 8.8 (`vpc-egress-v0.11.1`, Lesson 59); the log-debugging runbook; step 4's MWAA workflow and the `compute` fix (Lesson 60); **step 2 end to end** — the `dev-env` slice, the 256-character cap on an app image configuration, decision 8 putting the proxy environment in the Dockerfile, the attach and both app types starting on the image, INT-01 and INT-17 closed, the second Python environment on uv, the `sync` that outgrew SSM and moved to SSH, the uv cache in the image layer, `default-v0.2.0` built and pushed, and the first version bump with the two things it taught (the apps first; a detach is `[]`); **2026-09-11, the remote IDE** — 8.4's delivery closed with a stock-image negative control, 3.1's R refusal and decision 6 (CRAN in, conda out, unapplied), the `StartSession` caller read as the **project role** from the client off the VPN, decision 5 answered by two refusals and a fallback, the two IDE servers in one container, the client pinned to the image's version, the first session's egress by host (`api.anthropic.com` and editor telemetry refused, a fourth IDE host riding the `.amazonaws.com` entry), `rust-src` missing from the image's rustup profile, and the CRAN apply with its in-space proof one association interval later. |
| Stage 7 — GitLab, Runners and ECR | — | *no entries yet*; will carry the internal CA fingerprint (D36) |
| Stage 8 — CI/CD pipelines | — | *no entries yet* |
| Stage 9 — Deployment target platforms | — | *no entries yet* |
| Stage 10 — Workflow orchestration and promotion | — | *no entries yet* |
| Stage 11 — Data protection and DLP | — | *no entries yet* |
| Stage 12 — Observability, governance and FinOps | — | *no entries yet* |
| Stage 13 — Public-facing web tier | — | *no entries yet* |
| Stage 14 — Per-business-unit Sandbox vending | — | *no entries yet* |
| Stage 15 — GuardDuty org-wide | — | *no entries yet* |
| Stage 16 — The sandbox lake | [log-stage-16-sandbox-lake.md](log-stage-16-sandbox-lake.md) | 2026-08-26, the whole stage in four sittings: the three applies and the Lake Formation admin-seat finding (`v0.4.0` → `v0.5.0`); the contrast pair and the laptop test; the project wiring (the connection form, the CloudTrail both-doors reading, the notebook readings, the auto-vend plugin); the revoke exercise (`SL-4`'s defect, the ≤19 s vend-door window, the bearer residual). |

## How an entry gets written

Claude writes into a `docs/log/log-stage-*` file only on a request in that sitting. The request takes
one of two shapes; the difference is who holds the pen, not what is allowed.

| Mode | When it is the right one |
|---|---|
| **Claude drafts, the user pastes** | The user is at the keyboard and wants the file to stay in their hand. The only mode when the entry is about acts Claude did not observe |
| **Claude writes the file directly** | The entry is long, interleaves Claude's readings with the user's, or amends an entry already there. The user says so explicitly ("escreva no log", "atualize o log") and Claude states what it wrote |

In either mode the entry names its hands (see Provenance above) and follows the rules below. In the
drafting mode the entry goes to the chat as one fenced block, so it is pasted untouched.

- **English and Markdown** in both modes; the chat is in Portuguese and these files are not. In the
  drafting mode, one fenced code block and never chat prose: a ` ```markdown ` fence, or a longer outer
  fence (` ````markdown `) when the draft itself contains one.
- **No identifiers.** An account id becomes the account's AWS `Account.Name` in angle brackets
  (`<Audit Account>`, `<Sandbox Account 1>`, `<Management Account>`); the names are in
  [`docs/ORGANIZATION.md`](../ORGANIZATION.md), and which id is which account is resolved from the
  entry's own surrounding text or from `aws/output/`, never guessed. An e-mail address inside an ARN
  becomes that user's role (`<control tower admin user>`). Nothing else in a pasted output is touched:
  the `AWSReservedSSO_*` suffixes, the policy, organization and root ids, the error wording and the
  encoded authorization failure blobs stay verbatim. The entry declares the substitution once, in its
  provenance note; the tenth entry of [`log-stage-04-vpn.md`](log-stage-04-vpn.md) is the wording to
  copy.
- **Concise:** the command, the outcome, and any finding that survives nowhere else. Leave out what
  `aws/output/` holds (regenerated on demand), what a `docs/plan/` file explains, and the reasoning
  behind a choice. The log carries what happened, in order.

`./scripts/check-identifiers.py` gates the identifier rule: it runs in `make check` and in `pre-commit`
over every tracked file and fails on a standalone twelve-digit number or an e-mail address. It was added
on 2026-08-17 after three log files were found holding twenty-four ids and two addresses (Lesson 14). It
cannot reach git history and cannot decide which account an id belongs to. A hit inside an existing entry
is still an edit to a stage log, so it waits for the user's request; the gate names the line, it does not
authorise the fix.

**Adding a stage log:** the user creates `docs/log/log-<same-filename-as-the-stage-file>` and copies the
two-line header from an existing one; Claude replaces that stage's `—` above with the link and a
one-line `Records` summary, and keeps it current as the file grows. A `Records` cell that says less than
the file holds defeats the index.

**Not in these files:** break-glass use is recorded here (date, reason, actions), but the procedure is
[`docs/plan/runbooks/break-glass.md`](../plan/runbooks/break-glass.md); why the plan changed is
[`docs/plan/history.md`](../plan/history.md).

---

*Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md) · Plan core: [GENERAL_PLAN.md](../GENERAL_PLAN.md)*
