# The first boot. It installs a toolchain, TELLS EVERY CLIENT ON THE HOST ABOUT THE PROXY, and
# runs nothing else - no build happens here.
#
# WHY THE BUILD IS NOT IN THE USER DATA, which is the obvious thing to try: user data runs
# once, unattended, with its output in a log nobody is watching, and a container build is an
# iterative act whose whole value is watching it fail. This host is a place to build FROM a
# session, not a build that happens to leave a host behind. The build context arrives with
# `./scripts/buildbox.py sync`, which can be re-run against a running host; baking it in here
# was measured and rejected - a gzip+base64 of images/ is ~27 KB against user data's 16 KB
# ceiling, and it would make every Dockerfile edit REPLACE the host (user_data_replace_on_
# change), which is the opposite of what iterating wants.
#
# THE SHELL LANDS AS ssm-user, NOT AS ec2-user, and that is the one surprise worth writing
# into the banner rather than into a runbook nobody opens: Session Manager creates ssm-user on
# its first connection - it does not exist while this script runs, so it cannot be added to
# the docker group here - and it has passwordless sudo. So `sudo docker ...` works out of the
# box, and `sudo -iu ec2-user` gets a shell in the docker group for anyone who prefers it.
#
# ---------------------------------------------------------------------------------------------
# THE PROXY, AND WHY IT TAKES FOUR PLACES RATHER THAN ONE (6c step 5.8, 2026-09-06)
#
# There is no default route in this tier. An explicit proxy is not transparent: a client that has
# not been told about it does not fail over to it, it simply hangs. Four different things on this
# host open connections and each reads the setting from a different place - which is Lesson 14 in
# its most literal form, one intent that must appear in four files or it is missing from one:
#
#   1. /etc/environment          every login shell and everything systemd starts with
#                                EnvironmentFile. This is what `curl`, `git`, `pip` and `dnf`
#                                read. BOTH CASES ARE WRITTEN - `http_proxy` and `HTTP_PROXY` -
#                                because clients disagree about which they honour and the
#                                disagreement is silent.
#   2. the docker DAEMON         a systemd drop-in. The daemon is what pulls a base image, and it
#                                is NOT a child of the shell, so it never sees /etc/environment.
#                                A `docker pull` from a shell with a perfect environment still
#                                hangs without this file, and the symptom names the registry
#                                rather than the proxy.
#   3. the docker CLIENT's       ~/.docker/config.json `proxies` block, which is what injects
#      BUILD containers          http_proxy into `RUN` steps. Without it the daemon can pull the
#                                base image and every `pip install` inside the build hangs.
#   4. dnf                       THE ENVIRONMENT, AND EXPLICITLY *NOT* `proxy=` IN dnf.conf. This
#                                was written the other way round first and it broke the first boot
#                                (measured 2026-09-06): `dnf.conf` has a `proxy=` setting and NO
#                                exclusion setting to go with it, so setting it sends EVERYTHING at
#                                the proxy - including the AL2023 repositories, which live on S3 and
#                                must go direct through the gateway endpoint. The proxy refused them
#                                with a 403 (a build host's plane deliberately excludes
#                                `.amazonaws.com`) and `dnf` reported `Failed to download metadata`,
#                                which reads as a broken mirror. dnf goes through libcurl, which
#                                honours `http_proxy`/`no_proxy` from the environment - so the
#                                environment is the only place that can express both halves.
#
# WHAT MUST NOT GO THROUGH IT, and this half is the one that fails quietly in the other
# direction: `no_proxy` is GENERATED from this VPC's endpoint list (5.6) and carries the SSM
# names. Session Manager is how anyone gets a shell here, so a `no_proxy` that missed
# `ssmmessages.<region>.amazonaws.com` would send the agent's websocket at Squid and lock the
# host out of its own management path - on a host whose only door that is. It also carries the
# S3 and DynamoDB names IN BOTH SPELLINGS - plain and `dualstack` - which no endpoint list can
# produce (a gateway endpoint has no private DNS at all) and which carry the LAYERS of every
# image pull AND the AL2023 repositories. The dualstack form was added at
# `vpc-egress-v0.9.1` after this host's first boot failed on precisely its absence.
# ---------------------------------------------------------------------------------------------

locals {
  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail
    exec > >(tee /var/log/awsds-buildbox-boot.log) 2>&1
    echo "=== awsds buildbox first boot: $(date -Is) ==="

    PROXY="${local.proxy_url}"
    NOPROXY="${local.no_proxy}"

    # AND IN THIS SCRIPT'S OWN ENVIRONMENT, which /etc/environment does NOT provide: that file is
    # read by PAM at login and by systemd units that name it, and cloud-init's user data is
    # neither. Without these four lines every command below runs with no proxy at all - which is
    # the shape of a first boot that "works" until something needs the internet.
    export http_proxy="$PROXY" https_proxy="$PROXY"
    export HTTP_PROXY="$PROXY" HTTPS_PROXY="$PROXY"
    export no_proxy="$NOPROXY" NO_PROXY="$NOPROXY"

    # (1) EVERY SHELL AND EVERY systemd UNIT THAT READS THIS FILE. Both cases, deliberately.
    echo "--- proxy: /etc/environment"
    cat >> /etc/environment <<ENVEOF
    http_proxy=$PROXY
    https_proxy=$PROXY
    HTTP_PROXY=$PROXY
    HTTPS_PROXY=$PROXY
    no_proxy=$NOPROXY
    NO_PROXY=$NOPROXY
    ENVEOF

    # (4) dnf IS CONFIGURED BY THE `export` ABOVE AND BY NOTHING ELSE. A `proxy=` line in
    # /etc/dnf/dnf.conf stood here and is deliberately gone: dnf.conf has a proxy setting and no
    # exclusion setting to pair with it, so it would send the AL2023 repositories - which are on
    # S3 and must go direct through the gateway endpoint - at a proxy whose plane refuses
    # `.amazonaws.com`. That is what broke this host's first boot on 2026-09-06.

    # docker AND git: git because a build context is usually a checkout, and because the
    # dev-env image's own INT-09 story starts with one.
    echo "--- installing docker and git"
    dnf -y install docker git

    # (2) THE DAEMON. Not a child of any shell, so /etc/environment never reaches it. This is
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

    # (3) THE BUILD CONTAINERS. `proxies` in the CLIENT's config is what injects http_proxy into
    # every RUN step; without it the base image pulls and the first `pip install` inside the
    # build hangs. Written for BOTH accounts that run docker on this host - root (the ssm-user
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

    # THE EGRESS READING, TAKEN ONCE AND LEFT IN THE LOG - AND IT IS TWO READINGS, BECAUSE ONE
    # WOULD NOT BE A VERIFICATION (Lesson 13). The first name is on this host's plane and must
    # return 200; the second is deliberately NOT on any plane and must return 403 FROM SQUID. A
    # boot log showing 200 then 403 says the proxy is up, the peering route works, and the
    # allow-list is being enforced. 000 on both says the proxy is unreachable; 403 on both says
    # this plane is empty or wrong.
    #
    # IT NO LONGER PRINTS THE EXIT ADDRESS, and the reason is the control rather than an
    # oversight: `checkip.amazonaws.com` would answer that question and this plane refuses
    # `.amazonaws.com` on purpose - a build host has no business calling the AWS control plane
    # through the proxy, since everything it legitimately calls has an endpoint. The address is
    # measured from the TUNNEL plane instead, at 6c step 6.1.
    # AND THE REFUSED PROBE IS `http://`, NOT `https://`, WHICH IS NOT A DETAIL. Measured
    # 2026-09-06: over https the client asks for a CONNECT tunnel, Squid refuses it, and `curl`
    # reports `%%{http_code}` as **000** because no HTTP response ever crossed the tunnel - the
    # 403 exists but is on the CONNECT, where this format string cannot see it. Over http the
    # refusal IS the response and reads as a plain 403 whose body names Squid. So the two probes
    # deliberately use different schemes: the allowed one proves a working tunnel (200), the
    # refused one proves the allow-list is being enforced (403). A 000 on the second would mean
    # the proxy is unreachable, which is a different fault with the same appearance (Lesson 42).
    echo "--- egress check: an allowed name, then a refused one"
    echo "    pypi.org over https (must be 200): $(curl -s -o /dev/null -w '%%{http_code}' --max-time 20 --proxy "$PROXY" https://pypi.org/ || true)"
    echo "    example.com over http (must be 403): $(curl -s -o /dev/null -w '%%{http_code}' --max-time 20 --proxy "$PROXY" http://example.com/ || true)"

    mkdir -p /opt/awsds
    chown ec2-user:ec2-user /opt/awsds

    cat > /etc/profile.d/awsds-buildbox.sh <<'BANNER'
    echo
    echo "  awsds buildbox - the amd64 build host. [E]: destroyed at the end of the session."
    echo "  You are $(id -un). Session Manager gives you passwordless sudo; the docker group"
    echo "  belongs to ec2-user, so use  sudo docker ...  or  sudo -iu ec2-user"
    echo
    echo "  THE INTERNET HERE IS A PROXY, and nothing reaches it without being told:"
    echo "    $PROXY   - already set for shells, dnf, the docker daemon and build containers"
    echo "    a hang, not a refusal, is the shape of a client that was not told"
    echo "    a 403 naming a host means that name is not on this plane's allow-list"
    echo
    echo "  build context (after ./scripts/buildbox.py sync):  /opt/awsds/images"
    echo "  first-boot log:                                    /var/log/awsds-buildbox-boot.log"
    echo
    BANNER

    echo "=== awsds buildbox first boot done: $(date -Is) ==="
  EOT
}
