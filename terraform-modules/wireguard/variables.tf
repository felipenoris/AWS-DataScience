# Inputs. NOTHING HERE IS AN ADDRESS THE MODULE CHOOSES: the VPC facts arrive from
# foundation/'s outputs through the caller's terraform_remote_state, the client range from the
# generated tfvars (scripts/tfhygiene/backend.py), and the keys from a git-ignored .tfvars the
# user writes. A literal in this file would be a copy of one of those three (Lesson 14).

variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here, including the awsds-<env>-vpn Name tag that scripts/slices.py and ./aws/vpn.py both find the host by. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "public_subnet_ids" {
  description = "foundation/'s public subnets BY ZONE ID. The host lands in one of them - it is the tunnel endpoint, so it needs an address the internet can reach."
  type        = map(string)
  nullable    = false
}

variable "zone_ids" {
  description = "The authored zone ids (scripts/tfhygiene/backend.py) - zone_index picks one."
  type        = list(string)
  nullable    = false
}

# WHY THIS KNOB EXISTS: t4g.nano capacity was MEASURED ABSENT in one of this region's zones
# during Stage 3 - Server.InsufficientInstanceCapacity, after 25 minutes of provider retry.
# That measurement was taken on the Graviton family this module carried until 2026-08-20, and
# the knob is kept for the x86_64 one rather than retired with it: what it defends against is a
# zone's pool being short of a size, which is not a property of an architecture, and the cost of
# keeping it is one variable nobody has to touch.
# (The region literal belongs in this comment and not in the description below: step 9.1's
# scan reads string VALUES and skips full-line comments, deliberately.)
variable "zone_index" {
  description = "Which authored zone the host lands in. Everything this host consumes is AZ-free - the Elastic IP, the security group, the internet gateway and the S3 gateway endpoint all belong to the VPC rather than to a zone - so moving it is a one-variable retry rather than a redesign. See the note above for what made that necessary."
  type        = number
  default     = 0

  validation {
    condition     = var.zone_index >= 0 && var.zone_index < length(var.zone_ids)
    error_message = "zone_index must be an index into zone_ids."
  }
}

variable "security_group_id" {
  description = "foundation/'s [P] WireGuard security group (step 2.2) - created there, not here, because Stage 7's GitLab rule admits it BY ID across an account boundary and a group a rebuild can replace is not worth referencing."
  type        = string
  nullable    = false
}

variable "eip_allocation_id" {
  description = "foundation/'s [P] Elastic IP allocation (step 2.1). Associated here and allocated there: after step 8.3 the address is what every persona permission set pins the whole AWS control plane to, so it must survive an instance replacement."
  type        = string
  nullable    = false
}

variable "peer_cidr" {
  description = "The client range, from the allocation table through the generated tfvars (step 4.2, Stage 3 decision 1). The host takes .1 of it. NOTHING INSIDE AWS EVER SEES THIS RANGE - the instance SNATs (see the user data) - so its one job is not colliding with a home or cafe LAN."
  type        = string
  nullable    = false

  validation {
    condition     = can(cidrhost(var.peer_cidr, 1))
    error_message = "peer_cidr must be a CIDR block."
  }
}

# ---------------------------------------------------------------------------- the keys
#
# BOTH SIDES OF EVERY KEY PAIR ARE GENERATED ON A LAPTOP AND NEVER BY TERRAFORM (steps 4.1,
# 4.3): a `tls_private_key` resource would put the key in state AND make it a thing Terraform
# rotates. What arrives here is the public half of each client (the caller's TRACKED roster)
# and - since the third design review (2026-08-16) - a POINTER to the host's private half:
# the [P] Secrets Manager secret the caller's foundation/ owns. The value itself never
# enters Terraform anywhere: the user writes it at enrollment, the instance reads it at
# first boot with its own role.

variable "peers" {
  description = "One entry per PERSON PER DEVICE, keyed by a name that reads in `wg show` output (e.g. \"felipe-laptop\"). Revoking a device is deleting one entry, which is the price D4 accepted when it turned down Identity Center integration - so the shape has to make that a one-line diff. A MAP AND NOT A LIST, deliberately: `host` is authored per peer rather than derived from position, so removing an entry cannot renumber everybody else's tunnel address and silently invalidate their client configs."
  type = map(object({
    public_key = string
    host       = number
  }))
  nullable = false

  validation {
    condition     = alltrue([for p in var.peers : p.host >= 2])
    error_message = "host must be 2 or greater - .1 of peer_cidr is the WireGuard server itself."
  }

  validation {
    condition     = length(distinct([for p in var.peers : p.host])) == length(var.peers)
    error_message = "two peers share a host number - each device needs its own address in peer_cidr."
  }

  validation {
    condition     = alltrue([for p in var.peers : can(regex("^[A-Za-z0-9+/]{43}=$", p.public_key))])
    error_message = "public_key must be a base64 WireGuard key (44 chars, ending in '='): `wg genkey | wg pubkey`."
  }
}

variable "host_key_secret_arn" {
  description = "The [P] Secrets Manager secret holding the SERVER's private key (step 2.2a; decision 4, third review) - the ARN alone, never the value. The key is in a secret rather than generated on first boot because every client config pins the server's PUBLIC key as well as its address: a key that lived only inside the instance would be destroyed by the next AMI drift or user-data edit and would break every client at once, silently - Lesson 4 in a [D] resource. And it is a POINTER rather than a key variable so that neither state nor user data carries the secret: the instance fetches the value at first boot with its own role (iam.tf grants GetSecretValue on exactly this ARN; the secret's resource policy admits nobody else but InfrastructureAccess). The consequence to know: a new VALUE changes nothing Terraform can see, so rotation is put-secret-value PLUS a deliberate -replace of the instance (the keys runbook, procedure C)."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:secretsmanager:", var.host_key_secret_arn))
    error_message = "host_key_secret_arn must be a Secrets Manager secret ARN (foundation/'s wireguard_host_key_secret_arn output)."
  }
}

# ------------------------------------------------------------------ shape and observability

variable "instance_type" {
  description = "D4's shape - the smallest burstable there is - on the ARCHITECTURE main.tf's AMI pins, x86_64 since 2026-08-20 (it was t4g.nano, arm64, from D4 until then). Measured at 0.0052 USD/h in this region, +23.8% on the Graviton shape it replaced (docs/PRICING.md 8, both rows read the same day; Lesson 6). A variable rather than a literal so a capacity or throughput finding is a one-line change - not an invitation to grow it. THE VALUE MUST MATCH THE IMAGE: this module validates nothing here, deliberately - a size list belongs with the caller that selects from it, and the caller's own validation is the closed list. What decides which family is admissible is the SSM parameter in main.tf and nothing else, so moving that line is what moves this default, in that order."
  type        = string
  default     = "t3.nano"
}

variable "mtu" {
  description = "The tunnel's MTU on the SERVER side, and it governs one direction only: the size of what this host injects into the tunnel, which is the DOWNLOAD direction for every client. Absent this line wg-quick derives it from the uplink - 9001 on an AWS ENA, so wg0 came up at 8921 (measured 2026-08-17), a value nobody chose and which no internet path carries. WHY 1280 AND NOT A LARGER 'CORRECT' VALUE: it is the IPv6 minimum and the same number the client template pins, so the two sides of the design say one thing. The reason this was left open at pass 2 - that a server value trades against every client's path at once, rather than one - only bites when the value chosen sits BETWEEN paths; the floor trades against nobody. WHAT IT DOES NOT FIX: the upload direction is still governed by the client's own MTU line, typed by hand per device, and closing that needs an MSS clamp in PostUp - deliberately not here, because a clamp is two rules whose directions are easy to get wrong by reading and which nothing in this repository would exercise (Lesson 20)."
  type        = number
  default     = 1280

  validation {
    # 1280 is the IPv6 minimum link MTU and the floor a WireGuard interface may carry; 8921 is
    # what the uplink offered. A value outside that band is a typo rather than a decision, and
    # the failure it would otherwise produce is the silent one: a tunnel that handshakes, passes
    # DNS, and stalls on anything large (docs/plan/runbooks/vpn.md section C4).
    condition     = var.mtu >= 1280 && var.mtu <= 8921
    error_message = "mtu must be between 1280 (the IPv6 minimum, and this design's choice) and 8921 (what an AWS ENA's 9001 leaves after WireGuard's 80 bytes)."
  }
}

variable "listen_port" {
  description = "The UDP port the tunnel listens on - and the ONLY world-open port in this estate (step 3.1). It must match the ingress rule of foundation/'s [P] security group, which is why it is a variable in both places and a literal in neither."
  type        = number
  default     = 51820
}

variable "log_retention_days" {
  description = "Retention of the handshake log group, 30 days - the same decision Stage 3 took for flow logs, for the same reason: a diagnostic, not an audit trail."
  type        = number
  default     = 30
}

variable "root_volume_size" {
  description = "GiB. The [D] idle cost of this host, ~USD 0.65/month at gp3 rates (docs/PRICING.md 3) - it goes on billing while the instance is stopped, which is the deal [D] makes."
  type        = number
  default     = 8
}
