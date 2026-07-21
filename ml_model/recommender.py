"""
Content-based learning path recommender using TF-IDF and cosine similarity.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def _load_phases_json(json_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load phase definitions keyed by role_id."""
    with open(json_path, encoding="utf-8") as f:
        raw: dict[str, list[dict[str, Any]]] = json.load(f)
    return raw


def _load_dataset(csv_path: Path, phases_path: Path) -> tuple[pd.DataFrame, dict[str, list[dict[str, Any]]]]:
    """Load the learning path catalog from CSV and phase definitions from JSON."""
    df = pd.read_csv(csv_path)
    df["combined_text"] = (
        df["role_name"].fillna("")
        + " "
        + df["skills_keywords"].fillna("")
        + " "
        + df["learning_path_summary"].fillna("")
    )
    phases_by_role = _load_phases_json(phases_path)
    return df, phases_by_role


def _scale_days(
    phases: list[dict[str, Any]],
    hours_per_day: float,
    experience_level: str,
) -> list[dict[str, Any]]:
    """
    Scale phase day ranges by available study hours and experience.

    More hours per day compresses the calendar; advanced learners get shorter spans.
    """
    hours_per_day = max(0.5, min(float(hours_per_day), 12.0))
    exp = (experience_level or "Beginner").strip().lower()
    if exp == "intermediate":
        factor = 0.85
    elif exp == "advanced":
        factor = 0.7
    else:
        factor = 1.0

    # More hours => fewer calendar days needed (sqrt dampening)
    hour_scale = math.sqrt(8.0 / hours_per_day)

    scaled: list[dict[str, Any]] = []
    cursor = 1
    for p in phases:
        start = int(p["days_start"])
        end = int(p["days_end"])
        span = max(1, round((end - start + 1) * hour_scale * factor))
        new_start = cursor
        new_end = cursor + span - 1
        scaled.append(
            {
                "phase": p.get("phase", "Phase"),
                "days_start": new_start,
                "days_end": new_end,
                "topics": p.get("topics", ""),
            }
        )
        cursor = new_end + 1
    return scaled


def _build_roadmap_lines(phases: list[dict[str, Any]]) -> list[str]:
    """Format phases as human-readable Day X–Y lines."""
    lines = []
    for p in phases:
        lines.append(
            f"Day {p['days_start']}–{p['days_end']}: {p['phase']} — {p['topics']}"
        )
    return lines


class LearningPathRecommender:
    """
    Recommend a learning path by comparing user goal + skills to catalog rows
    using TF-IDF vectors and cosine similarity.
    """

    def __init__(self, csv_path: str | Path | None = None) -> None:
        """Initialize vectorizer, fit on dataset, and keep reference to dataframe."""
        base_dir = Path(__file__).resolve().parent / "data"
        self._csv_path = Path(csv_path) if csv_path else base_dir / "learning_paths.csv"
        phases_path = self._csv_path.parent / "phases_by_role.json"
        self._df, self._phases_by_role = _load_dataset(self._csv_path, phases_path)
        self._vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self._matrix = self._vectorizer.fit_transform(self._df["combined_text"])

    def recommend(
        self,
        goal: str,
        skills: list[str],
        hours_per_day: float,
        experience_level: str,
    ) -> dict[str, Any]:
        """
        Return the best matching path, scaled timeline, roadmap lines, and courses.

        Parameters
        ----------
        goal : str
            Target role or objective (e.g. Data Scientist).
        skills : list of str
            Skills the user already has or wants to emphasize.
        hours_per_day : float
            Study hours per day.
        experience_level : str
            Beginner, Intermediate, or Advanced.
        """
        query = f"{goal} {' '.join(skills)}"
        q_vec = self._vectorizer.transform([query])
        sims = cosine_similarity(q_vec, self._matrix).flatten()
        best_idx = int(np.argmax(sims))
        row = self._df.iloc[best_idx]
        rid = str(row["role_id"])
        phases = list(self._phases_by_role.get(rid, []))
        scaled = _scale_days(phases, hours_per_day, experience_level)
        total_days = scaled[-1]["days_end"] if scaled else 0
        weeks = max(1, round(total_days / 7))

        roadmap_lines = _build_roadmap_lines(scaled)
        courses = [c.strip() for c in str(row["suggested_courses"]).split(";") if c.strip()]

        kw = str(row["skills_keywords"])
        return {
            "matched_role": str(row["role_name"]),
            "similarity_score": float(sims[best_idx]),
            "summary": str(row["learning_path_summary"]),
            "phases": scaled,
            "roadmap": roadmap_lines,
            "timeline_days": total_days,
            "timeline_weeks": weeks,
            "recommended_skill_sequence": self._skill_sequence(goal, skills, scaled),
            "course_suggestions": courses,
            "ai_explanation": self._explain_match(goal, skills, row["role_name"], sims[best_idx]),
            "skill_gap_analysis": self._skill_gaps(skills, kw),
            "role_skills_keywords": kw,
        }

    def _skill_sequence(
        self,
        goal: str,
        skills: list[str],
        phases: list[dict[str, Any]],
    ) -> list[str]:
        """Build an ordered skill list: user skills first, then phase topics."""
        base = [s.strip() for s in skills if s.strip()]
        extras: list[str] = []
        for p in phases:
            for part in str(p.get("topics", "")).split(","):
                t = part.strip()
                if t and t not in base and t not in extras:
                    extras.append(t)
        return base + extras[:12]

    def _explain_match(
        self,
        goal: str,
        skills: list[str],
        role_name: str,
        score: float,
    ) -> str:
        """Produce a short natural-language rationale for the recommendation."""
        skill_part = ", ".join(skills[:5]) if skills else "your selected areas"
        return (
            f"Based on your goal ({goal}) and skills ({skill_part}), "
            f"the closest catalog path is **{role_name}** "
            f"(content similarity {score:.2f}). "
            "Phases are ordered from foundations to advanced topics and scaled to your schedule."
        )

    def _skill_gaps(self, user_skills: list[str], role_keywords: str) -> list[str]:
        """List role keyword tokens that are not covered by user skills (simple heuristic)."""
        tokens = {t.strip().lower() for t in role_keywords.replace(",", " ").split() if len(t) > 2}
        have = {s.lower() for s in user_skills}
        gaps = sorted(tokens - have)
        return gaps[:10]

    def scored_skill_gaps(self, user_skills: list[str], role_keywords: str) -> list[dict[str, Any]]:
        """
        Skill gaps with priority (HIGH/MEDIUM/LOW) and importance score.

        Earlier keywords in the role profile are treated as more foundational → higher priority.
        """
        raw = [t.strip() for t in role_keywords.replace(",", " ").split() if len(t.strip()) > 2]
        # Preserve order, dedupe case-insensitively
        seen: set[str] = set()
        ordered: list[str] = []
        for t in raw:
            k = t.lower()
            if k not in seen:
                seen.add(k)
                ordered.append(t)

        have = {s.lower() for s in user_skills}
        gaps = [g for g in ordered if g.lower() not in have][:14]
        n = max(len(ordered), 1)

        scored: list[dict[str, Any]] = []
        for g in gaps:
            try:
                idx = next(i for i, x in enumerate(ordered) if x.lower() == g.lower())
            except StopIteration:
                idx = n - 1
            # Earlier in role keyword list → higher score
            position_score = 1.0 - (idx / n) * 0.55
            length_boost = min(0.15, max(0, (12 - len(g)) * 0.01))
            score = min(1.0, position_score + length_boost)
            if score >= 0.72:
                priority = "HIGH"
            elif score >= 0.48:
                priority = "MEDIUM"
            else:
                priority = "LOW"
            scored.append({"skill": g, "priority": priority, "score": round(float(score), 3)})
        return scored
