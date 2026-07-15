from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.lab1_collection.cleaner import clean_posts, fingerprint, normalize_text
from src.lab1_collection.collector import run_lab1
from src.lab1_collection.geo import infer_district
from src.lab1_collection.queries import build_queries
from src.lab1_collection.sources import CollectionError, collect_raw_posts
from src.common.models import PostRaw


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
    # Synthetic strings for UNIT tests only — not project dataset.
    posts = [
        PostRaw(id="1", platform="other", text="今天天气不错去逛街", time="2026-07-01T12:00:00+08:00", city="北京"),
        PostRaw(
            id="2",
            platform="other",
            text="望京路灯坏了晚上太黑",
            time="2026-07-01T12:00:00+08:00",
            city="北京",
            facility_scope_hint="road_lighting",
        ),
        PostRaw(
            id="3",
            platform="other",
            text="望京路灯坏了晚上太黑!!!",
            time="2026-07-01T13:00:00+08:00",
            city="北京",
            facility_scope_hint="road_lighting",
        ),
        PostRaw(id="4", platform="other", text="短", time="2026-07-01T13:00:00+08:00", city="北京"),
    ]
    cleaned = clean_posts(posts)
    kept = [c for c in cleaned if not c.meta.dropped]
    assert len(kept) == 1
    reasons = {c.meta.drop_reason for c in cleaned if c.meta.dropped}
    assert "out_of_scope" in reasons
    assert "duplicate" in reasons
    assert "too_short" in reasons


def test_lab1_refuses_without_real_data():
    with pytest.raises(CollectionError):
        run_lab1(source="auto")
    with pytest.raises(CollectionError):
        collect_raw_posts("auto")
