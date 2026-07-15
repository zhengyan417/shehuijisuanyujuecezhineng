"""Raw data sources for Lab1.

OWNER: AGENT_LAB1

HARD RULE (team policy):
  ABSOLUTELY NO FAKE / FIXTURE SOCIAL-MEDIA DATA for the course pipeline.
  If there is no real crawled or manually imported data, FAIL LOUDLY.
  Do not invent posts. Do not fall back to samples.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.common.io import dump_models, parse_models, read_jsonl, write_json, write_jsonl
from src.common.models import PostRaw
from src.common.paths import RAW, ensure_data_dirs
from src.lab1_collection.queries import build_queries, queries_as_dicts

SourceMode = Literal["auto", "raw", "crawl"]


class CollectionError(RuntimeError):
    pass


NO_FAKE_DATA_MSG = (
    "NO REAL DATA — refused to use fake/fixture posts.\n"
    "Team policy: 绝对禁止假数据；没有真实微博数据就不跑流水线。\n"
    "Get real data first:\n"
    "  1) put Weibo Cookie into secrets/weibo_cookie.txt\n"
    "  2) python scripts/run_weibo_crawl.py\n"
    "  3) python scripts/convert_weibo_to_lab1.py\n"
    "Or place a real export at data/raw/import_*.jsonl / data/raw/crawl_*.jsonl\n"
)


def load_raw_dir_posts(raw_dir: Path | None = None) -> list[PostRaw]:
    ensure_data_dirs()
    d = raw_dir or RAW
    files = sorted(
        f
        for f in d.glob("*.jsonl")
        if f.name.startswith("import_") or f.name.startswith("crawl_")
    )
    if not files:
        raise CollectionError(NO_FAKE_DATA_MSG + f"(looked under {d})")
    rows: list[dict] = []
    for f in files:
        rows.extend(read_jsonl(f))
    if not rows:
        raise CollectionError(NO_FAKE_DATA_MSG + f"(empty files under {d})")
    # sanity: reject fixture-looking platforms dominating a supposed real dump
    platforms = {r.get("platform") for r in rows}
    if platforms == {"fixture"}:
        raise CollectionError(NO_FAKE_DATA_MSG + "(file only contains platform=fixture)")
    return parse_models(rows, PostRaw)


def try_crawl_posts() -> list[PostRaw]:
    """Load real Weibo crawl outputs only. Never fabricate rows."""
    ensure_data_dirs()
    existing = sorted(RAW.glob("crawl_*.jsonl"))
    if existing:
        rows: list[dict] = []
        for f in existing:
            rows.extend(read_jsonl(f))
        if rows and not ({r.get("platform") for r in rows} == {"fixture"}):
            return parse_models(rows, PostRaw)

    from src.lab1_collection.weibo_adapter import RESULT_ROOT, convert_weibo_csvs

    if RESULT_ROOT.exists() and any(RESULT_ROOT.rglob("*.csv")):
        out = convert_weibo_csvs()
        return parse_models(read_jsonl(out), PostRaw)

    cookie = os.getenv("WEIBO_COOKIE", "").strip()
    cookie_file = Path(__file__).resolve().parents[2] / "secrets" / "weibo_cookie.txt"
    has_cookie = bool(cookie)
    if cookie_file.exists():
        body = cookie_file.read_text(encoding="utf-8")
        has_cookie = has_cookie or any(
            ln.strip() and not ln.strip().startswith("#") for ln in body.splitlines()
        )
    hint = NO_FAKE_DATA_MSG
    if not has_cookie:
        hint += "(Cookie missing — cannot crawl yet.)\n"
    else:
        hint += "(Cookie present but crawl/convert not run yet, or结果 empty.)\n"
    raise CollectionError(hint)


def collect_raw_posts(mode: SourceMode = "auto") -> tuple[list[PostRaw], dict]:
    """Collect real PostRaw only. Never falls back to fixtures."""
    ensure_data_dirs()
    provenance: dict = {
        "mode_requested": mode,
        "queries": queries_as_dicts(),
        "query_count": len(build_queries()),
        "source_used": None,
        "fallback": False,
        "fake_data_allowed": False,
        "error": None,
        "collected_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }

    def _ok(posts: list[PostRaw], source: str) -> tuple[list[PostRaw], dict]:
        provenance["source_used"] = source
        provenance["raw_count"] = len(posts)
        return posts, provenance

    if mode == "raw":
        return _ok(load_raw_dir_posts(), str(RAW))

    if mode == "crawl":
        return _ok(try_crawl_posts(), "crawl")

    # auto: crawl_* / import_* only — no fixture fallback
    try:
        return _ok(load_raw_dir_posts(), str(RAW))
    except CollectionError:
        return _ok(try_crawl_posts(), "crawl")


def persist_raw_snapshot(posts: list[PostRaw], provenance: dict, stem: str = "beijing_raw") -> Path:
    ensure_data_dirs()
    out = RAW / f"{stem}.jsonl"
    write_jsonl(out, dump_models(posts))
    write_json(RAW / f"{stem}_provenance.json", provenance)
    write_json(RAW / "lab1_query_plan.json", {"queries": provenance.get("queries", [])})
    return out
