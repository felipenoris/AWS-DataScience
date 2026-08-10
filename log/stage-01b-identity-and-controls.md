# Log — Stage 1b — Identity Center, permission sets, and the alarm above them

*Manual actions performed by the user. Written by the user, **never** by Claude.
Stage: [`plan/stages/stage-01b-identity-and-controls.md`](../plan/stages/stage-01b-identity-and-controls.md).*

---

- Started step 8.3

- Login as CT Admin SSO, AWSAdministratorAccess. CloudWatch -> Logs -> Log Management. Selected log group `aws-controltower/CloudTrailLogs-gcs-gsx`. At Metric filters -> Create metric filter. Used this pattern:

```
{ ($.eventSource = "sso-directory.amazonaws.com" && ($.eventName = "AddMemberToGroup" || $.eventName = "RemoveMemberFromGroup")) || ($.eventSource = "identitystore.amazonaws.com" && ($.eventName = "CreateGroupMembership" || $.eventName = "DeleteGroupMembership")) || ($.eventSource = "sso.amazonaws.com" && ($.eventName = "CreateAccountAssignment" || $.eventName = "DeleteAccountAssignment")) }
```

- Set filter name as `Identity Center membership and assignment changes`. Namespace (existing) `AWSDS/Security`. Metric name `IdentityCenterChangeCount`. Metric value 1.

- Selecting the metric -> Create Alarm. Metric name `IdentityCenterChangeCount`. Statistic `Sum`, 1 minute. Greater/Equal to 1. In alarm send a notification to `awsds-org-break-glass-alerts`. Alarm name `Identity Center membership and assignment change`. Alarm description `Identity Center membership and assignment change detected.`.

- Ended step 8.3. Starting step 1.

- From CloudShell console, using the real `IDENTITY_ACCOUNT_ID`:

```
aws organizations register-delegated-administrator --account-id <IDENTITY_ACCOUNT_ID> --service-principal sso.amazonaws.com
```

- Running `aws organizations list-delegated-administrators --service-principal sso.amazonaws.com` lists the identity account id successfuly.

- Received Break-Glass alert at this time.

- Ended step 1. Moving to step 2.

- Login as Infrastructure User -> Identity Account -> AWSAdministratorAccess. Checked region `us-west-2`.

- At IAM Identity Center. The current user list is `Infrastructure User` and `AWS Control Tower Admin`. Current groups are: AWSAuditAccountAdmins, AWSLogArchiveAdmins, AWSServiceCatalogAdmins, AWSSecurityAuditors, AWSLogArchiveViewers, AWSSecurityAuditPowerUsers, AWSControlTowerAdmins, AWSAccountFactory. Left untouched.

- Used this script in CloudShell to create groups, where d-xxxxxxxxxx is the IdentityStoreId returned by `aws sso-admin list-instances`, and `<EMAIL>` is the real email stored in secrets:

```
aws identitystore create-group --identity-store-id d-xxxxxxxxxx --display-name "sso-group-infrastructure" --description "who builds and changes the infrastructure"
aws identitystore create-group --identity-store-id d-xxxxxxxxxx --display-name "sso-group-data-scientists" --description "who uses the interactive environment"
aws identitystore create-group --identity-store-id d-xxxxxxxxxx --display-name "sso-group-deployment-managers" --description "who approves releases"
aws identitystore create-group --identity-store-id d-xxxxxxxxxx --display-name "sso-group-governance-managers" --description "manages users permissions to datasets"
aws identitystore create-group --identity-store-id d-xxxxxxxxxx --display-name "sso-group-dev-env-stewards" --description "is this runtime safe to hand to everyone? approves deployment of new dev-env."

aws identitystore create-user --identity-store-id d-xxxxxxxxxx --display-name "Data Scientist User" --name Formatted="Data Scientist User",FamilyName="User",GivenName="Data Scientist" --user-name "<EMAIL>" --emails Value="<EMAIL>"
aws identitystore create-user --identity-store-id d-xxxxxxxxxx --display-name "Dev Env Steward User" --name Formatted="Dev Env Steward User",FamilyName="User",GivenName="Dev Env Steward" --user-name "<EMAIL>" --emails Value="<EMAIL>"
aws identitystore create-user --identity-store-id d-xxxxxxxxxx --display-name "Deployment Manager User" --name Formatted="Deployment Manager User",FamilyName="User",GivenName="Deployment Manager" --user-name "<EMAIL>" --emails Value="<EMAIL>"
aws identitystore create-user --identity-store-id d-xxxxxxxxxx --display-name "Governance Manager User" --name Formatted="Governance Manager User",FamilyName="User",GivenName="Governance Manager" --user-name "<EMAIL>" --emails Value="<EMAIL>"
```

- Associated manually:
	- Dev Env Steward User -> sso-group-dev-env-stewards
	- Deployment Manager User -> sso-group-deployment-managers
	- Data Scientist User -> sso-group-data-scientists
	- Governance Manager User -> sso-group-governance-managers

- Received Alarm (Identity Center membership and assignment change).
---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
