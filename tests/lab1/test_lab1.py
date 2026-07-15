from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.lab1_collection.cleaner import clean_posts, fingerprint, normalize_text
from src.lab1_collection.collector import run_lab1
from src.lab1_collection.geo import infer_district
from src.lab1_collection.queries import build_queries
from src.lab1_collection.sources import collect_raw_posts
from src.common.models import PostRaw
from src.common.paths import CLEANED, SAMPLE_RAW


def test_queries_cover_three_scopes():
    qs = build_queries()
    scopes = {q.facility_scope for q in qs}
    assert scopes == {"road_lighting", "public_charging", "public_transit"}
    assert len(qs) >= 30


def test_normalize_and_fingerprint_near_dup():
    a = normalize_text("望京路灯坏了!!! https://example.com")
    b = normalize_text("望京路灯坏了")
    assert "http" not in a
    assert fingerprint(a) == fingerprint(b)


def test_infer_district_landmark():
    d, conf, matched = infer_district("西二旗地铁口路灯坏了")
    assert d == "海淀区"
    assert conf >= 0.6
    assert matched == "西二旗"


def test_clean_drops_noise_and_dupes():
    posts = [
        PostRaw(id="1", platform="fixture", text="今天天气不错去逛街", time="2026-07-01T12:00:00+08:00", city="北京"),
        PostRaw(id="2", platform="fixture", text="望京路灯坏了晚上太黑", time="2026-07-01T12:00:00+08:00", city="北京", facility_scope_hint="road_lighting"),
        PostRaw(id="3", platform="fixture", text="望京路灯坏了晚上太黑!!!", time="2026-07-01T13:00:00+08:00", city="北京", facility_scope_hint="road_lighting"),
        PostRaw(id="4", platform="fixture", text="短", time="2026-07-01T13:00:00+08:00", city="北京"),
    ]
    cleaned = clean_posts(posts)
    kept = [c for c in cleaned if not c.meta.dropped]
    assert len(kept) == 1
    reasons = {c.meta.drop_reason for c in cleaned if c.meta.dropped}
    assert "out_of_scope" in reasons
    assert "duplicate" in reasons
    assert "too_short" in reasons


def test_run_lab1_fixture_mode_offline():
    assert SAMPLE_RAW.exists()
    out = run_lab1(source="fixture")
    path = Path(out)
    assert path.exists()
    rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) >= 20
    scopes = {r["meta"]["facility_scope_hint"] for r in rows}
    assert {"road_lighting", "public_charging", "public_transit"} <= scopes
    report = json.loads((CLEANED / "lab1_cleaning_report.json").read_text(encoding="utf-8"))
    assert report["dropped_count"] >= 1
    assert report["kept_by_scope"]["road_lighting"] >= 1


def test_collect_raw_fixture_provenance():
    posts, prov = collect_raw_posts("fixture")
    assert len(posts) >= 20
    assert prov["source_used"]
    assert prov["query_count"] >= 30
