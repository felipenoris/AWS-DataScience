#!/usr/bin/env -S uv run --quiet
# dns-allowlist.py - re-resolve every name on the PROXY's source-scoped allow-lists and report
# what each one answers with, which entries collide under Squid's matching rules, and what the
# committed lists say against what the estate is actually serving them from.
#
#   needs:    NOTHING, in the default mode - no SSO session, no profile, no AWS call. It
#             reads this repository's own .tf and asks a resolver. `dig` must be on PATH.
#             `--from-api PROFILE` is the AWS mode and needs a live session:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/dns-allowlist.py                    the planes as CODE declares them
#             ./aws/dns-allowlist.py --whois            + who owns each answer address
#             ./aws/dns-allowlist.py --from-api awsds-infra-prod
#                                                       + the DEPLOYED parameter, compared
#             ./aws/dns-allowlist.py --resolver 1.1.1.1 ask a specific resolver
#   writes:   aws/output/dns-allowlist.txt   (untracked - see .gitignore)
#   reads:    DNS, and `whois` only with --whois. With --from-api, one read-only call:
#             ssm:GetParameter. This script never creates, updates or deletes anything.
#
# WHAT THIS FILE MEASURED UNTIL 2026-09-06, AND WHY IT NOW MEASURES SOMETHING ELSE. It was
# written for the Route 53 Resolver DNS Firewall allow-lists in the two Interactive `egress/`
# slices, when those lists WERE the estate's egress policy: a NAT gateway carried anything, so a
# name that did not resolve was a host nobody reached. Stage 6c step 5.1 removed the last default
# route (D38) and step 5.7 cut those lists from sixty-three entries to ten - AWS's own namespaces
# and this estate's private zones, nothing else. The policy moved, whole, to the explicit proxy's
# source-scoped allow-lists, so this instrument moved with it. Pointing it at a list that no
# longer decides anything would be Lesson 31 in the other direction: a check that keeps reading
# `pass` about a thing that stopped mattering.
#
# THE SUBSTITUTION IS NOT A TRANSLATION, and that is the first thing to know before reading a row
# here against an old report. Three things changed at once:
#
#   1. THERE ARE FIVE LISTS, NOT TWO, and they are keyed by SOURCE rather than by account: the
#      tunnel range carries the institutional web filter (what a person may reach), each spoke
#      CIDR carries its own. Two filters where the resolver could only ever hold one, which is
#      the whole reason D38 splits them.
#   2. SQUID MATCHES THE HOSTNAME THAT WAS REQUESTED. It never evaluates a CNAME chain, so
#      EXC-05's entire failure mode - a listed name blocked because a hop was not listed, with
#      the log blaming the queried name - has no place to occur. `TRUST_REDIRECTION_DOMAIN`, the
#      v0.4.0 repair, is now a setting on a list that no longer carries a CDN-fronted name.
#   3. THE SYNTAX IS THE OTHER ONE. Route 53 needs `x` and `*.x` as two entries; Squid's `.x`
#      covers both, and listing the apex BESIDE it is not redundant but FATAL - `ERROR: '.x' is
#      a subdomain of 'x'`, then `FATAL: Bungled`. That is DN-2's new question, and it is not a
#      style rule: it is a proxy that refuses to start (Lesson 53).
#
# WHAT STAYED. DN-1 is the same question it always was - does every name somebody depends on
# still answer - and it is the reason this file resolves anything at all. A dead entry is a dead
# dependency whichever system enforces it.
#
# TWO DELIBERATE DEVIATIONS from aws/INDEX.md's rules for this folder, both stated because a
# reader is entitled to know why this file looks unlike its neighbours:
#   - It runs with NO AWS identity by default. Every other script here photographs AWS; this
#     one photographs the DNS the allow-list depends on, which is not AWS's to answer.
#   - Its default source is the repository rather than the deployed estate. Read the two
#     together: --from-api answers "is the deployed list still resolvable, and does it still
#     match the code", the default answers "is the list we are about to deploy still resolvable".
#     The parameter is [P] and always present, unlike the [E] domain lists this file used to
#     read - so --from-api is now reliable rather than opportunistic.
#
# WHAT IT CANNOT SEE, stated because a clean run here is not a clean run in the VPC:
#   - THE RESOLVER IS NOT THE ONE THAT MATTERS, and under an explicit proxy it is even further
#     away: a spoke client does not resolve an internet name at all - SQUID does, from
#     VPC-Networking. This asks the laptop's resolver (or --resolver). A CDN can steer an answer
#     by geography or by EDNS client subnet, so a name can answer here and not there. This is a
#     SCREEN, and a fast one; the proof is a request through the proxy.
#   - Private-zone names (*.internal) are answered only inside the VPC. They are listed and
#     skipped, never resolved, and never counted as a failure.
#   - A leading-dot entry (`.example.com`) is COVERAGE, not a subject: it is not a name anything
#     queries, so it is never a row in section 2. It still participates in DN-2, which is about
#     entries colliding with each other rather than about what resolves.
#   - Whether the RUNNING squid.conf matches the parameter. That is PX-3 in ./aws/proxy.py, read
#     on the host over SSM. The chain is code -> parameter -> host; DN-3 is the first link and
#     PX-3 is the second, and neither one alone says the proxy is enforcing what was written.

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

# The [P] slice that owns the proxy's allow-lists (Stage 6c steps 4.9/4.10). ONE file, because
# the lists are locals in it and the SSM parameter is rendered from them - which is what makes
# "the committed list" a thing this script can read without an AWS call.
ANCHORS = ("production", "networking", "hub-anchors.tf")

# The parameter the [D] proxy renders at boot and on a State Manager schedule. Its name is built
# in the .tf from `/datascience/${var.env}/proxy/allowlist`; `prod` is production's env token.
# NOT `/awsds/...` - Parameter Store reserves every name beginning with `aws`.
PARAMETER = "/datascience/prod/proxy/allowlist"

# Answered only by a private hosted zone inside the VPC - listed, never resolved here.
PRIVATE_SUFFIXES = (".internal",)

DIG_TIMEOUT = 15
WHOIS_TIMEOUT = 25

# THE PLANES A DECISION HAS PUT IN `open` MODE, AND WHY - DN-4's allow-list of exceptions.
# DN-4 used to read "every plane but `tunnel` must be an allow-list", which was true of the
# design on the day it was written and stopped being true on 2026-09-08. Rewriting it as
# "whatever is open is fine" would have retired the check; this keeps it load-bearing, because a
# NEW plane going `open` still fails, and the entry a person has to add to make it pass carries
# the decision that took it. The value is the reason, printed in the pass line - a reader of the
# report should not have to open a decision file to learn why a plane is open (Lesson 50).
OPEN_BY_DECISION = {
    "tunnel": "the client's internet is MONITORED, not restricted - objectives.md, 2026-09-07",
    "production-foundation": (
        "a BUILD plane, not a compute one: its control is the review of the Dockerfile in git, "
        "not a hostname list - D38 section 6 as amended, 2026-09-08"
    ),
}


# --------------------------------------------------------------------------- the lists


def _anchors_path(ctx):
    return ctx.repo_root.joinpath("terraform-live", *ANCHORS)


def _balanced(text: str, start: int, opener: str, closer: str) -> tuple[str, int]:
    """The body between one opener at `start` and its matching closer."""
    depth, i = 1, start + 1
    while i < len(text) and depth:
        if text[i] == opener:
            depth += 1
        elif text[i] == closer:
            depth -= 1
        i += 1
    if depth:
        raise SystemExit(f"unbalanced {opener}{closer} starting at offset {start}")
    return text[start + 1 : i - 1], i


_STRIP_COMMENTS = re.compile(r"#[^\n]*")
# `proxy_deny_*` as well as `proxy_allow_*` since 2026-09-07 - the client plane carries a DENY
# list, and a regex that only knew one kind would read it as an absent plane.
_LIST_ASSIGN = re.compile(r"^\s*(proxy_(?:allow|deny)_[a-z_]+)\s*=\s*\[", re.M)

# THE SECOND SHAPE A LIST CAN TAKE, and it was added to the .tf before it was added here - which
# cost a KeyError traceback rather than the loud, readable refusal this parser promises.
# `proxy_allow_shared` became `concat(<comprehension>, <literal>)` on 2026-09-06, when one
# CloudFront distribution had to be added to a list that is otherwise DERIVED from the notebook's.
# Both halves are parsed; anything else still fails by name.
# NOTHING IN THE .tf MATCHES EITHER FORM SINCE 2026-09-08 - `proxy_allow_shared` was deleted when
# the build plane became `open` (D38 section 6, 6d step 9). KEPT ANYWAY, and not because it might
# come back: without the derived branch a `[for d in local.x : d if d != "y"]` list would be read
# by the literal path, whose `findall` would return the EXCLUDED name and nothing else. That is a
# silent misreading, and this parser's whole contract is that an unknown form fails loudly. The
# dead branch is what keeps the failure loud.
_CONCAT_ASSIGN = re.compile(r"^\s*(proxy_(?:allow|deny)_[a-z_]+)\s*=\s*concat\(", re.M)
_DERIVED = re.compile(
    r"^\s*for\s+(\w+)\s+in\s+local\.(proxy_allow_[a-z_]+)\s*:\s*\1\s+if\s+\1\s*!=\s*\"([^\"]+)\"\s*$"
)
# BOTH KINDS OF LOCAL SINCE 2026-09-08. `proxy_deny_by_plane` names the planes that are `open`,
# and its rows have the same shape as the allow map's - so the grammar widens by one alternation
# rather than growing a second regex that could drift from this one.
_PLANE_ROW = re.compile(
    r'^\s*"?([a-z0-9-]+)"?\s*=\s*(local\.(proxy_(?:allow|deny)_[a-z_]+)|\[\s*\])\s*$'
)


def parse_anchors(path) -> dict[str, list[str]]:
    """`({plane: [names]}, {plane: mode})` from the [P] slice that declares them.

    The names are what this file RESOLVES, and both kinds are worth resolving: a dead entry on a
    deny list is as stale as one on an allow list. The mode is what stops DN-4 reading an empty
    deny list as an empty allow list, which are opposite states.

    A small explicit grammar rather than an HCL parser, for the reason parse_slice had before
    it: this package is dependency-free (the CloudShell fallback needs it). It fails LOUDLY on
    any form it was not written for - a plane silently read as empty would report a proxy that
    allows nothing as a proxy with nothing to check.
    """
    text = path.read_text(encoding="utf-8")

    named: dict[str, list[str]] = {}
    derived: list[tuple[str, str, str]] = []
    for m in _LIST_ASSIGN.finditer(text):
        body, _ = _balanced(text, m.end() - 1, "[", "]")
        clean = _STRIP_COMMENTS.sub("", body).strip()
        d = _DERIVED.match(clean)
        if d:
            derived.append((m.group(1), d.group(2), d.group(3)))
            continue
        named[m.group(1)] = re.findall(r'"([^"]*)"', clean)

    # Derived lists, evaluated rather than transcribed. There are none in the .tf today (see the
    # note on _CONCAT_ASSIGN); the loop is what makes a re-introduced one correct instead of
    # silently inverted.
    for name, source, excluded in derived:
        if source not in named:
            raise SystemExit(f"{path}: {name} derives from {source}, which was not parsed")
        named[name] = [d for d in named[source] if d != excluded]

    # `concat(...)` lists, parsed after the literals so a derived half can look its source up.
    for m in _CONCAT_ASSIGN.finditer(text):
        body, _ = _balanced(text, m.end() - 1, "(", ")")
        clean = _STRIP_COMMENTS.sub("", body)
        collected: list = []
        for part in re.finditer(r"\[(.*?)\]", clean, re.S):
            chunk = part.group(1)
            d = _DERIVED.match(chunk.strip())
            if d:
                if d.group(2) not in named:
                    raise SystemExit(f"{path}: {m.group(1)} derives from {d.group(2)}, not parsed")
                collected += [x for x in named[d.group(2)] if x != d.group(3)]
            else:
                collected += re.findall(r'"([^"]*)"', chunk)
        named[m.group(1)] = collected

    planes: dict[str, list[str]] = {}
    modes: dict[str, str] = {}

    # TWO MAPS SINCE 2026-09-08, AND WHICH ONE A PLANE IS IN IS ITS MODE. `proxy_allow_by_plane`
    # holds the allow-lists; `proxy_deny_by_plane` holds the planes that are `open` and carries
    # what they may NOT reach. Both are REQUIRED here: a missing deny map would make an `open`
    # plane read as an allow-list with nothing on it, which is the exact inversion this parser
    # exists to prevent - a plane that reaches everything, reported as a plane that reaches
    # nothing.
    for map_name, mode in (("proxy_allow_by_plane", "allowlist"), ("proxy_deny_by_plane", "open")):
        m = re.search(r"^\s*" + map_name + r"\s*=\s*\{", text, re.M)
        if not m:
            raise SystemExit(f"{path}: no {map_name} map found")
        body, _ = _balanced(text, m.end() - 1, "{", "}")
        for line in _STRIP_COMMENTS.sub("", body).splitlines():
            if not line.strip():
                continue
            row = _PLANE_ROW.match(line)
            if not row:
                raise SystemExit(f"{path}: {map_name} row not understood: {line.strip()!r}")
            if row.group(3) and row.group(3) not in named:
                raise SystemExit(
                    f"{path}: plane {row.group(1)} points at local `{row.group(3)}`, which this "
                    "parser did not recognise. Its assignment is a form the grammar here does not "
                    "cover - add the form rather than letting the plane read as empty."
                )
            if row.group(1) in planes:
                raise SystemExit(
                    f"{path}: plane {row.group(1)} is in BOTH plane maps. The .tf has a "
                    "precondition for this; if it applied anyway, the mode is whatever the "
                    "render script happened to branch on."
                )
            planes[row.group(1)] = list(named[row.group(3)]) if row.group(3) else []
            modes[row.group(1)] = mode

    # THE CLIENT PLANE IS NOT IN THAT MAP, AND ITS ABSENCE IS THE POINT (2026-09-07). `tunnel` used
    # to be a row there carrying a 23-name allow-list. `objectives.md` asks for the client's
    # internet to be **monitored** rather than restricted, so it is now an `open` plane whose list
    # is a DENY list - `proxy_deny_tunnel`, empty by decision. It is read from its own local
    # because it is a different KIND of list, and merging the two would let this instrument report
    # "the tunnel allows nothing", which is the exact opposite of what an empty deny list means.
    if "proxy_deny_tunnel" in named:
        planes["tunnel"] = list(named["proxy_deny_tunnel"])
        modes["tunnel"] = "open"
    if not planes:
        raise SystemExit(f"{path}: the plane maps parsed empty")
    return planes, modes


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


def read_from_api(cli, errors: ErrorLog) -> dict[str, dict] | None:
    """The DEPLOYED parameter - the [P] value the proxy renders its configuration from."""
    res = cli.call(
        "ssm",
        "get-parameter",
        "--name",
        PARAMETER,
        "--query",
        "Parameter.Value",
        "--output",
        "text",
    )
    if not res.ok:
        errors.add(("ssm", "get-parameter", PARAMETER), res.merged, cli.profile)
        return None
    try:
        return json.loads(res.text.strip())
    except json.JSONDecodeError:
        errors.add(("ssm", "get-parameter", PARAMETER), "value is not JSON", cli.profile)
        return None


# --------------------------------------------------------------------------- matching


def covers(pattern: str, name: str) -> bool:
    """Does one Squid `dstdomain` entry match this name?

    SQUID'S SEMANTICS, NOT ROUTE 53's, and the difference is the whole of Lesson 53: a leading
    dot means "this domain AND every subdomain of it", so `.example.com` matches both
    `example.com` and `a.b.example.com` - where Route 53 needed `example.com` and `*.example.com`
    as two separate entries and its wildcard never matched the apex. An entry with no leading dot
    is an EXACT hostname match.
    """
    p, n = pattern.rstrip(".").lower(), name.rstrip(".").lower()
    if p.startswith("."):
        return n == p[1:] or n.endswith(p)
    return n == p


def collisions(names: list[str]) -> tuple[list[str], list[str]]:
    """Squid's two overlap outcomes, which are NOT the same severity.

    Measured 2026-09-06 while building the proxy, and it cost four attempts to learn:

      an apex listed BESIDE its own leading-dot form   ->  FATAL. Squid logs
          `ERROR: '.x' is a subdomain of 'x'` and then `FATAL: Bungled`, and refuses to start.
          The estate's single egress does not come up, which surfaces as every spoke losing the
          internet at once - a symptom no reader attributes to one redundant line.

      a DEEPER name under a leading-dot form           ->  a WARNING only. `d35uxhjf90umnp.cloudfront.net`
          sat beside `.cloudfront.net` for a fortnight without breaking anything. It is still
          worth removing - a line that warns on every reconfigure is a line people stop reading -
          but it is a tidy, not an outage.
    """
    fatal, redundant = [], []
    lowered = [n.rstrip(".").lower() for n in names]
    for i, a in enumerate(lowered):
        for j, b in enumerate(lowered):
            if i == j:
                continue
            if a.startswith(".") and b == a[1:]:
                fatal.append(f"{b} is listed beside {a}")
            elif a.startswith(".") and not b.startswith(".") and b.endswith(a):
                redundant.append(f"{b} is already covered by {a}")
    return sorted(set(fatal)), sorted(set(redundant))


def is_private(name: str) -> bool:
    return name.rstrip(".").lower().endswith(PRIVATE_SUFFIXES)


def queryable(names: list[str]) -> list[str]:
    """What is worth asking a resolver about: a real hostname, not coverage, not a private zone."""
    return [n for n in names if not n.startswith(".") and not is_private(n)]


# --------------------------------------------------------------------------- resolution


@dataclass
class Answer:
    name: str
    hops: list[str] = field(default_factory=list)  # CNAME targets, in order
    addrs: list[str] = field(default_factory=list)  # terminal A/AAAA
    error: str = ""

    @property
    def chain(self) -> list[str]:
        return [self.name, *self.hops]


def resolve(name: str, resolver: str | None) -> Answer:
    """One `dig`, read as a chain. The CNAME hops are kept because section 3b needs them."""
    cmd = ["dig", "+noall", "+answer", "+tries=1", f"+time={DIG_TIMEOUT // 3 or 1}", name, "A"]
    if resolver:
        cmd.insert(1, f"@{resolver}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=DIG_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return Answer(name, error=f"dig failed: {exc}")
    ans = Answer(name)
    for line in res.stdout.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue
        rtype, value = parts[3], parts[4]
        if rtype == "CNAME":
            ans.hops.append(value.rstrip("."))
        elif rtype in ("A", "AAAA"):
            ans.addrs.append(value)
    if not ans.addrs:
        ans.error = ans.error or "no address in the answer"
    return ans


def owner_of(addr: str) -> str:
    """whois, reduced to the organisation - never to a network label."""
    try:
        res = subprocess.run(["whois", addr], capture_output=True, text=True, timeout=WHOIS_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return "(whois failed)"
    found = [
        (m.group(1).strip().lower(), m.group(2).strip())
        for m in re.finditer(r"^(OrgName|org-name|owner|descr):\s*(.+)$", res.stdout, re.M)
    ]
    for want in ("orgname", "org-name"):  # the organisation, before any network label
        for f, v in found:
            if f == want:
                return v
    return found[0][1] if found else "(not reported)"


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
    coded_raw, plane_modes = parse_anchors(_anchors_path(ctx))
    planes: dict[str, list[str]] = {}
    subs: list[str] = []
    for plane, names in coded_raw.items():
        planes[plane], s = substitute(names)
        subs += s

    deployed: dict[str, dict] | None = None
    source_note = (
        "terraform-live/production/networking/hub-anchors.tf (the planes as CODE declares them)"
    )
    if from_api:
        selected, src = profiles.select(argv)
        callers = profiles.preflight(selected, errors, out_label=out_label)
        cli = next(
            (
                profiles.cli_for(c.profile, errors)
                for c in callers
                if c.live and "prod" in c.profile
            ),
            None,
        )
        if cli is None:
            note("  no live Production profile - DN-3 cannot be answered")
        else:
            deployed = read_from_api(cli, errors)
            source_note += f"; the DEPLOYED parameter read through {src}"

    checks = Checks()

    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        rep.banner("dns-allowlist - does every name the proxy admits still resolve")
        rep.text(f"""generated : {context.utc_stamp()}
region    : {context.REGION}
source    : {source_note}
parameter : {PARAMETER}
resolver  : {resolver or "the system resolver of this machine"}
owners    : {"whois, per terminal address" if do_whois else "not measured (--whois)"}

THESE ARE SQUID'S LISTS, NOT THE DNS FIREWALL'S (re-aimed at Stage 6c step 5.7, 2026-09-06).
One list per SOURCE - the tunnel range carries the institutional web filter, each spoke CIDR
carries its own - which is the split a VPC resolver could never express, because a VPC has one
resolver and everything in it shared one answer. Squid matches the hostname the client
REQUESTED and evaluates no CNAME chain, so a name that redirects off the list is not a block:
EXC-05's failure mode has no place left to occur. The chains below are read for ATTRIBUTION
(section 3b), never for a verdict.
""")

        # ---------------------------------------------------------------- 1
        rep.h1("1. The planes, as read")
        for plane, names in planes.items():
            rep.h2(f"{plane} - {len(names)} entries, mode {plane_modes.get(plane, '?')}")
            if not names:
                if plane_modes.get(plane) == "open":
                    rep.text(
                        "  empty, and for an `open` plane empty means EVERYTHING IS PERMITTED - the\n"
                        "  opposite of the line below. This is the client plane, and the objectives\n"
                        "  ask for its internet to be MONITORED rather than restricted: the control\n"
                        "  is the access log in /awsds/prod/proxy, not this list. An entry here, when\n"
                        "  one is added, is a name the estate's people may NOT reach.\n"
                    )
                else:
                    rep.text(
                        "  empty, and for an `allowlist` plane empty is a DENY: with no allow line for\n"
                        "  this source Squid falls to the final `http_access deny all` and returns a\n"
                        "  named 403. A source the security group admits and the allow-list has never\n"
                        "  heard of is reachable and mute, which is the failure that looks like a\n"
                        "  network fault.\n"
                    )
                continue
            rows = ["ENTRY\tKIND"]
            for n in names:
                kind = (
                    "subtree (`.x` - the apex AND every subdomain; never queried directly)"
                    if n.startswith(".")
                    else "private zone (answered inside the VPC only)"
                    if is_private(n)
                    else "exact hostname"
                )
                rows.append(f"{n}\t{kind}")
            rep.tabulate(rows)
        if subs:
            rep.h2("interpolations resolved while reading the code")
            rep.tabulate(["WRITTEN\t\tREAD AS"] + subs)

        # ---------------------------------------------------------------- 2
        rep.h1("2. Resolution, per plane - what each exact hostname answers with")
        rep.text(
            "CHAIN is the name asked for, then each CNAME target in order. Two verdicts, because\n"
            "under an explicit proxy there is no third: `ok` reached an address, `no-answer` did\n"
            "not. A redirection is not a finding here - Squid never sees it.\n"
        )
        answers: dict[str, dict[str, Answer]] = {}
        unanswered: list[str] = []
        for plane, names in planes.items():
            answers[plane] = {}
            subjects = queryable(names)
            if not subjects:
                continue
            rep.h2(f"{plane} - {len(subjects)} exact hostname(s) of {len(names)}")
            rows = ["NAME\tVERDICT\tHOPS\tCHAIN"]
            for n in subjects:
                note(f"  {plane}: {n}")
                ans = resolve(n, resolver)
                answers[plane][n] = ans
                if ans.error:
                    unanswered.append(f"{plane}: {n} ({ans.error})")
                    rows.append(f"{n}\tno-answer\t{len(ans.hops)}\t{ans.error}")
                else:
                    rows.append(f"{n}\tok\t{len(ans.hops)}\t{' -> '.join(ans.chain)}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 3
        rep.h1("3. Entries that collide with each other - the FATAL one and the tidy one")
        rep.text(
            "Squid's two overlap outcomes are not the same severity, and the expensive one is not\n"
            "the one that reads as worse. An APEX listed beside its own `.x` form is FATAL: Squid\n"
            "logs `'.x' is a subdomain of 'x'`, then `FATAL: Bungled`, and does not start - which\n"
            "surfaces as every spoke losing the internet at once. A DEEPER name under a `.x` is a\n"
            "WARNING and nothing more; it is worth removing because a line that warns on every\n"
            "reconfigure is a line people stop reading.\n"
        )
        all_fatal: list[str] = []
        all_redundant: list[str] = []
        for plane, names in planes.items():
            fatal, redundant = collisions(names)
            all_fatal += [f"{plane}: {f}" for f in fatal]
            all_redundant += [f"{plane}: {r}" for r in redundant]
            rep.h2(plane)
            rows = ["SEVERITY\tFINDING"]
            for f in fatal:
                rows.append(f"FATAL\t{f}")
            for r in redundant:
                rows.append(f"redundant\t{r}")
            if len(rows) == 1:
                rows.append("-\tno entry on this plane overlaps another")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 3b
        rep.h1("3b. What is behind each name")
        rep.text(
            "Who actually serves the bytes to the PROXY - which is the only host in the estate\n"
            "that fetches them. An entry extends trust to whoever owns the name, wherever they\n"
            "point it, exactly as it always did; what changed is that only one host follows.\n"
            "Run with --whois to attribute each address to an organisation.\n"
        )
        for plane in planes:
            if not answers[plane]:
                continue
            rep.h2(plane)
            rows = ["NAME\tADDRESS\tOWNER OF THE ADDRESS"]
            for n, ans in answers[plane].items():
                addr = ans.addrs[0] if ans.addrs else "-"
                owner = owner_of(ans.addrs[0]) if (do_whois and ans.addrs) else "-"
                rows.append(f"{n}\t{addr}\t{owner}")
            rep.tabulate(rows)

        # ---------------------------------------------------------------- 4
        rep.h1("4. The two filters, and they are two DIFFERENT KINDS since 2026-09-07")
        rep.text(
            "THE DESIGN CLAIM THIS SECTION USED TO MEASURE was that a name a PERSON may reach is not\n"
            "thereby reachable from a NOTEBOOK - an overlap between two allow-lists. That comparison\n"
            "no longer applies, because the two planes are no longer the same kind of list.\n"
            "`objectives.md`: the client's internet is MONITORED (an `open` plane, whose list is a\n"
            "DENY list) and the restriction belongs to the SageMaker-managed compute (an `allowlist`\n"
            "plane). Comparing their contents would compare a blocklist with a permit-list.\n"
            "\n"
            "So what is reported is the SHAPE, and the finding to look for is a plane whose mode is\n"
            "not what its role calls for. `open` is not by itself the finding - `production-foundation`\n"
            "is open by a decision (a BUILD plane; its control is the reviewed Dockerfile, not a\n"
            "hostname list). An open plane NOBODY DECIDED is the finding, and DN-4 is what separates\n"
            "the two: it fails on a plane that is not in OPEN_BY_DECISION, and prints the reason for\n"
            "each one that is.\n"
        )
        rep.tabulate(
            ["PLANE\tMODE\tENTRIES\tWHAT AN ENTRY MEANS"]
            + [
                f"{p}\t{plane_modes.get(p, '?')}\t{len(planes[p])}\t"
                + (
                    "a name this plane may NOT reach"
                    if plane_modes.get(p) == "open"
                    else "the only kind of name this plane MAY reach"
                )
                for p in sorted(planes)
            ]
        )
        open_planes = sorted(p for p in planes if plane_modes.get(p) == "open")
        unexpected_open = [p for p in open_planes if p not in OPEN_BY_DECISION]

        # ---------------------------------------------------------------- 5
        rep.h1("5. Checks")
        if unanswered:
            checks.fail(
                "DN-1",
                "every exact hostname on every plane answers",
                f"{len(unanswered)} did not: " + "; ".join(unanswered),
            )
        else:
            checks.ok(
                "DN-1",
                "every exact hostname on every plane answers",
                f"{sum(len(v) for v in answers.values())} names, all with an address",
            )

        if all_fatal:
            checks.fail(
                "DN-2",
                "no plane carries a Squid dstdomain collision",
                f"{len(all_fatal)} FATAL: " + "; ".join(all_fatal),
            )
        elif all_redundant:
            # `note` rather than `fail`, and the asymmetry is Squid's rather than a soft reading:
            # a redundant entry produces a warning on reconfigure and a working proxy, while the
            # apex pair produces `FATAL: Bungled` and no proxy at all.
            checks.note(
                "DN-2",
                "no plane carries a Squid dstdomain collision",
                f"nothing fatal; {len(all_redundant)} redundant (warning only): "
                + "; ".join(all_redundant),
            )
        else:
            checks.ok(
                "DN-2",
                "no plane carries a Squid dstdomain collision",
                "no apex beside its own subtree entry, and no name already covered by one",
            )

        if deployed is None:
            checks.note(
                "DN-3",
                "the committed planes equal the deployed parameter",
                "not answered - re-run with --from-api <a Production profile> to read "
                f"{PARAMETER}. The parameter is [P] and always present, so this is a session "
                "away rather than an apply away",
            )
        else:
            diffs = []
            for plane in sorted(set(planes) | set(deployed)):
                want = planes.get(plane)
                got = deployed.get(plane, {}).get("allow") if plane in deployed else None
                if want is None:
                    diffs.append(f"{plane} is deployed and not in the code")
                elif got is None:
                    diffs.append(f"{plane} is in the code and not deployed")
                elif list(want) != list(got):
                    only_code = sorted(set(want) - set(got))
                    only_dep = sorted(set(got) - set(want))
                    if only_code or only_dep:
                        diffs.append(
                            f"{plane}: only in code {only_code or '-'}, only deployed {only_dep or '-'}"
                        )
                    else:
                        diffs.append(f"{plane}: same entries, different order")
            if diffs:
                checks.fail(
                    "DN-3",
                    "the committed planes equal the deployed parameter",
                    "; ".join(diffs),
                )
            else:
                checks.ok(
                    "DN-3",
                    "the committed planes equal the deployed parameter",
                    f"{len(planes)} planes, entry for entry - the first link of "
                    "code -> parameter -> host",
                )

        if unexpected_open:
            checks.fail(
                "DN-4",
                "no plane is `open` except the ones a decision names",
                f"{', '.join(unexpected_open)} is `open` and no decision names it - a plane whose "
                "list is a DENY list may reach anything not on it. If that is intended, add it to "
                "OPEN_BY_DECISION with the decision that took it; if it is not, the objectives' "
                "restriction (`the restriction is on the SageMaker-MANAGED COMPUTE`) is inverted",
            )
        else:
            checks.ok(
                "DN-4",
                "no plane is `open` except the ones a decision names",
                f"{len(planes) - len(open_planes)} allow-list plane(s); `open`: "
                + ("; ".join(f"{p} ({OPEN_BY_DECISION[p]})" for p in open_planes) or "none")
                + ". An `open` plane's control is the access log, not its list - so an empty one "
                "is permissive by decision, not empty by omission",
            )
        rep.checks_table(checks)
        rep.text("""
A `fail` on DN-2 is the one to act on FIRST, and the action is to delete the apex, not the
subtree entry: Squid refuses to start on that pair, so the finding is an outage waiting for
the next reconfigure rather than a tidy. A redundant row is a warning in Squid and a warning
here.

DN-3 is the FIRST of two links. It compares the repository against the SSM parameter; PX-3
in ./aws/proxy.py compares the parameter against the squid.conf actually running on the host.
A green DN-3 and no PX-3 says what was written reached the parameter, and nothing about what
the proxy is enforcing.

DN-4 is a gate, not information - and the paragraph that stood here said the opposite, because
it described an overlap comparison this report stopped making when the two planes became two
different KINDS of list. What DN-4 asks now is whether every `open` plane was chosen: it fails
on one that is not in OPEN_BY_DECISION, and makes the pass line carry each exception's reason,
so a reader does not have to open a decision file to learn why a plane is open.

A clean run here is a screen, not a proof: this resolver is not the proxy's, and a CDN can
steer a chain by geography. Confirm anything surprising from a request through the proxy.
""")

        rep.h1("6. Calls that failed")
        failed_calls_epilogue(rep, errors)

    note(f"\nwrote {out_label}")
    print(open(out_path, encoding="utf-8").read())
    return 2 if checks.n_fail() else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
