"""
MongoDB connection helpers for the learning path application.
"""

from __future__ import annotations

import os
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database


def get_mongo_uri() -> str:
    """Read Mongo connection URI from environment."""
    uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    return uri


def get_client() -> MongoClient:
    """Create a MongoClient (callers should reuse one per process)."""
    return MongoClient(get_mongo_uri())


def get_database(client: MongoClient | None = None, db_name: str | None = None) -> Database[Any]:
    """Return the application database, optionally creating a client."""
    name = db_name or os.getenv("MONGODB_DB_NAME", "learning_path_app")
    cli = client or get_client()
    return cli[name]


def users_collection(db: Database[Any]) -> Collection[Any]:
    """Users collection."""
    return db["users"]


def learning_paths_collection(db: Database[Any]) -> Collection[Any]:
    """Stored generated learning paths."""
    return db["learning_paths"]


def history_collection(db: Database[Any]) -> Collection[Any]:
    """History of generations per user."""
    return db["history"]


def feedback_collection(db: Database[Any]) -> Collection[Any]:
    """User step feedback (completed / not understood) for adaptive learning."""
    return db["step_feedback"]
