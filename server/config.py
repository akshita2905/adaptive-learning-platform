"""Application settings: load ``server/.env`` then read variables (including API keys via ``os.getenv``)."""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve ``server/.env`` and load into ``os.environ`` before any ``os.getenv`` / Settings reads.
_SERVER_DIR = Path(__file__).resolve().parent
_ENV_FILE = _SERVER_DIR / ".env"
load_dotenv(_ENV_FILE, override=False)

logger = logging.getLogger(__name__)


def _env_str(name: str, default: str = "") -> str:
    """Read a string env var with optional default; strip whitespace."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip()


class Settings(BaseSettings):
    """
    Non-secret defaults and values pydantic reads from the environment.

    ``OPENAI_API_KEY`` and ``YOUTUBE_API_KEY`` are applied in ``get_settings()`` using
    ``os.getenv`` so behavior matches the explicit requirement and ``load_dotenv`` output.
    """

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "learning_path_app"
    jwt_secret: str = "change-me-in-production-use-long-random-secret"
    jwt_algorithm: str = "HS256"
    jwt_exp_hours: int = 72
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    openai_api_key: str = ""
    youtube_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    generate_cache_ttl_seconds: int = 300
    youtube_max_per_topic: int = 3


@lru_cache
def get_settings() -> Settings:
    """
    Build settings: merge pydantic env parsing with ``os.getenv`` for API keys.

    Logs one-time warnings when API keys are missing (fallback roadmap / empty videos).
    """
    base = Settings()
    openai_key = _env_str("OPENAI_API_KEY", "")
    youtube_key = _env_str("YOUTUBE_API_KEY", "")

    if not openai_key:
        logger.warning(
            "OPENAI_API_KEY is not set or empty in the environment (check server/.env). "
            "Using the local fallback AI roadmap template."
        )
    if not youtube_key:
        logger.warning(
            "YOUTUBE_API_KEY is not set or empty in the environment (check server/.env). "
            "YouTube video lists will be empty."
        )

    # ``Settings`` is a frozen-like pydantic model; copy with API keys attached for services.
    return base.model_copy(update={"openai_api_key": openai_key, "youtube_api_key": youtube_key})
