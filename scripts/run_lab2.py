#!/usr/bin/env python
"""Run Lab2 only. OWNER: AGENT_LAB2. Requires Lab1 real cleaned output."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.paths import ANALYZED, CLEANED
from src.lab2_analysis.analyzer import run_lab2


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab2 intent/emotion/NER/need mapping (REAL DATA)")
    parser.add_argument("--input", default="beijing_cleaned.jsonl")
    parser.add_argument("--output", default="beijing_analyzed.jsonl")
    args = parser.parse_args()

    in_path = CLEANED / args.input
    if not in_path.exists():
        print(
            f"Missing real Lab1 input: {in_path}\n"
            "Pull latest main or ask Lab1 for data/cleaned/beijing_cleaned.jsonl",
            file=sys.stderr,
        )
        raise SystemExit(2)

    out = run_lab2(input_name=args.input, output_name=args.output)
    report_path = ANALYZED / "lab2_analysis_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
    print(f"[lab2] wrote {out}")
    print(
        f"[lab2] mapped={report.get('mapped_count')}/{report.get('input_count')} "
        f"ratio={report.get('mapped_ratio')} "
        f"rule_hits={report.get('rule_hit_count')} "
        f"fallback={report.get('scope_fallback_count')} "
        f"unmapped={report.get('unmapped_count')}"
    )
    print(f"[lab2] intents={report.get('intent_counts')}")
    print(f"[lab2] needs={report.get('need_counts')}")
    print(f"[lab2] by_scope={json.dumps(report.get('by_scope'), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
