"""
Optional TensorFlow/Keras model for experience-level classification.

Install TensorFlow separately (`pip install tensorflow`) to use `train_and_predict`.
If TensorFlow is not installed, functions raise ImportError with a clear message.
"""

from __future__ import annotations

from typing import Iterable

try:
    import numpy as np
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
except ImportError:  # pragma: no cover - optional dependency
    tf = None  # type: ignore
    keras = None  # type: ignore
    layers = None  # type: ignore
    np = None  # type: ignore


def _ensure_tf() -> None:
    """Raise ImportError if TensorFlow is not available."""
    if tf is None:
        raise ImportError(
            "TensorFlow is not installed. Run: pip install tensorflow"
        )


def train_small_level_model(
    texts: list[str],
    labels: list[int],
    epochs: int = 30,
) -> keras.Model:
    """
    Train a tiny dense network on integer-encoded labels (0=Beginner,1=Intermediate,2=Advanced).

    Parameters
    ----------
    texts : list of str
        Training sentences.
    labels : list of int
        Integer labels aligned with texts.
    epochs : int
        Training epochs (small data converges quickly).
    """
    _ensure_tf()
    assert np is not None and keras is not None and layers is not None

    max_words = 2000
    max_len = 40
    vectorize = layers.TextVectorization(max_tokens=max_words, output_sequence_length=max_len)
    raw_ds = tf.data.Dataset.from_tensor_slices((texts, labels))
    text_only = raw_ds.map(lambda x, y: x)
    vectorize.adapt(text_only)

    num_classes = len(set(labels))
    model = keras.Sequential(
        [
            vectorize,
            layers.Embedding(max_words + 1, 32),
            layers.GlobalAveragePooling1D(),
            layers.Dense(32, activation="relu"),
            layers.Dense(num_classes, activation="softmax"),
        ]
    )
    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    ds = tf.data.Dataset.from_tensor_slices((texts, np.array(labels))).batch(8)
    model.fit(ds, epochs=epochs, verbose=0)
    return model


def predict_level_tensorflow(
    model: "keras.Model",
    goal: str,
    skills: Iterable[str],
) -> int:
    """Return predicted class index for goal + skills using a trained Keras model."""
    _ensure_tf()
    import numpy as np_local

    text = f"{goal} {' '.join(skills)}"
    pred = model.predict(tf.constant([text]), verbose=0)
    return int(np_local.argmax(pred, axis=1)[0])
