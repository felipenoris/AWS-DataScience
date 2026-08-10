# AWS CLI

Use CloudShell at AWS Console.

## Lists accounts with IDs

Login as `AWS Control Tower Admin User`.

```
aws organizations list-accounts --query 'Accounts[].[Name,Id]' --output table
```
## Lists Identity Store ID (SSO)

```
aws sso-admin list-instances
```

## Busca alertas:

Métrics:

```
aws cloudwatch get-metric-statistics --namespace AWSDS/Security --metric-name IdentityCenterChangeCount --start-time "$(date -u -d '-6 hours' +%Y-%m-%dT%H:%M:%SZ)" --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --period 300 --statistics Sum
```

Alarm:

```
aws cloudwatch describe-alarm-history --alarm-name "Identity Center membership and assignment change" --history-item-type StateUpdate --max-records 10 --query 'AlarmHistoryItems[].[Timestamp,HistorySummary]' --output text
```