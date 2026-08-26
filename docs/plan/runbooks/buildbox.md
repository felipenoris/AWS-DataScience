# Runbook — the buildbox

The `amd64` build host of [Stage 6 step 5.0](../stages/stage-06-unified-studio.md), in the Sandbox
account. Slice: [`terraform-live/sandbox/buildbox/`](../../../terraform-live/sandbox/buildbox/README.md).
Layer **`[E]`** — created for a build session, destroyed at the end of it.

**The estate-wide picture — every VPC, route and address, and where this host's one route sits in
them — is [`docs/NETWORK.md`](../../NETWORK.md).** This file stays the procedure.

## D. What it is

One EC2 instance (`t3.xlarge`, 64 GiB gp3, both selectable in the tracked
`instance_type.auto.tfvars` beside the slice), with docker and git installed at first boot, plus the
one route that gives it a way out. It holds nothing worth keeping: the volume dies with the
instance, the state carries no secret, and anything that must survive leaves as an image in ECR.

## M. Why it exists

**The images this estate runs on are `linux/amd64` and the laptop is `arm64`.** SageMaker instance
types are x86 and `sagemaker-distribution` publishes `-cpu`/`-gpu` tags with **no `arm64` variant at
all** (measured 2026-08-21 from the public registry's tag list); the laptop also has no docker. So
[`images/`](../../../images/README.md) — `base` and `dev-env` — is built here rather than there, on a
machine of the right architecture, inside the perimeter, that exists only while a build runs.

It is a **builder, not a workstation**. It cannot push: its role carries Session Manager and no
`ecr:` permission at all, because the Production registry grants the Interactive accounts a *pull*
and nothing more. The push is step 5.0's own act, from an identity that may — **§P is how that
identity reaches a host that has none, and why the two acts share one session**.

## C. The components, and how they connect

| Piece | Where | What it does |
|---|---|---|
| the instance | isolated tier, no public IP | the build host itself |
| its security group | the slice, `[E]` | **egress only — no ingress rule at all.** Session Manager needs none |
| **the route** | `0.0.0.0/0` in the **isolated** route table, `[E]` | sends this tier's default at the WireGuard host's **ENI** |
| `vpc_nat_cidrs` | `sandbox/vpn/`, module `wireguard-v0.4.0`, `[D]` | makes that host a **NAT instance** for this tier: source/dest check off, MASQUERADE + FORWARD in `wg0`'s `PostUp` |
| the WireGuard **security group** | `sandbox/foundation/vpn-anchors.tf`, `[P]` | admits the isolated tier's ranges **inbound**. Without it the other three do their jobs and the packet is dropped on arrival |

**Those last three are one path in three slices, and that is what made the gap easy to miss.** Reach is
an **intersection** (Lesson 28): the first apply had the route and the masquerade and no security-group
rule, so the host booted, installed its packages through the S3 gateway endpoint, and then timed out on
`ssm.<region>.amazonaws.com`. Nothing in any single file was wrong.

**In: nothing.** There is no ingress rule at all — the *"reachable only over the VPN"* requirement was
**withdrawn by the user on 2026-08-21** rather than delivered in name only: the rule that used to be here
did not gate the shell (`ssm start-session` reaches the agent's *outbound* channel and no security group
sees it) and it left port 22 reachable on a host with no authorized keys. **What gates the shell is IAM** —
for the six persona sets the VPN still does; for `InfrastructureAccess` it does not, by open question 17,
option (a). A port served during a build is reached with SSM **port forwarding**, not with an ingress rule.

**Out:** through the WireGuard host, the single public egress of this design. **No NAT gateway is
involved**, so `egress/` need never be up for a build — 0.160 USD/h not spent. **That is true of the
route and not of the names** — see the last coupling below.

**Three couplings worth holding in mind:**

- **Three lifetimes, one path.** The security group is `[P]` (a private range, admitting a tier that is
  empty between sessions), the masquerade rules are `[D]` with the host, and only the **route** is `[E]`.
  So the reach is the one thing that comes and goes.
- **The capability is `[D]`, the reach is `[E]`.** A masquerade rule matches nothing until a route
  table sends traffic at it. Turning `vpc_nat_cidrs` on is one standing attribute; everything
  metered comes and goes with the session. (`vpn.md` §S carries the rest, including why the rules
  ride `PostUp` rather than the user data.)
- **A stopped WireGuard host makes the route a blackhole**, not an error — every symptom then looks
  like a broken package mirror. `up` starts it; `down` does **not** stop it (it is `[D]` and shared).
- **It must not coexist with `sandbox/probes/`.** That slice's perimeter probe measures the isolated
  tier's *absence* of a default route; this one adds one. `buildbox.py` refuses rather than warns.
- **`egress/` is irrelevant to this host's ROUTE and hostile to its NAME RESOLUTION** — so **build with
  `egress/` DOWN**, which is the normal state anyway (measured 2026-08-23). Design A's DNS Firewall rule
  group associates to the **VPC id**, not to a route table, so while `egress/` is up every lookup from
  this host is judged by an allow-list written for the SageMaker subnets — and `public.ecr.aws` and
  `static.rust-lang.org`, two of the five things a build pulls, are **deliberately off it**: both are
  CNAMEs into a shared CDN, DNS Firewall evaluates the whole chain, and the only thing that would make
  them resolve is allowing the CDN namespace, which ends the control (Stage 6 step 4.3). **Adding the
  names does not fix it, and the list is not the place to try.** Never yet exercised: no build has run
  while `egress/` was up. **The symptom distinguishes the two failures** — a blackholed route hangs, a
  blocked name returns *no such host* immediately — and the rule action is in
  `/awsds/sandbox/dns-firewall`, where the block is reported against the **queried** name even when a
  CNAME target is what matched. The list is `terraform-live/sandbox/egress/main.tf`, and its own plan
  never converges (`EXC-04`).

## U. Up

```bash
./scripts/buildbox.py up && ./scripts/buildbox.py sync && ./scripts/buildbox.py ssm
```

`up` refuses if a probe instance exists, starts the WireGuard host if it is stopped, applies the
slice, and waits for Session Manager. `sync` puts `images/` at `/opt/awsds/images` — the one write
API in the tooling (`ssm:SendCommand`), fenced the way `./aws/vpn.py --on-host` is. `ssm` opens the
shell.

**In the session you are `ssm-user`, not `ec2-user`** — Session Manager creates that account on its
first connection, so the first boot cannot add it to the `docker` group. Use `sudo docker …` or
`sudo -iu ec2-user`. Then:

```bash
cd /opt/awsds/images && sudo docker build -t awsds/base:local base && sudo docker build -t awsds/dev-env:local dev-env
```

**`dev-env` is `FROM base`, so any change to `base` rebuilds `dev-env` from its first layer** — Julia,
R and Rust download again. That is the price of D17's single ancestor and it is paid on every edit to
`images/base/`, not only on the big ones. It also means a rebuild writes a **second** copy of a ~17 GB
image before the old one loses its tag: read §S before starting one on a disk you have not looked at.

**If it never registers with SSM**, the route is failing nine times out of ten. Read the first boot
without SSM: `aws ec2 get-console-output --instance-id <id> --latest`, and `/var/log/awsds-buildbox-boot.log`
once you are in — its egress check prints the public address the host leaves under, which must be the
WireGuard Elastic IP.

To test a docker container:

```bash
sudo docker run --rm -it awsds/dev-env:local bash
```

Neither `Dockerfile` sets an `ENTRYPOINT` or a `CMD` — that is the SMUS BYOI rule, not an omission — so
both are inherited from the distribution: `/usr/local/bin/_entrypoint.sh` with `/bin/bash`, running as
`sagemaker-user` in `/home/sagemaker-user`. The entrypoint activates the conda environment and `exec`s
what you passed, which is why the run above is also the cheapest proof that the rule was respected.

## S. Space — checking it, and getting it back

**The root volume is 64 GiB and the two images are most of it.** `base` is ~12 GB and `dev-env` ~17.4 GB
(measured 2026-08-21, first build). A rebuild is where the wall is actually hit, because the new image is
written *before* the old one loses its tag, and the failure arrives mid-build as `no space left on
device` — after the twenty minutes, not before.

```bash
df -h / && sudo docker system df
```

**Read them in that order and do not add the two image sizes together.** `df` is the truth about the
filesystem; `docker system df` says who is holding it, split into Images / Containers / Build Cache with
a RECLAIMABLE column. The `SIZE` column of `docker images` counts **shared layers once per image**, so
`base` at 12 GB and `dev-env` at 17.4 GB are not 29.4 GB on disk — `dev-env` *contains* `base`'s layers.
`docker system df` is the one that de-duplicates. `-v` breaks it down per image and per cache record.

**Dropping the notebook image:**

```bash
sudo docker rmi awsds/dev-env:local
```

It frees the **delta**, not the 17.4 GB: `base` still references the shared layers below. If a container
still exists from that image the removal is refused — `sudo docker ps -a`, then `sudo docker rm <id>`
(a `docker run --rm` has already done this for you).

**What usually holds the space is not an image.** After a rebuild the previous `dev-env` is still there,
untagged, holding its unique layers, and the build cache holds another copy of everything expensive:

```bash
sudo docker image prune && sudo docker builder prune
```

The first removes dangling images (no tag, nothing referencing them), the second the build cache. Both
are safe: neither touches a tagged image, and the cache only costs time to rebuild. **`docker system
prune -a` is a different thing** — it removes every image not backing a running container, `base`
included, so the next build starts by pulling the distribution again.

**And the escape hatch is the layer.** This host is `[E]` and holds nothing worth keeping: if the disk
is a mess, `down` then `up` gives a clean 64 GiB in about two minutes. Weigh it against a full rebuild
(~20 minutes) — pruning first is nearly always the cheaper move, recreating is for when it is not.

## P. Push — the one act this host cannot do under its own name

**Build and push are ONE session, and that is a property of the layer rather than a preference.** The
volume dies with the instance (§D), so a `down` between the two acts throws the build away — measured on
2026-08-22, when the host was absent and the 2026-08-21 images with it. Until this section existed the
two were described in consecutive sentences that read as two sittings; the cost of that reading is the
full rebuild, and the rebuild is the twenty minutes, not the push.

**Why the identity has to arrive from somewhere else — read from the live registry, 2026-08-22, not
inferred.** Both repository policies carry exactly one statement, `AllowConsumerAccountsToPull`, granting
the two Interactive accounts `BatchCheckLayerAvailability`, `BatchGetImage`, `GetDownloadUrlForLayer` and
`DescribeImages`. **No statement anywhere grants a push to anybody**, and none needs to: same-account
access is decided by the identity policy alone, so the push is a **Production** principal's act and can
be nothing else. Giving this instance's role an `ecr:` permission would not change that — it would meet
a repository policy that offers Sandbox a *pull*, which is the design (§M), not an oversight.

**So the credential travels and the permission does not.** `ecr:GetAuthorizationToken`, called on the
laptop as `awsds-infra-prod`, mints a 12-hour bearer token that the docker client presents to the
registry: what authorizes the upload is the **token's identity**, not the host holding it. Nothing here
is granted to the buildbox, nothing survives the session, and the box's role is untouched.

**The ceiling permits this and forbids its mirror image**, which is worth knowing before the first
`InitiateLayerUpload` fails and gets blamed on the relay. `awsds-org-scp-perimeter`'s
`DenyEcrPushOutsideOrganization` denies the four push actions when `aws:ResourceOrgID` is **not** ours —
it is the exfiltration shape, our layers into somebody else's registry — and `awsds-org-rcp-perimeter`'s
`EnforceOrgIdentitiesOnRegistry` denies `ecr:*` to principals outside the organization. This push is an
org identity into an org registry and neither statement sees it.

### The relay

On the **laptop** — SSO user: the **infrastructure user**; account: **Production**; permission set:
**`InfrastructureAccess`**, through `awsds-infra-prod`. The first command prints the two registry URIs
(the host part before the first `/` is the registry); the second prints the token, and only the token:

```bash
aws ecr describe-repositories --profile awsds-infra-prod --region us-west-2 --query 'repositories[].repositoryUri' --output text
```

```bash
aws ecr get-login-password --profile awsds-infra-prod --region us-west-2
```

In the **buildbox session**, take it without echoing it. `read -rs` keeps the token off the screen and out
of the shell history, and nothing else records it: the account has **no `SSM-SessionManagerRunShell`
document** (measured 2026-08-22), so Session Manager runs on defaults and no session stream is logged.
The daemon runs as root and every build command here is `sudo docker`, so the login has to be `sudo`
too — otherwise the credential lands in `ssm-user`'s config and the push looks unauthenticated.

```bash
read -rs ECR_TOKEN
```

```bash
REGISTRY=<the host part of either URI>
```

```bash
echo "$ECR_TOKEN" | sudo docker login --username AWS --password-stdin "$REGISTRY" && unset ECR_TOKEN
```

### Tag, push, record

**The repositories are `IMMUTABLE`, so a tag is spent the first time it lands** — a re-push under the
same tag is refused, and that is the control rather than a nuisance (`images/README.md`). Pick the tag
deliberately: the first one written here is the convention Stage 8's pipeline inherits.

```bash
sudo docker tag awsds/base:local "$REGISTRY/awsds-prod-ecr-base:v0.1.0" && sudo docker tag awsds/dev-env:local "$REGISTRY/awsds-prod-ecr-dev-env:v0.1.0"
```

```bash
sudo docker push "$REGISTRY/awsds-prod-ecr-base:v0.1.0"
```

```bash
sudo docker push "$REGISTRY/awsds-prod-ecr-dev-env:v0.1.0"
```

```bash
sudo docker logout "$REGISTRY"
```

**Both digests go in the stage log** — Stage 6 step 5.1 registers a SageMaker image *version* against
one of them, and Stage 7 step 2.6 has to be able to say which digest its CA rebuild replaced. Read them
back from the laptop rather than from the push output:

```bash
aws ecr describe-images --profile awsds-infra-prod --region us-west-2 --repository-name awsds-prod-ecr-base --query 'imageDetails[].{Tag:imageTags[0],Digest:imageDigest,Bytes:imageSizeInBytes}' --output table
```

### What the bytes do on the way out

**The push does not touch the S3 gateway endpoint, and the endpoint policy's missing `PutObject` is not
a gap.** AWS's own page is explicit in both directions: `ecr.dkr` is the Docker Registry API and *"Docker
client commands such as `push` and `pull` use this endpoint"*, while the S3 gateway endpoint exists so
that containers **downloading** an image can fetch the layers — its documented minimum is `s3:GetObject`
on `prod-<region>-starport-layer-bucket`. Sandbox's endpoint policy grants exactly that plus
`ListBucket`, which is the pull path Stage 3 already provided for; the push uploads its layer parts to
the registry endpoint instead.

**And the Sandbox VPC has no interface endpoint of any kind** (measured 2026-08-22 — the `egress/`
slice that would carry them is `[E]` and down), so `dkr.ecr` resolves to its public address and the
upload leaves through the default route: the WireGuard host, a `t3.nano`, doing NAT for this tier (§C).
**That path is proven rather than novel** — the build pulls the SageMaker distribution and every Julia,
R and Rust artifact through the same instance, in the same hop, and the first build did it clean. The
push is the same order of magnitude in the other direction, so budget the time and do not go looking
for a broken mirror when it is merely slow.

**Do not size it from `docker images`.** That column is uncompressed and counts shared layers once per
image; ECR stores layers **compressed** and **per repository**, so `dev-env` uploads its copy of
`base`'s layers again into the second repository. Two repositories, not one deduplicated push.

## X. Down

```bash
./scripts/buildbox.py down
```

Destroys the host **and the route**, so the isolated tier goes back to having no default route. It
deliberately leaves the WireGuard host running — `make down ENV=sandbox` is what stops that.

**`./scripts/buildbox.py status` is the reading**, and the reason to take it: `t3.xlarge` is
**0.1664 USD/h** (`PRICING.md` §8) — a week left up is USD 28 against D12's USD 50/month.

## Setting up github conectivity

```
ssh-keygen -t ed25519 -C "<EMAIL>"
eval "$(ssh-agent -s)"
cat ~/.ssh/id_ed25519.pub
```

- go to <https://github.com/settings/keys> and add new ssh key. paste pulic key.

- Clone with git protocol:

```
git clone git@github.com:felipenoris/AWS-DataScience
```
