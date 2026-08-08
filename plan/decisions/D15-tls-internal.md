# D15 — TLS for internal endpoints

**Status:** Decided (2026-08-07): **a real public domain plus split-horizon DNS**

**In one line:** A real public domain plus split-horizon DNS; ACM cannot certify `.internal` and Private CA is over budget. **Needs a domain name from the user.**

**Related decisions:** —

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md), [Stage 3](../stages/stage-03-networking.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md)

---

## Rationale and consequences

ACM cannot issue a certificate for `sandbox.internal` — public certificates require a domain you can validate publicly, and AWS Private CA costs ~USD 400/month (~USD 50 in short-lived mode), both over the ceiling. The workable path: register one public domain, keep a public hosted zone **for DNS validation only**, issue free public ACM certificates (including the wildcard GitLab Pages needs), and resolve the names to private addresses through the **private** hosted zone. A public certificate on an internal ALB is supported; nothing is published. Cost ~USD 0.50/zone plus the domain (~USD 12-15/year). **Needs input from the user: which domain name to register.**

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
