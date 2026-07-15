"""Beijing geo / district inference for Lab1.

OWNER: AGENT_LAB1
"""

from __future__ import annotations

from src.common.io import load_yaml
from src.common.paths import CITY

# Landmark / colloquial place -> district. Expand carefully; keep Beijing-only.
LANDMARK_TO_DISTRICT: dict[str, str] = {
    "望京": "朝阳区",
    "国贸": "朝阳区",
    "三里屯": "朝阳区",
    "通州北苑": "通州区",
    "通州": "通州区",
    "中关村": "海淀区",
    "五道口": "海淀区",
    "清河": "海淀区",
    "西二旗": "海淀区",
    "上地": "海淀区",
    "回龙观": "昌平区",
    "天通苑": "昌平区",
    "昌平城区": "昌平区",
    "亦庄": "大兴区",
    "旧宫": "大兴区",
    "西单": "西城区",
    "金融街": "西城区",
    "前门": "东城区",
    "王府井": "东城区",
    "石景山万达": "石景山区",
    "苹果园": "石景山区",
    "房山城关": "房山区",
    "良乡": "房山区",
    "顺义城区": "顺义区",
    "后沙峪": "顺义区",
}


def district_list() -> list[str]:
    return list(load_yaml(CITY).get("districts", []))


def infer_district(
    text: str,
    district_hint: str | None = None,
    geo_raw: str | None = None,
    poi: str | None = None,
) -> tuple[str | None, float, str | None]:
    """Return (district, confidence, matched_place).

    Priority: explicit hint > POI/geo_raw landmark > district name in text > landmark in text.
    """
    districts = district_list()
    if district_hint:
        return district_hint, 0.95, district_hint

    blob = " ".join(x for x in [poi or "", geo_raw or "", text] if x)

    # longer landmark keys first (通州北苑 before 通州)
    for landmark in sorted(LANDMARK_TO_DISTRICT.keys(), key=len, reverse=True):
        if landmark in (poi or "") or landmark in (geo_raw or ""):
            return LANDMARK_TO_DISTRICT[landmark], 0.85, landmark

    for d in districts:
        if d in blob:
            return d, 0.8, d
        short = d.replace("区", "")
        if len(short) >= 2 and short in blob:
            return d, 0.75, short

    for landmark in sorted(LANDMARK_TO_DISTRICT.keys(), key=len, reverse=True):
        if landmark in text:
            return LANDMARK_TO_DISTRICT[landmark], 0.65, landmark

    return None, 0.0, None
