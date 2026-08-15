# tflint - Stage 2 step 6.4. Repository-wide config; the pre-commit hook points every slice at
# this one file, so a rule is enabled once rather than per slice.
#
# Run `tflint --init` once after installing tflint (and again when a version below changes):
# the rulesets are plugins and are downloaded on demand, not bundled with the binary.

config {
  call_module_type = "local"
}

plugin "terraform" {
  enabled = true
  preset  = "recommended"
}

# The AWS ruleset is the half that knows what an invalid instance type or a deprecated
# argument is. Pinned for the same reason the provider is (step 1): a linter that changes
# under a repository turns a clean commit into a failing one with no diff to explain it.
plugin "aws" {
  enabled = true
  version = "0.48.0"
  source  = "github.com/terraform-linters/tflint-ruleset-aws"
}
