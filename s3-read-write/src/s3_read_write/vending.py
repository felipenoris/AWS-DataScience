"""Credential vending for a SageMaker Unified Studio project's S3 storage.

Why this module exists
----------------------

Inside SageMaker Unified Studio (SMUS), the user never touches S3 with
their own identity: every notebook and every file-browser action runs as
the **project's IAM role** (trusted identity propagation is off in this
estate, by decision), and that role's policies reach exactly the project's
own path inside the projects bucket
(``<bucket>/<domain-id>/<project-id>/...``).

On a laptop, the user holds an **SSO persona session** instead
(``DataScientistAccess``), which deliberately has no direct grant on the
projects bucket or its KMS key. The bridge between the two identities is
**S3 Access Grants**, a credential-vending feature of S3 that SMUS itself
provisions: each project environment registers a *location* covering the
project's S3 prefix, with the project role as the location's vending role.

The flow this module implements:

1. the persona session calls ``s3control.GetDataAccess`` against the
   account's Access Grants instance, naming a target such as
   ``s3://<bucket>/<domain-id>/<project-id>/shared/*``;
2. S3 Access Grants checks that a **grant** exists for the caller on that
   prefix, assumes the location's role (the project role) and hands back
   short-lived credentials **scoped down to the granted prefix**;
3. the laptop uses those credentials with plain boto3 S3 calls — the same
   identity Studio uses, so bucket policy and KMS behave identically.

Two prerequisites live outside this code: the persona's IAM policy must
allow the vending handshake (``s3:GetDataAccess`` plus the two discovery
reads, on the Access Grants instance), and a grant for the persona role
must exist on the project's location. Both are administered in the
infrastructure repository, not here.

boto3 concepts used here
------------------------

* **S3 Control client** (``session.client("s3control")``): the S3
  *account-level* API — Access Grants lives here, not on the ``s3``
  client. Every operation takes an explicit ``AccountId``.
* **Session** (``boto3.Session``): holds credentials + region. This module
  receives an authenticated session (the SSO persona) and *returns* a new
  one built from the vended credentials, so downstream code does ordinary
  ``session.client("s3")`` work without knowing where the credentials
  came from.
"""

from typing import Any

import boto3

from s3_read_write._pagination import paginate

__all__ = [
    "list_caller_grants",
    "vend_credentials",
    "scoped_session",
]


def _account_id(session: boto3.Session) -> str:
    """Return the account id of the session's identity, via STS.

    S3 Control operations require an explicit ``AccountId`` parameter.
    The Access Grants instance queried by this module is always the one in
    the caller's own account (the persona and the projects bucket live in
    the same account), so the id is derived from the session instead of
    being passed around — and never hard-coded.
    """
    return session.client("sts").get_caller_identity()["Account"]


def list_caller_grants(session: boto3.Session, prefix: str | None = None) -> list[dict[str, Any]]:
    """List the S3 Access Grants available to the calling identity.

    This is the discovery half of the flow: it answers "which project
    prefixes can I ask credentials for?" without requiring the caller to
    know domain ids or project ids in advance — useful because SMUS path
    segments (``dzd-.../<project-id>/``) are machine-generated.

    Requires the ``s3:ListCallerAccessGrants`` permission on the account's
    Access Grants instance.

    Args:
        session: authenticated boto3 session (the SSO persona).
        prefix: optional ``s3://...`` scope filter; only grants at or
            under it are returned.

    Returns:
        A list of dictionaries with ``grant_scope`` (the ``s3://...``
        prefix the grant covers) and ``permission`` (``READ``, ``WRITE``
        or ``READWRITE``).
    """
    s3control = session.client("s3control")
    kwargs: dict[str, Any] = {"AccountId": _account_id(session)}
    if prefix is not None:
        kwargs["GrantScope"] = prefix
    return [
        {
            "grant_scope": grant["GrantScope"],
            "permission": grant["Permission"],
        }
        for grant in paginate(
            s3control, "list_caller_access_grants", "CallerAccessGrantsList", **kwargs
        )
    ]


def vend_credentials(
    session: boto3.Session,
    target: str,
    permission: str = "READWRITE",
    duration_seconds: int = 3600,
    privilege: str = "Default",
) -> dict[str, Any]:
    """Ask S3 Access Grants for temporary credentials on an S3 prefix.

    This is the vend itself (``GetDataAccess``). If a grant covering
    ``target`` exists for the caller, the service assumes the location's
    IAM role — for SMUS locations, the **project role** — and returns
    short-lived credentials restricted to the granted prefix.

    Requires the ``s3:GetDataAccess`` permission on the account's Access
    Grants instance, *and* a matching grant.

    Args:
        session: authenticated boto3 session (the SSO persona).
        target: the ``s3://bucket/prefix/*`` being requested. Asking for a
            sub-prefix of the granted scope is fine.
        permission: ``READ``, ``WRITE`` or ``READWRITE``.
        duration_seconds: credential lifetime, 900–43200 (AWS bounds).
            Prefer the shortest duration the task needs: the credentials
            are bearer tokens once issued.
        privilege: ``Default`` widens the credentials to the whole granted
            scope; ``Minimal`` narrows them to exactly ``target``.

    Returns:
        A dictionary with ``access_key_id``, ``secret_access_key``,
        ``session_token``, ``expiration`` (an aware ``datetime``) and
        ``matched_grant_target`` (the grant scope that satisfied the
        request).

    Raises:
        botocore.exceptions.ClientError: ``AccessDenied`` if the persona
            lacks the handshake permission or no grant covers the target.
    """
    s3control = session.client("s3control")
    response = s3control.get_data_access(
        AccountId=_account_id(session),
        Target=target,
        Permission=permission,
        DurationSeconds=duration_seconds,
        Privilege=privilege,
    )
    credentials = response["Credentials"]
    return {
        "access_key_id": credentials["AccessKeyId"],
        "secret_access_key": credentials["SecretAccessKey"],
        "session_token": credentials["SessionToken"],
        "expiration": credentials["Expiration"],
        "matched_grant_target": response.get("MatchedGrantTarget"),
    }


def scoped_session(
    session: boto3.Session,
    target: str,
    permission: str = "READWRITE",
    duration_seconds: int = 3600,
) -> boto3.Session:
    """Build a boto3 session holding vended, prefix-scoped credentials.

    Convenience wrapper over :func:`vend_credentials`: the returned
    session authenticates as the project role (scoped down to the granted
    prefix) and can be handed directly to the functions in
    :mod:`s3_read_write.s3`.

    Note that the vended credentials are **not renewed** automatically:
    after ``duration_seconds`` the session's calls start failing with
    ``ExpiredToken`` — call this function again for a fresh one.

    Args:
        session: authenticated boto3 session (the SSO persona).
        target: the ``s3://bucket/prefix/*`` to request access to.
        permission: ``READ``, ``WRITE`` or ``READWRITE``.
        duration_seconds: credential lifetime, 900–43200.

    Returns:
        A new ``boto3.Session`` in the same region as ``session``, whose
        identity is the project role restricted to the granted prefix.
    """
    vended = vend_credentials(
        session, target, permission=permission, duration_seconds=duration_seconds
    )
    return boto3.Session(
        aws_access_key_id=vended["access_key_id"],
        aws_secret_access_key=vended["secret_access_key"],
        aws_session_token=vended["session_token"],
        region_name=session.region_name,
    )
