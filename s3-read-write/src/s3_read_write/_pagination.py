"""Internal pagination helper, shared by the package modules.

The ``_`` prefix in the module name marks it as an internal detail of the
``s3_read_write`` package, not part of the public API.

Why this helper exists: AWS listing APIs return results in batches
("pages"), and obtaining the complete list means repeating the call with a
continuation token. boto3 abstracts that loop with *paginators*
(``client.get_paginator(...)``); this module abstracts the remaining step —
accumulating the items of every page — so the other modules do not repeat
the same loop (following the convention of the reference project,
`benes3 <https://github.com/felipenoris/benes3>`_).
"""

from typing import Any


def paginate(client: Any, operation: str, result_key: str, **kwargs: Any) -> list[Any]:
    """Walk every page of an AWS listing operation.

    Args:
        client: boto3 client of the service (for example, the S3 or the
            S3 Control client).
        operation: name of the listing operation (e.g. ``"list_objects_v2"``).
        result_key: response key holding the items (e.g. ``"Contents"``).
        **kwargs: parameters forwarded to the operation (e.g. ``Bucket=...``).

    Returns:
        A list with the items of every page, concatenated.
    """
    paginator = client.get_paginator(operation)
    items: list[Any] = []
    for page in paginator.paginate(**kwargs):
        # .get() because AWS APIs commonly omit the key when a page has no
        # results.
        items.extend(page.get(result_key, []))
    return items
