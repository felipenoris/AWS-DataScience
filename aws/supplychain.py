#!/usr/bin/env -S uv run --quiet
# supplychain.py - Stage 7's evidence, producer and consumers side by side: the GitLab host
# and its [D] state, the runner ([E] - absent between sessions is the design), the [P]
# anchors a rebuild depends on (object/backup buckets, the gitlab-secrets container), the
# TLS surface (imported ACM leaves and their expiry - ACM does NOT renew imports - the DNS
# records, the one-source CA root parameter), the registries (ECR repositories with tag
# immutability and scan-on-push, the pull-through cache rules, the CodeArtifact domain and
# its policy), and the cross-account consumer reads that are INT-01/INT-02's mechanical
# half.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/supplychain.py                    # every awsds-* profile
#             ./aws/supplychain.py awsds-infra-prod   # only the ones named
#             python3 aws/supplychain.py -            # CloudShell, ambient credentials
#   writes:   aws/output/supplychain.txt   (untracked - see .gitignore)
#   reads:    ec2:DescribeInstances, DescribeSecurityGroups, dlm:GetLifecyclePolicies,
#             s3api:ListBuckets, GetBucketVersioning, secretsmanager:DescribeSecret,
#             acm:ListCertificates, DescribeCertificate, ssm:GetParameter,
#             route53:ListHostedZones, ListResourceRecordSets, ecr:DescribeRepositories,
#             GetRegistryScanningConfiguration, DescribePullThroughCacheRules,
#             GetLifecyclePolicy, DescribeImages, codeartifact:ListDomains,
#             ListRepositoriesInDomain, DescribeRepository, GetDomainPermissionsPolicy,
#             GetRepositoryEndpoint, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything. It never reads a secret VALUE:
#             the gitlab-secrets check is DescribeSecret metadata only, on purpose - a
#             report file must not contain what Secrets Manager exists to hold.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. D14 puts the
# registries in Production while every legitimate consumer is an Interactive account, so
# "does the consumer map reach everyone" (Lesson 14) is only readable from BOTH sides: the
# policies from Production, and a cross-account read from each consumer - a denied read
# from a consumer that should be in the map IS the finding. Section 1 pays the rule back
# with the caller ARN of every profile.
#
# CONTRACTS THIS FILE READS, each named in the stage file so a rename fails loudly:
#   - the GitLab host's Name tag is awsds-prod-gitlab (Stage 7 step 1.2)
#   - the runner's Name tag matches awsds-prod-runner* (step 6.1)
#   - the required ECR repositories are awsds-prod-ecr-base and awsds-prod-ecr-dev-env,
#     tag-immutable (step 5.1)
#   - the CodeArtifact domain is awsds-prod-packages, repositories pypi and crates (5.3)
#   - the secret container is awsds-prod-gitlab-secrets (step 1.1)
#   - the CA root parameter is /datascience/prod/pki/ca-root-pem (step 2.3)
#
# WHAT IT CANNOT SEE, stated because an empty listing and a missing account look alike:
#   - The behavioural proofs - the clone pair, the SAML round-trip, the restore rehearsal,
#     the TLS triple on the three client surfaces (INT-19) - are the stage's own
#     (Lesson 20). A describe call cannot shake hands with a certificate.
#   - Whether the backup → destroy → restore path works (step 8.2) is a rehearsal, not a
#     reading; this file only shows the anchors it depends on.
#   - GitLab's own objects - groups, protected tags, mirror settings - live behind
#     gitlab.prod.internal, which no AWS API reads.

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog, head2
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "supplychain.txt"

# The producer account and the consumers (D14; D35 - the sandbox side is per unit).
PROD_PROFILE = "awsds-infra-prod"
CONSUMER_PROFILES = ("awsds-infra-sandbox-1", "awsds-infra-dev")

# The contracts (see header).
GITLAB_NAME_TAG = "awsds-prod-gitlab"
RUNNER_NAME_GLOB = "awsds-prod-runner*"
REQUIRED_REPOS = ("awsds-prod-ecr-base", "awsds-prod-ecr-dev-env")
CA_DOMAIN = "awsds-prod-packages"
CA_REPOS = ("pypi", "crates")
SECRET_NAME = "awsds-prod-gitlab-secrets"
CA_ROOT_PARAM = "/datascience/prod/pki/ca-root-pem"
ZONES = ("prod.internal.", "pages.internal.")
LEAF_EXPIRY_WARN_DAYS = 45


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c.profile for c in callers if c.live]
    checks = Checks()

    prod_live = PROD_PROFILE in live
    prod_account = next((c.account for c in callers if c.profile == PROD_PROFILE), None)

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    def logerr(profile: str, what: str, err: str) -> None:
        errors.entries.append(f"[{profile}] aws {what}\n    {head2(err)}")

    # ------------------------------------------------- the two instances (tooling, runners)
    host_rows: list = []  # (name, id, type, state, imdsv2, sg ids)
    runner_rows: list = []
    host_sg_ids: list = []
    dlm_policies: list = []  # (id, state, description)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        note(f"measuring {PROD_PROFILE} ...")
        for tag, into in ((GITLAB_NAME_TAG, host_rows), (RUNNER_NAME_GLOB, runner_rows)):
            res = cli.run(
                "ec2",
                "describe-instances",
                "--filters",
                f"Name=tag:Name,Values={tag}",
                "Name=instance-state-name,Values=pending,running,stopping,stopped",
                "--query",
                "Reservations[].Instances[].[Tags[?Key=='Name']|[0].Value,InstanceId,"
                "InstanceType,State.Name,MetadataOptions.HttpTokens,"
                "join(' ',SecurityGroups[].GroupId)]",
                "--output",
                "json",
                log=False,
            )
            if not res.ok:
                logerr(PROD_PROFILE, f"ec2 describe-instances ({tag})", res.stderr)
                continue
            for row in json.loads(res.stdout or "[]"):
                into.append(tuple(str(x) for x in row))
        host_sg_ids = sorted({sg for r in host_rows for sg in (r[5] or "").split() if sg})
        res = cli.run(
            "dlm",
            "get-lifecycle-policies",
            "--query",
            "Policies[].[PolicyId,State,Description]",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            dlm_policies = [tuple(str(x) for x in r) for r in json.loads(res.stdout or "[]")]

    # ------------------------------------ the host SGs: nothing world-open on this instance
    sg_world_open: list = []  # (sg id, proto, port range, cidr)
    if prod_live and host_sg_ids:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "ec2",
            "describe-security-groups",
            "--group-ids",
            *host_sg_ids,
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            for sg in json.loads(res.stdout or "{}").get("SecurityGroups", []):
                for perm in sg.get("IpPermissions", []):
                    for rng in perm.get("IpRanges", []):
                        if rng.get("CidrIp") == "0.0.0.0/0":
                            sg_world_open.append(
                                (
                                    sg.get("GroupId", "?"),
                                    str(perm.get("IpProtocol", "?")),
                                    f"{perm.get('FromPort', '-')}-{perm.get('ToPort', '-')}",
                                    "0.0.0.0/0",
                                )
                            )

    # ----------------------------------------------- the [P] anchors: buckets, the secret
    gitlab_buckets: list = []  # (name, versioning or '-')
    secret_state = "(not measured)"
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "s3api",
            "list-buckets",
            "--query",
            "Buckets[].Name",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            for name in json.loads(res.stdout or "[]"):
                if "gitlab" not in name:
                    continue
                r = cli.run(
                    "s3api",
                    "get-bucket-versioning",
                    "--bucket",
                    name,
                    "--query",
                    "Status",
                    "--output",
                    "text",
                    log=False,
                )
                gitlab_buckets.append((name, r.stdout.strip() if r.ok else "(read failed)"))
        res = cli.run(
            "secretsmanager",
            "describe-secret",
            "--secret-id",
            SECRET_NAME,
            "--query",
            "[Name,LastChangedDate]",
            "--output",
            "json",
            log=False,
            tolerate="ResourceNotFoundException",
        )
        if res.tolerated:
            secret_state = "(absent)"
        elif res.ok and res.stdout:
            _name, changed = json.loads(res.stdout)
            secret_state = f"present, last changed {changed or '(never - container only)'}"

    # --------------------------- TLS: imported leaves in ACM, the CA parameter, the records
    acm_rows: list = []  # (domain, type, days-left, arn tail)
    ca_param_state = "(not measured)"
    record_rows: list = []  # (zone, record, type)
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "acm",
            "list-certificates",
            "--query",
            "CertificateSummaryList[].CertificateArn",
            "--output",
            "json",
            log=False,
        )
        for arn in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            r = cli.run(
                "acm",
                "describe-certificate",
                "--certificate-arn",
                arn,
                "--query",
                "Certificate.[DomainName,Type,NotAfter]",
                "--output",
                "json",
                log=False,
            )
            if not r.ok:
                continue
            dom, ctype, not_after = json.loads(r.stdout or "[null,null,null]")
            days = "-"
            if not_after:
                try:
                    dt = datetime.fromisoformat(str(not_after))
                    days = str((dt - datetime.now(timezone.utc)).days)
                except ValueError:
                    days = "?"
            acm_rows.append((str(dom), str(ctype), days, arn.rsplit("/", 1)[-1][:13]))
        res = cli.run(
            "ssm",
            "get-parameter",
            "--name",
            CA_ROOT_PARAM,
            "--query",
            "Parameter.[Version,LastModifiedDate]",
            "--output",
            "json",
            log=False,
            tolerate="ParameterNotFound",
        )
        if res.tolerated:
            ca_param_state = "(absent)"
        elif res.ok and res.stdout:
            version, modified = json.loads(res.stdout)
            ca_param_state = f"present, version {version} ({modified})"
        res = cli.run(
            "route53",
            "list-hosted-zones",
            "--query",
            "HostedZones[?Config.PrivateZone].[Id,Name]",
            "--output",
            "json",
            log=False,
        )
        for zid, zname in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            if zname not in ZONES:
                continue
            r = cli.run(
                "route53",
                "list-resource-record-sets",
                "--hosted-zone-id",
                zid,
                "--query",
                "ResourceRecordSets[?Type!='NS' && Type!='SOA'].[Name,Type]",
                "--output",
                "json",
                log=False,
            )
            for rname, rtype in json.loads(r.stdout or "[]") if r.ok and r.stdout else []:
                record_rows.append((zname, str(rname).replace("\\052", "*"), str(rtype)))

    # ----------------------------------------------------- ECR: repositories and the cache
    ecr_rows: list = []  # (name, mutability, scan-on-push flag, lifecycle?)
    scan_config = "(not measured)"
    ptc_rows: list = []  # (prefix, upstream, credential arn or '-')
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "ecr",
            "describe-repositories",
            "--query",
            "repositories[].[repositoryName,imageTagMutability,"
            "imageScanningConfiguration.scanOnPush]",
            "--output",
            "json",
            log=False,
        )
        for rname, mut, sop in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
            r = cli.run(
                "ecr",
                "get-lifecycle-policy",
                "--repository-name",
                rname,
                "--query",
                "repositoryName",
                "--output",
                "text",
                log=False,
                tolerate="LifecyclePolicyNotFoundException",
            )
            lifecycle = "-" if res.tolerated else ("yes" if r.ok and not r.tolerated else "-")
            ecr_rows.append((str(rname), str(mut), str(sop), lifecycle))
        res = cli.run(
            "ecr",
            "get-registry-scanning-configuration",
            "--query",
            "scanningConfiguration.[scanType,join(' ',rules[].scanFrequency)]",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            stype, freqs = json.loads(res.stdout)
            scan_config = f"{stype} ({freqs or 'no rules'})"
        res = cli.run(
            "ecr",
            "describe-pull-through-cache-rules",
            "--query",
            "pullThroughCacheRules[].[ecrRepositoryPrefix,upstreamRegistryUrl,credentialArn]",
            "--output",
            "json",
            log=False,
        )
        if res.ok and res.stdout:
            ptc_rows = [
                (str(p), str(u), str(c) if c else "-") for p, u, c in json.loads(res.stdout or "[]")
            ]

    # ------------------------------------------------- CodeArtifact: domain, repos, policy
    ca_domain_found = False
    ca_repo_rows: list = []  # (repo, external connections)
    ca_policy_state = "(not measured)"
    if prod_live:
        cli = cli_for(PROD_PROFILE)
        res = cli.run(
            "codeartifact",
            "list-domains",
            "--query",
            "domains[].name",
            "--output",
            "json",
            log=False,
        )
        domains = json.loads(res.stdout or "[]") if res.ok and res.stdout else []
        ca_domain_found = CA_DOMAIN in domains
        if ca_domain_found:
            res = cli.run(
                "codeartifact",
                "list-repositories-in-domain",
                "--domain",
                CA_DOMAIN,
                "--query",
                "repositories[].name",
                "--output",
                "json",
                log=False,
            )
            for rname in json.loads(res.stdout or "[]") if res.ok and res.stdout else []:
                r = cli.run(
                    "codeartifact",
                    "describe-repository",
                    "--domain",
                    CA_DOMAIN,
                    "--repository",
                    rname,
                    "--query",
                    "repository.externalConnections[].externalConnectionName",
                    "--output",
                    "json",
                    log=False,
                )
                conns = json.loads(r.stdout or "[]") if r.ok and r.stdout else []
                ca_repo_rows.append((str(rname), " ".join(conns) or "-"))
            res = cli.run(
                "codeartifact",
                "get-domain-permissions-policy",
                "--domain",
                CA_DOMAIN,
                "--query",
                "policy.document",
                "--output",
                "text",
                log=False,
                tolerate="ResourceNotFoundException",
            )
            if res.tolerated:
                ca_policy_state = "(no domain policy)"
            elif res.ok:
                n = res.stdout.count('"AWS"')
                ca_policy_state = f"present ({n} principal block(s))"

    # ------------------- the consumer reads: INT-01/INT-02's mechanical half, from outside
    consumer_rows: list = []  # (profile, ecr read, codeartifact read)
    if prod_account:
        for p in CONSUMER_PROFILES:
            if p not in live:
                continue
            cli = cli_for(p)
            note(f"measuring {p} (cross-account reads) ...")
            res = cli.run(
                "ecr",
                "describe-images",
                "--registry-id",
                prod_account,
                "--repository-name",
                REQUIRED_REPOS[1],
                "--max-results",
                "1",
                "--query",
                "length(imageDetails)",
                "--output",
                "text",
                log=False,
                tolerate="RepositoryNotFoundException|AccessDenied",
            )
            if res.tolerated:
                ecr_read = "(denied or no repository)"
            elif res.ok:
                ecr_read = f"ok ({res.stdout.strip()} image(s) visible)"
            else:
                ecr_read = "(call failed)"
            res = cli.run(
                "codeartifact",
                "get-repository-endpoint",
                "--domain",
                CA_DOMAIN,
                "--domain-owner",
                prod_account,
                "--repository",
                CA_REPOS[0],
                "--format",
                "pypi",
                "--query",
                "repositoryEndpoint",
                "--output",
                "text",
                log=False,
                tolerate="ResourceNotFoundException|AccessDenied",
            )
            if res.tolerated:
                ca_read = "(denied or no domain)"
            elif res.ok:
                ca_read = "ok (endpoint answered)"
            else:
                ca_read = "(call failed)"
            consumer_rows.append((p, ecr_read, ca_read))

    # -------------------------------------------------------------------------- the checks
    built = bool(host_rows)  # the stage's first slice landed: notes become regressions

    # SC-1: the GitLab host under its contracted Name tag, IMDSv2 required. Stopped is [D]
    # working, not an outage.
    if prod_live:
        if not host_rows:
            checks.note(
                "SC-1",
                "the GitLab host",
                "none - expected before Stage 7 step 1.",
            )
        else:
            for name, iid, itype, state, tokens, _sgs in host_rows:
                detail = f"{itype}, {state}, IMDSv2={tokens}"
                if tokens != "required":
                    checks.fail("SC-1", f"IMDSv2 on {iid}", f"HttpTokens={tokens} - not enforced.")
                else:
                    checks.ok("SC-1", f"the GitLab host ({iid})", detail)

    # SC-2: nothing world-open on the host's SGs - the one world-open rule in the whole
    # organization is WireGuard's UDP/51820 (Stage 4 step 3), and it is not here.
    if prod_live and host_rows:
        if sg_world_open:
            checks.fail(
                "SC-2",
                "world-open rule on the GitLab SGs",
                f"{len(sg_world_open)} rule(s) admit 0.0.0.0/0 - the host is VPN-reached "
                "through the peering; nothing here may be world-open.",
            )
        else:
            checks.ok("SC-2", "the GitLab SGs", "no world-open ingress")

    # SC-3: the [P] anchors - buckets and the secret container (step 1.1). The backup
    # bucket must be versioned; the secret may legitimately be a container with no value
    # until first boot (step 1.5).
    if prod_live:
        backup = [b for b in gitlab_buckets if "backup" in b[0]]
        objects = [b for b in gitlab_buckets if "object" in b[0]]
        if not gitlab_buckets:
            checks.note("SC-3", "the GitLab buckets", "none - expected before Stage 7 step 1.")
        else:
            if backup and backup[0][1] != "Enabled":
                checks.fail(
                    "SC-3",
                    f"versioning on {backup[0][0]}",
                    f"'{backup[0][1]}' - the restore path depends on this bucket.",
                )
            elif backup:
                checks.ok("SC-3", "the backup bucket", f"{backup[0][0]}, versioned")
            if not objects:
                checks.note("SC-3", "the object-storage bucket", "no *object* bucket found.")
        if secret_state == "(absent)":
            (checks.fail if built else checks.note)(
                "SC-3",
                "the gitlab-secrets container",
                f"{SECRET_NAME} absent - "
                + ("a restore cannot decrypt without it." if built else "expected before step 1."),
            )
        elif secret_state.startswith("present"):
            checks.ok("SC-3", "the gitlab-secrets container", secret_state)

    # SC-4: the two required repositories exist, tag-IMMUTABLE (the Stage 8 premise).
    if prod_live:
        have = {r[0]: r for r in ecr_rows}
        for rname in REQUIRED_REPOS:
            if rname not in have:
                checks.note("SC-4", f"repository {rname}", "absent - expected before step 5.")
            elif have[rname][1] != "IMMUTABLE":
                checks.fail(
                    "SC-4",
                    f"tag immutability on {rname}",
                    f"{have[rname][1]} - Stage 8's approved-digest chain stands on "
                    "immutable tags (step 5.1).",
                )
            else:
                checks.ok("SC-4", f"repository {rname}", "IMMUTABLE")

    # SC-5: the pull-through cache repositories must NOT be tag-immutable (the documented
    # trap: an immutable tag blocks the cache update).
    if prod_live and ptc_rows:
        prefixes = tuple(p for p, _u, _c in ptc_rows)
        stuck = [
            r[0]
            for r in ecr_rows
            if r[1] == "IMMUTABLE" and any(r[0].startswith(pfx) for pfx in prefixes)
        ]
        if stuck:
            checks.fail(
                "SC-5",
                "immutable cache repositories",
                f"{', '.join(stuck[:3])} - an immutable tag blocks the pull-through "
                "cache update (step 5.2's trap).",
            )
        else:
            checks.ok("SC-5", f"{len(ptc_rows)} cache rule(s)", "no immutable cache repository")
    elif prod_live and built and not ptc_rows:
        checks.note("SC-5", "pull-through cache rules", "none - step 5.2 creates them.")

    # SC-6: the CodeArtifact domain, its two repositories with external connections, and a
    # domain policy (INT-02's provider half).
    if prod_live:
        if not ca_domain_found:
            checks.note("SC-6", f"CodeArtifact domain {CA_DOMAIN}", "absent - before step 5.")
        else:
            have = {r[0] for r in ca_repo_rows}
            missing = [r for r in CA_REPOS if r not in have]
            if missing:
                checks.fail(
                    "SC-6",
                    "CodeArtifact repositories",
                    f"missing {', '.join(missing)} - step 5.3's contract.",
                )
            else:
                checks.ok("SC-6", "CodeArtifact repositories", "pypi and crates exist")
            if ca_policy_state == "(no domain policy)":
                checks.fail(
                    "SC-6",
                    "the domain policy",
                    "absent - the consumers of INT-02 are granted here (step 5.4).",
                )
            elif ca_policy_state.startswith("present"):
                checks.ok("SC-6", "the domain policy", ca_policy_state)

    # SC-7: the consumer reads answer from both Interactive accounts - a deny once the
    # registry exists means the D35 map missed a consumer (Lesson 14).
    for p, ecr_read, ca_read in consumer_rows:
        for label, reading, exists in (
            ("ECR", ecr_read, any(r[0] == REQUIRED_REPOS[1] for r in ecr_rows)),
            ("CodeArtifact", ca_read, ca_domain_found),
        ):
            if reading.startswith("ok"):
                checks.ok("SC-7", f"{label} cross-account read from {p}", reading)
            elif exists:
                checks.fail(
                    "SC-7",
                    f"{label} cross-account read from {p}",
                    f"{reading} - the resource exists in Production, so the consumer "
                    "map (step 5.4) is missing this account.",
                )
            else:
                checks.note("SC-7", f"{label} read from {p}", "nothing to read yet.")

    # SC-8: imported leaves and their runway - ACM does not renew imports (step 2.4).
    imported = [r for r in acm_rows if r[1] == "IMPORTED"]
    if prod_live and imported:
        for dom, _t, days, tail in imported:
            try:
                d = int(days)
            except ValueError:
                d = -1
            if 0 <= d < LEAF_EXPIRY_WARN_DAYS:
                checks.fail(
                    "SC-8",
                    f"leaf {dom} ({tail})",
                    f"{d} day(s) to expiry - ACM does not renew imports; re-import now.",
                )
            else:
                checks.ok("SC-8", f"leaf {dom}", f"{days} day(s) of runway")
    elif prod_live and built and not imported:
        checks.note(
            "SC-8",
            "imported certificates",
            "none in ACM - the nginx option (decision 1) serves leaves from the "
            "instance; expiry is then watched through the log's re-import date.",
        )

    # SC-9: the one-source CA root parameter (step 2.3, INT-19).
    if prod_live:
        if ca_param_state == "(absent)":
            (checks.fail if built else checks.note)(
                "SC-9",
                "the CA root parameter",
                f"{CA_ROOT_PARAM} absent - "
                + (
                    "the runner and image builds have no one source (Lesson 14)."
                    if built
                    else "expected before step 2.3."
                ),
            )
        elif ca_param_state.startswith("present"):
            checks.ok("SC-9", "the CA root parameter", ca_param_state)

    # SC-10: the runner is [E] - absent between sessions is D11 working; present is a burn
    # to be aware of, not a failure.
    if prod_live:
        running = [r for r in runner_rows if r[3] == "running"]
        if running:
            checks.note(
                "SC-10",
                f"{len(running)} runner(s) running",
                "metered by the hour - expected during a session, a leak after "
                "`make down` (./aws/egress.py section 6 is the burn meter).",
            )
        elif runner_rows:
            checks.note("SC-10", "runner present but not running", "destroy it - runners are [E].")
        elif built:
            checks.ok("SC-10", "no runner instance", "[E] between sessions is D11 working")

    # ---------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Supply chain - the Stage 7 evidence: GitLab, TLS, registries, consumers")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/supplychain.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The GitLab host and the runner (tooling [D], runners [E])
  3. The [P] anchors: buckets and the gitlab-secrets container
  4. TLS: imported leaves, the CA root parameter, the DNS records
  5. ECR: repositories, scanning, the pull-through cache
  6. CodeArtifact: the domain, its repositories, the domain policy
  7. The consumer reads, from each Interactive account (INT-01/INT-02)
  8. CHECKS
  9. The accounts nothing here is measuring
 10. Calls that failed

HOW TO READ THIS FILE
  - "NOT BUILT YET" IS THE EXPECTED ANSWER UNTIL STAGE 7 RUNS - each such reading
    is a note, not a failure; it becomes a regression the moment the stage closes.
    Pass 0 (pki/, registry/) lands BEFORE Stage 6, so sections 5-7 fill up first.
  - A STOPPED GitLab host is [D] working, not an outage. An ABSENT runner is [E]
    working. A MISSING ACCOUNT is not a passing account - section 9.
  - THIS IS A CONTROL-PLANE READING. The clone pair, the SAML round-trip, the
    restore rehearsal and the TLS triple (INT-19) are behavioural proofs the
    stage runs itself (Lesson 20).

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

        # ==============================================================================
        rep.h1("1. Which accounts were measured, and as whom")
        rep.text("""A profile is an (account, permission set) pair; every awsds-* profile here resolves
to the infrastructure user. A `(failed)` row is a profile that did not authenticate,
never a compliant one.

""")
        rep.tabulate(
            ["PROFILE\tACCOUNT\tCALLER ARN"]
            + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
        )

        # ==============================================================================
        rep.h1("2. The GitLab host and the runner (tooling [D], runners [E])")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            rows = ["INSTANCE\tID\tTYPE\tSTATE\tIMDSV2\tSECURITY GROUPS"]
            for r in host_rows + runner_rows:
                rows.append("\t".join(r))
            if host_rows or runner_rows:
                rep.tabulate(rows)
            else:
                rep.line("No instance under either Name tag. Expected before Stage 7.")
            rep.line()
            if sg_world_open:
                rep.tabulate(["SG\tPROTO\tPORTS\tSOURCE"] + ["\t".join(r) for r in sg_world_open])
            elif host_rows:
                rep.line("No world-open ingress on the host's security groups.")
            rep.line()
            if dlm_policies:
                rep.tabulate(
                    ["DLM POLICY\tSTATE\tDESCRIPTION"] + ["\t".join(r) for r in dlm_policies]
                )
            else:
                rep.line("No DLM snapshot policy. Expected before Stage 7 step 1.2.")

        # ==============================================================================
        rep.h1("3. The [P] anchors: buckets and the gitlab-secrets container")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            if gitlab_buckets:
                rep.tabulate(
                    ["BUCKET\tVERSIONING"] + [f"{n}\t{v or '-'}" for n, v in gitlab_buckets]
                )
            else:
                rep.line("No gitlab-named bucket. Expected before Stage 7 step 1.1.")
            rep.line()
            rep.line(f"{SECRET_NAME}: {secret_state}")
            rep.text("""
Metadata only, on purpose: this file never calls GetSecretValue - a report must
not contain what Secrets Manager exists to hold. "container only" (no change
date) is the expected state between creation (1.1) and the first boot (1.5).""")

        # ==============================================================================
        rep.h1("4. TLS: imported leaves, the CA root parameter, the DNS records")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            if acm_rows:
                rep.tabulate(
                    ["DOMAIN\tTYPE\tDAYS LEFT\tARN TAIL"] + ["\t".join(r) for r in acm_rows]
                )
            else:
                rep.line("No certificate in ACM (the nginx option needs none - decision 1).")
            rep.line()
            rep.line(f"{CA_ROOT_PARAM}: {ca_param_state}")
            rep.line()
            if record_rows:
                rep.tabulate(["ZONE\tRECORD\tTYPE"] + ["\t".join(r) for r in record_rows])
            else:
                rep.line("No record in prod.internal / pages.internal beyond NS/SOA yet.")

        # ==============================================================================
        rep.h1("5. ECR: repositories, scanning, the pull-through cache")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        else:
            if ecr_rows:
                rep.tabulate(
                    ["REPOSITORY\tTAGS\tSCAN-ON-PUSH(legacy flag)\tLIFECYCLE"]
                    + ["\t".join(r) for r in ecr_rows]
                )
            else:
                rep.line("No repository. Expected before pass 0 (step 5).")
            rep.line()
            rep.line(f"Registry scanning configuration: {scan_config}")
            rep.line()
            if ptc_rows:
                rep.tabulate(
                    ["CACHE PREFIX\tUPSTREAM\tCREDENTIAL"] + ["\t".join(r) for r in ptc_rows]
                )
            else:
                rep.line("No pull-through cache rule. Expected before step 5.2.")
            rep.text("""
The scanning line is the decision-2 reading: BASIC is the recommended free path
(the Stage 8 gate reads DescribeImageScanFindings either way); ENHANCED is the
Stage 11 upgrade, measured at 0.09/image + 0.01/re-scan.""")

        # ==============================================================================
        rep.h1("6. CodeArtifact: the domain, its repositories, the domain policy")
        if not prod_live:
            rep.line(f"{PROD_PROFILE} was not measured - nothing to show.")
        elif not ca_domain_found:
            rep.line(f"No domain named {CA_DOMAIN}. Expected before pass 0 (step 5.3).")
        else:
            rep.tabulate(
                ["REPOSITORY\tEXTERNAL CONNECTIONS"] + ["\t".join(r) for r in ca_repo_rows]
            )
            rep.line()
            rep.line(f"Domain policy: {ca_policy_state}")
            rep.text("""
Presence, never sufficiency: whether the policy's principal list matches the
D35 consumer map is read against the .tfvars, and the behavioural proof is the
consumer read in section 7 (and Stage 6's package install, INT-02).""")

        # ==============================================================================
        rep.h1("7. The consumer reads, from each Interactive account (INT-01/INT-02)")
        if not consumer_rows:
            rep.line("No consumer profile was measured (or Production was not).")
        else:
            rep.tabulate(
                ["PROFILE\tECR describe-images\tCODEARTIFACT get-repository-endpoint"]
                + ["\t".join(r) for r in consumer_rows]
            )
        rep.text("""
Each row is a real cross-account read exercising the resource policies from the
consumer's side - the direction a describe call in Production cannot see. A
denied read AFTER the registry exists is the D35 map missing a consumer
(Lesson 14) - SC-7 fails on exactly that.""")

        # ==============================================================================
        rep.h1("8. CHECKS")
        rep.checks_table(checks)
        n_fail = checks.n_fail()
        rep.line()
        rep.line(f"{n_fail} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  SC-1   the GitLab host under its Name tag, IMDSv2 required (step 1.2)
  SC-2   nothing world-open on the host's SGs (Stage 4 step 3's rule)
  SC-3   the [P] anchors: versioned backup bucket, the secret container (1.1)
  SC-4   base and dev-env repositories exist, tag-IMMUTABLE (5.1; Stage 8)
  SC-5   no immutable pull-through cache repository (5.2's documented trap)
  SC-6   the CodeArtifact domain, pypi + crates, a domain policy (5.3-5.4)
  SC-7   the cross-account reads answer from every consumer (INT-01/INT-02)
  SC-8   imported leaves have runway - ACM does not renew imports (2.4)
  SC-9   the CA root parameter exists - INT-19's one source (2.3)
  SC-10  the runner reported as the [E] burn it is (6.1, D11)""")

        # ==============================================================================
        rep.h1("9. The accounts nothing here is measuring")
        rep.text("""Read this BEFORE reading section 8 as a pass.

  - `Staging` has no profile until the vend - and is deliberately NOT in the
    consumer map: it pulls images through the pipeline's roles (INT-07,
    Stage 8), not through a standing grant.
  - Every Sandbox beyond unit 1 has no profile until Stage 14 - re-run after
    each vend: the consumer map and section 7 must both grow with N (D35).
  - GitLab's own objects (groups, protected tags, mirrors) live behind
    gitlab.prod.internal - no AWS API reads them; the stage log does.""")

        # ==============================================================================
        rep.h1("10. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/supplychain.py")

    # ------------------------------------------------------------------------------ run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 8)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
