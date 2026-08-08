# D4 — VPN technology

**Status:** Decided (2026-08-07): **self-managed WireGuard**

**In one line:** Self-managed WireGuard on `t4g.nano`, layer `[D]`; Client VPN documented as the managed alternative.

**Related decisions:** —

**Referenced by stages:** [Stage 4](../stages/stage-04-vpn.md)

---

## Rationale and consequences

A `t4g.nano` EC2 instance in a public subnet, layer `[D]` — stopped between sessions, not destroyed, so the host key and peer configuration stay stable. Idle cost is its 8 GB EBS volume (~USD 0.65/month) plus the Elastic IP, which lives in the `[P]` foundation slice (~USD 3.65/month) so the endpoint address never changes. Consequences to handle in Stage 4: no native Identity Center integration, so peer public keys are provisioned by Terraform from a git-ignored variable file; and it is a single point of failure, which is acceptable for a lab. AWS Client VPN (~USD 73/month, SAML to Identity Center) stays documented as the managed alternative if SSO-integrated VPN becomes a requirement.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
