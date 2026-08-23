"""Laptop access to a SageMaker Unified Studio project's S3 storage.

Two modules, one seam:

* :mod:`s3_read_write.vending` — turns the SSO persona session into a
  short-lived session of the **project role**, scoped to the project's S3
  prefix, via S3 Access Grants (``GetDataAccess``). All the SMUS-specific
  knowledge lives here.
* :mod:`s3_read_write.s3` — ordinary read/write/list operations, taking
  whatever authorized session they are given. No SMUS knowledge at all.

Typical use::

    import boto3
    from s3_read_write import s3, vending

    persona = boto3.Session(profile_name="awsds-scientist-sandbox")

    # Which project prefixes can I reach?
    grants = vending.list_caller_grants(persona)

    # Trade the persona session for a prefix-scoped project-role session.
    target = grants[0]["grant_scope"]
    project = vending.scoped_session(persona, target)

    bucket, prefix = s3.split_s3_uri(target)
    s3.list_objects(project, bucket, prefix)

See ``README.md`` for the prerequisites (VPN up, the persona's vending
permission, and a grant for the project) — none of them is this
library's to create.
"""

from s3_read_write import s3, vending

__all__ = ["s3", "vending"]
