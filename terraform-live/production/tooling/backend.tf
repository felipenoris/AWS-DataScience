# The backend - partial configuration (Stage 2 step 2.5), live from the first init.
#
#   ./scripts/gen-backend-hcl.py production tooling   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production tooling        (region, env, tag, zone_ids, account_folder,
#                                                      interactive_private_cidrs)
#   terraform init -backend-config=backend.hcl
#
# A [D] slice: applied by hand, like production/vpn/ and production/proxy/, and never by `make up`,
# which starts and stops its host by Name tag (refusal 5). The SAML inputs (step 3.2) are the one
# thing a person types into this directory, as `saml.auto.tfvars` - gitignored, since it carries
# the identity provider's URL and certificate - and the generated file is regenerated beside it.

terraform {
  backend "s3" {}
}
