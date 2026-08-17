# Log — Stage 1a — Landing zone, accounts and OUs

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-01a-landing-zone.md`](../plan/stages/stage-01a-landing-zone.md).*

---

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

- Created a `Workloads` OU under `Root`.

- Created `Production Account` under `Workloads` OU with IAM SSO user `Infrastructure User`.

- I checked that `Infrastructure User` now has access to `Development Account`, `Sandbox Account 1` and `Production Account`.

- Created `Data` OU under `Root`.

- Created `Data Governance Account` under `Data` OU with IAM SSO user `Infrastructure User`.

- Created `Policy Test` OU under `Root`.

- Created `Policy Canary Account` under `Policy Test` OU with IAM SSO user `Infrastructure User`.

- Couldn't create `Identity Account` under `Security` OU. Looks like it's blocked by AWS, maybe because it is foundational. I created a `Identity` OU. Created `Identity Account` under `Identity` OU.

- Now to the break-glass. Logged with root account. On CloudWatch I can see a log group called `aws-controltower/CloudTrailLogs-gcs-gsx`.

- Moving to `CloudTrail` -> Trails with the root account, I can see `aws-controltower-BaselineCloudTrail` with Multi-region trail set to `Yes`. Organization trail set to `Yes`. The console does not show the `Global service events` parameter. To check the parameter I used the following command line on `CloudShell`: `aws cloudtrail get-trail --name aws-controltower-BaselineCloudTrail`. It returned `IncludeGlobalServiceEvents: true`. From this, I conclude that Global service events is set to `Yes`.

- Moving to `SNS` with the root account. Create topic -> Topic name = `awsds-org-break-glass-alerts` -> Next step. Type = `Standard`. Name = `AWS Break Glass Alert`. Topic is now saved.

	- On SNS topic `awsds-org-break-glass-alerts` -> create subscription. Protocol = `Email`. Endpoint set to the break-glass email. Added new subscription with Protocol = `SMS`, added the break-glass phone number, which was confirmed via SMS. After creating EMAIL subscription, clicked on "Request confirmation" for the email subscription. I noticed that the AWS email with confirmation code was caught in my spam email filter. Solved this in my email app. Clicked the link within the email and the subscription was confirmed.

	- The plan says: "Do not reuse the two Control Tower topics". But the topic list has only one item, which is the one that I created manually (`awsds-org-break-glass-alerts`).

- Moving to `CloudWatch` with the root account -> Logs -> Log Management -> `aws-controltower/CloudTrailLogs-gcs-gsx` -> Metric filters -> Create metric filter. Filter pattern set to `{ $.userIdentity.type = "Root" && $.userIdentity.invokedBy NOT EXISTS && $.eventType != "AwsServiceEvent" }`. Filter name set to `awsds-org-root-activity`. Metric namespace set to `AWSDS/Security`. Metric name set to `RootActivityCount`. Metric value set to `1`.

- Moving to `CloudWatch` with the root account -> Alarms -> Create. Selected `RootActivityCount`, classic, Sum 1 minute, static, Greater/Equal to 1. Additional configuration -> Missing data treatment -> Treat missing data as good (not breaching threshold). In alarm -> Select an existing SNS topic -> send a notification to `awsds-org-break-glass-alerts`. Alarm name set to `AWS Break Glass Alert`, with description `A root account login was detected.`.

- Testing the break-glass: logged out. Logged in with root account. Did nothing (no actions). Logged out. The alarm was received successfully, on both SMS and Email.

- Logged as AWS Control Tower Admin → AWSAdministratorAccess → IAM → root access management → Enable. Enabled `Root credentials management` and `Privileged root actions in member accounts`. Left `Delegated administrator` empty. Clicked `Enable`. Em seguida, retornou sucesso com a seguinte mensagem `Root access management enabled. You can now delete root user credentials for member accounts from the Root access management page.`.

- Running command `aws iam list-organizations-features` on CloudShell, in the same session, returns `RootSessions` and `RootCredentialsManagement` as `EnabledFeatures`.

- Running command `aws organizations list-aws-service-access-for-organization`, the result includes `iam.amazonaws.com` at `EnabledServicePrincipals`.

- Next step is 6.4. `Take privileged action` is not active on the management account. I checked the following accounts and "Take privileged action" does not list `Delete root credentials` option. This means that none of these accounts have existing root credentials. For every account, the option `Allow password recovery` appears. So I guess I'll all set.
	- Development Account
	- Audit Account
	- Data Governance Account
	- Log Archive Account
	- Policy Canary Account
	- Production Account
	- Sandbox Account 1
	- Identity Account

- **2026-08-15 — the cap has not moved, first authoritative reading.** CloudShell on
  Management as `AWS Control Tower Admin`, `aws/cloudshell/management-quotas.sh`
  (single-file upload): applied value **10.0** = default, **10 accounts** in the
  organization — the cap fully spent, EXC-01's suspended account among the 10. The
  increase request is visible in Service Quotas itself: `CASE_OPENED`, desired **15**,
  created 2026-08-08, still in flight. No policy-size quota published for
  `organizations` (re-confirms 1c 7.0 step 5). The run also exposed and fixed the
  script's Region defect: these quotas answer only in us-east-1 —
  NoSuchResourceException elsewhere — matching how the ticket had to be raised.
  Report at `aws/output/cloudshell/management-quotas.txt`.

- No user has `Delegated administrator for centralized root access`.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
