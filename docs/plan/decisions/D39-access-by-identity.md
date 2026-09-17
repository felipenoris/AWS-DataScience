# D39 — AWS is reached by identity, and the VPN reaches the private network

**Status:** Decided (2026-09-17, user): no network condition binds a person's access to AWS; the VPN is required only to reach private addresses and names; the laptop's one direct write to the governed lake is admitted by principal; both VPN client profiles stay.

**In one line:** A person reaches the AWS console, the AWS APIs and the SageMaker Unified Studio portal from any network with an Identity Center session, which the institution grants only on a laptop it monitors; the VPN carries the private network and nothing else is conditioned on it.

**Related decisions:** [D4](D04-vpn-wireguard.md), [D5](D05-sagemaker-egress.md), [D6](D06-dlp-approach.md), [D13](D13-lake-formation-enforcement.md), [D15](D15-tls-internal.md), [D18](D18-data-scientist-access.md), [D20](D20-staging-account.md), [D38](D38-single-egress-hub.md)

**Referenced by stages:** [Stage 6g](../stages/stage-06g-access-by-identity.md) (executes it), [Stage 4](../stages/stage-04-vpn.md), [Stage 6c](../stages/stage-06c-networking-hub.md), [Stage 6d](../stages/stage-06d-unified-studio-remainder.md), [Stage 9](../stages/stage-09-deployment-targets.md), [Stage 11](../stages/stage-11-dlp.md), [Stage 15](../stages/stage-15-guardduty.md)

**Closes:** open question 17, and INT-16 as a recorded deviation.

---

## Rationale and consequences

### 1. The requirement

[`objectives.md`](../objectives.md) carries it. This decision records what it changes in the controls, the
documents and the stages; it does not restate it.

### 2. What enforced the previous requirement

Two statements, and nothing else in the estate tests the network a person calls from. Read on 2026-09-17
across `terraform-live/`, `terraform-modules/` and every organization policy document: no SCP or RCP
carries `aws:SourceIp`, `aws:SourceVpc` or `aws:SourceVpce`.

| Statement | Where | What it tests | What it held |
|---|---|---|---|
| `DenyControlPlaneOffVpn` | `identity/sso/`, composed into the six persona permission sets: `DataScientistAccess`, `DataScientistStagingAccess`, `DataScientistProdAccess`, `DeploymentManagerAccess`, `GovernanceManagerAccess`, `DevEnvStewardAccess`. `InfrastructureAccess` never carried it (open question 17) | denies `*` on `*` unless `aws:SourceIp` is one of the hub's Elastic IPs, `aws:SourceVpc` is `VPC-Networking`, or a service makes the call on the caller's behalf | every persona call, control plane and data plane: the console, Athena, Glue, `lakeformation:GetDataAccess`, `s3:GetDataAccess` and `s3:ListCallerAccessGrants`, `ecr:GetAuthorizationToken`, the drop-box write |
| `DenyOutsideTrustedNetworks` | `data-governance/data/`, on `awsds-data-{raw,curated,artifacts,logs,dropbox}` | denies `s3:*` unless the call arrives through a trusted S3 gateway endpoint, from a `Data Governance` principal, from one of the hub's Elastic IPs, or from a service | the lake. The Elastic IP branch and `VPC-Networking`'s gateway endpoint exist for laptops only, and the one laptop path they serve is `DataScientistAccess`'s drop-box `s3:PutObject` |

The portal was behind neither. INT-16 measured it reachable off the VPN on 2026-08-22, JupyterLab
included, and 6c step 6.6 accepted that as a recorded deviation on 2026-09-07.

### 3. The persona deny, the lake's laptop admission and the client profiles

- **The persona deny is deleted, not narrowed** (the user). The alternative was a narrower deny keeping
  object reads, credential vending and the drop-box on the proxy's address. It would have kept a VPN term
  on a public endpoint against the requirement, and the portal's own download path was never behind it.
  After Stage 6g no permission set carries a network-origin condition: `InfrastructureAccess`'s shape,
  extended to the other six.
- **The lake admits the laptop by principal, and only for the drop-box write** (the user). The
  `aws:SourceIp` branch and `VPC-Networking`'s gateway endpoint leave `DenyOutsideTrustedNetworks`. A
  principal branch admits `DataScientistAccess`'s `s3:PutObject` on the drop-box from any network, written
  against the action and the bucket as well as the principal, so an allow added later inherits nothing
  (Lesson 29). Every other request to the lake still arrives through a consumer's gateway endpoint, from a
  `Data Governance` principal, or from a service acting for its caller.
- **`awsds-prod-outputs` takes the same shape** when Stage 9 builds it: `DataScientistProdAccess` reads its
  named prefixes by identity, and the bucket's network deny keeps its endpoint and service branches for
  every other principal.
- **Both VPN client profiles stay** (the user). The monitored profile remains the institution's model:
  while connected, a laptop's internet crosses the proxy and is logged. It is no longer a condition of
  reaching AWS, so its access log records what a connected laptop reached, never who reached AWS.

### 4. Where the data-leakage circuit closes

D6 closed the client plane's circuit on the network: only institution laptops, carrying Microsoft 365
endpoint DLP, held a VPN peer, and every persona call needed the tunnel. The requirement moves the closure
to the identity. A session is granted only on a laptop the institution monitors, so what is pulled out of
SageMaker, the console or the APIs lands on a device whose DLP is the institution's.

**The lab models that premise and does not enforce it.** Identity Center's own directory evaluates no
device posture, and a sign-in succeeds from any device that completes MFA (Lesson 5: an intention is not a
control). The institution enforces it at the identity provider, with a sign-in policy that admits a
managed, compliant device only, federated into Identity Center. `institutional-delta.md`'s device-trust row
carries that delta. Stage 11's threat model carries the lab's residual and its detective half: CloudTrail's
per-principal record of every data call and GuardDuty's findings on credential use (Stage 15).

### 5. What stays bound to the network

- **The private network.** WireGuard is the only way into the estate's private addresses and the
  `awsds.internal` names: GitLab and Pages, the internal CA's consumers, any host (D4, D15, D38).
- **The compute's egress** (D5, D38). SageMaker compute reaches the internet only through its plane's list
  on the proxy, and the lake only through its own VPC's gateway endpoint.
- **The lake's workload path.** A principal that is not a person reaches the lake only through the doors
  section 3 leaves in place.

### 6. Consequences in other decisions, stages and instruments

- **D6.** The client plane's leg closes on section 4's identity premise.
- **D38.** The proxy's Elastic IP stops being an IAM condition value: §3's reason for keeping it `[P]` is
  re-examined at Stage 6g, §4's anchor and INT-16's fallback (i) shape are retired, §5 keeps its DNS
  reason and loses the persona-condition one, and §6's tunnel-range filter applies to a laptop on the
  monitored profile.
- **D18 and D20.** The laptop reaches the data plane by identity; D18's drop-box write is section 3's
  principal branch.
- **D5 and D15.** The client plane is a laptop, behind the proxy only on the monitored profile; the VPN is
  the only way into the private network.
- **Retired.** INT-16 as a deviation; open question 17; 6c step 6.6's acceptance and its decision due 3;
  Stage 4 step 8's statement; Stage 11 step 3.4, step 5.2's `awsds-data-portal-offproxy` rule, decision
  due 10 and verification xi; Stage 15 step 6's re-read of open question 17; 6d decision due 4's VPN
  half, 7.5's tunnel-down control and 7.7's tunnel half; `./aws/proxy.py` `PX-5`; `./aws/vpn.py` `VP-7`
  as written.
- **Triggered.** Stage 11 decision due 5, Malware Protection for S3 on the drop-box, whose revisit
  condition was a file arriving from outside the tunnel.

### 7. Cost

None. Two statements shrink, the `vpn_homes` input leaves two slices, and nothing is created.

## Revision trigger

- An identity is granted to a device the institution does not monitor, or the lab federates an identity
  provider whose sign-in policy checks the device: section 4's premise stops being true, or becomes a
  control, and Stage 11 re-reads the residual.
- A detection attributes a data movement to a session that section 4's premise says cannot exist.
- A requirement binds a data download to a network again.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
