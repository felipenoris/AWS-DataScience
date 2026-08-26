# Inputs. Everything that differs between the two callers is here and nothing else is: the
# whole point of this module is that `sandbox/data/` and `development/data/` are the SAME
# design applied twice (Stage 5 step 8's heading, "one module for both"), and D35 makes that
# three times at the second business unit. A setting that lives in the slice instead of here
# is a setting that will differ between accounts by accident (Lesson 14).

variable "env" {
  description = "The <env> NAME TOKEN of docs/plan/conventions.md - what goes into a resource name. Never *the* sandbox: D35 vends one per business unit."
  type        = string
  nullable    = false
}

variable "region" {
  description = "AWS region - portability rule (docs/plan/architecture.md 4.1). Consumed by the kms:ViaService condition, which is written per region and cannot be a wildcard without becoming a different statement."
  type        = string
  nullable    = false
}

variable "lake_catalog_id" {
  description = "The Data Governance account id, resolved LIVE by the caller's aliased provider (aws/INDEX.md rule 1 - never a literal in a tracked file). It addresses two different things and both are cross-account: the target catalog of every resource link, and the catalog that OWNS the LF-Tags the re-grants below are written over."
  type        = string
  nullable    = false
}

variable "lake_databases" {
  description = "The shared databases to resource-link, by short key, read from data-governance/data/'s own state output rather than typed (Lesson 14). The DROP-BOX is expected to be absent: it is gated out of the share by the `layer` expression (Lesson 29), so a link to it would resolve nothing - and its presence in this map is a finding, not a convenience."
  type        = map(string)
  nullable    = false
}

variable "data_lake_admin_role_arn" {
  description = "This account's data lake administrator - InfrastructureAccess, per Stage 5 decision 5. Resolved BY PATTERN in the caller (the AWSReservedSSO_* suffix is minted per account and cannot be written down). Without one, AWS shows the account an EMPTY catalog while its RAM holds the share - measured on both consumers 2026-08-19, and the reason this resource exists at all."
  type        = string
  nullable    = false
}

variable "data_scientist_role_arn" {
  description = "The persona the share is re-granted to (D18). A cross-account grant lands on the ACCOUNT; nothing inside it can read a row until the local administrator passes the permission on to a local principal - that re-grant is this module's, and it is why the producer side grants everything WITH the grant option (docs/GOVERNANCE.md, Grants)."
  type        = string
  nullable    = false
}

variable "scan_limit_bytes" {
  description = "Per-query bytes-scanned cutoff on the workgroup - Athena bills USD 5/TB (docs/PRICING.md), so this is the cost guard on a query nobody meant to run. The default is 10 GiB = USD 0.05 at that rate, which is three orders of magnitude above anything this lake holds today and still bounds a runaway. A query that exceeds it is CANCELLED, so raising it is a deliberate act with a number attached."
  type        = number
  default     = 10737418240
}

variable "derived_expiration_days" {
  description = "Lifecycle expiry on the derived zone (D19 practice iii, Stage 5 step 9.2) - the shadow lake does not silently become permanent. 30 days is the stage's own starting figure; DL-9 checks the rule exists, never the number."
  type        = number
  default     = 30
}

variable "additional_data_key_policy_statements" {
  description = "Extra statements appended to the account data CMK's policy - KMS holds ONE policy per key, so a second reader can only arrive through the module (the same constraint s3-bucket's additional_policy_statements answers for buckets). Empty by default, which is what keeps a consumer that adds nothing byte-identical across the tag bump. Type `any`, deliberately: IAM statements are heterogeneous objects and the module only ever concat()s and jsonencode()s them. The first caller is Stage 16's sandbox lake, admitting its access role; anything passed here is a WIDENING of D31's read control and belongs in the calling slice's README row."
  type        = any
  default     = []
}

variable "additional_data_lake_admin_role_arns" {
  description = "Data lake administrators BESIDES var.data_lake_admin_role_arn - concat()ed into `admins`, which this resource replaces wholesale. Empty by default. It exists because SageMaker Unified Studio adds its own two service roles when the first project in an account is created (found 2026-08-26, Sandbox; Development has no project and still re-plans `No changes`), and a narrow list would strip them on the next apply. ADOPTION, not endorsement: whether a SMUS provisioning role should administer Lake Formation is a Stage 6 governance question this variable does not answer."
  type        = list(string)
  default     = []
}

variable "allow_full_table_external_data_access" {
  description = "The DataLakeSettings flag of the same name. NULL - the default - leaves it undeclared, which is what a consumer with no SMUS project wants. Sandbox reads back `true`, set by the service alongside the two administrators above; the value is adopted rather than chosen, and it is an input because it is read from the account, not decided here."
  type        = bool
  default     = null
}
