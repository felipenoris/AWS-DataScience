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

# THE ISOLATED TIER'S ADDRESS RANGES, READ FROM THE SUBNETS THEMSELVES (2026-08-21, with the
# buildbox). foundation/ exports subnet IDs and not their CIDRs, and the right repair is this
# data source rather than a new output: a CIDR is a property of the subnet, `aws_subnet`
# already reports it, and adding an output would be a second place for the same fact to live
# (Lesson 14). Writing the range as a literal here would be a third - a copy of the allocation
# table in scripts/tfhygiene/backend.py that nothing keeps in step.
data "aws_subnet" "isolated" {
  for_each = data.terraform_remote_state.foundation.outputs.isolated_subnet_ids

  id = each.value
}

module "wireguard" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/wireguard?ref=wireguard-v0.4.0"

  env        = var.env
  zone_ids   = var.zone_ids
  zone_index = var.zone_index
  peer_cidr  = var.peer_cidr

  # THE SIZE IS A PARAMETER, NOT A CONSTANT - the first of the two knobs this slice adds to
  # the module (the disk below is the second), and the reason it is a variable rather than the
  # literal it briefly was: the host is SWITCHED between a forwarding-only nano and a
  # t3.medium with room to work in, by whoever runs the apply, without touching a .tf file
  # either way. THE SELECTION LIVES IN A TRACKED
  # TFVARS: instance_type.auto.tfvars beside this file - assigned there to switch up,
  # COMMENTED OUT to fall back to variables.tf's default (t3.nano, D4's shape). Auto-loaded,
  # so both directions are a plain `terraform apply`. variables.tf carries the default and the
  # closed-list validation; the procedure - what to read before, what the plan must say, what
  # survives the stop/start - is docs/plan/runbooks/vpn.md section S6.
  #
  # WHY EVERY ALLOWED VALUE IS t3: THE AMI DECIDES THE FAMILY, NOT THE SIZE. The module
  # pins the AL2023 X86_64 image (/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-
  # default-x86_64), and an AMI is specific to its processor architecture - so t4g.medium is
  # not a same-shape alternative to t3.medium, it is a machine this image cannot run on,
  # and EC2 REFUSES the request rather than producing a broken host (documented, not
  # measured here: the EC2 resize-compatibility page, docs/REFERENCES.md).
  #
  # AND THAT IS PRECISELY HOW THE ARCHITECTURE ITSELF WAS MOVED, on 2026-08-20 (user
  # direction): the values here were t4g.nano / t4g.micro / t4g.medium on the arm64 image
  # from D4 until that day, and going to x86 was an AMI change IN THE MODULE - a different
  # SSM parameter, wireguard-v0.3.0, a REPLACED instance and a re-run of the user data -
  # exactly as this paragraph said it would have to be, and never a value of this variable.
  # Going back would be the same act in reverse, at the same price.
  instance_type = var.instance_type

  # AND THE DISK, THE SAME WAY AND FROM THE SAME FILE - a second variable rather than the
  # module's default because that default (8 GiB) is sized for a host that only forwards, and
  # a host somebody works on has to hold something. WHAT MAKES THIS KNOB DIFFERENT FROM THE ONE
  # ABOVE, and it is worth reading before assigning rather than after: instance_type goes both
  # ways, root_volume_size does not. EBS grows a volume IN PLACE - the provider issues
  # ModifyVolume and the instance is not even stopped - but EBS CANNOT SHRINK ONE, so
  # commenting the assignment out does not return the disk the way it returns the type; it
  # asks for a shrink EBS refuses. Down is a host REPLACEMENT (Part K), never an apply. Two
  # consequences of the same asymmetry: the growth reaches the OS only at BOOT, when
  # cloud-init's growpart runs, and the volume bills while the host is STOPPED. Both, with the
  # readings that settle them, are docs/plan/runbooks/vpn.md section S6.
  root_volume_size = var.root_volume_size

  public_subnet_ids = data.terraform_remote_state.foundation.outputs.public_subnet_ids
  security_group_id = data.terraform_remote_state.foundation.outputs.wireguard_security_group_id
  eip_allocation_id = data.terraform_remote_state.foundation.outputs.wireguard_eip_allocation_id

  # The POINTER, never the key (decision 4, third review): the module grants its instance
  # role GetSecretValue on exactly this ARN and the host fetches the value at first boot.
  host_key_secret_arn = data.terraform_remote_state.foundation.outputs.wireguard_host_key_secret_arn

  # THE HOST BECOMES A NAT INSTANCE FOR THE ISOLATED TIER - added 2026-08-21, and it is the
  # smaller half of a two-part arrangement whose other half lives in an [E] slice.
  #
  # WHAT THIS LINE DOES: one MASQUERADE and two FORWARD rules per range in wg0's PostUp, and
  # source/destination checking OFF on this ENI (the module's own comment carries the argument
  # and now carries the exception too). WHAT IT DOES NOT DO: send anything here. A masquerade
  # rule matches only traffic that was ROUTED to this host, and the route that does it -
  # 0.0.0.0/0 in the isolated route table, pointed at this instance's ENI - is created and
  # destroyed by terraform-live/sandbox/buildbox/, which is [E]. So the capability stands with
  # the [D] host and the reach comes and goes with the session.
  #
  # WHY THE ISOLATED TIER AND NOT THE PRIVATE ONE: the private tier's default route belongs to
  # egress/ under egress_mode=A, and two slices writing 0.0.0.0/0 into one route table is a
  # collision rather than a design. The isolated tier has no default route by construction,
  # which is exactly the property that leaves room for one.
  #
  # WHY IT IS A LIST AND NOT THE VPC CIDR: `-s <vpc_cidr>` would also match this host's own
  # traffic, since the host is in that VPC - harmless, and still a rule that says more than it
  # means. The subnets that can actually be routed here are the ones named.
  vpc_nat_cidrs = [for s in data.aws_subnet.isolated : s.cidr_block]

  peers = var.peers
}
