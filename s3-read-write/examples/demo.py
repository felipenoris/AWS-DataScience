"""End-to-end demo: laptop -> project S3 path, via S3 Access Grants.

What it does, in order (steps 4-6 WRITE one small object under the
project's ``shared/`` scope, key ``s3-read-write-demo/hello.txt``, and
read it back; nothing is deleted — this library exposes no delete helper
by design, though the READWRITE-vended session itself does carry
``s3:DeleteObject`` on the granted prefix, because Access Grants' WRITE
level includes delete — a convention here, not a control):

1. builds the persona session from ``--profile``;
2. discovers the caller's Access Grants (which project prefixes exist);
3. vends a prefix-scoped project-role session for ``--target`` (or the
   first discovered grant) and prints the identity it received — expect
   an ``assumed-role/datazone_usr_role_...`` ARN, which is the whole
   point: the laptop is acting as the project role, not as the persona;
4. writes the demo object;
5. lists the prefix;
6. reads the object back and checks the content.

Run it ON THE VPN, signed in as the data-scientist persona::

    uv run examples/demo.py --profile awsds-scientist-sandbox

Failures it explains rather than hides: ``AccessDenied`` on the discovery
call (the persona's vending permission is not applied, or the tunnel is
down), an empty grant list (no grant was created for this persona yet),
and ``AccessDenied`` on the vend (a grant exists but not for this
identity or permission level).
"""

import argparse
import sys

import boto3
from botocore.exceptions import ClientError
from s3_read_write import s3, vending

DEMO_KEY_SUFFIX = "s3-read-write-demo/hello.txt"
DEMO_CONTENT = b"hello from the laptop, via S3 Access Grants\n"


def error_code(error: ClientError) -> str:
    """Extract the AWS error code from a boto3 ClientError."""
    return error.response.get("Error", {}).get("Code", "?")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--profile",
        default="awsds-scientist-sandbox",
        help="AWS named profile of the persona session (default: %(default)s)",
    )
    parser.add_argument(
        "--target",
        default=None,
        help=(
            "s3://... prefix to request access to; default: the first grant returned by discovery"
        ),
    )
    args = parser.parse_args()

    persona = boto3.Session(profile_name=args.profile)

    # -- 2. discovery -------------------------------------------------------
    try:
        grants = vending.list_caller_grants(persona)
    except ClientError as error:
        print(f"Discovery failed ({error_code(error)}): {error}")
        print(
            "Checks: is the VPN tunnel up? Is the persona's "
            "VendProjectStorageCredentials statement applied?"
        )
        return 1

    print(f"Grants available to this identity: {len(grants)}")
    for grant in grants:
        print(f"  {grant['permission']:9} {grant['grant_scope']}")

    target = args.target
    if target is None:
        if not grants:
            print(
                "No grants found and no --target given. Create the "
                "per-project grant first (see README.md, 'Prerequisites — "
                "administered outside this library', item 2)."
            )
            return 1
        target = grants[0]["grant_scope"]

    # -- 3. vend ------------------------------------------------------------
    try:
        project = vending.scoped_session(persona, target)
    except ClientError as error:
        print(f"Vend failed for {target} ({error_code(error)}): {error}")
        return 1

    identity = project.client("sts").get_caller_identity()["Arn"]
    print(f"Vended identity: {identity}")

    bucket, prefix = s3.split_s3_uri(target)
    demo_key = f"{prefix.rstrip('/')}/{DEMO_KEY_SUFFIX}"

    # -- 4. write -----------------------------------------------------------
    s3.write_object_bytes(project, DEMO_CONTENT, bucket, demo_key)
    print(f"Wrote s3://{bucket}/{demo_key}")

    # -- 5. list ------------------------------------------------------------
    objects = s3.list_objects(project, bucket, prefix)
    print(f"Objects under s3://{bucket}/{prefix}: {len(objects)}")
    for obj in objects[:10]:
        print(f"  {obj['size_bytes']:>10}  {obj['key']}")
    if len(objects) > 10:
        print(f"  ... and {len(objects) - 10} more")

    # -- 6. read back -------------------------------------------------------
    content = s3.read_object_bytes(project, bucket, demo_key)
    if content != DEMO_CONTENT:
        print("Read-back MISMATCH — investigate before trusting the path.")
        return 1
    print("Read back OK — laptop read/write/list on the project path works.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
