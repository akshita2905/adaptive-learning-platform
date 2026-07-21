"""MongoDB access wired to application settings."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from pymongo import MongoClient
from pymongo.database import Database

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from config import get_settings
from database.connection import (
    feedback_collection,
    history_collection,
    learning_paths_collection,
    users_collection,
)

_client: MongoClient[Any] | None = None


def get_mongo_client() -> MongoClient[Any]:
    """Singleton Mongo client per process."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_db() -> Database[Any]:
    """Application database handle."""
    settings = get_settings()
    return get_mongo_client()[settings.mongodb_db_name]


def users_coll():
    """Users collection."""
    return users_collection(get_db())


def history_coll():
    """History collection."""
    return history_collection(get_db())


def learning_paths_coll():
    """Learning paths collection."""
    return learning_paths_collection(get_db())


def feedback_coll():
    """Step-level user feedback for adaptive paths."""
    return feedback_collection(get_db())
