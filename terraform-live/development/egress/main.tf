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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.3.0"

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
  # `datazone` JOINED THE LIST AT STAGE 6 STEP 4.2 (2026-08-21): the SMUS network-isolation
  # page marks it REQUIRED under VpcOnly, so an app cannot reach the domain without it. It is
  # the ONLY entry added from that page on faith. The rest of the required table
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

  # THE ALLOW-LIST ITSELF, and every name on it was MEASURED before it was written
  # (2026-08-23, step 4.3's session). The rule the module's dns-firewall.tf states and this
  # list obeys: DNS Firewall evaluates the WHOLE RESOLUTION CHAIN, so a name belongs here
  # only if its chain ends inside this list. `dig +short <name>` is the check - a line
  # ending in a dot is a hop to somewhere that also has to be listed.
  #
  # WHAT IS DELIBERATELY ABSENT IS THE LARGER HALF, and it is not an omission: the ARTIFACT
  # host of nearly every ecosystem. files.pythonhosted.org, index/static.crates.io,
  # static.rust-lang.org, sh.rustup.rs, pkg.julialang.org, cran/cloud.r-project.org,
  # deb.debian.org, archive/security.ubuntu.com and public.ecr.aws are each a CNAME into
  # Fastly, CloudFront, Cloudflare or Global Accelerator. Listing them changes nothing;
  # listing the CDN namespaces would work and would END this control, because those
  # namespaces are self-service - anyone can publish into them in minutes. So pip
  # downloads, cargo, rustup, CRAN, apt and ECR Public have NO path under design A. That is
  # the measured input D5 exists to receive (step 6.1), not a gap to close by widening this
  # list.
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

    # PyPI's INDEX, and only the index. Resolution and metadata work; the download does not,
    # because files.pythonhosted.org is Fastly. A half path, listed knowingly - `uv pip
    # install` finds a version and dies fetching the wheel, and this line is the reason.
    "pypi.org",

    # conda - a COMPLETE path. Both channel hosts answer with A records.
    "conda.anaconda.org",
    "repo.anaconda.com",

    # Julia - a COMPLETE path, and the one entry here that needs its second hop named:
    # us-west.pkg.julialang.ORG is a CNAME to us-west.pkg.julialang.NET, so both are listed
    # and the chain lands on a name this list carries. Pkg's DEFAULT server,
    # pkg.julialang.org, is Fastly and is deliberately not here - point Pkg at the regional
    # one (JULIA_PKG_SERVER) or it has no path at all.
    "us-west.pkg.julialang.org",
    "us-west.pkg.julialang.net",
    "storage.julialang.net",

    # uv and ruff - a COMPLETE path: the installer host answers with A records.
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
