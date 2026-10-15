#!/usr/bin/env python3
# versions.py - the house image's versions in every account that runs it (AWS-DataScience's Stage 8
# step 1.6, decisions 7 and 18). Standard library and the AWS CLI only, so the deploy image runs it as
# it is.
#
#   register  creates the approved release's image version from the pushed digest, with the release's
#             semver as an alias, and reads it back against that digest. The domain attaches the image
#             with no version number, so the portal offers the new version at once and no domain write
#             follows (dev-env.md §B)
#   retire    deletes every version past the newest --keep that nothing names. A version a space or a
#             domain still names stays and is listed: a space whose version is gone does not start
#             (AWS_STATE.md EXC-09), and the steward moves it first
#
#   python3 release/versions.py register --tag <flavour>-v<semver>-<sha> --digest sha256:<64 hex>
#   python3 release/versions.py retire --keep 10
#
#   --target P      a profile to act as, repeatable. Default: every awsds-deploy-devenv-* profile in the
#                   AWS config, the deploy runner's one per Sandbox unit. From a laptop, the
#                   infrastructure user's SSO profile: --target awsds-infra-sandbox-1
#   --repository U  register only: the ECR repository URI the digest is in. Default: the repository of
#                   the newest version the image already holds
#   --dry-run       reads, and prints each write instead of making it
#
#   needs:  the AWS CLI v2, and a region in each profile
#   writes: register, one image version per target; retire, the deletion of the versions it names
#   exit:   0 done | 1 a step failed | 2 usage or refusal
#
# Each target account holds one image named awsds-<env>-dev-env, found by name, so no account list lives
# in this project: the targets are the deploy runner's profiles, which AWS-DataScience's
# production/runners/ renders from its map of Sandbox units (D35). User profiles are not read for
# references: SageMaker Unified Studio attaches images on the domain and pins versions on the space.

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time

TAG_RE = re.compile(r"^[a-z0-9]+-v(\d+\.\d+\.\d+)(-[0-9a-f]{8,40})?$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
IMAGE_RE = re.compile(r"^awsds-[a-z0-9-]+-dev-env$")
DEPLOY_PROFILE_RE = re.compile(r"^awsds-deploy-devenv-[a-z0-9-]+$")
CREATE_TIMEOUT_S = 300


class Refusal(Exception):
    """A condition under which nothing is written: exit 2."""


def masked(text: str) -> str:
    """The same text with every account id replaced: a job log carries none."""
    return re.sub(r"\b[0-9]{12}\b", "<acct>", text)


def aws(profile: str, *args: str, write: bool = False, dry: bool = False) -> dict | None:
    """One AWS CLI call as `profile`, its JSON parsed. A write is announced, and under --dry-run not made."""
    cmd = ["aws", "--profile", profile, "--output", "json", *args]
    if write:
        print(f"  $ {masked(' '.join(cmd))}", flush=True)
        if dry:
            return None
    res = subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if res.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:2])}: {masked(res.stderr.strip())}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def targets(given: list[str] | None) -> list[str]:
    """The profiles to act as: the ones named, or every dev-env deploy profile in the AWS config."""
    if given:
        return given
    res = subprocess.run(
        ["aws", "configure", "list-profiles"],
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )
    if res.returncode != 0:
        raise Refusal(f"aws configure list-profiles: {res.stderr.strip()}")
    found = sorted(p for p in res.stdout.split() if DEPLOY_PROFILE_RE.match(p))
    if not found:
        raise Refusal("no awsds-deploy-devenv-* profile in the AWS config, and no --target")
    return found


def the_image(profile: str) -> dict:
    """The account's one dev-env image."""
    out = aws(profile, "sagemaker", "list-images", "--name-contains", "dev-env")
    images = [i for i in out.get("Images", []) if IMAGE_RE.match(i["ImageName"])]
    if len(images) != 1:
        names = ", ".join(i["ImageName"] for i in images) or "none"
        raise Refusal(f"expected one awsds-<env>-dev-env image, found {names}")
    return images[0]


def versions(profile: str, image: str) -> list[dict]:
    """Every version of the image, newest first, with its container image and its aliases."""
    out = aws(profile, "sagemaker", "list-image-versions", "--image-name", image)
    held = []
    for v in sorted(out.get("ImageVersions", []), key=lambda v: v["Version"], reverse=True):
        number = str(v["Version"])
        d = aws(
            profile,
            "sagemaker",
            "describe-image-version",
            "--image-name",
            image,
            "--version-number",
            number,
        )
        a = aws(
            profile, "sagemaker", "list-aliases", "--image-name", image, "--version-number", number
        )
        held.append(
            {
                "version": v["Version"],
                "status": d.get("ImageVersionStatus"),
                "container": d.get("ContainerImage", ""),
                "aliases": a.get("SageMakerImageVersionAliases", []),
            }
        )
    return held


def app_settings(block: dict) -> list[dict]:
    """The per-app-type settings of a domain's or a space's settings block."""
    return [v for k, v in block.items() if k.endswith("AppSettings") and isinstance(v, dict)]


def references(profile: str, image: dict, held: list[dict]) -> dict[int, list[str]]:
    """Version number -> who names it: a space's pinned version or alias, or a domain's numbered entry.

    A space created in the portal pins a version ARN; one set by update-space may name an alias, which
    resolves to the version holding it. A domain attaches with no number since decision 7, and an
    entry that still carries one keeps its version too. An image named with neither starts the newest,
    which is always kept.
    """
    name, image_arn = image["ImageName"], image["ImageArn"]
    version_arn = image_arn.replace(":image/", ":image-version/") + "/"
    by_alias = {alias: v["version"] for v in held for alias in v["aliases"]}
    used: dict[int, list[str]] = {}

    for s in aws(profile, "sagemaker", "list-spaces").get("Spaces", []):
        d = aws(
            profile,
            "sagemaker",
            "describe-space",
            "--domain-id",
            s["DomainId"],
            "--space-name",
            s["SpaceName"],
        )
        where = f"space {s['DomainId']}/{s['SpaceName']}"
        for settings in app_settings(d.get("SpaceSettings", {})):
            spec = settings.get("DefaultResourceSpec") or {}
            arn = spec.get("SageMakerImageVersionArn", "")
            if arn.startswith(version_arn):
                used.setdefault(int(arn[len(version_arn) :]), []).append(where)
            elif (
                spec.get("SageMakerImageArn") == image_arn
                and spec.get("SageMakerImageVersionAlias") in by_alias
            ):
                used.setdefault(by_alias[spec["SageMakerImageVersionAlias"]], []).append(where)

    for dom in aws(profile, "sagemaker", "list-domains").get("Domains", []):
        d = aws(profile, "sagemaker", "describe-domain", "--domain-id", dom["DomainId"])
        for block in (d.get("DefaultUserSettings", {}), d.get("DefaultSpaceSettings", {})):
            for settings in app_settings(block):
                for entry in settings.get("CustomImages", []):
                    if (
                        entry.get("ImageName") == name
                        and entry.get("ImageVersionNumber") is not None
                    ):
                        used.setdefault(entry["ImageVersionNumber"], []).append(
                            f"domain {dom['DomainId']}"
                        )
    return used


def register(profile: str, args: argparse.Namespace) -> None:
    image = the_image(profile)
    name = image["ImageName"]
    semver = TAG_RE.match(args.tag).group(1)
    held = versions(profile, name)
    print(f"\n== {profile}: {name}, {len(held)} version(s), release {args.tag}", flush=True)

    for v in held:
        if v["container"].endswith(f"@{args.digest}"):
            print(f"  already registered: version {v['version']}, {v['status']}")
            return
    for v in held:
        if semver in v["aliases"]:
            raise Refusal(
                f"alias {semver} is version {v['version']}'s, another digest: bump the release"
            )

    repository = args.repository
    if not repository:
        if not held:
            raise Refusal("no version to read the repository from: pass --repository")
        repository = held[0]["container"].split("@", 1)[0]
    out = aws(
        profile,
        "sagemaker",
        "create-image-version",
        "--image-name",
        name,
        "--base-image",
        f"{repository}@{args.digest}",
        "--aliases",
        semver,
        "--vendor-guidance",
        "STABLE",
        "--release-notes",
        args.tag,
        write=True,
        dry=args.dry_run,
    )
    if out is None:
        return

    number = out["ImageVersionArn"].rsplit("/", 1)[-1]
    deadline = time.monotonic() + CREATE_TIMEOUT_S
    while True:
        d = aws(
            profile,
            "sagemaker",
            "describe-image-version",
            "--image-name",
            name,
            "--version-number",
            number,
        )
        status = d.get("ImageVersionStatus")
        if status == "CREATED":
            break
        if status == "CREATE_FAILED":
            raise RuntimeError(f"version {number} CREATE_FAILED: {d.get('FailureReason')}")
        if time.monotonic() > deadline:
            raise RuntimeError(f"version {number} still {status} after {CREATE_TIMEOUT_S} s")
        time.sleep(3)

    container = d.get("ContainerImage", "")
    print(f"  {name} version {number}: CREATED, alias {semver}")
    print(f"    ContainerImage {masked(container)}")
    print(f"    pushed digest  {args.digest}")
    if not container.endswith(f"@{args.digest}"):
        raise RuntimeError(f"version {number}'s ContainerImage is not the pushed digest")


def retire(profile: str, args: argparse.Namespace) -> bool:
    image = the_image(profile)
    name = image["ImageName"]
    held = versions(profile, name)
    used = references(profile, image, held)
    print(
        f"\n== {profile}: {name}, {len(held)} version(s), keeping the newest {args.keep}",
        flush=True,
    )
    for v in held[: args.keep]:
        print(f"  keep    version {v['version']} {' '.join(v['aliases'])}")

    ok = True
    for v in held[args.keep :]:
        if v["version"] in used:
            print(f"  keep    version {v['version']}, named by {', '.join(used[v['version']])}")
            continue
        try:
            aws(
                profile,
                "sagemaker",
                "delete-image-version",
                "--image-name",
                name,
                "--version-number",
                str(v["version"]),
                write=True,
                dry=args.dry_run,
            )
            print(f"  retired version {v['version']} {' '.join(v['aliases'])}")
        except RuntimeError as e:
            print(f"  FAILED  version {v['version']}: {e}")
            ok = False
    return ok


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="The house image's versions in every account that runs it."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("register", "retire"):
        p = sub.add_parser(command)
        p.add_argument("--target", action="append", help="a profile to act as, repeatable")
        p.add_argument(
            "--dry-run", action="store_true", help="read, and print each write instead of making it"
        )
        if command == "register":
            p.add_argument(
                "--tag", required=True, help="the image tag, <flavour>-v<semver>[-<sha>]"
            )
            p.add_argument("--digest", required=True, help="the dev-env digest the build pushed")
            p.add_argument("--repository", help="the ECR repository URI the digest is in")
        else:
            p.add_argument(
                "--keep", type=int, default=10, help="how many of the newest versions stay"
            )
    args = parser.parse_args(argv)

    if args.command == "register":
        if not TAG_RE.match(args.tag):
            print(f"not a dev-env tag: {args.tag} - <flavour>-v<semver>[-<sha>]", file=sys.stderr)
            return 2
        if not DIGEST_RE.match(args.digest):
            print(f"not a digest: {args.digest}", file=sys.stderr)
            return 2
    elif args.keep < 1:
        print("--keep is at least 1: the newest version is never retired", file=sys.stderr)
        return 2

    try:
        profiles = targets(args.target)
    except Refusal as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    print(f"targets: {', '.join(profiles)}")

    failed = refused = 0
    for profile in profiles:
        try:
            if args.command == "register":
                register(profile, args)
            elif not retire(profile, args):
                failed += 1
        except Refusal as e:
            print(f"  REFUSED ({profile}): {e}")
            refused += 1
        except RuntimeError as e:
            print(f"  FAILED ({profile}): {e}")
            failed += 1
    if refused:
        return 2
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
