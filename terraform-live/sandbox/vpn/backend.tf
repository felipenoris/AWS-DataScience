# The backend - partial configuration (Stage 2 step 2.5), live from the first init.
#
#   ./scripts/gen-backend-hcl.py sandbox vpn   (writes the untracked backend.hcl)
#   ./scripts/gen-tfvars.py sandbox vpn        (region, env, tag, zone_ids, account_folder, peer_cidr)
#   terraform init -backend-config=backend.hcl
#
# THE ONE HAND-WRITTEN TFVARS - what makes this slice different from every other one on
# disk. `peers.auto.tfvars` carries the client PUBLIC keys and is TRACKED (the roster is
# reviewable history; ./scripts/check-tfvars-shape.py holds it to public halves only). The
# SERVER'S PRIVATE KEY is deliberately not an input: it lives in foundation/'s [P] Secrets
# Manager secret, enrolled by the user and fetched by the instance at first boot (steps 4.1,
# 4.3; decision 4, third review). The `.auto.` is what loads the roster with no -var-file to
# forget. Shape and enrollment command in README.md beside this file.

terraform {
  backend "s3" {}
}
