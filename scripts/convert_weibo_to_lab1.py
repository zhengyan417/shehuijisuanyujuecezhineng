#!/usr/bin/env python
"""Convert weibo-search CSV results -> data/raw/crawl_weibo_beijing.jsonl then optionally run Lab1."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab1_collection.collector import run_lab1
from src.lab1_collection.weibo_adapter import RESULT_ROOT, convert_weibo_csvs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-lab1", action="store_true", help="after convert, run Lab1 --source raw")
    args = parser.parse_args()

    if not RESULT_ROOT.exists():
        raise SystemExit(
            f"No crawler output at {RESULT_ROOT}. Run: python scripts/run_weibo_crawl.py first."
        )
    out = convert_weibo_csvs()
    print(f"[convert] wrote {out}")
    if args.run_lab1:
        cleaned = run_lab1(source="raw")
        print(f"[lab1] wrote {cleaned}")


if __name__ == "__main__":
    main()
