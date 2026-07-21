"""
In-memory TTL cache for full /generate-path JSON responses.

Thread-safe; suitable for single-process dev. Use Redis in production for multi-worker setups.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any

_lock = threading.Lock()
_store: dict[str, tuple[float, dict[str, Any]]] = {}


def _hash_key(parts: dict[str, Any]) -> str:
    """Stable SHA256 key from a JSON-serializable dict."""
    blob = json.dumps(parts, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def cache_get(key: str) -> dict[str, Any] | None:
    """Return cached payload if present and not expired."""
    now = time.time()
    with _lock:
        hit = _store.get(key)
        if not hit:
            return None
        expires_at, payload = hit
        if now > expires_at:
            del _store[key]
            return None
        return payload


def cache_set(key: str, payload: dict[str, Any], ttl_seconds: int) -> None:
    """Store payload until TTL elapses."""
    with _lock:
        _store[key] = (time.time() + max(1, ttl_seconds), payload)


def make_generate_cache_key(
    *,
    user_id: str,
    skills: list[str],
    goal: str,
    hours_per_day: float,
    experience_level: str | None,
    regenerate_smarter: bool,
    feedback_fingerprint: str,
) -> str:
    """Build dedupe key including user feedback state so new feedback misses stale cache."""
    parts = {
        "user_id": user_id,
        "skills": sorted(s.strip().lower() for s in skills),
        "goal": goal.strip().lower(),
        "hours": round(float(hours_per_day), 2),
        "exp": experience_level or "infer",
        "smarter": regenerate_smarter,
        "fb": feedback_fingerprint,
    }
    return _hash_key(parts)


def clear_all() -> None:
    """Testing / admin hook to drop cache entries."""
    with _lock:
        _store.clear()
