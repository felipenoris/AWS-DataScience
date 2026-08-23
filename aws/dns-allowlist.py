#!/usr/bin/env -S uv run --quiet
# dns-allowlist.py - re-resolve every name on the Interactive egress allow-lists and report
# what each one answers with, which entries are redundant hops, and which reach their address
# only because the ALLOW rule trusts the redirection chain.
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
# WHY THIS EXISTS, AND WHY ITS MAIN QUESTION INVERTED ON 2026-08-23. It was written that
# morning for docs/AWS_STATE.md EXC-05: DNS Firewall inspected the WHOLE resolution chain, so
# a name was allowed only while every hop it took was also on the list, and eight of nine
# external names resolved only because their authoritative side FLATTENED the CDN behind an A
# record served under the queried name - a switch a third party could turn off unannounced,
# after which the Resolver log blamed the ORIGINAL name and the block read like "that name was
# never on the allow-list". That misattribution cost one correct hypothesis (the 2026-08-23
# log entry).
#
# vpc-egress-v0.4.0 MADE `firewall_domain_redirection_action` A MODULE INPUT - default
# INSPECT, and both Interactive slices pass `TRUST_REDIRECTION_DOMAIN` on their ALLOW rule, so
# in those two VPCs the firewall inspects the QUERIED name and trusts the chain beneath it.
# THIS SCRIPT ASSUMES THAT SETTING, because it reads only the two lists that carry it; a slice
# left on the default is not in SLICES and would need DN-2 and DN-4 read the other way round. EXC-05's failure mode is closed and DN-2 no longer asks whether a chain stays inside its
# list - it asks the question the new rule makes load-bearing: IS ANYTHING ON A LIST A HOP OF
# SOMETHING ELSE ON THE SAME LIST. A listed hop is not redundancy, it is a widening: the trust
# is scoped to one query transaction, so a redirection target is unreachable on its own until
# somebody lists it. DN-4 keeps the old measurement as information rather than as a verdict -
# which names would stop resolving if the module were ever reverted to the API default.
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
    """Three outcomes, and none of them is a block since vpc-egress v0.4.0.

    The queried name is an entry on the list by construction, and the ALLOW rule trusts
    whatever it redirects through - so the only thing worth separating is HOW the address
    was reached. `uncovered` is the hops no entry matches: under the old default those were
    the block, and now they are the part of the answer that rests on the trust setting.
    """
    if ans.error:
        return "no-answer", []
    uncovered = [h for h in ans.hops if not any(covers(p, h) for p in patterns)]
    if not ans.hops:
        return "ok-flat", []
    return ("ok-trusted" if uncovered else "ok-listed"), uncovered


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

Both Interactive slices pass firewall_domain_redirection_action = TRUST_REDIRECTION_DOMAIN
(vpc-egress v0.4.0, whose own default is INSPECT): the firewall inspects the name that was
QUERIED and trusts the chain under it. So a chain leaving its list is no longer a
block (that was EXC-05, closed) - the finding to act on is a HOP that somebody left ON a list,
because listing one is what makes that redirection target resolvable on its own.
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
        rep.h1("2. Resolution, per list - what each name answers with")
        rep.text(
            "CHAIN is the name asked for, then each CNAME target in order. Three verdicts:\n"
            "  ok-flat     an A record under the queried name - no redirection at all\n"
            "  ok-listed   it redirects, and every hop happens to be on the list as well\n"
            "  ok-trusted  it redirects off the list, and reaches its address because the\n"
            "              ALLOW rule trusts the chain. Normal since v0.4.0, and the count\n"
            "              DN-4 reports - these are the rows that would break on a revert.\n"
        )
        answers: dict[str, dict[str, Answer]] = {}
        trusted: list[str] = []  # rows reaching their address through an unlisted hop
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
                if v == "no-answer":
                    unanswered.append(f"{env}: {n} ({ans.error})")
                    detail = ans.error
                else:
                    if unc:
                        trusted.append(f"{env}: {n} -> {' -> '.join(unc)}")
                    detail = " -> ".join(ans.chain)
                rows.append(f"{n}\t{v}\t{len(ans.hops)}\t{detail}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 3
        rep.h1("3. Entries that are really hops - the v0.4.0 finding")
        rep.text(
            "An entry that appears in ANOTHER entry's chain, on the same list, is a hop that\n"
            "was left behind. Before v0.4.0 listing it was mandatory; now it is a widening -\n"
            "the trust is scoped to one query transaction, so a redirection target cannot be\n"
            "reached on its own UNLESS it is listed, and listing it is what grants that. This\n"
            "is measured from the chains in section 2, not from a list of known CDN suffixes.\n"
        )
        hops_listed: list[str] = []
        for env in lists:
            rep.h2(env)
            reached_by: dict[str, list[str]] = {}
            for n, ans in answers[env].items():
                for h in ans.hops:
                    reached_by.setdefault(h.rstrip(".").lower(), []).append(n)
            rows = ["ENTRY\tALSO A HOP OF"]
            for n in answers[env]:
                via = reached_by.get(n.rstrip(".").lower(), [])
                if via:
                    hops_listed.append(f"{env}: {n} (hop of {', '.join(via)})")
                rows.append(f"{n}\t{', '.join(via) if via else '-'}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 3b
        rep.h1("3b. What is behind each name")
        rep.text(
            "Who actually serves the bytes. This stopped being a control question at v0.4.0 -\n"
            "a CDN-fronted name is listable like any other - and stayed a useful one: the\n"
            "chain is trusted wherever the owner of the listed name points it, so this is the\n"
            "party each entry extends trust to.\n"
        )
        counted = False
        for env in lists:
            rep.h2(env)
            rows = ["NAME\tVERDICT\tADDRESS\tOWNER OF THE ADDRESS"]
            for n, ans in answers[env].items():
                v, _ = verdict(ans, lists[env])
                addr = ans.addrs[0] if ans.addrs else "-"
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
        if hops_listed:
            checks.fail(
                "DN-2",
                "no entry is a redirection target of another entry",
                f"{len(hops_listed)} is/are: " + "; ".join(hops_listed),
            )
        else:
            checks.ok(
                "DN-2",
                "no entry is a redirection target of another entry",
                "no list carries a hop of its own - nothing is widened by leftovers",
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
            "the owner column in section 3b says whose infrastructure each one lands on"
            if counted
            else "WHOSE they are is not measured - re-run with --whois to attribute them"
        )
        checks.note(
            "DN-4",
            "names reaching their address through an unlisted hop",
            f"{len(trusted)} name(s) resolve only because their slice passes "
            f"TRUST_REDIRECTION_DOMAIN - these are what dropping back to the module default "
            f"would break: {'; '.join(trusted) if trusted else 'none'}; {attribution}",
        )
        rep.checks_table(checks)
        rep.text("""
A `fail` on DN-2 is the one to act on, and the action is to REMOVE the entry, not to keep
it: a slice passing TRUST_REDIRECTION_DOMAIN needs no hop listed, and the listing is what
makes that redirection target resolvable on its own. On a slice left at the module default
the finding reverses - there the hop is REQUIRED, and this check does not apply to it. Check first that nothing queries the name
directly - a hop of one entry can still be a name a different tool asks for by itself, and
then it is an entry in its own right rather than a leftover.

DN-4 is information, not a warning. A large count is the expected shape of a list written
against TRUST; it becomes a work item only if a slice drops back to the module default.

A clean run here is a screen, not a proof: this resolver is not the VPC's, and a CDN can
steer a chain by geography. Confirm anything surprising from inside the VPC.
""")

        rep.h1("6. Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"\nwrote {out_label}")
    print(open(out_path, encoding="utf-8").read())
    return 2 if checks.n_fail() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
