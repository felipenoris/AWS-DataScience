# The release this slice runs (Stage 8 decision 12 and step 3.7): the application tag, the image
# digest its pipeline pushed and the bundle's SHA256. The pipeline passes the release it promotes, and
# step 3.7 records it here as the default, so a by-hand re-apply after a teardown runs the same
# release (Lesson 4). The default is v0.4.6 (pipeline #102, 2026-10-25), read from the tag's release
# job. Null creates nothing.

variable "release" {
  description = "The application release: its git tag, the image digest in awsds-prod-ecr-app-etl and the SHA256 of its bundle in awsds-prod-releases. Null creates nothing."
  type = object({
    tag           = string
    digest        = string
    bundle_sha256 = string
  })
  default = {
    tag           = "v0.4.6"
    digest        = "sha256:ba8d41bf08bebee084b38e7df9b8efa28e6fcccaf9865e0591fdec7d0462f98d"
    bundle_sha256 = "7334604b2f58564ebb3ee3032dea9900b4916966b84376880e36f4c9737fb50c"
  }

  validation {
    condition     = var.release == null ? true : can(regex("^v[0-9]+\\.[0-9]+\\.[0-9]+$", var.release.tag))
    error_message = "release.tag is the application's release tag, vMAJOR.MINOR.PATCH (Stage 8 step 2.1)."
  }

  validation {
    condition     = var.release == null ? true : can(regex("^sha256:[0-9a-f]{64}$", var.release.digest))
    error_message = "release.digest is sha256: followed by 64 lowercase hex characters."
  }

  validation {
    condition     = var.release == null ? true : can(regex("^[0-9a-f]{64}$", var.release.bundle_sha256))
    error_message = "release.bundle_sha256 is 64 lowercase hex characters, the value store-bundle checked."
  }
}
