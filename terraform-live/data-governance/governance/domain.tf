# THE UNIFIED DOMAIN (D26, INT-12) - one domain, in the account that owns nothing else about
# it: a REGISTRY, never a runtime.
#
# THE SENTENCE MOST EASILY MISREAD, AND IT IS ENFORCED RATHER THAN ASSERTED: no blueprint is
# enabled in this account, so the domain provisions nothing here. The enforcement is an OU SCP
# (awsds-org-scp-ou-data denies sagemaker:Create*, 1c step 7.6) which stays FREE precisely
# because of the split - and Stage 6 step 0.4 reads this slice's plan for any
# aws_sagemaker_* / awscc_sagemaker_* resource before the first apply. There is none, and the
# correction if one ever appears is re-checking why a blueprint got enabled here, never
# weakening the OU document.
#
# THE REGION COUPLING (step 1.1): the domain and IAM Identity Center must share a Region, and
# neither can move afterwards. Multi-Region became possible in 2026-04 but only with an
# EXTERNAL IdP connected to IdC - this project uses the native directory - and trusted identity
# propagation does not cross Regions either way. Both are us-west-2.
#
# THIS APPLY IS ALSO THE CARVE-OUT PROBE (step 0.1a). DenyDataZoneDomainOutsideDataOu has never
# been exercised in either direction: its condition is ForAllValues:StringNotLike on
# aws:PrincipalOrgPaths, and a ForAllValues operator over a key that does not populate
# evaluates TRUE - so if DataZone requests carry no org path, the deny catches everyone, this
# account included. The 2026-08-20 CLI probe never reached authorization at all (four role
# shapes, two accounts, one byte-identical `Cross-account pass role is not allowed`), so the
# reading rides HERE, on the next CreateDomain this organization issues. Stage it with Recipe D
# so the domain goes first and nothing is half-built around a refused domain, and read the
# three-outcome fork in the stage file - created / SCP-denied / the validation wall again.
#
# NO CUSTOMER KMS KEY, AND IT IS A CHOICE. kms_key_identifier would put the domain's metadata
# under a CMK of ours at +USD 1.00/key-month (docs/PRICING.md 2) against a domain whose whole
# at-rest cost is ~USD 0.50/month. docs/GOVERNANCE.md §Encryption's rule is "one data CMK per
# account for DATA" and says in as many words that it is not a merger of every key in the
# account - the catalog holds names and descriptions, not rows. REVISION TRIGGER: the first
# catalog metadata whose CONTENT is itself sensitive - a column name that discloses what a
# restricted table is about would be the concrete case.
#
# user_assignment = AUTOMATIC: an Identity Center user who reaches the portal gets a user
# profile created on first sign-in. It grants NOTHING on its own - a user with no project
# membership sees an empty portal - and the alternative (MANUAL) adds an admin step per person
# to a design whose entitlement is carried by IdC groups, project membership and Lake
# Formation. REVISION TRIGGER: the day the Identity Center directory holds people who should
# not be able to reach the portal at all.

resource "aws_datazone_domain" "this" {
  name        = var.domain_name
  description = "The one SageMaker Unified Studio domain (D26). A registry: blueprints provision compute into Sandbox and Development, never into this account."

  domain_version        = "V2"
  domain_execution_role = module.domain_execution_role.role_arn
  service_role          = module.domain_service_role.role_arn

  single_sign_on {
    type            = "IAM_IDC"
    user_assignment = "AUTOMATIC"
  }

  # A domain with projects in it refuses to be deleted unless this is set. Leaving it FALSE is
  # the safety: the delete path for this object is "understand what depends on it first", and
  # D11 never touches it anyway - the domain is [P], metadata-priced, and destroying it would
  # orphan every project's home storage and churn every id (Stage 6 step 8.3).
  skip_deletion_check = false
}
