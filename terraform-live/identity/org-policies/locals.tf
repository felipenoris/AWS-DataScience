# What the configuration computes - Stage 2 step 5.
#
# THE SHAPE OF THIS FILE IS THE SHAPE OF THE IMPORT. Everything below exists so that the ten
# documents and the ten attachments can be derived from two authored sources - the templates in
# policies/ and the map in attachments.json - and from identifiers read out of the API. Nothing
# is typed twice, and the two places where something MUST be authored a second time (the policy
# TYPE and the DESCRIPTION, neither of which lives in a tracked file today) are guarded by a
# precondition that names the drift rather than absorbing it.

locals {
  # ------------------------------------------------------------------------- the authored map
  #
  # ONE FILE, TWO CONSUMERS, ON PURPOSE (Lesson 14): scripts/check-ou-coverage.py and this
  # for_each read the same bytes, so the thing step 9.3 checks is the thing the apply uses. Read
  # attachments.json itself before changing anything here - the `_note` at the top of it is the
  # reasoning, and it is longer than the data.
  attachments = jsondecode(file("${path.module}/attachments.json"))

  # ------------------------------------------------------- the five identifiers render.py uses
  #
  # SAME FIVE NAMES, SAME FIVE VALUES, COMPUTED THE SAME WAY. render.py produced the bytes that
  # are attached to the organization right now, and decision 5 turns on that: the import
  # compares a document against itself only if this substitution is the one that was performed.
  org_id  = data.aws_organizations_organization.this.id
  root_id = one(data.aws_organizations_organization.this.roots[*].id)

  # `Data` is required whether or not it carries a document, because <ACCOUNT_ID_DATA> and
  # <ORG_PATH_DATA> are rendered from it. Deriving the requirement from the map alone would make
  # the baseline document's substitution depend on the Data OU still being in the .ou list - a
  # coupling nobody would predict from reading either file.
  ou_names_required = setunion(toset(keys(local.attachments.ou)), toset(["Data"]))

  ou_ids = {
    for name in local.ou_names_required : name => one([
      for ou in data.aws_organizations_organizational_unit_descendant_organizational_units.all.children :
      ou.id if ou.name == name
    ])
  }

  ou_id_data = local.ou_ids["Data"]

  # aws:PrincipalOrgPaths is the full path WITH a trailing slash, and `Data` sits directly under
  # the root, so this is the whole path. A nested OU would need one more segment - and `*` in
  # place of the final slash only if the carve-out is meant to reach children.
  org_path_data = "${local.org_id}/${local.root_id}/${local.ou_id_data}/"

  account_id_data = one([
    for a in data.aws_organizations_organizational_unit_child_accounts.data_ou.accounts :
    a.id if a.status == "ACTIVE"
  ])

  # THE ACCOUNT THIS SLICE IS APPLIED FROM, for the profile precondition in policies.tf. The
  # name is the EXACT VENDED ONE - Control Tower gave every account an ` Account` suffix, and
  # 1d step 9 paid for that once already. `status == "ACTIVE"` is not decoration either: a
  # SUSPENDED `Sandbox` sits in this roster, so a name match alone can find a dead account.
  # `one()` yields null on no match and raises on an ambiguous one, and the precondition turns
  # the null into a sentence about the profile.
  identity_account_id = one([
    for a in data.aws_organizations_organization.this.accounts :
    a.id if a.name == "Identity Account" && a.status == "ACTIVE"
  ])

  # ----------------------------------------------------------------------- the ten documents
  #
  # DERIVED FROM THE MAP, NOT FROM A GLOB OVER THE FOLDER - and the difference is `canary/`.
  # That folder holds throwaway documents attached to `Policy Test` during a battery and
  # detached in the same sitting; a Terraform resource for one would turn a document that must
  # not persist into one that does. Driving from attachments.json cannot reach it, and cannot
  # reach an untethered file in policies/ either. The reverse direction - a file nobody
  # attached - is what `unmapped_documents` below is for.
  documents     = sort(distinct(concat(local.attachments.root, flatten(values(local.attachments.ou)))))
  documents_set = toset(local.documents)

  # --------------------------------------------------------------------------- the rendering
  #
  # `replace(file(...))` AND NOT `templatefile()` - decision 5, settled 2026-08-16. The
  # placeholders are angle-bracketed rather than `${...}`, so templatefile() does not see them;
  # converting them would mean editing render.py in the same commit that first compares against
  # what render.py generated, which makes the reference and the comparison move together.
  #
  # ALL FIVE SUBSTITUTIONS RUN ON EVERY DOCUMENT, though only three appear in policies/ today
  # (<ORG_ID> x6, <ORG_PATH_DATA> x1, <ACCOUNT_ID_DATA> x1 - measured 2026-08-16). Replacing an
  # absent placeholder is a no-op, and running the full set is what keeps this and render.py the
  # same substitution rather than two that currently agree. No token is a substring of another,
  # so the order of the five is immaterial.
  rendered = {
    for name in local.documents : name => replace(
      replace(
        replace(
          replace(
            replace(file("${path.module}/policies/${name}.json"), "<ORG_ID>", local.org_id),
            "<ROOT_ID>", local.root_id
          ),
          "<OU_ID_DATA>", local.ou_id_data
        ),
        "<ORG_PATH_DATA>", local.org_path_data
      ),
      "<ACCOUNT_ID_DATA>", local.account_id_data
    )
  }

  # THE `jsonencode(jsondecode(...))` WRAPPER IS NOT DECORATION. It normalises this side the way
  # the provider normalises the other, so what is compared is content and not whitespace.
  #
  # WHAT IT DOES NOT DO, measured 2026-08-16 and worth knowing before reading a diff: it does not
  # make the two strings byte-equal. `jsonencode` sorts object keys; Organizations minifies but
  # preserves the order it was given. The plan is empty anyway because the provider compares
  # `content` STRUCTURALLY (verify.SuppressEquivalentJSONDiffs, a reflect.DeepEqual on the
  # decoded values) - which is also why that comparison is not IAM-aware, and why
  # awsds-org-rcp-perimeter.json had to stop writing a one-element Action as an array: `["ecr:*"]`
  # and `"ecr:*"` mean the same thing to IAM and are different values to DeepEqual.
  policy_documents = { for name, text in local.rendered : name => jsonencode(jsondecode(text)) }

  # An unsubstituted placeholder parses as JSON and attaches, and the deny it guards then names
  # a literal `<ORG_ID>` and never fires. render.py refuses to leave one; so does this.
  survivors = { for name, text in local.rendered : name => regexall("<[A-Z_]+>", text) }

  # ------------------------------------------------------- what has to be authored twice, and
  #                                                          the checks that say so out loud
  #
  # NEITHER THE TYPE NOR THE DESCRIPTION LIVES IN A TRACKED FILE. A policy document is JSON and
  # carries no field for either; attachments.json records targets, not attributes. So both are
  # written out below - and both are checked against `documents` in both directions, because a
  # map that has drifted from the document set fails in two different ways and only one of them
  # is loud on its own (an index into a missing key errors; a stale extra key does nothing).

  # MEASURED FROM THE ORGANIZATION 2026-08-16, not inferred from the file names. `type` is
  # ForceNew: a wrong entry here does not fail politely, it plans a destroy and a create on a
  # document that is attached - which is a momentary hole in the ceiling, and the reason
  # policies.tf carries prevent_destroy.
  policy_types = {
    "awsds-org-scp-baseline"        = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-perimeter"       = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-tag-enforcement" = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-ou-workloads"    = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-ou-identity"     = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-ou-interactive"  = "SERVICE_CONTROL_POLICY"
    "awsds-org-scp-ou-data"         = "SERVICE_CONTROL_POLICY"
    "awsds-org-rcp-perimeter"       = "RESOURCE_CONTROL_POLICY"
    "awsds-org-tag-policy"          = "TAG_POLICY"
    "awsds-org-declarative-ec2"     = "DECLARATIVE_POLICY_EC2"
  }

  # THE FIRST APPLY CHANGES FOUR OF THESE IN AWS, AND THAT IS THE POINT OF WRITING THEM HERE.
  # Read back 2026-08-16: `awsds-org-scp-tag-enforcement` carries an empty string,
  # `awsds-org-tag-policy` and `awsds-org-declarative-ec2` carry none at all, and
  # `awsds-org-rcp-perimeter` carries its whole text wrapped in literal double quotes - a
  # console paste that kept its quoting. The other six are already what is below, to the byte.
  #
  # The alternative was to reproduce the four defects so the first plan touched no description.
  # That buys a cleaner gate and pays for it by versioning the defect, and the gate step 5.5
  # actually asks for is about `content` and `type` - so the repository becomes the source of
  # truth instead, and the four are named above so the plan is read rather than approved.
  policy_descriptions = {
    "awsds-org-scp-baseline"        = "Stage 1c step 7.5 - organization baseline: LeaveOrganization, IAM users, account BPA (carve-out), snapshot and AMI sharing, ecr-public, GuardDuty, datazone outside Data OU."
    "awsds-org-scp-perimeter"       = "Stage 1c step 7.5 - trusted resources: deny S3 object writes and ECR layer/image pushes to resources outside this organization."
    "awsds-org-scp-tag-enforcement" = "Stage 1c step 7.8 - Environment and Project required on ec2:RunInstances, one statement per key, scoped to instance/*."
    "awsds-org-scp-ou-workloads"    = "Stage 1c step 7.6 - Workloads OU: no interactive SageMaker surface, no DataZone."
    "awsds-org-scp-ou-identity"     = "Stage 1c step 7.6 - Identity OU: deny user compute (EC2, SageMaker, Glue, Lambda, ECS) in an account that runs no workload, only Terraform managing Identity Center."
    "awsds-org-scp-ou-interactive"  = "Stage 1c step 7.6 - Interactive OU (Development + the nested Sandboxes): deny the classic SageMaker notebook instance and its presigned URL. SMUS notebooks are spaces and apps and are unaffected."
    "awsds-org-scp-ou-data"         = "Stage 1c step 7.6 - Data OU: deny user compute; crawler and column-statistics runs allowed only for awsds-data-catalog-maintenance (D27); deny bucket deletion and Lake Formation deregistration."
    "awsds-org-rcp-perimeter"       = "Stage 1c step 7.8 - deny access to S3, DynamoDB, SQS, KMS, Secrets Manager, ECR and sts:AssumeRole from principals outside the organization."
    "awsds-org-tag-policy"          = "Stage 1c step 7.8 - canonical capitalisation and value enumerations for the five mandatory tags. Reports, does not enforce."
    "awsds-org-declarative-ec2"     = "Stage 1c step 7.8 - snapshot and AMI public-access blocks, IMDSv2 as the account default, serial console off."
  }

  # A file in policies/ that the map never attaches. Not an error in AWS - it is a document
  # nobody owns, which is the shape Lesson 5 keeps naming: an intention is not a control.
  # check-ou-coverage.py checks the other direction (every name in the map is a file); this is
  # the half a script running against the live tree cannot see.
  policy_files       = toset([for f in fileset("${path.module}/policies", "*.json") : trimsuffix(f, ".json")])
  unmapped_documents = setsubtract(local.policy_files, local.documents_set)

  types_missing        = setsubtract(local.documents_set, toset(keys(local.policy_types)))
  types_extra          = setsubtract(toset(keys(local.policy_types)), local.documents_set)
  descriptions_missing = setsubtract(local.documents_set, toset(keys(local.policy_descriptions)))
  descriptions_extra   = setsubtract(toset(keys(local.policy_descriptions)), local.documents_set)

  # ----------------------------------------------------------------------- the ten attachments
  #
  # THE KEY IS `<document>:<target>` AND THE TARGET HALF IS THE MAP'S VOCABULARY: the literal
  # `root`, or an OU NAME. It contains no id and reads nothing from AWS, which is what step 5.3
  # point 7 asks for - adding an OU adds a key and leaves every existing key untouched, so a new
  # attachment cannot re-create an existing one. A plan that wants to destroy and re-create an
  # SCP attachment is a momentary hole in the ceiling.
  #
  # ./aws/import-ids.py EMITS THIS EXACT KEY, and it was corrected to do so in this sitting: the
  # Organizations API calls the root `Root` and the map calls it `root`. The configuration owns
  # the address and the script follows it - the same correction the sso/ assignments needed.
  attachment_pairs = merge(
    {
      for doc in local.attachments.root : "${doc}:root" => {
        document  = doc
        target    = "root"
        target_id = local.root_id
      }
    },
    merge([
      for ou_name, docs in local.attachments.ou : {
        for doc in docs : "${doc}:${ou_name}" => {
          document  = doc
          target    = ou_name
          target_id = local.ou_ids[ou_name]
        }
      }
    ]...)
  )
}
