"""Bridge to scikit-learn recommenders and level classifiers."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, TYPE_CHECKING

# Project root (parent of server/) must be on path for ml_model imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

if TYPE_CHECKING:
    from ml_model.level_classifier import ExperienceLevelClassifier
    from ml_model.recommender import LearningPathRecommender

_recommender: Any = None
_classifier: Any = None


def get_recommender() -> Any:
    """Lazy singleton for TF-IDF recommender (loads sklearn on first use)."""
    global _recommender
    if _recommender is None:
        from ml_model.recommender import LearningPathRecommender

        _recommender = LearningPathRecommender()
    return _recommender


def get_classifier() -> Any:
    """Lazy singleton for experience level model."""
    global _classifier
    if _classifier is None:
        from ml_model.level_classifier import ExperienceLevelClassifier

        _classifier = ExperienceLevelClassifier()
    return _classifier


def build_path_payload(
    goal: str,
    skills: list[str],
    hours_per_day: float,
    experience_level: str | None,
) -> tuple[dict[str, Any], str, str | None, dict[str, float] | None]:
    """
    Run ML models and return output dict, resolved level, predicted label, probabilities.

    If experience_level is None, the classifier fills it in.
    """
    clf = get_classifier()
    rec = get_recommender()

    predicted: str | None = None
    probs: dict[str, float] | None = None
    if experience_level:
        level = experience_level
    else:
        predicted = clf.predict_level(goal, skills)
        probs = clf.predict_proba_dict(goal, skills)
        level = predicted

    raw = rec.recommend(goal, skills, hours_per_day, level)
    return raw, level, predicted, probs
