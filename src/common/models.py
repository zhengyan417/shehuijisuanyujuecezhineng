"""Shared pydantic models = SINGLE SOURCE OF TRUTH for inter-lab data.

OWNERSHIP: common / SHARED CONFLICT ZONE.
Any field rename/add/remove requires:
1) update schemas/*.schema.json
2) update configs if needed
3) notify Lab1+Lab2+Lab3 agents in same PR/commit series
4) regenerate fixtures if breaking
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

FacilityScope = Literal["road_lighting", "public_charging", "public_transit"]
Platform = Literal["weibo", "xiaohongshu", "fixture", "other"]
Intent = Literal["抱怨", "建议", "询问", "其他"]
Emotion = Literal["不满", "焦虑", "期待", "中性"]


class GeoInfo(BaseModel):
    raw: Optional[str] = None
    poi: Optional[str] = None
    district: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class PostRaw(BaseModel):
    id: str
    platform: Platform
    text: str
    time: str
    city: Literal["北京"] = "北京"
    url: Optional[str] = None
    author_id_hash: Optional[str] = None
    geo_raw: Optional[str] = None
    poi: Optional[str] = None
    district_hint: Optional[str] = None
    facility_scope_hint: Optional[FacilityScope] = None
    source_query: Optional[str] = None


class Lab1Meta(BaseModel):
    lab1_version: str = "lab1-stub-0.1.0"
    is_duplicate: bool = False
    dropped: bool = False
    drop_reason: Optional[str] = None
    facility_scope_hint: Optional[FacilityScope] = None
    # B类：媒体/接诉转述市民诉求（非一手居民发帖）
    is_mediated: bool = False


class PostCleaned(BaseModel):
    id: str
    platform: Platform
    text: str
    clean_text: str
    time: str
    city: Literal["北京"] = "北京"
    geo: GeoInfo
    meta: Lab1Meta


class Entities(BaseModel):
    facility: list[str] = Field(default_factory=list)
    location: list[str] = Field(default_factory=list)


class MappedNeed(BaseModel):
    need_id: Optional[str] = None
    need_name_zh: Optional[str] = None
    facility_scope: Optional[FacilityScope] = None
    rule_id: Optional[str] = None


class Lab2Meta(BaseModel):
    lab1_version: str
    lab2_version: str = "lab2-stub-0.1.0"
    facility_scope_hint: Optional[FacilityScope] = None


class PostAnalyzed(BaseModel):
    id: str
    platform: Platform
    text: str
    clean_text: str
    time: str
    city: Literal["北京"] = "北京"
    geo: GeoInfo
    intent: Intent
    emotion: Emotion
    entities: Entities
    mapped_need: MappedNeed
    urgency_score: float = Field(ge=0.0, le=1.0)
    meta: Lab2Meta


class FacilityGap(BaseModel):
    district: str
    facility_scope: str
    need_id: str
    need_name_zh: str
    count: int
    avg_urgency: float
    sample_ids: list[str]


class PriorityItem(BaseModel):
    rank: int
    need_id: str
    district: str
    score: float
    suggested_action: str


class DecisionReport(BaseModel):
    report_id: str
    city: Literal["北京"] = "北京"
    generated_at: str
    summary: str
    facility_gaps: list[FacilityGap]
    priorities: list[PriorityItem]
    method_notes: str
    meta: dict = Field(default_factory=dict)
