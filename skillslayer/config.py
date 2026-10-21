"""Paths and the fixed reference date. The data is synthetic and dated, so every run is reproducible."""

from __future__ import annotations

from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SOURCES = DATA / "sources"
AS_OF = date(2026, 10, 1)
