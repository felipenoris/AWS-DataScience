# D9 — Number of AZs

**Status:** Decided: **2 for subnets, 1 for metered endpoints**

**AMENDED 2026-09-05:** the rule is unchanged and now applies to five VPCs rather than three — two AZs of free subnet plumbing everywhere, one AZ for metered interface endpoints, and both hub hosts plus every endpoint set pinned to `usw2-az1` so peering traffic stays same-AZ and free ([D38](D38-single-egress-hub.md)).

**In one line:** Two AZs for free subnet plumbing, one AZ for metered interface endpoints.

**Related decisions:** —

**Referenced by stages:** [Stage 3](../stages/stage-03-networking.md)

---

## Rationale and consequences

Subnets, route tables and NAT-less network plumbing are free, so the topology spans 2 AZs and stays honest. Interface VPC endpoints are charged per AZ, so they default to a single AZ during lab sessions; a resource in the other AZ still resolves and reaches them, at the cost of cross-AZ traffic and no AZ redundancy — an acceptable trade in a lab, and a one-variable change if it ever is not.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
