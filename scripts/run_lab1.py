#!/usr/bin/env python
"""Run Lab1 only. OWNER: AGENT_LAB1."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab1_collection.collector import run_lab1


def main() -> None:
    out = run_lab1()
    print(f"[lab1] wrote {out}")


if __name__ == "__main__":
    main()
