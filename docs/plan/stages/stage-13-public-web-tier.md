# Stage 13 — Public-facing web tier (experiment)

| | |
|---|---|
| **Status** | not started — **re-scoped 2026-09-05 by [D38](../decisions/D38-single-egress-hub.md) and rewritten into the action-checklist format.** The public tier lands in **`VPC-Networking`'s public tier**, the estate's only internet-facing tier, with IP targets reaching the backend in `VPC-Workloads` over the peering. The ALB becomes the **second enumerated listener** there (the WireGuard endpoint is the first), and `docs/AWS_STATE.md` carries that enumeration — a world-open rule anywhere else is a finding. The public DNS half (D15 phase 2) is unchanged and still needs the domain name from the user |
| **Prerequisites** | [6c](stage-06c-networking-hub.md) (the hub and its public tier; the Networking↔Workloads peering), [Stage 9](stage-09-deployment-targets.md) (a backend to front). **The domain name from the user** — this is the only stage that needs it, and the only blocking input left in the whole plan |
| **Consumes** | [D15](../decisions/D15-tls-internal.md), [D36](../decisions/D36-internal-pki.md), **[D38](../decisions/D38-single-egress-hub.md)** |
| **Proves** | that the ingress enumeration of 6c step 1.4 survives its first real addition — the only stage that tests it |

*Read with [`docs/NETWORK.md`](../../NETWORK.md) (the hub's public tier and what may terminate there) and
[`docs/plan/conventions.md`](../conventions.md).*

---

**Objective:** the experiment `CLAUDE.md` describes — a public web server reaching a private backend — and,
since D15's revision, **the only stage where public DNS enters the project at all**. Everything before it is
named in private hosted zones and certified by the internal CA; nothing before it is registered, published
or resolvable from outside the VPN.

## Who executes each action

| Marker | Meaning |
|---|---|
| **[Claude]** | repository edits and read-only AWS calls — done without asking |
| **[Claude⚡]** | `terraform apply` or any AWS write — only after the user authorizes that specific action in chat, with the SSO user / account / permission set stated first |
| **[user]** | the domain name, the registration, every DNS decision, and every log entry |
| **[Claude reads, user decides]** | a measurement Claude takes and a choice only the user can make |

## Step numbers are identifiers, not an order

**Step 1 comes first for a scheduling reason, not a dependency one**: registration and validation are slow,
and discovering that after the ALB is built wastes a sitting. Steps 2-4 are the build; step 5 is the
teardown contract; step 6 is the decision D15 deliberately left here.

---

## To execute

### 1. Register the domain and create the public hosted zone (D15 phase 2)

**Action:** the project's first and only public name. **Why:** everything downstream needs a validated
certificate, and ACM validation waits on DNS. **Explanation:** this is the only use of `route53domains:*` in
the project — Stage 1c step 7's region-exemption list carries it for exactly this moment.

- **1.1 — [user] Supply the domain name.** Nothing else in this stage can start.
- **1.2 — [user] Register it** and create the public hosted zone (Management or Production per the
  registrar's constraint; record which, because it decides where the delegation lives).
- **1.3 — [Claude] Record the new zone in `NETWORK.md` §10 beside the private ones** — the first row in that
  table that is resolvable from outside, which is the fact worth making visible.

### 2. Build the public tier in `VPC-Networking`, and enumerate it

**Action:** a public ALB with WAF and a public ACM certificate, in the hub's public tier. **Why:** D38 makes
that tier the estate's only internet-facing one; a public ALB anywhere else would create a second ingress
and break the invariant 6c step 1.4 wrote. **Explanation:** the ALB is `[E]` — an ALB cannot stop, so if it
exists it bills.

- **2.1 — [Claude] Write `production/webtier/`** — a new `[E]` slice with its own rank, reading
  `production/networking/`'s public subnets and `production/workloads/`'s private ones. Two slices, not one:
  the hub's `[P]` network must not be opened to change an experiment's listener.
- **2.2 — [Claude⚡] Issue the public ACM certificate** against 1.2's zone. **For a CloudFront variant it
  must be issued in `us-east-1`** — which is what `acm:*` is exempted from the region control for.
- **2.3 — [Claude⚡] Create the ALB with WAF** in the hub's public tier, HTTPS only, HTTP redirecting.
- **2.4 — [Claude] Add the listener to the ingress enumeration** in `docs/AWS_STATE.md` — the **second**
  row, after the WireGuard endpoint's UDP/51820. **This is the step that keeps 6c's invariant true**, and
  `./aws/networking.py`'s no-public-address gate (6c step 1.5) fails without it.

### 3. Put the application behind it, in `VPC-Workloads`

**Action:** the app on ECS Fargate in `VPC-Workloads`' private tier, reached as **IP targets over the
peering**. **Why:** peering shares an address and never a path (Lesson 44), and an ALB target group of IP
targets is exactly an address — which is why this works while "route the ALB's traffic through the peering"
would not. **Explanation:** the backend never gains a public address and never gains a default route; its
outbound calls, if any, cross the proxy like everything else.

- **3.1 — [Claude] Write the ECS service** in `VPC-Workloads`' private subnets, image from ECR by digest.
- **3.2 — [Claude] Register it as an IP target group** on 2.3's ALB, with the health check crossing the
  peering. **Read the cross-AZ peering charge** before pinning: same-AZ is free, cross-AZ is charged each
  way (6c step 7.4's PRICING rows).
- **3.3 — [Claude] Write the data tier** — RDS, or the Iceberg catalog through Athena — in the isolated
  subnets, reached only from the app's security group.
- **3.4 — [Claude] Write the security groups as a chain**: ALB → app → data, and nothing else. No rule in
  this stage may admit `0.0.0.0/0` except the ALB's own listener.

### 4. Prove the two directions

**Action:** one reading that the public path works and one that the private path did not widen. **Why:** the
whole value of putting this in the hub is that it changes nothing about what a spoke can reach.
**Explanation:** both are distinguishable outcomes, not a single "it loads".

- **4.1 — [user] Load the site from a browser with the tunnel DOWN** — it answers, on a public certificate.
- **4.2 — [Claude] Re-run `./aws/networking.py`** — the no-public-address gate still passes everywhere
  outside the hub's public tier, and `NT-3`/`NT-6` still show no path between an Interactive VPC and
  `VPC-Workloads`.

### 5. Write the teardown contract before anything is public

**Action:** state what tearing this down means, including the DNS. **Why:** a record left behind after
teardown points the world at something that no longer exists — or worse, at whatever takes the address next.
**Explanation:** public DNS is part of the blast radius now, and it is the part that outlives the resources.

- **5.1 — [Claude] Write the teardown order into the slice's README**: records first, then the ALB, then the
  certificate, then the service.
- **5.2 — [Claude] Add the dangling-record check** to `./aws/networking.py`: every record in the public zone
  resolves to something this project still owns.

### 6. Take the decision D15 deliberately left here

**Action:** decide whether the internal endpoints stay on `*.awsds.internal` with the internal CA, or move
onto a subdomain of the registered domain with split-horizon DNS and public ACM. **Why:** the trade is now
measurable rather than predicted. **Explanation:** **defaulting silently to "we have a domain now, use it
everywhere" is the outcome to avoid** — it is a real change in what is publicly known about this
environment.

- **6.1 — [Claude] Put the two costs side by side**: the internal CA's distribution friction, **measured**
  at Stage 7 (four surfaces, one rebuild, INT-19's failures) — against publishing the internal name
  inventory in **Certificate Transparency logs**, which is what public ACM does to every name it certifies.
- **6.2 — [Claude reads, user decides] Record the decision either way**, in D15's file with a dated line.

---

## Deliverables

- A public site answering off-VPN on a public certificate, in the hub's public tier and nowhere else.
- The ingress enumeration in `AWS_STATE.md` carrying its second row, with the gate still green.
- A backend in `VPC-Workloads` with no public address and no default route.
- A teardown contract that includes the DNS, and a check that enforces it.
- D15's remaining question answered with a dated line.

## Validation

1. `./aws/networking.py` — the no-public-address gate passes outside the hub's public tier; `NT-3`/`NT-6`
   unchanged.
2. The site loads with the tunnel down; the backend is unreachable from anywhere but the ALB.
3. `./aws/egress.py` §6 at session end — the ALB is `[E]` and burns while it exists.

## Risks

- **A public ALB outside `VPC-Networking` breaks the estate's single-ingress invariant** — 2.4's
  enumeration and 6c step 1.5's gate are the controls, and this is the first stage that tests them.
- **A dangling public record outlives the teardown** and can be taken over — 5.2 is the check.
- **Public ACM publishes every certified name in Certificate Transparency** — which is precisely the
  argument step 6 must not skip.
- **Do not read this stage as unblocking OIDC for CI.** Principle 2 rules OIDC out because a VPN-only
  GitLab cannot serve a JWKS that IAM can *fetch*. That is reachability, not naming: registering a domain
  changes nothing about it.

---

*Stage index: [stages/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
