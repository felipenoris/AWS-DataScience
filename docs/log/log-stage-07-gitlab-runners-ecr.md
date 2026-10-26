# Log — Stage 7 — GitLab, Runners and ECR

*Written cooperatively. Every entry names whose hand performed the act; a measurement the user pasted
stays verbatim. The stage file is
[`docs/plan/stages/stage-07-gitlab-runners-ecr.md`](../plan/stages/stage-07-gitlab-runners-ecr.md).
Account ids are replaced by the account's name in angle brackets.*

---

## 2026-10-12 — the readings before pass 1

- **[Claude] The prerequisites, read live as the infrastructure user.** `VPC-SharedServices`
  (`10.30.0.0/16`) exists; the Sandbox↔SharedServices peering is `active`; the `awsds.internal` apex is
  associated with 5 VPCs and holds `proxy.` and `vpn.` and nothing else, so 1.4's `gitlab` record is
  owed; `awsds-pages.internal` is associated with 2 VPCs and holds NS and SOA only. The Sandbox domain
  `awsds-studio` holds one project, `eighth-experimentation` (`ACTIVE`), the INT-09 clone's source.
  `alias/awsds-prod-tfstate-pki` exists and no `production/pki/` state object does; the only Production
  secret is `awsds-prod-vpn-host-key`; the only `/datascience/prod/` parameter is the proxy allow-list;
  the only Production bucket is the state bucket, so step 2.3's "existing bucket" does not exist and the
  certificates are published into the GitLab objects bucket 1.1 creates. Production held two instances,
  the hub pair, both `stopped`; `production/egress` and `production/buildbox` were destroyed.
- **[Claude] `./aws/supplychain.py awsds-infra-prod awsds-infra-sandbox-1 awsds-infra-staging`: 0
  FAILED**, 4 notes (`SC-1`, `SC-3` twice, `SC-9`: "expected before Stage 7"), 8 passes: both
  repositories `IMMUTABLE`, registry scanning `BASIC (no rules)`, no pull-through cache rule,
  CodeArtifact `pypi`/`crates` with a domain policy, and the cross-account reads answering from both
  Interactive accounts (1 image visible each, the endpoint answered).
- **[Claude] EBS snapshot storage priced from the Price List Query API** (`aws pricing get-products`,
  `us-east-1`, `productFamily = Storage Snapshot`, `location = US West (Oregon)`): `USW2-EBS:SnapshotUsage`
  **0.05 USD/GB-month**, archive 0.0125, archive early-delete 0.0125, archive retrieval 0.03/GB.
  `docs/PRICING.md` §8 carries the row; the São Paulo column already read 0.068.
- **[Claude] The build plane confirmed `open` and the hub `stopped` at the reading**; the user ran
  `make hub-up` afterwards and authorized the stage's applies in chat.
- **[Claude] A session finding, 02:4x UTC: `GetRoleCredentials` answered `ForbiddenException: No access`
  for `awsds-infra-prod` while `awsds-infra-sandbox-1` still answered.** The `awsds` session's token file
  was rewritten at 02:35 UTC, after the readings above; the Sandbox profile was answering from its cached
  role credential and the Production one needed a fresh mint, which the current token's identity was
  refused. The shape Lesson 25 and 6c's notes record: a login over the same `sso-session` as another
  identity replaces the token. Pass 1's applies wait for a login as the **infrastructure user**.

## 2026-10-12 — pass 1, the applies (steps 1.1, 1.7, 2.2, 2.3, 2.4)

- **[user] `make hub-up`** before the sitting; both hub hosts read `running` (launched 02:42 UTC) when
  the applies began. **[user]** signed in again as the infrastructure user after the token finding
  above; `awsds-infra-prod` answered.
- **[Claude] `production/foundation/` applied (1.1): `18 to add, 0 to change, 0 to destroy`, re-plan
  `No changes`.** The key `alias/awsds-prod-gitlab`, the two buckets `awsds-prod-gitlab-objects` and
  `awsds-prod-gitlab-backup` (versioned, the second expiring at 30 days), the two containers
  `awsds-prod-gitlab-secrets` and `awsds-prod-runner-token` with their `GetSecretValue` denies.
- **[Claude] `production/egress/` applied (1.7) through `./scripts/slices.py up --env production --only
  egress --auto-approve`: `14 added`.** The hub check ran first and read both hub hosts `running`; the
  dormant hook was narrowed to no `[D]` slice by `--only`; `vpn`, `proxy` and `tooling` were listed as
  refused by name. `vpc-egress-v0.17.0`, 6c 5.5's thirteen plus `secretsmanager`. The plan-time output
  `no_proxy_all_groups` read **60 entries, sha256 `f8bc1df99d224181`**, and is the literal
  `production/tooling/variables.tf` carries (1.3). Before the output was re-exported by the slice the
  plan showed only `no_proxy` as `(known after apply)`: the module had the output since v0.17.0, the
  slice did not.
- **[Claude] `production/pki/` applied (2.1, 2.2): `20 to add, 0 to change, 0 to destroy`, re-plan `No
  changes`**, the first object ever encrypted under `alias/awsds-prod-tfstate-pki` (created 2026-08-15).
  The plan printed no private key. Read back from the published parameters with `openssl x509`:

  | Certificate | Subject | notAfter | SHA256 fingerprint |
  |---|---|---|---|
  | the root (D36 §5) | `O=AWS-DataScience, CN=awsds internal root CA` | 2036-10-09 06:35:12 UTC | `7B:E4:89:85:32:EB:98:E6:54:B0:19:AA:B2:C0:B3:FE:3C:46:1B:E4:FF:0B:18:5B:00:F3:C1:50:72:1D:1D:52` |
  | `gitlab.awsds.internal` | `O=AWS-DataScience, CN=gitlab.awsds.internal` | 2027-10-22 06:35:12 UTC | `D0:9A:BE:44:F2:18:2C:6E:FE:A4:CD:0C:F1:AE:09:4D:69:8A:23:1C:8B:4A:D1:31:A1:BF:33:1A:1E:2B:E5:6C` |
  | `*.awsds-pages.internal` | `O=AWS-DataScience, CN=*.awsds-pages.internal` | 2027-10-22 06:35:12 UTC | `23:D6:0C:3A:79:CB:5D:34:39:00:42:B8:B4:D7:09:B7:BB:81:CB:B9:80:1D:0D:55:81:61:E8:F7:74:E6:94:B9` |

  The leaves' re-issue is owed by 2027-09-22, when the plan starts proposing it (`early_renewal_hours`
  720). Published: `/datascience/prod/pki/{ca-root,leaf-gitlab,leaf-pages}-pem` and
  `s3://awsds-prod-gitlab-objects/pki/{awsds-root,gitlab.awsds.internal,awsds-pages.internal}.crt`; the
  keys in `awsds-prod-tls-gitlab` and `awsds-prod-tls-pages`.
- **[user] Decisions 6 and 7 taken as recommended, in chat:** CodeArtifact stays idle with no endpoint
  and no `assets` bucket family; Staging leaves the registry consumer map, which `registry/`'s 5.b apply
  carries (the four policies re-applied without it).

## 2026-10-12 — pass 1, GitLab applied (steps 1.2-1.6); the registry apply did not run

- **[Claude] `production/tooling/` planned twice and applied once.** The first plan failed at
  validation: `Error: invalid value for description` on the DLM lifecycle policy, whose description
  admits letters, digits, spaces, underscores and hyphens and nothing else; the apostrophe and the
  parentheses in the first wording were the fault, fixed in the slice. The second plan read `17 to add,
  0 to change, 0 to destroy`, with the rendered `gitlab.rb` as the S3 object's content (Lesson 54): the
  four `['env']` blocks carrying the 60-entry literal, `letsencrypt['enable'] = false`, the consolidated
  object storage with nine prefixes on `awsds-prod-gitlab-objects`, the backup upload to
  `awsds-prod-gitlab-backup`, Pages on `awsds-pages.internal` with access control, no SAML block. Applied:
  `17 added` at 06:38 UTC - the host `awsds-prod-gitlab` (`t4g.large`, `usw2-az1`), its 50 GiB data
  volume and the attachment, both security groups, the role and its profile, the DLM role and policy,
  the alarm, the S3 object and the two records.
- **[Claude] The `awsds` SSO token expired between the apply and the re-plan** (`refresh cached SSO
  token failed`, `CreateToken` `400`): the tooling re-plan, `terraform output` and the whole
  `production/registry/` apply failed on credentials before touching anything, so **`registry/` 5.b is
  not applied** and its plan (`8 to add, 6 to change, 0 to destroy` - the app-etl repository, three cache
  rules and three creation templates added; the six policies losing Staging's principal) is owed. The
  `aws` CLI kept answering for `awsds-infra-prod` from its cached role credential, which is how the
  readings below were taken. The session token lived about an hour and could not be refreshed.

## 2026-10-12 — the first boot deadlocked at `systemctl start gitlab-runsvdir`

- **[Claude] The reading.** The serial console (`get-console-output --latest`, the 64 KB window)
  stopped at 06:43:12 UTC on `template[/usr/lib/systemd/system/gitlab-runsvdir.service] sending run
  action to execute[systemctl start gitlab-runsvdir] (immediate)` and did not move for twenty minutes.
  CPU averaged 30% in the five minutes of the package install and **0.95% every five minutes after
  06:41**; network out fell from 2.5 MB to kilobytes; both status checks `ok`; the SSM agent `Online`
  (3.3.5226.0, through the `ssm` endpoints); the `gitlab-secrets` container still holds no version, so
  the bootstrap never reached the step after `gitlab-ctl reconfigure`. A reconfigure that is working
  does not sit at 1%; one that is waiting does.
- **[Claude] The cause, from GitLab's troubleshooting page** (`docs/REFERENCES.md`): *"The GitLab
  systemd unit file by default uses `multi-user.target` for both `After` and `WantedBy` fields"*, and
  *"this interacts poorly with cloud-init's own unit ordering"*. The bootstrap runs inside cloud-init's
  final stage, a dependency of `multi-user.target`; the start job for `gitlab-runsvdir` waits for that
  target, which waits for cloud-init, which waits for the reconfigure. The page's fix is
  `package['systemd_after']` and `package['systemd_wanted_by']` in `gitlab.rb`.
- **[Claude] The fix, in code:** `package['systemd_after'] = 'network-online.target'` and
  `package['systemd_wanted_by'] = 'multi-user.target'` in `gitlab.rb.tftpl`; `tooling/`'s next apply
  changes the S3 object alone. The stuck host has fetched the old file: either a `sudo systemctl
  restart gitlab-runsvdir` in an SSM session lets the stalled reconfigure continue (the page's own
  mid-run step), after which `awsds-gitlab-refresh` installs the new unit ordering, or the instance and
  its data volume are replaced (`terraform apply -replace=...`) once a session exists, and the new
  first boot carries the fix from the start. Neither has run; the host holds nothing worth keeping.

## 2026-10-12 — the host replaced with the fix; `registry/` 5.b applied

- **[Claude] The deadlock's end, read from the console before the replacement.** Chef gave up at
  07:44:09 UTC: `Mixlib::ShellOut::CommandTimeout: execute[systemctl start gitlab-runsvdir]
  (package::runit_systemd line 58) had an error: ... Command timed out after 3600s`; cloud-init
  `finished ... Up 3895.09 seconds` with `Failed to start cloud-final`. The host had run 65 minutes
  and configured nothing, and `awsds-prod-gitlab-secrets` still held no version.
- **[user] SSO login as the infrastructure user**, 14:07 UTC; `awsds-infra-prod` and
  `awsds-infra-sandbox-1` both answered `get-caller-identity`.
- **[Claude] `production/tooling/` applied with `-replace=aws_instance.gitlab
  -replace=aws_ebs_volume.data`**, 14:10-14:11 UTC: `3 added, 4 changed, 3 destroyed`. The attachment
  went first (the instance stopped before the detach, 32 s), then the old instance and volume; the S3
  object was rewritten with the two `package['systemd_*']` lines before the new volume
  `vol-072c3d3dc9883b104` and host `i-0e661200795f0e62e` (`10.30.52.94`, the same subnet) were
  created; both records and the alarm were repointed. `aws_instance.gitlab` now carries `depends_on =
  [aws_s3_object.gitlab_rb]`, so a replacement launches after the object it fetches is written.
  Re-plan `No changes` at 14:13 UTC.
- **[Claude] `production/registry/` 5.b applied**, 14:11 UTC, from a fresh plan identical to the
  morning's: `8 added, 6 changed, 0 destroyed` - `awsds-prod-ecr-app-etl` and its lifecycle policy,
  the three pull-through cache rules (`ecr-public`, `k8s`, `quay`) and their creation templates, the
  registry key's policy, the two repository policies and the three CodeArtifact policies re-written
  without Staging's principal (decision 7). Re-plan `No changes`.
- **[Claude] The instruments after the applies**, 14:14 UTC. `./aws/supplychain.py`: `SC-1` reads
  the new host (`t4g.large`, running, IMDSv2 required); `SC-7` both cross-account reads from Sandbox
  pass; `SC-8` 374 days of runway on both leaves; `SC-11` 60 entries, equal to egress's list;
  **`SC-12` fails three times** - no repository under any cache prefix, because nothing has pulled
  through yet. It reads red until 6.4's first pipeline pulls an image (verification vii): a dated gap,
  not a finding (Lesson 50). `./aws/egress.py` `0 FAILED`, `EG-5` 14 interface endpoints at 0.140
  USD/h. The persona and `ctadmin` profiles read `Token ... does not exist` in both snapshots: only
  the `awsds` session was signed in, which the scripts list as failed calls.
- **[Claude] The second first boot passed the point where the first one stopped.** `=== awsds gitlab
  first boot: 2026-10-12T14:11:21+00:00`; the package installed by 14:14; at 14:15:10 UTC Chef was
  writing nginx's configuration and at 14:16:30 running `migrate gitlab-rails database`, so
  `systemctl start gitlab-runsvdir` returned this time. One warning so far: `Object storage for
  ci_catalog_bundles must have a bucket specified`, a consolidated-storage object type the template
  does not name.
- **[Claude] The second boot's end.** `gitlab Reconfigured!` at 14:19:53 UTC (`Infra Phase complete,
  529/1346 resources updated in 05 minutes 03 seconds`, no `letsencrypt` or ACME line anywhere in the
  console: verification xii), the generated `gitlab-secrets.json` pushed as the container's first
  version (`AWSCURRENT`, 14:19:59), the refresh helper and the backup timer installed, then **the
  readiness probe read `404` on every try for five minutes**: `https://gitlab.awsds.internal/-/readiness
  -> 404`, `=== awsds gitlab first boot done: 2026-10-12T14:25:03+00:00 ===`, cloud-init `finished ...
  Up 829.32 seconds`. A `404` is Rails answering, not nginx's `502`, so the stack was up. GitLab's
  health-check page says the probes are reachable from localhost under the default allowlist
  (`docs/REFERENCES.md`); this probe connected to the host's own name, so it arrived from
  `10.30.52.94`, a client the allowlist does not admit. The bootstrap now probes with `--resolve
  "$GITLAB_HOST:443:127.0.0.1"`, the name kept for TLS; the user data is held, so the change rides the
  next first boot (8.2's rehearsal is the first). Both status checks `ok`, the alarm `OK` on the new
  id, the data volume `in-use` at `/dev/sdf`, no `available` volume and no snapshot in the account.
  Launch to a reconfigured host 8 min 44 s, to the end of cloud-init 13 min 54 s (verification vi:
  outside D8's 3-5 minutes).
- **[Claude] `ci_catalog_bundles` added to the consolidated object store**, the warning's object type,
  and `tooling/` planned `0 to add, 1 to change, 0 to destroy` - the S3 object alone, no replacement
  (verification xiii's plan half) - applied 14:22 UTC, re-plan `No changes`. The running host holds the
  previous file until the first `sudo awsds-gitlab-refresh`, in 1.8's session.

## 2026-10-12 — step 1.8, the first sign-in

- **[user] 1.8 done.** In the SSM session: `sudo cat /etc/gitlab/initial_root_password`, then
  `sudo awsds-gitlab-refresh`. Signed in at `https://gitlab.awsds.internal` as `root`, changed the
  username to `felipenoris` and set a new password. The account stays local: it is the break-glass.
  The browser still marks the address "Not secure", `https` struck through.
- **[Claude] The "Not secure" is the laptop, not the host.** Read through the tunnel: the host serves
  the leaf and the root (`s:/O=AWS-DataScience/CN=gitlab.awsds.internal`, issued by `CN=awsds internal
  root CA`), the chain verifies against the published root (`Verify return code: 0 (ok)`; `curl
  --cacert` reads `200` on the sign-in page) and the system store refuses it (`self signed certificate
  in certificate chain`); `security find-certificate` finds no copy of the root in the login or System
  keychain. The leaf meets Apple's TLS requirements (SAN `gitlab.awsds.internal`, `TLS Web Server
  Authentication`, 375 days, ECDSA P-256), so runbook §C's `add-trusted-cert` is the whole fix:
  verification x's laptop surface, half-answered. The refresh's `gitlab Reconfigured!` was not read
  here (verification xiii's host half).
- **[Claude] The runbook gained §I, the initial setup of a fresh host, and §U names the up/down order
  with the hub and the tunnel**, at the user's request.
- **[Claude] The instance read through the user's Chrome session** (read-only, the user's offer).
  **GitLab CE v19.4.2** (Shell 14.57.3, Workhorse and KAS v19.4.2, Pages 19.4.2, Ruby 3.3.12, Rails
  7.2.3.1, PostgreSQL 17.11 for `main` and `ci`, Redis 7.2.16), components `Up to date`. Users: 2 -
  the administrator `felipenoris` and **`GitLab Duo`, a bot the instance created on its own** 12
  minutes after the reconfigure (Lesson 17); administrators 1, both without 2FA. Features: **sign-up
  `Enabled`** (the home page carries the banner *"Your GitLab instance allows anyone to register for an
  account"*), OmniAuth `Enabled` with no provider yet, GitLab Pages `Enabled`, container registry
  `Not enabled`, instance runners `Enabled` and none registered, groups 0, projects 1: the user's
  `felipenoris/test-project` with `main` pushed over HTTPS through the tunnel 8 minutes before the
  reading. **Auto DevOps reads `instance enabled`** in the project's CI/CD settings: a project without
  a `.gitlab-ci.yml` would run a pipeline nobody wrote once a runner exists, so runbook §I step 6
  turns it off. **Verification iv, read in the test project's CI/CD settings**: the sections are
  General pipelines, Auto DevOps, Runners, Artifacts, Variables, Pipeline trigger tokens, Deploy
  freezes, Job token permissions and Secure files - **no Protected environments, no deployment
  approvals**: this is CE, and Stage 8's two gates take the protected-tag shape (3.3). The tab opened
  with no certificate interstitial because Chrome keeps the bypass for the session; the trust step
  stands as read above.
- **[user] Two confirmations, in chat.** `sudo awsds-gitlab-refresh` ended in `gitlab Reconfigured!`
  (verification xiii's host half: a `gitlab.rb` change reached the running host through decision 8's
  path, with no replacement). The root was trusted on the laptop with runbook §C's two commands, and
  the browser stopped marking `https://gitlab.awsds.internal` "Not secure" (verification x's laptop
  surface). The runbook's §C is now the client procedure, numbered, with the verification at its end,
  and the client runbook points at it.
- **[user] Sign-up kept open**, in chat, after runbook §I step 6 recommended it off.
- **[user] `make gitlab-down` run at the end of the first session**, with the reading that it destroys
  every SageMaker-related endpoint in Production, and the question whether a GitLab session raises the
  whole production egress.
- **[Claude] It does.** `production/egress/` is one flat list - the module's core eight plus the
  slice's six extras, 14 interface endpoints - with no optional group in Production, so `gitlab-up`
  creates all 14 and `gitlab-down` destroys all 14 (at 15:40 UTC: `athena` deleted, ten `deleting`,
  the hub untouched). The SageMaker pair has carried a comment since 6c calling it vestigial and
  deferring the question to this stage; `athena`, `glue` and `lakeformation` are the module's core,
  overridden never. Opened as **decision 9** in the stage file, recommended: drop the pair, keep the
  core.
- **[user] Are the two to be cut used later by the plan?** **[Claude]** Read across the stages: no.
  Stage 9 3.3a names the job-facing set for `VPC-Workloads` (`sagemaker.api` among it) and 4.3a re-cuts
  Staging's; the runner's future SageMaker calls (Stage 10's model-package registration as
  `awsds-deploy-prod`) are control-plane calls the `open` build plane carries through the proxy, and
  `sagemaker.api` is added here by the stage that wants them private; no stage invokes an inference
  endpoint from this VPC. Recorded in decision 9.
- **[Claude] `make gitlab-down` read back at 15:53 UTC**: the host `stopped` (user initiated 15:44:08
  UTC) and still `10.30.52.94`, with `gitlab.awsds.internal` pointing at it; interface endpoints in the
  account: none; no runner; `awsds-prod-vpn` and `awsds-prod-proxy` `running`. Verification i's first
  half: the address survived the stop; the start answers the second.

## 2026-10-12 — the second session: verification i, the namespace and the persona groups (3.4, 3.5)

- **[user] `./scripts/slices.py up --env production --only tooling,egress`**, the pre-token form; the
  environment came back, and a browser session was opened for Claude.
- **[Claude] Verification i closed.** The host started at 15:59:24 UTC with the same `10.30.52.94`,
  `gitlab.awsds.internal` and `*.awsds-pages.internal` unchanged, the 14 endpoints back, and the
  sign-in page reading `200` from the laptop against the system store (16:03 UTC). A `[D]` stop/start
  moves no address and repoints no record.
- **[Claude] Steps 3.4 and 3.5 done through the user's browser session**, at the user's request: the
  group **`awsds`** (ID 4, private) and, inside it, **`data-scientists`** (5), **`deployment-managers`**
  (6), **`governance-managers`** (7) and **`dev-env-stewards`** (8), each private, each with the
  administrator as its only member. The membership mirroring of the Identity Center groups is by hand
  and the user's, after SAML (3.2) creates the users. 3.6's repositories are not created.
- **[Claude] Step 3.6 done through the user's browser session**, at the user's request: the projects
  **`awsds/app-etl`** (ID 2) and **`awsds/dev-env`** (ID 3), both private, both empty (no README, so the
  first push names `main`). On `dev-env`, the roles and the protection Stage 8 step 1.0 specifies,
  taken now: `awsds/data-scientists` invited as **Developer**, `awsds/dev-env-stewards` as
  **Maintainer**, and the protected tag **`*-v*`** with creation **Maintainers** only (the CE gate: who
  can push the release tag). `app-etl` carries no role and no protection yet; Stage 8 owns its deploy
  roles. Read back on the members page (`Groups 2`) and the repository settings (`*-v*`, `0 matching
  tags`, `Maintainers`).
- **[Claude] Two readings about the tool, not the instance.** The REST path (`/api/v4/projects/3/share`
  from the page's own session) was refused by the assistant's permission classifier, so the UI did
  it. In GitLab's modal dialogs the browser extension's element clicks close the dialog and its
  keystrokes land on the page when no input is focused, where `t`, `i` and `s` are GitLab shortcuts;
  clicks by screen coordinate worked every time. The second `dev-env` form submission arrived with an
  empty name for the same reason, and was redone with a screenshot before the submit.

## 2026-10-12 — step 3.2, the SAML block delivered

- **[user] Steps 3.1 to 3.3 of runbook §A done in the Identity Center console**: the `GitLab` application,
  the two attribute mappings, the four persona groups assigned; the application's metadata URL handed
  over in chat.
- **[Claude] Step 4 and 5.** The metadata XML (public, `200`, 2575 bytes) carries one `SingleSignOnService`
  (HTTP-POST) and one certificate: `CN=amazonaws.com, OU=IDAS, O=Amazon`, valid **2026-10-12 to
  2031-10-12**, SHA256 `05:61:B4:BB:C4:9A:4A:63:FA:81:AC:2B:C9:CF:BA:5C:76:66:9C:09:5C:5C:87:38:12:EF:F4:73:0A:FD:75:B7`.
  Written into `terraform-live/production/tooling/saml.auto.tfvars` in this session's worktree (ignored by
  the `*.tfvars` rule). `production/tooling/` planned `0 to add, 1 to change, 0 to destroy`, the S3 object
  gaining `omniauth_enabled`, `omniauth_allow_single_sign_on = ['saml']`, `block_auto_created_users =
  false`, `auto_link_saml_user = true` and the `saml` provider; applied 16:37 UTC, re-plan `No changes`.
  The host runs the previous file until `sudo awsds-gitlab-refresh` (the user). The round-trip (3.2's
  user half, verification iii) is unread. The `.tfvars` lives in one checkout: a plan elsewhere proposes
  removing the block, and runbook §A names that plan as the signal (Lesson 61).
- **[user] Asked for the installation procedure in the runbook**, having read the build as an EC2 instance
  with an EBS volume and GitLab installed on it. **[Claude]** That is the shape, with the install done by
  the first boot and nothing by hand: runbook §P now carries it, the ten bootstrap steps in order, with
  the measured timings and the rebuild's two forms.
- **[user] The SAML round-trip works** (verification iii): `sudo awsds-gitlab-refresh` run, then a sign-in
  as the data-scientist persona through the **AWS Identity Center** button; GitLab created the account on
  the first sign-in. The account belongs to no group.
- **[Claude] Read from the persona's own session**, which replaced the administrator's in the same Chrome
  profile (`/admin/users` answers `404` to it, so the membership edit is the administrator's): the
  account's username is the e-mail's local part with the `+` dropped, the groups page reads *"You don't
  have any groups yet"*. The shape that worked is the one the template sends: NameID
  `urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress` from `Subject = ${user:email}` plus the
  `email` attribute in `basic` format; no loop and no browser refusal reported. **Owed**: the user into
  `awsds/data-scientists` as Developer (§I step 7's mirroring), which gives Developer on `dev-env` through
  the share; the remaining personas as they first sign in.
- **[user] The data-scientist persona added to `awsds/data-scientists` as Developer**, in the UI, as the
  administrator. The session ends here; the next one starts at the remaining personas' memberships,
  Pages (4.2) and pass 3 (runbook §K).

## 2026-10-12 — the third session: pass 3 prepared, the environment raised

- **[Claude] The readings before pass 3**, 17:37 UTC, as the infrastructure user: the hub pair, GitLab,
  `egress/`, `runners/` and `buildbox/` all down (`make status ENV=production`: 0.0000 USD/h); three
  peer sessions on the laptop, all idle and none on Stage 7.
- **[Claude] `production/runners/` reviewed before its first apply, three findings, fixed in
  `0628be2`.** (1) The runbook's first pipeline ran `apk add aws-cli` inside `moby/buildkit:rootless`,
  whose Dockerfile ends in `USER 1000:1000`, so the job could not install the client that minted its
  registry login. The boot now fetches Amazon's ECR credential helper v0.12.0 through the proxy, checks
  it against the SHA256 its release page publishes (`a22ab6d5…ded1a6`, a static build,
  `CGO_ENABLED=0`), and the runner mounts it read-only into every job beside `ECR_REGISTRY`. (2) Runbook
  §K created an instance runner. Any job reads the role's credentials through the metadata service (hop
  limit 2), the role pushes to the three image repositories, and sign-up is open, so an instance runner
  would let a self-registered account push an image; §K now creates a protected project runner of
  `awsds/app-etl`, the stage's "protected refs, project locks". (3) The boot's GitLab check read
  `/-/readiness`, which answers `404` outside the monitoring allowlist (this log, the second boot); it
  reads the sign-in page, and the boot waits up to ten minutes for it before registering. The template
  rendered with stub values and passed `bash -n`; `validate` and the hooks passed. The upstreams were read
  from the laptop: the runner repository for Amazon Linux 2023 serves `gitlab-runner` up to 19.4.1, each
  version requiring `gitlab-runner-helper-images` at the same version.
- **[user] `git push`, `make hub-up`, then `./scripts/slices.py up --env production --only
  tooling,egress`.** **[Claude]** Read back at 18:00 UTC: `awsds-prod-vpn` and `awsds-prod-proxy`
  running (started 17:53:21 and 17:53:24 UTC), `awsds-prod-gitlab` running since 17:53:40 on
  `10.30.52.94`, 14 interface endpoints `available`, the sign-in page `200` from the laptop through the
  tunnel with the chain verified (`ssl_verify=0`); `awsds-prod-runner-token` holds no version. Decision 9
  stays open: `egress/` came up with its 14.
- **[user] Step 6.1's GitLab half and the token**: the project runner created on `awsds/app-etl`
  (protected, untagged jobs, `awsds-prod-runner`) and its token put into `awsds-prod-runner-token`
  (version `AWSCURRENT` at 18:12:31 UTC). A first `put-secret-value`, at 18:04:41 UTC, ran before the
  runner existed and wrote whatever was typed at the silent prompt; that version is `AWSPREVIOUS`.
- **[Claude] `production/runners/` planned `6 to add, 0 to change, 0 to destroy`** (the role, its two
  inline policies, the SSM managed policy, the profile, the instance); the rendered bootstrap read in
  the plan: the proxy, `egress/`'s 40-entry `no_proxy`, the helper's version and digest, the registry.
  The three peer sessions told before the write. **Applied through `make gitlab-up AUTO=1`** (the
  user's authorization), 18:15:45 to 18:16:55 UTC: GitLab `already running`, `egress/` `No changes`,
  `runners/` `6 added`; the instance `i-002105d808682af49` on `10.30.32.132`.
- **[Claude] The runner's first boot, read from the serial console: 1 min 42 s, registered.** Boot start
  18:16:49 UTC; the helper passed its digest check; GitLab's sign-in page `200` on the first try;
  `Runner registered successfully`, `Verifying runner... is valid` as
  `awsds-prod-runner-i-002105d808682af49`; the egress check `pypi.org` `200` through the proxy,
  `10.31.0.1` `403`, GitLab direct `200`; `first boot done` at 18:18:31 UTC, cloud-init `Up 106.84
  seconds`. Verification viii's registration half: yes, from the Secrets Manager token on a fresh
  instance.
- **[user] `make gitlab-up RUNNERS=0` asked for**, to raise GitLab without the runner. **[Claude]**
  Added (`edbc3ad`): `RUNNERS=0` narrows `gitlab-up` to `tooling,egress`, any value but `0` or `1` is
  refused, and `gitlab-down` destroys the runner whatever the flag says.

## 2026-10-12 — step 6.4, the first pipeline

- **[user] The three files of runbook §K pushed to `awsds/app-etl`'s `main`** (commit `0817e161`).
  Pipeline #1: `build-image` and `cache-probe` failed in 12 and 11 s. The runner took both jobs (the
  protected runner served the first push's pipeline), so the branch was protected before the pipeline
  was created.
- **[Claude] Both logs read through the user's Chrome, at the user's request.** Everything before the
  first `FROM` worked: runner 19.4.1, `moby/buildkit:rootless` pulled from Docker Hub through the proxy,
  the clone with the CA root (`Updating CA certificates...`), BuildKit rootless up with no privileged mode,
  and `[auth] sharing credentials for <the registry>`. Then every pull through the cache read `not found`:
  `ecr-public/docker/library/alpine:3.22` in one job, the probe's three in the other.
- **[Claude] The cause, from CloudTrail.** The runner role's two `GetAuthorizationToken` calls succeeded
  (the credential helper works); its four `BatchGetImage` calls read `RepositoryNotFoundException`; and
  ECR's four `CreateRepository` calls, made as
  `AWSServiceRoleForECRTemplate/ECRPullThroughCacheWithTemplate`, were refused: *"is not authorized to
  perform: ecr:TagResource"*. That service-linked role (created 2026-10-12T14:11:54Z by `registry/`'s 5.b
  apply) carries `ECRTemplateServiceRolePolicy`, which grants `ecr:CreateRepository` and nothing else,
  and the three creation templates carried the five tags. The repository creation templates page says it:
  the creation role *"must be provided when using repository tags and/or KMS in the template, otherwise
  the repository creation will fail"*. `cache.tf` had carried the KMS half of that sentence and not the
  tags half.
- **[user] Option (a) taken: the templates carry no tags**, recommended over a custom creation role
  (a second principal for public bytes, `cache.tf`'s own argument against a CMK). **[Claude]
  `production/registry/` applied 18:34 UTC: `0 added, 3 changed, 0 destroyed`**, the saved plan the
  user approved, re-plan `No changes`; the three templates read back with no tags, `MUTABLE`, `AES256`
  and no custom role.
- **[Claude] Pipeline #2 started through the user's Chrome, at the user's request: both jobs passed.**
  ECR created the four cache repositories at 18:34:57 UTC (`MUTABLE`, `AES256`, the templates' two
  lifecycle rules, no tags) and filled them between 18:35:00 and 18:35:08 as
  `AWSServiceRoleForECRPullThroughCache` (`InitiateLayerUpload` to `PutImage` in CloudTrail).
  **Verification vii: yes.** The first pull through each of the three rules succeeded with no route to
  the internet: the upstreams need no credential and ECR fetches them itself. **Verification viii: yes**,
  on both halves: BuildKit rootless built and pushed with no privileged mode under `seccomp=unconfined`.
  `build-image` took about 8 s: the `FROM` through the cache 1.3 s with the import, `apk add` through the
  proxy (`dl-cdn.alpinelinux.org`), and the push of `awsds-prod-ecr-app-etl:v0.1.0-0817e161`
  (`sha256:9a37b6929c23…`, 4.0 MB) at 18:34:59 UTC.
- **[Claude] A pull through the cache imports every platform of a multi-architecture index**, as the
  pull-through cache page says: `pause:3.10` stored five Linux images of 0.2 to 0.36 MB and two Windows
  images of 270 and 308 MB; `alpine:3.22` and `busybox:1.37` seventeen entries each, attestation
  manifests included. A large multi-architecture image is pulled by its platform digest when the other
  platforms are not wanted.
- **[Claude] The retry of `build-image` (job 7) was refused, the deliverable's second half:** *"failed to
  push …/awsds-prod-ecr-app-etl:v0.1.0-0817e161: unknown: The image tag 'v0.1.0-0817e161' already exists
  in the 'awsds-prod-ecr-app-etl' repository and cannot be overwritten because the tag is immutable."*
  The rebuild had produced another manifest (`sha256:a580d4771ad5…`): the build is not byte-reproducible,
  and the layers uploaded before the refusal came at the manifest.
- **[Claude] `proxy-pair` (job 6), run by hand: `through the proxy -> 200`, then `curl: (28) Connection
  timed out after 20001 milliseconds` with the proxy variables unset.** INT-21's job half; the access
  log's half (the proxy naming the runner's requests) is unread and needs `./aws/proxy.py --on-host`,
  which writes through `ssm:SendCommand`.
- **[Claude] `./aws/supplychain.py`: all checks passed**, `SC-12` green on all three rules (2, 1 and 1
  cached repositories) and `SC-10` the note of a runner running.
- **[user] Decision 3 taken, in chat: the three credential-free cache rules stay**, the condition holding
  (the first pull needed no route). **[user]** authorized `./aws/proxy.py --on-host` for INT-21's log half.
  **[Claude] Not run:** the access log is exported to CloudWatch Logs (`/awsds/prod/proxy`, 365 days),
  so the reading is a `filter-log-events` with no `ssm:SendCommand`. **INT-21's log half, read for
  `10.30.32.132` between 18:16 and 18:40 UTC: every external request of the runner is named, all `200
  TCP_TUNNEL`** - `storage.googleapis.com` 2 requests, 571 MB (the runner and helper-image packages
  `packages.gitlab.com` redirects to, 14 requests), `production.cloudfront.docker.com` 8, 122.5 MB, with
  `registry-1.docker.io` 16 and `auth.docker.io` 2 (`moby/buildkit:rootless`),
  `d5l0dvt14r5h8.cloudfront.net` 2, 54.7 MB, with `public.ecr.aws` 7 (the job images from ECR Public),
  the credential helper's bucket 1, 9.1 MB, `dl-cdn.alpinelinux.org` 2, 5.5 MB (the two builds' `apk
  add`), `pypi.org` 2 - and the boot's `http://10.31.0.1/` `403 TCP_DENIED`. No ECR name and no
  `us-west-2` S3 name appears: the pushes and the cache's pulls left by the endpoints and the gateway.

## 2026-10-12 — step 4.2, Pages

- **[user] A `pages` job and a `pages-readback` job pushed to `app-etl`'s `main`** (commit `b30af685`,
  pipeline #3, at Claude's draft): `pages: true` on a job that writes `public/index.html`, then a job in
  a later stage that reads `$CI_PAGES_URL` with `--cacert /etc/gitlab-runner/certs/ca.crt`.
- **[Claude] Followed through the user's Chrome, at the user's request.** `build-image`, `pages` and
  `pages:deploy` passed; `CI_PAGES_URL=https://app-etl-ffa1fa.awsds-pages.internal`, a unique domain
  (GitLab's default for a new project), under the wildcard record and the wildcard leaf. **The runner's
  read-back: `pages: http=302 ssl_verify=0`**, redirected to `https://projects.awsds-pages.internal/auth`:
  the leaf validated against the CA root from the runner, and access control asked for a session.
- **[Claude] The laptop's visit stopped at an OAuth consent**: *"GitLab Pages is requesting access to
  your account"*, scope `api`, and for an administrator *"Authorizing GitLab Pages will let it act as an
  administrator"*; the application is the one Omnibus registered at the first reconfigure. **[user]
  Authorized it, as the administrator `felipenoris`.** The page then rendered in Chrome with no
  certificate warning: *"app-etl - Published by job 10 on awsds-prod-runner from commit b30af685."*
  From the laptop's shell: `http=302 ssl_verify=0` against the system store, the served certificate
  `CN=*.awsds-pages.internal` issued by `CN=awsds internal root CA`, `notAfter` 2027-10-22. **Step 4.2
  done: Pages answers on two of INT-19's surfaces, the laptop and the runner.** Each user who visits a
  private project's site authorizes the same application once.

## 2026-10-12 — step 2.6, `default-v0.6.0` built on the runner

- **[Claude] The readings before the build.** The root has been in the recipe since pass 1
  (`images/base/ca-certificates/awsds-root.crt`, `CA_ROOTS_EXPECTED=1`). `./aws/devenv.py` could not
  compare the baked bypass list (`DE-2` fails while `sandbox/egress` is down, which leaves no outputs); a
  read-only plan of that slice gave `no_proxy_all_groups` 70 entries, sha256 `aafa08da98a61f5c`, equal to
  the Dockerfile's literal (`DE-1`) and to version 5's (`DE-5`): no edit owed.
- **[user] Items 1 to 4 of Claude's proposal taken, in chat**: the image's trust beyond the OS store, the
  build as a pipeline of the GitLab project `awsds/dev-env`, the distribution through the pull-through
  cache, a smoke test inside the job.
- **[Claude] `e885dcd`**: `base` section 5 sets `SSL_CERT_FILE`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE`
  and `NODE_EXTRA_CA_CERTS` to `/etc/ssl/certs/ca-certificates.crt` and asserts the root reached that
  bundle; `images/smoke/Dockerfile` reads `https://gitlab.awsds.internal` with curl, git and both
  Pythons; `images/build.gitlab-ci.yml` is the pipeline (the recipe cloned at `RECIPE_SHA`, `base` with
  `SMD_IMAGE` pointed at the cache and the digest pin kept, `dev-env` `FROM` the pushed base, the smoke
  build discarded). Pushed to GitHub, the commit served at 200.
- **[user] The runner linked to `awsds/dev-env`** (GitLab 19.4's label for the action is "Link", not
  "Enable") **and the file pushed as its `.gitlab-ci.yml`** (commit `63f3fe47`); the push created no
  pipeline, as the rules require a web trigger. **[Claude]** Read through the user's Chrome: the runner
  is assigned to `dev-env` and reads Protected, Lock to current projects and Run untagged jobs; the
  project lets Developers and above set pipeline variables.
- **[Claude] Pipeline #4 started through the user's Chrome, at the user's request**, on `main` with
  `IMAGE_TAG=default-v0.6.0` and `RECIPE_SHA=e885dcd484458a9fbffb4d7f6fd9d4f43566c194`: job 13 on the
  runner from 19:24:12 UTC.
- **[Claude] Job 13 succeeded in about 16 minutes**, read through the user's Chrome and from ECR. The
  distribution came through the cache: `ecr-public/sagemaker/sagemaker-distribution` held its one image
  at 19:27:57 UTC, pulled by the digest pin, its 2.94 GB layer arriving at about 35 MB/s through the
  endpoint (the buildbox took about 27 minutes through the proxy for the same order of bytes, 6d).
  **Pushed**, digests from the job's metadata and from `describe-images`:

  | Image | Digest | Size (ECR) | Pushed (UTC) |
  |---|---|---|---|
  | `awsds-prod-ecr-base:default-v0.6.0` | `sha256:94359041f65b8bfada3ec1603937dadd49055854c034910f20d8be4a53341975` | 3,745,648,934 | 19:29:13 |
  | `awsds-prod-ecr-dev-env:default-v0.6.0` | `sha256:43079013d424374161bc4025444623bfe31cc933bbde3637a51a05cb28bc5518` | 6,675,093,373 | 19:40:24 |

  They replace `default-v0.5.0`'s `sha256:c7ad2c964335…` (3,745,881,983) and `sha256:8ec04e357792…`
  (6,969,138,672); the new `dev-env` is 294 MB smaller compressed. **The smoke test passed, 19:40:25
  UTC**, every client reading `https://gitlab.awsds.internal` through the image's own trust:
  `curl (/usr/bin/curl): 200 ssl_verify=0`; `git (/usr/bin/git): fatal: could not read Username ...
  terminal prompts disabled`, the authentication wall and not a certificate; `/opt/conda/bin/python
  urllib 200`, `requests 200`; `/opt/awsds/venv/bin/python urllib 200`, `requests 200`. The seven
  `FATAL` matches in the log are the guards' own command text. Basic scan-on-push started on the new
  `dev-env` (`IN_PROGRESS` at the reading).
- **[user] The registration authorized as one sequence, in chat** (runbook `dev-env.md` §B, steps 2, 3
  and 5). **[Claude] The readings first**: one SageMaker domain, `d-p6gthxc82ckg`, with version 5
  attached to both app types; no app running (`down-studio-apps.py sandbox --dry-run`: `no running
  app`), so step 1 had nothing to delete; one space, `default-28f1b390-…`, on AWS's distribution by
  alias `4.5`, so step 6 had nothing to repair. The first plan of `sandbox/dev-env/` read `1 to add, 1 to
  change, 1 to destroy`: the change was the image role's read statement gaining
  `awsds-prod-ecr-app-etl`, because `registry/`'s `ecr_repository_arns` output carries it since 5.b.
  The statement now names `base` and `dev-env` by key, and the plan read `1 to add, 0 to change, 1 to
  destroy`. The three peer sessions told before the writes.
- **[Claude] Executed**: 19:47:50 UTC the detach (`update-domain` from the live block with both
  `CustomImages` emptied; domain `InService`); 19:48:13 the apply of the saved plan, version 5
  destroyed and **version 6 created** (`1 added, 0 changed, 1 destroyed`); version 6 `CREATED` with
  `ContainerImage` `…/awsds-prod-ecr-dev-env@sha256:43079013d424374161bc4025444623bfe31cc933bbde3637a51a05cb28bc5518`,
  the pushed digest; 19:48:45 the re-attach, its block differing from the pre-detach read only in
  `ImageVersionNumber` 5 -> 6 on both app types, and read back identical to what was sent. Re-plan `No
  changes`. `./aws/devenv.py`: `DE-5` pass, *"version 6, sha256:43079013d424...: 70 names, sha256
  aafa08da98a61f5c"*; `DE-2` fails because `sandbox/egress` is down, the known reading. **`default-v0.6.0`
  is what a new space's picker offers** since 19:48:45 UTC. INT-09's clone from a notebook is owed.
- **[user] The session ended**: the runner destroyed at 19:51:29 UTC, `awsds-prod-vpn` and
  `awsds-prod-proxy` stopped at 19:51:52 and 19:51:55, `awsds-prod-gitlab` at 19:57:40 (the instances'
  own transition records). **[Claude]** Read back at 20:10 UTC: no interface endpoint in Production or
  Sandbox, no instance and no app running in Sandbox, `make status` `estimated burn: USD 0.0000/h` across
  every environment, `./aws/egress.py` `0 check(s) FAILED` (its exit 1 is the persona and `ctadmin`
  profiles, signed out). Owed for the next session: INT-09's clone from a notebook on version 6, step 6.5,
  pass 4.

## 2026-10-12 — after the merge: two readings with the environment down, step 6.5

- **[user] PR #119 merged** (squashed as `a3f698b`); the session continued on a new branch cut from it.
- **[Claude] The clone pair's negative half, 20:32 UTC, the hub stopped**: from the laptop, `git
  ls-remote https://gitlab.awsds.internal/awsds/app-etl.git` read `Could not resolve host:
  gitlab.awsds.internal`, the name resolving only through the tunnel.
- **[Claude] Verification xiv's second half, read with `make down ENV=production DRY=1`**, which runs
  nothing: `vpn` and `proxy` are listed as *"refusal 6 - the hub is not stopped by ENV=production;
  `make hub-down` is its target"*, by name, and the only `[D]` host the target would stop is
  `awsds-prod-gitlab`.
- **[Claude] Step 6.5, in the repository alone.** Read first: `production/buildbox/`'s state lists no
  resource, and Production holds no security group, role, instance profile or instance named for the
  buildbox. Deleted: the slice, its `layers.py` rank and slice row, `scripts/buildbox.py`, the runbook's
  procedures, the size file's `.gitignore` exception and its `check-tfvars-shape.py` row, the
  `NETWORK_SLICES` entry. The release ledger moved to `images/README.md` §*The releases*, with
  `default-v0.6.0` added. Live references were repointed (`CLAUDE.md`'s routing row, both READMEs,
  `NETWORK.md`, `PRICING.md`, `cost-model.md`, `conventions.md` §6, `SMUS.md`, five runbooks, the
  Makefile's help, `aws/devenv.py`, two recipe comments); executed stages and logs keep theirs as
  records. `docs/plan/runbooks/buildbox.md` stays as a pointer page, because two stage logs link to it
  and `check-plan-refs.py` fails on a dead link. `make check` OK; `check-network-doc.py` clean. The empty
  state object stays in the state bucket.
- **[user] Decisions 2 and 4 taken as recommended, in chat**: ECR keeps basic scan-on-push, with enhanced
  scanning left to Stage 11 step 4 and the Julia/R residual accepted; no standing mirror between this
  repository and GitLab (step 7.1). Only decision 9 is open.
- **[user] Decision 9 taken as recommended, in chat**: the SageMaker pair leaves `production/egress/`.
  **[Claude]** The pair removed from the slice's extras; a read-only plan of the slice (down) reads `12 to
  add`, and its plan-time `no_proxy_all_groups` 56 entries, sha256 `0f80372bf880bb16`, the four SageMaker
  names (`api.sagemaker`, `runtime.sagemaker`, each in both spellings) the only difference from the 60.
  `tooling/`'s literal re-copied; with `saml.auto.tfvars` copied from the worktree that wrote it, the
  plan of `tooling/` reads `0 to add, 1 to change, 0 to destroy`, the S3 object alone, its eight
  `no_proxy`/`NO_PROXY` lines and nothing else.
- **[Claude] `production/tooling/` applied 21:26 UTC, at the user's authorization: `0 added, 1 changed, 0
  destroyed`**, the reviewed plan, re-plan `No changes`. The object read back from
  `s3://awsds-prod-gitlab-objects/config/gitlab.rb`: a `no_proxy` of 56 entries, no `sagemaker` name, the
  SAML block present. GitLab is stopped and runs the previous file until `sudo awsds-gitlab-refresh` at
  the next session; `egress/` builds its 12 at the next `make gitlab-up`.

## 2026-10-12 — decision 9 reaches the host

- **[user] `sudo awsds-gitlab-refresh` on `awsds-prod-gitlab`**, in a Session Manager shell, ended
  `gitlab Reconfigured!`: the host serves the 56-entry `no_proxy` the S3 object has held since the
  21:26 UTC apply. The shell's first command form failed in the project folder, where
  `production/tooling/` was never initialised, so `terraform output` returned nothing and `start-session`
  got an empty target; the runbook now finds the host by its Name tag.

## 2026-10-16 — the running release read; decision 10 written

- **[Claude] The release `awsds-prod-gitlab` runs, read with no write and no GitLab sign-in**, before
  22:41 UTC, as the infrastructure user through `awsds-infra-prod`, the tunnel up and the host `running`
  since 16:33:50 UTC. `https://gitlab.awsds.internal/help`, opened in the desktop app's browser with no
  GitLab session, shows "GitLab Community Edition" with no version and publishes `gon.revision`
  `ecff27ae760`; gitlab.com's API names `ecff27ae76032d42095793aa7639d3e73ae6f0de` as the commit of
  `gitlab-foss`'s tag `v19.4.2` (2026-10-07), so the host runs **CE 19.4.2**. The sign-in page publishes
  no revision, and `/api/v4/version` answers `401` without a token. The backup bucket holds two
  objects, `1791860449_2026_10_13_19.4.2_gitlab_backup.tar` (931,840 bytes) and
  `1792033259_2026_10_15_19.4.2_gitlab_backup.tar` (9,953,280 bytes). Systems Manager holds no software
  inventory for the host (`list-inventory-entries`, `AWS:Application`, empty).
- **[Claude] The `amazon/2023` `aarch64` index of `gitlab-ce`**, its primary metadata last modified
  2026-10-15 13:38:32 GMT, 315 packages: 19.4.0 built 2026-09-16, 19.4.1 on 09-22, 19.4.2 on 10-07 and
  19.5.0 on 10-15, with 19.3.5 on 10-12 on the older line, each release `ce.0.amazon2023`. The
  bootstrap's unpinned `dnf -y -q install gitlab-ce` would have installed 19.5.0 that day, and GitLab's
  restore page restores a backup only into the release that created it.
- **[Claude] Decision 10 written as recommended**, nothing applied: `gitlab_ce_version = "19.4.2"` in
  `production/tooling/variables.tf`, installed as `gitlab-ce-19.4.2-ce.0.amazon2023`, and
  `gitlab_runner_version`'s description names it. `terraform validate` and `tflint` clean on `tooling/`
  and `runners/`. The read-only plan of `tooling/` as `awsds-infra-prod` with the project folder's
  `saml.auto.tfvars`, 22:47:09 to 22:47:26 UTC: `No changes. Your infrastructure matches the
  configuration.`, `-detailed-exitcode` 0, no drift noted.
- **[Claude] The two pins' checks, written and exercised** (decision 10, 8.4). `scripts/check-gitlab-pins.py`
  read `gitlab_ce_version` `19.4.2` and `gitlab_runner_version` `19.4.1`: `both on 19.4`, `OK`. On a copy
  with the runner at 19.5.0 it printed `the server installs 19.4 and the runners 19.5` and `FAILED`, exit 1;
  a missing variable and a default that is not a literal each read `UNREAD`, exit 2.
  `./aws/supplychain.py awsds-infra-prod`, read-only, from 23:04 UTC: `SC-13` pass,
  `1792033259_2026_10_15_19.4.2_gitlab_backup.tar (2026-10-15T03:01:09+00:00), made by 19.4.2, equal to
  gitlab_ce_version`, every check passed. With `gitlab_ce_version` set to 19.5.0 in the working copy,
  `SC-13` failed and the script exited 2; the file was restored, and a third run left the snapshot green.

## 2026-10-16 — decision 10 taken

- **[user] Decision 10** (by 23:43 UTC, in this session's chat): "Tomo a decisão 10 da etapa 7 como
  recomendada. Registre aqui num PR pequeno." `gitlab-ce` pinned at 19.4.2 by `gitlab_ce_version`,
  written in PR #151 and checked by PR #154 (`check-gitlab-pins.py`, `SC-13`). Nothing to apply: the plan
  reads `No changes`, and the pin reaches the host at its next rebuild.

## 2026-10-17 — 8.3's down half: `supplychain.py` with GitLab stopped

*Written by Claude, in a session with the environment down. `./aws/supplychain.py awsds-infra-prod`
(account `<Production>`, permission set `InfrastructureAccess`), exit 0, "all checks passed". The report
itself carries account ids and stays out of git; this is its verdict list, for the diff 8.3 asks for at
the up half.*

| Check | Verdict |
|---|---|
| `SC-1` the GitLab host | pass: `t4g.large`, stopped, IMDSv2 required |
| `SC-2` the GitLab security groups | pass: no world-open ingress |
| `SC-3` the backup bucket and the `gitlab-secrets` container | pass: versioned; the container last changed 2026-10-12 14:19:59Z |
| `SC-4` `awsds-prod-ecr-base` and `-dev-env` | pass: both `IMMUTABLE` |
| `SC-5` the cache rules | pass: three, no immutable cache repository |
| `SC-6` CodeArtifact | pass: `pypi` and `crates`, one domain-policy block |
| `SC-8` the two leaves | pass: 369 days of runway, to 2027-10-22 06:35:12Z |
| `SC-9` the CA root parameter | pass: version 1, 2026-10-12 06:35:15Z |
| `SC-10` the runner | pass: no instance, the `[E]` layer between sessions |
| `SC-11` the bypass list | note: not compared, `production/egress` is down |
| `SC-12` the three caches | pass: `ecr-public` 4 repositories, `quay` 1, `k8s` 1 |
| `SC-13` the newest backup | pass: 2026-10-15 03:01:09Z, made by 19.4.2, equal to `gitlab_ce_version` |

`SC-7`, the consumers' cross-account reads, prints no verdict when only the Production profile is
named. 8.3's up half is the same run with GitLab up and the runner registered, every consumer profile
included: only timestamps and instance state may move.

## 2026-10-18 — 8.4's remainder: `SC-11` reads the deployed proxy configuration

*Written by Claude, session `stage-07-supplychain`, with the environment down (the hub hosts and GitLab
stopped, `production/egress/` and `production/runners/` destroyed). Every AWS call was a read, as the
infrastructure user through `awsds-infra-prod` (account `<Production>`, permission set
`InfrastructureAccess`) and `awsds-infra-sandbox-1` (`<Sandbox>`, the same permission set). Nothing was
applied.*

- **[Claude, session stage-07-supplychain] `config/gitlab.rb` read from S3 with GitLab stopped.**
  `s3://awsds-prod-gitlab-objects/config/gitlab.rb`, 103 lines, answered to the infrastructure user (the
  object is under `alias/awsds-prod-gitlab`, so `kms:Decrypt` answered as well). It holds four
  `<component>['env']` blocks, `gitlab_rails`, `gitaly`, `gitlab_workhorse` and `gitlab_pages`, each with the
  six variables `http_proxy`, `https_proxy`, `HTTP_PROXY`, `HTTPS_PROXY`, `no_proxy` and `NO_PROXY`. The four
  proxy variables read `http://proxy.awsds.internal:3128` in every block, and the two bypass variables carry
  one list in all four, equal to the literal in `terraform-live/production/tooling/main.tf` after
  `REGION` becomes `us-west-2`: 56 entries, sha256 `0f80372bf880bb16` (the digest convention of
  `aws/awslib/devenvrecipe.py`, recomputed here from the file). The object holds no secret: the lines that
  match `secret` are the bypass list's `secretsmanager` name, and the SAML values are public metadata.
- **[Claude, session stage-07-supplychain] `./aws/supplychain.py` extended.** `SC-11` keeps its comparison of
  the literal with `egress/`'s output (a note while `egress/` is down) and gains three readings. (1) The
  deployed object's four env blocks must each tell the contracted proxy in the four variables, and
  `tooling/main.tf`'s `proxy_url` must say the same: `GitLab's proxy target`. (2) The blocks must carry one
  bypass list in both spellings, equal to the literal in the code, so an object older than the code is a
  fail with the missing and extra names: `GitLab's deployed bypass list`. (3) A runner's rendered user
  data, `ec2:DescribeInstanceAttribute` `userData` decoded: the `PROXY` and `NOPROXY` assignments, `NOPROXY`
  equal to `egress/`'s `no_proxy` (the output `runners/` reads, not the all-groups list), and the six
  `--env` flags of `gitlab-runner register`, each referring to the assignment of its kind. Between sessions
  that reading is a note, naming `runners/main.tf`'s `proxy_url` as the code's side. Also fixed: the block
  comment of the ACM read (nothing is imported, decision 1), section 9's line about `Staging` (it has the
  profile `awsds-infra-staging`; it is not measured because decision 7 left it out of the consumer map),
  and section 4's title, which now names the proxy lines it already carried.
- **[Claude, session stage-07-supplychain] The extension exercised before it was believed (Lesson 54).**
  The run of 2026-10-18 20:09 UTC, `./aws/supplychain.py awsds-infra-prod awsds-infra-sandbox-1`, exit 0,
  *all checks passed*: 21 passes, 2 notes, 0 fails. The `SC-11` rows: a note (the bypass literal is not
  compared, `production/egress` is down), a note (*no runner instance*, with `runners/main.tf` saying
  `http://proxy.awsds.internal:3128`), a pass for `GitLab's proxy target` (*4 env blocks (gitaly,
  gitlab_pages, gitlab_rails, gitlab_workhorse) tell http://proxy.awsds.internal:3128 in 4 variables each, as
  terraform-live/production/tooling/main.tf does*) and a pass for `GitLab's deployed bypass list` (*56
  entries, sha256 0f80372bf880bb16, one list in the 4 blocks, equal to the literal in
  terraform-live/production/tooling/main.tf*). Thirty-one assertions ran offline on real payloads and
  mutated copies of them: the deployed object (another proxy in two blocks, a block removed, a second bypass
  list, a variable removed, a fifth block holding no proxy); the stopped GitLab host's real user data,
  whose `PROXY` and `NOPROXY` assignments parse (it has no register call, so exactly the six job-variable
  problems come back); and offline renderings of the three runner templates, clean as rendered and
  named correctly when `PROXY` is changed, a job variable points at the wrong assignment or is missing, or
  `NOPROXY` is not egress's. Two negative controls in the working copy, each restored: the `proxy_url` of
  `tooling/` and of `runners/` set to `http://10.31.0.1:3128` and one bypass entry changed (`127.0.0.1` to
  `127.0.0.2`) in the literal gave three fails and exit 2, the second naming `missing 1 (127.0.0.2),
  extra 1 (127.0.0.1)`; the contract constant moved to port 3129 in the script gave two fails, 17
  findings on `GitLab's proxy target` (16 in the object, 1 in the code) and the runners' proxy, and exit 2.
  **Unexercised: a runner's up path against a real instance**, which waits for a session with
  `production/runners/` applied; the decode is the one the stopped host's user data went through.
- **[Claude, session stage-07-supplychain] The identity pair, read from the entries above (the deliverable
  of the stage file).** Nothing was signed into. After the refresh that put the SAML provider on the host
  (the entry *step 3.2, the SAML block delivered*), the persona signed in through the Identity Center
  button and GitLab created the account (verification iii), and the local administrator `felipenoris`, the
  account renamed from `root`, edited that persona's membership of `awsds/data-scientists` "in the UI, as
  the administrator" (the user's entry), and authorized GitLab Pages as the administrator (*step 4.2*).
  The persona's session had replaced the administrator's in the same Chrome profile, so the membership edit
  followed a fresh administrator sign-in (inference: no entry names the sign-in form or the browser
  profile). Both halves of the pair are answered by the record: an Identity Center user with no local
  account created by hand, and the kept local account in use after SAML went live. The three other
  personas' memberships (3.5) stay owed.

## 2026-10-18 — the backups' expiry, the house image's spaces, and text read against the record

- **[Claude, session stage-07-supplychain] The two backups' expiry, dated by S3.** The backup bucket
  `awsds-prod-gitlab-backup` is versioned and holds three lifecycle rules: `expire-current-versions` (30
  days, prefix empty, so the whole bucket), `expire-noncurrent-versions` (7 days) and
  `abort-incomplete-multipart-uploads` (7 days). `HeadObject`'s `Expiration` header on the two objects:
  `1791860449_2026_10_13_19.4.2_gitlab_backup.tar` (931,840 bytes) `expiry-date="Fri, 13 Nov 2026 00:00:00 GMT"`;
  `1792033259_2026_10_15_19.4.2_gitlab_backup.tar` (9,953,280 bytes) `expiry-date="Sun, 15 Nov 2026 00:00:00 GMT"`,
  rule `expire-current-versions` on both. In a versioned bucket the expiry adds a delete marker and the
  noncurrent rule deletes the version 7 days later (the S3 page, `docs/REFERENCES.md`). The timer writes a
  backup at 03:00 UTC only while the host runs, so with GitLab down past 2026-11-13 the bucket holds no current
  backup and `SC-13` reads a note. The DLM policy kept going with the host stopped: six snapshots of the
  50 GiB data volume, 2026-10-13 to 2026-10-18, each taken between 03:48 and 03:57 UTC, the last two after
  the host stopped on 2026-10-16. No runbook procedure restores from a snapshot. 8.2 opens with
  `gitlab-backup create`, so the rehearsal is unaffected; the stage file's 8.2 carries the record.
- **[Claude, session stage-07-supplychain] The Sandbox spaces and the house image's versions, read for
  INT-09 and INT-19.** `awsds-infra-sandbox-1` lists two SageMaker AI domains, `d-lfgbdrjncmsu` and
  `d-p6gthxc82ckg` (one per project), each `InService` with the image `awsds-sandbox-dev-env` attached to
  JupyterLab and to the Code Editor, no version number. Each domain has one space,
  `default-28f1b390-0041-7068-8cc7-9ccef94277d1` (created 2026-10-15 in the first and 2026-08-23 in the
  second), and both run AWS's `sagemaker-distribution-cpu` at alias `4.5`: **no space uses the house
  image**. The image has versions 7, 8 and 9, all `CREATED` (2026-10-14, 2026-10-15 and 2026-10-16 local
  time); 6 and the earlier ones no longer exist. The space `jup-house-image`, started on version 7 on
  2026-10-15 (Stage 8's log), was deleted, and no entry of any log records a clone of GitLab from a
  notebook, so verifications x and xi keep the notebook surface owed.
- **[Claude, session stage-07-supplychain] Text corrected against the record, each item read first.**
  *The stage file's status* said pass 2 "nearly closed" while the plan core and the project notes said
  "closed"; both are one fact, pass 2 closed but for 3.5's three persona memberships, which wait for each
  persona's first sign-in. *`saml.auto.tfvars`* lives in the project folder's `secrets/` since 2026-10-13
  (its existence was checked, never its content). *The bypass literal* in `tooling/main.tf` holds 56
  entries, sha256 `0f80372bf880bb16`, recomputed; the 60-entry digest `f8bc1df99d224181` is the literal
  before decision 9. *`production/egress/`* lists no SageMaker endpoint: the module's core eight, the Session
  Manager trio and `secretsmanager` make the 12. *5.1 to 5.4 and 6.1 and 6.2* read "apply owed" and
  "unapplied" next to the entries that record their applies. *D8* holds no boot time: the "3-5 minutes"
  appears only in the stage file and this log, and conventions §5.1 rule 7 moves a `[D]` service to `[E]`
  when it proves cheap to rebuild and an `[E]` one to `[D]` when its rebuild proves slow, so a slow start of
  a `[D]` host re-opens nothing. Verification vi had been answered with the first boot, a fresh install;
  the one timed start (host started 15:59:24 UTC on 2026-10-12, the sign-in page `200` read at 16:03)
  bounds a start at 3 min 36 s. *Verification x*: the image's smoke test read GitLab through the image's
  own trust on 2026-10-12, so only the notebook is left. *Runbook §I step 6*: sign-up was kept open by the
  user, and no entry in this log or in Stage 8's records an act on Auto DevOps or on the restricted
  visibility level, so both are owed. *Runbook §M*: since Stage 8 decision 18 the dev-env pipeline's `register` and `retire` call the SageMaker API from
  `release/versions.py` and clone nothing; no file under `gitlab/` or `examples/app-etl/` clones
  `awsds/infrastructure` or uses a job token, which leaves the mirror with no reader in this repository
  (whether Stage 8 keeps it for the promotion jobs is that stage's). *INT-09's fallback* named a second
  peering and Development's commits, both gone with 6b, and a mirror decision 4 left unbuilt; *INT-19's
  owed clause* named image version 6; *`docs/PRICING.md`'s key row* said `production/pki/` does not exist.

## 2026-10-22 — 5.6's scope taken, and the backups read again

*Claude, in the session `stages-7-8-pending` (branch `claude/stages-7-8-pending-03936d`), after a review of
Stages 7 and 8 against their logs. AWS read as the infrastructure user with `InfrastructureAccess`
(`awsds-infra-prod`), reads only. Times UTC.*

- **[user] The decision**: *"Sobre os itens "Decisões suas, sem ambiente", registre que vamos acolher suas
  recomendações em todas essas decisões."*, then *"Faça as correções necessárias no plano, considerando os
  itens que você identificou que necessitam de ajuste. Registre as decisões e atualize os arquivos do plano
  e o log."*
- **[Claude] 5.6's scope, taken as recommended**, the recommendation written in this sitting after the
  user's acceptance and named in the closing message: `DataScientistAccess` pulls `awsds-prod-ecr-dev-env`;
  `DataScientistProdAccess` reads and pulls the application repositories, each by name; `DevEnvStewardAccess`
  reads `awsds-prod-ecr-dev-env` and `awsds-prod-ecr-base`, no pull; the registry-level actions stay on `*`.
  The grant is owed to `identity/sso/`.
- **[Claude] The backups**, `s3api list-objects-v2` on `awsds-prod-gitlab-backup`: the two objects of
  2026-10-18, `1791860449_2026_10_13_19.4.2_gitlab_backup.tar` (931,840 bytes, 2026-10-13 03:00:58) and
  `1792033259_2026_10_15_19.4.2_gitlab_backup.tar` (9,953,280 bytes, 2026-10-15 03:01:09), and the
  lifecycle's three rules unchanged, so the expiry stays 2026-11-13 and 2026-11-15. `describe-instances`:
  `awsds-prod-gitlab` stopped, last started 2026-10-21 23:26:08 in Stage 18's sitting, `awsds-prod-proxy`
  stopped, no `awsds-prod-runner*`. That sitting left no backup, so the host was down at 03:00 [inferred:
  the stop time is unread].
- **[Claude] The plan revised, no AWS call**: the status (`SC-11` reads a runner's user data only once one
  is up), 1.4's and 1.6's leftovers, 6.4's, 5.6's scope, 8.2's backup schedule (the timer, not a cron entry)
  and the snapshot cost row. D36 §5's data events and alarm went to Stage 11's 5.1 and 5.2, and its §6
  rotation rehearsal to Stage 12's 8.5, the receiving ends that did not carry them (Lesson 34).

## 2026-10-22 — 5.6's ECR grant written and planned

*Claude, in the session `stages-7-8-pending`, a plan as the infrastructure user (`awsds-infra-identity`),
no apply.*

- **[user] The request**: *"Do both here: first Stage 7 5.6's ECR grant in identity/sso, written and
  planned, then Stage 8 pass 4's code. Plan the application slices now that Stage 9 is applied. Apply
  nothing without my authorization."*
- **[Claude] What was written**, the scope the user took that morning: `identity/sso/locals.tf`'s
  `ecr_repository_arns`, each repository by its name in `production/registry/` and Production's account id
  from the organization; `DataScientistAccess` gains `PullTheHouseImage` on `awsds-prod-ecr-dev-env`;
  `DataScientistProdAccess`'s `ReadEcrImageMetadata` becomes `AuthenticateToEcr` on `*` and
  `ReadAndPullTheApplicationImages` on `awsds-prod-ecr-app-etl`; `DevEnvStewardAccess`'s
  `ReadEcrImageMetadataAndScanFindings` narrows to `awsds-prod-ecr-base` and `-dev-env`, its two
  registry-level reads moving to `ReadTheRegistryScanningConfiguration` on `*`.
- **[Claude] The plan**: 0 to add, 3 to change, 0 to destroy, the three sets' inline policies;
  `inline_policy_bytes` reads `data_scientist` 8,640 to 8,993, `data_scientist_prod` 6,808 to 7,098 and
  `dev_env_steward` 6,768 to 7,069, of 10,240. Each planned ECR ARN names Production's account,
  `us-west-2` and the repository by name.
- **[Claude] What follows**: the apply joins the waiting list.

## 2026-10-22 — 5.6 applied; the apply's state and lock left behind by a network drop

*Claude, in the session `stages-7-8-pending`, as the infrastructure user (`awsds-infra-identity`).*

- **[user] The authorization**: *"I authorize applying identity/sso (Stage 7 5.6) and staging/foundation and
  production/foundation (the Glue job grant) as the infrastructure user. Warn the other sessions and re-plan
  before applying."*
- **[Claude] Before**: the Stage 9 session and `Chat lateral` warned; a fresh plan, 0 to add, 3 to change.
- **[Claude] The apply**: `DevEnvStewardAccess`'s policy *"Modifications complete after 42s"*; then the
  laptop's DNS stopped resolving AWS's names (*"lookup sso.us-west-2.amazonaws.com: no such host"*,
  *"lookup awsds-org-tfstate.s3.us-west-2.amazonaws.com: i/o timeout"*): the other two sets' read-back,
  the state upload and the lock's release failed, and the apply exited 1.
- **[Claude] Readings after, the network back**: Identity Center holds all three new policies
  (`PullTheHouseImage`, `ReadAndPullTheApplicationImages` without `ReadEcrImageMetadata`,
  `ReadTheRegistryScanningConfiguration`), and `list-accounts-for-provisioned-permission-set` with
  `LATEST_PERMISSION_SET_NOT_PROVISIONED` lists no account for any of them. The state object
  `identity/sso/terraform.tfstate` is the 19:28:06Z version; `errored.tfstate` (312,211 bytes) is in the
  slice, gitignored; the lock object holds ID `f81ea42e-cc66-d468-e02c-b3223d0a93f8`, operation
  `OperationTypeApply`, this laptop's user, created 2026-10-22T20:51:27Z.
- **[Claude] What follows**: the recovery, `terraform force-unlock` of that lock and `terraform apply
  -refresh-only`, waits on the user, since the project's rule forbids a force-unlock; the slice refuses
  every plan until then.

## 2026-10-22 — identity/sso's lock removed and its state refreshed

*Claude, in the session `stages-7-8-pending`, as the infrastructure user (`awsds-infra-identity`).*

- **[user] The authorization**: *"I authorize terraform force-unlock f81ea42e-cc66-d468-e02c-b3223d0a93f8 on
  identity/sso (the lock of your own failed apply) and terraform apply -refresh-only as
  awsds-infra-identity, then a re-plan."*
- **[Claude] Before**: the lock object still held that ID, created 2026-10-22T20:51:27Z, and the state
  object was still the 19:28:06Z version; the Stage 9 session and `Chat lateral` warned.
- **[Claude] The recovery**: `terraform force-unlock -force` with that ID, *"The state has been
  unlocked"*, the lock object gone; `terraform plan -refresh-only` read the three sets' policies as
  *"changed outside of Terraform"*, no resource action, `DataScientistAccess` +`PullTheHouseImage`,
  `DataScientistProdAccess` +`AuthenticateToEcr` +`ReadAndPullTheApplicationImages` −`ReadEcrImageMetadata`,
  `DevEnvStewardAccess` +`ReadTheRegistryScanningConfiguration`; its apply *"0 added, 0 changed, 0
  destroyed"*, the state object written at 21:07:44Z, no lock left; the re-plan `No changes`
  (`-detailed-exitcode` 0). The failed apply's `errored.tfstate` moved out of the slice to the session's
  scratch directory.

## 2026-10-24 — GitLab's and the build runner's load history, read against their instance types

*Claude's hand, in the session `gitlab-runners-instance-analysis`, on the user's request in chat (the load
history of the runners and of the GitLab server, whether their instance types fit, and the types to use), as
the infrastructure user (`awsds-infra-prod`, `InfrastructureAccess`). Reads only; nothing was started,
stopped or written in AWS. Times UTC; the deploy and test runners are Stage 8's log entry of the same date.*

- **[Claude] The method.** CloudTrail's event history gave every `RunInstances`, `StartInstances`,
  `StopInstances` and `TerminateInstances` in Production since 2026-09-01 (242 events), and from them each
  host's running windows. CloudWatch's `AWS/EC2` metrics at five minutes were read over each window (basic
  monitoring: a point carries the statistics of up to five one-minute samples, so its `Maximum` is the
  busiest minute), with `AWS/EBS` for GitLab's two volumes; `get-console-output --latest` gave the newest
  instances' kernel console; the prices are the Price List Query API's, offer published
  2026-10-23T22:13:55Z (`docs/PRICING.md` §8). No host runs the CloudWatch agent, so memory and disk use
  have no history.
- **[Claude] GitLab, `t4g.large`**: 10 sessions and 37.02 h, 2026-10-12 14:11 to 2026-10-22 01:01 (the first
  host, deadlocked at its boot, left out). Past a session's first 15 minutes the CPU averaged 10.0%, p50
  9.2%, p95 14.1%, p99 19.9%, peak 36.9% (five-minute averages), against a 30% baseline; the first 15
  minutes averaged 14.6% and peaked at 59.1% with the fresh install's reconfigure on 2026-10-12, the busiest
  minutes at 99%. The credit balance climbed from 0 at the first start to 851.8 of the type's 864 by
  2026-10-22, since T4g keeps it for seven days after a stop; 4.12 surplus credits were borrowed once, at
  that first boot, and nothing was charged. The data volume read p95 4 IOPS (peak 31) and the root p95 6
  (peak 172), against gp3's 3,000 IOPS and 125 MB/s, at 0.6 ms per read and 1.0 ms per write (p50);
  `EBSIOBalance%` stayed at 99 or more; the network peaked at 4.1 MB/s in. The kernel reports 7,808 MB and
  the host has no swap: the user data creates none and the zram generator declined. The console of the
  2026-10-21 session, boot to power-off, holds no OOM-killer line.
- **[Claude] The build runner, `m8i.xlarge`**: 11 instances over 8 GitLab sessions, 30.91 h. Five image
  builds (2026-10-12 19:21, 2026-10-15 00:42, 01:27 and 16:06, 2026-10-16 21:43), each 15 minutes with two
  five-minute samples at 38-59% and a busiest minute at 98-99.8%; Stage 8's log times `build-images` at 951
  and 956 s. Outside them the CPU sits at 0.5% (p50): the mean is 2.5%, and the builds hold 1.25 h of the
  30.91 h. Four of the eight sessions built no image: 12.60 h, 2.67 USD of the 6.54 the runner's hours cost
  at 0.2117. The disk peaked at 74 MB/s and 759 IOPS against the root's gp3 125 MB/s and 3,000 IOPS, the
  network at 19.4 MB/s in (the cache's pull) and 13.3 MB/s out (the push), `EBSByteBalance%` at 99 or more.
  The console of the 2026-10-19 and 2026-10-21 instances, whole sessions, holds no OOM line; neither session
  built an image.
- **[Claude] The verdicts** (analysis, prices from `docs/PRICING.md` §8):
  - GitLab's `t4g.large` fits. The CPU uses a third of its baseline and the credit balance is at its cap,
    so a burst costs nothing, and the disk and the network are idle. GitLab's requirements page discourages
    burstable types for inconsistent performance, which needs the credits to run out; this host's never did
    after its first boot. Memory sizes GitLab and is unmeasured: the same page names 8 GB as the
    memory-constrained minimum and 16 GB as a single node's baseline. `t4g.medium` (4 GiB) is below that
    minimum, and `t4g.xlarge` (16 GiB, 0.1344 USD/h, twice the rate) would follow a memory reading, never
    the CPU.
  - The build runner's `m8i.xlarge` fits the build: the build fills the four vCPUs at its peaks, so
    `m8i.large` (2 vCPU, 0.1058) lengthens it, and an 8 GiB type such as `c8i.xlarge` (0.1874) bets on a
    memory figure nobody has read. The hours do not fit: the host is busy about 4% of the time it bills.
    `m8i-flex.xlarge` (0.2011) keeps the processor and the memory, halves the EBS baseline and saves 5%;
    raising the runner only for a session that builds saves the 12.60 h above.
  - A memory reading is what would move either verdict: `free -m`, `/proc/pressure/memory` and the
    processes' resident sizes in a GitLab session, and on the build runner during a build, or the
    CloudWatch agent's `mem_used_percent` on both hosts.

## 2026-10-24 — decision 5 amended: the build runner rises on `make gitlab-up BUILD=1`

*Claude's hand, in the session `gitlab-runners-instance-analysis`, as the infrastructure user
(`awsds-infra-prod`, `InfrastructureAccess`). Code and plans only; nothing was applied. Times UTC.*

- **[user] The request**, in chat after the load-history entry above (Claude's rendering): the option for
  `make gitlab-up` to raise the build runner only when asked, the test and deploy runners kept.
- **[Claude] What was written.** `production/runners/`: `build_runner` (bool, default `false`) as the
  `count` of the build runner's role module, instance profile and instance, and its three outputs through
  `one()`. The Makefile: `BUILD` (`0` or `1`, unset `0`) becomes `TF_VAR_build_runner` on `gitlab-up`, the
  way `GROUPS` reaches `up`, and lasts one apply; `BUILD=1` beside `RUNNERS=0` and a lower-case `build=`
  are refused. `layers.Slice.optional_hosts`: the runners row is 0.0376 USD/h, and `make status` adds
  `aws_instance.runner`'s 0.2117 while the state holds it. Runbooks `gitlab.md` §S, §U and §K and
  `promotion.md` §H and §T, whose image builds and tag pipeline need the build runner, now say
  `BUILD=1`; so do `terraform-live/README.md`, `NETWORK.md`'s row, the waiting list's Promotion row and
  `PRICING.md`'s GitLab session, 0.2436 USD/h by default against 0.4623 with the flag.
- **[Claude] The readings.** The slice's state held no managed resource before the change (serial 42),
  so no address moved. `make -n gitlab-up` expands `TF_VAR_build_runner=false`, and `true` with
  `BUILD=1`; `BUILD=2` and `RUNNERS=0 BUILD=1` exit 2. With `egress/` down the slice cannot plan (its
  user data reads `egress/`'s `no_proxy`), so a copy of it planned against the real state with that one
  local overridden: `build_runner=false` *"6 to add"*, the deploy and test runners and the test runner's
  role, the three build-runner outputs null; `build_runner=true` *"13 to add"*, the same six and the build
  runner, its instance profile, its role and the role's three inline policies and one attachment.
  `make status` against fabricated states priced the slice 0.0376 without the build runner and 0.2493
  with it. `make check` passed.

## 2026-10-24 — the runbooks read against decision 5's amendment and the plan's revisions of 2026-10-22..24

*Claude's sitting, in the session `runbooks-review`, on the user's request in chat (the runbooks reviewed
against the plan's recent revisions, `gitlab.md` against `make gitlab-up` with and without the runners).
No AWS call: the code, the pipeline files, the stage logs and the battery's snapshot of 2026-10-22 01:53Z
in Stage 18's worktree were read, and `./scripts/slices.py up --env production --dry-run`, which runs
nothing.*

- **[Claude] Which runner takes which job**, read from the pipeline files: `awsds/app-etl`'s `pages`
  extends `.gates-uv` and carries `awsds-test` (since the template's first commit, 2026-10-14), so
  `main`'s pipelines run on the test runner; the build runner's untagged jobs are `app-etl`'s
  `build-image`, `scan-gate`, `store-bundle`, `release` and `production-gate` on a tag, `dev-env`'s
  `build-images`, `scan-base` and `scan-dev-env` on a release tag, and `deploy-image`'s
  `build-deploy-image` on a web pipeline. The help text and `gitlab.md` §U of 2026-10-24 named "Pages on
  `main`" among them; both corrected.
- **[Claude] What the session targets do**, read from `slices.py`: only `up` checks the hub, and only
  the proxy refuses; `make gitlab-down` reads neither. `RUNNERS=0` leaves `runners/` unapplied, so runners
  an earlier `make gitlab-up` raised keep running. The dry run of `make up ENV=production` starts GitLab
  and applies `egress/`, `workloads-egress/`, `warehouse-compute/`, `runners/` and `probes/`, refusing
  `app/app-etl` and `orchestration` (refusal 7); with `build_runner` false, its `runners/` apply destroys a
  build runner.
- **[Claude] Corrected**: `gitlab.md` §S, §U (a table of the three forms, `BUILD=1`'s one-apply life,
  `make up ENV=production`'s effect, `RUNNERS=0`, the prices), §I, §C, §K (the runners' table, a build
  runner subsection, `awsds/deploy-image`'s assignment, the template procedure reused by a later change)
  and pass 3's session; `promotion.md` §H, §P and §T step 4, whose bare `make up ENV=production` before
  `production-deploy` would destroy the build runner `production-gate` runs on, now
  `ONLY=workloads-egress`, as is the waiting list's Promotion row; `dev-env.md` §B (a release runs on the
  three runners) and §E (the copy under `gitlab/` at 72 entries, read 2026-10-18; version 9 at 70);
  `claude-code-sagemaker.md`'s rebuild step; `scp-battery.md`'s instance-preference rows, which ran
  2026-10-22, each `ok`; `terraform-changes.md`, `sandbox/observability/` among the slices reading
  `alerts.auto.tfvars`; `log-debugging.md`, Stage 10's two log groups and the chain's reading order; the
  Makefile's help for `RUNNERS=0`, `BUILD=1` and `GROUPS`, which `production/workloads-egress/` takes
  since 2026-10-23.
- **[Claude] Left to the stages' own sessions**: the bare `make up ENV=production` in Stage 8 3.6's text
  and Stage 9 2.4's and 9.1's, each a record of what ran or a step a runbook now names with `ONLY=`.

## 2026-10-24 — 3.5's three persona memberships, by the user

*The user's hand, at the GitLab sitting of `runbooks/promotion.md` §H; Claude recording, in the session
that holds Stages 8 to 10.*

- **[user]** The Deployment Manager, Governance Manager and Dev-env Steward personas signed in once by
  SAML and were added by the administrator to `awsds/deployment-managers`, `awsds/governance-managers`
  and `awsds/dev-env-stewards`; `awsds/deployment-managers` joined `awsds/infrastructure` as Reporter
  and `awsds/dev-env-stewards` left it, and the mirror's job token admits `awsds/app-etl` in place of
  `awsds/dev-env` (Stage 8 decision 2). Reported in chat (*"Fiz os atos do §H: ... as configurações e
  memberships ..."*); no read of GitLab's members reaches them from the laptop.

## 2026-10-25 — 7.2, INT-13's VPC half: the console's host form in Data Governance offers no VPC

*Claude's hand, reading the AWS console through the user's Chrome session (Claude in Chrome, a tab of its own,
closed after) as the infrastructure user with `InfrastructureAccess` in Data Governance, `us-west-2`, at the
user's request; nothing created, no form submitted. About 18:51 UTC.*

- **[Claude] The pages**: *Developer Tools → Connections* lists no connection and its *Hosts* tab reads *"No
  hosts configured"*; *Create host* opens the form at `/codesuite/settings/connections/hosts/new`.
- **[Claude] The form**: *Select a provider* offers `GitHub Enterprise Server` and `GitLab self-managed`; *URL*,
  *"The endpoint of the server to connect to"*; *VPC configuration*, *"Choose to set up a network-connected host
  or a host with an Amazon VPC configuration"*, with two options: *No VPC*, *"If your GitHub Enterprise Server is
  only accessible in a VPC, configure details here. Otherwise, skip this step."* (the text names GitHub with
  `GitLab self-managed` selected), and *Use a VPC*, *"If the endpoint is accessible via a VPC you may configure
  this here."*. With *Use a VPC* marked and `GitLab self-managed` selected, the *VPC ID* selector (*"Choose the
  VPC for your configuration. Your VPC must be in the same AWS Region as your host."*) reads **`No results`**
  once loaded, and *TLS certificate - optional* appears for a private CA. No SCP names `codeconnections`, so the
  console met no organization policy.
- **[Claude] The reading**: a host for the private instance needs a VPC in the host's account, and Data
  Governance has none to offer (D22, D26): INT-13's answer, as expected. The *No VPC* form would try the public
  internet, where `gitlab.awsds.internal` does not exist; creating that host and running *Set up host* is the
  user's optional half, for the wording of the failed setup, deleted after. The accepted path stays the manual
  `git remote add` and push from inside a project (INT-09).

## 2026-10-25 — 7.2 closed on the VPC half, by the user's decision

*The user's decision in chat (*"Fico com a leitura da metade VPC; cancelo o formulário sem criar o host."*); Claude's
hand for the record. No AWS call.*

- **[user]** The *Create host* form cancelled, no host created; the *No VPC* attempt not run.
- **[Claude]** 7.2 and verification ix are closed on the reading above: INT-13's answer is *no*, the console
  offering no VPC in Data Governance for a GitLab self-managed host, and the accepted path stays the manual
  `git remote add` and push from inside a project. The waiting list keeps only §I step 6's GitLab settings for
  this stage.

## 2026-10-25 — the user's observation: Production's host form lists its VPCs; the path INT-13 lacked, read on AWS's pages

*The user's hand in the console (*"Notei que entrando em production, Developer Tools, Hosts, criar uma conexão
com gitlab lista as VPCs. Esse não seria um caminho possível de configuração?"*); Claude's reading of five AWS
pages (`docs/REFERENCES.md`). No AWS call, nothing created.*

- **[user]** In Production the same *Create host* form offers the account's VPCs under *Use a VPC*.
- **[Claude] The pages**: a GitLab self-managed host takes a VPC, subnets and security groups *"for the
  infrastructure where your host is installed"*, a TLS certificate for a private CA, and is set up with a GitLab
  administrator's PAT (`api`, and `admin_mode` if enabled); a connection on it is authorized by a GitLab user,
  and *"connections only provide access for the account that was used to create and authorize the
  connection"*. `codeconnections` connections are shared across accounts through RAM. SageMaker Unified Studio's
  Git connections live at the account level since 2026-07-30 (*Settings → Account settings → Git connections*),
  reach every domain and project in the account once enabled, and may come from another account through RAM
  with `AWSRAMPermissionsAmazonDatazoneDomainExtendedServiceAccess` at its latest version; *"all users who can
  sign in to any domain in the account have read and write access to all repositories on that connection"*,
  regardless of project membership.
- **[Claude] The reading**: the path exists, a host in Production's VPC-SharedServices, a connection on it, the
  connection shared to Data Governance and enabled there, which INT-13's row of 2026-09 did not have. Its cost
  is an identity flattening (every domain user writes as the one GitLab user who authorized the connection,
  against Stage 7's per-persona roles and the CE gate, Lesson 12), a service-managed ingress into
  VPC-SharedServices and an administrator PAT at setup; nothing in Stages 7 to 10 needs it. Recorded in INT-13,
  7.2, `SMUS.md`, `upstream-releases.md` and the waiting list as the user's decision, recommended not now; the
  first reading, the account-level Git connections page in Data Governance's SageMaker Unified Studio console,
  needs nothing up.
- **[Claude] The user's follow-up, how a connection authenticates** (the user guide's repository pages,
  `docs/REFERENCES.md`): a member brings no SSH key, PAT or password; the service clones the repository into the
  project's S3 bucket, shared by every member, and pushes and pulls with the connection's token, so a disabled
  connection leaves the clone and stops every push and pull. JupyterLab's Git panel and the terminal's `git`
  act on that clone, the terminal's changes showing on the *Repositories* page. The pages promise *"per-commit
  authorship"* and say nothing about where the author's name and e-mail come from; what GitLab records as the
  pusher is the connection's user. Today's spaces hold no such clone: INT-09's clone is made by hand in the
  space with the person's own GitLab credential and `git config`, a different channel.
- **[Claude] The user's second follow-up, several connections**: a host takes one or more connections, each the
  GitLab user who authorized it, who needs the Owner role on the repositories; but an enabled connection reaches
  every user of every domain in the account and the member chooses the connection when adding a repository, so
  several connections are several shared identities, not one per person. Binding a connection to a project by
  IAM (`UseConnection` on one ARN per project role) is conceivable and unmeasured, and would still be per
  project. Recorded in INT-13.
- **[Claude] The user's design, a low-privilege identity for the connection**: a dedicated Identity Center user
  signing in to GitLab by SAML (no local account), a Developer on the chosen projects alone, so the connection
  lists those repositories and pushes only to unprotected branches, `main` and the `*-v*` tags staying
  Maintainers' through merge requests the person opens. It narrows the shared identity to one low-privilege
  pusher and keeps the gate in GitLab. Unmeasured: the vendor's note naming the Owner role for the authorizing
  user, the author the service writes, the OAuth refresh past the SAML session, and the IAM narrowing. Recorded
  in INT-13 for the evaluation, if the path is ever wanted.

## 2026-10-26 — `awsds/app-etl`'s protected refs read free of Stage 18's branch

*Claude's hand; the project's API in the user's GitLab session, reads only. Time UTC.*

- **[Claude]** `protected_branches` and `protected_tags` of `awsds/app-etl` at 00:21: one protected
  branch, `main`, push and merge by Maintainers, force push off; one protected tag pattern, `v*`, created
  by Maintainers. `stage-18-staging`, Stage 18's branch, protects nothing any more: the leftover of
  2026-10-22 is read.

## 2026-10-26 — the readings before the acts: the instance settings, the host's outbound calls, 8.2's pre-flight

*Claude's hand, in the session that holds Stage 7 at the sitting of `runbooks/promotion.md` §N (the hub,
GitLab with its three runners and the tunnel up, raised by the user on 2026-10-25 at 20:07 UTC). GitLab read
through the user's Chrome session as the local administrator (Claude in Chrome, a tab of its own, closed
after); AWS read as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), reads only;
the two Terraform plans saved outside the repository. Times UTC.*

- **[Claude] The instance settings**, `GET /api/v4/application/settings` at 00:43: `signup_enabled` true
  with `require_admin_approval_after_user_signup` true (the user's choice of 2026-10-12);
  `auto_devops_enabled` true; `restricted_visibility_levels` empty; `usage_ping_enabled` true,
  `usage_ping_generation_enabled` true, `usage_ping_features_enabled` false,
  `include_optional_metrics_in_service_ping` true; `version_check_enabled` true;
  `gitlab_product_usage_data_enabled` true with `gitlab_product_usage_data_source` `database` and
  `snowplow_enabled` false; `update_runner_versions_enabled` true. The admin pages of 19.4.2 name them:
  **Metrics and profiling → Usage statistics**: *Enable version check*, *Enable Service Ping*, *Enable
  Service Ping Generation*, *Enable Registration Features*; **Metrics and profiling → Event tracking**:
  *Enable event tracking — Send event data to GitLab* and *Enable Snowplow tracking — Send event data to
  your own Snowplow collector*, *"Only one can be selected at a time"*; **CI/CD → Runners**: *Fetch GitLab
  Runner release version data from GitLab.com*; **CI/CD → Auto DevOps**: *Default to Auto DevOps pipeline
  for all projects*; **General → Visibility and access controls → Restricted visibility levels**: three
  checkboxes, *Public* the third; **General → New user account restrictions**: *Allow new user accounts*.
- **[Claude] The host's outbound calls**, `logs filter-log-events` on `/awsds/prod/proxy` for `10.30.52.94`
  from 2026-10-12 00:00 to 00:50 today (Squid's `awsds` format: destination, status, bytes from the server,
  bytes from the client): 9,313 lines, every one `200 TCP_TUNNEL`.

  | Destination | `CONNECT`s | From the client | From the server | First .. last |
  |---|---|---|---|---|
  | `events.gitlab.net:443` | 9,240 | 38.5 MB | 44.6 MB | 2026-10-12 14:56 .. 2026-10-26 00:45 |
  | `packages.gitlab.com:443` | 51 | 59 KB | 278.0 MB | 2026-10-12 14:12 .. 2026-10-25 20:08 |
  | `version.gitlab.com:443` | 14 | 27 KB | 81 KB | 2026-10-12 14:57 .. 2026-10-25 22:54 |
  | `gitlab.com:443` | 7 | 13 KB | 189 KB | 2026-10-12 18:18 .. 2026-10-25 20:14 |
  | `storage.googleapis.com:443` | 1 | 5 KB | 1.06 GB | 2026-10-12 14:12 |

  Stage 12's 4,049 are the first five days (729, 328, 814, 1,406 and 772); the count follows the use of the
  instance (1,970 on 2026-10-24 and 2,233 on 2026-10-25, the promotion sittings). `packages.gitlab.com` and
  the one Google storage call are the package installs and dnf's metadata; `version.gitlab.com` carries the
  version check and Service Ping; `gitlab.com` the runner release reading [inferred:
  `update_runner_versions_enabled` is the only setting that names gitlab.com].
- **[Claude] 8.3's up half**, `./aws/supplychain.py` with every profile at 00:47: 0 checks failed; `SC-1`
  running, `SC-10` three runners (a note), `SC-11` read in the three runners' user data, `SC-13` the backup of
  2026-10-25 03:01:03 made by 19.4.2; the persona profiles read `(failed)` in section 10, no session for
  them. The report is kept outside git for 8.3's diff.
- **[Claude] 8.2's pre-flight.** `production/tooling/` initialised in the worktree and planned with
  `-var-file=<project folder>/secrets/saml.auto.tfvars`: `No changes`; `plan -destroy`: `17 to destroy`,
  the instance, the data volume and its attachment, the two records, the `gitlab.rb` object, the host's role
  with its two inline policies, its managed attachment and the instance profile, the DLM role and policy,
  the two security groups and the status-check alarm. `production/runners/` reads
  `runner_security_group_id` and `gitlab_url` from this state and no other slice reads it, so the runners
  go before the slice does. The secrets' resource policies name the host's role as a string in
  `aws:PrincipalArn`, never as a `Principal`, so a re-created role keeps its reads. The backup bucket holds
  the backups of 2026-10-13, 2026-10-15 and 2026-10-25 (03:01:03, 14,233,600 bytes); the data volume
  `vol-072c3d3dc9883b104`, created 2026-10-12, has seven DLM snapshots, 2026-10-19 to 2026-10-25, which
  outlive the policy. The host's role holds `s3:GetObject` on the backup bucket, the restore's fetch. From
  the laptop, `/users/sign_in` answers `200` in about 0.9 s with the root at `$HOME/awsds-root.crt`.
- **[Claude] The runners**, `GET /api/v4/runners/all`: ids 1 (`awsds-prod-runner`), 3
  (`awsds-prod-runner-deploy`) and 4 (`awsds-prod-runner-test`), project runners, all `online` and idle.
- **[Claude] Coordination**: the Stage 9 session's manual job `production-warehouse-ddl` (#616, pipeline
  #102) and the Stages 7-10 session's Stage 10 exercises hold GitLab and the runners; the cycle waits for
  both, and the first act is asked of the user only then.

## 2026-10-26 — §I step 6: the usage data off, Auto DevOps off, Public restricted

*The user's hand for the decision and the first act, in their browser as the local administrator
`felipenoris`; Claude's hand for the rest, in the same browser session through a tab of its own (Claude in
Chrome), at the user's request (*"Abri uma sessão no chrome para você. Pode continuar por lá e fazer as
ações."*); read back from `GET /api/v4/application/settings`. No AWS call. About 01:00 to 01:15 UTC.*

- **[user] The decision**: the recommendation accepted whole: event tracking, Service Ping with its
  generation, the version check and the runner release fetch off; Auto DevOps off; Public restricted;
  sign-up kept on with admin approval; no `TM` row.
- **[user]** *Metrics and profiling → Event tracking → Enable event tracking* unchecked and saved
  (*"Desliguei "Enable event tracking""*). *Enable Service Ping* would not uncheck in the user's tab
  (*"observei que não consigo desmarcar"*).
- **[Claude]** In a tab of its own on the same session the checkbox unchecked at the first click, which also
  freed *Enable Service Ping Generation* (disabled while Service Ping is on); *Enable version check* and the
  generation unchecked too, *Save changes* of the Usage statistics form: *"Application settings saved
  successfully"*. Then *CI/CD → Continuous Integration and Deployment → Default to Auto DevOps pipeline
  for all projects* off, saved; *CI/CD → Runners → Fetch GitLab Runner release version data from GitLab.com*
  off, saved; *General → Visibility and access controls → Restricted visibility levels → Public* checked,
  saved; each with the same flash.
- **[Claude] Read back at 01:15**: `gitlab_product_usage_data_enabled` false, `snowplow_enabled` false,
  `usage_ping_enabled` false, `usage_ping_generation_enabled` false, `usage_ping_features_enabled` false,
  `version_check_enabled` false, `update_runner_versions_enabled` false, `auto_devops_enabled` false,
  `restricted_visibility_levels` `["public"]`, `signup_enabled` true with
  `require_admin_approval_after_user_signup` true. The forms re-submitted their empty fields as empty
  strings where the API had read `null` (`auto_devops_domain`, `default_ci_config_path`,
  `enabled_git_access_protocol`, `custom_http_clone_url_root`, `shared_runners_text`, the three
  `snowplow_*` strings), the same meaning.
- **[Claude]** The settings precede 8.2's backup on purpose: a restore carries the database, and a fresh
  host without one carries the defaults (Lesson 17). Whether the events stopped is read in
  `/awsds/prod/proxy` at the end of the sitting.

## 2026-10-26 — 8.1: the cycle, with the boot timed (verification vi)

*The user's hand for the two targets, run from a terminal of their own in this worktree, with the user's
authorization in chat (*"Sim, fazemos o ciclo 8.1-8.3 hoje."*); Claude's for the readings: EC2 as the
infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`), and `GET /users/sign_in` from the laptop
through the tunnel every five seconds. The two peer sessions were told before the first target (the Stages 7-10
session had agreed that this `make gitlab-down` is the sitting's last for GitLab, `make hub-down` staying its own;
the Stage 9 session's manual job `production-warehouse-ddl` had finished at 01:05:15). Times UTC.*

- **[user]** `make gitlab-down`: the three runners `terminated`, zero interface endpoints left in the account
  (the Stage 9 session had taken `workloads-egress/` down minutes before), the host's stop `User initiated
  (2026-10-26 01:24:33 GMT)`, `stopped` read at 01:25:35.
- **[user]** `make gitlab-up RUNNERS=0`: the host `running` with `LaunchTime` 01:29:03, the same address
  `10.30.52.94` (verification i, again); nginx answered `502` from 01:29:17 and the sign-in page `200` at
  01:30:45, **1 min 42 s from the start to the first HTTPS answer** (the poll's step is five seconds plus two
  calls); the 12 endpoints of `production/egress/` back by 01:31.
- **[user]** The SSM session for the backup refused at about 01:35: `An error occurred (TargetNotConnected)
  when calling the StartSession operation: i-0e661200795f0e62e is not connected`.
- **[Claude] Why**, from the serial console and `describe-instance-information`: `make gitlab-up` starts the
  `[D]` host before it applies `production/egress/`, so the agent came up at 01:29:16 with no `ssm` endpoint
  (created 01:29:56), resolved the public `ssm.us-west-2.amazonaws.com` (`44.248.101.66`), timed out with
  no route and logged `SSM Agent entering hibernation due to error` at 01:31:26; the host had no record in
  SSM until the hibernation's retry registered it `Online` at 01:51:26, twenty minutes after. The proxy saw
  only the two `packages.gitlab.com` calls of dnf's start. An `[E]` runner never meets this: its first boot
  comes after the endpoints. A session right after `make gitlab-up` waits for that retry, or
  `scripts/slices.py` applies `egress/` before it starts `tooling/`, a change for the session that owns
  the lifecycle script (runbook §U carries the reading).

## 2026-10-26 — 8.2: the fresh backup

*The user's hand in an SSM session on the host, Claude's reading of the bucket as the infrastructure user with
`InfrastructureAccess` (`awsds-infra-prod`). Times UTC.*

- **[user]** `sudo gitlab-backup create STRATEGY=copy`, from a Session Manager shell opened once the agent was
  `Online`.
- **[Claude]** The bucket at 01:56: `1792979588_2026_10_26_19.4.2_gitlab_backup.tar`, 15,073,280 bytes,
  `LastModified` 01:53:19, `aws:kms`, `Expiration` 2026-11-26 by `expire-current-versions`, beside the three
  of 2026-10-13, 2026-10-15 and 2026-10-25 (the gate before the destroy: a backup made by 19.4.2, the pin).

## 2026-10-26 — 8.2: the destroy and the re-apply of `production/tooling/`

*Claude's hand from this worktree, the slice initialised here, with the user's authorization in chat
(*"Autorizo o terraform destroy de production/tooling/ (17 recursos, volume de dados incluído) e o re-apply em
seguida."*), as the infrastructure user with `InfrastructureAccess` (`awsds-infra-prod`); both plans with
`-var-file=<project folder>/secrets/saml.auto.tfvars`, saved outside the repository. Times UTC.*

- **[Claude] The destroy**, `plan -destroy` then `apply` of the saved plan: `Apply complete! Resources: 0 added,
  0 changed, 17 destroyed`, 02:00:33 to 02:01:50. The attachment took 52 s (the instance stopped before the
  detach), the two records 16 s, the volume 10 s, the instance 11 s, the rest a second or less; no
  `DependencyViolation`, the runners being gone since 8.1.
- **[Claude] The re-apply**: `plan` read `17 to add, 0 to change, 0 to destroy` (02:02:15) and the apply ended
  02:03:24, `17 added`, 58 s: the new host `i-0b4cb5f62e65abf70`, the new data volume `vol-0e0fff3694f95fa63`
  (formatted by the first boot), the two records on the new address, the DLM policy `policy-0776691c894780872`,
  the status-check alarm, the role and profile under their old names. The first boot's markers and the first
  HTTPS answer are polled from the laptop (the serial console and `/users/sign_in`).
- **[Claude] The first boot**, read on the serial console: `=== awsds gitlab first boot: 02:02:56` (the
  instance launched 02:02:45), `installing gitlab-ce 19.4.2` at +53 s, the package through the proxy
  (`packages.gitlab.com` 73.5 MB, then `storage.googleapis.com` 1.07 GB, logged at 02:04:34), `gitlab
  Reconfigured!` at +471 s, `/-/readiness -> 200` at +482 s and `=== awsds gitlab first boot done:
  02:10:52 ===`, **8 min 07 s from launch to the end of cloud-init** (13 min 54 s on 2026-10-12, when the
  readiness probe waited five minutes). The console buffer keeps the tail alone, so the `rpm -q` line and
  the secrets' `restored from Secrets Manager` are read in `/var/log/awsds-gitlab-boot.log` at the restore.
  The agent registered `Online` at 02:16:32 with the endpoints already there. The new address is
  `10.30.39.111`, both records on it at 02:03; `dig` on the laptop answers it, while `curl` by name failed
  at once (`000` in 4 ms) and by `--resolve` read `200`, the macOS resolver's cache holding the old name
  [inferred]; the browser is read next.

## 2026-10-26 — 8.2: the restore on the new host (verifications ii, v and xv)

*The user's hand in a Session Manager shell on the new host, the output pasted in chat; Claude's readings
from the laptop: the sign-in page by address every five seconds, the proxy log, `./aws/supplychain.py` and
the API through the user's browser session. Times UTC.*

- **[user] The boot log**, `grep` on `/var/log/awsds-gitlab-boot.log`: `gitlab-ce-19.4.2-ce.0.amazon2023.aarch64`
  twice (dnf's line and `rpm -q`), **verification xv's first half: the rebuild installed the pinned release**;
  `restored from Secrets Manager`, **verification ii's restore half: the fresh boot took `gitlab-secrets.json`
  from its container**; `first boot done: 02:10:52`.
- **[user]** `aws s3 cp` of the archive into `/var/opt/gitlab/backups/` and `chown git:git`, with the host's
  role; `gitlab-ctl stop puma` and `stop sidekiq` (`ok: down`); the sign-in page went `502` at 02:20:46.
- **[user]** `gitlab-backup restore BACKUP=1792979588_2026_10_26_19.4.2`, 02:21:29 to 02:22:27: the
  database wiped and restored (six `ERROR: must be owner of extension pg_trgm | btree_gist | amcheck` lines,
  GitLab's documented noise for a restore run as the `gitlab` database user, no `version mismatch`;
  **verification xv's second half**), `Source backup for the database ci doesn't exist. Skipping`, the six
  repositories and their wikis restored (`unable to reset refs ... repository not found. Proceeding with a
  normal restore` on each, the empty Gitaly), uploads, builds, artifacts, pages, lfs, terraform states,
  packages, ci secure files, agent plan content, CI catalog bundles and external diffs each `done` in the
  same second (they live in the object-storage bucket, outside the archive), `authorized_keys` rebuilt,
  `Restore task is done`.
- **[user]** `gitlab-ctl reconfigure` (`3/779 resources updated in 14 seconds`, `gitlab Reconfigured!` at
  02:22:57), `gitlab-ctl restart` (ten services `ok: run`), `gitlab-rake gitlab:check SANITIZE=true` straight
  after: GitLab Shell's *Internal API available: FAILED - Internal API unreachable* and *Sidekiq: Running?
  ... no*, the two services still booting behind the restart [inferred from the timing]; the GitLab App block
  all `yes`: migrations up, the six projects with their namespaces, `Active users: ... 5`, hashed storage.
- **[user]** `gitlab-rake gitlab:doctor:secrets` at 02:25:07: every model `failures: 0`, `Ci::Variable`,
  `Ci::Runner`, `ApplicationSetting`, `User` and `Project` among them, `Total: 0 row(s) affected`: **the
  restored secrets file decrypts the restored database**.
- **[Claude] The sign-in page** by address: `200` until 02:20:46, `502` through the restore and the
  restart, `200` again at 02:24:49. **Verification v: from the destroy's start at 02:00:33 to the restored
  sign-in page, 24 min 16 s**, of which the first boot 8 min 07 s and the restore itself 58 s; the backup
  two minutes before the destroy.
- **[Claude] The API through the user's browser session, which survived the restore**: the six projects
  with their ids and `last_activity_at` as before the backup; the repository reads below.
- **[Claude] 8.3's diff**, `./aws/supplychain.py` with every profile after the restore (02:26), 0 checks
  failed, against the run of 00:47 with everything up: `SC-1` carries the new instance id, `SC-10` reads *no
  runner instance* (a pass) where it read three runners (a note), `SC-11`'s three runner lines became the
  note for an absent `[E]` runner, and `SC-13` names the new archive; every other line identical, `SC-3`'s
  container `last changed 2026-10-12` among them. **Only the instance, the `[E]` runners and the timestamps
  moved: nothing leaked into the wrong layer.**
- **[Claude] The proxy after §I step 6**: the old host's last `CONNECT` to `events.gitlab.net` at 01:08:32,
  then only dnf's two `packages.gitlab.com` at its restart; the new host, 02:02 to 02:27, `packages.gitlab.com`
  15 times and `storage.googleapis.com` once, no `events.gitlab.net` and no `version.gitlab.com`: **the
  settings travelled with the database, and the channel is closed.**
- **[Claude] The restored instance read from outside, 02:27 to 02:29**: `awsds/app-etl`'s `main` at
  `8d50f685` and its 14 tags, `v0.4.6` on that commit, as before the backup (a Gitaly read of the restored
  repositories); the six users and the runners' three records (ids 1, 3 and 4, read `online` on their
  restored `contacted_at`, their hosts gone since 8.1); the application settings of §I step 6 as set before
  the backup (`gitlab_product_usage_data_enabled`, `usage_ping_enabled`, `version_check_enabled`,
  `update_runner_versions_enabled` and `auto_devops_enabled` false, `restricted_visibility_levels`
  `["public"]`); Sidekiq's one process started 02:24:49, so `gitlab:check`'s two failures were the services
  behind the restart; the Pages site `https://app-etl-ffa1fa.awsds-pages.internal/` answering `302` to its
  OAuth sign-in, the private project's access control read from the restored database; the help page `200`.
  The administrator's browser session outlived the restore through its remember-me cookie (a sign-in
  recorded at 02:27:25); the laptop's resolver answered the new address by 02:28.
- **[user] The clone**, from the laptop over the tunnel at about 02:33: `git clone --depth 1
  https://gitlab.awsds.internal/awsds/app-etl.git` received 33 objects and `rev-parse HEAD` printed
  `8d50f6851af08f394e18ac17099a4e5db68b3fc4`, `main`'s commit before the backup: **a pre-backup repository
  clones cleanly from the restored host** (8.2's proof, the stage's lifecycle deliverable). The clone deleted.
- **[user] The sitting's last `make gitlab-down`** (the Stages 7-10 session's agreed final descent for
  GitLab): no runner to destroy, the 12 endpoints gone by 02:38:01, the host's stop `User initiated
  (2026-10-26 02:38:08 GMT)`, `stopped` at 02:39:13; the proxy left running for the hub's own descent, the
  Stages 7-10 session's. The bucket holds the four archives (2026-10-13, 10-15, 10-25 and 10-26), the newest
  expiring 2026-11-26. **Pass 4 is closed.** The sitting's GitLab bill: the host 20:07 to 02:39 and the
  rebuild's hour, the endpoints and the runners by `make status` at each descent.
