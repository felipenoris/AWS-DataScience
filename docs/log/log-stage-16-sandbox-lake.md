# Log — Stage 16 — The sandbox lake

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-16-sandbox-lake.md`](../plan/stages/stage-16-sandbox-lake.md).*

*Provenance is named by SUBJECT rather than by ordinal — the convention
[Stage 3's log](log-stage-03-networking.md) adopted. Identifiers are redacted as
`scripts/check-identifiers.py` requires; no substitution was needed below — ARNs are written without
their account segment, and sign-ins are named by permission set. All times UTC.*

*File written 2026-08-26 by Claude, on the user's request, at the close of pass 6. The whole stage ran
in one day — created in the morning sitting, closed in the evening one — so this is one dated section
with the day's four sittings inside it. **Every measurement the user pasted is quoted verbatim**; the
analysis around the measurements is the stage file's §"What ran", and this file does not repeat it:
this is the operator's record — what was done, by which hand, in what order.*

---

## 2026-08-26 — the whole stage, four sittings

### Sitting 1 — creation, preflight, the three applies (passes 0-3), and the finding

*Provenance: the stage file, the slice, the module bumps and every probe are Claude's; the
`objectives.md` line, the sign-ins, the adoption-vs-ownership decision and every authorization are the
user's. Applies run by Claude, each authorized per occurrence.*

- **[user]** Requested the stage — permanent per-SSO-group artifact storage, mounted into SageMaker
  Unified Studio projects — and wrote the requirement into `objectives.md` (step 0.1) in their own
  words, as a bullet in the SMUS list: *"connect to user's `sso-group` S3 bucket using SageMaker to
  read-write data to group's `sandbox-lake`"*.
- **[user]** Signed in as the **infrastructure user** — account **Sandbox**, permission set
  **`InfrastructureAccess`** — the identity behind every apply and every `s3control` write below.
- **[Claude]** Preflight (0.2-0.3): the tenant roster read back three groups, one-to-one with their
  permission sets; the D13 boundary names nothing of this bucket; and the account data CMK carries
  **no delegate-to-IAM statement** — the reading that made pass 2.2 load-bearing rather than
  paperwork. `./aws/sandboxlake.py` first run: clean baseline, nothing built yet.
- **[Claude]** Applied `sandbox/lake/` — **`12 added, 0 changed, 0 destroyed`**, re-plan `No changes`:
  the bucket (**no current-object expiry**, the only such bucket in the estate), the access role
  `awsds-sandbox-lake-access`, the Access Grants location `3b7613eb-…`, three standing grants.
  Battery 11/11 `pass`.
- **THE FINDING** — `sandbox/data/`'s first plan carried a second change nobody asked for: it would
  have stripped **two Lake Formation administrator seats SMUS created for itself** at the first
  project (2026-08-22). The apply **stopped**. **[user]** first chose adoption
  (`consumer-data-v0.4.0`), then — their own question, the same day — caught adoption freezing a
  service-managed list, and authorized the correction: **`v0.5.0`**, one declared create-time admin
  plus `ignore_changes` over the list, with `./aws/datalake.py` **`DL-13`** as the list's defence.
  Measured after it: three admins live, one declared, plan `No changes`.
- **[Claude]** Applied `sandbox/data/` reduced to the one key-policy statement
  (`AllowSandboxLakeAccessRoleViaS3`); the key read back three `Sid`s; `development/data/` re-planned
  **`No changes`** across every bump — the reading that attributed the finding to SMUS, not to the
  module change.

### Sitting 2 — the contrast pair and the laptop test (2.3 and pass 5)

*Provenance: the tunnel and the persona sign-in are the user's; every probe is Claude's, run as the
persona with the user's authorization.*

- **[user]** VPN up, signed in as a data-scientist persona — account **Sandbox**,
  **`DataScientistAccess`**.
- **[Claude]** 2.3 in the contrast form — three refusals, three independently-worded layers, one
  positive control: direct-as-persona (*"no identity-based policy allows"*), the other group's vend
  (*"You do not have READWRITE permissions to the requested S3 Prefix"*), the vended session outside
  its scope (*"no session policy allows"*); beside them the own-prefix vend succeeded and its session
  read back **`assumed-role/awsds-sandbox-lake-access/access-grants-…`**.
- **[Claude]** Pass 5: the `s3-read-write` sequence **unchanged** end to end. Discovery returned
  **two** grants with the lake's listed first — verification (ix)'s answer, and the `grants[0]`
  caveat added to that README. Write, list, read-back clean; `head-object` named `aws:kms` under the
  account data CMK — the key-policy statement exercised on the bucket's first object.

### Sitting 3 — the first project wired, the connection, and the notebook (pass 4)

*Provenance: every portal act and every notebook cell is the user's — pasted outputs quoted verbatim.
The grant, the trust apply and the CloudTrail/IAM readings are Claude's, authorized.*

- **[user]** Provided the pair off the project's overview page: the Stage 6 test project, id
  `avhvbqn37ty7m8`, user role `datazone_usr_role_avhvbqn37ty7m8_5hkjdsy3umpi1c`; confirmed the
  prefix is `sso-group-data-scientists/`.
- **[Claude]** §W's first exercise: grant `18229b9a-…` cut by hand (`READWRITE`, the group prefix, the
  project role); the trust entry applied through `var.wired_projects` — the role **NAME**, never the
  ARN, which carries the account id into a tracked table; battery 12/12 after fixing its own
  counting grain (SL-2 had counted trust statements as project roles).
- **[user]** Created the connection in the portal — **it worked first try**, and the form was exactly
  **four fields** (the list step 6.3 asks this file to keep): **Name** = `sandbox-lake`, **S3 URI** =
  `s3://awsds-sandbox-lake/sso-group-data-scientists/`, **Region** = `us-west-2`, and the **access
  role** `awsds-sandbox-lake-access` picked from the dropdown. Nothing more was demanded — no
  `S3AG*`/`iam:PassRole` complaint, so the access role's deliberate omission of the
  location-management statements stands measured. The S3 browser showed the pass-5 object; read and
  write through the Studio UI both worked — the user's words: *"Consegui ler e escrever arquivos pela
  interface do SageMaker."*
- **[Claude]** The CloudTrail principal reading (the other half 6.3 names), from full event JSON —
  the ResourceName lookup index misses service-side assumes: the connection used **both documented
  doors**. Two direct `sts:AssumeRole` of the access role by the project role (`externalId` = the
  project id, session tags `AmazonDataZoneProject` and `AmazonDataZoneDomain`, a scoping session
  policy, 1800 s) and `GetDataAccess` vends, each answered by a service-side assume
  (`invokedBy: access-grants.s3.amazonaws.com`). **Every session on the bucket is a session of the
  access role.**
- **[user]** The notebook readings. The other group's vend refused with the register's wording,
  pasted verbatim:

  > `An error occurred (AccessDenied) when calling the GetDataAccess operation: You do not have
  > READWRITE permissions to the requested S3 Prefix:
  > s3://awsds-sandbox-lake/sso-group-deployment-managers/*`

  The "direct un-vended" probe **did not refuse** (a 200 with the objects). The user's own kernel
  readings narrowed it, pasted verbatim: the credentials method is `container-role`, and `pip list`
  carries `aws_s3_access_grants_boto3_plugin 1.3.0`. The discriminator: a "direct" `get_object`
  returned **`b'hello'`** — plaintext through a key that delegates nothing to IAM, so only a vended
  access-role session could have decrypted it.
- **[Claude]** The second channel, as the infrastructure user: seven `GetDataAccess` events in the
  window — six `OK` (the kernel's session and the portal UI's session, from two different private
  addresses) and the one refusal; answered vends and service assumes matched **1:1**, the refused
  vend followed by none; and the project role reads back **zero inline policies**, three attached —
  all AWS-managed Studio documents, none naming the lake. **The SMUS image auto-vends "direct" S3
  calls; the in-image direct-refusal test is unrunnable by design; vended-only holds**, its
  direct-refusal proof staying sitting 2's laptop, where no plugin sits in the path.

### Sitting 4 — the revoke exercise and the close (pass 6)

*Provenance: every act this sitting is Claude's, authorized by the user ("pode rodar o passe 6"); the
log file itself is 6.3, written on the user's request in the same sitting. Timestamps are the
terminal's, UTC.*

- **[Claude]** The plan's sacrificial form — *same grantee, probe sub-prefix* — was found unmeasurable
  **before** it ran: the standing group grant covers every sub-prefix, so after the delete the re-vend
  would succeed through it and the refusal could never be read. The exercised form: grantee = the
  **operator's own reserved role** (`InfrastructureAccess`, which holds no standing grant), prefix
  `sso-group-data-scientists/probe/*` as planned.
- `20:13:23` — sacrificial grant `48b8f9f4-…` created: `READWRITE`, the probe prefix, the operator's
  role as grantee.
- **The battery did not fire on it** — `SL-4` classified the grant *standing …
  to InfrastructureAccess* and passed, printing `<group>/*` whatever the real sub-prefix. **The
  detector's first live anomaly found the detector's defect**: any `AWSReservedSSO_*` grantee counted
  as a tenant, and the printed scope was the top segment, not the grant's. Fixed while the anomaly
  lived — `SL-4` now carries the tenant table (grantee must be that group's own permission set, scope
  exactly `<group>/*`) — and the re-run read `fail … matches no tenant row` on the live grant, the
  four legitimate grants still passing.
- `20:14:07` — vended against the sacrificial grant (900 s, the minimum; expiry `20:29:08`).
  `20:14:49` — probe object written with the vended session: `aws:kms` under the account data CMK,
  session identity `awsds-sandbox-lake-access/access-grants-…`.
- `20:16:54` — **grant deleted** (§R's command). `20:16:55` — a re-vend still **answered** (+1 s),
  minting a fresh 900 s bearer *after* the delete; `20:17:13` — the re-vend **refused** (+19 s), in
  the register's own wording. **The vend door closes in under twenty seconds, and not in one** — and
  the true residual horizon is `delete + propagation + duration`, not just the credentials
  outstanding at the delete.
- `20:17:34-37` — the `20:14:07` credentials, forty seconds past the delete: **list, read
  (KMS-decrypted), and `DeleteObject`** — a write-class act on a revoked grant, doubling as the
  cleanup (a delete marker; the noncurrent version expires under the module's 90-day rule).
  **Revocation does not reach issued sessions.**
- `20:29:20` — the expiry probe, twelve seconds past the credential's stated expiry (`20:29:08`):
  **`ExpiredToken`** — *"The provided token has expired."* A different error class from every refusal
  above — the credential died of age, no policy in the wording — and it is the only thing that ever
  stopped the revoked grant's sessions.
- Battery after the delete: **12/12 `pass`, zero failed calls** — with the hardened `SL-4`. The human
  register diff against `docs/AWS_STATE.md`: three standing grants and one project grant, every row
  accounted for; the sacrificial pair was created and deleted inside this one entry and holds no row.
- **What §R's first exercise did not cover**: the trust-entry half — the sacrificial grantee has no
  trust entry, so removing one (and its `AWS_STATE` row) waits for a real project's death.
