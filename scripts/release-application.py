#!/usr/bin/env -S uv run --quiet
# release-application.py - Stage 10 step 2.4: a release's bundle written into a deployment target's
# definitions home, the release job of each promotion leg (Stage 8 steps 3.2 and 3.6).
#
#   run:      ./scripts/release-application.py <account> --bundle <app>.zip --sha256 <hex>
#                 --tag vX.Y.Z --image-uri <uri> [--app app-etl] [--release-vars <file>] [--dry-run]
#   reads:    the bundle, already downloaded by the runner's own role (Stage 8 decision 20); data/'s
#             state for the outputs bucket; the states render-workflow.py reads.
#   writes:   s3://<outputs bucket>/applications/<app>/<tag>/, the bundle's tree with each workflow
#             rendered for the account and MANIFEST.sha256 last; the inbox inbox/<app>/ from samples/
#             (decision 20 (d)); with --release-vars, the orchestration slice's `release` as tfvars
#             JSON. --dry-run writes nothing and prints what it would.
#   exit:     0 written and read back | 1 a check failed | 2 usage
#
# Run as the account's deploy role (by hand, its infrastructure profile, Stage 8 step 3.8). The order
# is the step's: the bundle's SHA256 against the value the tag pipeline passed down, before a file of
# it is read; every object written with an SHA256 checksum S3 computes; the manifest last; then the
# prefix read back with list-objects-v2 and head-object --checksum-mode ENABLED, failing on a key
# missing, a key the manifest lacks or a checksum that differs. Nothing is downloaded to check it.
# An inbox object is written only when absent or different: each object created there starts the
# consuming chain through its bridge (Stage 10 step 3.6).

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from tfhygiene.states import StateError, state_outputs

REPO = Path(__file__).resolve().parents[1]
MANIFEST = "MANIFEST.sha256"


class ReleaseError(Exception):
    pass


def sha256_hex(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hex_to_b64(digest: str) -> str:
    return base64.b64encode(bytes.fromhex(digest)).decode()


def aws_json(*args: str) -> dict:
    res = subprocess.run(["aws", *args, "--output", "json"], capture_output=True, text=True)
    if res.returncode != 0:
        raise ReleaseError(f"aws {' '.join(args[:2])}: {res.stderr.strip()}")
    return json.loads(res.stdout) if res.stdout.strip() else {}


def unpack(bundle: Path, into: Path) -> list:
    """The bundle's files, refusing a member that would land outside `into`."""
    names = []
    with zipfile.ZipFile(bundle) as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            target = (into / info.filename).resolve()
            if into.resolve() not in target.parents:
                raise ReleaseError(f"{info.filename}: outside the bundle's tree")
            names.append(info.filename)
        z.extractall(into)
    return sorted(names)


def render(account: str, source: Path, out: Path, tag: str, image_uri: str, app: str) -> None:
    res = subprocess.run(
        [
            str(REPO / "scripts" / "render-workflow.py"),
            account,
            str(source),
            "--tag",
            tag,
            "--image-uri",
            image_uri,
            "--app",
            app,
            "--out",
            str(out),
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        raise ReleaseError(f"render {source.name}: {res.stderr.strip()}")


def put(bucket: str, key: str, path: Path, dry: bool) -> dict:
    if dry:
        return {"VersionId": "(dry run)"}
    return aws_json(
        "s3api",
        "put-object",
        "--bucket",
        bucket,
        "--key",
        key,
        "--body",
        str(path),
        "--checksum-algorithm",
        "SHA256",
    )


def head_checksum(bucket: str, key: str) -> str | None:
    """The object's SHA256 checksum, base64 as S3 keeps it, or None when absent."""
    res = subprocess.run(
        [
            "aws",
            "s3api",
            "head-object",
            "--bucket",
            bucket,
            "--key",
            key,
            "--checksum-mode",
            "ENABLED",
            "--output",
            "json",
        ],
        capture_output=True,
        text=True,
    )
    if res.returncode != 0:
        if "404" in res.stderr or "Not Found" in res.stderr:
            return None
        raise ReleaseError(f"head-object {key}: {res.stderr.strip()}")
    return json.loads(res.stdout).get("ChecksumSHA256")


def release(args) -> int:
    if sha256_hex(args.bundle) != args.sha256:
        raise ReleaseError(f"{args.bundle}: SHA256 differs from the value the tag pipeline passed")
    bucket = state_outputs(args.account, "data")["outputs_bucket_name"]
    prefix = f"applications/{args.app}/{args.tag}/"
    print(f"== {args.bundle.name} {args.sha256} into s3://{bucket}/{prefix}")

    with tempfile.TemporaryDirectory() as tmp:
        tree = Path(tmp) / "bundle"
        rendered = Path(tmp) / "rendered"
        tree.mkdir()
        rendered.mkdir()
        names = unpack(args.bundle, tree)

        # Each file to write, and the bundle's own SHA256 beside the written one's.
        files = {}
        for name in names:
            source = tree / name
            written = source
            if re.fullmatch(r"workflows/[^/]+\.ya?ml", name):
                written = rendered / Path(name).name
                render(args.account, source, written, args.tag, args.image_uri, args.app)
            files[name] = (written, sha256_hex(written), sha256_hex(source))

        version_ids = {}
        for name, (path, _, _) in files.items():
            reply = put(bucket, prefix + name, path, args.dry_run)
            version_ids[name] = reply.get("VersionId")
            print(f"  wrote {prefix}{name} {version_ids[name]}")

        lines = [
            f"{written}  {bundled}  {path.stat().st_size}  {prefix}{name}"
            for name, (path, written, bundled) in sorted(files.items())
        ]
        manifest = Path(tmp) / MANIFEST
        manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
        put(bucket, prefix + MANIFEST, manifest, args.dry_run)
        print(f"  wrote {prefix}{MANIFEST}, {len(lines)} entries")
        for line in lines:
            print(f"    {line}")

        if not args.dry_run:
            listed = aws_json(
                "s3api", "list-objects-v2", "--bucket", bucket, "--prefix", prefix
            ).get("Contents", [])
            keys = {o["Key"] for o in listed}
            expected = {prefix + n: hex_to_b64(w) for n, (_, w, _) in files.items()}
            expected[prefix + MANIFEST] = hex_to_b64(sha256_hex(manifest))
            extra = sorted(keys - set(expected))
            if extra:
                raise ReleaseError(f"{', '.join(extra)}: in the prefix, not in the manifest")
            for key, checksum in sorted(expected.items()):
                if key not in keys:
                    raise ReleaseError(f"{key}: in the manifest, missing from the prefix")
                if head_checksum(bucket, key) != checksum:
                    raise ReleaseError(f"{key}: its checksum differs from the manifest's")
            print(f"  read back: {len(expected)} objects, each checksum the manifest's")

        # Decision 20 (d): the template's own test input, written only when absent or different.
        for name, (path, written, _) in sorted(files.items()):
            if not name.startswith("samples/"):
                continue
            key = f"inbox/{args.app}/{name[len('samples/') :]}"
            current = None if args.dry_run else head_checksum(bucket, key)
            if current == hex_to_b64(written):
                print(f"  inbox {key}: unchanged")
                continue
            put(bucket, key, path, args.dry_run)
            print(f"  inbox {key}: written")

    if args.release_vars:
        workflows = {}
        for name in names:
            m = re.fullmatch(r"workflows/([^/]+)\.ya?ml", name)
            if not m:
                continue
            entry = {"definition_version_id": version_ids[name]}
            code = f"code/{m.group(1)}.zip"
            if code in version_ids:
                entry["code_version_id"] = version_ids[code]
            workflows[m.group(1)] = entry
        doc = {"release": {"tag": args.tag, "workflows": workflows}}
        args.release_vars.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        print(f"== {args.release_vars}: the orchestration slice's release")
    return 0


def main(argv: list) -> int:
    ap = argparse.ArgumentParser(description="Write a release's bundle into a target's home.")
    ap.add_argument("account", choices=["staging", "production"])
    ap.add_argument("--bundle", type=Path, required=True)
    ap.add_argument("--sha256", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--image-uri", required=True)
    ap.add_argument("--app", default="app-etl")
    ap.add_argument("--release-vars", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        ap.error("--tag is the release tag, vMAJOR.MINOR.PATCH")
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
        ap.error("--sha256 is 64 lowercase hex characters")
    try:
        return release(args)
    except (OSError, ReleaseError, StateError, zipfile.BadZipFile) as e:
        print(f"release-application: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
