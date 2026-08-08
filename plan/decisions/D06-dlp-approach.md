# D6 — DLP approach

**Status:** Decided (2026-08-07): **native AWS combination**, on top of a data perimeter

**In one line:** DLP is four problems with four native controls, all sitting on top of the data perimeter.

**Related decisions:** [D5](D05-sagemaker-egress.md), [D13](D13-lake-formation-enforcement.md)

**Referenced by stages:** [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

The objective in `CLAUDE.md` is split into four problems, each with its own control: discovery/classification → **Macie**; fine-grained access → **Lake Formation** (LF-Tags, column and row filters), made enforceable by D13; egress control → **D5** plus the SageMaker VPC-only domain; exfiltration detection → **CloudTrail data events + GuardDuty + Security Hub** with CloudWatch alarms. **Underneath all four sits the data perimeter (`plan/architecture.md` §4.2)** — SCPs, RCPs and VPC endpoint policies built in Stage 1, not Stage 11, because they are the only controls that make exfiltration structurally impossible rather than merely visible. A third-party agent-based DLP is only evaluated in Stage 11, after these are in place and their gaps are known.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
