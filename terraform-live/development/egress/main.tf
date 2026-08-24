# development/egress/ - the [E] metered network of Development (Stage 3 pass 3): the NAT
# under design A, step 8's Development endpoint list, step 9's org policy on every entry.
# Lifecycle belongs to `make up ENV=development` / `make down ENV=development` (D11), never
# to a by-hand apply (runbook, "What you never do"); `./aws/egress.py` 6 is the burn meter.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).

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

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3) - D5's comparison is Stage 6's.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9) - a selection, not an anchor.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Development row: the three SageMaker endpoints - the same list as Sandbox
  # since 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  # `datazone` JOINED THE LIST AT STAGE 6 STEP 4.2 (2026-08-21) ON A MISREAD, measured
  # 2026-08-24. The sentence here used to claim the network-isolation page marks it "REQUIRED
  # under VpcOnly, so an app cannot reach the domain without it" - three errors in one clause:
  # the page's required table is scoped by its OWN premise ("access to the public internet is
  # denied from the VPC" - design B, never VpcOnly); under design A the app reaches DataZone
  # through the NAT (datazone.<region>.api.aws is on the list below); and the entry is not
  # free - its private DNS zone is AUTHORITATIVE FOR THE WHOLE SUBTREE, so
  # agent.datazone.<region>.api.aws, which the SAME page's public-internet table says the
  # portal front-end needs, is NXDOMAIN for every client of the VPC resolver, the full-tunnel
  # laptop included: the portal broke ON the VPN while Sandbox's twin of this slice was up
  # (Lessons 40-42; this account's zone does the same the day this slice is up). REMOVAL IS
  # RECOMMENDED AND PENDING the user's authorization - the removal's prediction, that the
  # app's calls move to the NAT, is measured at the apply rather than assumed.
  # The rest of the required table
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

  # THE ALLOW-LIST ITSELF, AND THE LINE ABOVE IS THE RULE IT OBEYS. Under TRUST the firewall
  # reads the name that was queried, so an entry here is a name a tool asks for; a CNAME
  # target is not an entry. Listing a hop is
  # a widening rather than a safety net - the trust holds inside one query transaction, so a
  # redirection target stays unreachable on its own unless somebody lists it. This list
  # carried exactly one hop, `us-west.pkg.julialang.net`, removed on 2026-08-23.
  #
  # WHAT THE PARAGRAPH HERE USED TO SAY, and why it is gone: until v0.4.0 a name belonged
  # here only if its whole chain ended inside this list, so eight of nine external names
  # worked only because their authoritative side FLATTENS the CDN behind an A record served
  # under the queried name - a switch a third party could turn off unannounced
  # (docs/AWS_STATE.md EXC-05, now closed). Whether a CDN serves the bytes is no longer this
  # list's business. Who OWNS a listed name still is: the chain is trusted wherever that
  # owner points it.
  #
  # WHAT IS STILL ABSENT IS THE ARTIFACT HALF, and it is now a CHOICE rather than a ceiling.
  # files.pythonhosted.org, index/static.crates.io, static.rust-lang.org, sh.rustup.rs,
  # pkg.julialang.org, cloud.r-project.org, deb.debian.org, archive/security.ubuntu.com and
  # public.ecr.aws are each a CNAME into Fastly, CloudFront, Cloudflare or Global
  # Accelerator, and every one of them is a single listable name under v0.4.0. They are not
  # here because THIS account has not needed them - `development/` is the pipeline-engineering
  # account, and D5's comparison at step 6.1 is about where packages should come from, which
  # is a different question from whether the firewall can express it. The sandbox list is
  # where the ad-hoc set lives; the two lists diverging is expected and DN-3 reports it.
  #
  # WHAT THIS LIST DOES NOT DO, unchanged by v0.4.0: it is a control against ACCIDENT. A
  # process that already knows an ADDRESS asks no resolver, and a query sent to `1.1.1.1:53`
  # over the NAT or over DoH on 443 is never seen by this firewall - the VPC resolver only
  # inspects what it is asked, the tier security group permits all egress and the NACLs sit
  # at the default allow. Closing either needs an SNI/Host control (Network Firewall, or a
  # proxy), and neither is built.
  dns_firewall_allow_domains = [
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

    # PyPI's INDEX, and only the index - still a half path, but for a different reason since
    # vpc-egress-v0.4.0. files.pythonhosted.org is Fastly-fronted and used to be UNLISTABLE;
    # under TRUST_REDIRECTION_DOMAIN it is one ordinary name and adding it would work. It is
    # absent because nothing in this account has asked for it yet, not because it cannot be
    # reached: `uv pip install` finds a version and dies fetching the wheel, and this line is
    # the reason. Adding it is a one-line decision now, not a design question.
    "pypi.org",

    # conda - a COMPLETE path. Both channel hosts, and no hop of theirs, is the whole rule.
    "conda.anaconda.org",
    "repo.anaconda.com",

    # Julia - a COMPLETE path. Pkg queries us-west.pkg.julialang.ORG (JULIA_PKG_SERVER), and
    # that is the whole entry: the .NET spelling it hops to was listed until v0.4.0 and was
    # removed with every other hop, because the ALLOW rule trusts the chain and a listed hop
    # is what makes the hop resolvable on its own. Pkg's DEFAULT server, pkg.julialang.org,
    # is listable now too and is still not here - the regional one is the deliberate choice,
    # not a workaround for the firewall.
    "us-west.pkg.julialang.org",
    "storage.julialang.net",

    # uv and ruff - a COMPLETE path. "Answers flat" stopped being the criterion at v0.4.0;
    # this is simply the name the installer asks for.
    "releases.astral.sh",

    # DuckDB - a COMPLETE path. Extensions are fetched at FIRST QUERY, from inside the
    # notebook process and long after any install step, so a miss here surfaces as a broken
    # query rather than a broken install.
    "extensions.duckdb.org",
    "blobs.duckdb.org",

    # The internal zones REACHABLE FROM THIS ACCOUNT, and the set differs per account, which
    # is half of why this list moved out of the module (v0.3.0). DNS Firewall is evaluated by
    # the VPC resolver, which is also what answers a private hosted zone - so an unlisted
    # internal name is blocked exactly like an internet one, and GitLab stops resolving at
    # Stage 7. This account authors NO zone of its own: prod.internal and pages.internal are
    # Production's, reaching here through the cross-account associations of Stage 3 step 4.4,
    # and sandbox.internal is deliberately not here because it is not associated with this
    # VPC - listing it would be a name that can never answer.
    "prod.internal", "*.prod.internal",
    "pages.internal", "*.pages.internal",
  ]

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
