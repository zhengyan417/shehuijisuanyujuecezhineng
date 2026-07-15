"""Intent classifier for public-facility posts.

OWNER: AGENT_LAB2
"""

from __future__ import annotations

from src.common.models import Intent


def classify_intent(text: str, mapping_cfg: dict, rule_intent: str | None = None) -> Intent:
    cues = mapping_cfg.get("intent_cues") or {}
    # Inquiry has priority when explicit question markers exist
    for cue in cues.get("询问", []):
        if cue in text:
            return "询问"
    for cue in cues.get("建议", []):
        if cue in text:
            return "建议"
    for cue in cues.get("抱怨", []):
        if cue in text:
            return "抱怨"
    if rule_intent in {"抱怨", "建议", "询问", "其他"}:
        return rule_intent  # type: ignore[return-value]
    return "其他"
