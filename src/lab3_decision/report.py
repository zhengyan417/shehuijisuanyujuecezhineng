"""Lab3 — aggregate analyzed posts into generative decision-support products.

OWNER: AGENT_LAB3
READS: data/analyzed/*.jsonl
WRITES: data/reports/*
MUST NOT EDIT: src/lab1_collection/**, src/lab2_analysis/**, configs/keywords_taxonomy.yaml
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from src.common.io import parse_models, read_jsonl, write_json
from src.common.models import DecisionReport, FacilityGap, PostAnalyzed, PriorityItem
from src.common.paths import ANALYZED, REPORTS, ensure_data_dirs

LAB3_VERSION = "lab3-stub-0.1.0"

ACTION_TEMPLATES = {
    "lighting_repair": "安排道路照明巡检与故障灯具维修，优先夜查高频路段。",
    "lighting_coverage": "评估夜间步行安全保障，补充照明覆盖盲区。",
    "charging_availability": "核查公共充电桩布局与可用率，补充供给或加快故障修复。",
    "charging_occupancy_governance": "加强充电车位专位管理与占位治理执法/劝导。",
    "bus_stop_amenity": "推进公交站台遮雨、指示与候车设施维护改善。",
    "pedestrian_crossing_safety": "评估过街设施可达性与安全风险，研究天桥/通道优化。",
}


def _district_of(p: PostAnalyzed) -> str:
    return p.geo.district or "未定位/全市"


def aggregate(posts: list[PostAnalyzed]) -> tuple[list[FacilityGap], list[PriorityItem]]:
    buckets: dict[tuple[str, str, str, str], list[PostAnalyzed]] = defaultdict(list)
    for p in posts:
        if not p.mapped_need.need_id:
            continue
        key = (
            _district_of(p),
            p.mapped_need.facility_scope or "unknown",
            p.mapped_need.need_id,
            p.mapped_need.need_name_zh or p.mapped_need.need_id,
        )
        buckets[key].append(p)

    gaps: list[FacilityGap] = []
    for (district, scope, need_id, need_name), items in buckets.items():
        avg_u = sum(i.urgency_score for i in items) / max(len(items), 1)
        gaps.append(
            FacilityGap(
                district=district,
                facility_scope=scope,
                need_id=need_id,
                need_name_zh=need_name,
                count=len(items),
                avg_urgency=round(avg_u, 3),
                sample_ids=[i.id for i in items[:5]],
            )
        )

    scored = []
    for g in gaps:
        score = g.count * 0.6 + g.avg_urgency * 10 * 0.4
        scored.append((score, g))
    scored.sort(key=lambda x: x[0], reverse=True)

    priorities: list[PriorityItem] = []
    for rank, (score, g) in enumerate(scored, start=1):
        priorities.append(
            PriorityItem(
                rank=rank,
                need_id=g.need_id,
                district=g.district,
                score=round(score, 3),
                suggested_action=ACTION_TEMPLATES.get(g.need_id, "结合现场核查后提出专项整治方案。"),
            )
        )
    return gaps, priorities


def render_markdown(report: DecisionReport) -> str:
    lines = [
        f"# 北京市公共服务「沉默需求」发现报告",
        "",
        f"- 报告ID: `{report.report_id}`",
        f"- 生成时间: {report.generated_at}",
        f"- 城市: {report.city}",
        "",
        "## 摘要",
        report.summary,
        "",
        "## 设施缺口清单",
    ]
    for g in report.facility_gaps:
        lines.append(
            f"- [{g.district}] ({g.facility_scope}) {g.need_name_zh} — {g.count}条信号, 平均紧迫度 {g.avg_urgency}"
        )
    lines.extend(["", "## 优先级建议"])
    for p in report.priorities:
        lines.append(
            f"{p.rank}. [{p.district}] `{p.need_id}` score={p.score} — {p.suggested_action}"
        )
    lines.extend(["", "## 方法说明", report.method_notes, ""])
    return "\n".join(lines)


def run_lab3(input_name: str = "beijing_analyzed.jsonl", report_stem: str = "beijing_silent_demand") -> str:
    ensure_data_dirs()
    in_path = ANALYZED / input_name
    if not in_path.exists():
        raise FileNotFoundError(f"Lab3 requires analyzed input missing: {in_path}. Run Lab2 first.")
    posts = parse_models(read_jsonl(in_path), PostAnalyzed)
    gaps, priorities = aggregate(posts)
    now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    summary = (
        f"基于 {len(posts)} 条北京市相关帖子信号，识别出 {len(gaps)} 个区域-需求缺口组合；"
        f"覆盖道路照明、公共充电与公共交通设施三类主题。"
    )
    report = DecisionReport(
        report_id=f"{report_stem}-{now[:10]}",
        city="北京",
        generated_at=now,
        summary=summary,
        facility_gaps=gaps,
        priorities=priorities,
        method_notes=(
            "流水线：社交媒体信号采集清洗 → 意图/情绪/实体/需求映射 → 区域聚合与优先级生成。"
            "当前 Lab3 stub 使用模板化建议；可替换为 LLM grounding + 权威知识检索。"
            f" lab3_version={LAB3_VERSION}"
        ),
        meta={"lab3_version": LAB3_VERSION, "input_count": len(posts)},
    )
    json_path = REPORTS / f"{report_stem}.json"
    md_path = REPORTS / f"{report_stem}.md"
    write_json(json_path, report.model_dump(mode="json"))
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return str(md_path)
