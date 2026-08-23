variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "vpc_id" {
  description = "The foundation/ VPC - read by the caller through terraform_remote_state, never pasted (Lesson 3)."
  type        = string
  nullable    = false
}

variable "egress_mode" {
  description = "Step 10's switch, PER ACCOUNT (10.3): 'A' builds the NAT and the private tier's default route; 'B' builds neither - no default route at all until Stages 6-7 build B's package path. Default A (Stage 3 decision 4); choosing A as the default is not choosing A as the outcome - D5's comparison happens at Stage 6."
  type        = string
  default     = "A"

  validation {
    condition     = contains(["A", "B"], var.egress_mode)
    error_message = "egress_mode is 'A' (NAT) or 'B' (no default route) - D5's two designs, nothing else."
  }
}

variable "nat_public_subnet_id" {
  description = "The ONE public subnet the NAT lands in (step 7.1) - the caller picks the first authored zone. The documented one-per-AZ switch: make this a map like private_route_table_ids and give aws_route.private_default a per-zone NAT - foundation's route tables are already per AZ so it is a route change, not a re-plumbing."
  type        = string
  nullable    = false
}

variable "private_route_table_ids" {
  description = "foundation/'s private route tables, BY ZONE ID - under design A every one of them gets the default route toward the one NAT (steps 2.2, 7, 10). Read through terraform_remote_state."
  type        = map(string)
  nullable    = false
}

variable "endpoint_subnet_id" {
  description = "The ONE subnet every interface endpoint lands in - single AZ (D9, step 8.5): two AZs doubles the largest hourly line item, and a resource in the other AZ still resolves and reaches it. The caller picks the private subnet of the first authored zone."
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
  description = "The per-account-role adds of step 8.3 - authored in each caller, because the list being DIFFERENT per role is the point: one list everywhere was wrong in both directions. Short service tokens ('sagemaker.api'); the region prefix is built here. Every entry is ~USD 0.010/h for the whole session."
  type        = list(string)
  default     = []
}

# ------------------------------------------------ design A's control (Stage 6 step 4.1)

variable "dns_firewall" {
  description = "Attach the Route 53 Resolver DNS Firewall to this VPC - design A's allow-list. false everywhere it does not apply: the deployment targets have no interactive user to constrain, and under egress_mode = B there is no default route for a name to be useful on (dns-firewall.tf enforces the second half itself, so a caller cannot half-enable it)."
  type        = bool
  default     = false
}

variable "dns_firewall_allow_domains" {
  description = "The allow-list, declared BY THE CALLER. Empty by default, and an empty list means the firewall creates no ALLOW rule at all - every lookup in the VPC returns NXDOMAIN. Read the note in dns-firewall.tf before adding a name: the whole resolution chain is evaluated, so a name is not allowed by being listed if its CNAME target is not."
  type        = list(string)

  # EMPTY BY DESIGN, AND THE DEFAULT IS THE POLICY (v0.3.0, 2026-08-23). Until v0.2.1 this
  # variable carried the estate's actual allow-list, on a "one copy so two callers cannot
  # drift" argument. That argument was worth less than it looked: the list is not a property
  # of the MECHANISM, it is a property of what a particular account is allowed to reach, and
  # keeping it here meant a module tag bump to change one account's reach and a silent
  # inheritance for any caller that never thought about it. The trade is deliberate and is
  # not free - two Interactive slices now each carry a list and CAN diverge, and nothing
  # mechanical compares them. That is the cost side, recorded so it is not discovered.
  #
  # WHAT A CALLER MUST SATISFY BEFORE ADDING A NAME - the reason this comment is here rather
  # than beside each list: dns-firewall.tf's header carries the mechanism (the whole
  # resolution chain is evaluated, so a CNAME to an unlisted target is blocked and the log
  # blames the original name). The operational form of it is one command per candidate,
  # BEFORE it goes on a list:
  #
  #     dig +noall +answer <name>     # +short hides the record TYPE, and the type is the answer
  #
  # READ THE CHAIN, NEVER THE PROVIDER. Three shapes, and only the third is unusable:
  #
  #   1. A records under the name that was asked for  -> listable; one name in the chain.
  #   2. CNAME staying inside the project's own namespace -> listable, but LIST EVERY HOP.
  #      us-west.pkg.julialang.ORG hops to us-west.pkg.julialang.NET, which is why both are
  #      on the Interactive lists - the second is load-bearing, not decoration.
  #   3. CNAME into a shared multi-tenant namespace (fastly.net, cloudfront.net,
  #      cdn.cloudflare.net, fastlydns.net, awsglobalaccelerator.com) -> NOT listable, and
  #      listing the tail is not the fix: those namespaces are self-service, so allowing one
  #      ends the control this firewall is. Widening the list is not the answer to shape 3;
  #      D5 is (step 6.1).
  #
  # "DOES IT GO THROUGH A CDN" IS THE WRONG QUESTION, and it is wrong in the direction that
  # flatters the list (measured 2026-08-23, `dig` + `whois` on the answer address + response
  # headers). Of the nine external names the two Interactive slices carry, EIGHT are
  # CDN-fronted: datazone.<region>.api.aws is CloudFront, pypi.org is Fastly, and
  # conda.anaconda.org, repo.anaconda.com, storage.julialang.net, releases.astral.sh,
  # extensions.duckdb.org and blobs.duckdb.org are Cloudflare. Exactly one -
  # us-west.pkg.julialang.net - is a host of its own. They work anyway because the
  # authoritative side FLATTENS the CDN behind an A record served under the queried name, so
  # the chain never leaves the list. What this firewall matches is the SHAPE OF THE DNS
  # ANSWER; whether a CDN serves the bytes afterwards is not its business.
  #
  # WHICH MAKES EVERY ONE OF THOSE EIGHT A DEPENDENCY ON A THIRD PARTY'S DNS CONFIGURATION.
  # Flattening is a switch its owner can turn off without announcing it; the day one does,
  # that name starts answering with a CNAME, the chain leaves the list, and the notebook
  # breaks in a way that looks like this estate's fault. It is a live failure mode, not a
  # hypothetical - docs/AWS_STATE.md EXC-05 carries the symptom and the triage, and the
  # diagnostic is the same dig, re-run.
  default = []
}
