# The release this slice runs (Stage 8 decision 12): the application tag and the digest its pipeline
# pushed, recorded in this repository so that a re-apply after a teardown runs the same image (Lesson 4).
# In Sandbox a person writes it once the tag's pipeline has printed the digest; in Staging and Production
# the pipeline passes the release it promotes, and step 3.7 records it here the same way.

variable "release" {
  description = "The application release: its git tag and the image digest in awsds-prod-ecr-app-etl. Null until the first release exists; the job request (outputs.tf) is null with it."
  type = object({
    tag    = string
    digest = string
  })
  # v0.1.0, pushed by awsds/app-etl's pipeline #15 as v0.1.0-d7e093a9 (2026-10-14).
  default = {
    tag    = "v0.1.0"
    digest = "sha256:33f76dec8bf7b7be760db1daf575c388172e49862381f66f8032b534bce5280d"
  }

  validation {
    condition     = var.release == null || can(regex("^v[0-9]+\\.[0-9]+\\.[0-9]+$", var.release.tag))
    error_message = "release.tag must be v<major>.<minor>.<patch>, the protected tag shape (step 2.1)."
  }

  validation {
    condition     = var.release == null || can(regex("^sha256:[0-9a-f]{64}$", var.release.digest))
    error_message = "release.digest must be sha256: followed by 64 lowercase hex characters."
  }
}
