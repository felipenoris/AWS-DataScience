# Stage 13 — Public-facing web tier (experiment)

| | |
|---|---|
| **Status** | not started |
| **Prerequisites** | Stages 3, 9. |
| **Consumes** | — |
| **Proves** | — |

*Read with [`plan/conventions.md`](../conventions.md) (naming, layout, `[P]`/`[D]`/`[E]`, IAM rules).*

---

**Objective:** the experiment described in `CLAUDE.md` — a public web server reaching a private backend.

**Prerequisites:** Stages 3, 9.

**To execute:**

1. Public ALB in the public subnets with WAF and an ACM certificate; a public Route 53 hosted zone.
2. Application on ECS Fargate in the private subnets; database (RDS or the Iceberg catalog through Athena)
   in the isolated subnets.
3. Security groups allowing only ALB → app → data, and nothing else.
4. Document the blast radius and how to tear the whole tier down.
---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
