
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

**50 entries, read from `sandbox/egress` after the `vpc-egress-v0.11.1` apply of 2026-09-09**
(6d step 8.8). It was 28 before that: the generator read the *service's* one canonical name and
now reads every name the *endpoint* answers for. If your copy has 28, it is missing
`datazone.us-west-2.api.aws` among twenty-one others, and DataZone will be refused in the space.

```
export NO_PROXY='.awsds-pages.internal,.awsds.internal,.dkr-ecr.us-west-2.on.aws,.dkr.ecr.us-west-2.amazonaws.com,.studio.sagemaker.us-west-2.app.aws,.studio.us-west-2.sagemaker.aws,127.0.0.1,169.254.169.254,169.254.170.2,api.ecr.us-west-2.amazonaws.com,api.sagemaker.us-west-2.amazonaws.com,api.sagemaker.us-west-2.api.aws,athena.us-west-2.amazonaws.com,athena.us-west-2.api.aws,datazone.us-west-2.amazonaws.com,datazone.us-west-2.api.aws,dkr-ecr.us-west-2.on.aws,dkr.ecr.us-west-2.amazonaws.com,dynamodb.dualstack.us-west-2.amazonaws.com,dynamodb.us-west-2.amazonaws.com,ec2.us-west-2.amazonaws.com,ec2.us-west-2.api.aws,ec2messages.us-west-2.amazonaws.com,ecr.us-west-2.api.aws,glue.us-west-2.amazonaws.com,glue.us-west-2.api.aws,kms.us-west-2.amazonaws.com,kms.us-west-2.api.aws,lakeformation.us-west-2.amazonaws.com,lakeformation.us-west-2.api.aws,localhost,logs.us-west-2.amazonaws.com,logs.us-west-2.api.aws,runtime.sagemaker.us-west-2.amazonaws.com,runtime.sagemaker.us-west-2.api.aws,s3.dualstack.us-west-2.amazonaws.com,s3.us-west-2.amazonaws.com,s3tables.us-west-2.amazonaws.com,s3tables.us-west-2.api.aws,secretsmanager.us-west-2.amazonaws.com,ssm.us-west-2.amazonaws.com,ssm.us-west-2.api.aws,ssmmessages.us-west-2.amazonaws.com,ssmmessages.us-west-2.api.aws,streaming-logs.us-west-2.amazonaws.com,streaming-logs.us-west-2.api.aws,sts.us-west-2.amazonaws.com,sts.us-west-2.api.aws,studio.sagemaker.us-west-2.app.aws,studio.us-west-2.sagemaker.aws'

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
    ".dkr-ecr.us-west-2.on.aws",
    ".dkr.ecr.us-west-2.amazonaws.com",
    ".studio.sagemaker.us-west-2.app.aws",
    ".studio.us-west-2.sagemaker.aws",
    "127.0.0.1",
    "169.254.169.254",
    "169.254.170.2",
    "api.ecr.us-west-2.amazonaws.com",
    "api.sagemaker.us-west-2.amazonaws.com",
    "api.sagemaker.us-west-2.api.aws",
    "athena.us-west-2.amazonaws.com",
    "athena.us-west-2.api.aws",
    "datazone.us-west-2.amazonaws.com",
    "datazone.us-west-2.api.aws",
    "dkr-ecr.us-west-2.on.aws",
    "dkr.ecr.us-west-2.amazonaws.com",
    "dynamodb.dualstack.us-west-2.amazonaws.com",
    "dynamodb.us-west-2.amazonaws.com",
    "ec2.us-west-2.amazonaws.com",
    "ec2.us-west-2.api.aws",
    "ec2messages.us-west-2.amazonaws.com",
    "ecr.us-west-2.api.aws",
    "glue.us-west-2.amazonaws.com",
    "glue.us-west-2.api.aws",
    "kms.us-west-2.amazonaws.com",
    "kms.us-west-2.api.aws",
    "lakeformation.us-west-2.amazonaws.com",
    "lakeformation.us-west-2.api.aws",
    "localhost",
    "logs.us-west-2.amazonaws.com",
    "logs.us-west-2.api.aws",
    "runtime.sagemaker.us-west-2.amazonaws.com",
    "runtime.sagemaker.us-west-2.api.aws",
    "s3.dualstack.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
    "s3tables.us-west-2.amazonaws.com",
    "s3tables.us-west-2.api.aws",
    "secretsmanager.us-west-2.amazonaws.com",
    "ssm.us-west-2.amazonaws.com",
    "ssm.us-west-2.api.aws",
    "ssmmessages.us-west-2.amazonaws.com",
    "ssmmessages.us-west-2.api.aws",
    "streaming-logs.us-west-2.amazonaws.com",
    "streaming-logs.us-west-2.api.aws",
    "sts.us-west-2.amazonaws.com",
    "sts.us-west-2.api.aws",
    "studio.sagemaker.us-west-2.app.aws",
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
on `sandbox/egress` — the value at the top of this file — never transcribed. The array above is a
**snapshot of that output**, so regenerate it rather than copying it whenever an endpoint moves.
The generator already emits every **wildcard service name in two forms**, bare and dot-prefixed, because
the matchers disagree about which one covers a subtree. What it cannot know is that VS Code's
`http.noProxy` is documented with a **glob** (`*.awsds.internal`) where the environment variable
suffix-matches on a **leading dot** (`.awsds.internal`) — [Lesson 53](../lessons.md) in its smallest
form — so the array carries **two entries the generator did not produce**: the glob spelling of the two
internal zones. Everything else is the output verbatim.

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
not use it.

**But the ENVIRONMENT does reach it — measured 2026-09-09, and it corrects the sentence that stood here.**
`code-editor-server --install-extension`, run from the terminal with the six variables exported and
`VSCODE_IPC_HOOK_CLI` unset, connected and returned an **HTTP** `403`, never `getaddrinfo`. **The client
honours `http_proxy`/`https_proxy` and ignores the `http.proxy` setting** — two delivery routes that look
like one fact and are read by different code.

And the `403` was **Squid's**, naming the last missing piece: **`open-vsx.org` serves the API and
`openvsx.eclipsecontent.org` serves the `.vsix` bytes**. Both are now on the compute plane (committed
2026-09-09; **the second is unapplied** until the parameter write). A single-name allow-list authorised
the question and refused the answer.

**So the repair is two acts**: the compute plane's second name, and the environment delivered to the
`codeeditorserver` supervisord program — which can be attached only at the **domain or user-profile**
level (`SpaceSettings` carries a smaller shape that has neither `LifecycleConfigArns` nor
`CustomImages`), so it inherits Stage 6d step 2.4's reconciliation question. Until then, the by-hand
`export` in a terminal is what works.

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

## Installing an extension in a Code Editor space — the working procedure

**Use this whenever an extension is needed in a Code Editor space.** The `Install` button in the
Extensions view does **not** work and will not until Stage 6d step 2 delivers the environment to the
`codeeditorserver` supervisord program: the server the space starts has no proxy variables, and the
gallery client honours `http_proxy`/`https_proxy` while **ignoring** the `http.proxy` setting. This
procedure gives that one invocation the environment the server lacks.

**It is per space and it dies with the space.** A rebuilt or recreated space needs it again.

### 1. Install

Replace `Anthropic.claude-code` with the extension id you want — the `publisher.name` shown on the
extension's page.

```bash
export http_proxy=http://proxy.awsds.internal:3128 https_proxy=$http_proxy HTTP_PROXY=$http_proxy HTTPS_PROXY=$http_proxy && unset VSCODE_IPC_HOOK_CLI && /opt/conda/share/sagemaker-code-editor/bin/code-editor-server --install-extension Anthropic.claude-code --extensions-dir "$PERSISTENT_VOLUME_EXTENSIONS_DIR" --force ; echo "rc=$?"
```

Four parts of that line are load-bearing, and three of them were learned by getting them wrong first:

| | why |
|---|---|
| the **six variables** | the gallery client reads the environment and ignores the `http.proxy` setting — two delivery routes that look like one fact and are read by different code |
| `unset VSCODE_IPC_HOOK_CLI` | without it the `remote-cli` **forwards the call into the already-running server**, which has no proxy. The command would then measure that server's environment instead of this shell's, and fail exactly as the button does |
| `--extensions-dir "$PERSISTENT_VOLUME_EXTENSIONS_DIR"` | the directory the running server actually reads. Installing into a scratch directory succeeds and the IDE never sees it |
| `; echo "rc=$?"` — a semicolon, **not** `&&` | the exit code is wanted **especially** on failure, and `&&` would swallow it ([Lesson 46](../lessons.md)) |

### 2. Reload

**Developer: Reload Window.** The server scans the extensions directory at startup, so without the
reload it does not see what appeared underneath it.

### 3. What is fixed, and what is still broken

`rc=0` and the extension appears with its `Install` button gone. **It runs** — measured 2026-09-09 from
the command palette.

**Clicking the extension's card still raises `An unknown error occurred`.** That is the extension's
**detail page**, which is a gallery read, and it fails for the same reason the button does. It is not a
sign that the install went wrong, and the extension works regardless — **test it by using it, never by
opening its marketplace entry**, which is the one action guaranteed to fail. The same cause also produces
the `getaddrinfo ENOTFOUND open-vsx.org` burst at every space start, from the auto-update check.

Platform-specific extensions get the **right** build this way: the CLI negotiates the platform
(`…-linux-x64`), while the browser workbench names none and the registry then answers with its own
default — which is why a gallery URL in the log may read `targetPlatform=alpine-arm64` on an `x86_64`
container.

### 4. If it fails with a `403`

The `403` is **Squid's**, and the refused name is in `/awsds/prod/proxy` within seconds:

```bash
aws logs filter-log-events --profile awsds-infra-prod --region us-west-2 --log-group-name /awsds/prod/proxy --start-time $(python3 -c "import time;print(int((time.time()-600)*1000))") --output json
```

An extension can pull from hosts nobody has listed. Adding a name is a decision, not a fix — Stage 6d
decision due 6, and the first question about a refused name is **whether it has a VPC endpoint**: one
that does belongs in `NO_PROXY`, never on the proxy's allow-list, or the call works while arriving
without `aws:SourceVpce`.
