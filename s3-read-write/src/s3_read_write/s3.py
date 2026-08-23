"""Read, write and list operations on the project's S3 prefix.

These functions are deliberately ordinary S3 code: they expect a session
that is *already* authorized for the paths being touched — normally the
prefix-scoped session returned by :func:`s3_read_write.vending.scoped_session`.
Nothing here knows about SageMaker, Access Grants or the persona; keeping
the authentication concern in :mod:`s3_read_write.vending` and the object
operations here mirrors the reference project
(`benes3 <https://github.com/felipenoris/benes3>`_), where "authentication
lives in another module" is the organizing rule.

S3 concepts worth keeping in mind
---------------------------------

* **Key and prefix**: S3 has no real directories — each file is an
  *object* under a string *key*; slashes are convention, and "listing a
  folder" is filtering keys by prefix. The SMUS project path is exactly
  such a prefix: ``<domain-id>/<project-id>/<scope>/...``.
* **Managed transfers** (``upload_file`` / ``download_file``): for local
  files, boto3's transfer manager splits large objects into parallel
  multipart uploads and retries transient failures. Preferred over manual
  ``put_object`` / ``get_object`` whenever the source or destination is a
  file on disk.
* **Scope**: with credentials vended at ``Minimal``/``Default`` privilege,
  calls outside the granted prefix fail with ``AccessDenied`` — that is
  the feature working, not a bug in this module.

There is deliberately no delete function: the task this library serves is
read, write and list. That is an API-surface choice, not a control — a
session vended with WRITE or READWRITE carries ``s3:DeleteObject`` on the
granted prefix (Access Grants has no put-without-delete level) and plain
boto3 can call it; the projects bucket is versioned, so such a delete is a
recoverable delete marker.
"""

import os
from typing import Any

import boto3

from s3_read_write._pagination import paginate

__all__ = [
    "split_s3_uri",
    "list_objects",
    "read_object_bytes",
    "download_file",
    "write_object_bytes",
    "upload_file",
]


def split_s3_uri(uri: str) -> tuple[str, str]:
    """Split an ``s3://bucket/prefix`` URI into ``(bucket, prefix)``.

    Access Grants speaks ``s3://...`` URIs (grant scopes, vend targets)
    while the S3 object APIs take bucket and key separately; this helper
    converts between the two so callers can carry a single string around.
    A trailing ``*`` (common in grant scopes) is stripped.

    Args:
        uri: an ``s3://bucket`` or ``s3://bucket/prefix`` string.

    Returns:
        The ``(bucket, prefix)`` pair; ``prefix`` may be empty.

    Raises:
        ValueError: if ``uri`` does not start with ``s3://``.
    """
    scheme = "s3://"
    if not uri.startswith(scheme):
        raise ValueError(f"Not an S3 URI: {uri}")
    bucket, _, prefix = uri.removeprefix(scheme).partition("/")
    return bucket, prefix.removesuffix("*")


def list_objects(session: boto3.Session, bucket: str, prefix: str = "") -> list[dict[str, Any]]:
    """List the objects of a bucket under a prefix.

    Uses ``ListObjectsV2`` with a paginator, so it works for any number of
    objects (the API caps each page at 1000 items).

    Requires ``s3:ListBucket`` on the bucket, which the vended credentials
    carry confined to the granted prefix — listing outside it is denied.

    Args:
        session: boto3 session authorized for the prefix (normally the
            vended one).
        bucket: bucket name.
        prefix: filters objects whose key starts with this text — for the
            project storage, always start at the project path, e.g.
            ``"<domain-id>/<project-id>/shared/"``.

    Returns:
        A list of dictionaries with ``key``, ``size_bytes`` and
        ``last_modified``.
    """
    s3 = session.client("s3")
    return [
        {
            "key": obj["Key"],
            "size_bytes": obj["Size"],
            "last_modified": obj["LastModified"],
        }
        for obj in paginate(s3, "list_objects_v2", "Contents", Bucket=bucket, Prefix=prefix)
    ]


def read_object_bytes(session: boto3.Session, bucket: str, key: str) -> bytes:
    """Read an object's content directly into memory.

    Alternative to :func:`download_file` for small objects (configuration
    files, small datasets). ``GetObject`` returns the content as a stream;
    ``.read()`` consumes it whole into memory, so avoid this for large
    objects.

    Requires ``s3:GetObject`` on the key.

    Args:
        session: boto3 session authorized for the key.
        bucket: bucket name.
        key: key of the object to read.

    Returns:
        The complete object content, as bytes.

    Raises:
        botocore.exceptions.ClientError: ``NoSuchKey`` if absent, or
            ``AccessDenied`` outside the granted prefix.
    """
    s3 = session.client("s3")
    response = s3.get_object(Bucket=bucket, Key=key)
    return response["Body"].read()


def download_file(session: boto3.Session, bucket: str, key: str, destination_path: str) -> None:
    """Download an object to a local file.

    Uses boto3's managed transfer (parallel parts, automatic retries).
    An existing local file at ``destination_path`` is silently replaced.

    Requires ``s3:GetObject`` on the key.

    Args:
        session: boto3 session authorized for the key.
        bucket: bucket name.
        key: key of the object to download.
        destination_path: local destination; intermediate directories are
            created if missing.
    """
    directory = os.path.dirname(destination_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    s3 = session.client("s3")
    s3.download_file(Bucket=bucket, Key=key, Filename=destination_path)


def write_object_bytes(session: boto3.Session, data: bytes, bucket: str, key: str) -> None:
    """Write in-memory bytes as an object.

    Counterpart of :func:`read_object_bytes`, for content that never
    touches disk. An existing object under the same key is silently
    replaced — standard S3 behaviour (the projects bucket is versioned,
    so the previous content survives as a noncurrent version).

    The object is encrypted at rest by the bucket's default SSE-KMS
    configuration (the project CMK); nothing needs to be passed here, but
    the caller's credentials must be allowed to use that key — the vended
    project-role session is.

    Requires ``s3:PutObject`` on the key (and key use on the bucket's
    CMK, satisfied by the vended session).

    Args:
        session: boto3 session authorized for the key.
        data: content to write.
        bucket: destination bucket name.
        key: destination key.
    """
    s3 = session.client("s3")
    s3.put_object(Bucket=bucket, Key=key, Body=data)


def upload_file(session: boto3.Session, filepath: str, bucket: str, key: str) -> str:
    """Upload a local file to the bucket.

    Uses boto3's managed transfer (multipart for large files, automatic
    retries). An existing object under the same key is silently replaced,
    with the same versioning note as :func:`write_object_bytes`.

    Unlike the reference project, ``key`` is required here: on the project
    storage every write must land under the project prefix, so a default
    of "the file's basename at the bucket root" would only ever produce
    an ``AccessDenied``.

    Requires ``s3:PutObject`` on the key (and CMK use, satisfied by the
    vended session).

    Args:
        session: boto3 session authorized for the key.
        filepath: local file to send.
        bucket: destination bucket name.
        key: destination key, e.g.
            ``"<domain-id>/<project-id>/shared/data.csv"``.

    Returns:
        The key used for the object.

    Raises:
        FileNotFoundError: if ``filepath`` does not exist or is not a file.
        botocore.exceptions.ClientError: on missing permission.
    """
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    s3 = session.client("s3")
    s3.upload_file(Filename=filepath, Bucket=bucket, Key=key)
    return key
