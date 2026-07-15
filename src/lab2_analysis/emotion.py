"""Emotion classifier (domain-specific, not product-review polarity).

OWNER: AGENT_LAB2
"""

from __future__ import annotations

from src.common.models import Emotion, Intent


def classify_emotion(
    text: str,
    intent: Intent,
    mapping_cfg: dict,
    rule_emotion: str | None = None,
) -> Emotion:
    cues = mapping_cfg.get("emotion_cues") or {}
    for emo in ("焦虑", "不满", "期待"):
        for cue in cues.get(emo, []):
            if cue in text:
                return emo  # type: ignore[return-value]

    if rule_emotion in {"不满", "焦虑", "期待", "中性"}:
        return rule_emotion  # type: ignore[return-value]

    # Intent priors when cues are weak
    if intent == "询问":
        return "中性"
    if intent == "建议":
        return "期待"
    if intent == "抱怨":
        return "不满"
    return "中性"
