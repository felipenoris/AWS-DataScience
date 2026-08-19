variable "bucket_name" {
  description = "Bucket name, awsds-<env>-<component> (conventions §6). Name buckets as if permanent - from this module they are (prevent_destroy)."
  type        = string
  nullable    = false
}

variable "kms_key_arn" {
  description = "The CMK that encrypts the bucket - SSE-KMS is unconditional here; which key is the caller's decision (D19/D36: a key shared across trust boundaries merges two questions into one)."
  type        = string
  nullable    = false
}

variable "noncurrent_version_expiration_days" {
  description = "Days a noncurrent version is kept - a cost choice (Stage 2 decision 3's shape)."
  type        = number
  default     = 90
}

variable "additional_policy_statements" {
  description = "Extra bucket-policy statements appended after the TLS-only deny - S3 holds one policy per bucket, so they must arrive through the module. Type `any`, deliberately (v0.2.0): IAM statements are heterogeneous objects - a Deny with three condition operators and an Allow with one do not unify into the single element type list(any) demands - and the module only ever concat()s and jsonencode()s them, so the loose type costs nothing the JSON encoding does not already accept."
  type        = any
  default     = []
}
