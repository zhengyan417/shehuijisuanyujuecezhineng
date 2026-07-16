"""Facility / location lexicon NER for Beijing silent-demand posts.

OWNER: AGENT_LAB2
"""

from __future__ import annotations

from src.common.models import Entities, FacilityScope

FACILITY_LEXICON: dict[FacilityScope, list[str]] = {
    "road_lighting": [
        "路灯",
        "道路照明",
        "夜间照明",
        "马路灯",
        "路灯杆",
        "灯杆",
        "灯不亮",
        "黑灯瞎火",
        "红绿灯",
        "信号灯",
        "照明",
        "人行道路灯",
    ],
    "public_charging": [
        "充电桩",
        "充电站",
        "公共充电",
        "快充",
        "慢充",
        "充电位",
        "换电站",
        "新能源充电",
        "特斯拉充电桩",
        "电动汽车充电",
        "电动车充电桩",
        "充电器",
    ],
    "public_transit": [
        "公交站",
        "公交站台",
        "候车亭",
        "天桥",
        "过街天桥",
        "人行天桥",
        "过街设施",
        "站台",
        "过马路",
        "公交车",
        "地铁口",
    ],
}

LOCATION_LEXICON = [
    "望京SOHO",
    "望京新荟城",
    "望京桥",
    "望京",
    "花家地",
    "广顺南大街",
    "广顺北大街",
    "三里屯",
    "中关村",
    "五道口",
    "西二旗",
    "上地",
    "回龙观",
    "天通苑",
    "通州北苑",
    "通州",
    "亦庄",
    "国贸",
    "西单",
    "清河",
    "金融街",
    "王府井",
    "后沙峪",
    "良乡",
    "苹果园",
    "劲松",
    "双井",
    "太阳宫",
    "芍药居",
    "奥森",
    "北苑",
    "朝阳公园",
    "朝阳区",
    "海淀区",
    "昌平区",
    "大兴区",
    "通州区",
    "西城区",
    "东城区",
    "丰台区",
    "石景山区",
    "顺义区",
    "房山区",
]


def extract_entities(text: str) -> Entities:
    facilities: list[str] = []
    for words in FACILITY_LEXICON.values():
        for w in sorted(words, key=len, reverse=True):
            if w in text and w not in facilities:
                facilities.append(w)

    locations: list[str] = []
    for w in sorted(LOCATION_LEXICON, key=len, reverse=True):
        if w in text and w not in locations:
            if any(w != loc and w in loc for loc in locations):
                continue
            locations.append(w)
    return Entities(facility=facilities, location=locations)


def infer_scope_from_entities(
    entities: Entities,
    hint: FacilityScope | None,
    text: str = "",
) -> FacilityScope | None:
    """Prefer lexical evidence over Lab1 soft hint when they conflict strongly."""
    scores: dict[FacilityScope, int] = {
        "road_lighting": 0,
        "public_charging": 0,
        "public_transit": 0,
    }
    for scope, words in FACILITY_LEXICON.items():
        for w in words:
            if w in text or w in entities.facility:
                scores[scope] += max(1, len(w) // 2)

    best_scope = max(scores, key=scores.get)
    best_score = scores[best_scope]
    if best_score > 0:
        # If hint agrees or hint missing → use best lexical scope
        if not hint or hint == best_scope:
            return best_scope
        # If hint conflicts but lexical evidence is strong, trust lexicon
        if best_score >= 3 and scores.get(hint, 0) == 0:
            return best_scope
        return hint
    return hint
