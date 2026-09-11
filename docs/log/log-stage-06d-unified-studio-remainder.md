# Log — Stage 6d: Unified Studio, what 6a left owed

*The stage file is [`docs/plan/stages/stage-06d-unified-studio-remainder.md`](../plan/stages/stage-06d-unified-studio-remainder.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

---

## 2026-09-07 — readings taken ahead of the stage: 3.6 and 7.2

*Stage 6c's pass 6 is waiting on four `[user]` readings, so the two 6d steps that need nothing from
anybody were taken first. Each is a **lead time**, not a portal click.*

### 3.6 — the portal surfaces, measured against the Region's own catalog

- **[Claude] All four names exist in `us-west-2`** — read from
  `describe-vpc-endpoint-services`, not from the vendor table:

  | name | in the catalog | in an estate list |
  |---|---|---|
  | `logs` | yes | **yes** — it is in `vpc-egress`'s `core_services`, so **CloudWatch is already covered in every VPC** |
  | `sqlworkbench` | yes | **no** |
  | `sqlworkbench-v2` | yes | **no** |
  | `codeconnections.api` | yes | no — **Stage 7's** input (open question 26's `gitConnectionArn`), not this stage's |
  | `codestar-connections.api` | yes | no — same, and the older spelling of it |

- **[Claude] The finding is the asymmetry.** One of the two surfaces the optional table names is
  covered by accident — `logs` was in the core list from Stage 3 for a different reason — and the
  other, **Portal Query Editors, has no endpoint in any VPC**. Under design B that is not a slower
  path, it is **no path at all**: a portal feature that exists in the UI and fails on first use.
- **[Claude] What is not decided here, deliberately.** Both spellings exist, and which one the portal
  actually calls is a measurement that needs the feature opened — a step that belongs to whoever
  opens it. Adding both would be 0.020/h for a feature nobody has used; adding neither is the state
  today. **Recorded as a named gap**: the symptom will be a 403 or a timeout with `sqlworkbench` in it.

### 7.2 — which principal makes the remote-IDE call

- **[Claude] The answer is worse than the step feared.** 6a step 3.2
  attached two denies — `DenyRemoteSessionOnSomeoneElsesSpace` and `DenyRemoteSessionAsSomeoneElse`,
  both on `sagemaker:StartSession` — to the **six persona sets**, to *scope* the remote-IDE channel
  rather than deny it. Read back from Identity Center today, `DataScientistAccess` carries:

  ```
  Deny   DenyRemoteSessionOnSomeoneElsesSpace   sagemaker:StartSession
  Deny   DenyRemoteSessionAsSomeoneElse         sagemaker:StartSession
  Allow  ReadSageMakerStatus                    sagemaker:Search, List*, GetSearchSuggestions, Describe*
  ```

  **There is no `Allow` for `sagemaker:StartSession` anywhere in the set.** The only SageMaker Allow
  is read-only status. And `policies-sagemaker.tf` says in its own comment where the grant does live:
  *"these six sets are not where `sagemaker:StartSession` is granted — the project role is"*.
- **[Claude] So the pair is attached to a principal that cannot make the call, and absent from the
  principal that can.** Whichever way 7.5's CloudTrail resolves the caller, the conclusion holds:
  - if the laptop connects with the **persona's** credentials, the call fails for want of an
    `Allow` — an access-denied that is **not** the deny pair, and that reads like a broken feature
    rather than a scoping decision;
  - if it connects with the **project role**, it succeeds **unscoped**, because that role carries
    neither deny.
  Either way **the objective's scoping was granted by nothing** (Lesson 18, with Lesson 28
  underneath: the grant and the constraint are in two different slices, and neither file shows the gap).
- **[Claude] The repair the step already names is the right one, and it is not a new SCP.** An SCP would
  deny the feature rather than scope it. The estate has exactly one instrument that reaches a role a
  blueprint writes: **the D13 permissions boundary of 6a step 2.1**. The two conditions move there.
  **Not done here**: it changes a boundary on a blueprint-authored role, the boundary field is
  write-only (always `get-role`, never `list-roles`), and 7.5's CloudTrail is what names the role to
  attach it to.
- **[Claude] What this does not settle**: whether a space is created with remote access at all (7.3,
  the user's decision) and which of the three connection methods works (7.4). The reading above makes
  7.3's recommendation stronger rather than weaker — *on for one space, by hand, off as the default* —
  because the scoping everyone assumed was in place is not.

## 2026-09-07 — 7.1: the required set derived from the vendor's pages, and the Sandbox list already had it

*The step said to take it first because a missing endpoint is a slice edit with a lead time. There is
no missing endpoint. What the pages carry instead is three requirements the step never asked about
and one fact that re-frames 7.2.*

- **[Claude] Eight pages read, two of them the ones `REFERENCES.md` had carried since 2026-08-16
  without a consumer** — the SMUS admin guide's *Configuring remote access* and *Network configuration
  for remote access* — plus the SageMaker AI guide's remote-access family (the concept page, *Set up
  remote access*, *Set up Remote IDE*, the private-subnet pair, the ABAC page), the VS Code remote FAQ
  both AWS pages delegate to, and the `session-manager-plugin`'s own source for the one question no
  page answers.
- **[Claude] The space side needs seven names, and `sandbox/egress/` declares all seven.** The SMUS
  isolated-VPC table, read against the slice:

  | vendor row | service token | where the estate has it |
  |---|---|---|
  | STS | `sts` | `core_services` |
  | SSM | `ssm` | `extra_services`, 6c 5.5 |
  | SSM-Messages | `ssmmessages` | `extra_services`, 6c 5.5 |
  | SM Studio | `sagemaker.studio` | `extra_services`, Stage 3 |
  | SM Runtime | `sagemaker.runtime` | `extra_services`, Stage 3 |
  | SM API | `sagemaker.api` | `extra_services`, Stage 3 |
  | DataZone | `datazone` | `extra_services`, back at 6c 5.2 |
  | DataZone FIPS | `datazone-fips` | **not declared, not needed** — a compliance variant |

  The SageMaker AI guide's private-subnet page adds only `ssm` and `ssmmessages` *"in addition to the
  standard set"*. **`ec2messages` is on neither page** — 6c 5.5's trio was two-thirds this channel's
  answer; the third entry serves the probe hosts, which is the reason it was added. **No slice edit.**
- **[Claude] The endpoint policy already carries the vendor's recommended branch.** AWS's page asks
  for `aws:PrincipalIsAWSService: true` on the `ssm` and `ssmmessages` endpoints, because the space's
  SSM registration is made by an AWS service principal that carries no `aws:PrincipalOrgID`.
  `vpc-egress`'s policy has had exactly that second statement (`AllowAWSServicePrincipals`) since
  Stage 3, for flow-log delivery — so the registration passes statement 2 rather than dying at
  statement 1, and a refusal at the endpoint is **not** one of 7.4's failure modes.
- **[Claude] The laptop side needs five names and the tunnel plane is `open`.** The SageMaker AI
  guide's local prerequisites: `ssm.<region>.amazonaws.com`, `ssm.<region>.api.aws`,
  `ssmmessages.<region>.amazonaws.com`, `ec2messages.<region>.amazonaws.com` — plus
  `api.sagemaker.<region>.amazonaws.com`, which Methods 2 and 3 call from the laptop for
  `StartSession` itself. Since the 2026-09-07 decision the tunnel plane refuses nothing, so the list
  is a diagnosis aid, not an ACL edit. **What is left is whether each program honours the proxy:**
  `aws` does (botocore). `session-manager-plugin` dials with gorilla's `websocket.DefaultDialer`,
  whose `Proxy` field is `http.ProxyFromEnvironment` — read from `websocketutil.go`, not measured —
  so it honours `HTTPS_PROXY` **when the variable reaches its process**. That is the catch: Method 1's
  deep link opens VS Code from the browser, and a macOS app opened that way inherits no shell
  environment (issue #67's neighbour), so the plugin dials `ssmmessages` directly, the WireGuard host's
  FORWARD chain rejects it, and the symptom is a **timeout** (Lesson 55). Method 3 from a terminal
  that exported the variables is the only method whose process tree the user controls. Written into
  7.1 and 7.5 so the first timeout is diagnosed as the environment and not as the endpoint set.
- **[Claude] Three requirements the pages carry that the step did not ask about**, each checked
  against the estate the same sitting:
  - **≥ 8 GB of memory**, and `ml.t3.medium` — the estate's default and its only measured Studio
    price — is named **unsupported**. `ml.t3.large` and `ml.m5.large` are inside
    `sagemaker-denies`' ceiling, and **neither is priced** in `PRICING.md` §8: a measurement owed
    before 7.3, not an estimate (Lesson 6).
  - **SMD ≥ 2.7, or a BYOI carrying `curl`/`wget`, `unzip`, `tar`, `gzip`** — `images/base/` is
    `sagemaker-distribution:4.3.0-cpu` and installs `curl` and `unzip`; and **TIP must be off** —
    delivered `false` and non-editable by 6a decision 2, which named this feature as its reason.
  - **The VS Code server is downloaded by the space**, from `update.code.visualstudio.com` and
    `vscode.download.prss.microsoft.com` (extensions: `marketplace.visualstudio.com`,
    `*.gallerycdn.vsassets.io`). The vendor's private-subnet answer is an HTTP proxy with those names
    allowed — on this estate a **compute-plane widening**, the plane the user's rule keeps
    restricted. Two shapes avoid it: VS Code's `remote.SSH.localServerDownload = always` with
    `remote.downloadExtensionsLocally = true` (the laptop downloads on the open plane and pushes
    through the SSH tunnel), and AWS's pre-packaged tarball installed by a lifecycle configuration
    from S3. Recorded as **decision due 5**, recommended: the client settings.
- **[Claude] The pages re-frame 7.2.** The SMUS
  guide names the **project role** as the principal that must hold `StartSession`, and says AWS's
  managed policy *"has already been updated to provide access for the Spaces they own"* —
  conditioned on `AmazonDataZoneProject` and `datazone:userId`, the same two tags as the estate's
  denies, in **Allow** form, on the principal that makes the call. Three consequences:
  - **The method decides the perimeter.** With the deep link the portal makes the call server-side as
    the project role — `DenyControlPlaneOffVpn` never sees it, the portal is reachable off-VPN
    (INT-16), the data channel is a token-bearing WebSocket — so **that method is usable entirely off
    the VPN**, and 7.5's expected reading (*the proxy's Elastic IP as `sourceIPAddress`*) is wrong for
    it: the address will be AWS's. With SSH or the Toolkit the laptop's credentials call it and the
    VPN statement applies.
  - **The persona pair would deny everything, not scope.** A persona's SSO session carries no
    `AmazonDataZoneProject` or `datazone:userId` principal tag, so `StringNotEquals` against an
    unresolvable variable is true for every space. The guard `policies-sagemaker.tf` describes —
    *"a deny is what survives someone else granting it"* — is a kill-switch, not a scoping.
    The 2026-09-07 morning reading said *granted by nothing*; the precise sentence is **scoped by
    AWS's Allow on the project role if that policy is attached, and by nothing of ours**.
  - **No method is both VPN-bound and scoped today.** Decision due 4 re-framed: choose the method
    first, after 7.4/7.5 read each one's caller and address. Recommended if VPN-only is to be true of
    this channel: Method 3, a tag-scoped Allow on the persona sets keyed on something a persona session
    carries (the vendor's ABAC example uses `IDC_UserName` through Identity Center's attributes for
    access control; the one space is tagged by hand at 7.3), the pair rewritten to that key, and
    `StartSession` **denied on the D13 boundary** so the deep link's path closes.
- **[Claude] One reading not taken**: whether the Sandbox project
  role actually carries AWS's conditioned Allow — `list-attached-role-policies` and the inline
  documents, as `awsds-infra-sandbox-1`. The SSO session had expired; the user was asked for the
  sign-in (infrastructure user, `Sandbox`, `InfrastructureAccess`). It decides whether the deep-link
  path is *AWS-scoped* or *unscoped*, and nothing above changes with the answer except that word.

## 2026-09-07 — the session audited, the documentation swept for 6b/6c, and the plans re-cut

*Done at the user's request after 7.1, in this order: the transcript against the logs, then every living
document against what 6b and 6c built, then the plans for what remains.*

- **[Claude] The log audit found nothing missing from the session's final stretch** (the messages from
  2026-09-06 23:27 to 2026-09-07 05:13, read from the transcript): 6.1's four readings verbatim, the
  client-plane inversion, issue #67, the ULA, Lessons 55-58, 2.6/2.4, 6.7 and this stage's first readings
  each have a section in the 6c or 6d log. What said less than the repository knew were the **living
  documents**, not the logs.
- **[Claude] Twenty-five files corrected in the sweep**, found by three regex families (network terms,
  account terms, plane and remote-IDE claims) over every non-historical document. `conventions.md` §6
  still put a NAT in every `egress/`, the WireGuard host *and* a NAT instance in `sandbox/vpn/`, the
  buildbox in Sandbox, and carried **two `staging/` blocks** — one the migrated tree, one the planned
  target — now merged; `terraform-live/README.md` counted 26 slices, said *"no `staging/`"* and kept the
  VPN anchors in `sandbox/foundation/`; the root README pointed at `sandbox/vpn/peers.auto.tfvars`;
  GLOSSARY, `architecture.md` (the tree, the four roles) and `institutional-delta.md` still had four
  environments and a Development account; PRICING and `cost-model.md` carried the design-A hour and eight
  zones; `AWS_STATE.md`'s *"no Staging"* and *"one NAT per account"* rows stood unstruck; INT-21 read
  *"half built"*; `vpn.md` still said IPv6 was *"deliberately black-holed"* — Lesson 56's own sentence,
  in the runbook that lesson came from; the scp-battery and terraform-changes runbooks and Stage 11 named
  `awsds-infra-dev`; D15, D36 and D38 kept predictions as facts (`pages.internal` *"stands"*, *"three NAT
  gateways to destroy"*); both stage indexes read *not started* for 6c and 6d. Historical prose in the
  stage files and the logs was left alone — those are records.
- **[Claude] Three plans re-cut.** 6c's pass 6 into owned sub-steps — 6.2, 6.4, 6.5, 6.6, each `[user]`
  half named, the union trim and the `removed {}` in their order, `VP-3` widened to every account (it
  reads Production alone today, Lesson 31) — with its Status row taken from *"passes 0 and 1"* to the
  truth and two verifications answered. 6d's step 7 around the method finding: the per-method table,
  7.3-7.9 (`./aws/remote-ide.py` is 7.9), decision due 6 for the names step 3 will produce — **`conda`
  and CRAN are not on the compute plane**, and CodeArtifact needs no Sandbox endpoint because
  `.amazonaws.com` is — and 4.1/4.4 read against the vendor: the **`Workflows` blueprint is the
  provisioned MWAA shape**, not the serverless one D7 chose, and serverless workflows *"run with their
  own execution role and worker"*. Stage 7 against 6c as built: five corrections, the sharpest that the
  proxy has **no TLS listener**, so the leaf 2.4 planned for it is not issued.
- **[Claude] Three vendor pages re-read for the review, and none contradicted the plan**: ECR's
  pull-through page still says the first pull *"may require a route to the internet"* (Stage 7 quotes it
  right; 6c 5.9's measured fallback now ranks first); GitLab Runner's proxy page has the four layers 6.2
  lists; the SMUS blueprint and workflow pages are what re-cut 4.1.
- **[Claude] One script extended for a step that had no instrument**: `./aws/vpn.py --on-host` now prints
  the FORWARD chain (both families) and the nat `POSTROUTING` counters, so 6c 6.4 reads the REJECT
  rule's packet count across the user's attempt — the only place that refusal is legible (Lesson 55).
  Eighteen read commands; the ban list is unchanged.

## 2026-09-07 — the pending reading, two prices, and the space-path ceiling removed at the user's request

*After the sign-in (infrastructure user, `Sandbox`, `InfrastructureAccess`). Everything below is a read
except the Terraform change, which is authored, tagged and planned — and not applied.*

- **[Claude] The project role's policies — the reading 7.1 left pending.**
  One DataZone role in Sandbox, `datazone_usr_role_<project>_<env>`, under the boundary
  **`awsds-sandbox-project-boundary`** (D13's; `get-role`), with three AWS managed policies and no inline
  document: `SageMakerStudioProjectUserRolePolicy`, `SageMakerStudioProjectRoleMachineLearningPolicy` and
  the Bedrock knowledge-base service-role policy. **The second carries
  `AllowStartSessionForSpaceRemoteConnection`** — `Allow sagemaker:StartSession` on `space/*`, conditioned
  on `aws:ResourceTag/AmazonDataZoneProject = ${aws:PrincipalTag/AmazonDataZoneProject}` and
  `aws:ResourceTag/AmazonDataZoneUser = ${aws:PrincipalTag/datazone:userId}` — the vendor's page, verbatim,
  on the principal that makes the call. The role's own tags carry the project, domain, environment,
  `AmazonDataZoneBlueprint=Tooling`, the Spaces domain id and the VPC; the *principal* tags the conditions
  read come from the session SMUS opens, not from these. Nothing in 7.1's conclusions changes: the
  deep-link path is **AWS-scoped**, and by nothing of ours.
- **[Claude] The domain and its one space**: one SageMaker AI domain (`SageMakerUnifiedStudio-<project>-<env>-dev`,
  `InService`), one JupyterLab space at **`ml.t3.medium`**, **`RemoteAccess: DISABLED`**, owned by the
  user's profile. The field 7.3 toggles exists per space and reads back.
- **[Claude] Two prices measured** (Price List Query API, `AmazonSageMaker`, `us-west-2`; `ml.t3.medium`
  read beside them as the control and it returned the 0.050 `PRICING.md` already carries):
  **`ml.t3.large` 0.100/h**, **`ml.m5.large` 0.115/h**, JupyterLab and Code Editor identical;
  `sa-east-1` 0.161 (JupyterLab only — the offer has no Code Editor row for `t3.large` there) and 0.184.
  Two rows in `PRICING.md` §8; 7.3's pricing sub-step closed.
- **[Claude] Identity Center's ABAC pages read for decision 4**: attributes for access control are
  enabled on the instance (`CreateInstanceAccessControlAttributeConfiguration`, or **Settings → Attributes
  for access control**), a key is mapped to a value from the identity store, and it arrives in the account
  as a **session tag** readable as `aws:PrincipalTag/<key>` in every IAM policy type. The mechanism the
  `IDC_UserName` recommendation needs exists, and it is a console act in the Identity account.
- **[user] The instance-type ceiling no longer reaches spaces.** Asked mid-session: *"não colocar mais
  nenhum limite no tipo de instância que o usuário pode criar via Code Spaces"*. **[Claude]**
  `sagemaker-denies`' `DenySageMakerInstanceCeiling` moved from `Action: sagemaker:*` to **`NotAction:
  CreateApp, CreateSpace, UpdateSpace`** — the reach stays bounded by the key (a request carrying no
  `sagemaker:InstanceTypes` is untouched by `ForAnyValue`, as before) and now excludes the three calls
  that create or resize a space's app; jobs, endpoints and notebook instances keep the list. Read as
  *spaces exempt, jobs kept* — the user's sentence names spaces; dropping the ceiling entirely is one
  statement fewer if that is what was meant. **Simulated before it was tagged** (`simulate-custom-policy`,
  ten cases): `CreateTrainingJob`/`CreateProcessingJob` at `ml.p4d.24xlarge`/`ml.g5.xlarge` →
  **explicitDeny**, the same at `ml.m5.large` → allowed; `CreateSpace`/`UpdateSpace`/`CreateApp` at p4d/g5
  → **allowed**; `ListSpaces`, `DescribeDomain`, `s3:ListAllMyBuckets`, `glue:GetDatabases` with no key →
  allowed. Tagged **`sagemaker-denies-v0.2.0`** and **`sagemaker-prereqs-v0.4.0`** on the same commit (the
  boundary composes the denies by relative path, so its tag moves too); both callers bumped in the
  second commit; **plans read `0 to add, 6 to change, 0 to destroy`** in `identity/sso/` (the six persona
  sets, in place) and **`0 to add, 1 to change, 0 to destroy`** in `sandbox/sagemaker/` (the boundary
  policy, in place), the diff being the one statement. **Not applied** — the two applies (`identity/sso/`
  as `awsds-infra-identity`, `sandbox/sagemaker/` as `awsds-infra-sandbox-1`) wait for the word. **What it
  gives up**: an `ml.p4d` Code Editor space bills USD 30+/h and D12's budget notifies nobody;
  the Tooling idle shutdown bounds an idle space and nothing bounds a busy one.

## 2026-09-07 — the two applies, authorized in chat, and the ceiling read back from both objects

- **[Claude⚡] `identity/sso/` applied as `awsds-infra-identity`**: the six persona inline policies
  modified in place (`Modifications complete` on all six, 7-9 s each); re-plan **`No changes`**.
- **[Claude⚡] `sandbox/sagemaker/` applied as `awsds-infra-sandbox-1`**: `Apply complete! Resources: 0
  added, 1 changed, 0 destroyed` — the boundary policy `awsds-sandbox-project-boundary`, now at
  version **v2**; re-plan **`No changes`**.
- **[Claude] Read back from the live objects, not from the plan**: `get-policy-version` on the boundary's
  default version shows `DenySageMakerInstanceCeiling` as `Deny` with `NotAction`
  `[UpdateSpace, CreateSpace, CreateApp]` and the seven-type list unchanged;
  `get-inline-policy-for-permission-set` on all seven sets shows the same shape in the **six** persona
  sets and no ceiling statement in `AWSServiceCatalogEndUserAccess`, as before. `./aws/studio.py` reads
  **0 FAILED** — `US-8` all three blueprint-provisioned roles bounded, `US-9` both Sids in all six sets,
  `US-10` zero running apps; the seven persona and `ctadmin` profiles it could not authenticate are
  other `sso-session`s with no token (section 10), not findings.
- **What changed for a data scientist**: a Code Editor or JupyterLab space may now be
  created or resized at any `ml.*` type — from the portal (the project role, under the boundary) or by
  API (the persona set) — while a training, processing, tuning or transform job, an endpoint config or a
  notebook instance still refuses a type outside the seven.

## 2026-09-08 — the first working session under the proxy: 3.2 closed, 3.1 half taken, 3.3 read

*The user asked whether the plan anywhere tested a JupyterLab space's internet through the proxy, and
then ran the test the same night. Nothing was raised for it: `./scripts/slices.py status` read
`production/vpn` **UP**, `production/proxy` **UP**, `sandbox/egress` **UP** (27 resources), burn
**0.2040 USD/h**. The variables were exported by hand in the space's terminal — the durable delivery is
still 2.2's `ContainerEnvironmentVariables`, unapplied — and the space runs the **stock** image, not the
house image, which is why 3.1 is half taken rather than done.*

### [user] The terminal, verbatim

*(The `NO_PROXY` export carried the 28-entry value read from `terraform output -raw no_proxy` on
`sandbox/egress`; the identity output's account id and role ARN are elided here, per this folder's rule.)*

```
sagemaker-user@default:~$ curl https://pypi.org
curl: (6) Could not resolve host: pypi.org
sagemaker-user@default:~$ export no_proxy="$NO_PROXY" http_proxy=http://proxy.awsds.internal:3128 https_proxy=http://proxy.awsds.internal:3128 HTTP_PROXY=http://proxy.awsds.internal:3128 HTTPS_PROXY=http://proxy.awsds.internal:3128
sagemaker-user@default:~$ curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 https://pypi.org/
200
sagemaker-user@default:~$ curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 http://example.com/
403
sagemaker-user@default:~$ curl -s -o /dev/null -w '%{http_code}\n' --max-time 10 --noproxy '*' https://pypi.org/
000
sagemaker-user@default:~$ getent hosts sts.us-west-2.amazonaws.com && aws sts get-caller-identity
10.20.32.164    sts.us-west-2.amazonaws.com
{
    "UserId": "AROA47P7U4BDOUDA4B63F:SageMaker",
    "Account": "<elided>",
    "Arn": "arn:aws:sts::<account>:assumed-role/datazone_usr_role_<project>_<env>/SageMaker"
}
sagemaker-user@default:~$ pip download --no-deps -d /tmp/proxytest requests
Collecting requests
  Downloading requests-2.34.2-py3-none-any.whl.metadata (4.8 kB)
Downloading requests-2.34.2-py3-none-any.whl (73 kB)
Saved /tmp/proxytest/requests-2.34.2-py3-none-any.whl
Successfully downloaded requests
sagemaker-user@default:~$ curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 http://repo.anaconda.com/pkgs/main/noarch/repodata.json
403
sagemaker-user@default:~$ curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 http://cloud.r-project.org/src/contrib/PACKAGES
403
sagemaker-user@default:~$ curl -sL -o /dev/null -w '%{http_code}\n' --max-time 30 https://github.com/psf/requests/archive/refs/tags/v2.32.3.tar.gz
000
```

### [Claude] 3.2 is closed, and by two channels that do not share a failure mode

- **CloudTrail, from inside the account.** The `sts:GetCallerIdentity` the user typed
  (`aws-cli/2.36.31 … md/command#sts.get-caller-identity`, 03:49:25Z) carries **`vpcEndpointId`
  `vpce-0f5adbfef0071b8e5`** — confirmed by `describe-vpc-endpoints` as `com.amazonaws.us-west-2.sts`,
  Interface, private DNS on — `sourceIPAddress` **10.20.66.132** (the app ENI) and
  `clientProvidedHostHeader` `sts.us-west-2.amazonaws.com`, by the project role's `SageMaker` session.
  With `HTTPS_PROXY` set, the AWS call did **not** go to Squid: the 4d defect shape has not returned.
- **The proxy's own access log, from the other side.** The session's window carries **no AWS name at
  all**. An absence is weak evidence on its own and is not weak here: had `NO_PROXY` failed,
  `sts.us-west-2.amazonaws.com` would be a `CONNECT` line beside the others, because `.amazonaws.com`
  **is** on the `sandbox-foundation` plane — the proxy would have permitted it, and the call would have
  arrived carrying neither `aws:SourceVpc` nor `aws:SourceVpce`.
- `getent hosts` returning **10.20.32.164** for `sts` is the same address 6c step 6.2 recorded on
  2026-09-07 from a restarted space — an unplanned cross-check on the endpoint set.

### [Claude] 3.3 — what the proxy saw, and the GitHub redirect confirmed by name

`./aws/proxy.py --on-host` (authorized in chat; `ssm:SendCommand`) read **`PX-1`, `PX-2`, `PX-3`, `PX-5`
`pass`, `PX-4` the standing note** — five planes, entry for entry, the render current. The report does
not carry the access log, so the log group was read directly (`filter-log-events` on
`/awsds/prod/proxy`, `awsds-infra-prod`):

```
2026-09-08T03:48:58+0000 10.20.66.132 CONNECT pypi.org:443 200 TCP_TUNNEL
2026-09-08T03:49:10+0000 10.20.66.132 GET http://example.com/ 403 TCP_DENIED
2026-09-08T03:49:34+0000 10.20.66.132 CONNECT pypi.org:443 200 TCP_TUNNEL
2026-09-08T03:49:35+0000 10.20.66.132 CONNECT files.pythonhosted.org:443 200 TCP_TUNNEL
2026-09-08T03:49:35+0000 10.20.66.132 CONNECT pypi.org:443 200 TCP_TUNNEL
2026-09-08T03:49:44+0000 10.20.66.132 GET http://repo.anaconda.com/pkgs/main/noarch/repodata.json 403 TCP_DENIED
2026-09-08T03:49:48+0000 10.20.66.132 GET http://cloud.r-project.org/src/contrib/PACKAGES 403 TCP_DENIED
2026-09-08T03:49:53+0000 10.20.66.132 CONNECT codeload.github.com:443 403 TCP_DENIED
2026-09-08T03:49:53+0000 10.20.66.132 CONNECT github.com:443 200 TCP_TUNNEL
```

- **The redirect trap is now measured on a third source plane.** `github.com` is on the list and answered
  `200`; the release tarball redirects, and `codeload.github.com` — a name nobody put on any plane — was
  refused in the same second. Same shape as `public.ecr.aws` → CloudFront (2026-09-06, a build host),
  and the same remedy: read the new name out of this log, never widen to the namespace.
- **The `403`s are legible because the refused probes used `http://`** — over `https` the refusal is a
  CONNECT refusal and `%{http_code}` reads `000`, which is exactly what the tarball line returned to the
  user while the proxy was logging a named `403`.
- **The source address in every line is the app ENI, 10.20.66.132** — a spoke reaches 3128 over the
  peering, un-masqueraded, so the log is per-workload the same way the tunnel's is per-device.

### [Claude] The reading that is weaker than it looks

`curl --noproxy '*' https://pypi.org/` returned `000`, and the step wanted that read as *no default
route*. It is not: the user's **first** command, before the proxy variables were exported, returned
**`curl: (6) Could not resolve host: pypi.org`** — the Sandbox DNS Firewall, whose allow-list is the four
families of 6c step 5.7. So the `000` measured a **resolution** refusal, and the absent route was never
reached. Both facts are true — there is no default route, as code — but this measurement cannot separate
them (Lesson 42). **The routing half stays 6c step 6.3's probe**, which uses `checkip.amazonaws.com`: a
name inside `*.amazonaws.com`, so it resolves and then has nowhere to go. The `000` is not the route's
proof.

The same reading is the design working: with an explicit proxy the client never resolves the destination
— the name is handed to Squid — which is what allowed the DNS list to fall from 63 entries to 10.

### [Claude] What this closes, and what it does not

| | |
|---|---|
| **3.2** | **Closed** — two channels, above |
| **3.3** | **Read for this session** — the nine lines above; `PX-1`/`PX-2`/`PX-3`/`PX-5` `pass` |
| **3.1** | **Half taken.** Python measured end to end (`pip`, index **and** file host); `conda` and CRAN refused **by name**, which is decision due 6's evidence. **`uv`, `Pkg` (Julia) and R were not run** — a `curl` to a package host is a network reading, not a package manager's. And this was the **stock** image: 3.1 is written to be taken in the house image, where Julia and R are image-delivered, so the ecosystems that matter most to it are exactly the ones still owed |
| **3.4** | **Untouched.** The DataZone agent, the S3 Access Grants plugin and Amazon Q run in the server's process tree, which saw no `export` of the user's |
| **2.2** | Still the durable path. Everything above dies with the shell |

---

## 2026-09-08 — the second sitting: two components that never saw the proxy, and step 8

*The user kept working in the space after the entry above and hit two failures that look like the
allow-list and are not. Both were run by the user; the readings, the plane entry and the plan edits are
Claude's. Nothing was applied.*

### [user] `apt`, and the two runs whose identity is the measurement

*(The `Ign:` block repeats three times in each run — `apt`'s own retries. Elided as `[…]`; nothing else
is removed.)*

```
sagemaker-user@default:~$ sudo apt update
Ign:1 http://security.ubuntu.com/ubuntu noble-security InRelease
Ign:2 http://archive.ubuntu.com/ubuntu noble InRelease
Ign:3 http://archive.ubuntu.com/ubuntu noble-updates InRelease
Ign:4 http://archive.ubuntu.com/ubuntu noble-backports InRelease
[…]
0% [Working]^C
```

Then the six proxy variables were exported in that same shell — the 28-entry `NO_PROXY` and the four
`http_proxy`/`https_proxy` spellings — and the command was run again:

```
sagemaker-user@default:~$ sudo apt update
Ign:1 http://security.ubuntu.com/ubuntu noble-security InRelease
[…]
Err:2 http://archive.ubuntu.com/ubuntu noble InRelease
  Could not resolve 'archive.ubuntu.com'
Err:3 http://archive.ubuntu.com/ubuntu noble-updates InRelease
  Could not resolve 'archive.ubuntu.com'
Err:4 http://archive.ubuntu.com/ubuntu noble-backports InRelease
  Could not resolve 'archive.ubuntu.com'
Err:1 http://security.ubuntu.com/ubuntu noble-security InRelease
  Could not resolve 'security.ubuntu.com'
Reading package lists... Done
[…]
W: Some index files failed to download. They have been ignored, or old ones used instead.
```

### [Claude] What that proves: the export changed nothing

`archive.ubuntu.com` and `security.ubuntu.com` **are** on `proxy_allow_sandbox` — they have been since
6c step 4.9. So this is not the allow-list. It is not the proxy at all: the message is `Could not
resolve`, and **an explicit-proxy client never resolves the destination** — it hands the name to Squid.
A resolution attempt is therefore proof that `apt` was not using a proxy, and the refusal came from the
Sandbox DNS Firewall, whose ten entries are four families that do not include Ubuntu's archives and by
design never will.

**Why the export did not help: the two runs are identical.**
`sudo` on Ubuntu defaults to `env_reset`, and `http_proxy` is not in its `env_keep`: the variables were
stripped at the `sudo` boundary and `apt` ran with a clean environment. Not "the proxy failed" — *the
process never saw one*. This is the same class as 6c 5.8's *"the host is told in four places"*, arriving
on the notebook side, and it revises **2.2**: `ContainerEnvironmentVariables` sets a *process*
environment, which is exactly what `sudo` discards.

### [user] The repair, first attempt, using `apt`'s own option rather than the environment

```
sudo apt -o Acquire::http::Proxy="http://proxy.awsds.internal:3128" -o Acquire::https::Proxy="http://proxy.awsds.internal:3128" update
Hit:1 http://archive.ubuntu.com/ubuntu noble InRelease
Get:2 http://security.ubuntu.com/ubuntu noble-security InRelease [126 kB]
Get:3 http://archive.ubuntu.com/ubuntu noble-updates InRelease [126 kB]
Get:4 http://archive.ubuntu.com/ubuntu noble-backports InRelease [126 kB]
Get:5 http://security.ubuntu.com/ubuntu noble-security/main amd64 Packages [1240 kB]
Get:6 http://archive.ubuntu.com/ubuntu noble-updates/restricted amd64 Packages [1902 kB]
Get:7 http://archive.ubuntu.com/ubuntu noble-updates/universe amd64 Packages [2151 kB]
Get:8 http://archive.ubuntu.com/ubuntu noble-updates/main amd64 Packages [1562 kB]
Get:9 http://security.ubuntu.com/ubuntu noble-security/restricted amd64 Packages [1791 kB]
Get:10 http://security.ubuntu.com/ubuntu noble-security/universe amd64 Packages [1530 kB]
Fetched 10.6 MB in 3s (3608 kB/s)
Reading package lists... Done
Building dependency tree... Done
Reading state information... Done
41 packages can be upgraded. Run 'apt list --upgradable' to see them.
```

**10.6 MB at 3608 kB/s through the proxy** — the OS-package half of the compute plane, exercised for the
first time. `-o Acquire::http::Proxy` needs no environment and no sudoers change, which is why it is the
*test*; the durable form is `/etc/apt/apt.conf.d/01proxy` in the house image, plus a sudoers `env_keep`
so that a person's exported variables survive `sudo` for everything that is not `apt`. Both are now
2.2's.

**One incidental fact**: the packages are **`amd64`** — the only architecture reading this estate has
taken from inside a space, and it contradicts a string in the next section.

### [user] A Code Editor space, nothing configured, failing on its own startup

*A different space, a different app type, no proxy variables set anywhere. The user was installing the
`Anthropic/claude-code` extension. Excerpted — the `[Network]` failures are numbered `#69` through `#74`
and only three are kept.*

```
2026-09-08 12:21:23.328 [info] [Window] Resolving connection token (…studio.us-west-2.sagemaker.aws)...
2026-09-08 12:21:36.742 [info] [Window] Auto updating outdated extensions. amazonwebservices.amazon-q-vscode, amazonwebservices.aws-toolkit-vscode, ms-python.python, ms-toolsai.jupyter
2026-09-08 12:22:13.453 [error] [Window] An unknown error occurred. Please consult the log for more details.
2026-09-08 12:22:24.584 [info] [Window] Auto updating outdated extensions. amazonwebservices.amazon-q-vscode, amazonwebservices.aws-toolkit-vscode, ms-python.python, ms-toolsai.jupyter
2026-09-08 12:22:27.173 [error] [Network] #69: https://open-vsx.org/vscode/asset/Anthropic/claude-code/2.1.263/Microsoft.VisualStudio.Code.Manifest?targetPlatform=alpine-arm64 - error GET Failed to fetch
2026-09-08 12:22:27.654 [error] [Window] Error: getaddrinfo ENOTFOUND open-vsx.org
    at GetAddrInfoReqWrap.onlookupall [as oncomplete] (node:dns:122:26)
2026-09-08 12:22:27.666 [error] [Window] getaddrinfo ENOTFOUND open-vsx.org: Error: getaddrinfo ENOTFOUND open-vsx.org
2026-09-08 12:22:28.120 [error] [Window] Error: getaddrinfo ENOTFOUND open-vsx.org
```

Six `[Network]` failures, **four** `getaddrinfo ENOTFOUND open-vsx.org`, and the socket to the space
itself connected in 721 ms — the space works; its gallery does not.

### [Claude] Which side asked, settled by the shape of the error

The candidates are the **space's** VS Code server and the **laptop's** browser, and they resolve through
different resolvers. The laptop's DNS goes down the tunnel to `10.31.0.2`, which is `VPC-Networking`'s
resolver — and **`production/egress` leaves `dns_firewall` at its default `false`**, the module's own
variable saying *"false in the hub, which must resolve everything the proxy is asked to fetch"*. So a
laptop **resolves `open-vsx.org` successfully**; under the monitored profile it would then be *rejected*
by the host's FORWARD chain, and under split-tunnel it would simply work. Neither of those is
`ENOTFOUND`.

Only the Sandbox VPC has a resolver that answers this way. **The space asked.** `/awsds/sandbox/dns-firewall`
(30-day retention, the rule action beside the name) turns that from an argument into a record, and that
reading is step 8.2.

**The failure is not the allow-list.** `ENOTFOUND` means the server resolved the name itself,
which an explicit-proxy client never does — the same reading as `apt`, one layer up. Two components, one
cause: **no proxy in the process**. That is a cheaper repair than *"the component has no proxy support"*,
and the two have different fallbacks (D38's endpoint, then the per-VPC NAT contingency), only one of
them expensive.

**And the failing extensions are AWS's own.** `amazonwebservices.amazon-q-vscode` and
`amazonwebservices.aws-toolkit-vscode` update themselves at every space start. **Every Code Editor space
in this estate produces this failure, in silence**, and reads as a broken IDE rather than as a policy.

**One string is unexplained.** The requests asked for
`targetPlatform=alpine-arm64`; the JupyterLab space an hour earlier fetched `amd64` Ubuntu packages, and
the SageMaker Distribution image is not Alpine. It is more likely VS Code's own fallback than a fact
about the space, but nothing here measured it — `uname -m` and `/etc/os-release` from that terminal
settle it, and that is step 8.7. Recorded as a **string, not a finding** (Lesson 38).

### [Claude] What was authored, and none of it is applied

| | |
|---|---|
| `hub-anchors.tf` | **`open-vsx.org` added to `proxy_allow_sandbox`** (20 → 21 names) with the reasoning inline: why a gallery is the same class of path as `pypi.org`; why **this entry alone changes nothing** while the server has no variables; that the **asset host is unread** and, if the download fails after the manifest succeeds, its name is a `403` in `/awsds/prod/proxy` exactly as `public.ecr.aws` → CloudFront was; and that it propagates to `production-foundation` by the derivation — right today, and Lesson 51's fork condition named. `terraform fmt` clean, `terraform validate` **Success**, no `dstdomain` collision (there is no `.open-vsx.org` sibling) |
| Stage file | **Step 8 added** — seven sub-steps, 8.1 already done. 3.1 carries `apt`; 3.4 carries the gallery and hands it to step 8; **2.2 grew two image-side files**; decision due 6 records `open-vsx.org` as **taken by the user**, with `conda` and CRAN still open; the risk row's diagnosis order revised |
| Not done | **The apply.** A list edit reaches the host on the State Manager half-hour with no host replacement, so `PX-3` will read red between the two — expected, and 8.3 says to read it twice |

### [Claude] The decision the user took, and the qualifier it puts on the one that remains

`open-vsx.org` is allowed, on the user's instruction in this sitting. The argument is symmetry rather
than convenience: this plane already carries five package indexes, and an extension gallery is the same
kind of channel. Refusing it would not have been a narrower perimeter — it would have been the same
perimeter with one ecosystem missing for no stated reason.

Decision due 6 is written as *"every `403` the proxy
logs is a name to allow or a loss to record"*, and this name **never produced a `403`**: it failed at
resolution, upstream of the proxy, and the proxy's log has no line for it at all. So that decision's
instrument reads a **floor**, not the whole list — a missing name can fail without ever reaching the
log, and the second instrument for it is `/awsds/sandbox/dns-firewall`.

---

## 2026-09-08 — the third sitting: the attribution recorded, and the build plane stops being an allow-list

*The user read `hub-anchors.tf`, reported three more measurements from the JupyterLab space (Rust and
crates installed, GitHub cloned, random sites refused), asked a mechanism question about CNAMEs, and then
took a decision about the build plane. The readings, the code and the plan edits are Claude's; the decision
is the user's. **Nothing was applied.***

### [Claude] The mechanism question, answered — a CNAME is invisible to this filter, a redirect is not

The user asked whether the proxy allows a listed name whose DNS resolves into some CDN. **Yes, and the
reason is that Squid never looks.** `dstdomain` matches the hostname the client **requested** — the
`Host:` header, or the target of a `CONNECT` — and then Squid resolves that name itself and connects. No
CNAME chain is evaluated anywhere in the estate. So:

| what the client asks for | what Squid sees | outcome |
|---|---|---|
| `static.crates.io`, which is a CNAME into a CDN | `static.crates.io` | **allowed** — the CDN's name never appears |
| `github.com`, for a clone | `github.com` | **allowed** |
| `github.com` → **HTTP 302** → `codeload.github.com` | two requests, two names | first allowed, **second refused** (measured 3.1) |
| `public.ecr.aws` → **HTTP redirect** → a CloudFront distribution | two names | the second had to be listed by name (6c 5.8) |

**A CNAME and an HTTP redirect look alike from the outside and are opposite here.** A CNAME is resolution,
which this filter does not perform; a redirect is a new request with a new name, which is the only thing
this filter reads. The old DNS Firewall had it the other way round — it evaluated chains and needed
`TRUST_REDIRECTION_DOMAIN`, and never met a redirect at all (Lesson 53).

**One consequence**: because the control is *which names may be
requested*, an allowed CDN host is a front for whatever that CDN serves. D38 §6 already records domain
fronting through an allowed CDN as an accepted residual, in Stage 11's threat model.

### [Claude] 8.2 taken — `/awsds/sandbox/dns-firewall`, 2026-09-08 15:10-15:40 UTC, 358 events

`storedBytes` read **0** for this group and the streams were live; the field lags by hours, and a listing
of streams is the reading that settles it. The window covers both spaces.

| name | action | queries | source |
|---|---|---|---|
| `open-vsx.org.` | **BLOCK** | 8 | `10.20.65.56` |
| `idetoolkits.amazonwebservices.com.` | **BLOCK** | 20 | `10.20.65.56` |
| `idetoolkits-hostedfiles.amazonaws.com.` | *allowed* | 13 | `10.20.65.56` |
| `api.github.com.` | **BLOCK** | 12 | `10.20.65.56` |
| `raw.githubusercontent.com.` | **BLOCK** | 12 | `10.20.65.56` |
| `pypi.org.` | **BLOCK** | 8 + 8 | both spaces |
| `archive.ubuntu.com.` · `security.ubuntu.com.` | **BLOCK** | 4 each | `10.20.16.8` |
| `s3.us-west-2.amazonaws.com.` · `datazone.us-west-2.api.aws.` · `sts…` | *allowed* | 33 · 8 · 4 | `10.20.16.8` |

**8.2 is answered as predicted: the space asked.** `10.20.65.56` is a Sandbox address, and the ENIs are
gone (the spaces were stopped), so the two sources are named by their behaviour rather than by a lookup —
unambiguously: one queried `open-vsx.org`, `idetoolkits` and `api.github.com` (the **Code Editor**), the
other `archive.ubuntu.com`, `pypi.org`, `datazone` and the projects bucket (the **JupyterLab** space).

**Three names nobody had listed, and one of them is a domain this estate had not noticed:**

- **`idetoolkits.amazonwebservices.com` — `amazonwebservices.com` is not `amazonaws.com`.** A different
  registrable domain, AWS's, and `.amazonaws.com` on the plane does not cover a byte of it. Beside it in
  the same log, `idetoolkits-hostedfiles.amazonaws.com` **was** allowed — the two hosts of one feature,
  split across two domains, one covered and one not.
- **`api.github.com` and `raw.githubusercontent.com`.** The plane carries `github.com` as a **bare** name,
  and Squid's `dstdomain` matches a bare name **exactly**. Neither is covered — which is the same reason
  `codeload.github.com` was refused at 3.1, now stated as a property of the entry rather than as an
  incident.

**Two independent confirmations arrived free.** `pypi.org` BLOCK from `10.20.16.8` is the `curl` before
the export in 3.1; `archive.ubuntu.com` and `security.ubuntu.com` BLOCK from the same address is
`sudo apt update`. Both entries above were written from the terminal output alone; the resolver's own log
agrees with them.

**Every name is queried twice** — bare, and with `.us-west-2.compute.internal` appended by the VPC search
domain — and both forms are blocked. It doubles the log volume and is not a finding.

### [user] The decision: the build plane is not what the objectives restrict

Reading `proxy_allow_shared`, the user observed that it exists to serve the buildbox, that the buildbox is
today's stand-in for the CI/CD pipeline, and that a pipeline's external access is criticised **by the code
that defines it** rather than by a network list — the pipeline's whole job being to build the image for the
environment that *is* restricted. Decision: **the buildbox reaches the internet through the proxy with no
allow-list**, and `proxy_allow_shared` goes.

**Claude's reading agrees, and adds the practical half.** The list was a treadmill: every base image, every
package source, every registry redirect is a name somebody must read out of `/awsds/prod/proxy` and add.
`d5l0dvt14r5h8.cloudfront.net` was exactly that, and the comment carrying it said so — *"REVISION TRIGGER,
and it is a WHEN rather than an IF"*. A control whose maintenance cost is a refusal nobody can predict,
guarding a host whose real control is elsewhere, is one that gets widened in a hurry by whoever is blocked.

**One caveat was raised and accepted: a plane is a CIDR, not a host.** `10.30.0.0/16` is all of
`VPC-SharedServices` — the buildbox today, the GitLab runners from Stage 7. That is the intent, and it is
inherited by anything else that lands in that VPC for an unrelated reason (Lesson 29). Written into the
`.tf`, into D38 §6 and into the buildbox runbook: a host that should not have the open internet does not
belong in SharedServices.

### [Claude] What was authored

| | |
|---|---|
| `hub-anchors.tf` | `proxy_allow_shared` **deleted** with its CloudFront entry; `proxy_deny_shared = []` in its place; a second map `proxy_deny_by_plane` whose **membership is the mode**, so the merge no longer hard-codes `"allowlist"`. Two new preconditions: a plane in **both** maps fails at plan time; the "plane no peering generates" check reads both key sets |
| `aws/dns-allowlist.py` | The grammar reads **both** plane maps, both **required** — a missing deny map would make an `open` plane read as an allow-list with nothing on it, the exact inversion this parser exists to prevent. **`DN-4` rewritten rather than relaxed**: *"no plane is `open` except the ones a decision names"*, against `OPEN_BY_DECISION` whose values are the **reasons**, printed in the pass line. A new plane going open still fails (Lesson 50). Two stale paragraphs corrected — one still called DN-4 *"information, not a warning"* |
| `D38` §6 | **Amended in place**, dated, with what the amendment does **not** change: the three global denies, the absent default route, the security group's single port, and `sandbox-foundation` staying an allow-list. Plus what moved — a control from the network to code review — and the institutional delta that follows |
| Stage 6d | **Step 9** (six sub-steps), 8.2 closed with the reading, 8.6 re-aimed at the three names, deliverables/validation/decision 6 and a new decision 7 |
| `history.md`, `decisions/INDEX.md`, `institutional-delta.md`, `NETWORK.md`, `vpn.md`, `buildbox.md`, `buildbox/README.md`, `buildbox/main.tf` | the amendment carried to every place that described the build plane as an allow-list |

### [Claude] The readings taken, and the middle state to expect

- **`terraform plan` on `production/networking/`: `0 to add, 1 to change, 0 to destroy`** — the SSM
  parameter, with all four preconditions passing (a precondition failure fails the plan, so this is their
  proof as well).
- **`./aws/dns-allowlist.py`**: `DN-1` pass (20 resolvable names), `DN-2` pass (no `dstdomain` collision),
  **`DN-4` pass** naming both open planes with their reasons. The plane table now reads
  `production-foundation open 0`, `sandbox-foundation allowlist 21`.
- **`DN-3` fails, and its failure is the diff**: `sandbox-foundation: only in code ['open-vsx.org']`;
  `production-foundation: only deployed [the 20 names]`. Exactly the two authored changes and nothing else.

**The middle state to expect after the apply**: `DN-3` green immediately, `PX-3` green up to **half an hour
later** on the State Manager schedule, with no host replacement. A green `DN-3` beside a red `PX-3` is that
window, not a failure.

### [user] Three more friction readings from the JupyterLab space, all as designed

Rust installed and crates fetched (`sh.rustup.rs`, `index.crates.io`, `static.crates.io`,
`static.rust-lang.org` — four of the plane's entries); GitHub repositories cloned (`github.com`); random
sites off the list refused by Squid. Together with `pip` at 3.1 that is **Python, Rust and source** measured
end to end on the compute plane. Still owed by 3.1: `uv`, `Pkg` (Julia) and R, in the house image.

### [Claude⚡] The apply, authorized in chat the same sitting

One apply for steps 8 and 9 — the two edits are the same parameter in the same slice, and applying twice
was the named mistake to avoid. Recipe A, `production/networking/`, `awsds-infra-prod`
(`InfrastructureAccess` on `Production`).

```
aws_ssm_parameter.proxy_allowlist: Modifying... [id=/datascience/prod/proxy/allowlist]
aws_ssm_parameter.proxy_allowlist: Modifications complete after 2s
Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

Re-plan: **`No changes. Your infrastructure matches the configuration.`**

**The first link of the chain closed, and the second is owed.** `DN-3` went from the failure that *was*
the diff to `pass — 5 planes, entry for entry`; `DN-1`, `DN-2` and `DN-4` pass beside it, `DN-4` naming
both open planes with their reasons. **Code and parameter agree.** What no reading here can say is what
the proxy is *enforcing*: `PX-3` reads the running `squid.conf` and needs `--on-host`, an
`ssm:SendCommand` — a write API carrying only reads, so it is taken deliberately, and it is worth taking
only once the State Manager half-hour has passed. `PX-1`, `PX-2` and `PX-5` pass against the committed
file; `PX-4` carries its standing note.

**Still owed by step 9**: 9.5, one full build and push across the plane, which is the only thing that
exercises the deleted CloudFront entry's absence.

### [user] The running `squid.conf`, read on the host — the second link closes

*The user ran `./aws/proxy.py --on-host` and then an interactive `start-session`, pasting both files.
Claude verified the rendered list against the deployed parameter by hand, name for name.*

The drop-in's own header carries the timestamp that settles the ordering: **`Rendered
2026-09-09T00:01:22Z`** — the association run at 21:01:22 -03:00, and the parameter was written at
**20:58:42 -03:00**. The render is **after** the apply, by the file's own record rather than by
inference.

```
acl src_production_foundation src 10.30.0.0/16
http_access allow src_production_foundation

acl src_sandbox_foundation src 10.20.0.0/16
acl dst_sandbox_foundation dstdomain .amazonaws.com … github.com open-vsx.org
http_access allow src_sandbox_foundation dst_sandbox_foundation

acl src_tunnel src 10.90.0.0/24
http_access allow src_tunnel
```

| | |
|---|---|
| `sandbox-foundation` | **21 names, same order, same content** as the parameter — diffed, not eyeballed; `open-vsx.org` last |
| `production-foundation` | `dst_production_foundation` **gone**; a **bare** `http_access allow` in its place |
| `d5l0dvt14r5h8.cloudfront.net` | **absent from both files** |
| `squid.conf` part 1-4 | unchanged: `deny to_private` line 1, the port guards, the include, `deny all` last |

**The build plane now renders exactly like the tunnel**: two `open` planes, two bare allows, both sitting
**after** `deny to_private` and the port guards and **before** the backstop. "Open to the internet, never
open to the estate" is not a claim about this change — it is the position of the include in the file.

**One prediction was wrong in its detail.** Claude expected an empty
`dstdeny_production_foundation` ACL. There is none: the renderer emits **no ACL at all** for an empty
list, of either kind. So the observable signature of an `open` plane is `acl src_X` followed by a bare
`http_access allow src_X` — not a `dstdeny_` line, and somebody grepping for one would conclude the
change had not landed.

**A legibility note follows from the same rule.** `production-workloads` and
`staging-foundation` are `allowlist` with empty lists, so they render as **nothing** — they are absent
from the file entirely. On the host, *"a plane that refuses everything"* and *"a plane that does not
exist"* are indistinguishable. The behaviour is right either way (the backstop refuses that source by
name), and the typo case is caught upstream by the `.tf` precondition — but it is why the **parameter**,
not the rendered file, is the source of truth for which planes exist, and why `PX-3` compares the two
rather than reading either alone.

**Step 9's remaining item is 9.5**: one full build and push, the only thing that exercises the deleted
CloudFront entry's absence.

## 2026-09-08 — the fourth sitting: 9.5 exercised, and the allow-list would have refused this build

*The build and the push are the user's hand, in one buildbox session. Every reading below is Claude's,
taken afterwards from the registry and from the proxy's own access log — the user ran nothing to produce
them.*

### [user] The build ran, and both images are in the ECR

> Rodei o build completo das imagens, e publiquei no ECR com a tag v0.1.1

### [Claude] The push, read from the registry rather than from the report

`aws ecr describe-images` on both repositories, profile `awsds-infra-prod`:

| repository | tag | digest | stored | pushed |
|---|---|---|---|---|
| `awsds-prod-ecr-base` | `default-v0.1.1` | `sha256:a4b763a3…1ea6` | 3 959 751 977 B | 22:16:59 -03 |
| `awsds-prod-ecr-dev-env` | `default-v0.1.1` | `sha256:6916fc13…6d13` | 5 636 978 991 B | 22:19:07 -03 |

Both repositories are `IMMUTABLE` and both still carry `default-v0.1.0` from 2026-08-22, so the two tags
are four objects, not two — the digests above are the identity, the tag is the pointer (`SMUS.md`,
"the tag is not the identity").

### [Claude] What the build actually fetched — 196 requests

`/awsds/prod/proxy`, filtered to the build window. **196 requests, all from `10.30.47.211`**, a
`VPC-SharedServices` address — which is the first thing the reading confirms: the source matched
`acl src_production_foundation src 10.30.0.0/16` **by CIDR**, exactly as the plane is defined. 4.67 GiB
in 27 minutes 46 seconds, `00:39:55Z` → `01:07:41Z`.

| destination | req | MiB | on the 21-name list? |
|---|---:|---:|---|
| `d5l0dvt14r5h8.cloudfront.net` | 3 | 3758.5 | only on the deleted `proxy_allow_shared` |
| **`conda.anaconda.org`** | **155** | **368.2** | **no — on no list, of either plane** |
| `julialang-s3.julialang.org` | 1 | 277.2 | yes |
| `storage.julialang.net` | 2 | 222.7 | yes |
| `static.rust-lang.org` | 8 | 145.1 | yes |
| `archive.ubuntu.com` | 11 | 6.5 | yes |
| `security.ubuntu.com` | 5 | 4.5 | yes |
| `public.ecr.aws` | 4 | 0.1 | yes |
| `us-west.pkg.julialang.org`, `pypi.org`, `pkg.julialang.org` | 6 | 0.2 | yes |
| `10.31.0.1` | 1 | 0.0 | the boot probe — **403 `TCP_DENIED`** |

**The first line of the boot log read as the fix intended**: `pypi.org` 200, then `10.31.0.1` 403. The
probe corrected earlier the same day (it had asserted `example.com → 403`, which the amendment
falsified) now measures the control that survives an `open` plane — `deny to_private`, line 1 of
`squid.conf`, above every allow.

**`conda.anaconda.org` is on no allow-list.** Not on `proxy_allow_sandbox`'s 21 names, not on the
`proxy_allow_shared` that used to derive from them, and `.amazonaws.com` does not cover it. It is 155 of
the 196 requests and 368 MiB — and it could have been foreseen: 3.1 recorded on
2026-09-08 that **`conda` and CRAN are refused by name on the compute plane**. Nothing carried that
reading across to the build plane, because on the build plane it had never cost anything.

**So under the design this sitting replaced, this build fails.** The timing says where:

| | |
|---|---|
| `00:42:18` → `00:43:24` | `public.ecr.aws` — the manifest, 4 requests |
| `00:44:24` → `00:45:35` | the CloudFront distribution — **3.76 GiB of layers in 71 seconds** |
| `00:46:36` → `00:56:20` | `conda.anaconda.org` — 155 requests over ten minutes |

The refusal would have landed **one minute after** the 3.76 GiB pull completed, on the step after the one
the old allow-list had been patched for. The deleted comment called its own next revision *"a WHEN rather
than an IF"*, and the when was **the next build**.

The deleted list's CloudFront entry came from a failed `docker pull`, so what had been exercised against
it was the *pull* and nothing beyond: a list believed complete because it was only ever tested to its
first step.

### [Claude] Two readings the log gives away for free

**Squid is caching, and only for `apt`.** `archive.ubuntu.com` and `security.ubuntu.com` are the only
`GET` rows — apt speaks plain HTTP, so the proxy sees whole URLs, and one of the eleven came back
**`304`**. Everything else is `CONNECT`/`TCP_TUNNEL`, opaque by construction. Whatever caching the hub
does for a build, it does for the distro packages only.

**The `open` mode delivered precisely what it promised**: it restricted nothing and recorded everything —
every name, every byte, per request. The plane is not "unmonitored", it is *monitored instead of
restricted*.

### [Claude] The rebuild is the same recipe

`images/` carries **no commit** between `default-v0.1.0` and `default-v0.1.1` (last change `e49aa28`).
The two are the same Dockerfiles built seventeen days apart, and the entire delta is upstream drift:
`base` **+942 bytes**, `dev-env` **-11.8 MB**. That makes the patch bump the right shape, and makes one
property explicit: **the recipe is not reproducible
byte-for-byte**. A pipeline that assumes it is will report a change on every run and push a new digest
for none. Recorded in `buildbox.md` beside the spent-tag list, and in `SMUS.md`'s tag record.

### [Claude] 9.6 — nothing was written to the deny list

The build plane's deny list is empty, and this sitting adds nothing to it. There is no written policy
naming something a **build** may not fetch, and inventing one from this session's traffic would be the
allow-list treadmill in mirror image. Stage 11 owns the policy; this entry records that the list was
looked at, on the day the plane was first exercised, and left empty deliberately.

### [user] The teardown

The user brought `production/egress` down after the session. Verified: `production/egress` **down**,
`production/buildbox` **down**; estate burn back to **USD 0.2040/h** from the 0.3340/h the two doors cost
while a build is running. `production/vpn` and `production/proxy` remain up, as they are meant to be.

## 2026-09-08 — the fifth sitting: step 8 measured, and the setting works everywhere except the gallery

*The user applied the setting, restarted the space twice and pasted three logs. Claude read
`/awsds/prod/proxy`, `/awsds/sandbox/dns-firewall` and the VPC endpoints afterwards. Two of the three
readings below are **paired before/after comparisons the user did not set out to produce**: a space
restart gives the container a new address, so each restart cut the log into two non-overlapping windows
attributable by source.*

### [user] 8.7 — the terminal, and the unexplained string retires

```
sagemaker-user@default:~$ uname -m
x86_64
sagemaker-user@default:~$ cat /etc/os-release
PRETTY_NAME="Ubuntu 24.04.4 LTS"
VERSION_CODENAME=noble
ID=ubuntu
```

`x86_64`, glibc, Noble. **`targetPlatform=alpine-arm64` describes nothing in that container** — not the
architecture, not the libc, not the distribution. It is also not the cause of anything: the failure is
`getaddrinfo`, and a platform string sits in the URL *path*, downstream of resolution. Retired as VS
Code's own detection, which is what [Lesson 38](../plan/lessons.md) prescribed when it was written down
as a string rather than a finding. One coincidence recorded **without** promotion: `arm64` is the
**laptop's** architecture and the workbench runs in the laptop's browser (every stack trace is
`browser/workbench.js`), so a client-side probe is the likelier author than the server. Nothing measured
it; nothing depends on it.

> **Falsified the next day — 2026-09-09. The hypothesis above is wrong, and so is the sentence before
> it.** The Open VSX API, queried from the space, returns `targetPlatform: alpine-arm64` for this
> extension whenever **no platform is named** — at the root and at `/latest` alike — and `linux-x64` only
> when the path asks for it. So VS Code was not detecting a platform at all: the workbench queried the
> gallery, got that variant back as *the* version, and echoed its platform into the asset URL. The
> laptop coincidence was a coincidence. This paragraph stands as written because it records what was
> believed at the time; the reading that overturns it is in the sixth sitting below. **Lesson 38 twice
> over** — the string was correctly written down rather than believed, and then the *explanation* of it
> was believed one reading too early.

### [user] The environment inside the Code Editor, which answers a question 2.2 had left open

The terminal carries **no proxy variable of any kind** — and three lines say why that is a fact about the
*server*, not about the shell:

```
declare -x SUPERVISOR_ENABLED="1"
declare -x SUPERVISOR_PROCESS_NAME="codeeditorserver"
declare -x SAGEMAKER_APP_TYPE="CodeEditor"
```

The terminal is a child of the code-server process, which is a **supervisord program**. So the terminal's
environment *is* the server's environment, and reading one reads the other. That is the mechanism behind
2.2's note that a Code Editor app is not covered by a JupyterLab image configuration, and it is also why
candidate (b) has a shape: whatever writes those variables has to reach a supervisord program, not a
login shell.

### [Claude] 8.4 — the split is real, and it is the inverse of the prediction

The stage predicted *"gallery proxied, extension host not"*. **It is the extension host proxied and the
gallery not.**

The first restart cut the log cleanly: `10.20.102.237` ran 02:15:00→02:18:48Z and `10.20.79.130` ran
02:20:02→02:27:08Z, with **no overlap** — the same space, 74 seconds apart, before and after.

| name | before the restart | after |
|---|---|---|
| `idetoolkits.amazonwebservices.com` | DNS **BLOCK** ×20 | Squid **403** ×6 |
| `api.github.com` | DNS **BLOCK** ×12 | Squid **403** ×2 |
| `raw.githubusercontent.com` | DNS **BLOCK** ×12 | Squid **403** ×6 |
| `pypi.org` | DNS **BLOCK** ×8 | Squid **200** ×5 |
| **`open-vsx.org`** | DNS **BLOCK** | **DNS BLOCK ×24 — it did not move** |

After the restart the space made **98 proxied requests carrying 96 MiB**, including 52 MiB of AWS
language servers from `us-east-1`. `open-vsx.org` **never appears in the proxy log at all**, in any
window, from any address.

**So the diagnosis of the second sitting no longer covers this component.** *"No proxy in the process,
never a refused one"* was right at 12:21 and is false by 23:22: the process has one, the extension host
uses it, and the gallery does not. That is a **more expensive** class of failure than the one it replaces
— a component that ignores a configured proxy is not repaired by configuring the proxy somewhere else —
and it shifts the burden of proof onto (b) and (c), which deliver the same fact by another route.

### [user] The second restart, and it confirms the fix by confirming its absence

The user added the two names by hand and restarted again. `datazone.us-west-2.api.aws` **disappeared from
the proxy log entirely** and appears only in the resolver's, answered normally. The five remaining
refusals are unchanged in name and roughly in count, from both post-fix addresses. **A hand-patch that
removes exactly one row and leaves the other five is the cause confirmed**, not merely a symptom
relieved — which is what promotes 8.8 from a hypothesis about a data source to a defect with a
reproduction.

`open-vsx.org` was blocked 12 more times in the same window. The gallery result is now measured twice,
across two restarts and three container addresses.

### [Claude] 8.8 — one name per endpoint, where AWS answers for several

`datazone.us-west-2.api.aws` was refused **11 times** on a service that has an interface endpoint **in
this VPC**. Read from the endpoints rather than from the module's assumption:

| endpoint | names it answers for | in the generated list |
|---|---|---|
| `com.amazonaws.us-west-2.datazone` | `datazone.us-west-2.amazonaws.com`, **`datazone.us-west-2.api.aws`** | the first only |
| `aws.sagemaker.us-west-2.studio` | four, **two of them wildcards** | the first only |

`no-proxy.tf` reads `data.aws_vpc_endpoint_service.private_dns_name` — a **string**, the service's
canonical name — while the names AWS actually answers for live on the **endpoint**, in `dns_entry`, as a
list. The file already carries two hand-patches of exactly this shape: the gateway pair (a gateway
endpoint has no private DNS at all) and the `dualstack` spellings, added on 2026-09-06 after a build host
failed its first boot. **This is the third instance of one cause — the roster yields fewer names than the
resolver serves** — and `.api.aws` and `.app.aws` make it a *domain-family* problem rather than a
spelling one, exactly as `amazonwebservices.com` was at 8.2.

**The two repairs for a `403` are indistinguishable from the symptom.** A name with an endpoint
belongs in the bypass list, where the call keeps `aws:SourceVpce`; putting it on the proxy's allow-list
instead makes it *work* while sending it out through the hub as a public call. The first thing 8.6 asks
of a refused name is therefore not *may this be fetched* but **does this have an endpoint** — a question
the plane's list cannot answer and the endpoint roster can.

### [Claude] What step 8 now owes, and one name that fits no category yet

Five names are genuine allow-or-lose decisions (8.6): `idetoolkits.amazonwebservices.com`,
`raw.githubusercontent.com`, `api.github.com`, `sagemaker-unified-studio-mcp.us-west-2.api.aws`,
`ide-toolkits.app-composer.aws.dev`. **The asset host is still unread** — the gallery never reached a
redirect.

A sixth is in neither column. `dzd-<id>.sagemaker.us-west-2.on.aws` — the SMUS domain's own URL — is
**DNS-blocked** from every space address in every window read today: not in the bypass list, not on the
plane, and not resolvable. It has been failing throughout and nothing has attributed it. Recorded as an
open name, not a finding.

## 2026-09-09 — the sixth sitting: step 8 closes, and the compute plane loses source control

*The user ran every probe and took the decision; Claude read the logs, the service model and the
endpoints, and made the apply the user authorized. Two inferences Claude had committed earlier the same
night are falsified below, both in the same direction.*

### [user] The two probes — and the environment reaches what the setting could not

The gallery client was invoked directly, outside the running server:

```
$ ... && unset VSCODE_IPC_HOOK_CLI && code-editor-server --install-extension Anthropic.claude-code ...
Installing extensions...
Server returned 403
```

**No `getaddrinfo`.** Every earlier gallery attempt died at resolution; this one connected and got an
**HTTP** answer. So **the client honours `http_proxy`/`https_proxy` and ignores the `http.proxy`
setting** — and the plan had said, four hours earlier, that environment variables *"deliver the same fact
by another route, so neither is expected to reach a client that ignores `http.proxy`"*. That reasoning
treated two delivery routes as one fact. **They are read by different code, and only the setting is
ignored.** (b) and (c) went back to being the repair rather than being ruled out.

The `unset` is not incidental: with `VSCODE_IPC_HOOK_CLI` set, the `remote-cli` forwards the call into
the **already running** server and measures its environment instead of the shell's.

### [Claude] The `403` is Squid's, and it names the last unread host

The proxy log carries the whole install in sequence, from the space's own address:

| `03:32:00Z` | `CONNECT open-vsx.org:443` | **200** — the API, on the plane |
|---|---|---|
| `03:32:00Z` | `CONNECT openvsx.eclipsecontent.org:443` | **403** — the download, on no plane |

**`open-vsx.org` serves the API and `openvsx.eclipsecontent.org` serves the bytes.** That is the redirect
shape 8.6 predicted from `public.ecr.aws` → CloudFront and `github.com` → `codeload`, and the reason
8.1's single entry was never going to be enough: **it authorised the question and refused the answer.**
The negative control arrived free in the same minutes — the **tunnel** plane, which is `open`, reached
that host with a `200`, so the name was refused by this list and by nothing else.

### [Claude] The delivery mechanism, read from the service model — and it is step 2's question

Both candidates exist. `StudioLifecycleConfigAppType` includes **`CodeEditor`** (b), and
**`CodeEditorAppImageConfig`** exists with `ContainerConfig.ContainerEnvironmentVariables`, symmetric to
the JupyterLab shape 2.2 already plans to use (c).

**But neither attaches to a space.** `SpaceSettings.CodeEditorAppSettings` is a *different shape* —
`SpaceCodeEditorAppSettings`, carrying only `DefaultResourceSpec` and `AppLifecycleManagement`.
`LifecycleConfigArns` and `CustomImages` live **only** on `UserSettings.CodeEditorAppSettings`: the domain
default or a user profile, which in this estate the **`Tooling` blueprint** provisions.

**So the delivery question and INT-17 are the same question**, and 8.4 is not independent of step 2 after
all — it is blocked behind **2.4**, *does an attachment we make to a blueprint-provisioned domain survive
reconciliation*. Two mechanisms, one risk, which removes the argument for (b) as a bridge: it buys no
risk reduction over (c), only earliness.

### [user] Decision due 6, taken in full — and the first time it has subtracted

Allowed as one block, on the reasoning that each is the IDE working normally: the gallery's two names,
plus `idetoolkits.amazonwebservices.com`, `ide-toolkits.app-composer.aws.dev` and
`sagemaker-unified-studio-mcp.<region>.api.aws`. None has a VPC endpoint — the test that keeps an
allow-list entry from being a bypass-list one.

**Refused: `api.github.com` and `raw.githubusercontent.com`. Removed: `github.com`** — a name that was on
the plane, and that **worked**: 3.1 cloned a repository from a space the day before.

A name is judged not by whether it works but by whether an *interactive compute* plane should reach it,
and source control is the path by which code — and whatever a notebook has put beside it — leaves a
governed environment. `objectives.md` carries data-leakage protection as a requirement of its own; this
is that requirement costing something. **What it costs is written into the `.tf` beside the gap it
leaves**, so nobody re-adds the name as a bug fix: `clone`, `fetch` and `push` from a Sandbox space now
fail. **The build plane is untouched** — `production-foundation` is `open`, so the buildbox and the future
pipeline still reach GitHub, which is where a build belongs.

Claude noted the measured consequence before writing, and the user confirmed. `conda` and CRAN, this
decision's original two, remain undecided.

### [Claude⚡] The apply, and two gates that disagreed about one name

`0 to add, 1 to change`; parameter **6 → 7** at 01:24:39 -03:00; re-plan `No changes`; `DN-1`..`DN-4` all
pass.

**One name cost two rounds, and neither gate was wrong.** `check-tf-conventions` refused the literal
`us-west-2` in `sagemaker-unified-studio-mcp.us-west-2.api.aws` — a hard-coded region is a portability
defect that reads as data. Rewritten as `${data.aws_region.current.region}`, `dns-allowlist.py` then went
**red**, because it resolves `${var.region}` and **reports** any other interpolation as unresolved rather
than guessing. **Terraform says `No changes` for either form**, so the instrument was the only thing in
the toolchain that could tell the two apart. The `.tf` now carries why the form is what it is.

*A process note:*
the apply's output was piped through `tail -8`, which cut off the sentence saying what happened; a second
apply was then run on a spent plan and returned `Saved plan is stale`. The first apply had succeeded
(Lesson 46, in its smallest form).

### [user] `PX-3` green — the check that can see a removal

`sandbox_foundation allowlist 24` on the running host, **entry for entry**, the association having run at
01:31:18 after the 01:24:39 write.

**That verdict is what proves `github.com` is gone.** A drop-in lists what a plane allows and never what
it stopped allowing, so a removal leaves nothing a reader could grep for — an absence is indistinguishable
from a name that was never there. Only the parameter-against-host comparison can see one. It also resolves
the interpolation end to end: the host carries the region expanded, which no reading of the `.tf` alone
could confirm.

The running file shows **three** planes against the parameter's five, exactly as 9.4 recorded: an empty
`allowlist` plane renders as nothing.

### [user] 8.5 closes, on its own criterion

```
Installing extension 'anthropic.claude-code'...
Extension 'anthropic.claude-code' v2.1.266 was successfully installed.
rc=0
```

And the access log is the criterion the step was actually written to require — a `200` naming the gallery,
produced by the gallery client rather than by a `curl`:

| host | | |
|---|---|---|
| `openvsx.eclipsecontent.org` | **200** ×3 | **96.32 MiB** — the `.vsix` itself |
| `open-vsx.org` | **200** ×5 | the API |
| `idetoolkits.amazonwebservices.com` | **200** ×6 | was `403` |
| `sagemaker-unified-studio-mcp.us-west-2.api.aws` | **200** ×3 | was `403`; the interpolation, resolved |
| `ide-toolkits.app-composer.aws.dev` | **200** ×2 | was `403` |
| `api.github.com`, `raw.githubusercontent.com` | **403** ×15 | **refused by decision**, still asked at every start |

Five names moved `403` → `200` and the two refused ones did not. That is the decision, measured on both
sides, in one window.

### [Claude] What step 8 closes and what it does not

**Closed**: 8.1, 8.2, 8.3, 8.5, 8.6, 8.7. **8.4 has its answer but not its delivery** — the mechanism is
an *environment*, and the only place to attach one is the blueprint-provisioned domain, so it waits on
2.4. **8.8 is open**: the `no_proxy` generator defect.

**The thing that works is not the thing a user does.** Everything above is `code-editor-server`
invoked by hand with variables a person exported. **Opening the space and clicking Install still fails**,
because the server supervisord starts has none of them. Step 8 has therefore produced a *proof* and not
yet a *fix* (Lesson 5).

**The platform build was read, and it is `linux-x64`** — `anthropic.claude-code-2.1.266-linux-x64`. So
`code-editor-server` negotiates the platform correctly, and **8.7's second defect belongs to the browser
workbench alone**: the `alpine-arm64` it asks for is the registry's default reaching a client that named
none. The `.vsix` contingency is needed only where that path is in use.

**Installing it properly produced a third face of the same defect.** Into the server's own
`--extensions-dir`, the extension appears and the `Install` button goes — then **clicking it raises an
error**. Not an update: `claude-code` is **absent** from the `Auto updating outdated extensions` list,
yet the workbench fetches `Microsoft.VisualStudio.Code.Manifest` for the version **already installed**,
fails, and prints `An unknown error occurred`. That is the extension's **detail page**, which is a gallery
read. So the missing proxy costs three things rather than one: the startup auto-update, installing from
the UI, and **viewing an extension that is already installed** — which widens what step 2's delivery is
worth, since the fix is the same and the surface it repairs is larger than *"cannot install"*.

**The extension itself runs** — confirmed from the command palette. The two are cleanly separated: the
extension is fine, the IDE's marketplace surface is not, and the only broken action left in this space is
the one that reads the gallery.

**The procedure is written down.** [`sg-proxy.md`](../plan/runbooks/sg-proxy.md)
§*Installing an extension in a Code Editor space* carries the invocation with the reason for each
load-bearing part — three of which were learned by getting them wrong first — the reload it needs, what
stays broken afterwards so nobody reads the detail-page error as a botched install, and the `403` path
with 8.6's rule that a refused name **with** a VPC endpoint belongs in the bypass list and never on the
allow-list. It also says the two things that bound it: **per space, dies with the space**, and **only
until step 2 delivers the environment**.

## 2026-09-09 — the seventh sitting: 8.8, and the guard that moved with the reading

*Claude took every measurement, wrote the code and the documents, and ran the one apply the user
authorized; the user authorized the applies up front, took the two decisions below, and asked for this
entry. One inference Claude made mid-sitting was falsified by its own measurement and is recorded as
such rather than repaired silently.*

### [Claude] The defect measured before a line was written — sixteen of eighteen, not two

`describe-vpc-endpoints` on Sandbox, `DnsEntries` per interface endpoint. 8.8 had recorded two endpoints
answering for a name the generated list did not carry. The reading says **16 of 18**:

| endpoint | names it answers for, beyond the canonical one |
|---|---|
| twelve services | an `.api.aws` twin apiece |
| `logs` | `logs.<region>.api.aws`, **`streaming-logs.<region>.amazonaws.com`**, `streaming-logs.<region>.api.aws` |
| `ecr.dkr` | `dkr-ecr.<region>.on.aws` and its wildcard — a fifth AWS domain family |
| `sagemaker.studio` | four names, two of them wildcards, across `sagemaker.aws` and `app.aws` |
| `ec2messages`, `secretsmanager` | nothing — the only two with a single name |

**The `403`s that started this were loud by luck of the domain family.** `.api.aws` is on no compute
plane, so those refusals were visible. `.amazonaws.com` **is** on the plane — so
`streaming-logs.<region>.amazonaws.com` was answered **200**, left through the hub's IGW as a **public**
call, and arrived carrying neither `aws:SourceVpc` nor `aws:SourceVpce`. It is a different *label* under
a family the list already had, so no suffix rule covered it and no instrument would ever have reported
it. That name is the reason this was worth fixing in the generator rather than by adding entries.

**`dns_entry` also carries the endpoint's own names** — regional and zonal, `vpce-<id>-<hash>.…`.
Excluded: nothing dials them (`private_dns_enabled` is true on every endpoint the module makes) and they
embed an `[E]` id, so carrying them would make `NO_PROXY` churn on every up/down cycle. **Filtered on the
`vpce-` prefix, not on a `.vpce.amazonaws.com` suffix** — `sagemaker.studio`'s end in
`.vpce.sagemaker.aws`, and a suffix filter would have let four through. That is a measurement, not a
style choice.

### [user] Two decisions, both taken before any code was written

1. **The two DNS Firewall families.** Widening the module's coverage precondition to the same reading
   exposed two endpoints both compute VPCs pay for hourly that were **NXDOMAIN**:
   `dkr-ecr.<region>.on.aws` and `studio.sagemaker.<region>.app.aws`. Taken: **add `app.aws` and `on.aws`
   to `sandbox/egress` and `staging/egress`**, on the argument that put `sagemaker.aws` there. The
   alternative — fix `NO_PROXY` alone and record the gap — was refused for a reason the measurement had
   made concrete: a bypassed name stops asking Squid and starts asking the resolver, so fixing one half
   would have converted a legible `403` into an unattributable NXDOMAIN for exactly those names.
2. **Both spellings for a wildcard name**, bare and dot-prefixed. requests/botocore do a plain
   `endswith`, so bare covers the subtree *and* the apex while dot-prefixed covers the subtree only; a
   strict suffix matcher is the mirror image. Neither is right under all of them. Four extra entries.

### [Claude⚡] The module, the tags, and the one apply

Recipe B, twice — the second cycle is the next entry's subject. `vpc-egress-v0.11.1` on all four
callers; `sandbox/egress` was the only egress slice with anything in state (48 resources), so it is the
only one applied. The other three are `[E]` and down and take the module on their next `make up`.

- `terraform plan`: **`0 to add, 1 to change, 0 to destroy`** — the firewall domain list, in place.
- Applied. **Re-plan: `No changes`.**
- The bypass list: **28 → 50 entries, nothing removed.** Twenty-two added.
- Read back from Route 53 Resolver rather than from state: **14 domains live** (the ten, plus
  `app.aws.`, `*.app.aws.`, `on.aws.`, `*.on.aws.`).
- `./aws/dns-allowlist.py --from-api awsds-infra-prod`: `DN-1`..`DN-4` **pass**. `./aws/egress.py`:
  **69 pass, 0 fail**, with `EG-5`'s standing note that 18 interface endpoints are metered at
  ~USD 0.180/h. Neither instrument touches the proxy planes, which this change does not alter.

### [Claude] `vpc-egress-v0.11.0` is tagged and was never deployed, and its own measurement is why

`dns_entry` is a **resource attribute**. On a VPC whose endpoints do not exist yet it is
`(known after apply)`, so the whole coverage condition is unknown and Terraform **defers it to apply**.
Measured on `staging/egress`, torn down: `terraform plan` printed `20 to add`,
`no_proxy = (known after apply)` and **raised nothing** — where the same code with a missing family used
to fail before a single resource was touched.

6c step 5.7 wrote that precondition to turn a silent NXDOMAIN into *a plan-time failure naming the
endpoint*. v0.11.0 had quietly taken the plan half away. **The repair produced Lesson 39 in a step
written to remove a different defect**, which earned it a lesson of its own: **Lesson 59**.

v0.11.1 brings the service data source back **for the guard alone, never for the output**, and splits
the precondition in two — `declared` (one name per service, plan-time, narrow) and `served` (every name,
complete, sometimes late) — with **one matcher mapped over both lists** rather than two copies of it.
Each message names its reading. The v0.11.0 tag stays where it is; never retag.

### [Claude] Both halves have a negative control

A guard that passes proves nothing on its own.

| control | result |
|---|---|
| the two families removed for one plan, `sandbox/egress` (up) | precondition fails naming **all four** uncovered names |
| `sagemaker.aws` removed for one plan, `staging/egress` (**torn down**) | fails **in the plan**, naming `*.studio.us-west-2.sagemaker.aws` **and its own reading** — the proof that the plan-time bite came back |

### [Claude] 8.6's orphan, attributed for free

`dzd-<id>.sagemaker.us-west-2.on.aws` — the Unified Studio domain's own URL, DNS-blocked from every
space address in every window read on 2026-09-08, in the bypass list of nothing and on the plane of
nothing, attributed to nothing. It is **`.on.aws`**, a family the DNS Firewall did not carry. That is
the attribution, and it arrived as a side effect of listing what the endpoints answer for.

It resolves now. **Resolving is not reaching**: it has no endpoint, so it leaves as a proxy request and
returns a `403` naming the host — the diagnosable failure rather than the silent one. Whether to allow
it on the plane is decision due 6's, unchanged by this.

### [Claude] The documents the fix made false

- **`NETWORK.md`** said the list is read from `describe-vpc-endpoint-services` at plan time, which is no
  longer how it is built or when. Replaced, with the table that matters: a missing entry in an
  `.api.aws`-shaped family is a visible `403`, and one in the `.amazonaws.com` family is a silent `200`
  arriving without `aws:SourceVpce`. The firewall is **fourteen** entries, not ten. And
  `sandbox-foundation` reads **24**, not 21 — stale since decision 6 was taken in full the day before,
  counted from `hub-anchors.tf` rather than assumed.
- **`AWS_STATE.md`**'s "sixty-three entries to ten" gained its successor.
- **`sg-proxy.md`** carried the **28-entry** export string in *Latest reading* and a 32-entry settings
  array, two of whose entries were the user's hand-patch of 2026-09-08. Both replaced from the
  post-apply output. The array is the output **plus exactly two entries the generator cannot produce** —
  the glob spelling of the two internal zones, which is VS Code's syntax and not the environment's. The
  hand-patch is gone rather than annotated: at the user's reading, a correct list makes a paragraph
  explaining the incorrect one unnecessary.
- **`CLAUDE.md`**'s 8.8 bullet and Lesson 59's recognition key.

### [Claude] What 8.8 closes, and what it does not

**Closed**: the generator, the guard, the two families, and the runbook's two stale copies. 8.8 itself.

**Not closed, and both are the same shape — a fix nobody has yet seen work where it matters:**

1. **Applied in Sandbox only.** `staging/egress`, `production/egress` and `production/workloads-egress`
   are `[E]` and down; they take `v0.11.1` on their next `make up`, unverified until then.
   `staging/egress` is the one that matters — it carries a firewall and both new families.
2. **The in-space proof is the user's.** DataZone working from a space with **no** hand-patch in
   `http.noProxy` needs a running space, and no API reading substitutes for it. That is the test this
   sitting hands over.

**One operational note**: the infrastructure user's SSO session expired mid-sitting — the cached token
file was gone mid-command — so the runbook's export string was rebuilt from the post-apply output
already on disk rather than re-read live. The user signed in again for the verification below.

### [user ran the space, Claude read] The in-space proof — the name left the proxy log, and CloudTrail says which door it took

The user opened the `editor` Code Editor space, pasted the 52-entry array from
[`sg-proxy.md`](../plan/runbooks/sg-proxy.md) into User Settings, and restarted the space. **CloudTrail
dates the restart to the second**, which matters because the container address changes with it and that is
what cuts the proxy log into two non-overlapping windows (the 8.4 method):

| time (−03) | event | by |
|---|---|---|
| 19:39:49 → 19:40:46 | `CreateApp` | the user's browser, then the service |
| **19:43:50** | `DeleteApp` `editor`/CodeEditor | **the user — the restart's stop half** |
| **19:44:02** | `CreateApp` | **the user — the restart's start half** |
| 20:40:30 | `DeleteApp` on the **JupyterLab** space | `AWSServiceRoleForAmazonSageMakerNotebooks` |
| 20:47:20 | `DeleteApp` `editor`/CodeEditor | idem |

So the proxy log's two source addresses are the pair: **`10.20.74.163`** (2 requests, the pre-restart app)
and **`10.20.104.252`** (76 requests, 22:45:06→22:47:15Z — **the app running the new list**).

**`datazone.us-west-2.api.aws` is absent for `10.20.104.252`.** Searched across the log group's whole life
(retention 365 days, created 2026-09-06) the name has exactly three sources, and the contrast is between
two space containers on the same day:

| source | plane | result |
|---|---|---|
| `10.20.79.130` | a Sandbox space, earlier on 2026-09-09 | **`403` × 11** — the refusals that opened 8.8 |
| **`10.20.104.252`** | **the Sandbox space, after the restart** | **absent** — while making 76 other proxied requests in the same minutes |
| `10.90.0.2` | the tunnel — the laptop's browser reaching the portal | `200` × 23 (09-07) and × 14 (09-09), expected and unrelated |

**The absence is a door rather than a silence, which a proxy log cannot prove on its own.**
CloudTrail for the same window, `datazone.amazonaws.com`, filtered to that container:
`GetDomainExecutionRoleCredentials` × 4, `ListConnections` × 3, `GetUserProfile` × 1 — **eight calls, every
one carrying `vpcEndpointId vpce-0fb1f3ed96ef5653c`**, the Sandbox `datazone` interface endpoint. The app
did make the calls; they took the endpoint. Two channels that do not share a failure mode, which is the
shape 3.2 established.

**`streaming-logs.<region>.amazonaws.com` has never appeared in this log group at all** — zero hits over
its whole life. The entry is therefore **preventive and unexercised**: the fail-open it closes was real —
that name is on the compute plane's `.amazonaws.com`, so it would have been permitted and would have
arrived without `aws:SourceVpce` — but nothing has been measured taking it. Recorded as an absence with
its window, not as a hole that was seen and closed.

**Decision 6's subtraction is enforced and visible in the same burst**: `api.github.com` **`403` × 5** and
`raw.githubusercontent.com` **`403` × 3**, beside `idetoolkits.amazonwebservices.com`,
`ide-toolkits.app-composer.aws.dev` and `sagemaker-unified-studio-mcp.<region>.api.aws` all **`200`** — the
names allowed and the names refused, one day later, in one window.

**Two things read off the same burst that belong to other steps:**

- **Idle shutdown was observed, unasked — step 5.1's first half.** Both apps were deleted by
  `AWSServiceRoleForAmazonSageMakerNotebooks`, the JupyterLab space's at 20:40:30 and `editor`'s at
  20:47:20, `FailureReason` null. The Code Editor app had run 63 minutes.
- **The volume, and it is one host.** The post-restart container moved **98.1 MiB in 76 requests**, of
  which **`aws-language-servers.us-east-1.amazonaws.com` alone is 52.4 MiB in two** — the largest single
  item at every app start, through a `t3.micro` proxy. `files.pythonhosted.org` is 36.7 MiB in 51.
  *(Corrected the same sitting: the first figures were the log's raw byte counts read as MiB. The field
  is `%<st` — bytes from the upstream server — and it is bytes.)*
- **And two `t4g.nano` probes are running** in Sandbox since 21:27Z — `awsds-sandbox-probe-perimeter` and
  `awsds-sandbox-probe-peering`, the `[E]` Stage 3 slices — doing nothing but `ssm` and `time.aws.com`
  lookups every twenty minutes. The `time.aws.com` `BLOCK`s in `/awsds/sandbox/dns-firewall` are theirs
  (chrony), which attributes a block that had none.

### [Claude, at the user's request] The log-reading itself became a runbook

Four sittings have now diagnosed something by reading a log group, and each rediscovered the same
mechanics. [`log-debugging.md`](../plan/runbooks/log-debugging.md) is that, written from the commands
Stages 4, 5, 6a, 6c and 6d actually ran rather than from what the APIs offer: the map, the three
commands, then one section per **kind of event** — the Squid access log, the resolver query log,
CloudTrail, flow logs, the VPN host, Studio.

**Writing it required two readings, and both produced something.**

- **The inventory was measured, not listed from the code.** `describe-log-groups` in both accounts turned
  up **three families this estate did not create**: `datazone-<id>-dev`, one per DataZone project, whose
  retention the service picks — **3, 30 and 731 days in one account on one day**; `/aws/sagemaker/studio`
  and `/aws/mwaa-serverless/<domain>/<workflow>`, both retention `None`, which is **never expires**.
  Lesson 17 in a place nobody had looked: a service that sets itself up creates objects nobody chose, and
  731 days of retention is a cost line nobody priced. **And one of them is a finding for another step**:
  an MWAA Serverless workflow log group exists in Sandbox, so **step 4.1's surface has already been
  exercised** by somebody — the step should read that group before assuming it must be enabled.
- **The two record formats were read off live records rather than described from memory.** Squid's is
  *declared* — `logformat awsds` in `squid.conf.tftpl` — and says `%<st`, bytes from upstream. The
  resolver's is JSON, and its `firewall_rule_action` field is **absent** on an allowed query rather than
  set to `ALLOW`, which is a thing to know before writing a filter that looks for one.

**Reading the format corrected this entry.** The byte figures above were first written as MiB from
the log's raw counts — `aws-language-servers` as *54.98 MiB* — with no division. The post-restart
container moved **98.1 MiB in 76 requests**, of which that host is **52.4 MiB**. Corrected in place, and
the trap is in the runbook's §8 with its date, because the error is invisible: it produces a number of
plausible size in the right column.

### [Claude, at the user's request] The MWAA Serverless log group — step 4 had already run, unread, since 2026-08-27

The runbook's inventory turned up `/aws/mwaa-serverless/dzd-<domain>-<project>/MyWorkflow-<epoch-ms>` in
Sandbox, retention `None`. The user asked for it to be opened. **Nothing was submitted to produce any of
what follows** — it is a run from 2026-08-27 that nobody had read.

`aws mwaa-serverless list-workflows` returns **one workflow, `READY`**, created 2026-08-27 18:57 UTC,
`TriggerMode: manual_only`. The log group holds **one run, one task, two attempts**, 18:58 and 19:04, and
**both failed**.

**Four of step 4's questions are answered by that one object.**

| | reading |
|---|---|
| **4.1** — what enables the surface | **Nothing.** It exists with 6a's eleven blueprint configurations unchanged — no `Workflows` blueprint, no capability prompt. 6a's decision 5 does not re-open |
| **4.4** — the run's identity | **`datazone_usr_role_<project>_<domain>`, session name `AmazonMWAAServerless`.** The vendor's *"its own execution role and worker"* is **false for the role half**: there is no per-workflow role. **This is the governance-favourable outcome** — a blueprint-authored role sits inside the D13 boundary's reach |
| **4.6** — the network shape | **Measured, not read from a page**: the workflow's `NetworkConfiguration` carries **two subnets in two AZs**, `awsds-sandbox-private-usw2-az1` and `-usw2-az2`, this estate's own private tier, and one security group. Encryption is a `CUSTOMER_MANAGED_KEY` on `alias/awsds-sandbox-project` — ours |
| **4.3** — the definition | Readable two ways: inline as `WorkflowDefinition`, and at `DefinitionS3Location` = the projects bucket, `dzd-<domain>/<project>/dev/workflows/<name>.yaml` |

**And the run failed on this estate's own control, with the wording naming it:**

```
AccessDeniedException … not authorized to perform: sagemaker:CreateTrainingJob on resource:
arn:aws:sagemaker:us-west-2:<acct>:training-job/Notebook-task-… with an explicit deny in a
permissions boundary: arn:aws:iam::<acct>:policy/awsds-sandbox-project-boundary
```

The statement is **`DenySageMakerJobsOffVpc`** — `Null sagemaker:VpcSubnets = true`, read back from the
policy.

**Two things follow that were in no plan file.**

- **A "Notebook task" in a SMUS workflow IS a SageMaker training job.**
  `SageMakerNotebookOperator` executes the notebook by calling `CreateTrainingJob`. That is why a
  **compute** control reaches the **orchestration** surface at all — the two were being reasoned about as
  separate perimeters.
- **The portal emits `compute: {}`** — an empty block, so the operator supplies no `VpcConfig`, so the
  boundary denies. **Every default notebook workflow in this estate is dead on arrival** until that block
  carries subnets. It is 4.5's sharpest lint rule and a Stage 10 input.

**Step 1's deny pair is exercised in substance and not in the object it was written for** (Lesson 20).
The refusal proves the *statement* works and that its wording is
attributable — but it came from the **project boundary**, while step 1 was written for the **six persona
sets'** copy of the same statement. One intent in two objects (Lesson 33's shape). A persona-submitted job
is still owed.

**One observation held back from being a finding**: `TriggerMode` is `manual_only`, the definition carries
`is_paused_upon_creation: false`, and the run id is `scheduled__2026-08-27T00:00:00+00:00`. Those are two
different switches and which one the portal's *Run* button uses is unmeasured — 4.2's to settle, not this
sitting's to guess.

## 2026-09-10 — the eighth sitting: the `compute` fix, and it changes nothing

*Continues the seventh sitting's last section. The discovery above is 2026-09-09; everything below is
2026-09-10, and all of it was authorized in chat before it ran.*

### [Claude⚡, authorized in chat] The `compute: {}` fix, three runs — and a mistake of mine in the middle

The user asked for `compute: {}` to be filled and the workflow re-run. **It was, and the result is that
the fix is correct, complete, and changes nothing**: the third run reaches `CreateTrainingJob` and is
refused by the same boundary, with the same wording, on the same role.

**Why the fix could never have been enough, read from the code rather than from the symptom.** `compute`
accepts `instance_type`, `volume_size_in_gb` and `image_details`. The decisive source is the operator:
`SageMakerNotebookOperator` delegates to `SageMakerNotebookHook.start_notebook_execution()`, whose whole
contract is `domain_id`, `project_id`, `domain_region`, `input_config`, `output_config`, `compute`,
`termination_condition`, `tags`, `execution_name`, `waiter_*`. **There is no parameter for `VpcConfig`,
`NetworkIsolation`, `VolumeKmsKey` or `InterContainerTrafficEncryption`** — four of the boundary's five
conditions have nowhere to come from. The fifth, the instance ceiling, is the one the YAML can satisfy,
and satisfying it moved nothing.

**With the ceiling satisfied, four denies now match the same call at once** and AWS names the **policy**,
never the statement (Lesson 20). The refusal is real and attributable to the boundary;
it is attributable to no single `Sid` without four contrast probes.

### [Claude] The mistake

**`update-workflow` is a full replace, not a merge.** The first update passed three fields —
`--workflow-arn`, `--definition-s3-location`, `--role-arn` — and **silently dropped everything else**:

- **`NetworkConfiguration` became `null`.** The two subnets and the security group that put the workers
  in this estate's private tier were **gone**, on a workflow that had been correctly VPC-attached since
  2026-08-27.
- **`LoggingConfiguration` was replaced by a service default**, creating an orphan log group
  `/aws/mwaa-serverless/<workflow-arn-suffix>/` — which is also why the run's logs could not be found in
  the group everything else pointed at.

**The tell was an absence, and it took a negative control to read it.** The task failed in 7 seconds and
CloudTrail had **no SageMaker event at all** — where the 2026-08-27 failure *is* in CloudTrail, twice.
Two lookups settled it: my own `StartWorkflowRun` and `UpdateWorkflow` **were** in the trail for the same
window, so the trail was current and the worker genuinely never made an AWS call. A failure that reaches
no API at all is a failure before the API — which is where the dropped network configuration lives.

**Restored by re-passing every field**, then verified against the values recorded before the change:
log group, both subnets, the security group, `CUSTOMER_MANAGED_KEY`, `manual_only`, the role. The orphan
log group was empty (`storedBytes` 0) and was deleted.

**One loss the API could not restore by itself.** With the network back, the next run failed with
`ValueError: Project ID not found in environment` — the portal injects the domain and project into the
worker's environment, and an API-side update loses that binding. The workflow's tag
(`AmazonDataZoneProject`) survived and carries the **project**, but nothing carries the **domain**. The
repair was to name them in the definition — `domain_id`, `project_id`, `domain_region`, which is the
operator's documented contract — and that is what got the third run to the boundary.

**So the rule this sitting bought**: a portal-authored object edited through its service API loses both
what you did not pass *and* what its creator injected, and the second kind has no field to restore it
(Lesson 60).

**State left behind, deliberately.** The definition carries the requested fix plus the three project keys;
everything else on the workflow matches what it was. The original definition is recoverable byte for byte
— the bucket is versioned and the pre-change `VersionId` is in the register below. **What is not repaired is
the thing the user asked about**, and it is a decision rather than an edit: amend the boundary, abandon
the portal's notebook operator in favour of Stage 10's own DAGs (recommended), or record the loss.

### [Claude] The register — the runs, their definition versions, and the duration as diagnosis

Read back from `list-workflow-runs` and `list-task-instances` on 2026-09-10 rather than transcribed from
the sitting, because a run id read out of prose is a claim (Lesson 38).

| run | authored by | definition version | task | verdict |
|---|---|---|---|---|
| `QdphFF89leYx6M6` | the portal, 2026-08-27 18:57 UTC | `b03fe2a0…d661` | 2 attempts | boundary refusal, `compute: {}` |
| `h2z2UmY6Kytf7iW` | me, 02:31 UTC | `5ef4fd72…b257` | 2 × **7 s** | **no AWS call at all** — the dropped `NetworkConfiguration` |
| `N56gnBolC6Ojy0I` | me, 02:56 UTC | `9b170a13…c8a6` | 2 × **8 s** | `ValueError: Project ID not found in environment` |
| `lwPdgAQpWTqPAo1` | me, 03:06 UTC | `fd88f170…c023` | **12 s** then **17 s** | reached `CreateTrainingJob`, refused by the boundary |

The definition object: `s3://awsds-sandbox-smus-projects/dzd-<domain>/<project>/dev/workflows/MyWorkflow-<epoch-ms>.yaml`,
**pre-change `VersionId` `d1WGuB6S7KXg98QkAQE9EofUXU2IXe.y`** (2026-08-27 18:57:25, 451 bytes) — the byte-for-byte
restore point. The portal wrote the object **twice** at creation, 18 s apart. And the same reading confirms
the repair held: `describe-log-groups --log-group-name-prefix /aws/mwaa-serverless` now returns **one**
group, the workflow's own — the orphan is gone.

**Three readings this table gives that the sitting did not.**

- **Every `update-workflow` mints a new `WorkflowVersion`**, and a run records the one it used. So a run is
  attributable to an exact definition without trusting anybody's memory of what was current — the second
  recovery handle after S3 versioning, and the one that survives an object overwrite.
- **Every run is two attempts** — try 1 `UP_FOR_RETRY`, try 2 `FAILED`, in all four, the 2026-08-27 one
  included. One retry is the default and nothing here set it. It is also why a **7-second task** sits
  inside a **6-minute run**: the gap is the retry delay, and reading the run's duration as the task's is
  the mistake waiting there.
- **The duration separates the three failure modes before a single log line is opened.** 7 s = died before
  the AWS SDK; 8 s = died in the operator's own validation; 12-17 s = reached the API and was answered.
  A cheap first cut on any future MWAA failure, and it agrees with the CloudTrail reading that cost real
  work above.

### [Claude] What this failure is, and what it is not

The symptom presents as *one workflow failing*, and every fact above is about one object.

**It is not one workflow.** The refusal is on `sagemaker:CreateTrainingJob` by the **project role** under
the **project boundary** — both of which every Sandbox project gets from the same blueprint. So it is
**every SMUS workflow whose task is a notebook execution, in every project in this estate**, and
re-authoring it in the portal reproduces it exactly. **Other task types are unmeasured** — a query book or
a visual ETL task may never call `CreateTrainingJob` at all, and nothing here licenses a claim about them.

**Almost everything else works**:

| | |
|---|---|
| the Workflows surface | **exists with no blueprint enabled** — 4.1 |
| authoring, versioning, triggering, logging | all fine; four runs, four versions, one log group carrying all of them |
| the workers' network | **this estate's private tier, two AZs**, CMK `alias/awsds-sandbox-project` — 4.6 |
| the identity | **the project role**, so inside D13's reach — which is *why* the boundary could refuse — 4.4 |

**One act fails: the notebook becoming a training job.** The worker is VPC-attached by the service; the
job the worker submits is not, and the operator has no parameter that could attach it. So the collision is
between a portal feature and a deliberate compute control, and it is settled by a decision rather than by
an edit — the three options are at the end of the section above.

## 2026-09-10/11 — the ninth sitting: step 2 end to end, and the first version bump

*Two days in one sitting: 2.1 and 2.2 on the evening of 2026-09-10, everything from the build session
onwards on 2026-09-11. Claude wrote this file at the user's request. Every write in AWS was authorized
in chat before it ran; the domain writes and the buildbox session are the user's own hands, and the
readings around them are Claude's. The project's SageMaker AI domain is named rather than quoted, as
`dzd-` ids are elsewhere in this file.*

### [Claude⚡, authorized in chat] 2.1 and 2.2 — the slice, and the environment the API refused

`terraform-live/sandbox/dev-env/` applied: the image `awsds-sandbox-dev-env`, one version against
`default-v0.1.1`, two app image configurations and the image role. **Two applies**, because the first
one failed: `CreateAppImageConfig` refused both configurations with

```
ValidationException: 1 validation error detected: Value '{http_proxy=..., NO_PROXY=...}' at
'jupyterLabAppImageConfig.containerConfig.containerEnvironmentVariables' failed to satisfy constraint:
Map value must satisfy constraint: [Member must have length less than or equal to 256, ...]
```

The `ContainerConfig` API reference gives the cap as 25 entries and 256 characters per key and per
value; the generated `NO_PROXY` is 50 entries and about 2,300 characters. The second apply added the two
configurations **without any environment**. The four proxy variables were deliberately not shipped
alone: `.amazonaws.com` is on the compute plane, so a proxy with no bypass list succeeds while losing
`aws:SourceVpce`.

Two readings came out of the same apply:

- **The version is pinned to bytes.** `ImageVersionStatus: CREATED`, `ContainerImage` ending
  `@sha256:6916fc13ab533eb9…6d13` — the digest step 9.5 pushed on 2026-09-08.
- **The image's `RoleArn` is load-bearing.** Production's CloudTrail carries `BatchGetImage` and
  `GetDownloadUrlForLayer` on `awsds-prod-ecr-dev-env` at 17:05:37Z, `userIdentity.type AWSAccount`,
  principal `<role-id>:SageMaker`, from an AWS-internal address. The role id resolves to
  `awsds-sandbox-sagemaker-image`, the slice's own. Four ECR read actions are enough; the vendor's
  `AmazonSageMakerFullAccess` hint is not needed.

### [user] Decision 8 — the proxy environment goes into the image

Taken the same evening: the six variables become `ENV` in `images/dev-env/Dockerfile`, with `NO_PROXY`
as a dated literal, `/etc/apt/apt.conf.d/01proxy`, a sudoers `env_keep`, and `/opt/awsds-proxy.txt`
carrying the entry count and the list's sha256 prefix. `./aws/devenv.py` (`DE-1`..`DE-4`) compares the
literal against the account's current output. The lifecycle configuration was refused because it has no
update API and cannot be deleted while a domain references it; a compressed `NO_PROXY` was refused
because it would change the perimeter.

### [user ran the domain writes, Claude read] The attach, 2.3 and 2.5

`update-domain` put version 1 into **both** app settings in one write. The before/after diff of the
whole `DefaultUserSettings` carried only the two added entries; the domain came back `InService` with
no `FailureReason`. `DefaultSpaceSettings` was read in the same minute and holds no `CustomImages` and
no `CodeEditorAppSettings` at all — the control for what 2.3 then answered.

**2.3**: the user created spaces from the portal and **both started on the image, JupyterLab and Code
Editor**. So a SMUS space reads the domain's `DefaultUserSettings`, and INT-17's per-space fallback is
not needed. The Code Editor half had been attached as unexercised — the Dockerfile is JupyterLab-shaped
by the vendor's rule — and it works.

**2.5**: the registry account's CloudTrail carries the two spaces' pulls at 18:37:43Z and 18:38:31Z —
`BatchGetImage` by `datazone_usr_role_<project>_<env>`, session `SageMaker`, **by digest**. Beside the
17:05:37Z registration, which the image role made **by tag**. The tag is resolved once and a space never
sees it. The D13 boundary did not stand in the way of the ECR read, and no KMS grant was needed.
**INT-01 closed; INT-17 answered.**

### [user] The image's Python: no conda, uv, and two kernels in the Launcher

The user's decision, 2026-09-11: the distribution's environment, its interpreter and its default kernel
are left exactly as they ship, and the image gains a **second** Python built by uv on a uv-managed
CPython, from `images/dev-env/python/pyproject.toml` and a committed `uv.lock`, with its own Launcher
kernel. R stays on conda. Four readings from `uv lock` on the laptop, before any build:

- **TensorFlow publishes no wheel past `cp313`**, which set the interpreter at 3.13 (the user kept the
  framework and moved the Python).
- **The default PyPI `torch` drags the CUDA runtime**: 17 `nvidia-*` packages, 3.03 GiB, into a CPU
  image. torch and torchvision now come from PyTorch's CPU index.
- **`xgboost` pulls `nvidia-nccl`** (241 MiB) for the same reason; the dependency is `xgboost-cpu` —
  the same choice the distribution makes (`py-xgboost-cpu` in its own list).
- The set is about 1.6 GiB of wheels, against 4.7 GiB before those two changes.

The list was then diffed against the distribution's own authored one (`cpu.env.in` for SMD 4.3.0,
fetched): 71 packages, 30 already covered, 6 tooling, 36 missing. Of those, 24 are the server-side half
a kernel has no use for; the user took the other twelve — the S3 Access Grants boto3 plugin, the SMUS
kernel-side integrations and the agent SDKs. **`python-gssapi` was left out**: it is `gssapi` on PyPI
and publishes no linux wheel at all, so it would compile and need `libkrb5-dev`. What that costs is
Kerberos'd Hive.

### [user at the buildbox, Claude read and fixed] The build session

**`buildbox.py sync` failed before anything was copied**, and it was a regression this branch
introduced: `MaxDocumentSizeExceeded`, the context at 585 KB of base64 against SSM's 97 KB cap for the
document and its parameters together, because `uv.lock` had joined `images/`. Two fixes, in order: the
lock now resolves for one platform (`tool.uv.environments`, linux x86_64 — 1373 KB → 517 KB), and the
transfer moved to **SSH inside the Session Manager tunnel**, on a key EC2 Instance Connect authorises
for sixty seconds. Nothing new is opened on the host: no listening port, no security group rule, and
nothing through the proxy. First run: 180 298 bytes, nine files, digest matched on the host,
`/opt/awsds/images` owned by `ec2-user`.

**The first build came out at 28.1 GB**, and `docker history` attributed it: the Python layer at
10.7 GB against a 5.2 GB environment, a 109 MB interpreter and **5.4 GB of `/root/.cache/uv`** — uv
unpacks every wheel into the cache and then materialises it into the venv, both in the same layer.
`UV_NO_CACHE=1` inside that `RUN` is the fix, and a later `rm -rf` is not one. The rebuild came out at
**22.7 GB**.

Pushed as `default-v0.2.0` — a **minor**, because the recipe changed. The user's paste:

```
default-v0.2.0: digest: sha256:48b93ba0b527bed792e361e2f284e8a76802df322e19e17e06e1cd63250e176a size: 6582

default-v0.2.0: digest: sha256:b8f461dae73c1b6bc93b084c7009956049ff27a7b1e2591b001fd9d5585f16f2 size: 8893
```

The first is `awsds-prod-ecr-base`, the second `awsds-prod-ecr-dev-env`.

### [user ran the domain writes, Claude applied] The first version bump, and two things it taught

The order the runbook now carries was learned by running it wrong twice.

1. **The apps must go first.** `./scripts/down-studio-apps.py sandbox` deleted a running app for the
   first time since it was written (step 5.2's first exercise): one `JupyterLab/default`, `InService`
   since the 3.1 session. The vendor gates both domain writes on it — *"Before you can update the
   custom images, you must delete all of the applications in your domain."*
2. **A detach is an empty list, not a removed key.** The first detach sent the block with
   `CustomImages` omitted; `update-domain` returned success and **both attachments were unchanged**.
   The vendor's detach page carries the form — *"you will need to leave `CustomImages` blank, such that
   `"CustomImages": []`"*. So an omitted field reads as *unchanged* here, which is the opposite of what
   a full-replace API does, and it is now in `lessons.md`.
3. **The apply**: `1 to add, 1 to destroy` on the image version, re-plan `No changes`. Version **2** is
   `CREATED` with `ContainerImage` at `@sha256:b8f461dae73c1b6b…f16f2` — the digest of the push above.
4. **The re-attach** on version 2, and the read-back is exact: the live block equals the one that was
   sent, and against the detached block the only fields that moved are the two `CustomImages`.

### [user] What a space does now

The user's report, after a space on `default-v0.2.0`:

> Tudo funcionando perfeitamente! Kernels funcionando. Conectividade com internet sem necesidade de
> configurar proxy. Testei instalação de pacotes com Julia, Cargo (Rust), uv, apt. Kernel do R
> funcionando, não cheguei a testar instalação de pacotes novos.

So: the four kernels start, the proxy environment arrives with the image — the by-hand export of
`sg-proxy.md` is no longer needed on this tag, and `apt` works without `-o Acquire::http::Proxy` — and
package installation is exercised in Julia, Rust, Python (uv) and apt. **R is unexercised for
installation**; the kernel starts, and whether `install.packages` reaches CRAN is untested — CRAN is on
no compute plane, so the expected answer is a refusal and the image is the delivery path (3.1's
`conda`/CRAN decision, still open).

---

## 2026-09-11 — the tenth sitting: the remote IDE opens, and it is outside the controls written for it

*One sitting closed three things — 8.4's delivery, 3.1's last ecosystem and decision 6 — and opened the
one the stage had left for a decision: step 7. The user drove every provocation from two machines; the
readings are mine.*

### [user] 8.4's delivery, with a negative control nobody asked for

The user's report, from a Code Editor space on `default-v0.2.0`:

> Abri o code editor com a imagem nova. Instalei extensões rust-analyser, julia, claude code. Todas
> instalaram com sucesso e estão funcionando. Abri uma outra instância com a imagem padrão do
> SageMaker, e as falhas de instalação acontecem (conforme esperado).

So the mechanism is decision 8's `ENV` reaching the `codeeditorserver` supervisord program, and the
stock-image space is the contrast that says so. **[Claude]** attribution from `/awsds/prod/proxy`, one
Sandbox address, 15:30-15:32Z: `open-vsx.org:443 200 TCP_TUNNEL` for the API and
`openvsx.eclipsecontent.org:443 200` for the bytes — **18 requests, 128.9 MiB**, the largest single
transfer 102,238,249 bytes. Step 8's owed delivery is closed.

### [user ran it, Claude read] 3.1 closes on R, and the tool names nothing

The recipe needed three corrections before it measured the network at all: R lives in its own conda
environment (`/opt/conda/envs/r/bin/R`), its library is root-owned so `install.packages` needs an
explicit writable `lib`, conda-forge's `r-base` sets no mirror so `repos=` must be given, and the test
package has to be **pure R** (`R6`) or a missing compiler answers instead of the perimeter. The run,
pasted verbatim:

```
> capabilities("libcurl"); getOption("download.file.method")
libcurl
   TRUE
NULL
> download.file("https://pypi.org/pypi/requests/json", tempfile(), quiet = TRUE)  # controle positivo
> install.packages("R6", lib = "~/R/library", repos = "https://cloud.r-project.org")
Warning: unable to access index for repository https://cloud.r-project.org/src/contrib:
  cannot open URL 'https://cloud.r-project.org/src/contrib/PACKAGES'
Warning message:
package 'R6' is not available for this version of R
```

```
$ curl -sS -o /dev/null -w '%{http_code}\n' https://repo.anaconda.com/pkgs/main/noarch/repodata.json
curl: (56) CONNECT tunnel failed, response 403
000
```

- **R needs no proxy configuration of its own**: `capabilities("libcurl")` is `TRUE` with
  `download.file.method` unset, so libcurl reads the image's variables. The positive control succeeded
  in the same process, which separates the name from R's plumbing.
- **[Claude] The proxy log names both refusals** where R does not:
  `CONNECT cloud.r-project.org:443 403 TCP_DENIED` **three times in one second** — R tries more than one
  index candidate — and `CONNECT repo.anaconda.com:443 403 TCP_DENIED` at 15:50:31Z, against
  `pypi.org:443 200` with a 200,226-byte body at 15:50:10Z, the control.
- **R's message points at the wrong thing.** *"package 'R6' is not available for this version of R"* is
  what a user sees for a perimeter refusal. The `curl` half says `403` outright. Same refusal, two
  legibilities, and the attribution came from the log either way.

### [user] Decision due 6, closed on its original two: CRAN in, conda out

> Podemos ir pela opção (b).

**[Claude]** `cloud.r-project.org` added to `proxy_allow_sandbox` in
[`hub-anchors.tf`](../../terraform-live/production/networking/hub-anchors.tf) — 24 entries to 25,
`terraform validate` clean, `./scripts/check-tf-conventions.py` OK, **not applied**, so `DN-3` is red
until it is. conda's two names stay refused: the image build reaches them through the `open` build
plane, and a solver run inside a space would move the SageMaker Distribution's own pins. What CRAN does
not buy is the compiled half — it serves source packages, so `images/dev-env/r/conda-packages.txt`
stays the delivery path for anything with C or Fortran in it.

### [user] The remote IDE, connected from a second machine

The user's account of the flow, which is the record of what was done:

> num outro computador (windows) com uma instalação do VSCode, instalei o suplemento AWS. O suplemento
> oferece um painel específico do sagemaker. Nesse painel, ele tem a opção de logar (similar ao que tem
> descrito no site da AWS sobre uso remoto do VSCode). Loguei passando o domínio sagemaker. Ele
> autenticou. Em seguida abriu uma nova janela de sessão remota SSH , e consigo ver exatamente a mesma
> tela que aparece no VSCode por dentro do SageMaker, com as pastas.

### [Claude] Who made the call — 7.2 answered, and the method table was wrong twice

CloudTrail in Sandbox, two `StartSession` calls 13 seconds apart:

| field | 16:02:15Z and 16:02:28Z |
|---|---|
| principal | `datazone_usr_role_<project>_<env>` — **the project role**, by role id |
| session name, `sourceIdentity` | `<idc-user-id>@<env-id>` — the Identity Center user id, inside the role session |
| `sourceIPAddress` | the laptop's own public address — not the proxy's Elastic IP, not an AWS-internal one |
| `userAgent` | `aws-sdk-js/1.0.0 … os/win32#10.0.26100 lang/js md/nodejs#24.15.0` |
| resource | `space/<domain-id>/remote-editor`; `streamUrl` to `wss://ssmmessages.us-west-2.amazonaws.com/…` |

Beside it, 2026-09-10 19:37:27Z: the **same role**, the same address, a Chrome user agent — the portal's
deep link, refused with `ValidationException … does not have remote access enabled` because that space
had the flag off. So both available methods call it **client-side as the project role**, and the stage's
table was wrong about the principal in row 1 (*server-side*) and row 2 (*the persona*). Consequences:
`DenyControlPlaneOffVpn` and 6a's tag pair never evaluate, the channel worked with the laptop off the
VPN, and decision 4's repair has to land on the project role. Two keys exist without Identity Center
*attributes for access control*: `aws:SourceIdentity`, and the space's `OwnershipSettings.OwnerUserProfileName`,
which carries the same user id.

### [Claude] 7.3 read back, and the size is not the one the step priced

`describe-space` on `remote-editor`: `RemoteAccess: ENABLED`, `AppType CodeEditor`, image
`awsds-sandbox-dev-env` **version 2**, `ml.t3.xlarge`, idle timeout 60 minutes, 64 GB EBS, the `shared`
S3 mount, `SharingType Private`. Priced the same day from the Pricing API:
`USW2-Studio:CodeEditor-ml.t3.xlarge` **0.200/h**, `SAE1` 0.323 — twice the `ml.t3.large` floor, and the
space path carries no ceiling to refuse it (`PRICING.md` §8).

### [Claude] Decision due 5, answered by measurement — and the first answer was wrong

The proxy log, same space, after the session came up:

```
16:02:19  CONNECT update.code.visualstudio.com:443  403 TCP_DENIED
16:02:55  CONNECT update.code.visualstudio.com:443  403 TCP_DENIED
16:02:56  CONNECT update.code.visualstudio.com:443  403 TCP_DENIED
16:08:10  CONNECT marketplace.visualstudio.com:443  403 TCP_DENIED   (x2)
16:09:30  CONNECT marketplace.visualstudio.com:443  403 TCP_DENIED   (x3)
16:09:40  CONNECT marketplace.visualstudio.com:443  403 TCP_DENIED   (x2)
```

The space tries the vendor's default for both the server and the `.vsix`, the plane refuses both, and the
session works: Remote - SSH *"will attempt to download on the remote host, and fail back to downloading
VS Code Server locally and transferring it remotely"*, which is the `Copying VS Code Server to host with
scp` line the user saw. **No Microsoft name joins the compute plane**, and the estate pays nothing.

**Two of my own readings were wrong before this one, and both were absences** (Lesson 62). `ls
~/.vscode-server/bin` returned nothing and I read it as *no Microsoft server in the space* — the layout
is `~/.vscode-server/cli/servers/Stable-<commit>/` and six node processes were running from it. And
eight hours of the proxy log carried no Microsoft name, read as *the server never crossed the proxy* —
the log lags by minutes, the window's last line was 16:00:20Z and the `403`s are stamped 16:02:19Z. The
conclusion that survived is the same one, but it was true by luck the first time.

### [Claude] The first session's egress by host, and two refusals nobody had named

From `/awsds/prod/proxy`, the half hour around the first connection (15:30-16:00Z), one Sandbox
container, ordered by bytes:

| host | reading | what it is |
|---|---|---|
| `openvsx.eclipsecontent.org` | 200 — **128.88 MiB** in 18 | 8.4's three extensions |
| `aws-language-servers.us-east-1.amazonaws.com` | 200 — **52.44 MiB** in 2 | the Toolkit's language servers, the host 8.8 had already measured at 52.4 MiB. Allowed by the plane's `.amazonaws.com` entry and holding no endpoint, so a **public** call |
| `files.pythonhosted.org`, `pypi.org` | 200 — 36.72 + 6.58 MiB | wheels the IDE's own components pull |
| `idetoolkits.amazonwebservices.com` | 200 — 15.69 MiB in 14 | named by decision 6 at 8.6 |
| `idetoolkits-hostedfiles.amazonaws.com` | 200 — 0.16 MiB in 22 | **a fourth IDE host no decision names.** It works only because `.amazonaws.com` is on the plane, and it has no endpoint, so it leaves publicly — the fail-open row of `NETWORK.md`'s own table, happening unremarked |
| `api.anthropic.com` | **403 × 17** | the Claude Code extension the user had just installed, reaching its own service. On no plane: the extension installs, and cannot work |
| `westus-0.in.applicationinsights.azure.com`, `eastus-4.in.…` | **403** | editor telemetry nobody asked for, refused. Logged as `POST https://…/v2.1/track`, not `CONNECT` |
| `dzd-<id>.sagemaker.us-west-2.on.aws` | **403** | the documented shape rather than a finding: `on.aws` is on the DNS Firewall list so the name resolves, and it has no endpoint, so the proxy refuses it — `NETWORK.md`, *resolving is not reaching* |

**Two rows are decisions waiting rather than defects.** `api.anthropic.com` is decision 6's class of
question — an extension is worth what the names it may reach are worth — and
`idetoolkits-hostedfiles.amazonaws.com` is the argument for naming the IDE's hosts one at a time: a
family entry hides both the dependency and the loss of `aws:SourceVpce`.

### [user ran the probes, Claude read] Two IDE servers in one container

```
221  /opt/conda/share/sagemaker-code-editor/node …/out/server-main.js --port 8888 --base-path /codeeditor/default
513  /home/sagemaker-user/.vscode-server/cli/servers/Stable-4fe60c8b…/server/node …
```

| | Code Editor, from the portal | the remote session |
|---|---|---|
| version | **1.119.1** (`product.json`) | **1.127.0** — the client's own |
| gallery | `https://open-vsx.org/vscode/gallery` | `https://marketplace.visualstudio.com/_apis/public/gallery` |
| extensions | `~/sagemaker-code-editor-server-data/extensions` — `rust-analyzer 0.4.3045`, `aws-toolkit 3.101.0`, Q, the Python and Jupyter set | `~/.vscode-server/extensions` — `aws-toolkit 4.15.0`, `language-julia 1.238.2` |

Both directories are on the space's EBS volume, so both survive a restart and neither is in the image.
The AWS Toolkit sits in both at **different versions**, which is the clearest statement of what the
split means. `~/.sagemaker_remoteAccess_do_not_delete/sagemaker-remote-access-server` is AWS's own
binary, 6.87 MB, `mtime` 2026-09-04, in a directory created at 15:57 — between the credential vend at
15:52:45Z and the `StartSession` at 16:02:15Z — and its bytes are in no proxy log, so the service
delivered it.

**That settles the extension question the sitting kept returning to.** `Install in SSH` installs in the
space, in the VS Code Server's directory; installing "from the remote environment" had been installing
into the *other* server's directory, through the *other* gallery. A version complaint naming the
client's version is the marketplace offering a build that wants a newer editor — not the remote runtime,
which is the client's own build.

### [user] The client pinned to the image's version

The user chose to pin the Windows client to `1.119.1` — the version AWS pins in the image — from the
archive build, which needs no administrator and does not update itself. **[Claude]** verified the
download service before handing it over: `https://update.code.visualstudio.com/1.119.1/win32-x64-archive/stable`
redirects to commit `974500e6…`, sha256 `6fd3396113d865571811497949a6c01784102e24f076e95a207d66918475894b`
(arm64 `6438dc885a…`), and stable that day was **1.137.0**. The `data` folder beside `Code.exe` is what
keeps the pinned install out of `%APPDATA%\Code` and `%USERPROFILE%\.vscode`, and
`remote.downloadExtensionsLocally` plus `remote.SSH.localServerDownload` are what move the download to
the laptop. A second session was being set up on the pinned client when this entry was written; the
extension install through it is the reading that is still owed.

### [Claude] What this sitting wrote down

[`remote-ide.md`](../plan/runbooks/remote-ide.md) (7.8, the runbook, with the Windows section from the
user's own draft), the stage file's corrected method table and its three closures, `PRICING.md` §8's
`ml.t3.xlarge` row, `NETWORK.md`'s plane count and the remote-IDE paragraph, two `REFERENCES.md` rows
for VS Code's own pages, Lesson 62, and the proxy log's ingestion lag as a trap in
[`log-debugging.md`](../plan/runbooks/log-debugging.md) §8.

### [user] The pinned client connects, and `rust-analyzer` works

> Consegui subir a sessão remota no VSCode. Consegui instalar o rust-analyser. Ele funcionou
> corretamente num projeto rust.

With the extension's own log carrying, four times between 18:29:19Z and 18:30:50Z:

```
ERROR can't load standard library, try installing `rust-src` sysroot_path=/opt/rust/rustup/toolchains/1.98.0-x86_64-unknown-linux-gnu
```

### [Claude] The proxy log for that session, and the one thing it cannot attribute

**The currency check first** (Lesson 62): the group's newest line was 18:30:49Z against a wall clock of
18:33:48Z — a three-minute lag, so the window does cover the install.

The new container is `10.20.116.89`, 39 requests. At **18:29:17Z, `marketplace.visualstudio.com` `403
TCP_DENIED` × 3**, and the extension installed and ran anyway. No host in the marketplace or
`vsassets` families answered `200` anywhere in the window, so **no `.vsix` crossed the proxy** and the
bytes came through the session — the perimeter reading is the same as yesterday's.

**What this log cannot separate**: whether `remote.downloadExtensionsLocally` stopped the remote
download (leaving those three as the extension host's own gallery queries) or whether the download was
refused and VS Code fell back to fetching locally. Both end with no marketplace bytes and a working
extension. The instrument that would settle it is the **client's** Extensions output channel, not
anything in the estate. Recorded as unattributed rather than as a setting proven.

### [Claude] What else the session asked for, and one name that is new

| name | reading | what it is |
|---|---|---|
| `github.com` × 4, `api.github.com` × 3, `raw.githubusercontent.com` × 3 | **403** at 18:25:24-18:25:30Z | the IDE's startup traffic, refused by decision 6's removal of source control from this plane |
| `mobile.events.data.microsoft.com` × 3 | **403** | VS Code telemetry, a name not seen before — the same class as the Application Insights pair, and refused the same way |
| `cognito-identity.us-east-1.amazonaws.com` × 4, `idetoolkits-hostedfiles.amazonaws.com` × 2 | 200 | the Toolkit's own, through the plane's `.amazonaws.com` entry, so public calls |
| `index.crates.io` **2.07 MiB**, `static.crates.io` **0.34 MiB** | 200, 18:30:48-49Z | `cargo` fetching the registry index and crate sources while `rust-analyzer` ran — the Rust ecosystem's first attributed reading in this estate, on plane entries that were already there |

The other container in the same window (`10.20.101.127`, 108 requests) ran an `apt` pass:
`archive.ubuntu.com` and `security.ubuntu.com`, about 30 MiB of package indexes, all `200`.

### [Claude] `rust-src` is missing from the image, and the reason is in the Dockerfile

The error names the mechanism: `images/dev-env/Dockerfile` §4 installs the toolchain with
`rustup-init … --profile minimal --component rustfmt --component clippy`, and **the `minimal` profile
does not carry `rust-src`**, which is what `rust-analyzer` reads to index the standard library. The loss
is completion, hover and go-to-definition for `std`; analysis of the user's own crate is unaffected,
which is why nothing looked broken. It announces itself only in the extension's log.

**Fixed in the image** (`--component rust-src` added, with the measurement in the comment beside it),
so it arrives on the next build — this is not repairable from a space: `RUSTUP_HOME` is `/opt/rust/rustup`,
root-owned and `a+rX`, so `rustup component add` needs `sudo` and whatever it writes dies with the
container. The stopgap for the session in hand is exactly that, and it works today because the v0.2.0
sudoers file keeps the proxy variables and `static.rust-lang.org` is on the plane:

```bash
sudo rustup component add rust-src
```

### [Claude⚡, authorized in chat] The parameter carries CRAN

Recipe A, and the plan applied was the file that was read: `0 to add, 1 to change, 0 to destroy` on
`aws_ssm_parameter.proxy_allowlist`, then a re-plan of **`No changes`**.
`/datascience/prod/proxy/allowlist` is **version 8** (from 7), `LastModifiedDate`
2026-09-11T16:05:43-03.

- **`DN-1`..`DN-4` all pass**, and `DN-3` is the one that moved: *5 planes, entry for entry — the first
  link of code → parameter → host*. `DN-1` resolves 24 exact hostnames (the suffix entries are not
  hostnames), CRAN among them.
- **`PX-1`, `PX-2`, `PX-5` pass; `PX-3` is unanswered by design.** The second link needs `--on-host`
  (`ssm:SendCommand`, a write API carrying only reads), and the host re-renders when its association
  runs, so the reading belongs minutes later — the parameter is the source of truth for what *should*
  be enforced, never for what is.
- **Owed, and it is one line in a space**: `install.packages("R6", …, repos = "https://cloud.r-project.org")`
  should now succeed, and the same name should read `200 TCP_TUNNEL` in `/awsds/prod/proxy` instead of
  `403 TCP_DENIED`. That is the only proof that the chain reached the running file.

### [user ran it, Claude read] The chain closes on CRAN, and it dates itself

The first retry, at 19:17:43Z, was still refused — the association had last run at 19:00:31Z, five
minutes **before** the parameter write, so the running `squid.conf` was still the 24-entry one. It also
cost a second reading first: `~/R/library` did not exist in that space (`'lib = …' is not writable`, and
`install.packages` checks the library before touching the network), because the `mkdir` of the earlier
sitting lives on another space's EBS volume — [Lesson 61](../plan/lessons.md) in the hand of whoever
shortened the command to one line.

After the association ran at 19:30:57Z, the same line succeeded:

```
trying URL 'https://cloud.r-project.org/src/contrib/R6_2.6.1.tar.gz'
Content type 'application/x-gzip' length 64507 bytes (62 KB)
downloaded 62 KB
* installing *source* package 'R6' ...
* DONE (R6)
```

**The access log carries the pair on one container address**, which is the cleanest form this reading
takes — no restart in between, so nothing has to be matched across two addresses:

```
19:17:43  10.20.119.67  CONNECT cloud.r-project.org:443  403  3416     TCP_DENIED   (x3)
19:31:56  10.20.119.67  CONNECT cloud.r-project.org:443  200  1293832  TCP_TUNNEL   (the package index)
19:31:57  10.20.119.67  CONNECT cloud.r-project.org:443  200  70816    TCP_TUNNEL   (the tarball)
```

So the whole chain is measured end to end, with a timestamp at every link:

| when | what |
|---|---|
| 19:00:31Z | the association's previous run — the host renders version 7 |
| 19:05:43Z | the apply; `/datascience/prod/proxy/allowlist` becomes version 8; `DN-3` goes green |
| 19:17:43Z | a retry from a space: still `403`, because the parameter is not the running file |
| 19:30:57Z | the association runs again — `cron(0/30 * * * ? *)` |
| 19:31:56Z | the same name, the same container: `200`, and R builds the package |

**An allow-list edit costs an apply plus at most one half-hourly interval**, which is the trade
`reconfigure_schedule`'s own description names, now with numbers. It is also why `DN-3` and `PX-3` are
two checks: nothing about a green `DN-3` says the proxy is enforcing it yet. `PX-3` itself stays
unanswered — it needs `--on-host` — and this reading is its behavioural equivalent, taken from the
running file's own output rather than from the file.

### [Claude] The sitting's record, and what it leaves owed

Branch `claude/6d-remote-ide-and-cran`,
[PR #77](https://github.com/felipenoris/AWS-DataScience/pull/77), one subject per commit: `rust-src` in
the image; CRAN on the plane with `NETWORK.md`; the [`remote-ide.md`](../plan/runbooks/remote-ide.md)
runbook with `REFERENCES.md` and `PRICING.md`; the stage file's corrected method table and its three
closures; Lesson 62 with the access log's ingestion lag and `CLAUDE.md`; this log; the apply; and the
in-space proof that closed CRAN. `make check` OK at every step and `terraform validate` clean on
`production/networking`. The merge is the user's.

**Owed after this sitting**, so the next one does not re-derive it: **7.6** — the tag pair exercised on a
principal that carries it, which today is expected to *permit*, since it evaluates on nobody; **7.7** —
the 12-hour residual, whether a session outlives the tunnel and the portal logout; **7.9** —
`./aws/remote-ide.py`; and **decision due 4**, which now holds every reading it was waiting for. Outside
step 7: 2.4, step 1's persona half, 3.4, 3.5, 3.7, step 5 and step 6. `rust-src` is in the Dockerfile
and arrives with the next build; `PX-3` stays unanswered until someone runs `--on-host`.
