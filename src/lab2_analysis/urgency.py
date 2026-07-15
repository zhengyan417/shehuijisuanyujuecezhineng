"""Urgency scoring for decision prioritization.

OWNER: AGENT_LAB2
"""

from __future__ import annotations

from src.common.models import Emotion, Intent


def score_urgency(emotion: Emotion, intent: Intent, text: str) -> float:
    base = {"焦虑": 0.86, "不满": 0.72, "期待": 0.55, "中性": 0.34}.get(emotion, 0.4)
    if intent == "抱怨":
        base += 0.10
    elif intent == "建议":
        base += 0.05
    elif intent == "询问":
        base += 0.02

    # lexical boosters for safety-critical phrasing
    for w, bump in (
        ("危险", 0.06),
        ("不敢走", 0.07),
        ("害怕", 0.05),
        ("孩子", 0.04),
        ("老人", 0.04),
        ("反复", 0.03),
        ("没人管", 0.04),
    ):
        if w in text:
            base += bump

    return round(min(max(base, 0.0), 1.0), 3)
