#!/usr/bin/env python
"""Crawl real Beijing Weibo posts via crawl4weibo.

OWNER: AGENT_LAB1

Usage:
  python scripts/run_weibo_crawl.py --smoke
  python scripts/run_weibo_crawl.py --pages 1 --max-posts 600 --delay 3.5
  python scripts/run_weibo_crawl.py --run-lab1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab1_collection.collector import run_lab1
from src.lab1_collection.crawler import crawl_queries, persist_crawl
from src.lab1_collection.queries import build_queries
from src.lab1_collection.sources import CollectionError


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab1 real Weibo crawl (crawl4weibo)")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="only 5 narrow queries for first validation",
    )
    parser.add_argument("--pages", type=int, default=2, help="pages per query")
    parser.add_argument("--delay", type=float, default=1.2, help="extra delay seconds between requests")
    parser.add_argument("--max-posts", type=int, default=1500, help="stop after N unique posts (incl. merged)")
    parser.add_argument("--max-per-scope", type=int, default=100, help="cap taxonomy queries per facility")
    parser.add_argument("--run-lab1", action="store_true", help="run cleaner after crawl")
    parser.add_argument("--no-merge", action="store_true", help="do not merge existing crawl jsonl")
    args = parser.parse_args()

    queries = build_queries(max_per_scope=args.max_per_scope)
    print(f"[crawl] backend=crawl4weibo queries={len(queries)} smoke={args.smoke}")
    print(f"[crawl] sample={ [q.query for q in queries[:5]] }")
    print(f"[crawl] pages={args.pages} delay={args.delay} max_posts={args.max_posts}")

    try:
        posts, provenance = crawl_queries(
            queries=queries,
            pages_per_query=max(1, args.pages),
            delay_seconds=max(0.6, args.delay),
            max_posts=max(1, args.max_posts),
            smoke=args.smoke,
            merge_existing=not args.no_merge,
        )
    except Exception as e:
        print(f"[crawl] failed: {e}", file=sys.stderr)
        raise SystemExit(2) from e

    if not posts:
        print(
            "[crawl] 0 posts. Tips: check network; optionally set secrets/weibo_cookie.txt; "
            "try --smoke first; see provenance errors.",
            file=sys.stderr,
        )
        print(f"[crawl] provenance_errors={provenance.get('errors')}", file=sys.stderr)
        raise SystemExit(3)

    out = persist_crawl(posts, provenance)
    print(f"[crawl] wrote {out} count={len(posts)}")
    print(
        f"[crawl] cookie_provided={provenance.get('cookie_provided')} "
        f"errors={len(provenance.get('errors') or [])}"
    )

    if args.run_lab1:
        try:
            cleaned = run_lab1(source="raw")
            print(f"[lab1] wrote {cleaned}")
        except CollectionError as e:
            print(str(e), file=sys.stderr)
            raise SystemExit(2) from e


if __name__ == "__main__":
    main()
