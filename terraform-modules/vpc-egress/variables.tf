variable "env" {
  description = "The <env> name token (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "vpc_id" {
  description = "The foundation/ VPC - read by the caller through terraform_remote_state, never pasted (Lesson 3)."
  type        = string
  nullable    = false
}

# No `egress_mode`, `nat_public_subnet_id` or `private_route_table_ids`: D5's two designs and the
# NAT gateway that made design A a design are gone (6c step 5.1, 2026-09-06), and none of them is
# defaulted to "B". Under D38 the estate has one internet exit, an explicit proxy in the hub, and
# no VPC anywhere carries a default route, so a switch whose other position no longer exists would
# be dead code that reads like a choice. The route tables went with it: `aws_route.private_default`
# was their only consumer, and a module input nobody consumes is a claim about a capability that
# does not exist.
#
# The capability itself is not gone. Step 5.9 keeps a NAT gateway as a contingency - for a named
# service that needs the internet and cannot be told about a proxy, in that service's own VPC,
# with its own cost row and a removal trigger. Bringing it back means re-adding this file's
# resources for one caller, which is the friction the contingency wants.

variable "name_suffix" {
  description = "Distinguishes egress sets inside one account: names become awsds-<env>-<suffix>-*. Empty for a single-VPC account, which is every account but Production. Deferred here from 6c step 0.4a - the vpc module took the same input at v0.2.0, and this one waited so a single version could carry it beside the NAT removal rather than costing two bumps."
  type        = string
  default     = ""
  nullable    = false
}

variable "endpoint_subnet_id" {
  description = "The one subnet every interface endpoint lands in - single AZ (D9, step 8.5): two AZs doubles the largest hourly line item, and a resource in the other AZ still resolves and reaches it. The caller picks the private subnet of the first authored zone."
  type        = string
  nullable    = false
}

variable "endpoint_security_group_id" {
  description = "foundation/'s endpoint SG (step 2.4) - TCP/443 from the VPC CIDR, attached to every interface endpoint here."
  type        = string
  nullable    = false
}

variable "core_services" {
  description = "Step 8.2's common core, in every account: identity, logging, keys, images, and the data-plane three - under design B a missing athena/glue means no query executes at all (D13). lakeformation is the least certain entry and is included at a cent an hour rather than discovered at Stage 6; verification (ii) decides whether it stays. Overridden never - the per-role differences go in extra_services."
  type        = list(string)
  default     = ["sts", "logs", "kms", "ecr.api", "ecr.dkr", "athena", "glue", "lakeformation"]
}

variable "extra_services" {
  description = "The per-account-role adds of step 8.3 - authored in each caller, because the list being different per role is the point: one list everywhere was wrong in both directions. Short service tokens ('sagemaker.api'); the region prefix is built here. Every entry is ~USD 0.010/h for the whole session."
  type        = list(string)
  default     = []
}

# ------------------------------------------------- the optional groups (6c step 5.3, user decision)
#
# Under design A the NAT gateway covered every service silently, so an enabled blueprint always
# had a path. With no default route anywhere, a project that uses a blueprint whose endpoints are
# missing has no path at all - the feature exists in the portal and fails on first use. The estate
# keeps both optional blueprint families enabled (the user's decision, 2026-09-06) and controls
# their endpoints here instead.
#
# Empty is the default and it is the decision: `make up` with no groups creates no optional
# endpoint, so the cost of a family nobody is using that day is zero. `make up ENV=<x>
# GROUPS=bedrock` turns one on for that apply.
#
# It is per apply of one account's egress/ slice, not per project and not per person - while a
# group is on, it is on for everyone in that account. Nothing turns it off: the guard is that this
# slice is [E] and comes down with the session, not that anybody remembers.
#
# The map lives in the module and not in the three callers (Lesson 33): three hand-kept copies of
# "which endpoints does Bedrock need" would diverge on the first addition, and the failure mode is
# an account where a blueprint half-works.
variable "optional_service_groups" {
  description = "Which optional endpoint families to create, by group name. Empty by default - no optional endpoint exists unless a group is named. Threaded from `make up ENV=<x> GROUPS=a,b` through TF_VAR_optional_service_groups. Each group is ~USD 0.010/h per endpoint for the whole session (docs/PRICING.md 8)."
  type        = list(string)
  default     = []

  validation {
    # A closed list, because the failure of an unknown name is silent: a group nobody defined
    # contributes no endpoints, the apply succeeds, and the blueprint fails on first use exactly
    # as it would have with no flag at all. `make up GROUPS=bedrok` must be a plan error.
    condition     = alltrue([for g in var.optional_service_groups : contains(["bedrock", "bedrock-llm", "emr", "mwaa"], g)])
    error_message = "optional_service_groups admits only: bedrock, bedrock-llm, emr, mwaa. An unknown name would contribute nothing and fail silently at first use."
  }
}

# Narrow one endpoint's policy to a list of actions (Stage 6e step 4.4). Keyed by the SHORT service
# name - `bedrock-runtime`, not the full `com.amazonaws.<region>.bedrock-runtime` - which is the key
# every other map in this module uses.
#
# Default empty, and the default is the decision: an endpoint nobody names keeps `Action = "*"`
# under the organization condition, which is what every endpoint has carried since step 9. This
# variable adds a second axis to that document for the endpoints where a caller has an argument for
# one; it never widens, because the organization condition is untouched.
#
# It narrows the DOOR, not the caller. An action absent here cannot traverse this endpoint at all,
# whatever an identity policy allows - which is the property that makes it worth writing, and also
# the way to break a service by guessing: an SDK call nobody thought of gets no response and no
# denial that names this policy. Name only actions a consumer is known to make.
variable "endpoint_action_scopes" {
  description = "Per-endpoint action allow-list for the interface endpoint policy: short service name => list of actions. Endpoints not named here keep Action=* under the organization condition."
  type        = map(list(string))
  default     = {}

  validation {
    condition     = alltrue([for _k, v in var.endpoint_action_scopes : length(v) > 0])
    error_message = "an empty action list would emit `Action = []`, which denies everything through that endpoint while reading like a policy that was left blank. Omit the key instead."
  }
}

variable "dns_firewall" {
  description = "Attach the Route 53 Resolver DNS Firewall to this VPC. This sentence was rewritten at v0.6.0 and the old one is why: it said the firewall was design A's allow-list, that mode B made it pointless, and that `dns-firewall.tf` enforced that second half so a caller could not half-enable it. All three stopped being true when the NAT left - the module no longer reads egress_mode at all, so this flag is now the only gate and a caller gets exactly what it asks for. What the firewall is for also changed (6c step 5.7): not filtering the internet, which is the proxy's allow-list now, but closing the recursive resolver as an exfiltration channel - a job that exists with or without a default route. false where there is no interactive user to constrain, and false in the hub, which must resolve everything the proxy is asked to fetch."
  type        = bool
  default     = false
}

variable "firewall_domain_redirection_action" {
  description = "How the ALLOW rule treats a CNAME/DNAME chain. INSPECT_REDIRECTION_DOMAIN (the API default, and this module's) evaluates every domain in the chain, so a hop that is not listed blocks the lookup. TRUST_REDIRECTION_DOMAIN evaluates the queried name only and trusts the chain beneath it. Declared by the caller, like the list it governs."
  type        = string
  default     = "INSPECT_REDIRECTION_DOMAIN"

  # The default is the stricter reading, the same argument the empty allow-list above is built
  # on. A caller who never thought about this field gets the behaviour where nothing resolves
  # unless the whole chain was reasoned about; a caller who wants the chain trusted has to say
  # so, in its own slice, where the reach of that account is decided. It is not the setting this
  # estate's two Interactive slices use.
  #
  # It is a variable because the two values are not ranked: they answer different questions.
  # INSPECT asks "does every name this lookup touches belong to a set I enumerated" - the right
  # question for a slice reaching a small number of first-party hosts, and the only one that
  # survives a listed name whose owner is compromised. TRUST asks "did my tool ask for a name I
  # approve of", which is what an allow-list of hostnames means to the person writing it, and
  # the only workable question once artifact hosts are involved (see the list's comment). An
  # account answers the one that matches what it reaches.
  #
  # The field is per rule, not per rule group: dns-firewall.tf puts it on the ALLOW rule only.
  # The catch-all `*` matches at the first domain of every query and never has a chain left to
  # inspect, so there is nothing there for this to mean.
  validation {
    condition     = contains(["INSPECT_REDIRECTION_DOMAIN", "TRUST_REDIRECTION_DOMAIN"], var.firewall_domain_redirection_action)
    error_message = "firewall_domain_redirection_action is INSPECT_REDIRECTION_DOMAIN or TRUST_REDIRECTION_DOMAIN - the two values the Route 53 Resolver API defines, nothing else."
  }
}

variable "dns_firewall_allow_domains" {
  description = "The allow-list, declared by the caller. Empty by default, and an empty list means the firewall creates no ALLOW rule at all - every lookup in the VPC returns NXDOMAIN. Since v0.4.0 the ALLOW rule trusts the redirection chain, so an entry is the name a tool queries and never a CNAME target - listing a hop is a widening, not a safety net."
  type        = list(string)

  # Empty by design, and the default is the policy. The list is not a property of the mechanism,
  # it is a property of what a particular account is allowed to reach: holding it here would mean
  # a module tag bump to change one account's reach, and a silent inheritance for any caller that
  # never thought about it. The cost, recorded so it is not discovered: two Interactive slices
  # each carry a list and can diverge, and nothing mechanical compares them.
  #
  # What a caller must satisfy before adding a name - here rather than beside each list, because
  # dns-firewall.tf's header carries the mechanism. The ALLOW rule is set to
  # TRUST_REDIRECTION_DOMAIN, so the firewall inspects the name that was queried and trusts
  # whatever chain it resolves through. The rule that follows is one line:
  #
  #     List the name your tools ask for. Never list a redirection target.
  #
  # A hop on this list is not harmless redundancy. The trust is scoped to a single query
  # transaction, so a redirection target is unreachable on its own - unless somebody lists it,
  # which is what would make `dualstack.j2.shared.global.fastly.net` resolvable for anything
  # that cares to ask. Every hop removed from a list is a narrowing.
  #
  # What to check before adding a name: only that the name answers at all, and that you meant to
  # reach its owner.
  #
  #     dig +noall +answer <name>     # +short hides the record TYPE, and the type is the answer
  #
  # A CNAME row is not a disqualification - it is information about who you are trusting. Of the
  # three shapes a name can have (flat, same-namespace CNAME, CNAME into a shared CDN) only the
  # third is worth a second thought: `fastly.net`, `cloudfront.net`, `cdn.cloudflare.net`,
  # `fastlydns.net` and `awsglobalaccelerator.com` are multi-tenant, so the bytes come from a
  # host shared with everyone. That is an argument about who serves the artifact rather than
  # about whether the name can be listed, and it is D5's (step 6.1) rather than this variable's.
  #
  # What the list does not protect against: the control rests on the owner of each listed name
  # keeping its DNS honest. That was always true of an A record and is now true of the whole
  # chain. It never covered the two bypasses either - a raw address asks no resolver, and a query
  # sent to `1.1.1.1` or over DoH is not answered by the VPC resolver, so this firewall never
  # sees it. Closing those needs an SNI/Host control (Network Firewall, or a proxy); neither is
  # built.
  #
  # A reader meets this in the stage log and in EXC-05: under the API default,
  # INSPECT_REDIRECTION_DOMAIN, every hop had to be listed, and eight of the nine external names
  # the two Interactive slices carried resolved only because their authoritative side flattens
  # the CDN behind an A record served under the queried name (measured 2026-08-23: `dig`, `whois`
  # on the answer address, response headers) - a switch a third party could turn off without
  # announcing it. TRUST_REDIRECTION_DOMAIN removes that dependency. ./aws/dns-allowlist.py still
  # re-resolves both lists, and DN-2 asks the question this rule made important: is anything on a
  # list a hop.
  default = []
}
