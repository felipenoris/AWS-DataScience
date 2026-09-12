# Runbook — the remote IDE: a laptop's VS Code attached to a Sandbox space

| | |
|---|---|
| **Scope** | Connecting VS Code on a laptop to a SageMaker space in Sandbox, and everything that decides whether it works: the space's `RemoteAccess` flag, the identity that calls `sagemaker:StartSession`, the two IDE servers that end up running in the same container, where an extension installs and which gallery serves it, which of those calls cross the estate's proxy, and the files that cross the session itself in either direction. The space itself is the portal's ([`dev-env.md`](dev-env.md) owns the image it starts on); the network it sits in is [`docs/NETWORK.md`](../../NETWORK.md)'s |
| **Operator** | The **data scientist** at the laptop, through the portal identity (Identity Center). Every reading in §V is the **infrastructure user**'s — account **Sandbox**, permission set **`InfrastructureAccess`**, profile `awsds-infra-sandbox-1`, and the proxy log is Production's `awsds-infra-prod`. One SSO login covers both |
| **The rules** | **`RemoteAccess` is per space**, and settable after creation with the space stopped. **The space needs ≥ 8 GB**: `ml.t3.medium`, the estate's default, is named unsupported. **The call is the project role's**, so neither `DenyControlPlaneOffVpn` nor 6a's tag pair evaluates — §I. **The compute plane refuses both Microsoft names and the session works anyway**, by a documented fallback — §N, and it is what makes this channel cost the estate nothing |
| **The picture around it** | Why there is one egress and an explicit proxy: [D38](../decisions/D38-single-egress-hub.md). What a space reaches: [`docs/NETWORK.md`](../../NETWORK.md). The proxy inside a space by hand: [`sg-proxy.md`](sg-proxy.md). The image the space starts on: [`dev-env.md`](dev-env.md) |
| **Written** | 2026-09-11 at [Stage 6d](../stages/stage-06d-unified-studio-remainder.md) step 7.8, from **two** sessions measured that day — one on a current client, one on a client pinned to the image's version, which is what §N's comparison of the two client settings rests on. Exercised: §W end to end on Windows x64, §E's two surfaces and its three routes out of a version conflict, §N's readings, every §V instrument but the laptop-side logs, and three of §F's rows. Unexercised, and each says so in place: the tunnel-down negative control (7.5), the 12-hour residual (7.7), the tag pair on a principal that carries it (7.6), §C's bundle path, and §W's **macOS** client — its download, portable-mode rules and connect path are read from the vendor's pages and the Toolkit's own source on 2026-09-11, and nothing on a Mac has been run here. The vendor pages are the 2026-09-11 rows of [`docs/REFERENCES.md`](../../REFERENCES.md) |

---

## O. The pieces, and who owns each

A working session is five objects, and only one of them is this repository's.

| Piece | What it is | Owner |
|---|---|---|
| **The space, with `RemoteAccess` enabled** | the compute the session attaches to. Per space, per app type | the portal, by hand |
| **`sagemaker-remote-access-server`** | a binary AWS places in `~/.sagemaker_remoteAccess_do_not_delete/`, which is what answers the data channel. 6.87 MB, root-owned, its `mtime` AWS's own build date; the directory appears **between** the credential vend and the `StartSession` (15:57Z against 15:52:45Z and 16:02:15Z on 2026-09-11) and its bytes are in no proxy log, so the service delivers it and not the plane | the service |
| **`sagemaker:StartSession`** | the call that opens the channel, answered with a `wss://ssmmessages.<region>.amazonaws.com/v1/data-channel/…` URL | the client, as the project role (§I) |
| **The VS Code Server** | Microsoft's server, under `~/.vscode-server/cli/servers/Stable-<commit>/`, at the **client's own version** | the client, per connection |
| **The Code Editor server** | AWS's Code-OSS, `/opt/conda/share/sagemaker-code-editor`, already running on port 8888 for the browser surface | the image |

The last two run **at the same time, in the same container**, with separate extension directories and
separate settings files. That is §E's whole subject, and the first thing to understand before debugging
anything about extensions.

## I. Who makes the call, and which perimeter it crosses

Measured 2026-09-11 from CloudTrail in Sandbox, two `StartSession` calls at 16:02:15Z and 16:02:28Z:

| field | value |
|---|---|
| principal | `datazone_usr_role_<project>_<env>` — **the project role**, resolved by role id |
| session name and `sourceIdentity` | `<idc-user-id>@<env-id>` — the Identity Center user travels inside the role session |
| `sourceIPAddress` | the **laptop's own public address**, not the proxy's Elastic IP and not an AWS-internal one |
| `userAgent` | `aws-sdk-js/… os/win32 lang/js md/nodejs` — the call is made **client-side** |
| resource | `space/<domain-id>/<space-name>` |

**What this means for the controls the estate already has.** 1c withholds `sagemaker:StartSession` from
the `Interactive` document and 6a step 3.2 put two tag-scoped denies into the six persona permission
sets. Both are attached to personas; the caller here is a blueprint-authored project role, so **neither
evaluates**, and the session worked with the laptop off the VPN entirely. The scoping the objective asks
for is granted by nothing today (Lesson 18, with Lesson 28 underneath: the grant and the constraint live
in different slices).

**The Toolkit is not the persona path.** The AWS Toolkit's SageMaker panel signs in to the **SMUS domain**
and receives project-role credentials; it does not use the laptop's persona role. The portal's deep link
is the same principal by a different client — measured 2026-09-10 19:37:27Z, same role, same address, a
Chrome user agent, refused with `ValidationException … does not have remote access enabled` because that
space had the flag off. So both available methods put the project role in front of the call, from the
user's own address.

**Two keys exist for scoping it**, and neither needs Identity Center *attributes for access control*:
`aws:SourceIdentity` on the role session, and the space's `OwnershipSettings.OwnerUserProfileName`,
which carries the same user id. A condition on the **D13 permissions boundary** is the one instrument
this estate has that reaches a role the blueprint writes. Which shape it takes is decision due 4 in
[Stage 6d](../stages/stage-06d-unified-studio-remainder.md), still open; until it is taken, this channel
is reachable from any network by anyone the domain admits.

## W. Configuring the client for a remote session

**Pin the client to the Code Editor's version.** The remote VS Code Server is installed at the
**client's** commit, so the client's version is what the marketplace resolves extension builds against.
Matching the version AWS pins in the image (`1.119.1`, read from
`/opt/conda/share/sagemaker-code-editor/product.json` on 2026-09-11) is what keeps one extension set
usable in both surfaces. A pinned client receives no fixes — stable was `1.137.0` on the day this was
written — so keep a current install for everything else and use the pinned one for this session. **The
pin is a choice and not a prerequisite** — §E carries what it buys, what it costs, and the per-extension
route that needs no pin at all. **What holds the pin differs by platform**: the Windows archive does not
update itself, the macOS application does and has to be told not to.

One build per platform, all three from commit `974500e64f0d1cfdf7c9821a2a51c2cb3bf0e561`:

| platform | download | sha256 of the file |
|---|---|---|
| Windows x64 | `https://update.code.visualstudio.com/1.119.1/win32-x64-archive/stable` | `6fd3396113d865571811497949a6c01784102e24f076e95a207d66918475894b` |
| Windows arm64 | `https://update.code.visualstudio.com/1.119.1/win32-arm64-archive/stable` | `6438dc885a99b82fe72a5841f5caf7a321e689852c85bc087ff4eafd579d6ff5` |
| macOS Apple silicon | `https://update.code.visualstudio.com/1.119.1/darwin-arm64/stable` | `f00ca1d7bf0ba24ca1f39fb58252afe57adfbb672badd3bb8f00ef692d6e6e74` |

The hashes are the vendor's own, read 2026-09-11 from
`https://update.code.visualstudio.com/api/versions/1.119.1/<platform>/stable` (`sha256hash`). The two
Windows rows were in this file before the third was added and the API returned them unchanged, which is
the control on the `darwin-arm64` row. The macOS zip expands to `Visual Studio Code.app` and carries no
version in its name, so name the directory it goes into. Verify before extracting — no administrator is
needed for either step:

```powershell
Get-FileHash -Algorithm SHA256 .\VSCode-win32-x64-1.119.1.zip | Format-List
```

```bash
shasum -a 256 ~/Downloads/VSCode-darwin-arm64.zip
```

```bash
ditto -x -k ~/Downloads/VSCode-darwin-arm64.zip "$HOME/Applications/vscode-1.119.1"
```

**Turn the extracted folder into its own installation.** On Windows, create an empty `data` folder
beside `Code.exe`:

```
VSCode-win32-x64-1.119.1\
  Code.exe
  data\            <- create this
```

Its presence is the switch, and no setting configures it. VS Code then keeps **all** user state there —
settings at `data\user-data\User\settings.json`, extensions at `data\extensions` — instead of in
`%APPDATA%\Code` and `%USERPROFILE%\.vscode`, which every other installation on the machine shares. Skip
this and the pinned client writes its state into the current client's profile.

**On macOS the folder sits beside the application, under another name.** Put the app in a directory of
its own — not `/Applications`, where the current install lives — and create `code-portable-data` next to
it, never inside the bundle:

```
vscode-1.119.1/
  Visual Studio Code.app
  code-portable-data/      <- create this
```

Settings are then at `code-portable-data/user-data/User/settings.json` and extensions at
`code-portable-data/extensions`. Portable mode *"won't work if your application is in quarantine"*, which
is the state a browser download arrives in, so clear the attribute before the first launch — a `curl`
download carries none and the command is harmless either way:

```bash
xattr -dr com.apple.quarantine "Visual Studio Code.app"
```

**On macOS the package does not hold the pin; a setting does.** The vendor's own portable-mode page says
automatic updates keep working on macOS with nothing extra configured, so this installation would leave
`1.119.1` behind on its own, with no message and no diff, and §E's whole reason for the pin would go
with it. Disable updates in the same settings file as the two below:

```json
{
  "update.mode": "none"
}
```

**Set who downloads.** Open the pinned client, `Ctrl+Shift+P` (`Cmd+Shift+P` on macOS) → *Preferences:
Open User Settings (JSON)* — in portable mode this is the file inside `data` or `code-portable-data` —
and add:

```json
{
  "remote.downloadExtensionsLocally": true,
  "remote.SSH.localServerDownload": "always"
}
```

Both are **client-side** (application scope): the settings editor greys them out on the *Remote [SSH]*
tab. They are a different subject from the `data` folder — they decide which machine fetches the bytes,
which in this estate is the difference between a working install and a `403` (§N).

**Install two client extensions**: *Remote - SSH* and *AWS Toolkit*.

**Sign in to the domain.** Open the AWS panel from the sidebar icon, find **SAGEMAKER UNIFIED STUDIO**,
choose to sign in with IAM Identity Center, and enter the **full domain URL** — the portal's own address,
`https://dzd-<domain-id>.sagemaker.us-west-2.on.aws/` — then Enter. A browser opens to authorize the
application. The credentials that come back are the **project role's**, which is why §I reads the way it
does.

**Connect.** The Toolkit opens a new window: `Opening Remote`, then
`Setting up SSH Host sm_…: Copying VS Code Server to host with scp`, and it takes minutes on a first
connection. That message is the measurement: the server is **copied from the laptop**, because the
space's own attempt to fetch it was refused (§N).

### What the connection runs on the laptop, and what macOS adds to it

Read from the Toolkit's source on 2026-09-11 (`awsService/sagemaker/`, `shared/sshConfig.ts`,
`shared/utilities/cliUtils.ts`), because the pieces below are invisible from the UI and every one of
them is a place a macOS session can fail. **None of it is exercised here** — the Windows session of
7.8 is what this file measured.

**The Toolkit checks its dependencies before it connects**: the *Remote - SSH* extension at or above a
minimum version, an `ssh` on the path — macOS ships one — and a `session-manager-plugin`, which it
installs itself if the check fails.

**The Toolkit writes an SSH host and a connect script.** The host block is `Host sm_*` in
`~/.ssh/config` — `ForwardAgent yes`, `AddKeysToAgent yes`, `StrictHostKeyChecking accept-new` and a
`ProxyCommand`, with the file forced to `0600`. The `ProxyCommand` is the platform difference: on
Windows it is `powershell.exe … -File sagemaker_connect.ps1 %n`, and on macOS it is
`'<globalStorage>/sagemaker_connect' '%n'`, a bash script the extension copies out of itself and marks
executable. The script needs `curl`, which macOS ships, and **`jq`**, which it does not — this estate
installed `jq` long ago, and a laptop without it fails in the `ProxyCommand` rather than in the UI. It reads the session from a local HTTP server the Toolkit spawns
(`SAGEMAKER_LOCAL_SERVER_FILE_PATH` names the JSON that carries its port) and ends in
`exec "$AWS_SSM_CLI" "$SSM_SESSION_JSON" "$REGION" StartSession`.

**The `session-manager-plugin` the session uses is the Toolkit's own, not the laptop's.** The
toolkit's unix entry for that CLI is a single relative path under its own storage, so a Homebrew
install on `PATH` does not satisfy the check; it downloads the `mac_arm64` `.pkg`, expands it with
`pkgutil` and `tar` into its storage — no administrator, no installer run — and hands the connect
script the absolute path in `AWS_SSM_CLI`. Nothing has to be installed by hand for this, and the
`session-manager-plugin` Stage 4 put on the laptop (`vpn.md`'s table) is a different copy serving a
different purpose.

**Whether the laptop needs a proxy is decided by the profile, not by macOS.** The calls are the
SageMaker API and the `ssmmessages` data channel, both public names:

| the laptop's network | what the session needs |
|---|---|
| off the VPN | nothing — the two names are reached directly, which is how 7.8 ran |
| the tunnel in its split-tunnel profile | nothing — `AllowedIPs` carries the five VPC CIDRs, so a public AWS name is not routed into the tunnel |
| the tunnel in its monitored profile | the proxy has to reach the processes below, or the session times out with no refusal to read (Lesson 55) |

**On macOS the monitored profile has no system path to the proxy.** `scutil --proxy` is empty while the
tunnel is primary ([`client-vpn-proxy-configuration.md`](client-vpn-proxy-configuration.md) §4.1 [a],
issue #67), so a client launched from the Dock inherits nothing. Two shapes carry it, and the second is
a reading rather than a measurement:

- launch the pinned client from a terminal that has run `proxy-on`, so `process.env` carries the
  variables into the `ssh` child and into the plugin:

```bash
"$HOME/Applications/vscode-1.119.1/Visual Studio Code.app/Contents/MacOS/Electron" &
```

- or set `http.proxy` and `http.noProxy` in the client's settings. The Toolkit turns those two into
  `HTTP_PROXY`/`HTTPS_PROXY`/`NO_PROXY` and puts them in the environment of both the local server and
  the `ssh` process (`model.ts`'s `getLocalProxyEnv`, merged into the connection's `envProvider`), which
  is the whole path the plugin needs. Read from the code, never run here; the terminal launch is the
  shape whose process tree the operator controls.

**Two clients on one machine share `~/.ssh/config` and nothing else.** Each writes its own
`sagemaker_connect` under its own `globalStorage` — inside `code-portable-data/user-data` for a portable
install — and the Toolkit rewrites the host block when the `ProxyCommand` it finds is not its own. A
host that connects from one client and fails from the other is this, not the space.

## E. Extensions: UI, Workspace, and the version conflict

**The kinds.** VS Code splits extensions in two. *UI extensions* "contribute to the VS Code user
interface and are always run on the user's local machine" — themes, snippets, language grammars,
keymaps. *Workspace extensions* "are run on the same machine as where the workspace is located", so in a
remote session they run **in the space**. An extension declares this with `extensionKind` in its
`package.json`, and VS Code chooses when both are possible. A language server, a debugger or a linter is
a workspace extension by nature: it needs the files and the toolchain. `Developer: Show Running
Extensions` says which side each one is on.

So **`Install in SSH: <host>` installs in the space** — and specifically into the VS Code Server's own
directory, not into the surface the browser uses.

**The two surfaces, measured in one container on 2026-09-11:**

| | Code Editor, from the portal | the remote session, from the laptop |
|---|---|---|
| server | `/opt/conda/share/sagemaker-code-editor`, Code-OSS **1.119.1** | `~/.vscode-server/cli/servers/Stable-<commit>`, **the client's version** |
| gallery | `https://open-vsx.org/vscode/gallery` | `https://marketplace.visualstudio.com/_apis/public/gallery` |
| extensions | `~/sagemaker-code-editor-server-data/extensions` | `~/.vscode-server/extensions` |
| settings | `~/sagemaker-code-editor-server-data/data/User/` | `~/.vscode-server/data/User/` |

Both directories are under `/home/sagemaker-user`, which is the space's EBS volume, so both survive a
restart of the app and neither is in the image. **The settings files are separate in the same way**, and
that has bitten this estate once already: 6d step 8.4's `http.proxy` repair was written into the Code
Editor's settings and reaches nothing on the VS Code Server's side. A fix applied in one surface is not
applied in the other — check which file you edited before concluding a setting does not work. And
`~/.vscode-server/cli/servers/` holds **one tree per client version** that has ever connected — two
after a pin, a few hundred MB each on a 64 GB volume — so an old one is safe to delete and worth
deleting only if the volume is tight. An extension installed in one surface is invisible to the
other, and the same extension can sit in both at **different versions** — the AWS Toolkit was `3.101.0`
on the Open VSX side and `4.15.0` on the marketplace side the day this was written.

**The version conflict, and why it is not about the remote.** The compatibility check reads
`engines.vscode` against the runtime that will load the extension. Because the remote server takes the
client's version, a complaint naming *your* version is the marketplace offering a build that wants a
newer editor than the client — typically a **pre-release** build; `rust-analyzer` publishes its
pre-releases as `0.4.x`. The fixes, cheapest first:

1. the extension's gear menu → **Switch to Release Version**, or **Install Specific Version…** and pick
   one below the build that complained. Then turn **Auto Update** off for it, or it returns;
2. install it from the portal's Code Editor instead, where Open VSX resolves against 1.119.1;
3. carry the `.vsix` yourself: download the **`linux-x64`** build on the laptop — platform-specific,
   because the package embeds the language server binary — drag it into the remote window's Explorer,
   and in the remote terminal run `code --install-extension <file>.vsix`, which is the server's CLI and
   installs on the remote side. The space cannot fetch it itself (§N).

**What pinning the client actually buys, and what it costs.** Measured 2026-09-11: the remote server's
`product.json` read `1.127.0` against a `1.127.0` client, so a client-versus-remote mismatch does not
exist and a version complaint is never about the remote runtime. What the pin aligns is the **two
surfaces** — a client at the image's `1.119.1` resolves extension builds against the same engine the
portal's Code Editor does, so one extension set serves both, and the install that had complained
succeeded once the client was pinned. What it costs is an editor that never updates and that is, by
construction, behind the current stable — which makes *"requires a newer VS Code"* more likely for other
extensions, not less. The per-extension answer stays route 1; the pin is for the operator who wants one
extension set across both surfaces.

## N. What crosses the estate's egress, and what does not

Read from `/awsds/prod/proxy` on 2026-09-11, one space's address:

| name | reading | what it is |
|---|---|---|
| `update.code.visualstudio.com` | **403 TCP_DENIED** × 3, at 16:02:19-16:02:56 | the space trying to download the VS Code Server |
| `marketplace.visualstudio.com` | **403 TCP_DENIED** × 7, at 16:08-16:09 | the space trying to fetch a `.vsix` |
| `aws-language-servers.us-east-1.amazonaws.com` | 200, 50.73 MiB | the Toolkit's language servers, allowed by the plane's `.amazonaws.com` entry and therefore a **public** call, carrying neither `aws:SourceVpc` nor `aws:SourceVpce` |
| `idetoolkits.amazonwebservices.com`, `idetoolkits-hostedfiles.amazonaws.com`, `ide-toolkits.app-composer.aws.dev`, `sagemaker-unified-studio-mcp.<region>.api.aws` | 200 | the IDE's own startup traffic, four names, three of them decided at 6d 8.6 |
| `api.anthropic.com` | **403 TCP_DENIED** × 17 | an extension the user installed reaching its own service; on no plane, so it does not work in a space |
| `*.in.applicationinsights.azure.com` | **403 TCP_DENIED** | editor telemetry nobody asked for, refused |

**Neither refusal breaks the session**, and that is the design working rather than luck. Remote - SSH
"will attempt to download on the remote host, and fail back to downloading VS Code Server locally and
transferring it remotely once a connection is established", which is the `scp` line §W quotes; the
extension bytes take the same route. So the remote IDE channel needs **no entry on the compute plane**:
the two Microsoft names stay off it, and the laptop — whose own plane is `open` when it is on the
tunnel — is what fetches.

**The two client settings reduce those calls and do not remove them**, measured across two sessions the
same day. Without them, one container asked `update.code.visualstudio.com` three times and
`marketplace.visualstudio.com` fifteen times over four minutes. With `remote.SSH.localServerDownload:
always` and `remote.downloadExtensionsLocally: true` on the client, the next container asked
`update.code` **once** at connect and `marketplace` **three times** at install — and the extension
installed and ran. Every one of those lines is a 3.4 KB Squid error page, so no Microsoft byte has ever
crossed this plane. The operating rule: **a `403` on either name during a session that works is
expected**, not a failure to chase; what would be a finding is a `200`.

**One thing this log cannot settle**, and it is worth stating rather than implying: whether a given
remote call was a *download attempt* or a version-and-metadata probe. The CLI under `~/.vscode-server/cli`
checks for updates on its own, so a single `update.code` line after a connect is not evidence that the
server was being fetched. The instrument that separates them is the **client's** Extensions and
Remote-SSH output channels, outside the estate.

**The channel is also a file path the plane cannot see.** The `.vsix` that arrived on 2026-09-11 arrived
*through the session*, not through the proxy, and the same tunnel carries any file in either direction.
The compute plane's allow-list is a list of **names**, so it says nothing about this; `github.com` was
removed from that list on 2026-09-09 to keep code from leaving a governed environment, and this channel
is not covered by that removal. It is an input to decision due 4 and to
[Stage 11](../stages/stage-11-dlp.md)'s threat model, recorded here as a property of the channel rather
than as a defect in the list.

## C. Moving files between the laptop and the space

The session carries files in both directions and the estate's instruments do not see them: the bytes
travel inside the data channel, so no name reaches Squid and no query reaches the DNS Firewall (§N). The
same property carries the procedures below and makes this channel a
[Stage 11](../stages/stage-11-dlp.md) subject.

**Why a procedure is needed at all.** The compute plane carries no source control: `github.com` came off
it on 2026-09-09, and `git clone`, `fetch` and `push` from a space fail by that decision rather than by
accident. **This is the path for today and not the design.** The estate's GitLab is internal — it lands
in `VPC-SharedServices`, reached over the `Sandbox ↔ VPC-SharedServices` peering that
[INT-09](../integrations.md) already carries — so from
[Stage 7](../stages/stage-07-gitlab-runners-ecr.md) a space clones over private addresses with no laptop
in the middle, and this section becomes the exception rather than the route.

**A file arrives by drag and drop.** Drag it from the laptop's file manager — Explorer on Windows,
Finder on macOS — onto the file tree of the **remote** window. It lands in the directory it is dropped
on, under `/home/sagemaker-user`, which is the space's EBS volume — so it survives a restart of the app, and the portal's Code Editor sees the same file (§E).
Exercised 2026-09-11: the `linux-x64` `.vsix` of §E's route 3 arrived this way, and the remote terminal's
`code --install-extension` read it from disk.

**The reverse direction is the VS Code Explorer's context menu**, *Download* on a file in the remote
tree. It is the direction Stage 11 cares about, and it is unexercised here.

**One file is the proven case.** A folder drop is not, and a repository dropped as a folder is thousands
of transfers where the method below is one.

**A repository arrives as a `git bundle`.** A bundle is git's own transport for a channel that is not a
network: one file, the full history, and a real repository at the far end. On the laptop, where the
GitLab host resolves:

```bash
git clone --mirror https://<gitlab-host>/<group>/<project>.git project.git
git -C project.git bundle create ../project.bundle --all
```

`--mirror` is what makes `--all` mean every branch and every tag; from a plain clone the bundle carries
the one local branch that clone checked out. Drag `project.bundle` into the remote window, then from a
terminal in the space:

```bash
git bundle verify project.bundle
git clone project.bundle project
```

`verify` is the instrument: it lists the refs the bundle holds and says whether the bundle is
self-contained, which separates a file that did not arrive whole from a clone that is wrong. After the
clone, `origin` is the bundle's path on disk. **The space holds no GitLab credential and a `push` reaches
nothing**, which is a property of this path rather than a gap to repair.

**Later commits travel as a second bundle**, cut from the point the space is already at:

```bash
git -C project rev-parse main                                     # in the space: where it is
git -C project.git bundle create ../incr.bundle <that-sha>..main  # on the laptop
git -C project pull ../incr.bundle main                           # in the space, after the drop
```

The starting point is read from the space and not noted on the laptop, so the procedure does not depend
on a file only its author holds (Lesson 61). `git bundle verify` refuses `incr.bundle` in a repository
that lacks the commits it starts from, which is the same instrument answering a different question.

**Unexercised here: every command of the bundle path.** They are git's own, and the channel under them is
the one the `.vsix` proved, but nobody has run this sequence in this estate.

## V. Reading it back

One instrument per question, all read-only.

**Which principal made the call, and from where** — Sandbox:

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=StartSession \
  --max-results 10 --profile awsds-infra-sandbox-1 --output json --query 'Events[].CloudTrailEvent' \
  | jq -r '.[] | fromjson | [.eventTime, .userIdentity.arn, .sourceIPAddress, .userAgent] | @tsv'
```

**What the space is, and whether the flag is on**:

```bash
aws sagemaker describe-space --domain-id <domain-id> --space-name <space> \
  --profile awsds-infra-sandbox-1 --query 'SpaceSettings.[RemoteAccess,AppType,CodeEditorAppSettings.DefaultResourceSpec]'
```

**Read the third field, not only the first two.** `DefaultResourceSpec` carries the space's **own
copy of the image version number**, written when the space was created, and it **overrides the
domain default** — so an image bump leaves it naming a version that no longer exists. Measured
2026-09-12: after `default-v0.4.0` became image version 4, `remote-editor-claude` still pinned
version 3, which the apply had destroyed. Repairing it is [`dev-env.md`](dev-env.md) §B step 6, and
it is `update-space` rather than a recreate — **`RemoteAccess`, the EBS size and the project's S3
connection all live in that same block**, and a recreate loses the home directory with them.

**Which names the session's traffic asked for** — Production, and the window matters: this log lags its
own events by minutes, so an absence read too early is not an absence (`log-debugging.md`):

```bash
aws logs filter-log-events --log-group-name /awsds/prod/proxy --start-time <epoch-ms> \
  --profile awsds-infra-prod --query 'events[].message' --output text | tr '\t' '\n'
```

**Which surface's terminal you are in** — the question that precedes every other in-space reading,
because the two servers' terminals look identical:

```bash
echo "${PERSISTENT_VOLUME_EXTENSIONS_DIR:-<empty: not a Code Editor terminal>}"
echo "${SUPERVISOR_PROCESS_NAME:-<empty>}"
```

A Code Editor terminal is a child of the `codeeditorserver` supervisord program and carries both; the
remote session's terminal carries neither (measured 2026-09-11). The image's proxy environment reaches
**both**, since every process in the container inherits it — which is why `cargo` fetched
`index.crates.io` from a remote session with nothing configured.

**What the connect script did, on the laptop** — the `ProxyCommand` runs under `set -x` and writes to
the Toolkit's own storage, beside the local server's log. On macOS that directory is
`~/Library/Application Support/Code/User/globalStorage/amazonwebservices.aws-toolkit-vscode` for a normal
install, and the same path under `code-portable-data/user-data` for a pinned one:

```bash
ls -lt "$HOME/Library/Application Support/Code/User/globalStorage/amazonwebservices.aws-toolkit-vscode" | head
```

`sagemaker.connect.log` carries the script's trace and `sagemaker-local-server.*.log` the server that
vends the session. They are the instrument for a connection that fails before any AWS call appears in
CloudTrail, which is where §F's timeout row sends you.

**Which servers are running in the space, and where their extensions went** — from a terminal in the
space:

```bash
pgrep -af node | cut -c1-200
for p in ~/.vscode-server/cli/servers/Stable-*/server/product.json /opt/conda/share/sagemaker-code-editor/product.json; do
  python3 -c "import json;d=json.load(open('$p'));print(d['version'], d.get('extensionsGallery',{}).get('serviceUrl'))"
done
ls ~/.vscode-server/extensions ~/sagemaker-code-editor-server-data/extensions
```

## F. Failures, and what each one is

| symptom | what it is |
|---|---|
| `ValidationException … does not have remote access enabled` | the flag is off on that space. Stop the space, turn Remote Access on in its details, start it |
| an `AccessDenied` on `StartSession` naming an identity-based policy | the caller is a **persona**, not the project role — the persona sets hold no Allow. Read the caller before changing anything (§I) |
| the connection hangs at `Copying VS Code Server to host` for many minutes on a first connect | expected: the laptop is transferring the server because the space's own download was refused (§N) |
| a timeout with nothing in CloudTrail | the call never arrived. A permission failure is a response; a network failure is the absence of one (Lesson 42) |
| `getaddrinfo ENOTFOUND <name>` inside the space | the process has **no** proxy variables, so it resolved the name itself and the DNS Firewall refused it. On `default-v0.2.0` and later the image carries them; on earlier images see [`sg-proxy.md`](sg-proxy.md) |
| `Server returned 403` inside the space | the process has the variables and the **name** is not on the compute plane. The first question is whether that name has a VPC endpoint ([`docs/NETWORK.md`](../../NETWORK.md)) |
| an extension refuses to install, naming your VS Code version | the marketplace offered a build that wants a newer editor; §E's three fixes |
| an extension installed but not running | it went to the other surface, or it is a UI extension. `Developer: Show Running Extensions` |
| an extension is present in one surface and missing in the other | expected: two servers, two extension directories (§E). Install it in both, or pin the client so one set serves both |
| `403` on `marketplace.visualstudio.com` in the access log **while the install succeeds** | expected, and measured with the client settings on: the remote still probes the gallery, the bytes come from the laptop. A `200` on that name would be the finding |
| `rust-analyzer` logs `can't load standard library, try installing rust-src` | the image installs rustup's `minimal` profile, which omits `rust-src`; `std` is not indexed, and nothing else is affected. Fixed in `images/dev-env/Dockerfile` for the next build (2026-09-11). In the session at hand: `sudo rustup component add rust-src`, which works because the image's sudoers keeps the proxy variables and `static.rust-lang.org` is on the plane, and which dies with the container |
| an R or conda package manager refused in a space | not this channel's: [`sg-proxy.md`](sg-proxy.md) carries what a space may fetch, and `docs/NETWORK.md` the list |
| the connection times out on the monitored profile, with nothing in CloudTrail | the proxy did not reach the process: on macOS no system setting carries it while the tunnel is primary, so the client has to be launched from a terminal that ran `proxy-on`, or given `http.proxy` (§W). A refusal you cannot see is not silence (Lesson 55) |
| `jq: command not found` or `curl: …` in `sagemaker.connect.log` | the `ProxyCommand` runs with the client process's `PATH`, not a login shell's. Launch the client from a terminal, or install the tool where that `PATH` reaches |
| the pinned macOS client writes into `~/Library/Application Support/Code` | portable mode is not in effect: the folder is not a sibling of the `.app`, is not named `code-portable-data`, or the application is still in quarantine (§W) |
| the pinned macOS client is no longer `1.119.1` | it updated itself. The package does not hold the pin on macOS; `update.mode` set to `none` does (§W) |

## Cost

The session costs the space's instance plus the Sandbox `[E]` endpoint set. The space measured on
2026-09-11 was `ml.t3.xlarge` at **USD 0.200/h** ([`docs/PRICING.md`](../../PRICING.md) §8) — twice the
`ml.t3.large` that is the 8 GB floor the server needs, and the space path carries no instance ceiling
since `sagemaker-denies-v0.2.0`, so the size is a cost choice rather than a permitted one. Idle shutdown
applies to a Code Editor app as it does to JupyterLab: the space read that day had a 60-minute threshold.
The channel itself adds nothing: no endpoint, no plane entry, no NAT.

---

*Runbook index: [`CLAUDE.md`](../../../CLAUDE.md) routing table · Stage:
[6d](../stages/stage-06d-unified-studio-remainder.md) step 7*
