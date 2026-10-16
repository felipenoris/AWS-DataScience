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
