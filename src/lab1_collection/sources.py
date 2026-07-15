"""Raw data sources for Lab1: fixture / local raw / optional crawl hook.

OWNER: AGENT_LAB1

Network crawl is OFF by default. Course demo must stay offline-green.
If a future crawl plugin fails, automatically fall back to fixtures.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.common.io import dump_models, parse_models, read_jsonl, write_json, write_jsonl
from src.common.models import PostRaw
from src.common.paths import RAW, SAMPLE_RAW, ensure_data_dirs
from src.lab1_collection.queries import build_queries, queries_as_dicts

SourceMode = Literal["auto", "fixture", "raw", "crawl"]


class CollectionError(RuntimeError):
    pass


def load_fixture_posts(path: Path | None = None) -> list[PostRaw]:
    p = path or SAMPLE_RAW
    if not p.exists():
        raise CollectionError(f"fixture missing: {p}")
    return parse_models(read_jsonl(p), PostRaw)


def load_raw_dir_posts(raw_dir: Path | None = None, pattern: str = "*.jsonl") -> list[PostRaw]:
    ensure_data_dirs()
    d = raw_dir or RAW
    files = sorted(
        f
        for f in d.glob(pattern)
        if f.name.endswith(".jsonl")
        and not f.name.endswith("_provenance.json")
        and f.name != "lab1_query_plan.json"
    )
    # Ignore auto-written snapshot so "auto" can refresh from fixture.
    # Manual imports / crawls should use these names:
    #   data/raw/import_*.jsonl  OR  data/raw/crawl_*.jsonl
    manual = [f for f in files if f.name.startswith("import_") or f.name.startswith("crawl_")]
    use_files = manual if manual else []
    if not use_files:
        raise CollectionError(f"no manual/crawl raw jsonl under {d} (expect import_*.jsonl or crawl_*.jsonl)")
    rows: list[dict] = []
    for f in use_files:
        rows.extend(read_jsonl(f))
    if not rows:
        raise CollectionError(f"empty manual/crawl raw jsonl under {d}")
    return parse_models(rows, PostRaw)


def try_crawl_posts() -> list[PostRaw]:
    """Optional crawl entrypoint.

    Intentionally not implementing platform scrapers here:
    - anti-bot / ToS risk
    - course requires reproducible offline demo

    Hook for future: read credentials from env and call an approved API client.
    Always raise for now so caller falls back.
    """
    raise CollectionError(
        "crawl backend not configured; set --source fixture|raw or provide data/raw/import_*.jsonl"
    )


def collect_raw_posts(mode: SourceMode = "auto") -> tuple[list[PostRaw], dict]:
    """Collect PostRaw according to mode. Always returns posts + provenance dict."""
    ensure_data_dirs()
    provenance: dict = {
        "mode_requested": mode,
        "queries": queries_as_dicts(),
        "query_count": len(build_queries()),
        "source_used": None,
        "fallback": False,
        "error": None,
        "collected_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }

    def _ok(posts: list[PostRaw], source: str, fallback: bool = False) -> tuple[list[PostRaw], dict]:
        provenance["source_used"] = source
        provenance["fallback"] = fallback
        provenance["raw_count"] = len(posts)
        return posts, provenance

    if mode == "fixture":
        return _ok(load_fixture_posts(), str(SAMPLE_RAW))

    if mode == "raw":
        return _ok(load_raw_dir_posts(), str(RAW))

    if mode == "crawl":
        try:
            return _ok(try_crawl_posts(), "crawl")
        except CollectionError as e:
            provenance["error"] = str(e)
            posts = load_fixture_posts()
            return _ok(posts, str(SAMPLE_RAW), fallback=True)

    # auto: prefer manual/crawl imports, else fixture (offline-first)
    try:
        posts = load_raw_dir_posts()
        return _ok(posts, str(RAW))
    except CollectionError as e:
        provenance["error"] = str(e)
        return _ok(load_fixture_posts(), str(SAMPLE_RAW), fallback=True)


def persist_raw_snapshot(posts: list[PostRaw], provenance: dict, stem: str = "beijing_raw") -> Path:
    ensure_data_dirs()
    out = RAW / f"{stem}.jsonl"
    write_jsonl(out, dump_models(posts))
    write_json(RAW / f"{stem}_provenance.json", provenance)
    # also dump query plan for presentation
    write_json(RAW / "lab1_query_plan.json", {"queries": provenance.get("queries", [])})
    return out
