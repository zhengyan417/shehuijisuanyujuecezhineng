"""Mechanical text normalize + dedupe + geo only.

OWNER: AGENT_LAB1

NO keyword blacklists for keep/drop. Semantic filtering is llm_filter.py.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Iterable

from src.common.io import load_yaml
from src.common.models import FacilityScope, GeoInfo, Lab1Meta, PostCleaned, PostRaw
from src.common.paths import KEYWORDS
from src.lab1_collection.geo import infer_district

LAB1_VERSION = "lab1-llm-filter-0.6.0"

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_MENTION_RE = re.compile(r"@\S+")
_TOPIC_RE = re.compile(r"#[^#\s]+#")
_MULTI_WS = re.compile(r"\s+")
_EMOJI_LIKE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002700-\U000027BF"
    "]+",
    flags=re.UNICODE,
)


def normalize_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.replace("\u3000", " ").replace("\xa0", " ")
    text = _URL_RE.sub(" ", text)
    text = _MENTION_RE.sub(" ", text)
    text = _TOPIC_RE.sub(lambda m: m.group(0).strip("#"), text)
    text = _EMOJI_LIKE.sub(" ", text)
    text = _MULTI_WS.sub(" ", text).strip()
    return text


def fingerprint(text: str) -> str:
    key = re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE).lower()
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def infer_facility_scope(text: str, hint: FacilityScope | None) -> FacilityScope | None:
    """Soft label only — never used alone to drop rows."""
    if hint:
        return hint
    tax = load_yaml(KEYWORDS).get("facility_types") or {}
    scores: dict[str, int] = {}
    for scope, cfg in tax.items():
        score = 0
        for w in list(cfg.get("labels") or []) + list(cfg.get("symptoms") or []):
            if w and w in text:
                score += 2 if w in (cfg.get("labels") or []) else 1
        if score:
            scores[scope] = score
    if not scores:
        return None
    return max(scores, key=scores.get)  # type: ignore[arg-type]


def _place_from_query(source_query: str | None) -> str | None:
    if not source_query:
        return None
    tax = load_yaml(KEYWORDS)
    places = list(tax.get("place_hints", {}).get("hotspots", [])) + list(
        tax.get("place_hints", {}).get("district_shorts", [])
    )
    for p in sorted(places, key=len, reverse=True):
        if p and source_query.startswith(p):
            return p
    if source_query.startswith("北京"):
        return "北京"
    return None


def clean_posts(posts: Iterable[PostRaw]) -> list[PostCleaned]:
    """Mechanical pass only: normalize, too_short, duplicate, geo, soft scope hint."""
    seen: set[str] = set()
    out: list[PostCleaned] = []

    for p in posts:
        clean_text = normalize_text(p.text)
        dropped = False
        drop_reason = None
        is_dup = False
        q_place = _place_from_query(p.source_query)

        if len(clean_text) < 8:
            dropped = True
            drop_reason = "too_short"

        fp = fingerprint(clean_text)
        if not dropped and fp in seen:
            is_dup = True
            dropped = True
            drop_reason = "duplicate"
        elif not dropped:
            seen.add(fp)

        scope = infer_facility_scope(clean_text, p.facility_scope_hint)

        # Prefer PostRaw structured geo; only then text; query-place is last soft poi fallback
        poi = p.poi
        geo_raw = p.geo_raw
        district, conf, matched = infer_district(
            clean_text,
            district_hint=p.district_hint,
            geo_raw=geo_raw,
            poi=poi,
        )
        if not district and not matched and q_place and q_place != "北京":
            # structured fields empty → try query place as soft poi (not mixed into text matching)
            district, conf, matched = infer_district("", poi=q_place)

        geo = GeoInfo(
            raw=geo_raw or matched,
            poi=poi or matched or (None if q_place == "北京" else q_place),
            district=district,
            confidence=conf,
        )

        out.append(
            PostCleaned(
                id=p.id,
                platform=p.platform,
                text=p.text,
                clean_text=clean_text,
                time=p.time,
                city="北京",
                geo=geo,
                meta=Lab1Meta(
                    lab1_version=LAB1_VERSION,
                    is_duplicate=is_dup,
                    dropped=dropped,
                    drop_reason=drop_reason,
                    facility_scope_hint=scope,
                ),
            )
        )
    return out
