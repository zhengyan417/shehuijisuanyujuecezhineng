#!/usr/bin/env python
"""Re-clean existing crawl jsonl with mechanical + NVIDIA LLM gate.

OWNER: AGENT_LAB1

Usage:
  python scripts/run_lab1_llm_filter.py
  python scripts/run_lab1_llm_filter.py --model nvidia/nemotron-mini-4b-instruct --workers 8 --batch-size 10
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.paths import CLEANED
from src.lab1_collection.collector import run_lab1
from src.lab1_collection.sources import CollectionError


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab1 LLM semantic filter over real crawl jsonl")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument(
        "--model",
        default="nvidia/nemotron-mini-4b-instruct",
        help="NVIDIA integrate.api model id",
    )
    parser.add_argument("--source", choices=["auto", "raw"], default="raw")
    args = parser.parse_args()

    try:
        out = run_lab1(
            source=args.source,
            llm_filter=True,
            llm_workers=max(1, args.workers),
            llm_batch_size=max(1, args.batch_size),
            llm_model=args.model,
        )
    except CollectionError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e

    report = CLEANED / "lab1_cleaning_report.json"
    if report.exists():
        print(json.dumps(json.loads(report.read_text(encoding="utf-8")), ensure_ascii=False, indent=2))
    print(f"[lab1-llm] wrote {out}")


if __name__ == "__main__":
    main()
