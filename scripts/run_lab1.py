#!/usr/bin/env python
"""Run Lab1 only. OWNER: AGENT_LAB1.

Requires REAL data (crawl_* / import_*). Fake fixture data is banned.
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
from src.lab1_collection.collector import keyword_coverage_report, run_lab1
from src.lab1_collection.sources import CollectionError


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab1 collect + clean (REAL DATA ONLY)")
    parser.add_argument(
        "--source",
        choices=["auto", "raw", "crawl"],
        default="auto",
        help="auto|raw|crawl — never uses fixture/fake posts",
    )
    parser.add_argument(
        "--output",
        default="beijing_cleaned.jsonl",
        help="output filename under data/cleaned/",
    )
    args = parser.parse_args()

    try:
        out = run_lab1(output_name=args.output, source=args.source)
    except CollectionError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e

    report_path = CLEANED / "lab1_cleaning_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    coverage = keyword_coverage_report()
    print(f"[lab1] wrote {out}")
    print(
        f"[lab1] kept={report.get('kept_count')} dropped={report.get('dropped_count')} "
        f"scopes={report.get('kept_by_scope')}"
    )
    print(f"[lab1] taxonomy scopes={coverage.get('scopes')} queries={coverage.get('query_count')}")


if __name__ == "__main__":
    main()
