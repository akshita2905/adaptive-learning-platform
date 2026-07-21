"""
OpenAI Chat Completions: turn ML ``base_path`` into a richer structured roadmap (JSON).
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _strip_json_fence(text: str) -> str:
    """Remove optional ```json ... ``` wrapper from model output."""
    t = text.strip()
    m = re.match(r"^```(?:json)?\s*([\s\S]*?)```$", t)
    if m:
        return m.group(1).strip()
    return t


def _fallback_ai_roadmap(base_path: dict[str, Any], goal: str, hours: float) -> dict[str, Any]:
    """Deterministic template when API key is missing or the model fails."""
    phases = base_path.get("phases") or []
    detailed_plan: list[dict[str, Any]] = []
    for p in phases:
        topics = [x.strip() for x in str(p.get("topics", "")).split(",") if x.strip()]
        detailed_plan.append(
            {
                "day_range": f"Day {p['days_start']}–{p['days_end']}",
                "title": p.get("phase", "Phase"),
                "tasks": topics[:8] or [f"Practice core ideas for {p.get('phase', 'this phase')}"],
                "explanation": (
                    f"This block supports your goal ({goal}) with focus on {p.get('phase', 'key skills')}."
                ),
                "learning_tips": [
                    f"Block ~{hours}h/day; end each session with a 5-minute recap note.",
                    "Build one tiny artifact (snippet, diagram, or cheat sheet) per phase.",
                ],
            }
        )
    return {
        "detailed_plan": detailed_plan,
        "explanations": (
            "Set OPENAI_API_KEY for LLM-enhanced narratives. "
            "This fallback follows your ML-selected phases and schedule."
        ),
        "tips": [
            "Alternate deep work with active recall (flashcards or explain-aloud).",
            "If a topic feels fuzzy, watch one short video, then re-read your own notes only.",
        ],
    }


def generate_ai_roadmap(
    base_path: dict[str, Any],
    skills: list[str],
    goal: str,
    hours: float,
    api_key: str,
    model: str,
    smarter: bool = False,
    adaptive_hint: str = "",
) -> dict[str, Any]:
    """
    Call OpenAI to produce JSON with ``detailed_plan``, ``explanations``, and ``tips``.

    ``detailed_plan`` should align 1:1 with ``base_path['phases']`` (same count / order).
    """
    if not (api_key or "").strip():
        # Startup warning is emitted in ``config.get_settings``; keep this path quiet per request.
        logger.debug("Skipping OpenAI call: empty API key; using fallback roadmap.")
        return _fallback_ai_roadmap(base_path, goal, hours)

    try:
        from openai import OpenAI
    except ImportError:
        logger.error("openai package not installed")
        return _fallback_ai_roadmap(base_path, goal, hours)

    phases = base_path.get("phases") or []
    phase_json = json.dumps(phases, ensure_ascii=False)
    skills_s = ", ".join(skills)
    smarter_note = (
        "Be especially thorough: common pitfalls, checkpoints, and one mini-project idea per phase."
        if smarter
        else "Keep outputs concise but actionable."
    )

    system = (
        "You are an expert learning coach. Output ONLY valid JSON (no markdown) matching this schema:\n"
        "{\n"
        '  "detailed_plan": [\n'
        "    {\n"
        '      "day_range": string,\n'
        '      "title": string,\n'
        '      "tasks": string[],\n'
        '      "explanation": string,\n'
        '      "learning_tips": string[]\n'
        "    }\n"
        "  ],\n"
        '  "explanations": string,\n'
        '  "tips": string[]\n'
        "}\n"
        f"The detailed_plan array MUST have exactly {len(phases)} objects, in the same order as the input phases.\n"
        f"User goal: {goal}. Known skills: {skills_s}. Hours per day: {hours}.\n"
        f"{smarter_note}\n"
    )
    if adaptive_hint:
        system += f"Adaptive signals: {adaptive_hint}\n"

    user_msg = (
        "Here is the ML-generated phase list (JSON). Expand each into day-wise style guidance.\n"
        f"{phase_json}"
    )

    client = OpenAI(api_key=api_key.strip())
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user_msg},
            ],
            temperature=0.55 if smarter else 0.4,
            response_format={"type": "json_object"},
        )
        content = (resp.choices[0].message.content or "").strip()
        parsed = json.loads(_strip_json_fence(content))
    except Exception as exc:
        logger.exception("OpenAI roadmap generation failed: %s", exc)
        return _fallback_ai_roadmap(base_path, goal, hours)

    if not isinstance(parsed, dict):
        return _fallback_ai_roadmap(base_path, goal, hours)

    return normalize_ai_roadmap(parsed, phases, goal, hours)


def normalize_ai_roadmap(
    parsed: dict[str, Any],
    phases: list[dict[str, Any]],
    goal: str,
    hours: float,
) -> dict[str, Any]:
    """Merge model JSON with phase metadata so every step has required keys."""
    detailed = parsed.get("detailed_plan")
    if not isinstance(detailed, list):
        detailed = []

    out_plan: list[dict[str, Any]] = []
    for i, p in enumerate(phases):
        item = detailed[i] if i < len(detailed) and isinstance(detailed[i], dict) else {}
        tasks = item.get("tasks")
        if not isinstance(tasks, list):
            tasks = []
        tips = item.get("learning_tips")
        if not isinstance(tips, list):
            alt = item.get("tips")
            tips = alt if isinstance(alt, list) else []
        out_plan.append(
            {
                "day_range": item.get("day_range") or f"Day {p['days_start']}–{p['days_end']}",
                "title": item.get("title") or p.get("phase", "Phase"),
                "tasks": [str(t) for t in tasks][:12],
                "explanation": str(item.get("explanation") or "").strip()
                or f"Strengthen {p.get('phase', 'skills')} toward {goal}.",
                "learning_tips": [str(t) for t in tips][:8]
                or [f"Study in ~{hours}h focused blocks with short breaks."],
            }
        )

    expl = parsed.get("explanations")
    if not isinstance(expl, str):
        expl = json.dumps(expl) if expl is not None else ""

    tips_top = parsed.get("tips")
    if not isinstance(tips_top, list):
        tips_top = []

    return {
        "detailed_plan": out_plan,
        "explanations": expl.strip()
        or "Personalized explanations based on your goal, skills, and phased roadmap.",
        "tips": [str(t) for t in tips_top][:12],
    }
