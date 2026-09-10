locals {
  # Decision 5's category 1, by API name - the blueprints a project profile may bundle. The same
  # list terraform-modules/sagemaker-prereqs/ enables per member account and ./aws/studio.py US-3
  # holds; docs/SMUS.md is the reference table with the three categories and the billing shapes.
  # A category-2 blueprint (Workflows OnDemand, MLExperiments) joins all three in one commit
  # (Lesson 14).
  #
  # EmrServerless follows decision 1, taken 2026-08-21 as keep-or-remove: it is enabled here and
  # removed if either in-stage reading comes out against it (4.2's flow logs; whether a
  # `fineGrained` EMR-S connection is usable from an IdC-domain notebook). Landing on Glue
  # interactive sessions removes this one entry - Glue needs no blueprint at all.
  #
  # Every name here was re-read from the live domain on 2026-08-21, and three did not resolve:
  # `EMRServerless` (the API says `EmrServerless`), `EMRonEC2` (`EmrOnEc2`) and
  # `AmazonBedrockGenerativeAI` (a console grouping with no API identifier at all). They were
  # proper nouns taken from documentation prose (Lesson 38), and the plan of step 1.4 failed on
  # them before anything was applied.
  #
  # The order is a contract, and only its first element is measured: profiles.tf reads
  # `index(local.category_one_blueprints, bp)` as each environment's `deployment_order`, so
  # Tooling must come first - nothing else provisions a working project. The grouping after it is
  # not a dependency graph anybody has read; a stricter order is a measurement at step 2.4.
  category_one_blueprints = [
    # The base environment, first: it provisions the project's SageMaker AI domain, roles and
    # security groups, and nothing else works without it. `deployment_order` below is `index()`
    # into this list.
    "Tooling",
    # ToolingLite is absent - category 3 since 2026-08-21 (user decision, after step 1.5's apply
    # measured what no page documents: it is a base variant, not a capability. The service
    # refuses it ON_DEMAND in a project profile - "ToolingLite environment blueprint
    # configuration must have deployment mode ON_CREATE" - and a second base beside Tooling would
    # double-provision every new project). Category 3 means disabled: re-enabling starts by
    # amending the decision.
    # Storage and catalog.
    "DataLake",
    "S3Bucket",
    "S3TableCatalog",
    # LakehouseAdmin is absent - category 2 since 2026-08-21. It is a provisioning template whose
    # own description is an account-wide automatic ingest-and-catalog, and not Lake Formation's
    # data lake administrator (different objects, similar names). A comment saying "measure it at
    # 2.4 first" is an intention, not a control (Lesson 5), so the measurement is the enabling
    # trigger: it joins this list when step 2.4 has read what the environment provisions and what
    # the D13 boundary stops, or when a blueprint here proves to depend on it.
    # Compute.
    "EmrServerless",
    # The generative-AI surface, six entries. `AmazonBedrockGenerativeAI` is a console grouping
    # with no API identifier (measured 2026-08-21 - `list-environment-blueprints` returns seven
    # `AmazonBedrock*` blueprints and no aggregate), and six of the seven are category 1.
    # AmazonBedrockKnowledgeBase is absent - category 2, its vector store bills while it exists;
    # it joins in the commit that enables it (Lesson 14). Decision 5's category 1 is delivered by
    # naming them.
    "AmazonBedrockChatAgent",
    "AmazonBedrockEvaluation",
    "AmazonBedrockFlow",
    "AmazonBedrockFunction",
    "AmazonBedrockGuardrail",
    "AmazonBedrockPrompt",
  ]

  member_account_ids = {
    sandbox = data.aws_caller_identity.sandbox.account_id
  }

  # The profiles, where each provisions, and who may create from it (D21/D26). The names are a
  # contract with ./aws/studio.py (US-4), and the account pinning turns D21's boundary from
  # "which URL did the person open" into a property of the project.
  #
  # The `group` column is a separate authorization from the profile itself: a profile is a
  # template, and creating from it is granted per domain unit. Nothing granted it until
  # 2026-08-22 - measured in the portal (step 1.7's sitting) as `User is not permitted to perform
  # operation: CreateProject`, identical on and off the VPN, with `list-policy-grants` returning
  # an empty list for both CREATE_PROJECT and CREATE_PROJECT_FROM_PROJECT_PROFILE. Until then the
  # only principal that could create a project was the role that created the domain.
  #
  # The column lives here rather than in grants.tf because the account and the group are the same
  # kind of fact about the same object, and splitting them is how a profile ends up pinned to one
  # account while its grant names another (Lesson 33). grants.tf iterates this map.
  #
  # One group, because `experimentation` is Sandbox and D21 is decided there: the data
  # scientists' grant is a standing right. The `engineering` profile went with the account that
  # became headless `Staging` when D21's open half closed against an interactive surface next to
  # that account's data.
  project_profiles = {
    experimentation = {
      account     = "sandbox"
      group       = "sso-group-data-scientists"
      description = "Experimentation (D21): the unit of work is a notebook. Provisions into a business unit's Sandbox."
    }
  }

  # The Tooling parameters Stage 6 step 1.5 locks. The non-editable flag is the difference
  # between a default and a control (Lesson 5): the parameters exist so nobody can flip a project
  # to PublicInternetOnly, raise its idle ceiling, or give itself a 16 TiB volume.
  #
  # sagemakerDomainNetworkType = VpcOnly is already the blueprint default (read 2026-08-16), and
  # is written here anyway: a default nobody may change is a different object from a default.
  tooling_parameters = [
    { name = "sagemakerDomainNetworkType", value = "VpcOnly", is_editable = false },
    # "ENABLED", not "true": the template's AllowedValues are ENABLED/DISABLED, an enum rather
    # than the boolean the plan's prose implied (Lesson 38; the TIP parameter below is
    # "true"/"false", so both spellings coexist in one template). The wrong value survived 1.5's
    # apply because CreateProjectProfile validates no parameter against the template; the first
    # deploy to reach CloudFormation refused it ("Parameter 'lifecycleManagement' must be one of
    # AllowedValues", 400). AllowedValues were read from the downloaded template on 2026-08-22
    # and every other locked value was checked against it in the same sitting: the five below
    # are valid.
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

  # Parameter overrides per blueprint - the map profiles.tf consumes. Tooling's rows above are
  # controls (locked, is_editable=false); the two rows below exist for the opposite reason,
  # measured 2026-08-22: UpdateProjectProfile validates that every required blueprint parameter
  # without a default is declared ("Missing required Blueprint parameter(s): bucketName"), a
  # validation CreateProjectProfile never ran, which is how the profiles were created without
  # them. S3Bucket's bucketName and S3TableCatalog's catalogName are per-project names: both
  # templates consume them by literal Ref, with no per-project suffix added, so a locked value
  # would collide between projects and S3's namespace is global. The placeholder is what the
  # portal pre-fills when a member enables the capability (deployment_mode ON_DEMAND), and
  # is_editable = true so the member replaces it. A project deployed with the placeholder
  # unchanged fails or collides visibly, rather than sharing a name silently.
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
