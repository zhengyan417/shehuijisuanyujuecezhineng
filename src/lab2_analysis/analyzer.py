"""Lab2 orchestration — intent/emotion/NER/need-mapping over cleaned posts.

OWNER: AGENT_LAB2
READS: data/cleaned/*.jsonl, configs/need_mapping.yaml
WRITES: data/analyzed/*.jsonl
MUST NOT EDIT: src/lab1_collection/**, src/lab3_decision/**, configs/keywords_taxonomy.yaml
"""

from __future__ import annotations

from collections import Counter, defaultdict

from src.common.io import dump_models, load_yaml, parse_models, read_jsonl, write_json, write_jsonl
from src.common.models import Lab2Meta, PostAnalyzed, PostCleaned
from src.common.paths import ANALYZED, CLEANED, NEED_MAPPING, ensure_data_dirs
from src.lab2_analysis.emotion import classify_emotion
from src.lab2_analysis.intent import classify_intent
from src.lab2_analysis.mapper import map_need
from src.lab2_analysis.ner import extract_entities, infer_scope_from_entities
from src.lab2_analysis.urgency import score_urgency

LAB2_VERSION = "lab2-0.3.0"


def analyze_posts(posts: list[PostCleaned]) -> list[PostAnalyzed]:
    mapping_cfg = load_yaml(NEED_MAPPING)
    out: list[PostAnalyzed] = []
    for p in posts:
        text = p.clean_text or p.text
        entities = extract_entities(text)
        scope = infer_scope_from_entities(entities, p.meta.facility_scope_hint, text)
        mapped, rule_intent, rule_emotion = map_need(
            text,
            mapping_cfg,
            scope,
            has_facility_entity=bool(entities.facility),
        )
        intent = classify_intent(text, mapping_cfg, rule_intent)
        emotion = classify_emotion(text, intent, mapping_cfg, rule_emotion)
        urgency = score_urgency(
            emotion,
            intent,
            text,
            is_mediated=bool(p.meta.is_mediated),
            has_need=bool(mapped.need_id),
        )
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
                    is_mediated=bool(p.meta.is_mediated),
                ),
            )
        )
    return out


def _stats(analyzed: list[PostAnalyzed]) -> dict:
    mapped = [a for a in analyzed if a.mapped_need.need_id]
    by_scope: dict[str, dict] = {}
    scope_groups: dict[str, list[PostAnalyzed]] = defaultdict(list)
    for a in analyzed:
        scope_groups[a.meta.facility_scope_hint or "unknown"].append(a)
    for scope, items in scope_groups.items():
        m = [x for x in items if x.mapped_need.need_id]
        by_scope[scope] = {
            "n": len(items),
            "mapped": len(m),
            "mapped_ratio": round(len(m) / max(len(items), 1), 3),
            "intent_counts": dict(Counter(x.intent for x in items)),
            "need_counts": dict(Counter(x.mapped_need.need_id for x in m)),
            "avg_urgency": round(sum(x.urgency_score for x in items) / max(len(items), 1), 3),
        }

    rule_ids = Counter(a.mapped_need.rule_id for a in mapped)
    return {
        "lab2_version": LAB2_VERSION,
        "input_count": len(analyzed),
        "mapped_count": len(mapped),
        "unmapped_count": len(analyzed) - len(mapped),
        "mapped_ratio": round(len(mapped) / max(len(analyzed), 1), 3),
        "rule_hit_count": sum(1 for a in mapped if a.mapped_need.rule_id not in {None, "SCOPE_FALLBACK"}),
        "scope_fallback_count": rule_ids.get("SCOPE_FALLBACK", 0),
        "intent_counts": dict(Counter(a.intent for a in analyzed)),
        "emotion_counts": dict(Counter(a.emotion for a in analyzed)),
        "need_counts": dict(Counter(a.mapped_need.need_id for a in mapped)),
        "rule_id_counts": dict(rule_ids),
        "mediated_count": sum(1 for a in analyzed if a.meta.is_mediated),
        "with_facility_entity": sum(1 for a in analyzed if a.entities.facility),
        "with_location_entity": sum(1 for a in analyzed if a.entities.location),
        "avg_urgency": round(sum(a.urgency_score for a in analyzed) / max(len(analyzed), 1), 3),
        "avg_urgency_mapped": round(sum(a.urgency_score for a in mapped) / max(len(mapped), 1), 3)
        if mapped
        else 0.0,
        "by_scope": by_scope,
        "mapping_config_version": load_yaml(NEED_MAPPING).get("version"),
        "notes": (
            "public_transit n is small in upstream Lab1 kept set; avoid over-claiming transit conclusions. "
            "Unmapped rows are residual off-topic / no facility evidence after Lab1."
        ),
    }


def run_lab2(
    input_name: str = "beijing_cleaned.jsonl",
    output_name: str = "beijing_analyzed.jsonl",
) -> str:
    ensure_data_dirs()
    in_path = CLEANED / input_name
    if not in_path.exists():
        raise FileNotFoundError(
            f"Lab2 requires cleaned input missing: {in_path}. "
            "Need real Lab1 output data/cleaned/beijing_cleaned.jsonl."
        )
    posts = parse_models(read_jsonl(in_path), PostCleaned)
    if not posts:
        raise FileNotFoundError(f"Lab2 input empty: {in_path}")
    analyzed = analyze_posts(posts)
    out_path = ANALYZED / output_name
    write_jsonl(out_path, dump_models(analyzed))
    write_json(ANALYZED / "lab2_analysis_report.json", _stats(analyzed))
    return str(out_path)
