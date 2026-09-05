# D4 — VPN technology

**Status:** Decided (2026-08-07): **self-managed WireGuard**

**AMENDED 2026-09-05 (the 6b/6c re-scope):** the technology is unchanged and the **home moves** — the host leaves Sandbox for `VPC-Networking` in Production, its Elastic IP is *transferred* rather than reallocated (so no client `.conf` changes its `Endpoint`), and its second job as a NAT instance for the isolated tier **ends** with the buildbox's move. The host now forwards tunnel packets to RFC1918 destinations only and drops the rest: a VPN client is a client of the private network and reaches the internet through the proxy like every other one ([D38](D38-single-egress-hub.md), [Stage 6c](../stages/stage-06c-networking-hub.md)).

**In one line:** Self-managed WireGuard on the smallest burstable instance, layer `[D]`; Client VPN documented as the managed alternative. *(`t4g.nano` as decided; **`t3.nano` since the amd64 move of 2026-08-20** — the shape is the decision, the architecture is not.)*

**Related decisions:** —

**Referenced by stages:** [Stage 4](../stages/stage-04-vpn.md)

---

## Rationale and consequences

A `t4g.nano` EC2 instance in a public subnet, layer `[D]` — stopped between sessions, not destroyed, so the host key and peer configuration stay stable. *Qualified 2026-08-16, after Stage 3 executed:* `[D]` protects the instance from the **machinery**, not from **Terraform** — the SSM-resolved AMI forces a replacement whenever the parameter moves, and an instrument's user data needs `user_data_replace_on_change = true` — so the host key stays stable by living **outside** the instance (the git-ignored `.tfvars`, Stage 4 decision 4), not by the instance never dying. Idle cost is its 8 GB EBS volume (~USD 0.65/month) plus the Elastic IP, which lives in the `[P]` foundation slice (~USD 3.65/month) so the endpoint address never changes. Consequences to handle in Stage 4: no native Identity Center integration, so peer public keys are provisioned by Terraform from a git-ignored variable file; and it is a single point of failure, which is acceptable for a lab. AWS Client VPN (~USD 73/month, SAML to Identity Center) stays documented as the managed alternative if SSO-integrated VPN becomes a requirement.

*Amended 2026-08-20, on the user's direction: **the host is amd64**, `t3.nano`, not the `t4g.nano` decided above.* What this decision actually turns on is the **shape** — the smallest burstable instance there is, because the host forwards packets and does nothing else — and every argument above is written about that shape, about the `[D]` layer, or about Client VPN's price. **None of them is an argument for Graviton**: it was picked when this decision was written for the ~20% it saves, which at this size is **USD 0.0010/h** on a host that is powered off between sessions. So the amendment costs what that fraction is worth and changes nothing else here. What it *does* change is recorded where it bites: the `wireguard` module's AMI (`…-arm64` → `…-x86_64`, tag `wireguard-v0.3.0`), the closed list of `sandbox/vpn/`'s `instance_type` (`t4g.*` → `t3.*`, which **follows** the image and does not choose it), and the baseline the cost tables price (`docs/PRICING.md` §3 and §8, `scripts/tfhygiene/layers.py`, `./aws/vpn.py`'s `BASELINE_INSTANCE_TYPE`). The move is a **host replacement** rather than a resize — an AMI is specific to its processor architecture — which the qualification above already covers: the host key survives it because it lives outside the instance, and so does the address, so no client `.conf` moves. `docs/plan/runbooks/vpn.md` §S6 carries the procedure and what does not survive (the root volume, and anything ever put on it by hand).

---

*Index: [decisions/INDEX.md](INDEX.md) · Plan core: [GENERAL_PLAN.md](../../GENERAL_PLAN.md)*
