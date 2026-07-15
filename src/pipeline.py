"""End-to-end pipeline orchestrator.

OWNER: SHARED

Hard policy: no fake/fixture social data. Without real crawl/import, abort.
"""

from __future__ import annotations

from src.lab1_collection.collector import run_lab1
from src.lab1_collection.sources import CollectionError
from src.lab2_analysis.analyzer import run_lab2
from src.lab3_decision.report import run_lab3


def run_all() -> dict[str, str]:
    try:
        cleaned = run_lab1(source="auto")
    except CollectionError as e:
        raise CollectionError(
            "Pipeline blocked: Lab1 has no real Weibo data yet.\n" + str(e)
        ) from e
    analyzed = run_lab2()
    report = run_lab3()
    return {"cleaned": cleaned, "analyzed": analyzed, "report": report}
