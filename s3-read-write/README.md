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
- The persona's own permissions carry only the vending handshake — the customer-managed policy
  `awsds-org-project-storage-vending`, referenced by `DataScientistAccess` — which opens no object.

## Prerequisites — administered outside this library

1. **The persona's vending permission applied** — two slices, **members first**: the
   customer-managed policy `awsds-org-project-storage-vending` in each member account's
   [`foundation/`](../terraform-live/sandbox/foundation/persona-vending.tf), then the reference
   to it from `DataScientistAccess` in
   [`terraform-live/identity/sso/`](../terraform-live/identity/sso/permission-sets.tf). Applied
   in the other order, the permission set fails to provision until the objects exist.
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

| # | Command (persona, VPN up) | Before the policy is applied | After the policy, before the grant | After both |
|---|---|---|---|---|
| 1 | `aws s3control list-caller-access-grants --account-id <sandbox-account-id> --profile awsds-scientist-sandbox` | `AccessDenied` | empty list | the grant's row |
| 2 | `uv run examples/demo.py --profile awsds-scientist-sandbox` | fails at discovery | fails: "No grants found" | full read/write/list cycle |

The demo prints the vended identity — expect `assumed-role/datazone_usr_role_...`. **First full
run, 2026-08-23:** the identity came back as
`assumed-role/datazone_usr_role_<project>_<env>/access-grants-<uuid>`, and the write/list/read-back
cycle passed — which **answers the one unknown the strategy analysis left open**: SSE-KMS under
the project CMK works through a vended, scope-reduced session, with nothing granted to the
persona on either the bucket or the key.

**The tunnel question split in two rather than resolving once**, and the first run proved the
first half by failing on it: `sts:GetCallerIdentity` — which this library calls to learn the
account id `s3control` requires — takes the VPC's **`sts` interface endpoint**, so it presents a
VPC key rather than the Elastic IP. `DenyControlPlaneOffVpn` listed only *gateway* endpoint ids
at the time and denied it explicitly, **with the tunnel up**; the fix swapped that branch to
`aws:SourceVpc`. `s3control`, by contrast, has **no endpoint in this VPC**, so the vending calls
leave by the IGW on the Elastic IP. That second half is **derived from the endpoint lists, not
yet read** — the confirming CloudTrail event is named in `foundation/persona-vending.tf`.

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
- **Both member accounts, one object each.** Each copy of the policy names its **own** account's
  Access Grants instance, so nothing here is Sandbox-specific. Development's instance does not
  exist until that account's first project is born — until then the policy is simply inert
  there (an IAM policy may name a resource that does not exist).
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
