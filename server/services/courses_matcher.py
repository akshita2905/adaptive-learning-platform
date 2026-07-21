"""
Load curated ``courses.json`` and map roadmap phase text to recommended courses.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent.parent
_COURSES_PATH = _ROOT / "ml_model" / "data" / "courses.json"
_catalog: dict[str, list[str]] | None = None


def load_courses_catalog() -> dict[str, list[str]]:
    """Load and cache the topic → course list mapping."""
    global _catalog
    if _catalog is not None:
        return _catalog
    try:
        with open(_COURSES_PATH, encoding="utf-8") as f:
            _catalog = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Could not load courses.json: %s", exc)
        _catalog = {}
    return _catalog


def match_courses_for_phases(phases: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    For each catalog topic whose name appears in any phase title/topics string, attach courses.

    Returns a dict like ``{\"Python\": [\"Course A\", ...], ...}`` without duplicates per topic.
    """
    catalog = load_courses_catalog()
    if not catalog or not phases:
        return {}

    matched: dict[str, list[str]] = {}
    for phase in phases:
        blob = f"{phase.get('phase', '')} {phase.get('topics', '')}".lower()
        for topic, courses in catalog.items():
            if topic.lower() in blob:
                matched[topic] = list(courses)
    return matched
