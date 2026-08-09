# D15 — TLS and naming for internal endpoints

**Status:** Decided (2026-08-07); **revised 2026-08-09 — split into two phases, and no public domain
exists before Stage 13.**

**In one line:** Internal endpoints are named in **private hosted zones (`*.internal`)** and certified by a
**self-signed internal CA** whose root is distributed to the client surfaces; the public domain, the public
hosted zone and public ACM certificates arrive only at **Stage 13**, with the public web tier.
**Split-horizon DNS is not built.**

**Related decisions:** [D4](D04-vpn-wireguard.md) (the VPN is the only way in), [D8](D08-gitlab-hosting.md),
[D14](D14-supply-chain-account.md), [D26](D26-unified-studio.md)

**Referenced by stages:** [Stage 1b](../stages/stage-01b-identity-and-controls.md),
[Stage 3](../stages/stage-03-networking.md), [Stage 7](../stages/stage-07-gitlab-runners-ecr.md),
[Stage 13](../stages/stage-13-public-web-tier.md)

---

## The problem

ACM cannot issue a certificate for `gitlab.prod.internal` — a public certificate requires a domain whose
control can be validated publicly — and AWS Private CA costs ~USD 400/month (~USD 50/month in short-lived
mode), both far over the D12 ceiling. So an internal HTTPS endpoint needs *some* answer, and there are only
three: a public domain plus public ACM certificates, a managed private CA, or a CA of our own.

## What was decided first, and why it changed

The original decision (2026-08-07) took the first option: register one public domain, keep a public hosted
zone **for DNS validation only**, issue free public ACM certificates, and resolve the names to private
addresses through a private zone — split-horizon DNS. That put a **user input (the domain name) on the
critical path of Stage 7**, and it was the only such input in the whole plan.

**What changed on 2026-08-09:** `CLAUDE.md` now states explicitly that GitLab and GitLab Pages are reachable
**only through the intranet (VPN)** and never face the public internet. That makes the whole interactive
layer a closed audience, and it exposes what the public domain was actually buying: not reachability —
nothing is published — but only **a trust chain that browsers already ship**. For an audience of three
clients that we build ourselves, that convenience is purchasable more cheaply, and it is not free of cost:

- **A public ACM certificate is published to Certificate Transparency logs.** Issuing one for
  `gitlab.<domain>` and `*.pages.<domain>` makes the internal name inventory public knowledge, permanently
  and by design, for endpoints that resolve to nothing outside the VPN. ACM exposes a switch to disable CT
  logging, but browsers require the SCTs a public certificate carries, so the switch is not usable in
  practice. **The public path leaks names; the private path does not.**
- It buys a recurring public footprint (a registered domain, a public zone) for a lab that has, until
  Stage 13, no public anything.

So the decision is **not reversed, it is phased**: the original mechanism is exactly right *for the thing
that is actually public*, which is the Stage 13 web tier, and wrong as a prerequisite for everything before it.

## Phase 1 — Stages 3 to 12: internal names, internal trust

1. **Naming.** Every internal endpoint lives in a Route 53 **private hosted zone** per account
   (`sandbox.internal`, `prod.internal`, …), `[P]`, associated cross-account with the VPCs that must resolve
   it (Stage 3 step 4). No public zone, no registered domain, no split-horizon.
2. **Trust.** One **internal root CA**, generated once and living in `production/foundation/` `[P]` — the
   only pre-Stage-13 TLS consumers (GitLab, Pages) are in Production. Leaf certificates are issued from it,
   including the wildcard GitLab Pages requires, and **imported into ACM** for attachment to an internal
   ALB — ACM accepts imported certificates, charges nothing for them, and an ALB serves them like any other.
   Terminating on the instance's own nginx instead is a live option (Stage 7 step 1); the CA is the same
   either way.
3. **Distribution — this is the real cost of the decision, and it is a build dependency, not a runbook
   note.** The root has to be in the trust store of every client that speaks to an internal endpoint:
   the **laptop** (macOS keychain, and `git`/`curl`/Python each with their own opinion about CA bundles),
   the **`dev-env` image** (baked in at build time, so notebooks can `git clone`), and the **GitLab
   runners** (user data). That is three surfaces, they live in three accounts, and a missed one fails as an
   opaque TLS error rather than as an access denial — tracked as **INT-19**.
4. **The CA private key is state.** Generating it with the Terraform `tls` provider puts it in the state
   file; the state bucket's KMS key is then inside the CA's trust boundary. Acceptable at lab scale and
   stated rather than discovered — the alternative, generating it offline and keeping only the certificate
   in Terraform, is available if the trade stops being comfortable.
5. **Lifetimes.** ACM does **not** renew imported certificates. Issue leaves at or below **398 days** — do
   not rely on trust stores exempting locally-installed roots from that cap — and treat renewal as a
   scheduled re-import, recorded in Stage 12's operational checks.

**AWS-served surfaces need none of this** and are the second half of the answer: the Identity Center access
portal (`https://<id>.awsapps.com/start`), the Unified Studio portal (an AWS-generated URL — record the
exact host at Stage 6), ECR, CodeArtifact, EFS mount targets and every interface-endpoint name are named and
certified by AWS. Where a name has to resolve *privately*, that comes from **private DNS on the interface
endpoint**, not from anything we register.

## Phase 2 — Stage 13: the public domain, for the thing that is public

Stage 13 registers the domain, creates the **public** hosted zone, and issues public ACM certificates for
the public ALB (and, for CloudFront, in `us-east-1` — `plan/architecture.md` §4.1). This is the original
D15 mechanism, applied to the one tier it fits.

**One question is deliberately left to Stage 13 rather than answered here:** whether the internal endpoints
then move onto a subdomain of the registered domain (reviving split-horizon and retiring the internal CA) or
stay on `*.internal` permanently. The trade is trust-distribution effort against a public name inventory,
and it should be decided with the private CA already built and its real friction measured — not predicted now.

## Cost

| | Before Stage 13 | From Stage 13 |
|---|---|---|
| Public hosted zone | — | ~USD 0.50/mo |
| Domain registration | — | ~USD 12-15/year (~USD 1/mo) |
| Private hosted zones | ~USD 0.50/mo each | idem |
| Certificates | **0** (own CA, ACM import is free) | 0 (public ACM) |

The revision takes ~USD 1.50/month off the pre-Stage-13 floor. That is not the argument — the argument is
the name leak and the removed blocker — but `plan/cost-model.md` and `PRICING.md` carry it.

## Consequences

- **Stage 7 no longer blocks on a user input.** The only remaining input for the domain name is Stage 13.
- **Stage 3 loses the split-horizon zone and one of its three cross-account associations.**
- **Stage 1b's region-exemption list keeps `acm:*` but does not need `route53domains:*` until Stage 13** —
  registration is the only `route53domains` call, and it happens once, there.
- **A new build dependency exists that did not before:** the `dev-env` image and the runner AMI/user data
  carry the internal root. INT-19.
- **Nothing here re-opens OIDC.** Principle 2 rules out OIDC federation for CI because a VPN-only GitLab
  cannot serve a JWKS that IAM can *fetch* — that is about reachability, not about naming, so registering a
  domain at Stage 13 does not change it.

## Revision trigger

Re-open if any of these becomes true: a client surface appears that we do not build and cannot inject a CA
into (a managed service calling an internal endpoint, a third party); the trust distribution breaks twice in
a way that costs a session; or AWS Private CA's short-lived mode falls inside the D12 ceiling.

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
