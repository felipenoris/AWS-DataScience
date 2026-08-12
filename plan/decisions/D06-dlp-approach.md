# D6 — DLP approach

**Status:** Decided (2026-08-07): **native AWS combination**, on top of a data perimeter

**In one line:** DLP is four problems with four native controls on top of the data perimeter, and IAM Access Analyzer is the one component that checks the others instead of adding to them.

**Related decisions:** [D5](D05-sagemaker-egress.md), [D13](D13-lake-formation-enforcement.md), [D19](D19-derived-zone.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 1c](../stages/stage-01c-preventive-policies.md), [Stage 11](../stages/stage-11-dlp.md), Stage 12

---

## Rationale and consequences

The objective in `CLAUDE.md` is split into four problems, each with its own control: discovery/classification → **Macie**; fine-grained access → **Lake Formation** (LF-Tags, column and row filters), made enforceable by D13; egress control → **D5** plus the SageMaker VPC-only domain; exfiltration detection → **CloudTrail data events + GuardDuty + Security Hub** with CloudWatch alarms. **Underneath all four sits the data perimeter (`plan/architecture.md` §4.2)** — SCPs, RCPs and VPC endpoint policies built in Stage 1, not Stage 11, because they are the only controls that make exfiltration structurally impossible rather than merely visible. A third-party agent-based DLP is only evaluated in Stage 11, after these are in place and their gaps are known.

**Revised 2026-08-12 — the fifth component, and it is of a different kind: IAM Access Analyzer.** The four
controls above answer *what is protected*; not one of them answers *whether the protection holds*. Macie
says where sensitive data is, Lake Formation says who is entitled to it, D5 says where bytes may go, and the
detective trio says when something moved — and every one of those is a statement about a configuration this
project itself wrote. Access Analyzer is the only piece of the strategy that **checks the configuration
instead of adding to it**, and it does so by proof rather than by pattern: it reduces the resource-based
policies to logic and decides, over *all* possible requests, whether a principal outside the zone of trust
can reach the resource. That is why it belongs in the strategy and not only in a stage — it is the
verification half of two of the four problems, and of the perimeter beneath them:

| Finding type | What it verifies, and against what | Cost and where |
|---|---|---|
| **External access** | Which resources are reachable from outside the organization — the perimeter's trusted-identities axis (`plan/architecture.md` §4.2), **including the resource types no RCP covers**, where it is not a check on the perimeter but the only control there is | Free, org-wide from Audit — **Stage 1b step 8.2** |
| **Internal access** | Which principals *inside* the organization can reach a named bucket — i.e. **D13**'s claim that execution roles hold no direct S3 path to Lake Formation-registered prefixes, and the containment **D19** asserts around the derived zone | Paid per resource-month — **evaluated in Stage 11** |
| **Unused access** | Permissions granted to roles and permission sets and never exercised, against least privilege | Paid per principal-month — **Stage 12** |

**Two boundaries, because both are easy to get wrong.** First, Access Analyzer reports **reachability, never
movement**: a finding says a path exists, not that a byte travelled — so it does not shorten the exfiltration-
detection problem, and, read in the other direction, *an empty findings list is not evidence that nothing was
copied*, only that nothing outside the zone of trust is entitled to read. Second, an organization-scoped
external analyzer is **silent by construction about everything inside the organization**, which is precisely
where this environment's interesting movement happens (Sandbox reading Data Governance). That silence is the
gap internal-access findings exist to fill, and it is the reason Stage 11 still has work to do on a service
that was switched on in Stage 1b.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
