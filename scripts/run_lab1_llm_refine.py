#!/usr/bin/env python
"""Second-pass LLM refine on currently kept cleaned posts.

Uses a slightly better/fast model (default: meta/llama-3.1-8b-instruct)
with tightened ABCD prompt (办结优先DROP、外地劲松消歧、is_mediated).

OWNER: AGENT_LAB1
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.io import dump_models, parse_models, read_jsonl, write_json, write_jsonl
from src.common.models import PostCleaned
from src.common.paths import CLEANED, ensure_data_dirs
from src.lab1_collection.cleaner import LAB1_VERSION
from src.lab1_collection.llm_filter import REFINE_MODEL, refine_kept


def main() -> None:
    parser = argparse.ArgumentParser(description="Refine kept Lab1 posts with better LLM pass")
    parser.add_argument("--model", default=REFINE_MODEL)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument(
        "--input",
        default="beijing_cleaned_with_drops.jsonl",
        help="under data/cleaned/",
    )
    args = parser.parse_args()

    ensure_data_dirs()
    inp = CLEANED / args.input
    if not inp.exists():
        # fallback: rebuild from kept+assume no drops file
        kept_path = CLEANED / "beijing_cleaned.jsonl"
        if not kept_path.exists():
            raise SystemExit(f"missing {inp} and {kept_path}")
        rows = parse_models(read_jsonl(kept_path), PostCleaned)
    else:
        rows = parse_models(read_jsonl(inp), PostCleaned)

    before_kept = sum(1 for r in rows if not r.meta.dropped)
    print(f"[refine] before_kept={before_kept} model={args.model}", flush=True)

    # bump version marker for this pass
    for r in rows:
        r.meta.lab1_version = LAB1_VERSION

    refined = refine_kept(
        rows,
        model=args.model,
        workers=max(1, args.workers),
        batch_size=max(1, args.batch_size),
    )

    kept = [c for c in refined if not c.meta.dropped]
    write_jsonl(CLEANED / "beijing_cleaned.jsonl", dump_models(kept))
    write_jsonl(CLEANED / "beijing_cleaned_with_drops.jsonl", dump_models(refined))

    by_scope = Counter(c.meta.facility_scope_hint for c in kept if c.meta.facility_scope_hint)
    mediated = sum(1 for c in kept if c.meta.is_mediated)
    drop_reasons = Counter(c.meta.drop_reason for c in refined if c.meta.dropped)
    report = {
        "lab1_version": LAB1_VERSION,
        "pass": "llm_refine",
        "model": args.model,
        "input_count": len(refined),
        "before_kept": before_kept,
        "kept_count": len(kept),
        "dropped_count": len(refined) - len(kept),
        "kept_by_scope": dict(by_scope),
        "kept_mediated": mediated,
        "drop_reasons": dict(drop_reasons),
    }
    write_json(CLEANED / "lab1_cleaning_report.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[refine] wrote kept={len(kept)} mediated={mediated}")


if __name__ == "__main__":
    main()
