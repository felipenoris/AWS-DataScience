
# Log of activities

## Stage 0 — Baseline

- Management Account created manually at https://aws.amazon.com/. Root account has MFA enabled.

- Installed aws client from: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html.

- Installed terraform from: https://developer.hashicorp.com/terraform/install

## Stage 1a — Landing zone, accounts and OUs

- Opened support ticker to increase "Maximum number of accounts" to **15**. This is global setting, but must be requested selecting "us-east-1" region (N. Virginia). Issue can be tracked at <https://us-east-1.console.aws.amazon.com/servicequotas/home/requests?region=us-east-1>.

- I checked again my root account MFA. All set.

- At Budgets -> Create a budget. Set a monthly limit of USD 50.

- Enabled Control Tower with `us-west-2` as the home region.

- Added `Security OU`.

- Selected `Security OU` as the Default OU for service integrations.

- Enabled AWS Config. Created an `Audit Account` as "Aggregator Account" associated with AWS Config.

- Skipped AWS Backup configuration.

- Created `Interactive` OU.

- Set AWS Access Portal (setting for IAM Identity Center). URL registered at `secrets/emails.md` (see Portal IAM Identity Center).

- I noted that after setting up Control Tower, a IAM SSO user "AWS Control Tower Admin" was set with my root account email. This user is assigned to the following groups: "AWSAccountFactory" and "AWSControlTowerAdmins". This user has access to all accounts.

- Logged as "AWS Control Tower Admin" at AWS Access Portal.
	- set MFA for this IAM Identity Center user.
	- Accessed "AWSAdministratorAccess" under the root account.
	- Account Factory -> create account.
	- Added `Development Account` with IAM SSO user `Infrastructure User` under `Interactive` OU.

- Received email asking the infrastructure SSO user to accept invite. Setup password and MFA for Infrastructure user. When logging into access portal, I can see it has access to Development Account -> AWSAdministratorAccess. Looks like a full access to this account.

- Registered a new OU called `Sandboxes` under `Root` -> `Interactive`. This OU will be used to group all sandbox accounts.

- Created new account `Sandbox Account 1` under `Sandboxes` with IAM SSO user `Infrastructure User`. Now I can see that in the IAM Identity Center there's only one `Infrastructure User` with two accounts listed: `Development Account` and `Sandbox Account 1`.
