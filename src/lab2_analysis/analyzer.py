"""Lab2 orchestration — intent/emotion/NER/need-mapping over cleaned posts.

OWNER: AGENT_LAB2
READS: data/cleaned/*.jsonl, configs/need_mapping.yaml
WRITES: data/analyzed/*.jsonl
MUST NOT EDIT: src/lab1_collection/**, src/lab3_decision/**, configs/keywords_taxonomy.yaml
"""

from __future__ import annotations

from collections import Counter

from src.common.io import dump_models, load_yaml, parse_models, read_jsonl, write_json, write_jsonl
from src.common.models import Lab2Meta, PostAnalyzed, PostCleaned
from src.common.paths import ANALYZED, CLEANED, NEED_MAPPING, ensure_data_dirs
from src.lab2_analysis.emotion import classify_emotion
from src.lab2_analysis.intent import classify_intent
from src.lab2_analysis.mapper import map_need
from src.lab2_analysis.ner import extract_entities, infer_scope_from_entities
from src.lab2_analysis.urgency import score_urgency

LAB2_VERSION = "lab2-0.2.0"


def analyze_posts(posts: list[PostCleaned]) -> list[PostAnalyzed]:
    mapping_cfg = load_yaml(NEED_MAPPING)
    out: list[PostAnalyzed] = []
    for p in posts:
        entities = extract_entities(p.clean_text)
        scope = infer_scope_from_entities(entities, p.meta.facility_scope_hint)
        mapped, rule_intent, rule_emotion = map_need(p.clean_text, mapping_cfg, scope)
        intent = classify_intent(p.clean_text, mapping_cfg, rule_intent)
        emotion = classify_emotion(p.clean_text, intent, mapping_cfg, rule_emotion)
        urgency = score_urgency(emotion, intent, p.clean_text)
        out.append(
            PostAnalyzed(
                id=p.id,
                platform=p.platform,
                text=p.text,
                clean_text=p.clean_text,
                time=p.time,
                city="北京",
                geo=p.geo,
                intent=intent,
                emotion=emotion,
                entities=entities,
                mapped_need=mapped,
                urgency_score=urgency,
                meta=Lab2Meta(
                    lab1_version=p.meta.lab1_version,
                    lab2_version=LAB2_VERSION,
                    facility_scope_hint=scope or p.meta.facility_scope_hint,
                ),
            )
        )
    return out


def _stats(analyzed: list[PostAnalyzed]) -> dict:
    mapped = [a for a in analyzed if a.mapped_need.need_id]
    return {
        "lab2_version": LAB2_VERSION,
        "input_count": len(analyzed),
        "mapped_count": len(mapped),
        "mapped_ratio": round(len(mapped) / max(len(analyzed), 1), 3),
        "intent_counts": dict(Counter(a.intent for a in analyzed)),
        "emotion_counts": dict(Counter(a.emotion for a in analyzed)),
        "need_counts": dict(Counter(a.mapped_need.need_id for a in mapped)),
        "avg_urgency": round(sum(a.urgency_score for a in analyzed) / max(len(analyzed), 1), 3),
        "mapping_config_version": load_yaml(NEED_MAPPING).get("version"),
    }


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
    write_json(ANALYZED / "lab2_analysis_report.json", _stats(analyzed))
    return str(out_path)
