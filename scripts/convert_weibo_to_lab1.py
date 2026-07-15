#!/usr/bin/env python
"""Run Lab1 clean over existing data/raw/crawl_*.jsonl or import_*.jsonl.

OWNER: AGENT_LAB1

Legacy name kept for teammates. Scrapy CSV conversion is removed —
use crawl4weibo via scripts/run_weibo_crawl.py instead.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab1_collection.collector import run_lab1
from src.lab1_collection.sources import CollectionError


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--run-lab1",
        action="store_true",
        default=True,
        help="run Lab1 on existing crawl_/import_ jsonl (default: true)",
    )
    args = parser.parse_args()
    if not args.run_lab1:
        raise SystemExit("Nothing to do. Use scripts/run_weibo_crawl.py to crawl.")
    try:
        cleaned = run_lab1(source="raw")
    except CollectionError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e
    print(f"[lab1] wrote {cleaned}")


if __name__ == "__main__":
    main()
