"""Real Weibo crawl via crawl4weibo.

OWNER: AGENT_LAB1

Design: facility + symptom/place/need_cue combos from taxonomy;
continuous sampling (chronic domain), not one-shot disaster crawl.
Maps crawl4weibo Post -> project PostRaw (DATA_CONTRACT).
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from src.common.io import dump_models, write_json, write_jsonl
from src.common.models import FacilityScope, PostRaw
from src.common.paths import RAW, ROOT, ensure_data_dirs
from src.lab1_collection.queries import SearchQuery, build_queries

COOKIE_FILE = ROOT / "secrets" / "weibo_cookie.txt"
_TAG_RE = re.compile(r"<[^>]+>")


def _load_cookie() -> str | None:
    """Load cookie string; join continued lines; require SUB= for login cookie."""
    import os

    env = os.getenv("WEIBO_COOKIE", "").strip()
    raw = env
    if not raw and COOKIE_FILE.exists():
        lines = [
            ln.strip()
            for ln in COOKIE_FILE.read_text(encoding="utf-8").splitlines()
            if ln.strip() and not ln.strip().startswith("#")
        ]
        # allow accidental line wraps
        raw = "".join(lines) if lines else ""
    if not raw:
        return None
    raw = raw.strip().strip('"').strip("'")
    # normalize "Cookie: xxx" paste
    if raw.lower().startswith("cookie:"):
        raw = raw.split(":", 1)[1].strip()
    if "SUB=" not in raw and "SUBP=" not in raw:
        print("[crawl] warning: cookie missing SUB=/SUBP=; search quality may be poor")
    return raw


def _hash_author(user_id: str) -> str | None:
    uid = (user_id or "").strip()
    if not uid:
        return None
    return hashlib.sha256(uid.encode("utf-8")).hexdigest()[:16]


def _clean_html(text: str) -> str:
    text = _TAG_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", text).strip()


def _post_to_raw(post, query: SearchQuery) -> PostRaw | None:
    text = _clean_html(getattr(post, "text", "") or "")
    if not text:
        return None
    wid = str(getattr(post, "id", "") or getattr(post, "bid", "") or "").strip()
    if not wid:
        # stable fallback id from text+query
        wid = hashlib.md5(f"{query.query}:{text}".encode("utf-8")).hexdigest()[:12]

    created = getattr(post, "created_at", None)
    if isinstance(created, datetime):
        time_iso = created.astimezone().isoformat(timespec="seconds")
    else:
        time_iso = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

    loc = (getattr(post, "location", None) or "").strip() or None
    bid = str(getattr(post, "bid", "") or wid)
    scope: FacilityScope | None = query.facility_scope  # type: ignore[assignment]

    return PostRaw(
        id=f"wb_{wid}",
        platform="weibo",
        text=text,
        time=time_iso,
        city="北京",
        url=f"https://m.weibo.cn/detail/{bid}" if bid else None,
        author_id_hash=_hash_author(str(getattr(post, "user_id", "") or "")),
        geo_raw=loc,
        poi=loc,
        district_hint=None,
        facility_scope_hint=scope,
        source_query=query.query,
    )


def crawl_queries(
    queries: list[SearchQuery] | None = None,
    *,
    pages_per_query: int = 1,
    delay_seconds: float = 3.5,
    max_posts: int = 800,
    smoke: bool = False,
    merge_existing: bool = True,
) -> tuple[list[PostRaw], dict]:
    """Crawl Weibo with crawl4weibo. Returns posts + provenance."""
    try:
        from crawl4weibo import WeiboClient
        from crawl4weibo.utils.rate_limit import RateLimitConfig
    except ImportError as e:
        raise RuntimeError(
            "crawl4weibo not installed. Run: pip install crawl4weibo && playwright install chromium"
        ) from e

    qs = list(queries) if queries is not None else build_queries()
    if smoke:
        preferred = [q for q in qs if q.layer in {"place_symptom", "place_need"}]
        pool = preferred or qs
        picked: list[SearchQuery] = []
        for scope in ("road_lighting", "public_charging", "public_transit"):
            scoped = [q for q in pool if q.facility_scope == scope]
            seen_places: set[str] = set()
            for q in scoped:
                if q.place in seen_places:
                    continue
                seen_places.add(q.place)
                picked.append(q)
                if len(seen_places) >= 2:
                    break
        qs = picked or pool[:6]
        print("[crawl] smoke queries=", [q.query for q in qs])

    cookie = _load_cookie()
    # allow aggressive delay when user asks; floor ~0.6s only
    lo = max(delay_seconds * 0.7, 0.6)
    hi = max(delay_seconds * 1.1, lo + 0.2)
    rate = RateLimitConfig(base_delay=(lo, hi))
    client_kwargs: dict = {
        "rate_limit_config": rate,
        "browser_headless": True,
        "auto_fetch_cookies": cookie is None,
        "use_browser_cookies": cookie is None,
        "login_cookies": bool(cookie),
    }
    if cookie:
        client_kwargs["cookies"] = cookie

    client = WeiboClient(**client_kwargs)

    posts: list[PostRaw] = []
    seen: set[str] = set()
    errors: list[dict] = []
    per_query: list[dict] = []
    merged_from_disk = 0

    if merge_existing:
        ensure_data_dirs()
        from src.common.io import parse_models, read_jsonl

        crawl_path = RAW / "crawl_weibo_beijing.jsonl"
        if crawl_path.exists():
            try:
                existing = parse_models(read_jsonl(crawl_path), PostRaw)
                for p in existing:
                    if p.id in seen:
                        continue
                    if p.platform == "fixture":
                        continue
                    seen.add(p.id)
                    posts.append(p)
                    merged_from_disk += 1
                if merged_from_disk:
                    print(f"[crawl] merged existing posts={merged_from_disk}")
            except Exception as exc:
                print(f"[crawl] merge skip: {exc}")

    for qi, q in enumerate(qs):
        got = 0
        empty_pages = 0
        for page in range(1, pages_per_query + 1):
            if len(posts) >= max_posts:
                break
            try:
                results, meta = client.search_posts(q.query, page=page, use_proxy=False)
            except Exception as exc:
                errors.append({"query": q.query, "page": page, "error": str(exc)[:240]})
                time.sleep(delay_seconds)
                continue

            batch = results or []
            if not batch:
                empty_pages += 1
                # no more pages worth flipping for this query
                time.sleep(delay_seconds)
                break

            for post in batch:
                raw = _post_to_raw(post, q)
                if raw is None or raw.id in seen:
                    continue
                seen.add(raw.id)
                posts.append(raw)
                got += 1
                if len(posts) >= max_posts:
                    break

            time.sleep(delay_seconds)

        per_query.append(
            {
                "query": q.query,
                "facility_scope": q.facility_scope,
                "layer": q.layer,
                "kept": got,
                "empty_pages": empty_pages,
            }
        )
        if len(posts) >= max_posts:
            break
        if (qi + 1) % 10 == 0 or qi == 0:
            print(f"[crawl4weibo] {qi + 1}/{len(qs)} queries done, posts={len(posts)}")

    provenance = {
        "backend": "crawl4weibo",
        "smoke": smoke,
        "query_count": len(qs),
        "pages_per_query": pages_per_query,
        "delay_seconds": delay_seconds,
        "max_posts": max_posts,
        "raw_count": len(posts),
        "merged_existing": merged_from_disk,
        "cookie_provided": bool(cookie),
        "errors": errors[:20],
        "per_query": per_query,
        "collected_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
    }
    return posts, provenance


def persist_crawl(
    posts: list[PostRaw],
    provenance: dict,
    output_name: str = "crawl_weibo_beijing.jsonl",
) -> Path:
    ensure_data_dirs()
    out = RAW / output_name
    write_jsonl(out, dump_models(posts))
    write_json(RAW / "crawl_weibo_beijing_provenance.json", provenance)
    return out
