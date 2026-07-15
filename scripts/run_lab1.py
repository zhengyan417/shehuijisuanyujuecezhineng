#!/usr/bin/env python
"""Run Lab1 only. OWNER: AGENT_LAB1."""
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab1 collect + clean for Beijing silent demand")
    parser.add_argument(
        "--source",
        choices=["auto", "fixture", "raw", "crawl"],
        default="auto",
        help="data source mode (default auto: raw if present else fixture fallback)",
    )
    parser.add_argument(
        "--output",
        default="beijing_cleaned.jsonl",
        help="output filename under data/cleaned/",
    )
    args = parser.parse_args()

    out = run_lab1(output_name=args.output, source=args.source)
    report_path = CLEANED / "lab1_cleaning_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    coverage = keyword_coverage_report()
    print(f"[lab1] wrote {out}")
    print(f"[lab1] kept={report.get('kept_count')} dropped={report.get('dropped_count')} scopes={report.get('kept_by_scope')}")
    print(f"[lab1] taxonomy scopes={coverage.get('scopes')} queries={coverage.get('query_count')}")


if __name__ == "__main__":
    main()
