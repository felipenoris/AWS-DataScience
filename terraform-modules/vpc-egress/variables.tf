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
  description = "The allow-list, and THE ONE COPY OF IT (Lesson 33): both Interactive slices enable the firewall and neither carries a list, so the two cannot drift. Read the note in dns-firewall.tf before editing."
  type        = list(string)

  # WHAT IS ON THE LIST, BY REASON RATHER THAN BY NAME - the names go stale, the reasons do
  # not, and Stage 6 step 4.1 says in as many words to read the ACTUAL names at the time.
  #
  #   AWS itself      without it every SDK call over the NAT fails to resolve, including the
  #                   ones this design WANTS to leave the VPC. Design A is "limited
  #                   internet", not "no AWS".
  #   ECR Public      public.ecr.aws is NOT under amazonaws.com - a different registrable
  #                   domain on the `aws` TLD, and the one entry every reading of
  #                   "*.amazonaws.com covers AWS" silently misses. It is the ancestor of the
  #                   BYOI image (docs/SMUS.md, Custom images), so anything rebasing on
  #                   sagemaker-distribution resolves this name or does nothing.
  #   the package     PyPI, conda, CRAN, the Julia package server, crates.io - the ecosystems
  #   indexes         docs/plan/architecture.md 4.3 names. Under design B these are replaced
  #                   by CodeArtifact and this list is not consulted at all.
  #   the toolchain   rustup.rs, rust-lang.org, astral.sh. Rust and uv BOOTSTRAP from an
  #   installers      installer host, not from an index, so allow-listing the index alone
  #                   leaves the install itself failing on a name nobody listed.
  #   runtime         duckdb.org. DuckDB fetches an extension the FIRST TIME A QUERY NEEDS IT,
  #   extension       from inside the notebook process and long after any install step - so
  #   fetches         the failure surfaces as a broken query rather than a broken install.
  #   distro mirrors  the SageMaker Distribution image is Debian-based; an apt-get in a
  #                   notebook is a normal thing to do and a silent NXDOMAIN on it is an
  #                   afternoon.
  #   the internal    prod.internal / pages.internal / sandbox.internal. DNS Firewall is
  #   zones           evaluated by the VPC resolver, which is also what answers a private
  #                   hosted zone - so an unlisted internal name is blocked exactly like an
  #                   internet one, and GitLab stops resolving at Stage 7.
  #
  # TWO REGISTRABLE DOMAINS FOR ONE ECOSYSTEM IS THE TRAP THIS LIST WALKS INTO (2026-08-22):
  # Julia's package server is *.julialang.ORG and its storage server is storage.julialang.NET.
  # A wildcard covers DEPTH, never a sibling TLD - `*.julialang.org` matches
  # us-west.pkg.julialang.org at any nesting and matches julialang.net at none. So an ecosystem
  # is not "on the list" because one of its names is: read the hostnames a client actually
  # resolves (step 4.3's query log), never the project's home page.
  #
  # THIS LIST BINDS THE WHOLE VPC, buildbox included. The rule group associates to the VPC id
  # (dns-firewall.tf), not to a route table, so the isolated tier's build host is filtered by
  # it too - even though its egress leaves through the WireGuard NAT instance rather than
  # through this slice's NAT. The buildbox pulls public.ecr.aws, PyPI, conda-forge, julialang
  # and static.rust-lang.org (its security-group comment says so and defers the naming to
  # here); every one of those is on the list above. That coupling has never been exercised,
  # because no build has yet run while `egress/` was up.
  #
  # ONE FAMILY IS KEPT OFF THIS LIST ON PURPOSE, and the instruction is the point rather than
  # the omission (Stage 6 decision 3, 2026-08-19): Athena Spark's session hosting domains.
  # Default-deny already excludes them, so nothing is being ADDED here - what is being added
  # is the instruction NOT to add them when somebody debugging a blocked lookup works down
  # this list. The reasoning is in Stage 6 step 1.6 and in the `extra_services` comment of
  # both Interactive egress slices: Spark's executors run outside this VPC, so a notebook on
  # them sits outside every control the perimeter is made of. The SQL path does not touch
  # these names.
  default = [
    "amazonaws.com", "*.amazonaws.com",
    "public.ecr.aws", "*.public.ecr.aws",
    "pypi.org", "*.pypi.org",
    "pythonhosted.org", "*.pythonhosted.org",
    "astral.sh", "*.astral.sh",
    "anaconda.com", "*.anaconda.com",
    "anaconda.org", "*.anaconda.org",
    "r-project.org", "*.r-project.org",
    "julialang.org", "*.julialang.org",
    "julialang.net", "*.julialang.net",
    "crates.io", "*.crates.io",
    "rustup.rs", "*.rustup.rs",
    "rust-lang.org", "*.rust-lang.org",
    "duckdb.org", "*.duckdb.org",
    "debian.org", "*.debian.org",
    "ubuntu.com", "*.ubuntu.com",
    "prod.internal", "*.prod.internal",
    "pages.internal", "*.pages.internal",
    "sandbox.internal", "*.sandbox.internal",
  ]
}
