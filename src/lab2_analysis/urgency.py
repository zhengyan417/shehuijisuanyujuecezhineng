"""Urgency scoring for decision prioritization.

OWNER: AGENT_LAB2
"""

from __future__ import annotations

from src.common.models import Emotion, Intent


def score_urgency(
    emotion: Emotion,
    intent: Intent,
    text: str,
    *,
    is_mediated: bool = False,
    has_need: bool = True,
) -> float:
    if not has_need:
        return 0.0

    base = {"焦虑": 0.86, "不满": 0.72, "期待": 0.55, "中性": 0.34}.get(emotion, 0.4)
    if intent == "抱怨":
        base += 0.10
    elif intent == "建议":
        base += 0.05
    elif intent == "询问":
        base += 0.02

    for w, bump in (
        ("危险", 0.06),
        ("不敢走", 0.07),
        ("害怕", 0.05),
        ("孩子", 0.04),
        ("老人", 0.04),
        ("反复", 0.03),
        ("没人管", 0.04),
        ("摸着黑", 0.05),
        ("黑灯瞎火", 0.05),
        ("充不上", 0.04),
        ("排队", 0.03),
    ):
        if w in text:
            base += bump

    # Mediated (接诉/媒体转述) still counts, but slightly down-weight vs first-person.
    if is_mediated:
        base *= 0.92

    return round(min(max(base, 0.0), 1.0), 3)
