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

- 

---

*Log index: [log/INDEX.md](INDEX.md) · Stage index: [plan/stages/INDEX.md](../plan/stages/INDEX.md)*
