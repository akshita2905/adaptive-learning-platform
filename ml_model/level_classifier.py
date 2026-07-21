"""
Predict experience level (Beginner / Intermediate / Advanced) when not provided,CountVectorizer RandomForestClassifier- model use in project 
using a small supervised model on tabular features derived from skills and goals.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline


def _default_training_rows() -> pd.DataFrame:
    """
    Build a small synthetic dataset: text features -> level label.

    Used to train the classifier when no external training file is present.
    """
    rows = [
        ("python hello world variables", "Beginner"),
        ("html css first website", "Beginner"),
        ("javascript basics dom", "Beginner"),
        ("react hooks tutorial beginner", "Beginner"),
        ("pandas numpy data cleaning project", "Intermediate"),
        ("rest api authentication jwt", "Intermediate"),
        ("docker compose microservices", "Intermediate"),
        ("kubernetes helm production", "Advanced"),
        ("distributed systems consensus raft", "Advanced"),
        ("pytorch custom architecture paper", "Advanced"),
        ("system design scalable backend", "Advanced"),
        ("sql joins window functions analytics", "Intermediate"),
    ]
    return pd.DataFrame(rows, columns=["text", "label"])


class ExperienceLevelClassifier:
    """
    Classify experience level from a short description of skills + goal.

    Uses a pipeline: bag-of-words + RandomForest. Optionally compares with MLPClassifier.
    """

    def __init__(self, model_dir: str | Path | None = None) -> None:
        """Load or train the classifier and persist to model_dir when provided."""
        self._model_dir = Path(model_dir) if model_dir else Path(__file__).resolve().parent / "saved_models"
        self._model_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._model_dir / "level_classifier.joblib"
        self._pipeline: Pipeline | None = None
        self._mlp: Pipeline | None = None
        self._fit_models()

    def _fit_models(self) -> None:
        """Train sklearn models from default data; load from disk if available."""
        if self._path.exists():
            self._pipeline = joblib.load(self._path)
            mlp_path = self._model_dir / "level_mlp.joblib"
            if mlp_path.exists():
                self._mlp = joblib.load(mlp_path)
            return

        df = _default_training_rows()
        self._pipeline = Pipeline(
            [
                ("vect", CountVectorizer(ngram_range=(1, 2))),
                ("clf", RandomForestClassifier(n_estimators=80, random_state=42)),
            ]
        )
        self._pipeline.fit(df["text"], df["label"])
        joblib.dump(self._pipeline, self._path)

        # Optional small neural network (sklearn MLP) for comparison / enrichment
        self._mlp = Pipeline(
            [
                ("vect", CountVectorizer(ngram_range=(1, 2))),
                (
                    "mlp",
                    MLPClassifier(
                        hidden_layer_sizes=(64, 32),
                        max_iter=500,
                        random_state=42,
                    ),
                ),
            ]
        )
        self._mlp.fit(df["text"], df["label"])
        joblib.dump(self._mlp, self._model_dir / "level_mlp.joblib")

    def predict_level(self, goal: str, skills: Iterable[str]) -> str:
        """
        Predict Beginner / Intermediate / Advanced from goal and skills list.
        """
        text = f"{goal} {' '.join(skills)}".strip()
        if not text:
            return "Beginner"
        assert self._pipeline is not None
        pred = self._pipeline.predict([text])[0]
        return str(pred)

    def predict_proba_dict(self, goal: str, skills: Iterable[str]) -> dict[str, float]:
        """Return class probabilities for the primary RandomForest pipeline."""
        text = f"{goal} {' '.join(skills)}".strip()
        if not text:
            return {"Beginner": 1.0, "Intermediate": 0.0, "Advanced": 0.0}
        assert self._pipeline is not None
        classes = list(self._pipeline.named_steps["clf"].classes_)
        probs = self._pipeline.predict_proba([text])[0]
        return {str(c): float(p) for c, p in zip(classes, probs)}
