#!/usr/bin/env python
"""Run Lab2 only. OWNER: AGENT_LAB2. Requires Lab1 output."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab2_analysis.analyzer import run_lab2


def main() -> None:
    out = run_lab2()
    print(f"[lab2] wrote {out}")


if __name__ == "__main__":
    main()
