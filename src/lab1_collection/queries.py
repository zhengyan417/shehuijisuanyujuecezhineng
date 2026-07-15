"""Build search queries from Lab1 keyword taxonomy.

OWNER: AGENT_LAB1
"""

from __future__ import annotations

from dataclasses import dataclass

from src.common.io import load_yaml
from src.common.paths import CITY, KEYWORDS


@dataclass(frozen=True)
class SearchQuery:
    facility_scope: str
    query: str
    layer: str  # facility|symptom_combo|place_combo|need_cue


def load_taxonomy() -> dict:
    return load_yaml(KEYWORDS)


def build_queries(max_per_scope: int = 24) -> list[SearchQuery]:
    """Compose chronic/local queries: facility + symptom / place / need cue.

    Domain nature is non-burst: we prefer many narrow continuous queries
    over a single event keyword blast.
    """
    tax = load_taxonomy()
    city = load_yaml(CITY)
    districts = list(city.get("districts", []))[:8]
    landmarks = list(tax.get("place_hints", {}).get("landmarks_examples", []))

    out: list[SearchQuery] = []
    for scope, cfg in (tax.get("facility_types") or {}).items():
        labels = list(cfg.get("labels") or [])
        symptoms = list(cfg.get("symptoms") or [])
        cues = list(cfg.get("need_cues") or [])

        for lab in labels[:4]:
            out.append(SearchQuery(scope, f"北京 {lab}", "facility"))
            for sym in symptoms[:4]:
                out.append(SearchQuery(scope, f"北京 {lab} {sym}", "symptom_combo"))
            for cue in cues[:2]:
                out.append(SearchQuery(scope, f"北京 {lab} {cue}", "need_cue"))

        # place-aware queries (strong geo prior for this domain)
        seed_label = labels[0] if labels else scope
        for place in (landmarks + districts)[:10]:
            out.append(SearchQuery(scope, f"{place} {seed_label}", "place_combo"))

    # stable de-dupe while preserving order
    seen: set[str] = set()
    uniq: list[SearchQuery] = []
    per_scope: dict[str, int] = {}
    for q in out:
        if q.query in seen:
            continue
        if per_scope.get(q.facility_scope, 0) >= max_per_scope:
            continue
        seen.add(q.query)
        per_scope[q.facility_scope] = per_scope.get(q.facility_scope, 0) + 1
        uniq.append(q)
    return uniq


def queries_as_dicts() -> list[dict]:
    return [
        {
            "facility_scope": q.facility_scope,
            "query": q.query,
            "layer": q.layer,
        }
        for q in build_queries()
    ]
