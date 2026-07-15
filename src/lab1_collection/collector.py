"""Lab1 — collect / load raw posts and produce PostCleaned JSONL.

OWNER: AGENT_LAB1
READS: configs/keywords_taxonomy.yaml, configs/city_beijing.yaml, fixtures/
WRITES: data/raw/*.jsonl, data/cleaned/*.jsonl
MUST NOT EDIT: src/lab2_analysis/**, src/lab3_decision/**, configs/need_mapping.yaml
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable

from src.common.io import dump_models, load_yaml, parse_models, read_jsonl, write_jsonl
from src.common.models import GeoInfo, Lab1Meta, PostCleaned, PostRaw
from src.common.paths import CITY, KEYWORDS, RAW, SAMPLE_RAW, CLEANED, ensure_data_dirs

LAB1_VERSION = "lab1-stub-0.1.0"


def _normalize_text(text: str) -> str:
    text = text.replace("\u3000", " ").strip()
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _guess_district(text: str, district_hint: str | None, districts: list[str]) -> tuple[str | None, float]:
    if district_hint:
        return district_hint, 0.9
    for d in districts:
        if d in text:
            return d, 0.8
    # soft landmark fallback — Lab1 may improve later
    landmarks = {
        "望京": "朝阳区",
        "中关村": "海淀区",
        "五道口": "海淀区",
        "回龙观": "昌平区",
        "天通苑": "昌平区",
        "通州": "通州区",
        "亦庄": "大兴区",
        "国贸": "朝阳区",
        "西单": "西城区",
        "清河": "海淀区",
    }
    for k, dist in landmarks.items():
        if k in text:
            return dist, 0.6
    return None, 0.0


def load_raw_posts(raw_path=None) -> list[PostRaw]:
    """Prefer real crawl output under data/raw; fallback to fixture."""
    ensure_data_dirs()
    path = raw_path
    if path is None:
        candidates = sorted(RAW.glob("*.jsonl"))
        path = candidates[-1] if candidates else SAMPLE_RAW
    rows = read_jsonl(path)
    return parse_models(rows, PostRaw)


def clean_posts(posts: Iterable[PostRaw]) -> list[PostCleaned]:
    city_cfg = load_yaml(CITY)
    districts = list(city_cfg.get("districts", []))
    seen: set[str] = set()
    out: list[PostCleaned] = []

    for p in posts:
        clean_text = _normalize_text(p.text)
        dropped = False
        drop_reason = None
        if len(clean_text) < 6:
            dropped = True
            drop_reason = "too_short"

        fingerprint = hashlib.md5(clean_text.encode("utf-8")).hexdigest()
        is_dup = fingerprint in seen
        if not is_dup:
            seen.add(fingerprint)
        if is_dup:
            dropped = True
            drop_reason = "duplicate"

        district, conf = _guess_district(clean_text, p.district_hint, districts)
        geo = GeoInfo(raw=p.geo_raw, poi=p.poi, district=district, confidence=conf)
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
                    facility_scope_hint=p.facility_scope_hint,
                ),
            )
        )
    return out


def run_lab1(output_name: str = "beijing_cleaned.jsonl") -> str:
    ensure_data_dirs()
    posts = load_raw_posts()
    # Also mirror raw fixture into data/raw for pipeline transparency when empty
    if not list(RAW.glob("*.jsonl")):
        write_jsonl(RAW / "beijing_from_fixture.jsonl", dump_models(posts))
    cleaned = clean_posts(posts)
    kept = [c for c in cleaned if not c.meta.dropped]
    out_path = CLEANED / output_name
    write_jsonl(out_path, dump_models(kept))
    # write full with drops for audit
    write_jsonl(CLEANED / "beijing_cleaned_with_drops.jsonl", dump_models(cleaned))
    return str(out_path)


def keyword_coverage_report() -> dict:
    """Helper for presentation: show taxonomy layers exist."""
    return load_yaml(KEYWORDS)
