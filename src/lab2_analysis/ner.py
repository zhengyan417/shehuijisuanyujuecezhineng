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
        "灯不亮",
        "黑灯瞎火",
        "照明",
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
    ],
}

LOCATION_LEXICON = [
    "望京SOHO",
    "望京",
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
            # avoid adding both 朝阳区 and 朝阳 if both matched; keep longer first already
            if any(w in loc and w != loc for loc in locations):
                continue
            locations.append(w)
    return Entities(facility=facilities, location=locations)


def infer_scope_from_entities(entities: Entities, hint: FacilityScope | None) -> FacilityScope | None:
    if hint:
        return hint
    text_fac = " ".join(entities.facility)
    best: FacilityScope | None = None
    best_score = 0
    for scope, words in FACILITY_LEXICON.items():
        score = sum(1 for w in words if w in text_fac or w in entities.facility)
        if score > best_score:
            best_score = score
            best = scope
    return best
