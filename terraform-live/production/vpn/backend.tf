# The backend - partial configuration (Stage 2 step 2.5), live from the first init.
#
#   ./scripts/gen-backend-hcl.py production vpn   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py production vpn     (region, env, tag, zone_ids, account_folder,
#                                              peer_cidr, rfc1918_cidrs)
#   terraform init -backend-config=backend.hcl
#
# This slice is the only one with a hand-written tfvars. `peers.auto.tfvars` carries the client
# public keys and is tracked, so the roster is reviewable history; ./scripts/check-tfvars-shape.py
# holds it to public halves only. The server's private key is not an input: it lives in
# networking/'s [P] Secrets Manager secret, enrolled by the user and fetched by the instance at
# first boot (6c step 4.3; decision 4, third review). The `.auto.` is what loads the roster with no
# -var-file to forget. Shape and enrollment command in README.md beside this file.

terraform {
  backend "s3" {}
}
