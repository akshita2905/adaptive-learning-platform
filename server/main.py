"""
FastAPI application: auth, AI-enhanced learning paths, feedback, and history.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

# Project root for imports
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config as _config_bootstrap  # noqa: F401 — loads ``server/.env`` via python-dotenv

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(asctime)s [%(name)s] %(message)s",
)
logger = logging.getLogger("learning_path.app")

from auth_utils import create_access_token, hash_password, verify_password
from config import get_settings
from db import feedback_coll, history_coll, learning_paths_coll, users_coll
from dependencies import get_current_user_id
from path_pipeline import build_full_path_response
from schemas import (
    FeedbackItem,
    FeedbackRequest,
    GeneratePathRequest,
    GeneratePathResponse,
    HistoryItem,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SkillGapItem,
    TokenResponse,
    VideoItem,
)
from services.adaptive_service import fetch_user_feedback, feedback_fingerprint
from services.generation_cache import cache_get, cache_set, make_generate_cache_key

app = FastAPI(
    title="AI-Based Personalized Learning Path Generator",
    version="2.0.0",
    description="FastAPI + MongoDB + scikit-learn + OpenAI + YouTube for adaptive learning paths.",
)


def _configure_cors() -> None:
    """Enable CORS for local Vite dev server and configured origins."""
    settings = get_settings()
    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


_configure_cors()


@app.post("/register", response_model=TokenResponse)
def register(body: RegisterRequest) -> TokenResponse:
    """Create a new user account and return a JWT."""
    coll = users_coll()
    if coll.find_one({"email": body.email.lower()}):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    now = datetime.now(timezone.utc)
    doc = {
        "email": body.email.lower(),
        "full_name": body.full_name.strip(),
        "hashed_password": hash_password(body.password),
        "created_at": now,
    }
    result = coll.insert_one(doc)
    uid = str(result.inserted_id)
    token = create_access_token(uid)
    return TokenResponse(
        access_token=token,
        user_id=uid,
        email=body.email.lower(),
        full_name=body.full_name.strip(),
    )


@app.post("/login", response_model=TokenResponse)
def login(body: LoginRequest) -> TokenResponse:
    """Authenticate and return JWT."""
    coll = users_coll()
    user = coll.find_one({"email": body.email.lower()})
    if not user or not verify_password(body.password, user["hashed_password"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    uid = str(user["_id"])
    token = create_access_token(uid)
    return TokenResponse(
        access_token=token,
        user_id=uid,
        email=user["email"],
        full_name=user.get("full_name", ""),
    )


def _coerce_generate_response(data: dict) -> GeneratePathResponse:
    """Build a validated response model (coerces nested video items)."""
    videos_raw = data.get("videos") or {}
    videos: dict[str, list[VideoItem]] = {}
    for k, lst in videos_raw.items():
        if not isinstance(lst, list):
            continue
        videos[str(k)] = [VideoItem.model_validate(x) if isinstance(x, dict) else VideoItem() for x in lst]

    gaps_raw = data.get("skill_gaps") or []
    skill_gaps: list[SkillGapItem] = []
    for x in gaps_raw:
        if isinstance(x, dict):
            try:
                skill_gaps.append(SkillGapItem.model_validate(x))
            except Exception:
                skill_gaps.append(
                    SkillGapItem(
                        skill=str(x.get("skill", "?")),
                        priority="MEDIUM",
                        score=float(x.get("score", 0.5) or 0.5),
                    )
                )
        else:
            skill_gaps.append(SkillGapItem(skill=str(x), priority="MEDIUM", score=0.5))

    return GeneratePathResponse(
        base_path=data.get("base_path") or {},
        ai_roadmap=data.get("ai_roadmap") or {},
        videos=videos,
        skill_gaps=skill_gaps,
        courses=data.get("courses") or {},
        generation_id=data.get("generation_id"),
    )


@app.post("/generate-path", response_model=GeneratePathResponse)
def generate_path(
    body: GeneratePathRequest,
    user_id: str = Depends(get_current_user_id),
) -> GeneratePathResponse:
    """
    ML base roadmap + OpenAI enrichment + YouTube + courses + scored skill gaps.
    Respects adaptive feedback from MongoDB. Caches full JSON unless ``regenerate_smarter``.
    """
    settings = get_settings()
    feedback_rows = fetch_user_feedback(user_id)
    fbp = feedback_fingerprint(feedback_rows)

    cache_key = make_generate_cache_key(
        user_id=user_id,
        skills=body.skills,
        goal=body.goal.strip(),
        hours_per_day=body.hours_per_day,
        experience_level=body.experience_level,
        regenerate_smarter=body.regenerate_smarter,
        feedback_fingerprint=fbp,
    )

    if body.use_cache and not body.regenerate_smarter:
        cached = cache_get(cache_key)
        if cached:
            logger.info("generate-path cache hit user=%s…", user_id[:8])
            return _coerce_generate_response(cached)

    logger.info("generate-path cache miss — building pipeline user=%s…", user_id[:8])
    payload = build_full_path_response(
        user_id=user_id,
        skills=body.skills,
        goal=body.goal.strip(),
        hours_per_day=body.hours_per_day,
        experience_level=body.experience_level,
        settings=settings,
        regenerate_smarter=body.regenerate_smarter,
        feedback_rows=feedback_rows,
    )

    response = _coerce_generate_response(payload)
    now = datetime.now(timezone.utc)
    input_doc = {
        "skills": body.skills,
        "goal": body.goal.strip(),
        "experience_level": body.experience_level,
        "hours_per_day": body.hours_per_day,
        "regenerate_smarter": body.regenerate_smarter,
    }
    out_doc = response.model_dump()

    doc = {
        "user_id": user_id,
        "input": input_doc,
        "generated_output": out_doc,
        "created_at": now,
    }
    ins = history_coll().insert_one(dict(doc))
    learning_paths_coll().insert_one(dict(doc))
    gen_id = str(ins.inserted_id)
    out_doc["generation_id"] = gen_id

    cache_set(cache_key, out_doc, settings.generate_cache_ttl_seconds)

    return _coerce_generate_response(out_doc)


@app.post("/feedback", response_model=MessageResponse)
def submit_feedback(
    body: FeedbackRequest,
    user_id: str = Depends(get_current_user_id),
) -> MessageResponse:
    """Record step feedback (completed / not understood) for adaptive future roadmaps."""
    coll = feedback_coll()
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "step_index": body.step_index,
        "phase_name": body.phase_name.strip(),
        "status": body.status,
        "generation_id": body.generation_id,
        "created_at": now,
    }
    coll.insert_one(doc)
    logger.info(
        "feedback user=%s… step=%s status=%s phase=%r",
        user_id[:8],
        body.step_index,
        body.status,
        body.phase_name[:40],
    )
    return MessageResponse(message="Feedback saved")


@app.get("/feedback", response_model=list[FeedbackItem])
def list_feedback(user_id: str = Depends(get_current_user_id)) -> list[FeedbackItem]:
    """Return recent step feedback for the authenticated user."""
    coll = feedback_coll()
    cur = coll.find({"user_id": user_id}).sort("created_at", -1).limit(200)
    items: list[FeedbackItem] = []
    for doc in cur:
        items.append(
            FeedbackItem(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                step_index=int(doc.get("step_index", 0)),
                phase_name=str(doc.get("phase_name", "")),
                status=str(doc.get("status", "")),
                generation_id=doc.get("generation_id"),
                created_at=doc["created_at"],
            )
        )
    return items


@app.get("/history", response_model=list[HistoryItem])
def get_history(user_id: str = Depends(get_current_user_id)) -> list[HistoryItem]:
    """Return past generations for the authenticated user, newest first."""
    coll = history_coll()
    cursor = coll.find({"user_id": user_id}).sort("created_at", -1).limit(50)
    items: list[HistoryItem] = []
    for doc in cursor:
        items.append(
            HistoryItem(
                id=str(doc["_id"]),
                user_id=doc["user_id"],
                input=doc["input"],
                generated_output=doc["generated_output"],
                created_at=doc["created_at"],
            )
        )
    return items


@app.delete("/feedback/{feedback_id}", response_model=MessageResponse)
def delete_feedback(
    feedback_id: str,
    user_id: str = Depends(get_current_user_id),
) -> MessageResponse:
    """Remove a feedback entry (optional reset progress for a step)."""
    try:
        oid = ObjectId(feedback_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid feedback id")
    res = feedback_coll().delete_one({"_id": oid, "user_id": user_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return MessageResponse(message="Deleted")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}
