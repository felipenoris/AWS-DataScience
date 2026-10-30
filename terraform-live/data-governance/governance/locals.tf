locals {
  # Decision 5's category 1, by API name - the blueprints a project profile may bundle. The same
  # list terraform-modules/sagemaker-prereqs/ enables per member account and ./aws/studio.py US-3
  # holds; docs/SMUS.md is the reference table with the three categories and the billing shapes.
  # A category-2 blueprint (MLExperiments, for example) joins all three in one commit
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
  # `index(each.value.blueprints, bp)` as each environment's `deployment_order`, so
  # Tooling must come first and a name joins at the end - nothing else provisions a working project. The grouping after it is
  # not a dependency graph anybody has read; a stricter order is a measurement at step 2.4.
  category_one_blueprints = [
    # The base environment, first: it provisions the project's SageMaker AI domain, roles and
    # security groups, and nothing else works without it. `deployment_order` is `index()` into
    # each profile's copy of this list.
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
    # The generative-AI surface. `AmazonBedrockGenerativeAI` is a console grouping with no API
    # identifier (measured 2026-08-21 - `list-environment-blueprints` returns seven
    # `AmazonBedrock*` blueprints and no aggregate), so decision 5's category 1 is delivered by
    # naming them. AmazonBedrockKnowledgeBase, the seventh, is last in the list.
    "AmazonBedrockChatAgent",
    "AmazonBedrockEvaluation",
    "AmazonBedrockFlow",
    "AmazonBedrockFunction",
    "AmazonBedrockGuardrail",
    "AmazonBedrockPrompt",
    # Experiment tracking, out of category 2 at Stage 17 pass 1 (decision 2, taken 2026-10-12):
    # the serverless MLflow App. MLExperiments, the tracking server, stays category 2. Its
    # template's one user parameter, `mlflowAppName`, has a default, so `blueprint_parameters`
    # below declares nothing for it (read 2026-10-18).
    "MLflowApp",
    # The knowledge base, out of category 2 at Stage 17 step 7.0a (decision 1, taken 2026-10-12):
    # the portal opens its Generative AI menu only when the profile carries all seven Bedrock
    # blueprints (read from the portal's code 2026-10-19). Its template's parameters without a
    # default are the four `datazoneEnvironment*` ones, none of them a user parameter, so
    # `blueprint_parameters` declares nothing for it (read 2026-10-19). Appended last, like
    # MLflowApp, so every environment above keeps its `deployment_order`.
    "AmazonBedrockKnowledgeBase",
    # The SageMakerAIDomain blueprint (released 2026-10-20), out of `undefined` at 6d decision due 15,
    # taken 2026-10-30 by the user as (b): a standalone SageMaker AI domain per project beside
    # Tooling's, the code spaces experience as the profile's parameters below, RStudio on. Last, so
    # every environment above keeps its `deployment_order`; ON_DEMAND, so a project gets the domain
    # only when an owner enables it from Code spaces.
    "SageMakerAIDomain",
  ]

  member_account_ids = {
    sandbox = data.aws_caller_identity.sandbox.account_id
    # The domain's own account, a profile's target since Stage 6f step 11 (no association).
    data-governance = data.aws_caller_identity.current.account_id
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
  #
  # `blueprints` is the profile's own list, in deployment order with Tooling first (profiles.tf
  # refuses any other order and any blueprint outside category 1).
  project_profiles = merge(
    {
      experimentation = {
        account     = "sandbox"
        blueprints  = local.category_one_blueprints
        group       = "sso-group-data-scientists"
        description = "Experimentation (D21): the unit of work is a notebook. Provisions into a business unit's Sandbox."
      }
    },
    # Stage 6f step 11 (decision 1, shape (b), the pilot of 2026-10-26): the project that publishes
    # the lake's tables, in the lake's own account, where its Glue data source reads the catalog.
    # Tooling alone, spaces off: no compute, and the Data OU denies every launch here anyway. The
    # Governance Manager creates it and owns it, so a subscription is approved by the person whose
    # decisions the grant model resolves to (docs/ORGANIZATION.md), never by the requester.
    var.lake_publishing_enabled ? {
      lake-publishing = {
        account     = "data-governance"
        blueprints  = ["Tooling"]
        group       = "sso-group-governance-managers"
        description = "Lake publishing (Stage 6f step 11): publishes the governed lake's tables to the catalog from the lake's own account. Tooling with spaces off; no compute."
      }
    } : {},
  )

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
  # The house image's objects in Sandbox, by terraform-live/sandbox/dev-env/'s name contract
  # (`awsds-<env>-dev-env`, one app image configuration per app type). The version is the pin the
  # SageMakerAIDomain template writes into the domain's CustomImages, so a release reaches the pilot's
  # domain by moving var.sandbox_dev_env_version and an Update project per project (docs/SMUS.md,
  # "Custom images"); the default-image ARN carries the same version, which is what the release
  # pipeline's retire job keeps (gitlab/awsds/dev-env/release/versions.py reads CustomImages alone).
  sandbox_dev_env_image = "awsds-sandbox-dev-env"
  sandbox_dev_env_image_version_arn = format(
    "arn:%s:sagemaker:%s:%s:image-version/%s/%d",
    data.aws_partition.current.partition,
    var.region,
    local.member_account_ids.sandbox,
    local.sandbox_dev_env_image,
    var.sandbox_dev_env_version,
  )

  # The SageMakerAIDomain blueprint's parameters (6d decision due 15 (b), 2026-10-30). They are the
  # template's own and per app type, so Tooling's rows above do not reach this domain: the same
  # ceilings are written again, locked (Lesson 5), from the same variables. The image triples are
  # `imageName;appImageConfigName;versionNumber`, the template's comma-separated form, one entry per
  # app type. enableRStudio cannot be turned off once true (the template's note), so it is a locked
  # value, not a member's choice; with it the template adds an EFS home, service-managed security
  # groups and Posit's RStudio, whose licence and inline policy are the user's acts (the waiting
  # list). hiddenInstanceTypes, hiddenSageMakerImageVersionAliases and domainName keep the template's
  # empty defaults: the instance ceiling is the SCP's, not a picker's (Lesson 5).
  sagemaker_ai_domain_parameters = [
    {
      name        = "customImagesJupyterLab"
      value       = "${local.sandbox_dev_env_image};${local.sandbox_dev_env_image}-jupyterlab;${var.sandbox_dev_env_version}"
      is_editable = false
    },
    {
      name        = "customImagesCodeEditor"
      value       = "${local.sandbox_dev_env_image};${local.sandbox_dev_env_image}-codeeditor;${var.sandbox_dev_env_version}"
      is_editable = false
    },
    { name = "defaultImageVersionArnJupyterLab", value = local.sandbox_dev_env_image_version_arn, is_editable = false },
    { name = "defaultImageVersionArnCodeEditor", value = local.sandbox_dev_env_image_version_arn, is_editable = false },
    { name = "lifecycleManagementJupyterLab", value = "ENABLED", is_editable = false },
    { name = "lifecycleManagementCodeEditor", value = "ENABLED", is_editable = false },
    { name = "idleTimeoutInMinutesJupyterLab", value = tostring(var.idle_timeout_minutes), is_editable = true },
    { name = "idleTimeoutInMinutesCodeEditor", value = tostring(var.idle_timeout_minutes), is_editable = true },
    { name = "minIdleTimeoutInMinutesJupyterLab", value = tostring(var.idle_timeout_minutes), is_editable = false },
    { name = "minIdleTimeoutInMinutesCodeEditor", value = tostring(var.idle_timeout_minutes), is_editable = false },
    { name = "maxIdleTimeoutInMinutesJupyterLab", value = tostring(var.max_idle_timeout_minutes), is_editable = false },
    { name = "maxIdleTimeoutInMinutesCodeEditor", value = tostring(var.max_idle_timeout_minutes), is_editable = false },
    { name = "maxEbsVolumeSize", value = tostring(var.max_ebs_volume_size_gb), is_editable = false },
    { name = "enableRStudio", value = "true", is_editable = false },
  ]

  blueprint_parameters = {
    Tooling           = local.tooling_parameters
    SageMakerAIDomain = local.sagemaker_ai_domain_parameters
    S3Bucket = [
      { name = "bucketName", value = "changeme-project-bucket", is_editable = true },
    ]
    S3TableCatalog = [
      { name = "catalogName", value = "changemecatalog", is_editable = true },
    ]
  }

  # The overrides each profile passes, by profile name. `lake-publishing` takes experimentation's
  # Tooling rows plus `enableSpaces` false and locked: the template creates the project's SageMaker
  # AI domain only when it is true (read 2026-10-19), the Data OU denies sagemaker:Create*, and the
  # value is the one Stage 18 measured deploying with no CreateDomain (its step 3.2).
  profile_parameters = {
    experimentation = local.blueprint_parameters
    lake-publishing = {
      Tooling = concat(local.tooling_parameters, [
        { name = "enableSpaces", value = "false", is_editable = false },
      ])
    }
  }
}
