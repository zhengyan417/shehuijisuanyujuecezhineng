from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline import run_all
from src.common.paths import CLEANED, ANALYZED, REPORTS


def test_pipeline_produces_artifacts():
    result = run_all()
    assert Path(result["cleaned"]).exists()
    assert Path(result["analyzed"]).exists()
    assert Path(result["report"]).exists()
    assert (CLEANED / "beijing_cleaned.jsonl").exists()
    assert (ANALYZED / "beijing_analyzed.jsonl").exists()
    assert (REPORTS / "beijing_silent_demand.md").exists()
