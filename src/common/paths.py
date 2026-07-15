"""Path helpers. OWNER: shared/common. Do not hardcode paths elsewhere."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CONFIGS = ROOT / "configs"
SCHEMAS = ROOT / "schemas"
FIXTURES = ROOT / "fixtures"
DATA = ROOT / "data"
RAW = DATA / "raw"
CLEANED = DATA / "cleaned"
ANALYZED = DATA / "analyzed"
REPORTS = DATA / "reports"

SAMPLE_RAW = FIXTURES / "sample_raw" / "beijing_sample_posts.jsonl"
KEYWORDS = CONFIGS / "keywords_taxonomy.yaml"
NEED_MAPPING = CONFIGS / "need_mapping.yaml"
CITY = CONFIGS / "city_beijing.yaml"


def ensure_data_dirs() -> None:
    for p in (RAW, CLEANED, ANALYZED, REPORTS):
        p.mkdir(parents=True, exist_ok=True)
