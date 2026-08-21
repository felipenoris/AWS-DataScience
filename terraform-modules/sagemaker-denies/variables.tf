variable "allowed_instance_types" {
  description = "Every ml.* instance type any principal in this design may ask SageMaker for. D12's budget expressed as a control: the budget notifies nobody, so the only thing that stops a USD 30/hour parameter is a policy that refuses it in the first hour."
  type        = list(string)
  nullable    = false

  # THE CANONICAL LIST, AND THE ONE COPY OF IT. Both callers - the six persona sets in
  # terraform-live/identity/sso/ and the project boundary in sagemaker-prereqs - omit the
  # argument or pass null, which `nullable = false` resolves to this default. That is the
  # SECOND half of Lesson 33: the module already shares the structure, and a values list
  # written once at each end would have been exactly the divergence the module exists to
  # prevent.
  #
  # WHAT IS IN IT: the app sizes SMUS actually launches (ml.t3.medium is the JupyterLab and
  # Code Editor default, USD 0.050/h - docs/PRICING.md 8) plus a small general-purpose and
  # compute range for jobs. NO GPU AND NO *.2xlarge OR LARGER, deliberately: a single ml.p3
  # hour is a fifth of D12's whole monthly ceiling, and the budget notifies nobody.
  #
  # RAISING IT IS A DIFF ON THIS LINE, in a module whose tag every caller pins - which is the
  # property that makes "we widened the ceiling" a reviewable event rather than a discovery.
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
