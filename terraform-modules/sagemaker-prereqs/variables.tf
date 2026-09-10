# Inputs. Everything that differs between one member account and the next, and nothing else:
# the design lives here so that Sandbox and Development cannot drift (Lesson 14), and each
# caller says which account, never what.

variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - what every name below is built from. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false
}

variable "region" {
  description = "AWS region. No region literal ever appears in a .tf file (docs/plan/architecture.md 4.1)."
  type        = string
  nullable    = false
}

# ------------------------------------------------------------------- the network parameters
#
# What the blueprint configuration is pointed at (Stage 6 step 1.4). Read from this account's
# own foundation/ state by the caller, never pasted: an id in a .tf file is a copy of another
# slice's state that nothing keeps in step.

variable "vpc_id" {
  description = "The account's VPC - the aws:SourceVpc anchor every project app runs inside under VpcOnly."
  type        = string
  nullable    = false
}

variable "private_subnet_ids" {
  description = "The private subnets, keyed by AZ ZONE ID (never a name, never a list position - Stage 3 step 1.5). Project apps attach ENIs here; the map is flattened for the blueprint's Subnets parameter and its keys become the AZs parameter."
  type        = map(string)
  nullable    = false

  validation {
    condition     = length(var.private_subnet_ids) > 0
    error_message = "at least one private subnet is required - VpcOnly has nowhere to attach otherwise."
  }
}

# ----------------------------------------------------------------------- the lake's surface
#
# The D13 exclusion is built from these. They arrive from the lake account's state, through
# the caller's cross-account read, so a bucket renamed on the producer side is a plan diff
# here rather than a deny that quietly stops matching anything.

variable "lake_registered_bucket_arns" {
  description = "The bucket ARNs Lake Formation has REGISTERED (raw and curated today). The boundary denies s3:* on these and on everything under them - D13's whole content: a project role that could read the objects directly would make Lake Formation decorative."
  type        = list(string)
  nullable    = false
}

variable "lake_dropbox_write_arn" {
  description = "The one sanctioned direct write into the lake (D18, docs/GOVERNANCE.md §Drop-box): the dated-prefix object ARN pattern the drop-box bucket policy admits. Mirrors the persona's WriteIngestionDropBox statement - the identity half of a two-sided rule (INT-10)."
  type        = string
  nullable    = false
}

variable "lake_data_key_arn" {
  description = "The lake account's data CMK. The boundary lets a project role use it ONLY through S3 (kms:ViaService), mirroring UseLakeDataKeyViaS3 and the key policy's own condition - each side scoping the other."
  type        = string
  nullable    = false
}

# ------------------------------------------------------------------------ the cost ceiling
variable "allowed_instance_types" {
  description = "Pass-through to terraform-modules/sagemaker-denies, which OWNS the list (Lesson 33 - structure and values are both one copy). null, the default, means \"whatever the shared module says\" - which is what every caller should want: identity/sso/ composes the same fragment for the six persona sets, and a second list here is the divergence the shared module exists to prevent."
  type        = list(string)
  default     = null
}

variable "log_retention_days" {
  description = "Retention on /awsds/<env>/studio (Stage 6 step 9.1). 30 matches Stage 3's flow-log decision - the value is not the interesting part, agreeing with the other subsystem is."
  type        = number
  default     = 30
}

# ------------------------------------------------------------- the second apply (pass 2b)
#
# The account association has no public API (Stage 6 step 1.3), so the blueprint configuration
# cannot be created in the same apply as the roles it names: a domain has to exist and this
# account has to have accepted an invitation to it. Both halves ride on one flag, emitted from
# backend.SMUS_ASSOCIATED - a table whose rows are measurements, not intentions.

variable "blueprints_enabled" {
  description = "false until this account's SMUS association exists (it auto-accepts - no invitation; backend.SMUS_ASSOCIATED). true creates the blueprint configurations and their grants - the pass 2b apply."
  type        = bool
  default     = false
}

variable "domain_id" {
  description = "The DataZone V2 domain id, read from data-governance/governance/'s state. null while blueprints_enabled is false."
  type        = string
  default     = null
}

variable "domain_account_id" {
  description = "The DOMAIN account id - the value aws:SourceAccount must carry on both service-role trusts (roles.tf, v0.3.3): the service assumes them on behalf of the domain, so the guard names the domain's account, never this one. Known before the domain exists (it is the Data Governance account), so not gated."
  type        = string
  nullable    = false
}

variable "domain_execution_role_arn" {
  description = "The domain execution role (data-governance/governance/'s output) - a principal in the project CMK's key policy (kms.tf, the SMUS statements). null while blueprints_enabled is false drops it from the policy; the datazone service principal stays either way."
  type        = string
  default     = null
}

variable "root_domain_unit_id" {
  description = "The domain's root domain unit - the scope of grants.tf's project principal. Read from data-governance/governance/'s state; null while blueprints_enabled is false."
  type        = string
  default     = null
}

# Decision 5's category 1, by API name. Three names that do not exist in the API -
# `EMRServerless`, `EMRonEC2`, and `AmazonBedrockGenerativeAI`, a console grouping the API
# expands into seven - were measured against the live domain 2026-08-21 after step 1.4's plan
# failed on them (Lesson 38).
#
# The same list lives in three places (Lesson 14, and locals.tf says so too): here, in
# data-governance/governance/locals.tf, and in ./aws/studio.py's US-3 constant. A category change
# moves all three in one commit.
variable "blueprint_names" {
  description = "Decision 5's category 1, by API name (docs/SMUS.md is the reference table; ./aws/studio.py US-3 holds the same list). A category-2 blueprint joins BOTH in the same commit that enables it (Lesson 14)."
  type        = list(string)
  default = [
    # The base environment, first: it provisions the project's SageMaker AI domain, roles and
    # security groups, and nothing else works without it. `deployment_order` below is `index()`
    # into this list.
    "Tooling",
    # ToolingLite is absent - category 3 since 2026-08-21 (the user's decision). Step 1.5's apply
    # measured what no page documents: it is a base variant, not a capability - the service
    # refuses it ON_DEMAND in a project profile ("ToolingLite environment blueprint configuration
    # must have deployment mode ON_CREATE") - and a second base beside Tooling would
    # double-provision every new project with a shape nobody measured. Category 3 means disabled:
    # re-enabling starts by amending the decision.
    # Storage and catalog.
    "DataLake",
    "S3Bucket",
    "S3TableCatalog",
    # LakehouseAdmin is absent - category 2 since 2026-08-21. It is a provisioning template whose
    # own description is an account-wide automatic ingest-and-catalog, and not Lake Formation's
    # data lake administrator (different objects, similar names). A comment saying "measure it at
    # 2.4 first" is an intention, not a control (Lesson 5), so the measurement is the enabling
    # trigger instead. It joins this list when step 2.4 has read what the environment provisions
    # and what the D13 boundary actually stops - or when a blueprint here proves to depend on it.
    # Compute.
    "EmrServerless",
    # The generative-AI surface, six entries: `AmazonBedrockGenerativeAI` is a console grouping
    # with no API identifier (measured 2026-08-21 - `list-environment-blueprints` returns seven
    # `AmazonBedrock*` blueprints and no aggregate), and six of the seven are category 1.
    # AmazonBedrockKnowledgeBase is absent - category 2, its vector store billing while it
    # exists; it joins in the commit that enables it (Lesson 14).
    "AmazonBedrockChatAgent",
    "AmazonBedrockEvaluation",
    "AmazonBedrockFlow",
    "AmazonBedrockFunction",
    "AmazonBedrockGuardrail",
    "AmazonBedrockPrompt",
  ]
}
