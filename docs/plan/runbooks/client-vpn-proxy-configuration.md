# Runbook — The client: the session, the VPN and the proxy

> **New 2026-09-07, at the user's request.** Everything a person needs to put a laptop on the private
> network and, from there, on the internet — in the order it is done, and deliberately short. **The
> reasoning is not here**: what the pieces are, how a packet travels, the failure modes, the two planes
> and the keys are [`vpn.md`](vpn.md) (§S, §C4-§C6, §K); the whole network is
> [`docs/NETWORK.md`](../../NETWORK.md). §1-§3 replace `vpn.md`'s old §S5 (the session order) and
> §C0-§C3 (the config, up, down), moved here whole and trimmed.

| | |
|---|---|
| **Scope** | §1 up and §2 down — the session: the two hub hosts, and a spoke's `[E]` slices when the day needs them. §3 — the device and the tunnel: enrol, write the `.conf` — **two profiles since 2026-09-08, monitored and split-tunnel** (§3.3; the rule for choosing is `vpn.md` §C7) — up with its four checks, down. §4 — the device and the proxy: macOS (system, terminal, Chrome) and Linux |
| **Operator** | §1-§2: the **infrastructure user** (`sso-session awsds`), account **Production**, permission set **`InfrastructureAccess`**, profile `awsds-infra-prod` — plus the spoke's profile on the same session (`awsds-infra-sandbox-1` for `ENV=sandbox`). §3-§4: the **device's owner, on the device** — no AWS profile, no SSO session |
| **The values** | `Endpoint` **`52.89.212.1:51820`** · the host's `PublicKey` **`LCD1d6xjsxRAmOZA/FTo72TToGUkLYqlOryEJwfup28=`** · `DNS` **`10.31.0.2`** · `MTU` **`1280`** · this device's `Address` **`10.90.0.<n>/32, fd90::<n>/128`** · the proxy **`proxy.awsds.internal:3128`**, whose internet-facing address is **`184.33.8.126`**. All `[P]`: they survive every host stop, start and replacement. The proxy's *private* address is the one thing looked up by name and never written down |

---

## 1. Up — the session

Everything metered is stopped or destroyed between sessions (D11). A session always needs the two hub
hosts; it needs a spoke's `[E]` slices only when it uses them.

1. **Sign in** — one login covers every `awsds-infra-*` profile; pick the infrastructure user in the
   browser, then confirm which permission set answered:

   ```bash
   aws sso login --sso-session awsds && aws sts get-caller-identity --profile awsds-infra-prod
   ```

2. **Start the hub** — the WireGuard host *and* the proxy, nothing applied:

   ```bash
   make hub-up
   ```

   `./aws/vpn.py` must read `running` with `VP-1`..`VP-9` passing. The SSM agent needs a further
   minute; the tunnel needs only the handshake. `make status` prices what is up.

3. **Only when the session needs an account's `[E]` slices** — SageMaker apps in Sandbox need its
   interface endpoints:

   ```bash
   make up ENV=sandbox
   ```

   Add `GROUPS=bedrock,emr` for the optional families; the default is none. It **refuses** while a hub
   host is stopped, naming it — and it is never the way to start the hub: it raises endpoint sets a
   tunnel does not use.
   **Without it a space does not fail, it hangs** (measured 2026-09-07): JupyterLab loads, the terminal
   works, and *"IDE configuration in progress"* never clears — the app's AWS calls have no path. Run
   this, then stop and start the space. From its terminal, `getent hosts sts.us-west-2.amazonaws.com`
   must answer `10.20.x.x`.

4. Tunnel up on the device (§3.4), in the profile the day needs (§3.3), then the proxy (§4) — which under
   the split-tunnel profile is only for the applications acting as a persona.

## 2. Down — in this order

1. **Tunnel down on every device first** (§3.5): with a monitored (full) tunnel up, a stopped host strands the
   laptop's default route until `wg-quick down` runs; under split-tunnel it strands the private routes and
   the DNS.
2. **`make down ENV=<account>`** for each account whose `[E]` slices are up — it deletes the running
   Studio apps, destroys the `[E]` slices, then stops that account's `[D]` hosts. `ENV` is never optional.
3. **`make hub-down`** — last, and the easiest to forget. It **stops** both hub hosts; nothing is
   destroyed, and no client config moves: the addresses, the host key and the security groups are `[P]`.
4. **`make status`** must show nothing running. What still bills is the monthly floor — two Elastic IPs,
   the secret, two volumes — `docs/plan/cost-model.md`'s. On the laptop, proxy off (§4).

---

## 3. The device and the VPN

### 3.1 Install

- **macOS**: `brew install wireguard-tools` gives `wg` and `wg-quick`, the form every check below uses.
  The WireGuard app from the App Store imports the same `.conf` — see §4.1 [a] for what it does to the
  system proxy.
- **Linux**: the distribution's `wireguard-tools` package, plus `openresolv` or `systemd-resolved` — one
  of the two is what `wg-quick` uses to apply the `DNS =` line. *Documented, not exercised in this
  project (Lesson 54).*
- **Phone or tablet**: the WireGuard app. No file: the values below are typed into its form,
  **`MTU` included**.

### 3.2 Enrol the device — once

The private key is generated **on the device** and has no copy anywhere; only the public half travels.

```bash
cd ~ && (umask 077 && wg genkey | tr -d '\n' > mbp-private.key) && wg pubkey < mbp-private.key > mbp-public.key
```

Hand the content of `mbp-public.key` and a free `host` number to the roster,
`terraform-live/production/vpn/peers.auto.tfvars` (`2` is the laptop); the infrastructure user applies
that slice — an instance **replacement**, minutes of outage for every device, and the address does not
move. The procedure, and what `peer=unknown` in the handshake log means: [`vpn.md`](vpn.md) §K4.

### 3.3 Write the config

Outside the repository. The private key is read from its file and never typed, so it reaches neither the
screen nor the shell history; the `umask 077` inside the subshell lands the file `600`.

```bash
cd ~ && (umask 077 && cat > mbp.conf <<EOF
[Interface]
PrivateKey = $(cat mbp-private.key)
Address = 10.90.0.2/32, fd90::2/128
DNS = 10.31.0.2
MTU = 1280

[Peer]
PublicKey = LCD1d6xjsxRAmOZA/FTo72TToGUkLYqlOryEJwfup28=
AllowedIPs = 0.0.0.0/0, ::/0
Endpoint = 52.89.212.1:51820
PersistentKeepalive = 25
EOF
)
```

**The split-tunnel profile — the same file, one line changed** *(added 2026-09-08, 6c pass 8; which profile
when is `vpn.md` §C7)*. Write it as a second file from the same key, and replace the `AllowedIPs` line:

```bash
cd ~ && (umask 077 && sed 's#^AllowedIPs = .*#AllowedIPs = 10.20.0.0/16, 10.30.0.0/16, 10.31.0.0/16, 10.32.0.0/16, 10.50.0.0/16, 10.90.0.0/24#' mbp.conf > mbp-split.conf)
```

The five VPC CIDRs of `NETWORK.md` §1 plus the tunnel's own range. A sixth VPC is a new entry here and
nothing in the monitored file; `10.0.0.0/8` is the one-line alternative, and it captures a home LAN
numbered in `10.x`. `Address`, `DNS`, `MTU`, `PublicKey`, `Endpoint` and the key are the same — the two files
differ in that line alone. **One profile active at a time**: the same key is one peer on the host.

| Line | The rule it carries |
|---|---|
| `Address` | `<n>` is this device's `host` number from the roster. **The `fd90::` half must be present**: without it `AllowedIPs = ::/0` is inert and every IPv6-capable application leaves outside the tunnel (`vpn.md` §C6) |
| `DNS` | the hub's resolver, `VPC-Networking`'s `.2`. A VPC's resolver answers no query from across a peering, so any other value leaves the tunnel up and every name unresolvable |
| `MTU` | the one path-dependent value; `1280` passes every path met so far — phone tethering is where a derived value fails (`vpn.md` §C4) |
| `AllowedIPs` | **full tunnel in the monitored profile**: a persona's AWS call must leave through the proxy, whose address is the one `DenyControlPlaneOffVpn` accepts. **The split-tunnel profile lists the private ranges instead** (above; `vpn.md` §C7): the internet leaves direct, and a persona's call still needs the proxy — pointed at it by the application (§4) |

`PublicKey` and `Endpoint` are stable by design: if either ever changes without `vpn.md` §K3 having been
run, that is a finding, not a reconnection problem.

### 3.4 Up, and the four checks

```bash
sudo wg-quick up ~/mbp.conf
```

(Or activate the tunnel in the app.) **Bring the tunnel up before starting anything that talks to
AWS**: a socket opened earlier keeps the laptop's own uplink. Then, in order — each proves a different
claim:

| # | Command | Must read |
|---|---|---|
| 1 | `sudo wg show` — or, with the App Store app, **its window**: `wg` does not list a Network Extension tunnel (2026-09-08) | `latest handshake` seconds ago and non-zero `transfer`; in the app, *Latest handshake* and *Data received / sent* under the peer; the interface is a `utun*` on macOS |
| 2 | `dig +short SOA prod.awsds.internal ; dig +short SOA sandbox.internal` | the first **answers**, the second is **empty** — the resolver in use is the hub's. Then `dig +short proxy.awsds.internal` → a **private** address in `10.31.160.0/24` |
| 3 | `curl -sS --max-time 15 https://1.1.1.1` | **fails** — as `curl: (28)` timeout or as `curl: (7) … after 194 ms`, both measured 2026-09-07: the host refuses every time and rate-limits the ICMP that says so (Lesson 55). A `200` is the finding |
| 4 | `curl -s --max-time 20 -x http://proxy.awsds.internal:3128 https://checkip.amazonaws.com` | **`184.33.8.126`**, the proxy's address — the tunnel, the peering, the return route and the client plane, in one line |

**Under the split-tunnel profile the third reading inverts and the other three hold** (measured 2026-09-08,
6c step 8.3): check 3 **answers** — `301` in 10 ms, the site redirects — and
`curl -s https://checkip.amazonaws.com` prints the laptop's own uplink address; checks 1, 2 and 4 read the
same, because the private space, the resolver and the proxy are all still through the tunnel. In
`netstat -rn` the `utun`'s default carries the **`I`** flag in both families — interface-scoped, inert — and
`en0` keeps the primary; under the monitored profile the tunnel's default has no `I`. A timeout on check 3
under split-tunnel is the finding — a stale route, or the monitored tunnel still up.

A 403 on check 4 is the proxy refusing a *name*; nothing at all is the path, or a stopped host (§1).
When a check fails: `vpn.md` §C4.

### 3.5 Down

```bash
sudo wg-quick down ~/mbp.conf
```

The file stays and nothing is revoked. Then proxy off (§4).

---

## 4. The device and the proxy

**Which profile decides who needs this section** (`vpn.md` §C7, 2026-09-08): under the **monitored**
profile, every application; under the **split-tunnel** profile, **only the applications that act as a
persona** — a terminal running a persona profile, a Chrome opened on the console or the portal as a
persona — while everything else, the infrastructure user's terminal included, goes direct and needs nothing
here.

The estate's only internet is an **explicit** proxy, `proxy.awsds.internal:3128`, resolvable only
through the tunnel. Explicit means not transparent: a program that has not been told about it does not
fail over to it, it **hangs** — check 3 above is that hang, on purpose. Three rules for every setting
below:

- **Everything public goes through it, AWS included.** `*.amazonaws.com` never goes in a bypass list:
  the perimeter accepts the proxy's address and nothing else.
- **Nothing private goes through it.** The proxy refuses private destinations, so the estate's own names
  — `.awsds.internal`, `.awsds-pages.internal` — and `localhost` are bypassed.
- **Off with the tunnel.** Down, the proxy's name does not resolve, and a setting left behind breaks
  every tool that honours it.
- **Git over SSH has no path** — §4.3.

The proof, on any OS, is check 4 of §3.4. What the tunnel may reach through the proxy — everything,
logged — is `vpn.md` §C5a.

### 4.1 macOS

**[a] The system proxy — leave it OFF** (measured 2026-09-07,
[issue #67](https://github.com/felipenoris/AWS-DataScience/issues/67)). The setting is System Settings →
Network → Wi-Fi → Details… → Proxies, *Web proxy* and *Secure web proxy* both `proxy.awsds.internal`
port `3128`, bypass `*.awsds.internal, *.awsds-pages.internal, localhost, 127.0.0.1`; on the command
line, `networksetup -setsecurewebproxy "Wi-Fi" proxy.awsds.internal 3128`. It fails in both
directions. **Tunnel up, it is not consulted**: the WireGuard app's tunnel becomes the primary service
and carries no proxy of its own, so `scutil --proxy` — what applications are actually handed — returns
an empty dictionary while `networksetup -getsecurewebproxy "Wi-Fi"` says `Enabled: Yes`; Safari,
Chrome by default and every native application have no working path. **Tunnel down, it is consulted
again**, now pointing at a name that does not resolve: the `aws` CLI fails with `Failed to connect to
proxy URL`, and an empty `https_proxy` does not override it — only `NO_PROXY='*'` does. The two working
paths are [b] and [c].

**[b] The terminal — environment variables, verified.** Set after the tunnel is up, unset when it goes
down; both spellings, because `curl` reads the lower-case names and `botocore` reads either. Two
functions in `~/.zshrc`:

```bash
proxy-on() {
  export https_proxy=http://proxy.awsds.internal:3128
  export http_proxy=$https_proxy HTTPS_PROXY=$https_proxy HTTP_PROXY=$https_proxy
  export no_proxy=localhost,127.0.0.1,.awsds.internal,.awsds-pages.internal
  export NO_PROXY=$no_proxy
}
proxy-off() { unset https_proxy http_proxy HTTPS_PROXY HTTP_PROXY no_proxy NO_PROXY; }
```

`proxy-on` reaches `aws`, `uv run` and boto3, `curl`, `git` and `pip`; it reaches no GUI application.
A persona call denied *with the tunnel up* is a socket that predates the tunnel, or a shell without
`proxy-on`.

**[c] Google Chrome — the flag, verified 2026-09-07.** Chrome reads the system proxy by default, which
[a] says is empty; the flag replaces it and binds to a **new process**, so quit Chrome completely first:

```bash
open -na "Google Chrome" --args --proxy-server="http://proxy.awsds.internal:3128" --proxy-bypass-list="*.awsds.internal,*.awsds-pages.internal,localhost,127.0.0.1"
```

The SMUS portal and the AWS console open through it. With the tunnel down, that Chrome has no internet
until it is quit and relaunched without the flag. Firefox keeps its own proxy settings (Settings →
Network Settings → Manual proxy: the same host, port and bypass list) and is the alternative for a
browser that stays configured — not yet verified here.

### 4.2 Linux

*Documented from the tools' own manuals, not exercised in this project (Lesson 54). The macOS
limitation in [a] is a property of the NetworkExtension tunnel and is not expected here, where
`wg-quick` makes an ordinary interface — measure before relying on it.*

- **[a] The system proxy** (GNOME) — consulted by every application that reads the desktop setting,
  Chrome included; back to `mode 'none'` when the tunnel goes down:

  ```bash
  gsettings set org.gnome.system.proxy mode 'manual'
  gsettings set org.gnome.system.proxy.http host 'proxy.awsds.internal'
  gsettings set org.gnome.system.proxy.http port 3128
  gsettings set org.gnome.system.proxy.https host 'proxy.awsds.internal'
  gsettings set org.gnome.system.proxy.https port 3128
  gsettings set org.gnome.system.proxy ignore-hosts "['localhost', '127.0.0.1', '.awsds.internal', '.awsds-pages.internal']"
  ```

- **[b] The terminal** — the two functions of §4.1 [b], unchanged, in `~/.bashrc` or `~/.zshrc`.
- **[c] Google Chrome** — nothing, when [a] is set; otherwise the same two flags on the command line:
  `google-chrome --proxy-server="http://proxy.awsds.internal:3128" --proxy-bypass-list="*.awsds.internal,*.awsds-pages.internal,localhost,127.0.0.1"`.

### 4.3 GitHub — push over HTTPS, never SSH (measured 2026-09-07)

**The port is the problem, and no proxy setting fixes it.** `git@github.com` speaks SSH on port **22**;
the tunnel host rejects it like any other non-RFC1918 destination, and the proxy cannot carry it either:
Squid accepts `CONNECT` to **443 only** (the *unsafe ports* deny, `vpn.md` §C5a). So with the tunnel up a
`git fetch`/`push` over SSH reads *Connection refused* at `github.com:22`, however the shell is
configured. GitHub's SSH-over-443 endpoint (`ssh.github.com`) is not a way through on macOS either:
`nc -X connect` rejects Squid's `HTTP/1.1 200 Connection established` reply.

**The path is HTTPS, with `gh`'s token.** `gh` is already signed in (`gh auth status`) and honours
`https_proxy`; once, tell `git` to take its credentials from `gh`:

```bash
gh auth setup-git
```

Then either switch the remote to HTTPS —

```bash
git remote set-url origin https://github.com/felipenoris/AWS-DataScience.git
```

— or leave the SSH remote for tunnel-down work and push explicitly to the HTTPS URL when the tunnel is
up (`git push https://github.com/felipenoris/AWS-DataScience.git HEAD:refs/heads/<branch>`). Both go
through the proxy with `proxy-on` (§4.1 [b]) and appear in its access log as `CONNECT github.com:443`.
**With the tunnel down, SSH works again and the proxy variables must be off** — the same rule as every
other setting in this section.

---

*Runbooks: [`vpn.md`](vpn.md) · [`buildbox.md`](buildbox.md) · [`sandbox-lake.md`](sandbox-lake.md) ·
[`terraform-changes.md`](terraform-changes.md) · Plan core: [`GENERAL_PLAN.md`](../../GENERAL_PLAN.md)*
