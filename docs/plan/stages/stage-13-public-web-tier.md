# Stage 13 — Public-facing web tier (experiment)

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3, 9. **The domain name from the user** (D15 phase 2) — this is the only stage that needs it. |
| **Consumes** | [D15](../decisions/D15-tls-internal.md) |
| **Proves** | — |

*Read with [`docs/plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the experiment described in `CLAUDE.md` — a public web server reaching a private backend.
**And, since D15 was revised on 2026-08-09, this is also the stage where public DNS enters the project at
all.** Everything before it is named in private hosted zones and certified by the internal CA; nothing
before it is registered, published or resolvable from outside the VPN.

**Prerequisites:** Stages 3, 9, plus the domain name.

**To execute:**

1. **Register the domain and create the public hosted zone** (D15 phase 2). This is the first and only use
   of `route53domains:*` in the project — Stage 1c step 7's region-exemption list carries it for this
   moment. Registration and validation are slow, so start the stage here rather than discovering the wait
   after the ALB is built.
2. Public ALB in the public subnets with WAF and a **public ACM certificate** issued against the new zone.
   For a CloudFront variant the certificate must be issued in `us-east-1` (`docs/plan/architecture.md` §4.1) —
   which is what `acm:*` is exempted from the region control for.
3. Application on ECS Fargate in the private subnets; database (RDS or the Iceberg catalog through Athena)
   in the isolated subnets.
4. Security groups allowing only ALB → app → data, and nothing else.
5. Document the blast radius and how to tear the whole tier down. **Public DNS is part of the blast
   radius now**: a record left behind after teardown points the world at something that no longer exists,
   or worse, at whatever takes the address next.

**The one question D15 deliberately left here.** With a real domain finally registered, decide — and record —
whether the internal endpoints stay on `*.internal` with the internal CA, or move onto a subdomain of the
registered domain with split-horizon DNS and public ACM certificates. The trade is the internal CA's
distribution friction, now measured rather than predicted, against publishing the internal name inventory in
Certificate Transparency logs. **Defaulting silently to "we have a domain now, use it everywhere" is the
outcome to avoid** — it is a real change in what is publicly known about this environment, and it deserves
to be a decision.

**Do not read this stage as unblocking OIDC for CI.** Principle 2 rules OIDC out because a VPN-only GitLab
cannot serve a JWKS that IAM can *fetch*. That is reachability, not naming: registering a domain here
changes nothing about it.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
