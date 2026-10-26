# The release this slice runs (Stage 10 step 2.4, decision 1; Stage 8 steps 3.6 and 3.7). The release
# job extracts the tag's bundle under applications/<application>/<tag>/ of awsds-prod-outputs, the
# bundle's own tree with each workflow's YAML rendered for this account, and passes the S3 VersionIds
# of the YAML and the worker's code package with -var. The promoted release is then
# recorded as this variable's default, so a by-hand apply after `make down ENV=production` creates the
# same workflows from the same object versions (Lesson 4).
#
# The default is v0.4.6 (pipeline #102, 2026-10-25), its VersionIds read from the leg's record
# production-release.auto.tfvars.json; Staging creates no workflow for app-etl-warehouse, Production's alone (Stage 9
# decision 15). Null creates nothing: no workflow can exist before its definition does, and a chain
# names its workflows.

variable "release" {
  description = "The release this slice runs: the application's tag, and per workflow key the S3 VersionId of its rendered definition and, when it has Python or Bash tasks, of its code package. Null creates nothing."
  type = object({
    tag = string
    workflows = map(object({
      definition_version_id = string
      code_version_id       = optional(string)
    }))
  })
  default = {
    tag = "v0.4.6"
    workflows = {
      "app-etl" = {
        definition_version_id = "4NS.8XnUqg.opodG.h6A65pBT1vrFIwE"
        code_version_id       = "l1L3_a6GpJ0T8wyF4z5gMWEIiMtxIfpR"
      }
      "app-etl-train" = {
        definition_version_id = "HGgrM4QbDKsgTm2MMy9KEZzWjoaT8_0E"
        code_version_id       = "KkRVOadtFSijd3Sdgtjyy1lhsUQTi9KD"
      }
      "app-etl-warehouse" = {
        definition_version_id = "IXw8uLnPshTnOzZVZWayWcHVfabzSgBG"
      }
    }
  }

  validation {
    condition     = var.release == null ? true : can(regex("^v[0-9]+\\.[0-9]+\\.[0-9]+$", var.release.tag))
    error_message = "release.tag is the application's release tag, vMAJOR.MINOR.PATCH (Stage 8 step 2.1)."
  }
}
