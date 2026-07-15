#!/usr/bin/env python
"""Run full pipeline Lab1 -> Lab2 -> Lab3. REAL DATA ONLY."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.lab1_collection.sources import CollectionError
from src.pipeline import run_all


def main() -> None:
    try:
        result = run_all()
    except CollectionError as e:
        print(str(e), file=sys.stderr)
        raise SystemExit(2) from e
    for k, v in result.items():
        print(f"[pipeline] {k}: {v}")


if __name__ == "__main__":
    main()
