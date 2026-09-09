
# Proxy Config on SageMaker

## How to produce

Read as output of terraform endpoints:

```
cd terraform-live/sandbox/egress && terraform output -raw no_proxy
```

On JupyterLab terminal:

```
export http_proxy=http://proxy.awsds.internal:3128 https_proxy=$http_proxy HTTP_PROXY=$http_proxy HTTPS_PROXY=$http_proxy no_proxy='<cole a saída acima>' NO_PROXY=$no_proxy && curl -s -o /dev/null -w '%{http_code}\n' --max-time 20 https://pypi.org/
```

## Latest reading

```
export NO_PROXY='.awsds-pages.internal,.awsds.internal,127.0.0.1,169.254.169.254,169.254.170.2,api.ecr.us-west-2.amazonaws.com,api.sagemaker.us-west-2.amazonaws.com,athena.us-west-2.amazonaws.com,datazone.us-west-2.amazonaws.com,dkr.ecr.us-west-2.amazonaws.com,dynamodb.dualstack.us-west-2.amazonaws.com,dynamodb.us-west-2.amazonaws.com,ec2.us-west-2.amazonaws.com,ec2messages.us-west-2.amazonaws.com,glue.us-west-2.amazonaws.com,kms.us-west-2.amazonaws.com,lakeformation.us-west-2.amazonaws.com,localhost,logs.us-west-2.amazonaws.com,runtime.sagemaker.us-west-2.amazonaws.com,s3.dualstack.us-west-2.amazonaws.com,s3.us-west-2.amazonaws.com,s3tables.us-west-2.amazonaws.com,secretsmanager.us-west-2.amazonaws.com,ssm.us-west-2.amazonaws.com,ssmmessages.us-west-2.amazonaws.com,sts.us-west-2.amazonaws.com,studio.us-west-2.sagemaker.aws'

export no_proxy="$NO_PROXY" http_proxy=http://proxy.awsds.internal:3128 https_proxy=http://proxy.awsds.internal:3128 HTTP_PROXY=http://proxy.awsds.internal:3128 HTTPS_PROXY=http://proxy.awsds.internal:3128
```

## `apt` — the variables do not survive `sudo`

Measured 2026-09-08. `sudo` resets the environment (`env_reset`) and `http_proxy` is not in its
`env_keep`, so `apt` runs with a clean environment, resolves the destination itself and is refused by the
Sandbox DNS Firewall — `Could not resolve 'archive.ubuntu.com'`, on a name that **is** on the proxy's
allow-list. Exporting the variables first changes nothing, and that is the tell.

Use `apt`'s own option, which needs neither the environment nor a sudoers change:

```
sudo apt -o Acquire::http::Proxy="http://proxy.awsds.internal:3128" -o Acquire::https::Proxy="http://proxy.awsds.internal:3128" update
```

The durable form is in the house image, not in a shell: `/etc/apt/apt.conf.d/01proxy` carrying those two
`Acquire::` lines, plus a sudoers `env_keep` for the six proxy variables so a person's exports survive
`sudo` for everything that is not `apt`. Both belong to Stage 6d step 2.2.

## Code Editor — the extension gallery has no proxy at all

Measured 2026-09-08. A Code Editor space fails to update **AWS's own** `aws-toolkit-vscode` and
`amazon-q-vscode` at every start, with `getaddrinfo ENOTFOUND open-vsx.org`. That is a **resolution**
failure, so the VS Code server never had proxy variables — the allow-list was never consulted.
`open-vsx.org` is on the compute plane since 2026-09-08 (applied, read back on the host). The delivery
mechanism is the open half: Stage 6d **step 8.4**.

### The setting, and it is a probe before it is a fix

Per space, and it **dies with the space** — so this is how you learn whether the server honours a proxy
at all, not how every space gets one. Command Palette → **Preferences: Open User Settings (JSON)** (the
path is not written down here on purpose — the palette is stable, the path is not), then:

```json
{
  "http.proxy": "http://proxy.awsds.internal:3128",
  "http.proxySupport": "override",
  "http.proxyStrictSSL": true,
  "http.noProxy": [
    "*.awsds-pages.internal",
    "*.awsds.internal",
    ".awsds-pages.internal",
    ".awsds.internal",
    "127.0.0.1",
    "169.254.169.254",
    "169.254.170.2",
    "api.ecr.us-west-2.amazonaws.com",
    "api.sagemaker.us-west-2.amazonaws.com",
    "athena.us-west-2.amazonaws.com",
    "datazone.us-west-2.amazonaws.com",
    "dkr.ecr.us-west-2.amazonaws.com",
    "dynamodb.dualstack.us-west-2.amazonaws.com",
    "dynamodb.us-west-2.amazonaws.com",
    "ec2.us-west-2.amazonaws.com",
    "ec2messages.us-west-2.amazonaws.com",
    "glue.us-west-2.amazonaws.com",
    "kms.us-west-2.amazonaws.com",
    "lakeformation.us-west-2.amazonaws.com",
    "localhost",
    "logs.us-west-2.amazonaws.com",
    "runtime.sagemaker.us-west-2.amazonaws.com",
    "s3.dualstack.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
    "s3tables.us-west-2.amazonaws.com",
    "secretsmanager.us-west-2.amazonaws.com",
    "ssm.us-west-2.amazonaws.com",
    "ssmmessages.us-west-2.amazonaws.com",
    "sts.us-west-2.amazonaws.com",
    "studio.us-west-2.sagemaker.aws"
  ]
}
```

Four things in there are decisions rather than detail:

**`http.noProxy` is not optional.** `http.proxySupport` defaults to `override`, which patches the
**extension host's** HTTP stack — so an extension's AWS SDK calls would leave by the proxy instead of the
VPC endpoint: bytes paid for that the gateway endpoint carries free, and arrival **without
`aws:SourceVpce`**, which is a deny wherever a policy conditions on it. The same hazard the buildbox
carries, one layer up.

**The list is generated, and the syntax is not the environment's.** It is `terraform output -raw no_proxy`
on `sandbox/egress` — the value at the top of this file — never transcribed. But the env-var form
suffix-matches on a **leading dot** (`.awsds.internal`) and VS Code's `http.noProxy` is documented with a
**glob** (`*.awsds.internal`). They agree on all 26 exact names and differ on exactly the two wildcards
([Lesson 53](../lessons.md) in its smallest form), so **both spellings are carried** — correct under
either matcher, at a cost of two array entries. Regenerate it, do not copy it, whenever an endpoint moves.

**`http.proxyStrictSSL` stays `true`.** It is the first knob anyone turns when a proxy misbehaves, and it
would buy nothing here: Squid `CONNECT`-tunnels rather than terminating TLS, so the certificate the client
validates is the origin's. A failure that `proxyStrictSSL: false` fixes would mean the proxy had started
intercepting — a finding, not a setting.

**Restart the space, do not reload the window.** The failure is on the startup auto-update path
(`Auto updating outdated extensions`, before any user act), so only a stop/start from the portal
reproduces it.

### Reading the result — two logs, and the interesting outcome is not the clean one

| `/awsds/prod/proxy` | `/awsds/sandbox/dns-firewall` | reading |
|---|---|---|
| `open-vsx.org` **200** | no `open-vsx.org` BLOCK | the setting is honoured, end to end |
| `open-vsx.org` 200, **403 on another name** | that name absent | honoured; a **second name** is needed — the asset host (6d step 8.6) |
| **nothing** | `open-vsx.org` BLOCK persists | not honoured by this server; the mechanism is a lifecycle configuration instead |
| `open-vsx.org` 200 | **`idetoolkits.amazonwebservices.com` BLOCK** | **the split**: VS Code's own request service proxied, the extension host's not |

**Do not add names to the plane before this reading.** Ahead of it they turn an informative `403` into an
uninformative `200`. If the extension host ignores the proxy the names fail with `ENOTFOUND` whether they
are listed or not; if it honours it, the `403` is the measurement. The list is edited **after** step 8.6.

### What it measured, 2026-09-08 — row four, inverted

**The setting is honoured by everything except the gallery.** The restart gave the space a new address, so
the reading is a paired before/after on one space with no overlap. Three names moved **from a DNS `BLOCK`
to a Squid `403`** across it — `idetoolkits.amazonwebservices.com`, `api.github.com`,
`raw.githubusercontent.com` — `pypi.org` moved from `BLOCK` to `200`, and the space made **98 proxied
requests, 96 MiB**. **`open-vsx.org` alone did not move**: 24 `BLOCK`s from the new address and no
appearance in the proxy log at all.

So *"no proxy in the process"* no longer describes this component. The process has one; the gallery does
not use it. Environment variables deliver the same fact by another route, so they are not expected to
reach a client that ignores `http.proxy` either.

### ⚠ It also breaks DataZone, and that is the exception list, not the proxy

`datazone.us-west-2.api.aws` was refused **11 times**. The service has an interface endpoint in the VPC,
and the endpoint answers for **two** names — `datazone.us-west-2.amazonaws.com` **and**
`datazone.us-west-2.api.aws` — while the generated list carries only the first. `aws.sagemaker.us-west-2.studio`
carries **four** and contributes one. Until Stage 6d step 8.8 fixes the generator, **add the missing names
by hand** to `http.noProxy` when you set this up:

```
"datazone.us-west-2.api.aws",
"studio.sagemaker.us-west-2.app.aws"
```

**A refused name that has a VPC endpoint is never an allow-list entry.** Allowing it makes it work while
sending the call out through the hub as a public one, arriving without `aws:SourceVpce` — the symptom is
identical and only one of the two repairs is correct.
