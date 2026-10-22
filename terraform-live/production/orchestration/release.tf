# The release this slice runs (Stage 10 step 2.4, Stage 8 steps 3.6 and 3.7). The release job renders
# each workflow of the tag's bundle for this account, writes it under
# workflows/<application>/<tag>/workflows/ of awsds-prod-outputs with the worker's code package under
# .../code/, and passes the S3 VersionIds the writes returned with -var. The promoted release is then
# recorded as this variable's default, so a by-hand apply after `make down ENV=production` creates the
# same workflows from the same object versions (Lesson 4).
#
# Null until the first promotion, and the slice creates nothing while it is: no workflow can exist
# before its definition does, and a chain names its workflows.

variable "release" {
  description = "The release this slice runs: the application's tag, and per workflow key the S3 VersionId of its rendered definition and, when it has Python or Bash tasks, of its code package. Null creates nothing."
  type = object({
    tag = string
    workflows = map(object({
      definition_version_id = string
      code_version_id       = optional(string)
    }))
  })
  default = null

  validation {
    condition     = var.release == null ? true : can(regex("^v[0-9]+\\.[0-9]+\\.[0-9]+$", var.release.tag))
    error_message = "release.tag is the application's release tag, vMAJOR.MINOR.PATCH (Stage 8 step 2.1)."
  }
}
