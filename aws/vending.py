#!/usr/bin/env -S uv run --quiet
# vending.py - Stage 14's instrument: whether a business unit's Sandbox is fully vended, read per
# unit from the places a vend writes. A vend fails as an account that is 90 % configured, and each
# check is one of those places, parameterised by unit:
#
#   VN-1  the account is ACTIVE in `Sandboxes`, nested under `Interactive`, and neither the account
#         nor the OU carries a policy of its own (D37, INV-11): per policy type the root enables,
#         the type's AWS-managed full-access document and nothing else. In a run over every
#         declared unit, every ACTIVE account in `Sandboxes` is one of them.
#   VN-2  the unit's CIDR is its `VPC_CIDRS` row, inside `SANDBOX_SUPERNET`, overlapping no other
#         row, and the unit's VPC carries exactly that range under the Name tag the hub's slices
#         resolve it by.
#   VN-3  every `PEERINGS` row the unit is an end of is an `active` connection, routed from each
#         of the unit's private route tables and back to each of its private subnets (NT-11's
#         rule, per unit); the unit holds no other peering, and names the same peer slices as
#         the hand-built unit.
#   VN-4  the unit's child zone `<env>.awsds.internal` is associated with the unit's VPC and the
#         hub's and no other, its authorization toward the hub still exists (INT-22), the unit's
#         VPC resolves the apex and its child zone and nothing else, and the apex's authorization
#         toward the unit's VPC still exists.
#   VN-5  the proxy admits the unit's range: a TCP/3128 rule on its security group, and a plane of
#         the allow-list parameter whose source is that range, in `allowlist` mode (PX-1's and
#         PX-3's rules, per unit).
#   VN-6  the group holding `DataScientistAccess` on the unit holds no other seat in `Sandboxes`,
#         and a unit's own group holds no seat anywhere else. The shared
#         `sso-group-data-scientists` is the unit's principal while one unit is declared, and its
#         seats past the graduation boundary (`Workloads`) stay on it by design
#         (docs/ORGANIZATION.md, the dagger under Assignments): a note, not a failure, until the
#         second unit, when the shared group holding a unit's seat is the failure (Lesson 50).
#
# Every expectation is generated from scripts/tfhygiene/backend.py (VPC_CIDRS, PEERINGS,
# VPN_HOST_SLICE, PROFILES, ENV_TOKENS, SMUS_MEMBERS), read as text: aws/ imports nothing from
# scripts/. A vend adds rows there, and this file reads them.
#
#   needs:    a live SSO session as the infrastructure user; one login covers every profile:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/vending.py              # every unit backend.py declares
#             ./aws/vending.py sandbox      # only the account folders named
#   writes:   aws/output/vending.txt   (untracked - see .gitignore)
#   reads:    in Identity - organizations:ListRoots, ListOrganizationalUnitsForParent,
#             ListAccountsForParent, DescribeAccount, DescribeOrganizationalUnit, ListParents,
#             ListPoliciesForTarget; sso-admin:ListInstances, ListPermissionSets,
#             DescribePermissionSet, ListAccountAssignments, ListAccountAssignmentsForPrincipal;
#             identitystore:DescribeGroup. In each unit and in Production - ec2:DescribeVpcs,
#             DescribeSubnets, DescribeRouteTables, DescribeVpcPeeringConnections;
#             route53:ListHostedZones, GetHostedZone, ListHostedZonesByVPC,
#             ListVPCAssociationAuthorizations. In Production - ssm:GetParameter,
#             ec2:DescribeSecurityGroups. And sts:GetCallerIdentity. It never creates, updates
#             or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# Every object it reads is [P] (foundation/, networking/, the identity plane), so a run with the
# environment down is a full reading.
#
# What it cannot see, since an empty listing and a missing account look alike:
#   - Control Tower's own view: the controls enabled on `Sandboxes` and whether the account is
#     enrolled answer only from Management (INV-12). VN-1 sees a preventive control as the
#     `aws-guardrails-*` SCP it attaches; a detective or proactive control attaches none.
#   - The rest of a vend's obligations, which other instruments read per account: account-level
#     S3 Block Public Access (step 3b, ./aws/account-bpa.py), the domain association and the
#     blueprint configurations (step 4, ./aws/studio.py), the lake plumbing (step 5,
#     ./aws/datalake.py), the Bedrock gates (step 1, ./aws/bedrock.py).
#   - Whether a packet arrives. A route, a zone association and a plane are configuration; the
#     behavioural proof is a probe from inside the unit (Lesson 20).

from __future__ import annotations

import ast
import ipaddress
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

from awslib import cidr, context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, failed_calls_epilogue, note

OUT_NAME = "vending.txt"

# backend.py, read as text: aws/ imports nothing from scripts/, or the CloudShell fallback dies.
BACKEND_FILE = ("scripts", "tfhygiene", "backend.py")
BACKEND_NAMES = (
    "PROFILES",
    "ENV_TOKENS",
    "SANDBOX_SUPERNET",
    "VPC_CIDRS",
    "VPC_NAME_SUFFIXES",
    "PEERINGS",
    "VPN_HOST_SLICE",
    "SMUS_MEMBERS",
)

# The hand-built unit, which Stage 14 adopts rather than vends (step 7). A vended unit is
# compared with it where backend.py carries no per-unit expectation: its peer slices.
REFERENCE_UNIT = "sandbox"
IDENTITY_FOLDER = "identity"
UNIT_SLICE = "foundation"

# VN-1. The OU contract (D23, D37), and the document Organizations attaches to every node when a
# policy type is enabled. Only the SCP and RCP types have one.
SANDBOXES_OU = "Sandboxes"
INTERACTIVE_OU = "Interactive"
DEFAULT_DOCUMENTS = {
    "SERVICE_CONTROL_POLICY": "FullAWSAccess",
    "RESOURCE_CONTROL_POLICY": "RCPFullAWSAccess",
}
CLOSED_STATES = ("SUSPENDED", "PENDING_CLOSURE", "CLOSED")

# VN-4. The apex and the child zone of the INT-22 family; the child is named by the env token.
APEX_ZONE = "awsds.internal"
CHILD_ZONE = "{env}.awsds.internal"

# VN-5. The proxy's contracts, the ones ./aws/proxy.py reads, built with the hub's env token.
PROXY_PARAMETER = "/datascience/{env}/proxy/allowlist"
PROXY_GROUP = "awsds-{env}-proxy"
PROXY_PORT = 3128

# VN-6. The seat a unit's data scientists hold, the shared group, the per-unit group's prefix
# (docs/ORGANIZATION.md, SSO Groups), and the OU past the graduation boundary.
UNIT_PERMISSION_SET = "DataScientistAccess"
SHARED_GROUP = "sso-group-data-scientists"
UNIT_GROUP_PREFIX = "sso-group-data-scientists-"
WORKLOADS_OU = "Workloads"


# ------------------------------------------------------------------------------- backend.py


def module_tree(path: Path):
    """The parsed module, or None when the file is absent or does not parse."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError):
        return None


def assigned_literals(tree, names: tuple) -> dict:
    """{name: literal} for each module-level ``name = <literal>`` (annotated or not) in ``names``."""
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        else:
            continue
        for target in targets:
            if isinstance(target, ast.Name) and target.id in names:
                try:
                    out[target.id] = ast.literal_eval(value)
                except ValueError:
                    pass
    return out


@dataclass
class Backend:
    """The tables a vend adds rows to."""

    profiles: dict  # account folder -> SSO profile
    env_tokens: dict  # account folder -> <env> token
    supernet: str
    vpc_cidrs: dict  # (account folder, slice) -> /16
    name_suffixes: dict  # (account folder, slice) -> VPC name suffix
    peerings: list  # (requester account, requester slice, accepter account, accepter slice)
    hub: tuple  # (account folder, slice) of VPC-Networking
    members: list  # SMUS_MEMBERS

    def vpc_name(self, account: str, slice_name: str) -> str:
        """The Name tag the vpc module gives a slice's VPC, the one peer slices resolve it by."""
        env = self.env_tokens.get(account, account)
        suffix = self.name_suffixes.get((account, slice_name), "")
        return f"awsds-{env}-{suffix}-vpc" if suffix else f"awsds-{env}-vpc"

    def peer_rows(self, unit: str) -> list:
        """(peer account, peer slice, the unit's role) of every PEERINGS row the unit is an end of."""
        rows = []
        for r_acct, r_slice, a_acct, a_slice in self.peerings:
            if (r_acct, r_slice) == (unit, UNIT_SLICE):
                rows.append((a_acct, a_slice, "requester"))
            elif (a_acct, a_slice) == (unit, UNIT_SLICE):
                rows.append((r_acct, r_slice, "accepter"))
        return rows


def read_backend(repo_root: Path) -> tuple:
    """(Backend, '') or (None, why it could not be read)."""
    path = repo_root.joinpath(*BACKEND_FILE)
    tree = module_tree(path)
    if tree is None:
        return None, f"{'/'.join(BACKEND_FILE)} is absent or does not parse"
    found = assigned_literals(tree, BACKEND_NAMES)
    missing = [n for n in BACKEND_NAMES if n not in found]
    if missing:
        return None, f"{'/'.join(BACKEND_FILE)} assigns no literal to {', '.join(missing)}"
    return (
        Backend(
            profiles=found["PROFILES"],
            env_tokens=found["ENV_TOKENS"],
            supernet=found["SANDBOX_SUPERNET"],
            vpc_cidrs=found["VPC_CIDRS"],
            name_suffixes=found["VPC_NAME_SUFFIXES"],
            peerings=[tuple(r) for r in found["PEERINGS"]],
            hub=tuple(found["VPN_HOST_SLICE"]),
            members=list(found["SMUS_MEMBERS"]),
        ),
        "",
    )


def inside(inner: str, outer: str) -> bool:
    """Whether IPv4 block ``inner`` lies within (or equals) ``outer``."""
    try:
        a = ipaddress.ip_network(inner, strict=False)
        b = ipaddress.ip_network(outer, strict=False)
        return a.version == b.version and a.subnet_of(b)
    except (ValueError, TypeError):
        return False


def declared_units(b: Backend) -> dict:
    """{unit: [where it is declared]}: SMUS_MEMBERS, and every foundation row of VPC_CIDRS inside
    the supernet. The second list holds a unit between its address row and step 4's member row."""
    out: dict = {}
    for account in b.members:
        out.setdefault(account, []).append("SMUS_MEMBERS")
    for (account, slice_name), block in sorted(b.vpc_cidrs.items()):
        if slice_name == UNIT_SLICE and inside(block, b.supernet):
            out.setdefault(account, []).append("VPC_CIDRS inside SANDBOX_SUPERNET")
    return out


# ------------------------------------------------------------------------------- the reads


@dataclass
class Answer:
    """One call's parsed answer."""

    doc: dict
    ok: bool  # False: the call failed, and the failure is in the error log
    absent: bool = False  # True: the error said the thing asked about does not exist


class Reader:
    """One profile's reads: the CLI bound to it, every failure into the shared log."""

    def __init__(self, caller: profiles.Caller, errors: ErrorLog) -> None:
        self.profile = caller.profile
        self.account = caller.account or "-"
        self.live = caller.live
        self.errors = errors
        self.cli = AwsCli(
            profile=caller.profile, region=context.REGION, errors=errors, echo_profile=True
        )

    def json(self, *args: str, absent: str | None = None) -> Answer:
        """``aws <args> --output json``; ``absent`` is the error text that means "none exists"."""
        if not self.live:
            return Answer({}, False)
        res = self.cli.run(*args, "--output", "json", log=False, tolerate=absent)
        if res.tolerated:
            return Answer({}, True, True)
        if not res.ok:
            self.errors.add(args, res.merged, self.profile)
            return Answer({}, False)
        try:
            doc = json.loads(res.stdout or "{}")
        except json.JSONDecodeError:
            self.errors.add(args, f"the answer is not JSON: {res.stdout[:120]}", self.profile)
            return Answer({}, False)
        return Answer(doc if isinstance(doc, dict) else {}, True)

    def pages(self, key: str, *args: str) -> Answer:
        """``json`` for a listing the CLI does not paginate: the ``key`` entries of every page.

        ``ok`` is False when a page failed or the token outlived the page limit; both are
        logged, so a zone reading that stopped short reads as a failed read.
        """
        if not self.live:
            return Answer({}, False)
        listing = self.cli.pages(*args)
        return Answer({key: listing.items(key)}, listing.complete)


def tag_value(tags: list | None, key: str) -> str:
    for t in tags or []:
        if t.get("Key") == key:
            return t.get("Value", "")
    return ""


def joined(items, empty: str = "none") -> str:
    items = list(items)
    return ", ".join(items) if items else empty


# ------------------------------------------------------------------------------- VN-1


@dataclass
class OrgTree:
    """The organization as VN-1 reads it from Identity."""

    ok: bool
    types: list = field(default_factory=list)  # policy types ENABLED on the root
    sandboxes: str | None = None  # the Sandboxes OU id, found under Interactive by name
    sandboxes_path: str = "-"
    census: list | None = None  # [(account id, name, state)] in Sandboxes; None when unread
    ou_attachments: dict = field(default_factory=dict)  # type -> [(id, name, aws managed)] | None


@dataclass
class Placement:
    """One unit's account as Organizations sees it."""

    complete: bool = True
    name: str = "-"
    state: str = "-"
    parent: str = "-"  # OU id
    parent_name: str = "-"
    attachments: dict = field(default_factory=dict)  # type -> [(id, name, aws managed)] | None


def attachments_of(idn: Reader, target: str, types: list) -> dict:
    """{policy type: [(id, name, aws managed)]} attached directly to one node; None when unread."""
    out = {}
    for policy_type in types:
        ans = idn.json(
            "organizations",
            "list-policies-for-target",
            "--target-id",
            target,
            "--filter",
            policy_type,
        )
        out[policy_type] = (
            [
                (p.get("Id", "-"), p.get("Name", "-"), bool(p.get("AwsManaged")))
                for p in ans.doc.get("Policies", [])
            ]
            if ans.ok
            else None
        )
    return out


def child_ou(idn: Reader, parent: str, name: str) -> tuple:
    """(id, path) of the OU called ``name`` directly under ``parent``; (None, '-') when absent."""
    ans = idn.json("organizations", "list-organizational-units-for-parent", "--parent-id", parent)
    for ou in ans.doc.get("OrganizationalUnits", []):
        if ou.get("Name") == name:
            return ou.get("Id"), ou.get("Path") or "-"
    return None, "-"


def read_tree(idn: Reader) -> OrgTree:
    roots = idn.json("organizations", "list-roots")
    if not roots.ok or not roots.doc.get("Roots"):
        return OrgTree(False)
    root = roots.doc["Roots"][0]
    tree = OrgTree(
        True,
        types=[t.get("Type") for t in root.get("PolicyTypes", []) if t.get("Status") == "ENABLED"],
    )
    interactive, _ = child_ou(idn, root.get("Id", "-"), INTERACTIVE_OU)
    if interactive:
        tree.sandboxes, tree.sandboxes_path = child_ou(idn, interactive, SANDBOXES_OU)
    if tree.sandboxes:
        listing = idn.json(
            "organizations", "list-accounts-for-parent", "--parent-id", tree.sandboxes
        )
        if listing.ok:
            tree.census = [
                (a.get("Id", "-"), a.get("Name", "-"), a.get("State") or a.get("Status") or "-")
                for a in listing.doc.get("Accounts", [])
            ]
        tree.ou_attachments = attachments_of(idn, tree.sandboxes, tree.types)
    return tree


def read_placement(idn: Reader, account: str, types: list) -> Placement:
    p = Placement()
    acct = idn.json("organizations", "describe-account", "--account-id", account)
    parents = idn.json("organizations", "list-parents", "--child-id", account)
    p.complete = acct.ok and parents.ok
    info = acct.doc.get("Account") or {}
    p.name = info.get("Name", "-")
    p.state = info.get("State") or info.get("Status") or "-"
    for parent in parents.doc.get("Parents", []):
        p.parent = parent.get("Id", "-")
        if parent.get("Type") == "ORGANIZATIONAL_UNIT":
            ou = idn.json(
                "organizations",
                "describe-organizational-unit",
                "--organizational-unit-id",
                p.parent,
            )
            p.complete = p.complete and ou.ok
            p.parent_name = (ou.doc.get("OrganizationalUnit") or {}).get("Name", "-")
        else:
            p.parent_name = f"({parent.get('Type', '-').lower()})"
    p.attachments = attachments_of(idn, account, types)
    p.complete = p.complete and all(v is not None for v in p.attachments.values())
    return p


def attachment_findings(attachments: dict) -> list:
    """What is wrong with one node's direct attachments: a document of its own, or a type's
    full-access default missing, which denies everything on that node."""
    findings = []
    for policy_type, docs in sorted(attachments.items()):
        if docs is None:
            continue
        default = DEFAULT_DOCUMENTS.get(policy_type)
        own = [
            f"{name} ({pid})" for pid, name, managed in docs if not (managed and name == default)
        ]
        if own:
            findings.append(f"{policy_type} attached here: {', '.join(own)}")
        if default and not any(managed and name == default for _pid, name, managed in docs):
            findings.append(f"{policy_type}: {default} is missing, so the type denies everything")
    return findings


def attachment_rows(attachments: dict) -> list:
    """Section 2's table of one node: `(none)` for a type read empty, `(unread)` for a failed read."""
    rows = ["TYPE\tPOLICY\tID\tAWS MANAGED"]
    for policy_type, docs in sorted(attachments.items()):
        if docs is None:
            rows.append(f"{policy_type}\t(unread)\t-\t-")
        elif not docs:
            rows.append(f"{policy_type}\t(none)\t-\t-")
        else:
            rows += [f"{policy_type}\t{name}\t{pid}\t{managed}" for pid, name, managed in docs]
    return rows


def attachment_summary(attachments: dict) -> str:
    parts = []
    for policy_type, docs in sorted(attachments.items()):
        if docs is None:
            parts.append(f"{policy_type} unread")
        else:
            parts.append(f"{policy_type} {joined((name for _i, name, _m in docs), 'none')}")
    return "; ".join(parts)


def judge_tree(checks: Checks, tree: OrgTree, units_judged: dict, every_unit: bool) -> None:
    """VN-1's two OU-level questions: what `Sandboxes` carries, and who lives in it."""
    what = f"`{SANDBOXES_OU}` carries nothing of its own"
    if not tree.ok:
        checks.fail("VN-1", what, "the organization was not read (section 10)")
        return
    if not tree.sandboxes:
        checks.fail(
            "VN-1", what, f"no OU named {SANDBOXES_OU} directly under {INTERACTIVE_OU} (D23)"
        )
        return
    unread = [t for t, docs in tree.ou_attachments.items() if docs is None]
    findings = attachment_findings(tree.ou_attachments)
    if unread:
        checks.fail("VN-1", what, f"attachments unread for {', '.join(unread)} (section 10)")
    if findings:
        checks.fail(
            "VN-1",
            what,
            "; ".join(findings) + ". D37: nothing is attached there unless it differs from "
            f"{INTERACTIVE_OU}'s, and a document there is a divergence in writing or drift.",
        )
    elif not unread:
        checks.ok("VN-1", what, attachment_summary(tree.ou_attachments))

    what = f"every account in `{SANDBOXES_OU}` is a declared unit"
    if tree.census is None:
        checks.fail("VN-1", what, "the OU's accounts were not read (section 10)")
        return
    known = {account: unit for unit, account in units_judged.items()}
    strangers = [a for a in tree.census if a[0] not in known]
    if not every_unit:
        checks.note(
            "VN-1",
            what,
            f"not judged: the run named a subset of the units; {len(tree.census)} account(s) "
            f"in the OU, {len(strangers)} outside this run",
        )
        return
    active = [f"{name} ({state})" for _i, name, state in strangers if state not in CLOSED_STATES]
    closed = [f"{name} ({state})" for _i, name, state in strangers if state in CLOSED_STATES]
    if active:
        checks.fail(
            "VN-1",
            what,
            f"{joined(active)}: an account no backend.py unit describes, which is a vend the "
            "repository never recorded or an account moved in by hand",
        )
    if closed:
        checks.note(
            "VN-1",
            what,
            f"{joined(closed)}: a closed account stays in its OU for about 90 days (Stage 14 step 6)",
        )
    if not active:
        checks.ok(
            "VN-1",
            what,
            f"{len(tree.census) - len(closed)} active account(s), each a declared unit: "
            + joined(f"{name} = {known[i]}" for i, name, _s in tree.census if i in known),
        )


def judge_placement(checks: Checks, unit: str, tree: OrgTree, p: Placement | None) -> None:
    what = f"{unit}: ACTIVE in `{SANDBOXES_OU}`, nothing attached to the account"
    if p is None or not p.complete:
        checks.fail("VN-1", what, "the account's placement was not read (section 10)")
        return
    problems = []
    if p.state != "ACTIVE":
        problems.append(f"the account is {p.state}")
    if not tree.sandboxes or p.parent != tree.sandboxes:
        problems.append(
            f"its parent is {p.parent_name} ({p.parent}), not {INTERACTIVE_OU}/{SANDBOXES_OU}: "
            "the OU is what governs the account on arrival (step 2)"
        )
    problems += attachment_findings(p.attachments)
    if problems:
        checks.fail("VN-1", what, f"{p.name}: " + "; ".join(problems))
    else:
        checks.ok(
            "VN-1",
            what,
            f"{p.name} in {INTERACTIVE_OU}/{SANDBOXES_OU}; {attachment_summary(p.attachments)}",
        )


# ------------------------------------------------------------------------------- VN-2


@dataclass
class Vpc:
    vpc_id: str
    primary: str
    blocks: list  # every associated IPv4 block, primary included
    name: str
    is_default: bool


def read_vpcs(reader: Reader) -> list | None:
    ans = reader.json("ec2", "describe-vpcs")
    if not ans.ok:
        return None
    vpcs = []
    for v in ans.doc.get("Vpcs", []):
        blocks = [
            a.get("CidrBlock", "-")
            for a in v.get("CidrBlockAssociationSet", [])
            if (a.get("CidrBlockState") or {}).get("State") == "associated"
        ] or [v.get("CidrBlock", "-")]
        vpcs.append(
            Vpc(
                v.get("VpcId", "-"),
                v.get("CidrBlock", "-"),
                blocks,
                tag_value(v.get("Tags"), "Name") or "-",
                bool(v.get("IsDefault")),
            )
        )
    return vpcs


def vpc_by_block(vpcs: list | None, block: str) -> Vpc | None:
    """The VPC whose primary block is ``block``: the range is this estate's name for a VPC."""
    for v in vpcs or []:
        if v.primary == block:
            return v
    return None


def judge_allocation(checks: Checks, b: Backend, unit: str, vpcs: list | None) -> None:
    what = f"{unit}: the address allocation"
    block = b.vpc_cidrs.get((unit, UNIT_SLICE))
    if block is None:
        checks.fail(
            "VN-2",
            what,
            f"no VPC_CIDRS row for ({unit}, {UNIT_SLICE}): the address plan is authored before "
            "the folder exists (Stage 3 step 1.3)",
        )
        return
    problems = []
    if not inside(block, b.supernet):
        problems.append(f"{block} is outside SANDBOX_SUPERNET {b.supernet}")
    clashes = [
        f"{acct}/{sl} {other}"
        for (acct, sl), other in sorted(b.vpc_cidrs.items())
        if (acct, sl) != (unit, UNIT_SLICE) and cidr.overlap(block, other)
    ]
    if clashes:
        problems.append(f"{block} overlaps {', '.join(clashes)}")
    if vpcs is None:
        checks.fail("VN-2", what, "the unit's VPCs were not read (section 10)")
        return
    carrying = [v for v in vpcs if any(cidr.overlap(block, c) for c in v.blocks)]
    expected_name = b.vpc_name(unit, UNIT_SLICE)
    if not carrying:
        problems.append(f"no VPC in the unit's account carries {block}")
    elif len(carrying) > 1:
        problems.append(
            f"{len(carrying)} VPCs overlap {block}: {joined(v.vpc_id for v in carrying)}"
        )
    else:
        v = carrying[0]
        if v.primary != block or v.blocks != [block]:
            problems.append(f"{v.vpc_id} carries {joined(v.blocks)}, the allocation is {block}")
        if v.name != expected_name:
            problems.append(
                f"{v.vpc_id} is named {v.name}; the hub's slices resolve it as {expected_name} "
                "(a name another account resolves by is a contract, Lesson 48)"
            )
    if problems:
        checks.fail("VN-2", what, "; ".join(problems))
    else:
        checks.ok(
            "VN-2",
            what,
            f"{block} inside {b.supernet}, overlapping none of the other "
            f"{len(b.vpc_cidrs) - 1} rows; {carrying[0].vpc_id} carries it as {expected_name}",
        )
    others = [v for v in vpcs if v not in carrying]
    if others:
        checks.note(
            "VN-2",
            f"{unit}: other VPCs in the unit's account",
            joined(f"{v.vpc_id} {v.primary} {v.name}" for v in others)
            + ": NT-1's question (./aws/networking.py), not the allocation's",
        )


# ------------------------------------------------------------------------------- VN-3


@dataclass
class Route:
    table: str
    destination: str
    target: str
    state: str


@dataclass
class VpcRoutes:
    """One VPC's route tables, and which of them serve its private tier."""

    complete: bool
    routes: list = field(default_factory=list)  # [Route]
    tables: list = field(default_factory=list)  # every route table id
    private_tables: list = field(default_factory=list)
    private_subnets: list = field(default_factory=list)  # [(subnet id, block)]


def read_routes(reader: Reader, vpc_id: str, want_subnets: bool) -> VpcRoutes:
    """The VPC's routes; with ``want_subnets``, its private tier (subnets tagged Tier=private) and
    the tables those subnets use, the main table for a subnet with no association of its own."""
    rts = reader.json("ec2", "describe-route-tables", "--filters", f"Name=vpc-id,Values={vpc_id}")
    out = VpcRoutes(rts.ok)
    main = None
    by_subnet = {}
    for t in rts.doc.get("RouteTables", []):
        table = t.get("RouteTableId", "-")
        out.tables.append(table)
        for a in t.get("Associations", []):
            if a.get("Main"):
                main = table
            if a.get("SubnetId"):
                by_subnet[a["SubnetId"]] = table
        for r in t.get("Routes", []):
            target = (
                r.get("VpcPeeringConnectionId")
                or r.get("GatewayId")
                or r.get("NatGatewayId")
                or r.get("TransitGatewayId")
                or r.get("NetworkInterfaceId")
                or r.get("InstanceId")
                or "-"
            )
            destination = (
                r.get("DestinationCidrBlock")
                or r.get("DestinationIpv6CidrBlock")
                or r.get("DestinationPrefixListId")
                or "-"
            )
            out.routes.append(Route(table, destination, target, r.get("State", "-")))
    if want_subnets:
        subnets = reader.json(
            "ec2", "describe-subnets", "--filters", f"Name=vpc-id,Values={vpc_id}"
        )
        out.complete = out.complete and subnets.ok
        for s in subnets.doc.get("Subnets", []):
            if tag_value(s.get("Tags"), "Tier") != "private":
                continue
            out.private_subnets.append((s.get("SubnetId", "-"), s.get("CidrBlock", "-")))
            table = by_subnet.get(s.get("SubnetId")) or main
            if table and table not in out.private_tables:
                out.private_tables.append(table)
    return out


@dataclass
class Connection:
    pcx: str
    status: str
    requester: str
    requester_block: str
    accepter: str
    accepter_block: str

    def joins(self, a: str, b: str) -> bool:
        return {self.requester, self.accepter} == {a, b}

    def far_block(self, vpc_id: str) -> str:
        return self.accepter_block if self.requester == vpc_id else self.requester_block


def read_connections(reader: Reader) -> list | None:
    ans = reader.json("ec2", "describe-vpc-peering-connections")
    if not ans.ok:
        return None
    out = []
    for c in ans.doc.get("VpcPeeringConnections", []):
        req = c.get("RequesterVpcInfo") or {}
        acc = c.get("AccepterVpcInfo") or {}
        out.append(
            Connection(
                c.get("VpcPeeringConnectionId", "-"),
                (c.get("Status") or {}).get("Code", "-"),
                req.get("VpcId", "-"),
                req.get("CidrBlock", "-"),
                acc.get("VpcId", "-"),
                acc.get("CidrBlock", "-"),
            )
        )
    return out


@dataclass
class Peering:
    """One PEERINGS row of a unit, as AWS answers it from both ends."""

    peer: tuple  # (account folder, slice)
    role: str  # the unit's role in the row
    peer_block: str
    peer_vpc: Vpc | None = None
    peer_read: bool = False  # whether the peer account's VPCs were read
    connections: list = field(default_factory=list)  # [Connection] between the two VPCs
    unit_routes: list = field(default_factory=list)  # [Route] via the active connection
    peer_routes: list = field(default_factory=list)
    peer_complete: bool = True

    @property
    def active(self) -> Connection | None:
        for c in self.connections:
            if c.status == "active":
                return c
        return None


def judge_peering(
    checks: Checks, unit: str, block: str, own: VpcRoutes, p: Peering, label: str
) -> None:
    what = f"{unit} <-> {label}"
    if not p.peer_read:
        checks.fail("VN-3", what, "the peer account's VPCs were not read (section 10)")
        return
    if p.peer_vpc is None:
        checks.fail("VN-3", what, f"no VPC carries {p.peer_block} in the peer account")
        return
    c = p.active
    if c is None:
        seen = joined(f"{x.pcx} {x.status}" for x in p.connections)
        checks.fail(
            "VN-3",
            what,
            f"no active connection between the two VPCs (seen: {seen}); the PEERINGS row is "
            "generated into both slices, so a pending one is the accepter's apply not yet run",
        )
        return
    if not own.complete or not p.peer_complete:
        checks.fail("VN-3", what, f"{c.pcx}: a route table read failed (section 10)")
        return
    problems = []
    for table in own.private_tables:
        good = [
            r
            for r in p.unit_routes
            if r.table == table and r.state == "active" and inside(r.destination, p.peer_block)
        ]
        if not good:
            problems.append(f"the unit's private table {table} has no route to {p.peer_block}")
    if not own.private_tables:
        problems.append("the unit's VPC has no subnet tagged Tier=private")
    for subnet, sub_block in own.private_subnets:
        if not any(r.state == "active" and inside(sub_block, r.destination) for r in p.peer_routes):
            problems.append(f"no return route in the peer VPC covers {subnet} ({sub_block})")
    dead = [
        f"{r.table} {r.destination} {r.state}"
        for r in p.unit_routes + p.peer_routes
        if r.state != "active"
    ]
    if dead:
        problems.append(f"routes via {c.pcx} not active: {joined(dead)}")
    stray = [
        f"{r.table} {r.destination}"
        for r in p.unit_routes
        if not inside(r.destination, p.peer_block)
    ] + [f"{r.table} {r.destination}" for r in p.peer_routes if not inside(r.destination, block)]
    if stray:
        problems.append(
            f"routes via {c.pcx} to an address the peering cannot carry: {joined(stray)}"
        )
    if problems:
        checks.fail("VN-3", what, f"{c.pcx}: " + "; ".join(problems))
    else:
        unit_tables = {r.table for r in p.unit_routes}
        peer_tables = {r.table for r in p.peer_routes}
        checks.ok(
            "VN-3",
            what,
            f"{c.pcx} active; {len(p.unit_routes)} routes out of {len(unit_tables)} unit "
            f"tables, every private one among them; {len(p.peer_routes)} back from "
            f"{len(peer_tables)} peer tables, covering each private subnet",
        )


def judge_peer_shape(
    checks: Checks, b: Backend, unit: str, peerings: list, connections: list | None, unit_vpc: Vpc
) -> None:
    """The unit names the reference unit's peer slices, and holds no peering PEERINGS lacks."""
    what = f"{unit}: the peer slices"
    mine = sorted(p.peer for p in peerings)
    if not mine:
        checks.fail("VN-3", what, "no PEERINGS row names the unit")
    elif unit != REFERENCE_UNIT and REFERENCE_UNIT not in b.profiles:
        checks.note(
            "VN-3", what, f"the reference unit {REFERENCE_UNIT} has no PROFILES row to compare with"
        )
    elif unit != REFERENCE_UNIT:
        ref = sorted((a, s) for a, s, _r in b.peer_rows(REFERENCE_UNIT))
        if mine != ref:
            checks.fail(
                "VN-3",
                what,
                f"{joined('/'.join(x) for x in mine)}, where the hand-built unit has "
                f"{joined('/'.join(x) for x in ref)}: a vend adds rows, not a design",
            )
        else:
            checks.ok("VN-3", what, f"the hand-built unit's: {joined('/'.join(x) for x in mine)}")
    if connections is None:
        return
    expected = {p.peer_vpc.vpc_id for p in peerings if p.peer_vpc}
    extra = [
        f"{c.pcx} to {c.far_block(unit_vpc.vpc_id)}"
        for c in connections
        if c.status == "active"
        and unit_vpc.vpc_id in (c.requester, c.accepter)
        and ({c.requester, c.accepter} - {unit_vpc.vpc_id}).isdisjoint(expected)
    ]
    if extra:
        checks.fail(
            "VN-3",
            f"{unit}: no peering beyond PEERINGS",
            f"{joined(extra)}: the absent peerings are the control (docs/NETWORK.md)",
        )


# ------------------------------------------------------------------------------- VN-4


@dataclass
class Zones:
    """The unit's child zone, the zones its VPC resolves, and the apex's authorizations."""

    complete: bool = True
    child_ids: list = field(default_factory=list)  # private zones named like the child
    child_vpcs: list = field(default_factory=list)  # [vpc id]
    child_authorized: list = field(default_factory=list)  # [vpc id]
    resolved: list = field(default_factory=list)  # [(zone id, name, owner account)]
    hub_view: list = field(default_factory=list)  # zones the hub VPC resolves
    hub_read: bool = False
    apex_id: str = "-"
    apex_authorized: list | None = None  # None when the apex owner holds no profile here


def zone_summaries(reader: Reader, vpc_id: str) -> tuple:
    # ListHostedZonesByVPC has no CLI paginator: Reader.pages follows NextToken.
    ans = reader.pages(
        "HostedZoneSummaries",
        "route53",
        "list-hosted-zones-by-vpc",
        "--vpc-id",
        vpc_id,
        "--vpc-region",
        context.REGION,
    )
    rows = [
        (
            z.get("HostedZoneId", "-"),
            (z.get("Name") or "-").rstrip("."),
            (z.get("Owner") or {}).get("OwningAccount")
            or (z.get("Owner") or {}).get("OwningService")
            or "-",
        )
        for z in ans.doc.get("HostedZoneSummaries", [])
    ]
    return rows, ans.ok


def authorized_vpcs(reader: Reader, zone_id: str) -> tuple:
    ans = reader.json("route53", "list-vpc-association-authorizations", "--hosted-zone-id", zone_id)
    return [v.get("VPCId", "-") for v in ans.doc.get("VPCs", [])], ans.ok


def read_zones(
    unit_reader: Reader,
    hub_reader: Reader,
    readers_by_account: dict,
    child: str,
    unit_vpc: str,
    hub_vpc: str | None,
) -> Zones:
    z = Zones()
    listing = unit_reader.json("route53", "list-hosted-zones")
    z.complete = listing.ok
    for hz in listing.doc.get("HostedZones", []):
        if (hz.get("Config") or {}).get("PrivateZone") and hz.get("Name", "").rstrip(".") == child:
            z.child_ids.append(hz.get("Id", "-").rsplit("/", 1)[-1])
    if len(z.child_ids) == 1:
        zone = unit_reader.json("route53", "get-hosted-zone", "--id", z.child_ids[0])
        z.child_vpcs = [v.get("VPCId", "-") for v in zone.doc.get("VPCs", [])]
        z.child_authorized, ok = authorized_vpcs(unit_reader, z.child_ids[0])
        z.complete = z.complete and zone.ok and ok
    z.resolved, ok = zone_summaries(unit_reader, unit_vpc)
    z.complete = z.complete and ok
    if hub_vpc:
        z.hub_view, z.hub_read = zone_summaries(hub_reader, hub_vpc)
    for zone_id, name, owner in z.resolved:
        if name == APEX_ZONE:
            z.apex_id = zone_id
            owner_reader = readers_by_account.get(owner)
            if owner_reader is not None:
                z.apex_authorized, ok = authorized_vpcs(owner_reader, zone_id)
                z.complete = z.complete and ok
    return z


def judge_zones(
    checks: Checks,
    unit: str,
    unit_account: str,
    child: str,
    z: Zones,
    unit_vpc: Vpc,
    hub_vpc: Vpc | None,
) -> None:
    what = f"{unit}: {child} and the apex"
    if not z.complete:
        checks.fail("VN-4", what, "a zone read failed (section 10)")
        return
    if hub_vpc is None:
        checks.fail("VN-4", what, "the hub's VPC was not resolved (VN-3's peer reading)")
        return
    if len(z.child_ids) != 1:
        checks.fail(
            "VN-4",
            what,
            f"{len(z.child_ids)} private zone(s) named {child} in the unit's account, one expected",
        )
        return
    problems = []
    want = {unit_vpc.vpc_id, hub_vpc.vpc_id}
    have = set(z.child_vpcs)
    if want - have:
        problems.append(f"{child} is not associated with {joined(sorted(want - have))}")
    if have - want:
        problems.append(
            f"{child} is also associated with {joined(sorted(have - want))}, a VPC INT-22 keeps out"
        )
    if hub_vpc.vpc_id not in z.child_authorized:
        problems.append(
            f"no authorization toward the hub's {hub_vpc.vpc_id} on {child}: INT-22 keeps it, so a "
            "rebuilt hub VPC can associate again"
        )
    stray = [v for v in z.child_authorized if v != hub_vpc.vpc_id]
    if stray:
        problems.append(f"{child} also authorizes {joined(stray)}, which may associate itself")
    if z.hub_read and not any(
        i == z.child_ids[0] and owner == unit_account for i, _n, owner in z.hub_view
    ):
        problems.append(f"the hub's own listing does not show {child} owned by the unit")
    if not z.hub_read:
        problems.append("the hub's zone listing was not read (section 10)")
    names = {name for _i, name, _o in z.resolved}
    if {APEX_ZONE, child} - names:
        problems.append(
            f"the unit's VPC does not resolve {joined(sorted({APEX_ZONE, child} - names))}: "
            "gitlab.awsds.internal NXDOMAINs there (step 1)"
        )
    if names - {APEX_ZONE, child}:
        problems.append(
            f"the unit's VPC also resolves {joined(sorted(names - {APEX_ZONE, child}))}, "
            "a plane INT-22 keeps it out of"
        )
    if z.apex_authorized is None:
        checks.note(
            "VN-4",
            f"{unit}: the apex's authorization",
            "the apex's owner holds no profile in this run, so its authorizations were not read",
        )
    elif unit_vpc.vpc_id not in z.apex_authorized:
        problems.append(
            f"no authorization toward the unit's {unit_vpc.vpc_id} on {APEX_ZONE}, which "
            "production/foundation keeps for a VPC rebuild"
        )
    if problems:
        checks.fail("VN-4", what, "; ".join(problems))
    else:
        checks.ok(
            "VN-4",
            what,
            f"{child} ({z.child_ids[0]}) associated with the unit's VPC and the hub's, authorized "
            f"toward the hub; the unit's VPC resolves {APEX_ZONE} and {child} only"
            + ("" if z.apex_authorized is None else ", and the apex authorizes it"),
        )


# ------------------------------------------------------------------------------- VN-5


@dataclass
class Proxy:
    """The proxy's two gates, read in the hub's account."""

    parameter_read: bool = False
    parameter_absent: bool = False
    planes: dict = field(default_factory=dict)  # plane -> its document
    group_read: bool = False
    rules: list = field(default_factory=list)  # [(group id, block)] of TCP/3128 ingress


def read_proxy(hub: Reader, env: str) -> Proxy:
    out = Proxy()
    name = PROXY_PARAMETER.format(env=env)
    ans = hub.json("ssm", "get-parameter", "--name", name, absent="ParameterNotFound")
    out.parameter_read = ans.ok
    out.parameter_absent = ans.absent
    if ans.ok and not ans.absent:
        try:
            doc = json.loads((ans.doc.get("Parameter") or {}).get("Value") or "{}")
        except json.JSONDecodeError:
            doc = {}
            out.parameter_read = False
            hub.errors.add(("ssm", "get-parameter", "--name", name), "not JSON", hub.profile)
        out.planes = {k: v for k, v in doc.items() if isinstance(v, dict)}
    groups = hub.json(
        "ec2",
        "describe-security-groups",
        "--filters",
        f"Name=group-name,Values={PROXY_GROUP.format(env=env)}",
    )
    out.group_read = groups.ok
    for g in groups.doc.get("SecurityGroups", []):
        for perm in g.get("IpPermissions", []):
            if perm.get("IpProtocol") != "tcp":
                continue
            if perm.get("FromPort") != PROXY_PORT or perm.get("ToPort") != PROXY_PORT:
                continue
            for rng in perm.get("IpRanges", []):
                out.rules.append((g.get("GroupId", "-"), rng.get("CidrIp", "-")))
    return out


def judge_proxy(checks: Checks, unit: str, block: str, proxy: Proxy, env: str) -> None:
    what = f"{unit}: the proxy admits {block}"
    plane_key = f"{unit}-{UNIT_SLICE}"
    problems, notes = [], []
    if not proxy.parameter_read:
        problems.append("the allow-list parameter was not read (section 10)")
    elif proxy.parameter_absent:
        problems.append(f"{PROXY_PARAMETER.format(env=env)} does not exist")
    else:
        plane = proxy.planes.get(plane_key)
        if plane is None:
            problems.append(
                f"no plane {plane_key}: production/networking generates one per PEERINGS row, "
                "so the hub's apply has not run since the row was added"
            )
        else:
            sources = list(plane.get("sources") or [])
            if sources != [block]:
                problems.append(f"plane {plane_key} names sources {joined(sources)}, not {block}")
            if plane.get("mode") != "allowlist":
                problems.append(
                    f"plane {plane_key} is {plane.get('mode')!r}: a compute plane is an "
                    "allow-list, and `open` is a decision nobody took (DN-4)"
                )
            if not plane.get("allow"):
                notes.append(
                    f"plane {plane_key} allows no name, so the proxy refuses every request from "
                    "the unit's notebooks"
                )
        overlapping = [
            k
            for k, v in sorted(proxy.planes.items())
            if k != plane_key and any(cidr.overlap(block, s) for s in v.get("sources") or [])
        ]
        if overlapping:
            problems.append(f"{block} is also a source of {joined(overlapping)}")
    if not proxy.group_read:
        problems.append("the proxy's security group was not read (section 10)")
    elif not proxy.rules:
        problems.append(f"{PROXY_GROUP.format(env=env)} has no TCP/{PROXY_PORT} rule at all")
    elif not any(c == block for _g, c in proxy.rules):
        wider = [c for _g, c in proxy.rules if inside(block, c)]
        if wider:
            notes.append(f"TCP/{PROXY_PORT} admits {block} only through {joined(wider)}")
        else:
            problems.append(
                f"no TCP/{PROXY_PORT} rule admits {block}: the plane exists and every connection "
                "times out"
            )
    for line in notes:
        checks.note("VN-5", what, line)
    if problems:
        checks.fail("VN-5", what, "; ".join(problems))
    elif proxy.parameter_read:
        plane = proxy.planes.get(plane_key) or {}
        checks.ok(
            "VN-5",
            what,
            f"TCP/{PROXY_PORT} from {block}; plane {plane_key}, allowlist, "
            f"{len(plane.get('allow') or [])} name(s)",
        )


# ------------------------------------------------------------------------------- VN-6


@dataclass
class Seat:
    account: str
    account_name: str
    ou: str
    permission_set: str


@dataclass
class Group:
    """Who holds DataScientistAccess on a unit, and every seat that principal holds."""

    complete: bool = True
    permission_set_found: bool = True
    holders: list = field(default_factory=list)  # [(principal type, principal id, name)]
    seats: list = field(default_factory=list)  # [Seat] of the holder, when it is one group


class Directory:
    """Identity Center and the account tree, read from Identity once and cached."""

    def __init__(self, idn: Reader) -> None:
        self.idn = idn
        self.instance = None
        self.store = None
        self.sets: dict = {}  # name -> arn
        self.names: dict = {}  # arn -> name
        self.places: dict = {}  # account id -> (name, OU name)
        self.complete = True
        ans = idn.json("sso-admin", "list-instances")
        instances = ans.doc.get("Instances", [])
        if not ans.ok or len(instances) != 1:
            self.complete = False
            return
        self.instance = instances[0].get("InstanceArn")
        self.store = instances[0].get("IdentityStoreId")
        listing = idn.json("sso-admin", "list-permission-sets", "--instance-arn", self.instance)
        self.complete = listing.ok
        for arn in listing.doc.get("PermissionSets", []):
            one = idn.json(
                "sso-admin",
                "describe-permission-set",
                "--instance-arn",
                self.instance,
                "--permission-set-arn",
                arn,
            )
            self.complete = self.complete and one.ok
            name = (one.doc.get("PermissionSet") or {}).get("Name", "-")
            self.sets[name] = arn
            self.names[arn] = name

    def place(self, account: str) -> tuple:
        """(account name, the name of its parent OU)."""
        if account not in self.places:
            acct = self.idn.json("organizations", "describe-account", "--account-id", account)
            parents = self.idn.json("organizations", "list-parents", "--child-id", account)
            ou_name = "(root)"
            for parent in parents.doc.get("Parents", []):
                if parent.get("Type") == "ORGANIZATIONAL_UNIT":
                    ou = self.idn.json(
                        "organizations",
                        "describe-organizational-unit",
                        "--organizational-unit-id",
                        parent.get("Id", "-"),
                    )
                    ou_name = (ou.doc.get("OrganizationalUnit") or {}).get("Name", "-")
                    self.complete = self.complete and ou.ok
            self.complete = self.complete and acct.ok and parents.ok
            self.places[account] = ((acct.doc.get("Account") or {}).get("Name", "-"), ou_name)
        return self.places[account]


def read_group(d: Directory, account: str) -> Group:
    g = Group(complete=d.complete)
    arn = d.sets.get(UNIT_PERMISSION_SET)
    if not d.instance or arn is None:
        g.permission_set_found = arn is not None
        return g
    ans = d.idn.json(
        "sso-admin",
        "list-account-assignments",
        "--instance-arn",
        d.instance,
        "--account-id",
        account,
        "--permission-set-arn",
        arn,
    )
    g.complete = g.complete and ans.ok
    for a in ans.doc.get("AccountAssignments", []):
        ptype, pid = a.get("PrincipalType", "-"), a.get("PrincipalId", "-")
        name = "-"
        if ptype == "GROUP":
            grp = d.idn.json(
                "identitystore", "describe-group", "--identity-store-id", d.store, "--group-id", pid
            )
            g.complete = g.complete and grp.ok
            name = grp.doc.get("DisplayName", "-")
        g.holders.append((ptype, pid, name))
    if len(g.holders) != 1 or g.holders[0][0] != "GROUP":
        return g
    seats = d.idn.json(
        "sso-admin",
        "list-account-assignments-for-principal",
        "--instance-arn",
        d.instance,
        "--principal-id",
        g.holders[0][1],
        "--principal-type",
        "GROUP",
    )
    g.complete = g.complete and seats.ok
    for a in seats.doc.get("AccountAssignments", []):
        acct = a.get("AccountId", "-")
        acct_name, ou = d.place(acct)
        g.seats.append(Seat(acct, acct_name, ou, d.names.get(a.get("PermissionSetArn"), "-")))
    g.complete = g.complete and d.complete
    return g


def judge_group(checks: Checks, unit: str, account: str, g: Group, n_units: int) -> None:
    what = f"{unit}: its data-scientist group has one Sandbox seat"
    if not g.permission_set_found:
        checks.fail("VN-6", what, f"no permission set named {UNIT_PERMISSION_SET}")
        return
    if not g.complete:
        checks.fail("VN-6", what, "an Identity Center read failed (section 10)")
        return
    if not g.holders:
        checks.fail(
            "VN-6",
            what,
            f"nobody holds {UNIT_PERMISSION_SET} on the unit: its data scientists have no seat "
            "(step 3)",
        )
        return
    if len(g.holders) > 1 or g.holders[0][0] != "GROUP":
        checks.fail(
            "VN-6",
            what,
            f"{UNIT_PERMISSION_SET} on the unit is held by "
            + joined(f"{t.lower()} {n if n != '-' else i}" for t, i, n in g.holders)
            + ": one group per unit, and a set is assigned to a group, never to a user",
        )
        return
    name = g.holders[0][2]
    in_sandboxes = [s for s in g.seats if s.ou == SANDBOXES_OU]
    own = [
        s for s in in_sandboxes if s.account == account and s.permission_set == UNIT_PERMISSION_SET
    ]
    foreign = [s for s in in_sandboxes if s not in own]
    outside = [s for s in g.seats if s.ou != SANDBOXES_OU]

    def seat_text(seats: list) -> str:
        return joined(f"{s.permission_set} on {s.account_name} ({s.ou})" for s in seats)

    problems = []
    if foreign:
        problems.append(
            f"{name} also holds {seat_text(foreign)}: a group reaching a second unit's Sandbox is "
            "the isolation D35 exists for"
        )
    if name == SHARED_GROUP:
        if n_units > 1:
            problems.append(
                f"the shared {SHARED_GROUP} still holds the unit's seat with {n_units} units "
                "declared: the seat moves to sso-group-data-scientists-<bu> at the second unit "
                "(docs/ORGANIZATION.md, Assignments)"
            )
        elsewhere = [s for s in outside if s.ou != WORKLOADS_OU]
        if elsewhere:
            problems.append(
                f"{name} holds {seat_text(elsewhere)}, outside {SANDBOXES_OU} and {WORKLOADS_OU}"
            )
        boundary = [s for s in outside if s.ou == WORKLOADS_OU]
        if boundary:
            checks.note(
                "VN-6",
                f"{unit}: the shared group's seats past the graduation boundary",
                f"{seat_text(boundary)}: the shared group keeps them by design, and a vended "
                "unit's own group holds its Sandbox seat alone (docs/ORGANIZATION.md, the dagger "
                "under Assignments)",
            )
    else:
        if outside:
            problems.append(
                f"{name} also holds {seat_text(outside)}: a unit's group holds its Sandbox seat "
                "alone (step 3)"
            )
        if not name.startswith(UNIT_GROUP_PREFIX):
            checks.note(
                "VN-6",
                what,
                f"{name} is not named {UNIT_GROUP_PREFIX}<bu> (docs/ORGANIZATION.md, SSO Groups)",
            )
    if not own:
        problems.append(f"{name}'s own assignments do not list {UNIT_PERMISSION_SET} on the unit")
    if problems:
        checks.fail("VN-6", what, "; ".join(problems))
    elif name == SHARED_GROUP:
        checks.ok(
            "VN-6",
            what,
            f"{UNIT_PERMISSION_SET} on {own[0].account_name}, its one seat in {SANDBOXES_OU}, held "
            f"by the shared {SHARED_GROUP}, the unit's principal while one unit is declared",
        )
    else:
        checks.ok(
            "VN-6",
            what,
            f"{name}: exactly one assignment, {UNIT_PERMISSION_SET} on {own[0].account_name}",
        )


# ------------------------------------------------------------------------------- the run


@dataclass
class Unit:
    """Everything read for one unit."""

    name: str
    declared: list
    profile: str
    reader: Reader | None = None
    block: str | None = None
    placement: Placement | None = None
    vpcs: list | None = None
    vpc: Vpc | None = None
    own_routes: VpcRoutes | None = None
    connections: list | None = None
    peerings: list = field(default_factory=list)  # [Peering]
    zones: Zones | None = None
    group: Group | None = None


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    if ctx.standalone:
        note("vending.py reads scripts/tfhygiene/backend.py and needs the repository around it")
        return 1
    b, why = read_backend(ctx.repo_root)
    if b is None:
        note(f"cannot read the unit tables: {why}")
        return 1
    declared = declared_units(b)
    named = [a for a in argv if not a.startswith("-")]
    every_unit = not named
    names = named or sorted(declared)
    unknown = [n for n in names if n not in b.profiles]
    if unknown:
        note(f"no PROFILES row for {', '.join(unknown)} in {'/'.join(BACKEND_FILE)}")
        return 1
    if not names:
        note("backend.py declares no unit")
        return 1

    hub_account = b.hub[0]
    wanted = [b.profiles[IDENTITY_FOLDER]]
    for unit in names:
        wanted.append(b.profiles[unit])
        wanted += [b.profiles[a] for a, _s, _r in b.peer_rows(unit) if a in b.profiles]
    wanted.append(b.profiles[hub_account])
    selected = list(dict.fromkeys(wanted))

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    readers = {c.profile: Reader(c, errors) for c in callers}
    by_account = {r.account: r for r in readers.values() if r.live}
    idn = readers[b.profiles[IDENTITY_FOLDER]]
    hub = readers[b.profiles[hub_account]]
    hub_env = b.env_tokens.get(hub_account, hub_account)
    checks = Checks()

    # ----------------------------------------------------------------- the reads
    note("reading the organization and the hub ...")
    tree = read_tree(idn)
    directory = Directory(idn)
    peer_vpcs: dict = {hub_account: read_vpcs(hub)}  # account folder -> [Vpc] | None
    hub_vpc = vpc_by_block(peer_vpcs[hub_account], b.vpc_cidrs.get(b.hub, "-"))
    units = []
    for unit in names:
        note(f"measuring {unit} ...")
        u = Unit(unit, declared.get(unit, ["named on the command line"]), b.profiles[unit])
        u.reader = readers[u.profile]
        u.block = b.vpc_cidrs.get((unit, UNIT_SLICE))
        if u.reader.live:
            u.placement = read_placement(idn, u.reader.account, tree.types)
            u.group = read_group(directory, u.reader.account)
        u.vpcs = read_vpcs(u.reader)
        u.vpc = vpc_by_block(u.vpcs, u.block) if u.block else None
        if u.vpc:
            u.own_routes = read_routes(u.reader, u.vpc.vpc_id, want_subnets=True)
            u.connections = read_connections(u.reader)
        for peer_account, peer_slice, role in b.peer_rows(unit):
            peer_block = b.vpc_cidrs.get((peer_account, peer_slice), "-")
            p = Peering((peer_account, peer_slice), role, peer_block)
            peer_reader = readers.get(b.profiles.get(peer_account, ""))
            if peer_reader is not None and peer_account not in peer_vpcs:
                peer_vpcs[peer_account] = read_vpcs(peer_reader)
            p.peer_read = peer_vpcs.get(peer_account) is not None
            p.peer_vpc = vpc_by_block(peer_vpcs.get(peer_account), peer_block)
            if u.vpc and p.peer_vpc and u.connections is not None:
                p.connections = [
                    c for c in u.connections if c.joins(u.vpc.vpc_id, p.peer_vpc.vpc_id)
                ]
                active = p.active
                if active and u.own_routes:
                    p.unit_routes = [r for r in u.own_routes.routes if r.target == active.pcx]
                if active:
                    far = read_routes(peer_reader, p.peer_vpc.vpc_id, want_subnets=False)
                    p.peer_complete = far.complete
                    p.peer_routes = [r for r in far.routes if r.target == active.pcx]
            u.peerings.append(p)
        if u.vpc:
            u.zones = read_zones(
                u.reader,
                hub,
                by_account,
                CHILD_ZONE.format(env=b.env_tokens.get(unit, unit)),
                u.vpc.vpc_id,
                hub_vpc.vpc_id if hub_vpc else None,
            )
        units.append(u)
    note("reading the proxy ...")
    proxy = read_proxy(hub, hub_env)

    # ----------------------------------------------------------------- the checks
    units_judged = {u.name: u.reader.account for u in units if u.reader and u.reader.live}
    judge_tree(checks, tree, units_judged, every_unit)
    for u in units:
        if not u.reader.live:
            for check_id in ("VN-1", "VN-2", "VN-3", "VN-4", "VN-6"):
                checks.fail(check_id, u.name, f"{u.profile} did not authenticate (section 1)")
            continue
        judge_placement(checks, u.name, tree, u.placement)
        judge_allocation(checks, b, u.name, u.vpcs)
        if u.vpc is None:
            checks.fail("VN-3", u.name, "not judged: the unit's VPC was not found (VN-2)")
            checks.fail("VN-4", u.name, "not judged: the unit's VPC was not found (VN-2)")
        else:
            judge_peer_shape(checks, b, u.name, u.peerings, u.connections, u.vpc)
            for p in u.peerings:
                label = "/".join(p.peer) + (" (the hub)" if p.peer == b.hub else "")
                judge_peering(checks, u.name, u.block, u.own_routes, p, label)
            judge_zones(
                checks,
                u.name,
                u.reader.account,
                CHILD_ZONE.format(env=b.env_tokens.get(u.name, u.name)),
                u.zones,
                u.vpc,
                hub_vpc,
            )
        if u.block:
            judge_proxy(checks, u.name, u.block, proxy, hub_env)
        else:
            checks.fail("VN-5", u.name, "not judged: the unit has no allocation (VN-2)")
        judge_group(checks, u.name, u.reader.account, u.group or Group(False), len(declared))

    # ----------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)
        write_report(rep, b, callers, declared, units, tree, proxy, hub_env, every_unit)
        rep.h1("9. CHECKS")
        rep.checks_table(checks)
        rep.line()
        rep.line(f"{checks.n_fail()} check(s) FAILED.")
        rep.text("""
What the checks are, and where each comes from:
  VN-1  the account is ACTIVE in Interactive/Sandboxes, and neither it nor the OU carries a
        policy of its own (D37, INV-11); every active account in Sandboxes is a declared unit
  VN-2  the CIDR is the unit's VPC_CIDRS row, inside SANDBOX_SUPERNET, overlapping no other
        row, and the unit's VPC carries it under the Name the hub resolves (NT-5, per unit)
  VN-3  each PEERINGS row is an active connection routed on both sides; no other peering;
        the hand-built unit's peer slices (NT-11, per unit)
  VN-4  the child zone in the unit's VPC and the hub's and no other, both authorizations
        kept, the unit's VPC resolving the apex and its child only (INT-22, NT-12 per unit)
  VN-5  the proxy's security group and its allow-list plane admit the unit's range (PX-1,
        PX-3, per unit)
  VN-6  the group holding DataScientistAccess on the unit holds no other Sandbox seat, and a
        unit's own group nothing else; the shared group is unit 1's while one unit is declared""")
        rep.h1("10. Calls that failed")
        failed_calls_epilogue(rep, errors)
        rep.line()
        rep.line("Regenerate with:  ./aws/vending.py")

    # ----------------------------------------------------------------- the exit
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 10)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 9)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


def write_report(
    rep: Report,
    b: Backend,
    callers: list,
    declared: dict,
    units: list,
    tree: OrgTree,
    proxy: Proxy,
    hub_env: str,
    every_unit: bool,
) -> None:
    """Sections 1 to 8: the readings each check is judged on."""
    rep.banner("Vending - a business unit's Sandbox, read from every place a vend writes")
    rep.text(f"""generated : {context.utc_stamp()}
units     : {", ".join(u.name for u in units)}{"" if every_unit else "   (named on the command line)"}
region    : {context.REGION}
produced  : aws/vending.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom; the units and where each is declared
  2. The unit in the organization - VN-1
  3. The address allocation - VN-2
  4. The peerings and their routes - VN-3
  5. The child zone, the apex and their authorizations - VN-4
  6. The proxy's source block - VN-5
  7. The unit's data-scientist group - VN-6
  8. What nothing here measures
  9. CHECKS
  10. Calls that failed

HOW TO READ THIS FILE
  - A UNIT IS AN ACCOUNT FOLDER of scripts/tfhygiene/backend.py. Every expectation is
    generated from that file's tables (VPC_CIDRS, PEERINGS, VPN_HOST_SLICE, PROFILES,
    ENV_TOKENS), so a vend adds rows there and nothing here changes.
  - THE HAND-BUILT UNIT IS THE REFERENCE ({REFERENCE_UNIT}): a vended unit names the
    same peer slices.
  - VN-6 READS THE SHARED GROUP AS UNIT 1's while one unit is declared: its seats past
    the graduation boundary are a note; at the second unit the shared group holding a
    unit's seat is a failure.
  - EVERY VERDICT IS A CONFIGURATION READING, and every object read is [P]: a run with
    the environment down is complete, and a packet's arrival is a probe's question.

THIS FILE IS NOT VERSIONED (aws/output/ is in .gitignore) AND CONTAINS ACCOUNT IDS.
Do not copy one into a tracked file.""")

    # ==================================================================================
    rep.h1("1. Which accounts were measured, and as whom; the units and where each is declared")
    rep.text("""Every awsds-infra-* profile resolves to the infrastructure user through
InfrastructureAccess. A `(failed)` row is a profile that did not authenticate, never a
compliant one.

""")
    rep.tabulate(
        ["PROFILE\tACCOUNT\tCALLER ARN"]
        + [f"{c.profile}\t{c.account or '-'}\t{c.arn or '(failed)'}" for c in callers]
    )
    rep.line()
    rep.tabulate(
        ["UNIT\tPROFILE\tVPC_CIDRS\tDECLARED BY"]
        + [
            f"{u.name}\t{u.profile}\t{u.block or '(no row)'}\t{'; '.join(u.declared)}"
            for u in units
        ]
    )
    rep.line()
    rep.line(f"units declared in backend.py: {', '.join(sorted(declared)) or 'none'}")
    rep.line(f"the hub (VPN_HOST_SLICE): {'/'.join(b.hub)}  {b.vpc_cidrs.get(b.hub, '-')}")
    rep.line(f"SANDBOX_SUPERNET={b.supernet}")

    # ==================================================================================
    rep.h1("2. The unit in the organization - VN-1")
    rep.text(f"""$ aws --profile awsds-infra-identity organizations list-roots
$ aws --profile awsds-infra-identity organizations list-organizational-units-for-parent \\
      --parent-id <root, then Interactive>
$ aws --profile awsds-infra-identity organizations list-accounts-for-parent --parent-id <Sandboxes>
$ aws --profile awsds-infra-identity organizations describe-account --account-id <unit>
$ aws --profile awsds-infra-identity organizations list-parents --child-id <unit>
$ aws --profile awsds-infra-identity organizations list-policies-for-target \\
      --target-id <unit, then Sandboxes> --filter <each type ENABLED on the root>

The AWS-managed document a type attaches to every node is not a policy of the node's
own: {", ".join(f"{t} {d}" for t, d in DEFAULT_DOCUMENTS.items())}.

""")
    rep.line(f"policy types ENABLED on the root: {joined(tree.types)}")
    rep.line(f"SANDBOXES={tree.sandboxes or '(not found)'}   path {tree.sandboxes_path}")
    rep.h2(f"what {SANDBOXES_OU} carries")
    rep.tabulate(attachment_rows(tree.ou_attachments))
    rep.h2(f"the accounts in {SANDBOXES_OU}")
    census = tree.census
    if census is None:
        census = [("-", "(unread)", "-")]
    rep.tabulate(
        ["ACCOUNT\tNAME\tSTATE"]
        + [f"{i}\t{n}\t{s}" for i, n, s in census or [("-", "(no account)", "-")]]
    )
    for u in units:
        p = u.placement
        rep.h2(f"{u.name}")
        if p is None:
            rep.line("(not read - the unit's profile did not authenticate)")
            continue
        rep.line(f"ACCOUNT={u.reader.account}   {p.name}   {p.state}")
        rep.line(f"parent: {p.parent_name} ({p.parent})")
        rep.line()
        rep.tabulate(attachment_rows(p.attachments))

    # ==================================================================================
    rep.h1("3. The address allocation - VN-2")
    rep.text("""$ aws --profile <unit> ec2 describe-vpcs

The authored table is backend.py's VPC_CIDRS; the unit's row is (<unit>, foundation).

""")
    rep.tabulate(
        ["ACCOUNT FOLDER\tSLICE\tCIDR\tIN THE SUPERNET"]
        + [
            f"{a}\t{s}\t{c}\t{'yes' if inside(c, b.supernet) else 'no'}"
            for (a, s), c in sorted(b.vpc_cidrs.items())
        ]
    )
    for u in units:
        rep.h2(f"{u.name} - the VPCs in its account")
        if u.vpcs is None:
            rep.line("(not read - section 10)")
            continue
        rep.tabulate(
            ["VPC\tPRIMARY\tASSOCIATED BLOCKS\tNAME\tDEFAULT"]
            + [
                f"{v.vpc_id}\t{v.primary}\t{','.join(v.blocks)}\t{v.name}\t{v.is_default}"
                for v in u.vpcs
            ]
            or ["VPC\tPRIMARY\tASSOCIATED BLOCKS\tNAME\tDEFAULT", "(none)\t-\t-\t-\t-"]
        )
        if u.vpc:
            rep.line()
            rep.line(f"VPC={u.vpc.vpc_id}   expected Name {b.vpc_name(u.name, UNIT_SLICE)}")

    # ==================================================================================
    rep.h1("4. The peerings and their routes - VN-3")
    rep.text("""$ aws --profile <unit> ec2 describe-vpc-peering-connections
$ aws --profile <unit> ec2 describe-route-tables --filters Name=vpc-id,Values=<unit VPC>
$ aws --profile <unit> ec2 describe-subnets --filters Name=vpc-id,Values=<unit VPC>
$ aws --profile <peer> ec2 describe-vpcs
$ aws --profile <peer> ec2 describe-route-tables --filters Name=vpc-id,Values=<peer VPC>

A peer VPC is found by its VPC_CIDRS range. The unit's private tier is its subnets tagged
Tier=private, and their tables (the main table for a subnet with none of its own); a
return route covers a private subnet when its destination contains the subnet's block.

""")
    for u in units:
        rep.h2(u.name)
        if u.vpc is None:
            rep.line("(the unit's VPC was not found - VN-2)")
            continue
        own = u.own_routes
        if own:
            rep.line(f"private tables : {joined(own.private_tables)}")
            rep.line(f"private subnets: {joined(f'{s} {c}' for s, c in own.private_subnets)}")
            rep.line()
        rep.tabulate(
            ["PEERING ROW\tROLE\tPEER RANGE\tPEER VPC\tCONNECTION\tSTATUS"]
            + [
                f"{'/'.join(p.peer)}\t{p.role}\t{p.peer_block}\t"
                f"{p.peer_vpc.vpc_id if p.peer_vpc else '-'}\t"
                f"{joined((c.pcx for c in p.connections), '-')}\t"
                f"{joined((c.status for c in p.connections), '-')}"
                for p in u.peerings
            ]
            or [
                "PEERING ROW\tROLE\tPEER RANGE\tPEER VPC\tCONNECTION\tSTATUS",
                "(none)\t-\t-\t-\t-\t-",
            ]
        )
        for p in u.peerings:
            c = p.active
            if c is None:
                continue
            rep.line()
            rep.line(f"PCX={c.pcx}   {'/'.join(p.peer)}")
            rep.tabulate(
                ["SIDE\tTABLE\tDESTINATION\tSTATE"]
                + [f"unit\t{r.table}\t{r.destination}\t{r.state}" for r in p.unit_routes]
                + [f"peer\t{r.table}\t{r.destination}\t{r.state}" for r in p.peer_routes],
                indent="  ",
            )
        others = [
            c
            for c in u.connections or []
            if u.vpc.vpc_id in (c.requester, c.accepter)
            and not any(c in p.connections for p in u.peerings)
        ]
        if others:
            rep.line()
            rep.line("connections no PEERINGS row names:")
            rep.tabulate(
                [f"{c.pcx}\t{c.status}\t{c.requester_block} -> {c.accepter_block}" for c in others],
                indent="  ",
            )

    # ==================================================================================
    rep.h1("5. The child zone, the apex and their authorizations - VN-4")
    rep.text(f"""$ aws --profile <unit> route53 list-hosted-zones
$ aws --profile <unit> route53 get-hosted-zone --id <child zone>
$ aws --profile <unit> route53 list-vpc-association-authorizations --hosted-zone-id <child zone>
$ aws --profile <unit> route53 list-hosted-zones-by-vpc --vpc-id <unit VPC> --vpc-region {context.REGION}
$ aws --profile <hub> route53 list-hosted-zones-by-vpc --vpc-id <hub VPC> --vpc-region {context.REGION}
$ aws --profile <apex owner> route53 list-vpc-association-authorizations --hosted-zone-id <apex>

The child zone is {CHILD_ZONE} with the unit's env token. Its expected associations
are the unit's VPC and the hub's; the unit's VPC resolves {APEX_ZONE} and its child.

""")
    for u in units:
        z = u.zones
        rep.h2(u.name)
        if z is None:
            rep.line("(not read - the unit's VPC was not found)")
            continue
        rep.line(f"ZONE={joined(z.child_ids, '(none)')}")
        rep.line(f"  associated VPCs : {joined(z.child_vpcs)}")
        rep.line(f"  authorized VPCs : {joined(z.child_authorized)}")
        rep.line(f"APEX={z.apex_id}")
        rep.line(
            "  authorized VPCs : "
            + (
                "(the apex owner holds no profile here)"
                if z.apex_authorized is None
                else joined(z.apex_authorized)
            )
        )
        rep.line()
        rep.tabulate(
            ["RESOLVED BY\tZONE\tNAME\tOWNER"]
            + [f"the unit's VPC\t{i}\t{n}\t{o}" for i, n, o in z.resolved]
            + [f"the hub's VPC\t{i}\t{n}\t{o}" for i, n, o in z.hub_view]
        )

    # ==================================================================================
    rep.h1("6. The proxy's source block - VN-5")
    rep.text(f"""$ aws --profile <hub> ssm get-parameter --name {PROXY_PARAMETER.format(env=hub_env)}
$ aws --profile <hub> ec2 describe-security-groups \\
      --filters Name=group-name,Values={PROXY_GROUP.format(env=hub_env)}

production/networking generates one plane per PEERINGS row that ends in the hub, keyed
<account>-<slice>. The parameter is the first link of PX-3's chain; whether the host
serves it is ./aws/proxy.py --on-host.

""")
    rep.tabulate(
        ["PLANE\tSOURCES\tMODE\tALLOW\tDENY"]
        + [
            f"{k}\t{','.join(v.get('sources') or []) or '-'}\t{v.get('mode', '-')}\t"
            f"{len(v.get('allow') or [])}\t{len(v.get('deny') or [])}"
            for k, v in sorted(proxy.planes.items())
        ]
        or ["PLANE\tSOURCES\tMODE\tALLOW\tDENY", "(not read)\t-\t-\t-\t-"]
    )
    rep.line()
    rep.tabulate(
        [f"GROUP\tTCP/{PROXY_PORT} FROM"] + [f"{g}\t{c}" for g, c in proxy.rules]
        or [f"GROUP\tTCP/{PROXY_PORT} FROM", "(none read)\t-"]
    )

    # ==================================================================================
    rep.h1("7. The unit's data-scientist group - VN-6")
    rep.text(f"""$ aws --profile awsds-infra-identity sso-admin list-account-assignments \\
      --instance-arn <instance> --account-id <unit> --permission-set-arn <{UNIT_PERMISSION_SET}>
$ aws --profile awsds-infra-identity identitystore describe-group --identity-store-id <store> \\
      --group-id <the holder>
$ aws --profile awsds-infra-identity sso-admin list-account-assignments-for-principal \\
      --instance-arn <instance> --principal-id <the holder> --principal-type GROUP

The holder's seats are classified by the OU of each account: {SANDBOXES_OU} is a unit's,
{WORKLOADS_OU} is past the graduation boundary. ListAccountAssignmentsForPrincipal is
documented as a Management call and answered from the delegated administrator (measured
2026-10-18).

""")
    for u in units:
        g = u.group
        rep.h2(u.name)
        if g is None:
            rep.line("(not read - the unit's profile did not authenticate)")
            continue
        rep.tabulate(
            [f"HOLDS {UNIT_PERMISSION_SET} ON THE UNIT\tTYPE\tID"]
            + [f"{n}\t{t}\t{i}" for t, i, n in g.holders]
            or [f"HOLDS {UNIT_PERMISSION_SET} ON THE UNIT\tTYPE\tID", "(nobody)\t-\t-"]
        )
        if g.seats:
            rep.line()
            rep.tabulate(
                ["SEAT\tACCOUNT\tNAME\tOU"]
                + [f"{s.permission_set}\t{s.account}\t{s.account_name}\t{s.ou}" for s in g.seats]
            )

    # ==================================================================================
    rep.h1("8. What nothing here measures")
    rep.text("""Read this BEFORE reading section 9 as a pass.

  - Control Tower's view: the controls enabled on Sandboxes and the account's enrollment
    answer only from Management (INV-12). A preventive control shows here as the
    aws-guardrails-* SCP it attaches; a detective or proactive control attaches none.
  - The vend's other obligations, each read by its own instrument: account-level S3
    Block Public Access (step 3b, ./aws/account-bpa.py), the domain association and the
    blueprint configurations (step 4, ./aws/studio.py), the lake's settings, share and
    links (step 5, ./aws/datalake.py), the Bedrock gates (step 1, ./aws/bedrock.py and
    ./aws/bedrock-scope.py), and the [E] endpoints while egress/ is up (./aws/egress.py).
  - The internal CA root in the unit's image (INT-19, step 1's second PKI item): no
    describe call reads an image's trust store.
  - The running squid.conf (PX-3, ./aws/proxy.py --on-host) and the committed planes
    (DN-3, ./aws/dns-allowlist.py --from-api).
  - Whether a packet arrives. Every check reads configuration (Lesson 20).""")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
