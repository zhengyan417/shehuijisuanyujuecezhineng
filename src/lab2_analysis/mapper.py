"""Complaint/inquiry -> standardized need mapping.

OWNER: AGENT_LAB2
"""

from __future__ import annotations

import re

from src.common.models import FacilityScope, MappedNeed


def _rule_match(text: str, rule: dict) -> bool:
    keys = rule.get("if_any_keywords") or []
    mode = rule.get("match_mode", "keyword")
    if mode == "regex_or_keyword":
        for k in keys:
            if ".*" in k or "(" in k:
                if re.search(k, text):
                    return True
            elif k in text:
                return True
        return False
    return any(k in text for k in keys)


def map_need(
    text: str,
    mapping_cfg: dict,
    facility_scope: FacilityScope | None = None,
) -> tuple[MappedNeed, str | None, str | None]:
    """Return (mapped_need, rule_default_intent, rule_default_emotion)."""
    catalog = {n["id"]: n for n in mapping_cfg.get("needs_catalog", [])}

    for rule in mapping_cfg.get("mapping_rules", []):
        if not _rule_match(text, rule):
            continue
        need = catalog.get(rule["need_id"], {})
        # If rule scope conflicts with strong facility scope, skip soft rules only when mismatch
        need_scope = need.get("facility_scope")
        if facility_scope and need_scope and need_scope != facility_scope:
            # allow occupancy/charging rules only for charging scope etc.
            continue
        return (
            MappedNeed(
                need_id=rule.get("need_id"),
                need_name_zh=need.get("name_zh"),
                facility_scope=need_scope,
                rule_id=rule.get("id"),
            ),
            rule.get("default_intent"),
            rule.get("default_emotion"),
        )

    # scope fallback
    fallback = (mapping_cfg.get("scope_fallback_need") or {}).get(facility_scope or "")
    if fallback and fallback in catalog:
        need = catalog[fallback]
        return (
            MappedNeed(
                need_id=fallback,
                need_name_zh=need.get("name_zh"),
                facility_scope=need.get("facility_scope"),
                rule_id="SCOPE_FALLBACK",
            ),
            None,
            None,
        )
    return MappedNeed(), None, None
