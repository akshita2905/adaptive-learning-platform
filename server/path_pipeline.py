"""
Assemble ``base_path``, LLM roadmap, YouTube clips, scored skill gaps, and course matches.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

from config import Settings
from ml_service import build_path_payload, get_recommender
from services.adaptive_service import (
    apply_adaptive_extensions,
    build_adaptive_llm_hint,
    fetch_user_feedback,
    feedback_fingerprint,
    log_adaptive_summary,
    misunderstood_indices,
    rebuild_roadmap_metadata,
)
from services.courses_matcher import match_courses_for_phases
from services.openai_roadmap import generate_ai_roadmap
from services.youtube_service import get_youtube_videos

logger = logging.getLogger(__name__)


def _build_base_path_dict(
    raw: dict[str, Any],
    level_used: str,
    predicted: str | None,
    probs: dict[str, float] | None,
) -> dict[str, Any]:
    """Strip internal recommender fields and shape the ML layer response."""
    bp = copy.deepcopy(raw)
    bp.pop("role_skills_keywords", None)
    bp["experience_level_used"] = level_used
    bp["predicted_level"] = predicted
    bp["level_probabilities"] = probs
    return bp


def build_full_path_response(
    *,
    user_id: str,
    skills: list[str],
    goal: str,
    hours_per_day: float,
    experience_level: str | None,
    settings: Settings,
    regenerate_smarter: bool,
    feedback_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Run ML → adaptive extensions → OpenAI → YouTube → courses → skill gaps.

    Returns a plain dict matching ``GeneratePathResponse`` (without ``generation_id``).
    Pass ``feedback_rows`` to avoid a second Mongo read when the caller already loaded them.
    """
    if feedback_rows is None:
        feedback_rows = fetch_user_feedback(user_id)
    fb_print = feedback_fingerprint(feedback_rows)
    logger.debug("feedback fingerprint=%s count=%s", fb_print, len(feedback_rows))

    raw, level_used, predicted, probs = build_path_payload(
        goal.strip(), skills, hours_per_day, experience_level
    )

    phases = raw.get("phases") or []
    mu = misunderstood_indices(phases, feedback_rows)
    if mu:
        phases = apply_adaptive_extensions(phases, mu)
        total_days, weeks, roadmap_lines = rebuild_roadmap_metadata(phases)
        raw = copy.deepcopy(raw)
        raw["phases"] = phases
        raw["timeline_days"] = total_days
        raw["timeline_weeks"] = weeks
        raw["roadmap"] = roadmap_lines
        log_adaptive_summary(user_id, mu, True)
    else:
        log_adaptive_summary(user_id, set(), False)

    base_path = _build_base_path_dict(raw, level_used, predicted, probs)
    kw = raw.get("role_skills_keywords") or ""

    rec = get_recommender()
    skill_gaps = rec.scored_skill_gaps(skills, kw) if kw else []

    adaptive_hint = build_adaptive_llm_hint(feedback_rows)
    ai_roadmap = generate_ai_roadmap(
        base_path,
        skills,
        goal.strip(),
        float(hours_per_day),
        settings.openai_api_key,
        settings.openai_model,
        smarter=regenerate_smarter,
        adaptive_hint=adaptive_hint,
    )

    videos: dict[str, list[dict[str, Any]]] = {}
    yt_key = settings.youtube_api_key or ""
    max_v = settings.youtube_max_per_topic
    for i, ph in enumerate(base_path.get("phases") or []):
        q = f"{goal} {ph.get('phase', '')} tutorial"
        videos[str(i)] = get_youtube_videos(q, yt_key, max_results=max_v)

    courses = match_courses_for_phases(base_path.get("phases") or [])

    return {
        "base_path": base_path,
        "ai_roadmap": ai_roadmap,
        "videos": videos,
        "skill_gaps": skill_gaps,
        "courses": courses,
    }
