from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.lab1_collection.sources import CollectionError
from src.pipeline import run_all


def test_pipeline_refuses_without_real_data():
    with pytest.raises(CollectionError):
        run_all()
