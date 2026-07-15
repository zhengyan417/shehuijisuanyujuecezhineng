"""Build Weibo queries: many place-first + broader recall queries.

OWNER: AGENT_LAB1
"""

from __future__ import annotations

from dataclasses import dataclass

from src.common.io import load_yaml
from src.common.paths import KEYWORDS


@dataclass(frozen=True)
class SearchQuery:
    facility_scope: str
    query: str
    layer: str  # place_symptom|place_need|broad_bj|facility_symptom
    place: str = ""


def load_taxonomy() -> dict:
    return load_yaml(KEYWORDS)


def _compact(*parts: str) -> str:
    return "".join(p.strip() for p in parts if p and str(p).strip())


def build_queries(max_per_scope: int = 120) -> list[SearchQuery]:
    """Emit a large query set with reserved slots for place / broad / facility layers."""
    tax = load_taxonomy()
    places = list(
        dict.fromkeys(
            list(tax.get("place_hints", {}).get("hotspots", []))
            + list(tax.get("place_hints", {}).get("district_shorts", []))
        )
    )
    allow_bj = bool((tax.get("collection_policy") or {}).get("allow_beijing_facility_symptom", True))

    buckets: dict[str, list[SearchQuery]] = {
        "place_symptom": [],
        "place_need": [],
        "broad_bj": [],
        "facility_symptom": [],
    }

    for scope, cfg in (tax.get("facility_types") or {}).items():
        labels = list(cfg.get("labels") or [])
        symptoms = list(cfg.get("symptoms") or [])
        cues = list(cfg.get("need_cues") or [])
        seed = labels[0] if labels else "设施"

        for lab in labels:
            for sym in symptoms:
                buckets["facility_symptom"].append(
                    SearchQuery(scope, _compact(lab, sym), "facility_symptom")
                )
                if allow_bj:
                    buckets["broad_bj"].append(
                        SearchQuery(scope, _compact("北京", lab, sym), "broad_bj", place="北京")
                    )
            for cue in cues:
                buckets["facility_symptom"].append(
                    SearchQuery(scope, _compact(lab, cue), "facility_symptom")
                )
                if allow_bj:
                    buckets["broad_bj"].append(
                        SearchQuery(scope, _compact("北京", lab, cue), "broad_bj", place="北京")
                    )

        for place in places:
            for lab in labels[:3]:
                for sym in symptoms:
                    buckets["place_symptom"].append(
                        SearchQuery(scope, _compact(place, lab, sym), "place_symptom", place=place)
                    )
                for cue in cues[:4]:
                    buckets["place_need"].append(
                        SearchQuery(scope, _compact(place, lab, cue), "place_need", place=place)
                    )
                    if symptoms:
                        buckets["place_need"].append(
                            SearchQuery(
                                scope,
                                _compact(place, lab, symptoms[0], cue),
                                "place_need",
                                place=place,
                            )
                        )
            if symptoms:
                buckets["place_symptom"].append(
                    SearchQuery(scope, _compact(place, seed, symptoms[0]), "place_symptom", place=place)
                )

    # quotas within each scope (sum ~= max_per_scope)
    place_quota = max(int(max_per_scope * 0.55), 40)
    broad_quota = max(int(max_per_scope * 0.25), 15)
    facility_quota = max(max_per_scope - place_quota - broad_quota, 15)

    def _take(items: list[SearchQuery], scope: str, limit: int, seen: set[str]) -> list[SearchQuery]:
        out: list[SearchQuery] = []
        for q in items:
            if q.facility_scope != scope:
                continue
            if q.query in seen or len(q.query) < 4:
                continue
            seen.add(q.query)
            out.append(q)
            if len(out) >= limit:
                break
        return out

    uniq: list[SearchQuery] = []
    for scope in ("road_lighting", "public_charging", "public_transit"):
        seen: set[str] = set()
        place_items = buckets["place_symptom"] + buckets["place_need"]
        uniq.extend(_take(place_items, scope, place_quota, seen))
        uniq.extend(_take(buckets["broad_bj"], scope, broad_quota, seen))
        uniq.extend(_take(buckets["facility_symptom"], scope, facility_quota, seen))
    return uniq


def queries_as_dicts() -> list[dict]:
    return [
        {
            "facility_scope": q.facility_scope,
            "query": q.query,
            "layer": q.layer,
            "place": q.place,
        }
        for q in build_queries()
    ]
