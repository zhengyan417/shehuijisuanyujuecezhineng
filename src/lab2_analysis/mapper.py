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
            if any(ch in k for ch in ".*+?[]()|^$"):
                try:
                    if re.search(k, text):
                        return True
                except re.error:
                    if k in text:
                        return True
            elif k in text:
                return True
        return False
    return any(k in text for k in keys)


def has_scope_evidence(text: str, mapping_cfg: dict, facility_scope: FacilityScope | None) -> bool:
    if not facility_scope:
        return False
    cues = (mapping_cfg.get("scope_evidence_cues") or {}).get(facility_scope) or []
    return any(c in text for c in cues)


def map_need(
    text: str,
    mapping_cfg: dict,
    facility_scope: FacilityScope | None = None,
    has_facility_entity: bool = False,
) -> tuple[MappedNeed, str | None, str | None]:
    """Return (mapped_need, rule_default_intent, rule_default_emotion)."""
    catalog = {n["id"]: n for n in mapping_cfg.get("needs_catalog", [])}

    for rule in mapping_cfg.get("mapping_rules", []):
        if not _rule_match(text, rule):
            continue
        need = catalog.get(rule["need_id"], {})
        need_scope = need.get("facility_scope")
        if facility_scope and need_scope and need_scope != facility_scope:
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

    # scope fallback — only with facility evidence to avoid off-topic false needs
    require_evidence = bool(mapping_cfg.get("scope_fallback_requires_evidence", True))
    evidence_ok = has_facility_entity or has_scope_evidence(text, mapping_cfg, facility_scope)
    if require_evidence and not evidence_ok:
        return MappedNeed(), None, None

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
