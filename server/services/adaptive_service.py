"""
Load user step feedback and derive adaptive hints / phase extensions.
"""

from __future__ import annotations

import copy
import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def fetch_user_feedback(user_id: str, limit: int = 100) -> list[dict[str, Any]]:
    """Return recent feedback documents for a user, newest first."""
    from db import feedback_coll

    cur = feedback_coll().find({"user_id": user_id}).sort("created_at", -1).limit(limit)
    return list(cur)


def feedback_fingerprint(rows: list[dict[str, Any]]) -> str:
    """Short stable string for cache keys when feedback set changes."""
    sig = [(r.get("phase_name"), r.get("status"), r.get("step_index")) for r in rows[:60]]
    return hashlib.md5(json.dumps(sig, default=str).encode("utf-8")).hexdigest()


def misunderstood_indices(phases: list[dict[str, Any]], rows: list[dict[str, Any]]) -> set[int]:
    """Map ``not_understood`` feedback rows to phase indices."""
    name_to_i = {p.get("phase", ""): i for i, p in enumerate(phases)}
    out: set[int] = set()
    for r in rows:
        if r.get("status") != "not_understood":
            continue
        pn = r.get("phase_name") or ""
        if pn in name_to_i:
            out.add(name_to_i[pn])
        si = r.get("step_index")
        if isinstance(si, int) and 0 <= si < len(phases):
            out.add(si)
    return out


def apply_adaptive_extensions(
    phases: list[dict[str, Any]],
    misunderstood: set[int],
    extra_days: int = 4,
) -> list[dict[str, Any]]:
    """
    Extend day ranges for difficult phases and shift later phases to avoid overlap.

    This makes the next roadmap calendar-aware of struggle areas before LLM enrichment.
    """
    if not misunderstood:
        return phases

    ph = copy.deepcopy(phases)
    extra_days = max(1, int(extra_days))
    for i in sorted(misunderstood):
        if 0 <= i < len(ph):
            ph[i]["days_end"] = int(ph[i]["days_end"]) + extra_days

    for i in range(1, len(ph)):
        prev_end = int(ph[i - 1]["days_end"])
        cur_start = int(ph[i]["days_start"])
        if cur_start <= prev_end:
            delta = prev_end - cur_start + 1
            ph[i]["days_start"] = cur_start + delta
            ph[i]["days_end"] = int(ph[i]["days_end"]) + delta

    return ph


def rebuild_roadmap_metadata(phases: list[dict[str, Any]]) -> tuple[int, int, list[str]]:
    """Recompute timeline_weeks and roadmap lines after phase mutation."""
    if not phases:
        return 0, 0, []
    total_days = int(phases[-1]["days_end"])
    weeks = max(1, round(total_days / 7))
    lines = [
        f"Day {p['days_start']}–{p['days_end']}: {p.get('phase', '')} — {p.get('topics', '')}"
        for p in phases
    ]
    return total_days, weeks, lines


def build_adaptive_llm_hint(rows: list[dict[str, Any]]) -> str:
    """Natural-language hint appended to the OpenAI system prompt."""
    completed = [r for r in rows if r.get("status") == "completed"][:25]
    nu = [r for r in rows if r.get("status") == "not_understood"][:25]
    if not completed and not nu:
        return ""

    parts: list[str] = []
    if completed:
        names = ", ".join(sorted({str(r.get("phase_name") or "?") for r in completed}))
        parts.append(f"The learner marked these phases as completed (avoid redundant repetition): {names}.")
    if nu:
        names = ", ".join(sorted({str(r.get("phase_name") or "?") for r in nu}))
        parts.append(
            f"The learner struggled with these phases — add simpler substeps, analogies, "
            f"practice drills, and suggest extra buffer days in detailed_plan: {names}."
        )
    return " ".join(parts)


def log_adaptive_summary(user_id: str, misunderstood: set[int], extended: bool) -> None:
    """Structured log line for observability."""
    logger.info(
        "adaptive user=%s misunderstood_indices=%s extended=%s",
        user_id[:8] + "…",
        sorted(misunderstood),
        extended,
    )
