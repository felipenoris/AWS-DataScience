# sandbox/vpn/ - THE REPOSITORY'S FIRST [D] SLICE (Stage 4 pass 1). One module call, and the
# reason it is its own slice rather than three resources in foundation/ is the layer: `make
# down` stops what is here and destroys nothing, while foundation/ is never touched at all.
#
# WHAT IT NEEDS THAT IS ALREADY THERE, all of it [P] and all of it read rather than pasted:
# the public subnet, the internet gateway behind it, the [P] Elastic IP, the [P] security
# group and the [P] host-key secret of step 2, and - the two that decide the first boot -
# foundation/'s S3 GATEWAY endpoint with Stage 3's 9.3 allow-list on it (the packages), and
# the secret's VALUE, enrolled by the user before the apply (step 4.3 - the boot's fetch
# waits politely, saying so, until it exists). Nothing here waits for egress/, which is why
# `vpn` ranks 40 and egress 50: the tunnel is the first thing up and the last thing down, the
# order that becomes load-bearing the moment step 8.3 makes every API call exit through this
# host's address.
#
# THE MODULE ARRIVES BY GIT TAG, NEVER BY BRANCH (conventions §6; Stage 3 step 1.1a), and the
# tag is cut BETWEEN two commits - the validate hook inits from origin, so a module and its
# first caller cannot share one (Stage 3 pass 1's log entry).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

module "wireguard" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/wireguard?ref=wireguard-v0.2.0"

  env        = var.env
  zone_ids   = var.zone_ids
  zone_index = var.zone_index
  peer_cidr  = var.peer_cidr

  # THE SIZE IS A PARAMETER, NOT A CONSTANT - the one knob this slice adds to the module,
  # and the reason it is a variable rather than the literal it briefly was: the host is
  # SWITCHED between a forwarding-only nano and a t4g.medium with room to work in, by whoever
  # runs the apply, without touching a .tf file either way. THE SELECTION LIVES IN A TRACKED
  # TFVARS: instance_type.auto.tfvars beside this file - assigned there to switch up,
  # COMMENTED OUT to fall back to variables.tf's default (t4g.nano, D4's). Auto-loaded, so
  # both directions are a plain `terraform apply`. variables.tf carries the default and the
  # closed-list validation; the procedure - what to read before, what the plan must say, what
  # survives the stop/start - is docs/plan/runbooks/vpn.md section S6.
  #
  # WHY EVERY ALLOWED VALUE IS t4g: THE AMI DECIDES THE FAMILY, NOT THE SIZE. The module
  # pins the AL2023 ARM64 image (/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-
  # default-arm64), and an AMI is specific to its processor architecture - so t3.medium is
  # not a same-shape alternative to t4g.medium, it is a machine this image cannot run on,
  # and EC2 REFUSES the request rather than producing a broken host (documented, not
  # measured here: the EC2 resize-compatibility page, docs/REFERENCES.md). Moving to x86
  # would be an AMI change in the MODULE - a different SSM parameter, a replaced instance,
  # user data re-run - never a value of this variable.
  instance_type = var.instance_type

  public_subnet_ids = data.terraform_remote_state.foundation.outputs.public_subnet_ids
  security_group_id = data.terraform_remote_state.foundation.outputs.wireguard_security_group_id
  eip_allocation_id = data.terraform_remote_state.foundation.outputs.wireguard_eip_allocation_id

  # The POINTER, never the key (decision 4, third review): the module grants its instance
  # role GetSecretValue on exactly this ARN and the host fetches the value at first boot.
  host_key_secret_arn = data.terraform_remote_state.foundation.outputs.wireguard_host_key_secret_arn

  peers = var.peers
}
