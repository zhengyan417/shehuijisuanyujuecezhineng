"""End-to-end pipeline orchestrator.

OWNER: SHARED — edit only with coordination from all three lab agents.
"""

from __future__ import annotations

from src.lab1_collection.collector import run_lab1
from src.lab2_analysis.analyzer import run_lab2
from src.lab3_decision.report import run_lab3


def run_all() -> dict[str, str]:
    cleaned = run_lab1()
    analyzed = run_lab2()
    report = run_lab3()
    return {"cleaned": cleaned, "analyzed": analyzed, "report": report}
