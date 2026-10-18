"""The Bedrock scope, read out of the SCP that declares it.

THE SCP IS THE DECLARATION. Stage 6e decision 15 put the scoped models and the routed regions
into two statements of `awsds-org-scp-ou-interactive.json`, and that document is the ceiling an
invocation actually meets. Every other spelling of the list - the grant slice's `models` map, the
image's managed-settings pins, the endpoint policy - is a floor underneath it, and a script that
carried its own copy would be one more place for the set to go stale (Lesson 33).

That is not hypothetical: `bedrock.py` carried a literal, and it still named the models of the
generation Stage 6e decision 14 abandoned on 2026-09-12 - so its `BR-4` reported `pass` about three
profiles nobody had scoped for a day. A reader that returns None when the document is unreadable is
what makes the difference visible instead of plausible.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCP_PATH = "terraform-live/identity/org-policies/policies/awsds-org-scp-ou-interactive.json"
GRANT_VARS = "terraform-live/sandbox/bedrock/variables.tf"

# The keys of the house image's managed settings that pin a model, read by settings_pins().
PIN_KEYS = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
)

# `default = { "model" = "profile" ... }` inside the models block of the grant slice. Anchored on
# the variable name so another map in the same file cannot be picked up by accident.
MODELS_RE = re.compile(r'variable\s+"models"\s*\{.*?default\s*=\s*\{(?P<body>.*?)\}', re.S)
PAIR_RE = re.compile(r'"(?P<model>[^"]+)"\s*=\s*"(?P<profile>[^"]+)"')

SID_MODELS = "DenyBedrockInvocationOutsideTheScopedModels"
SID_REGIONS = "DenyBedrockReadsOutsideTheRoutedRegions"

PROFILE_ARN_RE = re.compile(r"^arn:aws:bedrock:[^:]*:[^:]*:inference-profile/(?P<id>.+)$")
MODEL_ARN_RE = re.compile(r"^arn:aws:bedrock:[^:]*::foundation-model/(?P<id>.+)$")


def scp_declaration(path: Path) -> tuple[dict | None, list | None, str]:
    """(models -> profile, routed regions, why it is None) read out of the SCP document.

    ``path`` is the document itself. A caller inside the repository passes
    ``ctx.repo_root / SCP_PATH``; a caller running standalone (CloudShell, where `locate` finds
    no repository) passes a path that does not exist and gets the `why` string to print.
    """
    if not path.is_file():
        return None, None, f"{SCP_PATH} not found - running outside the repository"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, None, f"{SCP_PATH} is not valid JSON: {exc}"

    by_sid = {st.get("Sid"): st for st in doc.get("Statement", [])}

    pairs: dict[str, str] = {}
    st = by_sid.get(SID_MODELS)
    if st is not None:
        profiles_seen, models_seen = {}, set()
        for arn in st.get("NotResource", []):
            m = PROFILE_ARN_RE.match(arn)
            if m:
                pid = m.group("id")
                # `us.anthropic.claude-x` is the profile for `anthropic.claude-x`.
                profiles_seen[pid.split(".", 1)[1] if "." in pid else pid] = pid
                continue
            m = MODEL_ARN_RE.match(arn)
            if m:
                models_seen.add(m.group("id"))
        for model in sorted(models_seen):
            pairs[model] = profiles_seen.get(model, "")

    regions = None
    st = by_sid.get(SID_REGIONS)
    if st is not None:
        cond = st.get("Condition", {}).get("StringNotEquals", {})
        value = cond.get("aws:RequestedRegion")
        if isinstance(value, str):
            regions = [value]
        elif isinstance(value, list):
            regions = sorted(value)

    missing = [s for s, present in ((SID_MODELS, pairs), (SID_REGIONS, regions)) if not present]
    why = f"{SCP_PATH} carries no {', '.join(missing)}" if missing else ""
    return (pairs or None), regions, why


def grant_models(path: Path) -> dict | None:
    """The grant slice's `models` map, model id -> inference profile id, or None when unreadable."""
    if not path.is_file():
        return None
    match = MODELS_RE.search(path.read_text(encoding="utf-8"))
    if not match:
        return None
    return {m.group("model"): m.group("profile") for m in PAIR_RE.finditer(match.group("body"))}


def settings_pins(path: Path) -> dict | None:
    """The profile ids the image's managed settings pin, by key, or None when unreadable."""
    if not path.is_file():
        return None
    try:
        env = json.loads(path.read_text(encoding="utf-8")).get("env", {})
    except json.JSONDecodeError:
        return None
    return {k: env[k] for k in PIN_KEYS if k in env}
