#!/usr/bin/env -S uv run --quiet
# scp-battery.py - run the SCP probe battery of docs/plan/runbooks/scp-battery.md.
#
#   run:      ./aws/probes/scp-battery.py              # every phase
#             ./aws/probes/scp-battery.py --phase ou   # one phase
#             ./aws/probes/scp-battery.py --list       # what would run, and where
#   probes:   aws/probes/probes.py - the data. Amending the battery means editing THAT file.
#   writes:   aws/output/scp-battery-<stamp>.txt (untracked), account ids masked.
#   exit:     0 when every probe met its expectation; 1 on a regression, an overreach or
#             a broken floor; 2 when the run could not be trusted (dead SSO session).
#
# WHAT THIS SCRIPT IS NOT ALLOWED TO DO, and the seam is deliberate: it never attaches,
# detaches, creates or updates a policy. The human attaches from the Management console;
# the script only measures what the attached ceiling does. A script that could both change
# the ceiling and report on it would be able to report on a ceiling it had just changed.
#
# WHETHER ANYTHING IS CREATED IS A DECLARED FIELD, NOT A JUDGEMENT. Every probe in probes.py
# carries a mandatory `safety` value and the driver refuses to run one that does not:
#   ro       read-only; changes nothing even if fully allowed
#   dryrun   carries --dry-run, which the driver verifies is actually there
#   blocked  mutating, but a prerequisite named in the command does not exist, so removing
#            the deny only moves the failure one step later
#   creates  would really do something if the deny lifted. SEVEN probes - three in the root
#            phase, four in `decl` - and the driver REFUSES to run them outside Policy Canary,
#            which is the one place this project accepts the residual risk of an "allowed".
#
# THE THREE THINGS THIS ENCODES THAT A HAND-RUN BATTERY KEPT GETTING WRONG:
#   1. A dead SSO session makes every probe come back looking exactly like a deny. It
#      happened twice in one sitting. So the session is checked per account per phase, and
#      a non-answer ABORTS the run instead of being recorded (exit 2). But ONLY an expired
#      token aborts: credentials can also fail to vend because the ceiling denied the
#      sign-in, and that is the most serious finding this battery can make rather than a
#      reason to stop - so ensure_session reads the wording too (Lesson 24).
#   2. The outcome is read from the error WORDING, never from the exit code - and an
#      explicit-deny message names the policy id, which is the attribution.
#   3. "The service validates before authorizing" is a property of the ACTION, not of the
#      service (Lesson 21), so each probe declares the wording that proves authorization
#      was reached for that action. Anything else is UNTESTED - never silently "allowed".

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# probes.py and readback.py sit beside this script, which Python puts on sys.path.
import probes as probes_data
import readback

# The one recognizer for "a token vended, just not for this human". It lives in awslib
# because three callers now need it and the wording is the datum in all three.
from awslib.profiles import wrong_identity

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
POLICY_DIR = REPO / "terraform-live" / "identity" / "org-policies" / "policies"
OUT_DIR = REPO / "aws" / "output"
REGION_DEFAULT = "us-west-2"

# One place mapping a probe's account token to a CLI profile. A token that is not here is a
# typo in probes.py, and it stops the run rather than skipping a probe silently.
PROFILES = {
    "canary": "awsds-policy-canary",
    "data": "awsds-infra-data",
    "identity": "awsds-infra-identity",
    "dev": "awsds-infra-dev",
    "sandbox1": "awsds-infra-sandbox-1",
    "prod": "awsds-infra-prod",
}

# The one place that decides "this is an expired token, not an answer". Shared by
# ensure_session and classify on purpose: two copies of this regex would drift, and the
# direction they drift in is silent - a real deny read as a dead session, or the reverse.
EXPIRY_RE = re.compile(
    "SSO session associated with this profile has expired|ExpiredToken"
    "|InvalidGrantException|Error loading SSO Token|Unable to locate credentials"
    "|security token included in the request is (expired|invalid)"
)

ACCOUNT_ID_RE = re.compile(r"[0-9]{12}")


def bold(text: str) -> None:
    print(f"\033[1m{text}\033[0m")


def mask(text: str) -> str:
    return ACCOUNT_ID_RE.sub("<acct>", text)


def die(message: str, code: int = 1) -> None:
    print(f"\n!! {message}", file=sys.stderr)
    sys.exit(code)


def aws(argv: list) -> tuple[str, int]:
    """One CLI call, stdout+stderr merged - the wording is the datum, so nothing is
    separated or discarded."""
    proc = subprocess.run(["aws", *argv], capture_output=True, text=True)
    return (proc.stdout + proc.stderr).rstrip("\n"), proc.returncode


def assignment_exists(profile: str) -> bool | None:
    """Does Identity Center itself say the CACHED TOKEN is assigned this profile's role?

    WHY THIS EXISTS, AND WHY IT IS NOT A SHORTCUT - Lesson 24, arriving from the other
    side. `ForbiddenException ... GetRoleCredentials` has ONE wording and TWO causes:

      - the ceiling denied the sign-in flow itself. `awsds-org-rcp-perimeter` did this on
        2026-08-14 in all six member accounts - the most serious finding this battery can
        produce, and the reason ensure_session stopped treating that wording as expiry.
      - a valid token cached for a DIFFERENT human, who holds no such role. Measured
        2026-08-20: a browser silently re-approved a live portal session, `aws sso login`
        reported success, and every `awsds-infra-*` profile failed exactly like a breach.

    Suppressing the second BY ITS WORDING would suppress the first with it - which is the
    failure ensure_session's docstring is already about, run in reverse. So ask the system
    that answers a different question: IdC's own listing of what this token is assigned.
    That path never traverses STS, so no SCP and no RCP can shape its answer.

    True  - the assignment exists, so a refusal to vend is the ceiling. The finding stands.
    False - this token's user has no such role. Operator error, and nothing about the org.
    None  - could not tell, and the caller must KEEP the finding: hiding a real breach is
            the expensive direction; a spurious one costs an investigation.
    """

    def conf(key: str) -> str:
        out, rc = aws(["configure", "get", key, "--profile", profile])
        return out.strip() if rc == 0 else ""

    account_id, role, session = conf("sso_account_id"), conf("sso_role_name"), conf("sso_session")
    if not (account_id and role and session):
        return None
    # The cache file is named for the sso-session, never for the user - which is precisely
    # how the wrong human's token comes to occupy the right human's slot.
    digest = hashlib.sha1(session.encode(), usedforsecurity=False).hexdigest()
    cache = Path.home() / ".aws" / "sso" / "cache" / f"{digest}.json"
    try:
        token = json.loads(cache.read_text()).get("accessToken")
    except (OSError, ValueError):
        return None
    if not token:
        return None
    out, rc = aws(
        [
            "sso",
            "list-account-roles",
            "--account-id",
            account_id,
            "--access-token",
            token,
            "--region",
            REGION_DEFAULT,
            "--query",
            "roleList[].roleName",
            "--output",
            "text",
        ]
    )
    if rc != 0:
        return None
    return role in out.split()


class Battery:
    def __init__(self, phase_filter: str, do_readback: bool):
        self.phase_filter = phase_filter
        self.do_readback = do_readback
        self.results: list = []  # (mark, phase, account, expect, outcome, detail, label)
        self.checked: set = set()  # (phase, account) with a live session
        # Accounts whose credentials would not vend, per phase. Recorded once and then
        # remembered, so the breach is reported once and the probes behind it are marked
        # untested rather than retried.
        self.broken: set = set()
        self.n_ok = 0
        self.n_bad = 0
        self.n_untested = 0
        self.resolve_cache: dict = {}

    # ---------------------------------------------------------------- session
    def ensure_session(self, acct: str, phase: str) -> bool:
        """The session is checked once per account per phase - "immediately before each
        block of probes", which is what the runbook asks for and what the two mid-battery
        expiries taught.

        WHY THIS READS THE WORDING INSTEAD OF THE EXIT CODE (Lesson 24, 2026-08-14). There
        are two reasons credentials fail to vend, they are indistinguishable by exit code,
        and they need opposite handling:
          - the SSO token expired. Nothing can be measured, and continuing would record
            every probe as a deny. Stop the run.
          - the ceiling denied the sign-in itself. `awsds-org-rcp-perimeter` did exactly
            that on 2026-08-14: its STS statement named the actions Identity Center's SAML
            flow needs, so `GetRoleCredentials` returned `ForbiddenException ... No access`
            in all six member accounts. That is the single most serious finding the battery
            can produce - and the old code aborted with "dead SSO session" before recording
            it, so the six `rcp` floor probes written to catch it could never run. The
            defence against the first case swallowed the second.
        So: expiry stops the run, anything else is recorded as a floor breach and the run
        continues to the accounts that still answer. Returns False when the account is
        unusable, and the caller records the probes it could not run rather than dropping
        them.
        """
        key = (phase, acct)
        if key in self.checked:
            return True
        if key in self.broken:
            return False
        profile = PROFILES.get(acct)
        if profile is None:
            die(f"unknown account token '{acct}' in probes.py", 64)

        out, rc = aws(["sts", "get-caller-identity", "--profile", profile])
        if rc == 0:
            self.checked.add(key)
            return True

        if EXPIRY_RE.search(out):
            die(
                f"""no usable session for profile {profile}.
   Sign in as the infrastructure user and run the battery again:
       aws sso login --sso-session awsds
   Nothing was recorded for this phase - a dead session makes every probe read like a deny.""",
                2,
            )

        # The wording below is the ceiling's, but it is also the wrong human's. Ask IdC
        # which, and stop ONLY when IdC says the role was never this token's to vend -
        # otherwise fall through and record the breach, including when it cannot answer.
        if wrong_identity(out) and assignment_exists(profile) is False:
            die(
                f"""a valid SSO token is cached, but for a user who does not hold
   {profile}'s role. Identity Center does not list that role for this token, so this is a
   sign-in as the wrong identity - NOT a ceiling finding, and nothing was recorded.
   Logging in again will not fix it: the browser re-approves the session it already has.
       aws sso logout && aws sso login --sso-session awsds""",
                2,
            )

        # Not the token. The credential path itself is refusing, which is a finding and not
        # a reason to stop: the other accounts still answer, and which ones do is the
        # diagnosis.
        m = re.search(r"\(([A-Za-z]+Exception)\)", out)
        why = m.group(1) if m else "no credentials"
        self.broken.add(key)
        self.record(
            phase, acct, "allow", f"floor: credentials vend at all in {acct}", "NO-CREDENTIALS", why
        )
        return False

    # ------------------------------------------------- real ids (Lesson 21)
    # Probes that must reach authorization need inputs that exist. Resolved once per
    # account+region and cached, because the alternative - an invented id - is rejected
    # before authorization and reports "untested" while reading like a pass.
    def resolve_ami(self, acct: str, region: str) -> str:
        key = ("ami", acct, region)
        if key not in self.resolve_cache:
            out, rc = aws(
                [
                    "ssm",
                    "get-parameter",
                    "--name",
                    "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
                    "--profile",
                    PROFILES[acct],
                    "--region",
                    region,
                    "--query",
                    "Parameter.Value",
                    "--output",
                    "text",
                ]
            )
            self.resolve_cache[key] = out if rc == 0 and out.startswith("ami-") else ""
        return self.resolve_cache[key]

    def resolve_subnet(self, acct: str, region: str) -> str:
        key = ("subnet", acct, region)
        if key not in self.resolve_cache:
            out, rc = aws(
                [
                    "ec2",
                    "describe-subnets",
                    "--profile",
                    PROFILES[acct],
                    "--region",
                    region,
                    "--query",
                    "Subnets[0].SubnetId",
                    "--output",
                    "text",
                ]
            )
            self.resolve_cache[key] = out if rc == 0 and out.startswith("subnet-") else ""
        return self.resolve_cache[key]

    def resolve_account_id(self, acct: str) -> str:
        key = ("acctid", acct)
        if key not in self.resolve_cache:
            out, rc = aws(
                [
                    "sts",
                    "get-caller-identity",
                    "--profile",
                    PROFILES[acct],
                    "--query",
                    "Account",
                    "--output",
                    "text",
                ]
            )
            self.resolve_cache[key] = out if rc == 0 else ""
        return self.resolve_cache[key]

    # ---------------------------------------------------------------- classify
    def classify(self, out: str, allowed_re: str, rc: int) -> tuple[str, str]:
        """Reads the WORDING. The order matters: a dead session and an IAM-level deny both
        contain "AccessDenied", and only the SCP wording names a policy."""
        if EXPIRY_RE.search(out):
            return "NOANSWER", ""
        if "explicit deny in a service control policy" in out:
            m = re.search(r"p-[a-z0-9]{8,}", out)
            return "DENY-SCP", m.group(0) if m else ""
        if "explicit deny in a resource control policy" in out:
            m = re.search(r"p-[a-z0-9]{8,}", out)
            return "DENY-RCP", m.group(0) if m else ""
        # A DECLARATIVE policy is enforced in the SERVICE's control plane, not in
        # authorization (AWS Organizations user guide, "How declarative policies work"). So
        # it names no policy id and produces no "explicit deny" wording: the attribution is
        # the EXCEPTION MESSAGE, which is why this project sets a custom one. Matching our
        # own marker first is what distinguishes "the policy fired and delivered our
        # message" from "the policy fired with AWS's default" - and the second is a
        # finding, because the custom message is half the point of the document.
        # ...with one correction, measured 2026-08-14: the custom message is ALSO echoed
        # back by a SUCCESSFUL read of a setting the policy manages.
        # `ec2 get-instance-metadata-defaults` returns rc=0 with "ManagedBy":
        # "declarative-policy" and "ManagedExceptionMessage": <our text>, so matching the
        # marker alone classified the two decl FLOOR probes - the ones whose whole job is
        # to prove the read still works - as denials. Enforcement arrives as an API error;
        # an echo arrives as a result, and the exit code is the only thing separating them.
        if rc != 0 and "organization EC2 declarative policy" in out:
            return "DENY-DECL", "custom-message"
        if rc != 0 and re.search("denied due to an organizational policy|declarative policy", out):
            return "DENY-DECL", "AWS-default-msg"
        if "DryRunOperation" in out:
            return "ALLOWED", "dry-run"
        if allowed_re and re.search(allowed_re, out):
            return "ALLOWED", "reached-authorization"
        if rc == 0:
            return "ALLOWED", "succeeded"
        # An AccessDenied that names no policy is an IAM/permission-set deny, not the
        # ceiling - worth separating, because it answers a different question from the one
        # being asked.
        if re.search("AccessDenied|UnauthorizedOperation|not authorized", out):
            return "DENY-NOT-SCP", ""
        return "UNTESTED", ""

    @staticmethod
    def verdict(expect: str, outcome: str) -> str:
        return {
            ("deny", "DENY-SCP"): "OK",
            ("deny", "DENY-RCP"): "OK",
            ("deny", "DENY-DECL"): "OK",
            ("deny", "ALLOWED"): "BAD",
            ("deny", "DENY-NOT-SCP"): "NOTE",
            ("deny", "UNTESTED"): "NOTE",
            ("allow", "ALLOWED"): "OK",
            ("allow", "DENY-SCP"): "BAD",
            ("allow", "DENY-RCP"): "BAD",
            ("allow", "DENY-DECL"): "BAD",
            ("allow", "DENY-NOT-SCP"): "BAD",
            ("allow", "UNTESTED"): "NOTE",
            # Credentials that do not vend at all. Against an `allow` expectation this is
            # the floor itself giving way - the most serious row the battery can print -
            # and it is BAD even though nothing was measured, because what failed is the
            # measurement's precondition.
            ("allow", "NO-CREDENTIALS"): "BAD",
        }.get((expect, outcome), "NOTE")

    def record(
        self, phase: str, acct: str, expect: str, label: str, outcome: str, detail: str
    ) -> None:
        v = self.verdict(expect, outcome)
        if v == "OK":
            self.n_ok += 1
            mark = "ok  "
        elif v == "BAD":
            self.n_bad += 1
            mark = "FAIL"
        else:
            self.n_untested += 1
            mark = "note"
        self.results.append((mark, phase, acct, expect, outcome, detail, label))
        print(f"  {mark:<4} {phase:<8} {acct:<9} {expect:<6} {outcome:<13} {detail:<22} {label}")

    # ---------------------------------------------------------------- the probe
    def run_probe(self, p: dict) -> None:
        phase, acct = p["phase"], p["account"]
        expect, allowed = p["expect"], p["allowed"] or ""
        safety, label, argv = p["safety"], p["label"], p["argv"]

        if self.phase_filter and self.phase_filter != phase:
            return

        # The safety field is mandatory and is checked before the probe runs, so "does this
        # create anything?" is answered by the file rather than by whoever last read it.
        if safety == "creates":
            if acct != "canary":
                die(
                    f"""probes.py asks to run a 'creates' probe ('{label}') in '{acct}'.
   A probe that would really do something if the deny lifted may run in Policy Canary and
   nowhere else. Give it a --dry-run form, aim it at a prerequisite that does not exist
   ('blocked'), or move it to the canary.""",
                    64,
                )
        elif safety not in ("ro", "dryrun", "blocked"):
            die(
                f"""probe '{label}' declares safety '{safety}', which is not one of
   ro | dryrun | blocked | creates. Every probe must say what it would do if the ceiling
   were removed - that classification is the file's answer to 'does this create anything',
   and a probe that does not carry it does not run.""",
                64,
            )

        # A probe claiming `dryrun` had better carry the flag; the claim is what the reader
        # trusts.
        if safety == "dryrun" and "--dry-run" not in argv:
            die(f"probe '{label}' is declared 'dryrun' but passes no --dry-run flag.", 64)

        # An account that cannot vend credentials has already been recorded as a floor
        # breach. Its probes are marked untested rather than skipped: a probe that vanishes
        # from the count reads as one that passed, and the whole point of this run is that
        # the totals mean something.
        if not self.ensure_session(acct, phase):
            self.record(phase, acct, expect, label, "UNTESTED", f"no credentials in {acct}")
            return
        profile = PROFILES[acct]

        # Substitute the placeholders that need a real, existing id.
        resolved = []
        for arg in argv:
            if "@AMI@" in arg or "@SUBNET@" in arg or "@ACCT@" in arg:
                region = REGION_DEFAULT
                if "--region" in argv:
                    # the LAST --region wins, matching the shell's grep -A1 | tail -1
                    idxs = [i for i, a in enumerate(argv) if a == "--region"]
                    region = argv[idxs[-1] + 1]
                # An id that could not be resolved must stop the probe, not be substituted
                # as an empty string: the call would then fail on a malformed argument and
                # be classified UNTESTED with no hint of why. Resolution itself can be
                # *denied* - a region control denies the ssm:GetParameter that finds the
                # AMI - and that is worth saying out loud.
                if "@AMI@" in arg:
                    ami = self.resolve_ami(acct, region)
                    if not ami:
                        self.record(
                            phase, acct, expect, label, "UNTESTED", f"no AMI resolvable in {region}"
                        )
                        return
                    arg = arg.replace("@AMI@", ami)
                if "@SUBNET@" in arg:
                    sub = self.resolve_subnet(acct, region)
                    if not sub:
                        self.record(
                            phase, acct, expect, label, "UNTESTED", f"no subnet in {region}"
                        )
                        return
                    arg = arg.replace("@SUBNET@", sub)
                if "@ACCT@" in arg:
                    arg = arg.replace("@ACCT@", self.resolve_account_id(acct))
            resolved.append(arg)

        out, rc = aws(resolved + ["--profile", profile])
        outcome, detail = self.classify(out, allowed, rc)

        if outcome == "NOANSWER":
            die(
                f"""probe '{label}' in {acct} returned a non-answer:
   {mask(chr(10).join(out.splitlines()[:2]))}
   The run is stopped rather than recorded. Re-authenticate and start again.""",
                2,
            )

        self.record(phase, acct, expect, label, outcome, detail)

    # ------------------------------------------------------- deployed vs repository
    def run_readback(self) -> None:
        """Answers "is the thing being probed the thing in policies/?" before a single
        probe runs. Every amendment this project has made was uploaded by hand, and a
        battery run against the previous content looks exactly like a battery run against
        the current one."""
        bold("Read-back: what is attached, against terraform-live/.../policies/")
        # If Identity cannot vend credentials the read-back cannot run - but that is itself
        # the finding, and the probes below still discriminate *which* accounts are locked
        # out. Say plainly that what follows is measured against unverified policy content,
        # and continue.
        if not self.ensure_session("identity", "readback"):
            print(
                "  SKIPPED - no credentials in Identity, so the deployed policies were never read."
            )
            print("  Every probe below is measured against policy content this run did not verify.")
            print()
            return
        readback.run(str(POLICY_DIR), PROFILES["identity"])
        print()


def main(argv: list) -> int:
    phase_filter = ""
    list_only = False
    do_readback = True

    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--phase":
            phase_filter = args.pop(0) if args else ""
        elif a == "--list":
            list_only = True
        elif a == "--no-readback":
            do_readback = False
        elif a in ("-h", "--help"):
            # The header comment is the manual, exactly as the shell printed it.
            header = Path(__file__).read_text(encoding="utf-8").splitlines()[1:39]
            print(
                "\n".join(
                    line[2:] if line.startswith("# ") else line.lstrip("#") for line in header
                )
            )
            return 0
        else:
            print(f"unknown argument: {a}", file=sys.stderr)
            return 64

    battery = Battery(phase_filter, do_readback)

    if list_only:
        bold(
            "Probes defined in probes/probes.py"
            + (f" (phase {phase_filter})" if phase_filter else "")
        )
        print(f"  {'PHASE':<8} {'ACCOUNT':<9} {'EXPECT':<6} PROBE")
        for p in probes_data.PROBES:
            if phase_filter and p["phase"] != phase_filter:
                continue
            print(f"  {p['phase']:<8} {p['account']:<9} {p['expect']:<6} {p['label']}")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    report = OUT_DIR / f"scp-battery-{stamp}.txt"

    bold(
        f"SCP battery - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        + (f"  (phase {phase_filter})" if phase_filter else "")
    )
    print("Runbook: docs/plan/runbooks/scp-battery.md   Nothing here creates anything.")
    print()

    if do_readback and not phase_filter:
        battery.run_readback()

    print(
        f"  {'MARK':<4} {'PHASE':<8} {'ACCOUNT':<9} {'EXPECT':<6} {'OUTCOME':<13} "
        f"{'DETAIL':<22} PROBE"
    )
    for p in probes_data.PROBES:
        battery.run_probe(p)

    print()
    bold(
        f"{battery.n_ok} as expected, {battery.n_bad} unexpected, {battery.n_untested} not measured"
    )

    lines = [
        f"SCP battery - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "mark\tphase\taccount\texpect\toutcome\tdetail\tprobe",
    ]
    lines += ["\t".join(r) for r in battery.results]
    lines += [
        "",
        f"{battery.n_ok} as expected, {battery.n_bad} unexpected, "
        f"{battery.n_untested} not measured",
    ]
    report.write_text(mask("\n".join(lines)) + "\n", encoding="utf-8")
    print(f"Report: {report.relative_to(REPO)}")

    if battery.n_bad > 0:
        print()
        print("A 'FAIL' row is one of three things, and they are not the same:")
        print(
            "  expect=deny,  outcome=ALLOWED        -> the ceiling has a hole. "
            "Read the row's probe."
        )
        print(
            "  expect=allow, outcome=DENY-*         -> the ceiling reaches something it should not."
        )
        print(
            "  expect=allow, outcome=NO-CREDENTIALS -> the account cannot vend credentials at all."
        )
        print(
            "     Not a probe result: the sign-in path itself is refusing, and every probe behind"
        )
        print(
            "     it reads 'no credentials in <account>' rather than passing. If the accounts that"
        )
        print("     failed are the member accounts and Management still answers, suspect a policy")
        print(
            "     reaching STS - see Lesson 24 and the awsds-org-rcp-perimeter row in POLICIES.md."
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
