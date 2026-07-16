from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.common.io import load_yaml
from src.common.models import GeoInfo, Lab1Meta, PostCleaned
from src.common.paths import ANALYZED, CLEANED, NEED_MAPPING
from src.lab2_analysis.analyzer import analyze_posts, run_lab2
from src.lab2_analysis.emotion import classify_emotion
from src.lab2_analysis.intent import classify_intent
from src.lab2_analysis.mapper import map_need
from src.lab2_analysis.ner import extract_entities


def _post(text: str, scope: str | None = None, mediated: bool = False) -> PostCleaned:
    # Synthetic unit-test rows only — NOT a substitute for crawled Weibo data.
    return PostCleaned(
        id="t1",
        platform="other",
        text=text,
        clean_text=text,
        time="2026-07-01T12:00:00+08:00",
        city="北京",
        geo=GeoInfo(district="海淀区", confidence=0.8),
        meta=Lab1Meta(
            lab1_version="test",
            facility_scope_hint=scope,  # type: ignore[arg-type]
            is_mediated=mediated,
        ),
    )


def test_intent_priority_inquiry_over_complaint():
    cfg = load_yaml(NEED_MAPPING)
    assert classify_intent("请问望京哪里有充电桩", cfg) == "询问"
    assert classify_intent("希望多装点充电桩", cfg) == "建议"
    assert classify_intent("充电桩坏了没人管真无语", cfg) == "抱怨"
    assert classify_intent("望京区域路灯都不亮啊", cfg) == "抱怨"


def test_emotion_anxiety_for_dark_road():
    cfg = load_yaml(NEED_MAPPING)
    intent = classify_intent("晚上黑漆漆不敢走", cfg)
    emo = classify_emotion("晚上黑漆漆不敢走", intent, cfg)
    assert emo == "焦虑"


def test_need_mapping_occupancy_and_overpass():
    cfg = load_yaml(NEED_MAPPING)
    m1, _, _ = map_need("燃油车占着充电位不走", cfg, "public_charging", True)
    assert m1.need_id == "charging_occupancy_governance"
    m2, _, _ = map_need("西单过马路太危险，能不能修个天桥", cfg, "public_transit", True)
    assert m2.need_id == "pedestrian_crossing_safety"
    m3, _, _ = map_need("进入望京区域路灯都不亮啊", cfg, "road_lighting", True)
    assert m3.need_id == "lighting_repair"


def test_no_false_need_without_facility_evidence():
    cfg = load_yaml(NEED_MAPPING)
    # birthday / off-topic with lighting scope hint but no facility evidence
    m, _, _ = map_need(
        "亲爱的宝贝生日快乐，今天是你的生日也是我陪你的第705天",
        cfg,
        "road_lighting",
        has_facility_entity=False,
    )
    assert m.need_id is None


def test_ner_extracts_facility_and_location():
    ents = extract_entities("望京SOHO附近路灯坏了")
    assert "路灯" in ents.facility
    assert any("望京" in x for x in ents.location)


def test_analyze_posts_maps_majority_on_unit_strings():
    posts = [
        _post("望京路灯坏了好多晚上太黑", "road_lighting"),
        _post("中关村找不到充电桩，要是有充电桩就好了", "public_charging"),
        _post("国贸公交站没遮雨候车亭坏了", "public_transit"),
        _post("请问通州哪里有充电桩", "public_charging"),
        _post("劳斯莱斯赖在充电桩车位上不走", "public_charging"),
    ]
    out = analyze_posts(posts)
    assert len(out) == 5
    assert sum(1 for x in out if x.mapped_need.need_id) >= 4
    assert all(0.0 <= x.urgency_score <= 1.0 for x in out)
    assert out[-1].mapped_need.need_id == "charging_occupancy_governance"


def test_run_lab2_on_real_cleaned_data():
    cleaned = CLEANED / "beijing_cleaned.jsonl"
    assert cleaned.exists(), "Lab1 real cleaned data required"
    out = Path(run_lab2())
    assert out.exists()
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) >= 1000
    mapped = [r for r in rows if r["mapped_need"]["need_id"]]
    ratio = len(mapped) / len(rows)
    assert 0.35 <= ratio <= 0.95
    # residual noise should NOT all become needs
    assert any(r["mapped_need"]["need_id"] is None for r in rows)
    report = json.loads((ANALYZED / "lab2_analysis_report.json").read_text(encoding="utf-8"))
    assert report["mapped_count"] == len(mapped)
    assert report["lab2_version"].startswith("lab2-")
    # intents valid
    assert set(report["intent_counts"]) <= {"抱怨", "建议", "询问", "其他"}
    # pass-through field present
    assert "is_mediated" in rows[0]["meta"]
