# Log — Stage 6d: Unified Studio, what 6a left owed

*The stage file is [`docs/plan/stages/stage-06d-unified-studio-remainder.md`](../plan/stages/stage-06d-unified-studio-remainder.md).
Every entry names whose hand wrote it. `[Claude]` is a reading or an authored change; `[Claude⚡]` is
an apply; `[user]` is something done by hand, with any measurement pasted verbatim.*

---

## 2026-09-07 — two readings taken ahead of the stage, because both are inputs to other people's steps

*Stage 6c's pass 6 is waiting on four `[user]` readings, so the two 6d steps that need nothing from
anybody were taken first. Both turned out to be worth taking early for the reason their own step
texts give: each one is a **lead time**, not a portal click.*

### 3.6 — the two portal surfaces, measured against the Region's own catalog

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
- **[Claude] WHAT IS NOT DECIDED HERE, deliberately.** Both spellings exist, and which one the portal
  actually calls is a measurement that needs the feature opened — a step that belongs to whoever
  opens it. Adding both would be 0.020/h for a feature nobody has used; adding neither is the state
  today. **Recorded as a named gap rather than closed by guess**, and it is a cheap one to close once
  somebody clicks the editor: the symptom will be a 403 or a timeout with `sqlworkbench` in it.

### 7.2 — which principal makes the remote-IDE call, and the static half is decisive

- **[Claude] The step asks the right question and the answer is worse than it feared.** 6a step 3.2
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
  Either way **the objective's scoping was granted by nothing**. This is Lesson 18 in its plainest
  form — a policy never constrains the principal that authors it — with Lesson 28 underneath: the
  grant and the constraint are in two different slices, and neither file shows the gap.
- **[Claude] The repair the step already names is the right one and is NOT a new SCP.** An SCP would
  deny the feature rather than scope it. The estate has exactly one instrument that reaches a role a
  blueprint writes: **the D13 permissions boundary of 6a step 2.1**. The two conditions move there.
  **Not done here**: it changes a boundary on a blueprint-authored role, the boundary field is
  write-only (always `get-role`, never `list-roles`), and 7.5's CloudTrail is what names the role to
  attach it to. Recorded so the repair is not rediscovered as a design question.
- **[Claude] What this does NOT settle**: whether a space is created with remote access at all (7.3,
  the user's decision) and which of the three connection methods works (7.4). The reading above makes
  7.3's recommendation stronger rather than weaker — *on for one space, by hand, off as the default* —
  because the scoping everyone assumed was in place is not.

## 2026-09-07 — 7.1: the required set derived from the vendor's pages, and the Sandbox list already had it

*The step said to take it first because a missing endpoint is a slice edit with a lead time. There is
no missing endpoint. What the pages carry instead is three requirements the step never asked about
and one fact that re-frames 7.2 — so the lead time went into the plan rather than into a slice.*

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
  - **The VS Code server is downloaded by the SPACE**, from `update.code.visualstudio.com` and
    `vscode.download.prss.microsoft.com` (extensions: `marketplace.visualstudio.com`,
    `*.gallerycdn.vsassets.io`). The vendor's private-subnet answer is an HTTP proxy with those names
    allowed — on this estate a **compute-plane widening**, the plane the user's rule keeps
    restricted. Two shapes avoid it: VS Code's `remote.SSH.localServerDownload = always` with
    `remote.downloadExtensionsLocally = true` (the laptop downloads on the open plane and pushes
    through the SSH tunnel), and AWS's pre-packaged tarball installed by a lifecycle configuration
    from S3. Recorded as **decision due 5**, recommended: the client settings.
- **[Claude] And the pages re-frame 7.2, which is why the lead time went into the plan.** The SMUS
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
    *"a deny is what survives someone else granting it"* — is a kill-switch wearing a scoping's name.
    The 2026-09-07 morning reading said *granted by nothing*; the precise sentence is **scoped by
    AWS's Allow on the project role if that policy is attached, and by nothing of ours**.
  - **No method is both VPN-bound and scoped today.** Decision due 4 re-framed: choose the method
    first, after 7.4/7.5 read each one's caller and address. Recommended if VPN-only is to be true of
    this channel: Method 3, a tag-scoped Allow on the persona sets keyed on something a persona session
    carries (the vendor's ABAC example uses `IDC_UserName` through Identity Center's attributes for
    access control; the one space is tagged by hand at 7.3), the pair rewritten to that key, and
    `StartSession` **denied on the D13 boundary** so the deep link's path closes.
- **[Claude] One reading NOT taken, named so it is not read as taken**: whether the Sandbox project
  role actually carries AWS's conditioned Allow — `list-attached-role-policies` and the inline
  documents, as `awsds-infra-sandbox-1`. The SSO session had expired; the user was asked for the
  sign-in (infrastructure user, `Sandbox`, `InfrastructureAccess`). It decides whether the deep-link
  path is *AWS-scoped* or *unscoped*, and nothing above changes with the answer except that word.

## 2026-09-07 — the session audited, the documentation swept for 6b/6c, and three plans re-cut

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
except the Terraform change, which is authored, tagged and planned — and NOT applied.*

- **[Claude] The project role's policies — the reading 7.1 left pending, and the word it was waiting for
  is *scoped*.** One DataZone role in Sandbox, `datazone_usr_role_<project>_<env>`, under the boundary
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
  gives up, said once**: an `ml.p4d` Code Editor space bills USD 30+/h and D12's budget notifies nobody;
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
- **What changed for a data scientist, in one sentence**: a Code Editor or JupyterLab space may now be
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
  arrived carrying neither `aws:SourceVpc` nor `aws:SourceVpce`. The failure this pair rules out is the
  one that succeeds.
- `getent hosts` returning **10.20.32.164** for `sts` is the same address 6c step 6.2 recorded on
  2026-09-07 from a restarted space — an unplanned cross-check on the endpoint set.

### [Claude] 3.3 — what the proxy saw, and the GitHub redirect is confirmed BY NAME

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
  user while the proxy was logging a named `403`. The two views of one event, in one sitting.
- **The source address in every line is the app ENI, 10.20.66.132** — a spoke reaches 3128 over the
  peering, un-masqueraded, so the log is per-workload the same way the tunnel's is per-device.

### [Claude] The one reading that is weaker than it looks, and the user's own first command is why

`curl --noproxy '*' https://pypi.org/` returned `000`, and the step wanted that read as *no default
route*. It is not: the user's **first** command, before the proxy variables were exported, returned
**`curl: (6) Could not resolve host: pypi.org`** — the Sandbox DNS Firewall, whose allow-list is the four
families of 6c step 5.7. So the `000` measured a **resolution** refusal, and the absent route was never
reached. Both facts are true — there is no default route, as code — but this measurement cannot separate
them (Lesson 42). **The routing half stays 6c step 6.3's probe**, which uses `checkip.amazonaws.com`: a
name inside `*.amazonaws.com`, so it resolves and then has nowhere to go. Recorded so that a later reader
does not cite the `000` as the route's proof.

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
