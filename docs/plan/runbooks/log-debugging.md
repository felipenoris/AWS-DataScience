# Reading the estate's logs — a debugging runbook

*Written 2026-09-09 from the commands the implementation sittings actually used — Stages 4, 5, 6a, 6c and
6d — rather than from what the APIs offer. Every format below was read off a live record on the day this
was written; every trap cost a measurement, and carries the date it cost one.*

**The rule this file exists for: pick the log from the question, never the question from the log.** Five
logs answer five different things, and the one that looks closest to the symptom is often the one that
cannot see it. The recurring shape of a real diagnosis here is **two logs that do not share a failure
mode** ([Lesson 24](../lessons.md)) — one says *which name was asked for*, the other says *which door the
call took*, and only the pair rules out the failure that succeeds.

---

## 1. The map — what exists, where, and what it answers

Measured 2026-09-09 with `aws logs describe-log-groups` in both accounts. **Retention is in the row
because it bounds every "this has never happened" claim below.**

| log group | account · profile | written by | answers |
|---|---|---|---|
| `/awsds/prod/proxy` **365 d** | Production · `awsds-infra-prod` | Squid, `production/networking` | which **name** a client asked the proxy for, whether it was allowed, and how many bytes came back |
| `/awsds/<env>/dns-firewall` **30 d** | the compute account · `awsds-infra-<env>` | Route 53 Resolver query logging, `vpc-egress` | which **name** was *resolved* in a VPC, by which source, and whether the firewall blocked it |
| `awsds-<env>-vpc-flow-logs` **30 d** | per account · same | the `vpc` module (`[P]` — always on) | ACCEPT/REJECT per flow: **addresses and ports, never names** |
| `/awsds/prod/vpn` **30 d** | Production · `awsds-infra-prod` | the WireGuard host | the tunnel host's own output |
| `/awsds/<env>/studio` **30 d** | the compute account · same | `sagemaker-prereqs` | Studio app output |
| CloudTrail — no group; the `lookup-events` **API** | every account · any profile that can read it | the organization trail | which **principal** made which API call, and **by which door** |

**Three families this estate did not create and does not control**, found in the same reading and worth
knowing before one is mistaken for ours:

- `datazone-<id>-dev` — one per DataZone project, service-created. **Their retention is whatever the
  service felt like**: measured 3, 30 and **731** days in one account on one day. Nobody chose those
  numbers ([Lesson 17](../lessons.md)), and 731 days is a cost line nobody priced.
- `/aws/sagemaker/studio` and `/aws/mwaa-serverless/dzd-<domain>-<project>/<workflow>` — AWS's own,
  retention `None` (**never expires**). The MWAA one carries the task's traceback; **§W** is why it is the
  second instrument and not the first.
- `/aws/lambda/aws-controltower-NotificationForwarder` — Control Tower's.

**`[E]` matters here.** The proxy and VPN groups are `[P]` and survive a teardown; what *writes* to them
does not. A silent group is usually a stopped host, not a broken pipeline — §2.2 is how you tell.

---

## 2. The three commands, and the one idiom

### 2.1 `filter-log-events` — the workhorse

```bash
aws logs filter-log-events --log-group-name /awsds/prod/proxy \
  --start-time <epoch-ms> [--end-time <epoch-ms>] \
  [--filter-pattern "<substring>"] \
  --profile awsds-infra-prod --region us-west-2 --output json
```

- **`--start-time` is epoch MILLISECONDS.** A date string is silently useless.
- `--filter-pattern "foo"` on an unstructured group is a **substring** match on the message. Leave it out
  to take the whole window.
- **Omit `--start-time` entirely to search the group's whole life.** That is the reading that turns *"I
  have not seen it"* into *"it has never happened"* — bounded by the group's **creation date**, which is
  usually more recent than its retention. Say which bound you used.

### 2.2 `describe-log-streams` — when a group looks empty

```bash
aws logs describe-log-streams --log-group-name /awsds/prod/proxy \
  --order-by LastEventTime --descending --max-items 5 \
  --profile awsds-infra-prod --region us-west-2 \
  --query 'logStreams[].{stream:logStreamName,last:lastEventTimestamp}'
```

`lastEventTimestamp` per stream, in epoch ms, tells you *when the writer last spoke* — which separates
"my window is wrong" from "the writer is stopped". One stream per instance (`i-…/access` for Squid), so
a host replacement shows up as a **new stream** and the old one simply stops.

> **`storedBytes` reads `0` while streams are live** (measured 2026-09-08). The field lags by hours. A
> listing of streams is the reading; `storedBytes` is not.

### 2.3 `cloudtrail lookup-events` — who, and by which door

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventSource,AttributeValue=datazone.amazonaws.com \
  --start-time 2026-09-09T22:44:00Z --end-time 2026-09-09T23:50:00Z \
  --profile awsds-infra-sandbox-1 --region us-west-2
```

- `AttributeKey` is one of `EventSource`, `EventName`, `Username`, `ResourceName`, … — **one attribute
  per call**, they do not combine.
- **`--start-time` here takes an ISO timestamp, not milliseconds.** The two APIs disagree; this is the
  single most common wasted call.
- **Management events only, and 90 days.** `GetObject` and the other data events are not here — they are
  [Stage 11](../stages/stage-11-dlp.md)'s to enable.
- The payload is `CloudTrailEvent`, **a JSON string inside the JSON** — parse it. The fields that earn
  their keep: `sourceIPAddress`, `vpcEndpointId`, `userIdentity.arn`, `userAgent`, `errorCode`,
  `requestParameters`.

### 2.4 The idiom: build the window in the shell, and never pipe a command whose exit code matters

```bash
START=$(python3 -c "import time; print(int((time.time()-3600)*1000))")
```

Redirect to a file, then parse the file. A pipeline hands you the *pipe's* exit code, not the command's
([Lesson 46](../lessons.md)), and a truncated JSON read as "no events" is a false negative that looks
exactly like a finding.

---

## 3. §P — The proxy access log: which name, and was it allowed

**The format is declared, not guessed** — `logformat awsds` in
[`squid.conf.tftpl`](../../../terraform-live/production/proxy/squid.conf.tftpl):

```
%{%Y-%m-%dT%H:%M:%S%z}tl  %>a   %rm     %ru   %>Hs    %<st       %>st        %Ss
     timestamp            src  method  url   status  bytes-in  bytes-out  squid code
```

```
2026-09-09T22:45:06+0000 10.20.104.252 CONNECT idetoolkits.amazonwebservices.com:443 200 1175143 2010 TCP_TUNNEL
2026-09-08T03:49:44+0000 10.20.66.132  GET http://repo.anaconda.com/pkgs/main/noarch/repodata.json 403 TCP_DENIED
```

**`%<st` is bytes from the upstream server and it is BYTES** — divide by 2²⁰ before writing MiB anywhere.
(Written down because it was got wrong on 2026-09-09, in this repository, by reading raw counts as MiB.)

### What each shape means

| shape | reading |
|---|---|
| `200 TCP_TUNNEL` | allowed `CONNECT` — the plane carries the name |
| `403 TCP_DENIED` | **the plane refused it, and the line names the host.** This is the first stop for *"why can't the space reach X"* |
| the name is **absent** | either it took another door, or nobody asked. **Absence is a verdict only with a positive control** — see §7 |

### Four things this log will not tell you unless you already know them

- **Squid matches the name the client REQUESTED, never a DNS answer** (measured 2026-09-08). A **CNAME is
  invisible**; an **HTTP redirect is a NEW name** (`github.com` → `codeload.github.com`, `public.ecr.aws`
  → its CloudFront); a **bare entry matches exactly**, so `github.com` covers neither `api.github.com`
  nor `raw.githubusercontent.com`. Read the new name out of this log and add *that*, never the namespace.
- **A `403` over `https` reads `000` at the client.** The refusal is a `CONNECT` refusal, so
  `curl -w '%{http_code}'` shows `000` while this log shows a named `403`. Two views of one event — and
  the reason a probe that must be legible is run over `http://`.
- **`.amazonaws.com` is on the compute plane**, so a missing bypass entry for an AWS name comes back
  **`200`**, not `403` — it succeeds, publicly, without `aws:SourceVpce`. **The loud failure is the lucky
  one**; see §7's second rule.
- **An `open` plane emits no deny at all**, so this log cannot distinguish *refuses everything* from
  *does not exist*. `./aws/proxy.py` is the instrument for the plane's shape; this log is for its traffic.

### The aggregation that answers most questions

```bash
python3 - <<'PY'
import json, io, collections
ev = json.load(io.open("proxy.json"))["events"]
n, b = collections.Counter(), collections.Counter()
for e in ev:
    p = e["message"].split()
    src, host, code, size = p[1], p[3].rsplit(":", 1)[0], p[4], int(p[5])
    n[(src, host, code)] += 1; b[(src, host, code)] += size
for k, c in n.most_common():
    print("%-16s %-50s %-4s %4d req %8.1f MiB" % (k[0], k[1], k[2], c, b[k]/2**20))
PY
```

Grouping by **source address first** is what makes a restart legible — see §7's third rule.

---

## 4. §D — The resolver query log: was the name even asked, and did the firewall stop it

Records are **one JSON object per query**. The fields, read off a live record 2026-09-09:

```json
{"query_name": "time.aws.com.", "query_type": "A", "rcode": "NXDOMAIN",
 "srcaddr": "10.20.137.172", "srcids": {"instance": "i-0d7998f0b6f47f78b"},
 "vpc_id": "vpc-…", "firewall_rule_action": "BLOCK",
 "firewall_domain_list_id": "rslvr-fdl-…", "answers": []}
```

- **`firewall_rule_action` is ABSENT when no firewall rule fired.** An allowed query simply has no such
  field — do not read the absence as a rule that permitted it. `BLOCK` arrives with
  `rcode: NXDOMAIN`.
- `query_name` is an **FQDN with a trailing dot**. Every comparison against a list has to normalise
  ([`EXC-04`](../../AWS_STATE.md) is what forgetting that costs).
- `srcids.instance` names an EC2 instance. **A SageMaker app has none**, so space containers are named by
  their **address** and identified by their **behaviour** — which names they asked for. That is how 8.2
  told a Code Editor space from a JupyterLab one with both ENIs already gone.

### Why this log is not optional

**A name missing from a compute plane can fail without ever reaching the proxy.** If the resolver
firewall blocks the query there is no `403` to find, and the client reports `getaddrinfo ENOTFOUND` —
which reads as a network fault. Two facts make the triage short:

- **The hub carries no DNS Firewall**, so an `ENOTFOUND` can only come from a compute VPC.
- A name that moved **from a `BLOCK` here to a `403` there** is the signature of a client that started
  honouring the proxy — the exact reading that separated 6d's gallery defect from its neighbours.

```bash
python3 - <<'PY'
import json, io, datetime
for e in json.load(io.open("dnsfw.json"))["events"]:
    m = json.loads(e["message"])
    t = datetime.datetime.utcfromtimestamp(e["timestamp"]/1000).strftime("%H:%M:%SZ")
    print("%s %-16s %-6s %-45s %s" % (t, m.get("srcaddr"), m.get("firewall_rule_action", "-"),
                                      m.get("query_name"), m.get("rcode")))
PY
```

---

## 5. §C — CloudTrail: which principal, and which door

**This is the only instrument that answers "which door".** The proxy log knows names, the flow log knows
addresses; only CloudTrail carries `vpcEndpointId`.

| field | reading |
|---|---|
| `vpcEndpointId` **present** | the call took that interface or gateway endpoint — it stayed inside, and `aws:SourceVpce` applied |
| `vpcEndpointId` **absent** | it left publicly; `sourceIPAddress` then says by which egress (the proxy's Elastic IP, the VPN's, a private address) |
| `errorCode` + the message | **the denial wording is the evidence, never the exit code**: *"explicit deny in a service control policy"* vs *"…in an identity-based policy"* vs an implicit deny that names nothing |
| `userAgent` | separates a person from a service: `Mozilla/…` is the console, `sagemaker.amazonaws.com` or an `AWSServiceRoleFor…` arn is the service acting on its own |
| `requestParameters` | what was actually asked — which space, which app, which resource |

**Two readings this estate keeps coming back to:**

- **Two doors by service family** (6c, 2026-09-07): one command produced `GetCallerIdentity` arriving as
  the **proxy's public address** with no endpoint id, and `GetDataAccess` arriving as a **private address
  with a gateway endpoint id**. Same host, same second, different families.
- **Who deleted it** (6d, 2026-09-09): `DeleteApp` from a browser `userAgent` is a person restarting a
  space; the same call from `AWSServiceRoleForAmazonSageMakerNotebooks` is **idle shutdown**. The API
  cannot tell you, the `userAgent` and the identity can.

```bash
python3 - <<'PY'
import json, sys
for e in json.load(sys.stdin)["Events"]:
    ct = json.loads(e["CloudTrailEvent"])
    print("%s %-30s src=%-16s vpce=%-24s err=%s" % (
        e["EventTime"], ct.get("eventName"), ct.get("sourceIPAddress"),
        ct.get("vpcEndpointId", "-"), ct.get("errorCode", "-")))
PY
```

---

## 6. §F — Flow logs, §V — the VPN host, §S — Studio

- **Flow logs** are `[P]` and always on, `ALL` traffic, aggregated at **600 s**, retention 30 days.
  Addresses and ports, `ACCEPT`/`REJECT`, **never names** — so they answer *did anything reach this ENI*
  and nothing about *what it was asking for*. **Gateway-endpoint traffic crosses no ENI at all**, so an
  S3 call through the gateway is invisible here; `vpcEndpointId` in CloudTrail is the instrument for
  that one (Stage 5, verification xix).
- **`/awsds/prod/vpn`** carries the WireGuard host's own output. For what the *running interface* holds —
  peers, handshakes — the log is not enough: `./aws/vpn.py --on-host` reads inside the host, and
  [`vpn.md`](vpn.md) owns that procedure.
- **`/awsds/<env>/studio`** is the Studio app groups' destination. AWS also writes `/aws/sagemaker/studio`
  and `datazone-<id>-dev` on its own; when a Studio symptom is not in ours, look there before concluding
  nothing was logged.

### §W — an MWAA Serverless workflow: the log group is the second instrument, not the first

Added 2026-09-10, from the run that debugged 6d step 4. `/aws/mwaa-serverless/<domain>-<project>/<workflow>`
holds the task's stdout — the traceback — but **the service's own API holds the verdict**, and it is faster:

```bash
WF=$(aws mwaa-serverless list-workflows --profile awsds-infra-sandbox-1        --query 'Workflows[0].WorkflowArn' --output text)
aws mwaa-serverless list-workflow-runs  --workflow-arn "$WF" --profile awsds-infra-sandbox-1
aws mwaa-serverless list-task-instances --workflow-arn "$WF" --run-id "$RUN"        --profile awsds-infra-sandbox-1
```

- **`DurationInSeconds` is a first-cut diagnosis.** A task that dies before the AWS SDK, one that dies in
  the operator's own validation, and one that reaches the API and is refused sat at **7 s, 8 s and 12-17 s**
  on the same workflow — three modes separated before a log line was opened.
- **Read the TASK's duration, never the RUN's.** Every run here is **two attempts** (try 1 `UP_FOR_RETRY`,
  try 2 `FAILED`) — the default retry — so a 7-second task sits inside a 6-minute run.
- **`WorkflowVersion` on the run names the exact definition it used**, and every `update-workflow` mints a
  new one. That is how a run is attributed to a definition without trusting memory.
- **The log group can be the WRONG one.** `LoggingConfiguration` is a field of the workflow, so an update
  that drops it silently re-points the logs at a service-default group — the symptom is *"the run produced
  no logs"* while a second, orphan group fills up ([Lesson 60](../lessons.md)).

---

## 7. The four readings that recur

1. **Two channels that do not share a failure mode.** The strongest result in this repository has this
   shape: *the name is absent from the proxy log* **and** *CloudTrail shows the calls carrying the
   endpoint id*. Either alone is ambiguous; together they rule out the failure that succeeds
   ([Lesson 24](../lessons.md)).
2. **The loud failure is the lucky one.** Whether a defect shows as a `403` or as a silent success is
   decided by the **domain family**, not by severity: a name on the plane comes back `200` and leaves
   publicly. Before concluding a log is clean, ask *what would this failure have looked like* — see
   [6d step 8.8](../stages/stage-06d-unified-studio-remainder.md).
3. **A restart cuts the log into non-overlapping windows.** A space's container gets a **new address**, so
   grouping by `srcaddr` gives a **paired before/after** on one log group with no clock arithmetic. Get
   the restart's exact time from CloudTrail (`DeleteApp` then `CreateApp`), not from memory.
4. **Absence is a verdict only with a positive control.** *"The name is not in the log"* is worth nothing
   until you show the client was talking at all — 76 other requests in the same four minutes, or the
   calls themselves in CloudTrail. Otherwise you have measured a quiet client.

---

## 8. Traps, each with what it cost

| trap | the tell |
|---|---|
| `--start-time` is **ms** for `logs`, **ISO** for `cloudtrail` | a silently empty result |
| `storedBytes` reads `0` on a live group (2026-09-08) | list the **streams** instead |
| `firewall_rule_action` **absent** ≠ allowed by a rule | it means no rule fired |
| `%<st` is **bytes** (2026-09-09) | a figure ~5 % too large, labelled MiB |
| a `403` over https is **`000`** at the client | the proxy log has the real code |
| CloudTrail has **no data events** yet | `GetObject` will never appear; that is Stage 11 |
| a piped command's exit code ([Lesson 46](../lessons.md)) | a truncated read that looks like a finding |
| a name searched with no `--start-time` is bounded by the group's **creation** | say *"never, since <date>"*, not *"never"* |
| an SSO session expiring mid-session | every later call fails on a **missing token**, not on permissions |
| an MWAA **run**'s duration read as its **task**'s (2026-09-10) | the retry delay, not the work — `list-task-instances` |

---

## 9. Which identity reads which log

**One `aws sso login --sso-session awsds` covers all of these** — the choice is which identity to pick in
the browser, not which profile to log in with.

| log | profile | permission set |
|---|---|---|
| `/awsds/prod/proxy`, `/awsds/prod/vpn`, the Production flow logs | `awsds-infra-prod` | `InfrastructureAccess` |
| `/awsds/sandbox/*`, `/aws/mwaa-serverless/*` and the `mwaa-serverless` API, the Sandbox flow logs, CloudTrail in Sandbox | `awsds-infra-sandbox-1` | idem |
| `/awsds/staging/*` | `awsds-infra-staging` | idem |

**Log Archive and Audit hold no CLI profile** — the organization trail's S3 copy is not read this way.
Everything above is a **read**; nothing in this runbook writes.

---

*Runbook index: [`CLAUDE.md`](../../../CLAUDE.md) §"What to read, and when" · The proxy's own shape:
[`sg-proxy.md`](sg-proxy.md), [`vpn.md`](vpn.md) · The instruments: [`aws/INDEX.md`](../../../aws/INDEX.md)*
