# The first boot. It installs a toolchain, tells every client on the host about the proxy, and runs
# nothing else - no build happens here.
#
# The build is not in the user data. User data runs once, unattended, with its output in a log
# nobody is watching, and a container build is an iterative act. The build context arrives with
# `./scripts/buildbox.py sync`, which can be re-run against a running host. Baking it in here was
# measured and rejected: a gzip+base64 of images/ is ~27 KB against user data's 16 KB ceiling, and
# it would make every Dockerfile edit replace the host (user_data_replace_on_change).
#
# The shell lands as ssm-user, not as ec2-user. Session Manager creates ssm-user on its first
# connection - it does not exist while this script runs, so it cannot be added to the docker group
# here - and it has passwordless sudo. `sudo docker ...` works out of the box, and `sudo -iu
# ec2-user` gets a shell in the docker group.
#
# ---------------------------------------------------------------------------------------------
# The proxy is configured in four places (6c step 5.8, 2026-09-06)
#
# There is no default route in this tier. An explicit proxy is not transparent: a client that has
# not been told about it does not fail over to it, it hangs. Four things on this host open
# connections and each reads the setting from a different place (Lesson 14):
#
#   1. /etc/environment          every login shell and everything systemd starts with
#                                EnvironmentFile. This is what `curl`, `git`, `pip` and `dnf`
#                                read. Both cases are written - `http_proxy` and `HTTP_PROXY` -
#                                because clients disagree about which they honour and the
#                                disagreement is silent.
#   2. the docker daemon         a systemd drop-in. The daemon is what pulls a base image, and it
#                                is not a child of the shell, so it never sees /etc/environment.
#                                A `docker pull` from a shell with a perfect environment still
#                                hangs without this file, and the symptom names the registry
#                                rather than the proxy.
#   3. the docker client's       ~/.docker/config.json `proxies` block, which injects http_proxy
#      build containers          into `RUN` steps. Without it the daemon can pull the base image
#                                and every `pip install` inside the build hangs.
#   4. dnf                       the environment, and not `proxy=` in dnf.conf. `dnf.conf` has a
#                                `proxy=` setting and no exclusion setting to go with it, so
#                                setting it sends everything at the proxy - including the AL2023
#                                repositories, which live on S3 and must go direct through the
#                                gateway endpoint. Measured 2026-09-06: the proxy refused them with
#                                a 403 (this plane excluded `.amazonaws.com` then) and `dnf`
#                                reported `Failed to download metadata`, which reads as a broken
#                                mirror. dnf goes through libcurl, which honours
#                                `http_proxy`/`no_proxy` from the environment, so the environment
#                                is the only place that can express both halves.
#                                Since 2026-09-08 (D38 section 6 amended) that failure is silent:
#                                the plane is `open`, so the proxy would fetch the AL2023
#                                repositories over the internet and everything would appear to work
#                                while S3 traffic left the VPC, paid for bytes the free gateway
#                                endpoint carries, and arrived without `aws:SourceVpce`. `no_proxy`
#                                is what stands between the two, and it is generated (5.6).
#
# `no_proxy` is generated from this VPC's endpoint list (5.6) and carries the SSM names. Session
# Manager is how anyone gets a shell here, so a `no_proxy` that missed
# `ssmmessages.<region>.amazonaws.com` would send the agent's websocket at Squid and lock the host
# out of its only management path. It also carries the S3 and DynamoDB names in both spellings -
# plain and `dualstack` - which no endpoint list can produce (a gateway endpoint has no private DNS
# at all) and which carry the layers of every image pull and the AL2023 repositories. The dualstack
# form was added at `vpc-egress-v0.9.1` after this host's first boot failed on its absence.
# ---------------------------------------------------------------------------------------------

locals {
  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail
    exec > >(tee /var/log/awsds-buildbox-boot.log) 2>&1
    echo "=== awsds buildbox first boot: $(date -Is) ==="

    PROXY="${local.proxy_url}"
    NOPROXY="${local.no_proxy}"

    # This script's own environment, which /etc/environment does not provide: that file is read
    # by PAM at login and by systemd units that name it, and cloud-init's user data is neither.
    # Without these three lines every command below runs with no proxy at all - the shape of a
    # first boot that "works" until something needs the internet.
    export http_proxy="$PROXY" https_proxy="$PROXY"
    export HTTP_PROXY="$PROXY" HTTPS_PROXY="$PROXY"
    export no_proxy="$NOPROXY" NO_PROXY="$NOPROXY"

    # (1) Every shell and every systemd unit that reads this file. Both cases, deliberately.
    echo "--- proxy: /etc/environment"
    cat >> /etc/environment <<ENVEOF
    http_proxy=$PROXY
    https_proxy=$PROXY
    HTTP_PROXY=$PROXY
    HTTPS_PROXY=$PROXY
    no_proxy=$NOPROXY
    NO_PROXY=$NOPROXY
    ENVEOF

    # (4) dnf is configured by the `export` above and by nothing else. A `proxy=` line in
    # /etc/dnf/dnf.conf stood here and is deliberately gone: dnf.conf has a proxy setting and no
    # exclusion setting to pair with it, so it would send the AL2023 repositories - which are on
    # S3 and must go direct through the gateway endpoint - at a proxy whose plane refuses
    # `.amazonaws.com`. That is what broke this host's first boot on 2026-09-06.

    # docker and git: git because a build context is usually a checkout, and because the
    # dev-env image's own INT-09 story starts with one.
    echo "--- installing docker and git"
    dnf -y install docker git

    # (2) The daemon. Not a child of any shell, so /etc/environment never reaches it. This is
    # the file whose absence makes `docker pull` hang while `curl` works.
    echo "--- proxy: the docker daemon"
    mkdir -p /etc/systemd/system/docker.service.d
    cat > /etc/systemd/system/docker.service.d/http-proxy.conf <<DOCKEREOF
    [Service]
    Environment="HTTP_PROXY=$PROXY"
    Environment="HTTPS_PROXY=$PROXY"
    Environment="NO_PROXY=$NOPROXY"
    DOCKEREOF
    systemctl daemon-reload

    echo "--- enabling docker"
    systemctl enable --now docker
    usermod -aG docker ec2-user

    # (3) The build containers. `proxies` in the **client's** config is what injects http_proxy
    # into every RUN step; without it the base image pulls and the first `pip install` inside the
    # build hangs. Written for both accounts that run docker on this host - root (the ssm-user
    # `sudo docker` path) and ec2-user (the docker-group path) - because a setting present for
    # one of them is a build that behaves differently depending on how you got your shell.
    echo "--- proxy: the docker client's build containers"
    for home in /root /home/ec2-user; do
      mkdir -p "$home/.docker"
      cat > "$home/.docker/config.json" <<CLIEOF
    {
      "proxies": {
        "default": {
          "httpProxy": "$PROXY",
          "httpsProxy": "$PROXY",
          "noProxy": "$NOPROXY"
        }
      }
    }
    CLIEOF
    done
    chown -R ec2-user:ec2-user /home/ec2-user/.docker

    # The egress reading, taken once and left in the boot log. Two probes, because one would not
    # be a verification (Lesson 13).
    #
    # The refused probe is a private address. `deny to_private` is line 1 of squid.conf and sits
    # above every plane's allow: it is what stops this proxy becoming an L7 bridge between VPCs
    # that peering keeps apart. On an `open` plane that deny is the perimeter, so proving it is
    # in force is worth more than proving an allow-list this plane no longer has. `10.31.0.1` is
    # the hub VPC's own first address and needs to answer nothing, because the refusal happens at
    # Squid before any connection is attempted. `http://example.com/` stood here until
    # 2026-09-08, reading 403 while it was on no plane; the plane became `open` that day (D38
    # section 6 amended, 6d step 9), which would have printed `must be 403: 200` at every boot -
    # a diagnostic announcing a failure that is the design, in the file somebody opens precisely
    # when something is wrong (Lesson 50).
    #
    # A boot log showing 200 then 403 says the proxy is up, the peering route works, and the
    # private-destination deny is being enforced. 000 on both says the proxy is unreachable.
    # 200 on both means `deny to_private` is gone or has been moved below an allow, the one
    # failure in this file that opens a path between spokes.
    #
    # The exit address is not printed here: `checkip.amazonaws.com` would answer that question
    # and this plane refuses `.amazonaws.com` on purpose - a build host has no business calling
    # the AWS control plane through the proxy, since everything it legitimately calls has an
    # endpoint. The address is measured from the tunnel plane instead, at 6c step 6.1.
    #
    # The refused probe is `http://` and not `https://`, and the scheme decides what curl can
    # see. Measured 2026-09-06: over https the client asks for a CONNECT tunnel, Squid refuses
    # it, and `curl` reports `%%{http_code}` as **000** because no HTTP response ever crossed the
    # tunnel - the 403 exists but is on the CONNECT, where this format string cannot see it. Over
    # http the refusal is the response and reads as a plain 403 whose body names Squid. So the
    # two probes use different schemes: the allowed one proves a working tunnel (200), the
    # refused one proves a deny is being enforced (403). A 000 on the second means the proxy is
    # unreachable, a different fault with the same appearance (Lesson 42).
    echo "--- egress check: an allowed name, then a refused destination"
    echo "    pypi.org over https (must be 200): $(curl -s -o /dev/null -w '%%{http_code}' --max-time 20 --proxy "$PROXY" https://pypi.org/ || true)"
    echo "    10.31.0.1 over http, a PRIVATE address (must be 403): $(curl -s -o /dev/null -w '%%{http_code}' --max-time 20 --proxy "$PROXY" http://10.31.0.1/ || true)"

    mkdir -p /opt/awsds
    chown ec2-user:ec2-user /opt/awsds

    cat > /etc/profile.d/awsds-buildbox.sh <<'BANNER'
    echo
    echo "  awsds buildbox - the amd64 build host. [E]: destroyed at the end of the session."
    echo "  You are $(id -un). Session Manager gives you passwordless sudo; the docker group"
    echo "  belongs to ec2-user, so use  sudo docker ...  or  sudo -iu ec2-user"
    echo
    echo "  The internet here is a proxy, and nothing reaches it without being told:"
    echo "    $PROXY   - already set for shells, dnf, the docker daemon and build containers"
    echo "    a hang, not a refusal, is the shape of a client that was not told"
    echo "    this plane is open since 2026-09-08: any public name, all of it logged"
    echo "    a 403 means a global deny - a private destination, or a port nobody named"
    echo
    echo "  build context (after ./scripts/buildbox.py sync):  /opt/awsds/images"
    echo "  first-boot log:                                    /var/log/awsds-buildbox-boot.log"
    echo
    BANNER

    echo "=== awsds buildbox first boot done: $(date -Is) ==="
  EOT
}
