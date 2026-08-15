#!/usr/bin/env -S uv run --quiet
# tf-backends.py - the Terraform state buckets and their keys, one row per account, side by
# side. The preflight for Stage 2 steps 2 and 3, and the standing regression after them.
#
#   needs:    a live SSO session - the ONLY prerequisite:
#
#                 aws sso login --sso-session awsds
#
#   run:      ./aws/tf-backends.py                        # every awsds-* profile
#             ./aws/tf-backends.py awsds-infra-prod       # only the ones named
#             python3 aws/tf-backends.py -                # CloudShell, ambient credentials
#   writes:   aws/output/tf-backends.txt   (untracked - see .gitignore)
#   reads:    s3api:ListBuckets, GetBucketVersioning, GetBucketEncryption,
#             GetPublicAccessBlock, GetBucketPolicy, GetBucketLifecycleConfiguration,
#             GetObjectLockConfiguration, kms:ListAliases, sts:GetCallerIdentity.
#             It never creates, updates or deletes anything.
#   exits:    0 all checks passed | 1 a call failed | 2 a check FAILED
#
# WHY THIS IS MULTI-PROFILE, which aws/INDEX.md admits only for a reason. The subject is a
# PER-ACCOUNT fact whose meaning is the comparison BETWEEN accounts: a state bucket that is
# versioned, encrypted under a customer-managed key and closed to the public in five accounts
# and merely versioned in the sixth is the sixth account's hole, and a single-profile version
# would answer nothing. Same shape as account-bpa.py and AZs.py, and it pays the rule back
# the same way - section 1 prints the caller ARN of every profile.
#
# WHAT IT IS FOR, IN TWO PHASES.
#
#   BEFORE Stage 2 steps 2 and 3: "is anything already there". A bucket that already exists
#   under the name the bootstrap slice is about to claim turns the first apply into either a
#   BucketAlreadyOwnedByYou or - worse, if somebody else owns the name - a create that fails
#   after the KMS key was made. Reading first costs seconds.
#
#   AFTER them: "did every bootstrapped account get the same treatment". That is otherwise
#   one `terraform plan` per account, in six directories, with six profiles - which is the
#   kind of check that gets done once.
#
# THE THING IT MAKES VISIBLE THAT NOTHING ELSE DOES - Stage 2 step 3.4's two keys. "The PKI
# key" is two different objects: the key that encrypts the production/pki/ STATE FILE, and
# whatever key the CA itself uses. Only the first belongs to Stage 2, and it cannot be created
# by the pki/ slice, because a backend is configured at `init` - before the slice has ever
# applied. So production/bootstrap/ creates TWO keys and Production is the one account whose
# alias list should read two rather than one. Section 4 is where that is either true or not.
#
# BUCKET NAMES ARE DISCOVERED, NEVER ASSUMED. The convention is awsds-<env>-tfstate
# (docs/plan/conventions.md), but the <env> token for the Identity account is not settled in
# any plan file, and a script that hardcodes a guess reports a correctly-named bucket as
# missing. So it lists what is there and matches on `tfstate`, which also catches the failure
# a hardcoded name cannot see: a state bucket somebody named something else.

from __future__ import annotations

import sys

from awslib import context, profiles
from awslib.awscli import AwsCli, ErrorLog
from awslib.report import Checks, Report, note

OUT_NAME = "tf-backends.txt"


def main(argv: list) -> int:
    ctx = context.locate(__file__)
    out_path = ctx.out_file(OUT_NAME)
    out_label = ctx.out_label(OUT_NAME)

    selected, source = profiles.select(argv)

    errors = ErrorLog()
    callers = profiles.preflight(selected, errors, out_label=out_label)
    live = [c for c in callers if c.live]
    checks = Checks()

    def cli_for(profile: str) -> AwsCli:
        return AwsCli(profile=profile, region=context.REGION, errors=errors, echo_profile=True)

    # ------------------------------------------------------------------- measure each account
    aliases: list = []  # (profile, alias, target key id)
    buckets: list = []  # (profile, bucket, vers, sse, key, bpa, tls, lifecycle, lock)
    all_buckets: dict = {}  # profile -> every bucket name

    def alias_of(profile: str, key: str) -> str:
        """Resolve a KMS key ARN or id back to its alias, so the table says
        `alias/awsds-prod-tfstate` rather than a uuid. The alias is the thing a human
        recognises and the thing 3.4's split is expressed in."""
        if not key:
            return "-"
        kid = key.rsplit("/", 1)[-1]
        for p, aname, akey in aliases:
            if p == profile and akey == kid:
                return aname
        return "(no alias)"

    for c in live:
        p = c.profile
        cli = cli_for(p)
        note(f"measuring {p} ...")

        # KMS aliases first, so the bucket rows can name a key rather than a uuid.
        res = cli.run(
            "kms",
            "list-aliases",
            "--query",
            "Aliases[?starts_with(AliasName,`alias/awsds`)].[AliasName,TargetKeyId]",
            "--output",
            "text",
        )
        for line in res.text.splitlines():
            f = line.split("\t")
            if len(f) >= 2 and f[0]:
                aliases.append((p, f[0], f[1]))

        res = cli.run("s3api", "list-buckets", "--query", "Buckets[].Name", "--output", "text")
        if not res.ok:
            continue
        names = sorted(b for b in res.text.split() if b)
        all_buckets[p] = names

        # Match on `tfstate` rather than on a composed name - see the header. The
        # per-attribute calls below tolerate failure silently on purpose, exactly as the
        # shell did: a NoSuchBucket-shaped error reads as "not set/none/off", which the
        # checks then judge; only the two listings above are logged as failures.
        for b in (n for n in names if "tfstate" in n.lower()):
            res = cli.run(
                "s3api",
                "get-bucket-versioning",
                "--bucket",
                b,
                "--query",
                "Status",
                "--output",
                "text",
                log=False,
            )
            vers = res.text or "NOT SET"
            if vers == "None":
                vers = "NOT SET"

            res = cli.run(
                "s3api",
                "get-bucket-encryption",
                "--bucket",
                b,
                "--query",
                "ServerSideEncryptionConfiguration.Rules[0]"
                ".ApplyServerSideEncryptionByDefault.[SSEAlgorithm,KMSMasterKeyID]",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                sse, key = "NOT SET", "-"
            else:
                f = res.stdout.split("\t")
                sse = f[0] if f else ""
                key = f[1] if len(f) > 1 else ""
                if key == "None":
                    key = ""
                key = alias_of(p, key)

            res = cli.run(
                "s3api",
                "get-public-access-block",
                "--bucket",
                b,
                "--query",
                "PublicAccessBlockConfiguration.[BlockPublicAcls,IgnorePublicAcls,"
                "BlockPublicPolicy,RestrictPublicBuckets]",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                bpa = "NOT SET"
            else:
                n_true = res.stdout.split("\t").count("True")
                bpa = f"{n_true}/4"

            # The TLS-only statement checkov requires in Stage 2 step 2.1. Matching on the
            # CONDITION rather than on a Sid: the statement's name is the author's, the
            # condition is the control.
            res = cli.run(
                "s3api",
                "get-bucket-policy",
                "--bucket",
                b,
                "--query",
                "Policy",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                tls = "no policy"
            elif "aws:SecureTransport" in res.stdout:
                tls = "yes"
            else:
                tls = "NO"

            res = cli.run(
                "s3api",
                "get-bucket-lifecycle-configuration",
                "--bucket",
                b,
                "--query",
                "Rules[].[ID,Status]",
                "--output",
                "text",
                log=False,
            )
            if not res.ok:
                lc = "none"
            else:
                n_rules = len([ln for ln in res.stdout.splitlines() if ln])
                lc = f"{n_rules} rule(s)"
                res = cli.run(
                    "s3api",
                    "get-bucket-lifecycle-configuration",
                    "--bucket",
                    b,
                    "--query",
                    "Rules[?NoncurrentVersionExpiration!=`null`].ID",
                    "--output",
                    "text",
                    log=False,
                )
                lc += ", noncurrent" if res.text else ", NO noncurrent"

            res = cli.run(
                "s3api",
                "get-object-lock-configuration",
                "--bucket",
                b,
                "--query",
                "ObjectLockConfiguration.ObjectLockEnabled",
                "--output",
                "text",
                log=False,
            )
            lock = res.text or "off" if res.ok else "off"

            buckets.append((p, b, vers, sse, key, bpa, tls, lc, lock))

    # ------------------------------------------------------------------------------- checks
    for c in live:
        p = c.profile
        mine = [row for row in buckets if row[0] == p]
        if not mine:
            checks.note(
                "BK-0",
                f"{p} has a state bucket",
                "none found. Expected BEFORE Stage 2 steps 2 and 3 have run in "
                "this account; a REGRESSION after. Nothing below is checked for "
                "this account.",
            )
            continue
        checks.ok("BK-0", f"{p} has a state bucket", f"{len(mine)} found")

        for _p, b, vers, sse, key, bpa, tls, lc, lock in mine:
            if vers == "Enabled":
                checks.ok("BK-1", f"versioning on {b}", "Enabled")
            else:
                checks.fail(
                    "BK-1",
                    f"versioning on {b}",
                    f"{vers} - without versioning a corrupt apply overwrites the "
                    "only copy of the state, and S3 native locking (use_lockfile, "
                    "D3) has nothing to fall back on.",
                )
            if sse == "aws:kms":
                checks.ok("BK-2", f"SSE-KMS on {b}", f"key {key}")
            elif sse == "AES256":
                checks.fail(
                    "BK-2",
                    f"SSE-KMS on {b}",
                    "AES256 - SSE-S3, not a customer-managed key. The key policy "
                    "is where 'who can read this state' is expressed, and D36 has "
                    "no other mechanism (Lesson 18).",
                )
            else:
                checks.fail("BK-2", f"SSE-KMS on {b}", sse)
            if key == "(no alias)":
                checks.note(
                    "BK-2",
                    f"SSE-KMS on {b}",
                    "the key has no alias, so nothing in a report can name it. "
                    "Aliases are free; add one.",
                )
            if bpa == "4/4":
                checks.ok("BK-3", f"block public access on {b}", "4/4")
            else:
                checks.fail(
                    "BK-3",
                    f"block public access on {b}",
                    f"{bpa} - three of four is not a partial pass: "
                    "RestrictPublicBuckets alone still allows a public ACL.",
                )
            if tls == "yes":
                checks.ok("BK-4", f"TLS-only policy on {b}", "aws:SecureTransport present")
            else:
                checks.fail(
                    "BK-4",
                    f"TLS-only policy on {b}",
                    f"{tls} - Stage 2 step 2.1 writes it explicitly rather than "
                    "letting checkov add it, because a policy the linter wrote is "
                    "a policy nobody read.",
                )
            if ", noncurrent" in lc:
                checks.ok("BK-5", f"noncurrent-version lifecycle on {b}", lc)
            else:
                checks.fail(
                    "BK-5",
                    f"noncurrent-version lifecycle on {b}",
                    f"{lc} - every apply writes a version, and a rule added later "
                    "does not reach what already accumulated (Stage 2 step 2.1).",
                )
            if lock != "off":
                checks.note(
                    "BK-6",
                    f"no Object Lock on {b}",
                    f"Object Lock reads '{lock}'. Nothing in this design puts it "
                    "on a STATE bucket - INV-14 is the CloudTrail bucket in Log "
                    "Archive - and a locked state bucket cannot be re-encrypted "
                    "or cleaned up.",
                )

    # BK-7: the two-key split of Stage 2 step 3.4, which only Production should show.
    for c in live:
        if "prod" not in c.profile:
            continue
        pki_aliases = [aname for p, aname, _k in aliases if p == c.profile and "pki" in aname]
        if pki_aliases:
            checks.ok("BK-7", f"the pki STATE key exists in {c.profile}", ", ".join(pki_aliases))
        else:
            checks.note(
                "BK-7",
                f"the pki STATE key exists in {c.profile}",
                "no alias matching 'pki'. Expected until Stage 2 step 3 runs. "
                "After it, this is the check that production/pki/ shares the "
                "Production bucket under its OWN key (D36) rather than under the "
                "account state key - one bucket, two keys, two answerable "
                "questions.",
            )

    # --------------------------------------------------------------------------- the report
    with open(out_path, "w", encoding="utf-8") as stream:
        rep = Report(stream)

        rep.banner("Terraform state buckets and their keys, one row per account")
        rep.text(f"""generated : {context.utc_stamp()}
profiles  : {source}
region    : {context.REGION}
produced  : aws/tf-backends.py   (index: aws/INDEX.md)

SECTIONS
  1. Which accounts were measured, and as whom
  2. The state buckets found, side by side
  3. The checks
  4. The KMS aliases, and Stage 2 step 3.4`s two keys
  5. The accounts nothing here is measuring
  6. Calls that failed

HOW TO READ THIS FILE
  - "NO STATE BUCKET" IS THE EXPECTED ANSWER UNTIL STAGE 2 STEPS 2 AND 3 HAVE RUN.
    It is reported as a `note`, not as a failure, and it becomes a REGRESSION the
    moment that account has been bootstrapped.
  - A MISSING ACCOUNT IS NOT A PASSING ACCOUNT. Section 5 names the ones nothing
    reached; an account in neither section 2 nor section 5 is the hole this script
    exists to expose - the same rule account-bpa.py carries.
  - BUCKET NAMES ARE DISCOVERED, matching on `tfstate`. A state bucket named
    something else still shows up here; one named nothing at all does not exist.
  - THE KEY COLUMN NAMES AN ALIAS. `(no alias)` means the bucket is encrypted under
    a key nothing can refer to by name, which makes every later report unreadable.""")

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
        rep.h1("2. The state buckets found, side by side")

        if buckets:
            rep.tabulate(
                ["PROFILE\tBUCKET\tVERSIONING\tSSE\tKEY\tBPA\tTLS-ONLY\tLIFECYCLE\tOBJ LOCK"]
                + sorted("\t".join(row) for row in buckets)
            )
        else:
            rep.text("""NONE FOUND IN ANY MEASURED ACCOUNT.

This is the expected state before Stage 2 steps 2 and 3. What the report is worth
right now is section 5 and the `allb` note below: it proves the names the bootstrap
slice is about to claim are free.""")

        rep.text("""
Every bucket in each measured account, so a state bucket under an unexpected name is
visible rather than absent:

""")
        for c in live:
            rep.h2(c.profile)
            names = all_buckets.get(c.profile, [])
            if names:
                for b in names:
                    rep.line(f"  {b}")
            else:
                rep.line("  (no buckets at all in this account)")

        # ==============================================================================
        rep.h1("3. The checks")

        rep.checks_table(checks)
        rep.line()
        rep.line(f"{checks.n_fail()} check(s) FAILED.")

        # ==============================================================================
        rep.h1("4. The KMS aliases, and Stage 2 step 3.4's two keys")

        rep.text("""PRODUCTION IS THE ONE ACCOUNT THAT SHOULD SHOW TWO. Stage 2 step 3.4 splits the key
that encrypts production/pki/`s STATE from the account`s general state key, because
D36 puts the CA root private key in that state file: one key for both would make "who
can read Production state" and "who can mint a certificate for any internal name" the
same permission. Every other account shows one.

""")

        if aliases:
            rep.tabulate(
                ["PROFILE\tALIAS\tTARGET KEY"]
                + sorted(f"{p}\t{aname}\t{akey}" for p, aname, akey in aliases)
            )
        else:
            rep.line(
                "(no awsds-* aliases in any measured account - expected before Stage 2 step 2)"
            )

        # ==============================================================================
        rep.h1("5. The accounts nothing here is measuring")

        rep.text("""Read this BEFORE reading section 3 as a pass.

  - Management, Log Archive and Audit hold NO CLI profile, by design, and none of
    them is a Terraform-managed account: Management is bootstrap-only (principle 1),
    and the other two are Control Tower`s. They have no state bucket and must not.
  - `Policy Canary` deliberately gets NO state bucket either (D29, docs/plan/architecture
    §3): an account whose point is to stay empty. Its profile authenticates, so it
    appears in section 1 with no bucket - and that is the correct reading, not a gap.
  - `Staging` has no profile because the account is UNVENDED, held on the account cap
    (Stage 1a). Stage 2 step 3.2 skips its bootstrap slice for exactly this reason.
  - Every Sandbox beyond the first has no profile until Stage 14 vends it (D35).

So the expected shape once Stage 2 steps 2 and 3 are done is FIVE state buckets -
sandbox-1, dev, data, prod, identity - and a sixth when Staging is vended.""")

        # ==============================================================================
        rep.h1("6. Calls that failed")

        if errors:
            rep.line(errors.text())
            rep.text("""
A NoSuchBucket-shaped error is not listed here: a bucket that does not exist is
read as "not created yet" by the checks, which is section 3`s BK-0 note.""")
        else:
            rep.line("None. Every call returned successfully.")

        rep.line()
        rep.line("Regenerate with:  ./aws/tf-backends.py")

    # ---------------------------------------------------------------------------------- run
    n_fail = checks.n_fail()
    note("")
    if errors:
        note(f"wrote {out_label} (some calls FAILED - see section 6)")
        return 1
    if n_fail > 0:
        note(f"wrote {out_label} ({n_fail} CHECK(S) FAILED - see section 3)")
        return 2
    note(f"wrote {out_label} (all checks passed)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
