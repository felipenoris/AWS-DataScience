# sandbox/egress/ - the [E] metered network of a business unit's sandbox (Stage 3 pass 3):
# the NAT under design A, the interface endpoints of step 8's Sandbox list, and step 9's
# org policy on every one of them. THE REPOSITORY'S FIRST [E] SLICE: its lifecycle belongs
# to `make up ENV=sandbox` / `make down ENV=sandbox` (D11), never to a by-hand apply
# (runbook, "What you never do") - a forgotten session costs ~USD 3.84/day and no budget
# alert exists to say so (D12); `./aws/egress.py` 6 is the burn meter that risk gets.
#
# foundation/'s [P] facts arrive through terraform_remote_state - the read its outputs.tf
# announces - never pasted (Lesson 3) and never looked up by tag: a tag lookup answers
# "what matches", remote state answers "what foundation/ BUILT", and for wiring two slices
# of one account the second question is the one being asked.

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.4.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3), not the outcome - D5's
  # comparison against B (no default route, CodeArtifact as the package path) is Stage 6's.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9); the maps stay keyed by
  # zone id, so this is a selection, not an anchor on list position.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Sandbox row: the three SageMaker endpoints (sagemaker.studio is what lets
  # JupyterLab/Code Editor apps START in a VPC-only domain). elasticfilesystem sat here
  # until 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  # `datazone` JOINED THE LIST AT STAGE 6 STEP 4.2 (2026-08-21) ON A MISREAD, measured
  # 2026-08-24. The sentence here used to claim the network-isolation page marks it "REQUIRED
  # under VpcOnly, so an app cannot reach the domain without it" - three errors in one clause:
  # the page's required table is scoped by its OWN premise ("access to the public internet is
  # denied from the VPC" - design B, never VpcOnly); under design A the app reaches DataZone
  # through the NAT (datazone.<region>.api.aws is on the list below); and the entry is not
  # free - its private DNS zone is AUTHORITATIVE FOR THE WHOLE SUBTREE, so
  # agent.datazone.<region>.api.aws, which the SAME page's public-internet table says the
  # portal front-end needs, is NXDOMAIN for every client of the VPC resolver, the full-tunnel
  # laptop included: the portal broke ON the VPN while this slice was up (Lessons 40-42).
  # REMOVAL IS RECOMMENDED AND PENDING the user's authorization - today the app's calls ride
  # this endpoint (CloudTrail), so the removal's prediction, that they move to the NAT, is
  # measured at the apply rather than assumed. The rest of the required table
  # (docs/SMUS.md §VpcOnly is the one copy - fifteen names) is added by MEASUREMENT and not by
  # copying: verification (viii) reads the flow logs of a working session and only what is
  # exercised gets an endpoint, at +USD 0.010/h each, per account, for the whole session.
  #
  # TWO ENTRIES OF THAT TABLE CANNOT BE SETTLED BY ADDING THEM HERE, and both are recorded so
  # nobody "fixes" them:
  #   s3   this account already has a [P] GATEWAY endpoint whose prefix-list route is more
  #        specific than any default, so S3 traffic may never reach an interface endpoint at
  #        all - and the request then presents the GATEWAY's aws:SourceVpce. Which one wins,
  #        per project subnet, is verification (xix), and flow logs are the wrong instrument
  #        (gateway traffic crosses no ENI): the field is CloudTrail's vpcEndpointId.
  #   q    the doc pairs it with com.amazonaws.US-EAST-1.codewhisperer, and an interface
  #        endpoint is regional - so under design B the Amazon Q surface has no private path
  #        from us-west-2 at all. Record what breaks at 4.3 rather than assuming either way.
  extra_services = ["sagemaker.api", "sagemaker.runtime", "sagemaker.studio", "datazone"]

  # DESIGN A's CONTROL (Stage 6 step 4.1) - the allow-list that makes the NAT "limited
  # internet" instead of internet. The module refuses to enable itself under
  # egress_mode = "B", where a name filter would be a control over a route that does not
  # exist.
  dns_firewall = true

  # HOW THE ALLOW-LIST BELOW IS READ, and it is this slice's call rather than the module's
  # (v0.4.0 - the module defaults to INSPECT_REDIRECTION_DOMAIN, the API's own default and the
  # stricter reading). TRUST means the firewall inspects the name that was QUERIED and trusts
  # the CNAME/DNAME chain beneath it. This account reaches package artifacts, and every
  # ecosystem serves those from a shared CDN, so under INSPECT the list can carry every index
  # and still have no download path - that is the whole reason this line exists.
  #
  # IT DOES NOT ALLOW THE CDN, which is the reading to check before accepting it: the trust
  # is scoped to a SINGLE query transaction, so a redirection target asked for on its own is
  # an independent query, matches no entry and is blocked by the catch-all. What it costs is
  # narrower and real - the chain is trusted wherever the OWNER of a listed name points it.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # THE ALLOW-LIST ITSELF, AND THE LINE ABOVE IS THE RULE IT OBEYS - which is why this list
  # is shorter than it was. Under TRUST the firewall reads the name that was queried, so an
  # entry here is a name a tool asks for. A CNAME target is NOT an entry, and listing one is a
  # widening rather than a safety net - the trust holds inside a single query transaction,
  # so a redirection target stays unreachable on its own unless somebody puts it on this
  # list. Twelve entries - ten distinct names - were removed on 2026-08-23 for exactly that
  # reason: `dualstack.j2.shared.global.fastly.net`, `dualstack.k3...`, `dualstack.k.sni...`
  # (which appeared three times, once per Rust host), `dualstack.python.map.fastly.net`,
  # `fastly-index.crates.io`, `fastly-static.crates.io`, `fastly-static.rust-lang.org`, both
  # `*.cdn.cloudflare.net` spellings of the Ubuntu mirrors, and `us-west.pkg.julialang.net`.
  # A commented-out `"*"` went with them: an allow-everything entry one keystroke from being
  # live has no business sitting in a default-deny list.
  #
  # WHICH IS ALSO WHY THE OLD PARAGRAPH ABOUT CDNs IS GONE. Until v0.4.0 a name belonged here
  # only if its whole chain ended inside this list, so eight of nine external names worked by
  # a third party's DNS FLATTENING - a switch its owner could turn off unannounced, which is
  # `docs/AWS_STATE.md` EXC-05 and is now closed. Whether a CDN serves the bytes is no longer
  # this list's business; who OWNS the name still is, because the chain is trusted wherever
  # that owner points it.
  #
  # WHAT THIS LIST STILL DOES NOT DO. It is a control against ACCIDENT, not against intent,
  # and v0.4.0 changes nothing there: a process that already knows an ADDRESS asks no
  # resolver, and a process that asks `1.1.1.1:53` over the NAT or DoH on 443 is never seen
  # by this firewall at all - the VPC resolver only inspects what it is asked. The tier
  # security group permits all egress and the NACLs are at the default allow, so both paths
  # are open. Closing them is an SNI/Host control (Network Firewall, or a proxy), and neither
  # is built - D5 at step 6.1 is where that is argued.
  dns_firewall_allow_domains = [

    # allow all
    "*",

    # AWS itself, and a wildcard rather than names because the regional service endpoints
    # cannot be enumerated and are AWS's own namespace. Without it every SDK call over the
    # NAT fails to resolve: design A is "limited internet", not "no AWS".
    "amazonaws.com", "*.amazonaws.com",

    # SageMaker Unified Studio's own control plane, and it is NOT under amazonaws.com - it
    # sits on the `aws` TLD, which the wildcard above does not reach, and the `datazone`
    # interface endpoint does not cover it either (its private DNS is the amazonaws.com
    # spelling). Measured BLOCKED 52 times in one session before it was added: the estate's
    # own workbench refused by the estate's own firewall.
    "datazone.${var.region}.api.aws",

    "public.ecr.aws",

    # ubuntu package manager
    "archive.ubuntu.com",
    "security.ubuntu.com",

    # uv
    "astral.sh",
    "releases.astral.sh",

    # duckdb
    "blobs.duckdb.org",
    "extensions.duckdb.org",

    # python - index AND artifacts. files.pythonhosted.org is Fastly-fronted and had no path
    # before v0.4.0; it is one name now, like everything else here.
    "pypi.org",
    "files.pythonhosted.org",

    # conda
    #"conda.anaconda.org",
    #"repo.anaconda.com",

    # julia. us-west.pkg.julialang.ORG hops to the .NET spelling and the hop is no longer
    # listed - Pkg queries the .org name (JULIA_PKG_SERVER), which is the one that belongs
    # here. install.julialang.org is listable again under v0.4.0 if the manual-from-S3
    # install is ever not wanted; it stays out because nothing needs it today.
    "install.julialang.org",
    "julialang-s3.julialang.org",
    "pkg.julialang.org",
    "storage.julialang.net",
    "us-west.pkg.julialang.org",

    # rust. Same note as Julia: sh.rustup.rs is a single listable name now, kept out because
    # `sudo apt install rustup` is the path in use.
    "sh.rustup.rs",
    "index.crates.io",
    "static.crates.io",
    "static.rust-lang.org",

    # github
    "github.com",

    # The internal zones REACHABLE FROM THIS ACCOUNT, and the set differs per account, which
    # is half of why this list moved out of the module (v0.3.0). DNS Firewall is evaluated by
    # the VPC resolver, which is also what answers a private hosted zone - so an unlisted
    # internal name is blocked exactly like an internet one, and GitLab stops resolving at
    # Stage 7. sandbox.internal is this account's own; prod.internal and pages.internal are
    # Production's, reaching here through the cross-account associations of Stage 3 step 4.4.
    "sandbox.internal", "*.sandbox.internal",
    "prod.internal", "*.prod.internal",
    "pages.internal", "*.pages.internal",
  ]

  # ONE REACH THIS LIST HAS THAT ITS NAME DOES NOT SUGGEST: the rule group associates to the
  # VPC ID, not to a route table, so it also filters sandbox/buildbox/ in the isolated tier -
  # whose egress leaves through the WireGuard NAT instance and never touches this slice's
  # NAT. public.ecr.aws is one of the five things that host pulls, and under v0.4.0 the entry
  # above is finally enough to reach it: it is a CNAME into CloudFront, so before the trust
  # setting a build run while this slice was up failed on it even though it was listed.

  # DELIBERATELY ABSENT, and this is the record that makes it a control rather than an
  # oversight (Lesson 5; Stage 6 decision 3, 2026-08-19): Athena Spark's three session
  # endpoints - athena.sessions (Spark Connect), athena.dashboard (Live UI) and
  # athena.persistent-dashboard (History Server). Athena Spark runs its executors OUTSIDE
  # this VPC - there is no NetworkConfiguration in its API - so a notebook on it sits
  # outside these endpoints, the flow logs and every aws:SourceVpce condition. The
  # preventive half is the SCP deny on athena:StartSession/UpdateSession (Stage 6 step 1.6);
  # not creating these is the free network half, and it is a CHOICE since the 2026-04
  # PrivateLink release, not a property of the service.
  #
  # THE SQL PATH IS UNAFFECTED and must stay that way: Athena SQL rides the `athena` API
  # endpoint (the module's core list), which is what D13 depends on. Three names in the
  # same family, two different products.
  #
  # Revision trigger: Athena Spark gaining executors in OUR subnets under OUR security
  # group - never a headline saying it "supports VPC", which is about the control path.

}
