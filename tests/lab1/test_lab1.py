from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common.models import PostRaw
from src.lab1_collection.cleaner import clean_posts, fingerprint, normalize_text
from src.lab1_collection.geo import infer_district
from src.lab1_collection.queries import build_queries
from src.lab1_collection.sources import CollectionError, collect_raw_posts


def test_queries_are_compact_place_first():
    qs = build_queries(max_per_scope=40)
    scopes = {q.facility_scope for q in qs}
    assert scopes == {"road_lighting", "public_charging", "public_transit"}
    assert len(qs) >= 60
    place_qs = [q for q in qs if q.layer.startswith("place")]
    assert place_qs
    for q in place_qs:
        assert " " not in q.query
        assert q.place and q.place != "北京"
    assert not any(q.query == "北京" for q in qs)


def test_normalize_and_fingerprint_near_dup():
    a = normalize_text("望京路灯坏了!!! https://example.com")
    b = normalize_text("望京路灯坏了")
    assert "http" not in a
    assert fingerprint(a) == fingerprint(b)


def test_infer_district_prefers_poi_over_text():
    # text looks Qingdao-ish street name but structured poi is Beijing 望京
    d, conf, matched = infer_district(
        "合肥路劲松一路路口红路灯不亮",
        poi="望京",
        geo_raw=None,
    )
    assert d == "朝阳区"
    assert matched == "望京"
    assert conf >= 0.85


def test_infer_district_text_fallback():
    d, conf, matched = infer_district("西二旗地铁口路灯坏了")
    assert d == "海淀区"
    assert matched == "西二旗"


def test_mechanical_clean_only_short_and_dup():
    # Keyword blacklists removed — literary text is NOT dropped here (LLM stage does that).
    posts = [
        PostRaw(
            id="lit",
            platform="weibo",
            text="糖饼里的月光北京的暮色，路灯次第亮起，暖光落进来往的车流。",
            time="2026-07-01T12:00:00+08:00",
            city="北京",
            facility_scope_hint="road_lighting",
            source_query="北京路灯不亮",
        ),
        PostRaw(
            id="ok",
            platform="weibo",
            text="望京这边晚上路灯坏了好多，走路好害怕，能不能快点修",
            time="2026-07-01T12:00:00+08:00",
            city="北京",
            facility_scope_hint="road_lighting",
            source_query="望京路灯坏了",
        ),
        PostRaw(
            id="dup",
            platform="weibo",
            text="望京这边晚上路灯坏了好多，走路好害怕，能不能快点修!!!",
            time="2026-07-01T13:00:00+08:00",
            city="北京",
            facility_scope_hint="road_lighting",
            source_query="望京路灯坏了",
        ),
        PostRaw(id="short", platform="weibo", text="短", time="2026-07-01T13:00:00+08:00", city="北京"),
    ]
    cleaned = clean_posts(posts)
    by_id = {c.id: c for c in cleaned}
    assert by_id["lit"].meta.dropped is False  # LLM will decide later
    assert by_id["ok"].meta.dropped is False
    assert by_id["dup"].meta.drop_reason == "duplicate"
    assert by_id["short"].meta.drop_reason == "too_short"


def test_lab1_refuses_without_real_data(tmp_path, monkeypatch):
    from src.lab1_collection import sources as sources_mod
    from src.common import paths as paths_mod

    monkeypatch.setattr(paths_mod, "RAW", tmp_path)
    monkeypatch.setattr(sources_mod, "RAW", tmp_path)
    with pytest.raises(CollectionError):
        collect_raw_posts("auto")
