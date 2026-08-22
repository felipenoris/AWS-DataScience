# The first boot. It installs a toolchain and nothing else - no build runs here.
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

locals {
  user_data = <<-EOT
    #!/bin/bash
    set -euo pipefail
    exec > >(tee /var/log/awsds-buildbox-boot.log) 2>&1
    echo "=== awsds buildbox first boot: $(date -Is) ==="

    # docker AND git: git because a build context is usually a checkout, and because the
    # dev-env image's own INT-09 story starts with one. Both come from the AL2023 repository,
    # which this tier reaches through foundation/'s S3 GATEWAY endpoint - so this step works
    # even if the route through the WireGuard host is not up yet, and its success proves
    # nothing about that route (Lesson 13: the reading that follows is what proves it).
    echo "--- installing docker and git"
    dnf -y install docker git

    echo "--- enabling docker"
    systemctl enable --now docker
    usermod -aG docker ec2-user

    # THE EGRESS READING, TAKEN ONCE AND LEFT IN THE LOG. If the route or the masquerade is
    # wrong, every later symptom is a timeout that looks like a broken mirror; this line is
    # what tells the two apart, and it is why it prints the address rather than just "ok" -
    # the address returned must be the WireGuard host's Elastic IP, because that host is the
    # single public egress by design. Anything else means traffic is leaving another way.
    echo "--- egress check: the public address this host leaves under"
    curl -s --max-time 20 https://checkip.amazonaws.com/ || echo "NO EGRESS - the route through the WireGuard host is not working"

    mkdir -p /opt/awsds
    chown ec2-user:ec2-user /opt/awsds

    cat > /etc/profile.d/awsds-buildbox.sh <<'BANNER'
    echo
    echo "  awsds buildbox - Stage 6 step 5.0's build host. [E]: destroyed at the end of the session."
    echo "  You are $(id -un). Session Manager gives you passwordless sudo; the docker group"
    echo "  belongs to ec2-user, so use  sudo docker ...  or  sudo -iu ec2-user"
    echo
    echo "  build context (after ./scripts/buildbox.py sync):  /opt/awsds/images"
    echo "  first-boot log:                                    /var/log/awsds-buildbox-boot.log"
    echo
    BANNER

    echo "=== awsds buildbox first boot done: $(date -Is) ==="
  EOT
}
