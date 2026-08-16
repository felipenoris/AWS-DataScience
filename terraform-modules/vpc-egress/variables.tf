variable "env" {
  description = "The <env> NAME TOKEN (docs/plan/conventions.md) - builds every name here. Not the Environment tag, which the caller's provider default_tags applies."
  type        = string
  nullable    = false
}

variable "vpc_id" {
  description = "The foundation/ VPC - read by the caller through terraform_remote_state, never pasted (Lesson 3)."
  type        = string
  nullable    = false
}

variable "egress_mode" {
  description = "Step 10's switch, PER ACCOUNT (10.3): 'A' builds the NAT and the private tier's default route; 'B' builds neither - no default route at all until Stages 6-7 build B's package path. Default A (Stage 3 decision 4); choosing A as the default is not choosing A as the outcome - D5's comparison happens at Stage 6."
  type        = string
  default     = "A"

  validation {
    condition     = contains(["A", "B"], var.egress_mode)
    error_message = "egress_mode is 'A' (NAT) or 'B' (no default route) - D5's two designs, nothing else."
  }
}

variable "nat_public_subnet_id" {
  description = "The ONE public subnet the NAT lands in (step 7.1) - the caller picks the first authored zone. The documented one-per-AZ switch: make this a map like private_route_table_ids and give aws_route.private_default a per-zone NAT - foundation's route tables are already per AZ so it is a route change, not a re-plumbing."
  type        = string
  nullable    = false
}

variable "private_route_table_ids" {
  description = "foundation/'s private route tables, BY ZONE ID - under design A every one of them gets the default route toward the one NAT (steps 2.2, 7, 10). Read through terraform_remote_state."
  type        = map(string)
  nullable    = false
}

variable "endpoint_subnet_id" {
  description = "The ONE subnet every interface endpoint lands in - single AZ (D9, step 8.5): two AZs doubles the largest hourly line item, and a resource in the other AZ still resolves and reaches it. The caller picks the private subnet of the first authored zone."
  type        = string
  nullable    = false
}

variable "endpoint_security_group_id" {
  description = "foundation/'s endpoint SG (step 2.4) - TCP/443 from the VPC CIDR, attached to every interface endpoint here."
  type        = string
  nullable    = false
}

variable "core_services" {
  description = "Step 8.2's common core, in every account: identity, logging, keys, images, and the data-plane three - under design B a missing athena/glue means no query executes at all (D13). lakeformation is the least certain entry and is included at a cent an hour rather than discovered at Stage 6; verification (ii) decides whether it stays. Overridden never - the per-role differences go in extra_services."
  type        = list(string)
  default     = ["sts", "logs", "kms", "ecr.api", "ecr.dkr", "athena", "glue", "lakeformation"]
}

variable "extra_services" {
  description = "The per-account-role adds of step 8.3 - authored in each caller, because the list being DIFFERENT per role is the point: one list everywhere was wrong in both directions. Short service tokens ('sagemaker.api'); the region prefix is built here. Every entry is ~USD 0.010/h for the whole session."
  type        = list(string)
  default     = []
}
