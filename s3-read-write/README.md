# `s3-read-write` — the project's S3 storage, from the laptop

A small Python library (boto3 as the only runtime dependency) that lets a data scientist,
**outside SageMaker Unified Studio and on the VPN**, read, write and list files in the S3
storage of their SMUS project — the same `awsds-sandbox-smus-projects` paths the Studio file
browser shows.

Strategy decided 2026-08-23 (option 1-A of the analysis): **credential vending via S3 Access
Grants**, the surface SMUS itself provisions. No bucket-policy statement, no KMS-policy edit
and no static persona grant on the projects bucket exists or is needed — the laptop borrows
the **project role**, scoped down to the project's prefix, for the lifetime of one vended
session.

## How it works

```
persona session (SSO, on VPN)                      Studio session
        │                                                │
        │ s3control GetDataAccess                        │ (same identity, different door)
        ▼                                                ▼
S3 Access Grants instance ──assumes──▶ datazone_usr_role_<project>_<env>   (the project role)
        │                                                │
        │ short-lived credentials,                       │
        │ scoped to the granted prefix                   │
        ▼                                                ▼
   s3://awsds-sandbox-smus-projects/<domain-id>/<project-id>/shared/...
```

- SMUS registers, at project provisioning, an Access Grants **location** covering the
  project's prefix, with the project role as the location's vending role (measured
  2026-08-23).
- A **grant** on that location authorizes the persona role to call `GetDataAccess` for the
  prefix; the vended session *is* the project role, so bucket access and the project CMK
  behave exactly as they do for Studio itself.
- The persona's own IAM policy carries only the vending handshake
  (`VendProjectStorageCredentials` in `terraform-live/identity/sso/`), which opens no object.

## Prerequisites — administered outside this library

1. **The persona statement** `VendProjectStorageCredentials` applied in
   [`terraform-live/identity/sso/`](../terraform-live/identity/sso/policies-data-scientists.tf)
   (this repository, same branch as this library).
2. **One grant per project** on the SMUS-provisioned location — a write to AWS, authorized per
   occurrence. Recipe (infrastructure user, Sandbox):

   ```bash
   aws s3control list-access-grants-locations \
     --account-id "$(aws sts get-caller-identity --query Account --output text --profile awsds-infra-sandbox-1)" \
     --profile awsds-infra-sandbox-1
   ```

   Take the `AccessGrantsLocationId` whose `LocationScope` is the project's prefix, and the
   persona role ARN from:

   ```bash
   aws iam list-roles --path-prefix /aws-reserved/sso.amazonaws.com/ \
     --query "Roles[?contains(RoleName,'DataScientistAccess')].Arn" --output text \
     --profile awsds-infra-sandbox-1
   ```

   Then create the grant, confined to the project's `shared/` scope — the scope the Tooling
   environment reports as its project-files location (`nonGitProjectRepositoryLocation`),
   while `dev/` is the environment's own working state (its `s3BucketPath` and
   `athenaOutputUri` both point into `dev/` — read from `get-environment`, 2026-08-23) and is
   deliberately not granted:

   ```bash
   aws s3control create-access-grant \
     --account-id "$(aws sts get-caller-identity --query Account --output text --profile awsds-infra-sandbox-1)" \
     --access-grants-location-id <location-id> \
     --access-grants-location-configuration S3SubPrefix='shared/*' \
     --grantee GranteeType=IAM,GranteeIdentifier=<data-scientist-role-arn> \
     --permission READWRITE \
     --profile awsds-infra-sandbox-1
   ```

   The grant is per project (each project has its own location), revocable with
   `delete-access-grant`, and visible with `list-access-grants` — it is the single object that
   opens the path, and deleting it closes the path without touching any policy. Note that
   `READWRITE` is Access Grants' write level and **includes `s3:DeleteObject`** — the service
   has no put-without-delete level, so the library's no-delete promise is only its own API
   surface, never a control.
3. **The VPN tunnel up** — the persona's `DenyControlPlaneOffVpn` covers the vending calls, so
   off-VPN the handshake itself is denied.

## First-run probe sequence

Each step distinguishes a different failure, in order:

| # | Command (persona, VPN up) | Before the statement applies | After statement, before grant | After both |
|---|---|---|---|---|
| 1 | `aws s3control list-caller-access-grants --account-id <sandbox-account-id> --profile awsds-scientist-sandbox` | `AccessDenied` | empty list | the grant's row |
| 2 | `uv run examples/demo.py --profile awsds-scientist-sandbox` | fails at discovery | fails: "No grants found" | full read/write/list cycle |

The demo prints the vended identity — expect `assumed-role/datazone_usr_role_...`. It also
answers, by its write/read-back cycle, the one unknown left open by the strategy analysis:
that the vended, prefix-scoped session passes SSE-KMS under the project CMK end to end.

One more first-run reading, owed back to `identity/sso`: **which branch of
`DenyControlPlaneOffVpn` the vending call rides**. Read the `GetDataAccess` CloudTrail event's
`sourceIPAddress`/`vpcEndpointId` — a gateway-endpoint id means the `aws:SourceVpce` carve-out
(the Stage 5 pass-4d split, the likely answer, since `s3-control.<region>` resolves inside the
S3 ranges the gateway route captures); the VPN EIP means the `aws:SourceIp` branch — and
replace the hedged comment beside `VendProjectStorageCredentials` with the reading.

## Usage

```python
import boto3
from s3_read_write import s3, vending

persona = boto3.Session(profile_name="awsds-scientist-sandbox")

# Which project prefixes can I reach? (no ids needed up front)
grants = vending.list_caller_grants(persona)
target = grants[0]["grant_scope"]  # s3://awsds-sandbox-smus-projects/dzd-.../<project>/shared/*

# Trade the persona session for a prefix-scoped project-role session.
project = vending.scoped_session(persona, target)

bucket, prefix = s3.split_s3_uri(target)
s3.list_objects(project, bucket, prefix)
s3.write_object_bytes(project, b"hello", bucket, f"{prefix}hello.txt")
s3.read_object_bytes(project, bucket, f"{prefix}hello.txt")
s3.upload_file(project, "local.csv", bucket, f"{prefix}local.csv")
s3.download_file(project, bucket, f"{prefix}local.csv", "roundtrip.csv")
```

Conventions follow the reference project [`benes3`](https://github.com/felipenoris/benes3):
every public function takes a pre-authenticated `boto3.Session` as its first parameter —
authentication lives in `vending`, object operations in `s3`, and the seam between them is a
plain session object. There is deliberately **no delete function** (the task is read, write,
list — an API-surface choice, not a control; see the recipe note above) and no automatic
credential renewal (vend again when the session expires).

## Limits worth knowing

- **Vended credentials are bearer tokens** for their lifetime (default 3600 s, min 900): once
  issued they work off-VPN too, the same accepted shape as the remote-IDE sessions (open
  question 14). Prefer short durations.
- **Sandbox only today.** The persona statement names only Sandbox's Access Grants instance;
  Development joins when its first project (and therefore its instance) exists.
- **One grant = one project × one persona role.** The grain is the persona role (every data
  scientist), which is this estate's declared entitlement grain — per-user attribution was
  declined by design (`docs/GOVERNANCE.md`, "the grain rule"). Note what this collapses:
  Access Grants never consults SMUS project **membership**, so once a project holds a grant,
  every `DataScientistAccess` holder can reach that project's `shared/*` from a laptop,
  member or not — strictly coarser than Studio's own membership gate. Accepting that on this
  surface is part of the 2026-08-23 decision, not a consequence of the Stage 5 grain rule
  (which was argued over the lake surfaces).

## Development

Independent `uv` project (Python 3.14, like the rest of the repository):

```bash
cd s3-read-write && uv sync && uv run python -c "import s3_read_write"
```
