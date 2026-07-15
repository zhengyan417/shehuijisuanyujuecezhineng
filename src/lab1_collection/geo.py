"""Beijing geo / district inference for Lab1.

OWNER: AGENT_LAB1

Priority (as required):
  1) district_hint
  2) poi
  3) geo_raw
  4) text landmarks/district names (fallback only)
"""

from __future__ import annotations

from src.common.io import load_yaml
from src.common.paths import CITY

LANDMARK_TO_DISTRICT: dict[str, str] = {
    "望京": "朝阳区",
    "劲松": "朝阳区",
    "国贸": "朝阳区",
    "三里屯": "朝阳区",
    "金盏": "朝阳区",
    "豆各庄": "朝阳区",
    "双井": "朝阳区",
    "酒仙桥": "朝阳区",
    "北苑": "朝阳区",
    "亚运村": "朝阳区",
    "通州北苑": "通州区",
    "通州": "通州区",
    "中关村": "海淀区",
    "五道口": "海淀区",
    "清河": "海淀区",
    "西二旗": "海淀区",
    "上地": "海淀区",
    "回龙观": "昌平区",
    "天通苑": "昌平区",
    "亦庄": "大兴区",
    "旧宫": "大兴区",
    "西单": "西城区",
    "金融街": "西城区",
    "新风街": "西城区",
    "前门": "东城区",
    "王府井": "东城区",
    "和平里": "东城区",
    "石景山万达": "石景山区",
    "苹果园": "石景山区",
    "大峪": "门头沟区",
    "房山城关": "房山区",
    "良乡": "房山区",
    "后沙峪": "顺义区",
}


def district_list() -> list[str]:
    return list(load_yaml(CITY).get("districts", []))


def _match_in_field(field: str) -> tuple[str | None, float, str | None]:
    """Match district/landmark inside a single structured geo field (not full post text)."""
    districts = district_list()
    for landmark in sorted(LANDMARK_TO_DISTRICT.keys(), key=len, reverse=True):
        if landmark in field:
            return LANDMARK_TO_DISTRICT[landmark], 0.9, landmark
    for d in districts:
        if d in field:
            return d, 0.88, d
        short = d.replace("区", "")
        if len(short) >= 2 and short in field:
            return d, 0.85, short
    if "北京" in field:
        return None, 0.5, "北京"
    return None, 0.0, None


def infer_district(
    text: str,
    district_hint: str | None = None,
    geo_raw: str | None = None,
    poi: str | None = None,
) -> tuple[str | None, float, str | None]:
    """Return (district, confidence, matched_place).

    Prefer structured geo fields before free-text extraction.
    """
    if district_hint:
        return district_hint, 0.95, district_hint

    if poi and str(poi).strip():
        d, conf, matched = _match_in_field(str(poi))
        if d or matched:
            return d, conf, matched

    if geo_raw and str(geo_raw).strip():
        d, conf, matched = _match_in_field(str(geo_raw))
        if d or matched:
            return d, conf, matched

    # fallback: text only
    districts = district_list()
    for d in districts:
        if d in text:
            return d, 0.8, d
        short = d.replace("区", "")
        if len(short) >= 2 and short in text:
            return d, 0.75, short

    for landmark in sorted(LANDMARK_TO_DISTRICT.keys(), key=len, reverse=True):
        if landmark in text:
            return LANDMARK_TO_DISTRICT[landmark], 0.65, landmark

    return None, 0.0, None
