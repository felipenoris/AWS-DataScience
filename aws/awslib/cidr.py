"""IPv4 CIDR overlap, shared by the networking scripts.

Host bits are masked rather than rejected (``strict=False``). Anything that is not an IPv4
CIDR - an IPv6 block, a prefix-list id, ``-`` - reports "no overlap", because the callers pass
route destinations of every shape and only the IPv4 question is being asked.
"""

from __future__ import annotations

import ipaddress
import re

_IPV4_CIDR = re.compile(r"^[0-9]+\.[0-9.]*/\d+$")


def overlap(a: str, b: str) -> bool:
    """True when the two IPv4 CIDR blocks share at least one address."""
    if not (_IPV4_CIDR.match(a or "") and _IPV4_CIDR.match(b or "")):
        return False
    try:
        na = ipaddress.IPv4Network(a, strict=False)
        nb = ipaddress.IPv4Network(b, strict=False)
    except ValueError:
        return False
    return na.overlaps(nb)
