# development/egress/ - the [E] metered network of Development (Stage 3 pass 3): the NAT
# under design A, step 8's Development endpoint list, step 9's org policy on every entry.
# Lifecycle belongs to `make up ENV=development` / `make down ENV=development` (D11), never
# to a by-hand apply (runbook, "What you never do"); `./aws/egress.py` 6 is the burn meter.
#
# foundation/'s [P] facts arrive through terraform_remote_state - never pasted (Lesson 3).

data "terraform_remote_state" "foundation" {
  backend = "s3"

  config = {
    bucket = "awsds-${var.env}-tfstate"
    key    = "${var.account_folder}/foundation/terraform.tfstate"
    region = var.region
  }
}

module "egress" {
  # checkov:skip=CKV_TF_1:pinned by git TAG by convention (conventions §6, Stage 3 step 1.1a) - a repository-internal tag only the repo owner can move
  source = "git::git@github.com:felipenoris/AWS-DataScience.git//terraform-modules/vpc-egress?ref=vpc-egress-v0.2.0"

  env    = var.env
  vpc_id = data.terraform_remote_state.foundation.outputs.vpc_id

  # Stage 3 decision 4: A is the DEFAULT, per account (10.3) - D5's comparison is Stage 6's.
  egress_mode = "A"

  # Single-AZ resources land in the FIRST authored zone (D9) - a selection, not an anchor.
  nat_public_subnet_id       = data.terraform_remote_state.foundation.outputs.public_subnet_ids[var.zone_ids[0]]
  private_route_table_ids    = data.terraform_remote_state.foundation.outputs.private_route_table_ids
  endpoint_subnet_id         = data.terraform_remote_state.foundation.outputs.private_subnet_ids[var.zone_ids[0]]
  endpoint_security_group_id = data.terraform_remote_state.foundation.outputs.endpoints_security_group_id

  # Step 8.3, the Development row: the three SageMaker endpoints - the same list as Sandbox
  # since 2026-08-17, when the NFS requirement was withdrawn (D24 with it).
  # `datazone` JOINED THE LIST AT STAGE 6 STEP 4.2 (2026-08-21): the SMUS network-isolation
  # page marks it REQUIRED under VpcOnly, so an app cannot reach the domain without it. It is
  # the ONLY entry added from that page on faith. The rest of the required table
  # (docs/SMUS.md §VpcOnly is the one copy - fifteen names) is added by MEASUREMENT and not by
  # copying: verification (viii) reads the flow logs of a working session and only what is
  # exercised gets an endpoint, at +USD 0.010/h each, per account, for the whole session.
  #
  # TWO ENTRIES OF THAT TABLE CANNOT BE SETTLED BY ADDING THEM HERE, and both are recorded so
  # nobody "fixes" them:
  #   s3   this account already has a [P] GATEWAY endpoint whose prefix-list route is more
  #        specific than any default, so S3 traffic may never reach an interface endpoint at
  #        all - and the request then presents the GATEWAY's aws:SourceVpce. Which one wins,
  #        per project subnet, is verification (xix), and flow logs are the wrong instrument
  #        (gateway traffic crosses no ENI): the field is CloudTrail's vpcEndpointId.
  #   q    the doc pairs it with com.amazonaws.US-EAST-1.codewhisperer, and an interface
  #        endpoint is regional - so under design B the Amazon Q surface has no private path
  #        from us-west-2 at all. Record what breaks at 4.3 rather than assuming either way.
  extra_services = ["sagemaker.api", "sagemaker.runtime", "sagemaker.studio", "datazone"]

  # DESIGN A's CONTROL (Stage 6 step 4.1) - the allow-list that makes the NAT "limited
  # internet" instead of internet. The LIST is not here: it lives once, in the module's
  # dns_firewall_allow_domains default, so the two Interactive accounts cannot drift and so
  # the instruction about what must stay OFF it is written where somebody adding a name will
  # read it (Lesson 33). The module refuses to enable itself under egress_mode = "B", where a
  # name filter would be a control over a route that does not exist.
  dns_firewall = true

  # DELIBERATELY ABSENT, and this is the record that makes it a control rather than an
  # oversight (Lesson 5; Stage 6 decision 3, 2026-08-19): Athena Spark's three session
  # endpoints - athena.sessions (Spark Connect), athena.dashboard (Live UI) and
  # athena.persistent-dashboard (History Server). Athena Spark runs its executors OUTSIDE
  # this VPC - there is no NetworkConfiguration in its API - so a notebook on it sits
  # outside these endpoints, the flow logs and every aws:SourceVpce condition. The
  # preventive half is the SCP deny on athena:StartSession/UpdateSession (Stage 6 step 1.6);
  # not creating these is the free network half, and it is a CHOICE since the 2026-04
  # PrivateLink release, not a property of the service.
  #
  # THE SQL PATH IS UNAFFECTED and must stay that way: Athena SQL rides the `athena` API
  # endpoint (the module's core list), which is what D13 depends on. Three names in the
  # same family, two different products.
  #
  # Revision trigger: Athena Spark gaining executors in OUR subnets under OUR security
  # group - never a headline saying it "supports VPC", which is about the control path.

}
