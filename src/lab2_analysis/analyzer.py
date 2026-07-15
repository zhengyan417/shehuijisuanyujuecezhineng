"""Lab2 — intent/emotion/NER/need-mapping over cleaned posts.

OWNER: AGENT_LAB2
READS: data/cleaned/*.jsonl, configs/need_mapping.yaml
WRITES: data/analyzed/*.jsonl
MUST NOT EDIT: src/lab1_collection/**, src/lab3_decision/**, configs/keywords_taxonomy.yaml
"""

from __future__ import annotations

from src.common.io import dump_models, load_yaml, parse_models, read_jsonl, write_jsonl
from src.common.models import (
    Entities,
    Lab2Meta,
    MappedNeed,
    PostAnalyzed,
    PostCleaned,
)
from src.common.paths import ANALYZED, CLEANED, NEED_MAPPING, ensure_data_dirs

LAB2_VERSION = "lab2-stub-0.1.0"

FACILITY_LEXICON = {
    "road_lighting": ["路灯", "照明", "太黑", "黑漆漆"],
    "public_charging": ["充电桩", "充电站", "充电", "快充", "慢充"],
    "public_transit": ["公交站", "候车亭", "天桥", "过街", "站台"],
}

LOCATION_LEXICON = [
    "望京",
    "中关村",
    "五道口",
    "回龙观",
    "天通苑",
    "通州",
    "亦庄",
    "国贸",
    "西单",
    "清河",
    "朝阳",
    "海淀",
    "昌平",
    "大兴",
]


def _extract_entities(text: str) -> Entities:
    facilities: list[str] = []
    for scope, words in FACILITY_LEXICON.items():
        for w in words:
            if w in text and w not in facilities:
                facilities.append(w)
    locations = [w for w in LOCATION_LEXICON if w in text]
    return Entities(facility=facilities, location=locations)


def _map_need(text: str, mapping_cfg: dict) -> MappedNeed:
    catalog = {n["id"]: n for n in mapping_cfg.get("needs_catalog", [])}
    for rule in mapping_cfg.get("mapping_rules", []):
        keys = rule.get("if_any_keywords", [])
        if any(k in text for k in keys):
            need = catalog.get(rule["need_id"], {})
            return MappedNeed(
                need_id=rule.get("need_id"),
                need_name_zh=need.get("name_zh"),
                facility_scope=need.get("facility_scope"),
                rule_id=rule.get("id"),
            )
    return MappedNeed()


def _infer_intent_emotion(text: str, mapping_cfg: dict) -> tuple[str, str]:
    for rule in mapping_cfg.get("mapping_rules", []):
        keys = rule.get("if_any_keywords", [])
        if any(k in text for k in keys):
            return rule.get("default_intent", "其他"), rule.get("default_emotion", "中性")
    if any(x in text for x in ["能不能", "希望", "要是能", "建议"]):
        return "建议", "期待"
    if any(x in text for x in ["哪有", "哪里", "有没有"]):
        return "询问", "中性"
    if any(x in text for x in ["太", "坏了", "烦", "不满", "危险"]):
        return "抱怨", "不满"
    return "其他", "中性"


def _urgency(emotion: str, intent: str) -> float:
    base = {"焦虑": 0.85, "不满": 0.7, "期待": 0.55, "中性": 0.35}.get(emotion, 0.4)
    if intent == "抱怨":
        base += 0.1
    if intent == "建议":
        base += 0.05
    return round(min(base, 1.0), 3)


def analyze_posts(posts: list[PostCleaned]) -> list[PostAnalyzed]:
    mapping_cfg = load_yaml(NEED_MAPPING)
    out: list[PostAnalyzed] = []
    for p in posts:
        intent, emotion = _infer_intent_emotion(p.clean_text, mapping_cfg)
        mapped = _map_need(p.clean_text, mapping_cfg)
        entities = _extract_entities(p.clean_text)
        out.append(
            PostAnalyzed(
                id=p.id,
                platform=p.platform,
                text=p.text,
                clean_text=p.clean_text,
                time=p.time,
                city="北京",
                geo=p.geo,
                intent=intent,  # type: ignore[arg-type]
                emotion=emotion,  # type: ignore[arg-type]
                entities=entities,
                mapped_need=mapped,
                urgency_score=_urgency(emotion, intent),
                meta=Lab2Meta(
                    lab1_version=p.meta.lab1_version,
                    lab2_version=LAB2_VERSION,
                    facility_scope_hint=p.meta.facility_scope_hint,
                ),
            )
        )
    return out


def run_lab2(
    input_name: str = "beijing_cleaned.jsonl",
    output_name: str = "beijing_analyzed.jsonl",
) -> str:
    ensure_data_dirs()
    in_path = CLEANED / input_name
    if not in_path.exists():
        raise FileNotFoundError(f"Lab2 requires cleaned input missing: {in_path}. Run Lab1 first.")
    posts = parse_models(read_jsonl(in_path), PostCleaned)
    analyzed = analyze_posts(posts)
    out_path = ANALYZED / output_name
    write_jsonl(out_path, dump_models(analyzed))
    return str(out_path)
