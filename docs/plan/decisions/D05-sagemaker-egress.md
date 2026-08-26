# D5 — SageMaker internet restriction mechanism

**Status:** Decided (2026-08-07): **build BOTH and compare, in Stage 6** — **re-scoped 2026-08-25 by the
user's clarification: D5 governs the egress of the SageMaker-MANAGED COMPUTE, never the client's machine**

**In one line:** Two egress designs for the SageMaker compute, behind a switch and compared: (A) NAT plus a small allowlist, (B) internet fully blocked — and whatever either allows still crosses the institution's single HTTP/HTTPS proxy.

**Related decisions:** [D6](D06-dlp-approach.md) (the client plane's egress is its territory)

**Referenced by stages:** [Stage 3](../stages/stage-03-networking.md), [Stage 6](../stages/stage-06-unified-studio.md), [Stage 8](../stages/stage-08-cicd-pipelines.md), [Stage 11](../stages/stage-11-dlp.md)

---

## Rationale and consequences

Not one mechanism but two designs, implemented behind a switch and evaluated against each other — see `docs/plan/architecture.md` §4.3. **(A) Limited internet:** NAT plus an allowlist, using Route 53 Resolver DNS Firewall and/or a Squid proxy. **(B) No internet:** no NAT at all for the SageMaker subnets; packages arrive through CodeArtifact (upstream to the public repositories) and ECR pull-through cache, everything else through VPC endpoints. AWS Network Firewall (~USD 290/month) stays documented as the enterprise variant of (A) but is not built. The user's stated reservation about (B) is recorded in `docs/plan/architecture.md` §4.3: CodeArtifact does not cover every language this environment needs.

**Re-scoped 2026-08-25 (the user's clarification; `docs/plan/objectives.md` carries it as requirement).**
Three consequences, each correcting a reading some file had made:

1. **D5's subject is one plane of two.** The estate has a *client plane* — the laptop on the VPN, whose
   internet runs through the cloud's egress under an institutional HTTP/HTTPS proxy, monitored but broad
   (D6, Stage 11) — and a *compute plane*, the SageMaker-managed compute this decision restricts. The
   two designs apply to the compute plane only. In particular, **the SMUS portal's public-internet
   requirements** (AWS's network-isolation page, its public-internet-access tables) **are the client
   plane's to serve**: the browser loads them through the monitored client egress, so neither (A) nor
   (B) is measured against the portal. This corrects the 2026-08-24 reading in
   `docs/plan/architecture.md` §4.3 that called the portal "a hard limit of (B)" — the limit was real,
   the plane was wrong.
2. **The (A)/(B) gap is smaller than the two names suggest**: with an internet whitelist as the
   mechanism, (B) is the empty list and (A) a short one (package registries, perhaps data providers).
   Both reach the *intranet* — the private zones, GitLab included — identically; internet is the only
   axis they differ on.
3. **One egress, one proxy, two filters.** The whole cloud converges on a single internet egress point
   with a single HTTP/HTTPS proxy; even a name on the compute's whitelist crosses it. So the compute's
   effective filter is the intersection: the institutional proxy's list AND SageMaker's stricter one.
   The lab today runs per-account NATs as the interim shape; how they converge on the single
   egress/proxy is open question 23 (`docs/plan/open-questions.md`), owned by Stage 11's egress-control
   leg — the L7 options priced in `docs/plan/architecture.md` §4.3a are no longer answers to a
   requirement nobody stated: the proxy is now stated.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
