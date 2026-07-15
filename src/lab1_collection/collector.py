"""Lab1 orchestration — collect raw posts and produce PostCleaned JSONL.

OWNER: AGENT_LAB1
Mechanical clean + optional NVIDIA LLM semantic gate (no keyword blacklists).
"""

from __future__ import annotations

import os
from collections import Counter

from src.common.io import dump_models, write_json, write_jsonl
from src.common.paths import CLEANED, ensure_data_dirs
from src.lab1_collection.cleaner import LAB1_VERSION, clean_posts
from src.lab1_collection.queries import build_queries, load_taxonomy
from src.lab1_collection.sources import SourceMode, collect_raw_posts, persist_raw_snapshot


def _stats(cleaned) -> dict:
    kept = [c for c in cleaned if not c.meta.dropped]
    dropped = [c for c in cleaned if c.meta.dropped]
    by_scope = Counter(c.meta.facility_scope_hint for c in kept if c.meta.facility_scope_hint)
    drop_reasons = Counter(c.meta.drop_reason for c in dropped)
    with_district = sum(1 for c in kept if c.geo.district)
    return {
        "lab1_version": LAB1_VERSION,
        "input_count": len(cleaned),
        "kept_count": len(kept),
        "dropped_count": len(dropped),
        "kept_by_scope": dict(by_scope),
        "drop_reasons": dict(drop_reasons),
        "kept_with_district": with_district,
        "district_coverage": round(with_district / max(len(kept), 1), 3),
        "query_plan_size": len(build_queries()),
        "taxonomy_version": load_taxonomy().get("version"),
    }


def run_lab1(
    output_name: str = "beijing_cleaned.jsonl",
    source: SourceMode = "auto",
    *,
    llm_filter: bool | None = None,
    llm_workers: int = 6,
    llm_batch_size: int = 8,
    llm_model: str | None = None,
) -> str:
    ensure_data_dirs()
    posts, provenance = collect_raw_posts(mode=source)
    persist_raw_snapshot(posts, provenance)

    cleaned = clean_posts(posts)

    use_llm = llm_filter
    if use_llm is None:
        use_llm = os.getenv("LAB1_LLM_FILTER", "0").strip() in {"1", "true", "True", "yes"}
    if use_llm:
        from src.lab1_collection import llm_filter as lf

        model = llm_model or os.getenv("LAB1_LLM_MODEL") or lf.DEFAULT_MODEL
        cleaned = lf.apply_llm_filter(
            cleaned,
            model=model,
            workers=llm_workers,
            batch_size=llm_batch_size,
        )

    kept = [c for c in cleaned if not c.meta.dropped]

    out_path = CLEANED / output_name
    write_jsonl(out_path, dump_models(kept))
    write_jsonl(CLEANED / "beijing_cleaned_with_drops.jsonl", dump_models(cleaned))

    stats = _stats(cleaned)
    stats["provenance"] = {
        "mode_requested": provenance.get("mode_requested"),
        "source_used": provenance.get("source_used"),
        "fallback": provenance.get("fallback"),
        "fake_data_allowed": provenance.get("fake_data_allowed"),
        "error": provenance.get("error"),
        "raw_count": provenance.get("raw_count"),
        "llm_filter": bool(use_llm),
    }
    write_json(CLEANED / "lab1_cleaning_report.json", stats)
    return str(out_path)


def keyword_coverage_report() -> dict:
    tax = load_taxonomy()
    return {
        "version": tax.get("version"),
        "scopes": list((tax.get("facility_types") or {}).keys()),
        "query_count": len(build_queries()),
        "collection_policy": tax.get("collection_policy"),
    }
