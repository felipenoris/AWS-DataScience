# The release this slice runs (Stage 8 decision 12 and step 3.7): the application tag, the image
# digest its pipeline pushed and the bundle's SHA256. The pipeline passes the release it promotes, and
# step 3.7 records it here as the default, so a by-hand re-apply after a teardown runs the same
# release (Lesson 4). The default is v0.4.7 (pipeline #117, 2026-11-15), read from the legs' deploy
# jobs. Null creates nothing.

variable "release" {
  description = "The application release: its git tag, the image digest in awsds-prod-ecr-app-etl and the SHA256 of its bundle in awsds-prod-releases. Null creates nothing."
  type = object({
    tag           = string
    digest        = string
    bundle_sha256 = string
  })
  default = {
    tag           = "v0.4.7"
    digest        = "sha256:14ae4d039eb34b08110c71648a253b7559b8615106c4713ffbec7ae2dfff6126"
    bundle_sha256 = "001eafbb4d90514802f14f97c75043b5d1d0241295e3b11d944f96c730c65826"
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
