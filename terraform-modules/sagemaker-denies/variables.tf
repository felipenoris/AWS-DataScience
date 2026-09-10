variable "allowed_instance_types" {
  description = "Every ml.* instance type any principal in this design may ask SageMaker for outside a space - jobs, endpoints, notebook instances. Since v0.2.0 (2026-09-07, the user's decision) the space path (CreateApp, CreateSpace, UpdateSpace) carries no ceiling. D12's budget expressed as a control: the budget notifies nobody, so the only thing that stops a USD 30/hour job parameter is a policy that refuses it in the first hour."
  type        = list(string)
  nullable    = false

  # The canonical list. Both callers - the six persona sets in terraform-live/identity/sso/ and
  # the project boundary in sagemaker-prereqs - omit the argument or pass null, which
  # `nullable = false` resolves to this default. The module shares the structure; a values list
  # written once at each end would be exactly the divergence it exists to prevent (Lesson 33).
  #
  # In it: the app sizes SMUS launched when the list still reached apps (ml.t3.medium is the
  # JupyterLab and Code Editor default, USD 0.050/h - docs/PRICING.md 8; ml.t3.large 0.100 is
  # the remote-IDE floor) plus a small general-purpose and compute range for jobs, which are the
  # only calls this list governs. No GPU and nothing at *.2xlarge or larger: a single ml.p3 hour
  # is a fifth of D12's whole monthly ceiling, and the budget notifies nobody.
  #
  # Raising it is a diff on this line, in a module whose tag every caller pins, so widening the
  # ceiling is a reviewable event rather than a discovery.
  default = [
    "ml.t3.medium",
    "ml.t3.large",
    "ml.t3.xlarge",
    "ml.m5.large",
    "ml.m5.xlarge",
    "ml.c5.large",
    "ml.c5.xlarge",
  ]

  validation {
    condition     = length(var.allowed_instance_types) > 0
    error_message = "an empty allow-list denies every SageMaker call that names an instance type - say so deliberately, in the caller."
  }
}
