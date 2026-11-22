"""EXC-27: the role a Bedrock IDE flow environment creates for itself, judged by its shape.

The flow app's stack creates `AmazonBedrockFlowServiceRole-<environment id>` with AWS's
`SageMakerStudioBedrockFlowServiceRolePolicy` and no permissions boundary, whatever the blueprint
configuration names (SUP-447). The user took it as an exception on 2026-11-22 (Stage 17's log), so
`sandbox-ml.py` ML-8 and `studio.py` US-8 note a role of this shape instead of failing on it, and
fail on one that differs in any part: the name, the trust and its scope to this account's flows, the
attached policy or an inline policy.
"""

from __future__ import annotations

EXCEPTION_ID = "EXC-27"
NAME_PREFIX = "AmazonBedrockFlowServiceRole-"
MANAGED_POLICY = "SageMakerStudioBedrockFlowServiceRolePolicy"
TRUSTED_SERVICE = "bedrock.amazonaws.com"

NOTE = (
    f"{EXCEPTION_ID}: a Bedrock IDE flow environment's own role, created with no boundary "
    f"(SUP-447); trusted by {TRUSTED_SERVICE} for this account's flows alone, {MANAGED_POLICY} "
    "its only policy."
)


def _as_list(value) -> list:
    if value is None:
        return []
    return [value] if isinstance(value, (str, dict)) else list(value)


def _scope_problems(statement: dict, account: str | None) -> list:
    """What keeps a trust statement from naming this account's flows alone."""
    cond = statement.get("Condition") or {}
    source_account = _as_list((cond.get("StringEquals") or {}).get("aws:SourceAccount"))
    source_arn = _as_list((cond.get("ArnLike") or {}).get("aws:SourceArn"))
    problems = []
    if not source_account:
        problems.append("trust carries no aws:SourceAccount")
    elif account and source_account != [account]:
        problems.append("trust's aws:SourceAccount is not this account")
    flows = f":{account}:flow/" if account else ":flow/"
    if not source_arn:
        problems.append("trust carries no aws:SourceArn")
    elif any(not (a.startswith("arn:aws:bedrock:") and flows in a) for a in source_arn):
        problems.append("trust's aws:SourceArn names more than this account's flows")
    return problems


def shape_problems(
    name: str, trust: dict | None, attached: list, inline: list, account: str | None = None
) -> list:
    """What keeps an unbounded role out of EXC-27's shape; empty when the role matches it."""
    problems = []
    if not name.startswith(NAME_PREFIX):
        problems.append(f"name not {NAME_PREFIX}*")
    statements = _as_list((trust or {}).get("Statement"))
    if not statements:
        problems.append("no trust statement read")
    for st in statements:
        principal = st.get("Principal") if isinstance(st, dict) else None
        actions = _as_list(st.get("Action")) if isinstance(st, dict) else []
        if not isinstance(st, dict) or st.get("Effect") != "Allow":
            problems.append("a trust statement other than Allow")
        elif not isinstance(principal, dict) or set(principal) != {"Service"}:
            problems.append(f"a trust principal other than a service: {principal}")
        elif _as_list(principal["Service"]) != [TRUSTED_SERVICE]:
            problems.append(f"trusts {principal['Service']}")
        elif actions != ["sts:AssumeRole"]:
            problems.append(f"trust actions {actions}")
        else:
            problems += _scope_problems(st, account)
    if list(attached) != [MANAGED_POLICY]:
        problems.append(f"attached {', '.join(attached) or 'none'}")
    if inline:
        problems.append(f"inline {', '.join(inline)}")
    return problems
