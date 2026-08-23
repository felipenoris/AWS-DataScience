#!/usr/bin/env -S uv run --quiet
# dns-allowlist.py - re-resolve every name on the Interactive egress allow-lists and report
# which ones still have their whole resolution chain inside the list they sit on.
#
#   needs:    NOTHING, in the default mode - no SSO session, no profile, no AWS call. It
#             reads this repository's own .tf and asks a resolver. `dig` must be on PATH.
#             `--from-api PROFILE` is the AWS mode and needs a live session:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/dns-allowlist.py                    the lists as CODE declares them
#             ./aws/dns-allowlist.py --whois            + who owns each answer address
#             ./aws/dns-allowlist.py --from-api awsds-infra-sandbox ...
#                                                       the lists as DEPLOYED (slice must be up)
#             ./aws/dns-allowlist.py --resolver 1.1.1.1 ask a specific resolver
#   writes:   aws/output/dns-allowlist.txt   (untracked - see .gitignore)
#   reads:    DNS, and `whois` only with --whois. With --from-api, two read-only calls:
#             route53resolver:ListFirewallDomainLists and ListFirewallDomains. This script
#             never creates, updates or deletes anything.
#
# WHY THIS EXISTS. docs/AWS_STATE.md EXC-05: DNS Firewall evaluates the WHOLE resolution
# chain, so a name is allowed only if every hop it takes is also on the list. Eight of the
# nine external names these lists carry are CDN-fronted and resolve only because their
# authoritative side FLATTENS the CDN behind an A record served under the queried name - the
# chain never leaves the list, so the firewall matches. Flattening is a switch its owner can
# turn off without announcing it. The day one does, that name starts answering with a CNAME
# into a shared namespace, the chain leaves the list, and the lookup is blocked - and the
# Resolver query log reports the block against the ORIGINAL name, which reads exactly like
# "that name was never on the allow-list" and is not. That misattribution has already cost
# one correct hypothesis in this project (the 2026-08-23 log entry). This script is the
# cheap standing instrument that catches the flip before a notebook does.
#
# It also closes the one gap terraform-modules/vpc-egress/variables.tf admits and nothing
# mechanical was checking: since v0.3.0 each Interactive slice owns its own list, so the two
# CAN diverge. DN-3 compares them.
#
# TWO DELIBERATE DEVIATIONS from aws/INDEX.md's rules for this folder, both stated because a
# reader is entitled to know why this file looks unlike its neighbours:
#   - It runs with NO AWS identity by default. Every other script here photographs AWS; this
#     one photographs the DNS the allow-list depends on, which is not AWS's to answer. The
#     AWS mode exists (--from-api) and is not the default, because the egress/ slice is [E]
#     and is down most of the time - a check that only works while the slice is up would not
#     be running when it matters, which is BEFORE bringing it up.
#   - Its default source is the repository rather than the deployed estate. Read the two
#     together: --from-api answers "is the deployed list still resolvable", the default
#     answers "is the list we are about to deploy still resolvable".
#
# WHAT IT CANNOT SEE, stated because a clean run here is not a clean run in the VPC:
#   - THE RESOLVER IS NOT THE ONE THAT MATTERS. This asks the laptop's resolver (or --resolver).
#     The firewall evaluates what the VPC's Route 53 Resolver resolves, and a CDN can steer a
#     chain by geography or by EDNS client subnet - so a name can be flat here and a CNAME
#     there. This is a SCREEN, and a fast one; the proof is a resolution from inside the VPC
#     (the buildbox, or a Studio terminal). A BROKEN row here is real either way; an ok row
#     is "no reason to worry from this vantage point".
#   - Private-zone names (*.internal) are answered only inside the VPC. They are listed and
#     skipped, never resolved, and never counted as a failure - a laptop NXDOMAIN on one of
#     them is the design, not a finding.
#   - Wildcard entries are coverage, not subjects: `*.amazonaws.com` cannot be queried, so it
#     is never a row here. It still covers other rows' hops, which is its job.
#   - Without --whois, section 3 has no owner column. The chain check does not need it; the
#     flattening EXPOSURE count does, and says so rather than guessing from a name.

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field

from awslib import context, profiles
from awslib.awscli import ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "dns-allowlist.txt"

# The Interactive tier. production/egress/ never sets dns_firewall, so it has no list.
SLICES = ("sandbox", "development")

# Answered only by a private hosted zone inside the VPC - listed, never resolved here.
PRIVATE_SUFFIXES = (".internal",)

DIG_TIMEOUT = 15
WHOIS_TIMEOUT = 25


# --------------------------------------------------------------------------- the lists


def _slice_path(ctx, env: str):
    return ctx.repo_root / "terraform-live" / env / "egress" / "main.tf"


_ASSIGN = re.compile(r"dns_firewall_allow_domains\s*=\s*\[")


def parse_slice(path) -> list[str]:
    """The names in one slice's dns_firewall_allow_domains, comments stripped.

    A regex rather than an HCL parser on purpose: this package is dependency-free (the
    CloudShell fallback needs it), and the block is a flat list of string literals. It
    fails LOUDLY on anything else - a silent empty list would read as "nothing to check".
    """
    text = path.read_text(encoding="utf-8")
    m = _ASSIGN.search(text)
    if not m:
        raise SystemExit(f"{path}: no dns_firewall_allow_domains assignment found")
    depth, i = 1, m.end()
    while i < len(text) and depth:
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
        i += 1
    if depth:
        raise SystemExit(f"{path}: dns_firewall_allow_domains list is not closed")
    body = re.sub(r"#[^\n]*", "", text[m.end() : i - 1])
    names = re.findall(r'"([^"]*)"', body)
    if not names:
        raise SystemExit(f"{path}: dns_firewall_allow_domains parsed empty")
    return names


def substitute(names: list[str]) -> tuple[list[str], list[str]]:
    """Resolve the one interpolation these lists use. Anything else is reported, not guessed."""
    out, notes = [], []
    for n in names:
        if "${var.region}" in n:
            sub = n.replace("${var.region}", context.REGION)
            notes.append(f"{n}\t->\t{sub}")
            n = sub
        if "${" in n:
            notes.append(f"{n}\t->\t(UNRESOLVED interpolation - skipped)")
            continue
        out.append(n)
    return out, notes


def read_from_api(cli, env: str, errors: ErrorLog) -> list[str] | None:
    """The DEPLOYED list, by the name the module gives it."""
    want = f"awsds-{env}-egress-allow"
    res = cli.call("route53resolver", "list-firewall-domain-lists", "--output", "json")
    if not res.ok:
        errors.add(("route53resolver", "list-firewall-domain-lists"), res.merged, cli.profile)
        return None
    try:
        lists = json.loads(res.text).get("FirewallDomainLists", [])
    except json.JSONDecodeError:
        return None
    match = next((d for d in lists if d.get("Name") == want), None)
    if match is None:
        return None
    res = cli.call(
        "route53resolver",
        "list-firewall-domains",
        "--firewall-domain-list-id",
        match["Id"],
        "--max-results",
        "500",
        "--output",
        "json",
    )
    if not res.ok:
        errors.add(
            ("route53resolver", "list-firewall-domains", match["Id"]), res.merged, cli.profile
        )
        return None
    try:
        # The API canonicalises every entry with a trailing dot (EXC-04). Strip it so the
        # deployed list and the coded list are comparable at all.
        return [d.rstrip(".") for d in json.loads(res.text).get("Domains", [])]
    except json.JSONDecodeError:
        return None


# --------------------------------------------------------------------------- matching


def covers(pattern: str, name: str) -> bool:
    """Does one allow-list entry match this name?

    The documented semantics, and the reason this is four lines rather than a substring
    test: `*` must replace a whole leftmost label, it matches EVERY depth beneath the base,
    and it never matches the base itself - so `*.foo.com` and `foo.com` are two entries.
    """
    p, n = pattern.rstrip(".").lower(), name.rstrip(".").lower()
    if p == "*":
        return True
    if p.startswith("*."):
        return n.endswith("." + p[2:])
    return n == p


def is_private(name: str) -> bool:
    return name.rstrip(".").lower().endswith(PRIVATE_SUFFIXES)


# --------------------------------------------------------------------------- resolution


@dataclass
class Answer:
    name: str
    hops: list[str] = field(default_factory=list)  # CNAME targets, in order
    addrs: list[str] = field(default_factory=list)  # terminal A/AAAA
    error: str = ""

    @property
    def chain(self) -> list[str]:
        """Every name the firewall evaluates for this lookup."""
        return [self.name] + self.hops


def resolve(name: str, resolver: str | None) -> Answer:
    cmd = ["dig", "+noall", "+answer"]
    if resolver:
        cmd.append("@" + resolver)
    cmd.append(name)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=DIG_TIMEOUT)
    except subprocess.TimeoutExpired:
        return Answer(name, error="dig timed out")
    if res.returncode != 0:
        return Answer(name, error=(res.stderr.strip() or f"dig exit {res.returncode}"))
    ans = Answer(name)
    for line in res.stdout.splitlines():
        f = line.split()
        if len(f) < 5:
            continue
        if f[3] == "CNAME":
            ans.hops.append(f[4].rstrip("."))
        elif f[3] in ("A", "AAAA"):
            ans.addrs.append(f[4])
    if not ans.hops and not ans.addrs:
        ans.error = "no answer (NXDOMAIN, or the name has no address record)"
    return ans


_OWNER = re.compile(r"^(OrgName|org-name|netname|NetName|descr):[ \t]*(.+)$", re.M | re.I)

# A registry that does not hold the block answers with a placeholder and then REFERS - so
# the first owner-shaped line in the output is routinely not the owner. Measured on
# 151.101.64.223 (Fastly): RIPE answers NON-RIPE-NCC-MANAGED-ADDRESS-BLOCK, and ARIN's real
# answer sits further down the same output. Taking the first match would have printed the
# placeholder and looked like a reading.
_PLACEHOLDER = ("non-ripe", "not managed", "not allocated", "no match", "reserved")


def owner_of(addr: str) -> str:
    try:
        res = subprocess.run(["whois", addr], capture_output=True, text=True, timeout=WHOIS_TIMEOUT)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return "(whois unavailable)"
    found = [
        (f.lower(), v.strip())
        for f, v in _OWNER.findall(res.stdout)
        if not any(ph in v.lower() for ph in _PLACEHOLDER)
    ]
    for want in ("orgname", "org-name"):  # the organisation, before any network label
        for f, v in found:
            if f == want:
                return v
    return found[0][1] if found else "(not reported)"


def verdict(ans: Answer, patterns: list[str]) -> tuple[str, list[str]]:
    if ans.error:
        return "no-answer", []
    uncovered = [h for h in ans.chain if not any(covers(p, h) for p in patterns)]
    if uncovered:
        return "BROKEN", uncovered
    return ("ok-chain" if ans.hops else "ok-flat"), []


# --------------------------------------------------------------------------- main


def main(argv: list) -> int:
    argv = list(argv)
    do_whois = "--whois" in argv
    if do_whois:
        argv.remove("--whois")
    resolver = None
    if "--resolver" in argv:
        i = argv.index("--resolver")
        if i + 1 >= len(argv):
            raise SystemExit("--resolver needs an address")
        resolver = argv[i + 1]
        del argv[i : i + 2]
    from_api = "--from-api" in argv
    if from_api:
        argv.remove("--from-api")

    if shutil.which("dig") is None:
        raise SystemExit("dig is not on PATH - this script has no other way to read a chain")

    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    errors = ErrorLog()
    clis: dict[str, object] = {}
    source_note = "terraform-live/<env>/egress/main.tf (the lists as CODE declares them)"
    if from_api:
        selected, src = profiles.select(argv)
        callers = profiles.preflight(selected, errors, out_label=out_label)
        clis = {c.profile: profiles.cli_for(c.profile, errors) for c in callers if c.live}
        source_note = f"the DEPLOYED domain lists, read through {src}"

    lists: dict[str, list[str]] = {}
    subs: list[str] = []
    for env in SLICES:
        if from_api:
            cli = next(
                (c for p, c in clis.items() if p.endswith("-" + env) or p.endswith("-" + env[:3])),
                None,
            )
            names = read_from_api(cli, env, errors) if cli is not None else None
            if names is None:
                note(f"  {env}: no deployed list reachable - falling back to the coded one")
                names, s = substitute(parse_slice(_slice_path(ctx, env)))
                subs += s
            lists[env] = names
        else:
            names, s = substitute(parse_slice(_slice_path(ctx, env)))
            subs += s
            lists[env] = names

    checks = Checks()

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("dns-allowlist - does every listed name still resolve inside its own list")
        rep.text(f"""generated : {context.utc_stamp()}
region    : {context.REGION}
source    : {source_note}
resolver  : {resolver or "the system resolver of this machine"}
owners    : {"whois, per terminal address" if do_whois else "not measured (--whois)"}

EXC-05 is what this measures. The firewall evaluates the WHOLE chain, so a name is allowed
only while every hop it takes is also listed. A BROKEN row means a hop left the list - it is
the finding, and it is almost always someone else's DNS change rather than ours.
""")

        # ---------------------------------------------------------------- 1
        rep.h1("1. The lists, as read")
        for env, names in lists.items():
            rep.h2(f"{env} - {len(names)} entries")
            rows = ["ENTRY\tKIND"]
            for n in names:
                kind = (
                    "wildcard (coverage only, never queried)"
                    if n.startswith("*")
                    else "private zone (answered inside the VPC only)"
                    if is_private(n)
                    else "queryable"
                )
                rows.append(f"{n}\t{kind}")
            rep.tabulate(rows)
        if subs:
            rep.h2("interpolations resolved while reading the code")
            rep.tabulate(["WRITTEN\t\tREAD AS"] + subs)

        # ---------------------------------------------------------------- 2
        rep.h1("2. Resolution, per list - the chain check")
        rep.text(
            "CHAIN is every name the firewall evaluates for that lookup: the name asked for,\n"
            "then each CNAME target in order. UNCOVERED names are the ones no entry on that\n"
            "list matches, and one of them is enough to block the lookup.\n"
        )
        answers: dict[str, dict[str, Answer]] = {}
        broken: list[str] = []
        unanswered: list[str] = []
        for env, names in lists.items():
            answers[env] = {}
            queryable = [n for n in names if not n.startswith("*") and not is_private(n)]
            rep.h2(f"{env} - {len(queryable)} queryable of {len(names)}")
            rows = ["NAME\tVERDICT\tHOPS\tCHAIN / UNCOVERED"]
            for n in queryable:
                note(f"  {env}: {n}")
                ans = resolve(n, resolver)
                answers[env][n] = ans
                v, unc = verdict(ans, names)
                if v == "BROKEN":
                    broken.append(f"{env}: {n} -> {' -> '.join(unc)}")
                    detail = "UNCOVERED: " + " ".join(unc)
                elif v == "no-answer":
                    unanswered.append(f"{env}: {n} ({ans.error})")
                    detail = ans.error
                else:
                    detail = " -> ".join(ans.chain)
                rows.append(f"{n}\t{v}\t{len(ans.hops)}\t{detail}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 3
        rep.h1("3. What is behind each name - the flattening exposure")
        rep.text(
            "An `ok-flat` verdict says the chain never leaves the list. It does NOT say the\n"
            "name is served from its own infrastructure: most of these are CDN-fronted and\n"
            "work only because the authoritative side flattens the CDN behind an A record\n"
            "served under the queried name. Each one of those is a dependency on a switch a\n"
            "third party owns. That is the EXC-05 exposure, and this is where it is counted.\n"
        )
        exposed = 0
        counted = False
        for env in lists:
            rep.h2(env)
            rows = ["NAME\tVERDICT\tADDRESS\tOWNER OF THE ADDRESS"]
            for n, ans in answers[env].items():
                v, _ = verdict(ans, lists[env])
                addr = ans.addrs[0] if ans.addrs else "-"
                if v == "ok-flat":
                    exposed += 1
                if do_whois and ans.addrs:
                    owner = owner_of(ans.addrs[0])
                    counted = True
                else:
                    owner = "-"
                rows.append(f"{n}\t{v}\t{addr}\t{owner}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 4
        rep.h1("4. The two Interactive lists side by side")
        rep.text(
            "Since vpc-egress v0.3.0 each slice owns its list, which is what lets one account's\n"
            "reach differ from another's - and also what lets them drift by accident. Private\n"
            "zones are EXPECTED to differ (each account is associated with different ones), so\n"
            "only the external halves are compared.\n"
        )
        ext = {e: {n for n in names if not is_private(n)} for e, names in lists.items()}
        a, b = SLICES
        only_a, only_b = sorted(ext[a] - ext[b]), sorted(ext[b] - ext[a])
        rows = ["ENTRY\tIN " + a.upper() + "\tIN " + b.upper()]
        for n in sorted(ext[a] | ext[b]):
            rows.append(f"{n}\t{'yes' if n in ext[a] else 'NO'}\t{'yes' if n in ext[b] else 'NO'}")
        rep.tabulate(rows)

        # ---------------------------------------------------------------- 5
        rep.h1("5. Checks")
        if unanswered:
            checks.fail(
                "DN-1",
                "every queryable name answers",
                f"{len(unanswered)} did not: " + "; ".join(unanswered),
            )
        else:
            checks.ok(
                "DN-1",
                "every queryable name answers",
                f"{sum(len(v) for v in answers.values())} names, all with an address",
            )
        if broken:
            checks.fail(
                "DN-2",
                "every chain stays inside its own list",
                f"{len(broken)} left it: " + "; ".join(broken),
            )
        else:
            checks.ok(
                "DN-2",
                "every chain stays inside its own list",
                "no hop is unmatched - EXC-05 has not fired",
            )
        if only_a or only_b:
            checks.fail(
                "DN-3",
                "the two Interactive lists carry the same external names",
                f"only in {a}: {only_a or '-'}; only in {b}: {only_b or '-'}",
            )
        else:
            checks.ok(
                "DN-3",
                "the two Interactive lists carry the same external names",
                f"{len(ext[a])} entries, identical",
            )
        attribution = (
            "the owner column in section 3 says which of them are a third party's CDN"
            if counted
            else "WHOSE they are is not measured - re-run with --whois to attribute them"
        )
        checks.note(
            "DN-4",
            "flattening exposure",
            f"{exposed} name(s) resolve flat, so each depends on its owner keeping it "
            f"that way (EXC-05); {attribution}",
        )
        rep.checks_table(checks)
        rep.text("""
A `fail` on DN-2 is the one to act on, and the action is NOT to add the uncovered name:
if it is a shared CDN namespace, listing it ends the control this firewall is (see
terraform-modules/vpc-egress/variables.tf, shape 3). The repairs are a host that still
answers flat, a mirror inside the estate, or design B - D5 at Stage 6 step 6.1.

A clean run here is a screen, not a proof: this resolver is not the VPC's. Confirm a
BROKEN row, and any surprise, from inside the VPC.
""")

        rep.h1("6. Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"\nwrote {out_label}")
    print(open(out_path, encoding="utf-8").read())
    return 2 if checks.n_fail() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
