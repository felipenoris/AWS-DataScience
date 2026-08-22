locals {
  # DECISION 5's CATEGORY 1, by API name - the blueprints a project profile may bundle. The
  # SAME list terraform-modules/sagemaker-prereqs/ enables per member account and the same one
  # ./aws/studio.py US-3 holds; docs/SMUS.md is the reference table with the three categories
  # and the billing shapes. A category-2 blueprint (Workflows OnDemand, MLExperiments) joins
  # all three in ONE commit, which is Lesson 14's rule applied to a list that lives in a
  # module, a slice and a check.
  #
  # EmrServerless FOLLOWS DECISION 1, taken 2026-08-21 as KEEP-or-REMOVE: it is enabled here and
  # removed if either in-stage reading comes out against it (4.2's flow logs; whether a
  # `fineGrained` EMR-S connection is usable from an IdC-domain notebook). Landing on Glue
  # interactive sessions removes this one entry - Glue needs no blueprint at all.
  #
  # EVERY NAME HERE WAS RE-READ FROM THE LIVE DOMAIN ON 2026-08-21, and three of the four this
  # list used to carry did not resolve: `EMRServerless` (the API says `EmrServerless`),
  # `EMRonEC2` (`EmrOnEc2`) and `AmazonBedrockGenerativeAI` (a console grouping with no API
  # identifier at all). They were proper nouns taken from documentation prose - Lesson 38 - and
  # the plan of step 1.4 failed on them before anything was applied.
  #
  # THE ORDER IS A CONTRACT, AND ONLY ITS FIRST ELEMENT IS MEASURED: profiles.tf reads
  # `index(local.category_one_blueprints, bp)` as each environment's `deployment_order`, so
  # Tooling must come first - nothing else provisions a working project. The grouping after it
  # is deliberate but NOT a dependency graph anybody has read; if a project's environments turn
  # out to need a stricter order, that is a measurement at step 2.4, not a preference.
  category_one_blueprints = [
    # The base environment, FIRST and deliberately so - it provisions the project's SageMaker AI
    # domain, roles and security groups, and nothing else works without it. `deployment_order`
    # below is `index()` into this list.
    "Tooling",
    # ToolingLite IS DELIBERATELY ABSENT - category 3 since 2026-08-21 (user decision, after
    # step 1.5's apply measured what no page documents: it is a BASE variant, not a capability.
    # The service refuses it ON_DEMAND in a project profile - "ToolingLite environment blueprint
    # configuration must have deployment mode ON_CREATE" - and a second base beside Tooling
    # would double-provision every new project). Category 3 means disabled: re-enabling starts
    # by amending the decision.
    # Storage and catalog.
    "DataLake",
    "S3Bucket",
    "S3TableCatalog",
    # LakehouseAdmin IS DELIBERATELY ABSENT - category 2 since 2026-08-21, not an omission. It is a
    # PROVISIONING TEMPLATE whose own description is an account-wide automatic ingest-and-catalog,
    # and NOT Lake Formation's data lake administrator (different objects, similar names). It was
    # briefly category 1 with a comment saying "measure it at 2.4 first"; a comment is an intention,
    # not a control (Lesson 5), so the measurement became the enabling trigger instead. It joins
    # this list when step 2.4 has read what the environment provisions and what the D13 boundary
    # actually stops - or when a blueprint here proves to depend on it.
    # Compute.
    "EmrServerless",
    # The generative-AI surface. SEVEN ENTRIES, NOT ONE: `AmazonBedrockGenerativeAI` is a CONSOLE
    # GROUPING with no API identifier (measured 2026-08-21 - `list-environment-blueprints` returns
    # these seven and no aggregate), so decision 5's category 1 is delivered by naming them.
    "AmazonBedrockChatAgent",
    "AmazonBedrockEvaluation",
    "AmazonBedrockFlow",
    "AmazonBedrockFunction",
    "AmazonBedrockGuardrail",
    "AmazonBedrockPrompt",
  ]

  member_account_ids = {
    sandbox     = data.aws_caller_identity.sandbox.account_id
    development = data.aws_caller_identity.development.account_id
  }

  # THE TWO PROFILES, WHERE EACH PROVISIONS, AND WHO MAY CREATE FROM IT (D21/D26). The names
  # are a contract with ./aws/studio.py (US-4) and the account pinning is what turns D21's
  # boundary from "which URL did the person open" into a property of the project.
  #
  # THE `group` COLUMN ARRIVED 2026-08-22, AND IT CLOSES A GAP THE STAGE HAD NOT NOTICED. A
  # profile is a template; being able to CREATE from it is a separate authorization, granted
  # per domain unit, and nothing granted it - measured in the portal (step 1.7's sitting) as
  # `User is not permitted to perform operation: CreateProject`, identical on and off the VPN,
  # with `list-policy-grants` returning an empty list for both CREATE_PROJECT and
  # CREATE_PROJECT_FROM_PROJECT_PROFILE. Until then the ONLY principal that could create a
  # project was the role that created the domain, which is the one nobody works as.
  #
  # WHY THE COLUMN LIVES HERE rather than in grants.tf: the account and the group are the same
  # kind of fact about the same object, and splitting them is how a profile ends up pinned to
  # one account while its grant names another (Lesson 33 - share the values, do not duplicate
  # the structure). grants.tf iterates THIS map.
  #
  # WHY THESE TWO GROUPS (user decision, 2026-08-22). `experimentation` is Sandbox and D21 is
  # already decided there, so the data scientists' grant is a standing right. `engineering` is
  # DEVELOPMENT, and whether a person needs an interactive surface next to Development's data
  # at all is the OPEN half of D21 - so it goes to the persona that owns the promotion chain
  # the account exists to start, and the grant is the instrument of that open question rather
  # than a settled entitlement. If D21 closes against the interactive surface, this row is
  # removed and that removal is the expected outcome, not a regression.
  project_profiles = {
    experimentation = {
      account     = "sandbox"
      group       = "sso-group-data-scientists"
      description = "Experimentation (D21): the unit of work is a notebook. Provisions into a business unit's Sandbox."
    }
    engineering = {
      account     = "development"
      group       = "sso-group-deployment-managers"
      description = "Engineering (D21): the unit of work is a pipeline. Provisions into Development, where the promotion chain starts."
    }
  }

  # THE TOOLING PARAMETERS STAGE 6 STEP 1.5 LOCKS. Every one is marked NON-EDITABLE, and that
  # flag is the whole difference between a default and a control (Lesson 5): the parameter
  # exists so nobody can flip a project to PublicInternetOnly, raise its idle ceiling, or give
  # itself a 16 TiB volume.
  #
  # sagemakerDomainNetworkType = VpcOnly IS ALREADY THE BLUEPRINT DEFAULT (read 2026-08-16).
  # It is written here anyway, for the reason above - a default that nobody may change is a
  # different object from a default.
  tooling_parameters = [
    { name = "sagemakerDomainNetworkType", value = "VpcOnly", is_editable = false },
    # "ENABLED", NOT "true" (corrected 2026-08-22): the template's AllowedValues are
    # ENABLED/DISABLED - an enum, not the boolean the plan's prose implied (Lesson 38; the TIP
    # parameter below IS "true"/"false", so both spellings coexist in one template). The wrong
    # value survived 1.5's apply because CreateProjectProfile validates no parameter against
    # the template; the FIRST deploy to reach CloudFormation refused it ("Parameter
    # 'lifecycleManagement' must be one of AllowedValues", 400) - itself proof the whole
    # pre-CFN pipeline had just started working. AllowedValues were read from the downloaded
    # template itself, and every other locked value was checked against it in the same
    # sitting: the five below are valid.
    { name = "lifecycleManagement", value = "ENABLED", is_editable = false },
    { name = "idleTimeoutInMinutes", value = tostring(var.idle_timeout_minutes), is_editable = true },
    { name = "maxIdleTimeoutInMinutes", value = tostring(var.max_idle_timeout_minutes), is_editable = false },
    { name = "maxEbsVolumeSize", value = tostring(var.max_ebs_volume_size_gb), is_editable = false },
    {
      name        = "enableTrustedIdentityPropagationPermissions"
      value       = tostring(var.enable_trusted_identity_propagation)
      is_editable = false
    },
  ]

  # PARAMETER OVERRIDES PER BLUEPRINT - the map profiles.tf consumes. Tooling's rows above are
  # CONTROLS (locked, is_editable=false); the two rows below are the OPPOSITE and exist for a
  # different reason, measured 2026-08-22: UpdateProjectProfile validates that every REQUIRED
  # blueprint parameter without a default is declared ("Missing required Blueprint
  # parameter(s): bucketName") - a validation CreateProjectProfile never ran, which is how the
  # profiles were created without them. S3Bucket's bucketName and S3TableCatalog's catalogName
  # are PER-PROJECT names: both templates consume them by literal Ref (no per-project suffix is
  # added), so a locked value would collide between projects - S3's namespace is global. The
  # placeholder is what the portal PRE-FILLS when a member enables the capability
  # (deployment_mode ON_DEMAND), and is_editable = true is the point: the member REPLACES it.
  # A project deployed with the placeholder unchanged fails or collides visibly - preferable
  # to a silently shared name.
  blueprint_parameters = {
    Tooling = local.tooling_parameters
    S3Bucket = [
      { name = "bucketName", value = "changeme-project-bucket", is_editable = true },
    ]
    S3TableCatalog = [
      { name = "catalogName", value = "changemecatalog", is_editable = true },
    ]
  }
}
