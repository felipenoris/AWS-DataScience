# apply-application.tf - Stage 8 step 4.1's grant, the deploy role's inline apply-application: the leg's
# read of the account's egress slice before it deploys (Stage 8 decision 27, scripts/check-egress.py),
# the two calls below with the slice's state among the role's state_read_keys.
#
# The statements one account adds are apply_application_in_this_account's: deploy-role.tf's in
# Staging, deploy-anchors.tf's in Production.
#
# The same file in staging/foundation/ and production/foundation/, byte for byte
# (./scripts/check-copies.py).
data "aws_iam_policy_document" "apply_application" {
  source_policy_documents = [data.aws_iam_policy_document.apply_application_in_this_account.json]

  # Stage 8 steps 3.1 and 3.6 (decision 27): the leg reads the account's egress slice before it writes,
  # and raises nothing. DescribeVpcEndpoints takes no resource; the association is read by its id.
  statement {
    sid       = "DescribeTheEgressEndpoints"
    effect    = "Allow"
    actions   = ["ec2:DescribeVpcEndpoints"]
    resources = ["*"]
  }

  statement {
    sid       = "ReadTheDnsFirewallAssociation"
    effect    = "Allow"
    actions   = ["route53resolver:GetFirewallRuleGroupAssociation"]
    resources = ["arn:${local.partition}:route53resolver:${local.region_account}:firewall-rule-group-association/*"]
  }
}
