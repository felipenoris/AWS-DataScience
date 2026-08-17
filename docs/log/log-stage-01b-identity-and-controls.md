# Log — Stage 1b — Identity Center, permission sets, and the alarm above them

*Manual actions performed in AWS, by hand. Written cooperatively by the user and Claude — **Claude
only when the user asks, never on its own initiative** ([`INDEX.md`](INDEX.md), which also carries the
provenance rule). **An entry carrying no provenance note of its own is the user's.**
Stage: [`docs/plan/stages/stage-01b-identity-and-controls.md`](../plan/stages/stage-01b-identity-and-controls.md).*

*One mechanical substitution was made on **2026-08-17**, by Claude at the user's request, and is named
here rather than at each line: **account ids → the account's name**, in the outputs pasted below — this
repository keeps no account id in a tracked file ([`aws/INDEX.md`](../../aws/INDEX.md) rule 1) and an ARN
carries one. Nothing else was edited: the `AWSReservedSSO_*` suffixes, the permission-set and landing-zone
ids and the wording arrived as they read.*

---

- Started step 8.3

- Login as CT Admin SSO, AWSAdministratorAccess. CloudWatch -> Logs -> Log Management. Selected log group `aws-controltower/CloudTrailLogs-gcs-gsx`. At Metric filters -> Create metric filter. Used this pattern:

```
{ ($.eventSource = "sso-directory.amazonaws.com" && ($.eventName = "AddMemberToGroup" || $.eventName = "RemoveMemberFromGroup")) || ($.eventSource = "identitystore.amazonaws.com" && ($.eventName = "CreateGroupMembership" || $.eventName = "DeleteGroupMembership")) || ($.eventSource = "sso.amazonaws.com" && ($.eventName = "CreateAccountAssignment" || $.eventName = "DeleteAccountAssignment")) }
```

- Set filter name as `Identity Center membership and assignment changes`. Namespace (existing) `AWSDS/Security`. Metric name `IdentityCenterChangeCount`. Metric value 1.

- Selecting the metric -> Create Alarm. Metric name `IdentityCenterChangeCount`. Statistic `Sum`, 1 minute, missing data notBreaching. Greater/Equal to 1. In alarm send a notification to `awsds-org-break-glass-alerts`. Alarm name `Identity Center membership and assignment change`. Alarm description `Identity Center membership and assignment change detected.`.

- Ended step 8.3. Starting step 1.

- This step registers Identity Account as delegated administrator for AWS IAM Identity Center service (sso.amazonaws.com). From CloudShell console, using the real `IDENTITY_ACCOUNT_ID`:

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

- Added Infrastructure user to sso-group-infrastructure. Alarm received successfuly.

- Login as Infrastructure User -> Identity Account -> AWSAdministratorAccess. Checked region `us-west-2`. IAM Center -> Settings -> Configura multi-factor authentication. Set `Every time they sign in` and `Require them to register an MFA device at sign in`.

- Testing alarm thru identitystore. Running on CloudShell, replacing d-xxxxxxxxxx with my IAM Center ID.

```
IDS=d-xxxxxxxxxx

GID=$(aws identitystore get-group-id \
    --identity-store-id $IDS \
    --alternate-identifier '{"UniqueAttribute":{"AttributePath":"displayName","AttributeValue":"sso-group-data-scientists"}}' \
    --query GroupId \
    --output text)


USERID=$(aws identitystore get-user-id \
    --identity-store-id $IDS \
    --alternate-identifier '{"UniqueAttribute":{"AttributePath":"userName","AttributeValue":"<USER_NAME>"}}' \
    --query UserId \
    --output text)


MID=$(aws identitystore get-group-membership-id --identity-store-id $IDS --group-id $GID --member-id UserId=$USERID --query MembershipId --output text)

aws identitystore delete-group-membership --identity-store-id $IDS --membership-id $MID
aws identitystore create-group-membership --identity-store-id $IDS --group-id $GID --member-id UserId=$USERID

aws identitystore list-group-memberships --identity-store-id $IDS --group-id $GID
```

- Alarm received successfuly and the user returned to the sso-group-data-scientists group.

- Ended step 2. Moving to Step 3.

- Login as Infrastructure User -> Identity Account -> AWSAdministratorAccess.

- Executed on CloudShell:

```
# IAM ARN and IdentityStoreID
INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text)
IDS=$(aws sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text)
echo "$INST / $IDS"

# creates InfrastructureAccess and attaches AdministratorAccess policy
PS=$(aws sso-admin create-permission-set --instance-arn "$INST" --name InfrastructureAccess --description "The builder: the identity terraform apply runs as" --session-duration PT4H --tags Key=Project,Value=AWS-DataScience Key=Environment,Value=org Key=ManagedBy,Value=terraform Key=CostCenter,Value=stage-01b Key=Owner,Value=sso-group-infrastructure --query 'PermissionSet.PermissionSetArn' --output text) && echo "$PS"
aws sso-admin attach-managed-policy-to-permission-set --instance-arn "$INST" --permission-set-arn "$PS" --managed-policy-arn arn:aws:iam::aws:policy/AdministratorAccess
```

- Group attribution on each account:

```
GID=$(aws identitystore get-group-id --identity-store-id "$IDS" --alternate-identifier '{"UniqueAttribute":{"AttributePath":"displayName","AttributeValue":"sso-group-infrastructure"}}' --query GroupId --output text) && echo "$GID"
for ACCT in $SANDBOX_ID $DEV_ID $DATA_GOVERNANCE_ID $PRODUCTION_ID $IDENTITY_ID; do aws sso-admin create-account-assignment --instance-arn "$INST" --target-id "$ACCT" --target-type AWS_ACCOUNT --permission-set-arn "$PS" --principal-type GROUP --principal-id "$GID"; done
```

- Checking

```
IDS=$(aws sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text)
INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text) # SSO ARN

GID=$(aws identitystore get-group-id \
  --identity-store-id "$IDS" \
  --alternate-identifier '{"UniqueAttribute":{"AttributePath":"displayName","AttributeValue":"sso-group-infrastructure"}}' \
  --query GroupId \
  --output text)

echo "Group ID: $GID"

aws sso-admin list-account-assignments-for-principal \
  --instance-arn "$INST" \
  --principal-id "$GID" \
  --principal-type GROUP \
  --output table
```


```
# Lists account assignments for group sso-group-infrastructure

SSO_GROUP_NAME=sso-group-infrastructure

INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text)
IDS=$(aws sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text)

ALTERNATE_ID=$(printf '{"UniqueAttribute":{"AttributePath":"displayName","AttributeValue":"%s"}}' "$SSO_GROUP_NAME")

GID=$(aws identitystore get-group-id \
  --identity-store-id "$IDS" \
  --alternate-identifier "$ALTERNATE_ID" \
  --query GroupId \
  --output text)

echo "Group ID: $GID"
echo ""
printf "%-20s %-30s %-40s %s\n" "AccountId" "AccountName" "PermissionSetName" "PermissionSetArn"
printf "%-20s %-30s %-40s %s\n" "---------" "-----------" "-----------------" "----------------"

aws sso-admin list-account-assignments-for-principal \
  --instance-arn "$INST" \
  --principal-id "$GID" \
  --principal-type GROUP \
  --query 'AccountAssignments[*].[AccountId,PermissionSetArn]' \
  --output text | while read ACCOUNT_ID PS_ARN; do

    ACCOUNT_NAME=$(aws organizations describe-account \
      --account-id "$ACCOUNT_ID" \
      --query 'Account.Name' \
      --output text)

    PS_NAME=$(aws sso-admin describe-permission-set \
      --instance-arn "$INST" \
      --permission-set-arn "$PS_ARN" \
      --query 'PermissionSet.Name' \
      --output text)

    printf "%-20s %-30s %-40s %s\n" "$ACCOUNT_ID" "$ACCOUNT_NAME" "$PS_NAME" "$PS_ARN"
done

# Result (Account IDs replaced by xxx)
#xxx         Development Account            InfrastructureAccess                     arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
#xxx         Data Governance Account        InfrastructureAccess                     arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
#xxx         Identity Account               InfrastructureAccess                     arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
#xxx         Sandbox Account 1              InfrastructureAccess                     arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
#xxx         Production Account             InfrastructureAccess                     arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
```

- Lists all permission set ARNs. AWSAdministratorAccess is the CT's permission set.

```
# lista o ARC de todos os Permission Sets:
for P in $(aws sso-admin list-permission-sets --instance-arn "$INST" --query 'PermissionSets[]' --output text); do echo "$(aws sso-admin describe-permission-set --instance-arn "$INST" --permission-set-arn "$P" --query 'PermissionSet.Name' --output text)  $P"; done

# Resultado
#AWSOrganizationsFullAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-79074d475a5b7b17
#AWSReadOnlyAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-79073b13c3d8a6cb
#InfrastructureAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-06c47afa33c0cad1
#AWSServiceCatalogAdminFullAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-7907a92899eacb91
#AWSAdministratorAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-7907c2179ed46d33
#AWSServiceCatalogEndUserAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-79072402f29fffac
#AWSPowerUserAccess  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-790755fafece7807
```

- At IAM Identity Center -> Permission Sets, I checked that `InfrastructureAccess` was created with AWS managed policy `AdministratorAccess`, session duration of 4H.
    - Tags:
        - Project=AWS-DataScience
        - Environment=org
        - ManagedBy=terraform
        - CostCenter=stage-01b
        - Owner=sso-group-infrastructure

    - Accounts:
        - Production Account
        - Development Account
        - Data Governance Account
        - Identity Account
        - Sandbox Account 1

    - On `Policy Canary`, Infrastructure User has "PrincipalId": "5851a330-90b1-70c6-730e-c607d8c87eb8".
    - Staging was skipped, not yet vended.

- checking 8.3 (ix):

```
aws cloudwatch describe-alarm-history --alarm-name "Identity Center membership and assignment change" --history-item-type StateUpdate --max-records 10 --query 'AlarmHistoryItems[].[Timestamp,HistorySummary]' --output text
2026-08-11T01:25:00.628000+00:00        Alarm updated from ALARM to OK
2026-08-11T01:18:00.628000+00:00        Alarm updated from OK to ALARM
2026-08-10T06:42:00.627000+00:00        Alarm updated from ALARM to OK
2026-08-10T06:34:00.627000+00:00        Alarm updated from OK to ALARM
2026-08-10T06:13:00.632000+00:00        Alarm updated from INSUFFICIENT_DATA to OK
2026-08-10T05:56:10.425000+00:00        Alarm updated from ALARM to INSUFFICIENT_DATA
2026-08-10T05:50:10.423000+00:00        Alarm updated from INSUFFICIENT_DATA to ALARM
2026-08-10T05:38:10.423000+00:00        Alarm updated from ALARM to INSUFFICIENT_DATA
2026-08-10T05:30:10.423000+00:00        Alarm updated from INSUFFICIENT_DATA to ALARM
```

- Verification (ix) — answered. Alarm history (Management, us-west-2):
    - 2026-08-10 05:30-05:56 UTC — step 2, flapping through INSUFFICIENT_DATA (before the fix)
    - 2026-08-10 06:13 UTC — missing-data treatment fix takes effect (INSUFFICIENT_DATA -> OK)
    - 2026-08-10 06:34-06:42 UTC — the `identitystore` membership test: OK -> ALARM -> OK
    - 2026-08-11 01:18-01:25 UTC — step 3's five `create-account-assignment` calls: one single
      OK -> ALARM -> OK transition for five events, as 8.3 predicted
  **The finding:** step 3 ran from the *Identity* account and the alarm, which lives in
  *Management*, fired. So Identity Center events still land in Management's org-trail log group
  after the step 1 delegation. The fallback 8.3 held in reserve — a second filter in Identity
  pointing cross-account at the same topic — is not needed.
  Event sources confirmed by own evidence: `identitystore.amazonaws.com` and
  `sso.amazonaws.com`. **`sso-directory.amazonaws.com` (the console path) was never exercised** —
  everything so far was done by CLI. Untested, not broken.

- Verification (i) (landing zone): `sso.amazonaws.com` as a delegated administrator (step 1) does not raise
  Control Tower drift on landing zone version 4.0 :

```
LZ=$(aws controltower list-landing-zones --query 'landingZones[0].arn' --output text) && echo "$LZ" && aws controltower get-landing-zone --landing-zone-identifier "$LZ" --query 'landingZone.[version,status,driftStatus,latestAvailableVersion]'
arn:aws:controltower:us-west-2:<Management Account>:landingzone/4I3ACTXON4Q7CJ8H
[
    "4.0",
    "ACTIVE",
    {
        "status": "IN_SYNC"
    },
    "4.0"
]
```

- Checking Canary:

```
INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text); for P in $(aws sso-admin list-permission-sets --instance-arn "$INST" --query 'PermissionSets[]' --output text); do aws sso-admin list-account-assignments --instance-arn "$INST" --account-id "$POLICY_CANARY_ID" --permission-set-arn "$P" --query "AccountAssignments[?PrincipalId=='5851a330-90b1-70c6-730e-c607d8c87eb8'].[PrincipalType,PrincipalId]" --output text | sed "s|^|$(aws sso-admin describe-permission-set --instance-arn "$INST" --permission-set-arn "$P" --query 'PermissionSet.Name' --output text)\t|"; done
```

results in:
```
AWSAdministratorAccess  USER    5851a330-90b1-70c6-730e-c607d8c87eb8
```

which shows PrincipalType = USER (direct assignment), CT's permission set AWSAdministratorAccess, and no line about InfrastructureAccess.

- Ended step 3. Moving to step 4.

- Starting Step 4. Checking if any persona reaches Management.

```
MGMT_ID=xxx # management account ID
INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text); for P in $(aws sso-admin list-permission-sets-provisioned-to-account --instance-arn "$INST" --account-id "$MGMT_ID" --query 'PermissionSets[]' --output text); do echo "== $(aws sso-admin describe-permission-set --instance-arn "$INST" --permission-set-arn "$P" --query 'PermissionSet.Name' --output text)"; aws sso-admin list-account-assignments --instance-arn "$INST" --account-id "$MGMT_ID" --permission-set-arn "$P" --output table; done
```

Result:

```
== AWSServiceCatalogEndUserAccess
---------------------------------------------------------------------------------------------------
|                                     ListAccountAssignments                                      |
+-------------------------------------------------------------------------------------------------+
||                                      AccountAssignments                                       ||
|+------------------+----------------------------------------------------------------------------+|
||  AccountId       |  xxx                                                              ||
||  PermissionSetArn|  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-79072402f29fffac   ||
||  PrincipalId     |  f8d16390-20f1-7094-b767-bc4b6f8be26d                                      ||
||  PrincipalType   |  GROUP                                                                     ||
|+------------------+----------------------------------------------------------------------------+|
== AWSServiceCatalogAdminFullAccess
---------------------------------------------------------------------------------------------------
|                                     ListAccountAssignments                                      |
+-------------------------------------------------------------------------------------------------+
||                                      AccountAssignments                                       ||
|+------------------+----------------------------------------------------------------------------+|
||  AccountId       |  xxx                                                              ||
||  PermissionSetArn|  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-7907a92899eacb91   ||
||  PrincipalId     |  7801e3c0-b091-7095-068a-692ab619c7c2                                      ||
||  PrincipalType   |  GROUP                                                                     ||
|+------------------+----------------------------------------------------------------------------+|
== AWSAdministratorAccess
---------------------------------------------------------------------------------------------------
|                                     ListAccountAssignments                                      |
+-------------------------------------------------------------------------------------------------+
||                                      AccountAssignments                                       ||
|+------------------+----------------------------------------------------------------------------+|
||  AccountId       |  xxx                                                              ||
||  PermissionSetArn|  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-7907c2179ed46d33   ||
||  PrincipalId     |  d8e1b360-f021-705d-ba51-7cd5b28b17d9                                      ||
||  PrincipalType   |  GROUP                                                                     ||
|+------------------+----------------------------------------------------------------------------+|
== AWSPowerUserAccess
---------------------------------------------------------------------------------------------------
|                                     ListAccountAssignments                                      |
+-------------------------------------------------------------------------------------------------+
||                                      AccountAssignments                                       ||
|+------------------+----------------------------------------------------------------------------+|
||  AccountId       |  xxx                                                              ||
||  PermissionSetArn|  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-790755fafece7807   ||
||  PrincipalId     |  c88113e0-e001-7081-2318-a37dd98d5a6f                                      ||
||  PrincipalType   |  GROUP                                                                     ||
|+------------------+----------------------------------------------------------------------------+|
== AWSReadOnlyAccess
---------------------------------------------------------------------------------------------------
|                                     ListAccountAssignments                                      |
+-------------------------------------------------------------------------------------------------+
||                                      AccountAssignments                                       ||
|+------------------+----------------------------------------------------------------------------+|
||  AccountId       |  xxx                                                              ||
||  PermissionSetArn|  arn:aws:sso:::permissionSet/ssoins-79076fdc3a54ee96/ps-79073b13c3d8a6cb   ||
||  PrincipalId     |  78b1a3b0-0071-7096-37c4-abe4d1ec3796                                      ||
||  PrincipalType   |  GROUP                                                                     ||
|+------------------+----------------------------------------------------------------------------+|
```

Listing groups:

```
INST=$(aws sso-admin list-instances --query 'Instances[0].InstanceArn' --output text); IDS=$(aws sso-admin list-instances --query 'Instances[0].IdentityStoreId' --output text); for P in $(aws sso-admin list-permission-sets-provisioned-to-account --instance-arn "$INST" --account-id "$MGMT_ID" --query 'PermissionSets[]' --output text); do PSN=$(aws sso-admin describe-permission-set --instance-arn "$INST" --permission-set-arn "$P" --query 'PermissionSet.Name' --output text); aws sso-admin list-account-assignments --instance-arn "$INST" --account-id "$MGMT_ID" --permission-set-arn "$P" --query 'AccountAssignments[].[PrincipalType,PrincipalId]' --output text | while read T PID; do if [ "$T" = "GROUP" ]; then N=$(aws identitystore describe-group --identity-store-id "$IDS" --group-id "$PID" --query DisplayName --output text); else N=$(aws identitystore describe-user --identity-store-id "$IDS" --user-id "$PID" --query DisplayName --output text); fi; printf "%-40s %-6s %s\n" "$PSN" "$T" "$N"; done; done
```

results in:

```
AWSServiceCatalogEndUserAccess           GROUP  AWSAccountFactory
AWSServiceCatalogAdminFullAccess         GROUP  AWSServiceCatalogAdmins
AWSAdministratorAccess                   GROUP  AWSControlTowerAdmins
AWSPowerUserAccess                       GROUP  AWSSecurityAuditPowerUsers
AWSReadOnlyAccess                        GROUP  AWSSecurityAuditors
```

```
for G in AWSControlTowerAdmins AWSServiceCatalogAdmins AWSAccountFactory AWSSecurityAuditors AWSSecurityAuditPowerUsers; do GID=$(aws identitystore get-group-id --identity-store-id "$IDS" --alternate-identifier "{\"UniqueAttribute\":{\"AttributePath\":\"displayName\",\"AttributeValue\":\"$G\"}}" --query GroupId --output text); echo "== $G"; aws identitystore list-group-memberships --identity-store-id "$IDS" --group-id "$GID" --query 'GroupMemberships[].MemberId.UserId' --output text | tr '\t' '\n' | while read U; do [ -n "$U" ] && aws identitystore describe-user --identity-store-id "$IDS" --user-id "$U" --query DisplayName --output text; done; done
```

results in :

```
== AWSControlTowerAdmins
AWS Control Tower Admin
== AWSServiceCatalogAdmins
== AWSAccountFactory
AWS Control Tower Admin
== AWSSecurityAuditors
== AWSSecurityAuditPowerUsers
```

- Verification (a) — answered. Two layers, because the assignment list alone does not close the Management
  account:
    - **Assignment path:** five permission sets provisioned to Management, five Control Tower groups behind
      them, no `sso-group-*` and no `PrincipalType USER`. No project persona holds an assignment there, the
      infrastructure user included — which is what `docs/ORGANIZATION.md` records as permanent.
    - **Membership path:** the only human reaching Management is `AWS Control Tower Admin`, through
      `AWSControlTowerAdmins` (administrator) and `AWSAccountFactory` (Service Catalog end user). Those are
      the two Control Tower groups it arrived with (D33/D34), and it is in no project group.
      `AWSSecurityAuditPowerUsers` — `AWSPowerUserAccess` on *every* account — and `AWSSecurityAuditors` are
      **empty**.
  **The caveat is the point of the step:** those two empty groups are state, not a control. Nothing prevents
  a membership being added, and step 4 closes the *assignment* path into Management while leaving the
  *membership* path open by construction. The 8.3 alarm is what observes it — which is why it was built
  before step 1 rather than beside it.

- Verification (ii) — answered for the assignment path, by probe. Deleting an assignment that does not
  exist, so the write path is exercised against Management with nothing to lose either way:

```
aws sso-admin delete-account-assignment --instance-arn "$INST" --target-id "$MGMT_ID" \
  --target-type AWS_ACCOUNT --permission-set-arn "$PS" --principal-type GROUP --principal-id "$GID"

An error occurred (AccessDeniedException) when calling the DeleteAccountAssignment operation:
User: arn:aws:sts::<IDENTITY_ID>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_<id>/<infrastructure user>
is not authorized to perform: sso:DeleteAccountAssignment
on resource: arn:aws:sso:::account/<MGMT_ID> with an explicit deny in a resource-based policy
```

  Three things it shows beyond the yes/no:
    - **The deny is explicit and lives in a resource-based policy**, not in what the principal was granted.
      The call was made by a principal holding `AdministratorAccess` *in the account that administers the
      directory* and was denied anyway — so the restriction cannot be lifted from inside Identity by editing
      an identity policy. Lesson 18 seen from the side that works: the delegated administrator does not
      author the policy that contains it.
    - **It is scoped by target account** (`arn:aws:sso:::account/<MGMT_ID>`), which is the shape step 4
      describes.
    - **Reads are not restricted.** Everything under (a) above was run from Identity, as the delegated
      administrator, and returned. So the boundary is manage-vs-read, not visibility.
  **What the probe does not answer:** whether Management-targeted assignments are the *only* thing the
  delegated administrator cannot manage. One operation was exercised. Registering/deregistering a delegated
  administrator and the instance-level operations are expected to stay with Management too, so the honest
  answer is **"no, not the only thing"**, and (ii) is recorded here as answered **for the assignment path**,
  pending a documentation check for the rest.

- **The identity that executed steps 2, 3 and 4** is the infrastructure user through Control Tower's
  `AWSReservedSSO_AWSAdministratorAccess_*` — the Account Factory direct assignment (D32), which the stage's
  "Who executes what" table names as the bootstrap of the whole stage. Consequence worth stating before
  step 5: **`sso-group-infrastructure` → `InfrastructureAccess` → an account is still unexercised.**
  Everything proven about that path so far is a listing of assignments, never an `sts:GetCallerIdentity`
  under it. Step 5 is where it turns into evidence, and that evidence is 5.1's precondition.

- Back to step 3, still owed — the tag check on the permission set. The console listing showed four tags
  and the create call sent five:

```
aws sso-admin list-tags-for-resource --instance-arn "$INST" --resource-arn "$PS"
```

  `Owner=sso-group-infrastructure`: present. This set is the first and only resource in the project
  carrying `Owner`, and `docs/plan/conventions.md` settled the value as an `sso-group-*` — never a user — on
  2026-08-10.

- Ended step 4. Moving to step 5.

- Configuring sso access with aws cli:

```
aws configure sso-session
```

session name: awsds
Start URL: https://[my-url].awsapps.com/start
SSO region: us-west-2
SSO registration scopes: left default value

- Logoff console from browser.

- Configuring Development profile:

    - `aws configure sso --profile awsds-infra-dev`
    - session name awsds
    - will open browser to login. used Infrastructure User sso.
    - selected Development Account
    - selected InfrastructureAccess
    - selected region us-west-2
    - selected output json

- repeated same steps for profiles:
    - awsds-infra-sandbox-1 (Sandbox account)
    - awsds-infra-prod (Production account)
    - awsds-infra-data (Data account)
    - awsds-infra-identity (Identity account)

- awsds-policy-canary profile configured with AWSAdministratorAccess.

- verifying:

```
for P in awsds-infra-sandbox-1 awsds-infra-dev awsds-infra-prod awsds-infra-data awsds-infra-identity awsds-policy-canary; do printf '%-24s ' "$P"; aws sts get-caller-identity --profile "$P" --query Arn --output text 2>&1; done
```

yields:

```
awsds-infra-sandbox-1: arn:aws:sts::<Sandbox Account 1>:assumed-role/AWSReservedSSO_InfrastructureAccess_59e5b26af457128d
awsds-infra-dev: arn:aws:sts::<Development Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_7edd72025c361e9b
awsds-infra-prod: arn:aws:sts::<Production Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_c2bcabf74c885115
awsds-infra-data: arn:aws:sts::<Data Governance Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_ba1899ccb658ab35
awsds-infra-identity: arn:aws:sts::<Identity Account>:assumed-role/AWSReservedSSO_InfrastructureAccess_a6d31eda0e5de20c
awsds-policy-canary: arn:aws:sts::<Policy Canary Account>:assumed-role/AWSReservedSSO_AWSAdministratorAccess_59a09ed7d34a9cd1
```

- Checking:

```
aws sso-admin list-instances --profile awsds-infra-identity
```

yields:

```
{
    "Instances": [
        {
            "InstanceArn": "arn:aws:sso:::instance/ssoins-79076fdc3a54ee96",
            "IdentityStoreId": "d-9267c9ef91",
            "OwnerAccountId": "xxxx",
            "Name": "yyyy",
            "CreatedDate": "2026-08-01T18:30:39.407000-03:00",
            "Status": "ACTIVE",
            "PrimaryRegion": "us-west-2",
            "Regions": [
                {
                    "RegionName": "us-west-2",
                    "Status": "ACTIVE",
                    "AddedDate": "2026-08-01T18:30:39.407000-03:00",
                    "IsPrimaryRegion": true
                }
            ]
        }
    ]
}
```

- Created the `aws/` script folder (`aws/list-identities.sh`) and ran it for the first time with the
  `awsds-infra-identity` profile. Read-only; writes `aws/output/list-identities.txt`, not versioned.
  Every call returned — the report's "calls that failed" section came back empty.

- What that first run settles, beyond the listings themselves:

  - **Step 3's owed tag check is answered.** `list-tags-for-resource` on the `InfrastructureAccess`
    permission set returns all five tags sent at creation: `Project`, `Environment=org`,
    `Owner=sso-group-infrastructure`, `ManagedBy=terraform`, `CostCenter=stage-01b`. The console listing
    that showed four was a console artifact, not a missing tag.

  - **Step 4's "reads are not restricted" now covers the read surface, not one probe.** From the delegated
    administrator, with no `AccessDenied` anywhere: `organizations` describe-organization, list-roots,
    list-organizational-units-for-parent, list-accounts-for-parent, list-accounts; `sso-admin`
    list-instances, list-permission-sets, describe-permission-set, list-managed-policies-in-permission-set,
    list-customer-managed-policy-references-in-permission-set, get-permissions-boundary-for-permission-set,
    get-inline-policy-for-permission-set, list-tags-for-resource,
    list-accounts-for-provisioned-permission-set, list-account-assignments; `identitystore` list-groups,
    list-users, list-group-memberships. **Including the assignments that target the Management account** —
    the one thing step 4 proved cannot be *changed* from here. The boundary is manage-vs-read, and it is
    now measured on both sides.

  - **Only `SERVICE_CONTROL_POLICY` is `ENABLED` on the organization root.** `RESOURCE_CONTROL_POLICY`,
    `TAG_POLICY` and `DECLARATIVE_POLICY_EC2` are absent, exactly as Stage 1c step 7.2 assumes. That
    assumption is now measured instead of inherited from documentation.

- Observed on the same run and unrelated to this stage: an account named `Sandbox`, `SUSPENDED`, attached
  directly to the organization root. Left over from an earlier experiment of mine, nothing to do with this
  project. Recorded as `EXC-01` in `docs/AWS_STATE.md` and ignored from here on.

- Ended step 5 (header). Starting step 5.1.

- First, cleaning aws/cli/cache:

```
rm -f ~/.aws/cli/cache/*.json
```

- listing cache files, returns session.db and no JSON files.

```
$ ls ~/.aws/cli/cache
session.db
```

- running:

```
for P in awsds-infra-sandbox-1 awsds-infra-dev awsds-infra-prod awsds-infra-data awsds-infra-identity; do printf '%-24s ' "$P"; aws sts get-caller-identity --profile "$P" --query Arn --output text 2>&1; done
```

- All five returned `AWSReservedSSO_InfrastructureAccess_*`.

- running:

```
for P in awsds-infra-sandbox-1 awsds-infra-dev awsds-infra-prod awsds-infra-data awsds-infra-identity; do printf '%-24s ' "$P"; aws iam get-role --role-name AWSControlTowerExecution --profile "$P" --query 'Role.AssumeRolePolicyDocument.Statement[0].Principal.AWS' --output text 2>&1; done
```

- All five returned `arn:aws:iam::*:root`

- Login AWS Console using Infrastructure SSO user, account Identity, AWSAdministratorAccess.

- IAM Identity Center -> AWS Accounts. Selected the `Data Governance Account`. On Users and Groups, selected `AWSAdministratorAccess` , `User` associated with sso user `Infrastructure User`. Selected `Remove access`. It errors with Access Denied. After debugging, it was found that The delegated administrator can't alter permission sets provisioned in the management account" (IAM Identity Center User Guide, "Delegated administration").

- Login AWS Console using sso user `AWS Control Tower Admin` -> AWSAdministratorAccess, on management account.

- IAM Identity Center -> AWS Accounts. Selected the `Data Governance Account`. On Users and Groups, selected `AWSAdministratorAccess` , `User` associated with sso user `Infrastructure User`. Selected `Remove access`. It worked. Repeated the same for accounts: Identity Account, Sandbox Account 1, Development Account, Production Account.

- I left Policy Canary Account untouched. It remains with direct SSO Infrastructure User attribution with Permission Set AWSAdministratorAccess.

- executed cleaning aws/cli/cache:

```
rm -f ~/.aws/cli/cache/*.json
```

- Verification: re-checked all six profiles after the removals, from a cleared cache:

```
for P in awsds-infra-sandbox-1 awsds-infra-dev awsds-infra-prod awsds-infra-data awsds-infra-identity awsds-policy-canary; do printf '%-24s ' "$P"; aws sts get-caller-identity --profile "$P" --query Arn --output text; done
```

  The five `awsds-infra-*` returned `AWSReservedSSO_InfrastructureAccess_*` and `awsds-policy-canary`
  returned `AWSReservedSSO_AWSAdministratorAccess_*` — the same ARNs as before 5.1. So the group path
  carries every account with no direct assignment standing behind it.

- Ordering, stated because it differed from the step: `Identity` was removed second rather than last.
  The step puts it last so the bootstrap is the last thing withdrawn; executing from Management made that
  moot — the session was in an account not being touched, and all five profiles had already returned
  `InfrastructureAccess` before the first removal. Recorded so the sequence is not read back as the
  planned one.

- Re-ran `./aws/list-identities.sh`. `AWSAdministratorAccess` now has exactly one USER assignment in the
  whole organization, on `Policy Canary`, and the report shows no `(provisioned, no assignment)` rows —
  the five removals deprovisioned the set cleanly rather than leaving an orphaned role behind.

- Verification (vi) — **opened, not answered.** The removals took effect on 2026-08-12 and had not been
  re-created as of that date. Whether they stick is only observable at the next landing-zone update,
  account update or Account Factory re-enrollment. Re-run `./aws/list-identities.sh` after the first of
  those and answer (vi) then; D32 is amended only if they come back.

- Ended step 5.1. Moving to step 6.

- Ran under each profile, `us-west-2`:

```
    aws ec2 describe-availability-zones \
      --query 'AvailabilityZones[].[ZoneName,ZoneId,ZoneType,State]'
```

-All six accounts return the **same** mapping. All four zones `available`, all `availability-zone` (no Local Zones offered):

```
| Zone name | Zone ID |
|---|---|
| `us-west-2a` | `usw2-az2` |
| `us-west-2b` | `usw2-az1` |
| `us-west-2c` | `usw2-az3` |
| `us-west-2d` | `usw2-az4` |
```

- Accounts checked: `Sandbox Account 1`, `Development`, `Production` (the three the step names — the three that get a VPC), plus `Data Governance`, `Identity` and `Policy Canary`, which the step does not require and which get no VPC. They were checked anyway, at the cost of two read-only calls, to see whether the shuffle is per-account or org-wide. Note the names are **not** in ID order: `a` is `az2`, `b` is `az1`.

- `Staging` is not checked — not yet vended. Its check is owed at the vend, with the rest of what Stage 1a's deferral leaves owed.

- **Outcome: Stage 3 anchors subnets on `zone_id`, not on list position** — even though nothing diverges today. The measurement can only speak for the accounts that exist, and D35 plus Stage 14 mean the account set grows; a mismatch in a future account produces no error, only cross-AZ charges on the D14/D21 peerings. `docs/plan/open-questions.md` item 3 closes on this.

- Ended step 6. Moving to 8.2

- Login as `AWS Control Tower Admin` -> AWSAdministratorAccess on management account.

- Listing current state for trusted access services Using CloudShell:

```
$ aws organizations list-aws-service-access-for-organization --query 'EnabledServicePrincipals[].ServicePrincipal' --output table
-------------------------------------------------------
|         ListAWSServiceAccessForOrganization         |
+-----------------------------------------------------+
|  cloudtrail.amazonaws.com                           |
|  config.amazonaws.com                               |
|  controltower.amazonaws.com                         |
|  iam.amazonaws.com                                  |
|  member.org.stacksets.cloudformation.amazonaws.com  |
|  sso.amazonaws.com                                  |
+-----------------------------------------------------+
```

- IAM -> Access Analyser -> Create Analyser. Selected `Resource analysis - External access` for `Current organization`.

- Repeated on CloudShell. See that `access-analyzer.amazonaws.com` was added to the list.

```
$ aws organizations list-aws-service-access-for-organization --query 'EnabledServicePrincipals[].ServicePrincipal' --output table
-------------------------------------------------------
|         ListAWSServiceAccessForOrganization         |
+-----------------------------------------------------+
|  access-analyzer.amazonaws.com                      |
|  cloudtrail.amazonaws.com                           |
|  config.amazonaws.com                               |
|  controltower.amazonaws.com                         |
|  iam.amazonaws.com                                  |
|  member.org.stacksets.cloudformation.amazonaws.com  |
|  sso.amazonaws.com                                  |
+-----------------------------------------------------+
```

- Analyser settings -> Add delegated administrator. Added `Audit Account` ID.

- Checking delegated admins:

```
$ aws organizations list-delegated-administrators --service-principal access-analyzer.amazonaws.com --query 'DelegatedAdministrators[].[Name,Id,Status]' --output table
---------------------------------------------
|        ListDelegatedAdministrators        |
+----------------+----------------+---------+
|  Audit Account |  xxxxxx  |  ACTIVE |
+----------------+----------------+---------+
```

- Note: `enable-aws-service-access` was never called explicitly. Used the console's Create-analyzer.

- The Analysed should have been created inside the Audit account. So I deleted the analyser in the Management account.

- Login as `AWS Control Tower Admin` -> AWSAdministratorAccess on Audit account.

- Executed on cloudshell:

```
aws accessanalyzer create-analyzer --region us-west-2 --analyzer-name awsds-org-external-access --type ORGANIZATION --tags Project=AWS-DataScience,Environment=org,ManagedBy=console,Owner=sso-group-infrastructure,CostCenter=stage-01b

{
    "arn": "arn:aws:access-analyzer:us-west-2:<Audit Account>:analyzer/awsds-org-external-access"
}
```

- listing analyser:

```
$ aws accessanalyzer get-analyzer --region us-west-2 --analyzer-name awsds-org-external-access --query 'analyzer.[name,type,status,createdAt]' --output table
-------------------------------
|         GetAnalyzer         |
+-----------------------------+
|  awsds-org-external-access  |
|  ORGANIZATION               |
|  ACTIVE                     |
|  2026-08-12T03:38:38+00:00  |
+-----------------------------+
```

- **2026-08-15 — first authoritative read of the organization analyzer** (CloudShell inside
  Audit, as `AWS Control Tower Admin`, via `aws/cloudshell/audit-iam-analyser.sh`, single-file
  upload). CHECK OK: one analyzer, `awsds-org-external-access`, ORGANIZATION, ACTIVE, five
  project tags, no archive rules; scan current. 35 ExternalAccess findings, all
  `AWSReservedSSO_*` permission-set roles trusting the directory's SAML provider — the
  assignment table restated, recorded as INV-16 in `docs/AWS_STATE.md`. Report stored at
  `aws/output/cloudshell/audit-iam-analyser.txt`.

- Ended step 8.2. Stage 1b complete.

---

*Log index: [docs/log/INDEX.md](INDEX.md) · Stage index: [docs/plan/stages/INDEX.md](../plan/stages/INDEX.md)*
