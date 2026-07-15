#!/usr/bin/env python
"""Run Lab3 only. OWNER: AGENT_LAB3. Requires Lab2 output."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab3_decision.report import run_lab3


def main() -> None:
    out = run_lab3()
    print(f"[lab3] wrote {out}")


if __name__ == "__main__":
    main()
